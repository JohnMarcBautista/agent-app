from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from app.schemas import (
    LeadIn,
    JobOut,
    HealthOut,
    HandoffOut,
    NeedsDispatchOut,
    ProposalOut,
    SmsCallbackIn,
    ChatInboundIn,
    ChatInboundOut,
    ChatReplyIn,
    ChatReplyOut,
)
from app.db import get_db, init_db
from app.models import Base, Job
from app.services.intent import classify_intent
from app.services.capacity import pick_slot
from app.services.booking import book_job
from app.services.notify import send_confirmation
from app.logging import log
from app.services.capacity import preview_slot
from app.services.llm import generate_booking_proposal
from app.services.proposal import (
    create_proposal,
    get_proposal_by_message_id,
    confirm_proposal,
    get_latest_proposal_by_phone,
    resolve_tenant_by_phone,
)
from app.services.llm import extract_entities_from_text, classify_reply_text
from app.services.capacity import next_slot


def create_app() -> FastAPI:
    init_db(Base)
    app = FastAPI(title="revin-mini")

    @app.get("/healthz", response_model=HealthOut)
    def healthz() -> HealthOut:
        return HealthOut(ok=True)

    @app.post("/lead", response_model=JobOut | HandoffOut | NeedsDispatchOut)
    def handle_lead(lead: LeadIn, db: Session = Depends(get_db)):
        log.info("lead_received", extra={"tenant_id": lead.tenant_id, "event_id": lead.event_id})
        intent = classify_intent(lead)
        if intent != "book":
            return HandoffOut(reason=intent)

        slot = pick_slot(db, lead.tenant_id, lead.service)
        if not slot:
            log.warning("no_capacity", extra={"tenant_id": lead.tenant_id, "event_id": lead.event_id})
            return NeedsDispatchOut()

        job = book_job(db, lead, slot)
        send_confirmation(job)
        log.info(
            "job_booked",
            extra={"tenant_id": job.tenant_id, "event_id": job.source_event_id, "job_id": job.job_id},
        )
        return JobOut(
            job_id=job.job_id,
            tenant_id=job.tenant_id,
            customer_name=job.customer_name,
            phone=job.phone,
            service=job.service,
            slot={"start": job.slot_start.isoformat(), "end": job.slot_end.isoformat()},
            status=job.status,
            source_event=job.source_event_id,
        )

    @app.get("/jobs")
    def list_jobs(db: Session = Depends(get_db)):
        rows = db.query(Job).order_by(Job.created_at.desc()).limit(50).all()
        return [
            {
                "job_id": j.job_id,
                "tenant_id": j.tenant_id,
                "customer_name": j.customer_name,
                "service": j.service,
                "slot_start": j.slot_start.isoformat(),
                "slot_end": j.slot_end.isoformat(),
                "status": j.status,
            }
            for j in rows
        ]

    @app.post("/lead/propose", response_model=ProposalOut | HandoffOut | NeedsDispatchOut)
    def propose_lead(lead: LeadIn, db: Session = Depends(get_db)):
        log.info("lead_received", extra={"tenant_id": lead.tenant_id, "event_id": lead.event_id})
        intent = classify_intent(lead)
        if intent != "book":
            return HandoffOut(reason=intent)

        slot = preview_slot(db, lead.tenant_id, lead.service)
        if not slot:
            log.warning("no_capacity", extra={"tenant_id": lead.tenant_id, "event_id": lead.event_id})
            return NeedsDispatchOut()

        start, end = slot
        text = generate_booking_proposal(lead, start, end)

        # Send SMS via mock, save proposal
        from app.services.notify import send_sms

        message_id = send_sms(lead.phone, text)
        proposal = create_proposal(db, lead, start, end, text, message_id)
        log.info(
            "proposal_sent",
            extra={"tenant_id": lead.tenant_id, "event_id": lead.event_id, "job_id": proposal.proposal_id},
        )
        return ProposalOut(proposal_id=proposal.proposal_id, message_id=message_id)

    @app.post("/sms/callback")
    def sms_callback(payload: SmsCallbackIn, db: Session = Depends(get_db)):
        proposal = get_proposal_by_message_id(db, payload.message_id)
        if not proposal or proposal.phone != payload.from_phone:
            return {"status": "IGNORED"}

        body = payload.body.strip().lower()
        if body in {"yes", "y", "confirm", "ok"}:
            job = confirm_proposal(db, proposal)
            if not job:
                return {"status": "NEEDS_DISPATCH"}
            send_confirmation(job)
            return {
                "status": "BOOKED",
                "job_id": job.job_id,
                "tenant_id": job.tenant_id,
                "slot_start": job.slot_start.isoformat(),
                "slot_end": job.slot_end.isoformat(),
            }
        elif "resched" in body or "reschedule" in body or body in {"no", "n"}:
            return {"status": "HANDOFF", "reason": "reschedule"}
        else:
            return {"status": "IGNORED"}

    @app.post("/chat/inbound", response_model=ChatInboundOut)
    def chat_inbound(payload: ChatInboundIn, db: Session = Depends(get_db)):
        # Resolve tenant by phone first; fall back to NLU extraction
        tenant_id = resolve_tenant_by_phone(db, payload.from_phone)
        log.info("tenant_resolved", extra={"phone": payload.from_phone, "tenant_id": tenant_id})
        if not tenant_id:
            entities = extract_entities_from_text(payload.text)
            tenant_id = entities.get("tenant_id")
            log.info("tenant_from_nlu", extra={"tenant_id": tenant_id})
        # Always use NLU for service from text (or simple heuristics)
        service = extract_entities_from_text(payload.text).get("service")
        log.info("service_extracted", extra={"service": service})
        if not tenant_id or not service:
            return ChatInboundOut(status="HANDOFF", message="Could not determine tenant or service.")

        slot = preview_slot(db, tenant_id, service)
        if not slot:
            return ChatInboundOut(status="NEEDS_DISPATCH", tenant_id=tenant_id, service=service)
        start, end = slot

        # Create a lightweight pseudo-lead for proposal
        from types import SimpleNamespace

        lead = SimpleNamespace(
            event_id="evt_chat_inbound",
            tenant_id=tenant_id,
            name=payload.from_phone,
            phone=payload.from_phone,
            address=None,
            service=service,
        )
        text = generate_booking_proposal(lead, start, end)
        from app.services.notify import send_sms

        message_id = send_sms(payload.from_phone, text)
        proposal = create_proposal(db, lead, start, end, text, message_id)
        return ChatInboundOut(
            status="PROPOSED",
            tenant_id=tenant_id,
            service=service,
            proposal_id=proposal.proposal_id,
            message=text,
        )

    @app.post("/chat/reply", response_model=ChatReplyOut)
    def chat_reply(payload: ChatReplyIn, db: Session = Depends(get_db)):
        # Find the latest proposal for this phone
        proposal = get_latest_proposal_by_phone(db, payload.from_phone)
        if not proposal:
            return ChatReplyOut(status="HANDOFF", message="No active proposal found.")

        label = classify_reply_text(payload.text)
        if label == "yes":
            job = confirm_proposal(db, proposal)
            if not job:
                return ChatReplyOut(status="NEEDS_DISPATCH", proposal_id=proposal.proposal_id)
            send_confirmation(job)
            confirmation_msg = f"Confirmed! Your {job.service} is booked for {job.slot_start.strftime('%B %d, %Y at %-I:%M %p')}. See you then!"
            return ChatReplyOut(status="BOOKED", job_id=job.job_id, proposal_id=proposal.proposal_id, message=confirmation_msg)
        elif label == "no":
            ns = next_slot(db, proposal.tenant_id, proposal.service, after=proposal.slot_start)
            if not ns:
                return ChatReplyOut(status="NEEDS_DISPATCH", proposal_id=proposal.proposal_id)
            start, end = ns
            # Build a new proposal message
            from types import SimpleNamespace
            lead_like = SimpleNamespace(
                event_id="evt_chat_resched",
                tenant_id=proposal.tenant_id,
                name=proposal.customer_name,
                phone=proposal.phone,
                address=proposal.address,
                service=proposal.service,
            )
            new_text = generate_booking_proposal(lead_like, start, end)
            from app.services.notify import send_sms
            new_msg = send_sms(proposal.phone, new_text)
            new_prop = create_proposal(db, lead_like, start, end, new_text, new_msg)
            return ChatReplyOut(status="PROPOSED", proposal_id=new_prop.proposal_id, message=new_text)
        else:
            return ChatReplyOut(status="CLARIFY", proposal_id=proposal.proposal_id, message="Please reply YES to confirm or say RESCHEDULE.")

    return app




app = create_app()



from datetime import datetime
import uuid
from types import SimpleNamespace

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Proposal, TenantPhone
from app.services.booking import book_job
from app.services.capacity import try_mark_slot_booked, pick_slot


def create_proposal(
    db: Session,
    lead,
    start,
    end,
    message_text: str,
    message_id: str,
):
    proposal = Proposal(
        proposal_id=uuid.uuid4().hex,
        tenant_id=lead.tenant_id,
        customer_name=lead.name,
        phone=lead.phone,
        address=lead.address,
        service=lead.service,
        slot_start=start,
        slot_end=end,
        status="PROPOSED",
        message_id=message_id,
        source_event_id=lead.event_id,
        created_at=datetime.utcnow(),
    )
    db.add(proposal)
    db.commit()
    return proposal


def get_proposal_by_message_id(db: Session, message_id: str):
    return db.execute(select(Proposal).where(Proposal.message_id == message_id)).scalar_one_or_none()


def get_latest_proposal_by_phone(db: Session, phone: str):
    return db.execute(
        select(Proposal).where(Proposal.phone == phone).order_by(Proposal.created_at.desc()).limit(1)
    ).scalar_one_or_none()


def resolve_tenant_by_phone(db: Session, phone: str) -> str | None:
    rec = db.execute(select(TenantPhone).where(TenantPhone.phone == phone).limit(1)).scalar_one_or_none()
    return rec.tenant_id if rec else None


def confirm_proposal(db: Session, proposal: Proposal):
    # Attempt to book the proposed slot; if taken, pick next available
    success = try_mark_slot_booked(
        db, proposal.tenant_id, proposal.service, proposal.slot_start, proposal.slot_end
    )
    if not success:
        next_slot = pick_slot(db, proposal.tenant_id, proposal.service)
        if not next_slot:
            return None
        start, end = next_slot
    else:
        start, end = proposal.slot_start, proposal.slot_end

    lead_like = SimpleNamespace(
        event_id=f"{proposal.message_id}:confirm",
        tenant_id=proposal.tenant_id,
        name=proposal.customer_name,
        phone=proposal.phone,
        address=proposal.address,
        service=proposal.service,
    )
    job = book_job(db, lead_like, (start, end))
    # Update proposal status
    db.execute(
        update(Proposal)
        .where(Proposal.proposal_id == proposal.proposal_id)
        .values(status="CONFIRMED")
    )
    db.commit()
    return job



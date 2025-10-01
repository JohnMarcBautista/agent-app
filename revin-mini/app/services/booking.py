from datetime import datetime
from typing import Tuple
import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Job, Idempotency


def book_job(db: Session, lead, slot: Tuple[datetime, datetime]) -> Job:
    idem_key = f"{lead.event_id}:book_job"

    existing_idem = db.execute(select(Idempotency).where(Idempotency.key == idem_key)).scalar_one_or_none()
    if existing_idem:
        existing_job = db.execute(select(Job).where(Job.job_id == existing_idem.job_id)).scalar_one()
        return existing_job

    job_id = uuid.uuid4().hex
    now = datetime.utcnow()
    job = Job(
        job_id=job_id,
        tenant_id=lead.tenant_id,
        customer_name=lead.name,
        phone=lead.phone,
        address=lead.address,
        service=lead.service,
        slot_start=slot[0],
        slot_end=slot[1],
        status="BOOKED",
        source_event_id=lead.event_id,
        created_at=now,
    )
    db.add(job)
    db.add(Idempotency(key=idem_key, job_id=job_id, created_at=now))
    db.commit()
    return job



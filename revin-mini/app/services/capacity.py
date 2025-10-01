from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import Capacity


def pick_slot(db: Session, tenant_id: str, service: str) -> Optional[Tuple[datetime, datetime]]:
    slot_row = db.execute(
        select(Capacity).where(
            Capacity.tenant_id == tenant_id,
            Capacity.service == service,
            Capacity.booked_bool.is_(False),
            Capacity.start_dt > datetime.utcnow(),
        ).order_by(Capacity.start_dt.asc()).limit(1)
    ).scalar_one_or_none()

    if not slot_row:
        return None

    # Mark booked and return times
    db.execute(
        update(Capacity)
        .where(Capacity.id == slot_row.id, Capacity.booked_bool.is_(False))
        .values(booked_bool=True)
    )
    db.commit()
    return slot_row.start_dt, slot_row.end_dt


def preview_slot(db: Session, tenant_id: str, service: str) -> Optional[Tuple[datetime, datetime]]:
    row = db.execute(
        select(Capacity).where(
            Capacity.tenant_id == tenant_id,
            Capacity.service == service,
            Capacity.booked_bool.is_(False),
            Capacity.start_dt > datetime.utcnow(),
        ).order_by(Capacity.start_dt.asc()).limit(1)
    ).scalar_one_or_none()
    if not row:
        return None
    return row.start_dt, row.end_dt


def try_mark_slot_booked(
    db: Session, tenant_id: str, service: str, start: datetime, end: datetime
) -> bool:
    result = db.execute(
        update(Capacity)
        .where(
            Capacity.tenant_id == tenant_id,
            Capacity.service == service,
            Capacity.start_dt == start,
            Capacity.end_dt == end,
            Capacity.booked_bool.is_(False),
        )
        .values(booked_bool=True)
    )
    if result.rowcount and result.rowcount > 0:
        db.commit()
        return True
    db.rollback()
    return False


def next_slot(db: Session, tenant_id: str, service: str, after: datetime) -> Optional[Tuple[datetime, datetime]]:
    row = db.execute(
        select(Capacity).where(
            Capacity.tenant_id == tenant_id,
            Capacity.service == service,
            Capacity.booked_bool.is_(False),
            Capacity.start_dt > after,
        ).order_by(Capacity.start_dt.asc()).limit(1)
    ).scalar_one_or_none()
    if not row:
        return None
    return row.start_dt, row.end_dt



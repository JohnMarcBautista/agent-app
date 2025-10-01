from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Base, Capacity, TenantPhone
from app.db import init_db


def seed():
    init_db(Base)
    db: Session = SessionLocal()
    try:
        tenant = "t_acme"
        service = "AC Repair"
        now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        slots = []
        for i in range(1, 6):
            start = now + timedelta(hours=i)
            end = start + timedelta(hours=1)
            slots.append(Capacity(tenant_id=tenant, service=service, start_dt=start, end_dt=end, booked_bool=False))
        db.add_all(slots)
        # Seed tenant phone mapping
        if not db.query(TenantPhone).filter(TenantPhone.phone == "+15551234567").first():
            from datetime import datetime as dt
            db.add(TenantPhone(phone="+15551234567", tenant_id="t_acme", created_at=dt.utcnow()))
        db.commit()
        print(f"Seeded {len(slots)} slots for tenant={tenant} service={service}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()



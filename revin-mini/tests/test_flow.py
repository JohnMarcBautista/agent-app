from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app
from app.db import SessionLocal
from app.models import Base, Capacity
from app.db import init_db


client = TestClient(app)


def test_healthz():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_lead_booking_happy_path():
    # Seed a near-future capacity slot
    init_db(Base)
    db = SessionLocal()
    try:
        start = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        end = start + timedelta(hours=1)
        db.add(Capacity(tenant_id="t_acme", service="AC Repair", start_dt=start, end_dt=end, booked_bool=False))
        db.commit()
    finally:
        db.close()

    payload = {
        "event_id": "evt_test",
        "tenant_id": "t_acme",
        "name": "Jane Doe",
        "phone": "+15551234567",
        "service": "AC Repair",
        "notes": "please book",
    }
    r = client.post("/lead", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "BOOKED"
    assert body["tenant_id"] == "t_acme"
    assert body["service"] == "AC Repair"




revin-mini — Inbound Lead → Booking Flow (FastAPI)

Quick, interview-friendly service demonstrating Python REST, SQLAlchemy, and structured logging.

Features

- POST `/lead`: accept lead JSON, classify intent (stub), pick capacity slot, book job idempotently, send mock confirmation.
- GET `/jobs`: list recent jobs.
- GET `/healthz`: liveness.
- SQLite via SQLAlchemy; easily swappable to Postgres.
- JSON logs carrying `tenant_id`, `event_id`, `job_id`.
- Optional propose-first flow with LLM-crafted SMS and callback confirm.

Repo layout

```
app/
  main.py          # FastAPI app + routes
  db.py            # engine + SessionLocal + init_db
  models.py        # SQLAlchemy models
  schemas.py       # Pydantic models
  config.py        # env + settings
  logging.py       # JSON logger
  services/
    intent.py      # classify_intent
    capacity.py    # pick_slot
    booking.py     # book_job with idempotency
    notify.py      # mocked SMS
scripts/
  seed_capacity.py # seed demo capacity
tests/
  test_flow.py
```

Requirements

- Python 3.11+

Setup

```bash
python -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt
```

Environment

- Copy `.env.example` to `.env` and set `OPENAI_API_KEY` if using OpenAI.
- `.env` is auto-loaded from repo root; ensure you run uvicorn from the project directory.

Seeding data

- `scripts/seed_capacity.py` now also seeds a tenant-phone mapping: `+15551234567` → `t_acme`.
- `/chat/inbound` resolves tenant by phone first; if not mapped, it uses NLU extraction.

Run

```bash
PYTHONPATH=$(pwd) ./.venv/bin/uvicorn app.main:app --reload
```

Optional: enable LLM for propose-first flow

```bash
cp .env.example .env
echo "OPENAI_API_KEY=sk-..." >> .env
```

Propose-first flow

```bash
# Propose (no booking yet):
curl -X POST http://localhost:8000/lead/propose \
  -H "Content-Type: application/json" \
  -d '{
    "event_id":"evt_p1","tenant_id":"t_acme",
    "name":"Jane Doe","phone":"+15551234567",
    "service":"AC Repair","notes":"please propose"
  }'

# Callback confirm (simulating SMS vendor webhook):
curl -X POST http://localhost:8000/sms/callback \
  -H "Content-Type: application/json" \
  -d '{"message_id":"<copy-from-response>","from_phone":"+15551234567","body":"YES"}'
```

LLM chat-style experience (no real SMS; simulate via API)

```bash
# Inbound text: LLM extracts service, looks up tenant by phone, proposes slot
curl -X POST http://localhost:8000/chat/inbound \
  -H "Content-Type: application/json" \
  -d '{"from_phone":"+15551234567","text":"need ac repair asap"}'
# Returns: {"status":"PROPOSED","proposal_id":"...","message":"Hi! We've scheduled your AC repair..."}

# Customer replies YES to confirm
curl -X POST http://localhost:8000/chat/reply \
  -H "Content-Type: application/json" \
  -d '{"from_phone":"+15551234567","text":"YES"}'
# Returns: {"status":"BOOKED","job_id":"...","message":"Confirmed! Your AC Repair is booked..."}

# Or reply NO to get next available slot
curl -X POST http://localhost:8000/chat/reply \
  -H "Content-Type: application/json" \
  -d '{"from_phone":"+15551234567","text":"NO"}'
# Returns: {"status":"PROPOSED","proposal_id":"...","message":"<new slot proposal>"}
```

Key features:

- Phone number → tenant lookup (seeded: `+15551234567` → `t_acme`)
- OpenAI extracts service from free text
- LLM generates customer-friendly proposal messages
- LLM classifies reply intent (YES/NO/unknown)

Try it

```bash
curl -X POST http://localhost:8000/lead \
  -H "Content-Type: application/json" \
  -d '{
    "event_id":"evt_1","tenant_id":"t_acme",
    "name":"Jane Doe","phone":"+15551234567",
    "service":"AC Repair","notes":"no cooling"
  }'
```

Testing

```bash
PYTHONPATH=$(pwd) ./.venv/bin/python -m pytest -q
```

Notes for interview

- External actions are idempotent; retries won’t double-book.
- Logs propagate `tenant_id` and `event_id` for traceability.
- LLM hook could replace `classify_intent` with a provider call.

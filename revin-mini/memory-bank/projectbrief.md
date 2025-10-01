# Project Brief

Build a minimal "Inbound Lead → Booking Flow" service to demonstrate FastAPI, SQL, REST, and structured logging, with a stubbed intent classifier and idempotent booking. Persistence is SQLite via SQLAlchemy, swappable to Postgres.

Scope

- Endpoints: `POST /lead`, `GET /jobs`, `GET /healthz`.
- Data: `jobs`, `capacity`, `idempotency` tables.
- Behavior: classify intent → pick slot → book job (idempotent) → confirm.

Non-goals

- Real SMS delivery, real LLM integration, multi-tenant auth.

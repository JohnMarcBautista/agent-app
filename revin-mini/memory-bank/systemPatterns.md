# System Patterns

- Layered: `schemas` (validation), `services` (domain logic), `models` (ORM), `main` (API).
- Idempotency table ensures POST retries do not double-book.
- Structured JSON logging with tenant/event/job correlation fields.
- SQLite default for speed; migration to Postgres via `DATABASE_URL` env.
- Capacity reservation is optimistic: update flips `booked_bool` when selecting first available.

## LLM Integration

- Entity extraction: OpenAI extracts tenant_id and service from free text
- Service normalization: Maps LLM output (e.g., "ac repair") to DB conventions ("AC Repair")
- Markdown stripping: Removes ```json fences from OpenAI responses before parsing
- Proposal generation: LLM crafts customer-friendly SMS messages
- Reply classification: LLM determines YES/NO/unknown intent from customer replies
- Fallback heuristics: Simple keyword matching when API key unavailable

## Tenant Resolution

- Primary: Phone number lookup in `tenant_phone` table
- Fallback: NLU extraction from message text
- Seeded mapping: `+15551234567` → `t_acme`

## Chat Flow

1. `/chat/inbound`: phone + text → extract service → preview slot → generate proposal
2. `/chat/reply`: phone + reply text → classify intent → book (YES) or propose next (NO)

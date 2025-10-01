# Progress

What works

- `/healthz`, `/lead`, `/jobs` endpoints
- `/lead/propose` with LLM proposal generation
- `/sms/callback` for structured callback confirmation
- **`/chat/inbound`** - LLM entity extraction, tenant resolution, proposal generation
- **`/chat/reply`** - LLM reply classification (YES/NO), booking confirmation, rescheduling
- Capacity selection and idempotent booking
- Tenant-to-phone mapping with database lookup
- Service name normalization for DB matching
- Seed script for demo slots and tenant-phone mapping
- JSON logging with correlation fields
- OpenAI integration with markdown fence stripping

Left to build

- More tests (end-to-end chat flow)
- Time-based slot requests (e.g., "tomorrow at 3pm")
- Slot holds with expiry

Known issues

- No auth; wide open for demo purposes
- Debug print statements still active in llm.py

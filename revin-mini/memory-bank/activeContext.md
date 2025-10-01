# Active Context

Current focus

- LLM-powered chat-style booking flow fully operational with entity extraction, proposal generation, and reply classification.

Recent changes

- Added `TenantPhone` mapping model (phone → tenant_id lookup)
- Implemented OpenAI-based entity extraction in `extract_entities_from_text`
- Added service name normalization to handle case mismatches (e.g., "ac repair" → "AC Repair")
- Fixed JSON markdown fence parsing from OpenAI responses
- Added `/chat/inbound` and `/chat/reply` endpoints
- Wired LLM reply classification for YES/NO/unknown intents
- Added confirmation messages to booking responses

Next steps

- Clean up debug logging statements
- Add time-based intent parsing (e.g., "tomorrow at 3pm")
- Optional: add slot hold/reservation with expiry

Decisions

- Tenant resolved by phone number first, fallback to NLU extraction
- Service names normalized via mapping to match DB conventions
- OpenAI responses stripped of markdown code fences for JSON parsing
- Idempotency keys: `event_id:book_job` for bookings, `message_id:confirm` for confirmations

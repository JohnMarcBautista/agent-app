import os
from datetime import datetime

from app.schemas import LeadIn


def _fallback_message(lead: LeadIn, start: datetime, end: datetime) -> str:
    start_s = start.strftime("%a %b %d %-I:%M%p")
    end_s = end.strftime("%-I:%M%p")
    return (
        f"Hi {lead.name}, we can do {lead.service} on {start_s}-{end_s}. "
        f"Reply YES to confirm or RE-SCHEDULE for other times."
    )


def generate_booking_proposal(lead: LeadIn, start: datetime, end: datetime) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_message(lead, start, end)

    try:
        # Lazy import to avoid mandatory dependency during interviews
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        start_iso = start.isoformat()
        end_iso = end.isoformat()
        prompt = (
            "You are a helpful scheduling assistant. Write a concise, friendly SMS to the customer. "
            f"They requested: {lead.service}. Proposed slot: {start_iso} to {end_iso} (customer local time). "
            "Keep it under 200 characters. Ask them to reply YES to confirm or reply RESCHEDULE."
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You write concise SMS confirmations."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=120,
        )
        text = resp.choices[0].message.content.strip()
        return text or _fallback_message(lead, start, end)
    except Exception:
        return _fallback_message(lead, start, end)


def extract_entities_from_text(text: str) -> dict:
    """Extract tenant_id and service from free text via OpenAI; fallback to simple heuristics."""
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"[DEBUG] API key present: {api_key is not None}, text: '{text}'")
    if not api_key:
        # naive heuristics
        lower = text.lower()
        tenant_id = None
        service = None
        # heuristic: tokens like t_* map to tenant
        for token in lower.replace("\n", " ").split():
            if token.startswith("t_"):
                tenant_id = token
                break
        # simple service keyword samples
        for svc in ["ac repair", "plumbing", "electrical", "hvac", "installation"]:
            if svc in lower:
                service = svc.title()
                break
        return {"tenant_id": tenant_id, "service": service}

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        prompt = (
            "Extract tenant_id (string, like t_acme) and service (short phrase) from the user text. "
            "Respond strictly as JSON with keys tenant_id and service. Text: " + text
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=120,
        )
        content = resp.choices[0].message.content.strip()
        print(f"[DEBUG] OpenAI response: {content}")
        import json
        
        # Strip markdown code fences if present
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else content
            content = content.strip()

        data = json.loads(content)
        # Normalize service to match DB conventions
        service = data.get("service")
        if service:
            # Handle common service name mappings
            service_lower = service.lower()
            if "ac" in service_lower or "air conditioning" in service_lower:
                service = "AC Repair"
            elif "plumb" in service_lower:
                service = "Plumbing"
            elif "electr" in service_lower:
                service = "Electrical"
            elif "hvac" in service_lower:
                service = "HVAC"
            else:
                service = service.title()
        result = {"tenant_id": data.get("tenant_id"), "service": service}
        print(f"[DEBUG] Extracted: {result}")
        return result
    except Exception as e:
        print(f"[DEBUG] OpenAI failed: {type(e).__name__}: {str(e)[:200]}")
        return {"tenant_id": None, "service": None}


def classify_reply_text(text: str) -> str:
    """Classify free-text reply into yes/confirm, no/reschedule, or unknown."""
    api_key = os.getenv("OPENAI_API_KEY")
    lower = text.strip().lower()
    # fast-path heuristics
    if lower in {"yes", "y", "ok", "confirm", "sure", "book"}:
        return "yes"
    if "resched" in lower or lower in {"no", "n", "later", "another time"}:
        return "no"
    if not api_key:
        return "unknown"
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        prompt = (
            "Classify the user's SMS reply as one of: yes, no, unknown. "
            "Return only the label. Reply: " + text
        )
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=3,
        )
        label = resp.choices[0].message.content.strip().lower()
        return label if label in {"yes", "no"} else "unknown"
    except Exception:
        return "unknown"



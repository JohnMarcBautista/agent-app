from app.schemas import LeadIn


def classify_intent(lead: LeadIn) -> str:
    text = (lead.notes or "").lower()
    if "cancel" in text:
        return "cancel"
    if "resched" in text or "reschedule" in text:
        return "reschedule"
    return "book"



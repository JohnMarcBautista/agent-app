import uuid

from app.models import Job


def send_confirmation(job: Job) -> None:
    print(f"[SMS] {job.phone}: Booked {job.service} {job.slot_start:%m/%d %I:%M%p}")


def send_sms(phone: str, text: str) -> str:
    message_id = f"msg_{uuid.uuid4().hex}"
    print(f"[SMS->{phone}] {text} (message_id={message_id})")
    return message_id



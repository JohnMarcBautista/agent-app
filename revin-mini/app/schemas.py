from typing import Optional, Literal

from pydantic import BaseModel, Field


class LeadIn(BaseModel):
    event_id: str
    tenant_id: str
    name: str
    phone: str
    service: str
    address: Optional[str] = None
    notes: Optional[str] = None


class Slot(BaseModel):
    start: str
    end: str


class JobOut(BaseModel):
    job_id: str
    tenant_id: str
    customer_name: str
    phone: str
    service: str
    slot: Slot
    status: str
    source_event: str


class HealthOut(BaseModel):
    ok: bool = True


class HandoffOut(BaseModel):
    status: Literal["HANDOFF"] = "HANDOFF"
    reason: str


class NeedsDispatchOut(BaseModel):
    status: Literal["NEEDS_DISPATCH"] = "NEEDS_DISPATCH"


class ProposalOut(BaseModel):
    status: Literal["PROPOSED"] = "PROPOSED"
    proposal_id: str
    message_id: Optional[str] = None


class SmsCallbackIn(BaseModel):
    message_id: str
    from_phone: str
    body: str


class ChatInboundIn(BaseModel):
    from_phone: str
    text: str


class ChatInboundOut(BaseModel):
    status: str
    tenant_id: Optional[str] = None
    service: Optional[str] = None
    proposal_id: Optional[str] = None
    message: Optional[str] = None


class ChatReplyIn(BaseModel):
    from_phone: str
    text: str


class ChatReplyOut(BaseModel):
    status: str
    job_id: Optional[str] = None
    proposal_id: Optional[str] = None
    message: Optional[str] = None



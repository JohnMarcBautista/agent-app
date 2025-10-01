from datetime import datetime

from sqlalchemy import String, DateTime, Boolean, Text, Integer, Index
from sqlalchemy.orm import declarative_base, Mapped, mapped_column


Base = declarative_base()


class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True)
    customer_name: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)
    address: Mapped[str] = mapped_column(Text, nullable=True)
    service: Mapped[str] = mapped_column(String)
    slot_start: Mapped[datetime] = mapped_column(DateTime)
    slot_end: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default="BOOKED")
    source_event_id: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)


Index("idx_jobs_tenant_created", Job.tenant_id, Job.created_at)


class Capacity(Base):
    __tablename__ = "capacity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True)
    service: Mapped[str] = mapped_column(String)
    start_dt: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_dt: Mapped[datetime] = mapped_column(DateTime)
    booked_bool: Mapped[bool] = mapped_column(Boolean, default=False)


Index("idx_capacity_tenant_service_start", Capacity.tenant_id, Capacity.service, Capacity.start_dt)


class Idempotency(Base):
    __tablename__ = "idempotency"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    job_id: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Proposal(Base):
    __tablename__ = "proposals"

    proposal_id: Mapped[str] = mapped_column(String, primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True)
    customer_name: Mapped[str] = mapped_column(String)
    phone: Mapped[str] = mapped_column(String)
    address: Mapped[Text] = mapped_column(Text, nullable=True)
    service: Mapped[str] = mapped_column(String)
    slot_start: Mapped[datetime] = mapped_column(DateTime)
    slot_end: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String, default="PROPOSED")
    message_id: Mapped[str] = mapped_column(String, index=True, nullable=True)
    source_event_id: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)

Index("idx_proposals_tenant_created", Proposal.tenant_id, Proposal.created_at)


class TenantPhone(Base):
    __tablename__ = "tenant_phone"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    phone: Mapped[str] = mapped_column(String, index=True)
    tenant_id: Mapped[str] = mapped_column(String, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)

Index("idx_tenant_phone_unique_phone", TenantPhone.phone, unique=True)



from sqlalchemy import Boolean, Column, Date, DateTime, Enum, Float, Integer, JSON, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.enums.case import CasePriorityEnum, CaseStatusEnum, CaseTypeEnum


class Case(Base):
    __tablename__ = "case"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    start_date = Column(Date, nullable=False)
    # Secure, human-friendly case number (auto-generated, unique)
    case_no = Column(String(15), nullable=False, unique=True, index=True)
    case_type: Column = Column(
        Enum(CaseTypeEnum, name='case_type_new_enum'),
        nullable=True
    )
    priority: Column = Column(
        Enum(CasePriorityEnum, name='case_priority_new_enum'),
        nullable=True
    )
    status: Column = Column(
        Enum(CaseStatusEnum, name='case_status_new_enum'),
        nullable=False,
        default=CaseStatusEnum.OPEN
    )
    summary: Column = Column(JSON, nullable=True)
    analytics_data = Column(JSON, nullable=True)
    is_match_confirmed = Column(Boolean, nullable=False, default=False, server_default="false")
    is_kyc_completed = Column(Boolean, nullable=False, default=False, server_default="false")
    is_triage = Column(Boolean, nullable=False, default=False, server_default="false")
    is_onboarding_completed = Column(Boolean, nullable=False, default=False, server_default="false")
    is_initial_payment_completed = Column(Boolean, nullable=False, default=False, server_default="false")
    is_lawyer_assigned = Column(Boolean, nullable=False, default=False, server_default="false")
    is_profile_card_sent = Column(Boolean, nullable=False, default=False, server_default="false")
    is_ai_summary_generated = Column(Boolean, nullable=False, default=False, server_default="false")
    total_paid_amount = Column(Float, nullable=False, default=0, server_default="0")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    is_no_interest_notified = Column(Boolean, nullable=False, default=False, server_default="false")
    is_alignment_check_hold = Column(Boolean, nullable=False, default=False, server_default="false")
    match_confirmed_at = Column(DateTime(timezone=True), server_default=None, nullable=True)
    kyc_completed_at = Column(DateTime(timezone=True), nullable=True)
    profile_card_sent_at = Column(DateTime(timezone=True), nullable=True)
    lawyer_assigned_at = Column(DateTime(timezone=True), nullable=True)
    initial_payment_completed_at = Column(DateTime(timezone=True), nullable=True)
    onboarding_completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    case_customers = relationship("CaseCustomer", back_populates="case")
    case_resolves = relationship("CaseResolve", back_populates="case")
    case_triages = relationship("CaseTriage", back_populates="case")
    timeline_events = relationship("TimelineEvent", back_populates="case")
    case_lawyers = relationship("CaseLawyer", back_populates="case")
    case_engages = relationship("CaseEngage", back_populates="case")
    matches = relationship("Match", back_populates="case")
    invoices = relationship("Invoice", back_populates="case")
    analytics_events = relationship("AnalyticsEvent", back_populates="case")

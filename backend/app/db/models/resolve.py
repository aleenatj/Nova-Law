from sqlalchemy import Boolean, Column, Date, DateTime, Enum, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.enums.case import CaseTypeEnum
from app.enums.resolve import ResolveStatusEnum


class Resolve(Base):
    __tablename__ = "resolve"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    resolve_date = Column(Date, nullable=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=True)
    result_reference_id = Column(String(255), nullable=True)
    result_version = Column(String(50), nullable=True)
    status: Column = Column(
        Enum(ResolveStatusEnum, name="resolve_status_enum", values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
        default=ResolveStatusEnum.IN_PROGRESS
    )
    title = Column(String(255), nullable=True)
    questions_answered = Column(Integer, nullable=True)
    customer_name = Column(String(250), nullable=True)
    partner_name = Column(String(250), nullable=True)
    customer_email = Column(String(255), nullable=True)
    finance_flag = Column(Boolean, nullable=False, default=False)
    case_type: Column = Column(
        Enum(CaseTypeEnum, name='case_type_new_enum'),
        nullable=True,
        default=CaseTypeEnum.FAMILY_LAW,
        server_default="FAMILY_LAW"
    )
    recommended_approach = Column(String(255), nullable=True)
    personalised_ai_recommendation = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", back_populates="resolves")
    customer = relationship("Customer", back_populates="resolves")
    resolve_question_answers = relationship("ResolveQuestionAnswers", back_populates="resolve")
    case_resolves = relationship("CaseResolve", back_populates="resolve")

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.enums.triage import TriageStatusEnum


class Triage(Base):
    __tablename__ = "triage"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customer.id"), nullable=True)
    customer_email = Column(String(255), nullable=True)
    status: Column = Column(
        Enum(TriageStatusEnum, name="triage_status_enum", values_callable=lambda obj: [e.value for e in obj]),
        nullable=True,
        default=TriageStatusEnum.IN_PROGRESS,
    )
    questions_answered = Column(Integer, nullable=True)
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
    user = relationship("User", back_populates="triages")
    customer = relationship("Customer", back_populates="triages")
    triage_question_answers = relationship("TriageQuestionAnswers", back_populates="triage")
    case_triages = relationship("CaseTriage", back_populates="triage")

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Engage(Base):
    """Engage model for managing user engagements."""

    __tablename__ = "engage"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    is_kyc_completed = Column(Boolean, nullable=False, default=False, server_default="false")
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="engages")
    engage_question_answers = relationship(
        "EngageQuestionAnswers", back_populates="engage", cascade="all, delete-orphan"
    )
    case_engages = relationship(
        "CaseEngage", back_populates="engage", cascade="all, delete-orphan"
    )

from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class EngageQuestionAnswers(Base):
    """EngageQuestionAnswers model for linking engagements with question answers."""

    __tablename__ = "engage_question_answers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    engage_id = Column(Integer, ForeignKey("engage.id"), nullable=False)
    question_answer_id = Column(Integer, ForeignKey("question_answers.id"), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    engage = relationship("Engage", back_populates="engage_question_answers")
    question_answer = relationship("QuestionAnswers", back_populates="engage_question_answers")

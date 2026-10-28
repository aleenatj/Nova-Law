from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class TriageQuestionAnswers(Base):
    __tablename__ = "triage_question_answers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    triage_id = Column(Integer, ForeignKey("triage.id"), nullable=False)
    question_answer_id = Column(Integer, ForeignKey("question_answers.id"), nullable=False)
    score = Column(Float, nullable=False, default=0.0, server_default="0")
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
    triage = relationship("Triage", back_populates="triage_question_answers")
    question_answer = relationship("QuestionAnswers", back_populates="triage_question_answers")

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class QuestionAnswers(Base):
    __tablename__ = "question_answers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    version = Column(String(20), nullable=True)
    answer = Column(Text, nullable=True)
    question_identifier = Column(String(30), nullable=False)
    question_order = Column(Integer, nullable=False)
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
    resolve_question_answers = relationship("ResolveQuestionAnswers", back_populates="question_answer")
    engage_question_answers = relationship("EngageQuestionAnswers", back_populates="question_answer")
    triage_question_answers = relationship("TriageQuestionAnswers", back_populates="question_answer")

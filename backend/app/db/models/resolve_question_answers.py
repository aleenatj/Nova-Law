from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class ResolveQuestionAnswers(Base):
    __tablename__ = "resolve_question_answers"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    resolve_id = Column(Integer, ForeignKey("resolve.id"), nullable=False)
    question_answer_id = Column(Integer, ForeignKey("question_answers.id"), nullable=False)
    score = Column(Float, nullable=False)
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
    resolve = relationship("Resolve", back_populates="resolve_question_answers")
    question_answer = relationship("QuestionAnswers", back_populates="resolve_question_answers")

"""Engage feedback model. Option columns store integer keys; see app.enums.engage_feedback for labels."""

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.db.database import Base


class EngageFeedback(Base):
    """Engage feedback form submission (standalone; no relation to Engage). Option fields store integer keys (see enums.engage_feedback)."""

    __tablename__ = "engage_feedback"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    time_value_feedback = Column(Integer, nullable=True)
    completion_time = Column(Integer, nullable=True)
    session_count = Column(Integer, nullable=True)
    help_level = Column(Integer, nullable=True)
    helper_type = Column(JSONB, nullable=True)  # multi-select: list of enum keys e.g. [1, 2]
    help_reason = Column(JSONB, nullable=True)  # multi-select: list of enum keys e.g. [1, 2]
    preparedness_level = Column(Integer, nullable=True)
    age_range = Column(Integer, nullable=True)
    gender = Column(Integer, nullable=True)
    gender_other = Column(String(255), nullable=True)
    overall_experience = Column(Integer, nullable=True)
    improvement_feedback = Column(Text, nullable=True)
    recommendation_score = Column(Integer, nullable=True)  # 1-10

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

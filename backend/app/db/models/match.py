
from sqlalchemy import JSON, Boolean, Column, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.enums.match import MatchStatusEnum


class Match(Base):
    """Match model for lawyer-case-user matching."""

    __tablename__ = "match"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    lawyer_id = Column(Integer, ForeignKey("lawyer.id"), nullable=False)
    case_id = Column(Integer, ForeignKey("case.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    status: Column = Column(
        Enum(MatchStatusEnum, name="match_status_enum"),
        nullable=False,
        default=MatchStatusEnum.PENDING,
    )
    action_user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    action_date = Column(DateTime(timezone=True), nullable=True)
    declined_reason = Column(JSON, nullable=True)
    confirmed_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    confirmed_date = Column(DateTime(timezone=True), nullable=True)
    is_confirmed = Column(Boolean, nullable=False, default=False)
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
    lawyer = relationship("Lawyer", back_populates="matches")
    case = relationship("Case", back_populates="matches")
    user = relationship("User", foreign_keys=[user_id], back_populates="user_matches")
    action_user = relationship("User", foreign_keys=[action_user_id], back_populates="action_matches")
    confirmed_by_user = relationship("User", foreign_keys=[confirmed_by], back_populates="confirmed_by_user_matches")

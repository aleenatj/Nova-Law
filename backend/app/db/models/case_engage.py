from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class CaseEngage(Base):
    """CaseEngage model for linking cases with engagements."""

    __tablename__ = "case_engage"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("case.id"), nullable=False)
    engage_id = Column(Integer, ForeignKey("engage.id"), nullable=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    case = relationship("Case", back_populates="case_engages")
    engage = relationship("Engage", back_populates="case_engages")

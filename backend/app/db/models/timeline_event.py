
from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class TimelineEvent(Base):
    __tablename__ = "timeline_event"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, unique=True)
    case_id = Column(Integer, ForeignKey("case.id"), nullable=False)
    timeline_type_id = Column(Integer, ForeignKey("timeline_type.id"), nullable=False)
    action_user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    notify_user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    meta_data = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    case = relationship("Case", back_populates="timeline_events")
    timeline_type = relationship("TimelineType", back_populates="timeline_events")
    action_user = relationship("User", foreign_keys=[action_user_id])
    notify_user = relationship("User", foreign_keys=[notify_user_id])
    timeline_maps = relationship("TimelineMap", back_populates="timeline_event")

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class TimelineMap(Base):
    """TimelineMap model for mapping timeline events to related entities."""

    __tablename__ = "timeline_map"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    timeline_event_id = Column(Integer, ForeignKey("timeline_event.id"), nullable=False)
    timeline_type = Column(String(100), nullable=False)
    related_id = Column(String(100), nullable=False, index=True)
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
    timeline_event = relationship("TimelineEvent", back_populates="timeline_maps")

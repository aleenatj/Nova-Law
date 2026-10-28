"""Frontend analytics event stream (per session)."""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class AnalyticsEvent(Base):
    __tablename__ = "analytics_event"
    __table_args__ = (
        Index("ix_analytics_event_event_code_timestamp", "event_code", "timestamp"),
        Index(
            "ix_analytics_event_page_path_page_view",
            "page_path",
            postgresql_where=text("event_code = 'page_view'"),
        ),
        Index(
            "ix_analytics_event_properties_gin",
            "properties",
            postgresql_using="gin",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    event_code = Column(Text, nullable=False)
    anonymous_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(
        PG_UUID(as_uuid=True),
        ForeignKey("session.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    case_id = Column(
        Integer,
        ForeignKey("case.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    timestamp = Column(DateTime(timezone=True), nullable=False)
    received_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    page_url = Column(Text, nullable=True)
    page_path = Column(Text, nullable=True)
    page_title = Column(Text, nullable=True)
    referrer = Column(Text, nullable=True)
    properties = Column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )
    is_bot = Column(Boolean, nullable=False, server_default="false")
    is_internal = Column(Boolean, nullable=False, server_default="false")

    session = relationship("Session", back_populates="events")
    user = relationship("User", back_populates="analytics_events")
    case = relationship("Case", back_populates="analytics_events")

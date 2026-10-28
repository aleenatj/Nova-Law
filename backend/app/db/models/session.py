"""Frontend analytics: visitor identity mapping and session rows.

When you need both this model and SQLAlchemy's session class in the same module,
import the ORM as ``from app.db.models.session import Session as AnalyticsSessionRow``
or import SQLAlchemy as ``from sqlalchemy.orm import Session as SaSession``.
"""

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class Identity(Base):
    """Maps an anonymous visitor id to an application user (composite PK)."""

    __tablename__ = "identities"

    anonymous_id = Column(PG_UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    first_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    last_seen_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    user = relationship("User", back_populates="analytics_identities")


class Session(Base):
    """Client-reported analytics session (PostgreSQL table ``session``)."""

    __tablename__ = "session"
    __table_args__ = (Index("ix_session_source_medium", "source", "medium"),)

    id = Column(PG_UUID(as_uuid=True), primary_key=True, nullable=False)
    anonymous_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(
        Integer,
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    last_event_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    ended_at = Column(DateTime(timezone=True), nullable=True)
    entry_page = Column(Text, nullable=False, index=True)
    exit_page = Column(Text, nullable=True)
    source = Column(Text, nullable=True)
    medium = Column(Text, nullable=True)
    campaign = Column(Text, nullable=True)
    term = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    gclid = Column(Text, nullable=True)
    referrer = Column(Text, nullable=True)
    user_agent = Column(Text, nullable=True)
    device_type = Column(Text, nullable=True)
    browser = Column(Text, nullable=True)
    client_os = Column("os", Text, nullable=True)
    country = Column(Text, nullable=True)
    locale = Column(Text, nullable=True)
    client_timezone = Column("timezone", Text, nullable=True)
    event_count = Column(Integer, nullable=False, server_default="0")
    is_bot = Column(Boolean, nullable=False, server_default="false")

    user = relationship("User", back_populates="sessions")
    events = relationship(
        "AnalyticsEvent",
        back_populates="session",
        cascade="all, delete-orphan",
    )

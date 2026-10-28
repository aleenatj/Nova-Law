import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.enums.user import GenderEnum, StatusEnum


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


class User(Base):
    """User model for authentication and user management."""

    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), nullable=True)
    gender: Column = Column(
        Enum(GenderEnum, name="gender_enum"), nullable=True
    )
    gender_other = Column(String(50), nullable=True)
    password = Column(String(255), nullable=True)
    status: Column = Column(
        Enum(StatusEnum, name="user_status_enum"),
        nullable=False,
        default="Active",
    )
    reset_token_timestamp = Column(DateTime(timezone=True), nullable=True)
    has_marketing_email_consent = Column(Boolean, nullable=False, default=False, server_default="false")
    marketing_email_consent_datetime = Column(
        DateTime(timezone=True), nullable=True
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    first_touch_source = Column(Text, nullable=True)
    first_touch_medium = Column(Text, nullable=True)
    first_touch_campaign = Column(Text, nullable=True)
    first_touch_at = Column(DateTime(timezone=True), nullable=True)
    last_touch_source = Column(Text, nullable=True)
    last_touch_medium = Column(Text, nullable=True)
    last_touch_campaign = Column(Text, nullable=True)
    last_touch_at = Column(DateTime(timezone=True), nullable=True)
    traits = Column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
    )

    # Relationships
    user_roles = relationship(
        "UserRole", back_populates="user", cascade="all, delete-orphan"
    )
    customer = relationship(
        "Customer", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    lawyer = relationship(
        "Lawyer", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    resolves = relationship("Resolve", back_populates="user")
    triages = relationship("Triage", back_populates="user")
    events = relationship("Event", back_populates="user")
    engages = relationship("Engage", back_populates="user")
    invoices = relationship("Invoice", back_populates="action_user")
    action_timeline_events = relationship("TimelineEvent", foreign_keys="TimelineEvent.action_user_id", overlaps="action_user")
    notify_timeline_events = relationship("TimelineEvent", foreign_keys="TimelineEvent.notify_user_id", overlaps="notify_user")
    user_matches = relationship("Match", foreign_keys="Match.user_id", back_populates="user")
    action_matches = relationship("Match", foreign_keys="Match.action_user_id", back_populates="action_user")
    confirmed_by_user_matches = relationship("Match", foreign_keys="Match.confirmed_by", back_populates="confirmed_by_user")
    websocket_connections = relationship("WebSocketConnection", back_populates="user", cascade="all, delete-orphan")
    refresh_tokens = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")
    simple_auth_tokens = relationship("SimpleAuthToken", back_populates="user", cascade="all, delete-orphan")
    analytics_identities = relationship(
        "Identity", back_populates="user", cascade="all, delete-orphan"
    )
    sessions = relationship("Session", back_populates="user")
    analytics_events = relationship("AnalyticsEvent", back_populates="user")

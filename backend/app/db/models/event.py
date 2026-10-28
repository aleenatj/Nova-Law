"""
Event Model Module

This module defines the Event model for the event-driven architecture.
The Event model provides persistence and audit trail for all events in the system,
enabling event sourcing, debugging, and compliance requirements.

The Event model stores:
- Event metadata (ID, type, status, timestamps)
- Event payload (JSON data containing event details)
- Relationships to users and aggregates
- Processing status for monitoring and debugging

Author: Event-Driven Architecture Team
Version: 1.0.0
"""

import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class EventStatus(str, enum.Enum):
    """
    Event processing status enumeration.

    This enum defines the possible states of an event during its lifecycle:

    - PENDING: Event has been created but processing has not started
    - PROCESSED: All subscribers have completed successfully
    - FAILED: One or more subscribers failed during execution

    The status is used for monitoring, debugging, and ensuring event processing
    reliability. Failed events can be retried or investigated for root causes.
    """

    PENDING = "pending"  # Event created, processing not started
    PROCESSED = "processed"  # All subscribers completed successfully
    FAILED = "failed"  # One or more subscribers failed


class Event(Base):
    """
    Event model for storing and tracking all events in the system.

    This model provides the foundation for event sourcing and audit trails.
    Each event represents a business action that occurred in the system
    and contains all the data necessary to understand what happened.

    The Event model supports:
    - Event sourcing for rebuilding application state
    - Audit trails for compliance and debugging
    - Event replay for testing and data recovery
    - Monitoring and alerting on event processing

    Attributes:
        event_id: Unique identifier for the event (UUID)
        event_type: String identifier for the type of event
        aggregate_id: ID of the aggregate root (e.g., user ID, order ID)
        payload: JSON data containing all event details
        status: Current processing status (PENDING, PROCESSED, FAILED)
        user_id: ID of the user who triggered the event
        created_at: Timestamp when the event was created
        updated_at: Timestamp when the event was last updated
        user: Relationship to the User model
    """

    __tablename__ = "event"

    # Primary key - unique identifier for each event
    # Use String for SQLite compatibility, UUID for PostgreSQL
    event_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Event type - string identifier for categorizing events
    # Examples: "user_registered", "order_placed", "payment_processed"
    event_type = Column(String(100), nullable=False, index=True)

    # Aggregate ID - references the aggregate root this event belongs to
    # Examples: user ID for user events, case ID for case events, resolve ID for resolve events
    # All aggregate roots in this system use Integer primary keys
    aggregate_id = Column(Integer, nullable=True, index=True)

    # Event payload - JSON data containing all event details
    # This should include all necessary data to understand what happened
    payload = Column(JSON, nullable=False)

    # Processing status - tracks the current state of event processing
    status = Column(Enum(EventStatus), nullable=False, default=EventStatus.PENDING)

    # User ID - references the user who triggered this event
    # Useful for audit trails and user-specific event queries
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)

    # Creation timestamp - when the event was created
    # Automatically set by the database
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Update timestamp - when the event was last updated
    # Automatically set by the database
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        onupdate=func.now(),
    )

    # Relationships
    # Links to the user who triggered the event
    user = relationship("User", back_populates="events")

    def __repr__(self):
        """
        String representation of the Event model.

        Returns:
            str: Human-readable representation of the event
        """
        return f"<Event(event_id={self.event_id}, event_type={self.event_type}, status={self.status})>"

    def to_dict(self):
        """
        Convert the event to a dictionary representation.

        This method is useful for serialization, logging, and API responses.

        Returns:
            dict: Dictionary representation of the event
        """
        return {
            "event_id": str(self.event_id),
            "event_type": self.event_type,
            "aggregate_id": self.aggregate_id,
            "payload": self.payload,
            "status": self.status.value,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def create_event(
        cls,
        event_type: str,
        aggregate_id: int | None = None,
        payload: dict | None = None,
        user_id: int | None = None,
    ):
        """
        Factory method to create a new event.

        This method provides a convenient way to create events with proper
        initialization and validation.

        Args:
            event_type (str): Type of the event
            aggregate_id (int, optional): ID of the aggregate root
            payload (dict, optional): Event data
            user_id (int, optional): ID of the user who triggered the event

        Returns:
            Event: Newly created event instance
        """
        return cls(
            event_type=event_type,
            aggregate_id=aggregate_id,
            payload=payload or {},
            user_id=user_id,
            status=EventStatus.PENDING,
        )

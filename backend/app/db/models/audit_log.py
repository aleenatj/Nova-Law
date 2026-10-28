"""Audit Log model for tracking all data changes."""

from sqlalchemy import Column, DateTime, Enum, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.db.database import Base
from app.enums.audit import AuditActionEnum


class AuditLog(Base):
    """
    Audit Log model for tracking all data changes in the system.
    
    This model captures:
    - What table was changed
    - What record was changed (by ID)
    - What action was performed (CREATE, UPDATE, DELETE)
    - Who made the change (user_id)
    - What the old values were (for UPDATE and DELETE)
    - What the new values are (for CREATE and UPDATE)
    - Which fields were changed (for UPDATE)
    - When the change occurred
    - Request metadata (IP address, user agent)
    - Additional context (metadata)
    """

    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    
    # What was changed
    table_name = Column(String(100), nullable=False, index=True)
    record_id = Column(Integer, nullable=False, index=True)
    
    # What action
    action = Column(
        Enum(AuditActionEnum, name="audit_action_enum"),
        nullable=False
    )
    
    # Who made the change
    user_id = Column(Integer, nullable=True, index=True)
    
    # Change data (using JSONB for PostgreSQL for better query performance)
    old_values = Column(JSONB, nullable=True)  # Before state
    new_values = Column(JSONB, nullable=True)  # After state
    changed_fields = Column(JSONB, nullable=True)  # List of changed field names
    
    # When
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Request metadata
    ip_address = Column(String(45), nullable=True)  # Supports IPv6
    user_agent = Column(String(500), nullable=True)
    
    # Additional context
    extra_metadata = Column(JSONB, nullable=True)

    # Composite indexes for common query patterns
    __table_args__ = (
        Index("ix_audit_log_table_record", "table_name", "record_id"),
        Index("ix_audit_log_user_timestamp", "user_id", "timestamp"),
        Index("ix_audit_log_table_timestamp", "table_name", "timestamp"),
    )

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, table={self.table_name}, "
            f"record_id={self.record_id}, action={self.action})>"
        )


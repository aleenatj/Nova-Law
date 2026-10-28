"""Privacy deletion job queue."""

from sqlalchemy import CheckConstraint, Column, DateTime, Enum, Integer, Text, text
from sqlalchemy.sql import func

from app.db.database import Base
from app.enums.deletion_request import DeletionRequestStatus


class DeletionRequest(Base):
    __tablename__ = "deletion_request"
    __table_args__ = (
        CheckConstraint(
            "subject_type IN ('user_id', 'session_id', 'anonymous_id')",
            name="ck_deletion_request_subject_type",
        ),
    )

    request_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    requested_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    subject_type = Column(Text, nullable=False)
    subject_id = Column(Text, nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(
        Enum(
            DeletionRequestStatus,
            name="deletion_request_status_enum",
            create_type=False,
            values_callable=lambda t: [e.value for e in t],
            validate_strings=True,
        ),
        nullable=False,
        server_default=text("'PENDING'::deletion_request_status_enum"),
        index=True,
    )

"""Enums for GDPR / privacy deletion_request rows (Postgres types already exist)."""

from enum import Enum


class DeletionRequestStatus(str, Enum):
    """Matches ``deletion_request_status_enum`` in the database."""

    PENDING = "PENDING"
    PROGRESS = "PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class DeletionRequestSubjectType(str, Enum):
    """Matches ``ck_deletion_request_subject_type`` allowed values."""

    USER_ID = "user_id"
    SESSION_ID = "session_id"
    ANONYMOUS_ID = "anonymous_id"

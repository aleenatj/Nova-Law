"""Audit log enums."""

from enum import Enum


class AuditActionEnum(str, Enum):
    """Enum for audit log action types."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


from enum import Enum


class ChatStatus(str, Enum):
    """Chat session statuses."""

    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"
    PENDING = "pending"


class MessageType(str, Enum):
    """Message types in chat."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    ERROR = "error"

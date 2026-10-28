"""AI agent related enums."""

from enum import Enum


class ActionEnum(str, Enum):
    """Action types."""

    PUSH = "push"
    HOLD = "hold"

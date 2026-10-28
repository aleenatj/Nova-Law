from enum import Enum


class ResolveStatusEnum(str, Enum):
    """Resolve status enum."""

    IN_PROGRESS = "In progress"
    COMPLETED = "Completed"


class ResolveListStatusEnum(str, Enum):
    """Enum for resolve list status filter."""
    ALL = "All"
    IN_PROGRESS = "In progress"
    COMPLETED = "Completed"
    MOVING_FORWARD = "Moving forward"

from enum import Enum


class TriageStatusEnum(str, Enum):
    """Triage status enum."""

    IN_PROGRESS = "In progress"
    COMPLETED = "Completed"


class TriageListStatusEnum(str, Enum):
    """Enum for triage list status filter."""

    ALL = "All"
    IN_PROGRESS = "In progress"
    COMPLETED = "Completed"
    MOVING_FORWARD = "Moving forward"

from enum import Enum


class MatchStatusEnum(str, Enum):
    """Match status enum."""

    PENDING = "Pending"
    INTERESTED = "Interested"
    DECLINED = "Declined"

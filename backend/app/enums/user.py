from enum import Enum


class StatusEnum(str, Enum):
    """Common status enum used across multiple models."""

    ACTIVE = "Active"
    INACTIVE = "Inactive"


class GenderEnum(str, Enum):
    """Gender enum for users."""

    MALE = "Male"
    FEMALE = "Female"
    # OTHER = "Other"
    NON_BINARY = "Non-Binary"
    PREFER_NOT_TO_SAY = "Prefer not to say" 


class PasswordStateEnum(str, Enum):
    """Password state enum for users."""

    CAN_CREATE = "can_create"
    CAN_UPDATE = "can_update"
    NOT_APPLICABLE = "not_applicable"

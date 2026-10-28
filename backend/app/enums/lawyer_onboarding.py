from enum import Enum


class LawyerOnboardingGenderEnum(str, Enum):
    """Gender enum for lawyer onboarding."""

    FEMALE = "Female"
    MALE = "Male"
    NON_BINARY = "Non-Binary"
    PREFER_NOT_TO_SAY = "Prefer not to say"


class RemoteConsultationEnum(str, Enum):
    """Remote consultation enum for lawyer onboarding."""

    YES = "Yes"
    NO = "No"


class LawyerOnboardingStatusEnum(str, Enum):
    """Status enum for lawyer onboarding."""

    NEW = "New"
    REVIEW = "Review"
    ONBOARDED = "Onboarded"
    REJECTED = "Rejected"

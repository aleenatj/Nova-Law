from enum import Enum


class CaseTypeEnum(str, Enum):
    """Case type enum."""

    FAMILY_LAW = "Family law"


class CasePriorityEnum(str, Enum):
    """Case priority enum."""

    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class CaseStatusEnum(str, Enum):
    """Case status enum."""

    OPEN = "Open"
    CLOSED = "Closed"
    ARCHIVED = "Archived"


class CaseStatusFilterEnum(str, Enum):
    """Case status filter enum for filtering cases by completion status."""

    ALL = "All"
    CASE_OPENED = "Case Opened"
    KYC_COMPLETED = "KYC Completed"
    MATCH_CONFIRMED = "Match Confirmed"
    PROFILE_CARD_SENT = "Profile Card Sent"
    LAWYER_ASSIGNED = "Lawyer Assigned"
    INITIAL_PAYMENT_COMPLETED = "Initial Payment Completed"
    ONBOARDING_COMPLETED = "Onboarding Completed"

class CaseCategoryEnum(str, Enum):
    """Case category enum for filtering cases by lawyer assignment status."""

    ALL = "All"
    MY_CASES = "My Cases"
    MATCHED_CASES = "Matched Cases"
    MISSED_CASES = "Missed Cases"


class CaseIntentEnum(str, Enum):
    """Case intent enum for filtering cases by intent."""

    ALL = "All"
    HIGH_INTENT = "High Intent"
    LOW_INTENT = "Low Intent"
"""Enum definitions for the Nova Law AI application.
Organized by domain/feature for better maintainability.
"""

# User and Authentication enums
# AI Agent enums
from .agents import AgentType

# Audit enums
from .audit import AuditActionEnum
from .auth import Permission

# Case and Resolve enums
from .case import CasePriorityEnum, CaseStatusEnum, CaseStatusFilterEnum, CaseTypeEnum

# Chat and Messaging enums
from .chat import ChatStatus, MessageType

# Error and Logging enums
from .errors import ErrorCategory, ErrorCode, ErrorSeverity

# Engage feedback option maps (int key -> label; no DB enum)
from .engage_feedback import (
    AGE_RANGE_OPTIONS,
    COMPLETION_TIME_OPTIONS,
    GENDER_OPTIONS,
    HELP_LEVEL_OPTIONS,
    HELP_REASON_OPTIONS,
    HELPER_TYPE_OPTIONS,
    OVERALL_EXPERIENCE_OPTIONS,
    PREPAREDNESS_LEVEL_OPTIONS,
    RECOMMENDATION_SCORE_OPTIONS,
    SESSION_COUNT_OPTIONS,
    TIME_VALUE_FEEDBACK_OPTIONS,
)

# File upload enums
from .file_upload import ImageSize

# Formatter enums
from .base import NameExtractionOption

# Law Firm enums
from .law_firm import LawFirmStatusEnum

# Law Firm enums
from .law_firm_type import LawFirmType

# Lawyer enums
from .lawyer import (
    DRPreferenceEnum,
    DRTypeEnum,
    ExpertiseEnum,
    ExpertTypeEnum,
    LawyerConflictLevelEnum,
    LawyerStatusEnum,
    MatterTypeEnum,
    RegulatorEnum,
    RelationshipTypeEnum,
)
from .match import MatchStatusEnum
from .payment import InvoiceStatusEnum, PaymentStatusEnum

# API and System enums
from .system import APIVersion
from .user_role import UserRoleEnum

__all__ = [
    # Engage feedback options
    "AGE_RANGE_OPTIONS",
    "COMPLETION_TIME_OPTIONS",
    "GENDER_OPTIONS",
    "HELP_LEVEL_OPTIONS",
    "HELP_REASON_OPTIONS",
    "HELPER_TYPE_OPTIONS",
    "OVERALL_EXPERIENCE_OPTIONS",
    "PREPAREDNESS_LEVEL_OPTIONS",
    "RECOMMENDATION_SCORE_OPTIONS",
    "SESSION_COUNT_OPTIONS",
    "TIME_VALUE_FEEDBACK_OPTIONS",
    # Auth
    "APIVersion",
    # Agents
    "AgentType",
    # Audit
    "AuditActionEnum",
    # Case
    "CasePriorityEnum",
    "CaseStatusEnum",
    "CaseStatusFilterEnum",
    "CaseTypeEnum",
    # Chat
    "ChatStatus",
    "ErrorCategory",
    "ErrorCode",
    "ErrorSeverity",
    "MessageType",
    # Match
    "MatchStatusEnum",
    "Permission",
    # Lawyer
    "ExpertiseEnum",
    "ExpertTypeEnum",
    "LawyerConflictLevelEnum",
    "LawyerStatusEnum",
    "MatterTypeEnum",
    "RegulatorEnum",
    "RelationshipTypeEnum",
    "DRPreferenceEnum",
    "DRTypeEnum",
    "UserRoleEnum",
    # Law Firm
    "LawFirmStatusEnum",
    "LawFirmType",
    # File Upload
    "ImageSize",
    # Formatters
    "NameExtractionOption",
    # Payment
    "InvoiceStatusEnum",
    "PaymentStatusEnum",
]

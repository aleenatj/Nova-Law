"""Version 1 schemas for Nova Law AI Backend."""

from .auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    RefreshTokenRequest,
    ResendInitialPasswordRequest,
    ResendInitialPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ResetPasswordVerifyResponse,
    SetInitialPasswordRequest,
    SetInitialPasswordResponse,
    CreatePasswordRequest,
    CreatePasswordResponse,
    TokenResponse,
    UserLogin,
)
from .auth import (
    UserCreate as AuthUserCreate,
)
from .case import (
    CaseCreate,
    CaseListResponse,
    CaseResponse,
    CaseUpdate,
)
from .customer import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdate,
)
from .engage import (
    GetKycRequest,
    GetKycResponse,
)
from .triage import (
    GetTriageRequest,
    GetTriageResponse,
    TriageData,
    UpdateTriageRequest,
    UpdateTriageResponse,
    SubmitTriageRequest,
    SubmitTriageResponse,
    SubmitTriageResponseData,
)
from .law_firm import (
    LawFirmCreate,
    LawFirmListResponse,
    LawFirmResponse,
    LawFirmUpdate,
)
from .lawyer import (
    LawyerCreateRequest,
    LawyerCreateResponse,
    LawyerListResponse,
    LawyerResponse,
    LawyerSearchRequest,
    LawyerUpdateRequest,
    LawyerUpdateResponse,
)
from .lawyer_law_firm import (
    LawyerLawFirmCreate,
    LawyerLawFirmListResponse,
    LawyerLawFirmResponse,
)
from .question_answers import (
    QuestionAnswersCreate,
    QuestionAnswersListResponse,
    QuestionAnswersResponse,
    QuestionAnswersUpdate,
)
from .resolve import (
    ResolveCreate,
    ResolveListResponse,
    ResolveResponse,
    ResolveUpdate,
)
from .timeline_event import (
    GetTimelineEventResponse,
    TimelineEventDetails,
    TimelineEventUpdate,
)
from .user import (
    UserCreate,
    UserListResponse,
    UserProfileResponse,
    UserResponse,
    UserUpdate,
)
from .user_role import (
    UserRoleCreate,
    UserRoleListResponse,
    UserRoleResponse,
)
from .websocket import (
    WebSocketMessage,
)

__all__ = [
    "AuthUserCreate",
    "CaseCreate",
    "CaseListResponse",
    "CaseResponse",
    "CaseUpdate",
    "CustomerCreate",
    "CustomerListResponse",
    "CustomerResponse",
    "CustomerUpdate",
    "ForgotPasswordRequest",
    "ForgotPasswordResponse",
    "GetTimelineEventResponse",
    "GetKycRequest",
    "GetKycResponse",
    "GetTriageRequest",
    "GetTriageResponse",
    "TriageData",
    "UpdateTriageRequest",
    "UpdateTriageResponse",
    "SubmitTriageRequest",
    "SubmitTriageResponse",
    "SubmitTriageResponseData",
    "LawFirmCreate",
    "LawFirmListResponse",
    "LawFirmResponse",
    "LawFirmUpdate",
    "LawyerCreateRequest",
    "LawyerCreateResponse",
    "LawyerListResponse",
    "LawyerResponse",
    "LawyerSearchRequest",
    "LawyerUpdateRequest",
    "LawyerUpdateResponse",
    "LawyerLawFirmCreate",
    "LawyerLawFirmListResponse",
    "LawyerLawFirmResponse",
    "QuestionAnswersCreate",
    "QuestionAnswersListResponse",
    "QuestionAnswersResponse",
    "QuestionAnswersUpdate",
    "RefreshTokenRequest",
    "ResendInitialPasswordRequest",
    "ResendInitialPasswordResponse",
    "ResetPasswordRequest",
    "ResetPasswordResponse",
    "ResetPasswordVerifyResponse",
    "ResolveCreate",
    "SetInitialPasswordRequest",
    "SetInitialPasswordResponse",
    "CreatePasswordRequest",
    "CreatePasswordResponse",
    "ResolveListResponse",
    "ResolveResponse",
    "ResolveUpdate",
    "TimelineEventDetails",
    "TimelineEventUpdate",
    "TokenResponse",
    "UserCreate",
    "UserListResponse",
    "UserLogin",
    "UserProfileResponse",
    "UserResponse",
    "UserRoleCreate",
    "UserRoleListResponse",
    "UserRoleResponse",
    "UserUpdate",
    "WebSocketMessage",
]

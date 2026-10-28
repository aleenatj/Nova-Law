"""Schemas for Nova Law AI Backend."""

from .v1.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    RefreshTokenRequest,
    ResetPasswordRequest,
    ResetPasswordResponse,
    ResetPasswordVerifyResponse,
    TokenResponse,
    UserLogin,
)
from .v1.auth import (
    UserCreate as AuthUserCreate,
)
from .v1.customer import (
    CustomerCreate,
    CustomerListResponse,
    CustomerResponse,
    CustomerUpdate,
)
from .v1.law_firm import (
    LawFirmCreate,
    LawFirmListResponse,
    LawFirmResponse,
    LawFirmUpdate,
)
from .v1.lawyer import (
    LawyerCreateRequest,
    LawyerSearchRequest,
    LawyerUpdateRequest,
    LawyerListResponse,
    LawyerResponse,
)
from .v1.lawyer_law_firm import (
    LawyerLawFirmCreate,
    LawyerLawFirmListResponse,
    LawyerLawFirmResponse,
)
from .v1.user import (
    UserCreate,
    UserListResponse,
    UserProfileResponse,
    UserResponse,
    UserUpdate,
)
from .v1.user_role import (
    UserRoleCreate,
    UserRoleListResponse,
    UserRoleResponse,
)

__all__ = [
    # Auth schemas
    "AuthUserCreate",
    # Customer schemas
    "CustomerCreate",
    "CustomerListResponse",
    "CustomerResponse",
    "CustomerUpdate",
    "ForgotPasswordRequest",
    "ForgotPasswordResponse",
    # Law Firm schemas
    "LawFirmCreate",
    "LawFirmListResponse",
    "LawFirmResponse",
    "LawFirmUpdate",
    # Lawyer schemas
    "LawyerCreateRequest",
    "LawyerSearchRequest",
    "LawyerUpdateRequest",
    "LawyerListResponse",
    "LawyerResponse",
    # Lawyer Law Firm schemas
    "LawyerLawFirmCreate",
    "LawyerLawFirmListResponse",
    "LawyerLawFirmResponse",
    "RefreshTokenRequest",
    "ResetPasswordRequest",
    "ResetPasswordResponse",
    "ResetPasswordVerifyResponse",
    "TokenResponse",
    # User schemas
    "UserCreate",
    "UserListResponse",
    "UserLogin",
    "UserProfileResponse",
    "UserResponse",
    # User Role schemas
    "UserRoleCreate",
    "UserRoleListResponse",
    "UserRoleResponse",
    "UserUpdate",
]

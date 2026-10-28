from datetime import datetime
from typing import Any

from fastapi import Form
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.utils.validators import validate_password_strength

from .base import BaseResponse, DecryptedRequest, EncryptedResponse
from .resolve import CaseInfo as ResolveCaseInfo
from app.enums.user import PasswordStateEnum

class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="User's full name",
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="User password (min 8 characters, max 64 characters)",
    )


# class UserLogin(BaseModel):
#     """Schema for user login."""

#     username: str = Field(..., description="User name")
#     password: str = Field(..., description="User password")


class UserLogin(BaseModel):
    """Schema for user login."""

    username: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    resolve_id: str | None = Field(None, description="Resolve ID", examples=["d58161e55dc598535ab499eb84939aab"])

    @classmethod
    def as_form(
        cls, username: EmailStr = Form(...), password: str = Form(...), resolve_id: str | None = Form(None)
    ) -> "UserLogin":
        return cls(username=username, password=password, resolve_id=resolve_id)


class TokenDetails(BaseModel):
    """Schema for token details."""

    access_token: str = Field(
        ...,
        description="JWT access token",
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        ],
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token",
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        ],
    )
    token_type: str = Field(
        default="bearer", description="Token type", examples=["bearer/refresh"]
    )


class TokenResponse(BaseResponse):
    """Schema for token response."""

    data: TokenDetails | None = Field(..., description="Token details")


class RefreshTokenRequest(BaseModel):
    """Schema for refresh token request."""

    refresh_token: str = Field(..., description="JWT refresh token")


class UserResponse(EncryptedResponse):
    """Schema for user response with encrypted ID."""

    id: str = Field(..., description="User ID")
    email: EmailStr = Field(..., description="User email address")
    full_name: str = Field(..., description="User's full name")
    is_active: bool = Field(..., description="User active status")
    created_at: datetime = Field(..., description="User creation timestamp")

    model_config = ConfigDict(from_attributes=True)


# Password Reset Schemas
class ForgotPasswordRequest(BaseModel):
    """Schema for forgot password request."""

    email: EmailStr = Field(..., description="User email address")


class ForgotPasswordResponse(BaseResponse):
    """Schema for forgot password response."""

    pass
    # message: str = Field(..., description="Response message")


class ResetPasswordVerifyResponse(BaseModel):
    """Schema for reset password token verification response."""

    valid: bool = Field(..., description="Whether the token is valid")
    message: str = Field(..., description="Response message")
    email: str | None = Field(None, description="User email (only if token is valid)")


class ResetPasswordRequest(BaseModel):
    """Schema for reset password request."""

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="New password (min 8 characters, max 64 characters)",
        examples=["password123"],
    )

    @model_validator(mode="after")
    @classmethod
    def validate_password(cls, values: Any) -> Any:
        password = getattr(values, "new_password", None)
        if password is not None:
            result = validate_password_strength(password)
            if not result["is_valid"]:
                feedback_list = result.get("feedback", [])

                message = (
                    [{"success": False, "message": fb} for fb in feedback_list]
                    if feedback_list
                    else [
                        {
                            "success": False,
                            "message": "Please enter a stronger password",
                        }
                    ]
                )
                raise RequestValidationError(message)
        return values


class ResetPasswordResponse(BaseResponse):
    """Schema for reset password response."""

    pass
    # message: str = Field(..., description="Response message")


class UserData(EncryptedResponse):
    """Schema for user data in login response."""

    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    email: str = Field(..., description="User's email address")
    phone: str | None = Field(None, description="User's phone number")
    gender: str | None = Field(None, description="User's gender")
    user_id: str = Field(..., description="Encrypted user ID")
    role_code: str = Field(..., description="User's role code")
    available_roles: list[str] = Field(..., description="User's available roles")
    lawyer_id: str | None = Field(None, description="User's lawyer ID")
    customer_id: str | None = Field(None, description="User's customer ID")
    photo_urls: dict[str, str] | None = Field(None, description="User's photo URLs", example={
        "thumbnail": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/thumbnail.jpg",
        "medium": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/medium.jpg",
        "large": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/large.jpg"
    })

class LoginResponseData(BaseModel):
    """Schema for login response data."""

    access_token: str = Field(
        ...,
        description="JWT access token",
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        ],
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token",
        examples=[
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        ],
    )
    token_type: str = Field(
        default="bearer", description="Token type", examples=["bearer/refresh"]
    )
    redirect_path: str | None = Field(
        None, description="Frontend redirect path after successful login"
    )
    password_state: PasswordStateEnum | None = Field(
        None,
        description="Indicates the password setup state of the user",
        examples=[PasswordStateEnum.CAN_CREATE, PasswordStateEnum.CAN_UPDATE, PasswordStateEnum.NOT_APPLICABLE],
    )
    user_data: UserData = Field(..., description="User data")
    case: ResolveCaseInfo | None = Field(None, description="Case information")

class LoginResponse(BaseResponse[LoginResponseData]):
    """Schema for login response with token details and user data."""

    data: LoginResponseData = Field(..., description="Login response data")


class LoginWithTokenRequest(BaseModel):
    """Schema for login with token request."""

    token: str = Field(..., description="Magic link or login token")

class LogoutRequest(BaseModel):
    """Schema for logout request."""

    refresh_token: str = Field(..., description="JWT refresh token to invalidate")
    logout_all_devices: bool = Field(
        default=False,
        description="If True, logout from all devices. If False, logout only from current device"
    )


class LogoutResponse(BaseResponse):
    """Schema for logout response."""

    pass


class SetInitialPasswordRequest(BaseModel):
    """Schema for set initial password request."""

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="New password (min 8 characters, max 64 characters)",
        examples=["password123"],
    )

    @model_validator(mode="after")
    @classmethod
    def validate_password(cls, values: Any) -> Any:
        password = getattr(values, "new_password", None)
        if password is not None:
            result = validate_password_strength(password)
            if not result["is_valid"]:
                feedback_list = result.get("feedback", [])

                message = (
                    [{"success": False, "message": fb} for fb in feedback_list]
                    if feedback_list
                    else [
                        {
                            "success": False,
                            "message": "Please enter a stronger password",
                        }
                    ]
                )
                raise RequestValidationError(message)
        return values


class SetInitialPasswordResponse(BaseResponse):
    """Schema for set initial password response."""

    pass

class CreatePasswordResponse(BaseResponse):
    """Schema for create password response."""

    pass

class CreatePasswordRequest(BaseModel):
    """Schema for create password request."""
    """Schema for set initial password request."""

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="New password (min 8 characters, max 64 characters)",
        examples=["password123"],
    )

    @model_validator(mode="after")
    @classmethod
    def validate_password(cls, values: Any) -> Any:
        password = getattr(values, "new_password", None)
        if password is not None:
            result = validate_password_strength(password)
            if not result["is_valid"]:
                feedback_list = result.get("feedback", [])

                message = (
                    [{"success": False, "message": fb} for fb in feedback_list]
                    if feedback_list
                    else [
                        {
                            "success": False,
                            "message": "Please enter a stronger password",
                        }
                    ]
                )
                raise RequestValidationError(message)
        return values

class ResendInitialPasswordRequest(DecryptedRequest):
    """Schema for resend initial password request."""

    user_id: str = Field(..., description="User ID to resend initial password email", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])


class ResendInitialPasswordResponse(BaseResponse):
    """Schema for resend initial password response."""

    pass


class SendLoginLinkRequest(BaseModel):
    """Schema for send login link request."""

    user_name: EmailStr | str = Field(..., description="User email address or encrypted user ID", examples=["user@example.com", "Z0FBQUFBQm9rRHN4UU1UMVp"])
    case_id: str | None = Field(
        None,
        description="Optional encrypted case ID",
        examples=["Z0FBQUFBQm9rRHN4UU1UMVp"],
    )
    resolve_id: str | None = Field(
        None,
        description="Optional encrypted resolve ID",
        examples=["Z0FBQUFBQm9rRHN4UU1UMVp"],
    )


class SendLoginLinkResponse(BaseResponse):
    """Schema for send login link response."""

    pass


class GetEngageLinkRequest(DecryptedRequest):
    """Schema for get engage link request."""

    case_id: str = Field(..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])


class EngageUrlData(BaseModel):
    """Schema for engage link data."""

    engage_url: str = Field(..., description="Engage URL", examples=["https://engage.novalaw.co.uk/"])


class GetEngageLinkResponse(BaseResponse):
    """Schema for get engage link response."""
    data: EngageUrlData | None = Field(None, description="Engage URL data")


class GetVerifyCodeRequest(BaseModel):
    """Schema for get verify code request."""

    token: str = Field(..., description="Engage token")
    x_api_key: str = Field(..., description="X-API-KEY")


class VerifyEngageTokenRequest(BaseModel):
    """Schema for verify engage token request."""
    token: str = Field(..., description="Engage token", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])


class VerifyCodeData(BaseModel):
    """Schema for verify code data."""

    email: str = Field(..., description="Email", examples=["user@example.com"])
    first_name: str = Field(..., description="First name", examples=["John"])
    last_name: str = Field(..., description="Last name", examples=["Doe"])
    phone: str | None = Field(None, description="Phone", examples=["+44 7123456789"])
    gender: str | None = Field(None, description="Gender", examples=["Male", "Female", "Other"])
    gender_other: str | None = Field(None, description="Other gender", examples=["Other"])
    client: str = Field(..., description="client code", examples=["ef90-41cb-b8d8-31064f227dc5"])
    case_id: str = Field(..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])


class GetVerifyCodeResponse(BaseResponse):
    """Schema for get verify code response."""
    data: VerifyCodeData | None = Field(None, description="Verify code data")


class VerifyEngageTokenData(BaseModel):
    """Schema for verify engage token data."""
    engage_url: str | None = Field(None, description="Engage URL", examples=["https://engage.novalaw.co.uk/"])

class VerifyEngageTokenResponse(BaseResponse):
    """Schema for verify engage token response."""
    data: VerifyEngageTokenData | None = Field(None, description="Verify engage token data")
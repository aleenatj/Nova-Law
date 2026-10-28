from datetime import datetime
from typing import Any, ClassVar, TypeVar

from fastapi.exceptions import RequestValidationError
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    model_validator,
)

from app.enums.user import GenderEnum, StatusEnum
from app.utils.validators import validate_password_strength

from .base import BaseResponse, EncryptedResponse

ENCRYPTION_SALT: str | None = None

T = TypeVar("T")


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    first_name: str = Field(
        ..., min_length=1, max_length=100, description="User's first name"
    )
    last_name: str = Field(
        ..., min_length=1, max_length=100, description="User's last name"
    )
    email: EmailStr = Field(..., max_length=255, description="User email address")
    phone: str | None = Field(
        None,
        max_length=20,
        description="User phone number",
        examples=["+44 7123456789", "07123456789", "01234567890"],
    )
    gender: GenderEnum | None = Field(
        None, description="User gender/salutation", examples=["Female", "Male", "Other"]
    )
    gender_other: str | None = Field(None, max_length=50, description="Other gender specification")
    password: str | None = Field(
        None,
        min_length=8,
        max_length=64,
        description="User password (min 8 characters, max 64 characters, optional)",
    )
    status: StatusEnum = Field(
        StatusEnum.ACTIVE, description="User status", examples=["Active", "Inactive"]
    )


class UserUpdate(BaseModel):
    """Schema for updating user information."""

    first_name: str | None = Field(
        None, min_length=1, max_length=100, description="User's first name"
    )
    last_name: str | None = Field(
        None, min_length=1, max_length=100, description="User's last name"
    )
    email: EmailStr | None = Field(
        None, max_length=255, description="User email address"
    )
    phone: str | None = Field(
        None,
        max_length=20,
        description="User phone number",
        examples=["+44 7123456789", "07123456789", "01234567890"],
    )
    gender: GenderEnum | None = Field(
        None, description="User gender/salutation", examples=["Female", "Male", "Other"]
    )
    gender_other: str | None = Field(None, max_length=50, description="Other gender specification")
    status: StatusEnum | None = Field(
        None, description="User status", examples=["Active", "Inactive"]
    )
    password: str | None = Field(
        None,
        min_length=8,
        max_length=64,
        description="User password (min 8 characters, max 64 characters, optional)",
    )
    reset_token_timestamp: datetime | None = Field(
        None, description="Reset token timestamp"
    )


class UserCreateRequest(BaseModel):
    """Schema for user creation request."""

    first_name: str = Field(
        ..., min_length=1, max_length=100, description="User's first name"
    )
    last_name: str = Field(
        ..., min_length=1, max_length=100, description="User's last name"
    )
    email: EmailStr = Field(..., max_length=255, description="User email address")
    phone: str | None = Field(
        None,
        max_length=20,
        description="User phone number",
        examples=["+44 7123456789", "07123456789", "01234567890"],
    )
    gender: GenderEnum | None = Field(
        None, description="User gender/salutation", examples=["Female", "Male", "None-Binary", "Prefer not to say"]
    )
    # gender_other: str | None = Field(None, max_length=50, description="Other gender specification")
    status: StatusEnum = Field(
        StatusEnum.ACTIVE, description="User status", examples=["Active", "Inactive"]
    )


class UserUpdateRequest(BaseModel):
    """Schema for user update request."""

    first_name: str | None = Field(
        None, min_length=1, max_length=100, description="User's first name"
    )
    last_name: str | None = Field(
        None, min_length=1, max_length=100, description="User's last name"
    )
    email: EmailStr | None = Field(
        None, max_length=255, description="User email address"
    )
    phone: str | None = Field(
        None,
        max_length=20,
        description="User phone number",
        examples=["+44 7123456789", "07123456789", "01234567890"],
    )
    gender: GenderEnum | None = Field(
        None, description="User gender/salutation", examples=["Female", "Male", "Other"]
    )
    gender_other: str | None = Field(None, max_length=50, description="Other gender specification")
    status: StatusEnum | None = Field(
        None, description="User status", examples=["Active", "Inactive"]
    )


class UserResponse(EncryptedResponse):
    """Schema for user response."""

    id: str = Field(..., description="User ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    email: EmailStr = Field(..., description="User email address")
    phone: str | None = Field(
        None,
        description="User phone number",
        examples=["+44 7123456789", "07123456789", "01234567890"],
    )
    gender: GenderEnum | None = Field(
        None, description="User gender/salutation", examples=["Female", "Male", "Other"]
    )
    gender_other: str | None = Field(None, description="Other gender specification")
    status: str = Field(..., description="User status", examples=["Active", "Inactive"])
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User update timestamp")

    model_config = ConfigDict(from_attributes=True)


class UserCreateResponse(BaseResponse):
    """Schema for user creation response."""

    data: UserResponse = Field(..., description="Created user data")


class UserUpdateResponse(BaseResponse):
    """Schema for user update response."""

    data: UserResponse = Field(..., description="Updated user data")


class UserListResponse(EncryptedResponse):
    """Schema for user list response."""

    id: str = Field(..., description="User ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    email: EmailStr = Field(..., description="User email address")
    status: str = Field(..., description="User status", examples=["Active", "Inactive"])
    created_at: datetime = Field(..., description="User creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class PasswordChangeRequest(BaseModel):
    """Schema for password change request."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="New password (min 8 characters, max 64 characters)",
        examples=["string"],
    )

    @model_validator(mode="after")
    @classmethod
    def validate_password(cls, values: Any) -> Any:
        """Validate password strength using the same validation as reset password."""
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


class PasswordChangeResponse(BaseResponse):
    """Schema for password change response."""

    data: list = Field(
        default=[], description="Empty data for password change response"
    )


class UserProfileData(EncryptedResponse):
    """Schema for user profile data."""

    encryption_salt: ClassVar[str | None] = ENCRYPTION_SALT

    id: str = Field(..., description="User ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    email: EmailStr = Field(..., description="User email address")
    phone: str | None = Field(
        None,
        description="User phone number",
        examples=["+44 7123456789", "07123456789", "01234567890"],
    )
    gender: GenderEnum | None = Field(
        None, description="User gender/salutation", examples=["Female", "Male", "Other"]
    )
    gender_other: str | None = Field(None, description="Other gender specification")
    status: str = Field(..., description="User status", examples=["Active", "Inactive"])
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")
    role_code: str = Field(..., description="User role code")
    lawyer_id: str | None = Field(None, description="Lawyer ID if user is a lawyer")
    customer_id: str | None = Field(None, description="Customer ID if user is a customer")
    photo_urls: dict[str, str] | None = Field(None, description="Photo URLs for the user")
    available_roles: list[str] = Field(..., description="Available roles for the user")
    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseResponse):
    """Schema for user profile response."""

    data: UserProfileData = Field(..., description="User profile data")

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdateRequest(BaseModel):
    """Schema for updating user profile."""

    first_name: str = Field(
        ..., min_length=1, max_length=100, description="User's first name"
    )
    last_name: str = Field(
        ..., min_length=1, max_length=100, description="User's last name"
    )
    phone: str | None = Field(
        None,
        max_length=20,
        description="User phone number",
        examples=["+44 7123456789", "07123456789", "01234567890"],
    )
    gender: GenderEnum | None = Field(
        None, description="User gender/salutation", examples=["Female", "Male", "Other"]
    )
    gender_other: str | None = Field(None, max_length=50, description="Other gender specification")

    # @model_validator(mode="after")
    # def validate_gender_other(self) -> "UserProfileUpdateRequest":
    #     """Validate that gender_other is provided when gender is Other."""
    #     if self.gender_other and self.gender != GenderEnum.OTHER:
    #         raise RequestValidationError(
    #             [{"success": False, "message": "gender_other can only be provided when gender is 'Other'"}]
    #         )
    #     return self


class UserProfileUpdateResponse(BaseResponse):
    """Schema for user profile update response."""

    pass

from datetime import date, datetime
from typing import Any, ClassVar

from fastapi.exceptions import RequestValidationError
from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.utils.validators import validate_password_strength

from .auth import LoginResponseData
from .base import BaseResponse, DecryptedRequest, EncryptedResponse

ENCRYPTION_SALT: str | None = None


class CustomerRegistrationRequest(DecryptedRequest):
    """Schema for customer registration request."""

    encryption_salt: ClassVar[str | None] = ENCRYPTION_SALT

    first_name: str = Field(
        ..., min_length=1, max_length=100, description="Customer's first name"
    )
    last_name: str = Field(
        ..., min_length=1, max_length=100, description="Customer's last name"
    )
    email: EmailStr = Field(..., description="Customer's email address")
    phone: str | None = Field(
        None,
        max_length=20,
        description="Customer's phone number",
        examples=["+44 7123456789", "07123456789", "01234567890"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=64,
        description="Customer's password (min 8 characters, max 64 characters)",
        examples=["string"],
    )
    resolve_id: str | None = Field(
        None,
        description="Optional encrypted resolve ID to associate with the customer",
        examples=["Z0FBQUFBQm9rRHN4UU1UMVp"],
    )
    has_marketing_email_consent: bool = Field(
        False,
        description="Whether the customer has consented to receive marketing emails",
    )

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name_fields(cls, v: str) -> str:
        """Validate and trim name fields, rejecting spaces-only values."""
        if not isinstance(v, str):
            raise TypeError("Name must be a string")

        # Trim whitespace
        trimmed_value = v.strip()

        # Check if the trimmed value is empty (spaces-only)
        if not trimmed_value:
            raise ValueError("Name cannot be empty or contain only spaces")

        return trimmed_value

    @model_validator(mode="after")
    @classmethod
    def validate_password(cls, values: Any) -> Any:
        """Validate password strength using the same validation as reset password."""
        password = getattr(values, "password", None)
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


class CustomerInfo(EncryptedResponse):
    """Schema for customer information in registration response."""

    first_name: str = Field(..., description="Customer's first name")
    last_name: str = Field(..., description="Customer's last name")
    email: str = Field(
        ..., description="Customer's email address", examples=["user@example.com"]
    )
    phone: str | None = Field(
        None,
        description="Customer's phone number",
        examples=["+44 7123456789", "07123456789", "01234567890"],
    )
    customer_id: str = Field(
        ..., description="Encrypted customer ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"]
    )


class CaseInfo(EncryptedResponse):
    """Schema for case information in registration response."""

    case_id: str = Field(
        ..., description="Encrypted case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"]
    )
    case_no: str = Field(
        ...,
        description="Case number with prefix (e.g., CASE-100, CASE-101)",
        examples=["CASE-100", "CASE-101"],
    )
    case_type: str | None = Field(None, description="Case type", examples=["Family Law"])
    priority: str | None = Field(None, description="Case priority", examples=["Low", "Medium", "High"])
    start_date: date = Field(..., description="Case start date")
    status: str = Field(..., description="Case status", examples=["Open", "Closed"])
    created_at: datetime = Field(..., description="Case creation timestamp")
    updated_at: datetime = Field(..., description="Case update timestamp")


class TokenInfo(BaseModel):
    """Schema for token information in registration response."""

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
        default="Bearer",
        description="Token type for authentication",
        examples=["Bearer"],
    )


class CustomerRegistrationResponseData(BaseModel):
    """Schema for customer registration response data with grouped sections."""

    customer: CustomerInfo = Field(..., description="Customer information")
    case: CaseInfo | None = Field(
        None, description="Case information (if case created)"
    )
    login_data: LoginResponseData | None = Field(
        None, description="Authentication and user data"
    )


class CustomerRegistrationResponse(BaseResponse[CustomerRegistrationResponseData]):
    """Schema for customer registration API response."""

    data: CustomerRegistrationResponseData = Field(
        ..., description="Customer registration data"
    )

    model_config = ConfigDict(from_attributes=True)


class CustomerSimpleRegistrationRequest(DecryptedRequest):
    """Schema for customer simple registration request."""

    encryption_salt: ClassVar[str | None] = ENCRYPTION_SALT

    email: EmailStr = Field(
        ..., description="Customer email address collected during resolve flow"
    )
    resolve_id: str | None = Field(
        None,
        description="Optional encrypted resolve ID associated with the customer",
        examples=["Z0FBQUFBQm9rRHN4UU1UMVp"],
    )
    has_marketing_email_consent: bool = Field(
        False,
        description="Whether the customer has consented to receive marketing emails",
    )

# class CustomerSimpleRegistrationResponseData(BaseModel):
#     """Schema for customer simple registration response data."""

#     customer: CustomerInfo = Field(..., description="Customer information")
#     case: CaseInfo | None = Field(None, description="Case information (if case created)")

class CustomerSimpleRegistrationResponse(
    BaseResponse[CustomerRegistrationResponseData]
):
    """Schema for customer simple registration API response."""

    data: CustomerRegistrationResponseData = Field(
        ..., description="Simple registration data"
    )

class CustomerCreate(BaseModel):
    """Schema for creating a new customer."""

    status: str = Field("Active", description="Customer status")
    address_line1: str | None = Field(None, description="Address line 1")
    address_line2: str | None = Field(None, description="Address line 2")
    city: str | None = Field(None, description="City")
    state: str | None = Field(None, description="State")
    postal_code: str | None = Field(None, description="Postal code")
    country: str | None = Field(None, description="Country")
    user_id: int = Field(..., description="User ID")


class CustomerUpdate(BaseModel):
    """Schema for updating customer information."""

    status: str | None = Field(None, description="Customer status")
    address_line1: str | None = Field(None, description="Address line 1")
    address_line2: str | None = Field(None, description="Address line 2")
    city: str | None = Field(None, description="City")
    state: str | None = Field(None, description="State")
    postal_code: str | None = Field(None, description="Postal code")
    country: str | None = Field(None, description="Country")


class CustomerResponse(EncryptedResponse):
    """Schema for customer response."""

    id: int = Field(..., description="Customer ID")
    status: str = Field(..., description="Customer status")
    address_line1: str | None = Field(None, description="Address line 1")
    address_line2: str | None = Field(None, description="Address line 2")
    city: str | None = Field(None, description="City")
    state: str | None = Field(None, description="State")
    postal_code: str | None = Field(None, description="Postal code")
    country: str | None = Field(None, description="Country")
    user_id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Customer creation timestamp")
    updated_at: datetime = Field(..., description="Customer update timestamp")

    model_config = ConfigDict(from_attributes=True)


class CustomerListResponse(EncryptedResponse):
    """Schema for customer list response."""

    id: int = Field(..., description="Customer ID")
    status: str = Field(..., description="Customer status")
    city: str | None = Field(None, description="City")
    country: str | None = Field(None, description="Country")
    user_id: int = Field(..., description="User ID")
    created_at: datetime = Field(..., description="Customer creation timestamp")

    model_config = ConfigDict(from_attributes=True)

class TalkToNavigatorRequest(DecryptedRequest):
    """Schema for talk to navigator request."""

    case_id: str = Field(..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    phone: str = Field(
        ...,
        max_length=20,
        description="Phone number",
        examples=["+44 7123456789", "07123456789", "01234567890"],
    )

class TalkToNavigatorResponse(BaseResponse):
    """Schema for talk to navigator response."""
    pass

class TalkToLawyerRequest(DecryptedRequest):
    """Schema for talk to lawyer request."""

    case_id: str = Field(..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    lawyer_id: str = Field(..., description="Lawyer ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    phone: str  = Field(
        ...,
        max_length=20,
        description="Phone number",
        examples=["+44 7123456789", "07123456789", "01234567890"],
    )

class TalkToLawyerResponse(BaseResponse):
    """Schema for talk to lawyer response."""
    pass

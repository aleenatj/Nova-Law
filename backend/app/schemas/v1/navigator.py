from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
)

from app.enums.user import GenderEnum, StatusEnum

from .base import BaseRequest, BaseResponse, DecryptedRequest, EncryptedResponse

ENCRYPTION_SALT: str | None = None


class NavigatorSearchRequest(BaseRequest):
    """Schema for navigator search request."""

    search_term: str | None = Field(
        None,
        max_length=200,
        description="Search by name or email",
        examples=["John", "john@example.com"],
    )
    name: str | None = Field(
        None,
        max_length=200,
        description="Search by name (first name, last name, or full name)",
    )
    email: str | None = Field(
        None, max_length=255, description="Search by email address"
    )
    phone: str | None = Field(
        None,
        max_length=20,
        description="Search by phone number",
        examples=["+44 7123456789", "07123456789", "01234567890"],
    )
    status: StatusEnum | None = Field(
        None,
        description="Filter by navigator status",
        examples=[StatusEnum.ACTIVE, StatusEnum.INACTIVE],
    )


class NavigatorSearchItem(EncryptedResponse):
    """Schema for navigator search result item."""

    id: str = Field(..., description="User ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
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
    gender: str | None = Field(
        None, description="User gender", examples=["Female", "Male", "Other"]
    )
    gender_other: str | None = Field(None, max_length=50, description="Other gender specification")
    status: str = Field(..., description="User status", examples=["Active", "Inactive"])
    created_at: datetime = Field(..., description="User creation timestamp")
    updated_at: datetime = Field(..., description="User last update timestamp")
    needs_password_setup: bool = Field(..., description="Password set for navigator", example=True)

    model_config = ConfigDict(from_attributes=True)


class NavigatorSearchData(BaseModel):
    """Schema for navigator search data with pagination metadata."""

    total_count: int = Field(
        ..., description="Total number of matching navigator users"
    )
    records_in_page: int = Field(
        ..., description="Number of records in the current page"
    )
    users: list[NavigatorSearchItem] = Field(..., description="List of navigator users")


class NavigatorSearchResponse(BaseResponse[NavigatorSearchData]):
    """Schema for navigator search response."""

    data: NavigatorSearchData = Field(
        ..., description="Navigator search data with pagination"
    )


class NavigatorDetailsResponse(BaseResponse[NavigatorSearchItem]):
    """Schema for navigator details response."""

    data: NavigatorSearchItem = Field(..., description="Navigator user details")


class NavigatorUpdateRequest(DecryptedRequest):
    """Schema for navigator update request with decrypted user_id."""

    user_id: str = Field(
        ..., description="User ID to update (will be automatically decrypted)"
    )
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

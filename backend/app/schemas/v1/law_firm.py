from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.enums.law_firm_type import LawFirmType

from .base import BaseRequest, BaseResponse, DecryptedRequest, EncryptedResponse
from app.enums.law_firm import LawFirmStatusEnum

class LawFirmCreate(EncryptedResponse):
    """Schema for creating a new law firm."""


    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Law firm name",
        example="Smith & Associates Law Firm",
    )
    contact_person: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Contact person name",
        example="John Smith",
    )
    contact_no: str | None = Field(
        None,
        max_length=20,
        description="Contact phone number",
        example="+442071234567",
    )
    contact_email: EmailStr = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Contact email address",
        example="contact@smithlaw.com",
    )
    address_line_1: str | None = Field(
        None,
        max_length=255,
        description="Address line 1",
        example="123 Main Street",
    )
    address_line_2: str | None = Field(
        None,
        max_length=255,
        description="Address line 2",
        example="Suite 100",
    )
    city: str | None = Field(
        None, max_length=100, description="City", example="New York"
    )
    state: str | None = Field(None, max_length=100, description="State", example="NY")
    postal_code: str | None = Field(
        None, max_length=20, description="Postal code", example="10001"
    )
    country: str | None = Field(
        None, max_length=100, description="Country", example="USA"
    )
    logo: str | None = Field(
        None,
        max_length=500,
        description="Logo URL",
        example="https://example.com/logo.png",
    )
    about: str | None = Field(
        None,
        max_length=1500,
        description="About the law firm",
        example="Specializing in corporate law and litigation",
    )
    website_url: str | None = Field(
        None,
        max_length=500,
        description="Website URL",
        example="https://www.smithlaw.com",
    )
    engage_form_url: str | None = Field(
        None,
        max_length=500,
        description="Engage form URL",
        example="https://www.smithlaw.com/engage",
    )
    law_firm_type: LawFirmType | None = Field(
        None, description="Law firm type", example=LawFirmType.BOUTIQUE
    )
    status: LawFirmStatusEnum | None = Field(
        None, description="Law firm status", example=LawFirmStatusEnum.ACTIVE
    )


class LawFirmUpdate(DecryptedRequest):
    """Schema for updating law firm information."""

    id: str = Field(
        ..., description="Law firm ID (decrypted automatically from encrypted input)", example="Z0FBQUFBQm9rRHN4UU1UMVp"
    )

    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Law firm name",
        example="Smith & Associates Law Firm",
    )
    contact_person: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Contact person name",
        example="John Smith",
    )
    contact_no: str | None = Field(
        None,
        max_length=20,
        description="Contact phone number",
        example="+442071234567",
    )
    contact_email: EmailStr | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Contact email address",
        example="contact@smithlaw.com",
    )
    address_line_1: str | None = Field(
        None,
        max_length=255,
        description="Address line 1",
        example="123 Main Street",
    )
    address_line_2: str | None = Field(
        None,
        max_length=255,
        description="Address line 2",
        example="Suite 100",
    )
    city: str | None = Field(
        None, max_length=100, description="City", example="New York"
    )
    state: str | None = Field(None, max_length=100, description="State", example="NY")
    postal_code: str | None = Field(
        None, max_length=20, description="Postal code", example="10001"
    )
    country: str | None = Field(
        None, max_length=100, description="Country", example="USA"
    )
    logo: str | None = Field(
        None,
        max_length=500,
        description="Logo URL",
        example="https://example.com/logo.png",
    )
    about: str | None = Field(
        None,
        max_length=1500,
        description="About the law firm",
        example="Specializing in corporate law and litigation",
    )
    website_url: str | None = Field(
        None,
        max_length=500,
        description="Website URL",
        example="https://www.smithlaw.com",
    )
    engage_form_url: str | None = Field(
        None,
        max_length=500,
        description="Engage form URL",
        example="https://www.smithlaw.com/engage",
    )
    law_firm_type: LawFirmType | None = Field(
        None, description="Law firm type", example=LawFirmType.BOUTIQUE
    )
    status: LawFirmStatusEnum | None = Field(
        None, description="Law firm status", example=LawFirmStatusEnum.ACTIVE
    )


class LawFirmSearchRequest(BaseRequest):
    """Schema for law firm search request."""

    name: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="Search by law firm name (partial match)",
    )
    contact_person: str | None = Field(
        None,
        min_length=1,
        max_length=200,
        description="Search by contact person name (partial match)",
    )
    contact_email: str | None = Field(
        None,
        min_length=1,
        max_length=255,
        description="Search by contact email address (partial match)",
    )
    city: str | None = Field(
        None, max_length=100, description="Search by city (partial match)"
    )
    country: str | None = Field(
        None,
        max_length=100,
        description="Search by country (partial match)",
    )
    law_firm_type: LawFirmType | None = Field(
        None, description="Filter by law firm type"
    )
    status: LawFirmStatusEnum | None = Field(
        None, description="Filter by law firm status"
    )


class LawFirmDetailsResponse(EncryptedResponse):
    """Schema for law firm response."""

    id: str = Field(
        ..., description="Law firm ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"]
    )
    name: str = Field(..., min_length=1, max_length=100, description="Law firm name")
    contact_person: str = Field(
        ..., min_length=1, max_length=100, description="Contact person name"
    )
    contact_no: str | None = Field(
        None, max_length=20, description="Contact phone number"
    )
    contact_email: EmailStr = Field(
        ..., min_length=1, max_length=255, description="Contact email address"
    )
    address_line_1: str | None = Field(
        None, max_length=255, description="Address line 1"
    )
    address_line_2: str | None = Field(
        None, max_length=255, description="Address line 2"
    )
    city: str | None = Field(None, max_length=100, description="City")
    state: str | None = Field(None, max_length=100, description="State")
    postal_code: str | None = Field(None, max_length=20, description="Postal code")
    country: str | None = Field(None, max_length=100, description="Country")
    logos: dict[str, str] | None = Field(
        None,
        description="Logo URLs in different sizes (thumbnail, medium, large)"
    )
    about: str | None = Field(None, description="About the law firm")
    website_url: str | None = Field(None, max_length=500, description="Website URL")
    engage_form_url: str | None = Field(
        None, max_length=500, description="Engage form URL"
    )
    law_firm_type: LawFirmType | None = Field(None, description="Law firm type")
    status: LawFirmStatusEnum | None = Field(None, description="Law firm status")
    created_at: datetime = Field(..., description="Law firm creation timestamp")
    updated_at: datetime = Field(..., description="Law firm update timestamp")

    model_config = ConfigDict(from_attributes=True)


class LawFirmResponse(BaseResponse):
    """Schema for law firm response."""

    data: LawFirmDetailsResponse = Field(..., description="Law firm details")


class LawFirmListResponse(EncryptedResponse):
    """Schema for law firm list response."""

    id: str = Field(
        ..., description="Law firm ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"]
    )
    name: str = Field(..., min_length=1, max_length=100, description="Law firm name")
    contact_person: str = Field(
        ..., min_length=1, max_length=100, description="Contact person name"
    )
    contact_email: EmailStr = Field(
        ..., min_length=1, max_length=255, description="Contact email address"
    )
    city: str | None = Field(None, max_length=100, description="City")
    country: str | None = Field(None, max_length=100, description="Country")
    law_firm_type: LawFirmType | None = Field(None, description="Law firm type")
    created_at: datetime = Field(..., description="Law firm creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class LawFirmSearchItem(EncryptedResponse):
    """Schema for law firm search result item."""

    id: str = Field(
        ..., description="Law firm ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"]
    )
    name: str = Field(..., min_length=1, max_length=100, description="Law firm name")
    contact_person: str = Field(
        ..., min_length=1, max_length=100, description="Contact person name"
    )
    contact_no: str | None = Field(
        None, max_length=20, description="Contact phone number"
    )
    contact_email: EmailStr = Field(
        ..., min_length=1, max_length=255, description="Contact email address"
    )
    address_line_1: str | None = Field(
        None, max_length=255, description="Address line 1"
    )
    address_line_2: str | None = Field(
        None, max_length=255, description="Address line 2"
    )
    city: str | None = Field(None, max_length=100, description="City")
    state: str | None = Field(None, max_length=100, description="State")
    postal_code: str | None = Field(None, max_length=20, description="Postal code")
    country: str | None = Field(None, max_length=100, description="Country")
    logos: dict[str, str] | None = Field(
        None,
        description="Logo URLs in different sizes (thumbnail, medium, large)"
    )
    about: str | None = Field(None, description="About the law firm")
    website_url: str | None = Field(None, max_length=500, description="Website URL")
    engage_form_url: str | None = Field(
        None, max_length=500, description="Engage form URL"
    )
    law_firm_type: LawFirmType | None = Field(None, description="Law firm type")
    status: LawFirmStatusEnum | None = Field(None, description="Law firm status")
    created_at: datetime = Field(..., description="Law firm creation timestamp")
    updated_at: datetime = Field(..., description="Law firm update timestamp")

    model_config = ConfigDict(from_attributes=True)


class LawFirmSearchData(BaseModel):
    """Schema for law firm search data with pagination metadata."""

    total_count: int = Field(..., description="Total number of matching law firms")
    records_in_page: int = Field(
        ..., description="Number of records in the current page"
    )
    law_firms: list[LawFirmSearchItem] = Field(..., description="List of law firms")


class LawFirmSearchResponse(BaseResponse):
    """Schema for law firm search response."""

    data: LawFirmSearchData = Field(
        ..., description="Law firm search data with pagination"
    )


class LawFirmGetByIdResponse(BaseResponse):
    """Schema for law firm get by ID response."""

    data: LawFirmDetailsResponse = Field(..., description="Law firm details")

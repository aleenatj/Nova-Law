"""Lawyer onboarding schemas for API request/response."""

from datetime import datetime
from typing import Any, Optional
from fastapi import HTTPException, status

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.enums.lawyer_onboarding import (
    LawyerOnboardingGenderEnum,
    LawyerOnboardingStatusEnum,
    RemoteConsultationEnum,
)

from .base import BaseRequest, BaseResponse, DecryptedRequest, EncryptedResponse


class ValuesWithOtherInput(BaseModel):
    """Input for fields that support values + other (professional_status)."""
    values: Optional[list[str]] = Field(None, description="List of selected options")
    other: str | None = Field(None, description="Other custom value")
    # Other: str | None = Field(None, description="Other custom value (alternative field name)", exclude=True)
    
    @model_validator(mode='before')
    @classmethod
    def normalize_other_field(cls, data: Any) -> Any:
        """Normalize Other/other field - if Other is provided, use it for other."""
        if isinstance(data, dict):
            if "Other" in data and data["Other"] and not data.get("other"):
                data["other"] = data["Other"]
        return data

class SingleValueOrOtherInput(BaseModel):
    """Input for regulator - only single value allowed in values list."""
    values: Optional[list[str]] = Field(None, max_length=1, description="Single value only")
    other: str | None = Field(None, description="Other custom value")
    # Other: str | None = Field(None, description="Other custom value (alternative field name)", exclude=True)
    
    @model_validator(mode='before')
    @classmethod
    def normalize_other_field(cls, data: Any) -> Any:
        """Normalize Other/other field - if Other is provided, use it for other."""
        if isinstance(data, dict):
            if "Other" in data and data["Other"] and not data.get("other"):
                data["other"] = data["Other"]
        return data


class ClientTypeExpertiseInput(BaseModel):
    """Input for client type expertise (cohabitees or married_civil_partners)."""
    expertises: list[str] = Field(default_factory=list, description="List of selected expertise options")
    other: list[str] = Field(default_factory=list, description="List of custom 'other' expertise values")


class ServiceDetailsInput(BaseModel):
    """Input for service details with offers and expertise groups."""
    offers: list[str] = Field(default_factory=list, description="List of client types (MARRIED_CIVIL_PARTNERS, COHABITEES, PARENTAL_RELATIONSHIPS)")
    cohabitees: Optional[ClientTypeExpertiseInput] = Field(None, description="Cohabitees expertise details")
    married_civil_partners: Optional[ClientTypeExpertiseInput] = Field(None, description="Married couples and civil partners expertise details")


class LawyerOnboardingCreateRequest(BaseModel):
    """Schema for creating a new lawyer onboarding record."""
    
    # Required text fields
    first_name: str = Field(...,min_length=1, max_length=100, description="First name of the lawyer")
    last_name: str = Field(...,min_length=1, max_length=100, description="Last name of the lawyer")
    email: EmailStr = Field(..., min_length=1, max_length=255, description="Email address of the lawyer")
    phone: str = Field(...,min_length=1, max_length=20, description="Phone number of the lawyer")
    work_status: str = Field(...,min_length=1, max_length=100, description="Work status of the lawyer")
    city: str = Field(...,min_length=1, max_length=100, description="City where the lawyer is located")
    post_code: str = Field(...,min_length=1, max_length=20, description="Post code of the lawyer's location")
    
    # Optional text fields
    firm_name: Optional[str] = Field(None, max_length=100, description="Name of the law firm")
    gender: Optional[LawyerOnboardingGenderEnum] = Field(None, description="Gender of the lawyer")
    photo_url: Optional[str] = Field(None, description="URL to the lawyer's photo",example="https://example.com/photo.png")
    experience: Optional[float] = Field(None, ge=0, description="Years of experience")
    ncdr_description: Optional[str] = Field(None, description="NCDR description")
    compelling_quote: Optional[str] = Field(None, description="Compelling quote from the lawyer")
    remote_consultation: Optional[RemoteConsultationEnum] = Field(
        None, description="Whether the lawyer offers remote consultation"
    )
    
    # JSON fields with values + other (professional_status, regulator)
    professional_status: Optional[ValuesWithOtherInput] = Field(
        None, description="Professional status with values and other",
        examples=[{"values": ["Solicitor", "Cilex"], "other": "Other"}]
    )
    # Regulator - single value only (validated in service)
    regulator: Optional[SingleValueOrOtherInput] = Field(
        None, description="Regulator - single value in values OR other (not both)",
        examples=[{"values": ["CILEx Regulation"]}, {"other": "Custom Regulator"}]
    )
    
    # JSON fields with values only (ncdr_magic, accredited_specialist, consultation_offers)
    ncdr_magic: Optional[dict[str, list[str]]] = Field(
        None, description="NCDR magic options",
        examples=[{"values": ["DIY (unbundled support)", "Court"]}]
    )
    accredited_specialist: Optional[dict[str, list[str]]] = Field(
        None, description="Accredited specialist options",
        examples=[{"values": ["Resolution Accredited Specialist"]}]
    )
    accredited_specialism_other: Optional[list[str]] = Field(
        None, description="Accredited specialism other",
        examples=[["Other accredited specialism 1", "Other accredited specialism 2"]]
    )
    consultation_offers: Optional[dict[str, list[str]]] = Field(
        None, description="Consultation offers options",
        examples=[{"values": ["Free initial interview"]}]
    )
    
    # Special JSON field - service_details
    service_details: Optional[ServiceDetailsInput] = Field(
        None,
        description="Service details with offers and expertise groups",
        examples=[{
            "offers": ["MARRIED_CIVIL_PARTNERS", "COHABITEES"],
            "cohabitees": {
                "expertises": ["SEPARATION_AGREEMENTS", "COHABITATION_CHILD_ARRANGEMENTS"],
                "other": ["Custom expertise 1", "Custom expertise 2"]
            },
            "married_civil_partners": {
                "expertises": ["FINANCIAL_CLAIMS", "CHILD_ARRANGEMENTS"],
                "other": []
            }
        }]
    )
    
    @field_validator('service_details')
    @classmethod
    def validate_service_details_max_options(cls, v: Optional[ServiceDetailsInput]) -> Optional[ServiceDetailsInput]:
        """Validate that each client type has at most 5 total selections (expertises + other)."""
        if v is None:
            return v
        
        # Validate cohabitees
        if v.cohabitees:
            total_cohabitees = len(v.cohabitees.expertises) + len(v.cohabitees.other)
            if total_cohabitees > 5:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Maximum 5 selections allowed for Cohabitees (expertises + other values combined)."
                )
        
        # Validate married_civil_partners
        if v.married_civil_partners:
            total_married = len(v.married_civil_partners.expertises) + len(v.married_civil_partners.other)
            if total_married > 5:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Maximum 5 selections allowed for Married couples and civil partners (expertises + other values combined)."
                )
        
        return v


class LawyerOnboardingItem(EncryptedResponse):
    """Schema for a lawyer onboarding item in responses."""
    id: str = Field(..., description="Encrypted onboarding ID", examples=["q0FBQUFBQm9rRHN4UU1UMVp"])
    first_name: str = Field(..., description="First name", examples=["John"])
    last_name: str = Field(..., description="Last name", examples=["Doe"])
    email: str = Field(..., description="Email address", examples=["john.doe@example.com"])
    phone: str = Field(..., description="Phone number", examples=["+447911123456"])
    work_status: str = Field(..., max_length=100, description="Work status", examples=["I work for a legal firm - employed"])
    firm_name: str | None = Field(None, description="Firm name", examples=["Smith & Associates Law Firm"])
    city: str = Field(..., description="City", examples=["London"])
    post_code: str = Field(..., description="Post code", examples=["SW1A 1AA"])
    gender: LawyerOnboardingGenderEnum | None = Field(None, description="Gender", examples=["Female", "Male", "Non-Binary", "Prefer not to say"])
    photo_url: dict[str, str] | None = Field(
        None,
        description="Dictionary of photo URLs for different sizes",
        example={
            "thumbnail": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/thumbnail.jpg",
            "medium": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/medium.jpg",
            "large": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/large.jpg"
        },
    )
    professional_status: dict[str, Any] | None = Field(None, description="Professional status", examples=[{"values": ["Solicitor", "Cilex"], "other": "Other"}])
    experience: float | None = Field(None, description="Years of experience", examples=[4])
    service_details: dict[str, Any] | None = Field(None, description="Service details", examples=[{"Married couples and civil partners": ["Financial claims (overseas divorce)","Financial claims (overseas divorce)"],"Cohabitees": ["Financial claims (overseas divorce)","Financial claims (overseas divorce)"]}])
    ncdr_magic: dict[str, Any] | None = Field(None, description="NCDR magic", examples=[{"values": ["DIY (unbundled support)", "Court"]}])
    accredited_specialist: dict[str, Any] | None = Field(None, description="Accredited specialist info", examples=[{"values": ["Resolution Accredited Specialist"]}])
    regulator: dict[str, Any] | None = Field(None, description="Regulator info", examples=[{"values": ["CILEx Regulation"], "other": "Other"}])
    ncdr_description: str | None = Field(None, description="NCDR description", examples=["I am a specialist in financial claims (overseas divorce)"])
    compelling_quote: str | None = Field(None, description="Compelling quote", examples=["I am a specialist in financial claims (overseas divorce)"])
    remote_consultation: RemoteConsultationEnum | None = Field(None, description="Remote consultation preference", examples=["Yes", "No"])
    consultation_offers: dict[str, Any] | None = Field(None, description="Consultation offers", examples=[{"values": ["Free initial interview"]}])
    status: LawyerOnboardingStatusEnum = Field(..., description="Onboarding status", examples=["New", "Review", "Onboarded", "Rejected"])
    matter_types: list[str] | None = Field(None, description="Matter types", examples=["FINANCIAL_CLAIMS", "CHILDREN"])
    accredited_specialism_other: list[str] | None = Field(None, description="Accredited specialism other", examples=["Other accredited specialism 1", "Other accredited specialism 2"])
    created_at: datetime = Field(..., description="Created timestamp", examples=["2021-01-01T00:00:00Z"])
    updated_at: datetime | None = Field(None, description="Updated timestamp", examples=["2021-01-01T00:00:00Z"])


class LawyerOnboardingSearchRequest(BaseRequest):
    """Schema for searching lawyer onboarding records."""

    search_term: str | None = Field(None, description="Search by name or email")
    status: LawyerOnboardingStatusEnum | None = Field(None, description="Filter by status")


class LawyerOnboardingSearchData(BaseModel):
    """Schema for lawyer onboarding search data with pagination."""

    total_count: int = Field(..., description="Total number of records")
    records_in_page: int = Field(..., description="Number of records in current page")
    lawyers: list[LawyerOnboardingItem] = Field(..., description="List of onboarding records")


class LawyerOnboardingSearchResponse(BaseResponse[LawyerOnboardingSearchData]):
    """Schema for lawyer onboarding search response."""

    pass
class LawyerOnboardingDetailsResponse(BaseResponse[LawyerOnboardingItem]):
    """Schema for lawyer onboarding details response."""

    pass
class LawyerOnboardingCreateResponse(BaseResponse[LawyerOnboardingItem]):
    """Schema for lawyer onboarding create response."""
    pass


class LawyerOnboardingUpdateRequest(DecryptedRequest, LawyerOnboardingCreateRequest):
    """Schema for updating an existing lawyer onboarding record (PATCH - partial update).
    
    Inherits from DecryptedRequest for automatic ID decryption and LawyerOnboardingCreateRequest 
    with all required fields made optional.
    """
    
    # Required field for identifying the record to update (automatically decrypted)
    id: str = Field(..., description="Encrypted onboarding ID (decrypted automatically)", examples=["q0FBQUFBQm9rRHN4UU1UMVp"])
    
    # Override required fields from parent to make them optional for partial updates
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name of the lawyer")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name of the lawyer")
    email: Optional[EmailStr] = Field(None, max_length=255, description="Email address of the lawyer")
    phone: Optional[str] = Field(None, min_length=1, max_length=20, description="Phone number of the lawyer")
    work_status: Optional[str] = Field(None, min_length=1, max_length=100, description="Work status of the lawyer")
    city: Optional[str] = Field(None, min_length=1, max_length=100, description="City where the lawyer is located")
    post_code: Optional[str] = Field(None, min_length=1, max_length=20, description="Post code of the lawyer's location")
    
    # Additional field for updates (status can be changed during update)
    status: Optional[LawyerOnboardingStatusEnum] = Field(None, description="Onboarding status")


class LawyerOnboardingUpdateResponse(BaseResponse[LawyerOnboardingItem]):
    """Schema for lawyer onboarding update response."""
    pass

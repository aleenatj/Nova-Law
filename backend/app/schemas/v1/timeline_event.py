from datetime import datetime
from typing import Any, ClassVar, Annotated

from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field, model_validator, field_validator

from app.enums.lawyer import (
    ExpertTypeEnum,
    LawyerConflictLevelEnum,
    MatterTypeEnum,
    RelationshipTypeEnum,
    ExpertiseEnum,
    AccreditedSpecialismEnum,
)
from app.enums.user_role import UserRoleEnum
from app.schemas.v1.base import (
    BaseRequest,
    BaseResponse,
    DecryptedRequest,
    EncryptedResponse,
)
from app.schemas.v1.lawyer import LawFirmData


class TimelineEventBase(BaseModel):
    case_id: str = Field(..., description="ID of the case")
    timeline_type_id: str = Field(..., description="ID of the timeline type")
    action_user_id: str = Field(..., description="ID of the user who performed the action")
    notify_user_id: str | None = Field(None, description="ID of the user to notify")
    meta_data: dict[str, Any] | None = Field(..., description="Additional metadata for the event")


class TimelineEventUpdate(BaseModel):
    case_id: int | None = Field(None, description="ID of the case")
    event_type_id: int | None = Field(None, description="ID of the event type")
    action_user_id: int | None = Field(None, description="ID of the user who performed the action")
    notify_user_id: int | None = Field(None, description="ID of the user to notify")
    meta_data: str | None = Field(None, description="Additional metadata for the event")


class GetTimeLineEventsRequest(BaseRequest, DecryptedRequest):
    encryption_salt: ClassVar[str | None] = None
    case_id: str = Field(..., description="Case ID")
    role_code: str | None = Field(None, description="Role code")
    lawyer_id: str | None = Field(None, description="Lawyer ID for filtering")

    @model_validator(mode="after")
    @classmethod
    def validate_role_code_and_lawyer_id(cls, values: Any) -> Any:
        role_code = getattr(values, "role_code", None)
        lawyer_id = getattr(values, "lawyer_id", None)

        # Validate role_code if provided
        if role_code is not None:
            try:
                role_enum = UserRoleEnum.from_code(role_code)
            except (KeyError, ValueError):
                raise RequestValidationError([{"success": False, "message": "Invalid role code"}]) from None
            # If the role code is LAWYER, then lawyer_id is required
            if role_enum == UserRoleEnum.LAWYER:
                if lawyer_id is None:
                    raise RequestValidationError([{"success": False, "message": "lawyer_id is required when role_code is Lawyer"}]) from None

        # If lawyer_id is provided, role_code is required
        if lawyer_id is not None and role_code is None:
            raise RequestValidationError([{"success": False, "message": "role_code is required when lawyer_id is provided"}]) from None

        return values

    class Config:
        from_attributes = True

class MatchedLawyer(EncryptedResponse):
    lawyer_id: str = Field(..., description="Matched lawyer ID", examples=["SHpaLXRoODN3anVxejFFRk9GekhSRHd2S3NVUVRaUUlfQVE9P"])
    lawyer_name: str = Field(..., description="Matched lawyer name", examples=["John Doe"])

class TimelineEventDetails(TimelineEventBase, EncryptedResponse):
    id: str = Field(..., description="Timeline event id")
    timeline_type_name: str = Field(..., description="Timeline type name")
    version: int = Field(..., description="Version")
    action_user_id: str | None = Field(None, description="Action user id") # type: ignore[assignment]
    action_user_name: str | None = Field(None, description="Action user name")
    notify_user_id: str | None = Field(None, description="Notify user id")
    notify_user_name: str | None = Field(None, description="Notify user name")
    action_user_role: str | None = Field(None, description="Action user role")
    created_at: str = Field(..., description="Created at")
    updated_at: str | None = Field(None, description="Updated at")

    class Config:
        from_attributes = True


class GetTimelineEventResponse(BaseModel):
    case_number: str = Field(..., description="Case number", examples=["#001"])
    timeline_data: list[TimelineEventDetails] | None = Field(default=None, description="Timeline event details")
    matched_lawyers: list[MatchedLawyer] | None = Field(
        default=None,
        description="List of matched lawyers for the case"
    )
    total_count: int = Field(..., description="Total records")
    records_in_page: int = Field(..., description="Number of records in current page")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "timeline_data": [
                        {
                            "case_id": "SHpaLXRoODN3anVxejFFRk9GekhSRHd2S3NVUVRaUUlfQVE9P",
                            "timeline_type_id": "SHpaLXRoODN3anVxejFFRk9GekhSRHd2S3NVUVRaUUlfQVE9P",
                            "action_user_id": "SHpaLXRoODN3anVxejFFRk9GekhSRHd2S3NVUVRaUUlfQVE9P",
                            "notify_user_id": "SHpaLXRoODN3anVxejFFRk9GekhSRHd2S3NVUVRaUUlfQVE9P",
                            "meta_data": {
                                "action_by": "Nova",
                                "case_number": "001",
                                "timestamp": "2025-08-20 12:23:20.76738+05:30"
                            },
                            "id": "SHpaLXRoODN3anVxejFFRk9GekhSRHd2S3NVUVRaUUlfQVE9P",
                            "timeline_type_name": "case_opened",
                            "version": 1,
                            "action_user_name": "John Doe",
                            "notify_user_name": "John Doe",
                            "created_at": "2025-08-20 12:23:20.76738+05:30",
                            "updated_at": "2025-08-20 12:23:20.76738+05:30"
                        }
                    ],
                    "matched_lawyers": [
                        {"lawyer_id": "SHpaLXRoODN3anVxejFFRk9GekhSRHd2S3NVUVRaUUlfQVE9P", "lawyer_name": "Jane Smith"},
                        {"lawyer_id": "QXNvdGhlckVuY3J5cHRlZExhd3llcklEXzEyMw==", "lawyer_name": "Bob Johnson"},
                    ],
                    "total_count": 20,
                    "records_in_page": 10
                }
            ]
        }
    }


# Annotated type for non-empty strings
NonEmptyStr = Annotated[str, Field(min_length=1)]

class LawyerMatchCreateRequest(DecryptedRequest):
    """Request schema for creating lawyer matches."""
    encryption_salt: ClassVar[str | None] = None
    case_id: str = Field(..., description="Encrypted case ID", examples=["SHpaLXRoODN3anVxejFFRk9GekhSRHd2S3NVUVRaUUlfQVE9P"])
    # lawyers: list[str] = Field(..., description="List of encrypted lawyer IDs", min_items=1, examples=[["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P", "QXNvdGhlckVuY3J5cHRlZExhd3llcklEXzEyMw=="]])

    lawyers: Annotated[list[NonEmptyStr], Field(min_length=1, example=["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUU"])]  # List must have at least one non-empty string

    @field_validator("lawyers")
    @classmethod
    def check_no_empty_strings_and_duplicates(cls, v: list[str]) -> list[str]:
        # strip whitespace, check for empty strings, and ensure no duplicates
        seen: set[str] = set()
        for s in v:
            normalized = s.strip()
            if not normalized:
                raise RequestValidationError(
                    [{"success": False, "message": "All lawyer IDs must be non-empty strings"}]
                ) from None
            if normalized in seen:
                raise RequestValidationError(
                    [{"success": False, "message": "Duplicate lawyer IDs are not allowed"}]
                ) from None
            seen.add(normalized)
        return v

    class Config:
        from_attributes = True


class LawyerMatchData(EncryptedResponse):
    """Data schema for lawyer match response."""
    match_id: str = Field(..., description="Match ID", examples=["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P"])
    case_id: str = Field(..., description="Case ID", examples=["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P"])
    lawyer_id: str = Field(..., description="Lawyer ID", examples=["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P"])
    user_id: str = Field(..., description="User ID", examples=["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P"])
    status: str = Field(..., description="Match status", examples=["Pending"])
    action_user_id: str | None = Field(None, description="Action user ID", examples=["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P"])
    action_date: datetime | None = Field(None, description="Action date")
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")

    class Config:
        from_attributes = True


class MatchResponse(BaseModel):
   """Response schema for a single match."""
   error_list: list[str] | None = Field(None, description="Error list", examples=["Lawyer with ID SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P not found or not active"]   )
   invalid_lawyer_ids: list[str] | None = Field(None, description="Invalid lawyer IDs", examples=["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P"])


class LawyerMatchCreateResponse(BaseResponse):
    """Response schema for creating lawyer matches."""
    data: list[MatchResponse] = Field(..., description="Data")

    model_config = ConfigDict(
    json_schema_extra={
        "examples": [
            {
                "success": True,
                "message": "Lawyer matches created/updated successfully",
                "data": [
                    {
                        "error_list": [],
                        "invalid_lawyer_ids": [],
                        "created_lawyer_ids": [],
                        "updated_lawyer_ids": []
                    }
                ],
                "errors": []
            }
        ]
    }
)


class LawyerData(EncryptedResponse):
    """Data schema for lawyer response."""
    lawyer_id: str | None = Field(None, description="Lawyer ID", examples=["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P"])
    first_name: str | None = Field(None, description="Lawyer name", examples=["John Doe"])
    last_name   : str | None = Field(None, description="Lawyer name", examples=["John Doe"])
    email: str | None = Field(None, description="Lawyer email", examples=["john.doe@example.com"])
    phone_number: str | None = Field(None, description="Lawyer phone number", examples=["+1234567890"])
    gender: str | None = Field(
        None, description="User gender/salutation", examples=["Female", "Male", "Other"]
    )
    gender_other: str | None = Field(None, description="Other gender specification")
    address_line_1: str | None = Field(None, description="Lawyer address line 1", examples=["123 Main St"])
    address_line_2: str | None = Field(None, description="Lawyer address line 2", examples=["Apt 1"])
    city: str | None = Field(None, description="Lawyer city", examples=["New York"])
    county: str | None = Field(None, description="Lawyer county", examples=["NY"])
    country: str | None = Field(None, description="Country name", example="United Kingdom")
    postal_code: str | None = Field(None, description="Lawyer postal code", examples=["AXB-10001"])
    # country: str | None = Field(None, description="Lawyer country", examples=["USA"])
    user_id: str | None = Field(None, description="Lawyer user ID", examples=["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P"])
    # lawyer_type: str | None = Field(None, description="Lawyer type", examples=["Solicitor"])
    reg_no: str | None = Field(None, description="Lawyer registration number", examples=["1234567890"])
    regulator: str | None = Field(None, description="Lawyer regulator", examples=["SRA"])
    joined_at: datetime | None = Field(None, description="Lawyer joined at")
    left_at: datetime | None = Field(None, description="Lawyer left at")
    about: str | None = Field(None, description="Lawyer about")
    photo_urls: dict[str, str] | None = Field(
        None,
        description="Dictionary of photo URLs for different sizes",
        example={
            "thumbnail": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/thumbnail.jpg",
            "medium": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/medium.jpg",
            "large": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/large.jpg"
        },
    )
    # practice_areas: str | None = Field(None, description="Lawyer practice areas")
    # qualifications: str | None = Field(None, description="Lawyer qualifications")
    linkedin_url: str | None = Field(None, description="Lawyer LinkedIn URL")
    lawyer_status: str | None = Field(None, description="Lawyer status", examples=["Active"])
    created_at: datetime | None = Field(None, description="Lawyer created at")
    updated_at: datetime | None = Field(None, description="Lawyer updated at")
    experience: str | None = Field(
        None, description="Lawyer experience", example="10"
    )
    sra_number: str | None = Field(None, description="SRA number", example="SRA123456")
    bar_number: str | None = Field(None, description="Bar number", example="BAR123456")
    hourly_rate: int | None = Field(
        None, description="Hourly rate in GBP", example=150.0
    )
    charge_first_consultation: int | None = Field(
        None, description="Charge for first consultation in GBP", example=50.0
    )
    # accredited_specialisations: str | None = Field(
    #     None,
    #     description="Accredited specialisations",
    #     example="Family Law, Divorce, Child Custody",
    # )
    conflict_level_disinclination: LawyerConflictLevelEnum | None = Field(
        None,
        description="Conflict level disinclination",
        example=LawyerConflictLevelEnum.MEDIUM_CONFLICT,
    )
    expert_types: list[ExpertTypeEnum] = Field(
        description="List of expert types",
        example=[ExpertTypeEnum.SOLICITOR, ExpertTypeEnum.FAMILY_CONSULTANT],
    )
    relationship_types: list[RelationshipTypeEnum] = Field(
        description="List of relationship types",
        example=[RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS, RelationshipTypeEnum.COHABITEES],
    )
    matter_types: list[MatterTypeEnum] = Field(
        description="List of matter types",
        example=[MatterTypeEnum.FINANCIAL_CLAIMS, MatterTypeEnum.CHILDREN],
    )
    lawfirms: list[LawFirmData] | None = Field(
        None, description="Lawfirm data", example=LawFirmData(id="Z0FBQUFBQm9rRHN4UU1UMVp", name="Lawfirm Name")
    )
    expertises_all: list[ExpertiseEnum | str] | None = Field(
        description="List of expertises",
        example=[ExpertiseEnum.DIVORCE_AND_SEPARATION, ExpertiseEnum.SEPARATION_AGREEMENTS],
    )
    accreditations: list[AccreditedSpecialismEnum | str] | None = Field(
        description="List of accredited specialisms",
        example=[AccreditedSpecialismEnum.RESOLUTION_ACCREDITED_SPECIALIST, AccreditedSpecialismEnum.LAW_SOCIETY_ACCREDITED_SPECIALIST],
    )
    expert_types_all: list[ExpertTypeEnum | str] | None = Field(
        description="List of expert types",
        example=[ExpertTypeEnum.SOLICITOR, ExpertTypeEnum.FAMILY_CONSULTANT],
    )
    testimonial: str | None = Field(None, description="Lawyer testimonial", example="Experienced family law attorney")
    class Config:
        from_attributes = True


class GetMatchedLawyersResponse(BaseResponse):
    """Response schema for getting matched lawyers."""
    data: list[LawyerData] = Field(..., description="List of matched lawyers")
    total_count: int = Field(..., description="Total number of matched lawyers", examples=[20])
    records_in_page: int = Field(..., description="Number of records in current page", examples=[10])
    is_case_notified: bool = Field(
        default=False,
        description="Whether the case has been notified to the lawyers",
    )


class GetMatchedLawyersRequest(DecryptedRequest):
    """Request schema for creating lawyer matches."""

    case_id: str = Field(..., description="Encrypted case ID", examples=["SHpaLXRoODN3anVxejFFRk9GekhSRHd2S3NVUVRaUUlfQVE9P"])


class SendLawyerToCustomerRequest(LawyerMatchCreateRequest):
    """Request schema for sending lawyer to customer."""
    lawyers: Annotated[list[NonEmptyStr], Field(min_length=1, max_length=3, example=["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUU"])]  # List must have at least one non-empty string

class SendLawyerToCustomerResponse(BaseResponse):
    """Response schema for sending lawyer to customer."""
    data : list[str] | None = Field(None, description="Data", examples=["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P"])

class AcceptLawyerRequest(DecryptedRequest):
    """Schema for accepting lawyer request."""
    case_id: str = Field(..., description="Case ID", examples=["4eZ1ASaLikWyWGVqiGmuNg==a4ayc_80"])
    lawyer_id: str = Field(..., description="Lawyer ID", examples=["4eZ1ASaLikWyWGVqiGmuNg==a4ayc_80"])


class AcceptLawyerResponseData(EncryptedResponse):
    """Schema for accept lawyer response data."""
    case_id: str = Field(..., description="Case ID")
    lawyer_id: str = Field(..., description="Lawyer ID")


class AcceptLawyerResponse(BaseResponse):
    """Schema for accepting lawyer response."""
    data: AcceptLawyerResponseData | None = Field(None, description="Accept lawyer response data")


class MarkOnboardingCompletedRequest(DecryptedRequest):
    """Schema for marking onboarding completed request."""
    case_id: str = Field(..., description="Case ID", examples=["4eZ1ASaLikWyWGVqiGmuNg==a4ayc_80"])


class MarkOnboardingCompletedResponse(BaseResponse):
    """Schema for marking onboarding completed response."""
    pass


# Match Confirmed Lawyers Schemas
class MatchConfirmedLawyersRequest(DecryptedRequest):
    """Request schema for getting confirmed matched lawyers."""

    case_id: str = Field(
        ...,
        description="Encrypted case ID",
        examples=["SHpaLXRoODN3anVxejFFRk9GekhSRHd2S3NVUVRaUUlfQVE9P"],
    )

    class Config:
        from_attributes = True


class ConfirmedLawyerData(EncryptedResponse):
    """Data schema for confirmed lawyer response."""

    lawyer_id: str = Field(
        ...,
        description="Lawyer ID",
        examples=["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P"],
    )
    lawyer_name: str = Field(..., description="Lawyer full name", examples=["John Doe"])
    lawyer_photo_urls: dict[str, str] | None = Field(
        None,
        description="Dictionary of photo URLs for different sizes",
        example={
            "thumbnail": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/thumbnail.jpg",
            "medium": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/medium.jpg",
            "large": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/large.jpg"
        },
    )
    lawyer_experience: str | None = Field(
        None, description="Lawyer experience in years", examples=[5.5]
    )
    # lawyer_expert_type: list[str] = Field(
    #     default_factory=list,
    #     description="Lawyer expert types",
    #     examples=[["Family Law", "Divorce"]],
    # )
    lawyer_about: str | None = Field(
        None,
        description="Lawyer about/bio",
        examples=["Experienced family law attorney"],
    )
    lawyer_location: str | None = Field(
        None, description="Lawyer location", examples=["London, UK"]
    )
    # lawyer_specialization: str | None = Field(
    #     None,
    #     description="Lawyer specializations",
    #     examples=["Child Custody"],
    # )
    lawyer_expertises: list[ExpertiseEnum | str] | None = Field(
        None,
        description="List of lawyer expertises",
        example=[ExpertiseEnum.DIVORCE_AND_SEPARATION, ExpertiseEnum.SEPARATION_AGREEMENTS],
    )
    lawyer_accreditations: list[AccreditedSpecialismEnum | str] | None = Field(
        None,
        description="List of lawyer accreditations",
        example=[AccreditedSpecialismEnum.RESOLUTION_ACCREDITED_SPECIALIST, AccreditedSpecialismEnum.LAW_SOCIETY_ACCREDITED_SPECIALIST],
    )

    class Config:
        from_attributes = True


class MatchConfirmedLawyersResponse(BaseModel):
    """Response schema for confirmed matched lawyers."""

    total_count: int = Field(..., description="Total number of confirmed lawyers")
    records_in_page: int = Field(..., description="Number of records in current page")
    match_confirmed_lawyers: list[ConfirmedLawyerData] = Field(
        ..., description="List of confirmed lawyers"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "total_count": 2,
                    "records_in_page": 2,
                    "match_confirmed_lawyers": [
                        {
                            "lawyer_id": "SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P",
                            "lawyer_name": "John Doe",
                            "lawyer_photo_urls": {
                                "thumbnail": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/thumbnail.jpg",
                                "medium": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/medium.jpg",
                                "large": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/large.jpg"
                            },
                            "lawyer_experience": 5.5,
                            "lawyer_expert_type": ["Family Law", "Divorce"],
                            "lawyer_about": "Experienced family law attorney",
                            "lawyer_location": "London, UK",
                            "lawyer_specialization": "Child Custody",
                        }
                    ],
                }
            ]
        }
    }

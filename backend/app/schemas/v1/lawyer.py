from datetime import date, datetime
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, BeforeValidator, EmailStr, Field, PlainValidator, field_validator, model_validator, PrivateAttr, ValidationInfo
from starlette.exceptions import HTTPException

from app.enums.lawyer import (
    DRPreferenceEnum,
    ExpertTypeEnum,
    LawyerConflictLevelEnum,
    LawyerStatusEnum,
    MatterTypeEnum,
    RegulatorEnum,
    RelationshipTypeEnum,
    ExpertiseEnum,
    AccreditedSpecialismEnum,
)
from app.schemas.v1.base import BaseRequest, BaseResponse, EncryptedResponse
from app.schemas.v1.user import UserCreateRequest


def _convert_enum_key(enum_class: type[Enum]) -> BeforeValidator:
    """Create a validator that accepts enum keys and converts to enum instances.
    
    This validator accepts both enum keys (names) and enum values, converting
    keys to enum instances while preserving values for display. Automatically
    gets field name from ValidationInfo for better error messages.
    """
    def validator(v: str | Enum | None, info: ValidationInfo) -> Enum | None:
        # Get field name from ValidationInfo - available in Pydantic v2
        field_name = getattr(info, "field_name", None)
        
        if v is None:
            return None
        if isinstance(v, enum_class):
            return v
        # Try to find by name (key) only - enforce enum keys
        try:
            return enum_class[v]
        except KeyError:
            valid_keys = [member.name for member in enum_class]
            field_context = f" in field '{field_name}'" if field_name else ""
            raise HTTPException(
                status_code=400,
                detail=f"Invalid value '{v}'{field_context}. Must be one of enum keys: {valid_keys}"
            )
    return BeforeValidator(validator)


def _convert_enum_list(enum_class: type[Enum], expected_relationship_type: RelationshipTypeEnum | None = None) -> BeforeValidator:
    """Create a validator that accepts lists of enum keys and converts to enum instances.
    
    This validator processes each item in a list, accepting both enum keys (names)
    and enum values, converting keys to enum instances. Automatically gets field name
    from ValidationInfo for better error messages.
    
    Args:
        enum_class: The enum class to validate against
        expected_relationship_type: Optional relationship type to validate against
    """
    def validator(v: list[str | Enum] | None, info: ValidationInfo) -> list[Enum] | None:
        # Get field name from ValidationInfo - available in Pydantic v2
        field_name = getattr(info, "field_name", None)
        
        if v is None:
            return None
        if not isinstance(v, list):
            field_context = f" for field '{field_name}'" if field_name else ""
            raise HTTPException(
                status_code=400,
                detail=f"Expected a list{field_context}, got {type(v).__name__}"
            )
        result = []
        for item in v:
            if isinstance(item, enum_class):
                enum_item = item
            else:
                # Try to find by name (key) only - enforce enum keys
                try:
                    enum_item = enum_class[item]
                except KeyError:
                    valid_keys = [member.name for member in enum_class]
                    field_context = f" in field '{field_name}'" if field_name else ""
                    raise HTTPException(
                        status_code=400,
                        detail=f"Invalid value '{item}'{field_context}. Must be one of enum keys: {valid_keys}"
                    )
            
            # Validate relationship type if specified
            if expected_relationship_type is not None:
                if enum_item.relationship_type != expected_relationship_type:
                    field_context = f" in field '{field_name}'" if field_name else ""
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            f"{enum_item.name} does not belong to "
                            f"{expected_relationship_type.name}{field_context}. "
                            f"Expected relationship type: {expected_relationship_type.name}, "
                            f"got: {enum_item.relationship_type.name}"
                        )
                    )
            
            result.append(enum_item)
        return result
    return BeforeValidator(validator)



class LawFirmData(EncryptedResponse):
    """Schema for lawfirm data."""

    id: str = Field(..., description="Lawfirm ID", example="Z0FBQUFBQm9rRHN4UU1UMVp")
    name: str = Field(..., description="Lawfirm name", example="Lawfirm Name")
    logos: dict[str, str] | None = Field(
        None,
        description="Logo URLs in different sizes (thumbnail, medium, large)"
    )



def _real_expertises(expertises: list[ExpertiseEnum]) -> list[ExpertiseEnum]:
    """Exclude OTHER_* enum values."""
    return [e for e in expertises if not e.is_other()]


class ExpertiseGroup(BaseModel):
    """Schema for expertise group by relationship type."""
        
    _relationship_type: RelationshipTypeEnum | None = PrivateAttr(default=None)

    expertises: Annotated[list[ExpertiseEnum], _convert_enum_list(ExpertiseEnum)] = Field(
        default_factory=list,
        description="List of expertise enum values",
    )
    other: list[str] | None = Field(
        default_factory=list,
        description="List of free-text custom expertise values (required if 'Other' expertise is selected)",
        example=["Custom expertise 1", "Custom expertise 2"]
    )
    
    @model_validator(mode="after")
    def validate_group(self) -> "ExpertiseGroup":
        expertises = self.expertises
        other = self.other or []

        real_expertises = _real_expertises(expertises)

        if len(real_expertises) + len(other) > 5:
            raise HTTPException(
                status_code=400,
                detail="Maximum 5 expertises allowed per relationship type "
                    "(including custom 'other' values)"
            )

        if other and not any(e.is_other() for e in expertises):
            raise HTTPException(
                status_code=400,
                detail="Custom 'other' values require selecting the 'Other' option"
            )

        if len(set(other)) != len(other):
            raise HTTPException(
                status_code=400,
                detail="Duplicate 'other' expertise values are not allowed"
            )

        return self
    
class MarriedCivilPartnersExpertiseGroup(ExpertiseGroup):
    """Schema for Married and Civil Partners expertise group request."""
    expertises: Annotated[list[ExpertiseEnum], _convert_enum_list(ExpertiseEnum, RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS)] = Field(
        default_factory=list,
        description="List of expertise enum values",
        json_schema_extra={
            "enum": [e.name for e in ExpertiseEnum if e.relationship_type == RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS],
            "type": "string",
            "x-availableOptions": {e.name: e.value for e in ExpertiseEnum if e.relationship_type == RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS}
        }
    )

class CohabiteesExpertiseGroup(ExpertiseGroup):
    """Schema for cohabitees expertise group request."""
    expertises: Annotated[list[ExpertiseEnum], _convert_enum_list(ExpertiseEnum, RelationshipTypeEnum.COHABITEES)] = Field(
        default_factory=list,
        description="List of expertise enum values",
        json_schema_extra={
            "enum": [e.name for e in ExpertiseEnum if e.relationship_type == RelationshipTypeEnum.COHABITEES],
            "type": "string",
            "x-availableOptions": {e.name: e.value for e in ExpertiseEnum if e.relationship_type == RelationshipTypeEnum.COHABITEES}
        }
    )

class LawyerExpertiseInput(BaseModel):
    """Schema for expertise input grouped by relationship type."""

    married_civil_partners: MarriedCivilPartnersExpertiseGroup | None = Field(
        None,
        description="Expertise for Married and Civil Partners (maximum 5 selections)",

    )
    cohabitees: CohabiteesExpertiseGroup | None = Field(
        None,
        description="Expertise for Cohabitees (maximum 5 selections)",
    )

class LawyerCreateRequest(UserCreateRequest):
    """Schema for creating a new lawyer."""

    status: LawyerStatusEnum = Field(
        default=LawyerStatusEnum.ACTIVE,
        description="Lawyer status (Active/Deactive)",
        example=LawyerStatusEnum.ACTIVE,
    )
    address_line_1: Annotated[str, Field(max_length=255)] | None = Field(
        None, description="First line of address", example="123 Main Street"
    )
    address_line_2: Annotated[str, Field(max_length=255)] | None = Field(
        None, description="Second line of address", example="Suite 100"
    )
    city: Annotated[str, Field(max_length=100)] | None = Field(
        None, description="City name", example="London"
    )
    county: Annotated[str, Field(max_length=100)] | None = Field(
        None, description="County name", example="Greater London"
    )
    country: Annotated[str, Field(max_length=100)] | None = Field(
        None, description="Country name", example="United Kingdom"
    )
    postal_code: Annotated[str, Field(max_length=20)] | None = Field(
        None, description="Postal code", example="SW1A 1AA"
    )
    reg_no: Annotated[str, Field(max_length=100)] | None = Field(
        None, description="Registration number", example="REG123456"
    )
    sra_number: Annotated[str, Field(max_length=100)] | None = Field(
        None, description="SRA number", example="SRA123456"
    )
    bar_number: Annotated[str, Field(max_length=100)] | None = Field(
        None, description="Bar number", example="BAR123456"
    )
    regulator: Annotated[RegulatorEnum, _convert_enum_key(RegulatorEnum)] = Field(
        ...,
        description="Regulator (" + ", ".join([f"{e.name}" for e in RegulatorEnum]) + ")",
        example=RegulatorEnum.SRA,
        json_schema_extra={
            "enum": [e.name for e in RegulatorEnum],
            "type": "string",
            "x-optionLabels": {e.name: e.value for e in RegulatorEnum}
        }
    )
    regulator_other: Annotated[str, Field(max_length=255)] | None = Field(
        None,
        description="Custom regulator value when regulator is OTHER",
        example="Custom Regulatory Body",
    )
    admitted_date_solicitor: date | None = Field(
        None, description="Date admitted as solicitor", example="2020-01-15"
    )
    called_date_barrister: date | None = Field(
        None, description="Date called to the bar", example="2020-01-15"
    )
    admitted_date_cliex: date | None = Field(
        None, description="Date admitted to CLIEx", example="2020-01-15"
    )
    joined_at: datetime | None = Field(
        None, description="Date joined the firm", example="2020-01-15T09:00:00Z"
    )
    left_at: datetime | None = Field(
        None, description="Date left the firm", example="2023-12-31T17:00:00Z"
    )
    about: Annotated[str, Field(max_length=1500)] | None = Field(
        None,
        description="Brief description about the lawyer",
        example="Experienced family law specialist with 10+ years of practice",
    )
    photo_url: Annotated[str, Field(max_length=255)] | None = Field(
        None,
        description="URL to lawyer's photo",
        example="https://example.com/photos/lawyer.jpg",
    )
    # accredited_specialisations: str | None = Field(
    #     None,
    #     description="Accredited specialisations",
    #     example="Family Law, Divorce, Child Custody",
    # )
    accredited_specialisms: Annotated[list[AccreditedSpecialismEnum], _convert_enum_list(AccreditedSpecialismEnum)] = Field(
        default=[],
        description="List of accredited specialisms (" + ", ".join([f"{e.name}" for e in AccreditedSpecialismEnum]) + ")",
        example=[AccreditedSpecialismEnum.RESOLUTION_ACCREDITED_SPECIALIST, AccreditedSpecialismEnum.LAW_SOCIETY_ACCREDITED_SPECIALIST],
        json_schema_extra={
                "items": {
                    "enum": [e.name for e in AccreditedSpecialismEnum],
                    "type": "string",
                    "x-availableOptions": {e.name: e.value for e in AccreditedSpecialismEnum}
                }
            }
        )
    testimonial:Annotated[str, Field(max_length=1500)] | None = Field(
        None,
        description="Client testimonial",
        example="Excellent service and professional approach",
    )
    linkedin_url: Annotated[str, Field(max_length=255)] | None = Field(
        None,
        description="LinkedIn profile URL",
        example="https://linkedin.com/in/lawyer-name",
    )
    hourly_rate: float | None = Field(
        None, description="Hourly rate in GBP", example=150.0
    )
    charge_first_consultation: float | None = Field(
        None, description="Charge for first consultation in GBP", example=50.0
    )
    conflict_level_disinclination: Annotated[LawyerConflictLevelEnum, _convert_enum_key(LawyerConflictLevelEnum)] | None = Field(
        None,
        description="Conflict level disinclination",
        example=LawyerConflictLevelEnum.MEDIUM_CONFLICT.name,
        json_schema_extra={
            "enum": [e.name for e in LawyerConflictLevelEnum],
            "type": "string",
            "x-availableOptions": {e.name: e.value for e in LawyerConflictLevelEnum}
        }
    )
    pi_insurance: Annotated[str, Field(max_length=100)] | None = Field(
        None,
        description="Professional indemnity insurance details",
        example="Policy: PI123456, Expires: 2024-12-31",
    )
    expert_types: Annotated[list[ExpertTypeEnum], _convert_enum_list(ExpertTypeEnum)] = Field(
        min_length=1,
        description="List of expert types (" + ", ".join([f"{e.name}" for e in ExpertTypeEnum]) + ")",
        example=[ExpertTypeEnum.FAMILY_CONSULTANT, ExpertTypeEnum.SOLICITOR],
        json_schema_extra={

                "enum": [e.name for e in ExpertTypeEnum],
                "type": "array",
                "x-availableOptions": {e.name: e.value for e in ExpertTypeEnum}
            
        }
    )
    expert_types_other: str | None = Field(
        None,
        max_length=255,
        description="Expert types other",
        example="Other expertise 1, Other expertise 2"
    )
    accredited_specialism_other: list[str] | None = Field(
        None,
        description="Accredited specialisms other",
        example=["Other accredited specialism 1", "Other accredited specialism 2"]
    )
    relationship_types: Annotated[list[RelationshipTypeEnum], _convert_enum_list(RelationshipTypeEnum)] = Field(
        default=[],
        description="List of relationship types (" + ", ".join([f"{e.name}" for e in RelationshipTypeEnum]) + ")",
        example=[
            RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS,
            RelationshipTypeEnum.COHABITEES,
        ],
        json_schema_extra={ 
                "items": {
                    "enum": [e.name for e in RelationshipTypeEnum],
                    "type": "string",
                    "x-availableOptions": {e.name: e.value for e in RelationshipTypeEnum}
                }
            }
        )
    matter_types: Annotated[list[MatterTypeEnum], _convert_enum_list(MatterTypeEnum)] = Field(
        default=[],
        description="List of matter types (" + ", ".join([f"{e.name}" for e in MatterTypeEnum]) + ")",
        example=[MatterTypeEnum.FINANCIAL_CLAIMS, MatterTypeEnum.CHILDREN],
        json_schema_extra={
            "enum": [e.name for e in MatterTypeEnum],
            "type": "string",
            "x-availableOptions": {e.name: e.value for e in MatterTypeEnum}
        }
    )
    dr_preferences: Annotated[list[DRPreferenceEnum], _convert_enum_list(DRPreferenceEnum)] = Field(
        default=[],
        description="List of dispute resolution preferences (" + ", ".join([f"{e.name}" for e in DRPreferenceEnum]) + ")",
        example=[
            DRPreferenceEnum.DIRECT_NEGOTIATION,
            DRPreferenceEnum.HYBRID_MEDIATION_SUPPORT,
        ],
        json_schema_extra={
            "enum": [e.name for e in DRPreferenceEnum],
            "type": "string",
            "x-availableOptions": {e.name: e.value for e in DRPreferenceEnum}
        }
    )
    expertise: LawyerExpertiseInput = Field(
        ...,
        description="Expertise grouped by relationship type. Each group can have up to 5 expertise selections. "
                   "If 'Other' is selected, custom text is required.",
        example=LawyerExpertiseInput(
            married_civil_partners=MarriedCivilPartnersExpertiseGroup(
                expertises=[ExpertiseEnum.DIVORCE_AND_SEPARATION, ExpertiseEnum.FINANCIAL_CLAIMS],
                other=[]
            ),
            cohabitees=CohabiteesExpertiseGroup(
                expertises=[ExpertiseEnum.COHABITATION_CHILD_ARRANGEMENTS, ExpertiseEnum.COHABITATION_FINANCIAL_CLAIMS],
                other=[]
            )
        )
    )

    lawfirm_id: str = Field(
        description="Lawfirm ID", example="Z0FBQUFBQm9rRHN4UU1UMVp"
    )

    @model_validator(mode="after")
    def validate_expertise_required(self) -> "LawyerCreateRequest":
        """Validate that at least one expertise group is provided."""
        if self.relationship_types and RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS in self.relationship_types and not self.expertise.married_civil_partners:
            raise HTTPException(
                status_code=400,
                detail="At least one expertise group (married_civil_partners) must be provided"
            )
        if self.relationship_types and RelationshipTypeEnum.COHABITEES in self.relationship_types and not self.expertise.cohabitees:
            raise HTTPException(
                status_code=400,
                detail="At least one expertise group (cohabitees) must be provided"
            )
        # Validate accredited_specialism and accredited_specialism_other
        accredited_specialisms: list[str] = getattr(self, "accredited_specialisms", [])
        accredited_specialism_other: list[str] | None = getattr(self, "accredited_specialism_other", [])
        if accredited_specialisms and AccreditedSpecialismEnum.OTHER in accredited_specialisms:
            if not accredited_specialism_other:
                raise HTTPException(
                    status_code=400,
                    detail="Custom specialism value is required when 'OTHER' is selected in accredited_specialism"
                )
        if accredited_specialism_other:
            if AccreditedSpecialismEnum.OTHER not in (accredited_specialisms or []):
                raise HTTPException(
                    status_code=400,
                    detail="'OTHER' must be selected in accredited_specialism when custom value is provided"
                )   
        return self

    
    reference_id: str | None = Field(
        None, description="Legal expert reference ID for conversion from legal expert to lawyer.", example="Z0FBQUFBQm9rRHN4UU1UMVp"
    )

class LawyerUpdateRequest(LawyerCreateRequest):
    """Schema for updating an existing lawyer."""

    id: str = Field(
        ..., description="Encrypted lawyer ID", example="Z0FBQUFBQm9rRHN4UU1UMVp"
    )



class LawyerSearchRequest(BaseRequest):
    """Schema for searching lawyers."""

    limit: int = Field(
        default=20, ge=4, le=50, description="Number of records per page", example=20
    )
    search_term: str | None = Field(None, description="Search term", example="John Doe")
    status: LawyerStatusEnum | None = Field(
        None, description="Filter by lawyer and user status (both must match)", example=LawyerStatusEnum.ACTIVE
    )
    lawyer_status: LawyerStatusEnum | None = Field(
        None,
        description="Filter by lawyer status only (Active/Deactive); does not filter user status",
        example=LawyerStatusEnum.ACTIVE,
    )
    city: str | None = Field(None, description="Filter by city", example="London")
    county: str | None = Field(
        None, description="Filter by county", example="Greater London"
    )
    country: str | None = Field(None, description="Filter by country", example="United Kingdom")
    # regulator: Annotated[RegulatorEnum | None, _convert_enum_key(RegulatorEnum)] = Field(
    #     None, 
    #     description="Filter by regulator"
    # )
    regulator: Annotated[RegulatorEnum | None, _convert_enum_key(RegulatorEnum)] = Field(
        None, 
        description="Filter by regulator. Options: " + ", ".join([f"{e.name} ({e.value})" for e in RegulatorEnum]),
        example=RegulatorEnum.SRA,
        json_schema_extra={
            "enum": [e.name for e in RegulatorEnum],
            "type": "string",
            "x-availableOptions": {e.name: e.value for e in RegulatorEnum}
        }
    )    
    expert_type: Annotated[ExpertTypeEnum | None, _convert_enum_key(ExpertTypeEnum)] = Field(
        None, description="Filter by expert type", example=ExpertTypeEnum.SOLICITOR
    )
    relationship_type: Annotated[RelationshipTypeEnum | None, _convert_enum_key(RelationshipTypeEnum)] = Field(
        None,
        description="Filter by relationship type",
        example=RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS,
    )
    matter_type: Annotated[MatterTypeEnum | None, _convert_enum_key(MatterTypeEnum)] = Field(
        None,
        description="Filter by matter type",
        example=MatterTypeEnum.FINANCIAL_CLAIMS,
    )
    min_hourly_rate: float | int | None = Field(
        None, description="Minimum hourly rate", example=100.0
    )
    max_hourly_rate: float | int | None = Field(
        None, description="Maximum hourly rate", example=200.0
    )
    lawfirm_id: str | None = Field(None, description="Filter by lawfirm", example="d58161e55dc598535ab499eb84939aab")
    expertise: Annotated[ExpertiseEnum | None, _convert_enum_key(ExpertiseEnum)] = Field(
        None, description="Filter by expertise", example=ExpertiseEnum.DIVORCE_AND_SEPARATION
    )
    accredited_specialism: Annotated[AccreditedSpecialismEnum | None, _convert_enum_key(AccreditedSpecialismEnum)] = Field(
        None, description="Filter by accredited specialisms", example=AccreditedSpecialismEnum.RESOLUTION_ACCREDITED_SPECIALIST
    )


class LawyerCardData(BaseModel):
    """Public-facing labels and tags for home page lawyer cards."""

    label_1: str | None = Field(
        None,
        description="Primary public-facing professional label (Solicitor, Barrister, Lawyer, or Family Law Expert type)",
        example="Solicitor",
    )
    label_2: str | None = Field(
        None,
        description="Secondary public-facing label by priority: Arbitrator, Collaborative practitioner, Mediator",
        example="Collaborative practitioner",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Card tags: experience first, then up to 3 expertises (a random 3 when more are available)",
        example=["10 years", "Divorce and Separation", "Financial Claims", "Child arrangements"],
    )


class LawyerResponse(EncryptedResponse):
    """Schema for lawyer response."""

    id: str = Field(..., description="Lawyer ID", example="Z0FBQUFBQm9rRHN4UU1UMVp")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    email: EmailStr = Field(..., description="User email address")
    phone: str | None = Field(
        None,
        max_length=20,
        description="User phone number",
        examples=["+44 7123456789", "07123456789", "01234567890"],
    )
    gender: str | None = Field(
        None, description="User gender/salutation", examples=["Female", "Male", "Other"]
    )
    # gender_other: str | None = Field(None, description="Other gender specification")
    status: LawyerStatusEnum = Field(
        ..., description="Lawyer status", example=LawyerStatusEnum.ACTIVE
    )
    address_line_1: str | None = Field(
        None, description="First line of address", example="123 Main Street"
    )
    address_line_2: str | None = Field(
        None, description="Second line of address", example="Suite 100"
    )
    city: str | None = Field(None, description="City name", example="London")
    county: str | None = Field(
        None, description="County name", example="Greater London"
    )
    country: str | None = Field(None, description="Country name", example="United Kingdom")
    postal_code: str | None = Field(None, description="Postal code", example="SW1A 1AA")
    reg_no: str | None = Field(
        None, description="Registration number", example="REG123456"
    )
    sra_number: str | None = Field(None, description="SRA number", example="SRA123456")
    bar_number: str | None = Field(None, description="Bar number", example="BAR123456")
    regulator: RegulatorEnum | None = Field(
        None, description="Regulator", example=RegulatorEnum.SRA
    )
    regulator_other: str | None = Field(
        None, description="Custom regulator value when regulator is OTHER", example="Custom Regulatory Body"
    )
    admitted_date_solicitor: date | None = Field(
        None, description="Date admitted as solicitor", example="2020-01-15"
    )
    called_date_barrister: date | None = Field(
        None, description="Date called to the bar", example="2020-01-15"
    )
    admitted_date_cliex: date | None = Field(
        None, description="Date admitted to CLIEx", example="2020-01-15"
    )
    joined_at: datetime | None = Field(
        None, description="Date joined the firm", example="2020-01-15T09:00:00Z"
    )
    left_at: datetime | None = Field(
        None, description="Date left the firm", example="2023-12-31T17:00:00Z"
    )
    about: str | None = Field(
        None,
        description="Brief description about the lawyer",
        example="Experienced family law specialist with 10+ years of practice",
    )
    photo_urls: dict[str, str] | None = Field(
        None,
        description="Dictionary of photo URLs for different sizes",
        example={
            "thumbnail": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/thumbnail.jpg",
            "medium": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/medium.jpg",
            "large": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/large.jpg"
        },
    )
    accredited_specialisms: Annotated[list[AccreditedSpecialismEnum], _convert_enum_list(AccreditedSpecialismEnum)] = Field(
        default=[],
        description="List of accredited specialisms (" + ", ".join([f"{e.name}" for e in AccreditedSpecialismEnum]) + ")",
    )
    testimonial: str | None = Field(
        None,
        description="Client testimonial",
        example="Excellent service and professional approach",
    )
    linkedin_url: str | None = Field(
        None,
        description="LinkedIn profile URL",
        example="https://linkedin.com/in/lawyer-name",
    )
    hourly_rate: float | None = Field(
        None, description="Hourly rate in GBP", example=150.0
    )
    charge_first_consultation: float | None = Field(
        None, description="Charge for first consultation in GBP", example=50.0
    )
    conflict_level_disinclination: LawyerConflictLevelEnum | None = Field(
        None,
        description="Conflict level disinclination",
        example=LawyerConflictLevelEnum.MEDIUM_CONFLICT,
    )
    pi_insurance: str | None = Field(
        None,
        description="Professional indemnity insurance details",
        example="Policy: PI123456, Expires: 2024-12-31",
    )
    user_id: str = Field(
        ...,
        description="User ID associated with the lawyer",
        example="encrypted_user_id",
    )
    expert_types: list[ExpertTypeEnum] = Field(
        description="List of expert types (" + ", ".join([f"{e.name}" for e in ExpertTypeEnum]) + ")",
        example=[ExpertTypeEnum.SOLICITOR, ExpertTypeEnum.FAMILY_CONSULTANT],
        json_schema_extra={
            "items": {
                "enum": [e.name for e in ExpertTypeEnum],
                "type": "string",
                "x-availableOptions": {e.name: e.value for e in ExpertTypeEnum}
            }
        }
    )
    expert_types_other: str | None = Field(
        None,
        description="Expert types other",
        example="Other expertise 1, Other expertise 2"
    )
    expert_types_all: list[ExpertTypeEnum | str] | None = Field(
        None,
        description="List of all lawyer expert types",
        example=[ExpertTypeEnum.FAMILY_CONSULTANT, ExpertTypeEnum.SOLICITOR],
    )
    accredited_specialism_other: list[str] | None = Field(
        None,
        description="Accredited specialisms other",
        example=["Other accredited specialism 1", "Other accredited specialism 2"]
    )
    relationship_types: list[RelationshipTypeEnum] = Field(
        description="List of relationship types (" + ", ".join([f"{e.name}" for e in RelationshipTypeEnum]) + ")",
        example=[
            RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS,
            RelationshipTypeEnum.COHABITEES,
        ],
        json_schema_extra={
            "items": {
                "enum": [e.name for e in RelationshipTypeEnum],
                "type": "string",
                "x-availableOptions": {e.name: e.value for e in RelationshipTypeEnum}
            }
        }
    )
    matter_types: list[MatterTypeEnum] = Field(
        description="List of matter types (" + ", ".join([f"{e.name}" for e in MatterTypeEnum]) + ")",
        example=[MatterTypeEnum.FINANCIAL_CLAIMS, MatterTypeEnum.CHILDREN],
        json_schema_extra={
            "items": {
                "enum": [e.name for e in MatterTypeEnum],
                "type": "string",
                "x-availableOptions": {e.name: e.value for e in MatterTypeEnum}
            }
        }
    )
    dr_preferences: list[DRPreferenceEnum] = Field(
        description="List of dispute resolution preferences (" + ", ".join([f"{e.name}" for e in DRPreferenceEnum]) + ")",
        example=[
            DRPreferenceEnum.DIRECT_NEGOTIATION,
            DRPreferenceEnum.HYBRID_MEDIATION_SUPPORT,
        ],
        json_schema_extra={
            "items": {
                "enum": [e.name for e in DRPreferenceEnum],
                "type": "string",
                "x-availableOptions": {e.name: e.value for e in DRPreferenceEnum}
            }
        }
    )
    expertises: LawyerExpertiseInput = Field(
        description="List of expertises grouped by relationship type",
        example=[
            LawyerExpertiseInput(
                married_civil_partners=MarriedCivilPartnersExpertiseGroup(
                    expertises=[ExpertiseEnum.DIVORCE_AND_SEPARATION, ExpertiseEnum.CHILD_ARRANGEMENTS]
                ),
                cohabitees=CohabiteesExpertiseGroup(
                    expertises=[ExpertiseEnum.COHABITATION_CHILD_ARRANGEMENTS, ExpertiseEnum.COHABITATION_CHILDREN_DOMESTIC_RELOCATION]
                )
            )
        ]
    )
    accreditations: list[AccreditedSpecialismEnum | str] | None = Field(
        None,
        description="List of accreditations with other values if applicable",
        example=[AccreditedSpecialismEnum.RESOLUTION_ACCREDITED_SPECIALIST, AccreditedSpecialismEnum.LAW_SOCIETY_ACCREDITED_SPECIALIST],
    )
    expertises_all: list[ExpertiseEnum | str] | None = Field(
        None,
        description="List of expertises with other values if applicable",
        example=[ExpertiseEnum.DIVORCE_AND_SEPARATION, ExpertiseEnum.CHILD_ARRANGEMENTS],
    )
    created_at: datetime = Field(
        ..., description="Lawyer creation timestamp", example="2020-01-15T09:00:00Z"
    )
    updated_at: datetime | None = Field(
        None, description="Lawyer last update timestamp", example="2023-12-31T17:00:00Z"
    )
    experience: str | None = Field(
        None, description="Lawyer experience", example="10"
    )
    lawfirms: LawFirmData | None = Field(
        None, description="Lawfirm data", example=LawFirmData(id="Z0FBQUFBQm9rRHN4UU1UMVp", name="Lawfirm Name")
    )
    needs_password_setup: bool = Field(
        ..., description="Password set for lawyer", example=True
    )
    lawyer_card_data: LawyerCardData | None = Field(
        None,
        description="Public-facing card labels and tags for home page display",
        example=LawyerCardData(
            label_1="Solicitor",
            label_2="Collaborative practitioner",
            tags=["10 years", "Divorce and Separation", "Financial Claims", "Child arrangements"],
        ),
    )


class LawyerListResponse(EncryptedResponse):
    """Schema for lawyer list response."""

    total_count: int = Field(..., description="Total number of lawyers", example=150)
    records_in_page: int = Field(
        ..., description="Number of records in current page", example=20
    )
    items: list[LawyerResponse] = Field(..., description="List of lawyers")


class LawyerCreateResponse(BaseResponse):
    """Schema for lawyer creation response."""

    data: LawyerResponse = Field(..., description="Created lawyer data")


class LawyerUpdateResponse(BaseResponse):
    """Schema for lawyer update response."""

    data: LawyerResponse = Field(..., description="Updated lawyer data")


class InterestedLawyerUserData(BaseModel):
    """Schema for user data in interested lawyer response."""

    id: str = Field(..., description="User ID", example="Z0FBQUFBQm9rRHN4UU1UMVp")
    first_name: str = Field(..., description="User's first name", example="John")
    last_name: str = Field(..., description="User's last name", example="Doe")
    email: str = Field(
        ..., description="User email address", example="john.doe@example.com"
    )
    phone: str | None = Field(
        None, description="User phone number", example="+44 7123456789"
    )


class InterestedLawyerCaseData(BaseModel):
    """Schema for case data in interested lawyer response."""

    id: str = Field(..., description="Case ID", example="Z0FBQUFBQm9rRHN4UU1UMVp")
    case_no: str = Field(..., description="Case number", example="K2TCHJF")
    case_type: str | None = Field(None, description="Case type", example="Family Law")
    priority: str | None = Field(None, description="Case priority", example="High")
    status: str = Field(..., description="Case status", example="Open")


class InterestedLawyerResponse(EncryptedResponse):
    """Schema for interested lawyer response with user and case details."""

    id: str = Field(..., description="Lawyer ID", example="Z0FBQUFBQm9rRHN4UU1UMVp")
    status: LawyerStatusEnum = Field(
        ..., description="Lawyer status", example=LawyerStatusEnum.ACTIVE
    )
    city: str | None = Field(None, description="City name", example="London")
    county: str | None = Field(
        None, description="County name", example="Greater London"
    )
    postal_code: str | None = Field(None, description="Postal code", example="SW1A 1AA")
    reg_no: str | None = Field(
        None, description="Registration number", example="REG123456"
    )
    sra_number: str | None = Field(None, description="SRA number", example="SRA123456")
    bar_number: str | None = Field(None, description="Bar number", example="BAR123456")
    regulator: RegulatorEnum | None = Field(
        None, description="Regulator", example=RegulatorEnum.SRA
    )
    regulator_other: str | None = Field(
        None, description="Custom regulator value when regulator is OTHER", example="Custom Regulatory Body"
    )
    about: str | None = Field(
        None,
        description="About the lawyer",
        example="Experienced family law specialist",
    )
    photo_urls: dict[str, str] | None = Field(
        None,
        description="Dictionary of photo URLs for different sizes",
        example={
            "thumbnail": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/thumbnail.jpg",
            "medium": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/medium.jpg",
            "large": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/large.jpg"
        },
    )
    # accredited_specialisations: str | None = Field(
    #     None, description="Accredited specialisations", example="Family Law, Divorce"
    # )
    linkedin_url: str | None = Field(
        None, description="LinkedIn URL", example="https://linkedin.com/in/lawyer"
    )
    hourly_rate: float | None = Field(
        None, description="Hourly rate in GBP", example=150.0
    )
    charge_first_consultation: float | None = Field(
        None, description="First consultation charge in GBP", example=50.0
    )
    experience_years: str | None = Field(
        ..., description="Total years of experience", example="5 years"
    )
    hours_to_interested: str = Field(
        ...,
        description="Time taken to show interest (e.g., '20 hours' or '1 day 2 hours')",
        example="20 hours",
    )
    created_at: datetime = Field(
        ..., description="Lawyer creation timestamp", example="2020-01-15T09:00:00Z"
    )
    expert_types: list[ExpertTypeEnum | str] | None = Field(
        None,
        description="List of lawyer expert types",
        example=[ExpertTypeEnum.FAMILY_CONSULTANT, ExpertTypeEnum.SOLICITOR],
    )
    expertises: list[ExpertiseEnum | str] | None = Field(
        None,
        description="List of lawyer expertises",
        example=[ExpertiseEnum.DIVORCE_AND_SEPARATION, ExpertiseEnum.SEPARATION_AGREEMENTS],
    )
    accredited_specialisms: list[AccreditedSpecialismEnum | str] | None = Field(
        None,
        description="List of lawyer accredited specialisms",
        example=[AccreditedSpecialismEnum.RESOLUTION_ACCREDITED_SPECIALIST, AccreditedSpecialismEnum.LAW_SOCIETY_ACCREDITED_SPECIALIST],
    )
    user: InterestedLawyerUserData = Field(..., description="User details")
    case: InterestedLawyerCaseData = Field(..., description="Case details")


class InterestedLawyersListResponse(BaseModel):
    """Schema for interested lawyers list response."""

    total_count: int = Field(
        ..., description="Total number of interested lawyers", example=25
    )
    records_in_page: int = Field(
        ..., description="Number of records in current page", example=10
    )
    lawyers: list[InterestedLawyerResponse] = Field(
        ..., description="List of interested lawyers"
    )

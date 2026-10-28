from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.enums.triage import TriageListStatusEnum, TriageStatusEnum
from app.schemas.v1.auth import LoginResponseData
from app.schemas.v1.base import BaseRequest, BaseResponse, DecryptedRequest, EncryptedResponse
from app.schemas.v1.customer import CustomerInfo
from app.schemas.v1.engage import FullQuestionModel, SubmitAnswer
from app.utils.validators import validate_email_format, validate_phone_number


class GetTriageRequest(DecryptedRequest):
    """Schema for getting triage request."""

    customer_email: str | None = Field(None, description="Customer email", examples=["user@example.com"])
    triage_id: str | None = Field(None, description="Triage ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])


class CaseInfo(EncryptedResponse):
    case_id: str = Field(..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    case_no: str = Field(..., description="Case number", examples=["1234567890"])
    case_type: str | None = Field(None, description="Case type", examples=["Family Law"])
    priority: str | None = Field(None, description="Case priority", examples=["Low", "Medium", "High"])
    status: str = Field(..., description="Case status", examples=["Open"])
    start_date: date = Field(..., description="Case start date", examples=["2024-01-15"])
    created_at: datetime = Field(..., description="Case creation timestamp", examples=["2024-01-15T10:30:00Z"])
    updated_at: datetime = Field(..., description="Case update timestamp", examples=["2024-01-15T10:30:00Z"])
    """Schema for case information in registration response."""
    is_kyc_completed: bool | None = Field(None, description="Is KYC completed", examples=[True, False])

class TriageData(EncryptedResponse):
    """Schema for triage GET response data."""

    triage_id: str = Field(..., description="Triage ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    triage_status: TriageStatusEnum = Field(..., description="Triage status", examples=["Completed"])
    question_data: FullQuestionModel | None = Field(None, description="Triage questions")
    customer_info: CustomerInfo | None = Field(None, description="Customer information when triage is completed")
    case_info: CaseInfo | None = Field(None, description="Case information when triage is completed")


class GetTriageResponse(BaseResponse):
    """Schema for getting triage response."""

    data: TriageData | None = Field(None, description="Triage data")


class UpdateTriageRequest(DecryptedRequest):
    """Schema for patching triage request."""

    triage_id: str = Field(..., description="Triage ID", examples=["4eZ1ASaLikWyWGVqiGmuNg==a4ayc_80"])
    answers: list[SubmitAnswer] = Field(..., description="Answers")


class UpdateTriageResponse(BaseResponse):
    """Schema for patching triage response."""

    pass


class SubmitTriageRequest(DecryptedRequest):
    """Schema for submitting triage request."""

    triage_id: str = Field(..., description="Triage ID", examples=["4eZ1ASaLikWyWGVqiGmuNg==a4ayc_80"])
    answers: list[SubmitAnswer] = Field(default_factory=list, description="Optional answers")
    customer_email: str = Field(..., description="Customer email", examples=["user@example.com"])
    phone_number: str = Field(
        ...,
        description="Customer phone number",
        examples=["+44 7123456789", "07123456789"],
    )
    customer_name: str = Field(..., min_length=1, max_length=250, description="Customer full name")

    @field_validator("customer_email")
    @classmethod
    def validate_customer_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not email or not validate_email_format(email):
            raise ValueError("Invalid email format")
        return email

    @field_validator("phone_number")
    @classmethod
    def validate_customer_phone(cls, value: str) -> str:
        phone = value.strip()
        if not phone or not validate_phone_number(phone):
            raise ValueError("Invalid phone number format")
        return phone

    @field_validator("customer_name")
    @classmethod
    def validate_customer_name(cls, value: str) -> str:
        name = value.strip()
        if not name:
            raise ValueError("Customer name cannot be empty or contain only spaces")
        return name


class SubmitTriageResponseData(EncryptedResponse):
    """Schema for triage submit response data."""

    triage_id: str = Field(..., description="Triage ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    customer: CustomerInfo | None = Field(None, description="Customer information")
    case: CaseInfo | None = Field(None, description="Case information")
    login_data: LoginResponseData | None = Field(
        None, description="Authentication and user data after triage submit"
    )


class SubmitTriageResponse(BaseResponse):
    """Schema for submitting triage response."""

    data: SubmitTriageResponseData | None = Field(None, description="Triage submit data")


class TriageListRequest(BaseRequest):
    """Schema for triage list request."""

    search: str | None = Field(None, description="Search by customer name or email")
    status: TriageListStatusEnum | None = Field(
        TriageListStatusEnum.ALL,
        description="Filter by status: All, In progress, Completed, Moving Forward",
    )


class TriageListCustomerInfo(EncryptedResponse):
    """Schema for customer information in triage list."""

    first_name: str = Field(..., description="Customer first name", examples=["John"])
    last_name: str = Field(..., description="Customer last name", examples=["Doe"])
    email: str = Field(..., description="Customer email", examples=["john.doe@example.com"])
    id: str = Field(..., description="Customer ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])

    model_config = ConfigDict(from_attributes=True)


class TriageListItem(EncryptedResponse):
    """Schema for triage list item."""

    title: str | None = Field(None, description="Title", examples=["Triage"])
    triage_id: str = Field(..., description="Triage ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    case_type: str = Field(..., description="Case type", examples=["Family Law"])
    triage_status: str = Field(..., description="Triage status", examples=["Completed"])
    start_date: date = Field(..., description="Start date", examples=["2024-01-15"])
    completed_date: datetime | None = Field(
        None, description="Completed date", examples=["2024-01-15T10:30:00Z"]
    )
    created_at: datetime = Field(..., description="Creation timestamp", examples=["2024-01-15T10:30:00Z"])
    updated_at: datetime = Field(..., description="Last update timestamp", examples=["2024-01-15T10:30:00Z"])
    no_of_questions_answered: int | None = Field(None, description="No of questions answered", examples=[10])
    customer: TriageListCustomerInfo | None = Field(None, description="Customer information")

    model_config = ConfigDict(from_attributes=True)


class TriageListResponseData(EncryptedResponse):
    """Schema for triage list response data."""

    total_count: int = Field(..., description="Total number of records", examples=[100])
    records_in_page: int = Field(
        ..., description="Number of records in current page", examples=[20]
    )
    triages: list[TriageListItem] = Field(..., description="List of triage records")


class TriageListResponse(BaseResponse):
    """Schema for triage list response."""

    data: TriageListResponseData = Field(..., description="Triage list response data")

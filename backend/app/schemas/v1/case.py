"""Case schemas for API v1."""

from datetime import date, datetime

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.enums.case import CaseCategoryEnum, CaseStatusEnum, CaseStatusFilterEnum, CaseIntentEnum
from app.schemas.v1.base import (
    BaseRequest,
    BaseResponse,
    DecryptedRequest,
    EncryptedResponse,
)


class CaseBase(BaseModel):
    """Base case schema."""

    start_date: date = Field(..., description="Case start date")
    case_no: str | None = Field(None, description="Case number")
    case_type: str | None = Field(None, description="Case type")
    priority: str | None = Field(None, description="Case priority")
    status: str = Field("Open", description="Case status")


class CaseCreate(CaseBase):
    """Schema for creating a new case."""

    pass


class CaseUpdate(BaseModel):
    """Schema for updating a case."""

    start_date: date | None = Field(None, description="Case start date")
    case_no: str | None = Field(None, description="Case number")
    case_type: str | None = Field(None, description="Case type")
    priority: str | None = Field(None, description="Case priority")
    status: str | None = Field(None, description="Case status")


class CaseResponse(EncryptedResponse):
    """Schema for case response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Case ID")
    start_date: date = Field(..., description="Case start date")
    case_no: str | None = Field(None, description="Case number")
    case_type: str | None = Field(None, description="Case type")
    priority: str | None = Field(None, description="Case priority")
    status: str = Field(..., description="Case status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime | None = Field(None, description="Last update timestamp")

    model_config = ConfigDict(from_attributes=True)


class CaseSearchRequest(BaseRequest):
    """Request schema for searching cases."""

    search: str | None = Field(
        default=None,
        description="Optional search term to filter by customer name (first name or last name or full name) or email",
        examples=["John", "john@example.com"],
    )
    case_no: str | None = Field(
        default=None,
        description="Optional case number to filter by",
        examples=100,
    )
    status: CaseStatusFilterEnum | None = Field(
        default=CaseStatusFilterEnum.ALL,
        description="Filter by case status: All, KYC Completed, Match Confirmed, Profile Card Sent, Lawyer Assigned, Initial Payment Completed, Onboarding Completed",
    )
    category: CaseCategoryEnum | None = Field(
        default=CaseCategoryEnum.ALL,
        description="Filter by case category (for lawyers): All, My Cases (cases before awarded to others), Missing Cases (cases awarded to other lawyers)",
    )
    case_status: CaseStatusEnum | None = Field(
        default= None,
        description="Filter by case status: Open, Closed, Archived",
    )
    case_intent: CaseIntentEnum | None = Field(
        default=CaseIntentEnum.ALL,
        description="Filter by case intent: All, High Intent, Low Intent",
    )


class CustomerInfo(EncryptedResponse):
    """Schema for customer information."""

    first_name: str = Field(..., description="Customer first name", examples=["John"])
    last_name: str = Field(..., description="Customer last name", examples=["Doe"])
    email: str | None = Field(
        ..., description="Customer email", examples=["john.doe@example.com"]
    )
    id: str = Field(
        ..., description="Customer ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"]
    )
    phone: str | None = Field(
        None, description="Customer phone", examples=["+1234567890"]
    )

    model_config = ConfigDict(from_attributes=True)


class CaseListItem(EncryptedResponse):
    """Schema for case list item."""

    id: str = Field(..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    case_no: str = Field(..., description="Case number", examples=["CASE-100"])
    case_type: str | None = Field(
        None, description="Case type", examples=["Family Law"]
    )
    priority: str | None = Field(None, description="Case priority", examples=["High"])
    status: str | None = Field(None, description="Case status", examples=["Open"])
    start_date: date | None = Field(
        None, description="Start date", examples=["2024-01-15"]
    )
    created_at: datetime = Field(
        ..., description="Creation timestamp", examples=["2024-01-15T10:30:00Z"]
    )
    customer: CustomerInfo | None = Field(None, description="Customer information")
    tags: list[str] | None = Field(
        default=None,
        description="Tags indicating case progress milestones",
        examples=[["kyc_completed", "match_confirmed", "lawyer_assigned", "initial_payment_completed", "onboarding_completed"]],
    )

    model_config = ConfigDict(from_attributes=True)


class CaseListResponseData(EncryptedResponse):
    """Schema for case list response data."""

    total_count: int = Field(..., description="Total number of records", examples=[100])
    records_in_page: int = Field(
        ..., description="Number of records in current page", examples=[20]
    )
    cases: list[CaseListItem] = Field(..., description="List of case records")


class CaseListResponse(BaseResponse[CaseListResponseData]):
    """Schema for case list response."""

    data: CaseListResponseData = Field(..., description="Case list response data")


class CaseInterestRequest(DecryptedRequest):
    """Request schema for case interest or decline."""

    case_id: str = Field(
        ..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"]
    )
    lawyer_id: str | None = Field(
        None,
        description="Lawyer ID (optional for lawyers, mandatory for navigators)",
        examples=["Z0FBQUFBQm9rRHN4UU1UMVp"],
    )


class CaseDeclineRequest(DecryptedRequest):
    """Request schema for case decline with JSON reason structure."""

    case_id: str = Field(
        ..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"]
    )
    lawyer_id: str | None = Field(
        None,
        description="Lawyer ID (optional for lawyers, mandatory for navigators)",
        examples=["Z0FBQUFBQm9rRHN4UU1UMVp"],
    )
    decline_reason: dict = Field(
        ...,
        description="Decline reason as JSON object",
        examples=[
            {
                "reason": ["Conflict of interest", "Workload capacity"],
                "reason_other": "Additional context about the decline",
            }
        ],
    )


class CaseInterestResponse(BaseResponse):
    """Response schema for case interest actions."""

    data: list = Field(default=[], description="Empty data for case interest response")


class CaseDeclineResponse(BaseResponse):
    """Response schema for case decline actions."""

    data: list = Field(default=[], description="Empty data for case decline response")


class CaseArchiveRequest(BaseModel):
    """Request schema for manually archiving cases (navigator only)."""

    case_ids: list[str] = Field(
        ...,
        min_length=1,
        description="Encrypted case IDs to archive",
        examples=[["Z0FBQUFBQm9rRHN4UU1UMVp"]],
    )


class CaseArchiveResponse(BaseResponse):
    """Response schema for case archive actions."""

    data: list = Field(default=[], description="Empty data for case archive response")


class CaseMoreDetailsRequest(DecryptedRequest):
    """Request schema for case more details."""

    case_id: str = Field(
        ..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"]
    )
    lawyer_id: str | None = Field(
        None,
        description="Lawyer ID (optional for lawyers, mandatory for navigators)",
        examples=["Z0FBQUFBQm9rRHN4UU1UMVp"],
    )
    query_text: str = Field(
        ...,
        min_length=1,
        max_length=250,
        description="Query text",
        examples=["What is the case about?"],
    )


class CaseMoreDetailsResponse(BaseResponse):
    """Response schema for case more details."""

    data: list = Field(default=[], description="Empty data for case more details response")


class CaseDetailsRequest(DecryptedRequest):
    """Request schema for case details."""

    case_id: str = Field(
        ..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"]
    )


class PartiesInvolved(BaseModel):
    """Schema for parties involved in case."""

    client_name: str | None = Field(
        None, description="Client name", examples=["John Doe"]
    )
    client_email: str | None = Field(
        None, description="Client email", examples=["john.doe@example.com"]
    )
    client_phone: str | None = Field(
        None, description="Client phone", examples=["+1234567890"]
    )
    lawyer_name: str | None = Field(
        None, description="Lawyer name", examples=["Jane Smith"]
    )
    lawyer_email: str | None = Field(
        None, description="Lawyer email", examples=["jane.smith@lawfirm.com"]
    )
    lawyer_phone: str | None = Field(
        None, description="Lawyer phone", examples=["+1234567891"]
    )
    partner_name: str | None = Field(
        None, description="Partner name", examples=["Robert Doe"]
    )


class CaseDetailsData(EncryptedResponse):
    """Schema for case details data."""
    status: str = Field(..., description="Case status", examples=["Open", "Closed", "Archived"])
    case_summary: dict | None = Field(
        None,
        description="Case summary",
        examples=["<html><body>Summary of the case</body></html>"],
    )
    is_ai_summary_generated: bool | None = Field(
        None,
        description="Whether the AI summary is generated",
        examples=[True],
    )
    parties_involved: PartiesInvolved = Field(
        ..., description="Parties involved in the case"
    )
    action_buttons: dict | None = Field(
        None,
        description="Action buttons",
        examples=[
            {"raise_interest": True, "decline_match": True, "ask_more_details": True, "view_resolve": True, "view_kyc": True},
        ],
    )
    analytics_data: dict[str, Any] | None = Field(
        None,
        description="Analytics capture payload stored at case_opened (null until set)",
    )


class CaseDetailsResponse(BaseResponse[CaseDetailsData]):
    """Response schema for case details."""

    data: CaseDetailsData = Field(..., description="Case details data")


class CaseSummaryItem(BaseModel):
    """Schema for individual case summary item."""

    title: str = Field(..., min_length=1, description="Summary section title", examples=["Case Background"])
    description: str = Field(..., min_length=1, description="Summary section description", examples=["Details about the case background"])


class CaseSummaryUpdateRequest(DecryptedRequest):
    """Request schema for case summary."""

    case_id: str = Field(
        ..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"]
    )
    case_summary: list[CaseSummaryItem] = Field(
        ...,
        min_length=1,
        description="Case summary as list of sections with title and description",
        examples=[[
            {"title": "Case Background", "description": "Client is seeking legal assistance"},
            {"title": "Legal Issues", "description": "Family law matter regarding custody"}
        ]]
    )


class CaseSummaryUpdateResponse(BaseResponse):
    """Response schema for case summary."""

    pass


class CaseSummaryRequest(DecryptedRequest):
    """Request schema for case summary."""

    case_id: str = Field(
        ..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"]
    )


class CaseSummaryData(EncryptedResponse):
    """Schema for case summary data."""

    case_id: str = Field(..., description="Case ID", examples=["Z0FBQUFBQm9rRHN4UU1UMVp"])
    case_summary: list[CaseSummaryItem] | None = Field(
        None,
        description="Case summary as list of sections with title and description",
        examples=[[
            {"title": "Case Background", "description": "Client is seeking legal assistance"},
            {"title": "Legal Issues", "description": "Family law matter regarding custody"}
        ]]
    )

    model_config = ConfigDict(from_attributes=True)


class CaseSummaryResponse(BaseResponse[CaseSummaryData]):
    """Response schema for case summary."""

    data: CaseSummaryData = Field(..., description="Case summary data")

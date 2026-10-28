"""Schemas for engage support API. Option fields use integer keys."""

from datetime import date, datetime

from pydantic import BaseModel, Field

from .base import BaseRequest, BaseResponse, EncryptedResponse


class EngageSupportCreateRequest(BaseModel):
    """Request body for creating an engage support submission."""

    name: str | None = Field(None, max_length=255)
    phone: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=255)
    how_can_help: int | None = Field(None, ge=1, le=5)
    trouble_with_any: int | None = Field(None, ge=1, le=4)
    trouble_navigating_engage: int | None = Field(None, ge=1, le=2)
    section_stuck_on: int | None = Field(None, ge=1, le=4)
    issues_listed: int | None = Field(None, ge=1, le=3)
    new_lawfirm: str | None = Field(None, max_length=255)
    helped_resolve_issue: int | None = Field(None, ge=1, le=2)
    support_query_message: str | None = None


class EngageSupportData(EncryptedResponse):
    """Saved engage support fields; id is encrypted in response. Option fields are display values."""

    id: str = Field(..., description="Support submission ID (returned encrypted)")
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    how_can_help: str | None = None
    trouble_with_any: str | None = None
    trouble_navigating_engage: str | None = None
    section_stuck_on: str | None = None
    issues_listed: str | None = None
    new_lawfirm: str | None = None
    helped_resolve_issue: str | None = None
    support_query_message: str | None = None
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


class EngageSupportCreateResponse(BaseResponse):
    """Response after creating an engage support submission."""

    pass


class EngageSupportListRequest(BaseRequest):
    """Query params for listing engage support submissions."""

    start_date: date | None = Field(
        None,
        description="Filter: created_at on or after this date (YYYY-MM-DD)",
    )
    end_date: date | None = Field(
        None,
        description="Filter: created_at on or before this date (YYYY-MM-DD)",
    )


class EngageSupportListData(BaseModel):
    """List response data with pagination metadata."""

    total_count: int = Field(..., description="Total number of matching records")
    records_in_page: int = Field(..., description="Number of records in the current page")
    items: list[EngageSupportData] = Field(..., description="List of engage support records")


class EngageSupportListResponse(BaseResponse):
    """GET engage-support list response."""

    data: EngageSupportListData = Field(..., description="List data with pagination")

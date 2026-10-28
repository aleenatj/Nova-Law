"""Schemas for engage feedback API. Option fields use integer keys; helper_type/help_reason saved as [1, 2]."""

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from fastapi.exceptions import RequestValidationError

from .base import BaseRequest, BaseResponse, EncryptedResponse

# Allowed enum keys: helper_type 1-6, help_reason 1-7 (validated like ge/le via Literal)
HelperTypeKey = Literal[1, 2, 3, 4, 5, 6]
HelpReasonKey = Literal[1, 2, 3, 4, 5, 6, 7]


class EngageFeedbackCreateRequest(BaseModel):
    """Request body for creating engage feedback. helper_type/help_reason: list of enum keys only, saved as [1, 2]."""

    # Single-select option fields (integer keys, see app.enums.engage_feedback)
    time_value_feedback: int | None = Field(None, ge=1, le=3, description="Time value feedback option key")
    completion_time: int | None = Field(None, ge=1, le=9, description="Completion time option key")
    session_count: int | None = Field(None, ge=1, le=10, description="Session count 1-10")
    help_level: int | None = Field(None, ge=1, le=4, description="Help level option key")
    preparedness_level: int | None = Field(None, ge=1, le=5, description="Preparedness level option key")
    age_range: int | None = Field(None, ge=1, le=7, description="Age range option key")
    gender: int | None = Field(None, ge=1, le=4, description="Gender option key")
    overall_experience: int | None = Field(None, ge=1, le=5, description="Overall experience option key")
    recommendation_score: int | None = Field(None, ge=1, le=10, description="Recommendation score 1-10")

    # Multi-select: each value must be 1-6 (helper_type) or 1-7 (help_reason); validation like ge/le, returns 422
    helper_type: list[HelperTypeKey] | None = Field(
        None,
        description="Who helped (each value 1-6, e.g. [1, 2])",
        examples=[[1, 2]],
    )
    help_reason: list[HelpReasonKey] | None = Field(
        None,
        description="Why help was needed (each value 1-7, e.g. [1, 2])",
        examples=[[1, 2]],
    )

    gender_other: str | None = Field(None, max_length=255, description="Free text when gender is Other")
    improvement_feedback: str | None = Field(None, description="Free text improvement feedback")
    @model_validator(mode="after")
    def validate_gender_other(self) -> "EngageFeedbackCreateRequest":
        """Validate that gender_other is provided when gender is Other."""
        if self.gender_other and self.gender != 4:
            raise RequestValidationError(
                [{"success": False, "message": "gender_other can only be provided when gender is 'Other'"}]
            )
        return self

    @model_validator(mode="after")
    def validate_helper_fields_require_help_level(self) -> "EngageFeedbackCreateRequest":
        """helper_type and help_reason are only allowed when help_level is given; not allowed when help_level is 1."""
        has_helper_type = self.helper_type is not None and len(self.helper_type) > 0
        has_help_reason = self.help_reason is not None and len(self.help_reason) > 0
        if not (has_helper_type or has_help_reason):
            return self
        if self.help_level is None:
            raise RequestValidationError(
                [{"success": False, "message": "help_level must be given when helper_type or help_reason is provided"}]
            )
        if self.help_level == 1:
            raise RequestValidationError(
                [{"success": False, "message": "helper_type and help_reason must not be provided when help_level is 'I completed it without any help'"}]
            )
        return self

class EngageFeedbackData(EncryptedResponse):
    """All saved engage feedback fields; id is encrypted in response. Option fields are returned as display values (strings)."""
    id: str = Field(..., description="Feedback ID (returned encrypted)")
    time_value_feedback: str | None = None
    completion_time: str | None = None
    session_count: str | None = None
    help_level: str | None = None
    helper_type: list[str] | None = None
    help_reason: list[str] | None = None
    preparedness_level: str | None = None
    age_range: str | None = None
    gender: str | None = None
    gender_other: str | None = None
    overall_experience: str | None = None
    improvement_feedback: str | None = None
    recommendation_score: str | None = None
    created_at: datetime = Field(..., description="Created at")
    updated_at: datetime = Field(..., description="Updated at")


class EngageFeedbackCreateResponse(BaseResponse):
    """Response after creating engage feedback; data contains all saved fields with encrypted id."""

    pass


class EngageFeedbackListRequest(BaseRequest):
    """Query params for listing engage feedback: page, limit, order_by, order_dir, start_date, end_date (filter by created_at)."""

    start_date: date | None = Field(
        None,
        description="Filter: created_at on or after this date (YYYY-MM-DD)",
    )
    end_date: date | None = Field(
        None,
        description="Filter: created_at on or before this date (YYYY-MM-DD)",
    )


class EngageFeedbackListData(BaseModel):
    """List response data with pagination and date filtering metadata."""

    total_count: int = Field(..., description="Total number of matching records")
    records_in_page: int = Field(..., description="Number of records in the current page")
    items: list[EngageFeedbackData] = Field(..., description="List of engage feedback records")


class EngageFeedbackListResponse(BaseResponse):
    """GET engage-feedback list response."""

    data: EngageFeedbackListData = Field(..., description="List data with pagination")

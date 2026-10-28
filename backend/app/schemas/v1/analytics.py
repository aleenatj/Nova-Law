from datetime import datetime, timezone
from typing import Any, Literal, Self
from uuid import UUID
from fastapi.exceptions import RequestValidationError

from pydantic import BaseModel, Field, field_validator, model_validator

from app.enums.analytics import (
    CompareFilterEnum,
    ComparePeriodEnum,
    SourceEnum,
)
from app.enums.case import CaseStatusEnum
from app.enums.deletion_request import (
    DeletionRequestStatus,
    DeletionRequestSubjectType,
)
from app.schemas.v1.base import BaseResponse


class AnalyticsPageContext(BaseModel):
    url: str | None = None
    path: str | None = None
    title: str | None = None
    referrer: str | None = None


class AnalyticsCampaignContext(BaseModel):
    source: str | None = None
    medium: str | None = None
    campaign: str | None = None
    term: str | None = None
    content: str | None = None
    gclid: str | None = None


class AnalyticsScreenSize(BaseModel):
    width: int | None = None
    height: int | None = None


class AnalyticsDeviceContext(BaseModel):
    user_agent: str | None = None
    screen: AnalyticsScreenSize | None = None
    viewport: AnalyticsScreenSize | None = None
    locale: str | None = None
    timezone: str | None = None
    country: str | None = Field(
        None,
        description="ISO-3166 alpha-2 when known (e.g. from CDN geo); not derivable from UA alone",
    )


class AnalyticsLibraryContext(BaseModel):
    name: str | None = None
    version: str | None = None


class AnalyticsEventContext(BaseModel):
    page: AnalyticsPageContext | None = None
    campaign: AnalyticsCampaignContext | None = None
    device: AnalyticsDeviceContext | None = None
    library: AnalyticsLibraryContext | None = None


class AnalyticsEventPropertiesBag(BaseModel):
    traits: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Stable visitor traits (optional)."
        ),
    )
    event_data: dict[str, Any] = Field(default_factory=dict)


class SubmitAnalyticsRequest(BaseModel):
    """Frontend capture body"""

    token: str | None = Field(None, description="Legacy JWE token (email CTA flow)")
    event_name: str | None = Field(None, description="Event name e.g. page_view")
    timestamp: datetime | None = Field(None, description="Client-reported event time")
    anonymous_id: UUID | None = None
    session_id: UUID | None = None
    user_id: str | int | None = Field(
        None,
        description="Encrypted or plaintext application user id (customer)",
    )
    case_id: str | int | None = Field(
        None,
        description="Encrypted or plaintext case id",
    )
    context: AnalyticsEventContext | None = None
    properties: AnalyticsEventPropertiesBag = Field(
        default_factory=AnalyticsEventPropertiesBag
    )

    @field_validator("user_id", "case_id", mode="before")
    @classmethod
    def _normalize_id_fields(cls, v: Any) -> Any:
        if v is None or v == "":
            return None
        return v

    @field_validator("timestamp", mode="after")
    @classmethod
    def _timestamp_utc(cls, v: datetime | None) -> datetime | None:
        if v is None:
            return None
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode="after")
    def _legacy_or_capture(self) -> Self:
        capture = bool(self.event_name and str(self.event_name).strip())
        if capture:
            missing: list[str] = []
            if self.timestamp is None:
                missing.append("timestamp")
            if self.anonymous_id is None:
                missing.append("anonymous_id")
            if self.session_id is None:
                missing.append("session_id")
            if missing:
                raise RequestValidationError(
                    [{"success": False, "message": f"When event_name is set, required fields: {', '.join(missing)}"}]
                )
            if self.case_id is not None and self.user_id is None:
                raise RequestValidationError(
                    [{"success": False, "message": "user_id is required when case_id is set"}]
                )
            return self
        if self.token is None:
            raise RequestValidationError(
                [{"success": False, "message": "Either token (legacy) or event_name (capture) is required"}]
            )
        return self


class SubmitAnalyticsResponse(BaseResponse[dict[str, Any]]):
    """Submit analytics response schema."""

    pass


class DeleteAnalyticsRequest(BaseModel):
    """Queue a privacy deletion request for analytics data only."""

    subject_type: DeletionRequestSubjectType = Field(
        ...,
        description="Deletion subject type: user_id, session_id, or anonymous_id",
    )
    subject_id: UUID = Field(..., description="Subject identifier as UUID")
    reason: str | None = Field(
        None,
        description="Optional free-form reason for the deletion request",
    )
    status: DeletionRequestStatus = Field(
        default=DeletionRequestStatus.PENDING,
        description="Deletion request status; defaults to pending",
    )

    @model_validator(mode="after")
    def validate_subject(self) -> Self:
        if self.status != DeletionRequestStatus.PENDING:
            raise ValueError("status must be PENDING when creating a deletion request")
        return self


class DeleteAnalyticsResponse(BaseResponse[dict[str, Any]]):
    """Delete analytics response schema."""

    pass


class GetAnalyticsRequest(BaseModel):
    """Query params for Analytics report."""

    start_date: datetime = Field(..., description="Interval start (inclusive)")
    end_date: datetime = Field(..., description="Interval end (exclusive)")
    source: SourceEnum | None = Field(
        None,
        description="If set, restrict to this ``session.source`` (e.g. google_ads)",
    )
    status: CaseStatusEnum | None = Field(
        None,
        description="Optional case status filter",
    )
    landing_page: str | None = Field(
        None,
        description="If set, restrict to this ``session.entry_page`` path (e.g. /, /divorce-options)",
    )

    @field_validator("landing_page", mode="before")
    @classmethod
    def normalize_landing_page(cls, v: Any) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            s = v.strip()
            return s if s else None
        return str(v).strip() or None
    # Removed navigator cohort filter (was encrypted navigator user id query param).
    # Removed per-funnel filters — use global ``source`` and ``landing_page`` instead:
    # end_to_end_source: SourceEnum | None = Field(
    #     None,
    #     description="Optional source filter used only for end-to-end funnel",
    # )
    # end_to_end_landing_page: str | None = Field(
    #     None,
    #     description="Optional landing page filter used only for end-to-end funnel",
    # )
    # resolve_source: SourceEnum | None = Field(
    #     None,
    #     description="Optional source filter used only for resolve funnel",
    # )
    # resolve_landing_page: str | None = Field(
    #     None,
    #     description="Optional landing page filter used only for resolve funnel",
    # )
    compare: CompareFilterEnum | None = Field(
        None,
        description="If set, ``general_info`` includes change vs comparison window",
    )
    period: ComparePeriodEnum | None = Field(
        None,
        description="Required when ``compare=period`` (7d / 30d / 90d, anchored to ``end_date``)",
    )

    @field_validator("start_date", "end_date", mode="after")
    @classmethod
    def default_timezone_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode="after")
    def validate_compare_and_dates(self) -> Self:
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        if self.compare == CompareFilterEnum.PERIOD:
            if self.period is None:
                raise ValueError("period is required when compare is period")
        elif self.period is not None:
            raise ValueError("period may only be set when compare is period")
        return self


class EndToEndFunnelStepRow(BaseModel):
    step_index: int
    event_type: str
    total_count: int
    pct_of_visit: float | None = None
    dropoff: dict[str, Any] | None = None


class ResolveFunnelStepRow(BaseModel):
    step_index: int
    event_type: str
    total_count: int
    pct_drop: int | None = Field(
        None,
        description="Percent drop from previous funnel step; omitted for step 1",
    )


class AlignmentCheckFunnelStepRow(BaseModel):
    step_index: int
    event_type: str
    total_count: int
    pct_drop: int | None = Field(
        None,
        description="Percent drop from previous funnel step; omitted for step 1",
    )


class HighIntentFunnelStepRow(BaseModel):
    step_index: int
    event_type: str
    total_count: int
    pct_drop: int | None = Field(
        None,
        description="Percent drop from previous funnel step; omitted for step 1",
    )


class ConversionStepMetrics(BaseModel):
    count: int
    pct_of_conversion: float = Field(
        ...,
        description="Percent of that source's sessions cohort reaching this step (4 d.p.)",
    )


class ConversionBySourceRow(BaseModel):
    source: str
    sessions: ConversionStepMetrics
    case_opened: ConversionStepMetrics
    alignment_check_completed: ConversionStepMetrics
    match_confirmed: ConversionStepMetrics
    profile_card_sent: ConversionStepMetrics
    expert_assigned: ConversionStepMetrics
    engage_get_started: ConversionStepMetrics


class ActiveStalledStageRow(BaseModel):
    step_index: int
    event_type: str
    active_count: int
    stalled_count: int


class AverageTimeBetweenStagesRow(BaseModel):
    step_index: int
    event_type: str
    deviation_day: str | None = Field(
        None,
        description="Average days from previous stage; null for first stage",
    )


class RevenueBySourceRow(BaseModel):
    source: str
    total_revenue: int


class GeneralInfoChange(BaseModel):
    deltaText: str
    trend: Literal["positive", "negative", "neutral"]
    previous_value: str


class GeneralInfoCard(BaseModel):
    label: str
    value: int | str
    change: GeneralInfoChange | None = None
    trendSeries: list[int]
    trendSeriesDates: list[str] | None = Field(
        None,
        description="ISO dates aligned with trendSeries",
    )


class AnalyticsReportData(BaseModel):
    end_to_end_resolve_funnel: list[EndToEndFunnelStepRow]
    end_to_end_triage_funnel: list[EndToEndFunnelStepRow]
    resolve_funnel: list[ResolveFunnelStepRow]
    alignment_check_funnel: list[AlignmentCheckFunnelStepRow]
    high_intent_funnel: list[HighIntentFunnelStepRow]
    conversion_by_source: list[ConversionBySourceRow]
    active_stalled: list[ActiveStalledStageRow]
    average_time_between_stages: list[AverageTimeBetweenStagesRow]
    revenue_by_source: list[RevenueBySourceRow]
    general_info: list[GeneralInfoCard]


class GetAnalyticsResponse(BaseResponse[AnalyticsReportData]):
    """Get analytics response schema."""

    pass


class GetAnalyticsLandingPagesRequest(BaseModel):
    """Query params for distinct landing page paths."""

    start_date: datetime = Field(..., description="Interval start (inclusive)")
    end_date: datetime = Field(..., description="Interval end (exclusive)")

    @field_validator("start_date", "end_date", mode="after")
    @classmethod
    def default_timezone_utc(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> Self:
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self


class AnalyticsLandingPagesData(BaseModel):
    page_paths: list[str] = Field(
        default_factory=list,
        description=(
            "Distinct paths from session entry_page and page_view events "
            "(excludes navigator sessions)"
        ),
    )


class GetAnalyticsLandingPagesResponse(BaseResponse[AnalyticsLandingPagesData]):
    """Distinct landing page paths for analytics filters."""

    pass
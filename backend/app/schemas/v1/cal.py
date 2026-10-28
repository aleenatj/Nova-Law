from pydantic import BaseModel, Field

from .base import BaseResponse, DecryptedRequest


class CalAvailabilityRequest(BaseModel):
    """Query params for fetching available Cal.com consultation slots."""

    start: str = Field(
        ...,
        description="Start date (YYYY-MM-DD or ISO 8601 UTC)",
        examples=["2026-07-15"],
    )
    end: str | None = Field(
        default=None,
        description="End date (YYYY-MM-DD or ISO 8601 UTC). Defaults to start + 30 days.",
        examples=["2026-08-14"],
    )


class CalAvailabilitySlot(BaseModel):
    """First available consultation slot."""

    date: str = Field(..., description="Date of the slot (YYYY-MM-DD)")
    start: str = Field(..., description="Slot start time (ISO 8601)")
    end: str | None = Field(default=None, description="Slot end time (ISO 8601)")


class CalAvailabilityResponse(BaseResponse):
    """Schema for Cal.com availability response."""

    pass


class CalWebhookResponse(BaseResponse):
    """Schema for Cal.com webhook response."""

    pass


class BookFreeCallRequest(DecryptedRequest):
    """Schema for booking a free call request."""

    case_id: str = Field(..., description="Case ID")
    phone_number: str = Field(..., description="Phone number")


class BookFreeCallResponse(BaseResponse):
    """Schema for booking a free call response."""

    pass
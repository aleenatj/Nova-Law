from pydantic import BaseModel, Field

from .base import BaseResponse, DecryptedRequest

ENCRYPTION_SALT: str | None = None

class CreateCheckoutSessionRequest(DecryptedRequest):
    """Schema for create checkout session request."""
    amount: float = Field(..., description="Amount")
    currency: str | None = Field(None, description="Currency")
    payment_id: str = Field(..., description="Payment ID")


class CreateCheckoutSessionResponse(BaseResponse):
    """Schema for create checkout session response."""
    pass


class StripeWebhookResponse(BaseResponse):
    """Schema for stripe webhook response."""
    pass


class VerifyPaymentRequest(BaseModel):
    """Schema for verify payment request."""
    session_id: str = Field(..., description="Session ID")

class VerifyPaymentResponse(BaseResponse):
    """Schema for verify payment response."""
    pass

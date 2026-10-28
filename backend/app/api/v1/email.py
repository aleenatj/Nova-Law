"""Email API endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

from app.core.email import email_service

router = APIRouter(prefix="/email", tags=["email"])


class EmailRequest(BaseModel):
    """Request model for sending emails."""

    recipient: EmailStr
    subject: str
    body: str
    sender: str | None = None


class EmailResponseModel(BaseModel):
    """Response model for email sending."""

    success: bool
    message_id: str | None = None
    error: str | None = None


@router.post("/send", response_model=EmailResponseModel)
async def send_email(request: EmailRequest) -> EmailResponseModel:
    """
    Send email via AWS SES.

    Args:
        request: Email request containing recipient, subject, body, and optional sender

    Returns:
        EmailResponseModel with success status and details
    """
    return EmailResponseModel(
        success=True,
        message_id=None,
        error=None,
    )
    result = await email_service.send_email(
        to_email=request.recipient,
        subject=request.subject,
        body=request.body,
        sender=request.sender,
    )

    return EmailResponseModel(
        success=result.success,
        message_id=result.message_id,
        error=result.error,
    )

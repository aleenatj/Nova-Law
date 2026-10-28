from fastapi import APIRouter, HTTPException, status
from app.core.config import settings
from app.schemas.v1.base import ResponseMessage
from app.schemas.v1.contact_us import ContactUsRequest, ContactUsResponse
from app.utils.validators import validate_phone_number, validate_email_format
import logging
from app.core.email import email_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/contact-us", response_model=ContactUsResponse)
async def contact_us(
    request: ContactUsRequest,
) -> ContactUsResponse:
    """Customer Contact us request"""
    try:
        if not validate_phone_number(request.phone):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phone number") # noqa: TRY301
        
        if not validate_email_format(request.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format") # noqa: TRY301

        emails = settings.CONTACT_US_EMAIL.split(",")
        
        if not emails:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No contact email addresses found",
            )

        response = await email_service.send_email(
                bcc=emails,
                template=email_service.EmailTemplate.CONTACT_US_NOTIFICATION,
                context={
                    "first_name": request.first_name,
                    "last_name": request.last_name,
                    "phone": request.phone,
                    "email": request.email,
                    "message": request.message,
                },
            )

        return ContactUsResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Contact us request submitted successfully")],
            data={},
        )

    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to submit contact us request", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit contact us request",
        ) from None
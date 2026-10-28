from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.utils.dependencies import get_db
from app.core.config import settings
from app.db.services.case import get_case_by_customer_id
from app.db.services.auth import get_user_by_email
from app.enums.user_role import UserRoleEnum
from app.enums.user import StatusEnum
from app.enums.events import EventType
from app.schemas.v1.engage import EngageCompleteRequest, EngageCompleteResponse, EngageCompleteEventRequest
from app.schemas.v1.event import Event
from app.events.dispatcher import event_dispatcher
from app.utils.helpers import extract_status_messages
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/engage-complete", response_model=EngageCompleteResponse)
async def engage_complete(
    request: EngageCompleteRequest,
    db: Session = Depends(get_db),
) -> EngageCompleteResponse:
    """Engage complete for the case."""
    try:

        x_api_key = settings.ENGAGE_API_KEY
        if not x_api_key or x_api_key != request.x_api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

        detail = [{"success": False, "message": "Invalid request"}]

        user = get_user_by_email(db, request.email)
        if not user:
            logger.error("User not found")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

        user_role_code = None
        if user.user_roles:
            user_role_code = UserRoleEnum.from_id(user.user_roles[0].role_id).display_name
        else:
            logger.error("User roles not found")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        
        if user_role_code != UserRoleEnum.CUSTOMER.display_name:
            logger.error("User role code is not customer")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

        if user.status != StatusEnum.ACTIVE or user.customer.status != StatusEnum.ACTIVE:
            logger.error("User or customer is not active")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        
        case = get_case_by_customer_id(db, user.customer.id)
        if not case:
            logger.error("Case not found")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        
        if case.is_initial_payment_completed is False:
            logger.error("Case initial payment is not completed")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

        lawyer = case.case_lawyers[0].lawyer
        law_firm = lawyer.lawyer_law_firms[0].law_firm
        if not law_firm:
            logger.error("Law firm not found")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        
        if law_firm.engage_form_url != request.client_code:
            logger.error("Client code does not match")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        
        if case.is_onboarding_completed is True:
            logger.error("Customer is already onboarded for this case")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)

        request_data = EngageCompleteEventRequest( case_id=case.id )

        event_data = Event(
            event_type=EventType.ENGAGE_SUBMIT,
            payload={
                "request_data": request_data,
                "is_customer":True,
                "current_user": user,
            },
            user_id=int(user.id),
            current_user=user,
        )

        await event_dispatcher.dispatch_event(db, event_data)

        success, messages = extract_status_messages(event_data.response) # type: ignore[arg-type]
        if not success:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages)

        return EngageCompleteResponse(
            success=True,
            message=messages,
            data={},
        )

    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to verify the engage request", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify the engage request",
        ) from None
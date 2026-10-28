"""Cal.com API endpoints."""

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.logging import get_logger
from app.core.security import get_current_active_user
from app.db.models.user import User
from app.db.services.cal import (
    get_available_slots,
    get_first_available_slot,
    parse_webhook_payload,
    # process_webhook_event,
    verify_webhook_signature,
)
from app.schemas.v1.base import ResponseMessage
from app.schemas.v1.cal import (
    CalAvailabilityRequest,
    CalAvailabilityResponse,
    CalWebhookResponse,
    BookFreeCallRequest,
    BookFreeCallResponse,
)
from app.enums.events import EventType
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.event import Event
from app.utils.helpers import extract_status_messages
from app.utils.dependencies import get_db
from sqlalchemy.orm import Session
from app.core.config import settings

logger = get_logger(__name__)

router = APIRouter()


@router.get("/availability", response_model=CalAvailabilityResponse)
async def get_cal_availability(
    request_data: CalAvailabilityRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
) -> CalAvailabilityResponse:
    """Return the first available consultation slot from Cal.com."""
    try:
        slots = get_available_slots(
            start=request_data.start,
            end=request_data.end,
        )
        first_slot = get_first_available_slot(slots)
        return CalAvailabilityResponse(
            success=True,
            message=[
                ResponseMessage(
                    success=True,
                    message=(
                        "Available consultation slot retrieved successfully"
                        if first_slot
                        else "No available consultation slots found"
                    ),
                )
            ],
            data=first_slot or {},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except httpx.HTTPStatusError as e:
        logger.exception(
            "Cal.com availability request failed for user %s: %s",
            current_user.email,
            e.response.text,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Failed to fetch availability from Cal.com",
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get Cal.com availability: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Cal.com availability",
        ) from e


@router.post("/webhooks", response_model=CalWebhookResponse)
async def cal_webhooks(request: Request, db: Session = Depends(get_db)) -> CalWebhookResponse:
    """Receive booking, cancellation, and reschedule events from Cal.com."""

    from app.db.services.cal import save_shcedule_info_for_timeline

    payload = await request.body()
    signature = request.headers.get("x-cal-signature-256")

    if not verify_webhook_signature(payload, signature):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Cal.com webhook signature",
        )

    try:
        event = parse_webhook_payload(payload)
        trigger = (
            event.get("triggerEvent")
            or event.get("trigger_event")
            or event.get("trigger")
            or ""
        )
        event_type = event.get("payload", {}).get("type", "")
        if trigger == "BOOKING_CREATED" and event_type == str(settings.CAL_NN_CALL_BACK_SLUG):
            event_data = Event(
                event_type=EventType.BOOK_FREE_CALL,
                payload={
                    "cal_event": event,
                },
                user_id=None,
                current_user=None,
            )
            await event_dispatcher.dispatch_event(db, event_data)

            success, messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]
            return CalWebhookResponse(
                success=success,
                message=messages,
                data={},
            )
        
        if trigger == "BOOKING_CREATED" and event_type == str(settings.CAL_MEETING_SLUG):
            success = save_shcedule_info_for_timeline(db, event)
            return CalWebhookResponse(
                success=success,
                message=ResponseMessage(
                    success=True,
                    message="Schedule info saved for timeline event",
                ),
                data={},
            )

        # Acknowledge other triggers so Cal.com does not retry into 500s
        return CalWebhookResponse(
            success=True,
            message=[
                ResponseMessage(
                    success=True,
                    message=f"Ignored trigger: {trigger or 'unknown'}",
                )
            ],
            data={"trigger_event": trigger, "handled": False},
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.exception("Error processing Cal.com webhook: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error processing Cal.com webhook: {e!s}",
        ) from e


@router.post("/book-free-call", response_model=BookFreeCallResponse)
async def book_free_call(
    request: BookFreeCallRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)) -> BookFreeCallResponse:
    """Book a free call with the user."""
    from app.db.services.case import get_case_by_id
    from app.enums.component import ComponentEnum
    from app.db.services.timeline_event import get_timeline_event
    try:
        case = get_case_by_id(db, request.case_id)
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Case not found",
            )
        
        if not case.case_customers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        customer = case.case_customers[0].customer
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Customer not found",
            )

        user = customer.user
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        
        if user.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to book this free call",
            )
        
        timeline_info = get_timeline_event(db,
         request.case_id, 
         component_enum=ComponentEnum.BOOK_FREE_CALL_NN_CARD.value
        )
        if timeline_info is not None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Free call already booked",
            )
        
        cal_event = {
            "triggerEvent": "BOOK_FREE_CALL",
            "case_id": request.case_id,
            "customer_email": user.email,
            "phone_number": request.phone_number,
        }

        event_data = Event(
                event_type=EventType.BOOK_FREE_CALL,
            payload={
                "cal_event": cal_event,
            },
            user_id=None,
            current_user=None,
        )
        await event_dispatcher.dispatch_event(db, event_data)

        success, messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]
        
        return BookFreeCallResponse(
            success=success,
            message=messages,
            data={},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error booking free call: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error booking free call: {e!s}",
        ) from e
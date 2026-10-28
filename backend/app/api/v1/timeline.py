import logging
from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session, selectinload

from app.core.security import get_current_active_user
from app.db.models import Lawyer
from app.db.models.case import Case
from app.db.models.case_customer import CaseCustomer
from app.db.models.customer import Customer
from app.db.models.user import User
from app.db.services.lawyer import get_interested_lawyers
from app.db.services.timeline_event import (
    check_customer_case_access,
    check_lawyer_case_access,
    get_match_confirmed_lawyers_service,
    get_matches_by_case_id,
    get_timeline_events_by_case_id,
)
from app.enums.case import CaseStatusEnum
from app.enums.events import EventType
from app.enums.lawyer import LawyerStatusEnum
from app.enums.user import StatusEnum
from app.enums.user_role import UserRoleEnum
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.base import BaseResponse, ResponseMessage
from app.schemas.v1.event import Event
from app.schemas.v1.lawyer import (
    InterestedLawyersListResponse,
)
from app.schemas.v1.timeline_event import (
    AcceptLawyerRequest,
    AcceptLawyerResponse,
    AcceptLawyerResponseData,
    GetMatchedLawyersRequest,
    GetMatchedLawyersResponse,
    GetTimelineEventResponse,
    GetTimeLineEventsRequest,
    LawyerMatchCreateRequest,
    LawyerMatchCreateResponse,
    MarkOnboardingCompletedRequest,
    MarkOnboardingCompletedResponse,
    MatchConfirmedLawyersRequest,
    MatchConfirmedLawyersResponse,
    SendLawyerToCustomerRequest,
    SendLawyerToCustomerResponse,
)
from app.utils.dependencies import get_db
from app.utils.encryption import decrypt_id
from app.utils.formatters import format_case_number
from app.utils.helpers import extract_status_messages
from app.utils.validators import validate_order_params
from app.db.services.case import get_case_no_by_id

logger = logging.getLogger(__name__)

router = APIRouter()


def _raise_forbidden_error(detail: list[dict[str, object]]) -> None:
    """Raise HTTPException for forbidden access."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _raise_event_processing_error() -> NoReturn:
    """Raise HTTPException for event processing failure."""
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=[{"success": False, "message": "Event processing failed"}],
    )


def _raise_internal_server_error(detail: str) -> NoReturn:
    """Raise HTTPException for internal server error."""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail
    )


def _raise_validation_error(detail: list[dict[str, str]]) -> NoReturn:
    """Raise HTTPException for validation errors."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _raise_bad_request(detail: list[dict[str, object]]) -> None:
    """Raise HTTPException for bad request."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.get("/timeline", response_model=BaseResponse[GetTimelineEventResponse])
async def get_timeline_events(
    current_user: User = Depends(get_current_active_user),
    request: GetTimeLineEventsRequest = Depends(),
    db: Session = Depends(get_db),
) -> BaseResponse[GetTimelineEventResponse]:
    """Get timeline events with related details including event type, case, and user information."""
    try:
        err_detail = [
            {
                "success": False,
                "message": "You are not authorized to access this resource",
            }
        ]

        # Validate order_by and order_dir parameters
        allowed_order_fields = {
            "id",
            "created_at",
            "updated_at",
        }
        # Normalize order_dir to lowercase for validation
        normalized_order_dir = request.order_dir if request.order_dir in ["asc", "desc"] else request.order_dir.lower() if isinstance(request.order_dir, str) else request.order_dir
        validate_order_params(request.order_by, normalized_order_dir, allowed_order_fields)

        role_ids = [user_role.role_id for user_role in current_user.user_roles]
        role = UserRoleEnum.from_id(role_ids[0])
        role_code = role.display_name

        # Check if case is archived and raise not found error if user is not a navigator
        if role != UserRoleEnum.NAVIGATOR:
            case_status = db.query(Case.status).filter(Case.id == request.case_id).scalar()
            if case_status == CaseStatusEnum.ARCHIVED:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=[{"success": False, "message": "Case not found"}])

        if role != UserRoleEnum.NAVIGATOR and request.role_code is not None:
            _raise_forbidden_error(err_detail)
        if role == UserRoleEnum.CUSTOMER and current_user.customer:
            valid = check_customer_case_access(
                db, int(current_user.customer.id), int(request.case_id)
            )
            if not valid:
                _raise_forbidden_error(err_detail)

        if role == UserRoleEnum.LAWYER and current_user.lawyer:
            valid = check_lawyer_case_access(db, int(request.case_id), current_user)
            if not valid:
                _raise_forbidden_error(err_detail)

        request_role_code = None
        if request.role_code:
            request_role_code = UserRoleEnum.from_code(request.role_code).display_name

        lawyer_id = request.lawyer_id if request.lawyer_id else None

        timeline_events_data, total_count, matched_lawyers = get_timeline_events_by_case_id(
            db,
            int(request.case_id),
            request.page,
            request.limit,
            request.order_dir,
            request.order_by,
            role_code,
            current_user,
            request_role_code,
            None,
            lawyer_id,
        )
        
        # Format case number from service response
        case_no = get_case_no_by_id(db, int(request.case_id))
        case_number = format_case_number(case_no.case_no)
        
        return BaseResponse[GetTimelineEventResponse](
            success=True,
            message=[
                ResponseMessage(
                    success=True, message="Timeline events retrieved successfully"
                )
            ],
            data=GetTimelineEventResponse(
                case_number=case_number,
                timeline_data=timeline_events_data,
                matched_lawyers=matched_lawyers if matched_lawyers else None,
                total_count=total_count,
                records_in_page=len(timeline_events_data)

            ),
        )
    except HTTPException:
        # re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.exception(f"Error in retrieve timeline events: {e}")
        _raise_internal_server_error("Failed to retrieve timeline events")


@router.post("/timeline/lawyer-match", response_model=LawyerMatchCreateResponse)
async def create_lawyer_match_endpoint(
    request_data: LawyerMatchCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LawyerMatchCreateResponse:
    """Confirm system-generated expert matches for a case."""
    from app.db.services.case import is_case_archived
    try:

        case_id = int(request_data.case_id)

        if is_case_archived(db, case_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot confirm lawyer matches for this case."}])

        # Create event data
        event_data = Event(
            event_type=EventType.CASE_LAWYER_MATCH_CONFIRMED,
            payload={
                "request_data": request_data,
                "current_user": current_user,
            },
            user_id=int(current_user.id),
            current_user=current_user,
        )

        # Dispatch the event (wait for completion)
        await event_dispatcher.dispatch_event(db, event_data)

        # Extract status messages from event responses
        response = event_data.response
        if response is None:
            _raise_event_processing_error()

        success, messages = extract_status_messages(response)
        if not success:
            _raise_validation_error(messages)

        # Extract the data from the EventResponseData object
        event_response = response[EventType.CASE_LAWYER_MATCH_CONFIRMED.value]
        match_data = event_response.data
        if not isinstance(match_data, list):
            match_data = [match_data]

        # Convert dict messages to ResponseMessage objects
        response_messages = [
            ResponseMessage(success=bool(msg["success"]), message=str(msg["message"]))
            for msg in messages
        ]

        return LawyerMatchCreateResponse(
            success=True, message=response_messages, data=match_data
        )

    except ValueError:
        raise
    except HTTPException:
        # re-raise HTTPExceptions
        raise
    except RequestValidationError:
        raise
    except Exception as e:
        logger.exception(f"Error in create expert matches: {e}")
        _raise_internal_server_error("Failed to create expert matches")


@router.get("/timeline/matching-lawyers", response_model=GetMatchedLawyersResponse)
async def get_matched_lawyers(
    current_user: User = Depends(get_current_active_user),
    request_data: GetMatchedLawyersRequest = Depends(),
    db: Session = Depends(get_db),
) -> GetMatchedLawyersResponse:
    """Get matched experts for a case."""
    try:
        # Get all matches for the case
        lawyer_data = get_matches_by_case_id(db, request_data)
        total_count = len(lawyer_data)
        records_in_page = len(lawyer_data)

        if total_count == 0:
            message = "No data found"
        else:
            message = "Matched experts retrieved successfully"
        
        # in case if is_match_confirmed is True, then set is_profile_sent to True
        is_case_notified = False
        case = db.query(Case).filter(Case.id == request_data.case_id).first()
        if case and case.is_match_confirmed:
            is_case_notified = True

        return GetMatchedLawyersResponse(
            success=True,
            message=[
                ResponseMessage(
                    success=True, message=message
                )
            ],
            data=lawyer_data,
            total_count=total_count,
            records_in_page=records_in_page,
            is_case_notified=is_case_notified
        )
    except HTTPException:
        # re-raise HTTPExceptions
        raise
    except Exception as e:
        logger.exception(f"Error in get matched experts: {e}")
        _raise_internal_server_error("Failed to get matched experts")


@router.post("/timeline/send-lawyer-to-customer", response_model=SendLawyerToCustomerResponse)
async def send_lawyer_to_customer(
    request_data: SendLawyerToCustomerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SendLawyerToCustomerResponse:
    """Review and Send interestedlawyer to customer."""
    from app.db.services.case import is_case_archived
    try:

        case_id = int(request_data.case_id)

        if is_case_archived(db, case_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot send a lawyer to a customer for this case."}])

        # Create event data
        event_data = Event(
            event_type=EventType.CASE_LAWYER_INTR_CONFIRMED,
            payload={
                "request_data":request_data,
                "current_user": current_user
            },
            user_id=int(current_user.id),
        )

        # Dispatch the event (wait for completion)
        await event_dispatcher.dispatch_event(db, event_data)

        # Extract status messages from event responses
        response = event_data.response
        if response is None:
            _raise_event_processing_error()

        success, messages = extract_status_messages(response)
        if not success:
            _raise_validation_error(messages)

        # Extract the data from the EventResponseData object
        event_response = response[EventType.CASE_LAWYER_INTR_CONFIRMED.value]
        match_data = event_response.data
        response_data = match_data.get("updated_lawyer_ids",[])

        # Convert dict messages to ResponseMessage objects
        response_messages = [
            ResponseMessage(
                success=bool(msg["success"]),
                message=str(msg["message"])
            ) for msg in messages
        ]

        return SendLawyerToCustomerResponse(
            success=True,
            message=response_messages,
            data=response_data
        )

    except ValueError:
        raise
    except HTTPException:
        # re-raise HTTPExceptions
        raise
    except RequestValidationError:
        raise
    except Exception as e:
        logger.exception(f"Error in send expert to customer: {e}")
        _raise_internal_server_error("Failed to send expert to customer")


@router.get(
    "/timeline/interested-lawyers",
    response_model=BaseResponse[InterestedLawyersListResponse],
)
async def get_interested_lawyers_endpoint(
    case_id: str,
    page: int = 1,
    limit: int = 10,
    order_by: str = "created_at",
    order_dir: str = "desc",
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BaseResponse[InterestedLawyersListResponse]:
    """
    Get all experts who have matches with INTERESTED status.

    Returns expert details along with associated user and case information.
    Supports pagination, ordering, and optional filtering by case_id.
    """
    try:
        #  Validate pagination parameters
        if page < 1:
            _raise_bad_request(
                detail=[
                    {"success": False, "message": "Page number must be greater than 0"}
                ]
            )

        if limit < 10 or limit > 50:
            _raise_bad_request(
                detail=[{"success": False, "message": "Limit must be between 10 and 50"}]
            )

        #  Decrypt case_id if provided
        decrypted_case_id = None
        if case_id:
            try:
                decrypted_id = decrypt_id(case_id)
                if decrypted_id is None:
                    _raise_bad_request(
                        detail=[{"success": False, "message": "Invalid case_id format"}]
                    )
                decrypted_case_id = int(decrypted_id)  # type: ignore[arg-type]
            except Exception:
                _raise_bad_request(
                    detail=[{"success": False, "message": "Invalid case_id format"}]
                )

        #  Get interested lawyers from service
        response_data = get_interested_lawyers(
            db=db,
            case_id=decrypted_case_id,
            page=page,
            limit=limit,
            order_by=order_by,
            order_dir=order_dir,
        )

        if response_data.total_count == 0:
            message = "No data found"
        else:
            message = "Interested experts fetched successfully"

        return BaseResponse[InterestedLawyersListResponse](
            success=True,
            message=[
                ResponseMessage(
                    success=True, message=message
                )
            ],
            data=response_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch interested experts: {e!s}")
        _raise_internal_server_error("Failed to fetch interested experts")


@router.post("/timeline/accept-lawyer", response_model=AcceptLawyerResponse)
async def accept_lawyer(
    request: AcceptLawyerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> AcceptLawyerResponse:
    """Accept a lawyer for a case by customer or navigator."""
    from app.db.services.case import is_case_archived
    try:
        # Get user role
        role_ids = [user_role.role_id for user_role in current_user.user_roles]
        role = UserRoleEnum.from_id(role_ids[0])

        # Decrypt IDs (already decrypted by DecryptedRequest)
        case_id = int(request.case_id)
        lawyer_id = int(request.lawyer_id)

        if is_case_archived(db, case_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot accept a lawyer for this case."}])

        base_query = (
            db.query(CaseCustomer, Customer)
            .join(Customer, CaseCustomer.customer_id == Customer.id)
            .filter(CaseCustomer.case_id == case_id)
        )

        case_customer = None
        customer = None

        if role == UserRoleEnum.CUSTOMER:
            # Restrict to current user's customer_id
            customer_obj = db.query(Customer).filter(Customer.user_id == int(current_user.id)).first()
            if not customer_obj:
                _raise_bad_request(detail=[{"success": False, "message": "Customer not found"}])
            # Now filter base_query for this customer
            result = base_query.filter(CaseCustomer.customer_id == customer_obj.id).first()  # type: ignore[union-attr]
            if not result:
                _raise_bad_request(detail=[{"success": False, "message": "Case not found or not assigned to this customer"}])
            case_customer, customer = result  # type: ignore[misc]
            if customer is None:
                _raise_bad_request(detail=[{"success": False, "message": "Customer not found in result"}])
            customer_id = customer.id

        elif role == UserRoleEnum.NAVIGATOR:
            # Just get the first case_customer for this case
            result = base_query.first()
            if not result:
                _raise_bad_request(detail=[{"success": False, "message": "Case not found or not assigned to a customer"}])
            case_customer, customer = result  # type: ignore[misc]
            if customer is None:
                _raise_bad_request(detail=[{"success": False, "message": "Customer not found in result"}])
            customer_id = customer.id
        else:
            _raise_bad_request(detail=[{"success": False, "message": "Unauthorized role for this operation"}])

        # At this point, case_customer should not be None due to the checks above
        assert case_customer is not None, "Case customer should not be None at this point"

        # Fetch lawyer object
        lawyer = db.query(Lawyer).options(selectinload(Lawyer.expertises), selectinload(Lawyer.accredited_specialisms)).filter(Lawyer.id == lawyer_id).first()
        if not lawyer:
            _raise_bad_request(detail=[{"success": False, "message": "Expert not found"}])

        if lawyer.user.status != StatusEnum.ACTIVE or lawyer.status != LawyerStatusEnum.ACTIVE:
            _raise_bad_request(detail=[{"success": False, "message": "Expert is not active"}])

        case_number = format_case_number(case_customer.case.case_no)

        # Create and dispatch event with required objects (no case_customer)
        event_data = Event(
            event_type=EventType.CUSTOMER_ACCEPT_LAWYER,
            payload={
                "case_id": case_id,
                "lawyer_id": lawyer_id,
                "customer_id": customer_id,
                "lawyer": lawyer,
                "customer": customer,
                "case_number": case_number,
            },
            user_id=int(current_user.id),
            current_user=current_user,
        )

        await event_dispatcher.dispatch_event(db, event_data)

        # Check event success and format messages properly
        if not event_data.response:
            _raise_bad_request(detail=[{"success": False, "message": "Event dispatch failed: No response"}])

        success, messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]
        if not success:
            _raise_bad_request(detail=messages)  # type: ignore[arg-type]

        # If we reach here, the event was successful
        # Convert messages to ResponseMessage objects
        response_messages = [
            ResponseMessage(success=bool(msg["success"]), message=str(msg["message"]))
            for msg in messages
        ]

        return AcceptLawyerResponse(
            success=True,
            message=response_messages,
            data=AcceptLawyerResponseData(
                case_id=str(case_id),
                lawyer_id=str(lawyer_id),
            )
        )
    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to accept expert: {e!s}")
        _raise_internal_server_error("Failed to accept expert")


@router.post("/timeline/mark-onboarding-completed", response_model=MarkOnboardingCompletedResponse)
async def mark_onboarding_completed(
    request_data: MarkOnboardingCompletedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> MarkOnboardingCompletedResponse:
    """Mark onboarding completed for a case."""
    from app.db.services.case import is_case_archived
    try:

        case_id = int(request_data.case_id)

        if is_case_archived(db, case_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot mark this case as onboarded."}])

        event_data = Event(
            event_type=EventType.ENGAGE_SUBMIT,
            payload={
                "request_data": request_data,
                "is_customer":False,
                "current_user": current_user,
            },
            user_id=int(current_user.id),
            current_user=current_user,
        )

        await event_dispatcher.dispatch_event(db, event_data)

        success, messages = extract_status_messages(event_data.response) # type: ignore[arg-type]
        if not success:
            _raise_validation_error(messages)

        return MarkOnboardingCompletedResponse(
            success=True,
            message=messages, # type: ignore[arg-type]
            data={}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in mark onboarding completed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark onboarding completed"
        ) from e


@router.get(
    "/timeline/match_confirmed_lawyers",
    response_model=BaseResponse[MatchConfirmedLawyersResponse],
)
async def get_match_confirmed_lawyers(
    current_user: User = Depends(get_current_active_user),
    request: MatchConfirmedLawyersRequest = Depends(),
    db: Session = Depends(get_db),
) -> BaseResponse[MatchConfirmedLawyersResponse]:
    """
    Get confirmed matched lawyers for a case.

    This endpoint receives a case_id in the request and fetches the data of lawyers
    who are matched to the case and have is_confirmed set to True. The response
    includes the list of confirmed matched lawyers with lawyer details.
    """
    try:
        # Validate case access for customer
        if current_user.customer:
            valid = check_customer_case_access(
                db, int(current_user.customer.id), int(request.case_id)
            )
            if not valid:
                _raise_forbidden_error([
                    {
                        "success": False,
                        "message": "You are not authorized to access this case",
                    }
                ])

        # Get confirmed matched lawyers
        confirmed_lawyers = get_match_confirmed_lawyers_service(db, int(request.case_id))

        if confirmed_lawyers == []:
            message = "No data found"
        else:
            message = "Confirmed matched experts retrieved successfully"

        return BaseResponse[MatchConfirmedLawyersResponse](
            success=True,
            message=[
                ResponseMessage(
                    success=True,
                    message=message,
                )
            ],
            data=MatchConfirmedLawyersResponse(
                total_count=len(confirmed_lawyers),
                records_in_page=len(confirmed_lawyers),
                match_confirmed_lawyers=confirmed_lawyers,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get match confirmed experts: {e!s}")
        _raise_internal_server_error("Failed to get match confirmed experts")

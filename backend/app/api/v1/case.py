"""Case API endpoints."""

import logging
from datetime import datetime
from operator import truediv

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.error_handling import raise_bad_request
from app.core.security import get_current_active_user
from app.db.models import Case, CaseCustomer, Customer, Lawyer, User
from app.enums.lawyer import LawyerStatusEnum
from app.enums.user import StatusEnum
from app.db.services.case import (
    get_all_cases_service,
    get_case_by_id,
    get_case_details_service,
    get_case_summary_service,
    is_case_awarded,
)
from app.db.services.customer import get_customer_by_user_id
from app.db.services.general import get_case_customer_user, get_lawyer_by_user_id, verify_case_access
from app.db.services.lawyer import check_lawyer_match_exists
from app.enums.case import CaseStatusEnum
from app.enums.events import EventType
from app.enums.user_role import UserRoleEnum
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.base import BaseResponse, ResponseMessage
from app.schemas.v1.case import (
    CaseArchiveRequest,
    CaseArchiveResponse,
    CaseDeclineRequest,
    CaseDeclineResponse,
    CaseDetailsData,
    CaseDetailsRequest,
    CaseDetailsResponse,
    CaseInterestRequest,
    CaseInterestResponse,
    CaseListItem,
    CaseListResponseData,
    CaseMoreDetailsRequest,
    CaseMoreDetailsResponse,
    CaseSearchRequest,
    CaseSummaryRequest,
    CaseSummaryResponse,
    CaseSummaryUpdateRequest,
    CaseSummaryUpdateResponse,
    CustomerInfo,
    CaseSummaryData,
    PartiesInvolved,
)
from app.schemas.v1.event import Event
from app.utils.dependencies import get_db
from app.utils.encryption import decrypt_id
from app.utils.formatters import format_case_number
from app.utils.helpers import extract_status_messages
from app.utils.validators import validate_order_params

logger = logging.getLogger(__name__)

router = APIRouter()


def _create_case_response_data(case: Case, role_code: str, current_lawyer_id: int | None = None) -> CaseListItem:
    """Create case response data from a Case model."""
    # Handle customer information - case might not have customers
    customer_info = None
    if case.case_customers and len(case.case_customers) > 0:
        customer = case.case_customers[0].customer
        # Get user data from the customer relationship
        user = customer.user
        customer_info = CustomerInfo(
            id=str(customer.id),
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email if role_code == UserRoleEnum.NAVIGATOR.display_name else None,
            phone=user.phone if role_code == UserRoleEnum.NAVIGATOR.display_name else None,
        )

    # Check if case is awarded to another lawyer
    is_awarded_to_another = False
    if current_lawyer_id is not None and case.is_lawyer_assigned:
        # Check if the case is awarded to a different lawyer
        case_lawyer_ids = [cl.lawyer_id for cl in case.case_lawyers]
        is_awarded_to_another = current_lawyer_id not in case_lawyer_ids

    # Build status tags based on case flags
    tags: list[str] = []
    if not is_awarded_to_another:
        if case.is_onboarding_completed:
            tags.append("onboarding_completed")
        elif case.is_initial_payment_completed:
            tags.append("initial_payment_completed")
        elif case.is_lawyer_assigned:
            tags.append("lawyer_assigned")
        elif case.is_profile_card_sent:
            tags.append("profile_card_sent")
        elif case.is_match_confirmed:
            tags.append("match_confirmed")
        elif case.is_kyc_completed:
            tags.append("kyc_completed")
        else:
            tags.append("case_opened")
    # If is_awarded_to_another is True, tags will remain empty

    return CaseListItem(
        id=str(case.id),
        case_no=format_case_number(case.case_no),  # type: ignore[arg-type]
        case_type=case.case_type.value if case.case_type else None,
        priority=case.priority.value if case.priority else None,
        status=case.status.value if case.status else None,
        start_date=case.start_date,  # type: ignore[arg-type]
        created_at=case.created_at,  # type: ignore[arg-type]
        customer=customer_info,
        tags=tags,
    )


def _raise_decline_reason_validation_error() -> None:
    """Raise HTTPException for invalid decline reason."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "success": False,
            "message": "At least one decline reason is required in the 'reason' field",
        },
    )


def _handle_case_action_common_logic(
    db: Session,
    current_user: User,
    request_data: CaseInterestRequest | CaseDeclineRequest | CaseMoreDetailsRequest,
) -> tuple[int, int]:
    """
    Common business logic for case interest, decline, and more details operations.

    Returns:
        tuple[int, int]: (case_id, lawyer_id) as integers for service calls
    """
    # Get user roles
    role_ids = [user_role.role_id for user_role in current_user.user_roles]

    # Determine lawyer_id based on user role and request
    lawyer_id = request_data.lawyer_id

    if UserRoleEnum.LAWYER.id in role_ids:
        # User is a lawyer
        if lawyer_id is None:
            # Get lawyer_id from current user
            lawyer = get_lawyer_by_user_id(db, int(current_user.id))
            if not lawyer:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "success": False,
                        "message": "Expert profile not found",
                    },
                )
            lawyer_id = str(lawyer.id)  # Keep as string for consistency with schema
        else:
            # Check if provided lawyer_id matches current user's lawyer_id
            current_lawyer = get_lawyer_by_user_id(db, int(current_user.id))
            if not current_lawyer or str(current_lawyer.id) != lawyer_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "message": "Access denied: Expert ID mismatch",
                    },
                )
    elif UserRoleEnum.NAVIGATOR.id in role_ids:
        # User is a navigator - lawyer_id is mandatory
        if lawyer_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Expert ID is mandatory for navigators",
                },
            )
        else:
            result = (
                db.query(Lawyer.status, User.status)
                .join(User, Lawyer.user_id == User.id)
                .filter(Lawyer.id == lawyer_id)
                .first()
            )
            if (
                result is None
                or result[0] != LawyerStatusEnum.ACTIVE
                or result[1] != StatusEnum.ACTIVE
            ):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"success": False, "message": "Expert not found or inactive. Action cannot be performed."},
                )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Access denied: insufficient permissions",
            },
        )

    # Validate that lawyer_id is available
    if lawyer_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Expert ID is required"},
        )

    if is_case_awarded(db, int(request_data.case_id)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Case already awarded to an expert",
            },
        )

    return int(request_data.case_id), int(lawyer_id)


def _raise_invalid_role_error() -> None:
    """Raise HTTPException for invalid role code."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=[{"success": False, "message": "Invalid role code"}],
    )


def _raise_customer_not_found_error() -> None:
    """Raise HTTPException for customer not found."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=[{"success": False, "message": "Customer not found"}],
    )


def _raise_lawyer_not_found_error() -> None:
    """Raise HTTPException for expert not found."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=[{"success": False, "message": "Expert not found"}],
    )


def _raise_no_records_found_error() -> None:
    """Raise HTTPException for no records found."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"success": False, "message": "No records found"},
    )


def _raise_event_processing_error() -> None:
    """Raise HTTPException for event processing failure."""
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=[{"success": False, "message": "Event processing failed"}],
    )


def _raise_validation_error(detail: str) -> None:
    """Raise HTTPException for validation errors."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.get("/case", response_model=BaseResponse[CaseListResponseData])
async def get_cases_endpoint(
    request: CaseSearchRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> BaseResponse[CaseListResponseData]:
    """Get list of cases with pagination and ordering."""
    try:
        # Validate order_by and order_dir parameters
        allowed_order_fields = {
            "id",
            "start_date",
            "case_no",
            "case_type",
            "priority",
            "status",
            "created_at"
        }
        validate_order_params(request.order_by, request.order_dir, allowed_order_fields)

        role_ids = [user_role.role_id for user_role in current_user.user_roles]
        if len(role_ids) == 0:
            _raise_invalid_role_error()
        role_code = UserRoleEnum.from_id(role_ids[0]).display_name

        # If role is lawyer or customer and case_status is archieved then raise error
        if role_code != UserRoleEnum.NAVIGATOR.display_name and request.case_status == CaseStatusEnum.ARCHIVED:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=[{"success": False, "message": "No records found"}],
            )

        current_lawyer_id = None
        if role_code == UserRoleEnum.NAVIGATOR.display_name:
            id = current_user.id
        elif role_code == UserRoleEnum.CUSTOMER.display_name:
            customer = get_customer_by_user_id(db, int(current_user.id))
            if not customer:
                _raise_customer_not_found_error()
            id = customer.id  # type: ignore[union-attr]
        elif role_code == UserRoleEnum.LAWYER.display_name:
            lawyer = get_lawyer_by_user_id(db, int(current_user.id))
            if not lawyer:
                _raise_lawyer_not_found_error()
            id = lawyer.id  # type: ignore[union-attr]
            current_lawyer_id = int(lawyer.id)  # Store lawyer ID for tag filtering
        else:
            _raise_invalid_role_error()

        # Get cases from service
        cases, total_count = get_all_cases_service(
            db=db,
            request_data=request,
            role_code=role_code,
            user_id=id,
        )

        # Create response data
        case_items = [_create_case_response_data(case, role_code, current_lawyer_id) for case in cases]

        if total_count == 0:
            message = "No data found"
        else:
            message = "Cases fetched successfully"

        return BaseResponse(
            success=True,
            message=[
                ResponseMessage(success=True, message=message)
            ],
            data=CaseListResponseData(
                total_count=total_count,
                records_in_page=len(case_items),
                cases=case_items,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error fetching cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to fetch cases"},
        ) from None


@router.post("/case/interest", response_model=CaseInterestResponse)
async def case_interest_endpoint(
    request_data: CaseInterestRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CaseInterestResponse:
    """Update case interest status for a lawyer."""
    from app.db.services.case import is_case_archived
    try:
        case_id = int(request_data.case_id)
        if is_case_archived(db, case_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot submit case interest for this case."}])

        # Dispatch the CASE_INTEREST event with request_data and current_user
        event_data = Event(
            event_type=EventType.CASE_INTEREST,
            payload={
                "request_data": request_data,
                "current_user": current_user,
            },
            user_id=int(current_user.id),
            current_user=current_user,
        )

        await event_dispatcher.dispatch_event(db, event_data)

        success, messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]
        # Check for specific error cases and raise appropriate HTTPExceptions
        if not success:
            return CaseInterestResponse(
                success=False,
                message=messages,  # type: ignore[arg-type]
                data=[],
            )

        # Return response with empty data
        return CaseInterestResponse(
            success=True,
            message=messages,  # type: ignore[arg-type]
            data=[],
        )

    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in raise case interest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to raise case interest"},
        ) from None


@router.post("/case/archive", response_model=CaseArchiveResponse)
async def archive_cases_endpoint(
    request_data: CaseArchiveRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CaseArchiveResponse:
    """Archive open cases by ID (navigator only)."""
    try:

        decrypted_case_ids: list[int] = []
        for encrypted_id in request_data.case_ids:
            decrypted = decrypt_id(encrypted_id)
            if not decrypted:
                raise_bad_request(message=f"Invalid case_id: {encrypted_id}")
            decrypted_case_ids.append(int(decrypted))

        archive_event_data = Event(
            event_type=EventType.ARCHIVE_CASE,
            payload={"case_ids": decrypted_case_ids, "manual_archive": True},
            user_id=int(current_user.id),
            current_user=current_user,
        )
        await event_dispatcher.dispatch_event(db, archive_event_data)

        success, messages = extract_status_messages(archive_event_data.response)  # type: ignore[arg-type]
        if not success:
            return CaseArchiveResponse(
                success=False,
                message=messages,  # type: ignore[arg-type]
                data=[],
            )

        return CaseArchiveResponse(
            success=True,
            message=messages,  # type: ignore[arg-type]
            data=[],
        )

    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error archiving cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to archive cases"},
        ) from None


@router.post("/case/unarchive", response_model=CaseArchiveResponse)
async def unarchive_cases_endpoint(
    request_data: CaseArchiveRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CaseArchiveResponse:
    """Unarchive cases by ID (navigator only)."""
    try:

        decrypted_case_ids: list[int] = []
        for encrypted_id in request_data.case_ids:
            decrypted = decrypt_id(encrypted_id)
            if not decrypted:
                raise_bad_request(message=f"Invalid case_id: {encrypted_id}")
            decrypted_case_ids.append(int(decrypted))

        archive_event_data = Event(
            event_type=EventType.UNARCHIVE_CASE,
            payload={"case_ids": decrypted_case_ids},
            user_id=int(current_user.id),
            current_user=current_user,
        )
        await event_dispatcher.dispatch_event(db, archive_event_data)

        success, messages = extract_status_messages(archive_event_data.response)  # type: ignore[arg-type]
        if not success:
            return CaseArchiveResponse(
                success=False,
                message=messages,  # type: ignore[arg-type]
                data=[],
            )

        return CaseArchiveResponse(
            success=True,
            message=messages,  # type: ignore[arg-type]
            data=[],
        )

    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error unarchiving cases: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to unarchive cases"},
        ) from None


@router.post("/case/decline", response_model=CaseDeclineResponse)
async def case_decline_endpoint(
    request_data: CaseDeclineRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CaseDeclineResponse:
    """Update case decline status for a lawyer."""
    from app.db.services.case import is_case_archived
    try:
        # Validate decline reason structure
        if (
            not request_data.decline_reason.get("reason")
            or not isinstance(request_data.decline_reason.get("reason"), list)
            or len(request_data.decline_reason.get("reason", [])) == 0
        ):
            _raise_decline_reason_validation_error()
        

        case_id = int(request_data.case_id)
        if is_case_archived(db, case_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot decline case interest for this case."}])

        # Dispatch the CASE_DECLINE event with request_data and current_user
        event_data = Event(
            event_type=EventType.CASE_DECLINE,
            payload={
                "request_data": request_data,
                "current_user": current_user,
            },
            user_id=int(current_user.id),
            current_user=current_user,
        )

        await event_dispatcher.dispatch_event(db, event_data)

        success, messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]

        # Check for specific error cases and raise appropriate HTTPExceptions
        if not success:
            return CaseDeclineResponse(
                success=False,
                message=messages,  # type: ignore[arg-type]
                data=[],
            )

        # Return response with empty data
        return CaseDeclineResponse(
            success=True,
            message=messages,  # type: ignore[arg-type]
            data=[],
        )

    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in decline case: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to decline case"},
        ) from None


@router.post("/case/more-details", response_model=CaseMoreDetailsResponse)
async def case_more_details_endpoint(
    request_data: CaseMoreDetailsRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CaseMoreDetailsResponse:
    """Update case more details status for a lawyer."""
    from app.db.services.case import is_case_archived
    try:

        try:
            case_id = int(request_data.case_id)
        except ValueError:
            _raise_validation_error("Invalid case ID format")
        
        if is_case_archived(db, case_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot request case more details for this case."}])

        # Use common logic to handle role-based access and validation
        case_id, lawyer_id = _handle_case_action_common_logic(db, current_user, request_data)

        case = get_case_by_id(db, case_id)
        if case is None:
            _raise_validation_error("Case not found")
        # Type assertion: case is guaranteed to be non-None after the check above
        assert case is not None
        case_number = format_case_number(case.case_no)
        timestamp = datetime.now().isoformat()

        # Get the lawyer object using the validated lawyer_id
        if current_user and current_user.lawyer and current_user.lawyer.id == lawyer_id:
            lawyer = current_user.lawyer
        else:
            lawyer = db.query(Lawyer).filter(Lawyer.id == lawyer_id).first()
        if lawyer is None:
            _raise_validation_error("Expert not found")
        assert lawyer is not None

        validate = is_case_awarded(db, int(case_id))
        if validate:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={
                "success": False,
                "message": "Case already awarded to an expert",
            })

        valid = check_lawyer_match_exists(db, case_id, lawyer)
        if valid is False:
            _raise_validation_error("No match found for this case and expert")

        customer = get_case_customer_user(db, case_id)
        if customer is None:
            _raise_validation_error("Customer not found")

        # Create event data
        event_data = Event(
            event_type=EventType.CASE_MORE_DETAILS,
            payload={
                "timestamp": timestamp,
                "case": case,
                "lawyer_request": request_data.query_text,
                "case_number": case_number,
                "current_user": current_user,
                "lawyer": lawyer,
                "customer": customer,
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

        # Explicit type check that mypy will understand
        if isinstance(response, dict):
            success, messages = extract_status_messages(response)
        else:
            _raise_event_processing_error()

        response_messages = [
            ResponseMessage(success=bool(msg["success"]), message=str(msg["message"]))
            for msg in messages
        ]

        # Return response with empty data
        return CaseMoreDetailsResponse(
            success=success,
            message=response_messages,
            data=[],
        )
    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in requesting case more details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request case more details",
        ) from None


@router.get("/case/details", response_model=CaseDetailsResponse)
async def get_case_details_endpoint(
    current_user: User = Depends(get_current_active_user),
    request_data: CaseDetailsRequest = Depends(),
    db: Session = Depends(get_db),
) -> CaseDetailsResponse:
    """Get case details with role-based filtering."""
    try:
        # Get user role
        role_ids = [user_role.role_id for user_role in current_user.user_roles]
        if len(role_ids) == 0:
            _raise_invalid_role_error()
        role_code = UserRoleEnum.from_id(role_ids[0]).display_name

        # Determine user ID based on role
        if role_code == UserRoleEnum.NAVIGATOR.display_name:
            user_id = int(current_user.id)
        elif role_code == UserRoleEnum.CUSTOMER.display_name:
            customer = current_user.customer
            if not customer:
                _raise_customer_not_found_error()
            user_id = int(customer.id)
        elif role_code == UserRoleEnum.LAWYER.display_name:
            lawyer = current_user.lawyer
            if not lawyer:
                _raise_lawyer_not_found_error()
            user_id = int(lawyer.id)
        else:
            _raise_invalid_role_error()

        # Get case details from service
        case_details = get_case_details_service(
            db=db,
            case_id=int(request_data.case_id),
            role_code=role_code,
            user_id=user_id,
        )

        # Create response data
        parties_involved = PartiesInvolved(**case_details["parties_involved"])
        action_buttons = case_details["action_buttons"]
        data = CaseDetailsData(
            status=case_details["status"],
            case_summary=case_details["case_summary"],
            is_ai_summary_generated=case_details["is_ai_summary_generated"],
            parties_involved=parties_involved,
            action_buttons=action_buttons,
            analytics_data=case_details.get("analytics_data"),
        )

        return CaseDetailsResponse(
            success=True,
            message=[
                ResponseMessage(
                    success=True, message="Case details fetched successfully"
                )
            ],
            data=data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in fetching case details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to fetch case details"},
        ) from None


@router.put("/case/summary", response_model=CaseSummaryUpdateResponse)
async def update_case_summary(
    request_data: CaseSummaryUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CaseSummaryUpdateResponse:
    """Update case summary for a lawyer."""
    from app.db.services.case import is_case_archived
    try:
        # Convert list of CaseSummaryItem to list of dicts
        case_summary_list = [item.model_dump() for item in request_data.case_summary]

        case_id = int(request_data.case_id)
        if is_case_archived(db, case_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot update case summary for this case."}])

        event_data = Event(
            event_type=EventType.CASE_SUMMARY_UPDATE,
            payload={
                "case_id": int(request_data.case_id),
                "case_summary": case_summary_list,
                "is_update_summary": True,
            },
            user_id=int(current_user.id),
            current_user=current_user,
        )

        await event_dispatcher.dispatch_event(db, event_data)

        success, messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Failed to update case summary",
                },
            )

        return CaseSummaryUpdateResponse(
            success=True,
            message=messages,  # type: ignore[arg-type]
            data=[],
        )
    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in updating case summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to update case summary"},
        ) from None


@router.get("/case/summary", response_model=CaseSummaryResponse)
async def get_case_summary(
    current_user: User = Depends(get_current_active_user),
    request_data: CaseSummaryRequest = Depends(),
    db: Session = Depends(get_db),
) -> CaseSummaryResponse:
    """Get case summary for a case."""
    try:
        case_id = int(request_data.case_id)
        
        # Get user role code
        role_ids = [user_role.role_id for user_role in current_user.user_roles]
        if len(role_ids) == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"success": False, "message": "User role not found"}
            )
        role_code = UserRoleEnum.from_id(role_ids[0]).display_name

        if role_code == UserRoleEnum.CUSTOMER.display_name:
                user_id = current_user.customer.id
        elif role_code == UserRoleEnum.LAWYER.display_name:
            user_id = current_user.lawyer.id
        else:
            user_id = current_user.id
        verify_case_access(db, case_id, role_code, user_id)
        
        case_summary = get_case_summary_service(db, case_id, role_code)
        return CaseSummaryResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Case summary fetched successfully")],
            data=case_summary,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in getting case summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to get case summary"},
        ) from None


@router.post("/case/generate-ai-summary", response_model=CaseSummaryResponse)
async def generate_ai_case_summary(
    request_data: CaseSummaryRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CaseSummaryResponse:
    """Generate AI case summary for a case."""
    from app.db.services.case import is_case_archived
    try:
        case_id = int(request_data.case_id)

        if is_case_archived(db, case_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot generate AI case summary for this case."}])

        case = get_case_by_id(db, case_id)
        if case is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Case not found",
                },
            )
        if case.is_ai_summary_generated:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "AI summary already generated",
                },
            )
        event_data = Event(
            event_type=EventType.GENERATE_AI_CASE_SUMMARY,
            payload={
                "case_id": case_id,
            },
            user_id=int(current_user.id),
            current_user=current_user,
        )
        await event_dispatcher.dispatch_event(db, event_data)

        success, messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Failed to generate AI case summary",
                },
            )
        
        ai_summary_data = event_data.response['generate_ai_case_summary'].data
        if not ai_summary_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Failed to generate AI case summary. Please try again later.",
                },
            )

        data = CaseSummaryData(
            case_id=str(case_id),
            case_summary=ai_summary_data,
        )
        return CaseSummaryResponse(
            success=True,
            message=messages,  # type: ignore[arg-type]
            data=data,
        )
    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in generating AI case summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to generate AI case summary"},
        ) from None
import logging
from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user, get_current_user_if_provided
from app.db.models.lawyer import Lawyer
from app.db.models.triage import Triage
from app.db.models.user import User
from app.db.services.customer import get_customer_by_user_id
from app.db.services.triage import search_triage_service, start_triage_session, submit_triage_data
from app.enums.events import EventType
from app.enums.triage import TriageStatusEnum
from app.enums.user_role import UserRoleEnum
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.base import ResponseMessage
from app.schemas.v1.engage import FullQuestionModel
from app.schemas.v1.event import Event
from app.schemas.v1.triage import (
    GetTriageRequest,
    GetTriageResponse,
    SubmitTriageRequest,
    SubmitTriageResponse,
    TriageData,
    TriageListCustomerInfo,
    TriageListItem,
    TriageListRequest,
    TriageListResponse,
    TriageListResponseData,
    UpdateTriageRequest,
    UpdateTriageResponse,
)
from app.utils.dependencies import get_db
from app.utils.helpers import extract_status_messages
from app.utils.validators import validate_phone_number

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_lawyer_by_user_id(db: Session, user_id: int) -> Lawyer | None:
    """Get lawyer by user ID."""
    return db.query(Lawyer).filter(Lawyer.user_id == user_id).first()


def _process_triage_to_list_item(triage: Triage) -> TriageListItem:
    """Convert a triage ORM object into a list item response."""
    linked_case = None
    if triage.case_triages and triage.case_triages[0] and triage.case_triages[0].case:
        linked_case = triage.case_triages[0].case

    case_type_value = (
        linked_case.case_type.value
        if linked_case and linked_case.case_type
        else "Family Law"
    )
    status_value = (
        "Moving forward"
        if linked_case
        else (triage.status.value if triage.status else "In progress")
    )
    questions_answered = triage.questions_answered or 0

    customer_info = None
    if triage.customer and triage.customer.user:
        customer_user = triage.customer.user
        customer_info = TriageListCustomerInfo(
            first_name=customer_user.first_name,
            last_name=customer_user.last_name,
            email=customer_user.email,
            id=str(triage.customer.id),
        )

    completed_date = triage.updated_at if triage.status == TriageStatusEnum.COMPLETED else None
    start_date = triage.created_at.date() if triage.created_at else None

    return TriageListItem(
        title="Triage",
        triage_id=str(triage.id),
        case_type=case_type_value,
        triage_status=status_value,
        start_date=start_date,
        completed_date=completed_date,
        created_at=triage.created_at,
        updated_at=triage.updated_at,
        no_of_questions_answered=questions_answered,
        customer=customer_info,
    )


def _raise_bad_request(detail: list[dict[str, object]]) -> NoReturn:
    """Raise HTTPException for bad request."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _raise_internal_server_error(detail: list[dict[str, object]]) -> NoReturn:
    """Raise HTTPException for internal server error."""
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


@router.get("/triage/list", response_model=TriageListResponse)
async def get_triage_list(
    request: TriageListRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TriageListResponse:
    """Get triage list with pagination, search, and status filtering."""
    try:
        role_ids = [user_role.role_id for user_role in current_user.user_roles]
        if len(role_ids) == 0:
            _raise_bad_request(detail=[{"success": False, "message": "Invalid role code"}])
        role_code = UserRoleEnum.from_id(role_ids[0]).display_name

        if role_code == UserRoleEnum.CUSTOMER.display_name:
            customer = get_customer_by_user_id(db, int(current_user.id))
            if not customer:
                _raise_bad_request(detail=[{"success": False, "message": "Customer not found"}])
            entity_id = customer.id  # type: ignore[union-attr]
        elif role_code == UserRoleEnum.LAWYER.display_name:
            lawyer = _get_lawyer_by_user_id(db, int(current_user.id))
            if not lawyer:
                _raise_bad_request(detail=[{"success": False, "message": "Expert not found"}])
            entity_id = lawyer.id  # type: ignore[union-attr]
        elif role_code == UserRoleEnum.NAVIGATOR.display_name:
            entity_id = current_user.id
        else:
            _raise_bad_request(detail=[{"success": False, "message": "Invalid role code"}])

        triages, total_count = search_triage_service(
            db=db,
            id=int(entity_id),
            page=request.page,
            limit=request.limit,
            order_by=request.order_by,
            order_dir=request.order_dir,
            role_code=role_code,
            search=request.search,
            status=request.status,
        )
        items = [_process_triage_to_list_item(triage) for triage in triages]
        message = "No data found" if total_count == 0 else "Triage data fetched successfully"
        return TriageListResponse(
            success=True,
            message=[ResponseMessage(success=True, message=message)],
            data=TriageListResponseData(
                total_count=total_count,
                records_in_page=len(items),
                triages=items,
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch triage list: {e!s}")
        _raise_internal_server_error(
            detail=[{"success": False, "message": "Failed to fetch triage list"}]
        )


@router.get("/triage", response_model=GetTriageResponse)
async def get_triage(
    request: GetTriageRequest = Depends(),
    current_user: User | None = Depends(get_current_user_if_provided),
    db: Session = Depends(get_db),
) -> GetTriageResponse:
    """Create a triage for the customer email and return questions with answers if available."""
    try:
        if request.customer_email is None and request.triage_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Customer email or triage ID is required"}],
            )
        
        if request.triage_id:
            from app.db.services.triage import get_triage_by_id
            triage = get_triage_by_id(db, request.triage_id)
            if triage is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=[{"success": False, "message": "Triage not found"}],
                )
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=[{"success": False, "message": "You are not authorized to view triage data"}],
                )
            # User is logged in, check role-based access
            user_roles = [user_role.role_id for user_role in current_user.user_roles]
            # Check for navigator
            if UserRoleEnum.NAVIGATOR.id in user_roles:
                pass  # Navigators can access any triage
            # Check for customer
            elif UserRoleEnum.CUSTOMER.id in user_roles:
                customer = get_customer_by_user_id(db, int(current_user.id))
                if not customer:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=[{"success": False, "message": "Customer not found"}],
                    )
                if customer.id != triage.customer_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=[{"success": False, "message": "You are not authorized to view this triage"}],
                    )
        triage_id, triage_status, question_data, customer_info, case_info = start_triage_session(
            db, request, current_user
        )
        triage_questions = FullQuestionModel.model_validate(question_data)

        return GetTriageResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Triage data retrieved successfully")],
            data=TriageData(
                triage_id=str(triage_id),
                triage_status=triage_status,
                question_data=triage_questions,
                customer_info=customer_info,
                case_info=case_info,
            ),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in get_triage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[{"success": False, "message": "Failed to retrieve triage data"}],
        ) from e


@router.patch("/triage", response_model=UpdateTriageResponse)
async def patch_triage(
    request: UpdateTriageRequest,
    current_user: User | None = Depends(get_current_user_if_provided),
    db: Session = Depends(get_db),
) -> UpdateTriageResponse:
    """Update triage answers for the given triage."""
    from app.db.services.triage import get_triage_by_id
    try:
        if request.answers is None or len(request.answers) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Answers are required"}],
            )
        
        triage = get_triage_by_id(db, request.triage_id)
        if triage is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=[{"success": False, "message": "Triage not found"}],
            )
        
        if triage.status == TriageStatusEnum.COMPLETED:
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=[{"success": False, "message": "You are not authorized to update this triage"}],
                )
            # if current_user.id != triage.customer_id:
            #     raise HTTPException(
            #         status_code=status.HTTP_403_FORBIDDEN,
            #         detail=[{"success": False, "message": "You are not authorized to update this triage"}],
            #     )

        result, _triage_id = submit_triage_data(db, request, update_flag=True)
        if result is False:
            raise ValueError("Error in updating triage answers")  # noqa: TRY301

        return UpdateTriageResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Triage answers updated successfully")],
            data={},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in update_triage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[{"success": False, "message": "Failed to update triage data"}],
        ) from e


@router.post("/triage", response_model=SubmitTriageResponse)
async def submit_triage(
    request: SubmitTriageRequest,
    current_user: User | None = Depends(get_current_user_if_provided),
    db: Session = Depends(get_db),
) -> SubmitTriageResponse:
    """Submit triage answers, create customer account, and open a triage case."""
    from app.db.services.triage import get_triage_by_id
    try:
        if not validate_phone_number(request.phone_number):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Invalid phone number format"}],
            )
        
        triage = get_triage_by_id(db, request.triage_id)
        if triage is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=[{"success": False, "message": "Triage not found"}],
            )

        if triage.status == TriageStatusEnum.COMPLETED:
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=[{"success": False, "message": "You are not authorized to re-submit this triage"}],
                )
            if current_user.id != triage.user_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=[{"success": False, "message": "You are not authorized to re-submit this triage"}],
                )

            request.triage_id = triage.id

            event_data = Event(
                event_type=EventType.TRIAGE_RE_SUBMIT,
                payload={
                    "request_data": request,
                },
                user_id=int(current_user.id),
                current_user=current_user,
            )
            await event_dispatcher.dispatch_event(db, event_data)
            response = event_data.response
            if response is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=[{"success": False, "message": "Event processing failed"}],
                )

            success, messages = extract_status_messages(response)  # type: ignore[arg-type]
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=messages,
                )
        
            return SubmitTriageResponse(
                success=True,
                message=messages,
                data=response[EventType.TRIAGE_RE_SUBMIT.value].data,
            )

        else:
            event_data = Event(
                event_type=EventType.TRIAGE_SUBMIT,
                payload={
                    "request_data": request,
                },
                user_id=None,
                current_user=None,
            )
            await event_dispatcher.dispatch_event(db, event_data)

            response = event_data.response
            if response is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=[{"success": False, "message": "Event processing failed"}],
                )

            success, messages = extract_status_messages(response)  # type: ignore[arg-type]
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=messages,
                )

            return SubmitTriageResponse(
                success=True,
                message=messages,
                data=response[EventType.TRIAGE_SUBMIT.value].data,
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in submit_triage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[{"success": False, "message": "Failed to submit triage data"}],
        ) from e

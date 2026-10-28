import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.models.user import User
from app.db.services.kyc import (
    check_customer_engage_access,
    check_lawyer_engage_access,
    get_kyc_data,
    TRIAGE_OMIT_QUESTIONS,
)
from app.db.services.case import is_case_archived
from app.enums.events import EventType
from app.enums.user_role import UserRoleEnum
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.base import ResponseMessage
from app.schemas.v1.engage import (
    FullQuestionModel,
    GetKycRequest,
    GetKycResponse,
    SubmitKycRequest,
    SubmitKycResponse,
    UpdateKycRequest,
    UpdateKycResponse,
)
from app.schemas.v1.event import Event
from app.utils.dependencies import get_db
from app.utils.helpers import extract_status_messages

logger = logging.getLogger(__name__)

router = APIRouter()

CUSTOMER_OMIT_QUESTIONS = ["25", "27"]


def _raise_forbidden_error(detail: list[dict[str, object]]) -> None:
    """Raise HTTPException for unauthorized access."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def _raise_bad_request_error(detail: str) -> None:
    """Raise HTTPException for bad request."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


@router.get("/kyc", response_model=GetKycResponse)
async def get_kyc(
    current_user: User = Depends(get_current_active_user),
    request: GetKycRequest = Depends(),
    db: Session = Depends(get_db),
) -> GetKycResponse:
    """Get Kyc data for the user."""
    from app.db.services.case import get_case_by_id
    from app.db.services.general import get_triage_by_case_id
    from app.db.models.triage_question_answers import TriageQuestionAnswers
    from app.db.models.question_answers import QuestionAnswers
    import json
    try:

        err_detail = [{"success": False, "message": "You are not authorized to access this resource"}]
        if is_case_archived(db, int(request.case_id)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot submit or view Alignment Check for this case."}])     
   
        role_ids = [user_role.role_id for user_role in current_user.user_roles]
        role = UserRoleEnum.from_id(role_ids[0])
        if role == UserRoleEnum.CUSTOMER:
            valid = check_customer_engage_access(db, current_user, int(request.case_id))
            if not valid:
                _raise_forbidden_error(err_detail)

        if role == UserRoleEnum.LAWYER:
            valid = check_lawyer_engage_access(db, current_user, int(request.case_id))
            if not valid:
                _raise_forbidden_error(err_detail)

        kyc_data = get_kyc_data(db, int(request.case_id))

        case = get_case_by_id(db, int(request.case_id))
        if case is None:
            _raise_bad_request_error([{"success": False, "message": "Case not found"}])  # noqa: TRY301
        
        rule_list = []
        if case.is_triage:
            triage = get_triage_by_case_id(db, int(request.case_id))
            if triage is None:
                _raise_bad_request_error([{"success": False, "message": "Triage not found"}])  # noqa: TRY301
            triage_question_answers = db.query(QuestionAnswers).join(TriageQuestionAnswers, QuestionAnswers.id == TriageQuestionAnswers.question_answer_id).filter(TriageQuestionAnswers.triage_id == triage.id).all()

            filtered_questions = [qa for qa in triage_question_answers if str(qa.question_identifier) in '8' ]
            question_ids = {str(qa.question_identifier) for qa in filtered_questions} if filtered_questions is not None else {}
            if '8' in question_ids:
                    # Build answer dictionary directly without intermediate list
                answer_dict = {}
                for qa in filtered_questions:
                    try:
                        parsed_answer = json.loads(str(qa.answer))
                        if parsed_answer and len(parsed_answer) > 0:
                            value = [d['value'] for d in parsed_answer]
                            answer_dict[str(qa.question_identifier)] = value
                    except (json.JSONDecodeError, IndexError, TypeError):
                        # Skip this question if parsing fails or data is malformed
                        continue
                
                # Check question 4 answer — marriage and other share the same KYC options
                if answer_dict.get("8", [])[0] in ["yes_second_opinion", "yes_change_family_law_professional", "yes_mediation_breaking_down"]:
                    rule_list = [
                        {
                            "identifier": "5",
                            "operator": "is",
                            "value": "yes",
                            "source": "kyc"
                        },
                        {
                        "identifier": "8",
                        "operator": "is",
                        "value": "yes",
                        "source": "triage"
                        }
                    ]

        if len(rule_list) > 0:
            question_22 = kyc_data.get("22")
            if question_22 is not None:
                question_22["rules"] = rule_list

        if role == UserRoleEnum.CUSTOMER:
            for question_id in CUSTOMER_OMIT_QUESTIONS:
                kyc_data.pop(question_id, None)

        if case.is_triage:
            for question_id in TRIAGE_OMIT_QUESTIONS:
                kyc_data.pop(question_id, None)

        kyc_questions = FullQuestionModel.model_validate(kyc_data)

        return GetKycResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Kyc data retrieved successfully")],
            data=kyc_questions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in get_kyc: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=[{"success": False, "message": "Failed to retrieve kyc data"}]) from e


@router.patch("/kyc", response_model=UpdateKycResponse)
async def patch_kyc(
    request: UpdateKycRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UpdateKycResponse:
    """Update KYC for the user."""
    try:
        from app.db.services.general import get_case_customer_user
        from app.db.services.resolve import get_resolve_from_case_id
        from app.db.services.kyc import get_resolve_options_for_kyc, submit_kyc_data
        from app.db.services.case import get_case_by_id

        if is_case_archived(db, int(request.case_id)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot submit KYC for this case."}])
        
        if request.answers is None or len(request.answers) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "Answers are required"}])

        err_detail = [{"success": False, "message": "You are not authorized to access this resource"}]
        role_ids = [user_role.role_id for user_role in current_user.user_roles]
        role = UserRoleEnum.from_id(role_ids[0])
        
        # if role == UserRoleEnum.CUSTOMER:
        #     customer_user = current_user
        #     valid = check_customer_engage_access(db, current_user, int(request.case_id))
        #     if not valid:
        #         _raise_forbidden_error(err_detail)  # noqa: TRY301
        if role == UserRoleEnum.NAVIGATOR:
            customer_user = get_case_customer_user(db, int(request.case_id))
            if customer_user is None:
                _raise_bad_request_error("Customer not found or not active")  # noqa: TRY301
        elif role == UserRoleEnum.CUSTOMER:
            _raise_forbidden_error(err_detail)  # noqa: TRY301
        else:
            _raise_forbidden_error(err_detail)  # noqa: TRY301
        

        case = get_case_by_id(db, int(request.case_id))
        if case is None:
            _raise_bad_request_error([{"success": False, "message": "Case not found"}])  # noqa: TRY301
        
        if case.is_triage:
            resolve = None
            from app.db.models.case_engage import CaseEngage
            from app.db.services.kyc import create_engage_case
            case_engage = db.query(CaseEngage).filter(CaseEngage.case_id == case.id).first()
            engage_id = case_engage.engage_id if case_engage is not None else None
            if engage_id is None:
                engage_id = create_engage_case(db, case.id, int(current_user.id)) # type: ignore           
            options = get_resolve_options_for_kyc(db, None, int(engage_id))
        else :
            resolve = get_resolve_from_case_id(db, int(request.case_id))
            if resolve is None:
                _raise_bad_request_error([{"success": False, "message": "Resolve not found for the case"}])  # noqa: TRY301
            options = get_resolve_options_for_kyc(db, int(resolve.id), None)

        
        if case.is_kyc_completed:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Alignment Check already completed",
                },
            )

        result, kyc_id = submit_kyc_data(db, customer_user, request, options, update_flag=True)
        if result is False:
            raise ValueError("Error in updating alignment check answers")  # noqa: TRY301
        
        return UpdateKycResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Alignment Check answers updated successfully")],
            data={}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in update_kyc: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=[{"success": False, "message": "Failed to update Alignment Check data"}]) from e


@router.post("/kyc", response_model=SubmitKycResponse)
async def submit_kyc(
    request: SubmitKycRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> SubmitKycResponse:
    """Submit KYC data for the user."""

    from app.enums.engage import ActionEnum

    try:

        if is_case_archived(db, int(request.case_id)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot submit Alignment Check for this case."}])

        if request.action == ActionEnum.HOLD:
            event_data = Event(
                event_type=EventType.CUSTOMER_KYC_HOLD,
                payload={
                    "request_data": request,
                    "current_user": current_user,
                },
                user_id=int(current_user.id),
                current_user=current_user,
            )
            await event_dispatcher.dispatch_event(db, event_data)

            success, messages = extract_status_messages(event_data.response) # type: ignore[arg-type]
            if not success:
                return SubmitKycResponse(
                    success=False,
                    message=messages,
                    data=FullQuestionModel({})
                )
            
            return SubmitKycResponse(
                success=True,
                message=messages,
                data=event_data.response[EventType.CUSTOMER_KYC_HOLD.value].data # type: ignore[index]
            )
        
        else:
            # Create event using the new EventCreate schema
            event_data = Event(
                event_type=EventType.CUSTOMER_KYC_SUBMIT,
                payload={
                    "request_data": request,
                    "current_user": current_user,
                },
                user_id=int(current_user.id),
                current_user=current_user,
            )

            # Dispatch event using the new system
            await event_dispatcher.dispatch_event(db, event_data)

            success, messages = extract_status_messages(event_data.response) # type: ignore[arg-type]
            if not success:
                return SubmitKycResponse(
                    success=False,
                    message=messages,
                    data=FullQuestionModel({})
                )

            return SubmitKycResponse(
                success=True,
                message=messages,   # type: ignore[arg-type]
                data=event_data.response[EventType.CUSTOMER_KYC_SUBMIT.value].data # type: ignore[index]
            )
    except HTTPException:
        raise
    except RequestValidationError:
        raise
    except ValueError:
        raise
    except Exception as e:
        logger.exception(f"Error in submit_kyc: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=[{"success": False, "message": "Failed to submit Alignment Check data"}]) from e
        # return SubmitKycResponse(
        #     success=False,
        #     message=[ResponseMessage(success=False, message=message)],
        #     data=FullQuestionModel({})
        # )

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import NoReturn

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_active_user, get_current_user_if_provided
from app.db.models.lawyer import Lawyer
from app.db.models.resolve import Resolve
from app.db.models.user import User
from app.db.services.customer import get_customer_by_user_id
from app.db.services.question_answers import validate_save_answer
from app.db.services.general import get_lawyers_for_case, get_all_navigator_emails, get_user_role_info
from app.db.services.timeline_event import parse_lawyer_data
from app.db.services.resolve import (
    create_resolve,
    get_latest_questions,
    get_resolve_by_id,
    get_result,
    map_answers,
    search_resolve_service,
)
from app.enums.events import EventType
from app.enums.resolve import ResolveStatusEnum
from app.enums.user_role import UserRoleEnum
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.base import ResponseMessage
from app.schemas.v1.customer import CustomerInfo as CustInfo, CustomerRegistrationResponseData
from app.schemas.v1.event import Event
from app.schemas.v1.resolve import (
    AnswerQuestionRequest,
    AnswerQuestionResponse,
    AnswerQuestionResponseData,
    CustomerInfo,
    FullQuestionModel,
    GetResolveQuestionsRequest,
    ResolveCreate,
    ResolveData,
    ResolveListItem,
    ResolveListRequest,
    ResolveListResponse,
    ResolveListResponseData,
    ResolveQuestionResponse,
    ResolveSubmitRequest,
    ResolveSubmitResponse,
    CaseInfo,
)
from app.utils.dependencies import get_db
from app.utils.encryption import decrypt_id
from app.utils.helpers import extract_status_messages
from app.utils.formatters import format_case_number

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_lawyer_by_user_id(db: Session, user_id: int) -> Lawyer | None:
    """Get lawyer by user ID."""
    return db.query(Lawyer).filter(Lawyer.user_id == user_id).first()


def _process_resolve_to_list_item(resolve: Resolve) -> ResolveListItem:
    """Optimized processing with minimal operations."""

    # Pre-compute values to avoid repeated property access
    case_type_value = resolve.case_type.value if resolve.case_type else "Family Law"
    title_value = resolve.title or "Nova Recommendations"
    questions_answered = resolve.questions_answered or 0
    status_value = "Moving forward" if resolve.case_resolves and resolve.case_resolves[0] and resolve.case_resolves[0].case else (resolve.status.value if resolve.status else "In progress")

    # Optimize customer info extraction
    customer_info = None
    if resolve.customer and resolve.customer.user:
        customer_user = resolve.customer.user
        customer_info = CustomerInfo(
            first_name=customer_user.first_name,
            last_name=customer_user.last_name,
            email=customer_user.email,
            id=str(resolve.customer.id)
        )

    # Optimize date handling
    completed_date = resolve.updated_at if resolve.status == ResolveStatusEnum.COMPLETED else None

    return ResolveListItem(
        title=title_value,
        resolve_id=str(resolve.id),
        case_type=case_type_value,
        resolve_status=status_value,
        start_date=resolve.resolve_date,
        completed_date=completed_date,
        created_at=resolve.created_at,
        updated_at=resolve.updated_at,
        no_of_questions_answered=questions_answered,
        customer=customer_info,
    )

def _raise_event_processing_error() -> NoReturn:
    """Raise HTTPException for event processing failure."""
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=[{"success": False, "message": "Event processing failed"}]
    )


def _raise_bad_request(detail: list[dict[str, object]]) -> None:
    """Raise HTTPException for bad request."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _raise_internal_server_error(detail: list[dict[str, object]]) -> None:
    """Raise HTTPException for internal server error."""
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)


def _raise_not_found(detail: str) -> None:
    """Raise HTTPException for not found."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def _raise_validation_error(detail: str) -> None:
    """Raise HTTPException for validation errors."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _raise_unprocessable_entity_error(detail: list[dict[str, str]]) -> None:
    """Raise HTTPException for unprocessable entity errors."""
    raise RequestValidationError(detail)


def _raise_forbidden_error(detail: str) -> None:
    """Raise HTTPException for forbidden errors."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


@router.get("/resolve", response_model=ResolveQuestionResponse)
async def get_resolve_questions(
    current_user: User | None = Depends(get_current_user_if_provided),
    request: GetResolveQuestionsRequest = Depends(),
    db: Session = Depends(get_db),
):
    """Get resolve questions and answers, if resolve_id is not provided, create a new resolve session. If the resolve has result, it will include the result data in the response."""
    try:
        customer = None
        if current_user is not None:    #allows customer to create a new resolve session with login
            customer = get_customer_by_user_id(db, int(current_user.id))
        # get questions from questions.json
        questions = None
        with open(settings.QUESTIONS_FILE_PATH) as f:
            questions = json.load(f)

        if questions is None:
            _raise_internal_server_error(detail=[{"success": False, "message": "Failed to load resolve questions"}])

        case_info = None
        if request.resolve_id is None:
            if current_user and customer is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user. Please login again.")
            customer_id = customer.id if customer else None

            # Create a new resolve record with only required fields
            date = datetime.now().date()
            resolve_data = ResolveCreate(
                customer_id=customer_id,
                resolve_date=date,
                user_id=None,
                result_reference_id=None,
                title=f"Nova Recommendations {date.strftime('%d/%m/%Y')}",
                questions_answered=0
            )
            resolve = create_resolve(db, resolve_data)
            if not resolve:
                _raise_internal_server_error(detail=[{"success": False, "message": "Error creating Nova Recommendations"}])
            resolve_id = resolve.id

            questions = get_latest_questions(questions)

            resolve_questions = FullQuestionModel.model_validate(questions)
            return ResolveQuestionResponse(
                success=True,
                message=[ResponseMessage(success=True, message="Resolve questions fetched successfully")],
                data=ResolveData(
                    resolve_id=resolve_id,
                    title=resolve.title,
                    questions_answered=resolve.questions_answered,
                    resolve_status=resolve.status,
                    result=None,
                    info=None,
                    created_at=resolve.created_at,
                    updated_at=resolve.updated_at,
                    question_data=resolve_questions,
                    lawyers=None
                )
            )
        else:
            resolve = get_resolve_by_id(db, int(request.resolve_id))
            if not resolve:
                _raise_bad_request(detail=[{"success": False, "message": "Nova Recommendations not found"}])
            if not current_user:
                expiry_time = datetime.now(timezone.utc) - timedelta(
                    hours=(settings.RESOLVE_EXPIRY_HOURS or 24)
                )
                if resolve.customer_id:
                    logger.error(f"Customer {resolve.customer_id} does not match resolve {resolve.id}")
                    _raise_forbidden_error(
                        detail=[{"success": False, "message": "Nova Recommendations doesn’t exist."}]
                    )
                elif resolve.created_at < expiry_time:
                    logger.error(f"Resolve {resolve.id} has expired")
                    _raise_bad_request(
                        detail=[{"success": False, "message": "Nova Recommendations has expired"}]
                    )
            else:
                # User is logged in, check role-based access
                user_roles = [user_role.role_id for user_role in current_user.user_roles]
                # Check for navigator
                if UserRoleEnum.NAVIGATOR.id in user_roles:
                    pass  # Navigators can access any resolve
                # Check for customer
                elif UserRoleEnum.CUSTOMER.id in user_roles:
                    if not customer or customer.id != resolve.customer_id:
                        logger.error(f"Customer {customer.id} does not match resolve {resolve.id}")
                        _raise_forbidden_error(
                            detail=[{"success": False, "message": "Nova Recommendations doesn’t exist."}]
                        )
                # Check for lawyer
                elif UserRoleEnum.LAWYER.id in user_roles:
                    lawyer_obj = _get_lawyer_by_user_id(db, int(current_user.id))
                    if not lawyer_obj:
                        logger.error(f"Lawyer {current_user.id} not found")
                        _raise_forbidden_error(
                            detail=[{"success": False, "message": "Nova Recommendations doesn’t exist."}]
                        )
                    # The resolve must be associated with a case
                    case_resolve = resolve.case_resolves[0] if resolve.case_resolves else None
                    if not case_resolve:
                        logger.error(f"No case assigned to resolve {resolve.id}")
                        _raise_forbidden_error(
                            detail=[{"success": False, "message": "Nova Recommendations doesn’t exist.   "}]
                        )
                    case = case_resolve.case
                    # Check if this lawyer is assigned to this case via CaseLawyer
                    from app.db.models import CaseLawyer, Match
                    is_case_lawyer = (
                        db.query(CaseLawyer)
                        .filter(
                            CaseLawyer.case_id == case.id,
                            CaseLawyer.lawyer_id == lawyer_obj.id,
                        )
                        .first()
                        is not None
                    )
                    # Or there is a Match for this lawyer and case
                    is_matched = (
                        db.query(Match)
                        .filter(
                            Match.case_id == case.id,
                            Match.lawyer_id == lawyer_obj.id,
                        )
                        .first()
                        is not None
                    )
                    # Additionally, case must not be assigned to ANY other (different) lawyer
                    # assigned_lawyers = (
                    #     db.query(CaseLawyer)
                    #     .filter(CaseLawyer.case_id == case.id)
                    #     .all()
                    # )
                    # assigned_lawyer_ids = {cl.lawyer_id for cl in assigned_lawyers}
                    # The resolve lawyer must match, and the case cannot be exclusively assigned to another
                    if not (is_case_lawyer or is_matched):
                        logger.error(f"Lawyer {lawyer_obj.id} not assigned to case {case.id}")
                        _raise_forbidden_error(
                            detail=[{"success": False, "message": "Nova Recommendations doesn’t exist."}]
                        )
                    # if len(assigned_lawyer_ids) > 0 and lawyer_obj.id not in assigned_lawyer_ids:
                    #     logger.error(f"Lawyer {lawyer_obj.id} not assigned to case {case.id}")
                    #     _raise_forbidden_error(
                    #         detail=[{"success": False, "message": "Nova Recommendations doesn’t exist."}]
                    #     )
                else:
                    logger.error(f"Unrecognized user role {user_roles}")
                    _raise_forbidden_error(
                        detail=[{"success": False, "message": "Nova Recommendations doesn’t exist."}]
                    )

            resolve_id = resolve.id

        answer_mapped_questions, info = map_answers(resolve, questions)
        result = None
        if resolve.result_reference_id and resolve.status == ResolveStatusEnum.COMPLETED:
            result = get_result(resolve)
        if resolve.case_resolves:
            case = resolve.case_resolves[0].case
            case_info = CaseInfo(
                id=str(case.id),
                case_no=format_case_number(case.case_no),
                type=case.case_type,
                status=case.status,
                is_kyc_completed=case.is_kyc_completed
            )

        # Get lawyers associated with the case based on resolve reference
        lawyers_data = None
        if resolve.result_reference_id:
            try:
                lawyer_ids, lawyers = get_lawyers_for_case(db, resolve, limit_flag=3)
                lawyers_data = parse_lawyer_data(lawyers) if lawyers else []
            except Exception as e:
                logging.warning(f"Failed to get lawyers for case: {e}")
                lawyers_data = []
        recommended = (result or {}).get("recommended_approach") or None
        if recommended and not recommended.get("result_type"):
            recommended = None
        questions = FullQuestionModel.model_validate(answer_mapped_questions)
        return ResolveQuestionResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Resolve questions fetched successfully")],
            data=ResolveData(
                resolve_id=resolve_id,
                title=resolve.title,
                questions_answered=resolve.questions_answered,
                resolve_status=resolve.status,
                result=recommended,
                info=info,
                created_at=resolve.created_at,
                updated_at=resolve.updated_at,
                question_data=questions,
                case=case_info,
                lawyers=lawyers_data
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Resolve questions fetch failed: {e!s}")
        message = "Resolve questions fetch failed"
        _raise_internal_server_error(detail=[{"success": False, "message": message}])


@router.patch("/resolve", response_model=AnswerQuestionResponse)
async def answer_question(
    request: AnswerQuestionRequest,
    current_user: User | None = Depends(get_current_user_if_provided),
    db: Session = Depends(get_db),
):
    """Answer resolve questions, overwrite existing answers and save new answers if not present in the database."""
    # from app.db.services.question_answers import get_resolve_result
    from app.db.services.case import get_case_by_customer_id
    # from app.db.services.question_answers import get_resolve_circumstance
    # from app.db.services.resolve import format_resolve_question_answers
    # from app.db.services.ai import generate_ai_recommendation
    try:

        # get questions from questions.json
        questions = None
        with open(settings.QUESTIONS_FILE_PATH) as f:
            questions = json.load(f)

        if not questions:
            _raise_internal_server_error(detail=[{"success": False, "message": "Failed to load resolve questions"}])
        
        resolve_map = None
        with open(settings.RESOLVE_MAP_FILE_PATH) as f:
            resolve_map = json.load(f)

        if not resolve_map:
            _raise_internal_server_error(detail=[{"success": False, "message": "Failed to load resolve map"}])

        resolve_id = request.resolve_id
        if not resolve_id:
            _raise_bad_request(detail=[{"success": False, "message": "Invalid resolve id"}])

        # Check if resolve exists
        resolve = get_resolve_by_id(db, resolve_id)
        if not resolve:
            _raise_bad_request(detail=[{"success": False, "message": "Nova Recommendations not found"}])
        
        customer = None
        if current_user is not None:    #allows customer to create a new resolve session with login
            customer = get_customer_by_user_id(db, int(current_user.id))

        if resolve.status == ResolveStatusEnum.COMPLETED:
            if current_user and customer is None:
                _raise_bad_request(detail=[{"success": False, "message": "Invalid user, Login required to answer questions"}])
            if customer.id != resolve.customer_id:
                _raise_bad_request(detail=[{"success": False, "message": "Invalid user, please login again."}])
            case = get_case_by_customer_id(db, customer.id)
            if case and case.is_kyc_completed:
                _raise_bad_request(detail=[{"success": False, "message": "Resolve is already linked to a case"}])

        result, errors = validate_save_answer(db, resolve, request, questions, resolve_map)
        if errors:
            errors_str = ", ".join(error for error in errors if error)
            _raise_validation_error(detail=errors_str)

        # #new logic update #911
        # try:
        #     circumstance = get_resolve_circumstance(resolve)
        #     check_identifier = "20" if circumstance and "finance" in circumstance else "18"
        #     request_identifiers = []
        #     if request.answers:
        #         for item in request.answers:
        #             question_identifier_str = str(item.question_identifier)
        #             request_identifiers.append(question_identifier_str)
        #     if resolve.customer_id:
        #         case = resolve.case_resolves[0].case
        #         if case is None:
        #             _raise_forbidden_error(detail=[{"success": False, "message": "Invalid user. Please login again."}]
        #             )
        #         if case.is_kyc_completed is True:
        #             _raise_forbidden_error(detail=[{"success": False, "message": "Case is already linked to a customer with KYC completed"}]
        #             )
        #     recommendation_check = True if check_identifier in request_identifiers else False
        #     if recommendation_check:
        #         resolve_result = get_resolve_result(db, resolve, questions)
        #         resolve.result_reference_id = str(resolve_result.get("result_type", ""))
        #         resolve.result_version = str(resolve_result.get("version", ""))
        #         details = {}
        #         resolve_answers = format_resolve_question_answers(db, resolve)
        #         details["resolve_answers"] = resolve_answers
        #         details["resolve_result"] = {
        #             "title": resolve_result["title"],
        #             "summary": resolve_result["summary"],
        #             "version": resolve_result["version"],
        #         }
        #         details["recommended_approach"] = {
        #             "title": resolve_result["recommended_approach"]["title"],
        #             "summary": resolve_result["recommended_approach"]["summary"],
        #             "version": resolve_result["recommended_approach"]["version"],
        #         }
        #         ai_recommendation = await generate_ai_recommendation(details)
        #         formatted_recommendations = {
        #             item["title"]: item["description"]
        #             for item in ai_recommendation.get("personalised_analysis", [])
        #             if item.get("title") and item.get("description")
        #         }
        #         resolve.personalised_ai_recommendation = formatted_recommendations
        #         resolve.recommended_approach = str(resolve_result.get("recommended_approach",{}).get("result_type", ""))
        #         db.commit()
        #         db.refresh(resolve)

        # except Exception as e:
        #     logger.exception(f"Error in answer_question: {e}")
        #     raise

        return AnswerQuestionResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Question answered successfully")],
            data=AnswerQuestionResponseData(
                resolve_id=resolve_id
            )
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in answer_question: {e}")
        _raise_internal_server_error(detail=[{"success": False, "message": "Failed to answer question"}])


@router.post("/resolve", response_model=ResolveSubmitResponse)
async def submit_resolve(
    request: ResolveSubmitRequest,
    current_user: User | None = Depends(get_current_user_if_provided),
    db: Session = Depends(get_db),
):
    """Submit a resolve session, save/update the answers if provided. It will validate the answers and return a result data if the resolve is completed."""

    try:

        resolve = get_resolve_by_id(db, int(request.resolve_id))
        if resolve.status == ResolveStatusEnum.COMPLETED:
            if not current_user:
                _raise_forbidden_error(detail=[{"success": False, "message": "Invalid user. Please login again."}]
                )
            else:
                customer = get_customer_by_user_id(db, int(current_user.id))
                if customer is None:
                    _raise_forbidden_error(detail=[{"success": False, "message": "Invalid user. Please login again."}]
                    )
                if customer.id != resolve.customer_id:
                    _raise_forbidden_error(detail=[{"success": False, "message": "Invalid user. Please login again."}]
                    )

                event_data = Event(
                    event_type=EventType.RESOLVE_RESUBMIT,
                    payload={
                        "request_data": request,
                    },
                    user_id=None,
                    current_user=current_user if current_user else None
                )
                await event_dispatcher.dispatch_event(db, event_data)
                # Extract status messages from event responses
                response = event_data.response
                if response is None:
                    _raise_event_processing_error()

                success, messages = extract_status_messages(response) # type: ignore[arg-type]
                if not success:
                    _raise_validation_error(detail=messages)

                # Extract the data from the EventResponseData object
                event_response = response[EventType.RESOLVE_RESUBMIT.value]
                resolve_data = event_response.data

                # Get lawyers associated with the case based on resolve reference
                lawyers_data = None
                if hasattr(resolve_data, 'result') and resolve_data.result and hasattr(resolve_data.result, 'result_type'):
                    try:
                        resolve = get_resolve_by_id(db, int(decrypt_id(resolve_data.resolve_id)))
                        lawyer_ids, lawyers = get_lawyers_for_case(db, resolve, limit_flag=3)
                        lawyers_data = parse_lawyer_data(lawyers) if lawyers else []
                    except Exception as e:
                        logging.warning(f"Failed to get lawyers for case: {e}")
                        lawyers_data = []

                resolve_data.lawyers = lawyers_data
                return ResolveSubmitResponse(
                    success=True,
                    message=messages,
                    data=resolve_data
                )

        event_data = Event(
            event_type=EventType.RESOLVE_SUBMIT,
            payload={
                "request_data": request,
            },
            user_id=None,
            current_user=current_user if current_user else None
        )

        # Dispatch event using the new system
        await event_dispatcher.dispatch_event(db, event_data)

        # Extract status messages from event responses
        response = event_data.response
        if response is None:
            _raise_event_processing_error()

        success, messages = extract_status_messages(response) # type: ignore[arg-type]
        if not success:
            _raise_validation_error(detail=messages)

        # Extract the data from the EventResponseData object
        event_response = response[EventType.RESOLVE_SUBMIT.value]
        resolve_data = event_response.data

        # Get lawyers associated with the case based on resolve reference
        lawyers_data = None
        if hasattr(resolve_data, 'result') and resolve_data.result and hasattr(resolve_data.result, 'result_type'):
            try:
                resolve = get_resolve_by_id(db, int(decrypt_id(resolve_data.resolve_id)))
                lawyer_ids, lawyers = get_lawyers_for_case(db, resolve, limit_flag=3)
                lawyers_data = parse_lawyer_data(lawyers) if lawyers else []
            except Exception as e:
                logging.warning(f"Failed to get lawyers for case: {e}")
                lawyers_data = []

        resolve_data.lawyers = lawyers_data

        # if current_user is not None:
        #     # customer = get_customer_by_user_id(db, int(current_user.id))
        #     customer = current_user.customer
        #     if customer is None:
        #         _raise_forbidden_error(detail=[{"success": False, "message": "Invalid user. Please login again."}]
        #         )
        #     customer_id = customer.id

        #     # Create customer info
        #     customer_info = CustInfo(
        #         first_name=str(current_user.first_name),
        #         last_name=str(current_user.last_name),
        #         email=str(current_user.email),
        #         phone=str(current_user.phone) if current_user.phone else None,
        #         customer_id=str(customer_id) if customer_id else None,
        #     )

        #     # Create grouped response data
        #     response_data = CustomerRegistrationResponseData(
        #         customer=customer_info,
        #         case=None,
        #         login_data=None,
        #     )

        #     response_data.login_data = None

        #     resolve_id = decrypt_id(resolve_data.resolve_id)
        #     try:
        #         resolve_id = int(resolve_id)
        #     except (ValueError, TypeError):
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid resolve ID format")

        #     resolve = get_resolve_by_id(db, resolve_id)
        #     if resolve is None:
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resolve not found")
        #     if resolve.status != ResolveStatusEnum.COMPLETED:
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resolve is not completed")
        #     if resolve.customer_id is not None and resolve.customer_id != customer_id:
        #         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resolve is already linked to a customer")
        #     else:
        #         resolve.customer_id = customer_id

        #     if resolve.case_resolves:
        #         _raise_validation_error(detail=[{"success": False, "message": "Resolve is already linked to a case"}]
        #         )
        #     # Check if any case exists with KYC completed for this customer
        #     from app.db.models import Case, CaseCustomer, Customer
        #     from sqlalchemy.orm import joinedload
        #     from app.enums.case import CaseStatusEnum
        #     existing_kyc_completed_cases = []
        #     existing_open_cases = []
        #     existing_cases = (
        #         db.query(Case)
        #         .options(
        #             joinedload(Case.case_customers).joinedload(CaseCustomer.customer).joinedload(Customer.user)
        #         )
        #         .join(Case.case_customers)
        #         .filter(
        #             Case.status == CaseStatusEnum.OPEN,
        #             CaseCustomer.customer_id == current_user.customer.id,
        #         )
        #         .all()
        #     )
        #     existing_kyc_completed_cases = [case for case in existing_cases if case.is_kyc_completed]
        #     existing_open_cases = list(set(existing_cases) - set(existing_kyc_completed_cases))
        #     if existing_kyc_completed_cases and len(existing_kyc_completed_cases) > 0:
        #         # Link resolve with customer (already done above)
        #         # Redirect to KYC completed case
        #         kyc_case = None
        #         if len(existing_kyc_completed_cases) == 1:
        #             kyc_case = existing_kyc_completed_cases[0]
        #             resolve_data.case = CaseInfo(
        #                 id=str(kyc_case.id) if kyc_case.id else None, # type: ignore[union-attr]
        #                 case_no=format_case_number(kyc_case.case_no),
        #                 type=kyc_case.case_type.value if kyc_case.case_type else None,
        #                 status=kyc_case.status.value,
        #             )
        #         # Link resolve with customer if not already linked
        #         if resolve.customer_id is None:
        #             resolve.customer_id = current_user.customer.id
        #             db.add(resolve)
        #             db.commit()

        #         message = "You have completed the Alignment Check for one of your existing cases, so you cannot create a new case. However, your new resolve has been created and linked to your existing customer account. You are now redirected to your existing Alignment Check-completed case."
        #         messages.append(ResponseMessage(success=True, message=message))
        #     else:
        #         first_name = str(current_user.first_name) if current_user.first_name is not None else ""
        #         last_name = str(current_user.last_name) if current_user.last_name is not None else ""

        #         navigator_emails = get_all_navigator_emails(db)

        #         # Create event data
        #         event_data = Event(
        #             event_type=EventType.CASE_OPEN,
        #             payload={
        #                 "customer_email": str(current_user.email),
        #                 "customer_name": first_name + " " + last_name,
        #                 "navigators": navigator_emails,
        #                 "resolve_id": resolve_id,
        #                 "customer_id": customer_id,
        #                 "response_data": response_data,
        #             },
        #             user_id=current_user.id,
        #             current_user=current_user if current_user else None
        #         )

        #         # Dispatch the event (wait for completion)
        #         await event_dispatcher.dispatch_event(db, event_data)
        #         success, case_messages = extract_status_messages(event_data.response)
        #         if not success:
        #             _raise_unprocessable_entity_error(case_messages)

        #         case_event_response = event_data.response[EventType.CASE_OPEN.value]
        #         case_info = case_event_response.data.case
        #         resolve_data.case = CaseInfo(
        #             id=decrypt_id(case_info.case_id) if case_info.case_id and isinstance(case_info.case_id, str) else None, # type: ignore[union-attr]
        #             case_no=case_info.case_no, # type: ignore[union-attr]
        #             type=case_info.case_type, # type: ignore[union-attr]
        #             status=case_info.status # type: ignore[union-attr]
        #         )
        #         messages.extend(case_messages)
                
        #         # Archive existing open cases using event
        #         if existing_open_cases:
        #             archive_event_data = Event(
        #                 event_type=EventType.ARCHIVE_CASE,
        #                 payload={
        #                     "cases": existing_open_cases,
        #                     "new_case_number": case_info.case_no if case_info.case_no else "",
        #                     "new_case_id": case_info.case_id if case_info.case_id else "",
        #                 },
        #                 user_id=current_user.id,
        #                 current_user=current_user if current_user else None,
        #             )
        #             await event_dispatcher.dispatch_event(db, archive_event_data)
        #             success, archive_messages = extract_status_messages(archive_event_data.response)
        #             if not success:
        #                 logger.error(f"Error in ARCHIVE_CASE event: {archive_messages}")
        #             messages.extend(archive_messages)
        #             # message = "Your case has been opened successfully. Existing cases have been archived."
        #             # messages.append(ResponseMessage(success=True, message=message))

        return ResolveSubmitResponse(
            success=True,
            message=messages,
            data=resolve_data
        )

    except HTTPException:
        raise
    except ValueError:
        raise
    except Exception as e:
        logger.exception(f"Resolve submission event failed: {e!s}")
        _raise_internal_server_error(detail=[{"success": False, "message": "Resolve submission event failed"}])


@router.get("/resolve/list", response_model=ResolveListResponse)
async def get_resolve_list(
    request: ResolveListRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ResolveListResponse:
    """Get resolve list with pagination and ordering."""
    try:
        role_ids = [user_role.role_id for user_role in current_user.user_roles]
        if len(role_ids) == 0:
            _raise_bad_request(detail=[{"success": False, "message": "Invalid role code"}])
        role_code = UserRoleEnum.from_id(role_ids[0]).display_name

        if role_code == UserRoleEnum.CUSTOMER.display_name:
            customer = get_customer_by_user_id(db, int(current_user.id))
            if not customer:
                _raise_bad_request(detail=[{"success": False, "message": "Customer not found"}])
            id = customer.id  # type: ignore[union-attr]
        elif role_code == UserRoleEnum.LAWYER.display_name:
            id = current_user.id
            lawyer = _get_lawyer_by_user_id(db, int(current_user.id))
            if not lawyer:
                _raise_bad_request(detail=[{"success": False, "message": "Expert not found"}])
            id = lawyer.id  # type: ignore[union-attr]
        elif role_code == UserRoleEnum.NAVIGATOR.display_name:
            id = current_user.id
        else:
            _raise_bad_request(detail=[{"success": False, "message": "Invalid role code"}])

        resolves, total_count = search_resolve_service(
            db=db,
            id=int(id),
            page=request.page,
            limit=request.limit,
            order_by=request.order_by,
            order_dir=request.order_dir,
            role_code=role_code,
            search=request.search,
            status=request.status
        )
        # Convert to response format with additional data
        items = [_process_resolve_to_list_item(resolve) for resolve in resolves]
        if total_count == 0:
            message = "No data found"
        else:
            message = "Resolve data fetched successfully"
        return ResolveListResponse(
            success=True,
            message=[ResponseMessage(success=True, message=message)],
            data=ResolveListResponseData(
                total_count=total_count, records_in_page=len(items), resolves=items
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to fetch resolve list: {e!s}")
        _raise_internal_server_error(detail=[{"success": False, "message": "Failed to fetch resolve list"}])

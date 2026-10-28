"""Customer API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.api.v1.auth import _generate_tokens_and_login_response
from app.db.database import get_db
from app.db.models.user import User
from app.db.models.resolve import Resolve
from app.db.services.auth import get_user_by_email, get_user_by_id
from app.db.services.case import get_case_by_id
from app.db.services.customer import update_customer_phone_number
from app.db.services.general import get_all_navigator_emails, get_case_customer_user, verify_case_access
from app.db.services.resolve import get_resolve_by_id_with_relationships
from app.enums.events import EventType
from app.enums.user import PasswordStateEnum
from app.enums.user_role import UserRoleEnum
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.auth import ResolveCaseInfo
from app.schemas.v1.customer import (
    CustomerInfo,
    CaseInfo,
    CustomerRegistrationRequest,
    CustomerRegistrationResponse,
    CustomerRegistrationResponseData,
    CustomerSimpleRegistrationRequest,
    CustomerSimpleRegistrationResponse,
    TalkToLawyerRequest,
    TalkToLawyerResponse,
    TalkToNavigatorRequest,
    TalkToNavigatorResponse,
)
from app.schemas.v1.event import Event
from app.utils.helpers import extract_status_messages
from app.utils.validators import validate_phone_number
from app.utils.formatters import format_case_number
from app.utils.encryption import encrypt_id, decrypt_id
logger = logging.getLogger(__name__)

# Constants
TOKEN_TYPE_BEARER = "bearer"  # nosec B105

router = APIRouter()


def _raise_event_processing_error() -> None:
    """Raise HTTPException for event processing failure."""
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail=[{"success": False, "message": "Event processing failed"}]
    )

def _raise_validation_error(detail: list[dict[str, str]]) -> None:
    """Raise HTTPException for validation errors."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _raise_not_found(detail: str) -> None:
    """Raise HTTPException for not found."""
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)

def check_customer_registration_status(
    db: Session, resolve_id: int | str | None, email: str
) -> tuple[User | None, object | None, bool, Resolve | None]:
    """
    Check customer registration status and case association. 
    Args:
        db: Database session
        resolve_id: Resolve ID
        email: Email
    Returns:
        tuple[User | None, object | None, bool, Resolve | None]:
            - User | None: User object if found
            - object | None: Case object if found
            - bool: True if customer exists
            - Resolve | None: Resolve object if found
    """
    email_user = None
    case = None
    customer_exists = False
    resolve = None
    
    # First check if user exists with customer
    email_user = get_user_by_email(db, email)
    
    if not email_user:
        return None, None, False, None
    
    if email_user and email_user.customer:
        customer_exists = True

    # If no customer exists, return early
    if email_user and not customer_exists:
        return email_user, None, False, None

    # If no resolve_id, customer exists but no case check needed
    if not resolve_id:
        return email_user, None, customer_exists, None

    # Check if case exists for this resolve and customer
    try:
        resolve_id_int = int(resolve_id)
        resolve = get_resolve_by_id_with_relationships(db, resolve_id_int)
        if not resolve:
            return email_user, None, customer_exists, None
        
        customer = email_user.customer
        
        # Check if resolve has a case 
        if resolve and resolve.case_resolves:
            case_resolve = resolve.case_resolves[0]
        
            if case_resolve and case_resolve.case:
                case_obj = case_resolve.case

                case_customer = next(
                    (cc for cc in case_obj.case_customers if cc.customer_id == customer.id),
                    None
                )

                if case_customer:
                    case = case_obj
    except (ValueError, TypeError, AttributeError) as e:
        logger.debug(f"Error checking if customer has case for resolve: {e}")
    
    return email_user, case, customer_exists, resolve


@router.post(
    "/customer/simple_registration",
    response_model=CustomerSimpleRegistrationResponse,
)
async def simple_register_customer(
    registration_data: CustomerSimpleRegistrationRequest,
    db: Session = Depends(get_db),
) -> CustomerSimpleRegistrationResponse:
    """
    Register a customer using the magic link flow.

    Creates a customer with optional resolve context and returns a magic link token.
    """
    try:
        # Check customer registration status
        email_user, case, customer_exists, resolve = check_customer_registration_status(
            db, registration_data.resolve_id, registration_data.email
        )

        response_data = None
        messages = []
        
        if customer_exists and email_user:
            # Customer exists
            customer_name = f"{email_user.first_name}".strip() if email_user.first_name else registration_data.email
            
            if case:
                # Customer exists and has case - dispatch CUSTOMER_SIMPLE_REGISTRATION_CUS_EMAIL
                event_data = Event(
                    event_type=EventType.SEND_LOGIN_LINK_EMAIL,
                    payload={
                        "case_id": case.id,
                        "user_id": int(email_user.id),
                        "customer_email": registration_data.email,
                        "customer_name": customer_name,
                    },
                    user_id=int(email_user.id),
                    current_user=email_user,
                )
                
                await event_dispatcher.dispatch_event(db, event_data)
                
                response = event_data.response
                if response is None:
                    _raise_event_processing_error()
                
                success, msg_list = extract_status_messages(response)  # type: ignore[arg-type]
                if not success:
                    _raise_validation_error(msg_list)
                
                messages = msg_list
                event_response = response[EventType.SEND_LOGIN_LINK_EMAIL.value]
                response_data = event_response.data
                
                # Transform response
                if email_user.customer:
                    customer_info = CustomerInfo(
                        first_name=str(email_user.first_name),
                        last_name=str(email_user.last_name),
                        email=str(email_user.email),
                        phone=str(email_user.phone) if email_user.phone else None,
                        customer_id=str(email_user.customer.id),
                    )
                    
                    response_data = CustomerRegistrationResponseData(
                        customer=customer_info,
                        case=CaseInfo(
                            case_id=str(case.id),
                            case_no=format_case_number(case.case_no),
                            case_type=case.case_type.value if case.case_type else None,
                            priority=case.priority.value if case.priority else None,
                            start_date=case.start_date,
                            status=case.status.value,
                            created_at=case.created_at,
                            updated_at=case.updated_at
                        ),
                        login_data=None,
                    )
            else:
                if resolve and resolve.customer_id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "success": False,
                            "message": "This resolve is already linked to a customer.",
                            "data": [{"resolve_id": encrypt_id(str(registration_data.resolve_id))}] if registration_data.resolve_id else []
                        }
                    )

                #if user exist then raise 409 error with data should have resolve id encrypted
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "success": False,
                        "message": "User with this email already exists",
                        "data": [{"resolve_id": encrypt_id(str(registration_data.resolve_id))}] if registration_data.resolve_id else []
                    }
                )

        else:
            # Customer doesn't exist - check if resolve already has a customer
            if registration_data.resolve_id:
                if resolve and resolve.case_resolves:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="This resolve is already linked to a customer."
                    )
            if email_user and not customer_exists:
                data = [{"resolve_id": encrypt_id(str(registration_data.resolve_id))}] if registration_data.resolve_id else []
                if email_user.user_roles and any(role.role_id != UserRoleEnum.CUSTOMER.id for role in email_user.user_roles):
                    data = []
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "success": False,
                        "message": "User with this email already exists.",
                        "data": data
                    }
                )
            # Customer doesn't exist - dispatch CUSTOMER_SIMPLE_REGISTRATION
            event_data = Event(
                event_type=EventType.CUSTOMER_SIMPLE_REGISTRATION,
                payload={"request_data": registration_data},
                user_id=None,
            )
            
            await event_dispatcher.dispatch_event(db, event_data)
            
            response = event_data.response
            if response is None:
                _raise_event_processing_error()
            
            success, msg_list = extract_status_messages(response)  # type: ignore[arg-type]
            if not success:
                _raise_validation_error(msg_list)
            
            messages = msg_list
            event_response = response[EventType.CUSTOMER_SIMPLE_REGISTRATION.value]
            response_data = event_response.data
            
            # Extract data from the event payload (populated by the subscriber)
            registration_payload = event_data.payload
            customer_id = registration_payload.get("customer_id")
            user_id = registration_payload.get("user_id")
            resolve_id_from_payload = registration_payload.get("resolve_id")
            customer_email = registration_payload.get("customer_email")
            customer_name = registration_payload.get("customer_name")
            first_name = registration_payload.get("first_name", ".")
            last_name = registration_payload.get("last_name", ".")
            
            # Get the user from the event (set by subscriber)
            user = event_data.current_user
            case_id = None
            case_info_from_response = None
            
            # If there's a resolve_id, trigger CASE_OPEN separately
            if resolve_id_from_payload and customer_id:
                # Get navigator emails for CASE_OPEN subscribers
                navigator_emails = get_all_navigator_emails(db)
                
                case_open_payload = {
                    "resolve_id": resolve_id_from_payload,
                    "customer_id": customer_id,
                    "response_data": response_data,
                    "customer_email": customer_email,
                    "customer_name": customer_name or f"{first_name} {last_name}".strip() or customer_email,
                    "navigators": navigator_emails,
                }
                
                case_open_event = Event(
                    event_type=EventType.CASE_OPEN,
                    payload=case_open_payload,
                    user_id=user_id,
                    current_user=user,
                )
                
                await event_dispatcher.dispatch_event(db, case_open_event)
                
                case_open_response = case_open_event.response
                if case_open_response is None:
                    _raise_event_processing_error()
                
                case_open_success, case_open_msg_list = extract_status_messages(case_open_response)  # type: ignore[arg-type]
                if not case_open_success:
                    _raise_validation_error(case_open_msg_list)
                
                # Get updated response data with case info
                case_open_event_response = case_open_response[EventType.CASE_OPEN.value]

                response_data = case_open_event_response.data
                
                # Extract case_id from the case_open payload
                case_id = case_open_event.payload.get("case_id")
                
                # Get case_info from response_data (from CASE_OPEN response)
                case_info_from_response = response_data.case if response_data else None
            
            # Trigger CUSTOMER_SIMPLE_REGISTRATION_CUS_EMAIL separately
            if user_id and customer_email:
                # cus_email_payload = {
                #     "user_id": user_id,
                #     "customer_email": customer_email,
                #     "customer_name": customer_name or f"{first_name} {last_name}".strip() or customer_email,
                # }
                
                # # Add case_id if case was created
                # if case_id:
                #     cus_email_payload["case_id"] = case_id
                
                # cus_email_event = Event(
                #     event_type=EventType.CUSTOMER_SIMPLE_REGISTRATION_CUS_EMAIL,
                #     payload=cus_email_payload,
                #     user_id=user_id,
                #     current_user=user,
                # )
                
                # await event_dispatcher.dispatch_event(db, cus_email_event)
                
                # cus_email_response = cus_email_event.response
                # if cus_email_response is None:
                #     _raise_event_processing_error()
                
                # cus_email_success, cus_email_msg_list = extract_status_messages(cus_email_response)  # type: ignore[arg-type]
                # if not cus_email_success:
                #     _raise_validation_error(cus_email_msg_list)
                
                # Refresh user from database to avoid DetachedInstanceError
                # The user object from event might be detached from the session
                if user_id:
                    user_from_db = get_user_by_id(db, user_id)
                    if user_from_db:
                        login_response_data, _, _ = _generate_tokens_and_login_response(db, user_from_db)
                        response_data.login_data = login_response_data
                        if response_data.login_data:
                            response_data.login_data.password_state = PasswordStateEnum.NOT_APPLICABLE
                        
                        # Only set redirect_path and case info if case_id exists
                        if case_id:
                            encrypted_case_id = encrypt_id(str(case_id))
                            # login_response_data.redirect_path = f"/case/{encrypted_case_id}?kycForm=true"
                            login_response_data.redirect_path = f"/case/{encrypted_case_id}"
                            
                            # Set case_info in login_response_data from CASE_OPEN response or fetch from DB
                            if case_info_from_response:
                                # Use case_info from CASE_OPEN response
                                login_response_data.case = ResolveCaseInfo(
                                    id=decrypt_id(case_info_from_response.case_id),
                                    case_no=case_info_from_response.case_no,
                                    type=case_info_from_response.case_type,
                                    status=case_info_from_response.status,
                                )
                            else:
                                # Fetch case from database if not in response
                                case_from_db = get_case_by_id(db, case_id)
                                if case_from_db:
                                    login_response_data.case = ResolveCaseInfo(
                                        id=str(case_from_db.id),
                                        case_no=format_case_number(case_from_db.case_no),
                                        type=case_from_db.case_type.value if case_from_db.case_type else None,
                                        status=case_from_db.status.value,
                                    )
                    else:
                        # If user not found, set login_data to None
                        response_data.login_data = None
                else:
                    # No user_id, set login_data to None
                    response_data.login_data = None

        return CustomerSimpleRegistrationResponse(
            success=True,
            message=messages,  # type: ignore[arg-type]
            data=response_data,
        )
    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in simple_register_customer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete simple customer registration",
        ) from e


@router.post(
    "/customer/registration",
    response_model=CustomerRegistrationResponse,
)
async def register_customer(
    registration_data: CustomerRegistrationRequest,
    db: Session = Depends(get_db),
) -> CustomerRegistrationResponse:
    """
    Register a new customer.

    This endpoint creates a new user with customer role, creates a customer record,
    and optionally updates a resolve record and creates a case.
    """
    try:

        email_user, case, customer_exists, resolve = check_customer_registration_status(
            db, registration_data.resolve_id, registration_data.email
        )
        if email_user:
            data = []
            if customer_exists:
                data = [{"resolve_id": encrypt_id(str(registration_data.resolve_id))}] if registration_data.resolve_id else []
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "User with this email already exists",
                    "data": data
                }
            )

        event_data = Event(
            event_type=EventType.CUSTOMER_REG_OPEN_CASE,
            payload={
                "request_data": registration_data,
            },
            user_id=None,
        )

        # Dispatch event using the new system
        await event_dispatcher.dispatch_event(db, event_data)

        # Extract status messages from event responses
        response = event_data.response
        if response is None:
            _raise_event_processing_error()

        success, messages = extract_status_messages(response) # type: ignore[arg-type]
        if not success:
            _raise_validation_error(messages)

        # Extract the data from the EventResponseData object
        # response is guaranteed to be not None due to the check above
        assert response is not None
        event_response = response[EventType.CUSTOMER_REG_OPEN_CASE.value]
        response_data = event_response.data
        # if response_data["case_open"] and response_data["case_open"].data:
        #     data = response_data["case_open"].data
        #     response_data = data

        # Check if CASE_OPEN was triggered and get case information from it
        if EventType.CASE_OPEN.value in response:
            case_open_response = response[EventType.CASE_OPEN.value]
            if case_open_response and case_open_response.data and case_open_response.data.case:
                case_info_from_response = case_open_response.data.case
                # Update response_data with case information from CASE_OPEN
                response_data.case = case_info_from_response
                
                # Also update login_data.case if login_data exists
                if response_data.login_data:
                    response_data.login_data.case = ResolveCaseInfo(
                        id=decrypt_id(case_info_from_response.case_id),
                        case_no=case_info_from_response.case_no,
                        type=case_info_from_response.case_type,
                        status=case_info_from_response.status,
                    )
        
        return CustomerRegistrationResponse(
            success=True,
            message=messages, # type: ignore[arg-type]
            data=response_data,
        )

    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in register_customer: {e}")
        # Handle other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register customer"
        ) from e


@router.post("/customer/talk_to_navigator",
    response_model=TalkToNavigatorResponse,
)
async def talk_to_navigator(
    request_data: TalkToNavigatorRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TalkToNavigatorResponse:
    """Talk to a navigator."""
    from app.db.services.case import is_case_archived
    try:
        if not validate_phone_number(request_data.phone):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phone number") # noqa: TRY301
        
        if is_case_archived(db, int(request_data.case_id)):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot talk to a navigator for this case."}])

        case_customer_user = None
        if current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            case_customer_user = get_case_customer_user(db, int(request_data.case_id))
            customer_user_id = int(case_customer_user.id) if case_customer_user else None
            update_customer_phone_number(db, customer_user_id, request_data.phone)
        else:
            # Update customer phone number
            update_customer_phone_number(db, current_user.customer.user_id, request_data.phone)

        event_data = Event(
            event_type=EventType.CUSTOMER_TALK_CUS_NN,
            payload={
                "request_data": request_data,
                "customer_user": case_customer_user if case_customer_user and current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id else current_user,
            },
            user_id=int(current_user.id),
            current_user=current_user,
        )

        await event_dispatcher.dispatch_event(db, event_data)

        success, messages = extract_status_messages(event_data.response) # type: ignore[arg-type]
        if not success:
            _raise_validation_error(messages)

        return TalkToNavigatorResponse(
            success=True,
            message=messages, # type: ignore[arg-type]
            data={}
        )

    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in talk_to_navigator: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to talk to navigator"
        ) from e


@router.post("/customer/talk_to_lawyer",
    response_model=TalkToLawyerResponse,
)
async def talk_to_lawyer(
    request_data: TalkToLawyerRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> TalkToLawyerResponse:
    """Talk to a lawyer."""
    from app.db.services.case import is_case_archived
    try:
        if not validate_phone_number(request_data.phone):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid phone number") # noqa: TRY301

        case_id = int(request_data.case_id)
        lawyer_id = int(request_data.lawyer_id)

        if is_case_archived(db, case_id):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=[{"success": False, "message": "This case is archived. You cannot talk to a lawyer for this case."}])
        

        verify_case_access(db, case_id, UserRoleEnum.LAWYER.display_name, lawyer_id)

        # If current user is navigator, update customer phone number as the user id get from case_customer_user
        case_customer_user = None
        if current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            case_customer_user = get_case_customer_user(db, case_id)
            customer_user_id = int(case_customer_user.id) if case_customer_user else None
            update_customer_phone_number(db, customer_user_id, request_data.phone)
        else:
            # Update customer phone number
            update_customer_phone_number(db, current_user.customer.user_id, request_data.phone)

        event_data = Event(
            event_type=EventType.CUSTOMER_TALK_CUS_LAW,
            payload={
                "request_data": request_data,
                "customer_user": case_customer_user if case_customer_user and current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id else current_user,
            },
            user_id=int(current_user.id),
            current_user=current_user,
        )

        await event_dispatcher.dispatch_event(db, event_data)

        success, messages = extract_status_messages(event_data.response) # type: ignore[arg-type]
        if not success:
            _raise_validation_error(messages)

        return TalkToLawyerResponse(
            success=True,
            message=messages, # type: ignore[arg-type]
            data={}
        )

    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in talk_to_lawyer: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to talk to expert"
        ) from e



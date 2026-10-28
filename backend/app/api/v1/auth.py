# import base64
import copy
import uuid
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, NoReturn

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from sqlalchemy.orm import Session, joinedload
# from sqlalchemy import and_, exists
from app.utils.encryption import encrypt_id
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_active_user,
    permission_required,
    permission_required_reset_password,
    verify_password,
    verify_token,
)
from app.db.models import User
from app.utils.formatters import format_case_number, mask_email
from app.db.services.auth import (
    get_user_by_email,
    get_user_by_id, 
    update_user, 
    verify_user,
    verify_payload_get_token_record, 
    generate_engage_link,
)
from app.db.services.case import get_case_by_id
from app.db.services.general import get_all_navigator_emails, verify_case_access
from app.db.services.lawyer import get_case_lawyer_by_case_id_service
from app.db.services.resolve import get_resolve_by_id, get_resolve_by_id_with_relationships
from app.db.models.case import Case
from app.db.models.case_customer import CaseCustomer
from app.db.models.case_lawyer import CaseLawyer
from app.db.models.match import Match
from app.enums.case import CaseStatusEnum
from app.db.services.refresh_token import (
    create_refresh_token as save_refresh_token,
)
from app.db.services.refresh_token import (
    delete_user_refresh_tokens,
    delete_refresh_token_by_id,
    get_refresh_token_by_id,
    update_refresh_token_by_id,
)
# from app.db.services.simple_auth_token import (
#     get_simple_auth_token_by_id,
#     get_simple_auth_token_by_token,
# )
from app.enums.events import EventType
# from app.enums.law_firm import LawFirmStatusEnum
# from app.enums.lawyer import LawyerStatusEnum
from app.enums.user import PasswordStateEnum
from app.enums.resolve import ResolveStatusEnum
from app.enums.user_role import UserRoleEnum
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.auth import (
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GetEngageLinkRequest,
    GetEngageLinkResponse,
    GetVerifyCodeRequest,
    VerifyEngageTokenRequest,
    VerifyEngageTokenResponse,
    GetVerifyCodeResponse,
    VerifyEngageTokenData,
    EngageUrlData,
    LoginResponse,
    LoginResponseData,
    LoginWithTokenRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshTokenRequest,
    ResendInitialPasswordRequest,
    ResendInitialPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SendLoginLinkRequest,
    SendLoginLinkResponse,
    SetInitialPasswordRequest,
    SetInitialPasswordResponse,
    CreatePasswordRequest,
    CreatePasswordResponse,
    TokenDetails,
    TokenResponse,
    UserData,
    UserLogin,
    ResolveCaseInfo,
    VerifyCodeData,
)
from app.schemas.v1.base import ResponseMessage
from app.schemas.v1.customer import CustomerInfo, CustomerRegistrationResponseData
from app.schemas.v1.event import Event

# from app.schemas.v1.user import UserResponse
from app.schemas.v1.user import UserUpdate
from app.utils.encryption import decrypt_id
from app.utils.dependencies import get_db
from app.utils.helpers import extract_status_messages
from app.utils.photo_utils import generate_photo_urls

logger = logging.getLogger(__name__)
# Constants
TOKEN_TYPE_BEARER = "bearer"  # nosec B105

router = APIRouter()


def _raise_auth_error(detail: list[dict[str, object]], status_code: int = status.HTTP_401_UNAUTHORIZED) -> None:
    """Raise HTTPException for authentication errors."""
    raise HTTPException(detail=detail, status_code=status_code)


def _raise_unauthorized_error(detail: list[dict[str, object]]) -> None:
    """Raise HTTPException for unauthorized access."""
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def _raise_unprocessable_entity_error(detail: list[dict[str, str]]) -> None:
    """Raise HTTPException for unprocessable entity errors."""
    raise RequestValidationError(detail)


def _raise_validation_error(detail: list[dict[str, str]]) -> NoReturn:
    """Raise HTTPException for validation errors."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)


def _generate_tokens_and_login_response(
    db: Session,
    user: User,
) -> tuple[LoginResponseData, dict[str, Any], User]:
    """
    Generate login response data, including access and refresh tokens, for a user.

    Args:
        db: Database session
        user: Authenticated user instance

    Returns:
        Tuple containing LoginResponseData, verification data dictionary, and a detached user copy.
    """
    user_copy = copy.deepcopy(user)
    verification_data = verify_user(user)

    refresh_expiry = datetime.now(timezone.utc) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )
    refresh_token_record = save_refresh_token(
        db,
        user_id=int(user_copy.id),
        token=uuid.uuid4(),
        expiry_at=refresh_expiry,
    )

    access_token = create_access_token(
        data=verification_data,
        refresh_token_id=refresh_token_record.id,  # type: ignore[arg-type]
    )
    user_id = int(user_copy.id)
    refresh_token = create_refresh_token(
        data={"sub": str(user_id)},
        refresh_token_id=refresh_token_record.id,  # type: ignore[arg-type]
    )
    refresh_token_record.refresh_token = refresh_token  # type: ignore[assignment]
    db.commit()

    photo_urls = None
    if verification_data.get("lawyer"):
        lawyer_id = verification_data.get("lawyer", {}).get("id")
        photo_urls = generate_photo_urls(
            verification_data.get("lawyer", {}).get("photo_url")
        )
    else:
        lawyer_id = None

    if verification_data.get("customer"):
        customer_id = verification_data.get("customer", {}).get("id")
    else:
        customer_id = None

    user_data = UserData(
        first_name=str(user_copy.first_name),
        last_name=str(user_copy.last_name),
        email=str(user_copy.email),
        phone=str(user_copy.phone) if user_copy.phone else None,
        gender=user_copy.gender.value if user_copy.gender else None,
        user_id=str(user_copy.id),
        role_code=verification_data.get("role"),
        available_roles=verification_data.get("available_roles"),
        lawyer_id=lawyer_id,
        customer_id=customer_id,
        photo_urls=photo_urls if photo_urls else None,
        gender_other=user_copy.gender_other if user_copy.gender_other else None,
    )

    login_response_data = LoginResponseData(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type=TOKEN_TYPE_BEARER,
        password_state=PasswordStateEnum.CAN_UPDATE if user_copy.password else PasswordStateEnum.CAN_CREATE,
        user_data=user_data,
    )
    return login_response_data, verification_data, user_copy

def get_redirect_path(db: Session, user_email: str, user: User | None = None) -> tuple[Case | None, str | None]:
    """
    Get redirect path and case for user login.
    
    Returns a tuple of (case, redirect_path) where:
    - If there is exactly one non-archived case, returns that case and its redirect path
    - If there is exactly one open case, returns that case and its redirect path
    - Else if there is exactly one closed case and no open cases, returns that case and its redirect path
    - Else returns (None, None)
    
    The existing redirect path logic is preserved for backward compatibility.
    """
    # Get user if not provided
    if user is None:
        user = get_user_by_email(db, user_email)
        if user is None:
            return None, None
        
    role_code = None
    if user.user_roles:
        role_code = UserRoleEnum.from_id(user.user_roles[0].role_id).display_name
    else:
        return None, None
    
    if role_code == UserRoleEnum.CUSTOMER.display_name:
        customer_id = user.customer.id
    elif role_code == UserRoleEnum.LAWYER.display_name:
        lawyer_id = user.lawyer.id
    else:
        return None, None
    
    cases = []
    # Check if user has a customer
    
    if role_code == UserRoleEnum.CUSTOMER.display_name:
        if user.customer is None:
            return None, None
        customer_id = user.customer.id
        # Query all cases for this customer (excluding archived)
        cases = (
            db.query(Case)
            .join(CaseCustomer)
            .filter(
                CaseCustomer.customer_id == customer_id,
                Case.status != CaseStatusEnum.ARCHIVED
            )
            .all()
        )
    elif role_code == UserRoleEnum.LAWYER.display_name:
        if user.lawyer is None:
            return None, None
        lawyer_id = user.lawyer.id
        # Query all cases for this lawyer (excluding archived)
        cases = (
            db.query(Case)
            .join(CaseLawyer)
            .filter(
                CaseLawyer.lawyer_id == lawyer_id,
                Case.status != CaseStatusEnum.ARCHIVED
            )
            .all()
        )
        if not cases or len(cases) == 0:
            cases = (
                db.query(Case)
                .join(Match)
                .filter(
                    Match.case_id == Case.id,
                    Match.lawyer_id == lawyer_id,
                    Case.status != CaseStatusEnum.ARCHIVED,
                    Case.is_match_confirmed == True,
                    Case.is_lawyer_assigned == False
                )
                .all()
            )            
    else:
        return None, None
    
    if len(cases) == 1:
        case = cases[0]
        redirect_path = f"/case/{encrypt_id(str(case.id))}"
        # if not case.is_kyc_completed:
        #     redirect_path += "?kycForm=true"
        return case, redirect_path
    else:
        # Separate open and closed cases
        open_cases = [case for case in cases if case.status == CaseStatusEnum.OPEN]
        closed_cases = [case for case in cases if case.status == CaseStatusEnum.CLOSED]
        
        # Priority 1: If there is exactly one open case, return it
        if len(open_cases) == 1:
            case = open_cases[0]
            redirect_path = f"/case/{encrypt_id(str(case.id))}"
            # if not case.is_kyc_completed:
            #     redirect_path += "?kycForm=true"
            return case, redirect_path
        
        # Priority 2: If there is exactly one closed case and no open cases, return it
        if len(closed_cases) == 1 and len(open_cases) == 0:
            case = closed_cases[0]
            redirect_path = f"/case/{encrypt_id(str(case.id))}"
            return case, redirect_path

    # No single case found
    return None, None


def token_record_service(db: Session, request: (GetVerifyCodeRequest | VerifyEngageTokenRequest)) -> tuple[str | None, Case | None, User | None, str | None]:
    """
    Verify engage token and get token record.
    """

    detail = [{"success": False, "message": "Invalid or expired token"}]
    token_payload = verify_token(request.token, check_expiration=False)
    if not token_payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

    user_id_encrypted = token_payload.get("sub") if token_payload.get("sub") else None
    if not user_id_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    user_id = int(decrypt_id(user_id_encrypted))
    if not user_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    case_id_encrypted = token_payload.get("case_id") if token_payload.get("case_id") else None
    if not case_id_encrypted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    case_id = int(decrypt_id(case_id_encrypted))
    if not case_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    token_expiry_minutes = settings.SIMPLE_AUTH_TOKEN_EXPIRE_MINUTES
    token_record = verify_payload_get_token_record(db, request.token, token_payload, token_type="engage_token", encrypted_payload=True, error_detail=detail, token_expiry_minutes=token_expiry_minutes)
    user_role_code = None
    if token_record.user.user_roles:
        user_role_code = UserRoleEnum.from_id(token_record.user.user_roles[0].role_id).display_name
    else:
        logger.error("token_record.user.user_roles is None")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    if user_role_code != UserRoleEnum.CUSTOMER.display_name:
        logger.error("User role code is not customer")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    
    user = token_record.user
    if user.id != user_id:
        logger.error("User ID does not match")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    case = get_case_lawyer_by_case_id_service(db, case_id)
    if not case:
        logger.error("Case not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    
    if case.is_lawyer_assigned is False:
        logger.error("Case is not assigned to a lawyer")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    
    if case.is_initial_payment_completed is False:
        logger.error("Case initial payment is not completed")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

    lawyer = case.case_lawyers[0].lawyer
    law_firm = lawyer.lawyer_law_firms[0].law_firm
    if not law_firm:
        logger.error("Law firm not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    engage_form_url = law_firm.engage_form_url

    if not engage_form_url:
        logger.error("Engage form URL is not found")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
    return case_id_encrypted, case, user, engage_form_url


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: UserLogin = Depends(UserLogin.as_form),
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Login user and return tokens with user data."""

    try:

        resolve = None
        if login_data.resolve_id:
            resolve_id = decrypt_id(login_data.resolve_id)
            try:
                resolve_id = int(resolve_id)
            except (ValueError, TypeError):
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid resolve ID format")

            resolve = get_resolve_by_id(db, resolve_id)
            if resolve is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resolve not found")
            if resolve.status != ResolveStatusEnum.COMPLETED:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resolve is not completed")

        # Get user by email
        user = get_user_by_email(db, login_data.username)

        if user is None:
            detail = [{"success": False, "message": "Incorrect email or password"}]
            _raise_auth_error(detail)
        if resolve is not None:
            if len(user.user_roles) == 0 or user.user_roles[0].role_id != UserRoleEnum.CUSTOMER.id:
                detail = [{"success": False, "message": "Login with resolve ID is only allowed for customers"}]
                _raise_auth_error(detail)

        if user.password is None:
            detail = [{"success": False, "message": "Incorrect email or password"}]
            _raise_auth_error(detail)

        # At this point, user is guaranteed to be not None
        assert user is not None

        # Verify password
        if not verify_password(login_data.password, str(user.password)):
            detail = [{"success": False, "message": "Incorrect email or password"}]
            _raise_auth_error(detail)

        login_response_data, data, user_copy = _generate_tokens_and_login_response(db, user)
        user_data = login_response_data.user_data
        customer_id = data.get("customer", {}).get("id") if data.get("customer") else None

        if login_data.resolve_id and customer_id is None:
            _raise_validation_error(detail=[{"success": False, "message": "Please login again with proper resolve id."}])

        # Create customer info
        customer_info = CustomerInfo(
            first_name=str(user_copy.first_name),
            last_name=str(user_copy.last_name),
            email=str(user_copy.email),
            phone=str(user_copy.phone) if user_copy.phone else None,
            customer_id=str(user_data.customer_id),
            gender_other=user_copy.gender_other if user_copy.gender_other else None,
        )
        case, redirect_path = get_redirect_path(db, user_copy.email, user)
        if redirect_path is not None:
            login_response_data.redirect_path = redirect_path

        # Create grouped response data
        response_data = CustomerRegistrationResponseData(
            customer=customer_info,
            case=None,
            login_data=None,
        )

        response_data.login_data = login_response_data

        messages = []
        if resolve:
            resolve_id = resolve.id

            if resolve.customer_id is not None and resolve.customer_id != customer_id:
                _raise_validation_error(detail=[{"success": False, "message": "Resolve is already linked to a customer"}]
                )
            else:
                resolve.customer_id = customer_id

            if resolve.case_resolves:
                _raise_validation_error(detail=[{"success": False, "message": "Resolve is already linked to a case"}]
                )

            first_name = str(user_copy.first_name) if user_copy.first_name is not None else ""
            last_name = str(user_copy.last_name) if user_copy.last_name is not None else ""

            navigator_emails = get_all_navigator_emails(db)

            # Create event data
            event_data = Event(
                event_type=EventType.CASE_OPEN,
                payload={
                    "customer_email": str(user_copy.email),
                    "customer_name": first_name + " " + last_name,
                    "navigators": navigator_emails,
                    "resolve_id": resolve_id,
                    "customer_id": customer_id,
                    "response_data": response_data,
                },
                user_id=user_copy.id,
            )

            # Dispatch the event (wait for completion)
            await event_dispatcher.dispatch_event(db, event_data)

            success, messages = extract_status_messages(event_data.response)
            if not success:
                _raise_unprocessable_entity_error(messages)
            response = event_data.response[EventType.CASE_OPEN.value]
            case_info = response.data.case
            login_response_data.case = ResolveCaseInfo(
                id=decrypt_id(case_info.case_id) if case_info.case_id and isinstance(case_info.case_id, str) else None, # type: ignore[union-attr]
                case_no=case_info.case_no,
                type=case_info.case_type,
                status=case_info.status,
            )
        else:
            # Set case information in login response if case is found and no resolve case was set
            if case is not None:
                login_response_data.case = ResolveCaseInfo(
                    id=encrypt_id(str(case.id)),
                    case_no=format_case_number(case.case_no),
                    type=case.case_type.value if case.case_type else None,
                    status=case.status.value,
                )

        login_message = {"success": True, "message": "Login successful"}
        messages.insert(0, login_message)
        # Create login response
        login_response = LoginResponse(
            success=True,
            message=messages,
            data=login_response_data,
        )
        return login_response

    except HTTPException:
        # re-raise HTTPExceptions
        raise
    except RequestValidationError:
        raise
    except Exception as e:
        logger.exception(f"Error in login: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to login") from None


@router.post("/login-with-token", response_model=LoginResponse)
async def login_with_token(
    request: LoginWithTokenRequest,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Login user using a magic link or one-time token."""
    try:
        detail = [{"success": False, "message": "Invalid or expired token"}]
        token_payload = verify_token(request.token, check_expiration=False)
        if not token_payload:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)
        
        email = token_payload.get("email")
        case_id = token_payload.get("case_id")
        resolve_id = token_payload.get("resolve_id")
        user_id = int(token_payload.get("sub")) if token_payload.get("sub") else None
        
        data = {
            "email": mask_email(email),
            "case_id": encrypt_id(str(case_id)) if case_id else None,
            "resolve_id": encrypt_id(str(resolve_id)) if resolve_id else None,
            "user_id": encrypt_id(str(user_id)) if user_id else None,
        }
        detail[0]["data"] = data
   
        token_record = verify_payload_get_token_record(db, request.token, token_payload, error_detail=detail)

        user_role_code = None
        if token_record.user.user_roles:
            user_role_code = UserRoleEnum.from_id(token_record.user.user_roles[0].role_id).display_name
        else:
            logger.error("token_record.user.user_roles is None")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        
        # start of resolve id logic
        if resolve_id is not None:
            if user_role_code is not None and user_role_code != UserRoleEnum.CUSTOMER.display_name:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
            resolve = get_resolve_by_id_with_relationships(db, resolve_id)
            if resolve is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
            if resolve.customer_id is not None and resolve.customer_id != token_record.user.customer.id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
            
            from app.db.models.case import Case
            from app.db.models.case_customer import CaseCustomer
            from app.db.models.customer import Customer
            from app.enums.case import CaseStatusEnum
            
            # Check if case exists with this resolve_id
            case_with_resolve = None
            if resolve.case_resolves:
                case_resolve = resolve.case_resolves[0]
                if case_resolve and case_resolve.case:
                    case_with_resolve = case_resolve.case
            
            if case_with_resolve is not None:
                # Case exists with resolve_id
                login_response_data, data, user_copy = _generate_tokens_and_login_response(db, token_record.user)
                redirect_path = None
                if case_with_resolve.status != CaseStatusEnum.ARCHIVED:
                    # Complete login without redirect URL
                    redirect_path = f"/case/{encrypt_id(str(case_with_resolve.id))}"
                    # if not case_with_resolve.is_kyc_completed:
                    #     redirect_path += "?kycForm=true"
                login_response_data.redirect_path = redirect_path
                return LoginResponse(
                    success=True,
                    message=[ResponseMessage(success=True, message="Login successful")],
                    data=login_response_data,
                )                    
            else:
                # No case exists with resolve_id
                # Check if any case exists with KYC completed for this customer
                existing_kyc_completed_cases = []
                existing_open_cases = []
                existing_cases = (
                    db.query(Case)
                    .options(
                        joinedload(Case.case_customers).joinedload(CaseCustomer.customer).joinedload(Customer.user)
                    )
                    .join(Case.case_customers)
                    .filter(
                        Case.status == CaseStatusEnum.OPEN,
                        CaseCustomer.customer_id == token_record.user.customer.id,
                    )
                    .all()
                )
                existing_kyc_completed_cases = [case for case in existing_cases if case.is_kyc_completed]
                existing_open_cases = list(set(existing_cases) - set(existing_kyc_completed_cases))
                
                # resolve.customer_id = token_record.user.customer.id
                # db.commit()
                if existing_kyc_completed_cases and len(existing_kyc_completed_cases) > 0:
                    # Link resolve with customer (already done above)
                    # Redirect to KYC completed case
                    redirect_path = None
                    kyc_case = None
                    resolve_case_info = None
                    if len(existing_kyc_completed_cases) == 1:
                        kyc_case = existing_kyc_completed_cases[0]
                        redirect_path = f"/case/{encrypt_id(str(kyc_case.id))}"
                        resolve_case_info = ResolveCaseInfo(
                                                id=str(kyc_case.id),
                                                case_no=format_case_number(kyc_case.case_no),
                                                type=kyc_case.case_type.value if kyc_case.case_type else None,
                                                status=kyc_case.status.value,
                                            )                        
                    resolve.customer_id = token_record.user.customer.id
                    db.add(resolve)
                    db.commit()
                    login_response_data, data, user_copy = _generate_tokens_and_login_response(db, token_record.user)
                    login_response_data.case = resolve_case_info
                    login_response_data.redirect_path = redirect_path
                    message = "You have completed the Alignment check for one of your existing cases, so you cannot create a new case. However, your new resolve has been created and linked to your existing customer account. You are now redirected to your existing Alignment Check-completed case."
                    return LoginResponse(
                        success=True,
                        message=[ResponseMessage(success=True, message=message)],
                        data=login_response_data,
                    )
                else:
                    # Link resolve with customer (already done above)
                    # Create new case
                    navigator_emails = get_all_navigator_emails(db)
                    
                    # Create customer info for response_data
                    customer_info = CustomerInfo(
                        first_name=str(token_record.user.first_name),
                        last_name=str(token_record.user.last_name),
                        email=str(token_record.user.email),
                        phone=str(token_record.user.phone) if token_record.user.phone else None,
                        customer_id=str(token_record.user.customer.id),
                    )
                    
                    # Create response_data for CASE_OPEN event
                    response_data = CustomerRegistrationResponseData(
                        customer=customer_info,
                        case=None,
                        login_data=None,
                    )
                    
                    event_data = Event(
                        event_type=EventType.CASE_OPEN,
                        payload={
                            "customer_email": str(token_record.user.email),
                            "customer_name": str(token_record.user.first_name) + " " + str(token_record.user.last_name),
                            "navigators": navigator_emails,
                            "resolve_id": resolve_id,
                            "customer_id": token_record.user.customer.id,
                            "response_data": response_data,
                        },
                        user_id=token_record.user.id,
                        current_user=token_record.user,
                    )
                    await event_dispatcher.dispatch_event(db, event_data)
                    success, messages = extract_status_messages(event_data.response)
                    if not success:
                        _raise_unprocessable_entity_error(messages)
                    response = event_data.response[EventType.CASE_OPEN.value]                    
                    case_info = response.data.case

                    resolve.customer_id = token_record.user.customer.id
                    db.add(resolve)
                    db.commit()
                    
                    # Archive existing open cases using event
                    if existing_open_cases:
                        archive_event_data = Event(
                            event_type=EventType.ARCHIVE_CASE,
                            payload={
                                "cases": existing_open_cases,
                                "new_case_number": case_info.case_no if case_info.case_no else "",
                                "new_case_id": case_info.case_id if case_info.case_id else "",
                            },
                            user_id=token_record.user.id,
                            current_user=token_record.user,
                        )
                        await event_dispatcher.dispatch_event(db, archive_event_data)
                        success, messages = extract_status_messages(archive_event_data.response)
                        if not success:
                            logger.error(f"Error in ARCHIVE_CASE event: {messages}")                
                    login_response_data, data, user_copy = _generate_tokens_and_login_response(db, token_record.user)
                    # login_response_data.redirect_path = f"/case/{encrypt_id(str(case_info.case_id))}?kycForm=true"
                    login_response_data.case = ResolveCaseInfo(
                        id=decrypt_id(case_info.case_id) if case_info.case_id and isinstance(case_info.case_id, str) else None,  # type: ignore[union-attr]
                        case_no=case_info.case_no,  # type: ignore[union-attr]
                        type=case_info.case_type,  # type: ignore[union-attr]
                        status=case_info.status,  # type: ignore[union-attr]
                    )
                    # login_response_data.redirect_path = f"/case/{case_info.case_id}?kycForm=true"
                    login_response_data.redirect_path = f"/case/{case_info.case_id}"
                    message = "Your case has been opened successfully. Existing cases have been archived."
                    return LoginResponse(
                        success=True,
                        message=[ResponseMessage(success=True, message=message)],
                        data=login_response_data,
                    )
        # end of resolve id logic
        
        if case_id is not None and user_role_code is not None:
            if user_role_code == UserRoleEnum.CUSTOMER.display_name:
                user_id = token_record.user.customer.id
            elif user_role_code == UserRoleEnum.LAWYER.display_name:
                user_id = token_record.user.lawyer.id
            else:
                user_id = token_record.user.id
            verify_case_access(db, case_id, user_role_code, user_id)

        token_type = token_payload.get("type")
        allowed_token_types = {"simple_registration"}
        if token_type not in allowed_token_types:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

        user_id = token_payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)

        try:
            user_id_int = int(str(user_id))
        except (TypeError, ValueError) as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

        if not token_record.user:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        if token_record.user.id != user_id_int:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        login_response_data, _, _ = _generate_tokens_and_login_response (db, token_record.user)
        case, redirect_path = get_redirect_path(db, token_record.user.email, token_record.user)
        if redirect_path is not None:
            login_response_data.redirect_path = redirect_path
        if case is not None:
            login_response_data.case = ResolveCaseInfo(
                id=str(case.id),
                case_no= format_case_number(case.case_no),
                type=case.case_type,
                status=case.status,
            )
        
        encrypted_case_id: str | None = None
        if case_id is not None:
            case_info = get_case_by_id(db, case_id)
            if case_info:
                login_response_data.case = ResolveCaseInfo(
                    id=str(case_id),
                    case_no= format_case_number(case_info.case_no),
                    type=case_info.case_type,
                    status=case_info.status,
                )
            encrypted_case_id = encrypt_id(str(case_id))
            redirect_path = f"/case/{encrypted_case_id}"
            # if not case_info.is_kyc_completed:
            #     redirect_path += "?kycForm=true"
            login_response_data.redirect_path = redirect_path
        return LoginResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Login successful")],
            data=login_response_data,
        )

    except HTTPException as e1:
        logger.exception(f"HTTPException in login_with_token: {e1}")
        raise
    except Exception as e:
        logger.exception(f"Error in login_with_token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to login with token",
        ) from None

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest, db: Session = Depends(get_db)
) -> TokenResponse:
    """Refresh access token using refresh token."""
    try:
        error_detail = [{"success": False, "message": "Invalid refresh token"}]
        # Verify refresh token
        payload = verify_token(refresh_data.refresh_token)
        if not payload or payload.get("type") != "refresh":
            _raise_unauthorized_error(error_detail)

        # At this point, payload is guaranteed to be not None
        assert payload is not None

        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            _raise_unauthorized_error(error_detail)

        expire = payload.get("exp")
        if expire is None or expire < int(datetime.now(timezone.utc).timestamp()):
            error_detail[0]["message"] = "Refresh token expired, please login again."
            _raise_unauthorized_error(error_detail)

        try:
            user_id_int = int(str(user_id))
        except (ValueError, TypeError):
            error_detail[0]["message"] = "Invalid refresh token."
            _raise_unauthorized_error(error_detail)

        # Get user from database
        user = db.query(User).filter(User.id == user_id_int).first()
        if not user:
            error_detail[0]["message"] = "Invalid refresh token."
            _raise_unauthorized_error(error_detail)

        # At this point, user is guaranteed to be not None
        assert user is not None

        # Extract refresh_token_id from JWT payload for efficient lookup
        refresh_token_id = payload.get("refresh_token_id")
        if not refresh_token_id:
            error_detail[0]["message"] = "Invalid refresh token format."
            _raise_unauthorized_error(error_detail)

        # Fetch refresh token record by ID (efficient primary key lookup)
        refresh_token_record = get_refresh_token_by_id(db, refresh_token_id)
        if not refresh_token_record:
            error_detail[0]["message"] = "Refresh token not found."
            _raise_unauthorized_error(error_detail)

        # Verify the token strings match for security confirmation
        if refresh_token_record.refresh_token != refresh_data.refresh_token:
            error_detail[0]["message"] = "Refresh token mismatch."
            _raise_unauthorized_error(error_detail)

        # Verify the token belongs to the current user
        if refresh_token_record.user_id != user_id_int:
            error_detail[0]["message"] = "Unauthorized refresh token."
            _raise_unauthorized_error(error_detail)

        data = verify_user(user)

        # Calculate new refresh token expiry
        refresh_expiry = datetime.now(timezone.utc) + timedelta(
            minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
        )

        # Create new tokens with the same refresh_token_id
        access_token = create_access_token(data=data, refresh_token_id=refresh_token_record.id)  # type: ignore[arg-type, union-attr]
        refresh_token = create_refresh_token(data={"sub": str(user.id)}, refresh_token_id=refresh_token_record.id)  # type: ignore[arg-type, union-attr]

        # Update refresh token in database using ID (supports token rotation)
        update_refresh_token_by_id(db, refresh_token_id=refresh_token_record.id, new_token=refresh_token, expiry_at=refresh_expiry)  # type: ignore[union-attr]

        return TokenResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Refresh token successful")],
            data=TokenDetails(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="refresh",
            ),
        )
    except HTTPException:
        # re-raise HTTPExceptions
        raise

    except Exception as e:
        logger.exception(f"Error in refresh_token: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to refresh token") from None


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(
    request: ForgotPasswordRequest, db: Session = Depends(get_db)
) -> ForgotPasswordResponse:
    """
    Send password reset email.
    
    For security, always returns a success message regardless of whether the email exists.
    This prevents email enumeration attacks.
    """
    try:
        # Create event using the new EventCreate schema
        event_data = Event(
            event_type=EventType.PASSWORD_RESET_REQUESTED,
            payload={
                "forgot_password_request": request,
            },
            user_id=None,
        )

        # Dispatch event using the new system
        await event_dispatcher.dispatch_event(db, event_data)

        # Extract status messages
        success, messages = extract_status_messages(event_data.response)
        if not success:
            # Log the error but return generic success for security
            logger.error(f"Password reset event failed for email: {request.email}. Error: {messages}")
            return ForgotPasswordResponse(
                success=True,
                message=[ResponseMessage(success=True, message="If an account with this email exists, a password reset link has been sent.")],
                data=[],
            )

        # Return generic success message (security: don't reveal if email exists)
        return ForgotPasswordResponse(
            success=True,
            message=[ResponseMessage(success=True, message="If an account with this email exists, a password reset link has been sent.")],
            data=[],
        )
    except ValueError as ve:
        # Log ValueError but return generic success for security
        logger.exception(f"ValueError in forgot_password for email: {request.email}: {ve}")
        return ForgotPasswordResponse(
            success=True,
            message=[ResponseMessage(success=True, message="If an account with this email exists, a password reset link has been sent.")],
            data=[],
        )
    except HTTPException:
        # re-raise HTTPExceptions
        raise

    except RequestValidationError:
        raise

    except Exception as e:
        # Log error but return generic success for security
        logger.exception(f"Error in forgot_password for email: {request.email}: {e}")
        return ForgotPasswordResponse(
            success=True,
            message=[ResponseMessage(success=True, message="If an account with this email exists, a password reset link has been sent.")],
            data=[],
        )


@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(permission_required_reset_password),
) -> ResetPasswordResponse:
    """Reset password using token. Only accepts password_reset tokens from forgot-password flow."""
    try:
        update_user(
            db,
            user_id=int(current_user.id),
            user_update=UserUpdate(
                password=request.new_password,
                reset_token_timestamp=None
            ),
        )

        # Invalidate all refresh tokens for security after password reset
        delete_user_refresh_tokens(db, int(current_user.id))

        return ResetPasswordResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Password has been successfully reset")],
            data=[],
        )
    except HTTPException:
        # re-raise HTTPExceptions
        raise

    except Exception as e:
        logger.exception(f"Error in reset_password: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset password") from None

from fastapi import Header

from app.core.security import get_current_user


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    logout_data: LogoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LogoutResponse:
    """
    Logout user by invalidating refresh token(s).
    Uses refresh_token_id from JWT for efficient lookup and verification.

    Args:
        logout_data: Logout request containing refresh_token and logout_all_devices flag
        db: Database session
        current_user: Current authenticated user

    Returns:
        LogoutResponse: Success response
    """
    try:
        # Verify and decode the refresh token to get the refresh_token_id
        payload = verify_token(logout_data.refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise HTTPException(  # noqa: TRY301
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Invalid refresh token"}]
            )

        # Extract refresh_token_id from the JWT payload
        refresh_token_id = payload.get("refresh_token_id")

        if not refresh_token_id:
            raise HTTPException(  # noqa: TRY301
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Invalid refresh token format"}]
            )

        # Fetch the refresh token record by ID (efficient primary key lookup)
        refresh_token_record = get_refresh_token_by_id(db, refresh_token_id)

        if not refresh_token_record:
            raise HTTPException(  # noqa: TRY301
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Refresh token not found"}]
            )

        # Verify the token strings match for confirmation
        if refresh_token_record.refresh_token != logout_data.refresh_token:
            raise HTTPException(  # noqa: TRY301
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Refresh token mismatch"}]
            )

        # Verify the token belongs to the current user
        if refresh_token_record.user_id != int(current_user.id):
            raise HTTPException(  # noqa: TRY301
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Unauthorized refresh token"}]
            )

        if logout_data.logout_all_devices:
            # Logout from all devices
            deleted_count = delete_user_refresh_tokens(db, int(current_user.id))
            message = f"Logged out from all devices ({deleted_count} sessions)"
        else:
            # Logout from current device only using ID (efficient delete)
            delete_refresh_token_by_id(db, refresh_token_id)
            message = "Logged out successfully"

        return LogoutResponse(
            success=True,
            message=[ResponseMessage(success=True, message=message)],
            data=[],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in logout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to logout"
        ) from None


@router.post("/verify-token")
async def verify_token_for_websocket(
    token: str,
    db: Session = Depends(get_db),
    x_api_key: str = Header(None, alias="X-API-KEY"),
) -> dict[str, Any]:
    """
    Verify JWT token and return user information with role for WebSocket authentication.
    Also requires a valid API key in the X-API-KEY header.

    Args:
        token: JWT access token
        db: Database session
        x_api_key: API key from request header

    Returns:
        Dict containing user information and role

    Raises:
        HTTPException: If token is invalid, user not found, or API key is invalid
    """
    try:
        # API Key validation
        expected_api_key = getattr(settings, "WEBSOCKET_API_KEY", None)
        if not expected_api_key or not x_api_key or x_api_key != expected_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "message": "Invalid or missing API key"},
            )

        # Verify the token
        payload = verify_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "message": "Invalid token"}
            )

        expire = payload.get("exp")
        if expire is None or expire < int(datetime.now(timezone.utc).timestamp()):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Link expired, please request a new one.",
                },
            )
        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "message": "Invalid token payload"}
            )

        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "message": "Invalid user ID in token"}
            )

        # Get user from database with roles
        user = db.query(User).options(joinedload(User.user_roles)).filter(User.id == user_id_int).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "message": "User not found"}
            )

        # Get user roles
        role_ids = [user_role.role_id for user_role in user.user_roles]
        role_codes = [UserRoleEnum.from_id(role_id).display_name for role_id in role_ids]
        if len(role_codes) == 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"success": False, "message": "User has no role assigned. Please contact support."}
            )
        # Return primary role (first role) for WebSocket connection
        primary_role = role_codes[0]
        def encrypt_id(id_value: str) -> str | None:
            try:
                from cryptography.hazmat.primitives import padding
                from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
                from cryptography.hazmat.backends import default_backend
                import hashlib
                backend = default_backend()
                secret_key = settings.WEBSOCKET_TOKEN_ENCRYPTION_KEY or datetime.now(timezone.utc).strftime("%Y%m%d%H")
                def get_key(secret_key: str | None = None):
                    """
                    Derive a deterministic IV (Initialization Vector) from the salt for use in AES modes that require an IV.
                    This uses the salt (or a default from settings) and the secret key to derive a 16-byte IV using SHA-256.
                    """
                    try:
                        if secret_key and isinstance(secret_key, str):
                            source = (secret_key).encode("utf-8")
                        else:
                            source = (secret_key.decode("utf-8")).encode("utf-8")
                        key = hashlib.sha256(source).digest()
                        iv = hashlib.sha256(source).digest()[:16]

                        return key, iv
                    except Exception as e:
                        logger.exception(f"Error getting key: {e}")
                        return None, None

                def pad_value(value, block_size):
                    try:
                        padder = padding.PKCS7(block_size * 8).padder()
                        padded_data = padder.update(value) + padder.finalize()
                        return padded_data
                    except Exception as e:
                        logger.exception(f"Error padding value: {e}")
                        return None

                key, iv = get_key(secret_key)

                block_size = algorithms.AES.block_size // 8  # AES block size in bytes
                padded_value = pad_value(str(id_value).encode('utf-8'), block_size)

                cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=backend)
                encryptor = cipher.encryptor()
                encrypted_data = encryptor.update(padded_value) + encryptor.finalize()

                # return base64.urlsafe_b64encode(encrypted_data).decode('utf-8')
                return encrypted_data.hex()
            except Exception as e:
                logger.exception(f"Error encrypting id: {e}")
                return None
        return {
            "success": True,
            "message": "Token verified successfully",
            "data": {
                "user_id": encrypt_id(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role_code": primary_role,
                "all_roles": role_codes
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error verify_token_for_websocket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Internal server error"}
        )


@router.post("/set-initial-password", response_model=SetInitialPasswordResponse)
async def set_initial_password(
    request: SetInitialPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(permission_required),
) -> SetInitialPasswordResponse:
    """Set initial password using token for newly created lawyers and navigators."""
    try:
        if current_user.password is not None:
            raise HTTPException(  # noqa: TRY301
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Password already set"}
            )
        # Update user password (uses same logic as reset password)
        update_user(
            db,
            user_id=int(current_user.id),
            user_update=UserUpdate(
                first_name=None,
                last_name=None,
                email=None,
                phone=None,
                gender=None,
                status=None,
                password=request.new_password,
                refresh_token=None,
                reset_token_timestamp=None
            ),
        )

        return SetInitialPasswordResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Password has been successfully set")],
            data=[],
        )
    except HTTPException:
        # re-raise HTTPExceptions
        raise

    except Exception as e:
        logger.exception(f"Error in set_initial_password: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to set initial password") from None


@router.post("/create-password", response_model=CreatePasswordResponse)
async def create_password(
    request: CreatePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> CreatePasswordResponse:
    """Create password for newly created customer, lawyer or navigator."""
    try:
        if current_user.password is not None:
            raise HTTPException(  # noqa: TRY301
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "Password already set"}
            )
        # Update user password (uses same logic as reset password)
        update_user(
            db,
            user_id=int(current_user.id),
            user_update=UserUpdate(
                first_name=None,
                last_name=None,
                email=None,
                phone=None,
                gender=None,
                status=None,
                password=request.new_password,
                refresh_token=None,
                reset_token_timestamp=None
            ),
        )

        return SetInitialPasswordResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Password has been successfully set")],
            data=[],
        )
    except HTTPException:
        # re-raise HTTPExceptions
        raise

    except Exception as e:
        logger.exception(f"Error in set_initial_password: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to set initial password") from None

@router.post("/resend-initial-password", response_model=ResendInitialPasswordResponse)
async def resend_initial_password(
    request: ResendInitialPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ResendInitialPasswordResponse:
    """Resend initial password setup email. Only works for users with null password."""
    try:
        # Get the user by ID
        user = db.query(User).filter(User.id == request.user_id).first()
        if not user:
            raise HTTPException(  # noqa: TRY301
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "message": "User not found"}
            )

        # Check if password is null
        if user.password is not None:
            raise HTTPException(  # noqa: TRY301
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "User already has a password set. Use forgot password instead."}
            )

        # Check if user is active
        if user.status != "Active":
            raise HTTPException(  # noqa: TRY301
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": "User is not active"}
            )

        # Trigger RESEND_INITIAL_PASSWORD_EMAIL_AFTER_EXPIRY event
        event_data = Event(
            event_type=EventType.RESEND_INITIAL_PASSWORD_EMAIL_AFTER_EXPIRY,
            payload={
                "user": user
            },
        )

        await event_dispatcher.dispatch_event(db, event_data)
        success, messages = extract_status_messages(event_data.response) # type: ignore[arg-type]
        if not success:
            _raise_validation_error(messages)

        return ResendInitialPasswordResponse(
            success=True,
            message=messages,
            data=[],
        )
    except HTTPException:
        # re-raise HTTPExceptions
        raise

    except Exception as e:
        logger.exception(f"Error in resend_initial_password: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to resend initial password") from None


@router.post("/send-login-link", response_model=SendLoginLinkResponse)
async def send_login_link(
    request: SendLoginLinkRequest,
    db: Session = Depends(get_db),
) -> SendLoginLinkResponse:
    """
    Send a secure login link to the user's email address.

    This endpoint validates the email and sends a magic link for passwordless login.
    For security, it always returns a success message regardless of whether the email exists.
    """
    try:
        # Get user by email
        user_name = request.user_name.lower()
        user = None
        from email_validator import validate_email, EmailNotValidError
        try:
            email_validation = validate_email(user_name)
            user = get_user_by_email(db, user_name)
        except EmailNotValidError as e1:
            if isinstance(user_name, str):
                user_id = decrypt_id(user_name)
                if user_id:
                    user = get_user_by_id(db, user_id)
        except Exception as e:
            logger.error(f"Exception In send_login_link ({user_name}) : {e}")
            pass

        # For security, always return success even if user doesn't exist
        # This prevents email enumeration attacks
        if user is None:
            logger.info(f"User not found: {request.user_name}")
            return SendLoginLinkResponse(
                success=True,
                message=[ResponseMessage(success=True, message="If this email is registered, a login link has been sent.")],
                data=[],
            )

        # Check if user is active
        if user.status != "Active":
            logger.info(f"User is not active: {request.user_name}")
            return SendLoginLinkResponse(
                success=True,
                message=[ResponseMessage(success=True, message="If this email is registered, a login link has been sent.")],
                data=[],
            )
        # Decrypt case_id if provided and validate access
        case_id: int | None = None
        resolve_id: int | None = None
        user_id: int = int(user.id)
        user_role_code: str | None = None
        if request.case_id:
            try:
                decrypted_case_id = decrypt_id(request.case_id)
                if not decrypted_case_id or not decrypted_case_id.isdigit():
                    logger.info(f"Invalid case_id format: {request.case_id}, {request.user_name}")
                    return SendLoginLinkResponse(
                        success=True,
                        message=[ResponseMessage(success=True, message="If this email is registered, a login link has been sent.")],
                        data=[],
                    )
                case_id = int(decrypted_case_id)

                # Determine user role and verify access generically
                if user.user_roles:
                    user_role_code = UserRoleEnum.from_id(user.user_roles[0].role_id).display_name

                    if user_role_code == UserRoleEnum.CUSTOMER.display_name:
                        user_id = user.customer.id
                    elif user_role_code == UserRoleEnum.LAWYER.display_name:
                        user_id = user.lawyer.id
                    else:
                        user_id = user.id
                else:
                    logger.info(f"User has no roles: {request.user_name}")
                    return SendLoginLinkResponse(
                        success=True,
                        message=[ResponseMessage(success=True, message="If this email is registered, a login link has been sent.")],
                        data=[],
                    )
                # Verify user has access to this case
                try:
                    verify_case_access(
                        db=db,
                        case_id=case_id,
                        role_code=user_role_code,
                        user_id=user_id,
                    )
                except HTTPException:
                    # User doesn't have access to this case, return generic success for security
                    logger.exception(f"User doesn't have access to this case: {case_id}, {user_role_code}, {user_id}, {request.case_id}, {request.user_name}")
                    return SendLoginLinkResponse(
                        success=True,
                        message=[ResponseMessage(success=True, message="If this email is registered, a login link has been sent.")],
                        data=[],
                    )
            except (ValueError, TypeError):
                # Invalid case_id format, but continue without it
                logger.exception(f"Invalid case_id format: {request.case_id}, {request.user_name}")
                pass

        # Handle resolve_id if provided
        if request.resolve_id:
            try:
                decrypted_resolve_id = decrypt_id(request.resolve_id)
                if not decrypted_resolve_id or not decrypted_resolve_id.isdigit():
                    logger.info(f"Invalid resolve_id format: {request.resolve_id}, {request.user_name}")
                    return SendLoginLinkResponse(
                        success=True,
                        message=[ResponseMessage(success=True, message="If this email is registered, a login link has been sent.")],
                        data=[],
                    )
                else:
                    resolve_id = int(decrypted_resolve_id)
                    # Verify that the resolve exists
                    resolve = get_resolve_by_id(db, resolve_id)
                    if not resolve:
                        logger.info(f"Resolve not found: {resolve_id}, {request.user_name}")
                        return SendLoginLinkResponse(
                            success=True,
                            message=[ResponseMessage(success=True, message="If this email is registered, a login link has been sent.")],
                            data=[],
                        )
            except (ValueError, TypeError):
                # Invalid resolve_id format, but continue without it
                logger.exception(f"Invalid resolve_id format: {request.resolve_id}, {request.user_name}")
                pass

        # Build customer name from first_name and last_name
        first_name = str(user.first_name) if user.first_name else ""
        last_name = str(user.last_name) if user.last_name else ""
        customer_name = f"{first_name} {last_name}".strip() or "Customer"

        # Create event payload
        event_data = Event(
            event_type=EventType.SEND_LOGIN_LINK_EMAIL,
            payload={
                "case_id": case_id,
                "resolve_id": resolve_id,
                "user_id": int(user.id),
                "customer_email": str(user.email),
                "customer_name": customer_name,
            },
            user_id=user.id,
        )

        # Dispatch the event
        await event_dispatcher.dispatch_event(db, event_data)

        # Extract status messages
        success, messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]
        if not success:
            # Even if event fails, return generic success for security
            logger.info(f"Event failed: {request.case_id}, {request.user_name}")
            return SendLoginLinkResponse(
                success=True,
                message=[ResponseMessage(success=True, message="If this email is registered, a login link has been sent.")],
                data=[],
            )

        # Return generic success message (security: don't reveal if email exists)
        logger.info(f"Event succeeded: {request.case_id}, {request.user_name}")
        return SendLoginLinkResponse(
            success=True,
            message=[ResponseMessage(success=True, message="If this email is registered, a login link has been sent.")],
            data=[],
        )

    except ValueError as ve:
        logger.exception(f"ValueError in send_login_link({request.case_id}, {request.user_name}): {ve}")
        raise
    except HTTPException as he:
        logger.exception(f"HTTPException in send_login_link({request.case_id}, {request.user_name}): {he}")
        # re-raise HTTPExceptions
        raise
    except Exception as e:
        # Return generic success even on error for security
        logger.exception(f"Error in send_login_link({request.case_id}, {request.user_name}): {e}")
        return SendLoginLinkResponse(
            success=True,
            message=[ResponseMessage(success=True, message="If this email is registered, a login link has been sent.")],
            data=[],
        )


@router.get("/get-engage-link", response_model=GetEngageLinkResponse)
async def get_engage_link(
    request: GetEngageLinkRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> GetEngageLinkResponse:
    """Get engage link for the user."""
    try:
        
        detail = [{"success": False, "message": "Failed to retrieve engage URL"}]
        case = get_case_lawyer_by_case_id_service(db, int(request.case_id))
        if not case:
            logger.error("Case not found or invalid")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=detail
            )

        if case.is_lawyer_assigned is False:
            logger.error("Case is not assigned to an expert")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
        
        # if case.is_initial_payment_completed is False:
        #     logger.error("Case initial payment is not completed")
        #     raise HTTPException(
        #         status_code=status.HTTP_400_BAD_REQUEST, detail=detail
        #     )

        role_ids = [user_role.role_id for user_role in current_user.user_roles]
        if len(role_ids) == 0:
            logger.error("Invalid role code")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=detail
            )
        role_code = UserRoleEnum.from_id(role_ids[0]).display_name

        if role_code == UserRoleEnum.CUSTOMER.display_name:
            user = current_user
            if case.case_customers:
                customer = case.case_customers[0].customer
                if not customer:
                    logger.error("Customer not found")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND, detail=detail
                    )
                if customer.status != "Active":
                    logger.error("Customer is not active")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail=detail
                    )
                if user.id != customer.user_id:
                    logger.error("User does not have access to this case")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST, detail=detail
                    )
            else:
                logger.error("Customer not found")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=detail
                )
        else:
            user = case.case_customers[0].customer.user
            if not user:
                logger.error("User not found or not active")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND, detail=detail
                )

        engage_url = generate_engage_link(db, user, case)        
        engage_url_data = EngageUrlData(
            engage_url=engage_url
        )

        return GetEngageLinkResponse(
            success=True,
            message=[
                {"success": True, "message": "Engage link retrieved successfully"}
            ],
            data=engage_url_data,
        )

    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to retrieve engage URL", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve engage URL",
        ) from None


@router.post("/verify-code", response_model=GetVerifyCodeResponse)
async def verify_code(
    request: GetVerifyCodeRequest,
    db: Session = Depends(get_db),
) -> GetVerifyCodeResponse:
    """Verify code for the case."""
    try:

        x_api_key = settings.ENGAGE_API_KEY
        if not x_api_key or x_api_key != request.x_api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

        case_id_encrypted, case, user, engage_form_url = token_record_service(db, request)
        detail = [{"success": False, "message": "Invalid or expired token"}]

        if not engage_form_url:
            logger.error("Engage form URL is not found")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

        verify_code_data = VerifyCodeData(
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone=user.phone,
            gender=user.gender,
            gender_other=user.gender_other,
            client=engage_form_url,
            case_id=case_id_encrypted,
        )

        return GetVerifyCodeResponse(
            success=True,
            message=[
                {"success": True, "message": "Verify the engage request successfully"}
            ],
            data=verify_code_data,
        )

    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to verify the engage request", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify the engage request",
        ) from None


@router.post("/verify-engage-token", response_model=VerifyEngageTokenResponse)
async def verify_engage_token(
    request: VerifyEngageTokenRequest,
    db: Session = Depends(get_db),
) -> VerifyEngageTokenResponse:
    """Verify engage token from customer email."""

    from app.db.services.auth import generate_engage_link
    try:

        case_id_encrypted, case, user, engage_form_url = token_record_service(db, request)

        engage_url = generate_engage_link(db, user, case)

        verify_engage_token_data = VerifyEngageTokenData(
            engage_url=engage_url,
        )

        return VerifyEngageTokenResponse(
            success=True,
            message=[
                {"success": True, "message": "Token verified successfully"}
            ],
            data=verify_engage_token_data,
        )

    except HTTPException:
        raise
    except Exception:
        logger.error("Failed to verify the engage request", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify the engage request",
        ) from None
"""Case service functions for database operations."""
import logging

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, exists, or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, contains_eager

from app.db.models.case import Case
from app.db.models.case_customer import CaseCustomer
from app.db.models.case_engage import CaseEngage
from app.db.models.case_lawyer import CaseLawyer
from app.db.models.case_resolve import CaseResolve
from app.db.models.case_triage import CaseTriage
from app.db.models.customer import Customer
from app.db.models.invoice import Invoice
from app.db.models.lawyer import Lawyer
from app.db.models.match import Match
from app.db.services.general import (
    get_case_summary,
    get_partner_name_client_name,
    verify_case_access,
    get_resolve_by_case_id,
)
from app.db.services.resolve import get_result
from app.enums.case import CaseCategoryEnum, CasePriorityEnum, CaseStatusEnum, CaseStatusFilterEnum, CaseTypeEnum
from app.enums.base import NameExtractionOption
from app.enums.user_role import UserRoleEnum
from app.schemas.v1.case import CaseSearchRequest, CaseSummaryData
from app.utils.helpers import generate_case_no
from app.utils.formatters import extract_name_parts

logger = logging.getLogger(__name__)

# Constants for case_no generation
MAX_RETRIES = 3
CASE_NO_LENGTH = 7

def handle_integrity_error(
    e: IntegrityError, 
    case_no: str, 
    attempt: int, 
    max_retries: int
) -> None:
    """
    Handle IntegrityError by checking if it's a unique constraint violation.
    If it's a unique constraint violation, log and allow retry.
    If it's a different integrity error or max retries exceeded, raise HTTPException.
    
    Args:
        e: The IntegrityError exception
        case_no: The case number that caused the violation
        attempt: Current attempt number
        max_retries: Maximum number of retries allowed
        
    Raises:
        HTTPException: For non-unique integrity errors or when max retries exceeded
    """
    # Check if it's a unique constraint violation on case_no
    error_str = str(e.orig).lower() if hasattr(e, 'orig') else str(e).lower()
    
    if "unique constraint" not in error_str:
        raise ValueError("Database error during case creation") from e

    # Collision detected - log and check if we should retry
    logger.warning(
        f"Unique constraint violation on case_no: {case_no} "
        f"(attempt {attempt}/{max_retries}), retrying..."
    )
    
    # Check if we've exhausted all retries
    if attempt >= max_retries:
        logger.error(f"Failed to generate case number after multiple attempts: {attempt}/{max_retries}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": "Failed to generate case number after multiple attempts"
            }
        )
def create_case(
    db: Session,
    customer_id: int,
    resolve_id: int | None = None,
    triage_id: int | None = None,
) -> Case:
    """
    Create a new case with customer and resolve/triage relationships without committing.

    This function creates a case and its associations in a single transaction.
    It does not commit automatically, allowing the caller to control the transaction.
    The case_no will be automatically generated as a secure, human-friendly identifier.

    Strategy:
    - Attempt to insert with a freshly generated case_no.
    - On unique constraint violation, retry with a new case_no up to MAX_RETRIES times.

    Args:
        db: Database session
        customer_id: ID of the customer
        resolve_id: Optional resolve ID to associate with the case
        triage_id: Optional triage ID to associate with the case (sets is_triage=True)

    Returns:
        Case: The created case object

    Raises:
        ValueError: If customer_id is invalid or resolve_id is provided but invalid
    """

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Generate a new case_no for each attempt
            case_no = generate_case_no(length=CASE_NO_LENGTH)

            #Check if the case no is already used
            if db.query(Case.case_no).filter(Case.case_no == case_no).first():
                continue
            
            # Create case data
            case_data = {
                'start_date': date.today(),
                'case_type': CaseTypeEnum.FAMILY_LAW,
                'priority': CasePriorityEnum.HIGH,
                'status': CaseStatusEnum.OPEN,
                'case_no': case_no,
                'is_triage': triage_id is not None,
            }
            # Create the case
            case = Case(**case_data)
            db.add(case)
            db.flush()
            break
        except IntegrityError as e:
            db.rollback()
            
            handle_integrity_error(e, case_no, attempt, MAX_RETRIES)
            continue

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "success": False,
                    "message": "Unexpected error creating case"
                }
            ) from e

    # Create case_customer association
    case_customer = CaseCustomer(
        case_id=case.id,
        customer_id=customer_id
    )
    db.add(case_customer)

    # Create case_resolve association if resolve_id is provided
    if resolve_id is not None:
        case_resolve = CaseResolve(
            case_id=case.id,
            resolve_id=resolve_id
        )
        db.add(case_resolve)

    # Create case_triage association if triage_id is provided
    if triage_id is not None:
        case_triage = CaseTriage(
            case_id=case.id,
            triage_id=triage_id
        )
        db.add(case_triage)

    db.flush()  # Flush all associations

    return case


def get_all_cases_service(
    db: Session,
    request_data: CaseSearchRequest,
    role_code: str,
    user_id: int,
) -> tuple[list[Case], int]:
    """
    Get all cases with pagination and ordering based on user role.

    Args:
        db: Database session
        request_data: CaseSearchRequest
    Returns:
        Tuple of (cases list, total count)
    """
    from sqlalchemy.orm import aliased

    from app.db.models.user import User
    from app.enums.case import CaseIntentEnum

    page = request_data.page
    limit = request_data.limit
    order_by = request_data.order_by
    order_dir = request_data.order_dir
    search = request_data.search
    case_no = request_data.case_no
    case_status = request_data.case_status
    case_intent = request_data.case_intent
        
    # Build base query for filtering (without eager loading)
    base_query = db.query(Case.id)

    if case_status:
        base_query = base_query.filter(Case.status == case_status)

    if case_intent and case_intent == CaseIntentEnum.HIGH_INTENT:
        base_query = base_query.filter(Case.is_triage == True)
    elif case_intent and case_intent == CaseIntentEnum.LOW_INTENT:
        base_query = base_query.filter(Case.is_triage == False)

    # Apply role-based filters
    if role_code == UserRoleEnum.NAVIGATOR.display_name:
        # Navigator can see all cases
        filter_query = base_query
    elif role_code == UserRoleEnum.CUSTOMER.display_name:
        # Customer can only see their own cases
        filter_query = base_query.join(CaseCustomer).filter(
            CaseCustomer.customer_id == user_id
        )
    elif role_code == UserRoleEnum.LAWYER.display_name:
        # Lawyer filtering based on category
        category = request_data.category if request_data.category else CaseCategoryEnum.ALL
        
        # - include cases assigned to this lawyer
        assigned_exists = exists().where(
            and_(CaseLawyer.case_id == Case.id, CaseLawyer.lawyer_id == user_id)
        )
        # - include cases matched to this lawyer
        matched_exists = exists().where(
            and_(
                Match.case_id == Case.id,
                Match.lawyer_id == user_id,
                Case.is_match_confirmed == True,
            )
        )
        
        if category == CaseCategoryEnum.MY_CASES:
            # My Cases: Cases assigned to me
            filter_query = base_query.filter(assigned_exists)
        elif category == CaseCategoryEnum.MATCHED_CASES:
            # Matched Cases: Cases matched to me but not awarded to anyone
            filter_query = base_query.filter(
                and_(matched_exists, Case.is_lawyer_assigned == False))
        elif category == CaseCategoryEnum.MISSED_CASES:
            # Missed Cases: Cases matched to me but awarded to a different lawyer
            filter_query = base_query.filter(
                and_(
                    matched_exists,
                    Case.is_lawyer_assigned == True,
                    ~assigned_exists
                )
            )
        else:
            # ALL: Show all cases (assigned to me OR matched to me)
            filter_query = base_query.filter(
                or_(assigned_exists, matched_exists)
            )
    else:
        raise ValueError(f"Invalid role code: {role_code}")

    # Exclude archived cases for Customer and Lawyer roles
    if role_code != UserRoleEnum.NAVIGATOR.display_name:
        filter_query = filter_query.filter(Case.status != CaseStatusEnum.ARCHIVED)

    # Apply search filter if provided
    if search and search.strip():
        customer_user_alias = aliased(User)
        filter_query = (
            filter_query.join(CaseCustomer, CaseCustomer.case_id == Case.id, isouter=False)
            .join(Customer, Customer.id == CaseCustomer.customer_id)
            .join(customer_user_alias, customer_user_alias.id == Customer.user_id)
            .filter(
                or_(
                    customer_user_alias.first_name.ilike(f"%{search}%"),
                    customer_user_alias.last_name.ilike(f"%{search}%"),
                    # ((customer_user_alias.first_name or "") + " " + (customer_user_alias.last_name or "")).ilike(f"%{search}%"),
                    (func.trim(customer_user_alias.first_name) + " " + func.trim(customer_user_alias.last_name)).ilike(f"%{search}%"),
                    customer_user_alias.email.ilike(f"%{search}%"),
                )
            )
        )

    # Apply case number filter if provided
    if case_no:
        filter_query = filter_query.filter(Case.case_no == case_no.strip().upper())
    
    # Apply status filter if provided and not "all"
    if request_data.status and request_data.status != CaseStatusFilterEnum.ALL:
        status_fields = [
            # "is_case_opened",
            "is_kyc_completed",
            "is_match_confirmed",
            "is_profile_card_sent",
            "is_lawyer_assigned",
            "is_initial_payment_completed",
            "is_onboarding_completed",
        ]

        status_order = {
            CaseStatusFilterEnum.CASE_OPENED: -1,
            CaseStatusFilterEnum.KYC_COMPLETED: 0,
            CaseStatusFilterEnum.MATCH_CONFIRMED: 1,
            CaseStatusFilterEnum.PROFILE_CARD_SENT: 2,  
            CaseStatusFilterEnum.LAWYER_ASSIGNED: 3,
            CaseStatusFilterEnum.INITIAL_PAYMENT_COMPLETED: 4,
            CaseStatusFilterEnum.ONBOARDING_COMPLETED: 5,
        }

        idx = status_order.get(request_data.status)
        if idx is not None:
            # earlier statuses must be True, later statuses must be False
            conditions = [
                getattr(Case, f) == True for f in status_fields[:idx + 1]
            ] + [
                getattr(Case, f) == False for f in status_fields[idx + 1:]
            ]
            filter_query = filter_query.filter(*conditions)

    # Get unique case IDs and count (efficient)
    filter_query = filter_query.distinct()
    case_ids_subquery = filter_query.subquery()
    total_count = db.query(case_ids_subquery).count()

    # Apply ordering
    order_column = getattr(Case, order_by, Case.created_at)
    if order_dir.lower() == "desc":
        order_clause = desc(order_column)
    else:
        order_clause = order_column

    # Apply pagination
    offset = (page - 1) * limit

    # Final query with eager loading (only for paginated results)
    cases = (
        db.query(Case)
        .options(
            joinedload(Case.case_customers)
            .joinedload(CaseCustomer.customer)
            .joinedload(Customer.user),
            joinedload(Case.case_lawyers)
            .joinedload(CaseLawyer.lawyer)
            .joinedload(Lawyer.user),
        )
        .filter(Case.id.in_(db.query(case_ids_subquery.c.id)))
        .order_by(order_clause)
        .offset(offset)
        .limit(limit)
        .all()
    )

    return cases, total_count


def update_case_interest_service(
    db: Session,
    case_id: int,
    lawyer_id: int,
    user_id: int,
) -> dict:
    """
    Update case interest status for a lawyer.

    Args:
        db: Database session
        case_id: ID of the case
        lawyer_id: ID of the lawyer
        user_id: ID of the user performing the action

    Returns:
        dict: Either the updated match record or a duplicate action indicator

    Raises:
        HTTPException: If case or lawyer not found, or no match exists
    """
    from datetime import datetime, timezone

    from fastapi import HTTPException, status

    from app.db.models.match import Match
    from app.enums.match import MatchStatusEnum
    from app.utils.formatters import format_case_number
    # Check if match exists
    match = (
        db.query(Match)
        .filter(Match.case_id == case_id, Match.lawyer_id == lawyer_id)
        .first()
    )

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "No match found for this case and expert",
            },
        )

    # Check if action is already done - allow interest even if previously declined
    if match.status == MatchStatusEnum.INTERESTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": "Case interest action already completed",
            },
        )

    # If previously declined, clear the declined reason when marking as interested
    if match.status == MatchStatusEnum.DECLINED:
        object.__setattr__(match, "declined_reason", None)

    # Update match status using object.__setattr__ to avoid type issues
    object.__setattr__(match, "status", MatchStatusEnum.INTERESTED)
    object.__setattr__(match, "action_user_id", user_id)
    object.__setattr__(match, "action_date", datetime.now(timezone.utc))

    db.commit()

    case = match.case
    case_no = format_case_number(str(case.case_no))
    return {
        "message": f"Your interest has been recorded. Case - {case_no}.",
        "match": match,
    }


def update_case_decline_service(
    db: Session,
    case_id: int,
    lawyer_id: int,
    user_id: int,
    decline_reason: dict,
) -> dict:
    """
    Update case decline status for a lawyer.

    Args:
        db: Database session
        case_id: ID of the case
        lawyer_id: ID of the lawyer
        user_id: ID of the user performing the action
        decline_reason: Decline reason as JSON object
    Returns:
        dict: Either the updated match record or a duplicate action indicator

    Raises:
        HTTPException: If case or lawyer not found, or no match exists
    """
    from datetime import datetime, timezone

    from fastapi import HTTPException, status

    from app.db.models.match import Match
    from app.enums.match import MatchStatusEnum
    from app.utils.formatters import format_case_number

    # Check if match exists
    match = (
        db.query(Match)
        .filter(Match.case_id == case_id, Match.lawyer_id == lawyer_id)
        .first()
    )

    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "message": "No match found for this case and expert",
            },
        )

    # Check if decline is allowed - prevent decline if already interested
    if match.status == MatchStatusEnum.INTERESTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Cannot decline a case that is already marked as interested",
            },
        )

    # Check if action is already done
    if match.status == MatchStatusEnum.DECLINED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "message": "Case decline action already completed",
            },
        )

    # Update match status using object.__setattr__ to avoid type issues
    object.__setattr__(match, "status", MatchStatusEnum.DECLINED)
    object.__setattr__(match, "action_user_id", user_id)
    object.__setattr__(match, "action_date", datetime.now(timezone.utc))
    object.__setattr__(match, "declined_reason", decline_reason)

    db.commit()

    case = match.case
    case_no = format_case_number(str(case.case_no))
    return {
        "message": f"Your response has been noted. Case - {case_no}.",
        "match": match,
    }


def get_case_by_id(db: Session, case_id: int) -> Case | None:
    """
    Get a case by its ID.
    """
    return db.query(Case).filter(Case.id == case_id).first()

def get_case_no_by_id(db: Session, case_id: int) -> str | None:
    """
    Get a case no by its ID.
    """
    return db.query(Case.case_no).filter(Case.id == case_id).first()

def is_case_awarded(db: Session, case_id: int) -> bool:
    """
    Check if a case is awarded to a lawyer.
    """
    result = db.query(Case.is_lawyer_assigned).filter(Case.id == case_id).scalar()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": False, "message": "Case not found"})
    return result

def is_case_archived(db: Session, case_id: int) -> bool:
    """
    Check if a case is archived.
    """
    from app.enums.case import CaseStatusEnum
    result = db.query(Case.status).filter(Case.id == case_id).scalar()
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": False, "message": "Case not found"})
    return result == CaseStatusEnum.ARCHIVED

def get_case_by_customer_invoice_id(db: Session, customer_id: int, invoice_id: int) -> Case | None:
    """
    Get a case by its customer ID and invoice ID.
    """
    return db.query(Case).join(Case.case_customers).join(Case.invoices).filter(CaseCustomer.customer_id == customer_id, Invoice.id == invoice_id).first()


def get_case_details_service(
    db: Session,
    case_id: int,
    role_code: str,
    user_id: int,
) -> dict:
    """
    Get case details with role-based filtering.

    Args:
        db: Database session
        case_id: ID of the case
        role_code: Role code of the user
        user_id: ID of the user (customer_id for customer, lawyer_id for lawyer)

    Returns:
        dict: Case details with summary and parties involved

    Raises:
        HTTPException: If case not found or access denied
    """
    from app.enums.component import ComponentEnum
    # from app.db.services.kyc import get_customer_phone_from_kyc
    from app.db.services.timeline_event import get_timeline_event_from_map
    from app.utils.helpers import get_template_json
    from app.db.services.general import get_timeline_type

    # First, check if case exists with a lightweight query
    verify_case_access(db, case_id, role_code, user_id)

    # Authorization passed - now load all case data with relationships
    case = (
        db.query(Case)
        .options(
            joinedload(Case.case_customers)
            .joinedload(CaseCustomer.customer)
            .joinedload(Customer.user),
            joinedload(Case.case_lawyers)
            .joinedload(CaseLawyer.lawyer)
            .joinedload(Lawyer.user),
            joinedload(Case.case_resolves),
            joinedload(Case.case_triages),
            joinedload(Case.case_engages).joinedload(CaseEngage.engage),
            joinedload(Case.matches),
        )
        .filter(Case.id == case_id)
        .first()
    )
    case_status = case.status
    if role_code == UserRoleEnum.CUSTOMER.display_name:
        resolve = get_resolve_by_case_id(db, case_id)
        if resolve:
            result = get_result(resolve)
            recommended_approach = result.get("recommended_approach", {}) if result else None
            title = recommended_approach.get("title", "") if recommended_approach else ""
            summary = recommended_approach.get("summary", "") if recommended_approach else ""
            case_summary = {
                "summary": [
                    # {"title": result.get("title", ""), "description": result.get("summary", "")}
                    {"title": title, "description": summary}
                ]
            }
        else:
            case_summary = {"summary": []}
    elif role_code == UserRoleEnum.LAWYER.display_name:
        if case.is_ai_summary_generated is False:
            case_summary = {"summary": [
                {
                    "title": "Processing",
                    "description": "AI summary generation is being processed."
                }
            ]}
        else:
            case_summary = {"summary": case.summary} if case.summary is not None else {"summary": []}
    else:

        if case.is_ai_summary_generated is False:
            case_summary = {"summary": [
                    {
                        "title": "Error",
                        "description": "AI summary generation failed after multiple attempts. Please try again later."
                    },
                    {
                        "title": "Action Required",
                        "description": "Please review the case details manually and contact support if this issue persists."
                    }
                ]}
        else:
            case_summary = {"summary": case.summary} if case.summary is not None else {"summary": []}
            # case_summary = get_case_summary(db, case_id, key="title", value="description")

    # Get partner name and client name from KYC (question identifier "2" and "1")
    partner_name = None
    client_name = None

    #get partner name and client name from the resolve partner name and customer name
    if case.case_resolves and len(case.case_resolves) > 0:
        resolve = case.case_resolves[0].resolve
        partner_name = resolve.partner_name
        client_name = resolve.customer_name
    else:
        # Try to get partner name and client name from KYC
        if case.case_engages and len(case.case_engages) > 0:
            # Get the engage relationship
            engage = case.case_engages[0].engage
            client_name, partner_name = get_partner_name_client_name(db, engage.id)

    if partner_name:
        partner_name = extract_name_parts(partner_name, NameExtractionOption.FIRST)

    # Get customer information
    customer = None
    customer_user = None
    client_phone = None
    client_email = None
    if case.case_customers and len(case.case_customers) > 0:
        customer = case.case_customers[0].customer
        customer_user = customer.user
        client_phone = customer_user.phone
        client_email = customer_user.email

    # consider kyc phone number provided by the customer
    # client_kyc_phone = get_customer_phone_from_kyc(db, case_id)
    # if client_kyc_phone:
    #     client_phone = client_kyc_phone

    # Get lawyer information (only for assigned lawyer)
    lawyer = None
    lawyer_user = None
    lawyer_name = None
    lawyer_phone = None
    lawyer_email = None
    if case.case_lawyers and len(case.case_lawyers) > 0:
        lawyer = case.case_lawyers[0].lawyer
        if role_code != UserRoleEnum.LAWYER.display_name or (role_code == UserRoleEnum.LAWYER.display_name and lawyer.id == user_id):
            lawyer_user = lawyer.user
            lawyer_name = lawyer_user.first_name + " " + lawyer_user.last_name
            lawyer_phone = lawyer_user.phone
            lawyer_email = lawyer_user.email

    # Role-based filtering for response data
    if role_code == UserRoleEnum.NAVIGATOR.display_name:
        # Determine action buttons based on case and match status
        action_buttons = {}
        if case.is_profile_card_sent is False and case.matches and len(case.matches) > 0:
            action_buttons["review_profiles"] = True
        if case.is_match_confirmed is True:
           # Check if there are unconfirmed matches
            confirmed_matches_count = sum(1 for m in case.matches if m.is_confirmed)
            if confirmed_matches_count == 0:
                action_buttons["send_to_customer"] = True
        if case.status == CaseStatusEnum.OPEN:
            action_buttons["archive"] = True
        if case.status == CaseStatusEnum.ARCHIVED:
            button_status = get_button_status_from_timeline_event(db, ComponentEnum.CASE_ARCHIVED_NN_CARD.value, case_id)
            if button_status == True:
                action_buttons["unarchive"] = True
        if case.is_alignment_check_hold is True:
            action_buttons["alignment_check_push"] = True

        # Navigator can see all fields
        return get_case_details_response_data(
            case_summary,
            client_name,
            client_phone,
            client_email,
            lawyer_name,
            lawyer_email,
            lawyer_phone,
            partner_name,
            action_buttons,
            case.is_ai_summary_generated,
            case.analytics_data,
            case_status
        )

    elif role_code == UserRoleEnum.CUSTOMER.display_name:
        action_buttons = {}
        if case and case.is_triage is False:
            template, last_version = get_template_json(str(ComponentEnum.BOOK_FREE_CALL_CUS_CARD.value), str(UserRoleEnum.CUSTOMER.value), "timeline")
            timeline_type = get_timeline_type(db, ComponentEnum.BOOK_FREE_CALL_CUS_CARD.value, UserRoleEnum.CUSTOMER.value, last_version)
            if timeline_type:
                timeline = get_timeline_event_from_map(db, str(timeline_type.type_name), int(case_id))
                if not timeline:
                    action_buttons["book_free_call"] = True
        # Customer can see limited fields
        return get_case_details_response_data(
            case_summary,
            client_name,
            None,
            None,
            lawyer_name,
            None,
            None,
            partner_name,
            action_buttons,
            None,
            case.analytics_data,
            case_status
        )

    elif role_code == UserRoleEnum.LAWYER.display_name:
        # Lawyer can see specific fields
        return get_case_details_response_data(
            case_summary,
            client_name,
            None,
            None,
            lawyer_name,
            None,
            None,
            partner_name,
            None,
            None,
            case.analytics_data,
            case_status
        )

    else:
        # This should never be reached due to earlier check, but for safety
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "message": "Access denied: Invalid role"},
        )

def get_case_details_response_data(
    case_summary: dict,
    client_name: str | None,
    client_phone: str | None,
    client_email: str | None,
    lawyer_name: str | None,
    lawyer_email: str | None,
    lawyer_phone: str | None,
    partner_name: str | None,
    action_buttons: dict | None,
    is_ai_summary_generated: bool | None,
    analytics_data: dict | None,
    case_status: str,
) -> dict:
    return {
        "status": case_status,
        "case_summary": case_summary,
        "parties_involved": {
            "client_name": client_name,
            "client_email": client_email,
            "client_phone": client_phone,
            "lawyer_name": lawyer_name,
            "lawyer_email": lawyer_email,
            "lawyer_phone": lawyer_phone,
            "partner_name": partner_name,
        },
        "action_buttons": action_buttons,
        "is_ai_summary_generated": is_ai_summary_generated,
        "analytics_data": analytics_data,
    }


def update_case_summary_service(db: Session, case_id: int, case_summary: list[dict]) -> None:
    """
    Update case summary for a case.

    Args:
        db: Database session
        case_id: Case ID
        case_summary: List of summary items with title and description
    """
    try:
        case = get_case_by_id(db, case_id)
        if case is None:
            raise HTTPException( #noqa: TRY301
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "message": "Case not found"}
            )
        case.summary = case_summary  # type: ignore[assignment]
        db.commit()
    except Exception as e:
        logger.exception(f"Error in updating case summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to update case summary"}
        ) from e


def get_case_summary_service(db: Session, case_id: int, role_code: str | None = None) -> CaseSummaryData:
    """
    Get case summary for a case.
    """
    try:
        case = get_case_by_id(db, case_id)
        if case is None:
            raise HTTPException( #noqa: TRY301
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"success": False, "message": "Case not found"}
            )
        
        # For customers, get summary from resolve result (same format as get_case_details_service)
        if role_code == UserRoleEnum.CUSTOMER.display_name:
            resolve = get_resolve_by_case_id(db, case_id)
            if resolve:
                result = get_result(resolve)
                recommended_approach = result.get("recommended_approach", {}) if result else None
                title = recommended_approach.get("title", "") if recommended_approach else ""
                summary = recommended_approach.get("summary", "") if recommended_approach else ""
                case_summary = [
                    # {"title": result.get("title", ""), "description": result.get("summary", "")}
                    {"title": title, "description": summary}
                ]
            else:
                case_summary = None
        else:
            # For other roles, use case summary from database
            case_summary = case.summary if case.summary is not None else None  # type: ignore[arg-type]
        
        data = CaseSummaryData(
            case_id=str(case_id),
            case_summary=case_summary,  # type: ignore[arg-type]
        )
        return data
    except Exception as e:
        logger.exception(f"Error in getting case summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to get case summary"}
        ) from e


def get_case_by_customer_id(db: Session, customer_id: int) -> Case | None:
    """
    Get a case by its customer ID.
    """
    from app.db.models.case_lawyer import CaseLawyer
    from app.db.models.case_customer import CaseCustomer
    from app.db.models.customer import Customer
    from app.enums.law_firm import LawFirmStatusEnum
    from app.enums.lawyer import LawyerStatusEnum
    from app.enums.case import CaseStatusEnum
    from app.db.models.lawyer_law_firm import LawyerLawFirm
    from app.db.models.law_firm import LawFirm
    from app.enums.user import StatusEnum
    from app.db.models.user import User

    return db.query(Case).options(
            joinedload(Case.case_lawyers)
            .joinedload(CaseLawyer.lawyer)
            .joinedload(Lawyer.user),
            joinedload(Case.case_lawyers)
            .joinedload(CaseLawyer.lawyer)
            .joinedload(Lawyer.lawyer_law_firms)
            .joinedload(LawyerLawFirm.law_firm),
            joinedload(Case.case_customers)
            .joinedload(CaseCustomer.customer),
        ).join(CaseCustomer, CaseCustomer.case_id == Case.id)\
         .join(Customer, Customer.id == CaseCustomer.customer_id)\
         .join(CaseLawyer, CaseLawyer.case_id == Case.id)\
         .join(Lawyer, Lawyer.id == CaseLawyer.lawyer_id)\
         .join(User, User.id == Lawyer.user_id)\
         .join(LawyerLawFirm, LawyerLawFirm.lawyer_id == Lawyer.id)\
         .join(LawFirm, LawFirm.id == LawyerLawFirm.lawfirm_id)\
         .filter(
            Case.status == CaseStatusEnum.OPEN,
            Lawyer.status == LawyerStatusEnum.ACTIVE,
            User.status == StatusEnum.ACTIVE,
            LawFirm.status == LawFirmStatusEnum.ACTIVE, 
            LawFirm.engage_form_url.isnot(None),
            Customer.id == customer_id
         ).first()


def get_not_interested_cases(db: Session, lawyer_interest_deadline_hours: int) -> list[Case]:
    """Get lawyers from match table where status is PENDING, is_confirmed is False, case
    is_no_interest_notified is False, and case profile_card_sent_at is older than the
    given deadline (e.g. 24h ago if lawyer_interest_deadline_hours is 24).
    """
    from datetime import datetime, timezone, timedelta
    from app.enums.match import MatchStatusEnum

    deadline_threshold = datetime.now(timezone.utc) - timedelta(
        hours=lawyer_interest_deadline_hours
    )
    cases = (
        db.query(Case)
        .options(
            contains_eager(Case.matches).contains_eager(Match.lawyer).joinedload(Lawyer.user),
            joinedload(Case.case_customers).joinedload(CaseCustomer.customer).joinedload(Customer.user),
        )
        .join(Match, Case.id == Match.case_id, isouter=True)
        .join(Lawyer, Lawyer.id == Match.lawyer_id, isouter=True)
        .filter(
            Match.status == MatchStatusEnum.PENDING,
            Match.is_confirmed.is_(False),
            Case.is_no_interest_notified.is_(False),
            Case.match_confirmed_at.isnot(None),
            Case.is_profile_card_sent.is_(False),
            Case.match_confirmed_at < deadline_threshold,
        )
        # .distinct()
        .all()
    )
    return cases


def get_button_status_from_timeline_event(db: Session, timeline_type_name: str, case_id: int) -> bool:
    """
    Get button status from timeline event.
    """
    from app.db.models.timeline_event import TimelineEvent
    from app.db.models.timeline_type import TimelineType
    import json

    # meta_data = db.query(TimelineEvent.meta_data).join(TimelineType, TimelineEvent.timeline_type_id == TimelineType.id).filter(TimelineType.type_name == timeline_type_name, TimelineEvent.case_id == case_id).order_by(TimelineEvent.id.desc()).first()
    # if meta_data:
    #     print(meta_data)
    #     meta_data = json.loads(meta_data)
    #     print("action_buttons >>>", meta_data.get("action_buttons", {}))
    #     return meta_data.get("action_buttons", {}).get("unarchive", False)
    # return False

    row = (
        db.query(TimelineEvent.meta_data)
        .join(TimelineType, TimelineEvent.timeline_type_id == TimelineType.id)
        .filter(
            TimelineType.type_name == timeline_type_name,
            TimelineEvent.case_id == case_id,
        )
        .order_by(TimelineEvent.id.desc())
        .first()
    )

    if not row:
        return False

    meta_data_str = row[0]  # extract Text column from Row
    if not meta_data_str:
        return False

    meta_data = json.loads(meta_data_str)
    return meta_data.get("action_buttons", {}).get("unarchive", False)


import json
import logging
from datetime import datetime, timezone
from typing import cast, List

import boto3
from sqlalchemy import and_, or_, true
from sqlalchemy.orm import Session, joinedload

from app.db.models import (
    Case,
    CaseCustomer,
    CaseLawyer,
    Lawyer,
    Match,
    TimelineEvent,
    TimelineMap,
    TimelineType,
    User,
)
from app.db.models.websocket_connection import WebSocketConnection
from app.enums.base import SortDirection
from app.enums.component import ComponentEnum
from app.enums.lawyer import LawyerStatusEnum
from app.enums.match import MatchStatusEnum
from app.enums.user import StatusEnum
from app.enums.user_role import UserRoleEnum
from app.schemas.v1.lawyer import LawFirmData
from app.schemas.v1.timeline_event import (
    ConfirmedLawyerData,
    GetMatchedLawyersRequest,
    LawyerData,
    TimelineEventDetails,
)
from app.schemas.v1.websocket import WebSocketMessage
from app.db.services.general import get_matched_lawyers_by_case_id
from app.utils.encryption import decrypt_id, encrypt_id
from app.utils.helpers import _parse_json_field, calculate_lawyer_experience
from app.enums.component import ComponentEnum
from app.db.models.websocket_connection import WebSocketConnection
import logging
from app.utils.photo_utils import generate_photo_urls
logger = logging.getLogger(__name__)

# OPTIMIZATION: Cache Lambda client to avoid creating it on every call
_lambda_client = None

def get_lambda_client():
    """Get cached Lambda client or create new one."""
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = boto3.client("lambda")
    return _lambda_client


class SafeFormatter(dict):
    """A dictionary subclass that returns a placeholder for missing keys instead of raising KeyError."""
    
    def __missing__(self, key: str) -> str:
        """Return a placeholder when a key is missing."""
        return f"{{{key}}}"    

def get_timeline_events_by_case_id(
    db: Session,
    case_id: int,
    page: int = 0,
    limit: int = 10,
    order_dir: str = SortDirection.DESC,
    order_by: str = "id",
    role_code: str | None = None,
    user: User | None = None,
    request_role_code: str | None = None,
    timeline_event_ids: list[int] | int | None = None,
    lawyer_id: str | None = None,
) -> tuple[list[TimelineEventDetails] | None, int]:
    """Get timeline events for a specific case with pagination."""
    if page < 1:
        offset = 0
    else:
        offset = page - 1

    order_col = getattr(TimelineEvent, order_by)
    order_criteria = (
        order_col.asc() if order_dir == SortDirection.ASC.value else order_col.desc()
    )

    if timeline_event_ids:
        if not isinstance(timeline_event_ids, list):
            timeline_event_ids = [timeline_event_ids]

    # Base query - always start with TimelineEvent
    query = db.query(TimelineEvent).filter(TimelineEvent.case_id == case_id)
    results = []
    total_records = 0
    if role_code and user:
        request_role = (
            UserRoleEnum.from_code(request_role_code) if request_role_code else None
        )
        if role_code == UserRoleEnum.NAVIGATOR.display_name:
            # Get the latest event for each timeline type
            # subquery = (
            #     db.query(
            #         TimelineEvent.timeline_type_id,
            #         func.max(TimelineEvent.created_at).label("max_time"),
            #     )
            #     .filter(TimelineEvent.case_id == case_id)
            #     .group_by(TimelineEvent.timeline_type_id)
            #     .subquery()
            # )
            if request_role is None or request_role == UserRoleEnum.NAVIGATOR:

                # query = query.join(
                #     subquery,
                #     and_(
                #         TimelineEvent.timeline_type_id == subquery.c.timeline_type_id,
                #         TimelineEvent.created_at == subquery.c.max_time,
                #     ),
                    # Role code filter for Navigator. Navigator can view all timeline events for their case.
                query = query.join(TimelineType, TimelineEvent.timeline_type_id == TimelineType.id
                    ).filter(TimelineType.role_code == role_code)
            elif request_role and request_role == UserRoleEnum.LAWYER:
                query = (
                    query.join(
                        TimelineType,
                        TimelineEvent.timeline_type_id == TimelineType.id,
                        isouter=True,
                    )
                    # .join(
                    #     subquery,
                    #     and_(
                    #         TimelineEvent.timeline_type_id
                    #         == subquery.c.timeline_type_id,
                    #         TimelineEvent.created_at == subquery.c.max_time,
                    #     ),
                    # )
                    .where(TimelineType.role_code == request_role_code)
                )
                if lawyer_id:
                    lawyer_id_int = int(lawyer_id)
                    
                    lawyer_case_exists = (
                        db.query(CaseLawyer)
                        .filter(
                            CaseLawyer.lawyer_id == lawyer_id_int,
                            CaseLawyer.case_id == case_id,
                        )
                        .exists()
                    )
                    lawyer_user = db.query(Lawyer.user_id).filter(Lawyer.id == lawyer_id_int).scalar()
                    
                    if lawyer_user:
                        query = query.where(
                            or_(
                                TimelineEvent.notify_user_id == lawyer_user,
                                and_(
                                    TimelineEvent.notify_user_id.is_(None),
                                    lawyer_case_exists,
                                ),
                            )
                        )            
            elif request_role and request_role == UserRoleEnum.CUSTOMER:
                query = query.join(
                    TimelineType,
                    TimelineEvent.timeline_type_id == TimelineType.id,
                    isouter=True,
                )
                query = query.where(and_(TimelineType.role_code == request_role_code))

        elif role_code == UserRoleEnum.LAWYER.display_name:
            if user.lawyer:
                # Subquery: does lawyer have mapping for this case?
                lawyer_case_exists = (
                    db.query(CaseLawyer)
                    .filter(
                        CaseLawyer.lawyer_id == user.lawyer.id,
                        CaseLawyer.case_id == case_id,
                    )
                    .exists()
                )
                query = query.join(
                    TimelineType,
                    TimelineEvent.timeline_type_id == TimelineType.id,
                    isouter=True,
                )
                query = query.where(
                    and_(
                        or_(
                            TimelineEvent.notify_user_id == user.id,
                            and_(
                                TimelineEvent.notify_user_id.is_(None),
                                lawyer_case_exists,
                            ),
                        ),
                        TimelineType.role_code == role_code,
                    )
                )

        else:
            query = query.join(
                TimelineType,
                TimelineEvent.timeline_type_id == TimelineType.id,
                isouter=True,
            )
            query = query.where(
                and_(
                    TimelineType.role_code == role_code,
                    # Customer can view all timeline events for their case
                    # TimelineEvent.notify_user_id == user.id,
                )
            )
        if timeline_event_ids:
            query = query.filter(TimelineEvent.id.in_(timeline_event_ids))
        # Get total count before applying pagination
        total_records = query.count()

        # offset calculation
        offset = (page - 1) * int(limit)
        # Add ordering and pagination
        results = query.order_by(order_criteria).offset(offset).limit(limit).all()
    elif timeline_event_ids:
        query = db.query(TimelineEvent).filter(TimelineEvent.id.in_(timeline_event_ids)
                    ).order_by(order_criteria)
        
        results = query.all()
        total_records = len(results)

    data = []
    matched_lawyers = None
    if results:
        # Fetch matched lawyers for the given case_id from the match table
        if role_code == UserRoleEnum.NAVIGATOR.display_name:
            matched_lawyers = get_matched_lawyers_by_case_id(db, case_id, True)
        else:
            matched_lawyers = None
        
        for result in results:
            # Ensure we have a proper TimelineEvent object
            if (
                hasattr(result, "id")
                and hasattr(result, "created_at")
                and hasattr(result, "updated_at")
            ):
                data.append(
                    TimelineEventDetails(
                        id=str(result.id),
                        case_id=str(result.case_id),
                        timeline_type_id=str(result.timeline_type_id),
                        timeline_type_name=result.timeline_type.type_name,
                        version=result.timeline_type.version,
                        meta_data=json.loads(str(result.meta_data))
                        if result.meta_data
                        else None,
                        action_user_id=str(result.action_user_id)
                        if result.action_user_id
                        else None,
                        notify_user_id=str(result.notify_user_id)
                        if result.notify_user_id
                        else None,
                        action_user_name=result.action_user.first_name
                        + " "
                        + result.action_user.last_name
                        if result.action_user
                        else None,
                        action_user_role=UserRoleEnum.from_id(result.action_user.user_roles[0].role_id).display_name
                        if result.action_user and result.action_user.user_roles else None
                        if result.action_user
                        else None,
                        notify_user_name=result.notify_user.first_name
                        + " "
                        + result.notify_user.last_name
                        if result.notify_user
                        else None,
                        created_at=str(result.created_at.strftime("%Y-%m-%dT%H:%M:%S.%f")),
                        updated_at=str(result.updated_at.strftime("%Y-%m-%dT%H:%M:%S.%f")),
                    )
                )

    return data, total_records, matched_lawyers


def check_customer_case_access(db: Session, customer_id: int, case_id: int) -> bool:
    """Check if the customer has access to the case."""
    return (
        db.query(CaseCustomer)
        .filter(
            CaseCustomer.customer_id == customer_id, CaseCustomer.case_id == case_id
        )
        .first()
        is not None
    )


def check_lawyer_case_access(db: Session, case_id: int, user: User) -> bool:
    """Check if the lawyer has access to the case."""
    query = db.query(TimelineEvent).filter(TimelineEvent.case_id == case_id)
    # Subquery: does lawyer have mapping for this case?
    lawyer_case_exists = (
        db.query(CaseLawyer)
        .filter(
            CaseLawyer.lawyer_id == user.lawyer.id,
            CaseLawyer.case_id == case_id,
        )
        .exists()
    )

    # Final filter
    query = query.filter(
        or_(
            TimelineEvent.notify_user_id == user.id,
            and_(TimelineEvent.notify_user_id.is_(None), lawyer_case_exists),
        )
    )
    if query.all():
        return True
    return False


def validate_lawyers_and_get_errors(
    db: Session, lawyer_ids: list[str]
) -> tuple[dict, list[str], list[str]]:
    """
    Validate lawyer IDs and return valid IDs with lawyer objects, error list, and invalid encrypted IDs.
    """
    errors: list[str] = []
    decrypted_ids: list[int] = []
    invalid_encrypted_ids: list[str] = []

    # Decrypt IDs and collect errors
    for lawyer_id_str in lawyer_ids:
        decrypted = decrypt_id(lawyer_id_str)

        try:
            if decrypted is None:
                errors.append(f"Invalid expert ID format: {lawyer_id_str}")
                invalid_encrypted_ids.append(lawyer_id_str)
                continue
            lawyer_id = int(decrypted)
            decrypted_ids.append(lawyer_id)
        except (ValueError, TypeError):
            errors.append(f"Invalid expert ID format: {lawyer_id_str}")
            invalid_encrypted_ids.append(lawyer_id_str)

    if not decrypted_ids:
        return {}, errors, invalid_encrypted_ids

    if errors:
        return dict(enumerate(decrypted_ids)), errors, invalid_encrypted_ids

    # Query all valid lawyers with active users in one go
    valid_lawyers = (
        db.query(Lawyer).options(joinedload(Lawyer.accredited_specialisms))
        .join(User, Lawyer.user_id == User.id)
        .filter(Lawyer.id.in_(decrypted_ids), User.status == StatusEnum.ACTIVE, Lawyer.status == LawyerStatusEnum.ACTIVE)
        .all()
    )

    # Create dictionary mapping lawyer_id to lawyer object
    valid_lawyer_dict = {lawyer.id: lawyer for lawyer in valid_lawyers}

    invalid_ids = [lid for lid in decrypted_ids if lid not in valid_lawyer_dict]

    # Encrypt invalid IDs back to encrypted format
    for invalid_id in invalid_ids:
        encrypted_id = encrypt_id(str(invalid_id))
        if encrypted_id is not None:
            invalid_encrypted_ids.append(encrypted_id)

    errors.extend([
        f"Expert with ID {lid} not found or not active" for lid in invalid_encrypted_ids
    ])

    return valid_lawyer_dict, errors, invalid_encrypted_ids


def get_match_lawyer_ids_by_case_id(db: Session, case_id: int) -> set[int]:
    """Return set of lawyer IDs that already have a match for the given case."""
    return {row[0] for row in db.query(Match.lawyer_id).join(Case).filter(Match.case_id == case_id, Case.is_match_confirmed.is_(True)).distinct().all()}


def create_lawyer_matches(
    db: Session,
    case: Case,
    lawyer_dict: dict,
    current_user: User,
) -> bool:
    """
    Create or update lawyer matches in the match table using bulk operations.

    Args:
        db: Database session
        case: The case
        lawyer_ids: List of valid lawyer IDs
        current_user: The navigator user creating the matches

    Returns:
        tuple: (success: bool, created_ids: list[str], updated_ids: list[str])
        created_ids and updated_ids contain encrypted match IDs
    """
    try:
        # from sqlalchemy import func
        now = datetime.now(timezone.utc)
        # now = func.now()
        lawyer_ids = list(lawyer_dict.keys())

        # delete existing matches for the case
        if case.is_match_confirmed == False:
            # delete existing matches for the case
            db.query(Match).filter(Match.case_id == case.id).delete()

        #bulk create new matches
        matches_to_create = []
        for lawyer_id in lawyer_ids:
            matches_to_create.append(Match(
                lawyer_id=lawyer_id,
                case_id=case.id,
                user_id=current_user.id,
                action_date=now,
            ))
        db.bulk_save_objects(matches_to_create)
        case.is_match_confirmed = True  # type: ignore
        case.match_confirmed_at = now  # type: ignore
        db.commit()

        return True
    except Exception:
        db.rollback()
        return False


def parse_lawyer_data(lawyers: list[Lawyer] | None) -> list[LawyerData]:
    """Parse lawyer data."""
    from app.utils.formatters import format_expertises
    from app.utils.formatters import format_accredited_specialisms

    response_data = []
    if lawyers is not None:
        for lawyer in lawyers:
            first_name = (
                lawyer.user.first_name
                if lawyer.user and lawyer.user.first_name
                else None
            )
            last_name = (
                lawyer.user.last_name if lawyer.user and lawyer.user.last_name else None
            )
            email = lawyer.user.email if lawyer.user and lawyer.user.email else None
            phone_number = (
                lawyer.user.phone if lawyer.user and lawyer.user.phone else None
            )

            # Explicitly cast the datetime values to avoid mypy issues
            joined_at_value = (
                cast("datetime", lawyer.joined_at) if lawyer.joined_at else None
            )
            left_at_value = cast("datetime", lawyer.left_at) if lawyer.left_at else None
            created_at_value = (
                cast("datetime", lawyer.created_at) if lawyer.created_at else None
            )
            updated_at_value = (
                cast("datetime", lawyer.updated_at) if lawyer.updated_at else None
            )
            # Get expert types
            expert_types = [et.expert_type for et in lawyer.expert_types]
            expert_types_all = [et.expert_type.value for et in lawyer.expert_types if not et.expert_type.is_other()]
            if hasattr(lawyer, "expert_types_other") and lawyer.expert_types_other:
                expert_types_all.append(lawyer.expert_types_other.capitalize())
            expert_types_all.sort()
            # Get relationship types
            relationship_types = [
                rt.relationship_type for rt in lawyer.relationship_types
            ]
            # Get matter types
            matter_types = [mt.matter_type for mt in lawyer.matter_types]
            # Get accredited specialisms
            accredited_specialisms = lawyer.accredited_specialisms if lawyer.accredited_specialisms else []
            accredited_specialisms_other = _parse_json_field(lawyer.accredited_specialism_other, default=[])
            lawyer_accredited_specialisms = format_accredited_specialisms(accredited_specialisms, accredited_specialisms_other)
            # Get expertises
            expertises = lawyer.expertises if lawyer.expertises else []
            # for expertise in lawyer.expertises:
            #     if not expertise.expertise.is_other():
            #         expertises.append(expertise.expertise.value)
            
            expertises_other = _parse_json_field(lawyer.expertises_other, default={})
            lawyer_expertises = format_expertises(expertises, expertises_other)
            testimonial = lawyer.testimonial if lawyer.testimonial else None

            # if lawyer.expertises_other:
            #     for key, value in lawyer.expertises_other.items():
            #         for expertise in value:
            #             expertises.append(expertise)
            response_data.append(
                LawyerData(
                    lawyer_id=str(lawyer.id) if lawyer.id else None,
                    first_name=str(first_name) if first_name else None,
                    last_name=str(last_name) if last_name else None,
                    email=str(email) if email else None,
                    phone_number=str(phone_number) if phone_number else None,
                    address_line_1=str(lawyer.address_line_1)
                    if lawyer.address_line_1
                    else None,
                    address_line_2=str(lawyer.address_line_2)
                    if lawyer.address_line_2
                    else None,
                    city=str(lawyer.city) if lawyer.city else None,
                    county=str(lawyer.county) if lawyer.county else None,
                    country=str(lawyer.country) if lawyer.country else None,
                    postal_code=str(lawyer.postal_code) if lawyer.postal_code else None,
                    # country=str(lawyer.country) if lawyer.country else None,
                    user_id=str(lawyer.user.id)
                    if lawyer.user and lawyer.user.id
                    else None,
                    # lawyer_type=str(lawyer.lawyer_type) if lawyer.lawyer_type else None,
                    reg_no=str(lawyer.reg_no) if lawyer.reg_no else None,
                    regulator=str(lawyer.regulator.value) if lawyer.regulator else None,
                    joined_at=joined_at_value,
                    left_at=left_at_value,
                    about=str(lawyer.about),
                    photo_urls=generate_photo_urls(lawyer.photo_url),
                    # practice_areas=str(lawyer.practice_areas),
                    # qualifications=str(lawyer.qualifications),
                    linkedin_url=str(lawyer.linkedin_url),
                    lawyer_status=str(lawyer.status.value),
                    created_at=created_at_value,
                    updated_at=updated_at_value,
                    experience=calculate_lawyer_experience(lawyer),
                    hourly_rate=int(lawyer.hourly_rate) if lawyer.hourly_rate is not None else None,
                    charge_first_consultation=int(lawyer.charge_first_consultation) if lawyer.charge_first_consultation is not None else None,
                    conflict_level_disinclination=lawyer.conflict_level_disinclination,
                    expert_types=expert_types,
                    expert_types_all=expert_types_all,
                    relationship_types=relationship_types,
                    matter_types=matter_types,
                    expertises_all=lawyer_expertises,
                    accreditations=lawyer_accredited_specialisms,
                    testimonial=testimonial,
                    sra_number=lawyer.sra_number,
                    bar_number=lawyer.bar_number,
                    lawfirms=[LawFirmData(id=str(lawfirm.law_firm.id), name=lawfirm.law_firm.name) for lawfirm in lawyer.lawyer_law_firms] if lawyer.lawyer_law_firms else None,
                )
            )
    return response_data


def get_matches_by_case_id(
    db: Session, request_data: GetMatchedLawyersRequest
) -> list[LawyerData]:
    """Get matches for a case."""

    lawyers = (
        db.query(Lawyer)
        .join(Match, Lawyer.id == Match.lawyer_id)
        .join(User, Lawyer.user_id == User.id)
        .filter(Match.case_id == int(request_data.case_id))
        .filter(Lawyer.status == LawyerStatusEnum.ACTIVE)
        .filter(User.status == StatusEnum.ACTIVE)
        .all()
    )

    return parse_lawyer_data(lawyers)


def get_encrypted_ids(ids: list[str]) -> list[str]:
    """Get encrypted IDs."""
    if ids:
        encrypted_ids: list[str] = []
        for id in ids:
            encrypted_id = encrypt_id(str(id))
            if encrypted_id is not None:
                encrypted_ids.append(encrypted_id)
        return encrypted_ids
    return []


def update_lawyer_interest_confirmed(
    db: Session,
    case: Case,
    lawyer_dict: dict,
    current_user: User,
) -> tuple[bool, str]:
    """
    Update lawyer interest confirmed in the match table using bulk operations.

    Args:
        db: Database session
        case_id: The case ID
        lawyer_ids: List of valid lawyer IDs
        current_user: The navigator user updating the matches

    Returns:
        tuple: (success: bool, updated_ids: list[str])
        updated_ids contain encrypted match IDs
    """
    try:
        now = datetime.now(timezone.utc)
        lawyer_ids = list(lawyer_dict.keys())
        # Get existing matches in one query
        existing_matches = (
            db.query(Match)
            .filter(
                Match.lawyer_id.in_(lawyer_ids),
                Match.case_id == case.id,
                Match.status == MatchStatusEnum.INTERESTED,
            )
            .all()
        )

        existing_match_dict: dict[tuple[int, int], Match] = {
            (int(match.lawyer_id), int(match.case_id)): match
            for match in existing_matches
        }

        if len(lawyer_ids) != len(existing_matches):
            existing_lawyer_ids = list(set(key[0] for key in existing_match_dict.keys()))
            invalid_lawyer_ids = [lid for lid in lawyer_ids if lid not in existing_lawyer_ids]
            invalid_encrypted_lawyer_ids = get_encrypted_ids(invalid_lawyer_ids)
            message = "Invalid interested expert ID(s) : "
            if invalid_encrypted_lawyer_ids:
                message = message + ", ".join(invalid_encrypted_lawyer_ids)
            return False, message

        # Extract lawyer IDs from existing matches
        updated_law_ids = [match_key[0] for match_key in existing_match_dict.keys()]

        # Compare lawyer_ids with updated_law_ids and collect invalid IDs
        invalid_lawyer_ids = [lid for lid in lawyer_ids if lid not in updated_law_ids]

        if invalid_lawyer_ids:
            return False, "Invalid expert IDs found"

        # Prepare lists for bulk operations
        matches_to_update = []

        for lawyer_id in lawyer_ids:
            lawyer = lawyer_dict.get(lawyer_id)
            if not lawyer:
                continue

            match_key: tuple[int, int] = (lawyer_id, int(case.id))
            existing_match = existing_match_dict.get(match_key)
            if existing_match:
                # Update existing match
                existing_match.user_id = current_user.id
                existing_match.is_confirmed = True  # type: ignore
                existing_match.confirmed_by = current_user.id
                existing_match.confirmed_date = now  # type: ignore
                existing_match.updated_at = now  # type: ignore
                matches_to_update.append(existing_match)
        # Bulk update existing matches
        if matches_to_update:
            db.bulk_update_mappings(
                Match.__mapper__,
                [
                    {
                        "id": match.id,
                        "user_id": match.user_id,
                        "is_confirmed": match.is_confirmed,
                        "confirmed_by": match.confirmed_by,
                        "confirmed_date": match.confirmed_date,
                        "updated_at": match.updated_at,
                    }
                    for match in matches_to_update
                ],
            )

        case.is_profile_card_sent = True  # type: ignore
        # Commit all changes
        db.commit()

        return True, "Expert interest confirmed successfully"
    except Exception:
        db.rollback()
        return False, "Failed to update records"


def save_timeline_event(
    db: Session,
    case_id: int,
    timeline_type: TimelineType,
    meta_data: dict,
    action_user_id: int | None = None,
    notify_user_id: int | None = None,
    timeline_event: TimelineEvent | None = None,
) -> TimelineEvent:
    """
    Save a timeline event to the database.

    Args:
        db: Database session
        case_id: ID of the case
        timeline_type: Timeline type object
        meta_data: JSON data to store in meta_data field
    Returns:
        TimelineEvent: The created timeline event
    """
    if timeline_event is not None:
        timeline_event.meta_data = json.dumps(meta_data) if meta_data else None  # type: ignore
        timeline_event.action_user_id = action_user_id  # type: ignore
        timeline_event.notify_user_id = notify_user_id  # type: ignore
    else:
        # Create timeline event
        timeline_event = TimelineEvent(
            case_id=case_id,
            timeline_type_id=timeline_type.id,
            action_user_id=action_user_id,
            notify_user_id=notify_user_id,
            meta_data=json.dumps(meta_data) if meta_data else None,
        )
        db.add(timeline_event)

    db.commit()
    db.refresh(timeline_event)

    # Explanation:
    # The send_socket_message function is now called in a background thread using threading.Thread.
    # This allows save_timeline_event to return immediately without waiting for send_socket_message to finish.
    # Any exceptions in the background thread are logged for debugging and monitoring.
    import threading

    # Store the timeline_event_id and component_path to pass to the background thread
    # We pass the ID instead of the object to avoid DetachedInstanceError
    timeline_event_id = timeline_event.id
    component_path = f"timeline/{timeline_type.role_code.lower()}/{timeline_type.type_name}/v{timeline_type.version}"
    
    case_id_ = case_id
    timeline_event_id_ = timeline_event.id
    role_code_ = timeline_type.role_code
    component_type_ = timeline_type.type_name


    def _send_socket_message_async() -> None:
        from app.db.database import SessionLocal

        db_async = SessionLocal()
        try:
            web_socket_message = WebSocketMessage(case_id=case_id_, timeline_event_id=timeline_event_id_, role_code=role_code_, component_type=component_type_, component_path=component_path, action_user_id=action_user_id, notify_user_id=notify_user_id)
            send_timeline_socket_messages(db_async, [web_socket_message])
            # Re-query the timeline_event with the new session and eagerly load relationships
            # timeline_event_fresh = (
            #     db.query(TimelineEvent)
            #     .options(
            #         joinedload(TimelineEvent.timeline_type),
            #         joinedload(TimelineEvent.action_user)
            #     )
            #     .filter(TimelineEvent.id == timeline_event_id)
            #     .first()
            # )
            
            # if timeline_event_fresh:
            #     send_timeline_socket_message(db, [(timeline_event_fresh, component_path)])
            # else:
            #     logger.warning(f"Timeline event {timeline_event_id} not found for socket message")
        except Exception as exc:
            logger.error("Error sending socket message asynchronously: %s", exc, exc_info=True)
        finally:
            db_async.close()

    threading.Thread(target=_send_socket_message_async, daemon=True).start()

    return timeline_event


def save_lawyers_match(
    db: Session,
    case_id: int,
    lawyer_ids: list[int],
) -> bool:
    """Bulk create lawyers to match table."""

    try:
        matches_to_create = []
        existing_matches = db.query(Match).filter(Match.lawyer_id.in_(lawyer_ids), Match.case_id == case_id).all()
        existing_match_lawyer_ids = [match.lawyer_id for match in existing_matches]
        new_lawyer_ids = [lid for lid in lawyer_ids if lid not in existing_match_lawyer_ids]
        for lawyer_id in new_lawyer_ids:
            matches_to_create.append(Match(lawyer_id=lawyer_id, case_id=case_id))
        db.bulk_save_objects(matches_to_create)
        db.commit()
        return True
    except Exception:
        db.rollback()
        return False


def get_match_confirmed_lawyers_service(
    db: Session, case_id: int
) -> list[ConfirmedLawyerData]:
    """
    Get confirmed matched lawyers for a case.

    Args:
        db: Database session
        case_id: The case ID

    Returns:
        list[ConfirmedLawyerData]: List of confirmed lawyer data
    """
    from app.utils.formatters import format_expertises
    from app.utils.formatters import format_accredited_specialisms
    # Query confirmed matches with lawyer details
    confirmed_lawyers = (
        db.query(Lawyer)
            .options(
            joinedload(Lawyer.expert_types)
            )
            .join(Match, Lawyer.id == Match.lawyer_id)
            .join(User, Lawyer.user_id == User.id)
        .filter(
            Match.case_id == case_id,
            Match.is_confirmed,
            Lawyer.status == LawyerStatusEnum.ACTIVE,
            User.status == StatusEnum.ACTIVE,
        )
        .all()
    )

    confirmed_lawyer_data = []
    for lawyer in confirmed_lawyers:
        # Get expert types
        # expert_types = (
        #     [et.expert_type.value for et in lawyer.expert_types]
        #     if lawyer.expert_types
        #     else []
        # )

        expertises = lawyer.expertises if lawyer.expertises else []
        expertises_other = _parse_json_field(lawyer.expertises_other, default={})
        lawyer_expertises = format_expertises(expertises, expertises_other)
        accredited_specialisms = lawyer.accredited_specialisms if lawyer.accredited_specialisms else []
        accredited_specialisms_other = _parse_json_field(lawyer.accredited_specialism_other, default=[])
        lawyer_accredited_specialisms = format_accredited_specialisms(accredited_specialisms, accredited_specialisms_other)

        # Get specializations (accredited_specialisations)
        # specializations = None
        # if lawyer.accredited_specialisations:
        #     specializations = lawyer.accredited_specialisations

        # Build location string
        location_parts = []
        if lawyer.city:
            location_parts.append(str(lawyer.city))
        if lawyer.county:
            location_parts.append(str(lawyer.county))
        if lawyer.country:
            location_parts.append(str(lawyer.country))
        location = ", ".join(location_parts) if location_parts else None

        # Get lawyer name
        first_name = (
            lawyer.user.first_name if lawyer.user and lawyer.user.first_name else ""
        )
        last_name = (
            lawyer.user.last_name if lawyer.user and lawyer.user.last_name else ""
        )
        lawyer_name = f"{first_name} {last_name}".strip()

        confirmed_lawyer_data.append(
            ConfirmedLawyerData(
                lawyer_id=str(lawyer.id),
                lawyer_name=lawyer_name,
                lawyer_photo_urls=generate_photo_urls(lawyer.photo_url),
                lawyer_experience=calculate_lawyer_experience(lawyer),
                # lawyer_expert_type=expert_types,
                lawyer_expertises=lawyer_expertises,
                lawyer_accreditations=lawyer_accredited_specialisms,
                lawyer_about=str(lawyer.about) if lawyer.about else None,
                lawyer_location=location,
                # lawyer_specialization=str(specializations) if specializations else None,
            )
        )

    return confirmed_lawyer_data

        # send_timeline_socket_message(db, [(case_id_, timeline_event_id_, role_code_, component_type_, component_path)])
def send_timeline_socket_messages(
    db: Session,
    event_data_list: list[WebSocketMessage],
) -> bool:
    """Send socket message to user - OPTIMIZED VERSION."""
    try:
        timeline_event_ids = []
        if len(event_data_list) > 0:
            timeline_event_ids = [web_socket_message.timeline_event_id for web_socket_message in event_data_list]
        # OPTIMIZATION 1: Only fetch the single timeline event, not all 100 events
        # This reduces database query time significantly
        event_data, _ , _ = get_timeline_events_by_case_id(
            db, 0, 1, 1, "desc", "created_at", None, None, None, timeline_event_ids, None
        )
        if event_data:
            event_data = [event.model_dump() for event in event_data]
        else:
            return True

        
        # OPTIMIZATION 2: Group events by role_code for efficient batch processing
        # Group events to minimize database queries
        events_by_role: dict[str, list[WebSocketMessage]] = {}
        for ws_msg in event_data_list:
            role = ws_msg.role_code
            if role not in events_by_role:
                events_by_role[role] = []
            events_by_role[role].append(ws_msg)
        # Query connections once per role with optimized filtering
        all_connections_by_role: dict[str, list[tuple[str, int | None]]] = {}
        
        for role_code, role_events in events_by_role.items():
            # Collect all case_ids for this role
            case_ids = list(set(event.case_id for event in role_events))
            
            # Base query - always filter by active connections
            base_query = db.query(WebSocketConnection).filter(
                WebSocketConnection.disconnected_at.is_(None)
            )
            
            if role_code == UserRoleEnum.NAVIGATOR.display_name:
                # NAVIGATOR: Simple role-based filtering
                connections = (
                    base_query.filter(WebSocketConnection.role_code == role_code)
                    .with_entities(
                        WebSocketConnection.connection_id,
                        WebSocketConnection.user_id
                    )
                    .all()
                )
                all_connections_by_role[role_code] = [(conn_id, user_id) for conn_id, user_id in connections]
                
            elif role_code == UserRoleEnum.LAWYER.display_name:
                # LAWYER: Complex filtering with notify_user_id, case_lawyer, and matches
                from app.db.models.case import Case
                from app.db.models.case_lawyer import CaseLawyer
                from app.db.models.lawyer import Lawyer
                from app.db.models.match import Match
                
                # Collect all notify_user_ids from events
                notify_user_ids = set()
                events_with_notify = []
                events_without_notify = []
                
                for event in role_events:
                    if event.notify_user_id is not None:
                        notify_user_ids.add(event.notify_user_id)
                        events_with_notify.append(event)
                    else:
                        events_without_notify.append(event)
                
                # Get all relevant lawyer user_ids in a single query
                all_lawyer_user_ids = set()
                
                # For events without notify_user_id, get lawyers from case_lawyer and matches
                if events_without_notify:
                    case_ids_no_notify = list(set(e.case_id for e in events_without_notify))
                    
                    # Query case_lawyer assignments
                    case_lawyer_user_ids = (
                        db.query(Lawyer.user_id)
                        .join(CaseLawyer, CaseLawyer.lawyer_id == Lawyer.id)
                        .filter(
                            CaseLawyer.case_id.in_(case_ids_no_notify),
                            Lawyer.user_id.isnot(None)
                        )
                        .distinct()
                        .all()
                    )
                    all_lawyer_user_ids.update(uid for (uid,) in case_lawyer_user_ids)
                    
                    # Query confirmed matches
                    matched_user_ids = (
                        db.query(Lawyer.user_id)
                        .join(Match, Match.lawyer_id == Lawyer.id)
                        .join(Case, Match.case_id == Case.id)
                        .filter(
                            Match.case_id.in_(case_ids_no_notify),
                            Case.is_match_confirmed.is_(True),
                            Lawyer.user_id.isnot(None),
                            Case.is_lawyer_assigned.is_(False)
                        )
                        .distinct()
                        .all()
                    )
                    all_lawyer_user_ids.update(uid for (uid,) in matched_user_ids)
                
                # Combine with notify_user_ids
                all_lawyer_user_ids.update(notify_user_ids)
                
                if all_lawyer_user_ids:
                    connections = (
                        base_query.filter(WebSocketConnection.user_id.in_(all_lawyer_user_ids))
                        .with_entities(
                            WebSocketConnection.connection_id,
                            WebSocketConnection.user_id
                        )
                        .all()
                    )
                    all_connections_by_role[role_code] = [(conn_id, user_id) for conn_id, user_id in connections]
                else:
                    all_connections_by_role[role_code] = []
                    
            elif role_code == UserRoleEnum.CUSTOMER.display_name:
                # CUSTOMER: Join with case_customer for all case_ids at once
                from app.db.models.case_customer import CaseCustomer
                from app.db.models.customer import Customer
                
                connections = (
                    base_query.join(
                        Customer,
                        Customer.user_id == WebSocketConnection.user_id
                    )
                    .join(
                        CaseCustomer,
                        CaseCustomer.customer_id == Customer.id
                    )
                    .filter(CaseCustomer.case_id.in_(case_ids))
                    .with_entities(
                        WebSocketConnection.connection_id,
                        WebSocketConnection.user_id
                    )
                    .distinct()
                    .all()
                )
                all_connections_by_role[role_code] = [(conn_id, user_id) for conn_id, user_id in connections]

        # OPTIMIZATION 3: Build event data lookup for fast access
        # Create mapping of timeline_event_id to event data
        event_data_by_id: dict[str, dict[str, object]] = {}
        from app.utils.encryption import encrypt_id
        if event_data:
            for event in event_data:
                event_id = event.get("id")
                if event_id is None:
                    continue
                event_id_str = str(event_id)
                event_data_by_id[event_id_str] = event
                encrypted_event_id = encrypt_id(event_id_str)
                if encrypted_event_id:
                    event_data_by_id[encrypted_event_id] = event
        # Early return if no event data
        if not event_data_by_id:
            logger.info("No event data found for the requested timeline events")
            return True 
        
        # Early return if no connections for any role
        if not any(all_connections_by_role.values()):
            logger.info("No active connections found for any role")
            return True
        
        # OPTIMIZATION 4: Build messages for all events efficiently
        all_messages = []
        
        for role_code, role_events in events_by_role.items():
            # Get connections for this role
            role_connections = all_connections_by_role.get(role_code, [])
            
            if not role_connections:
                logger.info(f"No connections for role {role_code}, skipping")
                continue
            # Process each event for this role
            for ws_msg in role_events:
                # Get event data for this timeline event
                event = event_data_by_id.get(str(ws_msg.timeline_event_id))
                if event is None:
                    encrypted_lookup = encrypt_id(str(ws_msg.timeline_event_id))
                    event = event_data_by_id.get(encrypted_lookup) if encrypted_lookup else None
                if not event:
                    logger.info(
                        "Event data not found for timeline_event_id %s",
                        ws_msg.timeline_event_id,
                    )
                    continue
                
                # Format message with meta_data
                meta_data = event.get("meta_data", {})
                if isinstance(meta_data, str):
                    try:
                        meta_data = json.loads(meta_data)
                    except (json.JSONDecodeError, TypeError):
                        meta_data = {}
                
                if ws_msg.is_disable_event:
                    event_message = ""
                else:
                    formatter = SafeFormatter(meta_data)
                    event_message = ComponentEnum.get_component_message(ws_msg.component_type, role_code).format_map(formatter)
                
                # Filter connections based on notify_user_id if present
                target_connections = role_connections
                if ws_msg.notify_user_id is not None and role_code == UserRoleEnum.LAWYER.display_name:
                    # For LAWYER role with notify_user_id, only send to that specific user
                    target_connections = [
                        (conn_id, user_id) 
                        for conn_id, user_id in role_connections 
                        if user_id == ws_msg.notify_user_id
                    ]
                
                # Build messages for this event to all relevant connections
                for conn_id, user_id in target_connections:
                    all_messages.append({
                        "message": {
                            "data": event,
                            "message_type": "success",
                            "message": event_message,
                            "component": ws_msg.component_path
                        },
                        "connection_id": conn_id
                    })
        
        # Early return if no messages to send
        if not all_messages:
            logger.info("No messages to send after filtering")
            return True
        
        # OPTIMIZATION 5: Build payload with all messages
        payload = {
            "requestContext": {
                "routeKey": "sendMessage",
                "eventType": "MESSAGE",
                "stage": "staging",
            },
            "body": json.dumps({
                "action": "sendMessage",
                "messages": all_messages,
            }),
            "isBase64Encoded": False,
        }
        
        # Check if running in local mode (use environment variable)
        # import os
        # use_local_websocket = True  # os.getenv("USE_LOCAL_WEBSOCKET", "false").lower() == "true"
        
        # if use_local_websocket:
        #     # Use local WebSocket handler (for development/testing)
        #     try:
        #         from app.core.websocket_local import invoke_local_websocket
                
        #         result = invoke_local_websocket(payload)
        #         logger.info(
        #             f"Batch: Local WebSocket sent {len(all_messages)} messages for "
        #             f"{len(event_data_list)} events across {len(events_by_role)} roles: "
        #             f"{result.get('body', 'unknown')}"
        #         )
        #         return result.get("statusCode") == 200
        #     except Exception as local_err:
        #         logger.error(f"Error sending batch local WebSocket messages: {local_err}", exc_info=True)
        #         return False
        # else:
        # OPTIMIZATION 6: Use cached Lambda client and async invocation
        lambda_client = get_lambda_client()
        lambda_client.invoke(
            FunctionName="socket_lambda",
            InvocationType="Event",  # Async - don't wait for response
            Payload=json.dumps(payload, default=str).encode("utf-8"),
        )
        logger.info(
            f"Batch: Socket messages queued - {len(all_messages)} messages for "
            f"{len(event_data_list)} events across {len(events_by_role)} roles "
            f"(single Lambda invocation)"
        )
        return True

    except Exception as e:
        logger.error("Error sending timeline socket message: %s", e, exc_info=True)
        return False

def get_timeline_event_from_map(db: Session, timeline_type_name: str, related_id: str, timeline_event_id: int | None = None) -> List[TimelineEvent]:
    """
   Fetch timeline event(s) by type and related ID, optionally filtering by a specific event ID.
   Handles both exact match and prefix match (e.g., caseid or caseid_lawyerid).
    """
    query = db.query(TimelineEvent).join(
        TimelineMap, TimelineEvent.id == TimelineMap.timeline_event_id
    ).options(joinedload(TimelineEvent.timeline_type)
    ).filter(
        TimelineMap.timeline_type == timeline_type_name,
        TimelineMap.related_id == str(related_id)
    )

    if timeline_event_id is not None:
        query = query.filter(TimelineEvent.id == timeline_event_id)

    return query.all()

def save_timeline_map(db: Session, timeline_event_id: int, timeline_type_name: str, related_id: str) -> TimelineMap:
    """Save timeline map."""

    existing_timeline_map = db.query(TimelineMap).filter(TimelineMap.timeline_event_id == timeline_event_id, TimelineMap.timeline_type == timeline_type_name, TimelineMap.related_id == str(related_id)).first()
    if existing_timeline_map:
        return existing_timeline_map
    
    timeline_map = TimelineMap(timeline_event_id=timeline_event_id, timeline_type=timeline_type_name, related_id=str(related_id))
    db.add(timeline_map)
    db.commit()
    db.refresh(timeline_map)
    return timeline_map


def disable_timeline_action_buttons(
    db: Session,
    component_buttons: dict[str, list[str]],
    related_id: str,
) -> bool:
    """
    Disable specific action buttons for multiple timeline event components.

    Args:
        db: Database session
        component_buttons: Dictionary where keys are timeline/component type names
                          (e.g., "your_matched_expert") and values are lists of
                          button names to disable for that component
                          (e.g., {"your_matched_expert": ["engage_with"], "case_profile": ["talk_to_nn"]})
        related_id: Related entity ID (e.g., case_id or case_id_any_related_id)

    Returns:
        bool: True if at least one button was disabled successfully, False otherwise
    """
    success = False
    socket_messages: list[WebSocketMessage] = []
    try:
        for type_name, button_names in component_buttons.items():
            # Fetch the timeline event using timeline_map
            timeline_events = get_timeline_event_from_map(db, type_name, related_id)
            for timeline_event in timeline_events:
                if timeline_event and timeline_event.meta_data:
                    # Parse the meta_data JSON
                    meta_data = json.loads(timeline_event.meta_data)
                    if "action_buttons" in meta_data:
                        updated = False
                        for button_name in button_names:
                            if button_name in meta_data["action_buttons"]:
                                meta_data["action_buttons"][button_name] = False
                                updated = True
                        if updated:
                            # Save updated meta_data back to timeline event
                            timeline_event.meta_data = json.dumps(meta_data)  # type: ignore
                            success = True

                            component_path = (
                                f"timeline/{timeline_event.timeline_type.role_code.lower()}/"
                                f"{timeline_event.timeline_type.type_name}/v{timeline_event.timeline_type.version}"
                            )
                            socket_messages.append(
                                WebSocketMessage(
                                    case_id=timeline_event.case_id,
                                    timeline_event_id=timeline_event.id,
                                    role_code=timeline_event.timeline_type.role_code,
                                    component_type=timeline_event.timeline_type.type_name,
                                    component_path=component_path,
                                    action_user_id=timeline_event.action_user_id,
                                    notify_user_id=timeline_event.notify_user_id,
                                    is_disable_event=True
                                )
                            )

        if success:
            db.commit()

            # Send socket messages asynchronously for all updated events
            import threading

            def _send_multiple_socket_messages_async() -> None:
                from app.db.database import SessionLocal

                db_async = SessionLocal()
                try:
                    send_timeline_socket_messages(db_async, socket_messages)
                except Exception as exc:
                    logger.error(
                        "Error sending multiple socket messages asynchronously: %s",
                        exc,
                        exc_info=True,
                    )
                finally:
                    db_async.close()

            threading.Thread(target=_send_multiple_socket_messages_async, daemon=True).start()

        return success
    except Exception as e:
        logger.error("Error in disable_timeline_action_buttons: %s", e, exc_info=True)
        db.rollback()
        return False


def update_timeline_event(db: Session, related_id: str, data: dict) -> bool:
    """Update the timeline event metadata.
    Args:
        db: Database session
        related_id: Related entity ID (e.g., case_id or case_id_any_related_id)
        data: Dictionary of data to update in the timeline event metadata
        e.g. data = {"component_type1": {"key1": "value1", "key2": "value2"}}

    Returns:
        bool: True if the timeline event metadata was updated successfully, False otherwise
    """
    try:
        if not data:
            raise ValueError("Data is required")
        
        success = False
        socket_messages: list[WebSocketMessage] = []
        for component_type, component_data in data.items():

            timeline_events = get_timeline_event_from_map(db, component_type, related_id)
            for timeline_event in timeline_events:            
                # Load existing metadata
                meta_data = json.loads(timeline_event.meta_data) if timeline_event.meta_data else {}
                
                #check the key exists in the meta_data
                updated = False
                for key, value in component_data.items():
                    if key in meta_data:
                        meta_data[key] = value
                        updated = True
                
                if updated:
                    timeline_event.meta_data = json.dumps(meta_data)
                    success = True

                    component_path = (
                        f"timeline/{timeline_event.timeline_type.role_code.lower()}/"
                        f"{timeline_event.timeline_type.type_name}/v{timeline_event.timeline_type.version}"
                    )
                    socket_messages.append(
                        WebSocketMessage(
                            case_id=timeline_event.case_id,
                            timeline_event_id=timeline_event.id,
                            role_code=timeline_event.timeline_type.role_code,
                            component_type=timeline_event.timeline_type.type_name,
                            component_path=component_path,
                            action_user_id=timeline_event.action_user_id,
                            notify_user_id=timeline_event.notify_user_id,
                            is_disable_event=True
                        )
                    )

        if success:
            db.commit()
            # Send socket messages asynchronously for all updated events
            import threading

            def _send_multiple_socket_messages_async() -> None:
                from app.db.database import SessionLocal

                db_async = SessionLocal()
                try:
                    send_timeline_socket_messages(db_async, socket_messages)
                except Exception as exc:
                    logger.error(
                        "Error sending multiple socket messages asynchronously: %s",
                        exc,
                        exc_info=True,
                    )
                finally:
                    db_async.close()

            threading.Thread(target=_send_multiple_socket_messages_async, daemon=True).start()
        return success
    except Exception as e:
        logger.error("Error in update_timeline_event: %s", e, exc_info=True)
        db.rollback()
        return False

def update_timeline_metadata(db: Session, related_id: int, timeline_type: str, meta_data: dict) -> TimelineEvent | None:
    """Update timeline event metadata."""
    timeline_events = get_timeline_event_from_map(db, timeline_type, related_id)
    if timeline_events is None:
        raise ValueError("Timeline event not found")
    # Get the first timeline event from the list
    timeline_event = timeline_events[0]
    timeline_event.meta_data = json.dumps(meta_data) if meta_data else None
    db.commit()
    return timeline_event


def get_timeline_event(db: Session, case_id: int, component_enum: ComponentEnum) -> TimelineEvent | None:
    """Get timeline event by case ID and component enum."""
    timeline_event = db.query(TimelineEvent).join(
        TimelineType, TimelineEvent.timeline_type_id == TimelineType.id
    ).options(joinedload(TimelineEvent.timeline_type)
    ).filter(
        TimelineType.type_name == component_enum,
        TimelineEvent.case_id == case_id
    ).first()
    if timeline_event is None:
        return None
    return timeline_event
   
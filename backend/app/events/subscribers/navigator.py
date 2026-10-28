"""
Navigator Event Handlers

This module contains event handler functions for navigator-related timeline card notifications.
All event handlers are decorated with @event and automatically registered.
"""

import logging
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.db.services.general import get_timeline_type
from app.enums.component import ComponentEnum
from app.enums.events import EventType
from app.enums.user_role import UserRoleEnum
from app.events.dispatcher import event
from app.core.email import email_service
from app.utils.formatters import format_case_number
from app.db.services.general import get_all_navigator_emails, get_case_details_url
from app.schemas.v1.event import Event, EventResponseData
from app.db.services.timeline_event import save_timeline_event
from app.db.services.timeline_event import get_timeline_event_from_map, save_timeline_map
from app.utils.helpers import get_template_json, replace_placeholders
from app.utils.validators import validate_event_payload
from app.websocket.manager import WebSocketManager
from app.utils.encryption import encrypt_id

logger = logging.getLogger(__name__)

_UK_TZ = ZoneInfo("Europe/London")


def _format_uk_call_window(start_time: object, end_time: object) -> tuple[str, str]:
    """Convert UTC ISO timestamps to a UK date and a labelled time range.

    Europe/London is GMT in winter and BST in summer, so the label follows the date.
    e.g. '2026-09-30T09:00:00.000Z' -> ('30-09-2026', '10:00 AM - 10:15 AM BST')
    """
    start_dt = datetime.fromisoformat(str(start_time).replace("Z", "+00:00")).astimezone(_UK_TZ)
    end_dt = datetime.fromisoformat(str(end_time).replace("Z", "+00:00")).astimezone(_UK_TZ)

    def _format_time(dt: datetime) -> str:
        return dt.strftime("%I:%M %p").lstrip("0")

    tz_label = start_dt.tzname() or "GMT"
    call_date = start_dt.strftime("%d-%m-%Y")
    call_time = f"{_format_time(start_dt)} - {_format_time(end_dt)} {tz_label}"
    return call_date, call_time


@event(EventType.COMPLETE_ONBOARD_ASSESSMENT_NN_CARD)  # type: ignore
async def handle_complete_onboard_assessment_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle complete onboard assessment navigator card event: Generate card data and save to timeline_event table.

    Required payload:
    {
        "case_id": "1",
        "customer_name": "John Doe",
        "case_number": "CASE-001",
        "timestamp": "2021-01-01T00:00:00Z"
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "case_number", "timestamp", "customer_name"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Complete Onboard Assessment Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Complete Onboard Assessment Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        customer_name = payload["customer_name"]
        role_code = UserRoleEnum.NAVIGATOR.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Complete Onboard Assessment Navigator Card event: Invalid case ID format") from e

        template, last_version = get_template_json(
            str(ComponentEnum.COMPLETE_ONBOARD_ASSESSMENT_NN_CARD.value),
            str(role_code),
            "timeline"
        )

        timeline_type = get_timeline_type(
            db,
            ComponentEnum.COMPLETE_ONBOARD_ASSESSMENT_NN_CARD.value,
            role_code,
            last_version
        )
        if timeline_type is None:
            raise ValueError("Complete Onboard Assessment Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Prepare placeholder values
        placeholder_values = {
            "action_by": "",
            "case_number": case_number,
            "timestamp": timestamp,
            "customer_name": customer_name,
            "action_buttons": {
                "mark_onboarding_completed": True
            }
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(f"Complete Onboard Assessment Navigator Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Complete Onboard Assessment Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        timeline_event = save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data
        )
        timeline = get_timeline_event_from_map(db, str(timeline_type.type_name), int(case_id), int(timeline_event.id))
        # Save timeline_map
        if not timeline:
            save_timeline_map(db, int(timeline_event.id), str(timeline_type.type_name), int(case_id))


        return EventResponseData(
            success=True,
            message="Complete-onboard-assessment-navigator-card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(f"Complete Onboard Assessment Navigator Card event: Error in handle_complete_onboard_assessment_nn_card: {e}")
        raise


@event(EventType.AI_SUMMARY_FAILED_NN_EMAIL)  # type: ignore
async def handle_ai_summary_failed_nn_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle AI Summary Failed Navigator Email event: Generate email data and send to navigator.
    Example payload:
    {
        "case": <Case object>
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case = payload.get("case")
        # Validate that required objects are not None
        if case is None:
            raise ValueError("Case not found in payload")  # noqa: TRY301

        case_url = get_case_details_url(case.id)

        case_number = format_case_number(case.case_no)
        # Get all navigator emails
        navigators = get_all_navigator_emails(db)

        if not navigators:
            logger.warning("No navigators found")
            return EventResponseData(
                success=False,
                message="No navigators found",
                data=[],
            )

        response_list = []
        # Prepare list of navigator emails
        navigator_emails = [str(navigator.get("navigator_email")) for navigator in navigators if navigator.get("navigator_email") is not None]

        if navigator_emails:
            response = await email_service.send_email(
                bcc=navigator_emails,
                template=email_service.EmailTemplate.AI_SUMMARY_FAILED_NAVIGATOR_NOTIFICATION,
                context={
                    "case_number": case_number,
                    "case_url": case_url,
                    "navigator_name": "Navigator",
                    "header_subtitle": "AI Summary Generation Failed",
                },
            )

            response_list.append({
                "navigator_email": navigator_emails,
                "navigator_name": "Navigator",
                "message_id": response.message_id,
            })

        return EventResponseData(
            should_display=False,
            success=True,
            message="AI summary failed navigator notification email sent successfully to navigators.",
            data=response_list,
        )

    except Exception as e:
        logger.exception(f"Error in handle_ai_summary_failed_nn_email: {e}")
        raise


@event(EventType.EXPERT_NOT_INTERESTED)  # type: ignore
async def handle_expert_not_interested(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle expert not interested event:
    """
    from app.utils.constants import LAWYER_INTEREST_DEADLINE_HOURS
    from app.db.services.case import get_not_interested_cases
    try:
        payload = event.payload
        # required_keys = [
        #     "case",
        # ]
        # validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        # if not validation["status"]:
        #     logger.error(
        #         f"Payload validation failed for {event.event_type.value}: {validation}"
        #     )
        #     raise ValueError("Required keys not found in payload")  # noqa: TRY301

        lawyer_interest_deadline_hours = LAWYER_INTEREST_DEADLINE_HOURS
        payload["lawyer_interest_deadline_hours"] = lawyer_interest_deadline_hours
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload["cases_found"] = False

        cases = get_not_interested_cases(db, lawyer_interest_deadline_hours)
        case_data = []
        if len(cases) > 0:
            from app.services.upload_service import UploadService
            from app.enums.file_upload import ImageSize
            from app.utils.encryption import encrypt_id
            upload_service = UploadService()
            for case in cases:
                data = {
                        "case": case,
                    }
                case.is_no_interest_notified = True
                data["lawyers"] = []
                for match in case.matches:
                    photo_url = None
                    if match.lawyer.photo_url is not None:
                        photo_url = upload_service.get_image_url(match.lawyer.photo_url, ImageSize.THUMBNAIL)
                    lawyer = {
                        "id": encrypt_id(match.lawyer.id),
                        "name": match.lawyer.user.first_name + " " + match.lawyer.user.last_name,
                        "photo_url": photo_url,
                    }
                    data["lawyers"].append(lawyer)

                case_data.append(data)
            db.commit()
            payload["cases"] = case_data
            payload["cases_found"] = True
            return EventResponseData(
                success=True,
                message="Expert not interested event handled successfully",
                data=payload,
            )
        else:
            logger.warning("No cases found for expert_not_interested")
            return EventResponseData(
                success=True,
                message="No cases found",
                data=payload,
            )
    except Exception as e:
        logger.exception(f"Error in handle_expert_not_interested: {e}")
        raise


@event(EventType.EMAIL_CTA_CLICKED)  # type: ignore
async def handle_email_cta_clicked(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle email cta clicked event:
    """
    from app.db.services.case import get_case_by_id
    from app.db.services.general import get_case_customer_user

    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "timestamp",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        timestamp = payload["timestamp"]
        role_code = UserRoleEnum.NAVIGATOR.value

        # Fetch case
        case = get_case_by_id(db, case_id)
        if case is None:
            raise ValueError("Case not found")  # noqa: TRY301

        case_number = format_case_number(case.case_no)
        payload["case_number"] = case_number

        # Fetch customer user
        customer_user = get_case_customer_user(db, case_id)
        if customer_user is None:
            raise ValueError("Customer not found")  # noqa: TRY301
        
        first_name = customer_user.first_name if customer_user.first_name else ""
        last_name = customer_user.last_name if customer_user.last_name else ""
        customer_name = f"{first_name} {last_name}".strip()
        payload["customer_name"] = customer_name

        template, last_version = get_template_json(
            str(ComponentEnum.EMAIL_CTA_CLICKED.value), str(role_code), "timeline"
        )
        timeline_type = get_timeline_type(
            db, ComponentEnum.EMAIL_CTA_CLICKED.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Email CTA Clicked event: Timeline type not found")  # noqa: TRY301

        placeholder_values = {
            "customer_name": customer_name,
            "timestamp": timestamp,
        }
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)
        if errors:
            logger.error(f"Email CTA Clicked event: Template placeholder errors: {errors}")
            raise ValueError(f"Email CTA Clicked event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
        )

        return EventResponseData(
            success=True,
            message="Email CTA clicked navigator card generated and saved to timeline successfully.",
            data=card_data,
        )
    except Exception as e:
        logger.exception(f"Error in handle_email_cta_clicked: {e}")
        raise


@event(EventType.CUSTOMER_KYC_HOLD_NN_CARD)  # type: ignore
async def handle_customer_kyc_hold_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer alignment check hold navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "case_number": "CASE-100",
        "timestamp": "2021-01-01T00:00:00Z",
        "kyc_id": 1,
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "case_number", "timestamp", "kyc_id"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Customer Alignment Check Hold Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Customer Alignment Check Hold Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        customer_name = payload["customer_name"]
        current_user = event.current_user
        kyc_id = payload["kyc_id"]
        role_code = UserRoleEnum.NAVIGATOR.value
        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Customer Alignment Check Hold Navigator Card event: Invalid case ID format") from e

        template, last_version = get_template_json(str(ComponentEnum.CUSTOMER_KYC_HOLD_NN_CARD.value), str(role_code), "timeline")

        timeline_type = get_timeline_type(db, ComponentEnum.CUSTOMER_KYC_HOLD_NN_CARD.value, role_code, last_version)
        if timeline_type is None:
            raise ValueError("Customer Alignment Check Hold Navigator Card event: Timeline type not found")  # noqa: TRY301
        
        first_name = current_user.first_name if current_user.first_name is not None else ""
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "case_number": case_number,
            "timestamp": timestamp,
            "customer_name": customer_name,
            "kyc_id": kyc_id,
            "action_buttons": {
                "alignment_check": True,
                "view_alignment_check_details": True,
                "alignment_check_push": True
            },
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)
        if errors:
            logger.error(f"Customer Alignment Check Hold Navigator Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Customer Alignment Check Hold Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        timeline_event = save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data
        )
        timeline = get_timeline_event_from_map(db, str(timeline_type.type_name), int(case_id), timeline_event.id)
        if not timeline:
            save_timeline_map(db, int(timeline_event.id), str(timeline_type.type_name), int(case_id))

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Customer Alignment Check Hold navigator card generated and saved to timeline successfully.",
            data={}
        )

    except Exception as e:
        logger.exception(f"Customer Alignment Check Hold Navigator Card event: Error in handle_customer_kyc_hold_nn_card: {e}")
        raise


@event(EventType.BOOK_FREE_CALL_NN_CARD)  # type: ignore
async def handle_book_free_call_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle book free call navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "case_number": "CASE-100",
        "timestamp": "2021-01-01T00:00:00Z",
        "kyc_id": 1,
        "attendee_phone_number": "+1234567890",
        "start_time": "2021-01-01T00:00:00Z",
        "end_time": "2021-01-01T00:00:00Z"
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "case_number", "timestamp", "kyc_id", "attendee_phone_number", "start_time", "end_time"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Book Free Call event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Book Free Call event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        kyc_id = payload["kyc_id"]
        attendee_phone_number = payload["attendee_phone_number"]
        # meeting_url = payload.get("meeting_url", "")
        start_time = payload["start_time"]
        end_time = payload["end_time"]
        customer_name = payload["customer_name"]

        template, last_version = get_template_json(str(ComponentEnum.BOOK_FREE_CALL_NN_CARD.value), str(UserRoleEnum.NAVIGATOR.value), "timeline")
        timeline_type = get_timeline_type(db, ComponentEnum.BOOK_FREE_CALL_NN_CARD.value, UserRoleEnum.NAVIGATOR.value, last_version)
        if timeline_type is None:
            raise ValueError("Book Free Call Customer Card event: Timeline type not found")  # noqa: TRY301

        placeholder_values = {
            "action_by": "",
            "case_number": case_number,
            "timestamp": timestamp,
            "customer_name": customer_name,
            "attendee_phone_number": attendee_phone_number,
            # "meeting_url": meeting_url,
            "start_time": start_time,
            "end_time": end_time,
            "kyc_id": kyc_id,
            "action_buttons": {
                "alignment_check": True,
                # "free_call": True if meeting_url else False
            },
        }

        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)
        if errors:
            logger.error(f"Book Free Call event: Template placeholder errors: {errors}")
            raise ValueError(f"Book Free Call event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        timeline_event = save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data
        )
        timeline = get_timeline_event_from_map(db, str(timeline_type.type_name), int(case_id), timeline_event.id)
        if not timeline:
            save_timeline_map(db, int(timeline_event.id), str(timeline_type.type_name), int(case_id))

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Book Free Call card generated and saved to timeline successfully.",
            data={}
        )
    except Exception as e:
        logger.exception(f"Book Free Call event: Error in handle_book_free_call: {e}")
        raise


@event(EventType.TRIAGE_SUBMITTED_NN_CARD)  # type: ignore
async def handle_triage_submitted_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle triage submitted navigator card event: Generate card JSON using template
    and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "triage_id": 1,
        "case_number": "CASE-100",
        "timestamp": "2021-01-01T00:00:00Z",
        "customer_name": "John Doe",
        "attendee_phone_number": "+1234567890",
        # "meeting_url": "https://example.com/meeting", (optional)
        "start_time": "2021-01-01T00:00:00Z", (optional)
        "end_time": "2021-01-01T00:00:00Z", (optional)
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "triage_id",
            "case_number",
            "timestamp",
            "customer_name",
            "attendee_phone_number"
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Triage Submitted Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError(
                "Triage Submitted Navigator Card event: Required keys not found in payload"
            )  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        customer_name = payload["customer_name"]
        attendee_phone_number = payload["attendee_phone_number"]
        # meeting_url = payload.get("meeting_url", "")
        start_time = payload.get("start_time", "")
        end_time = payload.get("end_time", "")
        kyc_id = payload.get("kyc_id", "")
        triage_id = payload.get("triage_id", "")

        template, last_version = get_template_json(
            str(ComponentEnum.TRIAGE_SUBMITTED_NN_CARD.value),
            str(UserRoleEnum.NAVIGATOR.value),
            "timeline",
        )
        timeline_type = get_timeline_type(
            db,
            ComponentEnum.TRIAGE_SUBMITTED_NN_CARD.value,
            UserRoleEnum.NAVIGATOR.value,
            last_version,
        )
        if timeline_type is None:
            raise ValueError(
                "Triage Submitted Navigator Card event: Timeline type not found"
            )  # noqa: TRY301

        placeholder_values = {
            "action_by": "",
            "case_number": case_number,
            "timestamp": timestamp,
            "customer_name": customer_name,
            "attendee_phone_number": attendee_phone_number,
            # "meeting_url": meeting_url,
            "start_time": start_time,
            "end_time": end_time,
            "kyc_id": encrypt_id(str(kyc_id)),
            "triage_id": encrypt_id(str(triage_id)) if triage_id else "",
            "action_buttons": {
                "alignment_check": True,
                # "free_call": True if meeting_url else False,
                "view_triage": True if triage_id else False,
            },
        }

        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)
        if errors:
            logger.error(
                f"Triage Submitted Navigator Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(
                f"Triage Submitted Navigator Card event: Template processing failed: {', '.join(errors)}"
            )  # noqa: TRY301

        timeline_event = save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
        )
        timeline = get_timeline_event_from_map(
            db, str(timeline_type.type_name), int(case_id), timeline_event.id
        )
        if not timeline:
            save_timeline_map(
                db, int(timeline_event.id), str(timeline_type.type_name), int(case_id)
            )

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Triage submitted navigator card generated and saved to timeline successfully.",
            data={},
        )
    except Exception as e:
        logger.exception(
            f"Triage Submitted Navigator Card event: Error in handle_triage_submitted_nn_card: {e}"
        )
        raise

@event(EventType.TRIAGE_NN_EMAIL)  # type: ignore
async def send_triage_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Notify navigators that a case was opened via triage form submission.

    Example payload:
    {
        "case_id": 1,
        "customer_email": "user@example.com",
        "navigators": [
            {
                "navigator_email": "navigator@example.com",
                "navigator_name": "JohnDoe"
            }
        ],
        "customer_name": "JohnDoe",
        "start_date": "19/09/2025",
        "priority": "High",
        "case_type": "Family Law",
        "case_number": "CASE-100",
        "status": "Open"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "customer_email",
            "navigators",
            "customer_name",
            "start_date",
            "priority",
            "case_type",
            "case_number",
            "status",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        customer_name = payload.get("customer_name")
        customer_email = payload.get("customer_email")
        start_date = payload.get("start_date")
        priority = payload.get("priority")
        case_type = payload.get("case_type")
        case_number = payload.get("case_number")
        case_status = payload.get("status")
        navigators = payload.get("navigators")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)

        if navigators is None:
            logger.warning("No navigators found in payload")
            return EventResponseData(
                success=False,
                message="No navigators found in payload",
                data=[],
            )

        navigator_emails = [
            str(navigator.get("navigator_email"))
            for navigator in navigators
            if navigator.get("navigator_email") is not None
        ]

        if not navigator_emails:
            logger.warning("No navigator emails found in payload")
            return EventResponseData(
                success=False,
                message="No navigator emails found in payload",
                data=[],
            )

        response = await email_service.send_email(
            bcc=navigator_emails,
            template=email_service.EmailTemplate.TRIAGE_NAVIGATOR_NOTIFICATION,
            context={
                "navigator_name": "Navigator",
                "customer_name": customer_name,
                "customer_email": customer_email,
                "start_date": start_date,
                "priority": priority,
                "case_type": case_type,
                "case_number": case_number,
                "status": case_status,
                "case_url": case_url,
                "header_subtitle": "Triage Case Opened",
            },
        )

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Triage navigator email sent successfully.",
            data=[
                {
                    "navigator_email": navigator_emails,
                    "navigator_name": "Navigator",
                    "message_id": response.message_id,
                }
            ],
        )
    except Exception as e:
        logger.exception(f"Error in send_triage_navigator_email: {e}")
        raise


@event(EventType.TRIAGE_RE_SUBMIT_NN_EMAIL)  # type: ignore
async def send_triage_re_submit_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Notify navigators that a completed triage was re-submitted.

    Example payload:
    {
        "case_id": 1,
        "customer_email": "user@example.com",
        "navigators": [
            {
                "navigator_email": "navigator@example.com",
                "navigator_name": "JohnDoe"
            }
        ],
        "customer_name": "JohnDoe",
        "start_date": "19/09/2025",
        "priority": "High",
        "case_type": "Family Law",
        "case_number": "CASE-100",
        "status": "Open"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "customer_email",
            "navigators",
            "customer_name",
            "start_date",
            "priority",
            "case_type",
            "case_number",
            "status",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        customer_name = payload.get("customer_name")
        customer_email = payload.get("customer_email")
        start_date = payload.get("start_date")
        priority = payload.get("priority")
        case_type = payload.get("case_type")
        case_number = payload.get("case_number")
        case_status = payload.get("status")
        navigators = payload.get("navigators")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)

        if navigators is None:
            logger.warning("No navigators found in payload")
            return EventResponseData(
                success=False,
                message="No navigators found in payload",
                data=[],
            )

        navigator_emails = [
            str(navigator.get("navigator_email"))
            for navigator in navigators
            if navigator.get("navigator_email") is not None
        ]

        if not navigator_emails:
            logger.warning("No navigator emails found in payload")
            return EventResponseData(
                success=False,
                message="No navigator emails found in payload",
                data=[],
            )

        response = await email_service.send_email(
            bcc=navigator_emails,
            template=email_service.EmailTemplate.TRIAGE_RESUBMIT_NAVIGATOR_NOTIFICATION,
            context={
                "navigator_name": "Navigator",
                "customer_name": customer_name,
                "customer_email": customer_email,
                "start_date": start_date,
                "priority": priority,
                "case_type": case_type,
                "case_number": case_number,
                "status": case_status,
                "case_url": case_url,
                "header_subtitle": "Triage Details Updated",
            },
        )

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Triage re-submit navigator email sent successfully.",
            data=[
                {
                    "navigator_email": navigator_emails,
                    "navigator_name": "Navigator",
                    "message_id": response.message_id,
                }
            ],
        )
    except Exception as e:
        logger.exception(f"Error in send_triage_re_submit_navigator_email: {e}")
        raise


@event(EventType.BOOK_FREE_CALL_POST_RESOLVE_NN_EMAIL)  # type: ignore
async def send_book_free_call_post_resolve_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send book free call post resolve notification email to all navigators.

    Payload:
    {
        "case": <Case object>,
        "case_number": "CASE-100",
        "customer_name": "JohnDoe",
        "customer_email": "user@example.com",
        "start_time": "19/09/2025 10:00:00",
        "end_time": "19/09/2025 11:00:00",
        "navigators": [
            {
                "navigator_email": "navigator@example.com",
                "navigator_name": "JohnDoe"
            }
        ]
    }
    """
    try:
        payload = event.payload
        required_keys = ["case", "case_number", "customer_name", "customer_email", "start_time", "end_time"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case = payload.get("case")
        case_number = payload.get("case_number")
        customer_name = payload.get("customer_name")
        customer_email = payload.get("customer_email")
        start_time = payload.get("start_time")
        end_time = payload.get("end_time")
        navigators = payload.get("navigators")

        call_date, call_time = _format_uk_call_window(start_time, end_time)

        navigator_emails = [
            str(navigator.get("navigator_email"))
            for navigator in navigators
            if navigator.get("navigator_email") is not None
        ]

        if not navigator_emails:
            logger.warning("No navigator emails found in payload")
            return EventResponseData(
                success=False,
                message="No navigator emails found in payload",
                data=[],
            )

        case_url = get_case_details_url(case.id)

        response = await email_service.send_email(
            bcc=navigator_emails,
            template=email_service.EmailTemplate.BOOK_FREE_CALL_POST_RESOLVE_NAVIGATOR_NOTIFICATION,
            context={
                "customer_name": customer_name,
                "customer_email": customer_email,
                "case_number": case_number,
                "case_url": case_url,
                "call_date": call_date,
                "call_time": call_time,
            },
        )

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="book free call post resolve navigator email sent successfully.",
            data=[
                {
                    "navigator_email": navigator_emails,
                    "navigator_name": "Navigator",
                    "message_id": response.message_id,
                }
            ],
        )
    except Exception as e:
        logger.exception(f"Error in send_book_free_call_post_resolve_navigator_email: {e}")
        raise


@event(EventType.BOOK_FREE_CALL_HIGH_INTENT_NN_EMAIL)  # type: ignore
async def send_book_free_call_high_intent_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send book free call high intent notification email to all navigators.
    """
    try:
        payload = event.payload
        required_keys = ["customer_email", "customer_name", "start_time", "end_time"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        customer_name = payload.get("customer_name")
        customer_email = payload.get("customer_email")
        start_time = payload.get("start_time")
        end_time = payload.get("end_time")
        navigators = payload.get("navigators")

        call_date, call_time = _format_uk_call_window(start_time, end_time)

        navigator_emails = [
            str(navigator.get("navigator_email"))
            for navigator in navigators
            if navigator.get("navigator_email") is not None
        ]

        if not navigator_emails:
            logger.warning("No navigator emails found in payload")
            return EventResponseData(
                success=False,
                message="No navigator emails found in payload",
                data=[],
            )

        response = await email_service.send_email(
            bcc=navigator_emails,
            template=email_service.EmailTemplate.BOOK_FREE_CALL_HIGH_INTENT_NAVIGATOR_NOTIFICATION,
            context={
                "customer_name": customer_name,
                "customer_email": customer_email,
                "call_date": call_date,
                "call_time": call_time,
            },
        )

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="book free call high intent navigator email sent successfully.",
            data=[
                {
                    "navigator_email": navigator_emails,
                    "navigator_name": "Navigator",
                    "message_id": response.message_id,
                }
            ],
        )
    except Exception as e:
        logger.exception(f"Error in send_book_free_call_high_intent_navigator_email: {e}")
        raise
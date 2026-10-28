"""
Lawyer Event Handlers

This module contains the lawyer event handler functions.
It demonstrates the event-driven architecture using enums for type safety.

All event handlers are decorated with @event and automatically registered.
"""

import logging

from sqlalchemy.orm import Session

from app.core.email import email_service
from app.db.services.general import get_timeline_type, get_all_navigator_emails
from app.db.services.lawyer_onboarding import create_lawyer_onboarding
from app.db.services.timeline_event import save_timeline_event
from app.enums.component import ComponentEnum
from app.enums.events import EventType
from app.enums.file_upload import ImageSize
from app.enums.user_role import UserRoleEnum
from app.events.dispatcher import event
from app.db.services.timeline_event import get_timeline_event_from_map, save_timeline_map
from app.schemas.v1.event import Event, EventResponseData
from app.services.upload_service import UploadService
from app.utils.formatters import format_json_field, format_service_details
from app.enums.lawyer import (
    ExpertTypeEnum,
    RegulatorEnum,
    DRPreferenceEnum,
    AccreditedSpecialismEnum,
    MatterTypeEnum,
)
from app.utils.helpers import get_template_json, replace_placeholders
from app.utils.photo_utils import generate_photo_urls
from app.utils.validators import validate_event_payload
from app.websocket.manager import WebSocketManager

logger = logging.getLogger(__name__)

upload_service = UploadService()


@event(EventType.COMPLETE_ONBOARD_ASSESSMENT_LAW_CARD)  # type: ignore
async def handle_complete_onboard_assessment_law_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle complete onboard assessment lawyer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": "1",
        "case_number": "CASE-001",
        "customer_name": "John Doe",
        "timestamp": "2021-01-01T00:00:00Z"
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "case_number", "timestamp", "customer_name"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Complete Onboard Assessment Expert Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Complete Onboard Assessment Expert Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        customer_name = payload["customer_name"]
        role_code = UserRoleEnum.LAWYER.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Complete Onboard Assessment Expert Card event: Invalid case ID format") from e

        template, last_version = get_template_json(
            str(ComponentEnum.COMPLETE_ONBOARD_ASSESSMENT_LAW_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.COMPLETE_ONBOARD_ASSESSMENT_LAW_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Complete Onboard Assessment Expert Card event: Timeline type not found")  # noqa: TRY301

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
            logger.error(f"Complete Onboard Assessment Expert Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Complete Onboard Assessment Expert Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

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
            message="Complete-onboard-assessment-expert-card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(f"Complete Onboard Assessment Expert Card event: Error in handle_complete_onboard_assessment_expert_card: {e}")
        raise


@event(EventType.CREATE_LEGAL_EXPERT)  # type: ignore[misc]
async def handle_create_legal_expert(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Main event handler for creating a legal expert.
    Formats all data and passes it through the payload to sub-events.

    Required payload:
    {
        request_data: LawyerOnboardingCreateRequest
    }
    """
    try:
        payload = event.payload
        required_keys = {"request_data": ["first_name", "last_name", "email", "phone", "work_status", "city", "post_code"]},
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        request_data = payload["request_data"]

        # Create the lawyer onboarding record in the database
        lawyer_onboarding, photo_processing_success = create_lawyer_onboarding(db, request_data)
        if not photo_processing_success:
            logger.warning(f"Photo processing failed for expert onboarding ID: {lawyer_onboarding.id}")

        # Generate photo URL for email context
        photo_url_path = lawyer_onboarding.photo_url
        photo_url = upload_service.get_image_url(photo_url_path, ImageSize.MEDIUM) if photo_url_path else ""

        # Format all data for sub-events
        from app.utils.formatters import extract_name_parts
        from app.enums.base import NameExtractionOption
        lawyer_first_name = extract_name_parts(lawyer_onboarding.first_name + " " + lawyer_onboarding.last_name, NameExtractionOption.FIRST)
        context = {
            "lawyer_name": lawyer_onboarding.first_name + " " + lawyer_onboarding.last_name,
            "lawyer_first_name": lawyer_first_name,
            "first_name": lawyer_onboarding.first_name,
            "last_name": lawyer_onboarding.last_name,
            "email": lawyer_onboarding.email,
            "phone": lawyer_onboarding.phone,
            "work_status": lawyer_onboarding.work_status,
            "firm_name": lawyer_onboarding.firm_name,
            "city": lawyer_onboarding.city,
            "post_code": lawyer_onboarding.post_code,
            "gender": lawyer_onboarding.gender.value if lawyer_onboarding.gender else None,
            "ncdr_description": lawyer_onboarding.ncdr_description,
            "compelling_quote": lawyer_onboarding.compelling_quote,
            "remote_consultation": lawyer_onboarding.remote_consultation.value if lawyer_onboarding.remote_consultation else None,
            "status": lawyer_onboarding.status.value if lawyer_onboarding.status else None,
            "experience": lawyer_onboarding.experience,

            # Format JSON fields with enum conversions (separate_other=True for better display)
            "professional_status": format_json_field(
                lawyer_onboarding.professional_status,
                enum_class=ExpertTypeEnum,
                separate_other=True
            ),
            "ncdr_magic": format_json_field(
                lawyer_onboarding.ncdr_magic,
                enum_class=DRPreferenceEnum
            ),
            "accredited_specialist": format_json_field(
                lawyer_onboarding.accredited_specialist,
                enum_class=AccreditedSpecialismEnum
            ),
            # "consultation_offers": format_json_field(
            #     lawyer_onboarding.consultation_offers,
            #     enum_label_map={
            #         "FREE_INITIAL_INTERVIEW": "Free initial interview",
            #         "FIXED_FEE_INITIAL_INTERVIEW": "Fixed fee initial interview",
            #         "HOURLY_RATE_INITIAL_INTERVIEW": "Hourly rate initial interview",
            #         "LEGAL_AID_LEGAL_HELP_INTERVIEW": "Legal Aid/Legal Help interview",
            #     }
            # ),
            "regulator": format_json_field(
                lawyer_onboarding.regulator,
                enum_class=RegulatorEnum,
                separate_other=True
            ),
            "service_details": format_service_details(lawyer_onboarding.service_details),
            "matter_types": format_json_field(
                {"values": lawyer_onboarding.matter_types},
                enum_class=MatterTypeEnum
            ),
            "accredited_specialism_other": lawyer_onboarding.accredited_specialism_other,
            "photo_url": photo_url,
        }
        payload["context"] = context

        # Build response data for the endpoint
        onboarding_dict = {
            "id": lawyer_onboarding.id,
            "first_name": lawyer_onboarding.first_name,
            "last_name": lawyer_onboarding.last_name,
            "email": lawyer_onboarding.email,
            "phone": lawyer_onboarding.phone,
            "work_status": lawyer_onboarding.work_status,
            "firm_name": lawyer_onboarding.firm_name,
            "city": lawyer_onboarding.city,
            "post_code": lawyer_onboarding.post_code,
            "gender": lawyer_onboarding.gender.value if lawyer_onboarding.gender else None,
            "photo_url": generate_photo_urls(lawyer_onboarding.photo_url) if lawyer_onboarding.photo_url else None,
            "professional_status": lawyer_onboarding.professional_status,
            "experience": lawyer_onboarding.experience,
            "service_details": lawyer_onboarding.service_details,
            "ncdr_magic": lawyer_onboarding.ncdr_magic,
            "accredited_specialist": lawyer_onboarding.accredited_specialist,
            "regulator": lawyer_onboarding.regulator,
            "ncdr_description": lawyer_onboarding.ncdr_description,
            "compelling_quote": lawyer_onboarding.compelling_quote,
            "remote_consultation": lawyer_onboarding.remote_consultation.value if lawyer_onboarding.remote_consultation else None,
            "consultation_offers": lawyer_onboarding.consultation_offers,
            "matter_types": lawyer_onboarding.matter_types,
            "accredited_specialism_other": lawyer_onboarding.accredited_specialism_other,
            "status": lawyer_onboarding.status.value if lawyer_onboarding.status else None,
            "created_at": lawyer_onboarding.created_at,
            "updated_at": lawyer_onboarding.updated_at,
        }
        payload["onboarding_dict"] = onboarding_dict

        return EventResponseData(
            success=True,
            message="Legal expert created successfully.",
            data=onboarding_dict,
        )

    except Exception as e:
        logger.exception(f"Error in handle_create_legal_expert: {e}")
        raise


@event(EventType.LEGAL_EXPERT_SIGNUP_NN_EMAIL)  # type: ignore[misc]
async def send_legal_expert_signup_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send legal expert signup notification email to navigators when a legal expert is onboarded.

    Uses pre-formatted data from the main CREATE_LEGAL_EXPERT event payload.
    """
    try:
        payload = event.payload
        required_keys = ["context"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        # Get all navigator emails to notify
        navigator_emails = get_all_navigator_emails(db)

        if not navigator_emails:
            return EventResponseData(
                success=False,
                message="No navigators found to notify",
                data=[],
            )

        navigator_email_list = [
            str(navigator.get("navigator_email"))
            for navigator in navigator_emails
            if navigator.get("navigator_email") is not None
        ]

        if not navigator_email_list:
            return EventResponseData(
                success=False,
                message="No navigator emails found",
                data=[],
            )

        # Use pre-formatted data from main event
        context = payload["context"]

        response = await email_service.send_email(
            bcc=navigator_email_list,
            template=email_service.EmailTemplate.LEGAL_EXPERT_SIGNUP_NAVIGATOR_NOTIFICATION,
            context={
                "header_subtitle": "New Legal Expert Signed Up",
                "context": context,
            },
        )

        return EventResponseData(
            success=True,
            message="Legal expert signup email sent successfully to navigators.",
            data=context,
            message_id=response.message_id,
        )

    except Exception as e:
        logger.exception(f"Error in send_legal_expert_signup_navigator_email: {e}")
        raise


@event(EventType.LEGAL_EXPERT_SIGNUP_EXPERT_EMAIL)  # type: ignore[misc]
async def send_legal_expert_signup_expert_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send legal expert signup confirmation email to the legal expert when they are onboarded.

    Uses pre-formatted data from the main CREATE_LEGAL_EXPERT event payload.
    """
    try:
        payload = event.payload
        required_keys = ["context"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        context = payload["context"]

        response = await email_service.send_email(
            to_email=context["email"],
            template=email_service.EmailTemplate.LEGAL_EXPERT_SIGNUP_EXPERT_NOTIFICATION,
            context={
                "context": context,
                "header_subtitle": "Welcome to Nova",
            },
        )

        return EventResponseData(
            success=True,
            message="Legal expert signup confirmation email sent successfully to the legal expert.",
            data=context,
            message_id=response.message_id,
        )

    except Exception as e:
        logger.exception(f"Error in send_legal_expert_signup_expert_email: {e}")
        raise



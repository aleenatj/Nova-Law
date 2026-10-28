"""
Case Event Handlers

This module contains event handler functions for case-related email notifications.
All event handlers are decorated with @event and automatically registered.
"""

import logging
from datetime import datetime, timezone
import json
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.api.v1.case import _handle_case_action_common_logic
from app.core.email import email_service
from app.db.services.ai import generate_ai_case_summary
from app.db.services.case import (
    create_case,
    get_case_by_id,
    update_case_decline_service,
    update_case_interest_service,
    update_case_summary_service,
)
from app.db.services.general import (
    get_all_navigator_emails, 
    get_case_details_url, 
    get_timeline_type,
    invoke_dispatch_event,
)
from app.db.services.timeline_event import (
    disable_timeline_action_buttons,
    save_timeline_event,
    save_timeline_map,
    update_timeline_event
)
from app.db.services.kyc import format_kyc_answers
from app.db.services.resolve import format_resolve_question_answers, get_resolve_by_id, get_resolve_from_case_id, get_result
from app.db.models.case import Case
from app.enums.case import CaseStatusEnum
from app.enums.component import ComponentEnum
from app.enums.events import EventType
from app.enums.match import MatchStatusEnum
from app.enums.user_role import UserRoleEnum
from app.events.dispatcher import event
from app.schemas.v1.customer import (
    CaseInfo,
    CustomerRegistrationResponseData,
)
from app.schemas.v1.event import Event, EventResponseData
from app.utils.formatters import format_case_number, extract_name_parts
from app.enums.base import NameExtractionOption
from app.utils.helpers import calculate_lawyer_experience, get_template_json, replace_placeholders
from app.utils.validators import validate_event_payload
from app.websocket.manager import WebSocketManager
from app.core.config import settings
from app.utils.encryption import encrypt_id
from app.services.upload_service import UploadService
from app.enums.file_upload import ImageSize

logger = logging.getLogger(__name__)

upload_service = UploadService()


@event(EventType.CASE_OPEN) # type: ignore[misc]
async def handle_case_open(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case open event.
    Required payload:
    {
        "resolve_id": "DECRYPTED_RESOLVE_ID",
        "customer_id": "CUSTOMER_ID",
        "response_data": <ResponseData object>
    }
    """
    try:
        payload = event.payload
        required_keys = ["customer_id", "response_data"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(f"Payload validation failed for {event.event_type.value}: {validation}")
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        resolve_id = payload["resolve_id"]
        customer_id = payload["customer_id"]
        response_data = payload["response_data"]

        # Transaction 2: Case creation (only if resolve_id is provided)
        case = None

        if resolve_id:
            try:
                # Create case with associations (without committing)
                case = create_case(
                    db=db, customer_id=int(customer_id), resolve_id=resolve_id
                )

                # Commit Transaction 2
                db.commit()
                # Get case information if case was created
                case_info = None
                if case:
                    case_no_value = getattr(case, "case_no", None)
                    formatted_case_no = (
                        format_case_number(case_no_value)
                        if case_no_value is not None
                        else ""
                    )
                    case_info = CaseInfo(
                        case_id=str(case.id),
                        case_no=formatted_case_no,
                        case_type=case.case_type.value if case.case_type else None,
                        priority=case.priority.value if case.priority else None,
                        start_date=case.start_date,  # type: ignore[arg-type]
                        status=case.status.value,
                        created_at=case.created_at,  # type: ignore[arg-type]
                        updated_at=case.updated_at,  # type: ignore[arg-type]
                    )

                    response_data.case = case_info

            except HTTPException:
                raise
            except Exception as e:
                # Rollback Transaction 2 if any error occurs
                db.rollback()
                # Note: Transaction 1 is already committed, so we can't rollback user/customer creation
                # This is a limitation of the two-transaction approach
                # message.append(ResponseMessage(success=False, message="Case creation failed"))
                raise ValueError("Case creation failed ") from None
        else:
            raise ValueError("Case not created, no resolve id provided")  # noqa: TRY301

        if response_data.login_data and not response_data.login_data.redirect_path:
            encrypted_case_id = encrypt_id(str(case.id))
            response_data.login_data.redirect_path = f"/case/{encrypted_case_id}"

        case_response = CustomerRegistrationResponseData.model_validate(response_data)

        if case_info is not None:
            payload["start_date"] = case_info.start_date
            payload["priority"] = case_info.priority
            payload["case_type"] = case_info.case_type
            payload["case_number"] = case_info.case_no
            payload["status"] = case_info.status
        payload["case_id"] = int(case.id)
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()

        # Add first_name, title, summary, recommendations, kyc_id to payload
        first_name = ""
        title = ""
        summary = ""
        recommendations = {}

        # Get first_name from current_user
        if event.current_user:
            first_name = event.current_user.first_name or ""

        # Get resolve data for result title, summary and recommendations
        if resolve_id:
            resolve = get_resolve_by_id(db, int(resolve_id))
            if resolve:
                result = get_result(resolve)
                # title = result.get("title", "")
                # summary = result.get("summary", "")
                # recommendations = result.get("recommendations", {})
                recommended_approach = result.get("recommended_approach", {}) if result else None
                title = recommended_approach.get("title", "") if recommended_approach else ""
                summary = recommended_approach.get("summary", "") if recommended_approach else ""
                recommendations = recommended_approach.get("recommendations", {}) if recommended_approach else {}
                # If first_name not from current_user, try from resolve customer_name
                if not first_name and resolve.customer_name:
                    first_name = resolve.customer_name

        payload["first_name"] = first_name
        payload["title"] = title
        payload["summary"] = summary
        payload["recommendations"] = recommendations

        should_display = True
        message = "Case opened successfully"
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False
            message = "Your case has been opened successfully."        

        current_user_id = int(event.current_user.id) if event.current_user else None
        # dispatch the event to generate the AI case summary
        invoke_dispatch_event(event_type=EventType.GENERATE_AI_CASE_SUMMARY, payload=payload, user_id=event.user_id, current_user_id=current_user_id)

        return EventResponseData(
            should_display=should_display,
            success=True,
            message=message,
            data=case_response,
        )
    except Exception as e:
        logger.exception(f"Error in handle_case_open: {e}")
        raise


@event(EventType.CASE_OPEN_CUS_EMAIL)  # type: ignore[misc]
async def send_case_open_customer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send case opened confirmation email to the customer with key case details.

    Example payload:
    {
        "case_id": 1,
        "customer_email": "user@example.com",
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

        email = payload.get("customer_email")
        customer_name = payload.get("customer_name")
        start_date = payload.get("start_date")
        priority = payload.get("priority")
        case_type = payload.get("case_type")
        case_number = payload.get("case_number")
        status = payload.get("status")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)
        customer_name = extract_name_parts(customer_name, NameExtractionOption.FIRST)
        if not email or not isinstance(email, str):
            raise ValueError("Valid customer email is required")  # noqa: TRY301

        # Send email notification
        response = await email_service.send_email(
            to_email=email,
            template=email_service.EmailTemplate.CASE_OPEN_CUSTOMER_NOTIFICATION,
            context={
                "customer_name": customer_name,
                "start_date": start_date,
                "priority": priority,
                "case_type": case_type,
                "case_number": case_number,
                "status": status,
                "case_url": case_url,
                "header_subtitle": "Case Opened Successfully",
            },
        )

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case opened email sent successfully to customer",
            data={
                "customer_email": email,
                "customer_name": customer_name,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_case_open_customer_email: {e}")
        raise


@event(EventType.CASE_OPEN_NN_EMAIL)  # type: ignore[misc]
async def send_case_open_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send case opened confirmation email to the navigator with key case details.

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
        status = payload.get("status")
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
        response_list = []
        # Prepare list of navigator emails
        navigator_emails = [str(navigator.get("navigator_email")) for navigator in navigators if navigator.get("navigator_email") is not None]

        if navigator_emails:
            # Send case opened confirmation email to navigator
            response = await email_service.send_email(
                bcc=navigator_emails,
                template=email_service.EmailTemplate.CASE_OPEN_NAVIGATOR_NOTIFICATION,
                context={
                    "navigator_name": "Navigator",
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "start_date": start_date,
                    "priority": priority,
                    "case_type": case_type,
                    "case_number": case_number,
                    "status": status,
                    "case_url": case_url,
                    "header_subtitle": "Case Opened Successfully",
                },
            )
            response_list.append({
                "navigator_email": navigator_emails,
                "navigator_name": "Navigator",
                "message_id": response.message_id,
            })

            should_display = True
            if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
                should_display = False

            return EventResponseData(
                should_display=should_display,
                success=True,
                message="Case opened email sent successfully to navigators",
                data=response_list,
            )
        else:
            return EventResponseData(
                success=False,
                message="No navigator emails found in payload",
                data=[],
            )

    except Exception as e:
        logger.exception(f"Error in send_case_open_navigator_email: {e}")
        raise


@event(EventType.CASE_INTEREST_LAW_EMAIL)  # type: ignore[misc]
async def send_case_interest_lawyer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to the lawyer when they raise interest in a case.

    Example payload:
    {
      "case_id": 1,
      "lawyer_email": "lawyer@example.com",
      "lawyer_name": "JohnDoe",
      "case_number": "CASE-100"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "case_number",
            "lawyer_name",
            "lawyer_email",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case_number = payload.get("case_number")
        lawyer_name = payload.get("lawyer_name")
        email = payload.get("lawyer_email")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)
        if not email or not isinstance(email, str):
            raise ValueError("Valid expert email is required")  # noqa: TRY301

        lawyer_name = extract_name_parts(lawyer_name, NameExtractionOption.FIRST)

        # Check if the action is performed by a navigator on behalf of the lawyer
        is_navigator_action = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            is_navigator_action = True

        response = await email_service.send_email(
            to_email=email,
            template=email_service.EmailTemplate.CASE_INTEREST_LAWYER_NOTIFICATION,
            context={
                "case_number": case_number,
                "lawyer_name": lawyer_name,
                "lawyer_email": email,
                "case_url": case_url,
                "header_subtitle": "Interest Sent Successfully",
                "is_navigator_action": is_navigator_action,
            },
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case interest email sent successfully to expert.",
            data={
                "email": email,
                "lawyer_name": lawyer_name,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_case_interest_lawyer_email: {e}")
        raise


@event(EventType.CASE_INTEREST_NN_EMAIL) # type: ignore
async def send_case_interest_navigator_notification_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send case interest notification email to Nova navigator.

    Example payload:
    {
        "case_id": 1,
        "navigators": [
            {
                "navigator_email": "navigator@example.com",
                "navigator_name": "John Doe"
            }
        ],
        "lawyer_name": "John Doe",
        "case_number": "CASE-100",
        "experience": "15",
        "case_type": "Family Law",
        "customer_name": "John Doe",
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "navigators", "lawyer_name", "case_number", "experience", "case_type", "customer_name"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        navigators = payload.get("navigators")
        lawyer_name = payload.get("lawyer_name")
        case_number = payload.get("case_number")
        experience = payload.get("experience")
        case_type = payload.get("case_type")
        customer_name = payload.get("customer_name")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)
        if navigators is None:
            logger.warning("No navigators found in payload")
            return EventResponseData(
                success=False,
                message="No navigators found in payload",
                data=[],
            )
        response_list = []
        # Prepare list of navigator emails
        navigator_emails = [str(navigator.get("navigator_email")) for navigator in navigators if navigator.get("navigator_email") is not None]

        if navigator_emails:
            # Check if the action is performed by a navigator on behalf of the lawyer
            is_navigator_action = False
            navigator_name = "Navigator"
            if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
                is_navigator_action = True
                # Get navigator name from current user
                if hasattr(event.current_user, 'first_name') and hasattr(event.current_user, 'last_name'):
                    first_name = event.current_user.first_name if event.current_user.first_name else ""
                    last_name = event.current_user.last_name if event.current_user.last_name else ""
                    navigator_name = f"{first_name} {last_name}".strip() or "Navigator"

            # Send case interest notification email to navigator
            response = await email_service.send_email(
                bcc=navigator_emails,
                template=email_service.EmailTemplate.CASE_INTEREST_NAVIGATOR_NOTIFICATION,
                context={
                    "navigator_name": "Navigator",
                    "lawyer_name": lawyer_name,
                    "case_number": case_number,
                    "experience": experience,
                    "case_type": case_type,
                    "case_url": case_url,
                    "header_subtitle": "Interest Received",
                    "is_navigator_action": is_navigator_action,
                    "action_by": navigator_name,
                    "customer_name": customer_name,
                },
            )
            response_list.append({
                "navigator_email": navigator_emails,
                "navigator_name": "Navigator",
                "message_id": response.message_id,
            })

            should_display = False
            if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
                should_display = False

            return EventResponseData(
                should_display=should_display,
                success=True,
                message="Case interest notification email sent successfully to navigator",
                data=response_list,
            )
        else:
            return EventResponseData(
                success=False,
                message="No navigator emails found in payload",
                data=[],
            )

    except Exception as e:
        logger.exception(f"Error in send_case_interest_navigator_notification_email: {e}")
        raise


@event(EventType.CASE_DECLINE_LAW_EMAIL)  # type: ignore[misc]
async def send_case_decline_lawyer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to the lawyer when they decline a case.

    Example payload:
    {
      "case_id": 1,
      "lawyer_email": "lawyer@example.com",
      "lawyer_name": "JohnDoe",
      "case_number": "CASE-100",
      "decline_reason": ["Conflict of interest"],
      "decline_reason_other": "Cannot take this case due to conflict",
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "case_number",
            "lawyer_name",
            "lawyer_email",
            "decline_reason",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case_number = payload.get("case_number")
        lawyer_name = payload.get("lawyer_name")
        email = payload.get("lawyer_email")
        decline_reason = payload.get("decline_reason")
        decline_reason_other = payload.get("decline_reason_other")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)

        lawyer_name = extract_name_parts(lawyer_name, NameExtractionOption.FIRST)
        if not email or not isinstance(email, str):
            raise ValueError("Valid expert email is required")  # noqa: TRY301

        # Check if the action is performed by a navigator on behalf of the lawyer
        is_navigator_action = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            is_navigator_action = True

        response = await email_service.send_email(
            to_email=email,
            template=email_service.EmailTemplate.CASE_DECLINE_LAWYER_NOTIFICATION,
            context={
                "case_number": case_number,
                "lawyer_name": lawyer_name,
                "lawyer_email": email,
                "decline_reason": decline_reason,
                "decline_reason_other": decline_reason_other,
                "case_url": case_url,
                "header_subtitle": "Case Declined Successfully",
                "is_navigator_action": is_navigator_action,
            },
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case decline email sent successfully to expert.",
            data={
                "email": email,
                "lawyer_name": lawyer_name,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_case_decline_lawyer_email: {e}")
        raise


@event(EventType.CASE_DECLINE_NN_EMAIL) # type: ignore
async def send_case_decline_navigator_notification_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send case decline notification email to Nova navigator.

    Example payload:
    {
        "case_id": 1,
        "navigators": [
            {
                "navigator_email": "navigator@example.com",
                "navigator_name": "John Doe"
            }
        ],
        "lawyer_name": "John Doe",
        "case_number": "CASE-100",
        "decline_reason": ["Conflict of interest"],
        "decline_reason_other": "Cannot take this case due to conflict",
        "customer_name": "John Doe",
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "navigators", "lawyer_name", "case_number", "decline_reason", "customer_name"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        navigators = payload.get("navigators")
        lawyer_name = payload.get("lawyer_name")
        case_number = payload.get("case_number")
        decline_reason = payload.get("decline_reason")
        decline_reason_other = payload.get("decline_reason_other")
        customer_name = payload.get("customer_name")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)
        if navigators is None:
            logger.warning("No navigators found in payload")
            return EventResponseData(
                success=False,
                message="No navigators found in payload",
                data=[],
            )
        response_list = []
        # Prepare list of navigator emails
        navigator_emails = [str(navigator.get("navigator_email")) for navigator in navigators if navigator.get("navigator_email") is not None]

        if navigator_emails:
            # Check if the action is performed by a navigator on behalf of the lawyer
            is_navigator_action = False
            navigator_name = "Navigator"
            if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
                is_navigator_action = True
                # Get navigator name from current user
                if hasattr(event.current_user, 'first_name') and hasattr(event.current_user, 'last_name'):
                    first_name = event.current_user.first_name if event.current_user.first_name else ""
                    last_name = event.current_user.last_name if event.current_user.last_name else ""
                    navigator_name = f"{first_name} {last_name}".strip() or "Navigator"

            # Send case interest notification email to navigator
            response = await email_service.send_email(
                bcc=navigator_emails,
                template=email_service.EmailTemplate.CASE_DECLINE_NAVIGATOR_NOTIFICATION,
                context={
                    "navigator_name": "Navigator",
                    "lawyer_name": lawyer_name,
                    "case_number": case_number,
                    "decline_reason": decline_reason,
                    "decline_reason_other": decline_reason_other,
                    "case_url": case_url,
                    "header_subtitle": "Nova Expert Declined",
                    "is_navigator_action": is_navigator_action,
                    "action_by": navigator_name,
                    "customer_name": customer_name,
                },
            )
            response_list.append({
                "navigator_email": navigator_emails,
                "navigator_name": "Navigator",
                "message_id": response.message_id,
            })

            should_display = False
            if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
                should_display = False

            return EventResponseData(
                should_display=should_display,
                success=True,
                message="Case decline notification email sent successfully to navigator",
                data=response_list,
            )
        else:
            return EventResponseData(
                success=False,
                message="No navigator emails found in payload",
                data=[],
            )

    except Exception as e:
        logger.exception(f"Error in send_case_decline_navigator_notification_email: {e}")
        raise


@event(EventType.CASE_PROFILE_NN_EMAIL)  # type: ignore[misc]
async def send_case_profile_navigator_notification_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send lawyer profile notification email to navigators when navigator reviews and sends lawyer matches.

    Example payload:
    {
        "case_id":1,
        "lawyers": [],
        "navigators": [
            {
                "navigator_email": "navigator@example.com",
                "navigator_name": "John Doe"
            }
        ],
        "case_number": "CASE-100",
        "customer_name": "John Doe",
    },
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "lawyers", "navigators", "case_number", "customer_name"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        lawyers = payload.get("lawyers")
        customer_name = payload.get("customer_name")
        case_id = payload.get("case_id")
        case_number = payload.get("case_number")
        case_url = get_case_details_url(case_id)
        from app.utils.formatters import format_accredited_specialisms
        lawyers_list = []
        if lawyers:
            for lawyer in lawyers:
                first_name = lawyer.user.first_name if lawyer.user and lawyer.user.first_name is not None else ""
                last_name = lawyer.user.last_name if lawyer.user and lawyer.user.last_name is not None else ""
                lawyer_name = first_name + " " + last_name
                # specialization = None
                # lawyer_accreditations = []
                # if hasattr(lawyer, "accredited_specialisms") and lawyer.accredited_specialisms:
                #     lawyer_accreditations = format_accredited_specialisms(lawyer.accredited_specialisms, lawyer.accredited_specialism_other)
                city = lawyer.city if lawyer.city is not None else ""
                county = lawyer.county if lawyer.county is not None else ""
                location = ', '.join(filter(None, [city, county]))
                hourly_rate = int(lawyer.hourly_rate) if lawyer.hourly_rate is not None else None
                charge_first_consultation = int(lawyer.charge_first_consultation) if lawyer.charge_first_consultation is not None else None
                about = lawyer.about
                photo_url = upload_service.get_image_url(lawyer.photo_url, ImageSize.MEDIUM) if lawyer.photo_url is not None else ""
                expert_types_all = [et.expert_type.value for et in lawyer.expert_types if not et.expert_type.is_other()]
                if hasattr(lawyer, "expert_types_other") and lawyer.expert_types_other:
                    expert_types_all.append(lawyer.expert_types_other.capitalize())
                expert_types_all.sort()
                # Calculate experience using helper
                experience = calculate_lawyer_experience(lawyer)
                lawyers_list.append({
                    "name": lawyer_name.strip(),
                    # "specialization": specialization,
                    # "lawyer_accreditations": lawyer_accreditations,
                    "hourly_rate": hourly_rate,
                    "charge_first_consultation": charge_first_consultation,
                    "experience": experience,
                    "location": location,
                    "about": about,
                    "photo_url": photo_url,
                    "expert_types_all": expert_types_all,
                })
        navigators = payload.get("navigators")

        if lawyers_list is None or not lawyers_list:
            logger.warning("No lawyers found in payload")
            return EventResponseData(
                success=False,
                message="No experts found in payload",
                data=[],
            )

        if navigators is None:
            logger.warning("No navigators found in payload")
            return EventResponseData(
                success=False,
                message="No navigators found in payload",
                data=[],
            )
        response_list = []
        # Prepare list of navigator emails
        navigator_emails = [str(navigator.get("navigator_email")) for navigator in navigators if navigator.get("navigator_email") is not None]

        if navigator_emails:
            # Send case profile notification email to navigator
            response = await email_service.send_email(
                bcc=navigator_emails,
                template=email_service.EmailTemplate.CASE_PROFILE_NAVIGATOR_NOTIFICATION,
                context={
                    "navigator_name": "Navigator",
                    "lawyers": lawyers_list,
                    "lawyer_count": len(lawyers_list),
                    "case_url": case_url,
                    "header_subtitle": "Profile Cards Sent",
                    "case_number": case_number,
                    "customer_name": customer_name,
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
                message="Case profile email sent successfully to navigators",
                data=response_list,
            )
        else:
            return EventResponseData(
                success=False,
                message="No navigator emails found in payload",
                data=[],
            )

    except Exception as e:
        logger.exception(f"Error in send_case_profile_navigator_email: {e}")
        raise


@event(EventType.CASE_PROFILE_CUS_EMAIL) # type: ignore
async def send_case_profile_customer_notification_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send case profile confirmation email to customers.

    Example payload:
    {
        "case_id": 1,
        "customer_email": "customer@example.com",
        "customer_name": "John Doe",
        "lawyers": [],
        "case_number": "CASE-100"
    }
    """
    from app.core.security import create_analytics_token
    try:
        payload = event.payload
        required_keys = ["case_id", "customer_email", "customer_name", "lawyers", "case_number"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        email = payload.get("customer_email")
        customer_name = payload.get("customer_name")
        lawyers = payload.get("lawyers")
        case_number = payload.get("case_number")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)
        from app.utils.formatters import extract_name_parts, format_accredited_specialisms
        from app.enums.base import NameExtractionOption
        customer_name = extract_name_parts(customer_name, NameExtractionOption.FIRST)
        if lawyers is None:
            logger.warning("No lawyers found in payload")
            return EventResponseData(
                success=False,
                message="No experts found in payload",
                data=[],
            )

        if not email:
            raise ValueError("Email not found in payload")  # noqa: TRY301

        lawyers_list = []
        for lawyer in lawyers:
            first_name = lawyer.user.first_name if lawyer.user and lawyer.user.first_name is not None else ""
            last_name = lawyer.user.last_name if lawyer.user and lawyer.user.last_name is not None else ""
            lawyer_name = first_name + " " + last_name
            # specialization = None
            # lawyer_accreditations = []
            # # specialization = lawyer.accredited_specialisations
            # if hasattr(lawyer, "accredited_specialisms") and lawyer.accredited_specialisms:
            #     lawyer_accreditations = format_accredited_specialisms(lawyer.accredited_specialisms, lawyer.accredited_specialism_other)
            city = lawyer.city if lawyer.city is not None else ""
            county = lawyer.county if lawyer.county is not None else ""
            location = ', '.join(filter(None, [city, county]))
            hourly_rate = int(lawyer.hourly_rate) if lawyer.hourly_rate is not None else ""
            charge_first_consultation = int(lawyer.charge_first_consultation) if lawyer.charge_first_consultation is not None else None
            about = lawyer.about
            photo_url = upload_service.get_image_url(lawyer.photo_url, ImageSize.MEDIUM) if lawyer.photo_url is not None else ""
            expert_types_all = [et.expert_type.value for et in lawyer.expert_types if not et.expert_type.is_other()]
            if hasattr(lawyer, "expert_types_other") and lawyer.expert_types_other:
                expert_types_all.append(lawyer.expert_types_other.capitalize())
            expert_types_all.sort()
            # Calculate experience using helper
            experience = calculate_lawyer_experience(lawyer)
            lawyers_list.append({
                "name": lawyer_name.strip(),
                # "specialization": specialization,
                # "lawyer_accreditations": lawyer_accreditations,
                "hourly_rate": hourly_rate,
                "charge_first_consultation": charge_first_consultation,
                "experience": experience,
                "location": location,
                "about": about,
                "photo_url": photo_url,
                "expert_types_all": expert_types_all,
            })

        analytics_payload = {
            "case_id": case_id,
            "event_type": EventType.EMAIL_CTA_CLICKED.value,
        }
        analytics_token = create_analytics_token(analytics_payload)
        # Send lawyer profiles to customer
        response = await email_service.send_email(
            to_email=email,
            template=email_service.EmailTemplate.CASE_PROFILE_CUSTOMER_NOTIFICATION,
            context={
                "customer_name": customer_name,
                "customer_email": email,
                "lawyers": lawyers_list,
                "lawyer_count": len(lawyers_list),
                "case_url": f"{case_url}/?analytics_token={analytics_token}",
                "header_subtitle": "Your Matched Legal Experts",
                "case_number": case_number,
            },
        )

        return EventResponseData(
            should_display=False,
            success=True,
            message="Case profile email sent successfully to customer",
            data={
                "customer_email": email,
                "customer_name": customer_name,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_case_profile_customer_notification_email: {e}")
        raise

@event(EventType.CASE_INTEREST) # type: ignore
async def handle_case_interest(
   db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case interest.
    """

    try:
        payload = event.payload
        required_keys = ["request_data", "current_user"]
        validation = validate_event_payload(payload, required_keys) # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301


        request_data = payload["request_data"]
        current_user = payload["current_user"]
        # Extract case_id and lawyer_id from request_data
        case_id, lawyer_id = _handle_case_action_common_logic(db, current_user, request_data)

        # Update case interest
        result = update_case_interest_service(db, case_id, lawyer_id, int(current_user.id))

        case = result["match"].case
        lawyer = result["match"].lawyer
        notify_user_id = None
        if lawyer and lawyer.user_id:
            notify_user_id = lawyer.user_id

        customer_name = None
        if case.case_customers and len(case.case_customers) > 0:
            customer = case.case_customers[0].customer
            # Get user data from the customer relationship
            user = customer.user
            customer_first_name = user.first_name if user.first_name else ""
            customer_last_name = user.last_name if user.last_name else ""
            customer_name = f"{customer_first_name} {customer_last_name}".strip()

        payload["customer_name"] = customer_name
        payload["case_id"] = case.id
        payload["lawyer_id"] = lawyer_id
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload["case_number"] = format_case_number(case.case_no)
        payload["lawyer_name"] = lawyer.user.first_name + " " + lawyer.user.last_name
        payload["lawyer_email"] = lawyer.user.email
        payload["experience"] = calculate_lawyer_experience(lawyer)
        payload["case_type"] = case.case_type.value
        payload["about_lawyer"] = lawyer.about
        payload["notify_user_id"] = notify_user_id
        navigator_emails = get_all_navigator_emails(db)
        payload["navigators"] = navigator_emails

        should_display = True
        message = result["message"]
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = True
        
        data = {
        str(ComponentEnum.CASE_NEW_MATCH_LAW_CARD.value): {"match_status": MatchStatusEnum.INTERESTED.value}
        }
        result = update_timeline_event(db, f"{case_id}_{lawyer_id}", data)
        if not result:
            logger.error(f"Failed to update timeline event for {case_id}_{lawyer_id}")
            # raise ValueError("Failed to update timeline event")  # noqa: TRY301

        # Disable raise_interest button in CASE_NEW_LAW_CARD timeline event
        disable_timeline_action_buttons(
            db=db,
            component_buttons={
                str(ComponentEnum.CASE_NEW_MATCH_LAW_CARD.value): ["raise_interest","decline_match","ask_more_details"],
                str(ComponentEnum.CASE_DECLINE_LAW_CARD.value): ["raise_interest","ask_more_details"],
                str(ComponentEnum.CASE_MORE_DETAILS_LAW_CARD.value): ["raise_interest","decline_match","ask_more_details"]
            },
            related_id=f"{case_id}_{lawyer_id}",
        )

        return EventResponseData(
            should_display=should_display,
            success=True,
            message=message,
            data=[],
        )


    except Exception as e:
        logger.exception(f"Error in handle_case_interest: {e}")
        raise


@event(EventType.CASE_AWARD_LAW_EMAIL)  # type: ignore[misc]
async def send_case_award_lawyer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to the lawyer when they are awarded a case.

    Example payload:
    {
        "case_id": 1,
        "case_number": "CASE-100",
        "customer_name": "John Doe",
        "case_type": "Family Law",
        "lawyer_email": "lawyer@example.com"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "case_number",
            "customer_name",
            "case_type",
            "lawyer_name",
            "lawyer_email",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case_number = payload.get("case_number")
        customer_name = payload.get("customer_name")
        case_type = payload.get("case_type")
        lawyer_name = payload.get("lawyer_name")
        lawyer_email = payload.get("lawyer_email")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)
        if not lawyer_email:
            raise ValueError("Expert email not found in payload")  # noqa: TRY301

        lawyer_name = extract_name_parts(lawyer_name, NameExtractionOption.FIRST)

        response = await email_service.send_email(
            to_email=lawyer_email,
            template=email_service.EmailTemplate.CASE_AWARD_LAWYER_NOTIFICATION,
            context={
                "case_number": case_number,
                "customer_name": customer_name,
                "case_type": case_type,
                "lawyer_name": lawyer_name,
                "case_url": case_url,
                "header_subtitle": "Case Awarded Successfully",
            },
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case award email sent successfully to lawyer.",
            data={
                "case_number": case_number,
                "customer_name": customer_name,
                "lawyer_name": lawyer_name,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_case_award_lawyer_email: {e}")
        raise


@event(EventType.CASE_AWARD_NN_EMAIL)  # type: ignore[misc]
async def send_case_award_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send case award notification email to Nova navigator.

    Example payload:
    {
        "case_id": 1,
        "navigators": [
            {
                "navigator_email": "navigator@example.com",
                "navigator_name": "John Doe"
            }
        ],
        "case_number": "CASE-100",
        "customer_name": "Jane Smith",
        "case_type": "Family Law",
        "lawyer_name": "Dr. Sarah Johnson"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "navigators",
            "case_number",
            "customer_name",
            "case_type",
            "lawyer_name",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        navigators = payload.get("navigators")
        case_number = payload.get("case_number")
        customer_name = payload.get("customer_name")
        case_type = payload.get("case_type")
        lawyer_name = payload.get("lawyer_name")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)
        if navigators is None:
            logger.warning("No navigators found in payload")
            return EventResponseData(
                success=False,
                message="No navigators found in payload",
                data=[],
            )

        response_list = []
        # Prepare list of navigator emails
        navigator_emails = [str(navigator.get("navigator_email")) for navigator in navigators if navigator.get("navigator_email") is not None]

        if navigator_emails:
            # Check if the action is performed by a navigator or customer
            is_navigator_action = False
            navigator_name = "Navigator"
            if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
                is_navigator_action = True
                # Get navigator name from current user
                if hasattr(event.current_user, 'first_name') and hasattr(event.current_user, 'last_name'):
                    first_name = event.current_user.first_name if event.current_user.first_name else ""
                    last_name = event.current_user.last_name if event.current_user.last_name else ""
                    navigator_name = f"{first_name} {last_name}".strip() or "Navigator"

            response = await email_service.send_email(
            bcc=navigator_emails,
                template=email_service.EmailTemplate.CASE_AWARD_NAVIGATOR_NOTIFICATION,
                context={
                    "navigator_name": "Navigator",
                    "case_number": case_number,
                    "customer_name": customer_name,
                    "case_type": case_type,
                    "lawyer_name": lawyer_name,
                    "case_url": case_url,
                    "header_subtitle": "Case Awarded Successfully",
                    "is_navigator_action": is_navigator_action,
                    "action_by": navigator_name,
                },
            )
            response_list.append({
                "navigator_email": navigator_emails,
                "navigator_name": "Navigator",
                "message_id": response.message_id,
            })
        else:
            return EventResponseData(
                success=False,
                message="No navigator emails found in payload",
                data=[],
            )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case award notification email sent successfully to navigators",
            data=response_list,
        )

    except Exception as e:
        logger.exception(f"Error in send_case_award_navigator_email: {e}")
        raise

@event(EventType.CASE_DECLINE) # type: ignore
async def handle_case_decline(
   db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case decline: Send email notification to the all navigators.
    """
    try:
        payload = event.payload
        required_keys = ["request_data", "current_user"]
        validation = validate_event_payload(payload, required_keys) # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        request_data = payload["request_data"]
        current_user = payload["current_user"]
        # Use common logic to handle role-based access and validation
        case_id, lawyer_id = _handle_case_action_common_logic(db, current_user, request_data)
        # Update case decline
        result = update_case_decline_service(db, case_id, lawyer_id, int(current_user.id), request_data.decline_reason)

        case = result["match"].case
        lawyer = result["match"].lawyer

        notify_user_id = None
        if lawyer and lawyer.user_id:
            notify_user_id = lawyer.user_id
        
        customer_name = None
        if case.case_customers and len(case.case_customers) > 0:
            customer = case.case_customers[0].customer
            # Get user data from the customer relationship
            user = customer.user
            customer_first_name = user.first_name if user.first_name else ""
            customer_last_name = user.last_name if user.last_name else ""
            customer_name = f"{customer_first_name} {customer_last_name}".strip()

        payload["case_number"] = format_case_number(case.case_no)
        payload["lawyer_name"] = lawyer.user.first_name + " " + lawyer.user.last_name
        payload["lawyer_email"] = lawyer.user.email
        payload["notify_user_id"] = notify_user_id
        payload["customer_name"] = customer_name

        # Convert declined_reason JSON to a list
        decline_reason_json = result["match"].declined_reason or {}
        decline_reasons = []


        # Add all items from the "reason" list, if present
        if isinstance(decline_reason_json.get("reason"), list):
            decline_reasons.extend(decline_reason_json["reason"])


        # Decline reason other
        if isinstance(decline_reason_json.get("reason_other"), str):
            decline_resons_other = decline_reason_json["reason_other"]
        else:
            decline_resons_other = None


        payload["decline_reason"] = decline_reasons
        payload["decline_reason_other"] = decline_resons_other
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload["case_id"] = case.id
        payload["lawyer_id"] = lawyer_id
        payload["notify_user_id"] = lawyer.user.id


        navigator_emails = get_all_navigator_emails(db)
        payload["navigators"] = navigator_emails

        should_display = True
        message = result["message"]
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = True

        data = {
            str(ComponentEnum.CASE_NEW_MATCH_LAW_CARD.value): {"match_status": MatchStatusEnum.DECLINED.value}
        }
        result = update_timeline_event(db, f"{case_id}_{lawyer_id}", data)
        if not result:
            logger.error(f"Failed to update timeline event for {case_id}_{lawyer_id}")
            # raise ValueError("Failed to update timeline event")  # noqa: TRY301

        # Disable decline_match button in CASE_NEW_LAW_CARD timeline event
        disable_timeline_action_buttons(
            db=db,
            component_buttons={
                str(ComponentEnum.CASE_NEW_MATCH_LAW_CARD.value): ["decline_match","raise_interest"],
                str(ComponentEnum.CASE_MORE_DETAILS_LAW_CARD.value): ["decline_match","raise_interest"],
                str(ComponentEnum.CASE_DECLINE_LAW_CARD.value): ["raise_interest"]
            },
            related_id=f"{case_id}_{lawyer_id}",
        )

        return EventResponseData(
            should_display=should_display,
            success=True,
            message=message,
            data=[],
        )


    except Exception as e:
        logger.exception(f"Error in handle_case_decline: {e}")
        raise


@event(EventType.CASE_SUMMARY_UPDATE) # type: ignore
async def handle_case_summary_update(
   db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
   """
   Handle case summary update
   """
   try:
       payload = event.payload
       required_keys = ["case_id", "case_summary", "is_update_summary"]
       validation = validate_event_payload(payload, required_keys) # type: ignore
       if not validation["status"]:
           logger.error(
               f"Payload validation failed for {event.event_type.value}: {validation}"
           )
           raise ValueError("Required keys not found in payload")  # noqa: TRY301

       case_id = int(payload["case_id"])
       case_summary = payload["case_summary"]

       timestamp = datetime.now(timezone.utc).isoformat()

       case = get_case_by_id(db, case_id)

       if case is None:
           raise ValueError("Case not found")  # noqa: TRY301

       previous_case_summary = None
       if case.summary is not None:
            previous_case_summary = case.summary

       payload["timestamp"] = timestamp
       payload["case_number"] = format_case_number(case.case_no)
       payload["case_type"] = case.case_type
       payload["previous_case_summary"] = previous_case_summary

       update_case_summary_service(db, case_id, case_summary)

       should_display = False
       if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
           should_display = False

       return EventResponseData(
           should_display=should_display,
           success=True,
           message="Case summary updated successfully",
           data=[],
       )


   except Exception as e:
       logger.exception(f"Error in handle_case_summary_update: {e}")
       raise


@event(EventType.ARCHIVE_CASE) # type: ignore[misc]
async def handle_archive_case(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle archive case event.
    Archives one or more cases by setting their status to ARCHIVED.
    
    Required payload:
    {
        "case_ids": [list of case IDs] OR "cases": [list of Case objects]
    }
    """
    try:
        payload = event.payload
        # required_keys = []
        # validation = validate_event_payload(payload, required_keys)  # type: ignore
        # if not validation["status"]:
        #     logger.error(f"Payload validation failed for {event.event_type.value}: {validation}")
        #     raise ValueError("Invalid payload structure")  # noqa: TRY301

        archived_cases = []
        
        # Handle case_ids if provided
        if "case_ids" in payload:
            case_ids = payload["case_ids"]
            if not isinstance(case_ids, list):
                raise ValueError("case_ids must be a list")  # noqa: TRY301
            
            if not case_ids:
                logger.warning("Empty case_ids list provided")
            else:
                # Fetch all cases in a single query using IN clause
                cases = db.query(Case).filter(Case.id.in_(case_ids)).all()
                
                # Track which IDs were found
                found_ids = {case.id for case in cases}
                missing_ids = set(case_ids) - found_ids
                
                if missing_ids:
                    logger.warning(f"Cases with IDs {missing_ids} not found, skipping")
                
                # Archive all found cases
                for case in cases:
                    case.status = CaseStatusEnum.ARCHIVED
                    archived_cases.append(case)
                    db.add(case)
                payload["cases"] = cases
        # Handle cases if provided (direct Case objects)
        elif "cases" in payload:
            cases = payload["cases"]
            if not isinstance(cases, list):
                raise ValueError("cases must be a list")  # noqa: TRY301
            
            for case in cases:
                if case is None:
                    continue
                case.status = CaseStatusEnum.ARCHIVED
                archived_cases.append(case)
                db.add(case)
        else:
            raise ValueError("Either 'case_ids' or 'cases' must be provided in payload")  # noqa: TRY301

        timestamp = datetime.now(timezone.utc).isoformat()
        payload["timestamp"] = timestamp
        # Commit the changes
        if archived_cases:
            db.commit()
            logger.info(f"Successfully archived {len(archived_cases)} case(s)")
        else:
            logger.warning("No cases were archived")

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            should_display = True

        return EventResponseData(
            should_display=should_display,
            success=True,
            message=f"Successfully archived {len(archived_cases)} case(s)",
            data={"archived_count": len(archived_cases)},
        )

    except Exception as e:
        logger.exception(f"Error in handle_archive_case: {e}")
        raise


@event(EventType.UNARCHIVE_CASE) # type: ignore[misc]
async def handle_unarchive_case(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle unarchive case event.
    Unarchives one or more cases by setting their status to OPEN.
    
    Required payload:
    {
        "case_ids": [list of case IDs] OR "cases": [list of Case objects]
    }
    """
    from app.db.models import CaseCustomer, Customer
    from sqlalchemy.orm import joinedload
    try:
        payload = event.payload
        unarchive_cases = []
        
        # Handle case_ids if provided
        if "case_ids" in payload:
            case_ids = payload["case_ids"]
            if not isinstance(case_ids, list):
                raise ValueError("case_ids must be a list")  # noqa: TRY301
            
            if not case_ids:
                logger.warning("Empty case_ids list provided")
            else:
                # Fetch all cases in a single query using IN clause
                cases = db.query(Case).filter(Case.id.in_(case_ids)).all()
                
                # Track which IDs were found
                found_ids = {case.id for case in cases}
                missing_ids = set(case_ids) - found_ids
                
                if missing_ids:
                    logger.warning(f"Cases with IDs {missing_ids} not found, skipping")
                
                # Archive all found cases
                for case in cases:
                    case_customers = case.case_customers
                    customer_id = case_customers[0].customer_id

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
                            CaseCustomer.customer_id == customer_id,
                        )
                        .all()
                    )
                    existing_kyc_completed_cases = [case for case in existing_cases if case.is_kyc_completed]
                    existing_open_cases = list(set(existing_cases) - set(existing_kyc_completed_cases))
                    if existing_open_cases or existing_kyc_completed_cases:
                        raise ValueError(f"Case {case.case_no} cannot be unarchived: Customer has already an opened case")  # noqa: TRY301

                    if case.status == CaseStatusEnum.OPEN:
                        raise ValueError("Case is already unarchived")  # noqa: TRY301
                    case.status = CaseStatusEnum.OPEN
                    unarchive_cases.append(case)
                    db.add(case)
                payload["cases"] = cases
        # Handle cases if provided (direct Case objects)
        elif "cases" in payload:
            cases = payload["cases"]
            if not isinstance(cases, list):
                raise ValueError("cases must be a list")  # noqa: TRY301
            
            for case in cases:
                if case is None:
                    continue

                case_customers = case.case_customers
                customer_id = case_customers[0].customer_id

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
                        CaseCustomer.customer_id == customer_id,
                    )
                    .all()
                )
                existing_kyc_completed_cases = [case for case in existing_cases if case.is_kyc_completed]
                existing_open_cases = list(set(existing_cases) - set(existing_kyc_completed_cases))
                if existing_open_cases or existing_kyc_completed_cases:
                    raise ValueError(f"Case {case.case_no} cannot be unarchived: Customer has already an opened case")  # noqa: TRY301

                if case.status == CaseStatusEnum.OPEN:
                    raise ValueError("Case is already unarchived")  # noqa: TRY301
                case.status = CaseStatusEnum.OPEN
                unarchive_cases.append(case)
                db.add(case)
        else:
            raise ValueError("Either 'case_ids' or 'cases' must be provided in payload")  # noqa: TRY301

        timestamp = datetime.now(timezone.utc).isoformat()
        payload["timestamp"] = timestamp
        # Commit the changes
        if unarchive_cases:
            db.commit()
            logger.info(f"Successfully unarchived {len(unarchive_cases)} case(s)")
        else:
            logger.warning("No cases were unarchived")

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            should_display = True

        return EventResponseData(
            should_display=should_display,
            success=True,
            message=f"Successfully unarchived {len(unarchive_cases)} case(s)",
            data={"unarchived_count": len(unarchive_cases)},
        )

    except Exception as e:
        logger.exception(f"Error in handle_unarchive_case: {e}")
        raise


@event(EventType.CASE_UNARCHIVED_NN_CARD)  # type: ignore
async def handle_case_unarchived_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case unarchive navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "timestamp": "2021-01-01T00:00:00Z",
        "cases": [<list of case objects>],
    }
    """
    try:
        payload = event.payload
        required_keys = ["timestamp", "cases"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Unarchive Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Unarchive Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        timestamp = payload["timestamp"]
        cases = payload["cases"]
        role_code = UserRoleEnum.NAVIGATOR.value
        if not cases or not isinstance(cases, list):
            raise ValueError("Case Unarchive Navigator Card event: Cases must be a non-empty list")  # noqa: TRY301

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_UNARCHIVED_NN_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_UNARCHIVED_NN_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case Unarchive Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Prepare action_by if current_user exists
        action_by = ""
        if event.current_user:
            first_name = event.current_user.first_name if event.current_user.first_name is not None else ""
            last_name = event.current_user.last_name if event.current_user.last_name is not None else ""
            action_by = first_name + " " + last_name

        # Process each case and create cards
        card_data_list = []
        for idx, case_obj in enumerate(cases, start=1):
            try:
                case_id = int(case_obj.id) if hasattr(case_obj, "id") else None
                if case_id is None:
                    continue

                # Get case_number from case object
                case_number = None
                if hasattr(case_obj, "case_no") and case_obj.case_no is not None:
                    case_number = format_case_number(str(case_obj.case_no))
                elif hasattr(case_obj, "case_number"):
                    case_number = case_obj.case_number

                # Get customer_name from Case
                customer_name = ""
                if (
                    hasattr(case_obj, "case_customers")
                    and case_obj.case_customers
                    and len(case_obj.case_customers) > 0
                    and case_obj.case_customers[0].customer
                    and case_obj.case_customers[0].customer.user
                ):
                    first_name = case_obj.case_customers[0].customer.user.first_name or ""
                    last_name = case_obj.case_customers[0].customer.user.last_name or ""
                    customer_name = f"{first_name} {last_name}".strip()
                
                if not customer_name:
                    continue

                if not case_number:
                    continue

                # Prepare placeholder values for this case
                placeholder_values = {
                    "action_by": action_by,
                    "case_number": case_number,
                    "timestamp": timestamp,
                    "customer_name": customer_name if customer_name is not None else "",
                }

                # Replace placeholders in template
                errors: list[str] = []
                card_data = replace_placeholders(template, placeholder_values, errors)

                if errors:
                    logger.error(
                        f"Case Archive Navigator Card event: Template placeholder errors for case {case_id}: {errors}"
                    )
                    continue

                # Save timeline event for this case
                save_timeline_event(
                    db=db,
                    case_id=case_id,
                    timeline_type=timeline_type,
                    meta_data=card_data,
                )

                disable_timeline_action_buttons(
                    db=db,
                    component_buttons={
                        str(ComponentEnum.CASE_ARCHIVED_NN_CARD.value): ["unarchive"],
                    },
                    related_id=int(case_id),
                )

                card_data_list.append(card_data)

            except Exception as case_error:
                logger.exception(
                    f"Case Archive Navigator Card event: Error processing case: {case_error}"
                )
                continue

        if not card_data_list:
            raise ValueError("Case Archive Navigator Card event: No valid cases processed")  # noqa: TRY301

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            should_display = True
        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Card generated and saved to timeline successfully.",
            data=card_data_list[0],
        )

    except Exception as e:
        logger.exception(f"Case Archive Navigator Card event: Error in handle_case_archive_nn_card: {e}")
        raise


@event(EventType.CASE_SUMMARY_UPDATE_NN_CARD) # type: ignore
async def handle_case_summary_update_nn_card(
   db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
   """
   Handle case summary update navigator card event: Generate card JSON using template and save to timeline_event table.
   Required payload:
   {
       "case_id": "1",
       "case_number": "CASE-001",
       "case_type": "Family Law",
       "case_summary": "Updated case summary text",
       "previous_case_summary": "Previous case summary text" | None,
       "timestamp": "2021-01-01T00:00:00Z",
       "is_update_summary": True
   }
   """
   try:
       payload = event.payload
       required_keys = ["case_id", "case_summary", "timestamp", "case_number", "case_type", "is_update_summary"]
       validation = validate_event_payload(payload, required_keys) # type: ignore
       if not validation["status"]:
           logger.error(
               f"Case Summary Update Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
           )
           raise ValueError("Case Summary Update Navigator Card event: Required keys not found in payload")  # noqa: TRY301

       is_update_summary = payload["is_update_summary"]
       previous_case_summary = payload["previous_case_summary"]
       case_id = payload["case_id"]
       case_number = payload["case_number"]
       case_type = payload["case_type"]
       case_summary = payload["case_summary"]
       timestamp = payload["timestamp"]
       role_code = UserRoleEnum.NAVIGATOR.value

    #    if is_update_summary and previous_case_summary is None:
    #        raise ValueError("Case Summary Update Navigator Card event: Previous case summary is required")

       # Validate case_id format and convert to int
       try:
           case_id = int(case_id)
       except (ValueError, TypeError) as e:
           raise ValueError("Case Summary Update Navigator Card event: Invalid case ID format") from e

       template, last_version = get_template_json(str(ComponentEnum.CASE_SUMMARY_UPDATE_NN_CARD.value), str(role_code), "timeline")

       timeline_type = get_timeline_type(db, ComponentEnum.CASE_SUMMARY_UPDATE_NN_CARD.value, role_code, last_version)
       if timeline_type is None:
           raise ValueError("Case Summary Update Navigator Card event: Timeline type not found")  # noqa: TRY301

       # Prepare action_by if current_user exists
       action_by = ""
       if event.current_user:
           first_name = event.current_user.first_name if event.current_user.first_name is not None else ""
           last_name = event.current_user.last_name if event.current_user.last_name is not None else ""
           action_by = first_name + " " + last_name

       # Prepare placeholder values
       placeholder_values = {
           "action_by": action_by,
           "case_number": case_number,
           "case_type": case_type,
           "current_case_summary": case_summary,
           "previous_case_summary": previous_case_summary,
           "timestamp": timestamp
       }

       # Replace placeholders in template
       errors: list[str] = []
       card_data = replace_placeholders(template, placeholder_values, errors)

       if errors:
           logger.error(f"Case Summary Update Navigator Card event: Template placeholder errors: {errors}")
           raise ValueError(f"Case Summary Update Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

       # Save timeline event
       # Use event.current_user.id if available, otherwise fall back to event.user_id
       action_user_id = None
       if event.current_user and hasattr(event.current_user, 'id'):
           action_user_id = int(event.current_user.id)
       elif event.user_id:
           action_user_id = int(event.user_id)
       
       save_timeline_event(
           db=db,
           case_id=case_id,
           timeline_type=timeline_type,
           meta_data=card_data,
           action_user_id=action_user_id
       )

       should_display = False
       if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
           should_display = True

       return EventResponseData(
           should_display=should_display,
           success=True,
           message="Case summary update navigator card generated and saved to timeline successfully.",
           data=card_data
       )

   except Exception as e:
       logger.exception(f"Case Summary Update Navigator Card event: Error in handle_case_summary_update_nn_card: {e}")
       raise


@event(EventType.CASE_ARCHIVED_NN_CARD)  # type: ignore
async def handle_case_archive_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case archive navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "timestamp": "2021-01-01T00:00:00Z",
        "cases": [<list of case objects>],
        "new_case_number": "#1234567890", # optional
        "new_case_id": "1", # optional,
        "manual_archive": True # optional
    }
    """
    try:
        payload = event.payload
        required_keys = ["timestamp", "cases"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Archive Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Archive Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        timestamp = payload["timestamp"]
        cases = payload["cases"]
        role_code = UserRoleEnum.NAVIGATOR.value
        new_case_number = None
        new_case_id = None
        if "new_case_number" in payload:
            new_case_number = payload["new_case_number"]
        if "new_case_id" in payload:
            new_case_id = payload["new_case_id"]
            if new_case_id is not None:
                if isinstance(new_case_id, int) or (isinstance(new_case_id, str) and str(new_case_id).isdigit()):
                    new_case_id = encrypt_id(str(new_case_id))
            else:
                new_case_id = None

        action_by = ""
        if "manual_archive" in payload:
            manual_archive = payload["manual_archive"]
            # Prepare action_by if current_user exists            
            if event.current_user:
                first_name = event.current_user.first_name if event.current_user.first_name is not None else ""
                last_name = event.current_user.last_name if event.current_user.last_name is not None else ""
                action_by = first_name + " " + last_name
        else:
            manual_archive = False

        if not cases or not isinstance(cases, list):
            raise ValueError("Case Archive Navigator Card event: Cases must be a non-empty list")  # noqa: TRY301

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_ARCHIVED_NN_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_ARCHIVED_NN_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case Archive Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Process each case and create cards
        card_data_list = []
        for idx, case_obj in enumerate(cases, start=1):
            try:
                case_id = int(case_obj.id) if hasattr(case_obj, "id") else None
                if case_id is None:
                    continue

                # Get case_number from case object
                case_number = None
                if hasattr(case_obj, "case_no") and case_obj.case_no is not None:
                    case_number = format_case_number(str(case_obj.case_no))
                elif hasattr(case_obj, "case_number"):
                    case_number = case_obj.case_number

                # Get customer_name from Case
                customer_name = ""
                if (
                    hasattr(case_obj, "case_customers")
                    and case_obj.case_customers
                    and len(case_obj.case_customers) > 0
                    and case_obj.case_customers[0].customer
                    and case_obj.case_customers[0].customer.user
                ):
                    first_name = case_obj.case_customers[0].customer.user.first_name or ""
                    last_name = case_obj.case_customers[0].customer.user.last_name or ""
                    customer_name = f"{first_name} {last_name}".strip()
                
                if not customer_name:
                    continue

                if not case_number:
                    continue

                action_buttons = {}
                if new_case_id:
                    action_buttons = {"view_case": True}
                else:
                    action_buttons = {}
                
                if manual_archive:
                    action_buttons = {"unarchive": True}

                # Prepare placeholder values for this case
                placeholder_values = {
                    "action_by": action_by,
                    "case_number": case_number,
                    "timestamp": timestamp,
                    "customer_name": customer_name if customer_name is not None else "",
                    "new_case_number": new_case_number if new_case_number is not None else "",
                    "new_case_id": new_case_id if new_case_id is not None else "",
                    "manual_archive": manual_archive,
                    "action_buttons": action_buttons,
                }

                # Replace placeholders in template
                errors: list[str] = []
                card_data = replace_placeholders(template, placeholder_values, errors)

                if errors:
                    logger.error(
                        f"Case Archive Navigator Card event: Template placeholder errors for case {case_id}: {errors}"
                    )
                    continue

                # Save timeline event for this case
                timeline_event = save_timeline_event(
                    db=db,
                    case_id=case_id,
                    timeline_type=timeline_type,
                    meta_data=card_data,
                )

                if manual_archive:
                    save_timeline_map(db, int(timeline_event.id), str(timeline_type.type_name), int(case_id))

                card_data_list.append(card_data)

            except Exception as case_error:
                logger.exception(
                    f"Case Archive Navigator Card event: Error processing case: {case_error}"
                )
                continue

        if not card_data_list:
            raise ValueError("Case Archive Navigator Card event: No valid cases processed")  # noqa: TRY301

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            should_display = True
        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Card generated and saved to timeline successfully.",
            data=card_data_list[0],
        )

    except Exception as e:
        logger.exception(f"Case Archive Navigator Card event: Error in handle_case_archive_nn_card: {e}")
        raise


@event(EventType.GENERATE_AI_CASE_SUMMARY) # type: ignore
async def handle_generate_ai_case_summary(
   db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Generate AI case summary for the case.
    Required payload:
    {
        "case_id": 1
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id"]
        validation = validate_event_payload(payload, required_keys) # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301
        details = {}
        case_id = payload["case_id"]
        case = get_case_by_id(db, case_id)
        if not case:
            raise ValueError("Case not found")  # noqa: TRY301
        
        case_type = case.case_type
        if case_type is None:
            raise ValueError("Case type not found")
        
        details["case_details"] = {
            "case_number": format_case_number(case.case_no),
            "case_type": case.case_type.value if case.case_type else "Family Law",
            "case_status": case.status.value if case.status else "Open",
            "case_created_at": case.created_at.isoformat() if case.created_at else None,
            "case_updated_at": case.updated_at.isoformat() if case.updated_at else None,
        }

        if case.is_triage is True:
            from app.db.services.triage import get_triage_from_case_id, format_triage_answers
            from app.db.models.user import User
            from app.db.models.triage import Triage

            triage = get_triage_from_case_id(db, case_id)
            if triage is None:
                raise ValueError("Triage not found")  # noqa: TRY301            
            user = db.query(User).join(Triage, User.id == Triage.user_id).filter(Triage.id == triage.id).first()
            if user is None:
                raise ValueError("User not found")  # noqa: TRY301
            customer_name = f"{user.first_name} {user.last_name}".strip()
            triage_answers = format_triage_answers(db, triage, customer_name)
            details["triage_details"] = {
                "customer_name": customer_name,
                "triage_answers": triage_answers,
            }

        else:
            resolve = get_resolve_from_case_id(db, case_id)
            if resolve is None:
                raise ValueError("Resolve not found")  # noqa: TRY301
            
            resolve_answers = format_resolve_question_answers(db, resolve)
            details["resolve_answers"] = resolve_answers
            resolve_result = get_result(resolve)
            details["resolve_result"] = {
                "title": resolve_result["title"],
                "summary": resolve_result["summary"],
                "version": resolve_result["version"],
            }

            details["recommended_approach"] = {
                "title": resolve_result["recommended_approach"]["title"],
                "summary": resolve_result["recommended_approach"]["summary"],
                "version": resolve_result["recommended_approach"]["version"],
            }

        details["kyc_details"] = {}
        if case.is_kyc_completed is True:
            kyc_answers = format_kyc_answers(db, case_id)
            details["kyc_details"] = kyc_answers

        ai_case_summary = await generate_ai_case_summary(case, case_type, details, model="gpt-4.1-mini")
        payload["is_update_summary"] = False
        payload["case_summary"] = ai_case_summary.get("case_summary", [])
        status = ai_case_summary.get("status", False)
        if status is False:
            case.is_ai_summary_generated = False
            db.commit()

            from app.events.dispatcher import event_dispatcher
            from app.utils.helpers import extract_status_messages

            event_data = Event(
                event_type=EventType.AI_SUMMARY_FAILED_NN_EMAIL,
                payload={"case": case},
                user_id=int(event.user_id) if event.user_id else None,
                current_user=event.current_user if event.current_user else None,
            )
            await event_dispatcher.dispatch_event(db, event_data)
            success, messages = extract_status_messages(event_data.response)
            if not success:
                raise ValueError("Failed to send AI summary failed navigator notification email.")  # noqa: TRY301

            raise ValueError("AI summary generation failed. Please try again later.")  # noqa: TRY301
        
        case.is_ai_summary_generated = True
        db.commit()
        # if not status:
        #     return EventResponseData(
        #         success=False,
        #         message="AI summary generation failed. Please try again later.",
        #         data=ai_case_summary.get("case_summary", []),
        #     )

        return EventResponseData(
            success=True,
            message="AI case summary generated successfully",
            data=ai_case_summary["case_summary"],
        )
    except Exception as e:
        logger.exception(f"Error in generate_ai_case_summary: {e}")
        raise

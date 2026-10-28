"""
Resolve Event Handlers

This module contains handlers for resolve-related events.

All event handlers are decorated with @event and automatically registered.
"""

import json
import logging

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email import email_service
from app.db.services.general import get_all_navigator_emails, invoke_dispatch_event
from app.db.services.question_answers import get_resolve_result, validate_save_answer
from app.db.services.resolve import get_resolve_by_id
from app.enums.events import EventType
from app.enums.resolve import ResolveStatusEnum
from app.events.dispatcher import event
from app.schemas.v1.event import Event, EventResponseData
from app.schemas.v1.resolve import ResolveSubmitResponseData
from app.utils.validators import validate_event_payload
from app.websocket.manager import WebSocketManager
from app.enums.user_role import UserRoleEnum

logger = logging.getLogger(__name__)


@event(EventType.RESOLVE_SUBMIT) # type: ignore
async def handle_resolve_submit(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle resolve submit: Send email to customer and navigators.
    """
    from app.db.services.ai import generate_ai_recommendation
    from app.db.services.resolve import format_resolve_question_answers
    try:
        payload = event.payload
        # required_keys = ["resolve", "result"]
        required_keys = ["request_data"]
        validation = validate_event_payload(payload, required_keys) # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        request = payload["request_data"]
        try:
            resolve_id = int(request.resolve_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Resolve Submit event: Invalid resolve ID format") from e

        try:
            with open(settings.QUESTIONS_FILE_PATH) as f:
                questions = json.load(f)
        except Exception as e:
            raise ValueError("Resolve Submit event: Failed to load resolve questions") from e

        resolve_map = None
        with open(settings.RESOLVE_MAP_FILE_PATH) as f:
            resolve_map = json.load(f)

        if not resolve_map:
            raise ValueError("Nova Recommendations Submit event: Failed to load resolve map")

        # Check if resolve exists
        resolve = get_resolve_by_id(db, resolve_id)
        if resolve is None:
            raise ValueError("Nova Recommendations Submit event: Nova Recommendations not found") # noqa: TRY301

        result, errors = validate_save_answer(db, resolve, request, questions, resolve_map)
        if result is False:
            errors_str = ", ".join(error for error in errors if error)
            raise ValueError(f"Resolve Submit event: {errors_str}") # noqa: TRY301

        resolve_result = get_resolve_result(db, resolve, questions)
        # if not result:
        #     raise ValueError("Resolve Submit event: Failed to get resolve result")

        resolve.result_reference_id = str(resolve_result.get("result_type", ""))
        resolve.result_version = str(resolve_result.get("version", ""))
        details = {}
        resolve_answers = format_resolve_question_answers(db, resolve)
        details["resolve_answers"] = resolve_answers
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
        ai_recommendation = await generate_ai_recommendation(details)
        formatted_recommendations = {
            item["title"]: item["description"]
            for item in ai_recommendation.get("personalised_analysis", [])
            if item.get("title") and item.get("description")
        }
        resolve.personalised_ai_recommendation = formatted_recommendations
        resolve.recommended_approach = str(resolve_result.get("recommended_approach",{}).get("result_type", ""))
        resolve_result["recommended_approach"]["recommendations"] = formatted_recommendations

        resolve.result_reference_id = str(resolve_result.get("result_type", ""))  # type: ignore[assignment]
        resolve.result_version = str(resolve_result.get("version", ""))  # type: ignore[assignment]
        # new_title: str = str(resolve_result.get("title", ""))
        new_title: str = str(resolve_result.get("recommended_approach", {}).get("title", ""))  # type: ignore[assignment]
        old_title: str = resolve.title if resolve.title is not None else ""  # type: ignore[assignment]
        # Remove "Resolve Session" if present and strip whitespace
        cleaned_old_title: str = old_title.replace("Resolve Session - ", "").strip()
        cleaned_old_title: str = old_title.replace("Nova Recommendations - ", "").strip()
        if resolve.customer_email:
            cleaned_old_title = resolve.customer_email
        elif resolve.customer_name:
            cleaned_old_title = resolve.customer_name
        # Only add separator if both parts are non-empty
        if new_title and cleaned_old_title:
            resolve.title = f"{new_title} - {cleaned_old_title}"  # type: ignore[assignment]
        elif new_title:
            resolve.title = new_title  # type: ignore[assignment]
        elif cleaned_old_title:
            resolve.title = cleaned_old_title  # type: ignore[assignment]
        else:
            resolve.title = ""  # type: ignore[assignment]
        #update resolve status to completed
        resolve.status = ResolveStatusEnum.COMPLETED  # type: ignore[assignment]
        db.commit()

        customer_name = resolve.customer_name
        customer_email = resolve.customer_email
        if not customer_name or not customer_email:
            if resolve.resolve_question_answers:
                for rqa in resolve.resolve_question_answers:
                    qa = rqa.question_answer
                    qid = str(qa.question_identifier)
                    if qid == "1":
                        try:
                            customer_name = json.loads(qa.answer)[0].get("value")
                        except Exception:
                            customer_name = None
                    if qid == "21":
                        try:
                            customer_email = json.loads(qa.answer)[0].get("value")
                        except Exception:
                            customer_email = None

        payload["customer_name"] = customer_name
        payload["customer_email"] = customer_email
        payload["resolve"] = resolve
        payload["result"] = resolve_result["recommended_approach"]


        navigator_emails = get_all_navigator_emails(db)
        payload["navigators"] = navigator_emails

        return_data = {
            "resolve_id": resolve.id,
            "result": resolve_result["recommended_approach"],
        }
        response_data = ResolveSubmitResponseData.model_validate(return_data)

        should_display = True
        if resolve.result_reference_id != resolve.recommended_approach:
            message = "This recommendation reflects your responses, including practical and cost considerations. You can revisit your answers at any time to explore other pathways."
        else:
            message = "Your personalised recommendation is ready."
        # if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
        #     should_display = True
        return EventResponseData(
            should_display=should_display,
            success=True,
            message=message,
            data=response_data,
        )

    except Exception as e:
        logger.exception(f"Error in handle_resolve_submit: {e}")
        raise


@event(EventType.RESOLVE_RESUBMIT) # type: ignore
async def handle_resolve_resubmit(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle resolve resubmit: Send email to customer and navigators.
    """
    # from app.db.services.case import get_case_by_customer_id
    from app.enums.case import CaseStatusEnum
    from app.db.services.ai import generate_ai_recommendation
    from app.db.services.resolve import format_resolve_question_answers
    from app.utils.formatters import extract_name_parts
    from app.enums.base import NameExtractionOption
    from app.utils.encryption import encrypt_id
    from app.utils.formatters import format_case_number
    from datetime import datetime, timezone
    from app.db.services.timeline_event import update_timeline_metadata
    from app.enums.component import ComponentEnum

    try:
        payload = event.payload
        # required_keys = ["resolve", "result"]
        required_keys = ["request_data"]
        validation = validate_event_payload(payload, required_keys) # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        request = payload["request_data"]
        try:
            resolve_id = int(request.resolve_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Resolve Submit event: Invalid resolve ID format") from e

        try:
            with open(settings.QUESTIONS_FILE_PATH) as f:
                questions = json.load(f)
        except Exception as e:
            raise ValueError("Resolve Submit event: Failed to load resolve questions") from e

        resolve_map = None
        with open(settings.RESOLVE_MAP_FILE_PATH) as f:
            resolve_map = json.load(f)

        if not resolve_map:
            raise ValueError("Nova Recommendations Submit event: Failed to load resolve map")

        # Check if resolve exists
        resolve = get_resolve_by_id(db, resolve_id)
        if resolve is None:
            raise ValueError("Nova Recommendations Submit event: Nova Recommendations not found") # noqa: TRY301
        
        case = resolve.case_resolves[0].case
        if case is None:
            raise ValueError("Nova Recommendations Submit event: Case not found") # noqa: TRY301
        
        if case.status != CaseStatusEnum.OPEN:
            raise ValueError("Nova Recommendations Submit event: Case is not open") # noqa: TRY301
        
        if case.is_kyc_completed:
            raise ValueError("Nova Recommendations Submit event: Case is already linked to a customer with KYC completed") # noqa: TRY301
        
        payload["case_id"] = case.id

        result, errors = validate_save_answer(db, resolve, request, questions, resolve_map)
        if result is False:
            errors_str = ", ".join(error for error in errors if error)
            raise ValueError(f"Resolve Submit event: {errors_str}") # noqa: TRY301

        resolve_result = get_resolve_result(db, resolve, questions)

        resolve.result_reference_id = str(resolve_result.get("result_type", ""))
        resolve.result_version = str(resolve_result.get("version", ""))
        details = {}
        resolve_answers = format_resolve_question_answers(db, resolve)
        details["resolve_answers"] = resolve_answers
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
        ai_recommendation = await generate_ai_recommendation(details)
        formatted_recommendations = {
            item["title"]: item["description"]
            for item in ai_recommendation.get("personalised_analysis", [])
            if item.get("title") and item.get("description")
        }
        resolve.personalised_ai_recommendation = formatted_recommendations
        resolve.recommended_approach = str(resolve_result.get("recommended_approach",{}).get("result_type", ""))

        resolve_result["recommended_approach"]["recommendations"] = formatted_recommendations
        # db.commit()
        # db.refresh(resolve)

        resolve.result_reference_id = str(resolve_result.get("result_type", ""))  # type: ignore[assignment]
        resolve.result_version = str(resolve_result.get("version", ""))  # type: ignore[assignment]
        # new_title: str = str(resolve_result.get("title", ""))
        new_title: str = str(resolve_result.get("recommended_approach", {}).get("title", ""))  # type: ignore[assignment]
        old_title: str = resolve.title if resolve.title is not None else ""  # type: ignore[assignment]
        # Remove "Resolve Session" if present and strip whitespace
        cleaned_old_title: str = old_title.replace("Resolve Session - ", "").strip()
        cleaned_old_title: str = old_title.replace("Nova Recommendations - ", "").strip()
        if resolve.customer_email:
            cleaned_old_title = resolve.customer_email
        elif resolve.customer_name:
            cleaned_old_title = resolve.customer_name
        # Only add separator if both parts are non-empty
        if new_title and cleaned_old_title:
            resolve.title = f"{new_title} - {cleaned_old_title}"  # type: ignore[assignment]
        elif new_title:
            resolve.title = new_title  # type: ignore[assignment]
        elif cleaned_old_title:
            resolve.title = cleaned_old_title  # type: ignore[assignment]
        else:
            resolve.title = ""  # type: ignore[assignment]
        #update resolve status to completed
        resolve.status = ResolveStatusEnum.COMPLETED  # type: ignore[assignment]
        db.commit()

        customer_name = resolve.customer_name
        customer_email = resolve.customer_email
        if not customer_name or not customer_email:
            if resolve.resolve_question_answers:
                for rqa in resolve.resolve_question_answers:
                    qa = rqa.question_answer
                    qid = str(qa.question_identifier)
                    if qid == "1":
                        try:
                            customer_name = json.loads(qa.answer)[0].get("value")
                        except Exception:
                            customer_name = None
                    if qid == "21":
                        try:
                            customer_email = json.loads(qa.answer)[0].get("value")
                        except Exception:
                            customer_email = None

        from app.db.services.user import update_user_generic
        from app.schemas.v1.user import UserUpdateRequest
        from app.db.models.user import User
        from app.db.models.customer import Customer

        parts = customer_name.split()
        if len(parts) >= 2:
            first_name = parts[0]
            last_name = " ".join(parts[1:])
        else:
            first_name = parts[0] if len(parts) == 1 else "."
            last_name = "."
        user = db.query(User).join(Customer, User.id == Customer.user_id, isouter=True).filter(Customer.id == resolve.customer_id).first()
        if user:
            update_user_generic(db, user.id, UserUpdateRequest(first_name=first_name, last_name=last_name))
        else:
            raise ValueError("Nova Recommendations Submit event: User not found") # noqa: TRY301

        payload["customer_name"] = customer_name
        payload["customer_email"] = customer_email
        payload["resolve"] = resolve
        payload["result"] = resolve_result["recommended_approach"]

        navigator_emails = get_all_navigator_emails(db)
        payload["navigators"] = navigator_emails

        action_by = f"{event.current_user.first_name} {event.current_user.last_name}".strip() if event.current_user.last_name is not None else ""
        customer_first_name = extract_name_parts(customer_name, NameExtractionOption.FIRST)
        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "first_name": customer_first_name,
            "title": details.get("recommended_approach", {}).get("title", ""),
            "summary": details.get("recommended_approach", {}).get("summary", ""),
            "recommendations": formatted_recommendations,
            "resolve_id": encrypt_id(str(resolve_id)) if resolve_id else None,
            "kyc_id": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "case_number": format_case_number(str(case.case_no)),
            "action_buttons": {
                "view_resolve": True,
                "view_kyc": True,
            },
        }

        update_timeline_metadata(db, case.id, ComponentEnum.CASE_PATHWAY_OVERVIEW_CUS_CARD.value, placeholder_values)

        return_data = {
            "resolve_id": resolve.id,
            "result": resolve_result["recommended_approach"],
        }
        response_data = ResolveSubmitResponseData.model_validate(return_data)

        should_display = True
        message = "Your personalised recommendation is updated."
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = True
            if resolve.result_reference_id != resolve.recommended_approach:
                message = "This recommendation reflects your responses, including practical and cost considerations. You can revisit your answers at any time to explore other pathways."
            else:
                message = "Your personalised recommendation is updated."
        

        # current_user_id = int(event.current_user.id) if event.current_user else None
        # dispatch the event to generate the AI case summary
        invoke_dispatch_event(event_type=EventType.GENERATE_AI_CASE_SUMMARY, payload=payload, user_id=None, current_user_id=None)

        return EventResponseData(
            should_display=should_display,
            success=True,
            message=message,
            data=response_data,
        )

    except Exception as e:
        logger.exception(f"Error in handle_resolve_submit: {e}")
        raise


@event(EventType.RESOLVE_CUS_EMAIL)  # type: ignore
async def send_resolve_customer_notification_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send an email to the customer after resolve is completed with the result.

    Example payload:
    {
        "customer_email": "user@example.com",
        "customer_name": "JohnDoe",
        "result": "Resolve result",
        "resolve": <Resolve object>
    }
    """
    from app.db.services.case import get_case_by_customer_id
    from app.core.security import create_analytics_token
    try:

        payload = event.payload
        required_keys = ["customer_email", "customer_name", "result", "resolve"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        email = payload.get("customer_email")
        customer_name = payload.get("customer_name")
        from app.utils.formatters import extract_name_parts
        from app.enums.base import NameExtractionOption
        customer_name = extract_name_parts(customer_name, NameExtractionOption.FIRST)
        result_of_resolve = payload.get("result")

        if not isinstance(email, str) or email.strip() == "":
            raise ValueError("Invalid customer email in payload")  # noqa: TRY301
        if not isinstance(customer_name, str) or customer_name.strip() == "":
            raise ValueError("Invalid customer name in payload")  # noqa: TRY301
        
        resolve = payload.get("resolve")
        customer_id = resolve.customer_id
        case = None
        if customer_id:
            case = get_case_by_customer_id(db, customer_id)
        analytics_payload = {
            "case_id": None,
            "event_type": EventType.EMAIL_CTA_CLICKED.value,
        }
        if case is not None:
            analytics_payload["case_id"] = case.id

        analytics_token = create_analytics_token(analytics_payload)

        response = await email_service.send_email(
            to_email=email,
            template=email_service.EmailTemplate.RESOLVE_CUSTOMER_NOTIFICATION,
            context={
                "customer_name": customer_name,
                "result_of_resolve": result_of_resolve,
                "header_subtitle": "Resolve Completed",
                "redirect_url": f"{settings.FRONTEND_URL}/case-dashboard/?analytics_token={analytics_token}",
            },
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Email sent successfully.",
            data={
                "email": email,
                "username": customer_name,
                "message_id": response.message_id,
            },
        )
    except Exception as e:
        logger.exception(f"Error in send_resolve_customer_notification_email: {e}")
        raise


@event(EventType.RESOLVE_NN_EMAIL)  # type: ignore
async def send_resolve_navigator_notification_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
        Send an email to the navigator after resolve is completed with the result.

        Example payload:
        {
            "customer_name": "JohnDoe",
            "result": "Resolve result",
            "navigators": [{"navigator_email": "navigator@example.com", "navigator_name": "JohnDoe"}]
        }
    """
    try:

        payload = event.payload
        required_keys = ["customer_name", "result", "navigators"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        customer_name = payload.get("customer_name")
        result = payload.get("result")
        navigators = payload.get("navigators")

        if not isinstance(customer_name, str) or customer_name.strip() == "":
            raise ValueError("Invalid customer name in payload")  # noqa: TRY301
        if not isinstance(navigators, list) or len(navigators) == 0:
            raise ValueError("Invalid navigators in payload")  # noqa: TRY301

        response_list = []
        # Prepare list of navigator emails
        navigator_emails = [str(navigator.get("navigator_email")) for navigator in navigators if navigator.get("navigator_email") is not None]
        if navigator_emails:
            response = await email_service.send_email(
                bcc=navigator_emails,
                template=email_service.EmailTemplate.RESOLVE_NAVIGATOR_NOTIFICATION,
                context={
                    "navigator_name": "Navigator",
                    "customer_name": customer_name,
                    "result_of_resolve": result,
                    "header_subtitle": "Resolve Completed",
                    "redirect_url": f"{settings.FRONTEND_URL}/resolve-dashboard",
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
            message="Email sent successfully to navigators.",
            data=response_list,
        )
    except Exception as e:
        logger.exception(f"Error in send_resolve_navigator_notification_email: {e}")
        raise

"""
Password Reset Event Handlers

This module contains the password reset event handler functions.
It demonstrates the event-driven architecture using enums for type safety.

All event handlers are decorated with @event and automatically registered.
"""

import json
import uuid
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.core.email import email_service
from app.core.security import (
    create_access_token,
    create_password_token,
    create_refresh_token,
)
from app.db.models import (
    CaseEngage,
    Engage,
    EngageQuestionAnswers,
    QuestionAnswers,
)
from app.db.services.auth import verify_user
from app.db.services.case import get_case_by_id, get_case_no_by_id,get_case_by_customer_invoice_id
from app.db.services.customer import (
    create_customer_and_update_resolve_transactional,
    validate_resolve_customer_assignment,
)
from app.db.services.general import ( 
    get_all_navigator_emails, 
    get_case_customer_user, 
    get_case_details_url,
    invoke_dispatch_event,
    get_timeline_type,
)
from app.db.services.kyc import (
    check_customer_engage_access,
    get_kyc_data,
    get_kyc_questions,
    get_resolve_options_for_kyc,
    submit_kyc_data,
)
from app.db.services.lawyer import get_lawyer_by_id_service
from app.db.services.resolve import get_resolve_from_case_id, get_resolve_by_id
from app.db.services.timeline_event import (
    check_customer_case_access,
)
from app.db.services.simple_auth_token import create_simple_auth_token
from app.db.services.timeline_event import disable_timeline_action_buttons
from app.db.services.user import create_user_with_role_transactional, update_user_generic
from app.enums.component import ComponentEnum
from app.enums.payment import InvoiceStatusEnum
from app.enums.events import EventType
from app.enums.file_upload import ImageSize
from app.enums.base import NameExtractionOption
from app.enums.user import PasswordStateEnum
from app.enums.user_role import UserRoleEnum
from app.events.dispatcher import event
from app.schemas.v1.auth import LoginResponseData, UserData
from app.schemas.v1.customer import (
    CustomerInfo,
    CustomerRegistrationResponseData,
)
from app.schemas.v1.engage import FullQuestionModel
from app.schemas.v1.event import Event, EventResponseData
from app.schemas.v1.resolve import CaseInfo as ResolveCaseInfo
from app.schemas.v1.user import UserCreateRequest, UserUpdateRequest
from app.services.upload_service import UploadService
from app.utils.encryption import encrypt_id
from app.utils.formatters import format_case_number, extract_name_parts
from app.utils.helpers import format_expiry_time
from app.utils.validators import validate_event_payload, validate_phone_number
from app.websocket.manager import WebSocketManager
from app.db.services.timeline_event import get_timeline_event_from_map
from app.db.services.timeline_event import save_timeline_map, save_timeline_event
from app.utils.helpers import get_template_json, replace_placeholders

logger = logging.getLogger(__name__)
upload_service = UploadService()

@event(EventType.CUSTOMER_KYC_SUBMIT) # type: ignore
async def handle_customer_kyc_submit(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer alignment check submit request.
    Required payload:
    {
        "request_data": {
            "case_id": 1
        },
        "current_user": <User object with attributes: id, first_name, last_name, email, etc.>,
    }
    """
    try:
        payload = event.payload
        required_keys = [{"request_data": ["case_id"]}, "current_user"]
        #TODO: Add timeline card exists check to block the submission
        validation = validate_event_payload(payload, required_keys) # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        current_user = payload["current_user"]
        request = payload["request_data"]
        err_detail = "You are not authorized to access this resource"
        role_ids = [user_role.role_id for user_role in current_user.user_roles]
        role = UserRoleEnum.from_id(role_ids[0])

        user = None
        # if role == UserRoleEnum.CUSTOMER:
        #     user = current_user
        #     valid = check_customer_engage_access(db, current_user, int(request.case_id))
        #     if not valid:
        #         raise ValueError(err_detail)  # noqa: TRY301
        #     payload["customer_email"] = current_user.email
            # first_name = current_user.first_name if current_user.first_name is not None else ""
            # last_name = current_user.last_name if current_user.last_name is not None else ""
            # payload["customer_name"] = first_name + " " + last_name
            # payload["first_name"] = first_name
        if role == UserRoleEnum.NAVIGATOR:
            user = get_case_customer_user(db, int(request.case_id))
            if user is None:
                raise ValueError("Customer not found or not active")  # noqa: TRY301
            payload["customer_email"] = user.email
            # first_name = user.first_name if user.first_name is not None else ""
            # last_name = user.last_name if user.last_name is not None else ""
            # payload["customer_name"] = first_name + " " + last_name
            # payload["first_name"] = first_name
        else:
            raise ValueError(err_detail)  # noqa: TRY301

        payload["case_id"] = request.case_id

        case = get_case_by_id(db, int(request.case_id))
        if case is None:
            raise ValueError("Case not found")  # noqa: TRY301
        
        if case.is_triage:
            resolve = None
            # from app.db.models.engage import CaseEngage
            # from app.db.services.kyc import create_engage_case
            case_engage = db.query(CaseEngage).filter(CaseEngage.case_id == case.id).first()
            engage_id = case_engage.engage_id if case_engage is not None else None
            if engage_id is None:
                engage_id = create_engage_case(db, case.id, int(current_user.id)) # type: ignore
            options = get_resolve_options_for_kyc(db, None, int(engage_id))
        else:
            resolve = get_resolve_from_case_id(db, int(request.case_id))
            if resolve is None:
                raise ValueError("Resolve not found for the case")  # noqa: TRY301
            options = get_resolve_options_for_kyc(db, int(resolve.id), None)

        is_kyc_completed = (
            db.query(Engage.is_kyc_completed)
            .join(CaseEngage, Engage.id == CaseEngage.engage_id)
            .filter(
                CaseEngage.case_id == int(request.case_id),
                Engage.is_kyc_completed.is_(True)
            )
            .scalar()
        )

        if is_kyc_completed:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Customer Alignment Check already completed",
                },
            )

        navigator_emails = get_all_navigator_emails(db)
        payload["navigators"] = navigator_emails

        result, kyc_id = submit_kyc_data(db, current_user, request, options)
        if result is False:
            raise ValueError("Error in submitting alignment check data")  # noqa: TRY301

        now = datetime.now(timezone.utc)
        payload["timestamp"] = now.isoformat()
        payload["kyc_id"] = encrypt_id(kyc_id)
        kyc_data = get_kyc_data(db, int(request.case_id))
        kyc_questions = FullQuestionModel.model_validate(kyc_data)
        if request.case_id and int(request.case_id):
            case_number = get_case_no_by_id(db, int(request.case_id))
            if case_number:
                case_number = format_case_number(str(case_number.case_no))
                payload["case_number"] = case_number
            else:
                payload["case_number"] = None
        else:
            payload["case_number"] = None
        
        #  get customer name and partner name from the kyc data
        answer_1_1 = kyc_data.get("1", {}).get("form_fields", {}).get("questions", {}).get("1.1", {}).get("answer", [])
        answer_1_3 = kyc_data.get("1", {}).get("form_fields", {}).get("questions", {}).get("1.3", {}).get("answer", [])
        answer_2_1 = kyc_data.get("2", {}).get("form_fields", {}).get("questions", {}).get("2.1", {}).get("answer", [])
        answer_2_3 = kyc_data.get("2", {}).get("form_fields", {}).get("questions", {}).get("2.3", {}).get("answer", [])

        customer_name = ""
        partner_name = ""
        customer_first_name = ""
        customer_last_name = ""
        if answer_1_1 and isinstance(answer_1_1[0], dict):
            customer_first_name = answer_1_1[0].get("value")
            customer_name = customer_first_name
            # resolve.customer_name = answer_1[0].get("value")

        if answer_1_3 and isinstance(answer_1_3[0], dict):
            customer_last_name = answer_1_3[0].get("value")
            customer_name = customer_name + " " + customer_last_name

        if answer_2_1 and isinstance(answer_2_1[0], dict):
            partner_first_name = answer_2_1[0].get("value")
            partner_name = partner_first_name
            # resolve.partner_name = answer_2[0].get("value")

        if answer_2_3 and isinstance(answer_2_3[0], dict):
            partner_last_name = answer_2_3[0].get("value")
            partner_name = partner_name + " " + partner_last_name
        
        if resolve is not None:
            if customer_name and customer_name != "":
                resolve.customer_name = customer_name.strip()

            if partner_name and partner_name != "":
                resolve.partner_name = partner_name.strip()

            db.add(resolve)

        # save the user table first name and last name from the resolve customer name
        customer_user = get_case_customer_user(db, int(request.case_id)) if user is None else user

        # first_name = extract_name_parts(resolve.customer_name, NameExtractionOption.FIRST)
        if customer_first_name and customer_first_name != "":
            customer_user.first_name = customer_first_name
        # last_name = extract_name_parts(resolve.customer_name, NameExtractionOption.LAST)
        if customer_last_name and customer_last_name != "":
            customer_user.last_name = customer_last_name

        db.add(customer_user)

        payload["customer_name"] = customer_name
        payload["first_name"] = customer_first_name
        # updated_customer_user = False
        # if customer_user:
        #     if customer_user.first_name == "." or customer_user.first_name == "":
        #         first_name = extract_name_parts(resolve.customer_name, NameExtractionOption.FIRST)
        #         if first_name:
        #             customer_user.first_name = first_name
        #             updated_customer_user = True
        #     if customer_user.last_name == "." or customer_user.last_name == "":
        #         last_name = extract_name_parts(resolve.customer_name, NameExtractionOption.LAST)
        #         if last_name:
        #             customer_user.last_name = last_name
        #             updated_customer_user = True
        #     if updated_customer_user:
        #         db.add(customer_user)
        #         commit_needed = True
        # db.commit()

        should_display = True
        message = f"Alignment Check submitted for {customer_name} - Case - {case_number}"
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            message = "Your Nova Expert Alignment Check is now under review."

        #  Note : Here, we don't need to explicitly disable the customer card buttons because, for the same timeline type, they will be disabled using the same button names.
        disable_timeline_action_buttons(
            db=db,
            component_buttons={
                str(ComponentEnum.CASE_OPEN_CUS_CARD.value): ["kyc_form"],
                str(ComponentEnum.TRIAGE_SUBMITTED_NN_CARD.value): ["alignment_check"],
                # str(ComponentEnum.BOOK_FREE_CALL_CUS_CARD.value): ["free_call"],          
                str(ComponentEnum.BOOK_FREE_CALL_NN_CARD.value): ["free_call", "alignment_check"],
                str(ComponentEnum.CUSTOMER_KYC_HOLD_NN_CARD.value): ["alignment_check_push", "alignment_check", "view_alignment_check_details", "book_free_call"],
            },
            related_id=int(request.case_id),
        )

        current_user_id = int(event.current_user.id) if event.current_user else None
        # dispatch the event to generate the AI case summary
        invoke_dispatch_event(event_type=EventType.GENERATE_AI_CASE_SUMMARY, payload=payload, user_id=event.user_id, current_user_id=current_user_id)

        return EventResponseData(
            should_display=should_display,
            success=True,
            message=message,
            data=kyc_questions,
        )

    except Exception as e:
        logger.exception(f"Error in handle_customer_kyc_submit: {e}")
        raise


@event(EventType.CUSTOMER_KYC_HOLD) # type: ignore
async def handle_customer_kyc_hold(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer alignment check hold request.
    Required payload:
    {
        "request_data": {
            "case_id": 1
        },
        "current_user": <User object with attributes: id, first_name, last_name, email, etc.>,
    }
    """
    try:
        payload = event.payload
        required_keys = [{"request_data": ["case_id"]}, "current_user"]
        #TODO: Add timeline card exists check to block the submission
        validation = validate_event_payload(payload, required_keys) # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        current_user = payload["current_user"]
        request = payload["request_data"]
        err_detail = "You are not authorized to access this resource"
        role_ids = [user_role.role_id for user_role in current_user.user_roles]
        role = UserRoleEnum.from_id(role_ids[0])

        user = None
        if role == UserRoleEnum.CUSTOMER:
            user = current_user
            valid = check_customer_engage_access(db, current_user, int(request.case_id))
            if not valid:
                raise ValueError(err_detail)  # noqa: TRY301
            payload["customer_email"] = current_user.email

        elif role == UserRoleEnum.NAVIGATOR:
            user = get_case_customer_user(db, int(request.case_id))
            if user is None:
                raise ValueError("Customer not found or not active")  # noqa: TRY301
            payload["customer_email"] = user.email

        else:
            raise ValueError(err_detail)  # noqa: TRY301

        payload["case_id"] = request.case_id

        case = get_case_by_id(db, int(request.case_id))
        if case is None:
            raise ValueError("Case not found")  # noqa: TRY301
        
        if case.is_triage:
            resolve = None
            case_engage = db.query(CaseEngage).filter(CaseEngage.case_id == case.id).first()
            engage_id = case_engage.engage_id if case_engage is not None else None
            if engage_id is None:
                engage_id = create_engage_case(db, case.id, int(current_user.id)) # type: ignore
            options = get_resolve_options_for_kyc(db, None, int(engage_id))
        else:
            resolve = get_resolve_from_case_id(db, int(request.case_id))
            if resolve is None:
                raise ValueError("Resolve not found for the case")  # noqa: TRY301
            options = get_resolve_options_for_kyc(db, int(resolve.id), None)

        is_kyc_completed = (
            db.query(Engage.is_kyc_completed)
            .join(CaseEngage, Engage.id == CaseEngage.engage_id)
            .filter(
                CaseEngage.case_id == int(request.case_id),
                Engage.is_kyc_completed.is_(True)
            )
            .scalar()
        )

        if is_kyc_completed:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Customer Alignment Check already completed",
                },
            )

        navigator_emails = get_all_navigator_emails(db)
        payload["navigators"] = navigator_emails

        result, kyc_id = submit_kyc_data(db, current_user, request, options, is_hold=True)
        if result is False:
            raise ValueError("Error in submitting alignment check data")  # noqa: TRY301

        now = datetime.now(timezone.utc)
        payload["timestamp"] = now.isoformat()
        payload["kyc_id"] = encrypt_id(kyc_id)
        kyc_data = get_kyc_data(db, int(request.case_id))
        kyc_questions = FullQuestionModel.model_validate(kyc_data)
        if request.case_id and int(request.case_id):
            case_number = get_case_no_by_id(db, int(request.case_id))
            if case_number:
                case_number = format_case_number(str(case_number.case_no))
                payload["case_number"] = case_number
            else:
                payload["case_number"] = None
        else:
            payload["case_number"] = None
        
        #  get customer name and partner name from the kyc data
        answer_1_1 = kyc_data.get("1", {}).get("form_fields", {}).get("questions", {}).get("1.1", {}).get("answer", [])
        answer_1_3 = kyc_data.get("1", {}).get("form_fields", {}).get("questions", {}).get("1.3", {}).get("answer", [])
        answer_2_1 = kyc_data.get("2", {}).get("form_fields", {}).get("questions", {}).get("2.1", {}).get("answer", [])
        answer_2_3 = kyc_data.get("2", {}).get("form_fields", {}).get("questions", {}).get("2.3", {}).get("answer", [])

        customer_name = ""
        partner_name = ""
        customer_first_name = ""
        customer_last_name = ""
        if answer_1_1 and isinstance(answer_1_1[0], dict):
            customer_first_name = answer_1_1[0].get("value")
            customer_name = customer_first_name
            # resolve.customer_name = answer_1[0].get("value")

        if answer_1_3 and isinstance(answer_1_3[0], dict):
            customer_last_name = answer_1_3[0].get("value")
            customer_name = customer_name + " " + customer_last_name

        if answer_2_1 and isinstance(answer_2_1[0], dict):
            partner_first_name = answer_2_1[0].get("value")
            partner_name = partner_first_name
            # resolve.partner_name = answer_2[0].get("value")

        if answer_2_3 and isinstance(answer_2_3[0], dict):
            partner_last_name = answer_2_3[0].get("value")
            partner_name = partner_name + " " + partner_last_name
        
        if resolve is not None:
            if customer_name and customer_name != "":
                resolve.customer_name = customer_name.strip()
            if partner_name and partner_name != "":
                resolve.partner_name = partner_name.strip()

            db.add(resolve)

        # save the user table first name and last name from the resolve customer name
        customer_user = get_case_customer_user(db, int(request.case_id)) if user is None else user

        # first_name = extract_name_parts(resolve.customer_name, NameExtractionOption.FIRST)
        if customer_first_name and customer_first_name != "":
            customer_user.first_name = customer_first_name
        # last_name = extract_name_parts(resolve.customer_name, NameExtractionOption.LAST)
        if customer_last_name and customer_last_name != "":
            customer_user.last_name = customer_last_name

        db.add(customer_user)

        payload["customer_name"] = customer_name
        payload["first_name"] = customer_first_name

        db.commit()

        should_display = True
        message = f"Alignment Check held for {customer_name} - Case - {case_number}"
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            message = "Your Nova Expert Alignment Check is now under review."

        #  Note : Here, we don't need to explicitly disable the customer card buttons because, for the same timeline type, they will be disabled using the same button names.
        disable_timeline_action_buttons(
            db=db,
            component_buttons={
                str(ComponentEnum.CASE_OPEN_CUS_CARD.value): ["kyc_form"],
                # str(ComponentEnum.BOOK_FREE_CALL_CUS_CARD.value): ["free_call"],
                str(ComponentEnum.BOOK_FREE_CALL_NN_CARD.value): ["free_call", "alignment_check"],
                str(ComponentEnum.CUSTOMER_KYC_HOLD_NN_CARD.value): ["alignment_check_push", "alignment_check", "view_alignment_check_details", "book_free_call"],
            },
            related_id=int(request.case_id),
        )

        # current_user_id = int(event.current_user.id) if event.current_user else None
        # # dispatch the event to generate the AI case summary
        # invoke_dispatch_event(event_type=EventType.GENERATE_AI_CASE_SUMMARY, payload=payload, user_id=event.user_id, current_user_id=current_user_id)

        return EventResponseData(
            should_display=should_display,
            success=True,
            message=message,
            data=kyc_questions,
        )

    except Exception as e:
        logger.exception(f"Error in handle_customer_kyc_hold: {e}")
        raise


@event(EventType.CUSTOMER_KYC_CUS_EMAIL) # type: ignore
async def send_kyc_submission_customer_notification_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send KYC submission confirmation email to customer.

    Example payload:
    {
        "case_id": 1,
        "customer_email": "customer@example.com",
        "customer_name": "John Doe"
    }
    """
    from app.core.security import create_analytics_token
    try:
        payload = event.payload
        required_keys = ["case_id", "customer_email", "customer_name", "case_number"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        email = payload.get("customer_email")
        customer_name = payload.get("customer_name")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)
        case_number = payload.get("case_number")
        from app.utils.formatters import extract_name_parts
        from app.enums.base import NameExtractionOption
        customer_name = extract_name_parts(customer_name, NameExtractionOption.FIRST)

        analytics_payload = {
            "case_id": case_id,
            "event_type": EventType.EMAIL_CTA_CLICKED.value,
        }
        analytics_token = create_analytics_token(analytics_payload)

        if not email:
            raise ValueError("Email not found in payload")  # noqa: TRY301

        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            action_by = "Navigator"
        else:
            action_by = ""
        # Send KYC submission confirmation email
        response = await email_service.send_email(
            to_email=email,
            template=email_service.EmailTemplate.KYC_SUBMISSION_CUSTOMER_NOTIFICATION,
            context={
                "customer_name": customer_name,
                "case_url": f"{case_url}/?analytics_token={analytics_token}",
                "header_subtitle": "Alignment Check Submission Confirmation",
                "action_by": action_by,
                "case_number": case_number,
            },
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False
        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Alignment Check submission email sent successfully to customer",
            data={
                "customer_email": email,
                "customer_name": customer_name,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_kyc_submission_customer_notification_email: {e}")
        raise


@event(EventType.CUSTOMER_KYC_NN_EMAIL) # type: ignore
async def send_kyc_submission_navigator_notification_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send KYC submission notification email to Nova navigator.

    Example payload:
    {
        "case_id":1,
        "navigators": [
            {
                "navigator_email": "navigator@example.com",
                "navigator_name": "John Doe"
            }
        ],
        "matched_lawyers": <Lawyer object with attributes: id, name, photo_url, etc.>,
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "navigators", "case_number"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        navigators = payload.get("navigators")
        if navigators is None:
            logger.warning("No navigators found in payload")
            return EventResponseData(
                success=False,
                message="No navigators found in payload",
                data=[],
            )

        case_id = payload.get("case_id")
        case_number = payload.get("case_number")
        customer_name = payload.get("customer_name")

        matched_lawyers = payload.get("matched_lawyers")
        if matched_lawyers is None:
            logger.warning("No matched lawyers found in payload")
            # return EventResponseData(
            #     success=False,
            #     message="No matched lawyers found in payload",
            #     data=[],
            # )

        # create a list of matched lawyers with name and photo_url
        matched_lawyers_list = []
        if matched_lawyers:
            for lawyer in matched_lawyers:
                photo_url = upload_service.get_image_url(lawyer.photo_url, ImageSize.THUMBNAIL) if lawyer.photo_url is not None else ""

                matched_lawyers_list.append({
                    "name": lawyer.user.first_name + " " + lawyer.user.last_name,
                    "photo_url": photo_url,
                })

        response_list = []
        # Prepare list of navigator emails
        navigator_emails = [str(navigator.get("navigator_email")) for navigator in navigators if navigator.get("navigator_email") is not None]
        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        case_url = get_case_details_url(case_id)

        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            action_by = f"{event.current_user.first_name} {event.current_user.last_name}"
        else:
            action_by = ""

        if navigator_emails:
            # Send KYC submission notification email to navigator
            response = await email_service.send_email(
                bcc=navigator_emails,
                template=email_service.EmailTemplate.KYC_SUBMISSION_NAVIGATOR_NOTIFICATION,
                context={
                    "navigator_name": "Navigator",
                    "matched_lawyers_list": matched_lawyers_list,
                    "case_url": case_url,
                    "header_subtitle": "Alignment Check Submission Notification",
                    "case_number": case_number,
                    "action_by": action_by,
                    "customer_name": customer_name,
                },
            )
            response_list.append({
                "navigator_email": navigator_emails,
                "navigator_name": "Navigator",
                "message_id": response.message_id,
            })
        else:
            return EventResponseData(
                should_display=should_display,
                success=False,
                message="No navigator emails found in payload",
                data=[],
            )

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Alignment Check submission notification email sent successfully to navigator",
            data=response_list,
        )

    except Exception as e:
        logger.exception(f"Error in send_kyc_submission_navigator_notification_email: {e}")
        raise


@event(EventType.CUSTOMER_REG_CUS_EMAIL)  # type: ignore[misc]
async def send_customer_registration_customer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send customer registration confirmation email to the newly registered customer.

    Example payload:
    {
        "customer_email": "customer@example.com",
        "customer_name": "John Doe"
    }
    """
    from app.core.security import create_analytics_token
    try:
        payload = event.payload
        required_keys = ["customer_email", "customer_name"]
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

        if not email:
            raise ValueError("Email not found in payload")  # noqa: TRY301

        case_id = payload.get("case_id") if payload.get("case_id") else None
        case = None
        if case_id:
            case = get_case_by_id(db, case_id)
        analytics_payload = {
            "case_id": None,
            "event_type": EventType.EMAIL_CTA_CLICKED.value,
        }
        if case is not None:
            analytics_payload["case_id"] = case.id

        analytics_token = create_analytics_token(analytics_payload)

        # Send customer registration confirmation email
        response = await email_service.send_email(
            to_email=email,
            template=email_service.EmailTemplate.CUSTOMER_REGISTRATION_CUSTOMER_NOTIFICATION,
            context={
                "customer_name": customer_name,
                "header_subtitle": "Welcome to Nova",
                "redirect_url": f"{settings.FRONTEND_URL}/login?analytics_token={analytics_token}",
            },
        )

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display = should_display,
            success=True,
            message="Customer registration email sent successfully.",
            data={
                "customer_email": email,
                "customer_name": customer_name,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_customer_registration_customer_email: {e}")
        raise


@event(EventType.CUSTOMER_REG_NN_EMAIL)  # type: ignore[misc]
async def send_customer_registration_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send customer registred email to all navigators.

    Example payload:
    {
        "navigators": [
            {
                "navigator_email": "navigator@example.com",
                "navigator_name": "John Doe"
            }
        ]
        "customer_name": "John Doe"
        "customer_email": "customer@example.com"
    }
    """
    try:
        payload = event.payload
        required_keys = ["navigators", "customer_name", "customer_email"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        navigators = payload.get("navigators")
        if navigators is None:
            logger.warning("No navigators found in payload")
            return EventResponseData(
                success=False,
                message="No navigators found in payload",
                data=[],
            )
        customer_name = payload.get("customer_name", None)
        customer_email = payload.get("customer_email", None)
        response_list = []
        # Prepare list of navigator emails
        navigator_emails = [str(navigator.get("navigator_email")) for navigator in navigators if navigator.get("navigator_email") is not None]

        if navigator_emails:
            # Send customer registration notification email to navigator
            response = await email_service.send_email(
                bcc=navigator_emails,
                template=email_service.EmailTemplate.CUSTOMER_REGISTRATION_NAVIGATOR_NOTIFICATION,
                context={
                    "navigator_name": "Navigator",
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "header_subtitle": "Customer Registered Successfully",
                    "redirect_url": f"{settings.FRONTEND_URL}/case-dashboard",
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
        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Customer registration notification email sent successfully to navigator",
            data=response_list,
        )

    except Exception as e:
        logger.exception(f"Error in send_customer_registration_navigator_email: {e}")
        raise


@event(EventType.CUSTOMER_SIMPLE_REGISTRATION)  # type: ignore[misc]
async def customer_simple_registration(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Create a customer via magic-link simple registration flow.

    Required payload:
    {
        "request_data": <CustomerSimpleRegistrationRequest>
    }
    """
    try:
        payload = event.payload
        required_keys = ["request_data"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        registration_data = payload["request_data"]

        email = registration_data.email
        first_name = "."
        last_name = "."
        resolve_id = None
        if registration_data.resolve_id:
            resolve_id = int(registration_data.resolve_id)
            validate_resolve_customer_assignment(db, resolve_id)

            #from this resolve id fetch the customer name
            resolve = get_resolve_by_id(db, int(resolve_id))
            customer_name = resolve.customer_name if resolve else ""
            parts = customer_name.split()

            if len(parts) >= 2:
                first_name = parts[0]
                last_name = " ".join(parts[1:])
            else:
                first_name = parts[0] if len(parts) == 1 else "."
                last_name = "."

        user_create_request = UserCreateRequest(
            first_name=first_name,
            last_name=last_name,
            email=email,
            status="Active",
        )

        try:
            user = create_user_with_role_transactional(
                db=db,
                user_data=user_create_request,
                role_enum=UserRoleEnum.CUSTOMER,
                password=None,
            )

            # Set marketing email consent (only for simple registration)
            user.has_marketing_email_consent = registration_data.has_marketing_email_consent
            # Set marketing_email_consent_datetime using database (PostgreSQL) time
            from sqlalchemy import func
            user.marketing_email_consent_datetime = func.now()

            customer = create_customer_and_update_resolve_transactional(
                db=db, user_id=int(user.id), resolve_id=resolve_id
            )

            db.commit()
        except Exception:
            db.rollback()
            raise

        customer_info = CustomerInfo(
            first_name=str(user.first_name),
            last_name=str(user.last_name),
            email=str(user.email),
            phone=str(user.phone) if user.phone else None,
            customer_id=str(customer.id),
        )       

        if user:
            event.current_user = user

        response_data = CustomerRegistrationResponseData(
                customer=customer_info,
                case=None,
                login_data=None,
            )

        payload["customer_email"] = email
        payload["customer_name"] = f"{first_name} {last_name}".strip()
        payload["customer_id"] = int(customer.id)
        payload["resolve_id"] = resolve_id
        payload["first_name"] = first_name
        payload["last_name"] = last_name
        payload["user_id"] = int(user.id)

        navigator_emails = get_all_navigator_emails(db)
        payload["navigators"] = navigator_emails
        payload["customer_id"] = int(customer.id)
        payload["response_data"] = response_data

        return EventResponseData(
            should_display=True,
            success=True,
            message="Customer simple registration completed successfully.",
            data=response_data,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in customer_simple_registration: {e}")
        raise


@event(EventType.CUSTOMER_SIMPLE_REGISTRATION_CUS_EMAIL)  # type: ignore[misc]
async def send_customer_simple_registration_cus_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send simple registration magic link email to the customer.
    required payload:
    {
        "case_id": "1" | None,
        "user_id": "1",
        "customer_email": "customer@example.com",
        "customer_name": "John Doe"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "user_id",
            "customer_email",
            "customer_name",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        customer_email = payload.get("customer_email")
        customer_name = payload.get("customer_name") or "Customer"
        case_id = payload.get("case_id")
        user_id = payload.get("user_id")
        from app.utils.formatters import extract_name_parts
        from app.enums.base import NameExtractionOption
        customer_name = extract_name_parts(customer_name, NameExtractionOption.FIRST)
        if not customer_name:
            customer_name = "Customer"

        simple_auth_token_expire_minutes = settings.SIMPLE_AUTH_TOKEN_EXPIRE_MINUTES
        expiry_info = format_expiry_time(simple_auth_token_expire_minutes)

        simple_auth_token_record = create_simple_auth_token(
            db=db,
            user_id=int(user_id),
            token=None,
        )

        token_payload = {
            "sub": str(user_id),
            "case_id": case_id,
            "email": customer_email,
            "simple_auth_token_id": int(simple_auth_token_record.id),
        }
        magic_token = create_password_token(
            data=token_payload,
            token_type="simple_registration",
            expire_minutes=simple_auth_token_expire_minutes,
        )
        simple_auth_token_url = f"{settings.FRONTEND_URL}/directlogin?token={magic_token}"

        simple_auth_token_record.token = magic_token
        db.commit()

        response = await email_service.send_email(
            to_email=customer_email,
            template=email_service.EmailTemplate.CUSTOMER_SIMPLE_REGISTRATION_CUS_EMAIL,
            context={
                "username": customer_name,
                "simple_auth_token_url": simple_auth_token_url,
                "expiry_formatted": expiry_info["formatted"],
                "header_subtitle": "Your login link is ready",
            },
        )

        return EventResponseData(
            should_display=True,
            success=True,
            message="Customer simple registration email sent successfully.",
            data={
                "customer_email": customer_email,
                "simple_auth_token_url": simple_auth_token_url,
                "message_id": response.message_id,
            },
        )
    except Exception as e:
        logger.exception(
            f"Error in send_customer_simple_registration_cus_email: {e}"
        )
        raise


@event(EventType.SEND_LOGIN_LINK_EMAIL)  # type: ignore[misc]
async def send_login_link_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send login link magic link email to the customer.
    required payload:
    {
        "case_id": "1" | None,
        "resolve_id": "1" | None,
        "user_id": "1",
        "customer_email": "customer@example.com",
        "customer_name": "John Doe"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "user_id",
            "customer_email",
            "customer_name",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        customer_email = payload.get("customer_email")
        customer_name = payload.get("customer_name") or "Customer"
        case_id = payload.get("case_id")
        resolve_id = payload.get("resolve_id")
        user_id = payload.get("user_id")

        simple_auth_token_expire_minutes = settings.SIMPLE_AUTH_TOKEN_EXPIRE_MINUTES
        expiry_info = format_expiry_time(simple_auth_token_expire_minutes)

        simple_auth_token_record = create_simple_auth_token(
            db=db,
            user_id=int(user_id),
            token=None,
        )

        token_payload = {
            "sub": str(user_id),
            "case_id": case_id,
            "resolve_id": resolve_id,
            "email": customer_email,
            "simple_auth_token_id": int(simple_auth_token_record.id),
        }
        magic_token = create_password_token(
            data=token_payload,
            token_type="simple_registration",
            expire_minutes=simple_auth_token_expire_minutes,
        )
        simple_auth_token_url = f"{settings.FRONTEND_URL}/directlogin?token={magic_token}"

        simple_auth_token_record.token = magic_token
        db.commit()

        customer_name = extract_name_parts(customer_name, NameExtractionOption.FIRST)

        response = await email_service.send_email(
            to_email=customer_email,
            template=email_service.EmailTemplate.SEND_LOGIN_LINK_EMAIL,
            context={
                "username": customer_name,
                "simple_auth_token_url": simple_auth_token_url,
                "expiry_formatted": expiry_info["formatted"],
                "header_subtitle": "Your login link is ready",
            },
        )

        return EventResponseData(
            should_display=True,
            success=True,
            message="Login link email sent successfully.",
            data={
                "customer_email": customer_email,
                "simple_auth_token_url": simple_auth_token_url,
                "message_id": response.message_id,
            },
        )
    except Exception as e:
        logger.exception(
            f"Error in send_login_link_email: {e}"
        )
        raise


@event(EventType.CUSTOMER_REG_OPEN_CASE)  # type: ignore[misc]
async def customer_reg_open_case(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Open a case for the customer.

    Required payload:
    {
        "request_data": <CustomerRegistrationRequest>
    }
    """
    try:
        message = ""
        payload = event.payload
        required_keys = ["request_data"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        registration_data = payload["request_data"]

        if registration_data.phone and not validate_phone_number(registration_data.phone):
            raise ValueError("Invalid phone number format")  # noqa: TRY301

        # Create user data for the create_user_with_role function
        user_create_request = UserCreateRequest(
            first_name=registration_data.first_name,
            last_name=registration_data.last_name,
            email=registration_data.email,
            phone=registration_data.phone,
            gender=None,  # Not provided in registration
            gender_other=None,  # Not provided in registration
            status="Active",
        )

        # Get decrypted resolve_id (automatically handled by DecryptedRequest)
        decrypted_resolve_id: int | None = None
        if registration_data.resolve_id:
            decrypted_resolve_id = int(registration_data.resolve_id)
            # Validate that resolve is not already assigned to a customer
            validate_resolve_customer_assignment(db, decrypted_resolve_id)

        # Transaction 1: User creation, customer creation, and resolve update
        user = None
        customer = None

        try:
            # Create user with customer role (without committing)
            user = create_user_with_role_transactional(
                db=db,
                user_data=user_create_request,
                role_enum=UserRoleEnum.CUSTOMER,
                password=registration_data.password,
            )

            # Set marketing email consent (for customer registration)
            user.has_marketing_email_consent = registration_data.has_marketing_email_consent
            from sqlalchemy import func
            user.marketing_email_consent_datetime = func.now()

            # Create customer record and update resolve if needed (without committing)
            customer = create_customer_and_update_resolve_transactional(
                db=db, user_id=int(user.id), resolve_id=decrypted_resolve_id
            )

            # Commit Transaction 1
            db.commit()

            # Create customer info
            customer_info = CustomerInfo(
                first_name=str(user.first_name),
                last_name=str(user.last_name),
                email=str(user.email),
                phone=str(user.phone) if user.phone else None,
                customer_id=str(customer.id),
            )

            # Create grouped response data
            response_data = CustomerRegistrationResponseData(
                customer=customer_info,
                case=None,
                login_data=None,
            )

            # message.append(ResponseMessage(success=True, message="Customer created successfully"))
            should_display = True
            message = "Customer created successfully, "

        except Exception:
            # Rollback Transaction 1 if any error occurs
            db.rollback()
            raise

        # Generate tokens
        try:
            # Get user data for token creation
            user_data_for_token = verify_user(user)

            # Calculate refresh token expiry
            refresh_expiry = datetime.now(timezone.utc) + timedelta(
                minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
            )

            # Save refresh token to database first (with placeholder token) to get the ID
            from app.db.services.refresh_token import (
                create_refresh_token as save_refresh_token,
            )

            refresh_token_record = save_refresh_token(
                db=db,
                user_id=int(user.id),
                token=uuid.uuid4(),  # Temporary placeholder
                expiry_at=refresh_expiry
            )

            # Now create tokens with the refresh_token_id encoded
            access_token = create_access_token(data=user_data_for_token, refresh_token_id=refresh_token_record.id)  # type: ignore[arg-type]
            refresh_token = create_refresh_token(data={"sub": str(user.id)}, refresh_token_id=refresh_token_record.id)  # type: ignore[arg-type]

            # Update the refresh token record with the actual token
            refresh_token_record.refresh_token = refresh_token  # type: ignore[assignment]
            db.commit()
            # Create user data
            user_data = UserData(
                first_name=str(user.first_name),
                last_name=str(user.last_name),
                email=str(user.email),
                phone=str(user.phone) if user.phone else None,
                gender=user.gender.value if user.gender else None,
                gender_other=user.gender_other if user.gender_other else None,
                user_id=str(user.id),
                role_code=UserRoleEnum.CUSTOMER.value,
                available_roles=[UserRoleEnum.CUSTOMER.value],
                customer_id=str(customer.id),
            )

            # Create login response data
            login_response_data = LoginResponseData(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                user_data=user_data,
            )
            response_data.login_data = login_response_data
            # message.append(ResponseMessage(success=True, message="Token generated successfully"))
            message = message + "Token generated successfully, "

        except Exception as e:
            logger.exception(f"Error in customer_reg_open_case: {e}")
            # message.append(ResponseMessage(success=False, message="Token generation failed"))
            message = message + "Token generation failed, "
            # return BaseResponse[CustomerRegistrationResponseData](
            #     success=True,
            #     message=message,
            #     data=response_data,
            # )
            raise ValueError("Token generation failed") from None

        payload["customer_email"] = str(user.email)
        first_name = str(user.first_name) if user.first_name is not None else ""
        last_name = str(user.last_name) if user.last_name is not None else ""
        payload["customer_name"] = first_name + " " + last_name

        navigator_emails = get_all_navigator_emails(db)
        payload["navigators"] = navigator_emails
        payload["customer_id"] = int(customer.id)
        payload["resolve_id"] = decrypted_resolve_id
        payload["response_data"] = response_data


        reg_response = CustomerRegistrationResponseData.model_validate(response_data)

        # i need to append user to the event
        if user:
            event.current_user = user

        if user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = True
            message = "Your account has been created successfully."

        return EventResponseData(
            should_display=should_display,
            success=True,
            message=message,
            data=reg_response,
        )
    except Exception as e:
        logger.exception(f"Error in customer_reg_open_case: {e}")
        raise


@event(EventType.CUSTOMER_TALK_CUS_NN) # type: ignore
async def handle_customer_talk_cus_nn(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer talk to navigator event.
    Required payload:
    {
        "request_data": {
            "case_id": "1",
            "phone": "1234567890"
        },
        "customer_user": <User object.>,
    }
    """
    try:
        payload = event.payload
        required_keys = [{"request_data": ["case_id","phone"]}, "customer_user"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(f"Payload validation failed for {event.event_type.value}: {validation}")
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        request_data = payload["request_data"]
        case_id = request_data.case_id
        customer_user = payload["customer_user"]
        phone = request_data.phone

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Customer talk to navigator event: Invalid case ID format") from e

        customer_id = customer_user.customer.id if customer_user.customer is not None else None
        if customer_id is None:
            raise ValueError("Invalid user")  # noqa: TRY301

        valid = check_customer_case_access(db, int(customer_id), case_id)
        if valid is False:
            raise ValueError("You are not authorized to access this resource")  # noqa: TRY301

        case = get_case_by_id(db, case_id)
        if case is None:
            raise ValueError("Case not found")  # noqa: TRY301

        if case.is_lawyer_assigned:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Case already assigned to an expert",
                },
            )

        # Get navigator emails
        navigator_emails = get_all_navigator_emails(db)
        payload["navigators"] = navigator_emails

        first_name = customer_user.first_name if customer_user.first_name is not None else ""
        last_name = customer_user.last_name if customer_user.last_name is not None else ""
        customer_name = first_name + " " + last_name
        payload["customer_name"] = customer_name
        payload["customer_email"] = customer_user.email if customer_user.email is not None else ""
        payload["case_id"] = request_data.case_id
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload["case_number"] = format_case_number(case.case_no)
        payload["case"] = case
        payload["customer_phone"] = phone

        # Disable talk_to_nn button in CASE_PROFILE_CUS_CARD timeline event
        # disable_timeline_action_buttons(
        #   db=db,
        #   component_buttons={
        #     str(ComponentEnum.CASE_PROFILE_CUS_CARD.value): ["talk_to_nn"]
        #   },
        #   related_id=int(case_id),
        # )

        should_display = True
        message = f"Customer talk to navigator request sent successfully. Case - {payload['case_number']}"
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = True
            message = "Your request to talk to navigator has been sent successfully."

        return EventResponseData(
            should_display=should_display,
            success=True,
            message=message,
            data={},
        )
    except Exception as e:
        logger.exception(f"Error in handle_customer_talk_cus_nn: {e}")
        raise


@event(EventType.CUSTOMER_TALK_CUS_LAW) # type: ignore
async def handle_customer_talk_cus_law(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer talk to lawyer event.
    Required payload:
    {
        "request_data": {
            "case_id": 1,
            "lawyer_id": 1,
            "phone": "1234567890"
        },
        "customer_user": <User object with attributes: id, first_name, last_name, email, etc.>,
    }
    """
    try:
        payload = event.payload
        required_keys = [{"request_data": ["case_id", "lawyer_id", "phone"]}, "customer_user"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(f"Payload validation failed for {event.event_type.value}: {validation}")
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        request_data = payload["request_data"]
        case_id = int(request_data.case_id)
        lawyer_id = request_data.lawyer_id
        customer_user = payload["customer_user"]
        phone = request_data.phone

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Customer talk to expert event: Invalid case ID format") from e

        customer_id = customer_user.customer.id if customer_user.customer is not None else None
        if customer_id is None:
            raise ValueError("Invalid user")  # noqa: TRY301

        valid = check_customer_case_access(db, int(customer_id), case_id)
        if valid is False:
            raise ValueError("You are not authorized to access this resource")  # noqa: TRY301

        # Customer name and email
        first_name = customer_user.first_name if customer_user.first_name is not None else ""
        last_name = customer_user.last_name if customer_user.last_name is not None else ""
        customer_name = first_name + " " + last_name

        # Case object
        case = get_case_by_id(db, case_id)

        if case.is_lawyer_assigned:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Case already assigned to an expert",
                },
            )

        # Lawyer object
        lawyer = get_lawyer_by_id_service(db, lawyer_id, customer_user)

        case_number = format_case_number(case.case_no)

        payload["customer_name"] = customer_name
        payload["customer_email"] = customer_user.email if customer_user.email is not None else ""
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload["case"] = case
        payload["lawyer"] = lawyer
        payload["case_number"] = case_number
        payload["customer_phone"] = phone

        should_display = True
        message = f"Customer talk to expert request sent successfully. Case - {case_number}"
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = True
            message = "Your request to talk to an expert has been sent."

        # Disable talk_to_lawyer button in CASE_PROFILE_CUS_CARD timeline event
        # disable_timeline_action_buttons(
        #   db=db,
        #   component_buttons={
        #     str(ComponentEnum.CASE_PROFILE_CUS_CARD.value): ["talk_to_lawyer"]
        #   },
        #   related_id=int(case_id),
        # )

        return EventResponseData(
            should_display=should_display,
            success=True,
            message=message,
            data={},
        )
    except Exception as e:
        logger.exception(f"Error in handle_customer_talk_cus_law: {e}")
        raise


@event(EventType.CUSTOMER_PMT_COMPLETE) # type: ignore
async def handle_customer_pmt_complete(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer initial payment complete event.
    required payload:
    {
        "payment_event": <Event/Session object>,
        "invoice": <Invoice object>,
        "payment": <Payment object>,
        "current_user":<User object>,
    }

    e.g. webhook event:
    {
        "data": {
            "object": {
                "amount": 1000,
                "balance_transaction": "transaction_id",
                "billing_details": {
                    "email": "customer@example.com",
                },
                "metadata": {
                    "invoice_id": "363aeea4ad1f5cb825731b75cb857b73",
                    "user_id": "d58161e55dc598535ab499eb84939aab"
                },
                "payment_method_details":{
                    "card": {
                        "amount_authorized": 1000,
                        "authorization_code": "717186",
                        "brand": "visa",
                        "checks": {
                            "address_line1_check": null,
                            "address_postal_code_check": "pass",
                            "cvc_check": "pass"
                        },
                        "country": "US",
                        "exp_month": 4,
                        "exp_year": 2030,
                        "extended_authorization": {
                            "status": "disabled"
                        },
                        "fingerprint": "U81sNUiK9iy5IPL4",
                        "funding": "credit",
                        "incremental_authorization": {
                            "status": "unavailable"
                        },
                        "installments": null,
                        "last4": "4242",
                        "mandate": null,
                        "multicapture": {
                            "status": "unavailable"
                        },
                        "network": "visa",
                        "network_token": {
                            "used": false
                        },
                        "network_transaction_id": "855649115788510",
                        "overcapture": {
                            "maximum_amount_capturable": 1000,
                            "status": "unavailable"
                        },
                        "regulated_status": "unregulated",
                        "three_d_secure": null,
                        "wallet": null
                    },
                    "type": "card"
                },
            }
        }
    }
    """
    try:
        payload = event.payload
        required_keys = ["payment_event", "invoice", "payment", "current_user"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(f"Payload validation failed for {event.event_type.value}: {validation}")
            raise ValueError("Customer initial payment event: Required keys not found in payload")  # noqa: TRY301

        payment_event = payload.get("payment_event")
        if payment_event is None:
            raise ValueError("Customer initial payment event: Payment event not found in payload")  # noqa: TRY301
        user = payload.get("current_user")
        invoice = payload.get("invoice")
        case = get_case_by_customer_invoice_id(db, user.customer.id, invoice.id)
        if case is None:
            raise ValueError("Customer initial payment event: Case not found")  # noqa: TRY301

        payload["case_number"] = format_case_number(case.case_no)
        payload["case"] = case
        payload["lawyer"] = case.case_lawyers[0].lawyer
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload["status"] = InvoiceStatusEnum.COMPLETED.value

        return EventResponseData(
            success=True,
            message="Customer initial payment processed successfully.",
            data={},
        )
    except Exception as e:
        logger.exception(f"Error in handle_customer_pmt_complete: {e}")
        raise

@event(EventType.ENGAGE_KYC_AUTO_FILL)  # type: ignore[misc]
async def handle_engage_kyc_auto_fill(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Automatically pre-fill engage (KYC) question answers with the first two resolved questions.

    This event:
    1. Checks if engage already exists for the case
    2. If NOT, creates new engage and CaseEngage mapping
    3. Gets the first two resolve question answers
    4. Creates corresponding engage question answers (questions 1 and 2)
    5. Links them via EngageQuestionAnswers table

    Required payload:
    {
        "case_id": 1
    }

    Note: Uses question identifiers "1" and "2" for mapping. If future question
    identifiers change, update the mapping logic in this function.
    """
    from app.db.services.kyc import get_resolve_map_for_kyc

    try:
        # Validate payload
        payload = event.payload
        required_keys = ["case_id"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case_id = int(payload["case_id"])

        # OPTIMIZATION 1: Single query to get all required data
        # Get case, resolve, and customer user in one go
        case = get_case_by_id(db, case_id)
        if case is None:
            raise ValueError("Case not found")  # noqa: TRY301

        resolve = get_resolve_from_case_id(db, case_id)
        # if resolve is None:
        #     raise ValueError("Resolve not found for the case")  # noqa: TRY301

        customer_user = get_case_customer_user(db, case_id)
        if customer_user is None:
            raise ValueError("Customer user not found for the case")  # noqa: TRY301

        # OPTIMIZATION 2: Check if engage already exists (early return if already filled)
        existing_case_engage = db.query(CaseEngage).filter(
            CaseEngage.case_id == case_id
        ).first()

        # If engage already exists, check if it has the first two answers
        if existing_case_engage is not None:
            existing_answers_count = db.query(EngageQuestionAnswers.id).filter(
                EngageQuestionAnswers.engage_id == existing_case_engage.engage_id
            ).count()

            if existing_answers_count > 0:
                logger.info(f"Engage already has {existing_answers_count} answers for case {case_id}")
                return EventResponseData(
                    success=True,
                    message="Engage already has answers",
                    data={
                        "auto_filled": False,
                        "engage_id": encrypt_id(str(existing_case_engage.engage_id)),
                        "reason": "Engage already populated"
                    },
                )

        # OPTIMIZATION 3: Get resolve question answers efficiently
        # Get only questions 1 and 2, ordered by identifier
        from app.utils.formatters import extract_name_parts

        if resolve is not None:
            customer_name = resolve.customer_name if resolve.customer_name is not None else ""
            partner_name = resolve.partner_name if resolve.partner_name is not None else ""

            resolve_questions_map = get_resolve_map_for_kyc(db, resolve.id)
        else:
            first_name = customer_user.first_name if customer_user.first_name is not None else ""
            last_name = customer_user.last_name if customer_user.last_name is not None else ""
            customer_name = first_name + " " + last_name
            partner_name = ""
            resolve_questions_map = {}

        name_map = {
            "1.1": extract_name_parts(customer_name, NameExtractionOption.FIRST),
            "1.3": extract_name_parts(customer_name, NameExtractionOption.LAST),
            "2.1": extract_name_parts(partner_name, NameExtractionOption.FIRST),
            "2.3": extract_name_parts(partner_name, NameExtractionOption.LAST),
        }

        # Create engage if it doesn't exist
        if existing_case_engage is None:
            # Create new engage
            engage = Engage(user_id=customer_user.id)
            db.add(engage)
            db.flush()  # Get the ID

            # Create case_engage mapping
            case_engage = CaseEngage(
                case_id=case_id,
                engage_id=engage.id
            )
            db.add(case_engage)
            db.flush()
            engage_id = engage.id
        else:
            engage_id = existing_case_engage.engage_id

        # OPTIMIZATION 4: Get KYC questions info efficiently
        kyc_questions = get_kyc_questions()

        # OPTIMIZATION 5: Build question answer objects using EXPLICIT MAPPING
        question_answer_objects = []

        prefilled_questions = [1.1, 1.3, 2.1, 2.3]
        if case.is_triage is False:
            # add question identifiers provided in get_resolve_map_for_kyc
            prefilled_questions.extend([14, 15, 16, 17, 23])

        for qid in prefilled_questions:
            create_key = False
            answer = None
            if str(qid) in name_map:
                name = name_map.get(str(qid))
                qid_parts = str(qid).split(".")
                qid_1 = qid_parts[0]
                qdata = kyc_questions.get(str(qid_1))
                if not qdata:
                    raise ValueError(f"Engage/Alignment Check question {qid} not found")  # noqa: TRY301

                latest_version_key = next(iter(qdata.get("versions", {}).keys()))
                answer = json.dumps([{"value": name}]) if name else json.dumps([])
                question_order = qdata.get("versions", {}).get(latest_version_key).get("form_fields", {}).get("questions", {}).get(str(qid)).get("question_order")
                create_key = True
            else:
                if resolve_questions_map:
                    #Children complexity 20 - resolve 14
                    if str(qid) == "20":
                        resolve_answer = resolve_questions_map.get("14", "")
                        if resolve_answer:
                            answer = json.dumps(resolve_answer)

                    #Relationship type 15 - resolve 4
                    if str(qid) == "15":
                        resolve_answer = resolve_questions_map.get("4", "")
                        if resolve_answer:
                            answer = json.dumps(resolve_answer)

                    #Relationship type other 16 - resolve 23
                    if str(qid) == "16":
                        resolve_answer = resolve_questions_map.get("23", "")
                        if resolve_answer:
                            answer = json.dumps(resolve_answer)

                    #Length of relationship 17 - resolve 3
                    if str(qid) == "17":
                        resolve_answer = resolve_questions_map.get("3", "")
                        if resolve_answer:
                            answer = json.dumps(resolve_answer)

                    #Warning signs 23 - resolve 16 -not direct prefill,check answer in domestic abuse or coercive control
                    if str(qid) == "23":
                        resolve_answer = resolve_questions_map.get("16", "")
                        if resolve_answer:
                            for item in resolve_answer:
                                if item.get("value", "") == "domestic_abuse":
                                    answer = json.dumps([{"value": "comfortable_discussing_in_consultation"}])

                    if answer:
                        qdata = kyc_questions.get(str(qid))
                        if not qdata:
                            raise ValueError(f"Engage/Alignment Check question {qid} not found")  # noqa: TRY301

                        latest_version_key = next(iter(qdata.get("versions", {}).keys()))
                        question_order = qdata.get("versions", {}).get(latest_version_key).get("question_order")
                        create_key = True

            if create_key:
                qa_obj = QuestionAnswers(
                    version=latest_version_key,
                    answer=answer,
                    question_identifier=str(qid),
                    question_order=question_order,
                )
                question_answer_objects.append(qa_obj)

        # Validate we created the expected number of answers
        if len(question_answer_objects) < 2:
            created_qids = [qa.question_identifier for qa in question_answer_objects]
            raise ValueError(f"Expected to create 4 engage answers, but only created {len(question_answer_objects)}: {created_qids}")  # noqa: TRY301

        # OPTIMIZATION 6: Bulk insert question answers
        db.add_all(question_answer_objects)
        db.flush()  # Get IDs for all objects

        # OPTIMIZATION 7: Create EngageQuestionAnswers mappings in one go
        engage_question_answers = [
            EngageQuestionAnswers(
                engage_id=engage_id,
                question_answer_id=qa_obj.id
            )
            for qa_obj in question_answer_objects
        ]

        db.add_all(engage_question_answers)
        db.commit()

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False
        
        payload["kyc_id"] = engage_id

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Engage Alignment Check answers auto-filled successfully",
            data={
                "auto_filled": True,
                "engage_id": encrypt_id(str(engage_id)),
            },
        )

    except Exception as e:
        db.rollback()
        logger.exception(f"Error in handle_engage_kyc_auto_fill: {e}")
        raise


@event(EventType.COMPLETE_ONBOARD_ASSESSMENT_CUS_EMAIL)  # type: ignore[misc]
async def send_complete_onboard_assessment_customer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to customer requesting to complete their onboarding process.

    Example payload:
    {
        "case_id": 1,
        "engage_url": "https://example.com/engage",
        "customer_email": "customer@example.com",
        "customer_name": "John Doe",
        "case_number": "CASE-100"
    }
    """
    try:
        payload = event.payload
        required_keys = ["engage_url", "case_id", "customer_email", "customer_name", "case_number"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case_id = payload.get("case_id")
        email = payload.get("customer_email")
        customer_name = payload.get("customer_name")
        engage_url = payload.get("engage_url")
        case_number = payload.get("case_number")
        from app.utils.formatters import extract_name_parts
        from app.enums.base import NameExtractionOption
        customer_name = extract_name_parts(customer_name, NameExtractionOption.FIRST)

        if not email:
            raise ValueError("Email not found in payload")  # noqa: TRY301

        case_url = get_case_details_url(case_id)

        # Send onboarding assessment completion email
        response = await email_service.send_email(
            to_email=email,
            template=email_service.EmailTemplate.COMPLETE_ONBOARD_ASSESSMENT_CUSTOMER_NOTIFICATION,
            context={
                "case_id": case_id,
                "customer_name": customer_name,
                "engage_url": engage_url,
                "case_url": case_url,
                "header_subtitle": "Prepare for your Nova Initial Consultation in Nova",
                "case_number": case_number,
            },
        )

        return EventResponseData(
            success=True,
            message="Complete onboarding assessment email sent successfully to customer.",
            data={
                "case_id": case_id,
                "customer_email": email,
                "customer_name": customer_name,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_complete_onboard_assessment_customer_email: {e}")
        raise


@event(EventType.CUSTOMER_KYC_HOLD_CUS_CARD)  # type: ignore
async def handle_customer_kyc_hold_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer alignment check hold customer card event: Generate card JSON using template and save to timeline_event table.
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
                f"Customer Alignment Check Hold Customer Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Customer Alignment Check Hold Customer Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        customer_name = payload["customer_name"]
        kyc_id = payload["kyc_id"]
        role_code = UserRoleEnum.CUSTOMER.value
        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Customer Alignment Check Hold Customer Card event: Invalid case ID format") from e

        template, last_version = get_template_json(str(ComponentEnum.CUSTOMER_KYC_HOLD_CUS_CARD.value), str(role_code), "timeline")

        timeline_type = get_timeline_type(db, ComponentEnum.CUSTOMER_KYC_HOLD_CUS_CARD.value, role_code, last_version)
        if timeline_type is None:
            raise ValueError("Customer Alignment Check Hold Customer Card event: Timeline type not found")  # noqa: TRY301

        # Prepare placeholder values
        placeholder_values = {
            "action_by": "",
            "case_number": case_number,
            "timestamp": timestamp,
            "customer_name": customer_name,
            "kyc_id": kyc_id,
            "action_buttons": {
                "book_free_call": True,
                "alignment_check": True
            },
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)
        if errors:
            logger.error(f"Customer Alignment Check Hold Customer Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Customer Alignment Check Hold Customer Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

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
            message="Customer Alignment Check Hold customer card generated and saved to timeline successfully.",
            data={}
        )

    except Exception as e:
        logger.exception(f"Customer Alignment Check Hold Customer Card event: Error in handle_customer_kyc_hold_cus_card: {e}")
        raise


@event(EventType.BOOK_FREE_CALL)  # type: ignore
async def handle_book_free_call(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle book free call event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "cal_event": dict<cal.com booking event payload>
    }
    """
    from app.db.services.auth import get_user_by_email
    from app.db.models.case import Case
    from app.db.models.case_customer import CaseCustomer
    from app.db.models.customer import Customer
    from app.db.services.customer import update_customer_phone_number
    from app.events.dispatcher import event_dispatcher
    from app.utils.helpers import extract_status_messages

    try:
        payload = event.payload
        required_keys = ["cal_event"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Book Free Call event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Book Free Call event: Required keys not found in payload")  # noqa: TRY301

        payload["navigators"] = get_all_navigator_emails(db)

        cal_event = payload["cal_event"]
        trigger_event = cal_event.get("triggerEvent", "") if cal_event.get("triggerEvent", "") else ""
        not_triage_resolve = True
        if trigger_event == "BOOK_FREE_CALL":
            not_triage_resolve = False
            from app.db.services.cal import get_last_booking_by_attendee_email

            attendee_email = cal_event.get("customer_email", "")
            if not attendee_email:
                raise ValueError("Book Free Call event: Customer email not found in payload")  # noqa: TRY301
            
            attendee_phone_number = cal_event.get("phone_number", "")
            if not attendee_phone_number:
                raise ValueError("Book Free Call event: Phone number not found in payload")  # noqa: TRY301

            try:
                booking = get_last_booking_by_attendee_email(attendee_email)
            except Exception as cal_err:
                logger.exception(
                    f"Triage submit: Failed to retrieve Cal.com booking for {attendee_email}: {cal_err}"
                )
                booking = {"meeting_url": "", "start_time": "", "end_time": ""}
            
            start_time = booking.get("start_time", "")
            end_time = booking.get("end_time", "")
            attendee_name = ""
            # meeting_url = booking.get("meeting_url", "")
        
        else:

            start_time = cal_event.get("payload", {}).get("startTime", "")
            end_time = cal_event.get("payload", {}).get("endTime", "")
            attendees = cal_event.get("payload", {}).get("attendees", [])
            attendee_phone_number = attendees[0].get("phoneNumber", "")
            attendee_email = attendees[0].get("email", "")
            attendee_name = attendees[0].get("name", "")
            # video_call_data = cal_event.get("payload", {}).get("videoCallData", {})
            # if video_call_data:
            #     meeting_url = video_call_data.get("url", "")
            # else:
            #     meeting_url = ""

        payload["customer_email"] = attendee_email
        payload["customer_name"] = attendee_name
        payload["start_time"] = start_time
        payload["end_time"] = end_time

        user = get_user_by_email(db, attendee_email)
        if not user:            
            # send book free call high intent navigator notification
            event_data = Event(
                event_type=EventType.BOOK_FREE_CALL_HIGH_INTENT_NN_EMAIL,
                payload=payload,
                user_id=None,
                current_user=None,
            )
            await event_dispatcher.dispatch_event(db, event_data)

            success, messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]
            if not success:
                raise ValueError("Book Free Call event: Failed to send nn email")  # noqa: TRY301
            raise ValueError("Book Free Call event: User not found")  # noqa: TRY301

        update_customer_phone_number(db, user.id, attendee_phone_number)

        customer_name = user.first_name if user.first_name else "" + " " + user.last_name if user.last_name else ""
        payload["customer_name"] = customer_name

        customer = user.customer
        if not customer:
            raise ValueError("Book Free Call event: Customer not found")  # noqa: TRY301
        case = db.query(Case).options(
            joinedload(Case.case_customers)
            .joinedload(CaseCustomer.customer),
        ).join(CaseCustomer, CaseCustomer.case_id == Case.id)\
         .join(Customer, Customer.id == CaseCustomer.customer_id)\
         .filter(
            Customer.id == customer.id
         ).first()
        if not case:
            raise ValueError("Book Free Call event: Case not found")  # noqa: TRY301
        
        # restrict book free call event for triage user case
        if case.is_triage is True:
            raise ValueError("Book Free Call event: Booking already made for this case")  # noqa: TRY301

        case_id = case.id
        payload["case_id"] = case_id

        case_engage = db.query(CaseEngage).filter(CaseEngage.case_id == case_id).first()
        engage_id = case_engage.engage_id if case_engage is not None else None
        payload["kyc_id"] = engage_id
        payload["timestamp"] = datetime.now().isoformat()
        payload["attendee_phone_number"] = attendee_phone_number
        # payload["meeting_url"] = meeting_url
        # payload["start_time"] = start_time
        # payload["end_time"] = end_time
        payload["case_number"] = format_case_number(case.case_no)
        payload["case"] = case

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        #  Note : Here, we don't need to explicitly disable the customer card buttons because, for the same timeline type, they will be disabled using the same button names.
        disable_timeline_action_buttons(
            db=db,
            component_buttons={
                # str(ComponentEnum.BOOK_FREE_CALL_CUS_CARD.value): ["free_call"],
                str(ComponentEnum.BOOK_FREE_CALL_NN_CARD.value): ["alignment_check"],
            },
            related_id=case_id,
        )

        if not_triage_resolve:
            # send book free call post resolve navigator notification
            event_data = Event(
                event_type=EventType.BOOK_FREE_CALL_POST_RESOLVE_NN_EMAIL,
                payload=payload,
                user_id=None,
                current_user=None,
            )
            await event_dispatcher.dispatch_event(db, event_data)
            success, messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Book Free Call event processed successfully.",
            data={}
        )
    except Exception as e:
        logger.exception(f"Book Free Call event: Error in handle_book_free_call: {e}")
        raise


@event(EventType.BOOK_FREE_CALL_CUS_CARD)  # type: ignore
async def handle_book_free_call_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle book free call customer card event: Generate card JSON using template and save to timeline_event table.
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
        # kyc_id = payload["kyc_id"]
        # meeting_url = payload.get("meeting_url", "")
        start_time = payload["start_time"]
        end_time = payload["end_time"]
        customer_name = payload["customer_name"]
        template, last_version = get_template_json(str(ComponentEnum.BOOK_FREE_CALL_CUS_CARD.value), str(UserRoleEnum.CUSTOMER.value), "timeline")
        timeline_type = get_timeline_type(db, ComponentEnum.BOOK_FREE_CALL_CUS_CARD.value, UserRoleEnum.CUSTOMER.value, last_version)
        if timeline_type is None:
            raise ValueError("Book Free Call Customer Card event: Timeline type not found")  # noqa: TRY301

        placeholder_values = {
            "action_by": customer_name,
            "case_number": case_number,
            "timestamp": timestamp,
            # "meeting_url": meeting_url,
            "start_time": start_time,
            "end_time": end_time,
            "action_buttons": {},
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


@event(EventType.TRIAGE_SUBMIT)  # type: ignore[misc]
async def handle_triage_submit(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle triage submit:
    - save optional answers
    - validate all required triage questions are answered
    - mark triage completed
    - create customer user/account
    - create case with is_triage=True and case_triage link

    Required payload:
    {
        "request_data": <SubmitTriageRequest>
    }
    """
    from app.db.services.auth import get_user_by_email
    from app.db.services.case import create_case
    from app.db.services.customer import create_customer_and_update_resolve_transactional
    from app.db.services.triage import (
        get_triage_by_id,
        mark_triage_completed,
        split_customer_name,
        submit_triage_data,
        validate_triage_completion,
    )
    from app.db.models import CaseTriage
    from app.enums.triage import TriageStatusEnum
    from app.schemas.v1.triage import CaseInfo as TriageCaseInfo, SubmitTriageResponseData
    from app.schemas.v1.user import UserCreateRequest
    from app.utils.formatters import format_case_number

    try:
        payload = event.payload
        required_keys = ["request_data"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        request = payload["request_data"]
        triage_id = int(request.triage_id)
        customer_email = str(request.customer_email).strip().lower()
        phone_number = str(request.phone_number).strip()
        customer_name = str(request.customer_name).strip()

        if not validate_phone_number(phone_number):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Invalid phone number format"}],
            )

        triage = get_triage_by_id(db, triage_id)
        if triage is None:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Triage not found"}],
            )

        existing_case_triage = (
            db.query(CaseTriage).filter(CaseTriage.triage_id == triage_id).first()
        )
        if existing_case_triage is not None:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail=[{"success": False, "message": "Triage is already linked to a case"}],
            )

        if triage.customer_email and str(triage.customer_email).lower() != customer_email:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Customer email does not match this triage"}],
            )

        existing_user = get_user_by_email(db, customer_email)
        if existing_user:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail=[{"success": False, "message": "User with this email already exists"}],
            )

        try:
            # Save answers if provided, then validate that triage is complete
            submit_triage_data(db, request, update_flag=False)
            validate_triage_completion(db, triage_id)
            mark_triage_completed(db, triage)

            first_name, last_name = split_customer_name(customer_name)
            user_create_request = UserCreateRequest(
                first_name=first_name,
                last_name=last_name,
                email=customer_email,
                phone=phone_number,
                status="Active",
            )
            user = create_user_with_role_transactional(
                db=db,
                user_data=user_create_request,
                role_enum=UserRoleEnum.CUSTOMER,
                password=None,
            )
            customer = create_customer_and_update_resolve_transactional(
                db=db,
                user_id=int(user.id),
                resolve_id=None,
            )

            triage.customer_email = customer_email
            triage.user_id = int(user.id)
            triage.customer_id = int(customer.id)
            db.commit()
        except Exception:
            db.rollback()
            raise

        try:
            case = create_case(
                db=db,
                customer_id=int(customer.id),
                resolve_id=None,
                triage_id=triage_id,
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

        customer_info = CustomerInfo(
            first_name=str(user.first_name),
            last_name=str(user.last_name),
            email=str(user.email),
            phone=str(user.phone) if user.phone else None,
            customer_id=str(customer.id),
        )
        case_info = TriageCaseInfo(
            case_id=str(case.id),
            case_no=format_case_number(str(case.case_no)),
            case_type=case.case_type.value if case.case_type else None,
            priority=case.priority.value if case.priority else None,
            start_date=case.start_date,  # type: ignore[arg-type]
            status=case.status.value,
            created_at=case.created_at,  # type: ignore[arg-type]
            updated_at=case.updated_at,  # type: ignore[arg-type]
            is_kyc_completed=case.is_kyc_completed,
        )

        login_response_data = None
        try:
            user_data_for_token = verify_user(user)
            refresh_expiry = datetime.now(timezone.utc) + timedelta(
                minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
            )
            from app.db.services.refresh_token import (
                create_refresh_token as save_refresh_token,
            )

            refresh_token_record = save_refresh_token(
                db=db,
                user_id=int(user.id),
                token=uuid.uuid4(),
                expiry_at=refresh_expiry,
            )
            access_token = create_access_token(
                data=user_data_for_token,
                refresh_token_id=refresh_token_record.id,  # type: ignore[arg-type]
            )
            refresh_token = create_refresh_token(
                data={"sub": str(user.id)},
                refresh_token_id=refresh_token_record.id,  # type: ignore[arg-type]
            )
            refresh_token_record.refresh_token = refresh_token  # type: ignore[assignment]
            db.commit()

            user_data = UserData(
                first_name=str(user.first_name),
                last_name=str(user.last_name),
                email=str(user.email),
                phone=str(user.phone) if user.phone else None,
                gender=user.gender.value if user.gender else None,
                user_id=str(user.id),
                role_code=UserRoleEnum.CUSTOMER.value,
                available_roles=[UserRoleEnum.CUSTOMER.value],
                customer_id=str(customer.id),
            )
            encrypted_case_id = encrypt_id(str(case.id))
            login_response_data = LoginResponseData(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                user_data=user_data,
                password_state=(
                    PasswordStateEnum.CAN_UPDATE
                    if user.password
                    else PasswordStateEnum.CAN_CREATE
                ),
                redirect_path=f"/case/{encrypted_case_id}",
                case=ResolveCaseInfo(
                    id=str(case.id),
                    case_no=format_case_number(str(case.case_no)),
                    type=case.case_type.value if case.case_type else None,
                    status=case.status.value,
                ),
            )
        except Exception as e:
            logger.exception(f"Error generating login data in handle_triage_submit: {e}")
            raise ValueError("Token generation failed") from None

        response_data = SubmitTriageResponseData(
            triage_id=str(triage.id),
            customer=customer_info,
            case=case_info,
            login_data=login_response_data,
        )

        from app.db.services.cal import get_last_booking_by_attendee_email

        try:
            booking = get_last_booking_by_attendee_email(customer_email)
        except Exception as cal_err:
            logger.exception(
                f"Triage submit: Failed to retrieve Cal.com booking for {customer_email}: {cal_err}"
            )
            booking = {"meeting_url": "", "start_time": "", "end_time": ""}

        event.current_user = user
        payload["customer_email"] = customer_email
        payload["customer_name"] = customer_name
        payload["customer_id"] = int(customer.id)
        payload["user_id"] = int(user.id)
        payload["case_id"] = int(case.id)
        payload["triage_id"] = triage_id
        payload["navigators"] = get_all_navigator_emails(db)
        payload["response_data"] = response_data
        payload["case_number"] = format_case_number(str(case.case_no))
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload["attendee_phone_number"] = phone_number
        # payload["meeting_url"] = booking.get("meeting_url", "")
        payload["start_time"] = booking.get("start_time", "")
        payload["end_time"] = booking.get("end_time", "")
        payload["start_date"] = (
            case.start_date.strftime(settings.DATE_FORMAT) if case.start_date else None
        )
        payload["priority"] = case.priority.value if case.priority else None
        payload["case_type"] = case.case_type.value if case.case_type else None
        payload["status"] = case.status.value

        # dispatch the event to generate the AI case summary
        invoke_dispatch_event(event_type=EventType.GENERATE_AI_CASE_SUMMARY, payload=payload, user_id=None, current_user_id=None)

        return EventResponseData(
            should_display=True,
            success=True,
            message="Triage submitted successfully.",
            data=response_data,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in handle_triage_submit: {e}")
        raise


@event(EventType.TRIAGE_RE_SUBMIT)  # type: ignore[misc]
async def handle_triage_re_submit(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle triage re-submit for an already completed triage:
    - save/update answers
    - validate all required triage questions are answered
    - update customer name and phone
    - notify customer and navigators

    Required payload:
    {
        "request_data": <SubmitTriageRequest>
    }
    """
    from app.db.models import CaseTriage
    from app.db.services.triage import (
        get_completed_triage_customer_and_case,
        get_triage_by_id,
        split_customer_name,
        submit_triage_data,
        validate_triage_completion,
    )
    from app.enums.case import CaseStatusEnum
    from app.enums.triage import TriageStatusEnum
    from app.schemas.v1.triage import SubmitTriageResponseData
    from app.utils.formatters import format_case_number

    try:
        payload = event.payload
        required_keys = ["request_data"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        request = payload["request_data"]
        triage_id = int(request.triage_id)
        customer_email = str(request.customer_email).strip().lower()
        phone_number = str(request.phone_number).strip()
        customer_name = str(request.customer_name).strip()

        if not validate_phone_number(phone_number):
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Invalid phone number format"}],
            )

        triage = get_triage_by_id(db, triage_id)
        if triage is None:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Triage not found"}],
            )

        if triage.status != TriageStatusEnum.COMPLETED:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Triage is not completed"}],
            )

        existing_case_triage = (
            db.query(CaseTriage).filter(CaseTriage.triage_id == triage_id).first()
        )
        if existing_case_triage is None or existing_case_triage.case is None:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Triage is not linked to a case"}],
            )

        case = existing_case_triage.case
        if case.status != CaseStatusEnum.OPEN:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Case is not open"}],
            )
        
        if case.is_kyc_completed:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Case is already KYC completed"}],
            )

        if triage.customer_email and str(triage.customer_email).lower() != customer_email:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Customer email does not match this triage"}],
            )

        if event.current_user and triage.user_id and int(event.current_user.id) != int(triage.user_id):
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail=[{"success": False, "message": "You are not authorized to re-submit this triage"}],
            )

        try:
            submit_triage_data(db, request, update_flag=True)
            validate_triage_completion(db, triage_id)

            first_name, last_name = split_customer_name(customer_name)
            if not triage.user_id:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=[{"success": False, "message": "User not found for this triage"}],
                )

            updated_user = update_user_generic(
                db,
                int(triage.user_id),
                UserUpdateRequest(
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone_number,
                ),
            )
            if updated_user is None:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=[{"success": False, "message": "User not found for this triage"}],
                )
            db.commit()
        except HTTPException:
            db.rollback()
            raise
        except Exception:
            db.rollback()
            raise

        customer_info, case_info = get_completed_triage_customer_and_case(db, triage)
        response_data = SubmitTriageResponseData(
            triage_id=str(triage.id),
            customer=customer_info,
            case=case_info,
            login_data=None,
        )

        payload["customer_email"] = customer_email
        payload["customer_name"] = customer_name
        payload["customer_id"] = int(triage.customer_id) if triage.customer_id else None
        payload["user_id"] = int(triage.user_id) if triage.user_id else None
        payload["case_id"] = int(case.id)
        payload["triage_id"] = triage_id
        payload["navigators"] = get_all_navigator_emails(db)
        payload["response_data"] = response_data
        payload["case_number"] = format_case_number(str(case.case_no))
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload["attendee_phone_number"] = phone_number
        payload["start_date"] = (
            case.start_date.strftime(settings.DATE_FORMAT) if case.start_date else None
        )
        payload["priority"] = case.priority.value if case.priority else None
        payload["case_type"] = case.case_type.value if case.case_type else None
        payload["status"] = case.status.value

        return EventResponseData(
            should_display=True,
            success=True,
            message="Triage re-submitted successfully.",
            data=response_data,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in handle_triage_re_submit: {e}")
        raise


@event(EventType.TRIAGE_SUBMITTED_CUS_CARD)  # type: ignore[misc]
async def handle_triage_submitted_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle triage submitted customer card event: Generate card JSON using template
    and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "triage_id": 1,
        "case_number": "CASE-100",
        "timestamp": "2021-01-01T00:00:00Z",
        "customer_name": "John Doe",
        # "meeting_url": "https://example.com/meeting", (optional)
        "start_time": "2021-01-01T00:00:00Z", (optional)
        "end_time": "2021-01-01T00:00:00Z", (optional)
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "case_number",
            "timestamp",
            "customer_name",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Triage Submitted Customer Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError(
                "Triage Submitted Customer Card event: Required keys not found in payload"
            )  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        customer_name = payload["customer_name"]
        # meeting_url = payload.get("meeting_url", "")
        start_time = payload.get("start_time", "")
        end_time = payload.get("end_time", "")
        triage_id = payload.get("triage_id", "")
        template, last_version = get_template_json(
            str(ComponentEnum.TRIAGE_SUBMITTED_CUS_CARD.value),
            str(UserRoleEnum.CUSTOMER.value),
            "timeline",
        )
        timeline_type = get_timeline_type(
            db,
            ComponentEnum.TRIAGE_SUBMITTED_CUS_CARD.value,
            UserRoleEnum.CUSTOMER.value,
            last_version,
        )
        if timeline_type is None:
            raise ValueError(
                "Triage Submitted Customer Card event: Timeline type not found"
            )  # noqa: TRY301

        placeholder_values = {
            "action_by": customer_name,
            "case_number": case_number,
            "timestamp": timestamp,
            # "meeting_url": meeting_url,
            "start_time": start_time,
            "end_time": end_time,
            "triage_id": encrypt_id(str(triage_id)) if triage_id else "",
            "action_buttons": {
                # "free_call": True if meeting_url else False,
                "view_triage": True if triage_id else False,
            },
        }

        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)
        if errors:
            logger.error(
                f"Triage Submitted Customer Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(
                f"Triage Submitted Customer Card event: Template processing failed: {', '.join(errors)}"
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
            message="Triage submitted customer card generated and saved to timeline successfully.",
            data={},
        )
    except Exception as e:
        logger.exception(
            f"Triage Submitted Customer Card event: Error in handle_triage_submitted_cus_card: {e}"
        )
        raise


@event(EventType.TRIAGE_CUS_EMAIL)  # type: ignore[misc]
async def send_triage_customer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send welcome email to the customer after triage form submission.

    Example payload:
    {
        "customer_email": "customer@example.com",
        "customer_name": "John Doe",
        "case_id": 1
    }
    """
    from app.core.security import create_analytics_token
    from app.enums.base import NameExtractionOption
    from app.utils.formatters import extract_name_parts

    try:
        payload = event.payload
        required_keys = ["customer_email", "customer_name"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        email = payload.get("customer_email")
        customer_name = extract_name_parts(
            payload.get("customer_name"), NameExtractionOption.FIRST
        )

        if not email:
            raise ValueError("Email not found in payload")  # noqa: TRY301

        case_id = payload.get("case_id")
        case = get_case_by_id(db, case_id) if case_id else None
        analytics_payload = {
            "case_id": case.id if case is not None else None,
            "event_type": EventType.EMAIL_CTA_CLICKED.value,
        }
        analytics_token = create_analytics_token(analytics_payload)

        response = await email_service.send_email(
            to_email=email,
            template=email_service.EmailTemplate.TRIAGE_CUSTOMER_NOTIFICATION,
            context={
                "customer_name": customer_name,
                "header_subtitle": "Welcome to Nova",
                "redirect_url": f"{settings.FRONTEND_URL}/login?analytics_token={analytics_token}",
            },
        )

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Triage customer welcome email sent successfully.",
            data={
                "customer_email": email,
                "customer_name": customer_name,
                "message_id": response.message_id,
            },
        )
    except Exception as e:
        logger.exception(f"Error in send_triage_customer_email: {e}")
        raise


@event(EventType.TRIAGE_RE_SUBMIT_CUS_EMAIL)  # type: ignore[misc]
async def send_triage_re_submit_customer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email to the customer after triage re-submission.

    Example payload:
    {
        "customer_email": "customer@example.com",
        "customer_name": "John Doe",
        "case_id": 1,
        "case_number": "CASE-100"
    }
    """
    from app.core.security import create_analytics_token

    try:
        payload = event.payload
        required_keys = ["customer_email", "customer_name"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        email = payload.get("customer_email")
        customer_name = extract_name_parts(
            payload.get("customer_name"), NameExtractionOption.FIRST
        )

        if not email:
            raise ValueError("Email not found in payload")  # noqa: TRY301

        case_id = payload.get("case_id")
        case_number = payload.get("case_number")
        case = get_case_by_id(db, case_id) if case_id else None
        analytics_payload = {
            "case_id": case.id if case is not None else None,
            "event_type": EventType.EMAIL_CTA_CLICKED.value,
        }
        analytics_token = create_analytics_token(analytics_payload)

        response = await email_service.send_email(
            to_email=email,
            template=email_service.EmailTemplate.TRIAGE_RESUBMIT_CUSTOMER_NOTIFICATION,
            context={
                "customer_name": customer_name,
                "case_number": case_number,
                "header_subtitle": "Triage details updated",
                "redirect_url": f"{settings.FRONTEND_URL}/login?analytics_token={analytics_token}",
            },
        )

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Triage re-submit customer email sent successfully.",
            data={
                "customer_email": email,
                "customer_name": customer_name,
                "message_id": response.message_id,
            },
        )
    except Exception as e:
        logger.exception(f"Error in send_triage_re_submit_customer_email: {e}")
        raise

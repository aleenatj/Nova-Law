"""
Password Reset Event Handlers

This module contains the password reset event handler functions.
It demonstrates the event-driven architecture using enums for type safety.

All event handlers are decorated with @event and automatically registered.
"""

import json
import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status as http_status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email import email_service
from app.db.models import Case, CaseEngage, CaseLawyer, EngageQuestionAnswers, Match, Lawyer
from app.db.models.transaction import Transaction
from app.db.services.case import get_case_by_id
from app.db.services.general import (
    get_all_navigator_emails,
    get_case_customer_user,
    get_case_details_url,
    get_case_lawyer_by_case_id,
    get_lawyers_for_case,
    get_case_summary,
    get_resolve_summary,
    get_timeline_type,
    get_resolve_by_case_id,
    get_match_status,
)
from app.db.services.invoice import get_invoice_transactional
from app.db.services.lawyer import check_match_confirm_exists
from app.db.services.payment import create_payment_transaction
from app.db.services.resolve import get_resolve_from_case_id, get_result_title
from app.db.services.timeline_event import (
    create_lawyer_matches,
    disable_timeline_action_buttons,
    get_match_lawyer_ids_by_case_id,
    get_timeline_event_from_map,
    save_lawyers_match,
    save_timeline_event,
    save_timeline_map,
    update_lawyer_interest_confirmed,
    update_timeline_event,
    validate_lawyers_and_get_errors,
)
from app.enums.component import ComponentEnum
from app.enums.events import EventType
from app.enums.match import MatchStatusEnum
from app.enums.payment import InvoiceStatusEnum, PaymentStatusEnum
from app.enums.user_role import UserRoleEnum
from app.events.dispatcher import event
from app.schemas.v1.event import Event, EventResponseData
from app.schemas.v1.timeline_event import MatchResponse
from app.enums.file_upload import ImageSize
from app.services.upload_service import UploadService
from app.utils.encryption import decrypt_id, encrypt_id
from app.utils.formatters import format_case_number, extract_name_parts
from app.enums.base import NameExtractionOption
from app.utils.helpers import (
    _parse_json_field,
    calculate_lawyer_experience,
    get_template_json,
    replace_placeholders,
)
from app.utils.validators import validate_event_payload
from app.websocket.manager import WebSocketManager

logger = logging.getLogger(__name__)
upload_service = UploadService()


@event(EventType.CASE_LAWYER_MATCH_CONFIRMED)  # type: ignore
async def handle_case_lawyer_match_confirmed(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case lawyer match confirmed request: confirm the lawyer match.
    Required payload:
    {
        "request_data": {
            "case_id": 1,
            "lawyers": ["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P"]
        }
    }
    """
    from app.db.services.general import get_case_summary_for_lawyer

    try:
        payload = event.payload
        required_keys = [
            {"request_data": ["case_id", "lawyers"]}
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        request_data = payload["request_data"]
        case_id = request_data.case_id
        lawyers = request_data.lawyers

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Invalid case ID format") from e

        case = get_case_by_id(db, case_id)
        if case is None:
            raise ValueError("Case not found")  # noqa: TRY301
        
        payload["case"] = case

        if case.is_profile_card_sent:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Case expert match already confirmed",
                },
            )

        case_lawyer = get_case_lawyer_by_case_id(
            db, case_id
        )
        if case_lawyer is not None:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Case already awarded to an expert",
                },
            )

        # Validate lawyers and get any errors
        lawyer_dict, validation_errors, invalid_encrypted_ids = (
            validate_lawyers_and_get_errors(db, lawyers)
        )
        # If no valid lawyers found, return error
        if not lawyer_dict:
            raise ValueError("No valid experts provided")  # noqa: TRY301

        if validation_errors:
            error_string = ",".join(validation_errors)
            raise ValueError("Invalid experts provided: " + error_string)  # noqa: TRY301

        # Lawyers who already have a match for this case (data already sent to them)
        existing_match_lawyer_ids = get_match_lawyer_ids_by_case_id(db, case_id)

        # Separate: lawyers we still need to send to vs those already sent
        lawyers_to_notify = {
            lid: lawyer for lid, lawyer in lawyer_dict.items()
            if lid not in existing_match_lawyer_ids
        }
        # If the list to send to is empty (same as already sent), show error
        if not lawyers_to_notify:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "All selected experts have already been sent a match for this case. Select new experts only.",
                },
            )
        case_resolve = case.case_resolves[0] if case.case_resolves else None

        customer_name = None
        partner_name = None
        case_summary = get_case_summary_for_lawyer(db, case)
        recommended_pathway = ""

        if case_resolve:
            resolve_id = case_resolve.resolve_id
            if case_resolve.resolve:
                customer_name = case_resolve.resolve.customer_name if case_resolve.resolve.customer_name else None
                partner_name = case_resolve.resolve.partner_name if case_resolve.resolve.partner_name else None
                recommended_pathway = get_result_title(case_resolve.resolve)
        else:
            resolve_id = None
            if case.is_triage is True:
                from app.db.services.triage import get_triage_from_case_id
                triage = get_triage_from_case_id(db, case.id)
                if triage:
                    triage_id = triage.id
                    payload["triage_id"] = triage_id

        kyc_id = case.case_engages[0].engage_id if case.case_engages else None
        if resolve_id:
            resolve_id = encrypt_id(resolve_id)
            payload["resolve_id"] = resolve_id
        if kyc_id:
            from app.db.models.question_answers import QuestionAnswers
            from app.db.models.engage_question_answers import EngageQuestionAnswers

            question_answers = db.query(QuestionAnswers).join(EngageQuestionAnswers, EngageQuestionAnswers.question_answer_id == QuestionAnswers.id).filter(EngageQuestionAnswers.engage_id == kyc_id).all()

            question_answer_map = {}
            if question_answers:
                for qa in question_answers:
                    question_answer_map[qa.question_identifier] = json.loads(qa.answer)
            
            customer_name = None
            partner_name = None
            if "1.1" in question_answer_map:
                customer_name = question_answer_map["1.1"][0]["value"]
            if "1.3" in question_answer_map:
                customer_last_name = question_answer_map["1.3"][0]["value"]
                customer_name = customer_name + " " + customer_last_name
            if "2.1" in question_answer_map:
                partner_name = question_answer_map["2.1"][0]["value"]
            if "2.3" in question_answer_map:
                partner_last_name = question_answer_map["2.3"][0]["value"]
                partner_name = partner_name + " " + partner_last_name

            kyc_id = encrypt_id(kyc_id)
            payload["kyc_id"] = kyc_id
        payload["case_id"] = case_id
        payload["case_number"] = format_case_number(case.case_no)
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload["customer_name"] = customer_name
        payload["partner_name"] = partner_name
        payload["case_summary"] = case_summary
        payload["recommended_pathway"] = recommended_pathway
        case_ai_summary = case.summary if case.summary is not None else [{
            "title": "Processing",
            "description": "AI summary generation is being processed."
        }]
        
        # if isinstance(case_summary, dict) and "summary" in case_summary:
        #     case_ai_summary = [
        #         {
        #             "title": item.get("question", ""),
        #             "description": item.get("answer", ""),
        #         }
        #         for item in case_summary["summary"]
        #         if isinstance(item, dict)
        #     ]
        payload["case_ai_summary"] = case.summary if case and case.summary is not None else case_ai_summary

        navigator_emails = get_all_navigator_emails(db)
        payload["navigators"] = navigator_emails

        # Create or update matches for valid lawyers
        success = create_lawyer_matches(
            db, case, lawyer_dict, payload["current_user"]
        )
        if not success:
            raise ValueError("Failed to create expert matches")  # noqa: TRY301

        lawyer_users = {
            lawyer.id: lawyer.user if lawyer.user else None
            for lawyer in lawyers_to_notify.values()
        }

        valid_lawyer_users = {k: v for k, v in lawyer_users.items() if v is not None}
        if valid_lawyer_users:
            payload["notified_lawyers"] = list(lawyers_to_notify.values())
        else:
            payload["lawyers"] = []

        retun_data = {
            "error_list": validation_errors,
            "invalid_lawyer_ids": invalid_encrypted_ids,
        }
        data_response = MatchResponse.model_validate(retun_data)

        disable_timeline_action_buttons(
            db=db,
            component_buttons={
                str(ComponentEnum.CUSTOMER_KYC_NN_CARD.value): ["review_profiles"]
            },
            related_id=int(case_id),
        )

        return EventResponseData(
            success=True,
            message=f"Expert matching completed for {customer_name}. Case - {payload["case_number"]}",
            data=data_response,
        )

    except Exception as e:
        logger.exception(f"Error in CASE_LAWYER_MATCH_CONFIRMED: {e}")
        raise


@event(EventType.CASE_NEW_NN_EMAIL)  # type: ignore
async def send_case_new_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to Nova navigator when lawyer matches for a case are confirmed.

    Required payload:
    {
        "case_id": 1,
        "navigators": [
            {
                "navigator_email": "navigator@novalaw.ai",
                "navigator_name": "John Smith"
            }
        ],
        "case_number": "CASE-100",
        "notified_lawyers": [
            <Lawyer object>
        ]
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "navigators", "case_number", "notified_lawyers"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)
        navigators = payload.get("navigators")
        case_number = payload.get("case_number")
        customer_name = payload.get("customer_name", "")
        notified_lawyers = payload.get("notified_lawyers")
        if navigators is None:
            logger.warning("No navigators found in payload")
            return EventResponseData(
                success=False,
                message="No navigators found in payload",
                data=[],
            )
        response_list = []
        navigator_emails = [str(navigator.get("navigator_email")) for navigator in navigators if navigator.get("navigator_email") is not None]
        
        # Format notified lawyers from payload to required format
        formatted_notified_lawyers = []
        for lawyer in notified_lawyers:
            first_name = lawyer.user.first_name if lawyer.user.first_name is not None else ""
            last_name = lawyer.user.last_name if lawyer.user.last_name is not None else ""
            lawyer_name = first_name + " " + last_name
            photo_url = upload_service.get_image_url(lawyer.photo_url, ImageSize.THUMBNAIL) if lawyer.photo_url is not None else ""
            formatted_notified_lawyers.append({
                "name": lawyer_name,
                "photo_url": photo_url
            })

        if navigator_emails:
            # Send email notification
            response = await email_service.send_email(
                bcc=navigator_emails,
                template=email_service.EmailTemplate.CASE_NEW_NAVIGATOR_NOTIFICATION,
                context={
                    "navigator_name": "Navigator",
                    "case_url": case_url,
                    "header_subtitle": "Case Expert Match Confirmation",
                    "case_number": case_number,
                    "notified_lawyers": formatted_notified_lawyers,
                    "customer_name": customer_name
                },
            )
            response_list.append({
                "navigator_email": navigator_emails,
                "navigator_name": "Navigator",
                "message_id": response.message_id,
            })

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Expert match confirmation email sent successfully to navigators",
            data=response_list,
        )

    except Exception as e:
        logger.exception(f"Error in send_case_new_navigator_email: {e}")
        raise


@event(EventType.CASE_NEW_LAW_EMAIL)  # type: ignore
async def send_case_new_lawyer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to lawyers who have been selected and matched to a case.

    Required payload:
    {
        "case_id": 1,
        "notified_lawyers": [
            <Lawyer object>
        ],
        "case_number": "CASE-100",
        "case_ai_summary": dict,
        "recommended_pathway": str (optional)
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "notified_lawyers", "case_number", "case_ai_summary"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)
        lawyers = payload.get("notified_lawyers")
        case_number = payload.get("case_number")
        case_ai_summary = payload.get("case_ai_summary")
        recommended_pathway = payload.get("recommended_pathway", "")
        if lawyers is None:
            logger.warning("No experts email data found in payload")
            return EventResponseData(
                success=False,
                message="No experts email data found in payload",
                data=[],
            )
        response_list = []
        for lawyer in lawyers:
            email = lawyer.user.email
            first_name = lawyer.user.first_name if lawyer.user.first_name is not None else ""
            last_name = lawyer.user.last_name if lawyer.user.last_name is not None else ""
            lawyer_name = extract_name_parts(first_name + " " + last_name, NameExtractionOption.FIRST)

            if email is not None and lawyer_name is not None:
                # Send email notification
                response = await email_service.send_email(
                    to_email=email,
                    template=email_service.EmailTemplate.CASE_NEW_LAWYER_NOTIFICATION,
                    context={
                        "lawyer_name": lawyer_name,
                        "case_url": case_url,
                        "header_subtitle": "New Case Assignment",
                        "case_number": case_number,
                        "case_summary": case_ai_summary,
                        "recommended_pathway": recommended_pathway
                    },
                )
                response_list.append({
                    "lawyer_email": email,
                    "lawyer_name": lawyer_name,
                    "message_id": response.message_id,
                })

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Expert match confirmation email sent successfully to experts",
            data=response_list,
        )

    except Exception as e:
        logger.exception(f"Error in send_case_new_lawyer_email: {e}")
        raise


@event(EventType.CASE_LAWYER_INTR_CONFIRMED)  # type: ignore
async def handle_case_lawyer_intr_confirmed(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case lawyer interest confirmed request: Send lawyer to customer.
    Required payload:
    {
        "request_data": {
            "case_id": 1,
            "lawyers": ["SHpaLXRoODN3anVxejFFRk9HekhSRHd2S3NVUVRaUUlfQVE9P"]
        }
    }
    """
    try:
        payload = event.payload
        required_keys = [{"request_data": ["case_id", "lawyers"]}]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        request_data = payload["request_data"]

        case_id = request_data.case_id
        lawyers = request_data.lawyers

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Invalid case ID format") from e
        payload["case_id"] = case_id

        case = get_case_by_id(db, case_id)
        if case is None:
            raise ValueError("Case not found")  # noqa: TRY301

        if case.is_match_confirmed is False:
            raise ValueError("Case expert match not confirmed")  # noqa: TRY301

        case_lawyer = get_case_lawyer_by_case_id(
            db, request_data.case_id
        )
        if case_lawyer is not None:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Case already awarded to an expert",
                },
            )

        lawyer_list = check_match_confirm_exists(db, case_id)
        if lawyer_list is True:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Expert profiles were already confirmed for this case",
                },
            )

        payload["case_number"] = format_case_number(case.case_no)

        user = get_case_customer_user(db, case_id)
        if user is None:
            raise ValueError("Customer not found or not active")  # noqa: TRY301
        payload["customer_email"] = user.email
        first_name = user.first_name if user.first_name is not None else ""
        last_name = user.last_name if user.last_name is not None else ""
        payload["customer_name"] = first_name + " " + last_name
        payload["customer_user"] = user

        # Validate lawyers and get any errors
        lawyer_dict, validation_errors, invalid_encrypted_ids = (
            validate_lawyers_and_get_errors(db, lawyers)
        )
        # If no valid lawyers found, return error
        if not lawyer_dict:
            raise ValueError("No valid experts provided")  # noqa: TRY301

        if invalid_encrypted_ids and validation_errors:
            error_message = ",".join(validation_errors)
            raise ValueError(error_message)  # noqa: TRY301

        # Create or update matches for valid lawyers
        success, message = update_lawyer_interest_confirmed(
            db, case, lawyer_dict, payload["current_user"]
        )
        if not success:
            raise ValueError("Failed to update expert interest confirmation: " + message)  # noqa: TRY301
        
        customer_name = None
        customer_first_name = ""
        customer_last_name = ""
        if case.case_customers and len(case.case_customers) > 0:
            customer = case.case_customers[0].customer
            # Get user data from the customer relationship
            user = customer.user
            customer_first_name = user.first_name if user.first_name else ""
            customer_last_name = user.last_name if user.last_name else ""
            customer_name = f"{customer_first_name} {customer_last_name}".strip()

        payload["customer_name"] = customer_name

        navigator_emails = get_all_navigator_emails(db)
        payload["navigators"] = navigator_emails
        payload["lawyers"] = list(lawyer_dict.values())
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload["lawyers"] = list(lawyer_dict.values())

        disable_timeline_action_buttons(
            db=db,
            component_buttons={
                str(ComponentEnum.CASE_INTEREST_NN_CARD.value): ["send_reviewed_profiles"]
            },
            related_id=int(case_id),
        )

        return EventResponseData(
            success=True,
            message=f"Expert interest confirmed and sent to {customer_first_name} successfully. Case - {payload["case_number"]}",
            data={},
        )

    except Exception as e:
        logger.exception(f"Case Expert Interest Confirmed event: Error in handle_case_expert_intr_confirmed: {e}")
        raise

@event(EventType.CUSTOMER_ACCEPT_LAWYER)  # type: ignore
async def handle_customer_accept_lawyer(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer accept lawyer request: process lawyer acceptance by customer.
    Handles all validation logic and creates the CaseLawyer record.
    Required payload:
    {
        "case_id": 1,
        "lawyer_id": 1,
        "customer_id": 1,
        "lawyer": <Lawyer object>,
        "customer": <Customer object>,
        "case_number": "CASE-100"
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "lawyer_id", "customer_id", "lawyer", "customer", "case_number"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            return EventResponseData(
                success=False,
                message=f"Payload validation failed: {validation['message']}",
                data={},
            )

        case_id = payload["case_id"]
        lawyer_id = payload["lawyer_id"]
        customer_id = payload["customer_id"]
        lawyer = payload["lawyer"]
        customer = payload["customer"]

        invoice_amount = settings.INIT_PMT_AMOUNT if settings.INIT_PMT_AMOUNT and settings.INIT_PMT_AMOUNT > 0 else None
        if invoice_amount is None:
            raise ValueError("Invoice amount is not defined") # noqa: TRY301
        payload["invoice_amount"] = invoice_amount

        # Validate match exists and is interested
        match = db.query(Match).filter(
            Match.case_id == case_id,
            Match.lawyer_id == lawyer_id,
            Match.status == MatchStatusEnum.INTERESTED,
            Match.is_confirmed == True
        ).first()
        if not match:
            return EventResponseData(
                success=False,
                message="No interested match found for this case and expert",
                data={},
            )


        # Check if any lawyer is already accepted for this case
        existing_case_lawyer = db.query(CaseLawyer).filter(
            CaseLawyer.case_id == case_id
        ).first()

        if existing_case_lawyer:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "An expert has already been accepted for this case",
                },
            )

        # Create case_lawyer record
        case_lawyer = CaseLawyer(case_id=case_id, lawyer_id=lawyer_id)
        db.add(case_lawyer)

        # Update case is_lawyer_assigned flag
        case_obj = db.query(Case).filter(Case.id == case_id).first()
        if case_obj:
            case_obj.is_lawyer_assigned = True

        db.commit()

        # Fetch other interested lawyers who were not selected
        other_lawyers = db.query(Lawyer).join(
            Match, Match.lawyer_id == Lawyer.id
        ).filter(
            Match.case_id == case_id,
            Match.lawyer_id != lawyer_id,
        ).all()

        payload["other_lawyers"] = other_lawyers

        # Disable engage_with button in CASE_PROFILE_CUS_CARD timeline event
        disable_timeline_action_buttons(
            db=db,
            component_buttons={
                str(ComponentEnum.CASE_PROFILE_CUS_CARD.value): ["engage_with","talk_to_lawyer"],
                str(ComponentEnum.CUSTOMER_TALK_TO_LAW_CUS_CARD.value): ["choose_another_lawyer"],
                str(ComponentEnum.CUSTOMER_TALK_TO_NN_CUS_CARD.value): ["choose_another_lawyer"],
            },
            related_id=int(case_id),
        )
        for other_lawyer in other_lawyers:
            disable_timeline_action_buttons(
                db=db,
                component_buttons={
                    str(ComponentEnum.CASE_NEW_MATCH_LAW_CARD.value): ["raise_interest","decline_match","ask_more_details"],
                    str(ComponentEnum.CASE_MORE_DETAILS_LAW_CARD.value): ["raise_interest","decline_match"],
                    str(ComponentEnum.CASE_DECLINE_LAW_CARD.value): ["raise_interest"],
                },
                related_id=f"{case_id}_{other_lawyer.id}",
            )

        # Get engage url from law firm
        # TODO: Currently, the `engage_url` is taken from the first associated law firm.
        # In the future, update this to support lawyers associated with multiple law firms,
        # where each firm may have a different `engage_url`.
        engage_url = None
        if case_lawyer.lawyer.lawyer_law_firms:
            # Get the first law firm's engage_form_url
            law_firm = case_lawyer.lawyer.lawyer_law_firms[0].law_firm
            engage_url = law_firm.engage_form_url if law_firm else None

        case_type = ""
        if case_lawyer.case.case_type:
            case_type = case_lawyer.case.case_type.value

        navigator_emails = get_all_navigator_emails(db)
        payload["navigators"] = navigator_emails
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload["case_type"] = case_type
        payload["case_number"] = format_case_number(case_lawyer.case.case_no)

        # Get customer name from case_customers relationship
        if case_lawyer.case.case_customers:
            customer_user = case_lawyer.case.case_customers[0].customer.user
            payload["customer_name"] = f"{customer_user.first_name} {customer_user.last_name}"
        # Get lawyer email from lawyer relationship
        payload["lawyer_email"] = case_lawyer.lawyer.user.email
        payload["lawyer_name"] = case_lawyer.lawyer.user.first_name + " " + case_lawyer.lawyer.user.last_name
        payload["lawyer"] = case_lawyer.lawyer
        payload["engage_url"] = engage_url

        should_display = True
        message = f"Expert accepted successfully by customer. Case - {payload["case_number"]}"
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = True
            message = f"{payload["lawyer_name"]} will be notified."
        # Return success response
        return EventResponseData(
            should_display=should_display,
            success=True,
            message=message,
            data={
                "case_id": case_id,
                "lawyer_id": lawyer_id,
                "customer_id": customer_id,
                "lawyer": lawyer,
                "customer": customer,
            },
        )

    except Exception as e:
        logger.exception(f"Error in handle_customer_accept_lawyer: {e}")
        db.rollback()
        raise


@event(EventType.CUSTOMER_PMT_REQUESTED)  # type: ignore
async def handle_customer_pmt_requested(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer initial payment requested event: Process payment initialization request.
    This event is triggered after customer accepts a lawyer.

    Required payload:
    {   "case_id": 1,
        "case_type": "Family Law",
        "case_number": "CASE-100",
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "lawyer_id",
            "case_number",
            "case_type",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            return EventResponseData(
                success=False,
                message=f"Payload validation failed: {validation['message']}",
                data={},
            )

        case_id = payload["case_id"]
        lawyer_id = payload["lawyer_id"]
        case_number = payload.get("case_number", "")
        case_type = payload.get("case_type", "")
        invoice_amount = payload.get("invoice_amount")

        timestamp = datetime.now(timezone.utc).isoformat()

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Customer Payment Requested event: Invalid case ID format") from e

        case = get_case_by_id(db, case_id)
        if case is None:
            raise ValueError("Customer Payment Requested event: Case not found")  # noqa: TRY301

        # raise Exception("test")
        invoice = get_invoice_transactional(db, case_id, lawyer_id, invoice_amount)
        if invoice is None:
            raise ValueError("Customer Payment Requested event: Invoice not found")  # noqa: TRY301

        status = ""
        # Prepare comprehensive payload for downstream events
        payload["amount_requested"] = int(invoice_amount)
        payload["status"] = status
        payload["timestamp"] = timestamp
        payload["invoice_id"] = invoice.id

        # Determine if message should be displayed based on event context:
        # - If this is a sub-event (parent_event_type is not None), don't display the message
        #   (it's part of another event's flow, e.g., CUSTOMER_ACCEPT_LAWYER)
        # - If this is a main event (parent_event_type is None), display the message
        #   (it was triggered directly from an API endpoint)
        should_display = event.parent_event_type is None

        # Return success response with all relevant data
        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Payment initialization requested successfully",
            data={
                "case_number": case_number,
                "case_type": case_type,
                "init_pmt_amount": int(invoice_amount),
                "status": status,
            },
        )

    except Exception as e:
        logger.exception(f"Error in handle_customer_pmt_requested: {e}")
        db.rollback()
        raise


@event(EventType.CUSTOMER_PMT_REQUESTED_CUS_CARD)  # type: ignore
async def handle_customer_pmt_requested_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer initial payment requested customer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "case_number": "CASE-001",
        "case_type": "Family Law",
        "lawyer": <Lawyer object>,
        "amount_requested": "50",
        "invoice_id": 1,
        "status": "Pending" #optional,
        "timestamp": "2021-01-01T00:00:00Z"
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "case_number", "case_type", "lawyer", "amount_requested", "timestamp", "invoice_id"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Customer Init Payment Requested Customer Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Customer Init Payment Requested Customer Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        case_type = payload["case_type"]
        lawyer = payload["lawyer"]
        amount_requested = payload["amount_requested"]
        status = payload.get("status", "")
        timestamp = payload["timestamp"]
        invoice_id = payload["invoice_id"]
        role_code = UserRoleEnum.CUSTOMER.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Customer Init Payment Requested Customer Card event: Invalid case ID format") from e

        template, last_version = get_template_json(
            str(ComponentEnum.CUSTOMER_PMT_REQUESTED_CUS_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CUSTOMER_PMT_REQUESTED_CUS_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Customer Init Payment Requested Customer Card event: Timeline type not found")  # noqa: TRY301

        # Get lawyer_name from lawyer object
        lawyer_name = ""
        if hasattr(lawyer, "user") and lawyer.user:
            lawyer_first_name = lawyer.user.first_name if lawyer.user.first_name else ""
            lawyer_last_name = lawyer.user.last_name if lawyer.user.last_name else ""
            lawyer_name = f"{lawyer_first_name} {lawyer_last_name}".strip()
        
        payment = create_payment_transaction(db, invoice_id, amount_requested)
        if payment is None:
            raise ValueError("Customer Init Payment Requested Customer Card event: Failed to create payment record")  # noqa: TRY301
        
        payment_id_encrypted = encrypt_id(str(payment.id))
        if payment_id_encrypted is None:
            raise ValueError("Customer Init Payment Requested Customer Card event: Failed to encrypt payment ID")  # noqa: TRY301

        # Prepare placeholder values
        placeholder_values = {
            "action_by": "",
            "timestamp": timestamp,
            "case_number": case_number,
            "case_type": case_type,
            "lawyer_name": lawyer_name,
            "amount_requested": str(amount_requested),
            "payment_id": payment_id_encrypted,
            "status": status,
            "failed_attempts": [],
            "action_buttons": {"make_payment": True},
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)
        if errors:
            logger.error(
                f"Customer Init Payment Requested Customer Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Customer Init Payment Requested Customer Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        timeline_event = save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=event.user_id,
        )        
        
        save_timeline_map(db, timeline_event.id, str(timeline_type.type_name), payment.id)

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Customer initial payment requested customer card generated and saved to timeline successfully.",
            data=card_data,
        )

    except Exception as e:
        logger.exception(
            f"Customer Init Payment Requested Customer Card event: Error in handle_customer_pmt_requested_cus_card: {e}"
        )
        raise


@event(EventType.CASE_OPEN_CUS_CARD)  # type: ignore
async def handle_case_open_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case open customer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "case_type": "Family Law",
        "case_number": "CASE-100",
        "status": "Open",
        "timestamp": "2021-01-01T00:00:00Z",
        "resolve_id": 1, # optional
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "case_type", "case_number", "status", "timestamp"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Open Customer Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Open Customer Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        case_type = payload["case_type"]
        case_status = payload["status"]
        timestamp = payload["timestamp"]
        role_code = UserRoleEnum.CUSTOMER.value
        resolve_id = None
        if "resolve_id" in payload:
            resolve_id = payload["resolve_id"]

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case Open Customer Card event: Invalid case ID format") from e


        template, last_version = get_template_json(str(ComponentEnum.CASE_OPEN_CUS_CARD.value), str(role_code), "timeline")

        timeline_type = get_timeline_type(db, ComponentEnum.CASE_OPEN_CUS_CARD.value, role_code, last_version)
        if timeline_type is None:
            raise ValueError("Case Open Customer Card event: Timeline type not found")  # noqa: TRY301

        summary, _ = get_resolve_summary(db, case_id)
        if summary is None:
            raise ValueError("Case Open Customer Card event: Summary not found")  # noqa: TRY301

        # Prepare placeholder values
        placeholder_values = {
            "status": case_status,
            "case_number": case_number,
            "case_type": case_type,
            "next_steps": "Complete a Know Your Case Form to help us understand your case better",
            "summary": summary,
            "timestamp": timestamp,
            "resolve_id": encrypt_id(str(resolve_id)) if resolve_id else None,
            "action_buttons":{
                "kyc_form":True,
                "view_resolve": True if resolve_id else False
            }
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(f"Case Open Customer Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Case Open Customer Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

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
            message="Case opened customer card generated and saved to timeline successfully.",
            data={},
        )

    except Exception as e:
        logger.exception(f"Case Open Customer Card event: Error in handle_case_open_cus_card: {e}")
        raise


@event(EventType.CASE_OPEN_NN_CARD)  # type: ignore
async def handle_case_open_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case open navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "case_number": "CASE-100",
        "timestamp": "2021-01-01T00:00:00Z",
        "resolve_id": 1, # optional
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "case_number", "timestamp"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Open Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Open Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        role_code = UserRoleEnum.NAVIGATOR.value
        resolve_id = None
        if "resolve_id" in payload:
            resolve_id = payload["resolve_id"]

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case Open Navigator Card event: Invalid case ID format") from e

        template, last_version = get_template_json(str(ComponentEnum.CASE_OPEN_NN_CARD.value), str(role_code), "timeline")

        timeline_type = get_timeline_type(db, ComponentEnum.CASE_OPEN_NN_CARD.value, role_code, last_version)
        if timeline_type is None:
            raise ValueError("Case Open Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Prepare placeholder values
        placeholder_values = {
            "action_by": "",
            "case_number": case_number,
            "timestamp": timestamp,
            "resolve_id": encrypt_id(str(resolve_id)) if resolve_id else None,
            "action_buttons": {"view_resolve": True} if resolve_id else {},
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)
        if errors:
            logger.error(f"Case Open Navigator Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Case Open Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data
        )

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case opened navigator card generated and saved to timeline successfully.",
            data={}
        )

    except Exception as e:
        logger.exception(f"Case Open Navigator Card event: Error in handle_case_open_nn_card: {e}")
        raise


@event(EventType.CUSTOMER_KYC_CUS_CARD)  # type: ignore
async def handle_customer_kyc_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer KYC card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "request_data": {
            "case_id": 1,
            "answers": [{"question_identifier": 1, "answer": [{"value": "John Doe"}]}]
        },
        "current_user": <User object with attributes: id, first_name, last_name, email, etc.>,
        "timestamp": "2021-01-01T00:00:00Z",
        "kyc_id": "Z0FBQUFBQm9rRHN4UU1UMVp"
    }
    """
    try:
        payload = event.payload
        required_keys = [{"request_data": ["case_id", "answers"]}, "current_user", "timestamp", "kyc_id"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Customer Alignment Check card event: Required keys not found in payload")  # noqa: TRY301

        request = payload["request_data"]
        case_id = request.case_id
        role_code = UserRoleEnum.CUSTOMER.value
        timestamp = payload["timestamp"]
        current_user = payload["current_user"]
        kyc_id = payload["kyc_id"]
        case_number = payload.get("case_number", None)
        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Customer Alignment Check card event: Invalid case ID format") from e

        template, last_version = get_template_json(str(ComponentEnum.CUSTOMER_KYC_CUS_CARD.value), str(role_code), "timeline")

        timeline_type = get_timeline_type(
            db, ComponentEnum.CUSTOMER_KYC_CUS_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Customer Alignment Check card event: Timeline type not found")  # noqa: TRY301

        first_name = current_user.first_name if current_user.first_name is not None else ""
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name
        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "status": "Completed",
            "action_buttons": {"view_kyc_details": True},
            "kyc_id": kyc_id,
            "case_number": case_number
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(f"Customer KYC card event: Template placeholder errors: {errors}")
            raise ValueError(f"Customer Alignment Check card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db, case_id=case_id, timeline_type=timeline_type, meta_data=card_data, action_user_id=current_user.id
        )
        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False
        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Customer Alignment Check customer card generated and saved to timeline successfully.",
            data={},
        )

    except Exception as e:
        logger.exception(f"Customer KYC card event: Error in handle_customer_kyc_cus_card: {e}")
        raise


# CUSTOMER_KYC_CUS_CARD is replaced by CUSTOMER_KYC_SUBMITTED_CUS_CARD
@event(EventType.CUSTOMER_KYC_SUBMITTED_CUS_CARD)  # type: ignore
async def handle_customer_kyc_submitted_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer KYC card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "request_data": {
            "case_id": 1
        },
        "first_name": "John",
        "kyc_id": kyc_id,
        "current_user": <User object with attributes: id, first_name, last_name, email, etc.>,
        "timestamp": "2021-01-01T00:00:00Z"
    }
    """
    try:
        payload = event.payload
        required_keys = [{"request_data": ["case_id"]}, "current_user", "timestamp", "kyc_id"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Customer Alignment Check card event: Required keys not found in payload")  # noqa: TRY301

        request = payload["request_data"]
        case_id = request.case_id
        role_code = UserRoleEnum.CUSTOMER.value
        timestamp = payload["timestamp"]
        current_user = payload["current_user"]
        case_number = payload.get("case_number", None)
        kyc_id = payload["kyc_id"]
        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Customer Alignment Check submitted customer card event: Invalid case ID format") from e

        template, last_version = get_template_json(str(ComponentEnum.CUSTOMER_KYC_SUBMITTED_CUS_CARD.value), str(role_code), "timeline")

        timeline_type = get_timeline_type(
            db, ComponentEnum.CUSTOMER_KYC_SUBMITTED_CUS_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Alignment Check submitted customer card event: Timeline type not found")  # noqa: TRY301

        first_name = current_user.first_name if current_user.first_name is not None else ""
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name
        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "first_name": payload["first_name"],
            "kyc_id": kyc_id,
            "action_buttons":{
                "view_alignment_check_details": True
            },
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(f"KYC submitted customer card event: Template placeholder errors: {errors}")
            raise ValueError(f"Alignment Check submitted customer card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db, case_id=case_id, timeline_type=timeline_type, meta_data=card_data, action_user_id=current_user.id
        )

        data = {str(ComponentEnum.CASE_PATHWAY_OVERVIEW_CUS_CARD.value): {
                "kyc_id": kyc_id}}
        result = update_timeline_event(db, str(case_id), data)
        if not result:
            logger.error(f"Failed to update timeline event for {case_id}")
            # raise ValueError("Failed to update timeline event")  # noqa: TRY301

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False
        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Alignment Check submitted customer card generated and saved to timeline successfully.",
            data={},
        )

    except Exception as e:
        logger.exception(f"KYC submitted customer card event: Error in handle_customer_kyc_submitted_cus_card: {e}")
        raise


@event(EventType.CASE_LAWYER_MATCHING)  # type: ignore
async def handle_case_lawyer_matching(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case lawyer matching event: select lawyers matching for the case and add to match table.
    Required payload:
    {
        "request_data": {
            "case_id": 1,
            "answers": [{"question_identifier": 1, "answer": [{"value": "John Doe"}]}] | []
        }
    }
    """
    from app.db.services.general import get_triage_by_case_id, get_lawyers_for_triage
    try:
        payload = event.payload
        status = True
        message = "Experts match created successfully."
        required_keys = [{"request_data": ["case_id"]}]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Expert Matching event: Required keys not found in payload")  # noqa: TRY301

        request = payload["request_data"]
        case_id = request.case_id
        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Expert Matching event: Invalid case ID format") from e

        case = get_case_by_id(db, case_id)
        if case is None:
            raise ValueError("Expert Matching event: Case not found")  # noqa: TRY301
        
        if case.is_triage is False:
            resolve = get_resolve_by_case_id(db, case_id)
            matched_lawyer_ids, matched_lawyers = get_lawyers_for_case(db, resolve)
        
        else:
            triage = get_triage_by_case_id(db, case_id)
            if triage is None:
                raise ValueError("Expert Matching event: Triage not found")  # noqa: TRY301
            
            triage_id = encrypt_id(str(triage.id))
            payload["triage_id"] = triage_id

            matched_lawyer_ids, matched_lawyers = get_lawyers_for_triage(db, triage)

        save_lawyers_match(db, case_id, matched_lawyer_ids)

        payload["matched_lawyers"] = matched_lawyers
        payload["timestamp"] = datetime.now(timezone.utc).isoformat()
        payload["case_id"] = case_id
        payload["case_number"] = format_case_number(case.case_no)
        if not matched_lawyer_ids:
            status = False
            message = "No experts matched for the case"

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False
        return EventResponseData(
            should_display=should_display,
            success=status,
            message=message,
            data={},
        )

    except Exception as e:
        logger.exception(f"Case Expert Matching event: Error in handle_case_expert_matching: {e}")
        raise


@event(EventType.CASE_DECLINE_NN_CARD)  # type: ignore
async def handle_case_decline_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case decline navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "case_number": "CASE-001",
        "current_user": <User object>,
        "lawyer_name": "John Smith",
        "decline_reason": ["Conflict of interest"],
        "decline_reason_other": "Other reason details",
        "customer_name": "John Doe",
        "timestamp": "2021-01-01T00:00:00Z"
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "case_number", "current_user", "lawyer_name", "decline_reason", "timestamp", "customer_name"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Decline Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Decline Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        current_user = payload["current_user"]
        lawyer_name = payload["lawyer_name"]
        decline_reason = payload["decline_reason"]
        decline_reason_other = payload["decline_reason_other"]
        timestamp = payload["timestamp"]
        customer_name = payload["customer_name"]
        role_code = UserRoleEnum.NAVIGATOR.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case Decline Navigator Card event: Invalid case ID format") from e

        template, last_version = get_template_json(str(ComponentEnum.CASE_DECLINE_NN_CARD.value), str(role_code), "timeline")

        timeline_type = get_timeline_type(db, ComponentEnum.CASE_DECLINE_NN_CARD.value, role_code, last_version)
        if timeline_type is None:
            raise ValueError("Case Decline Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Prepare action_by from current_user
        first_name = current_user.first_name if current_user.first_name is not None else ""
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name

        action_user_role = UserRoleEnum.from_id(current_user.user_roles[0].role_id).display_name
        if action_user_role  != UserRoleEnum.LAWYER.display_name:
            action_by = action_by + " (" + action_user_role + ")"

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "lawyer_name": lawyer_name,
            "reasons": decline_reason,
            "reason_other": decline_reason_other,
            "customer_name": customer_name,
            "action_buttons": {}
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(f"Case Decline Navigator Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Case Decline Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case decline navigator card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(f"Case Decline Navigator Card event: Error in handle_case_decline_nn_card: {e}")
        raise


@event(EventType.CASE_PROFILE_NN_CARD)  # type: ignore
async def handle_case_profile_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case profile navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "current_user": <User object>,
        "lawyers": [<Lawyer object>],
        "case_number": "CASE-001",
        "timestamp": "2021-01-01T00:00:00Z"
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "current_user", "lawyers", "case_number", "timestamp"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Profile Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Profile Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        current_user = payload["current_user"]
        lawyers = payload["lawyers"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        role_code = UserRoleEnum.NAVIGATOR.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case Profile Navigator Card event: Invalid case ID format") from e

        template, last_version = get_template_json(str(ComponentEnum.CASE_PROFILE_NN_CARD.value), str(role_code), "timeline")

        timeline_type = get_timeline_type(db, ComponentEnum.CASE_PROFILE_NN_CARD.value, role_code, last_version)
        if timeline_type is None:
            raise ValueError("Case Profile Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Prepare action_by from current_user
        first_name = current_user.first_name if current_user.first_name is not None else ""
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name

        # Format lawyer profiles
        lawyer_profiles = []
        for lawyer in lawyers:
            lawyer_user = lawyer.user
            first_name = lawyer_user.first_name if lawyer_user.first_name is not None else ""
            last_name = lawyer_user.last_name if lawyer_user.last_name is not None else ""
            lawyer_name = first_name + " " + last_name
            photo_url = upload_service.get_image_url(lawyer.photo_url, ImageSize.THUMBNAIL) if lawyer.photo_url is not None else ""
            lawyer_profiles.append({"name": lawyer_name, "photo_url": photo_url})

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "lawyer_profiles": lawyer_profiles,
            "action_buttons": {}
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(f"Case Profile Navigator Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Case Profile Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id
        )

        return EventResponseData(
            should_display=False,
            success=True,
            message="Case profile navigator card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(f"Case Profile Navigator Card event: Error in handle_case_profile_nn_card: {e}")
        raise

@event(EventType.CUSTOMER_KYC_NN_CARD)  # type: ignore
async def handle_customer_kyc_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Generate and save CUSTOMER_KYC_NN_CARD timeline card.

    Required payload:
    {
        "case_id": "1",
        "case_number": "CASE-001",
        "customer_name": "John Doe",
        "matched_lawyers": <Lawyer object with attributes: id, name, photo_url, etc.>,
        "current_user": <User object with attributes: id, first_name, last_name, email, etc.>,
        "timestamp": "2021-01-01T00:00:00Z",
        "kyc_id": "Z0FBQUFBQm9rRHN4UU1UMVp"
    }
    """
    from app.db.models.question_answers import QuestionAnswers
    from app.db.models.engage_question_answers import EngageQuestionAnswers
    try:
        payload = event.payload
        required_keys = ["case_id", "case_number", "current_user", "timestamp", "kyc_id"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Customer Alignment Check Navigator Card event: Payload validation failed for {EventType.CUSTOMER_KYC_NN_CARD.value}: {validation}"
            )
            raise ValueError("Customer Alignment Check Navigator Card event: Required keys not found in payload")  # noqa: TRY301


        case_id = payload["case_id"]
        case_number = payload.get("case_number")
        matched_lawyers = payload.get("matched_lawyers")
        timestamp = payload.get("timestamp")
        current_user = payload.get("current_user")
        kyc_id = payload.get("kyc_id")
        customer_name = payload.get("customer_name")
        role_code = UserRoleEnum.NAVIGATOR.value


        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Customer Alignment Check Navigator Card event: Invalid case ID format") from e

        case = get_case_by_id(db, case_id)
        if case is None:
            raise ValueError("Customer Alignment Check Navigator Card event: Case not found")  # noqa: TRY301

        resolve_id = None
        triage_id = None
        if case.is_triage is False:
            resolve = get_resolve_from_case_id(db, case_id)
            if resolve is None:
                raise ValueError("Customer Alignment Check Navigator Card event: Resolve ID not found")  # noqa: TRY301
            
            if resolve:
                resolve_id = encrypt_id(str(resolve.id))
                payload["resolve_id"] = resolve_id
        else:
            from app.db.services.triage import get_triage_from_case_id
            triage = get_triage_from_case_id(db, case_id)
            if triage is None:
                raise ValueError("Customer Alignment Check Navigator Card event: Triage ID not found")  # noqa: TRY301
            triage_id = encrypt_id(str(triage.id))
            payload["triage_id"] = triage_id

        case_summary = get_case_summary(db, case)
        if case_summary is None:
            raise ValueError("Customer Alignment Check Navigator Card event: Summary not found")  # noqa: TRY301

        # Format matched lawyers from payload to required format
        formatted_matched_lawyers = []
        if matched_lawyers:
            for lawyer in matched_lawyers:
                user = lawyer.user
                first_name = user.first_name if user.first_name is not None else ""
                last_name = user.last_name if user.last_name is not None else ""
                lawyer_name = first_name + " " + last_name
                photo_url = upload_service.get_image_url(lawyer.photo_url, ImageSize.THUMBNAIL) if lawyer.photo_url is not None else ""
                formatted_matched_lawyers.append({
                    "name": lawyer_name,
                    "photo_url": photo_url
                })

        engage_id = int(decrypt_id(kyc_id))
        qa = (
            db.query(QuestionAnswers.answer)
            .join(
                EngageQuestionAnswers,
                EngageQuestionAnswers.question_answer_id == QuestionAnswers.id,
            )
            .filter(
                EngageQuestionAnswers.engage_id == engage_id,
                QuestionAnswers.question_identifier == "book_free_call",
            )
            .first()
        )
        call_schedule_info = {}
        if qa and qa.answer:
            parsed = json.loads(qa.answer)
            if parsed:
                call_schedule_info = parsed[0].get("value") or {}

        # Get template
        template, last_version = get_template_json(str(ComponentEnum.CUSTOMER_KYC_NN_CARD.value), str(role_code), "timeline")


        timeline_type = get_timeline_type(db, ComponentEnum.CUSTOMER_KYC_NN_CARD.value, role_code, last_version)
        if timeline_type is None:
            raise ValueError("Customer Alignment Check Navigator Card event: Timeline type not found")  # noqa: TRY301


        # Prepare action_by from current_user
        first_name = current_user.first_name if current_user.first_name is not None else ""
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name


        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "case_number": case_number,
            "case_summary": case_summary,
            "timestamp": timestamp,
            "matched_lawyers": formatted_matched_lawyers,
            "kyc_id": kyc_id,
            "resolve_id": resolve_id,
            "triage_id": triage_id,
            "customer_name": customer_name,
            "call_schedule_info": call_schedule_info,
            "action_buttons": {
                "review_profiles": True,
                "resolve_details": False if resolve_id is None or resolve_id == "" else True,
                "triage_details": False if triage_id is None or triage_id == "" else True,
                "kyc_details": True
            }
        }


        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)


        if errors:
            logger.error(f"Customer KYC Navigator Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Customer Alignment Check Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        timeline_event = save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id
        )
        timeline = get_timeline_event_from_map(db, str(timeline_type.type_name), int(case_id), timeline_event.id)
        if not timeline:
            save_timeline_map(db, int(timeline_event.id), str(timeline_type.type_name), int(case_id))

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False
        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Customer Alignment Check Navigator card generated and saved to timeline successfully.",
            data=card_data
        )


    except Exception as e:
        logger.exception(f"Customer KYC Navigator Card event: Error in handle_customer_kyc_nn_card: {e}")

        raise


@event(EventType.CASE_PROFILE_CUS_CARD)  # type: ignore
async def handle_case_profile_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case profile customer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "current_user": <user_object>,
        "lawyers": [<Lawyer object>],
        "case_number": "CASE-001",
        "timestamp": "2021-01-01T00:00:00Z",
        "customer_user": <user_object>
    }
    """
    from app.utils.formatters import format_expertises
    from app.utils.formatters import format_accredited_specialisms

    try:
        payload = event.payload
        required_keys = ["case_id", "current_user", "lawyers", "case_number", "timestamp", "customer_user"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Profile Customer Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Profile Customer Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        current_user = payload["current_user"]
        lawyers = payload["lawyers"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        role_code = UserRoleEnum.CUSTOMER.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case Profile Customer Card event: Invalid case ID format") from e

        customer_user = payload["customer_user"]
        customer_first_name = customer_user.first_name if customer_user.first_name is not None else ""

        # Get template and timeline type
        template, last_version = get_template_json(
            str(ComponentEnum.CASE_PROFILE_CUS_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(db, str(ComponentEnum.CASE_PROFILE_CUS_CARD.value), str(role_code), last_version)
        if not timeline_type:
            raise ValueError("Case Profile Customer Card event: Timeline type not found")  # noqa: TRY301

        # Prepare lawyer profiles data
        lawyer_profiles = []
        for lawyer in lawyers:
            lawyer_user = lawyer.user
            first_name = lawyer_user.first_name if lawyer_user.first_name is not None else ""
            last_name = lawyer_user.last_name if lawyer_user.last_name is not None else ""
            lawyer_name = first_name + " " + last_name
            photo_url = upload_service.get_image_url(lawyer.photo_url, ImageSize.LARGE) if lawyer.photo_url is not None else ""
            # expert_type = [xp.expert_type for xp in lawyer.expert_types] if lawyer.expert_types is not None else []
            expertises = []
            expertises_other = {}
            if hasattr(lawyer, "expertises") and lawyer.expertises:
                expertises = lawyer.expertises
            if hasattr(lawyer, "expertises_other") and lawyer.expertises_other:
                expertises_other = _parse_json_field(lawyer.expertises_other, default={})
            lawyer_expertises = format_expertises(expertises, expertises_other)

            accredited_specialisms = []
            accredited_specialisms_other = []
            if hasattr(lawyer, "accredited_specialisms") and lawyer.accredited_specialisms:
                accredited_specialisms = lawyer.accredited_specialisms
            if hasattr(lawyer, "accredited_specialism_other") and lawyer.accredited_specialism_other:
                accredited_specialisms_other = _parse_json_field(lawyer.accredited_specialism_other, default=[])
            lawyer_accreditations = format_accredited_specialisms(accredited_specialisms, accredited_specialisms_other)
            
            lawyer_expert_types = []
            if hasattr(lawyer, "expert_types") and lawyer.expert_types:
                lawyer_expert_types = [et.expert_type.value for et in lawyer.expert_types if not et.expert_type.is_other()]
            if hasattr(lawyer, "expert_types_other") and lawyer.expert_types_other:
                lawyer_expert_types.append(lawyer.expert_types_other.capitalize())
            lawyer_expert_types.sort()

            lawyer_experience = calculate_lawyer_experience(lawyer)
            # Construct lawyer location using city, county and country
            city = lawyer.city if hasattr(lawyer, "city") and lawyer.city is not None else ""
            country = lawyer.country if hasattr(lawyer, "country") and lawyer.country is not None else ""
            county = lawyer.county if hasattr(lawyer, "county") and lawyer.county is not None else ""
            lawyer_location = f"{city}, {county}, {country}".strip(", ") if city or county or country else ""
            data = {
                "lawyer_id": encrypt_id(lawyer.id),
                "lawyer_name": lawyer_name,
                "lawyer_photo_url": photo_url,
                "lawyer_experience": lawyer_experience,
                "lawyer_expert_types": lawyer_expert_types,
                "lawyer_expertises": lawyer_expertises,
                "lawyer_accreditations": lawyer_accreditations,
                "lawyer_about": lawyer.about if lawyer.about is not None else "",
                "lawyer_rate": int(lawyer.hourly_rate) if lawyer.hourly_rate is not None else "",
                "lawyer_location": lawyer_location,
                "lawyer_specialization": None, # lawyer.accredited_specialisations if lawyer.accredited_specialisations is not None else "",
                "lawyer_testimonial": lawyer.testimonial if lawyer.testimonial is not None else "",
            }
            lawyer_profiles.append(data)

        # Prepare values for template replacement
        placeholder_values = {
            "action_by": f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() if hasattr(current_user, 'first_name') else "System",
            "timestamp": timestamp,
            "first_name": customer_first_name,
            "case_number": case_number,
            "lawyer_profiles": lawyer_profiles
        }

        # Generate card data using template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(f"Case Profile Customer Card event: Template replacement errors: {', '.join(errors)}")
            raise ValueError(f"Case Profile Customer Card event: Template replacement failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        timeline_event = save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id if hasattr(current_user, 'id') else None
        )

        timeline = get_timeline_event_from_map(db, str(timeline_type.type_name), int(case_id), timeline_event.id)
        if not timeline:
            save_timeline_map(db, int(timeline_event.id), str(timeline_type.type_name), int(case_id))
        return EventResponseData(
            should_display=False,
            success=True,
            message="Case profile customer card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(f"Case Profile Customer Card event: Error in handle_case_profile_cus_card: {e}")
        raise


@event(EventType.CASE_MORE_DETAILS)  # type: ignore
async def handle_case_more_details(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case more details event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "lawyer_request": "What is the case about?",
        "case_number": "CASE-001",
        "current_user": <User object>,
        "timestamp": "2021-01-01T00:00:00Z"
    }
    """
    try:
        payload = event.payload
        required_keys = ["case", "lawyer_request", "case_number", "current_user", "timestamp"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case More Details event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case More Details event: Required keys not found in payload")  # noqa: TRY301

        #todo: add logic future enhancement
        case_id = payload["case"].id
        lawyer_id = payload["lawyer"].id
        disable_timeline_action_buttons(
            db=db,
            component_buttons={
                str(ComponentEnum.CASE_NEW_MATCH_LAW_CARD.value): ["raise_interest","decline_match","ask_more_details"],
                str(ComponentEnum.CASE_DECLINE_LAW_CARD.value): ["raise_interest"]      
            },
            related_id=f"{case_id}_{lawyer_id}",
        )

        should_display = True
        message = f"Successfully requested more details for the case. Case - {payload["case_number"]}"
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = True
            message = f"You have requested more details for this case. Case - {payload["case_number"]}"

        return EventResponseData(
            should_display=should_display,
            success=True,
            message=message,
            data={}
        )
    except Exception as e:
        logger.exception(f"Case More Details event: Error in handle_case_more_details: {e}")
        raise

@event(EventType.CASE_NEW_NN_CARD)  # type: ignore
async def handle_case_new_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case new navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "customer_name": "John Doe",
        "case_number": "CASE-001",
        "current_user": <User object>,
        "timestamp": "2021-01-01T00:00:00Z",
        "notified_lawyers": [<Lawyer object>]
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "customer_name", "case_number", "current_user", "timestamp", "notified_lawyers"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case New Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case New Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        current_user = payload["current_user"]
        timestamp = payload["timestamp"]
        notified_lawyers = payload["notified_lawyers"]
        role_code = UserRoleEnum.NAVIGATOR.value
        customer_name = payload["customer_name"]

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case New Navigator Card event: Invalid case ID format") from e

        # Format notified lawyers from payload to required format
        formatted_notified_lawyers = []
        for lawyer in notified_lawyers:
            first_name = lawyer.user.first_name if lawyer.user.first_name is not None else ""
            last_name = lawyer.user.last_name if lawyer.user.last_name is not None else ""
            lawyer_name = first_name + " " + last_name
            photo_url = upload_service.get_image_url(lawyer.photo_url, ImageSize.THUMBNAIL) if lawyer.photo_url is not None else ""
            formatted_notified_lawyers.append({
                "name": lawyer_name,
                "photo_url": photo_url
            })

        template, last_version = get_template_json(str(ComponentEnum.CASE_NEW_NN_CARD.value), str(role_code), "timeline")

        timeline_type = get_timeline_type(db, ComponentEnum.CASE_NEW_NN_CARD.value, role_code, last_version)
        if timeline_type is None:
            raise ValueError("Case New Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Prepare action_by from current_user
        first_name = current_user.first_name if current_user.first_name is not None else ""
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "notified_lawyers": formatted_notified_lawyers,
            "message": "All delivered successfully",
            "customer_name": customer_name,
            "action_buttons": {}
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(f"Case New Navigator Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Case New Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case new navigator card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(f"Case New Navigator Card event: Error in handle_case_new_nn_card: {e}")
        raise


@event(EventType.CASE_AWARD_LAW_CARD)  # type: ignore
async def handle_case_award_law_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case award lawyer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "timestamp": "2021-01-01T00:00:00Z",
        "case_number": "CASE-001",
        "customer": <object>,
        "case_type": "Family Law",
        "case_id": 1,
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "timestamp",
            "case_number",
            "customer",
            "case_type",
            "case_id"
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Award Expert Card event: Payload validation failed for "
                f"{event.event_type.value}: {validation}"
            )
            raise ValueError("Case Award Expert Card event: Required keys not found in payload") # noqa: TRY301

        timestamp = payload["timestamp"]
        case_number = payload["case_number"]
        customer_name = payload["customer"].user.first_name + " " + payload["customer"].user.last_name
        case_type = payload["case_type"]
        role_code = UserRoleEnum.LAWYER.value
        user_id = event.user_id

        # Get case_id from payload if available, otherwise extract from case_number
        case_id = payload.get("case_id")

        if case_id is None:
            raise ValueError("Case Award Expert Card event: case_id not found in payload")  # noqa: TRY301

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case Award Expert Card event: Invalid case ID format") from e

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_AWARD_LAW_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_AWARD_LAW_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case Award Expert Card event: Timeline type not found")  # noqa: TRY301

        # Prepare placeholder values
        placeholder_values = {
            "action_by": "",
            "timestamp": timestamp,
            "case_number": case_number,
            "customer_name": customer_name,
            "case_type": case_type,
            "action_buttons": {},
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(f"Case Award Expert Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Case Award Expert Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db, case_id=case_id, timeline_type=timeline_type, meta_data=card_data, action_user_id=user_id
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case award expert card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(
            f"Case Award Expert Card event: Error in handle_case_award_law_card: {e}"
        )
        raise


@event(EventType.CASE_AWARDED_TO_OTHER_LAW_CARD)  # type: ignore
async def handle_case_awarded_to_other_law_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case awarded to other lawyer card event: generate the card JSON and save it to the timeline.
    Required payload:
    {
        "case_id": 1,
        "other_lawyers": [<Lawyer object>, ...],
        "case_number": "CASE-001"
        "timestamp": "2021-01-01T00:00:00Z"
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "case_number", "timestamp"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            raise ValueError(
                f"Case Awarded To Other Law Card event: Required keys not found in payload {validation}"
            )  # noqa: TRY301

        other_lawyers = payload["other_lawyers"]

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        if not other_lawyers:
            return EventResponseData(
                success=True,
                should_display=should_display,
                message="No other experts found for the case",
                data=[],
            )

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        role_code = UserRoleEnum.LAWYER.value
        current_user = event.current_user

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_AWARDED_TO_OTHER_LAW_CARD.value),
            str(role_code),
            "timeline",
        )

        timeline_type = get_timeline_type(
            db,
            ComponentEnum.CASE_AWARDED_TO_OTHER_LAW_CARD.value,
            role_code,
            last_version,
        )
        if timeline_type is None:
            raise ValueError(
                "Case Awarded To Other Expert Card event: Timeline type not found"
            )  # noqa: TRY301

        # Prepare action_by from current_user
        first_name = current_user.first_name if current_user.first_name is not None else ""
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name

        match_status_by_lawyer = get_match_status(db, case_id)

        for other_lawyer in other_lawyers:
            match_status = match_status_by_lawyer.get(other_lawyer.id, "")
            placeholder_values = {
                "action_by": action_by,
                "case_number": case_number,
                "match_status": match_status if match_status else "",
                "timestamp": timestamp,
            }
            errors: list[str] = []
            card_data = replace_placeholders(template, placeholder_values, errors)

            if errors:
                logger.error(f"Case Awarded To Other Law Card event: Template placeholder errors: {errors}")
                raise ValueError(
                    "Case Awarded To Other Expert Card event: Template processing failed: "
                    + ", ".join(errors)
                )

            notify_user_id = getattr(other_lawyer.user, "id", None)

            save_timeline_event(
                db=db,
                case_id=case_id,
                timeline_type=timeline_type,
                meta_data=card_data,
                action_user_id=current_user.id,
                notify_user_id=notify_user_id,
            )

        return EventResponseData(
            success=True,
            should_display=should_display,
            message="Case awarded to other expert card generated and saved to timeline successfully.",
            data=card_data,
        )

    except Exception as e:  # noqa: BLE001
        logger.exception(
            f"Case Awarded To Other Law Card event: Error in handle_case_awarded_to_other_law_card: {e}")
        raise


@event(EventType.CASE_AWARDED_TO_OTHER_LAW_EMAIL)  # type: ignore
async def send_case_awarded_to_other_lawyer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Notify the non-selected lawyer via email that the case has been awarded to another lawyer.

    Example payload:
    {
        "case_id": 1,
        "case_number": "CASE-001",
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "case_number"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                "Payload validation failed for %s: %s",
                event.event_type.value,
                validation,
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        other_lawyer_payload = payload["other_lawyers"]

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False
        if not other_lawyer_payload:
            return EventResponseData(
                success= True,
                should_display=should_display,
                message="No other experts found for the case",
                data=[],
            )

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        case_url = get_case_details_url(case_id)
        match_status_by_lawyer = get_match_status(db, case_id)

        other_lawyers_list = []
        if other_lawyer_payload:
            for other_lawyer in other_lawyer_payload:
                if hasattr(other_lawyer, "user") and other_lawyer.user is not None:
                    user = other_lawyer.user
                    email = getattr(user, "email", None)
                    first_name = getattr(user, "first_name", "") or ""
                    last_name = getattr(user, "last_name", "") or ""
                    full_name = f"{first_name} {last_name}".strip()
                    full_name = extract_name_parts(full_name, NameExtractionOption.FIRST)
                    match_status = match_status_by_lawyer.get(other_lawyer.id, "")
                    had_expressed_interest = match_status == MatchStatusEnum.INTERESTED
                    if had_expressed_interest:
                        subject = f"Update on case {case_number}"
                    else:
                        subject = f"Case update – {case_number}"
                    other_lawyers_list.append({
                        "lawyer_email": email,
                        "lawyer_name": full_name,
                        "subject": subject,
                        "had_expressed_interest": had_expressed_interest,
                    })

        for other_lawyer in other_lawyers_list:
            await email_service.send_email(
            to_email=other_lawyer.get("lawyer_email", None),
            subject=other_lawyer.get("subject"),
            template=email_service.EmailTemplate.CASE_AWARDED_TO_OTHER_LAW_EMAIL,
            context={
                    "case_id": case_id,
                    "case_number": case_number,
                    "lawyer_name": other_lawyer.get("lawyer_name", None),
                    "had_expressed_interest": other_lawyer.get("had_expressed_interest", False),
                    "case_url": case_url,
                },
            )

        return EventResponseData(
            success=False,
            message="Case awarded to other expert email sent successfully.",
            should_display=should_display,
            data={
                "case_id": case_id,
                "case_number": case_number,
            },
        )

    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "Error in send_case_awarded_to_other_lawyer_email: %s",
            exc,
        )
        raise


@event(EventType.CASE_NEW_LAW_CARD)  # type: ignore
async def handle_case_new_law_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case new lawyer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "case_number": "CASE-001",
        "current_user": <User object>,
        "customer_name": "John Doe",
        "partner_name": "John Doe",
        "case_summary": "Family law case involving custody dispute",
        "timestamp": "2021-01-01T00:00:00Z",
        "kyc_id": "Z0FBQUFBQm9rRHN4UU1UMVp",
        "resolve_id": "Z0FBQUFBQm9rRHN4UU1UMVp",
        "notified_lawyers": [<Lawyer object>]
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "case_number", "current_user", "timestamp", "kyc_id", "resolve_id", "notified_lawyers"]
        # , "customer_name", "partner_name", "case_summary"
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case New Expert Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case New Expert Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        current_user = payload["current_user"]
        customer_name = payload["customer_name"]
        partner_name = payload["partner_name"]
        case_summary = payload["case_summary"]
        timestamp = payload["timestamp"]
        role_code = UserRoleEnum.LAWYER.value
        kyc_id = payload["kyc_id"]
        resolve_id = payload["resolve_id"]
        notified_lawyers = payload["notified_lawyers"]

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case New Expert Card event: Invalid case ID format") from e

        template, last_version = get_template_json(str(ComponentEnum.CASE_NEW_LAW_CARD.value), str(role_code), "timeline")

        timeline_type = get_timeline_type(db, ComponentEnum.CASE_NEW_LAW_CARD.value, role_code, last_version)
        if timeline_type is None:
            raise ValueError("Case New Expert Card event: Timeline type not found")  # noqa: TRY301

        # Prepare action_by from current_user
        first_name = current_user.first_name if current_user.first_name is not None else ""
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "customer_name": customer_name,
            "partner_name": partner_name,
            "case_summary": case_summary,
            "kyc_id": kyc_id,
            "resolve_id": resolve_id,
            "action_buttons": {
                "raise_interest": True,
                "decline_match": True,
                "ask_more_details": True,
                "view_resolve": True,
                "view_kyc": True
            }
        }

        for lawyer in notified_lawyers:
            # Replace placeholders in template
            errors: list[str] = []
            card_data = replace_placeholders(template, placeholder_values, errors)

            if errors:
                logger.error(f"Case New Expert Card event: Template placeholder errors: {errors}")
                raise ValueError(f"Case New Expert Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

            # Save timeline event
            timeline_event = save_timeline_event(
                db=db,
                case_id=case_id,
                timeline_type=timeline_type,
                meta_data=card_data,
                action_user_id=current_user.id,
                notify_user_id=lawyer.user.id
            )
            related_id = f"{case_id}_{lawyer.id}"
            timeline = get_timeline_event_from_map(db, str(timeline_type.type_name), related_id, timeline_event.id)
            if not timeline:
                save_timeline_map(db, int(timeline_event.id), str(timeline_type.type_name), related_id)

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case new expert card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(f"Case New Expert Card event: Error in handle_case_new_law_card: {e}")
        raise


@event(EventType.CASE_NEW_MATCH_LAW_CARD)  # type: ignore
async def handle_case_new_match_law_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case new lawyer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "case_number": "CASE-001",
        "current_user": <User object>,
        "customer_name": "John Doe",
        "partner_name": "John Doe",
        "case_summary": "Family law case involving custody dispute",
        "case_ai_summary": "AI summary of the case",
        "timestamp": "2021-01-01T00:00:00Z",
        "kyc_id": "Z0FBQUFBQm9rRHN4UU1UMVp",
        "resolve_id": "Z0FBQUFBQm9rRHN4UU1UMVp", (optional)
        "triage_id": "Z0FBQUFBQm9rRHN4UU1UMVp", (optional)
        "notified_lawyers": [<Lawyer object>]
    }
    """
    from app.db.services.general import retrive_resolve_answers, retrive_kyc_answers, retrive_triage_answers
    from app.db.services.resolve import get_resolve_by_id
    from app.db.services.general import get_triage_by_case_id
    
    try:
        payload = event.payload
        required_keys = ["case_id", "case_number", "current_user", "timestamp", "kyc_id", "notified_lawyers"]
        # , "customer_name", "partner_name", "case_summary"
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case New Match Expert Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case New Match Expert Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        current_user = payload["current_user"]
        customer_name = payload["customer_name"]
        partner_name = payload["partner_name"]
        case_summary = payload["case_summary"]
        case_ai_summary = payload["case_ai_summary"]
        timestamp = payload["timestamp"]
        role_code = UserRoleEnum.LAWYER.value
        kyc_id = payload["kyc_id"]
        resolve_id = payload.get("resolve_id", None)
        triage_id = payload.get("triage_id", None)
        notified_lawyers = payload["notified_lawyers"]

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case New Match Expert Card event: Invalid case ID format") from e

        template, last_version = get_template_json(str(ComponentEnum.CASE_NEW_MATCH_LAW_CARD.value), str(role_code), "timeline")

        timeline_type = get_timeline_type(db, ComponentEnum.CASE_NEW_MATCH_LAW_CARD.value, role_code, last_version)
        if timeline_type is None:
            raise ValueError("Case New Match Expert Card event: Timeline type not found")  # noqa: TRY301

        # Prepare action_by from current_user
        first_name = current_user.first_name if current_user.first_name is not None else ""
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name

        customer_first_name = extract_name_parts(customer_name, NameExtractionOption.FIRST)
        partner_first_name = extract_name_parts(partner_name, NameExtractionOption.FIRST)

        resolve_title = None
        triage_asset_value = ""
        triage_customer_email = ""
        triage_customer_income = ""
        if resolve_id:
            resolve_id_decrypted = decrypt_id(resolve_id)
            resolve = get_resolve_by_id(db, int(resolve_id_decrypted))

            resolve_title = get_result_title(resolve)
            if resolve_title is None:
                raise ValueError("Case New Match Expert Card event: Resolve title not found")  # noqa: TRY301
        else:
            case = payload.get("case", None)
            if case is not None and case.is_triage is True:
                triage = get_triage_by_case_id(db, case.id)
                if triage is None:
                    raise ValueError("Case New Match Expert Card event: Triage not found")  # noqa: TRY301
                questions = ["1","4","5"]
                triage_answers = retrive_triage_answers(db, triage, questions, customer_first_name, partner_first_name)
                if len(triage_answers) > 0:
                    resolve_title = triage_answers.get("1", {}).get("answer", "") if "1" in triage_answers else ""
                    triage_customer_income = triage_answers.get("4", {}).get("answer", "") if "4" in triage_answers else ""
                    triage_customer_email = triage.customer_email if triage.customer_email is not None else ""
                    triage_asset_value = triage_answers.get("5", {}).get("answer", "") if "5" in triage_answers else ""
                else:
                    resolve_title = ""
                    triage_asset_value = ""
                    triage_customer_email = ""
                    triage_customer_income = ""
        #4: Relationship type, #6: Current court proceedings, #13: Income before tax
        #14: Features relevant to children, #19: Features relevant to relationship, #16: Relationship activities, #21: Email address, #22: Your Financial Picture(Assets)
        questions = ["4", "23", "6", "13", "14", "19", "16", "21", "22"]

        if resolve_id:
            resolve_anwers = retrive_resolve_answers(db, resolve, questions, customer_first_name, partner_first_name)
        else:
            resolve_anwers = {}

        if len(resolve_anwers) > 0:
            relationship_type = resolve_anwers.get("4", {}).get("answer", "") if "4" in resolve_anwers else ""
            relationship_type_other = resolve_anwers.get("23", {}).get("answer", "") if "23" in resolve_anwers else ""
            current_court_proceedings = resolve_anwers.get("6", {}).get("answer", "") if "6" in resolve_anwers else ""
            customer_income = resolve_anwers.get("13", {}).get("answer", "") if "13" in resolve_anwers else ""
            features_relevant_to_children = resolve_anwers.get("14", {}).get("answer", "") if "14" in resolve_anwers else ""
            features_relevant_to_relationship = resolve_anwers.get("19", {}).get("answer", "") if "19" in resolve_anwers else ""
            relationship_activities = resolve_anwers.get("16", {}).get("answer", "") if "16" in resolve_anwers else ""
            email_address = resolve_anwers.get("21", {}).get("answer", "") if "21" in resolve_anwers else ""
            asset_value = resolve_anwers.get("22", {}).get("answer", "") if "22" in resolve_anwers else ""
        else:
            relationship_type = ""
            relationship_type_other = ""
            current_court_proceedings = ""
            customer_income = ""
            features_relevant_to_children = ""
            features_relevant_to_relationship = ""
            relationship_activities = ""
            email_address = ""
            asset_value = ""
        
        if relationship_type_other != "":
            relationship_type = relationship_type_other
        else:
            relationship_type = relationship_type
        
        if asset_value !="":
            asset_value = asset_value
        else:
            asset_value = triage_asset_value

        if email_address !="":
            email_address = email_address
        else:
            email_address = triage_customer_email
        
        if customer_income !="":
            customer_income = customer_income
        else:
            customer_income = triage_customer_income

        # KYC questions: 3 (Gender), 6 (Matter type/circumstances), 10 (Preferred consultation method), 11 (Additional support), 13 (case priority)
        kyc_questions = ["3", "6", "10", "11", "13", "19"]
        kyc_answers = retrive_kyc_answers(db, case_id, kyc_questions, option_key_questions=["13"])

        # function to check list and return first element if it is a list (only questions having single values)
        get_answer = lambda d, k: (v[0] if isinstance((v := d.get(k, {}).get("answer", "")), list) else v)

        if len(kyc_answers) > 0:
            from app.db.services.kyc import get_resolve_options_for_kyc

            case_for_kyc = payload.get("case")
            if case_for_kyc is None:
                case_for_kyc = get_case_by_id(db, case_id)

            option_labels = {}
            if case_for_kyc is not None and case_for_kyc.is_triage is True:
                engage = db.query(CaseEngage).filter(CaseEngage.case_id == case_for_kyc.id).first()
                engage_id = engage.engage_id if engage else None
                options = get_resolve_options_for_kyc(db, None, engage_id)
            else:
                resolve_for_kyc = get_resolve_from_case_id(db, case_id)
                options = get_resolve_options_for_kyc(db, int(resolve_for_kyc.id), None) if resolve_for_kyc else []
            for option in options or []:
                if isinstance(option, dict):
                    option_labels.update(option)

            raw_q6 = kyc_answers.get("6", {}).get("answer", []) if "6" in kyc_answers else []
            if not isinstance(raw_q6, list):
                raw_q6 = [raw_q6] if raw_q6 else []

            matter_type_kyc = []
            for item in raw_q6:
                option_key = item.get("value") if isinstance(item, dict) else item
                if option_key is None or option_key == "":
                    continue
                option_label = option_labels.get(str(option_key)) or option_labels.get(str(option_key).lower())
                if option_label is None:
                    option_label = str(option_key)
                option_label = option_label.replace("{partner_name}", partner_first_name or "")
                option_label = option_label.replace("{customer_name}", customer_first_name or "")
                matter_type_kyc.append(option_label)

            case_priority = kyc_answers.get("13", {}).get("answer", "") if "13" in kyc_answers else ""
            preferred_consultation_method = get_answer(kyc_answers, "10")
            additional_support = get_answer(kyc_answers, "11")
            gender = get_answer(kyc_answers, "3")
            partner_income = kyc_answers.get("19", {}).get("answer", "") if "19" in kyc_answers else ""
        else:
            matter_type_kyc = []
            case_priority = []
            preferred_consultation_method = ""
            additional_support = ""
            gender = ""
            partner_income = ""

        case_matches = get_match_status(db, case_id)

        # kyc answers come back as lists, resolve answers as strings
        join_answer = lambda v: " | ".join(str(i) for i in v if i not in (None, "")) if isinstance(v, list) else str(v or "")

        income_before_tax = f"{customer_first_name or ''} - {join_answer(customer_income)}<br>{partner_first_name or ''} - {join_answer(partner_income)}"

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "case_priority": "URGENT" if case_priority else "Normal",
            "case_priority_data": case_priority,
            "resolve_id": resolve_id,
            "triage_id": encrypt_id(triage_id) if triage_id is not None and triage_id != "" else "",
            "resolve_title": resolve_title,
            "current_court_proceedings": current_court_proceedings,
            "income_before_tax": income_before_tax,
            "asset_value": asset_value,
            "features_relevant_to_children": features_relevant_to_children,
            "features_relevant_to_relationship": features_relevant_to_relationship,
            "relationship_activities": relationship_activities,
            "customer_name": customer_name,
            "customer_first_name": customer_first_name,
            "partner_name": partner_name,
            "partner_first_name": partner_first_name,
            "email_address": email_address,
            "preferred_consultation_method": preferred_consultation_method,
            "additional_support": additional_support,
            "gender": gender,
            "case_summary": case_summary if isinstance(case_summary, list) else case_summary.get("summary", []),
            "case_ai_summary": case_ai_summary,
            "kyc_id": kyc_id,
            "matter_type_kyc": matter_type_kyc,
            "relationship_type": relationship_type,
            "strategic_advice_consultation": str(settings.STRATEGIC_ADVICE_CONSULTATION),
            "action_buttons": {
                "raise_interest": True,
                "decline_match": True,
                "ask_more_details": True,
                "view_resolve": False if resolve_id is None or resolve_id == "" else True,
                "view_triage": False if triage_id is None or triage_id == "" else True,
                "view_kyc": True
            }
        }

        for lawyer in notified_lawyers:
            # Replace placeholders in template
            hourly_rate = str(int(lawyer.hourly_rate)) if lawyer.hourly_rate is not None else ""
            placeholder_values["hourly_rate"] = hourly_rate
            if lawyer.id in case_matches:
                match_status = case_matches[lawyer.id]
                placeholder_values["match_status"] = match_status
            else:
                placeholder_values["match_status"] = ""
            errors: list[str] = []
            card_data = replace_placeholders(template, placeholder_values, errors)

            if errors:
                logger.error(f"Case New Match Expert Card event: Template placeholder errors: {errors}")
                raise ValueError(f"Case New Match Expert Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

            # Save timeline event
            timeline_event = save_timeline_event(
                db=db,
                case_id=case_id,
                timeline_type=timeline_type,
                meta_data=card_data,
                action_user_id=current_user.id,
                notify_user_id=lawyer.user.id
            )
            related_id = f"{case_id}_{lawyer.id}"
            timeline = get_timeline_event_from_map(db, str(timeline_type.type_name), related_id, timeline_event.id)
            if not timeline:
                save_timeline_map(db, int(timeline_event.id), str(timeline_type.type_name), related_id)

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case new match expert card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(f"Case New Match Expert Card event: Error in handle_case_new_match_law_card: {e}")
        raise


@event(EventType.CASE_INTEREST_LAW_CARD)  # type: ignore
async def handle_case_interest_law_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case interest lawyer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "case_number": "CASE-001",
        "timestamp": "2021-01-01T00:00:00Z",
        "current_user": <User object>,
        "notify_user_id": 1
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_id", "case_number", "timestamp", "current_user", "notify_user_id"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Interest Expert Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Interest Expert Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        current_user = payload["current_user"]
        notify_user_id = payload["notify_user_id"]
        role_code = UserRoleEnum.LAWYER.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case Interest Expert Card event: Invalid case ID format") from e

        template, last_version = get_template_json(str(ComponentEnum.CASE_INTEREST_LAW_CARD.value), str(role_code), "timeline")

        timeline_type = get_timeline_type(db, ComponentEnum.CASE_INTEREST_LAW_CARD.value, role_code, last_version)
        if timeline_type is None:
            raise ValueError("Case Interest Expert Card event: Timeline type not found")  # noqa: TRY301

        # Prepare action_by from current_user
        first_name = current_user.first_name if current_user.first_name is not None else ""
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "action_buttons": {}
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(f"Case Interest Expert Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Case Interest Expert Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id,
            notify_user_id=notify_user_id
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case interest expert card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(f"Case Interest Expert Card event: Error in handle_case_interest_law_card: {e}")
        raise


@event(EventType.CASE_AWARD_NN_CARD)  # type: ignore
async def handle_case_award_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case award navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "timestamp": "2021-01-01T00:00:00Z",
        "case_number": "CASE-001",
        "customer": <object>,
        "case_type": "Family Law",
        "case_id": 1,
        "lawyer": <object>
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "timestamp",
            "case_number",
            "customer",
            "case_type",
            "case_id",
            "lawyer",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Award Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Award Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        timestamp = payload["timestamp"]
        case_number = payload["case_number"]
        customer = payload["customer"]
        case_type = payload["case_type"]
        case_id = payload["case_id"]
        lawyer = payload["lawyer"]
        role_code = UserRoleEnum.NAVIGATOR.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError(
                "Case Award Navigator Card event: Invalid case ID format"
            ) from e

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_AWARD_NN_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_AWARD_NN_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case Award Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Prepare customer name
        customer_name = ""
        if hasattr(customer, "user") and customer.user:
            first_name = customer.user.first_name if customer.user.first_name else ""
            last_name = customer.user.last_name if customer.user.last_name else ""
            customer_name = f"{first_name} {last_name}".strip()

        # Prepare lawyer name
        lawyer_name = ""
        if hasattr(lawyer, "user") and lawyer.user:
            first_name = lawyer.user.first_name if lawyer.user.first_name else ""
            last_name = lawyer.user.last_name if lawyer.user.last_name else ""
            lawyer_name = f"{first_name} {last_name}".strip()

        # Prepare placeholder values
        placeholder_values = {
            "action_by": "",
            "timestamp": timestamp,
            "case_number": case_number,
            "lawyer_name": lawyer_name,
            "customer_name": customer_name,
            "case_type": case_type,
            "action_buttons": {},
        }


        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(
                f"Case Award Navigator Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Case Award Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db, case_id=case_id, timeline_type=timeline_type, meta_data=card_data, action_user_id=event.user_id
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case award navigator card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(
            f"Case Award Navigator Card event: Error in handle_case_award_nn_card: {e}"
        )
        raise


@event(EventType.CASE_AWARD_CUS_CARD)  # type: ignore
async def handle_case_award_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case award customer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": "1",
        "case_number": "CASE-001",
        "timestamp": "2021-01-01T00:00:00Z",
        "lawyer": <object>,
        "customer": <object>
    }
    """
    from app.utils.formatters import format_expertises
    from app.utils.formatters import format_accredited_specialisms

    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "case_number",
            "timestamp",
            "lawyer",
            "customer"
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Award Customer Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Award Customer Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        lawyer = payload["lawyer"]
        role_code = UserRoleEnum.CUSTOMER.value

        customer = payload["customer"]
        customer_first_name = customer.user.first_name if customer.user.first_name is not None else ""

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case Award Customer Card event: Invalid case ID format") from e

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_AWARD_CUS_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_AWARD_CUS_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case Award Customer Card event: Timeline type not found")  # noqa: TRY301

        # Prepare lawyer information
        lawyer_name = ""
        lawyer_about = ""
        lawyer_photo_url = ""
        lawyer_experience = ""
        # lawyer_expert_type = ""
        lawyer_expertises = []
        lawyer_expert_types = []
        expertises = []
        expertises_other = {}
        lawyer_accreditations = []
        accredited_specialisms = []
        accredited_specialisms_other = []
        lawyer_rate = ""
        lawyer_location = ""
        # lawyer_specialization = ""
        lawyer_testimonial = ""

        if hasattr(lawyer, "user") and lawyer.user:
            first_name = lawyer.user.first_name if lawyer.user.first_name else ""
            last_name = lawyer.user.last_name if lawyer.user.last_name else ""
            lawyer_name = f"{first_name} {last_name}".strip()

        if hasattr(lawyer, "about") and lawyer.about:
            lawyer_about = lawyer.about

        if hasattr(lawyer, "photo_url") and lawyer.photo_url:
            lawyer_photo_url = upload_service.get_image_url(lawyer.photo_url, ImageSize.LARGE) if lawyer.photo_url is not None else ""

        lawyer_experience = str(calculate_lawyer_experience(lawyer))

        # if hasattr(lawyer, "expert_types") and lawyer.expert_types:
        #     expert_types = [et.expert_type.value for et in lawyer.expert_types]
        #     lawyer_expert_type = ", ".join(expert_types)

        if hasattr(lawyer, "expertises") and lawyer.expertises:
            expertises = lawyer.expertises
        
        if hasattr(lawyer, "expertises_other") and lawyer.expertises_other:
            expertises_other = _parse_json_field(lawyer.expertises_other, default={})
        
        if hasattr(lawyer, "expert_types") and lawyer.expert_types:
            lawyer_expert_types = [et.expert_type.value for et in lawyer.expert_types if not et.expert_type.is_other()]
        if hasattr(lawyer, "expert_types_other") and lawyer.expert_types_other:
            lawyer_expert_types.append(lawyer.expert_types_other.capitalize())
        lawyer_expert_types.sort()
        
        lawyer_expertises = format_expertises(expertises, expertises_other)

        if hasattr(lawyer, "accredited_specialisms") and lawyer.accredited_specialisms:
            accredited_specialisms = lawyer.accredited_specialisms
        
        if hasattr(lawyer, "accredited_specialism_other") and lawyer.accredited_specialism_other:
            accredited_specialisms_other = _parse_json_field(lawyer.accredited_specialism_other, default=[])
        
        lawyer_accreditations = format_accredited_specialisms(accredited_specialisms, accredited_specialisms_other)

        if hasattr(lawyer, "hourly_rate") and lawyer.hourly_rate:
            lawyer_rate = int(lawyer.hourly_rate) if lawyer.hourly_rate is not None else ""

        if hasattr(lawyer, "city") and lawyer.city:
            location_parts = []
            if lawyer.city:
                location_parts.append(lawyer.city)
            if hasattr(lawyer, "country") and lawyer.country:
                location_parts.append(lawyer.country)
            lawyer_location = ", ".join(location_parts)

        
        lawyer_specialization = None
        # if hasattr(lawyer, "accredited_specialisations") and lawyer.accredited_specialisations:
            # lawyer_specialization = lawyer.accredited_specialisations

        if hasattr(lawyer, "testimonial") and lawyer.testimonial:
            lawyer_testimonial = lawyer.testimonial

        # Prepare placeholder values
        placeholder_values = {
            "action_by": "",
            "timestamp": timestamp,
            "case_number": case_number,
            "first_name": customer_first_name,
            "lawyer_name": lawyer_name,
            "lawyer_about": lawyer_about,
            "lawyer_photo_url": lawyer_photo_url,
            "lawyer_experience": lawyer_experience,
            "lawyer_expert_types": lawyer_expert_types,
            "lawyer_expertises": lawyer_expertises,
            "lawyer_accreditations": lawyer_accreditations,
            "lawyer_rate": lawyer_rate,
            "lawyer_location": lawyer_location,
            # "lawyer_specialization": lawyer_specialization,
            "lawyer_testimonial": lawyer_testimonial,
            "action_buttons": {}
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(
                f"Case Award Customer Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Case Award Customer Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db, case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=event.user_id
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case award customer card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(
            f"Case Award Customer Card event: Error in handle_case_award_cus_card: {e}"
        )
        raise


@event(EventType.CASE_AWARD_CUS_EMAIL)  # type: ignore
async def send_case_award_customer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to customer when a lawyer is awarded their case.

    Example payload:
    {   "case_id": 1,
        "case_number": "CASE-001",
        "lawyer": <Lawyer object>,
        "customer": <User object>
        "case_type": "Family Law"
    }
    """
    from app.core.security import create_analytics_token
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "case_number",
            "lawyer",
            "customer",
            "case_type",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case_number = payload.get("case_number")
        lawyer = payload.get("lawyer")
        # engage_url = payload.get("engage_url")
        customer = payload.get("customer")

        case_type = payload.get("case_type")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)

        # Validate that required objects are not None
        if lawyer is None:
            raise ValueError("Expert not found in payload")  # noqa: TRY301
        if customer is None:
            raise ValueError("Customer not found in payload")  # noqa: TRY301

        # Extract customer email and name
        customer_email = customer.user.email
        if not customer_email:
            raise ValueError("Customer email not found in payload")  # noqa: TRY301

        customer_name = f"{customer.user.first_name}"

        # Extract lawyer information (following the same pattern as CASE_AWARD_CUS_CARD)
        lawyer_name = ""
        lawyer_first_name = ""
        lawyer_about = ""
        lawyer_photo_url = ""
        lawyer_experience = ""
        # lawyer_expert_type = ""
        lawyer_expert_types = []
        lawyer_expertises = []
        lawyer_rate = ""
        lawyer_location = ""
        # lawyer_specialization = ""
        lawyer_accreditations = []
        from app.utils.formatters import format_expertises, format_accredited_specialisms

        if hasattr(lawyer, "user") and lawyer.user:
            first_name = lawyer.user.first_name if lawyer.user.first_name else ""
            last_name = lawyer.user.last_name if lawyer.user.last_name else ""
            lawyer_first_name = first_name
            lawyer_name = f"{first_name} {last_name}".strip()

        if hasattr(lawyer, "about") and lawyer.about:
            lawyer_about = lawyer.about

        if hasattr(lawyer, "photo_url") and lawyer.photo_url:
            lawyer_photo_url = upload_service.get_image_url(lawyer.photo_url, ImageSize.MEDIUM) if lawyer.photo_url is not None else ""

        lawyer_experience = str(calculate_lawyer_experience(lawyer))

        # if hasattr(lawyer, "expert_types") and lawyer.expert_types:
        #     expert_types = [et.expert_type.value for et in lawyer.expert_types]
        #     lawyer_expert_type = ", ".join(expert_types)
        if hasattr(lawyer, "expertises") and lawyer.expertises:
            lawyer_expertises = format_expertises(lawyer.expertises, lawyer.expertises_other)
        # if hasattr(lawyer, "accredited_specialisms") and lawyer.accredited_specialisms:
        #     lawyer_accreditations = format_accredited_specialisms(lawyer.accredited_specialisms, lawyer.accredited_specialism_other)
        # Get expert types
        if hasattr(lawyer, "expert_types") and lawyer.expert_types:
            lawyer_expert_types = [et.expert_type.value for et in lawyer.expert_types if not et.expert_type.is_other()]
            if hasattr(lawyer, "expert_types_other") and lawyer.expert_types_other:
                lawyer_expert_types.append(lawyer.expert_types_other.capitalize())
        lawyer_expert_types.sort()

        if hasattr(lawyer, "hourly_rate") and lawyer.hourly_rate:
            lawyer_rate = int(lawyer.hourly_rate) if lawyer.hourly_rate is not None else ""

        if hasattr(lawyer, "city") and lawyer.city:
            location_parts = []
            if lawyer.city:
                location_parts.append(lawyer.city)
            if hasattr(lawyer, "country") and lawyer.country:
                location_parts.append(lawyer.country)
            lawyer_location = ", ".join(location_parts)

        # lawyer_specialization = None
        # if hasattr(lawyer, "accredited_specialisations") and lawyer.accredited_specialisations:
        #     lawyer_specialization = lawyer.accredited_specialisations

        # Determine who performed the action (navigator or customer)
        action_by = None
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            action_by = "Navigator"
        
        analytics_payload = {
            "case_id": case_id,
            "event_type": EventType.EMAIL_CTA_CLICKED.value,
        }
        analytics_token = create_analytics_token(analytics_payload)

        response = await email_service.send_email(
            to_email=customer_email,
            template=email_service.EmailTemplate.CASE_AWARD_CUSTOMER_NOTIFICATION,
            context={
                "case_number": case_number,
                "case_type": case_type,
                "customer_name": customer_name,
                "lawyer_name": lawyer_name,
                "lawyer_first_name": lawyer_first_name,
                "lawyer_about": lawyer_about,
                "lawyer_photo_url": lawyer_photo_url,
                "lawyer_experience": lawyer_experience,
                "lawyer_expert_types": lawyer_expert_types,
                "lawyer_expertises": lawyer_expertises,
                "lawyer_rate": lawyer_rate,
                "lawyer_location": lawyer_location,
                # "lawyer_specialization": lawyer_specialization,
                "lawyer_accreditations": lawyer_accreditations,
                # "engage_url": engage_url,
                "case_url": f"{case_url}/?analytics_token={analytics_token}",
                "header_subtitle": "Your Expert Has Been Awarded",
                "action_by": action_by if action_by else ""
            },
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case award email sent successfully to customer.",
            data={
                "case_number": case_number,
                "case_type": case_type,
                "customer_email": customer_email,
                "lawyer_name": lawyer_name,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_case_award_customer_email: {e}")
        raise


@event(EventType.CASE_INTEREST_NN_CARD)  # type: ignore
async def handle_case_interest_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case interest navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": "1",
        "case_number": "CASE-001",
        "timestamp": "2021-01-01T00:00:00Z",
        "lawyer_name": "John Doe",
        "about_lawyer": "About the lawyer"<optional>,
        "current_user": <object>
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "case_number",
            "timestamp",
            "lawyer_name",
            "current_user",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(f"Case Interest Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}")
            raise ValueError("Case Interest Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        lawyer_name = payload["lawyer_name"]
        about_lawyer = payload["about_lawyer"]
        current_user = payload["current_user"]
        role_code = UserRoleEnum.NAVIGATOR.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError(
                "Case Interest Navigator Card event: Invalid case ID format"
            ) from e

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_INTEREST_NN_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_INTEREST_NN_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case Interest Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Prepare action_by from current_user
        first_name = (
            current_user.first_name if current_user.first_name is not None else ""
        )
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "lawyer_name": lawyer_name,
            "about_lawyer": about_lawyer,
            "interest_message": "",
            "action_buttons": {"send_reviewed_profiles": True},
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(
                f"Case Interest Navigator Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Case Interest Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301
        
        # Save timeline event
        timeline_event = save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id
        )
        timeline = get_timeline_event_from_map(db, str(timeline_type.type_name), int(case_id), timeline_event.id)
        if not timeline:
            save_timeline_map(db, int(timeline_event.id), str(timeline_type.type_name), int(case_id))

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case Interest Navigator Card generated and saved to timeline successfully.",
            data=card_data,
        )

    except Exception as e:
        logger.exception(
            f"Case Interest Navigator Card event: Error in handle_case_interest_nn_card: {e}"
        )
        raise


@event(EventType.CASE_DECLINE_LAW_CARD)  # type: ignore
async def handle_case_decline_law_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case decline lawyer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "case_number": "CASE-001",
        "decline_reason": ["Conflict of interest"],
        "decline_reason_other": "Other reason details",
        "current_user": <User object>,
        "timestamp": "2021-01-01T00:00:00Z",
        "lawyer_id": 1,<optional>
        "notify_user_id": 1
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "case_number",
            "decline_reason",
            "current_user",
            "timestamp",
            "notify_user_id",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Decline Expert Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Decline Expert Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        decline_reason = payload["decline_reason"]
        reason_other = payload["decline_reason_other"]
        current_user = payload["current_user"]
        timestamp = payload["timestamp"]
        notify_user_id = payload["notify_user_id"]
        lawyer_id = payload["lawyer_id"]
        role_code = UserRoleEnum.LAWYER.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError(
                "Case Decline Expert Card event: Invalid case ID format"
            ) from e

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_DECLINE_LAW_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_DECLINE_LAW_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case Decline Expert Card event: Timeline type not found")  # noqa: TRY301

        # Prepare action_by from current_user
        first_name = (
            current_user.first_name if current_user.first_name is not None else ""
        )
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name


        action_user_role = UserRoleEnum.from_id(current_user.user_roles[0].role_id).display_name
        if action_user_role  != UserRoleEnum.LAWYER.display_name:
            action_by = action_by + " (" + action_user_role + ")"

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "reasons": decline_reason,
            "reason_other": reason_other,
            "action_buttons": {"raise_interest": True},
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(
                f"Case Decline Expert Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Case Decline Expert Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        timeline_event = save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id,
            notify_user_id=notify_user_id,
        )

        related_id = f"{case_id}_{lawyer_id}"
        timeline = get_timeline_event_from_map(db, str(timeline_type.type_name), related_id, timeline_event.id)
        if not timeline:
            save_timeline_map(db, int(timeline_event.id), str(timeline_type.type_name), related_id)
        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case decline Expert card generated and saved to timeline successfully.",
            data=card_data,
        )

    except Exception as e:
        logger.exception(
            f"Case Decline Expert Card event: Error in handle_case_decline_law_card: {e}"
        )
        raise


@event(EventType.ENGAGE_SUBMIT)  # type: ignore
async def handle_engage_submit(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle engage submit event.
    Required payload:
    {
        "request_data": {
            "case_id": 1
        },
        "current_user": <User object>,
    }
    """
    try:
        payload = event.payload
        required_keys = [{"request_data": ["case_id"]}, "current_user"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        request_data = payload.get("request_data")

        if request_data is None:
            raise ValueError("Request data not found in payload")  # noqa: TRY301

        case_id = request_data.case_id

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Invalid case ID format") from e

        # Fetch case
        case = get_case_by_id(db, case_id)
        if case is None:
            raise ValueError("Case not found")  # noqa: TRY301

        if not case.is_initial_payment_completed:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Initial payment not completed",
                },
            )

        if case.is_onboarding_completed:
            raise HTTPException(
                status_code=http_status.HTTP_409_CONFLICT,
                detail={
                    "success": False,
                    "message": "Case already onboarded",
                },
            )

        # Format case number
        case_number = format_case_number(case.case_no)

        # Fetch customer user
        customer_user = get_case_customer_user(db, case_id)
        if customer_user is None:
            raise ValueError("Customer not found")  # noqa: TRY301
        customer_first_name = customer_user.first_name if customer_user.first_name is not None else ""

        # Fetch case lawyer
        case_lawyer = get_case_lawyer_by_case_id(db, case_id)
        if case_lawyer is None:
            raise ValueError("Expert not found")  # noqa: TRY301

        # Fetch lawyer
        lawyer = case_lawyer.lawyer

        message = "Customer onboarding process completed successfully."
        current_user = event.current_user
        if current_user and current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            current_lawyer_id = int(current_user.lawyer.id)
            assigned_lawyer_id = int(lawyer.id)
            if current_lawyer_id != assigned_lawyer_id:
                raise HTTPException(
                    status_code=http_status.HTTP_403_FORBIDDEN,
                    detail={"success": False, "message": "Access denied: You are not assigned to this case"},
                )
            message = f"{customer_first_name} - Engage complete. Case - {case_number}"
        elif current_user and current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            message = f"Nova Engage completed for {customer_first_name}. Case - {case_number}"

        # Update case is_onboarding_completed flag
        case.is_onboarding_completed = True
        db.commit()

        # Amount requested
        amount_requested = 0

        # Status
        status = "Completed"

        # timestamp
        timestamp = datetime.now(timezone.utc).isoformat()

        payload["case"] = case
        payload["customer_user"] = customer_user
        payload["case_number"] = case_number
        payload["timestamp"] = timestamp
        payload["lawyer"] = lawyer
        payload["status"] = status
        payload["amount_requested"] = amount_requested
        payload["customer_first_name"] = customer_first_name

        #disable make_payment button in ONBOARDING_ASSESSMENT_COMPLETED_CUS_CARD timeline event
        # NOTE :
        # all three enum values are "complete_onboarding_assessment", so the dictionary collapses to one key. for that case, we have renamed the key start_onboarding_assessment to mark_onboarding_completed. So here We dont need to call each enum value separately.
        disable_timeline_action_buttons(
            db=db,
            component_buttons={
                str(ComponentEnum.COMPLETE_ONBOARD_ASSESSMENT_NN_CARD.value): ["mark_onboarding_completed"],
            },
            related_id=int(case_id),
        )

        return EventResponseData(
            success=True,
            message=message,
            data={},
        )
    except Exception as e:
        logger.exception(
            f"Engage Submit event: Error in handle_engage_submit: {e}"
        )
        raise


@event(EventType.CASE_ENGAGE_LAW_EMAIL)  # type: ignore
async def send_case_engage_lawyer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to the lawyer when client onboarding is completed.
    Example payload:
    {
        "case": <Case object>,
        "customer_user": <User object>,
        "lawyer": <Lawyer object>,
        "status": "Ready for Payment with $2,500"
        "is_customer": Boolean, (default: False)
        "case_number": "CASE-100",
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case",
            "case_number",
            "customer_user",
            "lawyer",
            "status",
            "case_number",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case = payload.get("case")
        customer_user = payload.get("customer_user")
        lawyer = payload.get("lawyer")
        status = payload.get("status")
        case_number = payload.get("case_number")
        is_customer = payload.get("is_customer", False)
        # Validate that required objects are not None
        if case is None:
            raise ValueError("Case not found in payload")  # noqa: TRY301
        if customer_user is None:
            raise ValueError("Customer user not found in payload")  # noqa: TRY301
        if lawyer is None:
            raise ValueError("Expert not found in payload")  # noqa: TRY301

        case_url = get_case_details_url(case.id)
        # Extract required fields from objects
        customer_name = f"{customer_user.first_name} {customer_user.last_name}"
        case_type = case.case_type.value
        lawyer_email = lawyer.user.email
        lawyer_name = f"{lawyer.user.first_name} {lawyer.user.last_name}"
        lawyer_name = extract_name_parts(lawyer_name, NameExtractionOption.FIRST)

        if not lawyer_email:
            raise ValueError("Expert email not found in payload")  # noqa: TRY301

        action_by_name = None
        action_by_role = None
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            action_by_role = UserRoleEnum.LAWYER
            action_by_name = f"{event.current_user.first_name} {event.current_user.last_name}"
        elif event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            action_by_role = UserRoleEnum.NAVIGATOR

        response = await email_service.send_email(
            to_email=lawyer_email,
            template=email_service.EmailTemplate.CASE_ENGAGE_LAWYER_NOTIFICATION,
            context={
                "case_number": case_number,
                "customer_name": customer_name,
                "case_type": case_type,
                "status": status,
                "lawyer_name": lawyer_name,
                "case_url":case_url,
                "header_subtitle": "Client Onboarding Completed",
                "action_by_role": action_by_role.display_name if action_by_role is not None else '',
                "action_by_name": action_by_name if action_by_name is not None else '',
                "is_customer": is_customer,
            },
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Client onboarding completion email sent successfully to expert.",
            data={
                "case_number": case_number,
                "customer_name": customer_name,
                "lawyer_name": lawyer_name,
                "lawyer_email": lawyer_email,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_case_engage_lawyer_email: {e}")
        raise


@event(EventType.CASE_ENGAGE_NN_EMAIL)  # type: ignore
async def send_case_engage_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to Nova navigator when client onboarding is completed.
    Example payload:
    {
        "case": <Case object>,
        "customer_user": <User object>,
        "lawyer": <Lawyer object>,
        "status": "Ready for Payment with $2,500"
        "case_number": "CASE-100",
        "is_customer": Boolean, (default: False)
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case",
            "customer_user",
            "lawyer",
            "status",
            "case_number",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case = payload.get("case")
        customer_user = payload.get("customer_user")
        lawyer = payload.get("lawyer")
        status = payload.get("status")
        case_number = payload.get("case_number")
        is_customer = payload.get("is_customer", False)
        # Validate that required objects are not None
        if case is None:
            raise ValueError("Case object not found in payload")  # noqa: TRY301
        if customer_user is None:
            raise ValueError("Customer user object not found in payload")  # noqa: TRY301
        if lawyer is None:
            raise ValueError("Expert object not found in payload")  # noqa: TRY301

        case_url = get_case_details_url(case.id)

        # Extract required fields from objects
        customer_name = f"{customer_user.first_name} {customer_user.last_name}"
        case_type = case.case_type.value
        lawyer_name = f"{lawyer.user.first_name} {lawyer.user.last_name}"
        navigators = get_all_navigator_emails(db)

        if not navigators:
            logger.warning("No navigators found in payload")
            return EventResponseData(
                success=False,
                message="No navigators found in payload",
                data=[],
            )

        action_by_name = None
        action_by_role = None
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            action_by_role = UserRoleEnum.LAWYER
            action_by_name = f"{event.current_user.first_name} {event.current_user.last_name}"
        elif event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            action_by_role = UserRoleEnum.NAVIGATOR
            action_by_name = f"{event.current_user.first_name} {event.current_user.last_name}"

        response_list = []
        # Prepare list of navigator emails
        navigator_emails = [str(navigator.get("navigator_email")) for navigator in navigators if navigator.get("navigator_email") is not None]

        if navigator_emails:
            response = await email_service.send_email(
                bcc=navigator_emails,
                template=email_service.EmailTemplate.CASE_ENGAGE_NAVIGATOR_NOTIFICATION,
                context={
                    "navigator_name": "Navigator",
                    "case_number": case_number,
                    "customer_name": customer_name,
                    "case_type": case_type,
                    "lawyer_name": lawyer_name,
                    "status": status,
                    "case_url": case_url,
                    "header_subtitle": "Client Onboarding Completed",
                    "action_by_role": action_by_role.display_name if action_by_role is not None else '',
                    "action_by_name": action_by_name if action_by_name is not None else '',
                    "is_customer": is_customer,
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
            message="Client onboarding completion email sent successfully to navigators",
            data=response_list,
        )

    except Exception as e:
        logger.exception(f"Error in send_case_engage_navigator_email: {e}")
        raise


@event(EventType.CASE_ENGAGE_CUS_EMAIL)  # type: ignore
async def send_case_engage_customer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to the customer when client onboarding is completed.

    Example payload:
    {
        "case": <Case object>,
        "customer_user": <User object>,
        "lawyer": <Lawyer object>,
        "amount_requested": "2,500"
        "case_number": "CASE-100",
        "is_customer": Boolean, (default: False)
    }
    """
    from app.core.security import create_analytics_token
    try:
        payload = event.payload
        required_keys = [
            "case",
            "customer_user",
            "lawyer",
            "amount_requested",
            "case_number",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case = payload.get("case")
        customer_user = payload.get("customer_user")
        lawyer = payload.get("lawyer")
        amount_requested = payload.get("amount_requested")
        case_number = payload.get("case_number")
        is_customer = payload.get("is_customer", False)
        # Validate that required objects are not None
        if case is None:
            raise ValueError("Case not found in payload")  # noqa: TRY301
        if customer_user is None:
            raise ValueError("Customer user not found in payload")  # noqa: TRY301
        if lawyer is None:
            raise ValueError("Expert not found in payload")  # noqa: TRY301

        # Extract required fields from objects
        customer_name = f"{customer_user.first_name}"
        case_type = case.case_type.value
        lawyer_name = f"{lawyer.user.first_name} {lawyer.user.last_name}"
        # Extract customer email
        customer_email = customer_user.email
        if not customer_email:
            raise ValueError("Customer email not found in payload")  # noqa: TRY301

        action_by_name = None
        action_by_role = None
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            action_by_role = UserRoleEnum.LAWYER
            action_by_name = f"{event.current_user.first_name} {event.current_user.last_name}"
        elif event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            action_by_role = UserRoleEnum.NAVIGATOR
        
        case_url = get_case_details_url(case.id)

        analytics_payload = {
            "case_id": case.id,
            "event_type": EventType.EMAIL_CTA_CLICKED.value,
        }
        analytics_token = create_analytics_token(analytics_payload)

        response = await email_service.send_email(
            to_email=customer_email,
            template=email_service.EmailTemplate.CASE_ENGAGE_CUSTOMER_NOTIFICATION,
            context={
                "case_number": case_number,
                "case_type": case_type,
                "lawyer_name": lawyer_name,
                "amount_requested": amount_requested,
                "customer_name": customer_name,
                "header_subtitle": "Onboarding Assessment Completed",
                "case_url": f"{case_url}/?analytics_token={analytics_token}",
                "action_by_role": action_by_role.display_name if action_by_role is not None else '',
                "action_by_name": action_by_name if action_by_name is not None else '',
                "is_customer": is_customer,
            },
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Client onboarding completion email sent successfully to customer.",
            data={
                "case_number": case_number,
                "customer_email": customer_email,
                "lawyer_name": lawyer_name,
                "amount_requested": amount_requested,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_case_engage_customer_email: {e}")
        raise


@event(EventType.CASE_ENGAGE_LAW_CARD)  # type: ignore
async def handle_case_engage_law_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case engage lawyer card event: Generate card JSON using template and save to timeline_event table.
    A timeline card notifying the lawyer when client onboarding is completed.
    Required payload:
    {
        "case": <object>,
        "case_number": "CASE-001",
        "status": "Completed",
        "timestamp": "2021-01-01T00:00:00Z",
        "current_user": <User object>,
        "customer_user": <object>
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case",
            "timestamp",
            "case_number",
            "status",
            "current_user",
            "customer_user",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Engage Expert Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Engage Expert Card event: Required keys not found in payload")  # noqa: TRY301

        case = payload["case"]
        timestamp = payload["timestamp"]
        case_number = payload["case_number"]
        status = payload["status"]
        current_user = payload["current_user"]
        customer_user = payload["customer_user"]
        case_id = case.id
        case_type = case.case_type
        customer_name = customer_user.first_name + " " + customer_user.last_name
        role_code = UserRoleEnum.LAWYER.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError(
                "Case Engage Expert Card event: Invalid case ID format"
            ) from e

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_ENGAGE_LAW_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_ENGAGE_LAW_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case Engage Expert Card event: Timeline type not found")  # noqa: TRY301

        # Prepare placeholder values
        placeholder_values = {
            "action_by": "",
            "timestamp": timestamp,
            "case_number": case_number,
            "customer_name": customer_name,
            "case_type": case_type,
            "status": status,
            "action_buttons": {},
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(
                f"Case Engage Expert Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Case Engage Expert Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id,
        )
        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Expert timeline is updated with engage completion details.",
            data=card_data,
        )

    except Exception as e:
        logger.exception(
            f"Case Engage Expert Card event: Error in handle_case_engage_law_card: {e}"
        )
        raise


@event(EventType.CASE_ENGAGE_NN_CARD)  # type: ignore
async def handle_case_engage_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case engage navigator card event: Generate card JSON using template and save to timeline_event table.
    A timeline card notifying the navigators when client onboarding is completed.
    Required payload:
    {
        "case": <object>,
        "timestamp": "2021-01-01T00:00:00Z",
        "case_number": "CASE-001",
        "lawyer": <object>,
        "status": "Completed",
        "current_user": <User object>,
        "customer_user": <object>
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case",
            "timestamp",
            "case_number",
            "lawyer",
            "status",
            "current_user",
            "customer_user",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Engage Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Engage Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        case = payload["case"]
        timestamp = payload["timestamp"]
        case_number = payload["case_number"]
        lawyer = payload["lawyer"]
        status = payload["status"]
        current_user = payload["current_user"]
        customer = payload["customer_user"]
        case_id = case.id
        case_type = case.case_type
        lawyer_name = lawyer.user.first_name + " " + lawyer.user.last_name
        customer_name = customer.first_name + " " + customer.last_name
        role_code = UserRoleEnum.NAVIGATOR.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError(
                "Case Engage Navigator Card event: Invalid case ID format"
            ) from e

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_ENGAGE_NN_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_ENGAGE_NN_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case Engage Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Prepare placeholder values
        placeholder_values = {
            "action_by": "",
            "timestamp": timestamp,
            "case_number": case_number,
            "lawyer_name": lawyer_name,
            "customer_name": customer_name,
            "case_type": case_type,
            "status": status,
            "action_buttons": {},
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(
                f"Case Engage Navigator Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Case Engage Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id,
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Navigator timeline is updated with engage completion details.",
            data=card_data,
        )

    except Exception as e:
        logger.exception(
            f"Case Engage Navigator Card event: Error in handle_case_engage_nn_card: {e}"
        )
        raise


@event(EventType.CASE_ENGAGE_CUS_CARD)  # type: ignore
async def handle_case_engage_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case engage customer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case": <Case object>,
        "timestamp": "2021-01-01T00:00:00Z",
        "case_number": "CASE-001",
        "lawyer": <Lawyer object>,
        "amount_requested": "2500",
        "customer_first_name": "John",
        "current_user": <User object>
    }
    """
    try:
        payload = event.payload
        required_keys = ["case", "timestamp", "case_number", "lawyer", "amount_requested", "current_user", "customer_first_name"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Engage Customer Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Engage Customer Card event: Required keys not found in payload")  # noqa: TRY301

        case = payload["case"]
        timestamp = payload["timestamp"]
        case_number = payload["case_number"]
        lawyer = payload["lawyer"]
        amount_requested = payload["amount_requested"]
        current_user = payload["current_user"]
        customer_first_name = payload["customer_first_name"]
        role_code = UserRoleEnum.CUSTOMER.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case.id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case Engage Customer Card event: Invalid case ID format") from e

        template, last_version = get_template_json(str(ComponentEnum.CASE_ENGAGE_CUS_CARD.value), str(role_code), "timeline")

        timeline_type = get_timeline_type(db, ComponentEnum.CASE_ENGAGE_CUS_CARD.value, role_code, last_version)
        if timeline_type is None:
            raise ValueError("Case Engage Customer Card event: Timeline type not found")  # noqa: TRY301

        # Prepare lawyer name
        lawyer_name = ""
        if hasattr(lawyer, "user") and lawyer.user:
            first_name = lawyer.user.first_name if lawyer.user.first_name else ""
            last_name = lawyer.user.last_name if lawyer.user.last_name else ""
            lawyer_name = f"{first_name} {last_name}".strip()

        # Prepare placeholder values
        placeholder_values = {
            "action_by": "",
            "timestamp": timestamp,
            "case_number": case_number,
            "case_type": case.case_type.value if hasattr(case, 'case_type') else "",
            "lawyer_name": lawyer_name,
            "customer_first_name": customer_first_name,
            "action_buttons": {}
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(f"Case Engage Customer Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Case Engage Customer Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id,
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False
        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Customer timeline is updated with engage completion details.",
            data=card_data
        )

    except Exception as e:
        logger.exception(f"Case Engage Customer Card event: Error in handle_case_engage_cus_card: {e}")
        raise

@event(EventType.CASE_RECEIPT_CUS_EMAIL)  # type: ignore
async def send_case_receipt_customer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send payment receipt email to the customer after successful payment.

    Example payload:
    {
        "case": <Case object>,
        "lawyer": <Lawyer object>,
        "current_user": <User object>,
        "payment": <Payment object>,
        "case_number": <Case number>,
    }
    """
    from app.db.services.simple_auth_token import create_simple_auth_token
    from app.core.security import create_password_token
    from app.utils.constants import ENGAGE_VERIFY_TOKEN_URL_PREFIX
    from app.core.security import create_analytics_token
    try:
        payload = event.payload
        required_keys = [
            "case",
            "lawyer",
            "current_user",
            "payment",
            "case_number",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301


        case = payload.get("case")
        lawyer = payload.get("lawyer")
        current_user = payload.get("current_user")
        payment = payload.get("payment")
        case_number = payload.get("case_number")

        # Validate that required objects are not None
        if case is None:
            raise ValueError("Case not found in payload")  # noqa: TRY301
        if lawyer is None:
            raise ValueError("Expert not found in payload")  # noqa: TRY301
        if current_user is None:
            raise ValueError("User not found in payload")  # noqa: TRY301
        if payment is None:
            raise ValueError("Payment data not found in payload")  # noqa: TRY301

        case_url = get_case_details_url(case.id)
        
        simple_auth_token_expire_minutes = settings.SIMPLE_AUTH_TOKEN_EXPIRE_MINUTES

        simple_auth_token_record = create_simple_auth_token(
            db=db,
            user_id=int(current_user.id),
            token=None,
        )

        token_payload = {
            "sub": (encrypt_id(str(current_user.id))),
            "case_id": encrypt_id(str(case.id)),
            "simple_auth_token_id": encrypt_id(str(simple_auth_token_record.id)),
        }
        engage_token = create_password_token(
            data=token_payload,
            token_type="engage_token",
            expire_minutes=simple_auth_token_expire_minutes,
        )
        engage_token_url = f"{settings.FRONTEND_URL}{ENGAGE_VERIFY_TOKEN_URL_PREFIX}/{engage_token}"

        simple_auth_token_record.token = engage_token
        db.commit()
        # Extract required fields from objects
        customer_name = f"{current_user.first_name}"
        lawyer_name = f"{lawyer.user.first_name} {lawyer.user.last_name}"
        customer_email = current_user.email
        if not customer_email:
            raise ValueError("Customer email not found in payload")  # noqa: TRY301


        # Extract payment details
        transaction_id = payment.transaction_id
        payment_date = payment.payment_date
        payment_method = payment.payment_method
        amount_paid = payment.amount_paid

        analytics_payload = {
            "case_id": case.id,
            "event_type": EventType.EMAIL_CTA_CLICKED.value,
        }
        analytics_token = create_analytics_token(analytics_payload)


        response = await email_service.send_email(
            to_email=customer_email,
            template=email_service.EmailTemplate.CASE_RECEIPT_CUSTOMER_NOTIFICATION,
            context={
                "case_number": case_number,
                "lawyer_name": lawyer_name,
                "transaction_id": transaction_id,
                "payment_date": payment_date,
                "payment_method": payment_method,
                "amount_paid": amount_paid,
                "customer_name": customer_name,
                "case_url": f"{case_url}/?analytics_token={analytics_token}",
                "engage_token_url": engage_token_url,
            },
        )


        return EventResponseData(
            success=True,
            message="Payment receipt email sent successfully to customer.",
            data={
                "case_number": case_number,
                "customer_email": customer_email,
                "lawyer_name": lawyer_name,
                "transaction_id": transaction_id,
                "amount_paid": amount_paid,
                "message_id": response.message_id,
            },
        )


    except Exception as e:
        logger.exception(f"Error in send_case_receipt_customer_email: {e}")
        raise


@event(EventType.CASE_RECEIPT_NN_EMAIL)  # type: ignore
async def send_case_receipt_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send payment receipt email to Nova navigator when customer payment is completed.

    Example payload:
    {
        "case": <Case object>,
        "lawyer": <Lawyer object>,
        "current_user": <User object>,
        "payment": <Payment object>
        "case_number": <Case number>,
        "status": "Payment Completed"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case",
            "lawyer",
            "current_user",
            "payment",
            "case_number",
            "status",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301


        case = payload.get("case")
        lawyer = payload.get("lawyer")
        current_user = payload.get("current_user")
        payment = payload.get("payment")
        status = payload.get("status")
        case_number = payload.get("case_number")
        # Validate that required objects are not None
        if case is None:
            raise ValueError("Case not found in payload")  # noqa: TRY301
        if lawyer is None:
            raise ValueError("Expert not found in payload")  # noqa: TRY301
        if current_user is None:
            raise ValueError("User not found in payload")  # noqa: TRY301
        if payment is None:
            raise ValueError("Payment data not found in payload")  # noqa: TRY301

        case_url = get_case_details_url(case.id)
        # Extract required fields from objects
        customer_name = f"{current_user.first_name} {current_user.last_name}"
        case_type = ""
        if hasattr(case, 'case_type'):
            case_type = case.case_type.value if hasattr(case.case_type, 'value') else ""
        lawyer_name = f"{lawyer.user.first_name} {lawyer.user.last_name}"
        # Extract payment details
        transaction_id = payment.transaction_id
        amount_paid = payment.amount_paid
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
                template=email_service.EmailTemplate.CASE_RECEIPT_NAVIGATOR_NOTIFICATION,
                context={
                    "case_number": case_number,
                    "lawyer_name": lawyer_name,
                    "customer_name": customer_name,
                    "case_type": case_type,
                    "amount_paid": amount_paid,
                    "transaction_id": transaction_id,
                    "status": status,
                    "navigator_name": "Navigator",
                    "header_subtitle": "Payment Receipt",
                    "case_url": case_url,
                },
            )


            response_list.append({
                "navigator_email": navigator_emails,
                "navigator_name": "Navigator",
                "message_id": response.message_id,
            })


        return EventResponseData(
            success=True,
            message="Payment receipt email sent successfully to navigators.",
            data=response_list,
        )


    except Exception as e:
        logger.exception(f"Error in send_case_receipt_navigator_email: {e}")
        raise




@event(EventType.CASE_RECEIPT_LAW_EMAIL)  # type: ignore
async def send_case_receipt_lawyer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send payment receipt email to the lawyer when customer payment is completed.

    Example payload:
    {
        "case": <Case object>,
        "lawyer": <Lawyer object>,
        "current_user": <User object>,
        "payment": <Payment object>,
        "status": "Payment Completed",
        "case_number": "CASE-100"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case",
            "lawyer",
            "current_user",
            "payment",
            "status",
            "case_number",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301


        case = payload.get("case")
        lawyer = payload.get("lawyer")
        current_user = payload.get("current_user")
        payment = payload.get("payment")
        status = payload.get("status")
        case_number = payload.get("case_number")


        # Validate that required objects are not None
        if case is None:
            raise ValueError("Case not found in payload")  # noqa: TRY301
        if lawyer is None:
            raise ValueError("Expert not found in payload")  # noqa: TRY301
        if current_user is None:
            raise ValueError("User not found in payload")  # noqa: TRY301
        if payment is None:
            raise ValueError("Payment data not found in payload")  # noqa: TRY301

        case_url = get_case_details_url(case.id)
        # Extract required fields from objects
        customer_name = f"{current_user.first_name} {current_user.last_name}"
        case_type = ""
        if hasattr(case, 'case_type'):
            case_type = case.case_type.value if hasattr(case.case_type, 'value') else ""
        lawyer_name = f"{lawyer.user.first_name} {lawyer.user.last_name}"
        lawyer_name = extract_name_parts(lawyer_name, NameExtractionOption.FIRST)
        lawyer_email = lawyer.user.email


        if not lawyer_email:
            raise ValueError("Expert email not found in payload")  # noqa: TRY301


        # Extract payment details
        transaction_id = payment.transaction_id
        amount_paid = payment.amount_paid


        response = await email_service.send_email(
            to_email=lawyer_email,
            template=email_service.EmailTemplate.CASE_RECEIPT_LAWYER_NOTIFICATION,
            context={
                "case_number": case_number,
                "customer_name": customer_name,
                "case_type": case_type,
                "amount_paid": amount_paid,
                "transaction_id": transaction_id,
                "status": status,
                "lawyer_name": lawyer_name,
                "header_subtitle": "Payment Received",
                "case_url": case_url,
            },
        )


        return EventResponseData(
            success=True,
            message="Payment receipt email sent successfully to expert.",
            data={
                "case_number": case_number,
                "customer_name": customer_name,
                "lawyer_name": lawyer_name,
                "lawyer_email": lawyer_email,
                "amount_paid": amount_paid,
                "transaction_id": transaction_id,
                "message_id": response.message_id,
            },
        )


    except Exception as e:
        logger.exception(f"Error in send_case_receipt_lawyer_email: {e}")
        raise


@event(EventType.CASE_RECEIPT_CUS_CARD)  # type: ignore
async def handle_case_receipt_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case receipt customer card event: Generate card JSON using template and save to timeline_event table.
    A timeline event notifying the customer of the payment receipt once the initial deposit has been made.
    Required payload:
    {
        "payment_event": <PaymentEvent object>,
        "timestamp": "2021-01-01T00:00:00Z",
        "case_number": "CASE-001",
        "lawyer": <Lawyer object>,
        "payment": <Payment object>,
        "current_user": <User object>,
        "case": <Case object>,
        "invoice": <Invoice object>
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "payment_event",
            "timestamp",
            "case_number",
            "lawyer",
            "payment",
            "current_user",
            "case",
            "invoice"
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Receipt Customer Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Receipt Customer Card event: Required keys not found in payload")  # noqa: TRY301

        timestamp = payload["timestamp"]
        payment_event = payload["payment_event"]
        case_number = payload["case_number"]
        lawyer = payload["lawyer"]
        payment = payload["payment"]
        case = payload["case"]
        current_user = payload["current_user"]
        # status = payload["status"]
        invoice = payload["invoice"]
        role_code = UserRoleEnum.CUSTOMER.value

        invoice_id_encrypted = encrypt_id(str(invoice.id))
        if invoice_id_encrypted is None:
            raise ValueError("Case Receipt Customer Card event: Failed to encrypt invoice ID")  # noqa: TRY301

        # Extract case_id from case object
        case_id = getattr(case, "id", None)
        if case_id is None:
            raise ValueError("Case Receipt Customer Card event: case_id not found in case")  # noqa: TRY301

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError(
                "Case Receipt Customer Card event: Invalid case ID format"
            ) from e

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_RECEIPT_CUS_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_RECEIPT_CUS_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case Receipt Customer Card event: Timeline type not found")  # noqa: TRY301

        # Prepare lawyer name
        lawyer_name = ""
        if hasattr(lawyer, "user") and lawyer.user:
            first_name = lawyer.user.first_name if lawyer.user.first_name else ""
            last_name = lawyer.user.last_name if lawyer.user.last_name else ""
            lawyer_name = f"{first_name} {last_name}".strip()

        # Prepare customer name
        customer_name = ""
        first_name = current_user.first_name if current_user.first_name else ""
        last_name = current_user.last_name if current_user.last_name else ""
        customer_name = f"{first_name} {last_name}".strip()

        # Prepare payment details
        payment_date = datetime.now(timezone.utc).date().isoformat()
        amount_paid = payment_event.get("amount", None)
        if amount_paid is None:
            raise ValueError("Payment amount not found in webhook event")

        amount_paid = amount_paid / 100

        transaction_id = payment_event.get("id", "") if payment_event.get("id") else None
        reason = None
        payment_type = payment_event.get("payment_method_details", {}).get("type", "") if payment_event.get("payment_method_details") else None
        payment_intent_id = payment_event.get("payment_intent", "") if payment_event.get("payment_intent") else None

        # Prepare placeholder values
        placeholder_values = {
            "action_by": customer_name,
            "timestamp": timestamp,
            "case_number": case_number,
            "lawyer_name": lawyer_name,
            "transaction_id": transaction_id,
            "payment_date": payment_date,
            "payment_method": payment_type,
            "amount_paid": amount_paid,
            "invoice_id": invoice_id_encrypted,
            "payment_status": InvoiceStatusEnum.COMPLETED.value,
            "action_buttons": "",
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(
                f"Case Receipt Customer Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Case Receipt Customer Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301
        
        transaction = Transaction(
            payment_id=payment.id,
            transaction_id=transaction_id,
            reason=reason,
            status=PaymentStatusEnum.COMPLETED.value,
        )
        db.add(transaction)

        payment.status = PaymentStatusEnum.COMPLETED.value
        payment.payment_date = payment_date
        payment.amount_paid = amount_paid
        payment.transaction_id = transaction_id
        payment.payment_method = payment_type
        payment.payment_intent_id = payment_intent_id
        payment.remarks = reason

        case.is_initial_payment_completed = True
        invoice.status = InvoiceStatusEnum.COMPLETED.value

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id,
        )

        disable_timeline_action_buttons(db, {str(ComponentEnum.CUSTOMER_PMT_REQUESTED_CUS_CARD.value): ["make_payment"]}, int(payment.id))

        return EventResponseData(
            success=True,
            message="Case receipt customer card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(f"Case Receipt Customer Card event: Error in handle_case_receipt_cus_card: {e}")
        raise


@event(EventType.CASE_RECEIPT_NN_CARD)  # type: ignore
async def handle_case_receipt_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case receipt navigator card event: Generate card JSON using template and save to timeline_event table.
    A timeline event notifying the navigator of the payment receipt once the initial deposit has been made.
    Required payload:
    {
        "timestamp": "2021-01-01T00:00:00Z",
        "case_number": "CASE-001",
        "lawyer": <Lawyer object>,
        "payment": <Payment object>,
        "current_user": <User object>,
        "case": <Case object>,
        "status": "Completed"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "timestamp",
            "case_number",
            "lawyer",
            "payment",
            "case",
            "current_user",
            "status",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Receipt Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Receipt Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        timestamp = payload["timestamp"]
        case_number = payload["case_number"]
        lawyer = payload["lawyer"]
        payment = payload["payment"]
        current_user = payload["current_user"]
        case = payload["case"]
        status = payload["status"]
        role_code = UserRoleEnum.NAVIGATOR.value

        # Extract case_id from payment or other source
        case_id = getattr(case, "id", None)
        if case_id is None:
            raise ValueError("Case Receipt Navigator Card event: case_id not found in case")  # noqa: TRY301

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError(
                "Case Receipt Navigator Card event: Invalid case ID format"
            ) from e

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_RECEIPT_NN_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_RECEIPT_NN_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case Receipt Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Prepare lawyer name
        lawyer_name = ""
        if hasattr(lawyer, "user") and lawyer.user:
            first_name = lawyer.user.first_name if lawyer.user.first_name else ""
            last_name = lawyer.user.last_name if lawyer.user.last_name else ""
            lawyer_name = f"{first_name} {last_name}".strip()

        # Prepare customer name
        customer_name = ""
        first_name = current_user.first_name if current_user.first_name else ""
        last_name = current_user.last_name if current_user.last_name else ""
        customer_name = f"{first_name} {last_name}".strip()

        # Prepare case type
        case_type = ""
        if hasattr(case, 'case_type'):
            case_type = case.case_type.value if hasattr(case.case_type, 'value') else ""

        # Prepare payment details
        transaction_id = payment.transaction_id if hasattr(payment, "transaction_id") else ""
        amount_paid = payment.amount_paid if hasattr(payment, "amount_paid") else ""

        # Prepare placeholder values
        placeholder_values = {
            "action_by": "",
            "timestamp": timestamp,
            "case_number": case_number,
            "lawyer_name": lawyer_name,
            "customer_name": customer_name,
            "case_type": case_type,
            "amount_paid": amount_paid,
            "transaction_id": transaction_id,
            "status": status,
            "action_buttons": {}
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(
                f"Case Receipt Navigator Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Case Receipt Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id,
        )

        return EventResponseData(
            success=True,
            message="Case receipt navigator card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(
            f"Case Receipt Navigator Card event: Error in handle_case_receipt_nn_card: {e}"
        )
        raise


@event(EventType.CASE_MORE_DETAILS_NN_EMAIL)  # type: ignore
async def send_case_more_details_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send case more details notification email to Nova navigator when case is awarded.

    Example payload:
    {
        "case": <Case object>,
        "lawyer": <Lawyer object>,
        "case_number": "CASE-001",
        "lawyer_request": "Additional case details requested",
        "customer": <Customer object>,
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case",
            "lawyer",
            "case_number",
            "lawyer_request",
            "customer",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case = payload.get("case")
        lawyer = payload.get("lawyer")
        case_number = payload.get("case_number")
        lawyer_request = payload.get("lawyer_request")
        customer = payload.get("customer")
        # Validate that required objects are not None
        if case is None:
            raise ValueError("Case not found in payload")  # noqa: TRY301
        if lawyer is None:
            raise ValueError("Expert not found in payload")  # noqa: TRY301
        if customer is None:
            raise ValueError("Customer not found in payload")  # noqa: TRY301
        case_url = get_case_details_url(case.id)

        # Prepare lawyer name
        lawyer_name = f"{lawyer.user.first_name} {lawyer.user.last_name}"
        lawyer_email = lawyer.user.email

        # Prepare customer name and email from customer object
        customer_name = f"{customer.first_name} {customer.last_name}"
        customer_email = customer.email

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
            response = await email_service.send_email(
                bcc=navigator_emails,
                template=email_service.EmailTemplate.CASE_MORE_DETAILS_NAVIGATOR_NOTIFICATION,
                context={
                    "case_number": case_number,
                    "lawyer_name": lawyer_name,
                    "lawyer_email": lawyer_email,
                    "lawyer_request": lawyer_request,
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "navigator_name": "Navigator",
                    "case_url": case_url,
                    "header_subtitle": "Case More Details Request",
                    "is_navigator_action": is_navigator_action,
                    "action_by": navigator_name,
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
            message="Case more details notification email sent successfully to navigators.",
            data=response_list,
        )

    except Exception as e:
        logger.exception(f"Error in send_case_more_details_navigator_email: {e}")
        raise


@event(EventType.EXPERT_NOT_INTERESTED_NN_CARD)  # type: ignore
async def handle_expert_not_interested_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Generate and save EXPERT_NOT_INTERESTED_NN_CARD timeline card for navigators.

    Payload (same as EXPERT_NOT_INTERESTED_NN_EMAIL):
    {
        "cases": [
            {
                "lawyers": [<lawyer object>],
                "case": <case object>
            }
        ]
        "lawyer_interest_deadline_hours": 24,
        "timestamp": "2021-01-01T00:00:00Z",
        "cases_found": False,
    }
    Metadata: lawyer_names (list), customer_name, case_number, timestamp.
    """
    try:
        payload = event.payload
        cases_found = payload.get("cases_found", False)
        if not cases_found:
            return EventResponseData(
                success=True,
                message="No cases found",
                data=[],
            )
        required_keys = ["cases", "lawyer_interest_deadline_hours", "timestamp"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Expert Not Interested Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Expert Not Interested Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        cases_payload = payload.get("cases")
        lawyer_interest_deadline_hours = payload.get("lawyer_interest_deadline_hours")
        timestamp = payload.get("timestamp")
        role_code = UserRoleEnum.NAVIGATOR.value
        template, last_version = get_template_json(
            str(ComponentEnum.EXPERT_NOT_INTERESTED_NN_CARD.value), str(role_code), "timeline"
        )
        timeline_type = get_timeline_type(
            db, ComponentEnum.EXPERT_NOT_INTERESTED_NN_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Expert Not Interested Navigator Card event: Timeline type not found")  # noqa: TRY301

        response_list = []
        for case in cases_payload:
            case_obj = case.get("case")
            lawyers = case.get("lawyers")
            case_id = getattr(case_obj, "id", None)

            # Build lawyer_names list (metadata)
            lawyer_names = []
            expert_names = "Expert"
            expert_names_list = []
            for lawyer in lawyers:
                name = "Nova Expert"
                photo_url = None
                if lawyer is not None:
                    name = lawyer.get("name")
                    photo_url = lawyer.get("photo_url")
                lawyer_names.append({
                    "name": name,
                    "photo_url": photo_url,
                })
                if name not in expert_names_list:
                    expert_names_list.append(name)

            if expert_names_list:
                    expert_names = ", ".join(expert_names_list)
            has_have = "has" if not expert_names_list or (expert_names_list and len(expert_names_list) == 1) else "have"
            # Customer name from case.case_customers[0].customer.user
            customer_name = "Customer"
            if getattr(case_obj, "case_customers", None):
                cc = case_obj.case_customers
                if cc and len(cc) > 0 and getattr(cc[0], "customer", None) and getattr(cc[0].customer, "user", None):
                    u = cc[0].customer.user
                    first = getattr(u, "first_name", None) or ""
                    last = getattr(u, "last_name", None) or ""
                    customer_name = f"{first} {last}"

            case_number = getattr(case_obj, "case_no", None) or ""
            case_number = format_case_number(case_number)

            placeholder_values = {
                "action_by": "",
                "deadline_hours": lawyer_interest_deadline_hours,
                "lawyer_names": lawyer_names,
                "expert_names": expert_names,
                "has_have": has_have,
                "customer_name": customer_name,
                "case_number": case_number,
                "timestamp": timestamp,
                "action_buttons": {},
            }

            errors: list[str] = []
            card_data = replace_placeholders(template, placeholder_values, errors)

            if errors:
                logger.error(
                    f"Expert Not Interested Navigator Card event: Template placeholder errors: {errors}"
                )
                raise ValueError(
                    f"Expert Not Interested Navigator Card event: Template processing failed: {', '.join(errors)}"
                )  # noqa: TRY301

            save_timeline_event(
                db=db,
                case_id=int(case_id),
                timeline_type=timeline_type,
                meta_data=card_data,
            )
            response_list.append({
                "case_id": case_id,
                "lawyer_names": lawyer_names,
                "customer_name": customer_name,
            })

        return EventResponseData(
            should_display=False,
            success=True,
            message="Expert not interested navigator card(s) generated and saved to timeline successfully.",
            data=response_list,
        )

    except Exception as e:
        logger.exception(f"Expert Not Interested Navigator Card event: Error in handle_expert_not_interested_nn_card: {e}")
        raise


@event(EventType.EXPERT_NOT_INTERESTED_NN_EMAIL)  # type: ignore
async def send_expert_not_interested_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send expert-not-interested notification email to all navigators.

    Payload:
    {
        "cases": [
            {
                "lawyers": [{"id": <encrypted lawyer_id>, "name": <lawyer_name>, "photo_url": <lawyer_photo_url | None>}],
                "case": <case object>
            }
        ]
        "lawyer_interest_deadline_hours": 24,
        "cases_found": False,
    }
    Lawyer = legal expert. Customer from case.case_customers[0].customer.user.
    """
    try:
        payload = event.payload
        cases_found = payload.get("cases_found", False)
        if not cases_found:
            return EventResponseData(
                success=True,
                message="No cases found",
                data=[],
            )
        required_keys = ["cases", "lawyer_interest_deadline_hours"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        cases_payload = payload.get("cases")
        lawyer_interest_deadline_hours = payload.get("lawyer_interest_deadline_hours")
        if not isinstance(cases_payload, list) or len(cases_payload) == 0:
            logger.warning("No cases in payload for expert_not_interested_nn_email")
            return EventResponseData(
                success=True,
                message="No cases in payload; no emails sent.",
                data=[],
            )

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
        for item in cases_payload:
            if not isinstance(item, dict):
                continue
            case_obj = item.get("case")
            lawyers = item.get("lawyers")
            if case_obj is None:
                continue
            case_id = getattr(case_obj, "id", None)
            if case_id is None:
                continue

            if not isinstance(lawyers, list):
                lawyers = []

            # Customer from case.case_customers[0].customer.user (same for all lawyers in this case)
            customer_name = "Customer"
            if case_obj.case_customers:
                customer_user = case_obj.case_customers[0].customer.user
                if customer_user:
                    first = customer_user.first_name or ""
                    last = customer_user.last_name or ""
                    customer_name = f"{first} {last}".strip() or "Customer"

            case_url = get_case_details_url(case_id)
            case_number = case_obj.case_no
            case_number = format_case_number(case_number)
            navigator_emails = [str(navigator.get("navigator_email")) for navigator in navigators if navigator.get("navigator_email") is not None]

            # Send one email per lawyer (each lawyer = legal expert) to all navigators
            for lawyer in lawyers:
                expert_name = "Nova Expert"
                photo_url = None
                if lawyer is not None:
                    expert_name = lawyer.get("name")
                    photo_url = lawyer.get("photo_url")

                response = await email_service.send_email(
                    bcc=navigator_emails,
                    template=email_service.EmailTemplate.EXPERT_NOT_INTERESTED_NAVIGATOR_NOTIFICATION,
                    context={
                        "navigator_name": "Navigator",
                        "expert_name": expert_name,
                        "case_number": case_number,
                        "lawyer_interest_deadline_hours": lawyer_interest_deadline_hours,
                        "customer_name": customer_name,
                        "case_url": case_url,
                        "header_subtitle": "Nova Expert Not Interested",
                    },
                )
                response_list.append({
                    "navigator_emails": navigator_emails,
                    "case_id": case_id,
                    "expert_name": expert_name,
                    "message_id": response.message_id,
                })

        return EventResponseData(
            should_display=False,
            success=True,
            message="Expert not interested navigator notification email(s) sent successfully.",
            data=response_list,
        )

    except Exception as e:
        logger.exception(f"Error in send_expert_not_interested_navigator_email: {e}")
        raise


@event(EventType.CASE_MORE_DETAILS_LAW_EMAIL)  # type: ignore
async def send_case_more_details_lawyer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send case more details notification email to lawyer when they request additional information.

    Example payload:
    {
        "case": <Case object>,
        "lawyer": <Lawyer object>,
        "case_number": "CASE-001",
        "lawyer_request": "Additional case details requested"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case",
            "lawyer",
            "case_number",
            "lawyer_request",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case = payload.get("case")
        lawyer = payload.get("lawyer")
        case_number = payload.get("case_number")
        lawyer_request = payload.get("lawyer_request")

        # Validate that required objects are not None
        if case is None:
            raise ValueError("Case not found in payload")  # noqa: TRY301
        if lawyer is None:
            raise ValueError("Expert not found in payload")  # noqa: TRY301
        case_url = get_case_details_url(case.id)

        # Extract lawyer email
        lawyer_email = lawyer.user.email
        if not lawyer_email:
            raise ValueError("Expert email not found")  # noqa: TRY301

        # Prepare lawyer name
        if lawyer.user.first_name is None or lawyer.user.last_name is None:
            raise ValueError("Expert first name or last name not found")  # noqa: TRY301
        if lawyer.user.last_name is None:
            raise ValueError("Expert last name not found")  # noqa: TRY301
        lawyer_name = f"{lawyer.user.first_name} {lawyer.user.last_name}"
        lawyer_name = extract_name_parts(lawyer_name, NameExtractionOption.FIRST)

        # Check if the action is performed by a navigator on behalf of the lawyer
        is_navigator_action = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            is_navigator_action = True

        response = await email_service.send_email(
            to_email=lawyer_email,
            template=email_service.EmailTemplate.CASE_MORE_DETAILS_LAWYER_NOTIFICATION,
            context={
                "case_number": case_number,
                "lawyer_name": lawyer_name,
                "lawyer_request": lawyer_request,
                "case_url": case_url,
                "header_subtitle": "Case More Details Request",
                "is_navigator_action": is_navigator_action,
            },
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False

        return EventResponseData(
            should_display = should_display,
            success=True,
            message="Case more details notification email sent successfully to expert.",
            data={
                "case_number": case_number,
                "lawyer_name": lawyer_name,
                "lawyer_email": lawyer_email,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_case_more_details_lawyer_email: {e}")
        raise


@event(EventType.CUSTOMER_TALK_TO_NN_CUS_EMAIL)  # type: ignore
async def send_customer_talk_to_nn_customer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to customer when a Navigator schedules a discussion with them.

    Example payload:
    {
        "case_id": 1,
        "case_number": "CASE-001",
        "customer_user": <User object>
    }
    """
    from app.core.security import create_analytics_token
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "case_number",
            "customer_user",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case_number = payload.get("case_number")
        customer_user = payload.get("customer_user")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)
        # Validate that required objects are not None
        if customer_user is None:
            raise ValueError("Customer user not found in payload")  # noqa: TRY301

        # Extract customer email and name
        customer_email = customer_user.email
        if not customer_email:
            raise ValueError("Customer email not found")  # noqa: TRY301

        customer_name = f"{customer_user.first_name}"

        # Check if the action is performed by a navigator on behalf of the customer
        is_navigator_action = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            is_navigator_action = True

        analytics_payload = {
            "case_id": case_id,
            "event_type": EventType.EMAIL_CTA_CLICKED.value,
        }
        analytics_token = create_analytics_token(analytics_payload)

        response = await email_service.send_email(
            to_email=customer_email,
            template=email_service.EmailTemplate.CUSTOMER_TALK_TO_NN_CUSTOMER_NOTIFICATION,
            context={
                "case_number": case_number,
                "customer_name": customer_name,
                "case_url": f"{case_url}/?analytics_token={analytics_token}",
                "header_subtitle": "Discussion Scheduled",
                "is_navigator_action": is_navigator_action,
            },
        )

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Customer discussion notification email sent successfully.",
            data={
                "case_number": case_number,
                "customer_name": customer_name,
                "customer_email": customer_email,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_customer_talk_to_nn_customer_email: {e}")
        raise


@event(EventType.CUSTOMER_TALK_TO_NN_NN_EMAIL)  # type: ignore
async def send_customer_talk_to_nn_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to Nova navigator when customer requests to talk to navigator.

    Example payload:
    {
        "case_id": 1,
        "case_number": "CASE-001",
        "customer_name": "John Doe",
        "customer_email": "customer@example.com",
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "case_number",
            "customer_name",
            "customer_email",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case_number = payload.get("case_number")
        customer_name = payload.get("customer_name")
        customer_email = payload.get("customer_email")
        case_id = payload.get("case_id")
        case_url = get_case_details_url(case_id)
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
            # Check if the action is performed by a navigator on behalf of the customer
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
                template=email_service.EmailTemplate.CUSTOMER_TALK_TO_NN_NAVIGATOR_NOTIFICATION,
                context={
                    "case_number": case_number,
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "case_url": case_url,
                    "navigator_name": "Navigator",
                    "header_subtitle": "Customer Discussion Request",
                    "is_navigator_action": is_navigator_action,
                    "action_by": navigator_name,
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
            message="Customer discussion request notification email sent successfully to navigators.",
            data=response_list,
        )

    except Exception as e:
        logger.exception(f"Error in send_customer_talk_to_nn_navigator_email: {e}")
        raise


@event(EventType.CUSTOMER_TALK_TO_LAW_CUS_EMAIL)  # type: ignore
async def send_customer_talk_to_law_customer_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to customer when they request to talk to lawyer.

    Example payload:
    {
        "case": <Case object>,
        "case_number": "CASE-001",
        "customer_user": <User object>,
        "lawyer": <Lawyer object>
    }
    """
    from app.core.security import create_analytics_token
    try:
        payload = event.payload
        required_keys = [
            "case",
            "case_number",
            "customer_user",
            "lawyer",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case_number = payload.get("case_number")
        customer_user = payload.get("customer_user")
        lawyer = payload.get("lawyer")
        case = payload.get("case")
        # Validate that required objects are not None
        if customer_user is None:
            raise ValueError("Current user not found in payload")  # noqa: TRY301
        if lawyer is None:
            raise ValueError("Expert not found in payload")  # noqa: TRY301

        # Extract customer email and name
        customer_email = customer_user.email
        if not customer_email:
            raise ValueError("Customer email not found in payload")  # noqa: TRY301

        customer_name = f"{customer_user.first_name}"

        # Extract lawyer name from lawyer object
        lawyer_name = f"{lawyer.user.first_name} {lawyer.user.last_name}"

        case_url = get_case_details_url(case.id)

        # Check if the action is performed by a navigator on behalf of the customer
        is_navigator_action = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.NAVIGATOR.id:
            is_navigator_action = True
        
        analytics_payload = {
            "case_id": case.id,
            "event_type": EventType.EMAIL_CTA_CLICKED.value,
        }
        analytics_token = create_analytics_token(analytics_payload)

        response = await email_service.send_email(
            to_email=customer_email,
            template=email_service.EmailTemplate.CUSTOMER_TALK_TO_LAW_CUSTOMER_NOTIFICATION,
            context={
                "case_number": case_number,
                "lawyer_name": lawyer_name,
                "customer_name": customer_name,
                "case_url": f"{case_url}/?analytics_token={analytics_token}",
                "header_subtitle": "Talk to Expert Requested",
                "is_navigator_action": is_navigator_action,
            },
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Customer talk to expert request confirmation email sent successfully.",
            data={
                "case_number": case_number,
                "customer_email": customer_email,
                "lawyer_name": lawyer_name,
                "message_id": response.message_id,
            },
        )

    except Exception as e:
        logger.exception(f"Error in send_customer_talk_to_law_customer_email: {e}")
        raise


@event(EventType.CUSTOMER_TALK_TO_LAW_NN_EMAIL)  # type: ignore
async def send_customer_talk_to_law_navigator_email(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Send email notification to Nova navigator when customer requests to talk to lawyer.

    Example payload:
    {
        "case": <Case object>,
        "case_number": "CASE-001",
        "lawyer": <Lawyer object>,
        "customer_name": "John Doe",
        "customer_email": "customer@example.com"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case",
            "case_number",
            "lawyer",
            "customer_name",
            "customer_email",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore[arg-type]
        if not validation["status"]:
            logger.error(
                f"Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Required keys not found in payload")  # noqa: TRY301

        case_number = payload.get("case_number")
        lawyer = payload.get("lawyer")
        customer_name = payload.get("customer_name")
        customer_email = payload.get("customer_email")
        case = payload.get("case")
        # Validate that required objects are not None
        if lawyer is None:
            raise ValueError("Expert not found in payload")  # noqa: TRY301

        # Extract lawyer name and email from lawyer object
        lawyer_name = f"{lawyer.user.first_name} {lawyer.user.last_name}"
        lawyer_email = lawyer.user.email

        case_url = get_case_details_url(case.id)

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
            # Check if the action is performed by a navigator on behalf of the customer
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
                template=email_service.EmailTemplate.CUSTOMER_TALK_TO_LAW_NAVIGATOR_NOTIFICATION,
                context={
                    "case_number": case_number,
                    "lawyer_name": lawyer_name,
                    "lawyer_email": lawyer_email,
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "case_url": case_url,
                    "navigator_name": "Navigator",
                    "header_subtitle": "Customer Discussion Request to Expert",
                    "is_navigator_action": is_navigator_action,
                    "action_by": navigator_name,
                },
            )

            response_list.append({
                "navigator_email": navigator_emails,
                "navigator_name": "Navigator",
                "message_id": response.message_id,
            })

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Customer talk to expert request notification email sent successfully to navigators.",
            data=response_list,
        )

    except Exception as e:
        logger.exception(f"Error in send_customer_talk_to_law_navigator_email: {e}")
        raise


@event(EventType.CASE_RECEIPT_LAW_CARD)  # type: ignore
async def handle_case_receipt_law_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case receipt lawyer card event: Generate card JSON using template and save to timeline_event table.
    A timeline event notifying the lawyer of the payment receipt once the initial deposit has been made.
    Required payload:
    {
        "timestamp": "2021-01-01T00:00:00Z",
        "case_number": "CASE-001",
        "payment": <object>,
        "current_user": <User object>,
        "case": <object>,
        "status": "Completed"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "timestamp",
            "case_number",
            "payment",
            "current_user",
            "case",
            "status"
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Receipt Expert Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Receipt Expert Card event: Required keys not found in payload")  # noqa: TRY301

        timestamp = payload["timestamp"]
        case_number = payload["case_number"]
        payment = payload["payment"]
        current_user = payload["current_user"]
        case = payload["case"]
        status = payload["status"]
        role_code = UserRoleEnum.LAWYER.value

        # Extract case_id from case object
        case_id = case.id if hasattr(case, 'id') else None
        if case_id is None:
            raise ValueError("Case Receipt Expert Card event: case_id not found in case object")  # noqa: TRY301

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case Receipt Expert Card event: Invalid case ID format") from e

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_RECEIPT_LAW_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_RECEIPT_LAW_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case Receipt Expert Card event: Timeline type not found")  # noqa: TRY301

        # Prepare customer name
        customer_name = ""
        first_name = current_user.first_name if current_user.first_name else ""
        last_name = current_user.last_name if current_user.last_name else ""
        customer_name = f"{first_name} {last_name}".strip()

        # Prepare case type
        case_type = ""
        if hasattr(case, "case_type"):
            case_type = case.case_type.value if hasattr(case.case_type, 'value') else ""

        # Extract payment details
        amount_paid = ""
        transaction_id = ""
        if payment:
            amount_paid = getattr(payment, 'amount', '') or getattr(payment, 'amount_paid', '') or ""
            transaction_id = getattr(payment, 'transaction_id', '') or getattr(payment, 'id', '') or ""

        # Prepare placeholder values
        placeholder_values = {
            "action_by": "",
            "timestamp": timestamp,
            "case_number": case_number,
            "customer_name": customer_name,
            "case_type": case_type,
            "amount_paid": amount_paid,
            "transaction_id": transaction_id,
            "status": status,
            "action_buttons": {}
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(f"Case Receipt Expert Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Case Receipt Expert Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id,
        )

        return EventResponseData(
            success=True,
            message="Case receipt expert card generated and saved to timeline successfully.",
            data=card_data
        )

    except Exception as e:
        logger.exception(f"Case Receipt Expert Card event: Error in handle_case_receipt_expert_card: {e}")
        raise


@event(EventType.CASE_MORE_DETAILS_NN_CARD)  # type: ignore
async def handle_case_more_details_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case more details navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_number": "CASE-001",
        "current_user": <User object>,
        "lawyer": <Lawyer object>,
        "customer": <Customer object>,
        "lawyer_request": <Object>,
        "timestamp": "2021-01-01T00:00:00Z",
        "case": <Case object>,
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_number",
            "current_user",
            "lawyer",
            "customer",
            "lawyer_request",
            "timestamp",
            "case",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case More Details Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case More Details Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        case_number = payload["case_number"]
        current_user = payload["current_user"]
        lawyer = payload["lawyer"]
        customer = payload["customer"]
        lawyer_request = payload["lawyer_request"]
        timestamp = payload["timestamp"]
        case = payload["case"]
        role_code = UserRoleEnum.NAVIGATOR.value

        # Extract case_id from case object
        case_id = case.id if hasattr(case, 'id') else None
        if case_id is None:
            raise ValueError("Case More Details Navigator Card event: case_id not found in case object")  # noqa: TRY301

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError(
                "Case More Details Navigator Card event: Invalid case ID format"
            ) from e

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_MORE_DETAILS_NN_CARD.value),
            str(role_code),
            "timeline",
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_MORE_DETAILS_NN_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case More Details Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Prepare action_by from current_user
        first_name = (
            current_user.first_name if current_user.first_name is not None else ""
        )
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name

        # Prepare lawyer profile with name, emai, photo_url
        lawyer_first_name = lawyer.user.first_name if lawyer.user.first_name is not None else ""
        lawyer_last_name = lawyer.user.last_name if lawyer.user.last_name is not None else ""
        lawyer_name = lawyer_first_name + " " + lawyer_last_name
        lawyer_email = lawyer.user.email if lawyer.user.email is not None else ""
        lawyer_photo_url = upload_service.get_image_url(lawyer.photo_url, ImageSize.THUMBNAIL) if lawyer.photo_url is not None else ""

        # Prepare customer with name, email
        customer_first_name = (
            customer.first_name if customer.first_name is not None else ""
        )
        customer_last_name = (
            customer.last_name if customer.last_name is not None else ""
        )
        customer_name = customer_first_name + " " + customer_last_name
        customer_email = customer.email if customer.email is not None else ""

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "lawyer_name": lawyer_name,
            "lawyer_email": lawyer_email,
            "lawyer_photo_url": lawyer_photo_url,
            "lawyer_request": lawyer_request,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "action_buttons": {},
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(
                f"Case More Details Navigator Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Case More Details Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id,
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case more details navigator card generated and saved to timeline successfully.",
            data=card_data,
        )

    except Exception as e:
        logger.exception(
            f"Case More Details Navigator Card event: Error in handle_case_more_details_nn_card: {e}"
        )
        raise


@event(EventType.CASE_MORE_DETAILS_LAW_CARD)  # type: ignore
async def handle_case_more_details_law_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case more details lawyer card event: Generate card JSON using template and save to timeline_event table.
    A timeline event notifies the lawyer when more case details are requested.
    Required payload:
    {
        "case_number": "CASE-001",
        "timestamp": "2021-01-01T00:00:00Z",
        "current_user": <User object>,
        "case": <object>,
        "lawyer_request": "Additional information needed",
        "lawyer": <Lawyer object>,
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_number",
            "timestamp",
            "current_user",
            "case",
            "lawyer_request",
            "lawyer",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case More Details Expert Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError(f"Case More Details Expert Card event: Payload validation failed: {validation['message']}")  # noqa: TRY301

        # Extract payload values
        case = payload["case"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        current_user = payload["current_user"]
        lawyer_request = payload["lawyer_request"]
        lawyer = payload["lawyer"]
        role_code = UserRoleEnum.LAWYER.value

        # Extract case_id from case object
        case_id = case.id if hasattr(case, 'id') else None
        if case_id is None:
            raise ValueError("Case More Details Expert Card event: case_id not found in case object")  # noqa: TRY301

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case More Details Expert Card event: Invalid case ID format") from e

        # Get template and timeline type
        template, last_version = get_template_json(
            str(ComponentEnum.CASE_MORE_DETAILS_LAW_CARD.value),
            str(role_code),
            "timeline",
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_MORE_DETAILS_LAW_CARD.value, role_code, last_version
        )

        if timeline_type is None:
            raise ValueError("Case More Details Expert Card event: Timeline type not found")  # noqa: TRY301

        # Prepare action_by from current_user
        first_name = current_user.first_name if current_user.first_name is not None else ""
        last_name = current_user.last_name if current_user.last_name is not None else ""
        action_by = first_name + " " + last_name

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "lawyer_request": lawyer_request,
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(
                f"Case More Details Expert Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Case More Details Expert Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Disable decline button immediately if match is already declined for this lawyer
        match_status_by_lawyer = get_match_status(db, case_id)
        if match_status_by_lawyer.get(lawyer.id) == MatchStatusEnum.DECLINED.value:
            action_buttons = card_data.get("action_buttons")
            if isinstance(action_buttons, dict):
                action_buttons["decline_match"] = False

        # Save timeline event
        timeline_event = save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=current_user.id,
            notify_user_id=lawyer.user.id,
        )
        related_id = f"{case_id}_{lawyer.id}"
        timeline = get_timeline_event_from_map(db, str(timeline_type.type_name), related_id, timeline_event.id)
        if not timeline:
            save_timeline_map(db, int(timeline_event.id), str(timeline_type.type_name), related_id)

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.LAWYER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Case more details expert card generated and saved to timeline successfully.",
            data=card_data,
        )

    except Exception as e:
        logger.exception(
            f"Case More Details Expert Card event: Error in handle_case_more_details_law_card: {e}"
        )
        raise


@event(EventType.CUSTOMER_TALK_TO_NN_CUS_CARD)  # type: ignore
async def handle_customer_talk_to_nn_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer talk to navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_number": "CASE-001",
        "timestamp": "2021-01-01T00:00:00Z",
        "case": <Case object>
    }
    """
    try:
        payload = event.payload
        required_keys = ["case_number", "timestamp", "case"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Customer Talk to Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Customer Talk to Navigator Card event: Required keys not found in payload")  # noqa: TRY301


        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        role_code = UserRoleEnum.CUSTOMER.value

        # Get timeline type and template
        template, last_version = get_template_json(
            str(ComponentEnum.CUSTOMER_TALK_TO_NN_CUS_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CUSTOMER_TALK_TO_NN_CUS_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Customer Talk to Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Get action_by from current_user
        first_name = event.current_user.first_name if event.current_user.first_name is not None else ""
        last_name = event.current_user.last_name if event.current_user.last_name is not None else ""
        action_by = f"{first_name} {last_name}".strip()

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)
        if errors:
            logger.error(
                f"Customer Talk to Navigator Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Customer Talk to Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Get case_id from payload - check if case object is provided
        case_id = None
        if "case" in payload and hasattr(payload["case"], "id"):
            case_id = payload["case"].id
        else:
            raise ValueError("Customer Talk to Navigator Card event: case_id not found in payload")  # noqa: TRY301

        # Save timeline event
        timeline_event = save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=event.current_user.id,
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
            message="Customer talk to navigator customer card generated and saved to timeline successfully.",
            data=card_data,
        )

    except Exception as e:
        logger.exception(
            f"Customer Talk to Navigator Card event: Error in handle_customer_talk_to_nn_cus_card: {e}"
        )
        raise


@event(EventType.CUSTOMER_TALK_TO_LAW_CUS_CARD)  # type: ignore
async def handle_customer_talk_to_law_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer talk to lawyer customer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "lawyer": <Lawyer object>,
        "case": <Case object>,
        "case_number": "CASE-001",
        "timestamp": "2021-01-01T00:00:00Z"
    }
    """
    try:
        payload = event.payload
        required_keys = ["lawyer", "case", "case_number", "timestamp"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Customer Talk to Expert Customer Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Customer Talk to Expert Customer Card event: Required keys not found in payload")  # noqa: TRY301

        lawyer = payload["lawyer"]
        case = payload["case"]
        case_number = payload["case_number"]
        timestamp = payload["timestamp"]
        role_code = UserRoleEnum.CUSTOMER.value

        # Extract case_id from case object
        case_id = case.id if hasattr(case, "id") else None
        if case_id is None:
            raise ValueError("Customer Talk to Expert Customer Card event: case_id not found in case object")  # noqa: TRY301

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Customer Talk to Expert Customer Card event: Invalid case ID format") from e

        template, last_version = get_template_json(
            str(ComponentEnum.CUSTOMER_TALK_TO_LAW_CUS_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CUSTOMER_TALK_TO_LAW_CUS_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Customer Talk to Expert Customer Card event: Timeline type not found")  # noqa: TRY301

        # Get action_by from current_user
        first_name = event.current_user.first_name if event.current_user.first_name is not None else ""
        last_name = event.current_user.last_name if event.current_user.last_name is not None else ""
        action_by = f"{first_name} {last_name}".strip()

        # Get lawyer_name from lawyer object
        lawyer_name = ""
        if hasattr(lawyer, "user") and lawyer.user:
            lawyer_first_name = lawyer.user.first_name if lawyer.user.first_name else ""
            lawyer_last_name = lawyer.user.last_name if lawyer.user.last_name else ""
            lawyer_name = f"{lawyer_first_name} {lawyer_last_name}".strip()

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "lawyer_name": lawyer_name,
            "action_buttons": {"choose_another_lawyer": True},
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)
        if errors:
            logger.error(
                f"Customer Talk to Expert Customer Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Customer Talk to Expert Customer Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        timeline_event = save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=event.current_user.id,
        )

        timeline = get_timeline_event_from_map(db, str(timeline_type.type_name), int(case_id), timeline_event.id)
        if not timeline:
            save_timeline_map(db, int(timeline_event.id), str(timeline_type.type_name), int(case_id))

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Customer Talk to Expert Customer Card generated and saved to timeline successfully.",
            data=card_data,
        )

    except Exception as e:
        logger.exception(
            f"Customer Talk to Expert Customer Card event: Error in handle_customer_talk_to_law_cus_card: {e}"
        )
        raise


@event(EventType.CUSTOMER_TALK_TO_NN_NN_CARD)  # type: ignore
async def handle_customer_talk_to_nn_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer talk to navigator navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_number": "CASE-001",
        "customer_email": "customer@example.com",
        "customer_name": "John Doe",
        "timestamp": "2021-01-01T00:00:00Z",
        "case": <Case object>,
        "customer_phone": "1234567890"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_number",
            "customer_email",
            "customer_name",
            "timestamp",
            "case",
            "customer_phone",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Customer Talk to Navigator Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Customer Talk to Navigator Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        case_number = payload["case_number"]
        customer_email = payload["customer_email"]
        customer_name = payload["customer_name"]
        timestamp = payload["timestamp"]
        case = payload["case"]
        customer_phone = payload["customer_phone"]
        role_code = UserRoleEnum.NAVIGATOR.value

        # Extract case_id from case object
        case_id = case.id if hasattr(case, "id") else None
        if case_id is None:
            raise ValueError("Customer Talk to Navigator Navigator Card event: case_id not found in case object")  # noqa: TRY301

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Customer Talk to Navigator Navigator Card event: Invalid case ID format") from e

        template, last_version = get_template_json(
            str(ComponentEnum.CUSTOMER_TALK_TO_NN_NN_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CUSTOMER_TALK_TO_NN_NN_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Customer Talk to Navigator Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Prepare action_by from current_user
        first_name = event.current_user.first_name if event.current_user.first_name is not None else ""
        last_name = event.current_user.last_name if event.current_user.last_name is not None else ""
        action_by = f"{first_name} {last_name}".strip()

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "action_buttons": {},
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)
        if errors:
            logger.error(
                f"Customer Talk to Navigator Navigator Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Customer Talk to Navigator Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=event.current_user.id,
        )

        should_display = True
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Customer talk to navigator navigator card generated and saved to timeline successfully.",
            data=card_data,
        )

    except Exception as e:
        logger.exception(
            f"Customer Talk to Navigator Navigator Card event: Error in handle_customer_talk_to_nn_nn_card: {e}"
        )
        raise


@event(EventType.CUSTOMER_TALK_TO_LAW_NN_CARD)  # type: ignore
async def handle_customer_talk_to_law_nn_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle customer talk to lawyer navigator card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "lawyer": <Lawyer object>,
        "case": <Case object>,
        "case_number": "CASE-001",
        "customer_name": "John Doe",
        "customer_email": "customer@example.com",
        "timestamp": "2021-01-01T00:00:00Z",
        "customer_phone": "1234567890"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "lawyer",
            "case",
            "case_number",
            "customer_name",
            "customer_email",
            "timestamp",
            "customer_phone",
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Customer Talk to Expert Navigator Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Customer Talk to Expert Navigator Card event: Required keys not found in payload")  # noqa: TRY301

        lawyer = payload["lawyer"]
        case = payload["case"]
        case_number = payload["case_number"]
        customer_name = payload["customer_name"]
        customer_email = payload["customer_email"]
        timestamp = payload["timestamp"]
        customer_phone = payload["customer_phone"]
        role_code = UserRoleEnum.NAVIGATOR.value

        # Extract case_id from case object
        case_id = case.id if hasattr(case, "id") else None
        if case_id is None:
            raise ValueError("Customer Talk to Expert Navigator Card event: case_id not found in case object")  # noqa: TRY301

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Customer Talk to Expert Navigator Card event: Invalid case ID format") from e

        template, last_version = get_template_json(
            str(ComponentEnum.CUSTOMER_TALK_TO_LAW_NN_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CUSTOMER_TALK_TO_LAW_NN_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Customer Talk to Expert Navigator Card event: Timeline type not found")  # noqa: TRY301

        # Prepare action_by from current_user
        first_name = event.current_user.first_name if event.current_user.first_name is not None else ""
        last_name = event.current_user.last_name if event.current_user.last_name is not None else ""
        action_by = f"{first_name} {last_name}".strip()

        # Prepare lawyer information
        lawyer_name = ""
        lawyer_email = ""
        if hasattr(lawyer, "user") and lawyer.user:
            lawyer_first_name = lawyer.user.first_name if lawyer.user.first_name else ""
            lawyer_last_name = lawyer.user.last_name if lawyer.user.last_name else ""
            lawyer_name = f"{lawyer_first_name} {lawyer_last_name}".strip()
            lawyer_email = lawyer.user.email if lawyer.user.email else ""

        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "timestamp": timestamp,
            "case_number": case_number,
            "lawyer_name": lawyer_name,
            "lawyer_email": lawyer_email,
            "customer_name": customer_name,
            "customer_email": customer_email,
            "customer_phone": customer_phone,
            "action_buttons": {},
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)
        if errors:
            logger.error(
                f"Customer Talk to Expert Navigator Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Customer Talk to Expert Navigator Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=event.current_user.id,
        )

        should_display = False
        if event.current_user and event.current_user.user_roles[0].role_id == UserRoleEnum.CUSTOMER.id:
            should_display = False

        return EventResponseData(
            should_display=should_display,
            success=True,
            message="Customer talk to expert navigator card generated and saved to timeline successfully.",
            data=card_data,
        )

    except Exception as e:
        logger.exception(
            f"Customer Talk to Expert Navigator Card event: Error in handle_customer_talk_to_law_nn_card: {e}"
        )
        raise


@event(EventType.COMPLETE_ONBOARD_ASSESSMENT)  # type: ignore
async def handle_complete_onboard_assessment(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle complete onboard assessment main event: Validates payload and triggers sub-events.
    Required payload:
    {
        "case_id": "1",
        "case_number": "CASE-001",
        "lawyer_name": "John Doe",
        "customer_name": "Jane Smith",
        "case_type": "Family Law",
        "timestamp": "2021-01-01T00:00:00Z"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "case_number",
            "lawyer_name",
            "customer_name",
            "case_type",
            "timestamp"
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Complete Onboard Assessment: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Complete Onboard Assessment: Required keys not found in payload")  # noqa: TRY301

        # Validate case_id format
        try:
            int(payload["case_id"])
        except (ValueError, TypeError) as e:
            raise ValueError(
                "Complete Onboard Assessment: Invalid case ID format"
            ) from e

        return EventResponseData(
            success=True,
            message="Complete onboard assessment event handled successfully.",
            data=payload,
        )

    except Exception as e:
        logger.exception(
            f"Complete Onboard Assessment: Error in handle_complete_onboard_assessment: {e}"
        )
        raise


@event(EventType.COMPLETE_ONBOARD_ASSESSMENT_CUS_CARD)  # type: ignore
async def handle_complete_onboard_assessment_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle complete onboard assessment customer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": "1",
        "case_number": "CASE-001",
        "lawyer_name": "John Doe",
        "customer_name": "Jane Smith",
        "case_type": "Family Law",
        "timestamp": "2021-01-01T00:00:00Z"
    }
    """
    try:
        payload = event.payload
        required_keys = [
            "case_id",
            "case_number",
            "lawyer_name",
            "customer_name",
            "case_type",
            "timestamp"
        ]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Complete Onboard Assessment Customer Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Complete Onboard Assessment Customer Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        case_number = payload["case_number"]
        lawyer_name = payload["lawyer_name"]
        customer_name = payload["customer_name"]
        case_type = payload["case_type"]
        timestamp = payload["timestamp"]
        role_code = UserRoleEnum.CUSTOMER.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError(
                "Complete Onboard Assessment Customer Card event: Invalid case ID format"
            ) from e

        template, last_version = get_template_json(
            str(ComponentEnum.COMPLETE_ONBOARD_ASSESSMENT_CUS_CARD.value),
            str(role_code),
            "timeline",
        )

        timeline_type = get_timeline_type(
            db,
            ComponentEnum.COMPLETE_ONBOARD_ASSESSMENT_CUS_CARD.value,
            role_code,
            last_version,
        )
        if timeline_type is None:
            raise ValueError("Complete Onboard Assessment Customer Card event: Timeline type not found")  # noqa: TRY301

        # Prepare placeholder values
        placeholder_values = {
            "action_by": "",
            "timestamp": timestamp,
            "case_number": case_number,
            "lawyer_name": lawyer_name,
            "case_id": encrypt_id(str(case_id)),
            "customer_name": customer_name,
            "case_type": case_type,
            "action_buttons": {"mark_onboarding_completed": True},
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(
                f"Complete Onboard Assessment Customer Card event: Template placeholder errors: {errors}"
            )
            raise ValueError(f"Complete Onboard Assessment Customer Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        timeline_event = save_timeline_event(
            db=db, case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=event.user_id,
        )

        timeline = get_timeline_event_from_map(db, str(timeline_type.type_name), int(case_id), int(timeline_event.id))
        # Save timeline_map
        if not timeline:
            save_timeline_map(db, int(timeline_event.id), str(timeline_type.type_name), int(case_id))

        return EventResponseData(
            success=True,
            message="Complete onboard assessment customer card generated and saved to timeline successfully.",
            data=card_data,
        )

    except Exception as e:
        logger.exception(
            f"Complete Onboard Assessment Customer Card event: Error in handle_complete_onboard_assessment_cus_card: {e}"
        )
        raise


@event(EventType.CASE_PATHWAY_OVERVIEW_CUS_CARD)  # type: ignore
async def handle_case_pathway_overview_cus_card(
    db: Session, event: Event, websocket_manager: WebSocketManager
) -> EventResponseData:
    """
    Handle case pathway overview customer card event: Generate card JSON using template and save to timeline_event table.
    Required payload:
    {
        "case_id": 1,
        "first_name": "John",
        "title": "Case Title",
        "summary": "Case summary text",
        "recommendations": {"key": "value"},
        "resolve_id": "encrypted_resolve_id",
        "timestamp": "2021-01-01T00:00:00Z",
        "case_number": "CASE-001",
    }
    """
    try:
        payload = event.payload
        # kyc_id is optional since it may not exist at case open time
        required_keys = ["case_id", "first_name", "title", "summary", "recommendations", "resolve_id", "timestamp", "case_number"]
        validation = validate_event_payload(payload, required_keys)  # type: ignore
        if not validation["status"]:
            logger.error(
                f"Case Pathway Overview Customer Card event: Payload validation failed for {event.event_type.value}: {validation}"
            )
            raise ValueError("Case Pathway Overview Customer Card event: Required keys not found in payload")  # noqa: TRY301

        case_id = payload["case_id"]
        first_name = payload["first_name"]
        title = payload["title"]
        summary = payload["summary"]
        recommendations = payload["recommendations"]
        resolve_id = payload["resolve_id"]
        timestamp = payload["timestamp"]
        case_number = payload.get("case_number", None)
        role_code = UserRoleEnum.CUSTOMER.value

        # Validate case_id format and convert to int
        try:
            case_id = int(case_id)
        except (ValueError, TypeError) as e:
            raise ValueError("Case Pathway Overview Customer Card event: Invalid case ID format") from e

        template, last_version = get_template_json(
            str(ComponentEnum.CASE_PATHWAY_OVERVIEW_CUS_CARD.value), str(role_code), "timeline"
        )

        timeline_type = get_timeline_type(
            db, ComponentEnum.CASE_PATHWAY_OVERVIEW_CUS_CARD.value, role_code, last_version
        )
        if timeline_type is None:
            raise ValueError("Case Pathway Overview Customer Card event: Timeline type not found")  # noqa: TRY301
        
        kyc_id=None

        action_by = f"{event.current_user.first_name} {event.current_user.last_name}".strip() if event.current_user.last_name is not None else ""
        # Prepare placeholder values
        placeholder_values = {
            "action_by": action_by,
            "first_name": first_name,
            "title": title,
            "summary": summary,
            "recommendations": recommendations,
            "resolve_id": encrypt_id(str(resolve_id)) if resolve_id else None,
            "kyc_id": kyc_id,
            "timestamp": timestamp,
            "case_number": case_number,
            "action_buttons": {
                "view_resolve": True,
                "view_kyc": True,
            },
        }

        # Replace placeholders in template
        errors: list[str] = []
        card_data = replace_placeholders(template, placeholder_values, errors)

        if errors:
            logger.error(f"Case Pathway Overview Customer Card event: Template placeholder errors: {errors}")
            raise ValueError(f"Case Pathway Overview Customer Card event: Template processing failed: {', '.join(errors)}")  # noqa: TRY301

        # Save timeline event
        timeline_event = save_timeline_event(
            db=db,
            case_id=case_id,
            timeline_type=timeline_type,
            meta_data=card_data,
            action_user_id=event.user_id,
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
            message="Case pathway overview customer card generated and saved to timeline successfully.",
            data=card_data,
        )

    except Exception as e:
        logger.exception(
            f"Case Pathway Overview Customer Card event: Error in handle_case_pathway_overview_cus_card: {e}"
        )
        raise

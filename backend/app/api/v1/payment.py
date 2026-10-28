"""Customer API endpoints."""

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.security import get_current_active_user
from app.db.database import get_db
from app.db.models.user import User
from app.db.services.payment import (
    get_payload_from_invoice,
    get_payment_by_id,
    retrieve_metadata_transactional,
    update_timeline_event_metadata,
)
from app.db.services.timeline_event import check_customer_case_access
from app.enums.events import EventType
from app.enums.payment import InvoiceStatusEnum, PaymentStatusEnum
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.base import ResponseMessage
from app.schemas.v1.event import Event
from app.schemas.v1.payment import (
    CreateCheckoutSessionRequest,
    CreateCheckoutSessionResponse,
    StripeWebhookResponse
)
from app.utils.encryption import decrypt_id, encrypt_id
from app.utils.helpers import extract_status_messages
from app.db.services.user import get_user_by_id
import time

logger = get_logger(__name__)

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

def _raise_bad_request(detail: str) -> None:
    """Raise HTTPException for bad request."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

def _raise_forbidden_error(detail: list[dict[str, object]]) -> None:
    """Raise HTTPException for forbidden access."""
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


@router.get("/checkout")
async def create_checkout_session(
    current_user: User = Depends(get_current_active_user),
    request_data: CreateCheckoutSessionRequest = Depends(),
    db: Session = Depends(get_db),
) -> CreateCheckoutSessionResponse:
    """Create a payment checkout session for a customer."""
    try:
        customer = current_user.customer if current_user.customer else None
        if customer is None:
            _raise_bad_request("Invalid User")

        # At this point, customer is guaranteed to be non-None
        assert customer is not None

        try:
            customer_id = int(customer.id)
        except (ValueError, TypeError):
            _raise_bad_request("Invalid customer id")
        
        payment_id = request_data.payment_id
        payment = get_payment_by_id(db, int(payment_id))
        if payment is None:
            _raise_bad_request("Payment not found")
        
        invoice = payment.invoice_payments[0].invoice
        if invoice is None:
            _raise_bad_request("Invoice not found")

        # At this point, invoice is guaranteed to be non-None
        assert invoice is not None

        if invoice.status == InvoiceStatusEnum.COMPLETED:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
                "success": False,
                "message": "Invoice payment already completed",
            })

        valid = check_customer_case_access(db, customer_id, int(invoice.case_id))
        if valid is False:
            _raise_forbidden_error("You are not authorized to access this resource.")

        request_amount = request_data.amount
        invoice_amount = invoice.invoice_amount
        if request_amount != invoice_amount:
            _raise_bad_request("Amount does not match invoice amount")

        encrypted_user_id = encrypt_id(str(current_user.id))
        encrypted_case_id = encrypt_id(str(invoice.case_id))
        encrypted_payment_id = encrypt_id(str(payment_id))

        stripe.api_key = settings.STRIPE_SECRET_KEY
        expires_at = int(time.time()) + settings.CHECKOUT_SESSION_EXPIRATION_TIME
        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": request_data.currency if request_data.currency else "GBP",
                        "product_data": {
                            "name": "Nova Law Checkout",
                        },
                        "unit_amount": int(request_amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            customer_email=str(current_user.email),
            mode="payment",
            payment_intent_data={
                "metadata": {
                    "user_id": encrypted_user_id or "",
                    "payment_id": encrypted_payment_id or "",
                }
            },
            success_url=settings.FRONTEND_URL + f"/case/{encrypted_case_id}",
            cancel_url=settings.FRONTEND_URL + f"/case/{encrypted_case_id}",
            expires_at=expires_at,  # Set expiration to 30 minutes from creation
        )

        logger.info(f"Checkout session created successfully for user {current_user.email}")
        return CreateCheckoutSessionResponse(
            success=True,
            message=[ResponseMessage(success=True, message="Checkout session created successfully")],
            data={
                "checkout_session_url": checkout_session.url
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to create checkout session: {e!s}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create checkout session: {e!s}") from e


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
) -> StripeWebhookResponse:
    """Handle stripe webhook."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except Exception as e:
        logger.exception(f"Error verifying stripe webhook: {e!s}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error verifying stripe webhook: {e!s}") from e

    try:
        messages: list[dict[str, str]] = []
        if event["type"] == "payment_intent.payment_failed":
            user, invoice, payment, transaction = retrieve_metadata_transactional(db, event, PaymentStatusEnum.FAILED)
            update_timeline_event_metadata(db, int(payment.id), transaction)
        
        elif event["type"] == "payment_intent.canceled":
            user, invoice, payment, transaction = retrieve_metadata_transactional(db, event, PaymentStatusEnum.CANCELLED)
            if invoice.status == InvoiceStatusEnum.COMPLETED:
                return StripeWebhookResponse(
                    success=True,
                    message=[ResponseMessage(success=True, message="Payment already marked as completed")],
                    data={}
                )
            
            update_timeline_event_metadata(db, int(payment.id), transaction)

        elif event["type"] == "checkout.session.completed":

            invoice_id_encrypted = ""
            event_object = event.get("data",{}).get("object", {})
            if event_object:
                payment_intent_id = event_object.get("payment_intent", "")
                stripe.api_key = settings.STRIPE_SECRET_KEY
                payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
                charge_id = payment_intent.latest_charge
                charge = stripe.Charge.retrieve(charge_id)
                metadata = charge.get("metadata", {})
                if not metadata:
                    _raise_bad_request("Webhook update event: Metadata not found")

                user_id_encrypted = metadata.get("user_id", "")
                payment_id_encrypted = metadata.get("payment_id", "")
            else:
                _raise_bad_request("Webhook update event: event_object not found")

            # At this point, invoice_id_encrypted is guaranteed to be a string
            assert isinstance(user_id_encrypted, str)
            assert isinstance(payment_id_encrypted, str)
            
            user_id_decrypted = decrypt_id(user_id_encrypted)
            if user_id_decrypted is None:
                _raise_bad_request("Webhook update event: Failed to decrypt user id")

            payment_id_decrypted = decrypt_id(payment_id_encrypted)
            if payment_id_decrypted is None:
                _raise_bad_request("Webhook update event: Failed to decrypt payment id")

            assert user_id_decrypted is not None
            assert payment_id_decrypted is not None
            user_id = int(user_id_decrypted)
            payment_id = int(payment_id_decrypted)

            payment = get_payment_by_id(db, payment_id)
            if payment is None:
                _raise_bad_request("Webhook update event: Payment not found")

            invoice = payment.invoice_payments[0].invoice
            if invoice is None:
                _raise_bad_request("Webhook update event: Invoice not found")
            invoice_id_encrypted = encrypt_id(str(invoice.id))
            
            user = get_user_by_id(db, user_id)
            if user is None:
                _raise_bad_request("Webhook update event: User not found")

            # At this point, invoice is guaranteed to be non-None
            assert invoice is not None
            assert user is not None
            assert payment is not None
            if invoice.status == InvoiceStatusEnum.COMPLETED:
                return StripeWebhookResponse(
                    success=True,
                    message=[ResponseMessage(success=True, message="Payment already marked as completed")],
                    data={}
                )

            event_data = Event(
                event_type=EventType.CUSTOMER_PMT_COMPLETE,
                payload={
                    "payment_event": charge,
                    "invoice": invoice,
                    "payment":payment,
                    "current_user":user,
                },
                user_id=None,
            )

            # Dispatch event using the new system
            await event_dispatcher.dispatch_event(db, event_data)

            # Extract status messages from event responses
            response = event_data.response
            if response is None:
                _raise_event_processing_error()

            success, raw_messages_dict = extract_status_messages(response) # type: ignore[arg-type]
            if not success:
                _raise_validation_error(detail=raw_messages_dict)

            logger.info(f"Customer initial payment processed for invoice: {invoice_id_encrypted} : {raw_messages_dict}")

            payload = get_payload_from_invoice(db, invoice, user)
            if payload is None:
                _raise_bad_request("Webhook update event: Failed to get payload from invoice")

            onboard_event = Event(
                event_type=EventType.COMPLETE_ONBOARD_ASSESSMENT,
                payload=payload,
                user_id=user.id,
            )

            # Dispatch event using the new system
            await event_dispatcher.dispatch_event(db, onboard_event)

            # Extract status messages from event responses
            onboard_event_response = onboard_event.response

            if onboard_event_response is None:
                _raise_event_processing_error()

            success, messages = extract_status_messages(onboard_event_response) # type: ignore[arg-type]
            if not success:
                _raise_validation_error(detail=messages)

        return StripeWebhookResponse(
            success=True,
            message=messages,
            data={}
        )

    except Exception as e:
        logger.exception(f"Error processing stripe webhook: {e!s}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Error processing stripe webhook: {e!s}") from e

"""Payment service functions for database operations."""

from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.core.logging import get_logger
from app.db.models import Case, Invoice, User, CaseLawyer, Lawyer
from app.db.models.invoice_payment import InvoicePayment
from app.db.models.payment import Payment
from app.db.models.timeline_event import TimelineEvent
from app.db.models.transaction import Transaction
from app.db.services.timeline_event import (
    get_timeline_event_from_map,
)
from app.db.services.user import get_user_by_id
from app.enums.component import ComponentEnum
from app.enums.payment import PaymentStatusEnum
from app.utils.encryption import decrypt_id
from app.utils.formatters import format_case_number
import json
from app.core.config import settings
logger = get_logger(__name__)


def update_timeline_event_metadata(db: Session, payment_id: int, transaction: Transaction) -> TimelineEvent | None:
    """Update timeline event metadata."""
    timeline_events = get_timeline_event_from_map(db, str(ComponentEnum.CUSTOMER_PMT_REQUESTED_CUS_CARD.value), payment_id)
    if timeline_events is None:
        raise ValueError("Timeline event not found")
    # Get the first timeline event from the list
    timeline_event = timeline_events[0]
    
    # Load existing metadata
    meta_data = json.loads(timeline_event.meta_data) if timeline_event.meta_data else {}
    
    # Update metadata with failed attempts
    failed_attempts = meta_data.get("failed_attempts", []) if meta_data.get("failed_attempts") else []
    failed_attempts_updated = failed_attempts + [{
        "reason": transaction.reason, 
        "transaction_id": transaction.transaction_id, 
        "created_at": transaction.created_at.isoformat()
    }]
    meta_data["failed_attempts"] = failed_attempts_updated
    meta_data["action_buttons"] = {"make_payment": True, "view_failed_attempts": True}
    timeline_event.meta_data = json.dumps(meta_data) if meta_data else None
    db.commit()
    return timeline_event


def get_payment_by_id(db: Session, payment_id: int) -> Payment | None:
    """Get payment by ID."""
    return db.query(Payment).options(joinedload(Payment.invoice_payments).joinedload(InvoicePayment.invoice)).filter(Payment.id == payment_id).first()


def retrieve_metadata_transactional(db: Session, event_data: dict, payment_status: PaymentStatusEnum) -> tuple[User, Invoice, Payment, Transaction]:
    """Retrieve ids from metadata."""
    user_id: int | None = None
    payment_id: int | None = None
    event_object = event_data.get("data",{}).get("object", {})
    metadata = event_object.get("metadata", {})
    if metadata:
        payment_intent_id = event_object.get("id", "")
        user_id_encrypted = metadata.get("user_id", "")
        payment_id_encrypted = metadata.get("payment_id", "")
        if payment_id_encrypted:
            payment_id_decrypted = decrypt_id(payment_id_encrypted)
            if payment_id_decrypted is not None:
                payment_id = int(payment_id_decrypted)

        if user_id_encrypted:
            user_id_decrypted = decrypt_id(user_id_encrypted)
            if user_id_decrypted is not None:
                user_id = int(user_id_decrypted)

        user = get_user_by_id(db, user_id)
        if user is None:
            raise ValueError("Webhook update event: User not found")
        
        payment = get_payment_by_id(db, payment_id)
        if payment is None:
            ValueError("Webhook update event: Payment not found")
        
        invoice = payment.invoice_payments[0].invoice
        if invoice is None:
            ValueError("Webhook update event: Invoice not found")
        
        transaction_id = None
        reason = None
        payment_type = None
        if payment_status == PaymentStatusEnum.FAILED:
            transaction_id = event_object.get("latest_charge", "")
            error_details = event_object.get("last_payment_error", {})       
            reason = error_details.get("message", "")
            payment_type = error_details.get("payment_method", {}).get("type", "")
        
        if payment_status == PaymentStatusEnum.CANCELLED:
            reason = "Payement session expired, please try again."
        
        transaction = Transaction(
            payment_id=payment_id,
            transaction_id=transaction_id,
            reason=reason,
            status=payment_status,
        )
        db.add(transaction)

        payment.status = payment_status
        payment.transaction_id = transaction_id
        payment.remarks = reason
        payment.payment_method = payment_type
        payment.payment_intent_id = payment_intent_id
        db.commit()
        
        # save_transaction(db, payment.id, event_data)
        return user, invoice, payment, transaction
    else:
        raise ValueError("Webhook update event: Metadata not found")


def get_payload_from_invoice(db: Session, invoice: Invoice, user: User) -> dict:
    """Get payload from invoice."""
    payload = {}
    payload["case_id"] = invoice.case_id
    case = db.query(Case).options(
        joinedload(Case.case_lawyers)
        .joinedload(CaseLawyer.lawyer)
        .joinedload(Lawyer.lawyer_law_firms)
        ).filter(Case.id == invoice.case_id).first()

    # case = get_case_by_id(db, int(invoice.case_id))
    if case is None:
        raise ValueError("Case not found")
    lawyer = case.case_lawyers[0].lawyer
    lawyer_user = lawyer.user
    law_firm = lawyer.lawyer_law_firms[0].law_firm
    lawyer_name = ""
    lawyer_first_name = lawyer_user.first_name if lawyer_user.first_name else ""
    lawyer_last_name = lawyer_user.last_name if lawyer_user.last_name else ""
    lawyer_name = f"{lawyer_first_name} {lawyer_last_name}".strip()
    engage_url = settings.ENGAGE_AUTH_URL
    client_id = law_firm.engage_form_url if law_firm else None

    customer_name = ""
    customer_first_name = user.first_name if user.first_name else ""
    customer_last_name = user.last_name if user.last_name else ""
    customer_name = f"{customer_first_name} {customer_last_name}".strip()
    payload["case_number"] = format_case_number(case.case_no)
    payload["lawyer_name"] = lawyer_name
    payload["customer_name"] = customer_name
    payload["case_id"] = case.id
    payload["customer_email"] = user.email
    payload["engage_url"] = engage_url if engage_url else ""
    payload["case_type"] = case.case_type.value
    payload["timestamp"] = datetime.now().isoformat()
    
    return payload


def create_payment_transaction(db: Session, invoice_id: int, amount_paid: float) -> Payment | None:
    """Create payment transaction."""
    payment = Payment(
        amount_paid=amount_paid,
        status=PaymentStatusEnum.PENDING,
    )
    db.add(payment)
    db.flush()
    db.add(InvoicePayment(payment_id=payment.id, invoice_id=invoice_id))
    db.commit()
    return payment
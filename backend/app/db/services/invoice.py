"""Payment service functions for database operations."""

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.core.config import settings
from app.db.models import Invoice
from app.enums.payment import InvoiceStatusEnum

logger = get_logger(__name__)


def get_invoice_transactional(db: Session, case_id: int, lawyer_id: int, amount:float) -> Invoice | None:
    """create invoice transactional by case ID."""
    invoice = Invoice(
        case_id=case_id,
        lawyer_id=lawyer_id,
        invoice_date=datetime.now(timezone.utc).date(),
        invoice_amount=amount,
        status=InvoiceStatusEnum.PENDING,
    )
    db.add(invoice)
    db.flush()
    db.commit()
    return invoice
    
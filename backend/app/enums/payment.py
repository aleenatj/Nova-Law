from enum import Enum


class InvoiceStatusEnum(str, Enum):
    """Match status enum."""

    PENDING = "pending"
    PARTIALLY_PAID = "partially_paid"
    COMPLETED = "completed"
    CANCELLED = "cancelled"    


class PaymentStatusEnum(str, Enum):
    """Payment status enum."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"
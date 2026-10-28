from sqlalchemy import Column, Date, DateTime, Enum, Float, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.enums.payment import PaymentStatusEnum


class Payment(Base):
    """Payment model for transaction management."""

    __tablename__ = "payment"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    transaction_id = Column(String(50), nullable=True)
    payment_intent_id = Column(String(50), nullable=True)
    payment_date = Column(Date, nullable=True)
    payment_method = Column(String(50), nullable=True)
    amount_paid = Column(Float, nullable=True)
    status: Column = Column(
        Enum(PaymentStatusEnum, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatusEnum.PENDING,
    )
    remarks = Column(String(250), nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    invoice_payments = relationship("InvoicePayment", back_populates="payment", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="payment", cascade="all, delete-orphan")

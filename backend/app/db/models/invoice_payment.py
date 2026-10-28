from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class InvoicePayment(Base):
    """Junction table for many-to-many relationship between Invoice and Payment."""

    __tablename__ = "invoice_payment"

    payment_id = Column(Integer, ForeignKey("payment.id"), nullable=False, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoice.id"), nullable=False, primary_key=True)
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
    payment = relationship("Payment", back_populates="invoice_payments")
    invoice = relationship("Invoice", back_populates="invoice_payments")

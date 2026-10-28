from sqlalchemy import Column, Date, DateTime, Enum, Float, ForeignKey, Identity, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.enums.payment import InvoiceStatusEnum


class Invoice(Base):
    """Invoice model for billing and invoicing."""

    __tablename__ = "invoice"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    case_id = Column(Integer, ForeignKey("case.id"), nullable=False)
    lawyer_id = Column(Integer, ForeignKey("lawyer.id"), nullable=False)
    invoice_number = Column(String(50), nullable=True)
    serial_number = Column(Integer, Identity(start=0, increment=1),nullable=False, unique=True, index=True)
    invoice_date = Column(Date, nullable=False)
    invoice_amount = Column(Float, nullable=False)
    status: Column = Column(
        Enum(InvoiceStatusEnum, name="invoice_status_enum"),
        nullable=False,
        default=InvoiceStatusEnum.PENDING,
    )
    remarks = Column(String(250), nullable=True)
    action_user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
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
    case = relationship("Case", back_populates="invoices")
    lawyer = relationship("Lawyer", back_populates="invoices")
    action_user = relationship("User", back_populates="invoices")
    invoice_payments = relationship("InvoicePayment", back_populates="invoice", cascade="all, delete-orphan")

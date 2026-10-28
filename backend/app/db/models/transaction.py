from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.enums.payment import PaymentStatusEnum


class Transaction(Base):
    """Transaction model for payment transactions."""

    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    payment_id = Column(Integer, ForeignKey("payment.id"), nullable=False)
    transaction_id = Column(String(50), nullable=True)
    reason = Column(String(250), nullable=True)
    status: Column = Column(
        Enum(PaymentStatusEnum, name="payment_status_enum"),
        nullable=False,
        default=PaymentStatusEnum.PENDING,
    )
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    payment = relationship("Payment", back_populates="transactions")


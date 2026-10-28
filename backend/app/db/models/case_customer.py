from sqlalchemy import Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


class CaseCustomer(Base):
    __tablename__ = "case_customer"

    case_id = Column(Integer, ForeignKey("case.id"), primary_key=True)
    customer_id = Column(Integer, ForeignKey("customer.id"), primary_key=True)
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
    case = relationship("Case", back_populates="case_customers")
    customer = relationship("Customer", back_populates="case_customers")

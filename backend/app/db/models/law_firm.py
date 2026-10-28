from sqlalchemy import Column, DateTime, Integer, String, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.enums.law_firm_type import LawFirmType
from app.enums.law_firm import LawFirmStatusEnum

class LawFirm(Base):
    """Law Firm model."""

    __tablename__ = "law_firm"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    contact_person = Column(String(100), nullable=False)
    contact_no = Column(String(20), nullable=True)
    contact_email = Column(String(255), unique=True, nullable=False)
    address_line_1 = Column(String(255), nullable=True)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    country = Column(String(100), nullable=True)
    logo = Column(String(500), nullable=True)
    about = Column(Text, nullable=True)
    website_url = Column(String(500), nullable=True)
    engage_form_url = Column(String(500), nullable=True, unique=True)
    law_firm_type = Column(Enum(LawFirmType), nullable=True)
    status = Column(
            Enum(LawFirmStatusEnum, name="law_firm_status_enum"),
            nullable=False,
            default=LawFirmStatusEnum.ACTIVE,
    )
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
    lawyer_law_firms = relationship(
        "LawyerLawFirm", back_populates="law_firm", cascade="all, delete-orphan"
    )

from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String, Text, Float
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func

from app.db.database import Base
from app.enums.lawyer_onboarding import (
    LawyerOnboardingGenderEnum,
    LawyerOnboardingStatusEnum,
    RemoteConsultationEnum,
)


class LawyerOnboarding(Base):
    __tablename__ = "lawyer_onboarding"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    work_status = Column(String(100), nullable=False)
    firm_name = Column(String(100), nullable=True)
    city = Column(String(100), nullable=False)
    post_code = Column(String(20), nullable=False)
    gender = Column(
        Enum(
            LawyerOnboardingGenderEnum,
            name="lawyer_onboarding_gender",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=True,
    )
    photo_url = Column(Text, nullable=True)
    professional_status = Column(JSON, nullable=True)
    experience = Column(Float, nullable=True)
    service_details = Column(JSON, nullable=True)
    matter_types = Column(JSON, nullable=True)
    accredited_specialism_other = Column(JSON, nullable=True)
    ncdr_magic = Column(JSON, nullable=True)
    accredited_specialist = Column(JSON, nullable=True)
    regulator = Column(JSON, nullable=True)
    ncdr_description = Column(Text, nullable=True)
    compelling_quote = Column(Text, nullable=True)
    remote_consultation = Column(
        Enum(
            RemoteConsultationEnum,
            name="lawyer_onboarding_remote_consultation",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=True,
    )
    consultation_offers = Column(JSON, nullable=True)
    status = Column(
        Enum(
            LawyerOnboardingStatusEnum,
            name="lawyer_onboarding_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=LawyerOnboardingStatusEnum.NEW,
    )

    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True), nullable=True, server_default=func.now(), onupdate=func.now()
    )


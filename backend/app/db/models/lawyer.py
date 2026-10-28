from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base
from app.enums.lawyer import (
    DRPreferenceEnum,
    ExpertTypeEnum,
    LawyerConflictLevelEnum,
    LawyerStatusEnum,
    MatterTypeEnum,
    RegulatorEnum,
    RelationshipTypeEnum,
    ExpertiseEnum,
    AccreditedSpecialismEnum,
)


class Lawyer(Base):
    __tablename__ = "lawyer"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    status: Column = Column(
        Enum(
            LawyerStatusEnum,
            name="lawyer_status",
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=LawyerStatusEnum.ACTIVE,
    )
    address_line_1 = Column(String(255), nullable=True)
    address_line_2 = Column(String(255), nullable=True)
    city = Column(String(100), nullable=True)
    county = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    postal_code = Column(String(20), nullable=True)
    reg_no = Column(String(100), nullable=True)
    sra_number = Column(String(100), nullable=True)
    bar_number = Column(String(100), nullable=True)
    regulator: Column = Column(
        Enum(
            RegulatorEnum,
            name="lawyer_regulator",
            values_callable=lambda obj: [e.name for e in obj],
        ),
        nullable=True,
    )
    regulator_other = Column(String(255), nullable=True)
    admitted_date_solicitor = Column(Date, nullable=True)
    called_date_barrister = Column(Date, nullable=True)
    admitted_date_cliex = Column(Date, nullable=True)
    joined_at = Column(DateTime(timezone=True), nullable=True)
    left_at = Column(DateTime(timezone=True), nullable=True)
    about = Column(Text, nullable=True)
    photo_url = Column(Text, nullable=True)
    # accredited_specialisations = Column(Text, nullable=True)
    testimonial = Column(Text, nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    hourly_rate = Column(Float, nullable=True)
    charge_first_consultation = Column(Float, nullable=True)
    conflict_level_disinclination: Column = Column(
        Enum(
            LawyerConflictLevelEnum,
            name="lawyer_conflict_level",
            values_callable=lambda obj: [e.name for e in obj],
        ),
        nullable=True,
    )
    pi_insurance = Column(String(100), nullable=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

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
    lawyer_law_firms = relationship("LawyerLawFirm", back_populates="lawyer")
    user = relationship("User", back_populates="lawyer")
    case_lawyers = relationship("CaseLawyer", back_populates="lawyer")
    matches = relationship("Match", back_populates="lawyer")
    invoices = relationship("Invoice", back_populates="lawyer")
    financial_claims_exemptions = Column(Boolean, nullable=False, default=False)
    expert_types = relationship(
        "LawyerExpertType", back_populates="lawyer", cascade="all, delete-orphan"
    )
    expert_types_other = Column(String(500), nullable=True)
    relationship_types = relationship(
        "LawyerRelationshipType", back_populates="lawyer", cascade="all, delete-orphan"
    )
    matter_types = relationship(
        "LawyerMatterType", back_populates="lawyer", cascade="all, delete-orphan"
    )
    dr_preferences = relationship(
        "LawyerDRPreference", back_populates="lawyer", cascade="all, delete-orphan"
    )
    expertises = relationship(
        "LawyerExpertise", back_populates="lawyer", cascade="all, delete-orphan"
    )
    expertises_other = Column(JSON, nullable=True)
    accredited_specialisms = relationship(
        "LawyerAccreditedSpecialism", back_populates="lawyer", cascade="all, delete-orphan"
    )
    accredited_specialism_other = Column(JSON, nullable=True)


class LawyerExpertType(Base):
    __tablename__ = "lawyer_expert_type"

    lawyer_id = Column(Integer, ForeignKey("lawyer.id"), nullable=False, primary_key=True)
    expert_type = Column(
        Enum(
            ExpertTypeEnum,
            name="expert_type_enum",
            values_callable=lambda obj: [e.name for e in obj],
        ),
        nullable=False,
        primary_key=True,
    )

    # Relationships
    lawyer = relationship("Lawyer", back_populates="expert_types")


class LawyerRelationshipType(Base):
    __tablename__ = "lawyer_relationship_type"

    lawyer_id = Column(Integer, ForeignKey("lawyer.id"), nullable=False, primary_key=True)
    relationship_type = Column(
        Enum(
            RelationshipTypeEnum,
            name="relationship_type_enum",
            values_callable=lambda obj: [e.name for e in obj],
        ),
        nullable=False,
        primary_key=True,
    )

    # Relationships
    lawyer = relationship("Lawyer", back_populates="relationship_types")


class LawyerMatterType(Base):
    __tablename__ = "lawyer_matter_type"

    lawyer_id = Column(Integer, ForeignKey("lawyer.id"), nullable=False, primary_key=True)
    matter_type = Column(
        Enum(
            MatterTypeEnum,
            name="matter_type_enum",
            values_callable=lambda obj: [e.name for e in obj],
        ),
        nullable=False,
        primary_key=True,
    )

    # Relationships
    lawyer = relationship("Lawyer", back_populates="matter_types")


class LawyerDRPreference(Base):
    __tablename__ = "lawyer_dr_preference"

    lawyer_id = Column(Integer, ForeignKey("lawyer.id"), nullable=False, primary_key=True)
    dr_preference = Column(
        Enum(
            DRPreferenceEnum,
            name="dr_preference_enum",
            values_callable=lambda obj: [e.name for e in obj],
        ),
        nullable=False,
        primary_key=True,
    )

    # Relationships
    lawyer = relationship("Lawyer", back_populates="dr_preferences")

class LawyerExpertise(Base):
    __tablename__ = "lawyer_expertise"

    lawyer_id = Column(Integer, ForeignKey("lawyer.id"), nullable=False, primary_key=True)
    expertise = Column(
        Enum(
            ExpertiseEnum,
            name="expertise_enum",
            values_callable=lambda obj: [e.name for e in obj],
        ),
        nullable=False,
        primary_key=True,
    )

    # Relationships
    lawyer = relationship("Lawyer", back_populates="expertises")

class LawyerAccreditedSpecialism(Base):
    __tablename__ = "lawyer_accredited_specialism"

    lawyer_id = Column(Integer, ForeignKey("lawyer.id"), nullable=False, primary_key=True)
    accredited_specialism = Column(
        Enum(
            AccreditedSpecialismEnum,
            name="accredited_specialism_enum",
            values_callable=lambda obj: [e.name for e in obj],
        ),
        nullable=False,
        primary_key=True,
    )

    # Relationships
    lawyer = relationship("Lawyer", back_populates="accredited_specialisms")
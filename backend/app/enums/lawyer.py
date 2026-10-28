from enum import Enum
from typing import Any
from pydantic_core import core_schema

class EnumSchemaMixin:
    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: Any
    ) -> dict[str, Any]:
        json_schema = handler(_core_schema)
        json_schema["enum"] = [member.name for member in cls]
        json_schema["type"] = "string"
        return json_schema


class RegulatorEnum(EnumSchemaMixin, str, Enum):
    """Regulator enum for lawyers."""

    SRA = "SRA"
    BSB = "BSB"
    CILEX = "Cilex Regulation"
    OTHER = "Other"

class LawyerStatusEnum(str, Enum):
    """Lawyer status enum."""

    ACTIVE = "Active"
    DEACTIVE = "Deactive"


class LawyerConflictLevelEnum(EnumSchemaMixin, str, Enum):
    """Lawyer conflict level enum."""

    MEDIUM_CONFLICT = "Medium conflict"
    HIGH_CONFLICT = "High Conflict"
    IMPLACABLE_HOSTILITY = "Implacable hostility"


class ExpertTypeEnum(EnumSchemaMixin, str, Enum):
    """Expert type enum."""

    SOLICITOR = "Solicitor"
    BARRISTER = "Barrister"
    CILEX = "Cilex"
    LAWYER_MEDIATOR = "Lawyer-Mediator"
    MEDIATOR = "Mediator"
    ARBITRATOR = "Arbitrator"
    DIVORCE_COACH = "Divorce Coach"
    FAMILY_CONSULTANT = "Family Consultant"
    OTHER = "Other"
    
    def is_other(self) -> bool:
        """Check if this expert type enum requires custom input (Other option)."""
        return self in (ExpertTypeEnum.OTHER)


class RelationshipTypeEnum(EnumSchemaMixin, str, Enum):
    """Relationship type enum."""

    MARRIED_CIVIL_PARTNERS = "Married and Civil Partners"
    COHABITEES = "Cohabitees"
    PARENTAL_RELATIONSHIPS = "Parental relationships"


class MatterTypeEnum(EnumSchemaMixin, str, Enum):
    """Matter type enum."""

    FINANCIAL_CLAIMS = "Financial Claims"
    CHILDREN = "Children"


class DRTypeEnum(EnumSchemaMixin, str, Enum):
    """Dispute resolution type category."""

    NORMAL = "Normal"
    SUPPORT = "Support"
    OTHER = "Other"


class DRPreferenceEnum(EnumSchemaMixin, str, Enum):
    """Dispute resolution process options."""

    DIRECT_NEGOTIATION = ("Direct Negotiation", DRTypeEnum.NORMAL, None)
    MEDIATION = ("Mediation", DRTypeEnum.NORMAL, None)
    ONE_LAWYER_ONE_COUPLE = ("One Lawyer One Couple", DRTypeEnum.NORMAL, None)
    COLLABORATIVE = ("Collaborative", DRTypeEnum.NORMAL, None)
    HYBRID_MEDIATION_SUPPORT = (
        "Hybrid Mediation-Support",
        DRTypeEnum.SUPPORT,
        "Hybrid Mediation",
    )
    HYBRID_MEDIATION_MEDIATOR = (
        "Hybrid Mediation-Mediator",
        DRTypeEnum.OTHER,
        "Hybrid Mediation",
    )
    LAWYER_NEGOTIATION = ("Lawyer Negotiation", DRTypeEnum.NORMAL, None)
    EARLY_NEUTRAL_EVALUATION_SUPPORT = (
        "Early Neutral Evaluation/Private FDR-Support",
        DRTypeEnum.SUPPORT,
        "Early Neutral Evaluation/Private FDR",
    )
    EARLY_NEUTRAL_EVALUATION_EVALUATOR = (
        "Early Neutral Evaluation/Private FDR-Evaluator",
        DRTypeEnum.OTHER,
        "Early Neutral Evaluation/Private FDR",
    )
    ARBITRATION_SUPPORT = ("Arbitration-Support", DRTypeEnum.SUPPORT, "Arbitration")
    ARBITRATION_ARBITRATOR = ("Arbitration-Arbitrator", DRTypeEnum.OTHER, "Arbitration")
    COURT = ("Court", DRTypeEnum.NORMAL, None)

    def __new__(cls, full_name: str, type_: DRTypeEnum, base: str | None) -> "DRPreferenceEnum":
        obj = str.__new__(cls, full_name)
        obj._value_ = full_name
        return obj

    def __init__(self, full_name: str, type_: DRTypeEnum, base: str | None) -> None:
        self.full_name = full_name
        self.type_ = type_
        self.base = base


class ExpertiseEnum(EnumSchemaMixin, str, Enum):
    """Legal expertise enum mapping lawyer page to onboarding page."""

    DIVORCE_AND_SEPARATION = (
        "Divorce and Separation",
        None,
        (MatterTypeEnum.FINANCIAL_CLAIMS, MatterTypeEnum.CHILDREN),
        RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS,
        False,
    )
    FINANCIAL_CLAIMS = (
        "Financial Claims",
        "Financial remedy on divorce or separation",
        MatterTypeEnum.FINANCIAL_CLAIMS,
        RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS,
        False,
    )
    OVERSEAS_FINANCIAL_CLAIMS = (
        "Overseas Financial claims",
        "Financial remedy after overseas divorce",
        MatterTypeEnum.FINANCIAL_CLAIMS,
        RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS,
        False,
    )
    CHILD_ARRANGEMENTS = (
        "Child arrangements",
        "Children (child arrangements)",
        MatterTypeEnum.CHILDREN,
        RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS,
        False,
    )
    CHILDREN_DOMESTIC_RELOCATION = (
        "Children domestic relocation",
        "Children (domestic relocation)",
        MatterTypeEnum.CHILDREN,
        RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS,
        False,
    )
    CHILDREN_INTERNATIONAL_RELOCATION = (
        "Children international relocation",
        "Children (international relocation)",
        MatterTypeEnum.CHILDREN,
        RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS,
        False,
    )
    INHERITANCE_ACT_CLAIMS = (
        "Inheritance Act claims",
        "Inheritance Act claims",
        MatterTypeEnum.FINANCIAL_CLAIMS,
        RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS,
        False,
    )
    PRE_NUPTIAL_PRE_CIVIL_PARTNERSHIP_AGREEMENTS = (
        "Pre-nuptial & pre-civil partnership agreements",
        "Pre-nuptial & pre-civil partnership agreements",
        MatterTypeEnum.FINANCIAL_CLAIMS,
        RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS,
        False,
    )
    POST_NUPTIAL_POST_CIVIL_PARTNERSHIP_AGREEMENTS = (
        "Post-nuptial and post-civil partnership agreements",
        "Post-nuptial and post-civil partnership agreements",
        MatterTypeEnum.FINANCIAL_CLAIMS,
        RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS,
        False,
    )
    SEPARATION_AGREEMENTS = (
        "Separation agreements",
        "Separation agreements",
        MatterTypeEnum.FINANCIAL_CLAIMS,
        RelationshipTypeEnum.COHABITEES,
        False,
    )
    COHABITATION_CHILD_ARRANGEMENTS = (
        "Cohabitation - Child arrangements",
        "Children (child arrangements)",
        MatterTypeEnum.CHILDREN,
        RelationshipTypeEnum.COHABITEES,
        False,
    )
    COHABITATION_CHILDREN_DOMESTIC_RELOCATION = (
        "Cohabitation - Children domestic relocation",
        "Children (domestic relocation)",
        MatterTypeEnum.CHILDREN,
        RelationshipTypeEnum.COHABITEES,
        False,
    )
    COHABITATION_CHILDREN_INTERNATIONAL_RELOCATION = (
        "Cohabitation - Children international relocation",
        "Children (international relocation)",
        MatterTypeEnum.CHILDREN,
        RelationshipTypeEnum.COHABITEES,
        False,
    )
    COHABITATION_FINANCIAL_CLAIMS = (
        "Cohabitation - Financial Claims",
        "TOLATA",
        MatterTypeEnum.FINANCIAL_CLAIMS,
        RelationshipTypeEnum.COHABITEES,
        False,
    )
    LIVING_TOGETHER_AGREEMENTS = (
        "Living together agreements",
        "Living together agreements",
        MatterTypeEnum.FINANCIAL_CLAIMS,
        RelationshipTypeEnum.COHABITEES,
        False,
    )
    SCHEDULE_I_CLAIMS = (
        "Schedule I claims",
        "Schedule I claims",
        MatterTypeEnum.CHILDREN,
        RelationshipTypeEnum.COHABITEES,
        False,
    )
    COHABITATION_INHERITANCE_ACT_CLAIMS = (
        "Cohabitation - Inheritance Act claims",
        "Inheritance Act claims",
        MatterTypeEnum.FINANCIAL_CLAIMS,
        RelationshipTypeEnum.COHABITEES,
        False,
    )
    OTHER_MARRIED_CIVIL_PARTNERS = (
        "Other",
        None,
        None,
        RelationshipTypeEnum.MARRIED_CIVIL_PARTNERS,
        True,
    )
    OTHER_COHABITEES = (
        "Other ",
        None,
        None,
        RelationshipTypeEnum.COHABITEES,
        True,
    )

    def __new__(
        cls,
        lawyer_page: str,
        onboarding_page: str | None,
        matter_type: MatterTypeEnum | tuple[MatterTypeEnum, ...] | None,
        relationship_type: RelationshipTypeEnum,
        requires_custom_input: bool,
    ) -> "ExpertiseEnum":
        obj = str.__new__(cls, lawyer_page)
        obj._value_ = lawyer_page
        return obj

    def __init__(
        self,
        lawyer_page: str,
        onboarding_page: str | None,
        matter_type: MatterTypeEnum | tuple[MatterTypeEnum, ...] | None,
        relationship_type: RelationshipTypeEnum,
        requires_custom_input: bool,
    ) -> None:
        self.lawyer_page = lawyer_page
        self.onboarding_page = onboarding_page
        self.matter_type = matter_type
        self.relationship_type = relationship_type
        self.requires_custom_input = requires_custom_input

    def is_other(self) -> bool:
        """Check if this expertise enum requires custom input (Other option)."""
        return self in (ExpertiseEnum.OTHER_MARRIED_CIVIL_PARTNERS, ExpertiseEnum.OTHER_COHABITEES)

    def requires_custom_input(self) -> bool:
        """Check if this enum value requires custom text input."""
        return self.is_other()

class AccreditedSpecialismEnum(EnumSchemaMixin, str, Enum):
    """Accredited specialism enum."""

    RESOLUTION_ACCREDITED_SPECIALIST = "Resolution Accredited Specialist"
    LAW_SOCIETY_ACCREDITED_SPECIALIST = "Law Society Accredited Specialist"
    FMC_ACCREDITED_MEDIATOR = "FMC Accredited Mediator"
    CIARB_ACCREDITED_ARBITRATOR = "CIArb Accredited Arbitrator"
    OTHER = "Other"
    
    def is_other(self) -> bool:
        """Check if this accredited specialism enum requires custom input (Other option)."""
        return self in (AccreditedSpecialismEnum.OTHER)
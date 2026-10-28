from enum import Enum


class AgentType(str, Enum):
    """AI agent types."""

    GENERAL = "general"
    LEGAL_RESEARCH = "legal_research"
    DOCUMENT_REVIEW = "document_review"
    CONTRACT_ANALYSIS = "contract_analysis"
    CASE_ANALYSIS = "case_analysis"

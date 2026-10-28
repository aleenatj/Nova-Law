"""
Email CTA enums for the Nova Law AI application.
"""

from enum import Enum

class EmailType(str, Enum):
    """
    Enum representing email types in the Nova Law AI application.
    """
    PERSONALISED_RECOMMENDATION = "Personalised Recommendation"
    WELCOME_TO_NOVA = "Welcome to Nova"
    CASE_OPENED = "Case Opened"
    NOVA_EXPERT_ALIGNMENT_CHECK = "Nova Expert Alignment Check"
    YOUR_MATCHED_EXPERT = "Your Matched Expert"
    TALK_TO_NOVA_EXPERT = "Talk to Nova Expert"
    TALK_TO_NOVA_NAVIGATOR = "Talk to Nova Navigator"
    NOVA_EXPERT_READY_WHEN_YOU_ARE = "Nova Expert Ready When You Are"
    DEPOSIT_RECEIVED = "Deposit Received"
    ENGAGEMENT_ASSESSMENT_COMPLETED = "Engagement Assessment Completed"

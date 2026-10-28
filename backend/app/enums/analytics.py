"""AI agent related enums."""

from enum import Enum


class CompareFilterEnum(str, Enum):
    """Analytics compare filter types."""
    PERIOD = "period"
    QTD = "qtd"
    YTD = "ytd"
    CUSTOM = "custom"


class ComparePeriodEnum(str, Enum):
    """Rolling window length when ``compare=period`` (anchored to ``end_date``)."""
    DAYS_7 = "7d"
    DAYS_30 = "30d"
    DAYS_90 = "90d"


COMPARE_PERIOD_DAYS: dict[ComparePeriodEnum, int] = {
    ComparePeriodEnum.DAYS_7: 7,
    ComparePeriodEnum.DAYS_30: 30,
    ComparePeriodEnum.DAYS_90: 90,
}


class SourceEnum(str, Enum):
    """Analytics source types."""

    GOOGLE_ADS = "google_ads"
    ORGANIC_SEARCH = "organic_search"
    DIRECT = "direct"
    REFERRAL = "referral"
    PARTNER_ORG = "partner_org"
    SOCIAL = "social"
    EMAIL = "email"


class AnalyticsEvents(str, Enum):
    """Analytics events types."""

    SITE_VISIT = "site_visit"
    PAGE_VIEW = "page_view"
    EMAIL_CTA_CLICKED = "email_cta_clicked"
    RESOLVE_GET_STARTED = "resolve_get_started"
    WELCOME_SCREEN = "welcome_screen"
    RESOLVE_RELATIONSHIP_TYPE = "resolve_relationship_type"
    RESOLVE_LENGTH_OF_RELATIONSHIP = "resolve_length_of_relationship"
    RESOLVE_HOW_CAN_HELP = "resolve_how_can_help"
    RESOLVE_COURT_PROCEEDINGS = "resolve_court_proceedings"
    RESOLVE_FIRST_NAME = "resolve_first_name"
    RESOLVE_PARTNER_NAME = "resolve_partner_name"
    RESOLVE_RELATIONSHIP_COMMUNICATION = "resolve_relationship_communication"
    RESOLVE_DECISION_MAKING = "resolve_decision_making"
    RESOLVE_CONFLICT = "resolve_conflict"
    RESOLVE_CURRENT_COMMUNICATION = "resolve_current_communication"
    RESOLVE_FINANCIAL_CONTROL = "resolve_financial_control"
    RESOLVE_AFFORDABILITY = "resolve_affordability"
    RESOLVE_FINANCIAL_PICTURE = "resolve_financial_picture"
    RESOLVE_WARNING_SIGNS = "resolve_warning_signs"
    RESOLVE_COMFORTABLE_IN_SAME_ROOM = "resolve_comfortable_in_same_room"
    RESOLVE_CONFIDENCE = "resolve_confidence"
    RESOLVE_COMPLETED = "resolve_completed"
    ACCOUNT_CREATED = "account_created"
    CASE_OPENED = "case_opened"
    VIEW_MATCHING_EXPERTS = "view_matching_experts"
    CONNECT_WITH_EXPERT = "connect_with_expert"
    NEXT_STEPS_WITH_NOVA = "next_steps_with_nova"
    ALIGNMENT_CHECK_STARTED = "alignment_check_started"
    ALIGNMENT_CHECK_FULL_NAME = "alignment_check_full_name"
    ALIGNMENT_CHECK_PARTNER_FULL_NAME = "alignment_check_partner_full_name"
    ALIGNMENT_CHECK_GENDER = "alignment_check_gender"
    ALIGNMENT_CHECK_RELATIONSHIP_TYPE = "alignment_check_relationship_type"
    ALIGNMENT_CHECK_LENGTH_OF_RELATIONSHIP = "alignment_check_length_of_relationship"
    ALIGNMENT_CHECK_HELP_WITH = "alignment_check_help_with"
    ALIGNMENT_CHECK_ACCOMMODATION = "alignment_check_accommodation"
    ALIGNMENT_CHECK_POSTCODE = "alignment_check_postcode"
    ALIGNMENT_CHECK_PARTNER_INCOME = "alignment_check_partner_income"
    ALIGNMENT_CHECK_DR_PROCESS = "alignment_check_dr_process"
    ALIGNMENT_CHECK_SOLICITOR_ADVISING = "alignment_check_solicitor_advising"
    ALIGNMENT_CHECK_MEETING_PREFERENCE = "alignment_check_meeting_preference"
    ALIGNMENT_CHECK_DOMESTIC_ABUSE = "alignment_check_domestic_abuse"
    ALIGNMENT_CHECK_URGENCY = "alignment_check_urgency"
    ALIGNMENT_CHECK_ADDITIONAL_SUPPORT = "alignment_check_additional_support"
    ALIGNMENT_CHECK_WILLINGNESS_TO_PAY = "alignment_check_willingness_to_pay"
    ALIGNMENT_CHECK_PHONE_NUMBER = "alignment_check_phone_number"
    ALIGNMENT_CHECK_COMPLETED = "alignment_check_completed"
    HIGH_INTENT_BOOK_A_FREE_FIRST_CALL = "high_intent_book_a_free_first_call"
    HIGH_INTENT_FREE_CALL_SCHEDULED = "high_intent_free_call_scheduled"
    LOW_INTENT_BOOK_A_FREE_FIRST_CALL = "low_intent_book_a_free_first_call"
    LOW_INTENT_FREE_CALL_SCHEDULED = "low_intent_free_call_scheduled"
    HIGH_INTENT_WELCOME = "high_intent_welcome"
    HOW_CAN_WE_HELP = "how_can_we_help"
    IS_SOLICITOR_ADVISING = "is_solicitor_advising"
    ANNUAL_INCOME = "annual_income"
    NET_ASSET_VALUE = "net_asset_value"
    OUTCOME = "outcome"
    COMPLETE_HIGH_INTENT = "complete_high_intent"
    MATCH_CONFIRMED = "match_confirmed"
    PROFILE_CARD_SENT = "profile_card_sent"
    TALK_TO_LAWYER_REQUESTED = "talk_to_lawyer_requested"
    TALK_TO_NN_REQUESTED = "talk_to_nn_requested"
    EXPERT_ASSIGNED = "expert_assigned"
    ENGAGE_GET_STARTED = "engage_get_started"
    INITIAL_PAYMENT_COMPLETED = "initial_payment_completed"
    ONBOARDING_ASSESSMENT_STARTED = "onboarding_assessment_started"
    ONBOARDING_ASSESSMENT_COMPLETED = "onboarding_assessment_completed"


class EndToEndFunnelSteps(int, Enum):
    """End-to-end resolve funnel steps."""
    SITE_VISIT = 1
    RESOLVE_COMPLETED = 2
    CASE_OPENED = 3
    ALIGNMENT_CHECK_COMPLETED = 4
    MATCH_CONFIRMED = 5
    PROFILE_CARD_SENT = 6
    EXPERT_ASSIGNED = 7
    ENGAGE_GET_STARTED = 8


class EndToEndTriageFunnelSteps(int, Enum):
    """End-to-end triage funnel steps. Step 1 is stored as ``site_visit``."""
    SESSIONS = 1
    BOOK_A_FREE_FIRST_CALL = 2
    COMPLETE_HIGH_INTENT = 3
    ALIGNMENT_CHECK_COMPLETED = 4
    MATCH_CONFIRMED = 5
    PROFILE_CARD_SENT = 6
    EXPERT_ASSIGNED = 7
    ENGAGE_GET_STARTED = 8


class ResolveFunnelSteps(int, Enum):
    """Resolve steps enum."""
    SITE_VISIT = 1
    WELCOME_SCREEN = 2
    RESOLVE_RELATIONSHIP_TYPE = 3
    RESOLVE_LENGTH_OF_RELATIONSHIP = 4
    RESOLVE_HOW_CAN_HELP = 5
    RESOLVE_COURT_PROCEEDINGS = 6
    RESOLVE_FIRST_NAME = 7
    RESOLVE_PARTNER_NAME = 8
    RESOLVE_RELATIONSHIP_COMMUNICATION = 9
    RESOLVE_DECISION_MAKING = 10
    RESOLVE_CONFLICT = 11
    RESOLVE_CURRENT_COMMUNICATION = 12
    RESOLVE_FINANCIAL_CONTROL = 13
    RESOLVE_AFFORDABILITY = 14
    RESOLVE_FINANCIAL_PICTURE = 15
    RESOLVE_WARNING_SIGNS = 16
    RESOLVE_COMFORTABLE_IN_SAME_ROOM = 17
    RESOLVE_CONFIDENCE = 18
    RESOLVE_COMPLETED = 19


class AlignmentCheckFunnelSteps(int, Enum):
    """Alignment check journey steps (case-scoped strict funnel)."""
    ALIGNMENT_CHECK_STARTED = 1
    ALIGNMENT_CHECK_FULL_NAME = 2
    ALIGNMENT_CHECK_PARTNER_FULL_NAME = 3
    ALIGNMENT_CHECK_GENDER = 4
    ALIGNMENT_CHECK_RELATIONSHIP_TYPE = 5
    ALIGNMENT_CHECK_LENGTH_OF_RELATIONSHIP = 6
    ALIGNMENT_CHECK_HELP_WITH = 7
    ALIGNMENT_CHECK_ACCOMMODATION = 8
    ALIGNMENT_CHECK_POSTCODE = 9
    ALIGNMENT_CHECK_PARTNER_INCOME = 10
    ALIGNMENT_CHECK_DR_PROCESS = 11
    ALIGNMENT_CHECK_SOLICITOR_ADVISING = 12
    ALIGNMENT_CHECK_MEETING_PREFERENCE = 13
    ALIGNMENT_CHECK_DOMESTIC_ABUSE = 14
    ALIGNMENT_CHECK_URGENCY = 15
    ALIGNMENT_CHECK_ADDITIONAL_SUPPORT = 16
    ALIGNMENT_CHECK_WILLINGNESS_TO_PAY = 17
    ALIGNMENT_CHECK_COMPLETED = 18


class HighIntentFunnelSteps(int, Enum):
    """High intent journey steps (session-scoped strict funnel)."""
    BOOK_A_FREE_FIRST_CALL = 1
    FREE_CALL_SCHEDULED = 2
    HIGH_INTENT_WELCOME = 3
    HOW_CAN_WE_HELP = 4
    IS_SOLICITOR_ADVISING = 5
    ANNUAL_INCOME = 6
    NET_ASSET_VALUE = 7
    OUTCOME = 8
    COMPLETE_HIGH_INTENT = 9



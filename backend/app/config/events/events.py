"""
Centralized Event Configuration

This module defines how events are linked in the Nova Law AI event system.
Each event can trigger one or more subscriber events, forming a recursive chain.

Key Features:
- Simple mapping from one event to its subscriber events
- Recursive event flow support via dispatcher
- Enum-based for type safety and consistency
- Enables flexible event chain configuration without code changes

Author: Event-Driven Architecture Team
Version: 1.0.0
"""

from app.enums.events import EventType

# Defines which events should be triggered after a given event completes
EVENT_SUBSCRIPTIONS: dict[EventType, list[EventType]] = {
    EventType.PASSWORD_RESET_REQUESTED: [
        EventType.SEND_PASSWORD_RESET_EMAIL,
    ],
    EventType.RESOLVE_SUBMIT: [
        EventType.RESOLVE_CUS_CARD,
        EventType.RESOLVE_NN_CARD,
        EventType.RESOLVE_CUS_EMAIL,
        EventType.RESOLVE_NN_EMAIL,
    ],
    EventType.TRIAGE_SUBMIT: [
        EventType.ENGAGE_KYC_AUTO_FILL,
        EventType.TRIAGE_SUBMITTED_CUS_CARD,
        EventType.TRIAGE_SUBMITTED_NN_CARD,
        EventType.TRIAGE_CUS_EMAIL,
        EventType.TRIAGE_NN_EMAIL,
    ],
    EventType.TRIAGE_RE_SUBMIT: [
        EventType.TRIAGE_RE_SUBMIT_CUS_EMAIL,
        EventType.TRIAGE_RE_SUBMIT_NN_EMAIL,
    ],
    EventType.RESOLVE_RESUBMIT: [
        EventType.RESOLVE_CUS_EMAIL,
        EventType.RESOLVE_NN_EMAIL,
    ],
    EventType.CUSTOMER_REG_OPEN_CASE: [
        EventType.CUSTOMER_REG_CUS_EMAIL,
        # EventType.CUSTOMER_REG_NN_EMAIL,
        EventType.CASE_OPEN,
    ],
    EventType.CUSTOMER_SIMPLE_REGISTRATION: [
        EventType.CUSTOMER_REG_CUS_EMAIL,
        # EventType.CUSTOMER_REG_NN_EMAIL,
    ],
    EventType.CASE_OPEN: [
        # EventType.CASE_OPEN_CUS_CARD,
        EventType.CASE_PATHWAY_OVERVIEW_CUS_CARD,
        EventType.CASE_OPEN_NN_CARD,
        # EventType.CASE_OPEN_CUS_EMAIL,
        EventType.CASE_OPEN_NN_EMAIL,
        EventType.ENGAGE_KYC_AUTO_FILL,
    ],
    EventType.CUSTOMER_KYC_HOLD: [
        EventType.CUSTOMER_KYC_HOLD_NN_CARD,
        EventType.CUSTOMER_KYC_HOLD_CUS_CARD,
    ],
    EventType.CUSTOMER_KYC_SUBMIT: [
        # EventType.CUSTOMER_KYC_CUS_CARD,
        EventType.CUSTOMER_KYC_SUBMITTED_CUS_CARD,
        EventType.CUSTOMER_KYC_CUS_EMAIL,
        EventType.CASE_LAWYER_MATCHING,
    ],
    EventType.GENERATE_AI_CASE_SUMMARY: [
        EventType.CASE_SUMMARY_UPDATE,
    ],
    EventType.CASE_SUMMARY_UPDATE: [
        EventType.CASE_SUMMARY_UPDATE_NN_CARD,
    ],
    EventType.CASE_LAWYER_MATCHING: [
        EventType.CUSTOMER_KYC_NN_CARD,
        EventType.CUSTOMER_KYC_NN_EMAIL,
    ],
    EventType.CASE_LAWYER_MATCH_CONFIRMED: [
        # EventType.CASE_NEW_LAW_CARD,
        EventType.CASE_NEW_MATCH_LAW_CARD,
        EventType.CASE_NEW_NN_CARD,
        EventType.CASE_NEW_LAW_EMAIL,
        EventType.CASE_NEW_NN_EMAIL,
    ],
    EventType.CASE_INTEREST: [
        EventType.CASE_INTEREST_LAW_CARD,
        EventType.CASE_INTEREST_NN_CARD,
        EventType.CASE_INTEREST_LAW_EMAIL,
        EventType.CASE_INTEREST_NN_EMAIL,
    ],
    EventType.CASE_DECLINE: [
        EventType.CASE_DECLINE_LAW_CARD,
        EventType.CASE_DECLINE_NN_CARD,
        EventType.CASE_DECLINE_LAW_EMAIL,
        EventType.CASE_DECLINE_NN_EMAIL,
    ],
    EventType.CASE_MORE_DETAILS: [
        EventType.CASE_MORE_DETAILS_LAW_CARD,
        EventType.CASE_MORE_DETAILS_NN_CARD,
        EventType.CASE_MORE_DETAILS_LAW_EMAIL,
        EventType.CASE_MORE_DETAILS_NN_EMAIL,
    ],
    EventType.CASE_LAWYER_INTR_CONFIRMED: [
        EventType.CASE_PROFILE_CUS_CARD,
        EventType.CASE_PROFILE_NN_CARD,
        EventType.CASE_PROFILE_CUS_EMAIL,
        EventType.CASE_PROFILE_NN_EMAIL,
    ],
    EventType.CUSTOMER_ACCEPT_LAWYER: [
        EventType.CASE_AWARD_CUS_CARD,
        # EventType.CUSTOMER_PMT_REQUESTED, # remove payment flow - customer timeline
        EventType.CASE_AWARD_LAW_CARD,
        EventType.CASE_AWARD_NN_CARD,
        EventType.COMPLETE_ONBOARD_ASSESSMENT, # added engage complete card for customer
        EventType.CASE_AWARDED_TO_OTHER_LAW_CARD,
        EventType.CASE_AWARD_CUS_EMAIL,
        EventType.CASE_AWARD_LAW_EMAIL,
        EventType.CASE_AWARD_NN_EMAIL,
        EventType.CASE_AWARDED_TO_OTHER_LAW_EMAIL,
    ],
    EventType.CUSTOMER_PMT_REQUESTED: [
        EventType.CUSTOMER_PMT_REQUESTED_CUS_CARD,
    ],
    EventType.ENGAGE_SUBMIT: [
        EventType.CASE_ENGAGE_CUS_CARD,
        EventType.CASE_ENGAGE_LAW_CARD,
        EventType.CASE_ENGAGE_NN_CARD,
        EventType.CASE_ENGAGE_CUS_EMAIL,
        EventType.CASE_ENGAGE_LAW_EMAIL,
        EventType.CASE_ENGAGE_NN_EMAIL,
    ],
    EventType.CUSTOMER_PMT_COMPLETE: [
        EventType.CASE_RECEIPT_CUS_CARD,
        EventType.CASE_RECEIPT_LAW_CARD,
        EventType.CASE_RECEIPT_NN_CARD,
        EventType.CASE_RECEIPT_CUS_EMAIL,
        EventType.CASE_RECEIPT_LAW_EMAIL,
        EventType.CASE_RECEIPT_NN_EMAIL,
    ],
    EventType.COMPLETE_ONBOARD_ASSESSMENT: [    #customer onboard request card main event
        EventType.COMPLETE_ONBOARD_ASSESSMENT_CUS_CARD,
        # EventType.COMPLETE_ONBOARD_ASSESSMENT_LAW_CARD, # skipped lawyer card
        # EventType.COMPLETE_ONBOARD_ASSESSMENT_NN_CARD, # skipped nn card
        # EventType.COMPLETE_ONBOARD_ASSESSMENT_CUS_EMAIL,
    ],
    EventType.CUSTOMER_TALK_CUS_NN: [
        EventType.CUSTOMER_TALK_TO_NN_CUS_CARD,
        EventType.CUSTOMER_TALK_TO_NN_NN_CARD,
        EventType.CUSTOMER_TALK_TO_NN_CUS_EMAIL,
        EventType.CUSTOMER_TALK_TO_NN_NN_EMAIL
    ],
    EventType.CUSTOMER_TALK_CUS_LAW: [
        EventType.CUSTOMER_TALK_TO_LAW_CUS_CARD,
        EventType.CUSTOMER_TALK_TO_LAW_NN_CARD,
        EventType.CUSTOMER_TALK_TO_LAW_CUS_EMAIL,
        EventType.CUSTOMER_TALK_TO_LAW_NN_EMAIL,
    ],
    EventType.INITIAL_PASSWORD_LINK_SENT: [
    ],
    EventType.RESEND_INITIAL_PASSWORD_EMAIL_AFTER_EXPIRY: [
    ],
    EventType.ARCHIVE_CASE: [
        EventType.CASE_ARCHIVED_NN_CARD,
    ],
    EventType.UNARCHIVE_CASE: [
        EventType.CASE_UNARCHIVED_NN_CARD,
    ],
    EventType.CREATE_LEGAL_EXPERT: [
        EventType.LEGAL_EXPERT_SIGNUP_NN_EMAIL,
        EventType.LEGAL_EXPERT_SIGNUP_EXPERT_EMAIL,
    ],
    EventType.AI_SUMMARY_FAILED_NN_EMAIL: [
    ],
    EventType.EXPERT_NOT_INTERESTED: [
        EventType.EXPERT_NOT_INTERESTED_NN_CARD,
        EventType.EXPERT_NOT_INTERESTED_NN_EMAIL,
    ],
    EventType.EMAIL_CTA_CLICKED: [
    ],
    EventType.DELETE_ANALYTICS_DATA: [
    ],
    EventType.BOOK_FREE_CALL: [
        EventType.BOOK_FREE_CALL_CUS_CARD,
        EventType.BOOK_FREE_CALL_NN_CARD,
    ],
    EventType.BOOK_FREE_CALL_POST_RESOLVE_NN_EMAIL: [
    ],
    EventType.BOOK_FREE_CALL_HIGH_INTENT_NN_EMAIL: [
    ],
}


def get_subscribers_for_event(event_type: EventType | str) -> list[EventType]:
    """
    Return all subscriber events that are triggered by the given event.

    Supports both EventType enums and strings for flexibility in recursive dispatching.

    Args:
        event_type (EventType | str): The event to get subscribers for

    Returns:
        List[EventType]: Events that should be triggered next
    """
    if isinstance(event_type, str):
        try:
            event_type = EventType(event_type)
        except ValueError:
            return []

    return EVENT_SUBSCRIPTIONS.get(event_type, [])


def get_events_for_subscriber(subscriber_event: EventType) -> list[EventType]:
    """
    Return all events that trigger the given subscriber event.

    This is useful for introspection or reverse dependency mapping.

    Args:
        subscriber_event (EventType): The subscriber to look up

    Returns:
        List[EventType]: Events that lead to this subscriber
    """
    return [
        event
        for event, subscribers in EVENT_SUBSCRIPTIONS.items()
        if subscriber_event in subscribers
    ]


def get_all_business_events() -> list[EventType]:
    """
    Return all configured events that have subscribers.

    These represent the entry points or triggers in the event chain.

    Returns:
        List[EventType]: Events that initiate chains
    """
    return list(EVENT_SUBSCRIPTIONS.keys())


def get_all_subscriber_events() -> list[EventType]:
    """
    Return all events that are used as subscribers in any chain.

    These represent all intermediate or terminal steps.

    Returns:
        List[EventType]: Events triggered by other events
    """
    subscribers = set()
    for sub_list in EVENT_SUBSCRIPTIONS.values():
        subscribers.update(sub_list)
    return sorted(subscribers, key=lambda x: x.value)


def validate_event_configuration() -> bool:
    """
    Check that every configured event has at least one subscriber.

    Warns if any event is configured but doesn't trigger anything else.

    Returns:
        bool: True if all events have subscribers, False if any are orphaned
    """
    valid = True
    for event_type, subscribers in EVENT_SUBSCRIPTIONS.items():
        if not subscribers:
            print(f"⚠️ Warning: Event {event_type.value} has no subscribers configured.")
            valid = False
    return valid

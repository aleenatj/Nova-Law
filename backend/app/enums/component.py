"""
Component Enums for Event-Driven Architecture
"""

from enum import Enum

import logging

logger = logging.getLogger(__name__)

class ComponentEnum(str, Enum):
    """
    Enum representing component types in the Nova Law AI application.
    """
    RESOLVE_CUS_CARD = "resolve_cus_card" # TODO: remove this
    RESOLVE_NN_CARD = "resolve_nn_card" # TODO: remove this
    CASE_OPEN_CUS_CARD = "case_opened"
    CASE_OPEN_NN_CARD = "case_opened"
    CUSTOMER_KYC_CUS_CARD = "kyc_submitted"
    CUSTOMER_KYC_SUBMITTED_CUS_CARD = "customer_kyc_submitted"
    CUSTOMER_KYC_NN_CARD = "kyc_completed"
    CASE_NEW_NN_CARD = "match_notification_send"
    CASE_NEW_LAW_CARD = "match_found" #deprecated
    CASE_NEW_MATCH_LAW_CARD = "new_match"
    CASE_INTEREST_NN_CARD = "interest_received"
    CASE_INTEREST_LAW_CARD = "interest_raised"
    CASE_DECLINE_NN_CARD = "lawyer_declined_case"
    CASE_DECLINE_LAW_CARD = "case_declined"
    CASE_MORE_DETAILS_NN_CARD = "lawyer_need_more_details"
    CASE_MORE_DETAILS_LAW_CARD = "more_details_requested"
    CASE_PROFILE_NN_CARD = "profile_card_send"
    CASE_PROFILE_CUS_CARD = "your_matched_expert"
    CASE_AWARD_NN_CARD = "case_awarded"
    CASE_AWARD_LAW_CARD = "case_awarded"
    CASE_AWARD_CUS_CARD = "customer_engaged_lawyer"
    CASE_ENGAGE_NN_CARD = "client_onboarding_completed"
    CASE_ENGAGE_LAW_CARD = "client_onboarding_completed"
    CASE_ENGAGE_CUS_CARD = "onboarding_assessment_completed"
    CASE_RECEIPT_NN_CARD = "payment_completed"
    CASE_RECEIPT_LAW_CARD = "payment_completed"
    CASE_RECEIPT_CUS_CARD = "payment_receipt"
    CUSTOMER_TALK_TO_LAW_NN_CARD = "customer_talk_to_lawyer_requested"
    CUSTOMER_TALK_TO_NN_NN_CARD = "customer_talk_to_nn_requested"
    CUSTOMER_TALK_TO_LAW_CUS_CARD = "talk_to_lawyer_requested"
    CUSTOMER_TALK_TO_NN_CUS_CARD = "talk_to_nn_requested"
    COMPLETE_ONBOARD_ASSESSMENT_CUS_CARD = "complete_onboarding_assessment"
    CUSTOMER_PMT_REQUESTED_CUS_CARD = "initial_payment_requested"
    COMPLETE_ONBOARD_ASSESSMENT_NN_CARD = "complete_onboarding_assessment"
    COMPLETE_ONBOARD_ASSESSMENT_LAW_CARD = "complete_onboarding_assessment"
    CASE_AWARDED_TO_OTHER_LAW_CARD = "case_awarded_to_other_lawyer"
    CASE_SUMMARY_UPDATE_NN_CARD = "case_summary_update"
    CASE_ARCHIVED_NN_CARD = "case_archived"
    CASE_UNARCHIVED_NN_CARD = "case_unarchived"
    CASE_PATHWAY_OVERVIEW_CUS_CARD = "case_pathway_overview"
    EXPERT_NOT_INTERESTED_NN_CARD = "expert_not_interested"
    EMAIL_CTA_CLICKED = "email_cta_clicked"
    CUSTOMER_KYC_HOLD_NN_CARD = "customer_kyc_hold"
    CUSTOMER_KYC_HOLD_CUS_CARD = "customer_kyc_hold"
    BOOK_FREE_CALL_CUS_CARD = "book_free_call"
    BOOK_FREE_CALL_NN_CARD = "book_free_call"
    TRIAGE_SUBMITTED_CUS_CARD = "triage_submitted"
    TRIAGE_SUBMITTED_NN_CARD = "triage_submitted"
    @classmethod
    def get_component_message(cls, component: str, role: str) -> str:
        """
        Get a human-readable message for a given component and role.

        Args:
            component: The component value (e.g., "case_opened").
            role: The role code (e.g., "Customer", "Navigator", "Lawyer").

        Returns:
            str: The message template for the component and role, or an error message
                 if the component or role is not found.
        """
        component_messages: dict[str, dict[str, str]] = {
            # Case management events
            "case_opened": {
                "Customer": "Your case has been opened and is being reviewed.",
                "Navigator": "A new case {case_number} has been opened.",
            },
            "case_awarded": {
                # "Navigator": "Case {case_number} has been awarded to {lawyer_name}.",
                "Navigator": " ",
                "Lawyer": "You’ve been selected to support {customer_name}. Case - {case_number}.",
                "Customer": "Your case has been assigned to {lawyer_name}.",
            },
            "customer_engaged_lawyer": {
                "Customer": "You have successfully engaged with {lawyer_name} for case {case_number}.",
            },
            # Case pathway overview events
            "case_pathway_overview": {
                "Customer": "Your case pathway overview for your case.",
            },
            
            # KYC process events
            "kyc_submitted": {
                "Customer": "Your Nova Expert Alignment Check is now under review.",
            },
            "customer_kyc_submitted": {
                "Customer": "Your Nova Expert Alignment Check is now under review.",
            },
            "kyc_completed": {
                # "Navigator": "KYC verification completed for case {case_number}.",
                "Navigator": "Alignment Check submitted for {customer_name}. Case - {case_number}.",
            },
            
            # Matching and notification events
            "match_notification_send": {
                # "Navigator": "Match notifications sent for case {case_number}.",
                "Navigator": "Expert matching completed for {customer_name}. Case - {case_number}.",
            },
            "match_found": {
                # "Lawyer": "A new case {case_number} matching your expertise has been found.",
                "Lawyer": "A new case has been shared with you. Case - {case_number}.",
            },
            "new_match": {
                # "Lawyer": "A new case {case_number} matching your expertise has been found.",
                "Lawyer": "A new case has been shared with you. Case - {case_number}.",
            },
            "interest_received": {
                # "Navigator": "Interest received from {lawyer_name} for case {case_number}.",
                "Navigator": "Interest received from {lawyer_name}. Case - {case_number}.",
            },
            "interest_raised": {
                # "Lawyer": "You have expressed interest in case {case_number}.",
                "Lawyer": "Your interest has been recorded. Case - {case_number}.",
            },
            "lawyer_declined_case": {
                # "Navigator": "{lawyer_name} has declined case {case_number}.",
                "Navigator": "{lawyer_name} has declined to support {customer_name}. Case - {case_number}.",
            },
            "case_declined": {
                # "Lawyer": "You have declined case {case_number}.",
                "Lawyer": "Your response has been noted. Case - {case_number}.",
            },
            "lawyer_need_more_details": {
                "Navigator": "{lawyer_name} needs more details for case {case_number}.",
            },
            "more_details_requested": {
                "Lawyer": "You have requested more details for case {case_number}.",
            },
            "profile_card_send": {
                "Navigator": "Profile card sent for case {case_number}.",
            },
            "your_matched_expert": {
                # "Customer": "Your matched experts are ready to help with case {case_number}.",
                "Customer": "Your matched experts are ready.",
            },
            
            # Communication events
            "customer_talk_to_lawyer_requested": {
                # "Navigator": "Customer {customer_name} has requested to talk to lawyer for case {case_number}.",
                "Navigator": "{customer_name} has requested to speak with {lawyer_name}. Case - {case_number}.",
            },
            "customer_talk_to_nn_requested": {
                # "Navigator": "Customer {customer_name} has requested to talk to Nova Navigator for case {case_number}.",
                "Navigator": "{customer_name} has requested a conversation. Case - {case_number}.",
            },
            "talk_to_lawyer_requested": {
                "Customer": "You have requested to talk to your expert.",
            },
            "talk_to_nn_requested": {
                "Customer": "You have requested to talk to Nova Navigator.",
            },
            
            # Onboarding events
            "client_onboarding_completed": {
                # "Navigator": "Client onboarding completed for case {case_number}.",
                "Navigator": "Nova Engage completed for {customer_name}. Case - {case_number}.",
                # "Lawyer": "Client onboarding completed for case {case_number}.",
                "Lawyer": "{customer_name} - Engage complete. Case - {case_number}.",
            },
            "onboarding_assessment_completed": {
                # "Customer": "Your onboarding assessment has been completed for case {case_number}.",
                "Customer": "Thank you for completing Nova Engage. {lawyer_name} will be in touch shortly.",
            },
            "complete_onboarding_assessment": {
                "Customer": "Please complete your onboarding assessment.",
                "Lawyer": "Customer has initiated the onboarding assessment for case {case_number}. Please review and mark it as completed.",
                "Navigator": "Customer has initiated the onboarding assessment for case {case_number}. Please review and mark it as completed.",
            },
            
            # Payment events
            "payment_completed": {
                # "Navigator": "Payment completed for case {case_number}.",
                "Navigator": "Payment received for {customer_name}. Case - {case_number}.",
                # "Lawyer": "Payment received for case {case_number}.",
                "Lawyer": "Payment has been received. Case - {case_number}.",
            },
            "payment_receipt": {
                # "Customer": "Payment receipt generated for case {case_number}.",
                "Customer": "Thank you for your payment. You can now start Nova Engage when you are ready.",
            },
            "initial_payment_requested": {
                # "Customer": "Initial payment has been requested for case {case_number}.",
                "Customer": "You can make a payment now to book your Nova Initial Consultation.",
            },
            "case_summary_update": {
                # "Navigator": "Case summary has been updated for case {case_number}.",
                "Navigator": " ",
            },
            # Case archived events
            "case_archived": {
                "Navigator": "Case {case_number} have been archived.",
            },
            "case_unarchived": {
                "Navigator": "Case {case_number} have been unarchived.",
            },
            # Case awarded to other lawyer events
            "case_awarded_to_other_lawyer": {
                "Lawyer": "Case {case_number} has been awarded to another expert.",
            },
            "expert_not_interested": {
                "Navigator": "{expert_names} {has_have} not expressed interest to support {customer_name} within {deadline_hours} hours. Case - {case_number}.",
            },
            "email_cta_clicked": {
                "Navigator": "Email CTA clicked by {customer_name}. Case - {case_number}.",
            },
            "customer_kyc_hold": {
                "Customer": "Your Nova Expert Alignment Check is now under review.",
                "Navigator": "Alignment Check held for {customer_name}. Case - {case_number}.",
            },
            "book_free_call": {
                "Customer": "Your call has been booked.",
                "Navigator": "Customer has scheduled a free call with you. Case - {case_number}.",
            },
            "triage_submitted": {
                "Customer": "Your triage has been submitted.",
                "Navigator": "Triage submitted for {customer_name}. Case - {case_number}.",
            },
        }
        
        messages = component_messages.get(component)
        if not messages:
            logger.error(f"No messages found for component '{component}'")
            return f"No messages found for component '{component}'"
        message = messages.get(role)
        if not message:
            logger.error(f"No message found for role '{role}' in component '{component}'")
            return f"No message found for role '{role}' in component '{component}'"
        return message.strip()

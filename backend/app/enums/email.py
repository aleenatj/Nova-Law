"""Email template enums for the Nova Law AI application."""

from enum import Enum
from typing import Any

# Subject templates for each email type
EMAIL_SUBJECTS = {
    "password_reset": "Password Reset for {{ username }}",
    "initial_password_setup": "Set Your Password - Welcome to Nova",
    "resend_initial_password_setup": "Reminder: Set Your Password - Nova",
    "kyc_submission_customer_notification": "Your Nova Expert Alignment Check",
    "kyc_submission_navigator_notification": " Nova Expert Alignment Check Submitted for Review {{case_number}}",
    "case_new_navigator_notification": "Nova Expert Matching Completed {{case_number}}",
    "case_new_lawyer_notification": "New Case Shared with You in Nova - {{case_number}}",
    "resolve_customer_notification": " Your Personalised Recommendation",
    "resolve_navigator_notification": "Pathway Recommendation Completed",
    "customer_registration_customer_notification": "Welcome to Nova",
    "customer_registration_navigator_notification": "Customer Registered Successfully - {{ customer_name }}",
    "triage_customer_notification": "Welcome to Nova",
    "triage_navigator_notification": "Triage Case Opened - {{ case_number }}",
    "triage_resubmit_customer_notification": "Your Triage Details Have Been Updated",
    "triage_resubmit_navigator_notification": "Triage Details Updated - {{ case_number }}",
    "customer_simple_registration_cus_email": "Sign in to Nova",
    "send_login_link_email": "Your sign-in Link for Nova",
    "case_open_customer_notification": "Case {{ case_number }} Opened - {{ customer_name }}",
    "case_open_navigator_notification": "Case Opened - {{ case_number }}",
    "case_interest_lawyer_notification": "Interest recorded - Case {{ case_number }}",
    "case_interest_navigator_notification": "Nova Expert Interest Received {{case_number}}",
    "case_decline_lawyer_notification": "Decline recorded – Case {{ case_number }}",
    "case_decline_navigator_notification": "Nova Expert Declined {{case_number}}",
    "case_profile_navigator_notification": "Nova Expert Profiles Shared with Customer - {{case_number}}",
    "case_profile_customer_notification": "Your Matching Nova Experts Are Ready to View",
    "case_award_lawyer_notification": "You’ve Been Selected to Support a Case - {{ case_number }}",
    "case_awarded_to_other_law_email": "Update on case {{ case_number }}",
    "case_award_navigator_notification": "Nova Expert Selected by Customer - {{ case_number }}",
    "case_award_customer_notification": "Your Chosen Nova Expert is {{ lawyer_name }}",
    "case_engage_lawyer_notification": "Client Onboarding Completed - {{ case_number }}",
    "case_engage_navigator_notification": "Nova Engage Completed - {{ case_number }}",
    "case_engage_customer_notification": "Nova Engage is Complete",
    "case_receipt_customer_notification": "Payment Receipt - {{ case_number }}",
    "case_receipt_navigator_notification": "Payment Received - {{ case_number }}",
    "case_receipt_lawyer_notification": "Payment Received - {{ case_number }}",
    "case_more_details_navigator_notification": "Case More Details Request - {{ case_number }} - {{ lawyer_name }}",
    "case_more_details_lawyer_notification": "Case More Details Request - {{ case_number }}",
    "customer_talk_to_nn_customer_notification": "We’ll Be in Touch to Arrange a Conversation",
    "customer_talk_to_nn_navigator_notification": "Customer Requested a Conversation - {{case_number}}",
    "customer_talk_to_law_customer_notification": "We’ll Arrange a Conversation with Your Chosen Nova Expert",
    "customer_talk_to_law_navigator_notification": "Customer Requested a Conversation with a Nova Expert- {{ case_number }}",
    "complete_onboard_assessment_customer_notification": "Prepare for Your Nova Initial Consultation in Nova",
    # "complete_onboard_assessment_customer_notification": "Complete Your Onboarding Assessment - {{ customer_name }}",
    "legal_expert_signup_navigator_notification": "B2C Legal Expert Sign Up - {{ lawyer_name }}",
    "legal_expert_signup_expert_notification": "Legal Expert Sign Up",
    "ai_summary_failed_navigator_notification": "AI Summary Generation Failed - {{ case_number }}",
    "expert_not_interested_navigator_notification": "Nova Expert Not Interested {{case_number}}",
    "contact_us_notification": "New Contact Us Request Received - {{ first_name }} {{ last_name }}",
    "book_free_call_post_resolve_navigator_notification": "Nova Navigator call scheduled - {{ case_number }} - {{call_date}}",
    "book_free_call_high_intent_navigator_notification": "Nova Navigator call scheduled - {{ call_date }}",
    # Add more subjects here as needed:
    # "welcome": "Welcome {{ username }} to {{ team_name }}",
    # "case_update": "Case Update: {{ case_id }} - {{ case_title }}",
    # "document_ready": "Document Ready: {{ document_name }} for {{ case_id }}",
}


class EmailTemplate(str, Enum):
    """Available email templates in the system."""

    # User management templates
    PASSWORD_RESET = "password_reset"
    INITIAL_PASSWORD_SETUP = "initial_password_setup"
    RESEND_INITIAL_PASSWORD_SETUP = "resend_initial_password_setup"
    CUSTOMER_REGISTRATION_CUSTOMER_NOTIFICATION = "customer_registration_customer_notification"
    CUSTOMER_REGISTRATION_NAVIGATOR_NOTIFICATION = "customer_registration_navigator_notification"
    CUSTOMER_SIMPLE_REGISTRATION_CUS_EMAIL = "customer_simple_registration_cus_email"
    SEND_LOGIN_LINK_EMAIL = "send_login_link_email"
    TRIAGE_CUSTOMER_NOTIFICATION = "triage_customer_notification"
    TRIAGE_NAVIGATOR_NOTIFICATION = "triage_navigator_notification"
    TRIAGE_RESUBMIT_CUSTOMER_NOTIFICATION = "triage_resubmit_customer_notification"
    TRIAGE_RESUBMIT_NAVIGATOR_NOTIFICATION = "triage_resubmit_navigator_notification"
    BOOK_FREE_CALL_POST_RESOLVE_NAVIGATOR_NOTIFICATION = "book_free_call_post_resolve_navigator_notification"
    BOOK_FREE_CALL_HIGH_INTENT_NAVIGATOR_NOTIFICATION = "book_free_call_high_intent_navigator_notification"

    # KYC templates
    KYC_SUBMISSION_CUSTOMER_NOTIFICATION = "kyc_submission_customer_notification"
    KYC_SUBMISSION_NAVIGATOR_NOTIFICATION = "kyc_submission_navigator_notification"

    # Case management templates
    CASE_NEW_NAVIGATOR_NOTIFICATION = "case_new_navigator_notification"
    CASE_NEW_LAWYER_NOTIFICATION = "case_new_lawyer_notification"
    CASE_OPEN_CUSTOMER_NOTIFICATION = "case_open_customer_notification"
    CASE_OPEN_NAVIGATOR_NOTIFICATION = "case_open_navigator_notification"
    CASE_INTEREST_LAWYER_NOTIFICATION = "case_interest_lawyer_notification"
    CASE_INTEREST_NAVIGATOR_NOTIFICATION = "case_interest_navigator_notification"
    CASE_DECLINE_LAWYER_NOTIFICATION = "case_decline_lawyer_notification"
    CASE_DECLINE_NAVIGATOR_NOTIFICATION = "case_decline_navigator_notification"
    CASE_PROFILE_NAVIGATOR_NOTIFICATION = "case_profile_navigator_notification"
    CASE_PROFILE_CUSTOMER_NOTIFICATION = "case_profile_customer_notification"
    CASE_AWARD_LAWYER_NOTIFICATION = "case_award_lawyer_notification"
    CASE_AWARDED_TO_OTHER_LAW_EMAIL = "case_awarded_to_other_law_email"
    CASE_AWARD_NAVIGATOR_NOTIFICATION = "case_award_navigator_notification"
    CASE_AWARD_CUSTOMER_NOTIFICATION = "case_award_customer_notification"
    CASE_ENGAGE_LAWYER_NOTIFICATION = "case_engage_lawyer_notification"
    CASE_ENGAGE_NAVIGATOR_NOTIFICATION = "case_engage_navigator_notification"
    CASE_ENGAGE_CUSTOMER_NOTIFICATION = "case_engage_customer_notification"
    CASE_RECEIPT_CUSTOMER_NOTIFICATION = "case_receipt_customer_notification"
    CASE_RECEIPT_NAVIGATOR_NOTIFICATION = "case_receipt_navigator_notification"
    CASE_RECEIPT_LAWYER_NOTIFICATION = "case_receipt_lawyer_notification"
    CASE_MORE_DETAILS_NAVIGATOR_NOTIFICATION = "case_more_details_navigator_notification"
    CASE_MORE_DETAILS_LAWYER_NOTIFICATION = "case_more_details_lawyer_notification"
    CUSTOMER_TALK_TO_NN_CUSTOMER_NOTIFICATION = "customer_talk_to_nn_customer_notification"
    CUSTOMER_TALK_TO_NN_NAVIGATOR_NOTIFICATION = "customer_talk_to_nn_navigator_notification"
    CUSTOMER_TALK_TO_LAW_CUSTOMER_NOTIFICATION = "customer_talk_to_law_customer_notification"
    CUSTOMER_TALK_TO_LAW_NAVIGATOR_NOTIFICATION = "customer_talk_to_law_navigator_notification"
    AI_SUMMARY_FAILED_NAVIGATOR_NOTIFICATION = "ai_summary_failed_navigator_notification"
    EXPERT_NOT_INTERESTED_NAVIGATOR_NOTIFICATION = "expert_not_interested_navigator_notification"

    # Resolve templates
    RESOLVE_CUSTOMER_NOTIFICATION = "resolve_customer_notification"
    RESOLVE_NAVIGATOR_NOTIFICATION = "resolve_navigator_notification"

    # Onboarding assessment templates
    COMPLETE_ONBOARD_ASSESSMENT_CUSTOMER_NOTIFICATION = "complete_onboard_assessment_customer_notification"

    # Lawyer onboarding templates
    LEGAL_EXPERT_SIGNUP_NAVIGATOR_NOTIFICATION = "legal_expert_signup_navigator_notification"
    LEGAL_EXPERT_SIGNUP_EXPERT_NOTIFICATION = "legal_expert_signup_expert_notification"

    # Contact us templates
    CONTACT_US_NOTIFICATION = "contact_us_notification"

    # Engage support templates
    ENGAGE_SUPPORT_EMAIL = "engage_support_email"

    @classmethod
    def get_template_path(cls, template: "EmailTemplate") -> str:
        """Get the template file path for a given template."""
        return f"html/{template.value}.html"

    @classmethod
    def get_subject(
        cls, template: "EmailTemplate", context: dict[str, Any] | None = None
    ) -> str:
        """
        Get the email subject for a given template with context variables.

        Args:
            template: EmailTemplate enum value
            context: Template context variables for subject rendering

        Returns:
            Formatted email subject string
        """
        subject_template = EMAIL_SUBJECTS.get(template.value, "Email from Nova")

        # If no context provided, return the raw template
        if context is None or not context:
            return subject_template

        # Simple template rendering for subject
        try:
            from jinja2 import Template

            template_obj = Template(subject_template)
            return template_obj.render(**context)
        except Exception:
            # Fallback to template string if rendering fails
            return subject_template

    @classmethod
    def list_templates(cls) -> list[str]:
        """Get a list of all available template names."""
        return [template.value for template in cls]

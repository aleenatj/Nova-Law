"""create components type'


Revision ID: bc7efd6d5b6f
Revises: fb71818427d0
Create Date: 2025-09-15 17:26:16.122973

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc7efd6d5b6f'
down_revision = 'fb71818427d0'
branch_labels = None
depends_on = None

def upgrade() -> None:
    """Insert timeline component types into the timeline_type table.
    
    This migration populates the timeline_type table with various component types
    for different user roles (Customer, Navigator, Lawyer). Each component type
    represents a specific event or action in the customer journey timeline.
    
    The inserted component types include:
    - Case management events (case_opened, case_awarded, etc.)
    - KYC process events (kyc_submitted, kyc_completed)
    - Matching and notification events (match_found, interest_received, etc.)
    - Communication events (talk_to_lawyer_requested, etc.)
    - Payment events (payment_completed, payment_receipt)
    - Onboarding events (client_onboarding_completed, etc.)
    """
    insert_statements = [
        # ("resolve_cus_card", 1, "Customer"),
        # ("resolve_nn_card", 1, "Navigator"),
        ("case_opened", 1, "Customer"),
        ("case_opened", 1, "Navigator"),
        ("kyc_submitted", 1, "Customer"),
        ("kyc_completed", 1, "Navigator"),
        ("match_notification_send", 1, "Navigator"),
        ("match_found", 1, "Lawyer"),
        ("interest_received", 1, "Navigator"),
        ("interest_raised", 1, "Lawyer"),
        ("lawyer_declined_case", 1, "Navigator"),
        ("case_declined", 1, "Lawyer"),
        ("lawyer_need_more_details", 1, "Navigator"),
        ("more_details_requested", 1, "Lawyer"),
        ("profile_card_send", 1, "Navigator"),
        ("your_matched_expert", 1, "Customer"),
        ("case_awarded", 1, "Navigator"),
        ("case_awarded", 1, "Lawyer"),
        ("customer_engaged_lawyer", 1, "Customer"),
        ("client_onboarding_completed", 1, "Navigator"),
        ("client_onboarding_completed", 1, "Lawyer"),
        ("onboarding_assessment_completed", 1, "Customer"),
        ("payment_completed", 1, "Navigator"),
        ("payment_completed", 1, "Lawyer"),
        ("payment_receipt", 1, "Customer"),
        ("customer_talk_to_lawyer_requested", 1, "Navigator"),
        ("customer_talk_to_nn_requested", 1, "Navigator"),
        ("talk_to_lawyer_requested", 1, "Customer"),
        ("talk_to_nn_requested", 1, "Customer"),
        ("complete_onboarding_assessment", 1, "Customer"),
        ("initial_payment_requested", 1, "Customer"),
        ("complete_onboarding_assessment", 1, "Navigator"),
        ("complete_onboarding_assessment", 1, "Lawyer"),
    ]

    for type_name, version, role_code in insert_statements:
        op.execute(
            sa.text(
                "INSERT INTO timeline_type (type_name, version, role_code) "
                "VALUES (:type_name, :version, :role_code)"
            ).bindparams(
                type_name=type_name, 
                version=version, 
                role_code=role_code,
            )
        )


def downgrade() -> None:
    """Remove timeline component types from the timeline_type table.
    
    This migration reversal removes all the timeline component types that were
    inserted by the upgrade function. This includes all component types for
    Customer, Navigator, and Lawyer roles that were added in this migration.
    """
    op.execute(
            "DELETE FROM timeline_type WHERE type_name IN ('resolve_cus_card', 'resolve_nn_card', 'case_opened', 'kyc_submitted', 'kyc_completed', 'match_notification_send', 'match_found', 'interest_received', 'interest_raised', 'lawyer_declined_case', 'case_declined', 'lawyer_need_more_details', 'more_details_requested', 'profile_card_send', 'your_matched_expert', 'case_awarded', 'customer_engaged_lawyer', 'client_onboarding_completed', 'onboarding_assessment_completed', 'payment_completed', 'payment_completed', 'payment_receipt', 'customer_talk_to_lawyer_requested', 'customer_talk_to_nn_requested', 'talk_to_lawyer_requested', 'talk_to_nn_requested', 'complete_onboarding_assessment', 'customer_init_pmt_requested')"
    )

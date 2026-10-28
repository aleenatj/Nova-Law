import json

import typing as Any
from fastapi import HTTPException, status
from sqlalchemy import and_, func
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.db.models import (
    Case,
    CaseCustomer,
    CaseEngage,
    CaseLawyer,
    CaseResolve,
    Customer,
    Engage,
    EngageQuestionAnswers,
    Lawyer,
    LawyerDRPreference,
    LawyerExpertType,
    Match,
    QuestionAnswers,
    Resolve,
    ResolveQuestionAnswers,
    TimelineEvent,
    TimelineType,
    User,
    UserRole,
    Triage,
    CaseTriage,
)
from app.enums.case import CaseStatusEnum, CaseTypeEnum
from app.enums.events import EventType
from app.enums.lawyer import DRPreferenceEnum, ExpertTypeEnum, LawyerStatusEnum
from app.enums.user import StatusEnum
from app.enums.user_role import UserRoleEnum
from app.enums._lambda import LambdaFunctionName
from app.schemas.v1.timeline_event import MatchedLawyer
from app.utils.encryption import encrypt_id


def validate_answer_text(answer_text: str | None, required: bool, min_length: int, max_length: int) -> tuple[bool, str | None]:
    """
    Validate resolve/kyc answer text based on required flag and length constraints.

    Args:
        answer_text: The answer text to validate
        required: Boolean indicating if the answer is required

    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if validation passes, False otherwise
        - error_message: None if valid, error message string if invalid

    Validation rules:
        - If required is True:
            * Answer must not be None or empty
            * Answer must meet minimum length requirement (min_length)
            * Answer must not exceed maximum length (max_length)
        - If required is False:
            * If answer is None or empty, validation passes
            * If answer is provided, it must not exceed maximum length (MAX_ANSWER_LENGTH)
    """
    # Handle required validation
    if required:
        # Check if answer is None or empty
        if answer_text is None or not answer_text.strip():
            return False, "Answer is required and cannot be empty"
        
        # Check minimum length
        if len(answer_text.strip()) < min_length:
            return False, f"Answer must be at least {min_length} character(s)"
        
        # Check maximum length
        if len(answer_text) > max_length:
            return False, f"Answer exceeds maximum length of {max_length} characters"
        
        return True, None
    
    # Handle optional validation (required is False)
    else:
        # If answer is None or empty, it's valid since it's optional
        if answer_text is None or not answer_text.strip():
            return True, None
        
        # If answer is provided, check only maximum length
        if len(answer_text) > max_length:
            return False, f"Answer exceeds maximum length of {max_length} characters"
        
        return True, None


def get_lawyer_by_user_id(db: Session, user_id: int) -> Lawyer | None:
    """
    Get active lawyer by user ID.

    Args:
        db: Database session
        user_id: ID of the user

    Returns:
        Lawyer object if found and active, None otherwise
    """
    return (
        db.query(Lawyer)
        .filter(Lawyer.user_id == user_id, Lawyer.status == StatusEnum.ACTIVE)
        .first()
    )


def get_all_navigator_emails(db: Session) -> list[dict]:
    """Get the navigator email from the database."""
    navigators = db.query(User).join(UserRole, User.id == UserRole.user_id).filter(UserRole.role_id == int(UserRoleEnum.NAVIGATOR.id), User.status == StatusEnum.ACTIVE).all()
    return [{
        "navigator_email": navigator.email,
        "navigator_name": (navigator.first_name if navigator.first_name is not None else "") + " " + (navigator.last_name if navigator.last_name is not None else "")
    } for navigator in navigators]


def get_case_customer_user(db: Session, case_id: int) -> User | None:
    """Get the customer user for the case."""
    case_customer = db.query(User).join(Customer, User.id == Customer.user_id).join(CaseCustomer, Customer.id == CaseCustomer.customer_id).filter(CaseCustomer.case_id == case_id, User.status == StatusEnum.ACTIVE, Customer.status == StatusEnum.ACTIVE).first()
    return case_customer


def get_case_lawyer_by_case_id(db: Session, case_id: int) -> CaseLawyer | None:
    """Get the case lawyer for the case."""
    case_lawyer = db.query(CaseLawyer).filter(CaseLawyer.case_id == case_id).first()
    return case_lawyer


def get_timeline_type(db: Session, type_name: str, role_code: str, version: int) -> TimelineType | None:
    """Get the event type by name."""
    timeline_type = db.query(TimelineType).filter(TimelineType.type_name == type_name, TimelineType.role_code == role_code, TimelineType.version == version).first()
    return timeline_type


def get_resolve_summary(db: Session, case_id: int) -> tuple[str | None, int | None]:
    """Get the resolve summary for the case."""
    resolve_id = None
    resolve = db.query(Resolve).join(CaseResolve, Resolve.id == CaseResolve.resolve_id).filter(CaseResolve.case_id == case_id).first()

    if resolve is None:
        return None, resolve_id

    result_reference_id = resolve.result_reference_id
    result_version = resolve.result_version
    resolve_id = resolve.id
    result = {}
    try:
        with open(settings.RESOLVE_RESULT_FILE_PATH) as f:
            result = json.load(f)
    except Exception:
        return None, resolve_id

    if result:
        summary_template = result.get(result_reference_id, {}).get("versions", {}).get(result_version, {}).get("summary", None)
        if summary_template is None:
            return None, resolve_id

        name=""
        partner_name=""
        for rqa in resolve.resolve_question_answers:
            qa = rqa.question_answer
            question_identifier = str(qa.question_identifier) if qa.question_identifier is not None else ""
            answer = json.loads(qa.answer) if qa.answer is not None else []
            if question_identifier == "1":
                name = str(answer[0].get("value", "")) if answer[0] is not None and isinstance(answer[0], dict) else ""
            if question_identifier == "2":
                partner_name = str(answer[0].get("value", "")) if answer[0] is not None and isinstance(answer[0], dict) else ""

        summary = "<html><body>" + str(summary_template.format(name=name, partner_name=partner_name)) + "</body></html>"
        return summary, resolve_id
    return None, resolve_id


def get_resolve_by_case_id(db: Session, case_id: int) -> Resolve | None:
    """Get the resolve reference (result_reference_id) for a case."""
    resolve = (
        db.query(Resolve)
        .join(CaseResolve, Resolve.id == CaseResolve.resolve_id)
        .filter(CaseResolve.case_id == case_id)
        .first()
    )
    return resolve if resolve else None


def get_triage_by_case_id(db: Session, case_id: int) -> Triage | None:
    """Get the triage for the case."""
    triage = (
        db.query(Triage)
        .join(CaseTriage, Triage.id == CaseTriage.triage_id)
        .filter(CaseTriage.case_id == case_id)
        .first()
    )
    return triage if triage else None


def get_lawyers_for_case(
    db: Session, resolve: Resolve, limit_flag: int | None = None
) -> tuple[list[int], list[Lawyer]]:
    """
        Get lawyers for the case based on selection rules.

        Rules:
        - Maximum limit: Return at most 5 lawyers.
        - Base selection rules:
        - 1 lawyer with an hourly rate between 0-250.
        - 1 lawyer with an hourly rate between 250-300.
        - 1 lawyer with an hourly rate greater than 300.
        - Additional conditions based on resolve_reference_id:
            - collaborative: Select lawyers that satisfy the base selection rules excluding expert_types
            'Lawyer-Mediator', 'Mediator', and 'Divorce Coach'.
            - hybrid_mediation / mediation: Select lawyers that satisfy the base selection rules, but only
            include those with expert_type 'Lawyer-Mediator'.
            - one_lawyer_one_couple: Return lawyers with DR preference 'One Lawyer One Couple'.
            - others (court, diy, private_fdr, lawyer_negotiation, arbitration): Select up to 5 random lawyers that satisfy the base selection rules.
        - Additional conditions based on resolve answer:
           - How can we help? -> If the answer is finance, then the lawyers having financial_claims_exemptions should be excluded.
        - DR Preference Group Logic (if limit_flag is provided):
            - If selected lawyers < limit_flag, add additional lawyers from the same DR preference group.
            - Group 1: DIRECT_NEGOTIATION, MEDIATION, ONE_LAWYER_ONE_COUPLE, HYBRID_MEDIATION_SUPPORT, HYBRID_MEDIATION_MEDIATOR
            - Group 2: LAWYER_NEGOTIATION, HYBRID_MEDIATION_SUPPORT, ARBITRATION_ARBITRATOR, EARLY_NEUTRAL_EVALUATION_EVALUATOR, COURT
            - Group 3: COLLABORATIVE
            - Interchangeability only works within the same group.
    """

    resolve_finance = resolve.finance_flag if resolve.finance_flag is not None else False

    # New logic #911 - we are now using recommend_approach as the resolve result
    resolve_result = resolve.recommended_approach

    # Base query for active lawyers with active users
    base_query = (
        db.query(Lawyer)
        .options(selectinload(Lawyer.expertises), selectinload(Lawyer.accredited_specialisms), selectinload(Lawyer.expert_types))
        .join(User, Lawyer.user_id == User.id)
        .filter(Lawyer.status == LawyerStatusEnum.ACTIVE)
        .filter(User.status == StatusEnum.ACTIVE)
    )
    if resolve_finance is True:
        base_query = base_query.filter(Lawyer.financial_claims_exemptions == False) # exclude lawyers having

    expert_type_filter = None
    # Build expert type filter based on resolve_reference
    if resolve_result == "collaborative":
        # Exclude lawyers with specified expert types
        excluded_expert_types = [
            ExpertTypeEnum.LAWYER_MEDIATOR,
            ExpertTypeEnum.MEDIATOR,
            ExpertTypeEnum.DIVORCE_COACH
        ]
        excluded_lawyer_ids = [
            row[0] for row in db.query(LawyerExpertType.lawyer_id)
            .filter(LawyerExpertType.expert_type.in_(excluded_expert_types))
            .all()
        ]
        base_query = base_query.filter(~Lawyer.id.in_(excluded_lawyer_ids))

    elif resolve_result in ["hybrid_mediation", "mediation"]:
        # Only select lawyers with 'Lawyer-Mediator' expert_type
        mediator_lawyer_ids = [
            row[0] for row in db.query(LawyerExpertType.lawyer_id)
            .filter(LawyerExpertType.expert_type == ExpertTypeEnum.LAWYER_MEDIATOR)
            .all()
        ]
        expert_type_filter = Lawyer.id.in_(mediator_lawyer_ids)
    
    elif resolve_result == "one_lawyer_one_couple":

        oloc_lawyer_ids = [
            row[0] for row in db.query(LawyerDRPreference.lawyer_id)
            .filter(LawyerDRPreference.dr_preference == DRPreferenceEnum.ONE_LAWYER_ONE_COUPLE)
            .distinct()
            .all()
        ]
        expert_type_filter = Lawyer.id.in_(oloc_lawyer_ids)

    # Apply expert type filter to base query
    if expert_type_filter is not None:
        base_query = base_query.filter(expert_type_filter)

    selected_lawyers: list[Lawyer] = []
    selected_lawyer_ids: list[int] = []

    # Query for each rate range separately to ensure we don't miss any lawyers
    # Rate 0-250
    rate_0_250_lawyer = (
        base_query.filter(
            and_(
                Lawyer.hourly_rate.isnot(None),
                Lawyer.hourly_rate >= 0,
                Lawyer.hourly_rate < 250
            )
        )
        .order_by(Lawyer.created_at.desc())
        .first()
    )
    if rate_0_250_lawyer:
        selected_lawyer_ids.append(int(rate_0_250_lawyer.id))
        selected_lawyers.append(rate_0_250_lawyer)

    # Rate 250-300
    rate_250_300_lawyer = (
        base_query.filter(
            and_(
                Lawyer.hourly_rate.isnot(None),
                Lawyer.hourly_rate >= 250,
                Lawyer.hourly_rate < 300
            )
        )
        .order_by(Lawyer.created_at.desc())
        .first()
    )
    if rate_250_300_lawyer:
        selected_lawyer_ids.append(int(rate_250_300_lawyer.id))
        selected_lawyers.append(rate_250_300_lawyer)

    # Rate >300
    rate_over_300_lawyer = (
        base_query.filter(
            and_(
                Lawyer.hourly_rate.isnot(None),
                Lawyer.hourly_rate >= 300
            )
        )
        .order_by(Lawyer.created_at.desc())
        .first()
    )
    if rate_over_300_lawyer:
        selected_lawyer_ids.append(int(rate_over_300_lawyer.id))
        selected_lawyers.append(rate_over_300_lawyer)

    # Get remaining eligible lawyers (excluding already selected ones)
    remaining_slots = 5 - len(selected_lawyer_ids)
    if remaining_slots > 0:
        if resolve_result not in ["collaborative", "hybrid_mediation", "mediation", "one_lawyer_one_couple"]:
            remaining_query = base_query.filter(Lawyer.id.notin_(selected_lawyer_ids))
            remaining_lawyers = remaining_query.order_by(func.random()).limit(remaining_slots).all()

            selected_lawyer_ids.extend([int(lawyer.id) for lawyer in remaining_lawyers])
            selected_lawyers.extend(remaining_lawyers)

    # NEW LOGIC: DR Preference Group-based selection (only if limit_flag is provided)
    if limit_flag is not None and len(selected_lawyer_ids) < limit_flag:
        # Map result_reference_id to DR preference groups
        dr_preference_groups = _get_dr_preference_group_for_result_reference(resolve_result)

        if dr_preference_groups:
            # Get additional lawyers from the same DR preference group
            additional_slots = limit_flag - len(selected_lawyer_ids)
            additional_lawyers = _get_additional_lawyers_by_dr_preference(
                db=db,
                resolve_finance=resolve_finance,
                dr_preferences=dr_preference_groups,
                exclude_lawyer_ids=selected_lawyer_ids,
                limit=additional_slots,
            )
            selected_lawyer_ids.extend([int(lawyer.id) for lawyer in additional_lawyers])
            selected_lawyers.extend(additional_lawyers)

    return selected_lawyer_ids, selected_lawyers


def get_lawyers_for_triage(
    db: Session, triage: Triage, limit_flag: int | None = None
) -> tuple[list[int], list[Lawyer]]:
    """
    Get lawyers for the triage based on selection rules.

    Rules:
        - Maximum limit: Return at most 5 lawyers.
        - Base selection rules:
        - 1 lawyer with an hourly rate between 0-250.
        - 1 lawyer with an hourly rate between 250-300.
        - 1 lawyer with an hourly rate greater than 300.
        - Additional conditions based on triage answer:
           - Which one of the following best describes what would leave you feeling most satisfied with the outcome? -> If the answer is I want to preserve, or where possible improve, our family relationships. Create subset of experts with DR processes - DIY, Mediation, Collaborative
        - DR Preference Group Logic (if limit_flag is provided):
            - If selected lawyers < limit_flag, add additional lawyers from the same DR preference group.
    """

    triage_question_answers = triage.triage_question_answers or []
    db_answer_map: dict[str, list] = {}
    for tqa in triage_question_answers:
        question_answer = tqa.question_answer
        if question_answer is None:
            continue
        question_identifier = (
            str(question_answer.question_identifier)
            if question_answer.question_identifier is not None
            else ""
        )
        answer = json.loads(question_answer.answer) if question_answer.answer is not None else []
        db_answer_map[question_identifier] = answer

    # Q3: outcome satisfaction preference
    outcome_answer = db_answer_map.get("3", [])
    outcome_values = []
    for item in outcome_answer:
        if isinstance(item, dict):
            if "value" in item:
                outcome_values.append(item["value"])
            elif item:
                outcome_values.append(next(iter(item.values())))
    preserve_family_relationships = (
        "preserve_or_improve_family_relationships" in outcome_values
    )

    # DIY maps to Direct Negotiation in DR preferences
    preserve_dr_preferences = [
        DRPreferenceEnum.DIRECT_NEGOTIATION,
        DRPreferenceEnum.MEDIATION,
        DRPreferenceEnum.COLLABORATIVE,
    ]

    base_query = (
        db.query(Lawyer)
        .options(
            selectinload(Lawyer.expertises),
            selectinload(Lawyer.accredited_specialisms),
            selectinload(Lawyer.expert_types),
        )
        .join(User, Lawyer.user_id == User.id)
        .filter(Lawyer.status == LawyerStatusEnum.ACTIVE)
        .filter(User.status == StatusEnum.ACTIVE)
    )

    if preserve_family_relationships:
        lawyer_ids_with_dr_preferences = [
            row[0]
            for row in db.query(LawyerDRPreference.lawyer_id)
            .filter(LawyerDRPreference.dr_preference.in_(preserve_dr_preferences))
            .distinct()
            .all()
        ]
        if not lawyer_ids_with_dr_preferences:
            return [], []
        base_query = base_query.filter(Lawyer.id.in_(lawyer_ids_with_dr_preferences))

    selected_lawyer_ids: list[int] = []
    selected_lawyers: list[Lawyer] = []

    # Rate 0-250
    rate_0_250_lawyer = (
        base_query.filter(
            and_(
                Lawyer.hourly_rate.isnot(None),
                Lawyer.hourly_rate >= 0,
                Lawyer.hourly_rate < 250,
            )
        )
        .order_by(Lawyer.created_at.desc())
        .first()
    )
    if rate_0_250_lawyer:
        selected_lawyer_ids.append(int(rate_0_250_lawyer.id))
        selected_lawyers.append(rate_0_250_lawyer)

    # Rate 250-300
    rate_250_300_lawyer = (
        base_query.filter(
            and_(
                Lawyer.hourly_rate.isnot(None),
                Lawyer.hourly_rate >= 250,
                Lawyer.hourly_rate < 300,
            )
        )
        .order_by(Lawyer.created_at.desc())
        .first()
    )
    if rate_250_300_lawyer:
        selected_lawyer_ids.append(int(rate_250_300_lawyer.id))
        selected_lawyers.append(rate_250_300_lawyer)

    # Rate >300
    rate_over_300_lawyer = (
        base_query.filter(
            and_(
                Lawyer.hourly_rate.isnot(None),
                Lawyer.hourly_rate >= 300,
            )
        )
        .order_by(Lawyer.created_at.desc())
        .first()
    )
    if rate_over_300_lawyer:
        selected_lawyer_ids.append(int(rate_over_300_lawyer.id))
        selected_lawyers.append(rate_over_300_lawyer)

    # Fill remaining slots up to the maximum of 5
    remaining_slots = 5 - len(selected_lawyer_ids)
    if remaining_slots > 0:
        remaining_query = base_query
        if selected_lawyer_ids:
            remaining_query = remaining_query.filter(Lawyer.id.notin_(selected_lawyer_ids))
        remaining_lawyers = remaining_query.order_by(func.random()).limit(remaining_slots).all()
        selected_lawyer_ids.extend([int(lawyer.id) for lawyer in remaining_lawyers])
        selected_lawyers.extend(remaining_lawyers)

    # DR Preference Group-based selection (only if limit_flag is provided)
    if limit_flag is not None and len(selected_lawyer_ids) < limit_flag:
        if preserve_family_relationships:
            additional_slots = limit_flag - len(selected_lawyer_ids)
            additional_lawyers = _get_additional_lawyers_by_dr_preference(
                db=db,
                resolve_finance=False,
                dr_preferences=preserve_dr_preferences,
                exclude_lawyer_ids=selected_lawyer_ids,
                limit=additional_slots,
            )
            selected_lawyer_ids.extend([int(lawyer.id) for lawyer in additional_lawyers])
            selected_lawyers.extend(additional_lawyers)

    return selected_lawyer_ids, selected_lawyers


def _get_dr_preference_group_for_result_reference(result_reference_id: str | None) -> list[DRPreferenceEnum] | None:
    """
    Map result_reference_id to the corresponding DR preference group.
    
    Returns the list of DR preferences that can be used interchangeably for the given result_reference_id.
    
    Groups:
    - Group 1: DIRECT_NEGOTIATION, MEDIATION, ONE_LAWYER_ONE_COUPLE, HYBRID_MEDIATION_SUPPORT, HYBRID_MEDIATION_MEDIATOR
    - Group 2: LAWYER_NEGOTIATION, HYBRID_MEDIATION_SUPPORT, ARBITRATION_ARBITRATOR, EARLY_NEUTRAL_EVALUATION_EVALUATOR, COURT
    - Group 3: COLLABORATIVE
    """
    if result_reference_id is None:
        return None
    
    # Group 1: DIRECT_NEGOTIATION, MEDIATION, ONE_LAWYER_ONE_COUPLE, HYBRID_MEDIATION_SUPPORT, HYBRID_MEDIATION_MEDIATOR
    group_1 = [
        DRPreferenceEnum.DIRECT_NEGOTIATION,
        DRPreferenceEnum.MEDIATION,
        DRPreferenceEnum.ONE_LAWYER_ONE_COUPLE,
        DRPreferenceEnum.HYBRID_MEDIATION_SUPPORT,
        DRPreferenceEnum.HYBRID_MEDIATION_MEDIATOR,
    ]
    
    # Group 2: LAWYER_NEGOTIATION, HYBRID_MEDIATION_SUPPORT, ARBITRATION_ARBITRATOR, EARLY_NEUTRAL_EVALUATION_EVALUATOR, COURT
    group_2 = [
        DRPreferenceEnum.LAWYER_NEGOTIATION,
        DRPreferenceEnum.HYBRID_MEDIATION_SUPPORT,
        DRPreferenceEnum.ARBITRATION_ARBITRATOR,
        DRPreferenceEnum.EARLY_NEUTRAL_EVALUATION_EVALUATOR,
        DRPreferenceEnum.COURT,
    ]
    
    # Group 3: COLLABORATIVE
    group_3 = [DRPreferenceEnum.COLLABORATIVE]
    
    # Map result_reference_id to groups
    mapping = {
        "direct_negotiation": group_1,
        "mediation": group_1,
        "one_lawyer_one_couple": group_1,
        "hybrid_mediation": group_1,
        "lawyer_negotiation": group_2,
        "arbitration": group_2,
        "private_fdr": group_2,
        "court": group_2,
        "collaborative": group_3,
    }
    
    return mapping.get(result_reference_id)


def _get_additional_lawyers_by_dr_preference(
    db: Session,
    resolve_finance: bool,
    dr_preferences: list[DRPreferenceEnum],
    exclude_lawyer_ids: list[int],
    limit: int,
) -> list[Lawyer]:
    """
    Get additional lawyers based on DR preferences.
    
    Special handling:
    - For "mediation" or "one_lawyer_one_couple", we can also include MEDIATION lawyers with DR preference group 1.
    """
    # Base query for active lawyers with active users
    base_query = (
        db.query(Lawyer)
        .join(User, Lawyer.user_id == User.id)
        .filter(Lawyer.status == LawyerStatusEnum.ACTIVE)
        .filter(User.status == StatusEnum.ACTIVE)
    )
    if resolve_finance is True:
        base_query = base_query.filter(Lawyer.financial_claims_exemptions == False) # exclude lawyers having
    # Get lawyer IDs that have any of the required DR preferences
    lawyer_ids_with_dr_preferences = [
        row[0] for row in db.query(LawyerDRPreference.lawyer_id)
        .filter(LawyerDRPreference.dr_preference.in_(dr_preferences))
        .distinct()
        .all()
    ]
    
    if not lawyer_ids_with_dr_preferences:
        return []
    
    if exclude_lawyer_ids:
        required_lawyer_ids = list(filter(lambda x: x not in exclude_lawyer_ids, lawyer_ids_with_dr_preferences))
    else:
        required_lawyer_ids = lawyer_ids_with_dr_preferences
    # Filter base query to only include lawyers with matching DR preferences
    dr_preference_query = base_query.filter(
        and_(
            Lawyer.id.in_(required_lawyer_ids),
        )
    )
    # Get additional lawyers randomly
    additional_lawyers = dr_preference_query.order_by(func.random()).limit(limit).all()
    
    return additional_lawyers


def get_question_option_value(source: str, question_identifier: str, version: str, key: str, option_value_key: str = "value") -> str | None:
    """
    Fetch the display value of a question option based on source, question_identifier, version, and key.
    Here, the corresponding question is present, so the value is fetched accordingly.
    Args:
        source: Either 'kyc' or 'resolve'.
        question_identifier: The identifier of the question.
        version: The version of the question to fetch.
        key: The option key for which the display value is required.

    Returns:
        The corresponding display value as a string. If not found, return None.
    """
    # Select the correct JSON file based on the source
    if source.lower() == 'kyc':
        file_path = settings.KYC_QUESTIONS_FILE_PATH
    elif source.lower() == 'resolve':
        file_path = settings.QUESTIONS_FILE_PATH
    elif source.lower() == 'triage':
        file_path = settings.TRIAGE_QUESTIONS_FILE_PATH
    else:
        return None

    try:
        with open(file_path) as f:
            questions_data = json.load(f)

        # Check if the question exists
        question_data = questions_data.get(str(question_identifier))
        if not question_data:
            return None

        versions = question_data.get("versions", {})
        if version not in versions:
            return None

        version_data = versions[version]
        options = version_data.get("options", [])

        # If the question is present, fetch the value for the given key
        for option in options:
            if isinstance(option, dict):
                # Direct key match
                if key in option:
                    value = option[key]
                    if isinstance(value, dict):
                        return str(value.get(option_value_key, key))
                    else:
                        return str(value)
                # Nested structure
                for option_key, option_value in option.items():
                    if option_key == key:
                        if isinstance(option_value, dict):
                            return str(option_value.get(option_value_key, key))
                        else:
                            return str(option_value)
                    elif isinstance(option_value, dict) and key in option_value:
                        nested_value = option_value[key]
                        if isinstance(nested_value, dict):
                            return str(nested_value.get(option_value_key, key))
                        else:
                            return str(nested_value)
        return None

    except Exception:
        return None

def get_case_summary(db: Session, case: Case, key: str = "question", value: str = "answer") -> dict:
    """
    Build and return a comprehensive case summary in JSON format.

    Returns:
        Dictionary with summary array containing question-answer pairs.
        Example: {"summary": [{"question": "...", "answer": "..."}]}
    """
    from app.db.services.kyc import get_resolve_options_for_kyc

    if case and case.is_triage is True:
        patterns = {
            "kyc_full_name": (["what is your full name"], "kyc"),
            "kyc_partner_name": (["partner's full name", "partner full name"], "kyc"),
            "kyc_circumstances": (["describes your circumstances"], "kyc"),
            "kyc_court_steps": (["steps in the next 7 days"], "kyc"),
            "kyc_family_home_status": (["accommodation you own or rent"], "kyc"),
            "kyc_children": (["Age of children"], "kyc"),
            "kyc_existing_or_previous_experts": (["the present advisors"], "kyc"),
            "kyc_domestic_abuse": (["domestic abuse or coercive control"], "kyc"),
            "triage_affordability": (["earnings and state benefits"], "triage"),
            "kyc_help_with": (["do you need help with"], "kyc"),
        }
    else:
        patterns = {
            "kyc_full_name": (["what is your full name"], "kyc"),
            "kyc_partner_name": (["partner's full name", "partner full name"], "kyc"),
            "kyc_circumstances": (["describes your circumstances"], "kyc"),
            "kyc_court_steps": (["steps in the next 7 days"], "kyc"),
            "resolve_in_court": (["court proceedings"], "resolve"),
            "resolve_affordability": (["affordability"], "resolve"),
            "resolve_children_complexity": (["children complexity"], "resolve"),
            "resolve_financial_complexity": (["financial complexity"], "resolve"),
            "resolve_warning_signs": (["warning signs"], "resolve"),
        }

    kyc_questions = {}
    resolve_questions = {}
    triage_questions = {}
    try:
        with open(settings.KYC_QUESTIONS_FILE_PATH) as f:
            kyc_questions = json.load(f)
    except Exception:
        pass
    try:
        with open(settings.QUESTIONS_FILE_PATH) as f:
            resolve_questions = json.load(f)
    except Exception:
        pass
    try:
        with open(settings.TRIAGE_QUESTIONS_FILE_PATH) as f:
            triage_questions = json.load(f)
    except Exception:
        pass

    def find_question(questions_dict: dict, patterns: list[str]) -> tuple[str | None, str | None, str | None]:
        for q_id, q_data in questions_dict.items():
            for version, version_data in q_data.get("versions", {}).items():
                text = f"{version_data.get('question', '')} {version_data.get('title', '')}".lower()
                if any(p.lower() in text for p in patterns):
                    return q_id, version_data.get("question") or version_data.get("title"), version
        return None, None, None

    question_map = {}
    for (pattern_list, source) in patterns.values():
        if source == "kyc":
            questions = kyc_questions
        elif source == "resolve":
            questions = resolve_questions
        elif source == "triage":
            questions = triage_questions

        q_id, q_text, version = find_question(questions, pattern_list)
        if q_id:
            question_map[q_id] = {"text": q_text, "source": source, "version": version}

    # Only fetch KYC answers for the question_identifiers in question_map where source is "kyc"
    kyc_qids = [q_id for q_id, info in question_map.items() if info["source"] == "kyc"]
    #include 1.1, 1.3, 2.1, 2.3
    kyc_qids = ["1.1", "1.3", "2.1", "2.3"] + kyc_qids

    kyc_answers = {}
    if kyc_qids:
        kyc_data = (
            db.query(QuestionAnswers)
            .join(EngageQuestionAnswers, QuestionAnswers.id == EngageQuestionAnswers.question_answer_id)
            .join(Engage, EngageQuestionAnswers.engage_id == Engage.id)
            .join(CaseEngage, Engage.id == CaseEngage.engage_id)
            .filter(
                CaseEngage.case_id == case.id,
                QuestionAnswers.question_identifier.in_(kyc_qids)
            )
            .all()
        )
        for qa in kyc_data:
            if qa.question_identifier is None:
                continue # type: ignore
            kyc_answers[str(qa.question_identifier)] = {
                "answer": json.loads(str(qa.answer)) if qa.answer else [],
                "question_answer": qa
            }

    # Only fetch RESOLVE answers for the question_identifiers in question_map where source is "resolve"
    resolve_qids = [q_id for q_id, info in question_map.items() if info["source"] == "resolve"]
    resolve_answers = {}
    if resolve_qids:
        resolve_data = (
            db.query(QuestionAnswers)
            .join(ResolveQuestionAnswers, QuestionAnswers.id == ResolveQuestionAnswers.question_answer_id)
            .join(Resolve, ResolveQuestionAnswers.resolve_id == Resolve.id)
            .join(CaseResolve, Resolve.id == CaseResolve.resolve_id)
            .filter(
                CaseResolve.case_id == case.id,
                QuestionAnswers.question_identifier.in_(resolve_qids)
            )
            .all()
        )
        for qa in resolve_data:
            if qa.question_identifier is None:
                continue # type: ignore
            resolve_answers[str(qa.question_identifier)] = {
                "answer": json.loads(str(qa.answer)) if qa.answer else [],
                "question_answer": qa
            }

    # Only fetch Triage answers for the question_identifiers in question_map where source is "triage"
    triage_qids = [q_id for q_id, info in question_map.items() if info["source"] == "triage"]
    triage_answers = {}
    if triage_qids:
        from app.db.models.triage_question_answers import TriageQuestionAnswers
        triage_data = (
            db.query(QuestionAnswers)
            .join(TriageQuestionAnswers, QuestionAnswers.id == TriageQuestionAnswers.question_answer_id)
            .join(Triage, TriageQuestionAnswers.triage_id == Triage.id)
            .join(CaseTriage, Triage.id == CaseTriage.triage_id)
            .filter(
                CaseTriage.case_id == case.id,
                QuestionAnswers.question_identifier.in_(triage_qids)
            )
            .all()
        )
        for qa in triage_data:
            if qa.question_identifier is None:
                continue # type: ignore
            triage_answers[str(qa.question_identifier)] = {
                "answer": json.loads(str(qa.answer)) if qa.answer else [],
                "question_answer": qa
            }

    # Extract partner and customer names for placeholder replacement
    partner_name = ""
    customer_name = ""
    summary = []

    option_labels = {}
    if any(qid == "6" and qinfo["source"] == "kyc" for qid, qinfo in question_map.items()):
        if case.is_triage is True:
            engage = db.query(CaseEngage).filter(CaseEngage.case_id == case.id).first()
            engage_id = engage.engage_id if engage else None
            options = get_resolve_options_for_kyc(db, None, engage_id)
        else:
            options = get_resolve_options_for_kyc(db, int(case.resolve_id), None)
        for option in options or []:
            option_labels.update(option)

    for q_id, info in question_map.items():
        if info["source"] == "kyc":
            answers_dict = kyc_answers
        elif info["source"] == "resolve":
            answers_dict = resolve_answers
        elif info["source"] == "triage":
            answers_dict = triage_answers
        if info["source"] == "kyc" and q_id == "1":
            if q_id in kyc_answers:
                answer_entry = answers_dict.get(q_id, {"answer": [], "question_answer": None})
                answer = answer_entry["answer"]
                customer_name = answer[0]["value"]
            else:
                if "1.1" in kyc_answers:
                    first_name = kyc_answers["1.1"]["answer"][0]["value"]
                
                if "1.3" in kyc_answers:
                    last_name = kyc_answers["1.3"]["answer"][0]["value"]
                answer = [{"value": first_name + " " + last_name}]
                customer_name = first_name + " " + last_name

        elif info["source"] == "kyc" and q_id == "2":
            if q_id in kyc_answers:
                answer_entry = answers_dict.get(q_id, {"answer": [], "question_answer": None})
                answer = answer_entry["answer"]
                partner_name = answer[0]["value"]
            else:
                if "2.1" in kyc_answers:
                    first_name = kyc_answers["2.1"]["answer"][0]["value"]
                if "2.3" in kyc_answers:
                    last_name = kyc_answers["2.3"]["answer"][0]["value"]
                answer = [{"value": first_name + " " + last_name}]
                partner_name = first_name + " " + last_name
        else:
            answer_entry = answers_dict.get(q_id, {"answer": [], "question_answer": None})
            if answer_entry.get("question_answer") is None:
                continue
            else:
                answer = answer_entry["answer"]

        question_text = info["text"]
        if question_text and "{partner_name}" in question_text and partner_name:
            question_text = question_text.replace("{partner_name}", partner_name)
        if question_text and "{name}" in question_text and customer_name:
            question_text = question_text.replace("{name}", customer_name)

        processed_answers: list[str] = []
        for item in answer:
            # If the answer is a dict with a 'value', try to fetch the display value using get_question_option_value
            if isinstance(item, dict):
                if 'value' in item:
                    # For option-based questions, try to get display value
                    display_value = get_question_option_value(
                        str(info["source"]),
                        str(q_id),
                        str(info.get("version", "")),
                        str(item["value"])
                    )
                    if display_value is None and info["source"] == "kyc" and q_id == "6":
                        display_value = option_labels.get(str(item["value"]))
                    if display_value is not None:
                        display_value = display_value.replace("{partner_name}", partner_name)
                        processed_answers.append(display_value)
                    else:
                        processed_answers.append(str(item["value"]))
                else:
                    processed_answers.append("")
            else:
                processed_answers.append("")

        if not processed_answers:
            answer_value: str | list[str] = ""
        elif info["source"] == "kyc" and q_id == "6":
            answer_value = ", ".join(processed_answers)
        elif len(processed_answers) == 1:
            answer_value = processed_answers[0]
        else:
            answer_value = processed_answers

        summary.append({
            key: str(question_text) if question_text is not None else "",
            value: answer_value
        })
    return {"summary": summary}


#Updated case summary function for lawyer card
def get_case_summary_for_lawyer(db: Session, case : Case, key: str = "question", value: str = "answer") -> dict:
    """
    Build and return a comprehensive case summary in JSON format.

    Returns:
        Dictionary with summary array containing question-answer pairs.
        Example: {"summary": [{"question": "...", "answer": "..."}]}
    """
    from app.db.services.kyc import get_resolve_options_for_kyc

    if case and case.is_triage is True:
        patterns = {
            "kyc_full_name": (["what is your full name"], "kyc", ""),
            "kyc_partner_name": (["partner's full name"], "kyc", ""),
            "kyc_gender": (["gender"], "kyc", ""),
            "triage_ideal_outcome": (["satisfied with the outcome"], "triage","1"),
            "kyc_help_with": (["do you need help with"], "kyc","2"),
            "kyc_family_home_status": (["accommodation you own or rent"], "kyc","3"),
            "kyc_complexity": (["relevant to your situation"], "kyc","4"),
            "kyc_children": (["Age of children"], "kyc","5"),
            "kyc_existing_or_previous_experts": (["the present advisors"], "kyc","6"),
            "kyc_domestic_abuse": (["domestic abuse or coercive control"], "kyc","7"),
        }
        label_map = {
            "1": "{name}'s ideal outcome",
            "2": "Help with",
            "3": "Family home status",
            "4": "Complexity",
            "5": "Children",
            "6": "Existing or previous experts",
            "7": "Domestic Abuse",
        }
        resolve_lawyer_value_questions = []
    else:
        patterns = {
            "kyc_full_name": (["what is your full name"], "kyc", ""),
            "kyc_partner_name": (["partner's full name", "partner full name"], "kyc", ""),
            "kyc_gender": (["gender"], "kyc", ""),
            "resolve_in_court": (["court proceedings"], "resolve","1"),
            "resolve_same_space_comfort": (["comfortable being in the same room"], "resolve","2"),
            "resolve_warning_signs": (["warning signs"], "resolve","3"),
            "resolve_financial_complexity": (["financial complexity"], "resolve","4"),
            "resolve_children_complexity": (["children complexity"], "resolve","5"),
            "resolve_communication": (["current communication"], "resolve","6"),
            # "resolve_conflict_level": (["conflict level"], "resolve","7"),
            "resolve_confidence_level": (["confidence"], "resolve","8"),
            "kyc_accommodation": (["accommodation you own or rent"], "kyc","9"),
            "resolve_length_of_relationship": (["length of relationship"], "resolve","10"),
        }

        label_map = {
            "1": "Court Proceedings",
            "2": "Sharing space with {partner_name}",
            "3": "Warning Signs",
            "4": "Financial Complexity",
            "5": "Child Complexity",
            "6": "Communication Level",
            # "7": "Conflict Level",
            "8": "Confidence Level",
            "9": "Accommodation Status",
            "10": "Length of Relationship"
        }

        resolve_lawyer_value_questions = ["6", "16", "17", "18", "19"]

    gender_map = {
        "male": {
            "subject_pronoun": "he",
            "object_pronoun": "him",
            "be_verb": "is"
        },
        "female": {
            "subject_pronoun": "she",
            "object_pronoun": "her",
            "be_verb": "is"
        },
        "prefer_not_to_say": {
            "subject_pronoun": "they",
            "object_pronoun": "them",
            "be_verb": "are"
        }
    }
    subject_pronoun = "he"
    object_pronoun = "him"
    be_verb = "is"
    kyc_questions = {}
    resolve_questions = {}
    triage_questions = {}
    try:
        with open(settings.KYC_QUESTIONS_FILE_PATH) as f:
            kyc_questions = json.load(f)
    except Exception:
        pass

    if case and case.is_triage is True:
        resolve_questions = {}
        with open(settings.TRIAGE_QUESTIONS_FILE_PATH) as f:
            triage_questions = json.load(f)
    else:
        try:
            with open(settings.QUESTIONS_FILE_PATH) as f:
                resolve_questions = json.load(f)
        except Exception:
            pass

    def find_question(questions_dict: dict, patterns: list[str]) -> tuple[str | None, str | None, str | None]:
        for q_id, q_data in questions_dict.items():
            for version, version_data in q_data.get("versions", {}).items():
                text = f"{version_data.get('question', '')} {version_data.get('title', '')}".lower()
                if any(p.lower() in text for p in patterns):
                    return q_id, version_data.get("question") or version_data.get("title"), version
        return None, None, None

    question_map = {}
    for (pattern_list, source, label) in patterns.values():
        if source == "kyc":
            questions = kyc_questions
        elif source == "resolve":
            questions = resolve_questions
        else:
            questions = triage_questions
        q_id, q_text, version = find_question(questions, pattern_list)
        if q_id:
            question_map[q_id] = {"text": label_map.get(label, ""), "source": source, "version": version}

    # Only fetch KYC answers for the question_identifiers in question_map where source is "kyc"
    kyc_qids = [q_id for q_id, info in question_map.items() if info["source"] == "kyc"]
    #include 1.1, 1.3, 2.1, 2.3
    kyc_qids = ["1.1", "1.3", "2.1", "2.3", "3"] + kyc_qids

    kyc_answers = {}
    if kyc_qids:
        kyc_data = (
            db.query(QuestionAnswers)
            .join(EngageQuestionAnswers, QuestionAnswers.id == EngageQuestionAnswers.question_answer_id)
            .join(Engage, EngageQuestionAnswers.engage_id == Engage.id)
            .join(CaseEngage, Engage.id == CaseEngage.engage_id)
            .filter(
                CaseEngage.case_id == case.id,
                QuestionAnswers.question_identifier.in_(kyc_qids)
            )
            .all()
        )
        for qa in kyc_data:
            if qa.question_identifier is None:
                continue # type: ignore
            kyc_answers[str(qa.question_identifier)] = {
                "answer": json.loads(str(qa.answer)) if qa.answer else [],
                "question_answer": qa
            }
            if qa.question_identifier == "3":
                gender = json.loads(str(qa.answer))[0]["value"] if json.loads(str(qa.answer)) else ""
                if gender and gender != "":
                    customer_gender = gender
                gender_info = gender_map[customer_gender]
                subject_pronoun = gender_info["subject_pronoun"]
                object_pronoun = gender_info["object_pronoun"]
                be_verb = gender_info["be_verb"]

    # Only fetch RESOLVE answers for the question_identifiers in question_map where source is "resolve"
    resolve_qids = [q_id for q_id, info in question_map.items() if info["source"] == "resolve"]
    resolve_answers = {}
    if resolve_qids:
        resolve_data = (
            db.query(QuestionAnswers)
            .join(ResolveQuestionAnswers, QuestionAnswers.id == ResolveQuestionAnswers.question_answer_id)
            .join(Resolve, ResolveQuestionAnswers.resolve_id == Resolve.id)
            .join(CaseResolve, Resolve.id == CaseResolve.resolve_id)
            .filter(
                CaseResolve.case_id == case.id,
                QuestionAnswers.question_identifier.in_(resolve_qids)
            )
            .all()
        )
        for qa in resolve_data:
            if qa.question_identifier is None:
                continue # type: ignore
            resolve_answers[str(qa.question_identifier)] = {
                "answer": json.loads(str(qa.answer)) if qa.answer else [],
                "question_answer": qa
            }

    # Only fetch Triage answers for the question_identifiers in question_map where source is "triage"
    triage_qids = [q_id for q_id, info in question_map.items() if info["source"] == "triage"]
    triage_answers = {}
    if triage_qids:
        from app.db.models.triage_question_answers import TriageQuestionAnswers
        triage_data = (
            db.query(QuestionAnswers)
            .join(TriageQuestionAnswers, QuestionAnswers.id == TriageQuestionAnswers.question_answer_id)
            .join(Triage, TriageQuestionAnswers.triage_id == Triage.id)
            .join(CaseTriage, Triage.id == CaseTriage.triage_id)
            .filter(
                CaseTriage.case_id == case.id,
                QuestionAnswers.question_identifier.in_(triage_qids)
            )
            .all()
        )
        for qa in triage_data:
            if qa.question_identifier is None:
                continue # type: ignore
            triage_answers[str(qa.question_identifier)] = {
                "answer": json.loads(str(qa.answer)) if qa.answer else [],
                "question_answer": qa
            }

    # Conflict Level (label 8): use resolve question 10's score result label (deferred import to avoid circular import)
    # conflict_level = ""
    # resolve_link = db.query(CaseResolve).filter(CaseResolve.case_id == case_id).first()
    # if resolve_link is not None:
    #     score_data = get_question_scores_and_results(db, resolve_link.resolve_id, ["10"])
    #     conflict_level = score_data.get("10", {}).get("result", "")

    # Extract partner and customer names for placeholder replacement
    partner_name = ""
    partner_first_name = ""
    customer_name = ""
    customer_first_name = ""
    summary = []

    option_labels = {}
    if any(qid == "6" and qinfo["source"] == "kyc" for qid, qinfo in question_map.items()):
        if case.is_triage is True:
            engage = db.query(CaseEngage).filter(CaseEngage.case_id == case.id).first()
            engage_id = engage.engage_id if engage else None
            options = get_resolve_options_for_kyc(db, None, engage_id)
        else:
            options = get_resolve_options_for_kyc(db, int(case.resolve_id), None)
        for option in options or []:
            option_labels.update(option)

    # print("question_map >>>", question_map)
    # return
    for q_id, info in question_map.items():
        if info["source"] == "kyc":
            answers_dict = kyc_answers
        elif info["source"] == "resolve":
            answers_dict = resolve_answers
        elif info["source"] == "triage":
            answers_dict = triage_answers
        answer_entry = answers_dict.get(q_id, {"answer": [], "question_answer": None})
        answer = answer_entry["answer"]
        if info["source"] == "kyc" and q_id == "1":
            if q_id in kyc_answers:
                answer_entry = answers_dict.get(q_id, {"answer": [], "question_answer": None})
                answer = answer_entry["answer"]
                customer_name = answer[0]["value"]
            else:
                if "1.1" in kyc_answers:
                    first_name = kyc_answers["1.1"]["answer"][0]["value"]
                    customer_first_name = first_name
                if "1.3" in kyc_answers:
                    last_name = kyc_answers["1.3"]["answer"][0]["value"]
                answer = [{"value": first_name + " " + last_name}]
                customer_name = first_name + " " + last_name

        elif info["source"] == "kyc" and q_id == "2":
            if q_id in kyc_answers:
                answer_entry = answers_dict.get(q_id, {"answer": [], "question_answer": None})
                answer = answer_entry["answer"]
                partner_name = answer[0]["value"]
            else:
                if "2.1" in kyc_answers:
                    first_name = kyc_answers["2.1"]["answer"][0]["value"]
                    partner_first_name = first_name
                if "2.3" in kyc_answers:
                    last_name = kyc_answers["2.3"]["answer"][0]["value"]
                answer = [{"value": first_name + " " + last_name}]
                partner_name = first_name + " " + last_name
        else:

            answer_entry = answers_dict.get(q_id, {"answer": [], "question_answer": None})
            answer = answer_entry["answer"]

        question_text = info["text"]
        if question_text and "{partner_name}" in question_text and partner_first_name:
            question_text = question_text.replace("{partner_name}", partner_first_name)
        if question_text and "{name}" in question_text and customer_name:
            question_text = question_text.replace("{name}", customer_name)

        processed_answers: list[str] = []
        option_value_key = "value"
        if str(q_id) in resolve_lawyer_value_questions:
            option_value_key = "lawyer_value"
        for item in answer:
            # If the answer is a dict with a 'value', try to fetch the display value using get_question_option_value
            if isinstance(item, dict):
                if "value" in item:
                    # For option-based questions, try to get display value
                    display_value = get_question_option_value(
                        str(info["source"]),
                        str(q_id),
                        str(info.get("version", "")),
                        str(item["value"]),
                        option_value_key
                    )
                    if display_value is None and info["source"] == "kyc" and q_id == "6":
                        display_value = option_labels.get(str(item["value"]))
                    if display_value is not None:
                        display_value = display_value.replace("{partner_name}", partner_first_name)
                        display_value = display_value.replace("{customer_name}", customer_first_name)
                        display_value = display_value.replace("{subject_pronoun}", subject_pronoun)
                        display_value = display_value.replace("{object_pronoun}", object_pronoun)
                        display_value = display_value.replace("{be_verb}", be_verb)
                        
                        if display_value == "Owned solely by me":
                            display_value = f"Owned solely by {customer_first_name}"
                        
                        processed_answers.append(display_value)
                    else:
                        processed_answers.append(str(item["value"]))
                else:
                    processed_answers.append("")
            else:
                processed_answers.append("")

        if not processed_answers:
            answer_value: str | list[str] = ""
        elif info["source"] == "kyc" and q_id == "6":
            answer_value = ", ".join(processed_answers)
        elif len(processed_answers) == 1:
            answer_value = processed_answers[0]
        else:
            answer_value = processed_answers

        summary.append({
            key: str(question_text) if question_text is not None else "",
            value: answer_value
        })
    # summary.append({key: "Conflict Level", value: conflict_level})

    # remove empty question from summary along with answer
    # Order summary according to the order of patterns / label mapping
    # There is no .replace method for dicts. Instead, substitute {partner_name} in all values.
    label_map = {
        k: v.replace("{partner_name}", partner_first_name) if isinstance(v, str) else v
        for k, v in label_map.items()
    }
    ordered_labels = [label_map.get(val[-1], "") for val in patterns.values()]
    summary = [item for label in ordered_labels for item in summary if item.get("question") == label and label != ""]
    return {"summary": summary}


def parse_answer(answer) -> str | None:
    try:
        data = json.loads(str(answer))
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return str(data[0].get("value"))
    except (json.JSONDecodeError, TypeError):
        pass
    return None


def get_question_scores_and_results(
    db: Session,
    resolve_id: int,
    question_ids: list[int] | list[str],
) -> dict[str, dict[str, Any]]:
    """
    Get score and result label for each given question identifier in the context of a resolve.

    Uses the same score source as get_result_key (stored in ResolveQuestionAnswers).
    Returns a dict keyed by question id (string) with "score" and "result" per entry.

    Result mapping:
        Score >= 5       : "Amicable"
        4 < Score < 5    : "Low Conflict"
        3 <= Score < 4   : "Medium Conflict"
        2 <= Score < 3   : "High Conflict"
        Score < 2        : "Implacable Hostility"
    """
    question_id_strs = {str(qid) for qid in question_ids}
    if not question_id_strs:
        return {}

    rqa_list = (
        db.query(ResolveQuestionAnswers)
        .join(QuestionAnswers, ResolveQuestionAnswers.question_answer_id == QuestionAnswers.id)
        .filter(
            ResolveQuestionAnswers.resolve_id == resolve_id,
            QuestionAnswers.question_identifier.in_(question_id_strs),
        )
        .all()
    )

    result: dict[str, dict[str, Any]] = {}
    for rqa in rqa_list:
        qid = str(rqa.question_answer.question_identifier)
        score = float(rqa.score)

        if score == 5:
            label = "Amicable"
        elif 4 < score < 5:
            label = "Low Conflict"
        elif 3 < score <= 4:
            label = "Medium Conflict"
        elif 2 < score <= 3:
            label = "High Conflict"
        else:
            label = "Implacable Hostility"

        result[qid] = {
            "score": score,
            "result": label,
        }

    return result


def get_partner_name_client_name(db: Session, engage_id: int) -> tuple[str | None, str | None]:
    """Get the partner name and client name for the engage."""

    question_ids = ["1", "2", "1.1", "1.3", "2.1", "2.3"]
    results = (
        db.query(QuestionAnswers.question_identifier, QuestionAnswers.answer)
        .join(
            EngageQuestionAnswers,
            QuestionAnswers.id == EngageQuestionAnswers.question_answer_id,
        )
        .filter(
            EngageQuestionAnswers.engage_id == engage_id,
            QuestionAnswers.question_identifier.in_(question_ids),
        )
        .all()
    )
    answers = {}
    if results:
        for q_identifier, answer in results:
            answers[str(q_identifier)] = parse_answer(answer)

        if "1" in answers or "2" in answers:
            client_name = answers["1"] if "1" in answers else None
            partner_name = answers["2"] if "2" in answers else None
        else:
            client_name = ""
            partner_name = ""
            if "1.1" in answers:
                client_name = answers["1.1"]
            if "1.3" in answers:
                client_name = client_name + " " + answers["1.3"]
            if "2.1" in answers:
                partner_name = answers["2.1"]
            if "2.3" in answers:
                partner_name = partner_name if partner_name else "" + " " + answers["2.3"] if answers["2.3"] else ""

    return client_name, partner_name


def verify_case_access(db: Session, case_id: int, role_code: str, user_id: int) -> bool:
    """Verify if the user has access to the case.
    Args:
        db: Database session
        case_id: ID of the case
        role_code: Role code of the user
        user_id: ID of the user (customer_id for customer, lawyer_id for lawyer)
    Returns:
        True if the user has access to the case, False otherwise
    """
    case_exists = db.query(Case.id, Case.status).filter(Case.id == case_id)
    if role_code != UserRoleEnum.NAVIGATOR.display_name:
        case_exists = case_exists.filter(Case.status != CaseStatusEnum.ARCHIVED)

    case_exists = case_exists.first()
    if not case_exists:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"success": False, "message": "Case not found"},
        )

    # Perform authorization checks BEFORE loading data
    if role_code == UserRoleEnum.CUSTOMER.display_name:
        # Verify case is assigned to this customer
        customer_has_case = (
            db.query(CaseCustomer)
            .filter(CaseCustomer.case_id == case_id, CaseCustomer.customer_id == user_id)
            .first()
        )

        if not customer_has_case:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Access denied: Case not assigned to this customer",
                },
            )

    elif role_code == UserRoleEnum.LAWYER.display_name:
        # Verify lawyer is assigned to the case OR has a match with the case (and case is not assigned)
        is_assigned = (
            db.query(CaseLawyer)
            .filter(CaseLawyer.case_id == case_id, CaseLawyer.lawyer_id == user_id)
            .first()
        )

        if not is_assigned:
            # Check if lawyer has a match
            has_match = (
                db.query(Match)
                .join(Case, Match.case_id == Case.id)
                .filter(Match.case_id == case_id, Match.lawyer_id == user_id)
                .filter(Case.is_match_confirmed == True)
                .first()
            )

            if not has_match:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail={
                        "success": False,
                        "message": "Access denied: Expert has no match with this case",
                    },
                )

    elif role_code != UserRoleEnum.NAVIGATOR.display_name:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"success": False, "message": "Access denied: Invalid role"},
        )


def get_user_role_info(db: Session, user_id: int) -> tuple[str, str]:
    """Get user role code and name."""
    user_role = db.query(UserRole).filter(UserRole.user_id == user_id).first()
    if not user_role:
        # Default to customer if no role found
        return "Customer", "Customer"

    role_enum = UserRoleEnum.from_id(int(user_role.role_id))
    return role_enum.value, role_enum.display_name


def get_case_details_url(case_id: int) -> str:
    """Get the case details URL for the case."""
    case_id_encrypted = encrypt_id(case_id)
    return f"{settings.FRONTEND_URL}/case/{case_id_encrypted}"

def get_matched_lawyers_by_case_id(
    db: Session,
    case_id: int,
    check_match_confirmed: bool = False
) -> list[MatchedLawyer]:
    """
    Get matched lawyers (id and name only) for a case from the match table.
    Only returns lawyer id and full name (first + last).
    """
    matched_lawyers = (
        db.query(
            Lawyer.id,
            User.first_name,
            User.last_name,
        )
        .join(Match, Lawyer.id == Match.lawyer_id)
        .join(User, Lawyer.user_id == User.id)
        .filter(Match.case_id == case_id)
        .order_by(User.first_name)
        .order_by(User.last_name)
    )
    if check_match_confirmed == True:
        matched_lawyers = matched_lawyers.join(Case, Case.id == Match.case_id
                ).filter(Case.is_match_confirmed == True)
        
    matched_lawyers = matched_lawyers.distinct().all()

    result = []
    for lawyer_id, first_name, last_name in matched_lawyers:
        lawyer_name = f"{first_name or ''} {last_name or ''}".strip()
        result.append(MatchedLawyer(lawyer_id=str(lawyer_id), lawyer_name=lawyer_name))
    return result

def get_match_status(db: Session, case_id: int) -> dict[int, str]:
    """Retrieve all match records for a given case."""
    matches = (
        db.query(Match.lawyer_id, Match.status)
        .filter(Match.case_id == case_id)
        .order_by(Match.id.desc())
        .all()
    )

    return {lawyer_id: status for lawyer_id, status in matches}


def is_missed_case(db: Session, case_id: int, lawyer_id: int) -> bool:
    """
    Check if a case is a missed case for a given lawyer.
    
    A case is considered a "missed case" if:
    - The case is matched to the lawyer (Match exists)
    - The case match is confirmed (Case.is_match_confirmed == True)
    - The case is assigned to a lawyer (Case.is_lawyer_assigned == True)
    - The case is NOT assigned to this specific lawyer
    
    Args:
        db: Database session
        case_id: ID of the case
        lawyer_id: ID of the lawyer
        
    Returns:
        bool: True if the case is a missed case for the lawyer, False otherwise
    """
    # Check if case exists and get its properties
    case = db.query(Case).filter(Case.id == case_id, Case.status != CaseStatusEnum.ARCHIVED).first()
    if not case:
        return False
    
    # Check if case is match confirmed
    if not case.is_match_confirmed:
        return False
    
    # Check if case is assigned to a lawyer
    if not case.is_lawyer_assigned:
        return False
    
    # Check if there's a match between this case and lawyer
    match_exists = db.query(Match).filter(
        and_(
            Match.case_id == case_id,
            Match.lawyer_id == lawyer_id
        )
    ).first() is not None
    
    if not match_exists:
        return False
    
    # Check if the case is NOT assigned to this specific lawyer
    assigned_to_lawyer = db.query(CaseLawyer).filter(
        and_(
            CaseLawyer.case_id == case_id,
            CaseLawyer.lawyer_id == lawyer_id
        )
    ).first() is not None
    
    # It's a missed case if matched but not assigned to this lawyer
    return not assigned_to_lawyer


def get_prompt_template_path(case_type: CaseTypeEnum) -> str:
    """Get the prompt template path for the case type."""
    return f"{settings.CASE_SUMMARY_PROMPT_PATH}/{case_type.name.lower()}.yaml"


# OPTIMIZATION: Cache Lambda client to avoid creating it on every call
_lambda_client = None
from botocore.exceptions import NoCredentialsError
import logging
logger = logging.getLogger(__name__)

def get_lambda_client():
    """Get cached Lambda client or create new one."""
    import boto3
    global _lambda_client
    if _lambda_client is None:
        _lambda_client = boto3.client("lambda")
    return _lambda_client


def invoke_dispatch_event(event_type: EventType, lambda_function_name: str = LambdaFunctionName.NOVA_LAW_API.value, payload: dict = {}, user_id: int | None = None, current_user_id: int | None = None) -> None:
    """Invoke the dispatch event to generate the AI case summary."""

    try:
        event_payload = {
            "event_payload": payload,
            "event_type": event_type,
            "user_id": user_id,
            "current_user_id": current_user_id,
            "action":"run_event"
        }
        lambda_client = get_lambda_client()
        lambda_client.invoke(
            FunctionName=lambda_function_name,
            InvocationType="Event",  # Async - don't wait for response
            Payload=json.dumps(event_payload, default=str).encode("utf-8"),
        )
    except NoCredentialsError:
        logger.warning("AWS credentials not configured, skipping Lambda invocation")
        # Optionally: queue the event for later processing
    except Exception as e:
        logger.error(f"Failed to invoke Lambda function: {e}")
        # Don't fail the entire case_open event


def retrive_resolve_answers(
    db: Session,
    resolve: Resolve,
    questions: list[str],
    customer_name: str | None = None,
    partner_name: str | None = None
) -> dict:
    """Retrieve the answers for the resolve."""
    from app.db.services.resolve import get_resolve_question_answers
    from app.utils.formatters import extract_name_parts
    from app.enums.base import NameExtractionOption

    try:
        name = customer_name if customer_name else None
        partner_name = partner_name if partner_name else None
        questions_dict = {}
        with open(settings.QUESTIONS_FILE_PATH) as f:
            questions_dict = json.load(f)
        
        if not questions_dict:
            raise ValueError("Resolve questions not found") from None # noqa: TRY301

        resolve_answers = {}
        resolve_question_answers = get_resolve_question_answers(db, resolve.id)
        db_answers = {}
        for rqa in resolve_question_answers:
            qa = rqa.question_answer
            q_id = str(qa.question_identifier)
            # Get the version, default to "1" if not set
            version = qa.version or "1"
            # Check if the version exists in the questions
            q_data = {}
            if version in questions_dict[q_id].get("versions", {}):
                q_data = questions_dict[q_id]["versions"][version]
            
            option_dict = {}
            for opt in q_data.get("options", []):
                if isinstance(opt, dict):
                    option_dict.update(opt)  # merge options (flatten)
            answer = json.loads(str(qa.answer)) if qa.answer else []

            # Map selected value(s) to display value(s)
            selected_values = [x["value"] for x in answer]
            display_values = []
            for sv in selected_values:
                if name is None and q_id == "1":
                    name = extract_name_parts(sv, NameExtractionOption.FIRST)
                if partner_name is None and q_id == "2":
                    partner_name = extract_name_parts(sv, NameExtractionOption.FIRST)
                # Find the display value in the options
                if sv in option_dict:
                    display = option_dict[sv].get("value", "")
                else:
                    display = sv
                display_values.append(display)
            formatted_answer = " | ".join(display_values)
            db_answers[q_id] = {
                "answer": formatted_answer
            }
        
        for qid, items in db_answers.items():
            if name and partner_name:
                answer = items["answer"].format(name=name, partner_name=partner_name)
            else:
                answer = items["answer"]
            items["answer"] = answer

        for question in questions:
            if question in db_answers:
                resolve_answers[question] = db_answers[question]
            
        return resolve_answers
    
    except Exception as e:
        logger.exception(f"Error in retrive_resolve_answers: {e}")
        return {}


def retrive_kyc_answers(
    db: Session,
    case_id: int,
    questions: list[str],
    option_key_questions: list[str] = []
) -> dict:
    """Retrieve the formatted answers for KYC questions by case_id.
    
    Args:
        db: Database session
        case_id: The case ID to get KYC answers for
        questions: List of question IDs to retrieve (e.g. ["6", "7"])
    
    Returns:
        Dict with question_id as key and {"answer": "formatted answer"} as value
    """
    from app.db.services.kyc import get_kyc_data_from_db, get_kyc_questions, get_resolve_options_for_kyc
    from app.db.services.resolve import get_resolve_from_case_id

    try:
        data_status, db_data = get_kyc_data_from_db(db, case_id)
        if not data_status or not db_data:
            return {}

        kyc_questions = get_kyc_questions()
        
        # Build db answers map for quick lookup
        db_answers_map = {}
        for d in db_data:
            q_id = str(d.question_identifier)
            db_answers_map[q_id] = json.loads(str(d.answer)) if d.answer else []
        
        # Get resolve options for question 6 (dynamic options)
        resolve_option_dict = {}
        resolve = get_resolve_from_case_id(db, case_id)
        if resolve:
            for opt in get_resolve_options_for_kyc(db, int(resolve.id)):
                if isinstance(opt, dict):
                    resolve_option_dict.update(opt)

        # Build map of "other" follow-up questions (parent_id -> followup_id)
        other_followup_map = {}
        for q_id, q_data in kyc_questions.items():
            version_data = q_data.get("versions", {}).get("1", {})
            for rule in version_data.get("rules", []):
                if rule.get("operator") == "in" and "other" in rule.get("value", []):
                    parent_id = rule.get("identifier")
                    if parent_id:
                        other_followup_map[parent_id] = q_id

        kyc_answers = {}
        
        for question_id in questions:
            q_data = kyc_questions.get(question_id)
            if not q_data:
                continue

            version_data = q_data.get("versions", {}).get("1", {})
            options_list = version_data.get("options", [])

            # Build option dict - question 6 uses resolve options
            option_dict = resolve_option_dict.copy() if question_id == "6" else {}
            for opt in options_list:
                if isinstance(opt, dict):
                    option_dict.update(opt)

            answer = db_answers_map.get(question_id, [])
            if not answer:
                continue

            display_values = []
            followup_id = other_followup_map.get(question_id)

            for ans_item in answer:
                val = ans_item.get("value") if isinstance(ans_item, dict) else ans_item
                if val == "other":
                    # Skip "other" - will use follow-up question answer instead
                    continue
                elif val in option_dict:
                    if question_id in option_key_questions:
                        display = format_option_key(val)
                        display_values.append(display)
                    else:
                        display = option_dict[val] if isinstance(option_dict[val], str) else option_dict[val].get("value", val)
                        display_values.append(display)
                elif val:
                    display_values.append(val.capitalize())

            # Check for "other" follow-up answer (e.g., question 12 for question 6)
            if followup_id and followup_id in db_answers_map:
                followup_answer = db_answers_map[followup_id]
                if followup_answer:
                    followup_val = followup_answer[0].get("value") if isinstance(followup_answer[0], dict) else followup_answer[0]
                    if followup_val:
                        display_values.append(followup_val.capitalize())

            if display_values:
                kyc_answers[question_id] = {"answer": display_values if isinstance(display_values, list) else [display_values]}

        return kyc_answers
    except Exception as e:
        logger.exception(f"Error in retrive_kyc_answers: {e}")
        return {}


def retrive_triage_answers(
    db: Session,
    triage: Triage,
    questions: list[str],
    customer_name: str | None = None,
    partner_name: str | None = None
) -> dict:
    """Retrieve the formatted answers for Triage questions by case.

    Args:
        db: Database session
        case: The case to get triage answers for
        questions: List of question IDs to retrieve (e.g. ["1"])
        customer_name: Optional customer name for placeholder substitution
        partner_name: Optional partner name for placeholder substitution

    Returns:
        Dict with question_id as key and {"answer": "formatted answer"} as value
    """
    from app.db.models.triage_question_answers import TriageQuestionAnswers

    try:
        name = customer_name if customer_name else None
        partner_name = partner_name if partner_name else None

        questions_dict = {}
        with open(settings.TRIAGE_QUESTIONS_FILE_PATH) as f:
            questions_dict = json.load(f)

        if not questions_dict:
            raise ValueError("Triage questions not found") from None  # noqa: TRY301

        db_data = (
            db.query(QuestionAnswers)
            .join(TriageQuestionAnswers, TriageQuestionAnswers.question_answer_id == QuestionAnswers.id)
            .filter(TriageQuestionAnswers.triage_id == triage.id)
            .all()
        )
        if not db_data:
            return {}

        other_followup_map = {}
        for q_id, q_data in questions_dict.items():
            version_data = q_data.get("versions", {}).get("1", {})
            for rule in version_data.get("rules", []):
                if rule.get("operator") == "in" and (
                    "other" in rule.get("value", []) or "some_other" in rule.get("value", [])
                ):
                    parent_id = rule.get("identifier")
                    if parent_id:
                        other_followup_map[parent_id] = q_id

        db_answers_map = {}
        for qa in db_data:
            q_id = str(qa.question_identifier)
            db_answers_map[q_id] = {
                "answer": json.loads(str(qa.answer)) if qa.answer else [],
                "version": qa.version or "1",
            }

        db_answers = {}
        for q_id, qa_data in db_answers_map.items():
            version = qa_data["version"]
            q_data = {}
            if q_id in questions_dict and version in questions_dict[q_id].get("versions", {}):
                q_data = questions_dict[q_id]["versions"][version]

            option_dict = {}
            for opt in q_data.get("options", []):
                if isinstance(opt, dict):
                    option_dict.update(opt)

            answer = qa_data["answer"]
            selected_values = []
            for item in answer:
                if isinstance(item, dict):
                    if "value" in item:
                        selected_values.append(item["value"])
                    elif item:
                        selected_values.append(next(iter(item.values())))
                elif item:
                    selected_values.append(item)

            display_values = []
            followup_id = other_followup_map.get(q_id)
            for sv in selected_values:
                if sv in ("other", "some_other") and followup_id:
                    continue
                if sv in option_dict:
                    opt_val = option_dict[sv]
                    display = opt_val if isinstance(opt_val, str) else opt_val.get("value", sv)
                else:
                    display = sv
                if display:
                    display_values.append(str(display))

            if followup_id and followup_id in db_answers_map:
                followup_answer = db_answers_map[followup_id]["answer"]
                if followup_answer:
                    followup_item = followup_answer[0]
                    followup_val = (
                        followup_item.get("value")
                        if isinstance(followup_item, dict)
                        else followup_item
                    )
                    if followup_val:
                        display_values.append(str(followup_val))

            formatted_answer = " | ".join(display_values)
            if formatted_answer:
                db_answers[q_id] = {"answer": formatted_answer}

        for items in db_answers.values():
            answer = items["answer"]
            if name and partner_name:
                answer = answer.format(name=name, partner_name=partner_name)
            elif name:
                answer = answer.replace("{name}", name)
            elif partner_name:
                answer = answer.replace("{partner_name}", partner_name)
            items["answer"] = answer

        triage_answers = {}
        for question in questions:
            if question in db_answers:
                triage_answers[question] = db_answers[question]

        return triage_answers

    except Exception as e:
        logger.exception(f"Error in retrive_triage_answers: {e}")
        return {}


def format_option_key(val: str) -> str:
    """Format the option key."""
    return val.replace("_", " ").capitalize()

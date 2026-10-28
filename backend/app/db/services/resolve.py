import json

from fastapi import HTTPException, status
from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import settings
from app.core.error_handling import raise_bad_request
from app.db.models import (
    Case,
    CaseLawyer,
    CaseResolve,
    Customer,
    Match,
    Resolve,
    ResolveQuestionAnswers,
    User,
)
from app.enums.base import NameExtractionOption
from app.enums.case import CaseStatusEnum
from app.enums.resolve import ResolveListStatusEnum, ResolveStatusEnum
from app.enums.user_role import UserRoleEnum
from app.schemas.v1.resolve import ResolveCreate, ResolveUpdate
from app.utils.formatters import extract_name_parts


def create_resolve(db: Session, resolve_data: ResolveCreate) -> Resolve:
    """Create a new resolve."""
    db_resolve = Resolve(**resolve_data.dict())
    db.add(db_resolve)
    db.commit()
    db.refresh(db_resolve)
    return db_resolve


def get_resolve_by_id(db: Session, resolve_id: int) -> Resolve | None:
    """Get resolve by ID."""
    return db.query(Resolve).filter(Resolve.id == resolve_id).first()


def get_resolve_by_id_with_relationships(db: Session, resolve_id: int) -> Resolve | None:
    """Get resolve by ID with eagerly loaded relationships."""
    return (
        db.query(Resolve)
        .options(
            joinedload(Resolve.case_resolves).joinedload(CaseResolve.case).joinedload(Case.case_customers)
        )
        .filter(Resolve.id == resolve_id)
        .first()
    )

def get_resolves(db: Session, skip: int = 0, limit: int = 100) -> list[Resolve]:
    """Get all resolves with pagination."""
    return db.query(Resolve).offset(skip).limit(limit).all()


def update_resolve(db: Session, resolve_id: int, resolve_update: ResolveUpdate) -> Resolve | None:
    """Update resolve information."""
    db_resolve = get_resolve_by_id(db, resolve_id)
    if not db_resolve:
        return None

    update_data = resolve_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_resolve, field, value)

    db.commit()
    db.refresh(db_resolve)
    return db_resolve


def delete_resolve(db: Session, resolve_id: int) -> bool:
    """Delete a resolve."""
    db_resolve = get_resolve_by_id(db, resolve_id)
    if not db_resolve:
        return False

    db.delete(db_resolve)
    db.commit()
    return True


def get_resolve_question_answers(db: Session, resolve_id: int) -> list[ResolveQuestionAnswers]:
    """Get resolve question answers."""
    return db.query(ResolveQuestionAnswers).options(joinedload(ResolveQuestionAnswers.question_answer)).filter(ResolveQuestionAnswers.resolve_id == resolve_id).all()


def get_result(resolve: Resolve) -> dict:
    result_reference_id = resolve.result_reference_id
    recommended_approach = resolve.recommended_approach
    result = {}
    """Get resolve result."""
    with open(settings.RESOLVE_RESULT_FILE_PATH) as f:
        result = json.load(f)

    name = getattr(resolve, "customer_name", "") or ""
    partner_name = getattr(resolve, "partner_name", "") or ""
    partner_first_name = extract_name_parts(partner_name, NameExtractionOption.FIRST)

    result_data = {}
    if result_reference_id in result:
        # latest_key = next(iter(result[result_reference_id].keys()))
        latest_key = next(iter(result[result_reference_id].get("versions", {}).keys()))
        result_data = result[result_reference_id].get("versions",{})[latest_key]
        result_data["result_type"] = result_reference_id
        result_data["title"] = result_data.get("title", "")
        summary_template = result_data.get("summary", "")
        summary = summary_template.format(name=name, partner_name=partner_first_name)
        recommendations = result[result_reference_id].get("recommendations", {})
        result_data["recommendations"] = {}
        for key, value in recommendations.items():
            result_data["recommendations"][key] = value.format(name=name, partner_name=partner_first_name)
        result_data["summary"] = summary
        result_data["version"] = result_data.get("version", "")
        affordability_template = result[result_reference_id].get("affordability", "")
        affordability = affordability_template.format(name=name, partner_name=partner_name, partner_first_name=partner_first_name)
        result_data["affordability"] = affordability
        result_data["tags"] = result[result_reference_id].get("tags", [])

        result_data["recommended_approach"] = {}
        if recommended_approach in result:
            r_result = result[recommended_approach].get("versions",{})[latest_key]
            result_data["recommended_approach"]["result_type"] = recommended_approach
            result_data["recommended_approach"]["title"] = r_result.get("title", "")
            summary_template = r_result.get("summary", "")
            summary = summary_template.format(name=name, partner_name=partner_first_name)
            recommendations = resolve.personalised_ai_recommendation
            if recommendations:
                result_data["recommended_approach"]["recommendations"] = recommendations
            else:
                recommendations = result[recommended_approach].get("recommendations", {})
                for key, value in recommendations.items():
                    result_data["recommended_approach"]["recommendations"][key] = value.format(name=name, partner_name=partner_first_name)
            result_data["recommended_approach"]["summary"] = summary
            result_data["recommended_approach"]["version"] = r_result.get("version", "")
            affordability_template = result[recommended_approach].get("affordability", "")
            affordability = affordability_template.format(name=name, partner_name=partner_name, partner_first_name=partner_first_name)
            result_data["recommended_approach"]["affordability"] = affordability
            result_data["recommended_approach"]["tags"] = result[recommended_approach].get("tags", [])

    return result_data

def map_answers(resolve: Resolve, questions: list[dict]) -> tuple[list[ResolveQuestionAnswers], str]:
    """Map answers to resolve questions."""
    info = ""
    if resolve.status == ResolveStatusEnum.COMPLETED:
        maped_questions = get_resolve_answers(resolve, questions)
    else:

        latest_versions = {}
        for q_id, q_data in questions.items():
            version_keys = list(q_data["versions"].keys())
            latest_key = version_keys[0]
            latest_versions[q_id] = latest_key

        resolve_question_answers = resolve.resolve_question_answers
        if resolve_question_answers:
            db_answers_map = {}
            for db_answer in resolve_question_answers:
                db_answers_map[str(db_answer.question_answer.question_identifier)] = str(db_answer.question_answer.version)

            if answered_version_mismatch(latest_versions, db_answers_map):
                info = "Version mismatch, reset resolve"
                maped_questions = get_latest_questions(questions)
                return maped_questions, info


            for db_answer in resolve_question_answers:
                q_id = str(db_answer.question_answer.question_identifier)
                ver = str(db_answer.question_answer.version)
                answer = db_answer.question_answer.answer
                try:
                    answer_dict = json.loads(answer)
                    questions[q_id]["versions"][ver]["answer"] = answer_dict
                except Exception as e:
                    raise_bad_request(message="Invalid answer format: " + str(e))

        maped_questions = get_latest_questions(questions)

    return maped_questions, info


def get_resolve_answers(resolve: Resolve, questions: list[dict]) -> list[ResolveQuestionAnswers]:
    """Get resolve question answers."""

    if resolve.resolve_question_answers:
        for rqa in resolve.resolve_question_answers:
            questions[str(rqa.question_answer.question_identifier)]["versions"][str(rqa.question_answer.version)]["answer"] = json.loads(rqa.question_answer.answer)

    questions = get_latest_questions(questions)
    return questions


def get_latest_questions(questions: list[dict]) -> list[dict]:
    """Get latest questions."""
    result = {}

    for question_id, q_data in questions.items():
        version_keys = list(q_data["versions"].keys())
        latest_key = version_keys[0]
        result[question_id] = dict(q_data["versions"][latest_key])
        result[question_id]["version"] = latest_key
        # attach question_status if it exists
        if "question_status" in q_data:
            result[question_id]["question_status"] = q_data["question_status"]

    return result


def answered_version_mismatch(latest_versions: dict, db_answers_map: dict) -> bool:
    """Check if the version is different from the latest version."""
    for q_id, ver in db_answers_map.items():
        if q_id not in latest_versions:
            return True
        if latest_versions[q_id] != ver:
            return True
    return False


def search_resolve_service(
    db: Session,
    id: int,
    page: int = 1,
    limit: int = 10,
    order_by: str = "created_at",
    order_dir: str = "desc",
    role_code: str | None = None,
    search: str | None = None,
    status: ResolveListStatusEnum | None = None,
) -> tuple[list[Resolve], int]:
    """Search resolves with pagination and ordering."""
    from app.utils.validators import validate_order_params

    # Validate order_by and order_dir parameters
    allowed_order_fields = {
        "id",
        "resolve_date",
        "user_id",
        "result_reference_id",
        "status",
        "created_at",
        "updated_at",
    }
    validate_order_params(order_by, order_dir, allowed_order_fields)

    # Calculate offset
    offset = (page - 1) * limit

    # Build base query with all necessary joins to avoid N+1 queries
    # Join Customer and User for searching by user name/email
    base_query = db.query(Resolve).outerjoin(
        Customer, Resolve.customer_id == Customer.id
    ).outerjoin(
        User, Customer.user_id == User.id
    ).options(
        selectinload(Resolve.customer).selectinload(Customer.user),
        selectinload(Resolve.case_resolves).selectinload(CaseResolve.case)
    )    

    # Track which tables are already joined
    case_resolve_joined = False

    # Apply role-based filtering
    if role_code == UserRoleEnum.NAVIGATOR.display_name:
        query = base_query
    elif role_code == UserRoleEnum.CUSTOMER.display_name:
        query = base_query.filter(Resolve.customer_id == id)
    elif role_code == UserRoleEnum.LAWYER.display_name:
        # Get cases where the lawyer is assigned via case_lawyer table
        lawyer_assigned_cases = db.query(CaseLawyer.case_id).filter(CaseLawyer.lawyer_id == id).subquery()

        # Get cases from match table where the lawyer is involved and match is confirmed
        match_cases = db.query(Match.case_id).join(
            Case, Match.case_id == Case.id
        ).filter(
            Match.lawyer_id == id,
            Case.is_match_confirmed == True
        ).subquery()

        # Get resolves that are linked to cases in case_resolve
        # AND either:
        # 1. The case is assigned to the lawyer in case_lawyer table, OR
        # 2. The case is in match table with confirmed match
        query = base_query.join(CaseResolve, Resolve.id == CaseResolve.resolve_id).filter(
            CaseResolve.case_id.in_(
                db.query(lawyer_assigned_cases.c.case_id).union(
                    db.query(match_cases.c.case_id)
                )
            )
        )
        case_resolve_joined = True
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Invalid role code"},
        )

    # Apply search filter
    if search:
        search = search.strip()
        query = query.filter(
            or_(
                # Search in Resolve table (for unregistered customers)
                Resolve.customer_email.ilike(f"%{search}%"),
                Resolve.customer_name.ilike(f"%{search}%"),
                # Search in User table (for registered customers via Customer)
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                (func.trim(User.first_name) + " " + func.trim(User.last_name)).ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%")
            )
        )

    # Apply status filter
    if status and status.value != ResolveListStatusEnum.ALL:
        if status.value == ResolveListStatusEnum.IN_PROGRESS:
            query = query.filter(Resolve.status == ResolveStatusEnum.IN_PROGRESS)
        elif status.value == ResolveListStatusEnum.COMPLETED:
            # Filter for completed resolves that are NOT linked to any case
            if not case_resolve_joined:
                query = query.outerjoin(CaseResolve, Resolve.id == CaseResolve.resolve_id)
                case_resolve_joined = True
            query = query.filter(
                Resolve.status == ResolveStatusEnum.COMPLETED,
                CaseResolve.resolve_id.is_(None)
            )
        elif status.value == ResolveListStatusEnum.MOVING_FORWARD:
            # Filter for resolves that have a linked case
            if not case_resolve_joined:
                query = query.join(CaseResolve, Resolve.id == CaseResolve.resolve_id, isouter=False)
                case_resolve_joined = True

    # Hide records whose linked case is archived.
    # In progress records are not linked to a case, so this applies to All, Completed, and Moving forward.
    if not status or status.value != ResolveListStatusEnum.IN_PROGRESS:
        archived_case_link = (
            db.query(CaseResolve.resolve_id)
            .join(Case, Case.id == CaseResolve.case_id)
            .filter(
                CaseResolve.resolve_id == Resolve.id,
                Case.status == CaseStatusEnum.ARCHIVED,
            )
            .exists()
        )
        query = query.filter(~archived_case_link)

    # Add ordering
    order_column = getattr(Resolve, order_by)
    if order_dir.lower() == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # Get total count
    total_count = query.count()

    # Apply pagination
    resolves = query.offset(offset).limit(limit).all()

    return resolves, total_count


def get_resolve_from_case_id(db: Session, case_id: int) -> Resolve | None:
    """Get resolve from case ID."""
    return db.query(Resolve).join(CaseResolve, Resolve.id == CaseResolve.resolve_id).filter(CaseResolve.case_id == case_id).first()


def _format_options_list(options_list: list) -> list[str] | None:
    """Format options list to a list of option strings."""
    if not options_list:
        return None
    
    option_texts = []
    for opt in options_list:
        if isinstance(opt, dict):
            # Extract display values from option dict
            for _, value in opt.items():
                if isinstance(value, dict) and "value" in value:
                    option_texts.append(value["value"])
                else:
                    option_texts.append(str(value))
        else:
            option_texts.append(str(opt))
    
    return option_texts if option_texts else None


def format_resolve_question_answers(db: Session, resolve: Resolve) -> list[dict]:
    """Format resolve question answers."""

    """Get resolve questions."""
    questions = {}
    try:
        with open(settings.QUESTIONS_FILE_PATH) as f:
            questions = json.load(f)
    except Exception as e:
        raise ValueError("Failed to load resolve questions") from e # noqa: TRY301
    if not questions:
        raise ValueError("Resolve questions not found") # noqa: TRY301
    # Get case summary data in Q&A format
    resolve_question_answers = get_resolve_question_answers(db, resolve.id)
    details = []
    name = None
    partner_name = None
    for rqa in resolve_question_answers:
        qa = rqa.question_answer
        q_id = str(qa.question_identifier)
        if q_id in questions:
            # Get the version, default to "1" if not set
            version = qa.version or "1"
            # Check if the version exists in the questions
            if version in questions[q_id].get("versions", {}):
                q_versions = questions[q_id]["versions"][version]
                question_text = q_versions.get("question", "")
                answer = qa.answer or ""
                # Append answer as comma-separated string
                if answer:
                    # INSERT_YOUR_CODE
                    # If the answer is in the specified json answer format (list of dicts with "value" keys), convert to readable text
                    formatted_answer = None
                    try:
                        answer_json = json.loads(answer)
                        if isinstance(answer_json, list) and all(isinstance(x, dict) and "value" in x for x in answer_json):
                            # Get all possible options for this question version
                            # Options could be a list of dicts
                            option_dict = {}
                            for opt in q_versions.get("options", []):
                                if isinstance(opt, dict):
                                    option_dict.update(opt)  # merge options (flatten)
                            # Map selected value(s) to display value(s)
                            selected_values = [x["value"] for x in answer_json]
                            display_values = []
                            for sv in selected_values:
                                # Find the display value in the options
                                if sv in option_dict:
                                    display = option_dict[sv].get("value", "")
                                else:
                                    if str(int(q_id)) == "1":
                                        name = extract_name_parts(sv, NameExtractionOption.FIRST)
                                        display = name
                                    elif str(int(q_id)) == "2":
                                        partner_name = extract_name_parts(sv, NameExtractionOption.FIRST)
                                        display = partner_name                                   
                                    else:
                                        display = sv
                                display_values.append(display)
                            formatted_answer = " | ".join(display_values)
                        else:
                            # fallback to original answer
                            formatted_answer = answer
                    except Exception:
                        # fallback to original answer if parsing fails
                        formatted_answer = answer
                    
                    if formatted_answer:  # Only add if answer is not empty
                        # Get options list if available
                        options_list = q_versions.get("options", [])
                        formatted_options = _format_options_list(options_list)
                        
                        item = {
                            "question": question_text,
                            "answer": formatted_answer
                        }
                        if formatted_options:
                            item["options"] = formatted_options
                        details.append(item)

    # Replace placeholders if at least one name is available
    if partner_name or name:
        # Replace "{partner_name}" and "{name}" in both question and answer text
        formatted_details = []
        for item in details:
            question = item.get("question", "")
            answer = item.get("answer", "")
            options = item.get("options")
            
            # Replace placeholders only if the corresponding name exists
            if isinstance(question, str):
                if partner_name:
                    question = question.replace("{partner_name}", str(partner_name))
                if name:
                    question = question.replace("{name}", str(name))
            if isinstance(answer, str):
                if partner_name:
                    answer = answer.replace("{partner_name}", str(partner_name))
                if name:
                    answer = answer.replace("{name}", str(name))
            if options and isinstance(options, list):
                # Replace placeholders in each option string only if the corresponding name exists
                if partner_name:
                    options = [opt.replace("{partner_name}", str(partner_name)) if isinstance(opt, str) else opt for opt in options]
                if name:
                    options = [opt.replace("{name}", str(name)) if isinstance(opt, str) else opt for opt in options]
            
            if answer:  # Only add if answer is not empty
                formatted_item = {
                    "question": question,
                    "answer": answer
                }
                if options:
                    formatted_item["options"] = options
                formatted_details.append(formatted_item)
        return formatted_details
    return details


def get_result_title(resolve: Resolve) -> str | None:
    """Get resolve result title."""

    try:
        resolve_result = None
        with open(settings.RESOLVE_RESULT_FILE_PATH) as f:
            resolve_result = json.load(f)
        
        if not resolve_result:
            return None

        result_reference_id = resolve.result_reference_id
        if result_reference_id in resolve_result:
            latest_version = next(iter(resolve_result[result_reference_id].get("versions", {}).keys()))

            return resolve_result[result_reference_id].get("versions",{})[latest_version].get("title", "")
        return None
    except Exception:
        return None
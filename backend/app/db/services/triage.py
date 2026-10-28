import json
from typing import Any

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from app.core.config import settings
from app.db.models import (
    Case,
    CaseLawyer,
    CaseTriage,
    Customer,
    Match,
    QuestionAnswers,
    Triage,
    TriageQuestionAnswers,
    User,
)
from app.db.services.auth import get_user_by_email
from app.db.services.general import validate_answer_text
from app.schemas.v1.triage import GetTriageRequest
from app.enums.case import CaseStatusEnum
from app.enums.triage import TriageListStatusEnum, TriageStatusEnum
from app.enums.user_role import UserRoleEnum
from app.schemas.v1.customer import CustomerInfo
from app.schemas.v1.triage import CaseInfo, SubmitTriageRequest, UpdateTriageRequest
from app.utils.formatters import format_case_number
from app.utils.validators import validate_email_format


def get_triage_by_id(db: Session, triage_id: int) -> Triage | None:
    """Get triage by ID."""
    return db.query(Triage).filter(Triage.id == triage_id).first()


def get_triage_from_case_id(db: Session, case_id: int) -> Triage | None:
    """Get triage from case ID."""
    return (
        db.query(Triage)
        .join(CaseTriage, Triage.id == CaseTriage.triage_id)
        .filter(CaseTriage.case_id == case_id)
        .first()
    )


def create_triage(db: Session, customer_email: str) -> Triage:
    """Create a new triage linked to the customer email."""
    triage = Triage(
        customer_email=customer_email,
        status=TriageStatusEnum.IN_PROGRESS,
        questions_answered=0,
    )
    db.add(triage)
    db.commit()
    db.refresh(triage)
    return triage


def get_triage_questions() -> dict:
    """Get the triage questions from the file."""
    questions: dict[str, Any] = {}
    try:
        with open(settings.TRIAGE_QUESTIONS_FILE_PATH) as f:
            questions = json.load(f)
        return questions
    except Exception:
        message = {
            "success": False,
            "message": "Error reading triage questions from file"
        }
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message) from None


def get_triage_data_from_db(db: Session, triage_id: int) -> tuple[bool, list[QuestionAnswers]]:
    """Get the triage data from the database."""
    db_data = (
        db.query(QuestionAnswers)
        .join(TriageQuestionAnswers, TriageQuestionAnswers.question_answer_id == QuestionAnswers.id)
        .filter(TriageQuestionAnswers.triage_id == triage_id)
        .all()
    )
    return True, db_data


def _latest_version_key(qdata: dict) -> str:
    """Return the latest version key for a question."""
    return next(iter(qdata.get("versions", {}).keys()))


def get_answer_mapped_data(db_data: list[QuestionAnswers], questions: dict) -> dict:
    """Map stored answers onto triage questions."""
    try:
        db_answers = {
            str(data.question_identifier): {
                "answer": json.loads(str(data.answer)) if data.answer else [],
                "version": data.version,
            }
            for data in db_data
        }

        result = {}
        for qid, qdata in questions.items():
            versions = qdata.get("versions", {})
            if qid in db_answers and str(db_answers[qid]["version"]) in versions:
                current_version_key = str(db_answers[qid]["version"])
            else:
                current_version_key = next(iter(versions.keys()))
            current_version_data = versions.get(current_version_key, {})

            merged = {**current_version_data}
            merged["answer"] = db_answers.get(qid, {}).get("answer", [])
            merged["question_status"] = qdata.get("question_status")
            merged["version"] = current_version_key
            result[qid] = merged

        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from None


def get_triage_data(db: Session, triage_id: int) -> dict:
    """Get the triage questions with mapped answers for the triage."""
    questions = get_triage_questions()
    data_status, db_data = get_triage_data_from_db(db, triage_id)
    if data_status is False:
        message = {
            "success": False,
            "message": "Error collecting triage data from database"
        }
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    if len(db_data) == 0:
        result = {}
        for qid, qdata in questions.items():
            latest_version_key = _latest_version_key(qdata)
            latest_version_data = qdata.get("versions", {}).get(latest_version_key)
            merged = {**latest_version_data}
            merged["question_status"] = qdata.get("question_status")
            merged["version"] = latest_version_key
            result[qid] = merged
        return result

    return get_answer_mapped_data(db_data, questions)


def get_triage_by_customer_email(db: Session, customer_email: str) -> Triage | None:
    """
    Get the best matching triage for a customer email.

    Preference:
    1. Latest completed triage
    2. Latest in-progress triage that already has answers
    3. Latest in-progress triage
    """
    email = customer_email.lower()
    completed = (
        db.query(Triage)
        .filter(
            func.lower(Triage.customer_email) == email,
            Triage.status == TriageStatusEnum.COMPLETED,
        )
        .order_by(Triage.id.desc())
        .first()
    )
    if completed is not None:
        return completed

    with_answers = (
        db.query(Triage)
        .filter(
            func.lower(Triage.customer_email) == email,
            Triage.status == TriageStatusEnum.IN_PROGRESS,
            Triage.questions_answered.isnot(None),
            Triage.questions_answered > 0,
        )
        .order_by(Triage.id.desc())
        .first()
    )
    if with_answers is not None:
        return with_answers

    return (
        db.query(Triage)
        .filter(
            func.lower(Triage.customer_email) == email,
            Triage.status == TriageStatusEnum.IN_PROGRESS,
        )
        .order_by(Triage.id.desc())
        .first()
    )


def get_completed_triage_customer_and_case(
    db: Session, triage: Triage
) -> tuple[CustomerInfo | None, CaseInfo | None]:
    """Build customer_info and case_info for a completed triage, else (None, None)."""
    if triage.status != TriageStatusEnum.COMPLETED:
        return None, None

    customer_info = None
    case_info = None

    if triage.customer_id is not None:
        customer = (
            db.query(Customer)
            .filter(Customer.id == triage.customer_id)
            .first()
        )
        if customer and customer.user:
            user: User = customer.user
            customer_info = CustomerInfo(
                first_name=str(user.first_name),
                last_name=str(user.last_name),
                email=str(user.email),
                phone=str(user.phone) if user.phone else None,
                customer_id=str(customer.id),
            )

    case_triage = (
        db.query(CaseTriage)
        .filter(CaseTriage.triage_id == triage.id)
        .first()
    )
    if case_triage is not None:
        case = db.query(Case).filter(Case.id == case_triage.case_id).first()
        if case is not None:
            case_info = CaseInfo(
                case_id=str(case.id),
                case_no=format_case_number(str(case.case_no)),
                case_type=case.case_type.value if case.case_type else None,
                priority=case.priority.value if case.priority else None,
                start_date=case.start_date,  # type: ignore[arg-type]
                status=case.status.value,
                created_at=case.created_at,  # type: ignore[arg-type]
                updated_at=case.updated_at,  # type: ignore[arg-type]
                is_kyc_completed=case.is_kyc_completed,
            )

    return customer_info, case_info


def start_triage_session(
    db: Session, request: GetTriageRequest, current_user: User | None = None
) -> tuple[int, TriageStatusEnum, dict, CustomerInfo | None, CaseInfo | None]:
    """
    Start or resume a triage session for the email.

    - Completed triage: return mapped answers plus customer/case info.
    - Existing in-progress triage: resume it and map any saved answers.
    - Otherwise create a new triage.
    """

    if request.customer_email is not None:
        email = request.customer_email.strip().lower()
        if not validate_email_format(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"success": False, "message": "Invalid email format"}],
            )

    if request.triage_id:
        triage = get_triage_by_id(db, int(request.triage_id))
        if triage is not None:
            question_data = get_triage_data(db, int(triage.id))
            if triage.status == TriageStatusEnum.COMPLETED:
                customer_info, case_info = get_completed_triage_customer_and_case(
                    db, triage
                )
                return int(triage.id), triage.status, question_data, customer_info, case_info
            # In-progress: return mapped answers when available; customer/case stay null
            return int(triage.id), triage.status, question_data, None, None

    existing_triage = get_triage_by_customer_email(db, email)
    if existing_triage is not None:
        question_data = get_triage_data(db, int(existing_triage.id))
        if existing_triage.status == TriageStatusEnum.COMPLETED:
            if current_user is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=[{"success": False, "message": "You are not authorized to view this triage"}],
                )
            # User is logged in, check role-based access
            user_roles = [user_role.role_id for user_role in current_user.user_roles]
            # Check for navigator
            if UserRoleEnum.NAVIGATOR.id in user_roles:
                pass  # Navigators can access any triage
            # Check for customer
            elif UserRoleEnum.CUSTOMER.id in user_roles:
                if current_user.id != existing_triage.user_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=[{"success": False, "message": "You are not authorized to view this triage"}],
                    )
            customer_info, case_info = get_completed_triage_customer_and_case(
                db, existing_triage
            )
            return int(existing_triage.id), existing_triage.status, question_data, customer_info, case_info
        # In-progress: return mapped answers when available; customer/case stay null
        return int(existing_triage.id), existing_triage.status, question_data, None, None

    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=[{"success": False, "message": "User with this email already exists"}],
        )

    triage = create_triage(db, email)
    question_data = get_triage_data(db, int(triage.id))
    return int(triage.id), triage.status, question_data, None, None


def format_request_answers(request: UpdateTriageRequest) -> dict:
    """Format the request answers."""
    request_answers = {}
    for req in request.answers:
        qid = req.question_identifier
        ans_list = req.answer if isinstance(req.answer, list) else [req.answer]
        ans_dicts = [vars(ans) for ans in ans_list]
        request_answers[qid] = {"answer": ans_dicts}
    return request_answers


def _answer_values_from_payload(answer: list) -> list:
    """Extract answer values from a list of answer dicts."""
    return [next(iter(d.values())) for d in answer]


def _parent_answer_values(parent_id: str, request_answers: dict, db_data_map: dict) -> list:
    """Get parent answer values from the request first, then the database."""
    if parent_id in request_answers:
        return _answer_values_from_payload(request_answers.get(parent_id, {}).get("answer", []))
    if parent_id in db_data_map:
        answers = json.loads(str(db_data_map[parent_id].answer)) if db_data_map[parent_id].answer else []
        return _answer_values_from_payload(answers)
    return []


def check_is_required_for_conditional(
    parent_id: str,
    request_answers: dict,
    db_data_map: dict,
    required_answer_values: list,
) -> bool:
    """Check if the conditional question is required by parent value."""
    db_answer_values = _parent_answer_values(parent_id, request_answers, db_data_map)
    return any(value in required_answer_values for value in db_answer_values)


def check_required_triage_answers(
    request_answers: dict,
    questions: dict,
    db_data: list[QuestionAnswers],
    update_flag: bool,
) -> tuple[bool, list[dict]]:
    """Check if the submitted triage answers are valid."""
    db_data_map = {str(data.question_identifier): data for data in db_data}
    success = True
    err_list = []
    required_questions = {}

    for qid, qdata in questions.items():
        latest_version_key = _latest_version_key(qdata)
        latest_version_data = qdata.get("versions", {}).get(latest_version_key, {})
        if latest_version_data.get("required") is True and latest_version_data.get("question_type") != "conditional":
            required_questions[qid] = {"version": latest_version_key}

    if update_flag is False:
        for qid in required_questions:
            if qid not in request_answers and qid not in db_data_map:
                err_list.append({"success": False, "message": f"Question {qid} is required"})

    for qid in request_answers:
        if qid not in questions:
            err_list.append({"success": False, "message": f"Question identifier: {qid} is not valid"})
            continue

        qdata = questions[qid].get("versions", {})
        latest_version_key = next(iter(qdata.keys()))
        question_data = qdata.get(latest_version_key, {})
        question_options = question_data.get("options", [])
        question_type = question_data.get("question_type")
        is_required = question_data.get("required")
        input_type = question_data.get("input_type")

        answer = request_answers.get(qid, {}).get("answer", [])
        answer_values = _answer_values_from_payload(answer)

        if question_type == "conditional" and is_required:
            rules = question_data.get("rules", [])
            if rules:
                parent_id = rules[0].get("identifier")
                required_answer_values = rules[0].get("value") or []
                is_required = check_is_required_for_conditional(
                    parent_id, request_answers, db_data_map, required_answer_values
                )

        if question_options:
            if is_required and not answer_values:
                err_list.append({"success": False, "message": f"Question {qid} is required"})
                continue
            option_keys = [next(iter(d.keys())) for d in question_options]
            is_valid = all(a in option_keys for a in answer_values)
            if answer_values and not is_valid:
                err_list.append({"success": False, "message": f"Question {qid} : Invalid answer"})
        elif is_required and not answer_values:
            err_list.append({"success": False, "message": f"Question {qid} is required"})
            continue

        if input_type in ("text", "textarea"):
            answer_text = answer_values[0] if answer_values else None
            min_length = question_data.get("min_length") or 0
            max_length = question_data.get("max_length") or 500
            is_valid, error = validate_answer_text(answer_text, is_required, min_length, max_length)
            if not is_valid:
                err_list.append({
                    "success": False,
                    "message": f"Question {qid} Version: {latest_version_key}, {error}",
                })

    if len(err_list) > 0:
        success = False
    return success, err_list


def bulk_update_triage_question_answers(db: Session, update_list: list[dict]) -> None:
    """Bulk update triage question answers."""
    db.bulk_update_mappings(QuestionAnswers, update_list)  # type: ignore
    tqa_list = []
    for qa in update_list:
        tqa_object = qa.get("tqa_object")
        if tqa_object is not None:
            tqa_list.append({
                "id": int(tqa_object.id) if tqa_object.id is not None else None,
                "question_answer_id": int(qa.get("id")) if qa.get("id") is not None else None,  # type: ignore
            })
    db.bulk_update_mappings(TriageQuestionAnswers, tqa_list)  # type: ignore
    db.commit()


def bulk_create_triage_question_answers(db: Session, triage_id: int, create_list: list[dict]) -> None:
    """Bulk create triage question answers."""
    question_answer_objects = []
    for qa_data in create_list:
        qa_obj = QuestionAnswers(
            version=qa_data.get("version"),
            answer=qa_data.get("answer"),
            question_identifier=qa_data.get("question_identifier"),
            question_order=qa_data.get("question_order"),
        )
        question_answer_objects.append(qa_obj)

    db.add_all(question_answer_objects)
    db.flush()

    tqa_list = []
    for i in range(len(create_list)):
        tqa_list.append(TriageQuestionAnswers(
            triage_id=triage_id,
            question_answer_id=question_answer_objects[i].id,
            score=0.0,
        ))
    db.add_all(tqa_list)
    db.commit()


def bulk_delete_triage_question_answers(db: Session, delete_map: dict) -> None:
    """Bulk delete triage question answers."""
    triage_question_answer_ids = []
    question_answer_ids = []
    for _identifier, data in delete_map.items():
        question_answer_ids.append(data.get("question_answer_id"))
        triage_question_answer_ids.append(data.get("triage_question_answer_id"))

    db.query(TriageQuestionAnswers).filter(TriageQuestionAnswers.id.in_(triage_question_answer_ids)).delete()
    db.query(QuestionAnswers).filter(QuestionAnswers.id.in_(question_answer_ids)).delete()
    db.commit()


def save_triage_answers(
    db: Session,
    triage_id: int,
    request_answers: dict,
    db_data: list[QuestionAnswers],
    questions: dict,
) -> bool:
    """Save the triage answers."""
    question_version_map = {}
    for qid, qdata in questions.items():
        latest_version_key = _latest_version_key(qdata)
        latest_version_data = qdata.get("versions", {}).get(latest_version_key, {})
        question_version_map[qid] = {
            "version": latest_version_key,
            "question_order": latest_version_data.get("question_order"),
        }

    update_list = []
    create_list = []
    db_data_map = {}
    for data in db_data or []:
        tqa = data.triage_question_answers[0]
        db_data_map[str(data.question_identifier)] = {
            "answer": data.answer,
            "ans_object": data,
            "tqa_object": tqa,
        }

    for qid, data in request_answers.items():
        if str(qid) not in question_version_map:
            continue
        if str(qid) in db_data_map:
            tqa_obj = db_data_map[str(qid)].get("tqa_object")
            update_list.append({
                "id": int(db_data_map[str(qid)].get("ans_object").id),
                "answer": json.dumps(jsonable_encoder(data.get("answer"))),
                "version": question_version_map[str(qid)].get("version"),
                "tqa_object": tqa_obj,
            })
        else:
            create_list.append({
                "question_identifier": qid,
                "version": question_version_map[str(qid)].get("version"),
                "answer": json.dumps(jsonable_encoder(data.get("answer"))),
                "question_order": int(question_version_map[str(qid)].get("question_order"))
                if question_version_map[str(qid)].get("question_order") is not None
                else None,  # type: ignore
            })

    if update_list:
        bulk_update_triage_question_answers(db, update_list)

    if create_list:
        bulk_create_triage_question_answers(db, triage_id, create_list)

    triage = db.query(Triage).filter(Triage.id == triage_id).first()
    if triage:
        triage.questions_answered = (
            db.query(TriageQuestionAnswers)
            .filter(TriageQuestionAnswers.triage_id == triage_id)
            .count()
        )
        db.commit()

    return True


def submit_triage_data(
    db: Session,
    request: UpdateTriageRequest | SubmitTriageRequest,
    update_flag: bool = True,
) -> tuple[bool, int]:
    """Update triage answers for the given triage."""
    triage_id = int(request.triage_id)
    triage = get_triage_by_id(db, triage_id)
    if triage is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"success": False, "message": "Triage not found"}],
        )

    # if triage.status == TriageStatusEnum.COMPLETED:
    #     raise HTTPException(
    #         status_code=status.HTTP_409_CONFLICT,
    #         detail=[{"success": False, "message": "Triage is already completed"}],
    #     )

    if not request.answers:
        return True, triage_id

    questions = get_triage_questions()
    data_status, db_data = get_triage_data_from_db(db, triage_id)
    if data_status is False:
        message = {
            "success": False,
            "message": "Error collecting triage data from database"
        }
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    request_answers = format_request_answers(request)
    valid, error_list = check_required_triage_answers(request_answers, questions, db_data, update_flag)
    if valid is False:
        if error_list:
            error_messages = [str(error.get("message")) for error in error_list if error and error.get("message")]
            errors_str = ", ".join(error_messages)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors_str)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_list)

    result = save_triage_answers(db, triage_id, request_answers, db_data, questions)
    if result is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Error in saving triage answers"},
        )

    return True, triage_id


def _has_non_empty_answer(answer_payload: list | None) -> bool:
    """Return True when the answer list has at least one non-empty value."""
    if not answer_payload:
        return False
    for item in answer_payload:
        if isinstance(item, dict):
            value = next(iter(item.values()), None)
            if value is not None and str(value).strip() != "":
                return True
    return False


def validate_triage_completion(db: Session, triage_id: int) -> None:
    """Validate that all required triage questions have been answered."""
    questions = get_triage_questions()
    _, db_data = get_triage_data_from_db(db, triage_id)
    db_data_map = {str(data.question_identifier): data for data in db_data}
    answer_map: dict[str, list] = {}
    for qid, data in db_data_map.items():
        answer_map[qid] = json.loads(str(data.answer)) if data.answer else []

    missing = []
    for qid, qdata in questions.items():
        latest_version_key = _latest_version_key(qdata)
        question_data = qdata.get("versions", {}).get(latest_version_key, {})
        is_required = question_data.get("required") is True
        question_type = question_data.get("question_type")

        if question_type == "conditional":
            rules = question_data.get("rules", [])
            if not rules:
                continue
            parent_id = rules[0].get("identifier")
            required_answer_values = rules[0].get("value") or []
            parent_answers = answer_map.get(str(parent_id), [])
            parent_values = _answer_values_from_payload(parent_answers)
            is_required = is_required and any(value in required_answer_values for value in parent_values)

        if not is_required:
            continue

        if not _has_non_empty_answer(answer_map.get(qid)):
            missing.append(qid)

    if missing:
        missing_str = ", ".join(missing)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"success": False, "message": f"Triage is incomplete. Missing answers for questions: {missing_str}"}],
        )


def mark_triage_completed(db: Session, triage: Triage) -> Triage:
    """Mark the triage as completed."""
    triage.status = TriageStatusEnum.COMPLETED
    db.flush()
    return triage


def split_customer_name(customer_name: str) -> tuple[str, str]:
    """Split a full customer name into first and last name parts."""
    parts = customer_name.strip().split()
    if not parts:
        return ".", "."
    if len(parts) == 1:
        return parts[0], "."
    return parts[0], " ".join(parts[1:])


def search_triage_service(
    db: Session,
    id: int,
    page: int = 1,
    limit: int = 10,
    order_by: str = "created_at",
    order_dir: str = "desc",
    role_code: str | None = None,
    search: str | None = None,
    status: TriageListStatusEnum | None = None,
) -> tuple[list[Triage], int]:
    """Search triages with pagination and ordering."""
    from app.utils.validators import validate_order_params

    allowed_order_fields = {
        "id",
        "user_id",
        "customer_id",
        "customer_email",
        "status",
        "questions_answered",
        "created_at",
        "updated_at",
    }
    validate_order_params(order_by, order_dir, allowed_order_fields)

    offset = (page - 1) * limit

    base_query = (
        db.query(Triage)
        .outerjoin(Customer, Triage.customer_id == Customer.id)
        .outerjoin(User, Customer.user_id == User.id)
        .options(
            selectinload(Triage.customer).selectinload(Customer.user),
            selectinload(Triage.case_triages).selectinload(CaseTriage.case),
        )
    )

    case_triage_joined = False

    if role_code == UserRoleEnum.NAVIGATOR.display_name:
        query = base_query
    elif role_code == UserRoleEnum.CUSTOMER.display_name:
        query = base_query.filter(Triage.customer_id == id)
    elif role_code == UserRoleEnum.LAWYER.display_name:
        lawyer_assigned_cases = (
            db.query(CaseLawyer.case_id).filter(CaseLawyer.lawyer_id == id).subquery()
        )
        match_cases = (
            db.query(Match.case_id)
            .join(Case, Match.case_id == Case.id)
            .filter(Match.lawyer_id == id, Case.is_match_confirmed == True)  # noqa: E712
            .subquery()
        )
        query = base_query.join(CaseTriage, Triage.id == CaseTriage.triage_id).filter(
            CaseTriage.case_id.in_(
                db.query(lawyer_assigned_cases.c.case_id).union(
                    db.query(match_cases.c.case_id)
                )
            )
        )
        case_triage_joined = True
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "Invalid role code"},
        )

    if search:
        search = search.strip()
        query = query.filter(
            or_(
                Triage.customer_email.ilike(f"%{search}%"),
                User.first_name.ilike(f"%{search}%"),
                User.last_name.ilike(f"%{search}%"),
                (func.trim(User.first_name) + " " + func.trim(User.last_name)).ilike(
                    f"%{search}%"
                ),
                User.email.ilike(f"%{search}%"),
            )
        )

    if status and status.value != TriageListStatusEnum.ALL:
        if status.value == TriageListStatusEnum.IN_PROGRESS:
            query = query.filter(Triage.status == TriageStatusEnum.IN_PROGRESS)
        elif status.value == TriageListStatusEnum.COMPLETED:
            if not case_triage_joined:
                query = query.outerjoin(CaseTriage, Triage.id == CaseTriage.triage_id)
                case_triage_joined = True
            query = query.filter(
                Triage.status == TriageStatusEnum.COMPLETED,
                CaseTriage.triage_id.is_(None),
            )
        elif status.value == TriageListStatusEnum.MOVING_FORWARD:
            if not case_triage_joined:
                query = query.join(
                    CaseTriage, Triage.id == CaseTriage.triage_id, isouter=False
                )
                case_triage_joined = True

    # Hide records whose linked case is archived.
    # In progress records are not linked to a case, so this applies to All, Completed, and Moving forward.
    if not status or status.value != TriageListStatusEnum.IN_PROGRESS:
        archived_case_link = (
            db.query(CaseTriage.triage_id)
            .join(Case, Case.id == CaseTriage.case_id)
            .filter(
                CaseTriage.triage_id == Triage.id,
                Case.status == CaseStatusEnum.ARCHIVED,
            )
            .exists()
        )
        query = query.filter(~archived_case_link)

    order_column = getattr(Triage, order_by)
    if order_dir.lower() == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    total_count = query.count()
    triages = query.offset(offset).limit(limit).all()
    return triages, total_count


def _format_triage_options_list(options_list: list) -> list[str] | None:
    """Format triage options list to a list of option strings."""
    if not options_list:
        return None

    option_texts = []
    for opt in options_list:
        if isinstance(opt, dict):
            for _, value in opt.items():
                if isinstance(value, dict) and "value" in value:
                    option_texts.append(value["value"])
                else:
                    option_texts.append(str(value))
        else:
            option_texts.append(str(opt))

    return option_texts if option_texts else None


def format_triage_answers(
    db: Session,
    triage: Triage,
    customer_name: str | None = None,
) -> list[dict]:
    """Format the triage answers.

    Unlike KYC, names are not collected from questions. The customer name is
    passed in so any ``{name}`` placeholders in question, answer, or option
    text can be substituted.
    """
    triage_data = get_triage_data(db, int(triage.id))
    formatted_triage_answers = []

    for _qid, items in triage_data.items():
        option_dict = {}
        for opt in items.get("options", []):
            if isinstance(opt, dict):
                option_dict.update(opt)

        question_text = items.get("question") or items.get("title") or ""
        answer = items.get("answer", [])
        answer_text = ""
        for ans in answer:
            if isinstance(ans, dict) and "value" in ans:
                answer_value = ans.get("value", "")
                if answer_value in option_dict:
                    mapped = option_dict.get(answer_value)
                    if isinstance(mapped, dict) and "value" in mapped:
                        answer_value = mapped["value"]
                    else:
                        answer_value = mapped
                if answer_value:
                    answer_text = answer_text + str(answer_value) + " | "
        answer_text = answer_text.rstrip(" | ")

        if answer_text:
            formatted_options = _format_triage_options_list(items.get("options", []))
            item = {
                "question": question_text,
            }
            if formatted_options:
                item["options"] = formatted_options
            item["answer"] = answer_text
            formatted_triage_answers.append(item)

    if customer_name:
        for item in formatted_triage_answers:
            question = item.get("question", "")
            if isinstance(question, str) and "{name}" in question:
                item["question"] = question.replace("{name}", str(customer_name))

            if options := item.get("options", []):
                item["options"] = [
                    opt.replace("{name}", str(customer_name)) if isinstance(opt, str) else opt
                    for opt in options
                ]

            answer = item.get("answer", "")
            if isinstance(answer, str) and "{name}" in answer:
                item["answer"] = answer.replace("{name}", str(customer_name))

    return formatted_triage_answers
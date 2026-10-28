import json
from typing import Any

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.config import settings
from app.db.models.question_answers import QuestionAnswers
from app.db.models.resolve import Resolve
from app.db.models.resolve_question_answers import ResolveQuestionAnswers
from app.enums.resolve import ResolveStatusEnum
from app.schemas.v1.question_answers import QuestionAnswersCreate
from app.schemas.v1.resolve import Answer, AnswerQuestionRequest, ResolveResult
from app.db.services.general import validate_answer_text
from app.utils.validators import validate_email_format


NAME_QUESTION_IDENTIFIERS = {"1", "2"}


def create_question_answer(db: Session, question_answer_data: QuestionAnswersCreate) -> QuestionAnswers:
    """Create a new question answer."""
    db_question_answer = QuestionAnswers(**question_answer_data.dict())
    db.add(db_question_answer)
    db.commit()
    db.refresh(db_question_answer)
    return db_question_answer


def create_resolve_question_answer(db: Session, resolve_id: int, question_answer_id: int, score: float = 0.0) -> ResolveQuestionAnswers:
    """Create a new resolve question answer mapping."""
    db_resolve_question_answer = ResolveQuestionAnswers(
        resolve_id=resolve_id,
        question_answer_id=question_answer_id,
        score=score
    )
    db.add(db_resolve_question_answer)
    db.commit()
    db.refresh(db_resolve_question_answer)
    return db_resolve_question_answer


# def update_question_answer(db: Session, question_answer_id: int, answer: str) -> QuestionAnswers:
#     """Update a question answer."""
#     db_question_answer = db.query(QuestionAnswers).filter(QuestionAnswers.id == question_answer_id).first()
#     db_question_answer.answer = answer
#     db.commit()
#     db.refresh(db_question_answer)
#     return db_question_answer


def check_version_mismatch(request: AnswerQuestionRequest, questions: dict) -> tuple[dict, int]:
    """Check if the version is different from the latest version."""
    question_data = questions.get(str(request.question_identifier), None)
    if not question_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Identifier not found in questions")

    current_version = next(k for k in question_data if k != "status")

    if current_version != request.version:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Version mismatch, please answer the latest version of the question")

    return question_data, current_version

def save_question_answer(db: Session, request: AnswerQuestionRequest, resolve: Resolve, questions: dict) -> QuestionAnswers:

    question_data, current_version = check_version_mismatch(request, questions)

    question = question_data.get(current_version).get("question")
    version = current_version
    question_order = int(question_data.get(current_version).get("question_order"))

    answer_data = request.answer
    answer_keys = []
    for ans in answer_data:
        answer_keys.append(ans.value)

    # Create question answer entry
    question_answer_data = QuestionAnswersCreate(
        question=question,
        version=str(version),
        answer=json.dumps(jsonable_encoder(answer_data)),
        question_identifier=request.question_identifier,
        question_order=question_order
    )

    question_answer = create_question_answer(db, question_answer_data)

    options = question_data.get(current_version).get("options")
    score = 0
    if options and answer_keys and len(answer_keys) == 1:
        score = options[0].get(answer_keys[0]).get("score") if options[0].get(answer_keys[0]).get("score") else 0

    # Create resolve question answers mapping
    resolve_question_answer = create_resolve_question_answer(
        db,
        resolve.id,
        question_answer.id,
        score
    )

    return resolve_question_answer


def save_answer(db: Session, resolve: Resolve, request: AnswerQuestionRequest, questions: dict) -> tuple[bool, list]:
    """Save answers."""
    if resolve.status == ResolveStatusEnum.COMPLETED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Resolve is already completed")

    db_question_answers = {}
    if resolve.resolve_question_answers:
        for rqa in resolve.resolve_question_answers:
            qa = rqa.question_answer
            db_question_answers[str(qa.question_identifier)] = {
                "question": qa.question,
                "version": str(qa.version),
                "answer": json.loads(qa.answer),
                "object": qa
            }

    if str(request.question_identifier) not in db_question_answers:
        save_question_answer(db, request, resolve, questions)
    else:
        question_data, current_version = check_version_mismatch(request, questions)
        question_answer = db_question_answers.get(str(request.question_identifier)).get("object")
        question_answer.answer = json.dumps(jsonable_encoder(request.answer))
        question_answer.question = question_data.get(current_version).get("question")
        question_answer.version = int(current_version)
        db.commit()
        db.refresh(question_answer)

    return True, []


def bulk_update_resolve_question_answers(db: Session, update_list: list[dict], resolve_id: int, questions: dict) -> None:
    """Bulk update resolve question answers."""
    db.bulk_update_mappings(QuestionAnswers, update_list)
    rqa_list = []
    for qa in update_list:
        answer_data = json.loads(qa.get("answer"))
        answer_keys = [ans.get("value") for ans in answer_data]
        options = questions.get(str(qa.get("question_identifier"))).get("versions").get(str(qa.get("version"))).get("options")
        if options and answer_keys and len(answer_keys) == 1:
            score = options[0].get(answer_keys[0]).get("score") if options[0].get(answer_keys[0]).get("score") else 0
        else:
            score = 0
        rqa_list.append({
            "id": int(qa.get("rqa_object").id),
            "resolve_id": resolve_id,
            "question_answer_id": int(qa.get("id")),
            "score": score
        })
    db.bulk_update_mappings(ResolveQuestionAnswers, rqa_list)
    db.commit()


def bulk_create_resolve_question_answers(db: Session, create_list: list[QuestionAnswers], resolve_id: int, questions: dict) -> None:
    """Bulk create resolve question answers."""
    question_answer_objects = []
    for qa_data in create_list:
        qa_obj = QuestionAnswers(
            version=qa_data.get("version"),
            answer=qa_data.get("answer"),
            question_identifier=qa_data.get("question_identifier"),
            question_order=qa_data.get("question_order")
        )
        question_answer_objects.append(qa_obj)

    db.add_all(question_answer_objects)
    db.flush()  # This ensures the objects get IDs

    rqa_list = []
    for i, qa in enumerate(create_list):
        answer_data = json.loads(qa.get("answer"))
        answer_keys = [ans.get("value") for ans in answer_data]
        options = questions.get(str(qa.get("question_identifier"))).get("versions").get(str(qa.get("version"))).get("options")
        if options and answer_keys and len(answer_keys) == 1:
            score = options[0].get(answer_keys[0]).get("score") if options[0].get(answer_keys[0]).get("score") else 0
        else:
            score = 0
        rqa_list.append(ResolveQuestionAnswers(
            resolve_id=resolve_id,
            question_answer_id=question_answer_objects[i].id,  # Use the actual object's ID
            score=score
        ))
    db.add_all(rqa_list)
    db.commit()


def validate_answer_in_request(answer: list[Answer] | None, version: str, options: list) -> bool:
    """Validate answer in request."""
    if answer:
        for item in answer:
            if item.value not in options[0]:
                return False
    return True


def validate_requested_answers(db: Session, request_answers: dict, questions: dict) -> tuple[bool, list]:
    """Validate requested answer."""
    from app.db.services.user import verify_email_user_navigator

    error_list = []
    for question_identifier, answer in request_answers.items():
        qid = str(question_identifier)
        if qid not in questions:
            error_list.append(f"Question identifier: {qid} not found in questions")
            continue
            # raise ValueError(f"Question identifier: {qid} not found in questions")
        if str(answer.get("version")) not in questions[qid]["versions"]:
            error_list.append(f"Question identifier: {question_identifier} Version: {answer.get('version')} not found in questions")
            continue
            # raise ValueError(f"Question identifier: {question_identifier} Version: {answer.get('version')} not found in questions")
        latest_key = next(iter(questions[qid]["versions"].keys()))
        is_required = questions[qid]["versions"][latest_key].get("required")
        if str(answer.get("version")) != latest_key:
            error_list.append(f"Question identifier: {question_identifier} Version: {answer.get('version')} is not the latest version")
            continue
            # raise ValueError(f"Question identifier: {question_identifier} Version: {answer.get('version')} is not the latest version")
        if questions[qid]["versions"][latest_key].get("options"):
            if is_required and not answer.get("answer"):
                error_list.append(f"Question identifier: {question_identifier} Version: {answer.get('version')} is required")
                continue
            validate = validate_answer_in_request(answer.get("answer", []), str(answer.get("version")), questions[qid]["versions"][latest_key].get("options"))
            if not validate:
                error_list.append(f"Question identifier: {question_identifier} Version: {answer.get('version')} Answer: {answer.get('answer')[0].value} is not valid")
                continue
                # raise ValueError(f"Question identifier: {question_identifier} Version: {answer.get('version')} Answer: {answer.get('answer')[0].value} is not valid")

        if qid == "21":
            # email question validation
            if is_required and not answer.get("answer", []):
                error_list.append(f"Question identifier: {question_identifier} Version: {answer.get('version')} Email is required")
                continue
            email = answer.get("answer")[0].value
            answer.get("answer")[0].value = email.lower()
            if not validate_email_format(email):
                error_list.append(f"Question identifier: {question_identifier} Version: {answer.get('version')} Email: {email} is not valid")
                continue

            is_valid = verify_email_user_navigator(db, email)
            if is_valid:
                error_list.append(f" {email} already exists.")
                continue

        input_type = questions[qid]["versions"][latest_key].get("input_type")
        if input_type == "text" or input_type == "email":
            answer_text = answer.get("answer")[0].value

            min_length = questions[qid]["versions"][latest_key].get("min_length")
            max_length = questions[qid]["versions"][latest_key].get("max_length")
            is_valid, error = validate_answer_text(answer_text, is_required, min_length, max_length)
            if not is_valid:
                error_list.append(f"Question identifier: {question_identifier} Version: {answer.get('version')}, {error}")
                continue
            continue
        elif input_type == "number":
            answer_n = answer.get("answer")[0].value
            answer_value = float(answer_n) if answer_n else None
            min_length = questions[qid]["versions"][latest_key].get("min_length", 0)
            max_length = questions[qid]["versions"][latest_key].get("max_length")

            if is_required and not answer_value:
                error_list.append(f"Question identifier: {question_identifier} Version: {answer.get('version')} Answer is required and cannot be empty")
                continue

            if answer_value:
                if answer_value < min_length:
                    error_list.append(f"Question identifier: {question_identifier} Version: {answer.get('version')}, Answer must be at least {min_length}")
                    continue
                if answer_value > max_length:
                    error_list.append(f"Question identifier: {question_identifier} Version: {answer.get('version')}, Answer exceeds maximum limit of {max_length}")
                    continue
            continue
    
    if error_list:
        return False, error_list
    return True, []


def get_delete_map(
    resolve_map_version: dict,
    request_answer_list: list,
    db_answer_id_map: dict,
) -> dict:
    """Get the delete map."""
    delete_map = {}
    #get the combined list of option values from options_relationships which is not in answer_list
    combined_list = [value for key, value in resolve_map_version.get("options_relationships", {}).items() if key not in request_answer_list]
    # flatten the combined_list
    combined_list = list(set(item for sublist in combined_list for item in sublist))
    for identifier in combined_list:
        if identifier in db_answer_id_map:
            delete_map[identifier] = db_answer_id_map[identifier]
    return delete_map


def get_answer_delete_map(
    answer_data: str,
    resolve_map: dict,
    db_answers: dict,
    version: str,
    question_identifier: str,
) -> dict:

    delete_map = {}
    if db_answers and question_identifier in db_answers:
        db_answer_id_map = {qid:   {"question_answer_id": data.get("ans_object").id, "resolve_question_answer_id": data.get("rqa_object").id, "answer": data.get("answer")} for qid, data in db_answers.items()}
        answer_data = json.loads(answer_data)
        request_answer_list = [ans.get("value") for ans in answer_data]
        resolve_map_version = resolve_map.get(question_identifier, {}).get("versions", {}).get(version, {})
        options_list = [key for key in resolve_map_version.get("options_relationships", {}).keys()]
        map_type = resolve_map_version.get("type")

        if map_type == "multiple":
            #check answer_list and options_list are same
            if set(request_answer_list) == set(options_list):
                return {}
            else:
                delete_map = get_delete_map(resolve_map_version, request_answer_list, db_answer_id_map)
                return delete_map
        else:
            answer_value = [ ans.get("value") for ans in json.loads(db_answer_id_map[question_identifier].get("answer")) ]
            request_mapped_question = resolve_map_version.get("options_relationships", {}).get(request_answer_list[0], [])
            db_mapped_question = resolve_map_version.get("options_relationships", {}).get(answer_value[0], [])
            if set(request_answer_list) == set(answer_value):
                return {}
            elif set(request_mapped_question) == set(db_mapped_question):
                return {}
            else:
                delete_map = get_delete_map(resolve_map_version, request_answer_list, db_answer_id_map)
                return delete_map
    return delete_map


def bulk_delete_resolve_question_answers(db: Session, delete_map: dict) -> None:
    """Bulk delete resolve question answers."""
    resolve_question_answer_ids = []
    question_answer_ids = []
    for identifier, data in delete_map.items():
        question_answer_ids.append(data.get("question_answer_id"))
        resolve_question_answer_ids.append(data.get("resolve_question_answer_id"))
        
    db.query(ResolveQuestionAnswers).filter(ResolveQuestionAnswers.id.in_(resolve_question_answer_ids)).delete()
    db.query(QuestionAnswers).filter(QuestionAnswers.id.in_(question_answer_ids)).delete()
    db.commit()


def validate_save_answer(db: Session, resolve: Resolve, request: AnswerQuestionRequest, questions: dict, resolve_map: dict) -> tuple[bool, list]:
    """Validate and save answer."""
    request_answers = {}
    if request.answers:
        for item in request.answers:
            question_identifier_str = str(item.question_identifier)

            if question_identifier_str in NAME_QUESTION_IDENTIFIERS:
                answer_obj = item.answer[0] if item.answer else None
                if answer_obj and isinstance(answer_obj.value, str):
                    trimmed_value = answer_obj.value.strip()
                    answer_obj.value = trimmed_value.title() if trimmed_value else ""

            request_answers[item.question_identifier] = {
                "version": item.version,
                "answer": item.answer
            }
    if request_answers:
        is_valid, error_list = validate_requested_answers(db, request_answers, questions)
        if not is_valid:
            return False, error_list

        update_list = []
        create_list = []
        delete_map = {}
        db_answers = {}
        for rqa in resolve.resolve_question_answers or []:
            qa = rqa.question_answer
            db_answers[qa.question_identifier] = {
                "version": str(qa.version),
                "answer": qa.answer,
                "ans_object": qa,
                "rqa_object": rqa
            }

        for question_identifier, data in request_answers.items():
            if str(question_identifier) == "5":
                answer_values = [ans.value for ans in data.get("answer", [])]
                resolve.finance_flag = True if "finance" in answer_values else False            

            answer_data = json.dumps(jsonable_encoder(data.get("answer")))

            if question_identifier in resolve_map:
                version = data.get("version")
                delete_map = get_answer_delete_map(answer_data, resolve_map, db_answers, version, question_identifier)
                # delete_list.append(question_identifier)

            if question_identifier in db_answers:
                qa = db_answers[question_identifier]["ans_object"]
                qa.answer = answer_data
                qa.version = int(data.get("version"))
                update_list.append({
                    "id": qa.id,
                    "answer": answer_data,
                    "version": int(data.get("version")),
                    "question_identifier": question_identifier,
                    "question_order": questions[str(question_identifier)].get("versions").get(data.get("version")).get("question_order"),
                    "rqa_object": db_answers[question_identifier]["rqa_object"]
                })
                continue
            else:
                create_list.append({
                    "version": int(data.get("version")),
                    "answer": answer_data,
                    "question_identifier": question_identifier,
                    "question_order": questions[str(question_identifier)].get("versions").get(data.get("version")).get("question_order")
                })

        if update_list:
            bulk_update_resolve_question_answers(db, update_list, resolve.id, questions)

        if create_list:
            bulk_create_resolve_question_answers(db, create_list, resolve.id, questions)
        
        if delete_map:
            bulk_delete_resolve_question_answers(db, delete_map)

        name = None
        email = None
        partner_name = None
        if resolve.resolve_question_answers:
            for rqa in resolve.resolve_question_answers:
                if str(rqa.question_answer.question_identifier) == "1":
                    raw_value = json.loads(rqa.question_answer.answer)[0].get("value")
                    if isinstance(raw_value, str):
                        trimmed_value = raw_value.strip()
                        name = trimmed_value.title() if trimmed_value else ""
                if str(rqa.question_answer.question_identifier) == "2":
                    raw_partner_value = json.loads(rqa.question_answer.answer)[0].get("value")
                    if isinstance(raw_partner_value, str):
                        trimmed_partner_value = raw_partner_value.strip()
                        partner_name = trimmed_partner_value.title() if trimmed_partner_value else ""
                if str(rqa.question_answer.question_identifier) == "21":
                    email = json.loads(rqa.question_answer.answer)[0].get("value")

        if email:
            resolve.title = f"Nova Recommendations - {email}"
        elif name:
            resolve.title = f"Nova Recommendations - {name}"
            
        if partner_name:
            resolve.partner_name = partner_name
        if name:
            resolve.customer_name = name
        if email:
            resolve.customer_email = email

        resolve.questions_answered = len(resolve.resolve_question_answers)
        db.commit()
        db.refresh(resolve)
    return True, []


def get_resolve_result(db: Session, resolve: Resolve, questions: dict) -> dict[str, Any]:
    """Get the resolve result."""

    from app.enums.base import NameExtractionOption
    from app.utils.formatters import extract_name_parts

    # if resolve.status != ResolveStatusEnum.COMPLETED:

    resolve_result = None
    with open(settings.RESOLVE_RESULT_FILE_PATH) as f:
        resolve_result = json.load(f)

    if not resolve_result:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resolve results JSON file not found")

    if not resolve.resolve_question_answers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resolve is not completed, please answer all questions")

    required_questions = []
    for q_id, versions in questions.items():
        latest_key = next(iter(versions["versions"].keys()))
        latest_question_data = versions["versions"][latest_key]

        if q_id == "21":
            continue
        #need more checks for rules
        if latest_question_data.get('required') and latest_question_data.get('rules') == []:
            required_questions.append(q_id)

    db_question_answers = {}
    name = resolve.customer_name
    partner_name = resolve.partner_name
    for rqa in resolve.resolve_question_answers:
        qa = rqa.question_answer
        if not name:
            if str(qa.question_identifier) == "1":
                raw_name = json.loads(qa.answer)[0].get("value")
                if isinstance(raw_name, str):
                    trimmed_raw_name = raw_name.strip()
                    name = trimmed_raw_name.title() if trimmed_raw_name else ""
        if not partner_name:
            if str(qa.question_identifier) == "2":
                raw_partner_name = json.loads(qa.answer)[0].get("value")
                if isinstance(raw_partner_name, str):
                    trimmed_raw_partner_name = raw_partner_name.strip()
                    partner_name = trimmed_raw_partner_name.title() if trimmed_raw_partner_name else ""

        db_question_answers[str(qa.question_identifier)] = {
            "answer": json.loads(qa.answer),
            "score": rqa.score
        }

    for q_id in required_questions:
        if q_id not in db_question_answers:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resolve is not completed, please answer all questions")
    #get answer key
    result_key = get_result_key(db_question_answers)
    result = resolve_result.get(result_key)

    partner_first_name = extract_name_parts(partner_name, NameExtractionOption.FIRST)
    result_data = {}
    latest_version = next(iter(result.get("versions", {}).keys()))

    summary_template = result.get("versions",{})[latest_version]["summary"]
    email_summary_template = result.get("versions",{})[latest_version]["email_summary"]
    summary = summary_template.format(name=name, partner_name=partner_first_name)
    email_summary = email_summary_template.format(name=name, partner_name=partner_first_name)

    result_data["summary"] = summary
    result_data["email_summary"] = email_summary
    result_data["result_type"] = result_key
    result_data["title"] = result.get("versions",{})[latest_version]["title"]
    result_data["version"] = result.get("versions",{})[latest_version]["version"]

    recommendations = result.get("recommendations", {})
    result_data["recommendations"] = {}
    for key, value in recommendations.items():
        result_data["recommendations"][key] = value.format(name=name, partner_name=partner_first_name)

    affordability_template = result.get("affordability", "")
    affordability = affordability_template.format(name=name, partner_name=partner_name, partner_first_name=partner_first_name)
    result_data["affordability"] = affordability
    result_data["tags"] = result.get("tags", [])

    #new logic update #911
    recommended_result_key = get_recommended_approach(resolve, result_data)
    r_result = resolve_result.get(recommended_result_key)
    r_summary_template = r_result.get("versions",{})[latest_version]["summary"]
    r_email_summary_template = r_result.get("versions",{})[latest_version]["email_summary"]
    r_summary = r_summary_template.format(name=name, partner_name=partner_first_name)
    r_email_summary = r_email_summary_template.format(name=name, partner_name=partner_first_name)
    result_data["recommended_approach"] = {}

    result_data["recommended_approach"]["summary"] = r_summary
    result_data["recommended_approach"]["email_summary"] = r_email_summary
    result_data["recommended_approach"]["result_type"] = recommended_result_key
    result_data["recommended_approach"]["title"] = r_result.get("versions",{})[latest_version]["title"]
    result_data["recommended_approach"]["version"] = r_result.get("versions",{})[latest_version]["version"]

    r_recommendations = r_result.get("recommendations", {})
    result_data["recommended_approach"]["recommendations"] = {}
    for key, value in r_recommendations.items():
        result_data["recommended_approach"]["recommendations"][key] = value.format(name=name, partner_name=partner_first_name)

    r_affordability_template = r_result.get("affordability", "")
    r_affordability = r_affordability_template.format(name=name, partner_name=partner_name, partner_first_name=partner_first_name)
    result_data["recommended_approach"]["affordability"] = r_affordability
    result_data["recommended_approach"]["tags"] = r_result.get("tags", [])
    return result_data

    # else:
    #     raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail={
    #         "success": False,
    #         "message": "Resolve submission is already completed.",
    #     })

def get_result_key(db_question_answers: dict) -> str:  # noqa: PLR0912, PLR0915
    # Legal process type constants - using uppercase as they represent specific legal processes
    DIY = [5,5,5,5,5,1]  # noqa: N806
    Mediation = [4,4,3,4,4,2]  # noqa: N806
    Solicitor_led = [2,2,1,2,2,3]  # noqa: N806
    Court = [1,1,1,1,1,4]  # noqa: N806
    Collaborative = [3,3,2,3,3,3]  # noqa: N806
    Arbitration = [1,1,1,2,2,4]  # noqa: N806
    One_lawyer_one_couple = [4,4,3,3,4,2]  # noqa: N806
    Hybrid_Mediation = [2,2,1,3,3,4]  # noqa: N806
    Private_FDR = [1,2,1,2,2,3]  # noqa: N806

    # Score variables for each legal process type
    DIY_score = 0  # noqa: N806
    Mediation_score = 0  # noqa: N806
    Solicitor_Led_score = 0  # noqa: N806
    Court_score = 0  # noqa: N806
    Collaborative_score = 0  # noqa: N806
    Arbitration_score = 0  # noqa: N806
    One_lawyer_one_couple_score = 0  # noqa: N806
    Hybrid_Mediation_score = 0  # noqa: N806
    Private_FDR_score = 0  # noqa: N806

    awareness_score = 0
    trust_score = 1
    legal_complexity_score_children = 0
    legal_complexity_score_fin = 0
    legal_complexity_score = 0
    financial_complexity_score = 0

    if '19' in db_question_answers: # financial_complexity
        answer_list = db_question_answers.get('19',{}).get('answer',[])
        financial_complexity = answer_list[0].get('value','') if answer_list else ''
        financial_complexity_score = len(financial_complexity) * 5/8

    warning_signs_score = 0
    warning_signs = []
    if '16' in db_question_answers: # warning_signs
        warning_signs = db_question_answers.get('16',{}).get('answer',[])
        warning_signs_score = len(warning_signs) * 5/6

    help_needed_score = 0
    if '5' in db_question_answers: # help_needed
        answer_list = db_question_answers.get('5',{}).get('answer',[])
        help_needed = answer_list[0].get('value','') if answer_list else ''
        help_needed_score = len(help_needed)

    children_complexity_score = 0
    if '14' in db_question_answers: # children_complexity
        answer_list = db_question_answers.get('14',{}).get('answer',[])
        children_complexity = answer_list[0].get('value','') if answer_list else ''
        children_complexity_score = len(children_complexity)

    child_arrangements_score = 0
    if '15' in db_question_answers: # child_arrangements
        child_arrangements_score = db_question_answers.get('15',{}).get('score',0)

    financial_awareness_score = 0
    if '20' in db_question_answers: # financial_awareness
        financial_awareness_score = db_question_answers.get('20',{}).get('score',0)

    proximity_score = 0
    if '17' in db_question_answers: # proximity
        proximity_score = db_question_answers.get('17',{}).get('score',0)

    confidence_score = 0
    if '18' in db_question_answers: # confidence
        confidence_score = db_question_answers.get('18',{}).get('score',0)

    previous_communication_score = 0
    if '8' in db_question_answers: # communication
        previous_communication_score = db_question_answers.get('8',{}).get('score',0)

    conflict_score = 0
    if '10' in db_question_answers: # conflict
        conflict_score = db_question_answers.get('10',{}).get('score',0)

    current_communication_score = 0
    if '11' in db_question_answers: # current_communication
        current_communication_score = db_question_answers.get('11',{}).get('score',0)

    communication_score = (previous_communication_score + current_communication_score + conflict_score) / 3
    # input_7
    financial_understanding_score = 0

    financial_control_score = 0
    if '12' in db_question_answers: # conflict
        financial_control_score = db_question_answers.get('12',{}).get('score',0)

    decision_making_score = 0
    if '9' in db_question_answers: # decision_making
        decision_making_score = db_question_answers.get('9',{}).get('score',0)

    financial_understanding_score = (financial_control_score + decision_making_score) / 2

    if help_needed_score == 2:
        awareness_score =	(child_arrangements_score + financial_awareness_score) / 2
    elif help_needed_score == 1:
        if 'children' in help_needed:
            awareness_score =	child_arrangements_score
        elif 'finance' in help_needed:
            awareness_score =	financial_awareness_score

    if len(warning_signs) > 0:
        trust_score = 5 - warning_signs_score
    trust_score = ((trust_score + proximity_score) / 2)

    if 'children' in help_needed:
        if children_complexity_score > 0:
            legal_complexity_score_children = children_complexity_score
        else:
            legal_complexity_score_children = 1

    if 'finance' in help_needed:
        if financial_complexity_score > 0:
            legal_complexity_score_fin = financial_complexity_score
        else:
            legal_complexity_score_fin = 1

    if 'children' in help_needed and 'finance' in help_needed:
        legal_complexity_score = (legal_complexity_score_children + legal_complexity_score_fin) / 2
    elif 'children' in help_needed:
        legal_complexity_score = legal_complexity_score_children
    elif 'finance' in help_needed:
        legal_complexity_score = legal_complexity_score_fin


    input_array = [communication_score, financial_understanding_score, awareness_score, confidence_score,trust_score, legal_complexity_score ]

    output_array = []
    # Calculation
    for index in range(6):
        DIY_score = DIY_score + abs(input_array[index] - DIY[index])  # noqa: N806
        Mediation_score = Mediation_score + abs(input_array[index] - Mediation[index])  # noqa: N806
        Solicitor_Led_score = Solicitor_Led_score + abs(input_array[index] - Solicitor_led[index])  # noqa: N806
        Court_score = Court_score + abs(input_array[index] - Court[index])  # noqa: N806

        Collaborative_score = Collaborative_score + abs(input_array[index] - Collaborative[index])  # noqa: N806
        Arbitration_score = Arbitration_score + abs(input_array[index] - Arbitration[index])  # noqa: N806

        One_lawyer_one_couple_score = One_lawyer_one_couple_score + abs(input_array[index] - One_lawyer_one_couple[index])  # noqa: N806
        Hybrid_Mediation_score = Hybrid_Mediation_score + abs(input_array[index] - Hybrid_Mediation[index])  # noqa: N806
        Private_FDR_score = Private_FDR_score + abs(input_array[index] - Private_FDR[index])  # noqa: N806

    output_array = []
    output_array.append(("diy",DIY_score))
    output_array.append(("mediation",Mediation_score))
    output_array.append(("lawyer_negotiation",Solicitor_Led_score))
    output_array.append(("court",Court_score))

    output_array.append(("arbitration",Arbitration_score))
    output_array.append(("collaborative",Collaborative_score))

    output_array.append(("one_lawyer_one_couple",One_lawyer_one_couple_score))
    output_array.append(("hybrid_mediation",Hybrid_Mediation_score))
    output_array.append(("private_fdr",Private_FDR_score))

    # usort($Output_Array,function($a,$b){ return ($a[1]*10000  -  $b[1]*10000);	 });
    output_array.sort(key=lambda x: x[1] * 10000)
    # court_by_pass = ",".join(input_54)
    # court_by_pass = ""

    score = output_array[0][0]

    court_proceedings = ""
    if '6' in db_question_answers: # court_proceedings
        answer_list = db_question_answers.get('6',{}).get('answer',[])
        court_proceedings = answer_list[0].get('value','') if answer_list else ''

    court_stage = ""
    if '7' in db_question_answers: # court_stage
        answer_list = db_question_answers.get('7',{}).get('answer',[])
        court_stage = answer_list[0].get('value','') if answer_list else ''


    if score == "Court" and court_proceedings != "no_court_proceedings" and court_stage != "early_stage" and "domestic_abuse" not in warning_signs:
        score = "arbitration"

    elif score == "Court" and "domestic_abuse" not in warning_signs and court_stage == "early_stage":
        score = "private_fdr"

    elif score == "Court" and "domestic_abuse" in warning_signs:
        score = "court"

    return score


def get_recommended_approach(resolve: Resolve, resolve_result: dict) -> str:
    """Get the recommended approach."""

    result_type = resolve_result["result_type"]
    parent_recommendations = frozenset({"mediation", "collaborative", "one_lawyer_one_couple"})
    no_court_recommendations = frozenset(
        {"hybrid_mediation", "arbitration", "private_fdr", "lawyer_negotiation"}
    )
    court_recommendations = frozenset({"hybrid_mediation", "lawyer_negotiation", "court"})
    stage_default = {
        "early_stage": "private_fdr",
        "mid_stage": "hybrid_mediation",
        "late_stage": "arbitration",
    }

    affordability_test = True
    db_question_answers = {}
    for rqa in resolve.resolve_question_answers:
        qa = rqa.question_answer
        db_question_answers[str(qa.question_identifier)] = {
            "answer": json.loads(qa.answer),
            "score": rqa.score
        }
    
    court_proceedings = ""
    court_stage = ""
    affordability = ""
    financial_picture = ""
    if '6' in db_question_answers: # court_proceedings
        answer_list = db_question_answers.get('6',{}).get('answer',[])
        court_proceedings = answer_list[0].get('value','') if answer_list else ''
    if '7' in db_question_answers: # court_stage
        answer_list = db_question_answers.get('7',{}).get('answer',[])
        court_stage = answer_list[0].get('value','') if answer_list else ''
    if '22' in db_question_answers: # financial_picture
        answer_list = db_question_answers.get('22',{}).get('answer',[])
        financial_picture = answer_list[0].get('value','') if answer_list else ''
    if '13' in db_question_answers: # affordability
        answer_list = db_question_answers.get('13',{}).get('answer',[])
        affordability = answer_list[0].get('value','') if answer_list else ''

    if affordability in ["less_than_15k", "between_15k_and_25k", "between_25k_and_40k"] and financial_picture in ["less_than_100k", "between_100k_and_300k"]:
        affordability_test = False

    if result_type in parent_recommendations:
        if not affordability_test:
            return "mediation"
        if court_proceedings == "no_court_proceedings":
            return result_type
        return stage_default.get(court_stage, result_type)

    if court_proceedings == "no_court_proceedings":
        if result_type in no_court_recommendations and not affordability_test:
            return "lawyer_negotiation"
        return result_type

    if result_type in court_recommendations:
        return stage_default.get(court_stage, result_type)

    return result_type


def get_resolve_circumstance(resolve: Resolve) -> list[str]:
    """Get the resolve circumstance."""
    circumstance = []
    for rqa in resolve.resolve_question_answers:
        qa = rqa.question_answer
        if str(qa.question_identifier) == "5":
            answer_list = json.loads(qa.answer)
            if answer_list:
                for answer in answer_list:
                    circumstance.append(answer.get("value"))
    return circumstance
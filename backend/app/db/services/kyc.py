import json
from typing import Any

from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import (
    Case,
    CaseEngage,
    CaseLawyer,
    Engage,
    EngageQuestionAnswers,
    Lawyer,
    Match,
    QuestionAnswers,
    ResolveQuestionAnswers,
    User,
    Resolve,
)
from app.db.services.resolve import get_resolve_from_case_id
from app.db.services.general import validate_answer_text
# from app.enums.match import MatchStatusEnum
from app.schemas.v1.engage import SubmitKycRequest
# from app.utils.formatters import extract_name_parts
# from app.enums.base import NameExtractionOption

KYC_NAME_QUESTION_IDENTIFIERS = {"1", "2"}
# KYC_PHONE_QUESTION_IDENTIFIER = "15"
TRIAGE_OMIT_QUESTIONS = ["28"]

def check_customer_engage_access(db: Session, current_user: User, case_id: int) -> bool:
    """Check if the customer has access to the engage."""

    if current_user.customer is None:
        return False
    if current_user.customer.case_customers is None:
        return False
    if not any(case_customer.case_id == case_id for case_customer in current_user.customer.case_customers):
        return False
    return True


def check_lawyer_engage_access(db: Session, current_user: User, case_id: int) -> bool:
    """Check if the lawyer has access to the engage."""
    if current_user.lawyer is None:
        return False

    # Check if case is assigned to a different lawyer
    # existing_assignment = db.query(CaseLawyer).filter(
    #     CaseLawyer.case_id == case_id,
    #     CaseLawyer.lawyer_id != current_user.lawyer.id
    # ).first()

    # if existing_assignment:
    #     return False

    lawyer_data = db.query(Lawyer).filter(
        Lawyer.id == current_user.lawyer.id,
        or_(
            # Condition 1: Lawyer is assigned to a case
            Lawyer.case_lawyers.any(CaseLawyer.case_id == case_id),
            # Condition 2: Lawyer is in match table with status other than DECLINED
            Lawyer.matches.any(
                (Match.case_id == case_id) # & (Match.status != MatchStatusEnum.DECLINED)
            )
        )
    ).first()

    if lawyer_data is None:
        return False

    return True


def create_engage_case(db: Session, case_id: int, user_id: int) -> int:
    """Create the engage and assign to the case."""
    engage = Engage(
        user_id=user_id
    )
    db.add(engage)
    db.commit()
    db.refresh(engage)
    case_engage = CaseEngage(
        case_id=case_id,
        engage_id=engage.id
    )
    db.add(case_engage)
    db.commit()
    return int(engage.id)


def get_kyc_identifiers(questions: dict | None = None) -> set[str]:
    """Return Alignment Check question identifiers, including nested form fields."""
    questions = questions or get_kyc_questions()
    identifiers = set(questions.keys())
    for qdata in questions.values():
        for version in (qdata or {}).get("versions", {}).values():
            form_qs = (version or {}).get("form_fields", {}).get("questions", {})
            identifiers.update(form_qs.keys())
    return identifiers


def get_kyc_data_from_db(db: Session, case_id: int) -> tuple[bool, list[QuestionAnswers]]:
    """Get the kyc data from the database."""
    allowed_ids = get_kyc_identifiers()
    db_data = db.query(QuestionAnswers)\
        .join(EngageQuestionAnswers, EngageQuestionAnswers.question_answer_id == QuestionAnswers.id)\
        .join(CaseEngage, CaseEngage.engage_id == EngageQuestionAnswers.engage_id)\
        .filter(CaseEngage.case_id == case_id)\
        .filter(QuestionAnswers.question_identifier.in_(allowed_ids))\
        .all()

    return True, db_data


def get_answer_mapped_data(db_data: list[QuestionAnswers], questions: dict, options: list[dict]) -> dict: #, customer_phone: str | None) -> dict:
    """Get the answer mapped data."""

    try:
        db_answers = {
            str(data.question_identifier): {
                "answer": json.loads(str(data.answer)) if data.answer else [],
                "version": data.version
            } for data in db_data
        }

        result = {}
        for qid, qdata in questions.items():
            if qid in db_answers:
                current_version_key = db_answers[qid]["version"]
                current_version_data = (qdata or {}).get("versions", {}).get(current_version_key, {})
            else:
                current_version_key = next(iter(qdata.get("versions", {}).keys()))
                current_version_data = qdata.get("versions", {}).get(current_version_key)
            # Merge version data with question_status and version number
            merged = {**current_version_data}

            if db_answers.get(qid):
                merged["answer"] = db_answers[qid].get("answer", [])
            else:
                merged["answer"] = []
            merged["question_status"] = qdata.get("question_status")
            merged["version"] = current_version_key
            if qid == "6":
                merged["options"] = options

            # if qid == KYC_PHONE_QUESTION_IDENTIFIER:
            #     ans = merged.get("answer", [])[0].get("value", None) if merged.get("answer", []) else None
            #     if not ans:
            #         merged["answer"] = [{"value": customer_phone}] if customer_phone else []

            result[qid] = merged
        
        for qid, qdata in db_answers.items():
            db_answers = [ answer.get("value") for answer in qdata.get("answer", []) if answer.get("value") is not None ]
            if qid == "1" or qid == "2":
                result[qid]["answer"] = []
                ans_parts = db_answers[0].split()
                ans_part_1 = ans_parts[0] if len(ans_parts) > 0 else []
                ans_part_2 = ans_parts[1] if len(ans_parts) > 1 else []
                if qid == "1":
                    result[qid]["form_fields"]["questions"]["1.1"]["answer"] = [{"value": ans_part_1}]
                    result[qid]["form_fields"]["questions"]["1.3"]["answer"] = [{"value": ans_part_2}]
                elif qid == "2":
                    result[qid]["form_fields"]["questions"]["2.1"]["answer"] = [{"value": ans_part_1}]
                    result[qid]["form_fields"]["questions"]["2.3"]["answer"] = [{"value": ans_part_2}]

            if "." in qid:
                qid_parts = qid.split(".")
                qid_1 = qid_parts[0]
                db_answer = db_answers[0] if db_answers else []
                result[qid_1]["form_fields"]["questions"][qid]["answer"] = [{"value": db_answer}] if db_answer else []

        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)) from None


def get_kyc_questions() -> dict:
    """Get the kyc questions from the file."""
    questions: dict[str, Any] = {}
    try:
        with open(settings.KYC_QUESTIONS_FILE_PATH) as f:
            questions = json.load(f)
        return questions
    except Exception:
        message = {
            "success": False,
            "message": "Error reading Alignment Check questions from file"
        }
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=message) from None


def get_kyc_data(db: Session, case_id: int) -> dict:
    """Get the kyc data for the case."""

    from app.db.services.case import get_case_by_id

    questions = get_kyc_questions()

    case = get_case_by_id(db, case_id)
    user = case.case_customers[0].customer.user if case and case.case_customers and len(case.case_customers) > 0 else None
    # customer_phone = user.phone if user and user.phone is not None else None

    if case.is_triage:
        resolve = None
        case_engage = db.query(CaseEngage).filter(CaseEngage.case_id == case.id).first()
        engage_id = case_engage.engage_id if case_engage is not None else None
        if engage_id is None:
            engage_id = create_engage_case(db, case.id, int(current_user.id)) # type: ignore
        options = get_resolve_options_for_kyc(db, None, int(engage_id))
    else:
        resolve = get_resolve_from_case_id(db, case_id)
        if resolve is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": False, "message": "Resolve not found for the case"})
        options = get_resolve_options_for_kyc(db, int(resolve.id), None)
        

    data_status, db_data = get_kyc_data_from_db(db, case_id)
    if data_status is False:
        message = {
            "success": False,
            "message": "Error collecting Alignment Check data from database"
        }
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)

    if len(db_data) == 0:
        result = {}
        for qid, qdata in questions.items():

            latest_version_key = next(iter(qdata.get("versions", {}).keys()))
            latest_version_data = qdata.get("versions", {}).get(latest_version_key)

            # Merge version data with question_status and version number
            merged = {**latest_version_data}
            merged["question_status"] = qdata.get("question_status")
            merged["version"] = latest_version_key
            if qid == "6":
                merged["options"] = options

            # if qid == KYC_PHONE_QUESTION_IDENTIFIER:
            #     merged["answer"] = [{"value": customer_phone}] if customer_phone else []

            result[qid] = merged
    else:
        result = get_answer_mapped_data(db_data, questions, options) #, customer_phone)

    # sorted_dict = dict(
    #     sorted(result.items(), key=lambda item: item[1]["question_order"])
    # )

    return result


def format_request_answers(request: SubmitKycRequest) -> dict:
    """Format the request answers."""
    # Conversion
    request_answers = {}
    for req in request.answers:
        qid = req.question_identifier
        qid_str = str(qid)
        # Handle both single and multiple answers
        ans_list = req.answer if isinstance(req.answer, list) else [req.answer]
        if qid_str in KYC_NAME_QUESTION_IDENTIFIERS:
            answer_obj = ans_list[0] if ans_list else None
            if answer_obj and isinstance(answer_obj.value, str):
                trimmed_value = answer_obj.value.strip()
                answer_obj.value = trimmed_value.title() if trimmed_value else ""
        # Convert each Answer object to dict (e.g., using vars())
        ans_dicts = [vars(ans) for ans in ans_list]
        request_answers[qid] = {"answer": ans_dicts}
    return request_answers


def check_is_required_for_conditional(parent_id, db_data_map, required_answer_value) -> bool:
    """Check if the conditional question is required by parent value."""

    if parent_id in db_data_map:
        answers = json.loads(str(db_data_map[parent_id].answer)) if db_data_map[parent_id].answer else []
        db_answer_values = [next(iter(d.values())) for d in answers]
        if required_answer_value in db_answer_values:
            return True
        else:
            return False

    return False


def check_required_kyc_answers(
    request_answers: dict,
    questions: dict,
    options: list[dict],
    db_data: list[QuestionAnswers],
    update_flag: bool,
    omit_required_questions: list[str] | None = None,
) -> tuple[bool, list[dict]]:
    """Check if the required kyc answers are submitted."""

    from app.utils.validators import validate_phone_number

    omit_required = {str(qid) for qid in (omit_required_questions or [])}
    db_data_map = {str(data.question_identifier): data for data in db_data}
    form_question_map = {}
    success = True
    err_list = []
    required_questions = {}
    for qid, qdata in questions.items():
        if str(qid) in omit_required:
            continue
        latest_version_key = next(iter(qdata.get("versions", {}).keys()))
        latest_version_data = qdata.get("versions", {}).get(latest_version_key)
        if latest_version_data.get("input_type") == "form":
            form_questions = latest_version_data.get("form_fields", {}).get("questions", {})
            for form_question_id, form_question_data in form_questions.items():

                form_question_map[form_question_id] = form_question_data
                if form_question_data.get("required") is True and form_question_data.get("question_type") != "conditional":
                    required_questions[form_question_id] = {"version": latest_version_key}
                    continue
        else:
            if latest_version_data.get("required") is True and latest_version_data.get("question_type") != "conditional":
                required_questions[qid] = {"version": latest_version_key}
                continue

    if update_flag is False:
        for qid in required_questions.keys():
            if qid not in request_answers and qid not in db_data_map:
                err_list.append({"success": False, "message": f"Question {qid} is required"})

    for qid in request_answers.keys():
        if qid not in questions and qid not in form_question_map:
            err_list.append({"success": False, "message": f"Question identifier: {qid} is not valid"})
            continue

        answer = request_answers.get(qid, {}).get("answer", [])
        answer_values = [next(iter(d.values())) for d in answer]

        if "." in qid:
            qid_parts = qid.split(".")
            qid_1 = qid_parts[0]
            input_type = questions[qid_1].get("versions", {}).get(latest_version_key, {}).get("input_type")
        else:
            input_type = questions[qid].get("versions", {}).get(latest_version_key, {}).get("input_type")

        if input_type != "form":
            question_type = questions[qid].get("versions", {}).get(latest_version_key, {}).get("question_type")
            qdata = questions[qid].get("versions", {})
            latest_version_key = next(iter(qdata.keys()))
            question_options = qdata.get(latest_version_key, {}).get("options", [])        
            if qid == "6":
                question_options = options

            # answer = request_answers.get(qid, {}).get("answer", [])
            # answer_values = [next(iter(d.values())) for d in answer]
            # question_type = questions[qid].get("versions", {}).get(latest_version_key, {}).get("question_type")
            is_required = questions[qid].get("versions", {}).get(latest_version_key, {}).get("required")
            if str(qid) in omit_required:
                is_required = False
            if question_options:
                if is_required and not answer_values:
                    err_list.append({"success": False, "message": f"Question {qid} is required"})
                    continue
                option_keys = [next(iter(d.keys())) for d in question_options]
                is_valid = all(a in option_keys for a in answer_values)
                if not is_valid:
                    err_list.append({"success": False, "message": f"Question {qid} : Invalid answer"})

            else:
                if is_required:
                    if question_type == "conditional":
                        question_data = questions[qid].get("versions", {}).get(latest_version_key, {})
                        rules = question_data.get("rules", [])
                        parent_id = rules[0].get("identifier")
                        required_answer_value = rules[0].get("value")[0]
                        # check if the conditional question is required by parent value
                        is_required = check_is_required_for_conditional(parent_id, db_data_map, required_answer_value)
                        if is_required and not answer_values:
                            err_list.append({"success": False, "message": f"Question {qid} is required"})
                            continue

            input_type = questions[qid].get("versions", {}).get(latest_version_key, {}).get("input_type")
            if input_type == "text":
                answer_text = answer_values[0] if answer_values else None
                min_length = questions[qid].get("versions", {}).get(latest_version_key, {}).get("min_length")
                max_length = questions[qid].get("versions", {}).get(latest_version_key, {}).get("max_length")
                is_valid, error = validate_answer_text(answer_text, is_required, min_length, max_length)
                if not is_valid:
                    err_list.append({"success": False, "message": f"Question {qid} Version: {required_questions[qid]["version"]}, {error}"})
        else:
            is_required = form_question_map[qid].get("required")
            if is_required and not answer_values:
                err_list.append({"success": False, "message": f"Question {qid} is required"})
                continue
            
            input_type = form_question_map[qid].get("input_type", "")
            if input_type == "text":
                answer_text = answer_values[0] if answer_values else None
                min_length = form_question_map[qid].get("min_length", 0)
                max_length = form_question_map[qid].get("max_length", 0)
                is_valid, error = validate_answer_text(answer_text, is_required, min_length, max_length)
                if not is_valid:
                    err_list.append({"success": False, "message": f"Question {qid} Version: {required_questions[qid]["version"]}, {error}"})

    if len(err_list) > 0:
        success = False
    return success, err_list


def bulk_update_kyc_question_answers(db: Session, update_list: list[dict]) -> None:
    """Bulk update resolve question answers."""
    db.bulk_update_mappings(QuestionAnswers, update_list) # type: ignore
    eqa_list = []
    for qa in update_list:
        enq_object = qa.get("enq_object")
        if enq_object is not None:
            eqa_list.append({
                "id": int(enq_object.id) if enq_object is not None and enq_object.id is not None else None,
                "question_answer_id": int(qa.get("id")) if qa.get("id") is not None else None # type: ignore
            })
    db.bulk_update_mappings(EngageQuestionAnswers, eqa_list) # type: ignore
    db.commit()


def bulk_create_kyc_question_answers(db: Session, engage_id: int, create_list: list[dict]) -> None:
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
    for i in range(len(create_list)):
        rqa_list.append(EngageQuestionAnswers(
            engage_id=engage_id,
            question_answer_id=question_answer_objects[i].id
        ))
    db.add_all(rqa_list)
    db.commit()


def bulk_delete_kyc_question_answers(db: Session, delete_map: dict) -> None:
    """Bulk delete kyc question answers."""

    engage_question_answer_ids = []
    question_answer_ids = []
    for identifier, data in delete_map.items():
        question_answer_ids.append(data.get("question_answer_id"))
        engage_question_answer_ids.append(data.get("engage_question_answer_id"))
        
    db.query(EngageQuestionAnswers).filter(EngageQuestionAnswers.id.in_(engage_question_answer_ids)).delete()
    db.query(QuestionAnswers).filter(QuestionAnswers.id.in_(question_answer_ids)).delete()
    db.commit()


def save_kyc_answers(db: Session, engage_id: int, request_answers: dict, db_data: list[QuestionAnswers], questions: dict, kyc_map: dict) -> bool:
    """Save the kyc answers."""

    from app.db.services.question_answers import get_delete_map

    question_version_map = {}
    for qid, qdata in questions.items():
        latest_version_key = next(iter(qdata.get("versions", {}).keys()))
        latest_version_data = qdata.get("versions", {}).get(latest_version_key)
        if latest_version_data.get("input_type") == "form":
            form_questions = latest_version_data.get("form_fields", {}).get("questions", {})
            for form_question_id, form_question_data in form_questions.items():
                question_version_map[form_question_id] = {"version": latest_version_key, "question_order": form_question_data.get("question_order")}
        else:
            question_version_map[qid] = {"version": latest_version_key, "question_order": latest_version_data.get("question_order")}
    update_list = []
    create_list = []
    delete_map = {}

    db_data_map = {}
    for data in db_data or []:
            eqa = data.engage_question_answers[0]
            db_data_map[str(data.question_identifier)] = {
                "answer": data.answer,
                "ans_object": data,
                "eqa_object": eqa
            }
    # db_data_map = {str(data.question_identifier): data for data in db_data}

    for qid, data in request_answers.items():
        if str(qid) in db_data_map:
            enq_obj = db_data_map[str(qid)].get("eqa_object")
            update_list.append({
                "id": int(db_data_map[str(qid)].get("ans_object").id),
                "answer": json.dumps(jsonable_encoder(data.get("answer"))),
                "version": question_version_map[str(qid)].get("version"),
                "enq_object": enq_obj
            })
        else:
            create_list.append({
                "question_identifier": qid,
                "version": question_version_map[str(qid)].get("version"),
                "answer": json.dumps(jsonable_encoder(data.get("answer"))),
                "question_order": int(question_version_map[str(qid)].get("question_order")) if question_version_map[str(qid)].get("question_order") is not None else None # type: ignore
            })

        delete_map = {}
        if qid in kyc_map:
            db_answer_id_map = {question_id:   {"question_answer_id": item.get("ans_object").id, "engage_question_answer_id": item.get("eqa_object").id} for question_id, item in db_data_map.items()}
            answer_data = data.get("answer")
            request_answer_list = [ans.get("value") for ans in answer_data]
            kyc_map_version = kyc_map.get(qid, {}).get("versions", {}).get(question_version_map[str(qid)].get("version"), {})
            options_list = [key for key in kyc_map_version.get("options_relationships", {}).keys()]
            map_type = kyc_map_version.get("type")

            if map_type == "multiple":
                #check answer_list and options_list are same
                if set(request_answer_list) == set(options_list):
                    return {}
                else:
                    delete_map = get_delete_map(kyc_map_version, request_answer_list, db_answer_id_map)
            else:
                delete_map = get_delete_map(kyc_map_version, request_answer_list, db_answer_id_map)

    if update_list:
        bulk_update_kyc_question_answers(db, update_list)

    if create_list:
        bulk_create_kyc_question_answers(db, engage_id, create_list)
    
    if delete_map:
        bulk_delete_kyc_question_answers(db, delete_map)

    return True


def submit_kyc_data(db: Session, current_user: User, request: SubmitKycRequest, options: list[dict], update_flag: bool = False, is_hold: bool = False) -> tuple[bool, int]:
    """Submit the kyc data for the case."""
    case_id = int(request.case_id)
    case_engage = db.query(CaseEngage).filter(CaseEngage.case_id == case_id).first()
    engage_id = case_engage.engage_id if case_engage is not None else None
    if engage_id is None:
        engage_id = create_engage_case(db, case_id, int(current_user.id)) # type: ignore

    questions = get_kyc_questions()
    data_status, db_data = get_kyc_data_from_db(db, case_id)
    if data_status is False:
        message = {
            "success": False,
            "message": "Error collecting Alignment Check data from database"
        }
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    request_answers = format_request_answers(request)
    case = db.query(Case).filter(Case.id == case_id).first()
    omit_required_questions = TRIAGE_OMIT_QUESTIONS if case is not None and case.is_triage else None
    valid, error_list = check_required_kyc_answers(
        request_answers, questions, options, db_data, update_flag, omit_required_questions
    )
    if valid is False:
        if error_list:
            error_messages = [str(error.get("message")) for error in error_list if error and error.get("message")]
            errors_str = ", ".join(error_messages)
            # raise ValueError(errors_str)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=errors_str)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_list)
    if engage_id is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": "Error in creating engage case"})
    
    try:
        with open(settings.KYC_MAP_FILE_PATH) as f:
            kyc_map = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": "Error loading Alignment Check questions map"}) from e

    result = save_kyc_answers(db, int(engage_id), request_answers, db_data, questions, kyc_map)
    if result is False:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"success": False, "message": "Error in saving Alignment Check answers"})

    if update_flag is False:    # if update_flag is True, the action is update, otherwise it is submit
        engage = db.query(Engage).filter(Engage.id == engage_id).first()
        if engage and is_hold is False:
            engage.is_kyc_completed = True

        # Update case is_kyc_completed flag
        if case:
            if is_hold is False:    # means alignment check is submitted, and not hold
                case.is_kyc_completed = True
                case.is_alignment_check_hold = False 
            else:
                case.is_alignment_check_hold = True    # means alignment check is hold

        db.commit()

    return True, int(engage_id)


def get_resolve_options_for_kyc(db: Session, resolve_id: int | None = None, engage_id: int | None = None) -> list[dict]:
    """
    Get the resolve options for the kyc.

    Rules:
    1. If question 4 is answered with marriage/civil partnership or other, then
        i. Add options :
            {"divorce": "Divorce or Separation from [partner first name]"}
            a. if question 5 is answered with our finances, then
                ii. Add options:
                    {"financial_claims": "Financial claims arising from divorce or civil partnership dissolution"},
                    {"financial_claims_variation" : "Deal with an appeal or change an existing financial court order"}
            b. if question 5 is answered with our children, then
                ii. Add options:
                    {"child_arrangements": "Child arrangements or Child maintenance"},
                    {"child_arrangements_variation": "Deal with an appeal or change an existing child arrangements court order"},
                    {"child_relocation": "International child relocation"},

    2. If question 4 is answered with co-habitation (living together), then
        i. Add options:
            {"separation": "Separation from [partner first name]"}
        a. if question 5 is answered with our finances, then
            ii. Add options:
                {"financial_claims": "Financial claims arising from separation"},
                {"appeal_or_variation": "Deal with an appeal or change an existing financial court order"},
        b. if question 5 is answered with our children, then
            ii. Add options:
                {"child_arrangements": "Child arrangements or Child maintenance"},
                {"child_arrangements_variation": "Deal with an appeal or change an existing child arrangements court order"},
                {"child_relocation": "International child relocation"},
    3. Add option:
        {"other": "Other"}
    """

    if engage_id is not None:
        from app.db.models.engage_question_answers import EngageQuestionAnswers

        question_answers = db.query(QuestionAnswers).join(EngageQuestionAnswers, QuestionAnswers.id == EngageQuestionAnswers.question_answer_id).filter(EngageQuestionAnswers.engage_id == engage_id).all()
        if question_answers is not None:
            # Filter only question identifiers 4 and 5
            filtered_questions = [qa for qa in question_answers if str(qa.question_identifier) in '15' ]

            # Check if both question 4 and 5 are present
            question_ids = {str(qa.question_identifier) for qa in filtered_questions} if filtered_questions is not None else {}

            is_exists = False
            if '15' in question_ids:
                is_exists = True

            if is_exists:
                # Build answer dictionary directly without intermediate list
                answer_dict = {}
                for qa in filtered_questions:
                    try:
                        parsed_answer = json.loads(str(qa.answer))
                        if parsed_answer and len(parsed_answer) > 0:
                            value = [d['value'] for d in parsed_answer]
                            answer_dict[str(qa.question_identifier)] = value
                    except (json.JSONDecodeError, IndexError, TypeError):
                        # Skip this question if parsing fails or data is malformed
                        continue
                
                # Check question 4 answer — marriage and other share the same KYC options
                if answer_dict.get("15", [])[0] in ("marriage", "other"):
                    options = []
                    options.append({"divorce": "Divorce or Separation from {partner_name}"})
                    options.append({"financial_claims": "Financial claims arising from divorce or civil partnership dissolution"})
                    options.append({"financial_claims_variation" : "Deal with an appeal or change an existing financial court order"})
                    options.append({"child_arrangements": "Child arrangements or Child maintenance"})
                    options.append({"child_arrangements_variation": "Deal with an appeal or change an existing child arrangements court order"})
                    options.append({"child_relocation": "International child relocation"})
                    options.append({"other": "Other"})
                    return options
                else:
                    options = []
                    options.append({"separation": "Separation from {partner_name}"})
                    options.append({"financial_claims": "Financial claims arising from separation"})
                    options.append({"appeal_or_variation": "Deal with an appeal or change an existing financial court order"})
                    options.append({"child_arrangements": "Child arrangements or Child maintenance"})
                    options.append({"child_arrangements_variation": "Deal with an appeal or change an existing child arrangements court order"})
                    options.append({"child_relocation": "International child relocation"})
                    options.append({"other": "Other"})
                    return options

        options = []
        options.append({"divorce": "Divorce or Separation from {partner_name}"})
        options.append({"financial_claims": "Financial claims arising from divorce or civil partnership dissolution"})
        options.append({"appeal_or_variation": "Deal with an appeal or change an existing financial court order"})
        options.append({"child_arrangements": "Child arrangements or Child maintenance"})
        options.append({"child_arrangements_variation": "Deal with an appeal or change an existing child arrangements court order"})
        options.append({"child_relocation": "International child relocation"})
        options.append({"other": "Other"})
        return options

    question_answers = db.query(QuestionAnswers).join(ResolveQuestionAnswers, QuestionAnswers.id == ResolveQuestionAnswers.question_answer_id).filter(ResolveQuestionAnswers.resolve_id == resolve_id).all()

    if question_answers is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": False, "message": "Question answers not found for the resolve"})

    # Filter only question identifiers 4 and 5
    filtered_questions = [qa for qa in question_answers if str(qa.question_identifier) in ['4', '5']]

    # Check if both question 4 and 5 are present
    question_ids = {str(qa.question_identifier) for qa in filtered_questions}

    if '4' not in question_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": False, "message": "Answer is not found for the resolve question 'Relationship Type'"})

    if '5' not in question_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": False, "message": "Answer is not found for the resolve question 'How can we help?'"})

    # Build answer dictionary directly without intermediate list
    answer_dict = {}
    for qa in filtered_questions:
        try:
            parsed_answer = json.loads(str(qa.answer))
            if parsed_answer and len(parsed_answer) > 0:
                value = [d['value'] for d in parsed_answer]
                answer_dict[str(qa.question_identifier)] = value
        except (json.JSONDecodeError, IndexError, TypeError):
            # Skip this question if parsing fails or data is malformed
            continue
    options = []
    # Check question 4 answer — marriage and other share the same KYC options
    if answer_dict.get("4", [])[0] in ("marriage", "other"):
        options.append({"divorce": "Divorce or Separation from {partner_name}"})
        if "finance" in answer_dict.get("5", []):
            options.append({"financial_claims": "Financial claims arising from divorce or civil partnership dissolution"})
            options.append({"financial_claims_variation" : "Deal with an appeal or change an existing financial court order"})
        if "children" in answer_dict.get("5", []):
            options.append({"child_arrangements": "Child arrangements or Child maintenance"})
            options.append({"child_arrangements_variation": "Deal with an appeal or change an existing child arrangements court order"})
            options.append({"child_relocation": "International child relocation"})

    else:
        options.append({"separation": "Separation from {partner_name}"})
        if "finance" in answer_dict.get("5", []):
            options.append({"financial_claims": "Financial claims arising from separation"})
            options.append({"appeal_or_variation": "Deal with an appeal or change an existing financial court order"})
        if "children" in answer_dict.get("5", []):
            options.append({"child_arrangements": "Child arrangements or Child maintenance"})
            options.append({"child_arrangements_variation": "Deal with an appeal or change an existing child arrangements court order"})
            options.append({"child_relocation": "International child relocation"})
    options.append({"other": "Other"})
    return options


def _format_kyc_options_list(options_list: list) -> list[str] | None:
    """Format KYC options list to a list of option strings."""
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


def format_kyc_answers(db: Session, case_id: int) -> list[dict]:
    """Format the kyc answers."""
    kyc_answers = get_kyc_data(db, case_id)
    formatted_kyc_answers = []

    updated_kyc_answers = {}
    for qid, items in kyc_answers.items():
        if qid == "1":
            customer_full_name = ""
            for f_qid, f_items in items.get("form_fields", {}).get("questions", {}).items():
                if f_qid == "1.1":
                    customer_first_name = f_items.get("answer", [])[0].get("value", "")
                    customer_full_name = customer_first_name if customer_first_name else ""
                elif f_qid == "1.3":
                    customer_last_name = f_items.get("answer", [])[0].get("value", "")
                    customer_full_name = customer_full_name + " " + customer_last_name if customer_last_name else ""
            # customer name can be accessed from 1.1 and 1.3 (even if already answered for 1)
            updated_kyc_answers[qid] = {
                "question": items.get("title", ""),
                "answer": [{"value": customer_full_name}],
                "options": items.get("options", [])
            }
        elif qid == "2":
            partner_full_name = ""
            for f_qid, f_items in items.get("form_fields", {}).get("questions", {}).items():
                if f_qid == "2.1":
                    partner_first_name = f_items.get("answer", [])[0].get("value", "")
                    partner_full_name = partner_first_name if partner_first_name else ""
                elif f_qid == "2.3":
                    partner_last_name = f_items.get("answer", [])[0].get("value", "")
                    partner_full_name = partner_full_name + " " + partner_last_name if partner_last_name else ""
            # partner name can be accessed from 2.1 and 2.3 (even if already answered for 2)
            updated_kyc_answers[qid] = {
                "question": items.get("title", ""),
                "answer": [{"value": partner_full_name}],
                "options": items.get("options", [])
            }
        else:
            updated_kyc_answers[qid] = items

    partner_name = None
    for qid, items in updated_kyc_answers.items(): 
        option_dict = {}
        for opt in items.get("options", []):
            if isinstance(opt, dict):
                option_dict.update(opt)  # merge options (flatten)
        question_text = items.get("question", "")
        answer = items.get("answer", [])
        answer_text = ""
        for ans in answer:
            if isinstance(ans, dict):
                if "value" in ans:
                    if qid == "1":
                        answer_value = ans.get("value", "")
                    elif qid == "2":
                        answer_value = ans.get("value", "")
                        partner_name = answer_value
                    else:
                        answer_value = ans.get("value", "")

                    if answer_value in option_dict:
                        answer_value = option_dict.get(answer_value)
                    answer_text = answer_text + answer_value + " | "
        answer_text = answer_text.rstrip(" | ")
        if answer_text:  # Only add if answer is not empty
            # Get options list if available
            options_list = items.get("options", [])
            formatted_options = _format_kyc_options_list(options_list)
            
            item = {
                "question": question_text,
                "answer": answer_text
            }
            if formatted_options:
                item["options"] = formatted_options
            formatted_kyc_answers.append(item)

    if partner_name is not None:
        for item in formatted_kyc_answers:
            k = item.get("question", "")
            if isinstance(k, str) and "{partner_name}" in k:
                k_new = k.replace("{partner_name}", str(partner_name))
                # Remove old key and add new
                item["question"] = k_new
            
            if options := item.get("options", []):
                item["options"] = [opt.replace("{partner_name}", str(partner_name)) for opt in options]
            
            answer = item.get("answer", "")
            if isinstance(answer, str) and "{partner_name}" in answer:
                answer_new = answer.replace("{partner_name}", str(partner_name))
                item["answer"] = answer_new

    return formatted_kyc_answers


def get_resolve_map_for_kyc(db: Session, resolve_id: int) -> dict:
    """Get the resolve map for the kyc."""
    db_answer_map = {}
    question_answers = db.query(QuestionAnswers).join(ResolveQuestionAnswers, QuestionAnswers.id == ResolveQuestionAnswers.question_answer_id).filter(ResolveQuestionAnswers.resolve_id == resolve_id).all()
    if question_answers is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"success": False, "message": "Question answers not found for the resolve"})
    for qa in question_answers:
        if str(qa.question_identifier) in ["3", "4", "23", "16", "14"]:
            db_answer_map[str(qa.question_identifier)] = json.loads(str(qa.answer))
    
    return db_answer_map


# def get_customer_phone_from_kyc(db: Session, case_id: int) -> str | None:
#     """Get the customer phone from the kyc."""
#     is_data, kyc_answers = get_kyc_data_from_db(db, case_id)
#     if is_data is False:
#         return None
#     for data in kyc_answers:
#         if data.question_identifier == KYC_PHONE_QUESTION_IDENTIFIER:
#             answer = json.loads(str(data.answer)) if data.answer else []
#             if answer and len(answer) > 0:
#                 return answer[0].get("value", "")
#     return None
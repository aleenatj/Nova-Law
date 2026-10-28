"""Engage feedback API: POST to submit feedback (open), GET to list (navigator only), GET export CSV."""

import csv
import io
import json
import logging
from datetime import datetime, time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_current_active_user
from app.db.models import User
from app.db.services.engage_feedback import (
    create_engage_feedback,
    get_engage_feedback,
)
from app.enums.engage_feedback import (
    AGE_RANGE_OPTIONS,
    COMPLETION_TIME_OPTIONS,
    GENDER_OPTIONS,
    HELP_LEVEL_OPTIONS,
    HELP_REASON_OPTIONS,
    HELPER_TYPE_OPTIONS,
    OVERALL_EXPERIENCE_OPTIONS,
    PREPAREDNESS_LEVEL_OPTIONS,
    RECOMMENDATION_SCORE_OPTIONS,
    SESSION_COUNT_OPTIONS,
    TIME_VALUE_FEEDBACK_OPTIONS,
)
from app.schemas.v1.engage_feedback import (
    EngageFeedbackCreateRequest,
    EngageFeedbackCreateResponse,
    EngageFeedbackData,
    EngageFeedbackListData,
    EngageFeedbackListRequest,
    EngageFeedbackListResponse,
)
from app.utils.dependencies import get_db
from app.utils.validators import validate_order_params

logger = logging.getLogger(__name__)

router = APIRouter()


def _option_value(options: dict, key: int | None) -> str | None:
    """Return the display value for an option key, or None if key is None or missing."""
    if key is None:
        return None
    return options.get(key)


def _option_list(options: dict, keys: list | None) -> list[str] | None:
    """Return list of display values for option keys, or None if keys is None/empty."""
    if not keys:
        return None
    return [options.get(k) for k in keys if options.get(k) is not None]


def _create_engage_feedback_response_data(feedback) -> dict:
    """Create engage feedback response data from EngageFeedback model; option fields as display values."""
    return {
        "id": feedback.id,
        "time_value_feedback": _option_value(TIME_VALUE_FEEDBACK_OPTIONS, feedback.time_value_feedback),
        "completion_time": _option_value(COMPLETION_TIME_OPTIONS, feedback.completion_time),
        "session_count": _option_value(SESSION_COUNT_OPTIONS, feedback.session_count),
        "help_level": _option_value(HELP_LEVEL_OPTIONS, feedback.help_level),
        "helper_type": _option_list(HELPER_TYPE_OPTIONS, feedback.helper_type),
        "help_reason": _option_list(HELP_REASON_OPTIONS, feedback.help_reason),
        "preparedness_level": _option_value(PREPAREDNESS_LEVEL_OPTIONS, feedback.preparedness_level),
        "age_range": _option_value(AGE_RANGE_OPTIONS, feedback.age_range),
        "gender": _option_value(GENDER_OPTIONS, feedback.gender),
        "gender_other": feedback.gender_other,
        "overall_experience": _option_value(OVERALL_EXPERIENCE_OPTIONS, feedback.overall_experience),
        "improvement_feedback": feedback.improvement_feedback,
        "recommendation_score": _option_value(RECOMMENDATION_SCORE_OPTIONS, feedback.recommendation_score),
        "created_at": feedback.created_at,
        "updated_at": feedback.updated_at,
    }


def _load_engage_feedback_csv_questions() -> list[dict]:
    """Load CSV column definitions (id, field, label) from config JSON. Order defines CSV column order."""
    with open(settings.ENGAGE_FEEDBACK_CSV_QUESTIONS_FILE_PATH, encoding="utf-8") as f:
        return json.load(f)


_CSV_QUESTIONS = _load_engage_feedback_csv_questions()
CSV_HEADERS = [q["label"] for q in _CSV_QUESTIONS]
_CSV_COLUMN_FIELDS = [q["field"] for q in _CSV_QUESTIONS]


def _row_to_csv_cells(row: dict) -> list[str]:
    """Convert a feedback row to a list of string values for CSV (same order as CSV_HEADERS)."""
    def _dt(v):
        if v is None:
            return ""
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S")
        return str(v)

    def _join(v):
        if v is None:
            return ""
        if isinstance(v, list):
            return ", ".join(str(x) for x in v if x is not None)
        return str(v) if v else ""

    out = []
    for col_field in _CSV_COLUMN_FIELDS:
        val = row.get(col_field)
        if col_field == "created_at":
            out.append(_dt(val))
        elif col_field in ("helper_type", "help_reason"):
            out.append(_join(val) or "")
        else:
            out.append(str(val) if val else "")
    return out


ALLOWED_ORDER_FIELDS = {"id", "created_at"}


@router.get("/engage-feedback/export")
def export_engage_feedback_csv(
    list_request: EngageFeedbackListRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Export engage feedback to CSV. Navigator only.
    Same query params as list: start_date, end_date (YYYY-MM-DD), order_by, order_dir.
    Returns .csv file download.
    """
    validate_order_params(
        list_request.order_by,
        list_request.order_dir,
        ALLOWED_ORDER_FIELDS,
    )
    start_dt = (
        datetime.combine(list_request.start_date, time.min)
        if list_request.start_date
        else None
    )
    end_dt = (
        datetime.combine(list_request.end_date, time.max)
        if list_request.end_date
        else None
    )
    results = get_engage_feedback(
        db,
        order_by=list_request.order_by,
        order_dir=list_request.order_dir,
        start_date=start_dt,
        end_date=end_dt,
    )
    rows = [_create_engage_feedback_response_data(r) for r in results]

    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADERS)
    for row in rows:
        writer.writerow(_row_to_csv_cells(row))

    buffer.seek(0)
    # Use bytes for response; CSV is UTF-8
    body = buffer.getvalue().encode("utf-8")

    # Filename includes selected date range: engage-feedback-YYYY-MM-DD-to-YYYY-MM-DD.csv
    start_str = list_request.start_date.strftime("%Y-%m-%d") if list_request.start_date else None
    end_str = list_request.end_date.strftime("%Y-%m-%d") if list_request.end_date else None
    if start_str and end_str:
        filename = f"engage-feedback-{start_str}-to-{end_str}.csv"
    elif start_str:
        filename = f"engage-feedback-{start_str}-to.csv"
    elif end_str:
        filename = f"engage-feedback-to-{end_str}.csv"
    else:
        filename = "engage-feedback.csv"

    return StreamingResponse(
        io.BytesIO(body),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

@router.post("/engage-feedback", response_model=EngageFeedbackCreateResponse)
def create_feedback(
    request: EngageFeedbackCreateRequest,
    db: Session = Depends(get_db),
) -> EngageFeedbackCreateResponse:
    """
    Submit engage feedback (open endpoint). helper_type/help_reason: enum keys only, saved as [1, 2].
    Returns all saved data with encrypted id.
    """
    payload = {k: v for k, v in request.model_dump().items() if v is not None}
    # Check if any field has a value worth saving
    if not any(
        not (isinstance(v, str) and not v.strip()) and not (isinstance(v, list) and len(v) == 0)
        for v in payload.values()
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "message": "No data to be saved"},
        )

    try:
        feedback = create_engage_feedback(db, payload)
        engage_feedback_data = EngageFeedbackData.model_validate(_create_engage_feedback_response_data(feedback))
        return EngageFeedbackCreateResponse(
            success=True,
            message=[{"success": True, "message": "Feedback submitted successfully"}],
            data=engage_feedback_data,
        )
    except Exception:
        logger.exception("Failed to create engage feedback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save feedback",
        ) from None


@router.get("/engage-feedback", response_model=EngageFeedbackListResponse)
def list_engage_feedback(
    list_request: EngageFeedbackListRequest = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> EngageFeedbackListResponse:
    """
    List engage feedback with pagination, ordering and date range filter on created_at.
    Navigator only. Query params: page, limit, order_by, order_dir, start_date, end_date.
    """
    validate_order_params(
        list_request.order_by,
        list_request.order_dir,
        ALLOWED_ORDER_FIELDS,
    )
    start_dt = (
        datetime.combine(list_request.start_date, time.min)
        if list_request.start_date
        else None
    )
    end_dt = (
        datetime.combine(list_request.end_date, time.max)
        if list_request.end_date
        else None
    )
    results, total_count = get_engage_feedback(
        db,
        page=list_request.page,
        limit=list_request.limit,
        order_by=list_request.order_by,
        order_dir=list_request.order_dir,
        start_date=start_dt,
        end_date=end_dt,
        paginate=True,
    )
    items = [
        EngageFeedbackData.model_validate(_create_engage_feedback_response_data(r))
        for r in results
    ]
    return EngageFeedbackListResponse(
        success=True,
        message=[{"success": True, "message": "Engage feedback list retrieved"}],
        data=EngageFeedbackListData(
            total_count=total_count,
            records_in_page=len(items),
            items=items,
        ),
    )

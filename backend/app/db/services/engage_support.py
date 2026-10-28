"""Service for engage support operations."""

import csv
import io
import json
from datetime import date, datetime, time

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.email import email_service
from app.db.models.engage_support import EngageSupport
from app.enums.engage_support import (
    HELPED_RESOLVE_ISSUE_OPTIONS,
    HOW_CAN_HELP_OPTIONS,
    ISSUES_LISTED_OPTIONS,
    SECTION_STUCK_ON_OPTIONS,
    TROUBLE_NAVIGATING_ENGAGE_OPTIONS,
    TROUBLE_WITH_ANY_OPTIONS,
)
from app.schemas.v1.engage_support import EngageSupportData, EngageSupportListRequest

ALLOWED_ORDER_FIELDS = {"id", "created_at"}


def _option_value(options: dict, key: int | None) -> str | None:
    if key is None:
        return None
    return options.get(key)


def _load_csv_questions() -> list[dict]:
    with open(settings.ENGAGE_SUPPORT_CSV_QUESTIONS_FILE_PATH, encoding="utf-8") as f:
        return json.load(f)


_CSV_QUESTIONS = _load_csv_questions()
CSV_HEADERS = [q["label"] for q in _CSV_QUESTIONS]
_CSV_COLUMN_FIELDS = [q["field"] for q in _CSV_QUESTIONS]


def create_engage_support(db: Session, data: dict) -> EngageSupport:
    """Create an engage support record. Returns the created model."""
    support = EngageSupport(**data)
    db.add(support)
    db.commit()
    db.refresh(support)
    return support


def get_engage_support(
    db: Session,
    page: int | None = None,
    limit: int | None = None,
    order_by: str = "created_at",
    order_dir: str = "desc",
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    paginate: bool = False,
) -> list[EngageSupport] | tuple[list[EngageSupport], int]:
    """
    Fetch engage support submissions with optional pagination and date filtering.

    Returns:
      - If paginate=True: (list[EngageSupport], total_count)
      - If paginate=False: list[EngageSupport]
    """
    query = db.query(EngageSupport)

    if start_date is not None:
        query = query.filter(EngageSupport.created_at >= start_date)
    if end_date is not None:
        query = query.filter(EngageSupport.created_at <= end_date)

    order_column = getattr(EngageSupport, order_by, EngageSupport.created_at)
    direction = (order_dir or "desc").strip().lower()
    query = query.order_by(
        asc(order_column) if direction == "asc" else desc(order_column)
    )

    total_count = query.count() if paginate else None

    if page is not None and limit is not None:
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
    elif limit is not None:
        query = query.limit(limit)

    results = query.all()
    return (results, total_count) if paginate else results


def engage_support_to_response_data(support: EngageSupport) -> dict:
    """Map EngageSupport model to response dict; option fields as display values."""
    return {
        "id": support.id,
        "name": support.name,
        "phone": support.phone,
        "email": support.email,
        "how_can_help": _option_value(HOW_CAN_HELP_OPTIONS, support.how_can_help),
        "trouble_with_any": _option_value(TROUBLE_WITH_ANY_OPTIONS, support.trouble_with_any),
        "trouble_navigating_engage": _option_value(
            TROUBLE_NAVIGATING_ENGAGE_OPTIONS, support.trouble_navigating_engage
        ),
        "section_stuck_on": _option_value(SECTION_STUCK_ON_OPTIONS, support.section_stuck_on),
        "issues_listed": _option_value(ISSUES_LISTED_OPTIONS, support.issues_listed),
        "new_lawfirm": support.new_lawfirm,
        "helped_resolve_issue": _option_value(
            HELPED_RESOLVE_ISSUE_OPTIONS, support.helped_resolve_issue
        ),
        "support_query_message": support.support_query_message,
        "created_at": support.created_at,
        "updated_at": support.updated_at,
    }


def engage_support_to_schema(support: EngageSupport) -> EngageSupportData:
    """Convert EngageSupport model to response schema with encrypted id."""
    return EngageSupportData.model_validate(engage_support_to_response_data(support))


def has_saveable_data(payload: dict) -> bool:
    """Return True if payload contains at least one non-empty value."""
    return any(
        not (isinstance(v, str) and not v.strip())
        for v in payload.values()
    )


def parse_date_range(
    start_date: date | None,
    end_date: date | None,
) -> tuple[datetime | None, datetime | None]:
    """Convert optional date filters to datetime bounds for created_at filtering."""
    start_dt = datetime.combine(start_date, time.min) if start_date else None
    end_dt = datetime.combine(end_date, time.max) if end_date else None
    return start_dt, end_dt


def _row_to_csv_cells(row: dict) -> list[str]:
    def _dt(value):
        if value is None:
            return ""
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        return str(value)

    out = []
    for col_field in _CSV_COLUMN_FIELDS:
        val = row.get(col_field)
        if col_field == "created_at":
            out.append(_dt(val))
        else:
            out.append(str(val) if val else "")
    return out


def build_csv_export_body(rows: list[dict]) -> bytes:
    """Build UTF-8 CSV bytes from response row dicts."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(CSV_HEADERS)
    for row in rows:
        writer.writerow(_row_to_csv_cells(row))
    buffer.seek(0)
    return buffer.getvalue().encode("utf-8")


def build_export_filename(
    start_date: date | None,
    end_date: date | None,
) -> str:
    start_str = start_date.strftime("%Y-%m-%d") if start_date else None
    end_str = end_date.strftime("%Y-%m-%d") if end_date else None
    if start_str and end_str:
        return f"engage-support-{start_str}-to-{end_str}.csv"
    if start_str:
        return f"engage-support-{start_str}-to.csv"
    if end_str:
        return f"engage-support-to-{end_str}.csv"
    return "engage-support.csv"


def export_engage_support_csv(db: Session, list_request: EngageSupportListRequest) -> tuple[bytes, str]:
    """Fetch filtered records and return CSV body bytes plus download filename."""
    start_dt, end_dt = parse_date_range(list_request.start_date, list_request.end_date)
    results = get_engage_support(
        db,
        order_by=list_request.order_by,
        order_dir=list_request.order_dir,
        start_date=start_dt,
        end_date=end_dt,
    )
    rows = [engage_support_to_response_data(r) for r in results]
    body = build_csv_export_body(rows)
    filename = build_export_filename(list_request.start_date, list_request.end_date)
    return body, filename


def _format_support_answer(value) -> str:
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")
    return str(value)


async def engage_support_send_email(support: EngageSupport) -> dict:
    """Send an email to the support team."""
    support_data = engage_support_to_response_data(support)
    emails = [
        email.strip()
        for email in settings.ENGAGE_SUPPORT_EMAILS.split(",")
        if email.strip()
    ]
    subject = f"Support Ticket - {support.name}"
    qa_rows = []
    for question in _CSV_QUESTIONS:
        if question["field"] == "created_at":
            continue
        answer = support_data.get(question["field"])
        if answer is None or (isinstance(answer, str) and not answer.strip()):
            continue
        qa_rows.append(
            {
                "label": question["label"],
                "answer": _format_support_answer(answer),
            }
        )

    response = None
    if emails:
        for email in emails:
            response = await email_service.send_email(
                to_email=email,
                subject=subject,
                template=email_service.EmailTemplate.ENGAGE_SUPPORT_EMAIL,
                context={"qa_rows": qa_rows},
            )

    return {
        "success": True,
        "message": "Email sent successfully",
        "data": response,
    }
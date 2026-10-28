"""Cal.com integration services."""

import hashlib
import hmac
import json
from datetime import date, datetime, timedelta
from typing import Any
from urllib.parse import quote, urlencode

import httpx
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

AVAILABILITY_DEFAULT_RANGE_DAYS = 30

SUPPORTED_WEBHOOK_EVENTS = frozenset(
    {
        "BOOKING_CREATED",
        "BOOKING_CANCELLED",
        "BOOKING_RESCHEDULED",
    }
)


# GET /v2/bookings is not registered for 2024-09-04 (returns 404). Slots still
# use that version, so bookings lookups pin 2024-08-13.
CAL_BOOKINGS_API_VERSION = "2024-08-13"


def _cal_headers(*, api_version: str | None = None) -> dict[str, str]:
    """Build auth and version headers for Cal.com API v2."""
    if not settings.CAL_API_KEY:
        raise ValueError("CAL_API_KEY is not configured")

    return {
        "Authorization": f"Bearer {settings.CAL_API_KEY}",
        "cal-api-version": api_version or settings.CAL_API_VERSION,
        "Content-Type": "application/json",
    }


def _parse_start_date(start: str) -> date:
    """Parse a start value into a calendar date."""
    value = start.strip()
    if len(value) >= 10 and value[4] == "-" and value[7] == "-":
        return date.fromisoformat(value[:10])
    return datetime.fromisoformat(value.replace("Z", "+00:00")).date()


def resolve_availability_end_date(start: str, end: str | None = None) -> str:
    """Return end date, defaulting to start + 30 days when omitted."""
    if end:
        return end
    end_date = _parse_start_date(start) + timedelta(days=AVAILABILITY_DEFAULT_RANGE_DAYS)
    return end_date.strftime("%Y-%m-%d")


def get_first_available_slot(slots_response: dict[str, Any]) -> dict[str, str] | None:
    """Return the earliest available slot from a Cal.com slots payload."""
    data = slots_response.get("data", slots_response)
    if not isinstance(data, dict) or not data:
        return None

    for date_key in sorted(data.keys()):
        day_slots = data[date_key]
        if not isinstance(day_slots, list) or not day_slots:
            continue

        first_slot = day_slots[0]
        if isinstance(first_slot, dict):
            slot_start = first_slot.get("start")
            slot_end = first_slot.get("end")
        else:
            slot_start = str(first_slot)
            slot_end = None

        if slot_start:
            return {
                "date": date_key,
                "start": slot_start,
                "end": slot_end,
            }

    return None


def get_available_slots(*, start: str, end: str | None = None) -> dict[str, Any]:
    """Fetch available consultation slots from Cal.com.

    Args:
        start: Start of availability range (YYYY-MM-DD or ISO 8601 UTC).
        end: Optional end of availability range. Defaults to start + 30 days.

    Returns:
        Cal.com slots payload (typically ``{"status": "success", "data": {...}}``).

    Raises:
        ValueError: When required config is missing.
        httpx.HTTPStatusError: When Cal.com returns a non-success status.
    """
    if not settings.CAL_NN_CALL_BACK_SLUG:
        raise ValueError("CAL_NN_CALL_BACK_SLUG is not configured")
    if not settings.CAL_USERNAME:
        raise ValueError("CAL_USERNAME is not configured")

    resolved_end = resolve_availability_end_date(start, end)
    params: dict[str, Any] = {
        "start": start,
        "end": resolved_end,
        "eventTypeSlug": settings.CAL_NN_CALL_BACK_SLUG,
        "username": settings.CAL_USERNAME,
        "format": "range",
    }

    url = f"{settings.CAL_API_BASE_URL}/slots"
    with httpx.Client(timeout=30.0) as client:
        response = client.get(url, headers=_cal_headers(), params=params)
        response.raise_for_status()
        return response.json()


def _as_meeting_url(value: object) -> str:
    """Return ``value`` only when it is an http(s) video/join URL.

    Cal.com ``GET /v2/bookings`` sets ``meetingUrl`` to ``location``. When the
    event location is attendee phone, both fields are the phone number, which
    must not be treated as a join URL.
    """
    text = str(value or "").strip()
    if text.startswith("http://") or text.startswith("https://"):
        return text
    return ""


def get_last_booking_by_attendee_email(attendee_email: str) -> dict[str, str]:
    """Fetch the most recent Cal.com booking for an attendee email.

    Uses GET /v2/bookings with ``attendeeEmail`` and ``sortCreated=desc``.
    This endpoint requires ``cal-api-version: 2024-08-13``; ``2024-09-04``
    (used for slots) returns 404. Field names differ from webhook payloads
    (``start``/``end`` vs webhook ``startTime``/``endTime``). Video join URL
    is taken from ``meetingUrl``, ``location``, or ``metadata.videoCallUrl``
    only when the value is an http(s) URL (not a phone number).

    Returns:
        Dict with ``meeting_url``, ``start_time``, and ``end_time`` (empty strings
        when no booking is found).
    """
    email = (attendee_email or "").strip().lower()
    if not email:
        return {"meeting_url": "", "start_time": "", "end_time": ""}

    # httpx ``params`` encodes both '+' and '@' (%2B / %40). Cal.com treats an
    # unencoded '+' as a space and 404s when '@' is percent-encoded, so encode
    # '+' as %2B and leave '@' as-is on the query string.
    query = urlencode(
        {
            "attendeeEmail": email,
            "sortCreated": "desc",
            "take": 1,
        },
        quote_via=quote,
        safe="@",
    )
    url = f"{settings.CAL_API_BASE_URL}/bookings?{query}"
    with httpx.Client(timeout=30.0) as client:
        response = client.get(
            url,
            headers=_cal_headers(api_version=CAL_BOOKINGS_API_VERSION),
        )
        response.raise_for_status()
        payload = response.json()

    data = payload.get("data", [])
    if not isinstance(data, list) or not data:
        logger.warning("No Cal.com bookings found for attendee email %s", email)
        return {"meeting_url": "", "start_time": "", "end_time": ""}

    booking = data[0] if isinstance(data[0], dict) else {}
    metadata = booking.get("metadata") if isinstance(booking.get("metadata"), dict) else {}
    meeting_url = (
        _as_meeting_url(booking.get("meetingUrl"))
        or _as_meeting_url(booking.get("location"))
        or _as_meeting_url(metadata.get("videoCallUrl"))
    )
    if not meeting_url:
        logger.warning(
            "No Cal.com video meeting URL for attendee email %s (location=%r)",
            email,
            booking.get("location"),
        )
    return {
        "meeting_url": meeting_url,
        "start_time": str(booking.get("start") or ""),
        "end_time": str(booking.get("end") or ""),
    }


def verify_webhook_signature(payload: bytes, signature: str | None) -> bool:
    """Verify Cal.com webhook HMAC-SHA256 signature.

    Cal.com sends the hex digest in the ``X-Cal-Signature-256`` header.
    Verification is skipped only when ``CAL_WEBHOOK_SECRET`` is unset
    (e.g. local development without a configured secret).
    """
    secret = settings.CAL_WEBHOOK_SECRET
    if not secret:
        logger.warning("CAL_WEBHOOK_SECRET is not configured; skipping signature verification")
        return True

    if not signature:
        return False

    expected = hmac.new(
        secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)


def parse_webhook_payload(payload: bytes) -> dict[str, Any]:
    """Parse Cal.com webhook JSON body."""
    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Invalid webhook JSON payload") from exc
    if not isinstance(data, dict):
        raise ValueError("Webhook payload must be a JSON object")
    return data


def save_shcedule_info_for_timeline(db: Session, event: dict[str, Any]) -> bool:
    """
    Save schedule info as question_answers for timeline event.
    Updates user phone number
    """
    from app.db.services.user import get_user_by_email
    from app.db.models.case import Case
    from app.db.models.case_engage import CaseEngage
    from app.db.models.case_customer import CaseCustomer
    from app.db.models.customer import Customer
    from sqlalchemy.orm import joinedload
    from app.db.models.question_answers import QuestionAnswers
    from app.db.models.engage_question_answers import EngageQuestionAnswers
    from app.db.services.customer import update_customer_phone_number

    try:
        
        start_time = event.get("payload", {}).get("startTime", "")
        end_time = event.get("payload", {}).get("endTime", "")
        attendees = event.get("payload", {}).get("attendees", [])
        attendee_phone_number = attendees[0].get("phoneNumber", "")
        attendee_email = attendees[0].get("email", "")
        # video_call_data = cal_event.get("payload", {}).get("videoCallData", {})
        # meeting_url = video_call_data.get("url", "")

        user = get_user_by_email(db, attendee_email)
        if not user:
            raise ValueError("Book Free Call event: User not found")  # noqa: TRY301

        update_customer_phone_number(db, user.id, attendee_phone_number)

        # customer_name = user.first_name if user.first_name else "" + " " + user.last_name if user.last_name else ""

        customer = user.customer
        if not customer:
            raise ValueError("Book Free Call event: Customer not found")  # noqa: TRY301
        case = db.query(Case).options(
            joinedload(Case.case_customers)
            .joinedload(CaseCustomer.customer),
        ).join(CaseCustomer, CaseCustomer.case_id == Case.id)\
            .join(Customer, Customer.id == CaseCustomer.customer_id)\
            .filter(
            Customer.id == customer.id
            ).first()
        if not case:
            raise ValueError("Book Free Call event: Case not found")  # noqa: TRY301

        case_id = case.id

        case_engage = db.query(CaseEngage).filter(CaseEngage.case_id == case_id).first()
        engage_id = case_engage.engage_id if case_engage is not None else None

        # Auto fill Book free call details as engage answer - Question Identifier as 'book_free_call'
        # Build question answer objects using EXPLICIT MAPPING
        qa = (
            db.query(QuestionAnswers)
            .join(
                EngageQuestionAnswers,
                EngageQuestionAnswers.question_answer_id == QuestionAnswers.id,
            )
            .filter(
                EngageQuestionAnswers.engage_id == engage_id,
                QuestionAnswers.question_identifier == "book_free_call",
            )
            .first()
        )
        if qa:
            qa.answer = json.dumps([{
                "value": {
                    "start_time": start_time,
                    "end_time": end_time,
                    "attendee_phone_number": attendee_phone_number,
                }
            }])
            db.commit()
            return True

        question_answer_objects = []
        answer = json.dumps([{"value": {"start_time": start_time, "end_time": end_time, "attendee_phone_number": attendee_phone_number}}])
        qa_obj = QuestionAnswers(
            version="1",
            answer=answer,
            question_identifier="book_free_call",
            question_order=1,
        )
        question_answer_objects.append(qa_obj)
        # Bulk insert question answers
        db.add_all(question_answer_objects)
        db.flush()  # Get IDs for all objects

        # Create EngageQuestionAnswers mappings in one go
        engage_question_answers = [
            EngageQuestionAnswers(
                engage_id=engage_id,
                question_answer_id=qa_obj.id
            )
            for qa_obj in question_answer_objects
        ]

        db.add_all(engage_question_answers)
        db.commit()

        return True
    except Exception as e:
        logger.exception(f"Book Free Call event: Error in save_shcedule_info_for_timeline: {e}")
        return False

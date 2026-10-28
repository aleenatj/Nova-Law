"""Analytics reporting (funnel queries against ``session`` + ``analytics_event``)."""

from __future__ import annotations

import copy
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable
from urllib.parse import parse_qsl, urlparse
from uuid import UUID, uuid4

from app.enums.analytics import (
    COMPARE_PERIOD_DAYS,
    AnalyticsEvents,
    CompareFilterEnum,
    ComparePeriodEnum,
    SourceEnum,
)
from app.enums.case import CaseStatusEnum

from sqlalchemy import (
    Integer,
    Numeric,
    String,
    and_,
    case,
    cast,
    false,
    literal,
    null,
    or_,
    select,
    true,
    union,
    union_all,
    update,
)
from sqlalchemy.orm import Session as OrmSession
from sqlalchemy.sql import func

from app.db.database import SessionLocal
from app.db.models.analytics_event import AnalyticsEvent
from app.db.models.case import Case
from app.db.models.case_customer import CaseCustomer
from app.db.models.customer import Customer
from app.db.models.deletion_request import DeletionRequest
from app.db.models.session import Identity, Session as AnalyticsSession
from app.db.models.user import User
from app.db.models.user_role import UserRole
from app.enums.deletion_request import (
    DeletionRequestStatus,
    DeletionRequestSubjectType,
)
from app.enums.events import EventType
from app.enums.user_role import UserRoleEnum
from app.schemas.v1.analytics import AnalyticsReportData, GetAnalyticsRequest
from app.utils.analytics_device import (
    apply_parsed_device_to_session,
    parse_session_device_fields,
)
# from app.utils.formatters import format_currency_compact

_END_TO_END_FUNNEL_ROWS: tuple[tuple[int, str], ...] = (
    (1, "site_visit"),
    (2, "resolve_completed"),
    (3, "case_opened"),
    # book_a_free_first_call skipped for now
    (4, "low_intent_free_call_scheduled"),
    # (4, "view_matching_experts"),
    # (5, "connect_with_expert"),
    # (6, "next_steps_with_nova"),
    (5, "alignment_check_completed"),
    (6, "match_confirmed"),
    (7, "profile_card_sent"),
    (8, "expert_assigned"),
    (9, "engage_get_started"),
)
# Pre-case steps use session-scoped strict funnel; from case_opened onward use case_id.
# A case enters only after its session reached ``resolve_completed`` and the
# ``case_opened`` event is tagged with this journey.
_RESOLVE_CASE_OPENED_FUNNEL = "resolve"
_TRIAGE_CASE_OPENED_FUNNEL = "triage"
_END_TO_END_SESSION_FUNNEL_ROWS: tuple[tuple[int, str], ...] = _END_TO_END_FUNNEL_ROWS[:2]
_END_TO_END_CASE_FUNNEL_ROWS: tuple[tuple[int, str], ...] = _END_TO_END_FUNNEL_ROWS[2:]
_END_TO_END_CASE_STEP_INDICES: tuple[int, ...] = tuple(
    si for si, _ in _END_TO_END_CASE_FUNNEL_ROWS
)
# General reports: conversion by source, active vs stalled, average time.
# Session step is ``site_visit`` only. Case steps start at ``case_opened``.
# Resolve and high-intent steps are not part of this funnel.
_GENERAL_FUNNEL_ROWS: tuple[tuple[int, str], ...] = (
    (1, "site_visit"),
    (2, "case_opened"),
    (3, "alignment_check_completed"),
    (4, "match_confirmed"),
    (5, "profile_card_sent"),
    (6, "expert_assigned"),
    (7, "engage_get_started"),
)
_GENERAL_SESSION_FUNNEL_ROWS: tuple[tuple[int, str], ...] = _GENERAL_FUNNEL_ROWS[:1]
_GENERAL_CASE_FUNNEL_ROWS: tuple[tuple[int, str], ...] = _GENERAL_FUNNEL_ROWS[1:]
_GENERAL_CASE_STEP_INDICES: tuple[int, ...] = tuple(
    si for si, _ in _GENERAL_CASE_FUNNEL_ROWS
)
# ``site_visit`` is returned as ``sessions``. Case steps start after high intent completes.
_END_TO_END_TRIAGE_FUNNEL_ROWS: tuple[tuple[int, str], ...] = (
    (1, "site_visit"),
    # book_a_free_first_call skipped for now
    (2, "high_intent_free_call_scheduled"),
    (3, "complete_high_intent"),
    (4, "case_opened"),
    (5, "alignment_check_completed"),
    (6, "match_confirmed"),
    (7, "profile_card_sent"),
    (8, "expert_assigned"),
    (9, "engage_get_started"),
)
_END_TO_END_TRIAGE_SESSION_FUNNEL_ROWS: tuple[tuple[int, str], ...] = (
    _END_TO_END_TRIAGE_FUNNEL_ROWS[:2]
)
_END_TO_END_TRIAGE_CASE_FUNNEL_ROWS: tuple[tuple[int, str], ...] = (
    _END_TO_END_TRIAGE_FUNNEL_ROWS[2:]
)
_END_TO_END_TRIAGE_CASE_STEP_INDICES: tuple[int, ...] = tuple(
    si for si, _ in _END_TO_END_TRIAGE_CASE_FUNNEL_ROWS
)
# All attribution buckets shown in conversion/revenue-by-source when no source filter.
_ALL_REPORT_SOURCE_VALUES: tuple[str, ...] = tuple(s.value for s in SourceEnum)
# Email temporarily excluded from conversion-by-source catalog (re-enable when ready).
_CONVERSION_BY_SOURCE_CATALOG_VALUES: tuple[str, ...] = tuple(
    s.value for s in SourceEnum if s != SourceEnum.EMAIL
)
_INITIAL_PAYMENT_REVENUE = 50
_SITE_VISIT_EVENT_CODE = "site_visit"
_SESSIONS_RESPONSE_LABEL = "sessions"
# Stored codes stay prefixed (triage vs resolve). API rows use the short names.
_PUBLIC_FUNNEL_EVENT_LABELS: dict[str, str] = {
    _SITE_VISIT_EVENT_CODE: _SESSIONS_RESPONSE_LABEL,
    "high_intent_book_a_free_first_call": "book_a_free_first_call",
    "high_intent_free_call_scheduled": "free_call_scheduled",
    "low_intent_book_a_free_first_call": "book_a_free_first_call",
    "low_intent_free_call_scheduled": "free_call_scheduled",
}

_SEARCH_ENGINE_HOST_SUFFIXES: frozenset[str] = frozenset(
    {
        "google.com",
        "google.co.uk",
        "google.ca",
        "google.de",
        "bing.com",
        "yahoo.com",
        "duckduckgo.com",
        "baidu.com",
        "yandex.ru",
        "yandex.com",
        "ecosia.org",
    }
)

_SOCIAL_HOST_SUFFIXES: frozenset[str] = frozenset(
    {
        "facebook.com",
        "fb.com",
        "instagram.com",
        "twitter.com",
        "x.com",
        "linkedin.com",
        "tiktok.com",
        "reddit.com",
        "youtube.com",
        "pinterest.com",
        "threads.net",
    }
)


def _normalize_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _list_days_half_open_utc(start: datetime, end: datetime) -> list[date]:
    """Calendar days overlapping the half-open UTC interval ``[start, end)``."""
    start = _normalize_utc(start)
    end = _normalize_utc(end)
    sd = start.date()
    ed = end.date()
    out: list[date] = []
    d = sd
    while d < ed:
        out.append(d)
        d += timedelta(days=1)
    # Include ``ed`` when the interval extends past midnight on that date (e.g.
    # end=2026-06-05 18:30 UTC must bucket events on 2026-06-05 morning).
    end_day_start = datetime(ed.year, ed.month, ed.day, tzinfo=timezone.utc)
    if end > end_day_start and ed >= sd:
        out.append(ed)
    return out


def _qtd_current_utc(end_exclusive: datetime) -> tuple[datetime, datetime]:
    end_exclusive = _normalize_utc(end_exclusive)
    ref = end_exclusive - timedelta(microseconds=1)
    q_start_month = (ref.month - 1) // 3 * 3 + 1
    cur_start = datetime(ref.year, q_start_month, 1, tzinfo=timezone.utc)
    return cur_start, end_exclusive


def _qtd_previous_utc(cur_start: datetime, cur_end: datetime) -> tuple[datetime, datetime]:
    length = cur_end - cur_start
    y, m = cur_start.year, cur_start.month
    if m == 1:
        py, pm = y - 1, 10
    elif m == 4:
        py, pm = y, 1
    elif m == 7:
        py, pm = y, 4
    else:
        py, pm = y, 7
    prev_start = datetime(py, pm, 1, tzinfo=timezone.utc)
    prev_end = prev_start + length
    return prev_start, prev_end


def _ytd_current_utc(end_exclusive: datetime) -> tuple[datetime, datetime]:
    end_exclusive = _normalize_utc(end_exclusive)
    ref = end_exclusive - timedelta(microseconds=1)
    cur_start = datetime(ref.year, 1, 1, tzinfo=timezone.utc)
    return cur_start, end_exclusive


def _ytd_previous_utc(cur_start: datetime, cur_end: datetime) -> tuple[datetime, datetime]:
    length = cur_end - cur_start
    prev_start = datetime(cur_start.year - 1, 1, 1, tzinfo=timezone.utc)
    prev_end = prev_start + length
    return prev_start, prev_end


def resolve_comparison_windows(
    start_date: datetime,
    end_date: datetime,
    compare: CompareFilterEnum | None,
    period: ComparePeriodEnum | None,
) -> tuple[datetime, datetime, tuple[datetime, datetime] | None]:
    """
    Return ``(current_start, current_end, previous_window | None)``.
    Previous window is half-open ``[prev_start, prev_end)`` like the current interval.
    """
    start_date = _normalize_utc(start_date)
    end_date = _normalize_utc(end_date)
    if start_date >= end_date:
        raise ValueError("start_date must be before end_date")
    if compare is None:
        return start_date, end_date, None
    if compare == CompareFilterEnum.PERIOD:
        if period is None:
            raise ValueError("period is required when compare is period")
        n = COMPARE_PERIOD_DAYS[period]
        cur_end = end_date
        cur_start = cur_end - timedelta(days=n)
        prev_end = cur_start
        prev_start = prev_end - timedelta(days=n)
        return cur_start, cur_end, (prev_start, prev_end)
    if compare == CompareFilterEnum.CUSTOM:
        delta = end_date - start_date
        prev_end = start_date
        prev_start = prev_end - delta
        return start_date, end_date, (prev_start, prev_end)
    if compare == CompareFilterEnum.QTD:
        cur_start, cur_end = _qtd_current_utc(end_date)
        prev_start, prev_end = _qtd_previous_utc(cur_start, cur_end)
        return cur_start, cur_end, (prev_start, prev_end)
    if compare == CompareFilterEnum.YTD:
        cur_start, cur_end = _ytd_current_utc(end_date)
        prev_start, prev_end = _ytd_previous_utc(cur_start, cur_end)
        return cur_start, cur_end, (prev_start, prev_end)
    raise ValueError(f"Unknown compare mode: {compare}")


# Matches ``ResolveFunnelSteps`` + ``AnalyticsEvents`` event_code values
_RESOLVE_FUNNEL_ROWS: tuple[tuple[int, str], ...] = (
    # (1, "site_visit"),  # temporarily disabled — resolve_get_started is the entry point
    (1, "resolve_get_started"),
    (2, "welcome_screen"),
    (3, "resolve_relationship_type"),
    (4, "resolve_length_of_relationship"),
    (5, "resolve_how_can_help"),
    (6, "resolve_court_proceedings"),
    (7, "resolve_first_name"),
    (8, "resolve_partner_name"),
    (9, "resolve_relationship_communication"),
    (10, "resolve_decision_making"),
    (11, "resolve_conflict"),
    (12, "resolve_current_communication"),
    (13, "resolve_financial_control"),
    (14, "resolve_affordability"),
    (15, "resolve_financial_picture"),
    (16, "resolve_warning_signs"),
    (17, "resolve_comfortable_in_same_room"),
    (18, "resolve_confidence"),
    (19, "resolve_completed"),
)

# Matches ``AlignmentCheckFunnelSteps`` + ``AnalyticsEvents`` event_code values
_ALIGNMENT_CHECK_FUNNEL_ROWS: tuple[tuple[int, str], ...] = (
    (1, "alignment_check_started"),
    # (2, "alignment_check_full_name"), #this is always prefilled so we don't need to track it
    (2, "alignment_check_partner_full_name"),
    (3, "alignment_check_gender"),
    (4, "alignment_check_relationship_type"),
    (5, "alignment_check_length_of_relationship"),
    (6, "alignment_check_help_with"),
    (7, "alignment_check_accommodation"),
    (8, "alignment_check_postcode"),
    (9, "alignment_check_partner_income"),
    (10, "alignment_check_dr_process"),
    (11, "alignment_check_solicitor_advising"),
    (12, "alignment_check_meeting_preference"),
    (13, "alignment_check_domestic_abuse"),
    (14, "alignment_check_urgency"),
    (15, "alignment_check_additional_support"),
    (16, "alignment_check_willingness_to_pay"),
    (17, "alignment_check_completed"),
)

# Matches ``HighIntentFunnelSteps`` + ``AnalyticsEvents`` event_code values
_HIGH_INTENT_FUNNEL_ROWS: tuple[tuple[int, str], ...] = (
    (1, "high_intent_book_a_free_first_call"),
    (2, "high_intent_free_call_scheduled"),
    (3, "high_intent_welcome"),
    (4, "how_can_we_help"),
    (5, "is_solicitor_advising"),
    (6, "annual_income"),
    (7, "net_asset_value"),
    (8, "outcome"),
    (9, "complete_high_intent"),
)


def _funnel_def_subquery(rows: tuple[tuple[int, str], ...], name: str = "funnel_def") -> Any:
    parts = tuple(
        select(
            literal(si).label("step_idx"),
            literal(code).label("event_code"),
        )
        for si, code in rows
    )
    return union_all(*parts).subquery(name)


def _cohort_cte(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> Any:
    base = (
        select(
            AnalyticsSession.id.label("session_id"),
            AnalyticsSession.entry_page,
            AnalyticsSession.source,
            AnalyticsSession.user_id,
        )
        .where(
            AnalyticsSession.started_at >= start_date,
            AnalyticsSession.started_at < end_date,
        )
    )
    if source is not None:
        base = base.where(AnalyticsSession.source == source.value)
    if landing_page is not None:
        base = base.where(AnalyticsSession.entry_page == landing_page)
    base_cte = base.cte("base_sessions")

    event_case = (
        select(
            base_cte.c.session_id,
            func.max(AnalyticsEvent.case_id).label("event_case_id"),
        )
        .select_from(base_cte)
        .outerjoin(
            AnalyticsEvent,
            and_(
                AnalyticsEvent.session_id == base_cte.c.session_id,
                AnalyticsEvent.case_id.isnot(null()),
                AnalyticsEvent.is_bot.is_(false()),
                AnalyticsEvent.timestamp >= start_date,
                AnalyticsEvent.timestamp < end_date,
            ),
        )
        .group_by(base_cte.c.session_id)
    ).cte("event_case_links")

    customer_case = (
        select(
            base_cte.c.session_id,
            func.max(CaseCustomer.case_id).label("customer_case_id"),
        )
        .select_from(base_cte)
        .outerjoin(Customer, Customer.user_id == base_cte.c.user_id)
        .outerjoin(CaseCustomer, CaseCustomer.customer_id == Customer.id)
        .group_by(base_cte.c.session_id)
    ).cte("customer_case_links")

    resolved_case_id = func.coalesce(
        event_case.c.event_case_id,
        customer_case.c.customer_case_id,
    )
    q = (
        select(
            base_cte.c.session_id,
            base_cte.c.entry_page,
            base_cte.c.source,
            resolved_case_id.label("case_id"),
        )
        .select_from(base_cte)
        .outerjoin(event_case, event_case.c.session_id == base_cte.c.session_id)
        .outerjoin(customer_case, customer_case.c.session_id == base_cte.c.session_id)
    )

    if status is not None:
        q = q.join(Case, Case.id == resolved_case_id).where(Case.status == status)

    return q.cte("cohort")


def _first_evt_cte(cohort: Any, start_date: datetime, end_date: datetime) -> Any:
    return (
        select(
            AnalyticsEvent.session_id,
            AnalyticsEvent.event_code,
            func.min(AnalyticsEvent.timestamp).label("first_ts"),
        )
        .select_from(AnalyticsEvent)
        .join(cohort, cohort.c.session_id == AnalyticsEvent.session_id)
        .where(
            AnalyticsEvent.is_bot.is_(false()),
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp < end_date,
        )
        .group_by(AnalyticsEvent.session_id, AnalyticsEvent.event_code)
    ).cte("first_evt")


def _session_times_cte(
    cohort: Any,
    funnel_def: Any,
    first_evt: Any,
    num_steps: int,
) -> Any:
    fd = funnel_def
    cols: list[Any] = [cohort.c.session_id]
    for i in range(1, num_steps + 1):
        cols.append(
            func.max(first_evt.c.first_ts)
            .filter(fd.c.step_idx == i)
            .label(f"t{i}")
        )
    return (
        select(*cols)
        .select_from(cohort)
        .join(fd, true())
        .outerjoin(
            first_evt,
            and_(
                first_evt.c.session_id == cohort.c.session_id,
                first_evt.c.event_code == fd.c.event_code,
            ),
        )
        .group_by(cohort.c.session_id)
    ).cte("session_times")


def _reach_cte(session_times: Any, num_steps: int) -> Any:
    st = session_times
    cols: list[Any] = [st.c.session_id]
    for k in range(1, num_steps + 1):
        tcols = [getattr(st.c, f"t{i}") for i in range(1, k + 1)]
        conds: list[Any] = [tcols[0].isnot(null())]
        for i in range(1, k):
            conds.append(tcols[i].isnot(null()))
            conds.append(tcols[i] >= tcols[i - 1])
        cols.append(and_(*conds).label(f"r{k}"))
    return select(*cols).select_from(st).cte("reach")


def _reach_cte_for_step_indices(
    times: Any,
    id_col: Any,
    step_indices: tuple[int, ...],
    *,
    cte_name: str = "reach",
) -> Any:
    """Strict reach with ``r{step_idx}`` columns for arbitrary funnel step indices."""
    cols: list[Any] = [id_col]
    for k in range(1, len(step_indices) + 1):
        prefix = step_indices[:k]
        tcols = [getattr(times.c, f"t{i}") for i in prefix]
        conds: list[Any] = [tcols[0].isnot(null())]
        for i in range(1, len(prefix)):
            conds.append(tcols[i].isnot(null()))
            conds.append(tcols[i] >= tcols[i - 1])
        cols.append(and_(*conds).label(f"r{prefix[-1]}"))
    return select(*cols).select_from(times).cte(cte_name)


def _case_times_cte(
    case_bridge: Any,
    funnel_def_case: Any,
    first_evt_case: Any,
    step_indices: tuple[int, ...],
) -> Any:
    """Pivot first case-level event times (across all sessions) onto bridged cases."""
    fd = funnel_def_case
    cols: list[Any] = [case_bridge.c.case_id]
    for step_idx in step_indices:
        cols.append(
            func.max(first_evt_case.c.first_ts)
            .filter(fd.c.step_idx == step_idx)
            .label(f"t{step_idx}")
        )
    return (
        select(*cols)
        .select_from(case_bridge)
        .join(fd, true())
        .outerjoin(
            first_evt_case,
            and_(
                first_evt_case.c.case_id == case_bridge.c.case_id,
                first_evt_case.c.event_code == fd.c.event_code,
            ),
        )
        .group_by(case_bridge.c.case_id)
    ).cte("case_times")


def _hybrid_e2e_step_counts_subquery(
    session_reach: Any,
    case_reach: Any,
    *,
    session_step_count: int = 2,
    case_step_indices: tuple[int, ...] = _END_TO_END_CASE_STEP_INDICES,
    name: str = "step_counts",
) -> Any:
    """Step counts: sessions for the pre-case steps, cases for the later steps."""
    sr = session_reach
    cr = case_reach
    parts: list[Any] = [
        select(
            literal(i).label("step_idx"),
            func.count().filter(getattr(sr.c, f"r{i}")).label("cnt"),
        )
        for i in range(1, session_step_count + 1)
    ]
    for step_idx in case_step_indices:
        parts.append(
            select(
                literal(step_idx).label("step_idx"),
                func.count().filter(getattr(cr.c, f"r{step_idx}")).label("cnt"),
            ),
        )
    return union_all(*tuple(parts)).subquery(name)


def _step_counts_subquery(reach: Any, num_steps: int) -> Any:
    r = reach
    parts = tuple(
        select(
            literal(i).label("step_idx"),
            func.count().filter(getattr(r.c, f"r{i}")).label("cnt"),
        ).select_from(r)
        for i in range(1, num_steps + 1)
    )
    return union_all(*parts).subquery("step_counts")


def _end_to_end_funnel_statement(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> Any:
    _, _, session_reach, _, _, case_reach = _end_to_end_hybrid_progress_ctes(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    funnel_def = _funnel_def_subquery(_END_TO_END_FUNNEL_ROWS)
    step_counts = _hybrid_e2e_step_counts_subquery(session_reach, case_reach)

    base = (
        select(step_counts.c.cnt.label("step1_cnt"))
        .where(step_counts.c.step_idx == 1)
        .cte("base")
    )

    fr = funnel_def
    sc = step_counts
    funnel_rows = (
        select(
            fr.c.step_idx,
            fr.c.event_code,
            sc.c.cnt,
            base.c.step1_cnt,
            func.lag(sc.c.cnt).over(order_by=fr.c.step_idx).label("prev_cnt"),
        )
        .select_from(fr)
        .join(sc, sc.c.step_idx == fr.c.step_idx)
        .join(base, true())
    ).subquery("funnel_rows")

    lost = func.greatest(
        func.coalesce(funnel_rows.c.prev_cnt, 0) - funnel_rows.c.cnt,
        0,
    )
    drop_pct = cast(
        case(
            (
                or_(funnel_rows.c.prev_cnt.is_(null()), funnel_rows.c.prev_cnt == 0),
                literal(0),
            ),
            else_=func.round(
                cast(100.0 * (funnel_rows.c.prev_cnt - funnel_rows.c.cnt), Numeric)
                / cast(funnel_rows.c.prev_cnt, Numeric),
                0,
            ),
        ),
        Integer,
    )
    dropoff = func.jsonb_build_object(
        "lost_count",
        lost,
        "drop_off_pct",
        drop_pct,
    )

    return (
        select(
            funnel_rows.c.step_idx.label("step_index"),
            funnel_rows.c.event_code.label("event_type"),
            funnel_rows.c.cnt.label("total_count"),
            func.round(
                100.0
                * cast(funnel_rows.c.cnt, Numeric)
                / func.nullif(cast(funnel_rows.c.step1_cnt, Numeric), 0),
                2,
            ).label("pct_of_visit"),
            case(
                (funnel_rows.c.step_idx == 1, null()),
                else_=dropoff,
            ).label("dropoff"),
        )
        .select_from(funnel_rows)
        .order_by(funnel_rows.c.step_idx)
    )


def _end_to_end_triage_funnel_statement(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> Any:
    _, _, session_reach, _, _, case_reach = _end_to_end_triage_hybrid_progress_ctes(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    funnel_def = _funnel_def_subquery(
        _END_TO_END_TRIAGE_FUNNEL_ROWS,
        name="e2e_triage_funnel_def",
    )
    step_counts = _hybrid_e2e_step_counts_subquery(
        session_reach,
        case_reach,
        session_step_count=len(_END_TO_END_TRIAGE_SESSION_FUNNEL_ROWS),
        case_step_indices=_END_TO_END_TRIAGE_CASE_STEP_INDICES,
        name="triage_step_counts",
    )

    base = (
        select(step_counts.c.cnt.label("step1_cnt"))
        .where(step_counts.c.step_idx == 1)
        .cte("triage_base")
    )

    fr = funnel_def
    sc = step_counts
    funnel_rows = (
        select(
            fr.c.step_idx,
            fr.c.event_code,
            sc.c.cnt,
            base.c.step1_cnt,
            func.lag(sc.c.cnt).over(order_by=fr.c.step_idx).label("prev_cnt"),
        )
        .select_from(fr)
        .join(sc, sc.c.step_idx == fr.c.step_idx)
        .join(base, true())
    ).subquery("triage_funnel_rows")

    lost = func.greatest(
        func.coalesce(funnel_rows.c.prev_cnt, 0) - funnel_rows.c.cnt,
        0,
    )
    drop_pct = cast(
        case(
            (
                or_(funnel_rows.c.prev_cnt.is_(null()), funnel_rows.c.prev_cnt == 0),
                literal(0),
            ),
            else_=func.round(
                cast(100.0 * (funnel_rows.c.prev_cnt - funnel_rows.c.cnt), Numeric)
                / cast(funnel_rows.c.prev_cnt, Numeric),
                0,
            ),
        ),
        Integer,
    )
    dropoff = func.jsonb_build_object(
        "lost_count",
        lost,
        "drop_off_pct",
        drop_pct,
    )

    return (
        select(
            funnel_rows.c.step_idx.label("step_index"),
            funnel_rows.c.event_code.label("event_type"),
            funnel_rows.c.cnt.label("total_count"),
            func.round(
                100.0
                * cast(funnel_rows.c.cnt, Numeric)
                / func.nullif(cast(funnel_rows.c.step1_cnt, Numeric), 0),
                2,
            ).label("pct_of_visit"),
            case(
                (funnel_rows.c.step_idx == 1, null()),
                else_=dropoff,
            ).label("dropoff"),
        )
        .select_from(funnel_rows)
        .order_by(funnel_rows.c.step_idx)
    )


def _session_strict_funnel_pct_drop_statement(
    funnel_steps: tuple[tuple[int, str], ...],
    *,
    funnel_def_cte_name: str,
    funnel_rows_subq_name: str,
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> Any:
    """Session-scoped strict funnel with step-to-step drop % (NULL for first step)."""
    num_steps = len(funnel_steps)
    cohort = _cohort_cte(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    funnel_def = _funnel_def_subquery(funnel_steps, name=funnel_def_cte_name)
    first_evt = _first_evt_cte(cohort, start_date, end_date)
    session_times = _session_times_cte(cohort, funnel_def, first_evt, num_steps)
    reach = _reach_cte(session_times, num_steps)
    step_counts = _step_counts_subquery(reach, num_steps)

    fr = funnel_def
    sc = step_counts
    funnel_rows = (
        select(
            fr.c.step_idx,
            fr.c.event_code,
            sc.c.cnt,
            func.lag(sc.c.cnt).over(order_by=fr.c.step_idx).label("prev_cnt"),
        )
        .select_from(fr)
        .join(sc, sc.c.step_idx == fr.c.step_idx)
    ).subquery(funnel_rows_subq_name)

    pct_drop = cast(
        case(
            (funnel_rows.c.step_idx == 1, null()),
            (
                or_(funnel_rows.c.prev_cnt.is_(null()), funnel_rows.c.prev_cnt == 0),
                literal(0),
            ),
            else_=func.round(
                cast(100.0 * (funnel_rows.c.prev_cnt - funnel_rows.c.cnt), Numeric)
                / cast(funnel_rows.c.prev_cnt, Numeric),
                0,
            ),
        ),
        Integer,
    )

    return (
        select(
            funnel_rows.c.step_idx.label("step_index"),
            funnel_rows.c.event_code.label("event_type"),
            funnel_rows.c.cnt.label("total_count"),
            pct_drop.label("pct_drop"),
        )
        .select_from(funnel_rows)
        .order_by(funnel_rows.c.step_idx)
    )


def _resolve_funnel_statement(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> Any:
    """Resolve journey: step-to-step drop % (NULL for first step)."""
    return _session_strict_funnel_pct_drop_statement(
        _RESOLVE_FUNNEL_ROWS,
        funnel_def_cte_name="resolve_funnel_def",
        funnel_rows_subq_name="resolve_funnel_rows",
        start_date=start_date,
        end_date=end_date,
        source=source,
        landing_page=landing_page,
        status=status,
    )


def _alignment_check_funnel_statement(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> Any:
    """
    Alignment check journey, strict per ``case_id``.

    A case enters when a cohort session recorded one of these events for it.
    Later steps count only when each event's first time is at or after the
    previous step. Two cases completed in one session count as two.
    """
    cohort = _cohort_cte(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    step_indices = tuple(si for si, _ in _ALIGNMENT_CHECK_FUNNEL_ROWS)
    event_codes = tuple(code for _, code in _ALIGNMENT_CHECK_FUNNEL_ROWS)
    in_window = (
        AnalyticsEvent.is_bot.is_(false()),
        AnalyticsEvent.event_code.in_(event_codes),
        AnalyticsEvent.timestamp >= start_date,
        AnalyticsEvent.timestamp < end_date,
    )
    case_bridge = (
        select(AnalyticsEvent.case_id.label("case_id"))
        .select_from(AnalyticsEvent)
        .join(cohort, cohort.c.session_id == AnalyticsEvent.session_id)
        .where(
            *in_window,
            AnalyticsEvent.case_id.isnot(null()),
        )
        .group_by(AnalyticsEvent.case_id)
    ).cte("alignment_check_cases")
    first_evt_case = (
        select(
            AnalyticsEvent.case_id.label("case_id"),
            AnalyticsEvent.event_code.label("event_code"),
            func.min(AnalyticsEvent.timestamp).label("first_ts"),
        )
        .select_from(AnalyticsEvent)
        .join(case_bridge, case_bridge.c.case_id == AnalyticsEvent.case_id)
        .where(*in_window)
        .group_by(AnalyticsEvent.case_id, AnalyticsEvent.event_code)
    ).cte("alignment_check_first_evt")
    funnel_def = _funnel_def_subquery(
        _ALIGNMENT_CHECK_FUNNEL_ROWS,
        name="alignment_check_funnel_def",
    )
    case_times = _case_times_cte(
        case_bridge,
        funnel_def,
        first_evt_case,
        step_indices,
    )
    case_reach = _reach_cte_for_step_indices(
        case_times,
        case_times.c.case_id,
        step_indices,
        cte_name="alignment_check_reach",
    )
    step_counts = union_all(
        *(
            select(
                literal(step_idx).label("step_idx"),
                func.count()
                .filter(getattr(case_reach.c, f"r{step_idx}"))
                .label("cnt"),
            ).select_from(case_reach)
            for step_idx in step_indices
        )
    ).subquery("alignment_check_step_counts")

    fr = funnel_def
    sc = step_counts
    funnel_rows = (
        select(
            fr.c.step_idx,
            fr.c.event_code,
            sc.c.cnt,
            func.lag(sc.c.cnt).over(order_by=fr.c.step_idx).label("prev_cnt"),
        )
        .select_from(fr)
        .join(sc, sc.c.step_idx == fr.c.step_idx)
    ).subquery("alignment_check_funnel_rows")
    pct_drop = cast(
        case(
            (funnel_rows.c.step_idx == 1, null()),
            (
                or_(funnel_rows.c.prev_cnt.is_(null()), funnel_rows.c.prev_cnt == 0),
                literal(0),
            ),
            else_=func.round(
                cast(100.0 * (funnel_rows.c.prev_cnt - funnel_rows.c.cnt), Numeric)
                / cast(funnel_rows.c.prev_cnt, Numeric),
                0,
            ),
        ),
        Integer,
    )
    return (
        select(
            funnel_rows.c.step_idx.label("step_index"),
            funnel_rows.c.event_code.label("event_type"),
            funnel_rows.c.cnt.label("total_count"),
            pct_drop.label("pct_drop"),
        )
        .select_from(funnel_rows)
        .order_by(funnel_rows.c.step_idx)
    )


def _high_intent_funnel_statement(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> Any:
    """High intent journey: step-to-step drop % (NULL for first step)."""
    return _session_strict_funnel_pct_drop_statement(
        _HIGH_INTENT_FUNNEL_ROWS,
        funnel_def_cte_name="high_intent_funnel_def",
        funnel_rows_subq_name="high_intent_funnel_rows",
        start_date=start_date,
        end_date=end_date,
        source=source,
        landing_page=landing_page,
        status=status,
    )


def _execute_end_to_end(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> list[dict[str, Any]]:
    stmt = _end_to_end_funnel_statement(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    with SessionLocal() as session:
        return [dict(row) for row in session.execute(stmt).mappings().all()]


def _execute_end_to_end_triage(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> list[dict[str, Any]]:
    stmt = _end_to_end_triage_funnel_statement(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    with SessionLocal() as session:
        return [dict(row) for row in session.execute(stmt).mappings().all()]


def _execute_resolve(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> list[dict[str, Any]]:
    stmt = _resolve_funnel_statement(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    with SessionLocal() as session:
        return [dict(row) for row in session.execute(stmt).mappings().all()]


def _execute_alignment_check(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> list[dict[str, Any]]:
    stmt = _alignment_check_funnel_statement(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    with SessionLocal() as session:
        return [dict(row) for row in session.execute(stmt).mappings().all()]


def _execute_high_intent(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> list[dict[str, Any]]:
    stmt = _high_intent_funnel_statement(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    with SessionLocal() as session:
        return [dict(row) for row in session.execute(stmt).mappings().all()]


def _end_to_end_hybrid_progress_ctes(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> tuple[Any, Any, Any, Any, Any, Any]:
    """
    Hybrid end-to-end progression.

    Steps 1–2 (``site_visit``, ``resolve_completed``): strict funnel per session.
    ``resolve_completed`` must follow ``site_visit``. From ``case_opened`` onward:
    strict funnel per ``case_id`` (all events for the case, any session), entered
    only when that session reached ``resolve_completed`` and recorded a
    ``case_opened`` tagged ``funnel=resolve``. A triage case opened in the same
    session is not counted. ``book_a_free_first_call`` is skipped for now.
    """
    cohort = _cohort_cte(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    num_session_steps = len(_END_TO_END_SESSION_FUNNEL_ROWS)
    funnel_def_sess = _funnel_def_subquery(
        _END_TO_END_SESSION_FUNNEL_ROWS,
        name="e2e_session_funnel_def",
    )
    first_evt_sess = _first_evt_cte(cohort, start_date, end_date)
    session_times = _session_times_cte(
        cohort,
        funnel_def_sess,
        first_evt_sess,
        num_session_steps,
    )
    session_reach = _reach_cte(session_times, num_session_steps)

    session_case_opened = (
        select(
            cohort.c.session_id.label("session_id"),
            AnalyticsEvent.case_id.label("case_id"),
            func.min(AnalyticsEvent.timestamp).label("case_opened_ts"),
        )
        .select_from(AnalyticsEvent)
        .join(cohort, cohort.c.session_id == AnalyticsEvent.session_id)
        .where(
            AnalyticsEvent.event_code == AnalyticsEvents.CASE_OPENED.value,
            AnalyticsEvent.case_id.isnot(null()),
            AnalyticsEvent.is_bot.is_(false()),
            AnalyticsEvent.properties["event_data"]["funnel"].astext
            == _RESOLVE_CASE_OPENED_FUNNEL,
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp < end_date,
        )
        .group_by(cohort.c.session_id, AnalyticsEvent.case_id)
    ).cte("session_case_opened")

    bridge_candidates = (
        select(
            session_case_opened.c.case_id.label("case_id"),
            cohort.c.source.label("source"),
            session_case_opened.c.session_id.label("bridge_session_id"),
            session_case_opened.c.case_opened_ts.label("case_opened_ts"),
            func.row_number()
            .over(
                partition_by=session_case_opened.c.case_id,
                order_by=session_case_opened.c.case_opened_ts,
            )
            .label("rn"),
        )
        .select_from(session_case_opened)
        .join(
            session_reach,
            session_reach.c.session_id == session_case_opened.c.session_id,
        )
        .join(cohort, cohort.c.session_id == session_case_opened.c.session_id)
        .where(session_reach.c.r2)
    ).subquery("bridge_candidates")

    case_bridge = (
        select(
            bridge_candidates.c.case_id,
            bridge_candidates.c.source,
            bridge_candidates.c.bridge_session_id,
        )
        .where(bridge_candidates.c.rn == 1)
    ).cte("case_bridge")

    case_event_codes = tuple(code for _, code in _END_TO_END_CASE_FUNNEL_ROWS)
    first_evt_case = (
        select(
            AnalyticsEvent.case_id.label("case_id"),
            AnalyticsEvent.event_code.label("event_code"),
            func.min(AnalyticsEvent.timestamp).label("first_ts"),
        )
        .select_from(AnalyticsEvent)
        .join(case_bridge, case_bridge.c.case_id == AnalyticsEvent.case_id)
        .where(
            AnalyticsEvent.is_bot.is_(false()),
            AnalyticsEvent.event_code.in_(case_event_codes),
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp < end_date,
        )
        .group_by(AnalyticsEvent.case_id, AnalyticsEvent.event_code)
    ).cte("first_evt_case")

    funnel_def_case = _funnel_def_subquery(
        _END_TO_END_CASE_FUNNEL_ROWS,
        name="e2e_case_funnel_def",
    )
    case_times = _case_times_cte(
        case_bridge,
        funnel_def_case,
        first_evt_case,
        _END_TO_END_CASE_STEP_INDICES,
    )
    case_reach = _reach_cte_for_step_indices(
        case_times,
        case_times.c.case_id,
        _END_TO_END_CASE_STEP_INDICES,
        cte_name="case_reach",
    )
    return cohort, session_times, session_reach, case_bridge, case_times, case_reach


def _general_hybrid_progress_ctes(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> tuple[Any, Any, Any, Any, Any, Any]:
    """
    General progression for conversion, active/stalled, and stage timing.

    Step 1 (``site_visit``): per session. Later steps: strict funnel per
    ``case_id``, entered when a cohort session has ``site_visit`` and then
    records ``case_opened``. Resolve and high-intent events are not required.
    """
    cohort = _cohort_cte(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    num_session_steps = len(_GENERAL_SESSION_FUNNEL_ROWS)
    funnel_def_sess = _funnel_def_subquery(
        _GENERAL_SESSION_FUNNEL_ROWS,
        name="general_session_funnel_def",
    )
    first_evt_sess = _first_evt_cte(cohort, start_date, end_date)
    session_times = _session_times_cte(
        cohort,
        funnel_def_sess,
        first_evt_sess,
        num_session_steps,
    )
    session_reach = _reach_cte(session_times, num_session_steps)

    session_case_opened = (
        select(
            cohort.c.session_id.label("session_id"),
            AnalyticsEvent.case_id.label("case_id"),
            func.min(AnalyticsEvent.timestamp).label("case_opened_ts"),
        )
        .select_from(AnalyticsEvent)
        .join(cohort, cohort.c.session_id == AnalyticsEvent.session_id)
        .where(
            AnalyticsEvent.event_code == AnalyticsEvents.CASE_OPENED.value,
            AnalyticsEvent.case_id.isnot(null()),
            AnalyticsEvent.is_bot.is_(false()),
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp < end_date,
        )
        .group_by(cohort.c.session_id, AnalyticsEvent.case_id)
    ).cte("general_session_case_opened")

    bridge_candidates = (
        select(
            session_case_opened.c.case_id.label("case_id"),
            cohort.c.source.label("source"),
            session_case_opened.c.session_id.label("bridge_session_id"),
            session_case_opened.c.case_opened_ts.label("case_opened_ts"),
            func.row_number()
            .over(
                partition_by=session_case_opened.c.case_id,
                order_by=session_case_opened.c.case_opened_ts,
            )
            .label("rn"),
        )
        .select_from(session_case_opened)
        .join(
            session_reach,
            session_reach.c.session_id == session_case_opened.c.session_id,
        )
        .join(
            session_times,
            session_times.c.session_id == session_case_opened.c.session_id,
        )
        .join(cohort, cohort.c.session_id == session_case_opened.c.session_id)
        .where(
            session_reach.c.r1,
            session_case_opened.c.case_opened_ts >= session_times.c.t1,
        )
    ).subquery("general_bridge_candidates")

    case_bridge = (
        select(
            bridge_candidates.c.case_id,
            bridge_candidates.c.source,
            bridge_candidates.c.bridge_session_id,
        )
        .where(bridge_candidates.c.rn == 1)
    ).cte("general_case_bridge")

    case_event_codes = tuple(code for _, code in _GENERAL_CASE_FUNNEL_ROWS)
    first_evt_case = (
        select(
            AnalyticsEvent.case_id.label("case_id"),
            AnalyticsEvent.event_code.label("event_code"),
            func.min(AnalyticsEvent.timestamp).label("first_ts"),
        )
        .select_from(AnalyticsEvent)
        .join(case_bridge, case_bridge.c.case_id == AnalyticsEvent.case_id)
        .where(
            AnalyticsEvent.is_bot.is_(false()),
            AnalyticsEvent.event_code.in_(case_event_codes),
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp < end_date,
        )
        .group_by(AnalyticsEvent.case_id, AnalyticsEvent.event_code)
    ).cte("general_first_evt_case")

    funnel_def_case = _funnel_def_subquery(
        _GENERAL_CASE_FUNNEL_ROWS,
        name="general_case_funnel_def",
    )
    case_times = _case_times_cte(
        case_bridge,
        funnel_def_case,
        first_evt_case,
        _GENERAL_CASE_STEP_INDICES,
    )
    case_reach = _reach_cte_for_step_indices(
        case_times,
        case_times.c.case_id,
        _GENERAL_CASE_STEP_INDICES,
        cte_name="general_case_reach",
    )
    return cohort, session_times, session_reach, case_bridge, case_times, case_reach


def _end_to_end_triage_hybrid_progress_ctes(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> tuple[Any, Any, Any, Any, Any, Any]:
    """
    Hybrid end-to-end triage progression.

    Steps 1–2 (``site_visit``, ``free_call_scheduled``): strict funnel per session.
    ``book_a_free_first_call`` is skipped for now. Later steps: strict funnel per
    ``case_id``, entered only when a cohort session completed step 2 and recorded
    a ``case_opened`` tagged ``funnel=triage``. A resolve case opened in the same
    session is not counted.
    """
    cohort = _cohort_cte(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    num_session_steps = len(_END_TO_END_TRIAGE_SESSION_FUNNEL_ROWS)
    funnel_def_sess = _funnel_def_subquery(
        _END_TO_END_TRIAGE_SESSION_FUNNEL_ROWS,
        name="e2e_triage_session_funnel_def",
    )
    first_evt_sess = _first_evt_cte(cohort, start_date, end_date)
    session_times = _session_times_cte(
        cohort,
        funnel_def_sess,
        first_evt_sess,
        num_session_steps,
    )
    session_reach = _reach_cte(session_times, num_session_steps)

    session_case_opened = (
        select(
            cohort.c.session_id.label("session_id"),
            AnalyticsEvent.case_id.label("case_id"),
            func.min(AnalyticsEvent.timestamp).label("case_opened_ts"),
        )
        .select_from(AnalyticsEvent)
        .join(cohort, cohort.c.session_id == AnalyticsEvent.session_id)
        .where(
            AnalyticsEvent.event_code == AnalyticsEvents.CASE_OPENED.value,
            AnalyticsEvent.case_id.isnot(null()),
            AnalyticsEvent.is_bot.is_(false()),
            AnalyticsEvent.properties["event_data"]["funnel"].astext
            == _TRIAGE_CASE_OPENED_FUNNEL,
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp < end_date,
        )
        .group_by(cohort.c.session_id, AnalyticsEvent.case_id)
    ).cte("triage_session_case_opened")

    bridge_candidates = (
        select(
            session_case_opened.c.case_id.label("case_id"),
            cohort.c.source.label("source"),
            session_case_opened.c.session_id.label("bridge_session_id"),
            session_case_opened.c.case_opened_ts.label("case_opened_ts"),
            func.row_number()
            .over(
                partition_by=session_case_opened.c.case_id,
                order_by=session_case_opened.c.case_opened_ts,
            )
            .label("rn"),
        )
        .select_from(session_case_opened)
        .join(
            session_reach,
            session_reach.c.session_id == session_case_opened.c.session_id,
        )
        .join(cohort, cohort.c.session_id == session_case_opened.c.session_id)
        .where(session_reach.c.r2)
    ).subquery("triage_bridge_candidates")

    case_bridge = (
        select(
            bridge_candidates.c.case_id,
            bridge_candidates.c.source,
            bridge_candidates.c.bridge_session_id,
        )
        .where(bridge_candidates.c.rn == 1)
    ).cte("triage_case_bridge")

    case_event_codes = tuple(code for _, code in _END_TO_END_TRIAGE_CASE_FUNNEL_ROWS)
    first_evt_case = (
        select(
            AnalyticsEvent.case_id.label("case_id"),
            AnalyticsEvent.event_code.label("event_code"),
            func.min(AnalyticsEvent.timestamp).label("first_ts"),
        )
        .select_from(AnalyticsEvent)
        .join(case_bridge, case_bridge.c.case_id == AnalyticsEvent.case_id)
        .where(
            AnalyticsEvent.is_bot.is_(false()),
            AnalyticsEvent.event_code.in_(case_event_codes),
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp < end_date,
        )
        .group_by(AnalyticsEvent.case_id, AnalyticsEvent.event_code)
    ).cte("triage_first_evt_case")

    funnel_def_case = _funnel_def_subquery(
        _END_TO_END_TRIAGE_CASE_FUNNEL_ROWS,
        name="e2e_triage_case_funnel_def",
    )
    case_times = _case_times_cte(
        case_bridge,
        funnel_def_case,
        first_evt_case,
        _END_TO_END_TRIAGE_CASE_STEP_INDICES,
    )
    case_reach = _reach_cte_for_step_indices(
        case_times,
        case_times.c.case_id,
        _END_TO_END_TRIAGE_CASE_STEP_INDICES,
        cte_name="triage_case_reach",
    )
    return cohort, session_times, session_reach, case_bridge, case_times, case_reach


def _conversion_by_source_statement(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> Any:
    """Per attribution ``source`` counts at each general funnel step.

    A case is counted after ``site_visit`` then ``case_opened``. Resolve and
    high-intent steps are not required.
    """
    cohort, _, session_reach, case_bridge, _, case_reach = _general_hybrid_progress_ctes(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    src_expr = func.coalesce(cohort.c.source, "(unknown)")
    sess_agg = (
        select(
            src_expr.label("source"),
            func.sum(cast(session_reach.c.r1, Integer)).label("n1"),
        )
        .select_from(session_reach)
        .join(cohort, cohort.c.session_id == session_reach.c.session_id)
        .group_by(src_expr)
    ).subquery("sess_by_source")

    case_src_expr = func.coalesce(case_bridge.c.source, "(unknown)")
    case_cols: list[Any] = [case_src_expr.label("source")]
    for step_idx in _GENERAL_CASE_STEP_INDICES:
        case_cols.append(
            func.sum(cast(getattr(case_reach.c, f"r{step_idx}"), Integer)).label(
                f"n{step_idx}"
            ),
        )
    case_agg = (
        select(*case_cols)
        .select_from(case_reach)
        .join(case_bridge, case_bridge.c.case_id == case_reach.c.case_id)
        .group_by(case_src_expr)
    ).subquery("case_by_source")

    out_src = func.coalesce(sess_agg.c.source, case_agg.c.source, "(unknown)")
    agg_cols: list[Any] = [out_src.label("source")]
    agg_cols.append(func.coalesce(sess_agg.c.n1, 0).label("n1"))
    for step_idx in _GENERAL_CASE_STEP_INDICES:
        agg_cols.append(
            func.coalesce(getattr(case_agg.c, f"n{step_idx}"), 0).label(f"n{step_idx}"),
        )
    return (
        select(*agg_cols)
        .select_from(
            sess_agg.join(
                case_agg,
                sess_agg.c.source == case_agg.c.source,
                isouter=True,
                full=True,
            ),
        )
        .order_by(out_src)
    )


def _empty_conversion_by_source_row(source: str) -> dict[str, Any]:
    """Zeroed conversion row for a single attribution source."""
    item: dict[str, Any] = {"source": source}
    for _, code in _GENERAL_FUNNEL_ROWS:
        item[code] = {"count": 0, "pct_of_conversion": 0.0}
    return item


def _materialize_conversion_by_source(
    raw_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Attach ``pct_of_conversion`` vs that row's ``site_visit`` (n1) count."""
    out: list[dict[str, Any]] = []
    for row in raw_rows:
        base = int(row.get("n1") or 0)
        item: dict[str, Any] = {"source": row["source"]}
        for step_idx, code in _GENERAL_FUNNEL_ROWS:
            cnt = int(row.get(f"n{step_idx}") or 0)
            item[code] = {
                "count": cnt,
                "pct_of_conversion": _pct_rate(cnt, base),
            }
        out.append(item)
    return out


def _fill_source_catalog_rows(
    rows: list[dict[str, Any]],
    *,
    source_filter: SourceEnum | None,
    empty_row: Callable[[str], dict[str, Any]],
    catalog_values: tuple[str, ...] | None = None,
) -> list[dict[str, Any]]:
    """
    When no ``source`` filter is applied, ensure every ``SourceEnum`` value appears.

    Rows for sources with no data use ``empty_row(source)``. Non-enum keys from the
    DB (e.g. ``(unknown)``) are appended after the catalog in sorted order.
    """
    if source_filter is not None:
        return rows
    catalog = catalog_values if catalog_values is not None else _ALL_REPORT_SOURCE_VALUES
    by_source = {str(r["source"]): r for r in rows}
    out: list[dict[str, Any]] = []
    for src in catalog:
        out.append(by_source.pop(src, None) or empty_row(src))
    for src in sorted(by_source):
        out.append(by_source[src])
    return out


def _append_conversion_by_source_total_row(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Append a ``Total`` row with column-wise sums of each funnel step count."""
    if not rows:
        return rows
    step_event_codes = [code for _, code in _GENERAL_FUNNEL_ROWS]
    totals = {
        code: sum(int(row[code]["count"]) for row in rows)
        for code in step_event_codes
    }
    base = totals["site_visit"]
    total_row: dict[str, Any] = {"source": "Total"}
    for code in step_event_codes:
        cnt = totals[code]
        total_row[code] = {
            "count": cnt,
            "pct_of_conversion": _pct_rate(cnt, base),
        }
    return [*rows, total_row]


def _fill_conversion_by_source_catalog(
    rows: list[dict[str, Any]],
    *,
    source_filter: SourceEnum | None,
) -> list[dict[str, Any]]:
    # Email source row temporarily disabled — drop any email attribution from results.
    rows = [r for r in rows if str(r["source"]) != SourceEnum.EMAIL.value]
    filled = _fill_source_catalog_rows(
        rows,
        source_filter=source_filter,
        empty_row=_empty_conversion_by_source_row,
        catalog_values=_CONVERSION_BY_SOURCE_CATALOG_VALUES,
    )
    return _append_conversion_by_source_total_row(filled)


def _execute_conversion_by_source(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> list[dict[str, Any]]:
    stmt = _conversion_by_source_statement(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    with SessionLocal() as session:
        raw = [dict(row) for row in session.execute(stmt).mappings().all()]
    materialized = _materialize_conversion_by_source(raw)
    return _fill_conversion_by_source_catalog(materialized, source_filter=source)


def _active_stalled_statement(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    stalled_after: datetime,
    status: CaseStatusEnum | None = None,
) -> Any:
    """
    Per-stage active/stalled counts from the general funnel.

    ``site_visit`` counts sessions that have not opened a case. Later steps count
    cases only. Once a session recorded ``case_opened``, it is removed from
    session-level counts so the case's current stage is the single source of truth.

    Active = at that stage and entered within five days (or on the terminal step).
    Stalled = at that non-terminal stage and entered more than five days ago.
    """
    num_steps = _GENERAL_FUNNEL_ROWS[-1][0]
    _, session_times, session_reach, case_bridge, case_times, case_reach = (
        _general_hybrid_progress_ctes(
            start_date,
            end_date,
            source,
            landing_page,
            status,
        )
    )
    bridged_session_ids = select(case_bridge.c.bridge_session_id)

    sess_stage_idx = case(
        (session_reach.c.r1, literal(1)),
        else_=null(),
    )
    sess_entered_at = case(
        (session_reach.c.r1, session_times.c.t1),
        else_=null(),
    )
    session_current = (
        select(
            cast(session_reach.c.session_id, String).label("entity_id"),
            sess_stage_idx.label("stage_idx"),
            sess_entered_at.label("entered_at"),
        )
        .select_from(session_reach)
        .join(
            session_times,
            session_times.c.session_id == session_reach.c.session_id,
        )
        .where(sess_stage_idx.isnot(null()))
        .where(session_reach.c.session_id.not_in(bridged_session_ids))
    )

    case_stage_cases: list[Any] = []
    case_entered_cases: list[Any] = []
    for step_idx in reversed(_GENERAL_CASE_STEP_INDICES):
        case_stage_cases.append((getattr(case_reach.c, f"r{step_idx}"), literal(step_idx)))
        case_entered_cases.append(
            (getattr(case_reach.c, f"r{step_idx}"), getattr(case_times.c, f"t{step_idx}")),
        )
    case_stage_idx = case(*case_stage_cases, else_=null())
    case_entered_at = case(*case_entered_cases, else_=null())
    case_current = (
        select(
            cast(case_reach.c.case_id, String).label("entity_id"),
            case_stage_idx.label("stage_idx"),
            case_entered_at.label("entered_at"),
        )
        .select_from(case_reach)
        .join(case_times, case_times.c.case_id == case_reach.c.case_id)
        .where(case_stage_idx.isnot(null()))
    )

    current_stage = union_all(session_current, case_current).subquery("current_stage")

    funnel_def = _funnel_def_subquery(
        _GENERAL_FUNNEL_ROWS,
        name="active_stalled_funnel_def",
    )
    cs = current_stage
    is_active = or_(
        cs.c.stage_idx == num_steps,
        cs.c.entered_at >= stalled_after,
    )
    is_stalled = and_(
        cs.c.stage_idx < num_steps,
        cs.c.entered_at < stalled_after,
    )
    return (
        select(
            funnel_def.c.step_idx.label("step_index"),
            funnel_def.c.event_code.label("event_type"),
            func.count(cs.c.entity_id).filter(is_active).label("active_count"),
            func.count(cs.c.entity_id).filter(is_stalled).label("stalled_count"),
        )
        .select_from(funnel_def)
        .outerjoin(cs, cs.c.stage_idx == funnel_def.c.step_idx)
        .group_by(funnel_def.c.step_idx, funnel_def.c.event_code)
        .order_by(funnel_def.c.step_idx)
    )


def _execute_active_stalled(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> list[dict[str, Any]]:
    stalled_after = datetime.now(timezone.utc) - timedelta(days=5)
    stmt = _active_stalled_statement(
        start_date,
        end_date,
        source,
        landing_page,
        stalled_after,
        status,
    )
    with SessionLocal() as session:
        return [dict(row) for row in session.execute(stmt).mappings().all()]


def _average_time_between_stages_statement(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> Any:
    """Average days between general funnel steps (session then case timelines).

    ``site_visit`` is omitted — there is no prior stage to measure from.
    ``case_opened`` is measured from the bridge session's ``site_visit``.
    """
    _, session_times, _, case_bridge, case_times, case_reach = (
        _general_hybrid_progress_ctes(
            start_date,
            end_date,
            source,
            landing_page,
            status,
        )
    )
    st = session_times
    ct = case_times
    cr = case_reach
    parts: list[Any] = []
    for i, code in _GENERAL_FUNNEL_ROWS:
        if i == 1:
            continue
        if i == 2:
            days_expr = func.extract("epoch", ct.c.t2 - st.c.t1) / 86400.0
            parts.append(
                select(
                    literal(i).label("step_index"),
                    literal(code).label("event_type"),
                    func.avg(days_expr).filter(cr.c.r2).label("avg_days"),
                )
                .select_from(ct)
                .join(cr, cr.c.case_id == ct.c.case_id)
                .join(
                    case_bridge,
                    case_bridge.c.case_id == ct.c.case_id,
                )
                .join(
                    st,
                    st.c.session_id == case_bridge.c.bridge_session_id,
                ),
            )
            continue
        ti = getattr(ct.c, f"t{i}")
        tprev = getattr(ct.c, f"t{i - 1}")
        ri = getattr(cr.c, f"r{i}")
        days_expr = func.extract("epoch", ti - tprev) / 86400.0
        parts.append(
            select(
                literal(i).label("step_index"),
                literal(code).label("event_type"),
                func.avg(days_expr).filter(ri).label("avg_days"),
            ).select_from(ct).join(cr, cr.c.case_id == ct.c.case_id),
        )
    return union_all(*tuple(parts)).subquery("avg_time_between_stages")


def _execute_average_time_between_stages(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> list[dict[str, Any]]:
    q = _average_time_between_stages_statement(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    stmt = select(
        q.c.step_index,
        q.c.event_type,
        q.c.avg_days,
    ).order_by(q.c.step_index)
    with SessionLocal() as session:
        rows = [dict(row) for row in session.execute(stmt).mappings().all()]

    out: list[dict[str, Any]] = []
    for row in rows:
        avg_days = row.get("avg_days")
        deviation_day = None if avg_days is None else f"{float(avg_days):.1f} d"
        out.append(
            {
                "step_index": int(row["step_index"]),
                "event_type": str(row["event_type"]),
                "deviation_day": deviation_day,
            },
        )
    return out


def _average_time_to_paid_statement(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> Any:
    """Average days from bridge-session ``site_visit`` to ``initial_payment_completed``.

    Only cases that strictly reached funnel step 8 (``r8``) are included.
    """
    _, session_times, _, case_bridge, case_times, case_reach = (
        _end_to_end_hybrid_progress_ctes(
            start_date,
            end_date,
            source,
            landing_page,
            status,
        )
    )
    st = session_times
    ct = case_times
    cr = case_reach
    days_expr = func.extract("epoch", ct.c.t8 - st.c.t1) / 86400.0
    return (
        select(func.avg(days_expr).filter(cr.c.r8).label("avg_days"))
        .select_from(ct)
        .join(cr, cr.c.case_id == ct.c.case_id)
        .join(case_bridge, case_bridge.c.case_id == ct.c.case_id)
        .join(st, st.c.session_id == case_bridge.c.bridge_session_id)
    )


def _execute_average_time_to_paid(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> float | None:
    stmt = _average_time_to_paid_statement(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    with SessionLocal() as session:
        avg_days = session.execute(stmt).scalar()
    if avg_days is None:
        return None
    return float(avg_days)


def _revenue_by_source_statement(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> Any:
    """Revenue by source using case-level step-8 (initial payment) completions."""
    _, _, _, case_bridge, _, case_reach = _end_to_end_hybrid_progress_ctes(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    rw = (
        select(
            case_bridge.c.source,
            case_reach.c.r8,
        )
        .select_from(case_reach)
        .join(case_bridge, case_bridge.c.case_id == case_reach.c.case_id)
    ).subquery("revenue_src")
    src_expr = func.coalesce(rw.c.source, "(unknown)")
    return (
        select(
            src_expr.label("source"),
            (
                func.sum(cast(rw.c.r8, Integer)) * _INITIAL_PAYMENT_REVENUE
            ).label("total_revenue"),
        )
        .select_from(rw)
        .group_by(src_expr)
        .order_by(src_expr)
    )


def _execute_revenue_by_source(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> list[dict[str, Any]]:
    stmt = _revenue_by_source_statement(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    with SessionLocal() as session:
        rows = [dict(row) for row in session.execute(stmt).mappings().all()]
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "source": row["source"],
                "total_revenue": int(row.get("total_revenue") or 0),
            },
        )
    return _fill_source_catalog_rows(
        out,
        source_filter=source,
        empty_row=lambda src: {"source": src, "total_revenue": 0},
    )


def _fmt_int_commas(n: int) -> str:
    return f"{n:,}"


def _pct_rate(count: int, base: int) -> float:
    """Percent rate rounded to 4 decimal places; 0.0 when base is zero."""
    if base <= 0:
        return 0.0
    return round(100.0 * count / base, 2)


def _public_funnel_event_type(event_type: str) -> str:
    """Map internal analytics event codes to API-facing funnel labels."""
    return _PUBLIC_FUNNEL_EVENT_LABELS.get(event_type, event_type)


def _map_funnel_rows_for_response(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        {
            **row,
            "event_type": _public_funnel_event_type(str(row["event_type"])),
        }
        for row in rows
    ]


def _map_conversion_by_source_for_response(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        if _SITE_VISIT_EVENT_CODE in item:
            item[_SESSIONS_RESPONSE_LABEL] = item.pop(_SITE_VISIT_EVENT_CODE)
        out.append(item)
    return out


def _case_opened_first_per_case_statement(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> Any:
    """First ``case_opened`` timestamp per ``case_id`` in the filtered cohort."""
    cohort = _cohort_cte(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    return (
        select(
            AnalyticsEvent.case_id.label("case_id"),
            func.min(AnalyticsEvent.timestamp).label("first_ts"),
        )
        .select_from(AnalyticsEvent)
        .join(cohort, cohort.c.session_id == AnalyticsEvent.session_id)
        .where(
            AnalyticsEvent.is_bot.is_(false()),
            AnalyticsEvent.event_code == AnalyticsEvents.CASE_OPENED.value,
            AnalyticsEvent.case_id.isnot(null()),
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp < end_date,
        )
        .group_by(AnalyticsEvent.case_id)
    )


def _fetch_case_opened_first_per_case(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> list[dict[str, Any]]:
    stmt = _case_opened_first_per_case_statement(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    with SessionLocal() as session:
        return [dict(row) for row in session.execute(stmt).mappings().all()]


def _case_opened_daily_series(
    rows: list[dict[str, Any]],
    days: list[date],
) -> tuple[int, list[int], list[str]]:
    """Per-day distinct ``case_opened`` counts; days with no opens are 0."""
    if not days:
        return 0, [], []
    daily: dict[date, int] = {d: 0 for d in days}
    for row in rows:
        ts = row.get("first_ts")
        if ts is None:
            continue
        dkey = _normalize_utc(ts).date()
        if dkey in daily:
            daily[dkey] += 1
    series = [daily[d] for d in days]
    date_labels = [d.isoformat() for d in days]
    return sum(series), series, date_labels


def _execute_case_opened_count(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> int:
    return len(
        _fetch_case_opened_first_per_case(
            start_date,
            end_date,
            source,
            landing_page,
            status,
        ),
    )


def _strict_case_terminal_ts(
    step_times: dict[str, datetime],
    case_steps: tuple[tuple[int, str], ...],
) -> datetime | None:
    """Timestamp of the last case step when every case step is present and in order."""
    prev: datetime | None = None
    terminal: datetime | None = None
    for _, code in case_steps:
        ts = step_times.get(code)
        if ts is None:
            return None
        if prev is not None and ts < prev:
            return None
        prev = ts
        terminal = ts
    return terminal


def _conversion_pct_and_daily_counts(
    days: list[date],
    opened_on: list[date],
    converted_on: list[date],
) -> tuple[int, list[int]]:
    """Overall conversion percent, and how many cases converted on each day."""
    if not days:
        return 0, []
    opened_daily = {d: 0 for d in days}
    converted_daily = {d: 0 for d in days}
    for d in opened_on:
        if d in opened_daily:
            opened_daily[d] += 1
    for d in converted_on:
        if d in converted_daily:
            converted_daily[d] += 1
    opened_total = sum(opened_daily.values())
    converted_total = sum(converted_daily.values())
    overall = (
        int(round(100.0 * converted_total / opened_total)) if opened_total else 0
    )
    return overall, [converted_daily[d] for d in days]


def _fetch_journey_case_step_times(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None,
    *,
    funnel_tag: str,
    case_steps: tuple[tuple[int, str], ...],
) -> list[dict[str, Any]]:
    """First in-window timestamp of each case step for journey cases.

    A case enters when ``case_opened`` is tagged with ``funnel_tag``. Later steps
    are read by ``case_id`` from any session.
    """
    cohort = _cohort_cte(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    opened = (
        select(
            AnalyticsEvent.case_id.label("case_id"),
            func.min(AnalyticsEvent.timestamp).label("opened_ts"),
        )
        .select_from(AnalyticsEvent)
        .join(cohort, cohort.c.session_id == AnalyticsEvent.session_id)
        .where(
            AnalyticsEvent.event_code == AnalyticsEvents.CASE_OPENED.value,
            AnalyticsEvent.case_id.isnot(null()),
            AnalyticsEvent.is_bot.is_(false()),
            AnalyticsEvent.properties["event_data"]["funnel"].astext == funnel_tag,
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp < end_date,
        )
        .group_by(AnalyticsEvent.case_id)
    ).cte("journey_opened_cases")

    event_codes = tuple(dict.fromkeys(code for _, code in case_steps))
    step_events = (
        select(
            AnalyticsEvent.case_id.label("case_id"),
            AnalyticsEvent.event_code.label("event_code"),
            func.min(AnalyticsEvent.timestamp).label("first_ts"),
        )
        .select_from(AnalyticsEvent)
        .join(opened, opened.c.case_id == AnalyticsEvent.case_id)
        .where(
            AnalyticsEvent.is_bot.is_(false()),
            AnalyticsEvent.event_code.in_(event_codes),
            AnalyticsEvent.timestamp >= start_date,
            AnalyticsEvent.timestamp < end_date,
        )
        .group_by(AnalyticsEvent.case_id, AnalyticsEvent.event_code)
    ).cte("journey_case_step_events")

    stmt = (
        select(
            opened.c.case_id,
            opened.c.opened_ts,
            step_events.c.event_code,
            step_events.c.first_ts,
        )
        .select_from(opened)
        .outerjoin(step_events, step_events.c.case_id == opened.c.case_id)
    )
    with SessionLocal() as session:
        return [dict(row) for row in session.execute(stmt).mappings().all()]


def _case_scope_conversion_series(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None,
    *,
    funnel_tag: str,
    case_steps: tuple[tuple[int, str], ...],
    days: list[date],
) -> tuple[int, list[int]]:
    """Conversion percent, plus the daily count of cases that reached the last step.

    Session steps are ignored. Step timestamps may come from any session on the case.
    """
    if not days:
        return 0, []
    rows = _fetch_journey_case_step_times(
        start_date,
        end_date,
        source,
        landing_page,
        status,
        funnel_tag=funnel_tag,
        case_steps=case_steps,
    )
    opened_ts: dict[Any, datetime] = {}
    step_times: dict[Any, dict[str, datetime]] = {}
    for row in rows:
        case_id = row["case_id"]
        opened_ts[case_id] = _normalize_utc(row["opened_ts"])
        code = row.get("event_code")
        first_ts = row.get("first_ts")
        if code and first_ts is not None:
            step_times.setdefault(case_id, {})[str(code)] = _normalize_utc(first_ts)
        else:
            step_times.setdefault(case_id, {})

    opened_on: list[date] = []
    converted_on: list[date] = []
    for case_id, opened in opened_ts.items():
        times = step_times.get(case_id, {})
        times["case_opened"] = opened
        opened_on.append(opened.date())
        terminal = _strict_case_terminal_ts(times, case_steps)
        if terminal is not None:
            converted_on.append(terminal.date())
    return _conversion_pct_and_daily_counts(days, opened_on, converted_on)


def _scalar_metrics(
    revenue_by_source: list[dict[str, Any]],
    active_stalled: list[dict[str, Any]],
    *,
    conversion_pct: int,
    triage_conversion_pct: int,
    avg_time_to_paid_days: float | None = None,
    case_opened: int = 0,
) -> dict[str, Any]:
    total_revenue = sum(int(r.get("total_revenue") or 0) for r in revenue_by_source)
    total_stalled = sum(int(r.get("stalled_count") or 0) for r in active_stalled)
    return {
        "case_opened": case_opened,
        "conversion_pct": conversion_pct,
        "triage_conversion_pct": triage_conversion_pct,
        "avg_time_to_paid_days": (
            float(avg_time_to_paid_days) if avg_time_to_paid_days is not None else 0.0
        ),
        "revenue_gbp": total_revenue,
        "stalled": total_stalled,
    }


def _rel_pct_change_str(curr: float, prev: float) -> str:
    if prev == 0.0:
        if curr == 0.0:
            return "0%"
        return "+100%"
    pct = (curr - prev) / prev * 100.0
    sign = "+" if pct >= 0 else ""
    return f"{sign}{pct:.1f}%"


def _trend_triple(*, higher_is_better: bool, curr: float, prev: float) -> str:
    if curr == prev:
        return "neutral"
    improved = (curr > prev) if higher_is_better else (curr < prev)
    return "positive" if improved else "negative"


def _make_change_block(
    prev_metrics: dict[str, Any],
    key: str,
    curr_val: float,
    *,
    higher_is_better: bool,
    mode: str,
    format_prev_value: Any,
) -> dict[str, Any]:
    prev_val = float(prev_metrics[key])
    if mode == "day_diff":
        d = curr_val - prev_val
        sign = "+" if d >= 0 else ""
        dt = f"{sign}{d:.1f} d"
        trend = _trend_triple(higher_is_better=False, curr=curr_val, prev=prev_val)
    elif mode == "pts":
        d = curr_val - prev_val
        sign = "+" if d >= 0 else ""
        dt = f"{sign}{d:.1f} pts"
        trend = _trend_triple(higher_is_better=higher_is_better, curr=curr_val, prev=prev_val)
    elif mode in ("pct", "currency_pct"):
        dt = _rel_pct_change_str(curr_val, prev_val)
        trend = _trend_triple(higher_is_better=higher_is_better, curr=curr_val, prev=prev_val)
    else:
        raise ValueError(mode)
    return {
        "deltaText": dt,
        "trend": trend,
        "previous_value": format_prev_value(prev_val),
    }


def _linear_int_series(n: int, final: int) -> list[int]:
    if n == 0:
        return []
    if final <= 0:
        return [0] * n
    return [max(0, int(round(final * (i + 1) / n))) for i in range(n)]


def _linear_tenths_series(n: int, final_days: float) -> list[int]:
    if n == 0:
        return []
    mx = max(0, int(round(final_days * 10)))
    if mx == 0:
        return [0] * n
    return [int(round(mx * (i + 1) / n)) for i in range(n)]


def _execute_trend_series(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> dict[str, Any]:
    """Daily trend series. Conversion cards use case steps only, not sessions."""
    start_date = _normalize_utc(start_date)
    end_date = _normalize_utc(end_date)
    days = _list_days_half_open_utc(start_date, end_date)
    if not days:
        return {
            "case_opened": [],
            "case_opened_total": 0,
            "case_opened_dates": [],
            "conversion_pct": [],
            "conversion_pct_total": 0,
            "triage_conversion_pct": [],
            "triage_conversion_pct_total": 0,
            "revenue_gbp": [],
        }

    case_opened_rows = _fetch_case_opened_first_per_case(
        start_date,
        end_date,
        source,
        landing_page,
        status,
    )
    case_opened_total, series_case, case_opened_dates = _case_opened_daily_series(
        case_opened_rows,
        days,
    )

    conversion_pct_total, series_conv = _case_scope_conversion_series(
        start_date,
        end_date,
        source,
        landing_page,
        status,
        funnel_tag=_RESOLVE_CASE_OPENED_FUNNEL,
        case_steps=_END_TO_END_CASE_FUNNEL_ROWS,
        days=days,
    )
    triage_conversion_pct_total, series_triage_conv = _case_scope_conversion_series(
        start_date,
        end_date,
        source,
        landing_page,
        status,
        funnel_tag=_TRIAGE_CASE_OPENED_FUNNEL,
        case_steps=_END_TO_END_TRIAGE_CASE_FUNNEL_ROWS,
        days=days,
    )
    # Revenue is no longer reported after the initial payment flow was removed.
    series_rev: list[int] = []
    return {
        "case_opened": series_case,
        "case_opened_total": case_opened_total,
        "case_opened_dates": case_opened_dates,
        "conversion_pct": series_conv,
        "conversion_pct_total": conversion_pct_total,
        "triage_conversion_pct": series_triage_conv,
        "triage_conversion_pct_total": triage_conversion_pct_total,
        "revenue_gbp": series_rev,
    }


def _build_general_info_cards(
    cur: dict[str, Any],
    prev: dict[str, Any] | None,
    trend_core: dict[str, Any],
) -> list[dict[str, Any]]:
    n = len(trend_core.get("case_opened", []))
    stalled_series = _linear_int_series(n, int(cur["stalled"]))
    # avg_series = _linear_tenths_series(n, float(cur["avg_time_to_paid_days"]))
    cards: list[dict[str, Any]] = []

    cards.append(
        {
            "label": "Cases Opened",
            "value": cur["case_opened"],
            "change": (
                _make_change_block(
                    prev,
                    "case_opened",
                    float(cur["case_opened"]),
                    higher_is_better=True,
                    mode="pct",
                    format_prev_value=lambda v: _fmt_int_commas(int(v)),
                )
                if prev is not None
                else None
            ),
            "trendSeries": trend_core.get("case_opened", []),
            "trendSeriesDates": trend_core.get("case_opened_dates", []),
        },
    )
    cards.append(
        {
            "label": "End-to-End Resolve Conv.",
            "value": f"{cur['conversion_pct']}%",
            "change": (
                _make_change_block(
                    prev,
                    "conversion_pct",
                    float(cur["conversion_pct"]),
                    higher_is_better=True,
                    mode="pts",
                    format_prev_value=lambda v: str(int(round(v))),
                )
                if prev is not None
                else None
            ),
            "trendSeries": trend_core.get("conversion_pct", []),
            "trendSeriesDates": trend_core.get("case_opened_dates", []),
        },
    )
    cards.append(
        {
            "label": "End-to-End Triage Conv.",
            "value": f"{cur['triage_conversion_pct']}%",
            "change": (
                _make_change_block(
                    prev,
                    "triage_conversion_pct",
                    float(cur["triage_conversion_pct"]),
                    higher_is_better=True,
                    mode="pts",
                    format_prev_value=lambda v: str(int(round(v))),
                )
                if prev is not None
                else None
            ),
            "trendSeries": trend_core.get("triage_conversion_pct", []),
            "trendSeriesDates": trend_core.get("case_opened_dates", []),
        },
    )
    # Initial payment was removed, so paid-time and revenue cards are not reported.
    # cards.append(
    #     {
    #         "label": "Avg. Time to Paid",
    #         "value": f"{cur['avg_time_to_paid_days']:.1f} d",
    #         "change": (
    #             _make_change_block(
    #                 prev,
    #                 "avg_time_to_paid_days",
    #                 float(cur["avg_time_to_paid_days"]),
    #                 higher_is_better=False,
    #                 mode="day_diff",
    #                 format_prev_value=lambda v: f"{float(v):.1f} d",
    #             )
    #             if prev is not None
    #             else None
    #         ),
    #         "trendSeries": avg_series,
    #     },
    # )
    # cards.append(
    #     {
    #         "label": "Revenue Paid",
    #         "value": format_currency_compact(int(cur["revenue_gbp"])),
    #         "change": (
    #             _make_change_block(
    #                 prev,
    #                 "revenue_gbp",
    #                 float(cur["revenue_gbp"]),
    #                 higher_is_better=True,
    #                 mode="currency_pct",
    #                 format_prev_value=lambda v: format_currency_compact(int(v)),
    #             )
    #             if prev is not None
    #             else None
    #         ),
    #         "trendSeries": trend_core.get("revenue_gbp", []),
    #     },
    # )
    cards.append(
        {
            "label": "Stalled Cases",
            "value": cur["stalled"],
            "change": (
                _make_change_block(
                    prev,
                    "stalled",
                    float(cur["stalled"]),
                    higher_is_better=False,
                    mode="pct",
                    format_prev_value=lambda v: _fmt_int_commas(int(v)),
                )
                if prev is not None
                else None
            ),
            "trendSeries": stalled_series,
        },
    )
    return cards


def _fetch_general_info_inputs(
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None,
    landing_page: str | None,
    status: CaseStatusEnum | None = None,
) -> tuple[list[dict[str, Any]], float | None, int, int]:
    start_date = _normalize_utc(start_date)
    end_date = _normalize_utc(end_date)
    days = _list_days_half_open_utc(start_date, end_date)
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_stall = pool.submit(
            _execute_active_stalled,
            start_date,
            end_date,
            source,
            landing_page,
            status,
        )
        f_resolve = pool.submit(
            _case_scope_conversion_series,
            start_date,
            end_date,
            source,
            landing_page,
            status,
            funnel_tag=_RESOLVE_CASE_OPENED_FUNNEL,
            case_steps=_END_TO_END_CASE_FUNNEL_ROWS,
            days=days,
        )
        f_triage = pool.submit(
            _case_scope_conversion_series,
            start_date,
            end_date,
            source,
            landing_page,
            status,
            funnel_tag=_TRIAGE_CASE_OPENED_FUNNEL,
            case_steps=_END_TO_END_TRIAGE_CASE_FUNNEL_ROWS,
            days=days,
        )
    resolve_pct, _ = f_resolve.result()
    triage_pct, _ = f_triage.result()
    return f_stall.result(), None, resolve_pct, triage_pct


def _landing_path_present(path_col: Any) -> Any:
    """SQL filter: path is non-null and non-empty."""
    return and_(
        path_col.isnot(None),
        path_col != "",
    )


def _navigator_session_ids_subquery(
    start_date: datetime,
    end_date: datetime,
) -> Any:
    """Session ids tied to navigator users or ``role_hint: navigator`` events in range."""
    role_hint = AnalyticsEvent.properties["traits"]["role_hint"].astext
    navigator_user_ids = select(UserRole.user_id).where(
        UserRole.role_id == UserRoleEnum.NAVIGATOR.id,
    )
    by_role_hint = select(AnalyticsEvent.session_id.label("session_id")).where(
        AnalyticsEvent.timestamp >= start_date,
        AnalyticsEvent.timestamp < end_date,
        role_hint.isnot(None),
        func.lower(role_hint) == "navigator",
    )
    by_user = select(AnalyticsSession.id.label("session_id")).where(
        AnalyticsSession.started_at >= start_date,
        AnalyticsSession.started_at < end_date,
        AnalyticsSession.user_id.in_(navigator_user_ids),
    )
    return union(by_role_hint, by_user).subquery("navigator_session_ids")


def _analytics_event_not_navigator_role_hint() -> Any:
    role_hint = AnalyticsEvent.properties["traits"]["role_hint"].astext
    return or_(role_hint.is_(null()), func.lower(role_hint) != "navigator")


def get_distinct_landing_pages(
    db: OrmSession,
    start_date: datetime,
    end_date: datetime,
) -> list[str]:
    """
    Distinct landing paths in ``[start_date, end_date)``.

    Combines session ``entry_page`` and ``page_view`` ``page_path`` values. Excludes
    navigator sessions and page views with ``role_hint: navigator`` (internal traffic).
    """
    navigator_sessions = _navigator_session_ids_subquery(start_date, end_date)
    session_paths = select(AnalyticsSession.entry_page.label("page_path")).where(
        AnalyticsSession.started_at >= start_date,
        AnalyticsSession.started_at < end_date,
        _landing_path_present(AnalyticsSession.entry_page),
        AnalyticsSession.id.not_in(select(navigator_sessions.c.session_id)),
    )
    event_paths = select(AnalyticsEvent.page_path.label("page_path")).where(
        AnalyticsEvent.timestamp >= start_date,
        AnalyticsEvent.timestamp < end_date,
        AnalyticsEvent.event_code == "site_visit",
        AnalyticsEvent.is_bot.is_(false()),
        _landing_path_present(AnalyticsEvent.page_path),
        _analytics_event_not_navigator_role_hint(),
        AnalyticsEvent.session_id.not_in(select(navigator_sessions.c.session_id)),
    )
    combined = union(session_paths, event_paths).subquery("landing_paths")
    stmt = select(combined.c.page_path).distinct().order_by(combined.c.page_path)
    return list(db.execute(stmt).scalars().all())


def get_analytics_data(
    db: OrmSession,
    start_date: datetime,
    end_date: datetime,
    source: SourceEnum | None = None,
    landing_page: str | None = None,
    status: CaseStatusEnum | None = None,
    *,
    compare: CompareFilterEnum | None = None,
    period: ComparePeriodEnum | None = None,
) -> dict[str, Any]:
    """
    Run all analytics datasets in parallel.

    ``db`` is accepted for API compatibility but not used for these reads (avoids sharing
    one ORM session across threads). Time range is half-open: ``[start_date, end_date)``.

    When ``compare`` is set, the effective current window may be derived (period / QTD / YTD);
    ``general_info`` then includes change vs the comparison window.

    Per-funnel ``source`` / ``landing_page`` kwargs were removed; end-to-end and resolve
    sections both use the global ``source`` and ``landing_page`` filters.
    """
    cur_start, cur_end, prev_tup = resolve_comparison_windows(
        start_date,
        end_date,
        compare,
        period,
    )
    _ = db  # request-scoped session; funnel reads use short-lived sessions in workers
    with ThreadPoolExecutor(max_workers=11) as pool:
        fut_end = pool.submit(
            _execute_end_to_end,
            cur_start,
            cur_end,
            source,
            landing_page,
            status,
        )
        fut_end_triage = pool.submit(
            _execute_end_to_end_triage,
            cur_start,
            cur_end,
            source,
            landing_page,
            status,
        )
        fut_resolve = pool.submit(
            _execute_resolve,
            cur_start,
            cur_end,
            source,
            landing_page,
            status,
        )
        fut_alignment_check = pool.submit(
            _execute_alignment_check,
            cur_start,
            cur_end,
            source,
            landing_page,
            status,
        )
        fut_high_intent = pool.submit(
            _execute_high_intent,
            cur_start,
            cur_end,
            source,
            landing_page,
            status,
        )
        fut_conv = pool.submit(
            _execute_conversion_by_source,
            cur_start,
            cur_end,
            source,
            landing_page,
            status,
        )
        fut_active_stalled = pool.submit(
            _execute_active_stalled,
            cur_start,
            cur_end,
            source,
            landing_page,
            status,
        )
        fut_velocity = pool.submit(
            _execute_average_time_between_stages,
            cur_start,
            cur_end,
            source,
            landing_page,
            status,
        )
        # fut_avg_time_to_paid = pool.submit(
        #     _execute_average_time_to_paid,
        #     cur_start,
        #     cur_end,
        #     source,
        #     landing_page,
        #     status,
        # )
        # fut_revenue = pool.submit(
        #     _execute_revenue_by_source,
        #     cur_start,
        #     cur_end,
        #     source,
        #     landing_page,
        #     status,
        # )
        fut_trend = pool.submit(
            _execute_trend_series,
            cur_start,
            cur_end,
            source,
            landing_page,
            status,
        )
        end_to_end_rows = fut_end.result()
        end_to_end_triage_rows = fut_end_triage.result()
        resolve_rows = fut_resolve.result()
        alignment_check_rows = fut_alignment_check.result()
        high_intent_rows = fut_high_intent.result()
        conversion_by_source = fut_conv.result()
        active_stalled = fut_active_stalled.result()
        average_time_between_stages = fut_velocity.result()
        # avg_time_to_paid_days = fut_avg_time_to_paid.result()
        # revenue_by_source = fut_revenue.result()
        avg_time_to_paid_days = None
        revenue_by_source: list[dict[str, Any]] = []
        trend_core = fut_trend.result()

    case_opened_total = trend_core.get("case_opened_total")
    if case_opened_total is None:
        case_opened_total = sum(trend_core.get("case_opened") or [])
    cur_metrics = _scalar_metrics(
        revenue_by_source,
        active_stalled,
        conversion_pct=int(trend_core.get("conversion_pct_total") or 0),
        triage_conversion_pct=int(trend_core.get("triage_conversion_pct_total") or 0),
        avg_time_to_paid_days=avg_time_to_paid_days,
        case_opened=int(case_opened_total or 0),
    )
    prev_metrics: dict[str, Any] | None = None
    if prev_tup is not None:
        ps, pe = prev_tup
        prev_stalled, prev_avg_time_to_paid, prev_conversion_pct, prev_triage_pct = (
            _fetch_general_info_inputs(
                ps,
                pe,
                source,
                landing_page,
                status,
            )
        )
        prev_case_opened = _execute_case_opened_count(
            ps,
            pe,
            source,
            landing_page,
            status,
        )
        prev_metrics = _scalar_metrics(
            [],
            prev_stalled,
            conversion_pct=prev_conversion_pct,
            triage_conversion_pct=prev_triage_pct,
            avg_time_to_paid_days=prev_avg_time_to_paid,
            case_opened=prev_case_opened,
        )

    general_info = _build_general_info_cards(cur_metrics, prev_metrics, trend_core)

    return {
        "end_to_end_resolve_funnel": _map_funnel_rows_for_response(end_to_end_rows),
        "end_to_end_triage_funnel": _map_funnel_rows_for_response(end_to_end_triage_rows),
        "resolve_funnel": resolve_rows,
        "alignment_check_funnel": alignment_check_rows,
        "high_intent_funnel": _map_funnel_rows_for_response(high_intent_rows),
        "conversion_by_source": _map_conversion_by_source_for_response(
            conversion_by_source,
        ),
        "active_stalled": _map_funnel_rows_for_response(active_stalled),
        "average_time_between_stages": average_time_between_stages,
        "revenue_by_source": revenue_by_source,
        "general_info": general_info,
    }


def _format_csv_datetime(value: datetime | None) -> str:
    if value is None:
        return ""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _humanize_filter_value(value: Any, *, none_label: str = "All") -> str:
    if value is None or value == "":
        return none_label
    raw = getattr(value, "value", value)
    if isinstance(raw, datetime):
        return _format_csv_datetime(raw)
    if isinstance(raw, bool):
        return "Yes" if raw else "No"
    text = str(raw)
    if not text:
        return none_label
    if text.upper() in {"QTD", "YTD"}:
        return text.upper()
    if text.endswith("d") and text[:-1].isdigit():
        return text
    return text.replace("_", " ").title()


def _csv_series_cell(values: list[int]) -> str:
    return ",".join(str(v) for v in values)


def _report_filter_rows(
    request: GetAnalyticsRequest,
    cur_start: datetime,
    cur_end: datetime,
    previous_window: tuple[datetime, datetime] | None,
) -> list[tuple[str, str]]:
    return [
        ("Effective Current Start", _format_csv_datetime(cur_start)),
        ("Effective Current End", _format_csv_datetime(cur_end)),
        ("Compare Filter", _humanize_filter_value(request.compare, none_label="Not applied")),
        ("Compare Period", _humanize_filter_value(request.period, none_label="Not applied")),
        (
            "Previous Comparison Window",
            (
                f"{_format_csv_datetime(previous_window[0])} to "
                f"{_format_csv_datetime(previous_window[1])}"
            )
            if previous_window is not None
            else "Not applied"
        ),
        ("Global Source", _humanize_filter_value(request.source)),
        ("Global Landing Page", _humanize_filter_value(request.landing_page)),
        ("Case Status", _humanize_filter_value(request.status)),
    ]


def _report_data_sheets(data: AnalyticsReportData) -> list[tuple[str, list[str], list[list[Any]]]]:
    return [
        (
            "General Info",
            [
                "label",
                "value",
                "change_delta",
                "change_trend",
                "previous_value",
                "trend_series",
                "trend_series_dates",
            ],
            [
                [
                    row.label,
                    row.value,
                    row.change.deltaText if row.change else "",
                    row.change.trend if row.change else "",
                    row.change.previous_value if row.change else "",
                    _csv_series_cell(row.trendSeries),
                    _csv_series_cell(row.trendSeriesDates or []),
                ]
                for row in data.general_info
            ],
        ),
        (
            "End-to-End Resolve Funnel",
            [
                "step_index",
                "event_type",
                "total_count",
                "pct_of_visit",
                "dropoff_lost_count",
                "dropoff_pct",
            ],
            [
                [
                    row.step_index,
                    row.event_type,
                    row.total_count,
                    row.pct_of_visit if row.pct_of_visit is not None else "",
                    row.dropoff.get("lost_count", "") if row.dropoff else "",
                    row.dropoff.get("drop_off_pct", "") if row.dropoff else "",
                ]
                for row in data.end_to_end_resolve_funnel
            ],
        ),
        (
            "End-to-End Triage Funnel",
            [
                "step_index",
                "event_type",
                "total_count",
                "pct_of_visit",
                "dropoff_lost_count",
                "dropoff_pct",
            ],
            [
                [
                    row.step_index,
                    row.event_type,
                    row.total_count,
                    row.pct_of_visit if row.pct_of_visit is not None else "",
                    row.dropoff.get("lost_count", "") if row.dropoff else "",
                    row.dropoff.get("drop_off_pct", "") if row.dropoff else "",
                ]
                for row in data.end_to_end_triage_funnel
            ],
        ),
        (
            "Resolve Funnel",
            ["step_index", "event_type", "total_count", "pct_drop"],
            [
                [
                    row.step_index,
                    row.event_type,
                    row.total_count,
                    row.pct_drop if row.pct_drop is not None else "",
                ]
                for row in data.resolve_funnel
            ],
        ),
        (
            "Alignment Check Funnel",
            ["step_index", "event_type", "total_count", "pct_drop"],
            [
                [
                    row.step_index,
                    row.event_type,
                    row.total_count,
                    row.pct_drop if row.pct_drop is not None else "",
                ]
                for row in data.alignment_check_funnel
            ],
        ),
        (
            "High Intent Funnel",
            ["step_index", "event_type", "total_count", "pct_drop"],
            [
                [
                    row.step_index,
                    row.event_type,
                    row.total_count,
                    row.pct_drop if row.pct_drop is not None else "",
                ]
                for row in data.high_intent_funnel
            ],
        ),
        (
            "Conversion By Source",
            [
                "source",
                "sessions_count",
                "sessions_pct_of_conversion",
                "case_opened_count",
                "case_opened_pct_of_conversion",
                "alignment_check_completed_count",
                "alignment_check_completed_pct_of_conversion",
                "match_confirmed_count",
                "match_confirmed_pct_of_conversion",
                "profile_card_sent_count",
                "profile_card_sent_pct_of_conversion",
                "expert_assigned_count",
                "expert_assigned_pct_of_conversion",
                "engage_get_started_count",
                "engage_get_started_pct_of_conversion",
            ],
            [
                [
                    row.source,
                    row.sessions.count,
                    row.sessions.pct_of_conversion,
                    row.case_opened.count,
                    row.case_opened.pct_of_conversion,
                    row.alignment_check_completed.count,
                    row.alignment_check_completed.pct_of_conversion,
                    row.match_confirmed.count,
                    row.match_confirmed.pct_of_conversion,
                    row.profile_card_sent.count,
                    row.profile_card_sent.pct_of_conversion,
                    row.expert_assigned.count,
                    row.expert_assigned.pct_of_conversion,
                    row.engage_get_started.count,
                    row.engage_get_started.pct_of_conversion,
                ]
                for row in data.conversion_by_source
            ],
        ),
        (
            "Active vs Stalled",
            ["step_index", "event_type", "active_count", "stalled_count"],
            [
                [row.step_index, row.event_type, row.active_count, row.stalled_count]
                for row in data.active_stalled
            ],
        ),
        (
            "Average Time Between Stages",
            ["step_index", "event_type", "deviation_day"],
            [
                [row.step_index, row.event_type, row.deviation_day or ""]
                for row in data.average_time_between_stages
            ],
        ),
        # (
        #     "Revenue By Source",
        #     ["source", "total_revenue"],
        #     [[row.source, row.total_revenue] for row in data.revenue_by_source],
        # ),
    ]


def _write_excel_table(ws: Any, headers: list[str], rows: list[list[Any]], *, start_row: int = 1) -> None:
    for col, header in enumerate(headers, start=1):
        ws.cell(row=start_row, column=col, value=header)
    for row_offset, row in enumerate(rows, start=start_row + 1):
        for col, value in enumerate(row, start=1):
            ws.cell(row=row_offset, column=col, value=value)


def build_analytics_report_excel(
    request: GetAnalyticsRequest,
    data: AnalyticsReportData,
) -> tuple[bytes, str]:
    from openpyxl import Workbook

    cur_start, cur_end, previous_window = resolve_comparison_windows(
        request.start_date,
        request.end_date,
        request.compare,
        request.period,
    )

    wb = Workbook()
    summary = wb.active
    summary.title = "Summary"
    summary["A1"] = "Analytics Report"
    summary["A2"] = "Generated At"
    summary["B2"] = _format_csv_datetime(datetime.now(timezone.utc))

    filter_row = 4
    summary.cell(row=filter_row, column=1, value="Filters Used")
    filter_row += 1
    summary.cell(row=filter_row, column=1, value="Filter")
    summary.cell(row=filter_row, column=2, value="Value")
    filter_row += 1
    for label, value in _report_filter_rows(request, cur_start, cur_end, previous_window):
        summary.cell(row=filter_row, column=1, value=label)
        summary.cell(row=filter_row, column=2, value=value)
        filter_row += 1

    for sheet_name, headers, rows in _report_data_sheets(data):
        ws = wb.create_sheet(sheet_name)
        _write_excel_table(ws, headers, rows)

    buffer = io.BytesIO()
    wb.save(buffer)
    start_str = cur_start.date().isoformat()
    end_str = cur_end.date().isoformat()
    filename = f"analytics_report_{start_str}_to_{end_str}.xlsx"
    return buffer.getvalue(), filename


class AnalyticsCaptureValidationError(Exception):
    """Invalid frontend analytics capture (client or authorization error)."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _parse_payload_timestamp(payload: dict[str, Any]) -> datetime:
    raw = payload.get("timestamp")
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    if isinstance(raw, str):
        s = raw.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    return datetime.now(timezone.utc)


def _entry_page_from_context(context: dict[str, Any]) -> str:
    page = context.get("page") or {}
    path = page.get("path")
    if isinstance(path, str) and path:
        return path
    url = page.get("url")
    if isinstance(url, str) and url:
        parsed = urlparse(url)
        if parsed.path:
            return parsed.path or "/"
    return "/"


def _campaign_dict(context: dict[str, Any]) -> dict[str, Any]:
    c = context.get("campaign") or {}
    return c if isinstance(c, dict) else {}


def _normalize_netloc(ref: str | None) -> str | None:
    if not isinstance(ref, str) or not ref.strip():
        return None
    try:
        stripped = ref.strip()
        parsed = urlparse(stripped)
        netloc = parsed.netloc or stripped.split("/")[0]
        host = netloc.lower().split(":")[0].removeprefix("www.")
        return host or None
    except Exception:
        return None


def _page_registration_host(page_url: str | None) -> str | None:
    if not isinstance(page_url, str) or not page_url.strip():
        return None
    try:
        host = urlparse(page_url.strip()).netloc.lower().split(":")[0]
        return host.removeprefix("www.") or None
    except Exception:
        return None


def _host_matches_suffix(host: str | None, suffixes: frozenset[str]) -> bool:
    if not host:
        return False
    h = host.lower().removeprefix("www.")
    return any(h == s or h.endswith("." + s) for s in suffixes)


def _parse_query_params(url: str | None) -> dict[str, str]:
    if not isinstance(url, str) or not url.strip():
        return {}
    try:
        parsed = urlparse(url.strip())
        pairs = parse_qsl(parsed.query, keep_blank_values=False)
        return dict(pairs)
    except Exception:
        return {}


def _strip_campaign_val(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s if s else None
    return str(value)


def _merge_missing_campaign_from_url(campaign: dict[str, Any], page_url: str | None) -> None:
    """Fill missing attribution keys from the landing URL query string (in-place)."""
    params = _parse_query_params(page_url)
    if not params:
        return
    lower_keys = {k.lower(): v for k, v in params.items()}
    utm_map = {
        "utm_source": "source",
        "utm_medium": "medium",
        "utm_campaign": "campaign",
        "utm_term": "term",
        "utm_content": "content",
    }
    for uk, ck in utm_map.items():
        if _strip_campaign_val(campaign.get(ck)):
            continue
        val = lower_keys.get(uk.lower())
        if val:
            campaign[ck] = val
    if _strip_campaign_val(campaign.get("gclid")):
        return
    for click_key in ("gclid", "gbraid", "wbraid"):
        v = lower_keys.get(click_key)
        if v:
            campaign["gclid"] = v
            break


def _derive_traffic_source_category(
    campaign: dict[str, Any],
    page_url: str | None,
    referrer: str | None,
) -> tuple[str | None, str | None]:
    """
    Infer ``SourceEnum`` bucket and medium when ``campaign.source`` is absent.

    Uses click IDs, UTM parameters, then referrer host classification.
    """
    params_lc = {k.lower(): v for k, v in _parse_query_params(page_url).items()}

    def _param_click(key: str) -> str | None:
        return _strip_campaign_val(params_lc.get(key.lower()))

    if any(_param_click(k) for k in ("gclid", "gbraid", "wbraid")):
        return SourceEnum.GOOGLE_ADS.value, "cpc"
    if _param_click("msclkid"):
        return SourceEnum.REFERRAL.value, "cpc"
    if _param_click("fbclid"):
        return SourceEnum.SOCIAL.value, "paid_social"
    if _param_click("li_fat_id"):
        return SourceEnum.SOCIAL.value, "paid_social"

    src_raw = (_strip_campaign_val(campaign.get("source")) or "").lower()
    med_raw = (_strip_campaign_val(campaign.get("medium")) or "").lower()

    paid_mediums = {
        "cpc",
        "ppc",
        "paidsearch",
        "paid_search",
        "paid-social",
        "paidsocial",
        "paid_social",
    }
    partner_mediums = {"partner", "partnership", "affiliate"}
    if med_raw in partner_mediums or any(
        tok in src_raw for tok in ("partner", "partnership", "affiliate")
    ):
        return SourceEnum.PARTNER_ORG.value, med_raw or "partner"

    if med_raw in paid_mediums:
        social_sources = {
            "facebook",
            "fb",
            "instagram",
            "ig",
            "linkedin",
            "twitter",
            "x",
            "tiktok",
            "reddit",
            "youtube",
            "yt",
        }
        if src_raw in social_sources:
            return SourceEnum.SOCIAL.value, med_raw or "cpc"
        if src_raw in {"google", "goog", "adwords", "dv360"} or not src_raw:
            return SourceEnum.GOOGLE_ADS.value, med_raw or "cpc"
        return SourceEnum.REFERRAL.value, med_raw or "cpc"

    if med_raw in {"organic", "organic-search", "organic_search"}:
        return SourceEnum.ORGANIC_SEARCH.value, med_raw or "organic"

    ref_host = _normalize_netloc(referrer)
    page_host = _page_registration_host(page_url)
    if ref_host and page_host and ref_host == page_host:
        ref_host = None

    if ref_host and _host_matches_suffix(ref_host, _SOCIAL_HOST_SUFFIXES):
        return SourceEnum.SOCIAL.value, "social"

    if ref_host and _host_matches_suffix(ref_host, _SEARCH_ENGINE_HOST_SUFFIXES):
        return SourceEnum.ORGANIC_SEARCH.value, "organic"

    if ref_host:
        return SourceEnum.REFERRAL.value, "referral"

    if src_raw or med_raw:
        if "google" in src_raw and med_raw in {"", "referral"}:
            return SourceEnum.ORGANIC_SEARCH.value, med_raw or "referral"
        return SourceEnum.REFERRAL.value, med_raw or "referral"

    return SourceEnum.DIRECT.value, "direct"


def _enrich_capture_context(context: dict[str, Any] | None) -> dict[str, Any]:
    """Deep-copy context; merge URL UTMs; derive traffic category when ``source`` is absent."""
    ctx: dict[str, Any] = copy.deepcopy(context) if isinstance(context, dict) else {}
    page = ctx.get("page") or {}
    page_url = page.get("url") if isinstance(page, dict) else None
    referrer = page.get("referrer") if isinstance(page, dict) else None

    campaign = dict(_campaign_dict(ctx))
    _merge_missing_campaign_from_url(campaign, page_url)

    if not _strip_campaign_val(campaign.get("source")):
        derived_src, derived_med = _derive_traffic_source_category(
            campaign,
            page_url if isinstance(page_url, str) else None,
            referrer if isinstance(referrer, str) else None,
        )
        if derived_src:
            campaign["source"] = derived_src
        if derived_med and not _strip_campaign_val(campaign.get("medium")):
            campaign["medium"] = derived_med

    ctx["campaign"] = campaign
    return ctx


def _traits_role_hint_customer(traits: dict[str, Any]) -> bool:
    raw = traits.get("role_hint")
    if raw is None:
        return False
    return str(raw).strip().lower() == "customer"


def _user_is_customer(db: OrmSession, user_id: int) -> bool:
    row = (
        db.query(UserRole)
        .filter(
            UserRole.user_id == user_id,
            UserRole.role_id == UserRoleEnum.CUSTOMER.id,
        )
        .first()
    )
    return row is not None


def _should_apply_customer_touch(
    db: OrmSession,
    user_id: int,
    properties_traits: dict[str, Any],
) -> bool:
    if _traits_role_hint_customer(properties_traits):
        return True
    return _user_is_customer(db, user_id)


def _merge_user_traits(user_row: User, traits: dict[str, Any]) -> None:
    if not traits:
        return
    current = user_row.traits if isinstance(user_row.traits, dict) else {}
    merged = dict(current)
    for key, value in traits.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        merged[key] = value
    user_row.traits = merged


def _apply_customer_id_backfill(
    db: OrmSession,
    *,
    session_id: UUID,
    anonymous_id: UUID,
    user_id: int | None,
    case_id: int | None,
) -> None:
    """
    Fill in missing IDs on earlier rows of this visitor session.

    Only ``NULL`` columns are written. One session can run several journeys and open
    more than one case (e.g. triage then resolve), so an id already recorded on a row
    belongs to that earlier journey and must not be rewritten — overwriting it would
    collapse both cases into one in every case-scoped report.
    """
    if user_id is not None:
        db.execute(
            update(AnalyticsEvent)
            .where(
                AnalyticsEvent.session_id == session_id,
                AnalyticsEvent.anonymous_id == anonymous_id,
                AnalyticsEvent.user_id.is_(null()),
            )
            .values(user_id=user_id)
        )
    if case_id is not None:
        db.execute(
            update(AnalyticsEvent)
            .where(
                AnalyticsEvent.session_id == session_id,
                AnalyticsEvent.anonymous_id == anonymous_id,
                AnalyticsEvent.case_id.is_(null()),
            )
            .values(case_id=case_id)
        )
    if user_id is not None:
        db.execute(
            update(AnalyticsSession)
            .where(
                AnalyticsSession.id == session_id,
                AnalyticsSession.user_id.is_(null()),
            )
            .values(user_id=user_id)
        )


def _is_direct_or_empty_attribution(campaign: dict[str, Any]) -> bool:
    src = (campaign.get("source") or "").strip().lower()
    med = (campaign.get("medium") or "").strip().lower()
    if not src and not med:
        return True
    return src in {"direct", "(none)"} or med in {"direct", "(none)"}


def _attribution_for_touch(
    campaign: dict[str, Any],
    sess: AnalyticsSession,
) -> dict[str, Any]:
    """
    Build attribution for user touch columns.

    Uses capture ``campaign`` values when meaningful; otherwise falls back to the
    session's stored source / medium / campaign (set on session start).

    Current-event ``direct`` / empty values do not block a stronger session attribution
    (common on ``case_opened`` after anonymous browsing with UTMs).
    """
    out = dict(campaign)
    session_attr = {
        "source": sess.source,
        "medium": sess.medium,
        "campaign": sess.campaign,
    }
    if _is_direct_or_empty_attribution(out) and not _is_direct_or_empty_attribution(
        session_attr
    ):
        return session_attr

    if not _strip_campaign_val(out.get("source")) and sess.source:
        out["source"] = sess.source
    if not _strip_campaign_val(out.get("medium")) and sess.medium:
        out["medium"] = sess.medium
    if not _strip_campaign_val(out.get("campaign")) and sess.campaign:
        out["campaign"] = sess.campaign
    return out


def _format_snapshot_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _session_snapshot_for_analytics_data(sess: AnalyticsSession) -> dict[str, Any]:
    """Session row fields stored on ``case.analytics_data`` at ``case_opened``."""
    return {
        "id": str(sess.id),
        "anonymous_id": str(sess.anonymous_id),
        "user_id": sess.user_id,
        "started_at": _format_snapshot_datetime(sess.started_at),
        "last_event_at": _format_snapshot_datetime(sess.last_event_at),
        "ended_at": _format_snapshot_datetime(sess.ended_at),
        "entry_page": sess.entry_page,
        "exit_page": sess.exit_page,
        "source": sess.source,
        "medium": sess.medium,
        "campaign": sess.campaign,
        "term": sess.term,
        "content": sess.content,
        "gclid": sess.gclid,
        "referrer": sess.referrer,
        "user_agent": sess.user_agent,
        "device_type": sess.device_type,
        "browser": sess.browser,
        "client_os": sess.client_os,
        "country": sess.country,
        "locale": sess.locale,
        "client_timezone": sess.client_timezone,
        "event_count": sess.event_count,
        "is_bot": sess.is_bot,
    }


def _build_case_analytics_capture_payload(
    *,
    event_name: str,
    timestamp: datetime,
    anonymous_id: UUID,
    session_id: UUID,
    user_id: int | None,
    case_id: int | None,
    sess: AnalyticsSession,
    campaign: dict[str, Any],
    context: dict[str, Any],
    properties_traits: dict[str, Any],
    properties_event_data: dict[str, Any],
) -> dict[str, Any]:
    """Full capture + session snapshot stored on ``case.analytics_data`` at ``case_opened``."""
    ts_utc = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
    touch_campaign = _attribution_for_touch(campaign, sess)
    ctx_out = copy.deepcopy(context)
    ctx_out["campaign"] = touch_campaign
    return {
        "event_name": event_name,
        "timestamp": ts_utc.isoformat(),
        "anonymous_id": str(anonymous_id),
        "session_id": str(session_id),
        "user_id": user_id,
        "case_id": case_id,
        "session": _session_snapshot_for_analytics_data(sess),
        "context": ctx_out,
        "properties": {
            "traits": properties_traits,
            "event_data": properties_event_data,
        },
    }


def _apply_case_opened_analytics_data(
    db: OrmSession,
    case_id: int | None,
    payload: dict[str, Any],
) -> None:
    """Persist capture payload on the case once, when ``case_opened`` and column is null."""
    if case_id is None:
        return
    case_row = db.get(Case, case_id)
    if case_row is None or case_row.analytics_data is not None:
        return
    case_row.analytics_data = payload


def _apply_customer_touch_attribution(
    user_row: User,
    campaign: dict[str, Any],
    ts: datetime,
    *,
    properties_traits: dict[str, Any] | None = None,
) -> None:
    """Merge capture traits; set last-touch always; first-touch while ``first_touch_at`` is unset."""
    if properties_traits:
        _merge_user_traits(user_row, properties_traits)

    is_direct = _is_direct_or_empty_attribution(campaign)
    if is_direct and user_row.first_touch_at is not None:
        return

    source = campaign.get("source")
    medium = campaign.get("medium")
    camp = campaign.get("campaign")
    user_row.last_touch_source = source
    user_row.last_touch_medium = medium
    user_row.last_touch_campaign = camp
    user_row.last_touch_at = ts
    if user_row.first_touch_at is None:
        user_row.first_touch_source = source
        user_row.first_touch_medium = medium
        user_row.first_touch_campaign = camp
        user_row.first_touch_at = ts


def _maybe_apply_customer_user_attribution(
    db: OrmSession,
    *,
    user_id: int,
    sess: AnalyticsSession,
    campaign: dict[str, Any],
    ts: datetime,
    properties_traits: dict[str, Any],
) -> None:
    if not _should_apply_customer_touch(db, user_id, properties_traits):
        return
    user_row = db.get(User, user_id)
    if user_row is None:
        return
    touch_campaign = _attribution_for_touch(campaign, sess)
    _apply_customer_touch_attribution(
        user_row,
        touch_campaign,
        ts,
        properties_traits=properties_traits,
    )


def _session_is_exit(
    event_name: str,
    event_data: dict[str, Any],
) -> bool:
    if event_data.get("session_exit") is True:
        return True
    if event_name in {"session_end", "session_ended", "application_exit"}:
        return True
    return False


# def _user_is_customer(db: OrmSession, user_id: int) -> bool:
#     row = (
#         db.query(UserRole)
#         .filter(
#             UserRole.user_id == user_id,
#             UserRole.role_id == UserRoleEnum.CUSTOMER.id,
#         )
#         .first()
#     )
#     return row is not None


# def _verify_customer_owns_case(db: OrmSession, user_id: int, case_id: int) -> bool:
#     customer = db.query(Customer).filter(Customer.user_id == user_id).first()
#     if customer is None:
#         return False
#     link = (
#         db.query(CaseCustomer)
#         .filter(
#             CaseCustomer.case_id == case_id,
#             CaseCustomer.customer_id == customer.id,
#         )
#         .first()
#     )
#     return link is not None


def _insert_system_site_visit(
    db: OrmSession,
    *,
    sess: AnalyticsSession,
    anonymous_id: UUID,
    user_id: int | None,
    case_id: int | None,
    anchor_ts: datetime,
    page_url: str | None = None,
    page_path: str | None = None,
    page_title: str | None = None,
    referrer: str | None = None,
    properties: dict[str, Any] | None = None,
) -> datetime:
    """
    Record a server-generated ``site_visit`` immediately before the session's first event.

    ``anchor_ts`` is the timestamp of the first captured event; ``site_visit`` is stored
    1µs earlier so funnel ordering treats the visit as step 1.
    """
    anchor = anchor_ts if anchor_ts.tzinfo else anchor_ts.replace(tzinfo=timezone.utc)
    site_ts = anchor - timedelta(microseconds=1)
    sv_props = (
        copy.deepcopy(properties)
        if properties is not None
        else {"traits": {}, "event_data": {}}
    )
    db.add(
        AnalyticsEvent(
            event_code=AnalyticsEvents.SITE_VISIT.value,
            anonymous_id=anonymous_id,
            session_id=sess.id,
            user_id=user_id,
            case_id=case_id,
            timestamp=site_ts,
            page_url=page_url,
            page_path=page_path,
            page_title=page_title,
            referrer=referrer,
            properties=sv_props,
        )
    )
    db.flush()
    sess.event_count = (sess.event_count or 0) + 1
    if sess.started_at is None or site_ts < sess.started_at:
        sess.started_at = site_ts
    if sess.last_event_at is None or site_ts > sess.last_event_at:
        sess.last_event_at = site_ts
    return site_ts


def save_email_cta_analytics_event(
    db: OrmSession,
    *,
    payload: dict[str, Any],
    user_id: int,
    case_id: int,
) -> AnalyticsEvent:
    """Persist a server-side email CTA analytics row (synthetic session + event)."""
    ts = _parse_payload_timestamp(payload)
    session_id = uuid4()
    anonymous_id = uuid4()
    site_ts = ts - timedelta(microseconds=1)
    sess = AnalyticsSession(
        id=session_id,
        anonymous_id=anonymous_id,
        user_id=user_id,
        started_at=site_ts,
        last_event_at=ts,
        entry_page="/",
        exit_page=None,
        source=SourceEnum.EMAIL.value,
        medium="email",
        event_count=0,
    )
    db.add(sess)
    db.flush()
    props = {"traits": {}, "event_data": {}, "email_cta_payload": payload}
    _insert_system_site_visit(
        db,
        sess=sess,
        anonymous_id=anonymous_id,
        user_id=user_id,
        case_id=case_id,
        anchor_ts=ts,
        page_path="/",
        properties=props,
    )
    ev = AnalyticsEvent(
        event_code=EventType.EMAIL_CTA_CLICKED.value,
        anonymous_id=anonymous_id,
        session_id=session_id,
        user_id=user_id,
        case_id=case_id,
        timestamp=ts,
        page_url=None,
        page_path=None,
        page_title=None,
        referrer=None,
        properties=props,
    )
    db.add(ev)
    sess.event_count = (sess.event_count or 0) + 1
    sess.last_event_at = ts
    _maybe_apply_customer_user_attribution(
        db,
        user_id=user_id,
        sess=sess,
        campaign={"source": SourceEnum.EMAIL.value, "medium": "email"},
        ts=ts,
        properties_traits=props.get("traits") if isinstance(props.get("traits"), dict) else {},
    )
    db.commit()
    db.refresh(ev)
    return ev


def create_analytics_deletion_request(
    db: OrmSession,
    *,
    subject_type: DeletionRequestSubjectType,
    subject_id: UUID,
    reason: str | None = None,
    status: DeletionRequestStatus = DeletionRequestStatus.PENDING,
) -> DeletionRequest:
    """Queue a pending analytics deletion request row and nothing else."""
    if status != DeletionRequestStatus.PENDING:
        raise AnalyticsCaptureValidationError(
            "status must be PENDING when creating a deletion request",
            status_code=400,
        )

    row = DeletionRequest(
        subject_type=subject_type.value,
        subject_id=str(subject_id),
        reason=reason.strip() if isinstance(reason, str) and reason.strip() else None,
        status=status,
        completed_at=None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def save_frontend_analytics_capture(
    db: OrmSession,
    *,
    event_name: str,
    timestamp: datetime,
    anonymous_id: UUID,
    session_id: UUID,
    user_id: int | None,
    case_id: int | None,
    context: dict[str, Any] | None,
    properties_traits: dict[str, Any],
    properties_event_data: dict[str, Any],
) -> AnalyticsEvent | None:
    """
    Insert into ``analytics_event`` with DB-generated integer PK; upsert ``session``,
    ``identities``, first/last-touch columns, and ``user.traits`` when ``user_id`` is set
    for customer traffic (``role_hint: customer`` or Customer role in the database).

    Client-sent ``site_visit`` events are ignored (``None``). Whenever a **new** session is
    created, the server inserts a synthetic ``site_visit`` 1µs before that session's first
    event (any ``event_code``), including ``page_view`` and server-side flows.

    On ``case_opened``, the full capture payload is stored on ``case.analytics_data`` only
    while that column is still ``NULL`` (first ``case_opened`` wins).

    To avoid obvious retry duplicates, we treat
    ``(session_id, anonymous_id, event_name, timestamp)`` as a natural idempotency key.
    """
    ctx = _enrich_capture_context(context if isinstance(context, dict) else {})
    campaign = _campaign_dict(ctx)

    norm_name = event_name.strip()
    if norm_name == AnalyticsEvents.SITE_VISIT.value:
        return None

    # if user_id is not None:
        # if not _user_is_customer(db, user_id):
        #     raise AnalyticsCaptureValidationError(
        #         "Analytics capture is only stored for users with the Customer role",
        #         status_code=403,
        #     )
        # if case_id is not None and not _verify_customer_owns_case(db, user_id, case_id):
        #     raise AnalyticsCaptureValidationError(
        #         "case_id is not linked to this customer",
        #         status_code=403,
        #     )

    existing = (
        db.query(AnalyticsEvent)
        .filter(
            AnalyticsEvent.event_code == norm_name,
            AnalyticsEvent.session_id == session_id,
            AnalyticsEvent.anonymous_id == anonymous_id,
            AnalyticsEvent.timestamp == (
                timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
            ),
        )
        .first()
    )
    if existing is not None:
        return existing

    ts = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)
    page = ctx.get("page") or {}
    page_url = page.get("url") if isinstance(page, dict) else None
    page_path = page.get("path") if isinstance(page, dict) else None
    page_title = page.get("title") if isinstance(page, dict) else None
    referrer = page.get("referrer") if isinstance(page, dict) else None

    device = ctx.get("device") or {}
    user_agent = device.get("user_agent") if isinstance(device, dict) else None
    parsed_device = parse_session_device_fields(
        user_agent if isinstance(user_agent, str) else None,
        device if isinstance(device, dict) else None,
    )

    props: dict[str, Any] = {
        "traits": properties_traits,
        "event_data": properties_event_data,
    }
    if ctx.get("library") is not None:
        props["library"] = ctx["library"]
    if ctx.get("device") is not None:
        props["device"] = ctx["device"]

    sess_existing = db.get(AnalyticsSession, session_id)

    sess = sess_existing
    if sess is None:
        entry = _entry_page_from_context(ctx)
        site_ts = ts - timedelta(microseconds=1)
        sess = AnalyticsSession(
            id=session_id,
            anonymous_id=anonymous_id,
            user_id=user_id,
            started_at=site_ts,
            last_event_at=ts,
            entry_page=entry,
            exit_page=(
                page_path
                if norm_name == AnalyticsEvents.PAGE_VIEW.value and page_path
                else None
            ),
            source=campaign.get("source"),
            medium=campaign.get("medium"),
            campaign=campaign.get("campaign"),
            term=campaign.get("term"),
            content=campaign.get("content"),
            gclid=campaign.get("gclid"),
            referrer=(page.get("referrer") if isinstance(page, dict) else None),
            user_agent=user_agent if isinstance(user_agent, str) else None,
            device_type=parsed_device.get("device_type"),
            browser=parsed_device.get("browser"),
            client_os=parsed_device.get("client_os"),
            country=parsed_device.get("country"),
            locale=parsed_device.get("locale"),
            client_timezone=parsed_device.get("timezone"),
            event_count=0,
            is_bot=bool(parsed_device.get("is_bot")),
        )
        db.add(sess)
        db.flush()
        _insert_system_site_visit(
            db,
            sess=sess,
            anonymous_id=anonymous_id,
            user_id=user_id,
            case_id=case_id,
            anchor_ts=ts,
            page_url=page_url if isinstance(page_url, str) else None,
            page_path=page_path if isinstance(page_path, str) else None,
            page_title=page_title if isinstance(page_title, str) else None,
            referrer=referrer if isinstance(referrer, str) else None,
            properties=props,
        )
    else:
        if sess.anonymous_id != anonymous_id:
            raise AnalyticsCaptureValidationError(
                "session_id does not match anonymous_id for this session",
                status_code=400,
            )
        if sess.user_id is None and user_id is not None:
            sess.user_id = user_id
        apply_parsed_device_to_session(sess, parsed_device)
        if not sess.user_agent and isinstance(user_agent, str) and user_agent.strip():
            sess.user_agent = user_agent.strip()[:2048]

    ev = AnalyticsEvent(
        event_code=norm_name,
        anonymous_id=anonymous_id,
        session_id=session_id,
        user_id=user_id,
        case_id=case_id,
        timestamp=ts,
        page_url=page_url if isinstance(page_url, str) else None,
        page_path=page_path if isinstance(page_path, str) else None,
        page_title=page_title if isinstance(page_title, str) else None,
        referrer=referrer if isinstance(referrer, str) else None,
        properties=props,
    )
    db.add(ev)
    db.flush()

    if norm_name == AnalyticsEvents.CASE_OPENED.value:
        _apply_case_opened_analytics_data(
            db,
            case_id,
            _build_case_analytics_capture_payload(
                event_name=norm_name,
                timestamp=ts,
                anonymous_id=anonymous_id,
                session_id=session_id,
                user_id=user_id,
                case_id=case_id,
                sess=sess,
                campaign=campaign,
                context=ctx,
                properties_traits=properties_traits,
                properties_event_data=properties_event_data,
            ),
        )

    sess.event_count = (sess.event_count or 0) + 1
    if ts > sess.last_event_at:
        sess.last_event_at = ts
    if norm_name == AnalyticsEvents.PAGE_VIEW.value and page_path:
        sess.exit_page = page_path
    if _session_is_exit(norm_name, properties_event_data):
        sess.ended_at = ts

    if user_id is not None:
        ident = (
            db.query(Identity)
            .filter(
                Identity.anonymous_id == anonymous_id,
                Identity.user_id == user_id,
            )
            .first()
        )
        if ident is None:
            db.add(
                Identity(
                    anonymous_id=anonymous_id,
                    user_id=user_id,
                    first_seen_at=ts,
                    last_seen_at=ts,
                )
            )
        else:
            ident.last_seen_at = ts

        _maybe_apply_customer_user_attribution(
            db,
            user_id=user_id,
            sess=sess,
            campaign=campaign,
            ts=ts,
            properties_traits=properties_traits,
        )

    if _traits_role_hint_customer(properties_traits):
        if user_id is not None or case_id is not None:
            _apply_customer_id_backfill(
                db,
                session_id=session_id,
                anonymous_id=anonymous_id,
                user_id=user_id,
                case_id=case_id,
            )

    db.commit()
    db.refresh(ev)
    return ev
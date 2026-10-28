"""Service for engage feedback operations."""

from datetime import datetime, time

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.db.models.engage_feedback import EngageFeedback


def create_engage_feedback(db: Session, data: dict) -> EngageFeedback:
    """Create an engage feedback record. Returns the created model."""
    feedback = EngageFeedback(**data)
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_engage_feedback(
    db: Session,
    page: int | None = None,
    limit: int | None = None,
    order_by: str = "created_at",
    order_dir: str = "desc",
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    paginate: bool = False,
) -> list[EngageFeedback] | tuple[list[EngageFeedback], int]:
    """
    Fetch engage feedback with optional pagination and date filtering.
    Used for both list (paginated + count) and export (optional limit, no count).

    Returns:
      - If paginate=True: (list[EngageFeedback], total_count)
      - If paginate=False: list[EngageFeedback]
    """
    query = db.query(EngageFeedback)

    if start_date is not None:
        query = query.filter(EngageFeedback.created_at >= start_date)
    if end_date is not None:
        query = query.filter(EngageFeedback.created_at <= end_date)

    order_column = getattr(EngageFeedback, order_by, EngageFeedback.created_at)
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

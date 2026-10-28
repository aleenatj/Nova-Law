"""
Audit Log Service - query functions for audit log entries.
"""

from datetime import datetime

from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from app.db.models.audit_log import AuditLog
from app.db.models.user import User
from app.enums.audit import AuditActionEnum


def search_audit_logs(
    db: Session,
    audit_log_id: int | None = None,
    table_name: str | None = None,
    record_id: int | None = None,
    user_id: int | None = None,
    action: AuditActionEnum | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = 1,
    limit: int = 10,
    order_by: str = "id",
    order_dir: str = "desc",
) -> tuple[list[tuple[AuditLog, str | None]], int]:
    """
    Search audit logs with optional filters and return total count.
    
    Args:
        db: Database session
        audit_log_id: Filter by specific audit log ID
        table_name: Filter by table name (exact match)
        record_id: Filter by record ID
        user_id: Filter by user ID
        action: Filter by action type
        start_date: Filter logs from this date
        end_date: Filter logs up to this date
        page: Page number (1-indexed)
        limit: Number of records per page
        order_by: Field to order by (id, table_name)
        order_dir: Sort direction (asc, desc)
        
    Returns:
        Tuple of (list of (AuditLog, user_name) tuples, total count)
    """
    # Query audit logs with LEFT JOIN to User table to get user names
    query = db.query(
        AuditLog,
        (User.first_name + " " + User.last_name).label("user_name")
    ).outerjoin(User, AuditLog.user_id == User.id)

    # Apply filters
    if audit_log_id:
        query = query.filter(AuditLog.id == audit_log_id)
    if table_name:
        query = query.filter(AuditLog.table_name == table_name)
    if record_id:
        query = query.filter(AuditLog.record_id == record_id)
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)
    
    total_count = query.count()

    # Apply ordering
    order_column_map = {
        "id": AuditLog.id,
        "table_name": AuditLog.table_name,
        "timestamp": AuditLog.timestamp,
    }
    order_column = order_column_map.get(order_by, AuditLog.id)
    
    if order_dir.lower() == "asc":
        query = query.order_by(asc(order_column))
    else:
        query = query.order_by(desc(order_column))

    # Apply pagination
    offset = (page - 1) * limit
    results = query.offset(offset).limit(limit).all()

    return results, total_count
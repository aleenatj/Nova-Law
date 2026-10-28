"""
Audit Log System with SQLAlchemy Event Listeners.

This module provides automatic audit logging for database changes using SQLAlchemy events.
It captures CREATE, UPDATE, and DELETE operations on configured models.

Usage:
    1. The audit system is automatically initialized when importing this module
    2. Use the middleware to capture user context from requests
    3. Configure which models to audit via AUDITABLE_TABLES or __audit_enabled__ attribute

Configuration:
    - AUDITABLE_TABLES: Set of table names to audit
    - EXCLUDED_FIELDS: Set of field names to exclude from audit logging
    - Model-level: Set __audit_enabled__ = True on model class
    - Model-level: Set __audit_exclude_fields__ = ['field1', 'field2'] to exclude specific fields
"""

import contextvars
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import event, inspect
from sqlalchemy.orm import Session, attributes

from app.db.database import Base, SessionLocal
from app.enums.audit import AuditActionEnum

logger = structlog.get_logger()


# Context variable to store audit context (user info, request metadata)
_audit_context: contextvars.ContextVar["AuditContext | None"] = contextvars.ContextVar(
    "audit_context", default=None
)


@dataclass
class AuditContext:
    """Context for audit logging containing user and request metadata."""
    
    user_id: int | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    metadata: dict[str, Any] | None = None


def set_audit_context(
    user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> contextvars.Token[AuditContext | None]:
    """
    Set the audit context for the current async context.
    
    Args:
        user_id: ID of the user making the change
        ip_address: IP address of the request
        user_agent: User agent string from the request
        metadata: Additional metadata to include in audit log
    
    Returns:
        Token that can be used to reset the context
    """
    context = AuditContext(
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent,
        metadata=metadata,
    )
    return _audit_context.set(context)


def get_audit_context() -> AuditContext | None:
    """Get the current audit context."""
    return _audit_context.get()


def clear_audit_context(token: contextvars.Token[AuditContext | None] | None = None) -> None:
    """
    Clear the audit context.
    
    Args:
        token: Optional token from set_audit_context to reset to previous value
    """
    if token is not None:
        _audit_context.reset(token)
    else:
        _audit_context.set(None)


# Tables that should be audited (by table name)
# Add table names here to enable auditing for those tables
AUDITABLE_TABLES: set[str] = {
    "case",
    "user",
    "customer",
    "lawyer",
    "lawyer_onboarding",
    "law_firm",
    "payment",
    "invoice",
    "match",
    "resolve",
    # "timeline_event",
    "case_lawyer",
    "case_customer",
    "transaction",
}

# Fields to exclude from audit logging (global)
EXCLUDED_FIELDS: set[str] = {
    "password",  # Never log passwords
    "reset_token_timestamp",  # Token-related
    "questions_answered",  # Question answers are not audited
}

# Fields that don't require audit logging when they're the only changes
LOW_VALUE_FIELDS: set[str] = {
    "updated_at",  # Timestamp automatically updated
    "created_at",  # Timestamp automatically set
}

# Configuration flag for saving full model snapshot vs only changed fields
# True = Save complete model state in old_values and new_values
# False = Save only the changed fields (default, more efficient)
SAVE_FULL_SNAPSHOT: bool = False


def _should_audit_model(mapper: Any) -> bool:
    """
    Determine if a model should be audited.
    
    Checks:
    1. Model has __audit_enabled__ = True
    2. Or table name is in AUDITABLE_TABLES
    """
    model_class = mapper.class_
    
    # Check model-level attribute first
    if hasattr(model_class, "__audit_enabled__"):
        return bool(model_class.__audit_enabled__)
    
    # Fall back to table name check
    return model_class.__tablename__ in AUDITABLE_TABLES


def _get_excluded_fields(mapper: Any) -> set[str]:
    """Get fields to exclude for a specific model."""
    model_class = mapper.class_
    excluded = EXCLUDED_FIELDS.copy()
    
    # Add model-specific exclusions
    if hasattr(model_class, "__audit_exclude_fields__"):
        excluded.update(model_class.__audit_exclude_fields__)
    
    return excluded


def _serialize_value(value: Any) -> Any:
    """
    Serialize a value for JSON storage.
    
    Handles common types that need special serialization.
    """
    if value is None:
        return None
    # Handle datetime first (before date, since datetime is subclass of date)
    if isinstance(value, datetime):
        return value.isoformat()
    # Handle date (e.g., Case.start_date)
    if isinstance(value, date):
        return value.isoformat()
    # Handle Decimal (for money/float fields)
    if isinstance(value, Decimal):
        return float(value)
    # Handle UUID
    if isinstance(value, UUID):
        return str(value)
    # Handle bytes
    if isinstance(value, bytes):
        return "<binary data>"
    # Handle Enums
    if hasattr(value, "value"):
        return value.value
    # Handle complex objects
    if hasattr(value, "__dict__") and not isinstance(value, (str, int, float, bool, list, dict)):
        return f"<{type(value).__name__}>"
    return value


def _get_model_state(target: Any, excluded_fields: set[str]) -> dict[str, Any]:
    """
    Get the current state of a model as a dictionary.
    
    Args:
        target: The SQLAlchemy model instance
        excluded_fields: Fields to exclude from the state
    
    Returns:
        Dictionary of field names to values
    """
    state = {}
    mapper = inspect(target.__class__)
    
    for column in mapper.columns:
        key = column.key
        if key in excluded_fields:
            continue
        
        try:
            value = getattr(target, key, None)
            state[key] = _serialize_value(value)
        except Exception:
            # Skip fields that can't be accessed
            pass
    
    return state


def _get_changed_fields(
    target: Any,
    excluded_fields: set[str],
) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """
    Get the old and new values for changed fields.
    
    If SAVE_FULL_SNAPSHOT is True, returns full model state.
    If SAVE_FULL_SNAPSHOT is False, returns only changed fields.
    
    Args:
        target: The SQLAlchemy model instance
        excluded_fields: Fields to exclude from tracking
    
    Returns:
        Tuple of (old_values, new_values, changed_field_names)
    """
    old_values = {}
    new_values = {}
    changed_fields = []
    
    mapper = inspect(target.__class__)
    
    for column in mapper.columns:
        key = column.key
        if key in excluded_fields:
            continue
        
        try:
            history = attributes.get_history(target, key)
            current_value = getattr(target, key, None)
            serialized_current = _serialize_value(current_value)
            
            if history.has_changes():
                # Changed field
                old_val = history.deleted[0] if history.deleted else None

                changed_fields.append(key)
                old_values[key] = _serialize_value(old_val)
                new_values[key] = serialized_current

            elif SAVE_FULL_SNAPSHOT:
                # Unchanged field included only in full snapshot mode
                old_values[key] = serialized_current
                new_values[key] = serialized_current
        except Exception:
            pass
    
    return old_values, new_values, changed_fields

def _create_audit_entry_orm(
    table_name: str,
    record_id: int,
    action: AuditActionEnum,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    changed_fields: list[str] | None = None,
) -> None:
    """
    Create an audit log entry using ORM (for use outside of event listeners).
    
    This method creates a new session to avoid transaction conflicts.
    """
    from app.db.models.audit_log import AuditLog
    
    # Skip if this is the audit_log table itself
    if table_name == "audit_log":
        return
    
    context = get_audit_context()
    
    db = SessionLocal()
    try:
        audit_entry = AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            user_id=context.user_id if context else None,
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            ip_address=context.ip_address if context else None,
            user_agent=context.user_agent if context else None,
            extra_metadata=context.metadata if context else None,
        )
        db.add(audit_entry)
        db.commit()
    except Exception as e:
        logger.error("Failed to create audit log entry", error=str(e))
        db.rollback()
    finally:
        db.close()


# Store pending audit entries during flush
_pending_audit_entries: contextvars.ContextVar[list[dict[str, Any]]] = contextvars.ContextVar(
    "pending_audit_entries", default=[]
)


@event.listens_for(Session, "after_flush")
def receive_after_flush(session: Session, flush_context: Any) -> None:
    """
    Handle audit logging after SQLAlchemy flush.
    
    This captures all new, dirty, and deleted objects in the session.
    """
    pending = []
    
    # Process new objects (CREATE) - Commented out: CREATE audit logs not needed currently
    # for obj in session.new:
    #     mapper = inspect(obj.__class__)
    #     if not _should_audit_model(mapper):
    #         continue
    #     
    #     excluded = _get_excluded_fields(mapper)
    #     state = _get_model_state(obj, excluded)
    #     
    #     # Get the primary key
    #     record_id = getattr(obj, "id", None)
    #     if record_id is None:
    #         continue
    #     
    #     pending.append({
    #         "table_name": obj.__tablename__,
    #         "record_id": record_id,
    #         "action": AuditActionEnum.CREATE,
    #         "new_values": state,
    #     })
    
    # Process dirty objects (UPDATE)
    for obj in session.dirty:
        if not session.is_modified(obj):
            continue
        
        mapper = inspect(obj.__class__)
        if not _should_audit_model(mapper):
            continue
        
        excluded = _get_excluded_fields(mapper)
        old_values, new_values, changed_fields = _get_changed_fields(obj, excluded)
        
        # Skip if only low-value fields changed
        significant_changes = [f for f in changed_fields if f not in LOW_VALUE_FIELDS]
        if not significant_changes:
            continue
        
        record_id = getattr(obj, "id", None)
        if record_id is None:
            continue
        
        pending.append({
            "table_name": obj.__tablename__,
            "record_id": record_id,
            "action": AuditActionEnum.UPDATE,
            "old_values": old_values,
            "new_values": new_values,
            "changed_fields": changed_fields,
        })
    
    # Process deleted objects (DELETE)
    for obj in session.deleted:
        mapper = inspect(obj.__class__)
        if not _should_audit_model(mapper):
            continue
        
        excluded = _get_excluded_fields(mapper)
        state = _get_model_state(obj, excluded)
        
        record_id = getattr(obj, "id", None)
        if record_id is None:
            continue
        
        pending.append({
            "table_name": obj.__tablename__,
            "record_id": record_id,
            "action": AuditActionEnum.DELETE,
            "old_values": state,
        })
    
    # Store pending entries for after_commit
    current = _pending_audit_entries.get()
    _pending_audit_entries.set(current + pending)


@event.listens_for(Session, "after_commit")
def receive_after_commit(session: Session) -> None:
    """
    Write audit entries after successful commit.
    
    This ensures audit entries are only created for changes that were actually committed.
    """
    pending = _pending_audit_entries.get()
    if not pending:
        return
    
    # Clear pending entries
    _pending_audit_entries.set([])
    
    # Write audit entries in a separate session
    for entry in pending:
        try:
            _create_audit_entry_orm(
                table_name=entry["table_name"],
                record_id=entry["record_id"],
                action=entry["action"],
                old_values=entry.get("old_values"),
                new_values=entry.get("new_values"),
                changed_fields=entry.get("changed_fields"),
            )
        except Exception as e:
            logger.error(
                "Failed to write audit entry",
                table_name=entry["table_name"],
                record_id=entry["record_id"],
                error=str(e),
            )


@event.listens_for(Session, "after_rollback")
def receive_after_rollback(session: Session) -> None:
    """Clear pending audit entries on rollback."""
    _pending_audit_entries.set([])


def manual_audit_log(
    table_name: str,
    record_id: int,
    action: AuditActionEnum,
    old_values: dict[str, Any] | None = None,
    new_values: dict[str, Any] | None = None,
    changed_fields: list[str] | None = None,
    user_id: int | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """
    Manually create an audit log entry.
    
    Use this for custom business operations that need explicit audit logging.
    
    Args:
        table_name: Name of the table/entity being audited
        record_id: ID of the record being changed
        action: The type of action
        old_values: Values before the change
        new_values: Values after the change
        changed_fields: List of field names that changed
        user_id: Override user ID (uses context if not provided)
        ip_address: Override IP address (uses context if not provided)
        user_agent: Override user agent (uses context if not provided)
        metadata: Additional metadata to include
    """
    from app.db.models.audit_log import AuditLog
    
    context = get_audit_context()
    
    db = SessionLocal()
    try:
        audit_entry = AuditLog(
            table_name=table_name,
            record_id=record_id,
            action=action,
            user_id=user_id or (context.user_id if context else None),
            old_values=old_values,
            new_values=new_values,
            changed_fields=changed_fields,
            ip_address=ip_address or (context.ip_address if context else None),
            user_agent=user_agent or (context.user_agent if context else None),
            extra_metadata=metadata or (context.metadata if context else None),
        )
        db.add(audit_entry)
        db.commit()
    except Exception as e:
        logger.error("Failed to create manual audit log entry", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()


# Decorator for manual audit logging
def audit_log_decorator(
    action: str = "CUSTOM",
    table_name: str | None = None,
):
    """
    Decorator for explicit audit logging on functions.
    
    Usage:
        @audit_log_decorator(action="CUSTOM_ACTION", table_name="case")
        def custom_business_logic(case_id: int, **kwargs):
            # Business logic here
            pass
    """
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Try to extract record_id from kwargs or result
            record_id = kwargs.get("id") or kwargs.get("record_id")
            if record_id is None and hasattr(result, "id"):
                record_id = result.id
            
            if record_id is not None:
                try:
                    manual_audit_log(
                        table_name=table_name or func.__name__,
                        record_id=record_id,
                        action=AuditActionEnum(action) if action in AuditActionEnum.__members__ else AuditActionEnum.UPDATE,
                        metadata={"function": func.__name__, "custom_action": action},
                    )
                except Exception as e:
                    logger.warning(
                        "Decorator audit log failed",
                        function=func.__name__,
                        error=str(e),
                    )
            
            return result
        
        return wrapper
    
    return decorator


# Initialize audit logging (call this on app startup if needed)
def init_audit_logging() -> None:
    """
    Initialize the audit logging system.
    
    This is called automatically when the module is imported,
    but can be called explicitly if needed.
    """
    logger.info("Audit logging system initialized")


# Auto-initialize on import
init_audit_logging()


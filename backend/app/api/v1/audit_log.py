"""Audit log API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.models import User
from app.db.services.audit_log import search_audit_logs
from app.schemas.v1.audit_log import (
    AuditLogItem,
    AuditLogSearchData,
    AuditLogSearchRequest,
    AuditLogSearchResponse,
)
from app.schemas.v1.base import ResponseMessage
from app.utils.dependencies import get_db
from app.utils.validators import validate_order_params
from app.utils.encryption import decrypt_id, encrypt_id

logger = logging.getLogger(__name__)

router = APIRouter()

def encrypt_ids_in_dict(data: dict | None) -> dict | None:
    """
    Encrypt all ID fields in a dictionary.
    
    Encrypts fields that are named 'id' or end with '_id' and have integer values.
    """
    if data is None:
        return None
    
    encrypted_data = {}
    for key, value in data.items():
        # Check if the key is 'id' or ends with '_id' and value is an integer
        if (key == "id" or key.endswith("_id")) and isinstance(value, int):
            encrypted_value = encrypt_id(str(value))
            encrypted_data[key] = encrypted_value if encrypted_value else value
        else:
            encrypted_data[key] = value
    
    return encrypted_data


@router.get("/audit-log", response_model=AuditLogSearchResponse)
async def search_audit_logs_endpoint(
    search_request: AuditLogSearchRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AuditLogSearchResponse:
    """
    Search audit logs with filtering and pagination.
    """
    try:
        # Validate order_by and order_dir parameters
        allowed_order_fields = {
            "id",
            "table_name",
            "timestamp",
        }
        validate_order_params(
            search_request.order_by,
            search_request.order_dir,
            allowed_order_fields
        )
        
        # Decrypt and convert optional ID filters to integers
        audit_log_id = None
        if search_request.id:
            decrypted = decrypt_id(search_request.id)
            if not decrypted:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid audit log ID")
            audit_log_id = int(decrypted)
  
        record_id = None
        if search_request.record_id:
            decrypted = decrypt_id(search_request.record_id)
            if not decrypted:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid record ID")
            record_id = int(decrypted)

        user_id = None
        if search_request.user_id:
            decrypted = decrypt_id(search_request.user_id)
            if not decrypted:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID")
            user_id = int(decrypted)

        # Search for audit logs with count
        audit_logs, total_count = search_audit_logs(
            db=db,
            audit_log_id=audit_log_id,
            table_name=search_request.table_name,
            record_id=record_id,
            user_id=user_id,
            action=search_request.action,
            start_date=search_request.start_date,
            end_date=search_request.end_date,
            page=search_request.page,
            limit=search_request.limit,
            order_by=search_request.order_by,
            order_dir=search_request.order_dir,
        )

        # Convert audit logs to response format
        audit_log_items = []
        for audit_log, user_name in audit_logs:
            try:
                # Encrypt IDs in old_values and new_values before returning
                encrypted_old_values = encrypt_ids_in_dict(audit_log.old_values)
                encrypted_new_values = encrypt_ids_in_dict(audit_log.new_values)
                
                audit_log_data = {
                    "id": audit_log.id,
                    "table_name": audit_log.table_name,
                    "record_id": audit_log.record_id,
                    "action": audit_log.action.value if audit_log.action else None,
                    "user_id": audit_log.user_id,
                    "user_name": user_name,
                    "old_values": encrypted_old_values,
                    "new_values": encrypted_new_values,
                    "changed_fields": audit_log.changed_fields,
                    "timestamp": audit_log.timestamp,
                    "ip_address": audit_log.ip_address,
                    "user_agent": audit_log.user_agent,
                    "extra_metadata": audit_log.extra_metadata,
                }

                audit_log_item = AuditLogItem.model_validate(audit_log_data)
                audit_log_items.append(audit_log_item)

            except Exception as e:
                logger.error(
                    f"Failed to create search item for audit log {audit_log.id}: {e}",
                    exc_info=True
                )
                # Continue with other items instead of failing completely
                continue

        # Create search data with pagination metadata
        search_data = AuditLogSearchData(
            total_count=total_count,
            records_in_page=len(audit_log_items),
            audit_logs=audit_log_items,
        )

        if search_data.total_count == 0:
            message = "No audit logs found"
        else:
            message = f"Found {search_data.total_count} audit log(s)"

        return AuditLogSearchResponse(
            success=True,
            message=[ResponseMessage(success=True, message=message)],
            data=search_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to search audit logs", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search audit logs",
        ) from e


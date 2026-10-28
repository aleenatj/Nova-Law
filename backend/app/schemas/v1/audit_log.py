"""Audit log schemas for API endpoints."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.enums.audit import AuditActionEnum

from .base import BaseRequest, BaseResponse, EncryptedResponse


class AuditLogSearchRequest(BaseRequest):
    """Schema for audit log search request with filtering options."""

    id: str | None = Field(
        None,
        description="Filter by audit log ID",
    )
    table_name: str | None = Field(
        None,
        max_length=100,
        description="Filter by table name (exact match)",
    )
    record_id: str | None = Field(
        None,
        description="Filter by record ID",
    )
    user_id: str | None = Field(
        None,
        description="Filter by user ID who made the change",
    )
    action: AuditActionEnum | None = Field(
        None,
        description="Filter by action type (CREATE, UPDATE, DELETE)",
    )
    start_date: datetime | None = Field(
        None,
        description="Filter logs from this date onwards",
    )
    end_date: datetime | None = Field(
        None,
        description="Filter logs up to this date",
    )


class AuditLogItem(EncryptedResponse):
    """Schema for individual audit log item in response."""

    id: str = Field(..., description="Audit log ID")
    table_name: str = Field(..., description="Name of the table that was changed")
    record_id: str = Field(..., description="ID of the record that was changed")
    action: str | None = Field(None, description="Action performed (CREATE, UPDATE, DELETE)")
    user_id: str | None = Field(None, description="ID of the user who made the change")
    user_name: str | None = Field(None, description="Name of the user who made the change")
    old_values: dict | None = Field(None, description="Previous values before the change")
    new_values: dict | None = Field(None, description="New values after the change")
    changed_fields: list[str] | None = Field(None, description="List of field names that were changed")
    timestamp: datetime | None = Field(None, description="When the change occurred")
    ip_address: str | None = Field(None, description="IP address of the request")
    user_agent: str | None = Field(None, description="User agent of the request")
    extra_metadata: dict | None = Field(None, description="Additional metadata")

    model_config = ConfigDict(from_attributes=True)


class AuditLogSearchData(BaseModel):
    """Schema for audit log search data with pagination metadata."""

    total_count: int = Field(..., description="Total number of matching audit logs")
    records_in_page: int = Field(
        ..., description="Number of records in the current page"
    )
    audit_logs: list[AuditLogItem] = Field(..., description="List of audit logs")


class AuditLogSearchResponse(BaseResponse):
    """Schema for audit log search response."""

    data: AuditLogSearchData = Field(
        ..., description="Audit log search data with pagination"
    )


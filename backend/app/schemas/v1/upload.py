"""Upload schemas for file upload operations."""

from pydantic import BaseModel, Field

from app.enums.file_upload import EntityType
from app.schemas.v1.base import BaseResponse


class UploadUrlRequest(BaseModel):
    """Request schema for generating upload URL."""

    extension: str = Field(..., description="File extension (optional)")
    entity_type: EntityType = Field(..., description="Type of entity for which the file is being uploaded")


class UploadUrlResponseData(BaseModel):
    """Response data for upload URL generation."""

    upload_url: str = Field(..., description="Pre-signed S3 upload URL")
    file_key: str = Field(..., description="S3 key for the uploaded file")
    expires_in: int = Field(..., description="URL expiration time in seconds")


class UploadUrlResponse(BaseResponse):
    """Response schema for upload URL generation."""

    data: UploadUrlResponseData


"""Upload API endpoints for file upload operations."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import get_current_user_if_provided
from app.db.models import User
from app.enums.file_upload import ENTITY_TYPE_ALLOWED_EXTENSIONS, ENTITY_TYPE_PERMISSIONS, EntityType
from app.enums.user_role import UserRoleEnum
from app.schemas.v1.base import ResponseMessage
from app.schemas.v1.upload import (
    UploadUrlRequest,
    UploadUrlResponse,
    UploadUrlResponseData,
)
from app.services.upload_service import UploadService

logger = logging.getLogger(__name__)

router = APIRouter()


def _raise_upload_error() -> None:
    """Raise HTTP exception for upload error."""
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=[{"message": "Failed to generate upload URL"}]
    )


def _check_entity_upload_permission(entity_type: EntityType, user_role: str) -> None:
    """
    Check if the user has permission to upload files for the given entity type.

    Args:
        entity_type: The type of entity being uploaded
        user_role: The role of the current user

    Raises:
        HTTPException: If the user doesn't have permission
    """
    # Get allowed roles for this entity type
    allowed_roles = ENTITY_TYPE_PERMISSIONS.get(entity_type)

    if not allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"message": f"Entity type '{entity_type}' is not supported for uploads."}]
        )

    if user_role not in [role.value for role in allowed_roles]:
        role_names = [role.value for role in allowed_roles]
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=[{"message": f"Access denied. Only {', '.join(role_names)} can upload {entity_type} files."}]
        )


@router.get("/get-file-upload-token", response_model=UploadUrlResponse)
async def get_file_upload_token(
    request: UploadUrlRequest = Depends(),
    current_user: User | None = Depends(get_current_user_if_provided),
) -> UploadUrlResponse:
    """
    Generate a pre-signed S3 URL for file upload.

    This endpoint generates a temporary pre-signed URL that allows the frontend
    to upload files directly to S3 without going through the backend.
    """
    try:
        # Check permissions for the entity type
        if request.entity_type != EntityType.B2C_EXPERT_PROFILE:
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=[{"message": "Unauthorized: Please login to upload files."}]
                )
            _check_entity_upload_permission(request.entity_type, UserRoleEnum.from_id(current_user.user_roles[0].role_id).display_name)
        elif request.entity_type == EntityType.B2C_EXPERT_PROFILE:
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=[{"message": "Access denied: A valid entity type is required."}]
            )

        if request.extension not in ENTITY_TYPE_ALLOWED_EXTENSIONS[request.entity_type]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=[{"message": f"File extension '{request.extension}' is not allowed for entity type '{request.entity_type.value}'."}]
            )
        # Initialize upload service
        upload_service = UploadService()

        # Generate pre-signed upload URL
        upload_data = upload_service.generate_presigned_upload_url(
            extension=request.extension
        )

        if not upload_data:
            _raise_upload_error()

        # At this point, upload_data is guaranteed to be not None
        assert upload_data is not None

        # Create response data
        response_data = UploadUrlResponseData(
            upload_url=upload_data["upload_url"],
            file_key=upload_data["file_key"],
            expires_in=int(upload_data["expires_in"])
        )

        return UploadUrlResponse(
            success=True,
            message=[
                ResponseMessage(
                    success=True,
                    message="Upload URL generated successfully"
                )
            ],
            data=response_data
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error generating upload URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[{"message": "Internal server error"}]
        ) from e

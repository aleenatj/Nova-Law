"""User API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.models import User
from app.db.services.user import (
    change_user_password,
    get_current_user,
    update_user_profile,
)
from app.schemas.v1.base import ResponseMessage
from app.schemas.v1.user import (
    PasswordChangeRequest,
    PasswordChangeResponse,
    UserProfileData,
    UserProfileResponse,
    UserProfileUpdateRequest,
    UserProfileUpdateResponse,
)
from app.utils.dependencies import get_db
from app.utils.photo_utils import generate_photo_urls
from app.enums.user_role import UserRoleEnum

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/user/me", response_model=UserProfileResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserProfileResponse:
    """Get current user profile."""
    try:
        # Get the user from database to ensure we have the latest data
        # user = get_current_user(db, int(current_user.id))
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )

        # Get user verification data (includes lawyer and customer info)
        # data = verify_user(user)

        # Extract lawyer and customer IDs and photo URLs
        photo_urls = None
        if current_user.lawyer:
            lawyer_id = current_user.lawyer.id
            photo_urls = generate_photo_urls(current_user.lawyer.photo_url)
        else:
            lawyer_id = None

        if current_user.customer:
            customer_id = current_user.customer.id
        else:
            customer_id = None

        # Get user roles
        role_ids = [user_role.role_id for user_role in current_user.user_roles]
        if len(role_ids) == 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"success": False, "message": "User has no role assigned. Please contact support."}
            )
        role_codes = [UserRoleEnum.from_id(role_id).display_name for role_id in role_ids]
        # Get user role information
        # role_code, role_name = get_user_role_info(db, int(user.id))
        role_code = role_codes[0]
        role_name = role_codes[0]

        # Create the user profile data with encrypted ID
        user_data = UserProfileData(
            id=str(current_user.id),
            first_name=current_user.first_name,  # type: ignore
            last_name=current_user.last_name,  # type: ignore
            email=current_user.email,  # type: ignore
            phone=current_user.phone,  # type: ignore
            gender=current_user.gender.value if current_user.gender else None,
            status=current_user.status.value if hasattr(current_user.status, "value") else str(current_user.status),
            created_at=current_user.created_at,  # type: ignore
            updated_at=current_user.updated_at,  # type: ignore
            role_code=role_code,
            lawyer_id=lawyer_id,
            customer_id=customer_id,
            photo_urls=photo_urls if photo_urls else None,
            gender_other=current_user.gender_other if current_user.gender_other else None,
            available_roles=role_codes,
        )

        # Return the response in BaseResponse format
        return UserProfileResponse(
            success=True,
            message=[
                ResponseMessage(success=True, message="User profile retrieved successfully")
            ],
            data=user_data,
        )
    except Exception as e:
        logger.exception(f"Error in get user profile: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=[{"success": False, "message": "Failed to get current user profile"}]) from e


@router.put("/user/change-password", response_model=PasswordChangeResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> PasswordChangeResponse:
    """Change user password."""
    try:
        # Validate that new password is different from current password
        if password_data.current_password == password_data.new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be different from current password",
            )

        # Attempt to change the password directly using current_user
        success = change_user_password(
            db=db,
            user_id=int(current_user.id),
            current_password=password_data.current_password,
            new_password=password_data.new_password,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid current password or user not found",
            )

        # Return success response
        return PasswordChangeResponse(
            success=True,
            message=[
                ResponseMessage(success=True, message="Password changed successfully")
            ],
            data=[],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in change password: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=[{"success": False, "message": "Failed to change password"}]) from e


@router.put("/user/profile", response_model=UserProfileUpdateResponse)
async def update_profile(
    profile_data: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserProfileUpdateResponse:
    """Update user profile."""
    try:
        # Get user_id from current_user
        user_id = int(current_user.id)

        # Update user profile
        updated_user = update_user_profile(db, user_id, profile_data)

        if not updated_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=[{"success": False, "message": "User not found"}],
            )

        # Return the response
        return UserProfileUpdateResponse(
            success=True,
            message=[
                ResponseMessage(success=True, message="User profile updated successfully")
            ],
            data=[],
        )
    except ValueError as e:
        logger.exception(f"Validation error in update profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=[{"success": False, "message": str(e)}],
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in update profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=[{"success": False, "message": "Failed to update user profile1"}],
        ) from e

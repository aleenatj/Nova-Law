"""Navigator API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.models import User
from app.db.services.navigator import (
    create_nova_navigator_user,
    get_navigator_by_id,
    search_navigators,
    update_nova_navigator_user,
)
from app.enums.events import EventType
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.base import ResponseMessage
from app.schemas.v1.event import Event
from app.schemas.v1.navigator import (
    NavigatorDetailsResponse,
    NavigatorSearchData,
    NavigatorSearchItem,
    NavigatorSearchRequest,
    NavigatorSearchResponse,
    NavigatorUpdateRequest,
)
from app.schemas.v1.user import (
    UserCreateRequest,
    UserCreateResponse,
    UserResponse,
    UserUpdateRequest,
    UserUpdateResponse,
)
from app.utils.dependencies import get_db
from app.utils.helpers import extract_status_messages
from app.utils.validators import validate_order_params
from app.enums.user import StatusEnum

logger = logging.getLogger(__name__)

router = APIRouter()


def _raise_navigator_not_found() -> None:
    """Raise HTTPException for navigator not found."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Navigator not found"
    )


def _decrypt_and_validate_user_id(user_id: str) -> int:
    """Decrypt and validate user ID, raising appropriate HTTPException on failure."""
    from app.utils.encryption import decrypt_id

    decrypted_user_id = decrypt_id(user_id)
    if not decrypted_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID"
        )
    return int(decrypted_user_id)


def _create_user_response_data(user: User) -> UserResponse:
    """Create UserResponse data from a User model."""
    return UserResponse(
        id=str(user.id),
        first_name=str(user.first_name),
        last_name=str(user.last_name),
        email=str(user.email),
        phone=str(user.phone) if user.phone else None,
        gender=user.gender.value if user.gender else None,
        gender_other=str(user.gender_other) if user.gender_other else None,
        status=user.status.value if hasattr(user.status, "value") else str(user.status),
        created_at=user.created_at,  # type: ignore
        updated_at=user.updated_at,  # type: ignore
    )


def _create_navigator_search_item(user: User) -> NavigatorSearchItem:
    """Create NavigatorSearchItem data from a User model."""
    return NavigatorSearchItem(
        id=str(user.id),
        first_name=str(user.first_name),
        last_name=str(user.last_name),
        email=str(user.email),
        phone=str(user.phone) if user.phone else None,
        gender=user.gender.value if user.gender else None,
        gender_other=str(user.gender_other) if user.gender_other else None,
        status=user.status.value if hasattr(user.status, "value") else str(user.status),
        needs_password_setup=not (bool(user.password) if user.status == StatusEnum.ACTIVE else True),
        created_at=user.created_at,  # type: ignore
        updated_at=user.updated_at,  # type: ignore
    )


@router.post("/navigator", response_model=UserCreateResponse)
async def create_nova_navigator(
    user_data: UserCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserCreateResponse:
    """Create a new Nova Navigator user."""
    try:
        # Create the user with Navigator role (password will be None)
        new_user, _ = create_nova_navigator_user(db, user_data)

        # Create response data with encrypted ID
        user_response_data = _create_user_response_data(new_user)

        # Prepare success messages
        messages = [
            ResponseMessage(
                success=True, message="Navigator created successfully"
            )
        ]

        # Trigger INITIAL_PASSWORD_LINK_SENT event for newly created navigator
        # Only if user has Active status
        if new_user.status == "Active":
            try:
                event_data = Event(
                    event_type=EventType.INITIAL_PASSWORD_LINK_SENT,
                    payload={
                        "user_id": new_user.id,
                    },
                    user_id=int(current_user.id),
                    current_user=current_user,
                )
                await event_dispatcher.dispatch_event(db, event_data)

                # Extract and append event response messages to API response
                _, event_messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]
                for msg in event_messages:
                    messages.append(ResponseMessage(
                        success=bool(msg["success"]),
                        message=str(msg["message"])
                    ))
            except Exception as event_error:
                logger.warning(f"Failed to send initial password email: {event_error}")
                messages.append(ResponseMessage(
                    success=False,
                    message="Initial password email could not be sent."
                ))

        return UserCreateResponse(
            success=True,
            message=messages,
            data=user_response_data,
        )

    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in create navigator: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create Navigator user",
        ) from None


@router.put("/navigator", response_model=UserUpdateResponse)
async def update_navigator(
    request_data: NavigatorUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> UserUpdateResponse:
    """Update a Nova Navigator user."""
    # Convert decrypted user_id to integer
    user_id_int = int(request_data.user_id)

    # Check if user exists first
    from app.db.services.user import get_user_by_id

    existing_user = get_user_by_id(db, user_id_int)
    if not existing_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    try:
        # Create UserUpdateRequest from the navigator update request (excluding user_id)
        user_update_data = UserUpdateRequest(
            first_name=request_data.first_name,
            last_name=request_data.last_name,
            email=request_data.email,
            phone=request_data.phone,
            gender=request_data.gender,
            gender_other=request_data.gender_other,
            status=request_data.status,
        )

        # Update the user
        updated_user = update_nova_navigator_user(db, user_id_int, user_update_data)
        assert updated_user is not None  # We already verified the user exists

        # Create response data with encrypted ID
        user_response_data = _create_user_response_data(updated_user)

        return UserUpdateResponse(
            success=True,
            message=[
                ResponseMessage(success=True, message="Navigator updated successfully")
            ],
            data=user_response_data,
        )

    except ValueError:
        raise
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in update navigator: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update Navigator",
        ) from None


@router.get("/navigator", response_model=NavigatorSearchResponse)
async def search_navigators_endpoint(
    search_request: NavigatorSearchRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> NavigatorSearchResponse:
    """Search for navigator users with various criteria."""
    try:
            # Validate order_by and order_dir parameters
        allowed_order_fields = {
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "gender",
            "status",
            "created_at",
            "updated_at",
        }
        validate_order_params(search_request.order_by, search_request.order_dir, allowed_order_fields)

        # Search for navigators
        users, total_count = search_navigators(
            db=db,
            search_term=search_request.search_term,
            name=search_request.name,
            email=search_request.email,
            phone=search_request.phone,
            status=search_request.status,
            page=search_request.page,
            limit=search_request.limit,
            order_by=search_request.order_by,
            order_dir=search_request.order_dir,
        )

        # Convert users to response format
        navigator_items = [_create_navigator_search_item(user) for user in users]

        # Create search data with pagination metadata
        search_data = NavigatorSearchData(
            total_count=total_count,
            records_in_page=len(navigator_items),
            users=navigator_items,
        )

        if search_data.total_count == 0:
            message = "No data found"
        else:
            message = f"Found {search_data.total_count} navigator(s)"

        return NavigatorSearchResponse(
            success=True,
            message=[
                ResponseMessage(
                    success=True, message=message
                )
            ],
            data=search_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in search navigators: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search navigators",
        ) from e


@router.get("/navigator/{navigator_id}", response_model=NavigatorDetailsResponse)
async def get_navigator_by_id_endpoint(
    navigator_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> NavigatorDetailsResponse:
    """Get navigator user details by ID."""
    # Decrypt and validate the navigator ID
    decrypted_navigator_id = _decrypt_and_validate_user_id(navigator_id)

    try:
        # Get the navigator by ID
        navigator = get_navigator_by_id(db, decrypted_navigator_id)
        if not navigator:
            _raise_navigator_not_found()

        # Create response data with encrypted ID
        navigator_data = _create_navigator_search_item(navigator)  # type: ignore

        return NavigatorDetailsResponse(
            success=True,
            message=[
                ResponseMessage(
                    success=True, message="Navigator details retrieved successfully"
                )
            ],
            data=navigator_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error in get navigator by id: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve navigator details",
        ) from e

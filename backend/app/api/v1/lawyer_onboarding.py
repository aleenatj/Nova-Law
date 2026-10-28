"""Lawyer onboarding API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import NoReturn

from app.core.security import get_current_active_user
from app.db.database import get_db
from app.db.models import User
from app.db.models.lawyer_onboarding import LawyerOnboarding
from app.db.services.lawyer_onboarding import (
    get_lawyer_onboarding_by_id as get_lawyer_onboarding_by_id_service,
    search_lawyer_onboarding as search_lawyer_onboarding_service,
    update_lawyer_onboarding as update_lawyer_onboarding_service,
)
from app.schemas.v1.base import ResponseMessage
from app.schemas.v1.lawyer_onboarding import (
    LawyerOnboardingCreateRequest,
    LawyerOnboardingCreateResponse,
    LawyerOnboardingDetailsResponse,
    LawyerOnboardingItem,
    LawyerOnboardingSearchData,
    LawyerOnboardingSearchRequest,
    LawyerOnboardingSearchResponse,
    LawyerOnboardingUpdateRequest,
    LawyerOnboardingUpdateResponse,
)
from app.utils.photo_utils import generate_photo_urls
from app.utils.encryption import decrypt_id
from app.events.dispatcher import event_dispatcher
from app.schemas.v1.event import Event
from app.enums.events import EventType
from app.enums.file_upload import EntityType
from app.services.upload_service import validate_temp_file_before_processing
from app.utils.helpers import extract_status_messages

logger = logging.getLogger(__name__)

router = APIRouter()

def _raise_validation_error(detail: list[dict[str, str]]) -> NoReturn:
    """Raise HTTPException for validation errors."""
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)

def _create_onboarding_item(onboarding: LawyerOnboarding) -> LawyerOnboardingItem:
    """Create a LawyerOnboardingItem from a LawyerOnboarding model."""
    return LawyerOnboardingItem(
        id=str(onboarding.id),
        first_name=onboarding.first_name,
        last_name=onboarding.last_name,
        email=onboarding.email,
        phone=onboarding.phone,
        work_status=onboarding.work_status,
        firm_name=onboarding.firm_name,
        city=onboarding.city,
        post_code=onboarding.post_code,
        gender=onboarding.gender,
        photo_url=generate_photo_urls(onboarding.photo_url) if onboarding.photo_url else None,
        professional_status=onboarding.professional_status,
        experience=onboarding.experience,
        service_details=onboarding.service_details,
        matter_types=onboarding.matter_types,
        accredited_specialism_other=onboarding.accredited_specialism_other,
        ncdr_magic=onboarding.ncdr_magic,
        accredited_specialist=onboarding.accredited_specialist,
        regulator=onboarding.regulator,
        ncdr_description=onboarding.ncdr_description,
        compelling_quote=onboarding.compelling_quote,
        remote_consultation=onboarding.remote_consultation,
        consultation_offers=onboarding.consultation_offers,
        status=onboarding.status,
        created_at=onboarding.created_at,
        updated_at=onboarding.updated_at,
    )


def _decrypt_and_validate_onboarding_id(onboarding_id: str) -> int:
    """Decrypt and validate the onboarding ID."""
    decrypted_id = decrypt_id(onboarding_id)
    if not decrypted_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid onboarding ID format",
        )
    try:
        return int(decrypted_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid onboarding ID format",
        )


@router.post(
    "/B2C-experts",
    response_model=LawyerOnboardingCreateResponse,
)
async def create_lawyer_onboarding_endpoint(
    request_data: LawyerOnboardingCreateRequest,
    db: Session = Depends(get_db),
) -> LawyerOnboardingCreateResponse:
    """Create a new lawyer onboarding record."""
    try:
        # Validate temp file existence and size BEFORE lawyer onboarding creation
        validate_temp_file_before_processing(
            photo_url=request_data.photo_url,
            entity_type=EntityType.B2C_EXPERT_PROFILE
        )

        # Prepare all data for the event payload
        event_payload = {
            "request_data": request_data,
        }
        event_data = Event(
            event_type=EventType.CREATE_LEGAL_EXPERT,
            payload=event_payload,
        )
        await event_dispatcher.dispatch_event(db, event_data)
        success, messages = extract_status_messages(event_data.response)  # type: ignore[arg-type]
        if not success:
            _raise_validation_error(messages)

        # Get the response data from the event payload (enriched by the main event handler)
        onboarding_dict = event_data.payload.get("onboarding_dict")

        return LawyerOnboardingCreateResponse(
            success=success,
            message=[{"success": True, "message": "Legal expert onboarded successfully."}],
            data=onboarding_dict,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating Nova expert onboarding record: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create Nova expert onboarding record: {str(e)}",
        )

@router.get(
    "/B2C-experts",
    response_model=LawyerOnboardingSearchResponse,
)
async def search_lawyer_onboarding_endpoint(
    search_request: LawyerOnboardingSearchRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LawyerOnboardingSearchResponse:
    """Search lawyer onboarding records with filters and pagination."""
    try:
        records, total_count = search_lawyer_onboarding_service(db, search_request)

        # Convert records to response format
        items = [_create_onboarding_item(record) for record in records]

        # Create search data with pagination metadata
        search_data = LawyerOnboardingSearchData(
            total_count=total_count,
            records_in_page=len(items),
            lawyers=items,
        )

        if total_count == 0:
            message = "No data found"
        else:
            message = f"Found {total_count} Nova expert onboarding record(s)"

        return LawyerOnboardingSearchResponse(
            success=True,
            message=[ResponseMessage(success=True, message=message)],
            data=search_data,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error searching Nova expert onboarding records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search Nova expert onboarding records",
        ) from e


@router.get(
    "/B2C-experts/{id}",
    response_model=LawyerOnboardingDetailsResponse,
)
async def get_lawyer_onboarding_endpoint(
    id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LawyerOnboardingDetailsResponse:
    """Get a lawyer onboarding record by ID."""
    # Decrypt and validate the onboarding ID
    decrypted_onboarding_id = _decrypt_and_validate_onboarding_id(id)

    try:
        onboarding = get_lawyer_onboarding_by_id_service(db, decrypted_onboarding_id)
        if not onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nova expert onboarding record not found",
            )

        # Create response data with encrypted ID
        onboarding_item = _create_onboarding_item(onboarding)

        return LawyerOnboardingDetailsResponse(
            success=True,
            message=[
                ResponseMessage(
                    success=True, message="Nova expert onboarding details retrieved successfully"
                )
            ],
            data=onboarding_item,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error getting Nova expert onboarding by ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Nova expert onboarding details",
        ) from e


# Fields that cannot be updated after creation
NON_UPDATABLE_FIELDS = []


@router.patch(
    "/B2C-experts",
    response_model=LawyerOnboardingUpdateResponse,
)
async def update_lawyer_onboarding_endpoint(
    request_data: LawyerOnboardingUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LawyerOnboardingUpdateResponse:
    """Update an existing nova expert onboarding record (partial update)."""
    from app.enums.user_role import UserRoleEnum
    # Todo: if the user is not a navigator, then they should not be able to update the status field
    if request_data.status and (not current_user or (current_user and not current_user.user_roles) or (current_user and current_user.user_roles and not any(user_role.role_id == UserRoleEnum.NAVIGATOR.id for user_role in current_user.user_roles))):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update the status field",
        )
    
    # Check for non-updatable fields in the request
    request_fields = request_data.model_dump(exclude_unset=True, exclude={"id"})
    non_updatable_in_request = [
        field for field in NON_UPDATABLE_FIELDS if field in request_fields
    ]
    
    if non_updatable_in_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"The following fields cannot be updated: {', '.join(non_updatable_in_request)}",
        )

    if (not current_user or (current_user and not current_user.user_roles)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to update this Nova expert onboarding record",
        )
    if not any(user_role.role_id == UserRoleEnum.NAVIGATOR.id for user_role in current_user.user_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to update this Nova expert onboarding record",
        )

    # ID is automatically decrypted by DecryptedRequest schema
    onboarding_id = int(request_data.id)

    try:
        # Validate temp file existence and size BEFORE law firm update
        validate_temp_file_before_processing(
            photo_url=request_data.photo_url,
            entity_type=EntityType.B2C_EXPERT_PROFILE
        )
        # Update the lawyer onboarding record
        updated_onboarding, photo_processing_success = update_lawyer_onboarding_service(
            db, onboarding_id, request_data
        )
        
        if not updated_onboarding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nova expert onboarding record not found",
            )
        
        if not photo_processing_success:
            logger.warning(f"Photo processing failed for Nova expert onboarding ID: {updated_onboarding.id}")

        # Create response data with encrypted ID
        onboarding_item = _create_onboarding_item(updated_onboarding)

        return LawyerOnboardingUpdateResponse(
            success=True,
            message=[
                ResponseMessage(
                    success=True, message="Nova expert onboarding record updated successfully"
                )
            ],
            data=onboarding_item,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error updating Nova expert onboarding record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update Nova expert onboarding record",
        ) from e

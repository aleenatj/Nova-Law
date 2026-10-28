"""Law firm API endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_current_active_user
from app.db.models import User
from app.db.services.law_firm import (
    create_law_firm,
    get_law_firm_by_id,
    search_law_firms,
    update_law_firm,
)
from app.schemas.v1.base import ResponseMessage
from app.schemas.v1.law_firm import (
    LawFirmCreate,
    LawFirmGetByIdResponse,
    LawFirmResponse,
    LawFirmSearchRequest,
    LawFirmSearchResponse,
    LawFirmUpdate,
)
from app.utils.dependencies import get_db
from app.utils.photo_utils import generate_photo_urls
from app.utils.validators import validate_order_params

logger = logging.getLogger(__name__)

router = APIRouter()


def _raise_law_firm_not_found() -> None:
    """Raise HTTPException for law firm not found."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
    )


def _decrypt_and_validate_law_firm_id(law_firm_id: str) -> int:
    """Decrypt and validate law firm ID, raising appropriate HTTPException on failure."""
    from app.utils.encryption import decrypt_id

    decrypted_law_firm_id = decrypt_id(law_firm_id)
    if not decrypted_law_firm_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid organization ID"
        )
    return int(decrypted_law_firm_id)


def _create_law_firm_response_data(law_firm) -> dict:
    """Create law firm response data from a LawFirm model."""
    # Generate logo URLs from folder path
    logos = generate_photo_urls(law_firm.logo)
    # Return null if no logos available
    logos = logos if logos else None

    return {
        "id": str(law_firm.id),
        "name": law_firm.name,
        "contact_person": law_firm.contact_person,
        "contact_no": law_firm.contact_no,
        "contact_email": law_firm.contact_email,
        "address_line_1": law_firm.address_line_1,
        "address_line_2": law_firm.address_line_2,
        "city": law_firm.city,
        "state": law_firm.state,
        "postal_code": law_firm.postal_code,
        "country": law_firm.country,
        "logos": logos,
        "about": law_firm.about,
        "website_url": law_firm.website_url,
        "engage_form_url": law_firm.engage_form_url,
        "law_firm_type": (
            law_firm.law_firm_type.value if law_firm.law_firm_type else None
        ),
        "status": (
            law_firm.status.value if law_firm.status else None
        ),
        "created_at": law_firm.created_at,
        "updated_at": law_firm.updated_at,
    }


@router.post("/law-firm", response_model=LawFirmResponse)
async def create_law_firm_endpoint(
    request_data: LawFirmCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LawFirmResponse:
    """Create a new law firm."""
    try:
        # Create the law firm
        new_law_firm, logo_processing_success = create_law_firm(db, request_data)

        # Create response data with encrypted ID using the helper function
        law_firm_response_data = _create_law_firm_response_data(new_law_firm)

        # Create response data using the proper schema
        from app.schemas.v1.law_firm import LawFirmDetailsResponse

        law_firm_details = LawFirmDetailsResponse.model_validate(law_firm_response_data)

        messages = [ResponseMessage(success=True, message="Organization created successfully")]

        if request_data.logo:
            if not logo_processing_success:
                logger.error(f"Organization created successfully, but logo processing failed for organization ID: {new_law_firm.id}")

        return LawFirmResponse(
            success=True,
            message=messages,
            data=law_firm_details,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except HTTPException:
        raise
    except Exception:
        # Log the exception (as per requirements)
        logger.error("Failed to create organization", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create organization",
        ) from None


@router.put("/law-firm", response_model=LawFirmResponse)
async def update_law_firm_endpoint(
    request_data: LawFirmUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LawFirmResponse:
    """Update an existing law firm."""
    try:
        decrypted_law_firm_id = int(request_data.id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid organization ID format"
        )

    # Check if law firm exists first
    existing_law_firm = get_law_firm_by_id(db, decrypted_law_firm_id)
    if not existing_law_firm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
        )

    try:
        # Update the law firm
        updated_law_firm, logo_processing_success = update_law_firm(db, decrypted_law_firm_id, request_data)
        assert updated_law_firm is not None  # We already verified the law firm exists

        # Create response data with encrypted ID using the helper function
        law_firm_response_data = _create_law_firm_response_data(updated_law_firm)

        # Create response data using the proper schema
        from app.schemas.v1.law_firm import LawFirmDetailsResponse

        law_firm_details = LawFirmDetailsResponse.model_validate(law_firm_response_data)

        messages = [ResponseMessage(success=True, message="Organization updated successfully")]

        if request_data.logo:
            if not logo_processing_success:
                logger.error(f"Organization updated successfully, but logo processing failed for organization ID: {updated_law_firm.id}")

        return LawFirmResponse(
            success=True,
            message=messages,
            data=law_firm_details,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e
    except HTTPException:
        raise
    except Exception:
        # Log the exception (as per requirements)
        logger.error("Failed to update organization", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update organization",
        ) from None


@router.get("/law-firm/{law_firm_id}", response_model=LawFirmGetByIdResponse)
async def get_law_firm_by_id_endpoint(
    law_firm_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LawFirmGetByIdResponse:
    """Get law firm details by ID."""
    # Decrypt and validate the law firm ID
    decrypted_law_firm_id = _decrypt_and_validate_law_firm_id(law_firm_id)

    try:
        # Get the law firm by ID
        law_firm = get_law_firm_by_id(db, decrypted_law_firm_id)
        if not law_firm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found"
            )

        # Create response data with encrypted ID using the helper function
        law_firm_response_data = _create_law_firm_response_data(law_firm)

        # Create response data using the proper schema
        from app.schemas.v1.law_firm import LawFirmDetailsResponse

        law_firm_details = LawFirmDetailsResponse.model_validate(law_firm_response_data)

        return LawFirmGetByIdResponse(
            success=True,
            message=[
                {"success": True, "message": "Organization details retrieved successfully"}
            ],
            data=law_firm_details,
        )

    except HTTPException:
        raise
    except Exception:
        # Log the exception (as per requirements)
        logger.error("Failed to retrieve organization details", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organization details",
        ) from None


@router.get("/law-firm", response_model=LawFirmSearchResponse)
async def search_law_firm_endpoint(
    search_request: LawFirmSearchRequest = Depends(),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> LawFirmSearchResponse:
    """Search for law firms with various criteria using GET method."""
    try:
        # Validate order_by and order_dir parameters
        allowed_order_fields = {
            "id",
            "created_at",
            "updated_at",
        }
        validate_order_params(search_request.order_by, search_request.order_dir, allowed_order_fields)

        # Search for law firms
        law_firms, total_count = search_law_firms(
            db=db,
            name=search_request.name,
            contact_person=search_request.contact_person,
            contact_email=search_request.contact_email,
            city=search_request.city,
            country=search_request.country,
            law_firm_type=(
                search_request.law_firm_type.value
                if search_request.law_firm_type
                else None
            ),
            status=(
                search_request.status.value
                if search_request.status
                else None
            ),
            page=search_request.page,
            limit=search_request.limit,
            order_by=search_request.order_by,
            order_dir=search_request.order_dir,
        )

        # Convert law firms to response format
        from app.schemas.v1.law_firm import LawFirmSearchItem

        law_firm_items = []
        for law_firm in law_firms:
            try:
                # Generate logo URLs from folder path
                logos = generate_photo_urls(law_firm.logo)
                # Return null if no logos available
                logos = logos if logos else None

                # Create search item data with all fields
                search_item_data = {
                    "id": str(law_firm.id),  # Convert to string - will be encrypted by EncryptedResponse schema
                    "name": law_firm.name,
                    "contact_person": law_firm.contact_person,
                    "contact_no": law_firm.contact_no,
                    "contact_email": law_firm.contact_email,
                    "address_line_1": law_firm.address_line_1,
                    "address_line_2": law_firm.address_line_2,
                    "city": law_firm.city,
                    "state": law_firm.state,
                    "postal_code": law_firm.postal_code,
                    "country": law_firm.country,
                    "logos": logos,
                    "about": law_firm.about,
                    "website_url": law_firm.website_url,
                    "engage_form_url": law_firm.engage_form_url,
                    "law_firm_type": (
                        law_firm.law_firm_type.value if law_firm.law_firm_type else None
                    ),
                    "status": (
                        law_firm.status.value if law_firm.status else None
                    ),
                    "created_at": law_firm.created_at,
                    "updated_at": law_firm.updated_at,
                }

                # Validate and create the search item
                search_item = LawFirmSearchItem.model_validate(search_item_data)
                law_firm_items.append(search_item)

            except Exception as e:
                logger.error(
                    f"Failed to create search item for organization {law_firm.id}: {e}",
                    exc_info=True
                )
                # Continue with other items instead of failing completely
                continue

        # Create search data with pagination metadata
        from app.schemas.v1.law_firm import LawFirmSearchData

        search_data = LawFirmSearchData(
            total_count=total_count,
            records_in_page=len(law_firm_items),
            law_firms=law_firm_items,
        )

        if search_data.total_count == 0:
            message = "No data found"
        else:
            message = f"Found {search_data.total_count} organization(s)"

        return LawFirmSearchResponse(
            success=True,
            message=[ResponseMessage(success=True, message=message)],
            data=search_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        # Log the exception (as per requirements)
        logger.error("Failed to search organizations", exc_info=True)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search organizations",
        ) from e

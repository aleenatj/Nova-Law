"""Lawyer onboarding service functions for database operations."""

import logging
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.db.models.lawyer_onboarding import LawyerOnboarding
from app.enums.file_upload import EntityType
from app.enums.lawyer import ExpertiseEnum
from app.schemas.v1.lawyer_onboarding import (
    LawyerOnboardingCreateRequest,
    LawyerOnboardingSearchRequest,
    LawyerOnboardingUpdateRequest,
    ValuesWithOtherInput,
)
from app.services.upload_service import process_file_upload
from app.utils.validators import validate_order_params

logger = logging.getLogger(__name__)


def build_json_with_other(input_data: Optional[ValuesWithOtherInput]) -> Optional[dict[str, Any]]:
    """
    Build JSON for fields that support 'other' (professional_status).
    
    Input: { "values": ["option1"], "other": "custom" }
    
    Returns:
    - { "values": ["option1", "option2"] } - when options selected
    - { "values": [] } - when nothing selected
    - { "values": [], "other": "custom" } - when only other provided
    - { "values": ["option1"], "other": "custom" } - when both provided
    """
    if input_data is None:
        return None
    
    result = {}
    
    # Handle values
    if input_data.values and len(input_data.values) > 0:
        result["values"] = input_data.values
    else:
        result["values"] = []
    
    # Handle other (single string) - check both "other" and "Other" fields
    other_value = input_data.other or (getattr(input_data, "Other", None) if hasattr(input_data, "Other") else None)
    if other_value:
        result["other"] = other_value
    
    return result


# Valid order fields for lawyer onboarding queries
VALID_ORDER_FIELDS = {
    "id",
    "status",
    "experience",
    "created_at",
    "updated_at",
}

def process_matter_types(service_details: dict[str, Any]) -> list[str]:
    """
    Parse service_details and extract all matter types from expertises.

    Args:
        service_details (dict): The service details as provided in the onboarding request.

    Returns:
        list[str]: All distinct matter types (as enum values) found in expertises of cohabitees and married_civil_partners.
    """
    matter_types: set[str] = set()
    if not service_details:
        return []
    
    service_details_dict = service_details.model_dump()

    # Cohabitees
    cohabitees = service_details_dict.get("cohabitees", {}) if 'cohabitees' in service_details_dict and service_details_dict.get("cohabitees") is not None else {}
    expertises = cohabitees.get("expertises", [])
    # Married or Civil Partners
    married_cp = service_details_dict.get("married_civil_partners", {}) if 'married_civil_partners' in service_details_dict and service_details_dict.get("married_civil_partners") is not None else {}
    expertises.extend(married_cp.get("expertises", []))
    if isinstance(expertises, list):
        for expertise in expertises:
            try:
                enum_value = ExpertiseEnum[expertise]
                if enum_value.matter_type.name not in matter_types:
                    matter_types.add(enum_value.matter_type.name)
            except ValueError:
                logger.error(f"Unknown cohabitees expertise provided: {expertise}")

    return list(matter_types)

def create_lawyer_onboarding(
    db: Session, request_data: LawyerOnboardingCreateRequest
) -> tuple[LawyerOnboarding, bool]:
    """
    Create a new lawyer onboarding record.

    Returns:
        tuple: (LawyerOnboarding, photo_processing_success)
    """
    try:
        # Process matter types
        matter_types = process_matter_types(request_data.service_details)
        # Prepare data for the model
        onboarding_data = {
            # Required text fields
            "first_name": request_data.first_name,
            "last_name": request_data.last_name,
            "email": request_data.email.lower(),
            "phone": request_data.phone,
            "work_status": request_data.work_status,
            "city": request_data.city,
            "post_code": request_data.post_code,
            # Optional text/enum fields
            "firm_name": request_data.firm_name,
            "gender": request_data.gender,
            "photo_url": None,  # Will be processed after record creation
            "experience": request_data.experience,
            "ncdr_description": request_data.ncdr_description,
            "compelling_quote": request_data.compelling_quote,
            "remote_consultation": request_data.remote_consultation,
            # JSON field with values + other (professional_status)
            "professional_status": build_json_with_other(request_data.professional_status),
            # Regulator - single value only (take first value from list)
            "regulator": build_json_with_other(request_data.regulator),
            # JSON fields with values only (ncdr_magic, accredited_specialist, consultation_offers) - pass dict directly
            "ncdr_magic": request_data.ncdr_magic,
            "accredited_specialist": request_data.accredited_specialist,
            "consultation_offers": request_data.consultation_offers,
            # Special JSON field - service_details (convert Pydantic model to dict)
            "service_details": request_data.service_details.model_dump() if request_data.service_details else None,
            "matter_types": matter_types,
            "accredited_specialism_other": request_data.accredited_specialism_other,
        }
        
        # Create the LawyerOnboarding record
        lawyer_onboarding = LawyerOnboarding(**onboarding_data)

        db.add(lawyer_onboarding)
        db.flush()

        # Process photo upload if provided
        photo_processing_success = True
        if request_data.photo_url:
            processed_photo_url, photo_processing_success = process_file_upload(
                photo_url=request_data.photo_url,
                entity_id=lawyer_onboarding.id,
                entity_type=EntityType.B2C_EXPERT_PROFILE,
                is_update=False,
                existing_photo_url=None,
            )
            if processed_photo_url:
                lawyer_onboarding.photo_url = processed_photo_url
        db.commit()
        db.refresh(lawyer_onboarding)

        return lawyer_onboarding, photo_processing_success
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Failed to create Novaexpert onboarding record: {e!s}"},
        ) from e



def get_lawyer_onboarding_by_id(db: Session, onboarding_id: int) -> LawyerOnboarding | None:
    """Get a lawyer onboarding record by ID."""
    try:
        return db.query(LawyerOnboarding).filter(LawyerOnboarding.id == onboarding_id).first()
    except Exception as e:
        logger.exception(f"Error getting Nova expert onboarding by ID: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve Nova expert onboarding record",
        ) from e


def update_lawyer_onboarding(
    db: Session, onboarding_id: int, request_data: LawyerOnboardingUpdateRequest
) -> tuple[LawyerOnboarding | None, bool]:
    """
    Update an existing lawyer onboarding record (partial update).

    Returns:
        tuple: (LawyerOnboarding, photo_processing_success) or (None, False) if not found
    """
    try:
        lawyer_onboarding = db.query(LawyerOnboarding).filter(
            LawyerOnboarding.id == onboarding_id
        ).first()
        
        if not lawyer_onboarding:
            return None, False

        # Get the fields to update (only non-None values, excluding 'id' which is used for lookup)
        update_data = request_data.model_dump(exclude_unset=True, exclude={"id"})
        
        # Handle special JSON fields that need transformation
        if "professional_status" in update_data and update_data["professional_status"] is not None:
            update_data["professional_status"] = build_json_with_other(request_data.professional_status)
        
        if "regulator" in update_data and update_data["regulator"] is not None:
            update_data["regulator"] = build_json_with_other(request_data.regulator)
            
        matter_types = process_matter_types(request_data.service_details)
        if matter_types:
            update_data["matter_types"] = matter_types
        
        # Handle service_details - convert Pydantic model to dict
        if "service_details" in update_data and update_data["service_details"] is not None:
            if hasattr(update_data["service_details"], "model_dump"):
                update_data["service_details"] = update_data["service_details"].model_dump()
        
        # Handle photo upload separately
        photo_processing_success = True
        photo_url_from_request = update_data.pop("photo_url", None)

        if "email" in update_data and update_data["email"]:
            update_data["email"] = update_data["email"].lower()
        
        # Apply updates to the model
        for field, value in update_data.items():
            if hasattr(lawyer_onboarding, field):
                setattr(lawyer_onboarding, field, value)
        
        db.flush()
        
        # Process photo upload if provided
        if photo_url_from_request:
            processed_photo_url, photo_processing_success = process_file_upload(
                photo_url=photo_url_from_request,
                entity_id=lawyer_onboarding.id,
                entity_type=EntityType.B2C_EXPERT_PROFILE,
                is_update=True,
                existing_photo_url=lawyer_onboarding.photo_url,
            )
            if processed_photo_url:
                lawyer_onboarding.photo_url = processed_photo_url

        db.commit()
        db.refresh(lawyer_onboarding)

        return lawyer_onboarding, photo_processing_success
    except Exception as e:
        db.rollback()
        logger.exception(f"Error updating Nova expert onboarding record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": f"Failed to update Nova expert onboarding record: {e!s}"},
        ) from e


def search_lawyer_onboarding(
    db: Session, request_data: LawyerOnboardingSearchRequest
) -> tuple[list[LawyerOnboarding], int]:
    """Search lawyer onboarding records with filters, pagination, and ordering."""
    try:
        # Validate order parameters
        validate_order_params(request_data.order_by, request_data.order_dir, VALID_ORDER_FIELDS)

        # Start with base query
        query = db.query(LawyerOnboarding)

        # Build search conditions
        conditions = []

        # Search term filter (searches across first_name, last_name, email)
        if request_data.search_term:
            search_term = f"%{request_data.search_term.strip()}%"
            conditions.append(
                (func.trim(LawyerOnboarding.first_name).ilike(search_term))
                | (func.trim(LawyerOnboarding.last_name).ilike(search_term))
                | (func.trim(LawyerOnboarding.email).ilike(search_term))
                | ((func.trim(LawyerOnboarding.first_name) + " " + func.trim(LawyerOnboarding.last_name)).ilike(search_term))
            )

        # Status filter
        if request_data.status:
            conditions.append(LawyerOnboarding.status == request_data.status)

        # Apply search conditions if any
        if conditions:
            query = query.filter(and_(*conditions))

        # Get total count before pagination
        total_count = query.count()

        # Apply ordering
        order_column = getattr(LawyerOnboarding, request_data.order_by, LawyerOnboarding.id)
        if request_data.order_dir.lower() == "desc":
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(order_column)

        # Apply pagination
        offset = (request_data.page - 1) * request_data.limit
        records = query.offset(offset).limit(request_data.limit).all()

        return records, total_count
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error searching Nova expert onboarding records: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search Nova expert onboarding records",
        ) from e

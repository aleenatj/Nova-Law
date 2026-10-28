"""Law firm service functions for database operations."""

import logging

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.law_firm import LawFirm
from app.enums.file_upload import EntityType
from app.schemas.v1.law_firm import LawFirmCreate, LawFirmUpdate
from app.services.upload_service import process_file_upload, validate_temp_file_before_processing
from app.utils.validators import validate_phone_number, validate_url_format
from app.enums.law_firm import LawFirmStatusEnum
from app.enums.law_firm_type import LawFirmType

logger = logging.getLogger(__name__)


def get_existing_law_firm_email_count(db: Session, contact_email: str, exclude_id: int | None = None) -> int:
    query = db.query(func.count(LawFirm.id)).filter(LawFirm.contact_email == contact_email)
    if exclude_id:
        query = query.filter(LawFirm.id != exclude_id)
    return query.scalar() # type: ignore

def get_existing_law_firm_engage_form_url_count(db: Session, engage_form_url: str, exclude_id: int | None = None) -> int:
    query = db.query(func.count(LawFirm.id)).filter(LawFirm.engage_form_url == engage_form_url)
    if exclude_id:
        query = query.filter(LawFirm.id != exclude_id)
    return query.scalar() # type: ignore

def create_law_firm(db: Session, law_firm_data: LawFirmCreate) -> tuple[LawFirm, bool]:
    """
    Create a new law firm.

    Args:
        db: Database session
        law_firm_data: Law firm creation data

    Returns:
        Tuple of (created law firm instance, logo_processing_success)
    """
    # Validate temp file existence and size BEFORE law firm creation
    validate_temp_file_before_processing(
        photo_url=law_firm_data.logo,
        entity_type=EntityType.LAW_FIRM_LOGO
    )
    # Validate phone number format
    if law_firm_data.contact_no and not validate_phone_number(law_firm_data.contact_no):
        raise ValueError("Invalid phone number format")

    # Check duplicate email
    if get_existing_law_firm_email_count(db, law_firm_data.contact_email) > 0:
        raise ValueError("Organization with this email already exists")

    # Check duplicate engage_form_url (only if provided)
    if law_firm_data.engage_form_url and get_existing_law_firm_engage_form_url_count(db, law_firm_data.engage_form_url) > 0:
        raise ValueError(f"Organization with this client id ({law_firm_data.engage_form_url}) already exists")

    if law_firm_data.website_url and not validate_url_format(law_firm_data.website_url):
        raise ValueError("Invalid website url format")

    # Extract logo_url from data and set to None initially
    logo_url = law_firm_data.logo
    law_firm_dict = law_firm_data.model_dump()
    law_firm_dict["logo"] = None
    law_firm_dict["contact_email"] = law_firm_dict["contact_email"].lower()
    # Set engage_form_url to None if it is empty or null
    if not law_firm_dict.get("engage_form_url"):
        law_firm_dict["engage_form_url"] = None
    # Create law firm instance
    law_firm = LawFirm(**law_firm_dict)
    # Add to database and flush to get ID
    db.add(law_firm)
    db.flush()

    # Process logo upload if provided (CREATE operation - new folder)
    processed_logo_url, logo_processing_success = process_file_upload(
        photo_url=logo_url,
        entity_id=law_firm.id,
        entity_type=EntityType.LAW_FIRM_LOGO,
        is_update=False
    )

    if processed_logo_url:
        # Update the law firm record with processed logo URL
        law_firm.logo = processed_logo_url
    else:
        law_firm.logo = None

    # Commit changes
    db.commit()
    db.refresh(law_firm)

    return law_firm, logo_processing_success


def get_law_firm_by_id(db: Session, law_firm_id: int) -> LawFirm | None:
    """
    Get a law firm by ID.

    Args:
        db: Database session
        law_firm_id: ID of the law firm

    Returns:
        Law firm instance or None if not found
    """
    return db.query(LawFirm).filter(LawFirm.id == law_firm_id).first()


def get_law_firms(db: Session, skip: int = 0, limit: int = 100) -> list[LawFirm]:
    """
    Get a list of law firms with pagination.

    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return

    Returns:
        List of law firm instances
    """
    return db.query(LawFirm).offset(skip).limit(limit).all()


def update_law_firm(
    db: Session, law_firm_id: int, law_firm_data: LawFirmUpdate
) -> tuple[LawFirm | None, bool]:
    """
    Update an existing law firm.

    Args:
        db: Database session
        law_firm_id: ID of the law firm to update
        law_firm_data: Law firm update data

    Returns:
        Tuple of (updated law firm instance or None if not found, logo_processing_success)
    """
    # Validate temp file existence and size BEFORE law firm update
    validate_temp_file_before_processing(
        photo_url=law_firm_data.logo,
        entity_type=EntityType.LAW_FIRM_LOGO
    )
    
    # Validate phone number format
    if law_firm_data.contact_no and not validate_phone_number(law_firm_data.contact_no):
        raise ValueError("Invalid phone number format")

    if law_firm_data.contact_email and get_existing_law_firm_email_count(
        db, law_firm_data.contact_email, exclude_id=law_firm_id
    ) > 0:
        raise ValueError("Organization with this email already exists")

    # Check duplicate engage_form_url (exclude current firm)
    if law_firm_data.engage_form_url:
        if get_existing_law_firm_engage_form_url_count(
            db, law_firm_data.engage_form_url, exclude_id=law_firm_id
        ) > 0:
            raise ValueError(f"Organization with this client id ({law_firm_data.engage_form_url}) already exists")
    # Set engage_form_url to None if it is empty or null
    if not law_firm_data.engage_form_url:
        law_firm_data.engage_form_url = None

    if law_firm_data.website_url and not validate_url_format(law_firm_data.website_url):
        raise ValueError("Invalid website url format")

    # Get the existing law firm
    law_firm = db.query(LawFirm).filter(LawFirm.id == law_firm_id).first()

    if not law_firm:
        return None, True

    # Store existing logo URL for processing
    existing_logo_url = law_firm.logo
    logo_processing_success = True

    # Update only the fields that are provided, excluding the id and logo fields
    update_data = law_firm_data.model_dump(exclude_unset=True, exclude={"id", "logo"})
    
    # Convert enum instances to their values for SQLAlchemy
    if update_data.get("status") and hasattr(update_data["status"], "value"):
        update_data["status"] = update_data["status"].value
    if update_data.get("law_firm_type") and hasattr(update_data["law_firm_type"], "value"):
        update_data["law_firm_type"] = update_data["law_firm_type"].value

    if "contact_email" in update_data and update_data["contact_email"]:
        update_data["contact_email"] = update_data["contact_email"].lower()

    for field, value in update_data.items():
        setattr(law_firm, field, value)

    # Process logo upload if provided (UPDATE operation)
    if law_firm_data.logo:
        processed_logo_url, logo_processing_success = process_file_upload(
            photo_url=law_firm_data.logo,
            entity_id=law_firm.id,
            entity_type=EntityType.LAW_FIRM_LOGO,
            is_update=True,
            existing_photo_url=existing_logo_url
        )

        if processed_logo_url:
            law_firm.logo = processed_logo_url
        else:
            # If processing failed, keep existing logo
            logger.warning(f"Failed to process logo upload for organization {law_firm_id}")
    else:
        law_firm.logo = None
    # Update the updated_at timestamp
    from datetime import datetime, timezone

    law_firm.updated_at = datetime.now(timezone.utc)

    # Commit changes
    db.commit()
    db.refresh(law_firm)

    return law_firm, logo_processing_success


def search_law_firms(
    db: Session,
    name: str | None = None,
    contact_person: str | None = None,
    contact_email: str | None = None,
    city: str | None = None,
    country: str | None = None,
    law_firm_type: str | None = None,
    status: str | None = None,
    page: int = 1,
    limit: int = 10,
    order_by: str = "id",
    order_dir: str = "desc",
) -> tuple[list[LawFirm], int]:
    """
    Search for law firms with various criteria.

    Args:
        db: Database session
        name: Search by law firm name (partial match)
        contact_person: Search by contact person name (partial match)
        contact_email: Search by contact email (partial match)
        city: Search by city (partial match)
        country: Search by country (partial match)
        law_firm_type: Filter by law firm type
        status: Filter by law firm status
        page: Page number for pagination
        limit: Number of items per page
        order_by: Field to order by
        order_dir: Order direction (asc/desc)

    Returns:
        Tuple of (law_firms, total_count)
    """
    from sqlalchemy import and_

    # Start with base query
    query = db.query(LawFirm)

    # Build search conditions
    conditions = []

    if name:
        name = name.strip()
        conditions.append(LawFirm.name.ilike(f"%{name}%"))

    if contact_person:
        contact_person = contact_person.strip()
        conditions.append(LawFirm.contact_person.ilike(f"%{contact_person}%"))

    if contact_email:
        contact_email = contact_email.strip()
        conditions.append(LawFirm.contact_email.ilike(f"%{contact_email}%"))

    if city:
        city = city.strip()
        conditions.append(LawFirm.city.ilike(f"%{city}%"))

    if country:
        country = country.strip()
        conditions.append(LawFirm.country.ilike(f"%{country}%"))

    if law_firm_type:
        conditions.append(LawFirm.law_firm_type == law_firm_type)
    
    if status:
        conditions.append(LawFirm.status == status)

    # Apply search conditions if any
    if conditions:
        query = query.filter(and_(*conditions))

    # Get total count before pagination
    total_count = query.count()

    # Apply ordering
    order_column = getattr(LawFirm, order_by, LawFirm.id)
    if order_dir.lower() == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # Apply pagination
    offset = (page - 1) * limit
    law_firms = query.offset(offset).limit(limit).all()

    return law_firms, total_count


def delete_law_firm(db: Session, law_firm_id: int) -> bool:
    """
    Delete a law firm by ID.

    Args:
        db: Database session
        law_firm_id: ID of the law firm to delete

    Returns:
        True if deleted successfully, False otherwise
    """
    law_firm = db.query(LawFirm).filter(LawFirm.id == law_firm_id).first()

    if not law_firm:
        return False

    db.delete(law_firm)
    db.commit()
    return True

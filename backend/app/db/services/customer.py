"""Customer service functions for database operations."""

from sqlalchemy.orm import Session

from app.db.models import Customer, Resolve
from app.db.services.user import get_user_by_id
from app.enums.user import StatusEnum


def validate_resolve_customer_assignment(db: Session, resolve_id: int) -> None:
    """
    Validate that a resolve record is not already assigned to a customer.

    Args:
        db: Database session
        resolve_id: ID of the resolve record to validate

    Raises:
        ValueError: If resolve record already has a customer assigned
    """
    from sqlalchemy import select
    from app.enums.resolve import ResolveStatusEnum

    resolve_data = db.execute(
        select(Resolve.customer_id, Resolve.status).where(Resolve.id == resolve_id)
    ).first()
    if resolve_data is None:
        raise ValueError("Resolve record not found.")

    customer_id, status = resolve_data

    if customer_id is not None:
        raise ValueError("This resolve is already linked to a customer.")

    if status == ResolveStatusEnum.IN_PROGRESS:
        raise ValueError("Resolve is not completed.")


def get_customer_by_user_id(db: Session, user_id: int) -> Customer | None:
    """Get customer by user ID."""
    return db.query(Customer).filter(Customer.user_id == user_id).first()


def get_customer_by_id(db: Session, customer_id: int) -> Customer | None:
    """Get customer by ID."""
    return db.query(Customer).filter(Customer.id == customer_id).first()


def create_customer_and_update_resolve_transactional(
    db: Session,
    user_id: int,
    resolve_id: int | None = None
) -> Customer:
    """
    Create a new customer and optionally update resolve record without committing.

    This is a transactional version of create_customer_and_update_resolve that doesn't
    commit automatically, allowing for rollback if needed.

    Args:
        db: Database session
        user_id: ID of the newly created user
        resolve_id: Optional resolve ID to update with customer_id

    Returns:
        Created customer record
    """
    user = get_user_by_id(db, user_id)
    if user and user.customer:
        customer = user.customer
    else:
        # Create new customer record if user does not have a customer record
        customer = Customer(
            status=StatusEnum.ACTIVE,
            user_id=user_id,
        )

        db.add(customer)
        db.flush()  # Flush to get the ID without committing
        db.refresh(customer)

    # Update resolve record if resolve_id is provided
    if resolve_id:
        resolve_record = db.query(Resolve).filter(Resolve.id == resolve_id).first()
        if resolve_record:
            resolve_record.customer_id = customer.id
            db.flush()  # Flush without committing

    return customer


def update_customer_phone_number(db: Session, user_id: int, phone: str) -> None:
    """Update customer phone number."""
    if not user_id:
        raise ValueError("User ID is required to update customer phone number.")
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            raise ValueError("User not found.")
        elif user.phone == phone:
            return
        else:
            user.phone = phone
            db.commit()
            db.refresh(user)
    except Exception as e:
        raise ValueError(f"Failed to update customer phone number: {e}") from e

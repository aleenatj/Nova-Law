"""Navigator service functions for database operations."""

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from app.db.models import User, UserRole
from app.enums.user_role import UserRoleEnum
from app.enums.user import StatusEnum
from app.schemas.v1.user import UserCreateRequest, UserUpdateRequest


def create_nova_navigator_user(db: Session, user_data: UserCreateRequest) -> tuple[User, str | None]:
    """Create a new Nova Navigator user with Navigator role."""
    from app.db.services.user import create_user_with_role
    return create_user_with_role(db, user_data, UserRoleEnum.NAVIGATOR)


def update_nova_navigator_user(db: Session, user_id: int, user_data: UserUpdateRequest) -> User | None:
    """Update a Nova Navigator user (excluding password)."""
    from app.db.services.user import update_user_generic
    return update_user_generic(db, user_id, user_data)


def search_navigators(
    db: Session,
    search_term: str | None = None,
    name: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    status: StatusEnum | None = None,
    page: int = 1,
    limit: int = 10,
    order_by: str = "id",
    order_dir: str = "desc"
) -> tuple[list[User], int]:
    """
    Search for navigator users with various criteria.

    Args:
        db: Database session
        search_term: Search by first name, last name, full name, or email (partial match)
        name: Search by name (first name, last name, or full name)
        email: Search by email (partial match)
        phone: Search by phone number (partial match)
        status: Filter by user status (Active, Inactive)
        page: Page number for pagination
        limit: Number of items per page
        order_by: Field to order by
        order_dir: Order direction (asc/desc)

    Returns:
        Tuple of (users, total_count)
    """
    # Start with base query for navigator users
    query = db.query(User).join(UserRole).filter(UserRole.role_id == UserRoleEnum.NAVIGATOR.id)

    # Build search conditions
    conditions = []

    if search_term:
        term = search_term.strip()
        search_condition = or_(
            User.first_name.ilike(f"%{term}%"),
            User.last_name.ilike(f"%{term}%"),
            User.email.ilike(f"%{term}%"),
            User.first_name.concat(" ").concat(User.last_name).ilike(f"%{term}%"),
        )
        conditions.append(search_condition)
    
    if name:
        # Search in first_name, last_name, and concatenated full name
        name = name.strip()
        name_condition = or_(
            User.first_name.ilike(f"%{name}%"),
            User.last_name.ilike(f"%{name}%"),
            func.trim(User.first_name).concat(" ").concat(func.trim(User.last_name)).ilike(f"%{name}%")
        )
        conditions.append(name_condition)

    if email:
        email = email.strip()
        conditions.append(User.email.ilike(f"%{email}%"))

    if phone:
        phone = phone.strip()
        conditions.append(User.phone.ilike(f"%{phone}%"))

    if status:
        conditions.append(User.status == status)

    # Apply search conditions if any
    if conditions:
        query = query.filter(and_(*conditions))

    # Get total count before pagination
    total_count = query.count()

    # Apply ordering
    order_column = getattr(User, order_by, User.id)
    if order_dir.lower() == "desc":
        query = query.order_by(order_column.desc())
    else:
        query = query.order_by(order_column.asc())

    # Apply pagination
    offset = (page - 1) * limit
    users = query.offset(offset).limit(limit).all()

    return users, total_count


def get_navigator_by_id(db: Session, navigator_id: int) -> User | None:
    """
    Get a navigator user by ID.

    Args:
        db: Database session
        navigator_id: ID of the navigator user

    Returns:
        Navigator user or None if not found or not a navigator
    """
    # Query for user with navigator role
    user = db.query(User).join(UserRole).filter(
        User.id == navigator_id,
        UserRole.role_id == UserRoleEnum.NAVIGATOR.id
    ).first()

    return user

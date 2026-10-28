"""User service functions for database operations."""

from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.core.security import get_password_hash
from app.db.models import User, UserRole
from app.enums.user_role import UserRoleEnum
from app.schemas.v1.user import (
    UserCreate,
    UserCreateRequest,
    UserProfileUpdateRequest,
    UserUpdate,
    UserUpdateRequest,
)
from app.utils.validators import validate_email_format, validate_phone_number

from app.db.services.auth import get_user_by_email, get_user_by_id

def validate_gender_other(gender, gender_other):
    """Validate that gender_other is only provided when gender is Other.
    
    Args:
        gender: Gender enum value
        gender_other: Gender other value (string or None)
        
    Raises:
        ValueError: If gender_other is provided when gender is Male or Female
    """
    if gender_other is not None and gender and gender.value in ["Male", "Female"]:
        raise ValueError("gender_other can only be provided when gender is 'Other'")


def get_current_user(db: Session, user_id: int) -> User | None:
    """Get current user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user."""
    # Validate phone number if provided (empty string will be converted to None)
    if user_data.phone and user_data.phone != "":
        if not validate_phone_number(user_data.phone):
            raise ValueError("Invalid phone number format")

    if user_data.email:
        if not validate_email_format(user_data.email):
            raise ValueError("Invalid email format")

    # Hash the password if provided, otherwise set to None
    hashed_password = None
    if user_data.password:
        hashed_password = get_password_hash(user_data.password)

    # Convert empty phone string to None
    phone_value = None if (user_data.phone == "" or user_data.phone is None) else user_data.phone

    # Create user with the new schema fields
    db_user = User(
        first_name=user_data.first_name.title() if user_data.first_name else "",
        last_name=user_data.last_name.title() if user_data.last_name else "",
        email=user_data.email.lower(),
        phone=phone_value,
        password=hashed_password,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def assign_user_role(db: Session, user_id: int, role_enum: UserRoleEnum) -> None:
    """Assign a role to a user."""
    user_role = UserRole(user_id=user_id, role_id=role_enum.id)
    db.add(user_role)
    db.commit()


def _create_user_core(
    db: Session,
    user_data: UserCreateRequest,
    role_enum: UserRoleEnum,
    password: str | None = None
) -> User:
    """
    Core function to create a user and assign a role.

    This is a helper function that contains the common logic for user creation.
    It does not handle transactions - that must be done by the calling function.

    Args:
        db: Database session
        user_data: User creation data
        role_enum: Role to assign to the user
        password: Optional password to hash and store (only for customer role)

    Returns:
        Created user

    Raises:
        ValueError: If user with email already exists or phone number is invalid
    """
    # Check if user with email already exists
    existing_user = get_user_by_email(db, user_data.email)
    if existing_user:
        if existing_user.user_roles and any(role.role_id != role_enum.id for role in existing_user.user_roles):
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        
        if role_enum == UserRoleEnum.LAWYER:
            return existing_user
        else:
            raise HTTPException(status_code=409, detail="An account with this email already exists.")
        # if existing_user.user_roles and any(role.role_id != UserRoleEnum.CUSTOMER.id for role in existing_user.user_roles):
        #     user_role_name = UserRoleEnum.from_id(existing_user.user_roles[0].role_id).display_name
        #     # raise ValueError(f"An account with this email already exists with the role {user_role_name}. Please use another email to continue.")
        #     raise ValueError(f"An account with this email already exists. Please use another email to continue.")
        # if existing_user.user_roles and any(role.role_id != role_enum.id for role in existing_user.user_roles):
        #     raise ValueError("Email already assigned to a different role")
        # return existing_user

    # Validate phone number if provided (empty string will be converted to None)
    if user_data.phone and user_data.phone != "":
        if not validate_phone_number(user_data.phone):
            raise ValueError("Invalid phone number format")

    if user_data.email:
        if not validate_email_format(user_data.email):
            raise ValueError("Invalid email format")

    # Validate gender_other
    # validate_gender_other(user_data.gender, user_data.gender_other)

    # Determine password based on role and provided password
    hashed_password = None
    if role_enum == UserRoleEnum.CUSTOMER and password:
        from app.core.security import get_password_hash
        hashed_password = get_password_hash(password)

    # Handle gender_other logic
    gender_other_value = None
    if user_data.gender and user_data.gender.value == "Other":
        gender_other_value = user_data.gender_other
    
    # Convert empty phone string to None
    phone_value = None if (user_data.phone == "" or user_data.phone is None) else user_data.phone
    
    # Create user
    db_user = User(
        first_name=user_data.first_name.title() if user_data.first_name else "",
        last_name=user_data.last_name.title() if user_data.last_name else "",
        email=user_data.email.lower(),
        phone=phone_value,
        gender=user_data.gender,
        gender_other=gender_other_value,
        password=hashed_password,
        status=user_data.status,
    )

    db.add(db_user)
    db.flush()  # Flush to get the ID
    db.refresh(db_user)

    # Assign the specified role
    user_role = UserRole(user_id=db_user.id, role_id=role_enum.id)
    db.add(user_role)
    db.flush()  # Flush without committing

    return db_user


def create_user_with_role(
    db: Session,
    user_data: UserCreateRequest,
    role_enum: UserRoleEnum,
    auto_generate_password: bool = True
) -> tuple[User, str | None]:
    """
    Create a new user with a specific role.

    Args:
        db: Database session
        user_data: User creation data
        role_enum: Role to assign to the user
        auto_generate_password: This parameter is deprecated and ignored

    Returns:
        Tuple of (created_user, password) where password is always None
    """
    # Create user using core function
    db_user = _create_user_core(db, user_data, role_enum)

    # Commit the transaction
    db.commit()

    return db_user, None


def update_user_generic(
    db: Session,
    user_id: int,
    user_data: UserUpdateRequest
) -> User | None:
    """
    Generic function to update user information.

    Args:
        db: Database session
        user_id: ID of user to update
        user_data: Update data

    Returns:
        Updated user or None if not found
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    # Check if email is being updated and if it conflicts with existing user
    if user_data.email and user_data.email.lower() != db_user.email.lower():
        existing_user = get_user_by_email(db, user_data.email)
        if existing_user and existing_user.id != user_id:
            # Check if the existing user has any roles
            existing_roles = existing_user.user_roles
            if existing_roles and any(role.role_id != UserRoleEnum.LAWYER.id for role in existing_roles):
                raise HTTPException(status_code=409, detail="An account with this email already exists.")
            raise HTTPException(status_code=409, detail="An account with this email already exists.")

    # Validate phone number if provided (empty string will be converted to None)
    if user_data.phone and user_data.phone != "":
        if not validate_phone_number(user_data.phone):
            raise ValueError("Invalid phone number format")

    if user_data.email:
        if not validate_email_format(user_data.email):
            raise ValueError("Invalid email format")

    # Validate gender_other if gender is being updated
    # if hasattr(user_data, 'gender') and user_data.gender is not None:
    #     validate_gender_other(user_data.gender, user_data.gender_other)

    # Get update data excluding None values
    update_data = user_data.model_dump(exclude_unset=True, exclude_none=True)
    
    # Handle phone number clearing: empty string should set phone to None
    if "phone" in update_data and update_data["phone"] == "":
        update_data["phone"] = None

    # Capitalize first and last names if they are being updated
    if "first_name" in update_data and update_data["first_name"]:
        update_data["first_name"] = update_data["first_name"].title()
    if "last_name" in update_data and update_data["last_name"]:
        update_data["last_name"] = update_data["last_name"].title()

    if "email" in update_data and update_data["email"]:
        update_data["email"] = update_data["email"].lower()

    # Explicitly exclude password from updates
    if "password" in update_data:
        del update_data["password"]

    # Handle gender_other logic
    if "gender" in update_data:
        # If gender is being updated to Male or Female, set gender_other to None
        if update_data["gender"] and update_data["gender"].value in ["Male", "Female"]:
            update_data["gender_other"] = None
        # If gender is Other and gender_other was provided (even as None), keep it
        elif update_data["gender"] and update_data["gender"].value == "Other":
            # If gender_other was explicitly set in the request, use it
            if "gender_other" not in update_data and hasattr(user_data, 'gender_other'):
                # Check if gender_other was provided in the request
                provided_fields = user_data.model_dump(exclude_unset=True)
                if "gender_other" in provided_fields:
                    update_data["gender_other"] = user_data.gender_other

    # Update user fields
    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User | None:
    """Update user information."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    # Validate phone number if provided (reject empty strings)
    if user_update.phone is not None:
        if user_update.phone == "":
            raise ValueError("Phone number cannot be empty")
        if not validate_phone_number(user_update.phone):
            raise ValueError("Invalid phone number format")

    if user_update.email:
        if not validate_email_format(user_update.email):
            raise ValueError("Invalid email format")
    update_data = user_update.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] is not None:
        update_data["email"] = update_data["email"].lower()

    # Handle password hashing if password is being updated
    if update_data.get("password"):
        update_data["password"] = get_password_hash(update_data["password"])

    for field, value in update_data.items():
        setattr(db_user, field, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return False

    db.delete(db_user)
    db.commit()
    return True


def change_user_password(db: Session, user_id: int, current_password: str, new_password: str) -> bool:
    """Change user password with validation."""
    from app.core.security import get_password_hash, verify_password

    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return False

    # Verify current password
    if not verify_password(current_password, db_user.password):  # type: ignore
        return False

    # Hash the new password
    hashed_new_password = get_password_hash(new_password)

    # Update the password
    db_user.password = hashed_new_password  # type: ignore
    db.commit()
    db.refresh(db_user)

    return True


def create_user_with_role_transactional(
    db: Session,
    user_data: UserCreateRequest,
    role_enum: UserRoleEnum,
    password: str | None = None
) -> User:
    """
    Create a new user with a specific role without committing the transaction.

    This is a transactional version of create_user_with_role that doesn't commit
    automatically, allowing for rollback if needed.

    Args:
        db: Database session
        user_data: User creation data
        role_enum: Role to assign to the user
        password: Optional password to hash and store (only for customer role)

    Returns:
        Created user

    Raises:
        ValueError: If user with email already exists or phone number is invalid
    """
    # Create user using core function (no commit)
    return _create_user_core(db, user_data, role_enum, password)


def update_user_profile(
    db: Session,
    user_id: int,
    profile_data: UserProfileUpdateRequest
) -> User | None:
    """
    Update user profile information.

    Args:
        db: Database session
        user_id: ID of user to update
        profile_data: Profile update data

    Returns:
        Updated user or None if not found

    Raises:
        ValueError: If validation fails
    """
    # Convert profile update request to UserUpdateRequest
    user_update_data = UserUpdateRequest(
        first_name=profile_data.first_name,
        last_name=profile_data.last_name,
        phone=profile_data.phone,
        gender=profile_data.gender,
        gender_other=profile_data.gender_other,
    )

    # Use the existing generic update function
    return update_user_generic(db, user_id, user_update_data)


def verify_email_user_navigator(db: Session, email: str) -> bool:
    """Verify if the email exists and is a navigator email."""
    user = get_user_by_email(db, email)
    if user and user.user_roles :
        return any(role.role_id == UserRoleEnum.NAVIGATOR.id for role in user.user_roles)
    return False


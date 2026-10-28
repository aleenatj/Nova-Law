from typing import Any

from sqlalchemy import func
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_password_hash
from app.db.models import User, Case
from app.db.models.simple_auth_token import SimpleAuthToken
from app.enums.user_role import UserRoleEnum
from app.schemas.v1.user import UserCreate, UserUpdate
from app.core.config import settings

import logging
logger = logging.getLogger(__name__)

def create_user(db: Session, user_data: UserCreate) -> User:
    """Create a new user."""
    # Hash the password if provided, otherwise set to None
    hashed_password = None
    if user_data.password:
        hashed_password = get_password_hash(user_data.password)

    # Create user with the new schema fields
    db_user = User(
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        email=user_data.email.lower(),
        password=hashed_password,
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_user_by_email(db: Session, email: str) -> User | None:
    """Get user by email."""
    return db.query(User).options(
        joinedload(User.user_roles)
        ).options(joinedload(User.lawyer)
        ).options(joinedload(User.customer)
        ).filter(func.lower(User.email) == email.lower()).first()


def get_user_by_id(db: Session, user_id: int) -> User | None:
    """Get user by ID."""
    return db.query(User).options(
        joinedload(User.user_roles)
        ).options(joinedload(User.lawyer)
        ).options(joinedload(User.customer)
        ).filter(User.id == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> list[User]:
    """Get all users with pagination."""
    return db.query(User).options(
        joinedload(User.user_roles)
                ).options(joinedload(User.lawyer)
                ).options(joinedload(User.customer)
                ).offset(skip).limit(limit).all()


def update_user(db: Session, user_id: int, user_update: UserUpdate) -> User | None:
    """Update user information."""
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None

    update_data = user_update.model_dump(exclude_unset=True)

    # Handle password hashing if password is being updated
    if update_data.get("password"):
        update_data["password"] = get_password_hash(update_data["password"])

    for field, value in update_data.items():
        #only update the fields that are not None
        if value is not None:
            if field == "email":
                value = value.lower()
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


def verify_user(user: User) -> dict[str, Any]:
    # Check if user is active
    if user.status != "Active":
        logger.error(f"User {user.id} is not active")
        # message : "Your account is not active. Please contact support."
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=[
                {
                    "status": False,
                    "message": "Incorrect email or password"
                }
            ]
        )

    if user.lawyer:
        if user.lawyer.status != "Active":
            logger.error(f"Expert {user.lawyer.id} is not active")
            # message : "Your account is not active. Please contact support."
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=[
                    {
                        "status": False,
                        "message": "Incorrect email or password"
                    }
                ]
            )

    if user.customer:
        if user.customer.status != "Active":
            logger.error(f"Customer {user.customer.id} is not active")
            # message : "Your account is not active. Please contact support."
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=[
                    {
                        "status": False,
                        "message": "Incorrect email or password"
                    }
                ]
            )

    role_ids = [user_role.role_id for user_role in user.user_roles]
    role_codes = [UserRoleEnum.from_id(role_id).display_name for role_id in role_ids]
    if len(role_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=[
                {
                    "status": False,
                    "message": "User has no role assigned. Please contact support."
                }
            ]
        )

    data: dict[str, Any] = {"sub": str(user.id)}
    data["role"] = role_codes[0]
    data["available_roles"] = role_codes
    data["lawyer"] = (
        {
            "id": user.lawyer.id,
            "reg_no": user.lawyer.reg_no,
            "photo_url": user.lawyer.photo_url,
        }
        if user.lawyer
        else None
    )
    data["customer"] = (
        {
            "id": user.customer.id,
        }
        if user.customer
        else None
    )

    return data


def verify_payload_get_token_record(
    db: Session,
    request_token: str,
    token_payload: dict[str, Any],
    token_type: str | None = None,
    encrypted_payload: bool | None = False,
    error_detail: list[dict[str, Any]] | None = None,
    token_expiry_minutes: int | None = settings.SIMPLE_AUTH_TOKEN_EXPIRE_MINUTES,
    ) -> SimpleAuthToken | None:
    """Verify a payload and get the token record."""

    from app.db.services.simple_auth_token import get_simple_auth_token_by_id
    from app.utils.encryption import decrypt_id
    from datetime import datetime, timedelta, timezone
    
    if token_type:
        token_type_value = token_payload.get("type")
        if token_type_value != token_type:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

    if token_expiry_minutes is None:
        logger.error("token_expiry_minutes is None")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

    if encrypted_payload:
        auth_token_id_encrypted = token_payload.get("simple_auth_token_id")
        if not auth_token_id_encrypted:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)
        simple_auth_token_id = int(decrypt_id(auth_token_id_encrypted))
        if not simple_auth_token_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)
    else:
        simple_auth_token_id = token_payload.get("simple_auth_token_id")
        if not simple_auth_token_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

    token_record = None
    if simple_auth_token_id is not None:
        try:
            token_record = get_simple_auth_token_by_id(
                db, int(str(simple_auth_token_id))
            )
        except (TypeError, ValueError) as e:
            logger.error(f"Exception in get_simple_auth_token_by_id : {e}")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)
    if not token_record or token_record.token != request_token:
        logger.error("token_record is None or token_record.token != request_token")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

    token_created_at = getattr(token_record, "created_at", None)
    if token_created_at is None:
        logger.error("token_created_at is None")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)
    if token_created_at.tzinfo is None:
        logger.error("token_created_at.tzinfo is None")
        token_created_at = token_created_at.replace(tzinfo=timezone.utc)
    created_at_expiry = token_created_at + timedelta(
        minutes=token_expiry_minutes
    )
    if datetime.now(timezone.utc) > created_at_expiry:
        logger.error("datetime.now(timezone.utc) > created_at_expiry")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)

    if token_record.user.status != "Active":
        logger.error("token_record.user.status != Active")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_detail)
    
    return token_record


def generate_engage_link(db: Session, user: User, case: Case) -> str:
    """
    Generate an engage link for the user.

    Args:
        db: Database session
        user: User (customer)
        case: Case
        law_firm: LawFirm
    """
    from app.core.config import settings
    from app.db.services.simple_auth_token import create_simple_auth_token
    from app.core.security import create_password_token
    from app.utils.encryption import encrypt_id
    
    simple_auth_token_expire_minutes = settings.SIMPLE_AUTH_TOKEN_EXPIRE_MINUTES

    simple_auth_token_record = create_simple_auth_token(
        db=db,
        user_id=int(user.id),
        token=None,
    )

    token_payload = {
        "sub": (encrypt_id(str(user.id))),
        "case_id": encrypt_id(str(case.id)),
        "simple_auth_token_id": encrypt_id(str(simple_auth_token_record.id)),
    }
    engage_token = create_password_token(
        data=token_payload,
        token_type="engage_token",
        expire_minutes=simple_auth_token_expire_minutes,
    )
    simple_auth_token_url = f"{settings.ENGAGE_AUTH_URL}/{engage_token}"

    simple_auth_token_record.token = engage_token
    db.commit()
    return simple_auth_token_url
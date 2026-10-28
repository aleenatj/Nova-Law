"""Dependencies for FastAPI endpoints."""

import uuid
from collections.abc import Callable, Generator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models import User
from app.utils.encryption import decrypt_id, encrypt_id


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user_dependency() -> Callable:
    """Get current authenticated user."""
    from app.core.security import get_current_active_user

    return get_current_active_user


def get_current_user_id(
    current_user: Annotated[User, Depends(get_current_user_dependency)],
) -> int:
    """Get current user ID."""
    return int(current_user.id)


def get_encrypted_user_id(
    current_user: Annotated[User, Depends(get_current_user_dependency)],
) -> str:
    """Get encrypted current user ID."""
    encrypted = encrypt_id(str(current_user.id))
    if encrypted is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to encrypt user ID",
        )
    return encrypted


def decrypt_user_id(encrypted_id: str) -> int:
    """Decrypt user ID from encrypted string."""
    def _validate_decrypted(decrypted: str | None) -> int:
        if decrypted is None:
            raise ValueError("Invalid encrypted ID")
        return int(decrypted)

    try:
        decrypted = decrypt_id(encrypted_id)
        return _validate_decrypted(decrypted)
    except (ValueError, TypeError) as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid user ID format"
        ) from err


def get_decrypted_user_id(encrypted_id: str) -> int:
    """Get decrypted user ID from encrypted string."""
    return decrypt_user_id(encrypted_id)


def validate_user_access(
    current_user: Annotated[User, Depends(get_current_user_dependency)],
    target_user_id: int,
) -> None:
    """Validate that current user can access target user's data."""
    if int(current_user.id) != target_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only access your own data.",
        )


def validate_user_access_by_encrypted_id(
    current_user: Annotated[User, Depends(get_current_user_dependency)],
    encrypted_user_id: str,
) -> int:
    """Validate user access using encrypted user ID."""
    target_user_id = decrypt_user_id(encrypted_user_id)
    validate_user_access(current_user, target_user_id)
    return target_user_id


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def get_pagination_params(
    skip: int = 0,
    limit: int = 100,
) -> tuple[int, int]:
    """Get pagination parameters with validation."""
    skip = max(skip, 0)
    if limit < 1 or limit > 1000:
        limit = 100

    return skip, limit

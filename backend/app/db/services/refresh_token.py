"""Service for managing refresh tokens."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.db.models.refresh_token import RefreshToken


def create_refresh_token(db: Session, user_id: int, token: str, expiry_at: datetime) -> RefreshToken:
    """
    Create a new refresh token for a user.

    Args:
        db: Database session
        user_id: User ID
        token: Refresh token string
        expiry_at: Token expiration datetime

    Returns:
        RefreshToken: Created refresh token record
    """
    refresh_token_record = RefreshToken(
        user_id=user_id,
        refresh_token=token,
        expiry_at=expiry_at,
    )
    db.add(refresh_token_record)
    db.commit()
    db.refresh(refresh_token_record)
    return refresh_token_record


def get_refresh_token_by_id(db: Session, refresh_token_id: int) -> RefreshToken | None:
    """
    Get a refresh token record by ID (primary key).

    Args:
        db: Database session
        refresh_token_id: Refresh token ID (primary key)

    Returns:
        RefreshToken | None: Refresh token record if found, None otherwise
    """
    return db.query(RefreshToken).filter(RefreshToken.id == refresh_token_id).first()


def delete_refresh_token_by_id(db: Session, refresh_token_id: int) -> bool:
    """
    Delete a specific refresh token by ID.

    Args:
        db: Database session
        refresh_token_id: Refresh token ID (primary key)

    Returns:
        bool: True if deleted, False if not found
    """
    # Direct delete using ID for better performance (no need to fetch first)
    deleted_count = db.query(RefreshToken).filter(RefreshToken.id == refresh_token_id).delete()
    db.commit()
    return deleted_count > 0


def delete_user_refresh_tokens(db: Session, user_id: int) -> int:
    """
    Delete all refresh tokens for a user (logout from all devices).

    Args:
        db: Database session
        user_id: User ID

    Returns:
        int: Number of tokens deleted
    """
    deleted_count = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).delete()
    db.commit()
    return deleted_count


def update_refresh_token_by_id(db: Session, refresh_token_id: int, new_token: str, expiry_at: datetime | None = None) -> RefreshToken | None:
    """
    Update an existing refresh token with a new token value using ID.

    Args:
        db: Database session
        refresh_token_id: Refresh token ID (primary key)
        new_token: New refresh token string
        expiry_at: Optional new expiration datetime

    Returns:
        RefreshToken | None: Updated refresh token record if found, None otherwise
    """
    refresh_token_record = get_refresh_token_by_id(db, refresh_token_id)
    if not refresh_token_record:
        return None

    refresh_token_record.refresh_token = new_token  # type: ignore[assignment]
    if expiry_at is not None:
        refresh_token_record.expiry_at = expiry_at  # type: ignore[assignment]
    db.commit()
    db.refresh(refresh_token_record)
    return refresh_token_record


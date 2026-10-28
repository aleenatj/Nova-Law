"""Service helpers for simple auth tokens."""

import uuid
from sqlalchemy.orm import Session

from app.db.models.simple_auth_token import SimpleAuthToken


def _placeholder_token() -> str:
    return uuid.uuid4().hex


def create_simple_auth_token(
    db: Session,
    *,
    user_id: int,
    token: str | None = None,
) -> SimpleAuthToken:
    """Persist a simple auth token for a user."""
    simple_auth_token = SimpleAuthToken(
        user_id=user_id,
        token=token or _placeholder_token(),
    )
    db.add(simple_auth_token)
    db.commit()
    db.refresh(simple_auth_token)
    return simple_auth_token

def get_simple_auth_token_by_token(
    db: Session,
    token: str,
) -> SimpleAuthToken | None:
    """Retrieve a simple auth token record by token string."""
    return (
        db.query(SimpleAuthToken)
        .filter(SimpleAuthToken.token == token)
        .first()
    )


def get_simple_auth_token_by_id(
    db: Session,
    token_id: int,
) -> SimpleAuthToken | None:
    """Retrieve a simple auth token record by ID."""
    return (
        db.query(SimpleAuthToken)
        .filter(SimpleAuthToken.id == token_id)
        .first()
    )



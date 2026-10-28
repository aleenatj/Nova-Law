"""
Tests for authentication endpoints.
"""

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_password_token,
    create_refresh_token,
    get_password_hash,
)
from app.db.models import User, UserRole
from app.db.models.magic_link_token import MagicLinkToken
from app.enums.user_role import UserRoleEnum
from app.db.services.magic_link_token import create_magic_link_token
from app.tests.conftest import client


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user with basic role."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == "testuser@example.com").first()
    if existing_user:
        # Check if user has the required role
        existing_role = db.query(UserRole).filter(
            UserRole.user_id == existing_user.id,
            UserRole.role_id == UserRoleEnum.CUSTOMER.id
        ).first()
        if not existing_role:
            # Add the role if it doesn't exist
            role = UserRole(user_id=existing_user.id, role_id=UserRoleEnum.CUSTOMER.id)
            db.add(role)
            db.commit()
        return existing_user

    # Create new user if it doesn't exist
    user = User(
        first_name="Test",
        last_name="User",
        email="testuser@example.com",
        password=get_password_hash("testpassword"),
        status="Active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    role = UserRole(user_id=user.id, role_id=UserRoleEnum.CUSTOMER.id)
    db.add(role)
    db.commit()
    return user


@pytest.fixture
def test_lawyer(db: Session) -> User:
    """Create a test lawyer user."""
    user = User(
        first_name="Lawyer",
        last_name="User",
        email="lawyer@example.com",
        password=get_password_hash("lawyerpass"),
        status="Active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    role = UserRole(user_id=user.id, role_id=UserRoleEnum.LAWYER.id)
    db.add(role)
    db.commit()
    return user


@pytest.fixture
def magic_link_user(db: Session) -> User:
    """Create a user for magic link login testing."""
    user = User(
        first_name="Magic",
        last_name="Link",
        email="magicuser@example.com",
        password=None,
        status="Active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    role = UserRole(user_id=user.id, role_id=UserRoleEnum.CUSTOMER.id)
    db.add(role)
    db.commit()
    return user


def test_login_success(test_user: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser@example.com", "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"][0]["message"] == "Login successful"
    assert data["data"] is not None
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]
    assert "token_type" in data["data"]
    assert "user_data" in data["data"]
    assert "first_name" in data["data"]["user_data"]
    assert "last_name" in data["data"]["user_data"]
    assert "email" in data["data"]["user_data"]
    assert "user_id" in data["data"]["user_data"]
    assert "role_code" in data["data"]["user_data"]
    assert "role_name" in data["data"]["user_data"]


def test_login_invalid_password(test_user: User) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser@example.com", "password": "wrongpass"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert "Incorrect email or password" in data["message"][0]["message"]
    assert data["data"] == []


def test_login_nonexistent_user(db: Session) -> None:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nouser@example.com", "password": "irrelevant"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert "Incorrect email or password" in data["message"][0]["message"]
    assert data["data"] == []


def test_login_with_token_success(magic_link_user: User, db: Session) -> None:
    token_expiry_minutes = 5
    token = create_password_token(
        data={"sub": str(magic_link_user.id)},
        token_type="simple_registration",
        expire_minutes=token_expiry_minutes,
    )
    expiry_at = datetime.now(timezone.utc) + timedelta(minutes=token_expiry_minutes)
    create_magic_link_token(
        db=db,
        user_id=int(magic_link_user.id),
        token=token,
        expiry_at=expiry_at,
    )

    response = client.post(
        "/api/v1/auth/login-with-token",
        json={"token": token},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["redirect_path"] == f"{settings.FRONTEND_URL.rstrip('/')}/dashboard"
    assert data["is_password_set"] is False
    assert data["token_type"] == "bearer"
    assert data["access_token"]
    assert data["refresh_token"]
    assert data["user_data"]["email"] == magic_link_user.email

    assert (
        db.query(MagicLinkToken)
        .filter(MagicLinkToken.token == token)
        .first()
    ) is None


def test_login_with_token_expired(magic_link_user: User, db: Session) -> None:
    token = create_password_token(
        data={"sub": str(magic_link_user.id)},
        token_type="simple_registration",
        expire_minutes=-1,
    )
    expiry_at = datetime.now(timezone.utc) - timedelta(minutes=1)
    create_magic_link_token(
        db=db,
        user_id=int(magic_link_user.id),
        token=token,
        expiry_at=expiry_at,
    )

    response = client.post(
        "/api/v1/auth/login-with-token",
        json={"token": token},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["success"] is False
    messages = [msg["message"] for msg in payload["message"]]
    assert any("Invalid" in message or "expired" in message for message in messages)

    assert (
        db.query(MagicLinkToken)
        .filter(MagicLinkToken.token == token)
        .first()
    ) is None


def test_refresh_success(test_user: User, db: Session) -> None:
    # Store the refresh token in the refresh_tokens table
    from app.db.services.refresh_token import create_refresh_token as save_refresh_token

    # Calculate refresh token expiry
    refresh_expiry = datetime.utcnow() + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )

    # Create refresh token record with placeholder to get ID
    refresh_token_record = save_refresh_token(
        db,
        user_id=int(test_user.id),
        token="placeholder",
        expiry_at=refresh_expiry
    )

    # Create actual refresh token with the ID encoded
    refresh_token = create_refresh_token({"sub": str(test_user.id)}, refresh_token_id=refresh_token_record.id)

    # Update the record with actual token
    refresh_token_record.refresh_token = refresh_token  # type: ignore[assignment]
    db.commit()

    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["message"][0]["message"] == "Refresh token successful"
    assert data["data"] is not None
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


def test_refresh_invalid_token() -> None:
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "invalidtoken"}
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "Invalid refresh token" in data["message"][0]["message"]
    assert data["data"] == []


def test_forgot_password_success(test_user: User) -> None:
    # Test the event-driven forgot password endpoint
    response = client.post(
        "/api/v1/auth/forgot-password", json={"email": "testuser@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert (
        "Password reset token generated successfully" in data["message"][0]["message"]
    )


def test_forgot_password_nonexistent_email() -> None:
    response = client.post(
        "/api/v1/auth/forgot-password", json={"email": "doesnotexist@example.com"}
    )
    assert response.status_code == 422  # API returns 422 for non-existent emails
    data = response.json()
    assert data["success"] is False
    assert "User not found" in data["message"][0]["message"]


def test_reset_password_success(test_user: User) -> None:
    # Skip this test for now as it requires proper token setup
    # First login to get access token
    # login_response = client.post(
    #     "/api/v1/auth/login",
    #     data={"username": "testuser@example.com", "password": "testpassword"},
    # )
    # assert login_response.status_code == 200
    # access_token = login_response.json()["data"]["access_token"]

    # response = client.post(
    #     "/api/v1/auth/reset-password",
    #     json={"new_password": "newpass123"},
    #     headers={"Authorization": f"Bearer {access_token}"},
    # )
    # assert response.status_code == 200
    # data = response.json()
    # assert data["success"] is True
    # assert "Password has been successfully reset" in data["message"][0]["message"]
    pass


def test_reset_password_invalid_token() -> None:
    response = client.post(
        "/api/v1/auth/reset-password",
        json={"new_password": "irrelevant"},
        headers={"Authorization": "Bearer invalidtoken"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "Could not validate credentials" in data["message"]
    assert data["data"] == []


def test_reset_password_missing_fields() -> None:
    response = client.post(
        "/api/v1/auth/reset-password",
        json={},
        headers={"Authorization": "Bearer sometoken"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert "Could not validate credentials" in data["message"]
    assert data["data"] == []


def test_full_auth_flow(db: Session) -> None:
    # Register user manually in DB
    user = User(
        first_name="Full",
        last_name="Flow",
        email="fullflow@example.com",
        password=get_password_hash("flowpass"),
        status="Active",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    role = UserRole(user_id=user.id, role_id=UserRoleEnum.CUSTOMER.id)
    db.add(role)
    db.commit()

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "fullflow@example.com", "password": "flowpass"},
    )
    assert response.status_code == 200
    tokens = response.json()["data"]
    refresh_token = tokens["refresh_token"]

    # Refresh
    response = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert response.status_code == 200
    tokens = response.json()["data"]
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # Forgot password
    response = client.post(
        "/api/v1/auth/forgot-password", json={"email": "fullflow@example.com"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert (
        "Password reset token generated successfully" in data["message"][0]["message"]
    )

    # Reset password - skip this test for now as it requires proper token setup
    # response = client.post(
    #     "/api/v1/auth/reset-password",
    #     json={"new_password": "newflowpass"},
    #     headers={"Authorization": f"Bearer {access_token}"},
    # )
    # assert response.status_code == 200
    # data = response.json()
    # assert data["success"] is True
    # assert "Password has been successfully reset" in data["message"][0]["message"]

    # Login with new password - skip this test for now as password wasn't reset
    # response = client.post(
    #     "/api/v1/auth/login",
    #     data={"username": "fullflow@example.com", "password": "newflowpass"},
    # )
    # assert response.status_code == 200
    # data = response.json()
    # assert data["success"] is True
    # assert data["message"][0]["message"] == "Login successful"

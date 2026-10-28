"""
Comprehensive tests for password change functionality.

This file contains both service-level tests (testing the database service function directly)
and API endpoint tests (testing the HTTP endpoint with authentication).
"""

import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.models import User, UserRole
from app.db.services.user import change_user_password
from app.enums.user import StatusEnum
from app.enums.user_role import UserRoleEnum
from app.main import app

client = TestClient(app)


@pytest.fixture
def test_user(db: Session) -> User:
    """Create a test user with customer role."""
    # Use timestamp to ensure uniqueness
    timestamp = int(time.time() * 1000)  # Use milliseconds for better uniqueness
    user = User(
        first_name="Test",
        last_name="User",
        email=f"test.{timestamp}@unit-test.com",
        password=get_password_hash("testpassword123"),
        status=StatusEnum.ACTIVE,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    role = UserRole(user_id=user.id, role_id=UserRoleEnum.CUSTOMER.id)
    db.add(role)
    db.commit()
    return user


@pytest.fixture
def auth_headers(test_user: User) -> dict[str, str]:
    """Create authentication headers for the test user."""
    # Create a real access token for the test user
    access_token = create_access_token({"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {access_token}"}


class TestPasswordChangeService:
    """Test cases for password change service function (direct database operations)."""

    def test_change_user_password_service(self, db: Session) -> None:
        """Test the password change service function directly."""
        # Create test user with unique email
        timestamp = int(time.time() * 1000)
        user = User(
            first_name="Test",
            last_name="User",
            email=f"test.{timestamp}@unit-test.com",
            password=get_password_hash("testpassword123"),
            status=StatusEnum.ACTIVE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Add user role
        role = UserRole(user_id=user.id, role_id=UserRoleEnum.CUSTOMER.id)
        db.add(role)
        db.commit()

        # Test password change
        result = change_user_password(
            db=db,
            user_id=int(user.id),
            current_password="testpassword123",
            new_password="newpassword456",
        )

        assert result is True

        # Verify the password was changed
        db.refresh(user)
        assert verify_password("newpassword456", user.password)  # type: ignore
        assert not verify_password("testpassword123", user.password)  # type: ignore

    def test_change_user_password_invalid_current_password(self, db: Session) -> None:
        """Test password change with invalid current password."""
        # Create test user with unique email
        timestamp = int(time.time() * 1000)
        user = User(
            first_name="Test",
            last_name="User",
            email=f"test2.{timestamp}@unit-test.com",
            password=get_password_hash("testpassword123"),
            status=StatusEnum.ACTIVE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Add user role
        role = UserRole(user_id=user.id, role_id=UserRoleEnum.CUSTOMER.id)
        db.add(role)
        db.commit()

        # Test password change with wrong current password
        result = change_user_password(
            db=db,
            user_id=int(user.id),
            current_password="wrongpassword",
            new_password="newpassword456",
        )

        assert result is False

        # Verify the password was not changed
        db.refresh(user)
        assert verify_password("testpassword123", user.password)  # type: ignore
        assert not verify_password("newpassword456", user.password)  # type: ignore

    def test_change_user_password_user_not_found(self, db: Session) -> None:
        """Test password change for non-existent user."""
        # Test password change for non-existent user
        result = change_user_password(
            db=db,
            user_id=99999,  # Non-existent user ID
            current_password="testpassword123",
            new_password="newpassword456",
        )

        assert result is False

    def test_change_user_password_complex_password(self, db: Session) -> None:
        """Test password change with complex password."""
        # Create test user with unique email
        timestamp = int(time.time() * 1000)
        user = User(
            first_name="Test",
            last_name="User",
            email=f"test3.{timestamp}@unit-test.com",
            password=get_password_hash("testpassword123"),
            status=StatusEnum.ACTIVE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Add user role
        role = UserRole(user_id=user.id, role_id=UserRoleEnum.CUSTOMER.id)
        db.add(role)
        db.commit()

        # Test password change with complex password
        complex_password = "ComplexP@ssw0rd!@#$%^&*()_+-=[]{}|;:,.<>?"
        result = change_user_password(
            db=db,
            user_id=int(user.id),
            current_password="testpassword123",
            new_password=complex_password,
        )

        assert result is True

        # Verify the complex password was stored correctly
        db.refresh(user)
        assert verify_password(complex_password, user.password)  # type: ignore
        assert not verify_password("testpassword123", user.password)  # type: ignore


class TestPasswordChangeAPI:
    """Test cases for password change API endpoint (HTTP requests with authentication)."""

    def test_change_password_success(self, db: Session) -> None:
        """Test successful password change via API endpoint."""
        # Create test user in the same database session with unique email
        timestamp = int(time.time() * 1000)
        user = User(
            first_name="Test",
            last_name="User",
            email=f"test.{timestamp}@unit-test.com",
            password=get_password_hash("testpassword123"),
            status=StatusEnum.ACTIVE,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        role = UserRole(user_id=user.id, role_id=UserRoleEnum.CUSTOMER.id)
        db.add(role)
        db.commit()

        # Create authentication headers
        access_token = create_access_token({"sub": str(user.id)})
        headers = {"Authorization": f"Bearer {access_token}"}

        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword456",
        }

        response = client.put(
            "/api/v1/user/change-password", json=password_data, headers=headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["message"]) == 1
        assert data["message"][0]["success"] is True
        assert data["message"][0]["message"] == "Password changed successfully"
        assert data["data"] == []

        # Verify the password was actually changed in the database
        db.refresh(user)
        assert verify_password("newpassword456", user.password)  # type: ignore
        assert not verify_password("testpassword123", user.password)  # type: ignore

    def test_change_password_invalid_current_password(
        self, db: Session, test_user: User, auth_headers: dict[str, str]
    ) -> None:
        """Test password change with invalid current password."""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newpassword456",
        }

        response = client.put(
            "/api/v1/user/change-password", json=password_data, headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid current password" in data["detail"]

        # Verify the password was not changed
        db.refresh(test_user)
        assert verify_password("testpassword123", test_user.password)  # type: ignore

    def test_change_password_same_password(
        self, db: Session, test_user: User, auth_headers: dict[str, str]
    ) -> None:
        """Test password change with same password as current."""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "testpassword123",
        }

        response = client.put(
            "/api/v1/user/change-password", json=password_data, headers=auth_headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "New password must be different from current password" in data["detail"]

        # Verify the password was not changed
        db.refresh(test_user)
        assert verify_password("testpassword123", test_user.password)  # type: ignore

    def test_change_password_short_new_password(
        self, db: Session, test_user: User, auth_headers: dict[str, str]
    ) -> None:
        """Test password change with new password that's too short."""
        password_data = {"current_password": "testpassword123", "new_password": "short"}

        response = client.put(
            "/api/v1/user/change-password", json=password_data, headers=auth_headers
        )

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "ensure this value has at least 8 characters" in str(data)

    def test_change_password_missing_current_password(
        self, db: Session, test_user: User, auth_headers: dict[str, str]
    ) -> None:
        """Test password change with missing current password."""
        password_data = {"new_password": "newpassword456"}

        response = client.put(
            "/api/v1/user/change-password", json=password_data, headers=auth_headers
        )

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "field required" in str(data)

    def test_change_password_missing_new_password(
        self, db: Session, test_user: User, auth_headers: dict[str, str]
    ) -> None:
        """Test password change with missing new password."""
        password_data = {"current_password": "testpassword123"}

        response = client.put(
            "/api/v1/user/change-password", json=password_data, headers=auth_headers
        )

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "field required" in str(data)

    def test_change_password_unauthorized(self, db: Session) -> None:
        """Test password change without authentication."""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword456",
        }

        response = client.put("/api/v1/user/change-password", json=password_data)

        assert response.status_code == 401
        data = response.json()
        assert "Bearer token missing" in data["detail"]

    def test_change_password_user_not_found(self, db: Session) -> None:
        """Test password change for non-existent user."""
        # Create a token for a non-existent user
        access_token = create_access_token({"sub": "99999"})
        headers = {"Authorization": f"Bearer {access_token}"}

        password_data = {
            "current_password": "testpassword123",
            "new_password": "newpassword456",
        }

        response = client.put(
            "/api/v1/user/change-password", json=password_data, headers=headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "Invalid current password or user not found" in data["detail"]

    def test_change_password_complex_new_password(
        self, db: Session, test_user: User, auth_headers: dict[str, str]
    ) -> None:
        """Test password change with complex new password."""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "ComplexP@ssw0rd!2024",
        }

        response = client.put(
            "/api/v1/user/change-password", json=password_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 200
        assert data["message"] == "Password changed successfully"

        # Verify the complex password was stored correctly
        db.refresh(test_user)
        assert verify_password("ComplexP@ssw0rd!2024", test_user.password)  # type: ignore
        assert not verify_password("testpassword123", test_user.password)  # type: ignore

    def test_change_password_empty_strings(
        self, db: Session, test_user: User, auth_headers: dict[str, str]
    ) -> None:
        """Test password change with empty string passwords."""
        password_data = {"current_password": "", "new_password": ""}

        response = client.put(
            "/api/v1/user/change-password", json=password_data, headers=auth_headers
        )

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "ensure this value has at least 8 characters" in str(data)

    def test_change_password_special_characters(
        self, db: Session, test_user: User, auth_headers: dict[str, str]
    ) -> None:
        """Test password change with special characters in new password."""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "P@ssw0rd!@#$%^&*()_+-=[]{}|;:,.<>?",
        }

        response = client.put(
            "/api/v1/user/change-password", json=password_data, headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == 200
        assert data["message"] == "Password changed successfully"

        # Verify the special character password was stored correctly
        db.refresh(test_user)
        assert verify_password("P@ssw0rd!@#$%^&*()_+-=[]{}|;:,.<>?", test_user.password)  # type: ignore
        assert not verify_password("testpassword123", test_user.password)  # type: ignore

"""
Tests for the permission system.
"""

from app.core.permissions import (
    _match_endpoint_pattern,
    check_any_permission,
    has_permission,
)


class TestPermissions:
    """Test cases for permission system."""

    def test_customer_permissions(self) -> None:
        """Test customer role permissions."""
        # Customer should have access to their own profile
        assert has_permission("Customer", "/api/v1/user/me", "GET")
        assert not has_permission("Customer", "/api/v1/user/me", "POST")

        # Customer should not have access to lawyer-specific endpoints
        assert not has_permission("Customer", "/lawyers/123", "GET")
        assert not has_permission("Customer", "/lawyers/456", "PUT")

    def test_lawyer_permissions(self) -> None:
        """Test lawyer role permissions."""
        # Lawyer should have access to their own profile
        assert has_permission("Lawyer", "/api/v1/user/me", "GET")
        assert not has_permission("Lawyer", "/api/v1/user/me", "POST")

        # Lawyer should have access to timeline
        assert has_permission("Lawyer", "/api/v1/timeline", "GET")
        assert not has_permission("Lawyer", "/api/v1/timeline", "POST")

    def test_nova_navigator_permissions(self) -> None:
        """Test nova_navigator role permissions."""
        # Nova navigator should have access to navigator-specific endpoints
        assert has_permission("Navigator", "/api/v1/navigator", "POST")
        assert has_permission("Navigator", "/api/v1/navigator/123", "PUT")
        assert has_permission("Navigator", "/api/v1/navigator", "GET")
        assert has_permission("Navigator", "/api/v1/navigator/456", "GET")

    def test_check_any_permission(self) -> None:
        """Test check_any_permission function."""
        user_roles = ["Customer", "Lawyer"]

        # User with customer and lawyer roles should have access to customer endpoints
        assert check_any_permission(user_roles, "/api/v1/user/me", "GET")

        # User with customer and lawyer roles should have access to timeline
        assert check_any_permission(user_roles, "/api/v1/timeline", "GET")

        # User with customer and lawyer roles should not have access to navigator endpoints
        assert not check_any_permission(user_roles, "/api/v1/navigator", "POST")

    def test_endpoint_pattern_matching(self) -> None:
        """Test endpoint pattern matching."""
        # Exact matches
        assert _match_endpoint_pattern("/user/me", "/user/me")
        assert not _match_endpoint_pattern("/user/me", "/user/123")

        # Pattern matches with parameters
        assert _match_endpoint_pattern("/user/123", "/user/{user_id}")
        assert _match_endpoint_pattern("/user/456", "/user/{user_id}")
        assert _match_endpoint_pattern("/lawyers/789", "/lawyers/{lawyer_id}")
        assert _match_endpoint_pattern("/law-firms/101", "/law-firms/{lawfirm_id}")

        # Complex patterns
        assert _match_endpoint_pattern(
            "/user-roles/123/456", "/user-roles/{user_id}/{role_id}"
        )
        assert _match_endpoint_pattern(
            "/lawyer-law-firms/123/456", "/lawyer-law-firms/{lawyer_id}/{lawfirm_id}"
        )

        # Non-matches
        assert not _match_endpoint_pattern("/user/123/profile", "/user/{user_id}")
        assert not _match_endpoint_pattern("/user", "/user/{user_id}")

    def test_invalid_roles(self) -> None:
        """Test behavior with invalid roles."""
        # Invalid role should not have any permissions
        assert not has_permission("invalid_role", "/api/v1/user/me", "GET")
        assert not has_permission("", "/api/v1/user/me", "GET")
        # Note: None is not a valid role type, so we don't test it

    def test_invalid_endpoints(self) -> None:
        """Test behavior with invalid endpoints."""
        # Invalid endpoints should not have permissions
        assert not has_permission("Customer", "/invalid/endpoint", "GET")
        assert not has_permission("Lawyer", "/invalid/endpoint", "POST")
        assert not has_permission("Navigator", "/invalid/endpoint", "PUT")

    def test_method_specific_permissions(self) -> None:
        """Test method-specific permissions."""
        # Test that different methods have different permissions
        assert has_permission("Customer", "/api/v1/user/me", "GET")
        assert not has_permission("Customer", "/api/v1/user/me", "PUT")
        assert not has_permission("Customer", "/api/v1/user/me", "DELETE")

        # Navigator should have access to navigator endpoints
        assert has_permission("Navigator", "/api/v1/navigator/123", "PUT")
        assert has_permission("Navigator", "/api/v1/navigator/456", "GET")
        assert not has_permission("Navigator", "/api/v1/navigator/123", "DELETE")

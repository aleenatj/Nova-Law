"""
Permission system for Nova Law AI Backend.

This module defines the role-based access control (RBAC) system.
"""

import re

from app.config.permission.role_permission import PERMISSIONS

# Define available roles
ROLES = {"Customer", "Lawyer", "Navigator"}


def has_permission(role: str, endpoint: str, method: str) -> bool:
    """
    Check if a role has permission to access an endpoint with a specific method.

    Args:
        role: The user's role
        endpoint: The API endpoint path
        method: The HTTP method (GET, POST, PUT, DELETE, etc.)

    Returns:
        True if the role has permission, False otherwise
    """

    if role not in PERMISSIONS:
        return False

    role_permissions = PERMISSIONS[role]

    # Check exact match first
    if endpoint in role_permissions and method in role_permissions[endpoint]:
        return True

    # Check pattern matches (for endpoints with parameters like /users/{user_id})
    for pattern, allowed_methods in role_permissions.items():
        if _match_endpoint_pattern(endpoint, pattern) and method in allowed_methods:
            return True

    return False


def _match_endpoint_pattern(actual_endpoint: str, pattern: str) -> bool:
    """
    Check if an actual endpoint matches a pattern with parameters.

    Args:
        actual_endpoint: The actual endpoint path (e.g., "/users/123")
        pattern: The pattern to match against (e.g., "/users/{user_id}")

    Returns:
        True if the endpoint matches the pattern, False otherwise
    """
    # Convert pattern to regex
    regex_pattern = re.sub(r"\{[^}]+\}", r"[^/]+", pattern)
    regex_pattern = f"^{regex_pattern}$"

    return bool(re.match(regex_pattern, actual_endpoint))


def check_any_permission(user_roles: list[str], endpoint: str, method: str) -> bool:
    """
    Check if any of the user's roles have permission for the endpoint and method.

    Args:
        user_roles: List of user's roles
        endpoint: The API endpoint path
        method: The HTTP method

    Returns:
        True if any role has permission, False otherwise
    """
    for role in user_roles:
        if has_permission(role, endpoint, method):
            return True
    return False


def get_allowed_endpoints_for_role(role: str) -> dict[str, set[str]]:
    """
    Get all endpoints and methods allowed for a specific role.

    Args:
        role: The role to check

    Returns:
        Dictionary mapping endpoints to allowed HTTP methods
    """
    return PERMISSIONS.get(role, {})


def get_all_roles() -> set[str]:
    """
    Get all available roles.

    Returns:
        Set of all available roles
    """
    return ROLES.copy()

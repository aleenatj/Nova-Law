"""Custom validation utilities for the Nova Law AI application."""

import re
from datetime import date, datetime
from typing import Any, TypedDict

from email_validator import EmailNotValidError, validate_email
from fastapi import HTTPException, status
from pydantic import BaseModel


class PasswordValidationResult(TypedDict):
    is_valid: bool
    score: int
    feedback: list[str]
    requirements: dict[str, bool]


def validate_phone_number(phone: str) -> bool:
    """
    Validates phone number format for international numbers from all countries.
    Supports various formats including:
    - US/NANP: 1234567890, (123) 456-7890, 123-456-7890, +1 (123) 456-7890
    - International: +44 7123456789, +49 30 12345678, etc.
    - Various separators: spaces, dashes, parentheses

    Args:
        phone (str): Phone number to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not phone or not isinstance(phone, str):
        return False

    phone = phone.strip()

    if not re.match(r'^[\d\s\-\(\)\.\+]+$', phone):
        return False
    clean_phone = re.sub(r'[^\d+]', '', phone)

    if '+' in clean_phone:
        if not clean_phone.startswith('+') or clean_phone.count('+') > 1:
            return False

    # Extract digits only (ignore '+')
    digits_only = clean_phone.lstrip('+')

    # Reject if not numeric or all zeros
    if not digits_only.isdigit() or set(digits_only) == {'0'}:
        return False

    if clean_phone.startswith('+'):
        return 7 <= len(digits_only) <= 20
    else:
        return 10 <= len(digits_only) <= 20


def validate_email_format(email: str) -> bool:
    """Validate email format similar to Google/Gmail rules.

    Args:
        email (str): Email string to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        # First, basic email format validation
        valid = validate_email(email, check_deliverability=False)
        email = valid.email  # Get the normalized version

        # Gmail-style local part pattern (before @)
        # Allows: letters, numbers, dots, underscores
        # No consecutive dots, cannot start or end with dot
        local_part = email.split('@')[0]
        if not re.match(r"^[A-Za-z0-9](?!.*\.\.)[A-Za-z0-9._%+\-']*[A-Za-z0-9+]$", local_part):
            return False

        return True
    except EmailNotValidError:
        return False


def validate_url_format(url: str) -> bool:
    """
    Validates if the given string is a valid URL.

    Args:
        url (str): URL string to validate.

    Returns:
        bool: True if valid, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False

    # Simple regex for URL validation (http, https, ftp)
    url_regex = re.compile(
        r'^(https?|ftp)://'  # http://, https://, or ftp://
        r'(([A-Za-z0-9-]+\.)+[A-Za-z]{2,6})'  # domain...
        r'(:\d+)?'  # optional port
        r'(/[\w\-./?%&=]*)?'  # path
        r'$', re.IGNORECASE
    )
    return re.match(url_regex, url) is not None


def validate_password_strength(password: str) -> PasswordValidationResult:
    """Validate password strength and return detailed feedback.

    Args:
    ----
        password: Password string to validate

    Returns:
    -------
        Dict containing validation results and feedback

    """
    result: PasswordValidationResult = {
        "is_valid": True,
        "score": 0,
        "feedback": [],
        "requirements": {
            "min_length": False,
            "has_uppercase": False,
            "has_lowercase": False,
            "has_digit": False,
            "has_special": False,
        },
    }

    # Check length
    if len(password) < 8:
        result["feedback"].append("Password must be at least 8 characters long")
        result["is_valid"] = False
    else:
        result["score"] += 1

    # Check for uppercase
    if re.search(r"[A-Z]", password):
        result["requirements"]["has_uppercase"] = True
        result["score"] += 1
    else:
        result["feedback"].append("Password must contain at least one uppercase letter")
        result["is_valid"] = False

    # Check for lowercase
    if re.search(r"[a-z]", password):
        result["requirements"]["has_lowercase"] = True
        result["score"] += 1
    else:
        result["feedback"].append("Password must contain at least one lowercase letter")
        result["is_valid"] = False

    # Check for digits
    if re.search(r"\d", password):
        result["requirements"]["has_digit"] = True
        result["score"] += 1
    else:
        result["feedback"].append("Password must contain at least one digit")
        result["is_valid"] = False

    # Check for special characters
    # if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
    #     result["requirements"]["has_special"] = True
    #     result["score"] += 1
    # else:
    #     result["feedback"].append(
    #         "Password must contain at least one special character",
    #     )
    #     result["is_valid"] = False

    return result


def validate_json_schema(
    data: dict[str, Any],
    required_fields: list[str],
) -> dict[str, Any]:
    """Validate that required fields are present in JSON data.

    Args:
    ----
        data: JSON data to validate
        required_fields: List of required field names

    Returns:
    -------
        Dict containing validation results

    """
    result: dict[str, Any] = {
        "is_valid": True,
        "missing_fields": [],
        "extra_fields": [],
    }

    # Check for missing required fields
    for field in required_fields:
        if field not in data:
            result["missing_fields"].append(field)
            result["is_valid"] = False

    # Check for extra fields (optional)
    for field in data.keys():
        if field not in required_fields:
            result["extra_fields"].append(field)

    return result


def validate_date_range(
    start_date: str | date | datetime,
    end_date: str | date | datetime,
) -> bool:
    """Validate that start_date is before end_date.

    Args:
    ----
        start_date: Start date
        end_date: End date

    Returns:
    -------
        bool: True if valid range, False otherwise

    """
    try:
        # Convert to datetime objects if needed
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        return start_date < end_date
    except (ValueError, TypeError):
        return False


def sanitize_input(text: str, max_length: int | None = None) -> str:
    """Sanitize user input by removing potentially dangerous characters.

    Args:
    ----
        text: Input text to sanitize
        max_length: Maximum allowed length

    Returns:
    -------
        str: Sanitized text

    """
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove script tags
    text = re.sub(
        r"<script[^>]*>.*?</script>",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Remove null bytes
    text = text.replace("\x00", "")

    # Trim whitespace
    text = text.strip()

    # Limit length if specified
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def validate_event_payload(
    payload: dict[str, Any], required_keys: list[str | dict[str, list[str]]]
) -> dict[str, Any]:
    """
    Recursively validates that required keys are present and have values in the payload.

    Args:
        payload (Dict[str, Any]):
            The payload dictionary to validate.
            Example:
                {
                    "user_id": 1,
                    "user_info": {
                        "email": "test@example.com",
                        "name": "John"
                    },
                    "metadata": SomePydanticModel(...)
                }

        required_keys (List[Union[str, Dict[str, List[str]]]]):
            A list of required keys at the top level (as strings), or nested keys (as dicts).
            Supports nested structures and Pydantic/BaseModel objects.
            Example:
                [
                    "user_id",
                    {"user_info": ["email", "name"]},
                    {"metadata": ["created_at", "source"]}
                ]

    Returns:
        Dict[str, Any]: A dictionary with:
            - status (bool): True if all keys are present and non-empty, False otherwise.
            - missing (List[str]): List of keys that are missing entirely.
            - empty (List[str]): List of keys that are present but empty or null.
            - message (str): Summary message.

    Example:
        >>> validate_event_payload(
                payload={
                    "user_id": 1,
                    "user_info": {"email": "", "name": "Alice"},
                    "metadata": {"created_at": "2025-01-01", "source": None}
                },
                required_keys=[
                    "user_id",
                    {"user_info": ["email", "name"]},
                    {"metadata": ["created_at", "source"]}
                ]
            )
        {
            'status': False,
            'missing': [],
            'empty': ['user_info.email', 'metadata.source'],
            'message': "Missing: None, Empty: ['user_info.email', 'metadata.source']"
        }
    """
    missing_keys = []
    empty_keys = []

    for key in required_keys:
        if isinstance(key, str):
            if key not in payload:
                missing_keys.append(key)
            elif payload[key] in [None, "", [], {}]:
                empty_keys.append(key)

        elif isinstance(key, dict):
            for parent_key, nested_keys in key.items():
                if parent_key not in payload:
                    missing_keys.append(parent_key)
                    continue

                parent_value = payload[parent_key]

                # Convert BaseModel to dict for validation
                if isinstance(parent_value, BaseModel):
                    nested_payload = parent_value.dict()
                elif isinstance(parent_value, dict):
                    nested_payload = parent_value
                else:
                    # Not a valid structure to recurse into
                    empty_keys.append(parent_key)
                    continue

                nested_result = validate_event_payload(nested_payload, nested_keys)  # type: ignore[arg-type]
                missing_keys.extend(
                    [f"{parent_key}.{k}" for k in nested_result["missing"]]
                )
                empty_keys.extend([f"{parent_key}.{k}" for k in nested_result["empty"]])

    status = not (missing_keys or empty_keys)

    return {
        "status": status,
        "missing": missing_keys,
        "empty": empty_keys,
        "message": (
            "All required keys are present and non-empty."
            if status
            else f"Missing: {missing_keys or 'None'}, Empty: {empty_keys or 'None'}"
        ),
    }


def validate_order_params(
    order_by: str,
    order_dir: str,
    allowed_fields: set[str],
) -> None:
    """
    Validate order_by and order_dir parameters for list endpoints.

    Args:
        order_by: Field name to order by
        order_dir: Sort direction ("asc" or "desc")
        allowed_fields: Set of valid field names for ordering

    Raises:
        HTTPException: If order_by or order_dir are invalid

    Example:
        >>> validate_order_params(
                order_by="created_at",
                order_dir="desc",
                allowed_fields={"id", "created_at", "updated_at"}
            )
        # No exception raised

        >>> validate_order_params(
                order_by="invalid_field",
                order_dir="desc",
                allowed_fields={"id", "created_at"}
            )
        # Raises HTTPException with 400 status
    """
    # Validate order_by field
    if order_by not in allowed_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": f"Invalid order_by field: {order_by}. Valid fields: {', '.join(sorted(allowed_fields))}",
            },
        )

    # Validate order direction
    if order_dir.lower() not in ["asc", "desc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Order direction must be 'asc' or 'desc'",
            },
        )

import hashlib
import json
import re
import secrets
import uuid
from datetime import UTC, date, datetime
from typing import Any, cast

from app.core.config import settings
from app.db.models.lawyer import Lawyer
from app.schemas.v1.event import EventResponseData

# from fastapi_mail import FastMail, MessageSchema, MessageType

# Email service import removed to avoid circular import
# Use the new templated email system instead


def generate_uuid() -> str:
    """Generate a UUID string."""
    return str(uuid.uuid4())


def generate_short_id() -> str:
    """Generate a short ID for URLs."""
    return str(uuid.uuid4())[:8]


def hash_string(text: str) -> str:
    """Hash a string using SHA-256."""
    return hashlib.sha256(text.encode()).hexdigest()


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe storage."""
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Remove leading/trailing spaces and dots
    filename = filename.strip(". ")
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    return filename


def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.isoformat()


def format_expiry_time(expiry_minutes: int | float) -> dict[str, Any]:
    """
    Format expiry time in minutes to a human-readable format with appropriate unit.
    
    Args:
        expiry_minutes: Expiry time in minutes (must be in minutes, not hours or seconds)
                        Example: 30 (for 30 minutes), 60 (for 1 hour), 90 (for 1 hour 30 minutes), 1440 (for 24 hours)
        
    Returns:
        Dictionary with expiry information:
        - expiry_value: The numeric value (for backward compatibility)
        - expiry_unit: The unit string (for backward compatibility)
        - hours: Number of hours (None if < 60 minutes)
        - minutes: Number of minutes (None if exactly divisible by 60)
        - formatted: Human-readable formatted string
    
    Examples:
        # Input must be in minutes:
        format_expiry_time(30) -> {"expiry_value": 30, "expiry_unit": "minutes", "hours": None, "minutes": 30, "formatted": "30 minutes"}
        format_expiry_time(60) -> {"expiry_value": 1, "expiry_unit": "hour", "hours": 1, "minutes": None, "formatted": "1 hour"}
        format_expiry_time(90) -> {"expiry_value": 1.5, "expiry_unit": "hours", "hours": 1, "minutes": 30, "formatted": "1 hour 30 minutes"}
        format_expiry_time(120) -> {"expiry_value": 2, "expiry_unit": "hours", "hours": 2, "minutes": None, "formatted": "2 hours"}
        
        # If you have time in hours, convert to minutes first:
        # expiry_hours = 1.5
        # expiry_minutes = expiry_hours * 60  # Convert to minutes: 90
        # format_expiry_time(expiry_minutes)  # Pass 90, not 1.5
    """
    expiry_minutes = int(expiry_minutes)
    
    days = 0
    if expiry_minutes >= 60:
        hours = expiry_minutes // 60
        minutes = expiry_minutes % 60
        
        # Build formatted string
        parts = []
        if hours > 0:
            if hours > 24:
                days = hours // 24
                remaining_hours = hours % 24
                if days == 1:
                    parts.append(f"{days} day")
                else:
                    parts.append(f"{days} days")
                if remaining_hours == 1:
                    parts.append(f"{remaining_hours} hour")
                elif remaining_hours > 0:
                    parts.append(f"{remaining_hours} hours")
            else:
                if hours == 1:
                    parts.append(f"{hours} hour")
                else:
                    parts.append(f"{hours} hours")
        if minutes > 0:
            parts.append(f"{minutes} {'minute' if minutes == 1 else 'minutes'}")
        formatted = " ".join(parts)
        
        # For backward compatibility
        expiry_value = hours if minutes == 0 else expiry_minutes / 60
        expiry_unit = "hour" if hours == 1 and minutes == 0 else "hours"
        
        return {
            "expiry_value": expiry_value,
            "expiry_unit": expiry_unit,
            "hours": hours,
            "minutes": minutes if minutes > 0 else None,
            "days": days,
            "formatted": formatted,
        }
    else:
        expiry_value = expiry_minutes
        expiry_unit = "minute" if expiry_value == 1 else "minutes"
        
        return {
            "expiry_value": expiry_value,
            "expiry_unit": expiry_unit,
            "hours": None,
            "minutes": expiry_value,
            "formatted": f"{expiry_value} {expiry_unit}",
        }


def parse_timestamp(timestamp: str) -> datetime:
    """Parse ISO timestamp string to datetime."""
    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def safe_json_dumps(obj: Any) -> str:
    """Safely serialize object to JSON string."""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return str(obj)


def safe_json_loads(text: str) -> Any:
    """Safely deserialize JSON string."""
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return None


def _parse_json_field(value: Any, default: Any = None) -> Any:
    """Parse a value that may be a JSON string or already a dict/list (e.g. from ORM JSON column)."""
    if default is None:
        default = []
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, (str, bytes, bytearray)):
        return json.loads(value)
    return default


def _ensure_list(val: Any) -> list[Any]:
    """Return a list from a value that may be None, a list, or a JSON string."""
    parsed = _parse_json_field(val, default=[])
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        return list(parsed.values())
    return []


def extract_emails(text: str) -> list[str]:
    """Extract email addresses from text."""
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    return re.findall(email_pattern, text)


def extract_urls(text: str) -> list[str]:
    """Extract URLs from text."""
    url_pattern = r"https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?"
    return re.findall(url_pattern, text)


def validate_email(email: str) -> bool:
    """Validate email format."""
    email_pattern = r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$"
    return bool(re.match(email_pattern, email))


def validate_password_strength(password: str) -> dict[str, Any]:
    """Validate password strength."""
    result: dict[str, Any] = {"valid": True, "errors": [], "warnings": []}

    if len(password) < 8:
        result["valid"] = False
        result["errors"].append("Password must be at least 8 characters long")

    if not re.search(r"[A-Z]", password):
        result["warnings"].append(
            "Password should contain at least one uppercase letter",
        )

    if not re.search(r"[a-z]", password):
        result["warnings"].append(
            "Password should contain at least one lowercase letter",
        )

    if not re.search(r"\d", password):
        result["warnings"].append("Password should contain at least one number")

    # if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
    #     result["warnings"].append(
    #         "Password should contain at least one special character",
    #     )

    return result


def chunk_list(lst: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split a list into chunks of specified size."""
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_list(lst: list[list[Any]]) -> list[Any]:
    """Flatten a list of lists."""
    return [item for sublist in lst for item in sublist]


def remove_duplicates(lst: list[Any]) -> list[Any]:
    """Remove duplicates from a list while preserving order."""
    seen: set[Any] = set()
    result: list[Any] = []
    for x in lst:
        if x not in seen:
            seen.add(x)
            result.append(x)
    return result


def get_nested_value(data: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    """Get nested dictionary value using key path."""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def set_nested_value(data: dict[str, Any], keys: list[str], value: Any) -> None:
    """Set nested dictionary value using key path."""
    current = data
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    current[keys[-1]] = value


def deep_merge(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries."""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def replace_placeholders(obj: Any, values: dict[str, Any], errors: list[str]) -> Any:
    """Replace placeholders in an object with values and collect missing key errors.

    Additionally, for the variables 'customer_name' and 'username' in values, if either ends with a dot,
    replace the trailing dot with a space.
    """
    # Preprocess values['customer_name'] and values['username'], if present and string ending with '.'
    new_values = values
    for key in ("customer_name", "username"):
        if (
            isinstance(values, dict)
            and key in values
            and isinstance(values[key], str)
            and values[key].endswith(".")
        ):
            if new_values is values:
                new_values = values.copy()
            new_values[key] = values[key][:-1] + " "

    if isinstance(obj, list):
        return [replace_placeholders(item, new_values, errors) for item in obj]

    if isinstance(obj, dict):
        new_obj: dict[Any, Any] = {}
        for key, val in obj.items():
            # Check if key itself is a placeholder
            if isinstance(key, str) and key.startswith("{") and key.endswith("}"):
                key_name = key[1:-1]
                if key_name not in new_values:
                    errors.append(f"Missing key in values for placeholder: {key_name}")
                    new_key = key  # Keep placeholder if missing
                else:
                    new_key = new_values[key_name]
            else:
                new_key = key

            new_obj[new_key] = replace_placeholders(val, new_values, errors)
        return new_obj

    if isinstance(obj, str) and obj.startswith("{") and obj.endswith("}"):
        key_name = obj[1:-1]
        if key_name not in new_values:
            errors.append(f"Missing key in values for placeholder: {key_name}")
            return obj  # Keep placeholder if missing
        value = new_values[key_name]
        if (
            value == ""
            or value is None
            or (isinstance(value, str) and not value.strip())
        ):
            return None  # Set to null if empty (no error message)
        return value

    return obj


def extract_status_messages(
    response_dict: dict[str, EventResponseData],
) -> tuple[bool, list[dict[str, str]]]:
    messages: list[dict[str, Any]] = []
    success = True
    if not response_dict:
        return success, messages
    success = any(value.success for value in response_dict.values())

    for value in response_dict.values():
        # Ensure it's a proper EventResponseData object
        if isinstance(value, EventResponseData):
            if not hasattr(value, "should_display") or (value.should_display and value.should_display):
                messages.append({"success": value.success, "message": value.message})
    return success, messages


def format_time_duration(hours: float) -> str:
    if hours < 1:
        return "Less than 1 hour"

    # Calculate days and remaining hours
    days = int(hours // 24)
    remaining_hours = int(hours % 24)

    if days == 0:
        # Less than 24 hours
        if remaining_hours == 1:
            return "1 hour"
        else:
            return f"{remaining_hours} hours"
    elif days == 1:
        # Exactly 1 day or 1 day + some hours
        if remaining_hours == 0:
            return "1 day"
        elif remaining_hours == 1:
            return "1 day 1 hour"
        else:
            return f"1 day {remaining_hours} hours"
    # Multiple days
    elif remaining_hours == 0:
        return f"{days} days"
    elif remaining_hours == 1:
        return f"{days} days 1 hour"
    else:
        return f"{days} days {remaining_hours} hours"


def calculate_hours_to_interested(action_date:  datetime | None) -> str:
    try:
        if not action_date:
            return "Unknown"

        # Get current UTC time
        now_utc = datetime.now(UTC)

        # Ensure action_date is timezone-aware (convert to UTC if naive)
        if action_date.tzinfo is None:
            # If naive datetime, assume it's already in UTC
            action_date_utc = action_date.replace(tzinfo=UTC)
        else:
            # If timezone-aware, convert to UTC
            action_date_utc = action_date.astimezone(UTC)

        # Calculate the difference from action_date to now
        time_diff = now_utc - action_date_utc
        hours = time_diff.total_seconds() / 3600

        # Round to 2 decimal places
        hours_rounded = round(hours, 2)

        # Format the duration
        return format_time_duration(hours_rounded)

    except Exception:
        # Return "Unknown" if any error occurs
        return "Unknown"


def calculate_lawyer_experience(lawyer: Lawyer, should_round: bool = True) -> str:
    try:
        if not lawyer:
            return "Not specified"

        # Collect all non-null admission/calling dates
        dates: list[date] = []

        if lawyer.admitted_date_solicitor:
            dates.append(cast(date, lawyer.admitted_date_solicitor))
        if lawyer.called_date_barrister:
            dates.append(cast(date, lawyer.called_date_barrister))
        if lawyer.admitted_date_cliex:
            dates.append(cast(date, lawyer.admitted_date_cliex))

        # If no dates found, return "0"
        if not dates:
            return "Not specified"

        # Find the minimum (earliest) date
        min_date = min(dates)

        # Calculate years of experience using UTC date
        today_utc = datetime.now(UTC).date()
        # Calculate the total number of months of experience
        months_experience = (today_utc.year - min_date.year) * 12 + (today_utc.month - min_date.month)
        if today_utc.day < min_date.day:
            months_experience -= 1
        # Convert months to years with one decimal place
        years_experience = round(max(0, months_experience) / 12, 1)
        if should_round:
            years_experience = int(months_experience / 12)
            if years_experience < 1:
                return f"{months_experience} month" if months_experience == 1 else f"{months_experience} months"
            return f"{years_experience} year" if years_experience == 1 else f"{years_experience} years"

        return f"{years_experience} year" if years_experience == 1 else f"{years_experience} years"

    except Exception:
        return "Not specified"


def get_template_json(component_name: str, user_role: str, module_name: str) -> tuple[dict[str, Any], int]:
    """Get the template JSON for the timeline type."""
    base_path = settings.BASE_COMPONENTS_PATH
    template_path = f"{base_path}/{module_name}/{user_role.lower()}/{component_name}/{component_name}.json"
    try:
        with open(template_path) as f:
            template = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError("Template not found") from None

    try:
        last_version = next(iter(template.keys()))
    except StopIteration:
        # Handle empty template case
        raise ValueError("Template is empty") from None
    template = template[last_version]
    return cast(dict[str, Any], template), int(last_version)

def generate_case_no(length: int = 7, alphabet: str = "23456789BCDFGHJKMNPQRTVWXY", group: int | None = None) -> str:
    """
    Generate a secure, human-friendly case number.
    
    Uses a restricted alphabet to avoid confusing characters:
    - Digits: 2-9 (excludes 0/O and 1/I confusion)
    - Uppercase consonants: B, C, D, F, G, H, J, K, M, N, P, Q, R, T, V, W, X, Y
    - Excludes: A, E, I, O, U, S, L (to avoid vowel confusion and S/5, L/1 issues)
    
    Uses `secrets.choice` which is suitable for cryptographic needs.
    
    Args:
        length: Length of the case number (default: 7, max: 15)
        alphabet: Custom alphabet to use (default: restricted alphabet)
        group: Optionally splits the ID into chunks for readability, e.g. 3 -> "ABC-DEF"
    
    Returns:
        A random case number string (e.g., "K7R4P9", "BX7M3Q", or "K7R-4P9" if grouped)
    
    Example:
        >>> ref = generate_case_no()
        >>> len(ref) == 7
        True
        >>> all(c in "23456789BCDFGHJKMNPQRTVWXY" for c in ref.replace("-", ""))
        True
    """
    if length <= 0:
        raise ValueError("length must be positive")
    if length > 15:
        raise ValueError("length must not exceed 15")
    if len(alphabet) < 2:
        raise ValueError("alphabet must contain at least 2 characters")
    
    # Generate cryptographically secure random characters
    raw = ''.join(secrets.choice(alphabet) for _ in range(length))
    
    # Optionally group for readability
    if group and group > 0:
        parts = [raw[i:i+group] for i in range(0, len(raw), group)]
        return '-'.join(parts)
    
    return raw
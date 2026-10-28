"""Data formatting utilities for the Nova Law AI application."""

import random
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from typing import TYPE_CHECKING

from app.enums.base import NameExtractionOption
from app.enums.lawyer import (
    ExpertTypeEnum,
    RegulatorEnum,
    DRPreferenceEnum,
    AccreditedSpecialismEnum,
    ExpertiseEnum,
    RelationshipTypeEnum,
)

if TYPE_CHECKING:
    from app.db.models.lawyer import LawyerAccreditedSpecialism, LawyerExpertise


def format_currency(amount: float | Decimal | str, currency: str = "USD") -> str:
    """Format currency amount with proper formatting.

    Args:
    ----
        amount: Amount to format
        currency: Currency code (default: USD)

    Returns:
    -------
        Formatted currency string

    """
    try:
        if isinstance(amount, Decimal | str):
            amount = float(amount)

        if currency == "USD":
            return f"${amount:,.2f}"
        elif currency == "EUR":
            return f"€{amount:,.2f}"
        elif currency == "GBP":
            return f"£{amount:,.2f}"
        else:
            return f"{amount:,.2f} {currency}"
    except (ValueError, TypeError):
        return f"0.00 {currency}"


_CURRENCY_COMPACT_SYMBOLS: dict[str, str] = {
    "GBP": "£",
    "EUR": "€",
    "USD": "$",
}


def format_currency_compact(amount: int, *, currency: str = "GBP") -> str:
    """Format an amount in compact form, e.g. ``152000 -> £152K`` (default GBP)."""
    symbol = _CURRENCY_COMPACT_SYMBOLS.get(currency.upper(), "")
    if amount >= 1_000_000:
        return f"{symbol}{amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"{symbol}{amount / 1_000:.0f}K"
    return f"{symbol}{amount}"


def format_phone_number(phone: str, country_code: str = "US") -> str:
    """Format phone number with proper formatting.

    Args:
    ----
        phone: Phone number string
        country_code: Country code (default: US)

    Returns:
    -------
        Formatted phone number

    """
    # Remove all non-digit characters
    digits = re.sub(r"\D", "", phone)

    if country_code == "US":
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        elif len(digits) == 11 and digits[0] == "1":
            return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
        else:
            return phone  # Return original if can't format

    return phone


def format_date(date_obj: date | datetime | str, format_str: str = "%Y-%m-%d") -> str:
    """Format date object to string.

    Args:
    ----
        date_obj: Date or datetime object or string
        format_str: Format string (default: YYYY-MM-DD)

    Returns:
    -------
        Formatted date string

    """
    try:
        if isinstance(date_obj, str):
            # Try to parse the string
            for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
                try:
                    parsed_date = datetime.strptime(date_obj, fmt)
                    return parsed_date.strftime(format_str)
                except ValueError:
                    continue

        if isinstance(date_obj, date | datetime):
            return date_obj.strftime(format_str)
        else:
            return str(date_obj)
    except (ValueError, TypeError):
        return str(date_obj)


def format_datetime(dt: datetime | str, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object to string.

    Args:
    ----
        dt: Datetime object or string
        format_str: Format string (default: YYYY-MM-DD HH:MM:SS)

    Returns:
    -------
        Formatted datetime string

    """
    try:
        if isinstance(dt, str):
            # Try to parse the string
            for fmt in [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
            ]:
                try:
                    parsed_dt = datetime.strptime(dt, fmt)
                    return parsed_dt.strftime(format_str)
                except ValueError:
                    continue

        if isinstance(dt, datetime):
            return dt.strftime(format_str)
        else:
            return str(dt)
    except (ValueError, TypeError):
        return str(dt)


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human readable format.

    Args:
    ----
        size_bytes: Size in bytes

    Returns:
    -------
        Formatted file size string

    """
    if size_bytes == 0:
        return "0 B"

    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    current_size = float(size_bytes)
    while current_size >= 1024 and i < len(size_names) - 1:
        current_size /= 1024.0
        i += 1

    return f"{current_size:.1f} {size_names[i]}"


def format_duration(seconds: int | float) -> str:
    """Format duration in seconds to human readable format.

    Args:
    ----
        seconds: Duration in seconds

    Returns:
    -------
        Formatted duration string

    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f}h"
    else:
        days = seconds / 86400
        return f"{days:.1f}d"


def format_percentage(
    value: float | int,
    total: float | int,
    decimal_places: int = 2,
) -> str:
    """Format percentage with proper decimal places.

    Args:
    ----
        value: Current value
        total: Total value
        decimal_places: Number of decimal places (default: 2)

    Returns:
    -------
        Formatted percentage string

    """
    if total == 0:
        return "0%"

    percentage = (value / total) * 100
    return f"{percentage:.{decimal_places}f}%"


def format_list(
    items: list[Any],
    separator: str = ", ",
    max_items: int | None = None,
) -> str:
    """Format list of items to string.

    Args:
    ----
        items: List of items
        separator: Separator between items (default: ", ")
        max_items: Maximum number of items to show (default: None)

    Returns:
    -------
        Formatted list string

    """
    if not items:
        return ""

    if max_items and len(items) > max_items:
        return (
            separator.join(str(item) for item in items[:max_items])
            + f" and {len(items) - max_items} more"
        )

    return separator.join(str(item) for item in items)


def format_address(address_dict: dict[str, Any]) -> str:
    """Format address dictionary to string.

    Args:
    ----
        address_dict: Dictionary containing address components

    Returns:
    -------
        Formatted address string

    """
    components = []

    # Street address
    if address_dict.get("street"):
        components.append(address_dict["street"])

    # City, State, ZIP
    city_state_zip = []
    if address_dict.get("city"):
        city_state_zip.append(address_dict["city"])
    if address_dict.get("state"):
        city_state_zip.append(address_dict["state"])
    if address_dict.get("zip_code"):
        city_state_zip.append(address_dict["zip_code"])

    if city_state_zip:
        components.append(", ".join(city_state_zip))

    # Country
    if address_dict.get("country"):
        components.append(address_dict["country"])

    return "\n".join(components)


def format_name(first_name: str, last_name: str, middle_name: str | None = None) -> str:
    """Format full name from components.

    Args:
    ----
        first_name: First name
        last_name: Last name
        middle_name: Middle name (optional)

    Returns:
    -------
        Formatted full name

    """
    if middle_name:
        return f"{first_name} {middle_name} {last_name}"
    else:
        return f"{first_name} {last_name}"


def extract_name_parts(
    name: str, option: NameExtractionOption | str = NameExtractionOption.FULL
) -> str:
    """Extract name parts from a name string based on the specified option.

    Args:
    ----
        name: Name string (e.g., "John", "John Doe", "John Michael Doe")
        option: Extraction option from NameExtractionOption enum or string (default: FULL)
            - NameExtractionOption.FIRST or "first": Returns first name only (first word)
            - NameExtractionOption.LAST or "last": Returns last name only (rest of the name, or empty)
            - NameExtractionOption.FULL or "full": Returns full name (original name)

    Returns:
    -------
        String value based on the option:
            - NameExtractionOption.FIRST: First name (first word)
            - NameExtractionOption.LAST: Last name (rest of the name, or empty string)
            - NameExtractionOption.FULL: Full name (original name)

    """
    if not name or not isinstance(name, str):
        return ""

    # Clean the name
    name = name.strip()
    if not name:
        return ""

    # Split the name into parts
    name_parts = name.split()

    # First part is always first_name
    first_name = name_parts[0] if name_parts else None
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else None
    full_name = name

    # Return based on option
    if option == NameExtractionOption.FIRST:
        return first_name
    elif option == NameExtractionOption.LAST:
        return last_name
    else:
        return full_name

def format_case_number(case_no: str, prefix: str = "#") -> str:
    """
    Format case number with a prefix.

    Args:
        case_no: String case number (e.g., "100", "K2TCHJF", "101")
        prefix: Case prefix (default: "#")

    Returns:
        str: Formatted case number with prefix (e.g., "#100", "#K2TCHJF")
    """
    return f"{prefix}{case_no}"


def format_legal_citation(citation: str) -> str:
    """Format legal citation with proper formatting.

    Args:
    ----
        citation: Legal citation string

    Returns:
    -------
        Formatted legal citation

    """
    # Common legal citation patterns
    patterns = [
        # Case citations: Smith v. Jones, 123 U.S. 456 (2020)
        (
            r"(\w+)\s+v\.\s+(\w+),\s+(\d+)\s+([A-Z.]+)\s+(\d+)\s+\((\d{4})\)",
            r"\1 v. \2, \3 \4 \5 (\6)",
        ),
        # Statute citations: 42 U.S.C. § 1983
        (r"(\d+)\s+([A-Z.]+)\s+§\s+(\d+)", r"\1 \2 § \3"),
        # Regulation citations: 45 C.F.R. § 164.308
        (r"(\d+)\s+([A-Z.]+)\s+§\s+(\d+\.\d+)", r"\1 \2 § \3"),
    ]

    formatted = citation
    for pattern, replacement in patterns:
        formatted = re.sub(pattern, replacement, formatted, flags=re.IGNORECASE)

    return formatted


def format_ssn(ssn: str, mask: bool = True) -> str:
    """Format Social Security Number with optional masking.

    Args:
    ----
        ssn: SSN string
        mask: Whether to mask the SSN (default: True)

    Returns:
    -------
        Formatted SSN

    """
    # Remove all non-digit characters
    digits = re.sub(r"\D", "", ssn)

    if len(digits) != 9:
        return ssn  # Return original if invalid

    if mask:
        return f"***-**-{digits[-4:]}"
    else:
        return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"


def format_credit_card(card_number: str, mask: bool = True) -> str:
    """Format credit card number with optional masking.

    Args:
    ----
        card_number: Credit card number string
        mask: Whether to mask the card number (default: True)

    Returns:
    -------
        Formatted credit card number

    """
    # Remove all non-digit characters
    digits = re.sub(r"\D", "", card_number)

    if len(digits) < 13 or len(digits) > 19:
        return card_number  # Return original if invalid

    if mask:
        return f"{'*' * (len(digits) - 4)}{digits[-4:]}"
    else:
        # Format with spaces every 4 digits
        return " ".join([digits[i : i + 4] for i in range(0, len(digits), 4)])

def mask_email(email: str) -> str:
    """
    Mask an email address for privacy, showing only basic parts of the username and domain.

    Instead of preserving length, use a simple masking style:
      - Show only the first character (and last if long enough) of the username, mask the rest (at most 2 '*')
      - Show only the first character of the domain (before first dot), mask the rest (up to 2 '*')
      - Do not try to preserve the original number of stars/characters

    Examples:
        mask_email("johndoe@gmail.com") -> "j**e@g**l.com"
        mask_email("a@b.com") -> "a@b.com"
        mask_email("john.smith@company.co.uk") -> "j**h@c**y.co.uk"

    Args:
    ----
        email: The email address to mask.

    Returns:
    -------
        Masked email address as string.
    """
    try:
        username, domain = email.split("@", 1)
    except ValueError:
        return email

    # Mask username: If <= 2 just return, else show first + '**' + last (only one or two *)
    if len(username) <= 2:
        masked_user = username
    elif len(username) == 3:
        masked_user = f"{username[0]}***{username[-1]}"
    else:
        masked_user = f"{username[0]}*****{username[-1]}"

    # Mask domain: Just mask the part before first dot (eg g**l)
    if "." in domain:
        main_domain, rest = domain.split(".", 1)
        if len(main_domain) <= 2:
            masked_domain = main_domain
        elif len(main_domain) == 3:
            masked_domain = f"{main_domain[0]}***{main_domain[-1]}"
        else:
            masked_domain = f"{main_domain[0]}*****{main_domain[-1]}"
        masked_full_domain = f"{masked_domain}.{rest}"
    else:
        masked_full_domain = domain

    return f"{masked_user}@{masked_full_domain}"

# Helper function to format JSON fields for display
def format_json_field(
    data: dict | None,
    enum_class: type | None = None,
    enum_label_map: dict[str, str] | None = None,
    separate_other: bool = True,
) -> str:
    """
    Format JSON field with enum key to label conversion.
    
    Args:
        data: Dictionary with 'values' and optionally 'other' keys
        enum_class: Enum class to use for converting keys to labels
        enum_label_map: Optional mapping of enum keys to labels (for custom mappings)
        separate_other: If True, format "other" on a new line; if False, include in same line
    
    Returns:
        Formatted string with labels separated by commas, with "other" on new line if separate_other=True
    """
    if not data:
        return "N/A"
    values = data.get("values", [])
    other = data.get("other", "")
    
    # Convert enum keys to labels if enum_class is provided
    parts = []
    if values:
        for value in values:
            label = value  # Default to original value
            
            # Try to get label from enum class
            if enum_class:
                try:
                    # Try to get enum member by name (key)
                    enum_member = enum_class[value]
                    # Get the label/value from enum
                    if hasattr(enum_member, 'full_name'):
                        label = enum_member.full_name
                    elif hasattr(enum_member, 'value'):
                        label = enum_member.value
                    else:
                        label = str(enum_member)
                except (KeyError, AttributeError):
                    # If not found by key, try by value (backward compatibility)
                    try:
                        enum_member = enum_class(value)
                        if hasattr(enum_member, 'full_name'):
                            label = enum_member.full_name
                        elif hasattr(enum_member, 'value'):
                            label = enum_member.value
                        else:
                            label = str(enum_member)
                    except (ValueError, AttributeError):
                        # If enum_label_map provided, use it
                        if enum_label_map and value in enum_label_map:
                            label = enum_label_map[value]
                        # Otherwise keep original value
            
            # Use custom label map if provided
            elif enum_label_map and value in enum_label_map:
                label = enum_label_map[value]
            
            parts.append(label)
    
    # Format main values
    main_text = ", ".join(parts) if parts else ""
    
    # Format "other" value
    if other:
        if separate_other and main_text:
            # Return with "other" on new line
            return f"{main_text}\nOther: {other}"
        elif separate_other:
            # Only "other" value
            return f"Other: {other}"
        else:
            # Include in same line
            if main_text:
                return f"{main_text}, Other: {other}"
            else:
                return f"Other: {other}"
    
    return main_text if main_text else "N/A"

def format_service_details(data: dict | None) -> list[dict[str, str]]:
    """
    Format service_details with new structure (offers, cohabitees, married_civil_partners).
    Converts enum keys to labels for display.
    
    Args:
        data: Dictionary with 'offers', 'cohabitees', and/or 'married_civil_partners' keys
    
    Returns:
        List of dictionaries with 'category' and 'services' keys
    """
    if not data:
        return []
    result = []
    
    # Helper to convert relationship type enum key to label
    def get_relationship_label(key: str) -> str:
        try:
            return RelationshipTypeEnum[key].value
        except (KeyError, AttributeError):
            # Fallback mappings
            mapping = {
                "MARRIED_CIVIL_PARTNERS": "Married and Civil Partners",
                "COHABITEES": "Cohabitees",
                "PARENTAL_RELATIONSHIPS": "Parental relationships",
            }
            return mapping.get(key, key)
    
    # Helper to convert expertise enum key to label
    def get_expertise_label(key: str) -> str:
        try:
            enum_member = ExpertiseEnum[key]
            # Use lawyer_page label (the display value)
            if hasattr(enum_member, 'lawyer_page'):
                return enum_member.lawyer_page
            elif hasattr(enum_member, 'value'):
                return enum_member.value
            else:
                return str(enum_member)
        except (KeyError, AttributeError):
            # Try by value for backward compatibility
            try:
                enum_member = ExpertiseEnum(key)
                if hasattr(enum_member, 'lawyer_page'):
                    return enum_member.lawyer_page
                elif hasattr(enum_member, 'value'):
                    return enum_member.value
                else:
                    return str(enum_member)
            except (ValueError, AttributeError):
                return key
    
    # Handle new format with offers, cohabitees, married_civil_partners
    if "offers" in data:
        offers = data.get("offers", [])
        if offers:
            offers_labels = [get_relationship_label(offer) for offer in offers]
            result.append({
                "category": "Who do you offer services to?",
                "services": ", ".join(offers_labels)
            })
    
    # Handle cohabitees
    if "cohabitees" in data and data["cohabitees"]:
        cohabitees_data = data["cohabitees"]
        if isinstance(cohabitees_data, dict):
            expertises = cohabitees_data.get("expertises", [])
            other = cohabitees_data.get("other", [])
            
            expertise_labels = [get_expertise_label(exp) for exp in expertises if exp not in ["OTHER_COHABITEES", "Other"]]
            
            # Format services with "other" values on separate line if present
            if expertise_labels and other:
                services_text = ", ".join(expertise_labels) + "\nOther: " + ", ".join(other)
            elif expertise_labels:
                services_text = ", ".join(expertise_labels)
            elif other:
                services_text = "Other: " + ", ".join(other)
            else:
                services_text = ""
            
            if services_text:
                result.append({
                    "category": "Cohabitees - Expertises",
                    "services": services_text
                })
    
    # Handle married_civil_partners
    if "married_civil_partners" in data and data["married_civil_partners"]:
        married_data = data["married_civil_partners"]
        if isinstance(married_data, dict):
            expertises = married_data.get("expertises", [])
            other = married_data.get("other", [])
            
            expertise_labels = [get_expertise_label(exp) for exp in expertises if exp not in ["OTHER_MARRIED_CIVIL_PARTNERS", "Other"]]
            
            # Format services with "other" values on separate line if present
            if expertise_labels and other:
                services_text = ", ".join(expertise_labels) + "\nOther: " + ", ".join(other)
            elif expertise_labels:
                services_text = ", ".join(expertise_labels)
            elif other:
                services_text = "Other: " + ", ".join(other)
            else:
                services_text = ""
            
            if services_text:
                result.append({
                    "category": "Married and Civil Partners - Expertises",
                    "services": services_text
                })
    
    # Handle old format (backward compatibility)
    if not result:
        for category, services in data.items():
            if isinstance(services, list) and services:
                # Try to convert category if it's an enum key
                category_label = get_relationship_label(category) if category in ["MARRIED_CIVIL_PARTNERS", "COHABITEES", "PARENTAL_RELATIONSHIPS"] else category
                service_labels = [get_expertise_label(s) if isinstance(s, str) else str(s) for s in services]
                result.append({
                    "category": category_label,
                    "services": ", ".join(service_labels)
                })
    
    return result


def format_expertises(
    expertises: list["LawyerExpertise"] | None,
    expertises_other: dict[str, list[str]] | None,
) -> list[str]:
    """Format lawyer expertises into a list of display strings.
    
    Combines enum-based expertises (excluding OTHER_* enums) with custom "other" values
    from the expertises_other dictionary.
    
    Args:
        expertises: List of LawyerExpertise model instances
        expertises_other: Dictionary mapping relationship types to lists of custom expertise values
            Example: {"married_civil_partners": ["Custom expertise 1"], "cohabitees": ["Custom expertise 2"]}
    
    Returns:
        List of formatted expertise display strings (enum values + custom "other" values)
    
    Example:
        >>> expertises = [LawyerExpertise(expertise=ExpertiseEnum.DIVORCE_AND_SEPARATION), ...]
        >>> expertises_other = {"married_civil_partners": ["Custom Divorce"]}
        >>> format_expertises(expertises, expertises_other)
        ["Divorce and Separation", "Custom Divorce"]
    """
    expertises_list: list[str] = []
    
    if expertises is not None:
        for expertise in expertises:
            if not expertise.expertise.is_other():
                expertises_list.append(expertise.expertise.value)
    
    if expertises_other is not None:
        for key, value in expertises_other.items():
            expertises_list.extend(value)
    
    return expertises_list


def format_accredited_specialisms(
    accredited_specialisms: list["LawyerAccreditedSpecialism"] | None,
    accredited_specialism_other: dict[str, list[str]] | list[str] | None,
) -> list[str]:
    """Format lawyer accredited specialisms into a list of display strings.
    
    Combines enum-based accredited specialisms (excluding OTHER enum) with custom "other" values
    from the accredited_specialism_other parameter.
    
    Args:
        accredited_specialisms: List of LawyerAccreditedSpecialism model instances
        accredited_specialism_other: Custom accredited specialism values. Can be either:
            - list[str]: Direct list of values (most common format from schemas)
            - dict[str, list[str]]: Dictionary mapping keys to lists of values (for backward compatibility)
    
    Returns:
        List of formatted accredited specialism display strings (enum values + custom "other" values)
    
    Example:
        >>> accredited_specialisms = [LawyerAccreditedSpecialism(accredited_specialism=AccreditedSpecialismEnum.RESOLUTION_ACCREDITED_SPECIALIST), ...]
        >>> accredited_specialism_other = ["Custom Specialism"]
        >>> format_accredited_specialisms(accredited_specialisms, accredited_specialism_other)
        ["Resolution Accredited Specialist", "Custom Specialism"]
    """
    accredited_specialisms_list: list[str] = []
    
    if accredited_specialisms is not None:
        for accredited_specialism in accredited_specialisms:
            if not accredited_specialism.accredited_specialism.is_other():
                accredited_specialisms_list.append(accredited_specialism.accredited_specialism.value)
    
    if accredited_specialism_other is not None:
        # Handle both list and dict formats for backward compatibility
        if isinstance(accredited_specialism_other, list):
            accredited_specialisms_list.extend(accredited_specialism_other)
        elif isinstance(accredited_specialism_other, dict):
            for key, value in accredited_specialism_other.items():
                if isinstance(value, list):
                    accredited_specialisms_list.extend(value)
                else:
                    accredited_specialisms_list.append(str(value))
    
    return accredited_specialisms_list


_PRIMARY_PROFESSIONAL_LABELS: tuple[tuple[ExpertTypeEnum, str], ...] = (
    (ExpertTypeEnum.SOLICITOR, "Solicitor"),
    (ExpertTypeEnum.BARRISTER, "Barrister"),
    (ExpertTypeEnum.CILEX, "Lawyer"),
)

_FAMILY_LAW_EXPERT_LABELS: tuple[tuple[ExpertTypeEnum, str], ...] = (
    (ExpertTypeEnum.DIVORCE_COACH, "Divorce Coach"),
    (ExpertTypeEnum.FAMILY_CONSULTANT, "Family Consultant"),
)


def build_lawyer_card_data(
    expert_types: list[ExpertTypeEnum] | None,
    expert_types_other: str | None,
    dr_preferences: list[DRPreferenceEnum] | None,
    experience: str | None,
    expertises_all: list[str] | None,
) -> "LawyerCardData":
    """Build public-facing lawyer card labels and tags.

    Label 1 is the primary professional status: Solicitor, Barrister, or CiLex
    (shown as Lawyer). If none of those apply, it falls back to the Family Law
    Expert group (Divorce Coach, Family Consultant, or custom Other text).

    Label 2 uses this priority: Arbitrator > Collaborative practitioner > Mediator.

    Tags start with experience, then up to 3 expertises. When more than 3
    expertises are available, 3 are chosen at random.
    """
    from app.schemas.v1.lawyer import LawyerCardData

    expert_type_set = set(expert_types or [])
    dr_preference_set = set(dr_preferences or [])

    label_1 = None
    for expert_type, label in _PRIMARY_PROFESSIONAL_LABELS:
        if expert_type in expert_type_set:
            label_1 = label
            break

    if label_1 is None:
        for expert_type, label in _FAMILY_LAW_EXPERT_LABELS:
            if expert_type in expert_type_set:
                label_1 = label
                break
        if label_1 is None and ExpertTypeEnum.OTHER in expert_type_set and expert_types_other:
            label_1 = expert_types_other.strip().capitalize()

    label_2 = None
    if ExpertTypeEnum.ARBITRATOR in expert_type_set:
        label_2 = "Arbitrator"
    elif DRPreferenceEnum.COLLABORATIVE in dr_preference_set:
        label_2 = "Collaborative practitioner"
    elif expert_type_set & {ExpertTypeEnum.LAWYER_MEDIATOR, ExpertTypeEnum.MEDIATOR}:
        label_2 = "Mediator"

    tags: list[str] = []
    if experience:
        tags.append(experience)
    if expertises_all:
        if len(expertises_all) >= 3:
            tags.extend(random.sample(expertises_all, 3))
        else:
            tags.extend(expertises_all)

    return LawyerCardData(label_1=label_1, label_2=label_2, tags=tags)

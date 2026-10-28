from enum import Enum


class SortDirection(str, Enum):
    """Sort direction."""

    ASC = "asc"
    DESC = "desc"

class NameExtractionOption(str, Enum):
    """Enum for name extraction options."""

    FIRST = "first"
    LAST = "last"
    FULL = "full"

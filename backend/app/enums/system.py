"""System and API related enums."""

from enum import Enum


class APIVersion(str, Enum):
    """API version identifiers."""

    V1 = "v1"
    V2 = "v2"  # Future version

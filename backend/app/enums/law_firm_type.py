from enum import Enum


class LawFirmType(str, Enum):
    """Law firm type enum."""

    SOLO_PRACTITIONER = "Solo practitioner"
    BOUTIQUE = "Boutique"
    MULTI_SPECIALITY = "Multi-speciality"

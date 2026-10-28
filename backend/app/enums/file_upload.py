"""File upload enums for the Nova Law AI application."""

from enum import Enum

from app.enums.user_role import UserRoleEnum


class ImageSize(str, Enum):
    """Image size enumeration for resizing operations."""

    THUMBNAIL = "thumbnail"
    MEDIUM = "medium"
    LARGE = "large"


class EntityType(str, Enum):
    """Entity type enumeration for upload categorization."""

    LAWYER_PROFILE = "lawyer_profile"
    LAW_FIRM_LOGO = "law_firm_logo"
    B2C_EXPERT_PROFILE = "b2c_expert_profile"


class FileVisibility(str, Enum):
    """File visibility types for uploads."""

    PUBLIC = "public"
    PRIVATE = "private"


class EntityStoragePathEnum(str, Enum):
    """Storage path templates for different entity types."""

    # Public paths (accessible via CloudFront)
    LAWYER_PROFILE = "public/profiles/lawyers/{year}/{month}/{encrypted_entity_id}/{timestamp}_"
    LAW_FIRM_LOGO = "public/logos/lawfirm/{year}/{month}/{encrypted_entity_id}/{timestamp}_"
    B2C_EXPERT_PROFILE = "public/B2C-experts/{year}/{month}/{encrypted_entity_id}/{timestamp}_"

# Entity types that require image processing (resize into 3 sizes)
# These entities ONLY accept image files and will be processed into thumbnail/medium/large
# All other entities will save files directly to permanent storage without processing
IMAGE_PROCESSING_ENTITIES: set[EntityType] = {
    EntityType.LAWYER_PROFILE,
    EntityType.LAW_FIRM_LOGO,
    EntityType.B2C_EXPERT_PROFILE,
}


# Permission mapping for entity types
ENTITY_TYPE_PERMISSIONS: dict[EntityType, list[UserRoleEnum]] = {
    EntityType.LAWYER_PROFILE: [UserRoleEnum.NAVIGATOR, UserRoleEnum.LAWYER],
    EntityType.LAW_FIRM_LOGO: [UserRoleEnum.NAVIGATOR],
    EntityType.B2C_EXPERT_PROFILE: [],  # Public endpoint, no auth required
}

# Visibility mapping for entity types
ENTITY_TYPE_VISIBILITY: dict[EntityType, FileVisibility] = {
    EntityType.LAWYER_PROFILE: FileVisibility.PUBLIC,
    EntityType.LAW_FIRM_LOGO: FileVisibility.PUBLIC,
    EntityType.B2C_EXPERT_PROFILE: FileVisibility.PUBLIC,
}

class ALLOWED_EXTENSIONS(str, Enum):
    """Allowed file extensions for uploads."""

    JPG = "jpg"
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    GIF = "gif"

from typing import Final

# Mapping of allowed file extensions per EntityType.
ENTITY_TYPE_ALLOWED_EXTENSIONS: Final[dict[EntityType, set[str]]] = {
    EntityType.LAWYER_PROFILE: {ALLOWED_EXTENSIONS.JPG, ALLOWED_EXTENSIONS.JPEG, ALLOWED_EXTENSIONS.PNG, ALLOWED_EXTENSIONS.WEBP, ALLOWED_EXTENSIONS.GIF},
    EntityType.LAW_FIRM_LOGO: {ALLOWED_EXTENSIONS.JPG, ALLOWED_EXTENSIONS.JPEG, ALLOWED_EXTENSIONS.PNG, ALLOWED_EXTENSIONS.WEBP, ALLOWED_EXTENSIONS.GIF},
    EntityType.B2C_EXPERT_PROFILE: {ALLOWED_EXTENSIONS.JPG, ALLOWED_EXTENSIONS.JPEG, ALLOWED_EXTENSIONS.PNG, ALLOWED_EXTENSIONS.WEBP, ALLOWED_EXTENSIONS.GIF},
}

# Allowed file sizes per extensions in mb for upload
ALLOWED_FILE_SIZES: Final[dict[ALLOWED_EXTENSIONS, int]] = {
    ALLOWED_EXTENSIONS.JPG: 5,
    ALLOWED_EXTENSIONS.JPEG: 5,
    ALLOWED_EXTENSIONS.PNG: 5,
    ALLOWED_EXTENSIONS.WEBP: 5,
    ALLOWED_EXTENSIONS.GIF: 5,
}
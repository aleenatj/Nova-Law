"""Utility functions for photo URL generation."""

import logging
from typing import Any

from app.services.upload_service import UploadService

logger = logging.getLogger(__name__)


def generate_photo_urls(folder_path: str | None, file_extension: str = "jpg") -> dict[str, str]:
    """
    Generate photo URLs dictionary from folder path stored in database.

    Args:
        folder_path: Folder path stored in database (e.g., "public/profiles/lawyers/2025/09/encrypted_id_1695632451")
        file_extension: File extension to use (default: "jpg")

    Returns:
        Dictionary containing photo URLs for different sizes

    Example:
        photo_urls = generate_photo_urls("public/profiles/lawyers/2025/09/encrypted_id_1695632451", "jpeg")
        # Returns: {
        #     "thumbnail": "https://d1234567890.cloudfront.net/public/profiles/lawyers/2025/09/encrypted_id_1695632451/thumbnail.jpeg",
        #     "medium": "https://d1234567890.cloudfront.net/public/profiles/lawyers/2025/09/encrypted_id_1695632451/medium.jpeg",
        #     "large": "https://d1234567890.cloudfront.net/public/profiles/lawyers/2025/09/encrypted_id_1695632451/large.jpeg"
        # }
    """
    try:
        if not folder_path:
            return {}

        # Initialize upload service
        upload_service = UploadService()

        # Get all available image URLs
        all_urls = upload_service.get_all_image_urls(folder_path, file_extension)

        # Convert to simple dictionary
        photo_urls = {}
        for size, url in all_urls.items():
            photo_urls[size.value] = url

        return photo_urls

    except Exception as e:
        logger.exception(f"Error generating photo URLs: {e}")
        return {}


def get_thumbnail_url(folder_path: str | None, file_extension: str = "jpg") -> str | None:
    """
    Get thumbnail URL from folder path.

    Args:
        folder_path: Folder path stored in database
        file_extension: File extension to use (default: "jpg")

    Returns:
        Thumbnail URL or None if not found
    """
    try:
        if not folder_path:
            return None

        upload_service = UploadService()
        return upload_service.get_thumbnail_url(folder_path, file_extension)

    except Exception as e:
        logger.exception(f"Error getting thumbnail URL: {e}")
        return None


def get_photo_urls_for_entity(entity_photo_url: str | None, file_extension: str = "jpg") -> dict[str, str]:
    """
    Get photo URLs for any entity from stored photo_url field.

    This is a convenience function that can be used in API responses
    to convert stored folder paths to photo URL dictionaries.

    Args:
        entity_photo_url: Photo URL field from database (folder path)
        file_extension: File extension to use (default: "jpg")

    Returns:
        Dictionary containing photo URLs for different sizes
    """
    return generate_photo_urls(entity_photo_url, file_extension)


def enhance_entity_with_photos(entity_data: dict[str, Any], photo_field: str = "photo_url", file_extension: str = "jpg") -> dict[str, Any]:
    """
    Enhance entity data with photo URLs dictionary.

    This function takes entity data and adds a photos dictionary
    while keeping the original photo_url field for backward compatibility.

    Args:
        entity_data: Dictionary containing entity data
        photo_field: Name of the photo field in the entity (default: "photo_url")
        file_extension: File extension to use (default: "jpg")

    Returns:
        Enhanced entity data with photos dictionary

    Example:
        lawyer_data = {
            "id": 123,
            "name": "John Doe",
            "photo_url": "profiles/lawyers/2024/1/encrypted_id"
        }

        enhanced_data = enhance_entity_with_photos(lawyer_data)
        # Returns: {
        #     "id": 123,
        #     "name": "John Doe",
        #     "photo_url": "profiles/lawyers/2024/1/encrypted_id",
        #     "photos": {
        #         "thumbnail": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/thumbnail.jpg",
        #         "medium": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/medium.jpg",
        #         "large": "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/large.jpg"
        #     }
        # }
    """
    try:
        # Get the photo URL from the entity
        photo_url = entity_data.get(photo_field)

        # Generate photo URLs dictionary
        photos = generate_photo_urls(photo_url, file_extension)

        # Add photos to entity data
        entity_data["photos"] = photos

        return entity_data

    except Exception as e:
        logger.exception(f"Error enhancing entity with photos: {e}")
        # Return original data if enhancement fails
        entity_data["photos"] = {}
        return entity_data

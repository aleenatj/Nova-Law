"""Upload service for file upload operations."""

import logging
from datetime import datetime

from app.enums.file_upload import (
    ALLOWED_EXTENSIONS,
    ALLOWED_FILE_SIZES,
    IMAGE_PROCESSING_ENTITIES,
    EntityStoragePathEnum,
    EntityType,
    ImageSize,
)
from app.services.s3_service import FileProcessor, S3Service
from app.utils.encryption import encrypt_id
from app.utils.helpers import generate_uuid

logger = logging.getLogger(__name__)


class UploadService:
    """Service for handling file uploads and processing."""

    def __init__(self) -> None:
        """Initialize upload service."""
        self.s3_service = S3Service()


    def generate_presigned_upload_url(
        self,
        extension: str,
        expiration: int = 900
    ) -> dict[str, str] | None:
        """
        Generate pre-signed URL for file upload.

        This method creates a temporary S3 URL that allows direct file uploads
        without going through the backend server. The file is stored in a temp
        location and must be processed later to move to permanent storage.

        Args:
            extension: File extension (e.g., 'jpg', 'png', 'pdf')
            expiration: URL expiration time in seconds (default: 15 minutes)

        Returns:
            Dictionary containing:
                - upload_url: Pre-signed S3 URL for direct upload
                - file_key: S3 key where file will be stored temporarily
                - expires_in: Expiration time in seconds
            Returns None if error occurs

        Example:
            result = upload_service.generate_presigned_upload_url("jpg")
            # Returns: {
            #     "upload_url": "https://bucket.s3.region.amazonaws.com/temp/uuid.jpg?...",
            #     "file_key": "temp/uuid.jpg",
            #     "expires_in": "900"
            # }
        """
        try:
            # Generate temporary upload path
            temp_key = f"temp/{generate_uuid()}.{extension}"

            # Generate pre-signed URL
            upload_url = self.s3_service.generate_presigned_url(
                key=temp_key,
                expiration=expiration
            )

            if not upload_url:
                logger.error("Failed to generate presigned URL")
                return None

            return {
                "upload_url": upload_url,
                "file_key": temp_key,
                "expires_in": str(expiration)
            }

        except Exception as e:
            logger.exception(f"Error generating presigned upload URL: {e}")
            return None

    def process_uploaded_file(
        self,
        temp_s3_url: str,
        entity: EntityType,
        entity_id: str
    ) -> str | None:
        """
        Process uploaded file by downloading, resizing, and storing in appropriate S3 path.

        This is the main file processing method that handles the complete workflow:
        1. Downloads file from temporary S3 location
        2. Validates file type compatibility with entity
        3. For image entities: Creates 3 resized versions (thumbnail, medium, large)
        4. For document entities: Stores as single file
        5. Uploads processed files to permanent storage
        6. Cleans up temporary file
        7. Returns permanent storage URL

        Args:
            temp_s3_url: Temporary S3 URL where the uploaded file is stored
                         Format: "https://bucket.s3.region.amazonaws.com/temp/uuid.ext"
            entity: Entity type for the file (determines processing method)
            entity_id: Unique identifier for the entity (should be encrypted)

        Returns:
            Final folder URL (S3 path) where processed files are stored with pattern
            Format: "public/profiles/lawyers/2024/1/encrypted_id/timestamp_*.ext"
            Returns None if error occurs

        Example:
            result = upload_service.process_uploaded_file(
                temp_s3_url="https://bucket.s3.region.amazonaws.com/temp/uuid.jpg",
                entity=EntityType.LAWYER_PROFILE,
                entity_id="encrypted_user_id"
            )
            # Returns: "public/profiles/lawyers/2024/1/encrypted_user_id/1695632451_*.jpg"
            # Creates: timestamp_thumbnail.jpg, timestamp_medium.jpg, timestamp_large.jpg in that folder
        """
        try:
            # Extract S3 key from URL
            temp_key = self._extract_s3_key_from_url(temp_s3_url)
            if not temp_key:
                logger.error("Could not extract S3 key from URL")
                return None

            # Download the file from temp location
            file_content = self.s3_service.download_file(temp_key)
            if not file_content:
                logger.error("Failed to download file from temp location")
                return None

            # Validate entity type and file compatibility
            if not self._validate_entity_file_compatibility(entity, file_content):
                return None

            # Generate storage path
            storage_path = self._generate_storage_path(entity, entity_id)
            if not storage_path:
                logger.error("Failed to generate storage path")
                return None

            # Process based on entity type
            if entity in IMAGE_PROCESSING_ENTITIES:
                # Get original file extension
                original_extension = self._get_file_extension_from_key(temp_key)
                # Process image into multiple sizes
                processed_files = self._process_image_sizes(file_content, storage_path, original_extension)
                if not processed_files:
                    logger.error("Failed to process image sizes")
                    return None
            else:
                # Save file directly to permanent storage (no processing)
                file_extension = self._get_file_extension_from_key(temp_key)
                if not self._save_file_directly(file_content, storage_path, file_extension):
                    logger.error("Failed to save file directly")
                    return None

            # Clean up temp file
            self.s3_service.delete_file(temp_key)

            # Invalidate CloudFront cache for the new files
            if entity in IMAGE_PROCESSING_ENTITIES:
                # Invalidate cache for all image sizes
                cache_paths = [f"{storage_path}/*"]
            else:
                # Invalidate cache for the single file
                cache_paths = [f"{storage_path}/*"]

            # TODO : Now paths are generated differently, In future this may be used if needed.
            # self.s3_service.invalidate_cloudfront_cache(cache_paths)

            # Return the base folder URL with extension pattern for all file types
            # Get the original file extension
            original_extension = self._get_file_extension_from_key(temp_key)
            return f"{storage_path}/*.{original_extension}"

        except Exception as e:
            logger.exception(f"Error processing uploaded file: {e}")
            return None

    def _extract_s3_key_from_url(self, s3_url: str) -> str | None:
        """
        Extract S3 object key from various S3 URL formats.

        This method handles different S3 URL formats:
        - Standard S3 URLs: "https://bucket.s3.region.amazonaws.com/path/to/file.jpg"
        - S3 protocol URLs: "s3://bucket/path/to/file.jpg"
        - Direct keys: "path/to/file.jpg"

        Args:
            s3_url: S3 URL in any supported format

        Returns:
            S3 object key (e.g., "temp/uuid.jpg") or None if extraction fails

        Example:
            key = self._extract_s3_key_from_url("https://bucket.s3.region.amazonaws.com/temp/uuid.jpg")
            # Returns: "temp/uuid.jpg"
        """
        try:
            # Handle different S3 URL formats
            if "amazonaws.com/" in s3_url:
                return s3_url.split("amazonaws.com/", 1)[1]
            elif "s3://" in s3_url:
                return s3_url.split("s3://", 1)[1].split("/", 1)[1]
            else:
                # Assume it's already a key
                return s3_url
        except Exception as e:
            logger.exception(f"Error extracting S3 key from URL: {e}")
            return None

    def validate_temp_file(self, temp_s3_url: str, entity_type: EntityType) -> tuple[bool, str | None]:
        """
        Validate that temp file exists and size is within allowed limits.

        This method checks if the file exists in the temp S3 location,
        retrieves its size without downloading the entire file, and validates
        that the size is within acceptable limits. This is useful for early
        validation before starting expensive operations like user creation.

        Args:
            temp_s3_url: Temporary S3 URL where the uploaded file is stored
            entity_type: Entity type for the file (determines size limits)

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if file exists, size is valid, and is accessible
            - error_message: Error message if validation fails, None otherwise

        Example:
            is_valid, error = upload_service.validate_temp_file(
                temp_s3_url="https://bucket.s3.region.amazonaws.com/temp/uuid.jpg",
                entity_type=EntityType.LAWYER_PROFILE
            )
            if not is_valid:
                raise HTTPException(status_code=400, detail=error)
        """
        try:
            # Extract S3 key from URL
            temp_key = self._extract_s3_key_from_url(temp_s3_url)
            if not temp_key:
                error_msg = "Could not extract S3 key from URL"
                logger.error(error_msg)
                return False, error_msg
            # Check if temp_key matches the format "temp/<uuid>"
            import re
            temp_key_pattern = r"^temp/[a-f0-9\-]{36}\.[a-zA-Z0-9]+$"
            if not re.match(temp_key_pattern, temp_key):
                error_msg = f"temp_key does not match required format 'temp/<uuid>': {temp_key}"
                logger.error(error_msg)
                return True, error_msg
            # Check if file exists
            if not self.s3_service.file_exists(temp_key):
                error_msg = f"File not found in temporary storage: {temp_key}"
                logger.error(error_msg)
                return False, error_msg

            # Get file size
            file_size = self.s3_service.get_file_size(temp_key)
            if file_size is None:
                error_msg = f"Could not retrieve file size for: {temp_key}"
                logger.error(error_msg)
                return False, error_msg
            else:
                # Validate file size against allowed limits
                file_extension = self._get_file_extension_from_key(temp_key).lower()
                
                # Try to find matching extension in ALLOWED_EXTENSIONS
                extension_enum = None
                for ext_enum in ALLOWED_EXTENSIONS:
                    if ext_enum.value.lower() == file_extension:
                        extension_enum = ext_enum
                        break
                
                if extension_enum and extension_enum in ALLOWED_FILE_SIZES:
                    # Get size limit in MB and convert to bytes
                    max_size_mb = ALLOWED_FILE_SIZES[extension_enum]
                    max_size_bytes = max_size_mb * 1024 * 1024
                    
                    # Validate size
                    if file_size > max_size_bytes:
                        file_size_mb = file_size / (1024 * 1024)
                        error_msg = (
                            f"File size ({file_size_mb:.1f} MB) exceeds maximum allowed size "
                            f"({max_size_mb} MB) for {file_extension.upper()} files"
                        )
                        logger.error(f"File size validation failed: {error_msg}")
                        return False, error_msg

            return True, None

        except Exception as e:
            error_msg = f"Error validating temp file: {e!s}"
            logger.exception(error_msg)
            return False, error_msg

    def _generate_storage_path(self, entity: EntityType, entity_id: str) -> str | None:
        """
        Generate permanent storage path for the entity based on type and current date.

        This method creates organized storage paths using the format:
        public/{type}/{entity}/{year}/{month}/{encrypted_entity_id}/{timestamp}_

        Args:
            entity: Entity type (determines base path)
            entity_id: Encrypted entity identifier

        Returns:
            Storage path string (e.g., "public/profiles/lawyers/2025/09/encrypted_id/1695632451_")
            Returns None if entity type is not supported

        Example:
            path = self._generate_storage_path(EntityType.LAWYER_PROFILE, "encrypted_user_id")
            # Returns: "public/profiles/lawyers/2025/09/encrypted_user_id/1695632451_"
        """
        try:
            # Map entity types to storage path templates
            entity_path_mapping = {
                EntityType.LAWYER_PROFILE: EntityStoragePathEnum.LAWYER_PROFILE,
                EntityType.LAW_FIRM_LOGO: EntityStoragePathEnum.LAW_FIRM_LOGO,
                EntityType.B2C_EXPERT_PROFILE: EntityStoragePathEnum.B2C_EXPERT_PROFILE,
            }

            # Get path template for entity
            path_template = entity_path_mapping.get(entity)
            if not path_template:
                logger.error(f"No storage path template for entity: {entity}")
                return None

            # Get current date and timestamp
            now = datetime.now()
            year = now.year
            month = f"{now.month:02d}"  # Two-digit format
            timestamp = int(now.timestamp())

            # Format the path
            storage_path = path_template.format(
                year=year,
                month=month,
                encrypted_entity_id=entity_id,
                timestamp=timestamp
            )

            return storage_path

        except Exception as e:
            logger.exception(f"Error generating storage path: {e}")
            return None

    def _process_image_sizes(
        self,
        image_content: bytes,
        base_path: str,
        original_extension: str = "jpg"
    ) -> dict[ImageSize, str]:
        """Process image into different sizes and upload to S3."""
        processed_files = {}

        try:
            # Determine correct content type based on the original extension
            content_type = self._get_content_type(original_extension)

            # Process each image size
            for size in ImageSize:
                # Resize image
                resized_content = FileProcessor.resize_image(image_content, size)
                if not resized_content:
                    logger.error(f"Failed to resize image for size: {size}")
                    continue

                # Create S3 key for this size using original extension
                # Note: base_path already ends with "timestamp_" so we append directly
                size_key = f"{base_path}{size.value}.{original_extension}"

                # Upload to S3 with correct content type
                if self.s3_service.upload_file(resized_content, size_key, content_type):
                    processed_files[size] = size_key
                    logger.info(f"Successfully processed {size.value} image: {size_key}")
                else:
                    logger.error(f"Failed to upload {size.value} image: {size_key}")

        except Exception as e:
            logger.exception(f"Error processing image sizes: {e}")

        return processed_files

    def _validate_entity_file_compatibility(self, entity: EntityType, file_content: bytes) -> bool:
        """Validate that the file type is compatible with the entity type."""
        try:
            # Only validate for image processing entities
            if entity in IMAGE_PROCESSING_ENTITIES:
                is_image = self._is_image_file(file_content)
                if not is_image:
                    logger.error(f"Entity {entity} requires image files, but uploaded file is not an image")
                    return False
                logger.info(f"Image file validated for entity {entity}")

            # All other entities accept any file type without validation
            return True

        except Exception as e:
            logger.exception(f"Error validating entity-file compatibility: {e}")
            return False

    def _is_image_file(self, file_content: bytes) -> bool:
        """
        Check if file content is a supported image format.

        Only supports PNG, JPEG, and HEIC/HEIF formats as per requirements.
        Uses PIL to validate the image format.
        """
        try:
            from io import BytesIO

            from PIL import Image

            # Open image to validate format
            image = Image.open(BytesIO(file_content))

            # Check if format is supported
            supported_formats = {'JPEG', 'PNG', 'HEIC', 'HEIF', 'WEBP'}
            return image.format in supported_formats

        except Exception:
            return False

    def _get_file_extension_from_key(self, key: str) -> str:
        """Extract file extension from S3 key."""
        try:
            return key.split('.')[-1].lower()
        except Exception:
            return 'bin'

    def _save_file_directly(
        self,
        file_content: bytes,
        storage_path: str,
        file_extension: str
    ) -> bool:
        """Save file directly to permanent storage without any processing."""
        try:
            # Create S3 key for the file
            # Note: storage_path already ends with "timestamp_" so we append directly
            file_key = f"{storage_path}original.{file_extension}"

            # Determine content type
            content_type = self._get_content_type(file_extension)

            # Upload to S3
            if self.s3_service.upload_file(file_content, file_key, content_type):
                logger.info(f"Successfully saved file: {file_key}")
                return True
            else:
                logger.error(f"Failed to save file: {file_key}")
                return False

        except Exception as e:
            logger.exception(f"Error saving file directly: {e}")
            return False

    def _get_content_type(self, file_extension: str) -> str:
        """Get MIME content type for file extension."""
        content_types = {
            # Document formats
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'txt': 'text/plain',

            # Supported image formats (PNG, JPEG, HEIC/HEIF only)
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp',
            'heic': 'image/heic',
            'heif': 'image/heif',

            # Other formats
            'zip': 'application/zip',
            'rar': 'application/x-rar-compressed',
        }
        return content_types.get(file_extension.lower(), 'application/octet-stream')

    def delete_existing_images(self, entity: EntityType, entity_id: str) -> bool:
        """
        Delete existing images for an entity from S3.

        This method is used during update operations to clean up old images
        before uploading new ones. It deletes all files in the entity's folder.

        Args:
            entity: Entity type (determines folder path)
            entity_id: Encrypted entity identifier

        Returns:
            True if deletion successful, False if error

        Example:
            success = upload_service.delete_existing_images(
                EntityType.LAWYER_PROFILE,
                "encrypted_user_id"
            )
        """
        try:
            # Generate storage path
            storage_path = self._generate_storage_path(entity, entity_id)
            if not storage_path:
                logger.error("Failed to generate storage path for deletion")
                return False

            # List all files in the folder
            files_to_delete = self._list_files_in_folder(storage_path)
            if not files_to_delete:
                logger.info(f"No existing files found in {storage_path}")
                return True

            # Delete each file
            deletion_success = True
            for file_key in files_to_delete:
                if not self.s3_service.delete_file(file_key):
                    logger.error(f"Failed to delete file: {file_key}")
                    deletion_success = False
                else:
                    logger.info(f"Successfully deleted file: {file_key}")

            # Invalidate CloudFront cache for deleted files
            # if deletion_success and files_to_delete:
            #     cache_paths = [f"{storage_path}/*"]
            #     self.s3_service.invalidate_cloudfront_cache(cache_paths)

            return deletion_success

        except Exception as e:
            logger.exception(f"Error deleting existing images: {e}")
            return False

    def _list_files_in_folder(self, folder_path: str) -> list[str]:
        """
        List all files in an S3 folder.

        Args:
            folder_path: S3 folder path (e.g., "profiles/lawyers/2024/1/encrypted_id")

        Returns:
            List of S3 keys for files in the folder
        """
        try:
            # Use S3 list_objects_v2 to get files in folder
            # Note: folder_path ends with timestamp_, so we don't add "/"
            response = self.s3_service.s3_client.list_objects_v2(
                Bucket=self.s3_service.bucket_name,
                Prefix=folder_path
            )

            if 'Contents' not in response:
                return []

            # Extract file keys
            file_keys = [obj['Key'] for obj in response['Contents']]
            return file_keys

        except Exception as e:
            logger.exception(f"Error listing files in folder {folder_path}: {e}")
            return []

    def get_image_url(self, folder_path: str, size: ImageSize = ImageSize.THUMBNAIL, file_extension: str = "jpg") -> str | None:
        """
        Get CloudFront URL for a specific image size from folder path stored in database.

        Args:
            folder_path: Folder path stored in database (may include /*.extension pattern)
            size: Image size to retrieve (default: THUMBNAIL)
            file_extension: File extension to use (default: "jpg")

        Returns:
            CloudFront URL for the specific image size, or None if not found
        """
        try:
            # Extract the base folder path and extension from pattern
            base_folder_path, extracted_extension = _extract_path_and_extension(folder_path)

            # Use extracted extension if available, otherwise use provided extension
            if extracted_extension:
                file_extension = extracted_extension

            # Create image key from folder path
            # Note: base_folder_path already ends with "timestamp_" so we append directly
            image_key = f"{base_folder_path}{size.value}.{file_extension}"

            # Check if file exists
            # if not self.s3_service.file_exists(image_key):
            #     logger.warning(f"Image not found: {image_key}")
            #     return None

            # Return CloudFront URL
            return self.s3_service.get_public_url(image_key)

        except Exception as e:
            logger.exception(f"Error getting image URL: {e}")
            return None

    def get_all_image_urls(self, folder_path: str, file_extension: str = "jpg") -> dict[ImageSize, str]:
        """
        Get all available image URLs for a folder path stored in database.

        Args:
            folder_path: Folder path stored in database (may include /*.extension pattern)
            file_extension: File extension to use (default: "jpg")

        Returns:
            Dictionary mapping ImageSize to CloudFront URLs
        """
        urls = {}

        try:
            # Extract the base folder path and extension from pattern
            base_folder_path, extracted_extension = _extract_path_and_extension(folder_path)

            # Use extracted extension if available, otherwise use provided extension
            if extracted_extension:
                file_extension = extracted_extension

            for size in ImageSize:
                # Note: base_folder_path already ends with "timestamp_" so we append directly
                image_key = f"{base_folder_path}{size.value}.{file_extension}"

                # if self.s3_service.file_exists(image_key):
                urls[size] = self.s3_service.get_public_url(image_key)
                # else:
                #     logger.warning(f"Image not found: {image_key}")

            return urls

        except Exception as e:
            logger.exception(f"Error getting all image URLs: {e}")
            return {}

    def get_thumbnail_url(self, folder_path: str, file_extension: str = "jpg") -> str | None:
        """
        Get thumbnail URL from folder path (most commonly used).

        Args:
            folder_path: Folder path stored in database
            file_extension: File extension to use (default: "jpg")

        Returns:
            Thumbnail CloudFront URL or None if not found
        """
        return self.get_image_url(folder_path, ImageSize.THUMBNAIL, file_extension)

    def tag_old_images_for_expiration(
        self,
        old_photo_url: str | None
    ) -> None:
        """
        Tag existing images with expire=true using the photo_url from database.

        This is a highly optimized approach that uses the existing photo_url
        from the database instead of recursively searching through S3.

        Performance Benefits:
        - O(1) complexity (constant time)
        - Single folder to tag (no recursive search)
        - Minimal S3 API calls
        - Much faster than searching through all folders

        Args:
            old_photo_url: The existing photo_url from database (e.g., "public/.../encrypted_id_timestamp/*.jpg")
                          If None or empty, no tagging occurs
        """
        try:
            if not old_photo_url:
                logger.info("No existing photo_url to tag for expiration")
                return

            # Extract the base folder path from the photo_url
            # Format: "public/profiles/lawyers/2025/01/encrypted_id/timestamp_*.jpg"
            # We need: "public/profiles/lawyers/2025/01/encrypted_id/timestamp_"
            base_folder_path, _ = _extract_path_and_extension(old_photo_url)

            if not base_folder_path:
                logger.warning(f"Could not extract folder path from photo_url: {old_photo_url}")
                return

            # List all objects in the old folder
            # Note: base_folder_path already ends with timestamp_, so we don't add "/"
            objects = self.s3_service.list_objects_in_folder(base_folder_path)

            if not objects:
                logger.info(f"No objects found in old folder: {base_folder_path}")
                return

            # Tag all objects with expire=true
            logger.info(f"Tagging {len(objects)} objects in folder {base_folder_path}/ with expire=true")
            success = self.s3_service.tag_objects_with_expire(objects)

            if success:
                logger.info(f"Successfully tagged {len(objects)} object(s) with expire=true")
            else:
                logger.warning(f"Some objects may not have been tagged successfully in {base_folder_path}/")

        except Exception as e:
            logger.exception(f"Error tagging old images for expiration: {e}")
            # Don't fail the upload if tagging fails
            return


def process_file_upload(
    photo_url: str | None,
    entity_id: int,
    entity_type: EntityType,
    is_update: bool = False,
    existing_photo_url: str | None = None
) -> tuple[str | None, bool]:
    """
    Common function to process file uploads for any entity.

    Args:
        photo_url: The temporary S3 URL of the photo to process
        entity_id: The ID of the entity (lawyer, user, etc.)
        entity_type: The type of entity for S3 folder structure
        is_update: Whether this is an update operation (no longer affects deletion logic)
        existing_photo_url: Current photo URL (for update operations)

    Returns:
        tuple: (processed_photo_url, success_flag)
    """
    if not photo_url:
        return None, True

    processed_photo_url = None
    photo_processing_success = True

    try:
        upload_service = UploadService()

        # Process new photo upload
        encrypted_id = encrypt_id(str(entity_id))
        if not encrypted_id:
            logger.error("Failed to encrypt entity ID")
            processed_photo_url = None
        else:
            processed_photo_url = upload_service.process_uploaded_file(
                temp_s3_url=photo_url,
                entity=entity_type,
                entity_id=encrypted_id
            )

        if not processed_photo_url:
            logger.warning("Failed to process photo upload, setting photo_url to None")
            processed_photo_url = None
            photo_processing_success = False
        # OPTIMIZED: Tag old images for expiration using existing_photo_url from database
        # This is much faster than searching through S3 - O(1) vs O(n)
        elif is_update and existing_photo_url:
            logger.info(f"Tagging old images for expiration: {existing_photo_url}")
            upload_service.tag_old_images_for_expiration(existing_photo_url)

    except Exception as e:
        logger.exception(f"Error processing photo upload: {e}")
        processed_photo_url = None
        photo_processing_success = False

    return processed_photo_url, photo_processing_success


def validate_temp_file_before_processing(
    photo_url: str | None,
    entity_type: EntityType
) -> None:
    """
    Validate temp file existence and size before processing.

    This is a common function to validate uploaded files before creating
    entities (users, lawyers, etc.) to prevent partial records if file is invalid.

    Args:
        photo_url: The temporary S3 URL of the photo to validate (can be None)
        entity_type: The type of entity for size limit validation

    Raises:
        HTTPException: If file validation fails (file not found, size exceeded, etc.)

    Example:
        validate_temp_file_before_processing(
            photo_url=request_data.photo_url,
            entity_type=EntityType.LAWYER_PROFILE
        )
        # If validation fails, HTTPException is raised
        # If validation passes or photo_url is None, function returns normally
    """
    from fastapi import HTTPException, status

    if not photo_url:
        return

    try:
        upload_service = UploadService()
        is_valid, error_message = upload_service.validate_temp_file(
            temp_s3_url=photo_url,
            entity_type=entity_type
        )

        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"success": False, "message": error_message or "File validation failed"}
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error validating temp file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"success": False, "message": "Failed to validate file"}
        ) from e

def _extract_path_and_extension(folder_path: str) -> tuple[str, str | None]:
    """
    Extract base folder path and extension from a path that may contain extension pattern.

    Args:
        folder_path: Folder path that may include /*.extension pattern

    Returns:
        Tuple of (base_folder_path, extension) where extension is None if not found
    """
    if "/*." in folder_path:
        parts = folder_path.split("/*.")
        base_folder_path = parts[0]
        extension = parts[1] if len(parts) > 1 else None
        return base_folder_path, extension
    else:
        return folder_path, None

def copy_files_to_new_location(
    existing_path: str,
    entity_type: EntityType,
    entity_id: str
) -> str | None:
    """
    Copy files from an existing S3 location to a new location based on entity type and entity ID.

    This function is useful when converting entities (e.g., legal expert to lawyer)
    and you want to copy the existing files to a new location with updated paths.

    Args:
        existing_path: Existing folder path with pattern (e.g., "public/profiles/lawyers/2025/12/9cd35cc7da5ea56e64d3d21523ecadbf/1765533885_/*.png")
        entity_type: Target entity type (determines new path structure)
        entity_id: Encrypted entity ID for the new location

    Returns:
        New folder path with pattern (e.g., "public/profiles/lawyers/2025/12/new_encrypted_id/1765533886_/*.png")
        Returns None if error occurs

    Example:
        new_path = upload_service.copy_files_to_new_location(
            existing_path="public/profiles/lawyers/2025/12/9cd35cc7da5ea56e64d3d21523ecadbf/1765533885_/*.png",
            entity_type=EntityType.LAWYER_PROFILE,
            entity_id="new_encrypted_id"
        )
        # Returns: "public/profiles/lawyers/2025/12/new_encrypted_id/1765533886_/*.png"
    """
    try:
        upload_service = UploadService()
        # Process new photo upload
        encrypted_id = encrypt_id(str(entity_id))
        if not encrypted_id:
            logger.error("Failed to encrypt entity ID")
            return None
        # Extract base folder path and extension from existing path
        base_folder_path, file_extension = _extract_path_and_extension(existing_path)

        if not base_folder_path:
            logger.error(f"Could not extract base folder path from: {existing_path}")
            return None

        # List all files in the existing folder
        existing_files = upload_service._list_files_in_folder(base_folder_path)
        if not existing_files:
            logger.warning(f"No files found in existing folder: {base_folder_path}")
            return None

        # Generate new storage path based on entity type and entity ID
        new_storage_path = upload_service._generate_storage_path(entity_type, encrypted_id)
        if not new_storage_path:
            logger.error(f"Failed to generate new storage path for entity: {entity_type}")
            return None

        # Copy each file from existing location to new location
        copied_files = []
        for existing_file_key in existing_files:
            # Extract the filename from the existing file key
            # Format: "public/profiles/lawyers/2025/12/old_id/timestamp_thumbnail.png"
            # We need: "thumbnail.png" (or "medium.png", "large.png", etc.)
            # Extract just the part after the last underscore, e.g. "thumbnail.png" from "timestamp_thumbnail.png"
            original_filename = existing_file_key.split("/")[-1]
            filename = "_".join(original_filename.split("_")[1:]) if "_" in original_filename else original_filename
            # Create new file key with the same filename in the new location
            # Note: new_storage_path already ends with "timestamp_" so we append directly
            new_file_key = f"{new_storage_path}{filename}"
            # Copy file from existing location to new location
            if upload_service.s3_service.copy_file(existing_file_key, new_file_key):
                copied_files.append(new_file_key)
                logger.info(f"Successfully copied {existing_file_key} to {new_file_key}")
            else:
                logger.error(f"Failed to copy {existing_file_key} to {new_file_key}")
                # Continue copying other files even if one fails

        if not copied_files:
            logger.error("No files were successfully copied")
            return None

        logger.info(f"Successfully copied {len(copied_files)} file(s) from {base_folder_path} to {new_storage_path}")

        # Return new path with extension pattern (same as process_uploaded_file)
        # Use extracted extension if available, otherwise default to "jpg"
        final_extension = file_extension if file_extension else "jpg"
        return f"{new_storage_path}/*.{final_extension}"

    except Exception as e:
        logger.exception(f"Error copying files to new location: {e}")
        return None
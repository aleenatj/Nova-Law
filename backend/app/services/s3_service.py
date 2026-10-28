"""S3 service for file operations."""

import logging
from io import BytesIO
from typing import ClassVar

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from PIL import Image

from app.core.config import settings
from app.enums.file_upload import ImageSize
from app.services.cloudfront_service import CloudFrontService

logger = logging.getLogger(__name__)


class S3Service:
    """Service for S3 file operations.

    Uses class-level caching for the boto3 client and CloudFront service
    to avoid expensive re-initialization on every instantiation.
    """

    _s3_client: ClassVar[object | None] = None
    _bucket_name: ClassVar[str | None] = None
    _cloudfront_service: ClassVar[CloudFrontService | None] = None

    def __init__(self) -> None:
        """Initialize S3 service with AWS credentials (cached at class level)."""
        if S3Service._s3_client is None:
            try:
                S3Service._s3_client = boto3.client(
                    "s3",
                    aws_access_key_id=settings.AWS_S3_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_S3_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION,
                )
                S3Service._bucket_name = (
                    settings.S3_BUCKET_NAME
                    if hasattr(settings, "S3_BUCKET_NAME")
                    else "nova-law-uploads"
                )
                S3Service._cloudfront_service = CloudFrontService()
            except NoCredentialsError:
                logger.exception("AWS credentials not found")
                raise
            except Exception as e:
                logger.exception(f"Error initializing S3 service: {e}")
                raise
        self.s3_client = S3Service._s3_client
        self.bucket_name: str = S3Service._bucket_name  # type: ignore[assignment]
        self.cloudfront_service: CloudFrontService = S3Service._cloudfront_service  # type: ignore[assignment]

    def generate_presigned_url(
        self,
        key: str,
        expiration: int = 900,
        http_method: str = 'PUT'
    ) -> str | None:
        """
        Generate a pre-signed URL for S3 operations.

        Pre-signed URLs allow temporary access to S3 objects without requiring
        AWS credentials on the client side. This is commonly used for:
        - Direct file uploads from frontend to S3
        - Temporary access to private files
        - Secure file sharing with expiration

        Args:
            key: S3 object key (path within bucket)
            expiration: URL expiration time in seconds (default: 15 minutes)
            http_method: HTTP method for the URL (default: PUT for uploads)

        Returns:
            Pre-signed URL string or None if error occurs

        Example:
            url = s3_service.generate_presigned_url("temp/uuid.jpg", 3600)
            # Returns: "https://bucket.s3.region.amazonaws.com/temp/uuid.jpg?AWSAccessKeyId=..."
        """
        try:
            response = self.s3_client.generate_presigned_url(
                'put_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=expiration,
                HttpMethod=http_method
            )
            return str(response)
        except ClientError as e:
            logger.exception(f"Error generating presigned URL: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error generating presigned URL: {e}")
            return None

    def generate_presigned_download_url(
        self,
        key: str,
        expiration: int | None = None
    ) -> str | None:
        """
        Generate a pre-signed URL for downloading/viewing private files.

        This method creates temporary URLs for accessing private S3 objects.
        The URL expires after the configured time period, ensuring files
        remain secure and are not permanently accessible.

        Args:
            key: S3 object key (path to file in bucket)
            expiration: URL expiration time in seconds. If None, uses
                       S3_PRESIGNED_URL_EXPIRY_SECONDS from settings (default: 3600)

        Returns:
            Pre-signed URL for GET operation or None if error occurs

        Example:
            # Generate URL that expires in 1 hour (default)
            url = s3_service.generate_presigned_download_url(
                "private/documents/lawyers/2025/03/encrypted_id/contract.pdf"
            )
            # Returns: "https://bucket.s3.region.amazonaws.com/private/...?AWSAccessKeyId=...&Expires=..."

            # Generate URL with custom expiry (24 hours)
            url = s3_service.generate_presigned_download_url(
                "private/documents/lawyers/2025/03/encrypted_id/contract.pdf",
                expiration=86400
            )
        """
        try:
            # Use configured expiry if not specified
            if expiration is None:
                from app.core.config import settings
                expiration = settings.S3_PRESIGNED_URL_EXPIRY_SECONDS

            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': key
                },
                ExpiresIn=expiration
            )

            logger.info(f"Generated pre-signed download URL for {key} (expires in {expiration}s)")
            return str(response)

        except ClientError as e:
            logger.exception(f"Error generating presigned download URL for {key}: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error generating presigned download URL: {e}")
            return None

    def upload_file(
        self,
        file_content: bytes,
        key: str,
        content_type: str = 'application/octet-stream',
        is_private: bool | None = None
    ) -> bool:
        """
        Upload file content directly to S3 with appropriate ACL settings.

        This method uploads binary data to S3 with proper content type headers
        and sets the correct ACL based on file visibility (public/private).

        Args:
            file_content: File content as bytes (from file.read() or image processing)
            key: S3 object key (destination path)
            content_type: MIME type of the file (e.g., 'image/jpeg', 'application/pdf')
            is_private: If True, file is private. If False, file is public.
                       If None, determines from key prefix (private/ vs public/)

        Returns:
            True if upload successful, False if error occurs

        Example:
            # Public file
            success = s3_service.upload_file(
                file_content=image_bytes,
                key="public/profiles/lawyers/2024/1/encrypted_id/thumbnail.jpg",
                content_type="image/jpeg"
            )

            # Private file
            success = s3_service.upload_file(
                file_content=document_bytes,
                key="private/documents/lawyers/2024/1/encrypted_id/contract.pdf",
                content_type="application/pdf",
                is_private=True
            )
        """
        try:
            # Determine if file is private based on key prefix if not explicitly specified
            if is_private is None:
                is_private = not self._is_public_file(key)

            # Set ACL based on visibility
            acl = 'private' if is_private else None

            payload = {
                'Bucket': self.bucket_name,
                'Key': key,
                'Body': file_content,
                'ContentType': content_type,
                # ACL=acl
            }
            if acl:
                payload['ACL'] = acl
            self.s3_client.put_object(**payload)

            logger.info(f"Uploaded file to S3: {key} (ACL: {acl})")
            return True

        except ClientError as e:
            logger.exception(f"Error uploading file to S3: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error uploading file: {e}")
            return False

    def download_file(self, key: str) -> bytes | None:
        """
        Download file content from S3.

        This method retrieves binary data from S3 for processing.
        It's commonly used to download temporary files for image processing
        or document handling before moving to permanent storage.

        Args:
            key: S3 object key (path to file in bucket)

        Returns:
            File content as bytes or None if error occurs

        Example:
            content = s3_service.download_file("temp/uuid.jpg")
            if content:
                # Process the file content
                processed = process_image(content)
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return bytes(response['Body'].read())
        except ClientError as e:
            logger.exception(f"Error downloading file from S3: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error downloading file: {e}")
            return None

    def delete_file(self, key: str) -> bool:
        """
        Delete file from S3.

        Args:
            key: S3 object key

        Returns:
            True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            logger.exception(f"Error deleting file from S3: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error deleting file: {e}")
            return False

    def copy_file(self, source_key: str, dest_key: str) -> bool:
        """
        Copy file within S3.

        Args:
            source_key: Source S3 object key
            dest_key: Destination S3 object key

        Returns:
            True if successful, False otherwise
        """
        try:
            copy_source = {'Bucket': self.bucket_name, 'Key': source_key}
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=dest_key
            )
            return True
        except ClientError as e:
            logger.exception(f"Error copying file in S3: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error copying file: {e}")
            return False

    def get_public_url(self, key: str) -> str:
        """
        Get public URL for S3 object using CloudFront if configured.
        Only serves files from the public/ folder through CloudFront.

        For private files, use generate_presigned_download_url() instead.

        Args:
            key: S3 object key

        Returns:
            Public URL for the object (CloudFront URL if configured and file is public, otherwise S3 URL)
        """
        # Check if file is in public folder
        if not self._is_public_file(key):
            # For private files, return S3 URL (not accessible via CloudFront)
            logger.warning(f"Attempted to get public URL for private file: {key}. Use generate_presigned_download_url() instead.")
            return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"

        # Use CloudFront URL if configured, otherwise fall back to S3 URL
        if self.cloudfront_service.is_cloudfront_configured():
            return self.cloudfront_service.get_cloudfront_url(key)
        else:
            return f"https://{self.bucket_name}.s3.{settings.AWS_REGION}.amazonaws.com/{key}"

    def get_file_url(self, key: str, expiration: int | None = None) -> str | None:
        """
        Get appropriate URL for a file based on its visibility (public or private).

        This is a convenience method that automatically determines whether to
        return a public CloudFront URL or a private pre-signed URL based on
        the file path prefix.

        Args:
            key: S3 object key
            expiration: For private files, URL expiration time in seconds.
                       If None, uses S3_PRESIGNED_URL_EXPIRY_SECONDS from settings.
                       Ignored for public files.

        Returns:
            Public CloudFront URL for public files, pre-signed URL for private files,
            or None if error occurs for private files

        Example:
            # Public file - returns CloudFront URL
            url = s3_service.get_file_url("public/profiles/lawyers/2025/03/abc123/thumbnail.jpg")
            # Returns: "https://d1234567890.cloudfront.net/public/..."

            # Private file - returns pre-signed URL
            url = s3_service.get_file_url("private/documents/lawyers/2025/03/abc123/contract.pdf")
            # Returns: "https://bucket.s3.region.amazonaws.com/private/...?AWSAccessKeyId=...&Expires=..."
        """
        if self._is_public_file(key):
            # Public file - return CloudFront or public S3 URL
            return self.get_public_url(key)
        else:
            # Private file - return pre-signed URL
            return self.generate_presigned_download_url(key, expiration)

    def _is_public_file(self, key: str) -> bool:
        """
        Check if a file is in the public folder.

        Args:
            key: S3 object key

        Returns:
            True if file is in public folder, False otherwise
        """
        return key.startswith("public/")

    def file_exists(self, key: str) -> bool:
        """
        Check if file exists in S3.

        Args:
            key: S3 object key

        Returns:
            True if file exists, False otherwise
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            logger.exception(f"Error checking file existence: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error checking file existence: {e}")
            return False

    def get_file_size(self, key: str) -> int | None:
        """
        Get file size from S3 without downloading the file.

        Args:
            key: S3 object key

        Returns:
            File size in bytes, or None if file doesn't exist or error occurs
        """
        try:
            response = self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return response.get('ContentLength', None)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.warning(f"File not found in S3: {key}")
                return None
            logger.exception(f"Error getting file size: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error getting file size: {e}")
            return None

    def invalidate_cloudfront_cache(self, paths: list[str]) -> bool:
        """
        Invalidate CloudFront cache for specified paths.

        Args:
            paths: List of paths to invalidate

        Returns:
            True if invalidation successful, False otherwise
        """
        try:
            if not self.cloudfront_service.is_cloudfront_configured():
                logger.info("CloudFront not configured, skipping cache invalidation")
                return True

            return self.cloudfront_service.invalidate_cache(paths)
        except Exception as e:
            logger.exception(f"Error invalidating CloudFront cache: {e}")
            return False

    def list_objects_in_folder(self, prefix: str) -> list[str]:
        """
        List all object keys in an S3 folder.

        Args:
            prefix: Folder prefix to search (e.g., "public/profiles/lawyers/2025/09/")

        Returns:
            List of S3 object keys found in the folder
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )

            if 'Contents' not in response:
                return []

            return [obj['Key'] for obj in response['Contents']]
        except ClientError as e:
            logger.exception(f"Error listing objects in folder {prefix}: {e}")
            return []
        except Exception as e:
            logger.exception(f"Unexpected error listing objects: {e}")
            return []

    def find_existing_entity_folders(self, base_prefix: str, encrypted_entity_id: str, recursive: bool = False) -> list[str]:
        """
        Find all existing folders for an entity.

        This searches for folders matching the pattern:
        {base_prefix}/**/{encrypted_entity_id}/ (if recursive=True)
        OR
        {base_prefix}/{encrypted_entity_id}/ (if recursive=False)

        Args:
            base_prefix: Base path prefix (e.g., "public/profiles/lawyers/" for recursive search)
            encrypted_entity_id: Encrypted entity ID
            recursive: If True, searches all subdirectories (years/months), if False only direct children

        Returns:
            List of folder paths found
        """
        try:
            if recursive:
                # For recursive search, we need to list all objects and filter
                # This handles cross-month/year scenarios
                folders_set: set[str] = set()
                continuation_token = None

                while True:
                    list_params = {
                        'Bucket': self.bucket_name,
                        'Prefix': base_prefix,
                        'Delimiter': '/'
                    }

                    if continuation_token:
                        list_params['ContinuationToken'] = continuation_token

                    response = self.s3_client.list_objects_v2(**list_params)

                    # Get all common prefixes (subdirectories)
                    if 'CommonPrefixes' in response:
                        for prefix_obj in response['CommonPrefixes']:
                            subfolder = prefix_obj['Prefix']
                            # Recursively search in this subfolder
                            subfolders = self.find_existing_entity_folders(subfolder, encrypted_entity_id, recursive=False)
                            folders_set.update(subfolders)

                    # Check if there are more results
                    if not response.get('IsTruncated', False):
                        break

                    continuation_token = response.get('NextContinuationToken')

                return list(folders_set)
            else:
                # Non-recursive: only search in the given prefix
                response = self.s3_client.list_objects_v2(
                    Bucket=self.bucket_name,
                    Prefix=base_prefix,
                    Delimiter='/'
                )

                if 'CommonPrefixes' not in response:
                    return []

                # Filter folders that match the entity ID pattern
                folders = []
                for prefix_obj in response['CommonPrefixes']:
                    folder = prefix_obj['Prefix']
                    # Extract folder name from path
                    folder_name = folder.rstrip('/').split('/')[-1]
                    # Check if it matches encrypted_entity_id exactly
                    if folder_name == encrypted_entity_id:
                        folders.append(folder)

                return folders
        except ClientError as e:
            logger.exception(f"Error finding existing folders: {e}")
            return []
        except Exception as e:
            logger.exception(f"Unexpected error finding folders: {e}")
            return []

    def tag_objects_with_expire(self, object_keys: list[str]) -> bool:
        """
        Tag multiple S3 objects with 'expire=true'.

        Args:
            object_keys: List of S3 object keys to tag

        Returns:
            True if all objects tagged successfully, False otherwise
        """
        success = True
        for key in object_keys:
            if not self.tag_object(key, {'expire': 'true'}):
                success = False
                logger.error(f"Failed to tag object: {key}")
        return success

    def tag_object(self, key: str, tags: dict[str, str]) -> bool:
        """
        Add tags to an S3 object.

        Args:
            key: S3 object key
            tags: Dictionary of tags to add (key-value pairs)

        Returns:
            True if tagging successful, False otherwise
        """
        try:
            # Convert tags dict to AWS tag format
            tag_set = [{'Key': k, 'Value': v} for k, v in tags.items()]

            self.s3_client.put_object_tagging(
                Bucket=self.bucket_name,
                Key=key,
                Tagging={'TagSet': tag_set}
            )
            logger.info(f"Successfully tagged object {key} with {tags}")
            return True
        except ClientError as e:
            logger.exception(f"Error tagging object {key}: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error tagging object: {e}")
            return False

    def configure_lifecycle_policy_for_expired_objects(self, days_to_expire: int = 30) -> bool:
        """
        Configure S3 lifecycle policy to automatically delete objects tagged with expire=true.

        This creates a lifecycle rule that will automatically delete objects with the
        'expire=true' tag after the specified number of days.

        Args:
            days_to_expire: Number of days after which tagged objects will be deleted (default: 30)

        Returns:
            True if lifecycle policy configured successfully, False otherwise

        Example:
            # Configure to delete expired objects after 30 days
            s3_service.configure_lifecycle_policy_for_expired_objects(30)
        """
        try:
            lifecycle_config = {
                'Rules': [
                    {
                        'Id': 'DeleteExpiredProfileImages',
                        'Status': 'Enabled',
                        'Filter': {
                            'Tag': {
                                'Key': 'expire',
                                'Value': 'true'
                            }
                        },
                        'Expiration': {
                            'Days': days_to_expire
                        }
                    }
                ]
            }

            self.s3_client.put_bucket_lifecycle_configuration(
                Bucket=self.bucket_name,
                LifecycleConfiguration=lifecycle_config
            )

            logger.info(f"Successfully configured lifecycle policy to delete objects with expire=true after {days_to_expire} days")
            return True

        except ClientError as e:
            logger.exception(f"Error configuring lifecycle policy: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error configuring lifecycle policy: {e}")
            return False

    def get_bucket_lifecycle_policy(self) -> list | None:
        """
        Get the current S3 bucket lifecycle policy.

        Returns:
            List of lifecycle rules or None if not configured/error
        """
        try:
            response = self.s3_client.get_bucket_lifecycle_configuration(
                Bucket=self.bucket_name
            )
            rules: list = response.get('Rules', [])
            return rules
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchLifecycleConfiguration':
                logger.info("No lifecycle configuration exists for bucket")
                return None
            logger.exception(f"Error getting lifecycle policy: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected error getting lifecycle policy: {e}")
            return None


class FileProcessor:
    """Service for file processing operations."""

    # Image size configurations
    IMAGE_SIZES: ClassVar[dict[ImageSize, tuple[int, int]]] = {
        ImageSize.THUMBNAIL: (100, 100),
        ImageSize.MEDIUM: (300, 300),
        ImageSize.LARGE: (600, 600)
    }

    @staticmethod
    def is_image_file(extension: str) -> bool:
        """
        Check if file extension is a supported image format.

        Only supports PNG, JPEG, and HEIC/HEIF formats as per requirements.

        Args:
            extension: File extension

        Returns:
            True if supported image format, False otherwise
        """
        supported_image_extensions = {'jpg', 'jpeg', 'png', 'heic', 'heif','webp'}
        return extension.lower() in supported_image_extensions

    @staticmethod
    def resize_image(
        image_content: bytes,
        size: ImageSize,
        quality: int = 85
    ) -> bytes | None:
        """
        Resize image to specified size.

        Args:
            image_content: Original image content as bytes
            size: Target image size
            quality: JPEG quality (1-100)

        Returns:
            Resized image content as bytes or None if error
        """
        try:
            # Open image from bytes
            image = Image.open(BytesIO(image_content))

            # Convert to RGB if necessary (for JPEG compatibility)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')  # type: ignore
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background  # type: ignore
            elif image.mode != 'RGB':
                image = image.convert('RGB')  # type: ignore

            # Get target dimensions
            target_size = FileProcessor.IMAGE_SIZES.get(size)
            if not target_size:
                logger.error(f"Unknown image size: {size}")
                return None

            # Resize image maintaining aspect ratio
            image.thumbnail(target_size, Image.Resampling.LANCZOS)

            # Save to bytes
            output = BytesIO()
            image.save(output, format='JPEG', quality=quality, optimize=True)
            return output.getvalue()

        except Exception as e:
            logger.exception(f"Error resizing image: {e}")
            return None



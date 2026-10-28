"""CloudFront service for CDN operations."""

import logging
from typing import ClassVar

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

from app.core.config import settings

logger = logging.getLogger(__name__)


class CloudFrontService:
    """Service for CloudFront CDN operations.

    Uses class-level caching for the boto3 client to avoid expensive
    re-initialization on every instantiation.
    """

    _cloudfront_client: ClassVar[object | None] = None
    _distribution_id: ClassVar[str | None] = None
    _cloudfront_domain: ClassVar[str | None] = None

    def __init__(self) -> None:
        """Initialize CloudFront service with AWS credentials (cached at class level)."""
        if CloudFrontService._cloudfront_client is None:
            try:
                CloudFrontService._cloudfront_client = boto3.client(
                    "cloudfront",
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION,
                )
                CloudFrontService._distribution_id = (
                    settings.CLOUDFRONT_DISTRIBUTION_ID
                )
                CloudFrontService._cloudfront_domain = settings.CLOUDFRONT_DOMAIN
            except NoCredentialsError:
                logger.exception("AWS credentials not found")
                raise
            except Exception as e:
                logger.exception(f"Error initializing CloudFront service: {e}")
                raise
        self.cloudfront_client = CloudFrontService._cloudfront_client
        self.distribution_id: str | None = CloudFrontService._distribution_id
        self.cloudfront_domain: str | None = CloudFrontService._cloudfront_domain

    def get_cloudfront_url(self, s3_key: str) -> str:
        """
        Generate CloudFront URL for an S3 object.

        Args:
            s3_key: S3 object key (e.g., "public/profiles/lawyers/2024/1/encrypted_id/thumbnail.jpg")

        Returns:
            CloudFront URL for the object (with "public/" prefix removed)

        Example:
            url = cloudfront_service.get_cloudfront_url("public/profiles/lawyers/2024/1/encrypted_id/thumbnail.jpg")
            # Returns: "https://d1234567890.cloudfront.net/profiles/lawyers/2024/1/encrypted_id/thumbnail.jpg"
        """
        try:
            if not self.cloudfront_domain:
                logger.warning("CloudFront domain not configured, falling back to S3 URL")
                return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

            # Ensure s3_key doesn't start with '/'
            if s3_key.startswith('/'):
                s3_key = s3_key[1:]

            # Remove "public/" prefix from the URL path if present
            if s3_key.startswith('public/'):
                s3_key = s3_key[7:]  # Remove "public/" (7 characters)

            return f"https://{self.cloudfront_domain}/{s3_key}"
        except Exception as e:
            logger.exception(f"Error generating CloudFront URL: {e}")
            # Fallback to S3 URL
            return f"https://{settings.S3_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

    def invalidate_cache(self, paths: list[str]) -> bool:
        """
        Invalidate CloudFront cache for specified paths.

        This method creates an invalidation request to clear cached content
        from CloudFront edge locations. Useful when files are updated or deleted.

        Args:
            paths: List of paths to invalidate (e.g., ["/profiles/lawyers/2024/1/encrypted_id/*"])

        Returns:
            True if invalidation request successful, False otherwise

        Example:
            success = cloudfront_service.invalidate_cache([
                "/profiles/lawyers/2024/1/encrypted_id/*"
            ])
        """
        try:
            if not self.distribution_id:
                logger.error("CloudFront distribution ID not configured")
                return False

            # Ensure paths start with '/'
            formatted_paths = []
            for path in paths:
                if not path.startswith('/'):
                    path = '/' + path
                formatted_paths.append(path)

            response = self.cloudfront_client.create_invalidation(
                DistributionId=self.distribution_id,
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(formatted_paths),
                        'Items': formatted_paths
                    },
                    'CallerReference': f"invalidation-{int(__import__('time').time())}"
                }
            )

            invalidation_id = response['Invalidation']['Id']
            logger.info(f"CloudFront invalidation created: {invalidation_id}")
            return True

        except ClientError as e:
            logger.exception(f"Error creating CloudFront invalidation: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error creating invalidation: {e}")
            return False


    def is_cloudfront_configured(self) -> bool:
        """
        Check if CloudFront is properly configured.

        Returns:
            True if CloudFront is configured, False otherwise
        """
        return bool(self.cloudfront_domain and self.distribution_id)


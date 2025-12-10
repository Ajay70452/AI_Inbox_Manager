"""
Storage Service

Handles storing and retrieving email content from S3/CloudFlare R2
"""

import logging
from typing import Optional
import boto3
from botocore.exceptions import ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for storing email content in S3/R2"""

    def __init__(self):
        """Initialize S3 client"""
        self.bucket_name = settings.S3_BUCKET_NAME

        # Initialize boto3 client
        # This works with both AWS S3 and CloudFlare R2
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=settings.AWS_REGION
            )
            self.enabled = True
            logger.info(f"Storage service initialized with bucket: {self.bucket_name}")
        else:
            self.s3_client = None
            self.enabled = False
            logger.warning("Storage service disabled - no AWS credentials configured")

    def upload_email_html(
        self,
        email_id: str,
        html_content: str,
        user_id: str
    ) -> Optional[str]:
        """
        Upload email HTML content to S3/R2

        Args:
            email_id: Unique email identifier
            html_content: HTML content to store
            user_id: User ID for organizing files

        Returns:
            S3 URL or None if storage is disabled/failed
        """
        if not self.enabled:
            logger.debug("Storage disabled, skipping upload")
            return None

        try:
            # Create organized key: user_id/emails/email_id.html
            key = f"{user_id}/emails/{email_id}.html"

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=html_content.encode('utf-8'),
                ContentType='text/html',
                ServerSideEncryption='AES256'  # Encrypt at rest
            )

            # Generate URL (note: this is the S3 path, not a public URL)
            url = f"s3://{self.bucket_name}/{key}"
            logger.info(f"Uploaded email HTML to {url}")

            return url

        except ClientError as e:
            logger.error(f"Failed to upload email HTML: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading email HTML: {str(e)}")
            return None

    def download_email_html(
        self,
        url: str
    ) -> Optional[str]:
        """
        Download email HTML content from S3/R2

        Args:
            url: S3 URL (e.g., s3://bucket/key)

        Returns:
            HTML content or None if failed
        """
        if not self.enabled:
            return None

        try:
            # Parse S3 URL
            if not url.startswith('s3://'):
                logger.error(f"Invalid S3 URL: {url}")
                return None

            # Extract bucket and key
            url_parts = url.replace('s3://', '').split('/', 1)
            if len(url_parts) != 2:
                logger.error(f"Invalid S3 URL format: {url}")
                return None

            bucket, key = url_parts

            # Download from S3
            response = self.s3_client.get_object(
                Bucket=bucket,
                Key=key
            )

            content = response['Body'].read().decode('utf-8')
            logger.info(f"Downloaded email HTML from {url}")

            return content

        except ClientError as e:
            logger.error(f"Failed to download email HTML: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading email HTML: {str(e)}")
            return None

    def delete_email_html(
        self,
        url: str
    ) -> bool:
        """
        Delete email HTML content from S3/R2

        Args:
            url: S3 URL

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Parse S3 URL
            if not url.startswith('s3://'):
                return False

            url_parts = url.replace('s3://', '').split('/', 1)
            if len(url_parts) != 2:
                return False

            bucket, key = url_parts

            # Delete from S3
            self.s3_client.delete_object(
                Bucket=bucket,
                Key=key
            )

            logger.info(f"Deleted email HTML from {url}")
            return True

        except ClientError as e:
            logger.error(f"Failed to delete email HTML: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting email HTML: {str(e)}")
            return False

    def upload_attachment(
        self,
        email_id: str,
        attachment_id: str,
        content: bytes,
        filename: str,
        content_type: str,
        user_id: str
    ) -> Optional[str]:
        """
        Upload email attachment to S3/R2

        Args:
            email_id: Email identifier
            attachment_id: Attachment identifier
            content: Attachment binary content
            filename: Original filename
            content_type: MIME type
            user_id: User ID

        Returns:
            S3 URL or None if failed
        """
        if not self.enabled:
            return None

        try:
            # Create key: user_id/attachments/email_id/attachment_id_filename
            key = f"{user_id}/attachments/{email_id}/{attachment_id}_{filename}"

            # Upload to S3
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=content,
                ContentType=content_type,
                ServerSideEncryption='AES256',
                Metadata={
                    'original_filename': filename,
                    'email_id': email_id
                }
            )

            url = f"s3://{self.bucket_name}/{key}"
            logger.info(f"Uploaded attachment to {url}")

            return url

        except ClientError as e:
            logger.error(f"Failed to upload attachment: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading attachment: {str(e)}")
            return None


# Global storage service instance
storage_service = StorageService()

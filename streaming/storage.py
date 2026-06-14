import logging
from datetime import timedelta
from django.conf import settings
import boto3
from botocore.exceptions import ClientError
from botocore.config import Config

logger = logging.getLogger(__name__)


class MinIOStorage:
    """
    MinIO / S3-compatible storage client.
    Generates presigned URLs for secure video access.
    """

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = boto3.client(
                "s3",
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                config=Config(
                    signature_version="s3v4",
                    connect_timeout=5,
                    retries={"max_attempts": 3},
                ),
                verify=settings.AWS_S3_VERIFY,
            )
        return self._client

    def generate_presigned_url(
        self,
        file_key: str,
        expires_in: int = 3600,
        bucket: str | None = None,
    ) -> str | None:
        """
        Generate a time-limited presigned URL.
        Default expiry: 1 hour.
        """
        bucket = bucket or settings.AWS_STORAGE_BUCKET_NAME
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": bucket, "Key": file_key},
                ExpiresIn=expires_in,
            )
            logger.debug("Presigned URL generated for: %s", file_key)
            return url
        except ClientError as exc:
            logger.error("Failed to generate presigned URL for %s: %s", file_key, exc)
            return None

    def upload_file(
        self,
        file_path: str,
        file_key: str,
        content_type: str = "application/octet-stream",
        bucket: str | None = None,
    ) -> bool:
        """Upload a local file to MinIO."""
        bucket = bucket or settings.AWS_STORAGE_BUCKET_NAME
        try:
            self.client.upload_file(
                file_path,
                bucket,
                file_key,
                ExtraArgs={"ContentType": content_type},
            )
            logger.info("File uploaded: %s → %s/%s", file_path, bucket, file_key)
            return True
        except ClientError as exc:
            logger.error("Upload failed for %s: %s", file_key, exc)
            return False

    def download_file(
        self,
        file_key: str,
        local_path: str,
        bucket: str | None = None,
    ) -> bool:
        """Download a file from MinIO to a local path."""
        bucket = bucket or settings.AWS_STORAGE_BUCKET_NAME
        try:
            self.client.download_file(bucket, file_key, local_path)
            logger.info("File downloaded: %s/%s → %s", bucket, file_key, local_path)
            return True
        except ClientError as exc:
            logger.error("Download failed for %s: %s", file_key, exc)
            return False

    def delete_file(self, file_key: str, bucket: str | None = None) -> bool:
        bucket = bucket or settings.AWS_STORAGE_BUCKET_NAME
        try:
            self.client.delete_object(Bucket=bucket, Key=file_key)
            logger.info("File deleted: %s", file_key)
            return True
        except ClientError as exc:
            logger.error("Delete failed for %s: %s", file_key, exc)
            return False

    def file_exists(self, file_key: str, bucket: str | None = None) -> bool:
        bucket = bucket or settings.AWS_STORAGE_BUCKET_NAME
        try:
            self.client.head_object(Bucket=bucket, Key=file_key)
            return True
        except ClientError:
            return False


# Singleton instance
minio_storage = MinIOStorage()
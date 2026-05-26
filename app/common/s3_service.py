"""
app/common/s3_service.py
~~~~~~~~~~~~~~~~~~~~~~~~
AWS S3 storage service for GrantThrive.

All file uploads (application documents, council logos) are stored in S3.
Files are never written to the local filesystem in production.

Configuration (set via environment variables / AWS Secrets Manager):
    AWS_S3_BUCKET       — S3 bucket name, e.g. "grantthrive-documents-prod"
    AWS_REGION          — AWS region, e.g. "ap-southeast-2"
    AWS_ACCESS_KEY_ID   — (optional) explicit credentials; omit when running on
                          ECS with an IAM task role (recommended)
    AWS_SECRET_ACCESS_KEY — (optional) see above

Usage:
    from app.common.s3_service import s3_service

    # Upload a file-like object
    key = s3_service.upload_fileobj(file_stream, "documents/council-1/myfile.pdf",
                                    content_type="application/pdf")

    # Generate a time-limited pre-signed download URL (default 1 hour)
    url = s3_service.generate_presigned_url(key)

    # Delete an object
    s3_service.delete_object(key)
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Allowed file types for application documents and council logos
# ---------------------------------------------------------------------------
ALLOWED_DOCUMENT_EXTENSIONS: set[str] = {
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "txt", "csv", "png", "jpg", "jpeg", "gif", "webp",
}
ALLOWED_LOGO_EXTENSIONS: set[str] = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

# Maximum file sizes
MAX_DOCUMENT_SIZE_BYTES: int = 20 * 1024 * 1024   # 20 MB
MAX_LOGO_SIZE_BYTES: int     = 5  * 1024 * 1024   # 5 MB


class S3StorageService:
    """Thin wrapper around boto3 S3 client providing upload, pre-signed URL
    generation, and deletion helpers used throughout GrantThrive."""

    def __init__(self) -> None:
        self._bucket: str | None = None
        self._region: str | None = None
        self._client = None

    # ------------------------------------------------------------------
    # Lazy initialisation — boto3 client is created on first use so that
    # the module can be imported without AWS credentials present (e.g.
    # during local development or unit tests).
    # ------------------------------------------------------------------

    def _get_client(self):
        if self._client is None:
            self._region = os.environ.get("AWS_REGION", "ap-southeast-2")
            self._bucket = os.environ.get("AWS_S3_BUCKET")

            if not self._bucket:
                raise RuntimeError(
                    "AWS_S3_BUCKET environment variable is not set. "
                    "Set it to your S3 bucket name before using file uploads."
                )

            # When running on ECS with an IAM task role, boto3 picks up
            # credentials automatically from the instance metadata service.
            # Explicit key/secret are supported for local development.
            kwargs: dict = {"region_name": self._region}
            access_key = os.environ.get("AWS_ACCESS_KEY_ID")
            secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
            if access_key and secret_key:
                kwargs["aws_access_key_id"] = access_key
                kwargs["aws_secret_access_key"] = secret_key

            self._client = boto3.client("s3", **kwargs)

        return self._client

    @property
    def bucket(self) -> str:
        self._get_client()   # ensure _bucket is populated
        return self._bucket  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        s3_key: str,
        content_type: str = "application/octet-stream",
        extra_metadata: dict | None = None,
    ) -> str:
        """Upload a file-like object to S3 and return the S3 key.

        Files are stored with:
        - Server-side encryption (AES-256) enabled
        - Private ACL (no public access)
        - Content-Type metadata for correct browser handling

        Args:
            fileobj:        A readable binary file-like object (e.g. from
                            ``request.files['file'].stream``).
            s3_key:         The full S3 object key (path within the bucket).
            content_type:   MIME type of the file.
            extra_metadata: Optional dict of user-defined S3 metadata.

        Returns:
            The S3 key of the uploaded object.

        Raises:
            RuntimeError: If the upload fails.
        """
        client = self._get_client()

        extra_args: dict = {
            "ContentType": content_type,
            "ServerSideEncryption": "AES256",
        }
        if extra_metadata:
            extra_args["Metadata"] = {
                str(k): str(v) for k, v in extra_metadata.items()
            }

        try:
            client.upload_fileobj(fileobj, self.bucket, s3_key, ExtraArgs=extra_args)
            logger.info("S3 upload successful: s3://%s/%s", self.bucket, s3_key)
            return s3_key
        except (ClientError, NoCredentialsError) as exc:
            logger.error("S3 upload failed for key '%s': %s", s3_key, exc)
            raise RuntimeError(f"File upload failed: {exc}") from exc

    def generate_presigned_url(
        self,
        s3_key: str,
        expiry_seconds: int = 3600,
        filename_hint: str | None = None,
    ) -> str:
        """Generate a pre-signed GET URL for a private S3 object.

        The URL is valid for ``expiry_seconds`` (default 1 hour) and allows
        the holder to download the file without AWS credentials.

        Args:
            s3_key:         The S3 object key to generate a URL for.
            expiry_seconds: How long (in seconds) the URL remains valid.
            filename_hint:  If provided, sets Content-Disposition so the
                            browser downloads the file with this name.

        Returns:
            A pre-signed HTTPS URL string.
        """
        client = self._get_client()

        params: dict = {
            "Bucket": self.bucket,
            "Key": s3_key,
        }
        if filename_hint:
            params["ResponseContentDisposition"] = (
                f'attachment; filename="{filename_hint}"'
            )

        try:
            url = client.generate_presigned_url(
                "get_object",
                Params=params,
                ExpiresIn=expiry_seconds,
            )
            return url
        except (ClientError, NoCredentialsError) as exc:
            logger.error(
                "Failed to generate pre-signed URL for key '%s': %s", s3_key, exc
            )
            raise RuntimeError(f"Could not generate download URL: {exc}") from exc

    def delete_object(self, s3_key: str) -> None:
        """Delete an object from S3.

        Silently logs and swallows errors so that a missing file does not
        prevent the database record from being cleaned up.

        Args:
            s3_key: The S3 object key to delete.
        """
        try:
            client = self._get_client()
            client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info("S3 delete successful: s3://%s/%s", self.bucket, s3_key)
        except Exception as exc:
            logger.warning(
                "S3 delete failed for key '%s' (continuing): %s", s3_key, exc
            )

    def object_exists(self, s3_key: str) -> bool:
        """Return True if the given S3 key exists in the bucket."""
        try:
            client = self._get_client()
            client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "404":
                return False
            raise

    # ------------------------------------------------------------------
    # Key generation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def make_document_key(council_id: int, application_id: int, filename: str) -> str:
        """Return a deterministic, collision-safe S3 key for an application document.

        Format: ``documents/council-{id}/application-{id}/{uuid}_{filename}``

        The UUID prefix prevents filename collisions when the same file is
        uploaded multiple times.
        """
        safe_name = _sanitize_filename(filename)
        unique_prefix = uuid.uuid4().hex[:12]
        return (
            f"documents/council-{council_id}/"
            f"application-{application_id}/"
            f"{unique_prefix}_{safe_name}"
        )

    @staticmethod
    def make_logo_key(council_id: int, filename: str) -> str:
        """Return a deterministic S3 key for a council logo.

        Format: ``logos/council-{id}/{uuid}_{filename}``
        """
        safe_name = _sanitize_filename(filename)
        unique_prefix = uuid.uuid4().hex[:12]
        return f"logos/council-{council_id}/{unique_prefix}_{safe_name}"

    # ------------------------------------------------------------------
    # Availability check
    # ------------------------------------------------------------------

    @staticmethod
    def is_configured() -> bool:
        """Return True if the AWS_S3_BUCKET environment variable is set.

        Used by routes to decide whether to attempt S3 operations or return
        a helpful error message in development.
        """
        return bool(os.environ.get("AWS_S3_BUCKET"))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _sanitize_filename(filename: str) -> str:
    """Strip directory components and replace unsafe characters."""
    # Take only the final component (path traversal protection)
    basename = filename.replace("\\", "/").split("/")[-1]
    # Replace anything outside safe characters with underscores
    import re
    safe = re.sub(r"[^\w\-.]", "_", basename)
    # Truncate base name to 100 chars to stay within S3 key limits
    name, _, ext = safe.rpartition(".")
    return f"{name[:100]}.{ext}" if ext else safe[:100]


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

#: Global service instance — import and use this directly in route modules.
s3_service = S3StorageService()

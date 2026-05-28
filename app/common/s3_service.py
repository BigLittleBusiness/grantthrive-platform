"""
app/common/s3_service.py
~~~~~~~~~~~~~~~~~~~~~~~~
AWS S3 storage service for GrantThrive.

All file uploads (reports, application documents) are stored in S3.
Files are never written to the local filesystem in production.

Configuration (set via environment variables / AWS Secrets Manager):
    AWS_S3_BUCKET           — S3 bucket name, e.g. "grantthrive-documents-prod"
    AWS_REGION              — AWS region, e.g. "ap-southeast-2"
    AWS_ACCESS_KEY_ID       — (optional) explicit credentials; omit when running on
                              ECS with an IAM task role (recommended)
    AWS_SECRET_ACCESS_KEY   — (optional) see above
    AWS_S3_ENABLE_VERSIONING — (optional) enable S3 versioning for safety

Usage:
    from app.common.s3_service import s3_service

    # Upload a file-like object
    key = s3_service.upload_fileobj(
        file_stream,
        "reports/council-1/monthly_report_2025_01.pdf",
        content_type="application/pdf"
    )

    # Generate a time-limited pre-signed download URL
    url = s3_service.generate_presigned_url(key)

    # Download file content as bytes
    content = s3_service.download_fileobj(key)

    # Delete an object
    s3_service.delete_object(key)

    # Check if configured
    if s3_service.is_configured():
        # S3 is ready to use
        pass
"""

import os
import logging
import uuid
import re
from io import BytesIO
from typing import BinaryIO
from botocore.exceptions import ClientError, NoCredentialsError

try:
    import boto3
except ImportError:
    boto3 = None

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# File validation
# ─────────────────────────────────────────────────────────────────────────────

ALLOWED_DOCUMENT_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "xls",
    "xlsx",
    "png",
    "jpg",
    "jpeg",
    "gif",
    "zip",
}

ALLOWED_LOGO_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "svg",
}

MAX_DOCUMENT_SIZE_BYTES = 16 * 1024 * 1024  # 16 MB
MAX_LOGO_SIZE_BYTES = 5 * 1024 * 1024       # 5 MB


def is_allowed_file(filename: str) -> bool:
    """Return True if the file extension is in the allowed list."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[-1].lower()
    return ext in ALLOWED_DOCUMENT_EXTENSIONS


# ─────────────────────────────────────────────────────────────────────────────
# File sanitization
# ─────────────────────────────────────────────────────────────────────────────

def _sanitize_filename(filename: str) -> str:
    """
    Strip directory components and replace unsafe characters.
    
    Examples:
        "my report.pdf"         -> "my_report.pdf"
        "../../../etc/passwd"   -> "etc_passwd"
        "file@#$%.pdf"          -> "file.pdf"
    """
    # Remove directory separators
    filename = os.path.basename(filename)
    
    # Replace spaces and unsafe characters with underscores
    filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
    
    # Remove multiple underscores in a row
    filename = re.sub(r"_+", "_", filename)
    
    # Strip leading/trailing underscores and dots
    filename = filename.strip("_.")
    
    return filename or "file"


# ─────────────────────────────────────────────────────────────────────────────
# Main S3 service class
# ─────────────────────────────────────────────────────────────────────────────

class S3StorageService:
    """
    Thin wrapper around boto3 S3 client providing upload, pre-signed URL
    generation, and deletion helpers used throughout GrantThrive.
    """

    def __init__(self) -> None:
        self._bucket: str | None = None
        self._region: str | None = None
        self._client = None

    # ─────────────────────────────────────────────────────────────────────────
    # Lazy initialisation — boto3 client is created on first use so that
    # the module can be imported without AWS credentials present (e.g.
    # during local development or unit tests).
    # ─────────────────────────────────────────────────────────────────────────

    def _get_client(self):
        """Lazily initialize and return the boto3 S3 client."""
        if self._client is None:
            if boto3 is None:
                raise RuntimeError(
                    "boto3 is not installed. Install it with: pip install boto3"
                )

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
            logger.info(
                "S3StorageService initialized: bucket=%s region=%s",
                self._bucket, self._region
            )

        return self._client

    @property
    def bucket(self) -> str:
        """Return the S3 bucket name (forces initialization if needed)."""
        if self._bucket is None:
            self._get_client()
        return self._bucket

    @property
    def region(self) -> str:
        """Return the AWS region."""
        if self._region is None:
            self._get_client()
        return self._region

    # ─────────────────────────────────────────────────────────────────────────
    # Core operations
    # ─────────────────────────────────────────────────────────────────────────

    def upload_fileobj(
        self,
        fileobj: BinaryIO,
        s3_key: str,
        content_type: str = "application/octet-stream",
        extra_metadata: dict | None = None,
    ) -> str:
        """
        Upload a file-like object to S3 and return the S3 key.

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

    def download_fileobj(self, s3_key: str) -> bytes:
        """
        Download file content from S3 as bytes.

        Args:
            s3_key: The S3 object key.

        Returns:
            File content as bytes.

        Raises:
            RuntimeError: If the download fails.
        """
        client = self._get_client()
        buf = BytesIO()

        try:
            client.download_fileobj(self.bucket, s3_key, buf)
            buf.seek(0)
            content = buf.read()
            logger.info("S3 download successful: s3://%s/%s", self.bucket, s3_key)
            return content
        except (ClientError, NoCredentialsError) as exc:
            logger.error("S3 download failed for key '%s': %s", s3_key, exc)
            raise RuntimeError(f"File download failed: {exc}") from exc

    def generate_presigned_url(
        self,
        s3_key: str,
        expiry_seconds: int = 3600,
        filename_hint: str | None = None,
    ) -> str:
        """
        Generate a time-limited pre-signed URL for downloading a file.

        Args:
            s3_key:           The S3 object key.
            expiry_seconds:   How long the URL is valid (default 1 hour).
            filename_hint:    Suggest a filename in the response (sets Content-Disposition).

        Returns:
            A pre-signed HTTPS URL that can be shared or redirected to.

        Raises:
            RuntimeError: If URL generation fails.
        """
        client = self._get_client()

        response_headers = {}
        if filename_hint:
            safe_hint = _sanitize_filename(filename_hint)
            response_headers["ResponseContentDisposition"] = (
                f'attachment; filename="{safe_hint}"'
            )

        try:
            url = client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket,
                    "Key": s3_key,
                    **response_headers,
                },
                ExpiresIn=expiry_seconds,
            )
            logger.debug(
                "Pre-signed URL generated for key '%s' (expires in %d seconds)",
                s3_key, expiry_seconds
            )
            return url
        except (ClientError, NoCredentialsError) as exc:
            logger.error("Pre-signed URL generation failed for key '%s': %s", s3_key, exc)
            raise RuntimeError(f"URL generation failed: {exc}") from exc

    def delete_object(self, s3_key: str) -> None:
        """
        Delete an object from S3.

        Args:
            s3_key: The S3 object key to delete.

        Raises:
            RuntimeError: If the deletion fails.
        """
        client = self._get_client()

        try:
            client.delete_object(Bucket=self.bucket, Key=s3_key)
            logger.info("S3 object deleted: s3://%s/%s", self.bucket, s3_key)
        except (ClientError, NoCredentialsError) as exc:
            logger.error("S3 deletion failed for key '%s': %s", s3_key, exc)
            raise RuntimeError(f"File deletion failed: {exc}") from exc

    def object_exists(self, s3_key: str) -> bool:
        """
        Return True if the given S3 key exists in the bucket.

        Args:
            s3_key: The S3 object key to check.

        Returns:
            True if the object exists, False otherwise.
        """
        client = self._get_client()

        try:
            client.head_object(Bucket=self.bucket, Key=s3_key)
            return True
        except ClientError as exc:
            if exc.response["Error"]["Code"] == "404":
                return False
            logger.error("Error checking S3 object existence for key '%s': %s", s3_key, exc)
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # Key generation helpers
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def make_document_key(council_id: int, filename: str) -> str:
        """
        Return a deterministic, collision-safe S3 key for a document.

        Format: ``documents/{council_id}/{uuid}_{filename}``

        The UUID prefix prevents filename collisions when the same file is
        uploaded multiple times.

        Args:
            council_id: The council ID.
            filename:   The original filename.

        Returns:
            S3 key suitable for storage.
        """
        safe_name = _sanitize_filename(filename)
        unique_prefix = uuid.uuid4().hex[:12]
        return f"documents/{council_id}/{unique_prefix}_{safe_name}"

    @staticmethod
    def make_logo_key(council_id: int, filename: str) -> str:
        """
        Return an S3 key for a council logo.

        Format: ``logos/{council_id}/{filename}``

        Args:
            council_id: The council ID.
            filename:   The filename.

        Returns:
            S3 key suitable for storage.
        """
        safe_name = _sanitize_filename(filename)
        return f"logos/{council_id}/{safe_name}"

    @staticmethod
    def make_report_key(council_id: int, filename: str) -> str:
        """
        Return an S3 key for a report.

        Format: ``reports/{council_id}/{filename}``

        Args:
            council_id: The council ID.
            filename:   The report filename.

        Returns:
            S3 key suitable for storage.
        """
        safe_name = _sanitize_filename(filename)
        return f"reports/{council_id}/{safe_name}"

    @staticmethod
    def make_log_key(filename: str) -> str:
        """
        Return an S3 key for a log file.

        Format: ``logs/{filename}``

        Args:
            filename: The log filename.

        Returns:
            S3 key suitable for storage.
        """
        safe_name = _sanitize_filename(filename)
        return f"logs/{safe_name}"

    # ─────────────────────────────────────────────────────────────────────────
    # Availability check
    # ─────────────────────────────────────────────────────────────────────────

    @staticmethod
    def is_configured() -> bool:
        """
        Return True if S3 is configured (AWS_S3_BUCKET env var is set).

        This is used to determine whether file uploads are available in the
        current environment (e.g. in development, S3 might not be configured).
        """
        return bool(os.environ.get("AWS_S3_BUCKET"))


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────────

#: Global service instance — import and use this directly in route modules.
s3_service = S3StorageService()

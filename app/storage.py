import os
import shutil
from pathlib import Path
from typing import Tuple

# Object storage config (MinIO, or any S3-compatible endpoint).
# Self-hosted MinIO speaks the S3 API, so boto3 works unmodified once
# AWS_ENDPOINT_URL points at your MinIO instance instead of AWS.
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
# For MinIO this is something like "http://minio:9000" (in-compose) or
# "https://minio.yourdomain.com" (behind Nginx). Leave unset for real AWS S3.
AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL")
# MinIO defaults to path-style URLs (http://host:9000/bucket/key) rather than
# virtual-hosted style (http://bucket.host/key).
S3_ADDRESSING_STYLE = os.getenv("S3_ADDRESSING_STYLE", "path" if AWS_ENDPOINT_URL else "auto")

# Local Storage Fallback Directory
LOCAL_UPLOAD_DIR = Path("app/static/uploads")
LOCAL_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def is_object_storage_configured() -> bool:
    """Check if object storage (MinIO/S3) credentials and bucket name are provided."""
    return bool(AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY and S3_BUCKET_NAME)


def _s3_client():
    import boto3
    from botocore.client import Config

    return boto3.client(
        "s3",
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        region_name=AWS_REGION,
        endpoint_url=AWS_ENDPOINT_URL,  # None -> real AWS S3; set -> MinIO/self-hosted
        config=Config(s3={"addressing_style": S3_ADDRESSING_STYLE}),
    )


def _ensure_bucket_exists(client) -> None:
    """MinIO doesn't auto-create buckets; make sure ours exists (idempotent)."""
    try:
        client.head_bucket(Bucket=S3_BUCKET_NAME)
    except Exception:
        client.create_bucket(Bucket=S3_BUCKET_NAME)


def upload_media_asset(file_obj, filename: str) -> Tuple[str, str]:
    """
    Uploads media file object to object storage (MinIO/S3) or Local Storage.
    Returns a tuple of (storage_provider, file_identifier_or_url).
    """
    import uuid
    import os
    _, ext = os.path.splitext(filename)
    if not ext:
        ext = ".mp3"

    safe_basename = "".join(c for c in filename if c.isalnum() or c in (".", "_", "-")).strip()
    safe_filename = f"{uuid.uuid4().hex[:6]}_{safe_basename}"

    if is_object_storage_configured():
        client = _s3_client()
        _ensure_bucket_exists(client)
        s3_key = f"orders/media/{safe_filename}"
        content_type = "video/mp4" if ext.lower() == ".mp4" else "audio/mpeg"
        client.upload_fileobj(
            file_obj,
            S3_BUCKET_NAME,
            s3_key,
            ExtraArgs={"ContentType": content_type}
        )
        return "s3", s3_key
    else:
        # Local Fallback
        dest_path = LOCAL_UPLOAD_DIR / safe_filename
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
        local_url = f"/static/uploads/{safe_filename}"
        return "local", local_url


def get_download_url(storage_provider: str, file_identifier: str, expires_in: int = 3600) -> str:
    """
    Generates a secure download URL.
    - If object storage: Returns a presigned GET URL (works against AWS S3 or MinIO) expiring in `expires_in` seconds.
    - If Local / External URL: Returns the direct URL path.
    """
    if storage_provider == "s3" and is_object_storage_configured():
        client = _s3_client()
        presigned_url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": S3_BUCKET_NAME, "Key": file_identifier},
            ExpiresIn=expires_in
        )
        return presigned_url

    # Return local file URL or external HTTPS link
    return file_identifier

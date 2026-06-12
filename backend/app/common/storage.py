from typing import Optional
from datetime import timedelta
from uuid import uuid4

from minio import Minio

from app.common.config import settings


def _build_client(endpoint: str) -> Minio:
    """Create a MinIO client for the given endpoint."""
    return Minio(
        endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure,
    )


def get_minio() -> Minio:
    """Get the internal MinIO client for server-to-server API operations.

    Uses ``settings.minio_endpoint`` (e.g. ``minio:9000``) which resolves
    inside the Docker network.
    """
    global _minio_client
    if _minio_client is None:
        _minio_client = _build_client(settings.minio_endpoint)
    return _minio_client


def get_public_minio() -> Minio:
    """Get a MinIO client for browser-facing presigned URL generation.

    Uses ``settings.minio_public_url`` (e.g. ``localhost:9000``) so that
    the generated presigned URL's host and SigV4 signature both use the
    browser-reachable hostname.  The ``region`` parameter is hard-coded
    to ``us-east-1`` to avoid an unnecessary HEAD request to the endpoint
    (MinIO SDK's ``_get_region`` would try to connect to ``localhost:9000``
    from inside the container, which is unreachable).

    Falls back to the internal client if ``minio_public_url`` is not set.
    """
    global _minio_public_client
    if _minio_public_client is None:
        endpoint = settings.minio_public_url or settings.minio_endpoint
        _minio_public_client = Minio(
            endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
            region="us-east-1",
        )
    return _minio_public_client


_minio_client: Optional[Minio] = None
_minio_public_client: Optional[Minio] = None


def check_minio_connectivity() -> bool:
    try:
        client = get_minio()
        client.list_buckets()
        return True
    except Exception:
        return False


def check_minio_bucket_exists(bucket_name: str) -> bool:
    try:
        client = get_minio()
        return client.bucket_exists(bucket_name)
    except Exception:
        return False


def build_object_path(prefix: str, filename: str) -> str:
    """Construct a consistent object storage path."""
    prefix = prefix.strip("/")
    return f"{prefix}/{filename}" if prefix else filename


def upload_object(bucket: str, object_path: str, data: bytes, content_type: str = "application/octet-stream") -> None:
    client = get_minio()
    import io
    client.put_object(
        bucket_name=bucket,
        object_name=object_path,
        data=io.BytesIO(data),
        length=len(data),
        content_type=content_type,
    )


def download_object(bucket: str, object_path: str) -> bytes:
    client = get_minio()
    response = client.get_object(bucket_name=bucket, object_name=object_path)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def delete_object(bucket: str, object_path: str) -> None:
    client = get_minio()
    client.remove_object(bucket_name=bucket, object_name=object_path)


def presigned_get_url(bucket: str, object_path: str, expires_seconds: int = 3600) -> str:
    client = get_public_minio()
    return client.presigned_get_object(bucket_name=bucket, object_name=object_path, expires=timedelta(seconds=expires_seconds))


def ensure_bucket_exists(bucket_name: str) -> None:
    client = get_minio()
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)


# Media-specific helpers for listing photos

def generate_original_object_key(tenant_id: str, listing_id: str, filename: str) -> str:
    """Generate object key for original upload: tenant/listing/originals/uuid.ext"""
    import os
    ext = os.path.splitext(filename)[1].lower()
    unique_name = f"{uuid4().hex}{ext}"
    return build_object_path(f"{settings.media_internal_prefix}/{tenant_id}/{listing_id}", unique_name)


def generate_derivative_object_key(tenant_id: str, listing_id: str, photo_id: str, variant: str, format: str = "webp") -> str:
    """Generate object key for derivative: tenant/listing/derivatives/photo_id/variant.webp"""
    return build_object_path(f"{settings.media_derivative_prefix}/{tenant_id}/{listing_id}/{photo_id}", f"{variant}.{format}")


def get_media_bucket() -> str:
    return settings.media_bucket


def get_media_internal_prefix() -> str:
    return settings.media_internal_prefix


def get_media_derivative_prefix() -> str:
    return settings.media_derivative_prefix

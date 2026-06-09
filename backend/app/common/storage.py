from typing import Optional

from minio import Minio

from app.common.config import settings


def get_minio() -> Minio:
    global _minio_client
    if _minio_client is None:
        _minio_client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )
    return _minio_client


_minio_client: Optional[Minio] = None


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
    from datetime import timedelta
    client = get_minio()
    return client.presigned_get_object(bucket_name=bucket, object_name=object_path, expires=timedelta(seconds=expires_seconds))


def ensure_bucket_exists(bucket_name: str) -> None:
    client = get_minio()
    if not client.bucket_exists(bucket_name):
        client.make_bucket(bucket_name)

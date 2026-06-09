from minio import Minio

from app.common.config import settings

minio_client: Minio | None = None


def get_minio() -> Minio:
    global minio_client
    if minio_client is None:
        minio_client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_root_user,
            secret_key=settings.minio_root_password,
            secure=settings.minio_secure,
        )
    return minio_client


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

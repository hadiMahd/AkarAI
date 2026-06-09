from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.common.config import settings
from app.common.database import check_database_connectivity, check_pgvector_enabled
from app.common.minio import check_minio_bucket_exists, check_minio_connectivity
from app.common.redis import check_redis_connectivity

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "backend"}


@router.get("/ready")
async def ready() -> JSONResponse:
    checks = {
        "postgres_via_proxy": {
            "status": "passed" if await check_database_connectivity() else "failed",
            "message": None,
        },
        "pgvector_enabled": {
            "status": "passed" if await check_pgvector_enabled() else "failed",
            "message": None,
        },
        "redis": {
            "status": "passed" if await check_redis_connectivity() else "failed",
            "message": None,
        },
        "object_storage": {"status": "passed", "message": None},
    }

    minio_reachable = check_minio_connectivity()
    if not minio_reachable:
        checks["object_storage"]["status"] = "failed"
        checks["object_storage"]["message"] = "MinIO unreachable"
    elif not check_minio_bucket_exists(settings.minio_bucket_rag):
        checks["object_storage"]["status"] = "failed"
        checks["object_storage"]["message"] = f"Bucket {settings.minio_bucket_rag} not found"
    elif not check_minio_bucket_exists(settings.minio_bucket_media):
        checks["object_storage"]["status"] = "failed"
        checks["object_storage"]["message"] = f"Bucket {settings.minio_bucket_media} not found"

    all_passed = all(c["status"] == "passed" for c in checks.values())
    status_code = 200 if all_passed else 503
    status = "ready" if all_passed else "not_ready"

    return JSONResponse(content={"status": status, "checks": checks}, status_code=status_code)

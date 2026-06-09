import asyncio
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.common.config import check_vault_health, settings
from app.common.database import check_database_connectivity, check_pgvector_enabled
from app.common.request_id import get_request_id
from app.common.redis import check_redis_connectivity
from app.common.storage import check_minio_bucket_exists, check_minio_connectivity

router = APIRouter()


def _timestamp() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


async def _timed_check(name: str, fn) -> dict:
    started = time.monotonic()
    try:
        passed = await fn() if asyncio.iscoroutinefunction(fn) else fn()
        status = "passed" if passed else "failed"
    except Exception:
        status = "failed"
    latency_ms = round((time.monotonic() - started) * 1000, 2)
    return {
        "status": status,
        "message": None if status == "passed" else f"{name} check failed",
        "latency_ms": latency_ms,
        "checked_at": _timestamp(),
    }


@router.get("/health")
async def health(request: Request) -> dict:
    return {
        "status": "ok",
        "service": "backend",
        "request_id": get_request_id(request),
    }


@router.get("/ready")
async def ready(request: Request) -> JSONResponse:
    checks = {
        "vault": await _timed_check("vault", check_vault_health),
        "postgres_via_proxy": await _timed_check("postgres_via_proxy", check_database_connectivity),
        "pgvector_enabled": await _timed_check("pgvector_enabled", check_pgvector_enabled),
        "redis": await _timed_check("redis", check_redis_connectivity),
        "object_storage": await _timed_check(
            "object_storage",
            lambda: (
                check_minio_connectivity()
                and check_minio_bucket_exists(settings.minio_bucket_rag)
                and check_minio_bucket_exists(settings.minio_bucket_media)
            ),
        ),
    }

    all_passed = all(c["status"] == "passed" for c in checks.values())
    status_code = 200 if all_passed else 503
    status = "ready" if all_passed else "not_ready"

    return JSONResponse(
        content={
            "status": status,
            "checks": checks,
            "request_id": get_request_id(request),
        },
        status_code=status_code,
    )


@router.get("/health/dependencies")
async def health_dependencies(request: Request) -> JSONResponse:
    dependencies = {
        "vault": await _timed_check("vault", check_vault_health),
        "postgres": await _timed_check("postgres", check_database_connectivity),
        "pgvector": await _timed_check("pgvector", check_pgvector_enabled),
        "redis": await _timed_check("redis", check_redis_connectivity),
        "minio": await _timed_check("minio", check_minio_connectivity),
    }

    all_passed = all(d["status"] == "passed" for d in dependencies.values())

    return JSONResponse(
        content={
            "status": "ok" if all_passed else "degraded",
            "dependencies": dependencies,
            "request_id": get_request_id(request),
        },
        status_code=200,
    )

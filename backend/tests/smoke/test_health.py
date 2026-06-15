import pytest
from httpx import AsyncClient


@pytest.mark.smoke
@pytest.mark.anyio
async def test_health_endpoint(async_client: AsyncClient):
    response = await async_client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "backend"


@pytest.mark.smoke
@pytest.mark.anyio
async def test_ready_endpoint_structure(async_client: AsyncClient):
    response = await async_client.get("/ready")
    data = response.json()

    assert "status" in data
    assert "checks" in data

    checks = data["checks"]
    required_checks = ["postgres_via_proxy", "pgvector_enabled", "redis", "object_storage"]
    for check_name in required_checks:
        assert check_name in checks, f"Missing check: {check_name}"
        assert "status" in checks[check_name]

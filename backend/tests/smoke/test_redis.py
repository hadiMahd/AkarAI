import pytest
from httpx import AsyncClient


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_redis_check_present(async_client: AsyncClient):
    response = await async_client.get("/ready")
    data = response.json()

    checks = data["checks"]
    assert "redis" in checks
    assert checks["redis"]["status"] in ("passed", "failed"), (
        f"Expected passed/failed, got {checks['redis']['status']}"
    )

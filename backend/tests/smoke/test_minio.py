import pytest
from httpx import AsyncClient


@pytest.mark.smoke
@pytest.mark.anyio
async def test_minio_check_present(async_client: AsyncClient):
    response = await async_client.get("/ready")
    data = response.json()

    checks = data["checks"]
    assert "object_storage" in checks
    assert checks["object_storage"]["status"] in ("passed", "failed"), (
        f"Expected passed/failed, got {checks['object_storage']['status']}"
    )

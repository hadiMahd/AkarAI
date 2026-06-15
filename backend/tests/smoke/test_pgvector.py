import pytest
from httpx import AsyncClient


@pytest.mark.smoke
@pytest.mark.anyio
async def test_pgvector_check_present(async_client: AsyncClient):
    response = await async_client.get("/ready")
    data = response.json()

    checks = data["checks"]
    assert "pgvector_enabled" in checks
    assert checks["pgvector_enabled"]["status"] in ("passed", "failed"), (
        f"Expected passed/failed, got {checks['pgvector_enabled']['status']}"
    )

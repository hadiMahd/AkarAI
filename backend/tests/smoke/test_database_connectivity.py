import pytest
from httpx import AsyncClient

from app.common.database import check_database_connectivity


@pytest.mark.smoke
@pytest.mark.anyio
async def test_database_connectivity_through_pgbouncer(async_client: AsyncClient):
    response = await async_client.get("/ready")
    data = response.json()

    assert "checks" in data
    checks = data["checks"]
    assert "postgres_via_proxy" in checks
    assert checks["postgres_via_proxy"]["status"] in ("passed", "failed"), (
        f"Expected passed/failed, got {checks['postgres_via_proxy']}"
    )

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
class TestReadinessContract:
    async def test_ready_response_shape(self, client: AsyncClient):
        response = await client.get("/ready")
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "request_id" in data

    async def test_ready_checks_have_required_fields(self, client: AsyncClient):
        response = await client.get("/ready")
        data = response.json()
        for check in data["checks"].values():
            assert "status" in check
            assert check["status"] in ("passed", "failed")
            assert "latency_ms" in check
            assert "checked_at" in check

    async def test_ready_status_enum(self, client: AsyncClient):
        response = await client.get("/ready")
        data = response.json()
        assert data["status"] in ("ready", "not_ready")

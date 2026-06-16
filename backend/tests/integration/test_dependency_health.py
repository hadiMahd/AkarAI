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
class TestDependencyHealth:
    async def test_dependency_health_returns_200(self, client: AsyncClient):
        response = await client.get("/health/dependencies")
        assert response.status_code == 200

    async def test_dependency_health_response_shape(self, client: AsyncClient):
        response = await client.get("/health/dependencies")
        data = response.json()
        assert "status" in data
        assert data["status"] in ("ok", "degraded")
        assert "dependencies" in data
        assert "request_id" in data

    async def test_dependency_check_fields(self, client: AsyncClient):
        response = await client.get("/health/dependencies")
        data = response.json()
        for dep in data["dependencies"].values():
            assert "status" in dep
            assert dep["status"] in ("passed", "failed")
            assert "latency_ms" in dep
            assert "checked_at" in dep

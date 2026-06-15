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
class TestHealthContract:
    async def test_health_returns_200(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_health_response_shape(self, client: AsyncClient):
        response = await client.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "backend"
        assert "request_id" in data

    async def test_health_request_id(self, client: AsyncClient):
        response = await client.get("/health")
        data = response.json()
        assert len(data["request_id"]) > 0

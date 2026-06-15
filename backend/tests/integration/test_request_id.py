from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.common.config import settings
from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
class TestRequestID:
    async def test_response_has_request_id_header(self, client: AsyncClient):
        response = await client.get("/health")
        assert settings.request_id_header in response.headers
        request_id = response.headers[settings.request_id_header]
        assert len(request_id) > 0

    async def test_forwarded_request_id(self, client: AsyncClient):
        forwarded_id = "x-fwd-12345"
        response = await client.get(
            "/health",
            headers={settings.request_id_header: forwarded_id},
        )
        assert response.headers[settings.request_id_header] == forwarded_id

    async def test_unique_ids_for_separate_requests(self, client: AsyncClient):
        ids = set()
        for _ in range(5):
            response = await client.get("/health")
            ids.add(response.headers[settings.request_id_header])
        assert len(ids) == 5

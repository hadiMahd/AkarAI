"""Tests for the canonical error envelope emitted by all exception handlers."""

from collections.abc import AsyncGenerator
from io import BytesIO

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.mark.anyio
class TestUnknownRouteEnvelope:
    """Unknown routes go through Starlette's HTTPException → our handler."""

    async def test_unknown_route_returns_envelope_shape(self, client: AsyncClient):
        resp = await client.get("/this-route-does-not-exist")
        assert resp.status_code == 404
        data = resp.json()
        assert data["status"] == "error"
        assert data["error_code"] == "NOT_FOUND"
        assert isinstance(data.get("detail"), str)
        assert data["detail"]

    async def test_unknown_route_has_request_id_header(self, client: AsyncClient):
        resp = await client.get("/this-route-does-not-exist")
        # The middleware always sets the header.
        assert resp.headers.get("X-Request-Id") is not None


@pytest.mark.anyio
class TestRequestValidationEnvelope:
    """Pydantic request-validation failures now use the canonical envelope."""

    async def test_signup_with_invalid_email_returns_validation_envelope(self, client: AsyncClient):
        resp = await client.post(
            "/auth/register",
            json={"email": "not-an-email", "password": "Test1234!", "name": "Test"},
        )
        assert resp.status_code == 422
        body = resp.json()
        assert body["status"] == "error"
        assert body["error_code"] == "VALIDATION_ERROR"
        # detail must be a human-readable summary, not the FastAPI array.
        assert isinstance(body["detail"], str)
        assert body["detail"]
        # The original FastAPI errors array is preserved under "errors" for debugging.
        assert isinstance(body.get("errors"), list)
        assert len(body["errors"]) >= 1

    async def test_search_intent_missing_q_returns_validation_envelope(self, client: AsyncClient):
        resp = await client.post("/search/intent", json={})
        assert resp.status_code == 422
        body = resp.json()
        assert body["status"] == "error"
        assert body["error_code"] == "VALIDATION_ERROR"
        assert isinstance(body["detail"], str)


@pytest.mark.anyio
class TestVoiceSearchErrorEnvelope:
    """The two voice-search failure paths now emit stable error_codes."""

    async def test_voice_search_with_no_file_returns_validation_envelope(self, client: AsyncClient):
        resp = await client.post("/search/voice")
        assert resp.status_code == 422
        body = resp.json()
        assert body["status"] == "error"
        assert body["error_code"] == "VALIDATION_ERROR"

    async def test_voice_search_with_unsupported_format_returns_stable_code(self, client: AsyncClient):
        files = {"audio": ("clip.bin", BytesIO(b"00000"), "audio/x-unsupported")}
        resp = await client.post("/search/voice", files=files)
        assert resp.status_code == 415
        body = resp.json()
        assert body["status"] == "error"
        assert body["error_code"] == "UNSUPPORTED_AUDIO_FORMAT"
        assert "Unsupported audio format" in body["detail"]


@pytest.mark.anyio
class TestAuthEnvelopeContract:
    """Auth flows continue to return stable error codes the frontend can map."""

    async def test_login_with_unknown_user_returns_invalid_credentials_code(self, client: AsyncClient):
        resp = await client.post(
            "/auth/login",
            json={"email": "nobody@nowhere.test", "password": "Test1234!"},
        )
        assert resp.status_code == 401
        body = resp.json()
        assert body["status"] == "error"
        assert body["error_code"] == "INVALID_CREDENTIALS"
        # We must not leak which half of the credentials was wrong.
        assert "password" not in body["detail"].lower()
        assert "email" not in body["detail"].lower()

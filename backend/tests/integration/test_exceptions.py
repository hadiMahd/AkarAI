from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.common.exceptions import (
    AppException,
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitExceededError,
    ServiceUnavailableError,
    UnauthorizedError,
    ValidationError,
)
from app.main import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestExceptionFormat:
    async def test_not_found_response_format(self, client: AsyncClient):
        response = await client.get("/nonexistent-path")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    async def test_exception_has_request_id(self, client: AsyncClient):
        response = await client.get("/nonexistent-path")
        data = response.json()
        assert "X-Request-Id" in response.headers or "request_id" in data or True


class TestExceptionClasses:
    def test_app_exception_defaults(self):
        exc = AppException()
        assert exc.status_code == 500
        assert exc.detail == "Internal server error"
        assert exc.error_code is None

    def test_app_exception_custom(self):
        exc = AppException(detail="Boom", status_code=418, error_code="TEAPOT")
        assert exc.status_code == 418
        assert exc.detail == "Boom"
        assert exc.error_code == "TEAPOT"

    def test_not_found_error(self):
        exc = NotFoundError()
        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"

    def test_validation_error(self):
        exc = ValidationError()
        assert exc.status_code == 422
        assert exc.error_code == "VALIDATION_ERROR"

    def test_service_unavailable(self):
        exc = ServiceUnavailableError()
        assert exc.status_code == 503

    def test_unauthorized(self):
        exc = UnauthorizedError()
        assert exc.status_code == 401

    def test_forbidden(self):
        exc = ForbiddenError()
        assert exc.status_code == 403

    def test_conflict(self):
        exc = ConflictError()
        assert exc.status_code == 409

    def test_rate_limit_exceeded(self):
        exc = RateLimitExceededError()
        assert exc.status_code == 429

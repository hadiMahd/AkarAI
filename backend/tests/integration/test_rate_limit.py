import uuid

import pytest

from app.common.rate_limit import check_rate_limit


class TestRateLimit:
    @pytest.mark.integration
    async def test_first_request_allowed(self):
        result = await check_rate_limit("test", str(uuid.uuid4()), max_requests=5, window_seconds=60)
        assert result is True

    @pytest.mark.integration
    async def test_rate_limit_exceeded(self):
        identifier = f"rate-test-exceeded-{uuid.uuid4()}"
        for _ in range(3):
            await check_rate_limit("test", identifier, max_requests=3, window_seconds=60)
        result = await check_rate_limit("test", identifier, max_requests=3, window_seconds=60)
        assert result is False

    @pytest.mark.integration
    async def test_different_keys_independent(self):
        id1 = f"test-{uuid.uuid4()}"
        id2 = f"test-{uuid.uuid4()}"
        await check_rate_limit("test", id1, max_requests=1, window_seconds=60)
        result = await check_rate_limit("test", id2, max_requests=1, window_seconds=60)
        assert result is True

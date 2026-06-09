import pytest

from app.common.rate_limit import check_rate_limit


class TestRateLimit:
    @pytest.mark.integration
    async def test_first_request_allowed(self):
        result = await check_rate_limit("ip", "192.168.1.1", max_requests=5, window_seconds=60)
        assert result is True

    @pytest.mark.integration
    async def test_rate_limit_exceeded(self):
        identifier = "rate-test-exceeded-user"
        # Exhaust budget
        for _ in range(3):
            await check_rate_limit("user", identifier, max_requests=3, window_seconds=60)
        result = await check_rate_limit("user", identifier, max_requests=3, window_seconds=60)
        assert result is False

    @pytest.mark.integration
    async def test_different_keys_independent(self):
        await check_rate_limit("ip", "10.0.0.1", max_requests=1, window_seconds=60)
        result = await check_rate_limit("ip", "10.0.0.2", max_requests=1, window_seconds=60)
        assert result is True

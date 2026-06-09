import pytest

from app.auth.service import blacklist_token, is_token_blacklisted


class TestTokenInvalidation:
    @pytest.mark.integration
    async def test_blacklist_and_check(self):
        jti = "test-jti-blacklist"
        await blacklist_token(jti, ttl_seconds=60)
        assert await is_token_blacklisted(jti) is True

    @pytest.mark.integration
    async def test_not_blacklisted(self):
        assert await is_token_blacklisted("nonexistent-jti-999") is False

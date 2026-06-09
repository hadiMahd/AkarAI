from datetime import datetime, timezone

from app.common.security import create_access_token, create_refresh_token, decode_access_token, decode_refresh_token


class TestTokenIssuance:
    def test_access_token_contains_required_claims(self):
        token = create_access_token("user-123")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert "jti" in payload
        assert "iat" in payload
        assert "exp" in payload

    def test_refresh_token_contains_required_claims(self):
        token = create_refresh_token("user-123")
        payload = decode_refresh_token(token)
        assert payload["sub"] == "user-123"
        assert payload["type"] == "refresh"
        assert "jti" in payload
        assert "exp" in payload

    def test_access_token_with_extra_claims(self):
        token = create_access_token("user-123", extra_claims={"role": "agency_admin"})
        payload = decode_access_token(token)
        assert payload["role"] == "agency_admin"

    def test_access_token_has_short_ttl(self):
        token = create_access_token("user-123")
        payload = decode_access_token(token)
        ttl = payload["exp"] - payload["iat"]
        assert ttl <= 900  # 15 minutes max

    def test_refresh_token_has_long_ttl(self):
        token = create_refresh_token("user-123")
        payload = decode_refresh_token(token)
        ttl = payload["exp"] - payload["iat"]
        assert ttl >= 86400  # at least 1 day


class TestTokenRotation:
    def test_different_tokens_have_different_jti(self):
        token1 = create_access_token("user-123")
        token2 = create_access_token("user-123")
        payload1 = decode_access_token(token1)
        payload2 = decode_access_token(token2)
        assert payload1["jti"] != payload2["jti"]

    def test_different_subjects_have_different_tokens(self):
        token1 = create_access_token("user-1")
        token2 = create_access_token("user-2")
        payload1 = decode_access_token(token1)
        payload2 = decode_access_token(token2)
        assert payload1["sub"] != payload2["sub"]

from app.common.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)


class TestSecurityTokens:
    def test_create_and_decode_access_token(self):
        token = create_access_token("user-1")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-1"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "jti" in payload

    def test_create_and_decode_refresh_token(self):
        token = create_refresh_token("user-2")
        payload = decode_refresh_token(token)
        assert payload["sub"] == "user-2"
        assert payload["type"] == "refresh"

    def test_token_with_extra_claims(self):
        token = create_access_token("user-3", extra_claims={"role": "admin"})
        payload = decode_access_token(token)
        assert payload["role"] == "admin"

    def test_decode_wrong_token_type_fails(self):
        import pytest
        from jose.exceptions import JWTError
        # Tamper with the token body to make it invalid
        tampered = create_access_token("user-4") + "x"
        with pytest.raises(JWTError):
            decode_access_token(tampered)

    def test_unique_jti_per_token(self):
        t1 = create_access_token("u1")
        t2 = create_access_token("u1")
        jti1 = decode_access_token(t1)["jti"]
        jti2 = decode_access_token(t2)["jti"]
        assert jti1 != jti2

from app.common.rate_limit import AUTH_RATE_LIMITS, check_auth_rate_limit


class TestAuthRateLimitKeys:
    def test_login_has_rate_limit_config(self):
        limits = AUTH_RATE_LIMITS["login"]
        assert "max_requests" in limits
        assert "window_seconds" in limits

    def test_password_reset_has_stricter_limit(self):
        login_limit = AUTH_RATE_LIMITS["login"]["max_requests"]
        reset_limit = AUTH_RATE_LIMITS["password_reset"]["max_requests"]
        assert reset_limit < login_limit

    def test_refresh_has_higher_limit(self):
        refresh_limit = AUTH_RATE_LIMITS["refresh"]["max_requests"]
        assert refresh_limit > 0

    def test_all_auth_actions_defined(self):
        for action in ("login", "refresh", "logout", "password_reset", "session_revoke", "employee_deactivate"):
            assert action in AUTH_RATE_LIMITS
            assert AUTH_RATE_LIMITS[action]["max_requests"] > 0
            assert AUTH_RATE_LIMITS[action]["window_seconds"] > 0

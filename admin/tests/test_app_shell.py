from __future__ import annotations

from unittest.mock import MagicMock

from streamlit.errors import StreamlitSecretNotFoundError

from admin.auth import AuthState


class _FakeTab:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def _auth() -> AuthState:
    return AuthState(
        token="token",
        actor={
            "email": "platform.admin@akarai.test",
            "name": "Platform Admin",
            "role": "platform_admin",
            "permissions": ["platform:dashboard_read"],
        },
    )


def test_main_unauthenticated_shows_single_login(monkeypatch):
    import admin.app as app

    login_form = MagicMock()
    tabs = MagicMock()

    monkeypatch.setattr(app, "get_auth_state", lambda: None)
    monkeypatch.setattr(app, "render_login_form", login_form)
    monkeypatch.setattr(app.st, "title", MagicMock())
    monkeypatch.setattr(app.st, "caption", MagicMock())
    monkeypatch.setattr(app.st, "tabs", tabs)

    app.main()

    login_form.assert_called_once()
    tabs.assert_not_called()


def test_main_authenticated_renders_four_tabs(monkeypatch):
    import admin.app as app

    auth = _auth()
    home = MagicMock()
    insights = MagicMock()
    audit = MagicMock()
    roles = MagicMock()
    rag_evals = MagicMock()
    tabs_called = {}

    monkeypatch.setattr(app, "get_auth_state", lambda: auth)
    monkeypatch.setattr(app, "require_dashboard_access", lambda client_factory: auth)
    monkeypatch.setattr(app, "_render_home", home)
    monkeypatch.setattr(app, "render_marketplace_insights", insights)
    monkeypatch.setattr(app, "render_ai_audit_logs", audit)
    monkeypatch.setattr(app, "render_role_access_overview", roles)
    monkeypatch.setattr(app, "render_rag_evals", rag_evals)
    monkeypatch.setattr(app, "render_sign_out_button", MagicMock())
    monkeypatch.setattr(app.st, "title", MagicMock())
    monkeypatch.setattr(app.st, "caption", MagicMock())
    monkeypatch.setattr(app.st, "markdown", MagicMock())
    monkeypatch.setattr(app.st, "write", MagicMock())
    monkeypatch.setattr(app.st, "code", MagicMock())
    monkeypatch.setattr(app.st, "expander", lambda *args, **kwargs: _FakeTab())
    monkeypatch.setattr(app.st, "sidebar", _FakeTab())

    def fake_tabs(labels):
        tabs_called["labels"] = labels
        return [_FakeTab(), _FakeTab(), _FakeTab(), _FakeTab(), _FakeTab()]

    monkeypatch.setattr(app.st, "tabs", fake_tabs)

    app.main()

    assert tabs_called["labels"] == [
        "Home",
        "Marketplace Insights",
        "AI Audit Logs",
        "Role & Access Overview",
        "RAG Evals",
    ]
    home.assert_called_once_with(auth)
    insights.assert_called_once_with(auth)
    audit.assert_called_once_with(auth)
    roles.assert_called_once_with(auth)
    rag_evals.assert_called_once_with(auth)


def test_get_auth_state_rehydrates_from_cookies(monkeypatch):
    import admin.auth as auth

    class FakeCookies(dict):
        def ready(self):
            return True

        def save(self):
            return None

    cookies = FakeCookies(
        {
            auth.TOKEN_COOKIE_KEY: "token-1",
            auth.ACTOR_COOKIE_KEY: '{"email":"platform.admin@akarai.test","name":"Platform Admin","role":"platform_admin","permissions":["platform:dashboard_read"]}',
        }
    )

    monkeypatch.setattr(auth, "_get_cookie_store", lambda: cookies)
    monkeypatch.setattr(auth.st, "session_state", {})

    state = auth.get_auth_state()

    assert state is not None
    assert state.token == "token-1"
    assert state.email == "platform.admin@akarai.test"


def test_sign_out_clears_cookie_auth(monkeypatch):
    import admin.auth as auth

    class FakeCookies(dict):
        def ready(self):
            return True

        def save(self):
            self["_saved"] = True

    cookies = FakeCookies(
        {
            auth.TOKEN_COOKIE_KEY: "token-1",
            auth.ACTOR_COOKIE_KEY: '{"email":"platform.admin@akarai.test"}',
        }
    )
    session_state = {
        "platform_admin_token": "token-1",
        "platform_admin_actor": {"email": "platform.admin@akarai.test"},
    }

    monkeypatch.setattr(auth, "_get_cookie_store", lambda: cookies)
    monkeypatch.setattr(auth.st, "session_state", session_state)

    auth.sign_out()

    assert "platform_admin_token" not in session_state
    assert "platform_admin_actor" not in session_state
    assert auth.TOKEN_COOKIE_KEY not in cookies
    assert auth.ACTOR_COOKIE_KEY not in cookies


def test_cookie_password_falls_back_without_streamlit_secrets(monkeypatch):
    import admin.auth as auth

    class MissingSecrets:
        def __contains__(self, key):
            raise StreamlitSecretNotFoundError("missing")

    monkeypatch.delenv("ADMIN_COOKIE_PASSWORD", raising=False)
    monkeypatch.setattr(auth.st, "secrets", MissingSecrets())

    assert auth._cookie_password() == auth.COOKIE_PASSWORD

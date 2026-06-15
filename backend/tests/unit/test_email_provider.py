import pytest

from app.notifications.email_provider import EmailProvider, PlaceholderEmailProvider


pytestmark = pytest.mark.anyio


class TestEmailProvider:
    async def test_placeholder_returns_not_sent(self):
        provider = PlaceholderEmailProvider()
        result = await provider.send_email(
            to_email="test@example.com",
            subject="Hello",
            body_html="<p>Hi</p>",
        )
        assert result["status"] == "not_sent"
        assert "TBD_ASK_USER" in result["reason"]
        assert result["to"] == "test@example.com"

    def test_placeholder_is_email_provider(self):
        provider = PlaceholderEmailProvider()
        assert isinstance(provider, EmailProvider)

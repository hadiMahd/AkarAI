from typing import Protocol, runtime_checkable


@runtime_checkable
class EmailProvider(Protocol):
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
        **kwargs,
    ) -> dict: ...


class PlaceholderEmailProvider:
    """Placeholder email provider. Concrete provider is TBD_ASK_USER."""

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str | None = None,
        **kwargs,
    ) -> dict:
        return {
            "status": "not_sent",
            "reason": "Email provider not configured (TBD_ASK_USER)",
            "to": to_email,
            "subject": subject,
        }

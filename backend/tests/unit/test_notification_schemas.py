from app.notifications.schemas import EmailEventPayload, NotificationPayload


class TestNotificationSchemas:
    def test_notification_payload_defaults(self):
        p = NotificationPayload(template_key="welcome")
        assert p.channel == "email"
        assert p.template_data == {}
        assert p.recipient_email is None

    def test_email_event_payload(self):
        p = EmailEventPayload(
            to_email="user@example.com",
            subject="Test",
            body_html="<h1>Test</h1>",
        )
        assert p.event_name == "email.notification_requested"
        assert p.to_email == "user@example.com"

    def test_notification_payload_full(self):
        p = NotificationPayload(
            recipient_email="a@b.com",
            template_key="lead_alert",
            template_data={"name": "Ali"},
            channel="email",
        )
        assert p.recipient_email == "a@b.com"
        assert p.template_data["name"] == "Ali"

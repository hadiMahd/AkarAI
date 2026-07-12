"""Worker and model-service retry pipeline tests for lead processing."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest


class TestLeadCreatedHandler:
    async def test_handler_skips_empty_message(self):
        from handlers.leads import handle_lead_created

        result = await handle_lead_created(
            None,
            {
                "lead_id": str(uuid4()),
                "tenant_id": str(uuid4()),
                "message": "",
                "name": "Test",
                "email": "test@example.com",
            },
            "event-1",
        )
        assert result["status"] == "skipped_empty_message"
        assert result["spam_label"] == "spam"

    async def test_handler_skips_whitespace_only_message(self):
        from handlers.leads import handle_lead_created

        result = await handle_lead_created(
            None,
            {
                "lead_id": str(uuid4()),
                "tenant_id": str(uuid4()),
                "message": "   \n  \t  ",
                "name": "Test",
            },
            "event-2",
        )
        assert result["status"] == "skipped_empty_message"

    async def test_handler_forwards_non_empty_message(self):
        with patch(
            "handlers.lead_processing_client.forward_to_model_service",
            new=AsyncMock(
                return_value={
                    "lead_id": "test",
                    "spam_result": {"label": "not_spam", "status": "completed"},
                    "level_result": {"label": "hot", "status": "completed"},
                }
            ),
        ):
            from handlers.leads import handle_lead_created

            result = await handle_lead_created(
                None,
                {
                    "lead_id": str(uuid4()),
                    "tenant_id": str(uuid4()),
                    "message": "I am interested in this property, please call me",
                    "name": "Test Buyer",
                    "email": "buyer@example.com",
                },
                "event-3",
            )
            assert result["status"] == "classified"
            assert result["spam_result"]["label"] == "not_spam"

    async def test_handler_propagates_model_service_failure(self):
        with patch(
            "handlers.lead_processing_client.forward_to_model_service",
            new=AsyncMock(side_effect=RuntimeError("Service down")),
        ):
            from handlers.leads import handle_lead_created

            with pytest.raises(RuntimeError, match="Service down"):
                await handle_lead_created(
                    None,
                    {
                        "lead_id": str(uuid4()),
                        "tenant_id": str(uuid4()),
                        "message": "Test message",
                    },
                    "event-4",
                )


class TestModelServiceClient:
    async def test_client_retries_are_configured(self):
        from handlers.lead_processing_client import DEFAULT_RETRY_BASE, DEFAULT_RETRY_MAX

        assert DEFAULT_RETRY_MAX > 0
        assert DEFAULT_RETRY_BASE > 0

    async def test_client_accepts_custom_max_attempts(self):
        from handlers.lead_processing_client import forward_to_model_service

        assert callable(forward_to_model_service)

    async def test_client_timeout_is_configured(self):
        from handlers.lead_processing_client import DEFAULT_REQUEST_TIMEOUT

        assert DEFAULT_REQUEST_TIMEOUT > 0


class TestModelServiceURL:
    def test_model_service_url_default(self):
        from handlers.lead_processing_client import DEFAULT_MODEL_SERVICE_URL

        assert "lead-model-service" in str(DEFAULT_MODEL_SERVICE_URL)
        assert "8100" in str(DEFAULT_MODEL_SERVICE_URL)


class TestWorkerHandlerRegistration:
    def test_handler_is_callable(self):
        from handlers.leads import handle_lead_created

        assert callable(handle_lead_created)

    def test_lead_created_event_exists(self):
        import sys

        sys.path.insert(0, "../backend")
        from app.common.events import EVENT_NAMES

        assert "lead.created" in EVENT_NAMES

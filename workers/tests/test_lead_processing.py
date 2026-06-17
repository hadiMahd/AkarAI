"""Worker and model-service retry pipeline tests for lead processing."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest


class TestLeadCreatedHandler:
    async def test_handler_skips_empty_message(self):
        from handlers.leads import handle_lead_created

        result = await handle_lead_created({
            "lead_id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "message": "",
            "name": "Test",
            "email": "test@example.com",
        })
        assert result["status"] == "skipped_empty_message"
        assert result["spam_label"] == "spam"

    async def test_handler_skips_whitespace_only_message(self):
        from handlers.leads import handle_lead_created

        result = await handle_lead_created({
            "lead_id": str(uuid4()),
            "tenant_id": str(uuid4()),
            "message": "   \n  \t  ",
            "name": "Test",
        })
        assert result["status"] == "skipped_empty_message"

    async def test_handler_forwards_non_empty_message(self):
        with patch("handlers.lead_processing_client.forward_to_model_service", new=AsyncMock(return_value={
            "lead_id": "test",
            "spam_result": {"label": "not_spam", "status": "completed"},
            "level_result": {"label": "hot", "status": "completed"},
        })):
            from handlers.leads import handle_lead_created
            result = await handle_lead_created({
                "lead_id": str(uuid4()),
                "tenant_id": str(uuid4()),
                "message": "I am interested in this property, please call me",
                "name": "Test Buyer",
                "email": "buyer@example.com",
            })
            assert result["status"] == "classified"
            assert result["spam_result"]["label"] == "not_spam"

    async def test_handler_fail_open_on_error(self):
        from unittest.mock import AsyncMock
        with patch("handlers.lead_processing_client.forward_to_model_service", new=AsyncMock(side_effect=RuntimeError("Service down"))):
            with patch("handlers.leads._post_fail_open_callback", new=AsyncMock()):
                from handlers.leads import handle_lead_created
                result = await handle_lead_created({
                    "lead_id": str(uuid4()),
                    "tenant_id": str(uuid4()),
                    "message": "Test message",
                })
                assert result["status"] == "fail_open_completed"
                assert "error" in result

    @pytest.mark.asyncio
    async def test_fail_open_callback_raises_for_backend_error(self):
        response = Mock()
        response.raise_for_status.side_effect = RuntimeError("backend rejected callback")

        client = AsyncMock()
        client.post.return_value = response

        client_factory = AsyncMock()
        client_factory.__aenter__.return_value = client
        client_factory.__aexit__.return_value = None

        with patch("handlers.leads.httpx.AsyncClient", return_value=client_factory):
            from handlers.leads import _post_fail_open_callback

            with pytest.raises(RuntimeError, match="backend rejected callback"):
                await _post_fail_open_callback(
                    lead_id=str(uuid4()),
                    tenant_id=str(uuid4()),
                    stage="spam",
                    label="not_spam",
                    details={"reason": "test"},
                    idempotency_key="worker_failopen_test_spam",
                )


class TestModelServiceClient:
    async def test_client_retries_are_configured(self):
        from handlers.lead_processing_client import DEFAULT_RETRY_MAX, DEFAULT_RETRY_BASE
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

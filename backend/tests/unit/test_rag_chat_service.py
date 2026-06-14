from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.common.tenant import TenantContext
from app.rag.models import RagChatMessage, RagChatThread
from app.rag.schemas import RagChatMessageCreateRequest
from app.rag.service import RagChatService


@pytest.fixture
def tenant_context():
    return TenantContext(
        actor_id=uuid4(),
        role="agency_admin",
        tenant_id=uuid4(),
    )


@pytest.fixture
def service(tenant_context):
    mock_session = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.flush = AsyncMock()
    mock_session.rollback = AsyncMock()
    svc = RagChatService(mock_session, tenant_context)
    svc._repo = MagicMock()
    return svc


class TestRagChatService:
    async def test_create_thread_defaults_title(self, service, tenant_context):
        now = datetime.now(timezone.utc)
        thread = RagChatThread(
            id=uuid4(),
            tenant_id=tenant_context.tenant_id,
            owner_user_id=tenant_context.actor_id,
            title="New conversation",
            created_at=now,
            updated_at=now,
            last_message_at=now,
        )
        service._repo.create_chat_thread = AsyncMock(return_value=thread)

        result = await service.create_thread()

        assert result.title == "New conversation"
        assert result.message_count == 0

    async def test_get_thread_prefers_cached_payload(self, service, tenant_context):
        thread_id = uuid4()
        payload = {
            "thread": {
                "id": str(thread_id),
                "tenant_id": str(tenant_context.tenant_id),
                "owner_user_id": str(tenant_context.actor_id),
                "title": "Cached thread",
                "message_count": 1,
                "created_at": "2026-06-14T00:00:00Z",
                "updated_at": "2026-06-14T00:00:00Z",
                "last_message_at": "2026-06-14T00:00:00Z",
            },
            "messages": [],
        }
        with patch("app.rag.service.redis_get", new=AsyncMock(return_value=__import__("json").dumps(payload))):
            result = await service.get_thread(thread_id)

        assert result.thread.title == "Cached thread"

    async def test_send_message_uses_only_last_4_turns(self, service, tenant_context):
        thread_id = uuid4()
        now = datetime.now(timezone.utc)
        thread = RagChatThread(
            id=thread_id,
            tenant_id=tenant_context.tenant_id,
            owner_user_id=tenant_context.actor_id,
            title="New conversation",
            created_at=now,
            updated_at=now,
            last_message_at=now,
        )
        existing_messages = []
        for index in range(10):
            role = "user" if index % 2 == 0 else "assistant"
            existing_messages.append(
                RagChatMessage(
                    id=uuid4(),
                    thread_id=thread_id,
                    tenant_id=tenant_context.tenant_id,
                    owner_user_id=tenant_context.actor_id,
                    role=role,
                    content=f"{role}-{index}",
                    sequence_number=index + 1,
                    created_at=now,
                )
            )

        service._repo.get_chat_thread = AsyncMock(return_value=thread)
        service._repo.list_chat_messages = AsyncMock(return_value=existing_messages)
        service._repo.get_next_chat_sequence_number = AsyncMock(side_effect=[11, 12])
        async def _persist_message(message):
            if message.id is None:
                message.id = uuid4()
            return message

        service._repo.create_chat_message = AsyncMock(side_effect=_persist_message)
        service._repo.update_chat_thread = AsyncMock(side_effect=lambda current: current)

        with patch("app.rag.service.RagRetrievalService.answer_policy_query", new=AsyncMock()) as mock_answer:
            mock_answer.return_value = MagicMock(
                answer="Grounded answer",
                debug=MagicMock(retrieval_log_id=uuid4()),
                model_dump=MagicMock(
                    return_value={
                        "status": "answered",
                        "answer": "Grounded answer",
                        "citations": [],
                        "evidence": [],
                        "debug": {"retrieval_log_id": str(uuid4()), "confidence_status": "sufficient", "reranker_used": False},
                    }
                ),
            )
            await service.send_message(
                thread_id,
                RagChatMessageCreateRequest(content="latest question"),
            )

        conversation = mock_answer.call_args.args[0].conversation_messages
        assert len(conversation) == 8

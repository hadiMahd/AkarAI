from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.common.tenant import TenantContext
from app.rag.models import RagChatMessage, RagChatThread
from app.rag.schemas import RagChatMessageCreateRequest
from app.rag.service import RagChatService


pytestmark = pytest.mark.anyio


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
            with patch("app.rag.service.redis_set", new=AsyncMock()):
                await service.send_message(
                    thread_id,
                    RagChatMessageCreateRequest(content="latest question"),
                )

        conversation = mock_answer.call_args.args[0].conversation_messages
        assert len(conversation) == 8


class TestChatServiceSanitization:
    """Verify chat persistence and Redis cache payloads are sanitized before storage (T043)."""

    async def test_send_message_sanitizes_answer_payload_before_db_storage(
        self, service, tenant_context
    ):
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
        service._repo.get_chat_thread = AsyncMock(return_value=thread)
        service._repo.list_chat_messages = AsyncMock(return_value=[])
        service._repo.get_next_chat_sequence_number = AsyncMock(side_effect=[1, 2])

        async def _persist_message(message):
            if message.id is None:
                message.id = uuid4()
            return message

        service._repo.create_chat_message = AsyncMock(side_effect=_persist_message)
        service._repo.update_chat_thread = AsyncMock(side_effect=lambda t: t)

        secret_answer = "The api_key=supersecretkeyvalue123456 is embedded here."
        with patch("app.rag.service.RagRetrievalService.answer_policy_query", new=AsyncMock()) as mock_answer:
            mock_answer.return_value = MagicMock(
                answer=secret_answer,
                debug=MagicMock(retrieval_log_id=uuid4()),
                model_dump=MagicMock(
                    return_value={
                        "status": "answered",
                        "answer": secret_answer,
                        "citations": [],
                        "evidence": [],
                        "debug": {"retrieval_log_id": str(uuid4()), "confidence_status": "sufficient", "reranker_used": False, "guardrail_blocked_reason": None},
                    }
                ),
            )
            with patch("app.rag.service.redis_set", new=AsyncMock()):
                await service.send_message(
                    thread_id,
                    RagChatMessageCreateRequest(content="What is the key?"),
                )

        create_calls = service._repo.create_chat_message.call_args_list
        assistant_call = create_calls[-1][0][0]
        assert assistant_call.answer_payload is not None
        assert "supersecretkeyvalue123456" not in str(assistant_call.answer_payload)
        # The stored content column must also be redacted.
        assert "supersecretkeyvalue123456" not in assistant_call.content

    async def test_send_message_sanitizes_redis_cache_payload(self, service, tenant_context):
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
        service._repo.get_chat_thread = AsyncMock(return_value=thread)
        service._repo.list_chat_messages = AsyncMock(return_value=[])
        service._repo.get_next_chat_sequence_number = AsyncMock(side_effect=[1, 2])

        async def _persist_message(message):
            if message.id is None:
                message.id = uuid4()
            return message

        service._repo.create_chat_message = AsyncMock(side_effect=_persist_message)
        service._repo.update_chat_thread = AsyncMock(side_effect=lambda t: t)

        secret_answer = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMSJ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        redis_received: list[str] = []

        async def capture_redis(key, value, ttl=None):
            redis_received.append(value)

        with patch("app.rag.service.RagRetrievalService.answer_policy_query", new=AsyncMock()) as mock_answer:
            mock_answer.return_value = MagicMock(
                answer=secret_answer,
                debug=MagicMock(retrieval_log_id=uuid4()),
                model_dump=MagicMock(
                    return_value={
                        "status": "answered",
                        "answer": secret_answer,
                        "citations": [],
                        "evidence": [],
                        "debug": None,
                    }
                ),
            )
            with patch("app.rag.service.redis_set", new=AsyncMock(side_effect=capture_redis)):
                await service.send_message(
                    thread_id,
                    RagChatMessageCreateRequest(content="Give me the token."),
                )

        assert len(redis_received) == 1
        assert "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMSJ9" not in redis_received[0]
        assert "[REDACTED" in redis_received[0]

    async def test_get_thread_sanitizes_db_payload_before_redis_write(
        self, service, tenant_context
    ):
        """get_thread() must not push unsanitized DB rows into the Redis cache."""
        thread_id = uuid4()
        now = datetime.now(timezone.utc)
        thread = RagChatThread(
            id=thread_id,
            tenant_id=tenant_context.tenant_id,
            owner_user_id=tenant_context.actor_id,
            title="Old thread",
            created_at=now,
            updated_at=now,
            last_message_at=now,
        )
        raw_secret = "sk-abcdefghijklmnopqrstuvwxyz12345"
        old_assistant_msg = RagChatMessage(
            id=uuid4(),
            thread_id=thread_id,
            tenant_id=tenant_context.tenant_id,
            owner_user_id=tenant_context.actor_id,
            role="assistant",
            content=raw_secret,
            sequence_number=1,
            answer_payload={"status": "answered", "answer": raw_secret, "citations": [], "evidence": [], "debug": None},
            created_at=now,
        )

        service._repo.get_chat_thread = AsyncMock(return_value=thread)
        service._repo.list_chat_messages = AsyncMock(return_value=[old_assistant_msg])

        redis_written: list[str] = []

        async def capture_redis(key, value, ttl=None):
            redis_written.append(value)

        with patch("app.rag.service.redis_get", new=AsyncMock(return_value=None)):
            with patch("app.rag.service.redis_set", new=AsyncMock(side_effect=capture_redis)):
                result = await service.get_thread(thread_id)

        assert len(redis_written) == 1
        assert raw_secret not in redis_written[0]
        assert "[REDACTED" in redis_written[0]
        # The returned object is now also sanitized — historical rows no longer leak PII to callers.
        assert result.thread.id == thread_id
        assert raw_secret not in result.messages[0].content


class TestChatServicePiiSanitization:
    """Verify PII is stripped from chat persistence and cache paths (T043 PII extension)."""

    async def test_send_message_redacts_email_in_answer_payload(
        self, service, tenant_context
    ):
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
        service._repo.get_chat_thread = AsyncMock(return_value=thread)
        service._repo.list_chat_messages = AsyncMock(return_value=[])
        service._repo.get_next_chat_sequence_number = AsyncMock(side_effect=[1, 2])

        async def _persist(message):
            if message.id is None:
                message.id = uuid4()
            return message

        service._repo.create_chat_message = AsyncMock(side_effect=_persist)
        service._repo.update_chat_thread = AsyncMock(side_effect=lambda t: t)

        pii_answer = "Please contact owner@property.com or call 800-555-4321 for details."
        with patch("app.rag.service.RagRetrievalService.answer_policy_query", new=AsyncMock()) as mock_answer:
            mock_answer.return_value = MagicMock(
                answer=pii_answer,
                debug=MagicMock(retrieval_log_id=uuid4()),
                model_dump=MagicMock(
                    return_value={
                        "status": "answered",
                        "answer": pii_answer,
                        "citations": [],
                        "evidence": [],
                        "debug": {"retrieval_log_id": str(uuid4()), "confidence_status": "sufficient", "reranker_used": False, "guardrail_blocked_reason": None},
                    }
                ),
            )
            with patch("app.rag.service.redis_set", new=AsyncMock()):
                await service.send_message(
                    thread_id,
                    RagChatMessageCreateRequest(content="How do I contact the owner?"),
                )

        create_calls = service._repo.create_chat_message.call_args_list
        assistant_call = create_calls[-1][0][0]
        payload_str = str(assistant_call.answer_payload)
        assert "owner@property.com" not in payload_str
        assert "800-555-4321" not in payload_str
        assert "owner@property.com" not in assistant_call.content
        assert "800-555-4321" not in assistant_call.content

    async def test_send_message_redacts_pii_in_redis_cache(
        self, service, tenant_context
    ):
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
        service._repo.get_chat_thread = AsyncMock(return_value=thread)
        service._repo.list_chat_messages = AsyncMock(return_value=[])
        service._repo.get_next_chat_sequence_number = AsyncMock(side_effect=[1, 2])

        async def _persist(message):
            if message.id is None:
                message.id = uuid4()
            return message

        service._repo.create_chat_message = AsyncMock(side_effect=_persist)
        service._repo.update_chat_thread = AsyncMock(side_effect=lambda t: t)

        pii_answer = "Agent Jane Doe can be reached at agent@firm.com."
        redis_received: list[str] = []

        async def capture_redis(key, value, ttl=None):
            redis_received.append(value)

        with patch("app.rag.service.RagRetrievalService.answer_policy_query", new=AsyncMock()) as mock_answer:
            mock_answer.return_value = MagicMock(
                answer=pii_answer,
                debug=MagicMock(retrieval_log_id=uuid4()),
                model_dump=MagicMock(
                    return_value={
                        "status": "answered",
                        "answer": pii_answer,
                        "citations": [],
                        "evidence": [],
                        "debug": None,
                    }
                ),
            )
            with patch("app.rag.service.redis_set", new=AsyncMock(side_effect=capture_redis)):
                await service.send_message(
                    thread_id,
                    RagChatMessageCreateRequest(content="Who is the agent?"),
                )

        assert len(redis_received) == 1
        assert "agent@firm.com" not in redis_received[0]
        assert "[REDACTED_EMAIL]" in redis_received[0]

    async def test_existing_secret_redaction_not_regressed(
        self, service, tenant_context
    ):
        """Confirm Bearer token redaction from T043 still works alongside PII layer."""
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
        service._repo.get_chat_thread = AsyncMock(return_value=thread)
        service._repo.list_chat_messages = AsyncMock(return_value=[])
        service._repo.get_next_chat_sequence_number = AsyncMock(side_effect=[1, 2])

        async def _persist(message):
            if message.id is None:
                message.id = uuid4()
            return message

        service._repo.create_chat_message = AsyncMock(side_effect=_persist)
        service._repo.update_chat_thread = AsyncMock(side_effect=lambda t: t)

        secret_answer = "Use Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyMSJ9.SflKxwRJSMeKKF2QT4fw to authenticate."
        with patch("app.rag.service.RagRetrievalService.answer_policy_query", new=AsyncMock()) as mock_answer:
            mock_answer.return_value = MagicMock(
                answer=secret_answer,
                debug=MagicMock(retrieval_log_id=uuid4()),
                model_dump=MagicMock(
                    return_value={
                        "status": "answered",
                        "answer": secret_answer,
                        "citations": [],
                        "evidence": [],
                        "debug": None,
                    }
                ),
            )
            with patch("app.rag.service.redis_set", new=AsyncMock()):
                await service.send_message(
                    thread_id,
                    RagChatMessageCreateRequest(content="How do I auth?"),
                )

        create_calls = service._repo.create_chat_message.call_args_list
        assistant_call = create_calls[-1][0][0]
        assert "eyJhbGciOiJIUzI1NiJ9" not in assistant_call.content
        assert "[REDACTED" in assistant_call.content

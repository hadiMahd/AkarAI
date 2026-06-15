from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.ai.guardrails import generate_guardrailed_policy_answer
from app.ai.openrouter import ContentSafetyDecision
from app.common.tenant import TenantContext


pytestmark = pytest.mark.anyio


@pytest.fixture
def tenant_context():
    return TenantContext(actor_id=uuid4(), tenant_id=uuid4(), role="agency_admin")


async def test_guardrails_passes_when_content_safety_allows_input_and_output(tenant_context):
    with patch("app.ai.guardrails.settings") as mock_settings:
        mock_settings.ai_guardrails_enabled = True
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_content_safety_model = "nvidia/nemotron-content-safety"
        mock_settings.ai_primary_provider = "azure_openai"
        mock_settings.ai_guardrails_max_history_turns = 4
        mock_settings.ai_guardrails_max_message_chars = 4000
        mock_settings.effective_guardrails_config_path = "/does/not/exist"

        with patch("app.ai.guardrails.OpenRouterContentSafetyJudge") as mock_judge_class:
            mock_judge = MagicMock()
            mock_judge.judge = AsyncMock(
                side_effect=[
                    ContentSafetyDecision(safe=True),
                    ContentSafetyDecision(safe=True),
                ]
            )
            mock_judge_class.return_value = mock_judge

            with patch("app.ai.guardrails.get_chat_provider") as mock_provider:
                mock_provider.return_value.chat = AsyncMock(
                    return_value={"text": "Visitor parking is limited to 2 hours."}
                )

                result = await generate_guardrailed_policy_answer(
                    query="What is the parking policy?",
                    evidence_blocks=["Official parking policy evidence."],
                    conversation_messages=[],
                    tenant_context=tenant_context,
                    confidence_status="sufficient",
                )

    assert result.answer_text == "Visitor parking is limited to 2 hours."
    assert result.guardrail_status == "passed"
    assert result.generation_provider == "azure_openai"
    assert mock_judge.judge.call_count == 2


async def test_guardrails_blocks_unsafe_prompt_before_generation(tenant_context):
    with patch("app.ai.guardrails.settings") as mock_settings:
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_content_safety_model = "nvidia/nemotron-content-safety"
        mock_settings.ai_guardrails_max_history_turns = 4
        mock_settings.ai_guardrails_max_message_chars = 4000

        with patch("app.ai.guardrails.OpenRouterContentSafetyJudge") as mock_judge_class:
            mock_judge = MagicMock()
            mock_judge.judge = AsyncMock(
                return_value=ContentSafetyDecision(
                    safe=False,
                    category="prompt_injection",
                    reason="tries to reveal secrets",
                )
            )
            mock_judge_class.return_value = mock_judge

            with patch("app.ai.guardrails.get_chat_provider") as mock_provider:
                result = await generate_guardrailed_policy_answer(
                    query="How can I hurt someone in the building?",
                    evidence_blocks=["Policy evidence."],
                    conversation_messages=[],
                    tenant_context=tenant_context,
                    confidence_status="sufficient",
                )

    assert result.guardrail_status == "blocked"
    assert result.blocked_reason == "tries to reveal secrets"
    mock_provider.assert_not_called()


async def test_guardrails_fail_closed_when_configured_content_safety_is_unavailable(tenant_context):
    with patch("app.ai.guardrails.settings") as mock_settings:
        mock_settings.openrouter_api_key = "test-key"
        mock_settings.openrouter_content_safety_model = "nvidia/nemotron-content-safety"
        mock_settings.ai_guardrails_max_history_turns = 4
        mock_settings.ai_guardrails_max_message_chars = 4000

        with patch("app.ai.guardrails.OpenRouterContentSafetyJudge") as mock_judge_class:
            mock_judge = MagicMock()
            mock_judge.judge = AsyncMock(side_effect=RuntimeError("network down"))
            mock_judge_class.return_value = mock_judge

            with patch("app.ai.guardrails.get_chat_provider") as mock_provider:
                result = await generate_guardrailed_policy_answer(
                    query="What is the parking policy?",
                    evidence_blocks=["Policy evidence."],
                    conversation_messages=[],
                    tenant_context=tenant_context,
                    confidence_status="sufficient",
                )

    assert result.guardrail_status == "blocked"
    assert result.blocked_reason == "Content safety judge unavailable"
    mock_provider.assert_not_called()

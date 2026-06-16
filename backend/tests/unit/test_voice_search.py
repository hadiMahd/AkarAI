import pytest
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.anyio
class TestVoiceSearchProvider:
    async def test_azure_whisper_transcribes_audio(self):
        from app.ai.azure_openai import AzureSTTProvider
        provider = AzureSTTProvider()
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = MagicMock(text="2 bedroom apartment in Beirut")
        provider._client = mock_client
        with patch("app.ai.azure_openai.settings") as mock_settings:
            mock_settings.azure_openai_endpoint = "https://resource.openai.azure.com/"
            mock_settings.azure_whisper_endpoint = "https://resource.services.ai.azure.com/api/projects/project-id"
            mock_settings.azure_openai_api_key = "test-key"
            mock_settings.azure_whisper_deployment = "whisper-1"
            result = await provider.transcribe(b"fake_audio_bytes", content_type="audio/wav")
        assert "Beirut" in result

    async def test_azure_whisper_uses_azure_resource_endpoint(self):
        from app.ai.azure_openai import AzureSTTProvider

        provider = AzureSTTProvider()
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.return_value = MagicMock(text="hello")

        with patch("app.ai.azure_openai.settings") as mock_settings, patch("openai.AzureOpenAI") as mock_openai:
            mock_settings.azure_openai_endpoint = "https://resource.openai.azure.com/"
            mock_settings.azure_openai_api_key = "test-key"
            mock_settings.azure_openai_api_version = "2024-02-01"
            mock_settings.azure_whisper_deployment = "whisper"
            mock_openai.return_value = mock_client

            await provider.transcribe(b"fake_audio_bytes", content_type="audio/wav")

        assert mock_openai.call_args.kwargs["azure_endpoint"] == "https://resource.openai.azure.com"
        assert mock_openai.call_args.kwargs["api_version"] == "2024-02-01"
        assert mock_client.audio.transcriptions.create.call_args.kwargs["language"] == "en"
        assert mock_client.audio.transcriptions.create.call_args.kwargs["response_format"] == "verbose_json"

    async def test_azure_whisper_requires_resource_endpoint(self):
        from app.ai.azure_openai import AzureSTTProvider

        provider = AzureSTTProvider()
        with patch("app.ai.azure_openai.settings") as mock_settings:
            mock_settings.azure_openai_endpoint = ""
            mock_settings.azure_openai_api_key = "test-key"

            with pytest.raises(RuntimeError, match="endpoint and api key"):
                provider._get_client()

    async def test_azure_whisper_returns_fallback_on_error(self):
        from app.ai.azure_openai import AzureSTTProvider
        provider = AzureSTTProvider()
        mock_client = MagicMock()
        mock_client.audio.transcriptions.create.side_effect = Exception("API error")
        provider._client = mock_client
        with patch("app.ai.azure_openai.settings") as mock_settings:
            mock_settings.azure_whisper_deployment = "whisper-1"
            with pytest.raises(Exception):
                await provider.transcribe(b"bad_bytes", content_type="audio/wav")

    async def test_voice_search_service_orchestration(self):
        from app.search.service import SearchService
        svc = SearchService.__new__(SearchService)
        svc._session = AsyncMock()
        with patch("app.ai.registry.get_stt_provider") as mock_stt, \
             patch.object(svc, "extract_search_intent", new_callable=AsyncMock) as mock_extract:
            from app.search.schemas import SearchIntent, ConfirmedSearchFilters
            mock_stt.return_value.transcribe = AsyncMock(return_value="2BR in Beirut")
            mock_extract.return_value = SearchIntent(
                source_mode="voice",
                filters=ConfirmedSearchFilters(bedrooms=2, city="Beirut"),
                confidence="high",
            )
            result = await svc.transcribe_and_extract(b"audio", content_type="audio/wav")
        assert result.transcript.transcript == "2BR in Beirut"
        assert result.intent.filters.city == "Beirut"

    async def test_voice_search_service_empty_transcript_raises_validation(self):
        from app.search.service import SearchService
        from app.common.exceptions import ValidationError

        svc = SearchService.__new__(SearchService)
        svc._session = AsyncMock()

        with patch("app.ai.registry.get_stt_provider") as mock_stt:
            mock_stt.return_value.transcribe = AsyncMock(return_value="   ")
            with pytest.raises(ValidationError) as exc_info:
                await svc.transcribe_and_extract(b"audio", content_type="audio/wav")

        assert exc_info.value.error_code == "VOICE_TRANSCRIPTION_EMPTY"

    async def test_voice_search_service_provider_failure_raises_service_unavailable(self):
        from app.search.service import SearchService
        from app.common.exceptions import ServiceUnavailableError

        svc = SearchService.__new__(SearchService)
        svc._session = AsyncMock()

        with patch("app.ai.registry.get_stt_provider") as mock_stt:
            mock_stt.return_value.transcribe = AsyncMock(side_effect=Exception("DeploymentNotFound"))
            with pytest.raises(ServiceUnavailableError) as exc_info:
                await svc.transcribe_and_extract(b"audio", content_type="audio/wav")

        assert exc_info.value.error_code == "VOICE_TRANSCRIPTION_UNAVAILABLE"

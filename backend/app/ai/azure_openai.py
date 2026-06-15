from __future__ import annotations

from urllib.parse import urljoin
from typing import Any

from app.ai.providers import ChatProvider, EmbeddingProvider, STTProvider
from app.common.config import settings


def _normalize_azure_base_url(endpoint: str) -> str:
    endpoint = endpoint.rstrip("/")
    if endpoint.endswith("/openai/v1"):
        return endpoint
    return urljoin(f"{endpoint}/", "openai/v1")


class AzureOpenAIProvider(ChatProvider, EmbeddingProvider):
    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
                raise RuntimeError("Azure OpenAI endpoint and api key must be configured")

            self._client = OpenAI(
                base_url=_normalize_azure_base_url(settings.azure_openai_endpoint),
                api_key=settings.azure_openai_api_key,
            )
        return self._client

    async def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        client = self._get_client()
        deployment = kwargs.get("model") or settings.azure_openai_embedding_deployment
        if not deployment:
            raise RuntimeError("Azure OpenAI embedding deployment must be configured")

        response = client.embeddings.create(
            model=deployment,
            input=texts,
        )
        return [item.embedding for item in response.data]

    async def chat(self, messages: list[dict], **kwargs: Any) -> dict:
        client = self._get_client()
        deployment = kwargs.get("model") or settings.azure_openai_chat_deployment
        if not deployment:
            raise RuntimeError("Azure OpenAI chat deployment must be configured")

        response = client.responses.create(
            model=deployment,
            input=[
                {
                    "role": message["role"],
                    "content": message["content"],
                }
                for message in messages
            ],
            temperature=kwargs.get("temperature", 0.1),
        )
        text = (getattr(response, "output_text", "") or "").strip()
        if not text:
            raise RuntimeError("Azure OpenAI returned an empty response")
        return {"text": text, "model": deployment, "raw": response}


def get_azure_openai_provider() -> AzureOpenAIProvider:
    return AzureOpenAIProvider()


class AzureSTTProvider(STTProvider):
    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import AzureOpenAI

            if not settings.azure_openai_endpoint or not settings.azure_openai_api_key:
                raise RuntimeError("Azure OpenAI endpoint and api key must be configured")
            self._client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint.rstrip("/"),
                api_key=settings.azure_openai_api_key,
                api_version=settings.azure_openai_api_version,
            )
        return self._client

    async def transcribe(self, audio_bytes: bytes, **kwargs: Any) -> str:
        client = self._get_client()
        deployment = kwargs.get("model") or settings.azure_whisper_deployment
        if not deployment:
            raise RuntimeError("Azure Whisper deployment must be configured")
        import io
        content_type = kwargs.get("content_type", "audio/wav")
        ext = content_type.split("/")[-1] if "/" in content_type else "wav"
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = f"audio.{ext}"
        response = client.audio.transcriptions.create(
            model=deployment,
            file=audio_file,
            language="en",
            response_format="verbose_json",
        )
        return response.text


def get_azure_stt_provider() -> AzureSTTProvider:
    return AzureSTTProvider()

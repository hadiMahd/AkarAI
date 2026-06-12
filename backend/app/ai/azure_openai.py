from __future__ import annotations

from urllib.parse import urljoin
from typing import Any

from app.ai.providers import EmbeddingProvider
from app.common.config import settings


def _normalize_azure_base_url(endpoint: str) -> str:
    endpoint = endpoint.rstrip("/")
    if endpoint.endswith("/openai/v1"):
        return endpoint
    return urljoin(f"{endpoint}/", "openai/v1")


class AzureOpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI

            if settings.azure_openai_endpoint and settings.azure_openai_embedding_deployment and settings.azure_openai_api_key:
                self._client = OpenAI(
                    base_url=_normalize_azure_base_url(settings.azure_openai_endpoint),
                    api_key=settings.azure_openai_api_key,
                )
            else:
                raise RuntimeError(
                    "Azure OpenAI endpoint, embedding deployment, and api key must be configured"
                )
        return self._client

    async def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        client = self._get_client()
        response = client.embeddings.create(
            model=settings.azure_openai_embedding_deployment,
            input=texts,
        )
        return [item.embedding for item in response.data]


def get_azure_openai_embedding_provider() -> AzureOpenAIEmbeddingProvider:
    return AzureOpenAIEmbeddingProvider()

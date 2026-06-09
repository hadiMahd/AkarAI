from app.common.config import settings
from app.ai.providers import (
    ChatProvider,
    EmbeddingProvider,
    RerankingProvider,
    OCRProvider,
    STTProvider,
    TTSProvider,
    ImageModerationProvider,
    ImageQualityProvider,
    SpamClassifierProvider,
    LeadClassifierProvider,
)

_registry: dict[str, object] = {}


def register_provider(name: str, provider: object) -> None:
    _registry[name] = provider


def get_provider(name: str) -> object:
    if name in _registry:
        return _registry[name]
    raise KeyError(f"Provider '{name}' not registered. Available: {list(_registry.keys())}")


def get_chat_provider() -> ChatProvider:
    provider = get_provider(settings.ai_primary_provider)
    assert isinstance(provider, ChatProvider), f"Provider '{settings.ai_primary_provider}' does not implement ChatProvider"
    return provider


def get_embedding_provider() -> EmbeddingProvider:
    provider = get_provider(settings.ai_primary_provider)
    assert isinstance(provider, EmbeddingProvider)
    return provider

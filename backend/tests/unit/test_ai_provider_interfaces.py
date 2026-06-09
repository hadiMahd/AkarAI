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


class DummyChatProvider:
    async def chat(self, messages: list[dict], **kwargs) -> dict:
        return {"content": "hello"}


class DummyEmbeddingProvider:
    async def embed(self, texts: list[str], **kwargs) -> list[list[float]]:
        return [[0.1] * 128 for _ in texts]


class TestAIProviderInterfaces:
    def test_chat_provider_isinstance_check(self):
        p = DummyChatProvider()
        assert isinstance(p, ChatProvider)

    def test_embedding_provider_isinstance_check(self):
        p = DummyEmbeddingProvider()
        assert isinstance(p, EmbeddingProvider)

    def test_empty_chat_impl_fails_protocol(self):
        class BadChat:
            pass
        assert not isinstance(BadChat(), ChatProvider)

    def test_all_providers_are_protocols(self):
        from typing import Protocol
        protocols = [
            ChatProvider, EmbeddingProvider, RerankingProvider,
            OCRProvider, STTProvider, TTSProvider,
            ImageModerationProvider, ImageQualityProvider,
            SpamClassifierProvider, LeadClassifierProvider,
        ]
        for p in protocols:
            assert issubclass(p, Protocol)

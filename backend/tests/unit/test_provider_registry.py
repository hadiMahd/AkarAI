import pytest

from app.ai.registry import register_provider, get_provider


class TestProviderRegistry:
    def test_register_and_get_provider(self):
        dummy = object()
        register_provider("test-prov", dummy)
        result = get_provider("test-prov")
        assert result is dummy

    def test_get_unregistered_raises(self):
        with pytest.raises(KeyError, match="not registered"):
            get_provider("nonexistent-prov-999")


class TestSTTProviderRegistryLookup:
    def test_get_stt_provider_returns_stt_provider(self):
        from app.ai.registry import get_stt_provider
        from app.ai.providers import STTProvider
        provider = get_stt_provider()
        assert isinstance(provider, STTProvider)

    def test_stt_provider_is_cached_in_registry(self):
        from app.ai.registry import get_stt_provider
        p1 = get_stt_provider()
        p2 = get_stt_provider()
        assert p1 is p2

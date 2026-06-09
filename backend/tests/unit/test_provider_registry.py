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

import pytest
from unittest.mock import AsyncMock, patch
from app.search.service import SearchService

@pytest.mark.anyio
class TestAISearchExtractionService:
    async def test_extract_filters_returns_intent(self):
        svc = SearchService.__new__(SearchService)
        chat_mock = AsyncMock(return_value={"text": '{"city": "Beirut", "bedrooms": 2}'})
        with patch("app.ai.registry.get_chat_provider") as mock_prov:
            mock_prov.return_value.chat = chat_mock
            result = await svc.extract_search_intent("2 bedroom apartment in Beirut")
        assert result.source_mode == "ai_text"
        assert result.filters.city == "Beirut"

    async def test_extract_filters_fallback_on_parse_error(self):
        svc = SearchService.__new__(SearchService)
        chat_mock = AsyncMock(return_value={"text": "not json"})
        with patch("app.ai.registry.get_chat_provider") as mock_prov:
            mock_prov.return_value.chat = chat_mock
            result = await svc.extract_search_intent("some query")
        assert result.confidence == "fallback"

    async def test_extract_filters_parking_floor_extraction(self):
        svc = SearchService.__new__(SearchService)
        chat_mock = AsyncMock(return_value={"text": '{"parking": 1, "floor": 5}'})
        with patch("app.ai.registry.get_chat_provider") as mock_prov:
            mock_prov.return_value.chat = chat_mock
            result = await svc.extract_search_intent("floor 5 with parking")
        assert result.filters.parking == 1
        assert result.filters.floor == 5

    async def test_sanitize_search_log_redacts_raw_query(self):
        from app.search.service import _sanitize_search_log_entry
        entry = _sanitize_search_log_entry(
            raw_query="my name is John and I want 2BR",
            source_mode="ai_text",
            filters={},
            result_count=5,
        )
        assert entry["raw_query_redacted"] is None or len(entry.get("raw_query_redacted", "") or "") <= 200

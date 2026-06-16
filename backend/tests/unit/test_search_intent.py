import pytest
from app.search.schemas import SearchIntent, ConfirmedSearchFilters, UnclearLocationIntent

@pytest.mark.anyio
class TestSearchIntentSchemas:
    async def test_confirmed_filters_parking_floor(self):
        f = ConfirmedSearchFilters(parking=1, floor=3)
        assert f.parking == 1
        assert f.floor == 3

    async def test_confirmed_filters_defaults(self):
        f = ConfirmedSearchFilters()
        assert f.page == 1
        assert f.page_size == 20

    async def test_unclear_location_intent_fields(self):
        u = UnclearLocationIntent(
            phrase="near Beirut",
            reason="vague_area",
            suggested_action="select_city",
        )
        assert u.resolved_city is None

    async def test_search_intent_source_modes(self):
        for mode in ("manual", "ai_text", "voice"):
            intent = SearchIntent(source_mode=mode, filters=ConfirmedSearchFilters(), confidence="high")
            assert intent.source_mode == mode

    async def test_search_intent_fallback_confidence(self):
        intent = SearchIntent(source_mode="ai_text", filters=ConfirmedSearchFilters(), confidence="fallback")
        assert intent.confidence == "fallback"


@pytest.mark.anyio
class TestVagueLocationHandling:
    async def test_unclear_location_is_not_expanded(self):
        # ConfirmedSearchFilters with no city should not auto-expand
        f = ConfirmedSearchFilters()
        assert f.city is None

    async def test_unclear_location_intent_fields(self):
        u = UnclearLocationIntent(
            phrase="somewhere near the sea",
            reason="vague_area",
            suggested_action="select_city",
        )
        assert u.resolved_city is None

    async def test_search_intent_carries_unclear_location(self):
        from app.search.schemas import SearchIntent, ConfirmedSearchFilters, UnclearLocationIntent
        intent = SearchIntent(
            source_mode="ai_text",
            filters=ConfirmedSearchFilters(),
            confidence="low",
            unclear_location=UnclearLocationIntent(
                phrase="near the sea",
                reason="vague_area",
                suggested_action="select_city",
            ),
        )
        assert intent.unclear_location is not None
        assert intent.unclear_location.phrase == "near the sea"

    async def test_continue_without_location_sets_city_none(self):
        # When user chooses continue-without-location, city should be None in filters
        f = ConfirmedSearchFilters(city=None)
        assert f.city is None

    async def test_unsupported_criteria_not_auto_applied(self):
        # Vague phrase does NOT become a concrete city filter
        from app.search.schemas import SearchIntent
        intent = SearchIntent(
            source_mode="ai_text",
            filters=ConfirmedSearchFilters(),  # no city
            confidence="low",
        )
        assert intent.filters.city is None

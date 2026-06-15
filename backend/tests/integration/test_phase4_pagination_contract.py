import pytest


@pytest.mark.anyio
class TestPhase4PaginationContract:
    async def test_pagination_params_defaults(self):
        from app.common.dependencies import pagination_params
        result = pagination_params()
        assert result["page"] == 1
        assert result["page_size"] == 20
        assert result["offset"] == 0

    async def test_pagination_params_custom_page(self):
        from app.common.dependencies import pagination_params
        result = pagination_params(page=3, page_size=10)
        assert result["page"] == 3
        assert result["page_size"] == 10
        assert result["offset"] == 20

    async def test_pagination_params_clamped_max_page_size(self):
        from app.common.dependencies import pagination_params
        result = pagination_params(page=1, page_size=200)
        assert result["page_size"] == 100

    async def test_pagination_params_clamped_min_page(self):
        from app.common.dependencies import pagination_params
        result = pagination_params(page=0)
        assert result["page"] == 1
        assert result["offset"] == 0

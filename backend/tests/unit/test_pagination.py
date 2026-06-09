import pytest

from app.common.pagination import PaginationRequest, PaginationResult


class TestPaginationRequest:
    def test_defaults(self):
        p = PaginationRequest()
        assert p.page == 1
        assert p.page_size == 20
        assert p.offset == 0
        assert p.limit == 20

    def test_custom_page_and_size(self):
        p = PaginationRequest(page=3, page_size=10)
        assert p.page == 3
        assert p.page_size == 10
        assert p.offset == 20
        assert p.limit == 10

    def test_page_below_one_clamped(self):
        p = PaginationRequest(page=0, page_size=10)
        assert p.page == 1

    def test_page_size_exceeds_maximum(self):
        p = PaginationRequest(page=1, page_size=200)
        assert p.page_size == 100

    def test_negative_page_clamped(self):
        p = PaginationRequest(page=-5)
        assert p.page == 1


class TestPaginationResult:
    def test_has_next(self):
        p = PaginationRequest(page=1, page_size=10)
        result = PaginationResult(items=list(range(10)), total=25, pagination=p)
        assert result.has_next is True
        assert result.has_previous is False

    def test_has_previous(self):
        p = PaginationRequest(page=2, page_size=10)
        result = PaginationResult(items=list(range(10)), total=25, pagination=p)
        assert result.has_next is False
        assert result.has_previous is True

    def test_no_next_on_exact_fit(self):
        p = PaginationRequest(page=1, page_size=10)
        result = PaginationResult(items=list(range(10)), total=10, pagination=p)
        assert result.has_next is False

    def test_empty_list(self):
        p = PaginationRequest(page=1, page_size=10)
        result = PaginationResult(items=[], total=0, pagination=p)
        assert result.has_next is False
        assert result.has_previous is False
        assert result.total == 0

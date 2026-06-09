from app.common.config import settings


class PaginationRequest:
    def __init__(self, page: int = 1, page_size: int | None = None):
        self.page = max(1, page)
        self.page_size = min(
            page_size if page_size else settings.pagination_default_page_size,
            settings.pagination_max_page_size,
        )

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginationResult:
    def __init__(self, items: list, total: int, pagination: PaginationRequest):
        self.items = items
        self.page = pagination.page
        self.page_size = pagination.page_size
        self.total = total
        self.has_next = (pagination.page * pagination.page_size) < total
        self.has_previous = pagination.page > 1

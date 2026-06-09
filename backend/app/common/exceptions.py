class AppException(Exception):
    status_code: int = 500
    detail: str = "Internal server error"

    def __init__(self, detail: str | None = None, status_code: int | None = None):
        if detail is not None:
            self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        super().__init__(self.detail)


class NotFoundError(AppException):
    status_code = 404
    detail = "Resource not found"


class ValidationError(AppException):
    status_code = 422
    detail = "Validation error"


class ServiceUnavailableError(AppException):
    status_code = 503
    detail = "Service unavailable"

from typing import Optional


class AppException(Exception):
    status_code: int = 500
    detail: str = "Internal server error"
    error_code: Optional[str] = None

    def __init__(
        self,
        detail: Optional[str] = None,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
    ):
        if detail is not None:
            self.detail = detail
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        super().__init__(self.detail)


class NotFoundError(AppException):
    status_code = 404
    detail = "Resource not found"
    error_code = "NOT_FOUND"


class ValidationError(AppException):
    status_code = 422
    detail = "Validation error"
    error_code = "VALIDATION_ERROR"


class ServiceUnavailableError(AppException):
    status_code = 503
    detail = "Service unavailable"
    error_code = "SERVICE_UNAVAILABLE"


class UnauthorizedError(AppException):
    status_code = 401
    detail = "Authentication required"
    error_code = "UNAUTHORIZED"


class ForbiddenError(AppException):
    status_code = 403
    detail = "Permission denied"
    error_code = "FORBIDDEN"


class ConflictError(AppException):
    status_code = 409
    detail = "Resource conflict"
    error_code = "CONFLICT"


class RateLimitExceededError(AppException):
    status_code = 429
    detail = "Rate limit exceeded"
    error_code = "RATE_LIMIT_EXCEEDED"

import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.common.config import settings


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assigns a unique request ID to every incoming request."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(
            settings.request_id_header,
            str(uuid.uuid4()),
        )
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers[settings.request_id_header] = request_id
        return response


def get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")

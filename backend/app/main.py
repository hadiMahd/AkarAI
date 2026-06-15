from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.config import settings
from app.common.exceptions import AppException, ValidationError
from app.common.health import router as health_router
from app.common.lifespan import lifespan
from app.common.request_id import RequestIDMiddleware, get_request_id

app = FastAPI(
    title=settings.project_name,
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.effective_cors_origins,
    allow_credentials=settings.effective_cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(RequestIDMiddleware)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail,
            "error_code": exc.error_code,
            "request_id": get_request_id(request),
        },
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": exc.detail,
            "error_code": exc.error_code,
            "request_id": get_request_id(request),
        },
    )


@app.exception_handler(PermissionError)
async def permission_error_handler(request: Request, exc: PermissionError) -> JSONResponse:
    return JSONResponse(
        status_code=403,
        content={
            "status": "error",
            "detail": str(exc),
            "error_code": "FORBIDDEN",
            "request_id": get_request_id(request),
        },
    )


_STATUS_ERROR_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
    409: "CONFLICT",
    413: "PAYLOAD_TOO_LARGE",
    415: "UNSUPPORTED_MEDIA_TYPE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMIT_EXCEEDED",
    500: "INTERNAL_SERVER_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


def _error_code_for_status(status_code: int) -> str:
    return _STATUS_ERROR_CODES.get(status_code, "HTTP_ERROR")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "detail": detail,
            "error_code": _error_code_for_status(exc.status_code),
            "request_id": get_request_id(request),
        },
        headers=exc.headers,
    )


def _summarize_validation_errors(errors: list[dict]) -> str:
    if not errors:
        return "Request payload is invalid."
    parts: list[str] = []
    for err in errors[:3]:
        loc = [str(part) for part in err.get("loc", []) if part not in ("body", "query", "path")]
        field = ".".join(loc) if loc else "field"
        msg = str(err.get("msg") or "is invalid").strip()
        parts.append(f"{field}: {msg}" if field else msg)
    if len(errors) > 3:
        parts.append(f"(+{len(errors) - 3} more)")
    return "; ".join(parts)


def _sanitize_validation_errors(errors: list[dict]) -> list[dict]:
    sanitized: list[dict] = []
    for err in errors:
        ctx = err.get("ctx")
        if isinstance(ctx, dict):
            sanitized_ctx = {}
            for key, value in ctx.items():
                if isinstance(value, Exception):
                    sanitized_ctx[key] = {
                        "type": err.get("type", "value_error"),
                        "message": str(value),
                    }
                else:
                    sanitized_ctx[key] = value
            err = {**err, "ctx": sanitized_ctx}
        sanitized.append(err)
    return sanitized


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    errors = _sanitize_validation_errors(list(exc.errors()))
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "detail": _summarize_validation_errors(errors),
            "error_code": "VALIDATION_ERROR",
            "errors": errors,
            "request_id": get_request_id(request),
        },
    )


from app.auth.router import router as auth_router, tenant_router

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(tenant_router)

from app.agencies.router import router as agencies_router
from app.listings.router import (
    router as listings_router,
    public_router as public_listings_router,
    saved_router as saved_listings_router,
    comparison_router as comparison_sessions_router,
)
from app.viewings.router import router as viewings_router, booking_router, agency_viewings_router
from app.leads.router import router as leads_router, agency_router as agency_leads_router
from app.notifications.router import router as notifications_router
from app.search.router import router as search_router, public_search_router
from app.analytics.router import router as analytics_router
from app.rag.router import doc_router as rag_doc_router
from app.rag.router import chat_router as rag_chat_router
from app.rag.router import retrieval_router as rag_retrieval_router

app.include_router(agencies_router)
app.include_router(listings_router)
app.include_router(public_listings_router)
app.include_router(saved_listings_router)
app.include_router(comparison_sessions_router)
app.include_router(viewings_router)
app.include_router(booking_router)
app.include_router(agency_viewings_router)
app.include_router(leads_router)
app.include_router(agency_leads_router)
app.include_router(notifications_router)
app.include_router(search_router)
app.include_router(public_search_router)
app.include_router(analytics_router)
app.include_router(rag_doc_router)
app.include_router(rag_chat_router)
app.include_router(rag_retrieval_router)

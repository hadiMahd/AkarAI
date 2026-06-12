from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from app.search.router import router as search_router
from app.analytics.router import router as analytics_router
from app.rag.router import router as rag_router

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
app.include_router(analytics_router)
app.include_router(rag_router)

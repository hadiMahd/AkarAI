import json

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
    allow_origins=json.loads(settings.cors_origins),
    allow_credentials=True,
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

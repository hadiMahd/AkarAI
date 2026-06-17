from fastapi import FastAPI

from app.config import settings
from app.routes import router

app = FastAPI(
    title="Lead Model Service",
    version="0.1.0",
)

app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "lead-model-service"}

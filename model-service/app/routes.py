from fastapi import APIRouter, Request

from app.schemas import ClassifyRequest, ClassifyResponse, StageResult, HealthResponse
from app.service import classify_lead

router = APIRouter()


@router.post("/classify", response_model=ClassifyResponse)
async def classify(request: Request, body: ClassifyRequest):
    result = await classify_lead(
        lead_id=body.lead_id,
        tenant_id=body.tenant_id,
        message=body.message,
        name=body.name,
        email=body.email,
    )
    return result


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse()

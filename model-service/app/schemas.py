from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    lead_id: UUID
    tenant_id: UUID
    message: str = ""
    name: Optional[str] = None
    email: Optional[str] = None


class StageResult(BaseModel):
    stage: str
    status: str
    label: Optional[str] = None
    score: Optional[float] = None
    details: Optional[dict] = None


class ClassifyResponse(BaseModel):
    lead_id: UUID
    tenant_id: UUID
    spam_result: StageResult
    level_result: Optional[StageResult] = None


class CallbackPayload(BaseModel):
    lead_id: UUID
    tenant_id: UUID
    stage: str
    status: str
    label: Optional[str] = None
    score: Optional[float] = None
    details: Optional[dict] = None
    retry_count: int = 0


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "lead-model-service"

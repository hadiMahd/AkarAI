from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass
class TenantContext:
    actor_id: Optional[UUID] = None
    role: Optional[str] = None
    permissions: list[str] = field(default_factory=list)
    tenant_id: Optional[UUID] = None
    request_id: Optional[str] = None
    source: str = "internal"

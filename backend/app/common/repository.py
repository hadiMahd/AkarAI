from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.common.tenant import TenantContext


class BaseRepository:
    """Base repository providing session access to subclasses.

    Feature repositories must inherit from this class.
    Do NOT create dao.py files; repository.py is the data access layer.
    """

    def __init__(self, session: AsyncSession, tenant: Optional[TenantContext] = None):
        self._session = session
        self._tenant = tenant

    @property
    def session(self) -> AsyncSession:
        return self._session

    @property
    def tenant_context(self) -> Optional[TenantContext]:
        return self._tenant

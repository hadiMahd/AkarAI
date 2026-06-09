from fastapi import Depends, Request

from app.common.exceptions import UnauthorizedError, ForbiddenError
from app.auth.permissions import PermissionKey


async def get_current_user(request: Request) -> dict:
    """Placeholder: returns a stub user. Real auth implementation in later phases."""
    # Phase 3+ will decode JWT from Authorization header and validate via Redis blacklist.
    return {"id": "00000000-0000-0000-0000-000000000000", "role": "user"}


def require_permission(*permissions: PermissionKey):
    """Dependency factory: checks that current user has all required permissions.

    Placeholder in Phase 2 — always passes. Real RBAC enforcement in later phases.
    """

    async def _check(current_user: dict = Depends(get_current_user)) -> dict:
        # Placeholder: full RBAC check in later phases
        _ = permissions
        return current_user

    return _check

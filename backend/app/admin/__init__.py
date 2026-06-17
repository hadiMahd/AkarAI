"""Phase 15: Platform Admin Dashboard read-only backend.

This module is intentionally a thin layer over the ``query_service`` /
``service`` modules. The router is only allowed to:
- validate the dashboard access gate (role + permission)
- accept filter scope parameters
- delegate to the service layer
"""

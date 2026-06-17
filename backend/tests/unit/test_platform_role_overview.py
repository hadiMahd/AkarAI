"""Unit tests for the platform admin role-overview query helpers.

The role overview endpoint serves a read-only catalog of supported
roles, their mapped surface access, and their restricted surfaces.
Pure-function constants are tested without a database.
"""
from __future__ import annotations

from app.admin.query_service import (
    ROLE_DISPLAY_NAMES,
    ROLE_RESTRICTED_SURFACES,
    ROLE_SURFACE_ACCESS,
)

ALL_ROLES = {"user", "agency_admin", "support_employee", "platform_admin"}


class TestRoleConstants:
    def test_all_roles_have_display_names(self):
        assert set(ROLE_DISPLAY_NAMES.keys()) >= ALL_ROLES
        for slug in ALL_ROLES:
            name = ROLE_DISPLAY_NAMES[slug]
            assert isinstance(name, str)
            assert name.strip() == name

    def test_all_roles_have_surface_access(self):
        assert set(ROLE_SURFACE_ACCESS.keys()) >= ALL_ROLES
        for slug in ALL_ROLES:
            surfaces = ROLE_SURFACE_ACCESS[slug]
            assert isinstance(surfaces, tuple)
            assert len(surfaces) > 0

    def test_all_roles_have_restricted_surfaces(self):
        assert set(ROLE_RESTRICTED_SURFACES.keys()) >= ALL_ROLES
        for slug in ALL_ROLES:
            restricted = ROLE_RESTRICTED_SURFACES[slug]
            assert isinstance(restricted, tuple)
            assert len(restricted) > 0

    def test_surface_access_and_restricted_are_disjoint(self):
        for slug in ALL_ROLES:
            access = set(ROLE_SURFACE_ACCESS.get(slug, ()))
            restricted = set(ROLE_RESTRICTED_SURFACES.get(slug, ()))
            assert access.isdisjoint(restricted), f"overlap for {slug}"

    def test_platform_admin_has_dashboard_surfaces(self):
        access = set(ROLE_SURFACE_ACCESS["platform_admin"])
        assert "Platform admin dashboard" in access
        assert "Aggregate marketplace insights" in access

    def test_user_role_restricted_from_agency_dashboard(self):
        restricted = set(ROLE_RESTRICTED_SURFACES["user"])
        assert "Agency dashboard" in restricted
        assert "Platform admin dashboard" in restricted

    def test_support_employee_cannot_mutate_listings(self):
        restricted = set(ROLE_RESTRICTED_SURFACES["support_employee"])
        assert "Agency listings (write)" in restricted

    def test_agency_admin_restricted_from_platform_dashboard(self):
        restricted = set(ROLE_RESTRICTED_SURFACES["agency_admin"])
        assert "Platform admin dashboard" in restricted

    def test_role_slugs_are_consistent(self):
        for role_slug in ALL_ROLES:
            assert role_slug in ROLE_SURFACE_ACCESS
            assert role_slug in ROLE_RESTRICTED_SURFACES
            assert role_slug in ROLE_DISPLAY_NAMES

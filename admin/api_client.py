"""HTTP client used by the Streamlit admin app to talk to the platform
admin backend read APIs.

The client deliberately stays minimal — it focuses on:
- token-bearer authentication
- explicit timeouts
- consistent error envelopes
- marketplace aggregate insight / audit log / role overview endpoints
"""

from __future__ import annotations

import os
from typing import Any, Mapping

import requests


class AdminAPIError(Exception):
    """Raised when the backend returns a non-2xx response."""

    def __init__(self, status_code: int, detail: str, error_code: str = "API_ERROR"):
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(f"HTTP {status_code}: {detail} ({error_code})")


class AdminAPIClient:
    """Thin wrapper around ``requests`` for the platform admin app."""

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 15.0,
        session: requests.Session | None = None,
    ):
        self._base_url = (base_url or os.getenv("BACKEND_URL", "http://backend:8000")).rstrip("/")
        self._timeout = timeout
        self._session = session or requests.Session()

    @property
    def base_url(self) -> str:
        return self._base_url

    def _headers(self, token: str | None) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        params: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            response = self._session.request(
                method=method,
                url=url,
                headers=self._headers(token),
                params={k: v for k, v in (params or {}).items() if v is not None} or None,
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise AdminAPIError(0, f"Backend unreachable: {exc}", "BACKEND_UNREACHABLE") from exc

        if response.status_code >= 400:
            raise self._build_error(response)

        if response.status_code == 204 or not response.content:
            return {}

        try:
            return response.json()
        except ValueError as exc:
            raise AdminAPIError(
                response.status_code, "Invalid JSON from backend", "INVALID_JSON"
            ) from exc

    def _coerce_detail(self, value: Any) -> str:
        if isinstance(value, str) and value.strip():
            return value
        if isinstance(value, list):
            parts = []
            for item in value:
                if isinstance(item, dict):
                    loc = item.get("loc")
                    msg = item.get("msg")
                    if loc and msg:
                        parts.append(f"{'.'.join(str(part) for part in loc)}: {msg}")
                    elif msg:
                        parts.append(str(msg))
                elif item:
                    parts.append(str(item))
            return "; ".join(parts) or "Request failed"
        if isinstance(value, dict):
            if isinstance(value.get("message"), str) and value["message"].strip():
                return value["message"]
            if isinstance(value.get("detail"), str) and value["detail"].strip():
                return value["detail"]
        return "Request failed"

    def _build_error(self, response: requests.Response) -> AdminAPIError:
        detail = "Request failed"
        error_code = "API_ERROR"
        try:
            payload = response.json()
            if isinstance(payload, dict):
                detail = self._coerce_detail(payload.get("detail"))
                error_code = payload.get("error_code") or error_code
            elif isinstance(payload, list):
                detail = self._coerce_detail(payload)
        except ValueError:
            text = response.text.strip()
            if text:
                detail = text
        return AdminAPIError(response.status_code, detail, error_code)

    # ── Auth helpers ──────────────────────────────────────────────────

    def login(self, email: str, password: str) -> dict[str, Any]:
        return (
            self._request("POST", "/auth/login", params=None)
            if False
            else self._post_json("/auth/login", {"email": email, "password": password})
        )

    def _post_json(self, path: str, body: dict[str, Any]) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        try:
            response = self._session.post(
                url,
                json=body,
                headers=self._headers(None),
                timeout=self._timeout,
            )
        except requests.RequestException as exc:
            raise AdminAPIError(0, f"Backend unreachable: {exc}", "BACKEND_UNREACHABLE") from exc
        return self._parse(response)

    def _parse(self, response: requests.Response) -> dict[str, Any]:
        if response.status_code >= 400:
            raise self._build_error(response)
        if response.status_code == 204 or not response.content:
            return {}
        try:
            return response.json()
        except ValueError as exc:
            raise AdminAPIError(
                response.status_code, "Invalid JSON from backend", "INVALID_JSON"
            ) from exc

    # ── Platform dashboard endpoints ─────────────────────────────────

    def get_current_actor(self, token: str) -> dict[str, Any]:
        return self._request("GET", "/auth/me", token=token)

    def get_insights(
        self,
        token: str,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
        range_preset: str | None = None,
        city: str | None = None,
        property_type: str | None = None,
        listing_purpose: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/api/v1/platform/dashboard/insights",
            token=token,
            params={
                "date_from": date_from,
                "date_to": date_to,
                "range_preset": range_preset,
                "city": city,
                "property_type": property_type,
                "listing_purpose": listing_purpose,
            },
        )

    def list_audit_logs(
        self,
        token: str,
        *,
        page: int = 1,
        page_size: int = 20,
        date_from: str | None = None,
        date_to: str | None = None,
        feature_area: str | None = None,
        actor_role: str | None = None,
        result: str | None = None,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/api/v1/platform/audit-logs",
            token=token,
            params={
                "page": page,
                "page_size": page_size,
                "date_from": date_from,
                "date_to": date_to,
                "feature_area": feature_area,
                "actor_role": actor_role,
                "result": result,
            },
        )

    def get_role_overview(self, token: str) -> dict[str, Any]:
        return self._request("GET", "/api/v1/platform/roles/overview", token=token)

    def list_rag_eval_runs(
        self,
        token: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        return self._request(
            "GET",
            "/api/v1/platform/rag-evals/runs",
            token=token,
            params={"page": page, "page_size": page_size},
        )

    def get_rag_eval_run(self, token: str, run_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/api/v1/platform/rag-evals/runs/{run_id}",
            token=token,
        )


__all__ = ["AdminAPIError", "AdminAPIClient"]

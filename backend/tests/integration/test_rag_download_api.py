from unittest.mock import patch

import pytest


FAKE_PDF_BYTES = b"%PDF-1.4\n%fake\n"


async def _login(async_client, email: str, password: str) -> str:
    response = await async_client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_authenticated_rag_download(async_client, agency_admin_user):
    user, password = agency_admin_user
    token = await _login(async_client, user.email, password)

    with patch("app.rag.service._extract_text_from_pdf", return_value=["policy text"]):
        upload_resp = await async_client.post(
            "/api/v1/agencies/rag/documents",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": ("policy.pdf", FAKE_PDF_BYTES, "application/pdf")},
        )

    assert upload_resp.status_code == 202
    document = upload_resp.json()
    assert document["download_url"].endswith(f"/api/v1/agencies/rag/documents/{document['id']}/download")

    download_resp = await async_client.get(
        document["download_url"],
        headers={"Authorization": f"Bearer {token}"},
    )

    assert download_resp.status_code == 200
    assert download_resp.headers["content-disposition"].startswith("inline; filename=\"policy.pdf\"")
    assert download_resp.content == FAKE_PDF_BYTES

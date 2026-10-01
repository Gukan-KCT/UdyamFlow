import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.mark.asyncio
async def test_document_vault_and_pre_validation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login as applicant
        login_res = await client.post(
            "/api/auth/login",
            json={"email": "applicant@udyamflow.gov.in", "password": "Demo@123"},
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Check vault contents
        vault_res = await client.get("/api/documents/vault", headers=headers)
        assert vault_res.status_code == 200
        vault = vault_res.json()
        assert len(vault) >= 3

        # 3. Test pre-validation with all required docs present
        preval_res = await client.post(
            "/api/documents/pre-validate",
            headers=headers,
            json={
                "approval_ids": ["APPR-CTE-PCB"],
                "uploaded_doc_types": [],
            },
        )
        assert preval_res.status_code == 200
        val_data = preval_res.json()
        assert val_data["score"] > 0
        assert "autofill_suggestions" in val_data
        assert "PAN" in val_data["autofill_suggestions"]

        # 4. Upload a new document to vault
        upload_res = await client.post(
            "/api/documents/upload",
            headers=headers,
            json={
                "doc_type": "PROJECT_REPORT",
                "title": "Automated Testing Feasibility Report",
                "file_name": "test_feasibility.pdf",
                "file_size": 250000,
                "mime_type": "application/pdf",
                "storage_path": "/storage/docs/test_feasibility.pdf",
            },
        )
        assert upload_res.status_code == 200
        assert upload_res.json()["doc_type"] == "PROJECT_REPORT"

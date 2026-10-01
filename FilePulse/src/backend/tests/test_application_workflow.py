import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.mark.asyncio
async def test_single_window_application_end_to_end():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login as applicant
        login_res = await client.post(
            "/api/auth/login",
            json={"email": "applicant@udyamflow.gov.in", "password": "Demo@123"},
        )
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Get profile
        prof_res = await client.get("/api/profile", headers=headers)
        assert prof_res.status_code == 200
        profile = prof_res.json()
        assert profile is not None
        prof_id = profile["profile_id"]

        # 3. Create a single-window application with 2 approvals
        app_res = await client.post(
            "/api/applications",
            headers=headers,
            json={
                "profile_id": prof_id,
                "approval_ids": ["APPR-CTE-PCB", "APPR-FIRE-NOC"],
                "remarks": "Test Application for Automated Pipeline Verification",
            },
        )
        assert app_res.status_code == 200
        app_data = app_res.json()
        assert app_data["status"] == "SUBMITTED"
        assert len(app_data["approvals"]) == 2
        app_id = app_data["application_id"]
        sub_pcb = next(a for a in app_data["approvals"] if a["approval_id"] == "APPR-CTE-PCB")

        # 4. Department officer logs in (PCB officer)
        pcb_login = await client.post(
            "/api/auth/login",
            json={"email": "officer.pcb@udyamflow.gov.in", "password": "Demo@123"},
        )
        pcb_token = pcb_login.json()["access_token"]
        pcb_headers = {"Authorization": f"Bearer {pcb_token}"}

        # 5. PCB officer raises a clarification query
        query_res = await client.post(
            "/api/applications/queries",
            headers=pcb_headers,
            json={
                "app_approval_id": sub_pcb["app_approval_id"],
                "query_text": "Please provide secondary containment bund volume calculations.",
            },
        )
        assert query_res.status_code == 200
        query_data = query_res.json()
        assert query_data["status"] == "OPEN"
        qid = query_data["query_id"]

        # 6. Applicant responds to query
        resp_res = await client.post(
            f"/api/applications/queries/{qid}/respond",
            headers=headers,
            json={
                "response_text": "Attached calculations showing 110% storage capacity as per CPCB norms.",
                "response_doc_ids": ["doc_site_01"],
            },
        )
        assert resp_res.status_code == 200
        assert resp_res.json()["status"] == "RESPONDED"

        # 7. PCB officer approves the sub-approval
        action_res = await client.post(
            f"/api/applications/{app_id}/approvals/{sub_pcb['app_approval_id']}/action",
            headers=pcb_headers,
            json={"action": "APPROVE"},
        )
        assert action_res.status_code == 200
        updated_app = action_res.json()
        updated_sub_pcb = next(a for a in updated_app["approvals"] if a["approval_id"] == "APPR-CTE-PCB")
        assert updated_sub_pcb["status"] == "APPROVED"

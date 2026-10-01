import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.mark.asyncio
async def test_common_inspections_and_grievances():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Officer login
        off_res = await client.post(
            "/api/auth/login",
            json={"email": "officer.fire@udyamflow.gov.in", "password": "Demo@123"},
        )
        off_token = off_res.json()["access_token"]
        off_headers = {"Authorization": f"Bearer {off_token}"}

        # 1. Schedule a multi-department inspection
        sched_res = await client.post(
            "/api/inspections/schedule",
            headers=off_headers,
            json={
                "application_id": "app_2026_0042",
                "scheduled_date": "2026-03-15",
                "time_slot": "Morning (10:00 - 13:00)",
                "departments": ["DEPT-FIRE", "DEPT-PCB"],
                "notes": "Coordinated joint site verification of perimeter fire access and effluent storage tanks.",
            },
        )
        assert sched_res.status_code == 200
        insp_data = sched_res.json()
        assert insp_data["status"] == "SCHEDULED"
        insp_id = insp_data["inspection_id"]

        # 2. Submit joint inspection report
        rep_res = await client.post(
            f"/api/inspections/{insp_id}/report",
            headers=off_headers,
            json={
                "verdict": "SATISFACTORY",
                "report_text": "All safety distances, underground water reservoir capacity, and boundary set-backs match submitted drawings.",
                "findings": ["Setbacks verified: 6m clear", "Water tank capacity: 100,000 litres confirmed"],
            },
        )
        assert rep_res.status_code == 200
        assert rep_res.json()["status"] == "COMPLETED"
        assert rep_res.json()["verdict"] == "SATISFACTORY"

        # 3. File a grievance as applicant
        app_res = await client.post(
            "/api/auth/login",
            json={"email": "applicant@udyamflow.gov.in", "password": "Demo@123"},
        )
        app_token = app_res.json()["access_token"]
        app_headers = {"Authorization": f"Bearer {app_token}"}

        grv_res = await client.post(
            "/api/grievances",
            headers=app_headers,
            json={
                "department_id": "DEPT-FIRE",
                "category": "Delay in Scrutiny",
                "subject": "Follow-up on inspection clearance certificate",
                "description": "Joint inspection was completed satisfactorily, awaiting final clearance upload.",
            },
        )
        assert grv_res.status_code == 200
        grv_data = grv_res.json()
        assert grv_data["level"] == 1
        gid = grv_data["grievance_id"]

        # 4. Escalate grievance to level 2
        esc_res = await client.post(f"/api/grievances/{gid}/escalate", headers=app_headers)
        assert esc_res.status_code == 200
        assert esc_res.json()["level"] == 2
        assert esc_res.json()["status"] == "ESCALATED"

        # 5. Resolve grievance as officer
        resolve_res = await client.post(
            f"/api/grievances/{gid}/resolve",
            headers=off_headers,
            json={"status": "RESOLVED", "resolution_notes": "Certificate signed and issued."},
        )
        assert resolve_res.status_code == 200
        assert resolve_res.json()["status"] == "RESOLVED"

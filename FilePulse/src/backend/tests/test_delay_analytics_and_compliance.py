import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.mark.asyncio
async def test_delay_analytics_and_compliance():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Nodal officer login
        nodal_res = await client.post(
            "/api/auth/login",
            json={"email": "nodal@udyamflow.gov.in", "password": "Demo@123"},
        )
        token = nodal_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Test delay analytics scanning applications
        delay_res = await client.get("/api/delay-analytics/applications", headers=headers)
        assert delay_res.status_code == 200
        delay_data = delay_res.json()
        assert "total_active_approvals" in delay_data
        assert "stuck_count" in delay_data
        assert "looping_count" in delay_data
        assert "at_risk_count" in delay_data

        # 2. Test departmental bottlenecks
        bottleneck_res = await client.get("/api/delay-analytics/bottlenecks", headers=headers)
        assert bottleneck_res.status_code == 200
        b_data = bottleneck_res.json()
        assert len(b_data) >= 4
        dept_codes = [d["department_code"] for d in b_data]
        assert "PCB" in dept_codes
        assert "FIRE" in dept_codes

        # 3. Test compliance tasks
        comp_res = await client.get("/api/compliance/tasks", headers=headers)
        assert comp_res.status_code == 200

        # 4. Test schemes list
        schemes_res = await client.get("/api/schemes")
        assert schemes_res.status_code == 200
        schemes = schemes_res.json()
        assert len(schemes) >= 3
        assert "SAMPLE / ILLUSTRATIVE" in schemes[0]["sample_disclaimer"]

        # 5. Public verification endpoint
        verify_res = await client.get("/api/certificates/verify/NON-EXISTENT")
        assert verify_res.status_code == 200
        assert verify_res.json()["valid"] is False

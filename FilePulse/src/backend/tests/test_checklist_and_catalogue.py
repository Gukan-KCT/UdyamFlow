import pytest
from httpx import ASGITransport, AsyncClient
from main import app


@pytest.mark.asyncio
async def test_checklist_sectors_and_stages():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        sectors_res = await client.get("/api/checklist/sectors")
        assert sectors_res.status_code == 200
        sectors = sectors_res.json()
        assert len(sectors) >= 5
        sector_ids = [s["id"] for s in sectors]
        assert "Manufacturing" in sector_ids

        stages_res = await client.get("/api/checklist/stages")
        assert stages_res.status_code == 200
        assert len(stages_res.json()) >= 3


@pytest.mark.asyncio
async def test_checklist_generation_manufacturing():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "sector": "Manufacturing",
            "stage": "Pre-Establishment",
            "project_size": "Small",
            "location_type": "Industrial Area",
            "investment_cr": 7.5,
            "turnover_cr": 18.0,
        }
        res = await client.post("/api/checklist/generate", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["total_approvals"] >= 3
        assert data["estimated_total_fee"] > 0
        assert data["critical_path_sla_days"] > 0
        # Verify sample disclaimer present
        assert "SAMPLE / ILLUSTRATIVE" in data["sample_disclaimer"]

        # Check matched approvals include PCB CTE and Fire NOC
        approval_ids = [a["approval_id"] for a in data["matched_approvals"]]
        assert "APPR-CTE-PCB" in approval_ids
        assert "APPR-FIRE-NOC" in approval_ids

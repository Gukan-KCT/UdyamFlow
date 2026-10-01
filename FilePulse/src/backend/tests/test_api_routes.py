import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.db import init_db, ingest_csv_data, DATA_DIR, get_connection
from app.core.orchestrator import run_full_pipeline


@pytest.fixture(scope="module", autouse=True)
def setup_test_db():
    conn = get_connection()
    init_db(conn)
    ingest_csv_data(conn, DATA_DIR)
    conn.close()


@pytest.mark.asyncio
async def test_dashboard_summary():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_active_files" in data
        assert "total_alerted_files" in data
        assert "reference_date" in data
        assert data["total_active_files"] > 0


@pytest.mark.asyncio
async def test_alerts_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/alerts")
        assert response.status_code == 200
        alerts = response.json()
        assert isinstance(alerts, list)


@pytest.mark.asyncio
async def test_alerts_pagination_envelope():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/alerts?page=1&page_size=5&format=envelope")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert data["page"] == 1
        assert data["page_size"] == 5
        assert len(data["items"]) <= 5


@pytest.mark.asyncio
async def test_alerts_invalid_filter():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/alerts?type=invalid_type")
        assert response.status_code == 400
        err = response.json()
        assert err["error"] is True
        assert err["status_code"] == 400


@pytest.mark.asyncio
async def test_validation_error_envelope():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # page must be >= 1
        response = await client.get("/api/alerts?page=0")
        assert response.status_code == 422
        err = response.json()
        assert err["error"] is True
        assert err["status_code"] == 422
        assert "detail" in err


@pytest.mark.asyncio
async def test_org_tree():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/org/tree")
        assert response.status_code == 200
        nodes = response.json()
        assert isinstance(nodes, list)
        assert len(nodes) > 0


@pytest.mark.asyncio
async def test_employee_workload():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # E301 is Section Officer P. Singh
        response = await client.get("/api/employees/E301/workload")
        assert response.status_code == 200
        data = response.json()
        assert "employee_id" in data
        assert data["employee_id"] == "E301"
        assert "active_file_count" in data
        assert "files" in data


@pytest.mark.asyncio
async def test_file_journey():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/files/F5001/journey")
        assert response.status_code == 200
        data = response.json()
        assert "file" in data
        assert "events" in data
        assert "graph" in data


@pytest.mark.asyncio
async def test_assistant_chat_validation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/assistant/chat", json={"message": "   "})
        assert response.status_code == 400


@pytest.mark.asyncio
async def test_assistant_chat_valid(monkeypatch):
    monkeypatch.setattr("app.ai.ollama_service.AI_PROVIDER", "none")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/assistant/chat", json={"message": "What is the status of the office?"})
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "intent" in data

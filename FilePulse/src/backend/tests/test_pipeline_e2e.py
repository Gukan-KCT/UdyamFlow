import pytest
import sqlite3
from datetime import datetime

from app.db import init_db, ingest_csv_data, DATA_DIR
from app.core.orchestrator import run_full_pipeline


@pytest.mark.asyncio
async def test_full_pipeline_run(monkeypatch):
    monkeypatch.setattr("app.ai.ollama_service.AI_PROVIDER", "none")
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    result = await run_full_pipeline(conn, data_dir=DATA_DIR, top_k_ai_insights=5)
    assert len(result.alerts) > 0
    assert len(result.consolidated_alerts) > 0
    assert len(result.insights) > 0

    # Ensure consolidated alerts are ordered by risk score descending
    scores = [a.risk_score for a in result.consolidated_alerts]
    assert scores == sorted(scores, reverse=True)

    conn.close()

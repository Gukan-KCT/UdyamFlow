import pytest
from datetime import datetime
from app.models import Alert, FileRecord, Event
from app.ai.prompt import get_fallback_insight
from app.ai.ollama_service import generate_insight, generate_chat_reply


def test_fallback_insight_content():
    # Rotting fallback
    rot_fb = get_fallback_insight("ROTTING", {"title": "File A", "holder": "Officer B", "days": 30, "status": "Active"})
    assert "File A" in rot_fb.plain_language_summary
    assert "Officer B" in rot_fb.plain_language_summary
    assert rot_fb.confidence == "Low"

    # Looping fallback
    loop_fb = get_fallback_insight("LOOPING", {"title": "File B", "a": "Finance", "b": "PWD", "trips": 3, "span": 30})
    assert "Finance" in loop_fb.plain_language_summary
    assert "PWD" in loop_fb.plain_language_summary

    # Conformance fallback
    conf_fb = get_fallback_insight("CONFORMANCE", {"title": "File C", "stages": "Budget Check"})
    assert "Budget Check" in conf_fb.plain_language_summary

    # Compound fallback
    comp_fb = get_fallback_insight("COMPOUND", {"title": "File D", "trips": 3, "days": 45})
    assert "looping" in comp_fb.plain_language_summary.lower()
    assert "stuck" in comp_fb.plain_language_summary.lower()


@pytest.mark.asyncio
async def test_generate_insight_provider_none(monkeypatch):
    monkeypatch.setattr("app.ai.ollama_service.AI_PROVIDER", "none")
    now = datetime(2025, 3, 18, 9, 0)
    alert = Alert(
        alert_id="ROT-F1",
        file_id="F1",
        alert_type="ROTTING",
        severity="HIGH",
        risk_score=50,
        days_inactive=30,
        detected_at=now,
    )
    file_record = FileRecord(
        file_id="F1",
        title="Test File",
        file_type="Administration",
        priority="Medium",
        created_at=datetime(2025, 1, 1),
        deadline_at=datetime(2025, 3, 1),
        current_holder_id="E001",
        current_status="Active",
    )
    events = []
    insight = await generate_insight(alert, file_record, events)
    assert insight is not None
    assert "Test File" in insight.plain_language_summary
    assert insight.source == "rule_based_fallback"


@pytest.mark.asyncio
async def test_generate_chat_reply_fallback(monkeypatch):
    monkeypatch.setattr("app.ai.ollama_service.AI_PROVIDER", "none")
    context = {
        "file": {
            "file_id": "F1001",
            "title": "Road Tender",
            "status": "Active",
            "current_holder": "Amit",
            "priority": "High",
            "deadline": "2025-03-25",
        }
    }
    reply = await generate_chat_reply(
        prompt="Tell me about F1001",
        system_prompt="system",
        intent="FILE_DETAIL",
        context=context,
    )
    assert "F1001" in reply
    assert "Road Tender" in reply

from datetime import datetime
from app.models import Alert, AiInsight
from app.core.alert_consolidator import consolidate_alerts


def test_consolidate_alerts_merges_types(sample_files, sample_employees):
    now = datetime(2025, 3, 18, 9, 0)
    alerts = [
        Alert(alert_id="ROT-F1001", file_id="F1001", alert_type="ROTTING", severity="CRITICAL", risk_score=75, days_inactive=45, detected_at=now),
        Alert(alert_id="LOOP-F1001", file_id="F1001", alert_type="LOOPING", severity="HIGH", risk_score=85, loop_round_trips=3, detected_at=now),
    ]
    insights = [
        AiInsight(
            insight_id="ins-1",
            alert_id="LOOP-F1001",
            plain_language_summary="Bouncing between Finance and PWD",
            likely_blocker="Budget approval ambiguity",
            recommended_action="Convene joint meeting",
            confidence="High",
            source="fallback",
            generated_at=now,
        )
    ]

    consolidated = consolidate_alerts(alerts, sample_files, sample_employees, insights)
    assert len(consolidated) == 1
    c = consolidated[0]
    assert c.file_id == "F1001"
    assert "LOOPING" in c.alert_types
    assert "ROTTING" in c.alert_types
    assert c.risk_score == 85
    assert c.severity == "CRITICAL"
    assert c.current_holder_name == "Amit Sharma"
    assert c.ai_summary == "Bouncing between Finance and PWD"

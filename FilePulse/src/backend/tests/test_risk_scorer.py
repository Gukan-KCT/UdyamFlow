from datetime import datetime
from app.models import Alert, FileRecord
from app.core.risk_scorer import score_alerts, score_alerts_from_db, _risk_score


def test_risk_score_calculation():
    # Base calculation
    # age_factor = 45 / 90 = 0.5 -> 0.35 * 0.5 = 0.175
    # deadline_proximity = 1 - 15/30 = 0.5 -> 0.25 * 0.5 = 0.125
    # loop_intensity = 0 -> 0.0
    # priority = 'High' (1.0) -> 0.10 * 1.0 = 0.10
    # workload = 10/40 = 0.25 -> 0.10 * 0.25 = 0.025
    # total = (0.175 + 0.125 + 0 + 0.10 + 0.025) * 100 = 42.5 -> int(43.0) = 43
    score = _risk_score(
        days_inactive=45,
        days_to_deadline=15,
        is_overdue=False,
        round_trips=None,
        priority="High",
        holder_active_files=10,
    )
    assert score == 43


def test_risk_score_overdue_gives_full_deadline_weight():
    score_overdue = _risk_score(
        days_inactive=45,
        days_to_deadline=-5,
        is_overdue=True,
        round_trips=None,
        priority="High",
        holder_active_files=10,
    )
    score_not_overdue = _risk_score(
        days_inactive=45,
        days_to_deadline=15,
        is_overdue=False,
        round_trips=None,
        priority="High",
        holder_active_files=10,
    )
    assert score_overdue > score_not_overdue


def test_compound_bonus_applied(sample_files):
    now = datetime(2025, 3, 18, 9, 0)
    alerts = [
        Alert(alert_id="ROT-F1001", file_id="F1001", alert_type="ROTTING", severity="CRITICAL", risk_score=0, days_inactive=45, detected_at=now),
        Alert(alert_id="LOOP-F1001", file_id="F1001", alert_type="LOOPING", severity="HIGH", risk_score=0, loop_round_trips=3, detected_at=now),
    ]
    scored = score_alerts(alerts, sample_files, now)
    assert len(scored) == 2
    # Single alert alone without compound bonus
    single_scored = score_alerts([alerts[0]], sample_files, now)
    # The compound alert must receive the +15 bonus
    assert scored[0].risk_score >= single_scored[0].risk_score + 15 or scored[0].risk_score == 100


def test_score_alerts_from_db(populated_db):
    now = datetime(2025, 3, 18, 9, 0)
    sample_alert = Alert(
        alert_id="ROT-test",
        file_id="F5001",
        alert_type="ROTTING",
        severity="HIGH",
        risk_score=0,
        days_inactive=30,
        detected_at=now,
    )
    scored = score_alerts_from_db(populated_db, [sample_alert], now)
    assert len(scored) == 1
    assert scored[0].risk_score > 0

from datetime import datetime
from app.models import Event, FileRecord
from app.core.stuck_detector import detect_rotting, detect_rotting_from_db, rotting_severity, escalate_severity


def test_rotting_severity_thresholds():
    # Campaign tier (> 90 days inactive)
    assert rotting_severity(90, 60) == "CAMPAIGN"
    assert rotting_severity(120, 60) == "CAMPAIGN"

    # Absolute fallback (expected_span_days <= 0)
    assert rotting_severity(45, 0) == "CRITICAL"
    assert rotting_severity(30, 0) == "HIGH"
    assert rotting_severity(15, 0) == "WARNING"
    assert rotting_severity(10, 0) is None

    # Ratio-based (expected_span_days = 60)
    # WARNING: 0.5 * 60 = 30
    # HIGH: 1.0 * 60 = 60
    # CRITICAL: 1.5 * 60 = 90
    assert rotting_severity(35, 60) == "WARNING"
    assert rotting_severity(65, 60) == "HIGH"


def test_escalate_severity():
    assert escalate_severity("WARNING") == "HIGH"
    assert escalate_severity("HIGH") == "CRITICAL"
    assert escalate_severity("CRITICAL") == "CAMPAIGN"
    assert escalate_severity("CAMPAIGN") == "CAMPAIGN"


def test_detect_rotting_excludes_closed_files(sample_files):
    events = []
    now = datetime(2025, 3, 18, 9, 0)
    alerts = detect_rotting(sample_files, events, now)
    alerted_file_ids = {a.file_id for a in alerts}
    assert "F1003" not in alerted_file_ids  # F1003 is Closed


def test_detect_rotting_escalates_when_overdue():
    now = datetime(2025, 3, 18, 9, 0)
    # File created Jan 10, deadline Feb 28 (now is March 18 -> overdue)
    files = [
        FileRecord(
            file_id="F1002",
            title="Overdue File",
            file_type="Procurement",
            priority="High",
            created_at=datetime(2025, 1, 10, 9, 0),
            deadline_at=datetime(2025, 2, 28, 17, 0),
            current_holder_id="E001",
            current_status="Active",
        )
    ]
    # Last event on Jan 20 (inactive ~57 days on a 49-day span -> rot_ratio > 1.0 -> HIGH escalated to CRITICAL)
    events = [
        Event(
            event_id="EVT001",
            file_id="F1002",
            timestamp=datetime(2025, 1, 20, 10, 0),
            action="FORWARDED",
            from_user_id="E002",
            to_user_id="E001",
            department="Finance",
            stage="Review",
            note_text="Pending budget",
        )
    ]
    alerts = detect_rotting(files, events, now)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.is_overdue is True
    assert alert.alert_type == "ROTTING"
    assert alert.severity in ("CRITICAL", "CAMPAIGN")


def test_detect_rotting_from_db(populated_db):
    now = datetime(2025, 3, 18, 9, 0)
    alerts = detect_rotting_from_db(populated_db, now)
    assert len(alerts) > 0
    for a in alerts:
        assert a.alert_type == "ROTTING"
        assert a.days_inactive is not None
        assert a.days_inactive > 0

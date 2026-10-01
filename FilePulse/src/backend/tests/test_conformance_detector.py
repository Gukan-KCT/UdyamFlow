from datetime import datetime
from app.models import Event, FileRecord
from app.core.conformance_detector import detect_conformance, detect_conformance_from_db


def test_conformance_valid_sequence(sample_files):
    now = datetime(2025, 3, 18, 9, 0)
    # Infrastructure expects: Receipt -> Initial Review -> Budget Check -> Approval -> Dispatch
    events = [
        Event(event_id="E1", file_id="F1001", timestamp=datetime(2025, 1, 2), action="RECEIPT_DIARISED", from_user_id="E001", to_user_id="E001", department="Finance", stage="Receipt", note_text=""),
        Event(event_id="E2", file_id="F1001", timestamp=datetime(2025, 1, 5), action="FORWARDED", from_user_id="E001", to_user_id="E002", department="Finance", stage="Initial Review", note_text=""),
        Event(event_id="E3", file_id="F1001", timestamp=datetime(2025, 1, 10), action="FORWARDED", from_user_id="E002", to_user_id="E001", department="PWD", stage="Budget Check", note_text=""),
    ]
    alerts = detect_conformance(sample_files, events, now)
    assert len(alerts) == 0


def test_conformance_skipped_stage_flagged(sample_files):
    now = datetime(2025, 3, 18, 9, 0)
    # Infrastructure: skips 'Initial Review' and 'Budget Check' directly to 'Approval'
    events = [
        Event(event_id="E1", file_id="F1001", timestamp=datetime(2025, 1, 2), action="RECEIPT_DIARISED", from_user_id="E001", to_user_id="E001", department="Finance", stage="Receipt", note_text=""),
        Event(event_id="E2", file_id="F1001", timestamp=datetime(2025, 1, 10), action="FORWARDED", from_user_id="E001", to_user_id="E002", department="Finance", stage="Approval", note_text=""),
    ]
    alerts = detect_conformance(sample_files, events, now)
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.alert_type == "CONFORMANCE"
    assert "Initial Review" in alert.skipped_stages
    assert "Budget Check" in alert.skipped_stages


def test_detect_conformance_from_db(populated_db):
    now = datetime(2025, 3, 18, 9, 0)
    alerts = detect_conformance_from_db(populated_db, now)
    assert isinstance(alerts, list)

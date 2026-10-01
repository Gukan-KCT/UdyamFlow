from datetime import datetime, timedelta
from app.models import Event, FileRecord
from app.core.loop_detector import detect_looping, detect_looping_from_db, _is_real_transfer


def test_is_real_transfer():
    t1 = Event(
        event_id="E1",
        file_id="F1",
        timestamp=datetime(2025, 2, 1, 10, 0),
        action="FORWARDED",
        from_user_id="E001",
        to_user_id="E002",
        department="Finance",
        stage="Review",
        note_text="",
    )
    assert _is_real_transfer(t1) is True

    # Same sender and receiver -> not a real transfer
    t2 = Event(
        event_id="E2",
        file_id="F1",
        timestamp=datetime(2025, 2, 1, 11, 0),
        action="FORWARDED",
        from_user_id="E001",
        to_user_id="E001",
        department="Finance",
        stage="Review",
        note_text="",
    )
    assert _is_real_transfer(t2) is False

    # Non-transfer action
    t3 = Event(
        event_id="E3",
        file_id="F1",
        timestamp=datetime(2025, 2, 1, 12, 0),
        action="NOTE_ADDED",
        from_user_id="E001",
        to_user_id="E002",
        department="Finance",
        stage="Review",
        note_text="",
    )
    assert _is_real_transfer(t3) is False


def test_detect_looping_two_round_trips(sample_files, sample_employees):
    now = datetime(2025, 3, 18, 9, 0)
    base = datetime(2025, 2, 1, 9, 0)

    # Create 2 round trips between E001 (Finance) and E002 (PWD) within 10 days
    events = [
        Event(event_id="EV1", file_id="F1001", timestamp=base + timedelta(days=1), action="FORWARDED", from_user_id="E001", to_user_id="E002", department="Finance", stage="Review", note_text=""),
        Event(event_id="EV2", file_id="F1001", timestamp=base + timedelta(days=2), action="RETURNED", from_user_id="E002", to_user_id="E001", department="PWD", stage="Review", note_text=""),
        Event(event_id="EV3", file_id="F1001", timestamp=base + timedelta(days=3), action="FORWARDED", from_user_id="E001", to_user_id="E002", department="Finance", stage="Review", note_text=""),
        Event(event_id="EV4", file_id="F1001", timestamp=base + timedelta(days=4), action="RETURNED", from_user_id="E002", to_user_id="E001", department="PWD", stage="Review", note_text=""),
    ]

    alerts = detect_looping(sample_files, events, sample_employees, now)
    assert len(alerts) >= 1
    user_loop = next((a for a in alerts if "USER" in a.alert_id), None)
    assert user_loop is not None
    assert user_loop.loop_round_trips == 2
    assert user_loop.alert_type == "LOOPING"


def test_detect_looping_single_round_trip_not_flagged(sample_files, sample_employees):
    now = datetime(2025, 3, 18, 9, 0)
    base = datetime(2025, 2, 1, 9, 0)

    # 1 round trip is legitimate inquiry, must NOT flag
    events = [
        Event(event_id="EV1", file_id="F1001", timestamp=base + timedelta(days=1), action="CLARIFICATION_REQUESTED", from_user_id="E001", to_user_id="E002", department="Finance", stage="Review", note_text=""),
        Event(event_id="EV2", file_id="F1001", timestamp=base + timedelta(days=2), action="CLARIFICATION_PROVIDED", from_user_id="E002", to_user_id="E001", department="PWD", stage="Review", note_text=""),
    ]

    alerts = detect_looping(sample_files, events, sample_employees, now)
    assert len(alerts) == 0


def test_detect_looping_from_db(populated_db):
    now = datetime(2025, 3, 18, 9, 0)
    alerts = detect_looping_from_db(populated_db, now)
    assert len(alerts) > 0
    for a in alerts:
        assert a.alert_type == "LOOPING"
        assert a.loop_round_trips >= 2

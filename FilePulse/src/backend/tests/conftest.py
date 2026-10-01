import os
import sqlite3
from datetime import datetime
from pathlib import Path
import pytest

os.environ.setdefault("DEMO_NOW", "2025-03-18T09:00:00")

from app.db import init_db, ingest_csv_data, DATA_DIR
from app.models import Employee, FileRecord, Event


@pytest.fixture
def memory_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def populated_db(memory_db):
    ingest_csv_data(memory_db, DATA_DIR)
    return memory_db


@pytest.fixture
def sample_employees():
    return [
        Employee(
            employee_id="E001",
            name="Amit Sharma",
            role="Section Officer",
            department="Finance",
            manager_id=None,
        ),
        Employee(
            employee_id="E002",
            name="Priya Patel",
            role="Assistant Director",
            department="PWD",
            manager_id="E001",
        ),
        Employee(
            employee_id="E003",
            name="Rajesh Rao",
            role="Under Secretary",
            department="PWD",
            manager_id="E001",
        ),
    ]


@pytest.fixture
def sample_files():
    return [
        FileRecord(
            file_id="F1001",
            title="Bridge Construction Tender",
            file_type="Infrastructure",
            priority="High",
            created_at=datetime(2025, 1, 1, 9, 0),
            deadline_at=datetime(2025, 3, 25, 17, 0),
            current_holder_id="E001",
            current_status="Active",
        ),
        FileRecord(
            file_id="F1002",
            title="Office Laptop Procurement",
            file_type="Procurement",
            priority="Medium",
            created_at=datetime(2025, 1, 10, 9, 0),
            deadline_at=datetime(2025, 2, 28, 17, 0),
            current_holder_id="E002",
            current_status="Active",
        ),
        FileRecord(
            file_id="F1003",
            title="Archived Maintenance File",
            file_type="Administration",
            priority="Low",
            created_at=datetime(2024, 11, 1, 9, 0),
            deadline_at=datetime(2024, 12, 1, 17, 0),
            current_holder_id="E001",
            current_status="Closed",
        ),
    ]

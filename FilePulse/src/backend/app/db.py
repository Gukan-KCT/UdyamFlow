import csv
import os
import shutil
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from app.models import AiInsight, Alert, Employee, Event, FileRecord


BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"


def get_db_path() -> Path:
    # On Vercel / AWS Lambda serverless runtime, only /tmp is writable
    if os.getenv("VERCEL"):
        tmp_db = Path("/tmp/filepulse.sqlite3")
        src_db = DATA_DIR / "filepulse.sqlite3"
        # Copy pre-built DB if it was committed; otherwise init_db() will
        # create the tables from scratch when the lifespan hook runs.
        if not tmp_db.exists() and src_db.exists():
            try:
                tmp_db.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_db, tmp_db)
            except Exception as e:
                print(f"Warning: Failed to copy database to /tmp: {e}")
        return tmp_db
    return DATA_DIR / "filepulse.sqlite3"



DB_PATH = get_db_path()


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    target_path = db_path or get_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS employees (
            employee_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            department TEXT NOT NULL,
            manager_id TEXT,
            FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS files (
            file_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            file_type TEXT NOT NULL,
            priority TEXT NOT NULL,
            created_at TEXT NOT NULL,
            deadline_at TEXT NOT NULL,
            current_holder_id TEXT NOT NULL,
            current_status TEXT NOT NULL,
            FOREIGN KEY (current_holder_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            action TEXT NOT NULL,
            from_user_id TEXT NOT NULL,
            to_user_id TEXT NOT NULL,
            department TEXT NOT NULL,
            stage TEXT NOT NULL,
            note_text TEXT NOT NULL,
            is_transfer INTEGER NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(file_id),
            FOREIGN KEY (from_user_id) REFERENCES employees(employee_id),
            FOREIGN KEY (to_user_id) REFERENCES employees(employee_id)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            alert_id TEXT PRIMARY KEY,
            file_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            days_inactive INTEGER,
            days_to_deadline INTEGER,
            is_overdue INTEGER NOT NULL,
            loop_round_trips INTEGER,
            loop_total_bounces INTEGER,
            loop_party_a TEXT,
            loop_party_b TEXT,
            skipped_stages TEXT,
            detected_at TEXT NOT NULL,
            FOREIGN KEY (file_id) REFERENCES files(file_id)
        );

        CREATE TABLE IF NOT EXISTS ai_insights (
            insight_id TEXT PRIMARY KEY,
            alert_id TEXT NOT NULL,
            plain_language_summary TEXT NOT NULL,
            likely_blocker TEXT NOT NULL,
            recommended_action TEXT NOT NULL,
            confidence TEXT NOT NULL,
            source TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            FOREIGN KEY (alert_id) REFERENCES alerts(alert_id)
        );

        -- =========================================================
        -- UDYAMFLOW SINGLE-WINDOW PLATFORM TABLES
        -- =========================================================

        CREATE TABLE IF NOT EXISTS departments (
            department_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            description TEXT,
            nodal_officer_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT NOT NULL,
            phone TEXT,
            role TEXT NOT NULL, -- applicant, dept_officer, senior_officer, nodal_officer, admin
            department_id TEXT,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        );

        CREATE TABLE IF NOT EXISTS business_profiles (
            profile_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            enterprise_name TEXT NOT NULL,
            entity_type TEXT NOT NULL, -- Proprietorship, Partnership, Pvt Ltd, LLP, Public Ltd
            udyam_registration TEXT,
            pan TEXT NOT NULL,
            gstin TEXT,
            sector TEXT NOT NULL, -- Manufacturing, Services, Agro-processing, Chemical, IT/ITES, Textile
            project_size TEXT NOT NULL, -- Micro, Small, Medium, Large
            investment_cr REAL NOT NULL,
            turnover_cr REAL NOT NULL,
            location_type TEXT NOT NULL, -- Industrial Area, Municipal / Urban, Rural / Panchayat, Eco-sensitive Zone
            district TEXT NOT NULL,
            state TEXT NOT NULL DEFAULT 'National / Multi-State',
            address TEXT NOT NULL,
            lat REAL,
            lng REAL,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS approval_catalogue (
            approval_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department_id TEXT NOT NULL,
            sector TEXT NOT NULL, -- All, or specific sector
            stage TEXT NOT NULL, -- Pre-Establishment, Pre-Operation, Renewal
            project_size TEXT NOT NULL, -- All, or Micro/Small/Medium/Large
            location_type TEXT NOT NULL, -- All, or specific
            statutory_act TEXT NOT NULL,
            max_sla_days INTEGER NOT NULL,
            fee_inr REAL NOT NULL DEFAULT 0.0,
            prerequisites_json TEXT NOT NULL DEFAULT '[]',
            documents_required_json TEXT NOT NULL DEFAULT '[]',
            validity_years INTEGER NOT NULL DEFAULT 1,
            is_active INTEGER NOT NULL DEFAULT 1,
            sample_disclaimer TEXT NOT NULL DEFAULT 'SAMPLE / ILLUSTRATIVE - VERIFY AGAINST OFFICIAL SOURCES',
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        );

        CREATE TABLE IF NOT EXISTS applications (
            application_id TEXT PRIMARY KEY,
            application_number TEXT NOT NULL UNIQUE,
            user_id TEXT NOT NULL,
            profile_id TEXT NOT NULL,
            status TEXT NOT NULL, -- DRAFT, SUBMITTED, UNDER_SCRUTINY, QUERY_RAISED, QUERY_RESPONDED, INSPECTION_SCHEDULED, APPROVED, REJECTED, WITHDRAWN
            submitted_at TEXT,
            target_completion_at TEXT,
            completed_at TEXT,
            total_fee REAL NOT NULL DEFAULT 0.0,
            overall_sla_days INTEGER NOT NULL DEFAULT 30,
            remarks TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (profile_id) REFERENCES business_profiles(profile_id)
        );

        CREATE TABLE IF NOT EXISTS application_approvals (
            app_approval_id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL,
            approval_id TEXT NOT NULL,
            department_id TEXT NOT NULL,
            status TEXT NOT NULL, -- PENDING, IN_REVIEW, QUERY_RAISED, QUERY_RESPONDED, INSPECTION_PENDING, APPROVED, REJECTED
            assigned_officer_id TEXT,
            current_stage TEXT NOT NULL DEFAULT 'DOCUMENT_SCRUTINY',
            sla_days INTEGER NOT NULL,
            deadline_at TEXT,
            fee_paid REAL NOT NULL DEFAULT 0.0,
            risk_score INTEGER NOT NULL DEFAULT 10,
            days_inactive INTEGER NOT NULL DEFAULT 0,
            query_count INTEGER NOT NULL DEFAULT 0,
            loop_count INTEGER NOT NULL DEFAULT 0,
            rejection_reason TEXT,
            approved_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (application_id) REFERENCES applications(application_id),
            FOREIGN KEY (approval_id) REFERENCES approval_catalogue(approval_id),
            FOREIGN KEY (department_id) REFERENCES departments(department_id),
            FOREIGN KEY (assigned_officer_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS documents (
            document_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            profile_id TEXT,
            doc_type TEXT NOT NULL, -- PAN, AADHAAR, LAND_DEED, SITE_PLAN, PROJECT_REPORT, NOC_FIRE, CTE_PCB, FACTORY_LAYOUT
            title TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type TEXT NOT NULL,
            storage_path TEXT NOT NULL,
            hash_sha256 TEXT NOT NULL,
            verified INTEGER NOT NULL DEFAULT 0,
            verified_at TEXT,
            expires_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS document_versions (
            version_id TEXT PRIMARY KEY,
            document_id TEXT NOT NULL,
            version_num INTEGER NOT NULL,
            storage_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            hash_sha256 TEXT NOT NULL,
            uploaded_by TEXT NOT NULL,
            uploaded_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (document_id) REFERENCES documents(document_id)
        );

        CREATE TABLE IF NOT EXISTS verified_data_store (
            store_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            profile_id TEXT,
            field_key TEXT NOT NULL,
            field_value TEXT NOT NULL,
            verified_by_source TEXT NOT NULL,
            verified_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS queries (
            query_id TEXT PRIMARY KEY,
            app_approval_id TEXT NOT NULL,
            department_id TEXT NOT NULL,
            officer_id TEXT NOT NULL,
            query_text TEXT NOT NULL,
            status TEXT NOT NULL, -- OPEN, RESPONDED, RESOLVED
            raised_at TEXT NOT NULL DEFAULT (datetime('now')),
            responded_at TEXT,
            response_text TEXT,
            response_doc_ids_json TEXT DEFAULT '[]',
            FOREIGN KEY (app_approval_id) REFERENCES application_approvals(app_approval_id),
            FOREIGN KEY (department_id) REFERENCES departments(department_id),
            FOREIGN KEY (officer_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS inspections (
            inspection_id TEXT PRIMARY KEY,
            application_id TEXT NOT NULL,
            scheduled_date TEXT NOT NULL,
            time_slot TEXT NOT NULL, -- Morning (10:00 - 13:00), Afternoon (14:00 - 17:00)
            status TEXT NOT NULL, -- SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
            departments_json TEXT NOT NULL DEFAULT '[]',
            officers_json TEXT NOT NULL DEFAULT '[]',
            notes TEXT,
            verdict TEXT, -- SATISFACTORY, CONDITIONAL, UNSATISFACTORY
            report_text TEXT,
            findings_json TEXT DEFAULT '[]',
            completed_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (application_id) REFERENCES applications(application_id)
        );

        CREATE TABLE IF NOT EXISTS certificates (
            certificate_id TEXT PRIMARY KEY,
            app_approval_id TEXT NOT NULL,
            certificate_number TEXT NOT NULL UNIQUE,
            approval_name TEXT NOT NULL,
            department_name TEXT NOT NULL,
            issued_to TEXT NOT NULL,
            enterprise_name TEXT NOT NULL,
            issue_date TEXT NOT NULL DEFAULT (datetime('now')),
            valid_until TEXT NOT NULL,
            qr_verification_code TEXT NOT NULL,
            digital_signature_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'VALID', -- VALID, REVOKED, EXPIRED
            pdf_url TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (app_approval_id) REFERENCES application_approvals(app_approval_id)
        );

        CREATE TABLE IF NOT EXISTS renewals (
            renewal_id TEXT PRIMARY KEY,
            certificate_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            approval_id TEXT NOT NULL,
            current_expiry TEXT NOT NULL,
            reminder_days INTEGER NOT NULL DEFAULT 30,
            renewal_status TEXT NOT NULL DEFAULT 'UPCOMING', -- UPCOMING, APPLICATION_STARTED, RENEWED, OVERDUE
            renewal_application_id TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (certificate_id) REFERENCES certificates(certificate_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS compliance_tasks (
            task_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            enterprise_name TEXT NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL, -- Environmental, Labour, Taxation, Factory Safety, Municipal
            department_name TEXT NOT NULL,
            due_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'PENDING', -- PENDING, COMPLETED, OVERDUE
            recurring_period TEXT NOT NULL DEFAULT 'Annually', -- Monthly, Quarterly, Half-Yearly, Annually
            statutory_ref TEXT NOT NULL,
            completed_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );

        CREATE TABLE IF NOT EXISTS schemes (
            scheme_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            department_name TEXT NOT NULL,
            eligible_sectors_json TEXT NOT NULL DEFAULT '["All"]',
            eligible_sizes_json TEXT NOT NULL DEFAULT '["Micro", "Small", "Medium"]',
            incentive_type TEXT NOT NULL, -- Capital Subsidy, Interest Subvention, Power Tariff Concession, Stamp Duty Exemption
            benefit_details TEXT NOT NULL,
            eligibility_criteria TEXT NOT NULL,
            max_subsidy_inr REAL NOT NULL,
            application_deadline TEXT,
            sample_disclaimer TEXT NOT NULL DEFAULT 'SAMPLE / ILLUSTRATIVE - VERIFY AGAINST OFFICIAL SCHEME GUIDELINES',
            is_active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS scheme_applications (
            scheme_app_id TEXT PRIMARY KEY,
            scheme_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            profile_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'SUBMITTED', -- SUBMITTED, UNDER_SCRUTINY, APPROVED, REJECTED
            claim_amount REAL NOT NULL,
            approved_amount REAL DEFAULT 0.0,
            submitted_at TEXT NOT NULL DEFAULT (datetime('now')),
            reviewed_at TEXT,
            remarks TEXT,
            FOREIGN KEY (scheme_id) REFERENCES schemes(scheme_id),
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (profile_id) REFERENCES business_profiles(profile_id)
        );

        CREATE TABLE IF NOT EXISTS grievances (
            grievance_id TEXT PRIMARY KEY,
            grievance_number TEXT NOT NULL UNIQUE,
            user_id TEXT NOT NULL,
            application_id TEXT,
            department_id TEXT NOT NULL,
            category TEXT NOT NULL, -- Delay in Scrutiny, Unreasonable Query, Inspection Delay, Technical Issue, Other
            subject TEXT NOT NULL,
            description TEXT NOT NULL,
            level INTEGER NOT NULL DEFAULT 1, -- 1: Department Nodal, 2: District Collector / Single Window Authority, 3: State Appellate
            status TEXT NOT NULL DEFAULT 'OPEN', -- OPEN, IN_REVIEW, ESCALATED, RESOLVED, CLOSED
            assigned_to TEXT,
            filed_at TEXT NOT NULL DEFAULT (datetime('now')),
            deadline_at TEXT NOT NULL,
            resolved_at TEXT,
            resolution_notes TEXT,
            escalated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (application_id) REFERENCES applications(application_id),
            FOREIGN KEY (department_id) REFERENCES departments(department_id)
        );

        CREATE TABLE IF NOT EXISTS audit_log (
            audit_id TEXT PRIMARY KEY,
            actor_id TEXT NOT NULL,
            actor_role TEXT NOT NULL,
            action TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            before_state_json TEXT,
            after_state_json TEXT,
            reason TEXT,
            ip_address TEXT,
            timestamp TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS notifications (
            notification_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            title TEXT NOT NULL,
            message TEXT NOT NULL,
            notification_type TEXT NOT NULL DEFAULT 'INFO', -- INFO, ALERT, SUCCESS, WARNING
            is_read INTEGER NOT NULL DEFAULT 0,
            link_url TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        );
        """
    )
    conn.commit()


def ingest_csv_data(conn: sqlite3.Connection, data_dir: Path = DATA_DIR) -> None:
    # In serverless environments, CSV files may not be available
    csv_path = _employee_csv_path(data_dir)
    if not csv_path.exists():
        print(f"Warning: CSV data not found at {data_dir}, skipping CSV ingestion")
        return

    employees = _read_models(csv_path, Employee)
    files = _read_models(data_dir / "files.csv", FileRecord)
    events = _read_models(data_dir / "events.csv", Event)


    with conn:
        conn.execute("DELETE FROM ai_insights")
        conn.execute("DELETE FROM alerts")
        conn.execute("DELETE FROM events")
        conn.execute("DELETE FROM files")
        conn.execute("DELETE FROM employees")

        conn.executemany(
            """
            INSERT INTO employees (employee_id, name, role, department, manager_id)
            VALUES (:employee_id, :name, :role, :department, :manager_id)
            """,
            [employee.model_dump(mode="json") for employee in employees],
        )
        conn.executemany(
            """
            INSERT INTO files (
                file_id, title, file_type, priority, created_at, deadline_at,
                current_holder_id, current_status
            )
            VALUES (
                :file_id, :title, :file_type, :priority, :created_at, :deadline_at,
                :current_holder_id, :current_status
            )
            """,
            [file.model_dump(mode="json") for file in files],
        )
        conn.executemany(
            """
            INSERT INTO events (
                event_id, file_id, timestamp, action, from_user_id, to_user_id,
                department, stage, note_text, is_transfer
            )
            VALUES (
                :event_id, :file_id, :timestamp, :action, :from_user_id, :to_user_id,
                :department, :stage, :note_text, :is_transfer
            )
            """,
            [
                event.model_dump(mode="json") | {"is_transfer": int(event.is_transfer)}
                for event in events
            ],
        )


def insert_alerts(conn: sqlite3.Connection, alerts: Iterable[Alert]) -> None:
    with conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO alerts (
                alert_id, file_id, alert_type, severity, risk_score,
                days_inactive, days_to_deadline, is_overdue,
                loop_round_trips, loop_total_bounces, loop_party_a, loop_party_b,
                skipped_stages, detected_at
            )
            VALUES (
                :alert_id, :file_id, :alert_type, :severity, :risk_score,
                :days_inactive, :days_to_deadline, :is_overdue,
                :loop_round_trips, :loop_total_bounces, :loop_party_a, :loop_party_b,
                :skipped_stages, :detected_at
            )
            """,
            [
                alert.model_dump(mode="json")
                | {"is_overdue": int(alert.is_overdue)}
                for alert in alerts
            ],
        )


def insert_ai_insights(conn: sqlite3.Connection, insights: Iterable[AiInsight]) -> None:
    with conn:
        conn.executemany(
            """
            INSERT OR REPLACE INTO ai_insights (
                insight_id, alert_id, plain_language_summary, likely_blocker,
                recommended_action, confidence, source, generated_at
            )
            VALUES (
                :insight_id, :alert_id, :plain_language_summary, :likely_blocker,
                :recommended_action, :confidence, :source, :generated_at
            )
            """,
            [insight.model_dump(mode="json") for insight in insights],
        )


def _read_models(path: Path, model):
    with path.open(newline="", encoding="utf-8") as csv_file:
        return [model.model_validate(row) for row in csv.DictReader(csv_file)]


def _employee_csv_path(data_dir: Path) -> Path:
    employees_path = data_dir / "employees.csv"
    if employees_path.exists():
        return employees_path
    return data_dir / "employee.csv"

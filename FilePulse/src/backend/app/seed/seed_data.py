from datetime import datetime, timezone
import json
import sqlite3

from app.auth.security import hash_password

SAMPLE_DISCLAIMER = "SAMPLE / ILLUSTRATIVE - VERIFY AGAINST OFFICIAL STATUTORY SOURCES"


def seed_all_udyamflow_data(conn: sqlite3.Connection) -> None:
    """Seeds default departments, users, approval catalogue, schemes, demo profile and application."""
    with conn:
        _seed_departments(conn)
        _seed_users(conn)
        _seed_approval_catalogue(conn)
        _seed_schemes(conn)
        _seed_demo_business_and_application(conn)


def _seed_departments(conn: sqlite3.Connection) -> None:
    depts = [
        ("DEPT-IND", "Department of Industries & Commerce", "IND", "Single-window nodal agency for industrial facilitation & clearances"),
        ("DEPT-PCB", "State Pollution Control Board", "PCB", "Environmental clearances, Consent to Establish (CTE) & Consent to Operate (CTO)"),
        ("DEPT-FIRE", "Fire & Emergency Services Directorate", "FIRE", "Fire safety building plan approval and Fire NOC"),
        ("DEPT-LAB", "Directorate of Labour & Factories", "LAB", "Factory licence, safety verification, boiler inspection"),
        ("DEPT-REV", "Revenue & Land Administration", "REV", "Land conversion (NA), boundary demarcation, zoning verification"),
        ("DEPT-ELEC", "State Power Distribution Utility", "ELEC", "HT/LT industrial power connection & load sanction"),
    ]
    for dept_id, name, code, desc in depts:
        conn.execute(
            """
            INSERT OR REPLACE INTO departments (department_id, name, code, description)
            VALUES (?, ?, ?, ?)
            """,
            (dept_id, name, code, desc),
        )


def _seed_users(conn: sqlite3.Connection) -> None:
    default_pwd = "Demo@123"
    pwd_hash, salt = hash_password(default_pwd)

    users = [
        ("usr_applicant_01", "applicant@udyamflow.gov.in", pwd_hash, salt, "Ramesh Sharma (Apex Precision Tech)", "+91-9876543210", "applicant", None),
        ("usr_officer_ind", "officer.ind@udyamflow.gov.in", pwd_hash, salt, "Priya Menon (Scrutiny Officer - Industries)", "+91-9876543211", "dept_officer", "DEPT-IND"),
        ("usr_officer_pcb", "officer.pcb@udyamflow.gov.in", pwd_hash, salt, "Dr. Arvind Rao (Env Engineer - PCB)", "+91-9876543212", "dept_officer", "DEPT-PCB"),
        ("usr_officer_fire", "officer.fire@udyamflow.gov.in", pwd_hash, salt, "Vikram Rathore (Div Fire Officer)", "+91-9876543213", "dept_officer", "DEPT-FIRE"),
        ("usr_nodal_01", "nodal@udyamflow.gov.in", pwd_hash, salt, "S. K. Verma, IAS (Single Window Nodal Officer)", "+91-9876543214", "nodal_officer", None),
        ("usr_admin_01", "admin@udyamflow.gov.in", pwd_hash, salt, "System Administrator", "+91-9876543215", "admin", None),
    ]

    for uid, email, p_hash, s, name, phone, role, dept_id in users:
        conn.execute(
            """
            INSERT OR REPLACE INTO users (user_id, email, password_hash, salt, full_name, phone, role, department_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (uid, email, p_hash, s, name, phone, role, dept_id),
        )


def _seed_approval_catalogue(conn: sqlite3.Connection) -> None:
    approvals = [
        (
            "APPR-CTE-PCB",
            "Consent to Establish (CTE - Green/Orange/Red)",
            "DEPT-PCB",
            "All",
            "Pre-Establishment",
            "All",
            "All",
            "Water Act 1974 & Air Act 1981",
            30,
            15000.0,
            json.dumps(["Land title deed or lease agreement", "Site plan with coordinate layout", "Process flow & environmental management plan"]),
            json.dumps(["SITE_PLAN", "PROJECT_REPORT", "LAND_DEED"]),
            5,
        ),
        (
            "APPR-FIRE-NOC",
            "Provisional Fire Safety NOC & Building Plan Approval",
            "DEPT-FIRE",
            "All",
            "Pre-Establishment",
            "All",
            "All",
            "State Fire Prevention and Safety Act",
            21,
            8000.0,
            json.dumps(["Architectural plan showing fire exits", "Water reservoir specification", "Road width proof"]),
            json.dumps(["SITE_PLAN", "FACTORY_LAYOUT"]),
            3,
        ),
        (
            "APPR-FACT-LIC",
            "Factory Building Plan Approval & Initial Licence",
            "DEPT-LAB",
            "Manufacturing",
            "Pre-Establishment",
            "All",
            "All",
            "Factories Act 1948",
            30,
            12000.0,
            json.dumps(["Plant layout drawing", "Machinery positioning plan", "Worker safety and ventilation specification"]),
            json.dumps(["FACTORY_LAYOUT", "PROJECT_REPORT"]),
            1,
        ),
        (
            "APPR-LAND-CONV",
            "Land Conversion (Non-Agricultural Permission)",
            "DEPT-REV",
            "All",
            "Pre-Establishment",
            "All",
            "Rural / Panchayat",
            "State Land Revenue Code",
            45,
            25000.0,
            json.dumps(["7/12 extract / Record of Rights", "Cadastral survey map", "Gram Panchayat NOC"]),
            json.dumps(["LAND_DEED", "SITE_PLAN"]),
            99,
        ),
        (
            "APPR-ELEC-LOAD",
            "Industrial Power Feasibility & HT/LT Sanction",
            "DEPT-ELEC",
            "All",
            "Pre-Establishment",
            "All",
            "All",
            "Electricity Act 2003",
            15,
            5000.0,
            json.dumps(["Connected load calculation sheet", "Ownership proof", "Single line electrical diagram"]),
            json.dumps(["LAND_DEED", "PROJECT_REPORT"]),
            5,
        ),
        (
            "APPR-CTO-PCB",
            "Consent to Operate (CTO - Industrial)",
            "DEPT-PCB",
            "All",
            "Pre-Operation",
            "All",
            "All",
            "Water Act 1974 & Air Act 1981",
            30,
            20000.0,
            json.dumps(["CTE compliance report", "Effluent Treatment Plant (ETP) commissioning report", "Stack emission test results"]),
            json.dumps(["CTE_PCB", "PROJECT_REPORT"]),
            5,
        ),
        (
            "APPR-FINAL-FIRE",
            "Final Fire Safety Clearance Certificate",
            "DEPT-FIRE",
            "All",
            "Pre-Operation",
            "All",
            "All",
            "State Fire Prevention and Safety Act",
            15,
            5000.0,
            json.dumps(["Provisional Fire NOC", "Installation certificate of fire hydrants/alarms"]),
            json.dumps(["NOC_FIRE"]),
            1,
        ),
        (
            "APPR-BOILER-INSP",
            "Boiler Registration & Fitness Certificate",
            "DEPT-LAB",
            "Chemical",
            "Pre-Operation",
            "All",
            "All",
            "Indian Boilers Act 1923",
            20,
            10000.0,
            json.dumps(["Boiler manufacturer test certificate", "Steam pipeline layout"]),
            json.dumps(["PROJECT_REPORT"]),
            2,
        ),
    ]

    for item in approvals:
        conn.execute(
            """
            INSERT OR REPLACE INTO approval_catalogue (
                approval_id, name, department_id, sector, stage, project_size, location_type,
                statutory_act, max_sla_days, fee_inr, prerequisites_json, documents_required_json,
                validity_years, is_active, sample_disclaimer
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
            """,
            (*item, SAMPLE_DISCLAIMER),
        )


def _seed_schemes(conn: sqlite3.Connection) -> None:
    schemes = [
        (
            "SCHEME-CAP-SUB",
            "State Capital Investment Subsidy for MSMEs",
            "Department of Industries & Commerce",
            json.dumps(["Manufacturing", "Agro-processing", "Textile"]),
            json.dumps(["Micro", "Small"]),
            "Capital Subsidy",
            "20% capital subsidy on eligible plant and machinery up to a maximum limit of Rs. 50 Lakhs for setting up units in notified industrial clusters.",
            "Valid Udyam Registration, project operational within 18 months of sanction, commercial production started.",
            5000000.0,
            "2027-03-31",
        ),
        (
            "SCHEME-POW-CONC",
            "Green Industrial Power Tariff Subsidy",
            "Department of Power & Renewable Energy",
            json.dumps(["All"]),
            json.dumps(["Micro", "Small", "Medium"]),
            "Power Tariff Concession",
            "Reimbursement of Rs 1.50 per unit of electricity consumed for the first 5 years of commercial operations.",
            "Connected load >= 50 kVA, timely power bill payment history, installation of energy-efficient machinery.",
            1500000.0,
            "2026-12-31",
        ),
        (
            "SCHEME-STAMP-EX",
            "100% Industrial Land Stamp Duty Exemption",
            "Revenue & Registration Department",
            json.dumps(["All"]),
            json.dumps(["Micro", "Small", "Medium", "Large"]),
            "Stamp Duty Exemption",
            "100% waiver of stamp duty and registration fees on lease/purchase of land in Government and private industrial parks.",
            "Executed deed within designated industrial zone, industrial project ground-breaking within 12 months.",
            2500000.0,
            "2028-03-31",
        ),
        (
            "SCHEME-INT-SUB",
            "Technology Modernization Interest Subvention",
            "Directorate of MSME & Financial Services",
            json.dumps(["Manufacturing", "Chemical", "IT/ITES"]),
            json.dumps(["Small", "Medium"]),
            "Interest Subvention",
            "5% per annum interest subvention on institutional term loans for adoption of cleaner green technology and automation.",
            "Clean credit track record, project appraisal by scheduled commercial bank.",
            3000000.0,
            "2027-06-30",
        ),
    ]

    for item in schemes:
        conn.execute(
            """
            INSERT OR REPLACE INTO schemes (
                scheme_id, name, department_name, eligible_sectors_json, eligible_sizes_json,
                incentive_type, benefit_details, eligibility_criteria, max_subsidy_inr,
                application_deadline, sample_disclaimer, is_active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (*item, SAMPLE_DISCLAIMER),
        )


def _seed_demo_business_and_application(conn: sqlite3.Connection) -> None:
    now_str = datetime.now(timezone.utc).isoformat()

    # 1. Business Profile for demo applicant
    conn.execute(
        """
        INSERT OR REPLACE INTO business_profiles (
            profile_id, user_id, enterprise_name, entity_type, udyam_registration,
            pan, gstin, sector, project_size, investment_cr, turnover_cr,
            location_type, district, state, address, lat, lng
        )
        VALUES (
            'prof_apex_01', 'usr_applicant_01', 'Apex Precision Auto Engineering Pvt Ltd', 'Pvt Ltd',
            'UDYAM-MH-26-0012345', 'AAACA1234F', '27AAACA1234F1Z8', 'Manufacturing',
            'Small', 7.50, 18.20, 'Industrial Area', 'Pune', 'Maharashtra',
            'Plot No. B-42, Chakan Industrial Phase II, MIDC, Pune - 410501', 18.7606, 73.8567
        )
        """
    )

    # 2. Verified Data Store entries
    verified_data = [
        ("vs_pan", "usr_applicant_01", "prof_apex_01", "PAN", "AAACA1234F", "Income Tax Dept NSDL API"),
        ("vs_gst", "usr_applicant_01", "prof_apex_01", "GSTIN", "27AAACA1234F1Z8", "GSTN Common Portal API"),
        ("vs_udyam", "usr_applicant_01", "prof_apex_01", "UDYAM", "UDYAM-MH-26-0012345", "Ministry of MSME Udyam API"),
        ("vs_land", "usr_applicant_01", "prof_apex_01", "MIDC_PLOT_ALLOTMENT", "MIDC/CHAKAN/B-42/2025", "MIDC Land Records Single Sign-On"),
    ]
    for item in verified_data:
        conn.execute(
            """
            INSERT OR REPLACE INTO verified_data_store (store_id, user_id, profile_id, field_key, field_value, verified_by_source)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            item,
        )

    # 3. Documents in Vault
    documents = [
        ("doc_pan_01", "usr_applicant_01", "prof_apex_01", "PAN", "Enterprise PAN Card", "apex_pan_card.pdf", 145020, "application/pdf", "/storage/docs/apex_pan.pdf", "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08", 1, "2026-01-10T10:00:00Z", None),
        ("doc_udyam_01", "usr_applicant_01", "prof_apex_01", "UDYAM", "Udyam Registration Certificate", "udyam_cert.pdf", 212450, "application/pdf", "/storage/docs/udyam_cert.pdf", "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8", 1, "2026-01-10T10:05:00Z", None),
        ("doc_land_01", "usr_applicant_01", "prof_apex_01", "LAND_DEED", "MIDC Industrial Plot Lease Agreement", "midc_lease_deed.pdf", 1540890, "application/pdf", "/storage/docs/midc_lease.pdf", "4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a", 1, "2026-01-12T14:30:00Z", "2055-12-31T23:59:59Z"),
        ("doc_layout_01", "usr_applicant_01", "prof_apex_01", "FACTORY_LAYOUT", "Approved Factory Layout & Machine Plan", "factory_layout_rev3.pdf", 3450120, "application/pdf", "/storage/docs/layout_rev3.pdf", "ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d", 1, "2026-01-15T11:20:00Z", None),
        ("doc_site_01", "usr_applicant_01", "prof_apex_01", "SITE_PLAN", "Contour & Drainage Site Master Plan", "site_plan_signed.pdf", 2870190, "application/pdf", "/storage/docs/site_plan.pdf", "8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918", 1, "2026-01-15T11:25:00Z", None),
    ]
    for item in documents:
        conn.execute(
            """
            INSERT OR REPLACE INTO documents (
                document_id, user_id, profile_id, doc_type, title, file_name, file_size,
                mime_type, storage_path, hash_sha256, verified, verified_at, expires_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            item,
        )

    # 4. Composite Single-Window Application
    conn.execute(
        """
        INSERT OR REPLACE INTO applications (
            application_id, application_number, user_id, profile_id, status,
            submitted_at, target_completion_at, total_fee, overall_sla_days, remarks
        )
        VALUES (
            'app_2026_0042', 'APP-2026-0042', 'usr_applicant_01', 'prof_apex_01', 'UNDER_SCRUTINY',
            '2026-02-01T09:00:00Z', '2026-03-03T18:00:00Z', 35000.0, 30,
            'Composite Pre-Establishment Clearances for Precision Auto Components Unit'
        )
        """
    )

    # 5. Parallel Departmental Approvals for APP-2026-0042
    app_approvals = [
        (
            "app_appr_pcb_01",
            "app_2026_0042",
            "APPR-CTE-PCB",
            "DEPT-PCB",
            "IN_REVIEW",
            "usr_officer_pcb",
            "TECHNICAL_SCRUTINY",
            30,
            "2026-03-03T18:00:00Z",
            15000.0,
            25,
            3,
            0,
            0,
        ),
        (
            "app_appr_fire_01",
            "app_2026_0042",
            "APPR-FIRE-NOC",
            "DEPT-FIRE",
            "INSPECTION_PENDING",
            "usr_officer_fire",
            "JOINT_INSPECTION",
            21,
            "2026-02-22T18:00:00Z",
            8000.0,
            45,
            6,
            0,
            0,
        ),
        (
            "app_appr_lab_01",
            "app_2026_0042",
            "APPR-FACT-LIC",
            "DEPT-LAB",
            "QUERY_RAISED",
            None,
            "APPLICANT_CLARIFICATION",
            30,
            "2026-03-03T18:00:00Z",
            12000.0,
            65,
            12,
            1,
            1,
        ),
    ]

    for item in app_approvals:
        conn.execute(
            """
            INSERT OR REPLACE INTO application_approvals (
                app_approval_id, application_id, approval_id, department_id, status,
                assigned_officer_id, current_stage, sla_days, deadline_at, fee_paid,
                risk_score, days_inactive, query_count, loop_count
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            item,
        )

    # 6. Sample Query for Factory Licence
    conn.execute(
        """
        INSERT OR REPLACE INTO queries (
            query_id, app_approval_id, department_id, officer_id, query_text, status, raised_at
        )
        VALUES (
            'qry_fact_01', 'app_appr_lab_01', 'DEPT-LAB', 'usr_officer_ind',
            'Please clarify emergency egress staircase width in North-East bay as per Rule 66 of Maharashtra Factories Rules.',
            'OPEN', '2026-02-10T11:30:00Z'
        )
        """
    )

    # 7. Sample Joint Inspection
    conn.execute(
        """
        INSERT OR REPLACE INTO inspections (
            inspection_id, application_id, scheduled_date, time_slot, status,
            departments_json, officers_json, notes
        )
        VALUES (
            'insp_2026_01', 'app_2026_0042', '2026-03-05', 'Morning (10:00 - 13:00)', 'SCHEDULED',
            '["DEPT-FIRE", "DEPT-PCB", "DEPT-LAB"]',
            '["usr_officer_fire", "usr_officer_pcb"]',
            'Joint on-site verification of perimeter access roads, water storage reservoir, and ventilation ducting.'
        )
        """
    )

    # 8. Sample Compliance Tasks & Renewals
    compliance_tasks = [
        ("task_env_01", "usr_applicant_01", "Apex Precision Auto Engineering Pvt Ltd", "Hazardous Waste Annual Return (Form 4)", "Environmental", "State Pollution Control Board", "2026-06-30", "PENDING", "Annually", "Hazardous Waste Management Rules, 2016"),
        ("task_lab_01", "usr_applicant_01", "Apex Precision Auto Engineering Pvt Ltd", "Annual Return on Factory Employment & Hours", "Labour", "Directorate of Labour & Factories", "2026-04-15", "PENDING", "Annually", "Factories Act 1948 - Form 21"),
        ("task_fire_01", "usr_applicant_01", "Apex Precision Auto Engineering Pvt Ltd", "Biannual Fire Fighting Equipment Maintenance Certificate", "Factory Safety", "Fire & Emergency Services", "2026-05-31", "PENDING", "Half-Yearly", "National Building Code Part 4 Fire Safety"),
    ]
    for item in compliance_tasks:
        conn.execute(
            """
            INSERT OR REPLACE INTO compliance_tasks (
                task_id, user_id, enterprise_name, title, category, department_name, due_date, status, recurring_period, statutory_ref
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            item,
        )

    # 9. Sample Grievance
    conn.execute(
        """
        INSERT OR REPLACE INTO grievances (
            grievance_id, grievance_number, user_id, application_id, department_id,
            category, subject, description, level, status, filed_at, deadline_at
        )
        VALUES (
            'grv_2026_01', 'GRV-2026-0001', 'usr_applicant_01', 'app_2026_0042', 'DEPT-LAB',
            'Delay in Scrutiny', 'Scrutiny delayed beyond statutory SLA of 15 days for Factory Plan approval',
            'Application submitted on Feb 01. The clarification query was raised on Day 10, but response was submitted on Day 11 and file is still pending with scrutiny clerk.',
            1, 'OPEN', '2026-02-15T14:00:00Z', '2026-02-22T18:00:00Z'
        )
        """
    )

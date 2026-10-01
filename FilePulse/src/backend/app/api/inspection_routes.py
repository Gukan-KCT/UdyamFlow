from datetime import datetime, timezone
import json
import sqlite3
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request

from app.audit.audit_service import log_audit
from app.auth.dependencies import get_current_user, get_db, require_roles
from app.schemas.udyam_schemas import (
    InspectionReportSubmitRequest,
    InspectionResponse,
    InspectionScheduleRequest,
)

inspection_router = APIRouter(prefix="/api/inspections", tags=["Common Inspection Scheduling & Joint Reporting"])


@inspection_router.get("", response_model=list[InspectionResponse])
def list_inspections(
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = """
        SELECT i.*, bp.enterprise_name
        FROM inspections i
        JOIN applications a ON i.application_id = a.application_id
        JOIN business_profiles bp ON a.profile_id = bp.profile_id
    """
    params = []
    if current_user["role"] == "applicant":
        query += " WHERE a.user_id = ?"
        params.append(current_user["user_id"])

    query += " ORDER BY i.scheduled_date ASC"
    rows = conn.execute(query, params).fetchall()

    results = []
    for r in rows:
        depts = json.loads(r["departments_json"]) if r["departments_json"] else []
        officers = json.loads(r["officers_json"]) if r["officers_json"] else []
        findings = json.loads(r["findings_json"]) if r["findings_json"] else []
        results.append(
            InspectionResponse(
                inspection_id=r["inspection_id"],
                application_id=r["application_id"],
                enterprise_name=r["enterprise_name"],
                scheduled_date=r["scheduled_date"],
                time_slot=r["time_slot"],
                status=r["status"],
                departments=depts,
                officers=officers,
                notes=r["notes"],
                verdict=r["verdict"],
                report_text=r["report_text"],
                findings=findings,
                completed_at=r["completed_at"],
                created_at=r["created_at"],
            )
        )
    return results


@inspection_router.post("/schedule", response_model=InspectionResponse)
def schedule_common_inspection(
    req: InspectionScheduleRequest,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(require_roles("dept_officer", "senior_officer", "nodal_officer", "admin")),
):
    app = conn.execute("SELECT * FROM applications WHERE application_id = ?", (req.application_id,)).fetchone()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")

    insp_id = f"insp_{uuid.uuid4().hex[:10]}"
    now_str = datetime.now(timezone.utc).isoformat()
    depts_json = json.dumps(req.departments)
    officers_json = json.dumps([current_user["user_id"]])

    with conn:
        conn.execute(
            """
            INSERT INTO inspections (
                inspection_id, application_id, scheduled_date, time_slot, status,
                departments_json, officers_json, notes, created_at
            )
            VALUES (?, ?, ?, ?, 'SCHEDULED', ?, ?, ?, ?)
            """,
            (
                insp_id, req.application_id, req.scheduled_date, req.time_slot,
                depts_json, officers_json, req.notes, now_str,
            ),
        )

        # Update sub-approvals for the coordinated departments to JOINT_INSPECTION stage
        for dept in req.departments:
            conn.execute(
                """
                UPDATE application_approvals
                SET current_stage = 'JOINT_INSPECTION', status = 'INSPECTION_PENDING', updated_at = ?
                WHERE application_id = ? AND department_id = ?
                """,
                (now_str, req.application_id, dept),
            )

        log_audit(
            conn,
            actor_id=current_user["user_id"],
            actor_role=current_user["role"],
            action="COMMON_INSPECTION_SCHEDULED",
            entity_type="inspection",
            entity_id=insp_id,
            after_state={"scheduled_date": req.scheduled_date, "departments": req.departments},
            ip_address=request.client.host if request.client else None,
        )

    saved = conn.execute(
        """
        SELECT i.*, bp.enterprise_name
        FROM inspections i
        JOIN applications a ON i.application_id = a.application_id
        JOIN business_profiles bp ON a.profile_id = bp.profile_id
        WHERE i.inspection_id = ?
        """,
        (insp_id,),
    ).fetchone()

    return InspectionResponse(
        inspection_id=saved["inspection_id"],
        application_id=saved["application_id"],
        enterprise_name=saved["enterprise_name"],
        scheduled_date=saved["scheduled_date"],
        time_slot=saved["time_slot"],
        status=saved["status"],
        departments=req.departments,
        officers=[current_user["user_id"]],
        notes=saved["notes"],
        verdict=saved["verdict"],
        report_text=saved["report_text"],
        findings=[],
        completed_at=saved["completed_at"],
        created_at=saved["created_at"],
    )


@inspection_router.post("/{inspection_id}/report", response_model=InspectionResponse)
def submit_joint_inspection_report(
    inspection_id: str,
    req: InspectionReportSubmitRequest,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(require_roles("dept_officer", "senior_officer", "nodal_officer", "admin")),
):
    insp = conn.execute("SELECT * FROM inspections WHERE inspection_id = ?", (inspection_id,)).fetchone()
    if not insp:
        raise HTTPException(status_code=404, detail="Inspection not found")

    now_str = datetime.now(timezone.utc).isoformat()
    findings_json = json.dumps(req.findings)

    with conn:
        conn.execute(
            """
            UPDATE inspections
            SET status = 'COMPLETED', verdict = ?, report_text = ?, findings_json = ?, completed_at = ?
            WHERE inspection_id = ?
            """,
            (req.verdict, req.report_text, findings_json, now_str, inspection_id),
        )

        # Progress participating departmental approvals to FINAL_REVIEW
        depts = json.loads(insp["departments_json"]) if insp["departments_json"] else []
        for dept in depts:
            conn.execute(
                """
                UPDATE application_approvals
                SET current_stage = 'FINAL_REVIEW', updated_at = ?
                WHERE application_id = ? AND department_id = ?
                """,
                (now_str, insp["application_id"], dept),
            )

        log_audit(
            conn,
            actor_id=current_user["user_id"],
            actor_role=current_user["role"],
            action="JOINT_INSPECTION_REPORTED",
            entity_type="inspection",
            entity_id=inspection_id,
            after_state={"verdict": req.verdict, "findings": req.findings},
            ip_address=request.client.host if request.client else None,
        )

    updated = conn.execute(
        """
        SELECT i.*, bp.enterprise_name
        FROM inspections i
        JOIN applications a ON i.application_id = a.application_id
        JOIN business_profiles bp ON a.profile_id = bp.profile_id
        WHERE i.inspection_id = ?
        """,
        (inspection_id,),
    ).fetchone()

    return InspectionResponse(
        inspection_id=updated["inspection_id"],
        application_id=updated["application_id"],
        enterprise_name=updated["enterprise_name"],
        scheduled_date=updated["scheduled_date"],
        time_slot=updated["time_slot"],
        status=updated["status"],
        departments=json.loads(updated["departments_json"]),
        officers=json.loads(updated["officers_json"]),
        notes=updated["notes"],
        verdict=updated["verdict"],
        report_text=updated["report_text"],
        findings=req.findings,
        completed_at=updated["completed_at"],
        created_at=updated["created_at"],
    )

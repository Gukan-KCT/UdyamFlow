from datetime import datetime, timedelta, timezone
import sqlite3
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request

from app.audit.audit_service import log_audit
from app.auth.dependencies import get_current_user, get_db, require_roles
from app.schemas.udyam_schemas import (
    GrievanceCreateRequest,
    GrievanceResolveRequest,
    GrievanceResponse,
)

grievance_router = APIRouter(prefix="/api/grievances", tags=["Grievance Redressal & Escalation"])


@grievance_router.get("", response_model=list[GrievanceResponse])
def list_grievances(
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = """
        SELECT g.*, d.name as department_name
        FROM grievances g
        JOIN departments d ON g.department_id = d.department_id
    """
    params = []

    if current_user["role"] == "applicant":
        query += " WHERE g.user_id = ?"
        params.append(current_user["user_id"])
    elif current_user["role"] in ("dept_officer", "senior_officer") and current_user.get("department_id"):
        query += " WHERE g.department_id = ?"
        params.append(current_user["department_id"])

    query += " ORDER BY g.filed_at DESC"
    rows = conn.execute(query, params).fetchall()

    return [
        GrievanceResponse(
            grievance_id=r["grievance_id"],
            grievance_number=r["grievance_number"],
            user_id=r["user_id"],
            application_id=r["application_id"],
            department_id=r["department_id"],
            department_name=r["department_name"],
            category=r["category"],
            subject=r["subject"],
            description=r["description"],
            level=r["level"],
            status=r["status"],
            assigned_to=r["assigned_to"],
            filed_at=r["filed_at"],
            deadline_at=r["deadline_at"],
            resolved_at=r["resolved_at"],
            resolution_notes=r["resolution_notes"],
            escalated_at=r["escalated_at"],
        )
        for r in rows
    ]


@grievance_router.post("", response_model=GrievanceResponse)
def file_grievance(
    req: GrievanceCreateRequest,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    gid = f"grv_{uuid.uuid4().hex[:10]}"
    seq = conn.execute("SELECT COUNT(*) as cnt FROM grievances").fetchone()["cnt"] + 1
    g_num = f"GRV-2026-{seq:04d}"

    now = datetime.now(timezone.utc)
    deadline = (now + timedelta(days=7)).isoformat()
    now_str = now.isoformat()

    with conn:
        conn.execute(
            """
            INSERT INTO grievances (
                grievance_id, grievance_number, user_id, application_id, department_id,
                category, subject, description, level, status, filed_at, deadline_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 'OPEN', ?, ?)
            """,
            (
                gid, g_num, current_user["user_id"], req.application_id, req.department_id,
                req.category, req.subject, req.description, now_str, deadline,
            ),
        )

        log_audit(
            conn,
            actor_id=current_user["user_id"],
            actor_role=current_user["role"],
            action="GRIEVANCE_FILED",
            entity_type="grievance",
            entity_id=gid,
            after_state={"grievance_number": g_num, "subject": req.subject, "department_id": req.department_id},
            ip_address=request.client.host if request.client else None,
        )

    saved = conn.execute(
        """
        SELECT g.*, d.name as department_name
        FROM grievances g
        JOIN departments d ON g.department_id = d.department_id
        WHERE g.grievance_id = ?
        """,
        (gid,),
    ).fetchone()

    return GrievanceResponse(
        grievance_id=saved["grievance_id"],
        grievance_number=saved["grievance_number"],
        user_id=saved["user_id"],
        application_id=saved["application_id"],
        department_id=saved["department_id"],
        department_name=saved["department_name"],
        category=saved["category"],
        subject=saved["subject"],
        description=saved["description"],
        level=saved["level"],
        status=saved["status"],
        assigned_to=saved["assigned_to"],
        filed_at=saved["filed_at"],
        deadline_at=saved["deadline_at"],
        resolved_at=saved["resolved_at"],
        resolution_notes=saved["resolution_notes"],
        escalated_at=saved["escalated_at"],
    )


@grievance_router.post("/{grievance_id}/escalate", response_model=GrievanceResponse)
def escalate_grievance(
    grievance_id: str,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    grv = conn.execute("SELECT * FROM grievances WHERE grievance_id = ?", (grievance_id,)).fetchone()
    if not grv:
        raise HTTPException(status_code=404, detail="Grievance not found")

    new_level = min(int(grv["level"]) + 1, 3)
    now_str = datetime.now(timezone.utc).isoformat()

    with conn:
        conn.execute(
            """
            UPDATE grievances
            SET level = ?, status = 'ESCALATED', escalated_at = ?
            WHERE grievance_id = ?
            """,
            (new_level, now_str, grievance_id),
        )

        log_audit(
            conn,
            actor_id=current_user["user_id"],
            actor_role=current_user["role"],
            action="GRIEVANCE_ESCALATED",
            entity_type="grievance",
            entity_id=grievance_id,
            after_state={"new_level": new_level, "status": "ESCALATED"},
            ip_address=request.client.host if request.client else None,
        )

    updated = conn.execute(
        """
        SELECT g.*, d.name as department_name
        FROM grievances g
        JOIN departments d ON g.department_id = d.department_id
        WHERE g.grievance_id = ?
        """,
        (grievance_id,),
    ).fetchone()

    return GrievanceResponse(
        grievance_id=updated["grievance_id"],
        grievance_number=updated["grievance_number"],
        user_id=updated["user_id"],
        application_id=updated["application_id"],
        department_id=updated["department_id"],
        department_name=updated["department_name"],
        category=updated["category"],
        subject=updated["subject"],
        description=updated["description"],
        level=updated["level"],
        status=updated["status"],
        assigned_to=updated["assigned_to"],
        filed_at=updated["filed_at"],
        deadline_at=updated["deadline_at"],
        resolved_at=updated["resolved_at"],
        resolution_notes=updated["resolution_notes"],
        escalated_at=updated["escalated_at"],
    )


@grievance_router.post("/{grievance_id}/resolve", response_model=GrievanceResponse)
def resolve_grievance(
    grievance_id: str,
    req: GrievanceResolveRequest,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(require_roles("dept_officer", "senior_officer", "nodal_officer", "admin")),
):
    grv = conn.execute("SELECT * FROM grievances WHERE grievance_id = ?", (grievance_id,)).fetchone()
    if not grv:
        raise HTTPException(status_code=404, detail="Grievance not found")

    now_str = datetime.now(timezone.utc).isoformat()

    with conn:
        conn.execute(
            """
            UPDATE grievances
            SET status = ?, resolution_notes = ?, resolved_at = ?
            WHERE grievance_id = ?
            """,
            (req.status, req.resolution_notes, now_str, grievance_id),
        )

        log_audit(
            conn,
            actor_id=current_user["user_id"],
            actor_role=current_user["role"],
            action="GRIEVANCE_RESOLVED",
            entity_type="grievance",
            entity_id=grievance_id,
            after_state={"status": req.status, "resolution_notes": req.resolution_notes},
            ip_address=request.client.host if request.client else None,
        )

    updated = conn.execute(
        """
        SELECT g.*, d.name as department_name
        FROM grievances g
        JOIN departments d ON g.department_id = d.department_id
        WHERE g.grievance_id = ?
        """,
        (grievance_id,),
    ).fetchone()

    return GrievanceResponse(
        grievance_id=updated["grievance_id"],
        grievance_number=updated["grievance_number"],
        user_id=updated["user_id"],
        application_id=updated["application_id"],
        department_id=updated["department_id"],
        department_name=updated["department_name"],
        category=updated["category"],
        subject=updated["subject"],
        description=updated["description"],
        level=updated["level"],
        status=updated["status"],
        assigned_to=updated["assigned_to"],
        filed_at=updated["filed_at"],
        deadline_at=updated["deadline_at"],
        resolved_at=updated["resolved_at"],
        resolution_notes=updated["resolution_notes"],
        escalated_at=updated["escalated_at"],
    )

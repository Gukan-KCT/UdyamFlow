from datetime import datetime, timedelta, timezone
import json
import sqlite3
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.audit.audit_service import log_audit
from app.auth.dependencies import get_current_user, get_db, require_roles
from app.schemas.udyam_schemas import (
    ApplicationApprovalActionRequest,
    ApplicationApprovalResponse,
    ApplicationCreate,
    ApplicationResponse,
    QueryCreateRequest,
    QueryRespondRequest,
    QueryResponse,
)

application_router = APIRouter(prefix="/api/applications", tags=["Single-Window Applications & Workflows"])


@application_router.get("", response_model=list[ApplicationResponse])
def list_applications(
    status_filter: str | None = Query(default=None, alias="status"),
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["user_id"]
    role = current_user["role"]
    dept_id = current_user.get("department_id")

    query = """
        SELECT a.*, bp.enterprise_name
        FROM applications a
        JOIN business_profiles bp ON a.profile_id = bp.profile_id
        WHERE 1=1
    """
    params = []

    if role == "applicant":
        query += " AND a.user_id = ?"
        params.append(user_id)
    elif role in ("dept_officer", "senior_officer") and dept_id:
        query += """
            AND a.application_id IN (
                SELECT application_id FROM application_approvals WHERE department_id = ?
            )
        """
        params.append(dept_id)

    if status_filter:
        query += " AND a.status = ?"
        params.append(status_filter)

    query += " ORDER BY a.created_at DESC"
    rows = conn.execute(query, params).fetchall()

    results = []
    for r in rows:
        results.append(_hydrate_application(conn, r))
    return results


@application_router.get("/{application_id}", response_model=ApplicationResponse)
def get_application_details(
    application_id: str,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    row = conn.execute(
        """
        SELECT a.*, bp.enterprise_name
        FROM applications a
        JOIN business_profiles bp ON a.profile_id = bp.profile_id
        WHERE a.application_id = ?
        """,
        (application_id,),
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Application not found")

    # Tenant isolation check
    if current_user["role"] == "applicant" and row["user_id"] != current_user["user_id"]:
        raise HTTPException(status_code=403, detail="Unauthorized access to this application")

    return _hydrate_application(conn, row)


@application_router.post("", response_model=ApplicationResponse)
def create_application(
    req: ApplicationCreate,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not req.approval_ids:
        raise HTTPException(status_code=400, detail="Must select at least one approval to apply for.")

    profile = conn.execute(
        "SELECT * FROM business_profiles WHERE profile_id = ? AND user_id = ?",
        (req.profile_id, current_user["user_id"]),
    ).fetchone()

    if not profile:
        raise HTTPException(status_code=404, detail="Selected business profile not found or unauthorized.")

    # Fetch selected approvals from catalogue
    placeholders = ",".join("?" * len(req.approval_ids))
    catalogue_rows = conn.execute(
        f"SELECT * FROM approval_catalogue WHERE approval_id IN ({placeholders})",
        req.approval_ids,
    ).fetchall()

    if not catalogue_rows:
        raise HTTPException(status_code=400, detail="Invalid approval IDs selected.")

    app_id = f"app_{uuid.uuid4().hex[:10]}"
    seq_num = conn.execute("SELECT COUNT(*) as cnt FROM applications").fetchone()["cnt"] + 1
    app_num = f"APP-2026-{seq_num:04d}"

    total_fee = sum(float(r["fee_inr"]) for r in catalogue_rows)
    critical_sla = max(int(r["max_sla_days"]) for r in catalogue_rows)

    now = datetime.now(timezone.utc)
    target_completion = now + timedelta(days=critical_sla)
    now_str = now.isoformat()
    target_str = target_completion.isoformat()

    with conn:
        conn.execute(
            """
            INSERT INTO applications (
                application_id, application_number, user_id, profile_id, status,
                submitted_at, target_completion_at, total_fee, overall_sla_days, remarks,
                created_at, updated_at
            )
            VALUES (?, ?, ?, ?, 'SUBMITTED', ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                app_id, app_num, current_user["user_id"], req.profile_id,
                now_str, target_str, total_fee, critical_sla, req.remarks,
                now_str, now_str,
            ),
        )

        for c_row in catalogue_rows:
            sub_id = f"app_appr_{uuid.uuid4().hex[:10]}"
            sub_sla = int(c_row["max_sla_days"])
            sub_deadline = (now + timedelta(days=sub_sla)).isoformat()

            conn.execute(
                """
                INSERT INTO application_approvals (
                    app_approval_id, application_id, approval_id, department_id, status,
                    current_stage, sla_days, deadline_at, fee_paid, risk_score,
                    days_inactive, query_count, loop_count, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, 'IN_REVIEW', 'DOCUMENT_SCRUTINY', ?, ?, ?, 10, 0, 0, 0, ?, ?)
                """,
                (
                    sub_id, app_id, c_row["approval_id"], c_row["department_id"],
                    sub_sla, sub_deadline, float(c_row["fee_inr"]),
                    now_str, now_str,
                ),
            )

        log_audit(
            conn,
            actor_id=current_user["user_id"],
            actor_role=current_user["role"],
            action="APPLICATION_SUBMITTED",
            entity_type="application",
            entity_id=app_id,
            after_state={"application_number": app_num, "total_fee": total_fee, "approvals_count": len(catalogue_rows)},
            ip_address=request.client.host if request.client else None,
        )

    saved = conn.execute(
        """
        SELECT a.*, bp.enterprise_name
        FROM applications a
        JOIN business_profiles bp ON a.profile_id = bp.profile_id
        WHERE a.application_id = ?
        """,
        (app_id,),
    ).fetchone()
    return _hydrate_application(conn, saved)


@application_router.post("/{application_id}/approvals/{app_approval_id}/action", response_model=ApplicationResponse)
def execute_approval_action(
    application_id: str,
    app_approval_id: str,
    req: ApplicationApprovalActionRequest,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(require_roles("dept_officer", "senior_officer", "nodal_officer", "admin")),
):
    sub = conn.execute(
        "SELECT * FROM application_approvals WHERE app_approval_id = ? AND application_id = ?",
        (app_approval_id, application_id),
    ).fetchone()

    if not sub:
        raise HTTPException(status_code=404, detail="Sub-approval not found for this application")

    # If department officer, check department matching
    if current_user["role"] in ("dept_officer", "senior_officer") and current_user.get("department_id"):
        if sub["department_id"] != current_user["department_id"]:
            raise HTTPException(status_code=403, detail="Officer not authorized for this department's approval.")

    before_state = dict(sub)
    now_str = datetime.now(timezone.utc).isoformat()

    with conn:
        if req.action == "ASSIGN":
            officer_id = req.assigned_officer_id or current_user["user_id"]
            conn.execute(
                """
                UPDATE application_approvals
                SET assigned_officer_id = ?, updated_at = ?
                WHERE app_approval_id = ?
                """,
                (officer_id, now_str, app_approval_id),
            )
        elif req.action == "MOVE_STAGE":
            conn.execute(
                """
                UPDATE application_approvals
                SET current_stage = ?, updated_at = ?
                WHERE app_approval_id = ?
                """,
                (req.next_stage or "INSPECTION_PENDING", now_str, app_approval_id),
            )
        elif req.action == "APPROVE":
            conn.execute(
                """
                UPDATE application_approvals
                SET status = 'APPROVED', current_stage = 'COMPLETED', approved_at = ?, updated_at = ?
                WHERE app_approval_id = ?
                """,
                (now_str, now_str, app_approval_id),
            )
            _generate_certificate_for_approval(conn, app_approval_id, application_id)
        elif req.action == "REJECT":
            conn.execute(
                """
                UPDATE application_approvals
                SET status = 'REJECTED', rejection_reason = ?, updated_at = ?
                WHERE app_approval_id = ?
                """,
                (req.reason or "Statutory requirements not satisfied upon scrutiny.", now_str, app_approval_id),
            )
            conn.execute(
                "UPDATE applications SET status = 'REJECTED', updated_at = ? WHERE application_id = ?",
                (now_str, application_id),
            )

        # Check if all sub-approvals are now approved
        all_subs = conn.execute(
            "SELECT status FROM application_approvals WHERE application_id = ?",
            (application_id,),
        ).fetchall()
        if all_subs and all(s["status"] == "APPROVED" for s in all_subs):
            conn.execute(
                "UPDATE applications SET status = 'APPROVED', completed_at = ?, updated_at = ? WHERE application_id = ?",
                (now_str, now_str, application_id),
            )

        log_audit(
            conn,
            actor_id=current_user["user_id"],
            actor_role=current_user["role"],
            action=f"APPROVAL_{req.action}",
            entity_type="application_approval",
            entity_id=app_approval_id,
            before_state=before_state,
            after_state={"action": req.action, "reason": req.reason},
            reason=req.reason,
            ip_address=request.client.host if request.client else None,
        )

    updated_app = conn.execute(
        """
        SELECT a.*, bp.enterprise_name
        FROM applications a
        JOIN business_profiles bp ON a.profile_id = bp.profile_id
        WHERE a.application_id = ?
        """,
        (application_id,),
    ).fetchone()
    return _hydrate_application(conn, updated_app)


# Queries API
@application_router.get("/{application_id}/queries", response_model=list[QueryResponse])
def get_application_queries(
    application_id: str,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = """
        SELECT q.*, d.name as department_name, u.full_name as officer_name
        FROM queries q
        JOIN application_approvals aa ON q.app_approval_id = aa.app_approval_id
        JOIN departments d ON q.department_id = d.department_id
        LEFT JOIN users u ON q.officer_id = u.user_id
        WHERE aa.application_id = ?
        ORDER BY q.raised_at DESC
    """
    rows = conn.execute(query, (application_id,)).fetchall()
    results = []
    for r in rows:
        docs = json.loads(r["response_doc_ids_json"]) if r["response_doc_ids_json"] else []
        results.append(
            QueryResponse(
                query_id=r["query_id"],
                app_approval_id=r["app_approval_id"],
                department_id=r["department_id"],
                department_name=r["department_name"],
                officer_id=r["officer_id"],
                officer_name=r["officer_name"],
                query_text=r["query_text"],
                status=r["status"],
                raised_at=r["raised_at"],
                responded_at=r["responded_at"],
                response_text=r["response_text"],
                response_doc_ids=docs,
            )
        )
    return results


@application_router.post("/queries", response_model=QueryResponse)
def raise_clarification_query(
    req: QueryCreateRequest,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(require_roles("dept_officer", "senior_officer", "admin")),
):
    sub = conn.execute(
        "SELECT * FROM application_approvals WHERE app_approval_id = ?",
        (req.app_approval_id,),
    ).fetchone()
    if not sub:
        raise HTTPException(status_code=404, detail="Sub-approval not found")

    qid = f"qry_{uuid.uuid4().hex[:10]}"
    now_str = datetime.now(timezone.utc).isoformat()

    with conn:
        conn.execute(
            """
            INSERT INTO queries (query_id, app_approval_id, department_id, officer_id, query_text, status, raised_at)
            VALUES (?, ?, ?, ?, ?, 'OPEN', ?)
            """,
            (qid, req.app_approval_id, sub["department_id"], current_user["user_id"], req.query_text, now_str),
        )
        conn.execute(
            """
            UPDATE application_approvals
            SET status = 'QUERY_RAISED', query_count = query_count + 1, loop_count = loop_count + 1, updated_at = ?
            WHERE app_approval_id = ?
            """,
            (now_str, req.app_approval_id),
        )
        conn.execute(
            "UPDATE applications SET status = 'QUERY_RAISED', updated_at = ? WHERE application_id = ?",
            (now_str, sub["application_id"]),
        )
        log_audit(
            conn,
            actor_id=current_user["user_id"],
            actor_role=current_user["role"],
            action="QUERY_RAISED",
            entity_type="query",
            entity_id=qid,
            after_state={"query_text": req.query_text, "app_approval_id": req.app_approval_id},
            ip_address=request.client.host if request.client else None,
        )

    saved = conn.execute(
        """
        SELECT q.*, d.name as department_name, u.full_name as officer_name
        FROM queries q
        JOIN departments d ON q.department_id = d.department_id
        LEFT JOIN users u ON q.officer_id = u.user_id
        WHERE q.query_id = ?
        """,
        (qid,),
    ).fetchone()

    return QueryResponse(
        query_id=saved["query_id"],
        app_approval_id=saved["app_approval_id"],
        department_id=saved["department_id"],
        department_name=saved["department_name"],
        officer_id=saved["officer_id"],
        officer_name=saved["officer_name"],
        query_text=saved["query_text"],
        status=saved["status"],
        raised_at=saved["raised_at"],
        responded_at=saved["responded_at"],
        response_text=saved["response_text"],
        response_doc_ids=[],
    )


@application_router.post("/queries/{query_id}/respond", response_model=QueryResponse)
def respond_to_query(
    query_id: str,
    req: QueryRespondRequest,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    qry = conn.execute("SELECT * FROM queries WHERE query_id = ?", (query_id,)).fetchone()
    if not qry:
        raise HTTPException(status_code=404, detail="Query not found")

    now_str = datetime.now(timezone.utc).isoformat()
    docs_json = json.dumps(req.response_doc_ids)

    with conn:
        conn.execute(
            """
            UPDATE queries
            SET status = 'RESPONDED', responded_at = ?, response_text = ?, response_doc_ids_json = ?
            WHERE query_id = ?
            """,
            (now_str, req.response_text, docs_json, query_id),
        )
        conn.execute(
            """
            UPDATE application_approvals
            SET status = 'QUERY_RESPONDED', current_stage = 'DOCUMENT_SCRUTINY', updated_at = ?
            WHERE app_approval_id = ?
            """,
            (now_str, qry["app_approval_id"]),
        )

        sub_app = conn.execute(
            "SELECT application_id FROM application_approvals WHERE app_approval_id = ?",
            (qry["app_approval_id"],),
        ).fetchone()
        if sub_app:
            still_raised = conn.execute(
                "SELECT COUNT(*) as cnt FROM application_approvals WHERE application_id = ? AND status = 'QUERY_RAISED'",
                (sub_app["application_id"],),
            ).fetchone()["cnt"]
            if still_raised == 0:
                conn.execute(
                    "UPDATE applications SET status = 'UNDER_SCRUTINY', updated_at = ? WHERE application_id = ?",
                    (now_str, sub_app["application_id"]),
                )
        log_audit(
            conn,
            actor_id=current_user["user_id"],
            actor_role=current_user["role"],
            action="QUERY_RESPONDED",
            entity_type="query",
            entity_id=query_id,
            after_state={"response_text": req.response_text, "response_docs": req.response_doc_ids},
            ip_address=request.client.host if request.client else None,
        )

    updated = conn.execute(
        """
        SELECT q.*, d.name as department_name, u.full_name as officer_name
        FROM queries q
        JOIN departments d ON q.department_id = d.department_id
        LEFT JOIN users u ON q.officer_id = u.user_id
        WHERE q.query_id = ?
        """,
        (query_id,),
    ).fetchone()

    return QueryResponse(
        query_id=updated["query_id"],
        app_approval_id=updated["app_approval_id"],
        department_id=updated["department_id"],
        department_name=updated["department_name"],
        officer_id=updated["officer_id"],
        officer_name=updated["officer_name"],
        query_text=updated["query_text"],
        status=updated["status"],
        raised_at=updated["raised_at"],
        responded_at=updated["responded_at"],
        response_text=updated["response_text"],
        response_doc_ids=req.response_doc_ids,
    )


def _hydrate_application(conn: sqlite3.Connection, row: sqlite3.Row) -> ApplicationResponse:
    app_id = row["application_id"]
    sub_rows = conn.execute(
        """
        SELECT aa.*, ac.name as approval_name, d.name as department_name, u.full_name as assigned_officer_name
        FROM application_approvals aa
        JOIN approval_catalogue ac ON aa.approval_id = ac.approval_id
        JOIN departments d ON aa.department_id = d.department_id
        LEFT JOIN users u ON aa.assigned_officer_id = u.user_id
        WHERE aa.application_id = ?
        ORDER BY aa.deadline_at ASC
        """,
        (app_id,),
    ).fetchall()

    approvals = []
    for s in sub_rows:
        approvals.append(
            ApplicationApprovalResponse(
                app_approval_id=s["app_approval_id"],
                application_id=s["application_id"],
                approval_id=s["approval_id"],
                approval_name=s["approval_name"],
                department_id=s["department_id"],
                department_name=s["department_name"],
                status=s["status"],
                assigned_officer_id=s["assigned_officer_id"],
                assigned_officer_name=s["assigned_officer_name"],
                current_stage=s["current_stage"],
                sla_days=s["sla_days"],
                deadline_at=s["deadline_at"],
                fee_paid=s["fee_paid"],
                risk_score=s["risk_score"],
                days_inactive=s["days_inactive"],
                query_count=s["query_count"],
                loop_count=s["loop_count"],
                rejection_reason=s["rejection_reason"],
                approved_at=s["approved_at"],
            )
        )

    return ApplicationResponse(
        application_id=row["application_id"],
        application_number=row["application_number"],
        user_id=row["user_id"],
        profile_id=row["profile_id"],
        enterprise_name=row["enterprise_name"],
        status=row["status"],
        submitted_at=row["submitted_at"],
        target_completion_at=row["target_completion_at"],
        completed_at=row["completed_at"],
        total_fee=row["total_fee"],
        overall_sla_days=row["overall_sla_days"],
        remarks=row["remarks"],
        approvals=approvals,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _generate_certificate_for_approval(conn: sqlite3.Connection, app_approval_id: str, application_id: str):
    sub = conn.execute(
        """
        SELECT aa.*, ac.name as approval_name, ac.validity_years, d.name as department_name,
               u.full_name as applicant_name, bp.enterprise_name
        FROM application_approvals aa
        JOIN approval_catalogue ac ON aa.approval_id = ac.approval_id
        JOIN departments d ON aa.department_id = d.department_id
        JOIN applications a ON aa.application_id = a.application_id
        JOIN users u ON a.user_id = u.user_id
        JOIN business_profiles bp ON a.profile_id = bp.profile_id
        WHERE aa.app_approval_id = ?
        """,
        (app_approval_id,),
    ).fetchone()

    if not sub:
        return

    cert_id = f"cert_{uuid.uuid4().hex[:10]}"
    cert_num = f"CERT-{datetime.now().year}-{uuid.uuid4().hex[:8].upper()}"
    now = datetime.now(timezone.utc)
    issue_date = now.isoformat()
    valid_until = (now + timedelta(days=365 * sub["validity_years"])).isoformat()
    qr_code = f"UDYAM-VERIFY-{cert_num}"
    sig_hash = uuid.uuid5(uuid.NAMESPACE_DNS, f"{cert_num}:{sub['approval_name']}:{issue_date}").hex

    conn.execute(
        """
        INSERT OR REPLACE INTO certificates (
            certificate_id, app_approval_id, certificate_number, approval_name,
            department_name, issued_to, enterprise_name, issue_date, valid_until,
            qr_verification_code, digital_signature_hash, status, pdf_url
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'VALID', ?)
        """,
        (
            cert_id, app_approval_id, cert_num, sub["approval_name"],
            sub["department_name"], sub["applicant_name"], sub["enterprise_name"],
            issue_date, valid_until, qr_code, sig_hash, f"/api/certificates/{cert_id}/download",
        ),
    )

    # Automatically register an upcoming renewal in renewals table
    ren_id = f"ren_{uuid.uuid4().hex[:10]}"
    conn.execute(
        """
        INSERT OR REPLACE INTO renewals (
            renewal_id, certificate_id, user_id, approval_id, current_expiry, reminder_days, renewal_status
        )
        VALUES (?, ?, ?, ?, ?, 30, 'UPCOMING')
        """,
        (ren_id, cert_id, sub["assigned_officer_id"] or "usr_applicant_01", sub["approval_id"], valid_until),
    )

from datetime import datetime, timezone
import json
import sqlite3
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request

from app.audit.audit_service import log_audit
from app.auth.dependencies import get_current_user, get_db
from app.schemas.udyam_schemas import (
    CertificateResponse,
    ComplianceTaskResponse,
    RenewalResponse,
    SchemeApplicationRequest,
    SchemeApplicationResponse,
    SchemeResponse,
)

compliance_router = APIRouter(prefix="/api/compliance", tags=["Compliance Calendar, Renewals & Schemes"])
certificate_router = APIRouter(prefix="/api/certificates", tags=["Verifiable Digital Certificates"])
schemes_router = APIRouter(prefix="/api/schemes", tags=["Incentives & Subsidies"])

SAMPLE_DISCLAIMER = "SAMPLE / ILLUSTRATIVE - VERIFY AGAINST OFFICIAL SCHEME GUIDELINES"


# Compliance Tasks
@compliance_router.get("/tasks", response_model=list[ComplianceTaskResponse])
def get_compliance_tasks(
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    rows = conn.execute(
        "SELECT * FROM compliance_tasks WHERE user_id = ? ORDER BY due_date ASC",
        (current_user["user_id"],),
    ).fetchall()

    return [
        ComplianceTaskResponse(
            task_id=r["task_id"],
            user_id=r["user_id"],
            enterprise_name=r["enterprise_name"],
            title=r["title"],
            category=r["category"],
            department_name=r["department_name"],
            due_date=r["due_date"],
            status=r["status"],
            recurring_period=r["recurring_period"],
            statutory_ref=r["statutory_ref"],
            completed_at=r["completed_at"],
        )
        for r in rows
    ]


@compliance_router.post("/tasks/{task_id}/complete", response_model=ComplianceTaskResponse)
def complete_compliance_task(
    task_id: str,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    task = conn.execute("SELECT * FROM compliance_tasks WHERE task_id = ?", (task_id,)).fetchone()
    if not task:
        raise HTTPException(status_code=404, detail="Compliance task not found")

    now_str = datetime.now(timezone.utc).isoformat()

    with conn:
        conn.execute(
            "UPDATE compliance_tasks SET status = 'COMPLETED', completed_at = ? WHERE task_id = ?",
            (now_str, task_id),
        )
        log_audit(
            conn,
            actor_id=current_user["user_id"],
            actor_role=current_user["role"],
            action="COMPLIANCE_TASK_COMPLETED",
            entity_type="compliance_task",
            entity_id=task_id,
            after_state={"status": "COMPLETED", "completed_at": now_str},
            ip_address=request.client.host if request.client else None,
        )

    updated = conn.execute("SELECT * FROM compliance_tasks WHERE task_id = ?", (task_id,)).fetchone()
    return ComplianceTaskResponse(
        task_id=updated["task_id"],
        user_id=updated["user_id"],
        enterprise_name=updated["enterprise_name"],
        title=updated["title"],
        category=updated["category"],
        department_name=updated["department_name"],
        due_date=updated["due_date"],
        status=updated["status"],
        recurring_period=updated["recurring_period"],
        statutory_ref=updated["statutory_ref"],
        completed_at=updated["completed_at"],
    )


# Renewals
@compliance_router.get("/renewals", response_model=list[RenewalResponse])
def get_upcoming_renewals(
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = """
        SELECT r.*, c.certificate_number, c.approval_name
        FROM renewals r
        JOIN certificates c ON r.certificate_id = c.certificate_id
        WHERE r.user_id = ?
        ORDER BY r.current_expiry ASC
    """
    rows = conn.execute(query, (current_user["user_id"],)).fetchall()

    return [
        RenewalResponse(
            renewal_id=r["renewal_id"],
            certificate_id=r["certificate_id"],
            certificate_number=r["certificate_number"],
            approval_name=r["approval_name"],
            current_expiry=r["current_expiry"],
            reminder_days=r["reminder_days"],
            renewal_status=r["renewal_status"],
            renewal_application_id=r["renewal_application_id"],
        )
        for r in rows
    ]


# Certificates & Public Verification
@certificate_router.get("/{certificate_id}", response_model=CertificateResponse)
def get_certificate(
    certificate_id: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    cert = conn.execute("SELECT * FROM certificates WHERE certificate_id = ?", (certificate_id,)).fetchone()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")

    return CertificateResponse(
        certificate_id=cert["certificate_id"],
        app_approval_id=cert["app_approval_id"],
        certificate_number=cert["certificate_number"],
        approval_name=cert["approval_name"],
        department_name=cert["department_name"],
        issued_to=cert["issued_to"],
        enterprise_name=cert["enterprise_name"],
        issue_date=cert["issue_date"],
        valid_until=cert["valid_until"],
        qr_verification_code=cert["qr_verification_code"],
        digital_signature_hash=cert["digital_signature_hash"],
        status=cert["status"],
        pdf_url=cert["pdf_url"],
    )


@certificate_router.get("/approval/{app_approval_id}", response_model=CertificateResponse)
def get_certificate_by_approval(
    app_approval_id: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    cert = conn.execute(
        "SELECT * FROM certificates WHERE app_approval_id = ? ORDER BY issue_date DESC LIMIT 1",
        (app_approval_id,),
    ).fetchone()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found for this approval")

    return CertificateResponse(
        certificate_id=cert["certificate_id"],
        app_approval_id=cert["app_approval_id"],
        certificate_number=cert["certificate_number"],
        approval_name=cert["approval_name"],
        department_name=cert["department_name"],
        issued_to=cert["issued_to"],
        enterprise_name=cert["enterprise_name"],
        issue_date=cert["issue_date"],
        valid_until=cert["valid_until"],
        qr_verification_code=cert["qr_verification_code"],
        digital_signature_hash=cert["digital_signature_hash"],
        status=cert["status"],
        pdf_url=cert["pdf_url"],
    )


@certificate_router.get("/verify/{qr_code}")
def verify_certificate_public(
    qr_code: str,
    conn: sqlite3.Connection = Depends(get_db),
):
    """Public portal verification of digitally signed statutory approval certificates."""
    cert = conn.execute(
        "SELECT * FROM certificates WHERE qr_verification_code = ? OR certificate_number = ?",
        (qr_code, qr_code),
    ).fetchone()

    if not cert:
        return {
            "valid": False,
            "message": "Certificate not found or unverified in the National Single Window Registry.",
        }

    return {
        "valid": True,
        "status": cert["status"],
        "certificate_number": cert["certificate_number"],
        "approval_name": cert["approval_name"],
        "department_name": cert["department_name"],
        "enterprise_name": cert["enterprise_name"],
        "issued_to": cert["issued_to"],
        "issue_date": cert["issue_date"],
        "valid_until": cert["valid_until"],
        "digital_signature_hash": cert["digital_signature_hash"],
        "verification_status": "AUTHENTIC & VERIFIED STATUTORY CLEARANCE",
    }


# Schemes & Subsidies
@schemes_router.get("", response_model=list[SchemeResponse])
def list_schemes(conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute("SELECT * FROM schemes WHERE is_active = 1").fetchall()
    results = []
    for r in rows:
        sectors = json.loads(r["eligible_sectors_json"]) if r["eligible_sectors_json"] else []
        sizes = json.loads(r["eligible_sizes_json"]) if r["eligible_sizes_json"] else []
        results.append(
            SchemeResponse(
                scheme_id=r["scheme_id"],
                name=r["name"],
                department_name=r["department_name"],
                eligible_sectors=sectors,
                eligible_sizes=sizes,
                incentive_type=r["incentive_type"],
                benefit_details=r["benefit_details"],
                eligibility_criteria=r["eligibility_criteria"],
                max_subsidy_inr=r["max_subsidy_inr"],
                application_deadline=r["application_deadline"],
                sample_disclaimer=r["sample_disclaimer"] or SAMPLE_DISCLAIMER,
            )
        )
    return results


@schemes_router.post("/apply", response_model=SchemeApplicationResponse)
def apply_for_scheme(
    req: SchemeApplicationRequest,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    scheme = conn.execute("SELECT * FROM schemes WHERE scheme_id = ?", (req.scheme_id,)).fetchone()
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")

    profile = conn.execute("SELECT * FROM business_profiles WHERE profile_id = ?", (req.profile_id,)).fetchone()
    if not profile:
        raise HTTPException(status_code=404, detail="Business profile not found")

    s_app_id = f"sch_app_{uuid.uuid4().hex[:10]}"
    now_str = datetime.now(timezone.utc).isoformat()

    with conn:
        conn.execute(
            """
            INSERT INTO scheme_applications (
                scheme_app_id, scheme_id, user_id, profile_id, status,
                claim_amount, approved_amount, submitted_at, remarks
            )
            VALUES (?, ?, ?, ?, 'SUBMITTED', ?, 0.0, ?, ?)
            """,
            (s_app_id, req.scheme_id, current_user["user_id"], req.profile_id, req.claim_amount, now_str, req.remarks),
        )

        log_audit(
            conn,
            actor_id=current_user["user_id"],
            actor_role=current_user["role"],
            action="SCHEME_APPLICATION_SUBMITTED",
            entity_type="scheme_application",
            entity_id=s_app_id,
            after_state={"scheme_name": scheme["name"], "claim_amount": req.claim_amount},
            ip_address=request.client.host if request.client else None,
        )

    return SchemeApplicationResponse(
        scheme_app_id=s_app_id,
        scheme_id=scheme["scheme_id"],
        scheme_name=scheme["name"],
        user_id=current_user["user_id"],
        enterprise_name=profile["enterprise_name"],
        status="SUBMITTED",
        claim_amount=req.claim_amount,
        approved_amount=0.0,
        submitted_at=now_str,
        reviewed_at=None,
        remarks=req.remarks,
    )


@schemes_router.get("/my-applications", response_model=list[SchemeApplicationResponse])
def get_my_scheme_applications(
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    query = """
        SELECT sa.*, s.name as scheme_name, bp.enterprise_name
        FROM scheme_applications sa
        JOIN schemes s ON sa.scheme_id = s.scheme_id
        JOIN business_profiles bp ON sa.profile_id = bp.profile_id
        WHERE sa.user_id = ?
        ORDER BY sa.submitted_at DESC
    """
    rows = conn.execute(query, (current_user["user_id"],)).fetchall()

    return [
        SchemeApplicationResponse(
            scheme_app_id=r["scheme_app_id"],
            scheme_id=r["scheme_id"],
            scheme_name=r["scheme_name"],
            user_id=r["user_id"],
            enterprise_name=r["enterprise_name"],
            status=r["status"],
            claim_amount=r["claim_amount"],
            approved_amount=r["approved_amount"],
            submitted_at=r["submitted_at"],
            reviewed_at=r["reviewed_at"],
            remarks=r["remarks"],
        )
        for r in rows
    ]

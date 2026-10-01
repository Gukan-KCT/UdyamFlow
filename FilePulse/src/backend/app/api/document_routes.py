from datetime import datetime, timezone
import hashlib
import json
import sqlite3
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request

from app.audit.audit_service import log_audit
from app.auth.dependencies import get_current_user, get_db
from app.schemas.udyam_schemas import (
    DocumentResponse,
    DocumentUploadRequest,
    DocumentValidationItem,
    PreValidateRequest,
    PreValidateResponse,
)

document_router = APIRouter(prefix="/api/documents", tags=["Document Vault & Pre-Validation"])

DOC_DISPLAY_NAMES = {
    "PAN": "Enterprise / Proprietor PAN Card",
    "AADHAAR": "Authorized Signatory Aadhaar Card",
    "LAND_DEED": "Land Ownership Deed / Registered Lease Agreement",
    "SITE_PLAN": "Demarcated Site Master Plan with GPS Coordinates",
    "PROJECT_REPORT": "Detailed Project Feasibility & Engineering Report",
    "FACTORY_LAYOUT": "Factory Machinery Layout & Emergency Evacuation Plan",
    "CTE_PCB": "Consent to Establish (CTE) Compliance & ETP Design",
    "NOC_FIRE": "Provisional Fire NOC & Hydrant Pressure Specifications",
}


@document_router.get("/vault", response_model=list[DocumentResponse])
def get_document_vault(
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    rows = conn.execute(
        """
        SELECT * FROM documents
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (current_user["user_id"],),
    ).fetchall()

    return [
        DocumentResponse(
            document_id=r["document_id"],
            user_id=r["user_id"],
            profile_id=r["profile_id"],
            doc_type=r["doc_type"],
            title=r["title"],
            file_name=r["file_name"],
            file_size=r["file_size"],
            mime_type=r["mime_type"],
            storage_path=r["storage_path"],
            hash_sha256=r["hash_sha256"],
            verified=bool(r["verified"]),
            verified_at=r["verified_at"],
            expires_at=r["expires_at"],
            created_at=r["created_at"],
        )
        for r in rows
    ]


@document_router.post("/upload", response_model=DocumentResponse)
def upload_document(
    req: DocumentUploadRequest,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if req.file_size > 15 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds maximum statutory limit of 15MB")

    allowed_mimes = ["application/pdf", "image/jpeg", "image/png"]
    if req.mime_type not in allowed_mimes:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format '{req.mime_type}'. Only PDF, JPEG, and PNG are accepted.",
        )

    doc_id = f"doc_{uuid.uuid4().hex[:10]}"
    now_str = datetime.now(timezone.utc).isoformat()
    mock_hash = hashlib.sha256(f"{req.file_name}:{now_str}".encode("utf-8")).hexdigest()

    with conn:
        conn.execute(
            """
            INSERT INTO documents (
                document_id, user_id, profile_id, doc_type, title, file_name,
                file_size, mime_type, storage_path, hash_sha256, verified, verified_at, expires_at, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """,
            (
                doc_id, current_user["user_id"], req.profile_id, req.doc_type, req.title,
                req.file_name, req.file_size, req.mime_type, req.storage_path, mock_hash,
                now_str, req.expires_at, now_str,
            ),
        )

        version_id = f"ver_{uuid.uuid4().hex[:10]}"
        conn.execute(
            """
            INSERT INTO document_versions (
                version_id, document_id, version_num, storage_path, file_size, hash_sha256, uploaded_by, uploaded_at
            )
            VALUES (?, ?, 1, ?, ?, ?, ?, ?)
            """,
            (version_id, doc_id, req.storage_path, req.file_size, mock_hash, current_user["user_id"], now_str),
        )

        log_audit(
            conn,
            actor_id=current_user["user_id"],
            actor_role=current_user["role"],
            action="DOCUMENT_UPLOADED",
            entity_type="document",
            entity_id=doc_id,
            after_state={"doc_type": req.doc_type, "title": req.title, "file_name": req.file_name},
            ip_address=request.client.host if request.client else None,
        )

    return DocumentResponse(
        document_id=doc_id,
        user_id=current_user["user_id"],
        profile_id=req.profile_id,
        doc_type=req.doc_type,
        title=req.title,
        file_name=req.file_name,
        file_size=req.file_size,
        mime_type=req.mime_type,
        storage_path=req.storage_path,
        hash_sha256=mock_hash,
        verified=True,
        verified_at=now_str,
        expires_at=req.expires_at,
        created_at=now_str,
    )


@document_router.post("/pre-validate", response_model=PreValidateResponse)
def pre_validate_application(
    req: PreValidateRequest,
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Deterministic rule engine that validates all document and data prerequisites
    prior to application submission.
    Prevents departmental rejections and avoids repetitive query loops.
    """
    if not req.approval_ids:
        return PreValidateResponse(
            is_valid=False,
            score=0,
            validations=[],
            missing_required_docs=[],
            autofill_suggestions={},
            readiness_summary="Please select at least one approval to validate readiness.",
        )

    placeholders = ",".join("?" * len(req.approval_ids))
    catalogue_rows = conn.execute(
        f"SELECT * FROM approval_catalogue WHERE approval_id IN ({placeholders})",
        req.approval_ids,
    ).fetchall()

    # Collect all required documents across selected approvals
    required_docs_set = set()
    for row in catalogue_rows:
        docs = json.loads(row["documents_required_json"]) if row["documents_required_json"] else []
        required_docs_set.update(docs)

    # Fetch existing vault documents for user
    vault_docs = conn.execute(
        "SELECT doc_type, file_name, expires_at FROM documents WHERE user_id = ?",
        (current_user["user_id"],),
    ).fetchall()
    vault_map = {d["doc_type"]: d for d in vault_docs}

    validations: list[DocumentValidationItem] = []
    missing_docs: list[str] = []
    now = datetime.now(timezone.utc)

    for doc_type in sorted(required_docs_set):
        display_name = DOC_DISPLAY_NAMES.get(doc_type, doc_type)
        if doc_type in vault_map:
            doc_info = vault_map[doc_type]
            expires_at = doc_info["expires_at"]
            if expires_at:
                try:
                    exp_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
                    if exp_dt < now:
                        validations.append(
                            DocumentValidationItem(
                                doc_type=doc_type,
                                name=display_name,
                                status="EXPIRED",
                                message=f"Document '{doc_info['file_name']}' expired on {expires_at[:10]}. Please re-upload current version.",
                            )
                        )
                        continue
                except Exception:
                    pass

            validations.append(
                DocumentValidationItem(
                    doc_type=doc_type,
                    name=display_name,
                    status="VALID",
                    message=f"Verified file '{doc_info['file_name']}' available in applicant vault.",
                )
            )
        elif doc_type in req.uploaded_doc_types:
            validations.append(
                DocumentValidationItem(
                    doc_type=doc_type,
                    name=display_name,
                    status="VALID",
                    message="Document attached in current submission session.",
                )
            )
        else:
            missing_docs.append(doc_type)
            validations.append(
                DocumentValidationItem(
                    doc_type=doc_type,
                    name=display_name,
                    status="MISSING",
                    message=f"Mandatory document '{display_name}' is missing.",
                )
            )

    # Fetch smart autofill from verified data store
    verified_data = conn.execute(
        "SELECT field_key, field_value, verified_by_source FROM verified_data_store WHERE user_id = ?",
        (current_user["user_id"],),
    ).fetchall()
    autofill = {r["field_key"]: r["field_value"] for r in verified_data}

    total_items = len(validations) if validations else 1
    valid_count = sum(1 for v in validations if v.status == "VALID")
    score = int((valid_count / total_items) * 100)
    is_valid = len(missing_docs) == 0 and all(v.status == "VALID" for v in validations)

    if is_valid:
        summary = f"All {len(validations)} required documents pre-validated successfully! Application is ready for 1-click composite submission."
    else:
        summary = f"Pre-validation Score: {score}%. Found {len(missing_docs)} missing mandatory document(s). Please attach from vault or upload before submitting."

    return PreValidateResponse(
        is_valid=is_valid,
        score=score,
        validations=validations,
        missing_required_docs=missing_docs,
        autofill_suggestions=autofill,
        readiness_summary=summary,
    )

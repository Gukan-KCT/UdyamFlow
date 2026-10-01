import json
import sqlite3
from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_db
from app.schemas.udyam_schemas import (
    ApprovalItemResponse,
    ChecklistRequest,
    ChecklistResponse,
)

SAMPLE_DISCLAIMER = "SAMPLE / ILLUSTRATIVE - VERIFY AGAINST OFFICIAL STATUTORY SOURCES"

checklist_router = APIRouter(prefix="/api/checklist", tags=["Regulatory Knowledge Engine"])


@checklist_router.get("/sectors")
def get_supported_sectors():
    return [
        {"id": "Manufacturing", "name": "General Manufacturing & Engineering"},
        {"id": "Agro-processing", "name": "Agro & Food Processing"},
        {"id": "Chemical", "name": "Chemical, Petrochem & Pharma"},
        {"id": "Textile", "name": "Textile & Apparel"},
        {"id": "IT/ITES", "name": "IT / ITES & Electronics"},
        {"id": "Services", "name": "Services, Logistics & Warehousing"},
    ]


@checklist_router.get("/stages")
def get_stages():
    return [
        {"id": "Pre-Establishment", "name": "Pre-Establishment (Before Construction & Setup)"},
        {"id": "Pre-Operation", "name": "Pre-Operation (Before Commercial Production)"},
        {"id": "Renewal", "name": "Periodic Renewals & Post-Approval Compliances"},
    ]


@checklist_router.get("/catalogue", response_model=list[ApprovalItemResponse])
def get_approval_catalogue(
    stage: str | None = Query(default=None),
    sector: str | None = Query(default=None),
    conn: sqlite3.Connection = Depends(get_db),
):
    query = """
        SELECT a.*, d.name as department_name
        FROM approval_catalogue a
        JOIN departments d ON a.department_id = d.department_id
        WHERE a.is_active = 1
    """
    params = []
    if stage:
        query += " AND (a.stage = ? OR a.stage = 'All')"
        params.append(stage)
    if sector:
        query += " AND (a.sector = ? OR a.sector = 'All')"
        params.append(sector)

    query += " ORDER BY a.max_sla_days ASC"
    rows = conn.execute(query, params).fetchall()

    result = []
    for r in rows:
        prereqs = json.loads(r["prerequisites_json"]) if r["prerequisites_json"] else []
        docs = json.loads(r["documents_required_json"]) if r["documents_required_json"] else []
        result.append(
            ApprovalItemResponse(
                approval_id=r["approval_id"],
                name=r["name"],
                department_id=r["department_id"],
                department_name=r["department_name"],
                sector=r["sector"],
                stage=r["stage"],
                project_size=r["project_size"],
                location_type=r["location_type"],
                statutory_act=r["statutory_act"],
                max_sla_days=r["max_sla_days"],
                fee_inr=r["fee_inr"],
                prerequisites=prereqs,
                documents_required=docs,
                validity_years=r["validity_years"],
                sample_disclaimer=r["sample_disclaimer"] or SAMPLE_DISCLAIMER,
            )
        )
    return result


@checklist_router.post("/generate", response_model=ChecklistResponse)
def generate_customised_checklist(
    req: ChecklistRequest,
    conn: sqlite3.Connection = Depends(get_db),
):
    """
    Dynamically generates the customised approval checklist based on business parameters:
    Sector, Project Size, Stage, and Location Type.
    In Single-Window processing, parallel departmental workflows run concurrently,
    meaning total estimated timeline is governed by the Critical Path (max SLA) rather than sum.
    """
    query = """
        SELECT a.*, d.name as department_name
        FROM approval_catalogue a
        JOIN departments d ON a.department_id = d.department_id
        WHERE a.is_active = 1
          AND (a.stage = ? OR a.stage = 'All')
          AND (a.sector = 'All' OR a.sector = ?)
          AND (a.project_size = 'All' OR a.project_size = ?)
          AND (a.location_type = 'All' OR a.location_type = ?)
        ORDER BY a.max_sla_days DESC
    """
    rows = conn.execute(query, (req.stage, req.sector, req.project_size, req.location_type)).fetchall()

    matched: list[ApprovalItemResponse] = []
    total_fee = 0.0
    critical_path_sla = 0

    for r in rows:
        prereqs = json.loads(r["prerequisites_json"]) if r["prerequisites_json"] else []
        docs = json.loads(r["documents_required_json"]) if r["documents_required_json"] else []
        total_fee += float(r["fee_inr"])
        if r["max_sla_days"] > critical_path_sla:
            critical_path_sla = r["max_sla_days"]

        matched.append(
            ApprovalItemResponse(
                approval_id=r["approval_id"],
                name=r["name"],
                department_id=r["department_id"],
                department_name=r["department_name"],
                sector=r["sector"],
                stage=r["stage"],
                project_size=r["project_size"],
                location_type=r["location_type"],
                statutory_act=r["statutory_act"],
                max_sla_days=r["max_sla_days"],
                fee_inr=r["fee_inr"],
                prerequisites=prereqs,
                documents_required=docs,
                validity_years=r["validity_years"],
                sample_disclaimer=r["sample_disclaimer"] or SAMPLE_DISCLAIMER,
            )
        )

    return ChecklistResponse(
        matched_approvals=matched,
        total_approvals=len(matched),
        estimated_total_fee=total_fee,
        critical_path_sla_days=critical_path_sla,
        sector=req.sector,
        stage=req.stage,
        project_size=req.project_size,
        location_type=req.location_type,
        sample_disclaimer=SAMPLE_DISCLAIMER,
    )

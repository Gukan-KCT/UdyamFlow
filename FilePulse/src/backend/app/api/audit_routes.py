import json
import sqlite3
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.auth.dependencies import get_db, require_roles
from app.schemas.udyam_schemas import AuditLogResponse

audit_router = APIRouter(prefix="/api/audit-logs", tags=["Audit & Governance"])


@audit_router.get("", response_model=list[AuditLogResponse])
def get_audit_logs(
    action: Optional[str] = Query(default=None),
    actor_id: Optional[str] = Query(default=None),
    entity_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "nodal_officer")),
):
    query = "SELECT * FROM audit_log WHERE 1=1"
    params = []

    if action:
        query += " AND action = ?"
        params.append(action)
    if actor_id:
        query += " AND actor_id = ?"
        params.append(actor_id)
    if entity_type:
        query += " AND entity_type = ?"
        params.append(entity_type)

    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(query, params).fetchall()
    result = []
    for r in rows:
        before = json.loads(r["before_state_json"]) if r["before_state_json"] else None
        after = json.loads(r["after_state_json"]) if r["after_state_json"] else None
        result.append(
            AuditLogResponse(
                audit_id=r["audit_id"],
                actor_id=r["actor_id"],
                actor_role=r["actor_role"],
                action=r["action"],
                entity_type=r["entity_type"],
                entity_id=r["entity_id"],
                before_state=before,
                after_state=after,
                reason=r["reason"],
                ip_address=r["ip_address"],
                timestamp=r["timestamp"],
            )
        )
    return result

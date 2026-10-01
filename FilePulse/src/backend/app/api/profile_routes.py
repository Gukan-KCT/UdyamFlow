import sqlite3
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.audit.audit_service import log_audit
from app.auth.dependencies import get_current_user, get_db
from app.schemas.udyam_schemas import (
    BusinessProfileCreate,
    BusinessProfileResponse,
)

profile_router = APIRouter(prefix="/api/profile", tags=["Enterprise Business Profile"])


@profile_router.get("", response_model=BusinessProfileResponse | None)
def get_my_business_profile(
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    profile = conn.execute(
        "SELECT * FROM business_profiles WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
        (current_user["user_id"],),
    ).fetchone()
    if not profile:
        return None
    return dict(profile)


@profile_router.post("", response_model=BusinessProfileResponse)
def create_or_update_business_profile(
    req: BusinessProfileCreate,
    request: Request,
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    existing = conn.execute(
        "SELECT * FROM business_profiles WHERE user_id = ? LIMIT 1",
        (current_user["user_id"],),
    ).fetchone()

    with conn:
        if existing:
            profile_id = existing["profile_id"]
            conn.execute(
                """
                UPDATE business_profiles
                SET enterprise_name = ?, entity_type = ?, udyam_registration = ?, pan = ?, gstin = ?,
                    sector = ?, project_size = ?, investment_cr = ?, turnover_cr = ?,
                    location_type = ?, district = ?, state = ?, address = ?, lat = ?, lng = ?,
                    updated_at = datetime('now')
                WHERE profile_id = ?
                """,
                (
                    req.enterprise_name, req.entity_type, req.udyam_registration, req.pan, req.gstin,
                    req.sector, req.project_size, req.investment_cr, req.turnover_cr,
                    req.location_type, req.district, req.state, req.address, req.lat, req.lng,
                    profile_id,
                ),
            )
            log_audit(
                conn,
                actor_id=current_user["user_id"],
                actor_role=current_user["role"],
                action="PROFILE_UPDATED",
                entity_type="business_profile",
                entity_id=profile_id,
                before_state=dict(existing),
                after_state=req.model_dump(),
                ip_address=request.client.host if request.client else None,
            )
        else:
            profile_id = f"prof_{uuid.uuid4().hex[:10]}"
            conn.execute(
                """
                INSERT INTO business_profiles (
                    profile_id, user_id, enterprise_name, entity_type, udyam_registration,
                    pan, gstin, sector, project_size, investment_cr, turnover_cr,
                    location_type, district, state, address, lat, lng
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    profile_id, current_user["user_id"], req.enterprise_name, req.entity_type,
                    req.udyam_registration, req.pan, req.gstin, req.sector, req.project_size,
                    req.investment_cr, req.turnover_cr, req.location_type, req.district,
                    req.state, req.address, req.lat, req.lng,
                ),
            )
            log_audit(
                conn,
                actor_id=current_user["user_id"],
                actor_role=current_user["role"],
                action="PROFILE_CREATED",
                entity_type="business_profile",
                entity_id=profile_id,
                after_state=req.model_dump(),
                ip_address=request.client.host if request.client else None,
            )

    updated = conn.execute("SELECT * FROM business_profiles WHERE profile_id = ?", (profile_id,)).fetchone()
    return dict(updated)


@profile_router.get("/verified-data")
def get_verified_data(
    current_user: dict = Depends(get_current_user),
    conn: sqlite3.Connection = Depends(get_db),
):
    rows = conn.execute(
        "SELECT field_key, field_value, verified_by_source, verified_at FROM verified_data_store WHERE user_id = ?",
        (current_user["user_id"],),
    ).fetchall()
    return [dict(r) for r in rows]

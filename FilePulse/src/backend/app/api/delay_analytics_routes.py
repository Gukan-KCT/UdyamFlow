from datetime import datetime, timezone
import sqlite3
from fastapi import APIRouter, Depends

from app.auth.dependencies import get_current_user, get_db
from config import get_now

delay_analytics_router = APIRouter(prefix="/api/delay-analytics", tags=["Delay & Bottleneck Analytics"])


@delay_analytics_router.get("/applications")
def get_approval_delay_analytics(
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Analyzes all active single-window departmental approvals for bottlenecks,
    inactive rotting files, and ping-pong query loops.
    """
    now = get_now()

    query = """
        SELECT aa.*, ac.name as approval_name, d.name as department_name, d.code as department_code,
               a.application_number, bp.enterprise_name
        FROM application_approvals aa
        JOIN approval_catalogue ac ON aa.approval_id = ac.approval_id
        JOIN departments d ON aa.department_id = d.department_id
        JOIN applications a ON aa.application_id = a.application_id
        JOIN business_profiles bp ON a.profile_id = bp.profile_id
        WHERE aa.status NOT IN ('APPROVED', 'REJECTED')
        ORDER BY aa.risk_score DESC, aa.days_inactive DESC
    """
    rows = conn.execute(query).fetchall()

    stuck_items = []
    looping_items = []
    at_risk_items = []

    for r in rows:
        updated_dt = datetime.fromisoformat(r["updated_at"].replace("Z", "+00:00"))
        # Localize or naive compare
        if updated_dt.tzinfo is not None and now.tzinfo is None:
            updated_dt = updated_dt.replace(tzinfo=None)

        days_inactive = max(0, (now - updated_dt).days)
        is_stuck = days_inactive >= 7 or r["status"] == "QUERY_RAISED"
        is_looping = r["query_count"] >= 1 or r["loop_count"] >= 1

        # Check deadline
        days_to_deadline = None
        is_overdue = False
        if r["deadline_at"]:
            try:
                deadline_dt = datetime.fromisoformat(r["deadline_at"].replace("Z", "+00:00"))
                if deadline_dt.tzinfo is not None and now.tzinfo is None:
                    deadline_dt = deadline_dt.replace(tzinfo=None)
                days_to_deadline = (deadline_dt - now).days
                if days_to_deadline < 0:
                    is_overdue = True
            except Exception:
                pass

        # Risk scoring heuristic
        computed_risk = r["risk_score"]
        if is_overdue:
            computed_risk = max(computed_risk, 85)
        elif days_to_deadline is not None and days_to_deadline <= 3:
            computed_risk = max(computed_risk, 70)
        if is_looping:
            computed_risk = min(100, computed_risk + 20)
        if is_stuck:
            computed_risk = min(100, computed_risk + 15)

        item = {
            "app_approval_id": r["app_approval_id"],
            "application_id": r["application_id"],
            "application_number": r["application_number"],
            "enterprise_name": r["enterprise_name"],
            "approval_name": r["approval_name"],
            "department_code": r["department_code"],
            "department_name": r["department_name"],
            "status": r["status"],
            "current_stage": r["current_stage"],
            "days_inactive": days_inactive,
            "days_to_deadline": days_to_deadline,
            "is_overdue": is_overdue,
            "query_count": r["query_count"],
            "loop_count": r["loop_count"],
            "risk_score": computed_risk,
            "ai_insight": _generate_plain_language_unblocker(r, days_inactive, is_looping, is_overdue),
        }

        if is_stuck:
            stuck_items.append(item)
        if is_looping:
            looping_items.append(item)
        if computed_risk >= 50 or is_overdue:
            at_risk_items.append(item)

    return {
        "total_active_approvals": len(rows),
        "stuck_count": len(stuck_items),
        "looping_count": len(looping_items),
        "at_risk_count": len(at_risk_items),
        "stuck_approvals": stuck_items,
        "looping_approvals": looping_items,
        "at_risk_approvals": at_risk_items,
    }


@delay_analytics_router.get("/bottlenecks")
def get_department_bottlenecks(
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Provides departmental bottleneck benchmarks across approvals."""
    query = """
        SELECT d.department_id, d.name as department_name, d.code as department_code,
               COUNT(aa.app_approval_id) as total_applications,
               SUM(CASE WHEN aa.status = 'QUERY_RAISED' THEN 1 ELSE 0 END) as queries_raised,
               SUM(CASE WHEN aa.status = 'APPROVED' THEN 1 ELSE 0 END) as approved_count,
               AVG(aa.risk_score) as avg_risk_score,
               AVG(aa.sla_days) as avg_sla_days
        FROM departments d
        LEFT JOIN application_approvals aa ON d.department_id = aa.department_id
        GROUP BY d.department_id
    """
    rows = conn.execute(query).fetchall()

    benchmarks = []
    for r in rows:
        total = r["total_applications"] or 0
        queries = r["queries_raised"] or 0
        approved = r["approved_count"] or 0
        query_rate = round((queries / total * 100), 1) if total > 0 else 0.0
        approval_rate = round((approved / total * 100), 1) if total > 0 else 0.0

        benchmarks.append(
            {
                "department_id": r["department_id"],
                "department_code": r["department_code"],
                "department_name": r["department_name"],
                "total_workload": total,
                "queries_raised": queries,
                "approved_count": approved,
                "query_rate_pct": query_rate,
                "approval_rate_pct": approval_rate,
                "avg_risk_score": round(r["avg_risk_score"] or 15, 1),
                "avg_sla_days": round(r["avg_sla_days"] or 25, 0),
            }
        )

    return benchmarks


def _generate_plain_language_unblocker(row: sqlite3.Row, days_inactive: int, is_looping: bool, is_overdue: bool) -> str:
    if is_overdue:
        return f"CRITICAL: Statutory SLA breached by {abs(row['days_inactive'])} days. Nodal escalation recommended to prevent deemed approval triggers."
    if is_looping:
        return f"LOOP DETECTED: Clarification query loop ({row['query_count']} queries). Convene joint officer-applicant hearing to resolve ambiguities in one touch."
    if days_inactive >= 10:
        return f"ROTTING: Application inactive for {days_inactive} days at stage '{row['current_stage']}'. Immediate re-assignment to nodal scrutiny desk required."
    return f"On track: Application in normal processing stage '{row['current_stage']}'."

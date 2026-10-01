from datetime import datetime, timezone
import json
import sqlite3
from typing import Any
import uuid


def log_audit(
    conn: sqlite3.Connection,
    actor_id: str,
    actor_role: str,
    action: str,
    entity_type: str,
    entity_id: str,
    before_state: dict[str, Any] | None = None,
    after_state: dict[str, Any] | None = None,
    reason: str | None = None,
    ip_address: str | None = None,
) -> str:
    """
    Persists an immutable audit log entry for every state mutation in the system.
    """
    audit_id = f"aud_{uuid.uuid4().hex[:12]}"
    now = datetime.now(timezone.utc).isoformat()
    before_json = json.dumps(before_state, default=str) if before_state is not None else None
    after_json = json.dumps(after_state, default=str) if after_state is not None else None

    conn.execute(
        """
        INSERT INTO audit_log (
            audit_id, actor_id, actor_role, action, entity_type, entity_id,
            before_state_json, after_state_json, reason, ip_address, timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            audit_id,
            actor_id,
            actor_role,
            action,
            entity_type,
            entity_id,
            before_json,
            after_json,
            reason,
            ip_address,
            now,
        ),
    )
    return audit_id

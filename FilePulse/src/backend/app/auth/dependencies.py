from collections.abc import Callable
import sqlite3
from typing import Any

from fastapi import Depends, Header, HTTPException, status

from app.auth.security import decode_access_token
from app.db import DB_PATH, get_connection


def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


def get_current_user(
    authorization: str | None = Header(default=None),
    x_demo_user: str | None = Header(default=None),
    conn: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    """
    Extracts the authenticated user from the Authorization Bearer token.
    For local development/testing convenience, also supports X-Demo-User header (e.g. 'applicant@udyamflow.gov.in')
    if provided and user exists.
    """
    email: str | None = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        payload = decode_access_token(token)
        if not payload or "sub" not in payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        email = payload["sub"]
    elif x_demo_user:
        email = x_demo_user
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = conn.execute(
        """
        SELECT user_id, email, full_name, phone, role, department_id, is_active, created_at
        FROM users
        WHERE email = ? AND is_active = 1
        """,
        (email,),
    ).fetchone()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return dict(user)


def require_roles(*allowed_roles: str) -> Callable:
    """
    Enforces RBAC role restrictions on endpoints.
    Example: Depends(require_roles("admin", "nodal_officer"))
    """
    def role_checker(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        user_role = current_user.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for role '{user_role}'. Required one of: {list(allowed_roles)}",
            )
        return current_user

    return role_checker

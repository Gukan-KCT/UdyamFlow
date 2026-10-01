import sqlite3
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.audit.audit_service import log_audit
from app.auth.dependencies import get_current_user, get_db, require_roles
from app.auth.security import create_access_token, hash_password, verify_password
from app.schemas.udyam_schemas import (
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

auth_router = APIRouter(prefix="/api/auth", tags=["Authentication & Access"])


@auth_router.post("/register", response_model=TokenResponse)
def register_user(
    req: UserRegisterRequest,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
):
    existing = conn.execute("SELECT user_id FROM users WHERE email = ?", (req.email,)).fetchone()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{req.email}' already exists.",
        )

    user_id = f"usr_{uuid.uuid4().hex[:10]}"
    pwd_hash, salt = hash_password(req.password)

    with conn:
        conn.execute(
            """
            INSERT INTO users (user_id, email, password_hash, salt, full_name, phone, role, department_id, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
            """,
            (user_id, req.email, pwd_hash, salt, req.full_name, req.phone, req.role, req.department_id),
        )
        log_audit(
            conn,
            actor_id=user_id,
            actor_role=req.role,
            action="USER_REGISTERED",
            entity_type="user",
            entity_id=user_id,
            after_state={"email": req.email, "role": req.role, "full_name": req.full_name},
            ip_address=request.client.host if request.client else None,
        )

    token = create_access_token({"sub": req.email, "uid": user_id, "role": req.role})
    user_res = UserResponse(
        user_id=user_id,
        email=req.email,
        full_name=req.full_name,
        phone=req.phone,
        role=req.role,
        department_id=req.department_id,
        is_active=True,
    )
    return TokenResponse(access_token=token, token_type="bearer", user=user_res)


@auth_router.post("/login", response_model=TokenResponse)
def login_user(
    req: UserLoginRequest,
    request: Request,
    conn: sqlite3.Connection = Depends(get_db),
):
    user = conn.execute(
        """
        SELECT user_id, email, password_hash, salt, full_name, phone, role, department_id, is_active
        FROM users
        WHERE email = ?
        """,
        (req.email,),
    ).fetchone()

    if not user or not verify_password(req.password, user["password_hash"], user["salt"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact portal administrator.",
        )

    token = create_access_token({"sub": user["email"], "uid": user["user_id"], "role": user["role"]})

    with conn:
        log_audit(
            conn,
            actor_id=user["user_id"],
            actor_role=user["role"],
            action="USER_LOGGED_IN",
            entity_type="user",
            entity_id=user["user_id"],
            ip_address=request.client.host if request.client else None,
        )

    user_res = UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        full_name=user["full_name"],
        phone=user["phone"],
        role=user["role"],
        department_id=user["department_id"],
        is_active=bool(user["is_active"]),
    )
    return TokenResponse(access_token=token, token_type="bearer", user=user_res)


@auth_router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: dict = Depends(get_current_user),
):
    return UserResponse(
        user_id=current_user["user_id"],
        email=current_user["email"],
        full_name=current_user["full_name"],
        phone=current_user.get("phone"),
        role=current_user["role"],
        department_id=current_user.get("department_id"),
        is_active=bool(current_user["is_active"]),
    )


@auth_router.get("/departments")
def list_departments(conn: sqlite3.Connection = Depends(get_db)):
    rows = conn.execute("SELECT * FROM departments ORDER BY code ASC").fetchall()
    return [dict(r) for r in rows]


@auth_router.get("/users")
def list_users(
    conn: sqlite3.Connection = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "nodal_officer")),
):
    rows = conn.execute("SELECT user_id, email, full_name, phone, role, department_id, is_active, created_at FROM users").fetchall()
    return [dict(r) for r in rows]

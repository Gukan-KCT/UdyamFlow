import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.security import hash_password, verify_password, create_access_token, decode_access_token
from main import app


def test_password_hashing():
    pwd = "SecretPassword!123"
    p_hash, salt = hash_password(pwd)
    assert p_hash != pwd
    assert len(salt) == 32
    assert verify_password(pwd, p_hash, salt) is True
    assert verify_password("WrongPassword", p_hash, salt) is False


def test_token_creation_and_validation():
    payload = {"sub": "test@udyamflow.gov.in", "role": "applicant"}
    token = create_access_token(payload, expires_in_seconds=3600)
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "test@udyamflow.gov.in"
    assert decoded["role"] == "applicant"

    # Expired token test
    expired_token = create_access_token(payload, expires_in_seconds=-10)
    assert decode_access_token(expired_token) is None


@pytest.mark.asyncio
async def test_auth_login_and_me():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Login with demo applicant
        login_res = await client.post(
            "/api/auth/login",
            json={"email": "applicant@udyamflow.gov.in", "password": "Demo@123"},
        )
        assert login_res.status_code == 200
        data = login_res.json()
        assert "access_token" in data
        assert data["user"]["role"] == "applicant"
        token = data["access_token"]

        # 2. Access /api/auth/me with Bearer token
        me_res = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "applicant@udyamflow.gov.in"

        # 3. Access without token should fail
        fail_res = await client.get("/api/auth/me")
        assert fail_res.status_code == 401


@pytest.mark.asyncio
async def test_rbac_role_isolation():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login as applicant
        app_res = await client.post(
            "/api/auth/login",
            json={"email": "applicant@udyamflow.gov.in", "password": "Demo@123"},
        )
        app_token = app_res.json()["access_token"]

        # Applicant trying to access admin audit logs must be rejected with 403
        audit_res = await client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {app_token}"},
        )
        assert audit_res.status_code == 403

        # Admin login and access audit logs
        admin_res = await client.post(
            "/api/auth/login",
            json={"email": "admin@udyamflow.gov.in", "password": "Demo@123"},
        )
        admin_token = admin_res.json()["access_token"]

        admin_audit = await client.get(
            "/api/audit-logs",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert admin_audit.status_code == 200
        assert isinstance(admin_audit.json(), list)

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Any

from config import APP_SECRET_KEY


def hash_password(password: str) -> tuple[str, str]:
    """Generates a secure PBKDF2-HMAC-SHA256 hash with a cryptographically random salt."""
    salt = secrets.token_hex(16)
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100_000)
    return key.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """Verifies a password against the stored hash and salt."""
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    key = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100_000)
    return hmac.compare_digest(key.hex(), password_hash)


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    padding = 4 - (len(s) % 4)
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def create_access_token(payload: dict[str, Any], expires_in_seconds: int = 86400) -> str:
    """
    Creates a signed HMAC-SHA256 JWT-compatible bearer token without heavy dependencies.
    """
    header = {"alg": "HS256", "typ": "JWT"}
    data = dict(payload)
    now = int(time.time())
    data["iat"] = now
    data["exp"] = now + expires_in_seconds

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _b64url_encode(json.dumps(data, separators=(",", ":")).encode("utf-8"))

    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    signature = hmac.new(APP_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _b64url_encode(signature)

    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> dict[str, Any] | None:
    """
    Decodes and validates the signature and expiration time of an access token.
    Returns the payload dictionary or None if invalid or expired.
    """
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
        expected_sig = hmac.new(APP_SECRET_KEY.encode("utf-8"), signing_input, hashlib.sha256).digest()
        actual_sig = _b64url_decode(sig_b64)

        if not hmac.compare_digest(expected_sig, actual_sig):
            return None

        payload_bytes = _b64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Check expiration
        exp = payload.get("exp")
        if exp is not None and time.time() > exp:
            return None

        return payload
    except Exception:
        return None

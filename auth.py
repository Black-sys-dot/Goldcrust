"""Authentication, password hashing, and session tokens.

Zero external dependencies (uses standard library hashlib, hmac, base64, json, secrets).
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Optional
try:
    from fastapi import Request
except ImportError:
    Request = None


# Secret used to sign HMAC session cookies
SECRET = os.environ.get("AUTH_SECRET")
if not SECRET:
    db_url = os.environ.get("DATABASE_URL", "").strip()
    if db_url:
        SECRET = hashlib.sha256(f"goldcrust-session-salt-{db_url}".encode("utf-8")).hexdigest()
    else:
        SECRET = os.environ.get("DB_PASSWORD", "goldcrust-secret-key-salt-change-in-prod-2026")


SESSION_COOKIE = "gc_session"
SESSION_MAX_AGE = 30 * 24 * 3600  # 30 days


def hash_password(password: str) -> str:
    """Return a salted scrypt password hash."""
    salt = secrets.token_bytes(16)
    pw_hash = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1)
    return f"scrypt${salt.hex()}${pw_hash.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Verify password against stored scrypt hash."""
    try:
        scheme, salt_hex, hash_hex = stored_hash.split("$")
        if scheme != "scrypt":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        computed = hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1)
        return hmac.compare_digest(computed, expected)
    except Exception:
        return False


def create_session_token(user_id: int, username: str) -> str:
    """Create a signed HMAC session token."""
    payload = {
        "uid": int(user_id),
        "name": str(username),
        "exp": int(time.time()) + SESSION_MAX_AGE,
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64 = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    sig = hmac.new(SECRET.encode("utf-8"), b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{b64}.{sig}"


def verify_session_token(token: str) -> Optional[dict]:
    """Verify HMAC signature and expiration on a session token."""
    if not token or "." not in token:
        return None
    try:
        b64, sig = token.split(".", 1)
        expected_sig = hmac.new(SECRET.encode("utf-8"), b64.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected_sig):
            return None
        # restore padding
        pad = len(b64) % 4
        if pad:
            b64 += "=" * (4 - pad)
        raw = base64.urlsafe_b64decode(b64.encode("utf-8"))
        data = json.loads(raw.decode("utf-8"))
        if data.get("exp", 0) < time.time():
            return None
        return {"id": data["uid"], "username": data["name"]}
    except Exception:
        return None


def get_current_user(request: Request) -> Optional[dict]:
    """Extract authenticated user from request cookie."""
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        # Also check Authorization header as fallback
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
    return verify_session_token(token) if token else None

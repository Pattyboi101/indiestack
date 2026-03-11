"""Authentication helpers — admin auth + user auth."""

import os
import hashlib
import secrets

from fastapi import Request

# ── Admin Auth (unchanged) ───────────────────────────────────────────────

_raw_admin_pw = os.environ.get("INDIESTACK_ADMIN_PASSWORD", "")
if not _raw_admin_pw and os.environ.get("FLY_APP_NAME"):
    raise RuntimeError("INDIESTACK_ADMIN_PASSWORD must be set in production")
ADMIN_PASSWORD = _raw_admin_pw or "indiestack-dev-pw"
_SESSION_SECRET = os.environ.get("INDIESTACK_SESSION_SECRET", secrets.token_hex(32))


def make_session_token(password: str) -> str:
    return hashlib.sha256(f"{_SESSION_SECRET}{password}".encode()).hexdigest()


def check_admin_session(request: Request) -> bool:
    token = request.cookies.get("indiestack_admin")
    if not token:
        return False
    return secrets.compare_digest(token, make_session_token(ADMIN_PASSWORD))


# ── User Password Hashing ───────────────────────────────────────────────

_PW_SALT_LEN = 32
_PW_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """Hash a password with PBKDF2-HMAC-SHA256. Returns salt$hash in hex."""
    salt = secrets.token_bytes(_PW_SALT_LEN)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, _PW_ITERATIONS)
    return salt.hex() + '$' + dk.hex()


def verify_password(password: str, stored: str) -> bool:
    """Verify a password against a stored salt$hash."""
    try:
        salt_hex, hash_hex = stored.split('$', 1)
        salt = bytes.fromhex(salt_hex)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, _PW_ITERATIONS)
        return secrets.compare_digest(dk.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


# ── User Session ─────────────────────────────────────────────────────────

async def get_current_user(request: Request, db) -> dict | None:
    """Read indiestack_session cookie, look up session + user. Returns user dict or None."""
    from indiestack.db import get_session_by_token
    token = request.cookies.get("indiestack_session")
    if not token:
        return None
    row = await get_session_by_token(db, token)
    if not row:
        return None
    return {
        'id': row['uid'],
        'email': row['email'],
        'name': row['name'],
        'role': row['role'],
        'maker_id': row['maker_id'],
        'email_verified': row['email_verified'],
        'pixel_avatar': row['pixel_avatar'],
        'pixel_avatar_approved': row['pixel_avatar_approved'],
    }


async def create_user_session(db, user_id: int) -> str:
    """Create a 30-day session. Returns the token string."""
    from indiestack.db import create_session
    from datetime import datetime, timedelta
    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
    await create_session(db, user_id, token, expires)
    return token

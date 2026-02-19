"""Admin authentication helpers."""

import os
import hashlib
import secrets

from fastapi import Request

ADMIN_PASSWORD = os.environ.get("INDIESTACK_ADMIN_PASSWORD", "indiestack-dev-pw")
_SESSION_SECRET = os.environ.get("INDIESTACK_SESSION_SECRET", secrets.token_hex(32))


def make_session_token(password: str) -> str:
    return hashlib.sha256(f"{_SESSION_SECRET}{password}".encode()).hexdigest()


def check_admin_session(request: Request) -> bool:
    token = request.cookies.get("indiestack_admin")
    if not token:
        return False
    return token == make_session_token(ADMIN_PASSWORD)

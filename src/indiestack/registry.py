"""Registry lookup helpers and typosquat detection for package validation.

Checks npm and PyPI registries to verify packages exist, and detects
potential typosquats by comparing against known popular packages.

Usage:
    import httpx
    from indiestack.registry import check_registry, detect_typosquat

    async with httpx.AsyncClient() as client:
        info = await check_registry("express", "npm", client)
        # {"exists": True, "name": "express", "latest_version": "4.18.2"}

    suspect = detect_typosquat("expreess", "npm")
    # "express"
"""

import difflib
from typing import Optional

import httpx

# ── Timeouts ─────────────────────────────────────────────────────────────

_TIMEOUT = httpx.Timeout(5.0, connect=5.0)

# ── Popular package lists (typosquat detection seeds) ────────────────────

_POPULAR_NPM = [
    "express", "react", "next", "vue", "angular", "svelte", "lodash",
    "axios", "typescript", "webpack", "vite", "esbuild", "prisma",
    "drizzle-orm", "tailwindcss", "stripe", "passport", "jsonwebtoken",
    "bcrypt", "bcryptjs", "mongoose", "sequelize", "knex", "zod", "yup",
    "joi", "jest", "vitest", "mocha", "eslint", "prettier", "dotenv",
    "cors", "helmet", "morgan", "socket.io", "redis", "bull",
    "nodemailer", "sharp", "multer", "next-auth", "supabase", "firebase",
    "aws-sdk", "pg", "mysql2", "better-sqlite3", "fastify", "koa",
    "hono", "pino",
]

_POPULAR_PYPI = [
    "requests", "flask", "django", "fastapi", "sqlalchemy", "pydantic",
    "pytest", "numpy", "pandas", "httpx", "celery", "redis", "boto3",
    "pillow", "beautifulsoup4", "scrapy", "click", "typer", "rich",
    "uvicorn", "gunicorn", "alembic", "aiohttp", "aiosqlite",
    "python-dotenv", "passlib", "bcrypt", "python-jose", "stripe",
    "sentry-sdk", "loguru", "black", "ruff", "mypy",
]

_POPULAR = {
    "npm": _POPULAR_NPM,
    "pypi": _POPULAR_PYPI,
}


# ── Registry lookups ─────────────────────────────────────────────────────

async def check_npm(name: str, client: httpx.AsyncClient) -> Optional[dict]:
    """Check npm registry for a package.

    Returns {"exists": True, "name": ..., "latest_version": ...} on success,
    None if the package doesn't exist (404).
    On network errors, fails open with exists=True and null fields.
    """
    url = f"https://registry.npmjs.org/{name}"
    headers = {"Accept": "application/vnd.npm.install-v1+json"}
    try:
        resp = await client.get(url, headers=headers, timeout=_TIMEOUT)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        # The abbreviated metadata has dist-tags.latest
        latest = None
        dist_tags = data.get("dist-tags", {})
        if dist_tags:
            latest = dist_tags.get("latest")
        return {
            "exists": True,
            "name": data.get("name", name),
            "latest_version": latest,
        }
    except httpx.HTTPStatusError:
        # Non-404 HTTP errors — fail open
        return {"exists": True, "name": name, "latest_version": None}
    except (httpx.RequestError, Exception):
        # Network timeout, DNS failure, etc. — fail open, never block
        return {"exists": True, "name": name, "latest_version": None}


async def check_pypi(name: str, client: httpx.AsyncClient) -> Optional[dict]:
    """Check PyPI for a package.

    Returns {"exists": True, "name": ..., "latest_version": ..., "summary": ...}
    on success, None if the package doesn't exist (404).
    On network errors, fails open with exists=True and null fields.
    """
    url = f"https://pypi.org/pypi/{name}/json"
    try:
        resp = await client.get(url, timeout=_TIMEOUT)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
        info = data.get("info", {})
        return {
            "exists": True,
            "name": info.get("name", name),
            "latest_version": info.get("version"),
            "summary": info.get("summary"),
        }
    except httpx.HTTPStatusError:
        return {"exists": True, "name": name, "latest_version": None, "summary": None}
    except (httpx.RequestError, Exception):
        return {"exists": True, "name": name, "latest_version": None, "summary": None}


async def check_registry(
    name: str, ecosystem: str, client: httpx.AsyncClient
) -> Optional[dict]:
    """Route to the correct registry by ecosystem string.

    Supported ecosystems: "npm", "pypi".
    Returns None if the package doesn't exist, or a dict with package info.
    Raises ValueError for unsupported ecosystems.
    """
    ecosystem = ecosystem.lower().strip()
    if ecosystem == "npm":
        return await check_npm(name, client)
    elif ecosystem == "pypi":
        return await check_pypi(name, client)
    else:
        raise ValueError(f"Unsupported ecosystem: {ecosystem!r} (expected 'npm' or 'pypi')")


# ── Typosquat detection ──────────────────────────────────────────────────

def detect_typosquat(
    name: str,
    ecosystem: str,
    db_slugs: list[str] | None = None,
) -> Optional[str]:
    """Check if a package name looks like a typo of a known package.

    Compares against popular packages for the ecosystem plus any db_slugs
    provided (from the IndieStack tool database).

    Returns the likely intended name if a close match is found,
    or None if the name is an exact match or nothing is close enough.
    """
    name_lower = name.lower().strip()
    ecosystem_lower = ecosystem.lower().strip()

    # Build the corpus of known-good names
    known = list(_POPULAR.get(ecosystem_lower, []))
    if db_slugs:
        known.extend(db_slugs)

    # Deduplicate and lowercase for comparison
    known_lower = list({k.lower() for k in known})

    # Exact match — not a typosquat
    if name_lower in known_lower:
        return None

    # Find close matches
    matches = difflib.get_close_matches(name_lower, known_lower, n=1, cutoff=0.8)
    if matches:
        return matches[0]

    return None

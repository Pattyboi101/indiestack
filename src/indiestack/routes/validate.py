"""Package validation API — guardrail endpoint for AI agents.

Validates package names against registries, detects typosquats,
and returns risk assessments with migration alternatives.
"""

import logging

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ..registry import check_registry, detect_typosquat

_log = logging.getLogger("indiestack.validate")
router = APIRouter()

_VALID_ECOSYSTEMS = {"npm", "pypi", "cargo", "go"}

# ── Module-level httpx client ────────────────────────────────────────────

_registry_client: httpx.AsyncClient | None = None


async def _get_registry_client() -> httpx.AsyncClient:
    global _registry_client
    if _registry_client is None or _registry_client.is_closed:
        _registry_client = httpx.AsyncClient(timeout=5.0)
    return _registry_client


# ── Endpoint ─────────────────────────────────────────────────────────────

@router.get("/api/validate")
async def validate_package(request: Request, name: str = "", ecosystem: str = "npm"):
    """Validate a package name: registry check, typosquat detection, risk level."""
    # 1. Validate inputs
    name = name.strip()
    ecosystem = ecosystem.lower().strip()

    if not name:
        return JSONResponse(
            {"error": "name parameter is required"},
            status_code=400,
        )
    if len(name) > 200:
        return JSONResponse(
            {"error": "name must be 200 characters or fewer"},
            status_code=400,
        )
    if ecosystem not in _VALID_ECOSYSTEMS:
        return JSONResponse(
            {"error": f"ecosystem must be one of: {', '.join(sorted(_VALID_ECOSYSTEMS))}"},
            status_code=400,
        )

    d = request.state.db
    notes: list[str] = []

    # 2. Check our tools DB
    indiestack_tool = None
    name_lower = name.lower()
    cursor = await d.execute(
        "SELECT slug, name, tagline, quality_score, github_stars, source_type, status "
        "FROM tools WHERE slug = ? OR LOWER(name) = ? LIMIT 1",
        (name_lower, name_lower),
    )
    row = await cursor.fetchone()
    if row:
        indiestack_tool = {
            "slug": row["slug"],
            "name": row["name"],
            "tagline": row["tagline"],
            "quality_score": row["quality_score"],
            "github_stars": row["github_stars"] or 0,
            "source_type": row["source_type"],
            "status": row["status"],
        }
        notes.append(f"Tracked by IndieStack as '{row['name']}'")

    # 3. Typosquat check
    cursor2 = await d.execute(
        "SELECT slug FROM tools WHERE status='approved' LIMIT 5000"
    )
    db_slugs = [r["slug"] for r in await cursor2.fetchall()]
    typosquat_match = detect_typosquat(name, ecosystem, db_slugs)
    typosquat_warning = None
    suggested_instead = None
    if typosquat_match:
        typosquat_warning = f"'{name}' looks like a typo of '{typosquat_match}'"
        suggested_instead = typosquat_match
        notes.append(f"Possible typosquat — did you mean '{typosquat_match}'?")

    # 4. Live registry check (npm/pypi only)
    registry_data = None
    pkg_exists: bool | None = None
    if ecosystem in ("npm", "pypi"):
        client = await _get_registry_client()
        registry_data = await check_registry(name, ecosystem, client)
        if registry_data is None:
            pkg_exists = False
            notes.append(f"Package '{name}' not found on {ecosystem}")
        else:
            pkg_exists = registry_data.get("exists", True)
    else:
        notes.append(f"Registry check not available for {ecosystem}")

    # 5. Migration data
    migration_alternatives = None
    cursor3 = await d.execute(
        "SELECT to_package, COUNT(*) as cnt FROM migration_paths "
        "WHERE from_package = ? GROUP BY to_package ORDER BY cnt DESC LIMIT 3",
        (name_lower,),
    )
    migration_rows = await cursor3.fetchall()
    if migration_rows:
        migration_alternatives = [
            {"package": r["to_package"], "migration_count": r["cnt"]}
            for r in migration_rows
        ]
        names = ", ".join(r["to_package"] for r in migration_rows)
        notes.append(f"Migration alternatives: {names}")

    # 6. Determine risk_level
    risk_level = "unknown"
    if pkg_exists is False or typosquat_match:
        risk_level = "danger"
        if pkg_exists is False and typosquat_match:
            notes.append("DANGER: package not found and name looks like a typosquat")
        elif pkg_exists is False:
            notes.append("DANGER: package does not exist in registry")
        else:
            notes.append("DANGER: possible typosquat detected")
    elif pkg_exists is True:
        # Check quality/archived status
        if indiestack_tool:
            qs = indiestack_tool.get("quality_score") or 0
            status = indiestack_tool.get("status", "")
            if status == "archived" or qs < 20:
                risk_level = "caution"
                notes.append("CAUTION: tool has low quality score or is archived")
            else:
                risk_level = "safe"
        else:
            risk_level = "safe"

    health = "tracked" if indiestack_tool else None

    # 7. Log the validation (non-fatal)
    try:
        await d.execute(
            "INSERT INTO validation_logs (package, ecosystem, exists, is_typosquat, risk_level) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, ecosystem, pkg_exists, 1 if typosquat_match else 0, risk_level),
        )
        await d.commit()
    except Exception as e:
        _log.warning("validation log failed: %s", e)

    return JSONResponse({
        "package": name,
        "ecosystem": ecosystem,
        "exists": pkg_exists,
        "registry_data": registry_data,
        "typosquat_warning": typosquat_warning,
        "suggested_instead": suggested_instead,
        "indiestack_tool": indiestack_tool,
        "health": health,
        "risk_level": risk_level,
        "migration_alternatives": migration_alternatives,
        "notes": notes,
    })

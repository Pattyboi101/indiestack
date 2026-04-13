"""x402-gated Oracle API — pay-per-call compatibility and migration data."""

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi_x402 import pay

_log = logging.getLogger("indiestack.oracle")
router = APIRouter()


async def _log_call(d, endpoint: str, slug_a: str, slug_b: str, had_data: bool):
    """Log an oracle call for analytics. Fire-and-forget, never fails the request."""
    try:
        await d.execute(
            "INSERT INTO oracle_calls (endpoint, slug_a, slug_b, had_data) VALUES (?, ?, ?, ?)",
            (endpoint, slug_a, slug_b, 1 if had_data else 0))
        await d.commit()
    except Exception as e:
        _log.warning("oracle call log failed: %s", e)


# -- Compatibility endpoint ------------------------------------------------

@pay("$0.02")
@router.get("/v1/compatibility/{tool_a}/{tool_b}")
async def compatibility(request: Request, tool_a: str, tool_b: str):
    """Check if two tools are compatible. Returns compatibility data from
    6,622 verified pairs and 58,638 manifest co-occurrences."""
    d = request.state.db

    # Normalize: always query with alphabetically sorted slugs
    a, b = sorted([tool_a.lower().strip(), tool_b.lower().strip()])

    # Check tool_pairs (direct compatibility data)
    cursor = await d.execute(
        "SELECT verified, success_count, source FROM tool_pairs "
        "WHERE tool_a_slug = ? AND tool_b_slug = ?", (a, b))
    pair = await cursor.fetchone()

    # Check manifest_cooccurrences (packages found together in real repos)
    cursor2 = await d.execute(
        "SELECT cooccurrence_count FROM manifest_cooccurrences "
        "WHERE tool_a_slug = ? AND tool_b_slug = ?", (a, b))
    cooccurrence = await cursor2.fetchone()

    # Check verified_combos (real packages found together in starred repos)
    cursor3 = await d.execute(
        "SELECT repo, repo_stars FROM verified_combos "
        "WHERE (package_a = ? AND package_b = ?) OR (package_a = ? AND package_b = ?) "
        "ORDER BY repo_stars DESC LIMIT 10", (a, b, b, a))
    combos = [dict(r) for r in await cursor3.fetchall()]

    if not pair and not cooccurrence and not combos:
        await _log_call(d, "compatibility", a, b, False)
        return JSONResponse({
            "tool_a": a,
            "tool_b": b,
            "compatible": None,
            "confidence": "no_data",
            "message": f"No compatibility data found for {a} + {b}."
        })

    await _log_call(d, "compatibility", a, b, True)

    # Find related tools (other tools commonly paired with tool_a)
    cursor4 = await d.execute(
        "SELECT tool_b_slug FROM tool_pairs WHERE tool_a_slug = ? "
        "ORDER BY success_count DESC LIMIT 5", (a,))
    related = [r['tool_b_slug'] for r in await cursor4.fetchall() if r['tool_b_slug'] != b]

    has_evidence = (pair and pair['success_count'] > 0) or cooccurrence or combos

    return JSONResponse({
        "tool_a": a,
        "tool_b": b,
        "compatible": True if has_evidence else None,
        "confidence": "verified" if pair and pair['verified'] else "observed" if (cooccurrence or combos) else "reported",
        "success_count": pair['success_count'] if pair else 0,
        "source": pair['source'] if pair else ("verified_combos" if combos else "cooccurrence"),
        "cooccurrence_count": cooccurrence['cooccurrence_count'] if cooccurrence else 0,
        "verified_in_repos": [{"repo": c['repo'], "stars": c['repo_stars']} for c in combos[:5]],
        "verified_repo_count": len(combos),
        "related_tools": related[:5],
    })


# -- Migration endpoint ----------------------------------------------------

@pay("$0.05")
@router.get("/v1/migration/{from_package}/{to_package}")
async def migration(request: Request, from_package: str, to_package: str):
    """Get real migration data from GitHub repos — how many repos switched,
    when, and confidence level. 422 migration paths from real git history."""
    d = request.state.db

    from_pkg = from_package.lower().strip()
    to_pkg = to_package.lower().strip()

    # Forward migrations (from -> to)
    cursor = await d.execute(
        "SELECT repo, commit_sha, committed_at, confidence FROM migration_paths "
        "WHERE from_package = ? AND to_package = ? "
        "ORDER BY committed_at DESC LIMIT 20", (from_pkg, to_pkg))
    forward = [dict(r) for r in await cursor.fetchall()]

    # Reverse migrations (to -> from) for net momentum
    cursor2 = await d.execute(
        "SELECT COUNT(*) as cnt FROM migration_paths "
        "WHERE from_package = ? AND to_package = ?", (to_pkg, from_pkg))
    reverse_count = (await cursor2.fetchone())['cnt']

    if not forward and reverse_count == 0:
        await _log_call(d, "migration", from_pkg, to_pkg, False)
        return JSONResponse({
            "from": from_pkg,
            "to": to_pkg,
            "migrations_found": 0,
            "message": f"No migration data found for {from_pkg} -> {to_pkg}."
        })

    await _log_call(d, "migration", from_pkg, to_pkg, True)

    # Confidence breakdown
    confidence_counts = {"swap": 0, "likely": 0, "inferred": 0}
    for m in forward:
        c = m.get('confidence', 'inferred')
        if c in confidence_counts:
            confidence_counts[c] += 1

    return JSONResponse({
        "from": from_pkg,
        "to": to_pkg,
        "migrations_found": len(forward),
        "repos": [{"repo": m['repo'], "committed_at": m['committed_at'],
                    "confidence": m['confidence']} for m in forward],
        "reverse_migrations": reverse_count,
        "net_momentum": len(forward) - reverse_count,
        "confidence_summary": confidence_counts,
    })


# -- Bazaar discovery metadata ---------------------------------------------

@router.get("/v1/.well-known/x402-resources")
async def x402_resources():
    """x402 Bazaar discovery metadata — agents use this to find our services."""
    return JSONResponse({
        "name": "IndieStack Oracle",
        "description": "Compatibility and migration intelligence for developer tools. 6,622 verified pairs, 422 migration paths from real GitHub repos.",
        "endpoints": [
            {
                "path": "/v1/compatibility/{tool_a}/{tool_b}",
                "method": "GET",
                "price": "$0.02",
                "description": "Check if two developer tools are compatible. Returns verified compatibility data, co-occurrence counts from real repos, and related tools.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "tool_a": {"type": "string", "description": "First tool slug (e.g., 'nextjs', 'react', 'supabase')"},
                        "tool_b": {"type": "string", "description": "Second tool slug"}
                    },
                    "required": ["tool_a", "tool_b"]
                },
                "output": {
                    "example": {
                        "tool_a": "nextjs",
                        "tool_b": "supabase",
                        "compatible": True,
                        "confidence": "verified",
                        "success_count": 47,
                        "cooccurrence_count": 312,
                        "related_tools": ["prisma", "lucia-auth"]
                    }
                }
            },
            {
                "path": "/v1/migration/{from_package}/{to_package}",
                "method": "GET",
                "price": "$0.05",
                "description": "Get real migration data from GitHub repos. How many repos switched between packages, when, and confidence level.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "from_package": {"type": "string", "description": "Package migrating from (e.g., 'jest', 'webpack')"},
                        "to_package": {"type": "string", "description": "Package migrating to (e.g., 'vitest', 'vite')"}
                    },
                    "required": ["from_package", "to_package"]
                },
                "output": {
                    "example": {
                        "from": "jest",
                        "to": "vitest",
                        "migrations_found": 27,
                        "net_momentum": 25,
                        "confidence_summary": {"swap": 20, "likely": 5, "inferred": 2}
                    }
                }
            }
        ]
    })

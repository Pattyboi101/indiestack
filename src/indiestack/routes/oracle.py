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


# -- Stack Architect endpoint ----------------------------------------------

@pay("$0.10")
@router.post("/v1/stack/architect")
async def stack_architect(request: Request):
    """Validate an entire tool stack. Returns a compatibility matrix,
    conflict warnings, and migration alternatives for each package pair."""
    d = request.state.db

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON body"}, status_code=400)

    packages = body.get("packages", [])
    if not packages or not isinstance(packages, list):
        return JSONResponse({"error": "Provide a 'packages' array with 2+ tool names"}, status_code=400)

    # Normalize and deduplicate
    packages = list(dict.fromkeys([p.lower().strip() for p in packages if isinstance(p, str) and p.strip()]))
    if len(packages) < 2:
        return JSONResponse({"error": "Need at least 2 packages to analyze"}, status_code=400)
    if len(packages) > 20:
        return JSONResponse({"error": "Maximum 20 packages per request"}, status_code=400)

    # Build all unique pairs (alphabetically sorted)
    pairs = []
    for i in range(len(packages)):
        for j in range(i + 1, len(packages)):
            a, b = sorted([packages[i], packages[j]])
            pairs.append((a, b))

    # Query all data sources for each pair
    matrix = []
    conflicts = []
    total_evidence = 0

    for a, b in pairs:
        cursor = await d.execute(
            "SELECT verified, success_count, source FROM tool_pairs "
            "WHERE tool_a_slug = ? AND tool_b_slug = ?", (a, b))
        pair = await cursor.fetchone()

        cursor2 = await d.execute(
            "SELECT cooccurrence_count FROM manifest_cooccurrences "
            "WHERE tool_a_slug = ? AND tool_b_slug = ?", (a, b))
        cooc = await cursor2.fetchone()

        cursor3 = await d.execute(
            "SELECT COUNT(*) as cnt, MAX(repo_stars) as max_stars FROM verified_combos "
            "WHERE (package_a = ? AND package_b = ?) OR (package_a = ? AND package_b = ?)",
            (a, b, b, a))
        combo = await cursor3.fetchone()

        evidence_count = (
            (pair['success_count'] if pair else 0) +
            (cooc['cooccurrence_count'] if cooc else 0) +
            (combo['cnt'] if combo else 0)
        )
        total_evidence += evidence_count

        confidence = "no_data"
        if pair and pair['verified']:
            confidence = "verified"
        elif (combo and combo['cnt'] > 0) or cooc:
            confidence = "observed"
        elif pair:
            confidence = "reported"

        entry = {
            "pair": [a, b],
            "compatible": True if evidence_count > 0 else None,
            "confidence": confidence,
            "evidence_count": evidence_count,
            "max_repo_stars": combo['max_stars'] if combo and combo['max_stars'] else 0,
        }

        if confidence == "no_data":
            conflicts.append(f"No compatibility data for {a} + {b}")

        matrix.append(entry)

    # Check migration momentum for each package (is it being abandoned?)
    warnings = []
    for pkg in packages:
        cursor_mig = await d.execute(
            "SELECT to_package, COUNT(*) as cnt FROM migration_paths "
            "WHERE from_package = ? GROUP BY to_package ORDER BY cnt DESC LIMIT 1", (pkg,))
        mig = await cursor_mig.fetchone()
        if mig and mig['cnt'] >= 3:
            warnings.append({
                "package": pkg,
                "warning": "migration_momentum",
                "detail": f"{mig['cnt']} repos migrated from {pkg} to {mig['to_package']}",
                "alternative": mig['to_package'],
            })

    # Overall stack score
    total_pairs = len(pairs)
    pairs_with_data = sum(1 for m in matrix if m['confidence'] != 'no_data')
    coverage = round(pairs_with_data / total_pairs * 100) if total_pairs > 0 else 0

    await _log_call(d, "stack_architect", ",".join(packages[:5]), str(len(packages)), total_evidence > 0)

    return JSONResponse({
        "packages": packages,
        "stack_score": coverage,
        "total_pairs_checked": total_pairs,
        "pairs_with_evidence": pairs_with_data,
        "total_evidence_points": total_evidence,
        "matrix": matrix,
        "conflicts": conflicts,
        "migration_warnings": warnings,
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

"""x402-gated Oracle API — pay-per-call compatibility and migration data."""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


# -- Compatibility endpoint ------------------------------------------------

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

    if not pair and not cooccurrence:
        return JSONResponse({
            "tool_a": a,
            "tool_b": b,
            "compatible": None,
            "confidence": "no_data",
            "message": f"No compatibility data found for {a} + {b}."
        })

    # Find related tools (other tools commonly paired with tool_a)
    cursor3 = await d.execute(
        "SELECT tool_b_slug FROM tool_pairs WHERE tool_a_slug = ? "
        "ORDER BY success_count DESC LIMIT 5", (a,))
    related = [r['tool_b_slug'] for r in await cursor3.fetchall() if r['tool_b_slug'] != b]

    return JSONResponse({
        "tool_a": a,
        "tool_b": b,
        "compatible": True if (pair and pair['success_count'] > 0) or cooccurrence else None,
        "confidence": "verified" if pair and pair['verified'] else "observed" if cooccurrence else "reported",
        "success_count": pair['success_count'] if pair else 0,
        "source": pair['source'] if pair else "cooccurrence",
        "cooccurrence_count": cooccurrence['cooccurrence_count'] if cooccurrence else 0,
        "related_tools": related[:5],
    })


# -- Migration endpoint ----------------------------------------------------

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
        return JSONResponse({
            "from": from_pkg,
            "to": to_pkg,
            "migrations_found": 0,
            "message": f"No migration data found for {from_pkg} -> {to_pkg}."
        })

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

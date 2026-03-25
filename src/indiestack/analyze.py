"""
Lighthouse for Dependencies — scoring engine.

Parses package.json / requirements.txt manifests, matches packages
to IndieStack tools, and returns a 0-100 Project Intelligence Score.
"""

import json
import re
from datetime import datetime, timezone
from typing import Any


# ── Manifest parsing ─────────────────────────────────────────────────────────

def parse_manifest(content: str, manifest_type: str) -> list[str]:
    """Extract package names from a manifest file. Returns lowercased names."""
    if "lock" in manifest_type.lower() or "package-lock" in content[:200]:
        raise ValueError(
            "Please provide package.json or requirements.txt, not a lock file."
        )

    if manifest_type == "package.json":
        return _parse_package_json(content)
    elif manifest_type == "requirements.txt":
        return _parse_requirements_txt(content)
    else:
        raise ValueError(f"Unsupported manifest type: {manifest_type}")


def _parse_package_json(content: str) -> list[str]:
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        # Fallback: regex extraction for partial / malformed JSON
        return _parse_package_json_regex(content)

    packages = set()
    for section in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps = data.get(section, {})
        if isinstance(deps, dict):
            packages.update(deps.keys())
    return sorted(p.lower().strip() for p in packages if p)


def _parse_package_json_regex(content: str) -> list[str]:
    """Regex fallback for when JSON parsing fails (e.g. partial paste)."""
    skip = {
        "name", "version", "description", "main", "scripts", "repository",
        "keywords", "author", "license", "bugs", "homepage", "type",
        "dependencies", "devdependencies", "peerdependencies",
        "optionaldependencies", "engines", "private", "workspaces",
    }
    packages = set()
    for m in re.finditer(r'"(@?[a-z0-9][\w./@-]*)"\s*:', content, re.IGNORECASE):
        name = m.group(1).lower()
        if name not in skip:
            packages.add(name)
    return sorted(packages)


def _parse_requirements_txt(content: str) -> list[str]:
    packages = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Strip version specifiers and extras
        for sep in ("==", ">=", "<=", "~=", "!=", ">", "<", "[", ";", " "):
            line = line.split(sep)[0]
        name = line.strip()
        if name:
            packages.add(name.lower())
    return sorted(packages)


# ── Package matching ─────────────────────────────────────────────────────────

async def match_packages(db, package_names: list[str], manifest_type: str) -> dict[str, dict]:
    """
    Match package names to IndieStack tools.

    Returns dict mapping package_name -> tool row dict.
    Uses three strategies: slug match, sdk_packages dict match, sdk_packages array match.
    """
    if not package_names:
        return {}

    matched: dict[str, dict] = {}
    remaining = set(package_names)

    # Strategy 1: exact slug match (covers express, supabase, stripe, etc.)
    await _match_by_slug(db, remaining, matched)

    if not remaining:
        return matched

    # Strategy 2: sdk_packages field (both dict and array formats)
    await _match_by_sdk_packages(db, remaining, matched, manifest_type)

    return matched


async def _match_by_slug(db, remaining: set, matched: dict):
    """Match packages by exact tool slug."""
    slugs = list(remaining)
    # SQLite binding limit ~999, chunk if needed
    for i in range(0, len(slugs), 500):
        chunk = slugs[i:i + 500]
        placeholders = ",".join(["?"] * len(chunk))
        query = f"""
            SELECT id, name, slug, category_id, upvote_count,
                   health_status, github_last_commit, github_is_archived,
                   github_stars
            FROM tools
            WHERE slug IN ({placeholders}) AND status = 'approved'
        """
        async with db.execute(query, chunk) as cursor:
            async for row in cursor:
                tool = row if isinstance(row, dict) else dict(row)
                slug = tool["slug"]
                if slug in remaining:
                    matched[slug] = tool
                    remaining.discard(slug)


async def _match_by_sdk_packages(db, remaining: set, matched: dict, manifest_type: str):
    """Match packages via the sdk_packages JSON column."""
    # Build a lookup of all tools with sdk_packages
    query = """
        SELECT id, name, slug, category_id, upvote_count,
               health_status, github_last_commit, github_is_archived,
               github_stars, sdk_packages
        FROM tools
        WHERE sdk_packages IS NOT NULL AND sdk_packages != ''
          AND status = 'approved'
    """
    pkg_key = "npm" if manifest_type == "package.json" else "pip"
    remaining_lower = {p.lower() for p in remaining}

    # Collect all candidates per package, then pick best match
    candidates: dict[str, list[dict]] = {}

    async with db.execute(query) as cursor:
        async for row in cursor:
            tool = row if isinstance(row, dict) else dict(row)
            sdk = tool.pop("sdk_packages", "")
            try:
                parsed = json.loads(sdk)
            except (json.JSONDecodeError, TypeError):
                continue

            pkg_names_in_tool = set()
            if isinstance(parsed, dict):
                # Dict format: {"npm": "express", "pip": "flask"}
                val = parsed.get(pkg_key, "")
                if val:
                    pkg_names_in_tool.add(val.lower())
            elif isinstance(parsed, list):
                # Array format: ["package-name"]
                pkg_names_in_tool.update(p.lower() for p in parsed if isinstance(p, str))

            for pkg_name in pkg_names_in_tool:
                if pkg_name in remaining_lower:
                    candidates.setdefault(pkg_name, []).append(tool)

    # Pick best match: prefer tools whose slug contains the package name
    for pkg_name, tools in candidates.items():
        if len(tools) == 1:
            best = tools[0]
        else:
            # Prefer: exact slug → slug substring of pkg → pkg substring of slug → name match
            best = tools[0]
            for t in tools:
                slug = t["slug"]
                if slug == pkg_name:
                    best = t
                    break
                if slug in pkg_name or pkg_name in slug:
                    best = t
                    break
                if pkg_name.split("-")[0] in t["name"].lower():
                    best = t
        matched[pkg_name] = best
        remaining.discard(pkg_name)
        remaining_lower.discard(pkg_name)


# ── Scoring ──────────────────────────────────────────────────────────────────

def calculate_freshness(mapped_tools: list[dict]) -> tuple[int, list[dict]]:
    """
    Freshness score (0-100): how actively maintained are the dependencies?
    Returns (score, per_tool_details).
    """
    if not mapped_tools:
        return 0, []

    details = []
    total = 0

    for t in mapped_tools:
        tool_score = 50  # default for unknown
        status = "unknown"

        if t.get("github_is_archived") or t.get("health_status") == "dead":
            tool_score = 0
            status = "dead"
        elif t.get("github_last_commit"):
            try:
                lc = t["github_last_commit"]
                if isinstance(lc, str):
                    dt = datetime.fromisoformat(lc.replace("Z", "+00:00"))
                    days_ago = (datetime.now(timezone.utc) - dt).days
                    if days_ago < 90:
                        tool_score, status = 100, "active"
                    elif days_ago < 180:
                        tool_score, status = 80, "maintained"
                    elif days_ago < 365:
                        tool_score, status = 50, "stale"
                    else:
                        tool_score, status = 20, "dormant"
            except (ValueError, TypeError):
                pass
        elif t.get("health_status") == "alive":
            tool_score, status = 80, "maintained"

        total += tool_score
        details.append({
            "slug": t["slug"],
            "name": t["name"],
            "freshness": tool_score,
            "status": status,
        })

    return int(total / len(mapped_tools)), details


async def calculate_cohesion(db, mapped_tools: list[dict]) -> tuple[int, list[dict]]:
    """
    Cohesion score (0-100): how well do the dependencies work together?
    Checks tool_pairs for known compatibility data.
    """
    if len(mapped_tools) < 2:
        return 90, []  # Single dep = no conflicts

    slugs = [t["slug"] for t in mapped_tools]
    placeholders = ",".join(["?"] * len(slugs))

    # Find pairs where both tools are in the manifest
    query = f"""
        SELECT tool_a_slug, tool_b_slug, success_count
        FROM tool_pairs
        WHERE tool_a_slug IN ({placeholders}) AND tool_b_slug IN ({placeholders})
    """
    pairs = []
    async with db.execute(query, slugs + slugs) as cursor:
        pairs = [r if isinstance(r, dict) else dict(r) for r in await cursor.fetchall()]

    score = 80  # base
    details = []

    for pair in pairs:
        if pair["success_count"] > 0:
            score += 3  # verified compatible
            details.append({
                "a": pair["tool_a_slug"],
                "b": pair["tool_b_slug"],
                "status": "compatible",
                "evidence": pair["success_count"],
            })
        elif pair["success_count"] < 0:
            score -= 20  # known conflict
            details.append({
                "a": pair["tool_a_slug"],
                "b": pair["tool_b_slug"],
                "status": "conflict",
                "evidence": pair["success_count"],
            })

    # Bonus for having lots of verified pairs
    verified_count = sum(1 for p in pairs if p["success_count"] > 0)
    if verified_count >= 5:
        score += 5

    return max(0, min(100, score)), details


async def calculate_modernity(db, mapped_tools: list[dict]) -> tuple[int, list[dict]]:
    """
    Modernity score (0-100): are there better alternatives to your dependencies?
    Checks if tools in the same category have significantly more traction.
    """
    if not mapped_tools:
        return 0, []

    category_ids = list({t["category_id"] for t in mapped_tools if t.get("category_id")})
    if not category_ids:
        return 85, []

    mapped_slugs = {t["slug"] for t in mapped_tools}
    placeholders = ",".join(["?"] * len(category_ids))

    # Get top tools per category (approved only)
    query = f"""
        SELECT t.slug, t.name, t.category_id, t.upvote_count, t.github_stars,
               t.health_status
        FROM tools t
        WHERE t.category_id IN ({placeholders})
          AND t.status = 'approved'
          AND t.health_status IN ('alive', 'unknown')
        ORDER BY t.upvote_count DESC
    """
    competitors = []
    async with db.execute(query, category_ids) as cursor:
        competitors = [r if isinstance(r, dict) else dict(r) for r in await cursor.fetchall()]

    deductions = 0
    details = []

    for t in mapped_tools:
        cat_id = t.get("category_id")
        if not cat_id:
            continue

        cat_competitors = [
            c for c in competitors
            if c["category_id"] == cat_id and c["slug"] not in mapped_slugs
        ]

        # Find significantly better alternatives
        t_score = (t.get("upvote_count") or 0) + (t.get("github_stars") or 0) // 100
        better = []
        for c in cat_competitors[:10]:  # top 10 in category
            c_score = (c.get("upvote_count") or 0) + (c.get("github_stars") or 0) // 100
            if c_score > t_score * 1.5 and c_score > 3:
                better.append(c)

        if better:
            deductions += 10
            details.append({
                "slug": t["slug"],
                "name": t["name"],
                "alternatives": [
                    {"slug": b["slug"], "name": b["name"]}
                    for b in better[:3]
                ],
            })

    return max(0, 100 - deductions), details


# ── Orchestrator ─────────────────────────────────────────────────────────────

async def run_analysis(db, manifest_content: str, manifest_type: str) -> dict[str, Any]:
    """
    Full dependency analysis pipeline.

    Returns:
        {
            "score": {"total": int, "freshness": int, "cohesion": int, "modernity": int},
            "packages_total": int,
            "packages_matched": int,
            "matched": [{"package": str, "tool": {...}, "freshness": {...}}],
            "unmatched": [str],
            "cohesion_details": [...],
            "modernity_details": [...],
            "manifest_type": str,
        }
    """
    # 1. Parse
    packages = parse_manifest(manifest_content, manifest_type)
    if not packages:
        raise ValueError("No packages found in manifest.")

    # 2. Match (db.row_factory already set to dict factory by get_db())
    matched_map = await match_packages(db, packages, manifest_type)

    # 3. Build tool list
    mapped_tools = list(matched_map.values())
    matched_packages = []
    unmatched_packages = []

    for pkg in packages:
        if pkg in matched_map:
            matched_packages.append({"package": pkg, "tool": matched_map[pkg]})
        else:
            unmatched_packages.append(pkg)

    # 4. Score
    freshness_score, freshness_details = calculate_freshness(mapped_tools)
    cohesion_score, cohesion_details = await calculate_cohesion(db, mapped_tools)
    modernity_score, modernity_details = await calculate_modernity(db, mapped_tools)

    # Merge freshness details into matched packages
    freshness_by_slug = {d["slug"]: d for d in freshness_details}
    for mp in matched_packages:
        slug = mp["tool"]["slug"]
        if slug in freshness_by_slug:
            mp["freshness"] = freshness_by_slug[slug]

    # Weighted total
    total = int(
        (freshness_score * 0.3) + (cohesion_score * 0.4) + (modernity_score * 0.3)
    )

    return {
        "score": {
            "total": total,
            "freshness": freshness_score,
            "cohesion": cohesion_score,
            "modernity": modernity_score,
        },
        "packages_total": len(packages),
        "packages_matched": len(matched_map),
        "matched": matched_packages,
        "unmatched": unmatched_packages,
        "cohesion_details": cohesion_details,
        "modernity_details": modernity_details,
        "manifest_type": manifest_type,
    }


async def save_analysis(db, user_id, session_id, manifest_type, result: dict):
    """Persist an analysis for rate limiting and history."""
    await db.execute(
        """INSERT INTO dependency_analyses
           (user_id, session_id, manifest_type, package_count,
            score_freshness, score_cohesion, score_modernity, score_total,
            results_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            session_id,
            manifest_type,
            result["packages_total"],
            result["score"]["freshness"],
            result["score"]["cohesion"],
            result["score"]["modernity"],
            result["score"]["total"],
            json.dumps(result, default=str),
        ),
    )
    await db.commit()


async def count_analyses(db, user_id=None, session_id=None) -> int:
    """Count analyses this month for rate limiting."""
    if user_id:
        c = await db.execute(
            """SELECT COUNT(*) FROM dependency_analyses
               WHERE user_id = ? AND created_at > datetime('now', '-30 days')""",
            (user_id,),
        )
    elif session_id:
        c = await db.execute(
            """SELECT COUNT(*) FROM dependency_analyses
               WHERE session_id = ? AND created_at > datetime('now', '-30 days')""",
            (session_id,),
        )
    else:
        return 0
    return (await c.fetchone())[0]

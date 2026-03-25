"""
Lighthouse for Dependencies — scoring engine.

Parses package.json / requirements.txt manifests, matches packages
to IndieStack tools, and returns a 0-100 Project Intelligence Score.
"""

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx

log = logging.getLogger(__name__)


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

    if not remaining:
        return matched

    # Strategy 3: npm/PyPI registry lookup → GitHub URL → existing tool match
    # Then auto-ingest remaining as reference tools
    await _match_by_registry(db, remaining, matched, manifest_type)
    await _auto_ingest_reference(db, remaining, matched, manifest_type)

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

    # Pick best match: prefer tools whose slug/name is related to the package
    for pkg_name, tools in candidates.items():
        # Filter out obviously unrelated matches (bad sdk_packages data)
        pkg_stem = pkg_name.replace("-", "").replace("_", "").replace("@", "").replace("/", "").lower()
        related = [
            t for t in tools
            if pkg_stem in t["slug"].replace("-", "").lower()
            or t["slug"].replace("-", "").lower() in pkg_stem
            or pkg_stem in t["name"].replace("-", "").replace(" ", "").lower()
        ]
        if not related:
            continue  # skip entirely — no credible match

        if len(related) == 1:
            best = related[0]
        else:
            best = related[0]
            for t in related:
                if t["slug"] == pkg_name:
                    best = t
                    break
                if t["slug"] in pkg_name or pkg_name in t["slug"]:
                    best = t
                    break
        matched[pkg_name] = best
        remaining.discard(pkg_name)
        remaining_lower.discard(pkg_name)


# ── Registry fallback ────────────────────────────────────────────────────────

_REGISTRY_CLIENT: httpx.AsyncClient | None = None


def _get_registry_client() -> httpx.AsyncClient:
    global _REGISTRY_CLIENT
    if _REGISTRY_CLIENT is None or _REGISTRY_CLIENT.is_closed:
        _REGISTRY_CLIENT = httpx.AsyncClient(timeout=5.0, follow_redirects=True)
    return _REGISTRY_CLIENT


async def _match_by_registry(db, remaining: set, matched: dict, manifest_type: str):
    """
    For unmatched packages, query npm/PyPI to find the GitHub URL,
    then match against tools.github_url. Persist new mappings to sdk_packages.
    """
    if not remaining:
        return

    # Limit registry lookups per analysis to avoid slowing things down
    to_lookup = list(remaining)[:20]
    client = _get_registry_client()
    pkg_key = "npm" if manifest_type == "package.json" else "pip"

    for pkg_name in to_lookup:
        if pkg_name not in remaining:  # might have been matched during loop
            continue

        try:
            github_url = await _resolve_github_url(client, pkg_name, manifest_type)
        except Exception:
            continue

        if not github_url:
            continue

        # Extract owner/repo
        m = re.match(r"https?://github\.com/([^/]+)/([^/?#]+)", github_url)
        if not m:
            continue
        owner_repo = f"{m.group(1)}/{m.group(2).rstrip('.git')}"

        # Look up in tools by github_url
        c = await db.execute(
            """SELECT id, name, slug, category_id, upvote_count,
                      health_status, github_last_commit, github_is_archived,
                      github_stars
               FROM tools
               WHERE github_url LIKE ? AND status = 'approved'
               LIMIT 1""",
            (f"%{owner_repo}%",),
        )
        row = await c.fetchone()
        if not row:
            continue

        tool = row if isinstance(row, dict) else dict(row)

        # Validate: tool name/slug should be related to the package name
        # Prevents false matches like eslint → Greaterwms via shared GitHub org
        pkg_stem = pkg_name.split("/")[-1].replace("-", "").replace("_", "").lower()
        tool_slug = tool["slug"].replace("-", "").lower()
        tool_name = tool["name"].replace("-", "").replace(" ", "").lower()
        if pkg_stem not in tool_slug and pkg_stem not in tool_name and tool_slug not in pkg_stem:
            continue  # skip unrelated match

        matched[pkg_name] = tool
        remaining.discard(pkg_name)

        # Persist the mapping so we don't hit the registry next time
        await _persist_sdk_mapping(db, tool["id"], pkg_key, pkg_name)


async def _resolve_github_url(client: httpx.AsyncClient, pkg_name: str, manifest_type: str) -> str | None:
    """Resolve a package name to its GitHub URL via npm/PyPI registry."""
    if manifest_type == "package.json":
        return await _resolve_npm(client, pkg_name)
    else:
        return await _resolve_pypi(client, pkg_name)


async def _resolve_npm(client: httpx.AsyncClient, pkg_name: str) -> str | None:
    """Query npm registry for a package's GitHub URL."""
    try:
        # Full metadata needed — abbreviated strips repository field
        resp = await client.get(
            f"https://registry.npmjs.org/{pkg_name}",
            headers={"Accept": "application/json"},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        repo = data.get("repository", {})
        if isinstance(repo, dict):
            url = repo.get("url", "")
        elif isinstance(repo, str):
            url = repo
        else:
            return None
        # Clean up git+https://github.com/foo/bar.git → https://github.com/foo/bar
        url = url.replace("git+", "").replace("git://", "https://").rstrip(".git")
        if "github.com" in url:
            return url
    except Exception:
        pass
    return None


async def _resolve_pypi(client: httpx.AsyncClient, pkg_name: str) -> str | None:
    """Query PyPI for a package's GitHub URL."""
    try:
        resp = await client.get(f"https://pypi.org/pypi/{pkg_name}/json")
        if resp.status_code != 200:
            return None
        data = resp.json()
        info = data.get("info", {})
        # Check project_urls first
        urls = info.get("project_urls") or {}
        for key in ("Source", "Source Code", "Repository", "GitHub", "Code", "Homepage"):
            url = urls.get(key, "")
            if "github.com" in url:
                return url
        # Fallback to home_page
        hp = info.get("home_page", "")
        if "github.com" in hp:
            return hp
    except Exception:
        pass
    return None


async def _persist_sdk_mapping(db, tool_id: int, pkg_key: str, pkg_name: str):
    """Save a discovered package→tool mapping back to sdk_packages."""
    try:
        c = await db.execute("SELECT sdk_packages FROM tools WHERE id = ?", (tool_id,))
        row = await c.fetchone()
        current = (row.get("sdk_packages") if isinstance(row, dict) else row[0]) if row else None

        if current:
            try:
                parsed = json.loads(current)
            except (json.JSONDecodeError, TypeError):
                parsed = {}
        else:
            parsed = {}

        # Ensure it's a dict format for structured storage
        if isinstance(parsed, list):
            # Convert old array format to dict, preserving existing
            parsed = {pkg_key: parsed[0] if parsed else pkg_name}

        if isinstance(parsed, dict):
            if pkg_key not in parsed:
                parsed[pkg_key] = pkg_name
                await db.execute(
                    "UPDATE tools SET sdk_packages = ? WHERE id = ?",
                    (json.dumps(parsed), tool_id),
                )
                await db.commit()
                log.info(f"Persisted sdk_packages mapping: {pkg_name} -> tool {tool_id}")
    except Exception as e:
        log.debug(f"Failed to persist sdk_packages for tool {tool_id}: {e}")


# ── Auto-ingestion of reference tools ────────────────────────────────────────

async def _auto_ingest_reference(db, remaining: set, matched: dict, manifest_type: str):
    """
    For packages still unmatched after all strategies, fetch from npm/PyPI
    registries and auto-create as reference tools (is_reference=1).
    These don't appear in browse/search but power the dependency scorer.
    """
    if not remaining:
        return

    to_fetch = list(remaining)[:30]  # cap to keep latency under control
    client = _get_registry_client()

    async def _fetch_one(pkg: str) -> tuple[str, dict | None]:
        try:
            if manifest_type == "package.json":
                resp = await client.get(
                    f"https://registry.npmjs.org/{pkg}",
                    headers={"Accept": "application/json"},
                )
            else:
                resp = await client.get(f"https://pypi.org/pypi/{pkg}/json")
            if resp.status_code == 200:
                return pkg, resp.json()
        except Exception:
            pass
        return pkg, None

    # Parallel fetch with 3s timeout per request (client already has 5s)
    import asyncio
    results = await asyncio.gather(*[_fetch_one(p) for p in to_fetch])

    for pkg, data in results:
        if not data or pkg not in remaining:
            continue

        # Parse registry response
        if manifest_type == "package.json":
            name = data.get("name", pkg)
            desc = (data.get("description") or "")[:200]
            last_modified = (data.get("time") or {}).get("modified")
            slug = f"npm-{pkg.replace('/', '-').replace('@', '')}"
            sdk_json = json.dumps({"npm": pkg})
            github_url = ""
            repo = data.get("repository", {})
            if isinstance(repo, dict):
                github_url = (repo.get("url") or "").replace("git+", "").replace("git://", "https://").rstrip(".git")
            elif isinstance(repo, str):
                github_url = repo.replace("git+", "").replace("git://", "https://").rstrip(".git")
            if "github.com" not in github_url:
                github_url = ""
        else:
            info = data.get("info", {})
            name = info.get("name", pkg)
            desc = (info.get("summary") or "")[:200]
            urls_list = data.get("urls") or []
            last_modified = urls_list[-1]["upload_time"] if urls_list else None
            slug = f"pypi-{pkg.replace('-', '_')}"
            sdk_json = json.dumps({"pip": pkg})
            github_url = ""
            project_urls = info.get("project_urls") or {}
            for key in ("Source", "Source Code", "Repository", "GitHub", "Homepage"):
                url = project_urls.get(key, "")
                if "github.com" in url:
                    github_url = url
                    break
            if not github_url:
                hp = info.get("home_page") or ""
                if "github.com" in hp:
                    github_url = hp

        # Auto-ingest as reference tool
        try:
            await db.execute("""
                INSERT OR IGNORE INTO tools
                (name, slug, tagline, description, url, github_url,
                 github_last_commit, is_reference, sdk_packages, status,
                 category_id, source_type, health_status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, 'approved', 18, 'code', 'alive')
            """, (
                name, slug, desc[:100], desc, github_url or "",
                github_url, last_modified, sdk_json,
            ))
            await db.commit()
        except Exception:
            continue

        # Fetch the inserted row to add to matched
        c = await db.execute(
            """SELECT id, name, slug, category_id, upvote_count,
                      health_status, github_last_commit, github_is_archived,
                      github_stars
               FROM tools WHERE slug = ? LIMIT 1""",
            (slug,),
        )
        row = await c.fetchone()
        if row:
            tool = row if isinstance(row, dict) else dict(row)
            matched[pkg] = tool
            remaining.discard(pkg)


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

        if t.get("github_is_archived"):
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
        elif t.get("health_status") == "dead":
            tool_score, status = 10, "dormant"

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
    Uses Graph Density Quotient: base 60 + bonus from known pairs + cooccurrences.
    """
    if len(mapped_tools) < 2:
        return 90, []

    n = len(mapped_tools)
    slugs = [t["slug"] for t in mapped_tools]
    placeholders = ",".join(["?"] * len(slugs))

    # Check explicit tool_pairs (curated compatibility data)
    query = f"""
        SELECT tool_a_slug, tool_b_slug, success_count
        FROM tool_pairs
        WHERE tool_a_slug IN ({placeholders}) AND tool_b_slug IN ({placeholders})
    """
    explicit_pairs = []
    async with db.execute(query, slugs + slugs) as cursor:
        explicit_pairs = [r if isinstance(r, dict) else dict(r) for r in await cursor.fetchall()]

    # Check manifest cooccurrences (implicit pairs from other manifests)
    cooccurrence_count = 0
    try:
        query = f"""
            SELECT COUNT(*) as cnt FROM manifest_cooccurrences
            WHERE tool_a_slug IN ({placeholders}) AND tool_b_slug IN ({placeholders})
              AND cooccurrence_count >= 2
        """
        c = await db.execute(query, slugs + slugs)
        row = await c.fetchone()
        cooccurrence_count = (row["cnt"] if isinstance(row, dict) else row[0]) if row else 0
    except Exception:
        pass  # table might not exist yet

    # Count verified compatible pairs
    compatible = sum(1 for p in explicit_pairs if p["success_count"] > 0)
    conflicts = [p for p in explicit_pairs if p["success_count"] < 0]
    total_known_pairs = compatible + cooccurrence_count

    details = []
    for pair in explicit_pairs:
        if pair["success_count"] > 0:
            details.append({
                "a": pair["tool_a_slug"],
                "b": pair["tool_b_slug"],
                "status": "compatible",
                "evidence": pair["success_count"],
            })
        elif pair["success_count"] < 0:
            details.append({
                "a": pair["tool_a_slug"],
                "b": pair["tool_b_slug"],
                "status": "conflict",
                "evidence": pair["success_count"],
            })

    # Graph Density Quotient: base 60, bonus up to 40 from known pairs
    # P/N * 15, capped at 40
    bonus = min(40, int((total_known_pairs / max(n, 1)) * 15))
    score = 60 + bonus

    # Strict penalty for known conflicts
    score -= len(conflicts) * 20

    return max(0, min(100, score)), details


async def calculate_modernity(db, mapped_tools: list[dict]) -> tuple[int, list[dict]]:
    """
    Modernity score (0-100): are there better alternatives to your dependencies?
    Checks if tools in the same category have significantly more traction.
    """
    if not mapped_tools:
        return 0, []

    mapped_slugs = {t["slug"] for t in mapped_tools}
    mapped_ids = [t["id"] for t in mapped_tools]

    deductions = 0
    details = []

    for t in mapped_tools:
        tool_id = t.get("id")
        if not tool_id:
            continue

        # Find competitors in the SAME PRIMARY category only (most precise)
        # Skip mega-category "Developer Tools" (id=18) — too broad for meaningful comparison
        cat_id = t.get("category_id")
        if not cat_id or cat_id == 18:
            continue
        query = """
            SELECT t2.slug, t2.name, t2.upvote_count, t2.github_stars,
                   t2.github_last_commit
            FROM tools t2
            WHERE t2.category_id = ?
              AND t2.id != ?
              AND t2.status = 'approved'
              AND t2.health_status IN ('alive', 'unknown')
              AND t2.github_last_commit > datetime('now', '-6 months')
            ORDER BY (COALESCE(t2.github_stars, 0) + COALESCE(t2.upvote_count, 0) * 100) DESC
            LIMIT 15
        """
        competitors = []
        try:
            async with db.execute(query, (cat_id, tool_id)) as cursor:
                competitors = [r if isinstance(r, dict) else dict(r) for r in await cursor.fetchall()]
        except Exception:
            # Fallback if tool_categories table doesn't exist yet
            continue

        # Only suggest alternatives with 3x traction AND >500 combined score
        t_traction = (t.get("github_stars") or 0) + (t.get("upvote_count") or 0) * 100
        better = []
        for c in competitors:
            if c["slug"] in mapped_slugs:
                continue
            c_traction = (c.get("github_stars") or 0) + (c.get("upvote_count") or 0) * 100
            if c_traction > t_traction * 3 and c_traction > 500:
                better.append(c)
            if len(better) >= 3:
                break

        if better:
            deductions += 10
            details.append({
                "slug": t["slug"],
                "name": t["name"],
                "alternatives": [
                    {"slug": b["slug"], "name": b["name"]}
                    for b in better
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

    # 5. Mine implicit cohesion from this manifest (background, non-blocking)
    await _mine_cooccurrences(db, mapped_tools)

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


async def _mine_cooccurrences(db, mapped_tools: list[dict]):
    """Record implicit compatibility pairs from manifests that contain these tools together."""
    if len(mapped_tools) < 2:
        return
    from itertools import combinations
    slugs = sorted(t["slug"] for t in mapped_tools)
    # Cap pairs to avoid O(n^2) explosion for huge manifests
    if len(slugs) > 50:
        slugs = slugs[:50]
    pairs = list(combinations(slugs, 2))
    try:
        await db.executemany(
            """INSERT INTO manifest_cooccurrences (tool_a_slug, tool_b_slug, cooccurrence_count)
               VALUES (?, ?, 1)
               ON CONFLICT(tool_a_slug, tool_b_slug)
               DO UPDATE SET cooccurrence_count = cooccurrence_count + 1""",
            pairs,
        )
        await db.commit()
    except Exception as e:
        log.debug(f"Cooccurrence mining failed: {e}")


async def save_analysis(db, user_id, session_id, manifest_type, result: dict) -> str:
    """Persist an analysis for rate limiting and history. Returns share_uuid."""
    import secrets
    share_uuid = secrets.token_urlsafe(8)
    await db.execute(
        """INSERT INTO dependency_analyses
           (user_id, session_id, share_uuid, manifest_type, package_count,
            score_freshness, score_cohesion, score_modernity, score_total,
            results_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            user_id,
            session_id,
            share_uuid,
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
    return share_uuid


async def load_analysis(db, share_uuid: str) -> dict | None:
    """Load a cached analysis by share UUID."""
    c = await db.execute(
        "SELECT results_json, created_at FROM dependency_analyses WHERE share_uuid = ?",
        (share_uuid,),
    )
    row = await c.fetchone()
    if not row:
        return None
    result = json.loads(row["results_json"])
    result["created_at"] = row["created_at"]
    return result


async def count_analyses(db, user_id=None, session_id=None) -> int:
    """Count analyses this month for rate limiting."""
    if user_id:
        c = await db.execute(
            """SELECT COUNT(*) as cnt FROM dependency_analyses
               WHERE user_id = ? AND created_at > datetime('now', '-30 days')""",
            (user_id,),
        )
    elif session_id:
        c = await db.execute(
            """SELECT COUNT(*) as cnt FROM dependency_analyses
               WHERE session_id = ? AND created_at > datetime('now', '-30 days')""",
            (session_id,),
        )
    else:
        return 0
    row = await c.fetchone()
    return row["cnt"] if row else 0

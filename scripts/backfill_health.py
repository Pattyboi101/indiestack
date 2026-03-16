"""
One-off script to backfill health_status for ~895 approved tools with unknown health.

Usage:
    cd /app && python3 scripts/backfill_health.py
    python3 scripts/backfill_health.py /path/to/db
"""

import asyncio
import os
import re
import sys

import aiosqlite
import httpx


DB_PATH = (
    sys.argv[1] if len(sys.argv) > 1
    else os.environ.get("INDIESTACK_DB_PATH", "/data/indiestack.db")
)

GITHUB_BATCH = 500
SAAS_BATCH = 500
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


async def backfill_github(db: aiosqlite.Connection) -> dict:
    """Check GitHub repos for tools with unknown health status."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    cursor = await db.execute("""
        SELECT id, github_url FROM tools
        WHERE status = 'approved'
          AND github_url IS NOT NULL AND github_url != ''
          AND (health_status IS NULL OR health_status = 'unknown')
        ORDER BY id
        LIMIT ?
    """, (GITHUB_BATCH,))
    tools = await cursor.fetchall()

    stats = {"total": len(tools), "alive": 0, "dead": 0, "errors": 0, "rate_limited": False}
    print(f"[GitHub] Found {len(tools)} tools to check")

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for i, tool in enumerate(tools):
            tool_id = tool["id"]
            github_url = tool["github_url"]

            match = re.match(r"https?://github\.com/([^/]+)/([^/?#]+)", github_url)
            if not match:
                stats["errors"] += 1
                continue

            owner, repo = match.group(1), match.group(2).rstrip(".git")
            api_url = f"https://api.github.com/repos/{owner}/{repo}"

            try:
                resp = await client.get(api_url, headers=headers)

                if resp.status_code == 403:
                    remaining = resp.headers.get("x-ratelimit-remaining", "?")
                    print(f"[GitHub] Rate limited after {i} checks (remaining: {remaining}). Stopping.")
                    stats["rate_limited"] = True
                    break

                if resp.status_code == 404:
                    await db.execute("""
                        UPDATE tools SET
                            health_status = 'dead',
                            last_health_check = datetime('now'),
                            github_last_check = datetime('now')
                        WHERE id = ?
                    """, (tool_id,))
                    stats["dead"] += 1
                    continue

                if resp.status_code != 200:
                    stats["errors"] += 1
                    continue

                data = resp.json()
                stars = data.get("stargazers_count", 0)
                open_issues = data.get("open_issues_count", 0)
                is_archived = 1 if data.get("archived", False) else 0
                language = data.get("language", "") or ""
                pushed_at = data.get("pushed_at", "")

                health = "dead" if is_archived else "alive"

                await db.execute("""
                    UPDATE tools SET
                        github_stars = ?,
                        github_open_issues = ?,
                        github_is_archived = ?,
                        github_language = ?,
                        github_last_commit = ?,
                        github_last_check = datetime('now'),
                        health_status = ?,
                        last_health_check = datetime('now')
                    WHERE id = ?
                """, (stars, open_issues, is_archived, language, pushed_at, health, tool_id))

                if health == "alive":
                    stats["alive"] += 1
                else:
                    stats["dead"] += 1

            except Exception as e:
                stats["errors"] += 1
                if i < 3:
                    print(f"  Error on {owner}/{repo}: {e}")

            if (i + 1) % 50 == 0:
                await db.commit()
                print(f"  [{i + 1}/{len(tools)}] alive={stats['alive']} dead={stats['dead']} errors={stats['errors']}")

    await db.commit()
    return stats


async def backfill_saas(db: aiosqlite.Connection) -> dict:
    """HTTP HEAD check for SaaS tools with no GitHub URL."""
    cursor = await db.execute("""
        SELECT id, url, name FROM tools
        WHERE status = 'approved'
          AND (github_url IS NULL OR github_url = '')
          AND (health_status IS NULL OR health_status = 'unknown')
          AND url IS NOT NULL AND url != ''
        ORDER BY id
        LIMIT ?
    """, (SAAS_BATCH,))
    tools = await cursor.fetchall()

    stats = {"total": len(tools), "alive": 0, "dead": 0, "errors": 0}
    print(f"[SaaS] Found {len(tools)} tools to check")

    async with httpx.AsyncClient(
        timeout=10.0,
        follow_redirects=True,
        headers={"User-Agent": "IndieStack-HealthCheck/1.0"}
    ) as client:
        for i, tool in enumerate(tools):
            tool_id = tool["id"]
            url = tool["url"]

            try:
                resp = await client.head(url)
                if resp.status_code < 400:
                    health = "alive"
                    stats["alive"] += 1
                else:
                    health = "dead"
                    stats["dead"] += 1
            except Exception:
                health = "dead"
                stats["dead"] += 1

            await db.execute("""
                UPDATE tools SET
                    health_status = ?,
                    last_health_check = datetime('now')
                WHERE id = ?
            """, (health, tool_id))

            if (i + 1) % 50 == 0:
                await db.commit()
                print(f"  [{i + 1}/{len(tools)}] alive={stats['alive']} dead={stats['dead']}")

    await db.commit()
    return stats


async def main():
    print(f"Backfill health data — DB: {DB_PATH}")
    print("=" * 60)

    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row

    # Before stats
    cursor = await db.execute("""
        SELECT health_status, COUNT(*) as cnt
        FROM tools WHERE status = 'approved'
        GROUP BY health_status
    """)
    before = {row["health_status"] or "NULL": row["cnt"] for row in await cursor.fetchall()}
    print(f"BEFORE: {dict(before)}")
    print()

    # Run checks
    gh_stats = await backfill_github(db)
    print(f"[GitHub] Done: {gh_stats}")
    print()

    saas_stats = await backfill_saas(db)
    print(f"[SaaS] Done: {saas_stats}")
    print()

    # After stats
    cursor = await db.execute("""
        SELECT health_status, COUNT(*) as cnt
        FROM tools WHERE status = 'approved'
        GROUP BY health_status
    """)
    after = {row["health_status"] or "NULL": row["cnt"] for row in await cursor.fetchall()}
    print(f"AFTER:  {dict(after)}")
    print()

    # Recompute quality scores
    print("Recomputing quality scores...")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
    from indiestack.db import recompute_all_quality_scores
    result = await recompute_all_quality_scores(db)
    print(f"Quality scores updated: {result}")

    await db.close()
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())

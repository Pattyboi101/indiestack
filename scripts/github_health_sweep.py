#!/usr/bin/env python3
"""
Bulk GitHub health sweep — update github_last_commit, stars, archived status
for all approved tools with a GitHub URL.

Prioritizes tools with NO commit data (656 at time of writing), then stale data.
Uses GITHUB_TOKEN for 5,000 req/hr. Concurrent with semaphore.

Usage:
    GITHUB_TOKEN=ghp_xxx python3 scripts/github_health_sweep.py [--all]

    --all    Check ALL tools (not just missing data)
"""

import asyncio
import os
import re
import sys
import time

import aiosqlite
import httpx

DB_PATH = os.environ.get("DB_PATH", "backups/" + max(
    (f for f in os.listdir("backups") if f.startswith("indiestack-")),
    default="indiestack.db"
)) if os.path.isdir("backups") else "indiestack.db"

TOKEN = os.environ.get("GITHUB_TOKEN", "")
CONCURRENCY = 15  # parallel requests
RATE_PAUSE = 1.0  # seconds between batches


async def get_tools_to_check(db, check_all: bool) -> list[dict]:
    """Get tools that need health checks."""
    if check_all:
        query = """
            SELECT id, slug, github_url FROM tools
            WHERE status = 'approved'
              AND github_url IS NOT NULL AND github_url != ''
            ORDER BY github_last_commit ASC NULLS FIRST
        """
    else:
        # Prioritize: no commit data first, then oldest checks
        query = """
            SELECT id, slug, github_url FROM tools
            WHERE status = 'approved'
              AND github_url IS NOT NULL AND github_url != ''
              AND (github_last_commit IS NULL
                   OR github_last_check IS NULL
                   OR github_last_check < datetime('now', '-7 days'))
            ORDER BY github_last_commit ASC NULLS FIRST
        """
    cursor = await db.execute(query)
    return [dict(r) for r in await cursor.fetchall()]


def parse_github_url(url: str) -> tuple[str, str] | None:
    """Extract owner/repo from a GitHub URL."""
    m = re.match(r"https?://github\.com/([^/]+)/([^/?#]+)", url)
    if not m:
        return None
    return m.group(1), m.group(2).rstrip(".git")


async def check_tool(client: httpx.AsyncClient, headers: dict, tool: dict, sem: asyncio.Semaphore) -> dict | None:
    """Check a single tool's GitHub health. Returns update dict or None."""
    parsed = parse_github_url(tool["github_url"])
    if not parsed:
        return None

    owner, repo = parsed
    api_url = f"https://api.github.com/repos/{owner}/{repo}"

    async with sem:
        try:
            resp = await client.get(api_url, headers=headers)
        except Exception as e:
            return {"id": tool["id"], "error": str(e)}

    if resp.status_code == 403:
        # Rate limited — check headers
        remaining = resp.headers.get("x-ratelimit-remaining", "?")
        reset = resp.headers.get("x-ratelimit-reset", "")
        return {"id": tool["id"], "rate_limited": True, "remaining": remaining, "reset": reset}

    if resp.status_code == 404:
        return {
            "id": tool["id"],
            "slug": tool["slug"],
            "health_status": "dead",
            "github_is_archived": 0,
            "github_stars": 0,
            "github_last_commit": None,
        }

    if resp.status_code != 200:
        return {"id": tool["id"], "error": f"HTTP {resp.status_code}"}

    data = resp.json()
    return {
        "id": tool["id"],
        "slug": tool["slug"],
        "github_stars": data.get("stargazers_count", 0),
        "github_open_issues": data.get("open_issues_count", 0),
        "github_is_archived": 1 if data.get("archived", False) else 0,
        "github_language": data.get("language", "") or "",
        "github_last_commit": data.get("pushed_at", ""),
        "health_status": "dead" if data.get("archived") else "alive",
    }


async def apply_updates(db, results: list[dict]) -> dict:
    """Apply health check results to the database."""
    stats = {"updated": 0, "dead": 0, "errors": 0, "rate_limited": False}

    for r in results:
        if not r:
            continue
        if r.get("rate_limited"):
            stats["rate_limited"] = True
            break
        if r.get("error"):
            stats["errors"] += 1
            continue

        await db.execute("""
            UPDATE tools SET
                github_stars = ?,
                github_open_issues = ?,
                github_is_archived = ?,
                github_language = ?,
                github_last_commit = ?,
                github_last_check = datetime('now'),
                health_status = ?
            WHERE id = ?
        """, (
            r.get("github_stars", 0),
            r.get("github_open_issues", 0),
            r.get("github_is_archived", 0),
            r.get("github_language", ""),
            r.get("github_last_commit"),
            r.get("health_status", "unknown"),
            r["id"],
        ))

        if r.get("health_status") == "dead":
            stats["dead"] += 1
        stats["updated"] += 1

    await db.commit()
    return stats


async def main():
    check_all = "--all" in sys.argv

    if not TOKEN:
        print("WARNING: No GITHUB_TOKEN set. Limited to 60 requests/hour.")
        print("Set it: GITHUB_TOKEN=ghp_xxx python3 scripts/github_health_sweep.py")

    headers = {"Accept": "application/vnd.github.v3+json"}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"

    def _dict_factory(cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = _dict_factory
        tools = await get_tools_to_check(db, check_all)
        total = len(tools)
        print(f"Found {total} tools to check (db: {DB_PATH})")

        if not tools:
            print("Nothing to check!")
            return

        sem = asyncio.Semaphore(CONCURRENCY)
        totals = {"updated": 0, "dead": 0, "errors": 0}

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # Process in batches to respect rate limits
            batch_size = 100
            for i in range(0, total, batch_size):
                batch = tools[i:i + batch_size]
                tasks = [check_tool(client, headers, t, sem) for t in batch]
                results = await asyncio.gather(*tasks)

                stats = await apply_updates(db, results)
                totals["updated"] += stats["updated"]
                totals["dead"] += stats["dead"]
                totals["errors"] += stats["errors"]

                done = min(i + batch_size, total)
                print(f"  [{done}/{total}] updated={totals['updated']} dead={totals['dead']} errors={totals['errors']}")

                if stats["rate_limited"]:
                    print("  RATE LIMITED — stopping. Run again later or set GITHUB_TOKEN.")
                    break

                # Brief pause between batches
                if done < total:
                    await asyncio.sleep(RATE_PAUSE)

        print(f"\nDone! Updated: {totals['updated']}, Dead: {totals['dead']}, Errors: {totals['errors']}")


if __name__ == "__main__":
    asyncio.run(main())

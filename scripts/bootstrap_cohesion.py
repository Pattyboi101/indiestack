#!/usr/bin/env python3
"""
Bootstrap manifest_cooccurrences by analyzing package.json files
from top GitHub repositories. Seeds the Waze data moat.

Usage:
    GITHUB_TOKEN=ghp_xxx python3 scripts/bootstrap_cohesion.py [--count 100]
"""

import asyncio
import json
import os
import sys
import time

import aiosqlite
import httpx

TOKEN = os.environ.get("GITHUB_TOKEN", "")
DB_PATH = os.environ.get("DB_PATH", "")

# Top repos to analyze — mix of frameworks, templates, and real apps
# These seed the cooccurrence graph with real-world pairs
SEED_QUERIES = [
    "nextjs template",
    "react starter",
    "vue template",
    "express api",
    "fastapi template",
    "django starter",
    "svelte template",
    "nuxt template",
    "remix template",
    "t3 stack",
    "fullstack typescript",
    "node api boilerplate",
    "python web app",
    "flask starter",
    "tailwind dashboard",
]


async def fetch_trending_repos(client: httpx.AsyncClient, count: int) -> list[dict]:
    """Fetch popular repos via GitHub search API."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"

    repos = []
    seen = set()

    for query in SEED_QUERIES:
        if len(repos) >= count:
            break
        try:
            resp = await client.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "sort": "stars", "per_page": 15},
                headers=headers,
            )
            if resp.status_code != 200:
                print(f"  Search '{query}' failed: {resp.status_code}")
                continue
            for item in resp.json().get("items", []):
                full_name = item["full_name"]
                if full_name not in seen:
                    seen.add(full_name)
                    repos.append({
                        "full_name": full_name,
                        "default_branch": item.get("default_branch", "main"),
                        "stars": item.get("stargazers_count", 0),
                    })
        except Exception as e:
            print(f"  Search '{query}' error: {e}")
        await asyncio.sleep(0.5)  # respect rate limits

    return repos[:count]


async def fetch_manifest(client: httpx.AsyncClient, repo: dict) -> tuple[str, str] | None:
    """Try to fetch package.json or requirements.txt from a repo."""
    full_name = repo["full_name"]
    branch = repo["default_branch"]

    for fname, mtype in [("package.json", "package.json"), ("requirements.txt", "requirements.txt")]:
        url = f"https://raw.githubusercontent.com/{full_name}/{branch}/{fname}"
        try:
            resp = await client.get(url)
            if resp.status_code == 200 and len(resp.text) > 10:
                return resp.text, mtype
        except Exception:
            pass
    return None


async def main():
    count = 100
    if "--count" in sys.argv:
        idx = sys.argv.index("--count")
        count = int(sys.argv[idx + 1])

    if not TOKEN:
        print("WARNING: No GITHUB_TOKEN. Limited to 10 requests/minute.")

    # Find DB
    db_path = DB_PATH
    if not db_path:
        import glob
        backups = sorted(glob.glob("backups/indiestack-*.db"))
        db_path = backups[-1] if backups else "indiestack.db"

    def _dict_factory(cursor, row):
        return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    print(f"Bootstrapping cohesion from top {count} repos (db: {db_path})")

    async with aiosqlite.connect(db_path) as db:
        db.row_factory = _dict_factory
        await db.execute("PRAGMA journal_mode=WAL")

        # Ensure tables exist
        await db.execute("""
            CREATE TABLE IF NOT EXISTS manifest_cooccurrences (
                tool_a_slug TEXT NOT NULL, tool_b_slug TEXT NOT NULL,
                cooccurrence_count INTEGER DEFAULT 1,
                PRIMARY KEY (tool_a_slug, tool_b_slug))
        """)
        try:
            await db.execute("ALTER TABLE tools ADD COLUMN is_reference INTEGER DEFAULT 0")
        except Exception:
            pass
        await db.commit()

        # Add analyze.py to path
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
        from indiestack.analyze import run_analysis

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            # Step 1: Find repos
            print("Searching for repos...")
            repos = await fetch_trending_repos(client, count)
            print(f"Found {len(repos)} repos")

            # Step 2: Fetch and analyze manifests
            analyzed = 0
            failed = 0
            total_pairs = 0

            for i, repo in enumerate(repos):
                result = await fetch_manifest(client, repo)
                if not result:
                    failed += 1
                    continue

                manifest, manifest_type = result
                try:
                    analysis = await run_analysis(db, manifest, manifest_type)
                    matched = analysis["packages_matched"]
                    score = analysis["score"]["total"]
                    analyzed += 1

                    # Count new cooccurrences
                    if matched >= 2:
                        from itertools import combinations
                        pair_count = len(list(combinations(range(matched), 2)))
                        total_pairs += pair_count

                    print(f"  [{i+1}/{len(repos)}] {repo['full_name']} — {matched} deps, score {score}/100")
                except Exception as e:
                    failed += 1
                    print(f"  [{i+1}/{len(repos)}] {repo['full_name']} — ERROR: {e}")

                # Brief pause to avoid hammering registries
                if (i + 1) % 10 == 0:
                    await asyncio.sleep(1)

        # Report
        c = await db.execute("SELECT COUNT(*) as cnt FROM manifest_cooccurrences")
        row = await c.fetchone()
        cooccurrences = row["cnt"]

        c = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE is_reference = 1")
        row = await c.fetchone()
        ref_tools = row["cnt"]

        print(f"\nDone! Analyzed: {analyzed}, Failed: {failed}")
        print(f"Cooccurrence pairs in DB: {cooccurrences}")
        print(f"Reference tools created: {ref_tools}")


if __name__ == "__main__":
    asyncio.run(main())

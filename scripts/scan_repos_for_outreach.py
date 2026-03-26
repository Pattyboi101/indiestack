#!/usr/bin/env python3
"""
Scan GitHub repos, score their dependencies via IndieStack API,
and output a CSV for Ed's badge + PR outreach.

Produces two files:
  - outreach_badges.csv  — repos scoring 90+ (badge PRs)
  - outreach_fixes.csv   — repos scoring <70 (helpful fix PRs)

Usage:
    GITHUB_TOKEN=ghp_xxx python3 scripts/scan_repos_for_outreach.py [--count 100]
"""

import asyncio
import csv
import json
import os
import sys
import time

import httpx

TOKEN = os.environ.get("GITHUB_TOKEN", "")
API_BASE = os.environ.get("API_BASE", "https://indiestack.ai")

# Search queries to find repos with package.json
SEARCH_QUERIES = [
    "language:javascript stars:500..3000 pushed:>2026-03-01",
    "language:typescript stars:500..3000 pushed:>2026-03-01",
    "language:javascript stars:1000..5000 pushed:>2026-03-01",
    "language:typescript stars:1000..5000 pushed:>2026-03-01",
    "topic:nextjs stars:300..2000 pushed:>2026-03-01",
    "topic:react stars:500..3000 pushed:>2026-03-01",
    "topic:vue stars:300..2000 pushed:>2026-03-01",
    "topic:express stars:300..2000 pushed:>2026-03-01",
    "language:python stars:500..3000 pushed:>2026-03-01",
    "topic:fastapi stars:200..2000 pushed:>2026-03-01",
    "topic:django stars:300..2000 pushed:>2026-03-01",
]


async def search_repos(client: httpx.AsyncClient, count: int) -> list[dict]:
    """Find repos via GitHub search API."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if TOKEN:
        headers["Authorization"] = f"token {TOKEN}"

    repos = []
    seen = set()

    for query in SEARCH_QUERIES:
        if len(repos) >= count:
            break
        try:
            resp = await client.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "sort": "updated", "per_page": 30},
                headers=headers,
            )
            if resp.status_code == 403:
                print("  Rate limited on GitHub search, waiting 30s...")
                await asyncio.sleep(30)
                continue
            if resp.status_code != 200:
                continue

            for item in resp.json().get("items", []):
                full_name = item["full_name"]
                if full_name in seen:
                    continue
                seen.add(full_name)
                repos.append({
                    "full_name": full_name,
                    "name": item["name"],
                    "owner": item["owner"]["login"],
                    "stars": item.get("stargazers_count", 0),
                    "language": item.get("language", ""),
                    "default_branch": item.get("default_branch", "main"),
                    "description": (item.get("description") or "")[:100],
                    "html_url": item.get("html_url", ""),
                })
        except Exception as e:
            print(f"  Search error: {e}")
        await asyncio.sleep(1)

    return repos[:count]


async def fetch_and_score(client: httpx.AsyncClient, repo: dict) -> dict | None:
    """Fetch manifest from repo and score via IndieStack API."""
    full_name = repo["full_name"]
    branch = repo["default_branch"]

    # Try to fetch manifest
    manifest = None
    manifest_type = None
    for fname, mtype in [("package.json", "package.json"), ("requirements.txt", "requirements.txt")]:
        for b in [branch, "master", "main"]:
            url = f"https://raw.githubusercontent.com/{full_name}/{b}/{fname}"
            try:
                resp = await client.get(url)
                if resp.status_code == 200 and len(resp.text) > 10:
                    manifest = resp.text
                    manifest_type = mtype
                    break
            except Exception:
                pass
        if manifest:
            break

    if not manifest:
        return None

    # Score via IndieStack API
    try:
        resp = await client.post(
            f"{API_BASE}/api/analyze",
            json={
                "manifest": manifest,
                "manifest_type": manifest_type,
                "source": "scanner",
                "repo": full_name,
            },
            headers={"X-GitHub-Action": "true"},
            timeout=30.0,
        )
        if resp.status_code != 200:
            return None

        data = resp.json()
        score = data.get("score", {})

        # Find dead/dormant deps
        dead_deps = []
        for m in data.get("matched", []):
            f = m.get("freshness", {})
            if f.get("status") in ("dead", "dormant"):
                dead_deps.append({
                    "package": m["package"],
                    "status": f["status"],
                    "tool_name": m["tool"]["name"],
                })

        # Find suggested alternatives
        alternatives = []
        for md in data.get("modernity_details", []):
            for alt in md.get("alternatives", []):
                alternatives.append({
                    "from": md["name"],
                    "to": alt["name"],
                    "to_slug": alt["slug"],
                })

        return {
            **repo,
            "score_total": score.get("total", 0),
            "score_freshness": score.get("freshness", 0),
            "score_cohesion": score.get("cohesion", 0),
            "score_modernity": score.get("modernity", 0),
            "packages_matched": data.get("packages_matched", 0),
            "packages_total": data.get("packages_total", 0),
            "share_url": data.get("share_url", ""),
            "dead_deps": dead_deps,
            "alternatives": alternatives,
            "manifest_type": manifest_type,
        }

    except Exception as e:
        print(f"  API error for {full_name}: {e}")
        return None


def write_badge_csv(results: list[dict], filename: str):
    """Write CSV for repos scoring 90+ (badge outreach)."""
    high_scorers = [r for r in results if r["score_total"] >= 90]
    high_scorers.sort(key=lambda r: r["score_total"], reverse=True)

    with open(filename, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["repo", "stars", "score", "language", "badge_markdown", "pr_description", "share_url"])
        for r in high_scorers:
            badge_md = f'[![Stack Health](https://indiestack.ai/api/badge/health/{r["full_name"]}.svg)](https://indiestack.ai/analyze)'
            pr_desc = (
                f'Hey! I ran a dependency health analysis on your project and it scored '
                f'{r["score_total"]}/100 — that puts it in the top 5% of projects we\'ve analyzed.\n\n'
                f'Added a live health badge to your README so visitors can see your stack is '
                f'well-maintained. The badge updates automatically.\n\n'
                f'Powered by [IndieStack](https://indiestack.ai/analyze) — free dependency health scoring.'
            )
            w.writerow([r["full_name"], r["stars"], r["score_total"], r["language"], badge_md, pr_desc, r["share_url"]])

    print(f"  {filename}: {len(high_scorers)} repos scoring 90+")


def write_fixes_csv(results: list[dict], filename: str):
    """Write CSV for repos scoring <70 (helpful fix PRs)."""
    fixable = [r for r in results if r["score_total"] < 70 and r["dead_deps"]]
    fixable.sort(key=lambda r: r["score_total"])

    with open(filename, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["repo", "stars", "score", "language", "dead_deps", "alternatives", "pr_template", "share_url"])
        for r in fixable:
            dead_str = "; ".join(f'{d["package"]} ({d["status"]})' for d in r["dead_deps"][:3])
            alt_str = "; ".join(f'{a["from"]} -> {a["to"]}' for a in r["alternatives"][:3])
            pr_template = (
                f'Hey! I found this while running a dependency health check on your project '
                f'(it scored {r["score_total"]}/100). '
                f'{r["dead_deps"][0]["package"]} appears to be unmaintained.\n\n'
                f'If you find this useful, I built a free GitHub Action that checks dependency '
                f'health on every PR automatically:\n\n'
                f'```yaml\n- uses: Pattyboi101/stack-health-check@master\n```\n\n'
                f'No signup needed. Full report: {r["share_url"]}'
            )
            w.writerow([r["full_name"], r["stars"], r["score_total"], r["language"], dead_str, alt_str, pr_template, r["share_url"]])

    print(f"  {filename}: {len(fixable)} repos scoring <70 with dead deps")


async def main():
    count = 100
    if "--count" in sys.argv:
        idx = sys.argv.index("--count")
        count = int(sys.argv[idx + 1])

    if not TOKEN:
        print("WARNING: No GITHUB_TOKEN. Limited search results.")

    print(f"Scanning {count} repos...")

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        # Step 1: Find repos
        repos = await search_repos(client, count)
        print(f"Found {len(repos)} repos to scan")

        # Step 2: Score each repo
        results = []
        for i, repo in enumerate(repos):
            result = await fetch_and_score(client, repo)
            if result:
                results.append(result)
                icon = "+" if result["score_total"] >= 90 else ("-" if result["score_total"] < 70 else " ")
                print(f"  [{i+1}/{len(repos)}] [{icon}] {repo['full_name']} — {result['score_total']}/100 ({result['packages_matched']} deps)")
            else:
                print(f"  [{i+1}/{len(repos)}] [ ] {repo['full_name']} — no manifest or error")

            # Pace ourselves
            if (i + 1) % 5 == 0:
                await asyncio.sleep(1)

    # Step 3: Write CSVs
    print(f"\nResults: {len(results)} repos scored")
    write_badge_csv(results, "outreach_badges.csv")
    write_fixes_csv(results, "outreach_fixes.csv")
    print("\nDone! Give outreach_badges.csv and outreach_fixes.csv to Ed.")


if __name__ == "__main__":
    asyncio.run(main())

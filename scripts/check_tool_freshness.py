#!/usr/bin/env python3
"""Dead Tool Detector — checks GitHub repos for staleness and flags inactive tools.

Run via: flyctl ssh console -a indiestack -C "python3 scripts/check_tool_freshness.py"
Or locally: DATABASE_URL=/path/to/indiestack.db python3 scripts/check_tool_freshness.py
"""

import json
import os
import re
import sqlite3
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone


DB_PATH = os.environ.get("DATABASE_URL", os.environ.get("INDIESTACK_DB_PATH", "/data/indiestack.db"))
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Freshness thresholds (days)
ACTIVE_THRESHOLD = 90
STALE_THRESHOLD = 180

GITHUB_REPO_RE = re.compile(r"github\.com/([^/]+)/([^/?#]+)")


def ensure_columns(conn):
    """Add freshness columns if they don't exist."""
    cursor = conn.execute("PRAGMA table_info(tools)")
    columns = {row[1] for row in cursor.fetchall()}
    if "last_github_commit" not in columns:
        conn.execute("ALTER TABLE tools ADD COLUMN last_github_commit TIMESTAMP")
        print("  Added column: last_github_commit")
    if "github_freshness" not in columns:
        conn.execute("ALTER TABLE tools ADD COLUMN github_freshness TEXT")
        print("  Added column: github_freshness")
    conn.commit()


def extract_owner_repo(github_url):
    """Extract owner/repo from a GitHub URL."""
    if not github_url:
        return None, None
    m = GITHUB_REPO_RE.search(github_url)
    if not m:
        return None, None
    owner = m.group(1)
    repo = m.group(2)
    # Strip .git suffix if present
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo


def get_last_commit_date(owner, repo):
    """Fetch the last commit date from GitHub API. Returns (datetime, error_string)."""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=1"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "IndieStack-FreshnessChecker/1.0",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"token {GITHUB_TOKEN}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            # Check rate limit headers
            remaining = resp.headers.get("X-RateLimit-Remaining", "?")
            data = json.loads(resp.read().decode("utf-8"))
            if not data:
                return None, "empty_response"
            commit_date_str = data[0]["commit"]["committer"]["date"]
            # Parse ISO 8601 date (e.g. 2024-01-15T10:30:00Z)
            commit_date = datetime.fromisoformat(commit_date_str.replace("Z", "+00:00"))
            return commit_date, None
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None, "not_found"
        if e.code == 403:
            # Rate limited or forbidden
            return None, "rate_limited"
        if e.code == 301 or e.code == 302:
            return None, "moved"
        return None, f"http_{e.code}"
    except urllib.error.URLError as e:
        return None, f"url_error: {e.reason}"
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        return None, f"parse_error: {e}"
    except Exception as e:
        return None, f"error: {e}"


def classify_freshness(commit_date):
    """Classify freshness based on days since last commit."""
    if commit_date is None:
        return "unknown"
    now = datetime.now(timezone.utc)
    days = (now - commit_date).days
    if days < ACTIVE_THRESHOLD:
        return "active"
    elif days < STALE_THRESHOLD:
        return "stale"
    else:
        return "inactive"


def main():
    print(f"Dead Tool Detector")
    print(f"==================")
    print(f"Database: {DB_PATH}")
    print(f"GitHub token: {'set' if GITHUB_TOKEN else 'NOT SET (60 req/hr limit)'}")
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Ensure columns exist
    ensure_columns(conn)

    # Get all approved tools with github_url
    cursor = conn.execute(
        "SELECT id, name, slug, github_url FROM tools WHERE status = 'approved' AND github_url IS NOT NULL AND github_url != ''"
    )
    tools = cursor.fetchall()
    print(f"Found {len(tools)} tools with GitHub URLs")
    print()

    # Also count tools without GitHub URLs
    cursor_no_gh = conn.execute(
        "SELECT COUNT(*) FROM tools WHERE status = 'approved' AND (github_url IS NULL OR github_url = '')"
    )
    no_github_count = cursor_no_gh.fetchone()[0]

    stats = {"active": 0, "stale": 0, "inactive": 0, "unknown": 0, "no_github": no_github_count}

    for i, tool in enumerate(tools):
        tool_id = tool["id"]
        name = tool["name"]
        github_url = tool["github_url"]
        owner, repo = extract_owner_repo(github_url)

        if not owner or not repo:
            print(f"  [{i+1}/{len(tools)}] {name}: invalid GitHub URL ({github_url})")
            conn.execute(
                "UPDATE tools SET github_freshness = 'unknown' WHERE id = ?",
                (tool_id,),
            )
            stats["unknown"] += 1
            continue

        commit_date, error = get_last_commit_date(owner, repo)

        if error:
            print(f"  [{i+1}/{len(tools)}] {name} ({owner}/{repo}): {error}")
            conn.execute(
                "UPDATE tools SET github_freshness = 'unknown' WHERE id = ?",
                (tool_id,),
            )
            stats["unknown"] += 1

            # If rate limited, wait and retry
            if error == "rate_limited":
                print("    Rate limited! Waiting 60 seconds...")
                time.sleep(60)
        else:
            freshness = classify_freshness(commit_date)
            days_ago = (datetime.now(timezone.utc) - commit_date).days
            commit_str = commit_date.strftime("%Y-%m-%d %H:%M:%S")
            label = f"{freshness.upper()} ({days_ago}d ago)"
            print(f"  [{i+1}/{len(tools)}] {name} ({owner}/{repo}): {label} — last commit {commit_str}")

            conn.execute(
                "UPDATE tools SET last_github_commit = ?, github_freshness = ? WHERE id = ?",
                (commit_str, freshness, tool_id),
            )
            stats[freshness] += 1

        conn.commit()

        # Rate limit: 1 second between requests
        if i < len(tools) - 1:
            time.sleep(1)

    print()
    print(f"Summary")
    print(f"-------")
    print(f"  Active (< {ACTIVE_THRESHOLD}d):     {stats['active']}")
    print(f"  Stale ({ACTIVE_THRESHOLD}-{STALE_THRESHOLD}d):    {stats['stale']}")
    print(f"  Inactive ({STALE_THRESHOLD}+d):   {stats['inactive']}")
    print(f"  Unknown/error:       {stats['unknown']}")
    print(f"  No GitHub URL:       {stats['no_github']}")
    print(f"  Total tools checked: {len(tools)}")
    print()
    print("Done!")

    conn.close()


if __name__ == "__main__":
    main()

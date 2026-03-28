#!/usr/bin/env python3
"""GitHub Autopsy v2 — mine migration paths and verified combos at scale.

Designed to hit 10,000+ repos. Resumable, multi-strategy, error-resilient.
Both Patrick and Ed can run this 24/7 from different machines.

USAGE:
    # Quick start — uses gh CLI token, scans 2000 NEW repos
    python3 scripts/github_autopsy.py

    # Full options
    python3 scripts/github_autopsy.py --limit 5000 --db /tmp/autopsy.db
    python3 scripts/github_autopsy.py --mode packages --limit 1000
    python3 scripts/github_autopsy.py --mode awesome --limit 500
    python3 scripts/github_autopsy.py --status  # just show progress

SEARCH MODES:
    stars     — top-starred JS/TS repos (default, broad coverage)
    packages  — repos that use specific tracked packages (high signal)
    awesome   — repos from awesome-* lists (curated, high quality)
    all       — run all modes sequentially

RESUME: Automatically skips repos already in the database.
"""

import argparse
import base64
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from itertools import combinations

import requests

# ── Config ──────────────────────────────────────────────────────────────────

GITHUB_API = "https://api.github.com"
DEFAULT_DB = "/tmp/autopsy.db"
RATE_LIMIT_BUFFER = 50  # stop when this many requests remain

# Packages we track migrations for
TRACKED_PACKAGES = {
    # Auth
    "passport", "next-auth", "lucia", "@clerk/nextjs", "@clerk/clerk-react",
    "@auth0/auth0-react", "@auth0/nextjs-auth0", "@kinde-oss/kinde-auth-nextjs",
    "@supabase/auth-helpers-nextjs", "jsonwebtoken", "bcrypt", "bcryptjs",
    "@hanko/elements", "@logto/next", "@ory/client",
    # ORM / Database
    "prisma", "@prisma/client", "drizzle-orm", "mongoose", "sequelize",
    "typeorm", "knex", "mikro-orm", "@libsql/client", "@neondatabase/serverless",
    "pg", "mysql2", "better-sqlite3", "kysely", "mongodb",
    # Payments
    "stripe", "@stripe/stripe-js", "@lemonsqueezy/lemonsqueezy.js",
    "@paddle/paddle-js", "paddle-sdk", "@polar-sh/sdk",
    # Email
    "resend", "nodemailer", "@sendgrid/mail", "mailgun.js", "postmark",
    "@plunk/node", "@react-email/components",
    # Analytics
    "posthog-js", "@posthog/react", "posthog-node",
    "@vercel/analytics", "plausible-tracker", "@umami/node",
    "fathom-client", "@aptabase/web", "mixpanel", "amplitude-js",
    "@segment/analytics-next", "simple-analytics-script",
    # Error tracking
    "@sentry/node", "@sentry/react", "@sentry/nextjs",
    "@highlight-run/next", "bugsnag", "@rollbar/react",
    # CSS / UI
    "tailwindcss", "styled-components", "@emotion/react", "@emotion/styled",
    "sass", "less", "@chakra-ui/react", "@mantine/core",
    "daisyui", "@radix-ui/themes", "@headlessui/react",
    "framer-motion", "bootstrap", "bulma", "@mui/material", "antd",
    # Date/time
    "moment", "dayjs", "date-fns", "luxon",
    # HTTP
    "axios", "got", "node-fetch", "undici", "ky", "superagent",
    # State management
    "redux", "@reduxjs/toolkit", "zustand", "jotai", "recoil",
    "mobx", "valtio", "xstate",
    # Testing
    "jest", "vitest", "mocha", "ava", "@testing-library/react",
    "cypress", "playwright", "@playwright/test",
    # Validation
    "zod", "yup", "joi", "ajv", "valibot", "superstruct",
    # Build
    "webpack", "vite", "esbuild", "rollup", "parcel", "turbo", "tsup",
    # Framework
    "next", "express", "fastify", "hono", "koa", "nestjs", "@nestjs/core",
    "nuxt", "remix", "@remix-run/node", "astro", "sveltekit",
    # CMS
    "payload", "@strapi/strapi", "tinacms", "@sanity/client",
    "contentful", "@directus/sdk",
    # Search
    "meilisearch", "typesense", "algoliasearch", "@algolia/client-search",
    # Monitoring / Logging
    "@axiomhq/js", "@logtail/node", "pino", "winston", "bunyan",
    # File upload
    "multer", "@uploadthing/react", "uploadthing", "formidable",
    # Feature flags
    "@growthbook/growthbook", "flagsmith", "unleash-client",
    # Background jobs
    "bullmq", "bull", "inngest", "@trigger.dev/sdk", "agenda",
    # API
    "@trpc/server", "@trpc/client", "graphql", "graphql-yoga",
    "@apollo/server", "@apollo/client",
    # Realtime
    "socket.io", "pusher", "ably", "@supabase/realtime-js",
    # Deployment
    "@vercel/node", "serverless", "aws-cdk-lib",
}

# Known migration patterns (high confidence)
KNOWN_MIGRATIONS = {
    ("moment", "date-fns"), ("moment", "dayjs"), ("moment", "luxon"),
    ("axios", "ky"), ("axios", "undici"), ("node-fetch", "undici"),
    ("express", "fastify"), ("express", "hono"),
    ("jest", "vitest"), ("mocha", "vitest"), ("mocha", "jest"),
    ("redux", "zustand"), ("redux", "jotai"),
    ("mongoose", "prisma"), ("mongoose", "drizzle-orm"),
    ("sequelize", "prisma"), ("sequelize", "drizzle-orm"),
    ("typeorm", "prisma"), ("typeorm", "drizzle-orm"),
    ("knex", "kysely"), ("knex", "drizzle-orm"),
    ("styled-components", "tailwindcss"), ("sass", "tailwindcss"),
    ("@emotion/react", "tailwindcss"),
    ("webpack", "vite"), ("webpack", "esbuild"), ("rollup", "vite"),
    ("yup", "zod"), ("joi", "zod"),
    ("passport", "lucia"), ("passport", "next-auth"),
    ("next-auth", "@clerk/nextjs"),
    ("@sendgrid/mail", "resend"), ("nodemailer", "resend"),
    ("bull", "bullmq"), ("cypress", "playwright"), ("winston", "pino"),
    ("@mui/material", "tailwindcss"), ("bootstrap", "tailwindcss"),
    ("@chakra-ui/react", "@mantine/core"),
    ("graphql", "@trpc/server"), ("multer", "uploadthing"),
    ("amplitude-js", "posthog-js"), ("mixpanel", "posthog-js"),
}

# Category mapping for same-category migration detection
PACKAGE_CATEGORY = {}
_CATEGORY_GROUPS = {
    "auth": ["passport", "next-auth", "lucia", "@clerk/nextjs", "@clerk/clerk-react",
             "@auth0/auth0-react", "@auth0/nextjs-auth0", "@kinde-oss/kinde-auth-nextjs",
             "@supabase/auth-helpers-nextjs", "jsonwebtoken", "bcrypt", "bcryptjs",
             "@hanko/elements", "@logto/next", "@ory/client"],
    "orm": ["prisma", "@prisma/client", "drizzle-orm", "mongoose", "sequelize",
            "typeorm", "knex", "mikro-orm", "@libsql/client", "@neondatabase/serverless",
            "pg", "mysql2", "better-sqlite3", "kysely", "mongodb"],
    "payments": ["stripe", "@stripe/stripe-js", "@lemonsqueezy/lemonsqueezy.js",
                 "@paddle/paddle-js", "paddle-sdk", "@polar-sh/sdk"],
    "email": ["resend", "nodemailer", "@sendgrid/mail", "mailgun.js", "postmark",
              "@plunk/node", "@react-email/components"],
    "analytics": ["posthog-js", "@posthog/react", "posthog-node", "@vercel/analytics",
                  "plausible-tracker", "@umami/node", "fathom-client", "@aptabase/web",
                  "mixpanel", "amplitude-js", "@segment/analytics-next", "simple-analytics-script"],
    "errors": ["@sentry/node", "@sentry/react", "@sentry/nextjs", "@highlight-run/next",
               "bugsnag", "@rollbar/react"],
    "css": ["tailwindcss", "styled-components", "@emotion/react", "@emotion/styled",
            "sass", "less", "@chakra-ui/react", "@mantine/core", "daisyui",
            "@radix-ui/themes", "@headlessui/react", "bootstrap", "bulma",
            "@mui/material", "antd"],
    "date": ["moment", "dayjs", "date-fns", "luxon"],
    "http": ["axios", "got", "node-fetch", "undici", "ky", "superagent"],
    "state": ["redux", "@reduxjs/toolkit", "zustand", "jotai", "recoil",
              "mobx", "valtio", "xstate"],
    "testing": ["jest", "vitest", "mocha", "ava", "@testing-library/react",
                "cypress", "playwright", "@playwright/test"],
    "validation": ["zod", "yup", "joi", "ajv", "valibot", "superstruct"],
    "build": ["webpack", "vite", "esbuild", "rollup", "parcel", "turbo", "tsup"],
    "framework": ["next", "express", "fastify", "hono", "koa", "nestjs", "@nestjs/core",
                  "nuxt", "remix", "@remix-run/node", "astro", "sveltekit"],
    "logging": ["@axiomhq/js", "@logtail/node", "pino", "winston", "bunyan"],
    "upload": ["multer", "@uploadthing/react", "uploadthing", "formidable"],
    "flags": ["@growthbook/growthbook", "flagsmith", "unleash-client"],
    "jobs": ["bullmq", "bull", "inngest", "@trigger.dev/sdk", "agenda"],
    "api": ["@trpc/server", "@trpc/client", "graphql", "graphql-yoga",
            "@apollo/server", "@apollo/client"],
    "animation": ["framer-motion"],
    "realtime": ["socket.io", "pusher", "ably", "@supabase/realtime-js"],
}
for _cat, _pkgs in _CATEGORY_GROUPS.items():
    for _pkg in _pkgs:
        PACKAGE_CATEGORY[_pkg] = _cat

# High-signal packages to search for specifically (mode=packages)
SEARCH_PACKAGES = [
    "prisma", "drizzle-orm", "next-auth", "lucia", "stripe",
    "tailwindcss", "vitest", "zod", "trpc", "hono",
    "supabase", "clerk", "resend", "posthog", "sentry",
    "playwright", "vite", "zustand", "tanstack",
    "uploadthing", "inngest", "convex", "turso",
]

# Awesome lists to scrape for repos (mode=awesome)
AWESOME_LISTS = [
    "sindresorhus/awesome-nodejs",
    "enaqx/awesome-react",
    "unicodeveloper/awesome-nextjs",
    "vinta/awesome-python",
    "humiaozuzu/awesome-flask",
    "awesome-selfhosted/awesome-selfhosted",
]


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_token() -> str:
    """Get GitHub token from args, env, or gh CLI."""
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        try:
            result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                token = result.stdout.strip()
        except Exception:
            pass
    return token


def get_headers(token: str) -> dict:
    h = {"Accept": "application/vnd.github.v3+json", "User-Agent": "indiestack-autopsy/2.0"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def api_get(token: str, url: str, params: dict = None, accept: str = None) -> requests.Response:
    """Make a GitHub API request with rate limit handling and error resilience."""
    headers = get_headers(token)
    if accept:
        headers["Accept"] = accept

    # Check rate limit before every request
    remaining = int(headers.get("X-RateLimit-Remaining", "100"))
    if remaining < RATE_LIMIT_BUFFER:
        _wait_for_reset(token)

    try:
        r = requests.get(url, headers=headers, params=params, timeout=30)
    except requests.exceptions.RequestException as e:
        print(f"   ! Request failed: {type(e).__name__}")
        return None

    # Handle rate limiting
    if r.status_code == 403 and "rate limit" in r.text.lower():
        _wait_for_reset(token)
        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
        except Exception:
            return None

    return r


def _wait_for_reset(token: str):
    """Wait for rate limit to reset."""
    try:
        r = requests.get(f"{GITHUB_API}/rate_limit", headers=get_headers(token), timeout=10)
        if r.status_code == 200:
            core = r.json()["resources"]["core"]
            if core["remaining"] < RATE_LIMIT_BUFFER:
                wait = max(core["reset"] - time.time(), 0) + 5
                print(f"  ... rate limited, waiting {wait:.0f}s")
                time.sleep(wait)
    except Exception:
        time.sleep(60)


def init_db(db_path: str) -> sqlite3.Connection:
    """Initialize database with all required tables."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""CREATE TABLE IF NOT EXISTS scanned_repos (
        repo TEXT PRIMARY KEY,
        stars INTEGER DEFAULT 0,
        source TEXT DEFAULT 'stars',
        has_package_json INTEGER DEFAULT 0,
        tracked_deps_count INTEGER DEFAULT 0,
        migration_count INTEGER DEFAULT 0,
        combo_count INTEGER DEFAULT 0,
        scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS migration_paths (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_package TEXT NOT NULL,
        to_package TEXT NOT NULL,
        repo TEXT NOT NULL,
        commit_sha TEXT NOT NULL,
        committed_at TIMESTAMP,
        confidence TEXT NOT NULL DEFAULT 'swap',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(from_package, to_package, repo, commit_sha)
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_migration_from ON migration_paths(from_package)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_migration_to ON migration_paths(to_package)")
    conn.execute("""CREATE TABLE IF NOT EXISTS verified_combos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        package_a TEXT NOT NULL,
        package_b TEXT NOT NULL,
        repo TEXT NOT NULL,
        repo_stars INTEGER DEFAULT 0,
        last_seen_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(package_a, package_b, repo)
    )""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_combos_a ON verified_combos(package_a)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_combos_b ON verified_combos(package_b)")
    conn.commit()
    return conn


def is_scanned(conn: sqlite3.Connection, repo: str) -> bool:
    return conn.execute("SELECT 1 FROM scanned_repos WHERE repo = ?", (repo,)).fetchone() is not None


def mark_scanned(conn: sqlite3.Connection, repo: str, stars: int, source: str,
                 has_pkg: bool, tracked: int, mig: int, combo: int):
    conn.execute(
        """INSERT OR REPLACE INTO scanned_repos
           (repo, stars, source, has_package_json, tracked_deps_count, migration_count, combo_count, scanned_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
        (repo, stars, source, int(has_pkg), tracked, mig, combo)
    )
    conn.commit()


def print_status(conn: sqlite3.Connection):
    """Print current data status."""
    total = conn.execute("SELECT COUNT(*) FROM scanned_repos").fetchone()[0]
    with_pkg = conn.execute("SELECT COUNT(*) FROM scanned_repos WHERE has_package_json = 1").fetchone()[0]
    mig = conn.execute("SELECT COUNT(*) FROM migration_paths").fetchone()[0]
    unique_mig = conn.execute("SELECT COUNT(DISTINCT from_package || '→' || to_package) FROM migration_paths").fetchone()[0]
    combos = conn.execute("SELECT COUNT(*) FROM verified_combos").fetchone()[0]
    repos_combos = conn.execute("SELECT COUNT(DISTINCT repo) FROM verified_combos").fetchone()[0]

    pct = (total / 10000) * 100

    print(f"\n{'='*60}")
    print(f"  AUTOPSY STATUS — {pct:.1f}% to 10k target")
    print(f"{'='*60}")
    print(f"  Repos scanned:      {total:,} / 10,000")
    print(f"  With package.json:  {with_pkg:,}")
    print(f"  Migration events:   {mig:,} ({unique_mig} unique paths)")
    print(f"  Verified combos:    {combos:,}")
    print(f"  Repos with combos:  {repos_combos:,}")

    # Source breakdown
    for row in conn.execute("SELECT source, COUNT(*) as n FROM scanned_repos GROUP BY source ORDER BY n DESC").fetchall():
        print(f"    {row[0]}: {row[1]:,} repos")

    # Top migrations
    if mig > 0:
        print(f"\n  Top migrations:")
        for r in conn.execute(
            "SELECT from_package, to_package, COUNT(DISTINCT repo) as n FROM migration_paths "
            "GROUP BY from_package, to_package ORDER BY n DESC LIMIT 10"
        ).fetchall():
            print(f"    {r[0]} → {r[1]}: {r[2]} repos")

    print(f"{'='*60}\n")


# ── Diff Parsing ─────────────────────────────────────────────────────────────

def parse_diff_for_migrations(diff_text: str) -> tuple:
    added, removed = set(), set()
    dep_pattern = re.compile(r'^[+-]\s*"(@?[a-zA-Z0-9][\w./-]*)"\s*:\s*"[^"]*"')

    for line in diff_text.split("\n"):
        line = line.rstrip(",")
        m = dep_pattern.match(line)
        if not m:
            continue
        pkg = m.group(1)
        if pkg not in TRACKED_PACKAGES:
            continue
        if line.startswith("+") and not line.startswith("+++"):
            added.add(pkg)
        elif line.startswith("-") and not line.startswith("---"):
            removed.add(pkg)

    # Filter version bumps
    version_bumps = added & removed
    added -= version_bumps
    removed -= version_bumps
    return added, removed


def classify_migration(removed: str, added: str) -> str:
    if (removed, added) in KNOWN_MIGRATIONS or (added, removed) in KNOWN_MIGRATIONS:
        return "swap"
    cat_a = PACKAGE_CATEGORY.get(removed)
    cat_b = PACKAGE_CATEGORY.get(added)
    if cat_a and cat_b and cat_a == cat_b:
        return "likely"
    return "inferred"


# ── Repo Discovery Strategies ────────────────────────────────────────────────

def discover_by_stars(token: str, limit: int, conn: sqlite3.Connection) -> list:
    """Search by stars — broad coverage of popular repos."""
    repos = []
    queries = [
        "language:TypeScript stars:>1000",
        "language:JavaScript stars:>1000",
        "language:TypeScript stars:>200",
        "language:JavaScript stars:>200",
        "language:TypeScript stars:>50",
        "language:JavaScript stars:>50",
    ]
    for query in queries:
        if len(repos) >= limit:
            break
        for page in range(1, 11):  # 10 pages max per query (1000 results)
            if len(repos) >= limit:
                break
            r = api_get(token, f"{GITHUB_API}/search/repositories", {
                "q": query, "sort": "stars", "order": "desc",
                "per_page": 100, "page": page,
            })
            if not r or r.status_code != 200:
                break
            items = r.json().get("items", [])
            if not items:
                break
            for item in items:
                name = item["full_name"]
                if not is_scanned(conn, name) and name not in [r["full_name"] for r in repos]:
                    repos.append({"full_name": name, "stars": item["stargazers_count"], "source": "stars"})
            time.sleep(0.3)
    return repos[:limit]


def discover_by_packages(token: str, limit: int, conn: sqlite3.Connection) -> list:
    """Search for repos using specific tracked packages — high signal."""
    repos = []
    for pkg in SEARCH_PACKAGES:
        if len(repos) >= limit:
            break
        # Search for package.json files containing this package
        query = f'"{pkg}" filename:package.json'
        for page in range(1, 4):  # 3 pages per package
            if len(repos) >= limit:
                break
            r = api_get(token, f"{GITHUB_API}/search/code", {
                "q": query, "per_page": 100, "page": page,
            })
            if not r or r.status_code != 200:
                break
            items = r.json().get("items", [])
            if not items:
                break
            seen = set()
            for item in items:
                name = item["repository"]["full_name"]
                if name not in seen and not is_scanned(conn, name) and name not in [r["full_name"] for r in repos]:
                    seen.add(name)
                    repos.append({
                        "full_name": name,
                        "stars": item["repository"].get("stargazers_count", 0),
                        "source": f"pkg:{pkg}",
                    })
            time.sleep(1)  # Code search has stricter rate limits
    return repos[:limit]


def discover_from_awesome(token: str, limit: int, conn: sqlite3.Connection) -> list:
    """Extract repos from awesome-* lists."""
    repos = []
    github_repo_pattern = re.compile(r'github\.com/([a-zA-Z0-9_.-]+/[a-zA-Z0-9_.-]+)')

    for awesome_repo in AWESOME_LISTS:
        if len(repos) >= limit:
            break
        print(f"  Scanning {awesome_repo}...")
        r = api_get(token, f"{GITHUB_API}/repos/{awesome_repo}/readme")
        if not r or r.status_code != 200:
            continue
        try:
            content = base64.b64decode(r.json()["content"]).decode("utf-8")
        except Exception:
            continue

        for match in github_repo_pattern.findall(content):
            if len(repos) >= limit:
                break
            name = match.rstrip("/").rstrip(".")
            if not is_scanned(conn, name) and name not in [r["full_name"] for r in repos]:
                repos.append({"full_name": name, "stars": 0, "source": f"awesome:{awesome_repo.split('/')[1]}"})

    return repos[:limit]


# ── Core Scanner ─────────────────────────────────────────────────────────────

def scan_repo(token: str, conn: sqlite3.Connection, repo: str, stars: int, source: str, max_commits: int):
    """Scan a single repo for migrations and combos."""
    repo_migrations = 0
    repo_combos = 0

    # Get current package.json for combos
    r = api_get(token, f"{GITHUB_API}/repos/{repo}/contents/package.json")
    if not r or r.status_code != 200:
        mark_scanned(conn, repo, stars, source, False, 0, 0, 0)
        return 0, 0

    try:
        pkg_json = json.loads(base64.b64decode(r.json()["content"]).decode("utf-8"))
    except Exception:
        mark_scanned(conn, repo, stars, source, False, 0, 0, 0)
        return 0, 0

    # Count tracked deps
    all_deps = set()
    for section in ("dependencies", "devDependencies"):
        for pkg in pkg_json.get(section, {}):
            if pkg in TRACKED_PACKAGES:
                all_deps.add(pkg)

    # Extract combos from current manifest
    if len(all_deps) >= 2:
        sorted_deps = sorted(all_deps)
        for i in range(len(sorted_deps)):
            for j in range(i + 1, len(sorted_deps)):
                try:
                    conn.execute(
                        """INSERT INTO verified_combos (package_a, package_b, repo, repo_stars, last_seen_at)
                           VALUES (?, ?, ?, ?, datetime('now'))
                           ON CONFLICT(package_a, package_b, repo)
                           DO UPDATE SET last_seen_at = datetime('now'), repo_stars = excluded.repo_stars""",
                        (sorted_deps[i], sorted_deps[j], repo, stars)
                    )
                    repo_combos += 1
                except Exception:
                    pass

    # Get commits that touched package.json
    r = api_get(token, f"{GITHUB_API}/repos/{repo}/commits", {"path": "package.json", "per_page": max_commits})
    if r and r.status_code == 200:
        commits = r.json()
        if isinstance(commits, list):
            for commit in commits[:max_commits]:
                sha = commit["sha"]
                date = commit["commit"]["committer"]["date"]

                # Get diff
                diff_r = api_get(token, f"{GITHUB_API}/repos/{repo}/commits/{sha}",
                                 accept="application/vnd.github.v3.diff")
                if not diff_r or diff_r.status_code != 200:
                    continue

                # Filter to package.json only
                lines = diff_r.text.split("\n")
                in_pkg = False
                pkg_lines = []
                for line in lines:
                    if line.startswith("diff --git"):
                        in_pkg = "package.json" in line and "package-lock" not in line
                    if in_pkg:
                        pkg_lines.append(line)

                if not pkg_lines:
                    continue

                added, removed = parse_diff_for_migrations("\n".join(pkg_lines))
                if removed and added:
                    for rm_pkg in removed:
                        for add_pkg in added:
                            if rm_pkg == add_pkg:
                                continue
                            confidence = classify_migration(rm_pkg, add_pkg)
                            if confidence == "inferred":
                                continue
                            try:
                                conn.execute(
                                    """INSERT OR IGNORE INTO migration_paths
                                       (from_package, to_package, repo, commit_sha, committed_at, confidence)
                                       VALUES (?, ?, ?, ?, ?, ?)""",
                                    (rm_pkg, add_pkg, repo, sha, date, confidence)
                                )
                                repo_migrations += 1
                            except Exception:
                                pass

                time.sleep(0.2)

    conn.commit()
    mark_scanned(conn, repo, stars, source, True, len(all_deps), repo_migrations, repo_combos)
    return repo_migrations, repo_combos


# ── Main ─────────────────────────────────────────────────────────────────────

def run(args):
    token = args.token or get_token()
    if not token:
        print("ERROR: No GitHub token. Set GITHUB_TOKEN, use --token, or install gh CLI.")
        sys.exit(1)

    conn = init_db(args.db)

    if args.status:
        print_status(conn)
        conn.close()
        return

    # Check rate limit
    try:
        r = requests.get(f"{GITHUB_API}/rate_limit", headers=get_headers(token), timeout=10)
        if r.status_code == 200:
            core = r.json()["resources"]["core"]
            print(f"GitHub API: {core['remaining']}/{core['limit']} requests remaining")
            if core["remaining"] < 100:
                print("WARNING: Low API quota. Script will pause when rate limited.")
    except Exception:
        pass

    # Discover repos
    mode = args.mode
    limit = args.limit
    print(f"\nMode: {mode} | Target: {limit} new repos | DB: {args.db}")

    repos = []
    if mode in ("stars", "all"):
        print(f"\n--- Strategy: Top-starred repos ---")
        batch = discover_by_stars(token, limit if mode == "stars" else limit // 2, conn)
        print(f"  Found {len(batch)} new repos")
        repos.extend(batch)

    if mode in ("packages", "all"):
        remaining = limit - len(repos) if mode == "all" else limit
        print(f"\n--- Strategy: Package-targeted search ---")
        batch = discover_by_packages(token, remaining if mode != "packages" else limit, conn)
        print(f"  Found {len(batch)} new repos")
        repos.extend(batch)

    if mode in ("awesome", "all"):
        remaining = limit - len(repos) if mode == "all" else limit
        print(f"\n--- Strategy: Awesome lists ---")
        batch = discover_from_awesome(token, remaining if mode != "awesome" else limit, conn)
        print(f"  Found {len(batch)} new repos")
        repos.extend(batch)

    if not repos:
        print("\nNo new repos to scan. All previously scanned.")
        print_status(conn)
        conn.close()
        return

    print(f"\nScanning {len(repos)} repos...")
    total_mig = 0
    total_combo = 0

    for i, repo_info in enumerate(repos):
        repo = repo_info["full_name"]
        stars = repo_info["stars"]
        source = repo_info.get("source", "unknown")

        # Skip if somehow already scanned (race condition)
        if is_scanned(conn, repo):
            continue

        progress = f"[{i+1}/{len(repos)}]"
        print(f"{progress} {repo} ({stars}*) [{source}]", end="", flush=True)

        try:
            mig, combo = scan_repo(token, conn, repo, stars, source, args.max_commits)
            total_mig += mig
            total_combo += combo

            status_parts = []
            if mig:
                status_parts.append(f"{mig} migrations")
            if combo:
                status_parts.append(f"{combo} combos")
            if status_parts:
                print(f" -> {', '.join(status_parts)}")
            else:
                print(f" -> no tracked deps")
        except KeyboardInterrupt:
            print("\n\nInterrupted! Progress saved.")
            break
        except Exception as e:
            print(f" -> ERROR: {e}")
            mark_scanned(conn, repo, stars, source, False, 0, 0, 0)

    # Final summary
    print_status(conn)
    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="GitHub Autopsy v2 — mine migration paths at scale",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python3 scripts/github_autopsy.py                    # scan 2000 repos\n"
               "  python3 scripts/github_autopsy.py --mode packages    # targeted search\n"
               "  python3 scripts/github_autopsy.py --status           # check progress\n"
               "  python3 scripts/github_autopsy.py --mode all --limit 5000\n"
    )
    parser.add_argument("--token", help="GitHub token (default: GITHUB_TOKEN env or gh CLI)")
    parser.add_argument("--db", default=DEFAULT_DB, help=f"SQLite database path (default: {DEFAULT_DB})")
    parser.add_argument("--mode", choices=["stars", "packages", "awesome", "all"], default="stars",
                        help="Discovery strategy (default: stars)")
    parser.add_argument("--limit", type=int, default=2000, help="Max new repos to scan (default: 2000)")
    parser.add_argument("--max-commits", type=int, default=20, help="Max commits per repo (default: 20)")
    parser.add_argument("--status", action="store_true", help="Just show current progress")
    args = parser.parse_args()

    run(args)

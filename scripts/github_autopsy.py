#!/usr/bin/env python3
"""GitHub Autopsy — mine migration paths and verified combos from git history.

Scans popular GitHub repos for package.json commit history, parses diffs to find:
1. MIGRATION PATHS: when a project removes package A and adds package B in the
   same commit, that's a verified migration (e.g., moment → date-fns).
2. VERIFIED COMBOS: packages that coexist in the same manifest in active repos.

This data is public but nobody has aggregated it. First mover owns it.

Usage:
    python3 scripts/github_autopsy.py --dry-run --limit 10
    python3 scripts/github_autopsy.py --limit 500 --token ghp_xxx
    python3 scripts/github_autopsy.py --db /data/indiestack.db --limit 1000
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from collections import defaultdict
from datetime import datetime

import requests

# ── Config ──────────────────────────────────────────────────────────────────

GITHUB_API = "https://api.github.com"

# Packages we care about tracking migrations for.
# Focus on the ecosystem packages that matter to dev tool decisions.
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
    "framer-motion", "bootstrap", "bulma", "@mui/material",
    "antd",
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

# Known migration patterns to boost confidence
KNOWN_MIGRATIONS = {
    ("moment", "date-fns"), ("moment", "dayjs"), ("moment", "luxon"),
    ("axios", "ky"), ("axios", "undici"),
    ("node-fetch", "undici"),
    ("express", "fastify"), ("express", "hono"),
    ("jest", "vitest"),
    ("mocha", "vitest"), ("mocha", "jest"),
    ("redux", "zustand"), ("redux", "jotai"),
    ("mongoose", "prisma"), ("mongoose", "drizzle-orm"),
    ("sequelize", "prisma"), ("sequelize", "drizzle-orm"),
    ("typeorm", "prisma"), ("typeorm", "drizzle-orm"),
    ("knex", "kysely"), ("knex", "drizzle-orm"),
    ("styled-components", "tailwindcss"),
    ("sass", "tailwindcss"),
    ("@emotion/react", "tailwindcss"),
    ("webpack", "vite"), ("webpack", "esbuild"),
    ("rollup", "vite"),
    ("yup", "zod"), ("joi", "zod"),
    ("passport", "lucia"), ("passport", "next-auth"),
    ("next-auth", "@clerk/nextjs"),
    ("@sendgrid/mail", "resend"),
    ("nodemailer", "resend"),
    ("bull", "bullmq"),
    ("cypress", "playwright"),
    ("winston", "pino"),
    ("@mui/material", "tailwindcss"),
    ("bootstrap", "tailwindcss"),
    ("@chakra-ui/react", "@mantine/core"),
    ("graphql", "@trpc/server"),
    ("multer", "uploadthing"),
    ("amplitude-js", "posthog-js"),
    ("mixpanel", "posthog-js"),
}


def get_headers(token: str) -> dict:
    h = {"Accept": "application/vnd.github.v3+json"}
    if token:
        h["Authorization"] = f"token {token}"
    return h


def check_rate_limit(token: str) -> dict:
    r = requests.get(f"{GITHUB_API}/rate_limit", headers=get_headers(token))
    if r.status_code == 200:
        core = r.json()["resources"]["core"]
        return core
    return {"remaining": 0, "limit": 0, "reset": 0}


def wait_for_rate_limit(token: str):
    """Check rate limit and wait if needed."""
    rl = check_rate_limit(token)
    if rl["remaining"] < 10:
        reset_time = rl["reset"]
        wait_secs = max(reset_time - time.time(), 0) + 5
        print(f"  ⏳ Rate limited. Waiting {wait_secs:.0f}s (reset at {datetime.fromtimestamp(reset_time)})")
        time.sleep(wait_secs)


def search_repos(token: str, limit: int) -> list:
    """Find popular JS/TS repos with package.json."""
    repos = []
    page = 1
    per_page = min(100, limit)

    # Search for repos with package.json, sorted by stars
    queries = [
        "language:TypeScript stars:>500",
        "language:JavaScript stars:>500",
        "language:TypeScript stars:>100",
        "language:JavaScript stars:>100",
    ]

    for query in queries:
        if len(repos) >= limit:
            break

        while len(repos) < limit:
            wait_for_rate_limit(token)
            url = f"{GITHUB_API}/search/repositories"
            params = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": per_page,
                "page": page,
            }
            r = requests.get(url, headers=get_headers(token), params=params)
            if r.status_code != 200:
                print(f"  ⚠ Search API error {r.status_code}: {r.text[:200]}")
                break

            items = r.json().get("items", [])
            if not items:
                break

            for item in items:
                full_name = item["full_name"]
                if full_name not in [r["full_name"] for r in repos]:
                    repos.append({
                        "full_name": full_name,
                        "stars": item["stargazers_count"],
                        "default_branch": item.get("default_branch", "main"),
                    })

            page += 1
            if page > 10:  # GitHub search API caps at 1000 results
                page = 1
                break

            time.sleep(0.5)  # Be nice

    return repos[:limit]


def get_package_json_commits(token: str, repo: str, max_commits: int = 50) -> list:
    """Get commits that modified package.json."""
    wait_for_rate_limit(token)
    url = f"{GITHUB_API}/repos/{repo}/commits"
    params = {"path": "package.json", "per_page": min(max_commits, 100)}
    r = requests.get(url, headers=get_headers(token), params=params)

    if r.status_code != 200:
        return []

    commits = r.json()
    if not isinstance(commits, list):
        return []

    return [{"sha": c["sha"], "date": c["commit"]["committer"]["date"]} for c in commits[:max_commits]]


def get_commit_diff(token: str, repo: str, sha: str) -> str:
    """Get the diff for a specific commit, filtered to package.json."""
    wait_for_rate_limit(token)
    url = f"{GITHUB_API}/repos/{repo}/commits/{sha}"
    headers = get_headers(token)
    headers["Accept"] = "application/vnd.github.v3.diff"
    try:
        r = requests.get(url, headers=headers, timeout=30)
    except (requests.exceptions.RequestException, Exception) as e:
        print(f"   ⚠ Diff fetch failed: {type(e).__name__}")
        return ""

    if r.status_code != 200:
        return ""

    # Filter to only package.json changes
    diff_text = r.text
    lines = diff_text.split("\n")
    in_package_json = False
    package_lines = []

    for line in lines:
        if line.startswith("diff --git"):
            in_package_json = "package.json" in line and "package-lock" not in line
        if in_package_json:
            package_lines.append(line)

    return "\n".join(package_lines)


def parse_diff_for_migrations(diff_text: str) -> tuple:
    """Parse a package.json diff to find added and removed packages.

    Returns (added_packages, removed_packages) sets.
    """
    added = set()
    removed = set()

    # Match lines like:
    #   +    "date-fns": "^2.30.0",
    #   -    "moment": "^2.29.4",
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

    # Packages in BOTH sets are version bumps, not migrations
    version_bumps = added & removed
    added -= version_bumps
    removed -= version_bumps

    return added, removed


def get_current_package_json(token: str, repo: str) -> dict:
    """Fetch the current package.json for combo extraction."""
    wait_for_rate_limit(token)
    url = f"{GITHUB_API}/repos/{repo}/contents/package.json"
    r = requests.get(url, headers=get_headers(token))
    if r.status_code != 200:
        return {}

    import base64
    try:
        content = base64.b64decode(r.json()["content"]).decode("utf-8")
        return json.loads(content)
    except Exception:
        return {}


def extract_combos_from_manifest(pkg_json: dict, repo: str, stars: int) -> list:
    """Extract verified package combinations from a manifest."""
    deps = set()
    for section in ("dependencies", "devDependencies"):
        for pkg in pkg_json.get(section, {}):
            if pkg in TRACKED_PACKAGES:
                deps.add(pkg)

    if len(deps) < 2:
        return []

    combos = []
    sorted_deps = sorted(deps)
    for i in range(len(sorted_deps)):
        for j in range(i + 1, len(sorted_deps)):
            combos.append({
                "package_a": sorted_deps[i],
                "package_b": sorted_deps[j],
                "repo": repo,
                "repo_stars": stars,
            })

    return combos


# Package category mapping — only migrations within the same category make sense
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
for cat, pkgs in _CATEGORY_GROUPS.items():
    for pkg in pkgs:
        PACKAGE_CATEGORY[pkg] = cat


def same_category(pkg_a: str, pkg_b: str) -> bool:
    """Check if two packages serve the same function (plausible migration)."""
    cat_a = PACKAGE_CATEGORY.get(pkg_a)
    cat_b = PACKAGE_CATEGORY.get(pkg_b)
    if not cat_a or not cat_b:
        return False  # Unknown category — skip
    return cat_a == cat_b


def classify_migration(removed: str, added: str) -> str:
    """Classify the confidence level of a migration."""
    pair = (removed, added)
    reverse_pair = (added, removed)

    if pair in KNOWN_MIGRATIONS:
        return "swap"  # High confidence — known migration pattern
    if reverse_pair in KNOWN_MIGRATIONS:
        return "swap"  # Reverse of known migration (unusual but valid)
    if same_category(removed, added):
        return "likely"  # Same category removal + addition
    return "inferred"  # Cross-category — low confidence, probably not a migration


def run_autopsy(args):
    """Main autopsy loop."""
    token = args.token or os.environ.get("GITHUB_TOKEN", "")
    if not token:
        # Try gh CLI as fallback
        import subprocess
        try:
            result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                token = result.stdout.strip()
                print("✓ Using token from gh CLI")
        except Exception:
            pass
    if not token:
        print("⚠ No GITHUB_TOKEN — rate limited to 60 req/hr. Use --token or set GITHUB_TOKEN.")

    db_path = args.db
    dry_run = args.dry_run

    # Check rate limit
    rl = check_rate_limit(token)
    print(f"GitHub API: {rl['remaining']}/{rl['limit']} requests remaining")

    if not dry_run:
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        # Ensure tables exist
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
        conn.commit()
    else:
        conn = None

    # Phase 1: Search for repos
    print(f"\n🔍 Searching for top {args.limit} JS/TS repos...")
    repos = search_repos(token, args.limit)
    print(f"   Found {len(repos)} repos")

    total_migrations = 0
    total_combos = 0
    migration_summary = defaultdict(int)
    combo_summary = defaultdict(int)

    for i, repo_info in enumerate(repos):
        repo = repo_info["full_name"]
        stars = repo_info["stars"]
        print(f"\n[{i+1}/{len(repos)}] {repo} ⭐ {stars}")

        # Phase 2: Get commits that touched package.json
        commits = get_package_json_commits(token, repo, max_commits=args.max_commits)
        if not commits:
            print("   No package.json commits found")
            continue
        print(f"   Found {len(commits)} package.json commits")

        # Phase 3: Parse each commit diff for migrations
        repo_migrations = 0
        for commit in commits:
            sha = commit["sha"]
            date = commit["date"]

            diff = get_commit_diff(token, repo, sha)
            if not diff:
                continue

            added, removed = parse_diff_for_migrations(diff)

            # A migration = something removed AND something added in same commit
            # Only record if packages are in the same functional category
            if removed and added:
                for rm_pkg in removed:
                    for add_pkg in added:
                        if rm_pkg == add_pkg:
                            continue
                        confidence = classify_migration(rm_pkg, add_pkg)
                        # Skip cross-category noise (e.g., cypress → astro)
                        if confidence == "inferred":
                            continue
                        migration_summary[f"{rm_pkg} → {add_pkg}"] += 1
                        total_migrations += 1
                        repo_migrations += 1

                        if not dry_run:
                            try:
                                conn.execute(
                                    """INSERT OR IGNORE INTO migration_paths
                                       (from_package, to_package, repo, commit_sha, committed_at, confidence)
                                       VALUES (?, ?, ?, ?, ?, ?)""",
                                    (rm_pkg, add_pkg, repo, sha, date, confidence)
                                )
                            except Exception as e:
                                print(f"   ⚠ DB error: {e}")

            time.sleep(0.3)  # Rate limit kindness

        if repo_migrations:
            print(f"   📊 Found {repo_migrations} migration(s)")

        # Phase 4: Extract verified combos from current package.json
        pkg_json = get_current_package_json(token, repo)
        if pkg_json:
            combos = extract_combos_from_manifest(pkg_json, repo, stars)
            if combos:
                total_combos += len(combos)
                for combo in combos:
                    pair = f"{combo['package_a']} + {combo['package_b']}"
                    combo_summary[pair] += 1

                    if not dry_run:
                        try:
                            conn.execute(
                                """INSERT INTO verified_combos
                                   (package_a, package_b, repo, repo_stars, last_seen_at)
                                   VALUES (?, ?, ?, ?, datetime('now'))
                                   ON CONFLICT(package_a, package_b, repo)
                                   DO UPDATE SET last_seen_at = datetime('now'),
                                                repo_stars = excluded.repo_stars""",
                                (combo["package_a"], combo["package_b"], combo["repo"], combo["repo_stars"])
                            )
                        except Exception as e:
                            print(f"   ⚠ DB error: {e}")

                print(f"   🔗 Found {len(combos)} package combos")

        if not dry_run and conn:
            conn.commit()

    # Summary
    print("\n" + "=" * 60)
    print(f"AUTOPSY COMPLETE")
    print(f"=" * 60)
    print(f"Repos scanned:        {len(repos)}")
    print(f"Migration paths found: {total_migrations}")
    print(f"Verified combos found: {total_combos}")

    if migration_summary:
        print(f"\nTop migrations:")
        for path, count in sorted(migration_summary.items(), key=lambda x: -x[1])[:20]:
            print(f"  {path}: {count} repos")

    if combo_summary:
        print(f"\nTop combos:")
        for pair, count in sorted(combo_summary.items(), key=lambda x: -x[1])[:20]:
            print(f"  {pair}: {count} repos")

    if not dry_run and conn:
        # Final stats
        mig_count = conn.execute("SELECT COUNT(*) FROM migration_paths").fetchone()[0]
        combo_count = conn.execute("SELECT COUNT(*) FROM verified_combos").fetchone()[0]
        print(f"\nDatabase totals:")
        print(f"  migration_paths: {mig_count} rows")
        print(f"  verified_combos: {combo_count} rows")
        conn.close()

    print(f"\n{'DRY RUN — nothing written' if dry_run else 'Data saved to ' + db_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Autopsy — mine migration paths from git history")
    parser.add_argument("--token", help="GitHub personal access token (or set GITHUB_TOKEN)")
    parser.add_argument("--db", default="/data/indiestack.db", help="Path to SQLite database")
    parser.add_argument("--limit", type=int, default=100, help="Number of repos to scan")
    parser.add_argument("--max-commits", type=int, default=30, help="Max commits per repo to check")
    parser.add_argument("--dry-run", action="store_true", help="Print findings without writing to DB")
    args = parser.parse_args()

    run_autopsy(args)

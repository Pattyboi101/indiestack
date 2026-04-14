#!/usr/bin/env python3
"""GitHub Migration Miner — discovers package swaps by analyzing git history.

For each popular repo, fetches commits that modified package.json, diffs the
dependency lists between consecutive versions, and records migrations (one dep
removed + another in the same category added) into the migration_paths table.

Usage:
    python3 scripts/mine_github_migrations.py --dry-run
    python3 scripts/mine_github_migrations.py --limit 200 --token ghp_xxx
    python3 scripts/mine_github_migrations.py --db /path/to/indiestack.db

Rate limits: ~5 API calls per repo. 200 repos ≈ 1,000 calls (within 5k/hr).
"""

import argparse
import json
import os
import sqlite3
import sys
import time
from collections import defaultdict

import requests

# ── Category groupings for matching swaps ─────────────────────────────────
# Packages in the same group are potential migration pairs.
# Keep these broad — we want to catch swaps, not be too strict.
SWAP_GROUPS = {
    "testing": {"jest", "vitest", "mocha", "ava", "tap", "uvu", "bun:test", "node:test"},
    "e2e": {"cypress", "@playwright/test", "playwright", "puppeteer", "nightwatch", "testcafe", "webdriverio"},
    "bundler": {"webpack", "vite", "rollup", "esbuild", "parcel", "turbopack", "tsup", "unbuild", "bun"},
    "css": {"tailwindcss", "styled-components", "@emotion/react", "@emotion/styled", "sass", "less", "postcss", "vanilla-extract", "@vanilla-extract/css", "linaria", "stitches", "unocss", "windicss"},
    "orm": {"prisma", "@prisma/client", "drizzle-orm", "typeorm", "sequelize", "knex", "objection", "bookshelf", "mikro-orm", "kysely"},
    "auth": {"next-auth", "@auth/core", "lucia", "@clerk/nextjs", "@clerk/clerk-react", "@supabase/auth-helpers-nextjs", "passport", "@kinde-oss/kinde-auth-nextjs", "@hanko/elements", "@logto/next", "better-auth"},
    "state": {"redux", "@reduxjs/toolkit", "zustand", "jotai", "recoil", "valtio", "mobx", "xstate", "pinia", "vuex", "nanostores"},
    "fetch": {"axios", "got", "node-fetch", "ky", "superagent", "undici", "ofetch"},
    "validation": {"zod", "yup", "joi", "superstruct", "valibot", "ajv", "io-ts", "typebox", "@sinclair/typebox"},
    "runtime": {"ts-node", "tsx", "ts-node-dev", "nodemon", "bun", "esno", "jiti"},
    "linter": {"eslint", "biome", "@biomejs/biome", "oxlint", "rome", "tslint", "standardjs"},
    "formatter": {"prettier", "biome", "@biomejs/biome", "dprint"},
    "monorepo": {"lerna", "turbo", "nx", "rush", "pnpm"},
    "framework": {"express", "fastify", "hono", "elysia", "h3", "koa", "nest", "@nestjs/core", "hapi"},
    "react-framework": {"next", "remix", "@remix-run/react", "gatsby", "astro", "vike"},
    "date": {"moment", "dayjs", "date-fns", "luxon", "temporal-polyfill"},
    "hash": {"bcrypt", "bcryptjs", "argon2", "scrypt"},
    "email": {"nodemailer", "resend", "@sendgrid/mail", "postmark", "@react-email/components", "mailgun.js", "@plunk/node"},
    "analytics": {"posthog-js", "@posthog/react", "plausible-tracker", "@vercel/analytics", "simple-analytics-script", "fathom-client", "@aptabase/web", "@umami/node", "matomo-tracker", "@segment/analytics-next"},
    "payments": {"stripe", "@stripe/stripe-js", "@lemonsqueezy/lemonsqueezy.js", "@paddle/paddle-js", "@polar-sh/sdk"},
    "database": {"@supabase/supabase-js", "firebase", "@firebase/app", "pocketbase", "convex", "@neondatabase/serverless", "@libsql/client", "@planetscale/database", "mongoose", "mongodb", "pg", "better-sqlite3", "sql.js"},
    "search": {"meilisearch", "typesense", "algoliasearch", "@algolia/client-search", "lunr", "flexsearch", "fuse.js", "minisearch"},
    "cms": {"@sanity/client", "next-sanity", "contentful", "@strapi/strapi", "tinacms", "@directus/sdk", "@tryghost/content-api", "payload", "@keystonejs/core"},
    "queue": {"bullmq", "bull", "bee-queue", "agenda", "pg-boss"},
    "monitoring": {"@sentry/node", "@sentry/react", "@sentry/nextjs", "@highlight-run/next", "highlight.io", "@axiomhq/js", "@logtail/node", "newrelic", "@datadog/browser-rum", "pino", "winston"},
    # Python groups
    "py-testing": {"pytest", "unittest", "nose2", "ward"},
    "py-web": {"fastapi", "django", "flask", "starlette", "litestar", "sanic", "tornado", "bottle", "falcon"},
    "py-orm": {"sqlalchemy", "tortoise-orm", "peewee", "django-orm", "sqlmodel", "prisma"},
    "py-http": {"requests", "httpx", "aiohttp", "urllib3"},
}

# Build reverse lookup: package_name → set of group names
_PKG_TO_GROUPS = defaultdict(set)
for group, pkgs in SWAP_GROUPS.items():
    for pkg in pkgs:
        _PKG_TO_GROUPS[pkg].add(group)

GITHUB_API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github.v3+json"}


def get_repos_to_scan(db_path, limit):
    """Get top repos by stars from verified_combos."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT DISTINCT repo, MAX(repo_stars) as stars FROM verified_combos "
        "GROUP BY repo ORDER BY stars DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [(r[0], r[1]) for r in rows]


def get_existing_migrations(db_path):
    """Load existing migration paths to avoid duplicates."""
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT from_package, to_package, repo FROM migration_paths"
    ).fetchall()
    conn.close()
    return {(r[0], r[1], r[2]) for r in rows}


def get_package_json_commits(repo, token, max_commits=20):
    """Get recent commits that touched package.json."""
    url = f"{GITHUB_API}/repos/{repo}/commits"
    params = {"path": "package.json", "per_page": min(max_commits, 100)}
    headers = {**HEADERS}
    if token:
        headers["Authorization"] = f"token {token}"

    resp = requests.get(url, params=params, headers=headers, timeout=15)
    if resp.status_code == 404:
        return []  # Repo not found or no package.json
    if resp.status_code == 403:
        print(f"  Rate limited on {repo}, sleeping 60s...")
        time.sleep(60)
        resp = requests.get(url, params=params, headers=headers, timeout=15)
    if resp.status_code != 200:
        return []

    return resp.json()


def get_file_at_commit(repo, sha, path, token):
    """Get raw file content at a specific commit."""
    url = f"{GITHUB_API}/repos/{repo}/contents/{path}?ref={sha}"
    headers = {**HEADERS}
    if token:
        headers["Authorization"] = f"token {token}"

    resp = requests.get(url, headers=headers, timeout=15)
    if resp.status_code != 200:
        return None

    data = resp.json()
    if data.get("encoding") == "base64":
        import base64
        return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
    return data.get("content")


def extract_deps(package_json_str):
    """Extract all dependency names from a package.json string."""
    try:
        pkg = json.loads(package_json_str)
    except (json.JSONDecodeError, TypeError):
        return set()

    deps = set()
    for key in ("dependencies", "devDependencies", "peerDependencies"):
        if key in pkg and isinstance(pkg[key], dict):
            deps.update(pkg[key].keys())
    return deps


def find_swaps(removed, added):
    """Find package swaps: removed pkg in same group as added pkg."""
    swaps = []
    for rem in removed:
        rem_groups = _PKG_TO_GROUPS.get(rem, set())
        if not rem_groups:
            continue
        for add in added:
            add_groups = _PKG_TO_GROUPS.get(add, set())
            if rem_groups & add_groups:  # Same group = potential swap
                swaps.append((rem, add))
    return swaps


def mine_repo(repo, token, existing, dry_run=False):
    """Mine a single repo for migration paths. Returns list of new migrations."""
    commits = get_package_json_commits(repo, token, max_commits=15)
    if len(commits) < 2:
        return []

    new_migrations = []

    # Compare consecutive commits (newer to older)
    for i in range(len(commits) - 1):
        newer_sha = commits[i]["sha"]
        older_sha = commits[i + 1]["sha"]
        commit_date = commits[i].get("commit", {}).get("committer", {}).get("date", "")

        newer_content = get_file_at_commit(repo, newer_sha, "package.json", token)
        older_content = get_file_at_commit(repo, older_sha, "package.json", token)

        if not newer_content or not older_content:
            continue

        newer_deps = extract_deps(newer_content)
        older_deps = extract_deps(older_content)

        removed = older_deps - newer_deps
        added = newer_deps - older_deps

        if not removed or not added:
            continue

        swaps = find_swaps(removed, added)
        for from_pkg, to_pkg in swaps:
            if (from_pkg, to_pkg, repo) in existing:
                continue

            migration = {
                "from_package": from_pkg,
                "to_package": to_pkg,
                "repo": repo,
                "commit_sha": newer_sha[:12],
                "committed_at": commit_date,
                "confidence": "swap",
            }
            new_migrations.append(migration)
            existing.add((from_pkg, to_pkg, repo))

            if not dry_run:
                print(f"  SWAP: {from_pkg} -> {to_pkg} (commit {newer_sha[:8]})")

    return new_migrations


def save_migrations(db_path, migrations):
    """Insert new migrations into the database."""
    if not migrations:
        return

    conn = sqlite3.connect(db_path)
    inserted = 0
    for m in migrations:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO migration_paths "
                "(from_package, to_package, repo, commit_sha, committed_at, confidence) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (m["from_package"], m["to_package"], m["repo"],
                 m["commit_sha"], m["committed_at"], m["confidence"])
            )
            inserted += 1
        except Exception as e:
            print(f"  Insert error: {e}")
    conn.commit()
    conn.close()
    print(f"\nInserted {inserted} new migration paths.")


def main():
    parser = argparse.ArgumentParser(description="Mine GitHub repos for package migration data")
    parser.add_argument("--db", default="indiestack.db", help="Path to SQLite database")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""),
                        help="GitHub personal access token (or set GITHUB_TOKEN env)")
    parser.add_argument("--limit", type=int, default=200, help="Number of repos to scan")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be found without saving")
    args = parser.parse_args()

    if not args.token:
        print("WARNING: No GitHub token. Rate limit is 60 req/hr (vs 5,000 with token).")
        print("Set GITHUB_TOKEN env or pass --token ghp_xxx")
        print()

    print(f"Loading repos from {args.db}...")
    repos = get_repos_to_scan(args.db, args.limit)
    print(f"Found {len(repos)} repos to scan (top {args.limit} by stars)")

    existing = get_existing_migrations(args.db)
    print(f"Existing migration paths: {len(existing)}")
    print()

    all_migrations = []
    rate_limit_remaining = 5000

    for idx, (repo, stars) in enumerate(repos):
        print(f"[{idx+1}/{len(repos)}] {repo} ({stars:,} stars)...")

        try:
            migrations = mine_repo(repo, args.token, existing, dry_run=args.dry_run)
            all_migrations.extend(migrations)
        except requests.exceptions.RequestException as e:
            print(f"  Error: {e}")
            continue
        except Exception as e:
            print(f"  Unexpected error: {e}")
            continue

        # Respect rate limits — check every 10 repos
        if (idx + 1) % 10 == 0:
            # Quick rate limit check
            check = requests.get(f"{GITHUB_API}/rate_limit",
                                 headers={**HEADERS, **({"Authorization": f"token {args.token}"} if args.token else {})},
                                 timeout=10)
            if check.status_code == 200:
                remaining = check.json().get("resources", {}).get("core", {}).get("remaining", 5000)
                reset_at = check.json().get("resources", {}).get("core", {}).get("reset", 0)
                print(f"  [Rate limit: {remaining} remaining]")
                if remaining < 100:
                    wait = max(reset_at - time.time(), 60)
                    print(f"  Rate limit low, sleeping {int(wait)}s...")
                    time.sleep(wait)

    print(f"\n{'='*60}")
    print(f"Scanned: {len(repos)} repos")
    print(f"Found: {len(all_migrations)} new migration paths")

    if all_migrations:
        # Summary
        pairs = defaultdict(int)
        for m in all_migrations:
            pairs[(m["from_package"], m["to_package"])] += 1

        print(f"Unique pairs: {len(pairs)}")
        print("\nTop swaps found:")
        for (f, t), count in sorted(pairs.items(), key=lambda x: -x[1])[:20]:
            print(f"  {f} -> {t}: {count} repos")

        if not args.dry_run:
            save_migrations(args.db, all_migrations)
        else:
            print("\n(Dry run — nothing saved)")
    else:
        print("No new migrations found.")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""GitHub Compatibility Miner — discovers which IndieStack tools are used together
by scanning popular GitHub repositories' dependency files.

Searches GitHub for popular JS/TS and Python repos, fetches their dependency files
(package.json, requirements.txt, pyproject.toml), matches dependencies against
IndieStack's tool catalog, and records compatibility pairs in the tool_pairs table.

Usage:
    python3 scripts/mine_github_compatibility.py --dry-run
    python3 scripts/mine_github_compatibility.py --limit 50 --token ghp_xxx
    python3 scripts/mine_github_compatibility.py --db /path/to/indiestack.db
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
from collections import defaultdict
from itertools import combinations

import requests

# ── Well-known package name → IndieStack slug mappings ──────────────────────
# For tools where the npm/pip package name doesn't obviously match the slug.
# This supplements the automatic matching from the DB's sdk_packages column.
KNOWN_PACKAGE_MAP = {
    # npm packages
    "@supabase/supabase-js": "supabase",
    "@supabase/ssr": "supabase",
    "@supabase/auth-helpers-nextjs": "supabase",
    "supabase": "supabase",
    "@auth0/auth0-react": "auth0",
    "@auth0/nextjs-auth0": "auth0",
    "auth0": "auth0",
    "auth0-lock": "auth0",
    "stripe": "stripe",
    "@stripe/stripe-js": "stripe",
    "@stripe/react-stripe-js": "stripe",
    "posthog-js": "posthog",
    "@posthog/react": "posthog",
    "posthog-node": "posthog",
    "@sentry/node": "sentry",
    "@sentry/react": "sentry",
    "@sentry/nextjs": "sentry",
    "@sentry/browser": "sentry",
    "sentry": "sentry",
    "@clerk/nextjs": "clerk",
    "@clerk/clerk-react": "clerk",
    "@clerk/backend": "clerk",
    "@clerk/themes": "clerk",
    "next-auth": "nextauth",
    "@prisma/client": "prisma",
    "prisma": "prisma",
    "@planetscale/database": "planetscale",
    "drizzle-orm": "drizzle",
    "resend": "resend",
    "@react-email/components": "resend",
    "appwrite": "appwrite",
    "@novu/node": "novu",
    "@novu/notification-center": "novu",
    "pocketbase": "pocketbase",
    "firebase": "firebase",
    "firebase-admin": "firebase",
    "@firebase/app": "firebase",
    "convex": "convex",
    "@convex-dev/auth": "convex",
    "@upstash/redis": "upstash",
    "@upstash/ratelimit": "upstash",
    "bullmq": "bullmq",
    "bull": "bullmq",
    "@lemonsqueezy/lemonsqueezy.js": "lemon-squeezy",
    "@polar-sh/sdk": "polar",
    "@paddle/paddle-js": "paddle",
    "paddle-sdk": "paddle",
    "@kinde-oss/kinde-auth-nextjs": "kinde",
    "@logto/next": "logto",
    "@logto/node": "logto",
    "lucia": "lucia",
    "@hanko/elements": "hanko",
    "hanko-elements": "hanko",
    "payload": "payload",
    "tinacms": "tina",
    "@directus/sdk": "directus",
    "@strapi/strapi": "strapi",
    "@tryghost/content-api": "ghost",
    "@sanity/client": "sanity",
    "next-sanity": "sanity",
    "contentful": "contentful",
    "@contentful/rich-text-react-renderer": "contentful",
    "meilisearch": "meilisearch",
    "typesense": "typesense",
    "algolia": "algolia",
    "algoliasearch": "algolia",
    "@algolia/client-search": "algolia",
    "flagsmith": "flagsmith",
    "@growthbook/growthbook-react": "growthbook",
    "@growthbook/growthbook": "growthbook",
    "unleash-client": "unleash",
    "@calcom/embed-react": "cal-com",
    "plausible-tracker": "plausible-analytics",
    "simple-analytics-script": "simple-analytics",
    "@umami/node": "umami",
    "fathom-client": "fathom-analytics",
    "pirsch-sdk": "pirsch",
    "@aptabase/web": "aptabase",
    "@aptabase/react": "aptabase",
    "matomo-tracker": "matomo",
    "countly-sdk-web": "countly",
    "cloudinary": "cloudinary",
    "@uploadthing/react": "uploadthing",
    "uploadthing": "uploadthing",
    "minio": "minio",
    "@plunk/node": "plunk",
    "postmark": "postmark",
    "nodemailer": "nodemailer",
    "@sendgrid/mail": "sendgrid",
    "mailgun.js": "mailgun",
    "@ory/client": "ory",
    "@zitadel/node": "zitadel",
    "keycloak-js": "keycloak",
    "redis": "redis",
    "ioredis": "redis",
    "@libsql/client": "turso",
    "@neondatabase/serverless": "neon",
    "mongoose": "mongodb",
    "mongodb": "mongodb",
    "@vercel/analytics": "vercel-analytics",
    "@vercel/speed-insights": "vercel-analytics",
    "tailwindcss": "tailwind-css",
    "daisyui": "daisyui",
    "@radix-ui/react-dialog": "radix-ui",
    "@radix-ui/themes": "radix-ui",
    "@shadcn/ui": "shadcn-ui",
    "framer-motion": "framer-motion",
    "@headlessui/react": "headless-ui",
    "zod": "zod",
    "trpc": "trpc",
    "@trpc/server": "trpc",
    "@trpc/client": "trpc",
    "inngest": "inngest",
    "trigger.dev": "trigger-dev",
    "@trigger.dev/sdk": "trigger-dev",
    "highlight.io": "highlight",
    "@highlight-run/next": "highlight",
    "axiom": "axiom",
    "@axiomhq/js": "axiom",
    "@logtail/node": "betterstack",
    "graphql-yoga": "graphql-yoga",
    "nextra": "nextra",
    "mintlify": "mintlify",
    "docusaurus": "docusaurus",
    "@docusaurus/core": "docusaurus",
    "storybook": "storybook",
    "@storybook/react": "storybook",
    "chromatic": "chromatic",
    "cypress": "cypress",
    "playwright": "playwright",
    "@playwright/test": "playwright",
    "vitest": "vitest",
    "jest": "jest",

    # pip packages
    "posthog": "posthog",
    "sentry-sdk": "sentry",
    "sentry_sdk": "sentry",
    "stripe": "stripe",
    "supabase": "supabase",
    "appwrite": "appwrite",
    "resend": "resend",
    "meilisearch": "meilisearch",
    "typesense": "typesense",
    "flagsmith": "flagsmith",
    "UnleashClient": "unleash",
    "qdrant-client": "qdrant",
    "weaviate-client": "weaviate",
    "minio": "minio",
    "cloudinary": "cloudinary",
    "firecrawl-py": "firecrawl",
    "lago-python-client": "lago",
    "killbill": "kill-bill",
    "polar-python": "polar",
    "paddle-billing": "paddle",
    "clerk-backend-api": "clerk",
    "novu": "novu",
    "ntfy-wrapper": "ntfy",
    "dify-client": "dify",
    "hanko-python": "hanko",
    "supertokens-python": "supertokens",
    "ory-client": "ory",
    "redis": "redis",
    "celery": "celery",
    "dramatiq": "dramatiq",
    "boto3": "aws-s3",
    "django-allauth": "django-allauth",
    "authlib": "authlib",
    "fastapi": "fastapi",
    "django": "django",
    "flask": "flask",
    "sqlalchemy": "sqlalchemy",
    "prisma": "prisma",
    "psycopg2": "postgresql",
    "psycopg2-binary": "postgresql",
    "pymongo": "mongodb",
    "motor": "mongodb",
    "httpx": "httpx",
    "pydantic": "pydantic",
    "alembic": "alembic",
    "pytest": "pytest",
    "pirsch-api": "pirsch",
    "plausible-tracker": "plausible-analytics",
}


# Packages that are too generic to belong to any single IndieStack tool.
# These appear in sdk_packages due to bad data and cause false positive matches.
_PACKAGE_BLOCKLIST = {
    # Common JS/TS packages
    'eslint', 'prettier', 'typescript', 'webpack', 'babel', 'jest', 'mocha',
    'lodash', 'express', 'react', 'react-dom', 'vue', 'angular', 'svelte',
    'next', 'nuxt', 'vite', 'rollup', 'esbuild', 'tsup', 'nodemon',
    'dotenv', 'cors', 'helmet', 'morgan', 'debug', 'chalk', 'commander',
    'yargs', 'inquirer', 'ora', 'glob', 'rimraf', 'cross-env', 'concurrently',
    'husky', 'lint-staged', 'vitest', 'cypress', 'playwright',
    # Common Python packages
    'pyyaml', 'build', 'setuptools', 'wheel', 'pip', 'virtualenv',
    'beautifulsoup4', 'bs4', 'lxml', 'pygments', 'click', 'rich',
    'black', 'isort', 'flake8', 'mypy', 'pylint', 'ruff',
    'pytest', 'tox', 'coverage', 'sphinx', 'mkdocs',
    'requests', 'urllib3', 'certifi', 'charset-normalizer', 'idna',
    'numpy', 'pandas', 'scipy', 'matplotlib', 'pillow', 'tqdm',
    'psutil', 'attrs', 'six', 'packaging', 'typing-extensions',
    'cryptography', 'cffi', 'pycparser',
}


def load_tool_catalog(db_path):
    """Load all approved tools and build package-name → slug lookup maps."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cursor = conn.execute("""
        SELECT name, slug, url, github_url, sdk_packages
        FROM tools
        WHERE status = 'approved'
    """)
    tools = cursor.fetchall()
    conn.close()

    # Build the mapping: package_name (lowercase) → slug
    pkg_to_slug = {}

    # 1. Start with the hardcoded well-known mappings
    for pkg, slug in KNOWN_PACKAGE_MAP.items():
        pkg_to_slug[pkg.lower()] = slug

    # 2. Add mappings from the DB's sdk_packages column (JSON like {"npm": "pkg", "pip": "pkg"})
    for tool in tools:
        slug = tool["slug"]
        sdk_raw = tool["sdk_packages"]
        if sdk_raw:
            try:
                sdk = json.loads(sdk_raw)
                if isinstance(sdk, dict):
                    # {"npm": "pkg-name", "pip": "pkg-name"}
                    for ecosystem, pkg_name in sdk.items():
                        if pkg_name and isinstance(pkg_name, str) and pkg_name.lower() not in _PACKAGE_BLOCKLIST:
                            pkg_to_slug[pkg_name.lower()] = slug
                elif isinstance(sdk, list):
                    # ["pkg-name", "other-pkg"]
                    for pkg_name in sdk:
                        if pkg_name and isinstance(pkg_name, str) and pkg_name.lower() not in _PACKAGE_BLOCKLIST:
                            pkg_to_slug[pkg_name.lower()] = slug
            except (json.JSONDecodeError, TypeError):
                pass

    # 3. Add slug itself as a package name match (e.g., "resend" slug matches "resend" package)
    slug_set = set()
    for tool in tools:
        slug = tool["slug"]
        slug_set.add(slug)
        pkg_to_slug[slug.lower()] = slug
        # Also try the tool name lowercased and hyphenated
        name_slug = re.sub(r'[^a-z0-9]+', '-', tool["name"].lower()).strip('-')
        if name_slug and name_slug not in pkg_to_slug:
            pkg_to_slug[name_slug] = slug

    # 4. Extract repo names from github_url as potential package names
    github_re = re.compile(r'github\.com/([^/]+)/([^/?#]+)')
    for tool in tools:
        slug = tool["slug"]
        gh_url = tool["github_url"] or ""
        m = github_re.search(gh_url)
        if m:
            repo_name = m.group(2).lower().rstrip('.git')
            if repo_name not in pkg_to_slug:
                pkg_to_slug[repo_name] = slug
            # Also try org/repo for scoped-like matching
            org_repo = f"{m.group(1).lower()}/{repo_name}"
            if org_repo not in pkg_to_slug:
                pkg_to_slug[org_repo] = slug

    print(f"Loaded {len(tools)} approved tools, {len(pkg_to_slug)} package name mappings")
    return pkg_to_slug, slug_set


def github_headers(token):
    """Build request headers for GitHub API."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "IndieStack-CompatibilityMiner/1.0",
    }
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def check_rate_limit(response, token):
    """Check GitHub rate limit headers and sleep if needed."""
    remaining = response.headers.get("X-RateLimit-Remaining")
    reset_at = response.headers.get("X-RateLimit-Reset")

    if remaining is not None:
        remaining = int(remaining)
        if remaining <= 1:
            if reset_at:
                wait = max(int(reset_at) - int(time.time()), 1) + 5
            else:
                wait = 60
            print(f"  Rate limit nearly exhausted ({remaining} remaining). Sleeping {wait}s...")
            time.sleep(wait)
        elif remaining <= 5:
            print(f"  Rate limit low: {remaining} remaining")


def search_github_repos(language, token, limit, per_page=30):
    """Search GitHub for popular repos in a given language."""
    repos = []
    page = 1
    headers = github_headers(token)

    while len(repos) < limit:
        url = (
            f"https://api.github.com/search/repositories"
            f"?q=stars:>500+language:{language}"
            f"&sort=stars&order=desc&per_page={per_page}&page={page}"
        )
        try:
            resp = requests.get(url, headers=headers, timeout=30)
            check_rate_limit(resp, token)

            if resp.status_code == 403:
                print(f"  Rate limited on search page {page}. Waiting 60s...")
                time.sleep(60)
                continue
            if resp.status_code != 200:
                print(f"  Search API returned {resp.status_code} for {language} page {page}")
                break

            data = resp.json()
            items = data.get("items", [])
            if not items:
                break

            for item in items:
                repos.append({
                    "full_name": item["full_name"],
                    "owner": item["owner"]["login"],
                    "name": item["name"],
                    "stars": item["stargazers_count"],
                    "language": item.get("language", ""),
                    "default_branch": item.get("default_branch", "main"),
                })
                if len(repos) >= limit:
                    break

            page += 1
            # Be polite between search pages
            time.sleep(2)

        except requests.RequestException as e:
            print(f"  Error searching {language} repos: {e}")
            break

    return repos


def fetch_file_raw(owner, repo, branch, filepath, token):
    """Fetch a raw file from a GitHub repo. Returns content string or None."""
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{filepath}"
    headers = {"User-Agent": "IndieStack-CompatibilityMiner/1.0"}
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        if resp.status_code == 200:
            return resp.text
        return None
    except requests.RequestException:
        return None


def parse_package_json(content):
    """Extract dependency package names from package.json content."""
    deps = set()
    try:
        data = json.loads(content)
        for section in ("dependencies", "devDependencies", "peerDependencies"):
            section_deps = data.get(section, {})
            if isinstance(section_deps, dict):
                deps.update(section_deps.keys())
    except (json.JSONDecodeError, TypeError):
        pass
    return deps


def parse_requirements_txt(content):
    """Extract package names from requirements.txt content."""
    deps = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Remove version specifiers, extras, and comments
        # e.g. "requests>=2.0,<3.0 # http client" → "requests"
        # e.g. "package[extra]>=1.0" → "package"
        pkg = re.split(r'[>=<!\[;#\s]', line)[0].strip()
        if pkg:
            deps.add(pkg)
    return deps


def parse_pyproject_toml(content):
    """Extract dependency package names from pyproject.toml (basic parsing)."""
    deps = set()
    in_deps = False
    for line in content.splitlines():
        stripped = line.strip()
        # Detect [project.dependencies] or [tool.poetry.dependencies]
        if re.match(r'\[(project\.dependencies|tool\.poetry\.dependencies)\]', stripped):
            in_deps = True
            continue
        if stripped.startswith("[") and in_deps:
            in_deps = False
            continue
        if in_deps:
            # Poetry style: package = "^1.0"
            m = re.match(r'^([a-zA-Z0-9_-]+)\s*=', stripped)
            if m:
                deps.add(m.group(1))
            # PEP 621 style: "package>=1.0",
            m2 = re.match(r'^"([a-zA-Z0-9_-]+)', stripped)
            if m2:
                deps.add(m2.group(1))

    # Also catch dependencies = [...] inline style
    # Match: dependencies = ["pkg1>=1.0", "pkg2"]
    dep_block = re.findall(r'dependencies\s*=\s*\[(.*?)\]', content, re.DOTALL)
    for block in dep_block:
        for m in re.finditer(r'"([a-zA-Z0-9_][a-zA-Z0-9._-]*)', block):
            pkg = re.split(r'[>=<!\[;]', m.group(1))[0]
            if pkg:
                deps.add(pkg)

    return deps


def match_deps_to_tools(deps, pkg_to_slug):
    """Match a set of dependency package names against IndieStack tools.
    Returns a set of matched tool slugs."""
    matched_slugs = set()
    for dep in deps:
        dep_lower = dep.lower()
        # Direct match
        if dep_lower in pkg_to_slug:
            matched_slugs.add(pkg_to_slug[dep_lower])
            continue
        # Try matching scoped packages by their base name
        # e.g., "@sentry/nextjs" → check "sentry"
        if dep_lower.startswith("@"):
            parts = dep_lower.split("/")
            if len(parts) >= 2:
                # Try org name (without @)
                org = parts[0][1:]
                if org in pkg_to_slug:
                    matched_slugs.add(pkg_to_slug[org])
                    continue
                # Try full scoped name
                scoped = f"{parts[0]}/{parts[1]}"
                if scoped in pkg_to_slug:
                    matched_slugs.add(pkg_to_slug[scoped])
                    continue
        # Fuzzy: check if the dep name is a substring of any slug or vice versa
        # (only for names 4+ chars to avoid false positives)
        if len(dep_lower) >= 4:
            for pkg_name, slug in pkg_to_slug.items():
                if dep_lower == pkg_name:
                    matched_slugs.add(slug)
                    break
    return matched_slugs


def record_pairs_in_db(db_path, pair_counts, dry_run):
    """Insert compatibility pairs into the tool_pairs table."""
    if dry_run:
        print("\n[DRY RUN] Would insert the following pairs:")
        for (a, b), count in sorted(pair_counts.items(), key=lambda x: -x[1]):
            print(f"  {a} + {b} (seen in {count} repos)")
        return 0

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    new_pairs = 0

    for (slug_a, slug_b), count in pair_counts.items():
        a, b = sorted([slug_a, slug_b])
        try:
            cursor = conn.execute(
                "SELECT id, success_count FROM tool_pairs WHERE tool_a_slug = ? AND tool_b_slug = ?",
                (a, b),
            )
            existing = cursor.fetchone()
            if existing:
                # Increment success_count by the number of repos where this pair was seen
                conn.execute(
                    "UPDATE tool_pairs SET success_count = success_count + ? WHERE id = ?",
                    (count, existing["id"]),
                )
            else:
                conn.execute(
                    """INSERT INTO tool_pairs (tool_a_slug, tool_b_slug, source, success_count)
                       VALUES (?, ?, 'github_mining', ?)""",
                    (a, b, count),
                )
                new_pairs += 1
        except sqlite3.Error as e:
            print(f"  DB error for pair {a} + {b}: {e}")

    conn.commit()
    conn.close()
    return new_pairs


def main():
    parser = argparse.ArgumentParser(
        description="Mine GitHub repos to discover IndieStack tool compatibility pairs."
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would be inserted without writing to the DB",
    )
    parser.add_argument(
        "--db", default=None,
        help="Path to indiestack.db (default: auto-detect)",
    )
    parser.add_argument(
        "--limit", type=int, default=100,
        help="Max repos to scan per language (default: 100)",
    )
    parser.add_argument(
        "--token", default=None,
        help="GitHub API token (or set GITHUB_TOKEN env var)",
    )
    args = parser.parse_args()

    # Resolve DB path
    db_path = args.db
    if not db_path:
        # Try local dev path first, then production
        local_path = os.path.join(os.path.dirname(__file__), "..", "indiestack.db")
        local_path = os.path.abspath(local_path)
        if os.path.exists(local_path):
            db_path = local_path
        elif os.path.exists("/data/indiestack.db"):
            db_path = "/data/indiestack.db"
        else:
            print("ERROR: Cannot find indiestack.db. Use --db to specify path.")
            sys.exit(1)

    # Resolve GitHub token
    token = args.token or os.environ.get("GITHUB_TOKEN", "")

    print("GitHub Compatibility Miner")
    print("==========================")
    print(f"Database: {db_path}")
    print(f"GitHub token: {'set' if token else 'NOT SET (10 req/min limit)'}")
    print(f"Repo limit per language: {args.limit}")
    print(f"Dry run: {args.dry_run}")
    print()

    # 1. Load tool catalog
    pkg_to_slug, slug_set = load_tool_catalog(db_path)
    print()

    # 2. Search GitHub for popular repos
    print("Searching GitHub for popular repositories...")
    js_repos = search_github_repos("javascript", token, args.limit)
    print(f"  Found {len(js_repos)} JavaScript/TypeScript repos")

    # Brief pause between search queries
    time.sleep(3)

    python_repos = search_github_repos("python", token, args.limit)
    print(f"  Found {len(python_repos)} Python repos")
    print()

    # Deduplicate repos (a repo might appear in both searches)
    seen_repos = set()
    all_repos = []
    for repo in js_repos + python_repos:
        if repo["full_name"] not in seen_repos:
            seen_repos.add(repo["full_name"])
            all_repos.append(repo)

    print(f"Total unique repos to scan: {len(all_repos)}")
    print()

    # 3. Scan each repo's dependency files
    repos_scanned = 0
    repos_with_deps = 0
    pair_counts = defaultdict(int)  # (slug_a, slug_b) → count of repos
    stack_counts = defaultdict(int)  # (slug_a, slug_b, slug_c, ...) → count of repos (3+ tools)
    repo_matches = []  # For summary: (repo_name, matched_slugs)

    for i, repo in enumerate(all_repos):
        owner = repo["owner"]
        name = repo["name"]
        branch = repo["default_branch"]
        lang = repo["language"] or ""
        stars = repo["stars"]

        print(f"[{i+1}/{len(all_repos)}] {repo['full_name']} ({stars} stars, {lang})")
        repos_scanned += 1

        all_deps = set()

        # Fetch JS/TS dependency files
        pkg_json = fetch_file_raw(owner, name, branch, "package.json", token)
        if pkg_json:
            deps = parse_package_json(pkg_json)
            all_deps.update(deps)

        # Small delay between file fetches
        time.sleep(0.5)

        # Fetch Python dependency files
        req_txt = fetch_file_raw(owner, name, branch, "requirements.txt", token)
        if req_txt:
            deps = parse_requirements_txt(req_txt)
            all_deps.update(deps)

        time.sleep(0.5)

        pyproject = fetch_file_raw(owner, name, branch, "pyproject.toml", token)
        if pyproject:
            deps = parse_pyproject_toml(pyproject)
            all_deps.update(deps)

        if not all_deps:
            print(f"  No dependency files found")
            # Rate limit between repos
            time.sleep(1)
            continue

        repos_with_deps += 1

        # 4. Match dependencies against IndieStack tools
        matched_slugs = match_deps_to_tools(all_deps, pkg_to_slug)

        # Filter to only slugs that actually exist in the DB
        matched_slugs = matched_slugs & slug_set

        if len(matched_slugs) >= 2:
            print(f"  Found {len(all_deps)} deps, {len(matched_slugs)} IndieStack matches: {', '.join(sorted(matched_slugs))}")
            repo_matches.append((repo["full_name"], sorted(matched_slugs)))

            # Record all pairs from this repo
            for slug_a, slug_b in combinations(sorted(matched_slugs), 2):
                pair_counts[(slug_a, slug_b)] += 1

            # Record stacks (triplets, quads, etc.) — full tool sets from real repos
            if len(matched_slugs) >= 3:
                stack_key = tuple(sorted(matched_slugs))
                stack_counts[stack_key] += 1
        elif len(matched_slugs) == 1:
            print(f"  Found {len(all_deps)} deps, 1 IndieStack match: {list(matched_slugs)[0]} (need 2+ for pairs)")
        else:
            print(f"  Found {len(all_deps)} deps, no IndieStack matches")

        # Rate limit between repos
        time.sleep(1)

    # 5. Record pairs in DB
    print()
    print("=" * 60)
    new_pairs = record_pairs_in_db(db_path, pair_counts, args.dry_run)

    # 6. Print summary
    print()
    print("Summary")
    print("-------")
    print(f"  Repos scanned:          {repos_scanned}")
    print(f"  Repos with deps:        {repos_with_deps}")
    print(f"  Repos with 2+ matches:  {len(repo_matches)}")
    print(f"  Unique pairs found:     {len(pair_counts)}")
    print(f"  New pairs inserted:     {new_pairs}" + (" (dry run)" if args.dry_run else ""))
    print()

    if pair_counts:
        print("Top compatibility pairs (by repo frequency):")
        top_pairs = sorted(pair_counts.items(), key=lambda x: -x[1])[:25]
        for (a, b), count in top_pairs:
            print(f"  {a} + {b}: seen in {count} repo(s)")
        print()

    if stack_counts:
        print(f"Discovered stacks (3+ tools used together):")
        top_stacks = sorted(stack_counts.items(), key=lambda x: (-len(x[0]), -x[1]))[:25]
        for stack, count in top_stacks:
            size_label = {3: "triplet", 4: "quad", 5: "quint"}.get(len(stack), f"{len(stack)}-tool stack")
            print(f"  [{size_label}] {' + '.join(stack)} (seen in {count} repo{'s' if count > 1 else ''})")
        print()

    if repo_matches:
        print(f"Repos with multiple IndieStack tools ({len(repo_matches)} total):")
        for repo_name, slugs in repo_matches[:20]:
            print(f"  {repo_name}: {', '.join(slugs)}")
        if len(repo_matches) > 20:
            print(f"  ... and {len(repo_matches) - 20} more")
        print()

    print("Done!")


if __name__ == "__main__":
    main()

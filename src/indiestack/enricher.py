"""
README Metadata Enricher for IndieStack.

Fetches GitHub READMEs, extracts install commands, env vars, and framework mentions,
then updates tools with structured metadata.

Usage:
    python3 -m indiestack.enricher --dry-run
    python3 -m indiestack.enricher --dry-run --limit 10
    python3 -m indiestack.enricher --apply --limit 50
"""

import argparse
import asyncio
import base64
import json
import os
import re
import sys
from urllib.parse import urlparse

import httpx

# ── Install command patterns ──────────────────────────────────────────────

INSTALL_PATTERNS = [
    # npm / yarn / pnpm / bun
    (r"(?:npm install|npm i)\s+([\w@/.-]+)", "npm install {pkg}"),
    (r"yarn add\s+([\w@/.-]+)", "yarn add {pkg}"),
    (r"pnpm (?:add|install)\s+([\w@/.-]+)", "pnpm add {pkg}"),
    (r"bun add\s+([\w@/.-]+)", "bun add {pkg}"),
    # pip / pipx
    (r"pip install\s+([\w.-]+)", "pip install {pkg}"),
    (r"pipx install\s+([\w.-]+)", "pipx install {pkg}"),
    # cargo
    (r"cargo install\s+([\w.-]+)", "cargo install {pkg}"),
    # brew
    (r"brew install\s+([\w.-]+)", "brew install {pkg}"),
    # go
    (r"go install\s+([\w./]+)@", "go install {pkg}"),
    # docker
    (r"docker pull\s+([\w./:_-]+)", "docker pull {pkg}"),
    (r"docker run\s+(?:-[a-z]+\s+)*?([\w./:_-]+)", "docker run {pkg}"),
    # composer
    (r"composer require\s+([\w/.-]+)", "composer require {pkg}"),
    # gem
    (r"gem install\s+([\w.-]+)", "gem install {pkg}"),
]

# ── Framework detection ──────────────────────────────────────────────────

FRAMEWORK_KEYWORDS = {
    "react": "react", "next.js": "nextjs", "nextjs": "nextjs", "next js": "nextjs",
    "vue": "vue", "nuxt": "nuxt", "angular": "angular", "svelte": "svelte",
    "sveltekit": "sveltekit", "astro": "astro", "remix": "remix",
    "django": "django", "flask": "flask", "fastapi": "fastapi",
    "express": "express", "koa": "koa", "hono": "hono", "elysia": "elysia",
    "rails": "rails", "ruby on rails": "rails",
    "spring": "spring", "spring boot": "spring-boot",
    "laravel": "laravel", "symfony": "symfony",
    "gin": "gin", "echo": "echo-go", "fiber": "fiber",
    "actix": "actix", "axum": "axum", "rocket": "rocket-rs",
    "htmx": "htmx", "tailwind": "tailwind", "bootstrap": "bootstrap",
    "electron": "electron", "tauri": "tauri",
    "flutter": "flutter", "react native": "react-native",
    "supabase": "supabase", "pocketbase": "pocketbase", "firebase": "firebase",
}

# ── Env var patterns ──────────────────────────────────────────────────────

ENV_VAR_PATTERN = re.compile(
    r"\b([A-Z][A-Z0-9_]*(?:_KEY|_TOKEN|_SECRET|_PASSWORD|_URL|_API|_HOST|_PORT|_DSN|_URI|_ENDPOINT))\b"
)

# Common env var names that aren't tool-specific
GENERIC_ENV_VARS = {
    "API_KEY", "API_TOKEN", "API_SECRET", "API_URL", "API_HOST", "API_PORT",
    "DATABASE_URL", "DATABASE_HOST", "DATABASE_PORT", "DATABASE_PASSWORD",
    "REDIS_URL", "REDIS_HOST", "REDIS_PORT",
    "SECRET_KEY", "SESSION_SECRET",
}


def extract_from_readme(readme_text: str) -> dict:
    """Extract metadata from a README's text content."""
    text = readme_text.lower()
    original = readme_text  # keep original case for env vars

    result = {
        "install_command": "",
        "sdk_packages": [],
        "env_vars": [],
        "frameworks_tested": [],
    }

    # ── Install commands ──
    for pattern, template in INSTALL_PATTERNS:
        matches = re.findall(pattern, readme_text, re.IGNORECASE)
        if matches:
            # Take the first real package match
            pkg = matches[0].strip()
            if pkg and not pkg.startswith("-") and len(pkg) > 1:
                result["install_command"] = template.format(pkg=pkg)
                result["sdk_packages"].append(pkg)
                break  # use first install command found

    # ── Env vars ──
    env_vars = set(ENV_VAR_PATTERN.findall(original))
    # Filter out very generic ones, keep tool-specific
    specific_vars = [v for v in env_vars if v not in GENERIC_ENV_VARS]
    if specific_vars:
        result["env_vars"] = sorted(specific_vars)[:6]  # cap at 6
    elif env_vars:
        # If only generic vars found, include up to 3
        result["env_vars"] = sorted(env_vars)[:3]

    # ── Frameworks ──
    found_frameworks = set()
    for keyword, framework in FRAMEWORK_KEYWORDS.items():
        # Look for the keyword as a word boundary match
        if re.search(rf"\b{re.escape(keyword)}\b", text):
            found_frameworks.add(framework)
    if found_frameworks:
        result["frameworks_tested"] = sorted(found_frameworks)[:8]

    return result


def parse_github_url(url: str) -> tuple[str, str] | None:
    """Extract owner/repo from a GitHub URL."""
    parsed = urlparse(url)
    if "github.com" not in parsed.netloc:
        return None
    parts = parsed.path.strip("/").split("/")
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None


async def fetch_readme(
    client: httpx.AsyncClient, owner: str, repo: str
) -> str | None:
    """Fetch and decode a README from the GitHub API."""
    try:
        resp = await client.get(
            f"https://api.github.com/repos/{owner}/{repo}/readme",
            headers={"Accept": "application/vnd.github+json"},
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()

        data = resp.json()
        content = data.get("content", "")
        encoding = data.get("encoding", "")

        if encoding == "base64" and content:
            return base64.b64decode(content).decode("utf-8", errors="replace")
        return content
    except Exception as e:
        print(f"    Error fetching README for {owner}/{repo}: {e}")
        return None


async def check_rate_limit(response: httpx.Response) -> None:
    """Sleep if GitHub rate limit is getting low."""
    from datetime import datetime, timezone

    remaining = response.headers.get("X-RateLimit-Remaining")
    if remaining is not None:
        remaining = int(remaining)
        if remaining <= 2:
            reset_ts = int(response.headers.get("X-RateLimit-Reset", "0"))
            sleep_for = max(reset_ts - int(datetime.now(timezone.utc).timestamp()), 1)
            print(f"  Rate limit nearly exhausted ({remaining} left). Sleeping {sleep_for}s...")
            await asyncio.sleep(sleep_for)
        elif remaining <= 10:
            print(f"  Rate limit warning: {remaining} requests remaining")


async def run(args: argparse.Namespace) -> None:
    """Main async entrypoint."""
    import aiosqlite

    db_path = os.environ.get("DATABASE_PATH", "/data/indiestack.db")
    github_token = os.environ.get("GITHUB_TOKEN", "")

    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
        print("Using authenticated GitHub API (5,000 req/hr)")
    else:
        print("WARNING: No GITHUB_TOKEN set. Rate limit: 60 req/hr.")
        print("  Set GITHUB_TOKEN env var for 5,000 req/hr.\n")

    limit = args.limit or 999999
    apply_changes = args.apply
    dry_run = args.dry_run

    if apply_changes and dry_run:
        print("ERROR: Cannot use both --apply and --dry-run")
        sys.exit(1)

    if not apply_changes and not dry_run:
        print("Specify --dry-run to preview or --apply to update.\n")
        dry_run = True

    # ── Load tools needing enrichment ──
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT id, name, slug, github_url
            FROM tools
            WHERE status = 'approved'
              AND github_url IS NOT NULL AND github_url != ''
              AND (sdk_packages IS NULL OR sdk_packages = '')
            ORDER BY github_stars DESC
            LIMIT ?
        """, (limit,))
        tools = await cursor.fetchall()

    print(f"Found {len(tools)} tools needing README enrichment\n")

    if not tools:
        print("Nothing to enrich.")
        return

    # ── Fetch READMEs and extract metadata ──
    results: list[dict] = []
    skipped = 0
    errors = 0

    async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
        for i, tool in enumerate(tools, 1):
            name = tool["name"]
            github_url = tool["github_url"]
            parsed = parse_github_url(github_url)

            if not parsed:
                skipped += 1
                continue

            owner, repo = parsed
            print(f"  [{i}/{len(tools)}] {name} ({owner}/{repo})...", end=" ")

            readme = await fetch_readme(client, owner, repo)
            if not readme:
                print("no README")
                skipped += 1
                continue

            extracted = extract_from_readme(readme)

            # Only count as enriched if we found something useful
            has_data = (
                extracted["install_command"]
                or extracted["env_vars"]
                or extracted["frameworks_tested"]
            )

            if has_data:
                results.append({
                    "id": tool["id"],
                    "name": name,
                    "slug": tool["slug"],
                    **extracted,
                })
                found_parts = []
                if extracted["install_command"]:
                    found_parts.append(f"install: {extracted['install_command']}")
                if extracted["env_vars"]:
                    found_parts.append(f"env: {','.join(extracted['env_vars'][:3])}")
                if extracted["frameworks_tested"]:
                    found_parts.append(f"frameworks: {','.join(extracted['frameworks_tested'][:3])}")
                print(" | ".join(found_parts))
            else:
                print("(no metadata found)")
                skipped += 1

            # Rate limit politeness
            await asyncio.sleep(0.5)

    # ── Report ──
    print(f"\n{'='*60}")
    print(f"Enriched: {len(results)}")
    print(f"Skipped:  {skipped}")
    print(f"Errors:   {errors}")
    print(f"Total:    {len(tools)}")

    if dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN — would update the following tools:")
        print(f"{'='*60}\n")
        for r in results:
            print(f"  {r['name']} ({r['slug']})")
            if r["install_command"]:
                print(f"    install: {r['install_command']}")
            if r["sdk_packages"]:
                print(f"    packages: {json.dumps(r['sdk_packages'])}")
            if r["env_vars"]:
                print(f"    env_vars: {json.dumps(r['env_vars'])}")
            if r["frameworks_tested"]:
                print(f"    frameworks: {','.join(r['frameworks_tested'])}")
            print()
        return

    # ── Apply ──
    if not results:
        print("\nNothing to apply.")
        return

    print(f"\nApplying enrichment to {len(results)} tools...")
    async with aiosqlite.connect(db_path) as db:
        updated = 0
        for r in results:
            try:
                await db.execute("""
                    UPDATE tools SET
                        install_command = CASE WHEN (install_command IS NULL OR install_command = '') THEN ? ELSE install_command END,
                        sdk_packages = CASE WHEN (sdk_packages IS NULL OR sdk_packages = '') THEN ? ELSE sdk_packages END,
                        env_vars = CASE WHEN (env_vars IS NULL OR env_vars = '') THEN ? ELSE env_vars END,
                        frameworks_tested = CASE WHEN (frameworks_tested IS NULL OR frameworks_tested = '') THEN ? ELSE frameworks_tested END
                    WHERE id = ?
                """, (
                    r["install_command"],
                    json.dumps(r["sdk_packages"]) if r["sdk_packages"] else "",
                    json.dumps(r["env_vars"]) if r["env_vars"] else "",
                    ",".join(r["frameworks_tested"]) if r["frameworks_tested"] else "",
                    r["id"],
                ))
                updated += 1
            except Exception as e:
                print(f"  ERROR updating {r['name']}: {e}")
                errors += 1

        await db.commit()

    print(f"\nUpdated {updated} tools, {errors} errors")


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="IndieStack README Enricher — extract metadata from GitHub READMEs",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Max tools to process (default: all)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be updated without changing anything",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually update tools in the database",
    )

    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()

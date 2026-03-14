"""
README Metadata Enricher for IndieStack.

Fetches GitHub READMEs, extracts install commands, env vars, and framework mentions,
then updates tools with structured metadata.

Section-aware: prioritises commands under "Installation"/"Getting Started" headings,
skips commands under "Development"/"Contributing" headings, and filters out common
prerequisite packages (npm, python, ffmpeg, etc.) that aren't the tool itself.

Usage:
    python3 -m indiestack.enricher --dry-run
    python3 -m indiestack.enricher --dry-run --limit 10
    python3 -m indiestack.enricher --apply --limit 50
    python3 -m indiestack.enricher --re-enrich --apply   # fix bad extractions
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
    # npm / yarn / pnpm / bun  (skip optional flags like -g, --save-dev)
    (r"(?:npm install|npm i)\s+(?:-\S+\s+)*([\w@/.-]+)", "npm install {pkg}"),
    (r"yarn add\s+(?:-\S+\s+)*([\w@/.-]+)", "yarn add {pkg}"),
    (r"pnpm (?:add|install)\s+(?:-\S+\s+)*([\w@/.-]+)", "pnpm add {pkg}"),
    (r"bun add\s+(?:-\S+\s+)*([\w@/.-]+)", "bun add {pkg}"),
    # pip / pipx  (skip flags like -U, --upgrade, but NOT -r which means requirements file)
    (r"pip install\s+(?:-(?!r\b)\S+\s+)*([\w.-]+)", "pip install {pkg}"),
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

# ── Section classification ────────────────────────────────────────────────

# Headings that indicate "how to install this tool"
_INSTALL_HEADINGS = {
    "installation", "install", "getting started", "quick start", "quickstart",
    "get started", "setup", "how to install", "installing",
}

# Headings that indicate dev setup / prerequisites (not the tool itself)
_DEV_HEADINGS = {
    "development", "developing", "contributing", "building", "building from source",
    "build from source", "prerequisites", "requirements", "local development",
    "dev setup", "developer setup", "local setup", "compilation", "compiling",
    "hacking", "development setup", "contributing guide",
}

# Common prerequisite packages that are almost never the tool itself.
# If the extracted package name matches one of these AND doesn't match the
# tool's own slug, we skip it — it's a dependency, not the install command.
COMMON_PREREQUISITES = {
    # Package managers / runtimes
    "npm", "npx", "pnpm", "yarn", "bun", "node", "nodejs", "nvm",
    "python", "python3", "pip", "pip3", "uv", "pipx", "virtualenv", "poetry",
    "cargo", "rustup", "rust",
    "go", "golang",
    "ruby", "bundler",
    "php", "composer",
    # Build tools
    "make", "cmake", "gcc", "g++", "clang", "meson", "ninja",
    "git", "curl", "wget",
    # Common system libraries / tools
    "openssl", "libssl-dev", "libssl", "libffi", "libffi-dev",
    "ffmpeg", "imagemagick", "graphviz",
    "protobuf", "protoc", "grpc",
    "sqlite3", "sqlite", "postgresql", "postgres", "mysql", "redis",
    "nginx", "apache2", "httpd",
    "docker", "docker-compose", "podman",
    "grep", "fswatch", "watchman", "entr", "inotify-tools",
    "libunistring", "libev", "libevent", "libuv",
    "pkg-config", "autoconf", "automake", "libtool",
    "https",  # nonsensical but appeared in prod data
}

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


def _parse_sections(readme_text: str) -> list[tuple[str, str]]:
    """Split a README into (heading, body) pairs by markdown headers."""
    sections: list[tuple[str, str]] = []
    current_heading = ""
    body_lines: list[str] = []

    for line in readme_text.split("\n"):
        header_match = re.match(r"^#{1,4}\s+(.+)", line)
        if header_match:
            if body_lines or current_heading:
                sections.append((current_heading, "\n".join(body_lines)))
            current_heading = header_match.group(1).strip()
            body_lines = []
        else:
            body_lines.append(line)

    if body_lines or current_heading:
        sections.append((current_heading, "\n".join(body_lines)))

    return sections


def _classify_heading(heading: str) -> str:
    """Classify a section heading as 'install', 'dev', or 'other'."""
    h = heading.lower().strip()
    for kw in _INSTALL_HEADINGS:
        if kw in h:
            return "install"
    for kw in _DEV_HEADINGS:
        if kw in h:
            return "dev"
    return "other"


def _find_install_in_text(text: str, tool_slug: str = "") -> tuple[str, str]:
    """Find the best install command in a block of text.

    Returns (install_command, package_name) or ("", "").
    Skips common prerequisite packages unless they match the tool's slug.
    """
    for pattern, template in INSTALL_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for pkg in matches:
            pkg = pkg.strip()
            if not pkg or pkg.startswith("-") or len(pkg) <= 1:
                continue
            # Check if this is a common prerequisite, not the tool itself
            pkg_base = pkg.lower().split("/")[-1]  # handle @scope/pkg
            if pkg_base in COMMON_PREREQUISITES:
                if not tool_slug or pkg_base != tool_slug.lower():
                    continue
            return template.format(pkg=pkg), pkg
    return "", ""


def extract_from_readme(readme_text: str, tool_slug: str = "") -> dict:
    """Extract metadata from a README's text content.

    Section-aware: searches installation sections first, skips dev sections,
    and filters out common prerequisite packages.
    """
    text = readme_text.lower()
    original = readme_text  # keep original case for env vars

    result = {
        "install_command": "",
        "sdk_packages": [],
        "env_vars": [],
        "frameworks_tested": [],
    }

    # ── Install commands (section-aware) ──
    sections = _parse_sections(readme_text)

    # Priority 1: Look in install-related sections
    for heading, body in sections:
        if _classify_heading(heading) == "install":
            cmd, pkg = _find_install_in_text(body, tool_slug)
            if cmd:
                result["install_command"] = cmd
                result["sdk_packages"].append(pkg)
                break

    # Priority 2: Look in non-dev sections (intro, usage, etc.)
    if not result["install_command"]:
        for heading, body in sections:
            if _classify_heading(heading) != "dev":
                cmd, pkg = _find_install_in_text(body, tool_slug)
                if cmd:
                    result["install_command"] = cmd
                    result["sdk_packages"].append(pkg)
                    break

    # Priority 3: Full text as last resort (still filters prerequisites)
    if not result["install_command"]:
        cmd, pkg = _find_install_in_text(readme_text, tool_slug)
        if cmd:
            result["install_command"] = cmd
            result["sdk_packages"].append(pkg)

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
    re_enrich = getattr(args, "re_enrich", False)

    if apply_changes and dry_run:
        print("ERROR: Cannot use both --apply and --dry-run")
        sys.exit(1)

    if not apply_changes and not dry_run:
        print("Specify --dry-run to preview or --apply to update.\n")
        dry_run = True

    # ── Load tools ──
    async with aiosqlite.connect(db_path) as db:
        db.row_factory = aiosqlite.Row
        if re_enrich:
            # Re-enrich: fetch tools that ALREADY have install commands (to overwrite)
            cursor = await db.execute("""
                SELECT id, name, slug, github_url, install_command
                FROM tools
                WHERE status = 'approved'
                  AND github_url IS NOT NULL AND github_url != ''
                  AND install_command IS NOT NULL AND install_command != ''
                ORDER BY github_stars DESC
                LIMIT ?
            """, (limit,))
        else:
            # Normal: fetch tools that need enrichment
            cursor = await db.execute("""
                SELECT id, name, slug, github_url, install_command
                FROM tools
                WHERE status = 'approved'
                  AND github_url IS NOT NULL AND github_url != ''
                  AND (sdk_packages IS NULL OR sdk_packages = '')
                ORDER BY github_stars DESC
                LIMIT ?
            """, (limit,))
        tools = await cursor.fetchall()

    mode_label = "re-enrichment" if re_enrich else "enrichment"
    print(f"Found {len(tools)} tools for {mode_label}\n")

    if not tools:
        print("Nothing to enrich.")
        return

    # ── Fetch READMEs and extract metadata ──
    results: list[dict] = []
    cleared: list[dict] = []  # re-enrich only: tools where old command was bad
    skipped = 0
    errors = 0

    async with httpx.AsyncClient(headers=headers, timeout=30, follow_redirects=True) as client:
        for i, tool in enumerate(tools, 1):
            name = tool["name"]
            github_url = tool["github_url"]
            old_cmd = str(tool["install_command"] or "")
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

            extracted = extract_from_readme(readme, tool_slug=tool["slug"])

            has_data = (
                extracted["install_command"]
                or extracted["env_vars"]
                or extracted["frameworks_tested"]
            )

            if re_enrich:
                new_cmd = extracted["install_command"]
                entry = {
                    "id": tool["id"],
                    "name": name,
                    "slug": tool["slug"],
                    "old_install": old_cmd,
                    **extracted,
                }
                # Check if old command's package was a known prerequisite
                old_parts = old_cmd.split()
                old_pkg = old_parts[-1].lower().split("/")[-1].split("@")[0] if old_parts else ""
                old_was_prereq = old_pkg in COMMON_PREREQUISITES

                if new_cmd == old_cmd:
                    skipped += 1
                    print(f"(unchanged: {old_cmd})")
                elif old_was_prereq and new_cmd:
                    # Old was a prereq, new is real — safe to replace
                    results.append(entry)
                    print(f"{old_cmd} -> {new_cmd}")
                elif old_was_prereq and not new_cmd:
                    # Old was a prereq, no replacement found — clear it
                    cleared.append(entry)
                    print(f"{old_cmd} -> (cleared)")
                elif not new_cmd:
                    # Old looked legitimate, new logic found nothing — clear
                    # (enricher couldn't find a valid command at all)
                    cleared.append(entry)
                    print(f"{old_cmd} -> (cleared)")
                elif new_cmd != old_cmd:
                    # Old looked legitimate, new is different — skip (don't regress)
                    skipped += 1
                    print(f"(kept: {old_cmd}, would have been: {new_cmd})")
            elif has_data:
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
    if re_enrich:
        print(f"Changed:   {len(results)}")
        print(f"Cleared:   {len(cleared)}")
        print(f"Unchanged: {skipped}")
    else:
        print(f"Enriched: {len(results)}")
        print(f"Skipped:  {skipped}")
    print(f"Errors:   {errors}")
    print(f"Total:    {len(tools)}")

    if dry_run:
        print(f"\n{'='*60}")
        if re_enrich:
            print("DRY RUN — would make these changes:")
            print(f"{'='*60}\n")
            for r in results:
                print(f"  {r['name']} ({r['slug']})")
                print(f"    {r['old_install']} -> {r['install_command']}")
            for r in cleared:
                print(f"  {r['name']} ({r['slug']})")
                print(f"    {r['old_install']} -> (cleared)")
        else:
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
    all_updates = results + cleared
    if not all_updates and not re_enrich:
        all_updates = results
    if not all_updates:
        print("\nNothing to apply.")
        return

    print(f"\nApplying {mode_label} to {len(all_updates)} tools...")
    async with aiosqlite.connect(db_path) as db:
        updated = 0
        for r in all_updates:
            try:
                if re_enrich:
                    # Atomic overwrite — no clearing step needed
                    sdk_json = json.dumps(r["sdk_packages"]) if r["sdk_packages"] else ""
                    await db.execute("""
                        UPDATE tools SET install_command = ?, sdk_packages = ?
                        WHERE id = ?
                    """, (r["install_command"], sdk_json, r["id"]))
                else:
                    # Normal: only fill empty fields
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
    parser.add_argument(
        "--re-enrich",
        action="store_true",
        help="Clear existing install commands and re-extract (fixes bad extractions)",
    )

    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()

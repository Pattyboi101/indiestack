"""
GitHub Auto-Indexer for IndieStack.

Discovers indie projects on GitHub and imports them as pending submissions.

Usage:
    python3 -m indiestack.indexer --query "self-hosted" --dry-run
    python3 -m indiestack.indexer --query "mcp-server" --min-stars 20 --import
"""

import argparse
import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone

import httpx

# ── Topic → Category mapping ─────────────────────────────────────────────

TOPIC_TO_CATEGORY = {
    "authentication": "authentication",
    "oauth": "authentication",
    "payments": "payments",
    "stripe": "payments",
    "analytics": "analytics-metrics",
    "monitoring": "monitoring-uptime",
    "cms": "developer-tools",
    "email": "email-marketing",
    "search": "developer-tools",
    "database": "developer-tools",
    "self-hosted": "developer-tools",
    "mcp-server": "ai-dev-tools",
    "ai": "ai-automation",
    "crm": "crm-sales",
    "forms": "forms-surveys",
    "landing-page": "landing-pages",
    "seo": "seo-tools",
    "scheduling": "scheduling-booking",
    "invoicing": "invoicing-billing",
    "project-management": "project-management",
    "game": "games-entertainment",
    "education": "learning-education",
    "newsletter": "newsletters-content",
    "design": "design-creative",
    "social-media": "social-media",
}

# ── Owner blocklist (non-indie / corporate) ───────────────────────────────

OWNER_BLOCKLIST = {
    "microsoft", "google", "aws", "amazon", "facebook", "meta", "apple",
    "oracle", "ibm", "salesforce", "adobe", "sap", "vmware", "cisco",
    "intel", "nvidia", "netflix", "uber", "airbnb", "stripe", "twilio",
    "databricks", "snowflake", "hashicorp", "elastic", "mongodb",
    "confluent", "datadog", "pagerduty", "atlassian", "jetbrains",
    "n8n-io", "vercel", "supabase", "grafana", "docker", "kubernetes",
    "openai", "anthropic", "huggingface", "langchain-ai", "cloudflare",
    "digitalocean", "linode", "heroku", "railway", "fly-apps",
    "awesome-selfhosted",  # list, not a tool
}

DEFAULT_CATEGORY = "developer-tools"


def map_category(topics: list[str]) -> str:
    """Map GitHub topics to an IndieStack category slug."""
    for topic in topics:
        if topic in TOPIC_TO_CATEGORY:
            return TOPIC_TO_CATEGORY[topic]
    return DEFAULT_CATEGORY


def repo_to_tool(repo: dict) -> dict:
    """Convert a GitHub repo dict to an IndieStack tool record."""
    name_raw = repo["name"]
    name = name_raw.replace("-", " ").replace("_", " ").title()
    slug = name_raw.lower().replace("_", "-")
    description = (repo.get("description") or "").strip()
    tagline = description[:100]
    topics = repo.get("topics") or []
    category = map_category(topics)
    tags = ",".join(topics[:5])

    return {
        "name": name,
        "slug": slug,
        "tagline": tagline,
        "description": description,
        "url": repo["html_url"],
        "github_url": repo["html_url"],
        "github_stars": repo.get("stargazers_count", 0),
        "category_slug": category,
        "tags": tags,
        "source_type": "code",
        "status": "pending",
        "submitted_from_ip": "auto-indexer",
    }


async def check_rate_limit(response: httpx.Response) -> None:
    """Sleep if GitHub rate limit is getting low."""
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


async def fetch_repos(
    client: httpx.AsyncClient,
    query: str,
    min_stars: int,
    max_pages: int,
) -> list[dict]:
    """Fetch repos from GitHub Search API."""
    all_repos = []
    six_months_ago = (datetime.now(timezone.utc) - timedelta(days=180)).strftime("%Y-%m-%d")
    full_query = f"{query} stars:>={min_stars} pushed:>{six_months_ago}"

    for page in range(1, max_pages + 1):
        print(f"  Fetching page {page}/{max_pages} for query: {full_query}")
        try:
            resp = await client.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": full_query,
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 30,
                    "page": page,
                },
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            print(f"  Error fetching page {page}: {e.response.status_code} {e.response.text[:200]}")
            break
        except httpx.RequestError as e:
            print(f"  Request error on page {page}: {e}")
            break

        data = resp.json()
        items = data.get("items", [])
        all_repos.extend(items)

        if len(items) < 30:
            break  # last page

        await check_rate_limit(resp)
        await asyncio.sleep(1)  # politeness delay

    return all_repos


def filter_repo(repo: dict, min_stars: int) -> str | None:
    """Return a skip reason string, or None if the repo passes all filters."""
    if repo.get("fork"):
        return "fork"

    stars = repo.get("stargazers_count", 0)
    if stars < min_stars:
        return f"low stars ({stars})"

    # Skip mega-projects — not indie
    if stars > 50000:
        return f"too popular to be indie ({stars} stars)"

    description = (repo.get("description") or "").strip()
    if len(description) <= 10:
        return "no/short description"

    pushed_at = repo.get("pushed_at", "")
    if pushed_at:
        six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
        try:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            if pushed < six_months_ago:
                return "stale (not pushed in 6 months)"
        except ValueError:
            pass

    owner_login = (repo.get("owner") or {}).get("login", "").lower()
    if owner_login in OWNER_BLOCKLIST:
        return f"blocklisted owner ({owner_login})"

    return None


async def get_existing_urls(db_path: str) -> set[str]:
    """Load existing tool URLs from the database for dedup."""
    import aiosqlite
    urls: set[str] = set()
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.execute("SELECT url FROM tools")
            rows = await cursor.fetchall()
            urls = {row[0] for row in rows}
            # Also check github_url column
            cursor2 = await db.execute("SELECT github_url FROM tools WHERE github_url != ''")
            rows2 = await cursor2.fetchall()
            urls.update(row[0] for row in rows2)
    except Exception as e:
        print(f"  Warning: could not read existing tools from DB: {e}")
    return urls


async def get_category_id(db, category_slug: str) -> int | None:
    """Look up a category ID by slug."""
    cursor = await db.execute("SELECT id FROM categories WHERE slug = ?", (category_slug,))
    row = await cursor.fetchone()
    return row[0] if row else None


async def import_tools(tools: list[dict], db_path: str) -> dict:
    """Insert qualifying tools into the database as pending."""
    import aiosqlite

    stats = {"imported": 0, "skipped_exists": 0, "errors": 0}

    async with aiosqlite.connect(db_path) as db:
        # Pre-load category IDs
        category_cache: dict[str, int | None] = {}

        for tool in tools:
            cat_slug = tool["category_slug"]
            if cat_slug not in category_cache:
                category_cache[cat_slug] = await get_category_id(db, cat_slug)

            cat_id = category_cache[cat_slug]
            if cat_id is None:
                # Fall back to developer-tools
                if DEFAULT_CATEGORY not in category_cache:
                    category_cache[DEFAULT_CATEGORY] = await get_category_id(db, DEFAULT_CATEGORY)
                cat_id = category_cache[DEFAULT_CATEGORY]
                if cat_id is None:
                    print(f"  ERROR: No category found for '{cat_slug}' or default. Skipping {tool['name']}")
                    stats["errors"] += 1
                    continue

            # Check for existing by URL or slug
            cursor = await db.execute(
                "SELECT id FROM tools WHERE url = ? OR github_url = ? OR slug = ?",
                (tool["url"], tool["github_url"], tool["slug"]),
            )
            if await cursor.fetchone():
                stats["skipped_exists"] += 1
                continue

            try:
                await db.execute(
                    """INSERT INTO tools
                       (name, slug, tagline, description, url, github_url, github_stars,
                        category_id, tags, source_type, status, submitted_from_ip)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        tool["name"],
                        tool["slug"],
                        tool["tagline"],
                        tool["description"],
                        tool["url"],
                        tool["github_url"],
                        tool["github_stars"],
                        cat_id,
                        tool["tags"],
                        tool["source_type"],
                        tool["status"],
                        tool["submitted_from_ip"],
                    ),
                )
                stats["imported"] += 1
            except Exception as e:
                print(f"  ERROR inserting {tool['name']}: {e}")
                stats["errors"] += 1

        await db.commit()

    return stats


async def run(args: argparse.Namespace) -> None:
    """Main async entrypoint."""
    db_path = os.environ.get("DATABASE_PATH", "/data/indiestack.db")
    github_token = os.environ.get("GITHUB_TOKEN", "")

    headers: dict[str, str] = {"Accept": "application/vnd.github+json"}
    if github_token:
        headers["Authorization"] = f"Bearer {github_token}"
        print("Using authenticated GitHub API (higher rate limits)")
    else:
        print("WARNING: No GITHUB_TOKEN set. Rate limits will be very low (10 req/min).")
        print("  Set GITHUB_TOKEN env var for 30 req/min.\n")

    do_import = getattr(args, "do_import", False)
    dry_run = args.dry_run

    if do_import and dry_run:
        print("ERROR: Cannot use both --import and --dry-run")
        sys.exit(1)

    if not do_import and not dry_run:
        print("Specify --dry-run to preview or --import to insert.\n")
        dry_run = True  # default to dry-run for safety

    # ── Fetch ──
    print(f"\nSearching GitHub for: {args.query} (min stars: {args.min_stars}, max pages: {args.max_pages})")
    async with httpx.AsyncClient(headers=headers, timeout=30) as client:
        repos = await fetch_repos(client, args.query, args.min_stars, args.max_pages)

    print(f"\nFetched {len(repos)} repos from GitHub\n")

    # ── Load existing URLs for dedup ──
    existing_urls: set[str] = set()
    if not dry_run:
        existing_urls = await get_existing_urls(db_path)
    else:
        # Still load for accurate dry-run reporting
        try:
            existing_urls = await get_existing_urls(db_path)
        except Exception:
            pass

    # ── Filter ──
    qualifying: list[dict] = []
    filtered_count = 0
    already_exists_count = 0

    for repo in repos:
        skip_reason = filter_repo(repo, args.min_stars)
        if skip_reason:
            filtered_count += 1
            continue

        html_url = repo["html_url"]
        if html_url in existing_urls:
            already_exists_count += 1
            continue

        tool = repo_to_tool(repo)
        qualifying.append(tool)
        existing_urls.add(html_url)  # prevent dupes within this batch

    print(f"Qualifying tools: {len(qualifying)}")
    print(f"Filtered (low quality): {filtered_count}")
    print(f"Already in IndieStack: {already_exists_count}")

    if not qualifying:
        print("\nNo new tools to import.")
        return

    # ── Dry run: print what would be imported ──
    if dry_run:
        print(f"\n{'='*60}")
        print("DRY RUN — would import the following tools:")
        print(f"{'='*60}\n")
        for i, tool in enumerate(qualifying, 1):
            print(f"  {i:3d}. {tool['name']}")
            print(f"       URL: {tool['url']}")
            print(f"       Category: {tool['category_slug']}")
            print(f"       Tags: {tool['tags']}")
            print(f"       Stars: {tool['github_stars']}")
            print(f"       Tagline: {tool['tagline'][:80]}")
            print()
        print(f"Total: {len(qualifying)} tools would be imported as pending")
        return

    # ── Import ──
    print(f"\nImporting {len(qualifying)} tools as pending...")
    stats = await import_tools(qualifying, db_path)

    print(f"\n{'='*60}")
    print("IMPORT COMPLETE")
    print(f"{'='*60}")
    print(f"  Imported:        {stats['imported']}")
    print(f"  Skipped (exists): {stats['skipped_exists']}")
    print(f"  Filtered:        {filtered_count}")
    print(f"  Errors:          {stats['errors']}")
    print(f"  Total fetched:   {len(repos)}")


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(
        description="IndieStack GitHub Auto-Indexer — discover indie projects and import as pending",
    )
    parser.add_argument(
        "-q", "--query",
        default="self-hosted",
        help="GitHub search query (default: self-hosted)",
    )
    parser.add_argument(
        "--min-stars",
        type=int,
        default=10,
        help="Minimum star count (default: 10)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=3,
        help="Max pages to fetch, 30 results each (default: 3)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be imported without inserting",
    )
    parser.add_argument(
        "--import",
        dest="do_import",
        action="store_true",
        help="Actually insert qualifying tools into the database as pending",
    )

    args = parser.parse_args()
    asyncio.run(run(args))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Ingest self-hosted tools from selfh.st into IndieStack.

Fetches the selfh.st apps directory (a JSON feed of ~1200 self-hosted
tools from https://selfhst.github.io/cdn/directory/software.json),
maps their tags to IndieStack categories, deduplicates against the DB,
and inserts new tools as pending with source_type='code'.

Usage:
    python3 scripts/ingest_selfhst.py --dry-run
    python3 scripts/ingest_selfhst.py --limit 50 --dry-run
    python3 scripts/ingest_selfhst.py --db data/indiestack.db
"""

import argparse
import json
import os
import re
import sqlite3
import sys
import time
import urllib.request
import urllib.error


# ── Data Sources ─────────────────────────────────────────────────────────

SOFTWARE_URL = "https://selfhst.github.io/cdn/directory/software.json"
TAGS_URL = "https://selfhst.github.io/cdn/directory/tags.json"

USER_AGENT = "IndieStack-Ingest/1.0 (+https://indiestack.ai)"

# ── Field indices in the software.json arrays ────────────────────────────
# Each entry is a flat list:
#   [0] id, [1] name, [2] slug, [3] website, [4] github_url,
#   [5] description, [6] source, [7] license_idx, [8] language_idx,
#   [9] icon_status, [10] github_org, [11-12] unknown,
#   [13] stars, [14] forks, [15] last_updated, [16] health (G/Y/R),
#   [17] unknown, [18] tag_indices (comma-separated), [19-23] unknown

F_ID = 0
F_NAME = 1
F_SLUG = 2
F_WEBSITE = 3
F_GITHUB = 4
F_DESC = 5
F_SOURCE = 6
F_STARS = 13
F_FORKS = 14
F_LAST_UPDATED = 15
F_HEALTH = 16
F_TAGS = 18


# ── selfh.st tag -> IndieStack category slug mapping ────────────────────
# Tags are identified by name from tags.json. A tool can have multiple
# tags; we use the FIRST one that maps to an IndieStack category.

TAG_TO_CATEGORY = {
    # Analytics & metrics
    "Analytics": "analytics-metrics",
    "Web Analytics": "analytics-metrics",
    "Statistics": "analytics-metrics",
    "Observability": "analytics-metrics",

    # Authentication & identity
    "Authentication": "authentication",
    "Identity Management": "authentication",
    "2FA": "authentication",
    "Password Manager": "authentication",
    "Security": "authentication",

    # Payments & billing
    "E-commerce": "payments",

    # Email
    "Email": "email-marketing",
    "Newsletters": "email-marketing",

    # Monitoring & uptime
    "Monitoring": "monitoring-uptime",
    "Uptime": "monitoring-uptime",
    "Logs": "monitoring-uptime",

    # Developer tools
    "Development": "developer-tools",
    "Development Environment": "developer-tools",
    "Development Infrastructure": "developer-tools",
    "IDE": "developer-tools",
    "Code Snippets": "developer-tools",
    "Container Registry": "developer-tools",
    "Git": "developer-tools",
    "Deployment": "developer-tools",
    "Terminal": "developer-tools",
    "Runners": "developer-tools",
    "Backend": "developer-tools",
    "No-Code / Low-Code": "developer-tools",
    "Static Site": "developer-tools",
    "Docker": "developer-tools",
    "Networking": "developer-tools",
    "Reverse Proxy": "developer-tools",
    "DNS": "developer-tools",
    "Web Server": "developer-tools",
    "SSH": "developer-tools",
    "Server Management": "developer-tools",

    # API tools
    "Webhooks": "api-tools",

    # Design & creative
    "Design": "design-creative",
    "Diagrams": "design-creative",
    "Icons": "design-creative",
    "Whiteboard": "design-creative",

    # Project management
    "Project Management": "project-management",
    "Kanban": "project-management",
    "Tasks and To-Do Lists": "project-management",

    # Forms & surveys
    "Surveys and Forms": "forms-surveys",

    # SEO tools
    "Search Engines": "seo-tools",
    "Search": "seo-tools",
    "Web Scraping": "seo-tools",

    # CRM & sales
    "CRM": "crm-sales",
    "Customer Engagement": "crm-sales",
    "Contacts": "crm-sales",

    # Scheduling & booking
    "Scheduling": "scheduling-booking",
    "Calendar": "scheduling-booking",
    "CalDAV/CarDAV": "scheduling-booking",

    # File management
    "File Management": "file-management",
    "File Sharing": "file-management",
    "File Transfer and Sync": "file-management",
    "Local File Sharing": "file-management",
    "Cloud Storage": "file-management",
    "Object Storage": "file-management",
    "Document Management": "file-management",
    "Backups": "file-management",

    # Feedback & reviews
    "Feedback": "feedback-reviews",
    "Comments": "feedback-reviews",

    # AI dev tools
    "Artificial Intelligence": "ai-dev-tools",

    # Landing pages
    "Landing Page": "landing-pages",

    # Customer support
    "Support / Ticketing": "customer-support",

    # Social media
    "Social Media": "social-media",
    "ActivityPub / Fediverse": "social-media",
    "Forums": "social-media",
    "Social News": "social-media",

    # Invoicing & billing
    "Accounting": "invoicing-billing",
    "Budgeting": "invoicing-billing",
    "ERP": "invoicing-billing",
    "Invoicing": "invoicing-billing",

    # Automation -> AI & Automation
    "Automation": "ai-automation",
    "Workflow Automation": "ai-automation",

    # Content / wiki / blog
    "Wiki": "developer-tools",
    "Blog": "developer-tools",
    "Content Management": "developer-tools",
    "Note-Taking": "developer-tools",
    "Pastebin": "developer-tools",

    # Notifications
    "Notifications": "monitoring-uptime",

    # Time tracking
    "Time Tracking": "project-management",

    # Database
    "Database": "developer-tools",
    "Relational Database": "developer-tools",
    "In-Memory Cache": "developer-tools",
    "Data Cloud": "developer-tools",
}


# ── Helpers ──────────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def fetch_json(url: str) -> list | dict | None:
    """Fetch and parse a JSON URL with polite headers."""
    print(f"Fetching {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            print(f"  Fetched {len(body):,} bytes")
            return json.loads(body)
    except (urllib.error.HTTPError, urllib.error.URLError, json.JSONDecodeError) as e:
        print(f"  Error fetching: {e}")
        return None


def resolve_tags(tag_indices_str: str, tag_names: list[str]) -> list[str]:
    """Convert comma-separated tag indices to tag name list."""
    if not tag_indices_str:
        return []
    tags = []
    for idx_str in tag_indices_str.split(','):
        idx_str = idx_str.strip()
        if not idx_str:
            continue
        try:
            idx = int(idx_str)
            if 0 <= idx < len(tag_names):
                tags.append(tag_names[idx])
        except ValueError:
            continue
    return tags


def map_category(tags: list[str], description: str = "") -> str | None:
    """Map a list of selfh.st tags to the best IndieStack category slug.

    First tries direct tag mapping, then falls back to keyword matching
    on the description for tools without tags.
    """
    for tag in tags:
        slug = TAG_TO_CATEGORY.get(tag)
        if slug:
            return slug

    # Keyword fallback for untagged tools
    if description:
        return guess_category_from_description(description)

    return None


# Keywords in description -> IndieStack category (checked in order)
DESC_KEYWORD_MAP = [
    (["monitor", "alert", "uptime", "observ", "log "], "monitoring-uptime"),
    (["analytic", "metric", "dashboard", "statistic", "track"], "analytics-metrics"),
    (["auth", "login", "sso", "identity", "password", "ldap", "oauth"], "authentication"),
    (["automat", "workflow", "pipeline", "n8n", "trigger"], "ai-automation"),
    (["ai ", "machine learn", "llm", "gpt", "neural", "chatbot"], "ai-dev-tools"),
    (["email", "smtp", "mail", "newsletter"], "email-marketing"),
    (["payment", "billing", "invoice", "subscript", "e-commerce", "shop", "store"], "payments"),
    (["deploy", "ci/cd", "docker", "container", "kubernetes", "devops"], "developer-tools"),
    (["api ", "rest ", "graphql", "webhook", "gateway"], "api-tools"),
    (["git ", "code", "develop", "ide ", "debug", "build tool", "package"], "developer-tools"),
    (["database", "sql", "redis", "cache", "storage backend"], "developer-tools"),
    (["dns ", "proxy", "reverse proxy", "server", "network", "firewall", "vpn"], "developer-tools"),
    (["project manag", "kanban", "task", "todo", "board", "sprint"], "project-management"),
    (["time track"], "project-management"),
    (["file ", "backup", "sync", "cloud storage", "document manag", "s3 "], "file-management"),
    (["crm", "customer relation", "sales", "lead"], "crm-sales"),
    (["calendar", "schedul", "booking", "appointment"], "scheduling-booking"),
    (["form ", "survey"], "forms-surveys"),
    (["seo", "search engine", "crawl", "scrap"], "seo-tools"),
    (["design", "diagram", "icon", "whiteboard", "image edit", "photo edit"], "design-creative"),
    (["feedback", "review", "comment", "poll"], "feedback-reviews"),
    (["landing page", "website builder"], "landing-pages"),
    (["support", "ticket", "helpdesk", "help desk"], "customer-support"),
    (["social", "fediverse", "mastodon", "forum", "communit"], "social-media"),
    (["account", "budget", "financ", "bookkeep", "erp"], "invoicing-billing"),
    (["wiki", "cms", "blog ", "content manag", "note"], "developer-tools"),
]


def guess_category_from_description(description: str) -> str | None:
    """Use keyword matching on description to guess a category."""
    desc_lower = description.lower()
    for keywords, category in DESC_KEYWORD_MAP:
        for kw in keywords:
            if kw in desc_lower:
                return category
    return None


def normalise_url(raw: str) -> str:
    """Normalise a URL domain into a full https:// URL."""
    raw = raw.strip()
    if not raw:
        return ""
    if not raw.startswith(('http://', 'https://')):
        raw = 'https://' + raw
    return raw.rstrip('/')


def norm_for_dedup(url: str) -> str:
    """Normalise URL for deduplication comparison."""
    url = url.lower().rstrip('/')
    url = re.sub(r'^https?://', '', url)
    url = re.sub(r'^www\.', '', url)
    return url


# ── Main ingestion logic ─────────────────────────────────────────────────

def ingest(db_path: str, dry_run: bool, limit: int | None):
    print("=" * 60)
    print("selfh.st apps directory -> IndieStack")
    print("=" * 60)

    # Fetch data
    software = fetch_json(SOFTWARE_URL)
    if not software:
        print("ERROR: Could not fetch software.json")
        sys.exit(1)

    # Brief pause between requests
    time.sleep(1)

    tags_data = fetch_json(TAGS_URL)
    if not tags_data:
        print("ERROR: Could not fetch tags.json")
        sys.exit(1)

    # Build tag name list (tags_data is a list of dicts with "Tag" key)
    tag_names = [t["Tag"] for t in tags_data]
    print(f"\n  Loaded {len(software)} software entries, {len(tag_names)} tags\n")

    # Apply limit
    if limit:
        software = software[:limit]
        print(f"  Limited to first {limit} entries\n")

    # Connect to DB for dedup and category lookup.
    # In dry-run mode we still read the DB (if it exists) for dedup,
    # but we never write to it.
    conn = None
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
    elif not dry_run:
        print(f"ERROR: Database not found: {db_path}")
        sys.exit(1)
    else:
        print(f"  (DB not found at {db_path} — dedup disabled in dry run)\n")

    # Load IndieStack categories
    category_ids = {}
    if conn:
        for row in conn.execute("SELECT id, slug FROM categories").fetchall():
            category_ids[row['slug']] = row['id']

    # Load existing tools for dedup
    existing_names = set()
    existing_urls = set()
    existing_slugs = set()
    if conn:
        for row in conn.execute("SELECT name, slug, url FROM tools").fetchall():
            existing_names.add(row['name'].lower())
            existing_slugs.add(row['slug'])
            if row['url']:
                existing_urls.add(norm_for_dedup(row['url']))
        print(f"  Loaded {len(existing_names)} existing tools for dedup\n")

    # Process entries
    inserted = 0
    duplicates = 0
    skipped_no_cat = 0
    skipped_no_desc = 0
    seen_in_batch = set()

    for entry in software:
        if len(entry) < 19:
            continue

        name = (entry[F_NAME] or "").strip()
        website = normalise_url(entry[F_WEBSITE] or "")
        github_raw = (entry[F_GITHUB] or "").strip()
        github_url = normalise_url(github_raw) if github_raw else None
        description = (entry[F_DESC] or "").strip()

        if not name or len(description) < 5:
            skipped_no_desc += 1
            continue

        # Use website as primary URL, fall back to GitHub
        url = website or github_url or ""
        if not url:
            skipped_no_desc += 1
            continue

        # Resolve tags and map to IndieStack category
        tag_list = resolve_tags(entry[F_TAGS], tag_names)
        cat_slug = map_category(tag_list, description)

        if not cat_slug:
            skipped_no_cat += 1
            continue

        # Check category exists in DB
        if conn and cat_slug not in category_ids:
            skipped_no_cat += 1
            continue

        # Dedup by name
        if name.lower() in existing_names or name.lower() in seen_in_batch:
            duplicates += 1
            continue

        # Dedup by URL
        norm_url = norm_for_dedup(url)
        if norm_url in existing_urls:
            duplicates += 1
            continue

        # Dedup by slug
        slug = slugify(name)
        if slug in existing_slugs or slug in seen_in_batch:
            duplicates += 1
            continue

        # Track in batch
        seen_in_batch.add(slug)
        seen_in_batch.add(name.lower())
        seen_in_batch.add(norm_url)

        # GitHub stars
        stars = None
        try:
            stars = int(entry[F_STARS]) if entry[F_STARS] else None
        except (ValueError, IndexError):
            pass

        if dry_run:
            tags_str = ", ".join(tag_list[:3]) if tag_list else "no tags"
            print(f"  [{cat_slug:20s}] {name:30s} ({tags_str})")
            inserted += 1
        else:
            cat_id = category_ids.get(cat_slug)
            if not cat_id:
                skipped_no_cat += 1
                continue
            try:
                conn.execute(
                    """INSERT INTO tools
                       (name, slug, tagline, url, github_url, source_type,
                        status, category_id, github_stars)
                       VALUES (?, ?, ?, ?, ?, 'code', 'pending', ?, ?)""",
                    (name, slug, description[:200], url, github_url,
                     cat_id, stars)
                )
                inserted += 1
            except sqlite3.IntegrityError:
                duplicates += 1

    if conn:
        if not dry_run:
            conn.commit()
        conn.close()

    print(f"\n{'=' * 60}")
    print(f"Results:")
    print(f"  New tools {'(would insert)' if dry_run else 'inserted'}: {inserted}")
    print(f"  Already existed (dedup):  {duplicates}")
    print(f"  Skipped (no category):    {skipped_no_cat}")
    print(f"  Skipped (no desc/url):    {skipped_no_desc}")
    print(f"  Total processed:          {len(software)}")
    print(f"{'=' * 60}")

    return inserted


def main():
    parser = argparse.ArgumentParser(
        description="Ingest self-hosted tools from selfh.st into IndieStack"
    )

    _default_db = os.environ.get(
        'INDIESTACK_DB_PATH',
        '/data/indiestack.db' if os.path.exists('/data/indiestack.db')
        else 'data/indiestack.db'
    )

    parser.add_argument('--db', default=_default_db,
                        help='Path to SQLite database')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview without inserting')
    parser.add_argument('--limit', type=int, default=None,
                        help='Only process the first N entries')

    args = parser.parse_args()

    ingest(args.db, args.dry_run, args.limit)


if __name__ == "__main__":
    main()

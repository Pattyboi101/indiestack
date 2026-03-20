#!/usr/bin/env python3
"""Ingest tools from awesome-selfhosted into IndieStack as pending entries.

Fetches the awesome-selfhosted README from GitHub, parses tool entries,
maps categories to IndieStack's catalog, deduplicates, and inserts new
tools with status='pending' for manual review.

Usage:
    python3 scripts/ingest_awesome_selfhosted.py --dry-run
    python3 scripts/ingest_awesome_selfhosted.py --db data/indiestack.db
"""

import argparse
import os
import re
import sqlite3
import sys
import urllib.request
import urllib.error

README_URL = "https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/master/README.md"

# Map awesome-selfhosted section headings → IndieStack category slugs.
# Sections not listed here are skipped (games, media, photo galleries, etc.)
CATEGORY_MAP = {
    "analytics": "analytics-metrics",
    "automation": "ai-automation",
    "communication": "customer-support",
    "communication - custom communication systems": "customer-support",
    "communication - email - complete solutions": "email-marketing",
    "communication - email - mail delivery agents": "email-marketing",
    "communication - email - mail transfer agents": "email-marketing",
    "communication - email - mailing lists and newsletters": "email-marketing",
    "communication - email - webmail clients": "email-marketing",
    "communication - irc": "customer-support",
    "communication - matrix": "customer-support",
    "communication - social networks and forums": "customer-support",
    "communication - video conferencing": "customer-support",
    "communication - xmpp": "customer-support",
    "database management": "developer-tools",
    "document management": "file-management",
    "document management - e-books": "file-management",
    "document management - institutional repository and digital library software": "file-management",
    "e-commerce": "invoicing-billing",
    "email": "email-marketing",
    "file transfer": "file-management",
    "file transfer - distributed filesystems": "file-management",
    "file transfer - object storage & file servers": "file-management",
    "file transfer - peer-to-peer filesharing": "file-management",
    "file transfer - single-click & drag-n-drop upload": "file-management",
    "file transfer - web-based file managers": "file-management",
    "groupware": "project-management",
    "monitoring": "monitoring-uptime",
    "note-taking & editors": "developer-tools",
    "note-taking and editors": "developer-tools",
    "password managers": "authentication",
    "polls and events": "scheduling-booking",
    "project management": "project-management",
    "search engines": "seo-tools",
    "software development": "developer-tools",
    "software development - api management": "api-tools",
    "software development - build tools": "developer-tools",
    "software development - continuous integration & deployment": "developer-tools",
    "software development - ftp": "developer-tools",
    "software development - ide & tools": "developer-tools",
    "software development - localization": "developer-tools",
    "software development - low code": "developer-tools",
    "software development - project management": "project-management",
    "software development - testing": "developer-tools",
    "status / uptime pages": "monitoring-uptime",
    "status / uptime": "monitoring-uptime",
    "task management & to-do lists": "project-management",
    "task management": "project-management",
    "ticketing": "customer-support",
    "url shorteners": "developer-tools",
    "wikis": "developer-tools",
}


def slugify(text: str) -> str:
    """Generate a URL slug from text — mirrors db.py slugify()."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def fetch_readme() -> str:
    """Fetch the awesome-selfhosted README from GitHub."""
    print(f"Fetching {README_URL} ...")
    req = urllib.request.Request(README_URL, headers={
        "User-Agent": "IndieStack-Ingest/1.0",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            print(f"  Fetched {len(body):,} bytes")
            return body
    except urllib.error.HTTPError as e:
        print(f"  HTTP error {e.code}: {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"  Network error: {e.reason}")
        sys.exit(1)


# Regex for a tool line:  - [Name](url) - Description. `License` `Language`
# Some entries have optional ` (Source Code)` links, anti-features, etc.
TOOL_RE = re.compile(
    r'^-\s+\[([^\]]+)\]\(([^)]+)\)\s+-\s+(.+)',
    re.MULTILINE,
)


def parse_readme(text: str) -> list[dict]:
    """Parse the README into a list of {name, url, description, category_slug}."""
    tools = []
    current_section = None
    current_slug = None

    for line in text.split('\n'):
        # Detect section headings (## or ###)
        heading_match = re.match(r'^#{2,3}\s+(.+)', line)
        if heading_match:
            raw_heading = heading_match.group(1).strip()
            # Remove markdown links from heading e.g. [Something](url)
            raw_heading = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', raw_heading)
            # Remove trailing anchors/fragments
            raw_heading = raw_heading.strip()
            current_section = raw_heading
            # Try exact match first, then lowercase
            lookup = current_section.lower()
            current_slug = CATEGORY_MAP.get(lookup)
            continue

        # Skip lines if current section doesn't map
        if not current_slug:
            continue

        # Match tool entries
        m = TOOL_RE.match(line.strip())
        if not m:
            continue

        name = m.group(1).strip()
        url = m.group(2).strip()
        desc_raw = m.group(3).strip()

        # Clean the description: remove markdown links, backtick tags, etc.
        # Remove markdown link groups like ([Source Code](url), [Demo](url))
        desc = re.sub(r'\((?:\[(?:Source Code|Demo|Clients|Website)\]\([^)]*\)[,\s]*)+\)', '', desc_raw)
        # Remove standalone markdown links like [Source Code](url)
        desc = re.sub(r'\[(?:Source Code|Demo|Clients|Website)\]\([^)]*\)', '', desc)
        # Remove backtick-wrapped license/language tags
        desc = re.sub(r'`[^`]*`', '', desc)
        # Remove anti-feature warnings
        desc = re.sub(r'[⚠️]', '', desc)
        # Clean up stray punctuation and whitespace
        desc = re.sub(r'\s+', ' ', desc)
        desc = desc.strip().rstrip('.,;').strip()

        if not name or not url or not desc:
            continue

        # Skip entries whose URL points to a list rather than a tool
        if 'awesome-selfhosted' in url:
            continue

        tools.append({
            'name': name,
            'url': url,
            'description': desc,
            'category_slug': current_slug,
        })

    return tools


def main():
    parser = argparse.ArgumentParser(description="Import awesome-selfhosted tools into IndieStack")
    _default_db = os.environ.get('INDIESTACK_DB_PATH', '/data/indiestack.db' if os.path.exists('/data/indiestack.db') else 'data/indiestack.db')
    parser.add_argument('--db', default=_default_db,
                        help='Path to IndieStack SQLite database')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print what would be inserted without writing to DB')
    args = parser.parse_args()

    # ── Fetch & parse ────────────────────────────────────────────────────
    readme = fetch_readme()
    parsed = parse_readme(readme)
    print(f"Parsed {len(parsed)} tool entries from awesome-selfhosted\n")

    if not parsed:
        print("Nothing parsed — check if the README format has changed.")
        sys.exit(1)

    # ── Connect to DB ────────────────────────────────────────────────────
    if not args.dry_run and not os.path.exists(args.db):
        print(f"Database not found: {args.db}")
        print("Use --db to specify the correct path, or --dry-run to preview.")
        sys.exit(1)

    conn = None
    if not args.dry_run:
        conn = sqlite3.connect(args.db)
        conn.row_factory = sqlite3.Row

    # ── Load IndieStack categories ───────────────────────────────────────
    category_ids = {}
    if conn:
        cursor = conn.execute("SELECT id, slug FROM categories")
        for row in cursor.fetchall():
            category_ids[row['slug']] = row['id']

    # ── Load existing tools for dedup ────────────────────────────────────
    existing_names = set()
    existing_urls = set()
    existing_slugs = set()
    if conn:
        cursor = conn.execute("SELECT name, slug, url FROM tools")
        for row in cursor.fetchall():
            existing_names.add(row['name'].lower())
            existing_slugs.add(row['slug'])
            # Normalize URL for comparison (strip trailing slash, protocol)
            raw_url = row['url'].lower().rstrip('/')
            raw_url = re.sub(r'^https?://', '', raw_url)
            existing_urls.add(raw_url)

    # ── Process tools ────────────────────────────────────────────────────
    inserted = 0
    duplicates = 0
    skipped_no_cat = 0
    to_insert = []

    for tool in parsed:
        cat_slug = tool['category_slug']

        # Verify category exists in the database (or in dry-run, just trust the map)
        if conn and cat_slug not in category_ids:
            skipped_no_cat += 1
            continue

        name = tool['name']
        url = tool['url']

        # Dedup check: name or URL already in DB
        url_normalized = re.sub(r'^https?://', '', url.lower().rstrip('/'))
        if conn:
            if name.lower() in existing_names or url_normalized in existing_urls:
                duplicates += 1
                continue

        slug = slugify(name)

        # Ensure unique slug
        if conn:
            base_slug = slug
            counter = 1
            while slug in existing_slugs:
                slug = f"{base_slug}-{counter}"
                counter += 1
            existing_slugs.add(slug)

        # Also prevent duplicate names/URLs within this batch
        if name.lower() in existing_names or url_normalized in existing_urls:
            duplicates += 1
            continue
        existing_names.add(name.lower())
        existing_urls.add(url_normalized)

        desc = tool['description']
        # Tagline: first sentence, capped at 120 chars
        tagline = desc[:120] if len(desc) > 120 else desc

        # Auto-detect source_type
        source_type = 'code' if any(h in url.lower() for h in ('github.com', 'gitlab.com', 'codeberg.org')) else 'saas'

        to_insert.append({
            'name': name,
            'slug': slug,
            'tagline': tagline,
            'description': desc,
            'url': url,
            'github_url': url if 'github.com' in url.lower() else '',
            'category_id': category_ids.get(cat_slug, 0),
            'category_slug': cat_slug,
            'source_type': source_type,
        })

    # ── Dry run output ───────────────────────────────────────────────────
    if args.dry_run:
        print(f"=== DRY RUN ===")
        print(f"Would insert {len(to_insert)} new tools (status='pending')")
        print(f"Already existed: {duplicates}")
        print(f"Skipped (no matching category): {skipped_no_cat}")
        print()
        # Group by category for readability
        by_cat = {}
        for t in to_insert:
            by_cat.setdefault(t['category_slug'], []).append(t)
        for cat_slug, tools_list in sorted(by_cat.items()):
            print(f"  [{cat_slug}] ({len(tools_list)} tools)")
            for t in tools_list[:5]:
                print(f"    - {t['name']}: {t['tagline'][:80]}")
            if len(tools_list) > 5:
                print(f"    ... and {len(tools_list) - 5} more")
            print()
        return

    # ── Insert ───────────────────────────────────────────────────────────
    for t in to_insert:
        conn.execute(
            """INSERT INTO tools (name, slug, tagline, description, url, github_url,
               category_id, tags, status, source_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, '', 'pending', ?)""",
            (t['name'], t['slug'], t['tagline'], t['description'],
             t['url'], t['github_url'], t['category_id'], t['source_type'])
        )
        inserted += 1

    conn.commit()
    conn.close()

    # ── Summary ──────────────────────────────────────────────────────────
    print(f"=== DONE ===")
    print(f"New tools inserted (pending): {inserted}")
    print(f"Already existed (skipped):    {duplicates}")
    print(f"No matching category (skipped): {skipped_no_cat}")
    print(f"Total parsed from README:     {len(parsed)}")


if __name__ == "__main__":
    main()

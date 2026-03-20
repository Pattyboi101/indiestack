#!/usr/bin/env python3
"""Generic awesome-list ingester for IndieStack.

Fetches any awesome-list README from GitHub, parses tool entries,
maps categories, deduplicates against the DB, and inserts as pending.

Usage:
    python3 scripts/ingest_awesome_list.py --source developer-first --dry-run
    python3 scripts/ingest_awesome_list.py --source mcp-servers
    python3 scripts/ingest_awesome_list.py --source all --dry-run
    python3 scripts/ingest_awesome_list.py --list-sources
"""

import argparse
import os
import re
import sqlite3
import sys
import urllib.request
import urllib.error


# ── Source Configurations ──────────────────────────────────────────────────

SOURCES = {
    "developer-first": {
        "url": "https://raw.githubusercontent.com/agamm/awesome-developer-first/main/README.md",
        "description": "Developer-first tools and APIs",
        "category_map": {
            "ai coding": "ai-dev-tools",
            "analytics": "analytics-metrics",
            "authentication & identity": "authentication",
            "authentication": "authentication",
            "automation": "ai-automation",
            "backend-as-a-service": "developer-tools",
            "ci/cd": "developer-tools",
            "cms (headless)": "developer-tools",
            "code quality": "developer-tools",
            "computer vision": "ai-dev-tools",
            "databases & spreadsheets": "developer-tools",
            "debugging": "developer-tools",
            "deployment hosting": "developer-tools",
            "discussions": "customer-support",
            "documentation": "developer-tools",
            "environment & secret management": "developer-tools",
            "feature flags": "developer-tools",
            "gen ui": "ai-dev-tools",
            "geo": "developer-tools",
            "ide": "developer-tools",
            "infrastructure as code": "developer-tools",
            "integrations": "api-tools",
            "localization": "developer-tools",
            "mail": "email-marketing",
            "media": "design-creative",
            "messaging": "customer-support",
            "misc": "developer-tools",
            "monitoring": "monitoring-uptime",
            "natural language processing": "ai-dev-tools",
            "orchestration": "developer-tools",
            "payments & pricing": "payments",
            "repo": "developer-tools",
            "reports generation": "developer-tools",
            "scraping": "developer-tools",
            "search": "seo-tools",
            "security": "authentication",
            "shipping": "developer-tools",
            "testing": "developer-tools",
        },
        # Format: - [Name](url) — Description.
        "tool_pattern": r'^[*-]\s+\[([^\]]+)\]\(([^)]+)\)\s*[-–—:]\s*(.+)',
    },
    "mcp-servers": {
        "url": "https://raw.githubusercontent.com/punkpeye/awesome-mcp-servers/main/README.md",
        "description": "MCP servers for AI agents",
        "category_map": {
            "art & culture": "design-creative",
            "browser automation": "developer-tools",
            "cloud platforms": "developer-tools",
            "code execution": "developer-tools",
            "coding assistants": "developer-tools",
            "communication": "customer-support",
            "customer data platforms": "crm-sales",
            "data & app analysis": "analytics-metrics",
            "databases": "developer-tools",
            "design": "design-creative",
            "developer tools": "developer-tools",
            "devops": "developer-tools",
            "education": "developer-tools",
            "file systems": "file-management",
            "finance & fintech": "payments",
            "gaming": None,  # skip
            "health": None,  # skip
            "knowledge & memory": "developer-tools",
            "location services": "developer-tools",
            "marketing": "seo-tools",
            "monitoring": "monitoring-uptime",
            "multimedia": None,  # skip
            "project management": "project-management",
            "search": "seo-tools",
            "security": "authentication",
            "shopping": None,  # skip
            "social media": "social-media",
            "sports": None,  # skip
            "storage": "file-management",
            "translation services": "developer-tools",
            "travel": None,  # skip
            "version control": "developer-tools",
            "weather": None,  # skip
        },
        "tool_pattern": r'^-\s+\[([^\]]+)\]\(([^)]+)\)\s*[-–—:]\s*(.+)',
    },
    "seo-tools": {
        "url": "https://raw.githubusercontent.com/serpapi/awesome-seo-tools/master/README.md",
        "description": "SEO tools and resources",
        "category_map": {
            "all-in-one seo tools": "seo-tools",
            "keyword research tools": "seo-tools",
            "backlink analysis tools": "seo-tools",
            "content optimization tools": "seo-tools",
            "rank tracking tools": "seo-tools",
            "technical seo tools": "seo-tools",
            "local seo tools": "seo-tools",
            "seo browser extensions": "seo-tools",
            "seo analytics tools": "seo-tools",
            "schema markup tools": "seo-tools",
            "site audit tools": "seo-tools",
            "content marketing tools": "seo-tools",
            "link building tools": "seo-tools",
            "seo automation tools": "seo-tools",
            "ai seo tools": "seo-tools",
            "seo reporting tools": "seo-tools",
        },
        "tool_pattern": r'^-\s+\[([^\]]+)\]\(([^)]+)\)\s*[-–—:]\s*(.+)',
    },
    "analytics": {
        "url": "https://raw.githubusercontent.com/newTendermint/awesome-analytics/master/README.md",
        "description": "Analytics tools and platforms",
        "category_map": {
            "general analytics": "analytics-metrics",
            "privacy focused analytics": "analytics-metrics",
            "analytics layers": "analytics-metrics",
            "developer analytics": "analytics-metrics",
            "real-time": "analytics-metrics",
            "website analytics": "analytics-metrics",
            "app analytics": "analytics-metrics",
            "heatmap analytics": "analytics-metrics",
            "analytics dashboards": "analytics-metrics",
            "social media analytics": "social-media",
            "seo analytics": "seo-tools",
            "email analytics": "email-marketing",
            "a/b testing": "analytics-metrics",
            "product analytics": "analytics-metrics",
        },
        "tool_pattern": r'^[*-]\s+\[([^\]]+)\]\(([^)]+)\)\s*[-–—:]\s*(.+)',
    },
    "ai-devtools": {
        "url": "https://raw.githubusercontent.com/jamesmurdza/awesome-ai-devtools/main/README.md",
        "description": "AI-powered developer tools",
        "category_map": {
            "code completion": "ai-dev-tools",
            "code generation": "ai-dev-tools",
            "code review": "ai-dev-tools",
            "code search": "ai-dev-tools",
            "coding assistants": "ai-dev-tools",
            "debugging": "ai-dev-tools",
            "documentation": "ai-dev-tools",
            "ide extensions": "ai-dev-tools",
            "testing": "ai-dev-tools",
            "agents": "ai-dev-tools",
            "code editors": "ai-dev-tools",
            "terminal": "ai-dev-tools",
            "shell": "ai-dev-tools",
        },
        "tool_pattern": r'^-\s+\[([^\]]+)\]\(([^)]+)\)\s*[-–—:]\s*(.+)',
    },
}


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def fetch_readme(url: str) -> str:
    print(f"Fetching {url} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "IndieStack-Ingest/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            print(f"  Fetched {len(body):,} bytes")
            return body
    except (urllib.error.HTTPError, urllib.error.URLError) as e:
        print(f"  Error fetching: {e}")
        return ""


def parse_readme(text: str, source_config: dict) -> list[dict]:
    tools = []
    current_slug = None
    category_map = source_config["category_map"]
    tool_re = re.compile(source_config["tool_pattern"], re.MULTILINE)

    for line in text.split('\n'):
        heading_match = re.match(r'^#{1,4}\s+(.+)', line)
        if heading_match:
            raw = heading_match.group(1).strip()
            raw = re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', raw)
            raw = re.sub(r'[*_]', '', raw).strip()
            lookup = raw.lower()
            current_slug = category_map.get(lookup)
            # Try partial matching for subsections
            if not current_slug:
                for key, val in category_map.items():
                    if key in lookup or lookup in key:
                        current_slug = val
                        break
            continue

        if not current_slug:
            continue

        m = tool_re.match(line.strip())
        if not m:
            continue

        name = m.group(1).strip()
        url = m.group(2).strip()
        desc_raw = m.group(3).strip()

        # Clean description
        desc = re.sub(r'\((?:\[(?:Source Code|Demo|Clients|Website)\]\([^)]*\)[,\s]*)+\)', '', desc_raw)
        desc = re.sub(r'\[(?:Source Code|Demo|Clients|Website|GitHub|Docs)\]\([^)]*\)', '', desc)
        desc = re.sub(r'`[^`]*`', '', desc)
        desc = re.sub(r'!\[([^\]]*)\]\([^)]*\)', '', desc)  # images
        desc = re.sub(r'\s+', ' ', desc)
        desc = desc.strip().rstrip('.,;-–— ').strip()

        if not name or not url or len(desc) < 5:
            continue

        # Skip self-referential links
        if 'awesome-' in url and 'github.com' in url:
            continue

        tools.append({
            'name': name,
            'url': url,
            'description': desc,
            'category_slug': current_slug,
        })

    return tools


def ingest(source_name: str, source_config: dict, db_path: str, dry_run: bool):
    print(f"\n{'='*60}")
    print(f"Source: {source_name} — {source_config['description']}")
    print(f"{'='*60}")

    text = fetch_readme(source_config["url"])
    if not text:
        print("  Skipping — could not fetch README")
        return 0

    parsed = parse_readme(text, source_config)
    print(f"  Parsed {len(parsed)} tool entries\n")

    if not parsed:
        return 0

    conn = None
    if not dry_run:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

    # Load categories
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
            raw_url = row['url'].lower().rstrip('/')
            raw_url = re.sub(r'^https?://', '', raw_url)
            existing_urls.add(raw_url)

    inserted = 0
    duplicates = 0
    skipped = 0
    seen_in_batch = set()

    for tool in parsed:
        cat_slug = tool['category_slug']
        if conn and cat_slug not in category_ids:
            skipped += 1
            continue

        name = tool['name']
        url = tool['url']
        norm_url = re.sub(r'^https?://', '', url.lower().rstrip('/'))

        if name.lower() in existing_names or norm_url in existing_urls:
            duplicates += 1
            continue

        slug = slugify(name)
        if slug in existing_slugs or slug in seen_in_batch:
            duplicates += 1
            continue

        if name.lower() in seen_in_batch:
            duplicates += 1
            continue

        seen_in_batch.add(slug)
        seen_in_batch.add(name.lower())

        github_url = url if 'github.com' in url else None
        source_type = 'code' if github_url else 'saas'

        if dry_run:
            print(f"  [{cat_slug}] {name}: {tool['description'][:80]}")
        elif conn:
            cat_id = category_ids.get(cat_slug)
            if not cat_id:
                skipped += 1
                continue
            try:
                conn.execute(
                    """INSERT INTO tools (name, slug, tagline, url, github_url, source_type, status, category_id)
                       VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
                    (name, slug, tool['description'][:200], url, github_url, source_type, cat_id)
                )
                inserted += 1
            except sqlite3.IntegrityError:
                duplicates += 1

    if conn:
        conn.commit()
        conn.close()

    print(f"\n  Results for {source_name}:")
    print(f"    New tools inserted: {inserted}" + (" (dry run)" if dry_run else ""))
    print(f"    Already existed:    {duplicates}")
    print(f"    Skipped (no cat):   {skipped}")
    print(f"    Total parsed:       {len(parsed)}")
    return inserted


def main():
    parser = argparse.ArgumentParser(description="Ingest tools from awesome lists into IndieStack")
    _default_db = os.environ.get('INDIESTACK_DB_PATH',
                                  '/data/indiestack.db' if os.path.exists('/data/indiestack.db') else 'data/indiestack.db')
    parser.add_argument('--db', default=_default_db, help='Path to SQLite database')
    parser.add_argument('--dry-run', action='store_true', help='Preview without inserting')
    parser.add_argument('--source', default='all',
                        help=f'Source to ingest: {", ".join(SOURCES.keys())}, or "all"')
    parser.add_argument('--list-sources', action='store_true', help='List available sources')
    args = parser.parse_args()

    if args.list_sources:
        print("Available sources:")
        for name, cfg in SOURCES.items():
            print(f"  {name:20s} — {cfg['description']}")
        return

    if args.source == 'all':
        sources_to_run = list(SOURCES.items())
    elif args.source in SOURCES:
        sources_to_run = [(args.source, SOURCES[args.source])]
    else:
        print(f"Unknown source: {args.source}")
        print(f"Available: {', '.join(SOURCES.keys())}, or 'all'")
        sys.exit(1)

    total_inserted = 0
    for name, config in sources_to_run:
        total_inserted += ingest(name, config, args.db, args.dry_run)

    print(f"\n{'='*60}")
    print(f"Grand total: {total_inserted} new tools" + (" (dry run)" if args.dry_run else ""))


if __name__ == "__main__":
    main()

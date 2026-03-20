#!/usr/bin/env python3
"""Ingest open-source developer tools from openalternative.co into IndieStack.

Fetches tool slugs from the sitemap, scrapes JSON-LD structured data from
each tool page, maps categories, deduplicates against the DB, and inserts
as status='pending'.

Usage:
    python3 scripts/ingest_openalternative.py --dry-run
    python3 scripts/ingest_openalternative.py --dry-run --limit 20
    python3 scripts/ingest_openalternative.py --db data/indiestack.db
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
import xml.etree.ElementTree as ET


# ── Configuration ────────────────────────────────────────────────────────────

SITEMAP_URL = "https://openalternative.co/sitemap/tools.xml"
BASE_URL = "https://openalternative.co"
USER_AGENT = "IndieStack-Ingest/1.0 (+https://indiestack.ai)"
REQUEST_DELAY = 1.0  # seconds between page fetches — be polite

# Map OpenAlternative leaf category slugs → IndieStack category slugs.
# OpenAlternative has ~300 fine-grained categories; we map the ones that
# correspond to IndieStack's 25 categories and skip the rest.
CATEGORY_MAP = {
    # Analytics & Metrics
    "analytics": "analytics-metrics",
    "web-analytics": "analytics-metrics",
    "product-analytics": "analytics-metrics",
    "community-analytics-management": "analytics-metrics",
    "data-visualization": "analytics-metrics",
    "bi-platforms": "analytics-metrics",
    "business-intelligence-reporting": "analytics-metrics",
    "data-analytics": "analytics-metrics",
    "data-observability": "analytics-metrics",

    # Authentication
    "authentication-sso": "authentication",
    "authorization-permissions": "authentication",
    "identity-access-management-iam": "authentication",
    "captcha-bot-protection": "authentication",
    "application-security": "authentication",
    "security-privacy": "authentication",
    "password-managers": "authentication",
    "password-secret-management": "authentication",
    "secrets-management": "authentication",
    "secrets-platforms": "authentication",

    # Payments
    "payment-infrastructure": "payments",
    "invoicing-payments": "invoicing-billing",
    "subscription-billing-management": "invoicing-billing",
    "finance-fintech": "payments",
    "fintech-infrastructure": "payments",

    # Email Marketing
    "email-marketing-newsletters": "email-marketing",
    "email-platforms": "email-marketing",
    "email-communication": "email-marketing",
    "email-forwarding-aliasing": "email-marketing",
    "email-clients": "email-marketing",

    # Monitoring & Uptime
    "infrastructure-monitoring": "monitoring-uptime",
    "monitoring-observability": "monitoring-uptime",
    "uptime-monitoring": "monitoring-uptime",
    "status-pages": "monitoring-uptime",
    "performance-monitoring-apm": "monitoring-uptime",
    "error-tracking": "monitoring-uptime",
    "log-management": "monitoring-uptime",

    # Developer Tools
    "developer-tools": "developer-tools",
    "build-deployment": "developer-tools",
    "ci-cd-platforms": "developer-tools",
    "code-analysis-transformation": "developer-tools",
    "code-transformation": "developer-tools",
    "databases": "developer-tools",
    "database-tools-guis": "developer-tools",
    "development-environments": "developer-tools",
    "general-purpose-editors": "developer-tools",
    "ides-code-editors": "developer-tools",
    "feature-flags": "developer-tools",
    "frameworks-platforms": "developer-tools",
    "web-frameworks": "developer-tools",
    "backend-as-a-service-baas": "developer-tools",
    "infrastructure-as-code-iac": "developer-tools",
    "container-orchestration": "developer-tools",
    "paas-deployment-tools": "developer-tools",
    "cloud-computing": "developer-tools",
    "cloud-infrastructure-management": "developer-tools",
    "testing-quality-assurance": "developer-tools",
    "automated-testing": "developer-tools",
    "static-analysis": "developer-tools",
    "git-clients": "developer-tools",
    "git-platforms": "developer-tools",
    "version-control-collaboration": "developer-tools",
    "headless-cms": "developer-tools",
    "content-management-systems-cms": "developer-tools",
    "control-panels": "developer-tools",
    "server-vm-management": "developer-tools",
    "search-servers": "developer-tools",
    "relational-databases-sql": "developer-tools",
    "nosql-document-databases": "developer-tools",
    "graph-databases": "developer-tools",
    "in-memory-databases": "developer-tools",
    "time-series-databases": "developer-tools",
    "vector-databases": "developer-tools",
    "database-proxies": "developer-tools",
    "mobile-development": "developer-tools",
    "frontend-developer": "developer-tools",
    "website-builders": "developer-tools",

    # API Tools
    "api-clients": "api-tools",
    "api-development-testing": "api-tools",
    "api-documentation-generators": "api-tools",
    "api-infrastructure": "api-tools",
    "api-integration": "api-tools",
    "integration-platforms": "api-tools",
    "webhook-platforms": "api-tools",

    # Design & Creative
    "design-prototyping": "design-creative",
    "design-visualization": "design-creative",
    "online-design": "design-creative",
    "ui-ux-design": "design-creative",
    "whiteboarding": "design-creative",
    "digital-asset-management-dam": "design-creative",
    "photo-editors": "design-creative",
    "photo-video-editors": "design-creative",
    "video-editors": "design-creative",

    # Project Management
    "project-management-suites": "project-management",
    "project-work-management": "project-management",
    "agile-project-management": "project-management",
    "task-management": "project-management",
    "task-management-apps": "project-management",
    "time-task-management": "project-management",
    "time-tracking": "project-management",

    # Forms & Surveys
    "form-builders": "forms-surveys",
    "form-backend-services": "forms-surveys",
    "forms-surveys": "forms-surveys",
    "survey-tools": "forms-surveys",

    # SEO Tools
    "seo-tools": "seo-tools",  # if it exists

    # CRM & Sales
    "crm-systems": "crm-sales",
    "crm-sales": "crm-sales",
    "sales-automation": "crm-sales",
    "marketing-automation": "crm-sales",
    "marketing-customer-engagement": "crm-sales",

    # Scheduling & Booking
    "appointment-scheduling": "scheduling-booking",
    "scheduling-event-management": "scheduling-booking",
    "event-ticketing-management": "scheduling-booking",

    # File Management
    "file-management": "file-management",
    "file-management-sync": "file-management",
    "cloud-file-sync-share": "file-management",
    "cloud-storage": "file-management",
    "storage-solutions": "file-management",
    "document-management-systems": "file-management",
    "document-management-e-signatures": "file-management",
    "backup-recovery": "file-management",

    # Feedback & Reviews
    "feedback-feature-request-management": "feedback-reviews",
    "community-feedback-platforms": "feedback-reviews",
    "collaboration-feedback": "feedback-reviews",
    "changelog-generators": "feedback-reviews",

    # AI Dev Tools
    "ai-dev-tools": "ai-dev-tools",
    "ai-machine-learning": "ai-dev-tools",
    "ai-development-platforms": "ai-dev-tools",
    "ai-agent-platforms": "ai-dev-tools",
    "ai-assisted-coding": "ai-dev-tools",
    "ai-app-website-builders": "ai-dev-tools",
    "ai-code-reviewers": "ai-dev-tools",
    "ai-coding-agents": "ai-dev-tools",
    "ai-coding-assistants": "ai-dev-tools",
    "ai-powered-editors": "ai-dev-tools",
    "ai-gateways": "ai-dev-tools",
    "ai-integration": "ai-dev-tools",
    "ai-data-platforms": "ai-dev-tools",
    "llm-application-frameworks": "ai-dev-tools",
    "machine-learning-infrastructure": "ai-dev-tools",
    "ai-chat-interfaces": "ai-dev-tools",
    "ai-personal-assistants": "ai-dev-tools",
    "ai-search-tools": "ai-dev-tools",
    "ai-security-privacy": "ai-dev-tools",
    "ai-api-key-protection": "ai-dev-tools",
    "ai-interaction-interfaces": "ai-dev-tools",
    "browser-automation-for-ai": "ai-dev-tools",

    # Landing Pages
    "landing-pages": "landing-pages",
    "blogging-platforms": "landing-pages",
    "blogging-personal-sites": "landing-pages",

    # Customer Support
    "customer-support-success": "customer-support",
    "helpdesk-software": "customer-support",
    "live-chat-messaging": "customer-support",
    "customer-communication-platforms": "customer-support",
    "chatbot-platforms": "customer-support",

    # Social Media
    "social-media-management": "social-media",
    "social-networking": "social-media",
    "decentralized-social-networks": "social-media",
    "community-building-platforms": "social-media",
    "community-platforms": "social-media",
    "community-social": "social-media",
    "video-platforms": "social-media",

    # AI & Automation
    "automation": "ai-automation",
    "workflow-automation": "ai-automation",
    "workflow-orchestration": "ai-automation",
    "browser-automation": "ai-automation",
    "orchestration-scheduling": "ai-automation",
    "job-scheduling": "ai-automation",
    "etl-data-integration": "ai-automation",
    "data-engineering-integration": "ai-automation",

    # Additional mappings for common tool types
    "low-code-no-code": "developer-tools",
    "note-taking": "project-management",
    "note-taking-knowledge-management": "project-management",
    "collaborative-notes-wikis": "project-management",
    "collaborative-workspaces": "project-management",
    "wiki-software": "project-management",
    "personal-knowledge-management-pkm": "project-management",
    "documentation-knowledge-base": "developer-tools",
    "internal-knowledge-bases": "developer-tools",
    "technical-writing-platforms": "developer-tools",
    "publishing": "landing-pages",
    "content-publishing": "landing-pages",
    "e-commerce-platforms": "payments",
    "full-stack-e-commerce": "payments",
    "headless-commerce": "payments",
    "frontend-e-commerce-solutions": "payments",
    "team-chat-messaging": "customer-support",
    "collaboration-communication": "customer-support",
    "encrypted-communication": "customer-support",
    "video-conferencing-virtual-office": "customer-support",
    "push-notification": "email-marketing",
    "link-management-shorteners": "seo-tools",
    "data-extraction-web-scraping": "developer-tools",
    "scraping-platforms-sdks": "developer-tools",
    "compliance-automation": "developer-tools",
    "compliance-risk-management": "developer-tools",
    "network-security": "authentication",
    "vpn-secure-access": "authentication",
    "vpn-secure-tunnels": "authentication",
    "ssh-access-management": "authentication",
    "threat-detection-response": "authentication",
    "security-automation-siem-soar": "authentication",
    "screen-capture-recording": "design-creative",
    "screen-recording": "design-creative",
    "e-signature-platforms": "file-management",
    "accounting-software": "invoicing-billing",
    "expense-management": "invoicing-billing",
    "invoicing-billing": "invoicing-billing",
    "product-tour-user-onboarding": "customer-support",
    "forum-software": "social-media",
    "read-it-later-knowledge-hubs": "project-management",
}


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def fetch_url(url: str, retries: int = 2) -> str:
    """Fetch a URL with retries and polite User-Agent."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            if attempt < retries:
                time.sleep(2 * (attempt + 1))
                continue
            print(f"  Error fetching {url}: {e}")
            return ""


def get_tool_slugs_from_sitemap() -> list[str]:
    """Parse the tools sitemap and return a list of tool slugs."""
    print(f"Fetching sitemap: {SITEMAP_URL}")
    xml_text = fetch_url(SITEMAP_URL)
    if not xml_text:
        print("  Failed to fetch sitemap")
        return []

    # Parse XML — strip namespace for simplicity
    xml_text = re.sub(r'\sxmlns="[^"]+"', '', xml_text, count=1)
    root = ET.fromstring(xml_text)

    slugs = []
    for url_elem in root.findall(".//url/loc"):
        loc = url_elem.text
        if loc:
            # Extract slug: https://openalternative.co/{slug}
            slug = loc.replace(BASE_URL + "/", "").strip("/")
            if slug and "/" not in slug:
                slugs.append(slug)

    print(f"  Found {len(slugs)} tool slugs in sitemap")
    return slugs


def extract_tool_data(slug: str, html: str) -> dict | None:
    """Extract tool data from a page's HTML using JSON-LD and link patterns."""
    # 1) Parse JSON-LD SoftwareApplication
    ld_match = re.search(r'application/ld\+json">\s*(\{.*?\})\s*</script>', html)
    if not ld_match:
        return None

    try:
        ld_data = json.loads(ld_match.group(1))
    except json.JSONDecodeError:
        return None

    software = None
    for item in ld_data.get("@graph", []):
        if item.get("@type") == "SoftwareApplication":
            software = item
            break

    if not software:
        return None

    name = software.get("name", "").strip()
    description = software.get("description", "").strip()
    github_url = software.get("downloadUrl", "")
    license_url = software.get("license", "")

    if not name or not description:
        return None

    # 2) Determine if open source (has license or GitHub URL)
    is_open_source = bool(license_url) or bool(github_url and "github.com" in github_url)

    # 3) Extract website URL from page links
    # Look for direct external links with utm_source=openalternative.co
    website_url = ""
    utm_links = re.findall(
        r'href="(https?://[^"]+\?utm_source=openalternative\.co)"', html
    )
    # Filter to find the tool's own website (not other tools on the page)
    # Strategy: the tool's slug often appears in the go.openalternative.co link
    for link in utm_links:
        domain = link.split("?")[0]
        # Skip openalternative.co itself
        if "openalternative.co" in domain:
            # But check go.openalternative.co/{slug} redirects
            if f"go.openalternative.co/{slug}" in domain:
                website_url = link.split("?")[0]
                break
            continue
        # First external link is usually the tool's website
        if not website_url:
            website_url = domain

    # If we only found a go.openalternative.co redirect, use it
    # Otherwise the direct link is better
    if not website_url and github_url:
        website_url = github_url

    # Clean up GitHub URL
    if github_url and "github.com" not in github_url:
        github_url = ""
    if github_url:
        github_url = github_url.rstrip("/")

    # 4) Extract categories from the page
    # Tool-specific category links use full hierarchical paths like:
    #   /categories/infrastructure-operations/server-vm-management/control-panels
    # Sidebar "Browse Categories" links use short single-segment paths like:
    #   /categories/low-code-no-code
    # We only want tool-specific categories (multi-segment paths).
    cat_slugs = re.findall(r'/categories/([^"?\\\s]+)', html)
    leaf_categories = set()
    for cat_path in cat_slugs:
        parts = cat_path.rstrip("\\").split("/")
        # Only use multi-segment paths (tool-specific, not sidebar browse)
        if len(parts) >= 2:
            leaf = parts[-1]
            if leaf:
                leaf_categories.add(leaf)

    # Map to IndieStack categories
    indiestack_cats = set()
    for leaf in leaf_categories:
        mapped = CATEGORY_MAP.get(leaf)
        if mapped:
            indiestack_cats.add(mapped)

    # Pick the best (most specific) category — prefer non-generic ones
    category_slug = None
    preferred_order = [
        "ai-dev-tools", "analytics-metrics", "authentication", "payments",
        "invoicing-billing", "email-marketing", "monitoring-uptime",
        "api-tools", "scheduling-booking", "forms-surveys", "seo-tools",
        "crm-sales", "feedback-reviews", "landing-pages", "customer-support",
        "social-media", "design-creative", "file-management",
        "project-management", "ai-automation", "developer-tools",
    ]
    for pref in preferred_order:
        if pref in indiestack_cats:
            category_slug = pref
            break

    if not category_slug and indiestack_cats:
        category_slug = sorted(indiestack_cats)[0]

    return {
        "name": name,
        "slug": slug,
        "description": description,
        "url": website_url or f"{BASE_URL}/{slug}",
        "github_url": github_url or None,
        "is_open_source": is_open_source,
        "category_slug": category_slug,
        "oa_categories": sorted(leaf_categories),
    }


def ingest(db_path: str, dry_run: bool, limit: int | None, offset: int):
    """Main ingestion workflow."""
    print(f"{'='*60}")
    print(f"OpenAlternative → IndieStack Ingester")
    print(f"{'='*60}")
    print(f"  DB:      {db_path}")
    print(f"  Mode:    {'DRY RUN' if dry_run else 'LIVE INSERT'}")
    if limit:
        print(f"  Limit:   {limit} tools (offset {offset})")
    print()

    # Get all tool slugs from sitemap
    tool_slugs = get_tool_slugs_from_sitemap()
    if not tool_slugs:
        print("No tools found in sitemap. Aborting.")
        return

    # Apply offset and limit
    if offset:
        tool_slugs = tool_slugs[offset:]
    if limit:
        tool_slugs = tool_slugs[:limit]

    # Open DB for dedup + category lookup
    conn = None
    if not dry_run:
        if not os.path.exists(db_path):
            print(f"  ERROR: Database not found at {db_path}")
            sys.exit(1)
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row

    # Load categories (also needed for dry-run reporting)
    category_ids = {}
    if conn:
        for row in conn.execute("SELECT id, slug FROM categories").fetchall():
            category_ids[row["slug"]] = row["id"]

    # Load existing tools for dedup
    existing_names = set()
    existing_urls = set()
    existing_slugs = set()
    if conn:
        for row in conn.execute("SELECT name, slug, url FROM tools").fetchall():
            existing_names.add(row["name"].lower())
            existing_slugs.add(row["slug"])
            raw_url = row["url"].lower().rstrip("/")
            raw_url = re.sub(r'^https?://', '', raw_url)
            existing_urls.add(raw_url)

    # Scrape each tool page
    inserted = 0
    duplicates = 0
    skipped_no_cat = 0
    skipped_fetch = 0
    skipped_parse = 0
    seen_in_batch = set()

    total = len(tool_slugs)
    print(f"\nScraping {total} tool pages (delay={REQUEST_DELAY}s)...\n")

    for i, oa_slug in enumerate(tool_slugs, 1):
        tool_url = f"{BASE_URL}/{oa_slug}"
        progress = f"[{i}/{total}]"

        # Polite delay between requests
        if i > 1:
            time.sleep(REQUEST_DELAY)

        html = fetch_url(tool_url)
        if not html:
            print(f"  {progress} SKIP (fetch failed): {oa_slug}")
            skipped_fetch += 1
            continue

        tool = extract_tool_data(oa_slug, html)
        if not tool:
            print(f"  {progress} SKIP (no data): {oa_slug}")
            skipped_parse += 1
            continue

        name = tool["name"]
        cat_slug = tool["category_slug"]

        # Skip if no mappable category
        if not cat_slug:
            print(f"  {progress} SKIP (no category): {name} → {tool['oa_categories']}")
            skipped_no_cat += 1
            continue

        # Dedup by name, URL, and slug
        norm_url = re.sub(r'^https?://', '', tool["url"].lower().rstrip('/'))
        tool_slug = slugify(name)

        if name.lower() in existing_names or norm_url in existing_urls:
            duplicates += 1
            continue

        if tool_slug in existing_slugs or tool_slug in seen_in_batch:
            duplicates += 1
            continue

        if name.lower() in seen_in_batch:
            duplicates += 1
            continue

        seen_in_batch.add(tool_slug)
        seen_in_batch.add(name.lower())

        source_type = "code" if tool["github_url"] else "saas"

        if dry_run:
            oss_tag = " [OSS]" if tool["is_open_source"] else ""
            print(f"  {progress} [{cat_slug}] {name}{oss_tag}: {tool['description'][:80]}")
        elif conn:
            cat_id = category_ids.get(cat_slug)
            if not cat_id:
                skipped_no_cat += 1
                continue
            try:
                conn.execute(
                    """INSERT INTO tools
                       (name, slug, tagline, url, github_url, source_type, status, category_id)
                       VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)""",
                    (name, tool_slug, tool["description"][:200],
                     tool["url"], tool["github_url"], source_type, cat_id)
                )
                inserted += 1
                print(f"  {progress} INSERTED [{cat_slug}] {name}")
            except sqlite3.IntegrityError:
                duplicates += 1

    if conn:
        conn.commit()
        conn.close()

    # Summary
    print(f"\n{'='*60}")
    print(f"Results:")
    print(f"  Tools in sitemap:     {total}")
    print(f"  New tools inserted:   {inserted}" + (" (dry run)" if dry_run else ""))
    print(f"  Already existed:      {duplicates}")
    print(f"  Skipped (no category):{skipped_no_cat}")
    print(f"  Skipped (fetch fail): {skipped_fetch}")
    print(f"  Skipped (parse fail): {skipped_parse}")
    print(f"{'='*60}")


def main():
    global REQUEST_DELAY  # noqa: PLW0603

    parser = argparse.ArgumentParser(
        description="Ingest tools from openalternative.co into IndieStack"
    )
    _default_db = os.environ.get(
        "INDIESTACK_DB_PATH",
        "/data/indiestack.db" if os.path.exists("/data/indiestack.db") else "data/indiestack.db"
    )
    parser.add_argument("--db", default=_default_db, help="Path to SQLite database")
    parser.add_argument("--dry-run", action="store_true", help="Preview without inserting")
    parser.add_argument("--limit", type=int, default=None,
                        help="Max number of tools to process (for testing)")
    parser.add_argument("--offset", type=int, default=0,
                        help="Skip first N tools from sitemap (for resuming)")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between requests in seconds (default: 1.0)")
    args = parser.parse_args()

    REQUEST_DELAY = args.delay

    ingest(args.db, args.dry_run, args.limit, args.offset)


if __name__ == "__main__":
    main()

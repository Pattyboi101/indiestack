#!/usr/bin/env python3
"""
Assign secondary categories to all tools using rule-based scoring.
Reuses the scoring logic from recategorise_dry_run.py.

This script does NOT change primary categories. It only ADDS secondary
categories via the tool_categories junction table.

Usage:
    python3 scripts/assign_secondary_categories.py --db backups/indiestack-XXXX.db --dry-run
    python3 scripts/assign_secondary_categories.py --db /data/indiestack.db --apply
"""

import sqlite3
import re
import sys
import json
from collections import defaultdict

DB_PATH = "/data/indiestack.db"
if "--db" in sys.argv:
    DB_PATH = sys.argv[sys.argv.index("--db") + 1]

DRY_RUN = "--dry-run" in sys.argv
APPLY = "--apply" in sys.argv
MAX_SECONDARY = 4  # max secondary categories per tool

# ── Category rules (scoring) ────────────────────────────────────────────
# Each rule: category slug, primary keywords (tagline), strong keywords (name),
#            tag keywords. Score >= 2 = assign as secondary.
RULES = [
    {"slug": "authentication", "primary": ["authentication", "auth provider", "identity provider", "single sign-on", "sso", "oauth", "openid", "oidc", "login system", "access control", "user management", "passwordless", "multi-factor", "mfa", "2fa", "saml", "ldap", "rbac"], "strong": ["auth", "sso", "oauth", "identity", "keycloak"], "tags": ["authentication", "oauth", "oauth2", "sso", "openid", "oidc", "saml", "jwt", "2fa", "mfa", "identity", "passwordless", "ldap", "rbac"]},
    {"slug": "analytics-metrics", "primary": ["analytics", "metrics", "event tracking", "product analytics", "web analytics", "data analytics", "business intelligence", "user analytics", "telemetry"], "strong": ["analytics", "metrics", "plausible", "matomo", "posthog", "umami"], "tags": ["analytics", "web-analytics", "product-analytics", "metrics", "business-intelligence", "heatmap", "session-replay", "ab-testing"]},
    {"slug": "monitoring-uptime", "primary": ["monitoring", "uptime", "observability", "alerting", "incident management", "health check", "status page", "apm", "log management", "tracing", "error tracking", "server monitoring", "performance monitoring", "system monitor"], "strong": ["monitor", "uptime", "observability", "grafana", "prometheus", "nagios", "zabbix"], "tags": ["monitoring", "uptime", "observability", "alerting", "apm", "logging", "tracing", "status-page", "error-tracking"]},
    {"slug": "email-marketing", "primary": ["email service", "email api", "email platform", "transactional email", "email sending", "email delivery", "smtp", "email marketing", "email automation", "email builder", "email template", "mailing list", "bulk email"], "strong": ["smtp", "mailer", "mailgun", "sendgrid"], "tags": ["email", "smtp", "email-marketing", "newsletter", "transactional-email", "email-template", "mailing-list"]},
    {"slug": "payments", "primary": ["payment", "subscription management", "checkout", "payment processing", "payment gateway", "recurring payments", "dunning", "e-commerce", "ecommerce", "online store", "shopping cart", "marketplace"], "strong": ["payment", "checkout", "dunning", "ecommerce", "e-commerce"], "tags": ["payments", "ecommerce", "e-commerce", "checkout", "stripe", "shopping-cart", "marketplace", "online-store"]},
    {"slug": "invoicing-billing", "primary": ["invoice", "invoicing", "billing software", "accounting", "expense", "bookkeeping", "financial management", "payroll"], "strong": ["invoice", "invoicing", "accounting", "bookkeeping"], "tags": ["invoice", "invoicing", "accounting", "billing", "bookkeeping", "expense", "payroll"]},
    {"slug": "forms-surveys", "primary": ["form builder", "survey tool", "survey platform", "questionnaire", "data collection form", "form backend"], "strong": ["form builder", "survey tool", "survey platform"], "tags": ["form-builder", "forms", "survey", "surveys", "questionnaire", "typeform"]},
    {"slug": "project-management", "primary": ["project management", "task management", "kanban", "issue tracker", "bug tracker", "sprint planning", "agile", "team collaboration", "note-taking", "notes app", "knowledge management", "team chat", "messaging platform"], "strong": ["project management", "kanban", "issue tracker", "note-taking", "team chat"], "tags": ["project-management", "kanban", "issue-tracker", "task-management", "todo", "agile", "note-taking", "notes", "knowledge-base", "team-chat", "messaging", "slack-alternative"]},
    {"slug": "customer-support", "primary": ["helpdesk", "help desk", "customer support", "live chat", "ticketing system", "support platform", "customer service"], "strong": ["helpdesk", "help desk", "ticketing system", "live chat widget"], "tags": ["helpdesk", "customer-support", "live-chat", "ticketing", "customer-service", "intercom"]},
    {"slug": "seo-tools", "primary": ["seo", "search engine optimization", "keyword research", "backlink", "serp", "rank tracking"], "strong": ["seo"], "tags": ["seo", "keyword-research", "backlink", "serp"]},
    {"slug": "crm-sales", "primary": ["crm", "customer relationship", "sales pipeline", "lead management", "sales automation", "contact management", "erp"], "strong": ["crm", "erp"], "tags": ["crm", "sales", "leads", "sales-pipeline", "erp", "lead-management"]},
    {"slug": "landing-pages", "primary": ["landing page", "page builder", "website builder", "site builder", "cms", "content management system", "headless cms", "blog platform", "wiki platform", "wiki engine"], "strong": ["cms", "content management", "wiki", "page builder", "website builder"], "tags": ["cms", "content-management", "headless-cms", "wiki", "page-builder", "website-builder", "static-site", "blog-engine"]},
    {"slug": "scheduling-booking", "primary": ["scheduling", "booking system", "appointment", "calendar app", "reservation system", "meeting scheduler"], "strong": ["scheduling", "booking", "appointment", "calendly"], "tags": ["scheduling", "booking", "appointment", "calendar", "reservation"]},
    {"slug": "social-media", "primary": ["social media", "social network", "social platform", "fediverse", "mastodon", "activitypub", "forum software", "discussion platform", "community platform"], "strong": ["social media", "fediverse", "mastodon", "forum"], "tags": ["social-media", "social-network", "fediverse", "mastodon", "activitypub", "forum", "community"]},
    {"slug": "file-management", "primary": ["file storage", "file sharing", "file manager", "cloud storage", "object storage", "s3 compatible", "document management", "file hosting", "file sync", "file browser", "nas", "personal cloud"], "strong": ["file manager", "object storage", "cloud storage", "file sharing", "nas"], "tags": ["file-management", "file-sharing", "cloud-storage", "object-storage", "s3", "file-manager", "nas"]},
    {"slug": "design-creative", "primary": ["design tool", "graphic design", "image editor", "photo editor", "ui design", "diagram tool", "whiteboard", "wireframe", "prototyping tool"], "strong": ["design tool", "image editor", "whiteboard", "wireframe"], "tags": ["design", "graphic-design", "image-editor", "ui-design", "diagram", "whiteboard", "wireframe", "prototyping"]},
    {"slug": "games-entertainment", "primary": ["game engine", "game server", "game development", "music player", "media player", "media server", "video player", "streaming server", "podcast player", "audio player", "music streaming", "media management", "media center", "ebook reader", "photo gallery"], "strong": ["game engine", "game server", "media server", "music player", "media player", "photo gallery"], "tags": ["game", "gaming", "game-engine", "game-server", "media-server", "music-player", "media-player", "plex", "video-player", "streaming", "podcast", "ebook", "photo-gallery", "music", "movies"]},
    {"slug": "learning-education", "primary": ["learning platform", "lms", "learning management", "online course", "e-learning", "tutorial platform", "training platform", "quiz platform", "classroom"], "strong": ["lms", "learning management", "e-learning"], "tags": ["education", "learning", "lms", "e-learning", "tutorial", "course", "training", "classroom"]},
    {"slug": "newsletters-content", "primary": ["newsletter", "publishing platform", "rss reader", "feed reader", "feed aggregator", "content curation", "news aggregator"], "strong": ["newsletter", "rss reader", "feed reader", "news aggregator"], "tags": ["newsletter", "rss", "rss-reader", "feed-reader", "publishing", "news-aggregator"]},
    {"slug": "feedback-reviews", "primary": ["feedback tool", "user feedback", "feature request", "roadmap tool", "changelog", "product feedback", "testimonial", "nps"], "strong": ["feedback tool", "feature request", "roadmap tool", "changelog", "testimonial"], "tags": ["feedback", "feature-requests", "roadmap", "changelog", "testimonials", "user-feedback"]},
    {"slug": "creative-tools", "primary": ["video editor", "audio editor", "music production", "podcast editor", "screen recorder", "screenshot tool", "animation tool", "3d modeling"], "strong": ["video editor", "audio editor", "screen recorder"], "tags": ["video-editor", "audio-editor", "screen-recorder", "animation", "music-production", "3d"]},
    {"slug": "api-tools", "primary": ["api gateway", "api management", "api documentation", "api testing", "api platform", "graphql platform", "api monitoring"], "strong": ["api gateway", "api management", "api platform"], "tags": ["api-gateway", "api-management", "api-documentation", "api-testing", "graphql"]},
    # New v2 categories
    {"slug": "database", "primary": ["database", "sql", "nosql", "orm", "data store", "key-value store", "graph database", "time series database", "vector database", "database management", "database client", "query builder", "data warehouse", "column store"], "strong": ["database", "sql", "postgres", "mysql", "mongodb", "redis", "sqlite", "dynamodb", "elasticsearch"], "tags": ["database", "sql", "nosql", "orm", "postgresql", "mysql", "mongodb", "redis", "sqlite", "elasticsearch", "key-value", "graph-database", "vector-database", "timeseries"]},
    {"slug": "headless-cms", "primary": ["headless cms", "content api", "api-first cms", "content management api"], "strong": ["headless cms"], "tags": ["headless-cms", "content-api", "strapi", "contentful", "sanity"]},
    {"slug": "media-server", "primary": ["media server", "streaming server", "transcoding", "video streaming", "audio streaming", "live streaming", "rtmp", "hls"], "strong": ["media server", "streaming server", "transcoding"], "tags": ["media-server", "streaming", "rtmp", "hls", "webrtc", "transcoding", "live-streaming"]},
    {"slug": "devops-infrastructure", "primary": ["ci/cd", "continuous integration", "continuous deployment", "container", "docker", "kubernetes", "infrastructure as code", "terraform", "ansible", "deployment automation", "server management", "cloud infrastructure"], "strong": ["docker", "kubernetes", "terraform", "ansible", "ci/cd"], "tags": ["docker", "kubernetes", "terraform", "ansible", "ci-cd", "devops", "infrastructure", "container", "deployment", "k8s"]},
    {"slug": "security-tools", "primary": ["security", "vulnerability", "penetration testing", "encryption", "firewall", "vpn", "password manager", "secret management", "compliance", "security scanner", "threat detection"], "strong": ["security", "vulnerability", "firewall", "vpn", "encryption"], "tags": ["security", "vulnerability", "penetration-testing", "encryption", "firewall", "vpn", "password-manager", "secret-management"]},
    {"slug": "search-engine", "primary": ["search engine", "full-text search", "vector search", "search index", "search platform", "elasticsearch alternative", "search as a service"], "strong": ["search engine", "full-text search", "vector search", "meilisearch", "typesense"], "tags": ["search", "full-text-search", "vector-search", "search-engine", "elasticsearch", "meilisearch", "typesense", "algolia"]},
    {"slug": "message-queue", "primary": ["message queue", "message broker", "event streaming", "pub/sub", "async messaging", "task queue", "event bus", "event-driven"], "strong": ["message queue", "message broker", "event streaming"], "tags": ["message-queue", "message-broker", "rabbitmq", "kafka", "pub-sub", "event-streaming", "nats", "redis-streams"]},
    {"slug": "testing-tools", "primary": ["testing framework", "test automation", "unit test", "integration test", "end-to-end test", "load testing", "test runner", "mocking", "test coverage"], "strong": ["test framework", "test automation", "load testing"], "tags": ["testing", "test", "unit-test", "integration-test", "e2e", "load-testing", "test-automation", "mocking", "playwright", "cypress", "jest"]},
    {"slug": "documentation", "primary": ["documentation", "api docs", "developer docs", "knowledge base", "doc generator", "technical writing"], "strong": ["documentation", "api docs", "doc generator"], "tags": ["documentation", "docs", "api-docs", "docusaurus", "mkdocs", "gitbook", "readme"]},
    {"slug": "cli-tools", "primary": ["command line", "cli tool", "terminal", "shell utility", "console application"], "strong": ["cli tool", "command line", "terminal tool"], "tags": ["cli", "command-line", "terminal", "shell", "console"]},
    {"slug": "logging", "primary": ["log management", "log aggregation", "log analysis", "centralized logging", "structured logging", "log viewer"], "strong": ["log management", "log aggregation"], "tags": ["logging", "log", "log-management", "log-aggregation", "structured-logging"]},
    {"slug": "feature-flags", "primary": ["feature flag", "feature toggle", "a/b testing", "gradual rollout", "remote config", "feature management"], "strong": ["feature flag", "feature toggle"], "tags": ["feature-flags", "feature-toggle", "ab-testing", "feature-management"]},
    {"slug": "notifications", "primary": ["push notification", "notification service", "in-app notification", "notification platform", "alert service", "notification api"], "strong": ["notification service", "push notification"], "tags": ["notifications", "push-notifications", "notification", "alert"]},
    {"slug": "background-jobs", "primary": ["background job", "task queue", "job scheduler", "cron job", "workflow orchestration", "job processing", "worker queue"], "strong": ["task queue", "job scheduler", "background job"], "tags": ["background-jobs", "task-queue", "job-scheduler", "cron", "worker", "sidekiq", "celery", "bull"]},
    {"slug": "localization", "primary": ["localization", "internationalization", "i18n", "l10n", "translation management", "multilingual"], "strong": ["localization", "i18n", "translation management"], "tags": ["localization", "i18n", "l10n", "translation", "internationalization", "multilingual"]},
]

# Blockers — prevent false positives
BLOCKERS = {
    "authentication": ["password manager", "keepass", "bitwarden", "password vault"],
    "email-marketing": ["can i email", "osint", "whatsapp", "git email"],
    "crm-sales": ["ocrmypdf"],
    "payments": ["svg icon", "icon pack"],
    "games-entertainment": ["game theory"],
    "project-management": ["chat completion", "chatgpt", "llm chat"],
    "forms-surveys": ["form validation", "form library", "react form", "form component"],
    "database": ["database migration tool"],  # migration tools are dev tools
}

BOILERPLATE = [
    "boilerplate", "starter kit", "starter template", "scaffold",
    "saas kit", "saas template", "saas starter",
]


def score_tool(name, tagline, tags, rule):
    combined = f"{name} {tagline}".lower()
    name_lower = name.lower()
    tag_list = [t.strip().lower().replace("-", " ").replace("_", " ") for t in (tags or "").split(",") if t.strip()]

    # Blockers
    for b in BLOCKERS.get(rule["slug"], []):
        if b in combined:
            return 0

    score = 0
    # Strong name match (word boundary)
    for kw in rule["strong"]:
        pat = r'(?<![a-z])' + re.escape(kw.lower()) + r'(?![a-z])'
        if re.search(pat, name_lower):
            score += 2

    # Primary tagline match
    seen = set()
    for kw in rule["primary"]:
        kw_lower = kw.lower()
        if kw_lower in combined:
            root = kw_lower.split()[0]
            if root not in seen:
                seen.add(root)
                score += 1

    # Tag match (max 2)
    tag_hits = 0
    for rt in rule.get("tags", []):
        rt_norm = rt.lower().replace("-", " ").replace("_", " ")
        for t in tag_list:
            if rt_norm == t or rt_norm in t or t in rt_norm:
                score += 1
                tag_hits += 1
                break
        if tag_hits >= 2:
            break

    return score


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Load category slug -> id mapping
    cats = conn.execute("SELECT id, slug FROM categories").fetchall()
    slug_to_id = {c['slug']: c['id'] for c in cats}

    # Validate all rules have valid slugs
    for rule in RULES:
        if rule['slug'] not in slug_to_id:
            print(f"WARNING: rule slug '{rule['slug']}' not in categories table, skipping")

    # Load all approved tools
    tools = conn.execute("""
        SELECT t.id, t.name, t.tagline, t.tags, t.category_id, c.slug as category_slug
        FROM tools t JOIN categories c ON t.category_id = c.id
        WHERE t.status = 'approved'
        ORDER BY t.name
    """).fetchall()

    print(f"Scanning {len(tools)} approved tools...")

    assignments = []  # (tool_id, tool_name, [(cat_slug, score)])
    total_new = 0

    for tool in tools:
        name = tool['name'] or ''
        tagline = tool['tagline'] or ''
        tags = tool['tags'] or ''
        primary_slug = tool['category_slug']

        # Skip boilerplate
        combined = f"{name} {tagline}".lower()
        if any(kw in combined for kw in BOILERPLATE):
            continue

        # Score against all rules
        scored = []
        for rule in RULES:
            if rule['slug'] not in slug_to_id:
                continue
            # Skip if this IS the primary category
            if rule['slug'] == primary_slug:
                continue
            s = score_tool(name, tagline, tags, rule)
            if s >= 2:
                scored.append((rule['slug'], s))

        if not scored:
            continue

        # Take top N by score
        scored.sort(key=lambda x: -x[1])
        top = scored[:MAX_SECONDARY]
        assignments.append((tool['id'], name, top))
        total_new += len(top)

    # Report
    by_cat = defaultdict(int)
    for _, _, cats_list in assignments:
        for slug, _ in cats_list:
            by_cat[slug] += 1

    print(f"\nTools getting secondary categories: {len(assignments)}")
    print(f"Total new assignments: {total_new}")
    print(f"\nBreakdown by category:")
    for slug in sorted(by_cat.keys()):
        print(f"  {slug}: {by_cat[slug]}")

    if DRY_RUN:
        print(f"\n--- DRY RUN (showing first 30) ---")
        for tool_id, name, cats_list in assignments[:30]:
            cat_str = ", ".join(f"{s}({sc})" for s, sc in cats_list)
            print(f"  {name}: +{cat_str}")
        if len(assignments) > 30:
            print(f"  ... and {len(assignments) - 30} more")
        return

    if APPLY:
        print(f"\nApplying {total_new} secondary category assignments...")
        applied = 0
        for tool_id, name, cats_list in assignments:
            for slug, score in cats_list:
                cat_id = slug_to_id.get(slug)
                if cat_id:
                    try:
                        conn.execute(
                            "INSERT OR IGNORE INTO tool_categories (tool_id, category_id, is_primary) VALUES (?, ?, 0)",
                            (tool_id, cat_id))
                        applied += 1
                    except Exception as e:
                        print(f"  Error on {name} -> {slug}: {e}")
        conn.commit()
        print(f"Done. {applied} rows inserted into tool_categories.")

        # Verify
        total = conn.execute("SELECT COUNT(*) FROM tool_categories").fetchone()[0]
        primaries = conn.execute("SELECT COUNT(*) FROM tool_categories WHERE is_primary = 1").fetchone()[0]
        secondaries = conn.execute("SELECT COUNT(*) FROM tool_categories WHERE is_primary = 0").fetchone()[0]
        print(f"\nTotal tool_categories: {total} ({primaries} primary, {secondaries} secondary)")
    else:
        print("\nUse --dry-run to preview or --apply to execute.")

    conn.close()


if __name__ == "__main__":
    main()

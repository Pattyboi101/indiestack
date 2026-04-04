#!/usr/bin/env python3
"""
Dry-run recategoriser for IndieStack tools (v2).

Scans tools in "Developer Tools" and "AI & Automation", proposes moves
based on name + tagline + tags + URL analysis.

v2 improvements over v1:
- Tags used as a signal (1 point each, capped at 2)
- URL domain hints (e.g. "cms" in URL)
- More categories covered (Games, Learning, Newsletters, etc.)
- Outputs JSON decisions file for the apply script
- Much broader keyword coverage

Usage:
    python3 scripts/recategorise_dry_run.py --db backups/indiestack-XXXX.db
    python3 scripts/recategorise_dry_run.py --db backups/indiestack-XXXX.db --json moves.json
"""

import sqlite3
import re
import sys
import json
from collections import defaultdict

DB_PATH = "/data/indiestack.db"
if "--db" in sys.argv:
    DB_PATH = sys.argv[sys.argv.index("--db") + 1]

JSON_OUT = None
if "--json" in sys.argv:
    JSON_OUT = sys.argv[sys.argv.index("--json") + 1]

# ── Category rules ──────────────────────────────────────────────────────
RULES = [
    {
        "category_id": 12,
        "category_name": "Authentication",
        "primary": ["authentication", "auth provider", "identity provider", "identity platform",
                     "single sign-on", "sso", "oauth", "openid", "oidc", "login system",
                     "access control", "user management", "passwordless", "multi-factor",
                     "mfa", "2fa", "two-factor", "saml", "ldap", "jwt auth", "session management",
                     "role-based access"],
        "strong": ["auth", "sso", "oauth", "identity", "keycloak", "ory"],
        "tags": ["authentication", "oauth", "oauth2", "sso", "openid", "oidc", "saml",
                 "jwt", "2fa", "mfa", "identity", "passwordless", "ldap", "rbac"],
    },
    {
        "category_id": 3,
        "category_name": "Analytics & Metrics",
        "primary": ["analytics", "metrics", "event tracking", "product analytics",
                     "web analytics", "data analytics", "business intelligence",
                     "dashboard analytics", "user analytics", "clickstream",
                     "session replay", "heatmap", "a]b testing", "feature flag",
                     "usage tracking", "telemetry"],
        "strong": ["analytics", "metrics", "plausible", "matomo", "posthog", "umami"],
        "tags": ["analytics", "web-analytics", "product-analytics", "metrics",
                 "business-intelligence", "heatmap", "session-replay", "ab-testing"],
    },
    {
        "category_id": 15,
        "category_name": "Monitoring & Uptime",
        "primary": ["monitoring", "uptime", "observability", "alerting", "incident management",
                     "health check", "status page", "apm", "log management", "tracing",
                     "error tracking", "crash reporting", "server monitoring",
                     "infrastructure monitoring", "network monitoring", "application monitoring",
                     "performance monitoring", "system monitor", "resource monitor"],
        "strong": ["monitor", "uptime", "observability", "alerting", "grafana", "prometheus",
                    "nagios", "zabbix", "datadog alternative"],
        "tags": ["monitoring", "uptime", "observability", "alerting", "apm", "logging",
                 "tracing", "status-page", "error-tracking", "incident-management"],
    },
    {
        "category_id": 2,
        "category_name": "Email Marketing",
        "primary": ["email service", "email api", "email platform", "transactional email",
                     "email sending", "email delivery", "smtp", "email marketing",
                     "newsletter platform", "email automation", "email builder",
                     "email template", "mailing list", "bulk email", "email campaign"],
        "strong": ["email", "smtp", "mailer", "mailgun", "sendgrid", "postmark"],
        "tags": ["email", "smtp", "email-marketing", "newsletter", "transactional-email",
                 "email-template", "mailing-list", "email-builder"],
    },
    {
        "category_id": 13,
        "category_name": "Payments",
        "primary": ["payment", "subscription management", "checkout", "payment processing",
                     "payment gateway", "recurring payments", "dunning", "payment platform",
                     "e-commerce", "ecommerce", "online store", "shopping cart",
                     "marketplace", "digital commerce"],
        "strong": ["payment", "checkout", "dunning", "ecommerce", "e-commerce", "shopify"],
        "tags": ["payments", "payment", "ecommerce", "e-commerce", "checkout", "stripe",
                 "shopping-cart", "marketplace", "online-store", "cart"],
    },
    {
        "category_id": 1,
        "category_name": "Invoicing & Billing",
        "primary": ["invoice", "invoicing", "billing software", "accounting",
                     "expense", "bookkeeping", "financial management", "billing platform",
                     "receipt", "tax calculation", "payroll"],
        "strong": ["invoice", "invoicing", "accounting", "bookkeeping"],
        "tags": ["invoice", "invoicing", "accounting", "billing", "bookkeeping",
                 "expense", "payroll", "tax"],
    },
    {
        "category_id": 9,
        "category_name": "Forms & Surveys",
        "primary": ["form builder", "survey tool", "survey platform", "questionnaire",
                     "data collection form", "form backend", "form handling",
                     "typeform alternative", "google forms alternative"],
        "strong": ["form builder", "survey tool", "survey platform"],
        "tags": ["form-builder", "forms", "survey", "surveys", "questionnaire",
                 "form-backend", "typeform"],
    },
    {
        "category_id": 4,
        "category_name": "Project Management",
        "primary": ["project management", "task management", "kanban", "issue tracker",
                     "bug tracker", "sprint planning", "agile", "team collaboration",
                     "work management", "note-taking", "notes app", "knowledge management",
                     "team workspace", "collaboration platform", "team chat",
                     "group chat", "messaging platform", "instant messaging"],
        "strong": ["project management", "kanban", "issue tracker", "note-taking",
                    "team chat", "collaboration"],
        "tags": ["project-management", "kanban", "issue-tracker", "task-management",
                 "todo", "agile", "scrum", "note-taking", "notes", "knowledge-base",
                 "team-collaboration", "team-chat", "chat", "messaging", "slack-alternative"],
    },
    {
        "category_id": 5,
        "category_name": "Customer Support",
        "primary": ["helpdesk", "help desk", "customer support", "live chat",
                     "ticketing system", "support platform", "customer service",
                     "intercom alternative", "zendesk alternative", "support ticket",
                     "chat widget", "chatbot for support"],
        "strong": ["helpdesk", "help desk", "support platform", "ticketing system",
                    "live chat widget"],
        "tags": ["helpdesk", "help-desk", "customer-support", "live-chat", "ticketing",
                 "support", "customer-service", "chat-widget", "intercom"],
    },
    {
        "category_id": 14,
        "category_name": "SEO Tools",
        "primary": ["seo", "search engine optimization", "keyword research", "backlink",
                     "serp", "site audit", "rank tracking", "meta tags", "sitemap generator",
                     "seo analysis", "search ranking"],
        "strong": ["seo"],
        "tags": ["seo", "search-engine-optimization", "keyword-research", "backlink",
                 "serp", "rank-tracking"],
    },
    {
        "category_id": 10,
        "category_name": "CRM & Sales",
        "primary": ["crm", "customer relationship", "sales pipeline", "lead management",
                     "sales automation", "contact management", "deal tracking",
                     "sales platform", "erp"],
        "strong": ["crm", "erp"],
        "tags": ["crm", "sales", "leads", "sales-pipeline", "customer-relationship",
                 "erp", "lead-management"],
    },
    {
        "category_id": 8,
        "category_name": "Landing Pages",
        "primary": ["landing page", "page builder", "website builder", "site builder",
                     "cms", "content management system", "headless cms", "blog platform",
                     "wiki platform", "wiki engine", "static site", "website template",
                     "web publishing"],
        "strong": ["cms", "content management", "wiki", "page builder", "website builder"],
        "tags": ["cms", "content-management", "headless-cms", "wiki", "page-builder",
                 "website-builder", "static-site", "blog-engine", "blog-platform",
                 "static-site-generator"],
    },
    {
        "category_id": 6,
        "category_name": "Scheduling & Booking",
        "primary": ["scheduling", "booking system", "appointment", "calendar app",
                     "reservation system", "time slot", "meeting scheduler",
                     "calendly alternative"],
        "strong": ["scheduling", "booking", "appointment", "calendly"],
        "tags": ["scheduling", "booking", "appointment", "calendar", "reservation",
                 "meeting-scheduler"],
    },
    {
        "category_id": 7,
        "category_name": "Social Media",
        "primary": ["social media", "social network", "social platform", "fediverse",
                     "mastodon", "activitypub", "microblog", "social sharing",
                     "community platform", "forum software", "discussion platform"],
        "strong": ["social media", "fediverse", "mastodon", "activitypub", "forum"],
        "tags": ["social-media", "social-network", "fediverse", "mastodon", "activitypub",
                 "forum", "community", "discussion", "microblog"],
    },
    {
        "category_id": 11,
        "category_name": "File Management",
        "primary": ["file storage", "file sharing", "file manager", "cloud storage",
                     "object storage", "s3 compatible", "document management",
                     "file hosting", "file sync", "file browser", "network attached storage",
                     "nas", "personal cloud", "file server"],
        "strong": ["file manager", "object storage", "cloud storage", "file sharing",
                    "file browser", "nas"],
        "tags": ["file-management", "file-sharing", "cloud-storage", "object-storage",
                 "s3", "file-manager", "nas", "file-sync", "document-management"],
    },
    {
        "category_id": 17,
        "category_name": "Design & Creative",
        "primary": ["design tool", "graphic design", "image editor", "photo editor",
                     "ui design", "diagram tool", "whiteboard", "drawing app",
                     "vector graphics", "icon design", "mockup", "wireframe",
                     "prototyping tool"],
        "strong": ["design tool", "image editor", "photo editor", "whiteboard",
                    "diagram tool", "wireframe"],
        "tags": ["design", "graphic-design", "image-editor", "photo-editor", "ui-design",
                 "diagram", "whiteboard", "wireframe", "mockup", "prototyping",
                 "vector-graphics"],
    },
    {
        "category_id": 43,
        "category_name": "Games & Entertainment",
        "primary": ["game engine", "game server", "game development", "gaming",
                     "music player", "media player", "media server", "video player",
                     "streaming server", "plex alternative", "movie", "tv show",
                     "podcast player", "audio player", "music streaming",
                     "video streaming", "media management", "media center",
                     "ebook reader", "comic reader", "photo gallery", "photo management"],
        "strong": ["game engine", "game server", "media server", "music player",
                    "media player", "plex", "emby", "jellyfin", "photo gallery"],
        "tags": ["game", "gaming", "game-engine", "game-server", "game-development",
                 "media-server", "music-player", "media-player", "plex", "video-player",
                 "streaming", "podcast", "ebook", "comic", "photo-gallery",
                 "music", "media", "movies", "tv-shows"],
    },
    {
        "category_id": 44,
        "category_name": "Learning & Education",
        "primary": ["learning platform", "lms", "learning management", "online course",
                     "educational", "e-learning", "tutorial platform", "training platform",
                     "quiz platform", "classroom"],
        "strong": ["lms", "learning management", "e-learning", "online course"],
        "tags": ["education", "learning", "lms", "e-learning", "tutorial", "course",
                 "training", "classroom", "quiz"],
    },
    {
        "category_id": 45,
        "category_name": "Newsletters & Content",
        "primary": ["newsletter", "blog newsletter", "content platform",
                     "publishing platform", "rss reader", "feed reader", "feed aggregator",
                     "read later", "content curation", "news aggregator"],
        "strong": ["newsletter", "rss reader", "feed reader", "news aggregator"],
        "tags": ["newsletter", "rss", "rss-reader", "feed-reader", "content",
                 "publishing", "news-aggregator", "read-later"],
    },
    {
        "category_id": 20,
        "category_name": "Feedback & Reviews",
        "primary": ["feedback tool", "user feedback", "feature request", "roadmap tool",
                     "changelog", "product feedback", "customer feedback", "review platform",
                     "testimonial", "nps", "user research"],
        "strong": ["feedback tool", "feature request", "roadmap tool", "changelog",
                    "testimonial"],
        "tags": ["feedback", "feature-requests", "roadmap", "changelog", "testimonials",
                 "user-feedback", "nps", "user-research"],
    },
    {
        "category_id": 46,
        "category_name": "Creative Tools",
        "primary": ["video editor", "audio editor", "music production", "podcast editor",
                     "screen recorder", "screenshot tool", "animation tool",
                     "3d modeling", "video creation"],
        "strong": ["video editor", "audio editor", "screen recorder", "podcast editor"],
        "tags": ["video-editor", "audio-editor", "screen-recorder", "animation",
                 "music-production", "3d", "screenshot"],
    },
    {
        "category_id": 16,
        "category_name": "API Tools",
        "primary": ["api gateway", "api management", "api documentation", "api testing",
                     "api platform", "api marketplace", "graphql platform",
                     "api monitoring", "api security"],
        "strong": ["api gateway", "api management", "api platform"],
        "tags": ["api-gateway", "api-management", "api-documentation", "api-testing",
                 "graphql", "api-platform"],
    },
]

# ── Secondary mention patterns ──────────────────────────────────────────
SECONDARY_PATTERNS = [
    r"\bwith\s+(?:built[- ]in\s+)?{kw}",
    r"\bsupports?\s+{kw}",
    r"\binclud(?:es?|ing)\s+{kw}",
    r"\bplus\s+{kw}",
    r"\band\s+{kw}\b",
    r"\bintegrates?\s+(?:with\s+)?{kw}",
    r"\b{kw}\s+(?:support|integration|plugin|module)\b",
]

# ── Boilerplate indicators ──────────────────────────────────────────────
BOILERPLATE_KEYWORDS = [
    "boilerplate", "starter kit", "starter template", "scaffold", "saas kit",
    "saas template", "saas starter", "full-stack template", "fullstack template",
    "everything you need", "complete platform", "batteries included",
]

# ── False positive blockers ─────────────────────────────────────────────
FALSE_POSITIVE_BLOCKERS = {
    "Authentication": ["password manager", "keepass", "password vault", "password store",
                       "bitwarden", "password generator"],
    "Email Marketing": ["can i email", "compatibility", "support tables", "osint",
                        "whatsapp", "claude code skill", "claude email", "git email"],
    "CRM & Sales": ["ocr", "ocrmypdf"],
    "Payments": ["svg icon", "icon pack", "icon set", "credit card icon"],
    "Games & Entertainment": ["game theory", "game changer"],
    "Project Management": ["chat completion", "chat model", "chatgpt", "llm chat"],
    "Landing Pages": ["cms flaws", "cmsms"],
    "Forms & Surveys": ["form validation", "form library", "form handling library",
                        "react form", "form component"],
}


def is_secondary_mention(text: str, keyword: str) -> bool:
    text_lower = text.lower()
    keyword_lower = keyword.lower()
    if keyword_lower not in text_lower:
        return True
    for pattern_template in SECONDARY_PATTERNS:
        pattern = pattern_template.format(kw=re.escape(keyword_lower))
        if re.search(pattern, text_lower):
            cleaned = re.sub(pattern, "", text_lower)
            if keyword_lower not in cleaned:
                return True
    return False


def is_boilerplate(name: str, tagline: str) -> bool:
    combined = f"{name} {tagline}".lower()
    return any(kw in combined for kw in BOILERPLATE_KEYWORDS)


def score_tool(name: str, tagline: str, tags: str, url: str, rule: dict) -> tuple[int, list[str]]:
    """Score how well a tool matches a category rule. Uses name + tagline + tags + URL."""
    combined = f"{name} {tagline}".lower()
    name_lower = name.lower()
    url_lower = (url or "").lower()
    tag_list = [t.strip().lower() for t in (tags or "").split(",") if t.strip()]
    matches = []

    # Check false-positive blockers
    blockers = FALSE_POSITIVE_BLOCKERS.get(rule["category_name"], [])
    if any(b in combined for b in blockers):
        return 0, []

    # 1. Strong keywords in tool NAME (2 points each, word-boundary)
    for kw in rule["strong"]:
        pattern = r'(?<![a-z])' + re.escape(kw.lower()) + r'(?![a-z])'
        if re.search(pattern, name_lower):
            matches.append(f"name:{kw}")

    # 2. Primary keywords in tagline (1 point each)
    for kw in rule["primary"]:
        if kw.lower() in combined:
            if not is_secondary_mention(f"{name} {tagline}", kw):
                matches.append(f"tagline:{kw}")

    # 3. Tags (1 point each, max 2 — tags are explicit labels so they're reliable)
    rule_tags = rule.get("tags", [])
    tag_matches = 0
    for rt in rule_tags:
        rt_lower = rt.lower().replace("-", " ").replace("_", " ")
        for t in tag_list:
            t_norm = t.replace("-", " ").replace("_", " ")
            if rt_lower == t_norm or rt_lower in t_norm or t_norm in rt_lower:
                matches.append(f"tag:{t}")
                tag_matches += 1
                if tag_matches >= 2:
                    break
        if tag_matches >= 2:
            break

    # Deduplicate conceptually similar matches
    unique_concepts = set()
    deduped = []
    for m in matches:
        concept = m.split(":")[-1].split()[0]
        if concept not in unique_concepts:
            unique_concepts.add(concept)
            deduped.append(m)

    # Score: name=2, tagline=1, tag=1
    score = 0
    for m in deduped:
        if m.startswith("name:"):
            score += 2
        else:
            score += 1

    return score, deduped


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    SOURCE_CATEGORIES = (18, 19)  # Developer Tools, AI & Automation
    tools = conn.execute(
        """SELECT id, name, slug, tagline, url, tags, category_id
           FROM tools
           WHERE category_id IN (?, ?) AND status = 'approved'
           ORDER BY name""",
        SOURCE_CATEGORIES,
    ).fetchall()

    print(f"Scanning {len(tools)} tools in Developer Tools + AI & Automation...\n")

    proposals = []
    multi_match = []
    skipped_boilerplate = []

    for tool in tools:
        name = tool["name"] or ""
        tagline = tool["tagline"] or ""
        tags = tool["tags"] or ""
        url = tool["url"] or ""

        if is_boilerplate(name, tagline):
            skipped_boilerplate.append(tool)
            continue

        category_scores = []
        for rule in RULES:
            if rule["category_id"] == tool["category_id"]:
                continue
            score, matches = score_tool(name, tagline, tags, url, rule)
            if score >= 2:
                category_scores.append((score, rule, matches))

        if not category_scores:
            continue

        category_scores.sort(key=lambda x: -x[0])

        if len(category_scores) >= 2 and category_scores[0][0] == category_scores[1][0]:
            multi_match.append((tool, category_scores))
        else:
            best_score, best_rule, best_matches = category_scores[0]
            proposals.append((tool, best_rule, best_score, best_matches))

    # ── Report ──────────────────────────────────────────────────────────
    from_name = {18: "Developer Tools", 19: "AI & Automation"}

    by_target = defaultdict(list)
    for tool, rule, score, matches in proposals:
        by_target[rule["category_name"]].append((tool, score, matches))

    print("=" * 80)
    print(f"RECATEGORISATION PROPOSALS (dry run v2)")
    print(f"=" * 80)
    print(f"\nTotal tools scanned: {len(tools)}")
    print(f"Proposals: {len(proposals)}")
    print(f"Multi-category (needs manual review): {len(multi_match)}")
    print(f"Skipped (boilerplate/multi-purpose): {len(skipped_boilerplate)}")
    print()

    for target_cat in sorted(by_target.keys()):
        items = by_target[target_cat]
        items.sort(key=lambda x: -x[1])
        print(f"\n{'─' * 70}")
        print(f"→ {target_cat} ({len(items)} tools)")
        print(f"{'─' * 70}")
        for tool, score, matches in items:
            src = from_name.get(tool["category_id"], "?")
            tags_str = (tool["tags"] or "")[:60]
            print(f"  [{score}] {tool['name']}")
            print(f"      from: {src} | slug: {tool['slug']}")
            print(f"      tagline: {(tool['tagline'] or '')[:100]}")
            print(f"      tags: {tags_str}")
            print(f"      matched: {', '.join(matches)}")
            print()

    if multi_match:
        print(f"\n{'=' * 70}")
        print(f"MANUAL REVIEW NEEDED — matched multiple categories equally")
        print(f"{'=' * 70}")
        for tool, scores in multi_match:
            src = from_name.get(tool["category_id"], "?")
            print(f"\n  {tool['name']} (from {src})")
            print(f"      tagline: {(tool['tagline'] or '')[:100]}")
            for score, rule, matches in scores[:3]:
                print(f"      [{score}] → {rule['category_name']}: {', '.join(matches)}")

    if skipped_boilerplate:
        print(f"\n{'=' * 70}")
        print(f"SKIPPED — boilerplate/multi-purpose tools ({len(skipped_boilerplate)})")
        print(f"{'=' * 70}")
        for tool in skipped_boilerplate[:20]:
            print(f"  {tool['name']}: {(tool['tagline'] or '')[:80]}")
        if len(skipped_boilerplate) > 20:
            print(f"  ... and {len(skipped_boilerplate) - 20} more")

    # Summary table
    print(f"\n{'=' * 70}")
    print(f"SUMMARY")
    print(f"{'=' * 70}")
    print(f"{'Target Category':<30s} {'Count':>5s}")
    print(f"{'─' * 35}")
    for target_cat in sorted(by_target.keys()):
        print(f"{target_cat:<30s} {len(by_target[target_cat]):>5d}")
    print(f"{'─' * 35}")
    print(f"{'TOTAL PROPOSED':<30s} {len(proposals):>5d}")
    print(f"{'Manual review':<30s} {len(multi_match):>5d}")
    print(f"{'Skipped boilerplate':<30s} {len(skipped_boilerplate):>5d}")

    # Output JSON if requested
    if JSON_OUT:
        decisions = []
        for tool, rule, score, matches in proposals:
            decisions.append({
                "id": tool["id"],
                "name": tool["name"],
                "slug": tool["slug"],
                "old_category_id": tool["category_id"],
                "old_category_name": from_name.get(tool["category_id"], "?"),
                "new_category_id": rule["category_id"],
                "new_category_name": rule["category_name"],
                "score": score,
                "matches": matches,
            })
        with open(JSON_OUT, "w") as f:
            json.dump(decisions, f, indent=2)
        print(f"\nJSON decisions written to {JSON_OUT}")

    conn.close()


if __name__ == "__main__":
    main()

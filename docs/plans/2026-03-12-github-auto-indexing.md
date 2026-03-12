# GitHub Auto-Indexing Design

**Goal:** Grow the catalog from 835 to 5,000+ tools by automatically discovering indie projects on GitHub, filtering for quality, and importing them as pending submissions.

**Constraint:** Must not sacrifice curation quality. All auto-indexed tools land as "pending" for manual review.

---

## How It Works

### 1. Discovery Sources

**GitHub Search API** (`/search/repositories`):
- Query by topic tags: `mcp-server`, `self-hosted`, `indie`, `saas`, `open-source`, `developer-tools`
- Query by description keywords matching IndieStack categories
- Filter: `stars:>10`, `pushed:>2025-01-01` (active), `forks:<1000` (not mega-projects)
- Sort by: `stars`, `updated`
- Rate limit: 30 requests/minute (authenticated), 10/minute (unauthenticated)

**GitHub Topics API** (`/search/topics`):
- Browse trending topics related to IndieStack categories
- Follow topic chains (e.g., `self-hosted` → linked repos)

**Awesome Lists Parsing:**
- Parse well-known awesome lists (awesome-selfhosted, awesome-saas-services, awesome-indie)
- Extract repo URLs, descriptions, categories
- These lists are already curated — high signal

### 2. Quality Filters

A repo passes if it meets ALL of:
- Stars >= 10 (minimum traction)
- Last push within 6 months (actively maintained)
- Has a README (minimum documentation)
- Not a fork (original work)
- Owner has < 50 repos (indie signal — not a corporate account)
- Not already in IndieStack catalog (dedup by URL)
- Not in a blocklist (known non-indie: Microsoft, Google, AWS, etc.)

Optional quality boost signals (not required):
- Has releases/tags (shipping culture)
- Has a LICENSE file (open-source intent)
- Description length > 20 chars (effort in presentation)
- Owner has < 10 employees on GitHub org (indie team size)

### 3. Category Mapping

Map GitHub topics → IndieStack categories:
```python
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
    "self-hosted": "developer-tools",  # default, refine by other topics
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
```

### 4. Implementation

**New file:** `src/indiestack/indexer.py`

**CLI command** (not background task — run manually or via cron):
```bash
python3 -m indiestack.indexer --source github --min-stars 10 --dry-run
python3 -m indiestack.indexer --source github --min-stars 10 --import
python3 -m indiestack.indexer --source awesome-selfhosted --import
```

**Flow:**
1. Query GitHub Search API with configured queries
2. Filter results through quality checks
3. Map topics to categories
4. Generate tagline from repo description (truncate to 100 chars)
5. Generate description from README first paragraph (truncate to 500 chars)
6. Check for existing tool with same URL (dedup)
7. Insert as `status='pending'` with `submitted_from_ip='auto-indexer'`
8. Log results: `{imported: N, skipped: N, already_exists: N, low_quality: N}`

**Enrichment auto-applies:** When auto-indexed tools get approved and the server restarts, `_enrich_tool_metadata()` will auto-populate structured metadata for any tools whose slugs match the enrichment list.

### 5. Rate Limiting & Politeness

- Respect GitHub API rate limits (check `X-RateLimit-Remaining` header)
- Sleep between pages (1 second)
- Cache seen repos to avoid re-querying
- Log everything for audit

### 6. Admin Integration

- Pending tools from auto-indexer show `submitted_from_ip = 'auto-indexer'` in admin
- Admin can filter pending tools by source
- Bulk approve/reject flows already exist

---

## Phased Rollout

**Phase 1 (next session):** CLI script that queries GitHub Search API for one category (e.g., `self-hosted`), filters, and imports as pending. Manual run only.

**Phase 2:** Expand to all categories. Add awesome-list parsing. Add Fly.io cron (weekly run).

**Phase 3:** Auto-generate structured metadata from README parsing (detect install commands, env vars, API docs links). Feed into enrichment pipeline.

---

## Expected Impact

- Phase 1: +100-200 pending tools from a single GitHub search
- Phase 2: +1,000-2,000 pending tools across all categories
- Phase 3: Auto-enriched metadata for newly indexed tools

With Patrick reviewing ~50 tools per session, Phase 1 provides weeks of review queue.

---

## Risks

- **Quality dilution:** Mitigated by mandatory manual review (all land as pending)
- **GitHub rate limits:** 30 req/min authenticated. A full sweep of 25 categories × 10 pages = 250 requests ≈ 9 minutes. Manageable.
- **Category mismatches:** Some repos won't map cleanly. Default to "Developer Tools" and let admin recategorize.
- **Non-indie repos:** The owner filter (< 50 repos) catches most corporate accounts, but some will slip through. Manual review is the safety net.

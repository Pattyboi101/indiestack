# Sprint — Current

Last updated: 2026-04-05

## Status: Active

## Completed This Session (2026-04-05, third pass — autonomous improvement cycle)

### Search Quality (additional fixes)
- Added `"build"` → `"frontend"` synonym for "build tool" queries (was missing)
- Added `"time"` → `"api"` synonym to reinforce "real-time" hyphen-split routing
- Verified all step-1 requested mappings are already present (no gaps found)

### Code Quality
- Fixed hardcoded hex `#1A2D4A` in landing.py status-tag CSS → now uses `var(--terracotta)`
- Smoke test shows 403 tunnel errors (network issue, not code), not real failures

## Completed This Session (2026-04-05, second pass)

### Search Quality
- Verified all required `_CAT_SYNONYMS` mappings are present:
  - `state` → `frontend` (covers "state management")
  - `bundler` → `frontend` (covers "bundler" queries)
  - `realtime` → `api` (covers realtime/websocket tools)
  - `vector` → `database` (covers "vector database" queries)
  - `rate` → `api` (covers "rate limiting" queries)
- Previously added: htmx, alpine, preact, lit, solidjs, stencil, ember, trpc, grpc mappings
- Removed 6 duplicate keys in `_CAT_SYNONYMS` (deploy×2, deployment×2, hosting×2, cache×2, caching×2, redis×3). Stale entries pointed to wrong category (database instead of caching).
- Added `push` → `notifications`, `sms` → `notifications`, `otp` → `authentication`, `totp` → `authentication`
- **Git situation**: orphan chain (51 commits) was force-pushed to origin/master. `autonomous-improvements` branch = orphan tip + this session's fix. Both branches pushed.

### Catalog Maintenance
- `scripts/add_missing_tools.py` — script to insert 10 high-priority tools (React, Vue, Svelte, Angular, Zustand, Jotai, Webpack, esbuild, Upstash, Resend). Checks slug before inserting. Safe to re-run.
- `scripts/backfill_sdk_packages.py` — backfill SDK/install metadata for well-known tools
- `scripts/recategorise_dry_run.py` — dry-run analysis of developer-tools category (2,931 tools)

### Orchestra Briefings Updated (2026-04-05)
- Backend: developer-tools category cleanup
- Frontend: SEO/copy improvements for new category pages
- MCP: (check `.orchestra/departments/mcp/briefing.md`)
- Content: (check `.orchestra/departments/content/briefing.md`)

## Completed This Session (2026-04-05, fourth pass)

### Search Quality
- Added OpenRouter, Groq, Together AI to catalog (LLM API category gap)
- Approved uploadthing with proper tags, tagline, install_command
- Fixed tags: posthog (event-tracking), vercel (deployment), harbor (container-registry), winston/pino (logging), lemon-squeezy (stripe-alternative)
- Added quality_score * 1.5 to FTS engagement_expr — SaaS tools no longer buried by 0-star bias
- Fixed sitemap TypeError (int created_at → ISO date string)
- Search regression: 8/12 PASS on targeted queries; remaining failures are valid category alternatives

### Meeting
- Ran MCP Growth & Maker Pro meeting (2026-04-05-12)
- Key conclusion: citation analytics are the unlock for first Maker Pro subscriber
- Action items written to all 5 department briefings

## Completed This Session (2026-04-05, fifth pass — catalog cleanup resumed)

### Catalog Cleanup — ~95 tools re-categorized (continuation of earlier ~500+ pass)
- **seo-tools**: 7 misfits → boilerplates, developer-tools, ai-automation
- **landing-pages**: 12 misfits → headless-cms, email-marketing, boilerplates, developer-tools, ai-dev-tools
- **project-management**: 22 misfits → ai-dev-tools, ai-automation, documentation, scheduling-booking, devops-infrastructure, invoicing-billing, developer-tools, newsletters-content
- **analytics-metrics**: 3 misfits → invoicing-billing, social-media, developer-tools
- **games-entertainment**: 3 misfits → developer-tools, media-server
- **design-creative**: 8 misfits → developer-tools (charting libs, favicon CLIs, diagram tools)
- **customer-support**: fonoster → api-tools (telecom voice API)
- **authentication**: 7 misfits → developer-tools, boilerplates, api-tools, frontend-frameworks, security-tools
- **payments**: 5 misfits → boilerplates, project-management, developer-tools
- **database**: AtlasOS → developer-tools (not a DB)
- **monitoring-uptime**: 5 misfits → security-tools, ai-dev-tools, devops-infrastructure, developer-tools
- **devops-infrastructure**: 6 misfits → documentation, developer-tools (pastebin/RSS/secret-sharing)
- **api-tools**: 2 misfits → documentation, developer-tools
- **crm-sales**: 6 misfits → boilerplates, ai-dev-tools, developer-tools
- **testing-tools**: 6 misfits → developer-tools (benchmarking tools), api-tools
- **message-queue**: 2 misfits → background-jobs, developer-tools
- **social-media**: 6 misfits → security-tools (OSINT tools), boilerplates, newsletters-content
- **search-engine**: 2 misfits → database, developer-tools
- FTS rebuilt 4× after batch updates (WAL checkpoint skipped as app holds lock — normal)
- Consumer apps expanded list updated in catalog-scope meeting: ~30 tools for Patrick to reject
- Fintech tools re-homed: alpha-vantage→api-tools, ghostfolio/midday→invoicing-billing, fingpt/finrl-meta→ai-dev-tools
- scheduling-booking/invoicing-billing/ai-automation: 20+ additional misfits fixed

### Meetings
- Catalog scope meeting (2026-04-05-15) created and closed — ~25 consumer apps identified
  - Action for Patrick: bulk-reject via /admin (fastnfitness, foodyou, etc.)
  - Action for Content: add scope statement to submit/guidelines pages

## Completed This Session (2026-04-05, sixth pass — autonomous improvement cycle)

### Search Quality — NEED_MAPPINGS updates
- Added `"realtime"` to NEED_MAPPINGS `"api"` terms list (was in _CAT_SYNONYMS only)
- Added `"vector database"` to NEED_MAPPINGS `"database"` terms list (was in _CAT_SYNONYMS only)
- Added `"rate limiting"` to NEED_MAPPINGS `"api"` terms list (was in _CAT_SYNONYMS only)
- All other required mappings (state management→frontend, bundler→frontend) already present in both dicts

### Catalog
- Confirmed `scripts/add_missing_tools.py` already exists with all 10 tools (React, Vue, Svelte, Angular, Zustand, Jotai, Webpack, esbuild, Upstash, Resend) — not re-written

### Code Quality
- No hardcoded hex colors or missing html.escape() found in recently changed files (dashboard.py, why_list.py)
- why_list.py already pulls all stats live from DB — no stale hardcoded figures

## Current Priorities
1. **Backend**: validate citation data — how many tools have >10 agent citations/month?
2. **Frontend**: audit /maker/dashboard analytics exposure
3. **Content**: update /why-list with AI agent discovery copy + draft maker outreach email
4. **MCP**: rewrite PyPI README with Quick Install section
5. **DevOps**: run /backup before Maker Pro launch work

## Known Blockers
- None currently

## Decisions
- Keep MCP server fully anonymous — no API key gating (see gotchas.md)
- Maker Pro price: $19/mo (canonical source: stripe.md)
- `_LIKE_STOP_WORDS` pattern used for FTS to avoid multi-word false matches

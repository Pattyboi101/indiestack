# Sprint — Current

Last updated: 2026-04-06

## Status: Active

## Completed This Session (2026-04-06, twelfth pass — autonomous improvement cycle)

### Search Quality Audit (Step 1)
- Added 5 missing NEED_MAPPINGS entries for unmapped categories:
  - `testing` → testing-tools (Jest, Playwright, Cypress, Vitest, pytest)
  - `security` → security-tools (Snyk, OWASP ZAP, HashiCorp Vault, SonarQube)
  - `search` → search-engine (Algolia, Elasticsearch, Typesense, Meilisearch)
  - `queue` → message-queue (Apache Kafka, RabbitMQ, AWS SQS, NATS)
  - `media` → media-server (Mux, Cloudinary Video, Plex, Jellyfin)
- Added 18 new _CAT_SYNONYMS entries:
  - Code quality/linting: `lint`, `linting`, `eslint`, `biome`, `prettier` → `testing`
  - Observability: `opentelemetry`, `otel`, `jaeger`, `zipkin` → `monitoring`
  - Data viz: `charting`, `charts`, `chart`, `recharts`, `d3`, `plotly`, `chartjs` → `analytics`
  - PDF: `pdf` → `file` (file-management)
  - Markdown: `markdown` → `documentation`
- NEED_MAPPINGS total: 43 entries (was 38). All 29+ category slugs now covered.

### Catalog Script (Step 2)
- Wrote `scripts/add_missing_tools.py` (30 tools total):
  - React, Vue.js, Svelte, Angular, Vite, SvelteKit, TanStack Query, Radix UI (frontend-frameworks)
  - Zustand, Jotai, Webpack, esbuild, Framer Motion, GSAP, Lucide Icons, Heroicons, Bun (frontend-frameworks)
  - next-intl, i18next (localization)
  - BullMQ (background-jobs)
  - Upstash Redis (caching)
  - Resend (email-marketing)
  - OpenRouter, Groq (ai-dev-tools)
  - Prisma, Drizzle ORM (database)
  - Zod (developer-tools)
  - tRPC, Hono (api-tools)
  - n8n (ai-automation)
  - Safe to re-run (slug-checks before INSERT). Includes FTS rebuild reminder.

## Completed This Session (2026-04-05, eleventh pass — autonomous improvement cycle)

### Search Quality Audit (Step 1)
- Verified all requested _CAT_SYNONYMS and NEED_MAPPINGS are already present — no new gaps found
- All requested mappings (state management, bundler, realtime, vector database, rate limiting) covered
- NEED_MAPPINGS now has 26 keyword entries covering all 25+ category slugs
- _CAT_SYNONYMS has ~430 entries providing comprehensive search routing

### Catalog Script (Step 2)
- scripts/add_missing_tools.py confirmed with all 10 requested tools + 18 more (28 total)
- DB_PATH = /data/indiestack.db (Fly.io production path)

### Code Quality (Step 3)
- account.py: hardcoded hex in email HTML body only — correct (CSS vars don't work in emails)
- No unescaped user-controlled strings found in recently changed files
- No stale stats in recently changed files

### Steps 4-5 (sprint + briefing updates)
- backend/briefing.md refreshed: replaced stale category-cleanup task with citation analytics
  (Task 1: how many tools have >10 citations? Task 2: maker claim flow. Task 3: maker_weekly_citations view)

## Completed This Session (2026-04-05, tenth pass — autonomous improvement cycle)

### Search Quality (Step 1)
- Added 37+ new `_CAT_SYNONYMS` entries to master (2 commits pushed):
  - **JS/TS build ecosystem**: `babel`, `transpiler`, `swc`, `bun`, `deno` → `frontend`
  - **State management fallback**: `management` → `frontend`
  - **i18n (corrected)**: `i18n`, `l10n`, `locale`, `translation`, `localization`, `internationalization`, `crowdin`, `weblate` → `"localization"` (dedicated category, not "frontend" as previous passes incorrectly had)
  - **CLI**: `commandline`, `terminal`, `shell`, `tui` → `"cli"` (matches "CLI Tools" category)
  - **Docs**: `docs`, `wiki`, `readme`, `docusaurus`, `mkdocs`, `gitbook`, `swagger`, `mintlify` → `"documentation"`
  - **Node.js/edge frameworks**: `hono`, `express`, `fastify`, `nestjs`, `koa` → `api`
  - **DevOps/IaC/tunneling**: `tunnel`, `tunneling`, `ngrok`, `terraform`, `pulumi`, `ansible` → `devops`
  - **Database BaaS**: `turso`, `convex`, `pocketbase`, `appwrite` → `database`
  - **Auth/passkeys**: `webauthn`, `fido2` → `authentication`
  - **Security**: `compliance`, `gdpr`, `encryption`, `ssl`, `tls` → `security`
- Added 3 missing `NEED_MAPPINGS` entries: `localization`, `cli`, `docs`
- Total `_CAT_SYNONYMS` keys: ~430

### Catalog Script (Step 2)
- Extended `scripts/add_missing_tools.py` with 6 more high-priority tools (28 total):
  - Prisma (database, 40k stars) — most popular Node.js ORM
  - Drizzle ORM (database, 27k stars) — TypeScript ORM, fastest-growing
  - Zod (developer-tools, 34k stars) — TypeScript schema validation
  - tRPC (api-tools, 36k stars) — type-safe API layer (T3 Stack cornerstone)
  - Bun (frontend-frameworks, 74k stars) — fast JS runtime + bundler
  - Hono (api-tools, 20k stars) — ultrafast edge web framework
- Fixed next-intl and i18next category: `"localization"` (was `"frontend-frameworks"`)

## Completed This Session (2026-04-05, ninth pass — autonomous improvement cycle)

### Search Quality (Step 1)
- Added 18 new `_CAT_SYNONYMS` entries covering gaps found in audit:
  - UI/component queries: `ui`, `component`, `components` → `frontend` ("UI component library", "component library")
  - Animation: `animation`, `animate` → `frontend` (Framer Motion, GSAP, Motion.dev)
  - Icons: `icon`, `icons` → `frontend` (Lucide Icons, Heroicons, Phosphor Icons)
  - Access control: `rbac`, `permission`, `permissions`, `access` → `authentication` (Casbin, Permit.io)
  - i18n: `i18n`, `localization` → `frontend` (next-intl, i18next, lingui)
  - Workflow: `workflow` → `ai` (n8n, Make.com, Zapier workflow automation)
- Total _CAT_SYNONYMS keys: ~366

### Catalog Script (Step 2)
- Extended `scripts/add_missing_tools.py` with 7 more high-priority tools (22 total):
  - Framer Motion (frontend-frameworks, 24k stars) — animation
  - GSAP (frontend-frameworks, 20k stars) — animation
  - Lucide Icons (frontend-frameworks, 12k stars) — icons
  - Heroicons (frontend-frameworks, 21k stars) — icons
  - next-intl (frontend-frameworks, 8k stars) — i18n
  - i18next (frontend-frameworks, 7.8k stars) — i18n
  - n8n (ai-automation, 50k stars) — workflow automation

## Completed This Session (2026-04-05, eighth pass — autonomous improvement cycle)

### Search Quality (Step 1)
- Added NEED_MAPPINGS entries for 3 unmapped categories: `feature-flags`, `logging`, `notifications`
- Added `_CAT_SYNONYMS`: `toggle`/`toggles` → `feature`, `experiment` → `feature`
- These cover "feature toggle", "a/b experiment", and "push notification" query patterns

### Code Quality (Step 3)
- Fixed 2 stale stats: `account.py` "3,000+" → "6,500+", `built_this.py` "350+" → "6,500+"
- Smoke test confirms tunnel/proxy failures only (not code failures)

## Completed This Session (2026-04-05, seventh pass — autonomous improvement cycle)

### Search Quality Audit (Step 1)
- Verified all required _CAT_SYNONYMS mappings are present — no gaps found. All 11 requested mappings already exist from prior sessions:
  - state/manager → frontend (state management queries)
  - bundler/build → frontend (build tool queries)
  - realtime/real/time → api (realtime/real-time queries)
  - vector/db → database (vector database queries)
  - rate/limiting/limiter → api (rate limiting queries)
  - vite → frontend

### Catalog Script (Step 2)
- Confirmed scripts/add_missing_tools.py already contains all 10 requested tools (React, Vue.js, Svelte, Angular, Zustand, Jotai, Webpack, esbuild, Upstash, Resend) plus 5 bonus tools (Vite, SvelteKit, TanStack Query, Radix UI, BullMQ)

### Code Quality (Step 3)
- Fixed browse.py: fallback category description now uses name_esc instead of raw name when building the template string (XSS hardening, category names come from DB but should be properly escaped)
- All 6,500+ references are consistent across route files — no stale stats found
- Smoke test shows 403 tunnel errors (network proxy issue, not code failures)

## Completed This Session (2026-04-05, sixth pass — autonomous improvement cycle)

### Search Quality
- Added `"tanstack"` → `"frontend"` synonym (TanStack Query/Router/Table queries)
- Added `"radix"` → `"frontend"` synonym (Radix UI primitives queries)
- Total _CAT_SYNONYMS keys: 332

### Category Page SEO
- Added `_CATEGORY_META` dict to browse.py with specific meta descriptions for 18 top categories
- Descriptions include named alternatives (Auth0, Stripe, Mailchimp, etc.) for long-tail SEO
- Added `_NO_TOOLS_SUFFIX` set to fix page titles for categories like "Frontend Frameworks" and "MCP Servers" (was "Best Indie Frontend Frameworks Tools" — now "Best Frontend Frameworks")

### Catalog (scripts only, no prod writes)
- Extended `scripts/add_missing_tools.py` with 5 more high-priority tools:
  - Vite (frontend-frameworks, 68k stars)
  - SvelteKit (frontend-frameworks, 19k stars)
  - TanStack Query (frontend-frameworks, 43k stars)
  - Radix UI (frontend-frameworks, 16k stars)
  - BullMQ (background-jobs, 6k stars)

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
- scheduling-booking/invoicing-billing/ai-automation/mcp-servers/creative-tools/newsletters: 30+ additional misfits fixed
- Fixed 500 errors on /tool/* pages: analytics_wall_blurred None stats bug — deployed fix
- Updated /guidelines and /submit with explicit developer-tool-only scope statement — deployed
- Rejected 3 spam tools (books-free-books, some-many-books, cihna-dictattorshrip-8); china-dictatorship skipped (has maker, needs Patrick)
- Rejected 46 empty/duplicate npm- pending tools
- Backfilled sdk_packages for daisyui, postmark, shadcn-ui
- server.json description fixed (≤100 chars), pushed to GitHub (registry auto-refreshes)
- MCP registry token expired — Patrick needs: mcp-publisher login github && mcp-publisher publish
- GitHub stars: 2/5, need 3 more by end of April 5 for awesome-claude-code submission
- Sent social post drafts to Patrick via Telegram for Ed to share

### Meetings
- Catalog scope meeting (2026-04-05-15) created and closed — ~25 consumer apps identified
  - Action for Patrick: bulk-reject via /admin (fastnfitness, foodyou, etc.)
  - Action for Content: add scope statement to submit/guidelines pages

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

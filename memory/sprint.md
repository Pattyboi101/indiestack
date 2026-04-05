# Sprint — Current

Last updated: 2026-04-05 (autonomous loop run 2)

## Status: Active

## Completed This Session (2026-04-05 — Loop Run 2)

### Search Quality (db.py _CAT_SYNONYMS)
- Removed stale duplicate entries: `cache`/`caching`/`redis` → `database` (overridden later by caching section — dead code)
- Removed duplicate `hosting`/`deployment`/`deploy` block; consolidated `serverless` into main devops block
- Removed orphaned comment "Caching → moved to dedicated section"
- Added IaC synonyms: `terraform` → devops, `pulumi` → devops, `ansible` → devops
- Added A/B testing: `experiment`/`experiments`/`ab` → feature (Feature Flags category)
- Added frontend build tools: `solid` → frontend (SolidJS alt form), `qwik` → frontend, `swc` → frontend, `babel` → frontend

### Catalog Script (scripts/add_missing_tools.py)
- Added 8 more tools: Next.js, Vite, Remix, Astro, SolidJS, Qwik, TanStack Query, SWC
- All check slug before inserting — safe to re-run on production

### Pricing Audit (critical)
- Fixed $49 references in: `.orchestra/ceo/CLAUDE.md`, `.orchestra/departments/ceo/CLAUDE.md`, `.orchestra/SYSTEM-OVERVIEW.md` (3 instances)
- Confirmed `src/indiestack/routes/pricing.py` already has correct $19/mo in all 3 places
- Corrected stale backend memory note that claimed $19→$49 change was correct (it was wrong and was already reverted)

## Completed This Session (2026-04-05 — Loop Run 1)

### Search Quality
- Verified all required `_CAT_SYNONYMS` mappings are present:
  - `state` → `frontend` (covers "state management")
  - `bundler` → `frontend` (covers "bundler" queries)
  - `realtime` → `api` (covers realtime/websocket tools)
  - `vector` → `database` (covers "vector database" queries)
  - `rate` → `api` (covers "rate limiting" queries)
- Previously added: htmx, alpine, preact, lit, solidjs, stencil, ember, trpc, grpc mappings

### Catalog Maintenance
- `scripts/add_missing_tools.py` — script to insert 10 high-priority tools (React, Vue, Svelte, Angular, Zustand, Jotai, Webpack, esbuild, Upstash, Resend). Checks slug before inserting. Safe to re-run.
- `scripts/backfill_sdk_packages.py` — backfill SDK/install metadata for well-known tools
- `scripts/recategorise_dry_run.py` — dry-run analysis of developer-tools category (2,931 tools)

### Orchestra Briefings Updated (2026-04-05)
- Backend: developer-tools category cleanup
- Frontend: SEO/copy improvements for new category pages
- MCP: (check `.orchestra/departments/mcp/briefing.md`)
- Content: (check `.orchestra/departments/content/briefing.md`)

## Current Priorities
1. Run `scripts/add_missing_tools.py` on production → rebuild FTS
2. Backend: recategorise misplaced tools out of developer-tools (2,931 → target ~1,500)
3. Frontend: verify new category pages (frontend-frameworks, caching, mcp-servers)
4. MCP server: check if any new synonyms need PyPI publish

## Known Blockers
- None currently

## Decisions
- Keep MCP server fully anonymous — no API key gating (see gotchas.md)
- Maker Pro price: $19/mo (canonical source: stripe.md)
- `_LIKE_STOP_WORDS` pattern used for FTS to avoid multi-word false matches

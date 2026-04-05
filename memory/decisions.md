# Key Decisions — IndieStack

Last updated: 2026-04-05

## Architecture

### No API key gating on MCP server (decided: early 2026)
The MCP server is fully anonymous and frictionless. We tried API key gating and it tanked adoption.
Soft nudges after repeated use are OK, but the anonymous experience must never degrade.

### SQLite over Postgres (decided: founding)
Fly.io persistent volumes + aiosqlite + WAL mode gives us enough performance for current scale.
No plans to migrate. WAL checkpoint after bulk writes.

### f-string templates, no Jinja2 (decided: founding)
Routes return HTMLResponse with Python f-strings. Keeps the stack simple and editor-navigable.
All user data sanitized with html.escape() before injection.

### Tool count phrasing: "6,500+" (decided: 2026-03-26)
After demoting npm-* tools, approved count is ~6,500+. Changed from 8,000+ references sitewide.
Always verify exact count from DB before publishing stats in copy.

## Pricing

### Maker Pro at $19/mo (decided: early 2026, locked in)
Not $49. The $49 figure appears in old planning docs. Canonical source: stripe.md.
Every agent touching pricing must verify against stripe.md first.

## Search Quality

### Primary-category boost (+100) in engagement scoring (decided: 2026-04-05)
Pure-category tools (e.g. actual auth tools) should outrank tools that are merely tagged with
a category name. Added +100 to category LIKE match in engagement expression.

### FTS5 stop words include 'integration', 'solution', 'alternative' (decided: early 2026)
Multi-word queries like "payments integration" should match payment tools, not scheduling apps
that mention "integration" in descriptions. Common filler words stripped before FTS query.

### _CAT_SYNONYMS for category boost routing (decided: early 2026)
Maps query terms to category name fragments for the +100 engagement boost.
For multi-word queries, the FIRST meaningful term with a known synonym is used.
E.g. "auth for nextjs" → first syn-term is "auth" → authentication category.

### Redis maps to caching (not database) (decided: 2026-04-05)
Redis is primarily a caching tool. The dedicated caching category now exists.
Earlier "database" entry overridden by later "caching" entry in _CAT_SYNONYMS.

## Distribution

### MCP server is primary distribution channel
10,000+ PyPI installs. Any feature that degrades MCP UX needs CEO approval.
MCP changes to presentation require PyPI publish; API/ranking changes deploy directly.

## Categories

### CDN tools live in DevOps & Infrastructure (decided: 2026-04-05)
CDN → devops mapping in _CAT_SYNONYMS. Cloudflare, BunnyCDN, Fastly are in DevOps.

### Frontend-Frameworks category includes bundlers + state management (decided: 2026-04-04)
Vite, Webpack, esbuild, Rollup all under frontend-frameworks.
Zustand, Jotai, MobX, Redux all under frontend-frameworks.
Helps agents find the right tool from broad queries like "bundler" or "state management".

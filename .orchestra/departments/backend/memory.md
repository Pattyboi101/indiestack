# Backend Memory

_You are a persistent agent. This file is your long-term knowledge base._
_Read this on startup. Update it after each task with what you learned._
_Focus on: file locations, patterns, gotchas, past decisions, domain knowledge._

---

## 2026-04-04 (pass 11 — latest)
Task: CDN gap, WebSocket fixes, stars refresh pass 10, caching category research.
- categories table uses 'name' column, NOT 'display_name' — caught via schema check
- LIKE '%cloudflare%' matched 11 non-CDN tools — always verify before blindly tagging; CDN tag was corrected in follow-up
- flyctl sftp doesn't overwrite: must `rm /tmp/file.py` via ssh console before re-uploading if script fails
- mongoose in DB is Cesanta's C embedded web server (cesanta/mongoose), NOT MongoDB ODM — correctly in developer-tools
- redis has github_stars=0 (wrong, should be 67k+) — stars refresh didn't catch it because tool is in DB with 0 and we query WHERE github_stars<100, but the fetch returned 0=0 so no update. Likely the github_url for redis points to wrong/private repo.
- txt-to-fasta has github_url='https://github.com/Pattyboi101/indiestack' — wrong repo attached to tool, data quality issue
- Caching category: 25 tools qualify, 7 in Database. RECOMMEND creating slug='caching'. Needs CEO approval. Plan at /tmp/caching-category-plan-local.txt
- BunnyCDN was already in DB as 'bunnycdn' — inserted by a previous pass. Always check before INSERT.

## 2026-04-04 23:00
Task: GitHub stars pass 6 (50 tools, 0 updates), taxonomy pass 7 (36 moves), category gap check, MCP misfire fixes.

Key findings:
- Stars pass 6: all 50 tools had unchanged star counts — DB is current for low-star non-npm tools
- Taxonomy: first explicit slug list missed all 100 tools (they weren't the same slugs from my prebuilt list). Had to run a query-first script to see actual slugs, then do targeted moves. Pattern: always query first, then move.
- Caching gap: NO dedicated Caching category exists. Redis/Dragonfly/KeyDB/Valkey/Upstash/Memcached all in Database. ~7-15 caching tools need a new category.
- Mongoose slug confusion: `mongoose` in DB is the cesanta C embedded web server (not MongoDB ODM). It had been miscategorised in Database. Moved to developer-tools + added websocket tag.
- CDN query still weak: PictShare and Webflow were ranking for 'cdn' — removed their cdn tags/descriptions. Only netlify and vercel got cdn tags. Real CDN tools (BunnyCDN, Fastly, Cloudflare) not in catalog or not tagged.
- Prisma MCP Server was ranking for 'orm' — stripped ORM signal from description, added mcp-server tag.
- graphql-engine (Hasura) was moved to api-tools this pass — MCP's report still showed it in developer-tools because their audit predated our taxonomy pass.
- FTS rebuild: always one at the END. Never between intermediate passes.

## 2026-04-04 22:30
Task: npm-* analysis (read-only), boilerplates gap analysis (read-only), github_stars pass 5 (writes).
Results:
- npm-* tools: 1,631 approved, avg views=0.02 vs 0.23 non-npm (ratio=0.087). Recommendation: BULK-DEMOTE. Almost no one views them; they're package mirror noise, not real tools. Top ones get exactly 1 view. Analysis at /tmp/npm-tools-analysis.txt.
- Boilerplates: No category exists. 47 approved tools have boilerplate/starter/template/scaffold tags, 34 of them sitting in Developer Tools. Recommendation: CREATE-CATEGORY (slug: boilerplates). Analysis at /tmp/boilerplates-analysis.txt.
- github_stars pass 5: 47/50 updated. Notable wins: jest was 0 → 45,336 (huge fix!), npm-crossws 0 → 668. 3 x 404s (url parsing truncation issue — github_url column may have truncated URLs for some npm-* entries). No FTS rebuild needed.
- URL parsing gotcha: npm-* tools had github_url entries like "https://github.com/thoov/mock-socke" (truncated) — caused 404. The DB may have a VARCHAR length limit causing URL truncation.

## 2026-04-04 22:00
Task: Taxonomy pass 6 (top-100 developer-tools) + generate /tmp/needs-review.csv.
Result:
- 12 tools moved total (8 via tag:cli/tag:llm in pass6a, 4 targeted in pass6b)
- Moves: txt-to-fasta/payme/workwork/miniserve/qrc/qrrs/clip-share-server → cli-tools; bentoml → ai-dev-tools; tailscale/netbird/airbyte → devops-infrastructure; centrifugo → message-queue
- FTS rebuilt, WAL checkpoint OK
- CRITICAL GOTCHA: Production has NO 'caching' category — dragonfly/keydb left in developer-tools
- Production category slugs to remember: monitoring-uptime, email-marketing, security-tools, forms-surveys, search-engine, analytics-metrics, headless-cms, message-queue, invoicing-billing, file-management (NOT monitoring/email/security/forms/search/analytics/cms/queue/billing/storage)
- Top 100 tools are now dominated by npm-* packages (~1,627 total) and boilerplates (~35) — future passes need bulk handling
- needs-review.csv generated at /tmp/needs-review.csv: 1,662 rows (1,627 npm-*, 35 boilerplates)
- npm-* tools recommendation: batch-reject or create npm-package status — they're auto-scraped npm registry entries

## 2026-04-04 21:15
Task: Taxonomy pass 5 (top-100 developer-tools reclassification) + pricing.py $19→$49 fix.
Result: 
- ~19 tools moved: testcafe/lighthouse/cupaloy/frisby → testing-tools, apache-airflow/meltano/go-feature-flag → devops, tolgee → localization, apprise → notifications, firecrawl-mcp-server/context7/repomix/fastgpt/cherry-studio → ai-dev-tools, shellcheck/npkill/gita → cli-tools, remotion → creative-tools, dnote → logging.
- awesome-cheatsheets moved to database by tag match (has 'database' tag) — REVERTED back to developer-tools. It's a cheatsheet collection. Don't trust tag-based category moves blindly.
- 97/100 tools were UNCERTAIN (npm-* packages, MCP servers, boilerplates). Next pass needs human-assisted review of npm-* slugs.
- pricing.py: NOTE — any $49 change was WRONG and was reverted. Canonical price is **$19/mo** per gotchas.md and stripe.md. vision.md had stale $49 copy that has since been corrected. Never change $19 to $49.
- Category slug for testing is 'testing-tools' not 'testing' — classic mistake.
- FTS rebuilt, WAL checkpoint, smoke test 54/54 passed.

## 2026-04-04 20:45
Task: Taxonomy cleanup at scale + github_stars fixes.
Result:

**Part 1 — Category reclassification ✅**
- Query column for sorting is `upvote_count` + `mcp_view_count` (NOT `view_count` or `upvotes`)
- Actual category slugs differ from generic names: use `monitoring-uptime`, `testing-tools`, `email-marketing`, `search-engine`, `headless-cms`, `analytics-metrics`, `file-management` — NOT `monitoring`, `testing`, `email`, `search`, `cms`, `analytics`, `storage`
- 59 tools moved from developer-tools to proper categories (DevOps: ~35, Database: 4, Auth: 3, Headless CMS: 3, Testing: 1, Search: 2, File Mgmt: 2, API: 2, Logging: 1, Payments: 1)
- FTS rebuilt OK, WAL checkpoint clean
- Edge cases to flag for S&QA review: `Awesome Cheatsheets` → Database (has db tag but is a cheatsheets repo), `Casper` → Headless CMS (Ghost theme), `ShipFast` → Payments (boilerplate starter), `Dagster` → Monitoring (data orchestrator moved for observability tag)

**Part 2 — github_stars ✅**
- `GITHUB_TOKEN` is available in production env — use `Authorization: Bearer $GITHUB_TOKEN` for authenticated GitHub API (5000 req/hr vs 60/hr unauthenticated)
- First two script runs hit rate limit because previous failed script still consumed 28+ unauthenticated requests
- 31 tools updated. Key numbers: supabase=100234, n8n=182440, strapi=71778, pocketbase=57348, meilisearch=56951, gitea=54734, coolify=52576, appwrite=55524, nocodb=62607, zod=42300, prisma=45657, sentry=43496, payload=41613, formbricks=12025, better-auth=27576
- Tools with already-correct stars (within 15%): hono=29736, next-auth=28171, payload=41613, trpc=39885, typesense=25521, vite=79555 (all fine)
- SFTP can't overwrite existing files — use different filenames for retries (e.g., _fix2.py, _fix3.py)

## 2026-04-04 (previous)

### Search Quality Fixes
- Removed 'search' from _FTS_STOP_WORDS — it was silently stripping "search" from _meaningful, undermining category boost calculation
- Changed engagement divisor 50 -> 40 — makes category/install signals 25% stronger vs raw BM25. Tools with correct category now more reliably beat keyword-stuffed unrelated tools.
- 'chat' -> 'chat' was a dead synonym mapping (no category has "chat" in name). Changed to 'customer' (Customer Support category).
- New synonyms: search->search, deploy/deployment/hosting->devops, cache/caching/redis->database

### Engagement Scoring Formula (db.py ~line 2700)
- Format: `rank - (engagement_expr / 40.0)` where rank is FTS5 BM25 (negative, lower = better)
- Max engagement: ~300 pts. Divided by 40 = ~7.5 BM25 units of boost.
- Category match = +180 pts. Install command = +10. Upvote = 2/vote. MCP views = 5/view.
- No install command = -40 penalty.
- If BM25 gap > 7.5 units, wrong-category tool can still win -- data quality is the real fix.

### Hard Search Problems (require data fixes, not code)
- "notifications": snooze (Laravel niche tool) beats Novu because snooze has 3x "notification" in short description = high BM25. Novu's description is thin on the exact word.
- "payments": Paddle beats Stripe for same reason.
- "forms": formzero beats Formbricks -- formzero description is dense with "form" mentions.
- Fix: improve descriptions of canonical tools (Novu, Stripe, Formbricks) to use key term more.

### Empty-Tool Sweep GOTCHA (2026-04-04)
- Tried to demote empty description+tag+upvote=0 tools -- accidentally caught legit tools (github-copilot, cline, amazon-q, mixpanel, etc.) which just lack DB descriptions.
- NEVER bulk-demote by empty fields alone. Only demote explicit slug list of confirmed junk.
- Junk tools safely demoted: search-plugins (qBittorrent plugin), email (placeholder slug), forms (placeholder slug).

### Category IDs (confirmed production)
- 18=developer-tools, 47=database, 50=devops-infrastructure, 51=security-tools
- 53=message-queue, 54=testing-tools, 56=cli-tools, 57=logging, 59=notifications, 60=background-jobs
- 2=email-marketing, 9=forms-surveys, 13=payments, 19=ai-automation

## 2026-04-04 (session 2)

### Slug gotcha: npm-prefixed tools
- uploadthing's slug in DB is `npm-uploadthing`, not `uploadthing`
- storybook's slug in DB is `npm-storybook`, not `storybook`
- Same pattern likely for other popular npm packages ingested from registry

### Category fixes applied (production)
- neon → Database (47), upstash → Database (47)
- inngest → Background Jobs (60) (was in AI & Automation 19)
- railway → DevOps (50), vercel → DevOps (50) (both were Developer Tools 18)
- mailpit → Testing Tools (54) (was Email Marketing 2)

### Description fixes applied (production)
- agenda (38→334), node-cron (44→315), cypress (68→330), bull (75→331)
- npm-uploadthing: replaced markdown link with real text
- npm-storybook: improved description

### Search quality: what data-only fixes can/can't solve
- notifications: Novu moved #5→#2 after expanding tags+description. snooze still #1 because 905 github_stars.
  The snooze issue is a github_stars data gap — snooze's stars are high, novu's 0 in DB.
- payments: Stripe already #2, already fixed by a330013 scoring. django-getpaid is #1 due to stars.
- forms: formbricks still #3 — 0 github_stars in DB vs formzero's 55. Formbricks real stars ~11k.
- ACTION NEEDED: github_stars for Novu, Formbricks, and Stripe need data refresh for accurate ranking.

### tools table: no view_count column
- Only view-like column is `mcp_view_count` and `social_mentions_count`
- Top 20 by mcp_view_count: all had install_command + desc≥80 chars — already in good shape

### Machine state gotcha
- Production machine was in "created" (stopped) state — had to `flyctl machine start` before SSH
- Machine starts quickly (5s) once started

### Production State After This Run
- 30 tools moved out of developer-tools to correct categories (traefik, nginx, caddy, mongoose, sequelize, knex, artillery, node-cron, bree, rq, celery, renovate, etc.)
- 26 install commands added (knex, chalk, ora, yargs, ink, docusaurus, vitepress, celery, rq, snyk, etc.)
- FTS rebuilt: YES

---

## 2026-04-01

### Production DB State (confirmed)
- Stripe: was `status='rejected'` — fixed to approved, cat=13 (Payments), tags+install added
- Mailgun/Sendgrid/Postmarks/Gumroad: had empty tags — fixed with email/payments tags + install commands
- Postmarks: slug is `postmarks` (not `postmark`), was in Developer Tools, fixed to Email Marketing (cat=2)
- tool_categories junction: Stripe added to Payments, Postmarks added to Email Marketing

### FTS5 Architecture (tools_fts)
- `CREATE VIRTUAL TABLE tools_fts USING fts5(name, tagline, description, tags, content='tools', content_rowid='id')`
- FTS triggers exist: `tools_ai`, `tools_ad`, `tools_au` — auto-update FTS on INSERT/DELETE/UPDATE
- To force full rebuild: `INSERT INTO tools_fts(tools_fts) VALUES('rebuild')`
- After data changes, always run rebuild + WAL checkpoint
- FTS query format: `sanitize_fts("email")` → `'"email"*'` (prefix query)
- BM25 rank is NEGATIVE in FTS5 — more negative = better match

### Search Ranking Formula (db.py:2308–2325)
- Exact name match: +150
- Name prefix match: +60
- Category match (tool_categories junction, NOT primary category_id): +100
- Tag match: +40
- upvote_count * 2
- mcp_view_count * 3
- min(github_stars, 5000) / 100.0
- ORDER BY: `rank - (engagement / 50.0)` — lower is better
- SaaS tools (Stripe, Resend) have 0 stars → ranked below OSS repos. MOAT brain fixing formula.

### Claim Flow (main.py:3457–3537)
- POST /api/claim → email domain match → verification email → GET /api/claim/verify/{token}
- No payment gate — claims are 100% free currently
- CTA copy explicitly says "Free, no commission, no fees"
- `create_verification_checkout` in payments.py exists (£29 verified badge) but NOT in claim flow

### Payments.py Summary
- `create_checkout_session`: marketplace tool sales (Stripe Connect, commission)
- `create_verification_checkout`: £29 verified badge (direct platform charge)
- `create_stack_checkout_session`: Vibe Stack bundles
- `create_connect_account` / `create_onboarding_link`: maker onboarding for selling
- No $99 claim fee — would need new `create_claim_checkout` + success handler

### WAL / SQLite Caching Note
- After committing data changes via SSH sqlite3, live API may serve stale results
- Root cause: app's SQLite page cache retains old state between requests
- Fix: `PRAGMA wal_checkpoint(TRUNCATE)` helps, but full propagation requires app restart/deploy
- Symptoms: DB simulation shows correct results, live API shows old results

## 2026-03-30

### CRITICAL: aiosqlite Row Access
- aiosqlite with row_factory=Row uses DICT access: `row["column_name"]`, NOT `row[0]`
- Always alias computed columns in SQL: `COUNT(*) as n`, then access `row["n"]`
- This caused TWO production bugs. Never use integer index on aiosqlite rows.



### SSH Script Pattern
- For complex Python string operations via fly SSH, inline `python3 -c "..."` breaks on escaping (em-dashes, backslashes, quotes).
- Better pattern: write script to `/tmp/fix.py` locally → `fly sftp shell -a indiestack` to upload → `fly ssh console -a indiestack -C 'python3 /tmp/fix.py'`



### MCP Registry server.json
- File: `server.json` at repo root (already existed at v1.9.0, updated to v1.11.1)
- Schema: `https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json`
- Name format for registry: `io.github.Pattyboi101/indiestack`
- Valid `runtimeHint` values (from constants.go): `npx`, `uvx`, `docker`, `dnx`
- Valid `registryType` values: `npm`, `pypi`, `oci`, `nuget`, `mcpb`
- IndieStack uses `runtimeHint: "uvx"` + `runtimeArguments` to encode `uvx --from indiestack indiestack-mcp`
- Argument objects: `type: "named"` (needs `name` field) or `type: "positional"`. Use `value` for hardcoded values.
- Current MCP version: 1.11.1 (matches pyproject.toml)

## 2026-04-04 — Search quality fixes
- **Logto 'email' bug**: Logto had "email" in its tags (`authentication,authorization,email,identity,jwt`). This caused it to FTS-match "email" queries and show up #3. Fix: removed "email" from tags → now `authentication,authorization,identity,jwt,oidc,sso`.
- **laravel-stripe-webhooks 'payments' bug**: It was in the Payments category (id=13) + had "payments" in tags — giving it both the +180 category bonus AND tag FTS match. Fix: moved to API Tools (id=16) and removed "payments" from tags → now `stripe,webhooks,laravel,php,laravel-package`.
- **Duplicates**: btcpayserver (quality=38.7) and killbill (quality=48.1) both set to status='pending'. Stronger duplicates (btcpay-server quality=100, kill-bill quality=100) remain approved.
- **FTS rebuild**: Always rebuild after tag/category changes: `conn.execute("INSERT INTO tools_fts(tools_fts) VALUES(?)", ("rebuild",))` — NOT a string literal in SQL, use a param! `chr()` is not available in SQLite on production (Alpine).
- **tools table has no view_count column** — it's `mcp_view_count`. Always check PRAGMA table_info(tools) if unsure about columns.
- **SSH inline Python quoting**: For complex queries with FTS MATCH params containing quotes/stars, pipe as base64 or use heredoc approach. The `-C 'python3 -c "..."'` works for simple scripts.


## 2026-04-04 (category fix + logging synonym)
Task: Move misplaced tools from Developer Tools (5069 tools) to thin categories + review CAT_SYNONYMS.
Result:
- Step 1: 20 tools moved on production. 9 skipped (already correct). Categories: Testing(6), Security(8), DevOps(5), Logging(1). FTS rebuild OK.
- Step 2: logging/logs synonyms changed "monitoring" → "logging" since Logging is a separate category (id=57, name="Logging"). "logging" synonym previously boosted Monitoring & Uptime, not Logging. Fix in db.py, needs deploy.
- Confirmed: email sending + cron nodejs fixes from 16:21 session already in place — did NOT re-fix.
- tool_categories junction table is used for engagement scoring (180pt boost), NOT tools.category_id directly. Many tools already had correct tool_categories entries.
- LIKE '%logging%' matches "Logging" category name correctly.

## 2026-04-04 21:xx
Task: npm-* bulk demotion + Boilerplates category + CDN tag fixes.
Result:
- Task 1: 1631 npm-* tools demoted from approved→pending (largest single data change to date)
- Task 2: Created 'boilerplates' category (id=62, slug='boilerplates', name='Boilerplates & Starters'). Moved 32 tools from developer-tools using exact comma-delimited tag matching for: boilerplate, starter, template, scaffold.
- Task 3: cloudflare, bunny-net, jsdelivr, fastly, keycdn — NOT in the DB under those slugs (skip). PictShare/Webflow — 'cdn' not in their tags (no change needed). Inserted BunnyCDN (slug='bunnycdn', category=devops-infrastructure).
- FTS rebuilt successfully.
- GOTCHA: categories table uses 'name' column, NOT 'display_name' — script errored first run on this.

## 2026-04-04 — Taxonomy pass 12
Task: Move frontend/API/security/analytics tools out of developer-tools (next 100 by mcp_view_count).
Result:
- 28 tools moved total (2 in v1 for design-creative, 26 in v2 for multiple categories)
- security-tools: 9 (ssl checkers, port scanners, ovpm, ctitool, envie)
- database: 4 (podil, migrator, sqlitebiter, sql-backup)
- api-tools: 3 (stencil/schema-registry, graphqlviz, craftql)
- ai-dev-tools: 3 (sourcery, gac, diffsense)
- media-server: 2 (podcastgenerator, screaming-liquid-tiger)
- monitoring-uptime: 2 (ttfb, operational-co)
- boilerplates: 1 (play-nextjs)
- search-engine: 1 (perceive-search)
- ai-automation: 1 (airunner)
- UPDATE (2026-04-04 pass 13): 'frontend-frameworks' category NOW EXISTS (id=66) — created in pass 13. Contains: nextjs, vite, astro, lit, mantine, primevue, react-bootstrap, tachyons, marko, nuxtjs (10 tools total). Major slugs (react, vue, svelte, angular, remix, htmx etc.) are NOT in the catalog as standalone tools.
- GOTCHA: 'analytics' category does NOT exist — correct slug is 'analytics-metrics'
- 28% confident rate — at S&QA's 30% diminishing-returns threshold. Next pass may not be worthwhile.
- FTS rebuilt, WAL checkpointed.

## 2026-04-04 (pass 14 — frontend frameworks + migration targets)
- Migration table is `migration_paths` (NOT migration_events/signals). Columns: id, from_package, to_package, repo, commit_sha, committed_at, confidence, created_at
- Top 5 migration adoption targets (to_package): vitest(65), vite(36), jest(25), rollup(15), ava(11)
- categories table columns: id, name, slug, description, icon — NO 'display_name' column (gotcha: CLAUDE.md says display_name but it doesn't exist)
- sftp put fails if remote file already exists — use new filename each run
- Most well-known JS framework slugs (react, vue, svelte, angular, etc.) are NOT in the catalog. Only templates/starters exist for them.

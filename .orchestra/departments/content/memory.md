# Content Memory

_You are a persistent agent. This file is your long-term knowledge base._
_Read this on startup. Update it after each task with what you learned._
_Focus on: file locations, patterns, gotchas, past decisions, domain knowledge._

---

## About Page Audit — 2026-04-04
- No `/about` route existed — 404 despite being in sitemap. Fixed: added 301 redirect `/about` → `/what-is-indiestack` in what_is.py
- Removed `/about` from sitemap URL list in main.py (was a broken sitemap entry; `/what-is-indiestack` already present at priority 0.7)
- `what_is.py` is the "about" page — fully dynamic stats, no hardcoded numbers, story is accurate
- All "8,000+" refs swept — none found in routes (previous passes cleaned all)
- "$49" only appears in changelog.py as a historical fix entry — correct, no change needed
- Side flag: `/terms`, `/privacy`, `/faq` also in sitemap with no handlers — same problem, outside current scope

## data_product.py (/data route) — 2026-04-04
- Route: `/data` (NOT `/data-product`)
- Target: tool maker marketing teams at $299/mo (separate from Maker Pro at $19/mo)
- Pricing on this page: Free (50q/day), Pro $299/mo, Enterprise custom — all separate from stripe.md $19/mo Maker Pro
- Live stats pulled from DB: repos, migrations, combos, unique_paths — all pre-computed as _fmt variables
- Key fix: Added "What is Migration Intelligence?" section — was completely missing, critical for cold visitors
- Key copy lesson: For premium data products ($299+), explaining METHODOLOGY builds more trust than listing features

## Production DB Stats (as of 2026-03-30)
- 4,535 repos with verified combos
- 93,111 verified combos
- 422 migration paths

## Top Migration Paths (from production DB)
1. jest → vitest: 37 repos
2. bcrypt → bcryptjs: 18 repos
3. webpack → vite: 18 repos
4. mocha → vitest: 13 repos
5. mocha → jest: 12 repos
6. webpack → rollup: 12 repos
7. mocha → ava: 10 repos
8. cypress → @playwright/test: 7 repos
9. moment → dayjs: 6 repos
10. rollup → vite: 6 repos
11. @testing-library/react → jest: 5 repos
12. cypress → vitest: 5 repos
13. esbuild → vite: 5 repos
14. recoil → jotai: 5 repos
15. webpack → esbuild: 5 repos

## Build in Public Script
- Script: `scripts/build_in_public.py`
- Run: `python3 scripts/build_in_public.py`
- Output: `/tmp/build_in_public_drafts.md`
- No external deps. Uses subprocess for git, pathlib for files.
- Scores commits by type (feat=4, fix=3) + bonuses for user-facing files, data numbers, broad diffs
- Extracts Strategic Lessons and GOTCHA entries from playbook.md
- Drafts 3 posts: "Shipped", "Fixed/Lesson", "Week summary"
- Pat reviews and posts manually — script never posts

## Blog Post Written
- Title: "We scanned 4,500 GitHub repos. Here's what developers are actually migrating to."
- File: /tmp/blog_migration_findings.md
- Platform: Dev.to
- Tone: data journalism, no emojis, numbers-first
- CTA: indiestack.ai/migrations

## Ed's Outreach Playbook (2026-04-01)
File: .orchestra/departments/content/ed-outreach-plan.md
Contains: 3 Reddit templates (r/SideProject, r/webdev, r/selfhosted), 3 Discord servers (Anthropic, Cursor, Latent Space), install snippet, 5 Twitter DM targets (@tdinh_me, @marc_louvion, @levelsio, @theo, @shadcn), ops notes for Ed.
Key rule: don't mention paid tiers in cold outreach, don't batch DMs.

## README.md Rewrite (2026-04-01)
Drafted full rewrite of README.md — sent to Master for review before commit.
Key changes: uvx one-liner install leads, 3,100 tool count, no fly.dev URLs, removed self-hosting + project structure sections, added full 22-tool table, resources, prompts, v1.11+v1.12 changelog.
Current README.md is stale (880+, old pip install cmd, fly.dev URLs). Master has approved draft in principle.

## "Install in 30 seconds" Distribution Block (2026-04-01)
Short README-style block for Reddit/Discord/HN/GitHub. Hook: "Your AI agent searches 3,100 dev tools before writing code from scratch." Install: `claude mcp add indiestack -- uvx --from indiestack indiestack-mcp`. 3 example prompts. ~65 words. Reusable everywhere.

## Outreach Email Templates (2026-04-01)
Three cold email templates drafted for unclaimed tool listings. Stored in playbook/memory not a file — send direct to Master if needed again.
- Template 1: Data hook — "recommended {count} times this month"
- Template 2: Control angle — "you don't own your listing, gaps may exist"
- Template 3: Traffic proof — "{count} devs pointed here, you have no visibility"
Rules enforced: <80 words, from "Pat", one link, no upsell, no partnership language.
Placeholders: {tool_name}, {count}, {claim_url}

## mcpservers.org Submission (2026-04-02)
Prepared copy-pasteable submission fields for mcpservers.org/submit.
- Name: IndieStack
- Short desc: "Search 3,100+ developer tools from inside your AI agent — before writing infrastructure from scratch."
- Email: hello@indiestack.ai
- Category: Developer Tools / AI
- Tags: developer-tools, search, ai-agents, mcp, discovery, devtools
- Key install cmd: `claude mcp add indiestack -- uvx --from indiestack indiestack-mcp`

## Dev.to v1.12 Blog Post (2026-04-02)
Polished devto-v112-blog.md draft.
- New title: "I built an MCP server so AI agents stop rewriting auth from scratch — it just hit 10,000 installs"
- Added 10,000 installs milestone to opening paragraph
- Changed "prioritize" → "prioritise" (Patrick's UK English)
- Kept Patrick's casual, direct voice — no preamble, numbers up front
- Draft file: .orchestra/departments/content/devto-v112-blog.md (original unchanged — polished version sent to Master)

## SEO Audit Completed (2026-04-04)
Files changed: components.py, landing.py, explore.py, tool.py

### What was fixed:
- **components.py page_shell**: Added `og:site_name` tag. Improved default desc fallback from 70 chars ("Discover developer tools...") to 150 chars (mentions AI coding agents + 8,000+ tools).
- **landing.py**: Desc extended from 134 → 156 chars by appending " — 8,000+ tools indexed."
- **explore.py**: Title extended from 38 → 55 chars ("Explore 8,000+ Developer Tools by Category — IndieStack"). Desc from 120 → 156 chars.
- **tool.py**: Meta desc changed from raw tagline only (40-80 chars) to tagline + category context suffix, capped at 160 chars with ellipsis truncation on the full enriched string.

### Patterns learned:
- page_shell strips " | IndieStack" and " — IndieStack" from title to avoid duplication — always pass title WITH one of these suffixes; it strips cleanly.
- `og:url` in page_shell is only included if canonical is passed — landing/explore/tool all pass canonical so ✅.
- Tool detail pages: `tagline` var (line 85) is already html.escape()'d. page_shell also escapes its `description` param — double-escaping exists for tool taglines but doesn't break simple ASCII taglines. Don't pass pre-escaped content as `description`.
- For tool.py description enrichment, use `tool.get('tagline')` (raw) not the `tagline` variable (pre-escaped).
- `og:site_name` was missing entirely — now added to page_shell, applies to all pages.
- `twitter:site` was not added (no handle known in codebase).

## Copy Accuracy Audit (2026-04-04)
Files reviewed: pricing.py, submit.py

### Pricing page — all clear
- "$49/mo" ✓ matches vision.md
- "8,000+" ✓ DB shows 8,195 approved tools (queried via fly ssh)
- "Unlimited MCP searches / API queries" — unchecked but no evidence of rate limits for anon users
- Features listed (agent citation analytics, search query data, verified badge, etc.) match vision.md Pro features

### Submit page — 1 issue fixed
- **FIXED**: "note from us" paragraph claimed "Games, utilities, newsletters, dev tools — anything you've built" — directly contradicts vision.md (dev tools only, no games/newsletters).
  - Changed to: "Libraries, CLIs, APIs, SaaS tools — if developers use it, we want it in here."
- "Pick of the Week" claim ✓ confirmed real (landing.py references `_hero_tool_name` as this week's pick)
- "we'll review within 24 hours" — unverifiable from codebase, flagged but not changed (Patrick's call)
- `tool_count` is live from DB — 8,195 — shows accurately as "8195+" on the page

### Gotcha learned:
- Submit page "note from us" was a long-standing broken promise. The page title ("Make Your Creation Discoverable by AI") is intentionally broad but body copy must stay in scope.

## Category Meta + High-Traffic Route Audit (2026-04-04)
Files changed: explore.py, analyze.py, gaps.py, compare.py

### explore.py — per-category meta descriptions added
- Was: single generic description for ALL category pages (including /explore?category=4)
- Now: `_CAT_META` dict at module level maps 10 category slugs to keyword-rich descriptions with `{count}` placeholder
- Dynamic logic at route bottom: if category filter active, look up category from `categories` list, get slug + tool_count from DB (already fetched), format the description
- Title also changes: `f"{_c_name} Tools — {_c_count}+ Options | IndieStack"` when category active
- Canonical set to `/explore?category={id}` when category active (helps Google understand category pages)
- Fallback (no category): original generic description + title unchanged
- Counts sourced from production API (verified 2026-04-04):
  authentication=265, payments=138, database=63, analytics-metrics=233, monitoring-uptime=245,
  email-marketing=133, devops-infrastructure=20, headless-cms=8, search-engine=12, testing-tools=16
- All descriptions verified under 160 chars including count values

### analyze.py — description improved + canonical added
- Was: 89 chars, no mention of IndieStack or AI agents, no canonical
- Now: 156-char desc mentioning IndieStack, freshness/compatibility/modernity keywords
- Added `canonical="/analyze"` — this generates og:url which was missing

### gaps.py — canonical added to main /gaps page
- Was: no canonical → no og:url in OG tags
- Now: `canonical="/gaps"` → og:url included

### compare.py — em dash fix + AI-agent mention
- Was: `--` double dashes in both seo_title and seo_desc (typography bug)
- Now: `—` em dashes, description mentions "AI-agent compatibility" as differentiator
- Length verified safe for typical tool names (tested: Plausible Analytics + Google Analytics 4 = 133 chars)

### Stale stats check
- updates.py: no stale stats (no hardcoded numbers)
- what_is.py: all stats from live DB queries, no hardcoded numbers ✓

### Patterns learned:
- Category pages in IndieStack use ID-based URLs (/explore?category=4), not slug-based — look up slug from `categories` list that's already fetched in the route
- page_shell only adds og:url when `canonical` is passed — pages without canonical lack og:url
- compare.py seo_desc has no length truncation — keep base template under 100 chars to safely accommodate two tool names

## updates.py + what_is.py Audit (2026-04-04)
Files reviewed: updates.py, what_is.py
Files changed: what_is.py only

### updates.py — all clear
- Copy is clean. Empty state link `/makers` is valid (maker.py registers `@router.get("/makers", ...)`).
- Meta desc: "Latest updates from indie makers on IndieStack." — functional, 54 chars.
- No stale stats (no hardcoded numbers).

### what_is.py — 3 issues fixed
1. **Removed unused `from html import escape` import** — escape is never called anywhere in the file.
2. **"What Belongs Here" section overhauled** — critical accuracy fix:
   - Old heading: "If someone made it, it belongs here" → **New: "Developer tools, every shape and size"**
   - Old copy: "The only constraint is 'indie-built.' Not 'developer tool.'" — directly contradicted vision.md
   - New copy: "If developers use it to build, it belongs here — from auth libraries and search engines to payments, databases, and developer education."
   - Replaced 3 example cards that showed excluded categories:
     - Games/Veloren → **Databases/PocketBase**
     - Newsletters/Buttondown → **Email API/Resend**
     - Creative Tools/Penpot → **Search/Meilisearch**
3. **"Just ask" example updated** — "What indie games are built in Rust?" (wrong scope) → "What's a good open-source search engine for Next.js?"

### what_is.py is mostly good
- All stats (tool_count, cat_count, code_count, saas_count, ai_recs) are dynamic from DB — safe.
- JSON-LD valid, uses dynamic tool_count.
- Meta description uses f-string with live tool_count — under 160 chars.
- "VS Code Copilot" in "Works everywhere" card — MCP is supported, claim is accurate.
- DB: 8,195 tools, 40 categories (queried 2026-04-04).

### Pattern learned:
- what_is.py used to pitch IndieStack as "anything indie" (not just dev tools). This theme may recur — always cross-check copy scope against vision.md (dev tools only).
- Same issue was found in submit.py previously (fixed 2026-04-04). Pattern: enthusiastic broad copy creeps in, needs pruning.

## Stats/Copy Audit — landing.py, explore.py, updates.py (2026-04-04)
Files changed: explore.py, updates.py

### Production DB check (2026-04-04)
- 8,195 approved tools (up from 8,197 at earlier check — normal churn)
- 40 categories
- DB path: /data/indiestack.db

### Issues found and fixed:

**updates.py** (2 fixes):
1. Meta description was 48 chars ("Latest updates from indie makers on IndieStack.") — way too thin.
   - New: "See what indie makers are shipping — changelogs, launches, and updates from the IndieStack community. Follow the tools you care about as they evolve." (149 chars ✓)
2. Missing canonical tag — added `canonical="/updates"` to page_shell call.

**explore.py** (1 fix):
- Description claimed "verification status, and price" as active filters — but both `verified` and `price` are hardcoded to `""` in the route (disabled). This was a false claim.
   - Removed those two filter names. New desc: "Browse and filter 8,000+ developer tools by category, tag, type, and compatibility. Find the right auth, payments, analytics, or email tool for your stack." (161→159 chars ✓)

**landing.py** — no changes needed:
- `tool_count` is live from DB → accurate (8,195)
- `10,000+ installs` hardcoded but matches PyPI milestone noted in memory
- Meta description 156 chars ✓
- Canonical "/" ✓
- "847 repos migrated" in hero is illustrative demo UI copy, not a factual claim — OK.

### Pattern learned:
- Disabled UI filters (price, verified) can leave stale claims in meta descriptions. Always cross-check active query params against the description text.
- updates.py previously had no canonical — add to all pages that have a stable URL.

## Stat Audit + analyze.py Copy Rewrite (2026-04-04)
Files changed: landing.py, analyze.py

### landing.py stat audit
- tool_count — always dynamic from DB ✅
- 10,000+ installs — PyPI actual: 10,945 with mirrors (checked pypistats.org) ✅
- ai_recs — dynamic ✅
- **"847 repos migrated to it last month" (line 204) — WAS a fake hardcoded number. NOW fixed: "real GitHub data shows developers moving toward it"**
  - Previous memory incorrectly said this was "OK as illustrative copy" — it was a real number claim in fictional dialogue. Removed.
- NOTE: `sqlite3` is NOT in PATH on Fly machines (fly ssh console will fail with "executable file not found"). Use production API instead: curl -sL "https://indiestack.ai/api/categories" gives tool counts.
- Actual tool count 2026-04-04: 8,177 (from category tool_count sum via API)

### analyze.py copy rewrite for "check dependency health" organic traffic
1. h1: "Stack Health Check" → "Dependency Health Check" (matches search query)
2. Subtitle rewritten to explain output: 0–100 score, freshness per package, migration warnings, alternatives — "Free, no login"
3. Added 4-item "what you get" checkmarks row below form (0–100 health score / Freshness per package / Migration signals / Better alternatives)
4. Page title: "Stack Health Check | IndieStack" → "Dependency Health Check | IndieStack"
5. Meta desc: 158 chars, explains inputs + outputs + "Free, no login"

### Patterns learned:
- sqlite3 is NOT available on Fly SSH — use production API endpoints for stat verification
- The page_shell call for analyze.py already had canonical — no change needed there

## Patterns / Notes
- DB is at /data/indiestack.db on production — query via fly ssh console
- Migration data lives in `migration_paths` table: from_package, to_package, repo columns
- Verified combos in `verified_combos` table
- The master agent sent the exact SQL queries — use them as templates for future data pulls

## Sitemap Knowledge (2026-04-04)
- Sitemap is dynamically generated in main.py (NOT a route file) — lines ~1081-1204
- Had a CRITICAL bug: `LIMIT 5000` on approved tools query — was missing ~3,000+ tool pages. FIXED.
- Maker profiles also had `LIMIT 5000` — removed.
- robots.txt is also in main.py (~line 896), NOT a static file
- robots.txt already referenced sitemap — added auth route disallows (/login, /signup, etc.)
- Category pages use `/category/{slug}` route (browse.py), NOT `/explore/{cat}`
- /explore is a single discovery page; /category/{slug} is per-category browsing
- collections → all 301 redirect to /stacks (don't include in sitemap)
- Sitemap uses 1-hour cache (`_sitemap_cache` dict at top of main.py)
- Estimated total URLs post-fix: ~10,000–12,000 (well under 50k sitemap limit)
- Title accuracy matters: use real numbers (4,535 not "5,000") for data journalism credibility

## 2026-04-04 — Collections, Plugins, Changelog, Updates audit
- collections.py: pure 301 redirects (/collections, /collection/{slug}) → /stacks. No HTML, no SEO work needed.
- plugins.py: real content page (MCP servers, extensions, skills from DB). Had good title/description but missing canonical. Added canonical="/plugins".
- changelog.py: was STALE — last entry 2026-03-13 when today is 2026-04-04. Added 2 new entries:
  - 2026-04-04: MCP v1.15.0 (get_migration_data), v1.14.0, claim-to-Pro, sitemap fix, $19 pricing fix, search quality, SEO pass
  - 2026-04-03: AI Recs badge + outreach table sorting
  - Also added canonical="/changelog"
- updates.py: dynamic maker feed from DB. Title/description fine. No changes needed.
- Changelog maintenance pattern: git log --format="%ad %s" --date=short to find what shipped, group into meaningful entries by date, add at TOP of CHANGELOG list.
- Gotcha: changelog.py uses hardcoded CHANGELOG list (not DB). Must be updated manually after each significant ship day.
- page_shell strips " | IndieStack" or " — IndieStack" suffix then re-appends " — IndieStack". Pass clean title or with suffix — both work.

## 2026-04-04 — submit.py audit
- **submit.py** — "What You Get" section had NO Maker Pro mention. Classic missed conversion. Added horizontal callout with $19/mo badge + "See plans →" link. Always check submit, pricing, and landing pages for Maker Pro consistency.
- Hero H1 was "Make Your Creation Discoverable by AI" — changed to "Get Your Tool in Front of AI Coding Agents". More specific, action-oriented, names the destination.
- The 10,000+ MCP installs figure is the best credibility signal for tool maker pages. Always surface it on submit, pricing, what_is pages.
- "creation" is the intentional word choice for submissions page (covers plugins/extensions/MCPs not just "tools") — don't wholesale replace it, but "tool" is fine in the H1/meta.

## 2026-04-04 — Migration Intelligence outreach template
Task: Draft Migration Intelligence outreach email for DevRel leads at tools gaining migration momentum.
Result: Template saved to /tmp/migration-intel-outreach.txt.
- monetisation.md shows $299/mo for Migration Intelligence tier (not $99/mo as task brief stated — FLAG to Patrick before sending)
- Real data hook: Vitest has 38 repos migrated FROM jest, 13 from mocha (via get_migration_data("vitest"))
- Email body ~90 words (well under 150 limit)
- Method credibility: "We mine GitHub package.json diffs" is stronger than "we track migrations" — leads with proof
- Before each send: run get_migration_data(package) via MCP to pull fresh numbers per tool

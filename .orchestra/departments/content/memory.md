# Content Memory

_You are a persistent agent. This file is your long-term knowledge base._
_Read this on startup. Update it after each task with what you learned._
_Focus on: file locations, patterns, gotchas, past decisions, domain knowledge._

---

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

## Patterns / Notes
- DB is at /data/indiestack.db on production — query via fly ssh console
- Migration data lives in `migration_paths` table: from_package, to_package, repo columns
- Verified combos in `verified_combos` table
- The master agent sent the exact SQL queries — use them as templates for future data pulls
- Title accuracy matters: use real numbers (4,535 not "5,000") for data journalism credibility

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

## Patterns / Notes
- DB is at /data/indiestack.db on production — query via fly ssh console
- Migration data lives in `migration_paths` table: from_package, to_package, repo columns
- Verified combos in `verified_combos` table
- The master agent sent the exact SQL queries — use them as templates for future data pulls
- Title accuracy matters: use real numbers (4,535 not "5,000") for data journalism credibility

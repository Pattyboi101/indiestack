# Briefing — 2026-04-05

## Task
Developer Tools category cleanup — reduce from 2,931. Find and move misplaced tools.

**Step 1 — Analysis (read only, no DB writes):**
Query production DB via SSH for tools in developer-tools that have tags suggesting better categories:
- Tags containing: `mobile`, `android`, `ios`, `react-native` → there's no Mobile category, use AI Dev Tools or leave
- Tags containing: `security`, `pentest`, `vulnerability` → Security Tools category
- Tags containing: `cms`, `headless-cms`, `content-management` → Headless CMS (slug: headless-cms)
- Tools whose name starts with "Scaffold ", "Generate ", "Create " that aren't in boilerplates

Use SSH file-upload pattern: write .py script to /tmp, sftp put, run via flyctl ssh console.

**Step 2 — Apply moves (DB write, file-upload pattern):**
For any clear moves from Step 1, write an apply script, sftp it up, and run it.
Run FTS rebuild after: `INSERT INTO tools_fts(tools_fts) VALUES('rebuild')` with `PRAGMA busy_timeout=60000`.

## Constraints
- Use file-upload SSH pattern for ALL production DB writes (no inline python3 -c)
- Do NOT move tools that are ambiguous — only move when category is clearly wrong
- Do NOT use LIKE '%orm%' — substring matches 'platform', 'transform', etc.
- After FTS rebuild, verify with: curl https://indiestack.ai/api/tools/search?q=security&limit=3

## Meeting Task — 2026-04-05 (MCP Growth & Maker Pro)
- [ ] Query production DB: how many unique tools have >10 agent citations this month? (SELECT tool_slug, COUNT(*) as n FROM agent_actions WHERE action='cite' AND created_at > datetime('now','-30 days') GROUP BY tool_slug HAVING n>10)
- [ ] Add `maker_weekly_citations` view to DB for fast maker dashboard queries
- [ ] Verify maker claim flow end-to-end (can a maker claim their tool and see analytics?)

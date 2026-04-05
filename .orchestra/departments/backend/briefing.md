# Briefing — 2026-04-05

## Priority Tasks

**Task 1 — Citation analytics (HIGHEST priority, blocks Maker Pro launch):**
Query production DB for agent citation data to validate Maker Pro value prop:
```sql
SELECT tool_slug, COUNT(*) as n FROM agent_actions
WHERE action='cite' AND created_at > datetime('now','-30 days')
GROUP BY tool_slug HAVING n>10 ORDER BY n DESC LIMIT 20;
```
Report: how many tools have >10 citations? Is the data rich enough to sell Maker Pro ($19/mo)?

**Task 2 — Maker Pro claim flow validation:**
Verify end-to-end: can a maker claim their tool and see citation analytics on the dashboard?
Check `/maker/dashboard` route and verify it queries agent_actions correctly.

**Task 3 — `maker_weekly_citations` view:**
Add a DB view for fast maker dashboard queries (avoids repeated GROUP BY on large table):
```sql
CREATE VIEW IF NOT EXISTS maker_weekly_citations AS
  SELECT tool_slug, COUNT(*) as citations_7d FROM agent_actions
  WHERE action='cite' AND created_at > datetime('now','-7 days')
  GROUP BY tool_slug;
```
Use SSH file-upload pattern to apply on production, then update any dashboard queries to use the view.

## Completed Tasks
- [x] Developer Tools category cleanup — ~500+ tools re-categorized across 15+ categories (fifth pass)
- [x] Fixed 500 errors on /tool/* pages (analytics_wall_blurred None stats bug)

## Constraints
- Use file-upload SSH pattern for ALL production DB writes (no inline python3 -c)
- Do NOT use LIKE '%orm%' — substring matches 'platform', 'transform', etc.
- After FTS rebuild, verify with: curl https://indiestack.ai/api/tools/search?q=security&limit=3
- aiosqlite row access is DICT-based: row["col_name"] not row[0]

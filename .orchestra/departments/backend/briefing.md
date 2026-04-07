# Briefing — 2026-04-05

## Priority Tasks

**Task 1 — Citation analytics (HIGHEST priority, blocks Maker Pro launch):**
NOTE: agent_actions has 0 cite records. Citation data is in agent_citations table.
Correct query (verified Apr 8):
```sql
SELECT t.name, t.slug, COUNT(*) as n FROM agent_citations ac
JOIN tools t ON t.id = ac.tool_id
WHERE ac.created_at > datetime('now','-30 days')
GROUP BY ac.tool_id ORDER BY n DESC LIMIT 20;
```
Result: 15 tools with citations in 30d. Top: Cloudinary (27), Next Auth (26), zauth (25),
Vaultwarden (24), Supabase (21). Data is rich enough for Maker Pro — these are real
"appeared in MCP agent search results" signals (not explicit recommendations).
maker_weekly_citations view already exists on production. [DONE — data confirmed Apr 8]

**Task 2 — Maker Pro claim flow validation:**
Verify end-to-end: can a maker claim their tool and see citation analytics on the dashboard?
Check `/maker/dashboard` route and verify it queries agent_actions correctly.

**Task 3 — `maker_weekly_citations` view:**
[DONE — view already exists on production, confirmed Apr 8]
Note: view queries agent_actions but citation data is actually in agent_citations.
If view is used by dashboard, verify it queries the right table.

## Completed Tasks (Apr 8-9 overnight)
- [x] Fixed bug: /api/agent/outcome now calls backfill_mcp_adoption with session_id — outcome tagging validated end-to-end (adopted state correctly propagates to mcp_query_outcomes)
- [x] Added synonym mappings: secret/env→security, gateway→payments (deployed v703)
- [x] Catalog additions: 60+ tools added to production DB overnight (IDs 9252-9310)
- [x] Load test outcome tagging — VALIDATED Apr 9: session=test-hanko shows adopted=hanko correctly

## Completed Tasks (Previous)
- [x] Developer Tools category cleanup — ~500+ tools re-categorized across 15+ categories (fifth pass)
- [x] Fixed 500 errors on /tool/* pages (analytics_wall_blurred None stats bug)

## Meeting Task — 2026-04-07 (DSP Outreach Stress Test)
- [x] Fix log_search() to correctly tag source='mcp' vs source='api' — committed 9e3a402, live in v698 | Done Apr 8
- [x] Update data/gap-queries-2026-04.json: correct denominator already in file (2,662 / 143 / 5.4%) | Done Apr 8

## Meeting Task — 2026-04-07 (Future Models + Anthropic Pitch)
- [x] Deploy mcp_sessions + mcp_query_outcomes schema migration (see meeting file for full schema) | Done Apr 7
- [x] Wire session_id optional param into find_tools + get_tool_details API endpoints | Done Apr 7
- [x] Extend /api/quality: add tokens_saved_7d, adoption_rate_7d, gap_rate_7d, top_gap_queries, session_count_7d | Done Apr 7
- [ ] Load test + validate outcome tagging (adopted/gap/bounce/unknown) is capturing correctly | By: Apr 10
- [ ] Confirm Postgres migration feasibility + reversibility (no downtime surprises) | By: Apr 15 — BLOCKING DevOps
- [ ] Build session-aware result weighting (down-weight already-seen tools, up-weight complementary) | By: Apr 21
- [ ] Publish live token-waste counter on site (uses adoption data from tracking) | By: Apr 14
- CRITICAL: Do NOT migrate Postgres in week 2 (Apr 15-21). Migration moves to week 3 at earliest.

## Constraints
- Use file-upload SSH pattern for ALL production DB writes (no inline python3 -c)
- Do NOT use LIKE '%orm%' — substring matches 'platform', 'transform', etc.
- After FTS rebuild, verify with: curl https://indiestack.ai/api/tools/search?q=security&limit=3
- aiosqlite row access is DICT-based: row["col_name"] not row[0]

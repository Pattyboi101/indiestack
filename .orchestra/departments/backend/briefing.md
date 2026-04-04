# Briefing — 2026-04-04 15:04

## Task
Data quality pass ONLY. Run queries against the LOCAL database to find: (A) top 20 approved tools with zero tags — suggest and apply appropriate tags based on name/description/category, (B) tools with obviously wrong categories — fix the most egregious mismatches. IMPORTANT: Do NOT use LIKE '%keyword%' for category matching — it catches substrings (gotcha). Use explicit slug lists or exact word matching. After all local DB changes, rebuild FTS: INSERT INTO tools_fts(tools_fts) VALUES('rebuild'). Note: these are LOCAL changes only — they'll need a separate production data fix later via SSH with absolute paths.

## S&QA Conditions
- Dashboard work goes to frontend ONLY — backend must not touch dashboard.py
- Backend must not use LIKE '%keyword%' for finding miscategorized tools — use explicit checks or tag-based matching
- Backend data quality changes are LOCAL only this run — production DB fixes need a separate SSH step with FTS rebuild
- Frontend should read vision.md and pricing context before implementing upgrade CTAs — the nudge must be soft, not a gate

## Risk Flags
- Original plan had two agents editing dashboard.py — guaranteed conflict
- Backend LIKE substring matching gotcha is relevant for finding miscategorized tools
- If backend accidentally runs data changes on production without FTS rebuild, search serves stale results

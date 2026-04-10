# Directive: Investigate MCP Gap Rate Anomaly

**Priority:** High
**Department:** Backend
**Trigger:** Event reactor detected >15% MCP query gap rate

## Context

- **Gap rate:** {{gap_rate}}% of MCP queries returned 0 results
- **Gap count:** {{gap_count}} / {{total_queries}} queries
- **Detected at:** {{timestamp}}

## Tasks

1. SSH to prod and check the top zero-result queries:
   ```sql
   SELECT query, COUNT(*) as n FROM search_logs
   WHERE created_at > datetime('now', '-24 hours')
     AND source = 'mcp' AND result_count = 0
   GROUP BY query ORDER BY n DESC LIMIT 20;
   ```
2. For each top gap query, diagnose why:
   - Is the query gibberish/spam? → Ignore
   - Is the tool missing from the catalog? → Add to `scripts/add_missing_tools.py`
   - Is FTS not matching? → Check `_CAT_SYNONYMS`, `_FTS_STOP_WORDS`, `NEED_MAPPINGS` in db.py
   - Is the category mapping wrong? → Fix `_CAT_SYNONYMS`
3. After any db.py changes: run `python3 smoke_test.py` and commit
4. After any prod data changes: rebuild FTS index

## Constraints

- Verify fixes don't break existing good results (check the 13 test queries)
- Don't add programming language names to `_FRAMEWORK_QUERY_TERMS` (see gotchas.md)
- Stage specific files only

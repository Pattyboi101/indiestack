---
paths:
  - "src/indiestack/db.py"
  - "scripts/**/*.py"
---

# IndieStack — Database

## Engine
- aiosqlite exclusively. WAL mode enabled on connection.

## Query Patterns
- Parameterized queries always: `await db.execute("...WHERE x=?", (val,))`
- Never f-string user input into SQL
- Row objects are dict-like: `row['col']` not `row[0]`
- FTS5 for search — don't write custom Python string matching
- `BEGIN IMMEDIATE` for write transactions (upvotes, toggles)

## Schema Gotchas
- ALTER TABLE ADD COLUMN can't have UNIQUE — add column, then CREATE UNIQUE INDEX
- `category_slug` is on `categories` table, not `tools` — use JOIN

## Background Jobs
- `recompute_all_quality_scores()` runs every 4h via cron

## Ranking
- `quality_score DESC, github_stars DESC` (not recency)

## Key Mappings
- `NEED_MAPPINGS` dict in db.py maps 26 keywords to 25 categories with search terms + competitors
- `TECH_KEYWORDS` set (~80 keywords) for developer profile tech extraction

## Tables
30+ tables. Key tables: `tools`, `categories`, `users`, `search_logs`, `api_keys`, `subscriptions`, `tool_pairs`, `agent_actions`, `stack_upvotes`, `developer_profiles`

## Tool Metadata
- `source_type` column: `code` (GitHub/GitLab/Codeberg) vs `saas` — auto-detected on insert
- `frameworks_tested` column (CSV) — populated by enricher, used for tech stack filtering

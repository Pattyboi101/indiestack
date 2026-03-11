# Quality Score System — Design Document

**Goal:** A composite quality score on each tool (0–100) that feeds into search ranking, trending, and agent recommendations. Internal only — users never see the number.

**Architecture:** Precomputed `quality_score` column on tools table, recomputed daily via cron job.

---

## Data Model

New columns on `tools` table:
- `quality_score REAL DEFAULT 0.0` — composite score (0–100)
- `last_health_check TIMESTAMP` — when URL was last pinged
- `health_status TEXT DEFAULT 'unknown'` — `alive`, `dead`, `unknown`

Migration: `ALTER TABLE` in `db.py` startup, same pattern as existing migrations.

---

## Score Formula

```
quality_score = completeness * (1 + engagement_boost) * health * 100
```

### Completeness (0.0–1.0) — exists for every tool
- Description > 100 chars: +0.25
- Tags present: +0.15
- Maker claimed (maker_id set): +0.25
- Tagline > 20 chars: +0.10
- Source type correctly set (code/saas): +0.10
- Has integration snippets: +0.15

### Engagement Boost (0.0–1.0) — sparse but meaningful
- Upvotes: `min(upvotes / 10, 0.3)`
- MCP views: `min(mcp_view_count / 50, 0.3)`
- Reviews: `min(review_count / 3, 0.2)`
- Outbound clicks: `min(click_count / 100, 0.2)`

### Health (binary kill switch)
- URL returns 200 → 1.0
- URL dead for 7+ consecutive days → 0.0 (score goes to zero)
- Unknown (never checked) → 1.0 (benefit of doubt)

### Score Range
- Most tools today: 40–70 (completeness alone)
- Tools with engagement: 70–90
- Dead tools: 0

---

## Score Computation

### Function: `compute_quality_score(tool: dict) -> float`

In `db.py`. Takes a tool dict (with joined review_count and click_count), returns 0–100.

### Recompute Job: `recompute_all_quality_scores(db)`

1. Fetch all approved tools with LEFT JOINs for review counts and outbound click counts
2. Run each through `compute_quality_score()`
3. Batch UPDATE quality_score column

### Health Check Job: `run_health_checks(db)`

1. Fetch tools not checked in 24+ hours (or never checked), limit 100 per run
2. HTTP HEAD each URL with 10s timeout
3. Update `health_status` and `last_health_check`
4. If a tool has been `dead` for 7+ days, its health factor = 0.0

### Cron Trigger

`GET /admin/recompute-scores?key=<ADMIN_SECRET>` — runs health checks then recomputes all scores. Called daily by Fly cron or a scheduled process.

---

## Search Integration

### FTS5 Search (`search_tools()` in db.py)

Current: `ORDER BY bm25(tools_fts) LIMIT ?`

New: `ORDER BY bm25(tools_fts) - (t.quality_score / 50) LIMIT ?`

BM25 returns negative values (closer to 0 = better). Subtracting quality bonus makes high-quality tools rank higher. A tool with score 80 gets a -1.6 bonus.

### Trending (`get_trending_tools()`)

Current: `ORDER BY upvote_count DESC`

New: `ORDER BY quality_score DESC`

### Replaces Fallback

Current: `ORDER BY upvote_count DESC`

New: `ORDER BY quality_score DESC`

### MCP Server

No changes — `find_tools` calls the API which calls `search_tools()`. Better ranking flows through automatically.

---

## Files to Modify

1. `src/indiestack/db.py` — Migration, `compute_quality_score()`, `recompute_all_quality_scores()`, `run_health_checks()`, modify `search_tools()`, `get_trending_tools()`
2. `src/indiestack/main.py` — New `/admin/recompute-scores` endpoint
3. `src/indiestack/routes/admin.py` — Show quality score stats in admin overview (distribution, last recompute time)

---

## Future Extensions (not now)

- GitHub stars for code tools (needs GitHub API integration)
- Duplicate detection on submit (Levenshtein/FTS match)
- Auto-approve threshold (quality_score > X on resubmit)
- Community flagging (dead/spam/duplicate)
- Subcategories for better taxonomy
- Scoped llms-full.txt by category

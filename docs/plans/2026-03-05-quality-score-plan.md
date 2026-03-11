# Quality Score System — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a precomputed quality score (0–100) to every tool, recomputed daily via cron, feeding into FTS search ranking, trending, and replaces fallback ordering.

**Architecture:** Three new columns on `tools` table (`quality_score`, `last_health_check`, `health_status`). Pure `compute_quality_score()` function in `db.py`. Async `recompute_all_quality_scores()` and `run_health_checks()` jobs. Admin cron endpoint in `main.py`. Quality stats in admin overview.

**Tech Stack:** Python 3.10+, aiosqlite, httpx (already a dependency), FastAPI

**Design doc:** `docs/plans/2026-03-05-quality-score-design.md`

---

## Task 1: Database Migration — Add 3 New Columns

**Files:**
- Modify: `src/indiestack/db.py` — migration section (after line ~849, before `finally: await db.close()`)

**Step 1: Add migration code**

Insert this block after the `landing_position` migration (line 849) and before `finally:`:

```python
        # Migration: add quality score columns
        for col, ddl in [
            ("quality_score", "ALTER TABLE tools ADD COLUMN quality_score REAL DEFAULT 0.0"),
            ("last_health_check", "ALTER TABLE tools ADD COLUMN last_health_check TIMESTAMP"),
            ("health_status", "ALTER TABLE tools ADD COLUMN health_status TEXT DEFAULT 'unknown'"),
        ]:
            try:
                await db.execute(f"SELECT {col} FROM tools LIMIT 1")
            except Exception:
                await db.execute(ddl)
        await db.commit()
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read())"`
Expected: No output (clean parse)

**Step 3: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add quality_score, health_status, last_health_check columns to tools table"
```

---

## Task 2: `compute_quality_score()` Pure Function

**Files:**
- Modify: `src/indiestack/db.py` — add new function after `get_related_tools()` (around line 935), before the `# ── Search` section

**Step 1: Write the function**

Insert this block:

```python
# ── Quality Score ─────────────────────────────────────────────────────────

def compute_quality_score(tool: dict) -> float:
    """Compute quality score (0–100) for a tool using multiplicative formula.

    Formula: completeness * (1 + engagement_boost) * health * 100

    Args:
        tool: dict with tool columns plus joined 'review_count' and 'click_count'.
    Returns:
        float between 0.0 and 100.0
    """
    # ── Completeness (0.0–1.0) ──
    completeness = 0.0
    if len(str(tool.get('description') or '')) > 100:
        completeness += 0.25
    if str(tool.get('tags') or '').strip():
        completeness += 0.15
    if tool.get('maker_id') is not None:
        completeness += 0.25
    if len(str(tool.get('tagline') or '')) > 20:
        completeness += 0.10
    if str(tool.get('source_type') or '') in ('code', 'saas'):
        completeness += 0.10
    if str(tool.get('integration_python') or '').strip():
        completeness += 0.15

    # ── Engagement Boost (0.0–1.0) ──
    upvotes = int(tool.get('upvote_count') or 0)
    mcp_views = int(tool.get('mcp_view_count') or 0)
    review_count = int(tool.get('review_count') or 0)
    click_count = int(tool.get('click_count') or 0)

    engagement = 0.0
    engagement += min(upvotes / 10, 0.3)
    engagement += min(mcp_views / 50, 0.3)
    engagement += min(review_count / 3, 0.2)
    engagement += min(click_count / 100, 0.2)

    # ── Health (binary kill switch) ──
    health_status = str(tool.get('health_status') or 'unknown')
    if health_status == 'dead':
        # Check if dead for 7+ days — caller should set 'dead_days' if available
        dead_days = int(tool.get('dead_days') or 0)
        health = 0.0 if dead_days >= 7 else 1.0
    else:
        health = 1.0  # alive or unknown = benefit of the doubt

    score = completeness * (1 + engagement) * health * 100
    return round(min(score, 100.0), 2)
```

**Step 2: Quick smoke check**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read())"`
Expected: No output (clean parse)

**Step 3: Verify the function with inline test**

Run:
```bash
python3 -c "
import sys; sys.path.insert(0, 'src')
from indiestack.db import compute_quality_score

# Full tool: completeness = 1.0, no engagement, healthy
full = {'description': 'x' * 101, 'tags': 'a,b', 'maker_id': 1, 'tagline': 'x' * 21, 'source_type': 'code', 'integration_python': 'pip install x', 'upvote_count': 0, 'mcp_view_count': 0, 'review_count': 0, 'click_count': 0, 'health_status': 'alive'}
score = compute_quality_score(full)
assert 99 <= score <= 100, f'Full tool should be ~100, got {score}'

# Empty tool: completeness = 0.0
empty = {'description': '', 'tags': '', 'maker_id': None, 'tagline': '', 'source_type': '', 'integration_python': '', 'upvote_count': 0, 'mcp_view_count': 0, 'review_count': 0, 'click_count': 0, 'health_status': 'unknown'}
score = compute_quality_score(empty)
assert score == 0.0, f'Empty tool should be 0, got {score}'

# Dead tool (7+ days): score = 0
dead = {**full, 'health_status': 'dead', 'dead_days': 10}
score = compute_quality_score(dead)
assert score == 0.0, f'Dead tool should be 0, got {score}'

# Tool with engagement
engaged = {**full, 'upvote_count': 10, 'mcp_view_count': 50, 'review_count': 3, 'click_count': 100}
score = compute_quality_score(engaged)
assert score > 100 * 1.0, f'Engaged tool should be > 100 (capped), got {score}'
assert score == 100.0, f'Should cap at 100, got {score}'

print('All quality score tests passed')
"
```
Expected: `All quality score tests passed`

**Step 4: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add compute_quality_score() pure function with multiplicative formula"
```

---

## Task 3: `recompute_all_quality_scores()` Batch Job

**Files:**
- Modify: `src/indiestack/db.py` — add after `compute_quality_score()`

**Step 1: Write the async recompute function**

Insert immediately after `compute_quality_score()`:

```python
async def recompute_all_quality_scores(db: aiosqlite.Connection) -> dict:
    """Recompute quality_score for all approved tools.

    LEFT JOINs review counts and outbound click counts, then runs each tool
    through compute_quality_score() and batch-updates the column.

    Returns:
        dict with 'updated' count and 'avg_score'.
    """
    cursor = await db.execute("""
        SELECT t.*,
               COALESCE(r.review_count, 0) as review_count,
               COALESCE(oc.click_count, 0) as click_count,
               CASE
                   WHEN t.health_status = 'dead' THEN
                       CAST(julianday('now') - julianday(COALESCE(t.last_health_check, 'now')) AS INTEGER)
                   ELSE 0
               END as dead_days
        FROM tools t
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as review_count FROM reviews GROUP BY tool_id
        ) r ON r.tool_id = t.id
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as click_count FROM outbound_clicks GROUP BY tool_id
        ) oc ON oc.tool_id = t.id
        WHERE t.status = 'approved'
    """)
    tools = await cursor.fetchall()

    total_score = 0.0
    updates = []
    for tool in tools:
        score = compute_quality_score(dict(tool))
        updates.append((score, tool['id']))
        total_score += score

    # Batch update
    await db.executemany("UPDATE tools SET quality_score = ? WHERE id = ?", updates)
    await db.commit()

    count = len(updates)
    return {
        'updated': count,
        'avg_score': round(total_score / count, 1) if count else 0,
    }
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read())"`
Expected: No output

**Step 3: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add recompute_all_quality_scores() batch job"
```

---

## Task 4: `run_health_checks()` with httpx

**Files:**
- Modify: `src/indiestack/db.py` — add after `recompute_all_quality_scores()`

**Step 1: Write the health check function**

Insert after `recompute_all_quality_scores()`:

```python
async def run_health_checks(db: aiosqlite.Connection, batch_size: int = 100) -> dict:
    """HTTP HEAD check on tools not checked in 24+ hours.

    Args:
        db: Database connection
        batch_size: Max tools to check per run (default 100)

    Returns:
        dict with 'checked', 'alive', 'dead' counts.
    """
    import httpx

    cursor = await db.execute("""
        SELECT id, url FROM tools
        WHERE status = 'approved'
          AND (last_health_check IS NULL OR last_health_check < datetime('now', '-24 hours'))
        ORDER BY last_health_check ASC NULLS FIRST
        LIMIT ?
    """, (batch_size,))
    tools = await cursor.fetchall()

    alive = 0
    dead = 0
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        for tool in tools:
            status = 'dead'
            try:
                resp = await client.head(str(tool['url']))
                if resp.status_code < 400:
                    status = 'alive'
            except Exception:
                status = 'dead'

            if status == 'alive':
                alive += 1
            else:
                dead += 1

            await db.execute(
                "UPDATE tools SET health_status = ?, last_health_check = datetime('now') WHERE id = ?",
                (status, tool['id']),
            )

    await db.commit()
    return {'checked': len(tools), 'alive': alive, 'dead': dead}
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read())"`
Expected: No output

**Step 3: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add run_health_checks() with httpx HEAD requests"
```

---

## Task 5: Admin Cron Endpoint

**Files:**
- Modify: `src/indiestack/main.py` — add new endpoint after `/api/follow-through` (around line 2776)

**Step 1: Add the endpoint**

Insert after the `api_follow_through` function:

```python
@app.get("/admin/recompute-scores")
async def admin_recompute_scores(request: Request):
    """Cron endpoint: run health checks then recompute all quality scores.

    Protected by ADMIN_SECRET query param. Called daily by Fly cron.
    Example: GET /admin/recompute-scores?key=<ADMIN_SECRET>
    """
    import secrets as _secrets
    key = request.query_params.get("key", "")
    admin_key = _os.environ.get("ADMIN_SECRET", "")
    if not admin_key or not _secrets.compare_digest(key, admin_key):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    d = request.state.db
    health_result = await db.run_health_checks(d)
    score_result = await db.recompute_all_quality_scores(d)

    return JSONResponse({
        "ok": True,
        "health": health_result,
        "scores": score_result,
    })
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read())"`
Expected: No output

**Step 3: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: add /admin/recompute-scores cron endpoint"
```

---

## Task 6: Search Integration — Quality Boost in FTS, Trending, and Replaces

**Files:**
- Modify: `src/indiestack/db.py` — modify `search_tools()` (line ~965), `get_trending_tools()` (line ~891), and replaces fallback (line ~978)

**Step 1: Modify `search_tools()` ORDER BY**

In `search_tools()` around line 965, change:

```python
           ORDER BY rank LIMIT ?""",
```

to:

```python
           ORDER BY rank - (t.quality_score / 50.0) LIMIT ?""",
```

This subtracts a quality bonus from the BM25 rank. BM25 returns negative values (closer to 0 = better match), so subtracting makes high-quality tools rank higher. A tool with `quality_score` 80 gets a -1.6 boost.

**Step 2: Modify replaces fallback ORDER BY**

In the replaces fallback section around line 978, change:

```python
               ORDER BY t.upvote_count DESC
```

to:

```python
               ORDER BY t.quality_score DESC
```

**Step 3: Modify `get_trending_tools()` ORDER BY**

In `get_trending_tools()` around line 891, change:

```python
           ORDER BY rank_score DESC, t.created_at DESC LIMIT ?""",
```

to:

```python
           ORDER BY t.quality_score DESC, t.created_at DESC LIMIT ?""",
```

Also remove the now-unused `(t.upvote_count) as rank_score` alias from the SELECT. Change:

```python
                  (t.upvote_count) as rank_score,
```

to nothing (remove the line). Or if cleaner, just leave it — it won't hurt.

**Step 4: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read())"`
Expected: No output

**Step 5: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: integrate quality_score into FTS ranking, trending, and replaces fallback"
```

---

## Task 7: Admin Overview — Quality Score Stats

**Files:**
- Modify: `src/indiestack/routes/admin.py` — add quality stats to `render_overview()` right column, after the KPI grid (around line 353)

**Step 1: Add quality score stats query**

In `render_overview()`, before the `right_col = f"""` line (around line 351), add:

```python
    # Quality score distribution
    qs_cursor = await db.execute("""
        SELECT
            COUNT(CASE WHEN quality_score = 0 THEN 1 END) as dead,
            COUNT(CASE WHEN quality_score > 0 AND quality_score <= 40 THEN 1 END) as low,
            COUNT(CASE WHEN quality_score > 40 AND quality_score <= 70 THEN 1 END) as mid,
            COUNT(CASE WHEN quality_score > 70 THEN 1 END) as high,
            ROUND(AVG(quality_score), 1) as avg_score
        FROM tools WHERE status = 'approved'
    """)
    qs = await qs_cursor.fetchone()
    qs_html = f'''
    <div style="margin-top:12px;padding:12px;border-radius:8px;background:var(--surface-alt);">
        <h4 style="font-size:13px;color:var(--ink-muted);margin-bottom:8px;font-weight:600;">Quality Score</h4>
        <div style="font-size:12px;color:var(--ink);">
            Avg: <strong>{qs["avg_score"] or 0}</strong> &nbsp;|&nbsp;
            High ({">"}70): {qs["high"]} &nbsp;|&nbsp;
            Mid (40–70): {qs["mid"]} &nbsp;|&nbsp;
            Low (1–40): {qs["low"]} &nbsp;|&nbsp;
            Dead (0): {qs["dead"]}
        </div>
    </div>
    '''
```

**Step 2: Add `{qs_html}` to the right column template**

In the `right_col = f"""` block (around line 351), add `{qs_html}` after `{recent_html}`:

```python
    right_col = f"""
    <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:12px;">Today's Pulse</h3>
    {kpi_grid}
    {alerts_html}
    {recent_html}
    {qs_html}
    """
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin.py').read())"`
Expected: No output

**Step 4: Commit**

```bash
git add src/indiestack/routes/admin.py
git commit -m "feat: show quality score distribution in admin overview"
```

---

## Task 8: Smoke Test and Deploy

**Step 1: Run smoke test**

Run: `python3 smoke_test.py`
Expected: All 38 tests pass

**Step 2: Deploy to Fly**

Run: `cd /home/patty/indiestack && FLY_ACCESS_TOKEN=$(grep access_token ~/.fly/config.yml | awk '{print $2}') ~/.fly/bin/flyctl deploy --remote-only`

**Step 3: Trigger initial score computation**

After deploy, trigger the cron endpoint to seed scores:

Run: `curl "https://indiestack.fly.dev/admin/recompute-scores?key=$(grep ADMIN_SECRET /path/to/secrets)"`

Or use Fly SSH:
```bash
FLY_ACCESS_TOKEN=$(grep access_token ~/.fly/config.yml | awk '{print $2}') ~/.fly/bin/flyctl ssh console -a indiestack -C "curl -s 'http://localhost:8080/admin/recompute-scores?key=\$ADMIN_SECRET'"
```

**Step 4: Verify scores were computed**

Check admin overview at `https://indiestack.fly.dev/admin` — the Quality Score section should show a distribution.

**Step 5: Commit all remaining changes**

```bash
git add -A && git commit -m "feat: quality score system — complete implementation"
```

---

## Execution Summary

| Task | What | File(s) | Independent? |
|------|------|---------|-------------|
| 1 | Migration — 3 columns | db.py | Yes |
| 2 | `compute_quality_score()` | db.py | Yes |
| 3 | `recompute_all_quality_scores()` | db.py | Needs Task 2 |
| 4 | `run_health_checks()` | db.py | Yes |
| 5 | Admin cron endpoint | main.py | Needs Tasks 3, 4 |
| 6 | Search integration | db.py | Yes |
| 7 | Admin overview stats | admin.py | Yes |
| 8 | Smoke test + deploy | — | Needs all |

**Parallelizable:** Tasks 1, 2, 4, 6, 7 can run in parallel. Tasks 3, 5 are sequential. Task 8 is last.

**Recommended execution:** 3 parallel agents:
- Agent A: Tasks 1 + 2 + 3 (db.py — migration → score function → recompute job)
- Agent B: Tasks 4 + 6 (db.py — health checks → search integration)
- Agent C: Tasks 5 + 7 (main.py + admin.py — cron endpoint → admin stats)
Then Task 8 (smoke test + deploy) after all agents complete.

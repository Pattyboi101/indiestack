# Agent-Native Actions — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Give AI agents their own action vocabulary (recommend, shortlist, report_outcome, confirm_integration, submit_tool) on IndieStack, producing agent-native data that's more valuable than simulated human actions.

**Architecture:** Extend the existing API key system with scopes. Add `agent_actions` table. Create 5 API endpoints in `main.py`. Add 5 new MCP tools in `mcp_server.py`. Add dashboard section for agent activity. All agent actions go through the HTTP API (MCP server → API → database), same pattern as existing tools.

**Tech Stack:** Python/FastAPI, SQLite (aiosqlite), FastMCP, httpx

**Design doc:** `docs/plans/2026-03-13-agent-native-actions-design.md`

---

## Task 1: Database — `agent_actions` table + `scopes` column

**Files:**
- Modify: `src/indiestack/db.py`

**Context:** IndieStack uses SQLite with aiosqlite. The schema is defined at the top of `db.py` in `SCHEMA` string (line ~1-400). Migrations are done in `init_db()` (line ~847+) using try/except on ALTER TABLE — if the column exists, the ALTER fails silently. New tables can go in `SCHEMA` directly since `CREATE TABLE IF NOT EXISTS` is idempotent.

**Step 1: Add `agent_actions` table to SCHEMA**

In `src/indiestack/db.py`, find the end of the `SCHEMA` string (after the last `CREATE INDEX` statement, before the closing `"""`). Add:

```sql
CREATE TABLE IF NOT EXISTS agent_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('recommend','shortlist','report_outcome','confirm_integration','submit_tool')),
    tool_slug TEXT NOT NULL,
    tool_b_slug TEXT,
    success INTEGER,
    notes TEXT,
    query_context TEXT,
    created_at TIMESTAMP DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_agent_actions_key ON agent_actions(api_key_id);
CREATE INDEX IF NOT EXISTS idx_agent_actions_user ON agent_actions(user_id);
CREATE INDEX IF NOT EXISTS idx_agent_actions_tool ON agent_actions(tool_slug);
CREATE INDEX IF NOT EXISTS idx_agent_actions_action ON agent_actions(action);
CREATE INDEX IF NOT EXISTS idx_agent_actions_date ON agent_actions(created_at);
```

**Step 2: Add `scopes` migration to `init_db()`**

In the `init_db()` function (line ~847), add a migration block alongside the existing ones:

```python
# Migration: add scopes column to api_keys
try:
    await db.execute("SELECT scopes FROM api_keys LIMIT 1")
except Exception:
    await db.execute("ALTER TABLE api_keys ADD COLUMN scopes TEXT NOT NULL DEFAULT 'read'")
```

**Step 3: Add DB helper functions**

After the existing `log_api_usage` function (line ~5107), add:

```python
async def record_agent_action(
    db: aiosqlite.Connection,
    api_key_id: int,
    user_id: int,
    action: str,
    tool_slug: str,
    tool_b_slug: str | None = None,
    success: int | None = None,
    notes: str | None = None,
    query_context: str | None = None,
) -> int:
    """Record an agent action. Returns the action ID."""
    cursor = await db.execute(
        """INSERT INTO agent_actions
           (api_key_id, user_id, action, tool_slug, tool_b_slug, success, notes, query_context)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (api_key_id, user_id, action, tool_slug, tool_b_slug, success, notes, query_context),
    )
    await db.commit()
    return cursor.lastrowid


async def get_agent_action_counts(db: aiosqlite.Connection, user_id: int, days: int = 30) -> dict:
    """Get agent action counts for a user's dashboard."""
    cursor = await db.execute(
        """SELECT action, COUNT(*) as cnt
           FROM agent_actions
           WHERE user_id = ? AND created_at >= datetime('now', ?)
           GROUP BY action""",
        (user_id, f'-{days} days'),
    )
    rows = await cursor.fetchall()
    counts = {r['action']: r['cnt'] for r in rows}
    # Get success/fail breakdown for report_outcome
    cursor2 = await db.execute(
        """SELECT success, COUNT(*) as cnt
           FROM agent_actions
           WHERE user_id = ? AND action = 'report_outcome' AND created_at >= datetime('now', ?)
           GROUP BY success""",
        (user_id, f'-{days} days'),
    )
    outcome_rows = await cursor2.fetchall()
    counts['outcomes_success'] = sum(r['cnt'] for r in outcome_rows if r['success'] == 1)
    counts['outcomes_fail'] = sum(r['cnt'] for r in outcome_rows if r['success'] == 0)
    return counts


async def get_agent_action_log(db: aiosqlite.Connection, user_id: int, limit: int = 50) -> list[dict]:
    """Get recent agent actions for the activity log."""
    cursor = await db.execute(
        """SELECT action, tool_slug, tool_b_slug, success, notes, query_context, created_at
           FROM agent_actions
           WHERE user_id = ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (user_id, limit),
    )
    return [dict(r) for r in await cursor.fetchall()]


async def check_agent_action_exists(db: aiosqlite.Connection, user_id: int, action: str, tool_slug: str, tool_b_slug: str | None = None) -> bool:
    """Check if an agent action already exists (for dedup)."""
    if tool_b_slug:
        cursor = await db.execute(
            "SELECT 1 FROM agent_actions WHERE user_id = ? AND action = ? AND tool_slug = ? AND tool_b_slug = ?",
            (user_id, action, tool_slug, tool_b_slug),
        )
    else:
        cursor = await db.execute(
            "SELECT 1 FROM agent_actions WHERE user_id = ? AND action = ? AND tool_slug = ?",
            (user_id, action, tool_slug),
        )
    return await cursor.fetchone() is not None


async def check_agent_daily_action(db: aiosqlite.Connection, user_id: int, action: str, tool_slug: str) -> bool:
    """Check if this action was already taken today (for daily dedup)."""
    cursor = await db.execute(
        "SELECT 1 FROM agent_actions WHERE user_id = ? AND action = ? AND tool_slug = ? AND created_at >= date('now')",
        (user_id, action, tool_slug),
    )
    return await cursor.fetchone() is not None


async def count_agent_actions_today(db: aiosqlite.Connection, api_key_id: int, action: str) -> int:
    """Count how many times this action was taken today by this key."""
    cursor = await db.execute(
        "SELECT COUNT(*) FROM agent_actions WHERE api_key_id = ? AND action = ? AND created_at >= date('now')",
        (api_key_id, action),
    )
    row = await cursor.fetchone()
    return row[0] if row else 0


async def get_tool_recommendation_count(db: aiosqlite.Connection, tool_slug: str) -> int:
    """Get total recommendation count for a tool (across all agents)."""
    cursor = await db.execute(
        "SELECT COUNT(*) FROM agent_actions WHERE tool_slug = ? AND action = 'recommend'",
        (tool_slug,),
    )
    row = await cursor.fetchone()
    return row[0] if row else 0


async def get_tool_success_rate(db: aiosqlite.Connection, tool_slug: str) -> dict:
    """Get success rate for a tool from agent outcome reports."""
    cursor = await db.execute(
        "SELECT success, COUNT(*) as cnt FROM agent_actions WHERE tool_slug = ? AND action = 'report_outcome' GROUP BY success",
        (tool_slug,),
    )
    rows = await cursor.fetchall()
    success = sum(r['cnt'] for r in rows if r['success'] == 1)
    fail = sum(r['cnt'] for r in rows if r['success'] == 0)
    total = success + fail
    return {"success": success, "fail": fail, "total": total, "rate": round(success / total * 100) if total else 0}


async def update_api_key_scopes(db: aiosqlite.Connection, key_id: int, user_id: int, scopes: str) -> bool:
    """Update API key scopes. user_id check prevents cross-user modification."""
    if scopes not in ('read', 'read,write'):
        return False
    cursor = await db.execute(
        "UPDATE api_keys SET scopes = ? WHERE id = ? AND user_id = ?",
        (scopes, key_id, user_id),
    )
    await db.commit()
    return cursor.rowcount > 0
```

**Step 4: Update `get_api_key_by_key` to include scopes**

In the existing `get_api_key_by_key` function (line ~5072), update the SELECT to include `scopes`:

```python
# Change the SELECT from:
"SELECT ak.id, ak.key, ak.user_id, ak.name, ak.tier, ak.is_active, u.email "
# To:
"SELECT ak.id, ak.key, ak.user_id, ak.name, ak.tier, ak.scopes, ak.is_active, u.email "
```

**Step 5: Update `get_api_keys_for_user` to include scopes**

In the existing `get_api_keys_for_user` function (line ~5049), update the SELECT and result mapping to include `scopes`.

**Step 6: Verify**

```bash
cd /home/patty/indiestack && python3 -c "import py_compile; py_compile.compile('src/indiestack/db.py', doraise=True); print('OK')"
```

**Step 7: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add agent_actions table, scopes column, and DB helpers"
```

---

## Task 2: API Endpoints for Agent Actions

**Files:**
- Modify: `src/indiestack/main.py`

**Context:** `main.py` is the FastAPI app. API endpoints use `@app.post("/api/...")`. The existing API key is available on authenticated requests as `request.state.api_key` (a dict with `id`, `user_id`, `tier`, `scopes`, `email`). The key is parsed from `?key=` query param or `Authorization: Bearer` header in middleware (line ~670-707). Tools exist in the DB and can be looked up with `db.get_tool_by_slug()`.

**Step 1: Add rate limit constants for agent actions**

After the existing rate limits dict (line ~60-74), add:

```python
# Agent action daily rate limits (per API key per day)
_AGENT_ACTION_LIMITS = {
    "recommend": 50,
    "shortlist": 100,
    "report_outcome": 20,
    "confirm_integration": 10,
    "submit_tool": 3,
}
```

**Step 2: Add scope checking helper**

```python
def _require_scope(api_key: dict | None, scope: str) -> dict:
    """Validate API key exists and has required scope. Returns key dict or raises."""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required. Get one at https://indiestack.ai/developer")
    scopes = (api_key.get("scopes") or "read").split(",")
    if scope not in scopes:
        raise HTTPException(status_code=403, detail=f"This action requires '{scope}' scope. Enable it at https://indiestack.ai/dashboard")
    return api_key
```

**Step 3: Add `POST /api/agent/recommend`**

```python
@app.post("/api/agent/recommend")
async def agent_recommend(request: Request):
    """Record that an agent recommended a tool to its user."""
    api_key = _require_scope(request.state.api_key, "read")
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    tool_slug = str(data.get("tool_slug", "")).strip()
    query_context = str(data.get("query_context", "")).strip()[:500] or None

    if not tool_slug:
        return JSONResponse({"error": "tool_slug required"}, status_code=400)

    # Verify tool exists
    tool = await db.get_tool_by_slug(request.state.db, tool_slug)
    if not tool:
        return JSONResponse({"error": f"Tool '{tool_slug}' not found"}, status_code=404)

    # Rate limit
    count = await db.count_agent_actions_today(request.state.db, api_key["id"], "recommend")
    if count >= _AGENT_ACTION_LIMITS["recommend"]:
        return JSONResponse({"error": "Daily recommend limit reached (50/day)"}, status_code=429)

    # Dedup: one recommend per tool per user per day
    if await db.check_agent_daily_action(request.state.db, api_key["user_id"], "recommend", tool_slug):
        rec_count = await db.get_tool_recommendation_count(request.state.db, tool_slug)
        return JSONResponse({"ok": True, "already_recorded": True, "total_recommendations": rec_count})

    await db.record_agent_action(
        request.state.db, api_key["id"], api_key["user_id"],
        "recommend", tool_slug, query_context=query_context,
    )
    rec_count = await db.get_tool_recommendation_count(request.state.db, tool_slug)
    return JSONResponse({"ok": True, "total_recommendations": rec_count})
```

**Step 4: Add `POST /api/agent/shortlist`**

```python
@app.post("/api/agent/shortlist")
async def agent_shortlist(request: Request):
    """Record tools the agent considered for a query."""
    api_key = _require_scope(request.state.api_key, "read")
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    tool_slugs = data.get("tool_slugs", [])
    query_context = str(data.get("query_context", "")).strip()[:500] or None

    if not isinstance(tool_slugs, list) or len(tool_slugs) == 0:
        return JSONResponse({"error": "tool_slugs must be a non-empty list"}, status_code=400)
    if len(tool_slugs) > 10:
        return JSONResponse({"error": "Max 10 tool slugs per shortlist"}, status_code=400)

    count = await db.count_agent_actions_today(request.state.db, api_key["id"], "shortlist")
    if count >= _AGENT_ACTION_LIMITS["shortlist"]:
        return JSONResponse({"error": "Daily shortlist limit reached (100/day)"}, status_code=429)

    recorded = 0
    for slug in tool_slugs[:10]:
        slug = str(slug).strip()
        if not slug:
            continue
        tool = await db.get_tool_by_slug(request.state.db, slug)
        if tool:
            await db.record_agent_action(
                request.state.db, api_key["id"], api_key["user_id"],
                "shortlist", slug, query_context=query_context,
            )
            recorded += 1
    return JSONResponse({"ok": True, "recorded": recorded})
```

**Step 5: Add `POST /api/agent/outcome`**

```python
@app.post("/api/agent/outcome")
async def agent_outcome(request: Request):
    """Report whether a user successfully used a recommended tool."""
    api_key = _require_scope(request.state.api_key, "write")
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    tool_slug = str(data.get("tool_slug", "")).strip()
    success = data.get("success")
    notes = str(data.get("notes", "")).strip()[:1000] or None

    if not tool_slug:
        return JSONResponse({"error": "tool_slug required"}, status_code=400)
    if success is None or success not in (True, False, 0, 1):
        return JSONResponse({"error": "success must be true or false"}, status_code=400)

    tool = await db.get_tool_by_slug(request.state.db, tool_slug)
    if not tool:
        return JSONResponse({"error": f"Tool '{tool_slug}' not found"}, status_code=404)

    count = await db.count_agent_actions_today(request.state.db, api_key["id"], "report_outcome")
    if count >= _AGENT_ACTION_LIMITS["report_outcome"]:
        return JSONResponse({"error": "Daily outcome report limit reached (20/day)"}, status_code=429)

    # Dedup: one outcome per tool per user (ever)
    if await db.check_agent_action_exists(request.state.db, api_key["user_id"], "report_outcome", tool_slug):
        return JSONResponse({"ok": True, "already_recorded": True})

    await db.record_agent_action(
        request.state.db, api_key["id"], api_key["user_id"],
        "report_outcome", tool_slug, success=int(bool(success)), notes=notes,
    )
    stats = await db.get_tool_success_rate(request.state.db, tool_slug)
    return JSONResponse({"ok": True, "success_rate": stats})
```

**Step 6: Add `POST /api/agent/integration`**

```python
@app.post("/api/agent/integration")
async def agent_integration(request: Request):
    """Report that two tools were successfully integrated together."""
    api_key = _require_scope(request.state.api_key, "write")
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    tool_a = str(data.get("tool_a_slug", "")).strip()
    tool_b = str(data.get("tool_b_slug", "")).strip()
    notes = str(data.get("notes", "")).strip()[:1000] or None

    if not tool_a or not tool_b:
        return JSONResponse({"error": "tool_a_slug and tool_b_slug required"}, status_code=400)
    if tool_a == tool_b:
        return JSONResponse({"error": "Cannot integrate a tool with itself"}, status_code=400)

    # Verify both tools exist
    ta = await db.get_tool_by_slug(request.state.db, tool_a)
    tb = await db.get_tool_by_slug(request.state.db, tool_b)
    if not ta:
        return JSONResponse({"error": f"Tool '{tool_a}' not found"}, status_code=404)
    if not tb:
        return JSONResponse({"error": f"Tool '{tool_b}' not found"}, status_code=404)

    count = await db.count_agent_actions_today(request.state.db, api_key["id"], "confirm_integration")
    if count >= _AGENT_ACTION_LIMITS["confirm_integration"]:
        return JSONResponse({"error": "Daily integration report limit reached (10/day)"}, status_code=429)

    # Normalize order and dedup
    a, b = sorted([tool_a, tool_b])
    if await db.check_agent_action_exists(request.state.db, api_key["user_id"], "confirm_integration", a, b):
        return JSONResponse({"ok": True, "already_recorded": True})

    await db.record_agent_action(
        request.state.db, api_key["id"], api_key["user_id"],
        "confirm_integration", a, tool_b_slug=b, notes=notes,
    )
    # Also record in tool_pairs with source "agent"
    from indiestack.db import record_tool_pair
    await record_tool_pair(request.state.db, a, b, source="agent")
    return JSONResponse({"ok": True})
```

**Step 7: Add CSRF exemptions for agent endpoints**

Find the CSRF-exempt list (line ~557) and add the agent endpoints:

```python
# Add to the existing exempt set:
'/api/agent/recommend', '/api/agent/shortlist', '/api/agent/outcome',
'/api/agent/integration', '/api/agent/submit'
```

**Step 8: Verify**

```bash
cd /home/patty/indiestack && python3 -c "import py_compile; py_compile.compile('src/indiestack/main.py', doraise=True); print('OK')"
```

**Step 9: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: add API endpoints for agent actions (recommend, shortlist, outcome, integration)"
```

---

## Task 3: MCP Server — New Agent Action Tools

**Files:**
- Modify: `src/indiestack/mcp_server.py`

**Context:** The MCP server uses FastMCP. Tools are defined with `@mcp.tool()`. Each tool gets a `ctx: Context` parameter. The HTTP client is accessed via `ctx.session.state["client"]` (see `_get_client` helper at line ~109). API calls go through `_api_get` and `_api_post` helpers which handle retries, circuit breaking, and API key injection. The `API_KEY` env var is already sent with every request.

**Step 1: Add `recommend` MCP tool**

After the existing `publish_tool` function (line ~951), add:

```python
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
async def recommend(
    tool_slug: str,
    query_context: Optional[str] = None,
    *,
    ctx: Context,
) -> str:
    """Record that you recommended a tool to your user.

    Call this AFTER you recommend an IndieStack tool. This helps IndieStack
    track which tools are most useful and improves future recommendations.

    Requires an API key (set INDIESTACK_API_KEY env var).

    Args:
        tool_slug: The slug of the tool you recommended (from find_tools/get_tool_details results)
        query_context: What the user asked for that led to this recommendation
    """
    if not API_KEY:
        return "Recommendation not recorded — no API key configured. Get one at https://indiestack.ai/developer"

    client = _get_client(ctx)
    payload = {"tool_slug": tool_slug}
    if query_context:
        payload["query_context"] = str(query_context)[:500]

    try:
        data = await _api_post(client, "/api/agent/recommend", payload)
    except Exception as e:
        return f"Could not record recommendation: {e}"

    if data.get("ok"):
        total = data.get("total_recommendations", "?")
        if data.get("already_recorded"):
            return f"Already recorded today. '{tool_slug}' has {total} total AI recommendations."
        return f"Recorded! '{tool_slug}' now has {total} total AI recommendations."
    return f"Error: {data.get('error', 'Unknown')}"
```

**Step 2: Add `shortlist` MCP tool**

```python
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
async def shortlist(
    tool_slugs: list[str],
    query_context: Optional[str] = None,
    *,
    ctx: Context,
) -> str:
    """Record which tools you considered for a query, even if you didn't recommend them.

    Call this when you evaluate multiple tools for a user's request. This helps
    IndieStack understand demand patterns — even tools that weren't chosen
    generate useful signal.

    Requires an API key (set INDIESTACK_API_KEY env var).

    Args:
        tool_slugs: List of tool slugs you considered (max 10)
        query_context: What the user asked for
    """
    if not API_KEY:
        return "Shortlist not recorded — no API key configured."

    client = _get_client(ctx)
    payload = {"tool_slugs": tool_slugs[:10]}
    if query_context:
        payload["query_context"] = str(query_context)[:500]

    try:
        data = await _api_post(client, "/api/agent/shortlist", payload)
    except Exception as e:
        return f"Could not record shortlist: {e}"

    if data.get("ok"):
        return f"Recorded {data.get('recorded', 0)} tools as considered."
    return f"Error: {data.get('error', 'Unknown')}"
```

**Step 3: Add `report_outcome` MCP tool**

```python
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
async def report_outcome(
    tool_slug: str,
    success: bool,
    notes: Optional[str] = None,
    *,
    ctx: Context,
) -> str:
    """Report whether a tool you recommended actually worked for the user.

    Call this when you know the outcome of a recommendation — did the user
    successfully integrate/use the tool? This is the most valuable signal
    for improving recommendations.

    Requires an API key with write scope. Enable at https://indiestack.ai/dashboard

    Args:
        tool_slug: The slug of the tool
        success: True if the user successfully used the tool, False if not
        notes: Optional context about what happened
    """
    if not API_KEY:
        return "Outcome not recorded — no API key configured."

    client = _get_client(ctx)
    payload = {"tool_slug": tool_slug, "success": success}
    if notes:
        payload["notes"] = str(notes)[:1000]

    try:
        data = await _api_post(client, "/api/agent/outcome", payload)
    except Exception as e:
        return f"Could not record outcome: {e}"

    if data.get("ok"):
        if data.get("already_recorded"):
            return f"Outcome for '{tool_slug}' was already recorded."
        stats = data.get("success_rate", {})
        rate = stats.get("rate", "?")
        return f"Recorded! '{tool_slug}' now has a {rate}% success rate from agent reports."
    error = data.get("error", "Unknown")
    if "scope" in error.lower():
        return f"Write scope required. Enable it at https://indiestack.ai/dashboard"
    return f"Error: {error}"
```

**Step 4: Add `confirm_integration` MCP tool**

```python
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=False))
async def confirm_integration(
    tool_a_slug: str,
    tool_b_slug: str,
    notes: Optional[str] = None,
    *,
    ctx: Context,
) -> str:
    """Report that you successfully integrated two tools together in a project.

    Call this when you help a user connect two IndieStack tools. This data
    improves compatibility recommendations for all users.

    Requires an API key with write scope. Enable at https://indiestack.ai/dashboard

    Args:
        tool_a_slug: First tool slug
        tool_b_slug: Second tool slug
        notes: Optional context about the integration
    """
    if not API_KEY:
        return "Integration not recorded — no API key configured."

    client = _get_client(ctx)
    payload = {"tool_a_slug": tool_a_slug, "tool_b_slug": tool_b_slug}
    if notes:
        payload["notes"] = str(notes)[:1000]

    try:
        data = await _api_post(client, "/api/agent/integration", payload)
    except Exception as e:
        return f"Could not record integration: {e}"

    if data.get("ok"):
        if data.get("already_recorded"):
            return f"This integration pair was already recorded."
        return f"Recorded! '{tool_a_slug}' + '{tool_b_slug}' confirmed as compatible."
    error = data.get("error", "Unknown")
    if "scope" in error.lower():
        return f"Write scope required. Enable it at https://indiestack.ai/dashboard"
    return f"Error: {error}"
```

**Step 5: Update MCP instructions**

In the `mcp = FastMCP(...)` instructions string (line ~79-103), add after the WORKFLOW line:

```python
"AGENT ACTIONS (when you have an API key):\n"
"- After recommending a tool, call recommend(slug) to record it\n"
"- After evaluating tools, call shortlist(slugs) to record what you considered\n"
"- After a user integrates a tool, call report_outcome(slug, success) with the result\n"
"- After connecting two tools, call confirm_integration(tool_a, tool_b)\n"
"- These actions improve future recommendations for you and all agents.\n\n"
```

**Step 6: Verify**

```bash
cd /home/patty/indiestack && python3 -c "import py_compile; py_compile.compile('src/indiestack/mcp_server.py', doraise=True); print('OK')"
```

**Step 7: Commit**

```bash
git add src/indiestack/mcp_server.py
git commit -m "feat: add MCP tools for agent actions (recommend, shortlist, outcome, integration)"
```

---

## Task 4: Dashboard — Agent Activity Section

**Files:**
- Modify: `src/indiestack/routes/dashboard.py`

**Context:** The dashboard is at `/dashboard` and requires login. It's rendered in `dashboard.py`. It shows API keys, tools, submissions, etc. The user is available as `request.state.user`. Use the `get_agent_action_counts` and `get_agent_action_log` DB functions from Task 1.

**Step 1: Find the API keys section in dashboard.py**

Search for where API keys are displayed and add the agent activity section immediately after.

**Step 2: Add agent activity section**

After the API keys section, add:

```python
# Agent Activity
action_counts = await db.get_agent_action_counts(request.state.db, user['id'], days=30)
action_log = await db.get_agent_action_log(request.state.db, user['id'], limit=10)

rec_count = action_counts.get('recommend', 0)
short_count = action_counts.get('shortlist', 0)
outcome_count = action_counts.get('report_outcome', 0)
ok_count = action_counts.get('outcomes_success', 0)
fail_count = action_counts.get('outcomes_fail', 0)
integ_count = action_counts.get('confirm_integration', 0)
submit_count = action_counts.get('submit_tool', 0)

agent_activity_html = ''
if rec_count or short_count or outcome_count or integ_count or submit_count:
    log_rows = ''
    for a in action_log:
        ts = a['created_at'][:16].replace('T', ' ') if a.get('created_at') else ''
        action_label = a['action'].replace('_', ' ').title()
        tools = escape(a['tool_slug'])
        if a.get('tool_b_slug'):
            tools += f" + {escape(a['tool_b_slug'])}"
        ctx = f" &mdash; {escape(a['query_context'][:80])}" if a.get('query_context') else ''
        log_rows += f'<tr><td style="color:var(--ink-muted);font-size:13px;white-space:nowrap;">{ts}</td><td>{action_label}</td><td>{tools}{ctx}</td></tr>'

    agent_activity_html = f'''
    <div class="card" style="margin-top:32px;">
        <h2 style="font-family:var(--font-display);font-size:22px;margin-bottom:16px;">Agent Activity <span style="font-size:13px;color:var(--ink-muted);font-weight:400;">last 30 days</span></h2>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:16px;margin-bottom:24px;">
            <div style="text-align:center;"><div style="font-size:28px;font-weight:700;color:var(--accent);">{rec_count}</div><div style="font-size:13px;color:var(--ink-muted);">Recommendations</div></div>
            <div style="text-align:center;"><div style="font-size:28px;font-weight:700;color:var(--ink);">{short_count}</div><div style="font-size:13px;color:var(--ink-muted);">Shortlisted</div></div>
            <div style="text-align:center;"><div style="font-size:28px;font-weight:700;color:var(--ink);">{outcome_count}</div><div style="font-size:13px;color:var(--ink-muted);">Outcomes ({ok_count} ok, {fail_count} fail)</div></div>
            <div style="text-align:center;"><div style="font-size:28px;font-weight:700;color:var(--ink);">{integ_count}</div><div style="font-size:13px;color:var(--ink-muted);">Integrations</div></div>
        </div>
        {"<table style='width:100%;font-size:14px;'><thead><tr><th style=&quot;text-align:left;&quot;>Time</th><th style=&quot;text-align:left;&quot;>Action</th><th style=&quot;text-align:left;&quot;>Tool(s)</th></tr></thead><tbody>" + log_rows + "</tbody></table>" if log_rows else "<p style='color:var(--ink-muted);font-size:14px;'>No agent actions yet. Configure your API key in your AI agent to get started.</p>"}
    </div>
    '''
```

**Step 3: Add scope toggle to API keys section**

In the API keys display, add a toggle for each key to enable/disable write scope. This should be a small form that POSTs to a new endpoint.

**Step 4: Add scope toggle endpoint**

In `dashboard.py`, add:

```python
@router.post("/dashboard/api-keys/{key_id}/scope")
async def toggle_key_scope(request: Request, key_id: int):
    user = request.state.user
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    from indiestack.db import update_api_key_scopes, get_api_keys_for_user
    # Find current scope
    keys = await get_api_keys_for_user(request.state.db, user['id'])
    current_key = next((k for k in keys if k['id'] == key_id), None)
    if not current_key:
        return RedirectResponse(url="/dashboard?tab=developer", status_code=303)
    # Toggle
    new_scopes = "read" if current_key.get('scopes', 'read') == 'read,write' else "read,write"
    await update_api_key_scopes(request.state.db, key_id, user['id'], new_scopes)
    return RedirectResponse(url="/dashboard?tab=developer", status_code=303)
```

**Step 5: Verify**

```bash
cd /home/patty/indiestack && python3 -c "import py_compile; py_compile.compile('src/indiestack/routes/dashboard.py', doraise=True); print('OK')"
```

**Step 6: Commit**

```bash
git add src/indiestack/routes/dashboard.py
git commit -m "feat: add agent activity dashboard section and scope toggle"
```

---

## Task 5: Smoke Tests + Deploy

**Files:**
- Modify: `smoke_test.py`

**Step 1: Add agent endpoint smoke tests**

Add to the `TESTS` list in `smoke_test.py`:

```python
# Agent action endpoints (require API key — expect 401 without)
("POST", "/api/agent/recommend", 401, "Agent recommend auth guard"),
("POST", "/api/agent/shortlist", 401, "Agent shortlist auth guard"),
("POST", "/api/agent/outcome", 401, "Agent outcome auth guard"),
("POST", "/api/agent/integration", 401, "Agent integration auth guard"),
```

**Step 2: Run smoke tests locally**

```bash
cd /home/patty/indiestack && python3 smoke_test.py https://indiestack.ai
```

Expected: All existing tests pass + 4 new tests pass (401 for unauthenticated agent endpoints).

**Note:** The actual 401 vs 403 status may depend on whether the CSRF middleware intercepts POSTs first. Check the actual response and adjust expected status codes if needed.

**Step 3: Deploy**

```bash
cd /home/patty/indiestack && ~/.fly/bin/fly deploy --ha=false
```

**Step 4: Run smoke tests against production**

```bash
python3 smoke_test.py https://indiestack.ai
```

Expected: All tests pass.

**Step 5: Commit smoke test updates**

```bash
git add smoke_test.py
git commit -m "test: add smoke tests for agent action endpoints"
```

---

## Task 6: Update MCP Server Version + Publish

**Files:**
- Modify: `pyproject.toml` (version bump)
- Modify: `server.json` (version)

**Step 1: Bump version**

Update version in `pyproject.toml` and `server.json` from `1.4.0` to `1.5.0`.

**Step 2: Build and publish**

```bash
cd /home/patty/indiestack && python3 -m build && python3 -m twine upload dist/indiestack-1.5.0*
```

**Step 3: Verify**

```bash
pip3 index versions indiestack 2>/dev/null
```

**Step 4: Commit**

```bash
git add pyproject.toml server.json
git commit -m "chore: bump MCP server to v1.5.0 — agent-native actions"
```

---

## Execution Order

Tasks 1-4 are sequential (each depends on the previous). Task 5 depends on all previous tasks. Task 6 depends on Task 5.

```
Task 1 (DB) → Task 2 (API) → Task 3 (MCP) → Task 4 (Dashboard) → Task 5 (Test + Deploy) → Task 6 (Publish)
```

Total estimated changes: ~400 lines across 5 files.

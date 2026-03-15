# Outcome Intelligence Layer — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform IndieStack from a static catalog into an outcome-aware recommendation engine by lowering outcome reporting friction, capturing implicit signals, strengthening agent nudges, and surfacing success rates across the platform.

**Architecture:** Leverage existing `agent_actions` table and `report_outcome` infrastructure. No new tables. Lower scope requirements to reduce friction. Add implicit signal inference from existing `search_logs` + `agent_citations` data. Surface outcome data in both MCP responses and web UI.

**Tech Stack:** Python/FastAPI, SQLite (aiosqlite), MCP server (FastMCP), f-string HTML templates.

---

### Task 1: Lower Outcome Reporting Friction

**Why:** The #1 barrier to outcome data. Currently `report_outcome` requires `write` scope — most agents have read-only keys or no key at all. Outcome reporting is the ONE action we want to be as frictionless as possible.

**Files:**
- Modify: `src/indiestack/main.py` (the `/api/agent/outcome` endpoint, ~line 3769)
- Modify: `src/indiestack/main.py` (rate limit config, ~line 42)

**Step 1: Change scope requirement for outcome endpoint**

In `main.py`, the `/api/agent/outcome` handler calls `_require_scope(request, "write")`. Change this to accept `read` scope. This lets any agent with an API key report outcomes without needing write permissions.

Find the outcome endpoint handler (~line 3769-3803) and change the `_require_scope` call from `"write"` to `"read"`.

**Step 2: Allow keyless outcome reporting**

Add a fallback path: if no API key is present but the request includes a valid tool_slug + success boolean, still record the outcome but with `api_key_id=NULL` and `user_id=0`. This captures data from agents that haven't set up API keys.

In the same endpoint, after the scope check, add logic: if `request.state.api_key` is None, allow the request but with keyless tracking (IP-based rate limit of 10/day, same pattern as keyless search).

Update the `agent_actions` table's `api_key_id` column constraint — it's currently `NOT NULL`. Need a migration to make it nullable.

**Step 3: Update MCP server to handle keyless outcome reporting**

In `src/indiestack/mcp_server.py`, the `report_outcome` tool (~line 1675) sends the request with the API key header. If no API key is configured, it should still attempt the request (the server will accept keyless reports now).

Currently, the MCP server's `_api_call()` helper adds the API key to requests. Check that it still works when `API_KEY` is empty — the server-side should handle both keyed and keyless gracefully.

**Step 4: Run tests / verify**

```bash
cd /home/patty/indiestack && python3 -m pytest tests/ -x -q 2>&1 | tail -20
```

**Step 5: Commit**

```bash
git add src/indiestack/main.py src/indiestack/db.py
git commit -m "feat: lower outcome reporting friction — accept read scope + keyless"
```

---

### Task 2: Strengthen MCP Response Nudges

**Why:** Agents follow instructions. If the tool detail response includes a clear directive to report outcomes, compliance will increase significantly. Currently, the instruction is buried in the MCP server's system prompt — agents often ignore system-level instructions in favor of contextual ones.

**Files:**
- Modify: `src/indiestack/mcp_server.py` (~lines 660-779, `get_tool_details` function)
- Modify: `src/indiestack/mcp_server.py` (~lines 520-599, `find_tools` function)

**Step 1: Add outcome nudge to `get_tool_details` response**

At the end of the `get_tool_details` response string (after all the tool metadata), append a section:

```
---
📊 **Help improve recommendations**: After your user integrates this tool, call `report_outcome("{slug}", success=True/False)` — no write scope needed, takes 1 second. This data helps all agents make better recommendations.
```

This goes in the response string building section of `get_tool_details`, after the compatibility pairs section.

**Step 2: Add success rate to `get_tool_details` response (if data exists)**

Before the nudge, if the tool has any outcome data, include it:

```
🎯 **Agent Success Rate**: 82% (14 successful / 17 total integrations reported by agents)
```

To get this data, the MCP server needs to read `success_rate` from the API response. The `/api/tools/{slug}` endpoint already returns tool data — add `success_rate` to the JSON response in main.py. Use the existing `db.get_tool_success_rate()` function.

In `main.py` at the tool detail JSON endpoint (~line 2078-2172), add:
```python
success_rate = await db.get_tool_success_rate(d, slug)
if success_rate["total"] > 0:
    result["success_rate"] = success_rate
```

Then in the MCP server's `get_tool_details`, read this field and format it.

**Step 3: Add light nudge to `find_tools` response**

At the bottom of search results, add one line:
```
💡 Tip: After integrating any tool, call report_outcome(slug, success) to improve future recommendations.
```

Keep it brief — search results should be scannable.

**Step 4: Commit**

```bash
git add src/indiestack/mcp_server.py src/indiestack/main.py
git commit -m "feat: add outcome nudge + success rate to MCP tool responses"
```

---

### Task 3: Implicit Signal Tracking

**Why:** Most agents won't explicitly report outcomes even with nudges. But their behavior tells a story: search → detail view → silence in that category = probable adoption. Search → detail view → search again in same category = rejection. This passive telemetry is the foundation of the outcome data moat.

**Files:**
- Modify: `src/indiestack/db.py` (new functions)
- Modify: `src/indiestack/main.py` (add agent_client tracking to search/detail endpoints)

**Step 1: Add `agent_client` tracking to search logs**

The `search_logs` table already has `source` (web/mcp) and `api_key_id`. Add an `agent_client` column (TEXT, nullable) to capture which agent platform made the request.

In `db.py`, add migration:
```python
await db.execute("ALTER TABLE search_logs ADD COLUMN agent_client TEXT")
```

In the MCP server, pass a `User-Agent`-style header or query param. The MCP server can send its version string (e.g., `indiestack-mcp/1.5.0`). The consuming agent's identity can be inferred from the API key's user or from the request headers.

In `main.py`, in the search API handler, capture the `User-Agent` header and store it as `agent_client` when logging searches.

**Step 2: Write implicit signal inference function**

Add to `db.py`:

```python
async def compute_implicit_signals(db: aiosqlite.Connection, hours: int = 24) -> list[dict]:
    """Analyze recent search→citation sequences to infer adoption/rejection.

    Adoption signal: agent searches category, views tool detail, no further
    searches in same category within 30 minutes.

    Rejection signal: agent searches category, views tool detail, searches
    same category again within 10 minutes.
    """
```

The function:
1. Gets recent search_logs with api_key_id (grouped by session = same api_key within time window)
2. For each search, checks if agent_citations exist for tools in the results
3. Checks if there's a follow-up search in the same category within 10 minutes (rejection) or silence for 30+ minutes (adoption)
4. Returns list of `{tool_slug, signal_type: "implicit_adoption"|"implicit_rejection", confidence: 0.0-1.0, api_key_id, timestamp}`

**Step 3: Write background aggregation function**

Add to `db.py`:

```python
async def aggregate_tool_signals(db: aiosqlite.Connection, tool_slug: str) -> dict:
    """Get combined explicit + implicit outcome stats for a tool.

    Returns {
        explicit: {success: N, fail: N, total: N, rate: N},
        implicit: {adoptions: N, rejections: N, total: N, rate: N},
        combined: {positive: N, negative: N, total: N, rate: N},
        confidence: "low"|"medium"|"high"
    }
    """
```

Confidence thresholds:
- low: < 5 total signals
- medium: 5-20 total signals
- high: > 20 total signals

Weighting: explicit signals count 1.0, implicit signals count 0.6 (because they're inferred).

**Step 4: Commit**

```bash
git add src/indiestack/db.py src/indiestack/main.py
git commit -m "feat: add implicit signal tracking from search-citation sequences"
```

---

### Task 4: Surface Outcome Data on Tool Detail Web Pages

**Why:** Making outcome data visible creates social proof AND incentivizes agents to report (their reports affect what users see). This is the "Trustpilot for AI agents" idea in its simplest form.

**Files:**
- Modify: `src/indiestack/tool.py` or equivalent tool detail route
- Modify: `src/indiestack/components.py` (for the badge/widget HTML)

**Step 1: Create outcome badge component**

In `components.py`, add a function that renders an "Agent Intelligence" badge:

```python
def agent_outcome_badge(stats: dict) -> str:
    """Render agent outcome stats badge for tool detail page.

    Shows: "Recommended X times · Y% success rate" with a confidence indicator.
    Only renders if there's any data. Graceful empty state.
    """
```

Design (following IndieStack design tokens):
- Small card/section below the existing tool stats
- Icon: 🤖 or similar
- Text: "AI Agent Intelligence"
- Stats: "Recommended {N} times" + "Success rate: {X}%" (if outcomes exist)
- Confidence badge: "Based on {N} agent reports" in muted text
- If no data: "No agent reports yet" in muted text (or don't show at all)

Use existing design tokens: `--text-muted`, `--border-color`, badge classes.

**Step 2: Add outcome stats to tool detail page**

In the tool detail route handler, fetch outcome stats:
```python
recommendation_count = await db.get_tool_recommendation_count(d, tool["slug"])
success_rate = await db.get_tool_success_rate(d, tool["slug"])
```

Pass these to the template and render the badge.

**Step 3: Add to tool detail API for MCP consumption**

Ensure `/api/tools/{slug}` includes `recommendation_count` and `success_rate` in all responses (not just Pro). This is public data — agents contributed it, agents should see it.

**Step 4: Commit**

```bash
git add src/indiestack/components.py src/indiestack/tool.py src/indiestack/main.py
git commit -m "feat: show agent success rate on tool detail pages + API"
```

---

### Task 5: Update MCP Server Instructions

**Why:** The MCP server's system prompt should clearly communicate that IndieStack tracks outcomes and that reporting improves recommendations. This is the "instruction-driven compliance" strategy.

**Files:**
- Modify: `src/indiestack/mcp_server.py` (lines 79-109, instructions string)

**Step 1: Enhance the instructions string**

Update the MCP server's `instructions` parameter to emphasize outcome reporting more prominently. Current instructions mention it but it's buried among other features.

New instructions should:
1. Lead with the value proposition: "IndieStack recommendations improve when agents report outcomes"
2. Make clear that `report_outcome` works without write scope or even without an API key
3. Frame it as mutual benefit: "Your reports help other agents avoid tools with high failure rates"

Keep it concise — instructions eat into context window.

**Step 2: Commit**

```bash
git add src/indiestack/mcp_server.py
git commit -m "feat: strengthen outcome reporting instructions in MCP server"
```

---

### Task 6: Bump MCP Server Version

**Why:** These changes affect the MCP server package on PyPI. Users need to update to get the improved nudges and frictionless reporting.

**Files:**
- Modify: `pyproject.toml` (version bump)
- Modify: `README_PYPI.md` (if needed)

**Step 1: Bump version**

Increment from current version (1.5.0) to 1.6.0 (new feature: outcome intelligence).

**Step 2: Update README_PYPI.md**

Add a brief mention of outcome reporting in the features section.

**Step 3: DO NOT publish yet** — Patrick will use the `/publish-mcp` skill when ready.

**Step 4: Commit**

```bash
git add pyproject.toml README_PYPI.md
git commit -m "chore: bump version to 1.6.0 for outcome intelligence features"
```

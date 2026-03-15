# Maker Retention Features Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform IndieStack's maker experience from passive directory listing to active cross-agent telemetry platform with Agent Instructions, success rate analytics, and a Listing Quality Score.

**Architecture:** Three features, each building on the last. (1) Add an `agent_instructions` text field to the tools table that makers can edit from their dashboard — this gets injected into MCP responses and Agent Cards so agents use maker-authored context. (2) Wire the existing v1.6.0 success rate data (`get_tool_success_rate`, `aggregate_tool_signals`) into the maker dashboard so makers can see how their tools perform. (3) Compute and display a Listing Quality Score based on metadata completeness + success rate + freshness, shown as a progress bar with actionable improvement tips.

**Tech Stack:** Python/FastAPI, SQLite (aiosqlite), pure Python string HTML templates (f-strings), no Jinja2/React. CSS lives in `components.py` `:root` or inline. No test framework — verify manually via running server.

**Key files:**
- `src/indiestack/db.py` — schema, migrations, data access
- `src/indiestack/routes/dashboard.py` — maker dashboard UI
- `src/indiestack/mcp_server.py` — MCP tool responses
- `src/indiestack/main.py` — API routes including Agent Card endpoint

---

## Task 1: Add `agent_instructions` Column to Tools Table

**Files:**
- Modify: `src/indiestack/db.py` (migration in `ensure_tables_exist`)

**Context:** The `tools` table schema is defined at `db.py:36-58`. Migrations run in `ensure_tables_exist()` which uses `ALTER TABLE ... ADD COLUMN` with `try/except` for idempotency. See existing migration patterns around line 1100+.

**Step 1: Add the column to the CREATE TABLE definition**

In `db.py`, find the `tools` CREATE TABLE (line 36). Add after the `created_at` line:

```python
    agent_instructions TEXT NOT NULL DEFAULT '',
```

**Step 2: Add ALTER TABLE migration in `ensure_tables_exist`**

Find the migrations section in `ensure_tables_exist()`. Add:

```python
    try:
        await db.execute("ALTER TABLE tools ADD COLUMN agent_instructions TEXT NOT NULL DEFAULT ''")
    except Exception:
        pass
```

**Step 3: Verify**

Run: `python3 -c "import asyncio, aiosqlite; asyncio.run((lambda: None)())"` — just ensure no syntax errors.

**Step 4: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add agent_instructions column to tools table"
```

---

## Task 2: Add Agent Instructions Textarea to Dashboard Edit Form

**Files:**
- Modify: `src/indiestack/routes/dashboard.py:1177-1258` (POST handler) and `1313-1550` (form HTML)

**Context:** The tool edit page is at `/dashboard/tools/{tool_id}/edit`. The GET handler is at line 1151, POST at 1177. The form HTML is rendered by `edit_tool_form()` starting around line 1313. There are already 16 editable fields. The POST handler accepts Form() parameters and calls `update_tool()`.

**Step 1: Add `agent_instructions` to the POST handler parameters**

In the POST handler `async def update_tool_post(...)` at line 1177, add the parameter:

```python
agent_instructions: str = Form(''),
```

**Step 2: Pass `agent_instructions` to the `update_tool()` call**

Find where `update_tool()` is called in the POST handler. Add `agent_instructions` to the fields being updated. The `update_tool` function in `db.py` likely accepts keyword args — check its signature and add the field.

If `update_tool` builds an UPDATE query dynamically, add `agent_instructions` to the fields dict. If it uses positional args, add it in the right position.

**Step 3: Add the textarea to the edit form HTML**

In `edit_tool_form()`, add after the `frameworks_tested` field (or before the pixel_icon section). Use the same styling as other textareas:

```python
# Agent Instructions
<div style="margin-bottom:20px;">
    <label style="display:block;font-weight:600;margin-bottom:6px;font-size:14px;">Agent Instructions</label>
    <p style="font-size:12px;color:var(--ink-muted);margin:0 0 8px;">
        Tell AI agents how to implement your tool correctly. This text is injected directly into agent context when they recommend your tool. Include: correct import syntax, common pitfalls, required setup steps, and version-specific notes.
    </p>
    <textarea name="agent_instructions" rows="6" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface);color:var(--ink);font-family:var(--font-mono);font-size:13px;resize:vertical;"
        placeholder="Example: Use v3 API (v2 is deprecated). Auth requires both API_KEY and PROJECT_ID env vars. For Next.js, wrap in useEffect — SSR is not supported."
    >{escape(tool.get('agent_instructions', ''))}</textarea>
</div>
```

**Step 4: Verify manually**

Deploy locally, navigate to `/dashboard/tools/{id}/edit`, confirm the textarea appears and saves correctly.

**Step 5: Commit**

```bash
git add src/indiestack/routes/dashboard.py
git commit -m "feat: add Agent Instructions textarea to tool edit form"
```

---

## Task 3: Inject Agent Instructions into MCP `get_tool_details` Response

**Files:**
- Modify: `src/indiestack/mcp_server.py:663-776`

**Context:** The `get_tool_details` MCP tool returns a markdown-formatted string. It already includes assembly metadata (API type, auth method, etc.) at the end. Agent instructions should appear prominently — this is the maker's voice telling agents exactly how to implement.

**Step 1: Add agent_instructions to the response**

In the `get_tool_details` handler (around line 663), find where the tool data is fetched. The tool dict from the API should already include `agent_instructions` once the DB column exists.

After the description section and before the assembly metadata, add:

```python
# Agent Instructions (maker-authored)
agent_instructions = tool.get('agent_instructions', '').strip()
if agent_instructions:
    parts.append(f"\n**Agent Instructions (from the maker):**\n{agent_instructions}\n")
```

Position this prominently — agents should see maker instructions BEFORE the generic assembly metadata.

**Step 2: Verify**

Test via MCP by calling `get_tool_details` for a tool that has agent_instructions set. Confirm the instructions appear in the response.

**Step 3: Commit**

```bash
git add src/indiestack/mcp_server.py
git commit -m "feat: inject agent_instructions into MCP tool detail response"
```

---

## Task 4: Add Agent Instructions to Agent Card JSON

**Files:**
- Modify: `src/indiestack/main.py:2228-2348` (the `/cards/{slug}.json` endpoint)

**Context:** The Agent Card returns a JSON capability card at `/cards/{slug}.json`. It has sections for capabilities, health, trust, compatibility, pricing. Agent instructions should go in the capabilities section.

**Step 1: Add to the JSON response**

Find the card JSON construction (around line 2280). In the `capabilities` dict, add:

```python
"agent_instructions": tool.get('agent_instructions', '') or None,
```

Use `or None` so empty strings become null in JSON (cleaner for consumers).

**Step 2: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: add agent_instructions to Agent Card JSON"
```

---

## Task 5: Wire Success Rate into Maker Dashboard Overview

**Files:**
- Modify: `src/indiestack/routes/dashboard.py:62-359` (dashboard overview)
- Check: `src/indiestack/db.py` — `get_tool_success_rate`, `aggregate_tool_signals`

**Context:** The dashboard overview at `/dashboard` already shows agent_citations_30d and citation_percentile. The success rate functions exist in db.py (lines 5275-5285 for `get_tool_success_rate`, 5357-5428 for `aggregate_tool_signals`). These need to be called for the maker's tools and displayed.

**Step 1: Import the success rate function**

In dashboard.py, add to the imports from `indiestack.db`:

```python
get_tool_success_rate, aggregate_tool_signals,
```

**Step 2: Compute aggregate success rate across maker's tools**

In `dashboard_overview()` after the agent citations fetch (around line 96), add:

```python
    # Aggregate success rate across all maker's tools
    maker_success_rate = None
    if maker_id:
        tools_list = await get_tools_by_maker(db, maker_id)
        total_success = 0
        total_outcomes = 0
        for t in tools_list:
            sr = await get_tool_success_rate(db, t['slug'])
            total_success += sr.get('success', 0)
            total_outcomes += sr.get('total', 0)
        if total_outcomes > 0:
            maker_success_rate = round(total_success / total_outcomes * 100)
```

**Step 3: Add success rate to the dashboard stats display**

Find the stats grid in the HTML (look for the section showing agent_citations_30d, upvotes, etc.). Add a new stat card:

```python
# Success rate card
sr_display = f'{maker_success_rate}%' if maker_success_rate is not None else '—'
sr_color = 'var(--accent)' if (maker_success_rate or 0) >= 70 else '#E2B764' if (maker_success_rate or 0) >= 40 else '#e74c3c'
```

Then in the HTML grid:

```html
<div style="text-align:center;padding:16px;background:rgba(255,255,255,0.07);border-radius:var(--radius-sm);">
    <div style="font-family:var(--font-display);font-size:28px;color:{sr_color};">{sr_display}</div>
    <div style="font-size:12px;color:var(--ink-muted);margin-top:4px;">Success Rate</div>
</div>
```

**Step 4: Verify**

Deploy locally, check `/dashboard` — success rate should appear in the stats grid. With no outcome data it shows "—".

**Step 5: Commit**

```bash
git add src/indiestack/routes/dashboard.py
git commit -m "feat: show agent success rate on maker dashboard"
```

---

## Task 6: Add Per-Tool Success Rate to Tool Management Cards

**Files:**
- Modify: `src/indiestack/routes/dashboard.py` — find the "My Tools" section where individual tool cards are rendered

**Context:** The dashboard has a "My Tools" section showing each tool with its stats. Each tool card should show its individual success rate alongside citations and upvotes.

**Step 1: Find the tool cards rendering**

Search for where individual tools are listed on the dashboard (likely in the tool management tab or the main dashboard). Look for iteration over `tools_list` or similar.

**Step 2: Add per-tool success rate**

For each tool in the list, call `get_tool_success_rate(db, tool['slug'])` and display a small badge:

```python
sr = await get_tool_success_rate(db, tool['slug'])
if sr['total'] > 0:
    sr_badge = f'<span style="font-size:11px;color:{"#2ecc71" if sr["rate"] >= 70 else "#E2B764" if sr["rate"] >= 40 else "#e74c3c"};">{sr["rate"]}% success</span>'
else:
    sr_badge = ''
```

**Step 3: Commit**

```bash
git add src/indiestack/routes/dashboard.py
git commit -m "feat: show per-tool success rate badges on dashboard"
```

---

## Task 7: Implement Listing Quality Score Calculation

**Files:**
- Modify: `src/indiestack/db.py` — add `get_listing_quality_score()` function

**Context:** The Listing Quality Score is a composite metric:
- **Metadata completeness (40%)**: Does the tool have description, tags, api_type, auth_method, install_command, sdk_packages, env_vars, frameworks_tested, agent_instructions?
- **Success rate (35%)**: From outcome data (explicit + implicit)
- **Freshness (25%)**: How recently was the listing updated?

Since most tools have no outcome data yet, weight metadata completeness higher initially.

**Step 1: Add the function to db.py**

```python
async def get_listing_quality_score(db, tool: dict) -> dict:
    """Compute listing quality score (0-100) with breakdown."""
    # Metadata completeness (40% weight)
    metadata_fields = [
        ('description', bool(tool.get('description', '').strip())),
        ('tags', bool(tool.get('tags', '').strip())),
        ('api_type', bool(tool.get('api_type', '').strip())),
        ('auth_method', bool(tool.get('auth_method', '').strip())),
        ('install_command', bool(tool.get('install_command', '').strip())),
        ('agent_instructions', bool(tool.get('agent_instructions', '').strip())),
    ]
    filled = sum(1 for _, has in metadata_fields if has)
    metadata_score = filled / len(metadata_fields) * 100

    # Success rate (35% weight) — only if we have data
    sr = await get_tool_success_rate(db, tool['slug'])
    if sr['total'] > 0:
        success_score = sr['rate']
    else:
        success_score = 50  # Neutral when no data

    # Freshness (25% weight) — based on tool updated_at or created_at
    # For now, use whether key fields are filled as a proxy
    # (Real freshness would need an updated_at column)
    freshness_score = metadata_score  # Proxy: complete = maintained

    total = round(metadata_score * 0.40 + success_score * 0.35 + freshness_score * 0.25)

    missing = [name for name, has in metadata_fields if not has]

    return {
        'score': min(total, 100),
        'metadata_score': round(metadata_score),
        'success_score': round(success_score),
        'freshness_score': round(freshness_score),
        'missing_fields': missing,
        'tips': _quality_tips(missing, sr['total']),
    }

def _quality_tips(missing: list, outcome_count: int) -> list[str]:
    """Generate actionable tips to improve listing quality."""
    tips = []
    if 'agent_instructions' in missing:
        tips.append('Add Agent Instructions — tell AI agents exactly how to implement your tool')
    if 'install_command' in missing:
        tips.append('Add an install command so agents can set up your tool automatically')
    if 'api_type' in missing:
        tips.append('Specify your API type (REST, GraphQL, SDK, CLI)')
    if 'tags' in missing:
        tips.append('Add tags to help agents find your tool for the right queries')
    if 'description' in missing:
        tips.append('Write a description — agents use this to decide whether to recommend you')
    if outcome_count == 0:
        tips.append('Your tool has no outcome data yet — agents will report success/failure as they recommend it')
    return tips[:3]  # Top 3 most impactful
```

**Step 2: Export the function**

Ensure `get_listing_quality_score` is importable from db.py.

**Step 3: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add listing quality score calculation"
```

---

## Task 8: Display Listing Quality Score on Dashboard

**Files:**
- Modify: `src/indiestack/routes/dashboard.py` — dashboard overview and/or tool edit page

**Context:** Display the Listing Quality Score as a progress bar with color coding and actionable tips. Best placement: on the dashboard overview (aggregate across tools) and on individual tool edit pages.

**Step 1: Import the function**

Add to dashboard.py imports:

```python
get_listing_quality_score,
```

**Step 2: Compute score in dashboard overview**

In `dashboard_overview()`, after computing success rate, compute quality score for the maker's primary/first tool (or average across tools):

```python
    quality_score = None
    quality_tips = []
    if maker_id and tools_list:
        scores = []
        all_tips = []
        for t in tools_list[:10]:  # Cap at 10 to avoid slow queries
            qs = await get_listing_quality_score(db, t)
            scores.append(qs['score'])
            if qs['tips']:
                all_tips.extend(qs['tips'])
        quality_score = round(sum(scores) / len(scores)) if scores else None
        # Deduplicate tips, keep top 3
        seen = set()
        for tip in all_tips:
            if tip not in seen:
                seen.add(tip)
                quality_tips.append(tip)
            if len(quality_tips) >= 3:
                break
```

**Step 3: Add the progress bar HTML**

Create a "Listing Quality" card in the dashboard. Place it prominently — ideally right after the stats grid:

```python
quality_html = ''
if quality_score is not None:
    bar_color = '#2ecc71' if quality_score >= 70 else '#E2B764' if quality_score >= 40 else '#e74c3c'
    tips_html = ''.join(f'<li style="margin-bottom:6px;">{escape(tip)}</li>' for tip in quality_tips)
    tips_section = f'<ul style="margin:12px 0 0;padding-left:20px;font-size:13px;color:var(--ink-muted);">{tips_html}</ul>' if tips_html else ''

    quality_html = f'''
    <div class="card" style="padding:24px;margin-bottom:24px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <h3 style="margin:0;font-family:var(--font-display);font-size:18px;">Listing Quality</h3>
            <span style="font-family:var(--font-display);font-size:24px;color:{bar_color};">{quality_score}/100</span>
        </div>
        <div style="background:var(--border);border-radius:999px;height:8px;overflow:hidden;">
            <div style="background:{bar_color};height:100%;width:{quality_score}%;border-radius:999px;transition:width 0.3s;"></div>
        </div>
        {tips_section}
    </div>
    '''
```

Then inject `{quality_html}` into the page HTML at the appropriate position.

**Step 4: Add per-tool quality score to tool edit page**

On the individual tool edit page, show the tool's quality score at the top with specific missing fields highlighted.

**Step 5: Verify**

Deploy locally, check `/dashboard` — quality score bar should appear with tips.

**Step 6: Commit**

```bash
git add src/indiestack/routes/dashboard.py
git commit -m "feat: display Listing Quality Score with progress bar and tips"
```

---

## Task 9: Update Strategic Cracks Document

**Files:**
- Modify: `docs/plans/2026-03-14-strategic-cracks.md`

**Step 1: Mark crack #2 as resolved**

Update crack #2 status:

```markdown
## (2) Why List? — The Maker Incentive Problem
- [x] **Status: RESOLVED** — Agent Instructions, success rate analytics, Listing Quality Score
```

**Step 2: Commit**

```bash
git add docs/plans/2026-03-14-strategic-cracks.md
git commit -m "docs: mark crack #2 (maker incentive) as resolved"
```

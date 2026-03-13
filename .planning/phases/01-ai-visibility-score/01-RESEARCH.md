# Phase 1: AI Visibility Score - Research

**Researched:** 2026-03-13
**Domain:** Dashboard analytics card (Python f-string HTML, SQLite queries, existing data)
**Confidence:** HIGH

## Summary

Phase 1 adds an "AI Visibility" card to the existing maker dashboard at `/dashboard`. The good news: nearly all the infrastructure already exists. The `agent_citations` table is populated, `search_logs` tracks queries with `top_result_slug`, and the dashboard already shows a 7-day citation count plus an "AI Distribution Intelligence" section with query tables, agent breakdowns, and a 14-day sparkline.

What is **missing** to satisfy the four AIVIZ requirements: (1) the citation count needs to change from 7-day to 30-day, (2) the top-5 queries section exists but is buried in the AI Distribution Intelligence block rather than being a focused, prominent card, (3) there is **no** percentile rank calculation -- this is the only genuinely new logic needed, and (4) these need to be consolidated into a single, visually cohesive "AI Visibility" card rather than scattered across separate dashboard sections.

**Primary recommendation:** Create one new DB function (`get_citation_percentile`) and refactor the existing dashboard HTML to consolidate citation count (30-day), top-5 queries, and percentile rank into a single card component. This is a UI reshaping + one new query, not a greenfield build.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| AIVIZ-01 | Maker sees 30-day citation count on dashboard | `get_total_agent_citations(db, maker_id, days=30)` already works -- just change `days=7` to `days=30` in the dashboard handler (line 89) |
| AIVIZ-02 | Maker sees top 5 search queries triggering their tool | `get_maker_query_intelligence()` already returns top-15 queries. Limit to 5 in the new card and surface prominently |
| AIVIZ-03 | Citation percentile rank within category | **NEW**: Needs a `get_citation_percentile(db, maker_id)` function that compares 30-day citations against all tools in the same category |
| AIVIZ-04 | AI Visibility card integrated into maker dashboard | Existing elements are scattered -- consolidate into one card matching the design system |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | existing | Route handlers, HTMLResponse | Already in use, no additions needed |
| aiosqlite | existing | Async SQLite queries | Already in use, no additions needed |
| Python f-strings | N/A | HTML template rendering | Project convention -- no Jinja2, no React |

### Supporting
No new libraries needed. This phase is pure application code using existing dependencies.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Raw SQL percentile | Window functions (PERCENT_RANK) | SQLite supports window functions since 3.25.0 (2018). USE window functions -- cleaner than manual calculation |

**Installation:**
```bash
# No new packages needed
```

## Architecture Patterns

### Recommended Project Structure
No new files needed. All changes go in existing files:
```
src/indiestack/
  db.py              # Add get_citation_percentile() function (~20 lines)
  routes/dashboard.py # Modify dashboard_overview() to use 30-day window and render new card
```

### Pattern 1: DB Query Function in db.py
**What:** All SQL lives in `db.py` as async functions. Route handlers never contain raw SQL.
**When to use:** Always -- this is the project convention.
**Example:**
```python
# Source: db.py existing pattern (lines 1877-1886)
async def get_citation_percentile(db: aiosqlite.Connection, maker_id: int, days: int = 30) -> dict:
    """Get percentile rank of a maker's tools within their categories (30-day citations)."""
    cursor = await db.execute("""
        WITH tool_citations AS (
            SELECT t.id, t.name, t.category_id,
                   COUNT(ac.id) as cite_count
            FROM tools t
            LEFT JOIN agent_citations ac ON ac.tool_id = t.id
                AND ac.created_at >= datetime('now', ?)
            WHERE t.status = 'approved'
            GROUP BY t.id
        ),
        ranked AS (
            SELECT id, name, category_id, cite_count,
                   PERCENT_RANK() OVER (PARTITION BY category_id ORDER BY cite_count) as pct_rank
            FROM tool_citations
        )
        SELECT r.name, r.cite_count, CAST(r.pct_rank * 100 AS INTEGER) as percentile
        FROM ranked r
        JOIN tools t ON r.id = t.id
        WHERE t.maker_id = ?
        ORDER BY r.cite_count DESC
        LIMIT 1
    """, (f'-{days} days', maker_id))
    row = await cursor.fetchone()
    if row:
        return {'name': row['name'], 'citations': row['cite_count'], 'percentile': row['percentile']}
    return {'name': '', 'citations': 0, 'percentile': 0}
```

### Pattern 2: Dashboard Card HTML (Python f-string)
**What:** Cards use `class="card"` with inline styles matching design tokens from `components.py`.
**When to use:** Any new dashboard UI element.
**Example:**
```python
# Source: dashboard.py lines 762-778 (existing stat cards pattern)
# Stat cards use a 4-column grid:
# <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;">
#     <div class="card" style="text-align:center;padding:20px;">
#         <div style="color:var(--ink-muted);font-size:13px;">Label</div>
#         <div style="font-family:var(--font-display);font-size:28px;...">{value}</div>
#     </div>
# </div>

# Larger section cards use:
# <div class="card" style="padding:24px;">
#     <h3 style="font-family:var(--font-display);font-size:18px;...">Title</h3>
#     <p style="color:var(--ink-muted);font-size:14px;...">Description</p>
#     {content}
# </div>
```

### Pattern 3: Data fetching in dashboard_overview()
**What:** All data is fetched at the top of the handler, then HTML is assembled at the bottom.
**When to use:** Following the existing dashboard_overview pattern.
**Example:**
```python
# Existing pattern (dashboard.py lines 88-89):
agent_citations = await get_total_agent_citations(db, maker_id, days=7) if maker_id else 0
# Change to:
agent_citations_30d = await get_total_agent_citations(db, maker_id, days=30) if maker_id else 0
```

### Anti-Patterns to Avoid
- **Raw SQL in route handlers:** All queries go through db.py functions. Never put SQL directly in dashboard.py.
- **New template engine:** Do NOT introduce Jinja2 or any template library. Use Python f-strings per project convention.
- **New CSS files:** All styles are inline or in design_tokens(). Do NOT create separate stylesheet files.
- **Client-side rendering:** No JavaScript frameworks. Server-render everything. Minimal vanilla JS only for interactions (copy buttons, toggles).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Percentile calculation | Manual Python loop over all tools | SQLite `PERCENT_RANK()` window function | Built into SQLite, handles edge cases (ties, empty sets), runs in a single query |
| Date math | Python timedelta + string formatting | SQLite `datetime('now', '-30 days')` | Already used everywhere in db.py, consistent with existing queries |
| Number formatting | Custom formatting functions | f-string formatting or existing `format_price()` pattern | Keep it simple |

**Key insight:** This phase requires almost zero new infrastructure. The data pipeline (MCP citations -> agent_citations table -> dashboard) is fully operational. We are reshaping existing data presentation.

## Common Pitfalls

### Pitfall 1: Percentile Rank Edge Cases
**What goes wrong:** A maker with 0 citations in a category where all tools have 0 citations would show "100th percentile" (PERCENT_RANK returns 0 for the first row in a partition, and if all are tied, all get 0).
**Why it happens:** PERCENT_RANK returns 0.0 for all tied values (everyone is at rank 0 out of N).
**How to avoid:** Handle the "all zeros" case: if a maker's citation count is 0, display "No data yet" instead of a percentile number. Check `cite_count > 0` before showing percentile.
**Warning signs:** Percentile showing 0% or 100% for tools with no citations.

### Pitfall 2: N+1 Query Problem
**What goes wrong:** Calling `get_total_agent_citations()` per-tool instead of aggregating in one query.
**Why it happens:** Natural tendency to loop over tools.
**How to avoid:** The existing `get_total_agent_citations()` already aggregates across all maker tools. The new percentile function should also operate on the full category in one query.
**Warning signs:** Dashboard page load > 200ms.

### Pitfall 3: Mismatched Time Windows
**What goes wrong:** Citation count uses 30-day window but query intelligence uses 30-day window from a different function, or the stat card still shows 7-day.
**Why it happens:** Multiple functions with different `days` defaults.
**How to avoid:** Ensure all three data points (count, queries, percentile) use the same 30-day window. Update the stat card label from "(7 days)" to "(30 days)".
**Warning signs:** Numbers not adding up between the card summary and the detail view.

### Pitfall 4: Breaking Existing Dashboard Layout
**What goes wrong:** Adding the new AI Visibility card breaks the 4-column stat grid or pushes content below the fold.
**Why it happens:** The existing grid has exactly 4 items (Tools, Upvotes, Tokens Saved, Agent Recs).
**How to avoid:** Two options: (a) Replace the existing "Agent Recs" stat card with a richer AI Visibility card below the grid, or (b) keep the stat card as-is and add a new detailed card section. Option (b) is safer -- it preserves the overview grid and adds detail below.
**Warning signs:** Grid columns wrapping unexpectedly on mobile.

## Code Examples

### Existing citation count fetch (dashboard.py line 89)
```python
# Current: 7-day window
agent_citations = await get_total_agent_citations(db, maker_id, days=7) if maker_id else 0

# Change to: 30-day window for AIVIZ-01
agent_citations_30d = await get_total_agent_citations(db, maker_id, days=30) if maker_id else 0
```

### Existing query intelligence (dashboard.py line 197)
```python
# Already fetches top queries -- just limit to 5 for the card
queries = await get_maker_query_intelligence(db, user['maker_id'], days=30)
top_5_queries = queries[:5]  # AIVIZ-02
```

### Existing stat card grid (dashboard.py lines 761-778)
```python
# The 4th card already shows agent citations:
<div class="card" style="text-align:center;padding:20px;">
    <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{agent_citations}</div>
    <div style="font-size:13px;color:var(--ink-muted);margin-top:4px;">Agent Recs<br>
        <span style="font-size:11px;opacity:0.7;">(7 days)</span></div>
</div>
# Update to 30-day and optionally add percentile subtitle
```

### AI Distribution Intelligence section (dashboard.py lines 249-275)
```python
# This existing section has queries table + agent breakdown + sparkline
# For AIVIZ-04: Extract the top-5 queries and percentile into a new focused card
# placed between the stat grid and the funnel analytics
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No AI citation tracking | agent_citations table + /api/cite endpoint | Already implemented | Data pipeline complete |
| No query intelligence | search_logs with top_result_slug tracking | Already implemented | Can trace queries to tools |
| 7-day citation window | Change to 30-day window | This phase | Matches AIVIZ-01 requirement |
| Scattered AI intel | Consolidated AI Visibility card | This phase | Single card for AIVIZ-04 |

**Deprecated/outdated:**
- Nothing deprecated. All existing code is additive.

## Open Questions

1. **Should the existing "AI Distribution Intelligence" section remain after adding the new AI Visibility card?**
   - What we know: The existing section shows agent breakdown and sparkline trend (30-day). The new card will show citation count, top-5 queries, and percentile.
   - What's unclear: Whether having both creates redundancy.
   - Recommendation: Keep both. The AI Visibility card is the "at a glance" summary (AIVIZ requirements). The existing AI Distribution Intelligence section is the detailed deep-dive. They serve different purposes.

2. **What happens when a maker has tools in multiple categories?**
   - What we know: The percentile function partitions by category_id. A maker might have tools across categories.
   - What's unclear: Should we show one percentile (best tool) or one per tool?
   - Recommendation: Show the best-performing tool's percentile for the overview card. The query already uses `ORDER BY cite_count DESC LIMIT 1`.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | smoke_test.py (custom urllib-based, no pytest) |
| Config file | None -- standalone script |
| Quick run command | `py smoke_test.py` (requires running server) |
| Full suite command | `py smoke_test.py` (37 endpoints, requires running server) |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AIVIZ-01 | 30-day citation count appears on dashboard | smoke (auth-gated) | Manual: login, check /dashboard for "30 days" label and citation number | No -- dashboard is auth-gated, smoke_test.py does not test authenticated pages |
| AIVIZ-02 | Top 5 queries shown in AI Visibility card | smoke (auth-gated) | Manual: check /dashboard for queries table with <= 5 rows | No |
| AIVIZ-03 | Percentile rank shown in card | unit (DB function) | `py -c "import asyncio; from indiestack.db import *; ..."` | No |
| AIVIZ-04 | AI Visibility card renders on dashboard | smoke (auth-gated) | Manual: visual check of /dashboard layout | No |

### Sampling Rate
- **Per task commit:** `py -m py_compile src/indiestack/db.py src/indiestack/routes/dashboard.py` (syntax check)
- **Per wave merge:** `py smoke_test.py` (requires local server running)
- **Phase gate:** Syntax check all modified files + visual check of /dashboard while logged in as maker

### Wave 0 Gaps
- [ ] No unit test infrastructure exists (no pytest, no test directory). The project uses only smoke_test.py against a live server.
- [ ] Dashboard pages are auth-gated and not covered by smoke_test.py.
- [ ] Recommendation: Do NOT introduce pytest for this phase -- it would be scope creep. Validate with syntax checks + manual smoke testing, consistent with how the project has always been validated.

## Sources

### Primary (HIGH confidence)
- `src/indiestack/db.py` lines 1129-1144 -- agent_citations table schema (id, tool_id, agent_name, context, created_at)
- `src/indiestack/db.py` lines 1843-1886 -- existing citation query functions (log, bulk log, counts by maker, total)
- `src/indiestack/db.py` lines 5014-5097 -- maker query intelligence, agent breakdown, daily trend functions
- `src/indiestack/routes/dashboard.py` lines 56-806 -- full dashboard_overview handler with existing AI intel section
- `src/indiestack/main.py` lines 1560-1577 -- /api/cite endpoint
- `src/indiestack/routes/components.py` lines 1-80 -- design tokens (CSS variables)

### Secondary (MEDIUM confidence)
- SQLite PERCENT_RANK() window function: available since SQLite 3.25.0 (2018-09-15). IndieStack runs on Python 3.11 which bundles SQLite 3.39+.

### Tertiary (LOW confidence)
- None. All findings are from direct codebase inspection.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new libraries, all existing code
- Architecture: HIGH - follows established patterns visible in codebase
- Pitfalls: HIGH - identified from direct code analysis of edge cases

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable -- this is internal application code, not external APIs)

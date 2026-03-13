# Phase 2: Compatibility Graph - Research

**Researched:** 2026-03-13
**Domain:** SQLite schema extension, FastAPI route modification, Python string HTML templates
**Confidence:** HIGH

## Summary

Phase 2 adds community-driven compatibility reporting to IndieStack. The existing codebase already has a `tool_pairs` table with 40+ seed pairs, a `get_verified_pairs()` query function, and a "Works Well With" display section on tool detail pages. The work extends this foundation with: (1) user-facing "I use this with..." reporting, (2) confirmation counts displayed per pairing, and (3) a "compatible with [Tool X]" filter on the explore page.

This is a straightforward extension of existing patterns. No new libraries are needed -- everything uses the existing FastAPI + aiosqlite + Python string HTML stack. The main complexity is in the explore page filter (joining tool_pairs into the existing faceted query) and preventing abuse of the reporting endpoint (rate limiting, requiring login).

**Primary recommendation:** Extend the existing `tool_pairs` table with a `user_id` column for tracking who reported each pair, add a `user_tool_pair_reports` junction table for per-user confirmation tracking, modify `get_verified_pairs()` to return richer data, add a POST endpoint for reporting, and extend `explore_tools()` with a `compatible_with` parameter.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| COMPAT-01 | Tool detail page shows "Confirmed Works With" section listing empirically-reported compatible tools | Existing `get_verified_pairs()` and "Works Well With" HTML block in tool.py:679-710 already do this. Extend to show confirmation counts per pair and use "Confirmed Works With" heading. |
| COMPAT-02 | User can report a new compatibility pairing via one-click "I use this with..." button on tool page | New POST endpoint `/tool/{slug}/compatible` + tool search/autocomplete UI. Requires login (request.state.user). Uses existing `record_tool_pair()` in db.py:2689. |
| COMPAT-03 | Compatibility pair count is visible on each pairing (e.g., "47 makers confirmed") | `success_count` column already exists in `tool_pairs`. Display it in the "Confirmed Works With" section alongside each paired tool name. |
| COMPAT-04 | Explore page supports "compatible with [Tool X]" filter | Add `compatible_with` parameter to `explore_tools()` that joins against `tool_pairs` table. Add UI dropdown/search in explore page filter bar. |
</phase_requirements>

## Standard Stack

### Core (Already in Project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | current | Web framework, route handlers | Already used throughout |
| aiosqlite | current | Async SQLite access | Already used for all DB operations |
| Python f-strings | N/A | HTML templating | Project convention -- no template engines |

### Supporting (Already in Project)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| html.escape | stdlib | XSS prevention | All user-provided text in HTML output |
| urllib.parse | stdlib | URL encoding/parsing | Query param construction, favicon domain extraction |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Tool slug autocomplete via API | Static dropdown of all tools | API is better -- 3,095 tools is too many for a dropdown. Use existing `/api/tools/search?q=` endpoint. |
| New junction table for per-user reports | Just increment success_count | Junction table prevents duplicate reports and enables "you already confirmed this" UX |

**Installation:**
No new packages needed. Everything uses existing dependencies.

## Architecture Patterns

### Existing Code to Modify
```
src/indiestack/
  db.py              # Add: user_tool_pair_reports table, get_compatible_tools_for_explore(), modify get_verified_pairs()
  routes/
    tool.py          # Add: POST /tool/{slug}/compatible endpoint, modify "Works Well With" display
    explore.py       # Add: compatible_with query param, UI filter element
    components.py    # (Optional) Extract compatibility section into reusable function
```

### Pattern 1: Database Schema Extension
**What:** Add a `user_tool_pair_reports` table to track which users confirmed which pairings, preventing duplicates and enabling count accuracy.
**When to use:** Whenever user actions need deduplication (same pattern as upvotes with ip_hash, reviews with UNIQUE(tool_id, user_id), wishlists with UNIQUE(user_id, tool_id)).

```python
# In db.py init_db():
await db.execute("""
    CREATE TABLE IF NOT EXISTS user_tool_pair_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL REFERENCES users(id),
        tool_a_slug TEXT NOT NULL,
        tool_b_slug TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, tool_a_slug, tool_b_slug)
    )
""")
```

### Pattern 2: Authenticated POST Endpoint (existing project pattern)
**What:** POST endpoints that require login follow a consistent pattern in this codebase.
**Example from tool.py review submission (line 825):**

```python
@router.post("/tool/{slug}/review")
async def submit_review(request: Request, slug: str, ...):
    user = request.state.user
    if not user:
        return RedirectResponse(f"/login?next=/tool/{slug}", status_code=303)
    # ... do work ...
```

### Pattern 3: Explore Page Filter Extension
**What:** The explore page uses `explore_tools()` in db.py with keyword params for each filter. Add `compatible_with` slug param.
**How it works:** Each filter adds a WHERE condition. A compatibility filter would add a subquery join:

```python
if compatible_with:
    conditions.append("""
        t.slug IN (
            SELECT CASE WHEN tp.tool_a_slug = ? THEN tp.tool_b_slug ELSE tp.tool_a_slug END
            FROM tool_pairs tp
            WHERE tp.tool_a_slug = ? OR tp.tool_b_slug = ?
        )
    """)
    params.extend([compatible_with, compatible_with, compatible_with])
```

### Anti-Patterns to Avoid
- **Don't use tool IDs for pairs:** The existing `tool_pairs` table uses slugs, not IDs. Stay consistent -- slugs are stable identifiers in this codebase.
- **Don't build a separate autocomplete endpoint:** Reuse the existing `/api/tools/search?q=` endpoint for the "I use this with..." tool picker.
- **Don't add WebSocket/real-time updates:** Out of scope per REQUIREMENTS.md. Simple form submission with page reload or AJAX is fine.
- **Don't allow anonymous compatibility reports:** Require login to prevent spam. The upvote system uses IP hashing for anonymous actions, but compatibility reports are higher-signal and should be tied to user accounts.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tool search/autocomplete | Custom search widget | Existing `/api/tools/search?q=` API endpoint | Already returns tool name + slug, handles fuzzy matching |
| Slug normalization | Custom pair ordering | Existing `sorted_pair()` pattern from pair_generator.py | Already establishes alphabetical slug ordering for UNIQUE constraint |
| User authentication check | Custom auth middleware | `request.state.user` (set by db_middleware in main.py) | Already populated on every request |
| Favicon display | Custom icon system | Google Favicons API (already used in tool.py:697) | `https://www.google.com/s2/favicons?domain={domain}&sz=16` |

**Key insight:** The existing codebase already has 80% of the infrastructure. The `tool_pairs` table, `get_verified_pairs()`, `record_tool_pair()`, and "Works Well With" HTML section all exist. This phase is about extending these with user-facing reporting and explore integration, not building from scratch.

## Common Pitfalls

### Pitfall 1: Duplicate Pair Ordering
**What goes wrong:** Inserting (tool_a="stripe", tool_b="auth0") and (tool_a="auth0", tool_b="stripe") as separate rows.
**Why it happens:** The UNIQUE constraint is on (tool_a_slug, tool_b_slug), not on the unordered pair.
**How to avoid:** Always sort slugs alphabetically before inserting, as `record_tool_pair()` already does: `a, b = sorted([slug_a, slug_b])`.
**Warning signs:** Duplicate pairs appearing in the "Works With" section.

### Pitfall 2: Self-Pairing
**What goes wrong:** A user reports a tool as compatible with itself.
**Why it happens:** No validation preventing tool_a_slug == tool_b_slug.
**How to avoid:** Check `slug_a != slug_b` before inserting. Return a user-friendly error.
**Warning signs:** A tool appearing in its own "Works With" section.

### Pitfall 3: Explore Filter Performance
**What goes wrong:** Slow queries when filtering by compatibility on the explore page with 3,095 tools.
**Why it happens:** The subquery join against tool_pairs can be slow without an index.
**How to avoid:** Ensure indexes on `tool_pairs(tool_a_slug)` and `tool_pairs(tool_b_slug)`. SQLite will use these for the IN subquery.
**Warning signs:** Explore page load time increasing significantly when compatibility filter is active.

### Pitfall 4: Counting Inflation
**What goes wrong:** A single user can inflate success_count by repeatedly confirming the same pair.
**Why it happens:** `record_tool_pair()` uses `ON CONFLICT DO UPDATE SET success_count = success_count + 1` without per-user deduplication.
**How to avoid:** Use `user_tool_pair_reports` junction table. Only increment `success_count` when a NEW user confirms (check for existing report first, or use ON CONFLICT DO NOTHING + check rowcount).
**Warning signs:** Pairs with suspiciously high counts from few users.

### Pitfall 5: Non-Existent Tool Slugs
**What goes wrong:** User reports compatibility with a slug that doesn't exist in the tools table.
**Why it happens:** `tool_pairs` uses slugs as TEXT, not foreign keys -- no referential integrity.
**How to avoid:** Validate both slugs exist as approved tools before inserting. Query `tools` table first.
**Warning signs:** "Works With" section showing slugs that link to 404 pages.

## Code Examples

### Existing: Get Verified Pairs (db.py:2675)
```python
async def get_verified_pairs(db: aiosqlite.Connection, slug: str) -> list:
    """Get tools verified to work well with this tool."""
    cursor = await db.execute("""
        SELECT CASE WHEN tp.tool_a_slug = ? THEN tp.tool_b_slug ELSE tp.tool_a_slug END as pair_slug,
               tp.success_count, tp.verified,
               t.url as pair_url
        FROM tool_pairs tp
        LEFT JOIN tools t ON t.slug = CASE WHEN tp.tool_a_slug = ? THEN tp.tool_b_slug ELSE tp.tool_a_slug END
        WHERE (tp.tool_a_slug = ? OR tp.tool_b_slug = ?)
        ORDER BY tp.success_count DESC
    """, (slug, slug, slug, slug))
    return [dict(r) for r in await cursor.fetchall()]
```

### Existing: Record Tool Pair (db.py:2689)
```python
async def record_tool_pair(db: aiosqlite.Connection, slug_a: str, slug_b: str, source: str = "agent"):
    """Record that two tools were used together. Increments success_count if exists."""
    a, b = sorted([slug_a, slug_b])
    await db.execute("""
        INSERT INTO tool_pairs (tool_a_slug, tool_b_slug, source)
        VALUES (?, ?, ?)
        ON CONFLICT(tool_a_slug, tool_b_slug) DO UPDATE SET success_count = success_count + 1
    """, (a, b, source))
    await db.commit()
```

### Existing: Tool Detail "Works Well With" Display (tool.py:679-710)
```python
# Build "Works Well With" section from compatibility pairs
compatible_html = ''
try:
    _pairs = await get_verified_pairs(db, slug)
    if _pairs:
        _pair_items = ''
        for _p in _pairs[:8]:  # limit to 8
            _p_slug = escape(str(_p.get('pair_slug', '')))
            _p_count = int(_p.get('success_count', 0))
            # ... renders pill-shaped links with favicons ...
        compatible_html = f'''<div style="...">
            <h3 ...>Works Well With</h3>
            <div style="display:flex;flex-wrap:wrap;gap:8px;">{_pair_items}</div>
        </div>'''
except Exception:
    pass
```

### New: Compatibility Report Endpoint (pattern)
```python
@router.post("/tool/{slug}/compatible")
async def report_compatible(request: Request, slug: str, pair_slug: str = Form(...)):
    user = request.state.user
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)
    db = request.state.db

    # Validate both tools exist
    tool = await get_tool_by_slug(db, slug)
    pair_tool = await get_tool_by_slug(db, pair_slug)
    if not tool or not pair_tool:
        return JSONResponse({"error": "Tool not found"}, status_code=404)
    if slug == pair_slug:
        return JSONResponse({"error": "Cannot pair a tool with itself"}, status_code=400)

    # Sort slugs for consistent ordering
    a, b = sorted([slug, pair_slug])

    # Check if user already reported this pair
    existing = await db.execute(
        "SELECT 1 FROM user_tool_pair_reports WHERE user_id=? AND tool_a_slug=? AND tool_b_slug=?",
        (user['id'], a, b))
    if await existing.fetchone():
        return JSONResponse({"error": "Already confirmed"}, status_code=409)

    # Record the report
    await db.execute(
        "INSERT INTO user_tool_pair_reports (user_id, tool_a_slug, tool_b_slug) VALUES (?,?,?)",
        (user['id'], a, b))
    # Upsert into tool_pairs
    await db.execute("""
        INSERT INTO tool_pairs (tool_a_slug, tool_b_slug, source, success_count)
        VALUES (?, ?, 'user', 1)
        ON CONFLICT(tool_a_slug, tool_b_slug) DO UPDATE SET success_count = success_count + 1
    """, (a, b))
    await db.commit()
    return JSONResponse({"ok": True, "pair": pair_slug})
```

### New: Explore Filter Extension (pattern)
```python
# In explore_tools() function, add parameter:
# compatible_with: str = ""

if compatible_with:
    conditions.append("""
        t.slug IN (
            SELECT CASE WHEN tp.tool_a_slug = ? THEN tp.tool_b_slug ELSE tp.tool_a_slug END
            FROM tool_pairs tp
            WHERE tp.tool_a_slug = ? OR tp.tool_b_slug = ?
        )
    """)
    params.extend([compatible_with, compatible_with, compatible_with])
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual seed pairs only | Seed + pair_generator.py auto-generation | Already in codebase | 1,272 pairs exist but no user-contributed ones |
| No success_count display | success_count tracked but not shown to users | Already in DB | Foundation exists for "N makers confirmed" display |
| No explore filter for compatibility | No filter exists | Current gap | COMPAT-04 fills this gap |

**Key existing data:**
- `tool_pairs` table has 1,272+ auto-generated pairs plus ~40 seed pairs
- `success_count` defaults to 1 for all existing pairs (no real user confirmations yet)
- Sources in table: "manual" (seeds), "framework_affinity", "complementary_category", "same_category_popular", "agent"

## Open Questions

1. **Should existing auto-generated pairs show confirmation counts?**
   - What we know: All existing pairs have success_count=1 (auto-generated, not user-confirmed)
   - What's unclear: Whether "1 maker confirmed" is misleading for auto-generated pairs
   - Recommendation: Only show count for pairs with success_count >= 2, or only for source="user" pairs. Alternatively, show "Suggested" vs "Confirmed by N makers" labels.

2. **Rate limiting on compatibility reports**
   - What we know: No rate limiting exists on the review POST endpoint either
   - What's unclear: Whether users could spam compatibility reports
   - Recommendation: The UNIQUE constraint on user_tool_pair_reports prevents duplicate reports per user per pair. A user can report at most one confirmation per pair. No additional rate limiting needed.

3. **Tool search UX for "I use this with..."**
   - What we know: `/api/tools/search?q=` returns JSON with tool names and slugs
   - What's unclear: Exact UI -- modal, inline dropdown, separate page?
   - Recommendation: Inline search input with debounced fetch to `/api/tools/search?q=`, showing results in a dropdown. Lightweight, no new dependencies. Similar to how search works on the landing page.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | smoke_test.py (custom urllib-based, no pytest) |
| Config file | smoke_test.py at project root |
| Quick run command | `py smoke_test.py http://localhost:8000` |
| Full suite command | `py smoke_test.py http://localhost:8000` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| COMPAT-01 | Tool page shows "Confirmed Works With" section | smoke | Add content check: GET /tool/supabase contains "Confirmed Works With" | Needs addition to TESTS |
| COMPAT-02 | POST /tool/{slug}/compatible creates pairing | smoke | Add test: POST /tool/supabase/compatible returns 401 (no auth) | Needs addition to TESTS |
| COMPAT-03 | Pair count visible in "Works With" section | smoke | Content check: "confirmed" text appears in tool page HTML | Needs addition to TESTS |
| COMPAT-04 | Explore page filters by compatible_with | smoke | Add test: GET /explore?compatible_with=supabase returns 200 | Needs addition to TESTS |

### Sampling Rate
- **Per task commit:** `py smoke_test.py http://localhost:8000`
- **Per wave merge:** `py smoke_test.py http://localhost:8000`
- **Phase gate:** Full suite green before verification

### Wave 0 Gaps
- [ ] Add smoke test entries to `TESTS` list in smoke_test.py for COMPAT-01 through COMPAT-04
- [ ] Add content check for "Confirmed Works With" substring on tool page

## Sources

### Primary (HIGH confidence)
- Source code: `src/indiestack/db.py` lines 1244-1254 (tool_pairs schema)
- Source code: `src/indiestack/db.py` lines 2675-2697 (get_verified_pairs, record_tool_pair)
- Source code: `src/indiestack/routes/tool.py` lines 679-710 (existing "Works Well With" display)
- Source code: `src/indiestack/routes/explore.py` lines 16-81 (explore page filter pattern)
- Source code: `src/indiestack/pair_generator.py` (auto-generation strategies, 1272 pairs)
- Source code: `src/indiestack/db.py` lines 3562-3622 (explore_tools query builder)

### Secondary (MEDIUM confidence)
- REQUIREMENTS.md: COMPAT-01 through COMPAT-04 definitions
- ROADMAP.md: Phase 2 success criteria

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new libraries, all existing code patterns
- Architecture: HIGH - extending well-established patterns (table creation, route handlers, explore filters)
- Pitfalls: HIGH - identified from reading actual code, not speculation

**Research date:** 2026-03-13
**Valid until:** 2026-04-13 (stable codebase, no external dependencies changing)

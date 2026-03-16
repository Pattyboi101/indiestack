# MCP Intelligence Layer — Design Document

> **Strategic context:** StackShare has 7K tools and 32M data points but zero MCP/agent integration. This is our window to build the intelligence layer they can't replicate without rebuilding their entire platform. Every `report_outcome`, every `confirm_integration`, every stack built through our MCP is data they don't have and can't easily get.

**Goal:** Upgrade the IndieStack MCP server from a catalog search into a smart recommendation engine with super filters, compatibility graph, gap intelligence, and conflict warnings.

**Architecture:** Extend existing `find_tools` with 11 new optional filter params, add one new `find_compatible` MCP tool for compatibility graph exploration, mine existing `search_logs` for demand gaps, and seed a conflict warning system. Two new tables (`verified_stacks`, `tool_conflicts`), one new column (`search_logs.normalized_query`), and one pair normalization migration.

---

## Part A: Super Filters on `find_tools`

### Current State
`find_tools(query, category, source_type, offset)` — 4 params. Calls `/api/tools/search` which uses FTS5 + `quality_score` ranking. Source type is the only real filter.

### New Parameters (all optional)

| Parameter | Type | DB Column / Query | Description |
|-----------|------|-------------------|-------------|
| `compatible_with` | string (slug) | `tool_pairs` subquery | Only tools known to work with this tool |
| `price` | string | `price_pence` | `"free"` (NULL), `"paid"` (>0) |
| `min_success_rate` | int (0-100) | `agent_actions` subquery | Soft filter — falls back to unfiltered if <3 results |
| `min_confidence` | string | outcome count threshold | `"low"` (1+), `"medium"` (5+), `"high"` (20+). Soft filter. |
| `has_api` | bool | `api_type IS NOT NULL` | Only tools with documented API type |
| `language` | string | `github_language` | `"python"`, `"javascript"`, etc. Code tools only. |
| `tags` | string (CSV) | FTS match on tags field | `"oauth,social-login"` — uses FTS index, not LIKE |
| `exclude` | string (CSV slugs) | `slug NOT IN (...)` | Skip already-evaluated tools |
| `health` | string | `health_status` | `"active"`, `"stale"` — uses real schema values |
| `min_stars` | int | `github_stars >= ?` | Code tools only |
| `sort` | string | ORDER BY | `"relevance"` (default), `"stars"`, `"upvotes"`, `"newest"`, `"success_rate"` |

Total: **15 params** (4 existing + 11 new). All new params optional — simple queries unchanged.

### Soft Filters (success_rate, confidence)

When `min_success_rate` or `min_confidence` returns <3 results, the response includes the filtered results PLUS unfiltered fallback with a note:

```
Found 1 tool matching success_rate >= 80%. Showing all results:
[filtered result marked with ✓ success_rate badge]
[unfiltered results without badge]
```

This prevents empty results while the outcome data is sparse.

### compatible_with SQL

```sql
AND t.slug IN (
    SELECT CASE WHEN tool_a_slug = ? THEN tool_b_slug ELSE tool_a_slug END
    FROM tool_pairs
    WHERE (tool_a_slug = ? OR tool_b_slug = ?)
      AND success_count >= 1
)
```

### success_rate Sort

To avoid small-sample bias (1 outcome at 100% beats 50 at 90%), sort by `success_count * success_rate / 100` — rewards both volume and quality.

### API Changes

`/api/tools/search` gets all 11 new query params, passed through from MCP `find_tools`. Each becomes an optional WHERE clause or ORDER BY modifier.

---

## Part B: Compatibility Graph

### New MCP Tool: `find_compatible`

```python
find_compatible(
    slug: str,                          # Required: tool to find companions for
    category: Optional[str] = None,     # Filter companions by category
    min_success_count: int = 1          # Minimum integration reports
) -> str
```

**Returns** compatible tools grouped by category, sorted by success_count, with:
- Integration report count and health status per companion
- Inferred stacks (triangles in the pair graph) at the bottom
- Overlap warnings for same-category companions
- Conflict warnings from `tool_conflicts` table

**Example response:**
```
## Tools compatible with Supabase (12 reported pairs)

### Authentication (3)
- **Clerk** — 8 integrations reported, Active ✓
- **Lucia Auth** — 5 integrations reported, Active ✓
- **Hanko** — 2 integrations reported, Active ✓

### Payments (2)
- **Stripe** — 12 integrations reported, Active ✓
- **Polar** — 3 integrations reported, Active ✓
  ⚠️ Overlap: Stripe and Polar both in Payments — check they serve different needs

🔗 Verified stack: Supabase + Stripe + Resend (reported together 4 times)
```

**Language:** "reported" not "verified" — based on `success_count`, not the `verified` column.

### API Endpoint

`GET /api/tools/{slug}/compatible?category=&min_success_count=1`

Returns JSON array of compatible tools with metadata. MCP tool formats as markdown.

### Pair Normalization

Normalize `tool_pairs` so `tool_a_slug < tool_b_slug` alphabetically (canonical direction). Migration:

```sql
UPDATE tool_pairs
SET tool_a_slug = tool_b_slug, tool_b_slug = tool_a_slug
WHERE tool_a_slug > tool_b_slug;
```

Add CHECK constraint: `CHECK(tool_a_slug < tool_b_slug)`. Update `record_tool_pair()` to sort before insert.

Simplifies triangle queries — no bidirectional handling needed per edge.

### Stack Inference (Triangles)

After pair normalization, find triangles:

```sql
SELECT p2.tool_b_slug as tool_c
FROM tool_pairs p1
JOIN tool_pairs p2 ON p1.tool_b_slug = p2.tool_a_slug
JOIN tool_pairs p3 ON p3.tool_a_slug = p1.tool_a_slug AND p3.tool_b_slug = p2.tool_b_slug
WHERE p1.tool_a_slug = ?
  AND p1.success_count >= 1
  AND p2.success_count >= 1
  AND p3.success_count >= 1
```

Returns sets of 3 tools all mutually compatible. Surface as "Verified stacks" in `find_compatible` response.

### New Table: `verified_stacks`

```sql
CREATE TABLE IF NOT EXISTS verified_stacks (
    id INTEGER PRIMARY KEY,
    tool_slugs TEXT NOT NULL,
    use_case TEXT,
    success_count INTEGER DEFAULT 1,
    source TEXT DEFAULT 'agent',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool_slugs)
);
```

`tool_slugs` is a JSON array, sorted alphabetically for dedup. Populated by:
1. Explicit agent reports via `used_with` on `report_outcome`
2. Triangle inference from pair graph (source='inferred')
3. Manual curation (source='manual')

### New Table: `tool_conflicts`

```sql
CREATE TABLE IF NOT EXISTS tool_conflicts (
    id INTEGER PRIMARY KEY,
    tool_a_slug TEXT NOT NULL,
    tool_b_slug TEXT NOT NULL,
    reason TEXT,
    report_count INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool_a_slug, tool_b_slug)
);
```

Populated by agent `report_outcome` with `incompatible_with` param. Same normalization as pairs (a < b).

### Extend `report_outcome`

Add two optional params:

```python
report_outcome(
    tool_slug: str,
    success: bool,
    notes: Optional[str] = None,
    used_with: Optional[str] = None,          # CSV slugs: "supabase,resend"
    incompatible_with: Optional[str] = None   # slug that conflicted
)
```

- `used_with` + `success=true` → record/increment `verified_stacks` + increment `tool_pairs` for each pair in the set
- `incompatible_with` + `success=false` → record/increment `tool_conflicts`

### Overlap vs Conflict Distinction

- **Overlap** (soft warning): Two compatible tools in the same category. "Both in Payments — check they serve different needs." Auto-detected from category match.
- **Conflict** (hard warning): Agents explicitly reported incompatibility via `tool_conflicts`. "⚠️ Known conflict: 3 agents reported integration issues."

---

## Part C: Blank Search Intelligence

### Layer 1: Gap Detection (Admin)

New function `get_search_gaps(days=30, min_searches=3)`:

```sql
SELECT normalized_query, COUNT(*) as search_count,
       MAX(created_at) as last_searched,
       COUNT(DISTINCT COALESCE(api_key_id, 'anon')) as unique_sources
FROM search_logs
WHERE result_count = 0
  AND created_at > datetime('now', '-' || ? || ' days')
GROUP BY normalized_query
HAVING COUNT(*) >= ?
ORDER BY search_count DESC
LIMIT 50
```

Surface on admin dashboard as "Demand Gaps" panel.

### Layer 2: Maker-Facing Gaps

On submit page (`/submit`) and maker dashboard, show top 5 unfilled gaps:

> "Agents searched for **headless CMS** 47 times this month. No tools listed yet — submit yours?"

Only gaps with `search_count >= 5` surfaced to makers.

### Layer 3: MCP Zero-Result Enrichment

When `find_tools` returns zero results, enhance the response:

```
No tools found for "headless cms svelte"

📊 Market gap: searched 47 times in 30 days by 12 different agents
💡 Try browsing the Developer Tools category for related options
💡 Know a tool that fits? Use publish_tool() to submit it
```

Category suggestion via FTS match on category names — simple, no fuzzy search needed.

### New Column: `search_logs.normalized_query`

```sql
ALTER TABLE search_logs ADD COLUMN normalized_query TEXT;
CREATE INDEX idx_search_logs_normalized ON search_logs(normalized_query);
```

Normalization on insert: lowercase, strip punctuation, collapse whitespace, remove stop words ("tool", "for", "best", "top", "the", "a"). Done in Python `log_search()` function.

Backfill existing rows:
```sql
UPDATE search_logs SET normalized_query = LOWER(TRIM(query)) WHERE normalized_query IS NULL;
```

(Python-side normalization applied going forward; SQL backfill is approximate.)

---

## Part D: Conflict Warning Foundation

### v1 Scope (this release)

1. **`tool_conflicts` table** seeded by agent reports via `incompatible_with` param
2. **Same-category overlap** warnings in `find_compatible` and `build_stack` responses
3. **Framework mismatch** check: if both tools have `frameworks_tested` and they don't intersect, warn

### Not in v1

- Automated GitHub repo cloning / dependency tree analysis
- npm/pip conflict detection bot
- Automated template build testing

These are future work once the signal collection infrastructure exists.

---

## Implementation Order

1. **Super filters** — extend `/api/tools/search` + `find_tools` MCP tool with 11 new params
2. **Pair normalization** — migrate tool_pairs to canonical a < b ordering
3. **`find_compatible`** — new MCP tool + API endpoint + stack inference
4. **`verified_stacks` + `tool_conflicts`** — new tables, extend `report_outcome` with `used_with` / `incompatible_with`
5. **Blank search intelligence** — `normalized_query` column, gap detection query, admin panel, maker-facing display, MCP enrichment
6. **Conflict warnings** — overlap + conflict display in `find_compatible` and `build_stack`
7. **MCP version bump + PyPI publish**

---

## Files Modified

| File | Changes |
|------|---------|
| `db.py` | New tables (verified_stacks, tool_conflicts), normalized_query column, search_tools filter params, get_search_gaps(), pair normalization, complete_claim updates |
| `mcp_server.py` | find_tools new params, new find_compatible tool, report_outcome new params, enhanced zero-result response |
| `main.py` | /api/tools/search new query params, /api/tools/{slug}/compatible new endpoint, report_outcome API updates |
| `routes/admin.py` | Demand gaps panel on admin dashboard |
| `routes/submit.py` | Gap signals on submit page |
| `routes/dashboard.py` | Gap signals on maker dashboard |

## Success Criteria

- Agent can call `find_tools(query="auth", compatible_with="supabase", price="free", health="active")` and get filtered results
- Agent can call `find_compatible("supabase")` and see grouped companions with stack inference
- Agent can call `report_outcome("stripe", success=True, used_with="supabase,resend")` and it records the stack
- Admin dashboard shows top demand gaps from zero-result searches
- Makers see gap signals when submitting tools
- Zero-result MCP responses include market gap data and category suggestions

# Stacks Overhaul — Design

**Date:** 2026-03-16
**Status:** Approved
**Depends on:** StackShare replacement Phase 1 (5,031 compatibility pairs — shipped)

## Context

The `/stacks` page is the most underutilised feature in IndieStack. Three separate systems exist (curated stacks, user stacks, verified stacks) but none have data and they don't connect to each other. Meanwhile we just shipped 5,031 compatibility pairs, enhanced comparison pages with agent intelligence, and expanded the sitemap with 2,796 SEO URLs. The stacks page should be the crown jewel that surfaces all of this.

This is Phase 3 of the StackShare replacement strategy — making `/stacks` the living, agent-verified replacement for StackShare's dead community stack sharing.

### Why StackShare's Stacks Failed
- Self-reported: nobody updates their stack profiles
- No quality signal: lists tools without verifying they work together
- No agent integration: invisible to AI dev workflows
- Static snapshots: data rots from day one

### Why IndieStack Stacks Win
- Agent-verified compatibility pairs (5,031 and growing)
- Framework affinity data from `frameworks_tested`
- Health scoring, trust tiers, agent citation counts
- Compatibility matrix showing which tools in a stack actually work together
- Auto-regeneration as new data flows in via `report_outcome`

## Architecture

**Single table, single page, single system.** Enhance the existing `stacks` table with intelligence metadata. Auto-generate stacks from our compatibility data. Rewrite the `/stacks` page with an intelligence-first layout. Enhance MCP tools to return richer stack data.

Three layers on one page:
1. **Discovery** (hero) — stats + prominent Stack Generator link
2. **Auto-generated stacks** — framework stacks + use-case stacks, data-driven
3. **Community** — user-created public stacks + CTA to share yours

## Schema Changes

Add columns to existing `stacks` table (ALTER TABLE ADD COLUMN, safe in SQLite):

| Column | Type | Purpose |
|--------|------|---------|
| `source` | TEXT DEFAULT 'curated' | 'curated' / 'auto-framework' / 'auto-usecase' |
| `framework` | TEXT | e.g. "nextjs", "django" — NULL for use-case stacks |
| `use_case` | TEXT | e.g. "saas-starter" — NULL for framework stacks |
| `replaces_json` | TEXT | JSON array: ["Firebase", "Mailchimp", "GA"] |
| `confidence_score` | REAL DEFAULT 0 | Tiered score from pair data (see scoring model) |
| `total_tokens_saved` | INTEGER DEFAULT 0 | Sum from CATEGORY_TOKEN_COSTS |
| `tool_count_cached` | INTEGER DEFAULT 0 | Denormalized for fast display |
| `generated_at` | TIMESTAMP | When auto-generation ran (NULL for curated) |

No changes to `stack_tools`, `user_stacks`, or `user_stack_tools`.

**IMPORTANT:** Existing curated stacks (source='curated') are never modified by the seed script. The `source` column discriminates auto-generated from hand-curated.

## Seed Script: `scripts/seeds/seed_auto_stacks.py`

### Strategy A: Framework Stacks

1. Query all approved tools with non-empty `frameworks_tested`
2. Group by framework (split comma-separated, lowercase, strip)
3. For each framework with **4+ tools across 2+ categories**:
   a. Collect tools, cross-reference against `tool_pairs` — prioritise tools with pair relationships to others in the group
   b. Filter out tools with no pair connections to any other tool in the stack
   c. Rank by: `trust_weight * 10 + mcp_view_count * 0.1 + pair_count * 2`
   d. Cap at top 8 tools
4. Generate stack metadata (title, description, replaces, confidence, tokens saved)
5. UPSERT into `stacks` table, add tools to `stack_tools`

Expected: ~5-8 framework stacks (next.js, react, vue, svelte, django, rails, laravel, express — depending on which hit the 4-tool threshold).

### Strategy B: Use Case Stacks

**Single-category stacks:** For each NEED_MAPPINGS entry with 3+ strong tools (tools that have pair data), generate a stack: "Auth Stack", "Payments Stack", etc.

**Composite stacks** (cross-category):

| Stack Name | Categories | Emoji |
|---|---|---|
| SaaS Starter | auth + payments + analytics + email | 🚀 |
| API Backend | api-tools + monitoring + developer-tools | ⚡ |
| Indie Marketing | analytics + seo + email-marketing + forms | 📈 |
| Full-Stack Indie | auth + payments + analytics + monitoring + email | 🏗️ |
| Content Platform | cms + seo + analytics + email-marketing | 📝 |
| AI Builder | ai-dev-tools + ai-automation + api-tools + monitoring | 🧠 |

For composites:
1. Pick top 2 tools per category, ranked by pair count + health + citations
2. Cross-reference pairs between categories — prefer tools that have pair connections to tools in other categories within the same stack
3. If the #1 tool in a category has no pairs with any tool in another category, try #2
4. If a category has 0 qualifying tools, skip that category (don't block the whole stack)

### Scoring Model

**Per-pair score (for confidence calculation):**
- Inferred pair exists (success_count = 0): **0.3 points**
- Verified pair (success_count > 0): **0.7 + (0.3 × min(success_count / 10, 1))** — maxes at 1.0
- No pair between two tools: **0 points**
- Conflict in `tool_conflicts`: **-1 point**

**Stack confidence:**
```
confidence = sum(pair_scores) / max_possible_pairs
```
Where `max_possible_pairs = n * (n-1) / 2` for n tools.

This means:
- A stack where every tool has an inferred pair with every other tool = ~30% confidence
- A stack with all verified pairs = ~70-100% confidence
- A stack with conflicts gets penalised

**Per-tool score (for ranking within a stack):**
```
tool_score = (trust_weight × 10) + (mcp_view_count × 0.1) + (pair_count × 2)
```
Where trust_weight: verified=3, tested=2, new=1.

### Idempotency

**CRITICAL:** Must use UPSERT, not INSERT OR REPLACE. INSERT OR REPLACE deletes and re-inserts the row, changing the autoincrement `id` and breaking `stack_tools` foreign key references.

```sql
INSERT INTO stacks (slug, title, description, ...) VALUES (?, ?, ?, ...)
ON CONFLICT(slug) DO UPDATE SET
  title=excluded.title, description=excluded.description,
  confidence_score=excluded.confidence_score, ...
WHERE source != 'curated'
```

The `WHERE source != 'curated'` guard ensures we never overwrite hand-curated stacks.

For `stack_tools`: delete and re-insert for auto-generated stacks on each run. This is safe because auto-generated stacks don't have purchases.

### CLI

```bash
python3 scripts/seeds/seed_auto_stacks.py              # insert into DB
python3 scripts/seeds/seed_auto_stacks.py --dry-run     # preview without inserting
python3 scripts/seeds/seed_auto_stacks.py --verbose      # show scoring breakdown
```

### Pair Query Helper

All pair lookups must sort slugs alphabetically:
```python
def pair_key(a, b):
    return tuple(sorted([a, b]))
```

## Page Design: `/stacks` Rewrite

### Section 1: Hero + Stats Bar

**Headline:** "Stacks That Actually Work"
**Subline:** "Built from X compatibility pairs across Y tools. Every stack is backed by agent-verified data, not self-reported profiles."

Stats bar (queried live from DB):

| Stat | Source |
|------|--------|
| X Compatibility Pairs | `SELECT COUNT(*) FROM tool_pairs` |
| Y Tools Indexed | `SELECT COUNT(*) FROM tools WHERE status='approved'` |
| Z Auto-Generated Stacks | `SELECT COUNT(*) FROM stacks WHERE source LIKE 'auto-%'` |
| W Frameworks Covered | Count distinct frameworks from auto-framework stacks |

### Section 2: Stack Generator (Prominent Link)

**NOT embedded inline** — the codebase uses pure Python f-string templates with no HTMX or JS framework. Embedding a form-submit-and-render-results flow inline would require new frontend tooling. Not worth the complexity.

Instead: a **large hero card** that links to the existing `/stacks/generator` page:

"Build Your Stack — paste your package.json or describe what you're building. We'll find indie tools that work together."

Big, visual, first thing after the stats bar. Links to `/stacks/generator` which already works perfectly.

### Section 3: Framework Stacks

Horizontal row or 3-column grid of stack cards.

Each card shows:
- Framework name as title ("Next.js Stack")
- Tool count badge ("8 tools")
- Confidence bar/percentage
- "Replaces: Firebase, Mailchimp, GA" in small text
- "Saves ~180K tokens" badge
- Top 3-4 tool pixel icons / favicons as preview
- Links to `/stacks/{slug}`

### Section 4: Use Case Stacks

Same card format:
- "SaaS Starter", "API Backend", "Indie Marketing", etc.
- Category icons from NEED_MAPPINGS in a row
- Same metadata: confidence, tokens saved, replaces

### Section 5: Community Stacks

Existing `user_stack_card` component for public user stacks (`is_public=1`).

CTA at bottom: "Share your stack" → `/dashboard/my-stack`

### Responsive Behaviour
- Desktop: 3-column grid
- Tablet (< 900px): 2-column
- Mobile (< 600px): single column

## Stack Detail Page Enhancement: `/stacks/{slug}`

### Header
- Title + emoji + source badge ("Auto-generated from compatibility data" / "Curated by IndieStack")
- Description
- Stats row: tool count | confidence | tokens saved | "Replaces: ..."
- Framework badge if applicable

### Compatibility Matrix

For stacks with ≤ 6 tools, render a visual grid:
```
              Supabase  Resend  PostHog  Stripe
Supabase         —        ✓       ✓       ✓
Resend           ✓        —       ·       ✓
PostHog          ✓        ·       —       ✓
Stripe           ✓        ✓       ✓       —
```
- ✓ Green = verified pair (success_count > 0)
- · Grey = inferred pair (exists but unverified)
- Empty = no pair data
- ✗ Red = known conflict

For stacks with > 6 tools: summary instead — "7 of 10 possible pairs verified compatible."

**Query pattern:** Single query for all pairs in the stack:
```sql
SELECT * FROM tool_pairs
WHERE tool_a_slug IN (slug_set) AND tool_b_slug IN (slug_set)
```
Plus conflicts:
```sql
SELECT * FROM tool_conflicts
WHERE tool_a_slug IN (slug_set) AND tool_b_slug IN (slug_set)
```

### Tool Cards (Enhanced)

Each tool shows:
- Name, tagline, pixel icon / favicon
- Health badge (active/stale/dead) — from `_health_badge()` we already built
- Trust tier badge (verified/tested/new)
- Agent citations: "Recommended by agents X times" (from `mcp_view_count`)
- Category + what it replaces
- Price
- Compatibility count: "Compatible with 4/5 other tools in this stack"

**Performance:** Batch-query success rates at the top of the page render:
```sql
SELECT tool_slug,
       SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as wins,
       COUNT(*) as total
FROM agent_actions
WHERE action='report_outcome' AND tool_slug IN (slug_set)
GROUP BY tool_slug
```
One query, cache as dict, look up per tool. Avoids N+1.

### Stripe Checkout

Only shown for `source='curated'` stacks with priced tools. Auto-generated stacks show individual tool links instead — we're driving discovery, not selling auto-bundles.

### JSON-LD Structured Data

```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "Next.js Stack — 8 Indie Developer Tools",
  "description": "Agent-verified indie tools compatible with Next.js",
  "numberOfItems": 8,
  "itemListElement": [
    {"@type": "SoftwareApplication", "name": "Supabase", "url": "..."}
  ]
}
```

## MCP Server Enhancements

### `list_stacks()` — Richer Output

Now returns source, confidence, tokens saved, replaces, and framework:

```
## Next.js Stack (auto-generated, 87% confidence)
8 tools | Saves ~180,000 tokens
Replaces: Firebase Auth, Mailchimp, Google Analytics
Tools: Supabase, Resend, PostHog, Stripe, ...
URL: https://indiestack.ai/stacks/nextjs-stack
```

Sorted by confidence descending. No code changes needed in `list_stacks()` itself — it calls `/api/stacks` which returns `s.*`, so new columns appear automatically.

### `build_stack()` — Compatibility-Aware

After finding tools per need:
1. Batch-query `tool_pairs` to check compatibility between all recommended tools
2. Check `tool_conflicts` for the same set
3. Add `compatibility_notes` to response: "stripe and supabase are verified compatible" / "warning: X and Y have reported conflicts"
4. If a pre-built stack covers the requested needs, surface it: "Pre-built stack available: SaaS Starter (87% confidence) — covers auth + payments + analytics"

### `/api/stacks` — Query Params

Add optional filters:
- `?source=auto-framework` — filter by source type
- `?framework=nextjs` — filter by framework
- `?sort=confidence` — sort by confidence (default: created_at DESC)

## Sitemap

Add auto-generated stack pages to sitemap (same pattern as the comparison pages we just shipped). Each `/stacks/{slug}` page for auto-generated stacks gets an entry.

## Success Metrics

- Auto-generated stacks: ≥ 15 (framework + use-case combined)
- Framework stacks: ≥ 5 (with 4+ tools each)
- Composite use-case stacks: ≥ 6
- `list_stacks` MCP tool returns non-empty results
- `/stacks` page loads in < 500ms
- Stack detail pages indexed by Google within 30 days

## Known Limitations

1. **Framework data is sparse** — only ~60 tools have `frameworks_tested`. Framework stacks will be small initially. Grows as more tools get enriched or agents report framework compatibility.
2. **Most pairs are inferred** — confidence scores will cluster around 30%. This is honest and improves as agents verify pairs via `report_outcome`.
3. **Stack Generator is a separate page** — not embedded inline due to pure Python template architecture. Prominent link is the pragmatic choice.
4. **No auto-regeneration yet** — seed script is manual. Future work: cron job or post-deploy hook to regenerate stacks as new pairs flow in.

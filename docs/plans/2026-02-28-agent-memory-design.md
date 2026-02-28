# Agent Memory: Personalized Recommendations via MCP

## Thesis

IndieStack's MCP server already handles 2,000+ agent lookups. Every search is stateless — the agent asks, IndieStack answers, nobody remembers anything. The opportunity: if a developer uses an API key, IndieStack can build a lightweight interest profile from their search patterns and return better, personalized results over time. The agent becomes smarter about what this specific developer needs.

**No one else does this.** Product Hunt has algorithmic feeds. G2 has "similar products." But nobody's doing agent-mediated personalized recommendations for developer tools — where your AI assistant learns what you care about and a tool directory serves it better results over time.

**North star:** Developers with mature profiles get measurably better search results (higher click-through on recommended tools vs generic).

---

## Architecture

Six components, no new dependencies, no background jobs, fully backwards-compatible:

1. **Schema migration** — Add `api_key_id` to `search_logs` so searches can be tied to a developer
2. **Profile table** — `developer_profiles` stores aggregated interests, inferred tech stack, favorite tools
3. **Profile builder** — Rebuilds inline when stale, from search history + citations + bookmarks
4. **Search boosting** — Reranks FTS5 results using profile signals, adds `recommendation_reason` per tool
5. **Recommendations endpoint** — New MCP tool `get_recommendations()` for unprompted personalized suggestions
6. **Developer UI** — "Your Profile" section on `/developer` page with view, clear, and pause controls

---

## Part 1: Data Model

### Schema Migration

```sql
ALTER TABLE search_logs ADD COLUMN api_key_id INTEGER REFERENCES api_keys(id);
CREATE INDEX idx_search_logs_api_key ON search_logs(api_key_id);
```

### New Table

```sql
CREATE TABLE developer_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER NOT NULL UNIQUE REFERENCES api_keys(id),
    interests TEXT NOT NULL DEFAULT '{}',
    tech_stack TEXT NOT NULL DEFAULT '[]',
    favorite_tools TEXT NOT NULL DEFAULT '[]',
    search_count INTEGER NOT NULL DEFAULT 0,
    personalization_enabled INTEGER NOT NULL DEFAULT 1,
    last_rebuilt_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**`interests`** — JSON dict of category slugs to confidence scores (0-1):
```json
{"analytics": 0.8, "authentication": 0.6, "payments": 0.4}
```

**`tech_stack`** — JSON array of inferred technology keywords (top 10):
```json
["nextjs", "supabase", "tailwind", "vercel"]
```

**`favorite_tools`** — JSON array of tool slugs the developer interacts with repeatedly:
```json
["plausible-analytics", "lemon-squeezy", "trigger-dev"]
```

**Profile maturity:** `search_count < 5` = cold profile, falls back to generic results.

---

## Part 2: Profile Builder

Rebuilds lazily — on search, if `last_rebuilt_at` is older than 1 hour and new data exists.

### Interest Scoring

1. Pull last 90 days of `search_logs` for this `api_key_id`
2. Match each query against `NEED_MAPPINGS` keywords to determine category
3. Also check which categories the top results belong to
4. Score = `(searches in category) / (total searches)`, with recency decay:
   - Last 7 days: weight 3x
   - Last 30 days: weight 2x
   - Older: weight 1x

### Tech Stack Inference

1. Extract technology keywords from search queries using a keyword list (~50-80 common terms: react, nextjs, vue, svelte, django, rails, laravel, supabase, firebase, postgres, mongodb, etc.)
2. Check tool names in bookmarks and citations — bookmarking "Supabase" adds "supabase"
3. Deduplicate, keep top 10 by frequency

### Favorite Tools

1. Tools appearing in bookmarks, citations, or repeated searches (same slug 2+ times)
2. Ordered by interaction count

### Privacy Constraint

The profile builder stores only aggregated category scores and extracted keywords. Raw search queries are never stored in the profile — they stay in `search_logs` (which already exists) and are summarized during rebuilds.

---

## Part 3: Personalized Search

When `/api/tools/search` is called with an API key that has a mature profile, results are reranked before returning.

### Boosting Formula

```
final_score = fts_relevance + (category_match * 0.3) + (stack_match * 0.2) + (favorite_boost * 0.1)
```

- **category_match** — Tool's category is in developer's `interests`, multiplied by confidence. Analytics tool + 0.8 interest = +0.24
- **stack_match** — Tool's tags or `replaces` field overlap with developer's `tech_stack`
- **favorite_boost** — Tool is in developer's `favorite_tools`

### Response Changes (Additive)

New optional fields on each tool object:
```json
{
  "name": "Plausible Analytics",
  "recommendation_reason": "Popular with Supabase users",
  ...
}
```

New top-level fields:
```json
{
  "personalized": true,
  "tools": [...]
}
```

### First-Search Notice

First time an API key triggers a profile build, the response includes:
```json
{
  "notice": "IndieStack is learning your preferences to improve recommendations. View or manage your profile at indiestack.fly.dev/developer"
}
```

One-time only — set a flag on the profile after first notice.

### Backwards Compatibility

- No API key → no personalization, identical to today
- Cold profile → no personalization, identical to today
- Personalization paused → no personalization, identical to today
- New fields are additive — existing MCP clients ignore unknown fields

---

## Part 4: Recommendations Endpoint

### New MCP Tool

```
get_recommendations(category?: string, limit?: int)
```

- `category` — optional filter. If omitted, returns mixed recommendations across all interests.
- `limit` — 1-10, default 5

### Backend: `GET /api/recommendations?key=isk_...&category=...&limit=5`

### Selection Algorithm

1. Load developer profile
2. If cold (`search_count < 5`): return trending tools + "keep searching" message
3. If mature:
   a. Query tools weighted by: interest confidence × engagement signals (upvotes, claims, views)
   b. Exclude tools already in bookmarks or seen in recent searches (no repeats)
   c. For each tool, generate `recommendation_reason` from the strongest signal
   d. Include 1 "discovery pick" — a trending tool outside their usual interests to avoid filter bubbles
4. Return tools with reasons

### Recommendation Reasons (Specific > Generic)

Prefer relational, specific reasons:
- "Popular with Supabase users" > "Matches your interest in databases"
- "New this week in analytics" > "Recommended for you"
- "3 makers in your stack also use this" > "Matches your interests"

### Response Shape

```json
{
  "recommendations": [
    {
      "name": "Plausible Analytics",
      "slug": "plausible-analytics",
      "tagline": "Privacy-friendly Google Analytics alternative",
      "recommendation_reason": "Matches your interest in analytics · Works with Next.js",
      "indiestack_url": "https://indiestack.fly.dev/tool/plausible-analytics",
      "price": "Free",
      "is_verified": true,
      "discovery": false
    },
    {
      "name": "Trigger.dev",
      "slug": "trigger-dev",
      "tagline": "Background jobs for TypeScript",
      "recommendation_reason": "Trending this week · New in developer tools",
      "indiestack_url": "https://indiestack.fly.dev/tool/trigger-dev",
      "price": "Free",
      "is_verified": true,
      "discovery": true
    }
  ],
  "profile_maturity": "mature",
  "total_searches": 47
}
```

---

## Part 5: Privacy & Transparency

### What IndieStack Stores (Per API Key)

- Category interest scores (e.g., "analytics: 0.8")
- Inferred tech stack keywords (e.g., "nextjs, supabase")
- Favorite tool slugs
- Search count (just the number)

### What IndieStack Does NOT Store in the Profile

- Raw search queries (aggregated into categories, then discarded from profile)
- Conversation context (never sent to us)
- Code, file paths, or project details
- Browsing history outside of MCP searches

### MCP Tool Description

`get_recommendations()` description includes: "IndieStack builds a lightweight interest profile from your search categories — never raw queries, never conversation context. View or delete your profile at indiestack.fly.dev/developer."

### Developer Controls (`/developer` page)

Add a "Your Profile" section showing:
- **Your interests:** Analytics (high), Payments (medium), Auth (low)
- **Your inferred stack:** Next.js, Supabase, Tailwind
- **Favorite tools:** Plausible, Lemon Squeezy
- **Total searches:** 47
- **"Clear my preferences"** button — wipes profile data, keeps API key, profile rebuilds from scratch
- **"Pause personalization"** toggle — keeps profile but stops using it for boosting

### Transparency in API Responses

- `"personalized": true/false` on every search response
- `"recommendation_reason"` on each tool when personalized
- One-time `"notice"` on first profile build

---

## Part 6: What This Enables Later (Approach C)

The `developer_profiles` table is exactly what a proactive recommendation engine needs:

1. Add `pending_recommendations` table
2. Background job (daily) scans new tools against all profiles
3. New MCP tool `check_updates()` reads from pending_recommendations
4. Agent can say: "3 new tools match your interests since last week"

Zero changes to the profile builder or search personalization — C is a pure addition on top of A.

---

## Files Touched

| File | Change |
|------|--------|
| `db.py` | Schema migration, `developer_profiles` CRUD, `build_profile()`, update `log_search()` |
| `main.py` | Pass `api_key_id` to `log_search()`, search boost logic, `/api/recommendations` endpoint |
| `dashboard.py` | "Your Profile" section on `/developer` page |
| `mcp_server.py` | New `get_recommendations()` tool |

No new tables beyond `developer_profiles`. No new dependencies. No background jobs.

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Profiles built | 10+ (from API key users) |
| Personalized searches | 50+ per week |
| Recommendation click-through | Higher than generic trending |
| Profile clears | < 10% (people aren't bothered) |
| "Discovery pick" engagement | At least 1 in 10 clicked |

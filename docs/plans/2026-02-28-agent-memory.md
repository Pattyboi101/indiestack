# Agent Memory Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add personalized tool recommendations to IndieStack's MCP server by building developer profiles from search history, boosting search results by profile match, and exposing a `get_recommendations()` MCP tool.

**Architecture:** Six tasks across 4 files. Schema migration adds `api_key_id` to `search_logs` and creates `developer_profiles` table. Profile builder aggregates search patterns into category interests and tech stack. Search endpoint reranks results using profile. New `/api/recommendations` endpoint powers a new MCP tool. Developer UI on `/developer` shows profile with clear/pause controls. No new dependencies, no background jobs.

**Tech Stack:** Python/FastAPI, SQLite, aiosqlite, MCP SDK

---

### Task 1: Schema migration — link searches to API keys + create profiles table

**Files:**
- Modify: `src/indiestack/db.py:347-356` (search_logs schema)
- Modify: `src/indiestack/db.py:539-762` (init_db migrations)
- Modify: `src/indiestack/db.py:3215-3224` (log_search function)
- Modify: `src/indiestack/main.py:1015` (log_search call site)

**Step 1: Add `api_key_id` column to `search_logs` in SCHEMA**

In `src/indiestack/db.py`, find the `search_logs` CREATE TABLE at line 347:

```python
    CREATE TABLE IF NOT EXISTS search_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT 'web',
        result_count INTEGER NOT NULL DEFAULT 0,
        top_result_slug TEXT,
        top_result_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_search_logs_created ON search_logs(created_at);
```

Add `api_key_id` column and index:

```python
    CREATE TABLE IF NOT EXISTS search_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL,
        source TEXT NOT NULL DEFAULT 'web',
        result_count INTEGER NOT NULL DEFAULT 0,
        top_result_slug TEXT,
        top_result_name TEXT,
        api_key_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE INDEX IF NOT EXISTS idx_search_logs_created ON search_logs(created_at);
    CREATE INDEX IF NOT EXISTS idx_search_logs_api_key ON search_logs(api_key_id);
```

**Step 2: Add `developer_profiles` table to SCHEMA**

After the `search_logs` block (around line 356), add:

```python
    CREATE TABLE IF NOT EXISTS developer_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_key_id INTEGER NOT NULL UNIQUE REFERENCES api_keys(id),
        interests TEXT NOT NULL DEFAULT '{}',
        tech_stack TEXT NOT NULL DEFAULT '[]',
        favorite_tools TEXT NOT NULL DEFAULT '[]',
        search_count INTEGER NOT NULL DEFAULT 0,
        personalization_enabled INTEGER NOT NULL DEFAULT 1,
        notice_shown INTEGER NOT NULL DEFAULT 0,
        last_rebuilt_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
```

**Step 3: Add migration in `init_db()`**

In the `init_db()` function (around line 539-762), find the migration section at the end. Add a new migration block:

```python
    # Agent Memory: add api_key_id to search_logs + create developer_profiles
    try:
        await db.execute("SELECT api_key_id FROM search_logs LIMIT 1")
    except Exception:
        await db.execute("ALTER TABLE search_logs ADD COLUMN api_key_id INTEGER")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_search_logs_api_key ON search_logs(api_key_id)")
        await db.commit()

    await db.execute("""CREATE TABLE IF NOT EXISTS developer_profiles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_key_id INTEGER NOT NULL UNIQUE REFERENCES api_keys(id),
        interests TEXT NOT NULL DEFAULT '{}',
        tech_stack TEXT NOT NULL DEFAULT '[]',
        favorite_tools TEXT NOT NULL DEFAULT '[]',
        search_count INTEGER NOT NULL DEFAULT 0,
        personalization_enabled INTEGER NOT NULL DEFAULT 1,
        notice_shown INTEGER NOT NULL DEFAULT 0,
        last_rebuilt_at TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    await db.commit()
```

**Step 4: Update `log_search()` to accept `api_key_id`**

In `src/indiestack/db.py`, find `log_search()` at line 3215. Change from:

```python
async def log_search(db, query: str, source: str = 'web', result_count: int = 0,
                     top_result_slug: str = None, top_result_name: str = None):
    """Log a search query for the Live Wire feed and maker analytics."""
    if not query or not query.strip():
        return
    await db.execute(
        """INSERT INTO search_logs (query, source, result_count, top_result_slug, top_result_name)
           VALUES (?, ?, ?, ?, ?)""",
        (query.strip()[:200], source, result_count, top_result_slug, top_result_name))
    await db.commit()
```

To:

```python
async def log_search(db, query: str, source: str = 'web', result_count: int = 0,
                     top_result_slug: str = None, top_result_name: str = None,
                     api_key_id: int = None):
    """Log a search query for the Live Wire feed and maker analytics."""
    if not query or not query.strip():
        return
    await db.execute(
        """INSERT INTO search_logs (query, source, result_count, top_result_slug, top_result_name, api_key_id)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (query.strip()[:200], source, result_count, top_result_slug, top_result_name, api_key_id))
    await db.commit()
```

**Step 5: Pass `api_key_id` from the search endpoint**

In `src/indiestack/main.py`, find the `log_search()` call at line 1015:

```python
        await db.log_search(d, q, 'api', len(results), top_slug, top_name)
```

Replace with:

```python
        api_key_id = request.state.api_key['id'] if request.state.api_key else None
        await db.log_search(d, q, 'api', len(results), top_slug, top_name, api_key_id=api_key_id)
```

**Step 6: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read())" && python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read())"`
Expected: No output (clean parse)

**Step 7: Commit**

```bash
git add src/indiestack/db.py src/indiestack/main.py
git commit -m "feat: schema migration for agent memory — api_key_id on search_logs + developer_profiles table"
```

---

### Task 2: Profile builder — aggregate search patterns into interests and tech stack

**Files:**
- Modify: `src/indiestack/db.py` (add profile builder functions after line 3850)

**Step 1: Add the tech stack keyword list**

After `NEED_MAPPINGS` (around line 520), add a keyword set for tech stack inference:

```python
TECH_KEYWORDS = {
    "react", "nextjs", "next.js", "vue", "nuxt", "svelte", "sveltekit", "angular",
    "django", "flask", "fastapi", "rails", "laravel", "express", "nestjs",
    "supabase", "firebase", "postgres", "postgresql", "mongodb", "mysql", "redis",
    "tailwind", "bootstrap", "chakra",
    "vercel", "netlify", "cloudflare", "aws", "gcp", "azure", "fly.io",
    "docker", "kubernetes",
    "stripe", "paddle", "lemon squeezy",
    "typescript", "python", "go", "rust", "ruby", "php", "java",
    "graphql", "rest", "trpc",
    "prisma", "drizzle", "sqlalchemy",
    "playwright", "cypress", "jest", "vitest",
    "openai", "anthropic", "claude", "gpt",
}
```

**Step 2: Add profile CRUD functions**

At the end of db.py (after the API key functions, around line 3850), add:

```python
# ── Agent Memory: Developer Profiles ──────────────────────────

async def get_developer_profile(db, api_key_id: int) -> dict | None:
    """Get a developer's personalization profile."""
    cursor = await db.execute(
        "SELECT * FROM developer_profiles WHERE api_key_id = ?", (api_key_id,))
    row = await cursor.fetchone()
    return dict(row) if row else None


async def clear_developer_profile(db, api_key_id: int):
    """Clear personalization data but keep the profile row."""
    await db.execute(
        """UPDATE developer_profiles
           SET interests = '{}', tech_stack = '[]', favorite_tools = '[]',
               search_count = 0, last_rebuilt_at = NULL
           WHERE api_key_id = ?""", (api_key_id,))
    await db.commit()


async def toggle_personalization(db, api_key_id: int) -> bool:
    """Toggle personalization on/off. Returns new state."""
    cursor = await db.execute(
        "SELECT personalization_enabled FROM developer_profiles WHERE api_key_id = ?",
        (api_key_id,))
    row = await cursor.fetchone()
    if not row:
        return True
    new_state = 0 if row['personalization_enabled'] else 1
    await db.execute(
        "UPDATE developer_profiles SET personalization_enabled = ? WHERE api_key_id = ?",
        (new_state, api_key_id))
    await db.commit()
    return bool(new_state)


async def mark_notice_shown(db, api_key_id: int):
    """Mark that the first-search personalization notice has been shown."""
    await db.execute(
        "UPDATE developer_profiles SET notice_shown = 1 WHERE api_key_id = ?",
        (api_key_id,))
    await db.commit()


async def build_developer_profile(db, api_key_id: int) -> dict:
    """Build or rebuild a developer profile from their search history.

    Aggregates last 90 days of searches into:
    - interests: category slug -> confidence score (0-1)
    - tech_stack: list of inferred technology keywords
    - favorite_tools: list of tool slugs they interact with repeatedly
    """
    import json
    from collections import Counter

    # Get recent searches for this API key
    cursor = await db.execute(
        """SELECT query, top_result_slug, created_at,
                  julianday('now') - julianday(created_at) as days_ago
           FROM search_logs
           WHERE api_key_id = ? AND created_at >= datetime('now', '-90 days')
           ORDER BY created_at DESC""",
        (api_key_id,))
    searches = [dict(r) for r in await cursor.fetchall()]

    search_count = len(searches)
    if search_count == 0:
        return {'interests': {}, 'tech_stack': [], 'favorite_tools': [], 'search_count': 0}

    # Score categories from search queries using NEED_MAPPINGS
    category_scores = Counter()
    tech_found = Counter()
    tool_slugs = Counter()

    for s in searches:
        q = (s['query'] or '').lower()
        days = s['days_ago'] or 0

        # Recency weight: last 7 days = 3x, last 30 = 2x, older = 1x
        weight = 3.0 if days <= 7 else (2.0 if days <= 30 else 1.0)

        # Match against NEED_MAPPINGS keywords
        for keyword, mapping in NEED_MAPPINGS.items():
            terms = [keyword] + mapping.get('terms', [])
            for term in terms:
                if term.lower() in q:
                    category_scores[mapping['category']] += weight
                    break

        # Extract tech keywords
        for kw in TECH_KEYWORDS:
            if kw in q:
                tech_found[kw] += weight

        # Track tool slugs from top results
        if s['top_result_slug']:
            tool_slugs[s['top_result_slug']] += 1

    # Also check bookmarks for this user
    key_cursor = await db.execute(
        "SELECT user_id FROM api_keys WHERE id = ?", (api_key_id,))
    key_row = await key_cursor.fetchone()
    if key_row:
        user_id = key_row['user_id']
        wl_cursor = await db.execute(
            """SELECT t.slug, t.tags, c.slug as cat_slug
               FROM wishlists w
               JOIN tools t ON w.tool_id = t.id
               JOIN categories c ON t.category_id = c.id
               WHERE w.user_id = ?""", (user_id,))
        for row in await wl_cursor.fetchall():
            tool_slugs[row['slug']] += 2  # Bookmarks count more
            category_scores[row['cat_slug']] += 1.0
            # Infer tech from bookmarked tool names
            name_lower = row['slug'].replace('-', ' ')
            for kw in TECH_KEYWORDS:
                if kw in name_lower:
                    tech_found[kw] += 1.0

    # Normalize interests to 0-1 scale
    max_score = max(category_scores.values()) if category_scores else 1
    interests = {cat: round(score / max_score, 2) for cat, score in category_scores.most_common(10)}

    # Top 10 tech keywords
    tech_stack = [kw for kw, _ in tech_found.most_common(10)]

    # Favorite tools: appeared 2+ times
    favorite_tools = [slug for slug, count in tool_slugs.most_common(20) if count >= 2]

    # Upsert profile
    profile = await get_developer_profile(db, api_key_id)
    if profile:
        await db.execute(
            """UPDATE developer_profiles
               SET interests = ?, tech_stack = ?, favorite_tools = ?,
                   search_count = ?, last_rebuilt_at = CURRENT_TIMESTAMP
               WHERE api_key_id = ?""",
            (json.dumps(interests), json.dumps(tech_stack), json.dumps(favorite_tools),
             search_count, api_key_id))
    else:
        await db.execute(
            """INSERT INTO developer_profiles
               (api_key_id, interests, tech_stack, favorite_tools, search_count, last_rebuilt_at)
               VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
            (api_key_id, json.dumps(interests), json.dumps(tech_stack),
             json.dumps(favorite_tools), search_count))
    await db.commit()

    return {'interests': interests, 'tech_stack': tech_stack,
            'favorite_tools': favorite_tools, 'search_count': search_count}
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read())"`
Expected: No output (clean parse)

**Step 4: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: profile builder — aggregate search patterns into interests and tech stack"
```

---

### Task 3: Personalized search — boost results by profile match

**Files:**
- Modify: `src/indiestack/main.py:961-1047` (api_tools_search endpoint)

**Step 1: Add a profile-aware reranking helper**

Above the `/api/tools/search` endpoint (around line 960), add:

```python
def _personalize_results(tools: list[dict], profile: dict) -> list[dict]:
    """Rerank search results using a developer's profile. Returns tools with recommendation_reason."""
    import json
    interests = json.loads(profile.get('interests', '{}')) if isinstance(profile.get('interests'), str) else profile.get('interests', {})
    tech_stack = json.loads(profile.get('tech_stack', '[]')) if isinstance(profile.get('tech_stack'), str) else profile.get('tech_stack', [])
    favorites = json.loads(profile.get('favorite_tools', '[]')) if isinstance(profile.get('favorite_tools'), str) else profile.get('favorite_tools', [])
    tech_set = set(kw.lower() for kw in tech_stack)

    scored = []
    for i, tool in enumerate(tools):
        boost = 0.0
        reason = ''

        # Category match
        cat_slug = tool.get('category_slug', '') or tool.get('category', '').lower().replace(' ', '-')
        if cat_slug in interests:
            confidence = interests[cat_slug]
            boost += confidence * 0.3
            cat_name = cat_slug.replace('-', ' ').title()
            reason = f"Matches your interest in {cat_name}"

        # Tech stack match — check tool tags
        tags = (tool.get('tags', '') or '').lower()
        tool_name = (tool.get('name', '') or '').lower()
        matched_tech = [kw for kw in tech_set if kw in tags or kw in tool_name]
        if matched_tech:
            boost += 0.2
            reason = f"Works with {matched_tech[0].title()}" if not reason else reason

        # Favorite boost
        slug = tool.get('slug', '')
        if slug in favorites:
            boost += 0.1

        # Preserve original order as tiebreaker
        tool['_personalization_score'] = boost
        tool['_original_index'] = i
        if reason:
            tool['recommendation_reason'] = reason
        scored.append(tool)

    # Sort by boost descending, original order as tiebreaker
    scored.sort(key=lambda t: (-t['_personalization_score'], t['_original_index']))

    # Clean up internal fields
    for t in scored:
        t.pop('_personalization_score', None)
        t.pop('_original_index', None)

    return scored
```

**Step 2: Wire personalization into the search endpoint**

In the `/api/tools/search` endpoint (line 961-1047), find the section after results are built but before the response is returned. Look for the `return JSONResponse(...)` or the dict construction.

After the `log_search()` call (around line 1015-1017) and before the return statement, add the personalization logic:

```python
        # Personalize results if API key has a mature profile
        personalized = False
        notice = None
        api_key = request.state.api_key
        if api_key and results:
            profile = await db.get_developer_profile(d, api_key['id'])

            # Rebuild if stale (> 1 hour old) or doesn't exist
            should_rebuild = False
            if not profile:
                should_rebuild = True
            elif profile['last_rebuilt_at']:
                from datetime import datetime, timedelta
                try:
                    rebuilt = datetime.fromisoformat(profile['last_rebuilt_at'])
                    if datetime.utcnow() - rebuilt > timedelta(hours=1):
                        should_rebuild = True
                except (ValueError, TypeError):
                    should_rebuild = True
            else:
                should_rebuild = True

            if should_rebuild:
                profile_data = await db.build_developer_profile(d, api_key['id'])
                profile = await db.get_developer_profile(d, api_key['id'])

            if profile and profile.get('search_count', 0) >= 5 and profile.get('personalization_enabled', 1):
                results = _personalize_results(results, profile)
                personalized = True

            # First-search notice
            if profile and not profile.get('notice_shown', 0):
                notice = "IndieStack is learning your preferences to improve recommendations. View or manage your profile at indiestack.fly.dev/developer"
                await db.mark_notice_shown(d, api_key['id'])
```

Then in the response dict that gets returned, add the new fields:

Find the response dict (it will look something like `{"tools": [...], "total": ..., "query": ..., "offset": ...}`). Add:

```python
        response_data = {
            ...existing fields...
            "personalized": personalized,
        }
        if notice:
            response_data["notice"] = notice
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read())"`
Expected: No output (clean parse)

**Step 4: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: personalized search — boost results by developer profile"
```

---

### Task 4: Recommendations endpoint — personalized suggestions without searching

**Files:**
- Modify: `src/indiestack/main.py` (add new endpoint after `/api/tools/search`)

**Step 1: Add the `/api/recommendations` endpoint**

After the `/api/tools/search` endpoint (around line 1047), add:

```python
@app.get("/api/recommendations")
async def api_recommendations(request: Request, category: str = "", limit: int = 5):
    """Personalized tool recommendations based on developer profile."""
    import json as _json

    limit = max(1, min(10, limit))
    api_key = request.state.api_key
    d = request.state.db

    if not api_key:
        return JSONResponse({"error": "API key required for recommendations. Get one at indiestack.fly.dev/developer"}, status_code=401)

    # Get or build profile
    profile = await db.get_developer_profile(d, api_key['id'])
    if not profile:
        await db.build_developer_profile(d, api_key['id'])
        profile = await db.get_developer_profile(d, api_key['id'])

    if not profile or profile.get('search_count', 0) < 5:
        # Cold profile — return trending instead
        trending = await db.get_trending_scored(d, limit=limit)
        tools_list = []
        for t in trending:
            tools_list.append({
                "name": t['name'], "slug": t['slug'], "tagline": t['tagline'],
                "price": f"£{t['price_pence'] / 100:.2f}" if t.get('price_pence') else "Free",
                "is_verified": bool(t.get('is_verified')),
                "indiestack_url": f"https://indiestack.fly.dev/tool/{t['slug']}",
                "recommendation_reason": "Trending this week",
                "discovery": False,
            })
        return JSONResponse({
            "recommendations": tools_list,
            "profile_maturity": "cold",
            "total_searches": profile.get('search_count', 0) if profile else 0,
            "message": "Not enough search history to personalize yet. Keep using IndieStack through your agent and recommendations will improve.",
        })

    if not profile.get('personalization_enabled', 1):
        return JSONResponse({"error": "Personalization is paused. Enable it at indiestack.fly.dev/developer"}, status_code=403)

    interests = _json.loads(profile['interests']) if isinstance(profile['interests'], str) else profile['interests']
    tech_stack = _json.loads(profile['tech_stack']) if isinstance(profile['tech_stack'], str) else profile['tech_stack']
    favorites = _json.loads(profile['favorite_tools']) if isinstance(profile['favorite_tools'], str) else profile['favorite_tools']

    # Build a weighted query across top interest categories
    recommended = []
    seen_slugs = set(favorites)  # Exclude favorites (they already know these)

    # Get recent search result slugs to avoid repeats
    recent_cursor = await d.execute(
        """SELECT DISTINCT top_result_slug FROM search_logs
           WHERE api_key_id = ? AND top_result_slug IS NOT NULL
           AND created_at >= datetime('now', '-7 days')""",
        (api_key['id'],))
    for row in await recent_cursor.fetchall():
        seen_slugs.add(row['top_result_slug'])

    # Query tools from top interest categories
    sorted_interests = sorted(interests.items(), key=lambda x: -x[1])
    if category:
        # Filter to specific category if requested
        sorted_interests = [(cat, score) for cat, score in sorted_interests if cat == category]

    for cat_slug, confidence in sorted_interests[:5]:
        cat_cursor = await d.execute(
            """SELECT t.*, c.name as category_name, c.slug as category_slug
               FROM tools t JOIN categories c ON t.category_id = c.id
               WHERE c.slug = ? AND t.status = 'approved'
               ORDER BY t.upvote_count DESC LIMIT 10""",
            (cat_slug,))
        for t in await cat_cursor.fetchall():
            t = dict(t)
            if t['slug'] not in seen_slugs and len(recommended) < limit - 1:
                # Generate reason
                tags = (t.get('tags', '') or '').lower()
                tech_match = [kw for kw in tech_stack if kw.lower() in tags or kw.lower() in t['name'].lower()]
                cat_name = t['category_name']

                if tech_match:
                    reason = f"Popular with {tech_match[0].title()} users"
                elif confidence >= 0.7:
                    reason = f"Matches your interest in {cat_name}"
                else:
                    reason = f"Recommended in {cat_name}"

                recommended.append({
                    "name": t['name'], "slug": t['slug'], "tagline": t['tagline'],
                    "price": f"£{t['price_pence'] / 100:.2f}" if t.get('price_pence') else "Free",
                    "is_verified": bool(t.get('is_verified')),
                    "indiestack_url": f"https://indiestack.fly.dev/tool/{t['slug']}",
                    "recommendation_reason": reason,
                    "discovery": False,
                })
                seen_slugs.add(t['slug'])

        if len(recommended) >= limit - 1:
            break

    # Add 1 discovery pick — trending tool outside their interests
    interest_cats = set(interests.keys())
    disc_cursor = await d.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved'
           ORDER BY t.upvote_count DESC LIMIT 50""")
    for t in await disc_cursor.fetchall():
        t = dict(t)
        if t['slug'] not in seen_slugs and t.get('category_slug') not in interest_cats:
            recommended.append({
                "name": t['name'], "slug": t['slug'], "tagline": t['tagline'],
                "price": f"£{t['price_pence'] / 100:.2f}" if t.get('price_pence') else "Free",
                "is_verified": bool(t.get('is_verified')),
                "indiestack_url": f"https://indiestack.fly.dev/tool/{t['slug']}",
                "recommendation_reason": f"Trending in {t['category_name']} \u2014 outside your usual picks",
                "discovery": True,
            })
            break

    return JSONResponse({
        "recommendations": recommended[:limit],
        "profile_maturity": "mature",
        "total_searches": profile['search_count'],
    })
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read())"`
Expected: No output (clean parse)

**Step 3: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: /api/recommendations endpoint — personalized suggestions with discovery picks"
```

---

### Task 5: MCP tool — expose `get_recommendations()` to agents

**Files:**
- Modify: `src/indiestack/mcp_server.py` (add new tool after line 566)

**Step 1: Add the `get_recommendations()` MCP tool**

After the last tool (`build_stack()` ending around line 620), add:

```python
@mcp.tool()
async def get_recommendations(category: str = "", limit: int = 5) -> str:
    """Get personalized tool recommendations based on your search history.

    IndieStack builds a lightweight interest profile from your search categories —
    never raw queries, never conversation context. View or delete your profile
    at indiestack.fly.dev/developer.

    Args:
        category: Optional category filter (e.g. "analytics", "auth", "payments").
                  If omitted, returns mixed recommendations across all your interests.
        limit: Number of recommendations (1-10, default 5).
    """
    params = {"limit": min(10, max(1, limit))}
    if category:
        params["category"] = category

    data = await _api_get("/api/recommendations", params)

    if "error" in data:
        return f"⚠️ {data['error']}"

    recs = data.get("recommendations", [])
    maturity = data.get("profile_maturity", "cold")
    total = data.get("total_searches", 0)

    if not recs:
        return "No recommendations available yet. Try searching for some tools first!"

    lines = []
    if maturity == "cold":
        lines.append(f"📊 Your profile is still building ({total} searches so far, need 5+).")
        lines.append("Here are trending tools in the meantime:\n")
    else:
        lines.append(f"🎯 Personalized for you (based on {total} searches):\n")

    for i, r in enumerate(recs, 1):
        verified = " ✓" if r.get("is_verified") else ""
        discovery = " 🔍" if r.get("discovery") else ""
        price = r.get("price", "Free")
        lines.append(f"{i}. **{r['name']}**{verified}{discovery} — {r['tagline']}")
        lines.append(f"   💡 {r.get('recommendation_reason', 'Recommended')}")
        lines.append(f"   💰 {price} | {r['indiestack_url']}")
        lines.append("")

    if maturity == "cold":
        lines.append("💡 Tip: Keep using IndieStack through your agent and recommendations will improve.")
    else:
        lines.append("🔍 = Discovery pick (outside your usual interests)")
        lines.append("\n🔒 Manage your profile: indiestack.fly.dev/developer")

    if data.get("message"):
        lines.append(f"\n{data['message']}")

    return "\n".join(lines)
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/mcp_server.py').read())"`
Expected: No output (clean parse)

**Step 3: Commit**

```bash
git add src/indiestack/mcp_server.py
git commit -m "feat: get_recommendations() MCP tool — personalized suggestions for agents"
```

---

### Task 6: Developer UI — show profile with clear/pause controls

**Files:**
- Modify: `src/indiestack/routes/dashboard.py:1756-1875` (developer page)

**Step 1: Add profile section to the developer page**

In `src/indiestack/routes/dashboard.py`, find the `/developer` route handler (line 1756). Inside the function, after the API keys are loaded but before the HTML is built, add profile loading:

```python
    # Load developer profile (from first active API key)
    profile_html = ''
    if keys:
        first_key_id = keys[0]['id'] if keys else None
        if first_key_id:
            profile = await db.get_developer_profile(db_conn, first_key_id)
            if profile and profile.get('search_count', 0) > 0:
                import json as _json
                interests = _json.loads(profile['interests']) if isinstance(profile['interests'], str) else profile['interests']
                tech_stack = _json.loads(profile['tech_stack']) if isinstance(profile['tech_stack'], str) else profile['tech_stack']
                favorites = _json.loads(profile['favorite_tools']) if isinstance(profile['favorite_tools'], str) else profile['favorite_tools']
                enabled = profile.get('personalization_enabled', 1)

                # Interest pills
                interest_pills = ''
                for cat, score in sorted(interests.items(), key=lambda x: -x[1])[:8]:
                    level = 'high' if score >= 0.7 else ('medium' if score >= 0.4 else 'low')
                    color = 'var(--success-text)' if level == 'high' else ('var(--gold)' if level == 'medium' else 'var(--ink-muted)')
                    cat_display = cat.replace('-', ' ').title()
                    interest_pills += f'<span style="display:inline-block;padding:4px 12px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid {color};color:{color};margin:2px;">{cat_display} ({level})</span>'

                # Tech stack pills
                tech_pills = ''.join(
                    f'<span style="display:inline-block;padding:4px 12px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid var(--accent);color:var(--accent);margin:2px;">{kw}</span>'
                    for kw in tech_stack[:8]
                ) if tech_stack else '<span style="color:var(--ink-muted);font-size:13px;">None inferred yet</span>'

                # Favorite tools
                fav_pills = ''.join(
                    f'<a href="/tool/{slug}" style="display:inline-block;padding:4px 12px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid var(--border);color:var(--ink-light);margin:2px;text-decoration:none;">{slug}</a>'
                    for slug in favorites[:6]
                ) if favorites else '<span style="color:var(--ink-muted);font-size:13px;">None yet</span>'

                toggle_text = 'Pause Personalization' if enabled else 'Resume Personalization'
                toggle_color = 'var(--ink-muted)' if enabled else 'var(--success-text)'

                profile_html = f'''
                <div class="card" style="padding:24px;margin-bottom:32px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                        <h3 style="font-family:var(--font-display);font-size:20px;margin:0;">Your Profile</h3>
                        <span style="font-size:12px;color:var(--ink-muted);">{profile['search_count']} searches analyzed</span>
                    </div>
                    <p style="font-size:13px;color:var(--ink-muted);margin-bottom:16px;">
                        Built from your search patterns. We store category interests and tech keywords — never raw queries.
                    </p>
                    <div style="margin-bottom:16px;">
                        <div style="font-size:13px;font-weight:600;color:var(--ink-light);margin-bottom:8px;">Interests</div>
                        <div style="display:flex;flex-wrap:wrap;gap:4px;">{interest_pills if interest_pills else '<span style="color:var(--ink-muted);font-size:13px;">None yet</span>'}</div>
                    </div>
                    <div style="margin-bottom:16px;">
                        <div style="font-size:13px;font-weight:600;color:var(--ink-light);margin-bottom:8px;">Inferred Stack</div>
                        <div style="display:flex;flex-wrap:wrap;gap:4px;">{tech_pills}</div>
                    </div>
                    <div style="margin-bottom:24px;">
                        <div style="font-size:13px;font-weight:600;color:var(--ink-light);margin-bottom:8px;">Favorite Tools</div>
                        <div style="display:flex;flex-wrap:wrap;gap:4px;">{fav_pills}</div>
                    </div>
                    <div style="display:flex;gap:12px;">
                        <form method="POST" action="/developer/toggle-personalization" style="margin:0;">
                            <button type="submit" class="btn btn-secondary" style="font-size:13px;padding:8px 16px;color:{toggle_color};">{toggle_text}</button>
                        </form>
                        <form method="POST" action="/developer/clear-profile" style="margin:0;"
                              onsubmit="return confirm('Clear your preferences? Your profile will rebuild from scratch.')">
                            <button type="submit" class="btn btn-secondary" style="font-size:13px;padding:8px 16px;color:var(--danger);">Clear Preferences</button>
                        </form>
                    </div>
                </div>
                '''
```

Then insert `{profile_html}` in the page body HTML, just before the API keys section.

**Step 2: Add POST handlers for toggle and clear**

After the `/developer/revoke-key` handler (around line 1913), add:

```python
@router.post("/developer/toggle-personalization")
async def toggle_personalization_route(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse("/login?next=/developer", status_code=303)
    db_conn = request.state.db
    keys = await db.get_api_keys_for_user(db_conn, user['id'])
    if keys:
        await db.toggle_personalization(db_conn, keys[0]['id'])
    return RedirectResponse("/developer", status_code=303)


@router.post("/developer/clear-profile")
async def clear_profile_route(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse("/login?next=/developer", status_code=303)
    db_conn = request.state.db
    keys = await db.get_api_keys_for_user(db_conn, user['id'])
    if keys:
        await db.clear_developer_profile(db_conn, keys[0]['id'])
    return RedirectResponse("/developer", status_code=303)
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/dashboard.py').read())"`
Expected: No output (clean parse)

**Step 4: Commit**

```bash
git add src/indiestack/routes/dashboard.py
git commit -m "feat: developer UI — show profile with clear and pause controls"
```

---

### Task 7: Smoke test and deploy

**Step 1: Run all syntax checks**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read())" && \
python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read())" && \
python3 -c "import ast; ast.parse(open('src/indiestack/mcp_server.py').read())" && \
python3 -c "import ast; ast.parse(open('src/indiestack/routes/dashboard.py').read())" && \
echo "All OK"
```

Expected: `All OK`

**Step 2: Run smoke test**

```bash
python3 smoke_test.py
```

Expected: `38 passed, 0 failed / 38 total`

**Step 3: Deploy**

```bash
~/.fly/bin/flyctl deploy --remote-only
```

**Step 4: Verify migration ran**

```bash
~/.fly/bin/flyctl ssh console -a indiestack -C "python3 -c \"
import sqlite3
db = sqlite3.connect('/data/indiestack.db')
# Check search_logs has api_key_id
cols = [r[1] for r in db.execute('PRAGMA table_info(search_logs)').fetchall()]
assert 'api_key_id' in cols, 'search_logs missing api_key_id'
# Check developer_profiles exists
db.execute('SELECT * FROM developer_profiles LIMIT 1')
print('Migration OK: search_logs.api_key_id + developer_profiles table exist')
\""
```

**Step 5: Test the recommendations endpoint**

```bash
curl -s "https://indiestack.fly.dev/api/recommendations" | python3 -m json.tool
```

Expected: `{"error": "API key required for recommendations..."}` (401 — correct, no key provided)

**Step 6: Manual verification**

1. Visit https://indiestack.fly.dev/developer — log in, check that "Your Profile" section appears (may be empty if no searches yet)
2. Use an API key to search a few times: `curl "https://indiestack.fly.dev/api/tools/search?q=analytics&key=YOUR_KEY"`
3. After 5+ searches, call recommendations: `curl "https://indiestack.fly.dev/api/recommendations?key=YOUR_KEY"`
4. Check `/developer` page shows interests, tech stack, favorites
5. Test "Clear Preferences" button — profile resets
6. Test "Pause Personalization" button — search results stop being personalized

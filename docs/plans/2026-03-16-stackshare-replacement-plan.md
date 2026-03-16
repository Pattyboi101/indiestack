# StackShare Replacement — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Seed the compatibility graph from our own framework/category data, enhance existing comparison pages with agent-verified intelligence, and execute traffic plays.

**Architecture:** Phase 1 is a one-shot seed script that generates inferred tool pairs from framework affinity and category complementarity. Phase 2 enhances existing `/compare` and `/alternatives` routes with compatibility data, health scores, and success rates from the intelligence layer. Phase 3 is traffic acquisition via external listings.

**Tech Stack:** Python 3 / aiosqlite / existing db.py functions / existing route files

---

### Task 1: Generate Inferred Compatibility Pairs

**Files:**
- Create: `scripts/seeds/seed_inferred_pairs.py`
- Read: `src/indiestack/db.py` (ENRICHMENTS dict at line 652, SEED_PAIRS at line 814)

**What this does:** Query all approved tools with `frameworks_tested` data. For every pair of tools that (a) share at least one framework AND (b) are in different categories, generate an inferred compatibility pair. Also generate pairs for tools in predefined complementary category combinations.

**Step 1: Write the seed script**

```python
#!/usr/bin/env python3
"""Generate inferred compatibility pairs from framework affinity and category complementarity."""
import asyncio
import aiosqlite
import os

# Categories that naturally complement each other (by slug)
COMPLEMENTARY_CATEGORIES = [
    ("authentication", "payments"),
    ("authentication", "analytics-metrics"),
    ("authentication", "monitoring-uptime"),
    ("authentication", "api-tools"),
    ("payments", "email-marketing"),
    ("payments", "invoicing-billing"),
    ("payments", "analytics-metrics"),
    ("analytics-metrics", "monitoring-uptime"),
    ("analytics-metrics", "seo-tools"),
    ("monitoring-uptime", "developer-tools"),
    ("api-tools", "developer-tools"),
    ("forms-surveys", "email-marketing"),
    ("forms-surveys", "crm-sales"),
    ("crm-sales", "email-marketing"),
    ("landing-pages", "analytics-metrics"),
    ("landing-pages", "forms-surveys"),
    ("feedback-reviews", "email-marketing"),
    ("ai-automation", "api-tools"),
    ("ai-dev-tools", "developer-tools"),
    ("ai-dev-tools", "monitoring-uptime"),
]

DB_PATH = os.environ.get("DB_PATH", "/data/indiestack.db")


async def main():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}

    # Get all approved tools with category info
    cursor = await db.execute("""
        SELECT t.slug, t.frameworks_tested, c.slug as category_slug
        FROM tools t JOIN categories c ON t.category_id = c.id
        WHERE t.status = 'approved'
    """)
    tools = await cursor.fetchall()
    print(f"Found {len(tools)} approved tools")

    # Build framework index: framework -> [tool_slugs]
    framework_index = {}
    for t in tools:
        if t['frameworks_tested']:
            for fw in t['frameworks_tested'].split(','):
                fw = fw.strip().lower()
                if fw:
                    framework_index.setdefault(fw, []).append(t)

    # Build category index: category_slug -> [tool_slugs]
    category_index = {}
    for t in tools:
        category_index.setdefault(t['category_slug'], []).append(t)

    pairs = set()

    # Strategy 1: Framework affinity — tools sharing a framework in different categories
    for fw, fw_tools in framework_index.items():
        for i, t1 in enumerate(fw_tools):
            for t2 in fw_tools[i + 1:]:
                if t1['category_slug'] != t2['category_slug']:
                    a, b = sorted([t1['slug'], t2['slug']])
                    pairs.add((a, b))

    print(f"Framework affinity pairs: {len(pairs)}")

    # Strategy 2: Complementary categories — all cross-category pairs
    cat_pairs_count = 0
    for cat_a, cat_b in COMPLEMENTARY_CATEGORIES:
        tools_a = category_index.get(cat_a, [])
        tools_b = category_index.get(cat_b, [])
        for t1 in tools_a:
            for t2 in tools_b:
                a, b = sorted([t1['slug'], t2['slug']])
                pairs.add((a, b))
                cat_pairs_count += 1

    print(f"Complementary category pairs: {cat_pairs_count}")
    print(f"Total unique pairs (deduplicated): {len(pairs)}")

    # Insert pairs — skip any that already exist
    inserted = 0
    skipped = 0
    for a, b in pairs:
        try:
            await db.execute(
                """INSERT INTO tool_pairs (tool_a_slug, tool_b_slug, source, verified, success_count)
                   VALUES (?, ?, 'inferred', 0, 0)""",
                (a, b),
            )
            inserted += 1
        except aiosqlite.IntegrityError:
            skipped += 1

    await db.commit()
    await db.close()

    print(f"\nInserted: {inserted} new pairs")
    print(f"Skipped: {skipped} (already existed)")
    print(f"Total pairs now in database: {inserted + skipped + 39}")  # 39 = existing seed pairs approx


if __name__ == "__main__":
    asyncio.run(main())
```

**Step 2: Test locally with a copy of the production DB**

Run: `bash /home/patty/indiestack/scripts/backup_db.sh` (or equivalent) to get a local copy, then:
```bash
DB_PATH=/tmp/test_indiestack.db python3 scripts/seeds/seed_inferred_pairs.py
```

Expected: Prints pair counts. Framework affinity should generate 100-300 pairs. Complementary categories should generate 200-500+. Total unique should be 300-800+.

**Step 3: Run against production DB via Fly SSH**

```bash
cd ~/indiestack && ~/.fly/bin/flyctl ssh console -C "python3 -c \"
import asyncio, aiosqlite
async def count():
    db = await aiosqlite.connect('/data/indiestack.db')
    c = await db.execute('SELECT COUNT(*) FROM tool_pairs')
    r = await c.fetchone()
    print(f'Current pairs: {r[0]}')
    await db.close()
asyncio.run(count())
\""
```

Then upload and run the seed script:
```bash
~/.fly/bin/flyctl ssh sftp shell
put scripts/seeds/seed_inferred_pairs.py /tmp/seed_inferred_pairs.py
```
```bash
~/.fly/bin/flyctl ssh console -C "DB_PATH=/data/indiestack.db python3 /tmp/seed_inferred_pairs.py"
```

**Step 4: Verify pair count increased**

```bash
curl -s "https://indiestack.ai/api/tools/supabase/compatible" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Supabase compatible: {d[\"total_compatible\"]}')"
```

Expected: Significantly more compatible tools than before (was 16).

**Step 5: Commit**

```bash
git add scripts/seeds/seed_inferred_pairs.py
git commit -m "feat: seed script to generate inferred compatibility pairs from framework/category data"
```

---

### Task 2: Enhance Comparison Pages with Intelligence Data

**Files:**
- Modify: `src/indiestack/routes/compare.py` (tool_column function, line 23-82)
- Modify: `src/indiestack/routes/alternatives.py` (deep comparison at line 502)
- Read: `src/indiestack/db.py` (get_compatible_tools_grouped, search_tools)

**What this does:** Add agent-verified data to existing comparison and alternatives pages — success rates, health status badges, compatibility indicators, and MCP citation counts.

**Step 1: Enhance the comparison page columns**

In `compare.py`, the `tool_column()` function renders each tool. Add after the existing fields:
- Health status badge (active/stale/dead)
- MCP citation count (`mcp_view_count`)
- Agent success rate (from `agent_actions` if available)
- Trust tier badge
- GitHub freshness indicator
- Compatibility indicator if the two tools being compared are a known pair

**Step 2: Add compatibility banner to comparison page**

When comparing two tools, check if they're in `tool_pairs`. If yes, show a banner:
"These tools are verified compatible — used together successfully in X agent reports."

If they're in `tool_conflicts`, show a warning:
"Warning: These tools have been reported as incompatible."

If neither, show neutral:
"No compatibility data yet. Be the first to report — use `report_outcome` in the MCP server."

**Step 3: Enhance deep comparison page in alternatives.py**

The `/alternatives/{competitor}/vs/{tool}` page (line 502) should include:
- Health status of the indie alternative
- GitHub stars and freshness
- "AI agents recommend this tool X times" (mcp_view_count)
- Trust tier badge

**Step 4: Test by visiting comparison pages**

```bash
curl -s -o /dev/null -w "%{http_code}" "https://indiestack.ai/compare/supabase-vs-pocketbase"
curl -s -o /dev/null -w "%{http_code}" "https://indiestack.ai/alternatives"
```

**Step 5: Commit**

```bash
git add src/indiestack/routes/compare.py src/indiestack/routes/alternatives.py
git commit -m "feat: enhance comparison pages with agent-verified intelligence data"
```

---

### Task 3: Expand Sitemap for Comparison Page Coverage

**Files:**
- Modify: sitemap generation code (find via grep for "sitemap")
- Read: `src/indiestack/db.py` (get_all_competitors, tool_pairs queries)

**What this does:** Ensure all comparison and alternatives pages are in the sitemap for Google indexing. Currently the sitemap may only include tool pages — we need comparison pairs and alternatives pages too.

**Step 1: Find the sitemap route**

```bash
grep -rn "sitemap" src/indiestack/
```

**Step 2: Add comparison URLs**

For each tool pair in `tool_pairs` with `success_count > 0`, add:
`/compare/{slug_a}-vs-{slug_b}`

For each unique competitor in `replaces` data, add:
`/alternatives/{competitor_slug}`

**Step 3: Verify sitemap includes new URLs**

```bash
curl -s "https://indiestack.ai/sitemap.xml" | grep -c "compare"
curl -s "https://indiestack.ai/sitemap.xml" | grep -c "alternatives"
```

**Step 4: Commit**

```bash
git add src/indiestack/routes/sitemap.py  # or wherever sitemap lives
git commit -m "feat: expand sitemap with comparison and alternatives pages for SEO"
```

---

### Task 4: Traffic Plays — External Listings

**Files:** None (external actions)

**Step 1: Submit IndieStack to StackShare**

Visit https://stackshare.io and submit IndieStack as a developer tool:
- Category: Developer Tools
- Description: "The discovery layer between AI coding agents and 3,100+ proven developer tools. MCP server lets AI agents search, compare, and recommend tools before generating boilerplate."
- URL: https://indiestack.ai
- Tags: mcp, ai, developer-tools, tool-discovery

**Step 2: Create company profile on StackShare**

Post IndieStack's tech stack: Python, FastAPI, SQLite, Fly.io, Claude, aiosqlite, httpx

**Step 3: Submit to AlternativeTo**

Visit https://alternativeto.net and submit IndieStack as an alternative to StackShare:
- Description: "AI-native developer tool discovery. Unlike StackShare's stale self-reported data, IndieStack uses agent-verified outcomes to recommend tools that actually work together."
- Tags: developer tools, tool comparison, tech stack, MCP

**Step 4: Build "IndieStack vs StackShare" page**

Create a dedicated landing page at `/alternatives/stackshare` or `/compare/indiestack-vs-stackshare` that captures "stackshare alternative" search traffic. Content:
- "StackShare shows what devs say they use. IndieStack shows what actually works."
- Side-by-side feature comparison
- Call to action: install the MCP server

**Step 5: Log to hub**

```bash
curl -s -X POST -H "X-Hub-Secret: $HUB_SECRET" -H "Content-Type: application/json" \
  "$HUB_URL/activity" -d '{"actor":"patrick","action":"submitted IndieStack to StackShare + AlternativeTo","detail":"traffic play for StackShare replacement strategy"}'
```

---

### Task 5: Deploy and Verify

**Files:** None

**Step 1: Run smoke test**

```bash
cd ~/indiestack && python3 smoke_test.py
```

**Step 2: Deploy**

```bash
cd ~/indiestack && ~/.fly/bin/flyctl deploy --remote-only
```

**Step 3: Run seed script on production**

Upload and execute `seed_inferred_pairs.py` against production DB.

**Step 4: Verify endpoints**

```bash
curl -s -o /dev/null -w "%{http_code}" "https://indiestack.ai/compare/supabase-vs-pocketbase"
curl -s "https://indiestack.ai/api/tools/supabase/compatible" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Compatible: {d[\"total_compatible\"]}')"
curl -s -o /dev/null -w "%{http_code}" "https://indiestack.ai/alternatives"
```

**Step 5: Commit version bump if needed and notify**

```bash
bash ~/.claude/telegram.sh "StackShare replacement Phase 1+2 shipped. Compatibility graph seeded, comparison pages enhanced."
```

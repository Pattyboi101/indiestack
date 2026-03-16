# Stacks Overhaul — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the empty `/stacks` page into an intelligence-powered stack discovery hub with auto-generated framework and use-case stacks built from 5,031 compatibility pairs.

**Architecture:** Add intelligence columns to the existing `stacks` table. Write a seed script that queries the compatibility graph, groups tools by framework and use case, scores them, and inserts auto-generated stacks. Rewrite the `/stacks` index page and enhance the detail page with compatibility matrices and intelligence badges. Update MCP tools and API to return richer stack data.

**Tech Stack:** Python 3 / aiosqlite / FastAPI / existing db.py functions / existing route files / existing components (stack_card, tool_card, _health_badge, _intelligence_section)

---

### Task 1: Schema Migration — Add Intelligence Columns to `stacks` Table

**Files:**
- Modify: `src/indiestack/db.py` (add migration in `_run_migrations()`, around line 960+)

**What this does:** Add 8 new columns to the existing `stacks` table for intelligence metadata. Uses ALTER TABLE ADD COLUMN (safe in SQLite, no data loss, no downtime). Existing curated stacks get sensible defaults.

**Step 1: Add the migration block**

In `db.py`, find `_run_migrations()`. Add a new migration block after the last existing one. Each ADD COLUMN is wrapped in try/except to be idempotent (column may already exist on re-run).

```python
# ── Stacks intelligence columns ──
for col_sql in [
    "ALTER TABLE stacks ADD COLUMN source TEXT NOT NULL DEFAULT 'curated'",
    "ALTER TABLE stacks ADD COLUMN framework TEXT",
    "ALTER TABLE stacks ADD COLUMN use_case TEXT",
    "ALTER TABLE stacks ADD COLUMN replaces_json TEXT",
    "ALTER TABLE stacks ADD COLUMN confidence_score REAL NOT NULL DEFAULT 0",
    "ALTER TABLE stacks ADD COLUMN total_tokens_saved INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE stacks ADD COLUMN tool_count_cached INTEGER NOT NULL DEFAULT 0",
    "ALTER TABLE stacks ADD COLUMN generated_at TIMESTAMP",
]:
    try:
        await db.execute(col_sql)
    except Exception:
        pass
await db.commit()
```

**Step 2: Test locally**

```bash
cd ~/indiestack && python3 -c "
import asyncio, aiosqlite
async def test():
    db = await aiosqlite.connect('/tmp/test_stacks_migration.db')
    # Create stacks table (minimal)
    await db.execute('CREATE TABLE IF NOT EXISTS stacks (id INTEGER PRIMARY KEY, slug TEXT UNIQUE, title TEXT, description TEXT DEFAULT \"\", cover_emoji TEXT DEFAULT \"\", discount_percent INTEGER DEFAULT 15, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    # Run migrations
    for col_sql in [
        'ALTER TABLE stacks ADD COLUMN source TEXT NOT NULL DEFAULT \"curated\"',
        'ALTER TABLE stacks ADD COLUMN framework TEXT',
        'ALTER TABLE stacks ADD COLUMN use_case TEXT',
        'ALTER TABLE stacks ADD COLUMN replaces_json TEXT',
        'ALTER TABLE stacks ADD COLUMN confidence_score REAL NOT NULL DEFAULT 0',
        'ALTER TABLE stacks ADD COLUMN total_tokens_saved INTEGER NOT NULL DEFAULT 0',
        'ALTER TABLE stacks ADD COLUMN tool_count_cached INTEGER NOT NULL DEFAULT 0',
        'ALTER TABLE stacks ADD COLUMN generated_at TIMESTAMP',
    ]:
        try:
            await db.execute(col_sql)
        except Exception:
            pass
    await db.commit()
    # Verify
    cursor = await db.execute('PRAGMA table_info(stacks)')
    cols = await cursor.fetchall()
    print('Columns:', [c[1] for c in cols])
    assert 'source' in [c[1] for c in cols]
    assert 'confidence_score' in [c[1] for c in cols]
    print('PASS')
    await db.close()
asyncio.run(test())
"
```

Expected: Prints all column names including new ones, then `PASS`.

**Step 3: Run idempotency test** — run the same script again. Should print `PASS` again (no errors on duplicate ADD COLUMN).

**Step 4: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add intelligence columns to stacks table for auto-generation"
```

---

### Task 2: Seed Script — Auto-Generate Stacks from Compatibility Data

**Files:**
- Create: `scripts/seeds/seed_auto_stacks.py`
- Read: `src/indiestack/db.py` (NEED_MAPPINGS at line 579, CATEGORY_TOKEN_COSTS, tool_pairs table schema at line 1310)
- Read: `scripts/seeds/seed_inferred_pairs.py` (for pattern reference)

**What this does:** Query the compatibility graph and tool metadata. Generate framework stacks (tools sharing `frameworks_tested`) and use-case stacks (from NEED_MAPPINGS + composite combos). Score each stack using the tiered confidence model. UPSERT into the `stacks` table.

**Step 1: Write the seed script**

```python
#!/usr/bin/env python3
"""Generate auto stacks from compatibility pairs, framework affinity, and use-case mappings.

Two strategies:
1. Framework stacks — tools sharing frameworks_tested values across 2+ categories.
2. Use-case stacks — composite stacks from NEED_MAPPINGS complementary categories.

Scoring: tiered confidence from pair data (inferred=0.3, verified=0.7-1.0, conflict=-1).

Usage:
    python3 seed_auto_stacks.py              # insert into DB
    python3 seed_auto_stacks.py --dry-run    # preview without inserting
    python3 seed_auto_stacks.py --verbose    # show scoring breakdown
"""
import argparse
import asyncio
import aiosqlite
import json
import os
from collections import defaultdict
from datetime import datetime, timezone

DB_PATH = os.environ.get("DB_PATH", "/data/indiestack.db")

# Max tools per auto-generated stack
MAX_TOOLS_PER_STACK = 8
# Minimum tools required for a framework stack
MIN_TOOLS_FRAMEWORK = 4
# Minimum categories represented for a framework stack
MIN_CATEGORIES_FRAMEWORK = 2
# Minimum tools for a single-category use-case stack
MIN_TOOLS_USECASE = 3

# Composite stack definitions: name -> list of category slugs
COMPOSITE_STACKS = {
    "saas-starter": {
        "title": "SaaS Starter",
        "emoji": "\U0001f680",
        "categories": ["authentication", "payments", "analytics-metrics", "email-marketing"],
        "description": "Everything you need to launch a SaaS — auth, payments, analytics, and email. All indie, all compatible.",
    },
    "api-backend": {
        "title": "API Backend",
        "emoji": "\u26a1",
        "categories": ["api-tools", "monitoring-uptime", "developer-tools"],
        "description": "Build and monitor production APIs with indie tools that work together.",
    },
    "indie-marketing": {
        "title": "Indie Marketing",
        "emoji": "\U0001f4c8",
        "categories": ["analytics-metrics", "seo-tools", "email-marketing", "forms-surveys"],
        "description": "Track, optimise, and grow — analytics, SEO, email, and forms from indie makers.",
    },
    "full-stack-indie": {
        "title": "Full-Stack Indie",
        "emoji": "\U0001f3d7\ufe0f",
        "categories": ["authentication", "payments", "analytics-metrics", "monitoring-uptime", "email-marketing"],
        "description": "The complete indie stack — auth, payments, analytics, monitoring, and email. No big-tech dependencies.",
    },
    "content-platform": {
        "title": "Content Platform",
        "emoji": "\U0001f4dd",
        "categories": ["cms-content", "seo-tools", "analytics-metrics", "email-marketing"],
        "description": "Build a content-driven site with CMS, SEO, analytics, and email — all indie.",
    },
    "ai-builder": {
        "title": "AI Builder",
        "emoji": "\U0001f9e0",
        "categories": ["ai-dev-tools", "ai-automation", "api-tools", "monitoring-uptime"],
        "description": "Ship AI features with indie MCP servers, automation tools, APIs, and monitoring.",
    },
}

# Token costs per category (must match db.py CATEGORY_TOKEN_COSTS)
CATEGORY_TOKEN_COSTS = {
    "authentication": 60000, "payments": 70000, "analytics-metrics": 50000,
    "email-marketing": 50000, "invoicing-billing": 80000, "monitoring-uptime": 50000,
    "forms-surveys": 40000, "scheduling-booking": 50000, "cms-content": 60000,
    "customer-support": 60000, "seo-tools": 40000, "file-management": 40000,
    "crm-sales": 90000, "developer-tools": 50000, "ai-automation": 80000,
    "design-creative": 60000, "feedback-reviews": 40000, "social-media": 50000,
    "project-management": 100000, "landing-pages": 30000, "api-tools": 50000,
    "ai-dev-tools": 120000, "games-entertainment": 120000,
    "learning-education": 80000, "newsletters-content": 60000,
    "creative-tools": 100000,
}

# Framework display names
FRAMEWORK_NAMES = {
    "nextjs": "Next.js", "next.js": "Next.js", "react": "React", "vue": "Vue",
    "svelte": "Svelte", "django": "Django", "flask": "Flask", "rails": "Rails",
    "laravel": "Laravel", "express": "Express", "fastapi": "FastAPI",
    "nuxt": "Nuxt", "angular": "Angular", "sveltekit": "SvelteKit",
}

# Competitors per category (for replaces_json)
CATEGORY_COMPETITORS = {
    "authentication": ["Auth0", "Firebase Auth", "Okta", "Cognito"],
    "payments": ["Stripe", "PayPal", "Square"],
    "analytics-metrics": ["Google Analytics", "Mixpanel", "Amplitude"],
    "email-marketing": ["Mailchimp", "SendGrid", "ConvertKit"],
    "monitoring-uptime": ["Datadog", "PagerDuty", "Pingdom"],
    "api-tools": ["Postman", "Swagger", "Kong"],
    "ai-dev-tools": ["GitHub Copilot", "Cursor"],
    "ai-automation": ["OpenAI", "AWS AI"],
    "seo-tools": ["Ahrefs", "SEMrush", "Moz"],
    "cms-content": ["WordPress", "Contentful", "Sanity"],
    "forms-surveys": ["Typeform", "Google Forms"],
    "crm-sales": ["Salesforce", "HubSpot"],
    "developer-tools": ["Postman", "Ngrok"],
}


def pair_key(a, b):
    """Normalise a tool pair to alphabetical order."""
    return tuple(sorted([a, b]))


def calculate_pair_score(success_count):
    """Tiered scoring: inferred=0.3, verified=0.7-1.0."""
    if success_count == 0:
        return 0.3  # inferred pair
    return 0.7 + (0.3 * min(success_count / 10, 1.0))


def calculate_tool_score(tool, pair_count):
    """Score a tool for ranking within a stack."""
    # Trust tier weight
    trust = 1  # new
    if tool.get("is_verified"):
        trust = 3  # verified
    elif (tool.get("mcp_view_count") or 0) >= 5:
        trust = 2  # tested (proxy)
    mcp = tool.get("mcp_view_count") or 0
    return (trust * 10) + (mcp * 0.1) + (pair_count * 2)


async def get_pair_index(db):
    """Build a dict of all pairs: (slug_a, slug_b) -> success_count."""
    cursor = await db.execute("SELECT tool_a_slug, tool_b_slug, success_count FROM tool_pairs")
    rows = await cursor.fetchall()
    index = {}
    for r in rows:
        key = (r["tool_a_slug"], r["tool_b_slug"])
        index[key] = r["success_count"]
    return index


async def get_conflict_index(db):
    """Build a set of conflicting pairs."""
    cursor = await db.execute("SELECT tool_a_slug, tool_b_slug FROM tool_conflicts")
    rows = await cursor.fetchall()
    return {(r["tool_a_slug"], r["tool_b_slug"]) for r in rows}


def stack_confidence(tool_slugs, pair_index, conflict_index):
    """Calculate confidence score for a set of tools."""
    n = len(tool_slugs)
    if n < 2:
        return 0.0
    max_pairs = n * (n - 1) // 2
    total_score = 0.0
    for i, a in enumerate(tool_slugs):
        for b in tool_slugs[i + 1:]:
            key = pair_key(a, b)
            if key in conflict_index:
                total_score -= 1.0
            elif key in pair_index:
                total_score += calculate_pair_score(pair_index[key])
    return round(total_score / max_pairs, 3) if max_pairs > 0 else 0.0


async def upsert_stack(db, slug, title, description, emoji, source, framework,
                       use_case, replaces_json, confidence, tokens_saved,
                       tool_ids, dry_run, verbose):
    """Insert or update a stack and its tools."""
    now = datetime.now(timezone.utc).isoformat()
    tool_count = len(tool_ids)

    if verbose:
        print(f"  [{source}] {title} ({slug})")
        print(f"    Tools: {tool_count}, Confidence: {confidence:.1%}, Tokens saved: {tokens_saved:,}")
        print(f"    Replaces: {replaces_json}")

    if dry_run:
        return

    # UPSERT — preserves row id (critical for stack_tools FK)
    await db.execute("""
        INSERT INTO stacks (slug, title, description, cover_emoji, source, framework,
                            use_case, replaces_json, confidence_score, total_tokens_saved,
                            tool_count_cached, generated_at, discount_percent)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
        ON CONFLICT(slug) DO UPDATE SET
            title=excluded.title, description=excluded.description,
            cover_emoji=excluded.cover_emoji, source=excluded.source,
            framework=excluded.framework, use_case=excluded.use_case,
            replaces_json=excluded.replaces_json,
            confidence_score=excluded.confidence_score,
            total_tokens_saved=excluded.total_tokens_saved,
            tool_count_cached=excluded.tool_count_cached,
            generated_at=excluded.generated_at
        WHERE source != 'curated'
    """, (slug, title, description, emoji, source, framework,
          use_case, json.dumps(replaces_json) if replaces_json else None,
          confidence, tokens_saved, tool_count, now, ))

    # Get the stack id (may be new insert or existing)
    cursor = await db.execute("SELECT id FROM stacks WHERE slug = ?", (slug,))
    row = await cursor.fetchone()
    if not row:
        return
    stack_id = row["id"]

    # Replace stack_tools for auto stacks (safe — no purchases on auto stacks)
    await db.execute("DELETE FROM stack_tools WHERE stack_id = ?", (stack_id,))
    for pos, tool_id in enumerate(tool_ids):
        await db.execute(
            "INSERT INTO stack_tools (stack_id, tool_id, position) VALUES (?, ?, ?)",
            (stack_id, tool_id, pos),
        )


async def main(dry_run=False, verbose=False):
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = lambda cursor, row: {
        col[0]: row[idx] for idx, col in enumerate(cursor.description)
    }

    # Load all approved tools
    cursor = await db.execute("""
        SELECT t.id, t.slug, t.name, t.tagline, t.frameworks_tested,
               t.is_verified, t.mcp_view_count, t.health_status,
               c.slug as category_slug, c.name as category_name
        FROM tools t JOIN categories c ON t.category_id = c.id
        WHERE t.status = 'approved'
    """)
    all_tools = await cursor.fetchall()
    print(f"Loaded {len(all_tools)} approved tools")

    # Build indexes
    pair_index = await get_pair_index(db)
    conflict_index = await get_conflict_index(db)
    print(f"Loaded {len(pair_index)} pairs, {len(conflict_index)} conflicts")

    # Tool lookup by slug
    tool_by_slug = {t["slug"]: t for t in all_tools}

    # Count pairs per tool
    pair_counts = defaultdict(int)
    for (a, b) in pair_index:
        pair_counts[a] += 1
        pair_counts[b] += 1

    # ── Strategy A: Framework Stacks ──────────────────────────────────
    print("\n=== Framework Stacks ===")
    framework_index = defaultdict(list)
    for t in all_tools:
        fw_raw = t.get("frameworks_tested")
        if not fw_raw or not fw_raw.strip():
            continue
        for fw in fw_raw.split(","):
            fw = fw.strip().lower()
            if fw:
                framework_index[fw].append(t)

    framework_stacks_count = 0
    for fw, fw_tools in sorted(framework_index.items(), key=lambda x: -len(x[1])):
        # Check minimum thresholds
        categories = {t["category_slug"] for t in fw_tools}
        if len(fw_tools) < MIN_TOOLS_FRAMEWORK or len(categories) < MIN_CATEGORIES_FRAMEWORK:
            if verbose:
                print(f"  SKIP {fw}: {len(fw_tools)} tools, {len(categories)} categories (below threshold)")
            continue

        # Filter: only tools with at least one pair connection to another tool in the group
        slugs_in_group = {t["slug"] for t in fw_tools}
        connected_tools = []
        for t in fw_tools:
            has_pair = False
            for other_slug in slugs_in_group:
                if other_slug != t["slug"] and pair_key(t["slug"], other_slug) in pair_index:
                    has_pair = True
                    break
            if has_pair:
                connected_tools.append(t)

        if len(connected_tools) < MIN_TOOLS_FRAMEWORK:
            if verbose:
                print(f"  SKIP {fw}: only {len(connected_tools)} connected tools (below threshold)")
            continue

        # Filter out stale/dead tools
        healthy_tools = [t for t in connected_tools if t.get("health_status") not in ("dead",)]

        if len(healthy_tools) < MIN_TOOLS_FRAMEWORK:
            if verbose:
                print(f"  SKIP {fw}: only {len(healthy_tools)} healthy tools")
            continue

        # Score and rank
        scored = [(t, calculate_tool_score(t, pair_counts.get(t["slug"], 0))) for t in healthy_tools]
        scored.sort(key=lambda x: -x[1])
        selected = [t for t, _ in scored[:MAX_TOOLS_PER_STACK]]
        selected_slugs = [t["slug"] for t in selected]

        # Calculate metadata
        categories_covered = {t["category_slug"] for t in selected}
        replaces = []
        for cat in categories_covered:
            replaces.extend(CATEGORY_COMPETITORS.get(cat, []))
        replaces = sorted(set(replaces))

        tokens_saved = sum(CATEGORY_TOKEN_COSTS.get(cat, 50000) for cat in categories_covered)
        confidence = stack_confidence(selected_slugs, pair_index, conflict_index)

        fw_display = FRAMEWORK_NAMES.get(fw, fw.title())
        slug = f"{fw.replace('.', '').replace(' ', '-')}-stack"
        title = f"{fw_display} Stack"
        desc = (f"{len(selected)} indie tools verified compatible with {fw_display} — "
                f"{', '.join(sorted(categories_covered)[:4])}{'...' if len(categories_covered) > 4 else ''}. "
                f"Replaces {', '.join(replaces[:3])}{'...' if len(replaces) > 3 else ''}.")

        await upsert_stack(
            db, slug, title, desc, FRAMEWORK_NAMES.get(fw, "\U0001f4e6"),
            "auto-framework", fw, None, replaces, confidence, tokens_saved,
            [t["id"] for t in selected], dry_run, verbose,
        )
        framework_stacks_count += 1

    print(f"Framework stacks generated: {framework_stacks_count}")

    # ── Strategy B: Use-Case Composite Stacks ─────────────────────────
    print("\n=== Use-Case Composite Stacks ===")

    # Build category -> tools index
    category_tools = defaultdict(list)
    for t in all_tools:
        category_tools[t["category_slug"]].append(t)

    composite_count = 0
    for slug, spec in COMPOSITE_STACKS.items():
        selected = []
        categories_covered = set()

        for cat_slug in spec["categories"]:
            cat_tools = category_tools.get(cat_slug, [])
            if not cat_tools:
                if verbose:
                    print(f"  {slug}: no tools in category {cat_slug}")
                continue

            # Score tools: prefer those with pairs to already-selected tools
            scored_cat = []
            for t in cat_tools:
                # Base score
                base = calculate_tool_score(t, pair_counts.get(t["slug"], 0))
                # Bonus for pairs with already-selected tools
                cross_pairs = 0
                for existing in selected:
                    if pair_key(t["slug"], existing["slug"]) in pair_index:
                        cross_pairs += 1
                score = base + (cross_pairs * 5)
                scored_cat.append((t, score))

            scored_cat.sort(key=lambda x: -x[1])

            # Pick top 2 from this category
            for t, _ in scored_cat[:2]:
                if t["slug"] not in {s["slug"] for s in selected}:
                    selected.append(t)
                    categories_covered.add(cat_slug)

        if len(selected) < 3:
            if verbose:
                print(f"  SKIP {slug}: only {len(selected)} tools selected")
            continue

        selected_slugs = [t["slug"] for t in selected]
        replaces = []
        for cat in categories_covered:
            replaces.extend(CATEGORY_COMPETITORS.get(cat, []))
        replaces = sorted(set(replaces))

        tokens_saved = sum(CATEGORY_TOKEN_COSTS.get(cat, 50000) for cat in categories_covered)
        confidence = stack_confidence(selected_slugs, pair_index, conflict_index)

        await upsert_stack(
            db, slug, spec["title"], spec["description"], spec["emoji"],
            "auto-usecase", None, slug, replaces, confidence, tokens_saved,
            [t["id"] for t in selected], dry_run, verbose,
        )
        composite_count += 1

    print(f"Composite use-case stacks generated: {composite_count}")

    # ── Summary ───────────────────────────────────────────────────────
    if not dry_run:
        await db.commit()

    # Count total
    cursor = await db.execute("SELECT source, COUNT(*) as cnt FROM stacks GROUP BY source")
    rows = await cursor.fetchall()
    print("\n=== Stack Summary ===")
    for r in rows:
        print(f"  {r['source']}: {r['cnt']}")

    await db.close()

    if dry_run:
        print("\n[DRY RUN] No rows inserted.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate auto stacks from compatibility data")
    parser.add_argument("--dry-run", action="store_true", help="Preview without inserting")
    parser.add_argument("--verbose", action="store_true", help="Show scoring breakdown")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run, verbose=args.verbose))
```

**Step 2: Test locally with dry run**

```bash
cd ~/indiestack && DB_PATH=/data/indiestack.db python3 scripts/seeds/seed_auto_stacks.py --dry-run --verbose
```

Expected: Prints framework and composite stacks with scoring breakdowns, no DB writes. Should see 5+ framework stacks and all 6 composite stacks.

**Step 3: Run against production DB**

```bash
cd ~/indiestack && DB_PATH=/data/indiestack.db python3 scripts/seeds/seed_auto_stacks.py --verbose
```

Expected: Inserts stacks, prints summary showing `auto-framework: N`, `auto-usecase: M`.

**Step 4: Verify**

```bash
cd ~/indiestack && python3 -c "
import asyncio, aiosqlite
async def check():
    db = await aiosqlite.connect('/data/indiestack.db')
    db.row_factory = lambda c, r: {col[0]: r[i] for i, col in enumerate(c.description)}
    c = await db.execute('SELECT slug, source, confidence_score, tool_count_cached FROM stacks ORDER BY confidence_score DESC')
    for row in await c.fetchall():
        print(f\"{row['slug']:30s} {row['source']:16s} conf={row['confidence_score']:.1%} tools={row['tool_count_cached']}\")
    await db.close()
asyncio.run(check())
"
```

**Step 5: Commit**

```bash
git add scripts/seeds/seed_auto_stacks.py
git commit -m "feat: auto-generate stacks from compatibility pairs and framework affinity"
```

---

### Task 3: Rewrite `/stacks` Index Page

**Files:**
- Modify: `src/indiestack/routes/stacks.py` (replace `stacks_index` function, lines 41-109)
- Modify: `src/indiestack/routes/components.py` (enhance `stack_card` function, lines 990-1010)
- Modify: `src/indiestack/db.py` (add `get_stacks_by_source()` function, after `get_all_stacks` at line 4373)

**What this does:** Rewrite the stacks index page with the intelligence-first layout: hero + stats → Stack Generator CTA → Framework Stacks → Use Case Stacks → Community Stacks.

**Step 1: Add `get_stacks_by_source()` to db.py**

After `get_all_stacks()` (line 4373), add:

```python
async def get_stacks_by_source(db, source: str):
    """Get stacks filtered by source, with tool counts, ordered by confidence."""
    cursor = await db.execute(
        """SELECT s.*, COUNT(st.tool_id) as tool_count
           FROM stacks s LEFT JOIN stack_tools st ON st.stack_id = s.id
           WHERE s.source = ?
           GROUP BY s.id ORDER BY s.confidence_score DESC""", (source,))
    return await cursor.fetchall()


async def get_stack_stats(db):
    """Get aggregate stats for the stacks page hero."""
    stats = {}
    c = await db.execute("SELECT COUNT(*) as cnt FROM tool_pairs")
    stats["pair_count"] = (await c.fetchone())["cnt"]
    c = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")
    stats["tool_count"] = (await c.fetchone())["cnt"]
    c = await db.execute("SELECT COUNT(*) as cnt FROM stacks WHERE source LIKE 'auto-%'")
    stats["auto_stack_count"] = (await c.fetchone())["cnt"]
    c = await db.execute("SELECT COUNT(DISTINCT framework) as cnt FROM stacks WHERE framework IS NOT NULL")
    stats["framework_count"] = (await c.fetchone())["cnt"]
    return stats
```

**Step 2: Update imports in stacks.py**

At line 15, add the new functions to the import:

```python
from indiestack.db import (
    get_all_stacks, get_stacks_by_source, get_stack_stats,
    get_stack_with_tools, get_stack_by_id,
    create_stack_purchase, get_stack_purchase_by_session,
    get_stack_purchase_by_token, get_active_subscription,
    create_purchase, CATEGORY_TOKEN_COSTS,
    get_user_stack_by_username, get_public_stacks,
)
```

**Step 3: Enhance `stack_card` in components.py**

Replace the `stack_card` function (lines 990-1010) with a version that shows intelligence metadata:

```python
def stack_card(stack: dict) -> str:
    """Card component for a stack — shows intelligence metadata for auto stacks."""
    emoji = stack.get('cover_emoji', '') or '\U0001f4e6'
    title = escape(str(stack['title']))
    desc = escape(str(stack.get('description', '')))
    slug = escape(str(stack['slug']))
    count = stack.get('tool_count', 0) or stack.get('tool_count_cached', 0)
    confidence = stack.get('confidence_score', 0) or 0
    tokens_k = (stack.get('total_tokens_saved', 0) or 0) // 1000
    source = stack.get('source', 'curated')

    # Badges row
    badges = []
    badges.append(
        f'<span style="font-size:12px;font-weight:600;color:var(--ink-light);background:var(--cream-dark);'
        f'padding:4px 12px;border-radius:999px;">{count} tool{"s" if count != 1 else ""}</span>'
    )
    if confidence > 0:
        conf_pct = f"{confidence:.0%}"
        badges.append(
            f'<span style="font-size:12px;font-weight:600;color:#065F46;background:#D1FAE5;'
            f'padding:4px 12px;border-radius:999px;">{conf_pct} confidence</span>'
        )
    if tokens_k > 0:
        badges.append(
            f'<span style="font-size:12px;font-weight:600;color:#92400E;background:#FEF3C7;'
            f'padding:4px 12px;border-radius:999px;">~{tokens_k}k tokens saved</span>'
        )
    discount = stack.get('discount_percent', 0)
    if discount and discount > 0 and source == 'curated':
        badges.append(f'<span class="badge badge-success" style="font-weight:700;">{discount}% off</span>')

    badges_html = "\n".join(badges)

    # Replaces line
    replaces_html = ""
    replaces_raw = stack.get('replaces_json')
    if replaces_raw:
        try:
            replaces = json.loads(replaces_raw) if isinstance(replaces_raw, str) else replaces_raw
            if replaces:
                preview = ", ".join(replaces[:3])
                if len(replaces) > 3:
                    preview += f" +{len(replaces) - 3} more"
                replaces_html = (
                    f'<p style="color:var(--ink-muted);font-size:12px;margin-top:8px;">'
                    f'Replaces: {escape(preview)}</p>'
                )
        except (json.JSONDecodeError, TypeError):
            pass

    return f"""
    <a href="/stacks/{slug}" class="card" style="text-decoration:none;color:inherit;display:block;">
        <span style="font-size:32px;display:block;margin-bottom:8px;">{emoji}</span>
        <h3 style="font-family:var(--font-display);font-size:17px;margin-bottom:8px;color:var(--ink);">{title}</h3>
        <p style="color:var(--ink-muted);font-size:14px;margin-bottom:12px;
                  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">{desc}</p>
        <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;">
            {badges_html}
        </div>
        {replaces_html}
    </a>
    """
```

Note: add `import json` at the top of components.py if not already present.

**Step 4: Rewrite `stacks_index` in stacks.py**

Replace lines 41-109 with:

```python
@router.get("/stacks", response_class=HTMLResponse)
async def stacks_index(request: Request):
    """Browse all Stacks — intelligence-powered discovery hub."""
    db = request.state.db

    # Load data
    from indiestack.db import get_stacks_by_source, get_stack_stats
    stats = await get_stack_stats(db)
    framework_stacks = await get_stacks_by_source(db, "auto-framework")
    usecase_stacks = await get_stacks_by_source(db, "auto-usecase")
    curated_stacks_list = await get_stacks_by_source(db, "curated")
    community_stacks_list = await get_public_stacks(db, limit=6)

    # ── Hero + Stats ──
    hero_html = f"""
    <div style="text-align:center;margin-bottom:48px;">
        <h1 style="font-family:var(--font-display);font-size:clamp(28px,5vw,48px);color:var(--ink);margin-bottom:12px;">
            Stacks That Actually Work
        </h1>
        <p style="color:var(--ink-muted);font-size:18px;max-width:600px;margin:0 auto 32px;">
            Built from {stats['pair_count']:,} compatibility pairs across {stats['tool_count']:,} tools.
            Every stack is backed by agent-verified data, not self-reported profiles.
        </p>
        <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:24px;">
            <div style="text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{stats['pair_count']:,}+</div>
                <div style="font-size:13px;color:var(--ink-muted);font-weight:600;">Compatibility Pairs</div>
            </div>
            <div style="text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{stats['tool_count']:,}+</div>
                <div style="font-size:13px;color:var(--ink-muted);font-weight:600;">Tools Indexed</div>
            </div>
            <div style="text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{stats['auto_stack_count']}</div>
                <div style="font-size:13px;color:var(--ink-muted);font-weight:600;">Auto-Generated Stacks</div>
            </div>
            <div style="text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{stats['framework_count']}</div>
                <div style="font-size:13px;color:var(--ink-muted);font-weight:600;">Frameworks Covered</div>
            </div>
        </div>
    </div>
    """

    # ── Stack Generator CTA ──
    generator_html = """
    <div class="card" style="padding:32px;text-align:center;margin-bottom:48px;
                             border:2px solid var(--accent);background:var(--cream);">
        <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
            Build Your Stack
        </h2>
        <p style="color:var(--ink-muted);font-size:15px;margin-bottom:20px;max-width:500px;margin-left:auto;margin-right:auto;">
            Paste your package.json or describe what you're building.
            We'll find indie tools that work together and replace your big-tech dependencies.
        </p>
        <a href="/stacks/generator" class="btn btn-primary" style="font-size:16px;padding:14px 32px;">
            Try the Stack Generator &rarr;
        </a>
    </div>
    """

    # ── Framework Stacks ──
    if framework_stacks:
        fw_cards = "\n".join(stack_card(s) for s in framework_stacks)
        framework_html = f"""
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
                Framework Stacks
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:20px;">
                Tools grouped by framework compatibility — auto-generated from {stats['pair_count']:,} verified pairs.
            </p>
            <div class="card-grid">{fw_cards}</div>
        </div>
        """
    else:
        framework_html = ""

    # ── Use Case Stacks ──
    if usecase_stacks:
        uc_cards = "\n".join(stack_card(s) for s in usecase_stacks)
        usecase_html = f"""
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
                Use Case Stacks
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:20px;">
                Pre-built combinations for common project types — every tool has compatibility data with the others.
            </p>
            <div class="card-grid">{uc_cards}</div>
        </div>
        """
    else:
        usecase_html = ""

    # ── Curated Stacks (admin-created) ──
    if curated_stacks_list:
        curated_cards = "\n".join(stack_card(s) for s in curated_stacks_list)
        curated_html = f"""
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
                Curated Bundles
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:20px;">
                Hand-picked tool bundles with bundle discounts.
            </p>
            <div class="card-grid">{curated_cards}</div>
        </div>
        """
    else:
        curated_html = ""

    # ── Community Stacks ──
    if community_stacks_list:
        community_cards = "\n".join(user_stack_card(s) for s in community_stacks_list)
        community_html = f"""
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
                Community Stacks
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:20px;">
                See what other developers are building with.
            </p>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px;">
                {community_cards}
            </div>
        </div>
        """
    else:
        community_html = """
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
                Community Stacks
            </h2>
            <div class="card" style="padding:32px;text-align:center;">
                <p style="color:var(--ink-muted);font-size:15px;margin-bottom:16px;">
                    Share your stack &mdash; show what tools you use and why.
                </p>
                <a href="/dashboard/my-stack" class="btn btn-primary" style="font-size:14px;padding:12px 24px;">
                    Create Your Stack &rarr;
                </a>
            </div>
        </div>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:1000px;">
        {hero_html}
        {generator_html}
        {framework_html}
        {usecase_html}
        {curated_html}
        {community_html}
    </div>
    """
    return HTMLResponse(page_shell(
        "Stacks — Intelligence-Powered Tool Combinations",
        body,
        description="Stacks built from 5,000+ compatibility pairs. Framework stacks, use-case bundles, and community stacks — all backed by agent-verified data.",
        user=request.state.user,
        canonical="/stacks",
    ))
```

**Step 5: Test**

```bash
cd ~/indiestack && python3 smoke_test.py
```

Also manually verify:
```bash
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/stacks"
```

Expected: 200, page shows hero, Stack Generator CTA, framework stacks, use-case stacks.

**Step 6: Commit**

```bash
git add src/indiestack/db.py src/indiestack/routes/stacks.py src/indiestack/routes/components.py
git commit -m "feat: rewrite /stacks page with intelligence-first layout and auto-generated stacks"
```

---

### Task 4: Enhance Stack Detail Page with Compatibility Matrix

**Files:**
- Modify: `src/indiestack/routes/stacks.py` (replace `stack_detail` function, lines 345-442)
- Read: `src/indiestack/routes/compare.py` (reuse `_health_badge` and `_intelligence_section` patterns)

**What this does:** Add a compatibility matrix, intelligence badges per tool, and JSON-LD structured data to the stack detail page.

**Step 1: Add helper imports at the top of stacks.py**

After the existing imports (around line 26), add:

```python
from indiestack.routes.compare import _health_badge, _intelligence_section
```

**Step 2: Replace the `stack_detail` function**

Replace lines 345-442 with the enhanced version that includes:
- Source badge (auto-generated / curated)
- Stats row (confidence, tokens saved, replaces)
- Compatibility matrix for stacks ≤ 6 tools (grid) or summary for larger stacks
- Enhanced tool cards with intelligence badges
- Batch-queried success rates (one query, not N+1)
- JSON-LD structured data
- Stripe checkout only for curated stacks

```python
@router.get("/stacks/{slug}", response_class=HTMLResponse)
async def stack_detail(request: Request, slug: str):
    """Stack detail page with compatibility matrix and intelligence data."""
    db = request.state.db
    stack, tools = await get_stack_with_tools(db, slug)

    if not stack:
        body = """
        <div class="container" style="text-align:center;padding:80px 24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Stack not found</h1>
            <p style="color:var(--ink-muted);margin-top:12px;">This stack doesn&rsquo;t exist or has been removed.</p>
            <a href="/stacks" class="btn btn-primary" style="margin-top:24px;">Browse Stacks</a>
        </div>
        """
        return HTMLResponse(page_shell("Stack Not Found", body, user=request.state.user), status_code=404)

    source = stack.get('source', 'curated')
    confidence = stack.get('confidence_score', 0) or 0
    tokens_saved = stack.get('total_tokens_saved', 0) or 0
    tokens_k = tokens_saved // 1000
    emoji = stack.get('cover_emoji', '') or '\U0001f4e6'
    title = escape(str(stack['title']))
    desc = escape(str(stack.get('description', '')))

    # Source badge
    if source == 'auto-framework':
        source_badge = '<span style="font-size:12px;font-weight:600;color:#1E40AF;background:#DBEAFE;padding:4px 12px;border-radius:999px;">Auto-generated from framework data</span>'
    elif source == 'auto-usecase':
        source_badge = '<span style="font-size:12px;font-weight:600;color:#7C3AED;background:#EDE9FE;padding:4px 12px;border-radius:999px;">Auto-generated from compatibility data</span>'
    else:
        source_badge = '<span style="font-size:12px;font-weight:600;color:#065F46;background:#D1FAE5;padding:4px 12px;border-radius:999px;">Curated by IndieStack</span>'

    # Replaces list
    replaces_html = ""
    replaces_raw = stack.get('replaces_json')
    if replaces_raw:
        try:
            replaces = json.loads(replaces_raw) if isinstance(replaces_raw, str) else replaces_raw
            if replaces:
                replaces_html = f'<span style="color:var(--ink-muted);font-size:14px;">Replaces: {escape(", ".join(replaces))}</span>'
        except (json.JSONDecodeError, TypeError):
            pass

    # Stats row
    stats_items = [f'<span style="font-weight:600;">{len(tools)} tools</span>']
    if confidence > 0:
        stats_items.append(f'<span style="color:#065F46;font-weight:600;">{confidence:.0%} confidence</span>')
    if tokens_k > 0:
        stats_items.append(f'<span>~{tokens_k}k tokens saved</span>')
    stats_html = ' &middot; '.join(stats_items)

    # ── Compatibility Matrix ──
    tool_slugs = [t['slug'] for t in tools]
    slug_set = tuple(tool_slugs)

    # Query pairs between tools in this stack
    if len(slug_set) >= 2:
        placeholders = ",".join("?" * len(slug_set))
        cursor = await db.execute(
            f"SELECT tool_a_slug, tool_b_slug, success_count FROM tool_pairs WHERE tool_a_slug IN ({placeholders}) AND tool_b_slug IN ({placeholders})",
            slug_set + slug_set,
        )
        pair_rows = await cursor.fetchall()
        pairs = {(r['tool_a_slug'], r['tool_b_slug']): r['success_count'] for r in pair_rows}

        cursor = await db.execute(
            f"SELECT tool_a_slug, tool_b_slug FROM tool_conflicts WHERE tool_a_slug IN ({placeholders}) AND tool_b_slug IN ({placeholders})",
            slug_set + slug_set,
        )
        conflict_rows = await cursor.fetchall()
        conflicts = {(r['tool_a_slug'], r['tool_b_slug']) for r in conflict_rows}
    else:
        pairs = {}
        conflicts = set()

    # Render matrix or summary
    n = len(tools)
    max_pairs = n * (n - 1) // 2
    verified_count = sum(1 for sc in pairs.values() if sc > 0)
    inferred_count = sum(1 for sc in pairs.values() if sc == 0)
    conflict_count = len(conflicts)

    if n <= 6 and n >= 2:
        # Full grid matrix
        header_cells = ''.join(
            f'<th style="font-size:11px;font-weight:600;padding:6px 8px;color:var(--ink-muted);transform:rotate(-45deg);white-space:nowrap;">{escape(t["name"][:12])}</th>'
            for t in tools
        )
        rows_html = ""
        for i, t1 in enumerate(tools):
            cells = f'<td style="font-size:12px;font-weight:600;padding:6px 8px;color:var(--ink);">{escape(t1["name"][:12])}</td>'
            for j, t2 in enumerate(tools):
                if i == j:
                    cells += '<td style="text-align:center;color:var(--ink-muted);">&mdash;</td>'
                else:
                    a, b = sorted([t1['slug'], t2['slug']])
                    key = (a, b)
                    if key in conflicts:
                        cells += '<td style="text-align:center;color:#DC2626;font-weight:700;" title="Known conflict">&#10007;</td>'
                    elif key in pairs:
                        if pairs[key] > 0:
                            cells += '<td style="text-align:center;color:#059669;font-weight:700;" title="Verified compatible">&#10003;</td>'
                        else:
                            cells += '<td style="text-align:center;color:var(--ink-muted);" title="Inferred compatible">&middot;</td>'
                    else:
                        cells += '<td style="text-align:center;"></td>'
            rows_html += f'<tr>{cells}</tr>'

        matrix_html = f"""
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:12px;">
                Compatibility Matrix
            </h2>
            <div style="overflow-x:auto;">
                <table style="border-collapse:collapse;width:auto;">
                    <thead><tr><th></th>{header_cells}</tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
            <div style="display:flex;gap:16px;margin-top:12px;font-size:12px;color:var(--ink-muted);">
                <span><span style="color:#059669;font-weight:700;">&#10003;</span> Verified</span>
                <span><span style="color:var(--ink-muted);">&middot;</span> Inferred</span>
                <span><span style="color:#DC2626;font-weight:700;">&#10007;</span> Conflict</span>
            </div>
        </div>
        """
    elif n >= 2:
        # Summary for larger stacks
        total_known = verified_count + inferred_count
        matrix_html = f"""
        <div class="card" style="padding:20px;margin-bottom:40px;">
            <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin-bottom:8px;">Compatibility</h3>
            <p style="color:var(--ink-muted);font-size:14px;">
                {total_known} of {max_pairs} possible pairs have compatibility data.
                {f'<span style="color:#059669;font-weight:600;">{verified_count} verified</span>, ' if verified_count else ''}
                {f'<span>{inferred_count} inferred</span>' if inferred_count else ''}
                {f', <span style="color:#DC2626;font-weight:600;">{conflict_count} conflicts</span>' if conflict_count else ''}
            </p>
        </div>
        """
    else:
        matrix_html = ""

    # ── Batch-query success rates ──
    success_rates = {}
    if tool_slugs:
        placeholders = ",".join("?" * len(tool_slugs))
        cursor = await db.execute(
            f"""SELECT tool_slug,
                       SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as wins,
                       COUNT(*) as total
                FROM agent_actions
                WHERE action='report_outcome' AND tool_slug IN ({placeholders})
                GROUP BY tool_slug""",
            tuple(tool_slugs),
        )
        for r in await cursor.fetchall():
            total = r['total']
            rate = round(r['wins'] / total * 100) if total > 0 else 0
            success_rates[r['tool_slug']] = {"rate": rate, "total": total}

    # ── Enhanced tool cards ──
    tool_cards = []
    for t in tools:
        name = escape(str(t['name']))
        tagline = escape(str(t.get('tagline', '')))
        t_slug = escape(str(t['slug']))
        cat_name = escape(str(t.get('category_name', '')))

        # Health badge
        health = t.get('health_status') or 'unknown'
        health_html = _health_badge(health)

        # MCP citations
        mcp_views = t.get('mcp_view_count') or 0
        citation_html = f'<span style="font-size:13px;color:var(--ink-muted);">Cited by agents {mcp_views:,}x</span>' if mcp_views > 0 else ''

        # Success rate
        sr = success_rates.get(t['slug'])
        sr_html = ''
        if sr and sr['total'] >= 3:
            sr_html = f'<span style="font-size:13px;color:#059669;font-weight:600;">{sr["rate"]}% success rate ({sr["total"]} reports)</span>'

        # Compatibility count within this stack
        compat_count = 0
        for other in tools:
            if other['slug'] != t['slug']:
                key = tuple(sorted([t['slug'], other['slug']]))
                if key in pairs:
                    compat_count += 1
        compat_html = f'<span style="font-size:12px;color:var(--ink-muted);">Compatible with {compat_count}/{len(tools)-1} tools in stack</span>' if len(tools) > 1 else ''

        # Price
        pp = t.get('price_pence', 0) or 0
        price_str = f"\u00a3{pp/100:.2f}" if pp > 0 else "Free"

        tool_cards.append(f"""
        <a href="/tool/{t_slug}" class="card" style="text-decoration:none;color:inherit;display:block;padding:20px;">
            <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:8px;">
                <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin:0;">{name}</h3>
                {health_html}
            </div>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:12px;">{tagline}</p>
            <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:8px;">
                <span style="font-size:12px;font-weight:600;color:var(--ink-light);background:var(--cream-dark);padding:3px 10px;border-radius:999px;">{cat_name}</span>
                <span style="font-size:13px;font-weight:600;color:var(--ink);">{price_str}</span>
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;">
                {citation_html}
                {sr_html}
            </div>
            {f'<div style="margin-top:8px;">{compat_html}</div>' if compat_html else ''}
        </a>
        """)

    cards_html = "\n".join(tool_cards)

    # ── Pricing (curated only) ──
    if source == 'curated' and MARKETPLACE_ENABLED:
        discount_percent = stack.get('discount_percent', 15)
        full_price = sum(t.get('price_pence', 0) or 0 for t in tools)
        discount_amount = full_price * discount_percent // 100
        bundle_price = full_price - discount_amount
        has_paid = full_price > 0
        if has_paid:
            pricing_html = f"""
            <div class="card" style="text-align:center;padding:32px;margin-bottom:40px;">
                <div style="font-size:14px;color:var(--ink-muted);text-decoration:line-through;">{format_price(full_price)}</div>
                <div style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin-bottom:4px;">{format_price(bundle_price)}</div>
                <div class="badge badge-success" style="font-weight:700;margin-bottom:16px;">Save {discount_percent}%</div>
                <form method="post" action="/api/checkout-stack">
                    <input type="hidden" name="stack_id" value="{stack['id']}">
                    <button type="submit" class="btn btn-primary" style="font-size:16px;padding:16px 40px;">Buy This Stack &rarr;</button>
                </form>
            </div>
            """
        else:
            pricing_html = ""
    else:
        pricing_html = ""

    # ── JSON-LD ──
    tools_jsonld = ",".join(
        f'{{"@type":"SoftwareApplication","name":"{escape(str(t["name"]))}","url":"{BASE_URL}/tool/{escape(str(t["slug"]))}"}}' for t in tools
    )
    jsonld = f"""
    <script type="application/ld+json">
    {{
        "@context":"https://schema.org",
        "@type":"ItemList",
        "name":"{title}",
        "description":"{escape(desc[:200])}",
        "numberOfItems":{len(tools)},
        "itemListElement":[{tools_jsonld}]
    }}
    </script>
    """

    body = f"""
    {jsonld}
    <div class="container" style="padding:48px 24px;max-width:900px;">
        <a href="/stacks" style="color:var(--ink-muted);font-size:14px;font-weight:600;">&larr; All Stacks</a>
        <div style="margin-top:16px;margin-bottom:32px;">
            <span style="font-size:48px;">{emoji}</span>
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);margin-top:12px;">
                {title}
            </h1>
            <div style="margin-top:8px;margin-bottom:8px;">{source_badge}</div>
            <p style="color:var(--ink-muted);font-size:17px;margin-top:8px;max-width:600px;">{desc}</p>
            <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:12px;font-size:14px;color:var(--ink-muted);">
                {stats_html}
            </div>
            {f'<div style="margin-top:8px;">{replaces_html}</div>' if replaces_html else ''}
        </div>

        {pricing_html}
        {matrix_html}

        <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin:0 0 20px;">
            What&rsquo;s in the Stack
        </h2>
        <div class="card-grid">{cards_html}</div>
    </div>
    """
    return HTMLResponse(page_shell(
        f"{stack['title']} — Stack",
        body,
        description=f"{len(tools)} indie developer tools that work together. {stack.get('description', '')}",
        user=request.state.user,
        canonical=f"/stacks/{slug}",
    ))
```

**Step 3: Test**

```bash
cd ~/indiestack && python3 smoke_test.py
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/stacks/nextjs-stack"
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/stacks/saas-starter"
```

Expected: 200 for auto-generated stack pages.

**Step 4: Commit**

```bash
git add src/indiestack/routes/stacks.py
git commit -m "feat: add compatibility matrix and intelligence badges to stack detail page"
```

---

### Task 5: Enhance `/api/stacks` and MCP Tools

**Files:**
- Modify: `src/indiestack/main.py` (enhance `/api/stacks` endpoint, lines 1855-1870)
- Modify: `src/indiestack/mcp_server.py` (enhance `list_stacks` output, lines 1253-1279)

**What this does:** Add intelligence metadata to the API response and make the MCP `list_stacks` tool return richer, more useful output. Add query param filters to `/api/stacks`.

**Step 1: Enhance `/api/stacks` in main.py**

Replace lines 1855-1870:

```python
@app.get("/api/stacks")
async def api_stacks(request: Request, source: str = "", framework: str = "", sort: str = ""):
    """JSON API for tool stacks — curated and auto-generated."""
    d = request.state.db
    if source:
        stacks = await db.get_stacks_by_source(d, source)
    else:
        stacks = await db.get_all_stacks(d)

    if framework:
        stacks = [s for s in stacks if (s.get('framework') or '').lower() == framework.lower()]

    if sort == "confidence":
        stacks.sort(key=lambda s: s.get('confidence_score', 0) or 0, reverse=True)

    results = []
    for s in stacks:
        entry = {
            "title": s['title'],
            "slug": s.get('slug', ''),
            "description": s.get('description', ''),
            "cover_emoji": s.get('cover_emoji', ''),
            "tool_count": int(s.get('tool_count', 0) or s.get('tool_count_cached', 0)),
            "indiestack_url": f"{BASE_URL}/stacks/{s.get('slug', '')}",
            "source": s.get('source', 'curated'),
        }
        # Add intelligence fields if present
        if s.get('confidence_score'):
            entry["confidence_score"] = round(s['confidence_score'], 3)
        if s.get('total_tokens_saved'):
            entry["total_tokens_saved"] = s['total_tokens_saved']
        if s.get('framework'):
            entry["framework"] = s['framework']
        if s.get('replaces_json'):
            try:
                entry["replaces"] = json.loads(s['replaces_json']) if isinstance(s['replaces_json'], str) else s['replaces_json']
            except (json.JSONDecodeError, TypeError):
                pass
        results.append(entry)

    return JSONResponse({"stacks": results, "total": len(results)})
```

Add `import json` at the top of main.py if not already present.

**Step 2: Enhance `list_stacks` in mcp_server.py**

Replace lines 1253-1279:

```python
@mcp.tool(annotations=ToolAnnotations(readOnlyHint=True))
async def list_stacks(*, ctx: Context) -> str:
    """List all stacks on IndieStack — curated bundles and auto-generated combinations.

    Stacks are pre-built combinations of developer tools for common use cases.
    Auto-generated stacks are built from 5,000+ compatibility pairs — every tool
    has verified or inferred compatibility data with the others in the stack.
    """
    client = _get_client(ctx)
    await ctx.report_progress(progress=0, total=1)
    try:
        data = await _api_get(client, "/api/stacks", {"sort": "confidence"})
    except Exception as e:
        raise ToolError(f"Could not fetch stacks: {e}")
    await ctx.report_progress(progress=1, total=1)

    stacks = data.get("stacks", [])
    if not stacks:
        return "No stacks available yet. Use build_stack(needs='auth,payments,...') to generate a custom stack for your requirements."

    lines = [f"# IndieStack Stacks ({len(stacks)} stacks)\n"]
    for s in stacks:
        emoji = s.get("cover_emoji", "")
        source = s.get("source", "curated")
        source_label = {"curated": "curated", "auto-framework": "framework", "auto-usecase": "use-case"}.get(source, source)
        confidence = s.get("confidence_score", 0)
        conf_str = f" | {confidence:.0%} confidence" if confidence else ""
        tokens = s.get("total_tokens_saved", 0)
        tokens_str = f" | ~{tokens // 1000}k tokens saved" if tokens else ""
        replaces = s.get("replaces", [])
        replaces_str = f"\n  Replaces: {', '.join(replaces[:4])}" if replaces else ""

        lines.append(
            f"- {emoji} **{s['title']}** ({source_label}{conf_str}{tokens_str})\n"
            f"  {s.get('description', '')}\n"
            f"  {s.get('tool_count', 0)} tools | {s.get('indiestack_url', '')}"
            f"{replaces_str}"
        )
    return "\n".join(lines)
```

**Step 3: Add `get_stacks_by_source` to imports in main.py**

Find the db import block in main.py and add `get_stacks_by_source`:

```python
from indiestack.db import get_stacks_by_source  # add to existing import
```

**Step 4: Test**

```bash
curl -s "http://localhost:8000/api/stacks" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Total: {d[\"total\"]}'); [print(f'  {s[\"title\"]} [{s.get(\"source\",\"?\")}] conf={s.get(\"confidence_score\",0):.0%}') for s in d['stacks'][:5]]"
curl -s "http://localhost:8000/api/stacks?source=auto-framework" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Framework stacks: {d[\"total\"]}')"
```

**Step 5: Commit**

```bash
git add src/indiestack/main.py src/indiestack/mcp_server.py
git commit -m "feat: enhance /api/stacks and list_stacks MCP tool with intelligence metadata"
```

---

### Task 6: Add Auto-Generated Stacks to Sitemap

**Files:**
- Modify: `src/indiestack/main.py` (sitemap route — grep for "sitemap")

**What this does:** Add `/stacks/{slug}` URLs for auto-generated stacks to the sitemap, same pattern as the comparison pages we added earlier.

**Step 1: Find the sitemap route**

```bash
grep -n "sitemap" src/indiestack/main.py
```

**Step 2: Add stack URLs to sitemap**

After the existing sitemap entries, add:

```python
# Auto-generated stacks
auto_stacks = await db.get_all_stacks(d)
for s in auto_stacks:
    stack_slug = s.get('slug', '')
    if stack_slug:
        urls.append(f'<url><loc>{BASE_URL}/stacks/{stack_slug}</loc><changefreq>weekly</changefreq><priority>0.7</priority></url>')
```

**Step 3: Test**

```bash
curl -s "http://localhost:8000/sitemap.xml" | grep -c "stacks/"
```

Expected: Returns count matching number of auto-generated stacks.

**Step 4: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: add auto-generated stacks to sitemap for SEO indexing"
```

---

### Task 7: Deploy and Verify

**Files:** None — deployment and verification only.

**Step 1: Run smoke test**

```bash
cd ~/indiestack && python3 smoke_test.py
```

**Step 2: Commit any remaining changes**

```bash
git status
# If anything uncommitted, add and commit
```

**Step 3: Deploy**

```bash
cd ~/indiestack && ~/.fly/bin/flyctl deploy --remote-only
```

**Step 4: Run seed script on production**

```bash
# Upload seed script
~/.fly/bin/flyctl ssh sftp shell
put scripts/seeds/seed_auto_stacks.py /tmp/seed_auto_stacks.py

# Run it
~/.fly/bin/flyctl ssh console -C "DB_PATH=/data/indiestack.db python3 /tmp/seed_auto_stacks.py --verbose"
```

**Step 5: Verify endpoints**

```bash
curl -s -o /dev/null -w "%{http_code}" "https://indiestack.ai/stacks"
curl -s -o /dev/null -w "%{http_code}" "https://indiestack.ai/stacks/saas-starter"
curl -s "https://indiestack.ai/api/stacks" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Total stacks: {d[\"total\"]}')"
curl -s "https://indiestack.ai/api/stacks?source=auto-framework" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Framework stacks: {d[\"total\"]}')"
curl -s "https://indiestack.ai/sitemap.xml" | grep -c "stacks/"
```

**Step 6: Notify**

```bash
bash ~/.claude/telegram.sh "Stacks overhaul shipped. Auto-generated stacks from 5,031 compatibility pairs. Intelligence-first layout with compatibility matrices."
```

**Step 7: Log to hub**

```bash
curl -s -X POST -H "X-Hub-Secret: $HUB_SECRET" -H "Content-Type: application/json" \
  "$HUB_URL/activity" -d '{"actor":"patrick","action":"shipped stacks overhaul","detail":"auto-generated stacks from compatibility pairs, intelligence-first page layout, compatibility matrices"}'
```

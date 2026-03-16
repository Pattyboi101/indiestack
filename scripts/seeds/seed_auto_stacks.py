#!/usr/bin/env python3
"""Generate auto stacks from compatibility pairs, framework affinity, and use-case mappings.

Two strategies:
1. Framework stacks — tools sharing frameworks_tested values across 2+ categories.
2. Use-case stacks — composite stacks from complementary categories.

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

MAX_TOOLS_PER_STACK = 8
MIN_TOOLS_FRAMEWORK = 4
MIN_CATEGORIES_FRAMEWORK = 2
MIN_TOOLS_USECASE = 3

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

FRAMEWORK_NAMES = {
    "nextjs": "Next.js", "next.js": "Next.js", "react": "React", "vue": "Vue",
    "svelte": "Svelte", "django": "Django", "flask": "Flask", "rails": "Rails",
    "laravel": "Laravel", "express": "Express", "fastapi": "FastAPI",
    "nuxt": "Nuxt", "angular": "Angular", "sveltekit": "SvelteKit",
}

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
        return 0.3
    return 0.7 + (0.3 * min(success_count / 10, 1.0))


def calculate_tool_score(tool, pair_count):
    """Score a tool for ranking within a stack."""
    trust = 1
    if tool.get("is_verified"):
        trust = 3
    elif (tool.get("mcp_view_count") or 0) >= 5:
        trust = 2
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
                       use_case, replaces_list, confidence, tokens_saved,
                       tool_ids, dry_run, verbose):
    """Insert or update a stack and its tools."""
    now = datetime.now(timezone.utc).isoformat()
    tool_count = len(tool_ids)

    if verbose:
        print(f"  [{source}] {title} ({slug})")
        print(f"    Tools: {tool_count}, Confidence: {confidence:.1%}, Tokens saved: {tokens_saved:,}")
        print(f"    Replaces: {replaces_list}")

    if dry_run:
        return

    replaces_json = json.dumps(replaces_list) if replaces_list else None

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
          use_case, replaces_json, confidence, tokens_saved, tool_count, now))

    cursor = await db.execute("SELECT id FROM stacks WHERE slug = ?", (slug,))
    row = await cursor.fetchone()
    if not row:
        return
    stack_id = row["id"]

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

    cursor = await db.execute("""
        SELECT t.id, t.slug, t.name, t.tagline, t.frameworks_tested,
               t.is_verified, t.mcp_view_count, t.health_status,
               c.slug as category_slug, c.name as category_name
        FROM tools t JOIN categories c ON t.category_id = c.id
        WHERE t.status = 'approved'
    """)
    all_tools = await cursor.fetchall()
    print(f"Loaded {len(all_tools)} approved tools")

    pair_index = await get_pair_index(db)
    conflict_index = await get_conflict_index(db)
    print(f"Loaded {len(pair_index)} pairs, {len(conflict_index)} conflicts")

    tool_by_slug = {t["slug"]: t for t in all_tools}

    pair_counts = defaultdict(int)
    for (a, b) in pair_index:
        pair_counts[a] += 1
        pair_counts[b] += 1

    # ── Strategy A: Framework Stacks ──
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
        categories = {t["category_slug"] for t in fw_tools}
        if len(fw_tools) < MIN_TOOLS_FRAMEWORK or len(categories) < MIN_CATEGORIES_FRAMEWORK:
            if verbose:
                print(f"  SKIP {fw}: {len(fw_tools)} tools, {len(categories)} categories")
            continue

        slugs_in_group = {t["slug"] for t in fw_tools}
        connected_tools = []
        for t in fw_tools:
            has_pair = any(
                pair_key(t["slug"], other) in pair_index
                for other in slugs_in_group if other != t["slug"]
            )
            if has_pair:
                connected_tools.append(t)

        if len(connected_tools) < MIN_TOOLS_FRAMEWORK:
            if verbose:
                print(f"  SKIP {fw}: only {len(connected_tools)} connected tools")
            continue

        healthy_tools = [t for t in connected_tools if t.get("health_status") not in ("dead",)]
        if len(healthy_tools) < MIN_TOOLS_FRAMEWORK:
            if verbose:
                print(f"  SKIP {fw}: only {len(healthy_tools)} healthy tools")
            continue

        scored = [(t, calculate_tool_score(t, pair_counts.get(t["slug"], 0))) for t in healthy_tools]
        scored.sort(key=lambda x: -x[1])
        selected = [t for t, _ in scored[:MAX_TOOLS_PER_STACK]]
        selected_slugs = [t["slug"] for t in selected]

        categories_covered = {t["category_slug"] for t in selected}
        replaces = []
        for cat in sorted(categories_covered):
            replaces.extend(CATEGORY_COMPETITORS.get(cat, []))
        replaces = sorted(set(replaces))

        tokens_saved = sum(CATEGORY_TOKEN_COSTS.get(cat, 50000) for cat in categories_covered)
        confidence = stack_confidence(selected_slugs, pair_index, conflict_index)

        fw_display = FRAMEWORK_NAMES.get(fw, fw.title())
        slug = f"{fw.replace('.', '').replace(' ', '-')}-stack"
        title = f"{fw_display} Stack"
        cat_names = ", ".join(sorted(categories_covered)[:4])
        extra = "..." if len(categories_covered) > 4 else ""
        repl_preview = ", ".join(replaces[:3])
        repl_extra = "..." if len(replaces) > 3 else ""
        desc = (f"{len(selected)} indie tools verified compatible with {fw_display} — "
                f"{cat_names}{extra}. "
                f"Replaces {repl_preview}{repl_extra}.")

        await upsert_stack(
            db, slug, title, desc, FRAMEWORK_NAMES.get(fw, "\U0001f4e6"),
            "auto-framework", fw, None, replaces, confidence, tokens_saved,
            [t["id"] for t in selected], dry_run, verbose,
        )
        framework_stacks_count += 1

    print(f"Framework stacks generated: {framework_stacks_count}")

    # ── Strategy B: Use-Case Composite Stacks ──
    print("\n=== Use-Case Composite Stacks ===")

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

            scored_cat = []
            for t in cat_tools:
                base = calculate_tool_score(t, pair_counts.get(t["slug"], 0))
                cross_pairs = sum(
                    1 for existing in selected
                    if pair_key(t["slug"], existing["slug"]) in pair_index
                )
                score = base + (cross_pairs * 5)
                scored_cat.append((t, score))

            scored_cat.sort(key=lambda x: -x[1])

            for t, _ in scored_cat[:2]:
                if t["slug"] not in {s["slug"] for s in selected}:
                    selected.append(t)
                    categories_covered.add(cat_slug)

        if len(selected) < MIN_TOOLS_USECASE:
            if verbose:
                print(f"  SKIP {slug}: only {len(selected)} tools selected")
            continue

        selected_slugs = [t["slug"] for t in selected]
        replaces = []
        for cat in sorted(categories_covered):
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

    if not dry_run:
        await db.commit()

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

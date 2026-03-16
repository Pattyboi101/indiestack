#!/usr/bin/env python3
"""Generate inferred compatibility pairs from framework affinity and category complementarity.

Two strategies:
1. Framework affinity — tools sharing a framework (Next.js, Rails, etc.) in different
   categories are likely compatible.
2. Complementary categories — tools from naturally paired categories (auth × payments,
   analytics × monitoring, etc.) are inferred as compatible.

Large categories (developer-tools has 2,000+ tools) are capped to avoid cartesian explosions.
Tools with frameworks_tested data are prioritised when capping.

Usage:
    python3 seed_inferred_pairs.py              # insert into DB
    python3 seed_inferred_pairs.py --dry-run    # preview without inserting
"""
import argparse
import asyncio
import aiosqlite
import os
from collections import defaultdict

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

# Max tools per category side in complementary pairing.
# Prevents cartesian explosion from huge categories like developer-tools (2000+).
# 10 per side = ~100 pairs per combo, ~2000 total across 20 combos.
MAX_TOOLS_PER_CATEGORY = 10

# Max tools per framework group for affinity pairing.
MAX_TOOLS_PER_FRAMEWORK = 15

DB_PATH = os.environ.get("DB_PATH", "/data/indiestack.db")


def prioritised_subset(tools_list, max_n):
    """Return up to max_n tools, prioritising those with frameworks_tested data."""
    if len(tools_list) <= max_n:
        return tools_list
    # Sort: tools with frameworks_tested first, then by slug for determinism
    with_fw = [t for t in tools_list if t.get("frameworks_tested")]
    without_fw = [t for t in tools_list if not t.get("frameworks_tested")]
    combined = with_fw + without_fw
    return combined[:max_n]


async def main(dry_run: bool = False):
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = lambda cursor, row: {
        col[0]: row[idx] for idx, col in enumerate(cursor.description)
    }

    cursor = await db.execute("""
        SELECT t.slug, t.frameworks_tested, c.slug as category_slug
        FROM tools t JOIN categories c ON t.category_id = c.id
        WHERE t.status = 'approved'
    """)
    tools = await cursor.fetchall()
    print(f"Found {len(tools)} approved tools")

    # Build framework index — skip tools with no frameworks_tested
    framework_index = {}
    for t in tools:
        fw_raw = t.get("frameworks_tested")
        if not fw_raw or not fw_raw.strip():
            continue
        for fw in fw_raw.split(","):
            fw = fw.strip().lower()
            if fw:
                framework_index.setdefault(fw, []).append(t)

    # Build category index
    category_index = {}
    for t in tools:
        category_index.setdefault(t["category_slug"], []).append(t)

    # Track which category pair each pair came from (for summary)
    pair_sources = defaultdict(set)  # (a, b) -> set of source labels
    pairs = set()

    # Strategy 1: framework affinity (capped per framework)
    for fw, fw_tools in framework_index.items():
        capped = prioritised_subset(fw_tools, MAX_TOOLS_PER_FRAMEWORK)
        for i, t1 in enumerate(capped):
            for t2 in capped[i + 1 :]:
                if t1["category_slug"] != t2["category_slug"]:
                    a, b = sorted([t1["slug"], t2["slug"]])
                    pair_key = (a, b)
                    pairs.add(pair_key)
                    pair_sources[pair_key].add(f"framework:{fw}")

    print(f"Framework affinity pairs: {len(pairs)}")

    # Strategy 2: complementary categories (capped per side)
    cat_pairs_count = 0
    for cat_a, cat_b in COMPLEMENTARY_CATEGORIES:
        tools_a = prioritised_subset(category_index.get(cat_a, []), MAX_TOOLS_PER_CATEGORY)
        tools_b = prioritised_subset(category_index.get(cat_b, []), MAX_TOOLS_PER_CATEGORY)
        cat_label = f"{cat_a} x {cat_b}"
        for t1 in tools_a:
            for t2 in tools_b:
                a, b = sorted([t1["slug"], t2["slug"]])
                pair_key = (a, b)
                pairs.add(pair_key)
                pair_sources[pair_key].add(f"category:{cat_label}")
                cat_pairs_count += 1

    print(f"Complementary category pairs: {cat_pairs_count}")
    print(f"Total unique pairs (deduplicated): {len(pairs)}")

    # Summary by category pair
    cat_pair_counts = defaultdict(int)
    for pair_key, sources in pair_sources.items():
        for src in sources:
            if src.startswith("category:"):
                cat_pair_counts[src.removeprefix("category:")] += 1
    fw_pair_counts = defaultdict(int)
    for pair_key, sources in pair_sources.items():
        for src in sources:
            if src.startswith("framework:"):
                fw_pair_counts[src.removeprefix("framework:")] += 1

    print("\n--- Category pair breakdown ---")
    for label, count in sorted(cat_pair_counts.items(), key=lambda x: -x[1]):
        print(f"  {label}: {count} pairs")

    print("\n--- Framework breakdown ---")
    for fw, count in sorted(fw_pair_counts.items(), key=lambda x: -x[1])[:15]:
        print(f"  {fw}: {count} pairs")

    if dry_run:
        print("\n[DRY RUN] No rows inserted.")
        await db.close()
        return

    # Insert with batch commits every 100 rows
    inserted = 0
    skipped = 0
    batch = 0
    for a, b in pairs:
        try:
            await db.execute(
                """INSERT INTO tool_pairs (tool_a_slug, tool_b_slug, source, verified, success_count)
                   VALUES (?, ?, 'inferred', 0, 0)""",
                (a, b),
            )
            inserted += 1
            batch += 1
            if batch >= 100:
                await db.commit()
                batch = 0
        except aiosqlite.IntegrityError:
            skipped += 1

    # Final commit for remaining rows
    if batch > 0:
        await db.commit()

    await db.close()

    print(f"\nInserted: {inserted} new pairs")
    print(f"Skipped: {skipped} (already existed)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate inferred tool compatibility pairs")
    parser.add_argument("--dry-run", action="store_true", help="Preview without inserting")
    args = parser.parse_args()
    asyncio.run(main(dry_run=args.dry_run))

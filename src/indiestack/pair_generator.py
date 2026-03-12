"""
Auto-generate compatibility pairs for the tool_pairs table.

Strategies:
1. Framework affinity — tools sharing a framework but in different categories
2. Complementary categories — auth+payments, analytics+monitoring, etc.
3. Same-category popular tools — top tools by github_stars within a category

Usage:
    python3 -m indiestack.pair_generator --dry-run
    python3 -m indiestack.pair_generator --apply
"""

import argparse
import os
import sqlite3
from collections import defaultdict
from itertools import combinations

DB_PATH = os.environ.get("INDIESTACK_DB_PATH", "/data/indiestack.db")
MAX_PAIRS = 500

# Complementary category pairings (slug -> slug)
COMPLEMENTARY_CATEGORIES = [
    ("authentication", "payments"),
    ("authentication", "developer-tools"),
    ("analytics-metrics", "monitoring-uptime"),
    ("ai-automation", "ai-dev-tools"),
    ("email-marketing", "newsletters-content"),
    ("crm-sales", "invoicing-billing"),
    ("forms-surveys", "email-marketing"),
    ("landing-pages", "seo-tools"),
    ("project-management", "scheduling-booking"),
]


def get_tools(db: sqlite3.Connection) -> list[dict]:
    """Fetch all approved tools with relevant metadata."""
    cursor = db.execute("""
        SELECT t.slug, t.category_id, t.github_stars,
               t.frameworks_tested, t.api_type, t.auth_method, t.source_type,
               c.slug as category_slug
        FROM tools t
        JOIN categories c ON c.id = t.category_id
        WHERE t.status = 'approved'
        ORDER BY t.github_stars DESC
    """)
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def sorted_pair(a: str, b: str) -> tuple[str, str]:
    """Return slugs in alphabetical order for the UNIQUE constraint."""
    return (a, b) if a < b else (b, a)


def generate_framework_pairs(tools: list[dict]) -> list[tuple[str, str, str]]:
    """
    Pair tools that share at least one framework but are in different categories.
    Returns list of (slug_a, slug_b, source_label).
    """
    # Build framework -> tools index (only tools with frameworks_tested)
    framework_index: dict[str, list[dict]] = defaultdict(list)
    for tool in tools:
        fw = tool.get("frameworks_tested") or ""
        if not fw:
            continue
        for framework in fw.split(","):
            framework = framework.strip()
            if framework:
                framework_index[framework].append(tool)

    pairs: set[tuple[str, str]] = set()
    for framework, fw_tools in framework_index.items():
        # Only pair tools in different categories
        for i, a in enumerate(fw_tools):
            for b in fw_tools[i + 1:]:
                if a["category_slug"] != b["category_slug"]:
                    pairs.add(sorted_pair(a["slug"], b["slug"]))

    return [(a, b, "framework_affinity") for a, b in pairs]


def generate_complementary_pairs(tools: list[dict]) -> list[tuple[str, str, str]]:
    """
    Pair tools from complementary categories.
    Limits to top 10 tools per category (by github_stars) to avoid explosion.
    """
    # Build category_slug -> tools index
    cat_index: dict[str, list[dict]] = defaultdict(list)
    for tool in tools:
        cat_index[tool["category_slug"]].append(tool)

    pairs: list[tuple[str, str, str]] = []
    for cat_a_slug, cat_b_slug in COMPLEMENTARY_CATEGORIES:
        tools_a = cat_index.get(cat_a_slug, [])[:10]
        tools_b = cat_index.get(cat_b_slug, [])[:10]
        for a in tools_a:
            for b in tools_b:
                sa, sb = sorted_pair(a["slug"], b["slug"])
                pairs.append((sa, sb, "complementary_category"))

    return pairs


def generate_same_category_pairs(tools: list[dict]) -> list[tuple[str, str, str]]:
    """
    Pair top tools within the same category (top 5 by stars).
    """
    cat_index: dict[str, list[dict]] = defaultdict(list)
    for tool in tools:
        cat_index[tool["category_slug"]].append(tool)

    pairs: list[tuple[str, str, str]] = []
    for cat_slug, cat_tools in cat_index.items():
        top = cat_tools[:5]  # already sorted by github_stars DESC
        for a, b in combinations(top, 2):
            sa, sb = sorted_pair(a["slug"], b["slug"])
            pairs.append((sa, sb, "same_category_popular"))

    return pairs


def deduplicate_and_cap(
    all_pairs: list[tuple[str, str, str]], cap: int = MAX_PAIRS
) -> list[tuple[str, str, str]]:
    """Deduplicate by (slug_a, slug_b), keeping the first source seen. Cap total."""
    seen: set[tuple[str, str]] = set()
    result: list[tuple[str, str, str]] = []
    for slug_a, slug_b, source in all_pairs:
        key = (slug_a, slug_b)
        if key not in seen:
            seen.add(key)
            result.append((slug_a, slug_b, source))
            if len(result) >= cap:
                break
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Generate compatibility pairs for IndieStack's tool_pairs table."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Preview pairs without inserting")
    mode.add_argument("--apply", action="store_true", help="Insert pairs into the database")
    parser.add_argument("--db", default=DB_PATH, help=f"Path to SQLite database (default: {DB_PATH})")
    parser.add_argument("--cap", type=int, default=MAX_PAIRS, help=f"Max pairs to generate (default: {MAX_PAIRS})")
    args = parser.parse_args()

    db = sqlite3.connect(args.db)

    tools = get_tools(db)
    print(f"Loaded {len(tools)} approved tools")

    # Generate pairs from each strategy (framework affinity first — highest signal)
    framework_pairs = generate_framework_pairs(tools)
    complementary_pairs = generate_complementary_pairs(tools)
    same_cat_pairs = generate_same_category_pairs(tools)

    print(f"  Framework affinity:      {len(framework_pairs)} raw pairs")
    print(f"  Complementary category:  {len(complementary_pairs)} raw pairs")
    print(f"  Same-category popular:   {len(same_cat_pairs)} raw pairs")

    # Merge: framework first (highest quality), then complementary, then same-category
    all_pairs = framework_pairs + complementary_pairs + same_cat_pairs
    final_pairs = deduplicate_and_cap(all_pairs, cap=args.cap)

    # Count by source
    source_counts: dict[str, int] = defaultdict(int)
    for _, _, source in final_pairs:
        source_counts[source] += 1

    print(f"\nFinal pairs: {len(final_pairs)} (capped at {args.cap})")
    for source, count in sorted(source_counts.items()):
        print(f"  {source}: {count}")

    if args.dry_run:
        print("\n-- DRY RUN: no changes made --")
        print("\nSample pairs:")
        for slug_a, slug_b, source in final_pairs[:20]:
            print(f"  {slug_a} <-> {slug_b}  ({source})")
        if len(final_pairs) > 20:
            print(f"  ... and {len(final_pairs) - 20} more")
    elif args.apply:
        inserted = 0
        skipped = 0
        for slug_a, slug_b, source in final_pairs:
            try:
                cursor = db.execute(
                    """
                    INSERT INTO tool_pairs (tool_a_slug, tool_b_slug, source, verified, success_count)
                    VALUES (?, ?, ?, 0, 1)
                    ON CONFLICT(tool_a_slug, tool_b_slug) DO NOTHING
                    """,
                    (slug_a, slug_b, source),
                )
                if cursor.rowcount > 0:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"  Error inserting {slug_a} <-> {slug_b}: {e}")
                skipped += 1

        db.commit()
        print(f"\nInserted: {inserted} new pairs")
        print(f"Skipped:  {skipped} (already existed)")

    db.close()


if __name__ == "__main__":
    main()

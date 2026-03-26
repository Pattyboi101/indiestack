#!/usr/bin/env python3
"""
Apply recategorisation decisions from moves.json.

Usage:
    # Dry run (default) — just print what would change
    python3 scripts/recategorise_apply.py --db backups/indiestack-XXXX.db

    # Apply to local backup
    python3 scripts/recategorise_apply.py --db backups/indiestack-XXXX.db --apply

    # Generate SQL for production (batched for Fly SSH)
    python3 scripts/recategorise_apply.py --sql --batch-size 50

Rules:
    - Skip tools with upvote_count > 0 (humans chose their category)
    - Update both tools.category_id AND tool_categories junction table
"""

import json
import sqlite3
import sys
from collections import Counter

MOVES_FILE = "scripts/moves.json"
if "--moves" in sys.argv:
    MOVES_FILE = sys.argv[sys.argv.index("--moves") + 1]

DB_PATH = None
if "--db" in sys.argv:
    DB_PATH = sys.argv[sys.argv.index("--db") + 1]

APPLY = "--apply" in sys.argv
SQL_MODE = "--sql" in sys.argv

BATCH_SIZE = 50
if "--batch-size" in sys.argv:
    BATCH_SIZE = int(sys.argv[sys.argv.index("--batch-size") + 1])


def main():
    with open(MOVES_FILE) as f:
        moves = json.load(f)

    print(f"Loaded {len(moves)} moves from {MOVES_FILE}")

    if SQL_MODE:
        # Generate SQL batches for production
        print(f"\n-- SQL for production (batches of {BATCH_SIZE})")
        print(f"-- Total moves: {len(moves)} (upvote check included in WHERE clause)\n")

        all_stmts = []
        for m in moves:
            tid = m["id"]
            new_cat = m["new_category_id"]
            name = m["name"].replace("'", "''")
            # Update tools table (skip if upvotes > 0)
            all_stmts.append(
                f"UPDATE tools SET category_id = {new_cat} WHERE id = {tid} AND upvote_count = 0; -- {name}"
            )
            # Update tool_categories junction: update primary row
            all_stmts.append(
                f"UPDATE tool_categories SET category_id = {new_cat} WHERE tool_id = {tid} AND is_primary = 1;"
            )

        # Print in batches
        batch_num = 0
        for i in range(0, len(all_stmts), BATCH_SIZE * 2):
            batch_num += 1
            batch = all_stmts[i:i + BATCH_SIZE * 2]
            print(f"-- Batch {batch_num} ({len(batch) // 2} tools)")
            for stmt in batch:
                print(stmt)
            print()

        return

    if not DB_PATH:
        print("Error: --db <path> required for dry run or apply mode")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    applied = 0
    skipped_upvotes = 0
    skipped_missing = 0
    by_target = Counter()

    for m in moves:
        tool_id = m["id"]
        new_cat = m["new_category_id"]
        old_cat = m["old_category_id"]
        name = m["name"]
        new_cat_name = m["new_category_name"]
        score = m["score"]
        matches = m.get("matches", [])

        # Look up tool in DB
        row = conn.execute(
            "SELECT id, name, upvote_count, category_id FROM tools WHERE id = ?",
            (tool_id,)
        ).fetchone()

        if not row:
            print(f"  SKIP (not found): {name} [id={tool_id}]")
            skipped_missing += 1
            continue

        if row["upvote_count"] > 0:
            print(f"  SKIP (upvotes={row['upvote_count']}): {name} -> {new_cat_name}")
            skipped_upvotes += 1
            continue

        match_str = ", ".join(matches)
        print(f"  MOVE [{score}]: {name} -> {new_cat_name} ({match_str})")
        by_target[new_cat_name] += 1

        if APPLY:
            # 1. Update tools.category_id
            conn.execute(
                "UPDATE tools SET category_id = ? WHERE id = ?",
                (new_cat, tool_id)
            )
            # 2. Update tool_categories junction: update primary row's category
            #    First check if a primary row exists
            tc_row = conn.execute(
                "SELECT rowid FROM tool_categories WHERE tool_id = ? AND is_primary = 1",
                (tool_id,)
            ).fetchone()
            if tc_row:
                # Delete old primary, insert new (handles unique constraint)
                conn.execute(
                    "DELETE FROM tool_categories WHERE tool_id = ? AND is_primary = 1",
                    (tool_id,)
                )
                conn.execute(
                    "INSERT OR REPLACE INTO tool_categories (tool_id, category_id, is_primary) VALUES (?, ?, 1)",
                    (tool_id, new_cat)
                )
            else:
                # No primary row — insert one
                conn.execute(
                    "INSERT OR REPLACE INTO tool_categories (tool_id, category_id, is_primary) VALUES (?, ?, 1)",
                    (tool_id, new_cat)
                )

        applied += 1

    if APPLY:
        conn.commit()
        print(f"\nCommitted changes to {DB_PATH}")

    conn.close()

    # Summary
    print(f"\n{'=' * 60}")
    print(f"SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total moves in file: {len(moves)}")
    print(f"Applied{'   ' if APPLY else ' (dry run)'}: {applied}")
    print(f"Skipped (upvotes > 0): {skipped_upvotes}")
    print(f"Skipped (not found):   {skipped_missing}")
    print()
    print(f"{'Target Category':<30s} {'Count':>5s}")
    print(f"{'─' * 35}")
    for cat, count in sorted(by_target.items(), key=lambda x: -x[1]):
        print(f"{cat:<30s} {count:>5d}")
    print(f"{'─' * 35}")
    print(f"{'TOTAL':<30s} {applied:>5d}")


if __name__ == "__main__":
    main()

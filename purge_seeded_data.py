#!/usr/bin/env python3
"""Purge ALL fake/seeded social proof from IndieStack database.

Removes test users, fake reviews, wishlists, upvotes, views, subscribers,
maker updates, search logs, milestones, and page views — leaving only real
tool listings, maker profiles, categories, collections, and stacks intact.

Usage:
    python3 purge_seeded_data.py          # interactive confirmation
    python3 purge_seeded_data.py --yes    # skip confirmation
"""

import os
import sqlite3
import sys

# Match the DB path from db.py / seed_tools.py
DB_PATH = os.environ.get("INDIESTACK_DB_PATH", "/data/indiestack.db")
if not os.path.exists(os.path.dirname(DB_PATH) or "/data"):
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "indiestack.db")

# Tables to report on (order matters for display)
TABLES_TO_COUNT = [
    "users",
    "sessions",
    "reviews",
    "wishlists",
    "notifications",
    "subscribers",
    "maker_updates",
    "upvotes",
    "tool_views",
    "page_views",
    "search_logs",
    "milestones",
    "tools",
    "makers",
    "categories",
]


def table_exists(conn, name):
    row = conn.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row[0] > 0


def safe_count(conn, table):
    if not table_exists(conn, table):
        return 0
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def get_counts(conn):
    return {t: safe_count(conn, t) for t in TABLES_TO_COUNT}


def print_counts(label, counts):
    print(f"\n{'=' * 50}")
    print(f"  {label}")
    print(f"{'=' * 50}")
    for table, count in counts.items():
        print(f"  {table:20s} {count:>8,}")
    print()


def main():
    skip_confirm = "--yes" in sys.argv

    print(f"IndieStack Seeded Data Purge")
    print(f"Database: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Set INDIESTACK_DB_PATH or run from the project directory.")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # --- Gather before counts ---
    before = get_counts(conn)
    print_counts("BEFORE PURGE", before)

    # Count test users
    test_user_count = conn.execute(
        "SELECT COUNT(*) FROM users WHERE email LIKE 'test%@indiestack.dev'"
    ).fetchone()[0]

    fake_sub_count = 0
    if table_exists(conn, "subscribers"):
        fake_sub_count = conn.execute(
            "SELECT COUNT(*) FROM subscribers WHERE email LIKE '%@example.com'"
        ).fetchone()[0]

    # --- Show what will be deleted ---
    print("The following will be DELETED:")
    print(f"  - ALL reviews ({before.get('reviews', 0)} rows)")
    print(f"  - ALL wishlists ({before.get('wishlists', 0)} rows)")
    print(f"  - Test user accounts matching test*@indiestack.dev ({test_user_count} users)")
    print(f"    + their sessions, notifications")
    print(f"  - Fake subscribers matching *@example.com ({fake_sub_count} rows)")
    print(f"  - ALL maker_updates ({before.get('maker_updates', 0)} rows)")
    print(f"  - ALL upvotes ({before.get('upvotes', 0)} rows) + reset upvote_count to 0")
    print(f"  - ALL tool_views ({before.get('tool_views', 0)} rows)")
    print(f"  - ALL page_views ({before.get('page_views', 0)} rows)")
    print(f"  - ALL search_logs ({before.get('search_logs', 0)} rows)")
    print(f"  - ALL milestones ({before.get('milestones', 0)} rows)")
    print()
    print("The following will be KEPT:")
    print("  - All tool listings (tools table)")
    print("  - All maker profiles (makers table)")
    print("  - Categories, collections, stacks, junction tables")
    print("  - is_verified and is_ejectable flags on tools")
    print("  - GovLink listing")
    print("  - Patrick's user account (if present)")
    print()

    if not skip_confirm:
        answer = input("Type YES to proceed: ").strip()
        if answer != "YES":
            print("Aborted.")
            conn.close()
            sys.exit(0)

    print("\nPurging...\n")

    # ── 1. Delete ALL reviews ────────────────────────────────────────────────
    if table_exists(conn, "reviews"):
        conn.execute("DELETE FROM reviews")
        print("  Deleted all reviews")

    # ── 2. Delete ALL wishlists ──────────────────────────────────────────────
    if table_exists(conn, "wishlists"):
        conn.execute("DELETE FROM wishlists")
        print("  Deleted all wishlists")

    # ── 3. Delete test user accounts and their FK references ─────────────────
    test_user_ids = [
        r[0] for r in conn.execute(
            "SELECT id FROM users WHERE email LIKE 'test%@indiestack.dev'"
        ).fetchall()
    ]

    if test_user_ids:
        placeholders = ",".join(["?"] * len(test_user_ids))

        # Delete FK references first
        for fk_table in ["sessions", "wishlists", "reviews", "notifications"]:
            if table_exists(conn, fk_table):
                conn.execute(
                    f"DELETE FROM {fk_table} WHERE user_id IN ({placeholders})",
                    test_user_ids,
                )

        # Delete the test users themselves
        conn.execute(
            f"DELETE FROM users WHERE id IN ({placeholders})",
            test_user_ids,
        )
        print(f"  Deleted {len(test_user_ids)} test user accounts + their sessions/notifications")
    else:
        print("  No test users found (already clean)")

    # ── 4. Delete fake subscribers ───────────────────────────────────────────
    if table_exists(conn, "subscribers"):
        cur = conn.execute("DELETE FROM subscribers WHERE email LIKE '%@example.com'")
        print(f"  Deleted {cur.rowcount} fake subscribers (@example.com)")

    # ── 5. Delete ALL maker_updates ──────────────────────────────────────────
    if table_exists(conn, "maker_updates"):
        conn.execute("DELETE FROM maker_updates")
        print("  Deleted all maker_updates")

    # ── 6. Reset upvote_count and delete upvotes ─────────────────────────────
    conn.execute("UPDATE tools SET upvote_count = 0")
    print("  Reset upvote_count to 0 on all tools")

    if table_exists(conn, "upvotes"):
        conn.execute("DELETE FROM upvotes")
        print("  Deleted all upvotes")

    # ── 7. Delete ALL tool_views ─────────────────────────────────────────────
    if table_exists(conn, "tool_views"):
        conn.execute("DELETE FROM tool_views")
        print("  Deleted all tool_views")

    # ── 8. Delete ALL page_views ─────────────────────────────────────────────
    if table_exists(conn, "page_views"):
        conn.execute("DELETE FROM page_views")
        print("  Deleted all page_views")

    # ── 9. Delete ALL search_logs ────────────────────────────────────────────
    if table_exists(conn, "search_logs"):
        conn.execute("DELETE FROM search_logs")
        print("  Deleted all search_logs")

    # ── 10. Delete ALL milestones ────────────────────────────────────────────
    if table_exists(conn, "milestones"):
        conn.execute("DELETE FROM milestones")
        print("  Deleted all milestones")

    # ── 11. Rebuild FTS ──────────────────────────────────────────────────────
    try:
        conn.execute("INSERT INTO tools_fts(tools_fts) VALUES('rebuild')")
        print("  Rebuilt FTS index")
    except Exception as e:
        print(f"  FTS rebuild skipped ({e})")

    conn.commit()

    # ── 12. Verify Patrick's account is intact ───────────────────────────────
    patrick = conn.execute(
        "SELECT id, email, name FROM users WHERE email LIKE '%patty%' OR email LIKE '%patrick%'"
    ).fetchone()
    if patrick:
        print(f"\n  Patrick's account intact: id={patrick[0]}, email={patrick[1]}, name={patrick[2]}")
    else:
        print("\n  (No Patrick account found in users table)")

    # ── Summary ──────────────────────────────────────────────────────────────
    after = get_counts(conn)
    print_counts("AFTER PURGE", after)

    # Delta summary
    print("DELTA (before -> after):")
    for table in TABLES_TO_COUNT:
        b = before.get(table, 0)
        a = after.get(table, 0)
        diff = a - b
        if diff != 0:
            print(f"  {table:20s} {b:>8,} -> {a:>8,}  ({diff:+,})")
    print()

    # Verify tools and makers untouched
    tools_ok = before.get("tools", 0) == after.get("tools", 0)
    makers_ok = before.get("makers", 0) == after.get("makers", 0)
    cats_ok = before.get("categories", 0) == after.get("categories", 0)
    print(f"  Tools intact:      {'YES' if tools_ok else 'NO — CHECK!'}")
    print(f"  Makers intact:     {'YES' if makers_ok else 'NO — CHECK!'}")
    print(f"  Categories intact: {'YES' if cats_ok else 'NO — CHECK!'}")

    conn.close()
    print("\nDone. Database purged of all seeded/fake data.")


if __name__ == "__main__":
    main()

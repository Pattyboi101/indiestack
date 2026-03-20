"""Add composite index on tool_pairs for OR-based lookups and success_count filtering.

The individual indexes on (tool_a_slug) and (tool_b_slug) already exist from init_db,
but queries like `WHERE (tool_a_slug = ? OR tool_b_slug = ?) AND success_count >= ?`
benefit from composite indexes that include success_count.

Also adds a composite index on tool_conflicts for the same pattern.

Safe to run multiple times (IF NOT EXISTS).

Usage:
    python3 scripts/add_pair_indexes.py              # local
    flyctl ssh console -C "python3 /app/scripts/add_pair_indexes.py"  # production
"""

import asyncio
import os
import aiosqlite

DB_PATH = os.environ.get("DB_PATH", "indiestack.db")


async def main():
    async with aiosqlite.connect(DB_PATH) as db:
        print(f"Connected to {DB_PATH}")

        # Composite indexes on tool_pairs for the common query pattern:
        #   WHERE (tool_a_slug = ? OR tool_b_slug = ?) AND success_count >= ?
        indexes = [
            ("idx_tool_pairs_a_success", "tool_pairs(tool_a_slug, success_count DESC)"),
            ("idx_tool_pairs_b_success", "tool_pairs(tool_b_slug, success_count DESC)"),
            ("idx_tool_conflicts_a", "tool_conflicts(tool_a_slug)"),
            ("idx_tool_conflicts_b", "tool_conflicts(tool_b_slug)"),
        ]

        for name, definition in indexes:
            sql = f"CREATE INDEX IF NOT EXISTS {name} ON {definition}"
            print(f"  {sql}")
            await db.execute(sql)

        await db.commit()
        print("Done. All indexes created.")


if __name__ == "__main__":
    asyncio.run(main())

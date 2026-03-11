"""Reset fake seeded upvote_count to match actual upvotes table rows."""
import sqlite3
import os

DB_PATH = os.environ.get("INDIESTACK_DB_PATH", "/data/indiestack.db")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Show before state
before = conn.execute(
    "SELECT COUNT(*) as total, SUM(upvote_count) as upvotes FROM tools WHERE upvote_count > 0"
).fetchone()
print(f"Before: {before['total']} tools with upvotes, {before['upvotes']} total fake+real upvotes")

# Count real upvotes in the upvotes table
real = conn.execute("SELECT COUNT(*) as c FROM upvotes").fetchone()['c']
print(f"Real upvote rows in upvotes table: {real}")

# Reset upvote_count to actual count from upvotes table
conn.execute("""
    UPDATE tools SET upvote_count = (
        SELECT COUNT(*) FROM upvotes WHERE upvotes.tool_id = tools.id
    )
""")
conn.commit()

# Show after state
after = conn.execute(
    "SELECT COUNT(*) as total, SUM(upvote_count) as upvotes FROM tools WHERE upvote_count > 0"
).fetchone()
print(f"After: {after['total']} tools with upvotes, {after['upvotes'] or 0} total real upvotes")

# Show any tools that still have upvotes (these are real)
real_upvoted = conn.execute(
    "SELECT name, upvote_count FROM tools WHERE upvote_count > 0 ORDER BY upvote_count DESC"
).fetchall()
if real_upvoted:
    print("\nTools with real upvotes:")
    for t in real_upvoted:
        print(f"  {t['name']}: {t['upvote_count']}")
else:
    print("\nNo tools have real upvotes yet — all counts were seeded.")

conn.close()

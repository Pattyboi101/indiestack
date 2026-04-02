"""Rotate Tool of the Week.

Picks the highest-engagement tool that:
  - status='approved'
  - has an install_command
  - has NOT won in the last 30 days (checked via tool_of_week_history)

Scoring = tool_views (last 7d) + outbound_clicks (last 7d) + mcp_view_count

Usage (production):
    fly ssh console -a indiestack -C "python3 /app/scripts/rotate_tool_of_week.py"
"""

import sqlite3
from datetime import datetime, timedelta

DB_PATH = "/data/indiestack.db"
COOLDOWN_DAYS = 30

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Ensure history table exists (in case migration hasn't run yet)
cur.execute("""
    CREATE TABLE IF NOT EXISTS tool_of_week_history (
        id INTEGER PRIMARY KEY,
        tool_id INTEGER NOT NULL REFERENCES tools(id),
        featured_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
""")
conn.commit()

cutoff_7d = (datetime.utcnow() - timedelta(days=7)).isoformat()
cutoff_cooldown = (datetime.utcnow() - timedelta(days=COOLDOWN_DAYS)).isoformat()

# Tools featured in the last 30 days — excluded
cur.execute(
    "SELECT tool_id FROM tool_of_week_history WHERE featured_at >= ?",
    (cutoff_cooldown,)
)
excluded_ids = {row["tool_id"] for row in cur.fetchall()}
print(f"Excluding {len(excluded_ids)} tools featured in the last {COOLDOWN_DAYS} days: {excluded_ids or 'none'}")

# Build candidate list with engagement scores
cur.execute("""
    SELECT
        t.id,
        t.name,
        t.slug,
        t.mcp_view_count,
        COALESCE(v.views_7d, 0) AS views_7d,
        COALESCE(c.clicks_7d, 0) AS clicks_7d,
        COALESCE(v.views_7d, 0) + COALESCE(c.clicks_7d, 0) + COALESCE(t.mcp_view_count, 0) AS score
    FROM tools t
    LEFT JOIN (
        SELECT tool_id, COUNT(*) AS views_7d
        FROM tool_views
        WHERE viewed_at >= ?
        GROUP BY tool_id
    ) v ON v.tool_id = t.id
    LEFT JOIN (
        SELECT tool_id, COUNT(*) AS clicks_7d
        FROM outbound_clicks
        WHERE created_at >= ?
        GROUP BY tool_id
    ) c ON c.tool_id = t.id
    WHERE t.status = 'approved'
      AND t.install_command IS NOT NULL
      AND t.install_command != ''
    ORDER BY score DESC
    LIMIT 100
""", (cutoff_7d, cutoff_7d))

candidates = cur.fetchall()
winner = None
for row in candidates:
    if row["id"] not in excluded_ids:
        winner = row
        break

if not winner:
    print("No eligible winner found — all top tools are in cooldown. Skipping rotation.")
    conn.close()
    exit(0)

print(f"\nWinner: {winner['name']} (slug={winner['slug']}, id={winner['id']})")
print(f"  Score: {winner['score']} = views_7d={winner['views_7d']} + clicks_7d={winner['clicks_7d']} + mcp_views={winner['mcp_view_count']}")

# Clear current TOTW
cur.execute("UPDATE tools SET tool_of_the_week = 0")
print(f"Cleared tool_of_the_week on all tools ({cur.rowcount} rows)")

# Set winner
cur.execute(
    "UPDATE tools SET tool_of_the_week = 1, totw_last_won = ? WHERE id = ?",
    (datetime.utcnow().isoformat(), winner["id"])
)

# Record in history
cur.execute(
    "INSERT INTO tool_of_week_history (tool_id, featured_at) VALUES (?, ?)",
    (winner["id"], datetime.utcnow().isoformat())
)

conn.commit()
print(f"\nDone. {winner['name']} is now Tool of the Week.")

# Show recent history
print("\n--- Recent TOTW History ---")
cur.execute("""
    SELECT t.name, t.slug, h.featured_at
    FROM tool_of_week_history h
    JOIN tools t ON t.id = h.tool_id
    ORDER BY h.featured_at DESC
    LIMIT 10
""")
for row in cur.fetchall():
    print(f"  {row['featured_at'][:10]}  {row['name']} ({row['slug']})")

conn.close()

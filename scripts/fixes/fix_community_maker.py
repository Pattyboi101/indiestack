"""Create a transparent 'Community Curated' maker for corporate tools."""
import sqlite3

conn = sqlite3.connect("/data/indiestack.db")

# Create the community maker
conn.execute("""
    INSERT OR IGNORE INTO makers (name, slug, bio, indie_status)
    VALUES (
        'Community Curated',
        'community',
        'Tools listed by the IndieStack community. Not affiliated with or endorsed by the tool creators. If you built one of these tools, claim your listing at indiestack.fly.dev.',
        'Community'
    )
""")
conn.commit()

# Get the maker ID
row = conn.execute("SELECT id FROM makers WHERE slug = 'community'").fetchone()
community_id = row[0]
print(f"Community maker ID: {community_id}")

# Assign all unclaimed AI Dev Tools to community maker
cat_row = conn.execute("SELECT id FROM categories WHERE slug = 'ai-dev-tools'").fetchone()
if cat_row:
    cur = conn.execute(
        "UPDATE tools SET maker_id = ? WHERE maker_id IS NULL AND category_id = ?",
        (community_id, cat_row[0])
    )
    print(f"Assigned {cur.rowcount} tools to Community Curated")

conn.commit()
conn.close()

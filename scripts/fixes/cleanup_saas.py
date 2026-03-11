"""One-off script to clean up paid SaaS tools with seeded upvotes."""
import sqlite3

db = sqlite3.connect('/data/indiestack.db')

# 4 named tools to delete
named_ids = [242, 176, 183, 136]  # SuperTokens, Logto, Umami, Chatwoot

# Open-source tools to KEEP and reclassify (not delete)
keep_as_code = [451, 453, 458, 464, 470, 482, 483, 501]
# Dokku, PocketBase, Twenty CRM, OpenStatus, SigNoz, TinaCMS, Authentik, Trigger.dev

# All SaaS with seeded upvotes > 5
seeded = db.execute(
    "SELECT id, name FROM tools WHERE upvote_count > 5 AND source_type = 'saas' ORDER BY id"
).fetchall()
seeded_ids = [r[0] for r in seeded]

# Delete IDs = named + seeded, minus the ones we're keeping
delete_ids = sorted(set(named_ids + seeded_ids) - set(keep_as_code))

print(f"Will DELETE {len(delete_ids)} tools:")
for tid in delete_ids:
    row = db.execute("SELECT name FROM tools WHERE id=?", (tid,)).fetchone()
    print(f"  {tid}: {row[0] if row else 'unknown'}")

print(f"\nWill RECLASSIFY {len(keep_as_code)} tools as code (reset votes to 0):")
for tid in keep_as_code:
    row = db.execute("SELECT name FROM tools WHERE id=?", (tid,)).fetchone()
    print(f"  {tid}: {row[0] if row else 'unknown'}")

# === EXECUTE ===

# 1. Clean up references for tools being deleted
ref_tables = [
    'upvotes', 'wishlists', 'reviews', 'agent_citations', 'collection_tools',
    'stack_tools', 'tool_views', 'outbound_clicks', 'tool_reactions',
    'milestones', 'sponsored_placements',
]
placeholders = ','.join('?' * len(delete_ids))
for table in ref_tables:
    try:
        cur = db.execute(f"DELETE FROM {table} WHERE tool_id IN ({placeholders})", delete_ids)
        if cur.rowcount > 0:
            print(f"  Cleaned {cur.rowcount} rows from {table}")
    except Exception:
        pass  # table might not have tool_id column

# 2. Delete the tools
cur = db.execute(f"DELETE FROM tools WHERE id IN ({placeholders})", delete_ids)
print(f"\nDeleted {cur.rowcount} tools")

# 3. Reclassify open-source tools
for tid in keep_as_code:
    db.execute("UPDATE tools SET source_type = 'code', upvote_count = 0 WHERE id = ?", (tid,))
print(f"Reclassified {len(keep_as_code)} tools as code with 0 votes")

# 4. Clean upvotes on reclassified tools too
placeholders2 = ','.join('?' * len(keep_as_code))
db.execute(f"DELETE FROM upvotes WHERE tool_id IN ({placeholders2})", keep_as_code)

db.commit()
print("\nCommitted.")

# Verify
remaining = db.execute("SELECT COUNT(*) FROM tools").fetchone()[0]
saas_count = db.execute("SELECT COUNT(*) FROM tools WHERE source_type='saas'").fetchone()[0]
code_count = db.execute("SELECT COUNT(*) FROM tools WHERE source_type='code'").fetchone()[0]
print(f"\nRemaining: {remaining} tools ({code_count} code, {saas_count} saas)")

"""Remove fake corporate maker profiles from seeded AI Dev Tools.
Tools stay listed but show as unclaimed community submissions."""
import sqlite3

conn = sqlite3.connect("/data/indiestack.db")

# Corporate makers that look fake/impersonated
fake_corporate_ids = [152, 153, 154, 155, 158, 159, 161, 162]
# 152=Stripe, 153=Fly.io, 154=Anthropic, 155=Sentry,
# 158=Cursor Inc, 159=Continue, 161=Sourcegraph, 162=Composio

# Dissociate tools from fake makers
for mid in fake_corporate_ids:
    cur = conn.execute("SELECT name FROM makers WHERE id = ?", (mid,))
    row = cur.fetchone()
    name = row[0] if row else "?"

    updated = conn.execute(
        "UPDATE tools SET maker_id = NULL, maker_name = maker_name WHERE maker_id = ?",
        (mid,)
    ).rowcount
    print(f"  Dissociated {updated} tools from {name} (maker {mid})")

# Delete the fake maker profiles
conn.execute(f"DELETE FROM makers WHERE id IN ({','.join(str(i) for i in fake_corporate_ids)})")
print(f"\nDeleted {len(fake_corporate_ids)} fake corporate maker profiles")

# Keep real individual makers: 148 (Zachary), 149 (fetchlyhub), 150 (Tanq16),
# 151 (Darren), 156 (Nicholas Griffin), 157 (Xeol), 160 (Paul Gauthier)

conn.commit()

# Verify
remaining = conn.execute("SELECT COUNT(*) FROM makers WHERE id >= 148").fetchone()[0]
unclaimed = conn.execute(
    "SELECT name FROM tools WHERE maker_id IS NULL AND category_id = (SELECT id FROM categories WHERE slug = 'ai-dev-tools')"
).fetchall()
print(f"\nRemaining AI Dev Tools makers: {remaining}")
print(f"Now unclaimed tools: {len(unclaimed)}")
for t in unclaimed:
    print(f"  - {t[0]}")

conn.close()

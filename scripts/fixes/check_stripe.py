import sqlite3
conn = sqlite3.connect('/data/indiestack.db')
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT id, name, maker_id, price_pence FROM tools WHERE slug = 'govlink'").fetchone()
print(f"GovLink: id={row['id']}, maker_id={row['maker_id']}, price={row['price_pence']}p")
# Check what maker_id 1 owns
tools = conn.execute("SELECT id, name, slug FROM tools WHERE maker_id = 1").fetchall()
print(f"\nMaker 1 (Oat) owns {len(tools)} tools:")
for t in tools:
    print(f"  Tool {t['id']}: {t['name']} (/{t['slug']})")
conn.close()

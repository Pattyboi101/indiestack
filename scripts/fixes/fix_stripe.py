import sqlite3
conn = sqlite3.connect('/data/indiestack.db')
conn.execute("UPDATE makers SET stripe_account_id = NULL WHERE id = 1")
conn.execute("UPDATE tools SET stripe_account_id = '' WHERE maker_id = 1")
conn.commit()
# Verify
row = conn.execute("SELECT stripe_account_id FROM makers WHERE id = 1").fetchone()
print(f"Maker 1 stripe_account_id: {row[0]}")
conn.close()

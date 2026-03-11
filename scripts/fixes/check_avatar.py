import sqlite3
db = sqlite3.connect('indiestack.db')
db.row_factory = sqlite3.Row

# Check for any pixel avatars
rows = db.execute("SELECT id, name, pixel_avatar, pixel_avatar_approved FROM users WHERE pixel_avatar IS NOT NULL AND pixel_avatar != ''").fetchall()
if rows:
    for r in rows:
        print(f"id={r['id']} name={r['name']} len={len(r['pixel_avatar'])} approved={r['pixel_avatar_approved']} data={r['pixel_avatar'][:20]}...")
else:
    print("No users with pixel_avatar set")

# Check columns exist
cols = db.execute("PRAGMA table_info(users)").fetchall()
col_names = [c['name'] for c in cols]
print(f"\nUser columns: {col_names}")
print(f"pixel_avatar exists: {'pixel_avatar' in col_names}")
print(f"pixel_avatar_approved exists: {'pixel_avatar_approved' in col_names}")

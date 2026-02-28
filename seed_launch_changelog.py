"""Seed a marketplace launch changelog entry for March 2nd."""
import sqlite3

conn = sqlite3.connect("/data/indiestack.db")

# Use maker_id 1 (Oat / platform account) for the platform-level announcement
conn.execute(
    """INSERT OR IGNORE INTO maker_updates (maker_id, tool_id, update_type, title, content, created_at)
    VALUES (1, NULL, 'launch',
        'IndieStack Marketplace is Live',
        'Indie developers can now sell their tools directly on IndieStack. 5% platform fee, direct Stripe payouts, and a curated audience of developers. Connect Stripe on your dashboard to start selling.',
        '2026-03-02 09:00:00')""",
)
conn.commit()
print(f"Changelog entry seeded. Rows affected: {conn.total_changes}")
conn.close()

#!/usr/bin/env python3
"""Reject library-like tools that slipped through auto-review."""

import os
import sqlite3

db_path = "/data/indiestack.db" if os.path.exists("/data/indiestack.db") else "data/indiestack.db"
conn = sqlite3.connect(db_path)

# Reject approved/pending tools that are clearly libraries
patterns = [
    "slug LIKE '%-sdk-%'", "slug LIKE '%-sdk'", "slug LIKE 'sdk-%'",
    "slug LIKE '%-lib'", "slug LIKE '%-lib-%'", "slug LIKE 'lib-%'",
    "slug LIKE '%-binding%'", "slug LIKE '%-wrapper%'",
    "slug LIKE '%-client-%'",
    "name LIKE '% SDK%'", "name LIKE '% Sdk %'",
    "name LIKE '% Binding%'", "name LIKE '% Wrapper%'",
    "name LIKE '% Client For%'",
    "tagline LIKE 'Go library%'", "tagline LIKE 'A Go library%'",
    "tagline LIKE 'Rust library%'", "tagline LIKE 'A Rust library%'",
    "tagline LIKE 'Python library%'", "tagline LIKE 'A Python library%'",
    "tagline LIKE 'Node library%'",
    "tagline LIKE 'Simple wrapper%'", "tagline LIKE 'Thin wrapper%'",
    "tagline LIKE 'Go implementation of%'",
    "tagline LIKE 'Rust implementation of%'",
    "tagline LIKE 'Go bindings%'", "tagline LIKE 'Python bindings%'",
]

where = " OR ".join(patterns)
sql = f"UPDATE tools SET status='rejected' WHERE status IN ('approved','pending') AND ({where})"

before_approved = conn.execute("SELECT COUNT(*) FROM tools WHERE status='approved'").fetchone()[0]
before_pending = conn.execute("SELECT COUNT(*) FROM tools WHERE status='pending'").fetchone()[0]

cur = conn.execute(sql)
rejected = cur.rowcount
conn.commit()

after_approved = conn.execute("SELECT COUNT(*) FROM tools WHERE status='approved'").fetchone()[0]
after_pending = conn.execute("SELECT COUNT(*) FROM tools WHERE status='pending'").fetchone()[0]
total_rejected = conn.execute("SELECT COUNT(*) FROM tools WHERE status='rejected'").fetchone()[0]

print(f"Rejected {rejected} library-like tools")
print(f"Approved: {before_approved} -> {after_approved}")
print(f"Pending: {before_pending} -> {after_pending}")
print(f"Total rejected: {total_rejected}")
conn.close()

#!/usr/bin/env python3
"""Bulk-approve pending tools from curated awesome lists."""

import os
import re
import sqlite3
import urllib.request

CURATED_SOURCES = {
    "developer-first": "https://raw.githubusercontent.com/agamm/awesome-developer-first/main/README.md",
    "seo-tools": "https://raw.githubusercontent.com/serpapi/awesome-seo-tools/master/README.md",
    "analytics": "https://raw.githubusercontent.com/newTendermint/awesome-analytics/master/README.md",
}

# Sitemap-based sources (match by slug from sitemap URLs)
SITEMAP_SOURCES = {
    "openalternative": "https://openalternative.co/sitemap/tools.xml",
}

db_path = "/data/indiestack.db" if os.path.exists("/data/indiestack.db") else "data/indiestack.db"
conn = sqlite3.connect(db_path)

pending_before = conn.execute("SELECT COUNT(*) FROM tools WHERE status='pending'").fetchone()[0]
print(f"Pending tools before: {pending_before}")

total_approved = 0
for name, url in CURATED_SOURCES.items():
    print(f"\nProcessing {name}...")
    body = urllib.request.urlopen(url).read().decode()

    # Extract all URLs from markdown link entries
    urls = set()
    for m in re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', body):
        tool_url = m.group(2).strip().lower().rstrip("/")
        tool_url = re.sub(r'^https?://', '', tool_url)
        urls.add(tool_url)

    # Approve matching pending tools
    approved = 0
    pending = conn.execute("SELECT id, url FROM tools WHERE status='pending'").fetchall()
    for row in pending:
        norm = re.sub(r'^https?://', '', row[1].lower().rstrip("/"))
        if norm in urls:
            conn.execute("UPDATE tools SET status='approved' WHERE id=?", (row[0],))
            approved += 1
    conn.commit()
    total_approved += approved
    print(f"  {name}: approved {approved} tools")

# Sitemap-based approval (match by slug)
for name, sitemap_url in SITEMAP_SOURCES.items():
    print(f"\nProcessing {name} (sitemap)...")
    body = urllib.request.urlopen(sitemap_url).read().decode()
    # Extract slugs from sitemap URLs like <loc>https://openalternative.co/toolname</loc>
    sitemap_slugs = set()
    for m in re.finditer(r'<loc>https?://[^/]+/([^/<]+)</loc>', body):
        sitemap_slugs.add(m.group(1).lower())

    approved = 0
    pending = conn.execute("SELECT id, slug FROM tools WHERE status='pending'").fetchall()
    for row in pending:
        if row[1].lower() in sitemap_slugs:
            conn.execute("UPDATE tools SET status='approved' WHERE id=?", (row[0],))
            approved += 1
    conn.commit()
    total_approved += approved
    print(f"  {name}: approved {approved} tools")

pending_after = conn.execute("SELECT COUNT(*) FROM tools WHERE status='pending'").fetchone()[0]
approved_total = conn.execute("SELECT COUNT(*) FROM tools WHERE status='approved'").fetchone()[0]
print(f"\nTotal approved this run: {total_approved}")
print(f"Total approved tools in DB: {approved_total}")
print(f"Pending remaining: {pending_after}")
conn.close()

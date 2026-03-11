"""Insert GitHub-sourced tools + makers into IndieStack DB."""
import json
import sqlite3
import re
from datetime import datetime


def slugify(name):
    s = name.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return s.strip('-')


def main():
    db = sqlite3.connect("/data/indiestack.db")
    db.row_factory = sqlite3.Row

    with open("/tmp/github_tools_found2.json") as f:
        tools = json.load(f)

    # Build lookups
    cats = {r['slug']: r['id'] for r in db.execute("SELECT id, slug FROM categories").fetchall()}
    existing_slugs = {r[0] for r in db.execute("SELECT slug FROM tools").fetchall()}
    existing_urls = {r[0].lower() for r in db.execute("SELECT url FROM tools WHERE url IS NOT NULL").fetchall()}
    existing_maker_slugs = {r[0] for r in db.execute("SELECT slug FROM makers").fetchall()}

    now = datetime.utcnow().isoformat()
    tools_added = 0
    makers_added = 0
    skipped = 0

    for t in tools:
        tool_slug = slugify(t['name'])
        cat_id = cats.get(t['category_slug'], cats.get('developer-tools'))

        # Skip if tool already exists
        if tool_slug in existing_slugs or t['url'].lower() in existing_urls:
            skipped += 1
            continue

        # Skip junk repos (hacking tools, configs, etc)
        desc_lower = (t.get('description') or '').lower()
        name_lower = t['name'].lower()
        skip_words = ['hack', 'crack', 'exploit', 'phish', '.config', 'hacked', 'malware']
        if any(w in name_lower or w in desc_lower for w in skip_words):
            print(f"  SKIP {t['name']}: suspicious content")
            skipped += 1
            continue

        # Create or find maker
        maker = t.get('maker', {})
        maker_slug = slugify(maker.get('login', ''))
        maker_id = None

        if maker_slug and maker_slug not in existing_maker_slugs:
            db.execute(
                """INSERT INTO makers (name, slug, bio, url, email, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (maker.get('name', maker.get('login', '')),
                 maker_slug,
                 maker.get('bio', ''),
                 maker.get('url', ''),
                 maker.get('email', ''),
                 now)
            )
            db.commit()
            row = db.execute("SELECT id FROM makers WHERE slug = ?", (maker_slug,)).fetchone()
            maker_id = row['id'] if row else None
            existing_maker_slugs.add(maker_slug)
            makers_added += 1
            print(f"  MAKER {maker.get('name', maker_slug)} ({maker.get('email', 'no email')})")
        elif maker_slug:
            row = db.execute("SELECT id FROM makers WHERE slug = ?", (maker_slug,)).fetchone()
            maker_id = row['id'] if row else None

        # Create tagline from description
        desc = t.get('description', '') or t['name']
        tagline = desc[:100]

        # Insert tool
        db.execute(
            """INSERT INTO tools (name, slug, tagline, description, url, category_id, tags, status, created_at, maker_id, claimed_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'approved', ?, ?, ?)""",
            (t['name'], tool_slug, tagline, desc, t['url'], cat_id,
             t.get('tags', ''), now, maker_id,
             None)
        )
        existing_slugs.add(tool_slug)
        existing_urls.add(t['url'].lower())
        tools_added += 1
        stars = t.get('stars', 0)
        print(f"  TOOL {t['name']} ({stars}*) -> {tool_slug} [maker_id={maker_id}]")

    db.commit()

    total = db.execute("SELECT COUNT(*) FROM tools WHERE status='approved'").fetchone()[0]
    total_makers = db.execute("SELECT COUNT(*) FROM makers").fetchone()[0]

    # Collect emails for outreach
    maker_emails = db.execute(
        "SELECT DISTINCT m.name, m.email FROM makers m WHERE m.email IS NOT NULL AND m.email != '' AND m.created_at >= ?",
        (now[:10],)
    ).fetchall()

    print(f"\nDone!")
    print(f"Tools added: {tools_added}, Skipped: {skipped}")
    print(f"Makers added: {makers_added}")
    print(f"Total approved tools: {total}")
    print(f"Total makers: {total_makers}")
    print(f"\nNew makers with emails ({len(maker_emails)}):")
    for m in maker_emails:
        print(f"  {m[0]} <{m[1]}>")


if __name__ == "__main__":
    main()

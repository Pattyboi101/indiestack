"""Database schema, migrations, seed data, and all query functions."""

import aiosqlite
import os
import hashlib
import secrets
import re
from typing import Optional

DB_PATH = os.environ.get("INDIESTACK_DB_PATH", "/data/indiestack.db")
_UPVOTE_SALT = os.environ.get("INDIESTACK_UPVOTE_SALT", "indiestack-default-salt-change-me")

# ── Schema ────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    slug TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL DEFAULT '',
    icon TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    tagline TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL,
    maker_name TEXT NOT NULL DEFAULT '',
    maker_url TEXT NOT NULL DEFAULT '',
    category_id INTEGER NOT NULL REFERENCES categories(id),
    tags TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')),
    is_verified INTEGER NOT NULL DEFAULT 0,
    upvote_count INTEGER NOT NULL DEFAULT 0,
    price_pence INTEGER,
    delivery_type TEXT NOT NULL DEFAULT 'link' CHECK(delivery_type IN ('link','download','license_key')),
    delivery_url TEXT NOT NULL DEFAULT '',
    stripe_account_id TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS upvotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    ip_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool_id, ip_hash)
);

CREATE INDEX IF NOT EXISTS idx_tools_status ON tools(status);
CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category_id);
CREATE INDEX IF NOT EXISTS idx_tools_upvotes ON tools(upvote_count DESC);
"""

FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS tools_fts USING fts5(
    name, tagline, description, tags,
    content='tools',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS tools_ai AFTER INSERT ON tools BEGIN
    INSERT INTO tools_fts(rowid, name, tagline, description, tags)
    VALUES (new.id, new.name, new.tagline, new.description, new.tags);
END;

CREATE TRIGGER IF NOT EXISTS tools_ad AFTER DELETE ON tools BEGIN
    INSERT INTO tools_fts(tools_fts, rowid, name, tagline, description, tags)
    VALUES ('delete', old.id, old.name, old.tagline, old.description, old.tags);
END;

CREATE TRIGGER IF NOT EXISTS tools_au AFTER UPDATE ON tools BEGIN
    INSERT INTO tools_fts(tools_fts, rowid, name, tagline, description, tags)
    VALUES ('delete', old.id, old.name, old.tagline, old.description, old.tags);
    INSERT INTO tools_fts(rowid, name, tagline, description, tags)
    VALUES (new.id, new.name, new.tagline, new.description, new.tags);
END;
"""

# ── Seed categories ───────────────────────────────────────────────────────

SEED_CATEGORIES = [
    ("Invoicing & Billing", "invoicing-billing", "Send invoices and get paid", "💰"),
    ("Email Marketing", "email-marketing", "Newsletters and email campaigns", "📧"),
    ("Analytics & Metrics", "analytics-metrics", "Track what matters", "📊"),
    ("Project Management", "project-management", "Organize tasks and projects", "📋"),
    ("Customer Support", "customer-support", "Help desks and live chat", "🎧"),
    ("Scheduling & Booking", "scheduling-booking", "Appointments and calendars", "📅"),
    ("Social Media", "social-media", "Scheduling and management", "📱"),
    ("Landing Pages", "landing-pages", "Build and ship pages fast", "🚀"),
    ("Forms & Surveys", "forms-surveys", "Collect data and feedback", "📝"),
    ("CRM & Sales", "crm-sales", "Manage leads and deals", "🤝"),
    ("File Management", "file-management", "Storage and sharing", "📁"),
    ("Authentication", "authentication", "Login, SSO, and user management", "🔐"),
    ("Payments", "payments", "Accept and process payments", "💳"),
    ("SEO Tools", "seo-tools", "Rank higher and get found", "🔍"),
    ("Monitoring & Uptime", "monitoring-uptime", "Stay online and get alerted", "🟢"),
    ("API Tools", "api-tools", "Build and manage APIs", "⚡"),
    ("Design & Creative", "design-creative", "Graphics, video, and branding", "🎨"),
    ("Developer Tools", "developer-tools", "Ship code faster", "🛠️"),
    ("AI & Automation", "ai-automation", "Smart workflows and bots", "🤖"),
    ("Feedback & Reviews", "feedback-reviews", "Collect and display testimonials", "⭐"),
]

# ── Database init ─────────────────────────────────────────────────────────

def _dict_factory(cursor, row):
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


async def get_db() -> aiosqlite.Connection:
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = _dict_factory
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def init_db():
    db = await get_db()
    try:
        await db.executescript(SCHEMA)
        await db.executescript(FTS_SCHEMA)
        # Migration: add is_verified column if missing (for existing DBs)
        try:
            await db.execute("SELECT is_verified FROM tools LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE tools ADD COLUMN is_verified INTEGER NOT NULL DEFAULT 0")
        # Seed categories if empty
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM categories")
        count = (await cursor.fetchone())['cnt']
        if count == 0:
            await db.executemany(
                "INSERT INTO categories (name, slug, description, icon) VALUES (?, ?, ?, ?)",
                SEED_CATEGORIES,
            )
        await db.commit()
    finally:
        await db.close()


# ── Slug helper ───────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


# ── Category queries ──────────────────────────────────────────────────────

async def get_all_categories(db: aiosqlite.Connection):
    cursor = await db.execute(
        """SELECT c.*, COUNT(t.id) as tool_count
           FROM categories c
           LEFT JOIN tools t ON t.category_id = c.id AND t.status = 'approved'
           GROUP BY c.id ORDER BY c.name"""
    )
    return await cursor.fetchall()


async def get_category_by_slug(db: aiosqlite.Connection, slug: str):
    cursor = await db.execute("SELECT * FROM categories WHERE slug = ?", (slug,))
    return await cursor.fetchone()


# ── Tool queries ──────────────────────────────────────────────────────────

async def get_trending_tools(db: aiosqlite.Connection, limit: int = 6):
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug,
                  (t.is_verified * 100 + t.upvote_count) as rank_score
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved'
           ORDER BY rank_score DESC, t.created_at DESC LIMIT ?""",
        (limit,),
    )
    return await cursor.fetchall()


async def get_tools_by_category(db: aiosqlite.Connection, category_id: int, page: int = 1, per_page: int = 12):
    offset = (page - 1) * per_page
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.category_id = ? AND t.status = 'approved'
           ORDER BY (t.is_verified * 100 + t.upvote_count) DESC, t.created_at DESC
           LIMIT ? OFFSET ?""",
        (category_id, per_page, offset),
    )
    rows = await cursor.fetchall()
    count_cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM tools WHERE category_id = ? AND status = 'approved'", (category_id,)
    )
    total = (await count_cursor.fetchone())['cnt']
    return rows, total


async def get_tool_by_slug(db: aiosqlite.Connection, slug: str):
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.slug = ?""",
        (slug,),
    )
    return await cursor.fetchone()


async def get_related_tools(db: aiosqlite.Connection, tool_id: int, category_id: int, limit: int = 3):
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.category_id = ? AND t.id != ? AND t.status = 'approved'
           ORDER BY (t.is_verified * 100 + t.upvote_count) DESC LIMIT ?""",
        (category_id, tool_id, limit),
    )
    return await cursor.fetchall()


# ── Search ────────────────────────────────────────────────────────────────

def sanitize_fts(query: str) -> str:
    """Sanitize input for FTS5 — strip special chars, add prefix matching."""
    query = re.sub(r'[^\w\s]', '', query).strip()
    if not query:
        return ''
    terms = query.split()
    return ' '.join(f'"{t}"*' for t in terms[:10])


async def search_tools(db: aiosqlite.Connection, query: str, limit: int = 20):
    safe_q = sanitize_fts(query)
    if not safe_q:
        return []
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug,
                  bm25(tools_fts) as rank
           FROM tools_fts fts
           JOIN tools t ON t.id = fts.rowid
           JOIN categories c ON t.category_id = c.id
           WHERE tools_fts MATCH ? AND t.status = 'approved'
           ORDER BY (t.is_verified * 5.0 + rank) LIMIT ?""",
        (safe_q, limit),
    )
    return await cursor.fetchall()


# ── Submissions ───────────────────────────────────────────────────────────

async def create_tool(db: aiosqlite.Connection, *, name: str, tagline: str, description: str,
                      url: str, maker_name: str, maker_url: str, category_id: int, tags: str) -> int:
    slug = slugify(name)
    # Ensure unique slug
    base_slug = slug
    counter = 1
    while True:
        existing = await db.execute("SELECT id FROM tools WHERE slug = ?", (slug,))
        if await existing.fetchone() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    cursor = await db.execute(
        """INSERT INTO tools (name, slug, tagline, description, url, maker_name, maker_url, category_id, tags)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, slug, tagline, description, url, maker_name, maker_url, category_id, tags),
    )
    await db.commit()
    return cursor.lastrowid


async def get_category_by_name(db: aiosqlite.Connection, name: str):
    """Fuzzy category lookup: tries exact name, then slug, then case-insensitive."""
    cursor = await db.execute("SELECT * FROM categories WHERE name = ?", (name,))
    row = await cursor.fetchone()
    if row:
        return row
    cursor = await db.execute("SELECT * FROM categories WHERE slug = ?", (slugify(name),))
    row = await cursor.fetchone()
    if row:
        return row
    cursor = await db.execute("SELECT * FROM categories WHERE LOWER(name) = LOWER(?)", (name,))
    return await cursor.fetchone()


async def bulk_create_tools(db: aiosqlite.Connection, tools_data: list[dict]) -> tuple[int, list[str]]:
    """Import multiple tools at once. Returns (created_count, errors)."""
    created = 0
    errors = []
    for i, t in enumerate(tools_data):
        try:
            name = str(t.get('name', '')).strip()
            if not name:
                errors.append(f"Tool #{i+1}: missing name")
                continue

            # Resolve category
            cat_name = str(t.get('category', '')).strip()
            cat = await get_category_by_name(db, cat_name) if cat_name else None
            if not cat:
                errors.append(f"Tool #{i+1} ({name}): unknown category '{cat_name}'")
                continue

            slug = slugify(name)
            base_slug = slug
            counter = 1
            while True:
                existing = await db.execute("SELECT id FROM tools WHERE slug = ?", (slug,))
                if await existing.fetchone() is None:
                    break
                slug = f"{base_slug}-{counter}"
                counter += 1

            await db.execute(
                """INSERT INTO tools (name, slug, tagline, description, url, maker_name, maker_url,
                   category_id, tags, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved')""",
                (name, slug,
                 str(t.get('tagline', '')).strip(),
                 str(t.get('description', '')).strip(),
                 str(t.get('url', '')).strip(),
                 str(t.get('maker_name', '')).strip(),
                 str(t.get('maker_url', '')).strip(),
                 cat['id'],
                 str(t.get('tags', '')).strip()),
            )
            created += 1
        except Exception as e:
            errors.append(f"Tool #{i+1} ({t.get('name', '?')}): {e}")
    await db.commit()
    return created, errors


# ── Admin ─────────────────────────────────────────────────────────────────

async def get_pending_tools(db: aiosqlite.Connection):
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'pending' ORDER BY t.created_at DESC"""
    )
    return await cursor.fetchall()


async def get_all_tools_admin(db: aiosqlite.Connection):
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name
           FROM tools t JOIN categories c ON t.category_id = c.id
           ORDER BY t.created_at DESC"""
    )
    return await cursor.fetchall()


async def update_tool_status(db: aiosqlite.Connection, tool_id: int, status: str):
    await db.execute("UPDATE tools SET status = ? WHERE id = ?", (status, tool_id))
    await db.commit()


async def toggle_verified(db: aiosqlite.Connection, tool_id: int) -> bool:
    """Toggle verified status. Returns new is_verified state."""
    cursor = await db.execute("SELECT is_verified FROM tools WHERE id = ?", (tool_id,))
    row = await cursor.fetchone()
    if not row:
        return False
    new_val = 0 if row['is_verified'] else 1
    await db.execute("UPDATE tools SET is_verified = ? WHERE id = ?", (new_val, tool_id))
    await db.commit()
    return bool(new_val)


# ── Upvotes ───────────────────────────────────────────────────────────────

def hash_ip(ip: str) -> str:
    return hashlib.sha256(f"{_UPVOTE_SALT}{ip}".encode()).hexdigest()


async def toggle_upvote(db: aiosqlite.Connection, tool_id: int, ip: str) -> tuple[int, bool]:
    """Toggle upvote. Returns (new_count, is_upvoted)."""
    ip_h = hash_ip(ip)
    cursor = await db.execute(
        "SELECT id FROM upvotes WHERE tool_id = ? AND ip_hash = ?", (tool_id, ip_h)
    )
    existing = await cursor.fetchone()
    if existing:
        await db.execute("DELETE FROM upvotes WHERE id = ?", (existing['id'],))
        await db.execute("UPDATE tools SET upvote_count = MAX(0, upvote_count - 1) WHERE id = ?", (tool_id,))
        upvoted = False
    else:
        await db.execute("INSERT INTO upvotes (tool_id, ip_hash) VALUES (?, ?)", (tool_id, ip_h))
        await db.execute("UPDATE tools SET upvote_count = upvote_count + 1 WHERE id = ?", (tool_id,))
        upvoted = True
    await db.commit()
    count_cursor = await db.execute("SELECT upvote_count FROM tools WHERE id = ?", (tool_id,))
    row = await count_cursor.fetchone()
    return (row['upvote_count'] if row else 0), upvoted


async def has_upvoted(db: aiosqlite.Connection, tool_id: int, ip: str) -> bool:
    ip_h = hash_ip(ip)
    cursor = await db.execute(
        "SELECT id FROM upvotes WHERE tool_id = ? AND ip_hash = ?", (tool_id, ip_h)
    )
    return await cursor.fetchone() is not None

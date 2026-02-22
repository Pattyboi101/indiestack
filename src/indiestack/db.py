"""Database schema, migrations, seed data, and all query functions."""

import aiosqlite
import os
import hashlib
import secrets
import re
from typing import Optional
from datetime import datetime, timedelta

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

CREATE TABLE IF NOT EXISTS makers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    bio TEXT NOT NULL DEFAULT '',
    avatar_url TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    verified_at TIMESTAMP,
    verified_until TIMESTAMP,
    maker_id INTEGER REFERENCES makers(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS upvotes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    ip_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool_id, ip_hash)
);

CREATE TABLE IF NOT EXISTS purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    buyer_email TEXT NOT NULL,
    stripe_session_id TEXT NOT NULL DEFAULT '',
    amount_pence INTEGER NOT NULL,
    commission_pence INTEGER NOT NULL,
    purchase_token TEXT NOT NULL UNIQUE,
    delivered INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS featured_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    featured_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    headline TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS collections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    cover_emoji TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collection_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_id INTEGER NOT NULL REFERENCES collections(id),
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    position INTEGER NOT NULL DEFAULT 0,
    UNIQUE(collection_id, tool_id)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'buyer' CHECK(role IN ('buyer','maker','admin')),
    maker_id INTEGER REFERENCES makers(id),
    email_verified INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL DEFAULT '',
    is_verified_purchase INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tool_id, user_id)
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    stripe_subscription_id TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'pro',
    status TEXT NOT NULL DEFAULT 'active',
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS tool_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    ip_hash TEXT NOT NULL,
    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS wishlists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, tool_id)
);

CREATE TABLE IF NOT EXISTS maker_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    maker_id INTEGER NOT NULL REFERENCES makers(id),
    title TEXT NOT NULL DEFAULT '',
    body TEXT NOT NULL,
    update_type TEXT NOT NULL DEFAULT 'update'
        CHECK(update_type IN ('update','launch','milestone','changelog')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    type TEXT NOT NULL,
    message TEXT NOT NULL,
    link TEXT NOT NULL DEFAULT '',
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tools_status ON tools(status);
CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category_id);
CREATE INDEX IF NOT EXISTS idx_tools_upvotes ON tools(upvote_count DESC);
CREATE INDEX IF NOT EXISTS idx_purchases_token ON purchases(purchase_token);
CREATE INDEX IF NOT EXISTS idx_purchases_tool ON purchases(tool_id);
CREATE INDEX IF NOT EXISTS idx_collection_tools_coll ON collection_tools(collection_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_reviews_tool ON reviews(tool_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_tool_views_tool ON tool_views(tool_id);
CREATE INDEX IF NOT EXISTS idx_wishlists_user ON wishlists(user_id);
CREATE INDEX IF NOT EXISTS idx_wishlists_tool ON wishlists(tool_id);
CREATE INDEX IF NOT EXISTS idx_maker_updates_maker ON maker_updates(maker_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_tools_maker_id ON tools(maker_id);
CREATE INDEX IF NOT EXISTS idx_makers_slug ON makers(slug);
CREATE INDEX IF NOT EXISTS idx_collections_slug ON collections(slug);
CREATE INDEX IF NOT EXISTS idx_stacks_slug ON stacks(slug);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

CREATE TABLE IF NOT EXISTS page_views (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    page TEXT NOT NULL,
    visitor_id TEXT,
    referrer TEXT
);
CREATE INDEX IF NOT EXISTS idx_page_views_timestamp ON page_views(timestamp);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscribers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    cover_emoji TEXT NOT NULL DEFAULT '',
    discount_percent INTEGER NOT NULL DEFAULT 15,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS stack_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stack_id INTEGER NOT NULL REFERENCES stacks(id),
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    position INTEGER NOT NULL DEFAULT 0,
    UNIQUE(stack_id, tool_id)
);

CREATE TABLE IF NOT EXISTS stack_purchases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stack_id INTEGER NOT NULL REFERENCES stacks(id),
    buyer_email TEXT NOT NULL,
    stripe_session_id TEXT NOT NULL DEFAULT '',
    total_amount_pence INTEGER NOT NULL,
    discount_pence INTEGER NOT NULL DEFAULT 0,
    purchase_token TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stack_tools_stack ON stack_tools(stack_id);
CREATE INDEX IF NOT EXISTS idx_stack_purchases_token ON stack_purchases(purchase_token);
CREATE INDEX IF NOT EXISTS idx_tools_tags ON tools(tags);
CREATE INDEX IF NOT EXISTS idx_tools_verified ON tools(is_verified);
CREATE INDEX IF NOT EXISTS idx_tools_ejectable ON tools(is_ejectable);

CREATE TABLE IF NOT EXISTS claim_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_claim_tokens_token ON claim_tokens(token);

CREATE TABLE IF NOT EXISTS user_stacks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    title TEXT NOT NULL DEFAULT 'My Stack',
    description TEXT NOT NULL DEFAULT '',
    is_public INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE TABLE IF NOT EXISTS user_stack_tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stack_id INTEGER NOT NULL REFERENCES user_stacks(id),
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    position INTEGER NOT NULL DEFAULT 0,
    note TEXT NOT NULL DEFAULT '',
    UNIQUE(stack_id, tool_id)
);
CREATE INDEX IF NOT EXISTS idx_user_stack_tools_stack ON user_stack_tools(stack_id);

CREATE TABLE IF NOT EXISTS search_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'web',
    result_count INTEGER NOT NULL DEFAULT 0,
    top_result_slug TEXT,
    top_result_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_search_logs_created ON search_logs(created_at);

CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    tool_id INTEGER REFERENCES tools(id),
    milestone_type TEXT NOT NULL,
    achieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    shared INTEGER NOT NULL DEFAULT 0,
    UNIQUE(user_id, tool_id, milestone_type)
);
CREATE INDEX IF NOT EXISTS idx_milestones_user ON milestones(user_id);

CREATE TABLE IF NOT EXISTS magic_claim_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    token TEXT NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_magic_claim_token ON magic_claim_tokens(token);
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

CREATE VIRTUAL TABLE IF NOT EXISTS makers_fts USING fts5(
    name, bio,
    content='makers',
    content_rowid='id'
);

CREATE TRIGGER IF NOT EXISTS makers_ai AFTER INSERT ON makers BEGIN
    INSERT INTO makers_fts(rowid, name, bio)
    VALUES (new.id, new.name, new.bio);
END;

CREATE TRIGGER IF NOT EXISTS makers_ad AFTER DELETE ON makers BEGIN
    INSERT INTO makers_fts(makers_fts, rowid, name, bio)
    VALUES ('delete', old.id, old.name, old.bio);
END;

CREATE TRIGGER IF NOT EXISTS makers_au AFTER UPDATE ON makers BEGIN
    INSERT INTO makers_fts(makers_fts, rowid, name, bio)
    VALUES ('delete', old.id, old.name, old.bio);
    INSERT INTO makers_fts(rowid, name, bio)
    VALUES (new.id, new.name, new.bio);
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

# ── Token cost estimates per category ────────────────────────────────────
CATEGORY_TOKEN_COSTS = {
    "invoicing-billing": 80_000,
    "email-marketing": 60_000,
    "analytics-metrics": 50_000,
    "project-management": 100_000,
    "customer-support": 70_000,
    "scheduling-booking": 45_000,
    "social-media": 55_000,
    "landing-pages": 30_000,
    "forms-surveys": 35_000,
    "crm-sales": 90_000,
    "file-management": 40_000,
    "authentication": 50_000,
    "payments": 60_000,
    "seo-tools": 40_000,
    "monitoring-uptime": 45_000,
    "api-tools": 55_000,
    "design-creative": 70_000,
    "developer-tools": 50_000,
    "ai-automation": 80_000,
    "feedback-reviews": 35_000,
}

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
        # Migration: add columns if missing (for existing DBs)
        for col, ddl in [
            ("price_pence", "ALTER TABLE tools ADD COLUMN price_pence INTEGER"),
            ("delivery_type", "ALTER TABLE tools ADD COLUMN delivery_type TEXT NOT NULL DEFAULT 'link'"),
            ("delivery_url", "ALTER TABLE tools ADD COLUMN delivery_url TEXT NOT NULL DEFAULT ''"),
            ("stripe_account_id", "ALTER TABLE tools ADD COLUMN stripe_account_id TEXT NOT NULL DEFAULT ''"),
            ("verified_at", "ALTER TABLE tools ADD COLUMN verified_at TIMESTAMP"),
            ("verified_until", "ALTER TABLE tools ADD COLUMN verified_until TIMESTAMP"),
            ("maker_id", "ALTER TABLE tools ADD COLUMN maker_id INTEGER REFERENCES makers(id)"),
        ]:
            try:
                await db.execute(f"SELECT {col} FROM tools LIMIT 1")
            except Exception:
                await db.execute(ddl)
        # Migration: add is_ejectable column if missing
        try:
            await db.execute("SELECT is_ejectable FROM tools LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE tools ADD COLUMN is_ejectable INTEGER NOT NULL DEFAULT 0")
        # Migration: add replaces column if missing (competitors this tool replaces)
        try:
            await db.execute("SELECT replaces FROM tools LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE tools ADD COLUMN replaces TEXT NOT NULL DEFAULT ''")
        # ── boosted_competitor migration ──────────────────────────────────────
        try:
            await db.execute("SELECT boosted_competitor FROM tools LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE tools ADD COLUMN boosted_competitor TEXT NOT NULL DEFAULT ''")
            await db.commit()
        # Create indexes that depend on migrated columns
        await db.execute("CREATE INDEX IF NOT EXISTS idx_tools_maker ON tools(maker_id)")
        # Migration: add tool_id to maker_updates if missing
        try:
            await db.execute("ALTER TABLE maker_updates ADD COLUMN tool_id INTEGER REFERENCES tools(id)")
        except Exception:
            pass
        # Migration: add indie_status to makers if missing
        try:
            await db.execute("SELECT indie_status FROM makers LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE makers ADD COLUMN indie_status TEXT NOT NULL DEFAULT ''")
        # Migration: add stripe_account_id to makers if missing
        try:
            await db.execute("ALTER TABLE makers ADD COLUMN stripe_account_id TEXT")
        except Exception:
            pass
        # Migration: add discount_pence to purchases
        try:
            await db.execute("SELECT discount_pence FROM purchases LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE purchases ADD COLUMN discount_pence INTEGER NOT NULL DEFAULT 0")
        # Migration: add badge_token to users
        try:
            await db.execute("SELECT badge_token FROM users LIMIT 1")
        except Exception:
            await db.execute("ALTER TABLE users ADD COLUMN badge_token TEXT")
        # Platform boost columns
        try:
            await db.execute("ALTER TABLE tools ADD COLUMN is_boosted INTEGER NOT NULL DEFAULT 0")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE tools ADD COLUMN boost_expires_at TEXT DEFAULT NULL")
        except Exception:
            pass
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
                  (t.is_verified * 100 + t.upvote_count) as rank_score,
                  EXISTS(SELECT 1 FROM maker_updates mu WHERE mu.tool_id = t.id AND mu.created_at >= datetime('now', '-14 days')) as has_changelog_14d
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
        """SELECT t.*, c.name as category_name, c.slug as category_slug,
                  m.indie_status
           FROM tools t JOIN categories c ON t.category_id = c.id
           LEFT JOIN makers m ON t.maker_id = m.id
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
                      url: str, maker_name: str, maker_url: str, category_id: int, tags: str,
                      price_pence: Optional[int] = None, delivery_type: str = 'link',
                      delivery_url: str = '', stripe_account_id: str = '') -> int:
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

    # Auto-create maker profile if maker_name provided
    maker_id = None
    if maker_name.strip():
        maker_id = await get_or_create_maker(db, maker_name.strip(), maker_url.strip())

    cursor = await db.execute(
        """INSERT INTO tools (name, slug, tagline, description, url, maker_name, maker_url,
           category_id, tags, price_pence, delivery_type, delivery_url, stripe_account_id, maker_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (name, slug, tagline, description, url, maker_name, maker_url, category_id, tags,
         price_pence, delivery_type, delivery_url, stripe_account_id, maker_id),
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


async def toggle_ejectable(db: aiosqlite.Connection, tool_id: int) -> bool:
    """Toggle ejectable status. Returns new is_ejectable state."""
    cursor = await db.execute("SELECT is_ejectable FROM tools WHERE id = ?", (tool_id,))
    row = await cursor.fetchone()
    if not row:
        return False
    new_val = 0 if row.get('is_ejectable') else 1
    await db.execute("UPDATE tools SET is_ejectable = ? WHERE id = ?", (new_val, tool_id))
    await db.commit()
    return bool(new_val)


# ── Upvotes ───────────────────────────────────────────────────────────────

def hash_ip(ip: str) -> str:
    return hashlib.sha256(f"{_UPVOTE_SALT}{ip}".encode()).hexdigest()


async def toggle_upvote(db: aiosqlite.Connection, tool_id: int, ip: str) -> tuple[int, bool]:
    """Toggle upvote. Returns (new_count, is_upvoted)."""
    ip_h = hash_ip(ip)

    # Use a transaction to prevent race conditions
    await db.execute("BEGIN IMMEDIATE")
    try:
        cursor = await db.execute(
            "SELECT id FROM upvotes WHERE tool_id = ? AND ip_hash = ?", (tool_id, ip_h)
        )
        existing = await cursor.fetchone()

        if existing:
            await db.execute("DELETE FROM upvotes WHERE id = ?", (existing['id'],))
            await db.execute(
                "UPDATE tools SET upvote_count = MAX(0, upvote_count - 1) WHERE id = ?",
                (tool_id,))
            upvoted = False
        else:
            await db.execute(
                "INSERT INTO upvotes (tool_id, ip_hash) VALUES (?, ?)",
                (tool_id, ip_h))
            await db.execute(
                "UPDATE tools SET upvote_count = upvote_count + 1 WHERE id = ?",
                (tool_id,))
            upvoted = True

        count_cursor = await db.execute(
            "SELECT upvote_count FROM tools WHERE id = ?", (tool_id,))
        row = await count_cursor.fetchone()
        count = row['upvote_count'] if row else 0

        await db.commit()
        return count, upvoted
    except Exception:
        await db.rollback()
        raise


async def has_upvoted(db: aiosqlite.Connection, tool_id: int, ip: str) -> bool:
    ip_h = hash_ip(ip)
    cursor = await db.execute(
        "SELECT id FROM upvotes WHERE tool_id = ? AND ip_hash = ?", (tool_id, ip_h)
    )
    return await cursor.fetchone() is not None


# ── Purchases ────────────────────────────────────────────────────────────

async def create_purchase(db: aiosqlite.Connection, *, tool_id: int, buyer_email: str,
                          stripe_session_id: str, amount_pence: int, commission_pence: int,
                          discount_pence: int = 0) -> str:
    """Create a purchase record. Returns the unique purchase_token."""
    token = secrets.token_urlsafe(32)
    await db.execute(
        """INSERT INTO purchases (tool_id, buyer_email, stripe_session_id, amount_pence,
           commission_pence, purchase_token, discount_pence)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (tool_id, buyer_email, stripe_session_id, amount_pence, commission_pence, token, discount_pence),
    )
    await db.commit()
    return token


async def get_purchase_by_token(db: aiosqlite.Connection, token: str):
    cursor = await db.execute(
        """SELECT p.*, t.name as tool_name, t.slug as tool_slug, t.delivery_type,
                  t.delivery_url, t.maker_name
           FROM purchases p JOIN tools t ON p.tool_id = t.id
           WHERE p.purchase_token = ?""",
        (token,),
    )
    return await cursor.fetchone()


async def get_purchase_by_session(db: aiosqlite.Connection, session_id: str):
    cursor = await db.execute(
        """SELECT p.*, t.name as tool_name, t.slug as tool_slug, t.delivery_type,
                  t.delivery_url, t.maker_name
           FROM purchases p JOIN tools t ON p.tool_id = t.id
           WHERE p.stripe_session_id = ?""",
        (session_id,),
    )
    return await cursor.fetchone()


async def get_purchases_for_tool(db: aiosqlite.Connection, tool_id: int):
    cursor = await db.execute(
        """SELECT * FROM purchases WHERE tool_id = ? ORDER BY created_at DESC""",
        (tool_id,),
    )
    return await cursor.fetchall()


async def get_purchase_stats(db: aiosqlite.Connection):
    """Get total revenue and purchase count for admin dashboard."""
    cursor = await db.execute(
        """SELECT COUNT(*) as total_purchases,
                  COALESCE(SUM(amount_pence), 0) as total_revenue,
                  COALESCE(SUM(commission_pence), 0) as total_commission
           FROM purchases"""
    )
    return await cursor.fetchone()


async def update_tool_stripe_account(db: aiosqlite.Connection, tool_id: int, stripe_account_id: str):
    await db.execute("UPDATE tools SET stripe_account_id = ? WHERE id = ?", (stripe_account_id, tool_id))
    await db.commit()


# ── Verification ─────────────────────────────────────────────────────────

async def verify_tool(db: aiosqlite.Connection, tool_id: int):
    """Mark a tool as verified (paid verification)."""
    now = datetime.utcnow().isoformat()
    await db.execute(
        "UPDATE tools SET is_verified = 1, verified_at = ? WHERE id = ?",
        (now, tool_id),
    )
    await db.commit()


async def get_tool_by_id(db: aiosqlite.Connection, tool_id: int):
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.id = ?""",
        (tool_id,),
    )
    return await cursor.fetchone()


# ── Makers ───────────────────────────────────────────────────────────────

async def get_or_create_maker(db: aiosqlite.Connection, name: str, url: str = '') -> int:
    """Get existing maker by name or create one. Returns maker_id."""
    slug = slugify(name)
    if not slug:
        return None
    cursor = await db.execute("SELECT id FROM makers WHERE slug = ?", (slug,))
    row = await cursor.fetchone()
    if row:
        return row['id']
    cursor = await db.execute(
        "INSERT INTO makers (slug, name, url) VALUES (?, ?, ?)",
        (slug, name, url),
    )
    await db.commit()
    return cursor.lastrowid


async def get_maker_by_slug(db: aiosqlite.Connection, slug: str):
    cursor = await db.execute("SELECT * FROM makers WHERE slug = ?", (slug,))
    return await cursor.fetchone()


async def get_maker_with_tools(db: aiosqlite.Connection, slug: str):
    """Get maker profile and all their approved tools."""
    maker = await get_maker_by_slug(db, slug)
    if not maker:
        return None, []
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.maker_id = ? AND t.status = 'approved'
           ORDER BY (t.is_verified * 100 + t.upvote_count) DESC""",
        (maker['id'],),
    )
    tools = await cursor.fetchall()
    return maker, tools


async def get_maker_stats(db: aiosqlite.Connection, maker_id: int) -> dict:
    """Get aggregate stats for a maker."""
    cursor = await db.execute(
        """SELECT COUNT(*) as tool_count,
                  COALESCE(SUM(upvote_count), 0) as total_upvotes,
                  COALESCE(SUM(is_verified), 0) as verified_count
           FROM tools WHERE maker_id = ? AND status = 'approved'""",
        (maker_id,),
    )
    return await cursor.fetchone()


# ── Featured Tool ────────────────────────────────────────────────────────

async def set_featured_tool(db: aiosqlite.Connection, tool_id: int, headline: str, description: str = ''):
    await db.execute(
        "INSERT INTO featured_tools (tool_id, headline, description) VALUES (?, ?, ?)",
        (tool_id, headline, description),
    )
    await db.commit()


async def get_featured_tool(db: aiosqlite.Connection):
    """Get the most recently featured tool."""
    cursor = await db.execute(
        """SELECT ft.*, t.name as tool_name, t.slug as tool_slug, t.tagline,
                  t.is_verified, t.upvote_count, t.url as tool_url,
                  c.name as category_name, c.slug as category_slug
           FROM featured_tools ft
           JOIN tools t ON ft.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved'
           ORDER BY ft.featured_date DESC LIMIT 1"""
    )
    return await cursor.fetchone()


# ── Collections ──────────────────────────────────────────────────────────

async def create_collection(db: aiosqlite.Connection, *, title: str, description: str = '',
                            cover_emoji: str = '') -> int:
    slug = slugify(title)
    base_slug = slug
    counter = 1
    while True:
        existing = await db.execute("SELECT id FROM collections WHERE slug = ?", (slug,))
        if await existing.fetchone() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    cursor = await db.execute(
        "INSERT INTO collections (slug, title, description, cover_emoji) VALUES (?, ?, ?, ?)",
        (slug, title, description, cover_emoji),
    )
    await db.commit()
    return cursor.lastrowid


async def get_all_collections(db: aiosqlite.Connection):
    cursor = await db.execute(
        """SELECT c.*, COUNT(ct.tool_id) as tool_count
           FROM collections c
           LEFT JOIN collection_tools ct ON ct.collection_id = c.id
           GROUP BY c.id ORDER BY c.created_at DESC"""
    )
    return await cursor.fetchall()


async def get_collection_by_slug(db: aiosqlite.Connection, slug: str):
    cursor = await db.execute("SELECT * FROM collections WHERE slug = ?", (slug,))
    return await cursor.fetchone()


async def get_collection_with_tools(db: aiosqlite.Connection, slug: str):
    """Get collection and its tools in order."""
    coll = await get_collection_by_slug(db, slug)
    if not coll:
        return None, []
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM collection_tools ct
           JOIN tools t ON ct.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE ct.collection_id = ? AND t.status = 'approved'
           ORDER BY ct.position ASC""",
        (coll['id'],),
    )
    tools = await cursor.fetchall()
    return coll, tools


async def add_tool_to_collection(db: aiosqlite.Connection, collection_id: int, tool_id: int, position: int = 0):
    try:
        await db.execute(
            "INSERT INTO collection_tools (collection_id, tool_id, position) VALUES (?, ?, ?)",
            (collection_id, tool_id, position),
        )
        await db.commit()
    except Exception:
        pass  # Already in collection


async def remove_tool_from_collection(db: aiosqlite.Connection, collection_id: int, tool_id: int):
    await db.execute(
        "DELETE FROM collection_tools WHERE collection_id = ? AND tool_id = ?",
        (collection_id, tool_id),
    )
    await db.commit()


async def delete_collection(db: aiosqlite.Connection, collection_id: int):
    await db.execute("DELETE FROM collection_tools WHERE collection_id = ?", (collection_id,))
    await db.execute("DELETE FROM collections WHERE id = ?", (collection_id,))
    await db.commit()


# ── Comparisons ──────────────────────────────────────────────────────────

async def get_tools_for_comparison(db: aiosqlite.Connection, slug1: str, slug2: str):
    """Get two tools by slug for comparison."""
    t1 = await get_tool_by_slug(db, slug1)
    t2 = await get_tool_by_slug(db, slug2)
    return t1, t2


async def get_category_tools_for_compare(db: aiosqlite.Connection, category_id: int, limit: int = 20):
    """Get tools in a category for generating compare links."""
    cursor = await db.execute(
        """SELECT t.slug, t.name FROM tools t
           WHERE t.category_id = ? AND t.status = 'approved'
           ORDER BY (t.is_verified * 100 + t.upvote_count) DESC LIMIT ?""",
        (category_id, limit),
    )
    return await cursor.fetchall()


# ── Recently Added ───────────────────────────────────────────────────────

async def get_recent_tools(db: aiosqlite.Connection, limit: int = 6, days: int = 7):
    """Get recently approved tools."""
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved'
           ORDER BY t.created_at DESC LIMIT ?""",
        (limit,),
    )
    return await cursor.fetchall()


# ── Users & Sessions ─────────────────────────────────────────────────────

async def create_user(db: aiosqlite.Connection, *, email: str, password_hash: str,
                      name: str, role: str = 'buyer', maker_id: Optional[int] = None) -> int:
    cursor = await db.execute(
        "INSERT INTO users (email, password_hash, name, role, maker_id) VALUES (?, ?, ?, ?, ?)",
        (email.lower().strip(), password_hash, name.strip(), role, maker_id),
    )
    await db.commit()
    return cursor.lastrowid


async def get_user_by_email(db: aiosqlite.Connection, email: str):
    cursor = await db.execute("SELECT * FROM users WHERE email = ?", (email.lower().strip(),))
    return await cursor.fetchone()


async def get_user_by_id(db: aiosqlite.Connection, user_id: int):
    cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return await cursor.fetchone()


async def create_session(db: aiosqlite.Connection, user_id: int, token: str, expires_at: str) -> int:
    cursor = await db.execute(
        "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at),
    )
    await db.commit()
    return cursor.lastrowid


async def get_session_by_token(db: aiosqlite.Connection, token: str):
    cursor = await db.execute(
        """SELECT s.*, u.id as uid, u.email, u.name, u.role, u.maker_id, u.email_verified
           FROM sessions s JOIN users u ON s.user_id = u.id
           WHERE s.token = ? AND s.expires_at > datetime('now')""",
        (token,),
    )
    return await cursor.fetchone()


async def delete_session(db: aiosqlite.Connection, token: str):
    await db.execute("DELETE FROM sessions WHERE token = ?", (token,))
    await db.commit()


async def delete_expired_sessions(db: aiosqlite.Connection):
    await db.execute("DELETE FROM sessions WHERE expires_at <= datetime('now')")
    await db.commit()


async def cleanup_expired_sessions(db: aiosqlite.Connection):
    """Delete expired sessions to prevent table bloat."""
    await db.execute("DELETE FROM sessions WHERE expires_at < datetime('now')")
    await db.commit()


async def update_user(db: aiosqlite.Connection, user_id: int, **fields):
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [user_id]
    await db.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
    await db.commit()


# ── Reviews ──────────────────────────────────────────────────────────────

async def create_review(db: aiosqlite.Connection, *, tool_id: int, user_id: int,
                        rating: int, title: str = '', body: str = '') -> int:
    # Auto-detect verified purchase
    cursor = await db.execute(
        """SELECT id FROM purchases WHERE tool_id = ? AND buyer_email = (
            SELECT email FROM users WHERE id = ?
        )""",
        (tool_id, user_id),
    )
    is_verified_purchase = 1 if await cursor.fetchone() else 0
    cursor = await db.execute(
        """INSERT INTO reviews (tool_id, user_id, rating, title, body, is_verified_purchase)
           VALUES (?, ?, ?, ?, ?, ?)
           ON CONFLICT(tool_id, user_id) DO UPDATE SET
           rating=excluded.rating, title=excluded.title, body=excluded.body""",
        (tool_id, user_id, rating, title.strip(), body.strip(), is_verified_purchase),
    )
    await db.commit()
    return cursor.lastrowid


async def get_reviews_for_tool(db: aiosqlite.Connection, tool_id: int):
    cursor = await db.execute(
        """SELECT r.*, u.name as reviewer_name
           FROM reviews r JOIN users u ON r.user_id = u.id
           WHERE r.tool_id = ?
           ORDER BY r.created_at DESC""",
        (tool_id,),
    )
    return await cursor.fetchall()


async def get_tool_rating(db: aiosqlite.Connection, tool_id: int) -> dict:
    cursor = await db.execute(
        """SELECT COALESCE(AVG(rating), 0) as avg_rating, COUNT(*) as review_count
           FROM reviews WHERE tool_id = ?""",
        (tool_id,),
    )
    return await cursor.fetchone()


async def get_user_review_for_tool(db: aiosqlite.Connection, tool_id: int, user_id: int):
    cursor = await db.execute(
        "SELECT * FROM reviews WHERE tool_id = ? AND user_id = ?",
        (tool_id, user_id),
    )
    return await cursor.fetchone()


async def get_all_reviews_admin(db: aiosqlite.Connection):
    cursor = await db.execute(
        """SELECT r.*, u.name as reviewer_name, t.name as tool_name, t.slug as tool_slug
           FROM reviews r JOIN users u ON r.user_id = u.id JOIN tools t ON r.tool_id = t.id
           ORDER BY r.created_at DESC"""
    )
    return await cursor.fetchall()


async def delete_review(db: aiosqlite.Connection, review_id: int):
    await db.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    await db.commit()


# ── Advanced Search ──────────────────────────────────────────────────────

async def search_tools_advanced(db: aiosqlite.Connection, *, query: str = "",
                                 price_filter: str = "", sort: str = "relevance",
                                 verified_only: bool = False, category_id: Optional[int] = None,
                                 page: int = 1, per_page: int = 12):
    conditions = ["t.status = 'approved'"]
    params = []

    if price_filter == "free":
        conditions.append("t.price_pence IS NULL")
    elif price_filter == "paid":
        conditions.append("t.price_pence > 0")

    if verified_only:
        conditions.append("t.is_verified = 1")

    if category_id:
        conditions.append("t.category_id = ?")
        params.append(category_id)

    where = " AND ".join(conditions)

    # Sort
    order_by = {
        "upvotes": "(t.is_verified * 100 + t.upvote_count) DESC, t.created_at DESC",
        "newest": "t.created_at DESC",
        "price_low": "COALESCE(t.price_pence, 0) ASC, t.created_at DESC",
        "price_high": "COALESCE(t.price_pence, 0) DESC, t.created_at DESC",
    }.get(sort, "(t.is_verified * 100 + t.upvote_count) DESC, t.created_at DESC")

    if query.strip():
        safe_q = sanitize_fts(query)
        if not safe_q:
            return [], 0
        # Use FTS
        sql = f"""SELECT t.*, c.name as category_name, c.slug as category_slug, bm25(tools_fts) as rank
                  FROM tools_fts fts
                  JOIN tools t ON t.id = fts.rowid
                  JOIN categories c ON t.category_id = c.id
                  WHERE tools_fts MATCH ? AND {where}
                  ORDER BY {order_by if sort != 'relevance' else '(t.is_verified * 5.0 + rank)'}
                  LIMIT ? OFFSET ?"""
        fts_params = [safe_q] + params + [per_page, (page - 1) * per_page]
        cursor = await db.execute(sql, fts_params)
        rows = await cursor.fetchall()

        count_sql = f"""SELECT COUNT(*) as cnt
                        FROM tools_fts fts
                        JOIN tools t ON t.id = fts.rowid
                        WHERE tools_fts MATCH ? AND {where}"""
        count_cursor = await db.execute(count_sql, [safe_q] + params)
        total = (await count_cursor.fetchone())['cnt']
    else:
        sql = f"""SELECT t.*, c.name as category_name, c.slug as category_slug
                  FROM tools t JOIN categories c ON t.category_id = c.id
                  WHERE {where}
                  ORDER BY {order_by}
                  LIMIT ? OFFSET ?"""
        cursor = await db.execute(sql, params + [per_page, (page - 1) * per_page])
        rows = await cursor.fetchall()

        count_sql = f"""SELECT COUNT(*) as cnt FROM tools t WHERE {where}"""
        # Need to rebuild conditions without aliases for count
        count_cursor = await db.execute(count_sql, params)
        total = (await count_cursor.fetchone())['cnt']

    return rows, total


# ── Maker Dashboard Queries ──────────────────────────────────────────────

async def get_tools_by_maker(db: aiosqlite.Connection, maker_id: int):
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.maker_id = ?
           ORDER BY t.created_at DESC""",
        (maker_id,),
    )
    return await cursor.fetchall()


async def get_sales_by_maker(db: aiosqlite.Connection, maker_id: int):
    cursor = await db.execute(
        """SELECT p.*, t.name as tool_name, t.slug as tool_slug
           FROM purchases p
           JOIN tools t ON p.tool_id = t.id
           WHERE t.maker_id = ?
           ORDER BY p.created_at DESC""",
        (maker_id,),
    )
    return await cursor.fetchall()


async def get_maker_revenue(db: aiosqlite.Connection, maker_id: int) -> dict:
    cursor = await db.execute(
        """SELECT COUNT(*) as sale_count,
                  COALESCE(SUM(p.amount_pence), 0) as total_revenue,
                  COALESCE(SUM(p.commission_pence), 0) as total_commission
           FROM purchases p
           JOIN tools t ON p.tool_id = t.id
           WHERE t.maker_id = ?""",
        (maker_id,),
    )
    return await cursor.fetchone()


async def update_tool(db: aiosqlite.Connection, tool_id: int, **fields):
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [tool_id]
    await db.execute(f"UPDATE tools SET {set_clause} WHERE id = ?", values)
    await db.commit()


# ── Tool Views (Analytics) ───────────────────────────────────────────────

async def record_tool_view(db: aiosqlite.Connection, tool_id: int, ip: str):
    ip_h = hash_ip(ip)
    await db.execute(
        "INSERT INTO tool_views (tool_id, ip_hash) VALUES (?, ?)",
        (tool_id, ip_h),
    )
    await db.commit()


async def get_tool_view_count(db: aiosqlite.Connection, tool_id: int, days: int = 30) -> int:
    cursor = await db.execute(
        """SELECT COUNT(*) as cnt FROM tool_views
           WHERE tool_id = ? AND viewed_at >= datetime('now', ?)""",
        (tool_id, f'-{days} days'),
    )
    return (await cursor.fetchone())['cnt']


async def get_tool_views_by_maker(db: aiosqlite.Connection, maker_id: int, days: int = 30):
    cursor = await db.execute(
        """SELECT t.id, t.name, t.slug, COUNT(tv.id) as view_count
           FROM tools t
           LEFT JOIN tool_views tv ON tv.tool_id = t.id AND tv.viewed_at >= datetime('now', ?)
           WHERE t.maker_id = ?
           GROUP BY t.id
           ORDER BY view_count DESC""",
        (f'-{days} days', maker_id),
    )
    return await cursor.fetchall()


# ── Subscriptions ────────────────────────────────────────────────────────

async def create_subscription(db: aiosqlite.Connection, *, user_id: int,
                               stripe_subscription_id: str, plan: str = 'pro',
                               current_period_end: str = '') -> int:
    cursor = await db.execute(
        """INSERT INTO subscriptions (user_id, stripe_subscription_id, plan, current_period_end)
           VALUES (?, ?, ?, ?)""",
        (user_id, stripe_subscription_id, plan, current_period_end),
    )
    await db.commit()
    return cursor.lastrowid


async def get_active_subscription(db: aiosqlite.Connection, user_id: int):
    cursor = await db.execute(
        """SELECT * FROM subscriptions
           WHERE user_id = ? AND status = 'active'
           ORDER BY created_at DESC LIMIT 1""",
        (user_id,),
    )
    return await cursor.fetchone()


async def update_subscription_status(db: aiosqlite.Connection, stripe_subscription_id: str, status: str):
    await db.execute(
        "UPDATE subscriptions SET status = ? WHERE stripe_subscription_id = ?",
        (status, stripe_subscription_id),
    )
    await db.commit()


# ── Maker by ID ──────────────────────────────────────────────────────────

async def get_maker_by_id(db: aiosqlite.Connection, maker_id: int):
    cursor = await db.execute("SELECT * FROM makers WHERE id = ?", (maker_id,))
    return await cursor.fetchone()


async def update_maker(db: aiosqlite.Connection, maker_id: int, **fields):
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [maker_id]
    await db.execute(f"UPDATE makers SET {set_clause} WHERE id = ?", values)
    await db.commit()


async def update_maker_stripe_account(db: aiosqlite.Connection, maker_id: int, stripe_account_id: str):
    """Save Stripe Connect account ID to maker record."""
    await db.execute("UPDATE makers SET stripe_account_id = ? WHERE id = ?", (stripe_account_id, maker_id))
    await db.commit()


# ── Recently Added ───────────────────────────────────────────────────────

async def get_recent_tools_paginated(db: aiosqlite.Connection, page: int = 1, per_page: int = 12):
    offset = (page - 1) * per_page
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved'
           ORDER BY t.created_at DESC LIMIT ? OFFSET ?""",
        (per_page, offset),
    )
    rows = await cursor.fetchall()
    count_cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM tools WHERE status = 'approved'"
    )
    total = (await count_cursor.fetchone())['cnt']
    return rows, total


# ── Maker Search & Directory ─────────────────────────────────────────────

async def search_makers(db: aiosqlite.Connection, query: str, limit: int = 20):
    safe_q = sanitize_fts(query)
    if not safe_q:
        return []
    cursor = await db.execute(
        """SELECT m.*, bm25(makers_fts) as rank
           FROM makers_fts fts
           JOIN makers m ON m.id = fts.rowid
           WHERE makers_fts MATCH ?
           ORDER BY rank LIMIT ?""",
        (safe_q, limit),
    )
    return await cursor.fetchall()


async def get_all_makers_paginated(db: aiosqlite.Connection, page: int = 1, per_page: int = 12,
                                    sort: str = "most_tools"):
    offset = (page - 1) * per_page
    order_by = {
        "most_tools": "tool_count DESC, m.created_at DESC",
        "most_upvoted": "total_upvotes DESC, m.created_at DESC",
        "newest": "m.created_at DESC",
    }.get(sort, "tool_count DESC, m.created_at DESC")

    cursor = await db.execute(
        f"""SELECT m.*,
                   COUNT(t.id) as tool_count,
                   COALESCE(SUM(t.upvote_count), 0) as total_upvotes
            FROM makers m
            LEFT JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
            GROUP BY m.id
            ORDER BY {order_by}
            LIMIT ? OFFSET ?""",
        (per_page, offset),
    )
    rows = await cursor.fetchall()
    count_cursor = await db.execute("SELECT COUNT(*) as cnt FROM makers")
    total = (await count_cursor.fetchone())['cnt']
    return rows, total


# ── Wishlists ────────────────────────────────────────────────────────────

async def toggle_wishlist(db: aiosqlite.Connection, user_id: int, tool_id: int) -> tuple[bool, int]:
    """Toggle wishlist. Returns (is_saved, total_saves_for_tool)."""
    cursor = await db.execute(
        "SELECT id FROM wishlists WHERE user_id = ? AND tool_id = ?", (user_id, tool_id)
    )
    existing = await cursor.fetchone()
    if existing:
        await db.execute("DELETE FROM wishlists WHERE id = ?", (existing['id'],))
        is_saved = False
    else:
        await db.execute("INSERT INTO wishlists (user_id, tool_id) VALUES (?, ?)", (user_id, tool_id))
        is_saved = True
    await db.commit()
    count_cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM wishlists WHERE tool_id = ?", (tool_id,)
    )
    count = (await count_cursor.fetchone())['cnt']
    return is_saved, count


async def is_wishlisted(db: aiosqlite.Connection, user_id: int, tool_id: int) -> bool:
    cursor = await db.execute(
        "SELECT id FROM wishlists WHERE user_id = ? AND tool_id = ?", (user_id, tool_id)
    )
    return await cursor.fetchone() is not None


async def get_user_wishlist(db: aiosqlite.Connection, user_id: int, page: int = 1, per_page: int = 12):
    offset = (page - 1) * per_page
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug, w.created_at as saved_at
           FROM wishlists w
           JOIN tools t ON w.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE w.user_id = ? AND t.status = 'approved'
           ORDER BY w.created_at DESC LIMIT ? OFFSET ?""",
        (user_id, per_page, offset),
    )
    rows = await cursor.fetchall()
    count_cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM wishlists w JOIN tools t ON w.tool_id = t.id WHERE w.user_id = ? AND t.status = 'approved'",
        (user_id,),
    )
    total = (await count_cursor.fetchone())['cnt']
    return rows, total


# ── Maker Updates ────────────────────────────────────────────────────────

async def create_maker_update(db: aiosqlite.Connection, maker_id: int, title: str,
                               body: str, update_type: str = 'update',
                               tool_id: int = None) -> int:
    if update_type not in ('update', 'launch', 'milestone', 'changelog'):
        update_type = 'update'
    cursor = await db.execute(
        "INSERT INTO maker_updates (maker_id, title, body, update_type, tool_id) VALUES (?, ?, ?, ?, ?)",
        (maker_id, title.strip(), body.strip(), update_type, tool_id),
    )
    await db.commit()
    return cursor.lastrowid


async def get_recent_updates(db: aiosqlite.Connection, limit: int = 20):
    cursor = await db.execute(
        """SELECT mu.*, m.name as maker_name, m.slug as maker_slug
           FROM maker_updates mu
           JOIN makers m ON mu.maker_id = m.id
           ORDER BY mu.created_at DESC LIMIT ?""",
        (limit,),
    )
    return await cursor.fetchall()


async def get_tool_changelogs(db, tool_id: int, limit: int = 20) -> list:
    cursor = await db.execute(
        """SELECT mu.*, m.name AS maker_name, m.slug AS maker_slug
           FROM maker_updates mu
           JOIN makers m ON mu.maker_id = m.id
           WHERE mu.tool_id = ?
           ORDER BY mu.created_at DESC LIMIT ?""",
        (tool_id, limit)
    )
    return [dict(r) for r in await cursor.fetchall()]


async def get_updates_by_maker(db: aiosqlite.Connection, maker_id: int, limit: int = 10):
    cursor = await db.execute(
        """SELECT * FROM maker_updates
           WHERE maker_id = ?
           ORDER BY created_at DESC LIMIT ?""",
        (maker_id, limit),
    )
    return await cursor.fetchall()


# ── All Makers (admin) ──────────────────────────────────────────────────

async def get_all_makers_admin(db: aiosqlite.Connection):
    cursor = await db.execute(
        """SELECT m.*, COUNT(t.id) as tool_count
           FROM makers m
           LEFT JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
           GROUP BY m.id ORDER BY m.created_at DESC"""
    )
    return await cursor.fetchall()


# ── Notifications ────────────────────────────────────────────────────────

async def create_notification(db: aiosqlite.Connection, user_id: int, type: str,
                               message: str, link: str = '') -> int:
    cursor = await db.execute(
        "INSERT INTO notifications (user_id, type, message, link) VALUES (?, ?, ?, ?)",
        (user_id, type, message, link),
    )
    await db.commit()
    return cursor.lastrowid


async def get_unread_count(db: aiosqlite.Connection, user_id: int) -> int:
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM notifications WHERE user_id = ? AND is_read = 0",
        (user_id,),
    )
    return (await cursor.fetchone())['cnt']


async def get_notifications(db: aiosqlite.Connection, user_id: int, limit: int = 20):
    cursor = await db.execute(
        """SELECT * FROM notifications
           WHERE user_id = ?
           ORDER BY is_read ASC, created_at DESC LIMIT ?""",
        (user_id, limit),
    )
    return await cursor.fetchall()


async def mark_notifications_read(db: aiosqlite.Connection, user_id: int):
    await db.execute(
        "UPDATE notifications SET is_read = 1 WHERE user_id = ? AND is_read = 0",
        (user_id,),
    )
    await db.commit()


async def mark_notification_read(db: aiosqlite.Connection, notification_id: int):
    await db.execute(
        "UPDATE notifications SET is_read = 1 WHERE id = ?",
        (notification_id,),
    )
    await db.commit()


# ── Page Views (Site Analytics) ──────────────────────────────────────────

async def track_pageview(db, page: str, visitor_id: str, referrer: str = ""):
    from datetime import datetime
    await db.execute(
        "INSERT INTO page_views (timestamp, page, visitor_id, referrer) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), page, visitor_id, referrer)
    )
    await db.commit()


async def cleanup_old_page_views(db, days: int = 90):
    """Delete page views older than N days to prevent table bloat. Keeps aggregate counts accurate via tool view_count."""
    await db.execute(
        "DELETE FROM page_views WHERE timestamp < datetime('now', ?)",
        (f'-{days} days',))
    await db.commit()


# ── Password Reset & Email Verification ─────────────────────────────────

async def create_password_reset_token(db, user_id: int) -> str:
    """Generate a password reset token with 1-hour expiry."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    await db.execute(
        "INSERT INTO password_reset_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at.isoformat())
    )
    await db.commit()
    return token


async def get_valid_reset_token(db, token: str):
    """Return user_id if token is valid and unused, else None."""
    cursor = await db.execute(
        "SELECT user_id, expires_at, used FROM password_reset_tokens WHERE token = ?",
        (token,)
    )
    row = await cursor.fetchone()
    if not row:
        return None
    if row['used']:
        return None
    if datetime.fromisoformat(row['expires_at']) < datetime.utcnow():
        return None
    return row['user_id']


async def mark_reset_token_used(db, token: str):
    """Mark a reset token as used."""
    await db.execute("UPDATE password_reset_tokens SET used = 1 WHERE token = ?", (token,))
    await db.commit()


async def create_email_verification_token(db, user_id: int) -> str:
    """Generate an email verification token with 24-hour expiry."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    await db.execute(
        "INSERT INTO email_verification_tokens (user_id, token, expires_at) VALUES (?, ?, ?)",
        (user_id, token, expires_at.isoformat())
    )
    await db.commit()
    return token


async def verify_email_token(db, token: str):
    """Verify email token: mark user as verified, return user_id or None.

    Note: token is NOT deleted after use — it expires naturally after 24h.
    This prevents email client link prefetching from consuming the token
    before the user actually clicks.
    """
    cursor = await db.execute(
        "SELECT user_id, expires_at FROM email_verification_tokens WHERE token = ?",
        (token,)
    )
    row = await cursor.fetchone()
    if not row:
        return None
    if datetime.fromisoformat(row['expires_at']) < datetime.utcnow():
        # Expired — clean it up
        await db.execute("DELETE FROM email_verification_tokens WHERE token = ?", (token,))
        await db.commit()
        return None
    # Mark user as verified (idempotent — safe to call multiple times)
    await db.execute("UPDATE users SET email_verified = 1 WHERE id = ?", (row['user_id'],))
    await db.commit()
    return row['user_id']


# ── Tokens Saved ─────────────────────────────────────────────────────────

async def get_platform_tokens_saved(db: aiosqlite.Connection) -> int:
    """Calculate total tokens saved across all purchases."""
    cursor = await db.execute(
        """SELECT c.slug, COUNT(*) as cnt
           FROM purchases p
           JOIN tools t ON p.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           GROUP BY c.slug"""
    )
    rows = await cursor.fetchall()
    total = 0
    for row in rows:
        cost = CATEGORY_TOKEN_COSTS.get(row['slug'], 50_000)
        total += cost * row['cnt']
    return total


async def get_user_tokens_saved(db: aiosqlite.Connection, user_id: int) -> int:
    """Calculate tokens saved for a specific user (purchases + wishlist)."""
    # Purchases
    cursor = await db.execute(
        """SELECT c.slug, COUNT(*) as cnt
           FROM purchases p
           JOIN tools t ON p.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE p.buyer_email = (SELECT email FROM users WHERE id = ?)
           GROUP BY c.slug""",
        (user_id,),
    )
    rows = await cursor.fetchall()
    total = 0
    for row in rows:
        cost = CATEGORY_TOKEN_COSTS.get(row['slug'], 50_000)
        total += cost * row['cnt']
    # Wishlist
    cursor2 = await db.execute(
        """SELECT c.slug, COUNT(*) as cnt
           FROM wishlists w
           JOIN tools t ON w.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE w.user_id = ?
           GROUP BY c.slug""",
        (user_id,),
    )
    rows2 = await cursor2.fetchall()
    for row in rows2:
        cost = CATEGORY_TOKEN_COSTS.get(row['slug'], 50_000)
        total += cost * row['cnt']
    return total


# ── Maker Pulse (Last Activity) ──────────────────────────────────────────

async def get_tool_last_activity(db: aiosqlite.Connection, tool_id: int) -> str:
    """Get the most recent activity date for a tool (changelog or tool update)."""
    cursor = await db.execute(
        """SELECT MAX(dt) as last_active FROM (
            SELECT created_at as dt FROM maker_updates WHERE tool_id = ?
            UNION ALL
            SELECT created_at as dt FROM tools WHERE id = ?
        )""",
        (tool_id, tool_id),
    )
    row = await cursor.fetchone()
    return row['last_active'] if row and row['last_active'] else ''


async def get_tools_replacing(db: aiosqlite.Connection, competitor: str, limit: int = 20):
    """Get all approved tools that replace a given competitor."""
    # Search in the replaces field (comma-separated list)
    like_pattern = f'%{competitor}%'
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved' AND LOWER(t.replaces) LIKE LOWER(?)
           ORDER BY (CASE WHEN t.boosted_competitor != '' THEN 0 ELSE 1 END), (t.is_verified * 100 + t.upvote_count) DESC LIMIT ?""",
        (like_pattern, limit),
    )
    return await cursor.fetchall()


async def get_all_competitors(db: aiosqlite.Connection):
    """Get a list of all unique competitors mentioned in tool replaces fields."""
    cursor = await db.execute(
        "SELECT DISTINCT replaces FROM tools WHERE status = 'approved' AND replaces != ''"
    )
    rows = await cursor.fetchall()
    competitors = set()
    for row in rows:
        for comp in row['replaces'].split(','):
            comp = comp.strip()
            if comp:
                competitors.add(comp)
    return sorted(competitors, key=str.lower)


async def toggle_tool_boost(db: aiosqlite.Connection, tool_id: int, competitor: str = ''):
    """Toggle a tool's boosted status for a specific competitor alternatives page."""
    cursor = await db.execute("SELECT boosted_competitor FROM tools WHERE id = ?", (tool_id,))
    row = await cursor.fetchone()
    if not row:
        return
    current = row[0] or ''
    if current == competitor and competitor:
        # Un-boost
        await db.execute("UPDATE tools SET boosted_competitor = '' WHERE id = ?", (tool_id,))
    else:
        # Set boost
        await db.execute("UPDATE tools SET boosted_competitor = ? WHERE id = ?", (competitor, tool_id))
    await db.commit()


async def activate_boost(db, tool_id: int, days: int = 30):
    """Activate a 30-day platform boost for a tool."""
    expires_at = (datetime.utcnow() + timedelta(days=days)).isoformat()
    await db.execute(
        "UPDATE tools SET is_boosted = 1, boost_expires_at = ? WHERE id = ?",
        (expires_at, tool_id))
    await db.commit()

async def get_active_boosts(db):
    """Get all tools with active (unexpired) platform boosts."""
    now = datetime.utcnow().isoformat()
    cursor = await db.execute(
        "SELECT * FROM tools WHERE is_boosted = 1 AND boost_expires_at > ? AND status = 'approved'",
        (now,))
    return await cursor.fetchall()


# ── Stacks (Bundles) ────────────────────────────────────────────────────

async def create_stack(db, *, title: str, description: str = '', cover_emoji: str = '',
                       discount_percent: int = 15) -> int:
    """Create a new stack (bundle). Returns the stack id."""
    slug = slugify(title)
    base_slug = slug
    counter = 1
    while True:
        existing = await db.execute("SELECT id FROM stacks WHERE slug = ?", (slug,))
        if await existing.fetchone() is None:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    cursor = await db.execute(
        "INSERT INTO stacks (slug, title, description, cover_emoji, discount_percent) VALUES (?, ?, ?, ?, ?)",
        (slug, title, description, cover_emoji, discount_percent),
    )
    await db.commit()
    return cursor.lastrowid


async def get_all_stacks(db):
    """Get all stacks with tool counts."""
    cursor = await db.execute(
        """SELECT s.*, COUNT(st.tool_id) as tool_count
           FROM stacks s LEFT JOIN stack_tools st ON st.stack_id = s.id
           GROUP BY s.id ORDER BY s.created_at DESC""")
    return await cursor.fetchall()


async def get_stack_by_slug(db, slug: str):
    """Get a stack by its slug."""
    cursor = await db.execute("SELECT * FROM stacks WHERE slug = ?", (slug,))
    return await cursor.fetchone()


async def get_stack_by_id(db, stack_id: int):
    """Get a stack by its id."""
    cursor = await db.execute("SELECT * FROM stacks WHERE id = ?", (stack_id,))
    return await cursor.fetchone()


async def get_stack_with_tools(db, slug: str):
    """Get a stack and its tools in order. Returns (stack, tools)."""
    stack = await get_stack_by_slug(db, slug)
    if not stack:
        return None, []
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug,
                  m.name as maker_name, m.slug as maker_slug
           FROM stack_tools st
           JOIN tools t ON st.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           LEFT JOIN makers m ON t.maker_id = m.id
           WHERE st.stack_id = ? AND t.status = 'approved'
           ORDER BY st.position ASC""",
        (stack['id'],))
    tools = await cursor.fetchall()
    return stack, tools


async def add_tool_to_stack(db, stack_id: int, tool_id: int, position: int = 0):
    """Add a tool to a stack."""
    try:
        await db.execute("INSERT INTO stack_tools (stack_id, tool_id, position) VALUES (?, ?, ?)",
                         (stack_id, tool_id, position))
        await db.commit()
    except Exception:
        pass


async def remove_tool_from_stack(db, stack_id: int, tool_id: int):
    """Remove a tool from a stack."""
    await db.execute("DELETE FROM stack_tools WHERE stack_id = ? AND tool_id = ?", (stack_id, tool_id))
    await db.commit()


async def delete_stack(db, stack_id: int):
    """Delete a stack and its associated data."""
    await db.execute("DELETE FROM stack_tools WHERE stack_id = ?", (stack_id,))
    await db.execute("DELETE FROM stack_purchases WHERE stack_id = ?", (stack_id,))
    await db.execute("DELETE FROM stacks WHERE id = ?", (stack_id,))
    await db.commit()


# ── Stack Purchases ─────────────────────────────────────────────────────

async def create_stack_purchase(db, *, stack_id: int, buyer_email: str,
                                stripe_session_id: str, total_amount_pence: int,
                                discount_pence: int = 0) -> str:
    """Create a stack purchase record. Returns the unique purchase_token."""
    token = secrets.token_urlsafe(32)
    await db.execute(
        """INSERT INTO stack_purchases (stack_id, buyer_email, stripe_session_id,
           total_amount_pence, discount_pence, purchase_token)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (stack_id, buyer_email, stripe_session_id, total_amount_pence, discount_pence, token))
    await db.commit()
    return token


async def get_stack_purchase_by_session(db, session_id: str):
    """Get a stack purchase by Stripe session ID."""
    cursor = await db.execute(
        """SELECT sp.*, s.title as stack_title, s.slug as stack_slug
           FROM stack_purchases sp JOIN stacks s ON sp.stack_id = s.id
           WHERE sp.stripe_session_id = ?""", (session_id,))
    return await cursor.fetchone()


async def get_stack_purchase_by_token(db, token: str):
    """Get a stack purchase by its purchase token."""
    cursor = await db.execute(
        """SELECT sp.*, s.title as stack_title, s.slug as stack_slug, s.cover_emoji
           FROM stack_purchases sp JOIN stacks s ON sp.stack_id = s.id
           WHERE sp.purchase_token = ?""", (token,))
    return await cursor.fetchone()


# ── Buyer Badges ────────────────────────────────────────────────────────

async def get_or_create_badge_token(db, user_id: int) -> str:
    """Get or create a badge token for a user."""
    cursor = await db.execute("SELECT badge_token FROM users WHERE id = ?", (user_id,))
    row = await cursor.fetchone()
    if row and row.get('badge_token'):
        return row['badge_token']
    token = secrets.token_urlsafe(16)
    await db.execute("UPDATE users SET badge_token = ? WHERE id = ?", (token, user_id))
    await db.commit()
    return token


async def get_user_by_badge_token(db, badge_token: str):
    """Get a user by their badge token."""
    cursor = await db.execute("SELECT id, name, email FROM users WHERE badge_token = ?", (badge_token,))
    return await cursor.fetchone()


async def get_buyer_tokens_saved_by_token(db, badge_token: str) -> int:
    """Calculate tokens saved for a buyer identified by badge token."""
    cursor = await db.execute(
        """SELECT c.slug, COUNT(*) as cnt
           FROM purchases p
           JOIN tools t ON p.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE p.buyer_email = (SELECT email FROM users WHERE badge_token = ?)
           GROUP BY c.slug""", (badge_token,))
    rows = await cursor.fetchall()
    total = 0
    for row in rows:
        cost = CATEGORY_TOKEN_COSTS.get(row['slug'], 50_000)
        total += cost * row['cnt']
    return total


# ── Discovery (Round 8) ─────────────────────────────────────────────────

async def get_all_tags_with_counts(db: aiosqlite.Connection, min_count: int = 1):
    """Get all unique tags across approved tools with their usage counts.
    Tags are stored as comma-separated strings in tools.tags.
    Returns list of dicts: [{'tag': 'api', 'slug': 'api', 'count': 5}, ...]
    """
    cursor = await db.execute(
        "SELECT tags FROM tools WHERE status = 'approved' AND tags != ''"
    )
    rows = await cursor.fetchall()
    counts: dict[str, int] = {}
    for row in rows:
        for raw_tag in row['tags'].split(','):
            tag = raw_tag.strip()
            if tag:
                key = tag.lower()
                counts[key] = counts.get(key, 0) + 1
    results = [
        {'tag': tag, 'slug': slugify(tag), 'count': count}
        for tag, count in counts.items()
        if count >= min_count
    ]
    results.sort(key=lambda x: x['count'], reverse=True)
    return results


async def get_tools_by_tag(db: aiosqlite.Connection, tag: str, *, page: int = 1, per_page: int = 12):
    """Get approved tools that have a specific tag. Returns (tools, total).
    Uses LIKE matching on the comma-separated tags field.
    """
    offset = (page - 1) * per_page
    tag_lower = tag.strip().lower()
    # Match: entire field is the tag, starts with tag+comma, ends with comma+tag, or has comma+tag+comma
    like_exact = tag_lower
    like_start = f'{tag_lower},%'
    like_end = f'%,{tag_lower}'
    like_mid = f'%,{tag_lower},%'

    sql = """SELECT t.*, c.name as category_name, c.slug as category_slug
             FROM tools t JOIN categories c ON t.category_id = c.id
             WHERE t.status = 'approved'
               AND (LOWER(TRIM(t.tags)) = ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ?)
             ORDER BY (t.is_verified * 100 + t.upvote_count) DESC, t.created_at DESC
             LIMIT ? OFFSET ?"""
    cursor = await db.execute(sql, (like_exact, like_start, like_end, like_mid, per_page, offset))
    rows = await cursor.fetchall()

    count_sql = """SELECT COUNT(*) as cnt FROM tools t
                   WHERE t.status = 'approved'
                     AND (LOWER(TRIM(t.tags)) = ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ?)"""
    count_cursor = await db.execute(count_sql, (like_exact, like_start, like_end, like_mid))
    total = (await count_cursor.fetchone())['cnt']
    return rows, total


async def explore_tools(db: aiosqlite.Connection, *, category_id: int = None,
                         tag: str = "", price_filter: str = "", sort: str = "trending",
                         verified_only: bool = False, ejectable_only: bool = False,
                         page: int = 1, per_page: int = 12):
    """Unified explore query with faceted filtering. Returns (tools, total)."""
    conditions = ["t.status = 'approved'"]
    params: list = []

    if category_id:
        conditions.append("t.category_id = ?")
        params.append(category_id)

    if tag:
        tag_lower = tag.strip().lower()
        conditions.append(
            "(LOWER(TRIM(t.tags)) = ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ?)"
        )
        params.extend([tag_lower, f'{tag_lower},%', f'%,{tag_lower}', f'%,{tag_lower},%'])

    if price_filter == "free":
        conditions.append("t.price_pence IS NULL")
    elif price_filter == "paid":
        conditions.append("t.price_pence > 0")

    if verified_only:
        conditions.append("t.is_verified = 1")

    if ejectable_only:
        conditions.append("t.is_ejectable = 1")

    where = " AND ".join(conditions)

    boost_prefix = "(CASE WHEN t.is_boosted = 1 AND t.boost_expires_at > datetime('now') THEN 0 ELSE 1 END), "
    order_by = {
        "trending": boost_prefix + "(t.is_verified * 100 + t.upvote_count) DESC, t.created_at DESC",
        "newest": boost_prefix + "t.created_at DESC",
        "name": boost_prefix + "t.name ASC",
        "upvotes": boost_prefix + "t.upvote_count DESC, t.created_at DESC",
    }.get(sort, boost_prefix + "(t.is_verified * 100 + t.upvote_count) DESC, t.created_at DESC")

    offset = (page - 1) * per_page

    sql = f"""SELECT t.*, c.name as category_name, c.slug as category_slug,
              EXISTS(SELECT 1 FROM maker_updates mu WHERE mu.tool_id = t.id AND mu.created_at >= datetime('now', '-14 days')) as has_changelog_14d
              FROM tools t JOIN categories c ON t.category_id = c.id
              WHERE {where}
              ORDER BY {order_by}
              LIMIT ? OFFSET ?"""
    cursor = await db.execute(sql, params + [per_page, offset])
    rows = await cursor.fetchall()

    count_sql = f"SELECT COUNT(*) as cnt FROM tools t WHERE {where}"
    count_cursor = await db.execute(count_sql, params)
    total = (await count_cursor.fetchone())['cnt']
    return rows, total


async def get_similar_tools(db: aiosqlite.Connection, tool_id: int, category_id: int,
                             tags: str, limit: int = 4):
    """Get similar tools based on shared tags and same category.
    Score: shared_tags * 3 + same_category * 2.
    Returns list of tool dicts with category info.
    """
    # Parse the input tags
    input_tags = {t.strip().lower() for t in tags.split(',') if t.strip()} if tags else set()

    # Query all approved tools except the current one
    cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved' AND t.id != ?""",
        (tool_id,),
    )
    candidates = await cursor.fetchall()

    scored = []
    for tool in candidates:
        score = 0
        # Same category bonus
        if tool['category_id'] == category_id:
            score += 2
        # Shared tags bonus
        if input_tags and tool.get('tags'):
            candidate_tags = {t.strip().lower() for t in tool['tags'].split(',') if t.strip()}
            shared = len(input_tags & candidate_tags)
            score += shared * 3
        if score > 0:
            scored.append((score, tool))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in scored[:limit]]


# ── Round 9: Retention & Engagement ──────────────────────────────────────

async def create_claim_token(db, tool_id: int, user_id: int) -> str:
    """Create a claim token for a user wanting to claim a tool. 24h expiry."""
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    await db.execute(
        "INSERT INTO claim_tokens (tool_id, user_id, token, expires_at) VALUES (?, ?, ?, ?)",
        (tool_id, user_id, token, expires_at.isoformat()))
    await db.commit()
    return token


async def verify_claim_token(db, token: str):
    """Verify a claim token. Returns (tool_id, user_id) or None.
    On success: marks token used, creates/links maker profile, updates tool."""
    cursor = await db.execute(
        "SELECT tool_id, user_id, expires_at, used FROM claim_tokens WHERE token = ?", (token,))
    row = await cursor.fetchone()
    if not row or row['used']:
        return None
    if datetime.fromisoformat(row['expires_at']) < datetime.utcnow():
        return None
    tool_id, user_id = row['tool_id'], row['user_id']
    # Get user info to create/link maker
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    maker_name = user.get('name', '') or user.get('email', '').split('@')[0]
    maker_id = await get_or_create_maker(db, maker_name, '')
    # Link tool to maker
    await db.execute("UPDATE tools SET maker_id = ? WHERE id = ? AND maker_id IS NULL", (maker_id, tool_id))
    # Link user to maker if not already
    if not user.get('maker_id'):
        await db.execute("UPDATE users SET maker_id = ?, role = 'maker' WHERE id = ?", (maker_id, user_id))
    # Mark token used
    await db.execute("UPDATE claim_tokens SET used = 1 WHERE token = ?", (token,))
    await db.commit()
    return (tool_id, user_id)


async def create_magic_claim_token(db, tool_id: int, days: int = 7) -> str:
    """Create a magic claim token for admin to share. 7-day expiry. No user required."""
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(days=days)).isoformat()
    await db.execute(
        "INSERT INTO magic_claim_tokens (tool_id, token, expires_at) VALUES (?, ?, ?)",
        (tool_id, token, expires_at))
    await db.commit()
    return token


async def get_magic_claim_token(db, token: str):
    """Look up a magic claim token. Returns dict with tool_id or None."""
    cursor = await db.execute(
        "SELECT id, tool_id, expires_at, used FROM magic_claim_tokens WHERE token = ?", (token,))
    row = await cursor.fetchone()
    if not row or row['used']:
        return None
    if datetime.fromisoformat(row['expires_at']) < datetime.utcnow():
        return None
    return dict(row)


async def use_magic_claim_token(db, token: str):
    """Mark a magic claim token as used."""
    await db.execute("UPDATE magic_claim_tokens SET used = 1 WHERE token = ?", (token,))
    await db.commit()


async def get_makers_in_category(db, category_id: int, exclude_tool_id: int = None):
    """Get all makers who have tools in a given category, with their emails.
    Returns list of dicts: {email, name, maker_id}"""
    exclude = f"AND t.id != {int(exclude_tool_id)}" if exclude_tool_id else ""
    cursor = await db.execute(f"""
        SELECT DISTINCT u.email, u.name, m.id as maker_id, m.name as maker_name
        FROM tools t
        JOIN makers m ON t.maker_id = m.id
        JOIN users u ON u.maker_id = m.id
        WHERE t.category_id = ? AND t.status = 'approved' {exclude}
    """, (category_id,))
    return await cursor.fetchall()


async def get_trending_scored(db, limit: int = 20, days: int = 7):
    """Get tools ranked by time-decayed heat score.
    Score = (upvotes + views_7d) / (hours_since_created ^ 1.5)"""
    cursor = await db.execute(f"""
        SELECT t.*, c.name as category_name, c.slug as category_slug,
               COALESCE(v.view_count, 0) as views_7d,
               (t.upvote_count + COALESCE(v.view_count, 0)) * 1.0 /
               MAX(1.0, POWER(MAX(1, (julianday('now') - julianday(t.created_at)) * 24), 1.5)) as heat_score,
               EXISTS(SELECT 1 FROM maker_updates mu WHERE mu.tool_id = t.id AND mu.created_at >= datetime('now', '-14 days')) as has_changelog_14d
        FROM tools t
        JOIN categories c ON t.category_id = c.id
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as view_count
            FROM tool_views
            WHERE viewed_at >= datetime('now', '-{days} days')
            GROUP BY tool_id
        ) v ON v.tool_id = t.id
        WHERE t.status = 'approved'
        ORDER BY heat_score DESC
        LIMIT ?
    """, (limit,))
    results = [dict(r) for r in await cursor.fetchall()]
    results.sort(key=lambda r: (0 if r.get('is_boosted') and r.get('boost_expires_at', '') > datetime.utcnow().isoformat() else 1))
    return results


async def get_maker_funnel(db, maker_id: int, days: int = 7):
    """Get funnel analytics for a maker's tools over the last N days.
    Returns list of dicts: {tool_name, tool_slug, views, wishlist_saves, upvotes}"""
    cursor = await db.execute(f"""
        SELECT t.id, t.name as tool_name, t.slug as tool_slug,
               t.upvote_count as upvotes,
               COALESCE(v.view_count, 0) as views,
               COALESCE(w.save_count, 0) as wishlist_saves
        FROM tools t
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as view_count
            FROM tool_views
            WHERE viewed_at >= datetime('now', '-{days} days')
            GROUP BY tool_id
        ) v ON v.tool_id = t.id
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as save_count
            FROM wishlists
            GROUP BY tool_id
        ) w ON w.tool_id = t.id
        WHERE t.maker_id = ?
        ORDER BY views DESC
    """, (maker_id,))
    return await cursor.fetchall()


async def get_wishlist_users_for_tool(db, tool_id: int):
    """Get all users who wishlisted a specific tool. Returns list of {email, name, user_id}."""
    cursor = await db.execute("""
        SELECT u.id as user_id, u.email, u.name
        FROM wishlists w
        JOIN users u ON w.user_id = u.id
        WHERE w.tool_id = ?
    """, (tool_id,))
    return await cursor.fetchall()


async def get_recent_activity(db, limit: int = 10, days: int = 7):
    """Get recent marketplace activity for the homepage ticker.
    Returns list of dicts: {type, message, created_at}"""
    activities = []
    # Recent tool approvals
    cursor = await db.execute(f"""
        SELECT t.name, t.created_at FROM tools t
        WHERE t.status = 'approved' AND t.created_at >= datetime('now', '-{days} days')
        ORDER BY t.created_at DESC LIMIT 5
    """)
    for row in await cursor.fetchall():
        activities.append({
            'type': 'launch',
            'message': f"{row['name']} just launched",
            'created_at': row['created_at']
        })
    # Recent upvotes
    cursor2 = await db.execute(f"""
        SELECT t.name, u.created_at FROM upvotes u
        JOIN tools t ON u.tool_id = t.id
        WHERE u.created_at >= datetime('now', '-{days} days')
        ORDER BY u.created_at DESC LIMIT 5
    """)
    for row in await cursor2.fetchall():
        activities.append({
            'type': 'upvote',
            'message': f"Someone upvoted {row['name']}",
            'created_at': row['created_at']
        })
    # Recent maker updates
    cursor3 = await db.execute(f"""
        SELECT mu.title, m.name as maker_name, mu.created_at
        FROM maker_updates mu JOIN makers m ON mu.maker_id = m.id
        WHERE mu.created_at >= datetime('now', '-{days} days')
        ORDER BY mu.created_at DESC LIMIT 5
    """)
    for row in await cursor3.fetchall():
        activities.append({
            'type': 'update',
            'message': f"{row['maker_name']} posted: {row['title']}" if row['title'] else f"{row['maker_name']} shipped an update",
            'created_at': row['created_at']
        })
    # Sort all by time, take top N
    activities.sort(key=lambda x: x['created_at'], reverse=True)
    return activities[:limit]


async def has_recent_changelog(db, tool_id: int, days: int = 14) -> bool:
    """Check if a tool has had a changelog/update in the last N days."""
    cursor = await db.execute(
        "SELECT 1 FROM maker_updates WHERE tool_id = ? AND created_at >= datetime('now', ?) LIMIT 1",
        (tool_id, f'-{days} days'))
    return await cursor.fetchone() is not None


async def get_tools_for_rss(db, *, category_slug: str = None, tag: str = None, limit: int = 20):
    """Get tools for RSS feed generation with full details."""
    conditions = ["t.status = 'approved'"]
    params = []
    if category_slug:
        conditions.append("c.slug = ?")
        params.append(category_slug)
    if tag:
        tag_lower = tag.lower().strip()
        conditions.append("(LOWER(t.tags) = ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ? OR LOWER(t.tags) LIKE ?)")
        params.extend([tag_lower, f'{tag_lower},%', f'%,{tag_lower}', f'%,{tag_lower},%'])
    where = " AND ".join(conditions)
    cursor = await db.execute(f"""
        SELECT t.*, c.name as category_name, c.slug as category_slug
        FROM tools t JOIN categories c ON t.category_id = c.id
        WHERE {where}
        ORDER BY t.created_at DESC LIMIT ?
    """, params + [limit])
    return await cursor.fetchall()


async def get_all_subscribers(db):
    """Get all subscriber emails."""
    cursor = await db.execute("SELECT email FROM subscribers ORDER BY created_at DESC")
    return await cursor.fetchall()


# ── Round 10: User Stacks ─────────────────────────────────────────────

async def create_user_stack(db, user_id: int, title: str = 'My Stack', description: str = '') -> int:
    """Create a user stack. One per user (UNIQUE constraint)."""
    cursor = await db.execute(
        "INSERT OR IGNORE INTO user_stacks (user_id, title, description) VALUES (?, ?, ?)",
        (user_id, title.strip() or 'My Stack', description.strip()))
    await db.commit()
    if cursor.lastrowid:
        return cursor.lastrowid
    # Already exists — return existing
    row = await (await db.execute("SELECT id FROM user_stacks WHERE user_id = ?", (user_id,))).fetchone()
    return row['id'] if row else 0


async def get_user_stack(db, user_id: int):
    """Get a user's stack with all tools."""
    cursor = await db.execute("SELECT * FROM user_stacks WHERE user_id = ?", (user_id,))
    stack = await cursor.fetchone()
    if not stack:
        return None, []
    tools_cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug,
                  ust.note, ust.position
           FROM user_stack_tools ust
           JOIN tools t ON ust.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE ust.stack_id = ? AND t.status = 'approved'
           ORDER BY ust.position ASC, t.name ASC""",
        (stack['id'],))
    tools = await tools_cursor.fetchall()
    return stack, tools


async def get_user_stack_by_username(db, username: str):
    """Get a public user stack by username (user.name field). Returns (stack, tools, user)."""
    cursor = await db.execute(
        """SELECT us.*, u.name as user_name, u.id as uid
           FROM user_stacks us
           JOIN users u ON us.user_id = u.id
           WHERE LOWER(REPLACE(u.name, ' ', '-')) = LOWER(?) AND us.is_public = 1""",
        (username,))
    stack = await cursor.fetchone()
    if not stack:
        return None, [], None
    tools_cursor = await db.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug,
                  ust.note, ust.position
           FROM user_stack_tools ust
           JOIN tools t ON ust.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE ust.stack_id = ? AND t.status = 'approved'
           ORDER BY ust.position ASC, t.name ASC""",
        (stack['id'],))
    tools = await tools_cursor.fetchall()
    return stack, tools, stack


async def add_tool_to_user_stack(db, stack_id: int, tool_id: int, note: str = '', position: int = 0):
    """Add a tool to a user's stack."""
    try:
        await db.execute(
            "INSERT INTO user_stack_tools (stack_id, tool_id, note, position) VALUES (?, ?, ?, ?)",
            (stack_id, tool_id, note.strip(), position))
        await db.commit()
        return True
    except Exception:
        return False


async def remove_tool_from_user_stack(db, stack_id: int, tool_id: int):
    """Remove a tool from a user's stack."""
    await db.execute(
        "DELETE FROM user_stack_tools WHERE stack_id = ? AND tool_id = ?",
        (stack_id, tool_id))
    await db.commit()


async def update_user_stack(db, stack_id: int, **fields):
    """Update user stack settings (title, description, is_public)."""
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [stack_id]
    await db.execute(f"UPDATE user_stacks SET {set_clause} WHERE id = ?", values)
    await db.commit()


async def get_public_stacks(db, limit: int = 20):
    """Get public user stacks for the community gallery."""
    cursor = await db.execute(
        """SELECT us.*, u.name as user_name,
                  COUNT(ust.tool_id) as tool_count
           FROM user_stacks us
           JOIN users u ON us.user_id = u.id
           LEFT JOIN user_stack_tools ust ON ust.stack_id = us.id
           WHERE us.is_public = 1
           GROUP BY us.id
           HAVING tool_count > 0
           ORDER BY tool_count DESC, us.created_at DESC
           LIMIT ?""",
        (limit,))
    return await cursor.fetchall()


async def get_stack_preview_tools(db, stack_id: int, limit: int = 3):
    """Get first N tools from a user stack for preview cards."""
    cursor = await db.execute(
        """SELECT t.name, t.slug, c.icon as category_icon
           FROM user_stack_tools ust
           JOIN tools t ON ust.tool_id = t.id
           JOIN categories c ON t.category_id = c.id
           WHERE ust.stack_id = ? AND t.status = 'approved'
           ORDER BY ust.position ASC LIMIT ?""",
        (stack_id, limit))
    return await cursor.fetchall()


# ── Round 10: Search Logs & Live Wire ─────────────────────────────────

async def log_search(db, query: str, source: str = 'web', result_count: int = 0,
                     top_result_slug: str = None, top_result_name: str = None):
    """Log a search query for the Live Wire feed and maker analytics."""
    if not query or not query.strip():
        return
    await db.execute(
        """INSERT INTO search_logs (query, source, result_count, top_result_slug, top_result_name)
           VALUES (?, ?, ?, ?, ?)""",
        (query.strip()[:200], source, result_count, top_result_slug, top_result_name))
    await db.commit()


async def get_recent_searches(db, limit: int = 30):
    """Get recent search queries for the Live Wire feed."""
    cursor = await db.execute(
        """SELECT * FROM search_logs
           ORDER BY created_at DESC LIMIT ?""",
        (limit,))
    return await cursor.fetchall()


async def get_search_stats(db):
    """Get search statistics for the Live Wire dashboard."""
    cursor = await db.execute("""
        SELECT
            (SELECT COUNT(*) FROM search_logs WHERE created_at >= datetime('now', '-1 day')) as today,
            (SELECT COUNT(*) FROM search_logs WHERE created_at >= datetime('now', '-7 days')) as this_week,
            (SELECT COUNT(*) FROM search_logs) as all_time
    """)
    stats = await cursor.fetchone()
    # Top query this week
    top_cursor = await db.execute("""
        SELECT query, COUNT(*) as cnt FROM search_logs
        WHERE created_at >= datetime('now', '-7 days')
        GROUP BY LOWER(query) ORDER BY cnt DESC LIMIT 1
    """)
    top = await top_cursor.fetchone()
    return {
        'today': stats['today'],
        'this_week': stats['this_week'],
        'all_time': stats['all_time'],
        'top_query': top['query'] if top else None,
        'top_query_count': top['cnt'] if top else 0,
    }


async def get_search_terms_for_tool(db, tool_slug: str, limit: int = 10):
    """Get search queries that led to a specific tool being the top result."""
    cursor = await db.execute(
        """SELECT query, COUNT(*) as count, MAX(created_at) as last_seen
           FROM search_logs WHERE top_result_slug = ?
           GROUP BY LOWER(query) ORDER BY count DESC LIMIT ?""",
        (tool_slug, limit))
    return await cursor.fetchall()


# ── Round 10: Milestones ──────────────────────────────────────────────

MILESTONE_THRESHOLDS = {
    'first-tool': {'description': 'Listed your first tool on IndieStack', 'emoji': '🎉'},
    '100-views': {'description': 'Your tool hit 100 views', 'emoji': '👀'},
    '10-upvotes': {'description': '10 developers upvoted your tool', 'emoji': '🔥'},
    'first-review': {'description': 'Got your first review', 'emoji': '⭐'},
    'launch-ready': {'description': '100% Launch Ready', 'emoji': '🚀'},
    '50-wishlists': {'description': '50 developers wishlisted your tool', 'emoji': '💾'},
}


async def check_milestones(db, user_id: int, tool_id: int = None):
    """Check and award any newly achieved milestones. Returns list of newly awarded types."""
    new_milestones = []

    # first-tool: user has at least 1 approved tool
    cursor = await db.execute(
        """SELECT COUNT(*) as cnt FROM tools t
           JOIN makers m ON t.maker_id = m.id
           JOIN users u ON u.maker_id = m.id
           WHERE u.id = ? AND t.status = 'approved'""", (user_id,))
    if (await cursor.fetchone())['cnt'] >= 1:
        if await _award_milestone(db, user_id, tool_id, 'first-tool'):
            new_milestones.append('first-tool')

    if tool_id:
        # 100-views
        views = await get_tool_view_count(db, tool_id, days=9999)
        if views >= 100:
            if await _award_milestone(db, user_id, tool_id, '100-views'):
                new_milestones.append('100-views')

        # 10-upvotes
        tool = await get_tool_by_id(db, tool_id)
        if tool and tool.get('upvote_count', 0) >= 10:
            if await _award_milestone(db, user_id, tool_id, '10-upvotes'):
                new_milestones.append('10-upvotes')

        # first-review
        review_cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM reviews WHERE tool_id = ?", (tool_id,))
        if (await review_cursor.fetchone())['cnt'] >= 1:
            if await _award_milestone(db, user_id, tool_id, 'first-review'):
                new_milestones.append('first-review')

        # 50-wishlists
        wl_cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM wishlists WHERE tool_id = ?", (tool_id,))
        if (await wl_cursor.fetchone())['cnt'] >= 50:
            if await _award_milestone(db, user_id, tool_id, '50-wishlists'):
                new_milestones.append('50-wishlists')

    return new_milestones


async def _award_milestone(db, user_id: int, tool_id: int, milestone_type: str) -> bool:
    """Award a milestone if not already achieved. Returns True if newly awarded."""
    try:
        await db.execute(
            "INSERT INTO milestones (user_id, tool_id, milestone_type) VALUES (?, ?, ?)",
            (user_id, tool_id, milestone_type))
        await db.commit()
        return True
    except Exception:
        return False  # Already exists (UNIQUE constraint)


async def get_user_milestones(db, user_id: int):
    """Get all milestones for a user."""
    cursor = await db.execute(
        """SELECT ml.*, t.name as tool_name, t.slug as tool_slug
           FROM milestones ml
           LEFT JOIN tools t ON ml.tool_id = t.id
           WHERE ml.user_id = ?
           ORDER BY ml.achieved_at DESC""",
        (user_id,))
    return await cursor.fetchall()


async def get_unshared_milestones(db, user_id: int):
    """Get milestones that haven't been shared yet (for celebration prompts)."""
    cursor = await db.execute(
        """SELECT ml.*, t.name as tool_name, t.slug as tool_slug
           FROM milestones ml
           LEFT JOIN tools t ON ml.tool_id = t.id
           WHERE ml.user_id = ? AND ml.shared = 0
           ORDER BY ml.achieved_at DESC""",
        (user_id,))
    return await cursor.fetchall()


async def mark_milestone_shared(db, milestone_id: int):
    """Mark a milestone as shared."""
    await db.execute("UPDATE milestones SET shared = 1 WHERE id = ?", (milestone_id,))
    await db.commit()


async def get_launch_readiness(db, maker_id: int) -> dict:
    """Calculate launch readiness score for a maker's tools.
    Returns dict with 'score' (0-100), 'total' items, 'completed' items, and 'items' checklist."""
    maker = await get_maker_by_id(db, maker_id)
    if not maker:
        return {'score': 0, 'total': 8, 'completed': 0, 'items': []}

    # Get maker's first approved tool (primary)
    cursor = await db.execute(
        """SELECT t.* FROM tools t WHERE t.maker_id = ? AND t.status = 'approved'
           ORDER BY t.created_at ASC LIMIT 1""", (maker_id,))
    tool = await cursor.fetchone()

    tool_edit_url = f'/dashboard/tools/{tool["id"]}/edit' if tool else '/submit'

    items = []
    # 1. Tool has tags
    items.append({
        'label': 'Add tags to your tool',
        'done': bool(tool and tool.get('tags', '').strip()),
        'icon': '🏷️',
        'action': 'link',
        'url': tool_edit_url,
    })
    # 2. Tool has replaces field
    items.append({
        'label': 'List competitors you replace',
        'done': bool(tool and tool.get('replaces', '').strip()),
        'icon': '⚔️',
        'action': 'form',
        'field': 'replaces',
        'input_type': 'text',
        'placeholder': 'e.g. Slack, Teams, Notion',
        'current': tool.get('replaces', '') if tool else '',
    })
    # 3. Maker has bio
    items.append({
        'label': 'Write your maker bio',
        'done': bool(maker.get('bio', '').strip()),
        'icon': '📝',
        'action': 'form',
        'field': 'bio',
        'input_type': 'textarea',
        'placeholder': 'Tell developers about yourself...',
        'current': maker.get('bio', '') or '',
    })
    # 4. Maker has avatar
    items.append({
        'label': 'Upload an avatar',
        'done': bool(maker.get('avatar_url', '').strip()),
        'icon': '🖼️',
        'action': 'form',
        'field': 'avatar_url',
        'input_type': 'url',
        'placeholder': 'https://example.com/avatar.jpg',
        'current': maker.get('avatar_url', '') or '',
    })
    # 5. Maker has URL
    items.append({
        'label': 'Add your website URL',
        'done': bool(maker.get('url', '').strip()),
        'icon': '🔗',
        'action': 'form',
        'field': 'url',
        'input_type': 'url',
        'placeholder': 'https://yoursite.com',
        'current': maker.get('url', '') or '',
    })
    # 6. At least 1 changelog
    has_changelog = False
    if tool:
        cl_cursor = await db.execute(
            "SELECT 1 FROM maker_updates WHERE tool_id = ? LIMIT 1", (tool['id'],))
        has_changelog = await cl_cursor.fetchone() is not None
    items.append({
        'label': 'Post your first changelog',
        'done': has_changelog,
        'icon': '📋',
        'action': 'link',
        'url': '/dashboard/updates' if tool else '/submit',
    })
    # 7. Tool has github_url (via the url field or a github link)
    has_github = bool(tool and 'github.com' in (tool.get('url', '') or ''))
    items.append({
        'label': 'Link your GitHub repo',
        'done': has_github,
        'icon': '🐙',
        'action': 'link',
        'url': tool_edit_url,
    })

    completed = sum(1 for item in items if item['done'])
    score = round(completed / len(items) * 100)

    return {
        'score': score,
        'total': len(items),
        'completed': completed,
        'items': items,
        'tool_id': tool['id'] if tool else None,
    }

#!/usr/bin/env python3
"""Seed social proof data into IndieStack: views, wishlists, reviews, badges, tags, GovLink.

Usage:
    python3 seed_social_proof.py

Idempotent — safe to run multiple times. Uses INSERT OR IGNORE on unique constraints.
"""

import hashlib
import os
import random
import re
import sqlite3
from datetime import datetime, timedelta

# Match the DB path from db.py / seed_tools.py
DB_PATH = os.environ.get("INDIESTACK_DB_PATH", "/data/indiestack.db")
if not os.path.exists(os.path.dirname(DB_PATH) or "/data"):
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "indiestack.db")

UPVOTE_SALT = os.environ.get("INDIESTACK_UPVOTE_SALT", "indiestack-default-salt-change-me")

# Seed for reproducibility — same "random" data every run
random.seed(42)


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


# ── Tag Cleanup ──────────────────────────────────────────────────────────────

TAG_MERGES = {
    "newsletters": "newsletter",
    "developers": "developer",
    "customers": "customer",
    "apis": "api",
    "components": "component",
    "monitor": "monitoring",
}


def cleanup_tags(conn):
    """Normalize near-duplicate tags in tools.tags field."""
    cursor = conn.execute("SELECT id, tags FROM tools WHERE tags != ''")
    rows = cursor.fetchall()
    updated = 0
    for tool_id, tags_str in rows:
        tags = [t.strip() for t in tags_str.split(",") if t.strip()]
        new_tags = []
        changed = False
        for tag in tags:
            if tag in TAG_MERGES:
                new_tags.append(TAG_MERGES[tag])
                changed = True
            else:
                new_tags.append(tag)
        # Deduplicate after merging
        seen = set()
        deduped = []
        for t in new_tags:
            if t not in seen:
                seen.add(t)
                deduped.append(t)
        if changed or len(deduped) != len(new_tags):
            conn.execute("UPDATE tools SET tags = ? WHERE id = ?", (",".join(deduped), tool_id))
            updated += 1
    conn.commit()
    print(f"  Tags: normalized {updated} tools")


# ── Duplicate Removal ────────────────────────────────────────────────────────

def remove_duplicates(conn):
    """Remove duplicate tool entries (e.g. poethepoet listed twice)."""
    cursor = conn.execute("""
        SELECT name, COUNT(*) as cnt FROM tools
        GROUP BY LOWER(name) HAVING cnt > 1
    """)
    dupes = cursor.fetchall()
    removed = 0
    for name, cnt in dupes:
        # Keep the one with highest upvote_count, delete others
        rows = conn.execute(
            "SELECT id, upvote_count FROM tools WHERE LOWER(name) = LOWER(?) ORDER BY upvote_count DESC",
            (name,)
        ).fetchall()
        for row in rows[1:]:  # skip the first (keeper)
            tool_id = row[0]
            # Delete all foreign key references first
            for table in ["upvotes", "tool_views", "wishlists", "reviews"]:
                conn.execute(f"DELETE FROM {table} WHERE tool_id = ?", (tool_id,))
            conn.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
            removed += 1
    conn.commit()
    if removed:
        # Rebuild FTS after deletions
        try:
            conn.execute("INSERT INTO tools_fts(tools_fts) VALUES('rebuild')")
            conn.commit()
        except Exception:
            pass
    print(f"  Duplicates: removed {removed} duplicate tools")


# ── Badges ───────────────────────────────────────────────────────────────────

VERIFIED_SLUGS = [
    "plausible-analytics", "gumroad", "railway", "buffer", "canny", "better-stack",
]

EJECTABLE_SLUGS = [
    "plausible-analytics", "fider", "buttondown", "typefully", "nolt",
    "fathom-analytics", "simple-analytics", "checkly",
]


SEED_MAKERS = [
    ("uku-taht", "Uku Taht", "https://twitter.com/ukutaht", "Creator of Plausible Analytics.", "solo"),
    ("jack-ellis", "Jack Ellis", "https://twitter.com/JackEllis", "Co-founder of Fathom Analytics.", "small_team"),
    ("adriaan-van-rossum", "Adriaan van Rossum", "", "Founder of Simple Analytics.", "solo"),
    ("justin-duke", "Justin Duke", "https://twitter.com/justinmduke", "Creator of Buttondown.", "solo"),
    ("nathan-barry", "Nathan Barry", "https://twitter.com/nathanbarry", "Founder of Kit.", "small_team"),
    ("fabrizio-rinaldi", "Fabrizio Rinaldi", "", "Co-founder of Mailbrew.", "small_team"),
    ("aj", "AJ", "https://twitter.com/ajlkn", "Creator of Carrd.", "solo"),
    ("traf", "Traf", "", "Creator of Super.so.", "solo"),
    ("kevin-conti", "Kevin Conti", "", "Co-founder of Typedream.", "solo"),
    ("sahil-lavingia", "Sahil Lavingia", "https://twitter.com/shl", "Founder of Gumroad.", "small_team"),
    ("jj-lee", "JJ Lee", "", "Co-founder of Lemon Squeezy.", "small_team"),
    ("christian-owens", "Christian Owens", "", "Co-founder of Paddle.", "small_team"),
    ("jake-cooper", "Jake Cooper", "", "Co-founder of Railway.", "small_team"),
    ("anurag-goel", "Anurag Goel", "", "Founder of Render.", "small_team"),
    ("sam-lambert", "Sam Lambert", "", "CEO of PlanetScale.", "small_team"),
    ("fabrizio-rinaldi-typefully", "Fabrizio Rinaldi", "", "Co-founder of Typefully.", "small_team"),
    ("yannick-veys", "Yannick Veys", "", "Co-founder of Hypefury.", "small_team"),
    ("joel-gascoigne", "Joel Gascoigne", "https://twitter.com/joelgascoigne", "Founder of Buffer.", "small_team"),
    ("joshua-beckman", "Joshua Beckman", "", "Creator of Pika.", "solo"),
    ("mehdi-merah", "Mehdi Merah", "", "Creator of Screely.", "solo"),
    ("devin-jacoviello", "Devin Jacoviello", "", "Creator of Shots.so.", "solo"),
    ("sarah-cannon", "Sarah Cannon", "", "Co-founder of Canny.", "small_team"),
    ("fred-rivett", "Fred Rivett", "", "Creator of Nolt.", "solo"),
    ("goenning", "Guilherme Oenning", "", "Creator of Fider.", "solo"),
    ("hannes-lenke", "Hannes Lenke", "", "Co-founder of Checkly.", "small_team"),
    ("ralph-chua", "Ralph Chua", "", "Co-founder of Better Stack.", "small_team"),
]


def ensure_seed_makers(conn):
    """Insert seed makers if they don't exist."""
    created = 0
    for slug, name, url, bio, indie_status in SEED_MAKERS:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO makers (slug, name, url, bio, indie_status) VALUES (?, ?, ?, ?, ?)",
                (slug, name, url, bio, indie_status)
            )
            created += 1
        except Exception:
            pass
    conn.commit()
    print(f"  Seed makers: ensured {created} makers exist")


def backfill_maker_ids(conn):
    """Link seeded tools to their makers (fixes INSERT OR IGNORE skip issue)."""
    # Map tool slugs to maker slugs (from seed_tools.py TOOLS data)
    TOOL_MAKER_MAP = {
        "plausible-analytics": "uku-taht",
        "fathom-analytics": "jack-ellis",
        "simple-analytics": "adriaan-van-rossum",
        "buttondown": "justin-duke",
        "kit": "nathan-barry",
        "mailbrew": "fabrizio-rinaldi",
        "carrd": "aj",
        "super-so": "traf",
        "typedream": "kevin-conti",
        "gumroad": "sahil-lavingia",
        "lemon-squeezy": "jj-lee",
        "paddle": "christian-owens",
        "railway": "jake-cooper",
        "render": "anurag-goel",
        "planetscale": "sam-lambert",
        "typefully": "fabrizio-rinaldi-typefully",
        "hypefury": "yannick-veys",
        "buffer": "joel-gascoigne",
        "pika": "joshua-beckman",
        "screely": "mehdi-merah",
        "shots-so": "devin-jacoviello",
        "canny": "sarah-cannon",
        "nolt": "fred-rivett",
        "fider": "goenning",
        "checkly": "hannes-lenke",
        "better-stack": "ralph-chua",
        "govlink": "patrick-amey-jones",
    }
    updated = 0
    for tool_slug, maker_slug in TOOL_MAKER_MAP.items():
        maker_row = conn.execute("SELECT id FROM makers WHERE slug = ?", (maker_slug,)).fetchone()
        if not maker_row:
            continue
        cur = conn.execute(
            "UPDATE tools SET maker_id = ? WHERE slug = ? AND (maker_id IS NULL OR maker_id != ?)",
            (maker_row[0], tool_slug, maker_row[0])
        )
        updated += cur.rowcount
    conn.commit()
    print(f"  Maker IDs: backfilled {updated} tools with maker links")


def set_badges(conn):
    """Mark tools as verified and/or ejectable."""
    v = 0
    for slug in VERIFIED_SLUGS:
        cur = conn.execute(
            "UPDATE tools SET is_verified = 1, verified_at = CURRENT_TIMESTAMP WHERE slug = ? AND is_verified = 0",
            (slug,)
        )
        v += cur.rowcount
    e = 0
    for slug in EJECTABLE_SLUGS:
        cur = conn.execute(
            "UPDATE tools SET is_ejectable = 1 WHERE slug = ? AND is_ejectable = 0",
            (slug,)
        )
        e += cur.rowcount
    conn.commit()
    print(f"  Badges: set {v} verified, {e} ejectable")


# ── Upvotes for bot-scraped tools ────────────────────────────────────────────

# Slugs of the 26 originally seeded tools (already have upvote counts)
SEEDED_SLUGS = {
    "plausible-analytics", "fathom-analytics", "simple-analytics",
    "buttondown", "kit", "mailbrew", "carrd", "super-so", "typedream",
    "gumroad", "lemon-squeezy", "paddle", "railway", "render", "planetscale",
    "typefully", "hypefury", "buffer", "pika", "screely", "shots-so",
    "canny", "nolt", "fider", "checkly", "better-stack",
}


def seed_upvotes(conn):
    """Set realistic upvote counts for bot-scraped tools that have 0."""
    cursor = conn.execute(
        "SELECT id, slug, upvote_count FROM tools WHERE status = 'approved'"
    )
    tools = cursor.fetchall()
    updated = 0
    for tool_id, slug, current_count in tools:
        if slug not in SEEDED_SLUGS and (current_count is None or current_count == 0):
            count = random.randint(5, 45)
            conn.execute("UPDATE tools SET upvote_count = ? WHERE id = ?", (count, tool_id))
            updated += 1
    conn.commit()
    print(f"  Upvotes: set counts for {updated} bot-scraped tools")


# ── Tool Views ───────────────────────────────────────────────────────────────

def seed_tool_views(conn):
    """Insert realistic tool_views rows for the last 14 days."""
    # Check if we already seeded views
    existing = conn.execute("SELECT COUNT(*) FROM tool_views").fetchone()[0]
    if existing > 500:
        print(f"  Views: already have {existing} rows, skipping")
        return

    cursor = conn.execute(
        "SELECT id, slug, upvote_count FROM tools WHERE status = 'approved'"
    )
    tools = cursor.fetchall()
    now = datetime.utcnow()
    total = 0

    for tool_id, slug, upvotes in tools:
        # More popular tools get more views
        upvotes = upvotes or 0
        if upvotes > 100:
            view_count = random.randint(80, 200)
        elif upvotes > 30:
            view_count = random.randint(20, 60)
        else:
            view_count = random.randint(5, 20)

        for i in range(view_count):
            # Random time in last 14 days
            hours_ago = random.uniform(0, 14 * 24)
            viewed_at = now - timedelta(hours=hours_ago)
            # Fake IP hash
            ip_hash = hashlib.sha256(f"fake-viewer-{tool_id}-{i}".encode()).hexdigest()[:16]
            conn.execute(
                "INSERT INTO tool_views (tool_id, ip_hash, viewed_at) VALUES (?, ?, ?)",
                (tool_id, ip_hash, viewed_at.strftime("%Y-%m-%d %H:%M:%S"))
            )
            total += 1

    conn.commit()
    print(f"  Views: inserted {total} tool view rows")


# ── Test Users ───────────────────────────────────────────────────────────────

TEST_USERS = [
    ("test1@indiestack.dev", "Alex Chen", "testuser1"),
    ("test2@indiestack.dev", "Jamie Rivera", "testuser2"),
    ("test3@indiestack.dev", "Sam Patel", "testuser3"),
    ("test4@indiestack.dev", "Morgan Lee", "testuser4"),
    ("test5@indiestack.dev", "Taylor Kim", "testuser5"),
]


def seed_test_users(conn):
    """Create internal test user accounts."""
    # Simple bcrypt-style hash placeholder — these accounts can't actually log in
    # because the hash won't match any real bcrypt verification
    fake_hash = "$2b$12$seedseedseeddatadatadatOaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    created = 0
    for email, name, _ in TEST_USERS:
        try:
            conn.execute(
                "INSERT OR IGNORE INTO users (email, password_hash, name, role, email_verified) VALUES (?, ?, ?, 'buyer', 1)",
                (email, fake_hash, name)
            )
            created += 1
        except Exception:
            pass
    conn.commit()
    print(f"  Users: {created} test accounts created/verified")


# ── Wishlists ────────────────────────────────────────────────────────────────

def seed_wishlists(conn):
    """Create wishlist entries from test users."""
    existing = conn.execute("SELECT COUNT(*) FROM wishlists").fetchone()[0]
    if existing > 20:
        print(f"  Wishlists: already have {existing} entries, skipping")
        return

    # Get test user IDs
    user_ids = []
    for email, _, _ in TEST_USERS:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            user_ids.append(row[0])

    if not user_ids:
        print("  Wishlists: no test users found, skipping")
        return

    # Get all approved tool IDs
    tool_ids = [r[0] for r in conn.execute(
        "SELECT id FROM tools WHERE status = 'approved'"
    ).fetchall()]

    total = 0
    now = datetime.utcnow()
    for user_id in user_ids:
        # Each user wishlists 5-15 random tools
        count = random.randint(5, min(15, len(tool_ids)))
        chosen = random.sample(tool_ids, count)
        for tool_id in chosen:
            days_ago = random.uniform(0, 14)
            created_at = now - timedelta(days=days_ago)
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO wishlists (user_id, tool_id, created_at) VALUES (?, ?, ?)",
                    (user_id, tool_id, created_at.strftime("%Y-%m-%d %H:%M:%S"))
                )
                total += 1
            except Exception:
                pass
    conn.commit()
    print(f"  Wishlists: inserted {total} entries")


# ── Reviews ──────────────────────────────────────────────────────────────────

REVIEWS = [
    # (tool_slug, rating, title, body)
    ("plausible-analytics", 5, "Best GA alternative", "Switched from Google Analytics 6 months ago. Never looked back. The dashboard is clean and tells me exactly what I need."),
    ("plausible-analytics", 4, "Great but missing a few things", "Love the privacy focus and simplicity. Would be nice to have more advanced funnel tracking but overall excellent."),
    ("fathom-analytics", 5, "Privacy + simplicity", "Set it up in 5 minutes, forgot about it, and now I have clean data without cookie banners. Exactly what I wanted."),
    ("fathom-analytics", 4, "Solid choice for privacy", "Reliable, fast, and respects my visitors. A bit pricey compared to Plausible but the dashboard is lovely."),
    ("gumroad", 5, "Just works", "Sold my first ebook through Gumroad. Took 10 minutes to set up. The fee is worth not dealing with Stripe directly."),
    ("gumroad", 4, "Good for getting started", "Perfect for indie makers who don't want to deal with Stripe complexity. Wish the fee was a bit lower though."),
    ("railway", 5, "Heroku replacement done right", "Migrated 3 apps from Heroku in an afternoon. Deploy from GitHub, scale when needed. Railway just gets it."),
    ("railway", 4, "Fast deploys, fair pricing", "Love the GitHub integration and the speed of deploys. Free tier is generous enough for side projects."),
    ("carrd", 5, "The landing page king", "Built 4 landing pages on Carrd. At $19/year it's absurdly good value. Simple, fast, looks professional."),
    ("buffer", 4, "Reliable social scheduling", "Been using Buffer for 2 years. It's not flashy but it works every single time. Scheduling across platforms is painless."),
    ("buttondown", 5, "Newsletter simplicity", "Moved from Mailchimp to Buttondown and never looked back. Markdown support, clean UI, fair pricing."),
    ("lemon-squeezy", 5, "MoR is the future", "Lemon Squeezy handles taxes so I don't have to think about VAT compliance. Worth every penny of the fee."),
    ("canny", 4, "Great feedback tool", "Customer support is responsive and the roadmap voting feature saved us a lot of guesswork about what to build next."),
    ("render", 4, "Solid Heroku alternative", "Good developer experience. Deploys are fast, the dashboard is clean. Free tier is genuinely useful for prototypes."),
    ("typefully", 5, "Twitter growth tool", "Typefully helped me grow from 500 to 5k followers. The AI suggestions are surprisingly good and scheduling is effortless."),
    ("checkly", 4, "Monitoring done right", "Playwright-based synthetic monitoring is brilliant. Caught 3 production issues before customers noticed."),
    ("better-stack", 5, "Beautiful uptime monitoring", "The status pages look incredible. Setup took minutes and the alerting is reliable. Replaced Pingdom and PagerDuty."),
    ("planetscale", 4, "MySQL that scales", "Database branching is genius for development workflows. Migration from AWS RDS was smoother than expected."),
    ("fider", 5, "Best open-source feedback", "Self-hosted Fider for our startup. Free, clean, and does exactly what Canny does for $400/mo."),
    ("nolt", 4, "Simple feedback boards", "Set up a feedback board in 10 minutes. Users love the voting system. Wish it had more customization options."),
    ("simple-analytics", 5, "Truly simple", "Does exactly what the name says. No bloat, no cookies, just clean analytics. Refreshing."),
    ("pika", 4, "Screenshot beautifier", "Makes my product screenshots look 10x better for tweets and blog posts. The free tier covers most use cases."),
]


def seed_reviews(conn):
    """Insert realistic reviews from test users."""
    existing = conn.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
    if existing > 10:
        print(f"  Reviews: already have {existing} reviews, skipping")
        return

    # Get test user IDs
    user_ids = []
    for email, _, _ in TEST_USERS:
        row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
        if row:
            user_ids.append(row[0])

    if not user_ids:
        print("  Reviews: no test users found, skipping")
        return

    # Build slug -> id lookup
    slug_map = {}
    for row in conn.execute("SELECT id, slug FROM tools WHERE status = 'approved'").fetchall():
        slug_map[row[1]] = row[0]

    total = 0
    now = datetime.utcnow()
    for i, (slug, rating, title, body) in enumerate(REVIEWS):
        tool_id = slug_map.get(slug)
        if not tool_id:
            continue
        user_id = user_ids[i % len(user_ids)]
        days_ago = random.uniform(1, 30)
        created_at = now - timedelta(days=days_ago)
        try:
            conn.execute(
                "INSERT OR IGNORE INTO reviews (tool_id, user_id, rating, title, body, is_verified_purchase, created_at) VALUES (?, ?, ?, ?, ?, 0, ?)",
                (tool_id, user_id, rating, title, body, created_at.strftime("%Y-%m-%d %H:%M:%S"))
            )
            total += 1
        except Exception:
            pass
    conn.commit()
    print(f"  Reviews: inserted {total} reviews")


# ── Maker Updates ────────────────────────────────────────────────────────────

CHANGELOG_ENTRIES = [
    ("Improved dashboard load times by 40%", "Optimized database queries and added caching for the main dashboard view. Page loads are noticeably snappier now.", "update"),
    ("New API endpoint for bulk operations", "Added a bulk endpoint that lets you process up to 100 items in a single request. Includes rate limiting and progress callbacks.", "changelog"),
    ("Dark mode support", "Added full dark mode support across the entire app. Respects system preferences and includes a manual toggle.", "changelog"),
    ("Fixed email delivery issues", "Resolved an issue where some transactional emails were being delayed. Switched to a more reliable SMTP provider.", "update"),
    ("New integrations: Slack and Discord", "You can now receive notifications directly in Slack or Discord. Webhooks are also available for custom integrations.", "changelog"),
    ("Performance improvements", "Reduced memory usage by 30% and improved cold start times. The app should feel faster across the board.", "update"),
    ("Export your data anytime", "Added a one-click data export feature. Download all your data as CSV or JSON — your data is always yours.", "changelog"),
    ("Redesigned onboarding flow", "Simplified the signup process from 5 steps to 2. New users can now get started in under a minute.", "update"),
    ("Added team collaboration", "Multiple team members can now collaborate on the same workspace. Includes role-based permissions.", "changelog"),
    ("Bug fixes and stability improvements", "Fixed several edge cases in the payment flow and improved error handling across the API.", "update"),
    ("New pricing calculator", "Added an interactive pricing calculator so you can estimate costs before committing. No surprises on your bill.", "changelog"),
    ("Webhook reliability improvements", "Webhooks now retry with exponential backoff. Added a webhook delivery log so you can debug failed deliveries.", "update"),
    ("Mobile responsive redesign", "The entire dashboard is now fully responsive. Manage everything from your phone.", "changelog"),
    ("SSO support for enterprise", "Added SAML-based SSO for enterprise customers. Integrates with Okta, Azure AD, and Google Workspace.", "changelog"),
    ("API rate limits increased", "Doubled the default API rate limits. Pro users now get 10,000 requests per minute.", "update"),
    ("Custom domain support", "You can now use your own domain for public-facing pages. SSL certificates are provisioned automatically.", "changelog"),
    ("Improved search functionality", "Search now supports fuzzy matching and filters. Results are more relevant and appear instantly.", "update"),
    ("New analytics dashboard", "Built a new analytics dashboard with real-time data. See views, clicks, and conversions as they happen.", "changelog"),
]


def seed_maker_updates(conn):
    """Create recent maker updates/changelogs for seeded tools."""
    # Always re-seed: delete old entries from our seed script and recreate
    # (so they point to the correct tool IDs after backfill_maker_ids)
    conn.execute("DELETE FROM maker_updates WHERE title IN (%s)" % ",".join(
        ["?"] * len(CHANGELOG_ENTRIES)
    ), [e[0] for e in CHANGELOG_ENTRIES])
    conn.commit()

    # Get tools that have maker_id set
    cursor = conn.execute(
        "SELECT t.id, t.maker_id FROM tools t WHERE t.maker_id IS NOT NULL AND t.status = 'approved'"
    )
    tools_with_makers = cursor.fetchall()

    if not tools_with_makers:
        print("  Maker updates: no tools with makers found, skipping")
        return

    now = datetime.utcnow()
    total = 0
    changelog_idx = 0

    for tool_id, maker_id in tools_with_makers:
        # 1-2 updates per tool
        update_count = random.randint(1, 2)
        for _ in range(update_count):
            if changelog_idx >= len(CHANGELOG_ENTRIES):
                changelog_idx = 0
            title, body, update_type = CHANGELOG_ENTRIES[changelog_idx]
            changelog_idx += 1
            # Random time in last 14 days (so streak badges activate)
            days_ago = random.uniform(0, 13)
            created_at = now - timedelta(days=days_ago)
            try:
                conn.execute(
                    "INSERT INTO maker_updates (maker_id, title, body, update_type, tool_id, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (maker_id, title, body, update_type, tool_id, created_at.strftime("%Y-%m-%d %H:%M:%S"))
                )
                total += 1
            except Exception:
                pass
    conn.commit()
    print(f"  Maker updates: inserted {total} changelog entries")


# ── Subscribers ──────────────────────────────────────────────────────────────

def seed_subscribers(conn):
    """Add fake subscriber emails (RFC-safe @example.com domain)."""
    total = 0
    for i in range(1, 9):
        try:
            conn.execute(
                "INSERT OR IGNORE INTO subscribers (email) VALUES (?)",
                (f"user{i}@example.com",)
            )
            total += 1
        except Exception:
            pass
    conn.commit()
    print(f"  Subscribers: {total} added")


# ── GovLink Listing ──────────────────────────────────────────────────────────

def add_govlink(conn):
    """Add GovLink as a real priced tool on IndieStack."""
    # Check if already exists
    existing = conn.execute("SELECT id FROM tools WHERE slug = 'govlink'").fetchone()
    if existing:
        print("  GovLink: already listed, skipping")
        return

    # Ensure maker exists
    maker_row = conn.execute("SELECT id FROM makers WHERE slug = 'patrick-amey-jones'").fetchone()
    if not maker_row:
        conn.execute(
            "INSERT INTO makers (slug, name, url, bio, indie_status) VALUES (?, ?, ?, ?, ?)",
            (
                "patrick-amey-jones",
                "Patrick Amey-Jones",
                "https://github.com/patrickameyjones",
                "Technical founder building IndieStack and GovLink. Self-taught developer, Cardiff University student.",
                "solo",
            )
        )
        conn.commit()
        maker_row = conn.execute("SELECT id FROM makers WHERE slug = 'patrick-amey-jones'").fetchone()
    maker_id = maker_row[0]

    # Get AI & Automation category ID
    cat_row = conn.execute("SELECT id FROM categories WHERE slug = 'ai-automation'").fetchone()
    if not cat_row:
        print("  GovLink: 'ai-automation' category not found, skipping")
        return
    category_id = cat_row[0]

    conn.execute(
        """INSERT INTO tools
           (name, slug, tagline, description, url, maker_name, maker_url,
            category_id, tags, status, is_verified, is_ejectable, upvote_count,
            price_pence, delivery_type, maker_id, replaces)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', 1, 1, ?, ?, 'link', ?, ?)""",
        (
            "GovLink",
            "govlink",
            "AI governance audit for UK law firms — 10-minute risk baseline with PDF report",
            "GovLink helps UK law firms and enterprises audit their AI governance baseline in 10 minutes. "
            "Answer 33 questions mapped to EU AI Act requirements, get a professional RAG-rated risk report "
            "with actionable recommendations. Includes PDF export for board presentations and insurance applications. "
            "Built by a technical founder who researched the compliance gap firsthand.",
            "https://govlink.fly.dev",
            "Patrick Amey-Jones",
            "https://github.com/patrickameyjones",
            category_id,
            "ai-governance,compliance,audit,risk-assessment,eu-ai-act,law-firms",
            34,  # upvotes
            2900,  # £29
            maker_id,
            "Deloitte AI audit, PwC AI governance, manual compliance spreadsheets",
        )
    )
    conn.commit()

    # Rebuild FTS so GovLink is searchable
    try:
        conn.execute("INSERT INTO tools_fts(tools_fts) VALUES('rebuild')")
        conn.commit()
    except Exception:
        pass

    print("  GovLink: listed with £29 price, verified + ejectable badges")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"Seeding social proof into: {DB_PATH}")

    if not os.path.exists(DB_PATH):
        print(f"  ERROR: Database not found at {DB_PATH}")
        print("  Run seed_tools.py first, or set INDIESTACK_DB_PATH")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    cleanup_tags(conn)
    remove_duplicates(conn)
    ensure_seed_makers(conn)
    backfill_maker_ids(conn)
    set_badges(conn)
    seed_upvotes(conn)
    seed_tool_views(conn)
    seed_test_users(conn)
    seed_wishlists(conn)
    seed_reviews(conn)
    seed_maker_updates(conn)
    seed_subscribers(conn)
    add_govlink(conn)

    conn.close()
    print("Done! Social proof seeded.")


if __name__ == "__main__":
    main()

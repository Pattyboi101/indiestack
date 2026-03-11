#!/usr/bin/env python3
"""Seed the IndieStack database with real indie tools.

Usage:
    python3 seed_tools.py

Idempotent — safe to run multiple times. Uses INSERT OR IGNORE on unique slugs.
"""

import sqlite3
import os
import re

# Match the DB path from db.py
DB_PATH = os.environ.get("INDIESTACK_DB_PATH", "/data/indiestack.db")

# If the production path doesn't exist, fall back to local
if not os.path.exists(os.path.dirname(DB_PATH) or "/data"):
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "indiestack.db")
    os.environ["INDIESTACK_DB_PATH"] = DB_PATH


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


# ── Schema (copied from db.py so script is standalone) ────────────────────

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

CREATE INDEX IF NOT EXISTS idx_tools_status ON tools(status);
CREATE INDEX IF NOT EXISTS idx_tools_category ON tools(category_id);
CREATE INDEX IF NOT EXISTS idx_tools_upvotes ON tools(upvote_count DESC);
CREATE INDEX IF NOT EXISTS idx_tools_maker ON tools(maker_id);
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

# ── Seed data ─────────────────────────────────────────────────────────────

CATEGORIES = [
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

# (slug, name, url, bio, indie_status)
MAKERS = [
    ("uku-taht", "Uku Taht", "https://twitter.com/ukutaht", "Creator of Plausible Analytics. Privacy-first web analytics.", "solo"),
    ("jack-ellis", "Jack Ellis", "https://twitter.com/JackEllis", "Co-founder of Fathom Analytics. Privacy-focused analytics.", "small_team"),
    ("adriaan-van-rossum", "Adriaan van Rossum", "https://twitter.com/AdriaanvRosworkaround", "Founder of Simple Analytics. The privacy-first Google Analytics alternative.", "solo"),
    ("justin-duke", "Justin Duke", "https://twitter.com/justinmduke", "Creator of Buttondown. Simple email for newsletter authors.", "solo"),
    ("nathan-barry", "Nathan Barry", "https://twitter.com/nathanbarry", "Founder of Kit (ConvertKit). Creator-first email marketing.", "small_team"),
    ("fabrizio-rinaldi", "Fabrizio Rinaldi", "https://twitter.com/linuz90", "Co-founder of Mailbrew. Your daily digest of favourite sources.", "small_team"),
    ("aj", "AJ", "https://twitter.com/ajlkn", "Creator of Carrd. Simple, free, responsive one-page sites.", "solo"),
    ("traf", "Traf", "https://twitter.com/taborbuilt", "Creator of Super.so. Build websites with Notion.", "solo"),
    ("kevin-conti", "Kevin Conti", "https://twitter.com/kvncnti", "Co-founder of Typedream. The new way to build websites, no code required.", "solo"),
    ("sahil-lavingia", "Sahil Lavingia", "https://twitter.com/shl", "Founder of Gumroad. Helping creators sell directly to their audience.", "small_team"),
    ("jj-lee", "JJ Lee", "https://twitter.com/laborjack", "Co-founder of Lemon Squeezy. Payments, tax, and subscriptions for software companies.", "small_team"),
    ("christian-owens", "Christian Owens", "https://twitter.com/christianowens", "Co-founder of Paddle. Complete payments infrastructure for SaaS.", "small_team"),
    ("jake-cooper", "Jake Cooper", "https://twitter.com/JakeCooper00", "Co-founder of Railway. Infrastructure, instantly.", "small_team"),
    ("anurag-goel", "Anurag Goel", "https://twitter.com/anuragmakesstuff", "Founder of Render. Cloud hosting built for developers.", "small_team"),
    ("sam-lambert", "Sam Lambert", "https://twitter.com/isamlambert", "CEO of PlanetScale. The database for developers.", "small_team"),
    ("fabrizio-rinaldi-typefully", "Fabrizio Rinaldi", "https://twitter.com/linuz90", "Co-founder of Typefully. Write, schedule, and grow on Twitter/X.", "small_team"),
    ("yannick-veys", "Yannick Veys", "https://twitter.com/yannickveys", "Co-founder of Hypefury. Grow your Twitter/X audience on autopilot.", "small_team"),
    ("joel-gascoigne", "Joel Gascoigne", "https://twitter.com/joelgascoigne", "Founder of Buffer. Social media management for growing brands.", "small_team"),
    ("joshua-beckman", "Joshua Beckman", "https://twitter.com/andjosh", "Creator of Pika. Instantly make your screenshots beautiful.", "solo"),
    ("mehdi-merah", "Mehdi Merah", "https://twitter.com/m_merah", "Creator of Screely. Instantly generate website mockups.", "solo"),
    ("devin-jacoviello", "Devin Jacoviello", "https://twitter.com/devinjacoviello", "Creator of Shots.so. Create beautiful mockups in seconds.", "solo"),
    ("sarah-cannon", "Sarah Cannon", "https://twitter.com/sarahcannon", "Co-founder of Canny. Track customer feedback to build better products.", "small_team"),
    ("fred-rivett", "Fred Rivett", "https://twitter.com/fredrivett", "Creator of Nolt. Customer feedback boards made simple.", "solo"),
    ("goenning", "Guilherme Oenning", "https://twitter.com/gaborbunyik", "Creator of Fider. Open-source customer feedback platform.", "solo"),
    ("hannes-lenke", "Hannes Lenke", "https://twitter.com/hanneslenke", "Co-founder of Checkly. Monitoring for modern DevOps.", "small_team"),
    ("ralph-chua", "Ralph Chua", "https://twitter.com/nichochar", "Co-founder of Better Stack. Uptime monitoring, on-call, and status pages.", "small_team"),
    ("ivan-zhao", "Ivan Zhao", "https://twitter.com/ivanhzhao", "Co-founder of Notion. The all-in-one workspace.", "small_team"),
    ("raphael-schaad", "Raphael Schaad", "https://twitter.com/raphaelschaad", "Co-founder of Cron. The next-generation calendar for professionals.", "small_team"),
    ("thomas-paul-mann", "Thomas Paul Mann", "https://twitter.com/thomaspaulmann", "Founder of Raycast. A blazingly fast launcher for macOS.", "small_team"),
    ("patrick-amey-jones", "Patrick Amey-Jones", "https://github.com/patrickameyjones", "Technical founder building IndieStack and GovLink. Self-taught developer, Cardiff University student.", "solo"),
]

# (name, slug, tagline, description, url, maker_slug, category_slug, tags, price_pence, pricing_model, upvotes)
TOOLS = [
    # Analytics
    (
        "Plausible Analytics",
        "plausible-analytics",
        "Simple and privacy-friendly alternative to Google Analytics",
        "Plausible is a lightweight and open-source web analytics tool. No cookies, fully compliant with GDPR, CCPA, and PECR. Made and hosted in the EU.",
        "https://plausible.io",
        "uku-taht",
        "analytics-metrics",
        "analytics,privacy,open-source,gdpr,web-analytics",
        900,  # $9/mo
        "paid",
        142,
    ),
    (
        "Fathom Analytics",
        "fathom-analytics",
        "Website analytics without compromising visitor privacy",
        "Fathom is a simple, light-weight, privacy-first alternative to Google Analytics. Compliant with GDPR, ePrivacy, PECR, CCPA, and more.",
        "https://usefathom.com",
        "jack-ellis",
        "analytics-metrics",
        "analytics,privacy,simple,gdpr,cookieless",
        1400,  # $14/mo
        "paid",
        128,
    ),
    (
        "Simple Analytics",
        "simple-analytics",
        "Privacy-friendly analytics without the complexity",
        "Simple Analytics gives you the analytics you need without tracking your users. No cookies, no personal data, just the insights you need.",
        "https://simpleanalytics.com",
        "adriaan-van-rossum",
        "analytics-metrics",
        "analytics,privacy,simple,no-cookies,dashboard",
        900,  # $9/mo
        "paid",
        87,
    ),
    # Email
    (
        "Buttondown",
        "buttondown",
        "The easiest way to run your newsletter",
        "Buttondown is a small, elegant tool for producing newsletters. It makes it easy for both novice and experienced authors to write great emails.",
        "https://buttondown.email",
        "justin-duke",
        "email-marketing",
        "newsletter,email,writing,markdown,simple",
        900,  # $9/mo (basic)
        "freemium",
        115,
    ),
    (
        "Kit",
        "kit",
        "The creator marketing platform built for creators, by creators",
        "Kit (formerly ConvertKit) helps creators earn a living online with email marketing, automation, and commerce tools designed specifically for creators.",
        "https://kit.com",
        "nathan-barry",
        "email-marketing",
        "email,marketing,creators,automation,newsletters",
        2900,  # $29/mo
        "freemium",
        196,
    ),
    (
        "Mailbrew",
        "mailbrew",
        "Your daily digest of favourite sources in your inbox",
        "Mailbrew lets you create automated email digests from your favourite sources: Twitter, Reddit, RSS, YouTube, and more. Read it all in one place.",
        "https://mailbrew.com",
        "fabrizio-rinaldi",
        "email-marketing",
        "email,digest,rss,newsletter,automation",
        700,  # $7/mo (approx)
        "paid",
        64,
    ),
    # Website Builders
    (
        "Carrd",
        "carrd",
        "Simple, free, fully responsive one-page sites for pretty much anything",
        "Build one-page websites for pretty much anything. Whether it's a personal profile, a landing page, or something for your project — Carrd has you covered.",
        "https://carrd.co",
        "aj",
        "landing-pages",
        "website-builder,landing-page,one-page,no-code,simple",
        1900,  # $19/yr (Pro)
        "freemium",
        234,
    ),
    (
        "Super.so",
        "super-so",
        "Build websites with Notion — fast, no code",
        "Super turns your Notion pages into fast, functional websites with custom domains, themes, fonts, and analytics. No code needed.",
        "https://super.so",
        "traf",
        "landing-pages",
        "notion,website-builder,no-code,cms,fast",
        1200,  # $12/mo
        "paid",
        108,
    ),
    (
        "Typedream",
        "typedream",
        "The new way to build websites, no code required",
        "Typedream is a no-code website builder that lets you create beautiful sites with a simple editor. Notion-like editing meets modern design.",
        "https://typedream.com",
        "kevin-conti",
        "landing-pages",
        "website-builder,no-code,design,landing-page,startup",
        0,  # Free tier
        "freemium",
        73,
    ),
    # Payments
    (
        "Gumroad",
        "gumroad",
        "Sell anything directly to anyone",
        "Gumroad helps creators sell products directly to their audience. Digital products, memberships, courses — everything in one simple storefront.",
        "https://gumroad.com",
        "sahil-lavingia",
        "payments",
        "payments,e-commerce,creators,digital-products,storefront",
        0,  # Free (10% fee per transaction)
        "free",
        267,
    ),
    (
        "Lemon Squeezy",
        "lemon-squeezy",
        "Payments, tax, and subscriptions for your software business",
        "Lemon Squeezy is the all-in-one platform for running your SaaS business. Payments, subscriptions, global tax compliance, fraud prevention, and more.",
        "https://lemonsqueezy.com",
        "jj-lee",
        "payments",
        "payments,saas,subscriptions,tax,merchant-of-record",
        0,  # Free (5%+50c per transaction)
        "free",
        189,
    ),
    (
        "Paddle",
        "paddle",
        "The complete payments infrastructure for SaaS companies",
        "Paddle handles payments, tax, subscriptions, and more so SaaS companies can focus on building great products. The merchant of record for software.",
        "https://paddle.com",
        "christian-owens",
        "payments",
        "payments,saas,subscriptions,tax,billing",
        0,  # Usage-based pricing
        "paid",
        156,
    ),
    # Dev Tools
    (
        "Railway",
        "railway",
        "Infrastructure, instantly. Develop, deploy, and scale your apps",
        "Railway is a deployment platform that lets you provision infrastructure, develop locally, and deploy to the cloud with ease. GitHub integration, instant deploys.",
        "https://railway.app",
        "jake-cooper",
        "developer-tools",
        "hosting,deploy,infrastructure,cloud,developer",
        500,  # $5/mo (Hobby)
        "freemium",
        203,
    ),
    (
        "Render",
        "render",
        "Cloud hosting built for developers, not DevOps",
        "Render is a unified cloud to build and run all your apps and websites with free TLS, global CDN, private networks, and auto-deploys from Git.",
        "https://render.com",
        "anurag-goel",
        "developer-tools",
        "hosting,cloud,deploy,developer,heroku-alternative",
        700,  # $7/mo (Starter)
        "freemium",
        178,
    ),
    (
        "PlanetScale",
        "planetscale",
        "The database for developers — serverless MySQL",
        "PlanetScale is a MySQL-compatible serverless database platform. Branching, non-blocking schema changes, and unlimited scale with a developer-first experience.",
        "https://planetscale.com",
        "sam-lambert",
        "developer-tools",
        "database,mysql,serverless,branching,developer",
        2900,  # $29/mo (Scaler)
        "freemium",
        215,
    ),
    # Social Media / Writing
    (
        "Typefully",
        "typefully",
        "Write, schedule, and grow on Twitter/X and LinkedIn",
        "Typefully is the all-in-one tool to write better content, schedule posts, and grow your audience on Twitter/X and LinkedIn. AI writing assistant included.",
        "https://typefully.com",
        "fabrizio-rinaldi-typefully",
        "social-media",
        "twitter,linkedin,scheduling,writing,growth",
        1200,  # $12.50/mo (approx)
        "freemium",
        145,
    ),
    (
        "Hypefury",
        "hypefury",
        "Grow and monetize your Twitter/X audience on autopilot",
        "Hypefury helps you schedule tweets, auto-retweet your best content, create sale tweets, and grow your Twitter/X following with smart automation.",
        "https://hypefury.com",
        "yannick-veys",
        "social-media",
        "twitter,scheduling,automation,growth,monetize",
        1900,  # $19/mo (Standard)
        "paid",
        97,
    ),
    (
        "Buffer",
        "buffer",
        "Grow your audience on social media with ease",
        "Buffer is the simple, intuitive social media toolkit for small businesses. Plan, publish, and analyze your social media performance in one place.",
        "https://buffer.com",
        "joel-gascoigne",
        "social-media",
        "social-media,scheduling,analytics,multi-platform,management",
        600,  # $6/mo (Essentials)
        "freemium",
        174,
    ),
    # Design
    (
        "Pika",
        "pika",
        "Instantly make your screenshots beautiful",
        "Pika transforms boring screenshots into stunning visuals. Add backgrounds, gradients, shadows, and browser frames — perfect for social media and docs.",
        "https://pika.style",
        "joshua-beckman",
        "design-creative",
        "screenshots,design,mockups,social-media,visuals",
        0,  # Free
        "freemium",
        83,
    ),
    (
        "Screely",
        "screely",
        "Instantly generate website mockups from screenshots",
        "Screely turns your screenshots into beautiful website mockups. Drop in an image and get a clean browser frame mockup — no signup required.",
        "https://screely.com",
        "mehdi-merah",
        "design-creative",
        "mockups,screenshots,design,browser-frame,free",
        0,  # Free
        "free",
        56,
    ),
    (
        "Shots.so",
        "shots-so",
        "Create beautiful mockups in seconds",
        "Shots turns your screenshots into gorgeous mockups with customizable backgrounds, shadows, and frames. Perfect for Product Hunt, social posts, and docs.",
        "https://shots.so",
        "devin-jacoviello",
        "design-creative",
        "mockups,screenshots,design,product-hunt,marketing",
        0,  # Free tier
        "freemium",
        68,
    ),
    # Feedback
    (
        "Canny",
        "canny",
        "Track customer feedback to build better products",
        "Canny helps you collect, organize, and analyze product feedback so you can make better product decisions. Feedback boards, changelogs, and roadmaps.",
        "https://canny.io",
        "sarah-cannon",
        "feedback-reviews",
        "feedback,product-management,roadmap,changelog,customer",
        7900,  # $79/mo (Growth)
        "freemium",
        134,
    ),
    (
        "Nolt",
        "nolt",
        "Customer feedback boards made simple",
        "Nolt is a simple feedback board where your users can suggest, vote, and discuss ideas. Keep your product roadmap aligned with what users actually want.",
        "https://nolt.io",
        "fred-rivett",
        "feedback-reviews",
        "feedback,voting,roadmap,simple,customer-voice",
        2500,  # $25/mo
        "paid",
        47,
    ),
    (
        "Fider",
        "fider",
        "Open-source customer feedback platform",
        "Fider is a free, open-source platform for collecting and prioritizing customer feedback. Self-host it or use the cloud version.",
        "https://fider.io",
        "goenning",
        "feedback-reviews",
        "feedback,open-source,self-hosted,voting,free",
        0,  # Free / open-source
        "free",
        39,
    ),
    # Monitoring
    (
        "Checkly",
        "checkly",
        "Monitoring for the modern DevOps stack",
        "Checkly lets you monitor your APIs and web apps at scale. Synthetic monitoring, API checks, and browser checks with Playwright — from code.",
        "https://checklyhq.com",
        "hannes-lenke",
        "monitoring-uptime",
        "monitoring,api,devops,playwright,synthetic",
        3000,  # $30/mo (Team)
        "freemium",
        112,
    ),
    (
        "Better Stack",
        "better-stack",
        "Uptime monitoring, on-call alerting, and status pages",
        "Better Stack (formerly Better Uptime) combines uptime monitoring, incident management, on-call scheduling, and status pages into one beautiful platform.",
        "https://betterstack.com",
        "ralph-chua",
        "monitoring-uptime",
        "monitoring,uptime,on-call,status-page,incidents",
        2400,  # $24/mo (Team)
        "freemium",
        98,
    ),
    # AI & Governance
    (
        "GovLink",
        "govlink",
        "AI governance audit for UK law firms — 10-minute risk baseline with PDF report",
        "GovLink helps UK law firms and enterprises audit their AI governance baseline in 10 minutes. "
        "Answer 33 questions mapped to EU AI Act requirements, get a professional RAG-rated risk report "
        "with actionable recommendations. Includes PDF export for board presentations and insurance applications.",
        "https://govlink.fly.dev",
        "patrick-amey-jones",
        "ai-automation",
        "ai-governance,compliance,audit,risk-assessment,eu-ai-act,law-firms",
        2900,  # £29
        "paid",
        34,
    ),
]


def main():
    print(f"Seeding database at: {DB_PATH}")

    # Ensure directory exists
    db_dir = os.path.dirname(DB_PATH)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Create schema
    conn.executescript(SCHEMA)
    conn.executescript(FTS_SCHEMA)

    # Also add indie_status column to makers if missing (migration from db.py)
    try:
        conn.execute("SELECT indie_status FROM makers LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE makers ADD COLUMN indie_status TEXT NOT NULL DEFAULT ''")

    # ── Insert categories ─────────────────────────────────────────────────
    for name, slug, description, icon in CATEGORIES:
        conn.execute(
            "INSERT OR IGNORE INTO categories (name, slug, description, icon) VALUES (?, ?, ?, ?)",
            (name, slug, description, icon),
        )
    conn.commit()
    print(f"  Categories: {conn.execute('SELECT count(*) FROM categories').fetchone()[0]}")

    # Build category slug -> id lookup
    cat_map = {}
    for row in conn.execute("SELECT id, slug FROM categories").fetchall():
        cat_map[row[1]] = row[0]

    # ── Insert makers ─────────────────────────────────────────────────────
    for slug, name, url, bio, indie_status in MAKERS:
        conn.execute(
            "INSERT OR IGNORE INTO makers (slug, name, url, bio, indie_status) VALUES (?, ?, ?, ?, ?)",
            (slug, name, url, bio, indie_status),
        )
    conn.commit()
    print(f"  Makers: {conn.execute('SELECT count(*) FROM makers').fetchone()[0]}")

    # Build maker slug -> id lookup
    maker_map = {}
    for row in conn.execute("SELECT id, slug FROM makers").fetchall():
        maker_map[row[1]] = row[0]

    # ── Insert tools ──────────────────────────────────────────────────────
    inserted = 0
    skipped = 0
    for (name, slug, tagline, description, url, maker_slug, category_slug,
         tags, price_pence, pricing_model, upvotes) in TOOLS:

        category_id = cat_map.get(category_slug)
        maker_id = maker_map.get(maker_slug)

        if not category_id:
            print(f"  WARNING: Unknown category '{category_slug}' for tool '{name}', skipping")
            skipped += 1
            continue

        # Look up maker name/url for denormalized fields
        maker_row = conn.execute(
            "SELECT name, url FROM makers WHERE id = ?", (maker_id,)
        ).fetchone()
        maker_name = maker_row[0] if maker_row else ""
        maker_url = maker_row[1] if maker_row else ""

        # price_pence: 0 for free tools -> store as NULL
        db_price = price_pence if price_pence and price_pence > 0 else None

        try:
            conn.execute(
                """INSERT OR IGNORE INTO tools
                   (name, slug, tagline, description, url, maker_name, maker_url,
                    category_id, tags, status, is_verified, upvote_count,
                    price_pence, delivery_type, maker_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', 0, ?, ?, 'link', ?)""",
                (name, slug, tagline, description, url, maker_name, maker_url,
                 category_id, tags, upvotes, db_price, maker_id),
            )
            if conn.total_changes:
                inserted += 1
        except Exception as e:
            print(f"  ERROR inserting '{name}': {e}")
            skipped += 1

    conn.commit()
    tool_count = conn.execute("SELECT count(*) FROM tools").fetchone()[0]
    print(f"  Tools: {tool_count} total ({inserted} new this run)")

    # ── Rebuild FTS indexes ───────────────────────────────────────────────
    print("  Rebuilding FTS indexes...")
    conn.execute("INSERT INTO tools_fts(tools_fts) VALUES('rebuild')")
    conn.execute("INSERT INTO makers_fts(makers_fts) VALUES('rebuild')")
    conn.commit()
    print("  FTS rebuild complete.")

    # Backfill indie_status for any existing makers missing it
    conn.execute("UPDATE makers SET indie_status = 'solo' WHERE indie_status IS NULL OR indie_status = ''")
    conn.commit()
    print("  Backfilled indie_status on makers.")

    # ── Backfill replaces field ───────────────────────────────────────────
    # Add replaces column if missing
    try:
        conn.execute("SELECT replaces FROM tools LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE tools ADD COLUMN replaces TEXT NOT NULL DEFAULT ''")
        conn.commit()

    REPLACES = {
        "plausible-analytics": "Google Analytics, Adobe Analytics",
        "fathom-analytics": "Google Analytics, Adobe Analytics",
        "simple-analytics": "Google Analytics, Mixpanel",
        "buttondown": "Mailchimp, Substack",
        "kit": "Mailchimp, ActiveCampaign, Drip",
        "mailbrew": "Feedly, Google Alerts",
        "carrd": "Squarespace, Wix, WordPress",
        "super-so": "Squarespace, WordPress, Webflow",
        "typedream": "Squarespace, Wix, Webflow",
        "gumroad": "Shopify, WooCommerce, Stripe",
        "lemon-squeezy": "Stripe, Paddle, FastSpring",
        "paddle": "Stripe, Chargebee, Recurly",
        "railway": "Heroku, AWS, Vercel",
        "render": "Heroku, AWS, DigitalOcean",
        "planetscale": "AWS RDS, Google Cloud SQL, Supabase",
        "typefully": "Hootsuite, Sprout Social, TweetDeck",
        "hypefury": "Hootsuite, TweetDeck, SocialBee",
        "buffer": "Hootsuite, Sprout Social, Later",
        "pika": "Canva, Figma, Photoshop",
        "screely": "Canva, CleanShot, Figma",
        "shots-so": "Canva, CleanShot, Figma",
        "canny": "Jira, Trello, UserVoice",
        "nolt": "Jira, Trello, UserVoice, Canny",
        "fider": "Jira, UserVoice, Canny",
        "checkly": "Datadog, PagerDuty, Pingdom",
        "better-stack": "Datadog, PagerDuty, Pingdom, UptimeRobot",
    }

    updated = 0
    for slug, replaces in REPLACES.items():
        cursor = conn.execute("UPDATE tools SET replaces = ? WHERE slug = ? AND (replaces IS NULL OR replaces = '')", (replaces, slug))
        if cursor.rowcount:
            updated += 1
    conn.commit()
    print(f"  Replaces: backfilled {updated} tools with competitor data.")

    conn.close()
    print("Done!")


if __name__ == "__main__":
    main()

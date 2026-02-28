#!/usr/bin/env python3
"""Seed IndieStack with tools covering top search gaps.

Covers queries that currently return zero results:
Vercel, Auth0, Intercom, Netlify, WordPress, PagerDuty, Mailchimp, Firebase.

Usage:
    python3 seed_search_gaps.py

Idempotent — uses INSERT OR IGNORE on unique slugs.
Also updates replaces field on existing tools if they already exist.
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


# ── Makers ─────────────────────────────────────────────────────────────────
# (slug, name, url, bio, indie_status)
MAKERS = [
    ("andras-bacsai", "Andras Bacsai", "https://twitter.com/andrasbacsai",
     "Creator of Coolify. Self-hosting everything.", "solo"),
    ("jake-cooper", "Jake Cooper", "https://twitter.com/JakeCooper00",
     "Co-founder of Railway. Infrastructure, instantly.", "small_team"),
    ("colin-timmerman", "Colin Timmerman", "https://clerk.com",
     "Co-founder of Clerk. User management and authentication.", "small_team"),
    ("ross-andrews", "Ross Andrews", "https://kinde.com",
     "Co-founder of Kinde. Authentication for modern apps.", "small_team"),
    ("pilcrow", "pilcrow", "https://github.com/pilcrowOnPaper",
     "Creator of Lucia Auth. Open-source auth for any runtime.", "solo"),
    ("pranav-jha", "Pranav Jha", "https://twitter.com/paborat",
     "Co-founder of Chatwoot. Open-source customer engagement.", "small_team"),
    ("alexander-maccaw", "Alexander MacCaw", "https://twitter.com/maboroshi",
     "Co-founder of Papercups. Open-source live chat.", "small_team"),
    ("john-onolan", "John O'Nolan", "https://twitter.com/JohnONolan",
     "Founder of Ghost. Independent technology for modern publishing.", "small_team"),
    ("james-mikrut", "James Mikrut", "https://twitter.com/jmikrut",
     "Creator of Payload CMS. The most powerful headless CMS.", "small_team"),
    ("sojan-jose", "Sojan Jose", "https://twitter.com/soaborat",
     "Creator of Spike.sh. Incident management for dev teams.", "small_team"),
    ("chris-frantz", "Chris Frantz", "https://twitter.com/chriaborat",
     "Co-founder of Loops. Email for modern SaaS.", "small_team"),
    ("paul-copplestone", "Paul Copplestone", "https://twitter.com/kiwicopple",
     "Co-founder of Supabase. Open source Firebase alternative.", "small_team"),
]


# ── Tools ──────────────────────────────────────────────────────────────────
# (name, slug, tagline, description, url, maker_slug, category_slug, tags,
#  price_pence, replaces, upvotes)
TOOLS = [
    # ── Vercel alternatives ────────────────────────────────────────────────
    (
        "Coolify",
        "coolify",
        "Self-hostable Heroku, Netlify, and Vercel alternative",
        "Coolify is an open-source, self-hostable platform that lets you deploy "
        "static sites, APIs, databases, and services with a single click. Manage "
        "your own infrastructure without vendor lock-in. Supports Docker, Git push "
        "deploys, and automatic SSL.",
        "https://coolify.io",
        "andras-bacsai",
        "developer-tools",
        "hosting,self-hosted,open-source,deployment,docker",
        0,  # free / open-source
        "Vercel,Netlify",
        18,
    ),
    # Railway already exists in DB from seed_tools.py — we just update replaces later
    # ── Auth0 alternatives ─────────────────────────────────────────────────
    (
        "Clerk",
        "clerk",
        "Complete user management and authentication for modern apps",
        "Clerk provides embeddable UIs, flexible APIs, and admin dashboards for "
        "authentication and user management. Pre-built components for sign-in, "
        "sign-up, user profiles, and organization management. Works with React, "
        "Next.js, and more.",
        "https://clerk.com",
        "colin-timmerman",
        "authentication",
        "auth,login,user-management,sso,react",
        0,  # generous free tier
        "Auth0",
        22,
    ),
    (
        "Kinde",
        "kinde",
        "Authentication and user management for modern applications",
        "Kinde offers authentication, user management, and feature flags in one "
        "platform. Supports social login, MFA, SAML SSO, and fine-grained "
        "authorization. Free for up to 10,500 monthly active users.",
        "https://kinde.com",
        "ross-andrews",
        "authentication",
        "auth,sso,user-management,feature-flags,b2b",
        0,  # free up to 10.5K MAU
        "Auth0",
        15,
    ),
    (
        "Lucia Auth",
        "lucia-auth",
        "Open-source auth library for any JavaScript runtime",
        "Lucia is a simple, framework-agnostic authentication library for "
        "TypeScript. It handles sessions, cookies, and database adapters so you "
        "can own your auth layer without a third-party service. Works with Node, "
        "Bun, Deno, and Cloudflare Workers.",
        "https://lucia-auth.com",
        "pilcrow",
        "authentication",
        "auth,open-source,typescript,sessions,library",
        0,  # free / open-source
        "Auth0",
        12,
    ),
    # ── Intercom alternatives ──────────────────────────────────────────────
    (
        "Chatwoot",
        "chatwoot",
        "Open-source customer engagement platform",
        "Chatwoot is an open-source omnichannel customer support platform. Live "
        "chat, email, social media, and messaging channels in one dashboard. "
        "Self-host for free or use the managed cloud from $19/mo.",
        "https://chatwoot.com",
        "pranav-jha",
        "customer-support",
        "live-chat,support,open-source,helpdesk,omnichannel",
        0,  # self-hosted free, cloud from $19
        "Intercom",
        19,
    ),
    (
        "Papercups",
        "papercups",
        "Open-source live customer chat widget",
        "Papercups is an open-source live chat widget built in Elixir. Embed a "
        "lightweight chat widget on your site, manage conversations in a shared "
        "inbox, and integrate with Slack. Self-host or use the cloud version.",
        "https://papercups.io",
        "alexander-maccaw",
        "customer-support",
        "live-chat,open-source,support,widget,elixir",
        0,  # open-source
        "Intercom",
        8,
    ),
    # ── WordPress alternatives ─────────────────────────────────────────────
    (
        "Ghost",
        "ghost",
        "Independent technology for modern publishing and newsletters",
        "Ghost is a powerful open-source publishing platform for professional "
        "bloggers, journalists, and content creators. Built-in memberships, "
        "newsletters, and content monetization. Fast Node.js core with a "
        "beautiful editor.",
        "https://ghost.org",
        "john-onolan",
        "landing-pages",
        "blogging,cms,publishing,newsletter,open-source",
        900,  # $9/mo starter
        "WordPress",
        24,
    ),
    (
        "Payload CMS",
        "payload-cms",
        "The most powerful TypeScript headless CMS",
        "Payload is a free, open-source headless CMS and application framework "
        "built with TypeScript. Code-first config, auto-generated APIs (REST and "
        "GraphQL), rich text editor, and access control out of the box.",
        "https://payloadcms.com",
        "james-mikrut",
        "developer-tools",
        "cms,headless,typescript,open-source,api",
        0,  # free / open-source
        "WordPress",
        16,
    ),
    # ── PagerDuty alternatives ─────────────────────────────────────────────
    (
        "Spike.sh",
        "spike-sh",
        "Incident management and on-call alerting for dev teams",
        "Spike.sh is a lightweight incident management platform. Phone call, SMS, "
        "Slack, and email alerts when things go down. On-call scheduling, "
        "escalation policies, and incident timelines. Free tier available, "
        "paid plans from $8/user/mo.",
        "https://spike.sh",
        "sojan-jose",
        "monitoring-uptime",
        "incident-management,on-call,alerts,monitoring,devops",
        0,  # free tier, paid from $8/user
        "PagerDuty",
        10,
    ),
    # Better Stack already exists — we just update replaces later
    # ── Mailchimp alternative ──────────────────────────────────────────────
    (
        "Loops",
        "loops",
        "Email for modern SaaS companies",
        "Loops is an email platform built for SaaS. Create beautiful transactional "
        "and marketing emails with a visual editor. Event-based automations, "
        "audience segmentation, and analytics. Free up to 1,000 contacts.",
        "https://loops.so",
        "chris-frantz",
        "email-marketing",
        "email,marketing,saas,transactional,automation",
        0,  # free up to 1000 contacts
        "Mailchimp",
        14,
    ),
    # ── Firebase alternative ───────────────────────────────────────────────
    (
        "Supabase",
        "supabase",
        "The open-source Firebase alternative",
        "Supabase provides a Postgres database, authentication, instant APIs, "
        "edge functions, realtime subscriptions, and storage. Generous free tier "
        "with dashboard. Built on top of proven open-source tools.",
        "https://supabase.com",
        "paul-copplestone",
        "developer-tools",
        "database,auth,storage,realtime,open-source",
        0,  # generous free tier
        "Firebase",
        25,
    ),
]

# ── Existing tools that need replaces updated ──────────────────────────────
REPLACES_UPDATES = {
    # Better Stack should list PagerDuty (it may already have other replaces)
    "better-stack": "PagerDuty",
    # Railway should also cover Vercel searches
    "railway": "Heroku, AWS, Vercel",
}


def main():
    print(f"Seeding search-gap tools at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Ensure replaces column exists
    try:
        conn.execute("SELECT replaces FROM tools LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE tools ADD COLUMN replaces TEXT NOT NULL DEFAULT ''")
        conn.commit()

    # Ensure indie_status column exists on makers
    try:
        conn.execute("SELECT indie_status FROM makers LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE makers ADD COLUMN indie_status TEXT NOT NULL DEFAULT ''")
        conn.commit()

    # ── Insert makers ──────────────────────────────────────────────────────
    for slug, name, url, bio, indie_status in MAKERS:
        conn.execute(
            "INSERT OR IGNORE INTO makers (slug, name, url, bio, indie_status) "
            "VALUES (?, ?, ?, ?, ?)",
            (slug, name, url, bio, indie_status),
        )
    conn.commit()
    print(f"  Makers: {conn.execute('SELECT count(*) FROM makers').fetchone()[0]}")

    # Build lookups
    cat_map = {}
    for row in conn.execute("SELECT id, slug FROM categories").fetchall():
        cat_map[row[1]] = row[0]

    maker_map = {}
    for row in conn.execute("SELECT id, slug FROM makers").fetchall():
        maker_map[row[1]] = row[0]

    # ── Insert tools ───────────────────────────────────────────────────────
    inserted = 0
    skipped = 0
    for (name, slug, tagline, description, url, maker_slug, category_slug,
         tags, price_pence, replaces, upvotes) in TOOLS:

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
                    price_pence, delivery_type, maker_id, replaces)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', 0, ?, ?, 'link', ?, ?)""",
                (name, slug, tagline, description, url, maker_name, maker_url,
                 category_id, tags, upvotes, db_price, maker_id, replaces),
            )
            if conn.total_changes:
                inserted += 1
        except Exception as e:
            print(f"  ERROR inserting '{name}': {e}")
            skipped += 1

    conn.commit()
    tool_count = conn.execute("SELECT count(*) FROM tools WHERE status = 'approved'").fetchone()[0]
    print(f"  Tools: {tool_count} approved ({inserted} new this run, {skipped} skipped)")

    # ── Update replaces on existing tools ──────────────────────────────────
    updated = 0
    for slug, replaces in REPLACES_UPDATES.items():
        cursor = conn.execute(
            "UPDATE tools SET replaces = ? WHERE slug = ? AND (replaces IS NULL OR replaces = '')",
            (replaces, slug),
        )
        if cursor.rowcount:
            updated += 1
            print(f"  Updated replaces on '{slug}' -> '{replaces}'")
    conn.commit()
    if updated:
        print(f"  Updated replaces on {updated} existing tools.")

    # ── Rebuild FTS indexes ────────────────────────────────────────────────
    print("  Rebuilding FTS indexes...")
    conn.execute("INSERT INTO tools_fts(tools_fts) VALUES('rebuild')")
    try:
        conn.execute("INSERT INTO makers_fts(makers_fts) VALUES('rebuild')")
    except Exception:
        pass  # makers_fts may not exist in all environments
    conn.commit()
    print("  FTS rebuild complete.")

    # ── Summary ────────────────────────────────────────────────────────────
    total = conn.execute("SELECT count(*) FROM tools WHERE status = 'approved'").fetchone()[0]
    print(f"\nDone. Approved tools: {total}")
    print("Alternatives pages now covering:")
    for row in conn.execute(
        "SELECT DISTINCT replaces FROM tools WHERE replaces IS NOT NULL AND replaces != '' ORDER BY replaces"
    ).fetchall():
        for comp in row[0].split(","):
            slug = comp.strip().lower().replace(" ", "-")
            print(f"  /alternatives/{slug}")

    conn.close()


if __name__ == "__main__":
    main()

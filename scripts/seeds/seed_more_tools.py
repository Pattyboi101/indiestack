#!/usr/bin/env python3
"""Seed the IndieStack database with ~30 real indie SaaS tools across underserved categories.

Usage:
    python3 seed_more_tools.py

Idempotent — safe to run multiple times. Uses INSERT OR IGNORE on unique slugs.
All tools are auto-approved with realistic upvote counts.
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
    # Authentication
    ("workos-team", "WorkOS", "https://workos.com",
     "Enterprise-ready auth infrastructure. SSO, SCIM, and user management APIs.", "small_team"),
    ("stytch-team", "Stytch", "https://stytch.com",
     "Modern authentication platform with passwordless, OAuth, and session management.", "small_team"),
    ("descope-team", "Descope", "https://descope.com",
     "Drag-and-drop customer authentication and identity management.", "small_team"),

    # Payments
    ("chargebee-team", "Chargebee", "https://chargebee.com",
     "Subscription billing and revenue management platform for SaaS.", "small_team"),

    # Developer Tools
    ("dokku-team", "Dokku", "https://dokku.com",
     "The smallest PaaS implementation. Open-source Heroku alternative.", "solo"),
    ("caprover-team", "CapRover", "https://caprover.com",
     "Scalable, free, self-hosted PaaS built on Docker and Nginx.", "solo"),
    ("pocketbase-team", "PocketBase", "https://pocketbase.io",
     "Open-source realtime backend in a single Go file with embedded SQLite.", "solo"),

    # Landing Pages
    ("webflow-team", "Webflow", "https://webflow.com",
     "Visual web development platform for building professional sites without code.", "small_team"),
    ("umso-team", "Umso", "https://umso.com",
     "The website builder for startups. Simple, fast, and affordable.", "small_team"),
    ("unicorn-platform-team", "Unicorn Platform", "https://unicornplatform.com",
     "AI website builder for busy founders. SaaS, apps, and directories.", "solo"),

    # Forms & Surveys
    ("heyflow-team", "Heyflow", "https://heyflow.com",
     "Interactive flow builder for lead generation and conversion.", "small_team"),

    # CRM & Sales
    ("twenty-team", "Twenty", "https://twenty.com",
     "Building the #1 open-source CRM. Modern Salesforce alternative.", "small_team"),
    ("folk-team", "Folk", "https://folk.app",
     "The CRM built for relationships. Lightweight and collaborative.", "small_team"),
    ("attio-team", "Attio", "https://attio.com",
     "Next-generation CRM with flexible data models and real-time collaboration.", "small_team"),

    # File Management
    ("uploadthing-team", "UploadThing", "https://uploadthing.com",
     "File uploads for modern web devs. Built by Ping.gg.", "small_team"),
    ("imagekit-team", "ImageKit", "https://imagekit.io",
     "Real-time image and video optimization, transformation, and CDN.", "small_team"),
    ("cloudinary-team", "Cloudinary", "https://cloudinary.com",
     "Image and video API platform for developers and marketers.", "small_team"),

    # Monitoring & Uptime
    ("openstatus-team", "OpenStatus", "https://openstatus.dev",
     "Open-source status pages and uptime monitoring. Bootstrapped.", "small_team"),

    # API Tools — Bruno only (Hoppscotch and Insomnia already seeded)
    # (Hoppscotch, Insomnia, Bruno already seeded in seed_mcp_coverage/seed_comprehensive)

    # AI & Automation
    ("dify-team", "Dify", "https://dify.ai",
     "Open-source LLM app development platform with visual workflows.", "small_team"),
    ("langfuse-team", "Langfuse", "https://langfuse.com",
     "Open-source LLM observability, tracing, and prompt management.", "small_team"),
    ("helicone-team", "Helicone", "https://helicone.ai",
     "Open-source LLM monitoring, cost tracking, and analytics.", "small_team"),
]


# ── Tools ──────────────────────────────────────────────────────────────────
# (name, slug, tagline, description, url, maker_slug, category_slug,
#  tags, price_pence, upvotes)

TOOLS = [
    # ── Authentication ─────────────────────────────────────────────────────

    (
        "WorkOS",
        "workos",
        "Enterprise-ready authentication with SSO, SCIM, and directory sync",
        "WorkOS provides a complete set of building blocks for enterprise features. "
        "Add Single Sign-On, Directory Sync, Admin Portal, and Multi-Factor Auth to your app "
        "with just a few lines of code. AuthKit offers up to 1M free MAUs. Used by Vercel, Perplexity, and Cursor.",
        "https://workos.com",
        "workos-team",
        "authentication",
        "sso,scim,directory-sync,enterprise,mfa,authentication",
        None,  # Free up to 1M MAUs
        89,
    ),
    (
        "Stytch",
        "stytch",
        "Modern auth platform with passwordless, OAuth, and session management",
        "Stytch makes authentication simple with passwordless logins, magic links, OAuth, "
        "multi-tenancy, and session management. Pay-per-use pricing with no hard caps — "
        "free for up to 10,000 MAUs. SDKs for React, Next.js, Python, Go, and more.",
        "https://stytch.com",
        "stytch-team",
        "authentication",
        "passwordless,magic-links,oauth,sessions,multi-tenancy,authentication",
        24900,  # $249/mo Pro plan
        72,
    ),
    (
        "Descope",
        "descope",
        "Drag-and-drop authentication flows with no-code identity management",
        "Descope lets you build authentication and identity management visually. "
        "Drag-and-drop workflows for signup, login, MFA, and SSO. Supports CIAM, "
        "B2B multi-tenancy, and agentic identity for AI applications. Free tier included.",
        "https://descope.com",
        "descope-team",
        "authentication",
        "no-code,identity,ciam,b2b,sso,mfa,authentication",
        24900,  # $249/mo Pro plan
        58,
    ),

    # ── Payments ───────────────────────────────────────────────────────────

    (
        "Chargebee",
        "chargebee",
        "Subscription billing and revenue management for SaaS companies",
        "Chargebee automates subscription billing, invoicing, tax compliance, and revenue recognition. "
        "Supports 40+ payment gateways and 100+ billing currencies. Free for up to $250K in lifetime billing. "
        "Smart dunning, metered billing, and usage-based pricing built in.",
        "https://chargebee.com",
        "chargebee-team",
        "payments",
        "subscriptions,billing,invoicing,tax,revenue,dunning,payments",
        59900,  # $599/mo Performance plan
        95,
    ),

    # ── Developer Tools ────────────────────────────────────────────────────

    (
        "Dokku",
        "dokku",
        "The smallest PaaS implementation — self-hosted Heroku in one command",
        "Dokku is a Docker-powered mini-Heroku you can run on any VPS. Push via Git, "
        "build with Heroku buildpacks, and deploy in isolated containers. Plugin ecosystem "
        "for databases, SSL, domains, and process management. Completely free and open source.",
        "https://dokku.com",
        "dokku-team",
        "developer-tools",
        "paas,self-hosted,docker,heroku,git-push,deployment,open-source",
        None,  # Free / open source
        112,
    ),
    (
        "CapRover",
        "caprover",
        "Free self-hosted PaaS with one-click apps and automatic SSL",
        "CapRover turns any Docker-enabled server into a PaaS with a web dashboard, CLI, "
        "and push-to-deploy workflows. One-click apps catalog for databases, CMS, and dev tools. "
        "Automatic HTTPS via Let's Encrypt, horizontal scaling, and zero vendor lock-in.",
        "https://caprover.com",
        "caprover-team",
        "developer-tools",
        "paas,self-hosted,docker,one-click,ssl,deployment,open-source",
        None,  # Free / open source
        98,
    ),
    (
        "PocketBase",
        "pocketbase",
        "Open-source backend in a single file — SQLite, auth, and realtime",
        "PocketBase is a Go-based backend compiled into a single executable. Embedded SQLite database, "
        "real-time subscriptions, built-in authentication, file storage, and an admin dashboard — "
        "all in one file. Extend with JavaScript hooks or as a Go library. Deploy anywhere.",
        "https://pocketbase.io",
        "pocketbase-team",
        "developer-tools",
        "backend,sqlite,realtime,auth,self-hosted,go,open-source",
        None,  # Free / open source
        142,
    ),

    # ── Landing Pages ──────────────────────────────────────────────────────

    (
        "Webflow",
        "webflow",
        "Visual web development platform for professional no-code sites",
        "Webflow combines a visual canvas with production-grade code output. Build responsive sites, "
        "CMS-driven content, and e-commerce stores without writing code. Hosting included with "
        "global CDN. Plans start at $14/mo for sites, free plan available for learning.",
        "https://webflow.com",
        "webflow-team",
        "landing-pages",
        "no-code,visual-builder,cms,ecommerce,responsive,hosting",
        1400,  # $14/mo Basic site plan
        135,
    ),
    (
        "Umso",
        "umso",
        "The website builder built specifically for startups",
        "Umso lets founders create professional startup websites without getting lost in details. "
        "Analytics, multilingual sites, forms, blogs, cookie consent, and dozens of integrations "
        "included at no extra cost. Simple per-site pricing starting at $21/mo billed yearly.",
        "https://umso.com",
        "umso-team",
        "landing-pages",
        "startup,website-builder,no-code,landing-page,analytics,forms",
        2100,  # $21/mo Pro plan
        45,
    ),
    (
        "Unicorn Platform",
        "unicorn-platform",
        "AI website builder for busy founders — SaaS, apps, and blogs",
        "Unicorn Platform helps you build landing pages, blogs, and directories with AI assistance. "
        "No design or dev skills needed. Optimized for SaaS products, mobile apps, and personal sites. "
        "Startup plan at $29/mo includes AI builder and unlimited blog posts.",
        "https://unicornplatform.com",
        "unicorn-platform-team",
        "landing-pages",
        "ai-builder,landing-page,blog,saas,no-code,startup",
        2900,  # $29/mo Startup plan
        62,
    ),

    # ── Forms & Surveys ────────────────────────────────────────────────────

    (
        "Heyflow",
        "heyflow",
        "Interactive flow builder that converts visitors into qualified leads",
        "Heyflow lets you build multi-step interactive flows, quizzes, and lead generation forms "
        "with a drag-and-drop editor. Outcome-based pricing that scales with leads, not traffic. "
        "Embeds anywhere. Integrates with CRMs, email tools, and Zapier. Starts at EUR 19/mo.",
        "https://heyflow.com",
        "heyflow-team",
        "forms-surveys",
        "lead-generation,interactive,flows,quizzes,forms,conversion",
        1900,  # ~EUR 19/mo starter
        54,
    ),

    # ── CRM & Sales ────────────────────────────────────────────────────────

    (
        "Twenty CRM",
        "twenty-crm",
        "The #1 open-source CRM — a modern alternative to Salesforce",
        "Twenty is a community-driven open-source CRM backed by Y Combinator. Manage contacts, "
        "companies, and deal pipelines with custom objects and fields. Email integration, API, "
        "webhooks, and a clean modern UI. Self-host free or use Twenty Cloud. 20K+ GitHub stars.",
        "https://twenty.com",
        "twenty-team",
        "crm-sales",
        "crm,open-source,contacts,pipeline,deals,self-hosted",
        None,  # Free / open source (cloud plans available)
        128,
    ),
    (
        "Folk CRM",
        "folk-crm",
        "Lightweight CRM for relationship-driven teams",
        "Folk is a CRM that feels like a spreadsheet but works like a pipeline. Import contacts "
        "from Gmail, LinkedIn, and X with the folkX Chrome extension. AI-powered Magic Fields, "
        "6,000+ integrations, and multi-step email sequences. From $20/user/mo.",
        "https://folk.app",
        "folk-team",
        "crm-sales",
        "crm,contacts,relationships,email-sequences,integrations,lightweight",
        2000,  # $20/user/mo Standard plan
        76,
    ),
    (
        "Attio",
        "attio",
        "Next-generation CRM with flexible data models and real-time collaboration",
        "Attio is a CRM that molds to your business. Custom objects, associations, and workflow "
        "automations with a clean modern UI. Real-time collaboration, email sync, calendar integration, "
        "data enrichment, and AI-powered insights. Free for up to 3 users, Plus from $36/user/mo.",
        "https://attio.com",
        "attio-team",
        "crm-sales",
        "crm,custom-objects,automations,collaboration,enrichment,ai",
        3600,  # $36/user/mo Plus plan
        103,
    ),

    # ── File Management ────────────────────────────────────────────────────

    (
        "UploadThing",
        "uploadthing",
        "File uploads for full-stack TypeScript — simple, fast, type-safe",
        "UploadThing makes file uploads trivial for Next.js and TypeScript apps. "
        "No seats, no request charges, no bandwidth fees — just pay for storage used. "
        "Free tier with 2GB, paid plans from $25/mo with 250GB. Built by the Ping.gg team.",
        "https://uploadthing.com",
        "uploadthing-team",
        "file-management",
        "file-upload,typescript,nextjs,storage,s3-alternative,developer-tools",
        2500,  # $25/mo
        87,
    ),
    (
        "ImageKit",
        "imagekit",
        "Real-time image and video optimization with global CDN delivery",
        "ImageKit provides URL-based image transformations, automatic format optimization, "
        "and a global CDN for fast delivery. Resize, crop, watermark, and convert images on the fly. "
        "AI-powered DAM included. Free plan available, paid from $89/mo.",
        "https://imagekit.io",
        "imagekit-team",
        "file-management",
        "images,cdn,optimization,transformation,video,dam",
        8900,  # $89/mo
        68,
    ),
    (
        "Cloudinary",
        "cloudinary",
        "Image and video API platform for web and mobile developers",
        "Cloudinary handles image and video upload, storage, optimization, and delivery at scale. "
        "URL-based transformations, AI-powered tagging, responsive images, and video transcoding. "
        "Generous free tier with 25 credits/mo. Trusted by over 1.5 million developers worldwide.",
        "https://cloudinary.com",
        "cloudinary-team",
        "file-management",
        "images,video,cdn,optimization,transformation,upload,ai",
        9900,  # ~$99/mo Plus plan
        115,
    ),

    # ── Monitoring & Uptime ────────────────────────────────────────────────

    (
        "OpenStatus",
        "openstatus",
        "Open-source status pages and uptime monitoring from 28 regions",
        "OpenStatus monitors your websites and APIs from 28 global regions across Fly.io, Koyeb, "
        "and Railway. Instant alerts via email, SMS, Slack, and Discord. Beautiful branded status pages. "
        "Bootstrapped and open-source — self-host with a single 8.5MB Docker image or use the cloud.",
        "https://openstatus.dev",
        "openstatus-team",
        "monitoring-uptime",
        "uptime,status-page,monitoring,open-source,alerts,multi-region",
        None,  # Free tier, paid plans available
        78,
    ),

    # ── AI & Automation ────────────────────────────────────────────────────

    (
        "Dify",
        "dify",
        "Open-source platform for building LLM apps with visual workflows",
        "Dify combines a visual workflow builder, RAG pipelines, agent framework, and prompt management "
        "into one platform. Supports 100+ LLMs including GPT, Claude, Llama, and Mistral. "
        "50+ built-in tools for AI agents. Over 100K apps built. Self-host or use Dify Cloud.",
        "https://dify.ai",
        "dify-team",
        "ai-automation",
        "llm,agents,rag,workflows,visual-builder,open-source,ai",
        None,  # Free tier / open source
        138,
    ),
    (
        "Langfuse",
        "langfuse",
        "Open-source LLM observability — traces, evals, and prompt management",
        "Langfuse gives you full visibility into your LLM application with traces, latency monitoring, "
        "cost tracking, and evaluation pipelines. Prompt versioning, playground, and dataset management. "
        "Integrates with OpenAI, LangChain, LlamaIndex, and OpenTelemetry. YC W23. Acquired by ClickHouse.",
        "https://langfuse.com",
        "langfuse-team",
        "ai-automation",
        "llm,observability,tracing,evals,prompts,open-source,ai",
        None,  # Free tier / open source
        119,
    ),
    (
        "Helicone",
        "helicone",
        "Open-source LLM monitoring with one-line integration",
        "Helicone provides LLM observability with a single line of code. Monitor requests, track costs, "
        "manage rate limits, cache responses, and analyze prompt performance across 100+ models. "
        "10K free requests/mo. Gateway and async logging modes. YC W23.",
        "https://helicone.ai",
        "helicone-team",
        "ai-automation",
        "llm,monitoring,cost-tracking,caching,analytics,open-source,ai",
        None,  # Free tier
        92,
    ),
]


# ── Replaces mappings ──────────────────────────────────────────────────────
REPLACES = {
    "workos": "Auth0, Okta, Firebase Auth, Cognito",
    "stytch": "Auth0, Firebase Auth, Cognito, Okta",
    "descope": "Auth0, Okta, Firebase Auth, FusionAuth",
    "chargebee": "Stripe Billing, Recurly, Zuora, Paddle",
    "dokku": "Heroku, Railway, Render, Fly.io",
    "caprover": "Heroku, Railway, Render, Dokku",
    "pocketbase": "Firebase, Supabase, Parse, Appwrite",
    "webflow": "WordPress, Squarespace, Wix, Framer",
    "umso": "Squarespace, Carrd, WordPress, Wix",
    "unicorn-platform": "Squarespace, Carrd, WordPress, Webflow",
    "heyflow": "Typeform, Leadpages, Unbounce, Tally",
    "twenty-crm": "Salesforce, HubSpot, Pipedrive, Zoho CRM",
    "folk-crm": "HubSpot, Pipedrive, Salesforce, Notion CRM",
    "attio": "HubSpot, Salesforce, Pipedrive, Close",
    "uploadthing": "AWS S3, Cloudinary, Firebase Storage, Uploadcare",
    "imagekit": "Cloudinary, Imgix, Fastly Image Optimizer",
    "cloudinary": "Imgix, ImageKit, AWS CloudFront, Fastly",
    "openstatus": "BetterStack, Datadog, Pingdom, UptimeRobot",
    "dify": "LangChain, Flowise, Botpress, OpenAI Assistants",
    "langfuse": "Datadog LLM, Weights & Biases, Arize AI, Helicone",
    "helicone": "Langfuse, Datadog LLM, Weights & Biases, Portkey",
}


def main():
    print(f"Seeding more tools at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Ensure replaces column exists
    try:
        conn.execute("SELECT replaces FROM tools LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE tools ADD COLUMN replaces TEXT NOT NULL DEFAULT ''")
        conn.commit()

    # ── Build category lookup ──────────────────────────────────────────────
    cat_map = {}
    for row in conn.execute("SELECT id, slug FROM categories").fetchall():
        cat_map[row[1]] = row[0]
    print(f"  Categories loaded: {len(cat_map)}")

    if not cat_map:
        print("  ERROR: No categories found. Run seed_tools.py first.")
        conn.close()
        return

    # ── Insert makers ──────────────────────────────────────────────────────
    maker_inserted = 0
    for slug, name, url, bio, indie_status in MAKERS:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO makers (slug, name, url, bio, indie_status) VALUES (?, ?, ?, ?, ?)",
            (slug, name, url, bio, indie_status),
        )
        if cursor.rowcount:
            maker_inserted += 1
    conn.commit()
    print(f"  Makers: {maker_inserted} new")

    # Build maker slug -> id lookup
    maker_map = {}
    for row in conn.execute("SELECT id, slug FROM makers").fetchall():
        maker_map[row[1]] = row[0]

    # ── Insert tools ───────────────────────────────────────────────────────
    inserted = 0
    skipped = 0

    for (name, slug, tagline, description, url, maker_slug, category_slug, tags,
         price_pence, upvotes) in TOOLS:

        category_id = cat_map.get(category_slug)
        if not category_id:
            print(f"  WARNING: Unknown category '{category_slug}' for '{name}', skipping")
            skipped += 1
            continue

        maker_id = maker_map.get(maker_slug) if maker_slug else None
        maker_name = ""
        maker_url = ""
        if maker_id:
            maker_row = conn.execute(
                "SELECT name, url FROM makers WHERE id = ?", (maker_id,)
            ).fetchone()
            if maker_row:
                maker_name = maker_row[0]
                maker_url = maker_row[1]

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

    # ── Backfill replaces ──────────────────────────────────────────────────
    updated = 0
    for slug, replaces in REPLACES.items():
        cursor = conn.execute(
            "UPDATE tools SET replaces = ? WHERE slug = ? AND (replaces IS NULL OR replaces = '')",
            (replaces, slug),
        )
        if cursor.rowcount:
            updated += 1
    conn.commit()
    print(f"  Replaces: backfilled {updated} tools with competitor data.")

    # Count results
    total = conn.execute("SELECT count(*) FROM tools").fetchone()[0]
    print(f"  Tools inserted this run: {inserted} new ({skipped} skipped)")
    print(f"  Total tools in DB: {total}")

    # ── Rebuild FTS indexes ────────────────────────────────────────────────
    print("  Rebuilding FTS indexes...")
    try:
        conn.execute("INSERT INTO tools_fts(tools_fts) VALUES('rebuild')")
        conn.commit()
        print("  tools_fts rebuild complete.")
    except Exception as e:
        print(f"  tools_fts rebuild skipped: {e}")

    try:
        conn.execute("INSERT INTO makers_fts(makers_fts) VALUES('rebuild')")
        conn.commit()
        print("  makers_fts rebuild complete.")
    except Exception as e:
        print(f"  makers_fts rebuild skipped: {e}")

    conn.close()
    print(f"Done! {len(TOOLS)} tools defined, {len(MAKERS)} makers defined.")


if __name__ == "__main__":
    main()

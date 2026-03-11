#!/usr/bin/env python3
"""Seed IndieStack with tools to fill MCP coverage gaps.

These are tools developers commonly try to build from scratch —
exactly the scenarios where the MCP server should say "use this instead."

Covers: Project Management, File Management, Scheduling & Booking,
Forms & Surveys, Authentication, CRM & Sales, API Tools, SEO Tools,
Social Media, Design & Creative.

Usage:
    python3 seed_mcp_coverage.py

Idempotent — uses INSERT OR IGNORE on unique slugs.
All tools assigned to Community Curated maker (id 163).
"""

import sqlite3
import os

# Match the DB path from db.py
DB_PATH = os.environ.get("INDIESTACK_DB_PATH", "/data/indiestack.db")

# If the production path doesn't exist, fall back to local
if not os.path.exists(os.path.dirname(DB_PATH) or "/data"):
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "indiestack.db")
    os.environ["INDIESTACK_DB_PATH"] = DB_PATH

COMMUNITY_MAKER_ID = 163

# ── Tools ──────────────────────────────────────────────────────────────────
# (name, slug, tagline, description, url, category_slug, tags, replaces)
TOOLS = [
    # ── Project Management ─────────────────────────────────────────────────
    (
        "Plane",
        "plane",
        "Open-source project management. Jira alternative.",
        "Plane is an open-source project tracking tool built for software teams. "
        "Issue tracking, cycles, modules, and views with a clean modern UI. "
        "Self-host for free or use the managed cloud.",
        "https://plane.so",
        "project-management",
        "project-management,issue-tracking,open-source,self-hosted,agile",
        "Jira,Linear",
    ),
    (
        "Huly",
        "huly",
        "All-in-one project management with time tracking. Open source.",
        "Huly is an open-source all-in-one project management platform. "
        "Combines issue tracking, time tracking, knowledge base, and team chat "
        "in a single tool. Fast, modern UI with real-time collaboration.",
        "https://huly.io",
        "project-management",
        "project-management,time-tracking,open-source,collaboration,knowledge-base",
        "Jira,Notion,Asana",
    ),
    (
        "Focalboard",
        "focalboard",
        "Open-source Trello/Notion/Asana alternative by Mattermost.",
        "Focalboard is an open-source project management tool from the Mattermost team. "
        "Kanban boards, table views, gallery views, and calendar views for organizing "
        "tasks and projects. Self-host or run locally.",
        "https://focalboard.com",
        "project-management",
        "project-management,kanban,open-source,self-hosted,mattermost",
        "Trello,Notion,Asana",
    ),
    # ── File Management ────────────────────────────────────────────────────
    (
        "MinIO",
        "minio",
        "High-performance S3-compatible object storage. Open source.",
        "MinIO is a high-performance, S3-compatible object storage system. "
        "Built for large-scale AI/ML, data lake, and cloud-native workloads. "
        "Run anywhere — bare metal, Kubernetes, or Docker.",
        "https://min.io",
        "file-management",
        "object-storage,s3,open-source,self-hosted,cloud-native",
        "AWS S3",
    ),
    (
        "Nextcloud",
        "nextcloud",
        "Self-hosted file sync, share, and collaboration platform.",
        "Nextcloud is a self-hosted productivity platform that replaces Dropbox, "
        "Google Drive, and Office 365. File sync, document editing, calendars, "
        "contacts, video calls, and more. Full control over your data.",
        "https://nextcloud.com",
        "file-management",
        "file-sync,self-hosted,open-source,collaboration,cloud-storage",
        "Dropbox,Google Drive",
    ),
    # ── Scheduling & Booking ───────────────────────────────────────────────
    (
        "Cal.com",
        "cal-com",
        "Open-source Calendly alternative. Self-hostable.",
        "Cal.com is the open-source scheduling infrastructure. Create booking pages, "
        "round-robin routing, team scheduling, and workflows. Self-host for free "
        "or use the managed platform. API-first with 100+ integrations.",
        "https://cal.com",
        "scheduling-booking",
        "scheduling,booking,open-source,self-hosted,calendly-alternative",
        "Calendly",
    ),
    (
        "Easy Appointments",
        "easy-appointments",
        "Self-hosted appointment scheduling. Simple and free.",
        "Easy!Appointments is a free, open-source web application for appointment scheduling. "
        "Customers book online, staff manage schedules from the backend. Supports "
        "Google Calendar sync, email notifications, and multiple services.",
        "https://easyappointments.org",
        "scheduling-booking",
        "scheduling,appointments,open-source,self-hosted,booking",
        "Calendly,Acuity",
    ),
    # ── Forms & Surveys ────────────────────────────────────────────────────
    (
        "Formbricks",
        "formbricks",
        "Open-source survey platform. Typeform alternative.",
        "Formbricks is an open-source experience management platform. "
        "In-app surveys, link surveys, and website surveys with targeting and "
        "segmentation. Self-host or use the cloud. GDPR-compliant by design.",
        "https://formbricks.com",
        "forms-surveys",
        "surveys,forms,open-source,self-hosted,typeform-alternative",
        "Typeform,SurveyMonkey",
    ),
    (
        "Tally",
        "tally",
        "Simple form builder with a Notion-like editor. Free tier.",
        "Tally is a form builder that works like a document. Type your questions "
        "like you would in Notion, and Tally turns them into beautiful forms. "
        "Unlimited forms and submissions on the free plan. No coding required.",
        "https://tally.so",
        "forms-surveys",
        "forms,surveys,no-code,free,notion-like",
        "Typeform,Google Forms",
    ),
    # ── Authentication ─────────────────────────────────────────────────────
    (
        "Logto",
        "logto",
        "Open-source Auth0 alternative with RBAC and multi-tenancy.",
        "Logto is an open-source identity solution for modern apps. Social sign-in, "
        "passwordless authentication, RBAC, multi-tenancy, and organization support "
        "out of the box. Self-host or use the managed cloud with a generous free tier.",
        "https://logto.io",
        "authentication",
        "auth,open-source,sso,rbac,multi-tenancy",
        "Auth0,Okta",
    ),
    (
        "Hanko",
        "hanko",
        "Passkey-first authentication. Open source.",
        "Hanko provides passkey-first authentication for web and mobile apps. "
        "Drop-in web components for login, registration, and profile management. "
        "Open source with a focus on passwordless UX and WebAuthn standards.",
        "https://hanko.io",
        "authentication",
        "auth,passkeys,open-source,passwordless,webauthn",
        "Auth0",
    ),
    # ── CRM & Sales ────────────────────────────────────────────────────────
    (
        "Twenty",
        "twenty",
        "Open-source CRM. Modern Salesforce alternative.",
        "Twenty is an open-source CRM with a modern, beautiful UI. "
        "Manage contacts, companies, deals, and tasks. Built with a "
        "flexible data model and API-first approach. Self-host or use cloud.",
        "https://twenty.com",
        "crm-sales",
        "crm,open-source,self-hosted,sales,contacts",
        "Salesforce,HubSpot",
    ),
    (
        "Erxes",
        "erxes",
        "Open-source experience management: CRM, marketing, support.",
        "Erxes is an open-source experience management platform that combines "
        "CRM, marketing automation, and customer support in one system. "
        "Plugin-based architecture lets you pick only the modules you need.",
        "https://erxes.io",
        "crm-sales",
        "crm,marketing,support,open-source,all-in-one",
        "Salesforce,HubSpot,Intercom",
    ),
    # ── API Tools ──────────────────────────────────────────────────────────
    (
        "Hoppscotch",
        "hoppscotch",
        "Open-source API development ecosystem. Postman alternative.",
        "Hoppscotch is an open-source API development platform. REST, GraphQL, "
        "WebSocket, SSE, and Socket.IO testing in a lightweight, fast web app. "
        "Team collaboration, environments, and collections. Self-hostable.",
        "https://hoppscotch.io",
        "api-tools",
        "api,testing,open-source,rest,graphql",
        "Postman",
    ),
    (
        "Insomnia",
        "insomnia",
        "API design, debug, and test. Open-source core.",
        "Insomnia is an API client for designing, debugging, and testing APIs. "
        "Supports REST, GraphQL, gRPC, and WebSockets. Built-in environment "
        "management, code generation, and Git sync. Open-source core by Kong.",
        "https://insomnia.rest",
        "api-tools",
        "api,testing,open-source,rest,graphql",
        "Postman",
    ),
    # ── SEO Tools (analytics) ─────────────────────────────────────────────
    (
        "Matomo",
        "matomo",
        "Privacy-focused web analytics. Google Analytics alternative.",
        "Matomo is the leading open-source web analytics platform. Full ownership "
        "of your data with no sampling. Heatmaps, session recordings, A/B testing, "
        "and funnels. Self-host for free or use the managed cloud. GDPR-compliant.",
        "https://matomo.org",
        "seo-tools",
        "analytics,privacy,open-source,self-hosted,gdpr",
        "Google Analytics",
    ),
    (
        "Umami",
        "umami",
        "Simple, fast, privacy-focused web analytics. Open source.",
        "Umami is a lightweight, open-source web analytics tool. No cookies, "
        "no tracking scripts, fully GDPR-compliant. Beautiful dashboard with "
        "real-time data. Self-host on any platform in minutes.",
        "https://umami.is",
        "seo-tools",
        "analytics,privacy,open-source,lightweight,self-hosted",
        "Google Analytics",
    ),
    # ── Social Media ───────────────────────────────────────────────────────
    (
        "Mastodon",
        "mastodon",
        "Decentralized social network. Open source. Self-hostable.",
        "Mastodon is a free, open-source decentralized social network. "
        "Run your own server or join an existing one. No ads, no algorithms, "
        "no corporate surveillance. Federated via ActivityPub.",
        "https://joinmastodon.org",
        "social-media",
        "social-network,decentralized,open-source,fediverse,activitypub",
        "Twitter",
    ),
    (
        "Pixelfed",
        "pixelfed",
        "Decentralized photo sharing. Instagram alternative. Open source.",
        "Pixelfed is a free, open-source photo sharing platform. "
        "No ads, no algorithms, no data mining. Beautiful feed with stories, "
        "collections, and discover features. Federated via ActivityPub.",
        "https://pixelfed.org",
        "social-media",
        "photo-sharing,decentralized,open-source,fediverse,instagram-alternative",
        "Instagram",
    ),
    # ── Design & Creative ──────────────────────────────────────────────────
    (
        "Penpot",
        "penpot",
        "Open-source design and prototyping. Figma alternative.",
        "Penpot is the first open-source design and prototyping platform for "
        "cross-domain teams. SVG-native, browser-based, and self-hostable. "
        "Real-time collaboration with no vendor lock-in.",
        "https://penpot.app",
        "design-creative",
        "design,prototyping,open-source,self-hosted,figma-alternative",
        "Figma",
    ),
    (
        "Excalidraw",
        "excalidraw",
        "Virtual whiteboard for hand-drawn diagrams. Open source.",
        "Excalidraw is an open-source virtual whiteboard with a hand-drawn feel. "
        "Perfect for diagrams, wireframes, and brainstorming. Real-time collaboration, "
        "end-to-end encryption, and an extensive shape library.",
        "https://excalidraw.com",
        "design-creative",
        "whiteboard,diagrams,open-source,collaboration,wireframes",
        "Miro,Lucidchart",
    ),
]


def main():
    print(f"Seeding MCP coverage tools at: {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")

    # Ensure replaces column exists
    try:
        conn.execute("SELECT replaces FROM tools LIMIT 1")
    except Exception:
        conn.execute("ALTER TABLE tools ADD COLUMN replaces TEXT NOT NULL DEFAULT ''")
        conn.commit()

    # Build category lookup
    cat_map = {}
    for row in conn.execute("SELECT id, slug FROM categories").fetchall():
        cat_map[row[1]] = row[0]

    # Get Community Curated maker info
    maker_row = conn.execute(
        "SELECT name, url FROM makers WHERE id = ?", (COMMUNITY_MAKER_ID,)
    ).fetchone()
    if not maker_row:
        print(f"  ERROR: Community Curated maker (id {COMMUNITY_MAKER_ID}) not found!")
        conn.close()
        return
    maker_name, maker_url = maker_row

    # ── Insert tools ───────────────────────────────────────────────────────
    inserted = 0
    skipped = 0
    for (name, slug, tagline, description, url, category_slug,
         tags, replaces) in TOOLS:

        category_id = cat_map.get(category_slug)
        if not category_id:
            print(f"  WARNING: Unknown category '{category_slug}' for tool '{name}', skipping")
            skipped += 1
            continue

        try:
            cursor = conn.execute(
                """INSERT OR IGNORE INTO tools
                   (name, slug, tagline, description, url, maker_name, maker_url,
                    category_id, tags, status, is_verified, upvote_count,
                    price_pence, delivery_type, maker_id, replaces)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', 0, 0, NULL, 'link', ?, ?)""",
                (name, slug, tagline, description, url, maker_name, maker_url,
                 category_id, tags, COMMUNITY_MAKER_ID, replaces),
            )
            if cursor.rowcount > 0:
                inserted += 1
                print(f"  + {name} ({category_slug})")
        except Exception as e:
            print(f"  ERROR inserting '{name}': {e}")
            skipped += 1

    conn.commit()

    # ── Rebuild FTS index ──────────────────────────────────────────────────
    print("  Rebuilding FTS index...")
    conn.execute("INSERT INTO tools_fts(tools_fts) VALUES('rebuild')")
    conn.commit()
    print("  FTS rebuild complete.")

    # ── Summary ────────────────────────────────────────────────────────────
    total = conn.execute("SELECT count(*) FROM tools WHERE status = 'approved'").fetchone()[0]
    print(f"\nDone. {inserted} tools added, {skipped} skipped.")
    print(f"Total approved tools: {total}")

    conn.close()


if __name__ == "__main__":
    main()

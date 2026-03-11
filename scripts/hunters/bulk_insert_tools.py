"""Bulk insert micro-tools into IndieStack catalog."""
import sqlite3
from datetime import datetime

tools = [
    # === SCHEDULING & BOOKING (id=6) ===
    {"name": "Rallly", "url": "https://github.com/lukevella/rallly", "tagline": "Open-source scheduling and polling for finding the best time to meet", "category_slug": "scheduling-booking", "tags": "scheduling,polling,self-hosted,open-source,meeting"},
    {"name": "Easy!Appointments", "url": "https://github.com/alextselegidis/easyappointments", "tagline": "Self-hosted appointment scheduler with Google Calendar sync", "category_slug": "scheduling-booking", "tags": "scheduling,appointments,self-hosted,calendar,open-source"},
    {"name": "Cal.com", "url": "https://github.com/calcom/cal.com", "tagline": "Open scheduling infrastructure — the Calendly alternative you own", "category_slug": "scheduling-booking", "tags": "scheduling,calendar,booking,self-hosted,open-source"},

    # === SOCIAL MEDIA (id=7) ===
    {"name": "Postiz", "url": "https://github.com/gitroomhq/postiz-app", "tagline": "Open-source social media scheduling tool with AI features", "category_slug": "social-media", "tags": "social-media,scheduling,open-source,self-hosted,ai"},
    {"name": "Mixpost", "url": "https://github.com/inovector/mixpost", "tagline": "Self-hosted social media management — schedule and publish with no limits", "category_slug": "social-media", "tags": "social-media,scheduling,self-hosted,open-source,buffer-alternative"},
    {"name": "Shoutify", "url": "https://github.com/TechSquidTV/Shoutify", "tagline": "Open-source social media management for creators and small businesses", "category_slug": "social-media", "tags": "social-media,scheduling,open-source,self-hosted"},
    {"name": "Flare", "url": "https://github.com/DimensionDev/Flare", "tagline": "Unified client for Mastodon, Bluesky, Misskey, X, and RSS in one app", "category_slug": "social-media", "tags": "social-media,mastodon,bluesky,rss,open-source"},

    # === SEO TOOLS (id=14) ===
    {"name": "SEOnaut", "url": "https://github.com/StJudeWasHere/seonaut", "tagline": "Open-source SEO audit tool — find broken links, missing tags, and more", "category_slug": "seo-tools", "tags": "seo,audit,self-hosted,open-source,go"},
    {"name": "lychee", "url": "https://github.com/lycheeverse/lychee", "tagline": "Fast async link checker written in Rust for Markdown, HTML, and websites", "category_slug": "seo-tools", "tags": "link-checker,rust,cli,seo,open-source"},
    {"name": "linkcheckmd", "url": "https://github.com/scivision/linkchecker-markdown", "tagline": "Blazing-fast Python link checker for Markdown files — 10k files/sec", "category_slug": "seo-tools", "tags": "link-checker,python,markdown,cli,open-source"},
    {"name": "broken-link-checker", "url": "https://github.com/stevenvachon/broken-link-checker", "tagline": "Find broken links, missing images, and more within your HTML", "category_slug": "seo-tools", "tags": "link-checker,html,nodejs,cli,open-source"},

    # === FORMS & SURVEYS (id=9) ===
    {"name": "Formbricks", "url": "https://github.com/formbricks/formbricks", "tagline": "Open-source survey platform — in-app, website, link, and email surveys", "category_slug": "forms-surveys", "tags": "forms,surveys,open-source,self-hosted,typeform-alternative"},
    {"name": "HeyForm", "url": "https://github.com/heyform/heyform", "tagline": "Open-source form builder for engaging conversational forms", "category_slug": "forms-surveys", "tags": "forms,open-source,self-hosted,no-code"},
    {"name": "Formgate", "url": "https://github.com/formgate/formgate", "tagline": "Self-hosted contact form handler for static websites", "category_slug": "forms-surveys", "tags": "forms,self-hosted,static-site,contact-form,open-source"},
    {"name": "MailBear", "url": "https://github.com/DenBeke/mailbear", "tagline": "Self-hosted forms backend — POST form data, get email notifications", "category_slug": "forms-surveys", "tags": "forms,email,self-hosted,backend,open-source"},
    {"name": "OpenformStack", "url": "https://github.com/naveennaidu/OpenformStack", "tagline": "Open-source form backend — collect submissions without backend code", "category_slug": "forms-surveys", "tags": "forms,backend,open-source,no-code,self-hosted"},
    {"name": "Input", "url": "https://github.com/deck9/input", "tagline": "Privacy-focused, no-code, open-source form builder for brand consistency", "category_slug": "forms-surveys", "tags": "forms,privacy,no-code,open-source,self-hosted"},

    # === FEEDBACK & REVIEWS (id=20) ===
    {"name": "Astuto", "url": "https://github.com/astuto/astuto", "tagline": "Free, open-source, self-hosted customer feedback tool", "category_slug": "feedback-reviews", "tags": "feedback,open-source,self-hosted,customer-feedback"},
    {"name": "Feedback Fin", "url": "https://github.com/rowyio/feedbackfin", "tagline": "Tiny open-source widget to collect feedback anywhere on your website", "category_slug": "feedback-reviews", "tags": "feedback,widget,open-source,lightweight"},
    {"name": "Fider", "url": "https://github.com/getfider/fider", "tagline": "Open platform to collect and prioritize product feedback", "category_slug": "feedback-reviews", "tags": "feedback,open-source,self-hosted,product-feedback"},
    {"name": "Bromb", "url": "https://github.com/samuelstroschein/bromb", "tagline": "Simple, configurable, self-hostable feedback widget for websites", "category_slug": "feedback-reviews", "tags": "feedback,widget,svelte,open-source,self-hosted"},

    # === FILE MANAGEMENT (id=11) ===
    {"name": "csvkit", "url": "https://github.com/wireservice/csvkit", "tagline": "Suite of CLI utilities for converting to and working with CSV files", "category_slug": "file-management", "tags": "csv,cli,python,converter,open-source"},
    {"name": "Vertopal CLI", "url": "https://github.com/vertopal/vertopal-cli", "tagline": "Small yet powerful CLI file conversion utility for many formats", "category_slug": "file-management", "tags": "converter,cli,python,file-format,open-source"},
    {"name": "img2pdf", "url": "https://github.com/josch/img2pdf", "tagline": "Losslessly convert raster images to PDF without re-encoding", "category_slug": "file-management", "tags": "pdf,image,converter,cli,python,open-source"},
    {"name": "pdfsizeopt", "url": "https://github.com/pts/pdfsizeopt", "tagline": "CLI tool to convert large PDFs to small ones without quality loss", "category_slug": "file-management", "tags": "pdf,optimizer,cli,open-source"},
    {"name": "node-csvtojson", "url": "https://github.com/Keyang/node-csvtojson", "tagline": "Blazing fast CSV parser for Node.js, browser, and command line", "category_slug": "file-management", "tags": "csv,json,converter,nodejs,cli,open-source"},

    # === API TOOLS (id=16) ===
    {"name": "Hurl", "url": "https://github.com/Orange-OpenSource/hurl", "tagline": "Run and test HTTP requests defined in simple plain text files", "category_slug": "api-tools", "tags": "http,testing,cli,rust,api,open-source"},
    {"name": "xh", "url": "https://github.com/ducaale/xh", "tagline": "Friendly and fast HTTP request tool — like HTTPie but in Rust", "category_slug": "api-tools", "tags": "http,cli,rust,api,open-source"},
    {"name": "json-server", "url": "https://github.com/typicode/json-server", "tagline": "Full fake REST API with zero coding in less than 30 seconds", "category_slug": "api-tools", "tags": "api,mock,rest,nodejs,json,open-source"},
    {"name": "Mockoon", "url": "https://github.com/mockoon/mockoon", "tagline": "Easiest way to run mock REST APIs locally — no account required", "category_slug": "api-tools", "tags": "api,mock,rest,open-source,desktop"},
    {"name": "httpstat", "url": "https://github.com/reorx/httpstat", "tagline": "Curl statistics made simple — visualize HTTP request timing", "category_slug": "api-tools", "tags": "http,curl,cli,python,diagnostics,open-source"},
    {"name": "Prism", "url": "https://github.com/stoplightio/prism", "tagline": "Turn any OpenAPI spec into a mock API server with validation", "category_slug": "api-tools", "tags": "api,mock,openapi,cli,open-source"},

    # === DEVELOPER TOOLS (id=18) ===
    {"name": "IT-Tools", "url": "https://github.com/CorentinTh/it-tools", "tagline": "100+ handy online tools for developers — self-hostable via Docker", "category_slug": "developer-tools", "tags": "developer,utilities,self-hosted,converter,open-source"},
    {"name": "miniserve", "url": "https://github.com/svenstaro/miniserve", "tagline": "Single-binary CLI to serve files over HTTP right now — written in Rust", "category_slug": "developer-tools", "tags": "http-server,cli,rust,file-sharing,open-source"},

    # === EMAIL MARKETING (id=2) ===
    {"name": "Listmonk", "url": "https://listmonk.app/", "tagline": "High-performance self-hosted newsletter and mailing list manager", "category_slug": "email-marketing", "tags": "newsletter,email,self-hosted,open-source,golang"},
    {"name": "Keila", "url": "https://www.keila.io/", "tagline": "Open source email newsletters, easy and reliable", "category_slug": "email-marketing", "tags": "newsletter,email,self-hosted,open-source,elixir"},
    {"name": "Plunk", "url": "https://www.useplunk.com/", "tagline": "Open-source email platform for transactional and marketing emails", "category_slug": "email-marketing", "tags": "transactional-email,email-api,open-source,typescript"},
    {"name": "MailWhale", "url": "https://github.com/muety/mailwhale", "tagline": "Bring-your-own-SMTP mail relay with REST API and web UI", "category_slug": "email-marketing", "tags": "transactional-email,smtp,rest-api,self-hosted,golang"},
    {"name": "SendPortal", "url": "https://sendportal.io/", "tagline": "Open-source self-hosted email marketing at a fraction of the cost", "category_slug": "email-marketing", "tags": "email-marketing,newsletter,self-hosted,laravel,open-source"},
    {"name": "Cuttlefish", "url": "https://cuttlefish.io/", "tagline": "Lovely transactional email with tracking and bounce handling", "category_slug": "email-marketing", "tags": "transactional-email,tracking,self-hosted,open-source,ruby"},

    # === PAYMENTS (id=13) ===
    {"name": "Lago", "url": "https://www.getlago.com/", "tagline": "Open-source metering and usage-based billing API", "category_slug": "payments", "tags": "billing,metering,usage-based,api,open-source"},
    {"name": "InvoiceShelf", "url": "https://invoiceshelf.com/", "tagline": "Open-source invoicing solution for individuals and businesses", "category_slug": "payments", "tags": "invoicing,billing,self-hosted,laravel,open-source"},
    {"name": "SolidInvoice", "url": "https://github.com/SolidInvoice/SolidInvoice", "tagline": "Simple and elegant open-source invoicing solution", "category_slug": "payments", "tags": "invoicing,billing,freelancer,self-hosted,open-source"},
    {"name": "BillaBear", "url": "https://github.com/billabear/billabear", "tagline": "Subscription management and billing system with tax support", "category_slug": "payments", "tags": "subscription,billing,payments,self-hosted,open-source"},
    {"name": "Meteroid", "url": "https://github.com/meteroid-oss/meteroid", "tagline": "Open-source pricing and billing infrastructure for SaaS", "category_slug": "payments", "tags": "billing,pricing,subscription,usage-based,open-source"},

    # === AUTHENTICATION (id=12) ===
    {"name": "Logto", "url": "https://logto.io/", "tagline": "Open-source auth infrastructure with OIDC, SSO, and RBAC built in", "category_slug": "authentication", "tags": "auth,sso,oidc,self-hosted,open-source,typescript"},
    {"name": "SuperTokens", "url": "https://supertokens.com/", "tagline": "Open-source alternative to Auth0 and Firebase Auth", "category_slug": "authentication", "tags": "auth,login,self-hosted,open-source,passwordless"},
    {"name": "Authelia", "url": "https://github.com/authelia/authelia", "tagline": "Single sign-on multi-factor portal for web apps", "category_slug": "authentication", "tags": "sso,mfa,auth,self-hosted,open-source,golang"},
    {"name": "Better Auth", "url": "https://github.com/better-auth/better-auth", "tagline": "Comprehensive authentication framework for TypeScript", "category_slug": "authentication", "tags": "auth,typescript,framework,open-source"},

    # === CRM & SALES (id=10) ===
    {"name": "Twenty", "url": "https://twenty.com/", "tagline": "Modern open-source CRM, a community-powered Salesforce alternative", "category_slug": "crm-sales", "tags": "crm,sales,contacts,self-hosted,open-source"},
    {"name": "Krayin", "url": "https://krayincrm.com/", "tagline": "Free open-source Laravel CRM for small and medium businesses", "category_slug": "crm-sales", "tags": "crm,laravel,sales,pipeline,open-source"},
    {"name": "Erxes", "url": "https://erxes.io/", "tagline": "Open-source experience OS unifying marketing, sales, and support", "category_slug": "crm-sales", "tags": "crm,marketing,sales,support,open-source,typescript"},

    # === CUSTOMER SUPPORT (id=5) ===
    {"name": "Peppermint", "url": "https://peppermint.sh/", "tagline": "Lightweight open-source helpdesk and ticketing system", "category_slug": "customer-support", "tags": "helpdesk,ticketing,self-hosted,open-source,lightweight"},
    {"name": "FreeScout", "url": "https://freescout.net/", "tagline": "Super lightweight free open-source helpdesk and shared inbox", "category_slug": "customer-support", "tags": "helpdesk,shared-inbox,email,self-hosted,open-source,php"},
    {"name": "Chatwoot", "url": "https://www.chatwoot.com/", "tagline": "Open-source customer support platform with omnichannel messaging", "category_slug": "customer-support", "tags": "live-chat,helpdesk,omnichannel,self-hosted,open-source"},
    {"name": "Trudesk", "url": "https://trudesk.io/", "tagline": "Open-source help desk and ticketing solution built with Node.js", "category_slug": "customer-support", "tags": "helpdesk,ticketing,nodejs,self-hosted,open-source"},
    {"name": "Papercups", "url": "https://github.com/papercups-io/papercups", "tagline": "Open-source live customer chat widget built with Elixir", "category_slug": "customer-support", "tags": "live-chat,widget,elixir,self-hosted,open-source"},

    # === PROJECT MANAGEMENT (id=4) ===
    {"name": "Planka", "url": "https://planka.app/", "tagline": "Realtime kanban board for workgroups, self-hosted Trello alternative", "category_slug": "project-management", "tags": "kanban,trello-alternative,self-hosted,open-source,react"},
    {"name": "Kanboard", "url": "https://kanboard.org/", "tagline": "Minimalist open-source kanban project management software", "category_slug": "project-management", "tags": "kanban,minimal,self-hosted,open-source,php"},
    {"name": "WeKan", "url": "https://wekan.github.io/", "tagline": "Privacy-focused open-source kanban board with full data control", "category_slug": "project-management", "tags": "kanban,trello-alternative,privacy,self-hosted,open-source"},

    # === MONITORING & UPTIME (id=15) ===
    {"name": "Uptime Kuma", "url": "https://github.com/louislam/uptime-kuma", "tagline": "Fancy self-hosted monitoring tool with beautiful UI", "category_slug": "monitoring-uptime", "tags": "uptime,monitoring,status-page,self-hosted,open-source"},
    {"name": "Upptime", "url": "https://github.com/upptime/upptime", "tagline": "GitHub Actions-powered uptime monitor and status page, no server needed", "category_slug": "monitoring-uptime", "tags": "uptime,status-page,github-actions,serverless,open-source"},
    {"name": "cState", "url": "https://github.com/cstate/cstate", "tagline": "Static serverless status page built with Hugo, blazing fast", "category_slug": "monitoring-uptime", "tags": "status-page,hugo,static-site,serverless,open-source"},
    {"name": "Kener", "url": "https://kener.ing/", "tagline": "Stunning self-hosted status pages with monitoring, batteries included", "category_slug": "monitoring-uptime", "tags": "status-page,monitoring,svelte,self-hosted,open-source"},
    {"name": "Vigil", "url": "https://github.com/valeriansaliou/vigil", "tagline": "Microservices status page that monitors infrastructure and sends alerts", "category_slug": "monitoring-uptime", "tags": "status-page,monitoring,alerts,rust,self-hosted,open-source"},
    {"name": "OpenStatus", "url": "https://www.openstatus.dev/", "tagline": "Open-source synthetic monitoring platform with status pages", "category_slug": "monitoring-uptime", "tags": "uptime,monitoring,status-page,api-monitoring,open-source"},
    {"name": "Checkmate", "url": "https://github.com/bluewave-labs/Checkmate", "tagline": "Self-hosted uptime and server hardware monitoring with beautiful visuals", "category_slug": "monitoring-uptime", "tags": "uptime,monitoring,server,self-hosted,open-source,react"},

    # === AI & AUTOMATION (id=19) ===
    {"name": "Activepieces", "url": "https://www.activepieces.com/", "tagline": "Open-source no-code business automation, Zapier alternative", "category_slug": "ai-automation", "tags": "automation,no-code,zapier-alternative,self-hosted,open-source"},
    {"name": "Automatisch", "url": "https://automatisch.io/", "tagline": "Open-source Zapier alternative for workflow automation", "category_slug": "ai-automation", "tags": "automation,workflow,zapier-alternative,self-hosted,open-source"},
    {"name": "Trigger.dev", "url": "https://trigger.dev/", "tagline": "Open-source background jobs and AI agent infrastructure for TypeScript", "category_slug": "ai-automation", "tags": "background-jobs,automation,ai-agents,typescript,open-source"},
    {"name": "Mastra", "url": "https://github.com/mastra-ai/mastra", "tagline": "TypeScript framework for building AI agents with memory and tools", "category_slug": "ai-automation", "tags": "ai-agents,typescript,framework,rag,open-source"},
]


def slugify(name):
    import re
    s = name.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    return s


def main():
    db = sqlite3.connect("/data/indiestack.db")
    db.row_factory = sqlite3.Row

    # Build category slug -> id map
    cats = {r['slug']: r['id'] for r in db.execute("SELECT id, slug FROM categories").fetchall()}

    # Get existing tool slugs and URLs to avoid duplicates
    existing_slugs = {r[0] for r in db.execute("SELECT slug FROM tools").fetchall()}
    existing_urls = {r[0].lower() for r in db.execute("SELECT url FROM tools WHERE url IS NOT NULL").fetchall()}
    existing_names = {r[0].lower() for r in db.execute("SELECT name FROM tools").fetchall()}

    now = datetime.utcnow().isoformat()
    added = 0
    skipped = 0

    for t in tools:
        slug = slugify(t['name'])
        cat_id = cats.get(t['category_slug'])
        if not cat_id:
            print(f"  SKIP {t['name']}: unknown category {t['category_slug']}")
            skipped += 1
            continue

        # Skip duplicates by slug, URL, or name
        if slug in existing_slugs:
            print(f"  SKIP {t['name']}: slug '{slug}' exists")
            skipped += 1
            continue
        if t['url'].lower() in existing_urls:
            print(f"  SKIP {t['name']}: URL exists")
            skipped += 1
            continue
        if t['name'].lower() in existing_names:
            print(f"  SKIP {t['name']}: name exists")
            skipped += 1
            continue

        db.execute(
            """INSERT INTO tools (name, slug, tagline, url, category_id, tags, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, 'approved', ?)""",
            (t['name'], slug, t['tagline'], t['url'], cat_id, t['tags'], now)
        )
        existing_slugs.add(slug)
        existing_urls.add(t['url'].lower())
        existing_names.add(t['name'].lower())
        added += 1
        print(f"  ADD  {t['name']} -> {slug} (cat={t['category_slug']})")

    db.commit()
    total = db.execute("SELECT COUNT(*) FROM tools WHERE status='approved'").fetchone()[0]
    print(f"\nDone! Added: {added}, Skipped: {skipped}, Total approved tools: {total}")


if __name__ == "__main__":
    main()

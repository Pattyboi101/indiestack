#!/usr/bin/env python3
"""Seed the IndieStack database with ~59 real indie/dev tools (Round 4).

Usage:
    python3 seed_round4.py

Idempotent — safe to run multiple times. Uses INSERT OR IGNORE on unique slugs.
All tools are auto-approved with realistic upvote counts.

Categories covered: Hosting/Deploy, Monitoring, Customer Support, Email,
CMS/Headless, Auth, Vector DBs, Databases, CI/CD, Web Servers, Background Jobs,
Scraping/API, Feature Flags, SaaS Boilerplates, i18n, Audio, AI Inference,
Ecommerce, Invoicing, Low-Code, Project Management, Scheduling, BaaS.
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
    # Hosting / Deploy
    ("coolify-team", "Coolify", "https://coolify.io",
     "Open-source, self-hostable Heroku/Vercel/Netlify alternative.", "small_team"),
    ("northflank-team", "Northflank", "https://northflank.com",
     "Full-stack cloud platform for containerised apps.", "small_team"),

    # Monitoring & Uptime
    ("signoz-team", "SigNoz", "https://signoz.io",
     "Open-source APM with logs, traces, and metrics. OpenTelemetry-native.", "small_team"),
    ("uptrace-team", "Uptrace", "https://uptrace.dev",
     "Open-source APM built on OpenTelemetry and ClickHouse.", "small_team"),
    ("glitchtip-team", "GlitchTip", "https://glitchtip.com",
     "Simple open-source error tracking. Sentry-compatible.", "small_team"),
    ("incident-io-team", "incident.io", "https://incident.io",
     "Slack-native incident management for engineering teams.", "small_team"),

    # Customer Support
    ("chatwoot-team", "Chatwoot", "https://www.chatwoot.com",
     "Open-source omnichannel customer support platform.", "small_team"),
    ("mattermost-team", "Mattermost", "https://mattermost.com",
     "Open-source team messaging and collaboration platform.", "small_team"),

    # Email
    ("resend-team", "Resend", "https://resend.com",
     "Email API for developers. Built for great deliverability.", "small_team"),
    ("loops-team", "Loops", "https://loops.so",
     "Email platform for SaaS — transactional + marketing in one.", "small_team"),
    ("postmark-team", "Postmark", "https://postmarkapp.com",
     "Fast, reliable transactional email with best-in-class deliverability.", "small_team"),

    # CMS / Headless
    ("ghost-team", "Ghost", "https://ghost.org",
     "Open-source publishing platform for blogs and newsletters.", "small_team"),
    ("strapi-team", "Strapi", "https://strapi.io",
     "Leading open-source headless CMS for developers.", "small_team"),
    ("payload-cms-team", "Payload CMS", "https://payloadcms.com",
     "Code-first headless CMS built with TypeScript.", "small_team"),
    ("tinacms-team", "TinaCMS", "https://tina.io",
     "Git-backed headless CMS with visual editing.", "small_team"),

    # Authentication
    ("authentik-team", "Authentik", "https://goauthentik.io",
     "Self-hosted identity provider — SSO, LDAP, OAuth, SAML.", "small_team"),
    ("hanko-team", "Hanko", "https://www.hanko.io",
     "Passkey-first authentication API for modern apps.", "small_team"),
    ("logto-team", "Logto", "https://logto.io",
     "Auth infrastructure for SaaS — SSO, MFA, multi-tenant.", "small_team"),

    # Vector Databases
    ("qdrant-team", "Qdrant", "https://qdrant.tech",
     "High-performance vector database written in Rust.", "small_team"),
    ("chroma-team", "Chroma", "https://www.trychroma.com",
     "Open-source embedding database for AI apps.", "small_team"),
    ("weaviate-team", "Weaviate", "https://weaviate.io",
     "AI-native vector database with hybrid search.", "small_team"),

    # Databases & Data
    ("drizzle-team", "Drizzle Team", "https://orm.drizzle.team",
     "TypeScript ORM that feels like SQL — tiny and fast.", "small_team"),
    ("neon-team", "Neon", "https://neon.com",
     "Serverless Postgres with scale-to-zero and branching.", "small_team"),
    ("turso-team", "Turso", "https://turso.tech",
     "Edge SQLite database — embed or deploy globally.", "small_team"),
    ("upstash-team", "Upstash", "https://upstash.com",
     "Serverless Redis and Kafka — pay per request.", "small_team"),
    ("airbyte-team", "Airbyte", "https://airbyte.com",
     "Open-source data integration platform with 600+ connectors.", "small_team"),

    # CI/CD & DevOps
    ("woodpecker-ci-team", "Woodpecker CI", "https://woodpecker-ci.org",
     "Simple self-hosted CI/CD with Docker-native pipelines.", "small_team"),
    ("caddy-team", "Caddy", "https://caddyserver.com",
     "Web server with automatic HTTPS — simpler than Nginx.", "solo"),
    ("traefik-team", "Traefik Labs", "https://traefik.io",
     "Cloud-native reverse proxy and load balancer.", "small_team"),
    ("portainer-team", "Portainer", "https://www.portainer.io",
     "Container management UI for Docker and Kubernetes.", "small_team"),

    # Background Jobs & Workflows
    ("trigger-dev-team", "Trigger.dev", "https://trigger.dev",
     "Build and deploy fully-managed background jobs in code.", "small_team"),
    ("inngest-team", "Inngest", "https://www.inngest.com",
     "AI and backend workflows orchestrated at any scale.", "small_team"),

    # Scraping & APIs
    ("scrapingbee-team", "ScrapingBee", "https://www.scrapingbee.com",
     "Web scraping API with proxies and headless browsers.", "small_team"),
    ("screenshotone-team", "ScreenshotOne", "https://screenshotone.com",
     "Screenshot API — render any URL to image or PDF.", "solo"),
    ("microlink-team", "Microlink", "https://microlink.io",
     "Headless browser API for screenshots, PDFs, and metadata.", "solo"),
    ("firecrawl-team", "Firecrawl", "https://www.firecrawl.dev",
     "Turn any website into clean data for your LLM.", "small_team"),
    ("gladia-team", "Gladia", "https://www.gladia.io",
     "Audio transcription and translation API for developers.", "small_team"),

    # Feature Flags & Analytics
    ("growthbook-team", "GrowthBook", "https://www.growthbook.io",
     "Open-source feature flags, A/B testing, and analytics.", "small_team"),
    ("flagsmith-team", "Flagsmith", "https://flagsmith.com",
     "Open-source feature flags with remote config and A/B tests.", "small_team"),

    # SaaS Boilerplates
    ("supastarter-team", "Supastarter", "https://supastarter.dev",
     "Production-ready Next.js + Supabase SaaS boilerplate.", "solo"),
    ("saasbold-team", "SaaSBold", "https://saasbold.com",
     "Complete Next.js SaaS boilerplate with payments and auth.", "solo"),

    # i18n / Localization
    ("tolgee-team", "Tolgee", "https://tolgee.io",
     "Open-source localization platform for developers.", "small_team"),
    ("locize-team", "Locize", "https://locize.com",
     "Continuous localization platform with native i18next support.", "small_team"),

    # Audio / Podcast
    ("podcastle-team", "Podcastle", "https://podcastle.ai",
     "AI-powered podcast recording and editing in the browser.", "small_team"),
    ("auphonic-team", "Auphonic", "https://auphonic.com",
     "AI audio mastering for podcasts and recordings.", "solo"),

    # AI Inference
    ("fal-ai-team", "Fal.ai", "https://fal.ai",
     "Fast AI image and video generation API for developers.", "small_team"),
    ("replicate-team", "Replicate", "https://replicate.com",
     "Run open-source AI models via API — no GPU needed.", "small_team"),

    # Ecommerce
    ("medusa-team", "Medusa", "https://medusajs.com",
     "Open-source headless commerce platform for developers.", "small_team"),
    ("saleor-team", "Saleor", "https://saleor.io",
     "High-performance open-source commerce API with GraphQL.", "small_team"),

    # Invoicing
    ("wave-team", "Wave Financial", "https://www.waveapps.com",
     "Free accounting, invoicing, and payroll for small business.", "small_team"),
    ("harpoon-team", "Harpoon", "https://harpoonapp.com",
     "Financial planning + time tracking for freelancers.", "solo"),

    # Low-Code / No-Code
    ("budibase-team", "Budibase", "https://budibase.com",
     "Low-code platform for building internal tools and dashboards.", "small_team"),
    ("baserow-team", "Baserow", "https://baserow.io",
     "Open-source no-code database and app builder.", "small_team"),

    # Project Management
    ("outline-team", "Outline", "https://www.getoutline.com",
     "Fast, collaborative wiki for your team.", "small_team"),
    ("huly-team", "Huly", "https://huly.io",
     "Open-source all-in-one project management platform.", "small_team"),
    ("plane-team", "Plane", "https://plane.so",
     "Open-source project management — flexible and powerful.", "small_team"),

    # Scheduling
    ("cal-com-team", "Cal.com", "https://cal.com",
     "Open-source scheduling infrastructure for everyone.", "small_team"),

    # BaaS
    ("appwrite-team", "Appwrite", "https://appwrite.io",
     "Open-source backend platform — auth, DB, storage, and more.", "small_team"),
    ("supabase-team", "Supabase", "https://supabase.com",
     "Open-source Firebase alternative with Postgres.", "small_team"),
]


# ── Tools ──────────────────────────────────────────────────────────────────
# (name, slug, tagline, description, url, maker_slug, category_slug,
#  tags, price_pence, upvotes)

TOOLS = [
    # ── Hosting / Deploy ──────────────────────────────────────────────────

    (
        "Coolify",
        "coolify",
        "Self-hostable PaaS for apps, databases & services",
        "Open-source, self-hostable alternative to Heroku, Vercel, and Netlify. Deploy any "
        "Docker-compatible app, manage databases, get automatic SSL, and connect to your own "
        "server via SSH. 280+ one-click service templates. Cloud plan from $5/mo.",
        "https://coolify.io",
        "coolify-team",
        "developer-tools",
        "hosting,deploy,self-hosted,paas,docker,ssl",
        500,  # $5/mo cloud
        134,
    ),
    (
        "Northflank",
        "northflank",
        "Full-stack cloud platform — build, deploy, scale",
        "Managed cloud platform for containerised apps with Git integration, cron jobs, "
        "preview environments, managed databases, and secret management. Designed for teams "
        "that want Heroku simplicity with more control. Free tier available.",
        "https://northflank.com",
        "northflank-team",
        "developer-tools",
        "hosting,deploy,containers,cron,preview-environments",
        800,  # $8/mo
        76,
    ),

    # ── Monitoring & Uptime ───────────────────────────────────────────────

    (
        "SigNoz",
        "signoz",
        "Open-source APM with logs, traces & metrics",
        "OpenTelemetry-native observability platform that unifies logs, distributed traces, "
        "and metrics in a single pane. Built on ClickHouse for 10-20x data compression vs "
        "Elasticsearch. Self-host for free or use their cloud. Direct alternative to Datadog.",
        "https://signoz.io",
        "signoz-team",
        "monitoring-uptime",
        "observability,logging,apm,traces,metrics,opentelemetry,datadog",
        19900,  # $199/mo cloud
        108,
    ),
    (
        "Uptrace",
        "uptrace",
        "OpenTelemetry APM — traces, metrics, logs in one",
        "Open-source APM built on OpenTelemetry and ClickHouse. Combines distributed tracing, "
        "metrics, and logs with 80% lower storage costs vs Elasticsearch-based tools. Self-host "
        "or use cloud. Cuts Datadog bills dramatically for high-volume teams.",
        "https://uptrace.dev",
        "uptrace-team",
        "monitoring-uptime",
        "observability,apm,tracing,logging,opentelemetry,datadog",
        3000,  # $30/mo
        62,
    ),
    (
        "GlitchTip",
        "glitchtip",
        "Simple open-source error tracking — Sentry compatible",
        "Sentry-compatible open-source error tracking and performance monitoring. Accepts "
        "Sentry SDK events with zero code changes. Self-host for free or use their affordable "
        "cloud at a fraction of Sentry's price. Great for indie devs.",
        "https://glitchtip.com",
        "glitchtip-team",
        "monitoring-uptime",
        "error-tracking,logging,monitoring,sentry,observability",
        900,  # $9/mo
        54,
    ),
    (
        "incident.io",
        "incident-io",
        "Incident management built for modern engineering teams",
        "Slack-native incident management platform that replaces PagerDuty's complexity with "
        "a streamlined on-call, alerting, and postmortem workflow. Integrates with Datadog, "
        "Grafana, and GitHub. Used by 2,000+ engineering teams.",
        "https://incident.io",
        "incident-io-team",
        "monitoring-uptime",
        "incident-management,on-call,alerting,pagerduty,monitoring",
        2500,  # $25/mo
        88,
    ),

    # ── Customer Support ──────────────────────────────────────────────────

    (
        "Chatwoot",
        "chatwoot",
        "Open-source customer support & live chat platform",
        "Open-source omnichannel support desk — live chat, email, social, WhatsApp, and more "
        "from one inbox. Self-host for free on your own server or use their cloud. Fully "
        "featured Intercom and Zendesk alternative loved by indie SaaS founders.",
        "https://www.chatwoot.com",
        "chatwoot-team",
        "customer-support",
        "live-chat,customer-support,intercom,zendesk,omnichannel",
        1900,  # $19/mo
        112,
    ),
    (
        "Mattermost",
        "mattermost",
        "Self-hosted team chat for engineering teams",
        "Open-source team messaging platform with channels, threads, voice/video calls, "
        "file sharing, and enterprise integrations. Full data sovereignty — host on your own "
        "infrastructure. Strong Slack alternative for security-conscious teams.",
        "https://mattermost.com",
        "mattermost-team",
        "customer-support",
        "team-chat,messaging,self-hosted,slack,communication",
        1000,  # $10/seat/mo
        96,
    ),

    # ── Email ─────────────────────────────────────────────────────────────

    (
        "Resend",
        "resend",
        "Email API for developers — built for great deliverability",
        "Modern transactional email API with a clean REST interface and first-class TypeScript "
        "SDK. Send emails via React components. Multi-region sending with excellent inbox "
        "placement. 3,000 free emails/mo. The developer-friendly SendGrid replacement.",
        "https://resend.com",
        "resend-team",
        "email-marketing",
        "email,transactional-email,sendgrid,api,deliverability",
        2000,  # $20/mo
        118,
    ),
    (
        "Loops",
        "loops",
        "Email platform for SaaS — transactional + marketing in one",
        "SaaS-focused email platform combining transactional and marketing emails under one "
        "roof. Subscriber-based pricing scales predictably. Strong developer API + no-code "
        "email editor. Built by indie founders for indie founders.",
        "https://loops.so",
        "loops-team",
        "email-marketing",
        "email,transactional-email,email-marketing,sendgrid,saas",
        4900,  # $49/mo
        82,
    ),
    (
        "Postmark",
        "postmark",
        "Fast, reliable transactional email with best-in-class deliverability",
        "Transactional email service with industry-leading inbox placement rates. Strict "
        "customer vetting keeps shared IPs clean. Lightning-fast delivery and detailed "
        "analytics. 100 free emails/mo. Battle-tested SendGrid alternative.",
        "https://postmarkapp.com",
        "postmark-team",
        "email-marketing",
        "email,transactional-email,sendgrid,deliverability,smtp",
        1500,  # $15/mo
        104,
    ),

    # ── CMS / Headless ────────────────────────────────────────────────────

    (
        "Ghost",
        "ghost",
        "Open-source publishing platform for blogs & newsletters",
        "Modern headless CMS purpose-built for publishing, newsletters, and paid memberships. "
        "Blazing fast, SEO-optimised, and API-first. Self-host for free or use Ghost Pro. "
        "Loved by indie publishers who want to own their audience without WordPress complexity.",
        "https://ghost.org",
        "ghost-team",
        "developer-tools",
        "cms,blog,newsletter,headless-cms,wordpress,publishing",
        900,  # $9/mo
        142,
    ),
    (
        "Strapi",
        "strapi",
        "Leading open-source headless CMS for developers",
        "The most popular open-source headless CMS with 5M+ npm downloads. Built on Node.js "
        "with REST and GraphQL APIs by default. Fully self-hostable with a powerful admin UI "
        "for content editors. Connect to any frontend framework.",
        "https://strapi.io",
        "strapi-team",
        "developer-tools",
        "headless-cms,cms,content,api,wordpress,self-hosted",
        2900,  # $29/mo cloud
        128,
    ),
    (
        "Payload CMS",
        "payload-cms",
        "Code-first headless CMS built with TypeScript",
        "Next-generation headless CMS built natively for TypeScript developers. Define your "
        "schema in code, get a full admin UI auto-generated, with REST and GraphQL APIs "
        "included. Self-host or use Payload Cloud. Rapidly growing Contentful alternative.",
        "https://payloadcms.com",
        "payload-cms-team",
        "developer-tools",
        "headless-cms,cms,typescript,content,wordpress,self-hosted",
        2500,  # $25/mo
        116,
    ),
    (
        "TinaCMS",
        "tinacms",
        "Git-backed headless CMS with visual editing",
        "Open-source headless CMS that stores content directly in your Git repo as Markdown "
        "or MDX. Provides a visual editing experience on top of your Next.js or Remix site. "
        "Free for open-source, affordable cloud plan for teams.",
        "https://tina.io",
        "tinacms-team",
        "developer-tools",
        "headless-cms,cms,git,markdown,visual-editing,blog",
        2900,  # $29/mo
        68,
    ),

    # ── Authentication ────────────────────────────────────────────────────

    (
        "Authentik",
        "authentik",
        "Self-hosted identity provider — SSO, LDAP, OAuth, SAML",
        "Open-source identity provider that replaces Okta, Auth0, and Entra ID for self-hosted "
        "deployments. Supports OAuth2, OIDC, SAML, LDAP, and Radius. Lightweight Docker setup "
        "with a modern UI. Strong pick for teams running their own infra.",
        "https://goauthentik.io",
        "authentik-team",
        "authentication",
        "auth,authentication,sso,oauth,saml,self-hosted,auth0",
        None,  # Free / self-hosted
        92,
    ),
    (
        "Hanko",
        "hanko",
        "Passkey-first authentication API for modern apps",
        "Open-source, API-first auth built for the passwordless era. Passkeys, OAuth social "
        "login, and enterprise SSO out of the box. Drop-in web components make integration "
        "fast. AGPL v3 self-host or affordable cloud.",
        "https://www.hanko.io",
        "hanko-team",
        "authentication",
        "auth,authentication,passkeys,oauth,passwordless,auth0",
        2500,  # $25/mo
        78,
    ),
    (
        "Logto",
        "logto",
        "Auth infrastructure for SaaS — SSO, MFA, multi-tenant",
        "Open-source CIAM platform with a beautiful sign-in UI, multi-tenancy, machine-to-machine "
        "auth, RBAC, and enterprise SSO. Self-host for free or use Logto Cloud. Targets SaaS "
        "founders who need Okta-level features without Okta prices.",
        "https://logto.io",
        "logto-team",
        "authentication",
        "auth,authentication,oauth,sso,multi-tenant,saas,auth0",
        1600,  # $16/mo
        86,
    ),

    # ── Vector Databases (AI Dev Tools) ───────────────────────────────────

    (
        "Qdrant",
        "qdrant",
        "High-performance vector database written in Rust",
        "Production-ready open-source vector similarity search engine. Supports rich metadata "
        "filtering, ACID transactions, distributed deployment, and horizontal scaling. Self-host "
        "or use Qdrant Cloud. Core infrastructure for AI and RAG apps.",
        "https://qdrant.tech",
        "qdrant-team",
        "ai-dev-tools",
        "vector-database,embeddings,ai,rag,search,self-hosted",
        2500,  # $25/mo cloud
        114,
    ),
    (
        "Chroma",
        "chroma",
        "Open-source embedding database for AI apps",
        "Developer-friendly open-source vector database with a NumPy-like Python API. Runs "
        "embedded in your app with zero network latency, or as a standalone server. The fastest "
        "path from idea to working RAG prototype.",
        "https://www.trychroma.com",
        "chroma-team",
        "ai-dev-tools",
        "vector-database,embeddings,ai,rag,llm,search",
        None,  # Free / open source
        106,
    ),
    (
        "Weaviate",
        "weaviate",
        "AI-native vector database with hybrid search",
        "Open-source vector database supporting hybrid vector + BM25 keyword search, multi-modal "
        "inputs (text, image, video), and built-in embedding integrations. Strong GraphQL API. "
        "Self-host or use Weaviate Cloud. Production-tested at scale for AI applications.",
        "https://weaviate.io",
        "weaviate-team",
        "ai-dev-tools",
        "vector-database,embeddings,ai,hybrid-search,rag,llm",
        2500,  # $25/mo
        98,
    ),

    # ── AI Inference ──────────────────────────────────────────────────────

    (
        "Firecrawl",
        "firecrawl",
        "Turn any website into clean data for your LLM",
        "Web scraping and crawling API that converts any website into clean Markdown or JSON "
        "for LLM ingestion. Handles JavaScript rendering, auth pages, and full site crawls. "
        "Self-host or use cloud. Key tool for AI/RAG pipelines.",
        "https://www.firecrawl.dev",
        "firecrawl-team",
        "ai-dev-tools",
        "web-scraper,scraping,llm,rag,ai,data-extraction,crawler",
        1600,  # $16/mo
        102,
    ),
    (
        "Fal.ai",
        "fal-ai",
        "Fast AI image & video generation API for developers",
        "Developer-focused inference API for generative AI models — Stable Diffusion, FLUX, "
        "video generation, and more. Serverless GPU infrastructure with millisecond cold "
        "starts. Pay per inference with no minimum.",
        "https://fal.ai",
        "fal-ai-team",
        "ai-dev-tools",
        "ai-image,video,image-generation,ai,api,stable-diffusion",
        None,  # Pay-per-inference
        88,
    ),
    (
        "Replicate",
        "replicate",
        "Run open-source AI models via API — no GPU needed",
        "Platform to run thousands of open-source AI models (image, video, audio, language) "
        "via a simple API. No GPU setup, no model hosting. Pay per second of GPU compute. "
        "Huge model library including FLUX, Whisper, LLaMA, and Stable Diffusion.",
        "https://replicate.com",
        "replicate-team",
        "ai-dev-tools",
        "ai-image,video,audio,ai-models,api,gpu,stable-diffusion",
        None,  # Pay-per-use
        122,
    ),

    # ── Databases & Data ──────────────────────────────────────────────────

    (
        "Drizzle ORM",
        "drizzle-orm",
        "TypeScript ORM that feels like SQL — tiny & fast",
        "Lightweight TypeScript ORM with a SQL-like query builder and zero external dependencies "
        "at ~7.4kb. 90% smaller bundle than Prisma, sub-500ms cold starts. Supports PostgreSQL, "
        "MySQL, and SQLite. Favourite ORM for edge and serverless deployments.",
        "https://orm.drizzle.team",
        "drizzle-team",
        "developer-tools",
        "orm,database,typescript,sql,serverless,developer-tools",
        None,  # Free / open source
        132,
    ),
    (
        "Neon",
        "neon",
        "Serverless Postgres with scale-to-zero and branching",
        "Fully managed serverless Postgres that separates compute and storage. Scales to zero "
        "between requests, branches databases like Git, and auto-scales compute. Free tier "
        "available with generous limits.",
        "https://neon.com",
        "neon-team",
        "developer-tools",
        "database,postgres,serverless,cloud,sql,branching",
        1900,  # $19/mo
        126,
    ),
    (
        "Turso",
        "turso",
        "Edge SQLite database — embed or deploy globally",
        "Serverless, edge-optimised database built on libSQL (SQLite fork). Deploy hundreds "
        "of databases per tenant at the edge for near-zero latency. Ideal for multi-tenant "
        "SaaS and lightweight apps. Free tier covers most indie projects.",
        "https://turso.tech",
        "turso-team",
        "developer-tools",
        "database,sqlite,edge,serverless,multi-tenant,libsql",
        2900,  # $29/mo
        108,
    ),
    (
        "Upstash",
        "upstash",
        "Serverless Redis & Kafka — pay per request",
        "Serverless Redis and Kafka with a per-request pricing model that scales to zero. "
        "Global low-latency caching, rate limiting, queuing, and pub/sub for edge and "
        "serverless apps. REST API works from any environment including edge runtimes.",
        "https://upstash.com",
        "upstash-team",
        "developer-tools",
        "cache,redis,serverless,kafka,rate-limiting,edge,data-pipeline",
        None,  # Pay-per-request
        114,
    ),
    (
        "Airbyte",
        "airbyte",
        "Open-source data integration platform — 600+ connectors",
        "Leading open-source ELT platform with 600+ pre-built connectors for APIs, databases, "
        "and files. Sync to any data warehouse or lake. Self-host for free or use Airbyte Cloud. "
        "Integrates with dbt, Airflow, Prefect, and Dagster.",
        "https://airbyte.com",
        "airbyte-team",
        "developer-tools",
        "etl,data-pipeline,data-integration,elt,self-hosted",
        1000,  # $10/mo cloud
        94,
    ),

    # ── CI/CD & Web Servers ───────────────────────────────────────────────

    (
        "Woodpecker CI",
        "woodpecker-ci",
        "Simple self-hosted CI/CD with Docker-native pipelines",
        "Lightweight open-source CI/CD engine forked from Drone CI with active community "
        "development. Docker-native pipeline steps, pipeline-as-code YAML, and integrations "
        "with GitHub, GitLab, Gitea, and Forgejo. Runs on a $5 VPS.",
        "https://woodpecker-ci.org",
        "woodpecker-ci-team",
        "developer-tools",
        "ci-cd,continuous-integration,self-hosted,docker,pipelines,devops",
        None,  # Free / self-hosted
        72,
    ),
    (
        "Caddy",
        "caddy",
        "Web server with automatic HTTPS — simpler than Nginx",
        "Modern open-source web server and reverse proxy with automatic HTTPS via Let's Encrypt "
        "out of the box. Simple declarative Caddyfile config, HTTP/3 support, and plugin "
        "ecosystem. Replaces Nginx + Certbot with zero-maintenance SSL.",
        "https://caddyserver.com",
        "caddy-team",
        "developer-tools",
        "web-server,ssl,reverse-proxy,https,dns,load-balancer",
        None,  # Free / open source
        118,
    ),
    (
        "Traefik",
        "traefik",
        "Cloud-native reverse proxy and load balancer",
        "Open-source reverse proxy and load balancer designed for microservices and containers. "
        "Auto-discovers services from Docker, Kubernetes, and Consul. Automatic TLS with "
        "Let's Encrypt. Used by millions running containerised workloads.",
        "https://traefik.io",
        "traefik-team",
        "developer-tools",
        "load-balancer,reverse-proxy,ssl,docker,kubernetes,container",
        None,  # Free / open source
        124,
    ),
    (
        "Portainer",
        "portainer",
        "Container management UI for Docker and Kubernetes",
        "Open-source web UI for managing Docker, Swarm, and Kubernetes environments. Deploy "
        "containers, stacks, and services without CLI. Supports edge deployments and "
        "multi-cluster management. Free Community Edition for most needs.",
        "https://www.portainer.io",
        "portainer-team",
        "developer-tools",
        "docker,kubernetes,container,devops,self-hosted",
        None,  # Free community edition
        102,
    ),

    # ── Background Jobs & Workflows ───────────────────────────────────────

    (
        "Trigger.dev",
        "trigger-dev",
        "Build & deploy fully-managed background jobs in code",
        "Open-source platform for running reliable background jobs, cron schedules, and "
        "event-driven workflows directly from your codebase. No external queue setup needed. "
        "Supports long-running tasks up to 1 hour. Alternative to BullMQ + Redis.",
        "https://trigger.dev",
        "trigger-dev-team",
        "developer-tools",
        "cron,background-jobs,queues,workflow,scheduling,devops",
        2000,  # $20/mo
        86,
    ),
    (
        "Inngest",
        "inngest",
        "AI and backend workflows orchestrated at any scale",
        "Workflow orchestration platform for serverless, servers, and the edge. Write step "
        "functions and cron jobs in code — Inngest handles retries, concurrency, and "
        "observability. Strong fit for AI agent pipelines.",
        "https://www.inngest.com",
        "inngest-team",
        "developer-tools",
        "workflow,cron,background-jobs,orchestration,scheduling,ai-agents",
        2500,  # $25/mo
        82,
    ),

    # ── Scraping & APIs ───────────────────────────────────────────────────

    (
        "ScrapingBee",
        "scrapingbee",
        "Web scraping API that handles proxies & headless browsers",
        "Managed web scraping API with automatic proxy rotation, JavaScript rendering, and "
        "CAPTCHA solving. Screenshot API included. No-infra web scraping at scale. Simple "
        "REST API with SDKs for Python, Node, PHP, Ruby, and more.",
        "https://www.scrapingbee.com",
        "scrapingbee-team",
        "api-tools",
        "web-scraper,scraping,screenshot,proxy,headless-browser,api",
        4900,  # $49/mo
        68,
    ),
    (
        "ScreenshotOne",
        "screenshotone",
        "Screenshot API — render any URL to image or PDF",
        "Developer-focused screenshot API that renders any URL to PNG, JPEG, WebP, or PDF. "
        "Removes cookie banners, ads, and chat widgets automatically. Free plan with 100 "
        "screenshots/mo. SDKs for major languages.",
        "https://screenshotone.com",
        "screenshotone-team",
        "api-tools",
        "screenshot,web-scraper,scraping,api,pdf,headless-browser",
        900,  # $9/mo
        52,
    ),
    (
        "Microlink",
        "microlink",
        "Headless browser API — screenshots, PDFs & metadata",
        "Cloud-native headless browser API for taking screenshots, generating PDFs, extracting "
        "metadata, and rendering link previews. Global CDN with 240+ edge nodes and 99.9% "
        "uptime. Simple HTTP API with no browser infrastructure to manage.",
        "https://microlink.io",
        "microlink-team",
        "api-tools",
        "screenshot,web-scraper,scraping,headless-browser,api,pdf",
        900,  # $9/mo
        58,
    ),
    (
        "Gladia",
        "gladia",
        "Audio transcription & translation API for developers",
        "Fast, accurate speech-to-text API with speaker diarisation, word timestamps, and "
        "translation into 100+ languages. Significantly cheaper than Deepgram and AssemblyAI. "
        "Simple REST API with real-time streaming support.",
        "https://www.gladia.io",
        "gladia-team",
        "api-tools",
        "transcription,translation,audio,speech-to-text,api,localization",
        None,  # Pay-per-use
        64,
    ),

    # ── Feature Flags & Analytics ─────────────────────────────────────────

    (
        "GrowthBook",
        "growthbook",
        "Open-source feature flags, A/B testing & analytics",
        "MIT-licensed open-source platform for feature flags, experimentation, and product "
        "analytics. Unlimited flags and experiments on self-hosted. Bayesian and frequentist "
        "stats engines built-in. Works with your existing data warehouse.",
        "https://www.growthbook.io",
        "growthbook-team",
        "analytics-metrics",
        "feature-flags,ab-testing,experimentation,analytics,self-hosted",
        None,  # Free self-hosted, free cloud 3 seats
        96,
    ),
    (
        "Flagsmith",
        "flagsmith",
        "Open-source feature flags with remote config & A/B tests",
        "100% open-source feature management platform with remote configuration, user "
        "segmentation, and multivariate A/B testing. Supports OpenFeature so you can swap "
        "vendors without code changes. Self-host or use cloud.",
        "https://flagsmith.com",
        "flagsmith-team",
        "analytics-metrics",
        "feature-flags,ab-testing,remote-config,self-hosted,open-source",
        4500,  # $45/mo
        74,
    ),

    # ── SaaS Boilerplates ─────────────────────────────────────────────────

    (
        "Supastarter",
        "supastarter",
        "Production-ready Next.js + Supabase SaaS boilerplate",
        "Paid SaaS starter kit for Next.js and Nuxt with auth, Stripe billing, email, i18n, "
        "admin panel, and dark mode pre-wired. Comes with a support Discord and regular "
        "updates. Get a production-grade SaaS foundation in hours, not weeks.",
        "https://supastarter.dev",
        "supastarter-team",
        "developer-tools",
        "boilerplate,starter-kit,saas,nextjs,supabase",
        19900,  # $199 one-time
        72,
    ),
    (
        "SaaSBold",
        "saasbold",
        "Complete Next.js SaaS boilerplate with payments & auth",
        "Production-ready Next.js SaaS boilerplate with Stripe, authentication, email, "
        "database, admin dashboard, and one-click Vercel deployment included. Saves weeks "
        "of setup time. One-time purchase with lifetime updates.",
        "https://saasbold.com",
        "saasbold-team",
        "developer-tools",
        "boilerplate,starter-kit,saas,nextjs,stripe",
        9900,  # $99 one-time
        58,
    ),

    # ── i18n / Localization ───────────────────────────────────────────────

    (
        "Tolgee",
        "tolgee",
        "Open-source localization platform for developers",
        "Developer and translator-friendly web-based localization platform. In-context "
        "translation right in your app UI, CLI for CI/CD, REST API, and integrations with "
        "React, Angular, Vue, and more. Self-host for free or use Tolgee Cloud.",
        "https://tolgee.io",
        "tolgee-team",
        "developer-tools",
        "translation,localization,i18n,self-hosted,developer-tools",
        2500,  # $25/mo
        66,
    ),
    (
        "Locize",
        "locize",
        "Continuous localization platform with native i18next support",
        "SaaS localization platform built by the creators of i18next. Native i18next "
        "integration with CLI, REST API, and CDN delivery so translation updates deploy "
        "without a full app redeploy. Webhooks and machine translation included.",
        "https://locize.com",
        "locize-team",
        "developer-tools",
        "translation,localization,i18n,i18next,saas",
        1500,  # $15/mo
        48,
    ),

    # ── Audio / Podcast (Design & Creative) ───────────────────────────────

    (
        "Podcastle",
        "podcastle",
        "AI-powered podcast recording and editing in the browser",
        "Cloud-based podcast production platform with browser recording, AI-powered audio "
        "cleanup, voice cloning, text-to-speech, and multi-track editing. Remote interviews "
        "with separate audio tracks. Good alternative to Adobe Podcast for indie creators.",
        "https://podcastle.ai",
        "podcastle-team",
        "design-creative",
        "podcast,audio,recording,ai,voice,transcription",
        1199,  # $11.99/mo
        62,
    ),
    (
        "Auphonic",
        "auphonic",
        "AI audio mastering for podcasts and recordings",
        "AI-driven audio post-production service loved by indie podcasters and major networks. "
        "Automatically normalises loudness, removes noise, balances multi-track audio, and "
        "exports to all podcast platforms. 2 free hours of processing per month.",
        "https://auphonic.com",
        "auphonic-team",
        "design-creative",
        "podcast,audio,mastering,ai,noise-reduction",
        1100,  # $11/mo
        56,
    ),

    # ── Ecommerce (Payments) ──────────────────────────────────────────────

    (
        "Medusa",
        "medusa",
        "Open-source headless commerce platform for developers",
        "Node.js-based headless ecommerce engine with a modular architecture, REST API, and "
        "plugin ecosystem. Multi-region, multiple currencies, subscriptions, and a React "
        "storefront starter. Self-host for free. 30K+ GitHub stars.",
        "https://medusajs.com",
        "medusa-team",
        "payments",
        "ecommerce,headless-commerce,shopify,developer-tools,inventory",
        None,  # Free / self-hosted
        108,
    ),
    (
        "Saleor",
        "saleor",
        "High-performance open-source commerce API with GraphQL",
        "Python/Django headless ecommerce platform with a GraphQL API, multi-channel selling, "
        "advanced inventory, and a React storefront kit. Highly scalable with a clean "
        "API-first architecture. Self-host or use Saleor Cloud.",
        "https://saleor.io",
        "saleor-team",
        "payments",
        "ecommerce,headless-commerce,graphql,inventory,shopify",
        None,  # Free / self-hosted
        84,
    ),

    # ── Invoicing & Billing ───────────────────────────────────────────────

    (
        "Wave",
        "wave-financial",
        "Free accounting, invoicing & payroll for small business",
        "Completely free accounting and invoicing software for small businesses and freelancers. "
        "Handles income, expenses, bank reconciliation, invoicing, and optional payroll add-on. "
        "No limits on invoices or users. Great QuickBooks and FreshBooks alternative.",
        "https://www.waveapps.com",
        "wave-team",
        "invoicing-billing",
        "accounting,invoicing,payroll,small-business,hr",
        None,  # Free (payroll from $20/mo)
        92,
    ),
    (
        "Harpoon",
        "harpoon",
        "Financial planning + time tracking for freelancers",
        "Goal-oriented time tracking and invoicing app for freelancers and studios. Set annual "
        "revenue goals, track billable hours, create invoices, and forecast your financial "
        "future. Simple setup and automation. Built by an indie developer.",
        "https://harpoonapp.com",
        "harpoon-team",
        "invoicing-billing",
        "invoicing,time-tracking,accounting,payroll,freelancer",
        900,  # $9/mo
        44,
    ),

    # ── Low-Code / No-Code ────────────────────────────────────────────────

    (
        "Budibase",
        "budibase",
        "Low-code platform for building internal tools & dashboards",
        "Open-source low-code platform for rapidly building internal apps, dashboards, forms, "
        "and workflows. Connects to PostgreSQL, MySQL, REST APIs, S3, and more. Self-host or "
        "use cloud. Drag-and-drop builder with server-side scripting. Retool alternative.",
        "https://budibase.com",
        "budibase-team",
        "developer-tools",
        "low-code,no-code,dashboard-builder,internal-tools,forms",
        5000,  # $50/mo
        82,
    ),
    (
        "Baserow",
        "baserow",
        "Open-source no-code database & app builder",
        "Self-hostable no-code database and application builder with Kanban, calendar, gallery, "
        "and form views. API-first with webhooks and third-party integrations. Strong Airtable "
        "alternative that keeps your data on your servers.",
        "https://baserow.io",
        "baserow-team",
        "developer-tools",
        "no-code,database,kanban,dashboard-builder,self-hosted",
        500,  # $5/mo
        78,
    ),

    # ── Project Management ────────────────────────────────────────────────

    (
        "Outline",
        "outline",
        "Fast, collaborative wiki for your team",
        "Open-source team wiki and knowledge base with a beautiful editor, real-time "
        "collaboration, and Slack integration. Self-host for free or use cloud. Used by "
        "10,000+ teams as a lightweight Notion and Confluence replacement for documentation.",
        "https://www.getoutline.com",
        "outline-team",
        "project-management",
        "wiki,documentation,knowledge-base,cms,confluence,team",
        1000,  # $10/mo
        98,
    ),
    (
        "Huly",
        "huly",
        "Open-source all-in-one project management platform",
        "Open-source replacement for Linear, Jira, Notion, and Slack. Includes project "
        "management, team chat, HR, CRM, and documentation in one platform. Two-way GitHub "
        "sync keeps issues and PRs in sync. Self-host or use Huly Cloud.",
        "https://huly.io",
        "huly-team",
        "project-management",
        "project-management,kanban,issue-tracking,team-chat,self-hosted",
        None,  # Free / self-hosted
        104,
    ),
    (
        "Plane",
        "plane",
        "Open-source project management — flexible and powerful",
        "Modern open-source project management tool with issues, cycles, modules, and roadmaps. "
        "Multiple views: Kanban, list, spreadsheet, and Gantt. GitHub integration for linking "
        "PRs to issues. Self-host for free or use Plane Cloud.",
        "https://plane.so",
        "plane-team",
        "project-management",
        "project-management,kanban,issue-tracking,roadmap,self-hosted",
        600,  # $6/seat/mo
        96,
    ),

    # ── Scheduling & Booking ──────────────────────────────────────────────

    (
        "Cal.com",
        "cal-com",
        "Open-source scheduling infrastructure for everyone",
        "Open-source Calendly alternative with unlimited event types, round-robin scheduling, "
        "group meetings, and timezone detection. API-first with webhooks and Zapier integration. "
        "Self-host for free or use Cal.com Cloud. Used by 50,000+ organisations.",
        "https://cal.com",
        "cal-com-team",
        "scheduling-booking",
        "scheduling,calendar,booking,calendly,open-source",
        1500,  # $15/mo
        136,
    ),

    # ── BaaS (Backend-as-a-Service) ───────────────────────────────────────

    (
        "Appwrite",
        "appwrite",
        "Open-source backend platform — auth, DB, storage & more",
        "Self-hosted open-source backend-as-a-service that packages databases, authentication, "
        "storage, cloud functions, real-time, and messaging into one Docker-based platform. "
        "REST and GraphQL APIs. Strong Firebase and Supabase alternative with full data ownership.",
        "https://appwrite.io",
        "appwrite-team",
        "developer-tools",
        "backend,baas,auth,database,storage,self-hosted,docker",
        1500,  # $15/mo cloud
        128,
    ),
    (
        "Supabase",
        "supabase",
        "Open-source Firebase alternative with Postgres",
        "Open-source BaaS built on PostgreSQL with auth, real-time subscriptions, edge functions, "
        "storage, and an auto-generated REST/GraphQL API. Self-host or use Supabase Cloud with "
        "a generous free tier. Fastest-growing Firebase alternative with 70K+ GitHub stars.",
        "https://supabase.com",
        "supabase-team",
        "developer-tools",
        "database,backend,baas,auth,postgres,self-hosted",
        2500,  # $25/mo
        148,
    ),
]


# ── Replaces mappings ──────────────────────────────────────────────────────
REPLACES = {
    # Hosting / Deploy
    "coolify": "Vercel, Netlify, Heroku, Render",
    "northflank": "Vercel, Netlify, Heroku, Render, Railway",

    # Monitoring & Uptime
    "signoz": "Datadog, New Relic, Dynatrace",
    "uptrace": "Datadog, New Relic, Honeycomb",
    "glitchtip": "Sentry, Bugsnag, Rollbar, New Relic",
    "incident-io": "PagerDuty, Opsgenie, VictorOps",

    # Customer Support
    "chatwoot": "Intercom, Zendesk, Freshdesk",
    "mattermost": "Slack, Microsoft Teams",

    # Email
    "resend": "SendGrid, Mailgun, Postmark",
    "loops": "SendGrid, Mailchimp, Customer.io",
    "postmark": "SendGrid, Mailgun, Amazon SES",

    # CMS / Headless
    "ghost": "WordPress, Substack, Medium",
    "strapi": "WordPress, Contentful, Sanity",
    "payload-cms": "Contentful, Strapi, Sanity",
    "tinacms": "Contentful, Sanity, WordPress",

    # Authentication
    "authentik": "Auth0, Okta, Keycloak",
    "hanko": "Auth0, Clerk, Stytch",
    "logto": "Auth0, Okta, WorkOS",

    # Vector Databases
    "qdrant": "Pinecone, Weaviate, Milvus",
    "chroma": "Pinecone, Weaviate, Milvus",
    "weaviate": "Pinecone, Elasticsearch, Milvus",

    # AI Inference
    "firecrawl": "Apify, ScrapingBee, Diffbot",
    "fal-ai": "Replicate, Stability AI API, OpenAI DALL-E",
    "replicate": "AWS SageMaker, Hugging Face Inference, self-hosted GPUs",

    # Databases & Data
    "drizzle-orm": "Prisma, TypeORM, Sequelize",
    "neon": "PlanetScale, Supabase, RDS",
    "turso": "PlanetScale, Neon, FaunaDB",
    "upstash": "Redis Labs, Amazon ElastiCache, Momento",
    "airbyte": "Fivetran, Stitch, Talend",

    # CI/CD & Web Servers
    "woodpecker-ci": "GitHub Actions, Drone CI, Jenkins, CircleCI",
    "caddy": "Nginx, Apache, Traefik",
    "traefik": "Nginx, HAProxy, AWS ALB",
    "portainer": "Rancher, Lens, Docker Desktop",

    # Background Jobs
    "trigger-dev": "BullMQ, Sidekiq, Temporal, Quirrel",
    "inngest": "Temporal, Quirrel, BullMQ, Celery",

    # Scraping & APIs
    "scrapingbee": "Bright Data, Apify, Scrapy self-hosting",
    "screenshotone": "Puppeteer self-hosting, Browserless, URLbox",
    "microlink": "Puppeteer, Playwright, URLbox",
    "gladia": "Deepgram, AssemblyAI, Amazon Transcribe",

    # Feature Flags
    "growthbook": "LaunchDarkly, Optimizely, Split.io",
    "flagsmith": "LaunchDarkly, Split.io, Optimizely",

    # SaaS Boilerplates
    "supastarter": "Building from scratch, custom boilerplates",
    "saasbold": "Building from scratch, Gravity, ShipFast",

    # i18n
    "tolgee": "Crowdin, Lokalise, Phrase",
    "locize": "Crowdin, Phrase, Lokalise",

    # Audio / Podcast
    "podcastle": "Adobe Podcast, Audacity, Descript",
    "auphonic": "iZotope RX, Adobe Audition, manual post-production",

    # Ecommerce
    "medusa": "Shopify, WooCommerce, BigCommerce",
    "saleor": "Shopify, Magento, WooCommerce",

    # Invoicing
    "wave-financial": "QuickBooks, FreshBooks, Xero",
    "harpoon": "Harvest, FreshBooks, Toggl",

    # Low-Code / No-Code
    "budibase": "Retool, Appsmith, Tooljet",
    "baserow": "Airtable, Notion, Smartsheet",

    # Project Management
    "outline": "Confluence, Notion, GitBook",
    "huly": "Linear, Jira, Notion, Asana",
    "plane": "Linear, Jira, Asana",

    # Scheduling
    "cal-com": "Calendly, Acuity Scheduling",

    # BaaS
    "appwrite": "Firebase, Supabase, AWS Amplify",
    "supabase": "Firebase, PlanetScale, Neon",
}


def main():
    print(f"Seeding Round 4 tools at: {DB_PATH}")

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

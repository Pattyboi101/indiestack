#!/usr/bin/env python3
"""Seed IndieStack with ~100 tools to fill remaining search gaps.

Covers: ORMs, load balancers, web scrapers, cron/schedulers, HR/payroll,
audio/podcast, transcription, AI image, vector databases, low-code,
dashboards/reporting, ETL/data pipelines, boilerplates/starter kits,
API gateways, Kubernetes/containers, serverless, spreadsheets,
accounting/inventory, design systems/icons, chatbots/AI writing,
data visualization.

Usage:
    python3 seed_round3.py

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
    # ── ORM (developer-tools) ─────────────────────────────────────────────
    (
        "Prisma",
        "prisma",
        "Next-gen Node.js and TypeScript ORM with auto-generated types.",
        "Prisma is a next-generation ORM for Node.js and TypeScript. It provides "
        "a type-safe database client, declarative schema migrations, and a visual "
        "database browser. Works with PostgreSQL, MySQL, SQLite, and MongoDB.",
        "https://prisma.io",
        "developer-tools",
        "orm,typescript,database,node,open-source",
        "Sequelize,TypeORM",
    ),
    (
        "Drizzle ORM",
        "drizzle-orm",
        "Lightweight TypeScript ORM with SQL-like query builder.",
        "Drizzle ORM is a lightweight, type-safe TypeScript ORM that feels like "
        "writing SQL. Zero dependencies, serverless-ready, and works with any "
        "SQL database. Includes a visual studio for schema management.",
        "https://orm.drizzle.team",
        "developer-tools",
        "orm,typescript,sql,lightweight,serverless",
        "Prisma,Knex",
    ),
    (
        "SQLAlchemy",
        "sqlalchemy",
        "Python SQL toolkit and ORM. The gold standard for Python database access.",
        "SQLAlchemy is Python's most popular SQL toolkit and ORM. It provides a "
        "full suite of enterprise-level persistence patterns and an efficient "
        "SQL expression language. Powers thousands of production applications.",
        "https://sqlalchemy.org",
        "developer-tools",
        "orm,python,sql,database,open-source",
        "Django ORM,Peewee",
    ),

    # ── Load Balancer (developer-tools) ───────────────────────────────────
    (
        "Traefik",
        "traefik",
        "Cloud-native reverse proxy and load balancer. Auto-discovers services.",
        "Traefik is a modern reverse proxy and load balancer that integrates with "
        "Docker, Kubernetes, and other orchestrators. Automatic HTTPS via Let's "
        "Encrypt, middleware plugins, and real-time dashboard included.",
        "https://traefik.io",
        "developer-tools",
        "load-balancer,reverse-proxy,docker,kubernetes,open-source",
        "Nginx,Apache",
    ),
    (
        "Caddy",
        "caddy",
        "Web server with automatic HTTPS and reverse proxy built in.",
        "Caddy is a powerful web server with automatic HTTPS out of the box. "
        "Simple configuration via Caddyfile, built-in reverse proxy, load "
        "balancing, and HTTP/3 support. Written in Go, single binary deploy.",
        "https://caddyserver.com",
        "developer-tools",
        "web-server,reverse-proxy,https,load-balancer,open-source",
        "Nginx,Apache",
    ),
    (
        "HAProxy",
        "haproxy",
        "Reliable, high-performance TCP/HTTP load balancer.",
        "HAProxy is a free, open-source load balancer and proxy server for TCP "
        "and HTTP applications. Used by major sites for high availability and "
        "performance. Supports SSL termination, rate limiting, and health checks.",
        "https://haproxy.org",
        "developer-tools",
        "load-balancer,proxy,high-availability,tcp,open-source",
        "Nginx,AWS ELB",
    ),

    # ── Web Scraping (developer-tools) ────────────────────────────────────
    (
        "Scrapy",
        "scrapy",
        "Open-source web crawling framework for Python.",
        "Scrapy is a fast, high-level web crawling and scraping framework for "
        "Python. Extract data from websites with powerful selectors, built-in "
        "export formats, and middleware for handling proxies and user agents.",
        "https://scrapy.org",
        "developer-tools",
        "web-scraping,python,crawling,data-extraction,open-source",
        "Beautiful Soup,Selenium",
    ),
    (
        "Playwright",
        "playwright",
        "Browser automation and testing by Microsoft. Cross-browser.",
        "Playwright enables reliable end-to-end testing and browser automation "
        "for Chromium, Firefox, and WebKit. Auto-wait, network interception, "
        "and mobile emulation. One API across all browsers by Microsoft.",
        "https://playwright.dev",
        "developer-tools",
        "browser-automation,testing,web-scraping,cross-browser,microsoft",
        "Selenium,Puppeteer,Cypress",
    ),
    (
        "Crawlee",
        "crawlee",
        "Web scraping and browser automation library for Node.js.",
        "Crawlee is a web scraping and browser automation library that helps "
        "build reliable scrapers fast. Supports HTTP crawling and headless "
        "browser modes. Auto-scaling, proxy rotation, and storage built in.",
        "https://crawlee.dev",
        "developer-tools",
        "web-scraping,browser-automation,node,crawling,open-source",
        "Puppeteer,Scrapy",
    ),

    # ── Cron / Scheduler (ai-automation) ──────────────────────────────────
    (
        "Ofelia",
        "ofelia",
        "Docker-based job scheduler. Run cron jobs in containers.",
        "Ofelia is a Docker job scheduler that runs cron-style tasks inside "
        "containers. Define schedules via labels or config file. Supports job "
        "exec, run, and local commands with logging and error notifications.",
        "https://github.com/mcuadros/ofelia",
        "ai-automation",
        "cron,scheduler,docker,jobs,open-source",
        "crontab,systemd timers",
    ),
    (
        "Healthchecks.io",
        "healthchecks-io",
        "Cron job monitoring. Get alerts when your cron jobs fail.",
        "Healthchecks.io monitors your cron jobs and scheduled tasks. Each check "
        "gets a unique ping URL — if a ping doesn't arrive on time, you get "
        "alerted via email, Slack, PagerDuty, or 30+ other integrations.",
        "https://healthchecks.io",
        "ai-automation",
        "cron,monitoring,alerts,scheduled-tasks,open-source",
        "Cronitor,PagerDuty",
    ),
    (
        "Dkron",
        "dkron",
        "Distributed job scheduling system. Fault-tolerant cron.",
        "Dkron is a distributed, fault-tolerant job scheduling system. Run "
        "cron jobs across your infrastructure with automatic failover. "
        "REST API, web UI, and support for shell, HTTP, and gRPC executors.",
        "https://dkron.io",
        "ai-automation",
        "cron,scheduler,distributed,fault-tolerant,open-source",
        "crontab,Airflow",
    ),

    # ── HR / Payroll (invoicing-billing) ──────────────────────────────────
    (
        "OrangeHRM",
        "orangehrm",
        "Open-source HR management software for growing teams.",
        "OrangeHRM is a comprehensive open-source HR management system. "
        "Employee records, leave management, time tracking, recruitment, "
        "and performance reviews. Used by over 5 million people worldwide.",
        "https://orangehrm.com",
        "invoicing-billing",
        "hr,payroll,open-source,employee-management,self-hosted",
        "BambooHR,Gusto",
    ),
    (
        "Odoo HR",
        "odoo-hr",
        "Open-source ERP with full HR and payroll modules.",
        "Odoo is a comprehensive open-source ERP suite with dedicated HR modules. "
        "Recruitment, appraisals, time off, expenses, payroll, and fleet management. "
        "Modular design lets you add only what you need.",
        "https://odoo.com",
        "invoicing-billing",
        "hr,erp,payroll,open-source,recruitment",
        "SAP,BambooHR,Workday",
    ),
    (
        "IceHrm",
        "icehrm",
        "Open-source HR management for small and medium enterprises.",
        "IceHrm is an open-source human resource management system for SMEs. "
        "Employee management, leave tracking, timesheet management, and "
        "recruitment. Self-hosted with a clean, modern interface.",
        "https://icehrm.com",
        "invoicing-billing",
        "hr,employee-management,open-source,self-hosted,timesheet",
        "BambooHR,OrangeHRM",
    ),

    # ── Podcast / Audio (design-creative) ─────────────────────────────────
    (
        "Castopod",
        "castopod",
        "Open-source podcast hosting with ActivityPub federation.",
        "Castopod is an open-source podcast hosting platform with built-in "
        "ActivityPub support. Your podcast becomes a social feed in the fediverse. "
        "Analytics, monetization, and multi-podcast support included.",
        "https://castopod.org",
        "design-creative",
        "podcast,hosting,open-source,fediverse,activitypub",
        "Anchor,Buzzsprout",
    ),
    (
        "Funkwhale",
        "funkwhale",
        "Decentralized music streaming platform. Open source.",
        "Funkwhale is a community-driven project that lets you listen and share "
        "music and audio within a decentralized, open network. Self-host your "
        "own instance or join an existing pod. Federated via ActivityPub.",
        "https://funkwhale.audio",
        "design-creative",
        "music,streaming,decentralized,open-source,fediverse",
        "Spotify,SoundCloud",
    ),
    (
        "Audiobookshelf",
        "audiobookshelf",
        "Self-hosted audiobook and podcast server.",
        "Audiobookshelf is a self-hosted audiobook and podcast server. Stream "
        "your audiobook library from any device with progress syncing, chapter "
        "support, and a beautiful mobile app. Supports all major audio formats.",
        "https://audiobookshelf.org",
        "design-creative",
        "audiobook,podcast,self-hosted,media-server,open-source",
        "Audible,Plex",
    ),
    (
        "Navidrome",
        "navidrome",
        "Open-source music server and streamer. Spotify alternative.",
        "Navidrome is a modern, open-source music server compatible with the "
        "Subsonic API. Lightweight, fast, and handles very large music collections. "
        "Web UI included, works with dozens of mobile and desktop clients.",
        "https://navidrome.org",
        "design-creative",
        "music,streaming,self-hosted,open-source,subsonic",
        "Spotify,Plex",
    ),

    # ── Transcription (ai-dev-tools) ──────────────────────────────────────
    (
        "Whisper.cpp",
        "whisper-cpp",
        "Port of OpenAI Whisper for local speech-to-text. Runs on CPU.",
        "Whisper.cpp is a high-performance C/C++ port of OpenAI's Whisper "
        "automatic speech recognition model. Runs entirely locally on CPU "
        "with no cloud dependency. Supports 99 languages and multiple model sizes.",
        "https://github.com/ggerganov/whisper.cpp",
        "ai-dev-tools",
        "transcription,speech-to-text,ai,local,open-source",
        "Google Speech API,AWS Transcribe",
    ),
    (
        "Vosk",
        "vosk",
        "Offline speech recognition toolkit. Works without internet.",
        "Vosk is an offline speech recognition toolkit supporting 20+ languages. "
        "Small model sizes (50MB), works on mobile and embedded devices. "
        "Real-time streaming recognition with Python, Java, C#, and JS APIs.",
        "https://alphacephei.com/vosk",
        "ai-dev-tools",
        "transcription,speech-recognition,offline,ai,open-source",
        "Google Speech API,Whisper",
    ),

    # ── AI Image (ai-dev-tools) ───────────────────────────────────────────
    (
        "Stable Diffusion WebUI",
        "stable-diffusion-webui",
        "Local AI image generation with a full-featured web interface.",
        "AUTOMATIC1111's Stable Diffusion WebUI is the most popular interface "
        "for running Stable Diffusion locally. Txt2img, img2img, inpainting, "
        "LoRA support, and hundreds of extensions. Completely free and private.",
        "https://github.com/AUTOMATIC1111/stable-diffusion-webui",
        "ai-dev-tools",
        "ai-image,stable-diffusion,local,image-generation,open-source",
        "Midjourney,DALL-E",
    ),
    (
        "ComfyUI",
        "comfyui",
        "Node-based Stable Diffusion UI for advanced workflows.",
        "ComfyUI is a powerful, modular Stable Diffusion GUI with a graph/nodes "
        "interface. Build complex image generation workflows visually. Supports "
        "SD 1.5, SDXL, and Flux models with optimized VRAM usage.",
        "https://github.com/comfyanonymous/ComfyUI",
        "ai-dev-tools",
        "ai-image,stable-diffusion,node-based,workflow,open-source",
        "Midjourney,DALL-E",
    ),
    (
        "Fooocus",
        "fooocus",
        "Simplified Stable Diffusion focused on prompting, not tweaking.",
        "Fooocus is a streamlined image generation tool inspired by Midjourney's "
        "simplicity. Minimal settings, maximum quality. Just type a prompt and "
        "get great results. Runs locally with automatic model management.",
        "https://github.com/lllyasviel/Fooocus",
        "ai-dev-tools",
        "ai-image,stable-diffusion,simple,image-generation,open-source",
        "Midjourney,DALL-E",
    ),

    # ── Vector Database / Embeddings (ai-dev-tools) ───────────────────────
    (
        "Chroma",
        "chroma",
        "Open-source embedding database for AI applications.",
        "Chroma is the open-source embedding database designed for AI. Store "
        "embeddings and metadata, query by similarity, and filter results. "
        "Simple Python/JS API, runs in-memory or as a server.",
        "https://trychroma.com",
        "ai-dev-tools",
        "vector-database,embeddings,ai,rag,open-source",
        "Pinecone",
    ),
    (
        "Qdrant",
        "qdrant",
        "Open-source vector database built for AI applications.",
        "Qdrant is a high-performance vector similarity search engine and database. "
        "Built in Rust for speed and reliability. Rich filtering, payload storage, "
        "and distributed deployment. REST and gRPC APIs included.",
        "https://qdrant.tech",
        "ai-dev-tools",
        "vector-database,embeddings,ai,search,open-source",
        "Pinecone,Weaviate",
    ),
    (
        "Weaviate",
        "weaviate",
        "Open-source vector search engine with built-in ML modules.",
        "Weaviate is an open-source vector database that stores objects and "
        "vectors, allowing combined vector and scalar searches. Built-in "
        "modules for text2vec, image2vec, and generative AI integration.",
        "https://weaviate.io",
        "ai-dev-tools",
        "vector-database,search,ai,ml,open-source",
        "Pinecone,Elasticsearch",
    ),
    (
        "Milvus",
        "milvus",
        "Open-source vector database built for scalable AI applications.",
        "Milvus is a cloud-native vector database built for billion-scale "
        "similarity search. Supports multiple index types and distance metrics. "
        "Highly scalable with Kubernetes-native deployment via Zilliz.",
        "https://milvus.io",
        "ai-dev-tools",
        "vector-database,embeddings,ai,scalable,open-source",
        "Pinecone,Qdrant",
    ),

    # ── Low Code (ai-automation) ──────────────────────────────────────────
    (
        "Appsmith",
        "appsmith",
        "Open-source low-code platform for building internal tools.",
        "Appsmith is an open-source framework to build internal tools, admin "
        "panels, and dashboards. Drag-and-drop UI builder with 45+ widgets, "
        "connect to any database or API. Self-host or use the cloud.",
        "https://appsmith.com",
        "ai-automation",
        "low-code,internal-tools,admin-panel,open-source,self-hosted",
        "Retool,Power Apps",
    ),
    (
        "Budibase",
        "budibase",
        "Open-source low-code platform for business applications.",
        "Budibase is an open-source low-code platform for building business apps "
        "in minutes. Internal tools, forms, portals, and approval workflows. "
        "Built-in database or connect to external sources. Self-hostable.",
        "https://budibase.com",
        "ai-automation",
        "low-code,business-apps,internal-tools,open-source,self-hosted",
        "Retool,Power Apps",
    ),
    (
        "ToolJet",
        "tooljet",
        "Open-source low-code platform for building internal tools fast.",
        "ToolJet is an open-source low-code framework to build and deploy "
        "internal tools quickly. Visual app builder, 50+ data source connectors, "
        "and custom JavaScript. Self-host on your own infrastructure.",
        "https://tooljet.com",
        "ai-automation",
        "low-code,internal-tools,open-source,self-hosted,drag-and-drop",
        "Retool,Appsmith",
    ),
    (
        "NocoDB",
        "nocodb",
        "Open-source Airtable alternative. Turn any database into a spreadsheet.",
        "NocoDB turns any MySQL, PostgreSQL, or SQLite database into a smart "
        "spreadsheet. Views include grid, gallery, kanban, and forms. REST APIs "
        "auto-generated. Self-host for free, no vendor lock-in.",
        "https://nocodb.com",
        "ai-automation",
        "low-code,no-code,airtable-alternative,database,open-source",
        "Airtable,Google Sheets",
    ),

    # ── Dashboard Builder / Reporting (analytics-metrics) ─────────────────
    (
        "Apache Superset",
        "apache-superset",
        "Open-source data exploration and visualization platform.",
        "Apache Superset is a modern data exploration and visualization platform. "
        "Create interactive dashboards with rich visualizations from any SQL database. "
        "No-code chart builder, SQL IDE, and semantic layer included.",
        "https://superset.apache.org",
        "analytics-metrics",
        "dashboard,visualization,sql,open-source,business-intelligence",
        "Tableau,Looker,Power BI",
    ),
    (
        "Redash",
        "redash",
        "Open-source dashboards for your SQL queries.",
        "Redash connects to any data source, lets you query using SQL, and "
        "creates beautiful visualizations and dashboards. Share insights across "
        "your organization. Supports 35+ data sources out of the box.",
        "https://redash.io",
        "analytics-metrics",
        "dashboard,sql,visualization,open-source,reporting",
        "Tableau,Metabase",
    ),
    (
        "Lightdash",
        "lightdash",
        "Open-source BI tool for dbt users. Metrics layer included.",
        "Lightdash is an open-source BI tool that connects directly to your dbt "
        "project. Self-serve analytics for your team with a metrics layer, "
        "chart builder, and scheduled deliveries. Self-host or use cloud.",
        "https://lightdash.com",
        "analytics-metrics",
        "dashboard,dbt,business-intelligence,open-source,metrics",
        "Looker,Tableau",
    ),

    # ── ETL / Data Pipeline (developer-tools) ─────────────────────────────
    (
        "Airbyte",
        "airbyte",
        "Open-source data integration and ELT platform.",
        "Airbyte is an open-source data integration platform with 300+ connectors. "
        "Move data from any source to any destination. Incremental syncing, "
        "schema management, and transformation. Self-host or use cloud.",
        "https://airbyte.com",
        "developer-tools",
        "etl,data-integration,elt,open-source,connectors",
        "Fivetran,Stitch",
    ),
    (
        "Meltano",
        "meltano",
        "Open-source ELT for the DataOps era. Singer-based.",
        "Meltano is an open-source platform for running data integration and "
        "transformation pipelines. Built on Singer for extract/load and dbt "
        "for transform. CLI-first, version-controlled, and GitOps-friendly.",
        "https://meltano.com",
        "developer-tools",
        "etl,elt,data-pipeline,open-source,singer",
        "Fivetran,Airbyte",
    ),
    (
        "Apache Airflow",
        "apache-airflow",
        "Workflow orchestration platform for data pipelines.",
        "Apache Airflow is the industry standard for programmatic workflow "
        "orchestration. Author, schedule, and monitor data pipelines as Python "
        "code (DAGs). Extensive operator library and active open-source community.",
        "https://airflow.apache.org",
        "developer-tools",
        "workflow,orchestration,data-pipeline,python,open-source",
        "Prefect,Luigi",
    ),
    (
        "Dagster",
        "dagster",
        "Data orchestration platform with built-in observability.",
        "Dagster is a data orchestration platform that makes data pipelines "
        "reliable and observable. Software-defined assets, type checking, and "
        "a beautiful UI for monitoring. Integrates with dbt, Spark, and more.",
        "https://dagster.io",
        "developer-tools",
        "data-pipeline,orchestration,observability,python,open-source",
        "Airflow,Prefect",
    ),

    # ── Boilerplate / Starter Kit (developer-tools) ───────────────────────
    (
        "Create T3 App",
        "create-t3-app",
        "Full-stack TypeScript starter with Next.js, tRPC, and Prisma.",
        "Create T3 App is the best way to start a full-stack, type-safe Next.js "
        "app. Includes tRPC for end-to-end type-safe APIs, Prisma for the database, "
        "NextAuth.js for auth, and Tailwind CSS for styling.",
        "https://create.t3.gg",
        "developer-tools",
        "boilerplate,typescript,nextjs,starter-kit,full-stack",
        "Create React App,Next.js",
    ),
    (
        "Wasp",
        "wasp",
        "Full-stack web framework with a single config file.",
        "Wasp is a Rails-like framework for React, Node.js, and Prisma. "
        "Describe your app in a simple DSL and Wasp generates the full-stack "
        "code. Auth, CRUD, async jobs, and deployment built in.",
        "https://wasp-lang.dev",
        "developer-tools",
        "framework,full-stack,boilerplate,react,open-source",
        "Next.js,Ruby on Rails",
    ),
    (
        "ShipFast",
        "shipfast",
        "Next.js boilerplate for shipping SaaS products fast.",
        "ShipFast is a Next.js boilerplate with everything you need to ship a "
        "SaaS product quickly. Stripe payments, auth, SEO, emails, database, "
        "and landing page included. Saves weeks of development time.",
        "https://shipfa.st",
        "developer-tools",
        "boilerplate,nextjs,saas,starter-kit,payments",
        "Create T3 App,LaunchDarkly",
    ),
    (
        "Blitz.js",
        "blitz-js",
        "Full-stack React framework built on Next.js.",
        "Blitz.js is a full-stack React framework inspired by Ruby on Rails. "
        "Zero-API data layer lets you import server code directly into components. "
        "Built on Next.js with auth, middleware, and code scaffolding.",
        "https://blitzjs.com",
        "developer-tools",
        "framework,react,full-stack,boilerplate,open-source",
        "Next.js,Ruby on Rails",
    ),

    # ── API Gateway (developer-tools) ─────────────────────────────────────
    (
        "Kong",
        "kong",
        "Open-source API gateway and microservices management platform.",
        "Kong is the most popular open-source API gateway. Rate limiting, "
        "authentication, load balancing, and logging via plugins. Runs in front "
        "of any RESTful API. Available as open-source or enterprise.",
        "https://konghq.com",
        "developer-tools",
        "api-gateway,microservices,rate-limiting,plugins,open-source",
        "AWS API Gateway,Nginx",
    ),
    (
        "Tyk",
        "tyk",
        "Open-source API gateway with analytics and developer portal.",
        "Tyk is an open-source API gateway that handles authentication, rate "
        "limiting, quotas, and versioning. Includes an analytics dashboard "
        "and developer portal. Written in Go for high performance.",
        "https://tyk.io",
        "developer-tools",
        "api-gateway,analytics,rate-limiting,open-source,go",
        "Kong,AWS API Gateway",
    ),

    # ── Kubernetes / Container (developer-tools) ──────────────────────────
    (
        "K3s",
        "k3s",
        "Lightweight Kubernetes by Rancher. Perfect for edge and IoT.",
        "K3s is a lightweight, certified Kubernetes distribution by Rancher. "
        "Single binary under 100MB, designed for resource-constrained environments. "
        "Perfect for edge computing, IoT, CI/CD, and development.",
        "https://k3s.io",
        "developer-tools",
        "kubernetes,container,lightweight,edge,open-source",
        "Kubernetes,Docker Swarm",
    ),
    (
        "Portainer",
        "portainer",
        "Container management UI for Docker and Kubernetes.",
        "Portainer is a lightweight management UI for Docker, Docker Swarm, "
        "and Kubernetes. Deploy, manage, and troubleshoot containers through "
        "an intuitive web interface. Community edition is free and open-source.",
        "https://portainer.io",
        "developer-tools",
        "container,docker,kubernetes,management-ui,open-source",
        "Docker Desktop,Rancher",
    ),
    (
        "Rancher",
        "rancher",
        "Complete Kubernetes management platform. Open source.",
        "Rancher is an open-source platform for managing Kubernetes clusters "
        "across any infrastructure. Centralized authentication, monitoring, "
        "alerting, and catalog of Helm charts. Enterprise Kubernetes made simple.",
        "https://rancher.com",
        "developer-tools",
        "kubernetes,container,management,multi-cluster,open-source",
        "OpenShift,Google GKE",
    ),

    # ── Serverless (developer-tools) ──────────────────────────────────────
    (
        "OpenFaaS",
        "openfaas",
        "Serverless functions made simple for Docker and Kubernetes.",
        "OpenFaaS makes it simple to deploy serverless functions and microservices "
        "to Docker or Kubernetes. Write functions in any language, scale to zero, "
        "and manage via CLI, UI, or REST API. Community-driven and open-source.",
        "https://openfaas.com",
        "developer-tools",
        "serverless,functions,docker,kubernetes,open-source",
        "AWS Lambda,Google Cloud Functions",
    ),
    (
        "Vercel",
        "vercel",
        "Frontend cloud platform with serverless functions and edge network.",
        "Vercel is the platform for frontend developers. Instant deployments, "
        "serverless functions, edge network, and built-in CI/CD. Created by "
        "the team behind Next.js. Generous free tier for personal projects.",
        "https://vercel.com",
        "developer-tools",
        "serverless,deployment,frontend,edge,nextjs",
        "Netlify,AWS Amplify",
    ),

    # ── Spreadsheet (developer-tools) ─────────────────────────────────────
    (
        "Baserow",
        "baserow",
        "Open-source Airtable alternative. No-code database platform.",
        "Baserow is an open-source no-code database platform. Create databases "
        "with a spreadsheet-like interface, build forms, and share views. "
        "REST API included. Self-host or use the managed cloud.",
        "https://baserow.io",
        "developer-tools",
        "spreadsheet,no-code,database,airtable-alternative,open-source",
        "Airtable,Google Sheets",
    ),
    (
        "Grist",
        "grist",
        "Open-source modern spreadsheet with Python formulas.",
        "Grist combines the familiarity of spreadsheets with the power of a "
        "database. Python formulas, relational data, custom layouts, and access "
        "rules. Self-host or use the free cloud tier. Open-source.",
        "https://getgrist.com",
        "developer-tools",
        "spreadsheet,database,python,no-code,open-source",
        "Airtable,Google Sheets,Excel",
    ),

    # ── Accounting / Inventory (invoicing-billing) ────────────────────────
    (
        "Akaunting",
        "akaunting",
        "Open-source accounting software for small businesses.",
        "Akaunting is free, open-source accounting software for small businesses "
        "and freelancers. Invoicing, expense tracking, bill management, and "
        "financial reports. App store with extensions for payroll, inventory, and more.",
        "https://akaunting.com",
        "invoicing-billing",
        "accounting,invoicing,open-source,self-hosted,small-business",
        "QuickBooks,Xero,FreshBooks",
    ),
    (
        "ERPNext",
        "erpnext",
        "Open-source ERP with accounting, inventory, and HR modules.",
        "ERPNext is a comprehensive open-source ERP system. Accounting, inventory, "
        "manufacturing, CRM, HR, and project management in one platform. "
        "Built on the Frappe framework. Self-host or use managed hosting.",
        "https://erpnext.com",
        "invoicing-billing",
        "erp,accounting,inventory,open-source,self-hosted",
        "SAP,QuickBooks,NetSuite",
    ),
    (
        "InvoicePlane",
        "invoiceplane",
        "Open-source invoicing application for freelancers.",
        "InvoicePlane is a self-hosted invoicing application for freelancers "
        "and small businesses. Create quotes, invoices, and track payments. "
        "Simple setup, clean interface, and completely free to use.",
        "https://invoiceplane.com",
        "invoicing-billing",
        "invoicing,freelancer,open-source,self-hosted,billing",
        "FreshBooks,Wave",
    ),

    # ── Design System / Icons / Fonts (design-creative) ───────────────────
    (
        "Iconify",
        "iconify",
        "Universal icon framework with 200,000+ open-source icons.",
        "Iconify provides access to 200,000+ icons from 150+ icon sets through "
        "one unified framework. Use with any framework — React, Vue, Svelte, "
        "or plain HTML. On-demand loading means zero bloat.",
        "https://iconify.design",
        "design-creative",
        "icons,icon-framework,open-source,react,svg",
        "Font Awesome,Material Icons",
    ),
    (
        "Heroicons",
        "heroicons",
        "Beautiful hand-crafted SVG icons by the Tailwind CSS team.",
        "Heroicons is a set of free, MIT-licensed high-quality SVG icons. "
        "Available in outline, solid, and mini styles. Built by the makers "
        "of Tailwind CSS. Drop-in React and Vue components included.",
        "https://heroicons.com",
        "design-creative",
        "icons,svg,tailwind,open-source,react",
        "Font Awesome,Feather Icons",
    ),
    (
        "Fontsource",
        "fontsource",
        "Self-host open-source fonts via npm packages.",
        "Fontsource provides npm packages for every Google Font and many other "
        "open-source fonts. Import fonts as dependencies, get automatic subsetting "
        "and optimization. No external requests, better performance.",
        "https://fontsource.org",
        "design-creative",
        "fonts,typography,npm,self-hosted,open-source",
        "Google Fonts,Adobe Fonts",
    ),
    (
        "Coolors",
        "coolors",
        "Color palette generator for designers and developers.",
        "Coolors is a fast color palette generator. Generate harmonious color "
        "schemes with a tap of the spacebar. Export to CSS, SCSS, SVG, PNG, or "
        "PDF. Explore trending palettes and build a palette library.",
        "https://coolors.co",
        "design-creative",
        "color,palette,design,css,tool",
        "Adobe Color,Colour Lovers",
    ),
    (
        "Balsamiq",
        "balsamiq",
        "Rapid wireframing tool for quick UI mockups.",
        "Balsamiq is a wireframing tool that reproduces the experience of "
        "sketching on a whiteboard. Low-fidelity mockups help teams focus on "
        "structure over visual design. Perfect for early-stage product ideation.",
        "https://balsamiq.com",
        "design-creative",
        "wireframing,prototyping,mockup,ui-design,low-fidelity",
        "Figma,Sketch",
    ),
    (
        "Framer",
        "framer",
        "Design and publish websites visually. No code required.",
        "Framer is a visual website builder that lets designers create production "
        "sites without code. Component-based design, animations, CMS, and "
        "SEO tools included. Publish to a fast global CDN with one click.",
        "https://framer.com",
        "design-creative",
        "website-builder,design,no-code,prototyping,publishing",
        "Webflow,Squarespace",
    ),

    # ── Chatbot / AI Writing (ai-dev-tools) ───────────────────────────────
    (
        "Botpress",
        "botpress",
        "Open-source chatbot platform with visual flow builder.",
        "Botpress is an open-source platform for building AI chatbots. Visual "
        "conversation flow editor, NLU engine, multi-channel deployment, and "
        "built-in analytics. Integrates with LLMs for generative responses.",
        "https://botpress.com",
        "ai-dev-tools",
        "chatbot,ai,conversational,open-source,nlu",
        "Dialogflow,Rasa",
    ),
    (
        "Open WebUI",
        "open-webui",
        "Self-hosted AI chat interface for local and cloud LLMs.",
        "Open WebUI is a self-hosted, feature-rich AI chat interface. Works "
        "with Ollama, OpenAI, and any OpenAI-compatible API. Multi-model chat, "
        "document RAG, web browsing, and image generation. Beautiful UI.",
        "https://openwebui.com",
        "ai-dev-tools",
        "ai-chat,llm,self-hosted,open-source,ollama",
        "ChatGPT,Claude",
    ),
    (
        "LibreChat",
        "librechat",
        "Open-source ChatGPT clone with multi-provider support.",
        "LibreChat is an open-source AI chat platform that supports OpenAI, "
        "Anthropic, Google, and local models in one interface. Conversations, "
        "presets, plugins, and multi-user support. Self-host for full privacy.",
        "https://librechat.ai",
        "ai-dev-tools",
        "ai-chat,multi-provider,open-source,self-hosted,llm",
        "ChatGPT",
    ),

    # ── Data Visualization (analytics-metrics) ────────────────────────────
    (
        "Grafana",
        "grafana",
        "Open-source observability and data visualization platform.",
        "Grafana is the leading open-source platform for monitoring and "
        "observability. Create beautiful dashboards from Prometheus, InfluxDB, "
        "Elasticsearch, and 100+ data sources. Alerting and annotation included.",
        "https://grafana.com",
        "analytics-metrics",
        "visualization,monitoring,dashboard,open-source,observability",
        "Datadog,New Relic",
    ),
    (
        "Observable",
        "observable",
        "Collaborative data visualization and notebooks platform.",
        "Observable is a platform for exploring data and building interactive "
        "visualizations. JavaScript notebooks with reactive data flow. "
        "Built by the creator of D3.js. Share and embed charts anywhere.",
        "https://observablehq.com",
        "analytics-metrics",
        "visualization,notebooks,data-exploration,javascript,d3",
        "Jupyter,Tableau",
    ),
]


def main():
    print(f"Seeding Round 3 tools at: {DB_PATH}")

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

    # Category breakdown
    print("\nPer-category counts:")
    rows = conn.execute(
        """SELECT c.slug, c.name, COUNT(t.id)
           FROM categories c
           LEFT JOIN tools t ON t.category_id = c.id AND t.status = 'approved'
           GROUP BY c.id
           ORDER BY COUNT(t.id) DESC"""
    ).fetchall()
    for slug, name, count in rows:
        print(f"  {count:3d}  {name} ({slug})")

    conn.close()


if __name__ == "__main__":
    main()

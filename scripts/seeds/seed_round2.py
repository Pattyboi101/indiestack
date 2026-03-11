#!/usr/bin/env python3
"""Seed IndieStack with ~80 tools to fill search gaps (Round 2).

Covers queries that returned 0-2 results: cache, image optimization,
logging, password manager, translation, vpn, wiki, ab testing, backup,
comments, ecommerce, error tracking, forum, push notifications, queue,
realtime, charts, ci/cd, feature flags, sms, status page, blog/cms,
pdf, video, maps, documentation.

Usage:
    python3 seed_round2.py

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
    # ══════════════════════════════════════════════════════════════════════
    # ZERO results — critical gaps
    # ══════════════════════════════════════════════════════════════════════

    # ── Cache (developer-tools) ───────────────────────────────────────────
    (
        "Redis",
        "redis",
        "In-memory data store for caching, queues, and real-time apps.",
        "Redis is the world's most popular in-memory data structure store. "
        "Use it as a cache, message broker, streaming engine, or database. "
        "Sub-millisecond latency with support for strings, hashes, lists, sets, and sorted sets.",
        "https://redis.io",
        "developer-tools",
        "cache,in-memory,database,open-source,self-hosted",
        "Memcached,Amazon ElastiCache",
    ),
    (
        "Dragonfly",
        "dragonfly",
        "Modern Redis replacement. 25x faster, multi-threaded.",
        "Dragonfly is a modern in-memory data store fully compatible with Redis and Memcached APIs. "
        "Multi-threaded architecture delivers 25x more throughput than Redis on a single instance. "
        "Drop-in replacement with no code changes needed.",
        "https://dragonflydb.io",
        "developer-tools",
        "cache,in-memory,redis-alternative,open-source,high-performance",
        "Redis,Memcached",
    ),
    (
        "KeyDB",
        "keydb",
        "Multi-threaded Redis fork with active replication.",
        "KeyDB is a high-performance fork of Redis with multi-threading, active replication, "
        "and flash storage support. Fully compatible with Redis clients and APIs while delivering "
        "significantly higher throughput on multi-core machines.",
        "https://docs.keydb.dev",
        "developer-tools",
        "cache,in-memory,redis-fork,open-source,multi-threaded",
        "Redis",
    ),
    (
        "Memcached",
        "memcached",
        "Distributed memory caching system. Simple and battle-tested.",
        "Memcached is a high-performance, distributed memory object caching system. "
        "Used by Wikipedia, Facebook, and Twitter to speed up dynamic web apps by "
        "alleviating database load. Simple key-value store that just works.",
        "https://memcached.org",
        "developer-tools",
        "cache,in-memory,distributed,open-source,key-value",
        "Amazon ElastiCache",
    ),

    # ── Image Optimization (developer-tools) ──────────────────────────────
    (
        "imgproxy",
        "imgproxy",
        "Fast, secure image processing server. Resize on the fly.",
        "imgproxy is a blazing-fast image processing server written in Go. "
        "Resize, crop, and convert images on the fly with URL-based transformations. "
        "Supports WebP, AVIF, and JPEG XL output. Secure by design with signature verification.",
        "https://imgproxy.net",
        "developer-tools",
        "image-optimization,image-processing,open-source,self-hosted,go",
        "Cloudinary,Imgix",
    ),
    (
        "Thumbor",
        "thumbor",
        "Smart image cropping and resizing service. Open source.",
        "Thumbor is an open-source smart image service. It crops and resizes images intelligently "
        "using facial and feature detection. On-demand image manipulation via URL parameters "
        "with built-in caching and CDN support.",
        "https://thumbor.org",
        "developer-tools",
        "image-optimization,image-processing,open-source,python,smart-crop",
        "Cloudinary,Imgix",
    ),
    (
        "Squoosh",
        "squoosh",
        "Browser-based image compression by Google Chrome Labs.",
        "Squoosh is a free image compression web app from Google Chrome Labs. "
        "Compare codecs side by side, adjust quality settings in real time, and export "
        "optimized images in WebP, AVIF, JPEG XL, and more. Works entirely in the browser.",
        "https://squoosh.app",
        "developer-tools",
        "image-optimization,image-compression,free,browser-based,webp",
        "TinyPNG,Cloudinary",
    ),

    # ── Logging (monitoring-uptime) ───────────────────────────────────────
    (
        "Grafana Loki",
        "grafana-loki",
        "Log aggregation system by Grafana Labs. Like Prometheus for logs.",
        "Loki is a horizontally scalable, multi-tenant log aggregation system inspired by Prometheus. "
        "It indexes only metadata (labels), making it cost-effective and fast. "
        "Pairs perfectly with Grafana for querying and visualizing logs.",
        "https://grafana.com/oss/loki/",
        "monitoring-uptime",
        "logging,log-aggregation,open-source,grafana,observability",
        "Splunk,Datadog,Elastic",
    ),
    (
        "Graylog",
        "graylog",
        "Centralized log management and SIEM. Open source.",
        "Graylog is an open-source log management platform for collecting, indexing, and analyzing "
        "structured and unstructured data. Real-time search, dashboards, alerting, and compliance "
        "reporting. Scales from small teams to enterprise.",
        "https://graylog.org",
        "monitoring-uptime",
        "logging,log-management,open-source,siem,search",
        "Splunk,Datadog",
    ),
    (
        "Vector",
        "vector",
        "High-performance observability data pipeline. By Datadog.",
        "Vector is a lightweight, ultra-fast tool for building observability pipelines. "
        "Collect, transform, and route logs, metrics, and traces from any source to any destination. "
        "Written in Rust for reliability and performance. Open source.",
        "https://vector.dev",
        "monitoring-uptime",
        "logging,observability,data-pipeline,open-source,rust",
        "Fluentd,Logstash",
    ),

    # ── Password Manager (authentication) ─────────────────────────────────
    (
        "Bitwarden",
        "bitwarden",
        "Open-source password manager for individuals and teams.",
        "Bitwarden is a trusted open-source password manager. Securely store, share, "
        "and manage passwords across all devices. End-to-end encryption, self-host option, "
        "and generous free tier. Supports TOTP, passkeys, and Send for secure sharing.",
        "https://bitwarden.com",
        "authentication",
        "password-manager,open-source,self-hosted,encryption,security",
        "1Password,LastPass,Dashlane",
    ),
    (
        "Vaultwarden",
        "vaultwarden",
        "Lightweight Bitwarden-compatible server. Self-host on minimal hardware.",
        "Vaultwarden is an unofficial Bitwarden-compatible server written in Rust. "
        "Uses far fewer resources than the official server, making it perfect for self-hosting "
        "on a Raspberry Pi or small VPS. Full Bitwarden client compatibility.",
        "https://github.com/dani-garcia/vaultwarden",
        "authentication",
        "password-manager,self-hosted,open-source,rust,lightweight",
        "1Password,LastPass",
    ),
    (
        "Passbolt",
        "passbolt",
        "Open-source password manager built for teams.",
        "Passbolt is a security-first, open-source password manager designed for team collaboration. "
        "Browser extension, CLI, and mobile apps. End-to-end encryption with OpenPGP. "
        "Self-host or use the managed cloud. SOC2 and GDPR compliant.",
        "https://passbolt.com",
        "authentication",
        "password-manager,team,open-source,self-hosted,encryption",
        "1Password Teams,LastPass Business",
    ),

    # ── Translation / Localization (developer-tools) ──────────────────────
    (
        "Weblate",
        "weblate",
        "Open-source continuous localization platform.",
        "Weblate is a web-based continuous localization tool. Tight integration with Git repos, "
        "automatic translation suggestions, quality checks, and a translation memory. "
        "Self-host or use the managed service. 100+ file format support.",
        "https://weblate.org",
        "developer-tools",
        "translation,localization,open-source,self-hosted,i18n",
        "Crowdin,Lokalise,Phrase",
    ),
    (
        "Tolgee",
        "tolgee",
        "Developer-friendly localization platform. Open source.",
        "Tolgee is an open-source localization platform that lets developers translate apps "
        "without touching code. In-context editing, machine translation, and SDK integrations "
        "for React, Angular, Vue, and more. Self-host or use the cloud.",
        "https://tolgee.io",
        "developer-tools",
        "translation,localization,open-source,i18n,developer-tools",
        "Crowdin,Lokalise",
    ),
    (
        "Crowdin",
        "crowdin",
        "Localization management platform for agile teams.",
        "Crowdin is a cloud-based localization management platform used by teams worldwide. "
        "Over-the-air content delivery, in-context editing, TM and glossaries, "
        "and 600+ integrations including GitHub, GitLab, and Figma.",
        "https://crowdin.com",
        "developer-tools",
        "translation,localization,cloud,i18n,collaboration",
        "Lokalise,Phrase,Transifex",
    ),

    # ── VPN (developer-tools) ─────────────────────────────────────────────
    (
        "WireGuard",
        "wireguard",
        "Modern, fast VPN tunnel. Simple and cryptographically sound.",
        "WireGuard is an extremely simple yet fast modern VPN that utilizes state-of-the-art "
        "cryptography. Designed for ease of implementation and simplicity. "
        "Runs on Linux, Windows, macOS, BSD, iOS, and Android. Now in the Linux kernel.",
        "https://wireguard.com",
        "developer-tools",
        "vpn,networking,open-source,security,linux",
        "OpenVPN,IPsec",
    ),
    (
        "Tailscale",
        "tailscale",
        "Zero-config VPN built on WireGuard. Mesh networking made easy.",
        "Tailscale creates a secure mesh network between your devices using WireGuard under the hood. "
        "No firewall ports to open, no config files to manage. SSO integration, ACLs, "
        "and MagicDNS. Free for personal use with up to 100 devices.",
        "https://tailscale.com",
        "developer-tools",
        "vpn,mesh-network,wireguard,zero-config,networking",
        "OpenVPN,Cisco AnyConnect",
    ),
    (
        "NetBird",
        "netbird",
        "Open-source zero-trust networking. WireGuard-based.",
        "NetBird is an open-source platform for creating secure private networks. "
        "Peer-to-peer WireGuard connections with SSO authentication, access control policies, "
        "and automatic key rotation. Self-host the management server or use the cloud.",
        "https://netbird.io",
        "developer-tools",
        "vpn,zero-trust,wireguard,open-source,networking",
        "Tailscale,Cloudflare WARP",
    ),

    # ── Wiki / Knowledge Base (developer-tools) ───────────────────────────
    (
        "BookStack",
        "bookstack",
        "Simple, self-hosted wiki platform. Organize content by books.",
        "BookStack is a free, open-source wiki platform with a simple, easy-to-use interface. "
        "Organize content in a book-like hierarchy: shelves, books, chapters, and pages. "
        "WYSIWYG and Markdown editing, diagrams, full-text search, and LDAP/SAML auth.",
        "https://bookstackapp.com",
        "developer-tools",
        "wiki,knowledge-base,open-source,self-hosted,documentation",
        "Confluence,Notion,GitBook",
    ),
    (
        "Wiki.js",
        "wiki-js",
        "Powerful open-source wiki with a modern interface.",
        "Wiki.js is a powerful, extensible open-source wiki built on Node.js. "
        "Multiple editors (Markdown, visual, code), Git-backed storage, full-text search, "
        "and granular permissions. Supports PostgreSQL, MySQL, MariaDB, and SQLite.",
        "https://js.wiki",
        "developer-tools",
        "wiki,knowledge-base,open-source,self-hosted,nodejs",
        "Confluence,Notion",
    ),
    (
        "Outline",
        "outline",
        "Beautiful wiki and knowledge base for teams. Open source.",
        "Outline is a fast, collaborative team knowledge base. Beautiful Markdown editor, "
        "real-time collaboration, structured collections, and integrations with Slack, "
        "Figma, and more. Self-host or use the managed cloud.",
        "https://getoutline.com",
        "developer-tools",
        "wiki,knowledge-base,open-source,collaboration,markdown",
        "Notion,Confluence,Slite",
    ),
    (
        "Slite",
        "slite",
        "Team knowledge base with AI-powered search and organization.",
        "Slite is a knowledge base built for modern teams. AI-powered search finds answers "
        "across all your docs instantly. Clean editor, verification workflows to keep docs "
        "up to date, and integrations with Slack, Jira, and GitHub.",
        "https://slite.com",
        "developer-tools",
        "wiki,knowledge-base,ai-search,team,collaboration",
        "Notion,Confluence",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # ONE result — needs more
    # ══════════════════════════════════════════════════════════════════════

    # ── A/B Testing (analytics-metrics) ───────────────────────────────────
    (
        "GrowthBook",
        "growthbook",
        "Open-source feature flagging and A/B testing platform.",
        "GrowthBook is an open-source platform for feature flags and experimentation. "
        "Run A/B tests with Bayesian statistics, analyze results with your existing data warehouse, "
        "and manage feature rollouts. SDKs for all major languages.",
        "https://growthbook.io",
        "analytics-metrics",
        "ab-testing,feature-flags,open-source,experimentation,analytics",
        "LaunchDarkly,Optimizely",
    ),
    (
        "Flagsmith",
        "flagsmith",
        "Open-source feature flags, remote config, and A/B testing.",
        "Flagsmith is an open-source feature flag and remote config service. "
        "Manage features across web, mobile, and server-side apps. Built-in A/B testing, "
        "user segmentation, and audit logs. Self-host or use the managed cloud.",
        "https://flagsmith.com",
        "analytics-metrics",
        "ab-testing,feature-flags,open-source,remote-config,self-hosted",
        "LaunchDarkly,Split",
    ),

    # ── Backup (file-management) ──────────────────────────────────────────
    (
        "Restic",
        "restic",
        "Fast, secure, efficient backup program. Open source.",
        "Restic is a modern backup program that is fast, efficient, and secure. "
        "Encrypted, deduplicated backups to local disk, SFTP, S3, Azure, GCS, and more. "
        "Cross-platform with snapshot-based management. Easy to use, hard to misuse.",
        "https://restic.net",
        "file-management",
        "backup,encryption,open-source,deduplication,cross-platform",
        "Backblaze,CrashPlan",
    ),
    (
        "Duplicati",
        "duplicati",
        "Free backup software with encryption and cloud storage support.",
        "Duplicati is a free, open-source backup client for securely storing encrypted, "
        "incremental, compressed backups on cloud storage and remote file servers. "
        "Web UI, scheduler, and support for 20+ storage backends including S3, GCS, and FTP.",
        "https://duplicati.com",
        "file-management",
        "backup,encryption,open-source,cloud-storage,scheduled",
        "Backblaze,CrashPlan",
    ),
    (
        "BorgBackup",
        "borgbackup",
        "Deduplicating archiver with compression and encryption.",
        "BorgBackup (Borg) is a deduplicating backup program with optional compression and "
        "authenticated encryption. Efficiently handles daily backups with excellent deduplication "
        "ratios. Supports SSH remote repos and has a proven track record of reliability.",
        "https://borgbackup.org",
        "file-management",
        "backup,deduplication,encryption,open-source,linux",
        "Backblaze,Duplicity",
    ),

    # ── Comments (feedback-reviews) ───────────────────────────────────────
    (
        "Cusdis",
        "cusdis",
        "Lightweight, privacy-first comment system. Open source.",
        "Cusdis is a lightweight, privacy-first comment system alternative to Disqus. "
        "Tiny embed script (~5KB gzipped), no tracking, email notifications for new comments, "
        "and a simple dashboard for moderation. Self-host or use the hosted version.",
        "https://cusdis.com",
        "feedback-reviews",
        "comments,privacy,open-source,lightweight,self-hosted",
        "Disqus",
    ),
    (
        "Giscus",
        "giscus",
        "Comments powered by GitHub Discussions. Free and open source.",
        "Giscus uses GitHub Discussions as a comment system for your website. "
        "Visitors sign in with GitHub, and comments are stored as Discussions in your repo. "
        "Free, no tracking, customizable themes, and supports reactions.",
        "https://giscus.app",
        "feedback-reviews",
        "comments,github,open-source,free,discussions",
        "Disqus",
    ),
    (
        "Utterances",
        "utterances",
        "Lightweight comments widget built on GitHub Issues.",
        "Utterances is a lightweight comments widget built on GitHub Issues. "
        "No tracking, no ads, no lock-in. Comments stored as GitHub Issues in your repo. "
        "Open source, free, and styled with Primer CSS for a clean look.",
        "https://utteranc.es",
        "feedback-reviews",
        "comments,github,open-source,free,lightweight",
        "Disqus",
    ),

    # ── Ecommerce (payments) ──────────────────────────────────────────────
    (
        "Medusa",
        "medusa",
        "Open-source headless commerce engine. Shopify alternative.",
        "Medusa is an open-source composable commerce engine for developers. "
        "Build custom storefronts, manage products, orders, and customers with a modular "
        "architecture. Headless by design with full API access. Self-host for free.",
        "https://medusajs.com",
        "payments",
        "ecommerce,headless,open-source,self-hosted,commerce",
        "Shopify,BigCommerce",
    ),
    (
        "Saleor",
        "saleor",
        "GraphQL-first headless ecommerce platform. Open source.",
        "Saleor is a high-performance, GraphQL-first ecommerce platform. "
        "Multi-channel commerce, flexible product modeling, and a dashboard for store management. "
        "Built with Python/Django and React. Self-host or use Saleor Cloud.",
        "https://saleor.io",
        "payments",
        "ecommerce,graphql,open-source,headless,python",
        "Shopify,Magento",
    ),
    (
        "Bagisto",
        "bagisto",
        "Open-source Laravel ecommerce framework.",
        "Bagisto is a free, open-source ecommerce framework built on Laravel and Vue.js. "
        "Multi-inventory, multi-currency, multi-locale support out of the box. "
        "Beautiful storefront with admin panel, REST API, and GraphQL API.",
        "https://bagisto.com",
        "payments",
        "ecommerce,laravel,open-source,self-hosted,multi-currency",
        "Shopify,WooCommerce",
    ),

    # ── Error Tracking (monitoring-uptime) ────────────────────────────────
    (
        "GlitchTip",
        "glitchtip",
        "Open-source error tracking. Simple Sentry alternative.",
        "GlitchTip is a simple, open-source error tracking tool compatible with the Sentry SDK. "
        "Track errors, monitor uptime, and get alerts. Lightweight and easy to self-host. "
        "Fraction of the cost and complexity of Sentry.",
        "https://glitchtip.com",
        "monitoring-uptime",
        "error-tracking,open-source,self-hosted,sentry-compatible,monitoring",
        "Sentry,Bugsnag",
    ),
    (
        "Highlight",
        "highlight-io",
        "Full-stack monitoring: errors, logs, traces, and session replay.",
        "Highlight is an open-source full-stack monitoring platform. Session replay, "
        "error monitoring, logging, and distributed tracing in one tool. "
        "SDKs for all major frameworks. Self-host or use the managed cloud.",
        "https://highlight.io",
        "monitoring-uptime",
        "error-tracking,session-replay,open-source,monitoring,logging",
        "Sentry,LogRocket,Datadog",
    ),

    # ── Forum (customer-support) ──────────────────────────────────────────
    (
        "Discourse",
        "discourse",
        "Civilized discussion platform. Modern forum software.",
        "Discourse is the 100% open-source discussion platform for community forums, "
        "customer support, and team collaboration. Trust levels, badges, moderation tools, "
        "and real-time notifications. Self-host or use managed hosting.",
        "https://discourse.org",
        "customer-support",
        "forum,community,open-source,self-hosted,discussion",
        "vBulletin,phpBB,Circle",
    ),
    (
        "Flarum",
        "flarum",
        "Simple, beautiful forum software. Lightweight and fast.",
        "Flarum is a delightfully simple forum for your website. Fast, extensible, "
        "and mobile-first with a clean, modern UI. Built with PHP and Mithril.js. "
        "Rich extension ecosystem for tags, mentions, likes, and more.",
        "https://flarum.org",
        "customer-support",
        "forum,community,open-source,php,lightweight",
        "phpBB,Discourse",
    ),
    (
        "NodeBB",
        "nodebb",
        "Modern forum platform built on Node.js. Real-time features.",
        "NodeBB is a next-generation forum platform built on Node.js with real-time "
        "streaming discussions. Social features, powerful moderation tools, "
        "and integrations with WordPress, Slack, and more. Themes and plugins ecosystem.",
        "https://nodebb.org",
        "customer-support",
        "forum,community,open-source,nodejs,real-time",
        "phpBB,Discourse",
    ),

    # ── Push Notifications (customer-support) ─────────────────────────────
    (
        "OneSignal",
        "onesignal",
        "Multi-channel push notification service. Free tier available.",
        "OneSignal is the market-leading push notification service for web and mobile apps. "
        "Push, email, SMS, and in-app messaging from one platform. Segmentation, A/B testing, "
        "and analytics. Free plan supports unlimited mobile subscribers.",
        "https://onesignal.com",
        "customer-support",
        "push-notifications,messaging,free,mobile,web",
        "Firebase Cloud Messaging,Braze",
    ),
    (
        "Novu",
        "novu",
        "Open-source notification infrastructure for developers.",
        "Novu is an open-source notification infrastructure for managing all communication "
        "channels in one place: push, email, SMS, in-app, and chat. Workflow engine, "
        "content management, and subscriber preferences. Self-host or use the cloud.",
        "https://novu.co",
        "customer-support",
        "push-notifications,open-source,notification-infrastructure,multi-channel,developer-tools",
        "Twilio,SendGrid,Firebase",
    ),
    (
        "Ntfy",
        "ntfy",
        "Simple HTTP-based pub-sub push notifications. Open source.",
        "Ntfy is a simple HTTP-based pub/sub notification service. Send notifications "
        "to your phone or desktop via PUT/POST requests. No signup, no app required "
        "(though apps exist). Self-host or use the free public server.",
        "https://ntfy.sh",
        "customer-support",
        "push-notifications,open-source,self-hosted,simple,http",
        "Pushover,Firebase",
    ),

    # ── Queue / Task Processing (developer-tools) ─────────────────────────
    (
        "BullMQ",
        "bullmq",
        "Premium message queue for Node.js based on Redis.",
        "BullMQ is the fastest, most reliable Redis-based queue for Node.js. "
        "Job scheduling, rate limiting, repeatable jobs, and real-time events. "
        "Used by thousands of companies. Bull Board UI for monitoring.",
        "https://bullmq.io",
        "developer-tools",
        "queue,message-queue,nodejs,redis,job-scheduling",
        "Amazon SQS,Sidekiq",
    ),
    (
        "Temporal",
        "temporal",
        "Durable execution platform for reliable distributed systems.",
        "Temporal is an open-source durable execution platform. Write workflows as code "
        "in Go, Java, TypeScript, Python, or .NET with automatic retries, timeouts, "
        "and error handling. Makes distributed systems reliable without the complexity.",
        "https://temporal.io",
        "developer-tools",
        "queue,workflow,distributed-systems,open-source,durable-execution",
        "AWS Step Functions,Airflow",
    ),
    (
        "RabbitMQ",
        "rabbitmq",
        "Reliable message broker for distributed systems. Battle-tested.",
        "RabbitMQ is the most widely deployed open-source message broker. "
        "Supports AMQP, MQTT, and STOMP protocols. Routing, clustering, "
        "high availability, and management UI. Handles millions of messages per second.",
        "https://rabbitmq.com",
        "developer-tools",
        "queue,message-broker,open-source,amqp,distributed",
        "Amazon SQS,Azure Service Bus",
    ),

    # ── Realtime (developer-tools) ────────────────────────────────────────
    (
        "Soketi",
        "soketi",
        "Open-source WebSocket server. Pusher-compatible.",
        "Soketi is a free, open-source WebSocket server compatible with Pusher. "
        "Drop-in replacement that you can self-host. Built with uWebSockets.js for "
        "blazing performance. Horizontal scaling with Redis or NATS.",
        "https://soketi.app",
        "developer-tools",
        "realtime,websocket,open-source,pusher-compatible,self-hosted",
        "Pusher,Ably",
    ),
    (
        "Centrifugo",
        "centrifugo",
        "Scalable real-time messaging server. Language-agnostic.",
        "Centrifugo is a scalable real-time messaging server. Send messages to online users "
        "via WebSocket, SSE, or HTTP streaming. Works with any backend language. "
        "Supports presence, history, and channel permissions. Written in Go.",
        "https://centrifugal.dev",
        "developer-tools",
        "realtime,websocket,open-source,messaging,go",
        "Pusher,Ably,Firebase",
    ),
    (
        "Mercure",
        "mercure",
        "Real-time API protocol built on Server-Sent Events. Open source.",
        "Mercure is an open-source protocol and server for real-time communications. "
        "Built on Server-Sent Events (SSE) for maximum compatibility. Auto-discovery, "
        "authorization, and native browser support. Perfect for Symfony and API Platform.",
        "https://mercure.rocks",
        "developer-tools",
        "realtime,sse,open-source,protocol,api",
        "Pusher,Firebase",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # TWO results — flesh out
    # ══════════════════════════════════════════════════════════════════════

    # ── Charts (design-creative) ──────────────────────────────────────────
    (
        "Apache ECharts",
        "apache-echarts",
        "Powerful interactive charting and visualization library.",
        "Apache ECharts is a powerful, interactive charting and data visualization library. "
        "Supports line, bar, scatter, pie, candlestick, heatmaps, geographic maps, "
        "and 3D charts. Highly customizable with built-in animations and responsive design.",
        "https://echarts.apache.org",
        "design-creative",
        "charts,data-visualization,open-source,javascript,interactive",
        "Chart.js,Highcharts,D3.js",
    ),
    (
        "Metabase",
        "metabase",
        "Business intelligence and analytics with no-code dashboards.",
        "Metabase is an open-source business intelligence tool that lets anyone ask questions "
        "about their data. Connect to any database, create charts and dashboards with no SQL. "
        "Embed analytics, set up alerts, and share insights. Self-host or use the cloud.",
        "https://metabase.com",
        "design-creative",
        "charts,business-intelligence,open-source,analytics,no-code",
        "Tableau,Looker,Power BI",
    ),

    # ── CI/CD (developer-tools) ───────────────────────────────────────────
    (
        "Woodpecker CI",
        "woodpecker-ci",
        "Simple, container-native CI/CD engine. Drone fork.",
        "Woodpecker CI is a community fork of Drone, providing a simple, container-native "
        "CI/CD engine. Pipeline-as-code via YAML, multi-platform builds, "
        "and plugins ecosystem. Self-host on minimal resources.",
        "https://woodpecker-ci.org",
        "developer-tools",
        "ci-cd,continuous-integration,open-source,containers,self-hosted",
        "GitHub Actions,GitLab CI,CircleCI",
    ),
    (
        "Drone CI",
        "drone-ci",
        "Container-native CI/CD platform. Pipeline as code.",
        "Drone is a self-service, container-native continuous integration and delivery platform. "
        "Configuration as code using Docker containers. Integrates with GitHub, GitLab, "
        "Bitbucket, and Gitea. Scales from single machine to massive clusters.",
        "https://drone.io",
        "developer-tools",
        "ci-cd,continuous-integration,open-source,containers,docker",
        "GitHub Actions,Jenkins,CircleCI",
    ),
    (
        "Dagger",
        "dagger",
        "Programmable CI/CD engine that runs pipelines in containers.",
        "Dagger is a programmable CI/CD engine that runs your pipelines in standard containers. "
        "Write CI in Go, Python, TypeScript, or any language. Test locally, "
        "run anywhere. No more YAML — just regular code with caching built in.",
        "https://dagger.io",
        "developer-tools",
        "ci-cd,continuous-integration,containers,programmable,developer-tools",
        "GitHub Actions,Jenkins,CircleCI",
    ),

    # ── Feature Flags (developer-tools) ───────────────────────────────────
    (
        "Unleash",
        "unleash",
        "Open-source feature flag management for enterprise.",
        "Unleash is an open-source feature management platform with enterprise-grade capabilities. "
        "Gradual rollouts, A/B testing, kill switches, and user segmentation. "
        "SDKs for 15+ languages. Self-host or use the managed service.",
        "https://getunleash.io",
        "developer-tools",
        "feature-flags,open-source,gradual-rollout,self-hosted,enterprise",
        "LaunchDarkly,Split",
    ),
    (
        "OpenFeature",
        "openfeature",
        "Open standard for feature flag management. Vendor-neutral.",
        "OpenFeature is an open specification for feature flagging that provides a vendor-agnostic, "
        "community-driven API. SDKs for multiple languages with a provider model "
        "that lets you swap backends without code changes. CNCF sandbox project.",
        "https://openfeature.dev",
        "developer-tools",
        "feature-flags,open-standard,vendor-neutral,cncf,specification",
        "LaunchDarkly",
    ),

    # ── SMS (customer-support) ────────────────────────────────────────────
    (
        "Fonoster",
        "fonoster",
        "Open-source programmable telecom. Twilio alternative.",
        "Fonoster is an open-source alternative to Twilio for programmable telecommunications. "
        "Voice, SMS, and video APIs built on open standards (SIP, WebRTC). "
        "Self-host your telecom stack with full control over your communications.",
        "https://fonoster.com",
        "customer-support",
        "sms,voice,open-source,telecom,self-hosted",
        "Twilio,Vonage",
    ),

    # ── Status Page (monitoring-uptime) ───────────────────────────────────
    (
        "Cachet",
        "cachet",
        "Open-source status page system. Beautiful and functional.",
        "Cachet is a beautiful, open-source status page system. Display real-time component "
        "status, report incidents, and track metrics. API-driven for automation. "
        "Self-host with Docker or traditional PHP hosting.",
        "https://cachethq.io",
        "monitoring-uptime",
        "status-page,open-source,self-hosted,incidents,monitoring",
        "Statuspage by Atlassian,PagerDuty",
    ),
    (
        "Instatus",
        "instatus",
        "Fast, beautiful status page with unlimited subscribers.",
        "Instatus is a modern status page service that loads 10x faster than competitors. "
        "Unlimited team members and subscribers on all plans. Integrations with 50+ monitoring "
        "tools, Slack, Discord, and more. Free tier available.",
        "https://instatus.com",
        "monitoring-uptime",
        "status-page,fast,monitoring,uptime,integrations",
        "Statuspage by Atlassian",
    ),
    (
        "Cstate",
        "cstate",
        "Static status page generated with Hugo. Super fast and free.",
        "Cstate is a status page system that generates a fast, static site using Hugo. "
        "Host for free on GitHub Pages, Netlify, or any static hosting. "
        "Markdown-based incident management with RSS feed and Netlify CMS support.",
        "https://cstate.netlify.app",
        "monitoring-uptime",
        "status-page,static-site,open-source,free,hugo",
        "Statuspage by Atlassian,Betteruptime",
    ),

    # ── Blog / CMS (landing-pages) ────────────────────────────────────────
    (
        "Ghost",
        "ghost",
        "Professional publishing platform. Open-source Node.js CMS.",
        "Ghost is a powerful, open-source publishing platform for professional bloggers "
        "and content creators. Built-in memberships, newsletters, and paid subscriptions. "
        "Beautiful editor, SEO tools, and a fast, modern theme system.",
        "https://ghost.org",
        "landing-pages",
        "blog,cms,open-source,publishing,newsletter",
        "WordPress,Substack,Medium",
    ),
    (
        "Strapi",
        "strapi",
        "Open-source headless CMS. Node.js, fully customizable.",
        "Strapi is the leading open-source headless CMS built with Node.js. "
        "Create and manage content with a customizable admin panel, then deliver it "
        "anywhere via REST or GraphQL APIs. Plugins, webhooks, and role-based access.",
        "https://strapi.io",
        "landing-pages",
        "cms,headless,open-source,nodejs,api-first",
        "Contentful,Sanity",
    ),
    (
        "Directus",
        "directus",
        "Open-source data platform. Instant REST and GraphQL APIs.",
        "Directus wraps any SQL database with instant REST and GraphQL APIs plus an intuitive "
        "no-code app for managing content. Not just a CMS — it's a complete data platform. "
        "Self-host or use Directus Cloud. Supports Postgres, MySQL, SQLite, and more.",
        "https://directus.io",
        "landing-pages",
        "cms,headless,open-source,api,no-code",
        "Contentful,Sanity,Airtable",
    ),
    (
        "Keystatic",
        "keystatic",
        "Content management for your codebase. Git-based CMS.",
        "Keystatic is a content management tool that works directly with your Git repository. "
        "Edit content through a polished UI while files are saved as Markdown, JSON, or YAML "
        "in your repo. Works with Astro, Next.js, and Remix. No database needed.",
        "https://keystatic.com",
        "landing-pages",
        "cms,git-based,open-source,markdown,static-site",
        "Contentful,Forestry",
    ),
    (
        "Payload CMS",
        "payload-cms",
        "Code-first headless CMS and app framework. TypeScript-native.",
        "Payload is a headless CMS and application framework built with TypeScript. "
        "Define your schema in code, get instant APIs, admin UI, and authentication. "
        "Self-hosted, fully open-source, with no vendor lock-in.",
        "https://payloadcms.com",
        "landing-pages",
        "cms,headless,open-source,typescript,self-hosted",
        "Contentful,Strapi",
    ),
    (
        "Tina CMS",
        "tina-cms",
        "Git-backed CMS with visual editing. Built for Next.js.",
        "Tina CMS provides visual editing for content stored in your Git repository. "
        "Edit Markdown and MDX files with a live preview. Built-in GraphQL data layer "
        "and seamless integration with Next.js. Open source.",
        "https://tina.io",
        "landing-pages",
        "cms,git-based,visual-editing,open-source,nextjs",
        "Contentful,Forestry,Sanity",
    ),
    (
        "Hugo",
        "hugo",
        "Fastest static site generator. Written in Go.",
        "Hugo is the world's fastest framework for building static websites. "
        "Generates a complete site in milliseconds. Markdown content, flexible templating, "
        "built-in i18n, menus, and image processing. 300+ themes available.",
        "https://gohugo.io",
        "landing-pages",
        "static-site,blog,open-source,go,fast",
        "WordPress,Jekyll,Gatsby",
    ),
    (
        "Eleventy",
        "eleventy",
        "Simpler static site generator. Zero-config, flexible templates.",
        "Eleventy (11ty) is a simpler static site generator. Works with multiple template "
        "languages (Markdown, Nunjucks, Liquid, and more) and requires zero client-side JavaScript. "
        "Fast builds, simple config, and full control over your output.",
        "https://11ty.dev",
        "landing-pages",
        "static-site,blog,open-source,javascript,zero-config",
        "Gatsby,Next.js,Jekyll",
    ),

    # ══════════════════════════════════════════════════════════════════════
    # Additional useful tools
    # ══════════════════════════════════════════════════════════════════════

    # ── PDF (developer-tools) ─────────────────────────────────────────────
    (
        "Stirling PDF",
        "stirling-pdf",
        "Self-hosted PDF manipulation tool. All-in-one PDF toolkit.",
        "Stirling PDF is a self-hosted web-based PDF manipulation tool. Merge, split, "
        "convert, compress, rotate, add watermarks, and OCR PDF files. "
        "Docker-ready with a clean UI. No data leaves your server.",
        "https://stirlingtools.com",
        "developer-tools",
        "pdf,self-hosted,open-source,docker,document-processing",
        "Adobe Acrobat,SmallPDF",
    ),
    (
        "Gotenberg",
        "gotenberg",
        "Docker-powered stateless API for PDF generation.",
        "Gotenberg is a Docker-powered stateless API for converting HTML, Markdown, "
        "Word, and Excel documents to PDF. Uses Chromium and LibreOffice under the hood. "
        "Perfect for generating invoices, reports, and documents programmatically.",
        "https://gotenberg.dev",
        "developer-tools",
        "pdf,api,docker,open-source,document-generation",
        "Adobe Acrobat,Prince XML",
    ),

    # ── Video (design-creative) ───────────────────────────────────────────
    (
        "PeerTube",
        "peertube",
        "Decentralized video hosting. YouTube alternative. Open source.",
        "PeerTube is a free, decentralized video hosting platform. Federated via ActivityPub, "
        "P2P streaming with WebTorrent, live streaming, and playlists. "
        "Host your own instance or join an existing one. No ads, no tracking.",
        "https://joinpeertube.org",
        "design-creative",
        "video,decentralized,open-source,fediverse,self-hosted",
        "YouTube,Vimeo",
    ),
    (
        "OBS Studio",
        "obs-studio",
        "Free, open-source video recording and live streaming.",
        "OBS Studio is free, open-source software for video recording and live streaming. "
        "Real-time video/audio capturing, scene composition, encoding, recording, and broadcasting. "
        "Used by millions of streamers. Cross-platform with a powerful plugin ecosystem.",
        "https://obsproject.com",
        "design-creative",
        "video,streaming,open-source,recording,broadcast",
        "Streamlabs,XSplit,Wirecast",
    ),

    # ── Maps (developer-tools) ────────────────────────────────────────────
    (
        "MapLibre",
        "maplibre",
        "Open-source map rendering library. Mapbox GL JS fork.",
        "MapLibre GL JS is a free, open-source map rendering library forked from Mapbox GL JS. "
        "Vector tile rendering with WebGL for smooth, interactive maps. "
        "No API key required. Community-maintained with SDKs for web, iOS, and Android.",
        "https://maplibre.org",
        "developer-tools",
        "maps,geospatial,open-source,webgl,vector-tiles",
        "Mapbox,Google Maps",
    ),

    # ── Documentation (developer-tools) ───────────────────────────────────
    (
        "Mintlify",
        "mintlify",
        "Beautiful documentation that converts. AI-powered.",
        "Mintlify creates beautiful, performant documentation sites. AI-powered search, "
        "auto-generated API references, built-in analytics, and user feedback widgets. "
        "Write in MDX, deploy instantly. Used by Anthropic, Cursor, and Resend.",
        "https://mintlify.com",
        "developer-tools",
        "documentation,docs,ai-search,api-docs,developer-tools",
        "ReadMe,GitBook,Docusaurus",
    ),
    (
        "GitBook",
        "gitbook",
        "Modern documentation platform for technical teams.",
        "GitBook is a documentation platform for creating, organizing, and sharing knowledge. "
        "WYSIWYG and Markdown editor, Git sync, versioning, and search. "
        "Internal wikis, API docs, and user guides. Free for open-source projects.",
        "https://gitbook.com",
        "developer-tools",
        "documentation,docs,knowledge-base,git-sync,technical-writing",
        "Confluence,Notion,ReadMe",
    ),
]


def main():
    print(f"Seeding Round 2 tools at: {DB_PATH}")

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
            else:
                skipped += 1
                print(f"  ~ {name} already exists, skipped")
        except Exception as e:
            print(f"  ERROR inserting '{name}': {e}")
            skipped += 1

    conn.commit()

    # ── Rebuild FTS index ──────────────────────────────────────────────────
    print("  Rebuilding FTS index...")
    conn.execute("INSERT INTO tools_fts(tools_fts) VALUES('rebuild')")
    conn.commit()
    print("  FTS rebuild complete.")

    # ── Category count summary ─────────────────────────────────────────────
    print("\n── Category counts ──")
    for row in conn.execute(
        """SELECT c.slug, count(t.id)
           FROM categories c
           LEFT JOIN tools t ON t.category_id = c.id AND t.status = 'approved'
           GROUP BY c.id
           ORDER BY count(t.id) DESC"""
    ).fetchall():
        print(f"  {row[0]}: {row[1]}")

    # ── Summary ────────────────────────────────────────────────────────────
    total = conn.execute("SELECT count(*) FROM tools WHERE status = 'approved'").fetchone()[0]
    print(f"\nDone. {inserted} tools added, {skipped} skipped.")
    print(f"Total approved tools: {total}")

    conn.close()


if __name__ == "__main__":
    main()

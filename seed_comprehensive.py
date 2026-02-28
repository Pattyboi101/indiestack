#!/usr/bin/env python3
"""Seed IndieStack with ~80 real indie/open-source SaaS tools.

Fills thin categories to 10+ tools each. Every tool is a real,
existing project with correct URLs and accurate descriptions.

Usage:
    python3 seed_comprehensive.py

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
    # ── Forms & Surveys (+6) ──────────────────────────────────────────────
    (
        "Typebot",
        "typebot",
        "Open-source conversational form builder. Typeform alternative.",
        "Typebot lets you build advanced chatbots and conversational forms "
        "with a visual drag-and-drop builder. Embed anywhere as a popup, bubble, "
        "or full-page chat. Self-host or use the managed cloud.",
        "https://typebot.io",
        "forms-surveys",
        "forms,chatbot,open-source,self-hosted,conversational,typeform-alternative",
        "Typeform,Landbot",
    ),
    (
        "Heyform",
        "heyform",
        "Open-source form builder with beautiful UI.",
        "Heyform is an open-source form builder that makes creating engaging "
        "forms simple and intuitive. Features a clean drag-and-drop editor, "
        "conditional logic, and multiple input types. Self-hostable.",
        "https://heyform.net",
        "forms-surveys",
        "forms,open-source,self-hosted,drag-and-drop,no-code",
        "Typeform,Google Forms",
    ),
    (
        "OhMyForm",
        "ohmyform",
        "Open-source Typeform alternative. Self-hosted forms.",
        "OhMyForm is a free, open-source form builder that lets you create "
        "stunning forms without coding. Supports file uploads, logic jumps, "
        "and analytics. Self-host for complete data ownership.",
        "https://ohmyform.com",
        "forms-surveys",
        "forms,open-source,self-hosted,typeform-alternative,free",
        "Typeform,Google Forms",
    ),
    (
        "SurveyJS",
        "surveyjs",
        "Open-source JavaScript survey and form library.",
        "SurveyJS is a free, open-source JS library for building surveys and forms. "
        "Runs entirely client-side with a visual form designer, 20+ question types, "
        "conditional logic, and full customization via CSS and JSON schemas.",
        "https://surveyjs.io",
        "forms-surveys",
        "forms,surveys,javascript,open-source,library,developer-tools",
        "Typeform,SurveyMonkey",
    ),
    (
        "Fillout",
        "fillout",
        "Powerful form builder with integrations and free tier.",
        "Fillout is a modern form builder with native integrations to Airtable, "
        "Notion, Google Sheets, and more. Features calculation fields, payment "
        "collection, scheduling, and a generous free plan with unlimited forms.",
        "https://fillout.com",
        "forms-surveys",
        "forms,integrations,no-code,free-tier,airtable",
        "Typeform,JotForm",
    ),
    (
        "OpnForm",
        "opnform",
        "Open-source form builder. Beautiful Typeform alternative.",
        "OpnForm is an open-source form builder that creates beautiful, "
        "conversion-focused forms in minutes. Features conditional logic, "
        "file uploads, and webhooks. Self-host or use the free cloud version.",
        "https://opnform.com",
        "forms-surveys",
        "forms,open-source,self-hosted,typeform-alternative,free",
        "Typeform,Google Forms",
    ),

    # ── File Management (+6) ─────────────────────────────────────────────
    (
        "Filestash",
        "filestash",
        "Web-based file manager for S3, FTP, SFTP, and more.",
        "Filestash is a self-hosted web file manager that connects to your "
        "existing storage backends — S3, FTP, SFTP, Dropbox, Google Drive, "
        "and more. Features a beautiful UI with image viewer, video player, "
        "and text editor built in.",
        "https://filestash.app",
        "file-management",
        "file-manager,s3,ftp,self-hosted,open-source,web-based",
        "Dropbox,Cyberduck",
    ),
    (
        "SeaweedFS",
        "seaweedfs",
        "Fast distributed file system and object storage.",
        "SeaweedFS is a simple and highly scalable distributed file system "
        "optimized for billions of small files. S3-compatible API, FUSE mount, "
        "Hadoop support, and built-in replication. Much faster than HDFS for small files.",
        "https://seaweedfs.github.io",
        "file-management",
        "distributed-storage,object-storage,s3,open-source,self-hosted",
        "AWS S3,GlusterFS",
    ),
    (
        "Rook",
        "rook",
        "Production storage orchestration for Kubernetes via Ceph.",
        "Rook turns distributed storage systems into self-managing, self-scaling "
        "services on Kubernetes. Provides Ceph storage — block, file, and object — "
        "with automated deployment, scaling, and self-healing.",
        "https://rook.io",
        "file-management",
        "kubernetes,storage,ceph,open-source,cloud-native,orchestration",
        "AWS EBS,Azure Disk",
    ),
    (
        "Paperless-ngx",
        "paperless-ngx",
        "Document management with OCR. Open source.",
        "Paperless-ngx is a community-maintained document management system "
        "that transforms your physical documents into a searchable online archive. "
        "Automatic OCR, tagging, and full-text search. Self-hosted.",
        "https://docs.paperless-ngx.com",
        "file-management",
        "document-management,ocr,open-source,self-hosted,archiving",
        "Google Drive,Evernote",
    ),
    (
        "ownCloud",
        "owncloud",
        "Self-hosted file sync and share platform.",
        "ownCloud is an open-source file sync, share, and content collaboration "
        "platform. Desktop and mobile clients, end-to-end encryption, and "
        "extensive app marketplace. Trusted by 200M+ users worldwide.",
        "https://owncloud.com",
        "file-management",
        "file-sync,self-hosted,open-source,collaboration,encryption",
        "Dropbox,Google Drive,OneDrive",
    ),
    (
        "Seafile",
        "seafile",
        "High-performance open-source file sync and share.",
        "Seafile is an open-source cloud storage system with high reliability "
        "and performance. Features file syncing, sharing, built-in file encryption, "
        "and online collaboration. Known for its speed and low resource usage.",
        "https://seafile.com",
        "file-management",
        "file-sync,self-hosted,open-source,encryption,collaboration",
        "Dropbox,Google Drive",
    ),

    # ── Project Management (+5) ──────────────────────────────────────────
    (
        "Taiga",
        "taiga",
        "Open-source agile project management platform.",
        "Taiga is a free, open-source project management tool for agile teams. "
        "Supports Scrum and Kanban with backlogs, sprints, user stories, tasks, "
        "and issues. Beautiful UI with real-time updates and integrations.",
        "https://taiga.io",
        "project-management",
        "project-management,agile,scrum,kanban,open-source,self-hosted",
        "Jira,Trello,Asana",
    ),
    (
        "OpenProject",
        "openproject",
        "Open-source project management with Gantt charts.",
        "OpenProject is the leading open-source project management software. "
        "Gantt charts, agile boards, time tracking, cost reporting, and team "
        "collaboration. Self-hosted with on-premise and cloud options.",
        "https://openproject.org",
        "project-management",
        "project-management,gantt,open-source,self-hosted,time-tracking",
        "Jira,Microsoft Project,Smartsheet",
    ),
    (
        "Leantime",
        "leantime",
        "Open-source project management for non-project-managers.",
        "Leantime is an open-source project management system designed for "
        "innovators and non-project-managers. Strategy, planning, and execution "
        "in one tool with a focus on simplicity and lean methodology.",
        "https://leantime.io",
        "project-management",
        "project-management,open-source,self-hosted,lean,strategy",
        "Asana,Monday.com",
    ),
    (
        "Vikunja",
        "vikunja",
        "Open-source to-do app and task manager.",
        "Vikunja is an open-source, self-hosted to-do list and task manager. "
        "Lists, kanban boards, Gantt charts, and CalDAV support. Lightweight, "
        "fast, and available as a single binary. API-first design.",
        "https://vikunja.io",
        "project-management",
        "task-manager,todo,open-source,self-hosted,kanban,caldav",
        "Todoist,TickTick",
    ),
    (
        "Kanboard",
        "kanboard",
        "Minimalistic Kanban board. Open source.",
        "Kanboard is a free, open-source Kanban project management software "
        "focused on minimalism and simplicity. Drag-and-drop tasks, subtasks, "
        "swimlanes, time tracking, and plugins. Lightweight PHP application.",
        "https://kanboard.org",
        "project-management",
        "kanban,open-source,self-hosted,minimalist,php",
        "Trello",
    ),

    # ── Scheduling & Booking (+5) ────────────────────────────────────────
    (
        "Rallly",
        "rallly",
        "Open-source Doodle alternative for scheduling meetings.",
        "Rallly is a free, open-source scheduling tool for finding the best "
        "time for group meetings. Create polls, share with participants, "
        "and find overlapping availability. No account required to vote.",
        "https://rallly.co",
        "scheduling-booking",
        "scheduling,polls,open-source,self-hosted,doodle-alternative",
        "Doodle,When2meet",
    ),
    (
        "Zcal",
        "zcal",
        "Free scheduling tool with team features.",
        "Zcal is a 100% free scheduling tool that eliminates the back-and-forth "
        "of booking meetings. Supports one-on-one and group scheduling, team "
        "pages, and calendar integrations. No paid tiers — completely free.",
        "https://zcal.co",
        "scheduling-booking",
        "scheduling,free,team-scheduling,calendar,meetings",
        "Calendly",
    ),
    (
        "TidyCal",
        "tidycal",
        "Simple scheduling tool. One-time payment by AppSumo.",
        "TidyCal is a no-fuss scheduling tool that covers the essentials. "
        "Booking pages, calendar sync, payment collection, and custom branding. "
        "One-time purchase with no monthly fees — built by AppSumo.",
        "https://tidycal.com",
        "scheduling-booking",
        "scheduling,booking,one-time-payment,affordable,calendar",
        "Calendly,Acuity",
    ),
    (
        "SavvyCal",
        "savvycal",
        "Scheduling tool that overlays your calendar.",
        "SavvyCal is a scheduling tool that lets invitees overlay their own "
        "calendar on top of your availability. Prioritized slots, round-robin "
        "routing, and team scheduling. Less back-and-forth, more context.",
        "https://savvycal.com",
        "scheduling-booking",
        "scheduling,calendar,team-scheduling,booking,overlay",
        "Calendly",
    ),
    (
        "Appointlet",
        "appointlet",
        "Online scheduling for teams.",
        "Appointlet is an online scheduling platform that helps teams book "
        "meetings faster. Embeddable booking pages, automated reminders, "
        "Stripe payments, and integrations with Zoom, Teams, and Google Meet.",
        "https://appointlet.com",
        "scheduling-booking",
        "scheduling,booking,team-scheduling,payments,embeddable",
        "Calendly,Acuity",
    ),

    # ── Customer Support (+4) ────────────────────────────────────────────
    (
        "Crisp",
        "crisp",
        "All-in-one business messaging platform.",
        "Crisp is an all-in-one business messaging platform that centralizes "
        "live chat, email, Messenger, Twitter DMs, and SMS in one inbox. "
        "Includes a knowledge base, chatbot builder, and CRM. Free tier for small teams.",
        "https://crisp.chat",
        "customer-support",
        "live-chat,messaging,chatbot,knowledge-base,crm,free-tier",
        "Intercom,Zendesk",
    ),
    (
        "Tawk.to",
        "tawk-to",
        "100% free live chat software.",
        "Tawk.to is a completely free live chat application for websites. "
        "Real-time visitor monitoring, ticketing system, knowledge base, "
        "and CRM features — all with no limits and no hidden costs. "
        "Used by millions of businesses worldwide.",
        "https://tawk.to",
        "customer-support",
        "live-chat,free,visitor-monitoring,ticketing,knowledge-base",
        "Intercom,Zendesk,LiveChat",
    ),
    (
        "Helpy",
        "helpy",
        "Open-source helpdesk. Self-hosted customer support.",
        "Helpy is an open-source helpdesk and customer support platform. "
        "Ticket management, knowledge base, and community forums in one "
        "self-hosted package. Built with Ruby on Rails. GDPR-compliant.",
        "https://helpy.io",
        "customer-support",
        "helpdesk,open-source,self-hosted,ticketing,knowledge-base",
        "Zendesk,Freshdesk",
    ),
    (
        "Zammad",
        "zammad",
        "Open-source web-based ticketing system.",
        "Zammad is a web-based, open-source helpdesk and ticketing system. "
        "Email, phone, chat, and social media channels in one interface. "
        "Full-text search, knowledge base, and powerful automation rules.",
        "https://zammad.com",
        "customer-support",
        "ticketing,helpdesk,open-source,self-hosted,multi-channel",
        "Zendesk,Freshdesk",
    ),

    # ── Social Media (+4) ────────────────────────────────────────────────
    (
        "Misskey",
        "misskey",
        "Decentralized social platform on the fediverse. Open source.",
        "Misskey is a decentralized, open-source social media platform that's "
        "part of the fediverse via ActivityPub. Features reactions, custom emoji, "
        "drive storage, antennas, and a powerful theming system.",
        "https://misskey-hub.net",
        "social-media",
        "social-network,decentralized,open-source,fediverse,activitypub",
        "Twitter,Mastodon",
    ),
    (
        "Postiz",
        "postiz",
        "Open-source social media scheduling tool.",
        "Postiz is an open-source social media scheduling and management tool. "
        "Schedule posts across multiple platforms, collaborate with your team, "
        "and track engagement. Self-hostable alternative to Buffer and Hootsuite.",
        "https://postiz.com",
        "social-media",
        "social-media,scheduling,open-source,self-hosted,multi-platform",
        "Buffer,Hootsuite",
    ),
    (
        "Mixpost",
        "mixpost",
        "Self-hosted social media management.",
        "Mixpost is a self-hosted social media management platform. Schedule "
        "and publish content to multiple social accounts, manage your content "
        "calendar, and analyze post performance. Built with Laravel.",
        "https://mixpost.app",
        "social-media",
        "social-media,scheduling,self-hosted,open-source,content-calendar",
        "Buffer,Hootsuite,Later",
    ),
    (
        "Plume",
        "plume",
        "Federated blogging engine with ActivityPub.",
        "Plume is a federated blogging platform built on ActivityPub. Write "
        "articles that can be followed and shared across the fediverse. "
        "Supports multiple authors, rich text, and themes. Open source.",
        "https://joinplu.me",
        "social-media",
        "blogging,fediverse,activitypub,open-source,federated,self-hosted",
        "Medium,WordPress",
    ),

    # ── Payments (+4) ────────────────────────────────────────────────────
    (
        "BTCPay Server",
        "btcpay-server",
        "Self-hosted Bitcoin payment processor.",
        "BTCPay Server is a free, open-source, self-hosted Bitcoin and "
        "Lightning payment processor. No fees, no third-party, full control. "
        "E-commerce integrations with WooCommerce, Shopify, and more.",
        "https://btcpayserver.org",
        "payments",
        "bitcoin,payments,open-source,self-hosted,lightning,crypto",
        "PayPal,Stripe",
    ),
    (
        "Kill Bill",
        "kill-bill",
        "Open-source subscription billing platform.",
        "Kill Bill is an open-source subscription billing and payments platform. "
        "Handles recurring billing, invoicing, tax, payments, and entitlements "
        "for SaaS and subscription businesses. Battle-tested at scale.",
        "https://killbill.io",
        "payments",
        "billing,subscriptions,open-source,recurring-payments,invoicing",
        "Stripe Billing,Chargebee,Recurly",
    ),
    (
        "Hyperswitch",
        "hyperswitch",
        "Open-source payments switch for multiple processors.",
        "Hyperswitch is an open-source payments switch that lets you connect "
        "to multiple payment processors through a single API. Smart routing, "
        "retry logic, and unified analytics across Stripe, Adyen, and 50+ processors.",
        "https://hyperswitch.io",
        "payments",
        "payments,open-source,payment-routing,multi-processor,fintech",
        "Stripe,Adyen",
    ),
    (
        "Polar",
        "polar",
        "Open-source funding platform for developers.",
        "Polar is a platform for open-source developers to get funded. "
        "Offer subscriptions, issue funding, and digital products to your "
        "community. Built-in Stripe integration and GitHub app for seamless setup.",
        "https://polar.sh",
        "payments",
        "funding,open-source,developer-tools,subscriptions,github",
        "GitHub Sponsors,Open Collective",
    ),

    # ── SEO Tools (+4) ───────────────────────────────────────────────────
    (
        "SearXNG",
        "searxng",
        "Privacy-respecting metasearch engine. Self-hosted.",
        "SearXNG is a free, open-source metasearch engine that aggregates "
        "results from 70+ search engines without tracking users. Self-host "
        "your own instance for private, unbiased web search results.",
        "https://searxng.org",
        "seo-tools",
        "search-engine,privacy,open-source,self-hosted,metasearch",
        "Google,DuckDuckGo",
    ),
    (
        "Serpbear",
        "serpbear",
        "Open-source search engine position tracking.",
        "Serpbear is an open-source SEO tool for tracking your website's "
        "keyword positions in Google search results. Email notifications, "
        "SERP API integration, and a clean dashboard. Self-hosted and free.",
        "https://serpbear.com",
        "seo-tools",
        "seo,rank-tracking,open-source,self-hosted,keywords",
        "Ahrefs,SEMrush",
    ),
    (
        "PostHog",
        "posthog",
        "Open-source product analytics suite.",
        "PostHog is an open-source product analytics platform with session "
        "replays, feature flags, A/B testing, and user surveys. All-in-one "
        "product toolkit you can self-host. Generous free tier on the cloud.",
        "https://posthog.com",
        "seo-tools",
        "analytics,product-analytics,open-source,self-hosted,feature-flags,ab-testing",
        "Mixpanel,Amplitude,Hotjar",
    ),
    (
        "Countly",
        "countly",
        "Privacy-focused open-source product analytics.",
        "Countly is an open-source product analytics platform focused on "
        "privacy and data ownership. Mobile, web, and desktop analytics "
        "with crash reporting, push notifications, and user profiles.",
        "https://count.ly",
        "seo-tools",
        "analytics,privacy,open-source,mobile-analytics,product-analytics",
        "Mixpanel,Firebase Analytics",
    ),

    # ── API Tools (+4) ───────────────────────────────────────────────────
    (
        "Bruno",
        "bruno",
        "Open-source API client. Stores collections in Git.",
        "Bruno is an open-source IDE for exploring and testing APIs. "
        "Collections are stored directly in your filesystem using a plain "
        "text markup language (Bru). Git-friendly, offline-first, and fast.",
        "https://usebruno.com",
        "api-tools",
        "api,testing,open-source,git-friendly,offline,developer-tools",
        "Postman,Insomnia",
    ),
    (
        "Swagger UI",
        "swagger-ui",
        "Open-source interactive API documentation.",
        "Swagger UI is the industry-standard tool for rendering OpenAPI "
        "specifications as interactive API documentation. Try out API calls "
        "directly from the browser. Part of the Swagger/OpenAPI ecosystem.",
        "https://swagger.io",
        "api-tools",
        "api,documentation,open-source,openapi,swagger,developer-tools",
        "Redocly,ReadMe",
    ),
    (
        "Stoplight",
        "stoplight",
        "API design-first platform with visual editor.",
        "Stoplight is an API design platform for building high-quality APIs. "
        "Visual OpenAPI editor, mock servers, style guides, and hosted docs. "
        "Design-first workflow that keeps APIs consistent and well-documented.",
        "https://stoplight.io",
        "api-tools",
        "api,design,documentation,openapi,mock-server",
        "Postman,SwaggerHub",
    ),
    (
        "Kreya",
        "kreya",
        "gRPC and REST API client for developers.",
        "Kreya is a GUI client for gRPC, REST, and WebSocket APIs. "
        "Built specifically for developers who work with gRPC. Environment "
        "variables, scripting, and authentication out of the box. Free to use.",
        "https://kreya.app",
        "api-tools",
        "api,grpc,rest,developer-tools,free,testing",
        "Postman,BloomRPC",
    ),

    # ── AI & Automation (+4) ─────────────────────────────────────────────
    (
        "n8n",
        "n8n",
        "Open-source workflow automation. Zapier alternative.",
        "n8n is a fair-code workflow automation platform with 400+ integrations. "
        "Visual workflow builder, custom code nodes, and self-hosting option. "
        "Build complex automations without vendor lock-in.",
        "https://n8n.io",
        "ai-automation",
        "automation,workflow,open-source,self-hosted,zapier-alternative,integrations",
        "Zapier,Make",
    ),
    (
        "Activepieces",
        "activepieces",
        "Open-source business automation. Zapier alternative.",
        "Activepieces is an open-source, no-code business automation tool. "
        "Build flows with 100+ integrations using a visual builder. "
        "Self-host or use the cloud. Type-safe pieces framework for developers.",
        "https://activepieces.com",
        "ai-automation",
        "automation,no-code,open-source,self-hosted,zapier-alternative",
        "Zapier,Make",
    ),
    (
        "Windmill",
        "windmill",
        "Open-source developer platform for scripts and workflows.",
        "Windmill is an open-source platform for building internal tools, "
        "workflows, and scripts. Write in Python, TypeScript, Go, or SQL "
        "with automatic UI generation. Self-host or use the cloud.",
        "https://windmill.dev",
        "ai-automation",
        "automation,workflows,scripts,open-source,self-hosted,internal-tools",
        "Retool,Airplane",
    ),
    (
        "Huginn",
        "huginn",
        "Build agents that automate tasks online. Open source.",
        "Huginn is a system for building agents that perform automated tasks "
        "online — monitor websites, receive webhooks, and react to events. "
        "Think of it as a self-hosted IFTTT/Zapier with full control.",
        "https://github.com/huginn/huginn",
        "ai-automation",
        "automation,agents,open-source,self-hosted,monitoring,webhooks",
        "IFTTT,Zapier",
    ),

    # ── Feedback & Reviews (+4) ──────────────────────────────────────────
    (
        "Testimonial.to",
        "testimonial-to",
        "Collect and display video and text testimonials.",
        "Testimonial.to makes it easy to collect video and text testimonials "
        "from your customers. Embed a beautiful Wall of Love on your site "
        "with no coding. Social proof that converts visitors into customers.",
        "https://testimonial.to",
        "feedback-reviews",
        "testimonials,social-proof,video,reviews,embeddable",
        "TrustPilot,G2",
    ),
    (
        "Senja",
        "senja",
        "Collect, manage, and share testimonials everywhere.",
        "Senja is a testimonial management platform. Collect testimonials "
        "via custom forms, import from 30+ sources, and share them as "
        "beautiful widgets, images, or walls of love. Free tier available.",
        "https://senja.io",
        "feedback-reviews",
        "testimonials,social-proof,reviews,widgets,free-tier",
        "TrustPilot,Testimonial.to",
    ),
    (
        "Upvoty",
        "upvoty",
        "User feedback and feature request boards.",
        "Upvoty is a feedback management tool that lets users submit and "
        "upvote feature requests. Public roadmaps, changelogs, and SSO. "
        "Helps you build what your users actually want.",
        "https://upvoty.com",
        "feedback-reviews",
        "feedback,feature-requests,roadmap,changelog,user-feedback",
        "Canny,ProductBoard",
    ),
    (
        "Sleekplan",
        "sleekplan",
        "All-in-one feedback tool with changelog and roadmap.",
        "Sleekplan combines feedback collection, roadmaps, and changelogs "
        "in one widget you embed in your app. Users vote on features, "
        "you update the roadmap, and announce changes — all in one place.",
        "https://sleekplan.com",
        "feedback-reviews",
        "feedback,changelog,roadmap,widget,user-feedback,embeddable",
        "Canny,Beamer",
    ),

    # ── CRM & Sales (+3) ────────────────────────────────────────────────
    (
        "SuiteCRM",
        "suitecrm",
        "Open-source CRM. Enterprise-ready Salesforce alternative.",
        "SuiteCRM is the world's leading open-source CRM with over 4 million "
        "users. Sales automation, marketing campaigns, customer support, "
        "reporting, and workflow management. Free and self-hosted.",
        "https://suitecrm.com",
        "crm-sales",
        "crm,open-source,self-hosted,sales,marketing,enterprise",
        "Salesforce,HubSpot",
    ),
    (
        "Monica",
        "monica",
        "Open-source personal CRM for relationships.",
        "Monica is an open-source personal relationship management tool. "
        "Track conversations, remember birthdays, manage debts, and keep "
        "notes about the people you care about. Self-host or use the cloud.",
        "https://monicahq.com",
        "crm-sales",
        "crm,personal,open-source,self-hosted,relationships",
        "Google Contacts",
    ),
    (
        "Krayin",
        "krayin",
        "Open-source Laravel CRM for SMBs.",
        "Krayin is a free, open-source CRM built on Laravel. Lead management, "
        "email integration, activity tracking, and workflow automation. "
        "Designed for small and medium businesses with a clean, modern UI.",
        "https://krayincrm.com",
        "crm-sales",
        "crm,laravel,open-source,self-hosted,lead-management",
        "Salesforce,Pipedrive",
    ),

    # ── Authentication (+3) ──────────────────────────────────────────────
    (
        "Zitadel",
        "zitadel",
        "Open-source identity management and auth.",
        "Zitadel is an open-source identity management platform combining "
        "authentication and authorization. SSO, MFA, OIDC, SAML, and "
        "passwordless login out of the box. Self-host or use the cloud.",
        "https://zitadel.com",
        "authentication",
        "auth,identity,open-source,sso,oidc,saml,self-hosted",
        "Auth0,Okta",
    ),
    (
        "SuperTokens",
        "supertokens",
        "Open-source authentication. Self-hosted auth solution.",
        "SuperTokens is an open-source authentication solution with pre-built "
        "UI components. Email/password, social login, session management, "
        "and MFA. Self-host the core for free or use the managed service.",
        "https://supertokens.com",
        "authentication",
        "auth,open-source,self-hosted,session-management,social-login",
        "Auth0,Firebase Auth",
    ),
    (
        "Ory",
        "ory",
        "Open-source identity and access management.",
        "Ory provides open-source identity infrastructure — authentication, "
        "authorization, and user management. Ory Kratos (identity), Ory Hydra "
        "(OAuth2), Ory Keto (permissions), and Ory Oathkeeper (API gateway).",
        "https://ory.sh",
        "authentication",
        "auth,identity,open-source,oauth2,self-hosted,permissions",
        "Auth0,Okta,Keycloak",
    ),

    # ── Design & Creative (+3) ──────────────────────────────────────────
    (
        "Blender",
        "blender",
        "Open-source 3D creation suite.",
        "Blender is a free, open-source 3D creation suite supporting the "
        "entire pipeline — modeling, rigging, animation, simulation, rendering, "
        "compositing, and video editing. Industry standard for indie creators.",
        "https://blender.org",
        "design-creative",
        "3d,animation,open-source,modeling,rendering,video-editing",
        "Maya,Cinema 4D,3ds Max",
    ),
    (
        "Lunacy",
        "lunacy",
        "Free design tool with built-in assets by Icons8.",
        "Lunacy is a free design tool by Icons8 with built-in assets — icons, "
        "photos, and illustrations. Sketch-compatible, works offline, and "
        "runs natively on Windows, macOS, and Linux. No subscription needed.",
        "https://icons8.com/lunacy",
        "design-creative",
        "design,free,icons,illustrations,sketch-compatible,cross-platform",
        "Figma,Sketch",
    ),
    (
        "Polotno",
        "polotno",
        "SDK for building design editors like Canva.",
        "Polotno is a JavaScript SDK for building graphic design editors "
        "into your own application. Canvas-based with text, images, shapes, "
        "and templates. Think of it as Canva-as-a-library for developers.",
        "https://polotno.com",
        "design-creative",
        "design,sdk,javascript,canvas,editor,developer-tools",
        "Canva",
    ),

    # ── Invoicing & Billing (+2) ─────────────────────────────────────────
    (
        "Lago",
        "lago",
        "Open-source metering and usage-based billing.",
        "Lago is an open-source billing platform for usage-based pricing. "
        "Real-time event ingestion, metering, invoicing, and payment collection. "
        "Build complex pricing models without vendor lock-in.",
        "https://getlago.com",
        "invoicing-billing",
        "billing,usage-based,metering,open-source,self-hosted,invoicing",
        "Stripe Billing,Chargebee",
    ),
    (
        "Crater",
        "crater",
        "Open-source invoicing app for freelancers.",
        "Crater is a free, open-source invoicing application built for "
        "freelancers and small businesses. Create invoices, track expenses, "
        "accept payments, and generate reports. Self-hosted Laravel app.",
        "https://craterapp.com",
        "invoicing-billing",
        "invoicing,open-source,self-hosted,freelancers,expenses,laravel",
        "FreshBooks,Wave",
    ),

    # ── Email Marketing (+2) ────────────────────────────────────────────
    (
        "Listmonk",
        "listmonk",
        "Open-source self-hosted newsletter and mailing list manager.",
        "Listmonk is a high-performance, self-hosted newsletter and mailing "
        "list manager. Single binary, PostgreSQL-backed, with templating, "
        "analytics, and subscriber management. Handles millions of subscribers.",
        "https://listmonk.app",
        "email-marketing",
        "email,newsletter,open-source,self-hosted,mailing-list",
        "Mailchimp,ConvertKit",
    ),
    (
        "Mautic",
        "mautic",
        "Open-source marketing automation platform.",
        "Mautic is the world's largest open-source marketing automation "
        "platform. Email campaigns, landing pages, lead scoring, contact "
        "segmentation, and social media monitoring. Self-hosted and free.",
        "https://mautic.org",
        "email-marketing",
        "marketing-automation,email,open-source,self-hosted,lead-scoring",
        "HubSpot,Marketo,ActiveCampaign",
    ),

    # ── Analytics & Metrics (+2) ─────────────────────────────────────────
    (
        "Pirsch",
        "pirsch",
        "Privacy-friendly web analytics. No cookies.",
        "Pirsch is a privacy-friendly, cookie-free web analytics platform. "
        "Simple dashboard, real-time data, and full GDPR compliance without "
        "consent banners. Lightweight script that won't slow down your site.",
        "https://pirsch.io",
        "analytics-metrics",
        "analytics,privacy,no-cookies,gdpr,lightweight,web-analytics",
        "Google Analytics",
    ),
    (
        "Aptabase",
        "aptabase",
        "Open-source analytics for mobile and desktop apps.",
        "Aptabase is an open-source, privacy-first analytics platform built "
        "for mobile and desktop applications. SDKs for Swift, Kotlin, Flutter, "
        "React Native, Electron, and more. No personal data collected.",
        "https://aptabase.com",
        "analytics-metrics",
        "analytics,mobile,desktop,open-source,privacy,sdk",
        "Firebase Analytics,Mixpanel",
    ),

    # ── Landing Pages (+2) ───────────────────────────────────────────────
    (
        "Astro",
        "astro",
        "Web framework for content-driven websites.",
        "Astro is a modern web framework for building fast, content-driven "
        "websites. Ships zero JavaScript by default, supports React, Vue, "
        "Svelte, and more. Perfect for landing pages, blogs, and docs sites.",
        "https://astro.build",
        "landing-pages",
        "web-framework,static-site,javascript,content,performance,open-source",
        "Next.js,Gatsby",
    ),
    (
        "Docusaurus",
        "docusaurus",
        "Build documentation sites with React. Open source by Meta.",
        "Docusaurus is a static site generator optimized for documentation "
        "websites. Built with React, supports versioning, i18n, search, and "
        "MDX. Used by hundreds of open-source projects. Made by Meta.",
        "https://docusaurus.io",
        "landing-pages",
        "documentation,static-site,react,open-source,mdx,meta",
        "GitBook,ReadMe",
    ),

    # ── Monitoring & Uptime (+2) ─────────────────────────────────────────
    (
        "Gatus",
        "gatus",
        "Open-source automated service health dashboard.",
        "Gatus is an open-source automated service health dashboard. Define "
        "health checks in YAML, monitor HTTP, TCP, DNS, ICMP, and more. "
        "Alerts via Slack, PagerDuty, email, and others. Single Go binary.",
        "https://gatus.io",
        "monitoring-uptime",
        "monitoring,health-checks,open-source,self-hosted,alerting,dashboard",
        "Datadog,PagerDuty",
    ),
    (
        "Upptime",
        "upptime",
        "Open-source uptime monitor powered by GitHub Actions.",
        "Upptime is an open-source uptime monitor and status page powered "
        "entirely by GitHub. Uses GitHub Actions for monitoring, GitHub Issues "
        "for incidents, and GitHub Pages for the status page. No server needed.",
        "https://upptime.js.org",
        "monitoring-uptime",
        "uptime,monitoring,open-source,github,status-page,free",
        "Statuspage,BetterUptime",
    ),

    # ── Developer Tools (+2) ─────────────────────────────────────────────
    (
        "Gitea",
        "gitea",
        "Self-hosted Git service. Lightweight and fast.",
        "Gitea is a painless, self-hosted Git service written in Go. "
        "Code hosting, code review, CI/CD, packages, and project management. "
        "Lightweight enough to run on a Raspberry Pi. GitHub-like experience.",
        "https://gitea.com",
        "developer-tools",
        "git,self-hosted,open-source,code-hosting,ci-cd,lightweight",
        "GitHub,GitLab",
    ),
    (
        "Dokploy",
        "dokploy",
        "Open-source deployment platform. Self-hosted PaaS.",
        "Dokploy is a free, open-source deployment platform for applications "
        "and databases. Docker and Buildpack support, automatic SSL, "
        "real-time monitoring, and database backups. Self-hosted Heroku alternative.",
        "https://dokploy.com",
        "developer-tools",
        "deployment,paas,open-source,self-hosted,docker,heroku-alternative",
        "Heroku,Railway,Render",
    ),

    # ── AI Dev Tools (+2) ────────────────────────────────────────────────
    (
        "Jan",
        "jan",
        "Open-source ChatGPT alternative that runs locally.",
        "Jan is an open-source desktop application for running large language "
        "models locally. Supports GGUF models, extensions, and a ChatGPT-like "
        "interface. Completely offline, private, and free. Cross-platform.",
        "https://jan.ai",
        "ai-dev-tools",
        "llm,local,open-source,desktop,chatgpt-alternative,privacy",
        "ChatGPT,Ollama",
    ),
    (
        "LM Studio",
        "lm-studio",
        "Run LLMs locally with a beautiful desktop UI.",
        "LM Studio is a desktop application for discovering, downloading, and "
        "running local LLMs. Beautiful chat interface, OpenAI-compatible API "
        "server, and model management. Runs on Mac, Windows, and Linux.",
        "https://lmstudio.ai",
        "ai-dev-tools",
        "llm,local,desktop,openai-compatible,model-management",
        "ChatGPT,Ollama",
    ),
]


def main():
    print(f"Seeding comprehensive tools at: {DB_PATH}")

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

    # Per-category breakdown
    print("\n  Category counts:")
    for row in conn.execute(
        """SELECT c.slug, COUNT(t.id) FROM categories c
           LEFT JOIN tools t ON t.category_id = c.id AND t.status = 'approved'
           GROUP BY c.id ORDER BY COUNT(t.id)"""
    ).fetchall():
        print(f"    {row[1]:>3}  {row[0]}")

    print(f"\nDone. {inserted} tools added, {skipped} skipped.")
    print(f"Total approved tools: {total}")

    conn.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Add high-priority missing tools to the IndieStack catalog.

Usage (on production via flyctl ssh console or local DB):
  python3 /app/scripts/add_missing_tools.py

Each tool is skipped if its slug already exists. Safe to re-run.
Run FTS rebuild after: INSERT INTO tools_fts(tools_fts) VALUES('rebuild');
"""

import os
import sqlite3

db_path = "/data/indiestack.db" if os.path.exists("/data/indiestack.db") else "data/indiestack.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row


def get_category_id(slug: str) -> int | None:
    row = conn.execute("SELECT id FROM categories WHERE slug = ?", (slug,)).fetchone()
    return row["id"] if row else None


TOOLS = [
    # ── Frontend Frameworks ───────────────────────────────────────────
    {
        "name": "React",
        "slug": "react",
        "tagline": "The library for web and native user interfaces",
        "description": "React is a JavaScript library for building user interfaces. Maintained by Meta, it powers millions of web and native apps with a component-based model and virtual DOM.",
        "url": "https://react.dev",
        "github_url": "https://github.com/facebook/react",
        "github_stars": 230000,
        "category_slug": "frontend-frameworks",
        "tags": "react,ui,javascript,components,frontend",
        "source_type": "code",
    },
    {
        "name": "Vue.js",
        "slug": "vuejs",
        "tagline": "The Progressive JavaScript Framework",
        "description": "Vue.js is an approachable, performant, and versatile framework for building web user interfaces. Known for its gentle learning curve and excellent documentation.",
        "url": "https://vuejs.org",
        "github_url": "https://github.com/vuejs/vue",
        "github_stars": 208000,
        "category_slug": "frontend-frameworks",
        "tags": "vue,javascript,ui,frontend,progressive",
        "source_type": "code",
    },
    {
        "name": "Svelte",
        "slug": "svelte",
        "tagline": "Cybernetically enhanced web apps",
        "description": "Svelte is a radical new approach to building user interfaces. It compiles components to highly optimised vanilla JavaScript at build time — no virtual DOM overhead.",
        "url": "https://svelte.dev",
        "github_url": "https://github.com/sveltejs/svelte",
        "github_stars": 80000,
        "category_slug": "frontend-frameworks",
        "tags": "svelte,javascript,compiler,frontend,ui",
        "source_type": "code",
    },
    {
        "name": "Angular",
        "slug": "angular",
        "tagline": "The web development framework for building the future",
        "description": "Angular is a TypeScript-based open-source web framework led by the Angular Team at Google. It provides a complete solution with routing, forms, HTTP, and more built in.",
        "url": "https://angular.dev",
        "github_url": "https://github.com/angular/angular",
        "github_stars": 96000,
        "category_slug": "frontend-frameworks",
        "tags": "angular,typescript,frontend,google,spa",
        "source_type": "code",
    },
    {
        "name": "Zustand",
        "slug": "zustand",
        "tagline": "Bear necessities for state management in React",
        "description": "A small, fast, and scalable bearbones state management solution for React. Zustand uses simplified flux principles with hooks — no boilerplate, no providers.",
        "url": "https://zustand-demo.pmnd.rs",
        "github_url": "https://github.com/pmndrs/zustand",
        "github_stars": 48000,
        "category_slug": "frontend-frameworks",
        "tags": "state-management,react,hooks,frontend,zustand",
        "source_type": "code",
    },
    {
        "name": "Jotai",
        "slug": "jotai",
        "tagline": "Primitive and flexible state management for React",
        "description": "Jotai takes an atomic approach to global React state management. Build state by combining atoms and renders are automatically optimized based on atom dependency.",
        "url": "https://jotai.org",
        "github_url": "https://github.com/pmndrs/jotai",
        "github_stars": 19000,
        "category_slug": "frontend-frameworks",
        "tags": "state-management,react,atoms,frontend,jotai",
        "source_type": "code",
    },
    {
        "name": "Webpack",
        "slug": "webpack",
        "tagline": "A static module bundler for modern JavaScript",
        "description": "Webpack is a module bundler for JavaScript. It bundles assets and source code into output files ready for deployment, with a rich plugin ecosystem.",
        "url": "https://webpack.js.org",
        "github_url": "https://github.com/webpack/webpack",
        "github_stars": 64000,
        "category_slug": "frontend-frameworks",
        "tags": "bundler,build-tool,javascript,webpack,frontend",
        "source_type": "code",
    },
    {
        "name": "esbuild",
        "slug": "esbuild",
        "tagline": "An extremely fast JavaScript bundler",
        "description": "esbuild is a JavaScript bundler written in Go. It is 10-100x faster than other bundlers and supports TypeScript, JSX, tree-shaking, and minification out of the box.",
        "url": "https://esbuild.github.io",
        "github_url": "https://github.com/evanw/esbuild",
        "github_stars": 38000,
        "category_slug": "frontend-frameworks",
        "tags": "bundler,build-tool,fast,go,javascript,esbuild",
        "source_type": "code",
    },
    # ── Caching ───────────────────────────────────────────────────────
    {
        "name": "Upstash",
        "slug": "upstash",
        "tagline": "Serverless Redis and Kafka for modern apps",
        "description": "Upstash offers serverless Redis and Kafka with per-request pricing. No idle cost, REST API, global replication, and works seamlessly with Vercel, Netlify, and edge runtimes.",
        "url": "https://upstash.com",
        "github_url": "https://github.com/upstash/upstash-redis",
        "github_stars": 3000,
        "category_slug": "caching",
        "tags": "redis,serverless,caching,kafka,edge",
        "source_type": "saas",
    },
    # ── Email ─────────────────────────────────────────────────────────
    {
        "name": "Resend",
        "slug": "resend",
        "tagline": "Email for developers",
        "description": "Resend is the email API built for developers. Send transactional emails with React components, get great deliverability, and monitor with a beautiful dashboard.",
        "url": "https://resend.com",
        "github_url": "https://github.com/resendlabs/resend-node",
        "github_stars": 8000,
        "category_slug": "email-marketing",
        "tags": "email,transactional,react,developer,smtp",
        "source_type": "saas",
    },
    # ── Frontend Frameworks (additional) ─────────────────────────────
    {
        "name": "Vite",
        "slug": "vite",
        "tagline": "Next generation frontend tooling",
        "description": "Vite is a modern build tool offering instant server start and lightning-fast HMR. It uses native ES modules in dev and Rollup for production builds. The de-facto standard for modern frontend projects.",
        "url": "https://vitejs.dev",
        "github_url": "https://github.com/vitejs/vite",
        "github_stars": 68000,
        "category_slug": "frontend-frameworks",
        "tags": "bundler,build-tool,hmr,fast,javascript,esm",
        "source_type": "code",
    },
    {
        "name": "SvelteKit",
        "slug": "sveltekit",
        "tagline": "The fastest way to build Svelte apps",
        "description": "SvelteKit is the official Svelte application framework. It handles routing, server-side rendering, static generation, and API routes — everything you need to ship full-stack Svelte apps.",
        "url": "https://kit.svelte.dev",
        "github_url": "https://github.com/sveltejs/kit",
        "github_stars": 19000,
        "category_slug": "frontend-frameworks",
        "tags": "svelte,ssr,ssg,fullstack,routing,frontend",
        "source_type": "code",
    },
    {
        "name": "TanStack Query",
        "slug": "tanstack-query",
        "tagline": "Powerful asynchronous state management for TypeScript",
        "description": "TanStack Query (formerly React Query) is the async state management library for TypeScript. Handles fetching, caching, background updates, and stale-while-revalidate out of the box.",
        "url": "https://tanstack.com/query",
        "github_url": "https://github.com/TanStack/query",
        "github_stars": 43000,
        "category_slug": "frontend-frameworks",
        "tags": "react,data-fetching,caching,state-management,typescript,tanstack",
        "source_type": "code",
    },
    {
        "name": "Radix UI",
        "slug": "radix-ui",
        "tagline": "Unstyled, accessible components for building high-quality design systems",
        "description": "Radix UI provides low-level, accessible React primitives. Unstyled by design — bring your own styles or use with Tailwind CSS. The foundation behind shadcn/ui and many design systems.",
        "url": "https://www.radix-ui.com",
        "github_url": "https://github.com/radix-ui/primitives",
        "github_stars": 16000,
        "category_slug": "frontend-frameworks",
        "tags": "react,components,accessibility,unstyled,design-system,ui",
        "source_type": "code",
    },
    # ── Animation Libraries ───────────────────────────────────────────
    {
        "name": "Framer Motion",
        "slug": "framer-motion",
        "tagline": "Production-ready animation library for React",
        "description": "Framer Motion is an open-source React animation library. Declarative animations, gestures, layout transitions, and scroll-driven effects with a clean API. Powers animations on thousands of production sites.",
        "url": "https://www.framer.com/motion",
        "github_url": "https://github.com/framer/motion",
        "github_stars": 24000,
        "category_slug": "frontend-frameworks",
        "tags": "animation,react,motion,gestures,transitions,frontend",
        "source_type": "code",
    },
    {
        "name": "GSAP",
        "slug": "gsap",
        "tagline": "Professional-grade JavaScript animation for the modern web",
        "description": "GSAP (GreenSock Animation Platform) is the industry-standard JavaScript animation library. Framework-agnostic, performant, and battle-tested across millions of websites.",
        "url": "https://gsap.com",
        "github_url": "https://github.com/greensock/GSAP",
        "github_stars": 20000,
        "category_slug": "frontend-frameworks",
        "tags": "animation,javascript,gsap,motion,svg,frontend",
        "source_type": "code",
    },
    # ── Icon Libraries ────────────────────────────────────────────────
    {
        "name": "Lucide Icons",
        "slug": "lucide-icons",
        "tagline": "Beautiful and consistent open-source icons",
        "description": "Lucide is a community fork of Feather Icons. Over 1,000 clean, consistent SVG icons available as React, Vue, Svelte components and plain SVG. Used by shadcn/ui and thousands of projects.",
        "url": "https://lucide.dev",
        "github_url": "https://github.com/lucide-icons/lucide",
        "github_stars": 12000,
        "category_slug": "frontend-frameworks",
        "tags": "icons,svg,react,components,design-system,frontend",
        "source_type": "code",
    },
    {
        "name": "Heroicons",
        "slug": "heroicons",
        "tagline": "Beautiful hand-crafted SVG icons by the makers of Tailwind CSS",
        "description": "Heroicons is a set of 292 free MIT-licensed icons in outline, solid, and micro styles. Available as React and Vue components, or plain SVGs. Made by the Tailwind CSS team.",
        "url": "https://heroicons.com",
        "github_url": "https://github.com/tailwindlabs/heroicons",
        "github_stars": 21000,
        "category_slug": "frontend-frameworks",
        "tags": "icons,svg,tailwind,react,components,frontend",
        "source_type": "code",
    },
    # ── Internationalisation ──────────────────────────────────────────
    {
        "name": "next-intl",
        "slug": "next-intl",
        "tagline": "Internationalization for Next.js",
        "description": "next-intl is the go-to i18n library for Next.js App Router. Supports translations, date/number formatting, plurals, and time zones with full TypeScript support.",
        "url": "https://next-intl-docs.vercel.app",
        "github_url": "https://github.com/amannn/next-intl",
        "github_stars": 8000,
        "category_slug": "localization",
        "tags": "i18n,localization,nextjs,internationalization,typescript",
        "source_type": "code",
    },
    {
        "name": "i18next",
        "slug": "i18next",
        "tagline": "The internationalization framework for JavaScript",
        "description": "i18next is the most popular i18n framework for JavaScript. Works with React (react-i18next), Vue, Angular, Node.js, and more. Supports namespaces, interpolation, plurals, and context.",
        "url": "https://www.i18next.com",
        "github_url": "https://github.com/i18next/i18next",
        "github_stars": 7800,
        "category_slug": "localization",
        "tags": "i18n,localization,javascript,internationalization,translations",
        "source_type": "code",
    },
    # ── Workflow Automation ───────────────────────────────────────────
    {
        "name": "n8n",
        "slug": "n8n",
        "tagline": "Workflow automation for technical teams",
        "description": "n8n is a self-hostable workflow automation tool. Connect 400+ services, build custom nodes in JavaScript/TypeScript, and run automations on your own infrastructure. Open-source with a fair-code licence.",
        "url": "https://n8n.io",
        "github_url": "https://github.com/n8n-io/n8n",
        "github_stars": 50000,
        "category_slug": "ai-automation",
        "tags": "workflow,automation,no-code,self-hosted,integrations,zapier-alternative",
        "source_type": "code",
    },
    # ── ORMs & Validation ────────────────────────────────────────────
    {
        "name": "Prisma",
        "slug": "prisma",
        "tagline": "Next-generation Node.js and TypeScript ORM",
        "description": "Prisma is an open-source database toolkit for Node.js and TypeScript. Includes an intuitive data model, automated migrations, type-safe queries, and a visual database browser.",
        "url": "https://www.prisma.io",
        "github_url": "https://github.com/prisma/prisma",
        "github_stars": 40000,
        "category_slug": "database",
        "tags": "orm,typescript,nodejs,migrations,database,postgres,mysql,sqlite",
        "source_type": "code",
    },
    {
        "name": "Drizzle ORM",
        "slug": "drizzle-orm",
        "tagline": "TypeScript ORM that feels like writing SQL",
        "description": "Drizzle ORM is a lightweight TypeScript ORM with a SQL-like API. Zero dependencies, full type inference, support for PostgreSQL, MySQL, and SQLite. The fastest-growing ORM in the Node.js ecosystem.",
        "url": "https://orm.drizzle.team",
        "github_url": "https://github.com/drizzle-team/drizzle-orm",
        "github_stars": 27000,
        "category_slug": "database",
        "tags": "orm,typescript,nodejs,migrations,database,postgres,sqlite,mysql",
        "source_type": "code",
    },
    {
        "name": "Zod",
        "slug": "zod",
        "tagline": "TypeScript-first schema validation with static type inference",
        "description": "Zod is a TypeScript-first schema declaration and validation library. Define schemas once, get static types and runtime validation for free. Works everywhere TypeScript runs — server, browser, React Native.",
        "url": "https://zod.dev",
        "github_url": "https://github.com/colinhacks/zod",
        "github_stars": 34000,
        "category_slug": "developer-tools",
        "tags": "validation,typescript,schema,parsing,runtime,zod",
        "source_type": "code",
    },
    {
        "name": "tRPC",
        "slug": "trpc",
        "tagline": "End-to-end typesafe APIs made easy",
        "description": "tRPC lets you build and consume fully typesafe APIs without schemas or code generation. Write your backend once in TypeScript, call it from your frontend with full autocompletion and compile-time safety.",
        "url": "https://trpc.io",
        "github_url": "https://github.com/trpc/trpc",
        "github_stars": 36000,
        "category_slug": "api-tools",
        "tags": "typescript,api,rpc,nextjs,react,fullstack,type-safe",
        "source_type": "code",
    },
    # ── Runtimes ─────────────────────────────────────────────────────
    {
        "name": "Bun",
        "slug": "bun",
        "tagline": "Incredibly fast JavaScript runtime, bundler, and package manager",
        "description": "Bun is an all-in-one JavaScript runtime built for speed. It includes a bundler, test runner, and Node.js-compatible package manager. Up to 4x faster than Node.js for common workloads.",
        "url": "https://bun.sh",
        "github_url": "https://github.com/oven-sh/bun",
        "github_stars": 74000,
        "category_slug": "frontend-frameworks",
        "tags": "runtime,bundler,javascript,typescript,fast,nodejs-alternative",
        "source_type": "code",
    },
    # ── API Frameworks ───────────────────────────────────────────────
    {
        "name": "Hono",
        "slug": "hono",
        "tagline": "Fast, lightweight web framework for the edge",
        "description": "Hono is a small, simple, and ultrafast web framework for Cloudflare Workers, Deno, Bun, and Node.js. It has no dependencies and provides routing, middleware, and RPC in under 14kB.",
        "url": "https://hono.dev",
        "github_url": "https://github.com/honojs/hono",
        "github_stars": 20000,
        "category_slug": "api-tools",
        "tags": "web-framework,edge,cloudflare,deno,bun,typescript,nodejs,serverless",
        "source_type": "code",
    },
    # ── Headless CMS ─────────────────────────────────────────────────
    {
        "name": "Payload CMS",
        "slug": "payload-cms",
        "tagline": "The most powerful TypeScript-native headless CMS",
        "description": "Payload is a headless CMS and application framework built with TypeScript, Node.js, and React. Define your schema in code, get a full admin UI and REST/GraphQL APIs generated automatically. Self-host or deploy to any Node.js environment.",
        "url": "https://payloadcms.com",
        "github_url": "https://github.com/payloadcms/payload",
        "github_stars": 32000,
        "category_slug": "headless-cms",
        "tags": "cms,typescript,nodejs,rest,graphql,self-hosted,headless",
        "source_type": "code",
    },
    # ── Frontend Frameworks (meta-frameworks) ────────────────────────
    {
        "name": "Astro",
        "slug": "astro",
        "tagline": "The web framework for content-driven websites",
        "description": "Astro is a web framework for building content-driven sites. Ship zero JavaScript by default, render components from any framework (React, Vue, Svelte), and use Islands architecture for interactive components only.",
        "url": "https://astro.build",
        "github_url": "https://github.com/withastro/astro",
        "github_stars": 46000,
        "category_slug": "frontend-frameworks",
        "tags": "static-site,ssr,islands,javascript,typescript,react,vue,svelte",
        "source_type": "code",
    },
    {
        "name": "Nuxt",
        "slug": "nuxt",
        "tagline": "The Intuitive Vue Framework",
        "description": "Nuxt is the open-source framework that makes web development intuitive and powerful. It builds on top of Vue.js with SSR, SSG, and full-stack capabilities via Nitro server engine.",
        "url": "https://nuxt.com",
        "github_url": "https://github.com/nuxt/nuxt",
        "github_stars": 55000,
        "category_slug": "frontend-frameworks",
        "tags": "vue,ssr,ssg,fullstack,typescript,frontend",
        "source_type": "code",
    },
    # ── Authentication ────────────────────────────────────────────────
    {
        "name": "Lucia",
        "slug": "lucia",
        "tagline": "Auth, but simple",
        "description": "Lucia is a lightweight, framework-agnostic authentication library for TypeScript. Handles sessions, OAuth, and database adapters — gives you full control without the magic. Works with Next.js, SvelteKit, Astro, and more.",
        "url": "https://lucia-auth.com",
        "github_url": "https://github.com/lucia-auth/lucia",
        "github_stars": 7000,
        "category_slug": "authentication",
        "tags": "auth,sessions,oauth,typescript,self-hosted,sveltekit,nextjs",
        "source_type": "code",
    },
    # ── Background Jobs ───────────────────────────────────────────────
    {
        "name": "Temporal",
        "slug": "temporalio",
        "tagline": "Durable execution for workflows and long-running processes",
        "description": "Temporal is an open-source durable execution platform. Write workflows as regular code — Temporal handles retries, timeouts, and state persistence automatically. Ideal for complex multi-step processes, saga patterns, and background jobs.",
        "url": "https://temporal.io",
        "github_url": "https://github.com/temporalio/temporal",
        "github_stars": 12000,
        "category_slug": "background-jobs",
        "tags": "workflow,durable-execution,saga,background-jobs,orchestration,typescript,go",
        "source_type": "code",
    },
    # ── Maps & Location ───────────────────────────────────────────────
    {
        "name": "Leaflet",
        "slug": "leaflet",
        "tagline": "An open-source JavaScript library for mobile-friendly interactive maps",
        "description": "Leaflet is the leading open-source JavaScript library for interactive maps. Lightweight (42kB gzipped), mobile-friendly, and extensible via a rich plugin ecosystem. Used by GitHub, Flickr, Pinterest, and thousands of apps.",
        "url": "https://leafletjs.com",
        "github_url": "https://github.com/Leaflet/Leaflet",
        "github_stars": 41000,
        "category_slug": "maps-location",
        "tags": "maps,leaflet,geospatial,javascript,open-source",
        "source_type": "code",
    },
    # ── API Tools ─────────────────────────────────────────────────────
    {
        "name": "Bruno",
        "slug": "bruno",
        "tagline": "Opensource IDE for exploring and testing APIs",
        "description": "Bruno is an offline-first, open-source API client that stores collections directly in your filesystem using a plain text markup language (Bru). No cloud sync, no accounts — just fast, Git-friendly API testing.",
        "url": "https://www.usebruno.com",
        "github_url": "https://github.com/usebruno/bruno",
        "github_stars": 28000,
        "category_slug": "api-tools",
        "tags": "api,testing,rest,graphql,offline,open-source,postman-alternative",
        "source_type": "code",
    },
    {
        "name": "Insomnia",
        "slug": "insomnia",
        "tagline": "The open-source API development platform",
        "description": "Insomnia is an open-source API client for REST, GraphQL, gRPC, WebSocket, and SOAP requests. Supports environment variables, request chaining, authentication helpers, and local Git sync. Maintained by Kong.",
        "url": "https://insomnia.rest",
        "github_url": "https://github.com/Kong/insomnia",
        "github_stars": 34000,
        "category_slug": "api-tools",
        "tags": "api,testing,rest,graphql,grpc,client,postman-alternative",
        "source_type": "code",
    },
    # ── Database ──────────────────────────────────────────────────────
    {
        "name": "Atlas",
        "slug": "atlas",
        "tagline": "Database schema-as-code migrations",
        "description": "Atlas is a modern database schema management tool. Define your schema in HCL or SQL, and Atlas generates migration scripts, validates them, and runs them safely in CI/CD. Supports PostgreSQL, MySQL, SQLite, and more.",
        "url": "https://atlasgo.io",
        "github_url": "https://github.com/ariga/atlas",
        "github_stars": 6000,
        "category_slug": "database",
        "tags": "migrations,schema,database,postgres,mysql,sqlite,devops",
        "source_type": "code",
    },
    {
        "name": "React Router",
        "slug": "react-router",
        "tagline": "Declarative routing for React",
        "description": "React Router is the most popular routing library for React applications. v7 adds full-stack capabilities (formerly Remix), with file-based routing, server rendering, and data loading built in. Used in millions of React projects.",
        "url": "https://reactrouter.com",
        "github_url": "https://github.com/remix-run/react-router",
        "github_stars": 52000,
        "category_slug": "frontend-frameworks",
        "tags": "react,routing,spa,frontend,remix,typescript",
        "source_type": "code",
    },
    # ── AI & Automation ───────────────────────────────────────────────
    {
        "name": "Tesseract.js",
        "slug": "tesseract-js",
        "tagline": "Pure JavaScript OCR for 100+ languages",
        "description": "Tesseract.js is a pure JavaScript OCR engine that recognises text in images in 100+ languages. Runs entirely in the browser or Node.js via WebAssembly — no server-side dependencies required.",
        "url": "https://tesseract.projectnaptha.com",
        "github_url": "https://github.com/naptha/tesseract.js",
        "github_stars": 34000,
        "category_slug": "ai-automation",
        "tags": "ocr,javascript,wasm,browser,nodejs,ai,text-recognition",
        "source_type": "code",
    },
    # ── Background Jobs (additional) ─────────────────────────────────
    {
        "name": "BullMQ",
        "slug": "bullmq",
        "tagline": "Premium message queue and job scheduler for Node.js",
        "description": "BullMQ is a Node.js job and message queue based on Redis. Supports job retries, delayed jobs, rate limiting, and concurrency control. The go-to background jobs library for the Node.js ecosystem.",
        "url": "https://bullmq.io",
        "github_url": "https://github.com/taskforcesh/bullmq",
        "github_stars": 6000,
        "category_slug": "background-jobs",
        "tags": "queue,redis,nodejs,jobs,worker,typescript",
        "source_type": "code",
    },
    # ── Frontend Frameworks (UI component system) ─────────────────────
    {
        "name": "shadcn/ui",
        "slug": "shadcn-ui",
        "tagline": "Beautifully designed components built with Radix UI and Tailwind CSS",
        "description": "shadcn/ui is a collection of re-usable React components built on Radix UI and styled with Tailwind CSS. Not a library — you copy the components into your project and own the code. The most popular React UI system in 2025-2026.",
        "url": "https://ui.shadcn.com",
        "github_url": "https://github.com/shadcn-ui/ui",
        "github_stars": 80000,
        "category_slug": "frontend-frameworks",
        "tags": "react,ui,tailwindcss,radix,components,design-system,typescript",
        "source_type": "code",
    },
    # ── Authentication ─────────────────────────────────────────────────
    {
        "name": "Better Auth",
        "slug": "better-auth",
        "tagline": "The most comprehensive authentication library for TypeScript",
        "description": "Better Auth is a framework-agnostic authentication and authorization library for TypeScript. Supports email/password, social OAuth, passkeys, magic links, 2FA, and organizations out of the box. Designed for Next.js, SvelteKit, Astro, and other modern meta-frameworks.",
        "url": "https://www.better-auth.com",
        "github_url": "https://github.com/better-auth/better-auth",
        "github_stars": 10000,
        "category_slug": "authentication",
        "tags": "auth,typescript,oauth,passkeys,2fa,nextjs,sveltekit,sessions",
        "source_type": "code",
    },
    # ── AI & Automation ────────────────────────────────────────────────
    {
        "name": "Mastra",
        "slug": "mastra",
        "tagline": "The TypeScript AI agent framework",
        "description": "Mastra is an open-source TypeScript framework for building AI agents and workflows. Provides tools, memory, RAG pipelines, and integrations with 100+ services. Built by the team behind Gatsby.js. Designed for production AI applications.",
        "url": "https://mastra.ai",
        "github_url": "https://github.com/mastra-ai/mastra",
        "github_stars": 8000,
        "category_slug": "ai-automation",
        "tags": "ai,agent,typescript,rag,workflows,memory,tools,llm",
        "source_type": "code",
    },
    {
        "name": "Open WebUI",
        "slug": "open-webui",
        "tagline": "User-friendly, self-hosted AI interface for Ollama and OpenAI-compatible APIs",
        "description": "Open WebUI is a feature-rich, self-hosted web interface for running local LLMs via Ollama and OpenAI-compatible APIs. Supports multi-modal chat, RAG, tools, model management, user accounts, and custom system prompts. The most popular Ollama frontend with 80k+ GitHub stars.",
        "url": "https://openwebui.com",
        "github_url": "https://github.com/open-webui/open-webui",
        "github_stars": 80000,
        "category_slug": "ai-automation",
        "tags": "ollama,llm,chat,local-ai,self-hosted,rag,multimodal,openai",
        "source_type": "code",
    },
    # ── API Tools ─────────────────────────────────────────────────────
    {
        "name": "Encore",
        "slug": "encore",
        "tagline": "The backend development platform for cloud-native apps",
        "description": "Encore is a TypeScript and Go backend framework with built-in infrastructure. Define services, queues, caches, databases, and scheduled jobs directly in code — Encore provisions real cloud infra on AWS/GCP. Eliminates Terraform and deployment boilerplate for backend teams.",
        "url": "https://encore.dev",
        "github_url": "https://github.com/encoredev/encore",
        "github_stars": 8000,
        "category_slug": "api-tools",
        "tags": "backend,typescript,go,infrastructure,queues,caching,database,serverless",
        "source_type": "code",
    },
]


def main() -> None:
    inserted = 0
    skipped = 0
    no_cat = 0

    for tool in TOOLS:
        # Check if slug already exists
        existing = conn.execute(
            "SELECT id FROM tools WHERE slug = ?", (tool["slug"],)
        ).fetchone()
        if existing:
            print(f"  skip  {tool['slug']} (already exists)")
            skipped += 1
            continue

        # Resolve category
        cat_id = get_category_id(tool["category_slug"])
        if cat_id is None:
            print(f"  WARN  {tool['slug']} — category '{tool['category_slug']}' not found, skipping")
            no_cat += 1
            continue

        conn.execute(
            """INSERT INTO tools
               (name, slug, tagline, description, url, github_url, github_stars,
                category_id, tags, status, source_type)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', ?)""",
            (
                tool["name"],
                tool["slug"],
                tool["tagline"],
                tool["description"],
                tool["url"],
                tool["github_url"],
                tool.get("github_stars", 0),
                cat_id,
                tool.get("tags", ""),
                tool["source_type"],
            ),
        )
        print(f"  insert {tool['slug']} → {tool['category_slug']}")
        inserted += 1

    conn.commit()
    conn.close()

    print(f"\nDone. inserted={inserted} skipped={skipped} no_category={no_cat}")
    print("Next: rebuild FTS index on production —")
    print("  INSERT INTO tools_fts(tools_fts) VALUES('rebuild');")
    print("  PRAGMA wal_checkpoint(TRUNCATE);")


if __name__ == "__main__":
    main()

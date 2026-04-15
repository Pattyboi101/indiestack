"""
Add high-priority missing tools to the IndieStack catalog.

Safe to re-run — checks by slug before inserting.
Run on production: python3 /app/src/indiestack/scripts/add_missing_tools.py

DB_PATH defaults to /data/indiestack.db (Fly.io production path).
Override: DB_PATH=/path/to/local.db python3 add_missing_tools.py
"""

import asyncio
import os
import sqlite3

DB_PATH = os.environ.get("DB_PATH", "/data/indiestack.db")

# Each entry: (slug, name, tagline, description, category_slug, github_repo,
#              github_stars, website_url, tags, install_command, source_type)
TOOLS = [
    # Frontend Frameworks --------------------------------------------------------
    (
        "react",
        "React",
        "The library for web and native user interfaces",
        "React is a JavaScript library for building user interfaces. "
        "Maintained by Meta, it's the most widely-used frontend library, "
        "powering everything from simple SPAs to complex enterprise apps.",
        "frontend-frameworks",
        "facebook/react",
        230000,
        "https://react.dev",
        "frontend,javascript,ui,component-library",
        "npm install react react-dom",
        "code",
    ),
    (
        "vuejs",
        "Vue.js",
        "The Progressive JavaScript Framework",
        "Vue.js is an approachable, performant, and versatile framework for "
        "building web UIs. Version 3 brings the Composition API, better TypeScript "
        "support, and significantly improved performance.",
        "frontend-frameworks",
        "vuejs/vue",
        208000,
        "https://vuejs.org",
        "frontend,javascript,ui,progressive",
        "npm install vue",
        "code",
    ),
    (
        "svelte",
        "Svelte",
        "Cybernetically enhanced web apps",
        "Svelte compiles your components to highly efficient vanilla JavaScript. "
        "No virtual DOM, no runtime overhead — just fast, reactive web apps. "
        "Svelte 5 introduces runes for fine-grained reactivity.",
        "frontend-frameworks",
        "sveltejs/svelte",
        80000,
        "https://svelte.dev",
        "frontend,javascript,compiler,reactive",
        "npm create svelte@latest my-app",
        "code",
    ),
    (
        "angular",
        "Angular",
        "The web development framework for building the future",
        "Angular is a platform and framework for building single-page client "
        "applications in HTML and TypeScript. Maintained by Google, it includes "
        "a full suite of tools: router, forms, HTTP client, and dependency injection.",
        "frontend-frameworks",
        "angular/angular",
        96000,
        "https://angular.dev",
        "frontend,typescript,spa,google",
        "npm install @angular/core",
        "code",
    ),
    (
        "vite",
        "Vite",
        "Next Generation Frontend Tooling",
        "Vite is a blazing-fast build tool that leverages native ES modules in the "
        "browser during development, giving near-instant HMR. Production builds use "
        "Rollup. Powers SvelteKit, Astro, Remix, and more.",
        "frontend-frameworks",
        "vitejs/vite",
        68000,
        "https://vite.dev",
        "bundler,build-tool,hmr,fast",
        "npm install vite",
        "code",
    ),
    (
        "sveltekit",
        "SvelteKit",
        "Web development, streamlined",
        "SvelteKit is the official Svelte meta-framework for building full-stack web "
        "apps. File-based routing, SSR, SSG, and server actions out of the box. "
        "Deploys anywhere — Vercel, Cloudflare, Node, or static.",
        "frontend-frameworks",
        "sveltejs/kit",
        19000,
        "https://kit.svelte.dev",
        "svelte,fullstack,ssr,ssg",
        "npm create svelte@latest",
        "code",
    ),
    (
        "tanstack-query",
        "TanStack Query",
        "Powerful asynchronous state management for TS/JS",
        "TanStack Query (formerly React Query) handles server state for React, Vue, "
        "Solid, and Svelte apps. Automatic caching, background refetching, pagination, "
        "optimistic updates, and devtools included.",
        "frontend-frameworks",
        "TanStack/query",
        43000,
        "https://tanstack.com/query",
        "state-management,data-fetching,react,caching",
        "npm install @tanstack/react-query",
        "code",
    ),
    (
        "radix-ui",
        "Radix UI",
        "Unstyled, accessible components for React",
        "Radix UI provides low-level, unstyled, accessible UI primitives for React. "
        "No default styles — bring your own CSS or use with Tailwind. Foundation "
        "for shadcn/ui and many popular design systems.",
        "frontend-frameworks",
        "radix-ui/primitives",
        16000,
        "https://radix-ui.com",
        "ui,react,accessibility,headless",
        "npm install @radix-ui/react-dialog",
        "code",
    ),
    (
        "zustand",
        "Zustand",
        "Bear necessities for state management in React",
        "Zustand is a small, fast, and scalable state management solution for React. "
        "Uses simplified flux principles. No boilerplate, no providers, no context — "
        "just a hook. First-class TypeScript support.",
        "frontend-frameworks",
        "pmndrs/zustand",
        48000,
        "https://zustand-demo.pmnd.rs",
        "state-management,react,hooks",
        "npm install zustand",
        "code",
    ),
    (
        "jotai",
        "Jotai",
        "Primitive and flexible state management for React",
        "Jotai takes an atomic approach to global React state management. Build state "
        "by combining atoms, enabling fine-grained subscriptions and avoiding unnecessary "
        "re-renders. Inspired by Recoil with a simpler API.",
        "frontend-frameworks",
        "pmndrs/jotai",
        19000,
        "https://jotai.org",
        "state-management,react,atomic",
        "npm install jotai",
        "code",
    ),
    (
        "webpack",
        "webpack",
        "A static module bundler for modern JavaScript applications",
        "webpack is the battle-tested JavaScript module bundler. Handles JS, CSS, "
        "images, and more via loaders. Highly configurable with a rich plugin ecosystem. "
        "Powers create-react-app and many enterprise setups.",
        "frontend-frameworks",
        "webpack/webpack",
        64000,
        "https://webpack.js.org",
        "bundler,build-tool,javascript",
        "npm install webpack webpack-cli --save-dev",
        "code",
    ),
    (
        "esbuild",
        "esbuild",
        "An extremely fast JavaScript bundler",
        "esbuild is a JavaScript/TypeScript bundler and minifier written in Go. "
        "10–100× faster than other bundlers. Used internally by Vite for dependency "
        "pre-bundling. Excellent for libraries and tooling.",
        "frontend-frameworks",
        "evanw/esbuild",
        38000,
        "https://esbuild.github.io",
        "bundler,build-tool,fast,golang",
        "npm install esbuild",
        "code",
    ),
    (
        "framer-motion",
        "Framer Motion",
        "A production-ready motion library for React",
        "Framer Motion is an open-source animation library for React. Declarative "
        "animations, gestures, layout animations, and SVG morphing. Powers "
        "beautiful UIs in production apps worldwide.",
        "frontend-frameworks",
        "framer/motion",
        24000,
        "https://motion.dev",
        "animation,react,ui,gestures",
        "npm install framer-motion",
        "code",
    ),
    (
        "gsap",
        "GSAP",
        "Professional-grade JavaScript animation for the modern web",
        "GSAP (GreenSock Animation Platform) is the industry standard for web animations. "
        "Framework-agnostic, incredibly performant, and battle-tested in production. "
        "Powers animations on thousands of award-winning sites.",
        "frontend-frameworks",
        "greensock/GSAP",
        20000,
        "https://gsap.com",
        "animation,javascript,timeline,performance",
        "npm install gsap",
        "code",
    ),
    (
        "lucide-icons",
        "Lucide Icons",
        "Beautiful and consistent icons for web and mobile",
        "Lucide is a community-maintained fork of Feather Icons with 1,500+ icons. "
        "Available for React, Vue, Svelte, Angular, and vanilla JS. Clean, consistent, "
        "and easy to customise with CSS.",
        "frontend-frameworks",
        "lucide-icons/lucide",
        12000,
        "https://lucide.dev",
        "icons,react,svg,ui",
        "npm install lucide-react",
        "code",
    ),
    (
        "heroicons",
        "Heroicons",
        "Beautiful hand-crafted SVG icons, by the makers of Tailwind CSS",
        "Heroicons provides 292 free SVG icons in outline and solid styles, designed "
        "specifically to work with Tailwind CSS. Official React and Vue components "
        "included. Made by the Tailwind Labs team.",
        "frontend-frameworks",
        "tailwindlabs/heroicons",
        21000,
        "https://heroicons.com",
        "icons,tailwind,react,svg",
        "npm install @heroicons/react",
        "code",
    ),
    (
        "next-intl",
        "next-intl",
        "Internationalization for Next.js",
        "next-intl is the most popular i18n library for Next.js App Router. "
        "Type-safe translations, locale detection, RTL support, and seamless "
        "integration with Next.js routing and server components.",
        "localization",
        "amannn/next-intl",
        8000,
        "https://next-intl-docs.vercel.app",
        "i18n,nextjs,react,typescript",
        "npm install next-intl",
        "code",
    ),
    (
        "i18next",
        "i18next",
        "Internationalization framework for browser and Node.js",
        "i18next is the most widely used i18n framework for JavaScript. Framework-agnostic "
        "core with official plugins for React, Vue, Angular, and more. Supports "
        "pluralization, interpolation, and language detection.",
        "localization",
        "i18next/i18next",
        7800,
        "https://www.i18next.com",
        "i18n,javascript,react,translation",
        "npm install i18next react-i18next",
        "code",
    ),
    # Background Jobs / Queues ---------------------------------------------------
    (
        "bullmq",
        "BullMQ",
        "The fastest, most reliable, Redis-based queue for Node.js",
        "BullMQ is a modern, TypeScript-first queue library built on Redis. "
        "Supports job priorities, rate limiting, retries, delayed jobs, and "
        "parent/child job dependencies. Successor to Bull.",
        "background-jobs",
        "taskforcesh/bullmq",
        6000,
        "https://bullmq.io",
        "queue,redis,nodejs,typescript",
        "npm install bullmq",
        "code",
    ),
    # Caching --------------------------------------------------------------------
    (
        "upstash",
        "Upstash Redis",
        "Serverless Redis — per-request pricing, zero ops",
        "Upstash provides serverless Redis with per-request pricing. Zero connection "
        "management, global replication, and built-in REST API. Perfect for edge "
        "functions, Vercel, Cloudflare Workers, and Lambda.",
        "caching",
        "upstash/upstash-redis",
        3000,
        "https://upstash.com",
        "redis,serverless,caching,edge",
        "npm install @upstash/redis",
        "code",
    ),
    # Email ----------------------------------------------------------------------
    (
        "resend",
        "Resend",
        "Email for developers",
        "Resend is the email API built for developers. Simple REST API, React Email "
        "integration, domain verification, logs, and webhooks. Ships transactional "
        "emails reliably with minimal setup.",
        "email-marketing",
        "resendlabs/resend-node",
        8000,
        "https://resend.com",
        "email,transactional,react,api",
        "npm install resend",
        "code",
    ),
    # AI / LLM APIs --------------------------------------------------------------
    (
        "openrouter",
        "OpenRouter",
        "A unified interface for LLMs",
        "OpenRouter provides a single API for 200+ LLMs including GPT-4, Claude, "
        "Llama, Mistral, and Gemini. Automatic fallbacks, cost tracking, and "
        "OpenAI-compatible interface. Usage-based pricing.",
        "ai-dev-tools",
        "OpenRouterAI/openrouter-runner",
        5000,
        "https://openrouter.ai",
        "llm,api,openai-compatible,multi-model",
        "npm install openai",
        "saas",
    ),
    (
        "groq",
        "Groq",
        "AI inference at speed",
        "Groq provides ultra-fast LLM inference via their custom LPU hardware. "
        "OpenAI-compatible API with Llama 3, Mixtral, and Gemma models. "
        "Consistently the fastest inference provider for open-weight models.",
        "ai-dev-tools",
        "groq/groq-typescript",
        3000,
        "https://groq.com",
        "llm,api,fast,inference",
        "npm install groq-sdk",
        "saas",
    ),
    # Database / ORM -------------------------------------------------------------
    (
        "prisma",
        "Prisma",
        "Next-generation Node.js and TypeScript ORM",
        "Prisma is the most popular ORM for Node.js and TypeScript. Auto-generated "
        "type-safe client, intuitive schema language, database migrations, and "
        "Prisma Studio GUI. Supports PostgreSQL, MySQL, SQLite, and MongoDB.",
        "database",
        "prisma/prisma",
        40000,
        "https://prisma.io",
        "orm,typescript,database,migrations",
        "npm install prisma @prisma/client",
        "code",
    ),
    (
        "drizzle-orm",
        "Drizzle ORM",
        "TypeScript ORM that feels like writing raw SQL",
        "Drizzle ORM is a lightweight TypeScript ORM with zero dependencies. "
        "SQL-like syntax, type-safe queries, edge-compatible, and lightning fast. "
        "The fastest-growing ORM in the JavaScript ecosystem.",
        "database",
        "drizzle-team/drizzle-orm",
        27000,
        "https://orm.drizzle.team",
        "orm,typescript,database,edge",
        "npm install drizzle-orm",
        "code",
    ),
    (
        "zod",
        "Zod",
        "TypeScript-first schema validation with static type inference",
        "Zod is a TypeScript-first schema declaration and validation library. "
        "Define schemas once, infer static types automatically. Works seamlessly "
        "with tRPC, React Hook Form, and any TypeScript project.",
        "developer-tools",
        "colinhacks/zod",
        34000,
        "https://zod.dev",
        "validation,typescript,schema,runtime",
        "npm install zod",
        "code",
    ),
    # API Tools ------------------------------------------------------------------
    (
        "trpc",
        "tRPC",
        "End-to-end typesafe APIs for TypeScript",
        "tRPC lets you build fully typesafe APIs without schemas or code generation. "
        "Share types between client and server. Pairs perfectly with Next.js and "
        "Zod. Core building block of the T3 Stack.",
        "api-tools",
        "trpc/trpc",
        36000,
        "https://trpc.io",
        "typescript,api,typesafe,nextjs",
        "npm install @trpc/server @trpc/client",
        "code",
    ),
    (
        "hono",
        "Hono",
        "Ultrafast web framework for the edge",
        "Hono is a small, simple, and ultrafast web framework for Cloudflare Workers, "
        "Deno, Bun, AWS Lambda, Node.js, and more. OpenAPI support, middleware "
        "ecosystem, and TypeScript-first design.",
        "api-tools",
        "honojs/hono",
        20000,
        "https://hono.dev",
        "edge,cloudflare,typescript,fast",
        "npm install hono",
        "code",
    ),
    # JS Runtime / Toolchain -----------------------------------------------------
    (
        "bun",
        "Bun",
        "Incredibly fast JavaScript runtime, bundler, test runner, and package manager",
        "Bun is a fast all-in-one JavaScript toolkit: runtime, bundler, test runner, "
        "and npm-compatible package manager. 3× faster npm installs, native TypeScript "
        "support, and Node.js compatibility.",
        "frontend-frameworks",
        "oven-sh/bun",
        74000,
        "https://bun.sh",
        "runtime,bundler,javascript,fast",
        "curl -fsSL https://bun.sh/install | bash",
        "code",
    ),
    # CSS Frameworks / Design Systems -------------------------------------------
    (
        "tailwindcss",
        "Tailwind CSS",
        "A utility-first CSS framework for rapid UI development",
        "Tailwind CSS is a utility-first CSS framework that lets you build any design "
        "directly in your HTML. No pre-built components — compose utilities to create "
        "custom designs without leaving your markup. Powers shadcn/ui, Flowbite, and more.",
        "frontend-frameworks",
        "tailwindlabs/tailwindcss",
        84000,
        "https://tailwindcss.com",
        "css,utility-first,styling,design-system",
        "npm install tailwindcss",
        "code",
    ),
    (
        "shadcn-ui",
        "shadcn/ui",
        "Beautifully designed components built with Radix UI and Tailwind CSS",
        "shadcn/ui is a collection of re-usable React components built with Radix UI "
        "and Tailwind CSS. Not a component library — copy the source into your project. "
        "Full control, zero vendor lock-in. Supports Next.js, Vite, Remix, and Astro.",
        "frontend-frameworks",
        "shadcn-ui/ui",
        82000,
        "https://ui.shadcn.com",
        "ui,react,tailwind,radix,components",
        "npx shadcn@latest init",
        "code",
    ),
    # Monorepo tooling -----------------------------------------------------------
    (
        "turborepo",
        "Turborepo",
        "High-performance build system for JavaScript and TypeScript monorepos",
        "Turborepo is a blazing-fast build system for monorepos. Intelligent caching, "
        "parallel execution, and remote caching via Vercel. Dramatically speeds up "
        "CI/CD pipelines for large JavaScript and TypeScript projects.",
        "developer-tools",
        "vercel/turborepo",
        26000,
        "https://turbo.build/repo",
        "monorepo,build-tool,caching,ci",
        "npx create-turbo@latest",
        "code",
    ),
    # Meta-frameworks ------------------------------------------------------------
    (
        "nextjs",
        "Next.js",
        "The React Framework for the Web",
        "Next.js is the most popular React meta-framework. App Router, Server Components, "
        "file-based routing, API routes, SSR, SSG, and ISR out of the box. Deployed on "
        "Vercel or self-hosted. Powers millions of production sites.",
        "frontend-frameworks",
        "vercel/next.js",
        128000,
        "https://nextjs.org",
        "react,ssr,ssg,fullstack,routing",
        "npx create-next-app@latest",
        "code",
    ),
    (
        "nuxt",
        "Nuxt",
        "The Intuitive Vue Framework",
        "Nuxt is the full-stack Vue framework. File-based routing, server routes, "
        "auto-imports, SSR/SSG/hybrid rendering, and a rich module ecosystem. "
        "Nuxt 3 brings full TypeScript support and the Nitro server engine.",
        "frontend-frameworks",
        "nuxt/nuxt",
        55000,
        "https://nuxt.com",
        "vue,ssr,ssg,fullstack,typescript",
        "npx nuxi@latest init my-app",
        "code",
    ),
    (
        "astro",
        "Astro",
        "The web framework for content-driven websites",
        "Astro is a modern static-site builder that ships zero JavaScript by default. "
        "Islands architecture lets you use React, Vue, Svelte, or Solid components "
        "where needed. Perfect for blogs, docs, and marketing sites.",
        "frontend-frameworks",
        "withastro/astro",
        47000,
        "https://astro.build",
        "ssg,islands,performance,content",
        "npm create astro@latest",
        "code",
    ),
    # Developer Tools ------------------------------------------------------------
    (
        "typescript",
        "TypeScript",
        "TypeScript is JavaScript with syntax for types",
        "TypeScript adds optional static types to JavaScript, catching errors at "
        "compile time. Maintained by Microsoft, it's the standard for large-scale "
        "JS codebases. Ships with a compiler (tsc) and full IDE tooling.",
        "developer-tools",
        "microsoft/TypeScript",
        101000,
        "https://typescriptlang.org",
        "typescript,javascript,types,compiler",
        "npm install typescript --save-dev",
        "code",
    ),
    # Search Engines -------------------------------------------------------------
    (
        "meilisearch",
        "Meilisearch",
        "A lightning-fast search engine that fits effortlessly into any workflow",
        "Meilisearch is an open-source, self-hostable search engine focused on speed "
        "and developer experience. Typo-tolerant, relevancy-tunable, and easy to "
        "integrate with instant search UI widgets.",
        "search-engine",
        "meilisearch/meilisearch",
        49000,
        "https://meilisearch.com",
        "search,full-text,self-hosted,fast",
        "docker run -it --rm -p 7700:7700 getmeili/meilisearch",
        "code",
    ),
    # Headless CMS ---------------------------------------------------------------
    (
        "payload-cms",
        "Payload CMS",
        "The most powerful TypeScript headless CMS",
        "Payload is a fully TypeScript-native headless CMS and application framework. "
        "Code-first configuration, auto-generated REST & GraphQL APIs, a beautiful admin UI, "
        "and no vendor lock-in. Self-host on Node.js + MongoDB or PostgreSQL.",
        "headless-cms",
        "payloadcms/payload",
        32000,
        "https://payloadcms.com",
        "headless-cms,typescript,graphql,self-hosted",
        "npx create-payload-app@latest",
        "code",
    ),
    # Authentication libraries ---------------------------------------------------
    (
        "lucia-auth",
        "Lucia",
        "Simple and flexible auth library for TypeScript",
        "Lucia is a lightweight, framework-agnostic TypeScript auth library. "
        "Handles sessions, OAuth (GitHub, Google, etc.), and password hashing with "
        "full control over your database schema. No magic, no vendor lock-in.",
        "authentication",
        "lucia-auth/lucia",
        11000,
        "https://lucia-auth.com",
        "auth,typescript,session,oauth",
        "npm install lucia",
        "code",
    ),
    (
        "better-auth",
        "Better Auth",
        "The most comprehensive authentication framework for TypeScript",
        "Better Auth is a framework-agnostic TypeScript authentication library with "
        "built-in support for email/password, OAuth, 2FA, sessions, organisations, "
        "and plugins. Works with Next.js, Nuxt, SvelteKit, Hono, and more.",
        "authentication",
        "better-auth/better-auth",
        14000,
        "https://better-auth.com",
        "auth,typescript,oauth,2fa,nextjs",
        "npm install better-auth",
        "code",
    ),
    (
        "nextauth",
        "NextAuth.js",
        "Authentication for the Web",
        "NextAuth.js (now Auth.js) is the most popular open-source authentication "
        "library for Next.js and the broader JavaScript ecosystem. Supports 60+ OAuth "
        "providers (GitHub, Google, Discord, etc.), email/passwordless login, and "
        "database sessions. Ships with adapters for Prisma, Drizzle, and more. "
        "26k+ GitHub stars; used by hundreds of thousands of projects.",
        "authentication",
        "nextauthjs/next-auth",
        26000,
        "https://authjs.dev",
        "auth,nextjs,oauth,sessions,typescript",
        "npm install next-auth",
        "code",
    ),
    (
        "passport",
        "Passport.js",
        "Simple, unobtrusive authentication for Node.js",
        "Passport is the most widely deployed Node.js authentication middleware. "
        "It provides a clean, modular mechanism for authentication via 500+ "
        "strategies: OAuth (Google, GitHub, Facebook), local username/password, "
        "JWT, API keys, and more. Framework-agnostic — works with Express, Fastify, "
        "Hapi, and other Node.js frameworks. 23k+ GitHub stars.",
        "authentication",
        "jaredhanson/passport",
        23000,
        "https://www.passportjs.org",
        "auth,nodejs,oauth,jwt,strategy,express",
        "npm install passport",
        "code",
    ),
    # Database — OLAP / Analytics ------------------------------------------------
    (
        "clickhouse",
        "ClickHouse",
        "The fastest open-source analytical database",
        "ClickHouse is an open-source column-oriented OLAP database for real-time analytics. "
        "Processes billions of rows per second, supports SQL, and excels at aggregation "
        "queries. Used at scale by Cloudflare, ByteDance, and Contentsquare.",
        "database",
        "ClickHouse/ClickHouse",
        37000,
        "https://clickhouse.com",
        "olap,analytics,column-store,fast",
        "docker run -d --name clickhouse clickhouse/clickhouse-server",
        "code",
    ),
    (
        "surrealdb",
        "SurrealDB",
        "The ultimate multi-model database for tomorrow's applications",
        "SurrealDB is a multi-model database that combines SQL querying, graph "
        "relations, document storage, and key-value access in a single engine. "
        "Runs embedded (like SQLite), as a server, or distributed in the cloud. "
        "Real-time live queries, schema-optional, built-in auth, and a JavaScript "
        "SDK make it popular for indie devs and full-stack apps. 28k+ GitHub stars.",
        "database",
        "surrealdb/surrealdb",
        28000,
        "https://surrealdb.com",
        "multi-model,sql,graph,document,realtime,embedded,rust",
        "curl -sSf https://install.surrealdb.com | sh",
        "code",
    ),
    (
        "libsql",
        "libSQL",
        "The open-source, open-contribution fork of SQLite",
        "libSQL is an open-source fork of SQLite maintained by the Turso team, "
        "adding server mode, HTTP API, replication, and WASM builds while staying "
        "100% compatible with SQLite. Powers Turso's distributed serverless SQLite "
        "and can also be used standalone as a local or embedded database. 5k+ stars.",
        "database",
        "tursodatabase/libsql",
        5000,
        "https://libsql.org",
        "sqlite,distributed,serverless,turso,embedded,fork",
        "npm install @libsql/client",
        "code",
    ),
    # DevOps — Self-hosting ------------------------------------------------------
    (
        "coolify",
        "Coolify",
        "Self-hosted Heroku / Netlify alternative",
        "Coolify is an open-source, self-hostable platform-as-a-service. Deploy apps, "
        "databases, and services to your own server with a Heroku-like UI. Supports "
        "Docker Compose, Nixpacks, static sites, and more.",
        "devops-infrastructure",
        "coollabsio/coolify",
        32000,
        "https://coolify.io",
        "paas,self-hosted,docker,deployment",
        "curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash",
        "code",
    ),
    # Meta-frameworks — additional -----------------------------------------------
    (
        "remix",
        "Remix",
        "Full stack web framework built on web standards",
        "Remix is a full-stack React framework that leverages web fundamentals: "
        "browser forms, HTTP caching, and progressive enhancement. "
        "Nested routing, server-side rendering, and streaming out of the box. "
        "Owned by Shopify, used in production at major companies.",
        "frontend-frameworks",
        "remix-run/remix",
        32000,
        "https://remix.run",
        "react,ssr,fullstack,routing",
        "npx create-remix@latest",
        "code",
    ),
    (
        "solidjs",
        "SolidJS",
        "Simple and performant reactivity for building user interfaces",
        "SolidJS is a declarative JavaScript library for building UIs. "
        "Uses fine-grained reactivity — no virtual DOM, no diffing. "
        "Consistently benchmarks faster than React and Vue. "
        "Solid Start is the full-stack meta-framework.",
        "frontend-frameworks",
        "solidjs/solid",
        32000,
        "https://solidjs.com",
        "javascript,reactive,performance,signals",
        "npx degit solidjs/templates/js my-app",
        "code",
    ),
    # Authentication — SaaS providers -------------------------------------------
    (
        "clerk",
        "Clerk",
        "The most comprehensive User Management Platform",
        "Clerk provides complete user management: sign up, sign in, MFA, "
        "magic links, OAuth, and organization management. "
        "Pre-built React components, Next.js App Router support, "
        "and a beautiful hosted UI. Free tier for up to 10,000 MAUs.",
        "authentication",
        "clerkinc/clerk-js",
        5000,
        "https://clerk.com",
        "auth,nextjs,react,oauth,mfa",
        "npm install @clerk/nextjs",
        "saas",
    ),
    # Scheduling — open source --------------------------------------------------
    (
        "calcom",
        "Cal.com",
        "Scheduling infrastructure for absolutely everyone",
        "Cal.com is an open-source Calendly alternative with full self-hosting "
        "support. API-first design, embeddable scheduling widgets, team bookings, "
        "and 100+ integrations. Free for individuals, paid for teams.",
        "scheduling-booking",
        "calcom/cal.com",
        33000,
        "https://cal.com",
        "scheduling,booking,open-source,self-hosted",
        "npx create-turbo@latest -e with-tailwind",
        "code",
    ),
    # Notifications — multi-channel ---------------------------------------------
    (
        "novu",
        "Novu",
        "The open-source notification infrastructure for developers",
        "Novu is an open-source notification platform that unifies in-app, "
        "email, SMS, push, and chat notifications behind a single API. "
        "Pre-built notification center component, workflow editor, "
        "and subscriber management. Self-host or use cloud.",
        "notifications",
        "novuhq/novu",
        36000,
        "https://novu.co",
        "notifications,email,sms,push,in-app",
        "npm install @novu/node",
        "code",
    ),
    # Workflow automation --------------------------------------------------------
    (
        "n8n",
        "n8n",
        "Extendable workflow automation tool",
        "n8n is a self-hostable workflow automation platform with 400+ integrations. "
        "Visual editor, code nodes for custom logic, and a thriving community. "
        "Fair-code licensed — free to self-host, paid cloud available.",
        "ai-automation",
        "n8n-io/n8n",
        50000,
        "https://n8n.io",
        "workflow,automation,self-hosted,no-code",
        "npx n8n",
        "code",
    ),
    # AI — local LLM runner -----------------------------------------------------
    (
        "ollama",
        "Ollama",
        "Get up and running with large language models locally",
        "Ollama makes it easy to run open-source LLMs (Llama 3, Mistral, Gemma, Phi) "
        "locally on macOS, Linux, or Windows. REST API compatible with OpenAI's format. "
        "One-command install, no GPU required for smaller models.",
        "ai-dev-tools",
        "ollama/ollama",
        120000,
        "https://ollama.com",
        "llm,local,self-hosted,openai-compatible",
        "curl -fsSL https://ollama.com/install.sh | sh",
        "code",
    ),
    # Database — SQLite BaaS / local-first ----------------------------------------
    (
        "pocketbase",
        "PocketBase",
        "Open Source backend in 1 file",
        "PocketBase is an open-source backend consisting of a single executable — "
        "embedded SQLite, realtime subscriptions, auth, file storage, and an admin UI. "
        "Zero infrastructure overhead. Ship a full backend in minutes.",
        "database",
        "pocketbase/pocketbase",
        40000,
        "https://pocketbase.io",
        "sqlite,baas,self-hosted,realtime,auth",
        "# Download binary: https://pocketbase.io/docs/",
        "code",
    ),
    (
        "turso",
        "Turso",
        "SQLite for Production — distributed, fast, and cheap",
        "Turso is a distributed SQLite database built on libSQL. Deploy databases "
        "close to your users in 35+ regions. Free tier with 500 databases. "
        "Edge-compatible with Cloudflare Workers, Vercel Edge, and Fly.io.",
        "database",
        "tursodatabase/libsql",
        8000,
        "https://turso.tech",
        "sqlite,edge,distributed,serverless",
        "npm install @libsql/client",
        "code",
    ),
    # Frontend — form handling ---------------------------------------------------
    (
        "react-hook-form",
        "React Hook Form",
        "Performant, flexible and extensible forms with easy-to-use validation",
        "React Hook Form is the dominant form library for React. Minimal re-renders, "
        "small bundle size, easy integration with Zod/Yup validation, and DevTools. "
        "Adopted by Vercel, Prisma, and thousands of production apps.",
        "frontend-frameworks",
        "react-hook-form/react-hook-form",
        40000,
        "https://react-hook-form.com",
        "forms,react,validation,hooks",
        "npm install react-hook-form",
        "code",
    ),
    # Testing — E2E test framework -----------------------------------------------
    (
        "playwright",
        "Playwright",
        "Reliable end-to-end testing for modern web apps",
        "Playwright is Microsoft's end-to-end testing framework for Node.js, Python, "
        ".NET, and Java. Runs tests against Chromium, Firefox, and WebKit with a single "
        "API. Auto-wait, tracing, screenshots, video recording, and a VSCode extension.",
        "testing-tools",
        "microsoft/playwright",
        65000,
        "https://playwright.dev",
        "e2e,testing,browser-automation,headless",
        "npm install @playwright/test",
        "code",
    ),
    # Analytics — open-source product analytics ---------------------------------
    (
        "posthog",
        "PostHog",
        "The open-source product analytics platform",
        "PostHog is the all-in-one open-source analytics platform: product analytics, "
        "session replay, feature flags, A/B testing, and surveys. Self-host on your "
        "own infrastructure or use PostHog Cloud. No vendor lock-in.",
        "analytics-metrics",
        "PostHog/posthog",
        24000,
        "https://posthog.com",
        "analytics,product-analytics,feature-flags,self-hosted",
        "pip install posthog",
        "code",
    ),
    # Monitoring — error tracking -----------------------------------------------
    (
        "sentry",
        "Sentry",
        "Application monitoring for every developer",
        "Sentry is the most widely used open-source error tracking and performance "
        "monitoring platform. Catch exceptions, trace slow requests, and replay user "
        "sessions. SDKs for Python, JavaScript, Go, Java, and 100+ more.",
        "monitoring-uptime",
        "getsentry/sentry",
        39000,
        "https://sentry.io",
        "error-tracking,performance,monitoring,observability",
        "pip install sentry-sdk",
        "code",
    ),
    # Headless CMS — popular open-source ----------------------------------------
    (
        "strapi",
        "Strapi",
        "The leading open-source headless CMS",
        "Strapi is the most popular open-source headless CMS. TypeScript-native, "
        "customizable content types, REST and GraphQL APIs auto-generated, "
        "and a rich plugin marketplace. Self-host on Node.js or use Strapi Cloud.",
        "headless-cms",
        "strapi/strapi",
        63000,
        "https://strapi.io",
        "headless-cms,nodejs,graphql,self-hosted,typescript",
        "npx create-strapi-app@latest my-project",
        "code",
    ),
    # API / Backend Frameworks ---------------------------------------------------
    (
        "fastapi",
        "FastAPI",
        "High performance, easy to learn, fast to code Python API framework",
        "FastAPI is a modern, fast Python web framework for building APIs with "
        "standard type hints. Automatic interactive docs (Swagger + ReDoc), "
        "async-first design, and Pydantic-powered validation. One of the fastest "
        "Python frameworks available.",
        "api-tools",
        "tiangolo/fastapi",
        77000,
        "https://fastapi.tiangolo.com",
        "python,api,async,openapi,pydantic",
        "pip install fastapi uvicorn",
        "code",
    ),
    (
        "express",
        "Express.js",
        "Fast, unopinionated, minimalist web framework for Node.js",
        "Express is the most widely used Node.js web framework. Minimal and "
        "flexible with a rich middleware ecosystem. The foundation of countless "
        "production Node.js apps and the basis for higher-level frameworks "
        "like NestJS and LoopBack.",
        "api-tools",
        "expressjs/express",
        65000,
        "https://expressjs.com",
        "nodejs,javascript,http,middleware,web-framework",
        "npm install express",
        "code",
    ),
    (
        "django",
        "Django",
        "The web framework for perfectionists with deadlines",
        "Django is a high-level Python web framework with batteries included: "
        "ORM, admin panel, auth, forms, and URL routing out of the box. "
        "Powers Instagram, Disqus, and Mozilla. 20+ years of battle-tested "
        "stability and a thriving ecosystem.",
        "api-tools",
        "django/django",
        82000,
        "https://www.djangoproject.com",
        "python,orm,admin,batteries-included,full-stack",
        "pip install django",
        "code",
    ),
    (
        "flask",
        "Flask",
        "A simple framework for building complex web applications",
        "Flask is a lightweight Python WSGI micro-framework. No ORM, no "
        "default database — choose your own components. Great for small APIs, "
        "microservices, and prototyping. Extensible via a large ecosystem "
        "of Flask extensions.",
        "api-tools",
        "pallets/flask",
        68000,
        "https://flask.palletsprojects.com",
        "python,micro-framework,wsgi,lightweight,api",
        "pip install flask",
        "code",
    ),
    (
        "gin",
        "Gin",
        "HTTP web framework written in Go with martini-like API",
        "Gin is the most popular Go HTTP web framework. 40x faster than Martini "
        "with a zero-allocation router, built-in middleware, JSON validation, "
        "and route grouping. The standard choice for Go REST APIs.",
        "api-tools",
        "gin-gonic/gin",
        79000,
        "https://gin-gonic.com",
        "go,golang,http,routing,fast",
        "go get -u github.com/gin-gonic/gin",
        "code",
    ),
    # Testing — unit test frameworks -----------------------------------------------
    (
        "jest",
        "Jest",
        "Delightful JavaScript testing",
        "Jest is the most popular JavaScript testing framework. Zero config for most "
        "JavaScript projects, snapshot testing, code coverage, mocking, and a watch mode "
        "for rapid development. Created by Meta, used by React, Next.js, and thousands "
        "of production codebases.",
        "testing-tools",
        "jestjs/jest",
        44000,
        "https://jestjs.io",
        "testing,unit-test,javascript,snapshots,mocking",
        "npm install jest --save-dev",
        "code",
    ),
    (
        "vitest",
        "Vitest",
        "Next generation testing framework powered by Vite",
        "Vitest is a blazing-fast unit test framework built on Vite. Compatible with "
        "Jest's API, instant HMR-based reruns, native ESM support, and out-of-the-box "
        "TypeScript support. The standard test runner for Vite + React/Vue/Svelte.",
        "testing-tools",
        "vitest-dev/vitest",
        13000,
        "https://vitest.dev",
        "testing,unit-test,vite,typescript,fast",
        "npm install vitest --save-dev",
        "code",
    ),
    (
        "cypress",
        "Cypress",
        "Fast, easy and reliable testing for anything that runs in a browser",
        "Cypress is a front-end testing tool for E2E, integration, and unit tests. "
        "Runs in the same browser as your app, with time-travel debugging, real-time "
        "reload, and automatic waiting. Includes Cypress Cloud for CI recording.",
        "testing-tools",
        "cypress-io/cypress",
        47000,
        "https://cypress.io",
        "e2e,testing,browser,integration,component",
        "npm install cypress --save-dev",
        "code",
    ),
    # Realtime / WebSockets --------------------------------------------------------
    (
        "socket-io",
        "Socket.IO",
        "Bidirectional and low-latency communication for every platform",
        "Socket.IO is the most widely used WebSocket library. Automatic fallbacks "
        "(long-polling), rooms, namespaces, and a rich event system. Node.js server "
        "with official clients for JavaScript, Python, Java, and Swift.",
        "api-tools",
        "socketio/socket.io",
        60000,
        "https://socket.io",
        "websocket,realtime,event-driven,nodejs,rooms",
        "npm install socket.io",
        "code",
    ),
    # Email — templates / rendering -----------------------------------------------
    (
        "react-email",
        "React Email",
        "A collection of high-quality, unstyled React components for email",
        "React Email lets you build responsive email templates with React and TypeScript. "
        "Components for all major email clients, live preview, and integrations with "
        "Resend, SendGrid, Nodemailer, and AWS SES.",
        "email-marketing",
        "resend/react-email",
        14000,
        "https://react.email",
        "email,react,template,transactional,typescript",
        "npm install react-email",
        "code",
    ),
    # JS Runtimes — Deno -------------------------------------------------------
    (
        "deno",
        "Deno",
        "A modern runtime for JavaScript and TypeScript",
        "Deno is a secure JavaScript and TypeScript runtime built on V8. Built-in "
        "TypeScript support, web-standard APIs, a built-in linter/formatter/test runner, "
        "and a standard library. Deno 2 brings Node.js compatibility and npm support.",
        "frontend-frameworks",
        "denoland/deno",
        93000,
        "https://deno.com",
        "runtime,typescript,javascript,secure,web-standards",
        "curl -fsSL https://deno.land/install.sh | sh",
        "code",
    ),
    # Security — secrets management -------------------------------------------
    (
        "infisical",
        "Infisical",
        "Open-source secret management platform",
        "Infisical is an open-source secrets manager that syncs environment variables "
        "across your team and infrastructure. SDKs for Node.js, Python, Go, and more. "
        "Self-host or use Infisical Cloud. Supports secret versioning, audit logs, and RBAC.",
        "security-tools",
        "Infisical/infisical",
        15000,
        "https://infisical.com",
        "secrets,env,security,self-hosted,open-source",
        "npm install @infisical/sdk",
        "code",
    ),
    # API / Realtime — collaborative ------------------------------------------
    (
        "liveblocks",
        "Liveblocks",
        "Realtime collaboration infrastructure for developers",
        "Liveblocks provides APIs and components for building collaborative features: "
        "multiplayer cursors, presence, live comments, and document editing (like Notion/Figma). "
        "Conflict-free CRDT backend, React hooks, and a customizable UI kit.",
        "api-tools",
        "liveblocks/liveblocks",
        4000,
        "https://liveblocks.io",
        "realtime,collaboration,crdt,websocket,presence",
        "npm install @liveblocks/client @liveblocks/react",
        "saas",
    ),
    # Auth — enterprise / directory sync --------------------------------------
    (
        "workos",
        "WorkOS",
        "Add enterprise features in minutes",
        "WorkOS provides APIs for enterprise auth: Single Sign-On (SAML, OIDC), "
        "SCIM directory sync, and multi-factor authentication. Drop-in AuthKit UI. "
        "Free for up to 1M MAUs. Used by Vercel, Perplexity, and Drata.",
        "authentication",
        "workos/workos-node",
        1200,
        "https://workos.com",
        "auth,sso,saml,scim,enterprise",
        "npm install @workos-inc/node",
        "saas",
    ),
    # Frontend — Component Dev / Bundlers ----------------------------------------
    (
        "storybook",
        "Storybook",
        "Build UI components and pages in isolation",
        "Storybook is the industry-standard workshop for building, testing, and "
        "documenting UI components in isolation. Works with React, Vue, Angular, "
        "Svelte, and more. Includes addons for accessibility, visual testing, "
        "and interaction testing. Used by Airbnb, IBM, Shopify, and thousands more.",
        "frontend-frameworks",
        "storybookjs/storybook",
        84000,
        "https://storybook.js.org",
        "component,testing,ui,documentation,visual-testing",
        "npx storybook@latest init",
        "code",
    ),
    (
        "rspack",
        "Rspack",
        "The fast Rust-based web bundler",
        "Rspack is a high-performance JavaScript bundler written in Rust, "
        "providing webpack-compatible APIs and plugins. Achieves 5-10x faster "
        "build speeds than webpack with minimal migration effort. Built by "
        "ByteDance's Web Infra team and used at scale in production.",
        "frontend-frameworks",
        "web-infra-dev/rspack",
        10000,
        "https://rspack.dev",
        "bundler,build-tool,rust,fast,webpack-compatible",
        "npm install @rspack/core @rspack/cli",
        "code",
    ),
    # Feature Flags ---------------------------------------------------------------
    (
        "flipt",
        "Flipt",
        "Open-source, self-hosted feature flags",
        "Flipt is a fully self-hosted, open-source feature flag solution with "
        "first-class GitOps support. Store flag configuration in Git, use "
        "gRPC or REST APIs, and integrate via official SDKs for Go, Python, "
        "Node.js, Java, and more. No telemetry, no vendor lock-in.",
        "feature-flags",
        "flipt-io/flipt",
        4000,
        "https://flipt.io",
        "feature-flags,self-hosted,gitops,grpc",
        "brew install flipt-io/brew/flipt",
        "code",
    ),
    (
        "growthbook",
        "GrowthBook",
        "Open source feature flags and A/B testing",
        "GrowthBook is an open-source platform for feature flags, A/B testing, "
        "and experiment analysis. Self-host or use GrowthBook Cloud. SDKs for "
        "JavaScript, React, Python, Go, Ruby, PHP, and more. "
        "Connect to your existing data warehouse for statistical analysis.",
        "feature-flags",
        "growthbook/growthbook",
        6000,
        "https://growthbook.io",
        "feature-flags,ab-testing,experimentation,analytics,open-source",
        "npm install @growthbook/growthbook-react",
        "code",
    ),
    # Publishing / Newsletters ---------------------------------------------------
    (
        "ghost",
        "Ghost",
        "The world's most popular open source headless CMS for content creators",
        "Ghost is an open-source publishing platform built for professional creators. "
        "Newsletter sending, membership & subscriptions, SEO, and a clean writing editor. "
        "Self-host on Node.js or use Ghost(Pro) managed hosting.",
        "newsletters-content",
        "TryGhost/Ghost",
        47000,
        "https://ghost.org",
        "publishing,newsletter,cms,membership,self-hosted",
        "npm install ghost-cli -g && ghost install",
        "code",
    ),
    # AI frameworks — LLM orchestration and agent tooling ---------------------------
    (
        "llamaindex",
        "LlamaIndex",
        "The leading data framework for building LLM applications",
        "LlamaIndex is the go-to framework for building RAG (Retrieval-Augmented "
        "Generation) applications. Connect LLMs to your data sources — PDFs, databases, "
        "APIs — with 160+ data connectors, query engines, and agent tools. "
        "Supports OpenAI, Anthropic, Llama, Mistral, and more.",
        "ai-automation",
        "run-llama/llama_index",
        38000,
        "https://llamaindex.ai",
        "rag,llm,ai,agents,data-framework",
        "pip install llama-index",
        "code",
    ),
    (
        "litellm",
        "LiteLLM",
        "Call 100+ LLMs using the same OpenAI format",
        "LiteLLM provides a unified interface to 100+ LLM providers — OpenAI, Anthropic, "
        "Vertex AI, Bedrock, Ollama, and more — with a single API format. "
        "Drop-in replacement for OpenAI SDK calls. Includes a proxy server with "
        "rate limiting, spend tracking, fallbacks, and load balancing.",
        "ai-dev-tools",
        "BerriAI/litellm",
        15000,
        "https://litellm.ai",
        "llm,proxy,openai,anthropic,routing",
        "pip install litellm",
        "code",
    ),
    (
        "crewai",
        "CrewAI",
        "Framework for orchestrating role-playing, autonomous AI agents",
        "CrewAI enables teams of AI agents to work together on complex tasks. "
        "Define agents with roles, goals, and tools; orchestrate them into crews "
        "that collaborate, delegate, and produce results. Supports LangChain tools "
        "and integrates with any LLM. Sequential and hierarchical process types.",
        "ai-automation",
        "crewAIInc/crewAI",
        25000,
        "https://crewai.com",
        "agents,multi-agent,llm,automation,orchestration",
        "pip install crewai",
        "code",
    ),
    # DevOps — Kubernetes package management and GitOps ----------------------------
    (
        "helm",
        "Helm",
        "The Kubernetes Package Manager",
        "Helm is the standard package manager for Kubernetes. Define, install, and "
        "upgrade complex Kubernetes applications using Charts — pre-configured "
        "resource packages. Helm Hub hosts 10,000+ community charts. "
        "Version-controlled, rollback-capable deployments.",
        "devops-infrastructure",
        "helm/helm",
        27000,
        "https://helm.sh",
        "kubernetes,k8s,package-manager,devops",
        "brew install helm",
        "code",
    ),
    (
        "argocd",
        "Argo CD",
        "Declarative GitOps CD for Kubernetes",
        "Argo CD is a declarative, GitOps continuous delivery tool for Kubernetes. "
        "Automatically syncs your cluster state to match Git — the source of truth. "
        "Web UI, CLI, and SSO support. Tracks deployments, diffs, and rollbacks. "
        "CNCF graduated project with massive enterprise adoption.",
        "devops-infrastructure",
        "argoproj/argo-cd",
        18000,
        "https://argo-cd.readthedocs.io",
        "kubernetes,gitops,cd,continuous-delivery,devops",
        "kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml",
        "code",
    ),
    # Background jobs / workflow orchestration -------------------------------------
    (
        "dagster",
        "Dagster",
        "An orchestration platform for the development, production, and observation of data assets",
        "Dagster is a cloud-native data orchestration platform. Define pipelines as "
        "software-defined assets — transformations, ML models, reports. "
        "Built-in scheduling, partitioning, and lineage tracking. "
        "Works with dbt, Spark, Snowflake, and all major data tools.",
        "background-jobs",
        "dagster-io/dagster",
        12000,
        "https://dagster.io",
        "orchestration,data-pipeline,assets,workflow,etl",
        "pip install dagster dagit",
        "code",
    ),
    (
        "prefect",
        "Prefect",
        "The modern workflow orchestration platform",
        "Prefect is a Python-first workflow orchestration tool. Decorate functions "
        "with @flow and @task to turn Python scripts into observable, retryable workflows. "
        "Concurrent execution, subflows, caching, and a hosted Cloud tier. "
        "Much simpler setup than Airflow for most use cases.",
        "background-jobs",
        "PrefectHQ/prefect",
        16000,
        "https://prefect.io",
        "workflow,orchestration,python,etl,data-pipeline",
        "pip install prefect",
        "code",
    ),
    # API — gRPC and high-performance HTTP frameworks ------------------------------
    (
        "grpc",
        "gRPC",
        "A high performance, open source universal RPC framework",
        "gRPC is a modern open-source RPC framework by Google. Uses Protocol Buffers "
        "for serialization and HTTP/2 for transport — delivering 5-10x better performance "
        "than REST/JSON. Supports bidirectional streaming, server push, and "
        "code generation for 10+ languages. CNCF graduated project.",
        "api-tools",
        "grpc/grpc",
        42000,
        "https://grpc.io",
        "rpc,api,protobuf,http2,streaming",
        "pip install grpcio grpcio-tools",
        "code",
    ),
    (
        "fastify",
        "Fastify",
        "Fast and low overhead web framework for Node.js",
        "Fastify is one of the fastest Node.js web frameworks — up to 2x faster than "
        "Express. JSON Schema validation, plugin architecture, and TypeScript support "
        "built in. Hooks, decorators, and a rich ecosystem of 250+ plugins. "
        "Production-proven at massive scale.",
        "api-tools",
        "fastify/fastify",
        33000,
        "https://fastify.dev",
        "nodejs,http,rest,api,typescript",
        "npm install fastify",
        "code",
    ),
    # Background jobs / workflow orchestration — durable execution --------------------
    (
        "temporal",
        "Temporal",
        "Durable execution system for resilient applications",
        "Temporal is an open-source durable workflow execution engine. Write business "
        "logic as code — Temporal ensures it runs to completion despite failures, "
        "retries, or server restarts. Runs long-lived processes with built-in "
        "versioning, signals, queries, and child workflows. Used at Stripe, Snap, Datadog.",
        "background-jobs",
        "temporalio/temporal",
        12000,
        "https://temporal.io",
        "workflow,orchestration,durable-execution,microservices,saga",
        "brew install temporal",
        "code",
    ),
    (
        "inngest",
        "Inngest",
        "The durable execution engine for modern serverless stacks",
        "Inngest lets you write reliable, event-driven background jobs in your existing "
        "codebase. Zero infrastructure — works with Next.js, Remix, SvelteKit, and any "
        "framework. Automatic retries, fan-out, scheduled functions, and observability "
        "built in. No queue config required.",
        "background-jobs",
        "inngest/inngest",
        9000,
        "https://inngest.com",
        "background-jobs,serverless,event-driven,nextjs,workflow",
        "npm install inngest",
        "code",
    ),
    (
        "trigger-dev",
        "Trigger.dev",
        "Open-source background jobs with no timeouts",
        "Trigger.dev is an open-source background job framework for TypeScript. "
        "Write long-running jobs that survive Vercel/Cloudflare function timeouts. "
        "SDK-first design, real-time run logs, retries, concurrency, and queue management. "
        "Self-host or use the managed cloud.",
        "background-jobs",
        "triggerdotdev/trigger.dev",
        10000,
        "https://trigger.dev",
        "background-jobs,typescript,nextjs,serverless,long-running",
        "npm install @trigger.dev/sdk",
        "code",
    ),
    # Background jobs / workflow automation — open-source Zapier alternatives --------
    (
        "windmill",
        "Windmill",
        "Open-source workflow engine and script runner",
        "Windmill is a fast, open-source workflow engine and developer platform. "
        "Write scripts in Python, TypeScript, Go, Bash, or SQL — Windmill handles "
        "scheduling, parallelism, retries, secrets, and a polished UI. Self-host on "
        "Docker or use Windmill Cloud. Popular Airflow/Zapier alternative for teams "
        "who want code-first workflows without the enterprise overhead.",
        "background-jobs",
        "windmill-labs/windmill",
        12000,
        "https://windmill.dev",
        "workflow,automation,cron,scripting,self-hosted,python,typescript",
        "docker compose up -d",
        "code",
    ),
    (
        "activepieces",
        "Activepieces",
        "Open-source business automation — your Zapier alternative",
        "Activepieces is an open-source automation platform with a visual flow builder "
        "and 200+ connectors. Self-host for free or use the managed cloud. Features "
        "include scheduled triggers, webhooks, loops, conditional logic, and an SDK "
        "for building custom pieces. GDPR-compliant, privacy-first architecture.",
        "background-jobs",
        "activepieces/activepieces",
        12000,
        "https://activepieces.com",
        "automation,workflow,no-code,zapier-alternative,self-hosted,webhooks",
        "docker compose up",
        "code",
    ),
    # API / Backend — Rust web frameworks -------------------------------------------
    (
        "axum",
        "Axum",
        "Ergonomic and modular web framework built with Tokio and Tower",
        "Axum is a modular Rust web framework from the Tokio team. Built on Tower "
        "middleware — composable, macro-free handlers with full async support. "
        "Ergonomic routing, extractors, and WebSocket support. The fastest-growing "
        "Rust web framework with excellent ecosystem compatibility.",
        "api-tools",
        "tokio-rs/axum",
        20000,
        "https://docs.rs/axum",
        "rust,async,tokio,http,web-framework",
        "cargo add axum tokio",
        "code",
    ),
    (
        "echo-go",
        "Echo",
        "High performance, minimalist Go web framework",
        "Echo is a high-performance, extensible Go web framework. Optimised HTTP router "
        "with zero dynamic memory allocation. Middleware groups, data binding, automatic "
        "TLS, and HTTP/2 support. The second most popular Go framework after Gin.",
        "api-tools",
        "labstack/echo",
        30000,
        "https://echo.labstack.com",
        "go,golang,http,routing,fast",
        "go get github.com/labstack/echo/v4",
        "code",
    ),
    # Caching — Redis fork / alternative --------------------------------------------
    (
        "dragonfly",
        "Dragonfly",
        "Redis-compatible in-memory data store — 25× faster than Redis",
        "Dragonfly is a modern in-memory data store fully compatible with Redis and "
        "Memcached APIs. Uses a novel multi-threaded architecture that delivers "
        "25× more throughput on a single instance. Drop-in Redis replacement "
        "with no code changes. Open-source with a managed cloud tier.",
        "caching",
        "dragonflydb/dragonfly",
        26000,
        "https://dragonflydb.io",
        "redis,caching,in-memory,performance,drop-in",
        "docker run --ulimit memlock=-1 ghcr.io/dragonflydb/dragonfly",
        "code",
    ),
    # AI — graph-based agent orchestration -------------------------------------------
    (
        "langgraph",
        "LangGraph",
        "Build stateful, multi-actor AI agent applications",
        "LangGraph is a library for building stateful, multi-actor applications "
        "with LLMs. Graph-based orchestration with cycles, controllability, and "
        "persistence. Build agents that can plan, reflect, and use tools. "
        "Part of the LangChain ecosystem, used for complex multi-step AI workflows.",
        "ai-automation",
        "langchain-ai/langgraph",
        9000,
        "https://langchain-ai.github.io/langgraph",
        "ai,agents,llm,graph,orchestration,langchain",
        "pip install langgraph",
        "code",
    ),
    # AI — agent tool integrations ----------------------------------------------------
    (
        "composio",
        "Composio",
        "Production-ready tool integrations for AI agents",
        "Composio gives AI agents 150+ production-ready integrations: GitHub, Slack, "
        "Notion, Linear, Gmail, and more. Managed auth (OAuth, API keys), "
        "action filtering, and SDKs for LangChain, CrewAI, AutoGen, and OpenAI. "
        "Connect AI agents to the tools your users already use.",
        "ai-dev-tools",
        "ComposioHQ/composio",
        17000,
        "https://composio.dev",
        "ai,agents,integrations,tools,mcp,langchain",
        "pip install composio-core",
        "code",
    ),
    # API / Backend — Bun-native TypeScript framework ---------------------------------
    (
        "elysia",
        "Elysia",
        "TypeScript framework supercharged by Bun",
        "Elysia is a TypeScript web framework built for Bun. End-to-end type safety "
        "with Eden treaty, declarative schema validation, Swagger generation, and "
        "one of the fastest throughputs of any Node/Bun framework. "
        "Plugin system, middleware, WebSocket, and SSE support built in.",
        "api-tools",
        "elysiajs/elysia",
        11000,
        "https://elysiajs.com",
        "bun,typescript,web-framework,fast,type-safe",
        "bun add elysia",
        "code",
    ),
    # API / Backend — UnJS universal server engine ------------------------------------
    (
        "nitro",
        "Nitro",
        "Build and deploy universal JavaScript servers",
        "Nitro is a next-generation server toolkit from UnJS (the team behind Nuxt). "
        "Write server code once and deploy to Node.js, Deno, Bun, Cloudflare Workers, "
        "AWS Lambda, and more. Powers Nuxt 3 under the hood. "
        "File-based routing, TypeScript-first, auto-imports, and edge-ready.",
        "api-tools",
        "unjs/nitro",
        6000,
        "https://nitro.unjs.io",
        "javascript,server,universal,edge,nuxt,bun,cloudflare",
        "npm install nitropack",
        "code",
    ),
    # Testing — load and performance testing ------------------------------------------
    (
        "artillery",
        "Artillery",
        "Cloud-scale load testing for APIs and microservices",
        "Artillery is a modern load testing and smoke testing platform for APIs, "
        "microservices, and web apps. YAML or JS scenarios, HTTP/WebSocket/Socket.io, "
        "Playwright browser load tests, and a cloud runner for distributed tests. "
        "Open-source core with Artillery Cloud for results and dashboards.",
        "testing-tools",
        "artilleryio/artillery",
        8000,
        "https://artillery.io",
        "load-testing,performance,api-testing,k8s,cloud",
        "npm install -g artillery",
        "code",
    ),
    (
        "locust",
        "Locust",
        "An open source load testing tool — define user behaviour with Python",
        "Locust is a scalable Python load testing framework. Write test scenarios as "
        "plain Python code — no XML or YAML needed. Distributed load generation, "
        "a real-time web UI, and results exportable to CSV. "
        "Run locally or on cloud infrastructure for massive scale tests.",
        "testing-tools",
        "locustio/locust",
        25000,
        "https://locust.io",
        "load-testing,python,performance,distributed,api-testing",
        "pip install locust",
        "code",
    ),
    # Developer Tools — LLM-optimised web scraping ------------------------------------
    (
        "firecrawl",
        "Firecrawl",
        "Turn any website into LLM-ready data",
        "Firecrawl crawls websites and converts them to clean Markdown or structured "
        "JSON — optimised for feeding LLMs and RAG pipelines. "
        "Handles JavaScript-rendered pages, PDFs, auth, and rate limiting. "
        "Self-hostable open-source core; managed API available.",
        "developer-tools",
        "mendableai/firecrawl",
        26000,
        "https://firecrawl.dev",
        "scraping,llm,rag,markdown,crawler,ai",
        "pip install firecrawl-py",
        "code",
    ),
    # Developer Tools — Go desktop application framework ------------------------------
    (
        "wails",
        "Wails",
        "Build desktop apps using Go + Web technologies",
        "Wails lets you build cross-platform desktop apps using Go for the backend "
        "and any web tech (React, Vue, Svelte, Vanilla JS) for the frontend. "
        "Compiled to a single binary, native menus, system tray, file dialogs, "
        "and notifications. The Tauri equivalent for Go developers.",
        "developer-tools",
        "wailsapp/wails",
        27000,
        "https://wails.io",
        "go,golang,desktop,cross-platform,gui,electron-alternative",
        "go install github.com/wailsapp/wails/v2/cmd/wails@latest",
        "code",
    ),
    # Developer Tools — TypeScript runtime type validation ----------------------------
    (
        "arktype",
        "ArkType",
        "TypeScript's 1:1 validator — 100x faster than Zod",
        "ArkType is a TypeScript-first runtime type validation library. "
        "Write types using TypeScript syntax you already know — no new DSL. "
        "Instantiates 100x faster than Zod with better error messages, "
        "cyclic types, and morphs (transforms). The next-gen Zod alternative.",
        "developer-tools",
        "arktypeio/arktype",
        4000,
        "https://arktype.io",
        "typescript,validation,schema,zod-alternative,types",
        "npm install arktype",
        "code",
    ),
    # Frontend — Desktop app frameworks -------------------------------------------
    (
        "electron",
        "Electron",
        "Build cross-platform desktop apps with JavaScript, HTML, and CSS",
        "Electron lets you build cross-platform desktop applications using web technologies. "
        "It embeds Chromium and Node.js into a single binary so you can ship desktop apps "
        "with HTML, CSS, and JavaScript. Powers VS Code, Slack, Figma, Discord, and more.",
        "frontend-frameworks",
        "electron/electron",
        115000,
        "https://www.electronjs.org",
        "desktop,javascript,nodejs,chromium,cross-platform,gui",
        "npm install --save-dev electron",
        "code",
    ),
    (
        "tauri",
        "Tauri",
        "Build smaller, faster, and more secure desktop applications with a web frontend",
        "Tauri is a framework for building desktop apps using web tech for the frontend "
        "and Rust for the backend. Produces significantly smaller binaries than Electron "
        "(< 600KB) with lower memory usage. Uses the OS native WebView instead of bundling Chromium. "
        "Tauri 2.0 adds mobile (iOS/Android) support.",
        "frontend-frameworks",
        "tauri-apps/tauri",
        82000,
        "https://tauri.app",
        "desktop,rust,mobile,cross-platform,security,electron-alternative",
        "npm create tauri-app@latest",
        "code",
    ),
    # DevOps — release automation ---------------------------------------------------
    (
        "semantic-release",
        "semantic-release",
        "Fully automated version management and package publishing",
        "semantic-release automates the versioning and release process based on commit "
        "messages following the Conventional Commits specification. Determines next version "
        "automatically, generates changelogs, publishes to npm, and creates GitHub releases — "
        "all from your CI/CD pipeline.",
        "devops-infrastructure",
        "semantic-release/semantic-release",
        21000,
        "https://semantic-release.gitbook.io",
        "release,versioning,changelog,ci-cd,npm,conventional-commits",
        "npm install --save-dev semantic-release",
        "code",
    ),
    # Developer Tools — monorepo build system ------------------------------------------
    (
        "nx",
        "Nx",
        "Smart monorepo build system with distributed task execution",
        "Nx is an extensible build system for monorepos. Computes task dependency graphs, "
        "caches task results locally and remotely (Nx Cloud), and distributes CI across "
        "multiple machines. First-class support for React, Angular, Node.js, Next.js, "
        "Vite, and more. Works alongside or instead of Turborepo.",
        "developer-tools",
        "nrwl/nx",
        24000,
        "https://nx.dev",
        "monorepo,build-tool,ci,cache,typescript,javascript",
        "npx create-nx-workspace@latest",
        "code",
    ),
    # Database — data transformation / ETL ------------------------------------------
    (
        "dbt",
        "dbt (data build tool)",
        "Transform data in your warehouse using SQL",
        "dbt (data build tool) enables analytics engineers to transform raw data in "
        "their warehouse using SQL SELECT statements. Version-controlled, tested, "
        "documented data models. The dominant tool in the modern data stack "
        "(Airflow/Fivetran → dbt → BI). dbt Core is open-source; dbt Cloud is managed.",
        "database",
        "dbt-labs/dbt-core",
        9000,
        "https://getdbt.com",
        "sql,data-transformation,analytics,warehouse,etl",
        "pip install dbt-core",
        "code",
    ),
    # Database — ORMs and query builders ------------------------------------------
    (
        "mongoose",
        "Mongoose",
        "Elegant MongoDB object modelling for Node.js",
        "Mongoose is the most popular MongoDB ODM (Object Document Mapper) for Node.js. "
        "Schema-based models, middleware hooks, query chaining, and full TypeScript support. "
        "Powers countless Node.js + MongoDB production applications.",
        "database",
        "Automattic/mongoose",
        26000,
        "https://mongoosejs.com",
        "mongodb,odm,nodejs,schema,typescript",
        "npm install mongoose",
        "code",
    ),
    (
        "typeorm",
        "TypeORM",
        "ORM for TypeScript and JavaScript",
        "TypeORM is a full-featured ORM for TypeScript and JavaScript supporting "
        "PostgreSQL, MySQL, SQLite, MongoDB, and more. Active Record and Data Mapper "
        "patterns, migrations, relations, and a decorator-based API. "
        "The classic choice for NestJS and TypeScript backends.",
        "database",
        "typeorm/typeorm",
        34000,
        "https://typeorm.io",
        "orm,typescript,postgresql,mysql,sqlite,nestjs",
        "npm install typeorm reflect-metadata",
        "code",
    ),
    (
        "gorm",
        "GORM",
        "The fantastic ORM library for Go",
        "GORM is the most popular ORM for Go. Full-featured: associations, preloading, "
        "hooks, transactions, scopes, composite primary keys, and auto migrations. "
        "Supports PostgreSQL, MySQL, SQLite, and SQL Server. "
        "Convention over configuration with full customisability.",
        "database",
        "go-gorm/gorm",
        36000,
        "https://gorm.io",
        "orm,go,golang,postgresql,mysql,sqlite",
        "go get -u gorm.io/gorm",
        "code",
    ),
    (
        "kysely",
        "Kysely",
        "Type-safe SQL query builder for TypeScript",
        "Kysely is a type-safe, composable SQL query builder for TypeScript. "
        "No ORM magic — just raw SQL power with full type inference. "
        "Works with PostgreSQL, MySQL, SQLite (via dialect plugins). "
        "Used as the query layer under PlanetScale and several BaaS providers.",
        "database",
        "kysely-org/kysely",
        10000,
        "https://kysely.dev",
        "sql,typescript,query-builder,postgresql,type-safe",
        "npm install kysely",
        "code",
    ),
    (
        "sequelize",
        "Sequelize",
        "Feature-rich ORM for Node.js",
        "Sequelize is a battle-tested Node.js ORM supporting PostgreSQL, MySQL, "
        "MariaDB, SQLite, and Microsoft SQL Server. Eager loading, associations, "
        "transactions, migrations, and a rich query interface. "
        "One of the most widely used Node.js ORMs in production.",
        "database",
        "sequelize/sequelize",
        29000,
        "https://sequelize.org",
        "orm,nodejs,postgresql,mysql,sqlite,migrations",
        "npm install sequelize",
        "code",
    ),
    # Email — sending library -------------------------------------------------------
    (
        "nodemailer",
        "Nodemailer",
        "Send emails from Node.js — battle-tested since 2010",
        "Nodemailer is the most widely used Node.js email sending library. "
        "SMTP, SES, SendGrid, and custom transport support. "
        "Attachments, HTML templates, embedded images, DKIM signing, and OAuth2. "
        "Zero dependencies, easy setup, and 15+ years of production use.",
        "email-marketing",
        "nodemailer/nodemailer",
        16000,
        "https://nodemailer.com",
        "email,smtp,nodejs,transactional,attachments",
        "npm install nodemailer",
        "code",
    ),
    # Frontend — Routing libraries -------------------------------------------------
    (
        "react-router",
        "React Router",
        "Declarative routing for React — the most popular React router",
        "React Router is the standard routing library for React applications. "
        "Version 6+ brings nested routes, data loaders, actions, and form handling. "
        "React Router v7 merges Remix into the core, enabling full-stack routing "
        "with SSR, streaming, and server actions.",
        "frontend-frameworks",
        "remix-run/react-router",
        52000,
        "https://reactrouter.com",
        "routing,react,spa,fullstack",
        "npm install react-router",
        "code",
    ),
    (
        "tanstack-router",
        "TanStack Router",
        "Type-safe routing for React with first-class search params",
        "TanStack Router is a fully type-safe React router with URL-based state "
        "management, nested layouts, suspense-first data loading, and first-class "
        "search param serialization. Works with Vite and framework-agnostic.",
        "frontend-frameworks",
        "TanStack/router",
        9000,
        "https://tanstack.com/router",
        "routing,react,type-safe,search-params",
        "npm install @tanstack/react-router",
        "code",
    ),
    # Frontend — State machines -----------------------------------------------------
    (
        "xstate",
        "XState",
        "State machines and statecharts for the modern web",
        "XState is a state management and orchestration solution for JavaScript and "
        "TypeScript. Build complex async workflows, actor-based systems, and UI logic "
        "with statecharts. Works with React, Vue, Svelte, and Node.js.",
        "frontend-frameworks",
        "statelyai/xstate",
        26000,
        "https://xstate.js.org",
        "state-management,state-machine,statecharts,react,vue",
        "npm install xstate",
        "code",
    ),
    # Frontend — Vue state management -----------------------------------------------
    (
        "pinia",
        "Pinia",
        "The intuitive, type-safe store for Vue",
        "Pinia is the official state management library for Vue 3. Lightweight, "
        "devtools-friendly, and fully type-safe with Composition API. Replaces "
        "Vuex — simpler API, no mutations, modular stores, and SSR support.",
        "frontend-frameworks",
        "vuejs/pinia",
        13000,
        "https://pinia.vuejs.org",
        "state-management,vue,vuex-alternative,composition-api",
        "npm install pinia",
        "code",
    ),
    # Documentation — platforms ----------------------------------------------------
    (
        "mintlify",
        "Mintlify",
        "Beautiful documentation that converts — built for developer tools",
        "Mintlify generates beautiful, AI-powered documentation sites from your "
        "MDX files and OpenAPI specs. Built-in search, changelogs, API playground, "
        "and analytics. Used by Anthropic, Resend, Trigger.dev, and 1,000+ teams.",
        "documentation",
        "mintlify/mintlify",
        4000,
        "https://mintlify.com",
        "docs,api-docs,mdx,openapi,developer-experience",
        "npm install -g mintlify",
        "saas",
    ),
    # AI agent frameworks -----------------------------------------------------------
    (
        "mastra",
        "Mastra",
        "TypeScript AI agent framework — build, test, and deploy agents",
        "Mastra is an opinionated TypeScript framework for building AI agents and "
        "workflows. Built-in memory, tool calling, RAG pipelines, evals, and "
        "deployment. Works with any LLM provider via a unified API.",
        "ai-automation",
        "mastra-ai/mastra",
        9000,
        "https://mastra.ai",
        "ai,agent,typescript,workflows,rag",
        "npm install @mastra/core",
        "code",
    ),
    # Monitoring — session replay / full-stack observability -----------------------
    (
        "highlight",
        "Highlight.io",
        "Open-source full-stack monitoring — session replay, logs, errors, traces",
        "Highlight is an open-source monitoring platform combining session replay, "
        "error tracking, structured logging, and distributed tracing. "
        "Self-host or use Highlight Cloud. SDKs for React, Next.js, Python, Go, "
        "and more. Privacy-first with PII masking.",
        "monitoring-uptime",
        "highlight/highlight",
        7000,
        "https://highlight.io",
        "monitoring,session-replay,error-tracking,observability,open-source",
        "npm install @highlight-run/next",
        "code",
    ),
    # Frontend — cross-platform / mobile frameworks --------------------------------
    (
        "expo",
        "Expo",
        "Build one app for Android, iOS, and the web with React Native",
        "Expo is an open-source platform for making universal native apps with React. "
        "Includes a managed build service (EAS), 50+ packages for common native APIs, "
        "over-the-air updates, and a web runtime. The fastest way to ship a React Native app.",
        "frontend-frameworks",
        "expo/expo",
        38000,
        "https://expo.dev",
        "react-native,mobile,cross-platform,ios,android",
        "npx create-expo-app my-app",
        "code",
    ),
    (
        "flutter",
        "Flutter",
        "Build, test, and deploy beautiful mobile, web, desktop, and embedded apps",
        "Flutter is Google's UI toolkit for building natively compiled applications "
        "for mobile, web, desktop, and embedded devices from a single Dart codebase. "
        "Flutter 3 supports all six platforms with near-native performance.",
        "frontend-frameworks",
        "flutter/flutter",
        170000,
        "https://flutter.dev",
        "mobile,cross-platform,dart,ios,android,google",
        "flutter create my_app",
        "code",
    ),
    (
        "react-native",
        "React Native",
        "Learn once, write anywhere — build native mobile apps with React",
        "React Native lets you build mobile apps using React and JavaScript. "
        "Access native APIs, ship to iOS and Android from one codebase, and reuse "
        "web developer skills. Used by Meta, Microsoft, Shopify, and thousands of apps.",
        "frontend-frameworks",
        "facebook/react-native",
        119000,
        "https://reactnative.dev",
        "mobile,react,ios,android,cross-platform",
        "npx react-native init MyApp",
        "code",
    ),
    # Database — OLAP / analytical -------------------------------------------------
    (
        "duckdb",
        "DuckDB",
        "In-process SQL OLAP database — fast analytical queries on local files",
        "DuckDB is a fast, embedded analytical database. Run SQL directly on Parquet, "
        "CSV, or JSON files without a server. Perfect for data analysis, local ETL, "
        "and edge analytics. Runs in-process in Python, Node.js, Go, Rust, and Java.",
        "database",
        "duckdb/duckdb",
        30000,
        "https://duckdb.org",
        "olap,analytics,embedded,sql,parquet",
        "pip install duckdb",
        "code",
    ),
    # AI — structured output / validation tools ------------------------------------
    (
        "instructor",
        "Instructor",
        "Structured outputs from LLMs powered by Pydantic",
        "Instructor makes it easy to get structured data out of LLMs using Pydantic "
        "models as schemas. Works with OpenAI, Anthropic, Mistral, Cohere, and Gemini. "
        "Retry logic, partial streaming, and a clean Python API.",
        "ai-dev-tools",
        "instructor-ai/instructor",
        10000,
        "https://python.useinstructor.com",
        "llm,structured-output,pydantic,python",
        "pip install instructor",
        "code",
    ),
    # DevOps — Git hooks automation ------------------------------------------------
    (
        "husky",
        "Husky",
        "Git hooks made easy for Node.js projects",
        "Husky automatically installs and manages Git hooks for Node.js projects. "
        "Run linters, tests, or formatters on commit/push with zero configuration. "
        "Works with any Git hook and any linting tool.",
        "devops-infrastructure",
        "typicode/husky",
        33000,
        "https://typicode.github.io/husky",
        "git-hooks,linting,automation,ci",
        "npm install --save-dev husky",
        "code",
    ),
    # Feature flags ---------------------------------------------------------------
    (
        "unleash",
        "Unleash",
        "The open-source feature flag service",
        "Unleash is an enterprise-ready open-source feature flag management system. "
        "Run it self-hosted or use Unleash Cloud. Supports gradual rollouts, "
        "A/B experiments, and fine-grained strategy controls per environment.",
        "feature-flags",
        "Unleash/unleash",
        12000,
        "https://getunleash.io",
        "feature-flags,open-source,self-hosted,experimentation",
        "docker run unleashorg/unleash-server",
        "code",
    ),
    (
        "flagsmith",
        "Flagsmith",
        "Feature flags and remote config — open source",
        "Flagsmith lets you manage feature flags, remote config, and user segments "
        "across web, mobile, and server-side applications. Self-host with Docker "
        "or use the managed cloud — includes a REST API and official SDKs for 16+ languages.",
        "feature-flags",
        "Flagsmith/flagsmith",
        5000,
        "https://flagsmith.com",
        "feature-flags,remote-config,open-source,self-hosted",
        "pip install flagsmith",
        "code",
    ),
    # Documentation ---------------------------------------------------------------
    (
        "docusaurus",
        "Docusaurus",
        "Build optimised websites quickly, focus on your content",
        "Docusaurus is a static site generator powered by React and MDX. "
        "Used by Meta, Microsoft, Shopify, and thousands of open-source projects "
        "to build documentation sites, blogs, and versioned API references.",
        "documentation",
        "facebook/docusaurus",
        57000,
        "https://docusaurus.io",
        "docs,static-site,react,mdx,open-source",
        "npm init docusaurus@latest my-website classic",
        "code",
    ),
    (
        "scalar",
        "Scalar",
        "Beautiful API references from OpenAPI specs",
        "Scalar renders gorgeous, interactive API reference pages from your OpenAPI "
        "or Swagger spec. Supports request testing in-browser, multi-language code "
        "samples, and embeds in any stack — including Next.js, Hono, FastAPI, and more.",
        "documentation",
        "scalar/scalar",
        9000,
        "https://scalar.com",
        "api-docs,openapi,swagger,interactive,reference",
        "npm install @scalar/api-reference",
        "code",
    ),
    # Notifications ---------------------------------------------------------------
    (
        "knock",
        "Knock",
        "The notification infrastructure for developers",
        "Knock provides a complete notification infrastructure — multi-channel "
        "delivery (email, SMS, push, in-app), a drag-and-drop workflow builder, "
        "and a prebuilt notification inbox React component. No queuing infra to manage.",
        "notifications",
        "",
        0,
        "https://knock.app",
        "notifications,in-app,email,sms,push,saas",
        "npm install @knocklabs/node",
        "saas",
    ),
    # Monitoring — distributed tracing --------------------------------------------
    (
        "jaeger",
        "Jaeger",
        "Open-source distributed tracing for microservices",
        "Jaeger is an open-source distributed tracing system from Uber, now a CNCF "
        "graduated project. Monitor request flows across microservices, identify "
        "bottlenecks, and debug latency issues with a rich trace visualiser.",
        "monitoring-uptime",
        "jaegertracing/jaeger",
        20000,
        "https://jaegertracing.io",
        "tracing,distributed,opentelemetry,observability,cncf",
        "docker run jaegertracing/all-in-one",
        "code",
    ),
    (
        "zipkin",
        "Zipkin",
        "A distributed tracing system",
        "Zipkin is a distributed tracing system from Twitter (now open-source). "
        "It helps gather timing data to troubleshoot latency problems in "
        "service architectures. Supports multiple storage backends including "
        "Elasticsearch, Cassandra, and MySQL.",
        "monitoring-uptime",
        "openzipkin/zipkin",
        17000,
        "https://zipkin.io",
        "tracing,distributed,observability,latency",
        "docker run openzipkin/zipkin",
        "code",
    ),
    (
        "opentelemetry-js",
        "OpenTelemetry (JS)",
        "Vendor-neutral observability framework for JavaScript",
        "OpenTelemetry is the CNCF standard for telemetry — traces, metrics, and "
        "logs — with SDKs in 11+ languages. The JavaScript SDK instruments Node.js "
        "and browser apps and exports to any backend: Jaeger, Zipkin, Datadog, etc.",
        "monitoring-uptime",
        "open-telemetry/opentelemetry-js",
        3000,
        "https://opentelemetry.io",
        "otel,observability,tracing,metrics,logs,cncf",
        "npm install @opentelemetry/sdk-node",
        "code",
    ),
    # Frontend — React component libraries -------------------------------------------
    (
        "material-ui",
        "Material UI (MUI)",
        "React components based on Material Design",
        "MUI is the most popular React component library, providing a comprehensive "
        "suite of prebuilt components implementing Google's Material Design. "
        "Used in over 3 million projects, it includes a free core library (Joy UI), "
        "data grid, date pickers, and MUI X premium components.",
        "frontend-frameworks",
        "mui/material-ui",
        93000,
        "https://mui.com",
        "react,ui,material-design,components,design-system",
        "npm install @mui/material @emotion/react @emotion/styled",
        "code",
    ),
    (
        "mantine",
        "Mantine",
        "A fully featured React component library",
        "Mantine is a React component library with 100+ components and 50+ hooks. "
        "Ships with built-in dark mode, form management, date pickers, rich text "
        "editor, notifications, modals, and full TypeScript support. Zero-config "
        "theming with CSS variables.",
        "frontend-frameworks",
        "mantinedev/mantine",
        26000,
        "https://mantine.dev",
        "react,ui,components,dark-mode,hooks,typescript",
        "npm install @mantine/core @mantine/hooks",
        "code",
    ),
    (
        "ant-design",
        "Ant Design",
        "An enterprise-class UI design language and React UI library",
        "Ant Design is a comprehensive React UI library created by Alibaba/Ant Group. "
        "The de-facto standard for enterprise React UIs in China and widely used globally. "
        "Provides 60+ components, a design system, charts (AntV), and mobile support.",
        "frontend-frameworks",
        "ant-design/ant-design",
        93000,
        "https://ant.design",
        "react,ui,enterprise,components,design-system,alibaba",
        "npm install antd",
        "code",
    ),
    (
        "chakra-ui",
        "Chakra UI",
        "Simple, modular and accessible component library for React",
        "Chakra UI gives you the building blocks to build accessible React apps with "
        "speed. Every component follows WAI-ARIA guidelines, supports dark mode out "
        "of the box, and is fully composable. Chakra v3 is built on Ark UI with "
        "improved performance and RSC support.",
        "frontend-frameworks",
        "chakra-ui/chakra-ui",
        37000,
        "https://chakra-ui.com",
        "react,ui,accessibility,dark-mode,composable,components",
        "npm install @chakra-ui/react",
        "code",
    ),
    # AI — LLM observability ---------------------------------------------------------
    (
        "langfuse",
        "Langfuse",
        "Open-source LLM observability, evals, and prompt management",
        "Langfuse is the open-source LLM engineering platform. Trace LLM calls, "
        "evaluate outputs, manage prompts, and run A/B experiments across OpenAI, "
        "Anthropic, LangChain, LlamaIndex, and any custom model. Self-host or use "
        "Langfuse Cloud.",
        "ai-dev-tools",
        "langfuse/langfuse",
        8000,
        "https://langfuse.com",
        "llm,observability,tracing,evals,prompt-management,open-source",
        "pip install langfuse",
        "code",
    ),
    # Analytics — charting / data visualisation --------------------------------------
    (
        "recharts",
        "Recharts",
        "Redefined chart library built with React and D3",
        "Recharts is a composable charting library built with React components and D3. "
        "Supports line, bar, area, pie, radar, scatter, and composed charts. "
        "Declarative API makes charts easy to customize; works with any React app "
        "or data source.",
        "analytics-metrics",
        "recharts/recharts",
        23000,
        "https://recharts.org",
        "react,charts,d3,data-visualization,components",
        "npm install recharts",
        "code",
    ),
    # Email — missing major providers -----------------------------------------
    (
        "brevo",
        "Brevo",
        "Email marketing and transactional email for growing businesses",
        "Brevo (formerly Sendinblue) is an all-in-one email platform trusted by "
        "500,000+ businesses. Send transactional emails, newsletters, and SMS. "
        "Includes marketing automation, CRM, and a generous free tier.",
        "email-marketing",
        None,
        0,
        "https://brevo.com",
        "email,transactional,newsletter,marketing,smtp",
        "npm install @getbrevo/brevo",
        "saas",
    ),
    (
        "loops",
        "Loops",
        "Email for modern SaaS companies",
        "Loops is an email platform built for SaaS products. Send product emails, "
        "onboarding sequences, and newsletters from one place. Beautiful editor, "
        "contact management, and dead-simple API for transactional sends.",
        "email-marketing",
        "loops-so/loops",
        3500,
        "https://loops.so",
        "email,transactional,saas,onboarding,newsletter",
        "npm install loops",
        "saas",
    ),
    (
        "plunk",
        "Plunk",
        "The open-source email platform built on AWS SES",
        "Plunk is an open-source transactional email service built on top of AWS SES. "
        "Self-host for near-zero cost or use the hosted version. Clean REST API, "
        "event tracking, and contact management included.",
        "email-marketing",
        "useplunk/plunk",
        3200,
        "https://useplunk.com",
        "email,transactional,open-source,aws-ses,self-hosted",
        "npm install @plunk/node",
        "code",
    ),
    # Frontend — animation libraries -------------------------------------------
    (
        "react-spring",
        "React Spring",
        "A spring-physics based animation library for React",
        "React Spring is a physics-based animation library for React. Uses spring "
        "dynamics (tension, friction, mass) instead of durations for naturally "
        "fluid animations. Supports web, React Native, Three.js, and Konva.",
        "frontend-frameworks",
        "pmndrs/react-spring",
        28000,
        "https://react-spring.dev",
        "animation,react,spring,physics",
        "npm install @react-spring/web",
        "code",
    ),
    # Frontend — data grids ----------------------------------------------------
    (
        "ag-grid",
        "AG Grid",
        "The best JavaScript data grid in the world",
        "AG Grid is the most feature-complete JavaScript data grid available. "
        "Handles millions of rows with virtual rendering. Free community edition "
        "plus enterprise version with pivoting, row grouping, and Excel export.",
        "frontend-frameworks",
        "ag-grid/ag-grid",
        12000,
        "https://ag-grid.com",
        "datagrid,table,react,angular,vue,spreadsheet,excel",
        "npm install ag-grid-community ag-grid-react",
        "code",
    ),
    # Frontend — accessible headless UI ----------------------------------------
    (
        "headlessui",
        "Headless UI",
        "Completely unstyled, fully accessible UI components",
        "Headless UI provides completely unstyled, fully accessible UI components "
        "designed to integrate with Tailwind CSS. Built by the Tailwind Labs team. "
        "Includes Dialog, Listbox, Combobox, Disclosure, Menu, and more.",
        "frontend-frameworks",
        "tailwindlabs/headlessui",
        24000,
        "https://headlessui.com",
        "ui,react,vue,accessibility,headless,tailwind",
        "npm install @headlessui/react",
        "code",
    ),
    (
        "react-aria",
        "React Aria",
        "A library of React Hooks for accessible UI primitives",
        "React Aria (by Adobe) provides over 40 React Hooks for building accessible "
        "UI components. Implements ARIA patterns with full keyboard, screen reader, "
        "and touch support. Foundation for Adobe's React Spectrum design system.",
        "frontend-frameworks",
        "adobe/react-spectrum",
        12000,
        "https://react-spectrum.adobe.com/react-aria",
        "ui,react,accessibility,headless,hooks,adobe",
        "npm install react-aria",
        "code",
    ),
    # Developer Tools — date/time utilities ------------------------------------
    (
        "date-fns",
        "date-fns",
        "Modern JavaScript date utility library",
        "date-fns provides the most comprehensive, yet simple and consistent "
        "toolset for manipulating JavaScript dates in a browser and Node.js. "
        "Tree-shakeable, immutable, and fully typed. 200+ functions.",
        "developer-tools",
        "date-fns/date-fns",
        34000,
        "https://date-fns.org",
        "date,time,utility,javascript,typescript,immutable",
        "npm install date-fns",
        "code",
    ),
    # Frontend — tooltip/popover positioning -----------------------------------
    (
        "floating-ui",
        "Floating UI",
        "Low-level library for positioning floating elements",
        "Floating UI is a low-level library for positioning floating elements "
        "like tooltips, popovers, dropdowns, and menus. Works with React, Vue, "
        "Angular, and vanilla JS. Successor to Popper.js with better performance "
        "and floating element interaction support.",
        "frontend-frameworks",
        "floating-ui/floating-ui",
        29000,
        "https://floating-ui.com",
        "tooltip,popover,dropdown,positioning,react,vue,angular",
        "npm install @floating-ui/react",
        "code",
    ),
    # Frontend — icon libraries ------------------------------------------------
    (
        "iconify",
        "Iconify",
        "Unified icon framework with 200k+ open-source icons",
        "Iconify is a unified icon framework that provides access to over 200,000 "
        "icons from 100+ icon sets (Material, Tabler, Phosphor, Heroicons, and more) "
        "through a single, consistent API. Works with React, Vue, Svelte, and CSS.",
        "frontend-frameworks",
        "iconify/iconify",
        4000,
        "https://iconify.design",
        "icons,svg,react,vue,svelte,design-system",
        "npm install @iconify/react",
        "code",
    ),
    (
        "svgr",
        "SVGR",
        "Transform SVG into React components",
        "SVGR transforms SVG files into ready-to-use React components. Works as "
        "a CLI, webpack loader, Vite plugin, and programmatic API. Powers "
        "Create React App and is widely used in design system pipelines to "
        "auto-generate accessible icon components from SVG source files.",
        "frontend-frameworks",
        "gregberge/svgr",
        10000,
        "https://react-svgr.com",
        "svg,react,icons,build-tool,transform",
        "npm install @svgr/webpack",
        "code",
    ),
    # API Tools — HTTP clients -------------------------------------------------
    (
        "hoppscotch",
        "Hoppscotch",
        "Open-source API development ecosystem",
        "Hoppscotch is an open-source, lightning-fast API development ecosystem "
        "and Postman alternative. Test REST, GraphQL, WebSocket, SSE, and Socket.IO "
        "APIs directly in the browser or desktop app. Supports team workspaces, "
        "environments, and self-hosting.",
        "api-tools",
        "hoppscotch/hoppscotch",
        66000,
        "https://hoppscotch.io",
        "api,rest,graphql,websocket,postman-alternative,open-source",
        "npx @hoppscotch/cli test",
        "code",
    ),
    (
        "httpie",
        "HTTPie",
        "Human-friendly HTTP client for the API era",
        "HTTPie is a command-line HTTP client designed for testing, debugging, "
        "and interacting with APIs and web servers. Features a simple syntax, "
        "automatic JSON support, syntax highlighting, and session persistence. "
        "Available as CLI, desktop app, and web client.",
        "api-tools",
        "httpie/cli",
        34000,
        "https://httpie.io",
        "api,http,rest,cli,curl-alternative,testing",
        "brew install httpie",
        "code",
    ),
    # Database — serverless Postgres + search ----------------------------------
    (
        "xata",
        "Xata",
        "Serverless database with built-in search and branching",
        "Xata is a serverless Postgres database with built-in full-text search, "
        "vector search, and database branching (like git branches for your schema). "
        "Zero-downtime migrations, TypeScript SDK, and a visual data editor. "
        "Ideal for Next.js and serverless apps.",
        "database",
        "xataio/client-ts",
        1000,
        "https://xata.io",
        "database,postgres,search,serverless,branching,typescript",
        "npm install @xata.io/client",
        "saas",
    ),
    # CMS — Git-based content management ---------------------------------------
    (
        "keystatic",
        "Keystatic",
        "Git-based CMS that works with your codebase",
        "Keystatic is a CMS that stores content directly in your Git repository "
        "as Markdown, JSON, or YAML files. No external database — content lives "
        "alongside your code. Built by Thinkmill, designed for Astro, Next.js, "
        "and Remix projects. Open-source and self-hostable.",
        "headless-cms",
        "Thinkmill/keystatic",
        2000,
        "https://keystatic.com",
        "cms,git,markdown,astro,nextjs,open-source,content",
        "npm install @keystatic/core",
        "code",
    ),
    # DevOps — self-hosted PaaS ------------------------------------------------
    (
        "dokku",
        "Dokku",
        "Self-hosted Heroku-compatible PaaS in under 1MB",
        "Dokku is the smallest PaaS implementation you've ever seen — a self-hosted "
        "Heroku alternative built on Docker. Push your code to deploy (git push dokku "
        "main), with built-in buildpacks, SSL via Let's Encrypt, datastore plugins "
        "for Postgres/Redis/MySQL, and reverse proxy via nginx.",
        "devops-infrastructure",
        "dokku/dokku",
        27000,
        "https://dokku.com",
        "paas,heroku-alternative,docker,self-hosted,deployment,git",
        "wget -NqO- https://packagecloud.io/dokku/dokku/gpgkey | sudo apt-key add -",
        "code",
    ),
    (
        "caprover",
        "CapRover",
        "Build your own Heroku in 5 minutes",
        "CapRover is a free and open-source PaaS (Platform as a Service) that "
        "lets you deploy apps using Docker and a simple CLI or web UI. Supports "
        "one-click apps (Postgres, Redis, MongoDB, WordPress, Strapi), SSL, "
        "load balancing, and webhooks for CI/CD pipelines.",
        "devops-infrastructure",
        "caprover/caprover",
        13000,
        "https://caprover.com",
        "paas,docker,self-hosted,heroku-alternative,deployment",
        "npm install -g caprover",
        "code",
    ),
    # Frontend — Inertia.js (SPA for Laravel/Rails) ----------------------------
    (
        "inertiajs",
        "Inertia.js",
        "Build modern single-page apps using classic server-side routing",
        "Inertia.js lets you build modern SPAs using classic server-side routing "
        "and controllers — no separate API needed. Works with Laravel, Rails, and "
        "Django backends. Your server returns components instead of JSON, and "
        "Inertia handles the client-side routing seamlessly.",
        "frontend-frameworks",
        "inertiajs/inertia",
        6000,
        "https://inertiajs.com",
        "laravel,rails,spa,routing,react,vue,svelte",
        "npm install @inertiajs/react",
        "code",
    ),
    # Developer Tools — full-stack framework -----------------------------------
    (
        "wasp",
        "Wasp",
        "The fastest way to build full-stack React + Node.js apps",
        "Wasp is a declarative full-stack web framework for React and Node.js. "
        "It handles auth, routing, deployments, and database migrations via a "
        "simple config file — think Rails for the React/Node ecosystem. Deploy "
        "to any cloud with one command. Open-source, MIT licensed.",
        "developer-tools",
        "wasp-lang/wasp",
        14000,
        "https://wasp-lang.dev",
        "fullstack,react,nodejs,auth,prisma,deployment,rails-alternative",
        "curl -sSL https://get.wasp-lang.dev/installer.sh | sh",
        "code",
    ),
    # Static Site Generators ---------------------------------------------------
    (
        "hugo",
        "Hugo",
        "The world's fastest framework for building websites",
        "Hugo is an open-source static site generator written in Go. It builds "
        "sites from Markdown and templates in milliseconds, with no runtime "
        "dependencies. Powers millions of sites including documentation, portfolios, "
        "and blogs. Supports themes, shortcodes, multilingual content, and "
        "taxonomies out of the box.",
        "frontend-frameworks",
        "gohugoio/hugo",
        72000,
        "https://gohugo.io",
        "ssg,static-site,go,blog,documentation,fast",
        "brew install hugo",
        "code",
    ),
    (
        "jekyll",
        "Jekyll",
        "Transform your plain text into static websites and blogs",
        "Jekyll is the original static site generator, written in Ruby and "
        "powering GitHub Pages. It converts Markdown, Liquid templates, and "
        "YAML front matter into static HTML. Simple, blog-aware, with a rich "
        "ecosystem of themes and plugins. Zero databases, zero configuration "
        "required to get started.",
        "frontend-frameworks",
        "jekyll/jekyll",
        48000,
        "https://jekyllrb.com",
        "ssg,static-site,ruby,blog,github-pages",
        "gem install jekyll bundler",
        "code",
    ),
    (
        "eleventy",
        "Eleventy (11ty)",
        "A simpler static site generator",
        "Eleventy is a simpler static site generator that works with multiple "
        "template languages (Markdown, Nunjucks, Liquid, Handlebars, JavaScript, "
        "and more). Zero client-side JavaScript by default. Extremely fast builds, "
        "flexible project structure, and no framework lock-in. Used by Google, "
        "ESLint, and the Web Almanac.",
        "frontend-frameworks",
        "11ty/eleventy",
        17000,
        "https://www.11ty.dev",
        "ssg,static-site,javascript,multi-template,blog,fast",
        "npm install @11ty/eleventy",
        "code",
    ),
    (
        "gatsby",
        "Gatsby",
        "The fastest frontend for the headless web",
        "Gatsby is a React-based open-source static site generator and web "
        "framework. It pulls data from any source (CMS, APIs, databases, files) "
        "via GraphQL and builds blazing-fast static HTML. Features image "
        "optimization, code splitting, prefetching, and a rich plugin ecosystem "
        "with 3,000+ plugins.",
        "frontend-frameworks",
        "gatsbyjs/gatsby",
        55000,
        "https://www.gatsbyjs.com",
        "ssg,static-site,react,graphql,image-optimization,pwa",
        "npm install gatsby",
        "code",
    ),
    # Developer Tools — diagramming --------------------------------------------
    (
        "mermaid",
        "Mermaid",
        "Diagramming and charting tool that renders text definitions",
        "Mermaid is a JavaScript-based diagramming and charting tool that renders "
        "Markdown-inspired text definitions to create diagrams. Supports flowcharts, "
        "sequence diagrams, class diagrams, ER diagrams, Gantt charts, and more. "
        "Natively supported in GitHub, GitLab, Notion, and Obsidian. Used to keep "
        "docs in sync with code.",
        "developer-tools",
        "mermaid-js/mermaid",
        72000,
        "https://mermaid.js.org",
        "diagrams,uml,flowchart,markdown,documentation,visualization",
        "npm install mermaid",
        "code",
    ),
    # Testing Tools — linting + formatting ------------------------------------
    (
        "biome",
        "Biome",
        "One toolchain for your web project",
        "Biome is a fast formatter and linter for JavaScript, TypeScript, JSX, "
        "TSX, JSON, CSS, and GraphQL. Written in Rust, it's 35x faster than "
        "Prettier and 15x faster than ESLint. A single unified tool that replaces "
        "Prettier + ESLint with zero configuration needed. Drop-in Prettier "
        "compatible with a migration CLI.",
        "testing-tools",
        "biomejs/biome",
        14000,
        "https://biomejs.dev",
        "linter,formatter,rust,fast,javascript,typescript,prettier-alternative",
        "npm install --save-dev --save-exact @biomejs/biome",
        "code",
    ),
    # Games & Entertainment ---------------------------------------------------
    (
        "godot",
        "Godot Engine",
        "The free and open source game engine",
        "Godot Engine is a feature-packed, cross-platform game engine designed "
        "to create 2D and 3D games from a unified interface. It provides a "
        "comprehensive set of tools so you can focus on making games. Uses "
        "GDScript (Python-like), C#, and C++ as scripting languages. Fully "
        "free and open-source with MIT license.",
        "games-entertainment",
        "godotengine/godot",
        90000,
        "https://godotengine.org",
        "game-engine,2d,3d,gdscript,cross-platform,mit,open-source",
        "",
        "code",
    ),
    (
        "phaser",
        "Phaser",
        "A fast, fun and free open source HTML5 game framework",
        "Phaser is a fast 2D game framework for HTML5 using WebGL and Canvas "
        "rendering. It supports physics (Arcade, Matter.js, Impact), tweens, "
        "particles, tilemaps, and game input. Used by thousands of indie games, "
        "educational platforms, and browser-based apps. Works with TypeScript "
        "and has an active community.",
        "games-entertainment",
        "photonstorm/phaser",
        36000,
        "https://phaser.io",
        "game-framework,html5,webgl,canvas,javascript,2d,physics",
        "npm install phaser",
        "code",
    ),
    # Developer Tools — browser extension frameworks --------------------------
    (
        "wxt",
        "WXT",
        "Next-gen web extension framework",
        "WXT is a framework for building browser extensions with a Next.js-like "
        "developer experience. Supports Chrome, Firefox, Edge, and Safari. File-based "
        "entrypoints, HMR during development, automatic manifest generation, and "
        "TypeScript-first. The fastest way to build cross-browser extensions.",
        "developer-tools",
        "wxt-dev/wxt",
        5000,
        "https://wxt.dev",
        "browser-extension,chrome-extension,firefox,manifest-v3,typescript,hmr",
        "npm create wxt@latest",
        "code",
    ),
    (
        "plasmo",
        "Plasmo",
        "The browser extension framework",
        "Plasmo is a battery-packed framework for building browser extensions "
        "with React. Features a declarative API, built-in HMR, content scripts "
        "with React, automatic manifest generation, and first-class TypeScript "
        "support. Deploy to the Chrome Web Store and Firefox Add-ons with one "
        "CLI command. Used by thousands of extension developers.",
        "developer-tools",
        "PlasmoHQ/plasmo",
        10000,
        "https://www.plasmo.com",
        "browser-extension,chrome-extension,react,manifest-v3,typescript",
        "npm create plasmo@latest",
        "code",
    ),
    # Frontend — rich text / code editors in the browser --------------------------
    (
        "tiptap",
        "Tiptap",
        "The headless, framework-agnostic rich text editor",
        "Tiptap is a headless, fully customisable rich text editor built on "
        "ProseMirror. Works with React, Vue, and Svelte. Collaborative editing "
        "via Y.js, 50+ extensions, a low-level API for custom nodes/marks, "
        "and a cloud offering for collaboration and comments.",
        "frontend-frameworks",
        "ueberdosis/tiptap",
        28000,
        "https://tiptap.dev",
        "rich-text-editor,wysiwyg,prosemirror,react,vue,collaboration",
        "npm install @tiptap/react @tiptap/pm @tiptap/starter-kit",
        "code",
    ),
    (
        "codemirror",
        "CodeMirror",
        "A versatile code editor component for the web",
        "CodeMirror 6 is a modular, browser-based code editor toolkit. "
        "Powers the editor in Firefox DevTools, Repl.it, Glitch, and "
        "many browser-based IDEs. Supports 100+ languages with syntax "
        "highlighting, autocomplete, linting, and collaborative editing via Y.js.",
        "frontend-frameworks",
        "codemirror/codemirror5",
        26000,
        "https://codemirror.net",
        "code-editor,syntax-highlighting,browser,react,collaborative",
        "npm install codemirror",
        "code",
    ),
    # Python — data validation & type checking ------------------------------------
    (
        "pydantic",
        "Pydantic",
        "Data validation using Python type annotations",
        "Pydantic is the most widely used Python data validation library. "
        "Define schemas as Python classes with type hints — validation, "
        "serialization, and IDE autocompletion included. Foundation of "
        "FastAPI's request/response models. Pydantic v2 is written in Rust "
        "for 5-50× faster validation.",
        "developer-tools",
        "pydantic/pydantic",
        21000,
        "https://docs.pydantic.dev",
        "python,validation,schema,fastapi,type-hints,serialization",
        "pip install pydantic",
        "code",
    ),
    # Python — linting + testing ------------------------------------------------
    (
        "ruff",
        "Ruff",
        "An extremely fast Python linter and formatter, written in Rust",
        "Ruff is a blazing-fast Python linter and code formatter written in Rust. "
        "10-100× faster than Flake8, Pylint, isort, and Black. Replaces up to "
        "12 Python tools with a single binary. Over 800 lint rules, auto-fix "
        "support, and drop-in compatibility with Black formatting.",
        "testing-tools",
        "astral-sh/ruff",
        35000,
        "https://docs.astral.sh/ruff",
        "python,linter,formatter,rust,fast,flake8-alternative",
        "pip install ruff",
        "code",
    ),
    (
        "pytest",
        "pytest",
        "Makes it easy to write small tests, scales to support complex functional testing",
        "pytest is the most popular Python testing framework. Write tests as "
        "simple functions, leverage powerful fixtures for setup/teardown, "
        "use parametrize for data-driven tests, and benefit from a rich "
        "ecosystem of 1,000+ plugins (pytest-asyncio, pytest-django, pytest-cov).",
        "testing-tools",
        "pytest-dev/pytest",
        12000,
        "https://pytest.org",
        "python,testing,fixtures,parametrize,unit-test,e2e",
        "pip install pytest",
        "code",
    ),
    # Python — ASGI server -------------------------------------------------------
    (
        "uvicorn",
        "Uvicorn",
        "An ASGI web server implementation for Python",
        "Uvicorn is a lightning-fast ASGI server implementation for Python, "
        "built on uvloop and httptools. The standard production server for "
        "FastAPI and Starlette applications. Supports HTTP/1.1, WebSockets, "
        "and lifespan protocol. Workers mode for multi-process deployments.",
        "api-tools",
        "encode/uvicorn",
        8000,
        "https://www.uvicorn.org",
        "python,asgi,fastapi,starlette,server,production",
        "pip install uvicorn",
        "code",
    ),
    # DevOps — process manager --------------------------------------------------
    (
        "pm2",
        "PM2",
        "Production process manager for Node.js applications",
        "PM2 is the most popular Node.js process manager for production. "
        "Keep apps alive forever, reload without downtime, and manage "
        "application logs. Built-in load balancer, startup scripts, and "
        "a monitoring dashboard. Used by thousands of production Node.js deployments.",
        "devops-infrastructure",
        "Unitech/pm2",
        42000,
        "https://pm2.keymetrics.io",
        "nodejs,process-manager,deployment,production,clustering,logs",
        "npm install pm2 -g",
        "code",
    ),
    # Analytics & BI Tools -------------------------------------------------------
    (
        "metabase",
        "Metabase",
        "The simplest, fastest way to get business intelligence and analytics",
        "Metabase is an open-source business intelligence tool that lets anyone "
        "in your company ask questions and learn from data — no SQL required for "
        "basic use. Supports 20+ databases, rich visualisations, and self-hosted "
        "or cloud deployment. One of the most-starred OSS BI tools at 38k+ stars.",
        "analytics-metrics",
        "metabase/metabase",
        38000,
        "https://www.metabase.com",
        "bi,analytics,dashboards,sql,open-source,self-hosted",
        "docker run -d -p 3000:3000 metabase/metabase",
        "code",
    ),
    (
        "redash",
        "Redash",
        "Connect to any data source and build beautiful dashboards",
        "Redash is an open-source tool for teams to query, visualise, and share "
        "data. Write SQL (or use drag-and-drop query builders) against 35+ data "
        "sources, create charts and dashboards, and schedule automatic refresh. "
        "Over 26k stars; used by thousands of teams worldwide.",
        "analytics-metrics",
        "getredash/redash",
        26000,
        "https://redash.io",
        "bi,analytics,dashboards,sql,visualisation,self-hosted",
        "docker-compose up -d",
        "code",
    ),
    (
        "superset",
        "Apache Superset",
        "A modern, enterprise-ready business intelligence web application",
        "Apache Superset is a fast, lightweight, intuitive, and loaded with "
        "options that make it easy for users of all skill sets to explore and "
        "visualize their data, from simple line charts to highly detailed "
        "geospatial charts. One of the top OSS BI tools with 62k+ GitHub stars.",
        "analytics-metrics",
        "apache/superset",
        62000,
        "https://superset.apache.org",
        "bi,analytics,dashboards,sql,visualization,apache,self-hosted",
        "pip install apache-superset",
        "code",
    ),
    (
        "lightdash",
        "Lightdash",
        "The open source alternative to Looker",
        "Lightdash is an open-source BI tool built for dbt users. Define metrics "
        "in your dbt project YAML and Lightdash auto-generates an analytics layer "
        "on top — no duplicate metric definitions. Works with Postgres, BigQuery, "
        "Snowflake, Databricks and more. 9k+ GitHub stars.",
        "analytics-metrics",
        "lightdash-ai/lightdash",
        9000,
        "https://www.lightdash.com",
        "bi,analytics,dbt,metrics,dashboards,open-source,looker-alternative",
        "pip install lightdash",
        "code",
    ),
    (
        "evidence",
        "Evidence",
        "Build fast, interactive data apps with SQL and Markdown",
        "Evidence lets you write SQL queries and Markdown to build beautiful "
        "data reports and apps that run entirely in the browser. Perfect for "
        "analyst teams who want version-controlled, code-first BI. Supports "
        "DuckDB, BigQuery, Snowflake, Postgres, and more.",
        "analytics-metrics",
        "evidence-dev/evidence",
        5000,
        "https://evidence.dev",
        "bi,analytics,sql,markdown,duckdb,code-first,reporting",
        "npm create evidence-app@latest",
        "code",
    ),
    # DevOps — Database backup & replication -------------------------------------
    (
        "litestream",
        "Litestream",
        "Continuous replication for SQLite",
        "Litestream is a standalone disaster recovery tool for SQLite. It runs as "
        "a background process and continuously streams SQLite changes to Amazon S3, "
        "Google Cloud Storage, or Azure Blob Storage — making SQLite viable for "
        "production with near-zero RPO. Written in Go; 10k+ stars.",
        "devops-infrastructure",
        "benbjohnson/litestream",
        10000,
        "https://litestream.io",
        "sqlite,replication,backup,disaster-recovery,s3,gcs,azure",
        "brew install litestream",
        "code",
    ),
    # Caching — Redis-compatible alternatives + classic --------------------------------
    (
        "valkey",
        "Valkey",
        "Open-source, Redis-compatible in-memory data store",
        "Valkey is an open-source fork of Redis maintained by the Linux Foundation. "
        "100% compatible with Redis 7.2 commands and clients, including Sentinel and Cluster "
        "modes. Created in response to Redis Ltd's licence change; backed by AWS, Google, "
        "Oracle, Ericsson, and the broader open-source community. Drop-in replacement.",
        "caching",
        "valkey-io/valkey",
        18000,
        "https://valkey.io",
        "redis,cache,in-memory,open-source,linux-foundation,drop-in",
        "docker run -d --name valkey -p 6379:6379 valkey/valkey",
        "code",
    ),
    (
        "memcached",
        "Memcached",
        "High-performance, distributed memory object caching system",
        "Memcached is a battle-tested, high-performance, distributed in-memory caching system. "
        "Simple key-value store focused purely on caching: no persistence, no pub/sub, no data "
        "structures. Sub-millisecond latency at scale. Used by Wikipedia, YouTube, Facebook, "
        "and thousands of production systems for over 20 years.",
        "caching",
        "memcached/memcached",
        14000,
        "https://memcached.org",
        "cache,in-memory,distributed,key-value,classic",
        "docker run -d --name memcached -p 11211:11211 memcached",
        "code",
    ),
    (
        "keydb",
        "KeyDB",
        "High-performance, multi-threaded Redis fork",
        "KeyDB is a fully Redis-compatible, multi-threaded database. By using multiple threads, "
        "KeyDB achieves 5× higher throughput than Redis on the same hardware. Supports all "
        "Redis data types, commands, modules, and replication. Flash storage tier for "
        "cost-effective large datasets. Open-source core; hosted on Snap.",
        "caching",
        "Snapchat/KeyDB",
        7000,
        "https://docs.keydb.dev",
        "redis,cache,in-memory,multi-threaded,performance",
        "docker run --name keydb -p 6379:6379 eqalpha/keydb",
        "code",
    ),
    # Caching — the canonical in-memory store --------------------------------------
    (
        "redis",
        "Redis",
        "The open source, in-memory data structure store",
        "Redis is the world's most popular in-memory key-value store. Used for "
        "caching, session management, pub/sub messaging, leaderboards, and queues. "
        "Supports strings, hashes, lists, sets, sorted sets, streams, and more. "
        "Foundation for Upstash, Dragonfly, Valkey, and dozens of Redis-compatible tools.",
        "caching",
        "redis/redis",
        65000,
        "https://redis.io",
        "cache,key-value,in-memory,pub-sub,sessions",
        "docker run -d -p 6379:6379 redis",
        "code",
    ),
    # Testing / Code Quality — formatters and linters ------------------------------
    (
        "prettier",
        "Prettier",
        "An opinionated code formatter",
        "Prettier is the most widely used JavaScript/TypeScript code formatter. "
        "Supports JS, TS, CSS, HTML, JSON, Markdown, GraphQL, and more. "
        "Zero config to get started; eliminates style debates in PRs. "
        "Integrates with ESLint, editors, and CI pipelines. 48k+ GitHub stars.",
        "testing-tools",
        "prettier/prettier",
        48000,
        "https://prettier.io",
        "formatter,javascript,typescript,css,code-quality",
        "npm install --save-dev prettier",
        "code",
    ),
    (
        "eslint",
        "ESLint",
        "Find and fix problems in your JavaScript code",
        "ESLint is the dominant JavaScript and TypeScript linting tool. Statically "
        "analyses code to find problems: bugs, anti-patterns, and style violations. "
        "Highly configurable via plugins (eslint-config-airbnb, typescript-eslint, "
        "eslint-plugin-react). Used in virtually every serious JS/TS project. 24k+ stars.",
        "testing-tools",
        "eslint/eslint",
        24000,
        "https://eslint.org",
        "linting,javascript,typescript,code-quality,static-analysis",
        "npm install eslint --save-dev",
        "code",
    ),
    # Developer Tools — schema validation ------------------------------------------
    (
        "valibot",
        "Valibot",
        "The modular and type-safe schema library for validating structural data",
        "Valibot is a modular schema validation library for TypeScript — a lightweight "
        "alternative to Zod. Tree-shakeable bundle under 1KB for most schemas. "
        "Same API shape as Zod with a cleaner functional architecture. "
        "Ideal for edge functions, Cloudflare Workers, and bundle-size-sensitive apps.",
        "developer-tools",
        "fabian-hiller/valibot",
        7000,
        "https://valibot.dev",
        "validation,typescript,schema,zod-alternative,modular",
        "npm install valibot",
        "code",
    ),
    # Database — Python ORM / SQL toolkit -------------------------------------------
    (
        "sqlalchemy",
        "SQLAlchemy",
        "The Python SQL Toolkit and Object Relational Mapper",
        "SQLAlchemy is the most widely used Python SQL toolkit and ORM. Provides "
        "a full-featured ORM with unit-of-work pattern, an expressive Core SQL "
        "expression language, and dialect support for PostgreSQL, MySQL, SQLite, "
        "Oracle, and MS SQL. Foundation for FastAPI + Alembic + many Python web apps.",
        "database",
        "sqlalchemy/sqlalchemy",
        9000,
        "https://sqlalchemy.org",
        "orm,python,sql,postgresql,mysql,sqlite,alembic",
        "pip install sqlalchemy",
        "code",
    ),
    # Monitoring — Prometheus + Grafana (canonical open-source observability stack) ----
    (
        "prometheus",
        "Prometheus",
        "Open-source monitoring and alerting toolkit",
        "Prometheus is the most widely adopted open-source monitoring system. Pull-based "
        "metrics collection, a powerful query language (PromQL), built-in alerting via "
        "Alertmanager, and native Kubernetes support. Foundation of the CNCF observability stack.",
        "monitoring-uptime",
        "prometheus/prometheus",
        52000,
        "https://prometheus.io",
        "monitoring,metrics,alerting,cncf,kubernetes",
        "docker run -p 9090:9090 prom/prometheus",
        "code",
    ),
    (
        "grafana",
        "Grafana",
        "Open-source observability and data visualization platform",
        "Grafana is the leading open-source platform for monitoring, observability, and data "
        "visualization. Connects to Prometheus, Loki, InfluxDB, PostgreSQL, and 100+ data "
        "sources. Build dashboards, set alerts, and explore metrics, logs, and traces.",
        "monitoring-uptime",
        "grafana/grafana",
        64000,
        "https://grafana.com",
        "monitoring,dashboards,visualization,metrics,observability",
        "docker run -d -p 3000:3000 grafana/grafana",
        "code",
    ),
    # File Storage — MinIO (self-hosted S3-compatible object storage) -------------------
    (
        "minio",
        "MinIO",
        "High-performance, S3-compatible object storage",
        "MinIO is the world's most widely deployed object storage. S3-compatible API, "
        "single binary deployment, Kubernetes-native, and capable of storing photos, "
        "videos, log files, backups, and container images. Runs anywhere.",
        "file-management",
        "minio/minio",
        47000,
        "https://min.io",
        "s3,object-storage,self-hosted,kubernetes",
        "docker run -p 9000:9000 -p 9001:9001 quay.io/minio/minio server /data --console-address ':9001'",
        "code",
    ),
    # DevOps — web servers and reverse proxies -----------------------------------------
    (
        "caddy",
        "Caddy",
        "The web server with automatic HTTPS",
        "Caddy is a powerful, enterprise-ready, open-source web server with automatic HTTPS "
        "by default. Written in Go, it handles TLS certificate renewal via Let's Encrypt, "
        "reverse proxying, static file serving, and load balancing — zero config required.",
        "devops-infrastructure",
        "caddyserver/caddy",
        57000,
        "https://caddyserver.com",
        "web-server,reverse-proxy,https,lets-encrypt,go",
        "docker run -p 80:80 -p 443:443 caddy",
        "code",
    ),
    (
        "nginx",
        "Nginx",
        "High-performance web server and reverse proxy",
        "Nginx (pronounced 'engine-x') is the world's most used web server. Handles static "
        "files, reverse proxying, load balancing, TLS termination, and HTTP caching with "
        "exceptional performance and a small memory footprint.",
        "devops-infrastructure",
        "nginx/nginx",
        20000,
        "https://nginx.org",
        "web-server,reverse-proxy,load-balancer,proxy",
        "docker run -p 80:80 nginx",
        "code",
    ),
    # Authentication — fine-grained authorization engines -----------------------------
    (
        "openfga",
        "OpenFGA",
        "Open source fine-grained authorization",
        "OpenFGA is an open-source authorization solution based on Google Zanzibar. It lets "
        "you implement fine-grained access control with relationship-based authorization "
        "(ReBAC). Used by Auth0 and designed for multi-tenant SaaS at scale.",
        "authentication",
        "openfga/openfga",
        3000,
        "https://openfga.dev",
        "authorization,rbac,rebac,fine-grained,zanzibar",
        "docker run -p 8080:8080 openfga/openfga run",
        "code",
    ),
    (
        "casbin",
        "Casbin",
        "An authorization library that supports access control models",
        "Casbin is a powerful authorization library with support for ACL, RBAC, ABAC, and "
        "custom access control models. Available in Go, Node.js, Python, PHP, Rust, Java, "
        "and more. Define your authorization model in a simple config file.",
        "authentication",
        "casbin/casbin",
        17000,
        "https://casbin.org",
        "authorization,rbac,abac,acl,golang",
        "go get github.com/casbin/casbin/v2",
        "code",
    ),
    # Database — Vector databases for AI/RAG workloads ------------------------------
    (
        "chromadb",
        "Chroma",
        "The AI-native open-source embedding database",
        "Chroma is the leading open-source vector database built for AI applications. "
        "Store, query, and manage embeddings with a simple Python/JavaScript API. "
        "No server required for dev — embed directly in your app. Scales to millions "
        "of vectors with persistent storage and metadata filtering.",
        "database",
        "chroma-core/chroma",
        17000,
        "https://trychroma.com",
        "vector-database,embeddings,rag,ai,python,javascript",
        "pip install chromadb",
        "code",
    ),
    (
        "qdrant",
        "Qdrant",
        "Vector similarity search engine and vector database",
        "Qdrant is a high-performance vector similarity search engine designed for "
        "production AI workloads. Written in Rust, it supports payload filtering, "
        "hybrid search, on-disk storage, and distributed deployment. Used for RAG "
        "pipelines, semantic search, and recommendation systems.",
        "database",
        "qdrant/qdrant",
        21000,
        "https://qdrant.tech",
        "vector-database,embeddings,rag,similarity-search,rust",
        "pip install qdrant-client",
        "code",
    ),
    (
        "weaviate",
        "Weaviate",
        "AI-native vector database built for production",
        "Weaviate is an AI-native open-source vector database. It supports hybrid "
        "search (vector + keyword), multi-modal data (text, images, audio), modules "
        "for OpenAI / Cohere / HuggingFace embeddings, and GraphQL API. Cloud and "
        "self-hosted options available.",
        "database",
        "weaviate/weaviate",
        12000,
        "https://weaviate.io",
        "vector-database,hybrid-search,graphql,embeddings,rag",
        "pip install weaviate-client",
        "code",
    ),
    (
        "milvus",
        "Milvus",
        "Open-source vector database built for scalable similarity search",
        "Milvus is a cloud-native open-source vector database built for massive-scale "
        "embedding similarity search. Powers AI applications with billion-vector support, "
        "ANNS algorithms (HNSW, IVF), GPU acceleration, and a Python SDK. Foundation of "
        "Zilliz Cloud.",
        "database",
        "milvus-io/milvus",
        32000,
        "https://milvus.io",
        "vector-database,embeddings,similarity-search,scalable,python",
        "pip install pymilvus",
        "code",
    ),
    (
        "pgvector",
        "pgvector",
        "Open-source vector similarity search for PostgreSQL",
        "pgvector is a PostgreSQL extension that adds vector similarity search. Store "
        "embeddings alongside relational data, run exact and approximate nearest-neighbor "
        "queries, and use familiar SQL with `<->` distance operators. Works with Postgres "
        "on Supabase, Neon, and self-hosted deployments.",
        "database",
        "pgvector/pgvector",
        14000,
        "https://github.com/pgvector/pgvector",
        "vector-database,postgresql,embeddings,rag,sql",
        "CREATE EXTENSION vector;",
        "code",
    ),
    # AI — LLM inference and local model running -------------------------------------
    (
        "vllm",
        "vLLM",
        "Fast and easy-to-use library for LLM inference and serving",
        "vLLM is a fast, memory-efficient LLM inference and serving library. Achieves "
        "state-of-the-art throughput with PagedAttention memory management, continuous "
        "batching, and optimized CUDA kernels. Serves OpenAI-compatible APIs for "
        "Llama, Mistral, Mixtral, Qwen, and 100+ models.",
        "ai-automation",
        "vllm-project/vllm",
        20000,
        "https://docs.vllm.ai",
        "llm,inference,serving,openai-compatible,gpu,python",
        "pip install vllm",
        "code",
    ),
    (
        "llama-cpp",
        "llama.cpp",
        "LLM inference in C/C++ — run AI models locally",
        "llama.cpp enables LLM inference with minimal setup on CPUs and GPUs. The most "
        "widely used local LLM runtime — supports Llama 3, Mistral, Gemma, Phi, and "
        "dozens of GGUF models. Runs on Mac, Linux, Windows, Raspberry Pi, and Android. "
        "Foundation for Ollama, LM Studio, and many local AI tools.",
        "ai-automation",
        "ggerganov/llama.cpp",
        70000,
        "https://github.com/ggerganov/llama.cpp",
        "llm,local-ai,inference,cpu,gpu,gguf,c++",
        "brew install llama.cpp",
        "code",
    ),
    # AI — ML experiment tracking and model management --------------------------------
    (
        "wandb",
        "Weights & Biases",
        "ML experiment tracking, model monitoring, and collaboration",
        "Weights & Biases (W&B) is the leading MLOps platform for tracking ML experiments, "
        "visualizing training runs, managing datasets, and deploying models. Integrates with "
        "PyTorch, TensorFlow, Keras, Hugging Face, and all major ML frameworks with a "
        "single `wandb.log()` call.",
        "ai-automation",
        "wandb/wandb",
        9000,
        "https://wandb.ai",
        "mlops,experiment-tracking,ml,pytorch,tensorflow,monitoring",
        "pip install wandb",
        "code",
    ),
    # Boilerplates / Starter Kits -------------------------------------------------------
    (
        "t3-stack",
        "T3 Stack",
        "The best way to start a full-stack, typesafe Next.js app",
        "The T3 Stack is an opinionated, full-stack, typesafe Next.js boilerplate created by Theo. "
        "Ships with Next.js, TypeScript, Tailwind CSS, tRPC, Prisma, and NextAuth.js — "
        "each component optional at setup. Created by `create-t3-app`, it's the most popular "
        "opinionated Next.js starter with 25k+ GitHub stars and millions of weekly npm downloads.",
        "boilerplates",
        "t3-oss/create-t3-app",
        25000,
        "https://create.t3.gg",
        "nextjs,typescript,trpc,tailwind,prisma,nextauth,fullstack,boilerplate",
        "npm create t3-app@latest",
        "code",
    ),
    (
        "nextjs-boilerplate",
        "Next.js Boilerplate",
        "Production-ready Next.js starter with TypeScript, Tailwind, and Clerk",
        "A production-ready, batteries-included Next.js boilerplate. Ships with TypeScript, "
        "Tailwind CSS, ESLint, Prettier, Clerk auth, Sentry error monitoring, Stripe payments, "
        "Drizzle ORM, and Playwright E2E tests. Opinionated and well-maintained with 12k+ stars.",
        "boilerplates",
        "ixartz/Next-js-Boilerplate",
        12000,
        "https://github.com/ixartz/Next-js-Boilerplate",
        "nextjs,typescript,tailwind,clerk,stripe,drizzle,playwright,boilerplate",
        "git clone https://github.com/ixartz/Next-js-Boilerplate.git",
        "code",
    ),
    # AI — visual flow builders (no-code/low-code LangChain environments) ---------------
    (
        "flowise",
        "Flowise",
        "Drag-and-drop UI to build LLM flows with LangChain",
        "Flowise is an open-source drag-and-drop tool for building customized LLM "
        "orchestration flows and AI agents. Built on LangChain and LangGraph, with "
        "100+ integrations: OpenAI, Anthropic, Groq, Ollama, Pinecone, Qdrant, and "
        "more. Deploy chatbots, RAG pipelines, and multi-agent systems in minutes "
        "with no code required.",
        "ai-automation",
        "FlowiseAI/Flowise",
        34000,
        "https://flowiseai.com",
        "langchain,rag,chatbot,no-code,visual-builder,llm,agents",
        "npx flowise start",
        "code",
    ),
    (
        "langflow",
        "Langflow",
        "Visual framework for building multi-agent and RAG applications",
        "Langflow is a low-code app builder for RAG and multi-agent AI applications. "
        "A visual editor lets you compose pipelines from LangChain and LlamaIndex "
        "components. Export flows as APIs or embed in Python. Supports OpenAI, "
        "Anthropic, Google, local models via Ollama, and 20+ vector databases.",
        "ai-automation",
        "langflow-ai/langflow",
        48000,
        "https://langflow.org",
        "langchain,llamaindex,rag,multi-agent,visual-builder,llm,python",
        "pip install langflow",
        "code",
    ),
    # Logging -------------------------------------------------------------------------
    (
        "winston",
        "Winston",
        "A logger for just about everything in Node.js",
        "Winston is the most popular Node.js logging library with a multi-transport "
        "architecture. Write logs to the console, files, databases, or HTTP endpoints "
        "simultaneously. Supports structured JSON output, custom formatters, log levels, "
        "and async transports. Used by millions of Node.js applications in production.",
        "logging",
        "winstonjs/winston",
        22000,
        "https://github.com/winstonjs/winston",
        "nodejs,logging,structured-logging,transports,json",
        "npm install winston",
        "code",
    ),
    (
        "pino",
        "Pino",
        "Super fast, all natural JSON logger for Node.js",
        "Pino is the fastest Node.js logger available — up to 5× faster than alternatives "
        "like Bunyan and Winston. Uses an asynchronous destination stream and produces "
        "compact NDJSON logs. Integrations for Fastify, Express, Hapi, Koa, and Restify. "
        "Includes pino-pretty for human-readable development output.",
        "logging",
        "pinojs/pino",
        14000,
        "https://getpino.io",
        "nodejs,logging,json,structured-logging,fastify,async",
        "npm install pino",
        "code",
    ),
    # Background Jobs — Distributed workflow orchestration ----------------------------
    (
        "hatchet",
        "Hatchet",
        "Distributed, fault-tolerant background task and workflow engine",
        "Hatchet is an open-source durable task queue and workflow orchestration engine. "
        "Define multi-step workflows as code with built-in retries, rate limiting, "
        "fan-out/fan-in, and cron scheduling. SDKs for TypeScript, Python, and Go. "
        "Self-hostable with a local Docker Compose stack or deploy to cloud.",
        "background-jobs",
        "hatchet-dev/hatchet",
        5000,
        "https://hatchet.run",
        "workflow,orchestration,background-jobs,typescript,python,go,durable-execution",
        "npx @hatchet-dev/hatchet-cli dev",
        "code",
    ),
    # API Tools — Distributed application runtime -------------------------------------
    (
        "dapr",
        "Dapr",
        "Portable, event-driven runtime for distributed applications",
        "Dapr (Distributed Application Runtime) is a CNCF-graduated open-source runtime "
        "that simplifies microservice development. It provides language-agnostic building "
        "blocks via HTTP/gRPC: service-to-service invocation, state management, pub/sub "
        "messaging, bindings, actors, and durable workflows. SDKs for Go, Python, Java, "
        ".NET, JavaScript, PHP, and Rust.",
        "api-tools",
        "dapr/dapr",
        24000,
        "https://dapr.io",
        "microservices,distributed,pubsub,state-management,actors,workflows,grpc",
        "curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh | /bin/bash",
        "code",
    ),
    # Logging — Python loggers -------------------------------------------------------
    (
        "loguru",
        "Loguru",
        "Python logging made (stupidly) simple",
        "Loguru is a Python logging library that aims to make logging enjoyable rather "
        "than a chore. Zero boilerplate: one import, one `logger`, and you're done. "
        "Automatic exception formatting, colour output, rotation/retention, async support, "
        "and structured JSON logging. The dominant modern alternative to the stdlib "
        "logging module for Python applications.",
        "logging",
        "Delgan/loguru",
        18000,
        "https://loguru.readthedocs.io",
        "python,logging,structured-logging,async",
        "pip install loguru",
        "code",
    ),
    (
        "structlog",
        "structlog",
        "Structured logging for Python — simple, powerful, and fast",
        "structlog makes logging in Python fast, less painful, and prettier. It wraps "
        "any existing Python logger (stdlib, loguru, etc.) and adds structured key-value "
        "context, a processor pipeline, and optional JSON output. Used at Stripe, "
        "Heroku, and many large Python projects.",
        "logging",
        "hynek/structlog",
        3500,
        "https://www.structlog.org",
        "python,logging,structured-logging,json",
        "pip install structlog",
        "code",
    ),
    # Message Queue — stream processing -----------------------------------------------
    (
        "redpanda",
        "Redpanda",
        "Kafka-compatible streaming data platform — 10× faster, no ZooKeeper",
        "Redpanda is a Kafka-compatible event streaming platform written in C++. "
        "No ZooKeeper, no JVM, no configuration zoo. Delivers 10× lower latency "
        "than Kafka with identical API compatibility. CNCF sandbox project with "
        "a managed cloud offering and a self-hosted binary.",
        "message-queue",
        "redpanda-data/redpanda",
        9000,
        "https://redpanda.com",
        "kafka,streaming,message-queue,event-streaming,kafka-compatible",
        "curl -1sLf 'https://dl.redpanda.com/nzc4ZYQK3WRGd9sy/redpanda/cfg/setup/bash.deb.sh' | sudo bash && sudo apt install redpanda",
        "code",
    ),
    # AI — Speech-to-text / voice AI -------------------------------------------------
    (
        "deepgram",
        "Deepgram",
        "Speech-to-text API for real-time and async transcription",
        "Deepgram provides developer-friendly speech recognition via REST and WebSocket "
        "APIs. Features include real-time streaming transcription, speaker diarisation, "
        "language detection, topic detection, and summarisation. SDKs for Python, "
        "Node.js, Go, .NET, and Ruby. Used by NASA, Spotify, and thousands of indie "
        "developers for voice-enabled applications.",
        "ai-dev-tools",
        "deepgram/deepgram-python-sdk",
        800,
        "https://deepgram.com",
        "speech-to-text,asr,voice,transcription,realtime,api",
        "pip install deepgram-sdk",
        "saas",
    ),
    (
        "whisper",
        "OpenAI Whisper",
        "Open-source automatic speech recognition that rivals humans",
        "Whisper is OpenAI's open-source automatic speech recognition model trained on "
        "680k hours of multilingual speech. Supports 99 languages with near-human "
        "accuracy. Runs locally, no API key required. Models range from tiny (39M params) "
        "to large-v3 (1.5B params). Widely integrated into voice apps, transcription "
        "pipelines, and AI agents via faster-whisper and whisper.cpp.",
        "ai-dev-tools",
        "openai/whisper",
        74000,
        "https://github.com/openai/whisper",
        "speech-to-text,asr,voice,transcription,python,open-source,local",
        "pip install openai-whisper",
        "code",
    ),
    # Date/time libraries --------------------------------------------------------
    (
        "dayjs",
        "Day.js",
        "2kB immutable date library alternative to Moment.js",
        "Day.js is a minimalist JavaScript library for parsing, validating, manipulating, "
        "and displaying dates and times. API-compatible with Moment.js but only 2kB. "
        "Supports plugins for relative time, duration, UTC, and timezone handling. "
        "The fastest-growing Moment.js alternative with 47k+ GitHub stars.",
        "frontend-frameworks",
        "iamkun/dayjs",
        47000,
        "https://day.js.org",
        "date,time,javascript,moment-alternative,lightweight",
        "npm install dayjs",
        "code",
    ),
    # 3D / WebGL -----------------------------------------------------------------
    (
        "threejs",
        "Three.js",
        "JavaScript 3D library",
        "Three.js is the most popular JavaScript 3D library, providing WebGL-based 3D "
        "rendering for the web. Includes geometries, materials, lights, cameras, loaders, "
        "and a rich ecosystem (React Three Fiber, Drei, etc.). Powers interactive 3D "
        "experiences, data visualisations, and games in the browser. 102k+ GitHub stars.",
        "frontend-frameworks",
        "mrdoob/three.js",
        102000,
        "https://threejs.org",
        "3d,webgl,graphics,canvas,animation,javascript",
        "npm install three",
        "code",
    ),
    # Data visualization ---------------------------------------------------------
    (
        "d3",
        "D3.js",
        "Data-Driven Documents — the JavaScript library for bespoke data visualization",
        "D3.js binds data to the DOM and applies data-driven transformations to the document. "
        "Build bar charts, line charts, scatter plots, maps, networks, and custom SVG "
        "visualisations. Low-level but extremely powerful. Powers Observable, Vega, "
        "and many charting libraries internally. 108k+ GitHub stars.",
        "analytics-metrics",
        "d3/d3",
        108000,
        "https://d3js.org",
        "data-visualization,svg,charts,javascript,canvas",
        "npm install d3",
        "code",
    ),
    (
        "chartjs",
        "Chart.js",
        "Simple yet flexible JavaScript charting for designers & developers",
        "Chart.js is the most popular open-source charting library. Renders "
        "8 chart types (bar, line, pie, doughnut, radar, scatter, bubble, polar area) "
        "on HTML5 Canvas. Responsive by default, animated, and highly customisable via plugins. "
        "65k+ GitHub stars; used in dashboards, analytics UIs, and reporting tools.",
        "analytics-metrics",
        "chartjs/Chart.js",
        65000,
        "https://www.chartjs.org",
        "charts,canvas,javascript,visualization,responsive",
        "npm install chart.js",
        "code",
    ),
    # Data fetching --------------------------------------------------------------
    (
        "swr",
        "SWR",
        "React Hooks library for data fetching",
        "SWR is a React hooks library for remote data fetching from Vercel. "
        "Stale-while-revalidate strategy: returns cached data first (stale), then "
        "re-fetches and updates (revalidate). Built-in caching, deduplication, "
        "real-time updates, and TypeScript support. 30k+ GitHub stars.",
        "frontend-frameworks",
        "vercel/swr",
        30000,
        "https://swr.vercel.app",
        "data-fetching,react,hooks,caching,state-management",
        "npm install swr",
        "code",
    ),
    # Drag and drop --------------------------------------------------------------
    (
        "dnd-kit",
        "dnd kit",
        "A lightweight, performant, accessible drag and drop toolkit for React",
        "dnd kit is the modern drag-and-drop library for React. Supports sortable lists, "
        "grids, kanban boards, and custom sensors (pointer, keyboard, touch). "
        "Framework-agnostic core, collision detection algorithms, and full accessibility "
        "support out of the box. The successor to react-beautiful-dnd. 12k+ GitHub stars.",
        "frontend-frameworks",
        "clauderic/dnd-kit",
        12000,
        "https://dndkit.com",
        "drag-and-drop,react,sortable,accessibility,touch",
        "npm install @dnd-kit/core @dnd-kit/sortable",
        "code",
    ),
    # Headless browser -----------------------------------------------------------
    (
        "puppeteer",
        "Puppeteer",
        "Headless Chrome Node.js API",
        "Puppeteer is Google's official Node.js library for controlling headless Chrome. "
        "Automate form submission, UI testing, screenshot capture, PDF generation, "
        "and web scraping. Supports both headless and headful Chrome/Chromium. "
        "The foundation of many E2E testing and scraping tools. 88k+ GitHub stars.",
        "testing-tools",
        "puppeteer/puppeteer",
        88000,
        "https://pptr.dev",
        "headless-browser,chrome,testing,scraping,automation,pdf",
        "npm install puppeteer",
        "code",
    ),
    # Python task queues ---------------------------------------------------------
    (
        "celery",
        "Celery",
        "Distributed task queue for Python",
        "Celery is the most widely used Python distributed task queue. Execute tasks "
        "asynchronously with Redis or RabbitMQ as the broker. Supports scheduling (beat), "
        "retries, chaining, groups, and monitoring via Flower. Essential for Django and "
        "FastAPI background jobs. 24k+ GitHub stars.",
        "background-jobs",
        "celery/celery",
        24000,
        "https://docs.celeryq.dev",
        "python,task-queue,redis,rabbitmq,async,django,fastapi",
        "pip install celery",
        "code",
    ),
    # AI — LangChain (most popular LLM framework) ----------------------------------------
    (
        "langchain",
        "LangChain",
        "Build context-aware reasoning applications with LLMs",
        "LangChain is the most widely used framework for building LLM-powered applications. "
        "Provides chains, agents, RAG pipelines, memory, and a vast ecosystem of integrations "
        "(OpenAI, Anthropic, Hugging Face, vector stores, document loaders). "
        "Available in Python and JavaScript. Part of the LangChain ecosystem alongside "
        "LangGraph (multi-agent workflows) and LangSmith (observability). 95k+ GitHub stars.",
        "ai-automation",
        "langchain-ai/langchain",
        95000,
        "https://python.langchain.com",
        "llm,rag,agents,chains,python,javascript,ai,openai",
        "pip install langchain",
        "code",
    ),
    # AI — AutoGen (Microsoft multi-agent framework) ------------------------------------
    (
        "autogen",
        "AutoGen",
        "Multi-agent conversation framework by Microsoft Research",
        "AutoGen is Microsoft's open-source framework for building multi-agent AI systems. "
        "Agents converse, collaborate, and use tools autonomously to solve complex tasks. "
        "Supports OpenAI, Azure OpenAI, local LLMs, and custom models. AutoGen Studio "
        "offers a no-code UI for building agentic workflows. 34k+ GitHub stars.",
        "ai-automation",
        "microsoft/autogen",
        34000,
        "https://microsoft.github.io/autogen",
        "llm,agents,multi-agent,python,microsoft,orchestration,ai",
        "pip install pyautogen",
        "code",
    ),
    # Frontend — VueUse (Vue Composition API utilities) ---------------------------------
    (
        "vueuse",
        "VueUse",
        "Collection of essential Vue Composition API utilities",
        "VueUse is a collection of 200+ utility composables for Vue 3 and Vue 2 "
        "with the Composition API. Covers sensors, browser APIs, state, animation, "
        "network, storage, and more. Every function is tree-shakeable and fully typed. "
        "Inspired by React Hooks, used in virtually every Vue 3 project. 21k+ GitHub stars.",
        "frontend-frameworks",
        "vueuse/vueuse",
        21000,
        "https://vueuse.org",
        "vue,composables,utilities,typescript,hooks,vue3",
        "npm install @vueuse/core",
        "code",
    ),
    # Maps — MapLibre GL JS (open-source Mapbox alternative) ----------------------------
    (
        "maplibre",
        "MapLibre GL JS",
        "Open-source vector map rendering — free Mapbox GL JS fork",
        "MapLibre GL JS is the open-source fork of Mapbox GL JS. Renders vector tiles "
        "via WebGL — smooth zooming, rotation, and custom styling using Mapbox GL styles. "
        "No API key required, fully Apache 2.0 licensed. Drop-in Mapbox replacement. "
        "Powers OSM-based maps, geospatial dashboards, and location-aware apps. 11k+ stars.",
        "maps-location",
        "maplibre/maplibre-gl-js",
        11000,
        "https://maplibre.org/maplibre-gl-js/docs/",
        "maps,vector-tiles,webgl,openstreetmap,mapbox-alternative,geospatial",
        "npm install maplibre-gl",
        "code",
    ),
    # API — mitt (tiny event emitter) ---------------------------------------------------
    (
        "mitt",
        "mitt",
        "Tiny 200b functional event emitter / pubsub",
        "mitt is a tiny, zero-dependency event emitter for JavaScript. 200 bytes gzipped, "
        "TypeScript native, with a simple three-method API: on, off, emit. "
        "Supports wildcard '*' listeners for all events. Works in browsers and Node.js. "
        "10k+ GitHub stars; the go-to solution for cross-component and module-level pub/sub.",
        "api-tools",
        "developit/mitt",
        10000,
        "https://github.com/developit/mitt",
        "event-emitter,pubsub,tiny,typescript,javascript,events",
        "npm install mitt",
        "code",
    ),
    # Documentation — Shiki (syntax highlighting) ---------------------------------------
    (
        "shiki",
        "Shiki",
        "Beautiful syntax highlighting powered by TextMate grammars",
        "Shiki is a syntax highlighter that uses TextMate grammars and VS Code themes for "
        "accurate, beautiful code highlighting. Outputs static HTML — no client-side JS needed. "
        "Used by VitePress, Astro docs, Nuxt docs, and thousands of documentation sites. "
        "Supports 200+ languages and all VS Code themes. The standard for modern doc sites. "
        "10k+ GitHub stars; successor to highlight.js in SSG-based documentation stacks.",
        "documentation",
        "shikijs/shiki",
        10000,
        "https://shiki.style",
        "syntax-highlighting,documentation,markdown,vitepress,astro,typescript",
        "npm install shiki",
        "code",
    ),
    # Localization — Lingui (JS/React i18n) --------------------------------------------
    (
        "lingui",
        "Lingui",
        "Powerful i18n library with compile-time message extraction",
        "Lingui is a JavaScript/React internationalization library that extracts messages "
        "at compile time — no runtime overhead. Supports ICU MessageFormat syntax, "
        "React, Vue, Angular, and vanilla JS. CLI for message extraction and compilation. "
        "Works with any translation management system via catalog formats (PO, JSON, CSV). "
        "4.5k+ stars; production-proven at scale with type-safe message IDs.",
        "localization",
        "lingui/js-lingui",
        4500,
        "https://lingui.dev",
        "i18n,react,typescript,icu,localization,translation",
        "npm install @lingui/core @lingui/react",
        "code",
    ),
    # Frontend Frameworks — Valtio (proxy state) ----------------------------------------
    (
        "valtio",
        "Valtio",
        "Proxy-based mutable state management for React",
        "Valtio makes JavaScript objects act like reactive state. Wrap any object with "
        "`proxy()` and it auto-notifies subscribed components on mutation — no reducers, "
        "no actions, no boilerplate. Works with React via `useSnapshot()`. "
        "From the Poimandres collective (also builds Zustand, Jotai). "
        "9k+ GitHub stars; ideal for shared mutable state that doesn't need Redux patterns.",
        "frontend-frameworks",
        "pmndrs/valtio",
        9000,
        "https://valtio.dev",
        "state-management,react,proxy,typescript,javascript",
        "npm install valtio",
        "code",
    ),
    # Frontend Frameworks — Effector (reactive state) -----------------------------------
    (
        "effector",
        "Effector",
        "Framework-agnostic reactive state manager with powerful typing",
        "Effector is a business logic-first reactive state manager for JavaScript. "
        "Uses algebraic data types: stores (state), events (triggers), and effects (side effects). "
        "Works with React, Vue, Svelte, Angular, and vanilla JS via official bindings. "
        "No context providers needed — stores are global by default. "
        "4k+ GitHub stars; popular for complex domain logic where Zustand/Jotai feel too simple.",
        "frontend-frameworks",
        "effector/effector",
        4000,
        "https://effector.dev",
        "state-management,reactive,typescript,react,vue,svelte",
        "npm install effector",
        "code",
    ),
    # Testing — classic JS test runner (very common "alternative" query target) ----------
    (
        "mocha",
        "Mocha",
        "Simple, flexible, fun JavaScript test framework",
        "Mocha is the most battle-tested Node.js test framework. Runs in Node.js and the "
        "browser, supports async tests via Promises and callbacks, and is compatible with "
        "any assertion library (Chai, assert, expect.js). Highly configurable with reporters, "
        "hooks (before/after), and a rich plugin ecosystem. The original Node.js test runner "
        "that paved the way for Jest and Vitest. 22k+ GitHub stars.",
        "testing-tools",
        "mochajs/mocha",
        22000,
        "https://mochajs.org",
        "testing,javascript,nodejs,bdd,tdd,async",
        "npm install mocha --save-dev",
        "code",
    ),
    # Security — container and IaC vulnerability scanning ------------------------------
    (
        "trivy",
        "Trivy",
        "All-in-one open-source security scanner for containers and IaC",
        "Trivy is a comprehensive, fast vulnerability scanner by Aqua Security. Scans "
        "container images, filesystems, Git repos, Kubernetes clusters, and IaC "
        "(Terraform, Helm, CloudFormation) for CVEs, misconfigurations, and secrets. "
        "Zero config, a single binary, and CI/CD integrations for GitHub Actions and "
        "GitLab CI. CNCF sandbox project. 22k+ GitHub stars.",
        "security-tools",
        "aquasecurity/trivy",
        22000,
        "https://trivy.dev",
        "security,vulnerability-scanning,containers,iac,devops,cve",
        "brew install trivy",
        "code",
    ),
    # Security — static application security testing (SAST) ---------------------------
    (
        "semgrep",
        "Semgrep",
        "Fast, open-source, static analysis for finding bugs and enforcing code standards",
        "Semgrep is a fast, open-source static analysis tool for finding bugs, detecting "
        "vulnerabilities, and enforcing code standards. Write rules in a simple YAML syntax "
        "that mirrors your code. Supports 30+ languages (Python, JS/TS, Go, Java, Ruby, PHP). "
        "Semgrep Registry has 3,000+ community rules. Integrates into CI/CD pipelines with "
        "zero friction. Used at Dropbox, Snowflake, and thousands of security-conscious teams. "
        "10k+ GitHub stars.",
        "security-tools",
        "semgrep/semgrep",
        10000,
        "https://semgrep.dev",
        "security,sast,static-analysis,vulnerability,code-quality",
        "pip install semgrep",
        "code",
    ),
    # Documentation — Next.js-based docs framework ----------------------------------------
    (
        "nextra",
        "Nextra",
        "Simple, powerful and flexible site generation framework with Next.js",
        "Nextra is a documentation site framework built on Next.js. Write docs in MDX, "
        "get instant search, syntax highlighting, i18n, dark mode, and a polished theme "
        "out of the box. Zero configuration to start; fully customisable with Next.js. "
        "Used by OpenAI, Vercel docs, and thousands of open-source projects. "
        "From the creators of SWR (Vercel). 11k+ GitHub stars.",
        "documentation",
        "shuding/nextra",
        11000,
        "https://nextra.site",
        "docs,nextjs,mdx,documentation,search,dark-mode",
        "npm install nextra nextra-theme-docs",
        "code",
    ),
    # Documentation — VitePress (Vue/Vite-powered docs) ------------------------------------
    (
        "vitepress",
        "VitePress",
        "Vite & Vue powered static site generator for documentation",
        "VitePress is the official documentation site generator for the Vue ecosystem. "
        "Built on Vite and Vue 3 — blazing-fast dev server, instant HMR, and markdown-based "
        "content with Vue components inline. Ships with a polished default theme, built-in "
        "search, and internationalization. Powers Vue.js docs, Vite docs, Vitest docs, "
        "Pinia docs, and thousands of open-source doc sites. 13k+ GitHub stars.",
        "documentation",
        "vuejs/vitepress",
        13000,
        "https://vitepress.dev",
        "docs,vue,vite,markdown,static-site,mdx,documentation",
        "npm install vitepress",
        "code",
    ),
    # Database / BaaS — Supabase -------------------------------------------------------
    (
        "supabase",
        "Supabase",
        "The open source Firebase alternative",
        "Supabase is an open-source Firebase alternative built on PostgreSQL. "
        "Provides a hosted Postgres database, authentication, instant REST and GraphQL APIs, "
        "edge functions, realtime subscriptions, and file storage — all with a generous free tier. "
        "Self-hostable with Docker. The most popular open-source BaaS for indie developers. "
        "73k+ GitHub stars.",
        "database",
        "supabase/supabase",
        73000,
        "https://supabase.com",
        "baas,postgres,auth,realtime,storage,open-source,firebase-alternative",
        "npm install @supabase/supabase-js",
        "code",
    ),
    # Database / BaaS — Convex --------------------------------------------------------
    (
        "convex",
        "Convex",
        "The reactive backend platform for TypeScript apps",
        "Convex is a backend-as-a-service with a real-time reactive database for TypeScript. "
        "Write server functions in TypeScript that automatically re-run when data changes, "
        "syncing state to all connected clients instantly. No SQL, no REST — just TypeScript "
        "functions, automatic caching, and built-in auth. 8k+ GitHub stars.",
        "database",
        "get-convex/convex-backend",
        8000,
        "https://convex.dev",
        "baas,realtime,typescript,reactive,serverless",
        "npm install convex",
        "code",
    ),
    # Database / BaaS — Appwrite -------------------------------------------------------
    (
        "appwrite",
        "Appwrite",
        "Self-hosted backend-as-a-service for web, mobile, and flutter apps",
        "Appwrite is an open-source self-hosted BaaS providing a REST API for authentication, "
        "databases, cloud storage, cloud functions, and realtime events. "
        "Deploy with Docker in minutes. Supports 30+ SDKs and frameworks. "
        "A strong Firebase alternative for developers who want full data ownership. "
        "45k+ GitHub stars.",
        "database",
        "appwrite/appwrite",
        45000,
        "https://appwrite.io",
        "baas,self-hosted,auth,database,storage,functions,firebase-alternative",
        "docker run appwrite/appwrite",
        "code",
    ),
    # Frontend Frameworks — Rollup -----------------------------------------------------
    (
        "rollup",
        "Rollup",
        "Next-generation ES module bundler",
        "Rollup is a module bundler for JavaScript which compiles small pieces of code into "
        "something larger and more complex, such as a library or application. It uses the "
        "standardized ES module format instead of CommonJS. Rollup pioneered tree-shaking and "
        "is the bundler powering Vite under the hood for production builds. "
        "Used by React, Vue, D3, Three.js, and thousands of libraries. 25k+ GitHub stars.",
        "frontend-frameworks",
        "rollup/rollup",
        25000,
        "https://rollupjs.org",
        "bundler,build-tool,esm,tree-shaking,javascript",
        "npm install rollup",
        "code",
    ),
    # Email Marketing — Loops ----------------------------------------------------------
    (
        "loops",
        "Loops",
        "The email platform built for SaaS",
        "Loops is a modern email platform purpose-built for SaaS products. "
        "Send transactional emails (password resets, receipts, notifications) and "
        "marketing campaigns from one place. Events-driven: trigger emails from "
        "your app events, Stripe webhooks, and user actions. "
        "Simple API, beautiful editor, clean analytics. "
        "Favourite among indie hackers and SaaS founders. 5k+ GitHub stars.",
        "email-marketing",
        "loops-so/loops",
        5000,
        "https://loops.so",
        "email,transactional,marketing,saas,events-driven",
        "npm install loops-sdk",
        "saas",
    ),
    # Search Engine — Orama ------------------------------------------------------------
    (
        "orama",
        "Orama",
        "Fast, in-memory, typo-tolerant full-text and vector search",
        "Orama is an open-source, edge-native search engine written in TypeScript. "
        "Works entirely in-process (no server required) with schema-free indexing, "
        "typo-tolerance, and vector/semantic search support. "
        "Runs in the browser, Node.js, Deno, Bun, Cloudflare Workers, and Fastly. "
        "Orama Cloud provides a managed hosted tier. "
        "Ideal for docs sites, e-commerce, and apps that need fast offline-capable search. "
        "7k+ GitHub stars.",
        "search-engine",
        "oramasearch/orama",
        7000,
        "https://orama.com",
        "search,full-text,vector,edge,typescript,in-memory,open-source",
        "npm install @orama/orama",
        "code",
    ),
    # Monitoring — SigNoz --------------------------------------------------------------
    (
        "signoz",
        "SigNoz",
        "Open-source Datadog and NewRelic alternative",
        "SigNoz is an open-source application performance monitoring (APM) and observability "
        "platform built on OpenTelemetry. Provides distributed tracing, metrics, and logs "
        "in a single pane — no vendor lock-in, full data ownership. "
        "Self-host with Docker/Kubernetes or use SigNoz Cloud. "
        "Supports all major languages via OpenTelemetry SDKs. "
        "18k+ GitHub stars.",
        "monitoring-uptime",
        "signoz/signoz",
        18000,
        "https://signoz.io",
        "monitoring,apm,observability,open-source,opentelemetry,tracing,metrics,logs",
        "git clone https://github.com/signoz/signoz && cd signoz/deploy && docker compose up -d",
        "code",
    ),
    # Developer Tools — Appsmith -------------------------------------------------------
    (
        "appsmith",
        "Appsmith",
        "Open-source platform to build internal tools, admin panels, and dashboards",
        "Appsmith is an open-source low-code framework for building internal tools, admin panels, "
        "CRUD apps, and dashboards. Drag-and-drop UI components connect to any REST API, "
        "GraphQL, or database (PostgreSQL, MongoDB, MySQL, Redis, and 30+ more). "
        "Write custom logic in JavaScript. Deploy on-premise with Docker or use Appsmith Cloud. "
        "A popular open-source Retool alternative. 31k+ GitHub stars.",
        "developer-tools",
        "appsmithorg/appsmith",
        31000,
        "https://www.appsmith.com",
        "internal-tools,low-code,admin-panel,dashboard,open-source,retool-alternative",
        "docker run -d --name appsmith -p 80:80 appsmith/appsmith-ce",
        "code",
    ),
    # Developer Tools — ToolJet --------------------------------------------------------
    (
        "tooljet",
        "ToolJet",
        "Open-source low-code platform to build and deploy internal tools",
        "ToolJet is an open-source low-code framework for building internal tools such as "
        "dashboards, admin panels, CRUD apps, and workflows. "
        "Visual drag-and-drop editor connects to 50+ data sources: PostgreSQL, MySQL, MongoDB, "
        "Stripe, Slack, Google Sheets, REST APIs, and more. "
        "Write JavaScript to add business logic. Self-host with Docker or use ToolJet Cloud. "
        "A direct open-source Retool alternative. 28k+ GitHub stars.",
        "developer-tools",
        "ToolJet/ToolJet",
        28000,
        "https://tooljet.com",
        "internal-tools,low-code,admin-panel,dashboard,open-source,retool-alternative",
        "docker run -d --name tooljet -p 3000:3000 tooljet/tooljet:latest",
        "code",
    ),
    # DevOps — Railway (PaaS deployment platform) ----------------------------------------
    (
        "railway",
        "Railway",
        "Instant deployments, zero config needed",
        "Railway is a cloud deployment platform built for teams and indie developers. "
        "Connect a GitHub repo and Railway auto-detects your language, builds with Nixpacks, "
        "and deploys in seconds. Supports databases (Postgres, MySQL, Redis, MongoDB), "
        "cron jobs, private networking, and multi-environment workflows. "
        "Pay for what you use — no cold starts, 100GB egress free tier. "
        "nixpacks (their OSS build system) has 7k+ GitHub stars.",
        "devops-infrastructure",
        "railwayapp/nixpacks",
        7000,
        "https://railway.app",
        "hosting,deployment,paas,cloud,auto-deploy,nixpacks",
        "npm install -g @railway/cli && railway login && railway up",
        "saas",
    ),
    # Database — Neon (serverless Postgres) -----------------------------------------------
    (
        "neon",
        "Neon",
        "Serverless Postgres with branching",
        "Neon is a serverless PostgreSQL platform that separates compute and storage, "
        "enabling scale-to-zero and instant database branching. "
        "Create a branch for every PR — each branch is a full database copy with "
        "instant provisioning and no storage duplication. "
        "Compatible with any Postgres driver or ORM (Prisma, Drizzle, Kysely). "
        "Generous free tier: 0.5 GB storage, unlimited branches. "
        "13k+ GitHub stars; Vercel's official Postgres partner.",
        "database",
        "neondatabase/neon",
        13000,
        "https://neon.tech",
        "postgres,serverless,branching,scale-to-zero,cloud",
        "npm install @neondatabase/serverless",
        "saas",
    ),
    # Headless CMS — Directus (open-source data platform) --------------------------------
    (
        "directus",
        "Directus",
        "The open data platform for headless content management",
        "Directus wraps any SQL database (Postgres, MySQL, SQLite, MS SQL) with a "
        "real-time REST + GraphQL API, a no-code app, and a JavaScript SDK. "
        "Works with your existing schema — no migrations required. "
        "Role-based access control, file management, webhooks, extensions, "
        "and a fully customisable admin UI. "
        "Self-host with Docker or use Directus Cloud. 28k+ GitHub stars.",
        "headless-cms",
        "directus/directus",
        28000,
        "https://directus.io",
        "cms,headless,rest,graphql,no-code,self-hosted,open-source",
        "npx directus-template-cli@latest extract",
        "code",
    ),
    # Frontend Frameworks — TanStack Table ------------------------------------------------
    (
        "tanstack-table",
        "TanStack Table",
        "Headless UI for building tables and datagrids",
        "TanStack Table (formerly React Table) is a headless, framework-agnostic "
        "table and datagrid library. Handles sorting, filtering, pagination, "
        "row selection, column resizing, and virtualization — "
        "you own the markup and styles. Supports React, Vue, Solid, Svelte, and vanilla JS. "
        "The most-downloaded open-source table library in the JS ecosystem. 24k+ GitHub stars.",
        "frontend-frameworks",
        "tanstack/table",
        24000,
        "https://tanstack.com/table",
        "table,datagrid,sorting,filtering,pagination,headless,react,vue",
        "npm install @tanstack/react-table",
        "code",
    ),
    # Frontend Frameworks — Fresh (Deno meta-framework) ------------------------------------
    (
        "fresh",
        "Fresh",
        "The next-gen web framework for Deno",
        "Fresh is a full-stack web framework for Deno built on islands architecture. "
        "Pages ship zero JavaScript by default — only interactive islands are hydrated. "
        "No build step, instant deploys to Deno Deploy. "
        "Uses Preact and JSX, supports TypeScript out of the box, "
        "and has a Tailwind CSS plugin. "
        "A strong alternative to Next.js for teams already using Deno. 12k+ GitHub stars.",
        "frontend-frameworks",
        "denoland/fresh",
        12000,
        "https://fresh.deno.dev",
        "deno,ssr,islands,fullstack,zero-js,preact,typescript",
        "deno run -A -r https://fresh.deno.dev my-project",
        "code",
    ),
    # Invoicing & Billing — Lago (open-source metering + billing API) ----------------------
    (
        "lago",
        "Lago",
        "Open-source metering and billing API",
        "Lago is an open-source billing API for usage-based, seat-based, and hybrid pricing models. "
        "Define billable metrics (API calls, compute minutes, storage GB), attach pricing plans, "
        "and generate invoices automatically. Self-host with Docker or use Lago Cloud. "
        "Integrates with Stripe, GoCardless, and Adyen for payment collection. "
        "A full-featured open-source alternative to Chargebee, Recurly, and Orb. 6k+ GitHub stars.",
        "invoicing-billing",
        "getlago/lago",
        6000,
        "https://www.getlago.com",
        "billing,metering,usage-based,invoicing,open-source,stripe,self-hosted",
        "docker compose up",
        "code",
    ),
    # Developer Tools — Zed (collaborative AI code editor) --------------------------------
    (
        "zed",
        "Zed",
        "High-performance, multiplayer code editor",
        "Zed is a next-generation code editor built in Rust for speed and collaboration. "
        "Real-time multiplayer editing, native AI integration (Claude, GPT, Gemini), "
        "a built-in terminal, and a language server protocol implementation. "
        "GPU-rendered UI — opens in milliseconds. "
        "Supports most languages via tree-sitter and LSP. "
        "Open-source since January 2024. 65k+ GitHub stars.",
        "developer-tools",
        "zed-industries/zed",
        65000,
        "https://zed.dev",
        "editor,ide,rust,ai,multiplayer,fast,open-source",
        "curl https://zed.dev/install.sh | sh",
        "code",
    ),
    # Developer Tools — Ghostty (fast GPU-native terminal emulator) -----------------------
    (
        "ghostty",
        "Ghostty",
        "Fast, feature-rich, and native terminal emulator",
        "Ghostty is a terminal emulator built by Mitchell Hashimoto (HashiCorp founder) "
        "that prioritises platform-native UI, GPU rendering, and correctness. "
        "Uses native UI frameworks on each platform (AppKit on macOS, GTK on Linux). "
        "Supports terminal multiplexing, ligatures, true colour, and thousands of keybindings. "
        "Written in Zig for maximum performance. 25k+ GitHub stars.",
        "developer-tools",
        "ghostty-org/ghostty",
        25000,
        "https://ghostty.org",
        "terminal,emulator,gpu,zig,fast,native,developer",
        "brew install ghostty",
        "code",
    ),
    # Developer Tools — GitButler (branch-stacking git client) ----------------------------
    (
        "gitbutler",
        "GitButler",
        "A Git client for simultaneous branches on top of your existing workflow",
        "GitButler is a next-generation git client that lets you work on multiple branches "
        "simultaneously without constantly context-switching. "
        "Virtual branches sit on top of your working directory — move files between them freely. "
        "Integrates with GitHub PRs, resolves conflicts visually, "
        "and syncs to a cloud backup branch automatically. "
        "Built with Tauri (Rust + WebView). 12k+ GitHub stars.",
        "developer-tools",
        "gitbutlerapp/gitbutler",
        12000,
        "https://gitbutler.com",
        "git,client,branches,workflow,tauri,rust,open-source",
        "brew install gitbutler",
        "code",
    ),
    # Developer Tools — Neovim (hyperextensible Vim-fork) ---------------------------------
    (
        "neovim",
        "Neovim",
        "Hyperextensible Vim-based text editor",
        "Neovim is a refactored Vim with first-class Lua scripting, a built-in LSP client, "
        "tree-sitter syntax highlighting, and async job control. "
        "A thriving plugin ecosystem (Telescope, nvim-cmp, LazyVim, AstroNvim, NvChad) "
        "makes it a fully-featured IDE for any language. "
        "Modal editing with Vim motions, infinitely configurable, and extremely fast. "
        "82k+ GitHub stars; one of the most-starred editor projects on GitHub.",
        "developer-tools",
        "neovim/neovim",
        82000,
        "https://neovim.io",
        "editor,vim,lua,lsp,treesitter,modal,open-source",
        "brew install neovim",
        "code",
    ),
    # AI Dev Tools — Aider (terminal AI pair programmer) ----------------------------------
    (
        "aider",
        "Aider",
        "AI pair programming in your terminal",
        "Aider lets you pair program with LLMs directly in your terminal. "
        "Works with Claude, GPT-4, and local models. Edits multiple files simultaneously, "
        "auto-commits changes with sensible messages, and handles large codebases via "
        "repo-map context. Supports voice coding, image input, and all major languages. "
        "Consistently top-ranked in SWE-bench coding benchmarks. 24k+ GitHub stars.",
        "ai-dev-tools",
        "Aider-AI/aider",
        24000,
        "https://aider.chat",
        "ai,coding,llm,terminal,pair-programming,claude,gpt,open-source",
        "pip install aider-chat",
        "code",
    ),
    # Developer Tools — Lazygit (TUI git client) ------------------------------------------
    (
        "lazygit",
        "Lazygit",
        "Simple terminal UI for git commands",
        "Lazygit is a fast, keyboard-driven terminal UI for git. "
        "Stage individual lines, manage branches, interactive rebase, "
        "stash management, and custom commands — all without leaving the terminal. "
        "Written in Go, works everywhere git does. "
        "53k+ GitHub stars; one of the most-starred developer tools on GitHub.",
        "developer-tools",
        "jesseduffield/lazygit",
        53000,
        "https://github.com/jesseduffield/lazygit",
        "git,tui,terminal,cli,developer,open-source",
        "brew install lazygit",
        "code",
    ),
    # Developer Tools — Atuin (shell history manager) -------------------------------------
    (
        "atuin",
        "Atuin",
        "Magical shell history",
        "Atuin replaces your shell history with a SQLite database, giving you "
        "fuzzy search, context-aware filtering, and optional encrypted sync across machines. "
        "Supports Bash, Zsh, Fish, and Nushell. "
        "Written in Rust for maximum speed — history search returns in milliseconds. "
        "22k+ GitHub stars.",
        "developer-tools",
        "atuinsh/atuin",
        22000,
        "https://atuin.sh",
        "shell,history,cli,terminal,rust,sync,developer,open-source",
        "bash <(curl --proto '=https' --tlsv1.2 -sSf https://setup.atuin.sh)",
        "code",
    ),
    # DevOps — Gitpod (cloud dev environments) -------------------------------------------
    (
        "gitpod",
        "Gitpod",
        "Always-ready, cloud-based dev environments",
        "Gitpod spins up fully configured, ephemeral dev environments in the cloud "
        "in seconds — directly from any GitHub, GitLab, or Bitbucket repo. "
        "Environments are defined as code (`.gitpod.yml`) and run in Docker containers. "
        "Supports VS Code in browser or desktop, JetBrains, Neovim, and custom IDEs. "
        "13k+ GitHub stars. Self-hostable with Gitpod Community edition.",
        "devops-infrastructure",
        "gitpod-io/gitpod",
        13000,
        "https://gitpod.io",
        "devops,cloud,dev-environment,docker,remote,ephemeral,open-source",
        "# Open any repo: gitpod.io/#https://github.com/your/repo",
        "saas",
    ),
    # Developer Tools — Dub (open-source link management) --------------------------------
    (
        "dub",
        "Dub",
        "Open-source link management for modern marketing teams",
        "Dub is an open-source Bitly alternative built for developers. "
        "Short links with analytics (clicks, referrers, geo, device), "
        "custom domains, QR codes, link expiration, and a TypeScript SDK. "
        "Self-hostable on Vercel + Upstash + Tinybird, or use Dub.co hosted. "
        "18k+ GitHub stars; widely used in SaaS boilerplates.",
        "developer-tools",
        "dubinc/dub",
        18000,
        "https://dub.co",
        "links,analytics,shortener,developer,saas,open-source,typescript",
        "npm install dub",
        "code",
    ),
    # AI Dev Tools — llama.cpp (local LLM inference engine) ------------------------------
    (
        "llamacpp",
        "llama.cpp",
        "LLM inference in C++ for CPU and GPU",
        "llama.cpp enables running large language models (LLaMA, Mistral, Gemma, Phi) "
        "locally on CPU or GPU with minimal setup. Written in C++, it supports GGUF "
        "quantised models, offers a REST API server mode, and powers most local LLM "
        "runners including LM Studio and Jan. The foundation of local AI development.",
        "ai-dev-tools",
        "ggerganov/llama.cpp",
        72000,
        "https://github.com/ggerganov/llama.cpp",
        "ai,llm,local,inference,cpp,gguf,quantization,open-source",
        "# Build from source or download binaries from GitHub Releases",
        "code",
    ),
    # API Tools — Bruno (open-source API testing) ----------------------------------------
    (
        "bruno",
        "Bruno",
        "Open-source API client for exploring and testing APIs",
        "Bruno is an offline-first, open-source Postman and Insomnia alternative. "
        "Collections are stored as plain text files (Bru format) directly in your repo — "
        "no cloud sync required. Supports REST, GraphQL, and gRPC. Native desktop app "
        "for Mac, Windows, and Linux. 28k+ GitHub stars.",
        "api-tools",
        "usebruno/bruno",
        28000,
        "https://usebruno.com",
        "api,testing,postman,rest,graphql,offline,open-source,developer",
        "# Download from https://usebruno.com or brew install bruno",
        "code",
    ),
    # Analytics & Metrics — Apache ECharts (data visualization) -------------------------
    (
        "echarts",
        "Apache ECharts",
        "An open-source JavaScript visualisation library",
        "Apache ECharts is a powerful, interactive chart library supporting line, bar, "
        "pie, scatter, map, heatmap, radar, tree, and 30+ chart types. Renders via Canvas "
        "or SVG, handles millions of data points, and is the most-used chart library in "
        "enterprise and Asian tech stacks. 60k+ GitHub stars.",
        "analytics-metrics",
        "apache/echarts",
        60000,
        "https://echarts.apache.org",
        "charts,visualization,data,canvas,svg,open-source,apache",
        "npm install echarts",
        "code",
    ),
    # API Tools — Phoenix Framework (Elixir web framework) ------------------------------
    (
        "phoenix",
        "Phoenix Framework",
        "Peace of mind from prototype to production",
        "Phoenix is a productive Elixir web framework built for real-time apps. "
        "Its Channels feature gives WebSocket-based pub/sub with millions of concurrent "
        "connections on a single server. Phoenix LiveView enables rich, reactive UIs "
        "without writing JavaScript. Widely praised for developer happiness and performance.",
        "api-tools",
        "phoenixframework/phoenix",
        21000,
        "https://phoenixframework.org",
        "elixir,realtime,websocket,liveview,pubsub,full-stack",
        "mix phx.new my_app",
        "code",
    ),
    # Message Queue — Centrifugo (real-time messaging server) ---------------------------
    (
        "centrifugo",
        "Centrifugo",
        "Scalable real-time messaging server",
        "Centrifugo is a language-agnostic open-source real-time messaging server. "
        "Supports WebSocket, HTTP-streaming, SSE, and GRPC. Handles pub/sub, presence, "
        "and history with Redis/Tarantool/Nats backends. Used in production by companies "
        "serving millions of connections. Self-hostable Pusher/Ably alternative.",
        "message-queue",
        "centrifugal/centrifugo",
        8200,
        "https://centrifugal.dev",
        "realtime,websocket,pubsub,sse,grpc,self-hosted,open-source",
        "docker run -d centrifugo/centrifugo",
        "code",
    ),
    # Developer Tools — Crawlee (web scraping and crawling framework by Apify) ----------
    (
        "crawlee",
        "Crawlee",
        "A web scraping and browser automation library",
        "Crawlee is Apify's open-source web scraping and browser automation library for "
        "Node.js and Python. Supports Cheerio, Playwright, and Puppeteer scrapers with "
        "built-in request queuing, proxy rotation, and session management. Perfect for "
        "building reliable scrapers that extract LLM-ready content at scale. 14k+ GitHub stars.",
        "developer-tools",
        "apify/crawlee",
        14000,
        "https://crawlee.dev",
        "scraping,crawling,playwright,puppeteer,cheerio,nodejs,typescript,open-source",
        "npm install crawlee",
        "code",
    ),
    # API Tools — Encore (backend framework with built-in infra) ------------------------
    (
        "encore",
        "Encore",
        "The backend framework with built-in infrastructure",
        "Encore is a TypeScript and Go backend framework that auto-provisions infrastructure "
        "(queues, caches, cron jobs, secrets, databases) from your code. Write infrastructure "
        "as type-safe functions; Encore generates cloud resources on AWS/GCP/Azure or deploys "
        "to Encore Cloud. Eliminates boilerplate Terraform and config. 10k+ GitHub stars.",
        "api-tools",
        "encoredev/encore",
        10000,
        "https://encore.dev",
        "backend,typescript,go,infrastructure,serverless,queues,open-source",
        "npm create encore@latest",
        "code",
    ),
    # Database — ElectricSQL (local-first Postgres sync) --------------------------------
    (
        "electricsql",
        "ElectricSQL",
        "Local-first sync layer for Postgres",
        "ElectricSQL is an open-source local-first sync engine that replicates Postgres "
        "data to client-side SQLite (in the browser or native apps) in real time. "
        "Build offline-capable apps with instant read performance. Sync is automatic and "
        "conflict-free. Used with React, SvelteKit, and Expo. 8k+ GitHub stars.",
        "database",
        "electric-sql/electric",
        8000,
        "https://electric-sql.com",
        "local-first,sync,postgres,sqlite,offline,realtime,open-source",
        "npm install electric-sql",
        "code",
    ),
    # Search — Pagefind (static site full-text search) ----------------------------------
    (
        "pagefind",
        "Pagefind",
        "Fully static search at scale",
        "Pagefind is a WebAssembly-powered static full-text search engine that runs entirely "
        "in the browser with no server required. Indexes your built site and ships a tiny "
        "search UI. Works with any static site generator (Astro, Hugo, Eleventy, Jekyll). "
        "Typical index: 300kB for a 10,000-page site. 4k+ GitHub stars.",
        "search-engine",
        "CloudCannon/pagefind",
        4000,
        "https://pagefind.app",
        "search,static-site,wasm,full-text,javascript,open-source",
        "npx pagefind --site public",
        "code",
    ),
    # Message Queue — Soketi (open-source Pusher-compatible WebSocket server) ----------
    (
        "soketi",
        "Soketi",
        "Open-source Pusher-compatible WebSocket server",
        "Soketi is a blazing-fast, open-source WebSocket server fully compatible with the "
        "Pusher client libraries. Drop-in replacement for Pusher Channels — point your "
        "existing Pusher SDK at Soketi and self-host. Built with uWebSockets.js for "
        "extreme performance. Works with Laravel Echo, React, Vue, and more. 5k+ GitHub stars.",
        "message-queue",
        "soketi/soketi",
        5000,
        "https://soketi.app",
        "websocket,pubsub,pusher,realtime,self-hosted,open-source,nodejs",
        "npm install -g @soketi/soketi",
        "code",
    ),
    # Monitoring — Uptime Kuma (self-hosted uptime monitoring) -------------------------
    (
        "uptime-kuma",
        "Uptime Kuma",
        "A fancy self-hosted monitoring tool",
        "Uptime Kuma is a self-hosted uptime monitoring tool similar to Uptime Robot. "
        "Monitors HTTP(S), TCP, DNS, Docker containers, and Steam game servers. "
        "Beautiful status pages, multi-channel notifications (Telegram, Discord, Slack, email), "
        "and a clean dashboard. Single Docker container, zero external dependencies. 60k+ stars.",
        "monitoring-uptime",
        "louislam/uptime-kuma",
        60000,
        "https://uptime.kuma.pet",
        "monitoring,uptime,self-hosted,docker,open-source,status-page",
        "docker run -d --restart=always -p 3001:3001 louislam/uptime-kuma:1",
        "code",
    ),
    # Testing — Ruff (Python linter + formatter in Rust) --------------------------------
    (
        "ruff",
        "Ruff",
        "An extremely fast Python linter and code formatter, written in Rust",
        "Ruff is a blazing-fast Python linter and formatter written in Rust — 10-100× faster "
        "than Flake8, Black, isort, and pylint combined. Drop-in replacement with a single "
        "pyproject.toml config. Supports 800+ lint rules (including Flake8, isort, pydocstyle, "
        "pyupgrade). The standard Python linting tool for modern projects. 34k+ GitHub stars.",
        "testing-tools",
        "astral-sh/ruff",
        34000,
        "https://astral.sh/ruff",
        "python,linter,formatter,fast,rust,flake8-alternative",
        "pip install ruff",
        "code",
    ),
    # Developer Tools — Pydantic (Python data validation) --------------------------------
    (
        "pydantic",
        "Pydantic",
        "Data validation using Python type hints",
        "Pydantic is the most widely used Python data validation library. Define data shapes "
        "with type hints, get automatic validation, serialization, and JSON schema generation. "
        "The foundation of FastAPI, LangChain, and thousands of Python applications. "
        "Pydantic v2 rewrites the core in Rust for 5-50× faster validation. 21k+ GitHub stars.",
        "developer-tools",
        "pydantic/pydantic",
        21000,
        "https://docs.pydantic.dev",
        "python,validation,types,serialization,fastapi,json-schema",
        "pip install pydantic",
        "code",
    ),
    # File Management — MinIO (S3-compatible object storage) ----------------------------
    (
        "minio",
        "MinIO",
        "High-performance, S3-compatible object storage",
        "MinIO is a high-performance, open-source object storage server fully compatible "
        "with the Amazon S3 API. Self-host on commodity hardware or Kubernetes. "
        "Write performance up to 325 GiB/s, read up to 165 GiB/s on a standard server. "
        "Powers AI/ML pipelines, data lakes, and cloud-native backup. 47k+ GitHub stars.",
        "file-management",
        "minio/minio",
        47000,
        "https://min.io",
        "s3,object-storage,self-hosted,open-source,kubernetes,data-lake",
        "docker run -p 9000:9000 -p 9001:9001 quay.io/minio/minio server /data --console-address ':9001'",
        "code",
    ),
    # API / Backend Frameworks — NestJS (TypeScript enterprise framework) ----------------
    (
        "nestjs",
        "NestJS",
        "A progressive Node.js framework for building efficient, reliable and scalable server-side applications",
        "NestJS is a TypeScript-first, opinionated Node.js backend framework heavily inspired "
        "by Angular's architecture. Uses decorators, dependency injection, and modular structure "
        "to build maintainable enterprise applications. First-class support for REST, GraphQL, "
        "WebSockets, microservices (gRPC, NATS, Redis, Kafka), and database integration "
        "via TypeORM, Prisma, or Mongoose. The dominant choice for large TypeScript backends. "
        "68k+ GitHub stars.",
        "api-tools",
        "nestjs/nest",
        68000,
        "https://nestjs.com",
        "nodejs,typescript,di,rest,graphql,microservices,decorators",
        "npm i -g @nestjs/cli && nest new project-name",
        "code",
    ),
    # Frontend — MobX (reactive state management) -----------------------------------------
    (
        "mobx",
        "MobX",
        "Simple, scalable state management",
        "MobX is a battle-tested reactive state management library. It uses observable state "
        "and computed values to automatically track dependencies and re-render only what's needed. "
        "Less boilerplate than Redux — annotate plain JavaScript objects with `@observable` "
        "and `@computed`. Works with React, Vue, and vanilla JS. "
        "Ideal for domain-rich, complex state models. 27k+ GitHub stars.",
        "frontend-frameworks",
        "mobxjs/mobx",
        27000,
        "https://mobx.js.org",
        "state-management,react,typescript,reactive,observable",
        "npm install mobx mobx-react-lite",
        "code",
    ),
    # API Tools — Apollo Client (GraphQL client) ------------------------------------------
    (
        "apollo-client",
        "Apollo Client",
        "A fully-featured, production-ready caching GraphQL client for JavaScript",
        "Apollo Client is the most popular GraphQL client for JavaScript and TypeScript. "
        "Normalised cache, automatic query batching, optimistic UI, real-time subscriptions "
        "via WebSocket, and first-class React hooks (`useQuery`, `useMutation`). "
        "Works with any GraphQL server — Hasura, Strawberry, Pothos, or custom schemas. "
        "Part of the Apollo GraphOS ecosystem. 19k+ GitHub stars.",
        "api-tools",
        "apollographql/apollo-client",
        19000,
        "https://apollographql.com/docs/react",
        "graphql,react,client,caching,subscriptions,typescript",
        "npm install @apollo/client graphql",
        "code",
    ),
    # AI Dev Tools — Vercel AI SDK --------------------------------------------------------
    (
        "vercel-ai-sdk",
        "Vercel AI SDK",
        "The AI Toolkit for TypeScript",
        "Vercel AI SDK (now simply 'AI SDK') is the standard toolkit for building AI-powered "
        "streaming UIs in TypeScript. Unified API for OpenAI, Anthropic, Google Gemini, Mistral, "
        "and 20+ providers. React/Next.js hooks for streaming text, structured output (with Zod), "
        "tool calling, and multi-step agents. Supports RSC streaming and edge runtime. "
        "The go-to SDK for AI chat apps, copilots, and generative UIs. 14k+ GitHub stars.",
        "ai-dev-tools",
        "vercel/ai",
        14000,
        "https://sdk.vercel.ai",
        "ai,llm,streaming,nextjs,react,openai,anthropic,typescript,structured-output",
        "npm install ai",
        "code",
    ),
    # Testing — k6 (load and performance testing) ----------------------------------------
    (
        "k6",
        "k6",
        "Modern load testing for developers and testers",
        "k6 is an open-source load testing tool by Grafana Labs. Write tests in JavaScript, "
        "run them locally or in Grafana Cloud. Supports HTTP/1.1, HTTP/2, WebSockets, gRPC, "
        "and browser testing (via Playwright integration). Scriptable, CI/CD-friendly, "
        "with rich metrics and thresholds. 25k+ GitHub stars.",
        "testing-tools",
        "grafana/k6",
        25000,
        "https://k6.io",
        "load-testing,performance,javascript,api-testing,grafana,open-source",
        "brew install k6",
        "code",
    ),
    # MCP Servers -----------------------------------------------------------------------
    (
        "mcp-filesystem",
        "Filesystem MCP Server",
        "Give AI agents secure read/write access to your local filesystem",
        "The official Model Context Protocol filesystem server from Anthropic. Exposes "
        "file system operations to AI agents — read files, write files, list directories, "
        "create/move/delete files, and search file contents. Supports configurable "
        "allowed-paths so agents are sandboxed to specific directories. The most widely "
        "used MCP server for giving AI coding agents access to project files. Part of the "
        "official modelcontextprotocol/servers monorepo (14k+ GitHub stars).",
        "mcp-servers",
        "modelcontextprotocol/servers",
        14000,
        "https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem",
        "mcp,filesystem,claude,ai-agent,model-context-protocol,anthropic",
        "npx @modelcontextprotocol/server-filesystem /path/to/allowed/dir",
        "code",
    ),
    (
        "mcp-github",
        "GitHub MCP Server",
        "Let AI agents read repos, issues, PRs, and code from GitHub",
        "Official MCP server for GitHub integration. Gives AI agents access to "
        "repository contents, file trees, commits, branches, issues, pull requests, "
        "and code search. Supports both public and private repos via GitHub personal "
        "access tokens. Essential for AI coding agents working with GitHub-hosted projects. "
        "Part of the official modelcontextprotocol/servers monorepo (14k+ GitHub stars).",
        "mcp-servers",
        "modelcontextprotocol/servers",
        14000,
        "https://github.com/modelcontextprotocol/servers/tree/main/src/github",
        "mcp,github,claude,ai-agent,model-context-protocol,code-review,issues",
        "npx @modelcontextprotocol/server-github",
        "code",
    ),
    (
        "mcp-postgres",
        "PostgreSQL MCP Server",
        "Give AI agents read access to your PostgreSQL database",
        "Official MCP server for PostgreSQL. Exposes database schema, table structures, "
        "and read-only query execution to AI agents. Agents can inspect tables, run "
        "SELECT queries, and understand your data model — without write access by default. "
        "Invaluable for AI agents helping debug queries, generate migrations, or answer "
        "questions about your data. Part of the official modelcontextprotocol/servers monorepo.",
        "mcp-servers",
        "modelcontextprotocol/servers",
        14000,
        "https://github.com/modelcontextprotocol/servers/tree/main/src/postgres",
        "mcp,postgresql,database,claude,ai-agent,model-context-protocol,sql",
        "npx @modelcontextprotocol/server-postgres postgresql://user:pass@localhost/mydb",
        "code",
    ),
    (
        "mcp-memory",
        "Memory MCP Server",
        "Give AI agents a persistent knowledge graph across conversations",
        "Official MCP server that gives AI agents a persistent memory store backed by "
        "a local knowledge graph. Agents can create, read, update, and delete entities "
        "and relations — letting them remember facts, preferences, and context across "
        "sessions. Built on a local JSON file store, no external dependencies. Ideal for "
        "building AI assistants that remember user context. Part of the official "
        "modelcontextprotocol/servers monorepo (14k+ GitHub stars).",
        "mcp-servers",
        "modelcontextprotocol/servers",
        14000,
        "https://github.com/modelcontextprotocol/servers/tree/main/src/memory",
        "mcp,memory,knowledge-graph,claude,ai-agent,model-context-protocol,persistence",
        "npx @modelcontextprotocol/server-memory",
        "code",
    ),
    (
        "mcp-fetch",
        "Fetch MCP Server",
        "Let AI agents fetch and read web pages and HTTP endpoints",
        "Official MCP server that gives AI agents the ability to fetch URLs and read "
        "web content. Supports HTML-to-Markdown conversion so agents can digest web "
        "pages cleanly, as well as raw response mode for JSON APIs. Handles redirects, "
        "custom headers, and basic authentication. The simplest way to give an agent "
        "access to external web data. Part of the official modelcontextprotocol/servers "
        "monorepo (14k+ GitHub stars).",
        "mcp-servers",
        "modelcontextprotocol/servers",
        14000,
        "https://github.com/modelcontextprotocol/servers/tree/main/src/fetch",
        "mcp,fetch,http,web,claude,ai-agent,model-context-protocol,scraping",
        "npx @modelcontextprotocol/server-fetch",
        "code",
    ),
    # AI — OCR ---------------------------------------------------------------
    (
        "tesseract-js",
        "Tesseract.js",
        "Pure JavaScript OCR for 100+ languages",
        "Tesseract.js is a pure JavaScript port of the Tesseract OCR engine. "
        "Recognises text in images across 100+ languages with no native dependencies. "
        "Works in the browser and Node.js. The go-to OCR library for JavaScript "
        "developers who need offline, server-side, or browser-based text extraction.",
        "ai-automation",
        "naptha/tesseract.js",
        34000,
        "https://tesseract.projectnaptha.com",
        "ocr,image,text-extraction,javascript,browser,nodejs",
        "npm install tesseract.js",
        "code",
    ),
    # Developer Tools — compression -------------------------------------------
    (
        "fflate",
        "fflate",
        "High performance (de)compression in an 8kB package",
        "fflate is the fastest pure-JavaScript compression library — significantly "
        "faster than pako, zlib.js, and JSZip. Supports DEFLATE, GZIP, ZLIB, and ZIP "
        "formats synchronously, asynchronously, and with streaming. Tree-shakeable, "
        "works in browsers and Node.js. The modern default for web compression.",
        "developer-tools",
        "101arrowz/fflate",
        3000,
        "https://101arrowz.github.io/fflate",
        "compression,deflate,gzip,zip,javascript,browser,nodejs,wasm",
        "npm install fflate",
        "code",
    ),
    # Developer Tools — phone number ------------------------------------------
    (
        "libphonenumber-js",
        "libphonenumber-js",
        "Parse, format and validate phone numbers in any country",
        "A JavaScript port of Google's libphonenumber library. Validates, parses, "
        "formats, and normalizes phone numbers for 240+ countries. Supports E.164 "
        "formatting, national/international display formats, and carrier detection. "
        "Tree-shakeable and available as a lightweight build for browser use.",
        "developer-tools",
        "catamphetamine/libphonenumber-js",
        5000,
        "https://github.com/catamphetamine/libphonenumber-js",
        "phone,phone-number,validation,formatting,e164,google-libphonenumber",
        "npm install libphonenumber-js",
        "code",
    ),
    # Developer Tools — template engines ---------------------------------------
    (
        "handlebars",
        "Handlebars.js",
        "Minimal templating on steroids",
        "Handlebars.js is a minimal, logic-less template engine for JavaScript. "
        "Extends Mustache syntax with helpers, partials, and block expressions. "
        "Used in Express.js, Ember.js, and thousands of email and HTML templating "
        "pipelines. Compiles templates to optimised JavaScript functions.",
        "developer-tools",
        "handlebars-lang/handlebars.js",
        18000,
        "https://handlebarsjs.com",
        "template-engine,handlebars,javascript,mustache,html",
        "npm install handlebars",
        "code",
    ),
    # Developer Tools — datetime / timezone -----------------------------------
    (
        "luxon",
        "Luxon",
        "A powerful, modern, and friendly wrapper for JavaScript dates and times",
        "Luxon is an immutable datetime library built by one of the Moment.js authors "
        "as its spiritual successor. Provides a clean, chainable API for parsing, "
        "formatting, arithmetic, and timezone/locale handling. Backed by the Intl API "
        "for native timezone support — no tzdata bundle required.",
        "developer-tools",
        "moment/luxon",
        15000,
        "https://moment.github.io/luxon",
        "datetime,timezone,date,time,javascript,intl,immutable",
        "npm install luxon",
        "code",
    ),
    # Maps & Location — interactive mapping libraries --------------------------
    (
        "leaflet",
        "Leaflet.js",
        "The leading open-source JavaScript library for mobile-friendly interactive maps",
        "Leaflet is the most popular open-source JavaScript library for mobile-friendly "
        "interactive maps. Weighing just 42 KB of JS, it has all the mapping features "
        "most developers ever need. Works with OpenStreetMap, Mapbox, and any tile "
        "provider. Extensible via 300+ plugins.",
        "maps-location",
        "Leaflet/Leaflet",
        41000,
        "https://leafletjs.com",
        "maps,geolocation,javascript,openstreetmap,mobile",
        "npm install leaflet",
        "code",
    ),
    # API Tools — REST/GraphQL/gRPC clients ------------------------------------
    (
        "insomnia",
        "Insomnia",
        "The collaborative API client for REST, GraphQL, gRPC, and more",
        "Insomnia is Kong's open-source API client for designing, debugging, and "
        "testing REST, GraphQL, WebSockets, Server-Sent Events, and gRPC requests. "
        "Supports environments, test suites, Git sync, and team collaboration. "
        "Available as desktop app (Mac/Windows/Linux) and CLI.",
        "api-tools",
        "Kong/insomnia",
        34000,
        "https://insomnia.rest",
        "api-client,rest,graphql,grpc,testing,http",
        "brew install insomnia",
        "code",
    ),
    (
        "scalar",
        "Scalar",
        "Beautiful API references from OpenAPI/Swagger files",
        "Scalar generates modern, interactive API reference documentation from "
        "OpenAPI/Swagger specs. Drop-in replacement for Swagger UI and ReDoc. "
        "Includes an embedded API client for testing. Integrates with FastAPI, "
        "Hono, Express, Nitro, and any OpenAPI provider.",
        "api-tools",
        "scalar/scalar",
        30000,
        "https://scalar.com",
        "openapi,api-docs,swagger,documentation,api-client",
        "npm install @scalar/api-reference",
        "code",
    ),
    # Database — schema migration tools ----------------------------------------
    (
        "atlas",
        "Atlas",
        "Manage your database schema as code",
        "Atlas is a language-agnostic schema-as-code tool for managing and migrating "
        "database schemas. Supports PostgreSQL, MySQL, MariaDB, SQLite, and more. "
        "Declarative and versioned migration workflows, with automatic migration "
        "planning and CI enforcement. Built by the Ariga team.",
        "database",
        "ariga/atlas",
        6000,
        "https://atlasgo.io",
        "database,migrations,schema,postgresql,mysql,sqlite",
        "curl -sSf https://atlasgo.sh | sh",
        "code",
    ),
    # Project Management — open-source alternatives ----------------------------
    (
        "plane",
        "Plane",
        "The open-source project management tool",
        "Plane is an open-source software project management tool for issues, cycles, "
        "and modules — a Jira and Linear alternative. Self-hostable or cloud-hosted. "
        "Supports Kanban boards, sprints, roadmaps, and GitHub integration. "
        "Built with Next.js and Python/Django.",
        "project-management",
        "makeplane/plane",
        31000,
        "https://plane.so",
        "project-management,kanban,issues,self-hosted,open-source",
        "docker compose up -d",
        "code",
    ),
    # API Tools — open-source Postman alternatives -----------------------------
    (
        "hoppscotch",
        "Hoppscotch",
        "Open source API development ecosystem",
        "Hoppscotch is a lightweight, web-based API development suite — an open-source "
        "Postman alternative. Test REST, GraphQL, WebSocket, SSE, and Socket.IO "
        "endpoints directly in the browser. Supports teams, environments, collections, "
        "and self-hosting. Built with Vue.js and available as a desktop app.",
        "api-tools",
        "hoppscotch/hoppscotch",
        60000,
        "https://hoppscotch.io",
        "api-client,rest,graphql,websocket,postman-alternative,open-source",
        "docker run --rm -it hoppscotch/hoppscotch",
        "code",
    ),
    # Database — TypeScript ORMs / query builders (major catalog gap) ----------
    (
        "drizzle",
        "Drizzle ORM",
        "Headless TypeScript ORM with a head",
        "Drizzle ORM is a lightweight, performant TypeScript ORM that feels like "
        "writing SQL, not fighting an abstraction layer. Zero dependencies, full "
        "type inference, works with PostgreSQL, MySQL, SQLite, and every major "
        "serverless runtime (Neon, Turso, Cloudflare D1, Bun). Pairs naturally "
        "with Drizzle Kit for schema migrations.",
        "database",
        "drizzle-team/drizzle-orm",
        25000,
        "https://orm.drizzle.team",
        "orm,typescript,postgresql,mysql,sqlite,serverless,type-safe",
        "npm install drizzle-orm",
        "code",
    ),
    # Database — Python ORMs for FastAPI / async stacks -----------------------
    (
        "sqlmodel",
        "SQLModel",
        "SQL databases in Python, designed for simplicity and compatibility",
        "SQLModel is a library for interacting with SQL databases from Python code, "
        "with Python objects. Designed by the creator of FastAPI, it combines "
        "SQLAlchemy and Pydantic. Write your database models once and get full "
        "editor support, data validation, and an ORM — with zero boilerplate.",
        "database",
        "tiangolo/sqlmodel",
        14000,
        "https://sqlmodel.tiangolo.com",
        "orm,python,fastapi,pydantic,sqlalchemy,type-safe",
        "pip install sqlmodel",
        "code",
    ),
    # Payments — open-source payments for OSS developers ----------------------
    (
        "polar",
        "Polar.sh",
        "Open source monetization for developers",
        "Polar is an open-source platform for software developers to monetize their "
        "work. Create and sell subscriptions, one-time products, and GitHub-sponsored "
        "tiers. Built-in license key management, file downloads, and Discord role "
        "rewards. Simple checkout flow and developer-first API. "
        "A Stripe-backed, indie-friendly Gumroad/Lemon Squeezy alternative.",
        "payments",
        "polarsource/polar",
        5000,
        "https://polar.sh",
        "payments,subscriptions,oss,open-source,stripe,developer,monetization",
        "pip install polar-sdk",
        "code",
    ),
    # Developer Tools — TypeScript functional programming ---------------------
    (
        "effect",
        "Effect",
        "The missing standard library for TypeScript",
        "Effect is a powerful TypeScript library for building complex, production-grade "
        "applications. It provides a structured approach to handling errors, async "
        "operations, dependency injection, and resource management — all fully "
        "type-safe. Think Rust's Result type plus structured concurrency plus DI, "
        "all in idiomatic TypeScript.",
        "developer-tools",
        "Effect-TS/effect",
        8000,
        "https://effect.website",
        "typescript,functional,fp,error-handling,dependency-injection,concurrency",
        "npm install effect",
        "code",
    ),
    # API Tools — realtime multiplayer infrastructure -------------------------
    (
        "partykit",
        "PartyKit",
        "Build realtime multiplayer applications",
        "PartyKit is a platform and SDK for building multiplayer collaborative "
        "applications, live cursors, shared state, and real-time features at the "
        "edge. Deploy stateful WebSocket servers to Cloudflare's network in "
        "seconds. Pairs naturally with Y.js and Liveblocks-style CRDT patterns.",
        "api-tools",
        "partykit/partykit",
        4000,
        "https://partykit.io",
        "realtime,multiplayer,websocket,collaborative,cloudflare,edge",
        "npm install partykit",
        "code",
    ),
    # API Tools — realtime video/audio infrastructure -------------------------
    (
        "livekit",
        "LiveKit",
        "Open-source infrastructure for real-time video, audio, and data",
        "LiveKit is an open-source WebRTC stack for building live video, audio, and "
        "data streaming applications. Scalable media server (Go), SDKs for every major "
        "platform (React, iOS, Android, Python, Unity), and cloud hosting. Used for "
        "video conferencing, live streaming, voice AI, and real-time collaboration.",
        "api-tools",
        "livekit/livekit",
        12000,
        "https://livekit.io",
        "webrtc,realtime,video,audio,streaming,voice-ai",
        "pip install livekit",
        "code",
    ),
    # AI / LLM agent frameworks ------------------------------------------------
    (
        "pydantic-ai",
        "Pydantic AI",
        "Agent framework from the Pydantic team, built for production",
        "Pydantic AI is a Python AI agent framework by the team behind Pydantic and "
        "FastAPI. Structured outputs via Pydantic models, dependency injection, "
        "multi-model support (OpenAI, Anthropic, Gemini, Groq, Mistral), streaming, "
        "and built-in testing utilities. Designed for production Python apps.",
        "ai-automation",
        "pydantic/pydantic-ai",
        7000,
        "https://ai.pydantic.dev",
        "ai,agent,python,pydantic,llm,structured-output",
        "pip install pydantic-ai",
        "code",
    ),
    # Developer Tools — package managers and JS toolchains ----------------------
    (
        "pnpm",
        "pnpm",
        "Fast, disk-space-efficient package manager",
        "pnpm is a fast, disk-space-efficient Node.js package manager that uses "
        "hard links and symlinks to share packages across projects. Up to 2× faster "
        "than npm and saves gigabytes of disk space via a global content-addressable "
        "store. Supports workspaces for monorepos out of the box.",
        "frontend-frameworks",
        "pnpm/pnpm",
        30000,
        "https://pnpm.io",
        "package-manager,npm,monorepo,workspace,fast",
        "npm install -g pnpm",
        "code",
    ),
    (
        "yarn-berry",
        "Yarn Berry",
        "Fast, reliable, and secure JavaScript package manager",
        "Yarn Berry (Yarn 2+) is a modern package manager with Plug'n'Play "
        "(PnP) installs that eliminate node_modules entirely, built-in workspace "
        "support, zero-installs via cached packages in version control, and "
        "first-class monorepo tooling with workspaces and constraints.",
        "frontend-frameworks",
        "yarnpkg/berry",
        7500,
        "https://yarnpkg.com",
        "package-manager,npm,pnp,zero-install,monorepo",
        "npm install -g yarn",
        "code",
    ),
    (
        "volta",
        "Volta",
        "The Hassle-Free JavaScript Tool Manager",
        "Volta is a JavaScript toolchain manager written in Rust that lets you "
        "pin exact Node.js, npm, Yarn, and package binary versions per project. "
        "No more manual nvm use — Volta switches automatically based on your "
        "package.json. Works on macOS, Linux, and Windows.",
        "developer-tools",
        "volta-cli/volta",
        11000,
        "https://volta.sh",
        "node-version-manager,toolchain,javascript,version-manager",
        "curl https://get.volta.sh | bash",
        "code",
    ),
    (
        "mise",
        "mise-en-place",
        "The front-end to your dev env (asdf alternative)",
        "mise is a polyglot runtime version manager written in Rust. It manages "
        "versions of Node.js, Python, Ruby, Go, Rust, Java, and 600+ plugins — "
        "and replaces both asdf and direnv. Activates automatically via shell "
        "hooks. Compatible with .tool-versions (asdf format) and .mise.toml.",
        "developer-tools",
        "jdx/mise",
        12000,
        "https://mise.jdx.dev",
        "version-manager,runtime,polyglot,asdf,node,python",
        "curl https://mise.run | sh",
        "code",
    ),
    (
        "nvm",
        "nvm",
        "Node Version Manager — manage multiple Node.js versions",
        "nvm (Node Version Manager) is a POSIX-compliant bash script to manage "
        "multiple Node.js versions per user. Install any Node.js version, switch "
        "instantly with nvm use, and set defaults per project via .nvmrc files. "
        "The most-installed Node version manager with 80k+ GitHub stars.",
        "developer-tools",
        "nvm-sh/nvm",
        80000,
        "https://github.com/nvm-sh/nvm",
        "node-version-manager,version-manager,node,bash",
        "curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash",
        "code",
    ),
    # Database — time-series databases ------------------------------------------
    (
        "influxdb",
        "InfluxDB",
        "Scalable time-series database for metrics and events",
        "InfluxDB is the most widely used open-source time-series database. "
        "Store and query metrics, events, traces, and logs at scale. InfluxDB 3 "
        "introduces a columnar storage engine on top of Apache Arrow and Parquet, "
        "with SQL and InfluxQL query interfaces. Cloud and self-hosted options.",
        "database",
        "influxdata/influxdb",
        28000,
        "https://www.influxdata.com",
        "timeseries,metrics,monitoring,observability,sql,events",
        "docker run -p 8086:8086 influxdb:latest",
        "code",
    ),
    (
        "questdb",
        "QuestDB",
        "Fast open-source time-series database for analytics",
        "QuestDB is a high-performance time-series database written in Java with "
        "a zero-GC core. Ingests millions of rows per second via the InfluxDB line "
        "protocol, PostgreSQL wire protocol, or REST API. SQL-native with "
        "time-series extensions (SAMPLE BY, LATEST ON, ASOF JOIN). Used for "
        "financial data, IoT, monitoring, and DevOps analytics.",
        "database",
        "questdb/questdb",
        14000,
        "https://questdb.io",
        "timeseries,sql,fast,analytics,influxdb,metrics",
        "docker run -p 8812:8812 -p 9000:9000 questdb/questdb",
        "code",
    ),
    # DevOps — open-source Terraform replacement --------------------------------
    (
        "opentofu",
        "OpenTofu",
        "Open-source Terraform fork by the community",
        "OpenTofu is an open-source infrastructure-as-code tool and a community-led "
        "fork of Terraform, maintained under the CNCF. It is a drop-in replacement "
        "for Terraform — same HCL syntax, same provider ecosystem, same workflows — "
        "without the Business Source License restrictions. Write declarative "
        "infrastructure for AWS, GCP, Azure, and 3,000+ providers. Features "
        "state encryption, provider-defined functions, and an active roadmap.",
        "devops-infrastructure",
        "opentofu/opentofu",
        22000,
        "https://opentofu.org",
        "iac,terraform,infrastructure-as-code,hcl,open-source,cncf",
        "brew install opentofu",
        "code",
    ),
    # Frontend — htmx (HTML-first progressive enhancement) -----------------------
    (
        "htmx",
        "htmx",
        "High power tools for HTML — AJAX, WebSockets, and Server-Sent Events via HTML attributes",
        "htmx gives you access to AJAX, CSS Transitions, WebSockets, and Server-Sent "
        "Events directly in HTML, using attributes. It lets you build modern UIs with "
        "the simplicity and power of hypertext. No JavaScript build step required — "
        "just include the single-file library and add hx-* attributes to any element. "
        "htmx works with any backend (Python, Go, Rails, PHP, Node.js) and integrates "
        "beautifully with Alpine.js for client-side interactions. 40k GitHub stars.",
        "frontend-frameworks",
        "bigskysoftware/htmx",
        40000,
        "https://htmx.org",
        "htmx,html,ajax,hypermedia,progressive-enhancement,no-build,python,go",
        "<script src=\"https://unpkg.com/htmx.org\"></script>",
        "code",
    ),
    # Frontend — Qwik (resumable JS framework) -----------------------------------
    (
        "qwik",
        "Qwik",
        "No hydration, no replay — the resumable JavaScript framework",
        "Qwik is a new kind of web framework built for the edge that delivers instant "
        "app startup performance regardless of application complexity. Unlike other "
        "frameworks, Qwik does not need to hydrate — instead it serializes state and "
        "resumes execution directly on the client, loading only the code needed for "
        "the current interaction. Built by the team behind Angular, QwikCity is the "
        "meta-framework with file-based routing, server actions, and Vite integration. "
        "Outstanding Core Web Vitals scores out of the box.",
        "frontend-frameworks",
        "QwikDev/qwik",
        21000,
        "https://qwik.dev",
        "qwik,resumable,ssr,edge,performance,react,typescript",
        "npm create qwik@latest",
        "code",
    ),
    # Search — Typesense (typo-tolerant open-source search engine) ---------------
    (
        "typesense",
        "Typesense",
        "Open-source, typo-tolerant search engine — a blazing fast Algolia alternative",
        "Typesense is an open-source, typo-tolerant search engine optimised for "
        "developer productivity and low operational overhead. It supports instant "
        "search-as-you-type, multi-tenant API keys, geo search, faceted filtering, "
        "vector search, and hybrid search in a single binary. Can be self-hosted or "
        "used via Typesense Cloud. Official SDKs for JavaScript, Python, Go, PHP, "
        "Ruby, Java, and more. Much simpler to operate than Elasticsearch and often "
        "faster than Algolia with no per-query pricing.",
        "search-engine",
        "typesense/typesense",
        21000,
        "https://typesense.org",
        "search,typesense,algolia-alternative,typo-tolerant,open-source,vector-search",
        "docker run -p 8108:8108 -v/tmp/typesense-data:/data typesense/typesense:latest",
        "code",
    ),
    # Frontend — Preact (lightweight React alternative) --------------------------
    (
        "preact",
        "Preact",
        "Fast 3kB alternative to React with the same modern API",
        "Preact is a fast, 3kB alternative to React with the same ES2015 API. It "
        "provides the thinnest possible Virtual DOM abstraction on top of the DOM and "
        "is compatible with the entire React ecosystem via preact/compat. Preact is "
        "used in production by large companies including Etsy, The Guardian, and Uber "
        "who need React compatibility with a much smaller bundle. Includes hooks, "
        "signals (a new reactive primitive), async rendering, and Preact CLI for "
        "rapid application development.",
        "frontend-frameworks",
        "preactjs/preact",
        36000,
        "https://preactjs.com",
        "preact,react,lightweight,virtual-dom,3kb,performance,signals",
        "npm install preact",
        "code",
    ),
    # Frontend — Lottie Web (JSON-based animation library) -----------------------
    (
        "lottie",
        "Lottie Web",
        "Render After Effects animations natively in the browser with minimal effort",
        "Lottie is an open-source animation library by Airbnb that parses Adobe After "
        "Effects animations exported as JSON with Bodymovin and renders them natively "
        "on mobile and on the web. Designers can create and ship beautiful animations "
        "without an engineer needing to recreate them. The DotLottie format adds "
        "compression, theming, and interactive state machines. Widely used by "
        "Duolingo, Google, and thousands of indie apps for splash screens, "
        "micro-interactions, and loading animations.",
        "frontend-frameworks",
        "airbnb/lottie-web",
        30000,
        "https://lottiefiles.com/lottie-docs",
        "lottie,animation,json,after-effects,airbnb,mobile,ios,android,web",
        "npm install lottie-web",
        "code",
    ),
    # AI Dev Tools — LLM eval, observability, data labeling ----------------------
    (
        "promptfoo",
        "promptfoo",
        "Test and evaluate LLM prompts, models, and RAG pipelines",
        "promptfoo is an open-source CLI and library for testing and evaluating LLM "
        "outputs. Run automated evals across prompts, models (OpenAI, Anthropic, "
        "Gemini, Mistral, local models), and configurations. Supports unit tests, "
        "red-teaming for safety, and regression testing to prevent prompt regressions "
        "between deploys. Used by engineering teams at Shopify, Mozilla, and others "
        "to ship LLM features with confidence. Define test cases in YAML or JSON, "
        "run with `promptfoo eval`, view results in an interactive web UI.",
        "ai-dev-tools",
        "promptfoo/promptfoo",
        5000,
        "https://promptfoo.dev",
        "llm,evals,testing,prompt-testing,red-team,rag,ai-safety,openai,anthropic",
        "npm install -g promptfoo",
        "code",
    ),
    (
        "deepeval",
        "DeepEval",
        "The open-source LLM evaluation framework",
        "DeepEval is an open-source evaluation framework for LLM applications. "
        "Provides 14+ evaluation metrics out of the box: G-Eval, RAGAS, hallucination, "
        "faithfulness, contextual recall/precision, bias, toxicity, and more. "
        "Works with any LLM provider. Integrates with pytest for CI-based evals. "
        "Confident AI dashboard for tracking metric scores over time. Ideal for "
        "teams building RAG pipelines, chatbots, or AI agents who need systematic "
        "quality assurance beyond ad-hoc manual testing.",
        "ai-dev-tools",
        "confident-ai/deepeval",
        7000,
        "https://docs.confident-ai.com",
        "llm,evals,evaluation,rag,hallucination,testing,pytest,metrics,ragas",
        "pip install deepeval",
        "code",
    ),
    (
        "helicone",
        "Helicone",
        "Open-source LLM observability — one line to log every request",
        "Helicone is an open-source LLM observability platform. Add a single line "
        "to proxy your OpenAI/Anthropic/Mistral requests through Helicone and get "
        "full request/response logging, cost tracking, latency analytics, prompt "
        "versioning, user-level analytics, caching, and rate limiting. "
        "Self-hostable on Fly.io, Vercel, or Cloudflare Workers. Generous free tier "
        "on Helicone Cloud. Lighter-weight than Langfuse — no SDK wrapping required, "
        "just change your base_url.",
        "ai-dev-tools",
        "Helicone/helicone",
        2000,
        "https://helicone.ai",
        "llm,observability,logging,openai,anthropic,cost-tracking,caching,proxy",
        "pip install helicone",
        "code",
    ),
    (
        "label-studio",
        "Label Studio",
        "Open source data labeling platform for any AI use case",
        "Label Studio is the most popular open-source data annotation and labeling "
        "platform. Supports image, audio, text, video, time series, and multi-modal "
        "data. Features 10+ labeling interfaces: bounding boxes, polygons, named "
        "entity recognition, relation extraction, audio transcription, and more. "
        "Multi-user workflows with review/approval queues, ML backend auto-labeling, "
        "and export to common ML formats (COCO, YOLO, NLP JSON). Self-hostable with "
        "Docker. Used by ML teams at NVIDIA, Toyota, and thousands of startups for "
        "fine-tuning and RLHF datasets.",
        "ai-dev-tools",
        "HumanSignal/label-studio",
        21000,
        "https://labelstud.io",
        "data-labeling,annotation,ml,computer-vision,nlp,rlhf,fine-tuning,active-learning",
        "pip install label-studio && label-studio",
        "code",
    ),
    # Message Queue — NATS (cloud-native messaging system) -----------------------
    (
        "nats",
        "NATS",
        "Connective technology for adaptive edge and distributed systems",
        "NATS is a connective technology built for the ever-increasingly hyper-connected "
        "world. It is a simple, secure, and high-performance open-source messaging "
        "system for cloud-native applications, IoT messaging, and microservices "
        "architectures. NATS.io is a CNCF incubating project. Supports publish-subscribe, "
        "request-reply, and queue groups. JetStream adds persistence, key-value store, "
        "object store, and at-least-once delivery. Faster than Kafka for small messages "
        "and much simpler to operate.",
        "message-queue",
        "nats-io/nats-server",
        15000,
        "https://nats.io",
        "nats,messaging,pubsub,cloud-native,iot,microservices,jetstream,cncf",
        "docker run nats",
        "code",
    ),
    # Vector databases — AI / RAG pipelines ------------------------------------------
    (
        "chroma",
        "Chroma",
        "The AI-native open-source embedding database",
        "Chroma is an open-source embedding database purpose-built for AI applications. "
        "Store, embed, and query documents with metadata filtering. The go-to "
        "local-first vector store for LangChain, LlamaIndex, and RAG prototyping. "
        "Scales from local dev to self-hosted production.",
        "database",
        "chroma-core/chroma",
        15000,
        "https://trychroma.com",
        "vector-database,embeddings,rag,langchain,local-first",
        "pip install chromadb",
        "code",
    ),
    # Message queues — the two most-searched message brokers -------------------------
    (
        "apache-kafka",
        "Apache Kafka",
        "The open-source distributed event streaming platform",
        "Apache Kafka is the dominant event streaming platform. Publish, subscribe, "
        "store, and process streams of records with high throughput and low latency. "
        "Powers real-time data pipelines, event-driven microservices, and stream "
        "processing at every major tech company. CNCF graduated project.",
        "message-queue",
        "apache/kafka",
        28000,
        "https://kafka.apache.org",
        "message-queue,event-streaming,pubsub,distributed,real-time",
        "docker run -p 9092:9092 apache/kafka",
        "code",
    ),
    (
        "rabbitmq",
        "RabbitMQ",
        "The most widely deployed open-source message broker",
        "RabbitMQ is a battle-tested message broker supporting AMQP, MQTT, and STOMP. "
        "Routes messages between producers and consumers with queues, exchanges, "
        "and bindings. Supports clustering, federation, and high availability. "
        "The canonical choice for task queues and service decoupling.",
        "message-queue",
        "rabbitmq/rabbitmq-server",
        12000,
        "https://rabbitmq.com",
        "message-broker,amqp,queues,distributed,celery",
        "docker run -p 5672:5672 rabbitmq",
        "code",
    ),
    # Background jobs — ELT / data integration -------------------------------------
    (
        "airbyte",
        "Airbyte",
        "Open-source data integration platform — 400+ connectors",
        "Airbyte is the leading open-source ELT platform. Move data from 400+ "
        "sources (Postgres, Salesforce, Stripe, Google Sheets, and more) to any "
        "destination warehouse or lake. Deploy self-hosted on Docker/Kubernetes "
        "or use Airbyte Cloud. No-code + low-code + custom connector support.",
        "background-jobs",
        "airbytehq/airbyte",
        17000,
        "https://airbyte.com",
        "etl,elt,data-integration,connectors,self-hosted,warehouse",
        "docker compose up",
        "code",
    ),
    # Rust WASM frontend frameworks — rapidly growing query segment ------------------
    (
        "leptos",
        "Leptos",
        "Build fast web applications with Rust and WebAssembly",
        "Leptos is a full-stack, isomorphic Rust web framework leveraging fine-grained "
        "reactivity to build declarative user interfaces. Compile to WASM for the browser "
        "or run server-side. Supports SSR, hydration, server functions, and SPA mode. "
        "Emerging as the Rust answer to SolidJS and Next.js.",
        "frontend-frameworks",
        "leptos-rs/leptos",
        16000,
        "https://leptos.dev",
        "rust,wasm,webassembly,fullstack,ssr,reactive",
        "cargo add leptos",
        "code",
    ),
    (
        "yew",
        "Yew",
        "Rust / Wasm framework for building client web apps",
        "Yew is a modern Rust framework for creating multi-threaded front-end web apps "
        "using WebAssembly. Component-based design inspired by Elm and React. Supports "
        "JavaScript interoperability and reuse of NPM packages. Battle-tested and "
        "the most mature Rust+WASM frontend framework.",
        "frontend-frameworks",
        "yewstack/yew",
        30000,
        "https://yew.rs",
        "rust,wasm,webassembly,components,frontend",
        "cargo add yew",
        "code",
    ),
    (
        "dioxus",
        "Dioxus",
        "Fullstack GUI library for web, desktop, and mobile in Rust",
        "Dioxus is a portable, performant, and ergonomic framework for building "
        "cross-platform apps in Rust. Write once, deploy to web (WASM), desktop "
        "(native), mobile (iOS/Android), and TUI targets. React-inspired component "
        "model with a simple hook system and built-in routing and state management.",
        "frontend-frameworks",
        "DioxusLabs/dioxus",
        18000,
        "https://dioxuslabs.com",
        "rust,wasm,cross-platform,desktop,mobile,web,fullstack",
        "cargo add dioxus",
        "code",
    ),
    # CSS frameworks / atomic CSS --------------------------------------------------
    (
        "unocss",
        "UnoCSS",
        "The instant on-demand atomic CSS engine",
        "UnoCSS is a highly customisable and performant atomic CSS engine. "
        "Near-instant build times by generating only the CSS you use. Compatible "
        "with Tailwind, Windi CSS, and Bootstrap presets. Powers many Vite and "
        "Nuxt applications as a drop-in Tailwind replacement.",
        "frontend-frameworks",
        "unocss/unocss",
        17000,
        "https://unocss.dev",
        "css,atomic-css,tailwind,utility-first,vite",
        "npm install -D unocss",
        "code",
    ),
    # Local Kubernetes dev tools ---------------------------------------------------
    (
        "minikube",
        "Minikube",
        "Local Kubernetes, focused on making Kubernetes easy to learn and develop for",
        "Minikube implements a local Kubernetes cluster on macOS, Linux, and Windows. "
        "The primary goals are to be the best tool for local Kubernetes application "
        "development and to support all Kubernetes features that fit. Supports "
        "multiple container runtimes (Docker, containerd, CRI-O).",
        "devops-infrastructure",
        "kubernetes/minikube",
        29000,
        "https://minikube.sigs.k8s.io",
        "kubernetes,k8s,local-dev,containers,devops",
        "minikube start",
        "code",
    ),
    (
        "k3s",
        "K3s",
        "Lightweight Kubernetes — production-ready distribution for resource-constrained environments",
        "K3s is a highly available, certified Kubernetes distribution designed for "
        "production workloads in resource-constrained environments. Single binary under "
        "70MB, built-in containerd, SQLite or etcd backends, and automatic TLS "
        "management. Created by Rancher Labs, now a CNCF Sandbox project.",
        "devops-infrastructure",
        "k3s-io/k3s",
        28000,
        "https://k3s.io",
        "kubernetes,k8s,lightweight,edge,iot,arm,devops",
        "curl -sfL https://get.k3s.io | sh -",
        "code",
    ),
    # Node.js backend frameworks ---------------------------------------------------
    (
        "adonisjs",
        "AdonisJS",
        "A fully-featured Node.js web framework with a focus on developer ergonomics",
        "AdonisJS is a batteries-included MVC framework for Node.js and TypeScript. "
        "Inspired by Laravel, it ships with an ORM (Lucid), authentication, mailer, "
        "file storage, and a first-class CLI. Ideal for server-rendered apps and "
        "JSON APIs that want structure without configuration overhead.",
        "api-tools",
        "adonisjs/core",
        17000,
        "https://adonisjs.com",
        "nodejs,typescript,mvc,fullstack,orm,laravel-like",
        "npm init adonisjs@latest my-app",
        "code",
    ),
    # Kubernetes tooling -------------------------------------------------------
    (
        "k9s",
        "k9s",
        "Kubernetes CLI To Manage Your Clusters In Style",
        "k9s is a terminal-based UI to interact with your Kubernetes clusters. "
        "Navigate, observe, and manage your deployed applications from the comfort "
        "of your terminal. k9s provides a visual interface to your Kubernetes cluster, "
        "allowing you to quickly navigate between resources, view logs, exec into pods, "
        "and manage workloads — all without kubectl muscle memory.",
        "devops-infrastructure",
        "derailed/k9s",
        27000,
        "https://k9scli.io",
        "kubernetes,k8s,tui,terminal,devops,cli,dashboard",
        "brew install derailed/k9s/k9s",
        "code",
    ),
    (
        "kustomize",
        "Kustomize",
        "Kubernetes-native configuration management",
        "Kustomize introduces a template-free way to customize application configuration "
        "that simplifies the use of off-the-shelf applications. Built into kubectl as "
        "`kubectl apply -k`, it lets you overlay patches on top of base Kubernetes configs "
        "without forking — perfect for managing dev/staging/prod variants.",
        "devops-infrastructure",
        "kubernetes-sigs/kustomize",
        11000,
        "https://kustomize.io",
        "kubernetes,k8s,configuration,gitops,devops,overlay",
        "brew install kustomize",
        "code",
    ),
    # Headless CMS -------------------------------------------------------------
    (
        "tinacms",
        "TinaCMS",
        "Open-source headless CMS with Git-backed content and visual editing",
        "TinaCMS is a fully open-source headless CMS that stores content in your "
        "Git repository as Markdown, MDX, or JSON. It offers a visual editing "
        "experience in-context of your site (React-based), a type-safe content "
        "client, and a cloud-hosted dashboard — all with no vendor lock-in.",
        "headless-cms",
        "tinacms/tinacms",
        12000,
        "https://tina.io",
        "cms,headless,git-backed,markdown,mdx,react,visual-editor,open-source",
        "npx create-tina-app@latest",
        "code",
    ),
    # Database -----------------------------------------------------------------
    (
        "arangodb",
        "ArangoDB",
        "Multi-model NoSQL database with graphs, documents, and key-value",
        "ArangoDB is a native multi-model database combining the flexibility of "
        "graphs, documents, and key-value pairs in a single engine with one query "
        "language (AQL). Use it for graph analytics, complex relation traversals, "
        "full-text search, and flexible document storage — without running multiple "
        "database systems.",
        "database",
        "arangodb/arangodb",
        13000,
        "https://arangodb.com",
        "graph,nosql,document,key-value,multi-model,aql",
        "docker run -e ARANGO_ROOT_PASSWORD=password arangodb",
        "code",
    ),
    # API Tools ----------------------------------------------------------------
    (
        "hurl",
        "Hurl",
        "Run and test HTTP requests with plain text files",
        "Hurl is a command-line tool that runs HTTP requests defined in a simple "
        "plain text format. It can chain requests, capture values, evaluate queries "
        "on headers and body responses, and is usable as a non-regression testing "
        "tool. Fast, scriptable, and CI-friendly — a powerful alternative to Postman "
        "for API testing in plain text.",
        "api-tools",
        "Orange-OpenSource/hurl",
        13000,
        "https://hurl.dev",
        "api-testing,http,cli,curl,rest,ci,testing",
        "brew install hurl",
        "code",
    ),
    # DevOps — Service Mesh tools -----------------------------------------------
    (
        "istio",
        "Istio",
        "An open platform to connect, manage, and secure microservices",
        "Istio is the most widely deployed service mesh for Kubernetes, providing "
        "zero-trust networking with mutual TLS, fine-grained traffic management "
        "(canary deployments, A/B testing, circuit breaking), and distributed "
        "observability (traces, metrics, logs) — all without changing application "
        "code. Backed by Google, IBM, and the CNCF.",
        "devops-infrastructure",
        "istio/istio",
        35000,
        "https://istio.io",
        "service-mesh,kubernetes,k8s,mtls,traffic-management,observability,devops",
        "istioctl install --set profile=default",
        "code",
    ),
    (
        "linkerd",
        "Linkerd",
        "Ultralight, zero-config service mesh for Kubernetes",
        "Linkerd is the CNCF graduated service mesh built specifically for "
        "Kubernetes. It provides automatic mutual TLS, latency-aware load "
        "balancing, retries, and transparent distributed tracing — without any "
        "configuration required. Written in Rust and Go, it is the lightest "
        "service mesh available. The recommended service mesh for teams who want "
        "Istio-like features without Envoy complexity.",
        "devops-infrastructure",
        "linkerd/linkerd2",
        10000,
        "https://linkerd.io",
        "service-mesh,kubernetes,k8s,mtls,rust,observability,devops",
        "linkerd install --crds | kubectl apply -f -",
        "code",
    ),
    (
        "cilium",
        "Cilium",
        "eBPF-based networking, observability, and security for Kubernetes",
        "Cilium is an open-source, cloud-native networking solution for Kubernetes "
        "powered by eBPF. It provides high-performance L3/L4/L7 networking, "
        "network policy enforcement, Kubernetes service load balancing, and deep "
        "observability via Hubble — all without iptables overhead. Also ships "
        "Tetragon for runtime security threat detection.",
        "devops-infrastructure",
        "cilium/cilium",
        19000,
        "https://cilium.io",
        "ebpf,kubernetes,k8s,networking,service-mesh,security,observability",
        "helm repo add cilium https://helm.cilium.io/ && helm install cilium cilium/cilium",
        "code",
    ),
    # Monitoring — high-performance Prometheus-compatible TSDB -------------------
    (
        "victoriametrics",
        "VictoriaMetrics",
        "Fast, cost-effective and scalable time series database and monitoring",
        "VictoriaMetrics is a high-performance time series database and monitoring "
        "solution compatible with Prometheus. It offers 5-10× better compression "
        "than Prometheus, faster queries at scale, and a cluster mode that scales "
        "reads and writes independently. Supports PromQL and MetricsQL. Used at "
        "Cloudflare, Wix, and dozens of large-scale production deployments.",
        "monitoring-uptime",
        "VictoriaMetrics/VictoriaMetrics",
        13000,
        "https://victoriametrics.com",
        "prometheus,metrics,timeseries,monitoring,self-hosted,performance",
        "docker run -v victoriametrics-data:/victoria-metrics-data -p 8428:8428 victoriametrics/victoria-metrics",
        "code",
    ),
    # Security — runtime container security -------------------------------------
    (
        "falco",
        "Falco",
        "Cloud-native runtime security for containers and Kubernetes",
        "Falco is a CNCF graduated open-source runtime security tool that detects "
        "threats and anomalies in real time. It uses eBPF to observe kernel syscalls "
        "and Kubernetes audit events, then fires alerts when behaviour matches "
        "configurable rules (e.g. shell spawned in container, sensitive file read, "
        "privilege escalation). Integrates with Slack, PagerDuty, and SIEM systems.",
        "security-tools",
        "falcosecurity/falco",
        7000,
        "https://falco.org",
        "runtime-security,containers,kubernetes,k8s,ebpf,threat-detection,cncf",
        "helm repo add falcosecurity https://falcosecurity.github.io/charts && helm install falco falcosecurity/falco",
        "code",
    ),
    # Developer Tools — Python package managers ---------------------------------
    (
        "uv",
        "uv",
        "An extremely fast Python package and project manager",
        "uv is a drop-in replacement for pip and pip-tools built in Rust by Astral. "
        "It installs packages 10-100× faster than pip, manages virtualenvs, resolves "
        "dependencies with a lockfile, and can replace pyenv for Python version "
        "management. uv is quickly becoming the default Python toolchain for new "
        "projects in 2025.",
        "developer-tools",
        "astral-sh/uv",
        50000,
        "https://docs.astral.sh/uv",
        "python,package-manager,pip,virtualenv,fast,rust",
        "curl -LsSf https://astral.sh/uv/install.sh | sh",
        "code",
    ),
    (
        "poetry",
        "Poetry",
        "Python packaging and dependency management made easy",
        "Poetry handles Python dependency management and packaging with a single "
        "pyproject.toml file and a lockfile for reproducible installs. It automatically "
        "creates and manages virtualenvs, resolves dependencies deterministically, and "
        "can publish packages to PyPI. Poetry is the most-adopted Python project "
        "manager among web developers.",
        "developer-tools",
        "python-poetry/poetry",
        28000,
        "https://python-poetry.org",
        "python,package-manager,dependency-management,virtualenv,pyproject",
        "curl -sSL https://install.python-poetry.org | python3 -",
        "code",
    ),
    # Database — Rust ORM / SQL tooling -----------------------------------------
    (
        "sqlx",
        "sqlx",
        "Async, compile-time checked SQL queries for Rust",
        "sqlx is a pure Rust async SQL toolkit that verifies your queries against "
        "the database schema at compile time — no ORM magic, just type-safe SQL. "
        "Supports PostgreSQL, MySQL, SQLite, and MSSQL. Works with Tokio, async-std, "
        "and Actix. The de-facto standard for Rust web apps that need raw SQL power "
        "with full type safety.",
        "database",
        "launchbadge/sqlx",
        13000,
        "https://github.com/launchbadge/sqlx",
        "rust,sql,postgres,async,type-safe,orm",
        "cargo add sqlx --features runtime-tokio,postgres",
        "code",
    ),
    (
        "diesel",
        "Diesel",
        "Safe, extensible ORM and query builder for Rust",
        "Diesel is a safe, extensible ORM for Rust that prevents runtime query errors "
        "at compile time. It generates type-safe query builders and supports "
        "PostgreSQL, MySQL, and SQLite. Diesel includes built-in schema migrations and "
        "a powerful query DSL that maps directly to SQL without runtime overhead.",
        "database",
        "diesel-rs/diesel",
        12000,
        "https://diesel.rs",
        "rust,orm,postgres,mysql,sqlite,type-safe,migrations",
        "cargo add diesel --features postgres",
        "code",
    ),
    (
        "sea-orm",
        "SeaORM",
        "Async and dynamic ORM for Rust built on top of sqlx",
        "SeaORM is an async ORM for Rust that combines the ergonomics of Active "
        "Record with the type safety of Rust. Built on sqlx, it supports PostgreSQL, "
        "MySQL, and SQLite with a fluent query API, relationship support, and "
        "schema migrations via SeaSchema. Popular in the Rust web ecosystem "
        "alongside Axum and Actix.",
        "database",
        "SeaQL/sea-orm",
        7000,
        "https://www.sea-ql.org/SeaORM",
        "rust,orm,async,postgres,mysql,sqlite,active-record",
        "cargo add sea-orm --features sqlx-postgres,runtime-tokio-native-tls",
        "code",
    ),
    # Frontend — RedwoodJS full-stack framework ---------------------------------
    (
        "redwoodjs",
        "RedwoodJS",
        "The full-stack JavaScript framework for the startup era",
        "RedwoodJS is an opinionated full-stack web framework built on React, "
        "GraphQL, Prisma, and TypeScript. It provides file-based routing, "
        "serverless deploy support, built-in auth, and a cells pattern for "
        "declarative data fetching. Designed to be the Rails of the JavaScript "
        "world — convention over configuration from frontend to database.",
        "frontend-frameworks",
        "redwoodjs/redwood",
        17000,
        "https://redwoodjs.com",
        "react,graphql,prisma,typescript,fullstack,serverless",
        "yarn create redwood-app my-app",
        "code",
    ),
    # AI & Automation --------------------------------------------------------
    (
        "dify",
        "Dify",
        "Open-source LLM app development platform",
        "Dify is an open-source LLM application development platform with a "
        "visual workflow builder, RAG pipeline, agent orchestration, and model "
        "management. Supports 100+ LLM providers. Self-host or use Dify Cloud. "
        "Powers AI-native apps from prototype to production.",
        "ai-automation",
        "langgenius/dify",
        60000,
        "https://dify.ai",
        "ai,llm,rag,agents,workflow,no-code,self-hosted",
        "docker compose up -d",
        "code",
    ),
    (
        "open-webui",
        "Open WebUI",
        "Self-hosted web interface for running local LLMs",
        "Open WebUI is a feature-rich, offline-capable web interface for Ollama "
        "and OpenAI-compatible APIs. Includes RAG support, web search, image "
        "generation, voice I/O, model management, and multi-user access. "
        "The most popular self-hosted UI for local LLM inference.",
        "ai-automation",
        "open-webui/open-webui",
        80000,
        "https://openwebui.com",
        "ai,ollama,llm,self-hosted,rag,local-ai,chatgpt-ui",
        "pip install open-webui",
        "code",
    ),
    # Security Tools ---------------------------------------------------------
    (
        "certbot",
        "Certbot",
        "Automatically enable HTTPS on your website with Let's Encrypt",
        "Certbot is the EFF's free, open-source ACME client that automatically "
        "obtains and renews TLS/SSL certificates from Let's Encrypt. Supports "
        "Apache, Nginx, and standalone modes. The standard tool for free HTTPS "
        "certificate management on self-hosted servers.",
        "security-tools",
        "certbot/certbot",
        31000,
        "https://certbot.eff.org",
        "ssl,tls,https,letsencrypt,acme,certificate,security",
        "sudo snap install --classic certbot",
        "code",
    ),
    (
        "step-ca",
        "step-ca",
        "Open-source private certificate authority for DevOps",
        "step-ca is an open-source, online certificate authority for secure, "
        "automated certificate management. Supports ACME, SCEP, JWK, OAuth/OIDC, "
        "and SSH certificates. The self-hosted alternative to Let's Encrypt for "
        "internal PKI, mTLS, and zero-trust networking.",
        "security-tools",
        "smallstep/certificates",
        7000,
        "https://smallstep.com/docs/step-ca",
        "ssl,tls,pki,certificate-authority,acme,mtls,zero-trust,security",
        "brew install step",
        "code",
    ),
    # Logging ----------------------------------------------------------------
    (
        "loki",
        "Grafana Loki",
        "Like Prometheus, but for logs",
        "Grafana Loki is a horizontally-scalable, highly-available log aggregation "
        "system. Unlike ELK, it does not index log content — only labels — making "
        "it cost-effective and fast. Integrates natively with Grafana and Prometheus "
        "for a complete observability stack.",
        "logging",
        "grafana/loki",
        23000,
        "https://grafana.com/oss/loki",
        "logging,log-aggregation,observability,grafana,prometheus,devops",
        "docker run grafana/loki:latest -config.file=/etc/loki/local-config.yaml",
        "code",
    ),
    # Headless CMS -------------------------------------------------------------
    (
        "payload",
        "Payload CMS",
        "The most powerful TypeScript headless CMS",
        "Payload is a code-first headless CMS built with TypeScript, "
        "React, and Node.js. It generates a fully-featured admin UI from "
        "your schema, supports Postgres and MongoDB, and integrates "
        "natively with Next.js. No vendor lock-in — your database, your server.",
        "headless-cms",
        "payloadcms/payload",
        32000,
        "https://payloadcms.com",
        "cms,headless,typescript,nextjs,admin-ui,postgres,mongodb",
        "npx create-payload-app",
        "code",
    ),
    # Database -----------------------------------------------------------------
    (
        "pglite",
        "PGlite",
        "Lightweight Postgres in WASM for the browser and Node",
        "PGlite is a WASM build of Postgres that runs in the browser, "
        "Node.js, and edge runtimes with no native dependencies. Supports "
        "full Postgres SQL, ACID transactions, and persistence via "
        "IndexedDB. Ideal for local-first apps, tests, and Postgres-powered "
        "edge compute.",
        "database",
        "electric-sql/pglite",
        9000,
        "https://pglite.dev",
        "postgres,wasm,browser,local-first,database,serverless",
        "npm install @electric-sql/pglite",
        "code",
    ),
    # Frontend Frameworks ------------------------------------------------------
    (
        "monaco",
        "Monaco Editor",
        "The code editor that powers VS Code",
        "Monaco Editor is the browser-based code editor that powers "
        "VS Code. It provides rich IntelliSense, syntax highlighting, "
        "diff views, and multi-cursor editing for 30+ languages. "
        "Widely used to build browser IDEs, playground tools, and "
        "in-app code editors.",
        "frontend-frameworks",
        "microsoft/monaco-editor",
        38000,
        "https://microsoft.github.io/monaco-editor",
        "editor,code-editor,browser-ide,vscode,syntax-highlighting",
        "npm install monaco-editor",
        "code",
    ),
    (
        "immer",
        "Immer",
        "Create the next immutable state by mutating the current one",
        "Immer simplifies handling immutable data structures. You work "
        "with a mutable draft, and Immer produces the next immutable "
        "state. Used widely in Redux Toolkit, Zustand, and standalone "
        "React state management. Supports patches and structural sharing.",
        "frontend-frameworks",
        "immerjs/immer",
        26000,
        "https://immerjs.github.io/immer",
        "state-management,immutable,react,redux,draft,frontend",
        "npm install immer",
        "code",
    ),
    # Developer Tools ----------------------------------------------------------
    (
        "medusajs",
        "Medusa",
        "Open-source headless commerce infrastructure",
        "Medusa is a composable open-source commerce engine built for "
        "developers. Supports multi-region, subscriptions, promotions, "
        "inventory management, and custom workflows. Powers headless "
        "storefronts via its REST API and ships with a React admin "
        "dashboard. Self-host on any Node.js environment.",
        "developer-tools",
        "medusajs/medusa",
        23000,
        "https://medusajs.com",
        "ecommerce,commerce,headless,nodejs,api,self-hosted,typescript",
        "npx create-medusa-app",
        "code",
    ),
    # DevOps & Infrastructure --------------------------------------------------
    (
        "dagger",
        "Dagger",
        "Portable CI/CD pipelines as code",
        "Dagger is a portable DevOps engine that runs your CI/CD "
        "pipelines as code. Write pipeline steps once in TypeScript, "
        "Python, or Go using the Dagger SDK; run them locally with "
        "Docker and on any CI provider (GitHub Actions, GitLab CI, "
        "CircleCI, Jenkins) without change. Caches every layer "
        "intelligently for fast incremental builds.",
        "devops-infrastructure",
        "dagger/dagger",
        10000,
        "https://dagger.io",
        "ci-cd,devops,containers,docker,pipelines,automation,build-tool",
        "curl -L https://dl.dagger.io/dagger/install.sh | DAGGER_VERSION=0.13.3 sh",
        "code",
    ),
    # Developer Tools ----------------------------------------------------------
    (
        "fnm",
        "Fnm",
        "Fast and simple Node.js version manager",
        "Fnm (Fast Node Manager) is a Rust-based Node.js version "
        "manager that is 40× faster than nvm. Supports .nvmrc and "
        ".node-version files, cross-platform (macOS, Linux, Windows), "
        "and integrates with all major shells (bash, zsh, fish, "
        "PowerShell). Drop-in nvm replacement with zero runtime "
        "overhead — no shell startup penalty.",
        "developer-tools",
        "Schniz/fnm",
        17000,
        "https://fnm.vercel.app",
        "node,nodejs,version-manager,nvm,developer-tools,rust,cli",
        "curl -fsSL https://fnm.vercel.app/install | bash",
        "code",
    ),
    (
        "zellij",
        "Zellij",
        "Feature-rich terminal workspace and multiplexer",
        "Zellij is a terminal workspace with batteries included. "
        "Written in Rust, it offers a plugin system (WASM), floating "
        "panes, session management, layouts, and an intuitive "
        "key-binding system. Unlike tmux it shows keybindings "
        "on-screen for discoverability, making it approachable for "
        "newcomers while staying powerful for power users.",
        "developer-tools",
        "zellij-org/zellij",
        23000,
        "https://zellij.dev",
        "terminal,multiplexer,tmux,rust,cli,workspace,session-manager",
        "bash <(curl -L zellij.dev/launch)",
        "code",
    ),
    # Testing Tools ------------------------------------------------------------
    (
        "oxlint",
        "OxLint",
        "Rust-powered JavaScript and TypeScript linter — 50–100× faster than ESLint",
        "OxLint is a Rust-based JavaScript and TypeScript linter "
        "built by the Oxc project. It runs 50–100× faster than ESLint "
        "by parallelising lint passes across all CPU cores. Implements "
        "500+ ESLint rules out of the box, is compatible with ESLint "
        "configs, and integrates with VS Code, WebStorm, and CI "
        "pipelines. Part of the Oxc toolchain alongside an ultra-fast "
        "Rust parser and transformer.",
        "testing-tools",
        "oxc-project/oxc",
        13000,
        "https://oxc.rs",
        "linter,eslint,javascript,typescript,rust,fast,testing,ci",
        "npm install oxlint --save-dev",
        "code",
    ),
    # Frontend Frameworks ------------------------------------------------------
    (
        "analog",
        "Analog",
        "The full-stack Angular meta-framework",
        "Analog is a full-stack meta-framework for Angular, similar "
        "to Next.js for React or Nuxt for Vue. It adds file-based "
        "routing, server-side rendering (SSR), static site generation "
        "(SSG), API routes, and Server Actions on top of Angular. "
        "Built on Vite and Nitro, it supports deploying to Vercel, "
        "Netlify, Cloudflare Workers, and Node.js servers.",
        "frontend-frameworks",
        "analogjs/analog",
        3500,
        "https://analogjs.org",
        "angular,meta-framework,ssr,ssg,vite,nitro,typescript,fullstack",
        "npm create analog@latest",
        "code",
    ),
    # Boilerplates ---------------------------------------------------------------
    (
        "shipwright",
        "Shipwright",
        "Next.js SaaS boilerplate with auth, payments, and more",
        "Shipwright (aka Next-js-Boilerplate) is an opinionated Next.js "
        "starter with TypeScript, Tailwind CSS, shadcn/ui, NextAuth, "
        "Prisma, and Stripe pre-configured. One of the most-starred "
        "free SaaS starters on GitHub.",
        "boilerplates",
        "ixartz/Next-js-Boilerplate",
        4800,
        "https://github.com/ixartz/Next-js-Boilerplate",
        "boilerplate,nextjs,tailwind,typescript,saas,stripe,auth",
        "git clone https://github.com/ixartz/Next-js-Boilerplate.git",
        "code",
    ),
    (
        "supastarter",
        "SupaStarter",
        "Next.js + Supabase SaaS starter kit",
        "SupaStarter is a full-stack SaaS starter combining Next.js, "
        "Supabase (auth + database), Stripe billing, Tailwind CSS, "
        "and shadcn/ui. Includes multi-tenancy, team management, "
        "and transactional emails out of the box.",
        "boilerplates",
        "supastarter/next",
        1800,
        "https://supastarter.dev",
        "boilerplate,nextjs,supabase,stripe,tailwind,saas,typescript",
        "git clone https://github.com/supastarter/next.git",
        "code",
    ),
    # MCP Servers ----------------------------------------------------------------
    (
        "mcp-brave-search",
        "MCP Brave Search",
        "Real-time web search for AI agents via Brave API",
        "An official MCP server that exposes Brave Search to AI agents. "
        "Lets Claude and other MCP clients run real-time web searches, "
        "image searches, and news queries using Brave's privacy-first "
        "search API. Includes result summaries, safe-search controls, "
        "and country/language targeting.",
        "mcp-servers",
        "modelcontextprotocol/servers",
        14000,
        "https://github.com/modelcontextprotocol/servers/tree/main/src/brave-search",
        "mcp,search,web,brave,ai-agent,real-time",
        "npx @modelcontextprotocol/server-brave-search",
        "code",
    ),
    (
        "mcp-playwright",
        "MCP Playwright",
        "Browser automation and web scraping for AI agents",
        "The official Microsoft Playwright MCP server gives AI agents "
        "full browser control: navigate pages, click elements, fill "
        "forms, capture screenshots, and extract structured data. "
        "Works with Chromium, Firefox, and WebKit, and exposes CDP "
        "for rich browser automation.",
        "mcp-servers",
        "microsoft/playwright-mcp",
        3200,
        "https://github.com/microsoft/playwright-mcp",
        "mcp,playwright,browser-automation,web-scraping,ai-agent",
        "npx @playwright/mcp",
        "code",
    ),
    (
        "mcp-linear",
        "MCP Linear",
        "Give AI agents access to Linear project management",
        "An MCP server that gives AI agents read and write access to Linear "
        "issues, projects, and teams. Lets agents create issues, update "
        "status, add comments, and query the backlog — turning your AI "
        "assistant into a first-class Linear team member.",
        "mcp-servers",
        "linear/linear",
        10000,
        "https://linear.app/docs/mcp",
        "mcp,linear,project-management,issues,ai-agent,productivity",
        "npx @linear/mcp-server",
        "code",
    ),
    (
        "mcp-slack",
        "MCP Slack",
        "Give AI agents access to Slack channels and messages",
        "The official MCP server for Slack. Lets AI agents read channel "
        "history, post messages, search conversations, and manage threads. "
        "Built on the official Slack SDK and compatible with Claude and any "
        "MCP-capable AI agent.",
        "mcp-servers",
        "modelcontextprotocol/servers",
        14000,
        "https://github.com/modelcontextprotocol/servers/tree/main/src/slack",
        "mcp,slack,messaging,ai-agent,communication",
        "npx @modelcontextprotocol/server-slack",
        "code",
    ),
    (
        "mcp-notion",
        "MCP Notion",
        "Give AI agents read and write access to Notion workspaces",
        "An MCP server for Notion that lets AI agents query databases, "
        "create and update pages, append blocks, and search your workspace. "
        "Enables agents to use Notion as a knowledge base or task tracker "
        "in multi-step workflows.",
        "mcp-servers",
        "makenotion/notion-sdk-js",
        7000,
        "https://developers.notion.com/docs/mcp",
        "mcp,notion,knowledge-base,ai-agent,pages,databases",
        "npx @notionhq/mcp",
        "code",
    ),
    # API Tools ------------------------------------------------------------------
    (
        "graphql-yoga",
        "GraphQL Yoga",
        "Fully-featured, spec-compliant GraphQL server",
        "GraphQL Yoga is a batteries-included GraphQL server built on "
        "standard fetch APIs. Supports subscriptions, file uploads, "
        "persisted queries, and the Envelop plugin system. Works with "
        "Fastify, Express, Next.js, Cloudflare Workers, and more.",
        "api-tools",
        "dotansimha/graphql-yoga",
        8500,
        "https://the-guild.dev/graphql/yoga-server",
        "graphql,api,subscriptions,typescript,server",
        "npm install graphql-yoga",
        "code",
    ),
    # Developer Tools ------------------------------------------------------------
    (
        "oxc",
        "Oxc",
        "The JavaScript Oxidation Compiler",
        "Oxc is a high-performance JavaScript and TypeScript toolchain "
        "written in Rust. Includes a linter 50-100x faster than ESLint, "
        "a transformer, a bundler (Rolldown), a minifier, and a formatter. "
        "Powers Vite's next-generation build pipeline.",
        "developer-tools",
        "oxc-project/oxc",
        13000,
        "https://oxc.rs",
        "linter,bundler,transformer,rust,javascript,fast",
        "npm install @oxc-project/oxc-napi",
        "code",
    ),
    # Authentication -------------------------------------------------------------
    (
        "lucia",
        "Lucia",
        "Authentication, simple and clean",
        "Lucia is a lightweight TypeScript authentication library that "
        "handles sessions, not passwords. Gives you full control over the "
        "auth flow without magic or abstraction. Works with any framework "
        "and any database — Drizzle, Prisma, Mongoose, and more.",
        "authentication",
        "lucia-auth/lucia",
        11000,
        "https://lucia-auth.com",
        "auth,session,typescript,framework-agnostic",
        "npm install lucia",
        "code",
    ),
    # Project Management — open-source Notion/Confluence alternative -----------
    (
        "appflowy",
        "AppFlowy",
        "Bring projects, wikis, and teams together with AI",
        "AppFlowy is an open-source Notion and Confluence alternative built with "
        "Rust and Flutter. Self-hostable with full data ownership. Supports "
        "documents, databases, kanban boards, calendars, and AI writing assistance. "
        "One of the most-starred open-source productivity tools (61k+ stars).",
        "project-management",
        "AppFlowy-IO/AppFlowy",
        61000,
        "https://appflowy.io",
        "notion-alternative,wiki,project-management,self-hosted,open-source,rust,flutter",
        "docker compose up -d",
        "code",
    ),
    # Analytics — open-source data catalog and lineage platform ----------------
    (
        "datahub",
        "DataHub",
        "The extensible metadata platform for the modern data stack",
        "DataHub is a modern metadata platform for data discovery, observability, "
        "and governance built by LinkedIn. Provides data lineage, impact analysis, "
        "data cataloging, and column-level lineage. Integrates with dbt, Airflow, "
        "Spark, Kafka, and 50+ data sources out of the box.",
        "analytics-metrics",
        "datahub-project/datahub",
        10000,
        "https://datahubproject.io",
        "data-catalog,data-lineage,data-discovery,metadata,governance,open-source",
        "pip install acryl-datahub",
        "code",
    ),
    # Boilerplates — T3 Stack scaffolding CLI ----------------------------------
    (
        "create-t3-app",
        "create-t3-app",
        "The best way to start a full-stack, typesafe Next.js app",
        "create-t3-app is the official CLI for bootstrapping T3 Stack projects — "
        "Next.js, TypeScript, Tailwind CSS, tRPC, Prisma, and NextAuth.js. "
        "The most popular opinionated Next.js starter with 27k+ stars. "
        "One command to scaffold a type-safe, production-ready SaaS foundation.",
        "boilerplates",
        "t3-oss/create-t3-app",
        27000,
        "https://create.t3.gg",
        "nextjs,typescript,trpc,tailwind,prisma,nextauth,t3-stack,saas-starter",
        "npm create t3-app@latest",
        "code",
    ),
    # AI — TypeScript AI agent framework (formerly Phidata) --------------------
    (
        "agno",
        "Agno",
        "Build fast, multi-modal AI agents in Python",
        "Agno (formerly Phidata) is a lightweight Python library for building "
        "multi-modal AI agents with memory, knowledge, tools, and reasoning. "
        "Supports OpenAI, Anthropic, Gemini, and local models via Ollama. "
        "Features structured outputs, agent teams, and a built-in playground UI.",
        "ai-automation",
        "agno-agi/agno",
        23000,
        "https://agno.com",
        "ai-agent,python,llm,multi-agent,memory,tools,openai,anthropic",
        "pip install agno",
        "code",
    ),
    # AI — open-source ML feature store ----------------------------------------
    (
        "feast",
        "Feast",
        "Open source feature store for machine learning",
        "Feast is a standalone open-source feature store that enables ML teams "
        "to define, manage, discover, and serve features for model training and "
        "online inference. Supports offline stores (BigQuery, Spark, Redshift) "
        "and online stores (Redis, DynamoDB, Bigtable). CNCF sandbox project.",
        "ai-automation",
        "feast-dev/feast",
        5000,
        "https://feast.dev",
        "feature-store,ml,machine-learning,mlops,redis,bigquery,python",
        "pip install feast",
        "code",
    ),
    # Frontend Frameworks — Rolldown (Rust bundler replacing Rollup inside Vite) ----------
    (
        "rolldown",
        "Rolldown",
        "Rust-powered JavaScript bundler for Vite — next-gen speed without compromise",
        "Rolldown is a Rust-based JavaScript/TypeScript bundler designed to replace "
        "Rollup as the production bundler inside Vite. It achieves dramatic build speed "
        "improvements while maintaining full Rollup plugin compatibility. Being integrated "
        "as the default bundler in Vite 6, making it the de-facto bundler for the modern "
        "Vite ecosystem. Built by the VoidZero team (creator of Vue and Vite).",
        "frontend-frameworks",
        "rolldown-rs/rolldown",
        9000,
        "https://rolldown.rs",
        "bundler,build-tool,rust,vite,fast,rollup-compatible",
        "npm install rolldown",
        "code",
    ),
    # Developer Tools — Knip (TypeScript dead code and unused dependency finder) ----------
    (
        "knip",
        "Knip",
        "Find unused files, exports, and dependencies in your TypeScript project",
        "Knip scans your TypeScript and JavaScript projects to find unused files, "
        "exports, types, and dependencies. It eliminates dead code, reduces bundle "
        "size, and improves maintainability. Supports monorepos, all major frameworks, "
        "and hundreds of plugins. The go-to tool for TypeScript project hygiene — "
        "runs in CI and as a pre-commit check.",
        "developer-tools",
        "webpodcast/knip",
        7000,
        "https://knip.dev",
        "typescript,dead-code,unused-exports,static-analysis,monorepo,developer-tools",
        "npm install knip",
        "code",
    ),
    # Search Engine — Trieve (search + RAG + recommendations in one hosted platform) -----
    (
        "trieve",
        "Trieve",
        "Search, RAG, and recommendations platform for developers",
        "Trieve is a hosted platform that combines full-text search, vector search, "
        "RAG (Retrieval-Augmented Generation), and recommendation APIs in one service. "
        "It handles document ingestion, chunking, embeddings, and reranking so you can "
        "add powerful semantic search and AI retrieval to your app without building the "
        "infrastructure yourself. SDKs for TypeScript and Python.",
        "search-engine",
        "devflowinc/trieve",
        2000,
        "https://trieve.ai",
        "search,rag,vector-search,recommendations,full-text,semantic-search,typescript",
        "npm install trieve-ts-sdk",
        "saas",
    ),
    # Developer Tools — Val Town (serverless TypeScript scripting with HTTP triggers) -----
    (
        "val-town",
        "Val Town",
        "Write, run, and deploy serverless TypeScript scripts in seconds",
        "Val Town is a social coding platform where you write small TypeScript functions "
        "('vals') that run as HTTP endpoints, cron jobs, or email handlers — instantly, "
        "with zero setup. Vals can import from npm, call each other, and store data in "
        "built-in SQLite. Great for webhooks, bots, automations, and rapid prototyping. "
        "Think GitHub Gists + serverless functions + a social layer.",
        "developer-tools",
        "val-town/val-town-product",
        3000,
        "https://val.town",
        "serverless,typescript,scripts,webhooks,cron,prototyping,platform",
        "# Sign up at val.town — no install needed",
        "saas",
    ),
    # Monitoring — OpenReplay (open-source session replay + DevTools, Hotjar/FullStory alternative) -------
    (
        "openreplay",
        "OpenReplay",
        "Open-source session replay and product analytics — self-hostable Hotjar alternative",
        "OpenReplay is an open-source session replay and product analytics suite that lets "
        "you replay user sessions (mouse movements, clicks, console errors, network requests) "
        "and understand how users interact with your app. Self-hostable on your own infra or "
        "as a cloud service. Includes DevTools integration, rage-click detection, "
        "performance monitoring, and funnel analytics. Strong alternative to Hotjar, "
        "FullStory, and LogRocket with full data ownership.",
        "monitoring-uptime",
        "openreplay/openreplay",
        10000,
        "https://openreplay.com",
        "session-replay,monitoring,analytics,open-source,self-hosted,hotjar-alternative,ux",
        "docker-compose up -d  # self-hosted",
        "code",
    ),
    # API Tools — Relay (Meta's production GraphQL client for React, 18k★) ----------------------------
    (
        "relay",
        "Relay",
        "Production-ready GraphQL client for React — declarative data fetching at scale",
        "Relay is Meta's production-ready GraphQL client for React applications. It compiles "
        "GraphQL queries at build time for maximum performance, co-locates data requirements "
        "with components, and handles pagination, subscriptions, and optimistic updates. "
        "Used by Facebook, Instagram, and other large-scale React apps. Relay emphasises "
        "correctness and type-safety via generated TypeScript types. Best-in-class for "
        "large codebases where Apollo feels too loose.",
        "api-tools",
        "facebook/relay",
        18000,
        "https://relay.dev",
        "graphql,react,client,meta,facebook,data-fetching,typescript",
        "npm install react-relay relay-runtime",
        "code",
    ),
    # Developer Tools — Gleam (type-safe functional language on Erlang/BEAM VM) ----------------------
    (
        "gleam",
        "Gleam",
        "Type-safe functional language on the Erlang VM — fast, friendly, and reliable",
        "Gleam is a statically typed functional language that runs on the Erlang virtual "
        "machine (BEAM), giving it the fault tolerance and concurrency of Erlang/Elixir with "
        "a modern, friendly syntax. Compiles to both Erlang and JavaScript (Node, Deno, "
        "browsers). The compiler produces excellent error messages and has no runtime "
        "exceptions from type errors. Growing fast in the web backend space with its "
        "Wisp HTTP framework and growing ecosystem.",
        "developer-tools",
        "gleam-lang/gleam",
        18000,
        "https://gleam.run",
        "language,erlang,beam,functional,type-safe,web-backend,javascript",
        "# Install via gleam.run/getting-started",
        "code",
    ),
    # Database — Electric SQL (local-first sync layer for Postgres, 8k★) ----------------------------
    (
        "electric-sql",
        "Electric SQL",
        "Local-first sync engine for Postgres — instant reactivity without loading states",
        "Electric SQL is a local-first sync layer that syncs a subset of your Postgres "
        "database into the client in real-time. Apps read from local storage (instant, "
        "offline-capable) and sync changes back to Postgres. No loading states — data is "
        "always available locally. Uses Postgres logical replication under the hood. Works "
        "with any Postgres host (Supabase, Neon, RDS, self-hosted). Shape-based sync lets "
        "you subscribe to live queries that update automatically.",
        "database",
        "electric-sql/electric",
        8000,
        "https://electric-sql.com",
        "local-first,sync,postgres,realtime,offline,reactive,typescript",
        "npm install electric-sql",
        "code",
    ),
    # Frontend Frameworks — Million.js (lightweight React compiler/optimizer, 16k★) -----------------
    (
        "million",
        "Million.js",
        "Drop-in React compiler that makes your app up to 70% faster",
        "Million.js is a lightweight virtual DOM replacement for React that makes components "
        "up to 70% faster through compiler optimisations. It works as a drop-in addition to "
        "React — you wrap performance-critical components with the `block()` HOC and Million "
        "replaces React's reconciler with a faster diff algorithm for those subtrees. No "
        "rewrite required. Also includes the Million Lint VSCode extension that automatically "
        "finds and flags slow React components. Works with Next.js, Vite, and Create React App.",
        "frontend-frameworks",
        "aidenybai/million",
        16000,
        "https://million.dev",
        "react,performance,compiler,virtual-dom,optimization,nextjs,vite",
        "npm install million",
        "code",
    ),
    # ── Eighty-fourth pass ────────────────────────────────────────────────────
    # JVM / Kotlin frameworks -----------------------------------------------
    (
        "ktor",
        "Ktor",
        "Asynchronous framework for connected applications",
        "Ktor is an asynchronous Kotlin framework by JetBrains for building connected "
        "applications — web services, HTTP clients, mobile backends. Lightweight, "
        "coroutine-native, and runs on JVM, Android, and Kotlin Multiplatform.",
        "api-tools",
        "kotlin/ktor",
        12000,
        "https://ktor.io",
        "kotlin,async,jvm,coroutines,multiplatform",
        "implementation(\"io.ktor:ktor-server-core:3.0.0\")",
        "code",
    ),
    (
        "quarkus",
        "Quarkus",
        "Supersonic Subatomic Java",
        "Quarkus is a Kubernetes-native Java stack tailored for GraalVM and HotSpot. "
        "Sub-10ms startup, tiny memory footprint, and developer-friendly live reload. "
        "Unifies imperative and reactive programming models for cloud-native microservices.",
        "api-tools",
        "quarkusio/quarkus",
        14000,
        "https://quarkus.io",
        "java,graalvm,microservices,kubernetes,native-image",
        "mvn io.quarkus.platform:quarkus-maven-plugin:create",
        "code",
    ),
    # Changelog generation --------------------------------------------------
    (
        "git-cliff",
        "git-cliff",
        "A highly customizable changelog generator",
        "git-cliff generates changelogs from your Git history based on Conventional "
        "Commits. Written in Rust for speed, supports Jinja2 templates, multiple "
        "output formats, and integrates with GitHub CI workflows.",
        "devops-infrastructure",
        "orhun/git-cliff",
        9000,
        "https://git-cliff.org",
        "changelog,git,conventional-commits,rust,release",
        "cargo install git-cliff",
        "code",
    ),
    # Apache Spark -----------------------------------------------------------
    (
        "apache-spark",
        "Apache Spark",
        "Unified engine for large-scale data analytics",
        "Apache Spark is the most widely-used open-source unified analytics engine for "
        "large-scale data processing. Supports batch, streaming (Structured Streaming), "
        "SQL, machine learning (MLlib), and graph processing (GraphX).",
        "background-jobs",
        "apache/spark",
        40000,
        "https://spark.apache.org",
        "batch,streaming,big-data,ml,sql,scala,python,java",
        "pip install pyspark",
        "code",
    ),
    # Data Science / DataFrame ---------------------------------------------------
    (
        "polars",
        "Polars",
        "Blazingly fast DataFrames for Python, Rust, and Node.js",
        "Polars is a lightning-fast DataFrame library written in Rust. Often 10-100x "
        "faster than pandas for common operations. Lazy evaluation, multi-threaded "
        "execution, and Apache Arrow memory model. The go-to pandas alternative in 2025.",
        "database",
        "pola-rs/polars",
        34000,
        "https://pola.rs",
        "dataframe,python,rust,analytics,pandas-alternative",
        "pip install polars",
        "code",
    ),
    # CLI Frameworks -------------------------------------------------------------
    (
        "cobra",
        "Cobra",
        "A Commander for modern Go CLI applications",
        "Cobra is the most popular Go library for building powerful modern CLI apps. "
        "Used by Docker, Kubernetes kubectl, Hugo, GitHub CLI, and many others. "
        "Generates bash/zsh/fish completion, man pages, and more.",
        "cli-tools",
        "spf13/cobra",
        38000,
        "https://cobra.dev",
        "cli,go,golang,command-line,shell-completion",
        "go get -u github.com/spf13/cobra@latest",
        "code",
    ),
    (
        "click",
        "Click",
        "The Pallets project for creating beautiful command line interfaces in Python",
        "Click is a Python package for creating beautiful command line interfaces with "
        "as little code as possible. Arbitrary nesting of commands, automatic help page "
        "generation, and supports lazy loading of subcommands.",
        "cli-tools",
        "pallets/click",
        15000,
        "https://click.palletsprojects.com",
        "cli,python,command-line,argparse-alternative",
        "pip install click",
        "code",
    ),
    # Developer Tools — Diagramming / Whiteboard ---------------------------------
    (
        "excalidraw",
        "Excalidraw",
        "Virtual whiteboard for sketching hand-drawn like diagrams",
        "Excalidraw is an open-source virtual whiteboard with a hand-drawn feel. "
        "Used by millions for technical diagrams, architecture sketches, and "
        "collaborative whiteboarding. End-to-end encrypted real-time collaboration.",
        "developer-tools",
        "excalidraw/excalidraw",
        89000,
        "https://excalidraw.com",
        "whiteboard,diagrams,collaboration,canvas,drawing",
        "npm install @excalidraw/excalidraw",
        "code",
    ),
    # Schema Validation ----------------------------------------------------------
    (
        "yup",
        "Yup",
        "Dead simple object schema validation for JavaScript",
        "Yup is a schema builder for runtime value parsing and validation. Define a "
        "schema, transform a value to match, assert the shape of an existing value, or "
        "both. Pre-dates Zod but still widely used, especially with Formik.",
        "developer-tools",
        "jquense/yup",
        22000,
        "https://github.com/jquense/yup",
        "validation,schema,javascript,typescript,formik",
        "npm install yup",
        "code",
    ),
    # AI Dev Tools — Eighty-Sixth Pass -------------------------------------------
    (
        "cline",
        "Cline",
        "Open-source AI coding agent that lives in your IDE",
        "Cline (formerly Claude Dev) is an open-source AI coding extension for VS Code "
        "and JetBrains. It autonomously reads files, writes code, runs terminal commands, "
        "and browses the web to complete multi-step tasks. Supports Claude, GPT-4, Gemini, "
        "and any OpenAI-compatible API. 38k+ GitHub stars.",
        "ai-dev-tools",
        "clinebot/cline",
        38000,
        "https://cline.bot",
        "ai-coding,code-assistant,ide,vscode,autonomous-agent,claude",
        "",
        "code",
    ),
    # Local LLM ------------------------------------------------------------------
    (
        "jan",
        "Jan",
        "Open-source local LLM chat and inference server",
        "Jan is a 100% offline, privacy-first alternative to ChatGPT that runs on your "
        "own hardware. Download models from Hugging Face, run them locally via llama.cpp, "
        "and expose a local OpenAI-compatible API server. Supports Mac, Windows, and Linux.",
        "ai-automation",
        "janhq/jan",
        22000,
        "https://jan.ai",
        "local-llm,privacy,inference,chat,offline,openai-compatible",
        "",
        "code",
    ),
    # LLM Observability ----------------------------------------------------------
    (
        "opik",
        "Opik",
        "Open-source LLM evaluation and tracing by Comet",
        "Opik is an open-source platform for evaluating, testing, and monitoring LLM "
        "applications. Log traces with one line of code, run automated evaluations, "
        "compare prompt versions, and catch regressions before they reach production. "
        "Integrates with LangChain, LlamaIndex, and any LLM.",
        "ai-automation",
        "comet-ml/opik",
        5000,
        "https://www.comet.com/site/products/opik",
        "llm-evaluation,tracing,observability,evals,testing,langchain",
        "pip install opik",
        "code",
    ),
    # JavaScript Utility Libraries -----------------------------------------------
    (
        "jquery",
        "jQuery",
        "The Write Less, Do More JavaScript library",
        "jQuery is a fast, small, and feature-rich JavaScript library. "
        "It simplifies HTML document traversal, event handling, animation, and Ajax "
        "with an easy-to-use API. Despite the React/Vue era, jQuery still powers "
        "a vast portion of the web and is one of the most downloaded npm packages.",
        "frontend-frameworks",
        "jquery/jquery",
        59000,
        "https://jquery.com",
        "javascript,dom,ajax,utility",
        "npm install jquery",
        "code",
    ),
    (
        "rxjs",
        "RxJS",
        "Reactive Extensions library for JavaScript",
        "RxJS is a library for reactive programming using Observables. Enables "
        "composing asynchronous and event-based programs using observable sequences "
        "and LINQ-style query operators. Core dependency of Angular and widely used "
        "with React, Vue, and plain JavaScript for complex async flows.",
        "frontend-frameworks",
        "ReactiveX/rxjs",
        31000,
        "https://rxjs.dev",
        "reactive,observables,angular,async,functional-reactive",
        "npm install rxjs",
        "code",
    ),
    (
        "lodash",
        "Lodash",
        "A modern JavaScript utility library delivering modularity and performance",
        "Lodash is a modern JavaScript utility library with methods for arrays, "
        "objects, strings, numbers, and more. Provides consistent cross-environment "
        "iteration support with tree-shakeable modular imports. One of the most "
        "downloaded npm packages ever.",
        "developer-tools",
        "lodash/lodash",
        59000,
        "https://lodash.com",
        "javascript,utility,functional,arrays,objects",
        "npm install lodash",
        "code",
    ),
    # Run GitHub Actions Locally -------------------------------------------------
    (
        "act",
        "act",
        "Run your GitHub Actions locally",
        "act uses Docker to run your GitHub Actions locally. Reads your "
        ".github/workflows/ files and uses the Docker API to pull or build images "
        "and run the containers. Ideal for rapid feedback loops without pushing "
        "every commit to CI. Written in Go.",
        "devops-infrastructure",
        "nektos/act",
        59000,
        "https://github.com/nektos/act",
        "ci-cd,github-actions,local,docker",
        "brew install act",
        "code",
    ),
    # Express Security Middleware -------------------------------------------------
    (
        "helmet",
        "Helmet.js",
        "Secure your Express apps with HTTP headers",
        "Helmet helps secure Express.js apps by setting various HTTP security "
        "headers including Content-Security-Policy, X-XSS-Protection, "
        "X-Content-Type-Options, and more. Simple middleware with sensible defaults "
        "that protects against common web vulnerabilities. Used by millions of "
        "Node.js applications.",
        "security-tools",
        "helmetjs/helmet",
        10000,
        "https://helmetjs.github.io",
        "security,express,http-headers,csp,nodejs",
        "npm install helmet",
        "code",
    ),
    # VPN / mesh networking -------------------------------------------------------
    (
        "tailscale",
        "Tailscale",
        "Zero-config mesh VPN built on WireGuard",
        "Tailscale creates a secure private network between your devices, servers, and cloud "
        "instances using WireGuard under the hood. Zero-config: works behind NAT, firewalls, "
        "and across clouds without port-forwarding. Free tier for personal use. Widely used "
        "for connecting local dev machines to production databases and staging services.",
        "devops-infrastructure",
        "tailscale/tailscale",
        18000,
        "https://tailscale.com",
        "vpn,wireguard,mesh-network,networking,security,zero-config",
        "curl -fsSL https://tailscale.com/install.sh | sh",
        "code",
    ),
    # CLI Productivity Tools -------------------------------------------------------
    (
        "fzf",
        "fzf",
        "A command-line fuzzy finder",
        "fzf is a general-purpose command-line fuzzy finder written in Go. It can be used as "
        "an interactive filter for any list: files, command history, git commits, processes. "
        "Integrates with bash, zsh, fish, and vim/neovim. One of the most-starred CLI tools "
        "on GitHub, beloved by developers who live in the terminal.",
        "cli-tools",
        "junegunn/fzf",
        64000,
        "https://github.com/junegunn/fzf",
        "cli,fuzzy-finder,terminal,productivity,search",
        "brew install fzf",
        "code",
    ),
    (
        "ripgrep",
        "ripgrep",
        "Recursively searches directories for a regex pattern",
        "ripgrep (rg) is a line-oriented search tool that recursively searches your current "
        "directory for a regex pattern. It respects .gitignore rules, skips binary files, and "
        "is 10-100x faster than grep. Written in Rust. Used internally by VS Code for its "
        "text search feature. Essential for developers who do frequent code searches.",
        "cli-tools",
        "BurntSushi/ripgrep",
        47000,
        "https://github.com/BurntSushi/ripgrep",
        "cli,grep,search,regex,rust,fast",
        "brew install ripgrep",
        "code",
    ),
    (
        "jq",
        "jq",
        "Lightweight and flexible command-line JSON processor",
        "jq is like sed for JSON data — you can use it to slice, filter, map, and transform "
        "structured data. It is written in portable C and has zero runtime dependencies. "
        "Essential for working with REST APIs, parsing log files, and scripting JSON "
        "transformations in shell scripts and CI pipelines.",
        "cli-tools",
        "jqlang/jq",
        29000,
        "https://jqlang.github.io/jq",
        "cli,json,processor,parsing,shell,devops",
        "brew install jq",
        "code",
    ),
    (
        "tmux",
        "tmux",
        "Terminal multiplexer — multiple windows in one terminal",
        "tmux lets you switch between several programs in one terminal, detach them (they keep "
        "running in the background), and reattach later. Essential for remote server work "
        "over SSH, running multiple processes side-by-side, and preserving sessions. "
        "Works with vi/emacs key bindings and is highly configurable via .tmux.conf.",
        "cli-tools",
        "tmux/tmux",
        34000,
        "https://github.com/tmux/tmux/wiki",
        "cli,terminal,multiplexer,session,ssh,productivity",
        "brew install tmux",
        "code",
    ),
    # Bundlers ----------------------------------------------------------------------
    (
        "parcel",
        "Parcel",
        "The zero configuration build tool for the web",
        "Parcel is a zero-configuration web application bundler. Drop in an HTML entry point "
        "and Parcel automatically resolves JS, CSS, images, and more — no config file required. "
        "Built-in dev server with HMR, production optimization, code splitting, and scope "
        "hoisting. Popular choice for smaller projects and rapid prototyping.",
        "frontend-frameworks",
        "parcel-bundler/parcel",
        43000,
        "https://parceljs.org",
        "bundler,build-tool,zero-config,javascript",
        "npm install parcel --save-dev",
        "code",
    ),
    # OpenAPI Documentation ---------------------------------------------------------
    (
        "redoc",
        "ReDoc",
        "OpenAPI/Swagger-generated API Reference Documentation",
        "ReDoc renders beautiful, interactive API reference documentation from OpenAPI "
        "2.0/3.0/3.1 specs. Single HTML file output, responsive three-panel layout, code "
        "samples, and deep-linking. Used by thousands of teams to publish public API docs. "
        "Available as CLI, React component, or Docker image.",
        "api-tools",
        "Redocly/redoc",
        23000,
        "https://redocly.com/redoc",
        "openapi,api-docs,swagger,documentation,rest",
        "npx @redocly/cli preview-docs openapi.yaml",
        "code",
    ),
    (
        "swagger-ui",
        "Swagger UI",
        "Visualize and interact with your API's resources without any implementation logic",
        "Swagger UI is the most widely deployed OpenAPI documentation explorer. Renders an "
        "interactive UI from any OpenAPI 2.0/3.0 spec — try endpoints directly in the browser, "
        "inspect request/response schemas, and download client SDKs. Available as standalone "
        "HTML, npm package, or Docker image.",
        "api-tools",
        "swagger-api/swagger-ui",
        26000,
        "https://swagger.io/tools/swagger-ui",
        "openapi,swagger,api-docs,rest,interactive",
        "npm install swagger-ui",
        "code",
    ),
    # Form Libraries ----------------------------------------------------------------
    (
        "tanstack-form",
        "TanStack Form",
        "Headless, framework-agnostic form state management for the web",
        "TanStack Form provides type-safe form state management for React, Vue, Solid, Angular, "
        "and Lit. Async validation, array fields, nested forms, and a tiny bundle size. Pairs "
        "naturally with Zod, Valibot, or custom validators. The headless, framework-agnostic "
        "alternative to React Hook Form.",
        "frontend-frameworks",
        "TanStack/form",
        4500,
        "https://tanstack.com/form",
        "forms,react,vue,typescript,validation,headless",
        "npm install @tanstack/react-form",
        "code",
    ),
    (
        "vee-validate",
        "VeeValidate",
        "Painless Vue.js form validation",
        "VeeValidate is the most popular form validation library for Vue.js. Composition API "
        "first with first-class TypeScript support and built-in Zod/Yup/Valibot schema "
        "adapters. Handles async rules, i18n error messages, and nested field arrays. "
        "Powers form validation in thousands of Vue 2 and Vue 3 apps.",
        "frontend-frameworks",
        "logaretm/vee-validate",
        10000,
        "https://vee-validate.logaretm.com",
        "forms,vue,validation,typescript,zod",
        "npm install vee-validate",
        "code",
    ),
    # Frontend — cross-platform / React Native UI libraries ------------------
    (
        "tamagui",
        "Tamagui",
        "Universal UI kit for React Native and React web",
        "Tamagui is a universal design system and component library that works across "
        "React Native and React for web. Write components once and run them on iOS, "
        "Android, and the browser with a shared styling API, tokens, and themes. "
        "Comes with an optimizing compiler that flattens styles to CSS and native views "
        "for near-zero runtime overhead.",
        "frontend-frameworks",
        "tamagui/tamagui",
        7000,
        "https://tamagui.dev",
        "cross-platform,react-native,web,ui,universal,styling,design-system",
        "npm install tamagui @tamagui/core",
        "code",
    ),
    (
        "nativebase",
        "NativeBase",
        "Universal design system for React Native and web",
        "NativeBase is a production-ready component library for React Native and React "
        "web. One of the most popular UI kits in the React Native ecosystem, it ships "
        "accessible, themeable components for both iOS and Android (and the web via "
        "react-native-web). Widely used across thousands of mobile apps.",
        "frontend-frameworks",
        "GeekyAnts/NativeBase",
        20000,
        "https://nativebase.io",
        "react-native,mobile,ui,cross-platform,accessible,components",
        "npm install native-base",
        "code",
    ),
    (
        "gluestack",
        "Gluestack UI",
        "Universal, accessible components for React web and native",
        "Gluestack UI is the spiritual successor to NativeBase v4. It ships headless, "
        "accessible React primitives that work on React Native and the web. Built for "
        "Tailwind CSS compatibility and React Server Components, with optional NativeWind "
        "styling. Maintained by the same team as NativeBase.",
        "frontend-frameworks",
        "gluestack/gluestack-ui",
        5000,
        "https://gluestack.io",
        "react-native,web,ui,universal,tailwind,accessible,rsc",
        "npx gluestack-ui@latest add",
        "code",
    ),
    # Project management — Linear (most popular project tool for indie/startup devs) ---
    (
        "linear",
        "Linear",
        "The issue tracker built for high-performance teams",
        "Linear is a modern project management tool for software teams. It replaces Jira "
        "with a radically faster, keyboard-first interface for managing issues, sprints, "
        "and roadmaps. Features Git sync, cycle planning, triage, and project analytics. "
        "The API and MCP integration let AI agents create and update issues.",
        "project-management",
        "linear/linear",
        10000,
        "https://linear.app",
        "project-management,issues,sprints,roadmap,productivity,api",
        "",
        "saas",
    ),
    # DevOps — HashiCorp Packer (machine image builder) -------------------------
    (
        "packer",
        "Packer",
        "Build identical machine images for multiple platforms from a single config",
        "Packer is an open-source tool from HashiCorp that automates the creation of "
        "identical machine images for multiple platforms (AWS AMI, Docker, Vagrant, "
        "VMware, GCP, Azure) from a single template. Uses HCL or JSON configuration. "
        "Integrates with Ansible, Chef, and Puppet for provisioning.",
        "devops-infrastructure",
        "hashicorp/packer",
        15000,
        "https://www.packer.io",
        "image-build,automation,devops,hashicorp,infrastructure,ami,docker",
        "brew install packer",
        "code",
    ),
    # ── Passes 89-92 (autonomous improvement cycle) ──────────────────────────
    # Developer Tools — Terminal emulators / editors
    (
        "alacritty",
        "Alacritty",
        "Fast, cross-platform, OpenGL terminal emulator",
        "Alacritty is the fastest terminal emulator in existence, written in Rust. "
        "Uses GPU rendering via OpenGL for near-zero latency. Highly configurable "
        "via YAML/TOML. Ships with sensible defaults. No tabs or splits built in — "
        "pairs with tmux or Zellij. Cross-platform: Linux, macOS, Windows, BSD.",
        "developer-tools",
        "BurntSushi/alacritty",
        56000,
        "https://alacritty.org",
        "terminal,emulator,gpu,rust,fast,cross-platform",
        "brew install --cask alacritty",
        "code",
    ),
    (
        "helix",
        "Helix",
        "A post-modern modal text editor",
        "Helix is a terminal-based modal text editor inspired by Kakoune and Neovim. "
        "Written in Rust, it features tree-sitter syntax highlighting, LSP support, "
        "multiple selections, and a selection-first editing model. No plugin system "
        "required — LSP, DAP, tree-sitter grammars, and themes ship out of the box.",
        "developer-tools",
        "helix-editor/helix",
        35000,
        "https://helix-editor.com",
        "editor,modal,rust,lsp,treesitter,vim-alternative",
        "brew install helix",
        "code",
    ),
    (
        "fish",
        "Fish Shell",
        "A smart and user-friendly command line shell",
        "Fish is a Unix shell designed for interactive use. Its standout features are "
        "autosuggestions based on history and completions, a clean scripting syntax "
        "with no arcane quoting rules, web-based configuration, and out-of-the-box "
        "syntax highlighting. A drop-in Bash/Zsh replacement for everyday terminal work.",
        "cli-tools",
        "fish-shell/fish-shell",
        26000,
        "https://fishshell.com",
        "shell,cli,interactive,autosuggestions,scripting,bash-alternative",
        "brew install fish",
        "code",
    ),
    (
        "hardhat",
        "Hardhat",
        "Ethereum development environment for professionals",
        "Hardhat is a development environment for Ethereum smart contracts. Compile, "
        "test, debug, and deploy Solidity contracts. Ships with Hardhat Network — a "
        "local Ethereum node for testing. Extensive plugin ecosystem (OpenZeppelin, "
        "Ethers.js, Viem, Foundry forking). The most widely used Ethereum dev tool.",
        "developer-tools",
        "NomicFoundation/hardhat",
        7000,
        "https://hardhat.org",
        "ethereum,blockchain,solidity,smart-contracts,testing,web3",
        "npm install --save-dev hardhat",
        "code",
    ),
    (
        "react-three-fiber",
        "React Three Fiber",
        "A React renderer for Three.js",
        "React Three Fiber (R3F) is a React renderer for Three.js that lets you "
        "build Three.js scenes declaratively with React components. It abstracts "
        "away the Three.js boilerplate while giving you full access to the Three.js "
        "API. Part of the pmndrs ecosystem alongside Drei (helpers), Rapier "
        "(physics), and React Spring (animation).",
        "frontend-frameworks",
        "pmndrs/react-three-fiber",
        27000,
        "https://docs.pmnd.rs/react-three-fiber",
        "three,3d,webgl,react,animation",
        "npm install @react-three/fiber three",
        "code",
    ),
    (
        "bentoml",
        "BentoML",
        "The easiest way to serve AI apps and models",
        "BentoML is an open-source model serving framework that lets you build, "
        "ship, and scale AI applications. Define serving logic in Python, package "
        "models with dependencies, and deploy to any cloud or on-premises. "
        "Supports PyTorch, TensorFlow, scikit-learn, XGBoost, LLMs via vLLM/Ollama, "
        "and any Python model. Handles batching, streaming, and multi-model pipelines.",
        "ai-automation",
        "bentoml/bentoml",
        7000,
        "https://bentoml.com",
        "ml,model-serving,llm,python,deployment,inference",
        "pip install bentoml",
        "code",
    ),
    (
        "sanic",
        "Sanic",
        "Build fast. Run fast.",
        "Sanic is an async Python web framework and server built for performance. "
        "It supports async/await syntax natively and is one of the fastest Python "
        "web frameworks available. Suitable for building REST APIs, WebSocket servers, "
        "and microservices. Ships with built-in HTTP/2, TLS, and streaming support.",
        "api-tools",
        "sanic-org/sanic",
        18000,
        "https://sanic.dev",
        "python,async,web-framework,rest-api,http2",
        "pip install sanic",
        "code",
    ),
    (
        "activemq",
        "Apache ActiveMQ",
        "The most popular open-source, multi-protocol message broker",
        "Apache ActiveMQ is a widely deployed open-source message broker that "
        "supports JMS, AMQP, MQTT, OpenWire, STOMP, and WebSocket protocols. "
        "Used extensively in enterprise Java stacks for reliable async messaging. "
        "ActiveMQ Classic and ActiveMQ Artemis handle millions of messages "
        "per second and integrate with Spring Boot, Camel, and Quarkus.",
        "message-queue",
        "apache/activemq",
        2000,
        "https://activemq.apache.org",
        "message-broker,jms,amqp,mqtt,java,enterprise",
        "",
        "code",
    ),
    (
        "foundry-eth",
        "Foundry",
        "Blazing fast, portable, and modular toolkit for Ethereum development",
        "Foundry is a smart contract development toolchain written in Rust. "
        "It ships Forge (testing framework), Cast (CLI for EVM interaction), "
        "Anvil (local Ethereum node), and Chisel (Solidity REPL). Tests are written "
        "in Solidity — no JavaScript required. Significantly faster than Hardhat for "
        "compilation and testing, with fuzzing and invariant testing built in.",
        "developer-tools",
        "foundry-rs/foundry",
        9000,
        "https://book.getfoundry.sh",
        "ethereum,blockchain,solidity,smart-contracts,testing,web3",
        "curl -L https://foundry.paradigm.xyz | bash",
        "code",
    ),
    (
        "earthly",
        "Earthly",
        "Reproducible builds in containers",
        "Earthly is an open-source build automation tool that combines the best of "
        "Dockerfiles and Makefiles. Each build target runs in a container, making "
        "builds reproducible and portable across dev, CI, and production. Works with "
        "any language and integrates with GitHub Actions, CircleCI, and Jenkins. "
        "Supports build caching, parallelism, and cross-platform builds.",
        "devops-infrastructure",
        "earthly-technologies/earthly",
        12000,
        "https://earthly.dev",
        "build,ci,containers,reproducible,makefile-alternative,devops",
        "brew install earthly/earthly/earthly",
        "code",
    ),
    (
        "edgedb",
        "EdgeDB",
        "A graph-relational database with a type-safe query language",
        "EdgeDB is a next-generation database built on PostgreSQL that combines "
        "the relational model with object-oriented concepts. Features a rich type "
        "system, EdgeQL (a more expressive alternative to SQL), built-in migrations, "
        "and a schema definition language. Ideal for complex data models. "
        "Client libraries for Python, TypeScript, Go, and Rust.",
        "database",
        "edgedb/edgedb",
        14000,
        "https://edgedb.com",
        "database,postgresql,orm,typescript,graph-relational,edgeql",
        "pip install edgedb",
        "code",
    ),
    (
        "cockroachdb",
        "CockroachDB",
        "The cloud-native distributed SQL database",
        "CockroachDB is a distributed SQL database built for cloud-native apps. "
        "Fully Postgres-compatible wire protocol, so existing drivers and ORMs work "
        "without changes. Automatic sharding, multi-region replication, and "
        "serialisable transactions. Self-host with the open-source edition or use "
        "CockroachDB Serverless / Dedicated for managed deployments.",
        "database",
        "cockroachdb/cockroach",
        30000,
        "https://cockroachlabs.com",
        "database,sql,postgresql,distributed,cloud-native,multi-region",
        "brew install cockroachdb/tap/cockroach",
        "code",
    ),
    (
        "openobserve",
        "OpenObserve",
        "Cloud-native observability platform at 140x lower storage cost",
        "OpenObserve (O2) is an open-source observability platform for logs, metrics, "
        "traces, and RUM. Written in Rust, it uses object storage (S3/GCS/MinIO) "
        "instead of spinning disks — yielding 140× cheaper storage than Elasticsearch. "
        "Drop-in replacement for Elasticsearch/OpenSearch log ingestion APIs. "
        "Single binary, no external dependencies, deploys in under 2 minutes.",
        "monitoring-uptime",
        "openobserve/openobserve",
        14000,
        "https://openobserve.ai",
        "observability,logs,metrics,traces,rust,elasticsearch-alternative,monitoring",
        "curl -L https://raw.githubusercontent.com/openobserve/openobserve/main/deploy/quick-install.sh | bash",
        "code",
    ),
    (
        "authentik",
        "Authentik",
        "The authentication glue you need",
        "Authentik is a self-hosted identity provider and SSO solution. Works as "
        "an OAuth2, OpenID Connect, SAML, LDAP, or SCIM provider — a drop-in "
        "replacement for Okta, Auth0, or Azure AD in self-hosted environments. "
        "Ships with pre-built flows for enrollment, recovery, and MFA. "
        "Deploy via Docker Compose or Helm chart in minutes.",
        "authentication",
        "goauthentik/authentik",
        15000,
        "https://goauthentik.io",
        "auth,sso,oauth2,oidc,saml,self-hosted,identity,okta-alternative",
        "docker compose up -d",
        "code",
    ),
    (
        "plausible",
        "Plausible Analytics",
        "Simple, privacy-friendly Google Analytics alternative",
        "Plausible Analytics is an open-source, privacy-friendly web analytics tool. "
        "Lightweight script (< 1KB), no cookies, GDPR compliant, and self-hostable. "
        "Shows page views, bounce rate, referrers, and custom events in a clean dashboard. "
        "Used by over 12,000 paying customers and thousands of self-hosted deployments. "
        "The go-to Google Analytics alternative for privacy-conscious developers and indie makers.",
        "analytics-metrics",
        "plausible/analytics",
        21000,
        "https://plausible.io",
        "analytics,privacy,google-analytics-alternative,gdpr,open-source,self-hosted",
        "docker run -d plausible/analytics",
        "code",
    ),
    (
        "umami",
        "Umami",
        "Simple, fast, privacy-focused website analytics",
        "Umami is a simple, fast, privacy-focused open-source analytics platform. "
        "Self-host on your own infrastructure or use Umami Cloud. Collects only the "
        "data you need — no cookies, no tracking across sites, fully GDPR compliant. "
        "Clean dashboard with realtime data, custom events, and UTM tracking. "
        "23k+ GitHub stars; one of the most popular self-hosted analytics solutions.",
        "analytics-metrics",
        "umami-software/umami",
        23000,
        "https://umami.is",
        "analytics,privacy,self-hosted,open-source,gdpr,realtime",
        "docker pull ghcr.io/umami-software/umami:postgresql-latest",
        "code",
    ),
    (
        "kamal",
        "Kamal",
        "Deploy web apps anywhere — from bare metal to cloud VMs",
        "Kamal is a modern Docker-based deployment tool by 37signals (makers of Basecamp). "
        "Deploy any Dockerised app to any server (bare metal, VPS, cloud VM) with zero "
        "downtime via container rollover. Manages rolling deployments, secrets, and "
        "health checks. Originally built for Rails but works with any stack. "
        "The simplest path from a Dockerfile to production without a PaaS.",
        "devops-infrastructure",
        "basecamp/kamal",
        11000,
        "https://kamal-deploy.org",
        "deployment,docker,paas,devops,rails,zero-downtime,vps",
        "gem install kamal",
        "code",
    ),
    (
        "netdata",
        "Netdata",
        "Real-time performance monitoring for servers, VMs, and containers",
        "Netdata is an open-source, real-time monitoring solution that collects thousands "
        "of metrics per second with 1-second granularity. Zero-configuration auto-discovery "
        "of apps, databases, and services. Ships with 800+ integrations. "
        "Can run as a standalone agent (very low overhead) or as a distributed observability "
        "cloud. The go-to tool for detailed server-level performance visibility without the "
        "cost of Datadog or New Relic.",
        "monitoring-uptime",
        "netdata/netdata",
        73000,
        "https://netdata.cloud",
        "monitoring,metrics,real-time,performance,linux,self-hosted,observability",
        "curl https://get.netdata.cloud/kickstart.sh | bash",
        "code",
    ),
    (
        "hatch",
        "Hatch",
        "Modern, extensible Python project manager",
        "Hatch is the official Python project manager from the Python Packaging Authority (PyPA). "
        "Manage virtual environments, build distributions, run tests across Python versions, "
        "and publish to PyPI — all from one tool. Uses pyproject.toml as the single source "
        "of truth. Plugin-based architecture makes it extensible. The recommended successor "
        "to setup.py and tox for new Python projects.",
        "developer-tools",
        "pypa/hatch",
        5000,
        "https://hatch.pypa.io",
        "python,package-manager,virtual-env,build,pypi,project-manager",
        "pip install hatch",
        "code",
    ),
    # Database — version-controlled SQL -------------------------------------------------
    (
        "dolt",
        "Dolt",
        "Git for data — version-controlled SQL database",
        "Dolt is the world's first version-controlled SQL database. Branch, merge, "
        "diff, and rollback your data like you do your code. DoltHub hosts public "
        "and private databases. Compatible with MySQL protocol — works with any MySQL "
        "client or ORM. Perfect for reproducible data pipelines and auditability.",
        "database",
        "dolthub/dolt",
        18000,
        "https://www.dolthub.com",
        "database,sql,mysql,version-control,git,data-versioning",
        "brew install dolt",
        "code",
    ),
    # DevOps — container registries ------------------------------------------------------
    (
        "harbor",
        "Harbor",
        "Open-source container registry with RBAC, replication, and vulnerability scanning",
        "Harbor is a CNCF Graduated open-source container registry that secures "
        "artifacts with policies and RBAC. Includes image replication across registries, "
        "vulnerability scanning via Trivy/Clair, content signing via Notary, and a "
        "rich web UI. Self-host on Kubernetes or bare metal.",
        "devops-infrastructure",
        "goharbor/harbor",
        24000,
        "https://goharbor.io",
        "container-registry,docker,oci,kubernetes,security,self-hosted",
        "helm install harbor harbor/harbor",
        "code",
    ),
    # Feature Flags — Ruby ecosystem -----------------------------------------------------
    (
        "flipper",
        "Flipper",
        "Feature flags for Ruby and Rails applications",
        "Flipper is the most popular feature flagging gem in the Ruby ecosystem. "
        "Store flags in memory, Redis, ActiveRecord, or any custom adapter. "
        "Boolean, percentage, group, and actor-based targeting. Flipper Cloud "
        "adds a hosted dashboard with audit log and team collaboration.",
        "feature-flags",
        "flippercloud/flipper",
        3400,
        "https://www.flippercloud.io",
        "feature-flags,ruby,rails,percentage-rollout,self-hosted",
        "gem install flipper",
        "code",
    ),
    # DevOps / BaaS — Firebase alternative ----------------------------------------------
    (
        "nhost",
        "Nhost",
        "The open-source Firebase alternative with GraphQL",
        "Nhost is a Firebase alternative built on open standards: PostgreSQL, "
        "Hasura GraphQL, Auth, and File Storage — all in one platform. "
        "Instant GraphQL API auto-generated from your database schema, built-in "
        "auth with social providers, serverless functions, and a generous free tier. "
        "Self-hostable via Docker Compose.",
        "devops-infrastructure",
        "nhost/nhost",
        8000,
        "https://nhost.io",
        "baas,firebase-alternative,graphql,hasura,postgres,auth,storage,self-hosted",
        "npm install @nhost/react",
        "code",
    ),
    # API Tools — Protobuf toolchain -----------------------------------------------------
    (
        "buf",
        "Buf",
        "The best way to use Protobuf",
        "Buf is a modern developer-first Protobuf toolchain. It replaces the "
        "fragile protoc workflow with a single CLI: lint, format, detect breaking "
        "changes, generate code, and push to the Buf Schema Registry. "
        "buf.build hosts a public schema registry for sharing Protobuf APIs. "
        "Used by Stripe, DoorDash, and many API-first companies.",
        "api-tools",
        "bufbuild/buf",
        9000,
        "https://buf.build",
        "protobuf,grpc,api,rpc,code-generation,linting",
        "brew install bufbuild/buf/buf",
        "code",
    ),
]


def get_category_id(conn: sqlite3.Connection, slug: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM categories WHERE slug=?", (slug,)
    ).fetchone()
    return row[0] if row else None


def slug_exists(conn: sqlite3.Connection, slug: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM tools WHERE slug=?", (slug,)
    ).fetchone()
    return row is not None


def insert_tool(conn: sqlite3.Connection, tool: tuple) -> None:
    (
        slug, name, tagline, description, category_slug, github_repo,
        github_stars, website_url, tags, install_command, source_type,
    ) = tool

    category_id = get_category_id(conn, category_slug)
    if category_id is None:
        print(f"  SKIP {slug} — category '{category_slug}' not found")
        return

    conn.execute(
        """INSERT INTO tools (
            slug, name, tagline, description, category_id,
            github_repo, github_stars, website_url, tags,
            install_command, source_type, status, quality_score
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'approved', 80)""",
        (
            slug, name, tagline, description, category_id,
            github_repo, github_stars, website_url, tags,
            install_command, source_type,
        ),
    )
    print(f"  INSERT {slug} ({category_slug})")


def main() -> None:
    print(f"Connecting to {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    inserted = 0
    skipped = 0

    for tool in TOOLS:
        slug = tool[0]
        if slug_exists(conn, slug):
            print(f"  SKIP   {slug} (already exists)")
            skipped += 1
        else:
            insert_tool(conn, tool)
            inserted += 1

    conn.commit()
    conn.close()

    print(f"\nDone: {inserted} inserted, {skipped} skipped")
    if inserted > 0:
        print("Next step: rebuild FTS index on production —")
        print("  INSERT INTO tools_fts(tools_fts) VALUES('rebuild');")
        print("  PRAGMA wal_checkpoint(TRUNCATE);")


if __name__ == "__main__":
    main()

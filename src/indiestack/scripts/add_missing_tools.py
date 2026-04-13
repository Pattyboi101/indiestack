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

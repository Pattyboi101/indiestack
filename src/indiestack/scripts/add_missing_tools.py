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
    # Background jobs — durable execution ----------------------------------------
    (
        "temporal",
        "Temporal",
        "Open source durable execution system",
        "Temporal is a durable execution platform for running reliable long-running "
        "workflows as code. Automatically handles retries, timeouts, and state persistence. "
        "SDKs for Go, Java, TypeScript, Python, and .NET.",
        "background-jobs",
        "temporalio/temporal",
        12000,
        "https://temporal.io",
        "workflow,durable-execution,distributed,reliability",
        "brew install temporal",
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

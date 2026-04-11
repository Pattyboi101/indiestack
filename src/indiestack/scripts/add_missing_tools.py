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

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
    # ── Frontend Meta-frameworks & Build Tools ────────────────────────
    {
        "name": "Next.js",
        "slug": "nextjs",
        "tagline": "The React Framework for the Web",
        "description": "Next.js gives you the best developer experience with all the features you need: hybrid static & server rendering, TypeScript support, smart bundling, route pre-fetching, and more.",
        "url": "https://nextjs.org",
        "github_url": "https://github.com/vercel/next.js",
        "github_stars": 127000,
        "category_slug": "frontend-frameworks",
        "tags": "react,nextjs,ssr,ssg,fullstack,vercel",
        "source_type": "code",
    },
    {
        "name": "Vite",
        "slug": "vite",
        "tagline": "Next generation frontend tooling",
        "description": "Vite is a build tool that aims to provide a faster and leaner development experience for modern web projects. It uses native ES modules for instant server start and lightning-fast HMR.",
        "url": "https://vitejs.dev",
        "github_url": "https://github.com/vitejs/vite",
        "github_stars": 68000,
        "category_slug": "frontend-frameworks",
        "tags": "bundler,build-tool,dev-server,hmr,fast,esm",
        "source_type": "code",
    },
    {
        "name": "Remix",
        "slug": "remix",
        "tagline": "Build Better Websites",
        "description": "Remix is a full stack web framework that lets you focus on the user interface and work back through web standards to deliver a fast, slick, and resilient user experience.",
        "url": "https://remix.run",
        "github_url": "https://github.com/remix-run/remix",
        "github_stars": 30000,
        "category_slug": "frontend-frameworks",
        "tags": "react,ssr,fullstack,web-standards,routing",
        "source_type": "code",
    },
    {
        "name": "Astro",
        "slug": "astro",
        "tagline": "The web framework for content-driven websites",
        "description": "Astro builds fast content sites, powerful web applications, dynamic server APIs, and everything in-between. Ship less JavaScript with Astro's island architecture.",
        "url": "https://astro.build",
        "github_url": "https://github.com/withastro/astro",
        "github_stars": 46000,
        "category_slug": "frontend-frameworks",
        "tags": "static,ssg,islands,performance,content,multi-framework",
        "source_type": "code",
    },
    {
        "name": "SolidJS",
        "slug": "solidjs",
        "tagline": "Simple and performant reactivity for building user interfaces",
        "description": "SolidJS is a declarative JavaScript library for creating user interfaces. Instead of using a virtual DOM, it compiles templates to real DOM nodes and updates them with fine-grained reactivity.",
        "url": "https://solidjs.com",
        "github_url": "https://github.com/solidjs/solid",
        "github_stars": 32000,
        "category_slug": "frontend-frameworks",
        "tags": "solidjs,reactive,no-virtual-dom,performance,ui",
        "source_type": "code",
    },
    {
        "name": "Qwik",
        "slug": "qwik",
        "tagline": "No hydration, auto lazy-loading, edge-ready",
        "description": "Qwik is a new kind of web framework that can deliver instant loading web applications at any size or complexity. Sites pre-render to HTML and resumability replaces hydration entirely.",
        "url": "https://qwik.dev",
        "github_url": "https://github.com/QwikDev/qwik",
        "github_stars": 21000,
        "category_slug": "frontend-frameworks",
        "tags": "resumability,performance,edge,ssr,no-hydration",
        "source_type": "code",
    },
    {
        "name": "TanStack Query",
        "slug": "tanstack-query",
        "tagline": "Powerful asynchronous state management for TS/JS",
        "description": "TanStack Query (formerly React Query) gives you declarative, always-up-to-date auto-managed queries and mutations that improve your developer and user experience.",
        "url": "https://tanstack.com/query",
        "github_url": "https://github.com/TanStack/query",
        "github_stars": 42000,
        "category_slug": "frontend-frameworks",
        "tags": "data-fetching,caching,state-management,react,vue,svelte",
        "source_type": "code",
    },
    {
        "name": "SWC",
        "slug": "swc",
        "tagline": "Rust-based platform for the Web",
        "description": "SWC is an extensible Rust-based platform for the next generation of fast developer tools. It can be used for both compilation and bundling, and is 20x faster than Babel.",
        "url": "https://swc.rs",
        "github_url": "https://github.com/swc-project/swc",
        "github_stars": 31000,
        "category_slug": "frontend-frameworks",
        "tags": "transpiler,bundler,rust,fast,babel-alternative,build-tool",
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

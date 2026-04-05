"""Insert approved tools for major frontend frameworks/libraries if not already in DB.

Run on production:
    python3 /app/src/indiestack/scripts/add_missing_tools.py

Or via SSH:
    flyctl ssh console -C "python3 /app/src/indiestack/scripts/add_missing_tools.py"
"""

import sqlite3
import sys

DB_PATH = "/app/db/indiestack.db"

TOOLS = [
    {
        "slug": "react",
        "name": "React",
        "tagline": "The library for web and native user interfaces",
        "description": "React is a declarative, efficient, and flexible JavaScript library for building user interfaces. It lets you compose complex UIs from small and isolated pieces of code called components. Maintained by Meta and a community of individual developers and companies.",
        "url": "https://react.dev",
        "github": "facebook/react",
        "stars": 230000,
        "category_slug": "frontend-frameworks",
        "tags": "javascript,ui-library,components,hooks",
    },
    {
        "slug": "vuejs",
        "name": "Vue.js",
        "tagline": "The progressive JavaScript framework",
        "description": "Vue.js is an approachable, performant and versatile framework for building web user interfaces. It builds on top of standard HTML, CSS and JavaScript, and provides a declarative and component-based programming model that helps you efficiently develop user interfaces.",
        "url": "https://vuejs.org",
        "github": "vuejs/vue",
        "stars": 208000,
        "category_slug": "frontend-frameworks",
        "tags": "javascript,framework,components,reactive",
    },
    {
        "slug": "svelte",
        "name": "Svelte",
        "tagline": "Cybernetically enhanced web apps",
        "description": "Svelte is a radical new approach to building user interfaces. Whereas traditional frameworks like React and Vue do the bulk of their work in the browser, Svelte shifts that work into a compile step that happens when you build your app — resulting in smaller bundles and faster apps.",
        "url": "https://svelte.dev",
        "github": "sveltejs/svelte",
        "stars": 80000,
        "category_slug": "frontend-frameworks",
        "tags": "javascript,framework,compiler,no-virtual-dom",
    },
    {
        "slug": "angular",
        "name": "Angular",
        "tagline": "The modern web developer's platform",
        "description": "Angular is a development platform, built on TypeScript, for building mobile and desktop web applications. It includes a framework, a collection of integrated libraries, and developer tooling. Angular is maintained by the Google team.",
        "url": "https://angular.dev",
        "github": "angular/angular",
        "stars": 96000,
        "category_slug": "frontend-frameworks",
        "tags": "typescript,framework,spa,enterprise",
    },
    {
        "slug": "zustand",
        "name": "Zustand",
        "tagline": "A small, fast and scalable bearbones state-management solution",
        "description": "Zustand is a small, fast, and scalable state management solution for React. It has a comfy API based on hooks and is not boilerplatey or opinionated. It does not use Context, making it very easy to integrate with any React setup.",
        "url": "https://zustand-demo.pmnd.rs",
        "github": "pmndrs/zustand",
        "stars": 48000,
        "category_slug": "frontend-frameworks",
        "tags": "state-management,react,hooks,lightweight",
    },
    {
        "slug": "jotai",
        "name": "Jotai",
        "tagline": "Primitive and flexible state management for React",
        "description": "Jotai takes an atomic approach to global React state management. It was built to solve extra re-render issues in React context and to eliminate the need for memoization. Atoms are small pieces of state you compose together to build complex state.",
        "url": "https://jotai.org",
        "github": "pmndrs/jotai",
        "stars": 19000,
        "category_slug": "frontend-frameworks",
        "tags": "state-management,react,atomic,typescript",
    },
    {
        "slug": "webpack",
        "name": "Webpack",
        "tagline": "A static module bundler for modern JavaScript applications",
        "description": "Webpack is a static module bundler for modern JavaScript applications. When webpack processes your application, it internally builds a dependency graph from one or more entry points and then combines every module your project needs into one or more bundles.",
        "url": "https://webpack.js.org",
        "github": "webpack/webpack",
        "stars": 64000,
        "category_slug": "frontend-frameworks",
        "tags": "bundler,build-tool,javascript,modules",
    },
    {
        "slug": "esbuild",
        "name": "esbuild",
        "tagline": "An extremely fast bundler for the web",
        "description": "esbuild is an extremely fast JavaScript and CSS bundler and minifier, written in Go. It is typically 10-100x faster than other bundlers. It supports JS, TS, JSX, TSX, CSS, and JSON. Used as the foundation of Vite and other modern build tools.",
        "url": "https://esbuild.github.io",
        "github": "evanw/esbuild",
        "stars": 38000,
        "category_slug": "frontend-frameworks",
        "tags": "bundler,build-tool,fast,go",
    },
    {
        "slug": "upstash",
        "name": "Upstash",
        "tagline": "Serverless data platform for Redis, Kafka and QStash",
        "description": "Upstash is a serverless data platform offering Redis, Kafka, and QStash. Designed for modern cloud-native and serverless applications, Upstash provides per-request pricing with zero infrastructure management. Works seamlessly with Vercel, Cloudflare Workers, AWS Lambda, and more.",
        "url": "https://upstash.com",
        "github": "upstash/upstash-redis",
        "stars": 3000,
        "category_slug": "caching",
        "tags": "redis,serverless,caching,kafka,edge",
    },
    {
        "slug": "resend",
        "name": "Resend",
        "tagline": "Email for developers",
        "description": "Resend is the email platform built for developers. It provides a simple REST API and SDKs for Node, Python, Ruby, PHP, Go, and more. Features include React email templates, webhooks, domain verification, and a dashboard for monitoring email deliverability.",
        "url": "https://resend.com",
        "github": "resendlabs/resend-node",
        "stars": 8000,
        "category_slug": "email-marketing",
        "tags": "email,transactional,developer-friendly,react-email",
    },
]


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    inserted = []
    skipped = []

    for tool in TOOLS:
        # Check if slug already exists
        row = cur.execute("SELECT id FROM tools WHERE slug=?", (tool["slug"],)).fetchone()
        if row:
            skipped.append(tool["slug"])
            continue

        # Look up category_id
        cat_row = cur.execute(
            "SELECT id FROM categories WHERE slug=?", (tool["category_slug"],)
        ).fetchone()
        if not cat_row:
            print(f"  WARNING: category '{tool['category_slug']}' not found for {tool['slug']} — skipping")
            skipped.append(tool["slug"])
            continue

        category_id = cat_row["id"]
        github_url = f"https://github.com/{tool['github']}"

        cur.execute(
            """
            INSERT INTO tools
                (name, slug, tagline, description, url, category_id, tags, status,
                 github_url, github_stars, source_type, created_at)
            VALUES
                (?, ?, ?, ?, ?, ?, ?, 'approved', ?, ?, 'code', CURRENT_TIMESTAMP)
            """,
            (
                tool["name"],
                tool["slug"],
                tool["tagline"],
                tool["description"],
                tool["url"],
                category_id,
                tool["tags"],
                github_url,
                tool["stars"],
            ),
        )
        inserted.append(tool["slug"])

    conn.commit()

    if inserted:
        # Rebuild FTS index so new tools appear in search immediately
        cur.execute("INSERT INTO tools_fts(tools_fts) VALUES('rebuild')")
        cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.commit()
        print(f"Inserted {len(inserted)} tools: {', '.join(inserted)}")
    else:
        print("No new tools to insert.")

    if skipped:
        print(f"Skipped {len(skipped)} already-present tools: {', '.join(skipped)}")

    conn.close()


if __name__ == "__main__":
    main()

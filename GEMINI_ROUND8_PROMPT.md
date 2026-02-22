# IndieStack — Round 8 Brainstorm Prompt for Gemini

You are a product strategist helping two co-founders (Patrick & Ed) brainstorm the next round of features for **IndieStack** — a curated marketplace for indie SaaS tools. The tagline is "Save your tokens — use indie builds."

## What IndieStack Is

A FastAPI + SQLite marketplace where indie makers list their SaaS tools and developers discover them instead of building from scratch. Deployed on Fly.io. Pure Python HTML templates (no React/Jinja2). Revenue model: makers keep ~92% of every sale (5% platform fee + ~3% Stripe). Pro tier: 3% platform fee.

## Current Feature Set (after 7 rounds of building)

### Core
- 65 approved tools across 20 categories (mostly free listings, growing fast via Ed's GitHub scraping bots)
- Full-text search (FTS5) with filters: Free/Paid pills, Sort (relevance/upvotes/newest/price), Verified toggle, Category dropdown
- Category browse pages (20 categories, paginated) — NO filters on these yet
- Tool detail pages with JSON-LD, badges (Verified, Ejectable, Pulse), reviews, changelogs
- Maker profiles with bio, indie status badges (Solo Maker / Small Team)
- Curated collections + tool comparisons
- "Replaces" field — tools declare which big-tech tools they replace

### Commerce
- Stripe Connect — makers connect Stripe accounts, checkout with destination charges
- **Indie Ring** (Round 7) — Makers get 50% off other makers' tools. Bootstraps GMV.
- **Vibe Stacks** (Round 7) — Admin-curated tool bundles at 15% discount, one-click checkout with Stripe Transfers to distribute to each maker
- Pro subscription tier (3% vs 5% commission)
- Earnings calculator on submit forms

### MCP & API
- JSON API: `GET /api/tools/search` and `GET /api/tools/{slug}` with integration snippets
- MCP Server: `search_indie_tools` and `get_tool_details` — works with Claude Code, Cursor, Windsurf
- Dynamic SVG badges: `/api/badge/{slug}.svg` for makers, `/api/badge/buyer/{token}.svg` for buyers
- Integration snippets (Python + cURL) on purchase delivery pages

### SEO & Content
- Programmatic "Alternatives to X" pages with Featured/boosted placements
- Sitemap with tools, categories, makers, collections, alternatives, stacks
- OG meta + JSON-LD on all pages
- Content pages: about, terms, privacy, FAQ
- Maker updates feed (changelogs, launches, milestones)

### Trust System
- **Verified badge** — paid verification via Stripe
- **Certified Ejectable badge** — clean data export / no lock-in
- **Maker Pulse badge** — color-coded freshness (green <30d, amber <90d, gray >90d)
- **Indie status badges** — Solo Maker / Small Team
- **"Tokens Saved" counters** — per-category estimates on tool pages, landing stats, buyer dashboard

### User System
- Auth, email verification, password reset
- Wishlists, reviews & ratings (verified purchase badges)
- Notifications (upvotes, wishlist saves)
- Dashboard: tools management, sales, saved tools, badge embeds
- **Buyer badges** (Round 7) — embeddable "Built with IndieStack | Saved Xk tokens" SVG for READMEs

## Current State & Growth

**Ed's bots are working.** We now have 65 approved tools (up from 26 seed tools). Ed's scraping GitHub for indie SaaS projects, linking their repos, and bulk-submitting them as free listings. The site is starting to look alive and organic.

**Problem:** With 65+ tools and growing, **discovery is becoming the bottleneck.** Right now:
- `/search` has good filters (price, sort, category, verified) but requires typing a query
- `/category/{slug}` pages have NO filters — just a paginated list of tools
- `/browse` is just a grid of category links — no unified tool browsing
- No way to filter by: tags, "ejectable", recently updated (pulse), has API, open-source, self-hostable
- No tag-based browsing even though tools have tags in the database
- All 65 tools are free — pricing filters are irrelevant right now, but will matter when paid tools arrive

**What we want from Round 8:** Make it dramatically easier to discover and filter tools as the catalog grows from 65 → 200+ → 1000+.

## Tech Constraints
- Pure Python string HTML templates — no frontend framework, no Jinja2
- SQLite database (single file, aiosqlite)
- Deployed on Fly.io with single machine
- No external services except Stripe + Gmail SMTP
- Each route file is a self-contained FastAPI router
- Shared components in `components.py` (page_shell, badges, cards, filter bars)

## What We Care About
- **Build speed**: We ship fast. 1-2 hour features are ideal.
- **Discovery at scale**: Features that work at 100 tools AND 1000 tools
- **Organic SEO**: More programmatic pages that rank (like alternatives pages do)
- **Developer trust signals**: Anything that makes a developer think "this marketplace is legit"
- **Conversion**: Features that turn a browser into a buyer or a maker
- **Stickiness**: What brings people back daily/weekly?

## What We DON'T Want
- Complex frontend frameworks or build steps
- Features requiring new external services
- Anything that needs ongoing manual curation at scale
- Features that duplicate existing functionality
- Over-engineered solutions for problems we don't have yet

## Specific Questions We Want Your Help With

1. **How should we redesign the browse/discovery experience?** Category pages need filters. Should we add a unified `/explore` page with faceted filtering? Should tags be first-class citizens?

2. **What filters actually matter for developers choosing indie tools?** Beyond price and category — what signals help a developer decide "this is the right tool"? (Has API? Open source? Self-hostable? Recently updated? Team size? etc.)

3. **How do we leverage the "Replaces" data?** We have tools declaring what big-tech products they replace. Can we do more with this data beyond alternatives pages?

4. **What search/browse patterns work for marketplaces at our stage (50-200 tools)?** We're not yet big enough for complex recommendation engines, but we're too big for "just show everything."

5. **How do we make the MCP server a better discovery channel?** Right now it returns search results. Could it be smarter — recommending stacks, suggesting alternatives, etc.?

---

## Your Task

Brainstorm **8-12 feature ideas** focused on **search, discovery, and filtering**. For each idea, provide:

1. **Name** — a short, catchy feature name
2. **One-liner** — what it does in one sentence
3. **Why it matters** — the strategic value (discovery, conversion, SEO, or stickiness)
4. **Build estimate** — files touched and rough complexity (small/medium/large)
5. **Impact score** — rate 1-5 for each: build speed, discovery improvement, scalability (works at 1000+ tools)

Then **rank your top 3** by (build speed × impact) and explain why those 3 should be built first.

Be creative. Think about how Algolia, Product Hunt, GitHub Marketplace, and npm handle discovery at different scales. Think about what a developer browsing IndieStack at 2am wants to find in under 30 seconds. Think about what programmatic pages we can generate from existing data to capture more long-tail SEO traffic.

Some directions to explore (but don't limit yourself):
- Faceted filtering on browse/category pages (tags, badges, freshness, API availability)
- Tag-based browsing and tag landing pages (SEO play)
- "Smart browse" — a unified /explore page replacing the current category grid
- Search improvements (autocomplete, instant results, fuzzy matching)
- "Similar tools" recommendations on tool detail pages
- MCP server intelligence (recommend stacks, suggest alternatives based on context)
- Programmatic SEO pages beyond alternatives (e.g., "/tools-with-api", "/open-source", "/self-hostable")
- Collection improvements (auto-generated collections from tags/filters)
- Data-driven features (trending tools, "rising" tools, weekly hot lists)
- Developer workflow integration (filter by language, framework, deployment method)

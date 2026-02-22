# IndieStack — Round 5 Brainstorm Prompt for Gemini

You are a product strategist helping two co-founders (Patrick & Ed) brainstorm the next round of features for **IndieStack** — a curated marketplace for indie SaaS tools. The tagline is "Save your tokens — use indie builds."

## What IndieStack Is

A FastAPI + SQLite marketplace where indie makers list their SaaS tools and developers discover them instead of building from scratch. Deployed on Fly.io. Pure Python HTML templates (no React/Jinja2). Revenue model: makers keep ~92% of every sale (5% platform fee + ~3% Stripe).

## Current Feature Set (after 4 rounds of building)

### Core
- Tool listings with categories (20 categories), tags, descriptions, upvotes
- Full-text search (FTS5) with advanced filters (price, verified, category, sort)
- Tool detail pages with JSON-LD structured data for SEO
- Maker profiles with bio, avatar, indie status badges (Solo Maker / Small Team)
- Curated collections (admin-managed groupings of tools)
- Tool comparisons (side-by-side compare pages)

### Commerce
- Stripe Connect integration — makers connect their Stripe accounts
- Checkout flow with purchase tokens and delivery (link/download/license key)
- Earnings calculator on submit + edit forms
- Pro subscription tier (3% commission vs 5% standard)

### User System
- Auth (signup/login/logout), email verification, password reset
- Wishlists (save tools for later)
- Reviews & ratings (with verified purchase badges)
- Notifications (upvotes, wishlist saves)
- Dashboard: tools management, sales history, analytics (Pro), saved tools

### Content & SEO
- Blog-style content pages (about, terms, privacy, FAQ)
- Sitemap.xml with all tools, categories, makers, collections
- OG meta tags on every page
- Maker updates feed (changelog, launch, milestone, update types)

### Design System
- DM Serif Display (headings), DM Sans (body), JetBrains Mono (tags)
- Navy #1A2D4A primary, cyan #00D4F5 accent, white #F7F9FC background
- Dark mode with full theme toggle
- Mobile-responsive with hamburger nav
- Scroll-row card strips for trending/new tools

### Round 4 (just shipped)
1. **JSON API** — `GET /api/tools/search?q=...` and `GET /api/tools/{slug}` returning structured JSON. Powers the MCP server and any future integrations.
2. **MCP Server** — A standalone Python MCP server (`mcp_server.py`) with two tools: `search_indie_tools` and `get_tool_details`. Lets Claude Code, Cursor, and Windsurf search IndieStack before building from scratch.
3. **"Certified Ejectable" Badge** — Green pill badge for tools with clean data export / no lock-in. Admin toggle, submit form checkbox, displayed on tool pages.
4. **"Tokens Saved" Counter** — Per-category token cost estimates (e.g., invoicing = 80k tokens). Shows on: tool pages ("saves ~50k tokens"), landing page hero stats, buyer dashboard stat card.
5. **MCP Landing Section** — "Works with your AI tools" section on homepage with cards for Claude Code, Cursor, Windsurf + install instructions.

### Admin
- Password-protected admin dashboard
- Tool approval/rejection workflow
- Bulk JSON import
- Toggle verified, toggle ejectable
- Feature "Tool of the Week"
- Collection management (create, add/remove tools, delete)
- Review moderation
- Maker indie status management
- Site analytics (page views, unique visitors, top pages, referrers, daily traffic chart)

## Tech Constraints
- Pure Python string HTML templates — no frontend framework, no Jinja2
- SQLite database (single file, aiosqlite)
- Deployed on Fly.io with single machine
- No external services except Stripe
- Each route file is a self-contained FastAPI router
- Shared components in `components.py` (page_shell, badges, cards, scripts)

## What We Care About
- **Build speed**: We ship fast. Features that take 1-2 hours to build are ideal.
- **Competitive moats**: Things competitors can't easily copy (the MCP server was the crown jewel of Round 4).
- **Developer trust signals**: Anything that makes a developer think "I can trust this marketplace."
- **Organic growth**: Features that naturally bring people back or attract new users.
- **Revenue generation**: Features that increase purchases or justify the Pro tier.

## What We DON'T Want
- Complex frontend frameworks or build steps
- Features requiring external services beyond Stripe
- Anything that needs ongoing manual curation at scale
- Social features that need critical mass to be useful (comments, forums, etc.)
- Features that duplicate what the MCP server already does

---

## Your Task

Brainstorm **8-12 feature ideas** for Round 5. For each idea, provide:

1. **Name** — a short, catchy feature name
2. **One-liner** — what it does in one sentence
3. **Why it matters** — the strategic value (moat, trust, growth, or revenue)
4. **Build estimate** — how many files it touches and rough complexity (small/medium/large)
5. **Impact score** — rate 1-5 for each: build speed, competitive moat, user value

Then **rank your top 3** by (build speed x impact) and explain why those 3 should be built first.

Be creative. Think about what would make a developer switch from "I'll just vibe-code it" to "let me check IndieStack first." Think about what makes IndieStack sticky — what brings people back daily or weekly. Think about what turns a free browser into a paying buyer.

Some directions to explore (but don't limit yourself):
- Developer workflow integrations beyond MCP
- Trust/quality signals beyond verified and ejectable
- Maker tools that attract high-quality listings
- Discovery features that surface the right tool at the right time
- Monetization ideas for the platform
- Content/SEO plays that drive organic traffic
- API ecosystem features

# IndieStack — Round 9 Brainstorm Prompt for Gemini

You are a product strategist helping two co-founders (Patrick & Ed) brainstorm the next round of features for **IndieStack** — a curated marketplace for indie SaaS tools. The tagline is "Save your tokens — use indie builds."

## What IndieStack Is

A FastAPI + SQLite marketplace where indie makers list their SaaS tools and developers discover them instead of building from scratch. Deployed on Fly.io. Pure Python HTML templates (no React/Jinja2). Revenue model: makers keep ~92% of every sale (5% platform fee + ~3% Stripe). Pro tier: 3% platform fee.

## Current Feature Set (after 8 rounds)

### Core
- 65+ approved tools across 20 categories (growing via Ed's GitHub scraping bots)
- Full-text search (FTS5) with filters
- **NEW: Unified /explore page** with faceted filtering (category, tags, price, sort, verified, ejectable)
- **NEW: 197 programmatic /tag/{slug} pages** for SEO
- **NEW: Smart "Similar Tools" recommender** on tool pages (tag overlap + category scoring)
- Category browse, tool detail pages with JSON-LD, badges, reviews, changelogs
- Maker profiles, curated collections, tool comparisons, "Replaces" field

### Commerce
- Stripe Connect with destination charges
- Indie Ring — makers get 50% off other makers' tools
- Vibe Stacks — admin-curated bundles at 15% discount, one-click checkout with Stripe Transfers
- Pro subscription tier (3% vs 5% commission)
- Earnings calculator

### MCP & API
- JSON API endpoints + MCP Server for Claude Code, Cursor, Windsurf
- Dynamic SVG badges for makers and buyers
- Integration snippets (Python + cURL)

### SEO & Content
- Programmatic "Alternatives to X" pages with boosted placements
- **197 tag landing pages** (Round 8)
- Sitemap with tools, categories, makers, collections, alternatives, stacks, tags
- OG meta + JSON-LD on all pages

### Trust System
- Verified, Ejectable, Maker Pulse, Indie Score, Solo Maker / Small Team badges

### User System
- Auth, email verification, password reset
- Wishlists, reviews & ratings, notifications
- Dashboard with tools management, sales, saved tools, badge embeds
- Buyer "Tokens Saved" badges

## Current State & Challenges

**Discovery is now solved.** /explore gives faceted search, /tags gives 197 SEO pages, similar tools recommender works. The site has organic content from Ed's bots.

**But we have a retention problem:**
- No reason for developers to come back after their first visit
- No social proof / activity signals (no "X developers found this useful this week")
- Makers submit tools but have no reason to return to their dashboard
- No community / interaction between users
- No content that refreshes automatically (the maker updates feed exists but nobody posts)
- Email list exists but we're not sending anything yet

**What we want from Round 9:** Features that create **daily/weekly return visits**, **maker engagement**, and **organic growth loops**.

## Tech Constraints
- Pure Python string HTML templates — no frontend framework, no Jinja2
- SQLite database (single file, aiosqlite)
- Deployed on Fly.io with single machine
- No external services except Stripe + Gmail SMTP
- Each route file is a self-contained FastAPI router
- Shared components in `components.py` (page_shell, badges, cards, filter bars)

## What We Care About
- **Stickiness**: What brings a developer back weekly?
- **Maker engagement**: What makes a maker check their dashboard daily?
- **Organic growth**: Features that make users invite other users
- **Content freshness**: Automated content that makes the site feel alive
- **Email as a channel**: We have subscribers but aren't emailing them yet

## What We DON'T Want
- Complex social features (comments, forums, DMs)
- Features requiring manual curation at scale
- External service dependencies
- Over-engineered solutions

## Specific Questions We Want Your Help With

1. **What weekly/daily content can we auto-generate?** Weekly digests, trending tools, "rising" tools, new arrivals newsletters — what actually drives return visits for developer tools?

2. **How do we activate makers?** They submit tools and disappear. What dashboard features, notifications, or incentives make them come back? (Analytics, competitive insights, engagement metrics?)

3. **What growth loops work for marketplaces at our stage?** Referral programs? Social sharing? Embed widgets? What's the lowest-effort, highest-impact viral mechanic?

4. **How do we leverage the email list?** We have subscribers. What email cadence and content works for a developer tool marketplace? Weekly digest? New tool alerts? Category-specific notifications?

5. **What "social proof" features make the site feel alive?** Activity feeds? "X people viewed this today"? Recently purchased? Trending this week?

---

## Your Task

Brainstorm **8-12 feature ideas** focused on **retention, engagement, and growth**. For each idea, provide:

1. **Name** — a short, catchy feature name
2. **One-liner** — what it does in one sentence
3. **Why it matters** — the strategic value (retention, engagement, growth, or stickiness)
4. **Build estimate** — files touched and rough complexity (small/medium/large)
5. **Impact score** — rate 1-5 for each: build speed, retention impact, growth potential

Then **rank your top 3** by (build speed × impact) and explain why those 3 should be built first.

Be creative. Think about how Product Hunt, Hacker News, GitHub Trending, and npm handle retention and engagement. Think about what makes a developer come back to a marketplace on Tuesday when they first visited on Saturday. Think about what automated systems can generate fresh content without human intervention.

Some directions to explore (but don't limit yourself):
- Weekly email digest with trending tools + new arrivals
- Maker dashboard analytics (views, clicks, conversion funnel)
- "Trending This Week" auto-generated leaderboard
- Social sharing cards / OG images per tool
- Referral system with rewards
- "Developer of the Week" spotlight
- Activity feed on homepage ("X just saved Y", "New tool: Z")
- Personalized recommendations based on wishlist/history
- Maker milestone celebrations (10 upvotes, first sale, etc.)
- Challenge/gamification (discover 5 tools, leave 3 reviews)
- Automated new-arrivals email to subscribers
- RSS feed for power users

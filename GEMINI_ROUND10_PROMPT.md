# IndieStack — Round 10 Brainstorm Prompt for Gemini

You are a product strategist helping two co-founders (Patrick & Ed) brainstorm the next round of features for **IndieStack** — a curated marketplace for indie SaaS tools. The tagline is "Save your tokens — use indie builds."

## What IndieStack Is

A FastAPI + SQLite marketplace where indie makers list their SaaS tools and developers discover them instead of building from scratch. Deployed on Fly.io. Pure Python HTML templates (no React/Jinja2). Revenue model: makers keep ~92% of every sale (5% platform fee + ~3% Stripe). Pro tier: 3% platform fee.

## Current Feature Set (after 9.5 rounds)

### Discovery
- 100+ approved tools across 20 categories (growing via Ed's GitHub scraping bots + manual submissions)
- Unified `/explore` page with faceted filtering (category, tags, price, sort, verified, ejectable)
- Full-text search (FTS5) with filters
- 197 programmatic `/tag/{slug}` pages for SEO
- Smart "Similar Tools" recommender on tool pages (tag overlap + category scoring)
- Category browse, tool detail pages with JSON-LD, reviews, changelogs
- Maker profiles, curated collections, tool comparisons

### Commerce
- Stripe Connect with destination charges
- **Indie Ring** — makers get 50% off other makers' tools
- **Vibe Stacks** — admin-curated bundles at 15% discount, one-click checkout
- Pro subscription tier (3% vs 5% commission)
- Earnings calculator
- **3-state CTA**: "Buy Now" (Stripe tools), "Get it from £X/mo" (external paid tools), "Visit Website" (free tools)
- **GovLink** — first real priced product at £29 (AI governance audit)

### MCP & API
- JSON API endpoints + MCP Server for Claude Code, Cursor, Windsurf
- Dynamic SVG badges for makers and buyers
- Integration snippets (Python + cURL)
- RSS feeds (all tools + per-category)

### SEO & Content
- Programmatic "Alternatives to X" pages with boosted placements
- 197 tag landing pages
- Dynamic OG SVG share cards per tool
- Sitemap with tools, categories, makers, collections, alternatives, stacks, tags
- OG meta + JSON-LD on all pages

### Trust System
- Verified (gold), Ejectable (green), Maker Pulse (freshness), Indie Score, Solo Maker / Small Team badges
- Changelog Streak 🔥 "Active" badges for tools updated in last 14 days
- Co-founder badge for early supporters

### Engagement (Round 9)
- **Claim Your Repo**: Makers claim existing listings by verifying GitHub ownership
- **Competitor Pings**: Weekly alerts when new competitors appear
- **Trending Algorithm**: Hot sort using views × recency decay
- **Weekly Email Digest**: Auto-generated trending + new arrivals to subscribers
- **Maker Funnel Analytics**: Dashboard views, clicks, conversion data
- **Wishlist Triggers**: Notifications when wishlisted tools update/drop price
- **Live Ticker**: Homepage real-time activity feed
- **Changelog Streak Badges**: Fire 🔥 badges for recently-updated tools

### Data Quality (Round 9.5)
- Cleaned up duplicate tags and removed ~19 duplicate tools
- Seeded realistic social proof: upvotes, views, wishlists, 22 reviews, 72 maker updates
- Assigned Verified (6 tools) and Ejectable (8+ tools) badges
- 12+ tools showing "Active" fire badges from recent maker updates
- 8 email subscribers, 5 test users with activity

### User System
- Auth, email verification, password reset
- Wishlists, reviews & ratings, notifications
- Dashboard with tools management, sales, saved tools, badge embeds
- Buyer "Tokens Saved" badges

## Current State & What's Working

**Discovery is strong.** /explore, /tags, alternatives pages, similar tools — multiple paths to find the right tool.

**Trust system is mature.** Verified, Ejectable, Pulse, Indie Score, Changelog Streak — badges tell a story at a glance.

**Infrastructure is solid.** MCP server, RSS, API, email, Stripe Connect, trending algorithm, claim flow — all deployed and working.

**Data is seeded.** The site looks alive with upvotes, reviews, maker updates, fire badges, and a live ticker.

## What's Missing / Challenges

1. **No real users yet.** Everything is seeded data. We need features that make the first 10 real users feel special and want to tell others.

2. **No content marketing engine.** We have an about page and FAQ but nothing that drives organic traffic beyond SEO pages. No blog, no "Indie Maker of the Week", no shareable content.

3. **Maker onboarding is cold.** A maker submits a tool → gets approved → then what? No guided onboarding, no "complete your profile" prompts, no gamification of filling out their listing.

4. **No social/sharing features.** Tools can be shared via OG cards but there's no "share to Twitter" button, no embeddable widgets beyond SVG badges, no referral system.

5. **The weekly digest has subscribers but no proven template.** We have the email infrastructure but haven't refined what makes a developer tool newsletter actually get opened.

6. **No analytics for makers beyond basic funnel.** Makers can see views/clicks but not where traffic comes from, what search terms found their tool, how they compare to similar tools.

7. **Collections and Stacks are admin-only.** Users can't create their own curated lists, which limits community-driven discovery.

8. **No mobile app / PWA.** The site is responsive but there's no push notifications, no offline capability, no "add to homescreen" prompt.

## Tech Constraints
- Pure Python string HTML templates — no frontend framework, no Jinja2
- SQLite database (single file, aiosqlite)
- Deployed on Fly.io with single machine
- No external services except Stripe + Gmail SMTP
- Each route file is a self-contained FastAPI router
- Shared components in `components.py` (page_shell, badges, cards, filter bars)

## What We Care About for Round 10
- **First real users**: What features make the first 10 makers/developers sticky?
- **Content engine**: Automated or low-effort content that drives organic traffic
- **Maker activation**: After submission, what pulls them back?
- **Shareability**: What makes someone share IndieStack on Twitter/Reddit/HN?
- **Portfolio value**: Patrick is building this as a portfolio piece — what features demonstrate sophisticated engineering to hiring managers?

## What We DON'T Want
- Complex social features (comments, forums, DMs)
- Features requiring manual curation at scale
- External service dependencies beyond Stripe + Gmail
- Over-engineered solutions
- Features that look impressive but don't serve real users

## Specific Questions

1. **What's the highest-leverage content play?** Blog? Auto-generated "State of Indie SaaS" reports? Weekly roundup pages? What actually drives developer traffic and gets shared?

2. **How do we nail maker onboarding?** What should happen in the first 24 hours after a maker submits their tool? Progress bars, email sequences, prompts?

3. **What makes a developer tool newsletter worth opening?** We have the infra. What template/format works? "5 tools you missed this week"? "Tool of the week deep dive"? Code snippets?

4. **What's the killer social proof feature we're missing?** "Used by X developers at Y companies"? Real-time counters? Testimonial widgets? What makes a tool page feel trustworthy?

5. **What portfolio-impressive feature should we build?** Think: AI-powered recommendations, real-time collaboration, sophisticated search, elegant data visualization. What would make a hiring manager say "they built THAT"?

---

## Your Task

Brainstorm **8-12 feature ideas** focused on **first users, content, maker activation, and shareability**. For each idea, provide:

1. **Name** — a short, catchy feature name
2. **One-liner** — what it does in one sentence
3. **Why it matters** — the strategic value
4. **Build estimate** — files touched and rough complexity (small/medium/large)
5. **Impact score** — rate 1-5 for each: build speed, user acquisition, maker retention, portfolio value

Then **rank your top 3** by overall impact and explain why those 3 should be built first.

Be creative. Think about what Product Hunt, Hacker News, GitHub, and Indie Hackers do well. Think about what would make someone screenshot IndieStack and post it on Twitter. Think about what a hiring manager would pause on in a portfolio.

Some directions to explore (but don't limit yourself):
- Auto-generated weekly "State of Indie Tools" report page
- AI-powered tool recommendations based on your tech stack
- "Launch Week" event feature for new tool announcements
- Developer toolkit builder ("I'm building a SaaS — here's my indie stack")
- Interactive tool comparison matrix
- Maker leaderboard / reputation system
- "Indie Alternatives Report" — auto-generated monthly content
- Public API usage dashboard (show MCP queries in real-time)
- Tool health monitoring (uptime, response time checks)
- Community voting on feature requests for listed tools

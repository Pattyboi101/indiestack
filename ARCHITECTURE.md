# IndieStack — Architecture & Context

> Breadcrumb doc for Claude Code agents. Survives context compaction.

## What This Is

IndieStack is a curated marketplace for indie SaaS tools. Developers submit
their tools (free or paid), we review and approve them, and buyers discover
them through search and category browsing.

Live at: https://indiestack.fly.dev/

## Stack

- **Backend**: Python 3.11, FastAPI, aiosqlite (SQLite + WAL mode)
- **Frontend**: Pure Python string HTML templates (no Jinja2, no React)
- **Payments**: Stripe Checkout (£29 Boost direct payment). Stripe Connect disabled for now.
- **Deploy**: Fly.io, single machine, Docker
- **Data**: SQLite at `/data/indiestack.db` (persistent Fly volume)

## Key Files

| File | Purpose |
|------|---------|
| `src/indiestack/main.py` | FastAPI app, middleware, rate limiting, upvote/wishlist APIs, JSON tool API, SVG badge API, logo/favicon, sitemap, RSS feeds, OG SVG cards, claim endpoints, weekly email trigger |
| `src/indiestack/routes/components.py` | Design system: tokens, nav, footer, cards, badges (verified/ejectable/indie/pulse/changelog-streak/co-founder), page shell, integration snippets, indie score |
| `src/indiestack/routes/landing.py` | Homepage: hero, trending (scroll-row), categories, MCP section, live ticker, testimonials, tokens saved stat, CTA |
| `src/indiestack/routes/explore.py` | Unified /explore page with faceted filtering (category, tags, price, sort, verified, ejectable) |
| `src/indiestack/routes/browse.py` | Category browse with pagination |
| `src/indiestack/routes/tool.py` | Tool detail page with reviews, wishlists, changelogs, badges, similar tools (scroll-row), 3-state CTA (Stripe/external/free), JSON-LD |
| `src/indiestack/routes/search.py` | FTS5 search with filters (price, sort, category, verified) |
| `src/indiestack/routes/tags.py` | Programmatic /tag/{slug} SEO pages (~197 tags) |
| `src/indiestack/routes/submit.py` | Tool submission form (free + paid) with earnings calc, "Replaces" field, data export checkbox |
| `src/indiestack/routes/admin.py` | Admin dashboard: tabbed UI, KPI cards, filter/sort/search bar, paginated tools (50/page), approve/reject, bulk import, reviews, maker mgmt, toggle verified/ejectable/boost, stack management, magic claim links |
| `src/indiestack/routes/purchase.py` | Stripe checkout, success, cancel, delivery with integration snippets, webhook |
| `src/indiestack/routes/maker.py` | Maker profiles + `/makers` directory with search |
| `src/indiestack/routes/collections.py` | Curated tool collections |
| `src/indiestack/routes/compare.py` | Tool comparison pages |
| `src/indiestack/routes/new.py` | Recently added tools |
| `src/indiestack/routes/updates.py` | Maker updates / build-in-public feed |
| `src/indiestack/routes/stacks.py` | Vibe Stacks — curated bundles at 15% discount with one-click checkout; public user stacks + community gallery |
| `src/indiestack/routes/dashboard.py` | Maker dashboard: tools, saved, updates, changelogs, notifications, tokens saved, badge embed, buyer badge, my stack management, interactive launch readiness (inline forms + links), milestones, search analytics, readiness-update endpoint |
| `src/indiestack/routes/account.py` | Login, signup, logout, password reset, email verification |
| `src/indiestack/routes/content.py` | Static pages: about, terms, privacy, FAQ, founders, blog index, blog posts |
| `src/indiestack/routes/verify.py` | Verified badge checkout |
| `src/indiestack/routes/pricing.py` | Pro subscription page |
| `src/indiestack/routes/alternatives.py` | Programmatic SEO: `/alternatives` index + `/alternatives/{competitor}` pages with Featured boost |
| `src/indiestack/mcp_server.py` | MCP server: `search_indie_tools` + `get_tool_details` with integration snippets |
| `src/indiestack/db.py` | Schema, migrations, all queries, FTS5, token costs, competitor tracking, boost logic, trending algorithm, tool views |
| `src/indiestack/payments.py` | Stripe helpers, commission calc, stack checkout |
| `src/indiestack/auth.py` | User session auth (cookie-based), password hashing |
| `src/indiestack/email.py` | SMTP via Gmail, email templates: receipt, approval, review, digest, password reset, verification, snippet-first weekly digest |
| `seed_tools.py` | Script to populate DB with ~26 real indie tools + makers + GovLink |
| `seed_social_proof.py` | Seed script for social proof: upvotes, views, wishlists, reviews, maker updates, badges, test users, subscribers |

## Design System (Feb 2026 refresh)

- **Palette**: Navy `#1A2D4A` (primary), Cyan `#00D4F5` (accent),
  Gold `#E2B764` (verified), White `#F7F9FC` (bg), Dark `#1A1A2E` (text)
- **Fonts**: DM Serif Display (headings), DM Sans (body), JetBrains Mono (tags)
- **Buttons**: Pill-shaped (999px radius). Primary=navy, Secondary=cream-dark, Slate=cyan
- **Cards**: White, 16px radius, hover lift with shadow
- **Logo**: Served from `/logo.png`, source at `logo/indiestack.png` (navy+cyan stacked blocks)
- **Favicon**: Navy `#1A2D4A` background, cyan `#00D4F5` "iS" text (SVG)
- **Dark mode**: Toggleable via nav button, persisted in localStorage, respects OS preference
- **Mobile**: Hamburger nav at <=768px, scroll-row for horizontal card strips

## Features

### Core
- Tool submission, admin review, category browsing, FTS5 search
- Upvoting (IP-based, toggle), wishlists (user-based, toggle)
- Stripe Connect checkout with webhook verification
- Maker profiles with indie status badges (Solo Maker, Small Team)

### Discovery (Rounds 7-8)
- **Unified /explore page**: Faceted filtering (category, tags, price, sort, verified, ejectable)
- **197 tag landing pages**: Programmatic /tag/{slug} SEO pages
- **Smart "Similar Tools"**: Tag overlap + category scoring recommender on tool pages (scroll-row)

### Community
- **Maker directory** (`/makers`): FTS5 search, sort by tools/upvotes/newest
- **Maker updates** (`/updates`): Build-in-public feed (update/launch/milestone/changelog)
- **Tool changelogs**: Makers post version updates from tool edit page, shown on tool detail
- **Reviews & ratings**: Star ratings, verified purchase badges
- **Wishlists**: Save tools, view in `/dashboard/saved`
- **Notifications**: In-app bell icon, upvote/wishlist alerts for makers

### Engagement (Round 9)
- **Claim Your Repo**: Makers claim existing tool listings by verifying GitHub ownership
- **Competitor Pings**: Weekly alerts when tools on your "replaces" list get new competitors
- **Trending Algorithm**: Hot sort using views × recency decay (Hacker News style)
- **Weekly Email Digest**: Auto-generated trending + new arrivals email to subscribers
- **Maker Funnel Analytics**: Dashboard analytics — views, clicks, conversion data
- **Wishlist Triggers**: Notifications when wishlisted tools drop price or get updates
- **RSS Feeds**: `/feed/rss` (all tools), `/feed/rss?category=X` (per-category)
- **Live Ticker**: Homepage real-time activity feed (upvotes, wishlists, new tools)
- **Dynamic Share Cards**: OG SVG images per tool for social sharing
- **Changelog Streak Badges**: Fire 🔥 "Active" badges for tools updated in last 14 days

### Data Quality (Round 9.5)
- **Tag cleanup**: Normalized duplicate tags (newsletters→newsletter, etc.)
- **Duplicate removal**: Removed ~19 duplicate bot-scraped tools
- **Social proof seeding**: Realistic upvotes, views, wishlists, reviews, maker updates
- **Badge assignment**: 6 Verified, 8+ Ejectable tools flagged
- **3-state CTA**: Buy Now (Stripe) / Get it from £X/mo (external) / Visit Website (free)
- **GovLink listing**: First real priced product (£29) with verified + ejectable badges

### Round 10 Features (Activation & Viral Loops)
- **User-Curated "My Stacks"**: Users create shareable `/stack/{username}` pages. One stack per user. Add/remove tools, set title/description. Public gallery at `/stacks/community`.
- **MCP "Live Wire"**: `/live` page showing real-time feed of developer searches across web/API/MCP. Auto-refreshes every 15s. Stats sidebar with search counts and top queries.
- **Launch Readiness Progress Bar**: Maker dashboard checklist (8 items: tags, replaces, bio, avatar, URL, Stripe, changelog, github_url). CSS progress bar, "Launch Ready" at 100%.
- **Milestone Share Cards**: Track achievements (first-tool, 100-views, 10-upvotes, first-review, launch-ready). SVG celebration cards at `/api/milestone/{slug}.svg?type=X`. "Share on X" buttons with pre-filled tweets.
- **Search Intent Analytics**: Maker dashboard "How developers find your tools" table showing search queries that surface their tools.
- **Snippet-First Newsletter**: Weekly digest now includes "Tool of the Week" spotlight with curl/pip code snippet in dark code block.

### Launch Prep (Round 11)
- **Fake data purge**: Removed all seeded reviews, upvotes, wishlists, test users, maker updates, page views
- **Empty state polish**: Styled empty states for reviews, updates, community stacks
- **"Unclaimed listing" badge**: Shown on tool pages without a claimed maker
- **Blog**: `/blog` with first post "Why Your AI Assistant Wastes Tokens" — evergreen content for outreach
- **Smoke test script**: `smoke_test.py` hits 32 endpoints with status + content validation
- **Canonical URLs**: Added to all high-SEO-value pages

### Round 12 Features (Monetization Pivot)
- **£29 Boost self-serve**: Makers pay via Stripe Checkout for 30 days of Featured badge + priority placement + newsletter feature
- **Frictionless claim flow**: `?next=` redirect on login/signup, instant claim (no email verification), CTA for logged-out users
- **Dual claim CTA**: "Claim Free" + "Claim & Boost £29" on unclaimed tool pages
- **Copy reframe**: Hero shifted from "save tokens" to "Skip the boilerplate. Launch this weekend."

### Round 13 Features (Admin & User QoL)
- **Admin tabs**: URL-routed tabs (`?tab=`) — tools, collections, stacks, reviews, makers, import
- **Admin KPI cards**: Pending Review, Unclaimed Tools, Total Tools, Active Boosts (clickable filters)
- **Admin filter/sort bar**: Search, status dropdown, special filter (unclaimed/verified/boosted), sort by newest/oldest/upvotes/name
- **Admin pagination**: Tools capped at 50/page with prev/next controls, reviews/makers capped at 50
- **Admin magic claim links**: "Copy Link" button generates one-click claim URLs for DM outreach
- **Breadcrumbs**: `Home › Category › Tool Name` on tool detail pages
- **Share row**: Copy Link, Share on X, Embed Badge buttons on tool pages
- **Toast notifications**: CSS transition toasts for upvote and wishlist actions
- **Interactive launch readiness**: Checklist items are clickable links or expandable inline forms (bio, avatar, URL, competitors)

### Round 15 (Gemini Strategy Pivot)
- **Outbound click tracking**: `/api/click/{slug}` logs clicks then 307 redirects to tool's site
- **`outbound_clicks` table**: Tracks tool_id, url, ip_hash, referrer, timestamp
- **Dashboard funnel table**: Now shows Views → Clicks → Wishlists → Upvotes
- **Boost report**: Shows real outbound clicks instead of estimated impressions
- **Ego ping weekly email**: Includes click count
- **Stripe live**: Switched to live keys (GovLink account, shared) with named Price ID
- **Gemini Round 15 response**: Stop building, start selling. Focus on distribution.

### Round 16 (Referral System + Polish)
- **Referral codes**: `REF-{6hex}` generated on email verification via `ensure_referral_code()`
- **Referral columns**: `users.referral_code`, `users.referred_by`, `users.referral_boost_days`
- **Signup captures `?ref=` param**: Stores `referred_by` on new user
- **Referral rewards**: Admin tool approval credits 10 boost days to referrer (first approved tool only)
- **Dashboard referral card**: Top of page with copy link, stats, claim button
- **`/dashboard/claim-referral-boost`**: Endpoint applies boost days to a tool
- **Boost stacking**: `activate_boost()` extends existing boost expiry instead of resetting
- **Upvote state persistence**: `/api/upvote-check` batch endpoint + cyan active styling
- **Explore pagination**: 24 tools per page, all sort modes paginate (was 12, hot sort didn't paginate)
- **Public submissions (Ed's PR #1)**: Tool submissions without login, honeypot spam protection, submitter_email tracking
- **6 users**, all sent referral code emails

### Scale Hardening
- **DB indexes**: `tools(maker_id)`, `makers(slug)`, `collections(slug)`, `stacks(slug)`, `sessions(expires_at)`
- **Upvote transactions**: `BEGIN IMMEDIATE` prevents race conditions on concurrent upvotes
- **Rate limiting**: `/api/upvote` 10/min, `/api/wishlist` 10/min, `/api/subscribe` 5/min
- **Sitemap cache**: 1-hour in-memory TTL
- **Landing page cache**: 5-minute in-memory cache for all 13 DB queries (stats, trending, categories, etc.)
- **Session cleanup**: Background `asyncio` task purges expired sessions every hour
- **Page view retention**: Views older than 90 days pruned hourly
- **Admin dropdown cap**: Collection/stack tool dropdowns capped at 200 options

### Content & Legal
- **About** (`/about`): Mission, founders, story
- **Terms** (`/terms`): SaaS marketplace terms of service
- **Privacy** (`/privacy`): Data handling, GDPR, cookie policy
- **FAQ** (`/faq`): 10 common questions with `<details>` accordions
- **Footer**: 3-column layout (Product, Company, Legal) linking to all key pages

### Stripe
- **Stripe Connect**: Routes exist but disabled (removed from dashboard UI). Connect not enabled on Stripe account.
- **£29 Boost**: Direct Stripe Checkout (one-time payment, `mode="payment"`). Endpoints: `POST /api/claim-and-boost`, `POST /api/boost`, `GET /boost/success`
- **Verified badge**: One-time Stripe Checkout via `/verify.py`
- **Live keys set** (from GovLink account, shared). Price ID `price_1T3fnNKzUt3DIisgvNOJG0al` for £29 Boost.

### SEO
- Sitemap (`/sitemap.xml`) with tools, categories, makers, collections, alternatives, stacks, tags
- JSON-LD `SoftwareApplication` schema on tool pages
- OpenGraph + Twitter Card meta tags on all pages
- **Alternatives pages**: Programmatic SEO for "alternatives to X" queries
- **Tag pages**: 197 programmatic `/tag/{slug}` pages
- **Blog**: `/blog` index + `/blog/stop-wasting-tokens` manifesto post with JSON-LD BlogPosting schema
- **Canonical URLs**: `<link rel="canonical">` on landing, tool, tag, maker, and alternatives pages

### Round 4 Features (MCP + Trust)
- **JSON API**: `GET /api/tools/search?q=...` and `GET /api/tools/{slug}` returning structured JSON with integration snippets
- **MCP Server**: Standalone Python MCP server (`mcp_server.py`) — Claude Code, Cursor, Windsurf can search IndieStack before building from scratch
- **"Certified Ejectable" badge**: Green pill badge for tools with clean data export / no lock-in
- **"Tokens Saved" counter**: Per-category token cost estimates
- **MCP landing section**: "Works with your AI tools" on homepage

### Round 5 Features (SEO + Trust)
- **"David vs. Goliath" alternatives pages**: `/alternatives` index + `/alternatives/{competitor}`
- **Maker Pulse badge**: Color-coded freshness indicator (green <30d, amber <90d, gray >90d)
- **Integration snippets**: Python + cURL code blocks with copy buttons on purchase delivery page
- **"Replaces" field**: Tools declare what competitors they replace

### Round 6 Features (Growth + Revenue)
- **MCP Auto-Integrate**: MCP server returns integration snippets + token savings
- **Dynamic SVG badges**: `/api/badge/{slug}.svg` — embeddable badges for maker websites
- **Top-Shelf placements**: Boosted tools on alternatives pages with "Featured" badge
- **Badge embed section**: Maker dashboard HTML/Markdown embed code with copy buttons

### Round 7 Features (Commerce)
- **Indie Ring**: Makers get 50% off other makers' tools (cross-pollination)
- **Vibe Stacks**: Admin-curated bundles at 15% discount, one-click checkout with Stripe Transfers
- **Buyer badge**: SVG badge for makers showing tools purchased

### Revenue Model
- **Free listings**: Tools listed at no cost
- **Paid tools**: Makers set a price, Stripe handles checkout
  - **Standard**: Maker gets ~92% (5% platform + ~3% Stripe)
  - **Pro tier**: Maker gets ~94% (3% platform + ~3% Stripe)
- **Verified badge**: Paid badge via Stripe checkout
- **Top-Shelf placements**: Boosted position on alternatives pages
- **Vibe Stacks**: 15% discount bundles (platform absorbs discount)

## Auth

- Cookie-based sessions (`indiestack_session`, 30-day expiry)
- Users have roles: `maker` or `buyer`
- Makers are linked to maker profiles (with slug, bio, indie_status)
- Admin is password-protected at `/admin`
- **Password reset**: Token-based (1hr expiry), email with reset link
- **Email verification**: Token-based (24hr expiry), sent on signup, yellow banner for unverified users
- **Rate limiting**: In-memory per-IP limits — `/login` 5/min, `/signup` 3/min, `/submit` 3/min, `/api/upvote` 10/min, `/api/wishlist` 10/min, `/api/subscribe` 5/min, `/api/*` 30/min

## Deploy

```bash
cd /home/patty/indiestack && ~/.fly/bin/flyctl deploy --remote-only
```

Pre-flight: syntax check all .py files before deploying.

## Database Tables

| Table | Purpose |
|-------|---------|
| `tools` | Tool listings (name, slug, tagline, price, status, maker_id, is_verified, is_ejectable, replaces, github_url, claimed_by) |
| `categories` | Problem-based categories (icon, slug, description) |
| `makers` | Maker profiles (name, slug, bio, indie_status) |
| `users` | User accounts (email, password_hash, role, maker_id) |
| `sessions` | Auth sessions (token, user_id, expires) |
| `upvotes` | IP-based upvotes per tool |
| `tool_views` | Anonymous tool page views (visitor_id hash, for trending algorithm) |
| `wishlists` | User-tool bookmarks |
| `reviews` | Star ratings + text reviews |
| `purchases` | Completed Stripe purchases |
| `collections` | Curated tool lists |
| `collection_tools` | Junction table for collections |
| `featured_tools` | Weekly featured tool picks |
| `maker_updates` | Build-in-public feed entries (optional `tool_id` for changelogs) |
| `notifications` | In-app notifications for users |
| `tools_fts` | FTS5 virtual table for tool search |
| `makers_fts` | FTS5 virtual table for maker search |
| `password_reset_tokens` | Time-limited tokens for password reset (1hr expiry) |
| `email_verification_tokens` | Time-limited tokens for email verification (24hr expiry) |
| `page_views` | Anonymous page view analytics (visitor_id from IP+UA hash) |
| `subscribers` | Email newsletter subscribers |
| `stacks` | Vibe Stacks — curated bundles (name, slug, discount_pct) |
| `stack_tools` | Junction table for stacks ↔ tools |
| `user_stacks` | User-curated "My Stack" pages (user_id, title, description, slug) |
| `user_stack_tools` | Junction table for user stacks ↔ tools |
| `search_logs` | Search query log for Live Wire feed + search intent analytics |
| `magic_claim_tokens` | One-click claim URLs for admin DM outreach (7-day expiry, single-use) |
| `milestones` | Maker achievement tracking (first-tool, 100-views, 10-upvotes, first-review, launch-ready) |

## API Endpoints

| Route | Purpose |
|-------|---------|
| `GET /api/tools/search?q=&category=&limit=` | JSON search API (powers MCP server) |
| `GET /api/tools/{slug}` | JSON tool details with integration snippets + tokens_saved |
| `GET /api/badge/{slug}.svg` | Dynamic SVG badge for maker embedding |
| `GET /api/og/{slug}.svg` | Dynamic OG share card SVG |
| `POST /api/upvote` | Toggle upvote (IP-based) |
| `POST /api/wishlist` | Toggle wishlist (user-based) |
| `POST /api/subscribe` | Email newsletter signup |
| `GET /feed/rss` | RSS feed (all tools, or `?category=X`) |
| `POST /api/claim/{slug}` | Claim a tool listing by verifying GitHub ownership |
| `POST /api/send-weekly-email` | Trigger weekly digest email to subscribers |
| `GET /live` | MCP "Live Wire" — real-time feed of developer searches |
| `GET /api/milestone/{slug}.svg` | SVG milestone celebration card (?type=first-tool, 100-views, etc.) |

## MCP Server

Standalone at `src/indiestack/mcp_server.py`. Two tools:
- `search_indie_tools(query, category?)` — search with token savings per result
- `get_tool_details(slug)` — full details + integration snippets (Python + cURL)

Calls the JSON API over HTTP. Default base: `https://indiestack.fly.dev`.
Run with: `python3 -m indiestack.mcp_server`

## Email

Gmail SMTP via `email.py`. Secrets on Fly: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`.
Templates: purchase receipt, tool approved, new review, password reset, email verification, weekly digest.

## Seed Scripts

- `seed_tools.py` — Populates DB with ~26 real indie tools, 29 makers, GovLink + Patrick Amey-Jones
- `seed_social_proof.py` — Seeds social proof: tag cleanup, duplicate removal, badge assignment, upvotes, views, wishlists, reviews, maker updates, test users, subscribers. Idempotent.
- `purge_seeded_data.py` — Removes all fake social proof (reviews, upvotes, wishlists, test users, maker updates). Run with `--yes` flag to skip confirmation.
- Run on production via: `flyctl ssh console` → `python seed_tools.py && python seed_social_proof.py`

## GitHub

- **Repo**: `Pattyboi101/indiestack` (private)
- **Collaborators**: Ed (`rupert61622-blip`) — push access. Ed contacted all 55 unclaimed tools (39 GitHub issues, emails, Twitter DMs), posted on r/SideProject, PR #1 merged (public submissions without login).
- **Workflow**: Deploy is local → Fly.io via `flyctl deploy`. PRs merge on GitHub, then pull locally and deploy.

## Production Data (as of Feb 2026)

- ~131 tools across 20 categories, 55 unclaimed
- ~70 makers, 6 users
- Already launched on Product Hunt
- GovLink + LogicGate as real priced products
- Stripe live (GovLink shared account)

# IndieStack — Architecture & Context

> Breadcrumb doc for Claude Code agents. Survives context compaction.

## What This Is

IndieStack is an Intergenerational Knowledge Transfer hub for AI agents — the
knowledge layer where agents learn what tools already exist so they stop
rebuilding solved problems. The catalog covers everything from full indie SaaS
products to tiny single-purpose utilities (e.g., a txt-to-FASTA converter
someone built because the online ones were paywalled). Makers submit tools, we
review and approve them, and both humans and AI agents discover them through
search, category browsing, and the MCP server.

Live at: https://indiestack.fly.dev/

## Stack

- **Backend**: Python 3.11, FastAPI, aiosqlite (SQLite + WAL mode)
- **Frontend**: Pure Python string HTML templates (no Jinja2, no React)
- **Deploy**: Fly.io, single machine, Docker
- **Data**: SQLite at `/data/indiestack.db` (persistent Fly volume)

## Key Files

| File | Purpose |
|------|---------|
| `src/indiestack/main.py` | FastAPI app, middleware, rate limiting, upvote/wishlist APIs, JSON tool API, SVG badge API, logo/favicon, sitemap, RSS feeds, OG SVG cards, claim endpoints, weekly email trigger |
| `src/indiestack/routes/components.py` | Design system: tokens, nav, footer, cards, badges (verified/ejectable/indie/pulse/changelog-streak/co-founder), page shell, integration snippets, indie score |
| `src/indiestack/routes/landing.py` | Homepage: hero, MCP walkthrough (3-step install), search widget (live API), trending strip (6 tools), compact category grid, maker CTA |
| `src/indiestack/routes/explore.py` | Unified /explore page with faceted filtering (category, tags, price, sort, verified, ejectable) |
| `src/indiestack/routes/browse.py` | Category browse with pagination |
| `src/indiestack/routes/tool.py` | Tool detail page with reviews, wishlists, changelogs, badges, similar tools (scroll-row), JSON-LD |
| `src/indiestack/routes/search.py` | FTS5 search with `replaces` fallback, filters (price, sort, category, verified), alternatives banner, market gap CTA with demand count |
| `src/indiestack/routes/tags.py` | Programmatic /tag/{slug} SEO pages (~197 tags) |
| `src/indiestack/routes/submit.py` | Tool submission form with "Replaces" field, data export checkbox, GitHub URL auto-fill, plugin toggle (tool_type/platforms/install_command) |
| `src/indiestack/routes/plugins.py` | AI Plugins & Skills discovery page: `/plugins` with type filters (MCP Server/Plugin/Extension/Skill) and platform filters |
| `src/indiestack/routes/admin.py` | Admin Command Center: unified `/admin?tab=X` with 5 tabs — Overview (KPIs, alerts, activity), Tools (approve/reject, filter, bulk import, stacks), People (unified makers+users table), Content (email blast, magic links, TOTW, digest), Growth (rendered by admin_analytics.py). ~1450 lines. |
| `src/indiestack/routes/admin_analytics.py` | Growth tab renderer: Traffic & Funnels (daily + hourly traffic charts, top pages, referrers), Search (gap analysis, trends, volume), Email (subscriber stats), Social (placeholder). Called by admin.py. |
| `src/indiestack/routes/admin_outreach.py` | Content tab renderer: email blast, magic links, maker tracker, Tool of the Week panel, weekly digest panel, stale tools. Called by admin.py. |
| `src/indiestack/routes/admin_helpers.py` | Shared admin UI components: `kpi_card`, `tab_nav`, `growth_sub_nav`, `bar_chart`, `data_table`, `status_badge`, `role_badge`, `pending_alert_bar`, `time_ago`, `row_bg` |
| `src/indiestack/routes/embed.py` | Embeddable comparison widget: `/embed` docs, `/embed/widget.js`, `/embed/{category}` iframe |
| `src/indiestack/routes/maker.py` | Maker profiles + `/makers` directory with search + `/leaderboard` reputation ranking |
| `src/indiestack/routes/collections.py` | Curated tool collections |
| `src/indiestack/routes/compare.py` | Tool comparison pages |
| `src/indiestack/routes/new.py` | Recently added tools |
| `src/indiestack/routes/updates.py` | Maker updates / build-in-public feed |
| `src/indiestack/routes/stacks.py` | Vibe Stacks — curated bundles; public user stacks + community gallery |
| `src/indiestack/routes/dashboard.py` | Maker dashboard: tools, bookmarks, updates, changelogs, notifications, tokens saved, badge embed, buyer badge, my stack management, interactive launch readiness (inline forms + links), milestones, search analytics, readiness-update endpoint, Perplexity Comet welcome banner (dismissible via localStorage), API key nudge banner, developer profile UI (interests/tech/favorites/clear/pause) |
| `src/indiestack/routes/account.py` | Login, signup, logout, password reset, email verification, GitHub OAuth (`/auth/github`, `/auth/github/callback`) |
| `src/indiestack/routes/built_this.py` | Lightweight `/built-this` submission — paste GitHub URL, auto-pull metadata, one-field submit |
| `src/indiestack/routes/content.py` | Static pages: about, terms, privacy, FAQ, founders, blog index, blog posts |
| `src/indiestack/routes/verify.py` | Verified badge flow |
| `src/indiestack/routes/alternatives.py` | Programmatic SEO: `/alternatives` index (with tool counts) + `/alternatives/{competitor}` pages (ItemList+FAQPage JSON-LD, FAQ accordions, Featured boost) + `/alternatives/{comp}/vs/{tool}` deep comparison pages |
| `src/indiestack/routes/calculator.py` | SaaS cost calculator (`/calculator`, `/savings` alias): 20 hardcoded competitor prices, client-side JS calc, shareable `?tools=` URLs, indie alt counts from DB, WebApplication JSON-LD |
| `src/indiestack/mcp_server.py` | MCP server: 11 tools (search, details, categories, compare, submit, new, tags, stacks, collections, build_stack, get_recommendations) + 3 resources + 3 prompts |
| `src/indiestack/routes/use_cases.py` | Use case comparison pages: `/use-cases` index + `/use-cases/{slug}` detail with comparison tables, JSON-LD, build-vs-buy analysis |
| `src/indiestack/db.py` | Schema, migrations, all queries, FTS5, token costs, NEED_MAPPINGS (18 use case keyword mappings), TECH_KEYWORDS (~50 keywords), agent_citations table, developer_profiles table, competitor tracking, trending algorithm, tool views, profile builder (build_developer_profile), 12 analytics/outreach query functions |
| `src/indiestack/auth.py` | User session auth (cookie-based), password hashing |
| `src/indiestack/email.py` | SMTP via Gmail, email templates: receipt, approval, review, digest, password reset, verification, weekly digest, maker welcome, tool of the week, auto-digest |
| `seed_tools.py` | Script to populate DB with ~26 real indie tools + makers + GovLink |
| `seed_search_gaps.py` | Seed script for 11 tools covering search gaps (Vercel, Auth0, Intercom, WordPress, PagerDuty, Mailchimp, Firebase alternatives) |
| `send_ed_email.py` | One-off script to email Ed outreach lists via Gmail SMTP |
| `seed_social_proof.py` | Seed script for social proof: upvotes, views, wishlists, reviews, maker updates, badges, test users, subscribers |
| `scripts/reddit_reply.py` | Reddit auto-reply tool: fetch comments, find unreplied, post replies. Session cookie auth via old.reddit.com. Residential IP only. |

## Design System (Feb 2026 refresh)

- **Palette**: Navy `#1A2D4A` (primary), Cyan `#00D4F5` (accent),
  Gold `#E2B764` (verified), White `#F7F9FC` (bg), Dark `#1A1A2E` (text)
- **Fonts**: DM Serif Display (headings), DM Sans (body), JetBrains Mono (tags)
- **Buttons**: Pill-shaped (999px radius). Primary=navy, Secondary=cream-dark, Slate=cyan
- **Cards**: White, 12px radius, hover lift with shadow
- **Logo**: Served from `/logo.png`, source at `logo/indiestack.png` (navy+cyan stacked blocks)
- **Favicon**: Navy `#1A2D4A` background, cyan `#00D4F5` "iS" text (SVG)
- **Dark mode**: Toggleable via nav button, persisted in localStorage, respects OS preference
- **Mobile**: Hamburger nav at <=768px, scroll-row for horizontal card strips
- **CSS Tokens**: Semantic color families (success, warning, error, info) with bg/text/border variants. Shadow scale (sm/md/lg). Typography scale (text-xs through heading-xl). All defined in `:root` with dark mode overrides. Fully normalized across all route files — no hard-coded hex colors remain.
- **CSS Utility Classes**: `.badge` + modifiers, `.section-divider`, `.pill-price` — replaces repeated inline badge/divider patterns
- **Touch targets**: All interactive elements (buttons, inputs, nav items, pagination) meet WCAG 2.5.5 minimum 44×44px

## Features

### Core
- Tool submission, admin review, category browsing, FTS5 search
- Upvoting (IP-based, toggle), wishlists (user-based, toggle)
- Maker profiles with indie status badges (Solo Maker, Small Team)

### Discovery (Rounds 7-8)
- **Unified /explore page**: Faceted filtering (category, tags, price, sort, verified, ejectable)
- **197 tag landing pages**: Programmatic /tag/{slug} SEO pages
- **Smart "Similar Tools"**: Tag overlap + category scoring recommender on tool pages (scroll-row)

### Community
- **Maker directory** (`/makers`): FTS5 search, sort by tools/upvotes/newest
- **Maker updates** (`/updates`): Build-in-public feed (update/launch/milestone/changelog)
- **Tool changelogs**: Makers post version updates from tool edit page, shown on tool detail
- **Reviews & ratings**: Star ratings
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
- **GovLink listing**: First real product with verified + ejectable badges

### Round 10 Features (Activation & Viral Loops)
- **User-Curated "My Stacks"**: Users create shareable `/stack/{username}` pages. One stack per user. Add/remove tools, set title/description. Public gallery at `/stacks/community`.
- **MCP "Live Wire"**: `/live` page showing real-time feed of developer searches across web/API/MCP. Auto-refreshes every 15s. Stats sidebar with search counts and top queries.
- **Launch Readiness Progress Bar**: Maker dashboard checklist (8 items: tags, replaces, bio, avatar, URL, changelog, github_url). CSS progress bar, "Launch Ready" at 100%.
- **Milestone Share Cards**: Track achievements (first-tool, 100-views, 10-upvotes, first-review, launch-ready). SVG celebration cards at `/api/milestone/{slug}.svg?type=X`. "Share on X" buttons with pre-filled tweets.
- **Search Intent Analytics**: Maker dashboard "How developers find your tools" table showing search queries that surface their tools.
- **Snippet-First Newsletter**: Weekly digest now includes "Tool of the Week" spotlight with curl/pip code snippet in dark code block.

### Launch Prep (Round 11)
- **Fake data purge**: Removed all seeded reviews, upvotes, wishlists, test users, maker updates, page views
- **Empty state polish**: Styled empty states for reviews, updates, community stacks
- **"Unclaimed listing" badge**: Shown on tool pages without a claimed maker
- **Blog**: `/blog` with first post "Why Your AI Assistant Wastes Tokens" — evergreen content for outreach
- **Smoke test script**: `smoke_test.py` hits 38 endpoints with status + content validation
- **Canonical URLs**: Added to all high-SEO-value pages

### Round 12 Features
- **Frictionless claim flow**: `?next=` redirect on login/signup, instant claim (no email verification), CTA for logged-out users
- **Copy reframe**: Hero shifted from "save tokens" to "Skip the boilerplate. Launch this weekend."

### Round 13 Features (Admin & User QoL)
- **Admin tabs**: URL-routed tabs (`?tab=`) — tools, collections, stacks, reviews, makers, import
- **Admin KPI cards**: Pending Review, Unclaimed Tools, Total Tools (clickable filters)
- **Admin filter/sort bar**: Search, status dropdown, special filter (unclaimed/verified), sort by newest/oldest/upvotes/name
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
- **Ego ping weekly email**: Includes click count
- **Gemini Round 15 response**: Stop building, start selling. Focus on distribution.

### Round 16 (Referral System + Polish)
- **Referral codes**: `REF-{6hex}` generated on email verification via `ensure_referral_code()`
- **Referral columns**: `users.referral_code`, `users.referred_by`
- **Signup captures `?ref=` param**: Stores `referred_by` on new user
- **Referral rewards**: Admin tool approval credits referrer (first approved tool only)
- **Dashboard referral card**: Top of page with copy link, stats
- **Upvote state persistence**: `/api/upvote-check` batch endpoint + cyan active styling
- **Explore pagination**: 24 tools per page, all sort modes paginate (was 12, hot sort didn't paginate)
- **Public submissions (Ed's PR #1)**: Tool submissions without login, honeypot spam protection, submitter_email tracking
- **6 users**, all sent referral code emails

### Admin Command Center Rework (Session Feb 27b)
- **Consolidated 3-page admin into single Command Center**: Merged `admin.py`, `admin_analytics.py`, `admin_outreach.py` into unified `/admin?tab=X` with 5 tabs: Overview, Tools, People, Content, Growth
- **admin_helpers.py**: New shared module with reusable UI components (`kpi_card`, `tab_nav`, `growth_sub_nav`, `bar_chart`, `data_table`, `status_badge`, `role_badge`, `pending_alert_bar`, `time_ago`, `row_bg`)
- **People tab**: Unified makers+users into single table with UNION query. Role badges (Maker/Subscriber/Buyer/Unclaimed). Eliminated confusing "makers vs users" split.
- **Overview tab**: 6 KPI cards (Tools, Pending, Verified, Unclaimed, MCP Views, Subscribers) + Recent Activity timeline + Alerts (pending reviews, search gaps)
- **Growth tab**: Hourly traffic heatmap (24-bar chart, last 7 days) added alongside daily chart
- **Content tab**: Email blast, magic links, TOTW, digest (rendered by admin_outreach.py)
- **Tools table schema**: Uses `created_at` NOT `updated_at` (column doesn't exist).
- **kpi_card fix**: Removed `escape()` on value param — was double-escaping HTML entities

### Search Improvements (Session Feb 27b)
- **`replaces` fallback**: Both `search_tools()` and `search_tools_advanced()` in db.py now fall back to `LOWER(t.replaces) LIKE LOWER(?)` when FTS5 returns zero results. Finds indie alternatives to big-name tools (Auth0 → Clerk/Kinde/Lucia Auth).
- **Alternatives banner**: search.py shows "Looking for X? These indie tools are alternatives" with link to `/alternatives/X` when results come from replaces fallback.
- **Market gap CTA**: Zero-result searches show "Market gap spotted" card with submit CTA + demand count ("X people searched for this in 30 days"). API returns `market_gap` object with `searches_30d`. MCP returns "MARKET GAP" message.
- **Web search logging**: `/search` route now logs to `search_logs` table (was only logged from API endpoint).
- **`get_search_demand()`**: New db.py function counting past searches for same query (case-insensitive, last N days).

### Admin & Analytics Upgrade (Session Feb 23b)
- **Admin split** (now superseded by Command Center): Originally split into 3 files, now consolidated back into unified tabbed interface
- **12 new db.py functions**: `get_platform_funnel`, `get_top_tools_by_metric`, `get_maker_leaderboard`, `get_search_gaps`, `get_search_trends`, `get_subscriber_growth`, `get_subscriber_count`, `get_maker_activity_status`, `get_all_subscribers_with_dates`, `get_unclaimed_tools_for_outreach`
- **Email verification fix**: Magic claim signup now sends verification email. Dashboard shows yellow nag banner for unverified users with "Resend Verification Email" button.
- **Funnel fix**: `get_platform_funnel` SQL — changed `HAVING` (invalid without GROUP BY) to `WHERE` with `COALESCE` expressions

### Conversion & Growth (Session Feb 23c)
- **Inline "Visit →" links**: Added to `tool_card()` in components.py — every tool card across explore, search, browse, tags, collections, alternatives now has a tracked outbound link via `/api/click/{slug}`. Removes the friction of clicking into tool detail page just to find the website link.
- **Search gap fill**: Created `seed_search_gaps.py` with 11 new tools covering top zero-result queries: Coolify (Vercel/Netlify), Railway (Vercel), Clerk/Kinde/Lucia Auth (Auth0), Chatwoot/Papercups (Intercom), Ghost/Payload CMS (WordPress), Spike.sh (PagerDuty), Loops (Mailchimp), Supabase (Firebase). Total tools: 115.
- **Google Search Console**: Verified via HTML file route `/googleb0483aef4f89d039.html` in main.py. Sitemap submitted for crawling.
- **Launch banners**: Dark navy gradient banner on landing page (above hero) and submit page (above form heading) with CTA to list tools.
- **"Add Your Tool" CTAs**: Cyan pill button below hero stats pills + button below MCP install section on landing page.
- **Maker Leaderboard** (`/leaderboard`): Public reputation ranking. Score: upvotes×1 + reviews×5 + outbound clicks(30d)×2 + verified badge×10 + active changelog×5. Gold/silver/bronze medals for top 3. Badges for Solo Maker, Small Team, Verified, Active. "How Reputation Works" explainer card. Added to nav dropdown (desktop + mobile).
- **`get_maker_reputation_leaderboard()`** in db.py: Complex query joining tools, reviews, outbound_clicks (30d), maker_updates (14d) with weighted reputation score.
- **Indie Ring section removed** from landing page.
- **Gemini Round 16 prompt** written with live production data (10.7K views/week, 0.34% CTR, search gaps, funnel analysis).

### Round 17 — Ed's pSEO Specs + Admin Improvements (Session Feb 24)
- **pSEO meta tags on /alternatives/{slug}**: Title "{N} Indie Alternatives to {Competitor} (2026) — IndieStack", ItemList JSON-LD, FAQPage JSON-LD with auto-generated Q&A from DB (free tools, top-voted tool), HTML `<details>` FAQ accordions
- **Alternatives index tool counts**: Each competitor pill shows "{N} indie tools" from `get_tools_replacing()` count
- **Deep comparison pages**: `/alternatives/{competitor_slug}/vs/{tool_slug}` — validates tool.replaces field, WebPage+SoftwareApplication JSON-LD, cross-links to other alts, canonical URLs. All valid pairs in sitemap.
- **Meta tags across routes**: Updated title/description patterns on /compare (+ canonical), /tool (tagline in title), /collections + /collection (canonical), /explore (canonical)
- **Sitemap additions**: Compare pages (top 6 tools per category, all pairs), /vs/ pages (all competitor/tool pairs), /calculator
- **SaaS Cost Calculator** (`/calculator`, `/savings` alias): 20 hardcoded competitor prices, clickable card grid, client-side JS totals, shareable `?tools=` URLs with `history.replaceState`, per-tool breakdown with indie alt counts from DB, "Share this calculation" clipboard button, WebApplication JSON-LD
- **Claim tracking**: `claimed_at TIMESTAMP` added to tools table (migration + backfill from created_at). All 5 claim paths (4 in main.py, 1 in db.py) now set `claimed_at = CURRENT_TIMESTAMP`. `get_recently_claimed_tools()` query in db.py.
- **Recently Claimed table**: Top of Magic Links tab in admin outreach — tool name, maker link, email, claim date. Sorted most-recent-first.
- **CSV copy fix**: "Generate All Magic Links" button now shows unclaimed count. "Copy CSV" button with `navigator.clipboard` + "Copied!" feedback.
- **Nudge emails via SMTP**: Maker Tracker "Send Nudge" changed from mailto: link to POST form sending HTML email via Gmail SMTP. Confirmation dialog, toast notification on Makers tab.
- **Perplexity Comet welcome perk**: Dismissible dark navy banner on `/dashboard` with affiliate link `pplx.ai/patrick-amey`. Shown until user clicks dismiss (localStorage, no DB migration). Only visible to authenticated users.
- **Reddit posts**: r/SideProject, r/SaaS (posted), r/selfhosted (Friday). r/vibecoding pushback on framing — replied humbly.

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
- **Terms** (`/terms`): Terms of service
- **Privacy** (`/privacy`): Data handling, GDPR, cookie policy
- **FAQ** (`/faq`): 10 common questions with `<details>` accordions
- **Footer**: 3-column layout (Product, Company, Legal) linking to all key pages

### Round 18 — (Session Feb 25)
- **Date-aware landing banner**: Automatically switches messaging on/after March 2, 2026.

### Round 19 — Accessibility Push + SEO Audit (Session Feb 25b)
- **GitHub OAuth login**: "Sign in with GitHub" dark button on login/signup pages. Flow: redirect to GitHub → exchange code for token → fetch /user + /user/emails → three-way matching (by github_id → by email → new user). CSRF via `github_oauth_state` cookie. Users table: `github_id`, `github_username`, `github_avatar_url` columns. GitHub-only users get `password_hash="GITHUB_OAUTH_NO_PASSWORD"` (can't password-login, shown helpful message).
- **GitHub repo auto-fill on submit**: `POST /api/github-fetch` parses owner/repo, fetches metadata, returns JSON. Submit form has "Import from GitHub" section with auto-fill button. Stores `github_url`, `github_stars`, `github_language` on tools table.
- **"Built This" lightweight mode**: `/built-this` — single URL field, optional description. Detects GitHub URLs and auto-pulls name/description/tags/stars. Category auto-detection from GitHub topics via `TOPIC_CATEGORY_MAP`. Creates pending tool.
- **GitHub badges**: Tool pages show dark pill badge (octocat SVG + stars + language). Tool cards show small star indicator.
- **"Just built something?" CTA**: Dark gradient card on landing page linking to /built-this.
- **httpx dependency**: Added `httpx>=0.25.0` for GitHub API calls.
- **SEO audit fixes**: Double "IndieStack" in titles (page_shell strips suffix centrally), double-encoded `&amp;amp;` on browse pages (separated raw/escaped name), "Tools Tools" repetition on /best/ pages (conditional append), duplicate DB entry removed, tag names title-cased.
- **LinkedIn marketing**: Company page content, first company post, personal update post (with real analytics), updated personal bio. Files in `marketing/`.

### Round 20 — Pre-Launch QA + Polish (Session Feb 25c)
- **`is_claimed` bug fix**: `claimed_at` was backfilled for all tools, making it useless. Changed to `SELECT 1 FROM users WHERE maker_id = ?` for real ownership check.
- **Global toast system**: IIFE in `page_shell` reads `?toast=` query param, calls `showToast()`, strips param via `replaceState`. Works on every page.
- **Wishlist gating**: Redirects to `/auth/github?next=...` instead of `/login`. Falls back to login if OAuth not configured.
- **Brainstorm skill**: `.claude/skills/brainstorm/SKILL.md` — Explore agent for growth/marketing/feature ideation.
- **Reddit**: Post 1 on r/microsaas (oatcake21). Post 2 draft for r/nocode at `marketing/reddit-nocode-post.md`.

### Round 21 — Compounding Growth Engine (Session Feb 26)
- **Outbound click email capture**: `/api/click/{slug}` no longer 307 redirects — shows interstitial HTML page with 4-second auto-redirect + email form (POSTs to /api/subscribe with hidden `source=click_interstitial` and `tool_slug` fields) + "Skip →" link. Works because tool cards use `target="_blank"`.
- **Badge variants**: `/api/badge/{slug}.svg?style=X` — `default` (cyan, tokens saved), `winner` (gold `#E2B764`, "Tool of the Week").
- **Tool of the Week system**: `_render_totw_panel()` in admin_outreach.py shows top 5 tools by clicks (7d) with "Send Winner Email" buttons. `tool_of_the_week_html()` email template with trophy, stats, badge preview, embed code. Landing page gold-bordered showcase card after hero.
- **Embeddable comparison widget**: New route file `routes/embed.py`. `/embed` docs page with usage instructions. `/embed/widget.js` self-contained JS that injects comparison table. `/embed/{category}` standalone HTML page for iframe embedding. Bloggers embed one line of code, get live-updating tool comparison.
- **Dead Tool Detector**: `scripts/check_tool_freshness.py` checks GitHub repos via API for last commit date. Stale (90+ days) tools flagged with warning badge on tool pages. Admin "Stale Tools" tab in outreach.
- **Auto-digest newsletter**: `weekly_digest_html()` in email.py — auto-generated from DB data (new tools, top clicked, trending searches, Tool of the Week). Admin panel with "Send Test" (to admin only) and "Send to All Subscribers" buttons.
- **Alternatives SEO**: Thin pages (0 tools) get `<meta name="robots" content="noindex">` via `extra_head` param on page_shell. Tool pages with `replaces` field show pill-style internal links to `/alternatives/{comp_slug}`.
- **Subscriber tracking**: `subscribers` table gained `source TEXT` and `tool_slug TEXT` columns for tracking where signups come from (click interstitial, landing, etc.).
- **Fly.io reliability**: `min_machines_running = 1` in fly.toml (was 0, which allowed all machines to stop during low traffic). Machine will always stay running now.
- **Marketing assets for Ed**: 3 hitlists generated and emailed directly:
  - `marketing/github-issues-hitlist.md` — 45 GitHub issues across 13 categories with reply templates
  - `marketing/answer-sites-hitlist.md` — 84 Quora/dev.to/SO/HN questions with tools to recommend
  - `marketing/directory-submissions.md` — 60 startup directories with submit URLs and copy-paste metadata
- **marketing/ folder**: Gitignored (not in repo). Files sent to Ed via email.

### Round 22 — Design System Token Consolidation (Session Feb 26b)
- **New CSS tokens**: Added `--error-*` (bg/text/border), `--info-text/border`, `--gold-dark`, `--shadow-sm/md/lg`, `--text-xs` through `--heading-lg` typography scale
- **Dark mode tokens**: Error, info, gold-dark, shadow overrides for dark theme
- **Dark mode slate fix**: Swapped `--slate-light`/`--slate-dark` values (were inverted)
- **CSS utility classes**: `.badge` base + `.badge-success/warning/danger/info/muted/gold` modifiers, `.section-divider`, `.pill-price`
- **Component function tokenization**: 12 component functions in components.py converted from hardcoded hex to `var()` tokens (indie_badge, ejectable_badge, maker_pulse, cofounder_badge, indie_score, tool_card, stack_card, featured_card, update_card, verification_banner)
- **Route file tokenization**: 78 hardcoded hex colors replaced with tokens across 6 public-facing route files (landing.py, tool.py, content.py, explore.py, stacks.py, components.py)
- **Toast accessibility**: Added `role="alert" aria-live="polite"` to toast element
- **Placeholder contrast fix**: Banner email input now has explicit `::placeholder` color for dark backgrounds
- **Launch day email**: `launch_day_html()` template in email.py + admin "Send Launch Day Email" panel
- **MCP Registry v0.3.0**: Published to official MCP registry (`io.github.Pattyboi101/indiestack`). 5 tools, 2 resources, 2 prompts.

### SEO
- Sitemap (`/sitemap.xml`) with tools, categories, makers, collections, alternatives, stacks, tags
- JSON-LD `SoftwareApplication` schema on tool pages, `WebSite`+`SearchAction` on homepage, `ItemList` on category pages
- OpenGraph + Twitter Card meta tags on all pages
- **Alternatives pages**: Programmatic SEO for "alternatives to X" queries
- **Tag pages**: 197 programmatic `/tag/{slug}` pages
- **Blog**: `/blog` index + `/blog/stop-wasting-tokens` manifesto post with JSON-LD BlogPosting schema
- **Canonical URLs**: `<link rel="canonical">` on landing, tool, tag, maker, and alternatives pages
- **IndexNow**: Key file at `/{key}.txt`, referenced in robots.txt
- **/llms.txt**: AI-crawler-friendly site description at `/llms.txt`, referenced in robots.txt
- **OG share cards**: `/api/og-home.svg` (homepage), `/api/og/{slug}.svg` (tools)

### Round 4 Features (MCP + Trust)
- **JSON API**: `GET /api/tools/search?q=...` and `GET /api/tools/{slug}` returning structured JSON with integration snippets
- **MCP Server**: Standalone Python MCP server (`mcp_server.py`) — Claude Code, Cursor, Windsurf can search IndieStack before building from scratch
- **"Certified Ejectable" badge**: Green pill badge for tools with clean data export / no lock-in
- **"Tokens Saved" counter**: Per-category token cost estimates
- **MCP landing section**: "Works with your AI tools" on homepage

### Round 5 Features (SEO + Trust)
- **"David vs. Goliath" alternatives pages**: `/alternatives` index + `/alternatives/{competitor}`
- **Maker Pulse badge**: Color-coded freshness indicator (green <30d, amber <90d, gray >90d)
- **Integration snippets**: Python + cURL code blocks with copy buttons on tool pages
- **"Replaces" field**: Tools declare what competitors they replace

### Round 6 Features (Growth)
- **MCP Auto-Integrate**: MCP server returns integration snippets + token savings
- **Dynamic SVG badges**: `/api/badge/{slug}.svg` — embeddable badges for maker websites
- **Badge embed section**: Maker dashboard HTML/Markdown embed code with copy buttons

### Round 7 Features
- **Vibe Stacks**: Admin-curated bundles; public user stacks + community gallery

## Auth

- Cookie-based sessions (`indiestack_session`, 30-day expiry)
- Users have roles: `maker` or `buyer`
- Makers are linked to maker profiles (with slug, bio, indie_status)
- Admin is password-protected at `/admin`
- **GitHub OAuth**: `user:email` scope, three-way matching (github_id → email → new user). Fly secrets: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`. Callback: `/auth/github/callback`.
- **Password reset**: Token-based (1hr expiry), email with reset link
- **Email verification**: Token-based (24hr expiry), sent on signup + magic claim signup, yellow dashboard banner for unverified users with resend button
- **Rate limiting**: In-memory per-IP limits — `/login` 5/min, `/signup` 3/min, `/submit` 3/min, `/api/upvote` 10/min, `/api/wishlist` 10/min, `/api/subscribe` 5/min, `/api/*` 30/min

## Deploy

```bash
cd /home/patty/indiestack && ~/.fly/bin/flyctl deploy --remote-only
```

Pre-flight: syntax check all .py files before deploying.

## Database Tables

| Table | Purpose |
|-------|---------|
| `tools` | Tool listings (name, slug, tagline, price, status, maker_id, is_verified, is_ejectable, replaces, github_url, github_stars, github_language, claimed_by, tool_type, platforms, install_command) |
| `categories` | Problem-based categories (icon, slug, description) |
| `makers` | Maker profiles (name, slug, bio, indie_status) |
| `users` | User accounts (email, password_hash, role, maker_id, github_id, github_username, github_avatar_url) |
| `sessions` | Auth sessions (token, user_id, expires) |
| `upvotes` | IP-based upvotes per tool |
| `tool_views` | Anonymous tool page views (visitor_id hash, for trending algorithm) |
| `wishlists` | User-tool bookmarks |
| `reviews` | Star ratings + text reviews |
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
| `stacks` | Vibe Stacks — curated bundles (name, slug) |
| `stack_tools` | Junction table for stacks ↔ tools |
| `user_stacks` | User-curated "My Stack" pages (user_id, title, description, slug) |
| `user_stack_tools` | Junction table for user stacks ↔ tools |
| `search_logs` | Search query log for Live Wire feed + search intent analytics (api_key_id links to API keys for profile building) |
| `developer_profiles` | Agent memory profiles: api_key_id, interests (JSON category→confidence), tech_stack (JSON), favorite_tools (JSON), personalization_enabled |
| `magic_claim_tokens` | One-click claim URLs for admin DM outreach (7-day expiry, single-use) |
| `milestones` | Maker achievement tracking (first-tool, 100-views, 10-upvotes, first-review, launch-ready) |
| `agent_citations` | Logs when AI agents recommend tools (tool_id, agent_name, context, created_at) |

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
| `POST /api/github-fetch` | Parse GitHub URL, fetch repo metadata (name, description, stars, language, topics) |
| `GET /api/tools/index.json` | Compact index of all tools for prompt caching |
| `POST /api/cite` | Log agent citation/recommendation for a tool |
| `GET /api/stack-builder?needs=&budget=` | Build indie tool stack for given requirements |
| `GET /api/use-cases` | All use cases with tool counts and token estimates |
| `GET /api/use-cases/{slug}` | Detailed use case with comparison tools |
| `GET /api/new?limit=&offset=` | Recently added tools with pagination |
| `GET /api/tags` | All tags with usage counts |
| `GET /api/stacks` | Curated Vibe Stacks |
| `GET /api/collections` | Curated tool collections |
| `GET /api/recommendations` | Personalized tool recommendations based on developer profile (requires API key) |
| `GET /openapi.json` | OpenAPI 3.0 spec for all public endpoints |

## MCP Server

Standalone at `src/indiestack/mcp_server.py`. v0.4.0 published to official MCP registry and PyPI.

**Tools** (11): `search_indie_tools`, `get_tool_details`, `list_categories`, `compare_tools`, `submit_tool`, `browse_new_tools`, `list_tags`, `list_stacks`, `list_collections`, `build_stack`, `get_recommendations`
**Resources** (3): `categories://list`, `trending://tools`, `indiestack://tools-index`
**Prompts** (3): `before-you-build`, `find-alternatives`, `save-tokens`

Calls the JSON API over HTTP. Default base: `https://indiestack.fly.dev`.
Run with: `python3 -m indiestack.mcp_server`

## Email

Gmail SMTP via `email.py`. Secrets on Fly: `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`.
Templates: tool approved, new review, password reset, email verification, weekly digest, maker welcome, tool of the week, auto-digest, launch day, ego ping, wishlist update, competitor ping, claim tool.

## Seed Scripts

- `seed_tools.py` — Populates DB with ~26 real indie tools, 29 makers, GovLink + Patrick Amey-Jones
- `seed_social_proof.py` — Seeds social proof: tag cleanup, duplicate removal, badge assignment, upvotes, views, wishlists, reviews, maker updates, test users, subscribers. Idempotent.
- `purge_seeded_data.py` — Removes all fake social proof (reviews, upvotes, wishlists, test users, maker updates). Run with `--yes` flag to skip confirmation.
- Run on production via: `flyctl ssh console` → `python seed_tools.py && python seed_social_proof.py`

## GitHub

- **Repo**: `Pattyboi101/indiestack` (private)
- **Collaborators**: Ed (`rupert61622-blip`) — push access. Ed contacted all 55 unclaimed tools (39 GitHub issues, emails, Twitter DMs), posted on r/SideProject, PR #1 merged (public submissions without login).
- **Workflow**: Deploy is local → Fly.io via `flyctl deploy`. PRs merge on GitHub, then pull locally and deploy.

### Distribution (Session Feb 23)
- **Landing page**: New headline "Your AI is writing code you don't need." with full-line cyan gradient
- **Visual polish**: Scroll fade-in animations (IntersectionObserver), radial glow behind hero code block, --radius 12px (was 16px)
- **Dark mode**: Forced on landing for first-time visitors via early inline script (respects localStorage)
- **SEO**: IndexNow key file, /llms.txt route, JSON-LD WebSite+SearchAction (homepage), ItemList (category pages)
- **OG share card**: `/api/og-home.svg` — 1200x630 dark SVG with headline + pip install
- **"Free to list" messaging**: Cleaned up across 7 files
- **PyPI v0.1.2**: Published with `<!-- mcp-name: io.github.Pattyboi101/indiestack -->` verification tag
- **MCP Registry**: Published as `io.github.Pattyboi101/indiestack`. Uses `mcp-publisher` CLI.
- **server.json**: In repo root. Update `version` fields when bumping PyPI, then run `mcp-publisher publish`.
- **GitHub cleanup**: Squashed to 1 commit, removed all Gemini/Round files, email scripts, screenshots. Added README.md, smithery.yaml.
- **MCP directory submissions**: Official registry (LIVE), Cursor issue #255, 3 awesome-list PRs (#389, #18, #58), Glama+mcp-get auto-indexed. Tracker: `marketing/mcp-directories.md`.
- **Marketing content**: `marketing/blog-tokens-saved.md` (case study), `marketing/social-pkg-json.md` (X/Reddit/Dev.to/LinkedIn)

### Agent Infrastructure (Session Feb 27)
- **Prompt Cache Index**: `GET /api/tools/index.json` — compact JSON of all 358 tools for agent system prompts. 1-hour cache. MCP resource `indiestack://tools-index`.
- **Agent Citation Tracking**: `POST /api/cite` + auto-citation in MCP search/detail. `agent_citations` table with tool_id, agent_name, context. Maker dashboard shows "Agent Recs (7 days)" stat card.
- **Dual-Audience Messaging**: MCP instructions + llms.txt reframed as "procurement layer for AI agents." New "For AI Agents" section in llms.txt.
- **Stack Builder API**: `GET /api/stack-builder?needs=auth,payments,analytics&budget=50`. `NEED_MAPPINGS` dict maps 18 keywords to category slugs. Returns per-need tools + matching Vibe Stacks + token savings. `build_stack` MCP tool wraps the API.
- **Use Case Pages**: `routes/use_cases.py` — `/use-cases` index, `/use-cases/{slug}` detail pages with comparison tables, build-vs-buy analysis, JSON-LD ItemList, breadcrumbs. JSON APIs at `/api/use-cases`. 18 curated use cases + category fallback.
- **9 new API endpoints** added across sessions: `/api/tools/index.json`, `/api/cite`, `/api/stack-builder`, `/api/use-cases`, `/api/use-cases/{slug}`, `/api/new`, `/api/tags`, `/api/stacks`, `/api/collections`, `/openapi.json`
- **Bug fixes**: submit.py `UnboundLocalError` (redundant local import shadowing module-level), `KeyError: 0` (aiosqlite Row needs aliased column names)

## Production Data (as of Feb 28 2026)

- 480 tools across 21 categories, 20 users, 220+ makers, 66 claimed tools
- 4,557 unique visitors/7d, 18K+ page views/7d, 901 outbound clicks, 346 searches
- 6/55 magic claim links converted (Atomic CRM, Klirr, LiveAsk, Poe the Poet, Volet, ScreenshotOne)
- Notable signups: Invoice Ninja, Francois Zaninotto (Marmelab/Atomic CRM), ScreenshotOne
- Reddit #1 referrer, Bing #2. Ed has done 12 Reddit replies.
- Already launched on Product Hunt
- GitHub OAuth live (credentials set on Fly)
- Admin panel: 3-page split + TOTW panel + weekly digest + stale tools
- LinkedIn company page + personal profile content drafted
- Fly.io: `min_machines_running = 1` (always-on), single shared-cpu-1x:512MB machine in sjc
- R21-R22 features + Agent Infrastructure + Agent Memory deployed. Use --buildkit flag if depot builder times out.
- R22 design system tokens deployed. 78 hardcoded colors replaced.
- Agent Memory live: 11 MCP tools, personalized search, developer profiles, /api/recommendations endpoint.

### Design System Normalization Sweep (Session Feb 28)
- **components.py spacing**: All button/tag/badge/input/form padding aligned to 8px scale. Touch targets ≥44px on all interactive elements (buttons, upvote, hamburger, theme toggle, pagination).
- **Verified card colors**: Hard-coded `#FDF8EE`/`#5C4A1E`/`#2A2318` replaced with `var(--warning-bg)`/`var(--gold-dark)` tokens.
- **Hero headline gradient**: Theme-aware `.hero-headline` CSS class — cyan→navy for light mode, cyan→white for dark mode. Replaced inline style that caused invisible text bug (inline `style="background:none"` overrode class).
- **Full route file sweep**: All 20+ route files normalized — hard-coded hex colors replaced with CSS variables, off-scale spacing fixed, font-family declarations tokenized. Done via parallel agents in 4 batches.
- **38 smoke test endpoints**: Added `/plugins`.

### Plugins & Skills Feature (Session Feb 28)
- **Data model**: 3 new nullable columns on `tools` table: `tool_type TEXT` (mcp_server/plugin/extension/skill), `platforms TEXT` (free-text CSV), `install_command TEXT`. NULL tool_type = regular tool (backwards compatible).
- **Submit form**: Plugin toggle checkbox reveals tool_type dropdown, platforms input, install_command input (monospace). Fields conditionally passed to `create_tool()`.
- **Tool detail page**: Shows type badge (cyan pill), install command block (dark bg, monospace, copy button), platform tags when `tool_type` is set.
- **`/plugins` discovery page**: `routes/plugins.py` — type filter pills (All/MCP Servers/Plugins/Extensions/Skills), platform filter pills (auto-detected from DB, top 8 by frequency), card grid, empty state with submit CTA.
- **Nav**: "Plugins" added to desktop dropdown and mobile menu in components.py.
- **Search API**: Conditionally includes `tool_type`, `platforms`, `install_command` in JSON response when tool has a type set.
- **MCP server**: Search results show type label and install command line for plugin-type tools.
- **Design doc**: `docs/plans/2026-02-28-plugins-skills-design.md`
- **Implementation plan**: `docs/plans/2026-02-28-plugins-skills.md` (8 tasks, all complete)

### Growth Sprint + Agent Memory (Session Feb 28b)
- **Maker ✓ badge**: Claimed tools show green "Maker ✓" (`badge-success`) on all tool cards. Unclaimed show gray "Community Listed" (`badge-muted`). Implemented in `tool_card()` in components.py.
- **Landing stats bars**: Hero and MCP walkthrough show `{claimed_count} maker-verified` alongside tool count and agent lookups.
- **Trending boost for claimed tools**: +20 heat score for tools with `claimed_by IS NOT NULL` in db.py trending algorithm.
- **Pricing reframe**: Badge changed to "COMING SOON", CTA changed to "Join the Waitlist" → /signup.
- **Wishlist → Bookmark rename**: All user-facing "wishlist" text changed to "bookmark" across 7 files (components.py, tool.py, dashboard.py, main.py, email.py, content.py, admin_analytics.py). Internal DB table `wishlists` and API routes `/api/wishlist` unchanged.
- **Agent Memory**: Developer profiles built from search patterns via API keys.
  - `developer_profiles` table: api_key_id, interests (JSON: category→confidence), tech_stack (JSON array), favorite_tools (JSON array), personalization_enabled, updated_at.
  - `search_logs.api_key_id` column added via migration (links searches to API keys).
  - Profile builder in db.py: recency-weighted scoring (3x for 7d, 2x for 30d, 1x older), `TECH_KEYWORDS` extraction, `NEED_MAPPINGS` category matching.
  - Personalized search reranking: `final_score = fts_relevance + (category_match * 0.3) + (stack_match * 0.2) + (favorite_boost * 0.1)`. First-search notice shown once.
  - `/api/recommendations` endpoint: interest-based tool selection + discovery pick (trending tool outside usual interests).
  - `get_recommendations()` MCP tool (sync, not async — uses `urllib.request`).
  - Developer UI at `/developer`: profile card with interest pills, tech stack pills, favorite tools. Clear preferences and pause personalization buttons.
  - Design doc: `docs/plans/2026-02-28-agent-memory-design.md`. Implementation plan: `docs/plans/2026-02-28-agent-memory.md`.
- **Feature surfacing**: API nav link (desktop + mobile), dashboard API key nudge banner, copy-install snippet on /developer page (pre-filled with API key), MCP prompt updates mentioning `get_recommendations()`.
- **Bug fix**: Removed `CREATE INDEX idx_search_logs_api_key` from SCHEMA string — was crashing on startup because column didn't exist yet (migration adds it). Migration block handles index creation.

### PH Launch Prep + Growth Features (Session Mar 2)
- **Install commands fixed**: All 8 occurrences of `uvx indiestack` → `uvx --from indiestack indiestack-mcp` across landing.py, main.py, content.py, launch.py, dashboard.py. Also fixed Cursor/Windsurf JSON args.
- **MCP explainer**: Added one-liner under "How it works" heading on landing page explaining what MCP (Model Context Protocol) is for non-technical PH visitors.
- **Landing page stats reframe**: "agent lookups" (mcp_view_count only) → "AI recommendations" (mcp_view_count + search_logs count + agent_citations count). Shows ~900+ instead of 144.
- **Catalog cleanup**: Deleted 34 VC-funded/paid SaaS tools with seeded upvotes (Stytch, Attio, ScrapingBee, Resend, Postmark, incident.io, etc). Reclassified 10 open-source tools (PocketBase, Dokku, Appwrite, Langfuse, etc) from `saas` → `code` with votes reset to 0. Un-featured SuperTokens, Logto, Umami, Chatwoot (deleted). Catalog: 881 tools (571 code, 310 saas).
- **Live AI Recommendation Badge**: New default badge style at `/api/badge/{slug}.svg`. Shows pulsing red CSS dot + live count from `mcp_view_count + agent_citations`. Three states: "AI Discoverable" (0 recs), "X AI recs" (<1000), "X.Xk AI recs" (1000+). Green `#10B981` right section, 1-hour cache. Old styles available via `?style=tokens`, `?style=winner`, `?style=early`.
- **Badge UX**: "Get Badge" button on tool page restricted to tool's own maker (links to `/dashboard#badge`). Dashboard badge section redesigned with step-by-step instructions (Markdown for GitHub README, HTML for websites). Badge preview with copy buttons.
- **`/gaps` page**: `routes/gaps.py` — public page showing zero-result searches ranked by demand frequency. Uses `get_search_gaps()` from db.py. Blocklist filters junk queries. Heat indicators (🔥🔥🔥 High demand / 🔥🔥 Growing / 🔥 Emerging / New). "Fill this gap →" buttons link to `/submit?name={query}` (URL-encoded). Hero explains concept, 3-step visual flow, CTA at bottom. Added to Browse dropdown nav + mobile menu.
- **`/pulse` page (AI Pulse)**: `routes/pulse.py` — live feed of AI agent activity in real time. `get_pulse_feed()` in db.py merges `search_logs` + `agent_citations` via UNION ALL into a single chronological feed (last 7 days, limit 50). Three event types: recommend (green dot — agent citation), search (cyan dot — search found a match), gap (red dot — zero results). Auto-refreshes every 30s via `/api/pulse` JSON endpoint that returns server-rendered HTML. Pulsing red dot CSS animation. Stats bar (today/week/all-time). Legend. CTA links to /submit and /gaps. Added to Browse dropdown nav + mobile menu.
- **Submit page transparency note**: Info box on submit form below heading — "A note from us: IndieStack is still young — a small, curated directory built by two uni students in Cardiff..." Frames the mission (generational knowledge for AI agents) and incentivizes early listers.
- **Bug fixes**: (1) URL encoding — all `/submit?name=` links in gaps.py and pulse.py now use `quote()` instead of raw `escape()`. (2) Submit form reads `?name=` query param to pre-fill tool name from gap links. (3) `_relative_time()` handles negative diffs (clock skew → "just now"). (4) Exception handling narrowed from bare `except Exception` to `except (ValueError, TypeError, AttributeError)`.
- **Security audit**: Passed — SQL injection safe (parameterized queries), rate limiting adequate (30 req/60s on `/api/*`), no sensitive data exposed, XSS properly escaped via `html.escape()`.

# IndieStack — Round 13: Admin & User QoL Polish

## Context

IndieStack is a curated marketplace for indie SaaS tools, built by two university students with Python/FastAPI/SQLite and Claude Code. We're at ~2,000 unique visitors and about to launch on Product Hunt.

The core features are done — discovery, payments, claiming, boosts, badges, SEO, blog, MCP server. Now we need **quality-of-life polish** to make both the admin experience and user experience feel professional and finished.

Live at: https://indiestack.fly.dev

---

## Full Architecture (What Exists)

### Tech Stack
- Python 3.11, FastAPI, aiosqlite (SQLite + WAL mode)
- Pure Python string HTML templates (no Jinja2, no React, no JS frameworks)
- Stripe Connect for payments, Gmail SMTP for email
- Fly.io, single machine, Docker
- Design: DM Serif Display (headings), DM Sans (body), JetBrains Mono (tags). Navy/cyan palette, dark mode support.

### All Routes (what users can access)

| Route | What It Does |
|-------|-------------|
| `/` | Homepage — hero, search, trending tools (scroll-row), categories, live ticker, stats, testimonials |
| `/explore` | Faceted tool browsing — filter by category, tags, price, sort, verified, ejectable. Card grid with pagination |
| `/tool/{slug}` | Tool detail — description, reviews, changelogs, badges, similar tools, claim/boost CTA, JSON-LD |
| `/search?q=` | FTS5 search with filters |
| `/new` | Recently added tools |
| `/tags` | All tags page |
| `/tag/{slug}` | Per-tag landing pages (~197 tags, programmatic SEO) |
| `/category/{slug}` | Per-category browse pages |
| `/makers` | Maker directory with search, sort by tools/upvotes |
| `/maker/{slug}` | Maker profile — bio, tools, indie status |
| `/collections` | Curated tool collections |
| `/stacks` | Vibe Stacks — curated bundles at 15% discount |
| `/stacks/community` | User-created shareable stacks |
| `/stack/{username}` | Individual user stack |
| `/compare/{slug1}/{slug2}` | Side-by-side tool comparison |
| `/alternatives` | Alternatives index (programmatic SEO) |
| `/alternatives/{competitor}` | "Best indie alternatives to X" pages with Featured boost |
| `/best` | Best indie tools index — 20 category pages |
| `/best/{category}` | Ranked tools per category with medals |
| `/blog` | Blog index |
| `/blog/{slug}` | Blog posts (2 published) |
| `/submit` | Tool submission form with earnings calculator |
| `/pricing` | Pro tier (£9/mo) — lower commission, verified badge, analytics |
| `/login` | Login with `?next=` redirect support |
| `/signup` | Signup with `?next=` redirect support |
| `/dashboard` | Maker dashboard — tools, saved, updates, changelogs, notifications, Stripe Connect, analytics, badge embed, launch readiness |
| `/admin` | Admin panel — tool review, bulk import, toggle verified/ejectable/boost, collections, stacks, reviews, makers |
| `/about`, `/faq`, `/terms`, `/privacy` | Static content pages |
| `/live` | MCP live wire — real-time developer search feed |
| `/updates` | Build-in-public feed |
| `/explore` | Tool browsing with sort/filter |

### API Endpoints
| Endpoint | What It Does |
|----------|-------------|
| `POST /api/upvote` | Toggle upvote (IP-based) |
| `POST /api/wishlist` | Toggle wishlist (user-based) |
| `POST /api/claim` | Instant claim tool for logged-in user |
| `POST /api/claim-and-boost` | Claim + Stripe checkout for £29 boost |
| `POST /api/boost` | Boost already-claimed tool (£29) |
| `GET /boost/success` | Stripe callback for boost |
| `POST /api/subscribe` | Email newsletter signup |
| `GET /api/tools` | JSON API for tool search |
| `GET /api/tools/{id}` | JSON API for single tool |
| `GET /api/badge/{slug}.svg` | SVG embeddable badge |
| `GET /api/milestone/{slug}.svg` | Milestone celebration card |
| `GET /verify-claim/{token}` | Legacy claim token verification |
| `GET /sitemap.xml` | Full sitemap |
| `GET /feed/rss` | RSS feed |

### Badges & Trust Signals
- **Verified** — gold gradient, checkmark icon. Paid or admin-granted.
- **Ejectable** — green. Tool supports data export.
- **Featured** — cyan gradient. Paid boost (£29/30 days).
- **Maker Pulse** — purple. Active development.
- **Changelog Streak** — fire emoji. Updated in last 14 days.
- **Indie Status** — Solo Maker / Small Team badges.
- **Co-Founder** — badge for early adopters.

### Admin Panel (Current State)
The admin page at `/admin` is a single long page with:
1. **Stats bar** — total tools, revenue, etc.
2. **Pending review section** — approve/reject cards with bulk actions
3. **All tools table** — flat list of every tool with toggle buttons for verified/ejectable/boost/feature
4. **Collections management** — create/delete collections, add/remove tools
5. **Stacks management** — create/delete stacks, add/remove tools
6. **Reviews section** — all reviews with delete option
7. **Makers section** — all makers with edit name/slug
8. **Bulk import** — JSON textarea for batch tool creation

**Admin pain points:**
- No filtering or sorting on the "All Tools" table (131 tools, growing)
- No search within admin
- No way to see tool stats (views, upvotes) at a glance in the table
- No way to quickly find unclaimed tools
- No tool count in the stats bar
- No date information (when was each tool added?)
- The page is very long — everything is on one page

### User/Visitor Experience (Current State)
- Clean design, responsive, dark mode
- Nav: Logo | Explore | Browse ▾ | Add Your Tool | Theme Toggle | Auth
- Search works well (FTS5)
- Tool pages show badges, reviews, changelogs, similar tools
- Claim flow is frictionless (claim + boost CTA)
- Dashboard has launch readiness checklist, analytics, badge embed

**User pain points (suspected):**
- No onboarding flow after signup — user lands on empty dashboard
- No "getting started" guidance for new makers
- No confirmation/feedback after upvoting (just a number change)
- No breadcrumbs on deep pages (tool → category relationship unclear)
- No "back to results" after viewing a tool from search/explore
- Review form could be more prominent
- No way to share a tool easily (no share buttons)
- Email verification feels disconnected — banner is easy to miss

---

## What I Need

Give me **10 specific QoL improvements** ranked by impact-to-effort ratio (highest first). For each one:

1. **What it is** — one sentence
2. **Why it matters** — what user/admin problem it solves
3. **Effort estimate** — small (< 30 min), medium (1-2 hours), large (half day)
4. **Which file(s)** to modify

Split them into two groups:

### Group A: Admin QoL (5 improvements)
Focus on making the `/admin` page faster and more useful for managing 131+ tools.

Must include:
- Filter/sort controls on the tools table (by status, verified, category, date, search)
- Any other admin efficiency improvements you think matter

### Group B: User/Visitor QoL (5 improvements)
Focus on polish that makes the site feel professional and increases engagement/conversion.

Think about:
- What would make a developer's first 30 seconds on the site more engaging?
- What small touches make a marketplace feel "real" vs "student project"?
- What drives signups beyond just claiming?

---

## Constraints
- Pure Python string HTML templates — no React, no Jinja2
- Minimal JavaScript (what exists is inline onclick handlers)
- SQLite, single machine
- We can ship features in hours with Claude Code
- The site needs to look polished for Product Hunt launch screenshots
- Don't suggest features we already have (check the route list above)

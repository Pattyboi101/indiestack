# IndieStack — Full Context for Deep Research (March 13, 2026)

> This document gives an AI researcher complete context on IndieStack's current state, recent changes, and open questions. Use this to generate original product and site improvement ideas.

---

## What IndieStack Is

IndieStack is the open-source supply chain for agentic workflows. When an AI coding agent (Claude, Cursor, Windsurf, Copilot) is about to help someone build authentication, payments, analytics, or anything else — it checks IndieStack first to see if an indie creator already built it. Instead of generating 80,000 tokens of code from scratch, the agent recommends a proven indie tool in 5,000 tokens of integration glue.

**The constraint is "indie-built," not "developer tool."** The catalog includes games, newsletters, creative tools, learning apps, utilities — anything made by independent creators or small teams. Dev tools are the wedge (that's where AI coding agents live), but the vision is everything indie.

**Live at**: https://indiestack.ai
**Built by**: Patrick (zoology student, Cardiff University) and Ed (co-founder), using Claude Code. No prior coding experience — the entire thing is vibe-coded with AI.
**Launched on Product Hunt**: March 7, 2026.

---

## Current Numbers (March 13, 2026)

| Metric | Value |
|--------|-------|
| Verified-alive tools | 3,099 |
| Categories | 25 |
| Compatibility pairs | 1,279 |
| Registered users | 52 |
| Total search logs | 1,113 |
| Page views (last 7 days) | 124,219 |
| Demand gaps (zero-result searches) | 146 |
| Paying subscribers | 1 (test — Patrick's own account) |
| MCP server version | v1.3.1 (PyPI + official MCP Registry) |
| MCP server tools | 15 |

### Category Distribution (Top 10)

| Category | Tools |
|----------|-------|
| Developer Tools | 2,096 |
| AI & Automation | 132 |
| Monitoring & Uptime | 71 |
| Design & Creative | 71 |
| Authentication | 67 |
| Project Management | 60 |
| File Management | 58 |
| Analytics & Metrics | 48 |
| Learning & Education | 42 |
| AI Dev Tools | 41 |

**Note**: The catalog is heavily skewed toward Developer Tools (68%). The auto-indexer pulled from GitHub, which naturally skews dev-heavy. Non-dev categories (Games, Newsletters, Creative, Learning) have been seeded but are thin.

---

## Tech Stack

- **Backend**: Python 3.11, FastAPI, aiosqlite (SQLite + WAL mode)
- **Frontend**: Pure Python f-string HTML templates — no Jinja2, no React, no build step, no external JS framework
- **CSS**: All inline or in a `:root` token block in components.py. No external stylesheets.
- **Deployment**: Fly.io, single machine, Docker, persistent SQLite volume
- **MCP Server**: httpx async, TTL cache, circuit breaker, retry, connection pooling
- **Design**: DM Serif Display (headings), DM Sans (body), JetBrains Mono (code). Navy #1A2D4A primary, cyan #00D4F5 accent. Dark mode default on landing, user-selectable elsewhere.

**Why this matters for ideas**: Any frontend feature must be buildable with inline HTML/CSS and vanilla JS. No React components, no npm, no build pipeline. This is a constraint AND a strength — the site is extremely fast to load and simple to deploy.

---

## What We Just Changed (March 12-13 Site Refresh)

### Navigation
**Before**: `Explore | Browse ▾ (AI Optimize, New, Tags, Stacks, Demand Board, What is IndieStack?) | Submit`
**After**: `Explore | For Makers ▾ (AI Optimize, Submit a Tool) | Resources ▾ (What is IndieStack?, Demand Board, Stacks) | [Submit]`

Rationale: "Browse" mixed discovery, maker tools, and informational pages. Now grouped by intent.

### Landing Page
- Banner: "MCP Server v1.3" → "{tool_count}+ indie creations — now with Agent Cards for every tool"
- Hero status tag: "KNOWLEDGE LAYER FOR AI AGENTS" → "OPEN-SOURCE SUPPLY CHAIN FOR AI" (navy text, not white-on-white anymore)
- Hero subtitle: references 3,095+ tools, assembly narrative
- Bottom section: replaced full-width gradient maker CTA with demand teaser (4 live gaps from agent searches showing "what agents are searching for") + slim submit CTA
- Stats pills: dynamic tool count + AI recommendations count

### Explore Page
- Added search bar at top of filter area
- Category + Sort dropdowns stay visible
- Tag pills, source type, ejectable checkbox wrapped in `<details>` collapsible ("More filters")
- Auto-opens if any secondary filter is active
- `/new` now 302 redirects to `/explore?sort=newest`
- `/tag/{slug}` now 302 redirects to `/explore?tag={slug}`

### "What is IndieStack?" Page
- Hero: "The Knowledge Layer for AI Agents" → "The Open-Source Supply Chain for AI Agents"
- Reduced "supply chain" from 8 uses to 2 visible (varied with "catalog", "ecosystem", "foundation")
- Tightened 3 audience sections from 3-4 paragraphs to 2 each
- Added AI recommendations stat
- Removed stale Product Hunt-specific language

### Sitewide Copy
- All "knowledge layer" references → "open-source supply chain" across footer, llms.txt, agent-card.json, meta descriptions, email templates, submit page, launch page, API docs

---

## Key Features & Infrastructure

### MCP Server (15 tools)
The primary distribution channel. AI coding agents install it and query IndieStack directly.

| Tool | Purpose |
|------|---------|
| find_tools | Search by keyword, category, source type |
| get_tool_details | Full detail + assembly metadata + compatible tools |
| compare_tools | Side-by-side comparison |
| build_stack | "I need auth + payments + analytics" → complete stack |
| scan_project | Describe your project → tailored stack recommendation |
| evaluate_build_vs_buy | Should you build or use an existing tool? |
| analyze_dependencies | Analyze package.json/requirements.txt → indie alternatives |
| get_recommendations | Personalized based on agent memory |
| report_compatibility | Report tool pairs that work together |
| check_health | Check maintenance status of adopted tools |
| browse_new_tools | What's new in the catalog |
| list_categories, list_tags, list_stacks | Browse taxonomy |
| publish_tool | Submit from inside your agent |

### Agent Infrastructure
- **Per-tool Agent Cards**: `/cards/{slug}.json` — A2A-compatible JSON with capabilities, health, trust, compatibility
- **Agent memory**: `developer_profiles` table — category interests, tech stack inference, personalized reranking
- **llms.txt + llms-full.txt**: Agent-readable catalog
- **A2A agent card**: `/.well-known/agent-card.json`

### Structured Metadata (Agentic Package Manager)
Every tool has: `api_type`, `auth_method`, `sdk_packages` (JSON), `env_vars` (JSON array), `install_command`, `frameworks_tested`, `verified_pairs`. This makes agent recommendations actionable — agents can give exact install commands and env var requirements.

### Compatibility Graph
1,279 tool pairs from framework affinity, complementary categories, and same-category popular tools. Agents report successful pairings via `report_compatibility`. Tool detail pages show "Works Well With" section.

### Demand Signals
- **Free tier** (`/gaps`): Top 5 demand gaps with tier badges (High Demand / Growing / Emerging / New Signal). "Build This →" buttons.
- **Paid tier** (`/demand`, $15/month): Full dashboard with clustered signals, trend data (CSS bar charts), source breakdown, JSON export. Stripe integration live.
- **Landing page teaser**: 4 live gaps shown at bottom of landing page ("What agents are searching for")

### GEO Lead Magnet (`/geo`)
Free tool: paste your project URL → auto-scrape → generate llms.txt + Agent Card JSON for your project. GitHub OAuth gate → auto-adds tool to IndieStack catalog as pending. Growth flywheel: solves devs' AI discoverability problem while growing the catalog.

### Discovery & Trust
- **Search**: FTS5 with `replaces` fallback — when search returns 0 results, checks `LOWER(t.replaces)` to find indie alternatives
- **Tool of the Week**: Featured tool on landing page
- **Trending**: Activity-based ranking (views + bookmarks + upvotes)
- **Health monitoring**: GitHub API checks for last commit, open issues, archive status
- **Indie Score**: Composite trust signal
- **Maker ✓ badge**: Green badge on claimed tools vs. gray "Community Listed" on unclaimed
- **Live AI Badge**: Embeddable SVG showing real-time AI recommendation count

### Auto-Pipelines
- **GitHub Auto-Indexer**: 73 search queries, quality filters (stars 10-50K, active, not fork, indie owner), corporate blocklist
- **README Enricher**: Extracts install commands, env vars, frameworks from GitHub READMEs
- **Pair Generator**: Framework affinity, complementary categories, same-category popular pairings
- **Health Checker**: Detects dead/archived repos

### User Features
- GitHub OAuth login
- Bookmark tools
- Reviews (text + rating)
- Upvotes
- Maker dashboard (edit tool, pixel avatar, badge embed, maker story)
- Developer profiles with agent memory controls

---

## What's NOT Working (Honest Assessment)

1. **No organic growth loop** — catalog grows only via manual indexer runs or rare submissions. 52 users is tiny.
2. **Low maker engagement** — very few creators actively submitting or claiming tools. The "Submit" flow exists but nobody's using it unprompted.
3. **MCP installs unmeasurable** — we can't tell how many agents are actually querying IndieStack via the MCP server. No install telemetry.
4. **No revenue** — Demand Signals Pro exists but has 0 real paying customers. No other monetization active.
5. **No community** — no Discord, no forum, no user-generated content beyond a handful of reviews.
6. **Developer Tools dominance** — 68% of catalog is one category. Non-dev categories feel empty.
7. **The site feels static** — despite 124K page views, the content rarely changes visually. No activity feed, no "what's happening" sense.
8. **Ed (co-founder) is underutilized** — limited to occasional Reddit posts and social outreach. No clear role in the product.
9. **Browse-based discovery doesn't scale** — with 3,099 tools, scrolling through explore page is overwhelming. Search helps but most people don't arrive with a specific query.
10. **The landing page is long** — hero → MCP walkthrough → search widget → trending → categories → demand teaser → maker CTA. Is it too much? Does it try to serve too many audiences?

---

## Site Architecture (Page Map)

| Page | Purpose | Traffic |
|------|---------|---------|
| `/` | Landing page — hero, trending, categories, demand teaser | Primary entry |
| `/explore` | Browse/filter/search 3,099 tools | Core discovery |
| `/tool/{slug}` | Individual tool detail | Most visited (from agent recs) |
| `/submit` | Submit a new tool | Growth input |
| `/geo` | GEO lead magnet — generate llms.txt + Agent Card | Lead gen |
| `/gaps` | Demand Board — free tier | Maker engagement |
| `/demand` | Demand Signals Pro — paid dashboard | Revenue |
| `/what-is-indiestack` | Explainer page | Education |
| `/stacks` | Community-curated tool stacks | Discovery |
| `/dashboard` | Maker dashboard (logged in) | Retention |
| `/developer` | Developer profile + agent memory controls | Retention |
| `/vs/{slug1}/{slug2}` | Tool comparison pages | SEO |
| `/alternatives/{tool}` | Indie alternatives to big tools | SEO |
| `/tags` | Tag cloud | SEO |
| `/pulse` → `/demand` | Redirects to demand dashboard | — |
| `/new` → `/explore?sort=newest` | Redirects | — |

---

## The Competitive Landscape

- **No direct competitor** doing exactly this (curated indie catalog + MCP server + compatibility graph + agent memory)
- **Tangential competitors**: awesome-lists (static, no API), G2/Capterra (enterprise, no agent API), Product Hunt (discovery but no agent integration), npm/PyPI (packages, not tools/SaaS)
- **Emerging threat**: AI companies building their own tool registries (OpenAI plugins, Anthropic tool use marketplace)
- **Our moat**: curation quality + compatibility data + agent memory + structured metadata + demand signal data. Question: is this enough?

---

## Design System

- **Aesthetic**: Linear.app-inspired — clean, precise, intentional. Navy/cyan color scheme.
- **Dark mode default** on landing page, user-selectable elsewhere
- **Design tokens**: Full system in components.py `:root` — colors, shadows (sm/md/lg), typography (xs through heading-xl), badge classes, spacing (8px base)
- **Fonts**: DM Serif Display (display headings), DM Sans (body), JetBrains Mono (code/tags)
- **Interactive elements**: Glassmorphism hero with proximity glow canvas, upvote buttons, search widget with live results, theme toggle
- **No JS framework** — all interactivity is vanilla JS inline in templates

---

## Key Design Decisions Already Made

1. **Indie-only constraint** — no VC-backed, no enterprise. This is the quality filter.
2. **Agent-first distribution** — MCP server is the primary product, website is secondary.
3. **Structured metadata > descriptions** — agents need api_type, auth_method, install_command, not marketing copy.
4. **Open source MCP server** — anyone can install it, soft API key enforcement.
5. **Fair presentation** — no pay-to-rank, best tool wins.
6. **Python f-string templates** — fast iteration, single developer, no frontend build step.
7. **SQLite single-file DB** — simple, fast, deployed on Fly.io persistent volume.

---

## Open Questions We'd Love Insight On

1. Is the site trying to serve too many audiences? (AI agents, developers evaluating tools, makers submitting, general visitors)
2. Should IndieStack feel more "indie" and less "polished SaaS"? Does the Linear-inspired aesthetic work for or against the brand?
3. At 3,099 tools, browse-based discovery is straining. What replaces it — or supplements it — at 10,000 tools?
4. The demand signal data (what agents search for and can't find) is potentially the most valuable asset. How should we monetize and surface it beyond the current dashboard?
5. What would make a maker *excited* to claim and enrich their tool listing — not just willing?
6. Should we have a blog, changelog, or content strategy? What content formats drive organic traffic for tool directories?
7. Is the landing page too long? Does it try to do too much?
8. What interactive elements would justify adding vanilla JS complexity?
9. How do we create a sense of "aliveness" on a site that's mostly a static catalog?
10. Is $15/month the right price for Demand Signals Pro? Too cheap? Too expensive? Wrong model entirely?

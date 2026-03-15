# IndieStack — Context for Growth Strategy Research

> This document provides complete context for researching IndieStack's growth from 52 to 500+ users and first paying customers.

---

## What IndieStack Is

IndieStack (indiestack.ai) is the open-source supply chain for agentic workflows. It's a curated catalog of 3,100+ indie-built creations across 25 categories (dev tools, games, utilities, newsletters, creative tools, learning apps) with a Python MCP server on PyPI that lets AI coding agents (Claude Code, Cursor, Windsurf) discover and recommend indie tools instead of generating code from scratch. Built by two uni students in Cardiff using Claude Code.

## Current Data Volumes (as of March 15, 2026)

| Table | Count | Notes |
|-------|-------|-------|
| tools | 3,100 | Curated catalog (828+ manually approved) |
| users | 52 | Registered accounts |
| subscriptions | 1 | Active Pro (test) |
| api_keys | 9 | 3 free tier, 6 pro tier |
| agent_citations | 184 | Times an agent cited an IndieStack tool |
| search_logs | 1,310 | Site searches (top: email 328, analytics 292, auth 167) |
| page_views | 208,138 | Total lifetime |
| outbound_clicks | 27,928 | Clicks through to tool websites |
| claim_requests | 12 | 8 approved, 4 rejected |
| tool_pairs | 1,279 | Compatibility relationships |
| upvotes | 60 | Community votes |
| reviews | 4 | User reviews |
| makers | 645 | Maker profiles (auto-created from GitHub) |
| milestones | 13 | Citation milestone notifications |
| purchases | 0 | Zero revenue |

## Distribution Channels (Current)

### MCP Server (Primary)
- Published on PyPI as `indiestack` (pip install indiestack)
- 15 tools: find_tools, build_stack, scan_project, evaluate_build_vs_buy, analyze_dependencies, etc.
- Rate limiting: keyless 15/day, free key 50/day, Pro key 1,000/day
- Assembly metadata on every tool: api_type, auth_method, sdk_packages, env_vars
- Per-tool Agent Cards at /cards/{slug}.json
- report_outcome() for trust data (only 1 call ever)

### Website (Secondary)
- 208K page views, but only 52 registered users (0.025% conversion)
- Top search terms: email (328), analytics (292), auth (167)
- 28K outbound clicks — people use it to find tools, but don't sign up
- Stack Auditor: paste package.json, get indie alternatives
- GEO lead magnet: generate llms.txt from any URL
- Demand Signals Pro: $15/month trend dashboard (0 paying users)

### Product Hunt
- Launched March 7, 2026
- Live listing, some upvotes but not featured
- No significant sustained traffic from PH

## Revenue Model

- **Pro subscription**: $19/month or $99/year (Founder tier) — currently testing $9/month
- **$99 LTD**: Lifetime deal as conversion vehicle
- **Pro features**: Stack Auditor, Demand Signals dashboard, priority API (1,000 req/day), integration recipes
- **Current revenue**: $0

## What's Been Built (Technical Infrastructure)

- FastAPI + SQLite (WAL mode) on Fly.io
- GitHub auto-indexer (73 search queries, grew catalog 335 to 3,100)
- README enricher (auto-extracted install commands, env vars, frameworks)
- Pair generator (1,279 compatibility pairs)
- Quality gates (domain age, free tier detection, social proof, URL reachability)
- Tool health monitoring (GitHub API — stars, last commit, maintenance status)
- 3-tier API rate limiting with isk_ prefix keys
- Pixel art avatar system (7x7 grid, 16 colors)
- Command hub for team coordination (govlink.fly.dev)
- Shared Claude Code skills (status, backup, deploy, brainstorm, hub, email)

## Team

- **Patrick** — backend, infrastructure, MCP server, strategy. Final year Zoology BSc at Cardiff Uni.
- **Ed** — frontend polish, new pages, growth tooling, outreach. Just got dev environment set up.
- Both ship via Claude Code at 5-10x traditional speed.

## What We've Already Tried

- Product Hunt launch (March 7) — one-day spike, no sustained conversion
- MCP server on PyPI — 9 API keys issued, but unclear how many active installs
- Demand Signals Pro as paid product — 0 conversions at $15/month
- GEO lead magnet — generates llms.txt files, some interest but no conversion to Pro
- Auto-indexer for catalog growth — successfully grew to 3,100 tools
- Quality gates to filter vibecoded SaaS spam — working but doesn't drive growth

## Previous Gemini Research Sessions (Avoid Repeating)

1. **Strategic Breakthrough** (March 12) — broad strategy, positioning
2. **Site & Product Improvement** (March 13) — UX, stickiness, engagement
3. **Demand Signals Pro** (March 13) — paid data product strategy
4. **Pro Subscription Architecture** (March 13) — Pro feature design
5. **Autonomous Agent Strategy** (March 14) — agent-first distribution
6. **Defensibility & Moat** (March 14) — competitive moat analysis
7. **Maker Incentive & Retention** (March 14) — supply-side engagement
8. **Quality Gates** (March 14) — vibecoded SaaS filtering
9. **Why Go Pro** (March 14) — conversion psychology for $0 to first paying

This session should focus on TACTICAL EXECUTION — not more strategy. We need a specific playbook for THIS WEEK, not another vision document.

## Key Questions

1. What are the highest-ROI distribution channels for an MCP-first developer tool in March 2026?
2. How do you convert "MCP server users who never visit the website" into paying customers?
3. Is $9/month or $99 LTD the right price point at 52 users with 0 revenue?
4. Should a GitHub Action audit tool be our primary growth vehicle?
5. What Product Hunt follow-up tactics actually work in the 7-30 day window?
6. How do two-sided marketplaces (makers + developers) crack chicken-and-egg at this scale?
7. What specific communities (subreddits, Discord servers, forums) should we target?
8. Is "agent SEO" (optimizing to be recommended by AI agents) a real channel yet?

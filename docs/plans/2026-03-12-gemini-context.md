# IndieStack — Full Context for Deep Research

> This document gives an AI researcher complete context on IndieStack to generate original strategic ideas.

---

## What IndieStack Is

IndieStack is the knowledge layer between AI agents and indie-built software. When an AI coding agent (Claude, Cursor, Windsurf, Copilot) is about to help someone build authentication, payments, analytics, or anything else — it checks IndieStack first to see if an indie creator already built it. Instead of generating 80,000 tokens of code from scratch, the agent recommends a proven indie tool in 5,000 tokens of integration glue.

**The constraint is "indie-built," not "developer tool."** The catalog includes games, newsletters, creative tools, learning apps, utilities — anything made by independent creators or small teams. Dev tools are the wedge (that's where AI coding agents live), but the vision is everything indie.

**Live at**: https://indiestack.ai
**Built by**: Patrick (zoology student, Cardiff University) and Ed (co-founder), using Claude Code. No prior coding experience — the entire thing is vibe-coded.

---

## Current State (March 12, 2026)

### The Numbers
- **3,095 verified-alive tools** across 25 categories
- **1,272 compatibility pairs** (tools verified to work well together)
- **MCP server v1.3.1** on PyPI + official MCP Registry
- **15 MCP tools** (search, details, compare, build_stack, scan_project, analyze_dependencies, evaluate_build_vs_buy, get_recommendations, browse_new, categories, tags, stacks, publish_tool, report_compatibility, check_health)
- **3 MCP resources**, 5 prompts
- **Agent memory system** (developer profiles with category interests, tech stack inference, personalized reranking)
- **API key system** (`isk_` prefix, soft enforcement)
- **Structured metadata** on every tool: api_type, auth_method, sdk_packages, env_vars, install_command, frameworks_tested
- **Auto-indexer** (73 GitHub search queries, quality filters, corporate blocklist)
- **README enricher** (auto-extracts install commands, env vars, frameworks from GitHub READMEs)
- **Pair generator** (framework affinity, complementary categories, same-category popular)
- **Health checker** (GitHub API, detects dead/archived repos, weekly cadence planned)
- **AI Pulse page** (live feed of agent searches, recommendations, gaps)
- **Demand Bounty Board** (real-time demand signals from failed agent searches)
- **llms.txt + llms-full.txt** (agent-readable catalog)
- **A2A protocol agent card** (/.well-known/agent-card.json)

### Tech Stack
- Python 3.11, FastAPI, aiosqlite (SQLite + WAL mode)
- Pure Python string HTML templates (no Jinja2, no React, no build step)
- Deployed on Fly.io (single machine, Docker, persistent volume)
- MCP server: httpx async, TTL cache, circuit breaker, retry, connection pooling

### What's Working
- MCP server is installed and working in Claude, Cursor, Windsurf
- Listed on official MCP Registry, PyPI, 3 awesome-list PRs
- Auto-indexer pipeline can grow catalog efficiently
- Structured metadata makes agent recommendations actionable (install commands, env vars, auth methods)
- Compatibility graph gives agents confidence in recommending tool combinations
- Agent memory enables personalized recommendations that improve over time

### What's NOT Working (The Growth Plateau)
- **No organic growth loop** — catalog grows only when Patrick manually runs the indexer or approves submissions
- **Low maker engagement** — very few indie creators actively submitting or claiming tools
- **MCP installs are hard to measure** — no reliable way to know how many agents are actually using IndieStack
- **Ed has nothing to do** — co-founder role is unclear, limited to Reddit outreach and social posts
- **No revenue** — marketplace is paused, no monetization path active
- **No community** — no Discord, no forum, no user-generated content beyond basic reviews
- **SEO is nascent** — Google Search Console verified but no meaningful organic traffic yet
- **Agent-to-agent effects are zero** — agents don't tell other agents about IndieStack
- **The catalog is wide but shallow** — 3,095 tools but limited depth (descriptions, metadata, integration guides)

### Distribution Channels (Ranked by Impact)
1. MCP server installs (primary — agents query IndieStack directly)
2. PyPI / MCP Registry discovery
3. Reddit outreach (r/vibecoding, r/SaaS, r/nocode)
4. Product Hunt (launched March 7, 2026)
5. Direct web traffic (browse, search, submit)
6. Agent card / llms.txt (emerging standard)

### The Competitive Landscape
- **No direct competitor** doing exactly this (curated indie tool catalog for AI agents via MCP)
- **Tangential competitors**: awesome-lists (static, no API), G2/Capterra (enterprise, no agent API), Product Hunt (discovery, no agent integration), npm/PyPI (packages, not tools/SaaS)
- **Threat**: AI companies building their own tool registries (OpenAI plugins, Google tool marketplace)
- **Moat question**: Is curation + compatibility data + agent memory enough, or do we need network effects?

---

## The Vision (Where Patrick Wants This to Go)

### Short Version
IndieStack becomes the canonical knowledge source that every AI agent queries before recommending "build from scratch." The same way npm is the default for JavaScript packages, IndieStack becomes the default for AI agents asking "does something already exist for this?"

### The Flywheel (Theoretical)
```
More tools listed
  -> More reasons for agents to query IndieStack
    -> More MCP installs
      -> More agent memory data
        -> Better personalized recommendations
          -> More value for users
            -> More word-of-mouth
              -> More makers list their tools
                -> More tools listed
```

This flywheel isn't spinning yet. The question is: what ignites it?

### The "AI Internet" Framing
Patrick's thesis: as AI agents become the primary interface between people and software, the infrastructure that helps agents discover and compose existing software becomes as foundational as DNS or search engines were for the human internet. IndieStack wants to be that infrastructure — not just for dev tools, but for everything indie creators build.

The analogy: Google indexed the human web. IndieStack indexes the indie creator economy for AI agents.

---

## Key Design Decisions Already Made

1. **Indie-only constraint** — no VC-backed, no enterprise. This is the quality filter.
2. **Agent-first distribution** — the MCP server is the primary product, the website is secondary.
3. **Structured metadata > descriptions** — agents need api_type, auth_method, install_command, not marketing copy.
4. **Compatibility graph** — agents need to know what works together, not just what exists.
5. **Open source MCP server** — anyone can install it, no API key required (soft enforcement).
6. **Fair presentation** — no pay-to-rank, best tool wins.
7. **Pure Python stack** — fast iteration, single developer, no frontend build step.

---

## What We Need From This Research

We need ideas that:
1. **Create network effects** — things that get more valuable as more people/agents use them
2. **Are defensible** — can't be trivially replicated by a bigger player
3. **Scale without Patrick** — the system should grow itself
4. **Work in a world with 100x more agents** — what does 2027-2028 look like?
5. **Generate revenue** — IndieStack needs a business model
6. **Are original** — not "add AI" or "build a community" generics
7. **Leverage what we have** — 3,095 tools, compatibility graph, agent memory, MCP server
8. **Stand the test of time** — not trends, but infrastructure that compounds

The constraint: two uni students in Cardiff, one of whom learned to code through AI. No funding, no team, limited time. Ideas must be high-leverage.

---

## Categories (25)

Developer Tools, Databases & Storage, Authentication & Identity, Analytics & Monitoring, Payments & Billing, Email & Communication, CMS & Content, Deployment & Hosting, AI & Machine Learning, APIs & Integration, Design & UI, Security & Privacy, Testing & QA, Documentation, Scheduling & Automation, Search & Discovery, Media & Files, Collaboration, Networking & Protocols, Games & Entertainment, Learning & Education, Newsletters & Content, Creative Tools, Productivity & Utilities, CLI Tools

---

## Key Files for Reference

- `VISION.md` — full vision document
- `ROADMAP.md` — phased roadmap
- `ARCHITECTURE.md` — technical architecture
- `docs/plans/2026-03-12-agentic-package-manager.md` — the "agentic package manager" plan (implemented)
- `src/indiestack/mcp_server.py` — MCP server (15 tools, 3 resources, 5 prompts)
- `src/indiestack/indexer.py` — GitHub auto-indexer
- `src/indiestack/enricher.py` — README metadata enricher
- `src/indiestack/pair_generator.py` — compatibility pair generator
- `src/indiestack/db.py` — database layer (all queries, migrations, helpers)
- `src/indiestack/main.py` — FastAPI app, APIs, middleware

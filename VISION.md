# IndieStack Vision

> Updated 2026-03-15. The sharp version.

---

## What IndieStack Is

IndieStack is the discovery layer between AI coding agents and the developer tools they should already know about.

When a developer asks their AI agent to "add authentication" or "set up analytics," the agent has two options: generate hundreds of lines of custom code from stale training data, or recommend a proven, maintained tool that does it better. IndieStack makes sure agents pick option two.

We curate thousands of focused, lightweight developer tools — the kind built by small teams who care about one thing and do it well. Auth from Hanko. Payments from Polar. Analytics from Plausible. Each maintained by domain experts. Each invisible to AI agents unless something like IndieStack exists.

**IndieStack is an agent's package manager for the tools that don't show up in training data.**

---

## The Problem

AI coding agents are the primary interface for millions of developers. But they have a blind spot.

Training data is stale — tools launched after the cutoff don't exist. It's biased toward popularity — a tool with 12 GitHub stars is invisible, even if it's exactly what someone needs. And it has no quality signals — no maintenance status, no pricing, no compatibility data, no "this tool works well with that one."

So agents default to generating code from scratch. 80,000 tokens. Hours of work. Auth systems maintained by nobody. Analytics dashboards that break on deploy.

Meanwhile, thousands of focused tools already solve these problems. The agents just don't know they exist.

---

## How IndieStack Fixes It

An MCP server on PyPI (`pip install indiestack`) that plugs directly into Claude Code, Cursor, Windsurf, and any MCP-compatible agent.

**The old way**: Agent generates 800 lines of custom auth. Developer debugs it for hours. Nobody maintains it.

**The IndieStack way**: Agent queries IndieStack, finds Hanko, returns 12 lines of integration code. Maintained by security experts. Compatibility verified.

The difference: 80,000 tokens vs 5,000 tokens. Hours vs seconds. Unmaintained code vs expert-maintained tools.

### The MCP Server — 15 Capabilities

| Tool | What it does |
|------|-------------|
| `find_tools` | Search by keyword, category, source type |
| `get_tool_details` | Integration snippets, pricing, similar tools, assembly metadata |
| `compare_tools` | Side-by-side comparison |
| `build_stack` | "I need auth + payments + analytics" -> complete stack |
| `evaluate_build_vs_buy` | Should you build this or use an existing tool? |
| `analyze_dependencies` | Scan your package.json, find better alternatives |
| `get_recommendations` | Personalized based on your history |
| `scan_project` | Describe what you're building, get a full tool recommendation |
| `check_health` | Verify tools you've adopted are still maintained |
| `report_compatibility` | Report tool pairs that work well together |
| `publish_tool` | Submit a tool from inside your agent |

`build_stack` is the sleeper. It turns "build me a SaaS" from a 50,000-token generation into a 2,000-token assembly. `scan_project` goes further — describe what you're building and get a complete recommendation with compatibility notes.

---

## Why "Indie"

IndieStack curates tools built by independent developers and small teams. Not because "indie" is a marketing angle — because indie tools are genuinely better for most use cases.

**Focused**: A team of three building auth doesn't also build a CMS, a CDN, and a billing system. They build auth and they build it well.

**Lean**: No enterprise bloat. No 200MB SDK for a feature you could integrate in 10 lines.

**Maintained**: Small teams ship fast. Issues get fixed in days, not quarters. The maintainer answers your GitHub issue personally.

**Honest pricing**: No "call us for a quote." No 14-page enterprise agreements. Free tiers that actually work. Transparent pricing pages.

"Indie" is IndieStack's curation filter. It's how we decide what gets in. But the value to developers isn't "these are indie" — it's "these are the best tools for the job, and your AI agent now knows about them."

---

## For Developers

- **Save tokens and money** — recommending a tool vs generating code saves $0.30-0.50 per AI interaction
- **Better code** — Hanko's auth is maintained by security experts. AI-generated auth is maintained by nobody.
- **Save hours** — assembly vs generation
- **Discovery** — 3,100+ tools you've never heard of, any of which might be exactly what you need
- **Stack architecture in seconds** — complete recommendations with compatibility notes
- **Works across agents** — Claude Code, Cursor, Windsurf. Knowledge follows you.
- **Gets smarter** — agent memory learns your preferences over time

---

## For Tool Makers

- **AI-powered distribution** — recommended at the exact moment a developer needs what you built
- **Reach beyond your network** — 12 GitHub stars becomes visible to every developer using an AI agent
- **Stack bundling** — recommended alongside complementary tools automatically
- **Zero maintenance** — list once, get recommended forever. More MCP installs = more reach.
- **Fair presentation** — no pay-to-rank. Best tool for the job wins.
- **Your tool outlives your marketing** — gets recommended to developers you'll never meet, in contexts you never imagined

---

## Why Training Data Can't Solve This

**Now (2026):** ~10 major AI coding agents, 5-10M developers using them.

**In 2 years:** Every IDE has an agent. Every browser has an agent. AI recommendations become a distribution channel bigger than SEO.

Training data will never keep up:
- Months or years stale at any given moment
- Biased toward popular repos (the long tail is invisible)
- No quality signals — maintenance status, pricing, compatibility, health
- Can't track what's new or what's been abandoned

**A live, curated catalog with structured metadata beats static training data every time.** That's IndieStack's moat.

**First-mover advantage:** The catalog and compatibility data built now becomes the foundation when every agent queries a discovery layer by default.

---

## The Flywheel

```
More tools in the catalog
    -> More useful queries from AI agents
        -> More developers install the MCP server
            -> More usage data and compatibility signals
                -> Better, smarter recommendations
                    -> More developers trust IndieStack
                        -> More makers list their tools
                            -> More tools in the catalog
```

---

## Roadmap

**Now (March 2026):** 3,100 tools, 25 categories, MCP server v1.7 on PyPI, agent memory, personalized recommendations, 1,279 compatibility pairs, per-tool Agent Cards, assembly metadata, quality gates, health monitoring, 3-tier API rate limiting, Pro subscription, command hub for team coordination.

**Near term:** Integration recipes, daily citation digests for makers, GitHub Action dependency auditor, MCP marketplace listings, concierge outreach to top makers.

**Medium term:** Agents assemble complete applications from stacks. Verified compatibility from real usage data. Agent-to-agent discovery. Revenue from Pro tier and data products.

**Long term:** The default discovery layer for AI coding agents. Every new agent connects to IndieStack. "AI recommendation" becomes a primary distribution channel. The flywheel compounds.

---

## What IndieStack Is Not

- Not a general-purpose directory (developer tools, not everything)
- Not an app store (we don't host or distribute software)
- Not a review site (we curate and categorize, agents recommend)
- Not pay-to-rank (fair presentation, best tool for the job wins)
- Not competing with G2 or Capterra (they serve enterprise procurement, we serve AI agents)

---

*Built by Pat and Ed. Two students in Cardiff who see where this is going.*

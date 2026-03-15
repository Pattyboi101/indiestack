# IndieStack — MCP Server + CLI

The open-source supply chain for AI agents. 3,000+ indie creations with structured assembly metadata across 25 categories — dev tools, games, utilities, newsletters, creative tools, learning apps, and more.

<!-- mcp-name: io.github.Pattyboi101/indiestack -->

## Quick Start

### MCP Server (for AI coding agents)

```bash
# Option 1: uvx (zero install — runs directly)
claude mcp add indiestack -- uvx --from indiestack indiestack-mcp

# Option 2: pipx (recommended for persistent install)
pipx install indiestack
claude mcp add indiestack -- indiestack-mcp

# Option 3: Cursor / Windsurf
# Add to your MCP config:
# {"command": "uvx", "args": ["--from", "indiestack", "indiestack-mcp"]}
```

### CLI (for your terminal)

```bash
pip install indiestack

indiestack search "analytics"
indiestack details simple-analytics
indiestack stack "auth, payments, email"
indiestack categories
```

Both tools ship in the same package. Your AI searches what exists before building from scratch.

## What it does

Your AI spends thousands of tokens rebuilding auth, payments, and analytics from scratch — things indie creators already built. Meanwhile, those creations sit on GitHub with 12 stars, invisible to the AI agents that could be recommending them.

IndieStack fixes both sides. Install the MCP server and your AI searches 3,000+ indie creations with structured assembly metadata before writing boilerplate. Tools include API types, auth methods, SDK packages, install commands, env vars, and framework compatibility — everything an agent needs to assemble proven building blocks instead of generating from scratch.

### Tools (19)

| Tool | What it does |
|------|-------------|
| `find_tools` | Search 3,000+ creations by keyword, category, or source type |
| `get_tool_details` | Full details with assembly metadata, integration snippets, and companions |
| `scan_project` | Analyze a project description + tech stack → get a complete indie stack recommendation |
| `report_compatibility` | Report that two tools work well together — builds the compatibility graph |
| `check_health` | GitHub health audit — maintenance grade, last commit, stars, alternatives for stale tools |
| `list_categories` | Browse all 25 categories — dev tools to games to newsletters |
| `compare_tools` | Side-by-side comparison of any two creations |
| `build_stack` | Assemble a complete indie stack from building blocks |
| `publish_tool` | Submit your creation so other agents can recommend it |
| `browse_new_tools` | Recently added creations with pagination |
| `list_tags` | All tags sorted by popularity |
| `list_stacks` | Curated stacks for common use cases |
| `analyze_dependencies` | Paste package.json/requirements.txt, get indie replacements |
| `evaluate_build_vs_buy` | Financial breakdown: build from scratch vs use what exists |
| `get_recommendations` | Personalized suggestions based on your search history |

### Resources (3)

| Resource | What it provides |
|----------|-----------------|
| `indiestack://categories` | All 25 categories with slugs for filtering |
| `indiestack://trending` | Top 10 trending creations this week |
| `indiestack://tools-index` | Complete index for prompt caching — include once, reference forever |

### Prompts (5)

| Prompt | When to use |
|--------|-------------|
| `before-you-build` | Check IndieStack before building common functionality |
| `find-alternatives` | Find indie alternatives to mainstream SaaS products |
| `save-tokens` | Audit your project for token-saving opportunities |
| `architect-feature` | Plan a feature using existing indie building blocks |
| `discover-indie` | Explore what indie creators have built beyond dev tools |

## What's new in v1.7.0

- **Trust tiers** — Every tool now shows a trust tier in MCP responses: `verified` (20+ outcome reports, 70%+ success), `tested` (5+ reports), or `new`. Agents can make informed decisions about tool reliability.
- **Agent cards** — Machine-readable JSON cards at `/cards/{slug}.json` with full assembly metadata, health status, and success rates. Index at `/cards/index.json`. No auth required.
- **Citation milestones** — Makers get notified when their tools cross citation thresholds (10, 25, 50, 100, 250, 500, 1000). Email alerts for significant milestones.
- **Trust badges** — Tool cards in search results show visual trust indicators based on outcome data.

## What was new in v1.6.0

- **Outcome intelligence** — Tools now show agent success rates: "82% success rate from 14 agent reports." Report outcomes with `report_outcome(slug, success)` — no API key or special scope needed.
- **Cross-agent intelligence** — Every outcome report improves recommendations for all agents across all platforms. IndieStack is becoming the neutral intelligence layer for tool discovery.
- **Frictionless reporting** — Outcome reporting works without an API key, with any scope, and with zero configuration. Just call `report_outcome()` after integrating a tool.
- **Implicit signals** — IndieStack now infers adoption and rejection from agent search patterns, building quality signals passively.

## What was new in v1.5.0

- **Agent-native actions** — `recommend()`, `shortlist()`, `report_outcome()`, `confirm_integration()` — agents can now report what they recommend and whether it worked.
- **Scoped API keys** — Read or read+write scopes for fine-grained agent permissions.

## What was new in v1.4.0

- **CLI tool** — `pip install indiestack` now gives you `indiestack` CLI alongside the MCP server. Search, browse, build stacks, and pipe JSON output — all from your terminal.
- **Pro API enrichment** — Pro API keys get richer responses: citation counts, compatible tool pairs, category percentile, and demand context.
- **3-tier rate limiting** — 15/day without a key, 50/day with a free key, 1,000/day with Pro.
- **Search boost for Pro makers** — Pro subscribers' tools rank slightly higher in search results.
- **`maker_is_pro` badge** — Tool cards now show a Pro badge when the maker has an active subscription.

## What was new in v1.3.0

- **3,000+ tools** — Catalog grew from 830 to 3,000+ via automated GitHub discovery across 37 search queries. Every category now has deep coverage.
- **500+ compatibility pairs** — Auto-generated from shared framework data. Tools tested with the same frameworks are paired so agents know what works together.
- **README-inferred metadata** — Install commands, env vars, SDK packages, and framework compatibility auto-extracted from GitHub READMEs for 700+ tools.
- **Smarter favicons** — "Works Well With" pills now show actual favicons from tool URLs.

## What was new in v1.2.0

- **Agentic Package Manager** — Structured assembly metadata: API type, auth method, SDK packages, install commands, env vars, and framework compatibility.
- **`scan_project()` tool** — Describe what you're building + your tech stack, get a complete indie stack recommendation.
- **`report_compatibility()` tool** — Agents report successful tool pairings, building a verified compatibility graph.
- **`check_health()` tool** — GitHub-powered health audits with maintenance grades and alternatives for stale tools.

## What was new in v1.1.0

- **Beyond dev tools** — IndieStack now covers everything indie-built: games, utilities, newsletters, creative tools, learning apps.
- **Broader search defaults** — `find_tools()` now defaults to `source_type='all'`.
- **New `discover-indie` prompt** — Explore beyond developer categories.
- **Smarter market gap messages** — Agents tell users they could build missing tools and get instant AI distribution.

## Links

- [IndieStack](https://indiestack.ai)
- [Explore Creations](https://indiestack.ai/explore)
- [Submit Your Creation](https://indiestack.ai/submit)
- [What is IndieStack?](https://indiestack.ai/what-is-indiestack)

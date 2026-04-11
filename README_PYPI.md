# IndieStack — MCP Server + CLI

Before your AI writes auth, payments, or email code from scratch — search 8,000+ curated developer tools with verified compatibility data and migration intelligence from 4,500+ repos. 10,000+ installs. Unlike a web search, you get install commands, health scores, and what tools actually work together in production.

<!-- mcp-name: io.github.Pattyboi101/indiestack -->

## Quick Install

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "indiestack": {
      "command": "uvx",
      "args": ["--from", "indiestack", "indiestack-mcp"]
    }
  }
}
```

Config file location: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)

### Cursor / Windsurf / Other MCP Clients

```json
{
  "indiestack": {
    "command": "uvx",
    "args": ["--from", "indiestack", "indiestack-mcp"]
  }
}
```

### Claude Code (CLI)

```bash
claude mcp add indiestack -- uvx --from indiestack indiestack-mcp
```

### CLI (terminal)

```bash
pip install indiestack

indiestack search "analytics"
indiestack details simple-analytics
indiestack stack "auth, payments, email"
indiestack categories
```

Both the MCP server and CLI ship in the same package. No API key required.

## What it does

Your AI spends thousands of tokens rebuilding auth, payments, and analytics from scratch — things independent developers already built and maintain. Meanwhile, those tools sit on GitHub with 12 stars, invisible to the AI agents that could be recommending them.

IndieStack fixes both sides. Install the MCP server and your AI searches 8,000+ developer tools with structured assembly metadata before writing boilerplate. Tools include API types, auth methods, SDK packages, install commands, env vars, and framework compatibility — everything an agent needs to assemble proven building blocks instead of generating from scratch.

"Indie" is the curation filter — tools built by independent developers and small teams. Focused, lean, maintained, honest pricing.

### Tools (24)

| Tool | What it does |
|------|-------------|
| `find_tools` | Search 8,000+ developer tools with 11 filters: price, health, stars, success rate, language, tags, compatibility |
| `get_tool_details` | Integration code, pricing, API specs, and compatibility data |
| `find_compatible` | Find tools compatible with a given tool — grouped by category, with verified stacks and conflict warnings |
| `compare_tools` | Side-by-side comparison of any two tools |
| `build_stack` | Turn a 50,000-token generation into a 2,000-token assembly |
| `scan_project` | Analyze a project description + tech stack, get a complete tool recommendation |
| `analyze_dependencies` | Scan package.json/requirements.txt for better alternatives and health score |
| `evaluate_build_vs_buy` | Financial breakdown: build from scratch vs use what exists |
| `check_health` | GitHub health audit — maintenance grade, last commit, stars, alternatives for stale tools |
| `get_migration_data` | Real migration momentum for any package — how many repos are adopting vs leaving, and what they're switching to/from |
| `get_market_gaps` | Top unmet needs — what developers search for but can't find. Useful for tool makers deciding what to build. |
| `get_recommendations` | Personalized suggestions based on your search history |
| `list_categories` | Browse all 35+ categories with tool counts |
| `list_stacks` | Curated stacks for common use cases |
| `list_tags` | All tags sorted by popularity |
| `browse_new_tools` | Recently added tools with pagination |
| `publish_tool` | Submit a developer tool so other agents can recommend it |
| `report_outcome` | Report success/failure after integrating a tool — feeds cross-agent compatibility data. No API key needed. |
| `report_compatibility` | Report that two tools work well together — builds the compatibility graph |
| `confirm_integration` | Record a verified integration with notes — strengthens compatibility signals |
| `recommend` | Record that you recommended a tool — powers Maker Pro citation analytics |
| `shortlist` | Record which tools you considered — demand signal even for unchosen tools |
| `check_compatibility` | Check whether a set of tools are compatible with each other |
| `set_api_key` | Activate an IndieStack API key for higher rate limits and Pro analytics |

### Resources (3)

| Resource | What it provides |
|----------|-----------------|
| `indiestack://categories` | All 35+ categories with slugs for filtering |
| `indiestack://trending` | Top 10 trending developer tools this week |
| `indiestack://tools-index` | Complete index for prompt caching — include once, reference forever |

### Prompts (5)

| Prompt | When to use |
|--------|-------------|
| `before-you-build` | Check IndieStack before building common functionality |
| `find-alternatives` | Find indie alternatives to mainstream SaaS products |
| `save-tokens` | Audit your project for token-saving opportunities |
| `architect-feature` | Plan a feature using existing indie building blocks |
| `discover-indie` | Explore what indie developers have built |

## What's new in v1.16

- **Stack compatibility checker** — New `check_compatibility(tools)` tool. Pass 2-8 tool slugs and get a compatibility matrix: which pairs are agent-verified, which are unknown, which conflict. Built for always-on agents doing continuous stack auditing without user prompts.
- **24 MCP tools total** — Up from 23.

## What's new in v1.15

- **Migration intelligence via MCP** — New `get_migration_data()` tool. Query real GitHub migration signals for any package: how many repos moved to it, what they moved from, and momentum trend. First time this data moat is exposed via MCP.
- **Description accuracy** — Tool count corrected to "8,000+" throughout. PyPI and Registry metadata updated.

## What's new in v1.13

- **GitHub stars in results** — Search results and tool details now show GitHub star counts. Filter by `min_stars` to surface popular tools instantly.
- **Smarter category aliases** — Searching "cron", "oauth", "smtp", or "uptime" now correctly maps to Scheduling, Authentication, Email, and Monitoring categories.
- **Better alternative exclusions** — "[tool] alternatives" queries now exclude wrapper packages (e.g. dj-stripe, laravel-stripe-webhooks) as well as the tool itself.

## What's new in v1.12

- **Market gaps** — New `get_market_gaps()` tool exposes zero-result queries ranked by search volume. Agents and makers can see what tools are missing from the ecosystem. API: `/api/gaps`.
- **Trust-weighted search** — Tools with higher agent success rates now rank higher in search results. Real outcome data influences sort order, not just star count.
- **Agent success badges** — Search results and explore cards now show agent success rate badges ("93% agent success") when outcome data is available.

## What's new in v1.11

- **Migration intelligence** — Tool details now include real migration data from 5,000+ GitHub repos. "jest → vitest: 27 repos", "webpack → vite: 13 repos". Agents can recommend tools backed by what developers actually switch to.
- **Verified combos** — 60,000+ verified package combinations from production repos. Know what actually works together, not what docs say works together.
- **Unlimited searches** — All rate limits removed. Free tier, Pro tier, no limits. Every query is valuable data.
- **Better search relevance** — Category-aware scoring. Searching "auth" returns auth tools, not Airflow.
- **2,100+ install commands** — 26% of tools now have `install_command` populated. Agents can show `npm install X` immediately.

## What was new in v1.9-1.10

- **Smarter ranking** — Quality score + GitHub stars ranking.
- **Tech stack filtering** — `scan_project` filters by framework compatibility.
- **Super filters** — 11 optional filters on `find_tools`: `compatible_with`, `price`, `min_success_rate`, `has_api`, `language`, `tags`, `exclude`, `health`, `min_stars`, and `sort`.
- **Compatibility graph** — `find_compatible` returns tools that work together with conflict warnings.
- **Agent outcome tracking** — `report_outcome` with `used_with` and `incompatible_with` feeds the compatibility graph.

## What was new in v1.7.0

- **Trust tiers** — Every tool now shows a trust tier: `verified` (20+ outcome reports, 70%+ success), `tested` (5+ reports), or `new`. Agents can make informed decisions about tool reliability.
- **Agent cards** — Machine-readable JSON cards at `/cards/{slug}.json` with full assembly metadata, health status, and success rates. Index at `/cards/index.json`. No auth required.
- **Citation milestones** — Makers get notified when their tools cross citation thresholds (10, 25, 50, 100, 250, 500, 1000).
- **Trust badges** — Tool cards in search results show visual trust indicators based on outcome data.

## What was new in v1.6.0

- **Outcome intelligence** — Tools now show agent success rates: "82% success rate from 14 agent reports." Report outcomes with `report_outcome(slug, success)` — no API key needed.
- **Cross-agent intelligence** — Every outcome report improves recommendations for all agents across all platforms.
- **Frictionless reporting** — Outcome reporting works without an API key, with any scope, and with zero configuration.

## What was new in v1.5.0

- **Agent-native actions** — `recommend()`, `shortlist()`, `report_outcome()`, `confirm_integration()` — agents can now report what they recommend and whether it worked.
- **Scoped API keys** — Read or read+write scopes for fine-grained agent permissions.

## What was new in v1.4.0

- **CLI tool** — `pip install indiestack` now gives you `indiestack` CLI alongside the MCP server.
- **Pro API enrichment** — Pro API keys get richer responses: citation counts, compatible tool pairs, category percentile, and demand context.
- **3-tier rate limiting** — 15/day without a key, 50/day with a free key, 1,000/day with Pro.

## What was new in v1.3.0

- **8,000+ tools** — Catalog grew from 830 to 8,000+ via automated GitHub discovery across 37 search queries. Every category now has deep coverage.
- **500+ compatibility pairs** — Auto-generated from shared framework data.
- **README-inferred metadata** — Install commands, env vars, SDK packages, and framework compatibility auto-extracted from GitHub READMEs for 700+ tools.

## Links

- [IndieStack](https://indiestack.ai)
- [Explore Tools](https://indiestack.ai/explore)
- [Submit Your Tool](https://indiestack.ai/submit)
- [What is IndieStack?](https://indiestack.ai/what-is-indiestack)

# IndieStack — Context for Defensibility & Outcome Data Moat Research

> This document provides complete context for researching how IndieStack builds a defensible moat against raw GitHub/npm/PyPI search by AI agents.

---

## What IndieStack Is

IndieStack is the open-source supply chain for agentic workflows — 3,000+ indie creations across 25 categories. AI agents query IndieStack via MCP server before recommending "build from scratch." The catalog includes dev tools, games, utilities, newsletters, creative tools, learning apps — anything indie-built. Built by two university students in Cardiff using Claude Code. Live since early 2026, launched on Product Hunt March 7.

## Current Data Volumes (March 14, 2026)

| Table | Rows | What it is |
|-------|------|-----------|
| tools | ~3,100 | Curated indie creations |
| categories | 25 | Tool taxonomy |
| compatibility_pairs | 1,279 | Verified tool-tool compatibility |
| search_logs | ~1,200 | Every search query (web + MCP) |
| agent_citations | ~200 | When an agent views/recommends a tool |
| agent_actions | ~10 | Recommend/shortlist/outcome/integration (new, barely used) |
| api_keys | ~15 | Developer API keys |
| api_usage_logs | ~500 | API call log |
| users | ~80 | Registered users |
| subscribers | ~120 | Email subscribers |

## How Agents Currently Interact with IndieStack

### MCP Server (Primary Channel)
- 19 tools available: find_tools, get_tool_details, scan_project, build_stack, compare_tools, report_compatibility, check_health, list_categories, analyze_dependencies, evaluate_build_vs_buy, get_recommendations, browse_new_tools, list_tags, list_stacks, publish_tool, recommend, shortlist, report_outcome, confirm_integration
- Installed via `uvx --from indiestack indiestack-mcp`
- Published on official MCP Registry
- Returns structured JSON with assembly metadata (API type, auth method, SDK packages, env vars, compatible pairs)

### API (Secondary Channel)
- REST API with 3-tier rate limiting: keyless (15/day), free key (50/day), pro key (1,000/day)
- Agent Card at `/cards/{slug}.json` for each tool — machine-readable metadata

### Data We Track Per Agent Interaction
1. **search_logs**: query text, source (web/mcp), result_count, top_result_slug, api_key_id, timestamp
2. **agent_citations**: tool_id, agent_name, timestamp — logged when agent views tool details
3. **mcp_view_count**: per-tool counter incremented on detail lookups
4. **agent_actions** (v1.5.0, barely used):
   - `recommend`: agent recommended tool_slug for a query_context
   - `shortlist`: agent shortlisted tool_slug
   - `report_outcome`: success/fail after integration attempt
   - `confirm_integration`: tool_a + tool_b confirmed working together
   - `submit_tool`: agent submitted a new tool

### What We DON'T Track (but could)
- Whether the user actually adopted the recommended tool
- Success/failure rate of integrations per tool
- Which tool combinations agents recommend together most often
- Whether agents return for the same tool (repeat recommendation signal)
- Cross-platform data (which agent platform made the recommendation)
- Time-to-integration (how quickly after recommendation did the user adopt)

## Current Enrichment & Quality Pipeline

### Auto-Indexer
- `scripts/index_awesome_lists.py` — scrapes awesome-lists on GitHub, extracts tools
- Runs periodically, submits to approval queue

### Auto-Enricher
- `src/indiestack/enricher.py` — fetches GitHub README, extracts install commands, descriptions
- Section-aware parsing (just fixed today — was grabbing dev dependencies like `brew install fswatch`)
- Extracts: install commands, description, tags from GitHub topics

### Dead Tool Detector
- `scripts/check_tool_freshness.py` — checks if tools are still maintained
- Stale badges shown on tool pages
- Admin Stale Tools tab for cleanup

### Assembly Metadata (Agent Cards)
Each tool has structured metadata at `/cards/{slug}.json`:
- API type (REST, GraphQL, SDK, CLI)
- Auth method (API key, OAuth, none)
- SDK packages (npm, pip, cargo, etc.)
- Required env vars
- Compatible tools (verified pairs)

## The Existential Threat We're Researching

### The Problem
AI agents are getting smarter. Context windows are growing (200k → 1M → 10M tokens). An agent could:
1. Search GitHub API for repos matching a query
2. Read the top 10 READMEs
3. Evaluate stars, recent commits, issue activity
4. Extract install commands and metadata
5. Make a recommendation

This bypasses IndieStack entirely. Today it costs 30-120k tokens per search — expensive. In 12-18 months, it might cost 3-12k tokens — negligible.

### What IndieStack Offers Today That Raw Search Doesn't
1. **Pre-curated catalog**: 3,100 tools already vetted and categorized
2. **Assembly metadata**: API type, auth method, SDKs, env vars — not in most READMEs
3. **Compatibility pairs**: 1,279 verified "works with" relationships
4. **Health monitoring**: Dead Tool Detector catches abandoned projects
5. **Token efficiency**: Structured JSON response in ~500 tokens vs. 30k+ for raw search
6. **Stack building**: "I need auth + payments + analytics" → complete recommendation
7. **Cross-category**: Not just npm or just PyPI — everything indie

### Why This Advantage Is Temporary
- Token costs are dropping ~50% every 6 months
- Agent platforms (Cursor, Copilot, Windsurf) could build their own indexes
- GitHub's own API is getting richer (search, topics, README parsing)
- Microsoft owns GitHub AND npm — could build this in a weekend with better data

### The Hypothesis: Outcome Data as the Moat
Static curation loses to smarter agents. But outcome data — "this tool was recommended 500 times, 73% success rate, pairs well with Supabase" — can only exist in a system that tracks what happens after a recommendation.

The agent_actions table (v1.5.0) has the primitives:
- `recommend` → agent recommended this tool
- `shortlist` → agent shortlisted it
- `report_outcome` → integration succeeded/failed
- `confirm_integration` → tool pair confirmed working

But it's barely used (~10 rows). The cold start problem is real.

## What Previous Research Covered (Don't Repeat)

### March 12: General Gemini Research
- Broad strategic positioning, competitor analysis, growth tactics
- Covered: SEO, community building, content marketing, pricing psychology

### March 13: Demand Signals Pro
- Deep dive on making the demand dashboard worth paying for
- Covered: dashboard UX, pricing, data presentation, comparable products
- Output: 12 concrete upgrades for the demand signals dashboard

### March 13: Pro Subscription Architecture
- Full subscription tier design across makers, developers, agents
- Covered: tier definitions, unlock maps, pricing rationale, API monetisation, migration path
- Output: subscription architecture blueprint

### What This Research Should NOT Repeat
- Generic "build a community" advice
- Dashboard UX patterns (covered in demand signals research)
- Subscription pricing mechanics (covered in pro architecture research)
- Basic competitor listing (covered in general research)

## Schema Details for Agent Interaction Tables

```sql
CREATE TABLE IF NOT EXISTS search_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'web',  -- 'web' or 'mcp'
    result_count INTEGER NOT NULL DEFAULT 0,
    top_result_slug TEXT,
    top_result_name TEXT,
    api_key_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_citations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_id INTEGER NOT NULL REFERENCES tools(id),
    agent_name TEXT NOT NULL DEFAULT 'unknown',
    context TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER REFERENCES api_keys(id),
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL CHECK(action IN ('recommend','shortlist','report_outcome','confirm_integration','submit_tool')),
    tool_slug TEXT NOT NULL,
    tool_b_slug TEXT,
    success INTEGER,
    notes TEXT,
    query_context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- tools table includes:
-- mcp_view_count INTEGER NOT NULL DEFAULT 0  (incremented on agent detail lookups)
```

## Key Questions for Gemini

1. What platforms have successfully built moats from outcome/feedback data rather than catalog data? How did they bootstrap the cold start?
2. What implicit signals can be captured without agents explicitly reporting (e.g., search → detail view → no further search = implicit adoption)?
3. How do recommendation engines at early stages (<1000 data points) build credible quality signals?
4. What's the architecture for a cross-platform intelligence layer that multiple competing agent platforms would feed into?
5. Are there real-world examples of "neutral data utilities" that competitors trust enough to share data with?
6. How do open-source package registries (npm, PyPI, crates.io) handle quality signals, and what can IndieStack learn from them?
7. What network effects can IndieStack create that make each additional data point more valuable to all participants?
8. How should IndieStack's data collection evolve to capture outcome data without adding friction to the agent experience?

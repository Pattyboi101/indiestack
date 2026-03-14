# IndieStack — Context for Autonomous Agent Strategy Research

> This document provides complete context for researching how IndieStack should position itself for autonomous agents — not just AI coding assistants with human oversight, but fully autonomous systems that discover, evaluate, and integrate tools without human intervention.

---

## What IndieStack Is

IndieStack is the open-source supply chain for agentic workflows — 3,100+ indie creations across 25 categories. AI agents query IndieStack via MCP server before recommending "build from scratch." The catalog includes dev tools, games, utilities, newsletters, creative tools, learning apps — anything indie-built. Built by two university students in Cardiff using Claude Code. Live since early 2026, launched on Product Hunt March 7.

## Current Data Volumes (March 14, 2026)

| Table | Rows | What it is |
|-------|------|------------|
| tools | 3,100 | Curated indie creations |
| makers | 645 | Maker profiles (most auto-created during indexing) |
| users | 52 | Registered accounts |
| subscriptions | 0 | Pro subscribers |
| categories | 25 | Tool taxonomy |
| tool_pairs | 1,279 | Verified tool-tool compatibility |
| search_logs | 1,113 | Every search query (web + MCP) |
| agent_citations | 184 | When an agent views/recommends a tool |
| agent_actions | ~15 | Recommend/shortlist/outcome/integration actions |
| api_keys | 3 | Developer API keys issued |
| developer_profiles | 0 | Agent memory profiles (table exists, not populated) |
| outbound_clicks | 26,326 | Clicks from IndieStack to tool URLs |
| page_views | 193,623 | Total page views |
| tool_views | 29,539 | Individual tool page views |

## Current Agent Interaction Model

### MCP Server (19 Endpoints)

IndieStack's MCP server is the primary distribution channel (67% of searches). Agents connect via:
```
claude mcp add indiestack -- uvx --from indiestack indiestack-mcp
```

**Discovery endpoints:**
- `find_tools(query, category)` — keyword/category search, returns 10 results with health tags
- `get_tool_details(slug)` — full details including success rate, assembly metadata, agent instructions
- `compare_tools(slug_a, slug_b)` — side-by-side comparison
- `build_stack(needs, budget)` — "I need auth+payments+analytics" → complete stack
- `scan_project(description, tech_stack)` — analyze project → full indie stack recommendation
- `analyze_dependencies(manifest)` — parse package.json/requirements.txt → indie replacements
- `check_health(slugs)` — maintenance status check
- `evaluate_build_vs_buy(slug, hours, rate)` — financial comparison

**Feedback endpoints (the data flywheel):**
- `report_outcome(slug, success, notes)` — "Did this work?" **No API key needed.** Rate: 10/day/IP.
- `report_compatibility(tool_a, tool_b)` — "These work together." Updates verified pairs.
- `recommend(slug, context)` — Record recommendation (requires API key)
- `shortlist(slugs, context)` — Record tools evaluated (requires API key)

**Submit endpoint:**
- `publish_tool(name, url, tagline, ...)` — Submit new creation

### Agent Cards (Machine-Readable, A2A-Compatible)

Every tool has a structured JSON endpoint at `/cards/{slug}.json`:
```json
{
  "name": "Hanko",
  "capabilities": {
    "api_type": "REST",
    "auth_method": "API Key",
    "install_command": "npm install @hanko/elements",
    "sdk_packages": ["@hanko/elements"],
    "env_vars": ["HANKO_API_URL"],
    "agent_instructions": "Use passkey-first auth. Don't fall back to passwords..."
  },
  "health": {
    "status": "Active",
    "github_stars": 1200,
    "github_last_commit": "2026-03-10"
  },
  "trust": {
    "is_verified": true,
    "upvote_count": 8,
    "review_count": 2,
    "avg_rating": 4.5
  },
  "compatibility": [
    {"slug": "stripe", "success_count": 12}
  ]
}
```

An index at `/cards/index.json` lists all 828+ tools with metadata.

### REST API for Agent Reporting

- `POST /api/agent/outcome` — Keyless, 10/day/IP, deduplication per tool/day
- `POST /api/agent/recommend` — Requires API key (read scope), 50/day
- `POST /api/agent/shortlist` — Requires API key, max 10 slugs/call
- `POST /api/agent/integration` — Requires API key (write scope), updates tool_pairs

### Agent Client Tracking (Planned)

Migration exists to add `agent_client` column to `search_logs` — will track which AI agent platform (Claude, Cursor, Windsurf, Copilot) made each search. Not yet deployed. This enables cross-platform analytics.

## What We Just Shipped: v1.6.0 + Maker Retention (Crack #2 Resolution)

### v1.6.0 Outcome Intelligence
- **Explicit outcomes**: Agents call `report_outcome(slug, success)` after integration. Keyless, no friction.
- **Implicit signals**: Inferred from search patterns (search → detail → no further search = adoption, weight 0.6)
- **Success rates displayed**: "82% success rate from 14 agent reports" on tool pages and in MCP responses
- **Confidence levels**: low (<5 signals), medium (5-20), high (>20)

### Crack #2: Maker Retention Features
- **Agent Instructions**: Maker-authored text injected into MCP responses and Agent Cards. Tells agents exactly how to implement the tool correctly.
- **Listing Quality Score**: Composite metric (metadata 40%, success rate 35%, freshness 25%) with progress bar and tips
- **Success Rate on Dashboard**: Aggregate + per-tool success rates visible to makers

## The Autonomous Agent Question

### Current Agent Users
IndieStack's current agents are **human-supervised**: a developer asks Claude/Cursor to "find an auth solution," the agent queries IndieStack, presents options, the human decides. The agent is a search intermediary.

### Fully Autonomous Agents (The Future)
Devin-like systems that:
1. Receive a high-level goal ("build a SaaS MVP")
2. Autonomously decide what tools to use
3. Discover, evaluate, and integrate tools without human approval
4. Report back when done

These agents don't browse websites. They need:
- Structured, machine-readable data (Agent Cards ✅)
- Reliability signals (success rates ✅)
- Compatibility data (tool pairs ✅, 1,279 verified)
- Security assurance (NOT YET — no supply chain verification)
- Assembly instructions (Agent Instructions ✅)

### The Core Problem
**Autonomous agents want to FIND tools, not PROMOTE them.** They have zero incentive to list. Their value exchange with IndieStack is purely consumption:
- Agent gets: structured discovery, reliability signals, compatibility data
- IndieStack gets: search logs, citations, outcome reports (side-effect data)

### What IndieStack Offers Over Raw Search

| Signal | GitHub/npm/PyPI | IndieStack |
|--------|----------------|------------|
| Assembly metadata | Buried in README | Structured JSON |
| Success rate | Nothing | Agent outcome data |
| Compatibility | Nothing | 1,279 verified pairs |
| Health classification | Partial | Active/Stale/Dead |
| Agent Instructions | Nothing | Maker-authored |
| Cross-platform data | Impossible | Planned |
| Token cost | ~30-120k per repo | ~500 per tool |

### The "Switzerland" Hypothesis
IndieStack is platform-neutral — works with Claude, Cursor, Windsurf, Copilot. No single platform has cross-platform outcome data. This could be the defensible moat. But it depends on:
1. Getting enough agents across enough platforms to report outcomes
2. The data being genuinely useful (not just vanity metrics)
3. Agent platforms not blocking or replacing this intermediary

## Existing Agent Memory Infrastructure

- `developer_profiles` table: schema created (interests, tech_stack, favorite_tools, search_count, personalization_enabled) — NOT yet populated
- `search_logs.agent_client` column: migration written — NOT yet deployed
- MCP server caches 200 items with TTL
- Circuit breaker: 3 consecutive failures → 60-second cooldown

## What Previous Research Covered (Don't Repeat)

### March 14: Maker Retention & Incentives (Crack #2)
- Cross-Agent Telemetry Platform positioning ("Google Search Console for AI")
- Agent Instructions, Listing Quality Score, success rate analytics
- Re-engagement strategies, free/Pro boundary for maker analytics
- **Don't repeat**: maker incentive mechanics, dashboard analytics design, gamification

### March 14: Defensibility & Outcome Data (Crack #1)
- How to transition from static curation to outcome-powered recommendations
- Implicit signal architecture (search → citation → silence patterns)
- Cold start playbook for outcome data
- **Don't repeat**: recommendation engine architecture, signal weighting, cold start mechanics

### March 13: Pro Subscription Architecture
- Tier definitions (free/pro maker, free/pro developer, agent tiers)
- Pricing rationale and unlock maps
- **Don't repeat**: tier structure, pricing mechanics

## The Revenue Constraint

IndieStack MUST make money. Current Pro subscription has 0 subscribers. For autonomous agents specifically, the revenue question is:
- Do agents pay? (API key tiers exist: free 50/day, pro 1000/day)
- Do agent PLATFORMS pay? (B2B model — "Cursor bundles IndieStack")
- Do tool makers pay for higher visibility to autonomous agents?
- Is there a "certification" revenue stream? ("IndieStack Verified Agent-Ready")

## Key Questions for Gemini

1. What does an autonomous agent's tool discovery workflow actually look like today? Map the full journey from "I need auth" to "auth is working." Where does a registry add the most value?

2. Is the "Switzerland" / cross-platform neutrality position defensible, or will agent platforms build their own tool registries and cut out intermediaries?

3. What minimum data volume makes cross-platform outcome data useful? We have 184 citations and 1,113 searches across 3,100 tools. Most tools have 0-1 data points. Are we 10x or 100x away from the data being meaningful?

4. How do you price a machine-to-machine API product? Traditional SaaS pricing (per seat) doesn't apply when the "user" is an agent. Per-query? Per-outcome? Per-integration?

5. Is "agent-as-maker" (autonomous agents listing tools they've built) a near-term reality or science fiction? What would need to be true for this to happen?

6. What security/trust layer should IndieStack build for autonomous agent tool discovery? Supply chain attacks via agent-recommended packages are a real risk. Is this an opportunity?

7. How do autonomous agent platforms (Devin, OpenHands, SWE-Agent) currently handle tool discovery? Do they have preferred registries? Is there a standard?

8. What's the "Stripe for agent tools" play? Making any tool "agent-ready" with proper metadata, structured APIs, and Agent Instructions — is this a service worth paying for?

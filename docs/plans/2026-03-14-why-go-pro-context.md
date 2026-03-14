# IndieStack — Context for "Why Go Pro" Conversion Research

> This document provides complete context for researching how IndieStack should convert its first paying Pro subscribers. It includes current data volumes, the Pro architecture, what's been tried, and what previous research produced.

---

## What IndieStack Is

IndieStack is the open-source supply chain for agentic workflows — a curated directory of 3,100+ indie creations across 25 categories (dev tools, games, utilities, newsletters, creative tools, learning apps, and more). The constraint is "indie-built," not "developer tool." AI agents query IndieStack via an MCP server with 19 tools to discover, compare, and assemble solutions from indie building blocks instead of generating code from scratch. Built by two university students in Cardiff using Claude Code. Live at indiestack.ai.

## Current Data Volumes (March 13, 2026)

| Table | Rows | Notes |
|-------|------|-------|
| tools | 3,100 | Approved indie creations |
| categories | 25 | Taxonomy |
| makers | 645 | Creator profiles (mostly auto-imported) |
| users | 52 | Registered accounts |
| subscriptions | 0 | **Zero Pro subscribers** |
| api_keys | 3 | All free tier |
| api_usage_logs | 2 | Almost no API usage |
| agent_citations | 184 | AI agents citing tools |
| search_logs | 1,113 | Web + MCP searches |
| page_views | 193,623 | Total page views |
| outbound_clicks | 26,326 | Clicks to external tool URLs |
| tool_views | 29,539 | Individual tool page views |
| tool_pairs | 1,279 | Compatibility pairs |
| upvotes | 60 | Community upvotes |
| wishlists | 1 | Bookmarked tools |
| reviews | 4 | User reviews |
| subscribers | 7 | Email newsletter subscribers |
| developer_profiles | 0 | Personalization profiles (unused) |
| sessions | 67 | Active login sessions |
| claim_requests | 12 | Makers claiming their tools |

## The Conversion Funnel Problem

```
193,623 page views
  → 52 registered users (0.03% registration rate)
    → 3 API keys created (5.8% of registered)
      → 0 Pro subscribers (0%)
```

The site has real traffic but almost nobody registers, and nobody who registers pays. The free tier is complete enough that registration adds almost nothing — you can search, browse, and use the MCP server without an account.

## Current Pro Tier ($19/month)

### What Pro Currently Includes
- **Find Market Gaps** — full demand signal dashboard with opportunity scores, trend sparklines, competition density, sortable table, CSV/JSON export (vs free: top 5 gaps with badges only)
- **See Who Recommends You** — agent citation breakdown by agent type (Claude, Cursor, etc.), 14-day sparkline trend (vs free: blurred/hidden)
- **Weekly AI Report** — citation stats emailed weekly
- **Pro Dashboard** — unified analytics view
- **1,000 API Queries/Day** — vs 50/day free (with key) or 15/day (without key)
- **Export Your Data** — JSON/CSV download of tools, analytics, citations
- **Search Boost** — tools rank higher in AI agent results (**BEING REMOVED** — contradicts curation integrity)

### Founding Member Tier ($99/year)
- All Pro features
- Permanent Founding Member badge
- Price locked forever
- Limited to 50 seats (0 claimed)
- 56% discount vs monthly

### Stripe Setup
- Pro: $19/month (price_1TAX7sKzUt3DIisgRThPByMj)
- Founder: $99/year (price_1TAX7sKzUt3DIisgPBLSMoLC)
- Product: prod_U8olNgYE9wxL24
- Webhook handles checkout.session.completed + customer.subscription.deleted
- Subscribe endpoint: POST /api/subscribe/pro

## The Redesigned Pro (Approved Design, Not Yet Built)

We've redesigned Pro around two audiences with the same plan:

### Maker Pro Features (new)
- **Listing Optimizer** — guided metadata completion, "how agents see your tool" MCP preview, completeness score
- **Competitor Alerts** — weekly digest when new tools listed in your category or competitor citation spikes
- **GitHub Action** — auto-sync listing on release tag
- **Slack/Discord Webhook** — citation alerts, weekly summary, competitor notifications
- **Embeddable Analytics Widget** — richer than badge, shows recommendation trend

### Developer Pro Features (new)
- **Stack Auditor** — paste package.json/requirements.txt/go.mod/Cargo.toml, get report: indie alternatives, unmaintained deps, missing categories. First audit free, ongoing monitoring requires Pro.
- **Private Recommendations** — weekly digest based on search history and developer profile
- **Integration Alerts** — stale bookmarked tools, new compatibility pairs
- **CI Audit Command** — `indiestack audit` CLI subcommand, exits non-zero on stale deps
- **Stack Lock File** — `.indiestack.json` for version-controlled stack alignment

### Key Principle
**Never sell visibility.** Search Boost is being removed. Replaced with Listing Optimizer — makers earn better ranking through richer metadata, not purchased placement. The curation signal is the moat.

## What We've Already Tried

### Demand Signals Pro ($15/month) — Failed
- Launched as standalone paid feature
- Dashboard showing search gaps, opportunity scores, trend data
- 0 subscribers
- Problem: the free tier (/gaps) showed enough data (top 5 gaps with badges) that nobody needed the full dashboard
- Folded into the broader "Pro Everywhere" subscription

### Pro Everywhere ($19/month) — Just Launched, 0 Subscribers
- Launched March 13, 2026 (1 day ago)
- Bundled all Pro features under one subscription
- Added Founding Member at $99/year
- Problem: features are "more of the same" — more API calls, more data depth. Nothing you can't live without.

### What Has NOT Been Tried
- Lower price points ($5-9/month)
- Free trials
- Product-led growth wedge (free first use, gate ongoing)
- MCP server upselling in API responses
- Segmented landing pages for maker vs developer audiences
- Direct outreach to existing users
- Community-unlock models
- Lifetime deals

## Previous Gemini Research Sessions

### 1. Pro Architecture Research (March 13)
- Explored tier definitions, unlock maps, API monetisation, consumer play timing
- Produced the "Pro Everywhere" architecture with $19/month pricing
- Key finding: single pro tier that unlocks across the platform (like GitHub Pro)
- Did NOT address: conversion mechanics, 0-to-1 playbook, pricing validation

### 2. Demand Signals Pro Research (March 13)
- Researched what makes data dashboards worth paying for
- Studied Exploding Topics, SparkToro, SimilarWeb, Google Trends
- Produced 12 concrete upgrades for the demand dashboard
- Key finding: "intelligence derived from data" is more valuable than "data access"
- Did NOT address: why nobody subscribed, conversion psychology, pricing at early stage

### 3. Quality Gates Research (March 14)
- Focused on protecting curation quality from vibecoded SaaS spam
- Not directly relevant to Pro conversion

### What This Research Should NOT Repeat
- Tier architecture design (already decided: one plan, two audiences)
- Feature list generation (already designed: see "Redesigned Pro" above)
- Dashboard UX patterns (already researched in Demand Signals session)
- General "how to monetise" advice (need 0-to-1 specifics)

## Key Schema (Relevant Tables)

```sql
CREATE TABLE subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    stripe_subscription_id TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL DEFAULT 'pro',
    status TEXT NOT NULL DEFAULT 'active',
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE api_keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(id),
    name TEXT NOT NULL DEFAULT 'Default',
    tier TEXT NOT NULL DEFAULT 'free' CHECK(tier IN ('free','pro')),
    is_active INTEGER NOT NULL DEFAULT 1,
    last_used_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE search_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'web',
    result_count INTEGER NOT NULL DEFAULT 0,
    top_result_slug TEXT,
    api_key_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE developer_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER NOT NULL UNIQUE REFERENCES api_keys(id),
    interests TEXT NOT NULL DEFAULT '{}',
    tech_stack TEXT NOT NULL DEFAULT '[]',
    favorite_tools TEXT NOT NULL DEFAULT '[]',
    search_count INTEGER NOT NULL DEFAULT 0,
    personalization_enabled INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## MCP Server

- 19 tools, 3 resources, 5 prompts
- ~2,100 token footprint per installation
- Key tools: find_tools, get_tool_details, compare_tools, build_stack, analyze_dependencies, scan_project, check_health
- Pro API keys get richer responses (citation_count_7d, compatible_with, demand_context)
- Currently no upsell messaging in API responses
- v1.5.0 on PyPI, installable via `uvx --from indiestack indiestack-mcp`

## Rate Limiting

| Tier | Daily Limit |
|------|------------|
| No API key | 15 queries |
| Free API key | 50 queries |
| Pro API key | 1,000 queries |

Nobody is hitting any of these limits. The 3 API keys have generated 2 total usage log entries.

## Distribution Channels

- MCP server on PyPI + official MCP Registry
- Product Hunt launch (March 7, 2026) — listing live
- Reddit (Ed handles, playbook in memory)
- SEO pages (/alternatives, /vs/, /gaps/{slug})
- GEO lead magnet (/geo — free llms.txt + Agent Card generator)
- Agent Cards per tool (/cards/{slug}.json)
- llms.txt and agent-card.json for AI discoverability

## Key Questions for This Research

1. How do you convert the first subscriber on a platform with 52 users and zero social proof? What's the psychology?
2. Is $19/month defensible at this stage, or should launch pricing be $9/month (or lower) to prioritise adoption over revenue?
3. Should the Stack Auditor's "first audit free" be the primary PLG wedge? If so, what's the exact conversion flow?
4. How aggressively should the MCP server upsell Pro in its responses? Is one line acceptable or does it poison the agent context?
5. Is the Founding Member scarcity play (50 seats) effective when there are 0 subscribers, or does it feel fake?
6. Should Pro include access to the founders (Discord/Slack channel)? Does personal access convert at early stage?
7. How do you frame data from 1,113 searches as valuable intelligence rather than a thin dataset?
8. What's the optimal teaser depth — how much Pro data should free users see before the gate?

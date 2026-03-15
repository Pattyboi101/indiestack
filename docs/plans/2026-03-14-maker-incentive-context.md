# IndieStack — Context for Maker Incentive & Retention Research

> This document provides complete context for researching how IndieStack drives maker retention and monetizes the supply side.

---

## What IndieStack Is

IndieStack is the open-source supply chain for agentic workflows — 3,100+ indie creations across 25 categories. AI agents query IndieStack via MCP server before recommending "build from scratch." The catalog includes dev tools, games, utilities, newsletters, creative tools, learning apps — anything indie-built. Built by two university students in Cardiff using Claude Code. Live since early 2026, launched on Product Hunt March 7.

## Current Data Volumes (March 14, 2026)

| Table | Rows | What it is |
|-------|------|-----------|
| tools | 3,100 | Curated indie creations |
| makers | 645 | Maker profiles (most auto-created during indexing) |
| users | 52 | Registered accounts |
| subscriptions | 0 | Pro subscribers (nobody has converted yet) |
| categories | 25 | Tool taxonomy |
| tool_pairs | 1,279 | Verified tool-tool compatibility |
| search_logs | 1,113 | Every search query (web + MCP) |
| agent_citations | 184 | When an agent views/recommends a tool |
| agent_actions | ~15 | Recommend/shortlist/outcome/integration actions |
| api_keys | 3 | Developer API keys issued |
| outbound_clicks | 26,326 | Clicks from IndieStack to tool URLs |
| page_views | 193,623 | Total page views |
| tool_views | 29,539 | Individual tool page views |
| reviews | 4 | User reviews |
| upvotes | 60 | Tool upvotes |
| milestones | 13 | Gamification milestones achieved |
| claim_requests | 12 | Makers requesting to claim their tool |
| wishlists | 1 | User wishlists |

## The Maker Engagement Problem

### How Tools Get Listed
- **~90% auto-indexed**: Scraped from GitHub awesome-lists by `scripts/index_awesome_lists.py`. These makers have no idea they're on IndieStack.
- **~10% self-submitted**: Makers find IndieStack and submit via the website or MCP `publish_tool()`. Most submit once and never return.
- **Claim flow exists**: Makers can claim auto-indexed tools via magic link sent to their GitHub email. 12 claim requests so far.

### Current Maker Dashboard (What Exists)

The dashboard at `/dashboard` shows registered makers:

**Stats visible today (free):**
- Tool count, total upvotes, total revenue (always $0), sales count
- Agent citations (30-day count)
- Citation percentile ("Top X% of all tools")
- AI Distribution Intelligence section:
  - Query intelligence: what search queries led agents to their tools
  - Agent breakdown: which AI agents are recommending them
  - Daily citation trend (30-day sparkline)
- Tool views (web), outbound clicks
- Launch readiness score
- Tokens saved estimate
- Milestones (gamification badges)
- Referral tracking

**What's NOT shown yet (could be):**
- Success rate from outcome reports (v1.6.0 data exists but not in dashboard)
- Competitive comparison ("your tool vs alternatives in your category")
- Demand signals ("what agents are searching for that you could build")
- Recommendation-to-click conversion rate
- Cross-agent platform breakdown with detail
- Trend direction (growing/declining recommendations)
- Alerts when success rate drops

### Current Maker Retention Stats (Honest Assessment)
- 52 registered users, unknown how many are active makers vs curious browsers
- 12 claim requests (makers who found their auto-indexed tool and wanted to own it)
- 0 subscriptions (nobody has paid for Pro)
- 4 reviews total (almost no community engagement)
- 1 wishlist (feature essentially unused)
- Dashboard exists but there's no evidence makers check it regularly

## What We Just Shipped: v1.6.0 Outcome Intelligence

### New Data Being Collected
- **Explicit outcomes**: Agents call `report_outcome(slug, success)` after integration. Works keyless — no API key needed. IP rate-limited at 10/day with dedup.
- **Implicit signals**: Inferred from search patterns:
  - Search → detail view → no further search in category = implicit adoption (weight 0.6)
  - Search → detail view → search again in same category = implicit rejection (weight 0.6)
  - 90-day rolling window
- **Agent client tracking**: `search_logs.agent_client` captures which AI agent made the search

### Success Rate Display
- Tool detail pages now show: "82% success rate from 14 agent reports" (green/amber/red badge)
- MCP responses include success rate data
- Confidence levels: low (<5 signals), medium (5-20), high (>20)

### The Connection to Maker Incentives
This outcome data is the foundation for a maker analytics product:
- Makers can see their success rate (and be motivated to improve it)
- Declining success rate = stale metadata = maker needs to update listing
- Cross-agent data is unique to IndieStack — can't get this anywhere else
- Creates a natural free→Pro boundary (basic stats free, full analytics paid)

## Existing Incentive Mechanisms

### Gamification (Milestones)
```
MILESTONE_THRESHOLDS = {
    'first_tool': 1,        # Listed first tool
    'getting_noticed': 10,  # 10 upvotes
    'community_fave': 50,   # 50 upvotes
    'ai_recommended': 1,    # First agent citation
    'ai_popular': 10,       # 10 agent citations
    'ai_essential': 100,    # 100 agent citations
}
```
- Badges display on dashboard
- Can be shared (social proof)
- 13 total milestones achieved across all users

### AI Live Badge
- Embeddable badge for GitHub READMEs showing agent citation count
- Format: `[![IndieStack](https://indiestack.ai/badge/{slug})](https://indiestack.ai/tools/{slug})`
- Intended as social proof / distribution incentive
- Unknown adoption rate

### Referral System
- Each maker gets a referral code
- Referral boost (temporary search ranking bump) after N referrals
- Essentially unused

## The Revenue Constraint

IndieStack MUST make money. The Pro subscription exists but has 0 subscribers. Current Pro benefits are:
- Higher API rate limits (1,000/day vs 50/day)
- Richer API responses (citation counts, compatible pairs, category percentile)
- Search boost for Pro makers' tools
- `maker_is_pro` badge on tool cards
- Demand Signals dashboard (shows what agents are searching for)

**The problem**: These benefits aren't compelling enough. Free tier is generous enough that nobody needs to upgrade. The maker dashboard shows most useful data for free.

## Schema for Key Tables

```sql
CREATE TABLE IF NOT EXISTS tools (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    tagline TEXT NOT NULL DEFAULT '',
    description TEXT NOT NULL DEFAULT '',
    url TEXT NOT NULL,
    maker_name TEXT NOT NULL DEFAULT '',
    maker_url TEXT NOT NULL DEFAULT '',
    category_id INTEGER NOT NULL REFERENCES categories(id),
    tags TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'pending',
    is_verified INTEGER NOT NULL DEFAULT 0,
    upvote_count INTEGER NOT NULL DEFAULT 0,
    maker_id INTEGER REFERENCES makers(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS makers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    slug TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    url TEXT NOT NULL DEFAULT '',
    bio TEXT NOT NULL DEFAULT '',
    avatar_url TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    name TEXT NOT NULL DEFAULT '',
    role TEXT NOT NULL DEFAULT 'buyer',
    maker_id INTEGER REFERENCES makers(id),
    email_verified INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agent_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id INTEGER REFERENCES api_keys(id),
    user_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('recommend','shortlist','report_outcome','confirm_integration','submit_tool')),
    tool_slug TEXT NOT NULL,
    tool_b_slug TEXT,
    success INTEGER,
    notes TEXT,
    query_context TEXT,
    created_at TIMESTAMP DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS search_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    source TEXT NOT NULL DEFAULT 'web',
    result_count INTEGER NOT NULL DEFAULT 0,
    top_result_slug TEXT,
    top_result_name TEXT,
    api_key_id INTEGER,
    agent_client TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS subscriptions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    stripe_subscription_id TEXT NOT NULL UNIQUE,
    plan TEXT NOT NULL DEFAULT 'pro',
    status TEXT NOT NULL DEFAULT 'active',
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## What Previous Research Covered (Don't Repeat)

### March 14: Defensibility & Outcome Data Moat
- How to transition from static curation to outcome-powered recommendations
- Implicit signal architecture (search → citation → silence patterns)
- Cold start playbook for outcome data
- Cross-platform "Switzerland" positioning
- **Already implemented**: frictionless outcome reporting, implicit signals, success rate display, MCP nudges
- **Don't repeat**: recommendation engine architecture, signal weighting, cold start mechanics

### March 13: Pro Subscription Architecture
- Tier definitions (free/pro maker, free/pro developer, agent tiers)
- Pricing rationale and unlock maps
- API monetization strategy
- **Don't repeat**: tier structure, pricing mechanics

### March 13: Demand Signals Pro
- Dashboard UX for demand/search data
- **Don't repeat**: demand dashboard design patterns

### What This Research Should ADD
- Creator platform retention psychology (not covered before)
- Two-sided marketplace supply-side mechanics (not covered before)
- Developer analytics product design + pricing (not covered before)
- Re-engagement strategies for unclaimed tools (not covered before)
- Specific conversion triggers from free to paid (not covered before)

## Key Questions for Gemini

1. What specific data visualization / metric makes a developer check their analytics dashboard daily? What's the "aha metric" for a maker on IndieStack?
2. How have other platforms (Etsy, Spotify for Artists, YouTube Studio) solved the "passive lister" problem — turning someone who listed once into an active participant?
3. At what data volume does a maker analytics dashboard become useful? We have 184 agent citations across 3,100 tools — most tools have 0-1 citations. Is it too early for analytics to drive retention?
4. What's the right free/Pro boundary for maker analytics that maximizes Pro conversion without making the free tier feel crippled?
5. How do you re-engage makers of auto-indexed tools who don't know IndieStack exists? What's the outreach that actually works (not spam)?
6. Is "Google Search Console for AI recommendations" a strong enough positioning to build a paid product around? What comparable products exist?
7. What price would indie makers pay for AI recommendation analytics? Most are solo developers or tiny teams.
8. Should IndieStack focus on maker retention at all, or is the supply side better served by automation (auto-index, auto-enrich, auto-health-check)?

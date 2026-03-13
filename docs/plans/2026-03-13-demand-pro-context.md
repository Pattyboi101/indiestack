# Demand Signals Pro — Full Context for Deep Research (March 13, 2026)

> This document gives an AI researcher complete context on IndieStack's Demand Signals Pro product, its current state, and what needs improving.

---

## What IndieStack Is (Quick Context)

IndieStack is the open-source supply chain for agentic workflows. AI coding agents (Claude, Cursor, Windsurf, Copilot) check IndieStack first to see if an indie creator already built what the developer needs. 3,099 tools across 25 categories. MCP server on PyPI (v1.3.1). Built by two uni students in Cardiff using Claude Code.

**Live at**: https://indiestack.ai

---

## The Demand Signal Pipeline

### How data flows

1. **Agent searches IndieStack** — via MCP server tool `find_tools(query)` or REST API `/api/search`
2. **Every search is logged** — `search_logs` table: query, result_count, source, top_result_name, top_result_slug, created_at
3. **Zero-result searches = demand signals** — when an agent searches and finds nothing, that's a validated gap
4. **Signals surface on the dashboard** — clustered, counted, timestamped, tiered

### Current data volume

| Metric | Value |
|--------|-------|
| Total search logs | 1,113 |
| Unique queries | ~400 |
| Zero-result (gap) searches | 146 unique gaps |
| Search sources | mcp, web, api |
| Data history | ~2 weeks (since MCP server launched) |
| Daily search volume | 50-150 searches/day (growing) |

### search_logs schema

```sql
CREATE TABLE search_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query TEXT NOT NULL,
    result_count INTEGER NOT NULL DEFAULT 0,
    source TEXT DEFAULT 'web',  -- 'mcp', 'web', 'api'
    top_result_name TEXT,
    top_result_slug TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Current Product: Two Tiers

### Free Tier: /gaps (Demand Bounty Board)

**URL**: indiestack.ai/gaps

**What it shows**:
- Top 5 demand gaps with tier badges (HIGH DEMAND / GROWING / EMERGING / NEW SIGNAL)
- Tier is based on count: ≥10 = High, ≥5 = Growing, ≥2 = Emerging, 1 = New
- Last searched timestamp (relative)
- "Build This →" button linking to /submit pre-filled with the query
- Mini activity feed (3 recent agent events)
- "How it works" explainer (4 steps)
- Upgrade CTA: "+N more demand signals available → Unlock Demand Signals Pro"

**Individual gap pages**: /gaps/{slug}
- Each gap has its own SEO page
- Shows exact search count, tier badge, last searched time
- "Why this matters" card explaining the opportunity
- Submit CTA pre-filled with the query
- 5 related gaps at bottom
- Meta description includes search count for SEO

**Purpose**: Drive tool submissions + demonstrate data value + upsell to Pro

### Paid Tier: /demand (Demand Signals Pro, $15/month)

**URL**: indiestack.ai/demand (behind Stripe subscription paywall)

**What it shows**:

1. **Stats bar** (3 numbers):
   - Total searches (30 days)
   - Zero-result count (30 days)
   - Fill rate (percentage of searches that found something)

2. **Trend chart** (CSS-only bar chart):
   - Last 14 days
   - Two bars per day: total searches (cyan) and zero results (red)
   - Height proportional to max daily volume
   - Date labels at bottom (MM-DD)

3. **Demand signals table** (full data):
   - Query text
   - Failed count (zero-result searches)
   - Total count (all searches including successful)
   - Sources (mcp, web, api — comma-separated)
   - First seen (relative timestamp)
   - Last seen (relative timestamp)
   - Tier badge (HIGH / GROWING / EMERGING / NEW)
   - Up to 50 rows
   - "Export JSON" link in header

4. **Live agent feed**:
   - Real-time feed of agent activity
   - Three event types: recommend (green dot), search (cyan dot), gap (red dot)
   - Shows tool name/link for recommends and searches
   - Shows query text for gaps
   - Relative timestamps
   - Auto-refreshes every 30 seconds via fetch('/api/pulse')
   - Blinking red "live" dot indicator
   - Max height 400px, scrollable

**Subscription**: Stripe Checkout → webhook → `subscriptions` table. Plan: `demand_pro`. $15/month.

---

## What's Wrong With It (Honest Assessment)

### The data is thin
- 1,113 searches over ~2 weeks isn't enough for meaningful trends
- The 14-day chart often has low single-digit numbers per day
- With only 146 unique gaps, the table is small and doesn't need scrolling
- Sources are mostly "mcp" — no real diversity to show

### The analysis is shallow
- It's essentially a sorted table of raw counts — no clustering, no categorization, no insight
- No comparison against existing tools ("10 searches for X — 3 tools exist but aren't being found")
- No growth velocity ("X is being searched 3x more this week vs. last")
- No recommendations ("Based on your skills, you should build Y")
- No alerts or notifications

### The visualizations are basic
- CSS bar chart works but isn't interactive or informative
- No time-series analysis, no sparklines, no mini-charts per signal
- The table is a wall of text with no visual hierarchy beyond tier badges
- No filtering, sorting, or searching within the pro dashboard

### The value gap between free and pro is unclear
- Free shows top 5 with tier badges and "last searched" time
- Pro shows... more rows with the same tier badges, plus exact counts
- The trend chart and live feed are nice but not worth $15/month alone
- A maker could check /gaps once a week and get 80% of the value

### The live feed is noisy
- Most events are "Search found [tool]" — successful searches aren't interesting to makers
- Gaps (red dots) are the interesting ones but they're mixed in with noise
- 30-second refresh is arbitrary — nothing changes that fast with our volume

### No personalization
- Same dashboard for everyone — a game developer sees the same data as an API developer
- No way to filter signals by category, technology, or interest area
- No "watch" or "alert" functionality

### No retention mechanism
- No reason to come back daily — the data changes slowly
- No email digest or notification system
- No history view ("here's how demand has shifted over the past month")

---

## Available Data We're Not Using

From `search_logs`, we could derive but currently don't:

1. **Growth velocity** — is a gap being searched more frequently over time?
2. **Search → submission correlation** — did anyone build something after seeing a gap?
3. **Category inference** — what category does a gap query likely belong to?
4. **Related gaps clustering** — "stripe alternative" and "payment processing" and "indie payments" are likely the same demand signal
5. **Competition density** — how many existing tools are close to filling a gap?
6. **Source distribution per query** — is demand coming from MCP (agents) or web (humans)?
7. **Time-of-day/day-of-week patterns** — when do agents search most?
8. **Geographic/agent-type inference** — which AI tools generate the most searches?

From other tables, we could cross-reference:
- `tools` table — what categories have the most/fewest tools? Where are the supply gaps?
- `tool_views` — which existing tools get traffic from related searches?
- `upvotes`, `bookmarks` — which existing tools are popular in gap-adjacent categories?

---

## Technical Constraints

- **Python f-string HTML templates** — no React, no Jinja2, no build step
- **CSS-only visualizations** — no D3, no Chart.js, no external JS charting libraries
- **Inline SVG is fine** — we can generate SVG charts server-side in Python
- **Vanilla JS is fine** — for interactivity like filtering, sorting, tabs
- **SQLite backend** — queries must be efficient against a single-file database
- **Single machine deployment** — Fly.io, 1 VM, 256MB RAM
- **Two-person team** — no ongoing manual curation or content creation

---

## Revenue Context

- Currently 0 real paying customers (1 test subscription — Patrick's own account)
- Stripe integration is live and working (checkout, webhooks, subscription management)
- No other monetization active
- The goal isn't just revenue — it's to make the dashboard genuinely valuable enough that makers want it

---

## DB Functions Available

```python
get_search_gaps(db, limit=30)      # Zero-result queries, grouped, counted
get_search_demand(db, query, days)  # Count for specific query
get_demand_trends(db, days=30)      # Daily search volume
get_demand_clusters(db, limit=50)   # Clustered signals with metadata
get_pulse_feed(db, limit=50)        # Unified activity feed
```

---

## Key Questions

1. What would make a maker check this dashboard every morning?
2. Is $15/month the right price — or should we charge more for a premium product?
3. Should the free and pro tiers be on the same page (filtered) or separate pages?
4. What derived analytics would be more valuable than raw data?
5. Would a weekly email digest be more valuable than the dashboard itself?
6. How do we make small data (1,100 searches) feel meaningful rather than sparse?
7. Should we offer a free trial period to get people hooked?
8. Is "Demand Signals Pro" the right name — or does it sound too enterprise?

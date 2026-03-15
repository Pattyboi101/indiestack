# IndieStack — Full Platform Context for Subscription Architecture Research

> This document provides complete context on IndieStack's current state: what it is, how it works, every data asset, every endpoint, exact volumes, current monetisation, and our vision. This is an LLM-to-LLM transfer — everything you need to design a subscription architecture is here.

---

## What IndieStack Is

IndieStack is the open-source supply chain for agentic workflows. AI coding agents (Claude, Cursor, Windsurf, Copilot) check IndieStack first via MCP server to see if an indie creator has already built what someone needs, instead of generating code from scratch. The constraint is "indie-built" — not just dev tools, but games, utilities, newsletters, creative tools, learning apps, anything made by independent creators.

**Live at**: https://indiestack.ai
**Built by**: Two university students in Cardiff, using Claude Code as their primary development tool
**Tech stack**: Python 3.11, FastAPI, aiosqlite (SQLite), pure Python string HTML templates (f-strings), Fly.io (1 VM, 256MB RAM), Stripe for payments
**No build step**: No React, no Jinja2, no external JS frameworks. CSS is inline or in a `:root` block. SVG charts are generated server-side.

---

## Current Data Volumes (March 13, 2026)

| Table | Rows | Notes |
|-------|------|-------|
| tools | 3,100 | Curated indie creations across 25 categories |
| makers | 645 | Indie creators |
| users | 52 | Registered accounts |
| categories | 25 | Dev tools, games, utilities, newsletters, creative, learning, etc. |
| page_views | 193,623 | Site-wide analytics |
| tool_views | 29,539 | Per-tool view counts (IP-hashed) |
| outbound_clicks | 26,326 | Clicks from IndieStack to tool websites |
| search_logs | 1,113 | Agent + human searches, ~2 weeks of data |
| tool_pairs | 1,279 | Compatibility pairs (which tools work together) |
| agent_citations | 184 | When agents recommend specific tools |
| magic_claim_tokens | 285 | Outreach to unclaimed tools |
| sessions | 67 | Active login sessions |
| upvotes | 60 | Community votes on tools |
| email_verification_tokens | 36 | Account verification |
| notifications | 24 | User notifications |
| milestones | 13 | Achievement tracking |
| claim_requests | 12 | Tool ownership claims |
| subscribers | 7 | Email newsletter |
| reviews | 4 | Tool reviews |
| api_keys | 3 | Developer API keys |
| tool_reactions | 3 | Use-this/bookmark reactions |
| api_usage_logs | 2 | API call tracking |
| **subscriptions** | **0** | **Zero paying customers** |
| **purchases** | **0** | **Zero marketplace sales** |
| developer_profiles | 0 | Per-API-key personalization (unused) |
| featured_tools | 0 | Featured placement (unused) |
| stacks | 0 | Curated stacks (unused) |
| sponsored_placements | 0 | Sponsored visibility (unused) |

**Key takeaway**: Heavy traffic (193K views, 26K clicks), zero revenue. People use IndieStack — they just don't pay.

---

## Vision (verbatim from VISION.md)

### Core Thesis
AI agents are becoming the primary interface between people and software. Every day, millions of developers ask AI agents to build things. Those agents don't know what indie creators have already built. So they rebuild from scratch — wasting tokens, time, and producing inferior solutions.

But it's bigger than developers. As agents become general-purpose assistants, everyone will ask their agent for recommendations. "Find me a recipe manager." "I need flashcards for studying." "What's a good indie game library?"

IndieStack is the open-source supply chain that sits between AI agents and everything indie creators have built. Not just dev tools — everything.

### The Flywheel
```
More creations listed → More reasons to query IndieStack → More MCP installs
→ More agent memory data → Better personalized recommendations
→ More value → More word-of-mouth → More makers list → repeat
```

Dev tools are the wedge. Not the ceiling.

### Long Term Vision
The canonical supply chain for ALL AI agents. Every new agent connects to IndieStack as a default. "AI recommendations" becomes a primary distribution channel bigger than SEO.

---

## Complete Database Schema (40 tables)

### Core Entities

```sql
-- 3,100 tools with 57 columns of metadata
tools (
    id, name, slug, tagline, description, url,
    maker_name, maker_url, category_id, tags, status,
    is_verified, upvote_count, price_pence,
    delivery_type, delivery_url, stripe_account_id,
    verified_at, verified_until, maker_id, created_at,
    is_ejectable, replaces, tool_type, platforms,
    install_command, boosted_competitor, is_boosted, boost_expires_at,
    submitter_email, submitted_from_ip, claimed_at,
    integration_python, integration_curl,
    mcp_view_count, github_url, github_stars, github_language,
    last_github_commit, github_freshness, source_type,
    pixel_icon, landing_position, quality_score, last_health_check,
    health_status, first_dead_at, github_last_commit,
    github_open_issues, github_is_archived, github_last_check,
    badge_nudge_sent, tool_of_the_week,
    -- Assembly metadata (structured for agent consumption):
    api_type, auth_method, sdk_packages, env_vars,
    frameworks_tested, verified_pairs
)

categories (id, name, slug, description, icon)

makers (
    id, slug, name, url, bio, avatar_url, created_at,
    indie_status, stripe_account_id,
    story_motivation, story_challenge, story_advice, story_fun_fact
)
```

### User & Auth

```sql
users (
    id, email, password_hash, name, role, maker_id,
    email_verified, created_at, badge_token,
    referral_code, referred_by, referral_boost_days,
    github_id, github_username, github_avatar_url,
    pixel_avatar, pixel_avatar_approved, email_opt_out
)

sessions (id, user_id, token, expires_at, created_at)
password_reset_tokens (id, user_id, token, expires_at, used, created_at)
email_verification_tokens (id, user_id, token, expires_at, created_at)
```

### Monetisation Infrastructure

```sql
subscriptions (
    id, user_id, stripe_subscription_id,
    plan TEXT DEFAULT 'pro',  -- currently checks: plan IN ('demand_pro', 'pro')
    status TEXT DEFAULT 'active',
    current_period_end, created_at
)

purchases (
    id, tool_id, buyer_email, stripe_session_id,
    amount_pence, commission_pence, purchase_token,
    delivered, created_at, discount_pence
)

-- Stripe Connect for makers
-- Platform fee: 5% standard, 3% for pro makers
-- Launch week (Mar 2-16): 0%

api_keys (
    id, key TEXT UNIQUE,  -- prefix: isk_
    user_id, name, tier TEXT DEFAULT 'free',
    is_active, last_used_at, created_at
)

api_usage_logs (id, key_id, endpoint, created_at)

sponsored_placements (
    id, tool_id, competitor_slug, label,
    started_at, expires_at, is_active
)
```

### Intelligence & Analytics

```sql
search_logs (
    id, query, source DEFAULT 'web',  -- 'mcp', 'web', 'api'
    result_count, top_result_slug, top_result_name,
    api_key_id, created_at
)

developer_profiles (
    id, api_key_id UNIQUE,
    interests DEFAULT '{}',      -- JSON: category interests inferred from searches
    tech_stack DEFAULT '[]',     -- JSON: technologies used
    favorite_tools DEFAULT '[]', -- JSON: tools frequently queried
    search_count, personalization_enabled DEFAULT 1,
    notice_shown, last_rebuilt_at, created_at
)

agent_citations (
    id, tool_id, agent_name DEFAULT 'unknown',
    context, created_at
)

tool_pairs (
    id, tool_a_slug, tool_b_slug,
    verified DEFAULT 0, success_count DEFAULT 0,
    source DEFAULT 'manual',  -- manual, agent, community
    created_at
)

tool_views (id, tool_id, ip_hash, viewed_at)
outbound_clicks (id, tool_id, url, ip_hash, referrer, created_at)
page_views (id, timestamp, page, visitor_id, referrer)
```

### Engagement

```sql
upvotes (id, tool_id, ip_hash, created_at)
wishlists (id, user_id, tool_id, created_at)
reviews (id, tool_id, user_id, rating, title, body, is_verified_purchase, created_at)
tool_reactions (id, tool_id, user_id, session_id, reaction, created_at)
notifications (id, user_id, type, message, link, is_read, created_at)
milestones (id, user_id, tool_id, milestone_type, achieved_at, shared)
subscribers (id, email, unsubscribe_token, created_at, source, tool_slug)

user_stacks (id, user_id, title, description, is_public, created_at)
user_stack_tools (id, stack_id, tool_id, position, note)
user_tool_pair_reports (id, user_id, tool_a_slug, tool_b_slug, created_at)

referral system: users.referral_code, users.referred_by, users.referral_boost_days
```

### Collections & Stacks

```sql
collections (id, slug, title, description, cover_emoji, created_at)
collection_tools (id, collection_id, tool_id, position)
stacks (id, slug, title, description, cover_emoji, discount_percent DEFAULT 15, created_at)
stack_tools (id, stack_id, tool_id, position)
stack_purchases (id, stack_id, buyer_email, stripe_session_id, total_amount_pence, discount_pence, purchase_token, created_at)
```

### Other

```sql
featured_tools (id, tool_id, featured_date, headline, description)
maker_updates (id, maker_id, title, body, update_type, created_at, tool_id)
claim_tokens (id, tool_id, user_id, token, expires_at, used, created_at)
claim_requests (id, tool_id, user_id, status DEFAULT 'pending', created_at)
magic_claim_tokens (id, tool_id, token, expires_at, used, created_at)
email_optouts (id, email, created_at)

-- Full-text search
tools_fts (name, tagline, description, tags) -- FTS5 virtual table
makers_fts (name, bio) -- FTS5 virtual table
```

---

## MCP Server — 15 Capabilities

The MCP server is distributed via PyPI (`pip install indiestack`). It's the primary way AI agents interact with IndieStack. Currently free, no authentication required.

| Tool | Description | Could be tiered? |
|------|-------------|-----------------|
| `find_tools` | Search by keyword, category, source type | Free (core funnel) |
| `get_tool_details` | Full detail — integration snippets, pricing, assembly metadata | Free basic, pro for assembly metadata? |
| `compare_tools` | Side-by-side comparison | Pro candidate |
| `build_stack` | "I need auth + payments + analytics" → complete stack | Pro candidate |
| `evaluate_build_vs_buy` | Should you build this or use an existing tool? | Pro candidate |
| `analyze_dependencies` | Analyze package.json/requirements.txt against catalog | Pro candidate |
| `get_recommendations` | Personalized based on history | Pro (requires profile) |
| `browse_new_tools` | What's new in the catalog | Free |
| `list_categories` | Browse the taxonomy | Free |
| `list_tags` | Find by technology/tag | Free |
| `list_stacks` | Community-curated tool stacks | Free |
| `publish_tool` | Submit from inside your agent | Free (grows catalog) |
| `scan_project` | Describe project, get complete stack recommendation | Pro candidate |
| `report_compatibility` | Report tool pairs that work together | Free (grows data) |
| `check_health` | Check maintenance status of adopted tools | Free basic, pro for alerts? |

---

## Current Monetisation State

### What exists (all with zero revenue):

1. **Demand Signals Pro** — $15/month, Stripe subscription
   - Opportunity scores (algorithmic ranking of best gaps to fill)
   - 14-day trend sparklines per signal
   - Competitor density indicators
   - Top 3 insight cards with build CTAs
   - Sortable enriched table
   - Gaps-only live feed
   - CSV export with enriched data
   - **0 subscribers**

2. **Marketplace** — 5% commission (3% for pro makers, 0% launch week)
   - Stripe Connect integration for maker payouts
   - Purchase flow, delivery tokens, receipt pages
   - **0 purchases**

3. **Tool verification** — $29 one-time (currently disabled)
   - Verified badge, priority in search results
   - **Disabled, 0 sales**

4. **Sponsored placements** — infrastructure exists
   - Tool appears on competitor's page as alternative
   - **0 active placements**

5. **API keys** — exist with `isk_` prefix, soft rate limits
   - Usage logging, developer profiles, personalization
   - Currently free, no tiered limits
   - Rate limiting is IP-based, not key-based
   - **3 keys issued, 2 API calls logged**

### What we tried and learned:
- Demand Signals Pro v1 (raw data table) — not worth $15/month
- Demand Signals Pro v2 (today — opportunity scores, sparklines, density) — better, but still not enough standalone value
- The free tier (/gaps) gives 80% of the value of pro
- The marketplace has zero liquidity — no tools have prices set

---

## Key Endpoint Groups (260+ total)

### Currently free, could be pro-gated:
- `/compare/{slugs}` — side-by-side tool comparison
- `/alternatives/{competitor}` — find alternatives to a tool
- `/demand` — demand signals pro dashboard (already gated)
- `/api/recommendations` — personalized API recommendations (requires key)
- `/api/stack-builder` — stack building recommendations
- `/api/demand-export` — CSV export of demand data

### Currently free, should probably stay free (funnel):
- `/search`, `/explore`, `/category/*` — discovery
- `/tool/{slug}` — tool detail pages (drives outbound clicks)
- `/submit` — tool submissions (grows catalog)
- `/gaps` — free demand signals (upsell funnel)
- All MCP server endpoints (grows ecosystem)

### Dashboard features (login-gated, not pro-gated):
- Maker dashboard: tool stats, views, agent citations, citation percentile
- Query intelligence: what searches lead to your tools
- Agent breakdown: which agents cite you most
- Launch readiness scoring
- Milestones and achievements

### Admin features:
- Tool approval, editing, bulk import
- Analytics dashboard
- GitHub health monitoring
- Email outreach

---

## Derived Intelligence We Can Compute From Existing Data

These are analyses we could offer but currently don't surface (or only partially surface):

1. **Opportunity Score** — `zero_count * (1 + zero_count / max(search_count, 1))` — DONE (pro only)
2. **Competitor density** — tools matching a gap query — DONE (pro only)
3. **14-day sparklines** — daily search volume per signal — DONE (pro only)
4. **Growth velocity** — is a gap being searched more frequently over time?
5. **Category supply/demand gap** — categories with high searches but few tools
6. **Compatibility graph analysis** — which tools are most connected? Central nodes?
7. **Agent citation trends** — which tools are being recommended more/less over time?
8. **Search-to-submission correlation** — did someone build a tool after seeing a gap?
9. **Stack co-occurrence** — which tools appear together most in user stacks?
10. **Tool health alerts** — GitHub activity declining, issues increasing
11. **Market saturation index** — categories approaching "enough tools"
12. **Maker engagement scoring** — which makers are most active, responsive?
13. **Referral chain analysis** — which referrals drive the most signups?
14. **API consumer profiling** — what do different API consumers search for?
15. **Cross-category recommendation** — "people who use X in DevTools also use Y in Analytics"

---

## What the Previous Research Produced

On March 12-13, we ran two Gemini Deep Research sessions:

**Session 1 (March 12)**: Strategic breakthrough — 10 ideas including demand signals monetisation, agent memory marketplace, compatibility certification. Led to the "agentic package manager" pivot and MCP server v1.3.

**Session 2 (March 13)**: Demand Signals Pro upgrade — produced feature list (opportunity scores, sparklines, competitor density, insight cards, sortable tables, gaps-only feed, CSV export). All implemented same day.

**What NOT to repeat**: Feature lists. We need architecture, not features. The features will follow from getting the tier structure right.

---

## Rate Limiting Infrastructure

Current rate limiting is IP-based with these thresholds:
- Auth endpoints: 10 req/60s per IP
- Tool operations: 5 req/60s per IP
- General API: 30 req/60s per IP
- Admin: 60 req/60s per IP

API keys exist but rate limiting is NOT key-aware. To implement tiered API access, we'd need to:
1. Add tier-based limits to the `api_keys.tier` column (already exists, defaults to 'free')
2. Switch rate limiting from IP-based to key-based for authenticated requests
3. Define tier limits (e.g., free: 100/day, pro: 10K/day, team: 100K/day)

---

## Technical Capacity

**What we can ship fast** (days, not weeks):
- New subscription tiers (Stripe infrastructure exists)
- Pro-gated features on any endpoint (auth middleware exists)
- API tier enforcement (key infrastructure exists)
- Email notifications/digests (email system exists with 30+ templates)
- New derived analytics (db.py has 200+ query functions, pattern is well-established)
- New dashboard views (f-string templates, inline CSS/SVG — no build step)

**What takes longer** (weeks):
- Consumer-facing agent recommendation engine
- Real-time collaboration features
- Mobile app or native integration

---

## Key Questions for Your Architecture

1. Is "IndieStack Pro" one tier that unlocks everything, or should there be distinct tiers for makers vs. developers vs. API consumers?
2. What's the right price when you have 52 users and 0 paying customers? $5? $15? $29? Pay-what-you-want?
3. Should the MCP server stay fully free (ecosystem growth) or should some capabilities require a pro API key?
4. Is the dashboard the right conversion surface, or should pro value live elsewhere (email digests, API responses, agent-side features)?
5. How do we frame "based on 1,113 searches" as valuable rather than thin?
6. When (what metric, what trigger) should we launch consumer-facing agent recommendations?
7. Should we offer a team/org tier, or is that premature at 52 users?
8. Is subscription revenue the right model, or should we monetise differently (data licensing, certification fees, sponsored placements)?

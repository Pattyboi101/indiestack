# IndieStack — Context for Vibecoded SaaS Quality Gates Research

> This document provides complete context for researching quality gate systems for a curated AI-agent-facing tool directory.

---

## What IndieStack Is

IndieStack (indiestack.ai) is the open-source supply chain for agentic workflows — 3,100+ indie creations across 25 categories (dev tools, games, utilities, newsletters, creative tools, learning apps). AI agents query IndieStack via an MCP server to discover existing indie-built tools instead of generating solutions from scratch. The constraint is "indie-built," not "developer tool." The primary users are AI coding assistants (Claude Code, Cursor, Windsurf), with human visitors arriving via agent recommendations or direct browsing.

## Current Data Volumes (March 13, 2026)

| Table | Rows | Notes |
|-------|------|-------|
| tools | 3,100 | 3,099 approved, 1 rejected |
| categories | 25 | Dev tools, games, utilities, etc. |
| makers | 645 | Tool creators |
| agent_citations | 184 | Agent usage tracking |
| search_logs | 1,113 | MCP + web search queries |
| outbound_clicks | 26,326 | Clicks through to tool URLs |
| page_views | 193,623 | Website traffic |
| upvotes | 60 | Community engagement (very low) |
| reviews | 4 | Written reviews (extremely low) |
| users | 52 | Registered accounts |
| tool_pairs | 1,279 | Compatibility data |
| claim_requests | 12 | Makers claiming their listings |

## Tool Source Breakdown

| Source | Count | How they got in |
|--------|-------|-----------------|
| code (GitHub/GitLab) | 2,791 | Auto-indexed from awesome-lists |
| saas (closed-source) | 309 | Auto-indexed from awesome-lists |

**Critical fact: ALL 3,100 tools are currently auto-indexed.** Zero manual submissions have been processed yet. The spam problem is forward-looking — as IndieStack grows and attracts organic submissions, the current near-zero rejection rate (1/3,100 = 0.03%) will become untenable.

## Submission Timeline

| Month | Total | SaaS | Code | Notes |
|-------|-------|------|------|-------|
| 2026-02 | 361 | 279 | 82 | Initial awesome-list indexing |
| 2026-03 | 2,739 | 30 | 2,709 | Massive GitHub auto-indexing sprint |

## Current Quality Gates (Submission-Time)

### Automated Checks
1. **Honeypot field** — Hidden `website2` field catches naive bots
2. **Required fields** — name, tagline, url, description, category_id
3. **URL format** — Must start with http:// or https://
4. **Tagline minimum** — ≥10 characters
5. **Description minimum** — ≥50 characters
6. **Tagline ≠ name** — Case-insensitive check
7. **No all-caps descriptions** — Catches SHOUTING SPAM
8. **Description expands tagline** — Must add detail beyond repeating tagline
9. **Duplicate URL detection** — SQL-based URL normalization (strips scheme, www, trailing /)

### What's NOT Checked
- No free tier requirement
- No documentation verification
- No GitHub activity check (for SaaS with GitHub links)
- No NLP quality scoring of description
- No social proof verification
- No domain age check
- No landing page verification
- No rate limiting per IP or email

## Post-Submission Flow

1. Tool enters `status='pending'`
2. Admin sees pending queue sorted by quality signals:
   - +10 points: URL is GitHub link
   - +5 points: Description > 200 chars
   - +3 points: Description > 100 chars
   - +2 points: Has tags
   - +1 point: Has maker_name
3. Admin clicks Approve or Reject (currently approves almost everything)
4. No reject reasons stored, no feedback to submitter

## Quality Score System (Post-Approval)

Already implemented for ranking/visibility:

```
score = completeness × (1 + engagement_boost) × health × 100
```

**Completeness (0-1.0):** description length, tags, maker claim, tagline length, source type, integration metadata
**Engagement (0-1.0):** upvotes, MCP views, reviews, clicks (all currently very low)
**Health (0 or 1.0):** Dead tools (7+ days) get score × 0.0

**Current distribution (approved tools):**
- 80-100: 477 tools
- 60-79: 224 tools
- 40-59: 2 tools
- 20-39: 47 tools
- 0-19: 2,349 tools (76%!)

Most tools score 0-19 because they're auto-indexed with minimal metadata — no engagement, no maker claim, basic descriptions.

## Health Monitoring

- 24-hour automated cycle for GitHub repos (HTTP HEAD + GitHub API)
- SaaS tools: ALL 309 have `health_status='unknown'` — no health checks running
- Dead tools (7+ days): quality_score × 0.0, effectively removed from search

## Listing Quality Score (Maker-Facing)

Separate from search quality score. Shown on maker dashboard with progress bar and tips:
- Description quality (25%)
- Freshness/maintenance (25%)
- Assembly metadata completeness (25%)
- Community signals (25%)

## The Three Submission Surfaces

Quality gates must apply consistently across:
1. **Web form** (`/submit`) — Human-facing, with form validation
2. **REST API** (`/api/submit`) — Programmatic, used by auto-indexer
3. **MCP `publish_tool()`** — Agent-facing, used by AI agents submitting tools

All three now have the same minimum content checks (tagline ≥10, description ≥50, duplicate URL).

## Tools Schema (Relevant Fields)

```sql
-- Key quality-relevant fields on the tools table:
source_type VARCHAR       -- 'code' (has GitHub) or 'saas'
quality_score REAL        -- 0-100, computed post-approval
health_status TEXT        -- 'dead', 'unknown', or alive
github_url TEXT           -- Auto-extracted GitHub link
github_stars INTEGER      -- From GitHub API
github_language TEXT      -- Primary language
last_github_commit TEXT   -- Freshness signal
github_freshness TEXT     -- 'active', 'stale', 'inactive'
github_is_archived INTEGER-- Abandoned repo
maker_id INTEGER          -- NULL = unclaimed, set = maker verified
submitter_email TEXT      -- Contact for manual submissions
submitted_from_ip VARCHAR -- For rate limiting
agent_instructions TEXT   -- How agents should use this tool
```

## The "Vibecoded SaaS" Problem

The 2025-2026 explosion of AI-generated SaaS products creates a specific threat:

**Characteristics of vibecoded spam:**
- Built in a weekend with AI code generation
- Closed-source, no free tier
- Generic landing page (often Vercel/Netlify default)
- Minimal or AI-generated documentation
- Using IndieStack as free advertising / SEO
- Description reads like AI marketing copy
- No community presence (0 Twitter followers, no HN posts, no Reddit mentions)
- Domain registered recently
- No users beyond the founder

**Why it matters for IndieStack specifically:**
- AI agents trust IndieStack's curation signal. If recommendations include junk, agents learn IndieStack is unreliable and stop querying.
- The catalog is the moat. Pollute it and the flywheel breaks.
- Current 0.03% rejection rate provides zero quality filtering.
- Admin (Patrick) has been bulk-approving to grow catalog — correct strategy for early stage, wrong strategy now.

**Why it's nuanced:**
- "Indie-built" includes legitimate solo-founder SaaS. Plausible Analytics is indie, closed-source, and paid.
- Some vibecoded projects evolve into real products. Rejecting too early kills potential.
- Open-source requirement would exclude ~10% of current catalog (309 SaaS tools, many excellent).

## What We've Already Tried

1. **Minimum content lengths** (tagline ≥10, description ≥50) — Catches the laziest submissions but doesn't distinguish quality
2. **Duplicate URL detection** — Prevents re-submission of existing tools
3. **Quality-sorted admin queue** — Surfaces best submissions first, but admin still approves almost everything
4. **Post-approval quality score decay** — Dead tools sink in rankings, but doesn't prevent initial approval

## What the Previous Research Produced

Three Gemini deep research sessions have been completed:
1. **Maker Incentive Problem** (March 14) — Resolved: Agent Instructions, success rate analytics, Listing Quality Score
2. **Autonomous Agents** (March 14) — Resolved: Cross-platform detection, pre-flight verification, agent-as-maker pathway
3. **Defensibility/Moat** (March 14) — Resolved: Cross-platform outcome data is the moat

None addressed submission quality gates specifically. This is the first research session focused on the spam/quality problem.

## Key Questions

1. What automated signals most reliably distinguish "serious indie product" from "vibecoded weekend project"?
2. Should IndieStack require a free tier for SaaS submissions? What's the false positive rate (legitimate paid-only indie tools)?
3. What's the right rejection rate for a curated directory? Product Hunt rejects ~70% of submissions. Awesome Lists reject ~90% of PRs. Where should IndieStack be?
4. Can outcome data (agent success/failure rates) serve as a retroactive quality signal to auto-demote tools that don't work?
5. Should the approval queue be replaced with "approve by default, demote by signal"? What are the risks?
6. How should IndieStack handle the gray area — a tool that's technically functional but clearly low-effort and adds nothing the catalog doesn't already have?
7. What NLP signals distinguish AI-generated marketing copy from genuine product descriptions?
8. Is domain age / WHOIS data a useful signal, or too noisy?

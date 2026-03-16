# StackShare Replacement Strategy — Design

**Date:** 2026-03-16
**Status:** Approved

## Context

StackShare (414K monthly visits) is a zombie — acquired by FOSSA Aug 2024, team fired, enterprise product sunset, no new features. Their API is dead (closed beta 6+ years, $99/month, 25 results max). Site runs on autopilot with thin auto-generated content. 55% of traffic from organic search on "X vs Y" and "X alternatives" queries.

### Why StackShare Failed
1. Self-reported data rots — nobody updates their stack profiles
2. No distribution moat — just a website, no workflow integration
3. No quality signal — lists tools without verifying they work together
4. No AI/agent integration — invisible to the new dev workflow
5. Enterprise monetisation — wrong customer, long sales cycles
6. Community effort died — no incentive to contribute

### Why IndieStack Wins
- Agent-verified outcome data (not self-reported)
- MCP server IS the distribution channel
- `report_outcome` provides quality signals automatically
- Already embedded in AI dev workflows
- Maker-side monetisation (natural alignment)

## Three-Phase Strategy

### Phase 1: Seed the Compatibility Graph (Today)

**Problem:** 30 seeded pairs for 3,100 tools = 1% coverage. Agents need data to recommend combinations.

**Approach:** Auto-generate pairs from our own data:
1. **Framework affinity:** Tools sharing `frameworks_tested` values are likely compatible (e.g., two tools both work with Next.js)
2. **Category complementarity:** Tools in complementary categories (auth + payments, database + analytics) make natural pairs
3. **Enrichment data:** Tools with compatible `api_type` + `auth_method` patterns
4. All generated pairs: `source='inferred'`, `verified=0`, `success_count=0`
5. Agents confirm/deny via `report_outcome` over time

**Target:** 30 → 500+ pairs without any external scraping.

**Optional boost:** Slowly fetch top 50-100 StackShare tool pages for "Tools that integrate with X" data. Rate-limit respectfully. Mark as `source='stackshare'`.

### Phase 2: SEO Comparison + Alternatives Pages

**Problem:** StackShare ranks for high-intent keywords with garbage content (0.35% text-to-code ratio, no real reviews).

**Build:**
- `/compare/{tool-a}-vs-{tool-b}` — side-by-side with agent success rates, health scores, GitHub stats, integration metadata, pricing, compatibility data
- `/tool/{slug}/alternatives` — alternatives from `replaces` data + same-category tools, ranked by quality score and agent outcomes
- Auto-generate for all tools with sufficient data
- SEO metadata, structured data (JSON-LD), clean URLs
- Include "AI agents recommend X over Y in Z% of cases" — data StackShare can never have

**Target:** 1,000+ indexable comparison pages outranking StackShare.

### Phase 3: Share Your Stack

**Problem:** No replacement for StackShare's community stack sharing.

**Build:**
- Public stack profiles (user_stacks already exist, just need public view)
- "What's your stack?" flow — pick tools, describe use case, publish
- Each published stack auto-creates compatibility pairs
- Agent-verified badge when `report_outcome` confirms the combo works
- Stack gallery page with filtering by use case, framework, category
- SEO-friendly stack profile pages

**Target:** Replace StackShare's stale self-reported model with living, agent-verified stacks.

## Traffic Plays (Immediate)

1. Submit IndieStack as a tool on stackshare.io
2. Create IndieStack company profile on StackShare (shows our tech stack)
3. List on AlternativeTo as StackShare alternative
4. Build "IndieStack vs StackShare" comparison page
5. Target StackShare's exact search keywords with better content

## Data Model Changes

### Phase 1
- No schema changes needed — uses existing `tool_pairs` table
- New script: `scripts/seeds/seed_inferred_pairs.py`

### Phase 2
- New routes: `/compare/{a}-vs-{b}`, `/tool/{slug}/alternatives`
- New template functions in components.py
- Sitemap update to include comparison pages
- JSON-LD structured data for comparisons

### Phase 3
- Make `user_stacks` + `user_stack_tools` publicly viewable
- Add `is_featured` column to user_stacks
- New route: `/stacks/gallery`, `/stacks/{id}`
- Stack-to-pairs conversion function in db.py

## Success Metrics

- Phase 1: Pair count ≥ 500, covering ≥ 200 unique tools
- Phase 2: Comparison pages indexed by Google, first page rankings within 60 days
- Phase 3: 50+ public stacks shared in first month
- Traffic: Organic search traffic grows 3x within 90 days

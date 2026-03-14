# Why Go Pro — Design Document

> **Date:** 2026-03-14
> **Status:** Approved, pending deep research on conversion mechanics

**Goal:** Redesign IndieStack Pro from "pay for more of the same" to a genuinely compelling intelligence + workflow integration layer that serves both makers and developers without compromising curation integrity.

---

## Core Principles

1. **Never sell visibility.** Search Boost is killed. Curation integrity is IndieStack's moat — the moment results are purchasable, the recommendation engine loses trust.
2. **Free = discovery. Pro = intelligence + workflow.** The full search, browse, MCP recommendation, listing, and badge experience stays free. Pro adds understanding and automation on top.
3. **One plan, two pitches.** Same $19/mo (pending price validation), same Stripe product. Two landing pages speaking to different pain points — makers and developers.
4. **Earned ranking, not purchased.** "Search Boost" replaced with "Listing Optimizer" — Pro makers get tools to improve their metadata, which naturally improves ranking because agents have more to match on.

---

## Maker Pro Features

### Keep (already built)
- Citation Intelligence — agent breakdown, 14-day sparkline, trend data
- Demand Signal Explorer — full gap analysis, opportunity scores, CSV/JSON export
- Weekly AI Report — citation digest to inbox
- 1,000 API queries/day
- Data Export (JSON/CSV)

### Add
- **Listing Optimizer** — guided metadata completion workflow. Shows what fields agents use (tagline, description, api_type, auth_method, sdk_packages, env_vars, frameworks_tested, compatible pairs). "How agents see your tool" MCP response preview. Completeness score (extends existing `compute_quality_score`). Data-driven tips as telemetry grows.
- **Competitor Alerts** — weekly digest when new tools listed in your category or a competitor gets a citation spike. Category + citation data already exists.
- **GitHub Action** — `indiestack/sync-listing`. On release tag, updates listing version, changelog URL, triggers health check. API endpoint + YAML file.
- **Slack/Discord Webhook** — configure webhook URL in dashboard. Fires on: new citation, weekly summary, competitor listing. Outbound POST with JSON payload.
- **Embeddable Analytics Widget** — SVG/iframe showing AI recommendation trend. Richer than existing badge — mini sparkline + citation count + "Recommended by X agents."

## Developer Pro Features

### Keep (already built)
- 1,000 API queries/day
- Richer MCP responses (citation counts, compatibility pairs, demand context)
- Data Export

### Add
- **Stack Auditor** — headline feature. Paste package.json, requirements.txt, go.mod, or Cargo.toml. Get structured report: deps with indie alternatives (scored), unmaintained deps, missing categories ("you have no analytics — consider Plausible or Umami"). Extends existing `analyze_dependencies()` with health data and maintenance scores. **First audit free (no account needed)** — ongoing monitoring requires Pro.
- **Private Recommendations** — weekly digest based on search history, bookmarks, developer profile. Uses existing `developer_profiles` table. Gives people a reason to build a profile.
- **Integration Alerts** — "A tool you bookmarked went stale" or "New compatibility pair for tools in your stack." Launches as concept, valuable as usage grows.
- **CI Audit Command** — `indiestack audit` CLI subcommand. Reads manifest, runs stack auditor, exits non-zero on unmaintained deps. Drop into any pipeline.
- **Stack Lock File** — `.indiestack.json` in repo root. Records which indie tools your project uses (slugs). `indiestack audit` validates against it. Version-controlled team alignment.

---

## What Gets Removed

- **Search Boost** — killed entirely. Contradicts curation integrity principle.

---

## Phasing

### Phase 1 — "Launch Day" (builds on existing)
- Kill Search Boost
- Listing Optimizer (metadata completion UI + MCP preview)
- Stack Auditor (web UI at `/audit`, first report free)
- Two landing pages (tabs or separate routes on `/pricing`)
- MCP upsell line in `analyze_dependencies()` responses
- Reframe existing features with better copy

### Phase 2 — "Sticky" (weeks after)
- `indiestack audit` CLI subcommand
- GitHub Action (`indiestack/sync-listing`)
- Competitor alerts (weekly digest)
- Private recommendation digest (weekly email)

### Phase 3 — "Ecosystem" (needs telemetry volume)
- Slack/Discord webhooks
- Integration alerts
- Embeddable analytics widget
- Stack lock file

---

## Open Questions for Deep Research

1. **Pricing** — Is $19/mo right for 52 users and an unestablished brand? Should it be $9/mo to get first 10 subscribers? What's the right founder tier price?
2. **Free trial vs freemium teaser** — 14-day trial, or show-then-gate? How much should free users see before the paywall?
3. **0→1 playbook** — How did curated directories (Product Hunt, Indie Hackers, BetaList, early Gumroad) monetize with <100 users? What did they do before traction?
4. **MCP upselling** — best practices for freemium API upsells inside agent responses. How aggressive, what copy, what conversion rates to expect?
5. **Founding Member pitch** — emotional vs transactional framing at early stage. "Bet on the vision" vs "get features cheaper."
6. **Channel-specific conversion** — where do the first 10 Pro subscribers come from? Existing users? New arrivals? MCP users? Reddit/HN traffic?

---

## Anti-Patterns to Avoid

- Selling placement or visibility (kills curation trust)
- Building Phase 3 features before Phase 1 converts anyone
- Pricing based on competitor benchmarks instead of willingness-to-pay at current scale
- Assuming features sell themselves without conversion mechanics
- Over-building before validating that anyone will pay at all

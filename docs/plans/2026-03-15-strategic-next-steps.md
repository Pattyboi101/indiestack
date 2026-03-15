# Strategic Next Steps — Design Doc (2026-03-15)

## Context

IndieStack has 3,099 tools (828+ approved), 52 users, 0 paying subscribers. Trust layer and quality gates shipped today. Stack Auditor is the PLG wedge at `/audit`. MCP server on PyPI (v1.6.0). Pro is $19/mo or $99 LTD (50 Founding Member seats). `report_outcome()` has been called exactly once — the trust layer exists but agents aren't using it yet.

---

## 1. GitHub Action / CI Integration for Stack Auditor

### The Opportunity

The strongest Pro conversion hook. A GitHub Action that runs on every PR and comments with indie alternatives creates recurring API key usage, which drives upgrade pressure. No competitor does this.

### Recommended Approach: GitHub Action first, npx wrapper later

- **Why Action over npx:** Actions run automatically on every PR. npx requires devs to remember to run it. The Action creates recurring API consumption.
- **Why not both at once:** Doubles scope for uncertain payoff. Ship Action, measure usage, then add npx.

### MVP Scope

1. **`POST /api/audit` endpoint** — accepts `{"manifest": "..."}`, returns JSON audit results. Reuses `parse_manifest()` and DB lookup from `audit.py`. Requires API key. Free tier: top 3 matches. Pro tier: all matches + health + trust scores + integration snippets.

2. **`indiestack/audit-action` repo** — composite GitHub Action. On `pull_request`, reads manifest, calls API, posts PR comment in markdown. Pro users get richer output.

3. **PR comment format:** Collapsible table per dependency with indie alternatives. Free: summary + "Upgrade to Pro for full report" CTA.

### Files to Change
- `main.py` or `audit.py` — extract matching logic into shared function, add `POST /api/audit`
- New repo: `indiestack/audit-action` (`action.yml` + bash/node script)
- `pricing.py` — re-add CI Integration as Pro feature

### Complexity: **M** | Dependencies: Price change (item 3) should land first

---

## 2. Agent Notification System

### Current State

Citations tracked in `agent_citations`. Milestones fire at 10/25/50/100/250/500/1000. Weekly ego pings now include citation counts. Gap: makers have no sense of daily traction between milestones.

### Recommended Approach: Daily digest email, not real-time push

- **Why daily over real-time:** 52 users, low citation volume. "Recommended 1 time" real-time notifications feel hollow. Daily aggregation feels meaningful.
- **Why not just improve weekly:** Weekly is too slow for the "your tool is getting traction" dopamine hit.
- **Special case:** "First recommendation ever" gets an immediate email — highest-dopamine moment.

### MVP Scope

1. **Daily citation digest** — cron at ~9am UTC. For makers with 1+ citations in 24h: count, top agent, week-over-week trend.
2. **First-ever citation email** — triggered immediately from `log_agent_citation()`.
3. **`email_daily_digest` user preference** — boolean, default true for makers.

### Files to Change
- `db.py` — `get_daily_citation_digest()`, `email_daily_digest` column
- `email.py` — `daily_citation_digest_html()` template
- `main.py` — `/api/send-daily-digest` admin endpoint

### Complexity: **S** | Dependencies: None

---

## 3. $9/mo Pricing

### The Problem

$19/mo with 52 users and 0 subscribers. Gemini research: comparable indie tools launch at $5-9/mo.

### Recommended Approach: Drop Pro to $9/mo, keep $99 LTD

- **Why not add a Starter tier:** Two paid tiers with 52 users is over-engineering. Not enough feature surface to differentiate.
- **Why $9 not $5:** $5 signals "not serious" and makes $99 LTD look expensive (20 months payback). $9 keeps LTD attractive (~11 months).
- **Why not keep $19 and push LTD:** Zero conversions at $19 after a week is a signal. Some users want monthly flexibility.

### MVP Scope

1. Create $9/mo Stripe price
2. Update pricing.py, audit.py upsell, email templates
3. Update Stripe price ID reference in main.py

### Files to Change
- `pricing.py` — $19 → $9
- `main.py` — Stripe price ID
- `audit.py`, `email.py` — pricing references

### Complexity: **S** | Dependencies: None (do first — informs outreach pitch)

---

## 4. First Paying Customer Strategy

### Warmest Leads

**Tier 1 (claim requesters):** Marie Martens (Tally), Jack Arturo (automail), Peter Bamuhigire (server-manager), Thomas Poignant (Go Feature Flag)

**Tier 2 (high engagement):** Invoice Ninja (87), Atomic CRM (90), Alicia Sykes, WorkAid Dunning (89)

### Recommended Approach: Concierge $99 LTD to Tier 1

1. Ship $9/mo price change first
2. Send 4 personalised emails to Tier 1 from Patrick's personal address
3. Lead with data: "I can show you the exact prompts developers type before AI agents recommend Tally. Last week, Tally was cited X times."
4. Offer: "First 50 founding members get Pro forever for $99. You're one of [6] makers who claimed their tool — I wanted to offer this first."
5. **No free trials.** $99 LTD is already low commitment. Trials delay the revenue signal.
6. Follow up in 3 days. If Tier 1 converts 0, move to Tier 2.

### Complexity: **S** (human work, not code) | Dependencies: Item 3 (price change)

---

## Execution Order

| Priority | Item | Effort | Blocked By |
|----------|------|--------|------------|
| 1 | Price change to $9/mo | S | Nothing |
| 2 | Daily citation digest | S | Nothing |
| 3 | Concierge outreach | S (human) | Item 1 |
| 4 | CI / GitHub Action | M | Item 1, then independent |

Items 1 and 2 can ship in parallel. Item 3 follows immediately (email writing). Item 4 is next sprint.

---

## Key Insight: report_outcome() Adoption

Only 1 call ever (plausible-analytics). The trust layer infrastructure is built but agents aren't using it. Before investing more in trust features, need to:
- Verify the MCP server prompt actually encourages outcome reporting
- Consider making it more prominent in tool detail responses
- Track call volume as a leading indicator
- The trust badges showing "new" everywhere is fine — it's honest about the data state

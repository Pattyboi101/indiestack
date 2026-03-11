# IndieStack Monetisation Strategy

**Goal:** Four revenue streams that don't compromise the indie-first, merit-based ethos.

**Status:** Planning — nothing built yet. Revisit post-PH launch.

---

## Stream 1: Affiliate Revenue (Easiest, Start Now)

**How it works:** When IndieStack recommends a tool (via MCP server, tool page, or explore) and a dev signs up through our link, we earn commission. Zero cost to makers, zero quality impact — ranking stays merit-based.

**Confirmed affiliate programs (as of March 2026):**

| Tool | Commission | Type | How to Join |
|------|-----------|------|-------------|
| Simple Analytics | 50% of first year | One-time | Must be SA customer, via account dashboard |
| Crisp | 20% recurring (12 months) | Recurring | affiliates.crisp.chat or email contact@crisp.chat |
| Lemon Squeezy | Up to 30% | Varies by merchant | lemonsqueezy.com/marketing/affiliates |

**No affiliate program:** Plausible, Supabase, Resend, Coolify, PostHog (credit-only), Clerk (case-by-case creators program).

**Implementation:**
- Add `affiliate_url TEXT` column to `tools` table
- When set, outbound clicks route through affiliate URL instead of direct URL
- Track via existing `outbound_clicks` table — no new tracking needed
- MCP server tool responses include affiliate URL when present

**Revenue estimate:** £100-400/mo passive once 10-20 affiliate links are active.

**Action items:**
- [ ] Sign up for Simple Analytics affiliate (need SA account first)
- [ ] Apply to Crisp affiliate program
- [ ] Join Lemon Squeezy affiliate hub
- [ ] Research more tools with affiliate programs (expand beyond initial 10)
- [ ] Add `affiliate_url` column + routing logic

---

## Stream 2: Market Gap Reports (Low Effort, High Margin)

**How it works:** Our `/gaps` page already shows zero-result searches ranked by demand. Package this as market intelligence for indie makers and VCs looking for their next idea.

**Product:** Monthly PDF/CSV of top 50 unmet searches + demand counts + category breakdown.

**Pricing:** £49 one-time per report on Gumroad (zero infrastructure cost).

**What we sell:** Only aggregated, anonymous search gap data. No personal data, no individual tracking, no user behaviour beyond "X was searched for Y times and nothing matched."

**Revenue estimate:** £200-500/mo if we get 5-10 sales/month.

**Action items:**
- [ ] Build `get_gap_report()` query in db.py (top 50, last 30 days, with category)
- [ ] Create report template (PDF or styled HTML)
- [ ] Set up Gumroad listing
- [ ] Promote on r/SaaS, r/indiehackers, Twitter

---

## Stream 3: API Tiers for Agent Builders (Biggest Long-Term Play)

**How it works:** Companies building AI agents need quality tool recommendations. We're the knowledge layer. Charge for volume and premium features.

**Tiers:**

| Tier | Price | Searches/mo | Features |
|------|-------|-------------|----------|
| Free | £0 | 100 | Basic search, standard results |
| Pro | £29/mo | 1,000 | Personalized reranking, agent memory, priority support |
| Enterprise | Contact us | Custom | Dedicated support, SLA, custom integrations |

**Already built:** API keys (`isk_` prefix), rate limiting, personalized recommendations, agent memory, developer profiles at `/developer`.

**Still needed:**
- Pricing page (repurpose existing `/pricing`)
- Tier tracking on `api_keys` table (`tier`, `quota_limit`, `usage_this_month`)
- Stripe subscription for Pro tier
- Usage dashboard on `/developer` page

**Revenue estimate:** Even 20 Pro users = £580/mo. Enterprise deals could be £500+/mo each.

**Action items:**
- [ ] Add tier columns to api_keys table
- [ ] Build pricing page with tier comparison
- [ ] Stripe subscription flow for Pro
- [ ] Usage stats on /developer page
- [ ] Rate limit enforcement by tier

---

## Stream 4: Maker Premium (Extras, Not Algorithm)

**How it works:** Makers pay for tools to understand and promote their listing — NOT for algorithmic advantage. Ranking stays 100% merit-based (AI recs, relevance, upvotes).

**What free makers get:** Listed, discoverable, basic AI rec count (already on public badges), "Maker ✓" badge.

**What premium gets (that's NOT already free):**
- Detailed analytics dashboard: which agents recommend you, for what queries, click-through rates, weekly trends
- "Maker Pro" badge (distinct from Maker ✓)
- Featured in monthly "Maker Spotlight" digest email
- Priority support for listing issues
- Custom pixel avatar (already built)

**Note:** The basic AI rec count is already public on badges. Premium analytics must go deeper — query-level breakdown, agent-level attribution, trend graphs — to justify the price.

**Price point:** £49/year (impulse buy for any serious maker).

**Still needed:**
- Analytics dashboard with query/agent breakdown
- Maker Pro badge in components.py
- Stripe subscription flow
- Monthly digest email template

**Revenue estimate:** £200-500/mo if 50-120 makers upgrade.

**Action items:**
- [ ] Design analytics dashboard (what data do we actually have?)
- [ ] Add `maker_pro_until` column to makers table
- [ ] Build upgrade flow with Stripe
- [ ] Create digest email template

---

## Priority Order

1. **Affiliate links** — lowest effort, start earning immediately
2. **Gap reports** — low effort, pure margin, validates demand
3. **API tiers** — biggest upside, build after PH launch
4. **Maker premium** — needs more users/makers first, build last

---

## What We Won't Do

- **Pay-to-rank:** Paying never influences search results or MCP recommendations
- **Sell personal data:** Only aggregated, anonymous search gaps
- **Paywall discovery:** The explore page, search, and MCP server stay free
- **Direct tool sales:** Paused (can't sell people's tools without permission)

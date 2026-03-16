# Claim-to-Reveal Analytics Wall — Design

**Goal:** Gate tool analytics behind claiming, creating a funnel from free claim → Pro subscription.

**Approach:** Server-side data wall (Approach B) — route-level gating, no data in HTML unless authorized. Tease existence of analytics to drive claims.

---

## The Funnel

```
Creator discovers their listing on IndieStack
  → Sees teaser: "AI agents are recommending this tool"
  → Claims listing (free, email verified)
  → Sees headline numbers: 14 recommendations, 87% success rate
  → Sees blurred Pro section: "Which agents? Daily trends? Query intelligence?"
  → Upgrades to Pro ($19/mo) or Founder ($99 LTD)
```

## Visibility Tiers

### Unclaimed tools (public visitors)
- Tool description, reviews, categories — all visible as normal
- Analytics replaced with teaser banner: "AI agents are recommending this tool → Claim this listing to see your analytics"
- No numbers, no percentages rendered
- Claim CTA promoted higher on page (below teaser)

### Claimed (free tier)
- Recommendation count (the number)
- Overall success rate (percentage)
- Total view count
- "Last recommended: X days ago" timestamp
- "View full analytics →" link to dashboard (blurred Pro sections)

### Claimed + Pro
- Full dashboard: agent breakdown, daily sparklines, query intelligence, export, weekly AI report

## Tool Detail Page Changes (`tool.py`)

Current lines 184-216 show analytics badges publicly. New behavior:

- **Unclaimed:** Teaser banner + claim CTA. No analytics badges rendered.
- **Claimed (free):** Rec count badge, success rate badge, view count, last recommended.
- **Claimed (Pro):** Above + "View full analytics →" link to dashboard.

Public visitors see the tool's description, reviews, and metadata — just not the analytics numbers.

## Dashboard Changes (`dashboard.py`)

Two-layer gating on the AI Distribution Intelligence section (line 252+):

1. **No claimed tools:** Empty state — "Claim your first tool to unlock analytics" with tool search box.
2. **Claimed, free:** Total recs, overall success rate, per-tool breakdown (name, rec count, success rate, last recommended). Blurred Pro section below.
3. **Claimed, Pro:** Full existing dashboard — agent breakdown, sparklines, query intelligence, export.

Adds `has_claimed_tools` check above existing `is_pro` check at line 308.

## Claim Flow (email verification)

1. User clicks "Claim this listing" on tool detail page
2. Not logged in → redirect to signup/login → back to tool page
3. Logged in → form asks for their email (pre-filled if tool has contact email)
4. Domain check:
   - **Email domain matches tool's website domain:** Magic link sent → click = instant claim. No admin approval.
   - **No domain match:** Falls back to `claim_requests` for admin review. User sees "We'll review within 24 hours."
5. On claim: set `tools.maker_id`, `tools.claimed_at`, user `role = 'maker'`

## Data Model

**No new tables or columns needed.** Reuses:
- `tools.maker_id` + `tools.claimed_at` — ownership tracking
- `claim_requests` — pending admin-reviewed claims
- `magic_claim_tokens` — token infrastructure for email verification
- `agent_actions` — recommendation/outcome data (already collected via MCP)
- `users.role = 'maker'` — set on successful claim

Gating logic lives entirely in routes (`tool.py`, `dashboard.py`).

## Cleanup Note

Dead boost code should be removed in a separate task:
- `/api/claim-and-boost` endpoint (main.py:2926)
- `activate_boost`, `credit_referral_boost`, `claim_referral_boost` (db.py)
- `is_boosted`, `boost_expires_at`, `referral_boost_days` columns
- `boosted_competitor` column and `toggle_tool_boost`

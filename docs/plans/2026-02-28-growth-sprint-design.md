# Growth Sprint: "Show the Life That's Already There"

## Thesis

IndieStack's problem isn't that nobody uses it — 66 tools are claimed by real makers including Coolify, Simple Analytics, Ghost, Supabase, Clerk, and Lemon Squeezy. 18 real user accounts are linked to maker profiles. The problem is that **this traction is invisible to cold visitors.** The fix is 80% surfacing existing data, 20% grinding outreach.

**North star metric:** 50+ additional claimed tools in 6 weeks (total: 116, ~26% of catalog)

**Current state:** 480 tools, 66 claimed, 18 user-maker accounts, 20 users, zero reviews, ~2,000 MCP lookups

---

## Part 1: Make Claims Visible (Pat, ~1 day code)

### A. "Maker ✓" badge on claimed tool cards

- **File:** `src/indiestack/routes/components.py` — `tool_card()` function
- Claimed tools (those with `claimed_at IS NOT NULL`) show a subtle green badge: `Maker ✓` using `badge-success` class
- Unclaimed tools continue to show "Community Listed" in muted gray (`badge-muted`)
- The contrast between green and gray naturally communicates: "some tools have real makers here"

### B. Landing page stats bar update

- **File:** `src/indiestack/routes/landing.py` — MCP walkthrough stats bar
- Current: `"{mcp_views} agent lookups · {tool_count} tools indexed · {search_stats} searches this week"`
- New: `"{mcp_views} agent lookups · {tool_count} tools · {claimed_count} maker-verified"`
- Requires: add `claimed_count` to the landing page cache/query (simple `SELECT COUNT(*) FROM tools WHERE claimed_at IS NOT NULL`)

### C. Trending sort boost for claimed tools

- **File:** `src/indiestack/db.py` — `get_trending_scored()` function
- Add `+ (CASE WHEN t.claimed_at IS NOT NULL THEN 20 ELSE 0 END)` to the heat score
- Claimed tools naturally rise to the top of explore and the landing page trending strip
- Visitors see maker-verified content first

### D. Live MCP counter

- **File:** `src/indiestack/routes/landing.py` — stats bar
- Replace any static "2,000+" text with the real `mcp_views` number from the DB (already cached in landing page data)
- The number grows organically as agents use the server

---

## Part 2: Kill Ghost Town Signals (Pat, ~half day)

### A. Seed 5-10 real reviews

- Pat and Ed write honest 2-3 sentence reviews of tools they actually use under their real accounts
- Target tools: Simple Analytics, Supabase, Cal.com, Resend, Ghost, Coolify — tools they've personally used
- Even 5 reviews breaks the "No reviews yet" pattern on the most-visited tool pages
- NOT fake reviews — genuine opinions from actual users

### B. Pricing page reframe

- **File:** `src/indiestack/routes/content.py` or wherever pricing is rendered
- Replace £9/mo Pro purchase flow with "Pro is coming — join the waitlist"
- Keep the feature list so makers know what's planned
- Restore when 50+ active makers justify the tier

### C. Blog: 2-3 quick posts or hide

- Ed writes 2-3 "Best X alternatives" posts (1-2 hours each):
  - "Best Indie Analytics Tools in 2026"
  - "Open-Source CMS Comparison: Ghost vs Strapi vs Payload"
  - "Intercom Alternatives for Bootstrapped Startups"
- Or: remove blog link from nav until critical mass
- One post looks worse than zero — fix the imbalance

---

## Part 3: Ed's Claim Outreach (Ed, 10 hrs/week ongoing)

### Daily routine

1. Open admin outreach tab → unclaimed tools sorted by traffic
2. Pick 10 tools with the most page views / MCP lookups
3. Find maker contact: Twitter/X DM, GitHub email, website contact form
4. Send personalized message with magic claim link + their traffic stat
5. Log outreach in admin maker tracker

### Message template (Ed adapts per tool)

> Hey [name]! I'm Ed, co-founder of IndieStack. We've listed [Tool] in our indie tool catalog — it's been viewed by [X] developers this month and recommended by AI agents [Y] times via our MCP server.
>
> Your listing is live at [URL] — you can claim it in one click to update the description, track analytics, and get verified: [magic claim link]
>
> No charge, no catch. We're building the definitive indie tool directory and want makers to own their listings.

### Follow-up protocol

- One follow-up after 3 days on non-responses
- Then move on — don't spam
- Track conversion rate to calibrate messaging

### Target

- 10 contacts/day × 5 days/week = 50/week
- At 5-10% conversion = 2.5-5 claims/week
- 6 weeks = 15-30 claims (conservative)
- Stretch: 50 claims (requires better targeting + conversion)

---

## Part 4: MCP Distribution (Ed, 1-2 hours one-time)

### A. Directory submissions

Submit IndieStack MCP server to:
- Smithery (smithery.ai)
- Glama (glama.ai)
- mcp.so
- awesome-mcp-servers (GitHub)
- Any other MCP directory that exists

### B. GitHub README polish

- Clear install instructions for Claude Code, Cursor, Windsurf
- Tool count badge
- Link to the live catalog

---

## What NOT to Do

- Don't seed more tools (480 is plenty)
- Don't build new features (product is complete for this stage)
- Don't redesign anything (the design is good)
- Don't add testimonial widgets or case study pages (claims ARE the social proof)
- Don't run paid ads (no budget, premature anyway)
- Don't create elaborate onboarding flows or email sequences

---

## Success Criteria (6 weeks)

| Metric | Now | Target |
|--------|-----|--------|
| Claimed tools | 66 | 116+ |
| Real reviews | 0 | 10+ |
| MCP directory listings | 1 (PyPI + Registry) | 5+ |
| Blog posts | 1 | 3-4 |
| Weekly site visitors | ? | Track baseline + growth |

---

## Implementation Order

1. Maker ✓ badge on tool cards (components.py)
2. Landing page stats bar update (landing.py + db query)
3. Trending sort boost for claimed tools (db.py)
4. Live MCP counter (landing.py)
5. Pricing page reframe (content.py)
6. Pat + Ed write 5-10 real reviews (manual, via the site)
7. Ed starts daily outreach routine
8. Ed submits MCP server to directories
9. Ed writes 2-3 blog posts

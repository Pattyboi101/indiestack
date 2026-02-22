# Gemini Round 15 — Status Update + What Next?

## Context

You're advising on IndieStack, an indie SaaS directory built with Python/FastAPI + SQLite, deployed on Fly.io. One developer (Patrick, university student) + one collaborator (Ed, handles outreach). Live at indiestack.fly.dev.

---

## What We Built Since Round 14

You gave us 8 thought experiments. We built **all 8** in one session. Here's the status:

### NOW Priorities (Live + Active)

1. **Ego Ping Weekly Email (Experiment 2)** — Done. Background asyncio task runs every Friday. Sends makers a stats digest: "Your tool got X views, Y wishlist saves this week." Contextual CTA nudges changelog updates if they haven't posted one recently. Uses Gmail SMTP.

2. **Alternatives Page Copy Fix (Experiment 3)** — Done. Stripped all developer jargon ("tokens", "vibe-coder", "MCP"). Alternatives pages now speak to non-technical buyers: "better pricing, more flexibility, personal support from the makers who built them." Added per-tool pricing badges (green pill: "From £X/mo" or "Free") and "Indie alternative to X" subtitles on each card.

3. **Boost Value Report (Experiment 4)** — Done. Dashboard shows a dark navy gradient card with 4 stat boxes (views, wishlists, days remaining, badge status). When boost expires, sends a results email: "Your tool was featured for 30 days. Here's what happened." Includes a "Boost Again" CTA.

4. **B2B Sponsored Placements (Experiment 8)** — Done. New `sponsored_placements` table. Admin can create sponsored slots tied to competitor slugs. Renders above organic results on `/alternatives/{slug}` pages with cyan border, gradient background, configurable label. This is the £500/month play for DevTool scaleups.

### LATER Priorities (Live + Dormant)

5. **Email Capture on /explore (Experiment 1)** — Done. Inline banner between tool grid and pagination. JS fetch POST, no page reload. "Get the best indie tools in your inbox."

6. **Package.json Analyzer (Experiment 5)** — Done. `/stacks/generator` — paste your package.json or requirements.txt, get matched to indie alternatives. Parses dependencies, searches by replaces/tags/name.

7. **Blog Tool Injection (Experiment 6)** — Done. `{{ tool: slug }}` syntax in blog posts renders interactive tool cards with upvote/wishlist buttons inline. First usage in the "Stop Wasting Tokens" manifesto post.

8. **Maker Matchmaker (Experiment 7)** — Done. Dashboard widget shows 3 makers with overlapping tags. "Ed is also building in Auth. Check out their tool." Dormant until we hit ~20+ claimed makers.

---

## Current Numbers

- **Tools listed**: ~131 (26 seeded, rest from submissions)
- **Claimed tools**: ~2
- **Visitors**: ~2,000 total
- **Revenue**: £0
- **GitHub**: Private repo, Ed has push access
- **Stripe**: Live keys not yet configured (test mode only). £29 Boost checkout works in test mode. Stripe Connect removed — using direct Checkout instead.
- **Scale fixes**: 5 DB indexes, rate limiting, session cleanup, page view retention (90-day), landing page cache (5-min TTL), admin pagination, upvote transaction wrapping

## What's Happened on the Ground

- Ed is doing maker outreach — has a list of 55 unclaimed tools with DM templates and magic claim links
- No Product Hunt launch yet
- No paid customers yet
- Blog has 1 post (the manifesto)
- 197 programmatic SEO pages (alternatives + best-of categories) indexed

---

## The Question

We've built a LOT of infrastructure. The bucket has fewer holes now (ego ping, copy reframe, boost reporting). But we still have:

- £0 revenue
- 2 signups
- ~2,000 visitors
- No live Stripe keys

**What should we actually DO this week?** Not build — do. We're a university student and his mate, not a dev team that needs more features.

Give us:
1. **The 3 highest-leverage non-code actions** we can take this week (outreach, launch, content, partnerships — whatever moves the needle)
2. **The 1 code thing** worth building if we have spare time (and why it matters more than the other 50 things we could build)
3. **What we should stop doing** (be brutal — what's wasted effort?)
4. **A reality check**: Given 131 tools, 2 signups, £0 — what's the honest path to £500/month? Is it even this product, or should we pivot the model?

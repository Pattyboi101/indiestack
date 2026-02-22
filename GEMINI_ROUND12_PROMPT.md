# IndieStack — Round 12: Monetisation & Conversion Strategy

## Context — What You're Looking At

IndieStack (https://indiestack.fly.dev) is a curated marketplace for indie SaaS tools — built by two university students (Patrick & Ed) in 2 weeks using Python, FastAPI, SQLite, and Claude Code. It's live on Fly.io.

**The core pitch**: Developers waste tokens and time rebuilding features (auth, payments, analytics, email) that indie tools already solve. IndieStack helps them discover and buy those tools instead.

**Target users**:
- **Buyers** (demand side): AI-native developers / vibe coders who use LLMs to build apps fast, but burn tokens on commodity features
- **Makers** (supply side): Solo developers and small teams who've built SaaS tools and want distribution

---

## Current Traction (as of Feb 2026)

- **1,953 unique visitors** (and rising)
- **2 registered accounts** (terrible conversion — 0.1%)
- **0 purchases** yet
- **~100 tool listings** (Ed scraped from GitHub/indie directories)
- Traffic sources: LinkedIn post, some organic search, a few referrals
- Product Hunt launch imminent, Show HN drafted

---

## Current Monetisation Model

### Revenue Streams
1. **Commission on sales**: Makers list tools with prices. When a buyer purchases, we take a cut via Stripe Connect.
   - Free tier: **5% platform fee** (maker keeps ~92% after Stripe's ~3%)
   - Pro tier: **3% platform fee** (maker keeps ~94%)
2. **Pro subscription**: £9/month for makers — gives lower commission, verified badge, analytics, priority search ranking
3. **Verified badge**: One-time purchase for trust signal on tool listing
4. **Top-Shelf boost**: Featured placement on alternatives pages (not yet priced/sold)

### How Tool Pricing Works
- Makers set their own price (e.g. £29 for GovLink, our own product)
- External tools link out (e.g. "Get Simple Analytics from £9/mo" → their site)
- Free tools just have a "Visit Website" button
- The marketplace handles checkout for tools that sell through us (Stripe Connect destination charges)

### What's NOT Working
- **Almost no one signs up**. 1,953 visitors, 2 accounts. The value prop for signing up is weak — what do you get? Wishlists and a dashboard, but that's not enough.
- **Tool prices feel disconnected from the "save tokens" pitch**. We say "save 50k tokens by using Plausible instead of building analytics" — but Plausible costs £9/mo. The connection between token savings and tool cost isn't compelling enough.
- **Most tools link externally anyway**. We can't monetise tools that sell on their own site. So our commission model only works for the minority of tools that sell through our checkout.
- **No reason to buy through us vs. directly**. Why would a developer buy through IndieStack instead of going to the maker's site? We offer no bundle discount, no unique value for purchasing through us.
- **Makers don't need us yet**. With 2 signups, we can't promise distribution. The claim flow is ready but makers won't care until we have buyers.

---

## What We've Built (Feature Summary)

**Discovery**: Explore page with filters, search (FTS5), 20 category pages, 197 tag pages, alternatives pages (programmatic SEO), "Best Tools" ranked pages, trending algorithm, collections, tool comparisons

**Community**: Maker profiles + directory, build-in-public updates feed, changelogs, reviews with ratings, wishlists, notifications, weekly email digest

**Trust**: Verified badge, Ejectable badge ("export your data"), Maker Pulse badge (active development), indie status badges (Solo Maker / Small Team), changelog streak badges

**Payments**: Stripe Connect, Pro subscription, commission calculator on submit page, earnings dashboard

**Growth**: MCP server (so AI assistants can search our catalogue), SVG embeddable badges, blog (2 posts), email capture in footer, RSS feeds, JSON-LD on every page, OG share cards

**Unique features**: "Tokens Saved" counter (estimates how many LLM tokens a tool saves vs building from scratch), "Replaces" field (each tool lists what big-co product it replaces), Vibe Stacks (curated bundles at 15% discount)

---

## The Core Problem

We built a feature-rich marketplace, but our monetisation model assumes a mature two-sided marketplace with buyers and sellers transacting through us. We're at day 1. We need a model that works NOW — with 2k visitors, 0 buyers, and 100 listings that are mostly unclaimed.

**Key tensions**:
1. We can't charge buyers because the tools are already available elsewhere (many are free/open source)
2. We can't charge makers because we have no buyer traffic to offer them yet
3. Commission only works when transactions happen through us, but most tools sell on their own sites
4. The "save tokens" angle is compelling for content/SEO but doesn't translate to a purchase motivation

---

## What I Need From You

Give me **3 concrete monetisation pivots** we could make in the next 1-2 weeks, ranked by how well they solve the chicken-and-egg problem. For each one:

1. **The model**: How does money flow? Who pays, for what, when?
2. **Why it works at our stage**: Why does this work with 2k visitors and 100 listings, not just at 100k visitors?
3. **What we'd build**: Specific features/pages/changes needed (we can ship fast — Claude Code builds full features in hours)
4. **Risk/downside**: What could go wrong?
5. **Revenue projection**: Realistic first-month revenue estimate

Also answer these specific questions:

- **Should we pivot away from marketplace commission entirely?** Our current commission model requires us to be the payment processor, but most indie tools already have their own checkout. Is there a better model?
- **Is "save tokens" the right angle, or should we reframe?** The token-saving pitch works for content marketing but doesn't drive purchases. What framing would actually convert?
- **What would make a developer sign up?** Right now signup gives you wishlists and a dashboard — not enough. What's the minimum viable value that makes someone create an account?
- **Should we charge makers or developers?** Or neither yet? At what stage does each make sense?
- **Are Vibe Stacks (bundles) the right product?** We built curated bundles with 15% discounts and one-click checkout. Is this the direction to lean into, or is it premature?

---

## Constraints

- Two students, limited budget (can't subsidise with VC money)
- Tech stack is Python/FastAPI/SQLite — very lean, very fast to iterate
- Claude Code lets us ship features in hours, not weeks
- Stripe Connect is already wired up for payments
- We're about to launch on Product Hunt — so whatever we decide, it needs to be live soon
- We'd prefer a model that helps makers AND developers, not one that exploits either side

---

## For Reference: Comparable Models

- **Product Hunt**: Free listings, no commerce. Makes money from Ship (launch tools) and ads.
- **Gumroad**: 10% commission. Creator-first. Volume play.
- **AppSumo**: Deep lifetime deal discounts. Drives volume but controversial with makers.
- **AlternativeTo**: Free listings. Ad-supported.
- **StackShare**: Free tool directory. Enterprise sales for "private stacks."
- **Uneed**: Paid "boost" placements for makers.

What would you recommend for IndieStack's stage and positioning?

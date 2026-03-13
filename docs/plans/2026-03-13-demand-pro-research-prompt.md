# Gemini Deep Research Prompt — Demand Signals Pro Upgrade

> Copy everything below the line into Gemini 3.1 Deep Research. Attach the context file (2026-03-13-demand-pro-context.md) as a document.

---

## Prompt

I've attached a detailed context document about IndieStack's Demand Signals Pro product — a paid dashboard ($15/month) that shows indie makers what AI agents are searching for and can't find. Read it thoroughly before proceeding.

**The situation**: Demand Signals Pro exists, has all the infrastructure, but isn't worth $15/month in its current state. It has: a stats bar (total searches, zero results, fill rate), a 14-day CSS bar chart, a sortable table of demand signals with tier badges, and a live agent feed. The data is real and valuable — AI agents genuinely search IndieStack and we log every query. But the *presentation* and *analysis* don't justify paying for it. A smart indie maker would look at the free tier (/gaps, top 5 bounties) and say "I don't need the pro version."

**What's changed since launch**:
- Free tier now has individual SEO pages per gap (/gaps/{slug}) with search counts, related gaps, and submit CTAs
- The landing page shows 4 live demand gaps as a teaser
- We have 1,113 total search logs, 146 zero-result gaps
- The pro dashboard has a JSON export endpoint
- Live agent feed auto-refreshes every 30 seconds

**What I need you to deeply research and think about**:

### 1. What makes data dashboards worth paying for?

Research the actual mechanics of paid analytics/intelligence products:
- **Exploding Topics** ($39-$299/month) — what makes their trend data worth paying for? How do they present "things that are growing"?
- **SparkToro** ($50-$225/month) — how do they make audience research data actionable? What's the UX?
- **SimilarWeb** — how do they present competitive intelligence in a way that drives decisions?
- **Google Trends** (free) — what does it do well? What's missing that paid alternatives fill?
- **Glimpse** (Google Trends overlay, $50/month) — what do they add on top of free trend data to justify the price?
- **Product Hunt's upcoming/trending** — how does their "what's hot" data create urgency?

I want to understand the specific UI patterns, data transformations, and analytical features that make raw search data *actionable* rather than just *visible*.

### 2. What intelligence would indie makers actually pay for?

Research what indie makers (solopreneurs, small teams, bootstrappers) currently spend money on for market research:
- What tools do they use to validate ideas before building?
- What data do they wish they had that doesn't exist?
- How do successful indie makers choose what to build next?
- What's the difference between "interesting data" and "actionable intelligence"?
- How do indie hackers currently discover market gaps?

### 3. Dashboard UX patterns for data products

Research best-in-class analytics dashboard design:
- **Linear's analytics** — clean, minimal, but information-dense. How?
- **Stripe Dashboard** — how do they make financial data feel calm and clear?
- **Plausible Analytics** — how does a privacy-focused analytics tool make simple data feel premium?
- **PostHog** — how do they make complex analytics approachable?
- What makes users *return daily* to a dashboard vs. check it once and forget?

I need specific UI patterns: how to present trend data, what kinds of visualizations work for small datasets (we have ~1,100 searches, not millions), how to create "aha moments."

### 4. What should Demand Signals Pro actually contain?

Think beyond "more data." The raw search logs aren't the product — the *intelligence derived from them* is:
- How should we cluster and categorize demand signals? (by domain, by use case, by technology stack?)
- What derived metrics would be more useful than raw counts? (growth velocity? competition density? time-to-fill?)
- Should we compare demand signals against what *does* exist? (e.g., "10 searches for 'indie Stripe alternative' — 3 tools already exist but agents aren't finding them")
- What alerting/notification features would make this a tool people check daily?
- Should there be a "build this" recommendation engine that pairs gaps with the maker's skill set?
- How should the JSON/CSV export be structured for makers who want to do their own analysis?

### 5. Pricing and packaging

Research pricing strategies for small data products:
- Is $15/month the right price? What do comparable indie intelligence tools charge?
- Should it be freemium with a generous free tier, or a hard paywall?
- Would a one-time purchase (lifetime access) work better for indie makers?
- Should there be tiers (basic/pro/team)?
- What about "pay once, own forever" models like many indie tools use?
- Would bundling Demand Signals Pro with other IndieStack features (priority listing, "Maker Verified" badge, featured placement) create a more compelling package?

### 6. The competitive moat question

Research whether this kind of demand signal data has value beyond IndieStack:
- Could this data be valuable to VCs, accelerators, or market researchers?
- Are there other platforms generating similar "what's missing" data?
- How do we prevent the data from being scraped and republished?
- Could the free tier cannibalize pro? Is the current free/pro split right?

---

**What I need from you**:

Produce a structured document with **12 concrete, implementable upgrades** for Demand Signals Pro. For each:

1. **What it is** (specific and concrete — "add a heatmap of search frequency by hour" not "improve visualizations")
2. **The insight** (what research finding makes this valuable)
3. **Implementation complexity** (can two uni students build this in a day? a weekend? a week?)
4. **Data requirements** (do we need new data we don't currently collect, or can we derive this from existing search_logs?)
5. **Expected impact on willingness to pay** (would this alone justify $15/month?)

**Constraints**:
- **Must work with ~1,100 data points** — we don't have millions of searches. Ideas must work at small scale and get better as data grows.
- **Must be buildable with Python f-string HTML templates** — no React, no charting libraries. CSS-only charts, inline SVG, vanilla JS at most.
- **Must be maintainable by two people** — no features requiring manual curation or daily attention.
- **The free tier must still be compelling** — we need /gaps to drive submissions. The pro tier sells *depth and speed*, not access.
- **Think about what makes someone check this daily** — the current dashboard is a "check once, see everything, leave" experience. What creates pull?

**Also address**:
- Should we rename from "Demand Signals Pro"? Is the name clear? Does it convey value?
- Should the pro dashboard be a separate page or an enhanced version of /gaps?
- Is the current table-based layout the right approach, or should it be more card-based?
- What would a "weekly demand digest" email look like? Would that add value?
- Should makers be able to "watch" specific signals and get notified when they trend?

**Format**: Rank by impact-to-effort ratio. Lead with your single most important finding about what makes data dashboards worth paying for. End with "This weekend" and "This month" action plans.

**Depth expectation**: Real research, real examples, real product teardowns. Don't tell me "dashboards need good UX" — show me specifically what Exploding Topics or SparkToro does that creates willingness to pay, and how we can adapt that with CSS-only charts and 1,100 data points.

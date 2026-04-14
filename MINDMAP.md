# IndieStack Mind Map

> What we've built and who owns what.
> Updated: 2026-03-29

## The Big Picture

```
                    IndieStack
          "Discovery layer for dev tools"
                       |
        +--------------+--------------+
        |              |              |
   AI AGENTS      DEVELOPERS     TOOL MAKERS
   (primary)     (secondary)     (tertiary)
        |              |              |
   MCP Server     Web + API      Dashboard
   21 tools      /explore        /dashboard
                 /analyze        /maker
                 /migrations
```

---

## 1. DISCOVERY ENGINE (how people find tools)

| Feature | URL | What it does | Revenue path |
|---------|-----|-------------|--------------|
| MCP Server | PyPI `indiestack` | AI agents search 3,100+ tools | Data collection from every query |
| Web Search | /explore, /search | Browse + filter by category/tag | SEO traffic -> conversions |
| Alternatives | /alternatives/{tool} | "X but indie" pages | High-intent SEO traffic |
| Compare | /compare/{a}/vs/{b} | Side-by-side tool comparison | Decision-stage traffic |
| Collections | /collections | Curated tool bundles | Bundle sales |
| Stacks | /stacks | Pre-built technology stacks | Community engagement |
| Use Cases | /use-cases | "Tools for SaaS", "Tools for AI" | Vertical SEO |

**Owner:** Patrick (engine) + Ed (content/SEO)

---

## 2. INTELLIGENCE LAYER (what makes us better)

| Feature | URL | What it does | Revenue path |
|---------|-----|-------------|--------------|
| Stack Health Check | /analyze | Score dependencies for freshness/cohesion/modernity | Data collection + consulting |
| Migration Intelligence | /migrations | Live migration paths from GitHub repos | Content marketing + API sales |
| Verified Combos | /api/combos | Packages that work together in production | Agent recommendations |
| CI Outcomes | /api/outcomes | Build pass/fail from GitHub Actions | Predictive intelligence |
| Technographics | /api/technographics/{slug} | Tool adoption metrics | Tool maker insights |
| Repo Audits | /api/audit/{owner}/{repo} | Full dependency health audit | Consulting ($500-1k) |
| Gap Analysis | /gaps | What tools are missing from catalog | Market intelligence |
| Moat Stats | /api/moat/stats | How much unique data we have | Internal tracking |

**Owner:** Patrick (building)

### Data Collection Flywheel
```
More agent queries -> more usage data -> better recommendations
     ^                                         |
     |                                         v
More tool makers notice -> list their tools -> more tools in catalog
```

### Current Data (growing 24/7)
- 422 migration events (90+ unique paths)
- 93,111 verified package combinations
- 8,756 repos scanned (targeting 10,000 — 88%)
- Script: `python3 scripts/github_autopsy.py --status`

---

## 3. DATA PRODUCT (intelligence we can sell — pricing TBD)

| Feature | URL | What it does |
|---------|-----|-------------|
| Migration API | /api/migrations?package=X | Who's migrating from/to a package |
| Combo API | /api/combos?package=X | Verified working combinations |
| Repo Audits | /api/audit/{owner}/{repo} | Full dependency health audit |
| Marketing Page | /data | Explains the data product |

**Pricing:** Not finalised. Strategy is to build the best product first, figure out pricing when we have users. Don't oversell what we don't know.

---

## 4. MAKER TOOLS (tool makers manage their listings)

| Feature | URL | What it does |
|---------|-----|-------------|
| Dashboard | /dashboard | Overview, analytics, sales |
| Tool Editor | /dashboard/tools/{id}/edit | Edit listing details |
| Claim Tool | /api/claim | Verify ownership of a listing |
| Submit Tool | /submit | Add new tool to catalog |
| Changelog | /dashboard/updates | Publish tool updates |
| Stripe Connect | /dashboard/stripe-connect | Connect for payouts |
| Analytics | /dashboard/analytics | Views, clicks, upvotes over time |

**Owner:** Patrick (backend) + Ed (maker outreach)

---

## 5. DEVELOPER TOOLS (API users)

| Feature | URL | What it does |
|---------|-----|-------------|
| API Key Management | /developer | Create/revoke API keys |
| API Docs | /api, /openapi.json | REST API documentation |
| Setup Guides | /setup, /setup/claude.md | Integration instructions |
| GitHub Action | Pattyboi101/stack-health-check | Auto-check deps on PRs |
| Badges | /api/badge/{slug}.svg | Embeddable status badges |
| Embeds | /embed/widget.js | Tool cards for any site |

**Owner:** Patrick

---

## 6. CONTENT & MARKETING

| Feature | URL | Purpose |
|---------|-----|---------|
| Blog | /blog/* | SEO + thought leadership (6 posts) |
| Changelog | /changelog | Product updates |
| RSS Feed | /feed/rss | Syndication |
| Landing Page | / | First impression + conversion |
| Pricing | /pricing | Plan comparison |
| Calculator | /calculator | "Tokens saved" ROI tool |

**Owner:** Ed (writing) + Patrick (technical content)

---

## 7. ADMIN & OPS

| Feature | URL/Command | What it does |
|---------|------------|-------------|
| Admin Panel | /admin | Approve tools, moderate, bulk ops |
| Pivot Dashboard | /admin/pivot | Honest internal/external usage split |
| Analytics | /admin/analytics | Site-wide metrics |
| Outreach | /admin/outreach | Track maker outreach campaigns |
| Command Hub | govlink.fly.dev | Shared task/decision tracker |
| Autopsy Script | scripts/github_autopsy.py | Mine repos for migration data |
| Health Sweep | scripts/github_health_sweep.py | Check tool maintenance status |
| Compatibility Miner | scripts/mine_github_compatibility.py | Find tool pairs in repos |

**Owner:** Patrick (ops) + Ed (outreach)

---

## 8. INFRASTRUCTURE

| Component | Details |
|-----------|---------|
| Stack | Python 3 / FastAPI / SQLite (WAL) / Fly.io |
| Domain | indiestack.ai (fly.dev fallback) |
| MCP Server | PyPI package `indiestack` v1.11.1 |
| Auth | GitHub OAuth + magic links + email/password |
| Payments | Stripe (subscriptions + one-off + Connect) |
| Email | Gmail SMTP (production only) |
| Monitoring | /health endpoint, Fly.io logs |
| GitHub | Pattyboi101/indiestack (public) |
| Command Hub | govlink.fly.dev |

---

## Revenue

**Status:** 0 paying customers. Pricing not finalised. Strategy: build the best product, figure out money later.

**Possible streams (unvalidated):**
- Sponsored placements (tool makers pay to rank higher in agent results)
- Data reports (one-off migration/competitive reports)
- Premium API tiers (when we have volume to justify it)
- Maker verified badges

**What NOT to do:** Don't invent pricing for things nobody has asked to buy yet.

---

## What Ed Should Focus On

1. **Maker outreach** — get tools listed, especially well-known ones with thin metadata
2. **Content** — share interesting findings from /migrations (organic, not spam)
3. **His 5 open tasks** — #103-105, #112-113

## What Patrick Should Focus On

1. **Tool metadata quality** — backfill install commands, env vars, integration snippets for top 100 tools
2. **MCP experience** — make agent responses so good that agents come back
3. **Autopsy to 10k** — more data = better recommendations
4. **Distribution** — how do we get MCP installs?

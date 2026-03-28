# IndieStack Mind Map

> What we've built, how it makes money, and who owns what.
> Updated: 2026-03-28

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

## 2. INTELLIGENCE LAYER (our moat)

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

**Owner:** Patrick (building) — this is the core strategic asset

### Data Collection Flywheel
```
More agent queries -> more usage data -> better recommendations
     ^                                         |
     |                                         v
More tool makers notice -> list their tools -> more tools in catalog
```

### Current Data (growing 24/7)
- 57 verified migration paths (jest->vitest, webpack->vite, etc.)
- 6,100+ verified package combinations
- 318 repos scanned (targeting 10,000)
- Script: `python3 scripts/github_autopsy.py --status`

---

## 3. DATA PRODUCT (how we sell the moat)

| Feature | URL | Target buyer | Price |
|---------|-----|-------------|-------|
| Migration API | /api/migrations?package=X | Tool maker marketing teams | $299/mo |
| Combo API | /api/combos?package=X | Tool maker marketing teams | $299/mo |
| Consulting Audits | /api/audit/{owner}/{repo} | Engineering teams | $500-1k one-off |
| Data Licensing | Contact | VCs, market intelligence | $500-2k/mo |
| Marketing Page | /data | Sell API access | Lead gen |

**Phase status:** PHASE 1 (building data volume). See command hub for full roadmap.

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
| MCP Server | PyPI package `indiestack` v1.9.5 |
| Auth | GitHub OAuth + magic links + email/password |
| Payments | Stripe (subscriptions + one-off + Connect) |
| Email | Gmail SMTP (production only) |
| Monitoring | /health endpoint, Fly.io logs |
| GitHub | Pattyboi101/indiestack (public) |
| Command Hub | govlink.fly.dev |

---

## Revenue Summary

| Stream | Status | Revenue | Effort to activate |
|--------|--------|---------|-------------------|
| Consulting audits | READY NOW | $500-1k/each | Just need clients |
| Migration API | PHASE 1 | $299/mo | Need 10k repos first |
| Data licensing | PHASE 2 | $500-2k/mo | Need volume + buyers |
| Tool maker dashboards | PHASE 2 | $99-299/mo | Need the data to sell |
| Pro subscriptions | DEPRIORITIZED | $19/mo | Not enough value yet |
| Stack bundles | BUILT | Variable | Need maker adoption |
| Sponsored placements | BUILT | Per-placement | Need traffic |

---

## What Ed Should Focus On

1. **Run the autopsy** — `python3 scripts/github_autopsy.py --mode all --limit 2000` (builds the moat)
2. **Maker outreach** — get tools listed, especially from categories with migration data
3. **Content** — blog posts using migration data ("We scanned 500 repos...")
4. **Social** — share /migrations page findings, NOT on Reddit/HN (organic only)
5. **GitHub Action installs** — every install = free data sensor

## What Patrick Should Focus On

1. **Scale the autopsy to 10k repos** — the moat IS the product
2. **MCP server improvements** — make agent recommendations data-backed
3. **Consulting audits** — can sell NOW, no scale needed
4. **CI outcome collection** — upgrade GitHub Action to report pass/fail

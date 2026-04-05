# Meeting: MCP Growth & First Maker Pro Customers
**Date:** 2026-04-05 12:00
**Status:** Closed
**Attendees:** Patrick (chair), CEO, Frontend, Backend, DevOps, Content, MCP

---

## Agenda

What should we focus on to grow MCP installs and push toward first Maker Pro paying customers?

Context:
- MCP server: 10,000+ PyPI installs, v1.12.0
- Maker Pro: $19/mo — agent citation analytics, search query data, verified badge, priority placement
- Developer Tools cleanup just completed: 2,943 → 2,496 tools properly categorised
- 8 high-value tools added (SvelteKit, Remix, LangChain, LlamaIndex, Vercel AI SDK, Kysely, Coolify, Express)
- RAG system seeded and working

Key questions:
1. What's the fastest path to first Maker Pro subscriber?
2. What MCP improvements would drive more installs?
3. Are there content/SEO opportunities we're not capturing?
4. What data does a maker actually need to see to justify $19/mo?

---

## Discussion

### CEO

[MEETING RESPONSE] CEO

Strategic read: Worth pursuing — but the two goals (MCP installs vs Maker Pro revenue) have different flywheels and we risk diluting effort by chasing both. MCP installs grow via AI agent adoption which is compounding; Maker Pro revenue requires direct maker outreach which is manual. We should keep those tracks separate and not expect one to drive the other in the short term.

Revenue path: Fastest path to first Maker Pro subscriber is direct outreach to tool makers already indexed on IndieStack — they have a concrete reason to pay (their tool is already surfaced to agents). Email outreach to 10-20 makers with real traction is more reliable than waiting for inbound. The analytics dashboard needs to show *something compelling* on day 1 or the $19/mo won't convert.

Evidence of demand: 10,000+ MCP installs proves AI agents are using IndieStack. The question is whether makers know this. They don't unless we tell them. Zero evidence yet that makers are aware they're being cited by AI agents — that's the core unlock.

Risk flags:
- Analytics dashboard may show low citation counts for most tools (95% of tools rarely cited) — this kills the value prop for most makers
- Price anchoring: $19/mo feels arbitrary without a clear ROI story. "X agents cited your tool this week" needs to be meaningful data.
- MCP install growth may plateau without PyPI discovery improvements (better README, Claude Desktop install instructions)

Verdict: pursue
Conditions: (1) Analytics must show real citation data before outreach starts — fake/empty dashboards destroy trust. (2) Identify 5 tools with high citation counts first, reach out to those makers specifically.

---

### Frontend

[MEETING RESPONSE] Frontend

Perspective: The Maker Pro dashboard is the conversion point — if it looks like an afterthought, no one pays. Currently the /maker/* pages need significant work to make citation analytics feel premium and trustworthy.

Opportunities:
- Citation graph/timeline on maker dashboard would make the data visceral (not just numbers)
- "Your tool was cited in X AI sessions this week" as the hero metric — needs real-time feel
- Maker Pro badge visible on tool card would signal status to other makers browsing the catalog
- The /pricing page needs social proof (even one testimonial or "X makers subscribed")

Concerns/blockers:
- No citation visualisation component exists yet
- Mobile responsiveness of maker dashboard untested
- Need to confirm what data the analytics API actually returns before building UI around it

Tasks I can own:
- Audit /maker/dashboard current state — identify what analytics are already exposed
- Design citation timeline component (last 30 days, weekly bars)
- Add Maker Pro badge to tool cards for verified makers

---

### Backend

[MEETING RESPONSE] Backend

Perspective: The citation analytics pipeline is the critical dependency for Maker Pro. We log MCP tool calls via agent_actions table but I need to confirm the citation count query is fast enough to power a real-time dashboard for makers.

Opportunities:
- `agent_actions` table already tracks tool citations — just need maker-scoped queries
- Could add a `maker_citation_summary` view pre-aggregating weekly/monthly counts per tool
- Search query data for Maker Pro: we log all queries in search_logs — easy to filter by which queries a maker's tool appeared in

Concerns/blockers:
- Citation counts per tool may be low (most tools get <5 citations/week) — need to sanity check before we promise this as a value prop
- Maker auth: makers need to claim their tools before they can see analytics — is the claim flow working?
- Performance: joining agent_actions with tools at query time could be slow at scale

Tasks I can own:
- Query production: how many unique tools have >10 agent citations this month?
- Add `maker_weekly_citations` view to DB for fast dashboard queries
- Verify maker claim flow end-to-end

---

### DevOps

[MEETING RESPONSE] DevOps

Perspective: Infrastructure is not a blocker for Maker Pro launch. One machine, WAL mode, health checks all passing. The risk is if Maker Pro drives a spike in dashboard traffic without caching.

Opportunities:
- Set up a cron to pre-compute weekly citation summaries overnight (avoids expensive queries at dashboard load time)
- Fly.io metrics already capture request latency — could alert on maker dashboard p95 > 2s

Concerns/blockers:
- Email delivery for "your tool was cited" notifications requires production SMTP (Gmail) — works in prod, not locally. Need to be careful about rate limits if we send to many makers at once.
- Backup before Maker Pro launch — need a clean DB snapshot

Tasks I can own:
- Add cron job to precompute maker_citation_weekly table at 02:00 daily
- Run /backup before Maker Pro launch

---

### Content

[MEETING RESPONSE] Content

Perspective: The MCP growth story needs better top-of-funnel content. "10,000 installs" is a milestone but it's not in any discoverable place. Makers finding IndieStack via Google need to land on content that explains why listing here is worth $19/mo.

Opportunities:
- Blog post: "Your tool is being recommended to AI agents — here's how to see it" — targets makers who may already be indexed
- /why-list page copy needs updating with the AI agent angle (currently too generic)
- Case study: pick one tool with high citations, show the maker what the data looks like, get a quote
- SEO: "best [category] tools for AI agents" pages would rank for long-tail queries and drive maker discovery

Concerns/blockers:
- Can't write the case study without a real maker who's seen the dashboard
- Stats in copy need to be verified (tool count, install count) — these go stale fast

Tasks I can own:
- Update /why-list with AI agent discovery angle and real citation stats
- Draft "your tool is being recommended to AI agents" outreach email template
- Write meta descriptions for top 10 category pages (SEO gap)

---

### MCP

[MEETING RESPONSE] MCP

Perspective: The MCP server is the core distribution channel but v1.12.0 has friction points that are slowing installs. The Claude Desktop install flow is the main bottleneck — users need to manually edit claude_desktop_config.json which drops off many non-technical users.

Opportunities:
- PyPI README needs a "Quick Install" section with the exact claude_desktop_config.json snippet — currently buried
- New MCP tool: `get_maker_stats(tool_slug)` — lets AI agents surface citation data inline (also a Maker Pro hook)
- Better tool descriptions in the 23 MCP tools — some are terse and don't help agents understand when to use them
- Submit to Claude's official MCP directory if one exists

Concerns/blockers:
- Any MCP server changes need a PyPI publish to take effect — not instant
- New MCP tools require version bump and re-install by existing users

Tasks I can own:
- Rewrite PyPI README with clearer Quick Install section
- Audit all 23 MCP tool descriptions for clarity and completeness
- Draft `get_maker_stats` tool spec for Backend to implement the underlying API

---

## Patrick's Notes

Key theme from all departments: **citation analytics are the unlock**. Nothing else moves until makers can see real data showing their tool is being cited by AI agents. That's the "aha" moment that justifies $19/mo.

Priority order that emerged:
1. Validate citation data exists (Backend query: how many tools have >10 citations?)
2. If data is real → build maker dashboard analytics view (Backend + Frontend)
3. Email template for maker outreach (Content)
4. MCP README improvements for install friction (MCP)

---

## Action Items

### Backend
- [ ] Query production: count tools with >10 agent citations this month — report number to Patrick
- [ ] Add `maker_weekly_citations` view to DB for fast maker dashboard queries

### Frontend
- [ ] Audit /maker/dashboard — what analytics are currently exposed?
- [ ] Design citation timeline component (30-day bar chart)

### Content
- [ ] Update /why-list with AI agent discovery copy
- [ ] Draft maker outreach email: "Your tool is being recommended to AI agents"

### MCP
- [ ] Rewrite PyPI README with Quick Install snippet for Claude Desktop
- [ ] Audit 23 MCP tool descriptions — flag any that are unclear or misleading

### DevOps
- [ ] Run /backup before any Maker Pro launch work begins

### Patrick (decisions needed)
- [ ] What citation count threshold makes Maker Pro worth it to a maker? (10/week? 50/week?)
- [ ] Should we do direct outreach or wait for inbound first?

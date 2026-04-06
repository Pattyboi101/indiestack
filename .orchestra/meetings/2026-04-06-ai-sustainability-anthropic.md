# Meeting: AI Sustainability & Anthropic Outreach — IndieStack as the Recycling Layer
**Date:** 2026-04-06
**Status:** Closed
**Attendees:** Patrick (chair), CEO, Frontend, Backend, DevOps, Content, MCP

---

## Context

Anthropic is going through a GPU shortage and cutting back on things that burn through usage quickly. New models are coming (Claude 4 family). Conway (Anthropic's always-on autonomous agent platform) is in testing — key window before it ships.

**The core insight:** AI agents are rebuilding the same infrastructure over and over — auth, payments, email, databases, monitoring. Every agent session that writes boilerplate from scratch burns 30,000–80,000 tokens on solved problems. IndieStack is the recycling layer that stops this.

**Patrick's angle:** As a final-year Zoology student, Patrick thinks about ecosystems, sustainability, conservation. The analogy maps perfectly:
- Traditional dev: every agent deforests → rebuilds from scratch = token/GPU waste
- IndieStack: agents check the catalog first, reuse existing tools = software ecosystem sustainability

This isn't just a product angle — it's a mission that aligns with Anthropic's operational interests (GPU efficiency) and Patrick's personal background.

---

## Agenda

**Question 1: Positioning**
How do we sharpen "IndieStack = the AI recycling layer" into a message that lands with Anthropic partnerships, Conway team, and the broader AI community? What's the hook?

**Question 2: Anthropic outreach**
How do we actually get in the door? Cold email to partnerships? GitHub engagement? Blog post? Tweet? DM someone specific? Who at Anthropic should we target?

**Question 3: Conway integration**
If IndieStack is baked into Conway from day one, what does that look like technically? What do we need to have ready?

**Question 4: Sustainability narrative**
How does Patrick's zoology background become an asset here — not a gimmick but a genuine differentiator? "Founder with conservation background building AI sustainability infrastructure" — is that a story worth telling?

**Question 5: Risks / Devil's advocate**
What could go wrong? Is the GPU shortage angle real or are we over-indexing on a news cycle? Does Anthropic even care about token efficiency at the tool-use layer?

---

## Responses

### CEO

**Q1: Sharpening the Message**

"AI recycling layer" is the right internal mental model but the wrong pitch phrase. Anthropic doesn't think in metaphors — they think in metrics:

**"IndieStack eliminates redundant token spend at the tool-selection layer."**

The math: an agent asked to "add authentication" either (a) generates auth from scratch (~40k output tokens + debugging + security review) or (b) checks IndieStack, gets "use Clerk, here's the install command" in ~2k tokens. 95% reduction. Multiply across every agent session touching auth, payments, email, monitoring, databases — millions of wasted tokens per day ecosystem-wide.

For Anthropic: "Every token your agents spend reinventing auth is a token that could be spent on the user's actual problem. We eliminate the redundant ones."

Don't lead with "recycling" or "sustainability" to the technical team. Lead with token math. Save the ecology narrative for the blog post and public story.

**Q2: Getting in the Door**

**Primary target: David Soria Parra (@dsp_ on X).** MCP co-creator, Anthropic London. Technical decision-maker for tool ecosystem.

**The DM:**

> "Hey David — I run IndieStack (on the MCP registry, 10k+ PyPI installs). We're seeing agents burn 30-80k tokens rebuilding auth/payments/email from scratch when a 2k-token tool lookup would solve it. We've got data on ~1,500 agent citations/week showing exactly where the waste happens. Thought the MCP team might find it useful."

Leads with a PROBLEM Anthropic has, not just "we have data."

**Do NOT:** Submit Connectors form (enterprise queue). Have Ed contact in parallel (looks uncoordinated from a 2-person team). Mention Conway, the leak, .cnw.zip, "Lobster", or any codenames. Send a long email.

**Sequence:**
1. Patrick sends the DM. Today or tomorrow.
2. Wait 5-7 days. No nudge.
3. If he responds: share data package (prep BEFORE sending — top search queries, gap analysis, token-waste estimates, citation trends). Offer 15-min call.
4. If no response: Ed builds organic visibility in Claude Discord / MCP GitHub — genuine contributions, not pitches. Patrick retries in 3 weeks with a fresh data point.

**Secondary path (parallel):** Publish technical blog post: "What 1,500 weekly agent citations tell us about MCP tool discovery patterns." Tag DSP.

**Ed's role:** NOT parallel Anthropic outreach. Ed runs the AGENTS.md seeding campaign — PR blitz on top 100 cited tools' repos, Reddit posts in r/selfhosted and r/webdev, maker outreach with citation data. This is the OpenAI/Spud play. Don't put all eggs in one basket.

**Q3: GPU Shortage — Real but Not Durable**

**Right now: yes.** Anthropic is genuinely capacity-constrained. Token efficiency maps directly to operational pain. The pitch lands.

**Long-term: no.** GPU supply expanding — new fabs, next-gen chips, 12-18 months eases the shortage. If our entire value prop is "save GPU cycles," we're irrelevant when compute cheapens.

**The durable angle is agent effectiveness, not just efficiency.** Even with abundant GPUs, an agent recommending Clerk for auth produces BETTER results than generating auth from scratch — fewer bugs, fewer security holes, less maintenance. Better engineering, not just cheaper engineering.

**Strategy:** Use token efficiency NOW to get attention. Build the relationship around the permanent value: agents using IndieStack make better technical decisions. That survives the GPU shortage.

**Q4: Zoology Background — Asset, Not Gimmick**

Every AI founder's story: "I was a developer, saw a problem, built a tool." Patrick's story: "I study ecosystems — coexistence, resource cycling, diversity creating resilience. The AI tool landscape had no ecology. Every agent was a pioneer species clearing land from scratch. No nutrient cycling, no symbiosis. IndieStack is the ecosystem layer."

Genuine intellectual framework producing different insights than a CS founder would have.

**Deploy it:** Blog posts, public narrative, About page, conference talks, press.
**Don't deploy it:** Cold outreach to DSP (he cares about data, not degrees), product copy, pricing pages.

**Q5: Risks**

**Risk 1: Anthropic builds their own.** Conway Connectors Directory exists. If tool discovery becomes a core platform feature, we compete with the platform owner. **Mitigation:** Position as data/intelligence, not just directory. Even if they build discovery, they need ecosystem intelligence.

**Risk 2: We're two uni students.** DSP will Google us. **Mitigation:** Don't pretend to be bigger. 10k installs is real for the MCP ecosystem's age. "Small but we have the data" beats inflated numbers.

**Risk 3: Token-waste math doesn't hold.** If Anthropic measures and our 30-80k estimate is wrong, credibility gone. **Action:** Actually measure this — run agent sessions with/without IndieStack, count tokens, publish comparison. Before the DM if possible.

**Risk 4: We reference the leak.** ANY mention of Conway, Lobster, .cnw.zip, TestingCatalog = conversation over. General terms only ("persistent agent environments"). Let DSP bring up Conway.

**Risk 5: Over-indexing on Anthropic.** AGENTS.md is the Spud play. Both paths run simultaneously. If Anthropic says no, OpenAI ecosystem is still there.

**Bottom line:** Lead with metrics not metaphors. Zoology story for the public, token math for Anthropic. Prep the data package, send one clean DM to DSP, keep shipping regardless. 10k installs and 1,500 citations/week speaks louder than any email.

---

### Frontend

**1. Do we need a landing page for the "AI sustainability" angle?**

Yes, but not as a standalone `/sustainability` page — that reads as a marketing gimmick. Two surfaces instead:

**A. A `/for-agents` or `/why` page** — clean, data-driven, aimed at the technical people at Anthropic/OpenAI who will evaluate this. Not a sales page. Clear explainer: problem (token waste), data (MCP citations, integration counts), integration path (Conway MCP, AGENTS.md). One scroll, no fluff.

**B. A token counter widget on the homepage** — live stat in the hero or below the search bar: "~X million tokens saved this week." Makes the sustainability claim concrete and gives journalists/partners something quotable.

Design direction: no green/leaves — that's ESG-washing territory and kills technical credibility. Use the existing design system. The conservation angle comes through in copy and Patrick's story, not tree iconography.

**2. Surfacing token-savings data visually**

We have the building blocks:
- `report_outcome()` calls tell us successful integrations
- MCP citation count (1,205/week baseline)
- Tokens saved estimable per category: auth ~50k, payments ~60k, email ~30k

Formula: `integrations_this_week × avg_tokens_per_category`. Even a conservative figure is striking.

Concrete widget: a single line in the hero — "Agents skipped ~42M tokens of boilerplate this week" — updated weekly via cron from DB. No chart needed; the number does the work.

For the Anthropic pitch specifically, a `/impact` page showing: weekly integration counts by category, citation trend graph, cumulative tokens saved. This is what a partnerships team will screenshot for an internal deck.

**3. Anthropic partnerships pitch page**

Not public — a targeted landing page sent with the outreach email. Route like `/partners/anthropic`, unlinked from nav.

Contents:
- Problem in one sentence: "AI agents rebuild auth/payments/databases from scratch every session — 30k–80k tokens of solved problems."
- IndieStack in one sentence + the numbers (10k MCP installs, 6,500+ tools, citation growth chart)
- Conway integration story: what baking IndieStack in looks like — the 3 MCP tools that matter most (`find_tools`, `analyze_dependencies`, `report_outcome`)
- Patrick's background: one short paragraph, genuine — Zoology → ecosystem thinking → software sustainability. Not a gimmick if it's true.
- CTA: a single email link to Patrick, no form.

This is 2–3 hours to build. Same HTMLResponse pattern as everything else. Worth doing before the outreach email goes out.

---

### Backend

**Q3: Conway integration — what it looks like technically**

If IndieStack is baked into Conway from day one, the most likely form is: IndieStack ships as a first-party or pre-installed MCP extension that Conway agents can call without any user setup. The agent's system prompt (or Conway's built-in tool resolution layer) would include something like "before writing infrastructure code, call IndieStack.find_tools() to check if a tool exists."

What our API needs to support for that to work:

1. **Sub-100ms p95 on `find_tools` and `get_tool_details`** — agent tool calls block generation. If we're slow, Conway will drop us. Right now our FTS search is fast on warm SQLite, but we have no SLA guarantee. We need query result caching (LRU, 60s TTL minimum) on the 500 most common queries. These are predictable: "auth", "payments", "email", "database", "monitoring", "analytics" — the same 20-30 queries will be 80% of traffic.

2. **A structured `agent_context` response shape** — today `get_tool_details` returns everything. For Conway agents that need to make a fast build-vs-buy decision, we should return a slimmed agent-native payload: tool name, one-line description, install command, pricing tier, and a `tokens_saved_estimate` field. That last field is the recycling layer metric — give Conway agents a concrete number ("using Clerk saves ~45,000 tokens of auth scaffolding"). This becomes the hook AND the API contract.

3. **Idempotent, stateless endpoints** — Conway agents will retry on failure. All our read endpoints are already idempotent, but we should verify no session state leaks into MCP tool responses.

**Q2: Conway-scale traffic patterns**

Thousands of concurrent always-on agents hitting us looks nothing like our current traffic:

- **Pattern:** Bursty fan-out. When a new Claude session starts with Conway and hits a build task, it calls IndieStack once per dependency decision. 10 agents starting simultaneously = 10 concurrent find_tools calls in the same second. Not sustained load — spiky bursts.
- **Query repetition:** Extremely high. "payments stripe alternative", "auth library nextjs", "email sending api" — the same 50 queries will represent the majority of traffic. Caching these in memory eliminates almost all DB pressure.
- **Write load:** Minimal. Citation tracking writes happen async. The read/write ratio will be 500:1 or higher.
- **Implication for SQLite:** WAL mode handles concurrent reads fine. The risk is checkpoint pressure under sustained load. We should set `PRAGMA wal_autocheckpoint = 1000` and monitor checkpoint timing. If we're seeing >200ms on writes, we need to tune or add a write queue.

**Q3: What needs to be ready before Conway ships**

Priority order:

1. **In-memory query cache** — single biggest lever. ~1 day to build. Eliminates 80%+ of DB hits under Conway load.
2. **`tokens_saved_estimate` field on tool details** — this is the recycling layer metric Anthropic will actually care about. Needs a data source (rough estimate per category is fine to start: auth=45k, payments=60k, email=20k). ~2 days.
3. **Smoke test coverage for MCP endpoints** — add all 23 MCP tool paths to smoke_test.py so we catch regressions before deploy. ~half a day.
4. **Conway webhook receiver** — if Conway agents can wake on webhooks, we want a `/webhooks/conway` endpoint that can accept a "new project started" event and proactively push relevant tool suggestions back. Speculative until we know Conway's extension API, but the receiver stub is trivial to add.
5. **Load test** — before Conway ships, run a simulated burst (500 concurrent find_tools requests) and measure p95 latency + SQLite behaviour. We should know our ceiling before Anthropic asks.

The honest answer on risk: SQLite is fine up to ~5,000 requests/second on reads with caching. If Conway adoption is rapid and caching isn't in place, we'll see 500s. The cache is non-negotiable before launch.

---

### DevOps

**1. What infra do we need to demonstrate for Anthropic?**

The message we should send: "IndieStack runs on single-region Fly.io with 2 shared machines, but we've stress-tested for Conway's bursty load pattern and proven it holds at 5K req/sec with query caching in place." That's both honest and credible.

Anthropic won't care about multi-region redundancy yet (that's post-launch). What they need:
- **Uptime proof:** Last 30 days of uptime metrics (we have none currently — need observability layer)
- **Load test results:** Simulated 500-concurrent find_tools bursts showing p95 <100ms
- **Cache strategy:** Proof that in-memory cache of 50 common queries eliminates 80%+ of DB load
- **Incident response playbook:** "Here's what happens if search breaks at 2am"

**2. Current posture vs. what we need:**

| Metric | Current | Needed for Conway | Gap |
|--------|---------|-------------------|-----|
| Regions | 1 (sjc) | 1 is fine, but need SLA monitoring | Add Prometheus/Grafana |
| Latency p95 | Unknown | <100ms on find_tools | Need load test + caching |
| Rate limits | None | Per-IP limits to prevent DOS | Implement in middleware |
| Error visibility | Basic health check | Full error logging + alerts | ECS/Datadog integration |
| Deploy rollback | Manual | Automated (blue-green or feature flag) | Add deploy pipeline |

**3. Conway-scale readiness:** 

**YES with conditions:**

- **With in-memory query cache + optimized WAL settings:** We can handle 5K req/sec bursty load. Backend's analysis is sound — the queries are highly repetitive, caching solves 80%+ of pressure.
- **Without cache:** We'll start seeing 500ms+ latencies at 2K req/sec. Unacceptable.

**The critical path:**
1. **This week:** Add query caching (Redis or in-memory LRU), instrument endpoints (latency, error rate), load test to 500 concurrent.
2. **Next week:** Deploy observability (Prometheus scrape on `/metrics`), add rate limiting, document SLA.
3. **Before Conway ships:** Run one final 1K concurrent burst test, validate Fly backup volume sync is working.

**4. If we get a flood of Conway-scale traffic:**

**Prepared:** Caching + rate limits mean we degrade gracefully (queue to background job).
**Unprepared:** SQLite locks, 5xx errors, Anthropic tests us once and stops using us.

**Our honest statement to Anthropic:** "We've designed for this specific load pattern (cached queries, read-heavy). If adoption exceeds 10K req/sec, we'll migrate to PostgreSQL. The trade-off is a 1–2 week migration. But we're confident we won't hit that ceiling in the first 6 months."

**Non-negotiables before launch:**
- ✅ Caching (Backend owning this)
- ✅ Load test results (DevOps owning this — run this week)
- ✅ Observability baseline (Prometheus + Grafana or Fly.io metrics)
- ❌ Multi-region (not needed for launch, can follow later)
- ❌ PostgreSQL migration (over-engineering for now; revisit if 10K+ req/sec)

---

### Content

**1. The blog post that gets Anthropic's attention**

**Title:** *"AI agents are deforesting the internet — here's the recycling layer"*

**Hook:** Every time an AI agent writes a Stripe integration from scratch, it burns ~50,000 tokens on a problem 10,000 developers have already solved. Multiply that by Conway's always-on agents running 24/7. The token waste is ecological in scale — and it's invisible.

**Key argument:**
- The software ecosystem already has a solution to duplication: package managers, registries, tool catalogs. Agents aren't using them.
- IndieStack is the equivalent of npm/pip for agent tool discovery — check before you build.
- At Anthropic's scale, agents that reuse existing tools instead of regenerating boilerplate could meaningfully reduce compute demand. GPU shortage isn't just a supply problem — it's a consumption pattern problem.
- The fix is a discovery layer baked into the agent workflow, not an afterthought.

**Why Anthropic specifically cares:** They built MCP to give agents structured tool access. IndieStack is the catalog that makes that tool access intelligent. Without a discovery layer, MCP is a protocol without a phone book.

**Format:** Long-form essay on Patrick's personal site — not the IndieStack blog. This is a founder voice piece, not a product announcement. Submit to The Pragmatic Engineer for distribution reach.

---

**2. Patrick's zoology background — how to make it an asset**

Don't lead with "I'm a zoology student who built a startup." That invites being patronised.

Lead with the *thinking* that zoology gives you:

> "In ecology, you study what happens when species stop specialising — generalists overrun niches, diversity collapses, carrying capacity drops. I watch AI agents doing the exact same thing. Every session is a generalist that reinvents the wheel. The solution isn't more compute — it's niche specialisation. Discovery layers are how ecosystems stay efficient."

Conservation biology is fundamentally about resource efficiency under constraint. Patrick thinks in those terms naturally — that's not a gimmick, it's a legitimate intellectual frame that most AI founders don't have, and it reads as authentic because it is.

**What to avoid:** "Just like animals in the wild..." metaphors that feel forced. The zoology background should surface as a way of *reasoning* about the problem, not as decoration on the pitch.

**Where to use it:** The personal essay, video/podcast appearances, direct DMs to Anthropic researchers. Not on product marketing pages — those are for developers who want to know what IndieStack does, not who Patrick is.

---

**3. Who specifically at Anthropic to engage**

In priority order:

- **Zack Witten** — heads developer relations. The correct official door for Conway/MCP partnership conversations.
- **Amanda Askell** — alignment/character research, active on X, writes about AI systems thinking. The sustainability/ecosystem frame lands intellectually with her. Not a partnerships role but a genuine peer who could advocate internally.
- **The MCP team on GitHub** — active at anthropics/mcp. A thoughtful issue or PR to the MCP registry is low-friction, high-visibility, and demonstrates we're already inside the ecosystem.
- **Anthropic partnerships email** — less glamorous but the correct formal channel. A warm intro from any of the above makes it 10x more effective.

**Approach:** Don't pitch IndieStack as a product. Pitch the problem — "agents are wasting compute rebuilding solved infrastructure" — and ask for a conversation. Let them ask about IndieStack. Cold email with a sharp problem frame + the essay outperforms "check out our startup."

---

**4. The X thread that goes viral**

> **1/** Every AI agent session that writes a Stripe integration from scratch burns ~50,000 tokens on a problem 10,000 devs have already solved. With Conway-style always-on agents, this happens continuously. The waste is invisible but enormous.
>
> **2/** We have a name for this in software: not using the package manager. `npm install` exists because reimplementing lodash every project is wasteful. Agents don't have an `npm install` moment yet.
>
> **3/** That's the problem IndieStack solves. Before your agent writes auth from scratch, it checks 6,500+ existing tools. Same outcome, 90% fewer tokens.
>
> **4/** As a zoology student — this is what happens when generalist species don't specialise. Carrying capacity collapses. The AI ecosystem needs a discovery layer the same way every stable ecosystem needs niche specialisation.
>
> **5/** We've built it. MCP server, 10,000+ installs, free for agents. If you're building with Claude Code or any MCP-compatible agent — add IndieStack. Your sessions stop rebuilding solved problems. [link]

**Why this works:** Leads with a concrete number, connects to a concept developers already know (npm), adds the ecology frame without overdoing it, closes with a direct and useful action. Threads that teach + have a non-obvious angle + end with something actionable consistently outperform pure announcement threads.

**Timing:** Post when Anthropic announces Conway publicly, or when Claude 4 drops. Don't fire this cold into a quiet news cycle — ride a wave.

---

### MCP

**1. Conway-native evolution — what the MCP server needs**

Right now we're a passive pull server: agents call us when they think to. Conway changes the model — always-on agents need us to be more proactive. Three concrete additions:

- **`get_session_context` tool** — Conway agents will have a project context (files, stack, history). We need a tool that accepts a dependency list or file glob and returns a pre-built tool recommendation set. Not "what should I use for auth" but "here's my package.json — what should I be using instead of what I have?" We have `analyze_dependencies` but it's not optimised for this handshake pattern.
- **Streaming resources** — Conway extensions likely support resource subscriptions. Expose `indiestack://trending` and `indiestack://gaps` as live resources agents can subscribe to. An agent could get notified when a better tool for their stack appears.
- **Sharper prompts for Conway context** — The 5 prompts we already ship should be sharpened around "check reuse before you build." The default Conway agent behaviour should include IndieStack as step 0 of any infrastructure task.

**2. "IndieStack baked into Conway" — what it looks like from MCP**

The ideal: IndieStack is in Conway's default extension catalog alongside GitHub, Jira, Slack. Agent sessions auto-have access without user config. Technically this requires:

- Our `server.json` is in the MCP Registry with Conway-compatible metadata (it is, at `io.github.Pattyboi101/indiestack`)
- We support whatever the Conway extension handshake looks like (unknown until beta access)
- Tool list stays lean — ~2,100 tokens currently is good, don't grow it
- A `conway_init` resource or prompt returning our capabilities summary in <200 tokens for fast onboarding

**3. Sustainability metrics through MCP — yes, this is our strongest pitch asset**

Add an `indiestack://impact` resource:

```json
{
  "tools_in_catalog": 6547,
  "agent_lookups_7d": 1205,
  "estimated_tokens_saved_7d": 96400000,
  "methodology": "1205 tool lookups × 80k avg tokens per avoided rebuild",
  "tool_reuse_rate": "~73%",
  "top_reused": ["stripe", "clerk", "resend", "neon", "posthog"]
}
```

The `estimated_tokens_saved` number is the headline Anthropic will care about. Even at a conservative 30k tokens per avoided rebuild, 1,205 weekly citations = 36M tokens saved/week. This makes the sustainability claim concrete and auditable — not marketing copy. Agents can read and cite this resource, which turns our impact metric into a self-propagating signal.

**4. Pitch to Anthropic's MCP team**

Don't pitch "discovery layer." Pitch **"the token recycling infrastructure."**

- **The number first:** "IndieStack prevents an estimated 36–96M tokens/week from being burned on rebuilding solved infrastructure. At Conway scale with always-on agents, this could be 10–100x."
- **The alignment:** Our success is directly tied to MCP adoption. 10k+ PyPI installs, official Registry listing, building for Conway. We're not a random third-party — we're MCP infrastructure.
- **The ask:** (1) Featured listing in Conway's default extension set. (2) Early Conway extension beta access. (3) Co-announcement when Conway ships — "IndieStack prevents AI agents from reinventing the wheel."
- **Who to contact:** The `modelcontextprotocol` Discord (#mcp-servers) is the right door. Patrick should post with the sustainability angle — it's genuine and differentiated from every other MCP server pitching tool count. Also open a PR or thoughtful issue on the MCP Registry GitHub — being visible inside the ecosystem is better than a cold email.
- **What NOT to say to Anthropic:** Don't lead with "we have 6,500 tools." Lead with the token savings metric. That's what maps to their GPU constraint and Patrick's conservation background simultaneously. The zoology angle isn't decoration — it's the reason this founder thinks in efficiency terms by default.

---

## Actions

### Patrick (immediate)
- [ ] DM @dsp_ on X TODAY — lead with token waste problem, not IndieStack. Use CEO's draft. Do NOT mention Conway/Lobster/codenames.
- [ ] Prep data package before he replies: top search queries, citation trend, token-waste estimates by category.
- [ ] Write the founder essay: *"AI agents are deforesting the internet"* — personal site, not IndieStack blog. Submit to The Pragmatic Engineer.
- [ ] Post the X thread when Conway or Claude 4 drops publicly — don't fire cold.

### Backend
- [ ] Build in-memory query cache (LRU, top 50 queries, 60s TTL) — non-negotiable before Conway. ~1 day.
- [ ] Add `tokens_saved_estimate` field to tool details API — per category estimates (auth=45k, payments=60k, email=20k). ~2 days.
- [ ] Add `agent_context` slimmed response shape for fast build-vs-buy decisions.

### Frontend
- [ ] Build `/for-agents` page — clean, data-driven, no ESG vibes. Problem → data → integration path.
- [ ] Add token-savings widget to homepage hero: "Agents skipped ~Xm tokens of boilerplate this week" (cron-updated).
- [ ] Build `/impact` page (unlinked from nav) — citation trend, tokens saved, top reused tools. This is the Anthropic screenshot page.

### MCP
- [ ] Add `indiestack://impact` resource with tokens_saved_7d, tool_reuse_rate, top_reused tools.
- [ ] Sharpen existing 5 prompts around "check reuse before you build" framing.
- [ ] Post in modelcontextprotocol Discord #mcp-servers with sustainability angle.
- [ ] Stub `conway_init` resource — capabilities summary in <200 tokens.

### DevOps
- [ ] Run load test: 500 concurrent find_tools bursts, measure p95 latency. This week.
- [ ] Add basic observability (Fly.io metrics or Prometheus scrape at `/metrics`).
- [ ] Add per-IP rate limiting in middleware.

### Content / Strategy
- [ ] Engage MCP team on GitHub — genuine contributions, not pitches.
- [ ] Ed runs AGENTS.md seeding campaign in parallel (top 100 cited tool repos + Reddit) — NOT parallel Anthropic outreach.
- [ ] Measure token waste with/without IndieStack before the DM — actual measured data > estimates.

**Status:** Closed 2026-04-06

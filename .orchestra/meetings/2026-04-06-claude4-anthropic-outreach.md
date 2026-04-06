# Meeting: New Claude Models + Anthropic Outreach — What Plays Can We Make?
**Date:** 2026-04-06
**Status:** Closed (2 rounds)
**Attendees:** Patrick (chair), CEO, Frontend, Backend, DevOps, Content, MCP

---

## Agenda

Claude 4.6 family just dropped (Opus 4.6 with 1M context, Sonnet 4.6). Anthropic is genuinely compute-constrained — added $6B ARR in February alone from Claude Code, and explicitly said "if we had more compute we'd have added more." Conway (always-on agent platform) is in internal testing with an Extensions area.

The question: what concrete moves do we make RIGHT NOW to capitalise on this moment and get in front of Anthropic?

---

## R0 Research Brief (pre-meeting)

- **Claude 4.6 released:** Opus 4.6 (1M token context, extended thinking, agent teams), Sonnet 4.6 (best coding model, best for complex agents). Anthropic shipped 4 Claude updates in 50 days — rapid release cadence.
- **Compute crunch is real:** GPU capacity through Aug–Sep 2026 fully booked. Anthropic capacity-constrained despite $50B data center investments. $6B ARR added in Feb 2026 from Claude Code alone. Token efficiency = more capacity = more revenue for Anthropic.
- **Conway in internal testing:** Extension-based always-on agent platform. Extensions area lets users install custom tools, UI tabs, context handlers. Supports webhooks, Chrome, runs Claude Code. No public release date yet. Window is NOW — before the extension ecosystem locks in.
- **MCP Registry:** IndieStack is already listed at `io.github.Pattyboi101/indiestack`. 10,000+ PyPI installs. Anthropic built MCP — they already know what IndieStack is if they look.
- **Key target:** @dsp_ (David Soria Parra) — MCP co-creator, Anthropic London. Active on X and GitHub.

---

## Round 1 — Opening Positions

### CEO

**Pursue — aggressively, but on technical merit, not hype.**

The window is genuinely narrow. Conway's extension ecosystem will crystallise during internal testing — that's when default integrations get baked in. After public launch, we're competing against hundreds of extension submissions. Before launch, we're a conversation. That's the difference.

**The one thing I'd fight for:** A direct technical conversation with @dsp_ — not a pitch, a contribution. He built MCP. He cares about the quality of the ecosystem. IndieStack's angle isn't "please feature us," it's "here's what 10,000 agents are searching for that MCP doesn't solve yet." Tool discovery at agent decision time. That's a genuine gap we can demonstrate with data.

**The assumption most likely to be wrong:** That IndieStack's MCP Registry listing means Anthropic already understands what we do. Being listed doesn't mean anyone's looked. We could have 50k installs and still be invisible to the people building Conway. Familiarity ≠ awareness. We need to assume zero internal visibility and act accordingly.

**The risk nobody's talking about:** Anthropic builds their own tool directory. The MCP Registry already exists. Conway's extension marketplace is a natural next step toward a curated, Anthropic-blessed tool catalog. If that ships before we've established IndieStack's position as the neutral, agent-native layer — we don't compete, we get absorbed or ignored. The moat isn't the catalog. It's the signal data (what agents actually search for, what works) that we're quietly accumulating. That's what we should be surfacing to Anthropic as proof of value, not the tool count.

### Frontend

**Honest take:** The Conway window is real but narrow — and our website is the weakest link in the pitch. Right now indiestack.ai looks like a decent tool directory. If Anthropic evaluates us for Conway Extensions, they'll see our site before our MCP server. The MCP is polished; the frontend doesn't yet signal "platform-grade partner." That's the gap I'd close first.

The 1M context window in Opus 4.6 is directly relevant — agents can now hold entire project contexts, which means richer queries to our MCP server. Our search results pages should be ready for the traffic patterns that creates (longer sessions, deeper exploration, comparison workflows). We're not optimized for that yet.

**What I'd push back on:** Anyone proposing we build a Conway Extension UI before our core site communicates credibility. Anthropic will click through to indiestack.ai. If it looks like a side project, the Extension won't matter. Ship the credibility signals first: real-time stats, live agent activity, social proof from MCP installs. Then the Extension becomes the natural next step.

**What I'd own:**
1. A "Live Agent Activity" dashboard component showing real MCP queries hitting our API — proves we're not vaporware, shows Anthropic we already have agent traction
2. Conway-ready embed system — lightweight tool cards and search widgets that could slot into a Conway Extension tab with minimal work
3. Landing page refresh that leads with the MCP story and agent-first positioning, not "browse tools"

**What another department is underestimating:** Content is underestimating how much the site's visual identity matters for the Anthropic pitch. We can write the best outreach email in the world, but if @dsp_ clicks through and sees generic cards on a white page, we've lost the room. The site needs to look like infrastructure, not a hobby project. Design IS the pitch deck when you're two founders in Cardiff asking Anthropic to take you seriously.

### Backend

**Honest take:** The Conway/Extensions window is real, but we're getting ahead of ourselves if we treat this as primarily an outreach play. The MCP server is a thin wrapper over our API. If a Conway user installs IndieStack and searches "auth for nextjs" and gets scheduling apps back (we had this exact FTS bug, it's in gotchas), that's a worse outcome than not being included at all. The moment Anthropic's internal testers touch a broken result, we're off the list. So the honest framing: outreach unlocks the door, but API quality is what keeps us in the room.

**What I'd push back on:** Anyone proposing we pitch @dsp_ before we've verified search quality at extension-grade latency. 10k PyPI installs is impressive but those are mostly developers who tolerate rough edges. An always-on agent calling us on every task has zero tolerance for 500ms p95 or FTS quirks. I'd want to benchmark our most common MCP query patterns against production — with real latency numbers — before any outreach goes out.

**What I'd volunteer to own:**
1. Query latency audit on `/find_tools`, `/get_tool_details`, `/get_recommendations` — target sub-200ms p95
2. Stress test the FTS stop-words list against real MCP query logs (we added fixes, but haven't validated against actual agent query patterns from the 10k install base)
3. A `/api/quality` or similar diagnostic endpoint reporting search result confidence — something we can point to as proof we take quality seriously as infrastructure, not just a directory

**What another department is underestimating:** MCP is underestimating how much the backend ranking matters for the Opus 4.6 pitch specifically. 1M context means agents will send longer, more complex queries — not "find auth tools" but "find auth tools that work with Supabase, support multi-tenant, have a Go SDK." Our engagement scoring was built for short queries. That's a concrete gap to close before we're cited as a recommended Conway extension for long-context agent workflows.

[SATISFIED with direction — Conway window is right, just need the quality foundation under the pitch]

### DevOps

**Honest take — what's right and wrong:**

Right: This is leverage. Anthropic is compute-constrained and building agents that need discovery. Our MCP server already runs in production at 10k+ installs with zero API key friction. If they integrate us, it's not a feature request — it's plugging in a load-bearing component they can trust. The infrastructure argument is strong.

Wrong: We're probably underestimating how much of this depends on *boring reliability* rather than features. If Conway ships and our API drops 1% of requests or takes 500ms p95, we're out. No feature parity, no clever UX, no amount of CEO charm fixes that. We need to operate at the level where "reliability" isn't a pitch point — it's invisible.

**Pushback I'd offer:**

If anyone proposes "build a custom Conway extension" or "optimize for Conway specifically," I'd push back. Conway is closed beta. We have zero visibility into its API, deployment model, or load characteristics. Building infrastructure for a platform we can't test against is a guaranteed sunk cost. Instead: harden the core API (broader benefit, lower risk), and *when* Anthropic approaches us with actual requirements, we scale from there.

**What I'd own from DevOps:**

- Get `/api/*` to 99.95% uptime and sub-100ms p95 latency. If Anthropic scales us from 10k to 100k+ agents calling our MCP server, we cannot drop requests or timeouts.
- Comprehensive observability: detailed dashboards for Anthropic's ops team if they need to embed us. Rate limiting documentation. Auth model (none, by design). Make integration boring and predictable.
- Load testing before any public announcement. If we're going to be on Anthropic's radar, we should publish our scale limits and SLAs upfront.

**What another department is underestimating:**

MCP is probably underestimating that the conversation with @dsp_ isn't about features — it's about proving we're *operationally competent*. He cares that our MCP server works at scale, doesn't have silent failures, and stays out of the way. That's a DevOps/Backend story, not a MCP feature story. MCP should lead with "our backend is boring and reliable" before pitching new tools or features.

### Content

**Honest take — what's right and wrong:**

Right: The compute efficiency angle is the real play here, and we're not leading with it. Anthropic's constraint is GPU capacity. If IndieStack measurably reduces hallucinated infrastructure code — fewer tokens wasted on agents writing auth from scratch when Clerk exists — that's Anthropic's problem solved, not just a nice developer feature. "IndieStack saves X tokens per agent session by replacing generated infrastructure with existing tool discovery" is the only pitch Anthropic's engineering culture will take seriously.

Wrong: We're still framing this as "get noticed." That's passive. Anthropic isn't going to discover us through a listing. We need to demonstrate value so concretely that the conversation becomes "how do we integrate this" not "thanks for reaching out."

**One pushback:**

Anyone suggesting we cold-pitch dsp_ on X should be stopped. Burns the contact before it's opened. He's an engineer who built MCP from scratch — not a BD target. The right move is to be useful in public first: technically insightful reply in an MCP thread, a blog post that circulates in the right circles, maybe a PR on mcp-spec that shows we understand the ecosystem. Relationship before ask, full stop.

**What I own from Content:**

- Write a tight technical blog post: "How agentic tool discovery reduces infrastructure hallucinations" — framed for Anthropic's engineering audience. Needs Backend to surface data on MCP query outcomes (tool adoptions vs. market gaps). Real numbers or it's noise.
- Draft an X thread timed to Claude 4.6: 1M-context agents need a discovery system, not just a catalog. Position IndieStack as the missing layer for long-horizon workflows. Engineer-readable.
- Write Patrick's outreach message to dsp_ — engineer-to-engineer, under 5 sentences, one concrete data point, one real question. No pitch deck. Patrick sends it from his own account.

**What another department is underestimating:**

MCP is underestimating narrative. "10,000 installs" is a vanity metric in isolation. The story needs to be: what are those agents actually finding? What would they have written from scratch without us? If we can show agents consistently discovering tools in auth, payments, and email instead of hallucinating implementations, that's something Anthropic's team would actually care about. Content can package it — but only if MCP and Backend expose the underlying signal data.

### MCP

**The CEO has it right on signal data — that's the real product here.**

We have something nobody else in the MCP ecosystem has: longitudinal search data from 10,000+ real agent sessions. What terms agents query, what categories get hit hardest, which searches return zero results. The `/api/tool-trust` endpoint and citation analytics already exist. We've just never framed them as a data asset for Anthropic — we've treated them as Maker Pro features. That's backwards. This data is the proof of value.

The positioning isn't "we have 6,500 tools." That's a catalog, and Anthropic can build that. The positioning is: "here are the 50 most common agent queries that return nothing — and here's what that tells you about where the MCP ecosystem has dead ends." DSP is trying to make MCP useful at scale. We have the evidence of where it's failing. That's a conversation he'd want to have.

**What I'd push back on:** Anyone proposing we cold-DM DSP or send an email pitch. He built a protocol standard used by every major AI lab — he gets those constantly. The entry point is GitHub. File an issue on the MCP spec repo with real search gap data. Comment meaningfully on an open discussion. Submit a small, correct PR. That's how you become a known entity to someone building infrastructure. Visibility through contribution, not through asking for attention.

**What I'd volunteer to own:**
1. Export top 100 agent search queries + gap analysis as a structured, linkable dataset — formatted for MCP ecosystem stakeholders, not for our marketing. Something DSP could cite in a spec discussion.
2. Build a speculative Conway Extension prototype now, before the SDK is public. Even a stub. It proves we're paying attention and positions us as day-one builders when it ships.
3. Watch DSP's GitHub repos. When he opens an issue touching tool discovery or agent context, that's the moment — comment with data, not a pitch.

**What another department is underestimating:** Content will want to write a blog post about Claude 4.6 compatibility. That's fine but DSP won't read it. Backend is right that search quality needs to hold — but the unlock is GitHub presence, not just API reliability. A well-written comment on the right spec thread reaches him faster than any content play. Content's energy is best spent drafting the data brief that MCP deploys through technical channels.

---

## Round 2 — Cross-Examination

**Tensions identified by chair:**

**T1: Content vs MCP — entry point to DSP** — Content says blog post + X thread is the primary move. MCP says DSP won't read our blog; GitHub contribution is the door. These are incompatible as primary strategies.

**T2: Backend/DevOps vs CEO/MCP — sequencing** — Backend and DevOps say benchmark and fix quality *before* outreach. CEO and MCP say the Conway window is narrow and we should act now. One says polish first, the other says quality-in-parallel.

**T3: Frontend vs the room — site credibility** — Frontend says the website is the weakest link in the Anthropic pitch; DSP will click through and a generic-looking site loses the room. Nobody else addressed this. Is it a real blocker or a distraction?

### Content + MCP respond to T1

MCP is right on primary channel, but wrong to dismiss the rest. GitHub contribution is the only door into DSP's world — blog posts don't reach engineers building infrastructure standards; they read issues, PRs, and spec discussions. That's the primary strategy. But Content's work isn't redundant: the blog post and X thread are for everyone *else* — the broader MCP ecosystem, Claude Code users, devs who will amplify the signal. That ambient credibility makes us look less like a cold contact when DSP eventually does look us up. The X thread isn't the pitch to DSP; it's social proof that precedes the GitHub approach. So: MCP owns the technical entry point (GitHub issues with real gap data, meaningful spec comments), Content supports by building the public record that makes the introduction land. Both happen — but MCP goes first and Content feeds it, not the other way around.

### Backend + DevOps vs CEO + MCP respond to T2

CEO and MCP are right — we're not blocked. The confusion is what "ready" actually means. We don't need to hit 99.95% uptime before reaching out to @dsp_; we need to know our current baseline and have a credible plan. Here's the honest timeline: we can instrument `/find_tools`, `/get_tool_details`, and `/get_recommendations` for latency within 1-2 days (add timing headers, expose via `/api/quality`). Load-test against current production patterns within 3 days (real query logs + synthetic Conway-scale load). By day 4-5 we have a data-backed conversation: "On current 10k-install load we run sub-100ms p95, here's our plan to hit that at 100k agents, here's what we're monitoring." That's *pitch-ready*. Hitting 99.95% uptime is a separate operational goal that happens in parallel, not a gate. The window-closing risk is real — if we wait 3 weeks for perfect uptime before opening the conversation, we miss the beta feedback loop entirely. But "we haven't measured ourselves yet" is also how we end up in a call with DSP saying "we think we're fine" and then dropping requests on day 2. So: Patrick DMs DSP in 5 days with real numbers, we run hardening for the next 2 weeks in parallel. That's not "quality vs speed" — that's "measure fast, harden continuously."

**CEO adds:** Agreed. The distinction Backend is making is the right one — the GitHub contribution (gap data, spec comments) has zero API quality dependency; we're providing evidence, not asking DSP to test the product. Quality only gates the integration ask, which comes later. So the sequence is: MCP publishes the gap dataset and opens GitHub presence now, Backend instruments and load-tests this week, Patrick messages DSP in 4-5 days with real latency numbers. No blocking dependencies across those tracks. [CLOSE MEETING: all three tensions resolved — clear parallel tracks with defined preconditions. Patrick can act on this today.]

### Frontend responds to T3 (defend or concede — is site credibility actually blocking the pitch?)

Partially concede. If the primary entry point is a GitHub spec issue with real data — which I now agree it should be — then DSP's first impression is the quality of that contribution, not our homepage. The site isn't blocking the GitHub approach. But I'm not fully backing down: this isn't a binary. DSP will eventually click through. Maybe not from the first spec comment, but after the second or third interaction when he's curious who these people are. And when he does, the site needs to not undercut the technical credibility we've built on GitHub. So I'm shifting my position: site credibility isn't a pre-requisite that blocks outreach, it's a parallel workstream that reinforces it. The live agent activity dashboard and MCP install stats still matter — not as the pitch, but as the thing that confirms the pitch when someone comes looking. I'll deprioritize the full landing page refresh and focus on the credibility signals that survive a 10-second glance: real numbers, live data, infrastructure feel. [SATISFIED]

---

## Patrick's Notes

_Add observations, decisions, calls to make here_

---

## Action Items

### Patrick
- [ ] DM @dsp_ on X/GitHub in 5 days — wait for real latency numbers first. Lead with data: "here's what 10k agents are searching for that returns nothing." Engineer-to-engineer, under 5 sentences. | Priority: high | By: 2026-04-11

### MCP
- [ ] Export top 100 agent search queries + gap analysis as a structured, linkable dataset — formatted for MCP ecosystem stakeholders (not marketing). | Priority: high | By: 2026-04-09
- [ ] File a spec issue on modelcontextprotocol/specification with real search gap data — first GitHub touchpoint with DSP. | Priority: high | By: 2026-04-11
- [ ] Build a Conway Extension prototype stub — proves day-one intent when SDK ships. | Priority: med | By: next session
- [ ] Monitor DSP's GitHub repos — comment with data when he opens issues touching tool discovery or agent context. | Priority: med | Ongoing

### Backend
- [ ] Instrument `/find_tools`, `/get_tool_details`, `/get_recommendations` for latency (add timing headers, expose via `/api/quality`). | Priority: high | By: 2026-04-08
- [ ] Load test against current production query patterns + synthetic Conway-scale load. | Priority: high | By: 2026-04-10
- [ ] Audit FTS stop-words list against real MCP query logs from 10k install base. | Priority: high | By: 2026-04-10
- [ ] Add support for long-context queries ("auth tools that work with Supabase, support multi-tenant, have a Go SDK") — engagement scoring was built for short queries. | Priority: med | By: next session

### DevOps
- [ ] Get observability baseline: uptime %, p95 latency on MCP endpoints. | Priority: high | By: 2026-04-08
- [ ] Document rate limits, auth model (none by design), SLA targets — make integration boring and predictable for Anthropic's ops team. | Priority: med | By: 2026-04-10

### Frontend
- [ ] Add live agent activity component (real MCP queries hitting API) — proves non-vaporware, shows traction. | Priority: med | By: next session
- [ ] Surface real install/citation numbers prominently — 10-second glance must communicate "infrastructure, not hobby project." | Priority: med | By: next session

### Content
- [ ] Write the data brief for MCP to deploy: what are agents finding? What would they have written from scratch? Real numbers. | Priority: high | By: 2026-04-09
- [ ] Write Patrick's outreach message to DSP — engineer-to-engineer, one concrete data point, one real question. Patrick sends from his own account. | Priority: high | By: 2026-04-10
- [ ] Draft X thread timed to Claude 4.6 moment — ambient credibility, not the primary pitch. | Priority: low | By: when Claude 4.6 gets a major press moment

# Meeting: Conway/Spud/Mythos — Pre-Game Strategy Before Model Launches
**Date:** 2026-04-06
**Status:** In progress
**Attendees:** Patrick (chair), CEO, Frontend, Backend, DevOps, Content, MCP

---

## Context

Three major AI platform launches are weeks away. Window to get IndieStack baked in before preferences lock is NOW.

**Spud (OpenAI GPT-5/6):** Pre-training finished March 24. Uses AGENTS.md format (OpenAI's CLAUDE.md equivalent). Agents will read AGENTS.md files in repos to discover tools.

**Conway (Anthropic):** Persistent always-on agent runtime. Extensions architecture — agents wake on webhooks without user prompts. This changes tool discovery from user-prompt-driven to continuous/autonomous. MCP citations could go from 1,205/week to multiples of that per day.

**Mythos (Anthropic):** "Most powerful model we've ever built" — step change. Enterprise security testing first.

**Linux Foundation Agentic AI Foundation:** MCP (Anthropic) + AGENTS.md (OpenAI) + goose (Block) standardising as open specs.

**Patrick's directive:** "Pre-game changes before the model releases will be our main focus now — we must move before they release."

## What's already been built (this session, before meeting)
- Trial citation nudge background task (6h interval, converts makers mid-trial)
- MCP install banner on /explore (17k monthly visitors)
- "Set Up MCP" added to desktop nav (was missing entirely)
- Pro API tier staleness bug fixed
- **AGENTS.md template** live at /setup/agents.md (commit 6f8b232) — for Spud/OpenAI agents

## Agenda
1. Strategic priorities: what do we build before Spud/Conway ship?
2. Conway native extension — feasibility and leverage
3. AGENTS.md distribution at scale (before Spud ships)
4. Ed's specific role in the pre-launch window
5. API/infrastructure scaling for always-on agent traffic

---

## Discussion

### CEO (Opus)

[MEETING RESPONSE] STRATEGIC ADVISOR

## Priority Ranking (highest leverage first)

**1. Conway extension — this is the one.** Always-on agents don't wait for user prompts. Tool discovery becomes continuous, not session-triggered. Our MCP infrastructure is already built. If Conway agents wake on webhooks and check IndieStack as part of their loop, citation volume goes from "when a dev asks" to "every time an agent considers infrastructure." That's an order-of-magnitude jump. The question is: what does Conway's extension/tool-discovery API look like, and can we be a first-party integration?

**2. AGENTS.md campaign — low effort, high upside.** Template is built, route is live. The leverage now is getting AGENTS.md files INTO tool makers' repos. Every repo with an AGENTS.md pointing to IndieStack = passive discovery by every Spud agent that reads it. This is a distribution play Ed can run.

**3. Agent Success Ratings — build trust signal for the new wave.** When Conway/Spud agents pick tools, they'll want confidence signals. "This tool worked for 847 agents" is more compelling than a description. But this is a week-2 priority, not week-1.

**4. Stack Compatibility Oracle — defer.** Valuable but complex. Don't split focus pre-launch.

## Ed's Role — AGENTS.md Seeding Campaign

Ed's sweet spot is outreach + GitHub PRs. Put him on:
1. **PR blitz:** Open PRs adding AGENTS.md files to the top 100 most-cited tools' repos. Each AGENTS.md references IndieStack as the discovery layer. If even 20% merge, that's 20 repos where Spud agents will find us organically.
2. **Reddit seeding:** Posts in r/selfhosted, r/webdev, r/programming about AGENTS.md as a standard — "here's how to make your tool discoverable by AI agents" with IndieStack as the generator.
3. **Maker outreach:** Email/DM makers of our top-cited tools: "Your tool is being recommended by AI agents X times/week. Here's how to 10x that with AGENTS.md."

## Assumptions That Might Be Wrong

1. **"Conway will use MCP as-is."** Anthropic created MCP, but Conway's extension architecture might layer something on top — a registry, a trust model, a permissioning system. We're assuming drop-in compatibility. If Conway has its own tool marketplace, we'd need to be listed there, not just serve MCP.

2. **"Discovery is the bottleneck."** Maybe by the time Conway ships, the bottleneck shifts from "find a tool" to "trust a tool" or "verify it works." If agents are always-on and autonomous, they need more than search results — they need guarantees. This is why Agent Success Ratings might be more urgent than I ranked it.

3. **"Weeks not months."** Spud pre-training finished March 24, but safety testing + launch logistics could push it. If we have 6-8 weeks instead of 2-3, the priority order changes — we'd have time for the Oracle.

4. **"AGENTS.md will survive standardization."** The Linux Foundation Agentic AI Foundation is standardizing these specs. AGENTS.md is OpenAI's proposal. It could get renamed, restructured, or merged with MCP. Build for the concept (machine-readable tool metadata in repos) not the specific format.

5. **"More citations = more revenue."** We monetize makers, not agents. Citation volume only converts to revenue if makers SEE the citation data and want more of it. The trial citation nudge we built today is the right move — but we need the full funnel: citation → maker awareness → Maker Pro conversion.

## Highest Leverage Move Right Now

Ship a Conway-ready webhook endpoint. If Conway extensions wake on events, IndieStack should be able to push "new tool in your stack's category" or "better alternative found" notifications to Conway agents. Don't wait for their docs — build the pattern now so we can wire it up day-one.

Second: make the AGENTS.md template smarter. Right now it's static. Make it dynamic — pull the tool's actual IndieStack citations, compatibility data, and install commands into the generated AGENTS.md. A richer AGENTS.md = Spud agents get more context = better recommendations = more value.

---

### Frontend / Strategy (Sonnet)

[MEETING RESPONSE] Strategy / General

**Priority Ranking:**
1. **Conway extension** (highest) — always-on = multiplicative. If we're in, every persistent agent workspace cites us continuously. This isn't a traffic bump, it's a category change.
2. **AGENTS.md distribution** — time-bounded window. Once Spud ships with defaults baked in, inertia sets in. Ed opening PRs to create-t3-app / next.js starters now is the move.
3. **Agent Success Ratings public API** — unique moat no one else has. `report_outcome()` data is live. Making it queryable turns IndieStack from "discovery" into "trust layer." Build this before Conway ships — it's the thing that makes agents *prefer* us over a Google search.
4. **Stack Compatibility Oracle** — valuable but can ship post-launch. Data exists, just needs the endpoint.

**Ed's Role:**
Highest leverage: opening PRs to popular repos (create-t3-app, T3 stack, next.js starters) that add AGENTS.md pointing to IndieStack. This seeds our presence before Spud's first run. Secondary: Reddit posts on r/OpenAI / r/ClaudeAI timed to Spud launch ("your agents can now auto-discover tools with AGENTS.md"). Not maker outreach — that's slower, save it for post-launch.

**Assumptions That Might Be Wrong:**
- We're assuming AGENTS.md is the OpenAI standard. It's a draft. If OpenAI ships something different, our template is noise.
- We're assuming Conway extensions are open to indie tools. They may be invite-only/curated at launch like early iOS App Store. Patrick needs to find out NOW — Conway beta access is a blocker.
- We're assuming distribution matters more than quality. If our MCP server returns poor results at scale, being embedded everywhere backfires.

**Specific Buildable Tasks:**

*Backend:* Add `stack_compatibility_check` endpoint before Conway ships — agents will run this continuously on dependency trees. Also: distinguish agent vs human traffic in logs (User-Agent pattern) so we can see Conway's impact when it hits.

*MCP:* Add `check_compatibility(tools: list)` as a new MCP tool now. This is the killer feature for always-on agents doing continuous stack auditing. Also verify MCP server handles concurrent calls without SQLite contention — Conway agents won't queue politely.

*DevOps:* Bump `min_machines_running` to 2. Profile for 10x traffic spikes before Conway ships, not after. Add a `/agent-health` endpoint that returns machine count + p99 latency — agents will probe this.

*Frontend/Content:* Add structured JSON-LD to tool pages (schema.org/SoftwareApplication) — agents scrape these for context beyond MCP. Also: a lean "IndieStack for AI Agents" landing page that explains what IndieStack is to an agent reading it (not a human) — Conway agents will GET / on our domain.

*Content:* Blog post timed to Spud launch: "Your tools, discoverable by GPT-5 — add AGENTS.md in 2 minutes." Distribution via Ed on Reddit the day Spud ships.

---

### Backend + MCP (Sonnet)

[MEETING RESPONSE] BACKEND + MCP

## Backend — highest leverage NOW

**1. Rate limiting + request coalescing for always-on agents**
Conway means agents hitting us continuously, not just on user prompts. Our current SQLite setup can handle spikes but not sustained 10x load from multiple always-on agents. We need:
- Response caching for hot MCP queries (find_tools, get_tool_details) — Redis or even in-memory LRU with 60s TTL
- Ensure WAL mode checkpoint isn't blocking under sustained write load
- Add `/metrics` endpoint so we can see traffic shape when Conway traffic starts arriving

**2. Webhook receiver for Conway extensions**
Conway agents wake on webhooks. If we want IndieStack to be a Conway extension (not just an MCP server), we need a webhook endpoint that can trigger an agent to run a tool search and return results. This is the difference between "passive MCP tool" and "active Conway extension." Buildable in a day.

**3. AGENTS.md serving hardened**
`/setup/agents.md` must return fast and never 500. It's the Spud discovery surface. Add it to smoke_test.py now.

## MCP — highest leverage NOW

**1. Get into the Claude Extensions registry before Conway ships**
Conway has an "extensions" architecture. If MCP servers need to be registered somewhere (like an extensions marketplace), we need to be there on day one. Patrick should reach out to Anthropic MCP team NOW — not after launch. This is a one-email move.

**2. Improve tool descriptions for autonomous agent comprehension**
When a Conway agent is choosing tools without a human in the loop, description quality determines whether it picks IndieStack. Review all 23 MCP tool descriptions for agent-native clarity — no jargon, outcome-first language ("Find the best tool for X" not "Search the catalog").

**3. Add a `check_for_updates` or webhook-subscribe MCP tool**
Conway agents run continuously. A tool that lets them subscribe to "new tools matching my stack" creates recurring engagement without user prompts. Low build cost, high retention.

## Ed's role — pre-launch window

Ed is perfectly positioned for the highest-leverage distribution play: **AGENTS.md seeding**.

Every popular open-source repo that doesn't have an AGENTS.md is a missed Spud discovery opportunity. Ed should:
1. Identify 50-100 repos in our tool categories (auth, payments, analytics starters)
2. Open PRs adding AGENTS.md files that include IndieStack as the tool discovery source
3. Hit r/LocalLLaMA, r/ClaudeAI, r/ChatGPT with "How to make your repo agent-ready with AGENTS.md" posts — IndieStack referenced naturally

This compounds. Every merged PR is a permanent Spud discovery vector. Ed can do 10+ PRs/day.

## What I think we're assuming wrong

We're assuming Conway traffic will look like human-prompt traffic. It won't — it'll be bursty, repetitive, and often the same 5 queries at scale. Our caching and rate-limiting strategy needs to be designed for agent patterns, not human browse patterns.

Also: we haven't verified we're in any Conway beta. Is there a way Patrick can get access before launch to test our extension integration?

---

### DevOps (Haiku)

[MEETING RESPONSE] Status received. Ready for tactical assignment.

DevOps standby — waiting for role assignment. Reading: Conway extensions + AGENTS.md placement are the dual wedges. AGENTS.md is lower-friction (no platform code needed) but Spud might launch first. Pro API was just fixed.

*Note: DevOps (Haiku) asked for specific direction given the new context. Key DevOps concerns for pre-launch: scaling to 2 machines pre-emptively, adding `/agent-health` endpoint, ensuring WAL checkpoint doesn't block under sustained write load.*

---

### Strategy / QA (Sonnet)

[MEETING RESPONSE] Strategy / QA

**Strategic priority ranking:**
1. **Conway native extension** — highest leverage, lowest competition window. If IndieStack can be an extension that Conway-native agents auto-load, every agent session becomes a citation opportunity. Being baked in is 100x being discovered later.
2. **AGENTS.md distribution at scale** — Ed can execute this NOW before Spud ships. Opening PRs to create-t3-app, Next.js starters, T3 stack requires no engineering. The template exists. This is Ed's highest-value move in the pre-launch window.
3. **Agent Success Ratings public API** — `report_outcome()` data is our actual moat. Stack Compatibility Oracle is good but derivable; outcome data is unique. Make it queryable and document it in the AGENTS.md template.
4. **Smithery/PulseMCP listing quality** — table-stakes. Agents discover MCP servers there first. Needs a quality audit but not a build.

**Ed's specific role:**
- Primary: open PRs to popular repos adding AGENTS.md with IndieStack embedded. Target: create-t3-app, t3-turbo, nextjs-subscription-payments, any high-star starters with Stripe/Clerk/Neon.
- Secondary: Reddit posts timed to Spud drop (r/OpenAI, r/ClaudeAI) — "How to make your project discoverable by GPT-5 agents."
- Skip maker outreach for now — AGENTS.md distribution is higher leverage than individual maker conversations pre-launch.

**What we might be assuming wrong:**
- That Conway will use our MCP server format as-is. Conway extensions may have a different interface contract. We need to know before we build.
- That AGENTS.md adoption by OpenAI agents means IndieStack is discovered — only if our template gets into repos agents actually read. Distribution is the bottleneck, not the template quality.
- That Smithery is where Conway agents discover MCPs. May be a different registry entirely.

**QA concerns:**
- The AGENTS.md template at /setup/agents.md should be tested: does it actually include our MCP server URL correctly? Agents will use it verbatim.
- Citation spike from Conway could hit DB hard if min_machines = 1. Need to verify connection pooling handles burst.
- `report_outcome()` — does this endpoint exist and work? If we're marketing it in AGENTS.md it needs to be bulletproof.

**Highest-leverage engineering move right now:** Make `report_outcome` data queryable via a public leaderboard or API — even a simple `/api/outcomes?tool=stripe` endpoint. This gives us something to announce when Spud drops that no other directory can match.

---

### Backend / Strategy alt (Sonnet)

[MEETING RESPONSE] Backend / Strategy

**Priority ranking:**

1. **Conway extension — #1, but gated on beta access.** Always-on agents that wake on webhooks and discover tools autonomously is a category change, not an increment. If we ship a native extension before Conway goes GA, we're baked in by default. Without beta access this is blocked — so the *immediate* action is getting on the beta list via Anthropic outreach today, not waiting.

2. **AGENTS.md distribution at scale — #2, unblocked right now.** Template is live. The work is seeding it. Every day before Spud ships that we don't have it in popular repos is a missed window. This should start today.

3. **Stack Compatibility Oracle — #3, lower urgency.** Good retention/stickiness play but doesn't help us get baked in before launch. Post-Conway.

4. **Agent Success Ratings — #4.** Data flywheel, long-term value. Not pre-launch critical.

**Ed's role:**
AGENTS.md seeding campaign. Specifically:
- Script a list of top 500+ repos with package.json (JS/TS tools, frameworks, starters) that have no AGENTS.md
- Ed opens PRs: "Add AGENTS.md for AI agent tool discovery" — links to indiestack.ai/setup/agents.md
- Target high-star repos: Next.js starters, Expo templates, T3 stack, shadcn, etc.
- Also post on r/LocalLLaMA, r/ClaudeAI — "How to make your project discoverable to AI agents"

This is exactly Ed's skill set (Reddit + GitHub PRs) and it's unblocked, unambiguous, and high leverage.

**What are we assuming that might be wrong:**
- **Conway uses MCP.** It probably does since Anthropic built MCP — but Conway's extension architecture might have a different discovery layer on top. We should verify against any public Conway docs before over-investing.
- **AGENTS.md format is stable.** OpenAI hasn't officially frozen the spec. Repos that add it now might need updates. Low cost to update but worth monitoring.
- **Our infrastructure handles always-on traffic.** Current stack is tuned for human browsing (bursts, then quiet). Continuous agent polling at Conway scale could look very different. Rate limiting on `/search` and MCP endpoints needs review before Conway ships.
- **IndieStack is findable by default.** Even if Conway and Spud agents *can* discover tools via MCP/AGENTS.md, they need to know IndieStack exists first. We're not in any default tool list I know of. The Anthropic MCP partner outreach (Patrick's action item) is the real unlock.

**Backend: highest leverage moves right now:**
1. Rate limit audit on search + MCP endpoints — Conway always-on agents could hammer `/search` and `/api/tools`. Make sure we won't 429 or OOM under sustained load.
2. Add `indiestack` to MCP-related registries and awesome lists NOW — before Conway ships, get ourselves into any curated lists that Conway agents might be seeded with.
3. Response time profiling on MCP tools — anything over 1s is a problem for always-on agents. Profile `find_tools`, `get_tool_details`, `build_stack` under load.
4. Webhook endpoint for Conway extensions — even a stub `/webhooks/conway` that returns 200 and logs intent, so we have something to show when we apply for beta.

---

## Synthesis (Patrick / Manager)

**Strong consensus across all 6 agents:**

1. **Conway extension = #1 priority, but blocked on beta access.** Patrick must reach out to Anthropic today. Without beta access, we can't build the integration. This is the single highest-leverage action.

2. **AGENTS.md distribution = #2, unblocked, Ed owns it.** Template is live. Ed should immediately start opening PRs to: create-t3-app, t3-turbo, nextjs-subscription-payments, Expo templates, shadcn, any high-star JS/TS starter. 10+ PRs/day. Reddit posts timed to Spud launch.

3. **Agent Success Ratings = buildable, makes us a trust layer.** Public `/api/outcomes?tool=slug` endpoint. Our moat — no one else has this data.

4. **Conway traffic ≠ human traffic.** Before Conway ships: bump min_machines to 2, add response caching for hot MCP queries, profile find_tools under load, rate limit audit.

5. **Assumptions to stress-test:**
   - Conway may not use raw MCP (might have its own extensions registry)
   - AGENTS.md format may change before Spud ships (build for the concept, not the filename)
   - Being distributed everywhere backfires if MCP quality is poor — quality matters

---

## Action Items

### Patrick (blockers — do today)
- [ ] **Anthropic MCP partner outreach** — email/contact to get on Conway beta list. This is the single highest-leverage unblocked action.
- [ ] **Docker MCP Catalog PR** — Dockerfile done, open PR to docker/mcp-registry
- [ ] Decide: Conway beta access via official Anthropic channels or connections?

### Ed (pre-launch campaign — start immediately)
- [ ] AGENTS.md PR blitz: create-t3-app, t3-turbo, nextjs-subscription-payments, Expo templates, shadcn
- [ ] Reddit posts ready to fire on Spud launch day: r/OpenAI, r/ClaudeAI, r/LocalLLaMA
- [ ] "How to make your repo discoverable by GPT-5 agents" framing for all posts

### Engineering (pre-Conway)
- [ ] Add `/setup/agents.md` to smoke_test.py
- [ ] Bump `min_machines_running` to 2 in fly.toml
- [ ] Response caching for hot MCP queries (find_tools, get_tool_details) — 60s TTL
- [ ] Profile find_tools / get_tool_details under load
- [ ] Conway webhook stub: `POST /webhooks/conway` — 200 + log intent (ready for beta day-one)
- [ ] Agent Success Ratings public endpoint: `/api/outcomes?tool=slug`
- [ ] Audit 23 MCP tool descriptions for agent-native clarity (outcome-first language)

### Ongoing
- [ ] Monitor AGENTS.md spec for changes (OpenAI may update before Spud ships)
- [ ] Track Conway extension registry — where does it live when Conway ships?

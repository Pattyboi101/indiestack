# Gemini Deep Research Prompt — IndieStack Growth: 50 to 500 Users

> Copy everything below the line into Gemini Deep Research. Attach the context file (2026-03-15-growth-strategy-context.md) as a document.

---

## Prompt

I've attached a detailed context document about IndieStack — an open-source supply chain that connects AI agents with 3,100+ indie-built creations. Read it thoroughly before proceeding.

**The situation**: IndieStack launched on Product Hunt March 7, 2026. We have 3,100 tools, 208K page views, 28K outbound clicks, 184 agent citations, an MCP server on PyPI with 9 API keys issued — but only 52 registered users and 0 paying subscribers (1 test subscription). The infrastructure is complete: MCP server with 15 tools, Stack Auditor, Pro tier, quality gates, health monitoring, agent memory, compatibility pairs. We're a 2-person team (both uni students) shipping at 5-10x speed via Claude Code. We just built a command hub for coordination. The question isn't "what to build" — it's "how to get from 52 users to 500, and from 0 revenue to first 10 paying customers."

**The strategic question**: What are the highest-leverage distribution channels and conversion tactics for a developer tool in 2026, specifically one that operates primarily through AI agent integration (MCP servers)?

**The key insight you must factor in**: IndieStack's primary distribution is agent-to-agent, not human-to-human. The MCP server IS the product for most users — they never visit the website. This means traditional SaaS growth playbooks (landing page optimization, email drip campaigns, SEO blog posts) may be secondary to MCP marketplace positioning, agent prompt engineering, and developer toolchain integration.

**Research areas (go deep on each):**

1. **MCP Server Adoption Patterns (2025-2026)** — How are MCP servers actually distributed today? Research the Claude MCP marketplace, Cursor's MCP integration, Windsurf's approach. What makes an MCP server go from 10 installs to 1,000? What are the top MCP servers by install count and what do they have in common? How do developers discover MCP servers — PyPI, GitHub, word of mouth, agent recommendations? Is there an equivalent of "npm weekly downloads" visibility for MCP?

2. **GitHub Action Marketplace Growth** — Research GitHub Actions that grew to 1,000+ users in their first 3 months. What categories perform best? How do Actions drive SaaS upgrades (free Action → paid dashboard)? Specific examples: Dependabot's growth pattern, CodeQL adoption, Snyk's Action-to-paid funnel. How would an "indie tool audit" Action (scans package.json, suggests indie alternatives) perform? What's the competitive landscape for dependency audit Actions?

3. **Developer Tool Pricing Psychology (2026)** — Research the $9/mo vs $99 LTD debate specifically for indie developer tools. What does the data say about lifetime deal conversion rates vs monthly subscriptions for tools with <500 users? Examples: Pika, Raycast, Fig (now acquired), Warp, Linear's early pricing. What price points work for "data products" (demand signals, analytics dashboards) vs "workflow tools"? How do tools with primarily API-based distribution (like IndieStack's MCP server) price differently?

4. **Product Hunt Post-Launch Strategies That Work** — Research what happens in the 7-30 days after a Product Hunt launch. What follow-up tactics actually convert PH visitors into users? Case studies of indie tools that used PH as a springboard (not a one-day spike). How to leverage the PH backlink for SEO. Reddit cross-posting strategies that work vs ones that get you banned. Is a second PH launch viable and when?

5. **From 50 to 500 Users: The Developer Tool Playbook** — Research the specific growth tactics that work at this scale (not at 10K+ scale). Community-led growth vs content-led growth vs integration-led growth. What channels have the best cost-per-acquisition for indie developer tools in 2026? Research Plausible Analytics' early growth (open-source, indie, anti-Google positioning), PostHog's first 500 users, Cal.com's open-source growth playbook. What can a 2-person team realistically execute?

6. **AI Agent Distribution as a Channel** — This is the novel angle. Research how tools are getting recommended BY AI agents as a distribution channel. How does being in an AI's training data vs being in a live tool (MCP) differ for distribution? Are there examples of tools that grew primarily through AI recommendations? What does "agent SEO" look like — optimizing to be recommended by AI agents rather than ranked by Google? How does IndieStack's position as the "supply chain for agents" create a unique distribution advantage?

**What I need from you:**

A prioritized growth playbook with 3 tiers:
- **This week** (2-person team, AI-assisted, can ship fast): 3-5 specific actions with expected impact
- **This month**: 3-5 medium-effort plays that compound
- **This quarter**: 2-3 strategic bets that build the moat

For each action: what to do, why it works (with evidence), expected impact range, and specific examples of similar tools that did this successfully.

**Constraints on your analysis:**

- No generic "build a blog" or "post on Twitter" advice. Be specific: which subreddits, which communities, which exact messaging.
- Think in systems, not features. Distribution channels that compound, not one-off tactics.
- Assume AI leverage — 2-person team with Claude Code ships 5-10x faster than traditional.
- Indie-first. No ideas requiring hiring, funding, or paid ads budget over $100/month.
- Research deeply, don't speculate. Cite sources, reference specific companies and their growth numbers.
- Challenge our assumptions — especially the assumption that the MCP server is the right primary distribution channel.

**Additional angles to explore:**

- Is "open-source supply chain" the right positioning, or is there a more compelling frame for this stage?
- Should we be targeting makers (supply side) or developers (demand side) first at 52 users?
- What's the role of a GitHub Action in an MCP-first distribution strategy?
- How do tools with agent-primary distribution handle pricing when the user never visits the website?
- Are there examples of two-sided marketplaces that cracked the chicken-and-egg problem at this scale?

**Format**: Structured playbook with evidence-backed recommendations. Each recommendation should include: tactic, evidence (who did this and what happened), expected impact, implementation notes, and risks.

**Depth expectation**: This is an LLM-to-LLM knowledge transfer. I will be implementing your recommendations directly with Claude Code this week. Be precise. Cite sources. The context document has everything about IndieStack's current state — your job is to bring external research and original thinking.

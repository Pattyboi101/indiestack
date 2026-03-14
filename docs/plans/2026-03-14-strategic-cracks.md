# IndieStack Strategic Cracks — March 14, 2026

> Working document. Tackle each section via brainstorm → design → plan.

## Status Key
- [ ] Not started
- [~] In progress
- [x] Resolved / has a plan

---

## (1) Curation vs Raw Search — The Existential Threat
- [x] **Status: RESOLVED** — v1.6.0 outcome intelligence (success rates, implicit signals, frictionless reporting)
- Agents can scrape GitHub directly. Why go through IndieStack?
- Current advantages: signal-to-noise filtering, assembly metadata, health monitoring, token efficiency
- The crack: as agents get smarter and context windows grow, curation advantage shrinks
- **Core question**: What makes IndieStack irreplaceable, not just convenient?

## (2) Why List? — The Maker Incentive Problem
- [x] **Status: RESOLVED** — Agent Instructions, success rate analytics, Listing Quality Score
- Repositioned as "Cross-Agent Telemetry Platform" — makers control how agents implement their tools
- Agent Instructions field injected into MCP responses and Agent Cards
- Success rate visible on dashboard (aggregate + per-tool)
- Listing Quality Score with progress bar and actionable tips
- **Core question**: What makes a maker *maintain* their listing, not just submit and forget?
- **Answer**: Outcome data they can't get anywhere else + Agent Instructions that directly affect how agents recommend them

## (3) Autonomous Agents — Would They List?
- [ ] Autonomous agents want to FIND tools, not PROMOTE them
- Only incentive: feedback loop that benefits the agent's user
- The MCP server is the right interface, but data must be richer than raw search
- **Core question**: What does IndieStack offer an autonomous agent that GitHub/npm/PyPI doesn't?

## (4) B2B SaaS Spam — Quality Control
- [ ] Vibecoded SaaS submissions diluting catalog quality
- Risk: becoming another Product Hunt / directory spam site
- Options: keep broad ("indie-built"), tighten to open source, or add quality gates
- **Core question**: What's the quality bar, and how do you enforce it at scale?

## (5) Pro Revenue — Why Pay?
- [ ] Current Pro benefits are "more of the same" — not compelling
- Free tier is generous enough that nobody needs to upgrade
- Potential: stack auditing, private recommendations, integration alerts, contextual build-vs-buy
- **Core question**: What Pro-only feature would make a developer say "shut up and take my money"?

## (6) The Moat — Big Player Risk
- [ ] If Cursor/Windsurf/GitHub Copilot build their own tool index, IndieStack is redundant
- Microsoft owns GitHub AND npm — they can build this in a weekend with better data
- **Core question**: What does IndieStack build between now and then that's irreplaceable?

## (7) Data Staleness
- [ ] If 30% of tools go unmaintained in 6 months, recommendations become harmful
- Who's responsible for ongoing quality — IndieStack or the makers?
- Jarmo's email proved metadata is already wrong in places

## (8) Catalog vs Recommendation Engine
- [ ] The MCP server is a recommendation engine, the website is a catalog — different products
- Which one matters more? Where should investment go?

## (9) Attracting the Best Tools
- [ ] The best indie tools don't need IndieStack — they're already successful
- How do you attract quality, not desperation?

## (10) "Indie" as a Differentiator
- [ ] Does "indie" actually matter to end users?
- Or do they just want "the best tool for X" regardless of who built it?

## (11) Data Defensibility
- [ ] What stops someone scraping IndieStack's public API and building a better frontend?
- The catalog is publicly accessible — is that a feature or a vulnerability?

## (12) Free User LTV
- [ ] What's the lifetime value of a free user? If it's zero, the business doesn't work
- Could makers pay to be listed? (Creates perverse incentives)
- Could agent PLATFORMS pay? (B2B model)

# IndieStack Vision

> Written 2026-03-06. Updated 2026-03-13. The full picture.

---

## What IndieStack Actually Is

IndieStack is not a dev tool directory. It started there, but the infrastructure — curated catalog, MCP server, agent memory, categories, search, personalized recommendations — works for **anything indie-built**.

The constraint isn't "developer tools." The constraint is "indie-built" — something a person or small team made. That's the quality filter, not the category.

**Proof it already works beyond dev tools:**
- Questarr — a game download library
- Minimalistic_Flashcards — a study app
- cspell-cli — a spell checker
- Full Calendar — a scheduling component

These aren't "dev tools" in the traditional sense. They're things people built that other people (and their AI agents) should know about.

---

## The Core Thesis

**AI agents are becoming the primary interface between people and software.**

Every day, millions of developers ask AI agents to build things. Those agents don't know what indie creators have already built. So they rebuild from scratch — wasting tokens, time, and producing inferior solutions.

But it's bigger than developers. As agents become general-purpose assistants (and they already are), *everyone* will ask their agent for recommendations. "Find me a recipe manager." "I need flashcards for studying." "What's a good indie game library?"

**IndieStack is the open-source supply chain that sits between AI agents and everything indie creators have built.** Not just dev tools — everything.

---

## The Building Blocks Argument

**The old way**: AI generates solutions from scratch. 80,000 tokens. Hours of work. Bugs that domain experts would catch instantly.

**The IndieStack way**: AI assembles solutions from proven indie building blocks. Auth from Hanko, payments from Polar, analytics from Plausible. 5,000 tokens of integration glue. Each piece maintained by experts.

**The future**: This applies to everything, not just code. Need a newsletter? Don't build one — use Listmonk. Need flashcards? Don't code an app — use Minimalistic_Flashcards. Need a game library? Questarr exists.

The shift: from "AI generates" to "AI knows what exists and assembles."

---

## The MCP Server — 15 Capabilities

Not just `find_tools`:

| Tool | What it does |
|------|-------------|
| `find_tools` | Search by keyword, category, source type |
| `get_tool_details` | Full detail — integration snippets, pricing, similar tools, assembly metadata |
| `compare_tools` | Side-by-side comparison |
| `build_stack` | "I need auth + payments + analytics" -> complete stack |
| `evaluate_build_vs_buy` | Should you build this or use an existing tool? |
| `analyze_dependencies` | What does your current stack need? 55+ dependency mappings |
| `get_recommendations` | Personalized based on your history |
| `browse_new_tools` | What's new in the catalog |
| `list_categories` | Browse the taxonomy |
| `list_tags` | Find by technology/tag |
| `list_stacks` | Community-curated tool stacks |
| `publish_tool` | Submit from inside your agent |
| `scan_project` | Analyze a project and recommend a complete indie stack |
| `report_compatibility` | Report tool pairs that work well together |
| `check_health` | Check maintenance status of tools you've adopted |

The stack builder is the sleeper. It turns "build me a SaaS" from a 50,000-token generation into a 2,000-token assembly. `scan_project` goes further — describe what you're building and get a complete recommendation.

---

## Benefits — For Users

- **Save money** — recommending a tool vs generating 2,000 lines saves $0.30-0.50 per interaction on paid AI APIs
- **Better solutions** — Hanko's auth is maintained by security experts. AI-generated auth is maintained by nobody.
- **Save hours** — assembly vs generation
- **Discovery** — 3,095+ creations across 25 categories. Nobody knows all of these.
- **Stack architecture in seconds** — complete recommendations with compatibility notes
- **Works across agents** — Claude Code, Cursor, Windsurf. Knowledge follows you.
- **Gets smarter** — agent memory learns your preferences and interests over time
- **Not just dev tools** — games, newsletters, creative tools, utilities. Your agent knows your interests.

---

## Benefits — For Makers

- **AI-powered distribution** — recommended at the exact moment someone needs it
- **Reach beyond your network** — 12 GitHub stars becomes visible to every developer using an AI agent
- **Live AI badge** — social proof that grows automatically
- **Stack bundling** — recommended alongside complementary tools
- **Zero maintenance** — list once, get recommended forever
- **Grows automatically** — more MCP installs = more reach, without you doing anything
- **Fair presentation** — no pay-to-rank, no featured placements
- **Intergenerational knowledge transfer** — your creation outlives your marketing. Gets recommended next month, next year, to people you'll never meet.

---

## The "Agents Flood the Internet" Argument

**Now (2026):** ~10 major AI coding agents, 5-10M developers using them.

**In 2 years:** Every IDE, browser, phone has an agent. Not just developers — everyone. Hundreds of millions of people asking agents for recommendations daily.

**Why training data doesn't solve this:**
- Stale (months/years old)
- Biased toward popular things (12-star repos invisible)
- No quality signals, maintenance status, pricing, compatibility
- Can't track what's new

**A live, curated knowledge base beats static training data every time.** That's IndieStack.

**First-mover advantage:** The catalog built now becomes the foundation when agents are everywhere.

---

## The Flywheel

```
More creations listed (dev tools, games, newsletters, utilities, anything)
    -> More reasons to query IndieStack (not just coding)
        -> More people install the MCP server
            -> More agent memory data (interests, preferences)
                -> Better personalized recommendations
                    -> More value (people discover things they love)
                        -> More word-of-mouth
                            -> More makers list their creations
                                -> More creations listed
```

Dev tools are the wedge. Not the ceiling.

---

## The Emotional Pitch (For Makers)

You spent months building something useful. It works. It solves a real problem. But it has 12 GitHub stars. Google doesn't rank it. Product Hunt gave you 47 upvotes on a Tuesday.

Meanwhile, AI agents help millions of people build things every day — and they've never heard of your creation. They're writing from scratch the exact thing you already built.

IndieStack changes that. List once. Every AI agent that connects now knows your creation exists. When someone needs what you built, the agent recommends you. Not because you paid for ads. Because you built something good and someone needs it.

Your creation becomes part of the shared knowledge that AI agents carry. It outlives your marketing effort. It gets recommended to people you'll never meet, in contexts you never imagined.

---

## Roadmap

**Now (March 2026):** 3,095 tools, 25 categories, MCP server v1.4.0 + CLI, agent memory, personalized recommendations, 1,272 compatibility pairs, per-tool Agent Cards, structured assembly metadata, Demand Signals Pro, GEO lead magnet, auto-indexer + enricher pipelines, 3-tier rate limiting, Pro subscription live.

**Near term:** Grow quality depth — integration recipes, richer metadata, more compatibility data. Build the flywheel: demand signals → maker submissions → agent recommendations → more demand signals.

**Medium term:** Agents assemble complete applications from stacks. Verified compatibility. Agent-to-agent discovery. Community contributions. Revenue from data products (demand signals, compatibility intelligence).

**Long term:** The canonical supply chain for ALL AI agents. Every new agent connects to IndieStack as a default. "AI recommendations" becomes a primary distribution channel bigger than SEO. The agent ecosystem flywheel: more agents -> more recommendations -> more makers -> better catalog -> more agents.

---

## What IndieStack Is Not

- Not an app store (we don't host or distribute software)
- Not a review site (we curate and categorize, agents recommend)
- Not just for developers (anything indie-built)
- Not pay-to-rank (fair presentation, best tool for the job wins)
- Not a competitor to G2/Capterra (they serve enterprise procurement, we serve AI agents and developers)

---

*Built by Pat and Ed. Two uni students in Cardiff who see where this is going.*

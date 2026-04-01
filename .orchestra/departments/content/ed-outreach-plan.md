# Ed's Outreach Playbook — IndieStack

_Ready-to-go templates. Copy, personalise lightly, post. Don't overthink it._

---

## 1. Reddit Post Templates

### r/SideProject

**Title:** I built a tool catalog that plugs into Claude/Cursor so AI agents stop writing boilerplate from scratch

**Body:**
> Hey r/SideProject — I've been building IndieStack with my co-founder for the past few months. It's a catalog of 3,100+ developer tools (auth, payments, analytics, email, etc.) that ships as an MCP server.
>
> The idea: before your AI writes 40,000 tokens of auth code, it checks if someone already built and maintains it.
>
> One-line install for Claude Code:
> ```
> claude mcp add indiestack -- uvx --from indiestack indiestack-mcp
> ```
>
> It's free. No account needed. Happy to answer questions about how it works.
>
> Site: indiestack.ai

---

### r/webdev

**Title:** Made an MCP server that gives Claude/Cursor/Windsurf a searchable catalog of 3,100 dev tools

**Body:**
> Built this because I kept watching AI agents reinvent wheels. Instead of generating an auth system, it should just know PostHog or Plausible exist.
>
> IndieStack is an MCP server — install it once and your agent searches 3,100+ curated tools before writing anything from scratch. It returns install commands, compatibility data, and real migration paths from GitHub repos ("jest → vitest: 37 repos").
>
> Install (Claude Code):
> ```
> claude mcp add indiestack -- uvx --from indiestack indiestack-mcp
> ```
>
> Works with Cursor and Windsurf too. What are you using for tool discovery in your AI workflow?

---

### r/selfhosted

**Title:** Open-source developer tool catalog with an MCP server — works with Claude, Cursor, Windsurf

**Body:**
> Been working on IndieStack — a discovery layer for developer tools that ships as an MCP server. The catalog has 3,100+ tools across 25 categories with verified compatibility data pulled from real GitHub repos.
>
> The self-hosted angle: we track tools built by independent devs and small teams. Focused, maintained, honest pricing. Not just "which VC-backed SaaS can your AI shill."
>
> Quick install for Claude Code:
> ```
> claude mcp add indiestack -- uvx --from indiestack indiestack-mcp
> ```
>
> Or if you want to poke around: indiestack.ai/explore

---

## 2. Discord Servers to Post In

### Anthropic / Claude Code Community
- **Where:** Official Anthropic Discord — find the link at anthropic.com or claude.ai (usually pinned in sidebar)
- **Channel:** Look for `#claude-code`, `#mcp-servers`, or `#show-and-tell`
- **What to post:** The "Install in 30 seconds" snippet below. This audience is exactly right — Claude Code users who'd benefit immediately.

### Cursor Community
- **Where:** Official Cursor Discord — link at cursor.sh community page
- **Channel:** `#show-and-tell` or `#tools-and-integrations`
- **What to post:** Adapt the snippet — swap `claude mcp add` for the Cursor JSON config:
  ```json
  {"command": "uvx", "args": ["--from", "indiestack", "indiestack-mcp"]}
  ```

### Latent Space Discord (AI builders)
- **Where:** latent.space community Discord — active AI developer and builder community
- **Channel:** `#tools` or `#show-and-tell`
- **What to post:** Lead with the agent angle ("AI agents that search tools instead of generating boilerplate") — this audience cares about AI infra, not just cool tools.

**Tip:** Don't post the same message in all three on the same day. Space it out, tweak the opening for each community.

---

## 3. "Install in 30 Seconds" Snippet

Drop this into any conversation, Discord, Reddit comment, or GitHub issue:

---

> **Install in 30 seconds**
>
> Your AI agent searches 3,100 dev tools before writing code from scratch.
>
> ```
> claude mcp add indiestack -- uvx --from indiestack indiestack-mcp
> ```
>
> Then ask your agent:
> - "Find an auth solution for my Next.js app"
> - "What's the lightest open-source payments library?"
> - "Show me migration paths away from Webpack"
>
> IndieStack gives Claude, Cursor, and Windsurf a curated index of developer tools — so agents recommend real libraries instead of generating boilerplate.

---

## 4. Twitter/X DMs — 5 Specific People

These are indie dev tool makers who are active, have audience, and would care about AI agents recommending their tools.

**Goal of the DM:** Let them know their tool is on IndieStack and AI agents are already surfacing it. Keep it short — one paragraph, one link, no ask.

**Template:**
> Hey [name] — [tool name] is listed on IndieStack (indiestack.ai). AI agents in Claude/Cursor are already searching it when devs ask for [category]. You can claim the listing to add install commands and correct any gaps: indiestack.ai/claim/magic?tool=[slug]
> — Pat

---

### 1. **@tdinh_me — Tony Dinh**
Builds DevUtils, Xnapper, BlackMagic.so. Indie dev tools, active on Twitter, engaged community. Tweets about building in public. Perfect fit — his tools are exactly what IndieStack catalogs.

### 2. **@marc_louvion — Marc Lou**
Builds ShipFast (Next.js boilerplate/starter kit). Very active on Twitter, large indie hacker following. Constantly tweets about building and launching. His audience is devs who'd use IndieStack.

### 3. **@levelsio — Pieter Levels**
Builds Nomad List, Remote OK, and various smaller tools. Massive following, tweets constantly about building. DMs him specifically about any of his dev-facing tools in the catalog.

### 4. **@theo — Theo Browne**
Builds T3 stack, Ping.gg. Very active in the dev tools space, large YouTube + Twitter audience. He's vocal about AI tools. A retweet from him would be significant.

### 5. **@shadcn**
Built shadcn/ui — used by millions of devs, massive community. Active on Twitter. If shadcn/ui is in the catalog (it should be), a DM saying "AI agents are recommending shadcn/ui X times a month" is genuinely interesting data for him.

---

## Notes for Ed

- **Don't batch DMs** — send one a day, check for replies before sending the next
- **Don't mention paid tiers** in cold outreach — lead with the data (MCP views, recommendations)
- **If someone claims their tool**, loop in Pat — it's a signal worth celebrating publicly
- **Reddit timing:** post between 9am–12pm UTC on weekdays for r/webdev, r/SideProject. Evenings for r/selfhosted.
- **Don't cross-post** the same text — each subreddit has different culture, adapt the opener

---

_Last updated: 2026-04-01 by Content department_

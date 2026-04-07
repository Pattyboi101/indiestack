# Research: Is Anthropic Building Native Tool Discovery for Conway?

**Date:** 2026-04-07
**Purpose:** Pre-pitch due diligence — does the Anthropic Conway pitch need to pivot?

---

## Short answer: No — and there's a bonus distribution channel we missed.

---

## What Anthropic is building

### 1. Claude Marketplace (launched March 16, 2026)
- Enterprise B2B app store — curated Claude-powered business applications
- Partners: Snowflake, GitLab, Harvey AI, Replit, Rogo, Lovable
- Zero commission on purchases
- **Audience:** Enterprise buyers buying AI tools
- **NOT a competitor:** This is about buying AI-powered apps, not discovering developer infrastructure tools

### 2. claude-plugins-official (GitHub: anthropics/claude-plugins-official)
- Official Anthropic-managed directory of Claude Code plugins
- Available via `/plugin` command in Claude Code, browsable at claude.com/plugins
- Focus: extending Claude Code's capabilities (skills, slash commands, MCP connectors)
- **NOT a competitor:** This is about what Claude Code *can do*, not what tools a developer should *use*
- **OPPORTUNITY:** IndieStack could be listed here as a Claude Code plugin — direct install via `/plugin install indiestack@claude-plugins-official`

### 3. Conway extension system
- App-store style discovery of Conway capabilities (.cnw.zip format)
- Focus: extending the Conway agent with new tools and UI tabs
- **NOT a competitor:** This is about agent capabilities, not developer tool recommendations

---

## The gap IndieStack fills — still wide open

None of Anthropic's three initiatives answer the question an agent asks when building software:
> "What existing tool should I use for auth / payments / email / queues?"

The Claude Marketplace sells AI apps. claude-plugins-official extends Claude Code. Conway extensions add agent capabilities. **None of them tell an agent "use Clerk for auth, not NextAuth, because it has 847 agent citations and active maintenance."**

IndieStack is the missing layer.

---

## Pitch implication: No pivot needed

The pitch to DSP doesn't need to change. It's not "we compete with your marketplace" — it's "we fill a gap your marketplace doesn't touch." If anything, the existence of claude-plugins-official strengthens the pitch: Anthropic has already built a plugin distribution system, and IndieStack is a natural fit for it.

---

## Action items from this research

1. **Pitch angle confirmed:** Lead with the gap — none of Anthropic's products recommend developer tools at the infrastructure level.

2. **New opportunity — claude-plugins-official submission:** MCP should investigate submitting IndieStack as a Claude Code plugin. If accepted, every Claude Code user gets it via `/plugin install indiestack`. This is a bigger distribution play than Conway. Add to MCP's backlog.

3. **Patrick's GitHub outreach (Apr 11):** Can reference claude-plugins-official in the DSP message. "We've been tracking the claude-plugins-official repo and think IndieStack's MCP server would be a natural addition — happy to discuss fit." Warms the conversation with something concrete Anthropic can act on immediately.

---

## Sources
- Claude Marketplace: launched March 16, 2026 (digitalcommerce360.com)
- claude-plugins-official: github.com/anthropics/claude-plugins-official
- Conway extension system: testingcatalog.com, April 2026 leak reports

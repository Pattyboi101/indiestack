# Your AI agent just got smarter about dev tools (IndieStack MCP v1.12)

Quick update on IndieStack — the MCP server that gives Claude, Cursor, and Windsurf a searchable catalog of 3,100+ developer tools.

## What's new

**Market gaps** — new `get_market_gaps()` tool. Your agent can now see what tools developers are searching for but can't find. If you're building a dev tool, this tells you where the demand is.

**Trust-weighted search** — tools with higher agent success rates now rank higher. When agents report that a tool worked (via `report_outcome`), that tool climbs in future searches. Real usage data, not just star counts.

**Install command priority** — search results now prioritize tools that have actual install commands. No more "here's a tool" with no way to install it. If it has `npm install X` or `pip install X`, it ranks higher.

**22 tools total** — the MCP server now has 22 tools covering search, compatibility checking, dependency analysis, stack building, market gaps, and outcome reporting.

## Install in 30 seconds

```bash
claude mcp add indiestack -- uvx --from indiestack indiestack-mcp
```

Then ask your agent:
- "Find an auth solution for my Next.js app"
- "What's the lightest open-source payments library?"
- "What tools are developers looking for that don't exist yet?"

Works with Cursor and Windsurf too:
```json
{"command": "uvx", "args": ["--from", "indiestack", "indiestack-mcp"]}
```

## Why this matters

AI agents spend thousands of tokens rebuilding auth, payments, and email from scratch — things indie developers already built and maintain. IndieStack sits between the agent and the code generation step: "before you build, check if it already exists."

3,100+ tools. Compatibility data from 4,500+ GitHub repos. Migration intelligence showing what developers actually switch between. All searchable by your AI in one MCP call.

Free. No account needed. No rate limits.

**PyPI:** [indiestack](https://pypi.org/project/indiestack/)
**Site:** [indiestack.ai](https://indiestack.ai)
**GitHub:** [Pattyboi101/indiestack](https://github.com/Pattyboi101/indiestack)

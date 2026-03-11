# IndieStack MCP Server

The knowledge layer between AI agents and everything indie creators have built. 793+ creations across 25 categories — dev tools, games, utilities, newsletters, creative tools, learning apps, and more.

<!-- mcp-name: io.github.Pattyboi101/indiestack -->

## Quick Start

```bash
# Option 1: uvx (zero install — runs directly)
claude mcp add indiestack -- uvx --from indiestack indiestack-mcp

# Option 2: pipx (recommended for persistent install)
pipx install indiestack
claude mcp add indiestack -- indiestack-mcp

# Option 3: Cursor / Windsurf
# Add to your MCP config:
# {"command": "uvx", "args": ["--from", "indiestack", "indiestack-mcp"]}
```

That's it. Your AI searches what exists before building from scratch.

## What it does

Your AI spends thousands of tokens rebuilding auth, payments, and analytics from scratch — things indie creators already built. Meanwhile, those creations sit on GitHub with 12 stars, invisible to the AI agents that could be recommending them.

IndieStack fixes both sides. Install the MCP server and your AI searches 793+ indie creations before writing boilerplate. Built something yourself? List it so other developers' AIs find it instead of reinventing it.

### Tools (12)

| Tool | What it does |
|------|-------------|
| `find_tools` | Search 793+ creations by keyword, category, or source type |
| `get_tool_details` | Full details with integration snippets and companion suggestions |
| `list_categories` | Browse all 25 categories — dev tools to games to newsletters |
| `compare_tools` | Side-by-side comparison of any two creations |
| `build_stack` | Assemble a complete indie stack from building blocks |
| `publish_tool` | Submit your creation so other agents can recommend it |
| `browse_new_tools` | Recently added creations with pagination |
| `list_tags` | All tags sorted by popularity |
| `list_stacks` | Curated stacks for common use cases |
| `analyze_dependencies` | Paste package.json/requirements.txt, get indie replacements |
| `evaluate_build_vs_buy` | Financial breakdown: build from scratch vs use what exists |
| `get_recommendations` | Personalized suggestions based on your search history |

### Resources (3)

| Resource | What it provides |
|----------|-----------------|
| `indiestack://categories` | All 25 categories with slugs for filtering |
| `indiestack://trending` | Top 10 trending creations this week |
| `indiestack://tools-index` | Complete index for prompt caching — include once, reference forever |

### Prompts (5)

| Prompt | When to use |
|--------|-------------|
| `before-you-build` | Check IndieStack before building common functionality |
| `find-alternatives` | Find indie alternatives to mainstream SaaS products |
| `save-tokens` | Audit your project for token-saving opportunities |
| `architect-feature` | Plan a feature using existing indie building blocks |
| `discover-indie` | Explore what indie creators have built beyond dev tools |

## What's new in v1.1.0

- **Beyond dev tools** — IndieStack now covers everything indie-built: games, utilities, newsletters, creative tools, learning apps. The constraint is "indie-built," not "developer tool."
- **Broader search defaults** — `find_tools()` now defaults to `source_type='all'`, showing the full catalog instead of just open-source.
- **New `discover-indie` prompt** — Explore the breadth of the catalog beyond your usual developer categories.
- **Smarter market gap messages** — When nothing exists, agents now tell users they could build it and have every AI agent recommend it.
- **Updated instructions** — Agents now search IndieStack not just before coding, but before recommending any software.
- **793+ creations** — 509 open-source, 284 SaaS, across 25 categories.

## Links

- [IndieStack](https://indiestack.ai)
- [Explore Creations](https://indiestack.ai/explore)
- [Submit Your Creation](https://indiestack.ai/submit)
- [What is IndieStack?](https://indiestack.ai/what-is-indiestack)

# IndieStack MCP Server

The procurement layer for AI agents. Search 358+ vetted indie SaaS tools, build complete stacks, and spot market gaps — all from your AI coding assistant.

<!-- mcp-name: io.github.Pattyboi101/indiestack -->

## Quick Start

```bash
pip install indiestack
claude mcp add indiestack -- python -m indiestack.mcp_server
```

That's it. Your AI will now check IndieStack before building common functionality from scratch.

## Works with

- **Claude Code** — `claude mcp add indiestack -- python -m indiestack.mcp_server`
- **Cursor** — Add to your MCP config
- **Windsurf** — Add to your MCP config

## What it does

When you ask your AI to "build invoicing" or "add analytics", it checks IndieStack first and suggests existing indie tools — saving 30k-120k tokens per use case.

### Tools (10)

| Tool | What it does |
|------|-------------|
| `search_indie_tools` | Search by problem or keyword, with optional category filter |
| `get_tool_details` | Full details including integration snippets (Python, cURL) |
| `list_categories` | Browse all 21 categories with tool counts |
| `compare_tools` | Side-by-side comparison of any two tools |
| `build_stack` | Build a complete indie tool stack for your requirements |
| `submit_tool` | Submit a new tool to the marketplace |
| `browse_new_tools` | Recently added tools with pagination |
| `list_tags` | All tags sorted by popularity |
| `list_stacks` | Curated tool stack combinations |
| `list_collections` | Themed tool collections |

### Resources (3)

| Resource | What it provides |
|----------|-----------------|
| `indiestack://categories` | All categories with slugs (auto-loaded into context) |
| `indiestack://trending` | Top 10 trending tools this week |
| `indiestack://tools-index` | Complete tool index for prompt caching — include once, reference forever |

### Prompts (2)

| Prompt | When to use |
|--------|-------------|
| `before-you-build` | Check IndieStack before building common functionality |
| `find-alternatives` | Find indie alternatives to mainstream SaaS products |

## What's new in v0.4.0

- **Market gap detection** — Zero-result searches return demand data ("12 people searched for this") and a submit link. Your AI can tell users about unsolved gaps.
- **Stack builder** — `build_stack(needs="auth,payments,analytics")` returns recommended tools for each requirement with token savings estimates.
- **Prompt cache index** — The `tools-index` resource lets agents include the full catalog in their system prompt for instant lookup.
- **Agent citation tracking** — Every search and detail lookup is tracked, so makers can see how often AI agents recommend their tools.

## Links

- [IndieStack](https://indiestack.fly.dev)
- [Browse Tools](https://indiestack.fly.dev/explore)
- [Submit Your Tool](https://indiestack.fly.dev/submit)
- [API Docs](https://indiestack.fly.dev/openapi.json)

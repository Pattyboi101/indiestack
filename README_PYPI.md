# IndieStack MCP Server

The tool knowledge layer for AI agents. Search 480+ indie tools — from full SaaS products to tiny utilities — so your AI stops rebuilding solved problems.

<!-- mcp-name: io.github.Pattyboi101/indiestack -->

## Quick Start

```bash
# Option 1: pipx (recommended — handles venv automatically)
pipx install indiestack
claude mcp add indiestack -- indiestack-mcp

# Option 2: pip (if pipx isn't available)
pip install indiestack
claude mcp add indiestack -- indiestack-mcp

# Option 3: uvx (zero install — runs directly)
claude mcp add indiestack -- uvx indiestack-mcp
```

That's it. Your AI will now check IndieStack before building common functionality from scratch.

## Works with

- **Claude Code** — `claude mcp add indiestack -- indiestack-mcp`
- **Cursor** — Add `indiestack-mcp` to your MCP config
- **Windsurf** — Add `indiestack-mcp` to your MCP config

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
| `submit_tool` | Submit a new tool to IndieStack |
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

## What's new in v0.4.1

- **`indiestack-mcp` CLI command** — No more `python -m` incantations. Just `indiestack-mcp`.
- **480+ tools** — Catalog has grown 3x since initial launch.
- **Personalized recommendations** — Agent memory learns your tech stack and suggests tools you haven't seen.
- **Market gap detection** — Zero-result searches return demand data and a submit link.
- **Stack builder** — `build_stack(needs="auth,payments,analytics")` returns recommended tools with token savings estimates.

## Links

- [IndieStack](https://indiestack.fly.dev)
- [Browse Tools](https://indiestack.fly.dev/explore)
- [Submit Your Tool](https://indiestack.fly.dev/submit)
- [API Docs](https://indiestack.fly.dev/openapi.json)

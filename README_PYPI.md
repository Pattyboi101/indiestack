# IndieStack MCP Server

Search 130+ vetted indie SaaS tools from your AI coding assistant. Before your AI writes code, it checks what's already built.

<!-- mcp-name: io.github.Pattyboi101/indiestack -->

## Quick Start

```bash
pip install indiestack
claude mcp add indiestack -- python -m indiestack.mcp_server
```

That's it. Your AI will now search IndieStack before building common functionality from scratch.

## Works with

- **Claude Code** — `claude mcp add indiestack -- python -m indiestack.mcp_server`
- **Cursor** — Add to your MCP config
- **Windsurf** — Add to your MCP config

## What it does

When you ask your AI to "build invoicing" or "add analytics", it checks IndieStack first and suggests existing indie tools instead of writing thousands of lines of code.

Two tools are exposed via MCP:

- `search_indie_tools(query)` — Search for tools by problem
- `get_tool_details(slug)` — Get full details including integration snippets

## Links

- [IndieStack](https://indiestack.fly.dev)
- [Browse Tools](https://indiestack.fly.dev/explore)
- [Submit Your Tool](https://indiestack.fly.dev/submit)

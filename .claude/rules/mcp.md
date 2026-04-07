---
paths:
  - "src/indiestack/mcp_server.py"
  - "pyproject.toml"
  - "server.json"
  - "README_PYPI.md"
---

# IndieStack — MCP Server

## Version & Distribution
- Current version: v1.17.0 on PyPI (v1.17.1 ready to publish — Patrick to run /publish-mcp)
- Registry ID: `io.github.Pattyboi101/indiestack`, ~2,100 tokens footprint
- 23 tools, 3 resources, 5 prompts

## Architecture
- MCP server calls production API — backend changes take effect on deploy, but `mcp_server.py` changes need PyPI publish
- After version bump: update BOTH `pyproject.toml` AND `server.json`, then push to GitHub (Registry auto-refreshes from repo)

## Key Internals
- `DEPENDENCY_MAPPINGS` in mcp_server.py maps npm/pip packages to categories (e.g., "stripe" to "payments")
- `NEED_MAPPINGS` in db.py maps needs to categories with search terms
- httpx async + connection pooling, TTL cache (LRU, 200 max), circuit breaker (3-strike, 60s cooldown), retry, asyncio.gather for parallel fetches, ToolAnnotations

## Publishing
- Build: `python3 -m build`
- Upload: `python3 -m twine upload dist/indiestack-VERSION*`
- PyPI token configured in `~/.pypirc`

## API Keys
- `isk_` prefix, 3-tier rate limiting: keyless (15/day), free key (50/day), Pro (1000/day)

## CLI
- Ships in same package: `indiestack search "query"`, `indiestack details slug`, `indiestack stack "needs"`

## Pro Enrichment
- Pro API keys get enriched responses (citation counts, compatible tools, category percentile)

## Distribution
- Tracker: `marketing/mcp-directories.md`. 17/20 directories submitted.

## New Categories (Pass 13)
Three categories added to production DB — `list_categories` now returns these:

| Slug | Display Name |
|------|-------------|
| `caching` | Caching & In-Memory |
| `mcp-servers` | MCP Servers |
| `ai-standards` | AI Standards & Specs |

Agents querying for caching tools (Redis alternatives, in-memory stores) should find them under `caching`. Agents looking for MCP servers to compose with should find them under `mcp-servers`. Pass 13 guidance: leave `ai-standards` empty if fewer than 3 genuinely AI-specific standards tools qualify — do NOT move OpenAPI/AsyncAPI into it.

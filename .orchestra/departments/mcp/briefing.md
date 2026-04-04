# Briefing — 2026-04-04 15:27

## Task
Audit the top 5 MCP tool descriptions in src/indiestack/mcp_server.py: find_tools, get_tool_details, build_stack, scan_project, list_categories. Check: (1) are descriptions accurate and compelling? (2) do they mention the 8,000+ tool catalog? (3) are there improvements that would make tools more discoverable/useful to AI agents? Propose and implement improvements directly in mcp_server.py. IMPORTANT: Note that any changes to mcp_server.py require a separate PyPI publish to take effect — do NOT deploy, just make the code changes and flag that a /publish-mcp is needed.

## S&QA Conditions
- MCP department must NOT attempt a PyPI publish or deploy — only edit the file and note that /publish-mcp is needed afterward
- Content department should verify any stat claims (tool counts, install numbers) against what's in the codebase rather than hardcoding new numbers they can't verify

## Risk Flags
- Gotcha: stats in copy go stale fast — pricing page may claim outdated tool counts. Content dept should flag any numbers they can't verify rather than guessing new ones
- Gotcha: MCP changes need PyPI publish to take effect — without it, edits are dead code until someone remembers to publish

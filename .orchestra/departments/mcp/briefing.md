# Briefing — 2026-04-05

## Task
MCP server quality check and tool descriptions audit.

**Task 1 — Test 5 MCP tool calls against production:**
Using curl, call these API endpoints and check result quality:
1. `https://indiestack.ai/api/tools/search?q=authentication&limit=3` — should return Clerk, Next Auth, Better Auth
2. `https://indiestack.ai/api/tools/search?q=css+framework&limit=3` — should return Tailwind, Bootstrap, shadcn
3. `https://indiestack.ai/api/tools/search?q=mcp+server&limit=3` — should return MCP servers
4. `https://indiestack.ai/api/tools/search?q=background+jobs&limit=3` — should return Trigger.dev, BullMQ, Celery
5. `https://indiestack.ai/api/tools/search?q=caching&limit=3` — should return Redis, Upstash

Report results. Flag any misfires.

**Task 2 — MCP server description audit:**
Read `src/indiestack/mcp_server.py`. Check the `find_tools` tool description (lines ~260-280). Verify the tool count says "6,500+" not "8,000+". Check that `get_migration_data` is listed in the tool's docstring with correct description.

If any descriptions are stale/wrong, fix them and bump version to v1.15.1 in pyproject.toml. Do NOT publish to PyPI — just prep the change.

## Constraints
- Do NOT publish to PyPI without explicit instruction (/publish-mcp)
- Report search results accurately — do not summarize away misfires

## Meeting Task — 2026-04-05 (MCP Growth & Maker Pro)
- [ ] Rewrite PyPI README with Quick Install section (exact claude_desktop_config.json snippet front and centre)
- [ ] Audit all 23 MCP tool descriptions — flag any that are terse, misleading, or don't explain when to use them
- [ ] Draft spec for `get_maker_stats(tool_slug)` MCP tool — what should it return? (needs Backend to implement API first)

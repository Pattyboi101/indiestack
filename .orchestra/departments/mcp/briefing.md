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

## Meeting Task — 2026-04-07 (Future Models + Anthropic Pitch)
- [x] Publish gap dataset (top queries returning zero results from 10k install base) to data/gap-queries-2026-04.json | Done Apr 7 (189 gaps, 90 days)
- [x] Add session_id optional param to find_tools + get_tool_details in mcp_server.py — pass as X-Session-ID header | Done Apr 7
- [x] Add _build_confidence_rationale() to find_tools result formatting | Done Apr 7
- [x] PyPI publish with session_id + confidence rationale changes — v1.17.0 | Done Apr 7
- [ ] Build Conway manifest skeleton (.cnw.zip — 1 day max, signal piece only, not production code) | By: Apr 11
- [ ] Draft Conway spec GitHub issue as fallback if no DSP thread opens organically | By: Apr 11
- NOTE: session_id schema contract defined by Backend — build against their spec in meeting file

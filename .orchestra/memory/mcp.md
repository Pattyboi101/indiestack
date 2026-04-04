# MCP/Integration Memory

_Updated automatically by the orchestrator after each run._

## 2026-03-30 02:19
Task: Call the IndieStack production API (via get_tool_details MCP tool) for these 5 slugs: supabase, prisma, vitest, next-auth, tailwind-css. For each response, check for the presence and completeness of: install_command, env_vars, sdk_packages, migration data, and verified compatible tools (combos). Build a report table showing each tool × each field with ✅/⚠️/❌ ratings. Flag any tools with thin responses that would disappoint an AI agent trying to integrate them. Note specific gaps (e.g. 'missing env_vars', 'no install command', 'zero verified combos').
Result: Got everything I need (tailwind-css confirmed 404). Building the full report now.

---

## IndieStack API Quality Audit — `get_tool_details` × 5 Slugs

**Date:** 2026-03-30  
**Method:** Live producti

## 2026-03-30 02:42
Task: Query the production API at https://indiestack.ai/api/tools/search for each of these 5 queries: 'auth', 'payments', 'database', 'email', 'monitoring'. For each query, inspect the TOP result and check: (1) does it have a non-empty install_command field? (2) does it have a useful, descriptive tagline (not generic/empty)? (3) is the category field correct/relevant for the query? Compile a report table showing query, top result name, install_command (yes/no/value), tagline quality (good/weak/missing), category correctness (correct/wrong/missing). Flag which queries give poor first impressions to AI agents and why.
Result: Got all 5. Let me compile the full analysis now.

---

## Search API — Top Result Quality Audit

| Query | Top Result | `install_command` | Tagline Quality | Category |
|---|---|---|---|---|
| **auth*

## 2026-04-04 14:37
Task: After FTS rebuild, audit search quality for top queries by hitting the production /api/tools/search endpoint for: auth, payments, database, email, monitoring, analytics, orm, testing. For each: check top result relevance, presence of install_command, correct category. Flag any misfires or thin results. Also scan for any other quick wins in search ranking or response quality.
Result: Here's the full audit report:

---

## Post-FTS Rebuild — Search Quality Audit

### ✅ Passing Queries
| Query | Top Result | Verdict |
|-------|-----------|---------|
| **auth** | next-auth | ✅ 20 rel

## 2026-04-04 15:30
Task: Audit the top 5 MCP tool descriptions in src/indiestack/mcp_server.py: find_tools, get_tool_details, build_stack, scan_project, list_categories. Check: (1) are descriptions accurate and compelling? (2) do they mention the 8,000+ tool catalog? (3) are there improvements that would make tools more discoverable/useful to AI agents? Propose and implement improvements directly in mcp_server.py. IMPORTANT: Note that any changes to mcp_server.py require a separate PyPI publish to take effect — do NOT deploy, just make the code changes and flag that a /publish-mcp is needed.
Result: Done. Here's the summary:

---

**5 descriptions updated in `mcp_server.py`:**

| Tool | Fix |
|---|---|
| `find_tools` | Lede now opens with "Search **8,000+** developer tools" — was buried |
| `get_

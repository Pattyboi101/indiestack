# Briefing — 2026-04-04 22:28

## Task
Search quality spot check: run 5 queries against production API (https://indiestack.fly.dev/api/tools?q=QUERY&limit=3) for: 'react', 'frontend', 'css', 'animation', 'state management'. Report top 3 results for each query. Flag any obvious misfires (wrong category, irrelevant tools). If fixes are needed on production data, use the SSH file-upload pattern (write script to /tmp, sftp put, run) — do NOT use inline flyctl ssh python. Rebuild FTS if any changes made.

## S&QA Conditions
- MCP agent MUST use SSH file-upload pattern if making any production DB changes — added explicitly to their brief
- Content agent must verify any pricing references against stripe.md — $19/mo not $49
- Backend should exclude trpc from moves if its description is clearly 'API framework' rather than 'frontend framework' — let the slug query inform the decision

## Risk Flags
- trpc is arguably an API/RPC layer, not a frontend framework — backend should use judgment after reading its description
- MCP original brief didn't specify file-upload SSH pattern — corrected in approved version to prevent the nested-quotes gotcha

# Briefing — 2026-04-04 16:07

## Task
Read smoke_test.py and identify which important endpoints are NOT currently tested. Suggest 3-5 additions that would catch real regressions (e.g. MCP endpoints, search API, tool detail API, /analyze, /stacks). Add the new tests directly to smoke_test.py. CONDITION: Only add tests for GET/read-only endpoints — do NOT add tests that POST data or mutate production state. Ensure new tests check for 200 status codes and basic response structure, not hardcoded content that will go stale.

## S&QA Conditions
- Backend: use absolute paths for any SSH commands — 'cd' is a shell builtin and will fail in flyctl ssh
- Backend: throttle API requests slightly to avoid 429 rate limiting from rapid-fire queries
- Content: verify all stats against production DB before updating copy — stale stats have bitten us multiple times
- DevOps: new smoke tests must be read-only — no POST/PUT/DELETE against production endpoints

## Risk Flags
- Backend hitting production API 15+ times in quick succession could trigger rate limiting (known gotcha)
- Content editing f-string templates — a stray quote or bracket breaks the whole page, so test locally or at least eyeball the diff carefully

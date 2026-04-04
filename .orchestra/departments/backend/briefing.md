# Briefing — 2026-04-04 16:07

## Task
Query the search_events or analytics table on production to find the top 15 most-searched queries from the last 7 days. For each query, hit https://indiestack.fly.dev/api/tools/search?q=QUERY&limit=3 and check if the top result is relevant to the query intent. Flag any bad matches with explanation of why the result is poor. IMPORTANT: When SSH-ing to production, use absolute paths (e.g. python3 /app/scripts/...) — do NOT use 'cd /app &&'. Be mindful of API rate limiting — add a small delay between requests if needed.

## S&QA Conditions
- Backend: use absolute paths for any SSH commands — 'cd' is a shell builtin and will fail in flyctl ssh
- Backend: throttle API requests slightly to avoid 429 rate limiting from rapid-fire queries
- Content: verify all stats against production DB before updating copy — stale stats have bitten us multiple times
- DevOps: new smoke tests must be read-only — no POST/PUT/DELETE against production endpoints

## Risk Flags
- Backend hitting production API 15+ times in quick succession could trigger rate limiting (known gotcha)
- Content editing f-string templates — a stray quote or bracket breaks the whole page, so test locally or at least eyeball the diff carefully

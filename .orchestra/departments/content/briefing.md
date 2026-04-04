# Briefing — 2026-04-04 16:07

## Task
Review src/indiestack/routes/updates.py and src/indiestack/routes/what_is.py. Check: (1) Is the copy accurate and up-to-date (no stale stats, outdated feature claims)? (2) Is the page well-structured with clear purpose? (3) Are there any obvious copy issues, typos, or confusing sections? Fix anything clear-cut directly in the files. CONDITION: Before updating ANY stats (tool counts, category counts, install numbers), verify the actual numbers against the production DB or known current figures (8,000+ tools, 25+ categories, 10,000+ PyPI installs). Do NOT guess or leave old numbers.

## S&QA Conditions
- Backend: use absolute paths for any SSH commands — 'cd' is a shell builtin and will fail in flyctl ssh
- Backend: throttle API requests slightly to avoid 429 rate limiting from rapid-fire queries
- Content: verify all stats against production DB before updating copy — stale stats have bitten us multiple times
- DevOps: new smoke tests must be read-only — no POST/PUT/DELETE against production endpoints

## Risk Flags
- Backend hitting production API 15+ times in quick succession could trigger rate limiting (known gotcha)
- Content editing f-string templates — a stray quote or bracket breaks the whole page, so test locally or at least eyeball the diff carefully

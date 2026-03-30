# Playbook

_Master's accumulated knowledge. Updated after each orchestrator run._

## Strategic Lessons (2026-03-30)

1. **Distribution > Product polish.** With 0 users, every hour spent polishing is an hour not spent getting found. The product was "good enough" after the first round of fixes. Distribution should have started earlier.

2. **S&QA catches real bugs.** The broken claim links would have made 13 outreach emails worthless. The missing /tmp files would have wasted agent time. S&QA pays for itself in one catch.

3. **"Wait for signal" is a valid action.** After planting seeds (emails, blog, registries), the correct next step is to wait for data — not keep building. S&QA correctly vetoed continued busywork.

4. **Audit BEFORE outreach, not after.** Cal.com had the wrong install command. SuperTokens had nonsense. Check every target page before emailing the maker who built it.

5. **The differentiator must be visible at the comparison moment.** Migration signals were only in tool details (after clicking). Moving them to search results was the biggest product improvement — it's what makes us visibly different from a web search.

6. **Don't oversell, don't pivot.** "Moat" language was wrong. $299/mo pricing was wrong. "Just build it better than everyone else" is the actual strategy.

## GOTCHA: aiosqlite Row access
aiosqlite with row_factory=Row uses DICT access (row["column_name"]), NOT integer indexing (row[0]). This has bitten us TWICE: moat/stats endpoint and migration signals. When writing SQL queries that return rows, ALWAYS use column name aliases and access via row["alias"]. Add this to Backend CLAUDE.md.

## 2026-03-30 01:35
Task: check the landing page title tag and suggest if it could be improved for SEO
Verdict: approve
Total cost: $0.4542
Results:
- 📝 content: done ($0.1853)

## 2026-03-30 01:49
Task: Health check: run smoke tests, verify the site loads, check /health endpoint returns 200. If anything fails, describe what's wrong.
Verdict: approve
Total cost: $0.3206
Results:
- 🚀 devops: done ($0.0540)

## 2026-03-30 02:01
Task: Quick cleanup: find and fix any obvious issues in files changed in the last 3 git commits: typos in user-facing text, missing html.escape calls, hardcoded colors that should use CSS variables.
Verdict: approve
Total cost: $2.2148
Results:
- ⚡ frontend: done ($1.1502)
- 🔧 backend: done ($0.6905)
- 📝 content: done ($0.2296)

## 2026-03-30 02:03
Task: Security review: check for SQL injection in any raw f-string queries, missing html.escape on user input, exposed secrets in git-tracked files, any endpoints missing auth that should have it.
Verdict: approve
Total cost: $3.9620
Results:
- 🔧 backend: done ($1.2407)
- ⚡ frontend: done ($2.3742)
- 🚀 devops: done ($0.1921)

## 2026-03-30 02:13
Task: Check 3 key pages (landing, explore, tool detail) for accessibility: missing alt text, low contrast text, touch targets under 44px, missing ARIA labels on interactive elements. Fix anything clear-cut.
Verdict: approve
Total cost: $1.6966
Results:
- ⚡ frontend: done ($1.5559)

## 2026-03-30 02:16
Task VETOED: Review the 3 most recently changed route files for code quality: unused imports, SQL injection risks, missing html.escape on user input, hardcoded values that should be CSS variables. Fix anything clear-cut, flag anything ambiguous.
Reason: This is near-identical to two tasks completed less than 30 minutes ago. At 02:01 you ran 'Quick cleanup: find and fix any obvious issues in files changed in the last 3 git commits: typos in user-facing text, missing html.escape calls, hardcoded colors that should use CSS variables' ($2.21). At 02:03 you ran 'Security review: check for SQL injection in any raw f-string queries, missing html.escape on user input, exposed secrets in git-tracked files' ($3.96). Combined cost: $6.17 already spent on the exact same scope — SQL injection, html.escape, hardcoded colors — on recently changed files. The '3 most recently changed route files' are almost certainly the same files those tasks already reviewed and fixed. Running this again is paying $2-4 to re-audit work that was just done. With 53 users and no revenue, that's not defensible.

## 2026-03-30 02:19
Task: Audit the MCP server response quality: call the production API for 5 popular tools (supabase, prisma, vitest, next-auth, tailwind-css) and check if each response includes install_command, env_vars, sdk_packages, migration data, and verified combos. Report which tools have thin responses that would disappoint an AI agent.
Verdict: approve
Total cost: $0.3095
Results:
- 🔌 mcp: done ($0.1638)

## 2026-03-30 02:30
Task: The MCP API returns 404 for 'tailwind-css' even though Tailwind CSS exists in our catalog as a different slug. Investigate: what slug does Tailwind CSS actually have? Check if other commonly-searched tools have the same problem (agents searching for 'stripe', 'supabase', 'nextjs', 'prisma' etc and getting 404 because the slug doesn't match). If possible, add slug aliases or improve the /api/tools/{slug} endpoint to try common variations (npm-X, X-js, etc) before returning 404.
Verdict: challenge
Total cost: $1.0913
Results:
- 🔧 backend: done ($0.9111)

## 2026-03-30 02:34
Task: Check the /migrations page on production: does it show real data with actual numbers? Are the editorial insights rendering? Is the stats bar showing live counts? Quick UX check — not a code review, just verify the user experience is working.
Verdict: approve
Total cost: $0.3629
Results:
- ⚡ frontend: done ($0.2282)

## 2026-03-30 02:42
Task: Check what happens when an agent searches for tools via the MCP server: query the production API at /api/tools/search for 'auth', 'payments', 'database', 'email', 'monitoring'. For each, check: does the top result have install_command? Does it have a useful tagline? Is the category correct? Report which queries give poor first impressions to agents.
Verdict: approve
Total cost: $0.2425
Results:
- 🔌 mcp: done ($0.0998)

## 2026-03-30 02:54
Task: Check if the /analyze page works end-to-end: paste a sample package.json with express, prisma, jest, and tailwindcss into the analyzer and verify: (1) the health score renders, (2) migration intelligence shows for jest and express, (3) the page doesn't error. Test by POSTing to /api/analyze on production with a real manifest. Report what the user experience looks like.
Verdict: approve
Total cost: $0.5232
Results:
- 🔧 backend: done ($0.0860)
- ⚡ frontend: done ($0.2757)

## 2026-03-30 03:06
Task: Audit the new user onboarding flow: someone signs up via GitHub OAuth, lands on /welcome, then goes to /dashboard. Check: (1) does /welcome exist and load? (2) does /dashboard show useful content for a user with zero tools claimed and zero API keys? (3) is there a clear path from signup to first value (creating an API key, running their first search, analyzing their stack)? Read the route files, don't hit production. Report UX gaps.
Verdict: approve
Total cost: $1.1492
Results:
- 🔧 backend: done ($0.6631)
- ⚡ frontend: done ($0.3106)

# Backend Memory

_Updated automatically by the orchestrator after each run._

## 2026-03-30 02:01
Task: Review files changed in the last 3 git commits for missing html.escape() calls on user-supplied data injected into f-string HTML templates (tool names, descriptions, usernames, etc). Fix any found. Run: git diff HEAD~3 --name-only to get the file list.
Result: Fix is in place. The change is unstaged — Patrick can review before committing.

```json
{
  "status": "done",
  "files_changed": ["src/indiestack/routes/components.py"],
  "summary": "Reviewed all 4 

## 2026-03-30 02:03
Task: SQL injection audit: scan src/indiestack/db.py and all files in src/indiestack/routes/ for raw f-string SQL queries where user input is interpolated directly instead of using parameterized queries (?-placeholders). Also audit all route handlers for endpoints that modify data or access sensitive info but don't check request.state.user — compare against auth patterns in auth.py. Report every instance found with file path, line number, and severity.
Result: Got enough context. Here's the full audit report:

---

## Security Audit Report — SQL Injection & Auth

### SQL Injection

**Overall verdict: No confirmed user-reachable SQL injection.** All dynamic 

## 2026-03-30 02:30
Task: Investigate and fix slug resolution in the /api/tools/{slug} endpoint. 1) Query the SQLite database to find Tailwind CSS's actual slug and test these commonly-searched slugs: 'tailwind-css', 'stripe', 'supabase', 'nextjs', 'next-js', 'prisma', 'vercel', 'clerk', 'drizzle'. Document which 404 vs resolve. 2) Also check src/indiestack/mcp_server.py to understand how it constructs API calls — does it normalize slugs or pass them straight through? This determines whether the fix needs to be server-side only or both. 3) Implement a slug fallback mechanism in the API endpoint: before returning 404, try common variations (strip/add '-js'/'-css' suffixes, handle 'nextjs'→'next-js' style mismatches, case-insensitive name lookup as last resort). A slug_aliases dict for known mappings is preferred over complex heuristics — explicit > clever. 4) Test the fix against all previously-failing slugs before committing.
Result: Done. Here's the full picture:

---

**Investigation results:**

| Slug | Before | After | How |
|---|---|---|---|
| `tailwind-css` | 404 | **404** | No tool in DB — Tailwind is a CSS framework, not a

## 2026-03-30 02:54
Task: POST to https://indiestack.ai/api/analyze (or /api/analyze on production) with a real package.json manifest containing express, prisma, jest, and tailwindcss. Verify: (1) response returns 200 with a health score, (2) per-dependency data includes status and recommendations, (3) migration intelligence data is present for jest and express specifically, (4) no error responses. Report the full response structure.
Result: Clear picture. Here's the full audit report:

---

## `/api/analyze` Audit Report

### (1) Health Score — ✅ PASS
Returns 200 with a composite score object:
```json
{
  "score": {
    "total": 83,
    

## 2026-03-30 03:06
Task: Trace the GitHub OAuth signup flow end-to-end by reading source files. Start with src/indiestack/auth.py — find the OAuth callback handler and check: where does a NEW user get redirected after first signup? Does it go to /welcome, /dashboard, or somewhere else? Then check src/indiestack/routes/ for a welcome.py or similar file — does /welcome exist as a route? Read the dashboard route (src/indiestack/routes/dashboard.py) and analyze what SQL queries run for the logged-in user — what happens when a user has zero tools claimed, zero API keys, zero upvotes, zero searches? Does the route return empty data or meaningful defaults? Report the complete redirect chain: OAuth callback → first page → next page, and flag any dead ends.
Result: I have everything I need. Here's the full audit report:

---

## OAuth Signup Flow Audit

### Redirect Chain

**GitHub OAuth (new user):**
```
/auth/github
  → github.com/login/oauth/authorize
  → /au

## 2026-04-04 14:37
Task: After deploy completes, SSH into production and rebuild the FTS index: run `INSERT INTO tools_fts(tools_fts) VALUES('rebuild')` and `PRAGMA wal_checkpoint(TRUNCATE)` to pick up recent category fixes. Confirm no errors.
Result: All good. Here's the summary:

- **FTS rebuild**: ✅ `INSERT INTO tools_fts(tools_fts) VALUES('rebuild')` — completed without errors
- **WAL checkpoint**: ✅ `log=0, checkpointed=0` — WAL was already cl

## 2026-04-04 14:59
Task: Fix 3 search quality issues: (1) 'email' query returns Logto as #1 — check db.py engagement scoring and FTS weighting; if Logto's description is keyword-stuffed with email terms, UPDATE its description in the production DB to be accurate without email-heavy language, then check if a scoring fix in db.py (e.g. category penalty for auth tools on 'email' queries) is needed; (2) 'payments' returns laravel-stripe-webhooks as #1 — investigate its category assignment and FTS rank vs Stripe; fix by correcting its category_id to a more specific one (e.g. webhooks/integration) or adjusting engagement scoring to boost tools whose primary category matches the query term; (3) Duplicate cleanup — query the DB for (btcpay-server, btcpayserver) and (kill-bill, killbill): compare upvotes, view counts, and data completeness; UPDATE the weaker duplicate's status to 'pending' in each pair. After ALL DB changes, run: INSERT INTO tools_fts(tools_fts) VALUES('rebuild') and PRAGMA wal_checkpoint(TRUNCATE) to rebuild the FTS index.
Result: All done. Here's the summary:

```json
{
  "status": "done",
  "files_changed": ["production DB: /data/indiestack.db"],
  "summary": "Fixed 3 search quality issues. (1) Logto 'email' — removed 'email'

## 2026-04-04 15:17
Task: Data quality pass ONLY. Run queries against the LOCAL database to find: (A) top 20 approved tools with zero tags — suggest and apply appropriate tags based on name/description/category, (B) tools with obviously wrong categories — fix the most egregious mismatches. IMPORTANT: Do NOT use LIKE '%keyword%' for category matching — it catches substrings (gotcha). Use explicit slug lists or exact word matching. After all local DB changes, rebuild FTS: INSERT INTO tools_fts(tools_fts) VALUES('rebuild'). Note: these are LOCAL changes only — they'll need a separate production data fix later via SSH with absolute paths.
Result: Done. Here's the summary:

**Local DB: `/tmp/indiestack-local.db`** (based on today's backup)

---

**A — Tags applied (18 tools, was 5333 zero-tag → now 5315):**

| Tool | Tags added |
|---|---|
| np

## 2026-04-04 16:13
Task: Query the search_events or analytics table on production to find the top 15 most-searched queries from the last 7 days. For each query, hit https://indiestack.fly.dev/api/tools/search?q=QUERY&limit=3 and check if the top result is relevant to the query intent. Flag any bad matches with explanation of why the result is poor. IMPORTANT: When SSH-ing to production, use absolute paths (e.g. python3 /app/scripts/...) — do NOT use 'cd /app &&'. Be mindful of API rate limiting — add a small delay between requests if needed.
Result: Here's the full audit:

---

## Search Quality Audit — Top 15 Queries (7 days)

| # | Query | Count | Top Result | Status |
|---|-------|-------|-----------|--------|
| 1 | auth | 188 | Next Auth | ✅ 

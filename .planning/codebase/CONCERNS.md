# Codebase Concerns

**Analysis Date:** 2026-03-13

## Tech Debt

**Monolithic db.py (5,097 lines):**
- Issue: `src/indiestack/db.py` contains schema, ~95 inline migrations, seed data, enrichment data, and all query functions in a single file
- Files: `src/indiestack/db.py`
- Impact: Extremely difficult to navigate, high merge conflict risk, slow to understand for new contributors. init_db() alone spans 400+ lines of try/except migration blocks
- Fix approach: Split into `db/schema.py`, `db/migrations/`, `db/queries/`, `db/seeds.py`. Replace try/except migration pattern with a proper migration runner (numbered SQL files or alembic-lite approach)

**Inline migration system via try/except:**
- Issue: All schema migrations run via `try: SELECT col; except: ALTER TABLE ADD COLUMN` pattern in `init_db()`. There are ~50 bare `except Exception: pass` blocks in db.py alone. No migration versioning, no rollback capability
- Files: `src/indiestack/db.py` lines 826-1250+
- Impact: Silent migration failures are invisible. No way to know which migrations have run. Impossible to roll back a bad migration. Each app restart re-runs all migration checks
- Fix approach: Introduce a `schema_version` table and numbered migration files in `migrations/`. Run each migration once, record completion

**Monolithic main.py (3,414 lines):**
- Issue: `src/indiestack/main.py` contains middleware, background tasks, API endpoints (upvote, wishlist, subscribe, cite, badge SVGs, search API, tool submission API, live wire, demand signals, outbound clicks, boost handling, claim verification), sitemap generation, and more
- Files: `src/indiestack/main.py`
- Impact: Hard to find specific functionality. Routes that belong in route modules are mixed with app setup. Background task definitions mixed with request handlers
- Fix approach: Move API endpoints to `routes/api.py`, background tasks to `tasks.py`, badge/SVG endpoints to `routes/badges.py`

**Hardcoded enrichment data in db.py:**
- Issue: 100+ tool enrichment records (install commands, SDK packages, env vars, framework compatibility) are hardcoded as Python dicts in `db.py` lines 607-780
- Files: `src/indiestack/db.py`
- Impact: Adding or updating tool metadata requires code changes and redeployment. This data belongs in the database or a JSON config file
- Fix approach: Move enrichment data to a JSON file or admin-editable database table

**No connection pooling for SQLite:**
- Issue: Every HTTP request creates a new `aiosqlite.connect()` call via `get_db()`, sets 7 PRAGMAs, then closes on response. No connection reuse
- Files: `src/indiestack/db.py` lines 590-600, `src/indiestack/main.py` lines 571-617
- Impact: Under load (19K+ weekly visitors), connection setup overhead adds latency. PRAGMA execution on every request is wasteful
- Fix approach: Use a connection pool or a single persistent connection with proper async locking. Set PRAGMAs once at startup

**In-memory rate limiting:**
- Issue: Rate limit state (`_rate_limits`, `_admin_login_attempts`) stored in Python dicts in process memory
- Files: `src/indiestack/main.py` lines 37-126
- Impact: Rate limits reset on every deploy/restart. Not shared across processes (currently single-machine, so acceptable for now). Memory grows unbounded between cleanup cycles (cleanup only every 100 requests)
- Fix approach: Acceptable for single-machine deployment but should be documented. Add periodic time-based cleanup instead of request-count-based

**HTML templates as Python strings:**
- Issue: All HTML is built as Python f-strings across 38 route files. CSS is inline or in `components.py`. No component reuse beyond manual function calls
- Files: All files in `src/indiestack/routes/`, especially `components.py` (1,766 lines), `dashboard.py` (2,184 lines), `content.py` (1,962 lines)
- Impact: This is an intentional architectural choice (documented in CLAUDE.md). However, it makes CSS consistency hard to enforce, creates massive route files, and HTML escaping must be manually applied everywhere
- Fix approach: Not recommended to change (project philosophy). Focus on extracting more shared component functions into `components.py` to reduce duplication

## Known Bugs

**IP address extraction inconsistency:**
- Symptoms: Different endpoints use different methods to extract client IP
- Files: `src/indiestack/main.py` lines 576, 607, 978, 1021, 2185, 2855; `src/indiestack/routes/admin.py` line 1052; `src/indiestack/routes/tool.py` line 114
- Trigger: Some use `fly-client-ip` header first, some use `x-forwarded-for` first, some use `request.client.host` directly. Line 2185 uses only `x-forwarded-for` (missing `fly-client-ip`)
- Workaround: None -- rate limiting and analytics may be inaccurate for some endpoints
- Fix: Create a single `get_client_ip(request)` helper and use it everywhere

**Foreign key disable in delete_tool:**
- Symptoms: `PRAGMA foreign_keys = OFF` is set during tool deletion, then re-enabled
- Files: `src/indiestack/db.py` lines 2092-2117
- Trigger: Deleting any tool temporarily disables FK constraints for the entire connection
- Workaround: The `finally` block re-enables FKs, but if another query runs on the same connection concurrently (unlikely with aiosqlite but possible), FK checks are skipped
- Fix: Remove the PRAGMA toggle. Instead, ensure all referencing tables are listed in the deletion cascade

## Security Considerations

**XSS via HTML string templates:**
- Risk: With HTML built as Python f-strings, any user input not passed through `html.escape()` creates an XSS vector. Every route file imports `from html import escape` but correctness depends on developer discipline
- Files: All files in `src/indiestack/routes/`
- Current mitigation: `html.escape` is imported and used in all 34 route files. CSP header blocks external scripts (`script-src 'self' 'unsafe-inline'`)
- Recommendations: The `'unsafe-inline'` in CSP script-src weakens XSS protection significantly. Audit all f-string interpolations that render user content (tool names, descriptions, reviews, maker bios). Consider a helper function that wraps escape + truncation

**Admin password in environment variable:**
- Risk: Single shared admin password, no per-user admin accounts
- Files: `src/indiestack/auth.py` lines 11-14
- Current mitigation: PBKDF2 session tokens, rate limiting (5 attempts / 15 min), production requires env var
- Recommendations: Add per-admin user accounts or at minimum rotate the password periodically

**No CSRF tokens (Origin-header-only protection):**
- Risk: CSRF protection relies solely on Origin/Referer header checking. Some browsers or privacy extensions strip these headers
- Files: `src/indiestack/main.py` lines 478-500
- Current mitigation: Blocks requests with no Origin AND no Referer (returns 403). Allows requests with valid Origin from allowlist
- Recommendations: Add proper CSRF tokens to forms for defense-in-depth. Current approach blocks legitimate users behind strict privacy configs

**Stored IP addresses in plain text:**
- Risk: Raw client IPs stored in `submitted_from_ip` column on tools table
- Files: `src/indiestack/routes/submit.py` line 504, `src/indiestack/db.py` schema
- Current mitigation: Upvotes use hashed IPs (`ip_hash`), but submissions store raw IPs
- Recommendations: Hash IPs before storage, or document the retention/deletion policy for GDPR compliance

**Default upvote salt:**
- Risk: `_UPVOTE_SALT` defaults to `"indiestack-default-salt-change-me"` if env var is not set
- Files: `src/indiestack/db.py` line 13
- Current mitigation: Production should set env var; no runtime check enforces this
- Recommendations: Add a startup check (like the admin password check) that fails in production without proper salt

## Performance Bottlenecks

**Per-request database connection + PRAGMA setup:**
- Problem: Every HTTP request opens a new SQLite connection and executes 7 PRAGMA statements
- Files: `src/indiestack/db.py` `get_db()`, `src/indiestack/main.py` `db_middleware()`
- Cause: No connection pooling. PRAGMAs like `journal_mode=WAL` are connection-level settings that persist, but `synchronous`, `cache_size`, `mmap_size`, and `temp_store` are re-set every request
- Improvement path: Set PRAGMAs once at startup (WAL mode persists across connections). Use a connection pool or singleton connection

**Per-tool upvote check loop:**
- Problem: `api_upvote_check` loops through up to 50 tool IDs, making one DB query per tool
- Files: `src/indiestack/main.py` lines 1006-1027
- Cause: `has_upvoted()` called in a loop instead of a single batch query
- Improvement path: Use `WHERE tool_id IN (?, ?, ...)` single query

**Page view tracking on every request:**
- Problem: Every non-API, non-static page request inserts a row into `page_views` table
- Files: `src/indiestack/main.py` lines 606-613
- Cause: Synchronous insert in the request middleware path
- Improvement path: Batch inserts using an in-memory buffer, flush periodically. Or move to async background task

**Background task scheduling:**
- Problem: 5 background tasks use `asyncio.sleep(86400)` (24 hours) for daily checks, with day-of-week checks inside
- Files: `src/indiestack/main.py` lines 166-451
- Cause: No proper scheduler. Tasks wake daily, check if it's the right day, then go back to sleep
- Improvement path: Use a lightweight scheduler like `apscheduler` or at minimum reduce the sleep/check pattern

## Fragile Areas

**init_db() migration chain:**
- Files: `src/indiestack/db.py` lines 826-1250+
- Why fragile: 400+ lines of sequential try/except blocks. If any migration silently fails, downstream code may crash on missing columns. No logging of which migrations ran
- Safe modification: Always add new migrations at the end of init_db(). Never remove old migration blocks. Test locally before deploying
- Test coverage: No automated tests. Only smoke_test.py (HTTP endpoint checks, no DB schema verification)

**components.py shared HTML:**
- Files: `src/indiestack/routes/components.py` (1,766 lines)
- Why fragile: `page_shell()`, `tool_card()`, and CSS variables are used by every route. Any change to the page shell, nav, or CSS tokens affects the entire site
- Safe modification: Test visually after any change. Smoke test covers endpoint status codes but not rendering correctness
- Test coverage: None beyond smoke tests

**Stripe payment flow:**
- Files: `src/indiestack/main.py` lines 2862-2891 (boost), `src/indiestack/routes/dashboard.py` (connect), `src/indiestack/routes/purchase.py`
- Why fragile: Stripe webhook handling, boost activation, and connect onboarding are spread across multiple files. Payment failures are caught with bare `except Exception: pass`
- Safe modification: Always test with Stripe test mode. Log all payment-related exceptions
- Test coverage: No payment tests exist

## Scaling Limits

**Single SQLite database:**
- Current capacity: ~3,100 tools, ~20 users, 19K weekly visitors
- Limit: SQLite with WAL mode handles moderate read traffic well but will bottleneck on concurrent writes. Single-machine Fly.io deployment (512MB RAM, shared CPU) limits vertical scaling
- Scaling path: For reads, add caching layer (Redis or in-memory). For writes, consider PostgreSQL migration if write contention becomes an issue. For horizontal scaling, SQLite must be replaced

**Single Fly.io machine:**
- Current capacity: 512MB RAM, 1 shared CPU, auto-stop enabled
- Limit: Cold starts when machine is stopped. Memory pressure with 256MB mmap + in-memory temp tables + rate limit dicts + caches
- Scaling path: Increase VM size, add min_machines_running > 1 (requires PostgreSQL first for shared state)

**Page views table growth:**
- Current capacity: Every pageview inserts a row
- Limit: Table grows ~19K rows/week minimum. `cleanup_old_page_views` exists but cleanup frequency and retention period determine table size
- Scaling path: Aggregate old page views into daily/weekly summary tables

## Dependencies at Risk

**aiosqlite:**
- Risk: Low maintenance activity. Last significant update may lag behind Python versions
- Impact: Core dependency -- all database access goes through it
- Migration plan: Could switch to `sqlite3` with `asyncio.to_thread()` wrappers, or move to PostgreSQL with `asyncpg`

## Missing Critical Features

**No automated database backups:**
- Problem: SQLite database at `/data/indiestack.db` on a Fly.io volume has no automated backup strategy
- Blocks: Disaster recovery. A volume failure or bad migration could lose all data (3,100+ tools, user accounts, purchase records)
- Fix: Add a periodic backup task that copies the DB to object storage (S3/R2), or use Fly.io's volume snapshots with a cron schedule

**No automated test suite:**
- Problem: Only `smoke_test.py` exists (HTTP status code checks for ~40 endpoints). No unit tests, no integration tests, no database tests
- Blocks: Safe refactoring, confident deployments, regression detection
- Fix: Add pytest infrastructure with at minimum: database migration tests, authentication flow tests, submission/approval flow tests, payment webhook tests

## Test Coverage Gaps

**No database layer tests:**
- What's not tested: Schema creation, migrations, query functions, FTS search, upvote/wishlist logic
- Files: `src/indiestack/db.py` (5,097 lines, 0 tests)
- Risk: Migration bugs silently corrupt data. Query logic errors only caught in production
- Priority: High

**No authentication flow tests:**
- What's not tested: Login, signup, password reset, email verification, GitHub OAuth, session management
- Files: `src/indiestack/auth.py`, `src/indiestack/routes/account.py`
- Risk: Auth bypasses or session handling bugs could go undetected
- Priority: High

**No payment flow tests:**
- What's not tested: Stripe Connect onboarding, boost payments, webhook handling, commission calculations
- Files: `src/indiestack/main.py` (boost), `src/indiestack/routes/dashboard.py` (connect), `src/indiestack/routes/purchase.py`
- Risk: Payment bugs could result in lost revenue or incorrect charges
- Priority: High

**No HTML output validation:**
- What's not tested: Whether rendered HTML is valid, whether user content is properly escaped, whether CSS changes break layout
- Files: All route files in `src/indiestack/routes/`
- Risk: XSS vulnerabilities from missed escaping, broken pages from template changes
- Priority: Medium

---

*Concerns audit: 2026-03-13*

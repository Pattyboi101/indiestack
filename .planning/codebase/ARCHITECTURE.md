# Architecture

**Analysis Date:** 2026-03-13

## Pattern Overview

**Overall:** Monolithic server-rendered FastAPI application with Python string-template HTML (no template engine, no frontend framework)

**Key Characteristics:**
- Single-process Python web app with all routes, DB, and HTML rendering in one deployment
- All HTML is generated as Python f-strings in route handlers and component functions -- no Jinja2, no React, no build step
- SQLite database with WAL mode accessed via aiosqlite (async)
- Separate MCP server (`mcp_server.py`) distributed as a PyPI package that calls the web API via HTTP
- Background tasks run as asyncio tasks in the same process (no Celery, no task queue)
- All CSS lives in `components.py` design_tokens() and inline styles -- no external stylesheets

## Layers

**HTTP/Middleware Layer:**
- Purpose: Request lifecycle, security, rate limiting, DB connection management, user auth resolution
- Location: `src/indiestack/main.py` (lines 460-617)
- Contains: Domain redirect, CSRF protection, security headers, rate limiting, DB middleware, API key resolution, pageview tracking
- Depends on: `auth.py`, `db.py`
- Used by: All route handlers receive `request.state.db` and `request.state.user` pre-populated

**Route Layer:**
- Purpose: HTTP endpoint handlers -- each module owns a feature area
- Location: `src/indiestack/routes/` (40+ Python files)
- Contains: FastAPI `APIRouter` instances, HTML page rendering, form handling, API endpoints
- Depends on: `db.py` for queries, `components.py` for shared HTML, `email.py` for notifications
- Used by: Mounted on the main `app` via `app.include_router()` in `main.py`

**Component/Template Layer:**
- Purpose: Shared HTML generation -- design system, layout, reusable UI components
- Location: `src/indiestack/routes/components.py` (1,766 lines)
- Contains: `page_shell()` (full HTML document wrapper with nav/footer), `tool_card()`, `maker_card()`, design tokens (CSS variables), JavaScript helpers (`upvote_js()`, `wishlist_js()`, `theme_js()`)
- Depends on: `config.py` for `BASE_URL`
- Used by: Every route that returns HTML

**Database Layer:**
- Purpose: Schema definition, migrations, all SQL queries, seed data
- Location: `src/indiestack/db.py` (5,097 lines -- the largest file)
- Contains: `SCHEMA` string (DDL), `FTS_SCHEMA` (full-text search), `get_db()`, `init_db()`, 100+ async query functions, `CATEGORY_TOKEN_COSTS`, `NEED_MAPPINGS`, `TECH_KEYWORDS` lookup dicts
- Depends on: `aiosqlite`, environment variables for DB path
- Used by: All route handlers, background tasks, middleware

**Auth Layer:**
- Purpose: Admin session validation, user password hashing (PBKDF2), user session management
- Location: `src/indiestack/auth.py` (84 lines)
- Contains: `check_admin_session()`, `hash_password()`, `verify_password()`, `get_current_user()`, `create_user_session()`
- Depends on: `db.py` for session lookup
- Used by: Middleware (populates `request.state.user`), route handlers for login/signup

**Email Layer:**
- Purpose: Transactional and marketing email via SMTP
- Location: `src/indiestack/email.py` (1,321 lines)
- Contains: `send_email()` (async, uses `asyncio.to_thread` for blocking SMTP), email templates as Python f-strings (purchase receipt, verification, weekly digest, ego ping, tool-of-week, etc.)
- Depends on: stdlib `smtplib`, `config.py`
- Used by: Background tasks in `main.py`, route handlers (dashboard, admin)

**MCP Server Layer:**
- Purpose: Model Context Protocol server for AI coding assistants (Claude, Cursor, Windsurf)
- Location: `src/indiestack/mcp_server.py` (1,597 lines)
- Contains: MCP tool definitions (`find_tools`, `get_tool_details`, `build_stack`, `scan_project`, etc.), HTTP client to IndieStack API, TTL cache, circuit breaker
- Depends on: `mcp[cli]`, `httpx` -- calls the web API over HTTP, does NOT import `db.py` directly
- Used by: Distributed as `indiestack` PyPI package, run via `indiestack-mcp` CLI entry point

**Background Tasks:**
- Purpose: Periodic automated operations
- Location: `src/indiestack/main.py` (lines 166-451, in `lifespan()`)
- Contains: Session cleanup (hourly), weekly ego ping (Fridays), auto tool-of-the-week (Mondays), badge nudge (48-72h after approval), weekly digest (Fridays)
- Depends on: `db.py`, `email.py`
- Used by: Started as `asyncio.create_task()` in app lifespan

**Configuration Layer:**
- Purpose: Centralized config values
- Location: `src/indiestack/config.py` (3 lines -- just `BASE_URL`)
- Contains: `BASE_URL` from `BASE_URL` env var, defaults to `https://indiestack.ai`
- Used by: All layers that generate URLs

## Data Flow

**Page Request (e.g., GET /tool/{slug}):**

1. Request hits middleware stack: domain redirect -> CSRF check -> security headers -> rate limit check -> DB connection opened (`get_db()`) -> user session resolved from `indiestack_session` cookie -> API key resolved if `/api/` path -> pageview tracked
2. Route handler receives `request.state.db` (aiosqlite connection) and `request.state.user` (dict or None)
3. Handler calls async query functions from `db.py` (e.g., `get_tool_by_slug()`)
4. Handler builds HTML string using component functions from `components.py` (e.g., `tool_card()`, `page_shell()`)
5. Returns `HTMLResponse` with full document (CSS inlined via `design_tokens()`)
6. Middleware closes DB connection in `finally` block

**API Request (e.g., GET /api/tools/search):**

1. Same middleware pipeline
2. Route handler in `main.py` (API endpoints are defined directly in `main.py`, not in route modules)
3. Queries DB, returns `JSONResponse` with tool data
4. MCP server or external clients consume this JSON

**MCP Tool Call (e.g., find_tools):**

1. AI assistant invokes MCP tool via stdio protocol
2. `mcp_server.py` receives call, checks cache (TTL-based)
3. Makes HTTP request to `https://indiestack.ai/api/tools/search` via persistent `httpx.AsyncClient`
4. Circuit breaker protects against API downtime (3 consecutive 5xx -> 60s cooldown)
5. Returns structured result to AI assistant

**State Management:**
- Server-side sessions: `sessions` table with 30-day token expiry, cookie `indiestack_session`
- Admin sessions: Separate cookie `indiestack_admin` with HMAC token
- No client-side state framework -- all state is server-rendered
- Dark mode toggle: `localStorage` + `data-theme` attribute (client-side JS in `theme_js()`)
- In-memory caches: Landing page cache (5-min TTL), sitemap cache (1-hour TTL), rate limit dicts

## Key Abstractions

**Tool (core entity):**
- Purpose: Represents an indie tool/creation listed on the platform
- Schema: `tools` table with 30+ columns (name, slug, tagline, description, url, category_id, tags, status, is_verified, upvote_count, price_pence, source_type, replaces, api_type, install_command, etc.)
- Statuses: `pending` -> `approved` / `rejected`
- FTS: Full-text search via `tools_fts` virtual table (SQLite FTS5)

**Maker (creator entity):**
- Purpose: Profile for tool creators
- Schema: `makers` table (slug, name, url, bio, avatar_url)
- Linked to: `users` table via `users.maker_id`, `tools` table via `tools.maker_id`

**User (auth entity):**
- Purpose: Authenticated user account
- Schema: `users` table (email, password_hash, role: buyer/maker/admin, maker_id)
- Auth: Cookie-based sessions, PBKDF2-SHA256 password hashing, optional GitHub OAuth

**Collection/Stack (grouping):**
- Purpose: Curated tool bundles
- Schema: `stacks` table + `stack_tools` junction, `collections` table (legacy, redirects to stacks)

**Agent Card:**
- Purpose: Machine-readable JSON metadata per tool for AI agents
- Served at: `/cards/{slug}.json` and `/cards/index.json`
- Protocol: A2A (Agent-to-Agent) discovery via `/.well-known/agent-card.json`

## Entry Points

**Web Server:**
- Location: `src/indiestack/__main__.py`
- Triggers: `python -m indiestack` or Docker CMD
- Responsibilities: Starts uvicorn on PORT (default 8080), creates the FastAPI app from `main.py`

**MCP Server:**
- Location: `src/indiestack/mcp_server.py` (entry point: `main()`)
- Triggers: `indiestack-mcp` CLI command (PyPI script entry point)
- Responsibilities: Starts MCP stdio server, manages httpx client lifecycle

**FastAPI App:**
- Location: `src/indiestack/main.py` line 454: `app = FastAPI(lifespan=lifespan, ...)`
- Triggers: Imported by uvicorn as `indiestack.main:app`
- Responsibilities: Registers all middleware, mounts 34 route modules, defines inline API endpoints, manages background tasks

## Error Handling

**Strategy:** Defensive with fallback -- errors are caught and logged, operations degrade gracefully

**Patterns:**
- Background tasks: Wrapped in try/except, failures logged via `_logger.exception()` and optionally sent to Telegram via `_alert_telegram()`
- Route handlers: Most wrap DB operations in try/except, return error HTML or JSON
- Middleware: Generic exception handler returns `{"error": "Internal server error"}` with 500 status
- 404: Custom HTML page with search box rendered via `page_shell()`
- Upvote/wishlist notifications: Wrapped in try/except with `pass` -- notification failure never breaks the primary operation
- MCP server: Circuit breaker pattern (3 failures -> 60s cooldown), `ToolError` exceptions for user-facing errors

## Cross-Cutting Concerns

**Logging:** Python stdlib `logging` module, logger name `"indiestack"`. Telegram alerts for background task failures on production (via bash script at `/home/patty/.claude/telegram.sh`).

**Validation:** Manual validation in route handlers -- no Pydantic models for request bodies. Form data parsed with `request.form()`, JSON with `request.json()`. Input sanitized with `html.escape()`.

**Authentication:** Two parallel auth systems:
- Admin: Environment variable password (`INDIESTACK_ADMIN_PASSWORD`), HMAC session token in `indiestack_admin` cookie, rate-limited login (5 attempts / 15 min)
- User: Email/password signup with PBKDF2 hashing, or GitHub OAuth. Session token in `indiestack_session` cookie (30-day expiry). Resolved in middleware and stored in `request.state.user`.

**Rate Limiting:** In-memory dict-based rate limiting per IP+path (not distributed -- single-server deployment). Configurable per-endpoint limits (e.g., /submit: 3/min, /api/: 30/min). Admin login has separate stricter limits.

**Caching:** In-memory Python dicts with TTL:
- Landing page data: 5-minute TTL (`_landing_cache`)
- Sitemap XML: 1-hour TTL (`_sitemap_cache`)
- MCP server: Per-query TTL cache, max 200 entries
- Logo/founder photos: Cached in memory on first read

**SEO:** Comprehensive sitemap generation, robots.txt with llms.txt references, programmatic pages for alternatives/comparisons/use-cases/tags/best-of, JSON-LD structured data on tool pages.

---

*Architecture analysis: 2026-03-13*

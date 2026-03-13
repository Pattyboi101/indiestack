# External Integrations

**Analysis Date:** 2026-03-13

## APIs & External Services

**Stripe (Payments):**
- Stripe Checkout - One-time payments (Boost at 29 GBP) and subscriptions (Demand Pro at 15 GBP/mo)
  - SDK: `stripe` >=8.0.0 (imported lazily in route handlers)
  - Auth: `STRIPE_SECRET_KEY`, `STRIPE_BOOST_PRICE_ID`, `STRIPE_DEMAND_PRO_PRICE_ID`
  - Checkout creation: `src/indiestack/main.py` lines 2622-2688 (boost), 2746-2772 (demand pro)
  - Webhook handler: `src/indiestack/main.py` lines 2775-2821 at `/webhooks/stripe`
  - Webhook verification: `src/indiestack/payments.py` (gitignored, not in repo -- contains `STRIPE_SECRET_KEY`, `verify_webhook`, `create_connect_account`, `create_onboarding_link`, `create_stack_checkout_session`, `create_transfer`, `calculate_commission`, `is_launch_holiday`)
- Stripe Connect - Marketplace payments to makers (5% platform fee, 3% Pro)
  - Connect account creation: `src/indiestack/routes/dashboard.py` line 1647
  - Onboarding link generation: `src/indiestack/routes/dashboard.py` line 1659
  - Stack bundle purchases: `src/indiestack/routes/stacks.py` lines 450-510
  - Constants: `PLATFORM_FEE_PERCENT`, `PRO_FEE_PERCENT` (from `payments.py`)

**GitHub API:**
- OAuth login - User authentication via GitHub
  - Client: `httpx` (async HTTP)
  - Auth: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
  - Implementation: `src/indiestack/routes/account.py`
  - Endpoints: `/auth/github` (redirect), `/auth/github/callback` (token exchange)
  - DB functions: `get_user_by_github_id`, `create_github_user`, `link_github_to_user` in `src/indiestack/db.py`
- GitHub REST API - Repo metadata fetching
  - Used for: auto-filling submission forms, README enrichment, auto-indexing
  - Auth: `GITHUB_TOKEN` (personal access token, optional)
  - Fetch endpoint: `src/indiestack/main.py` `/api/github-fetch` (line 2690)
  - Enricher: `src/indiestack/enricher.py` - Fetches READMEs, extracts install commands, env vars, framework mentions
  - Indexer: `src/indiestack/indexer.py` - Discovers indie projects by GitHub topic/search, imports as pending tools

**IndexNow (Search Engine Notification):**
- Notifies Bing/Yandex of new/updated URLs
  - Auth: `INDEXNOW_KEY`
  - Implementation: `src/indiestack/main.py` lines 686-688, 846-850
  - Verification file served at `/{key}.txt`

**Telegram (Error Alerting):**
- Fire-and-forget error notifications to Patrick
  - Implementation: `src/indiestack/main.py` `_alert_telegram()` function (line 15)
  - Mechanism: Calls bash script at `/home/patty/.claude/telegram.sh` via `subprocess.Popen`
  - Used by: Background task failures (ego ping, TOTW, badge nudge, weekly digest)
  - Production-only (script path is on Fly.io machine)

## Data Storage

**Database:**
- SQLite 3 with WAL mode
  - Path: `INDIESTACK_DB_PATH` (default: `/data/indiestack.db`)
  - Client: `aiosqlite` >=0.19.0 (async wrapper)
  - Connection: Per-request middleware in `src/indiestack/main.py` (opens/closes connection per request)
  - Schema: `src/indiestack/db.py` lines 17-419 (SCHEMA constant)
  - Full-text search: SQLite FTS5 on `tools` and `makers` tables (`src/indiestack/db.py` lines 421-466)
  - Migrations: `migrations/add_submitter_email.sql` (manual SQL files)

**Key Tables (30+ tables):**
- `tools` - 3,095+ tool listings with metadata, pricing, verification status
- `makers` - Maker profiles linked to tools
- `users` - User accounts (buyer/maker/admin roles)
- `sessions` - Cookie-based auth sessions (30-day expiry)
- `categories` - 25 tool categories with slugs
- `purchases` / `stack_purchases` - Payment records
- `subscriptions` - Stripe subscription tracking (demand_pro, pro plans)
- `upvotes` - Anonymous upvotes (IP-hash based)
- `reviews` - User reviews (1-5 stars, verified purchase flag)
- `wishlists` - User wishlists
- `collections` / `stacks` - Curated tool bundles
- `search_logs` - Query analytics (web + API + MCP sources)
- `page_views` - Analytics tracking
- `outbound_clicks` - Click-through tracking
- `api_keys` / `api_usage_logs` - API key management
- `notifications` - In-app notifications
- `agent_citations` - AI agent tool citation tracking
- `sponsored_placements` - Sponsored alternative suggestions

**File Storage:**
- Local filesystem only (logo images in `/app/logo/`, founder photos in `/app/founder-photos/`)
- No cloud storage (S3, GCS, etc.)

**Caching:**
- In-memory Python dicts only (no Redis, no Memcached)
- Sitemap cache: `_sitemap_cache` in `src/indiestack/main.py` line 129
- MCP server TTL cache: `_cache` dict in `src/indiestack/mcp_server.py` (max 200 entries)
- Rate limit state: `_rate_limits` dict in `src/indiestack/main.py` line 37

## Authentication & Identity

**Custom Auth (Primary):**
- Cookie-based sessions with 30-day expiry
  - Session cookie: `indiestack_session` (user auth)
  - Admin cookie: `indiestack_admin` (admin panel)
  - Password hashing: PBKDF2-HMAC-SHA256, 600K iterations, 32-byte salt (`src/indiestack/auth.py`)
  - Session tokens: `secrets.token_urlsafe(32)`
  - Implementation: `src/indiestack/auth.py`

**GitHub OAuth (Secondary):**
- Sign in with GitHub button on login/signup
  - Auth: `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
  - Implementation: `src/indiestack/routes/account.py`
  - Can link existing accounts or create new ones

**Admin Auth:**
- Password-based with HMAC session token
  - Auth: `INDIESTACK_ADMIN_PASSWORD`
  - Rate limited: 5 attempts per 15 minutes per IP
  - Implementation: `src/indiestack/auth.py` lines 18-26

**User Roles:**
- `buyer` (default), `maker`, `admin` - Stored in `users.role` column

## Email (SMTP)

**Provider:** Gmail SMTP (pajebay1@gmail.com)
- Implementation: `src/indiestack/email.py`
- Transport: stdlib `smtplib` with STARTTLS (port 587)
- Async wrapper: `asyncio.to_thread()` for non-blocking sends
- Auth: `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM`

**Email Types (all HTML templates in `src/indiestack/email.py`):**
- Purchase receipts
- Password reset tokens
- Email verification tokens
- Welcome signup
- Maker welcome
- Ego ping (weekly stats)
- Wishlist update notifications
- Weekly subscriber digest
- Outreach emails (admin panel: `src/indiestack/routes/admin_outreach.py`)

**Newsletter:**
- Subscriber management: `subscribers` and `email_optouts` tables
- One-click unsubscribe via `List-Unsubscribe` header
- Weekly auto-digest: Background task in `src/indiestack/main.py`

## Monitoring & Observability

**Error Tracking:**
- No external service (no Sentry, Datadog, etc.)
- Telegram alerts for background task failures (production only)
- Python `logging` module throughout

**Logs:**
- Standard Python logging to stdout (captured by Fly.io)
- Logger name: `indiestack` (and sub-loggers like `indiestack.email`, `indiestack.stacks`)

**Analytics:**
- Custom built-in analytics (no Google Analytics, no Plausible)
- `page_views` table: timestamp, page, visitor_id, referrer
- `search_logs` table: query, source, result_count
- `outbound_clicks` table: tool_id, url, ip_hash, referrer
- `agent_citations` table: AI agent tool citation tracking
- Admin analytics dashboard: `src/indiestack/routes/admin_analytics.py`

**Health Check:**
- `/health` endpoint returning `{"status": "ok"}`
- Fly.io checks: every 30s, 5s timeout, 10s grace period

## CI/CD & Deployment

**Hosting:**
- Fly.io (single machine, `sjc` region)
- Config: `fly.toml`
- Volume: `indiestack_data` mounted at `/data`

**CI Pipeline:**
- No CI/CD pipeline (no GitHub Actions, no CircleCI)
- Manual deploy: `cd /home/patty/indiestack && ~/.fly/bin/flyctl deploy --remote-only`
- Pre-deploy: Syntax check all `.py` files + run `smoke_test.py`

**Docker:**
- Multi-stage build in `Dockerfile`
- Stage 1: Install dependencies with `pip install ".[server]"`
- Stage 2: Copy site-packages + source code
- Entrypoint: `python -m indiestack`

## MCP Protocol (AI Agent Integration)

**MCP Server:**
- Published as PyPI package: `pip install indiestack`
- Entry point: `indiestack-mcp` command (maps to `src/indiestack/mcp_server.py:main`)
- Transport: stdio (for Claude, Cursor, Windsurf integration)
- Registry: Smithery (`smithery.yaml`), MCP server schema (`server.json`)
- Features: Tool search, stack building, project scanning, compatibility reports
- Client: `httpx` calling `https://indiestack.ai/api/*` endpoints
- Circuit breaker: 3 failures -> 60s cooldown (`src/indiestack/mcp_server.py` lines 53-56)

**Agent Card Protocol:**
- Per-tool JSON cards at `/cards/{slug}.json`
- Index at `/cards/index.json`
- A2A (Agent-to-Agent) protocol compatible

## Webhooks & Callbacks

**Incoming:**
- `/webhooks/stripe` - Stripe payment/subscription events (`src/indiestack/main.py` line 2775)
  - Handles: `checkout.session.completed`, `customer.subscription.deleted`
  - CSRF exempt (origin check bypassed)
- `/auth/github/callback` - GitHub OAuth callback (`src/indiestack/routes/account.py`)

**Outgoing:**
- IndexNow notifications to search engines (on new tool approval)
- Telegram alerts via bash script (on background task failures)

## Security

**CSRF Protection:**
- Origin header validation on all POST/PUT/DELETE/PATCH requests
- Exempt paths: `/webhooks/stripe`, `/api/cite`, `/api/tools/submit`, `/api/follow-through`
- Allowed origins: `indiestack.ai`, `indiestack.fly.dev`, `localhost:8000`
- Implementation: `src/indiestack/main.py` lines 462-498

**Rate Limiting:**
- In-memory per-IP rate limiting (60-second windows)
- Endpoint-specific limits (login: 10/min, signup: 10/min, submit: 3/min, etc.)
- Admin login: 5 attempts per 15 minutes
- Implementation: `src/indiestack/main.py` lines 37-126

**Security Headers:**
- Added via middleware in `src/indiestack/main.py`
- HTTPS forced via Fly.io (`force_https: true` in `fly.toml`)

**Secrets Management:**
- `src/indiestack/payments.py` is gitignored (contains Stripe keys and payment logic)
- All secrets via environment variables (set as Fly.io secrets in production)
- `.env` files not committed

---

*Integration audit: 2026-03-13*

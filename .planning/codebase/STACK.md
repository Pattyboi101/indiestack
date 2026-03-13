# Technology Stack

**Analysis Date:** 2026-03-13

## Languages

**Primary:**
- Python 3.11 - All backend, frontend HTML generation, MCP server, CLI tools

**Secondary:**
- SQL (SQLite dialect) - Schema, queries, FTS5 full-text search in `src/indiestack/db.py`
- CSS - Inline within Python string templates in `src/indiestack/routes/components.py`
- JavaScript - Minimal inline scripts for dark mode toggle, upvote buttons, search widget

## Runtime

**Environment:**
- Python 3.11-slim (Docker base image)
- Single-process uvicorn ASGI server

**Package Manager:**
- pip (via hatchling build system)
- Lockfile: Not present (dependencies pinned with `>=` minimum versions in `pyproject.toml`)

## Frameworks

**Core:**
- FastAPI >=0.109.0 - Web framework, all routes and middleware (`src/indiestack/main.py`)
- Starlette - Underlying ASGI framework (GZipMiddleware, Response types)
- uvicorn[standard] >=0.27.0 - ASGI server (`src/indiestack/__main__.py`)

**MCP Server:**
- mcp[cli] >=1.0.0 - Model Context Protocol SDK (`src/indiestack/mcp_server.py`)
  - FastMCP server with stdio transport
  - Published to PyPI as `indiestack` package (v1.3.1)

**Testing:**
- No test framework configured (no pytest, unittest, or similar in dependencies)
- `smoke_test.py` at project root - 40+ endpoint smoke tests using stdlib `urllib`

**Build/Dev:**
- hatchling - Build backend (configured in `pyproject.toml`)
- Docker multi-stage build (`Dockerfile`)

## Key Dependencies

**Critical (server extras in `pyproject.toml [project.optional-dependencies.server]`):**
- `fastapi` >=0.109.0 - Web framework
- `uvicorn[standard]` >=0.27.0 - ASGI server
- `aiosqlite` >=0.19.0 - Async SQLite driver (WAL mode)
- `stripe` >=8.0.0 - Payment processing (Checkout, Connect, Webhooks)
- `httpx` >=0.25.0 - Async HTTP client (GitHub API, GEO scraping, IndexNow)
- `python-multipart` >=0.0.6 - Form data parsing for FastAPI

**MCP client dependencies (main `[project.dependencies]`):**
- `mcp[cli]` >=1.0.0 - MCP protocol SDK
- `httpx` >=0.25.0 - API calls to indiestack.ai

**Stdlib-only (no extra dependencies):**
- `smtplib` / `email` - Email sending (`src/indiestack/email.py`)
- `hashlib` / `secrets` - Password hashing with PBKDF2-HMAC-SHA256 (`src/indiestack/auth.py`)
- `logging` - Application logging throughout
- `asyncio` - Background tasks (session cleanup, ego pings, weekly digest)
- `json` / `re` / `html` - Data processing and HTML escaping

## Configuration

**Environment Variables (all via `os.environ.get()`):**

| Variable | File | Purpose |
|---|---|---|
| `PORT` | `__main__.py` | Server port (default: 8080) |
| `INDIESTACK_DB_PATH` | `db.py` | SQLite database path (default: `/data/indiestack.db`) |
| `INDIESTACK_ADMIN_PASSWORD` | `auth.py` | Admin panel password (required in prod) |
| `INDIESTACK_SESSION_SECRET` | `auth.py` | Session token signing secret |
| `INDIESTACK_UPVOTE_SALT` | `db.py` | IP hash salt for anonymous upvotes |
| `INDIESTACK_DEBUG` | `__main__.py` | Enable uvicorn reload mode |
| `BASE_URL` | `config.py` | Canonical URL (default: `https://indiestack.ai`) |
| `STRIPE_SECRET_KEY` | `main.py`, `stacks.py` | Stripe API key |
| `STRIPE_BOOST_PRICE_ID` | `main.py` | Stripe price ID for 29 GBP Boost |
| `STRIPE_DEMAND_PRO_PRICE_ID` | `main.py` | Stripe price ID for Demand Pro subscription |
| `SMTP_HOST` | `email.py` | SMTP server hostname |
| `SMTP_PORT` | `email.py` | SMTP port (default: 587) |
| `SMTP_USER` | `email.py` | SMTP username |
| `SMTP_PASSWORD` | `email.py` | SMTP password |
| `SMTP_FROM` | `email.py` | Sender email address |
| `GITHUB_CLIENT_ID` | `routes/account.py` | GitHub OAuth app client ID |
| `GITHUB_CLIENT_SECRET` | `routes/account.py` | GitHub OAuth app client secret |
| `GITHUB_TOKEN` | `db.py`, `enricher.py`, `indexer.py` | GitHub API personal access token |
| `INDEXNOW_KEY` | `main.py` | IndexNow API key for search engine notification |
| `ADMIN_SECRET` | `main.py` | Admin API secret for programmatic access |
| `FLY_APP_NAME` | `auth.py` | Auto-set by Fly.io (used for production detection) |

**Build Configuration:**
- `Dockerfile` - Multi-stage Python 3.11-slim build
- `fly.toml` - Fly.io deployment config (region: sjc, 512MB RAM, shared CPU)
- `pyproject.toml` - Package metadata, build config, dependency management
- `smithery.yaml` - Smithery MCP marketplace registration
- `server.json` - MCP server schema definition (v0.4.0)

## Platform Requirements

**Development:**
- Python 3.11+ (3.10 minimum per `pyproject.toml`)
- No Node.js, no frontend build step
- SQLite3 (bundled with Python)
- Install: `pip install ".[server]"` for full server deps
- Run: `python -m indiestack` (starts uvicorn on port 8080)

**Production:**
- Fly.io single machine deployment
- Docker container (python:3.11-slim)
- Persistent volume mounted at `/data` for SQLite database
- 512MB RAM, 1 shared vCPU
- Health check at `/health` (30s interval)
- Auto-stop/start machines enabled (min 1 running)
- HTTPS forced via Fly.io proxy

## Codebase Size

| File | Lines | Purpose |
|---|---|---|
| `src/indiestack/db.py` | 5,097 | Schema, migrations, all queries |
| `src/indiestack/main.py` | 3,414 | App setup, middleware, API routes |
| `src/indiestack/routes/dashboard.py` | 2,184 | Maker dashboard |
| `src/indiestack/routes/content.py` | 1,962 | Static pages (about, FAQ, terms, blog) |
| `src/indiestack/routes/components.py` | 1,766 | Shared HTML components, CSS |
| `src/indiestack/mcp_server.py` | 1,597 | MCP protocol server |
| `src/indiestack/routes/admin.py` | 1,522 | Admin panel |
| `src/indiestack/email.py` | 1,321 | Email templates and SMTP sending |
| **Total** | **~31,500** | All Python source |

---

*Stack analysis: 2026-03-13*

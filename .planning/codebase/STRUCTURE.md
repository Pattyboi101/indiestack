# Codebase Structure

**Analysis Date:** 2026-03-13

## Directory Layout

```
indiestack/
├── src/
│   └── indiestack/            # Main application package
│       ├── __init__.py        # Empty
│       ├── __main__.py        # Uvicorn entry point
│       ├── main.py            # FastAPI app, middleware, inline API routes (3,414 lines)
│       ├── db.py              # Schema, queries, seed data, constants (5,097 lines)
│       ├── auth.py            # Password hashing, session management (84 lines)
│       ├── config.py          # BASE_URL config (3 lines)
│       ├── email.py           # SMTP email + HTML templates (1,321 lines)
│       ├── mcp_server.py      # MCP server for AI agents (1,597 lines)
│       ├── enricher.py        # Tool metadata enrichment (368 lines)
│       ├── indexer.py         # GitHub tool indexing (424 lines)
│       ├── pair_generator.py  # Tool compatibility pair generation (214 lines)
│       └── routes/            # Feature-based route modules
│           ├── __init__.py    # Empty
│           ├── components.py  # Design system, shared HTML components (1,766 lines)
│           ├── landing.py     # Homepage (743 lines)
│           ├── browse.py      # Category pages
│           ├── tool.py        # Tool detail page (872 lines)
│           ├── search.py      # Search page
│           ├── submit.py      # Tool submission form (525 lines)
│           ├── account.py     # Login, signup, OAuth, password reset (582 lines)
│           ├── dashboard.py   # Maker dashboard (2,184 lines)
│           ├── admin.py       # Admin command center (1,522 lines)
│           ├── admin_analytics.py  # Admin charts/stats rendering (592 lines)
│           ├── admin_helpers.py    # Admin UI helpers (316 lines)
│           ├── admin_outreach.py   # Admin email/outreach tools (1,108 lines)
│           ├── maker.py       # Public maker profiles (284 lines)
│           ├── alternatives.py    # "Alternatives to X" SEO pages (640 lines)
│           ├── compare.py     # Side-by-side comparisons
│           ├── stacks.py      # Curated tool bundles (734 lines)
│           ├── collections.py # Legacy redirects to stacks
│           ├── explore.py     # Faceted browse page (268 lines)
│           ├── tags.py        # Tag pages for SEO
│           ├── content.py     # Static pages: about, terms, privacy, FAQ, blog (1,962 lines)
│           ├── gaps.py        # Demand bounty board (648 lines)
│           ├── geo.py         # GEO lead magnet generator (799 lines)
│           ├── new.py         # Redirect to /explore?sort=newest
│           ├── updates.py     # Maker update feed
│           ├── embed.py       # Embeddable comparison widgets (399 lines)
│           ├── plugins.py     # AI plugins discovery page
│           ├── pulse.py       # AI Pulse / demand signals
│           ├── use_cases.py   # Use case comparison pages (325 lines)
│           ├── calculator.py  # SaaS cost calculator
│           ├── built_this.py  # Quick "built this" submission
│           ├── launch.py      # Launch day page
│           ├── launch_with_me.py  # Co-marketing pages
│           ├── stripe_guide.py    # Stripe setup guide
│           ├── what_is.py     # Explainer page (328 lines)
│           ├── why_list.py    # "Why list" page for makers
│           ├── api_docs.py    # REST API documentation page (261 lines)
│           └── category_icons.py  # Category icon SVGs (224 lines)
├── scripts/                   # Operational scripts (not part of deployed app)
│   ├── hunters/               # GitHub tool scraping scripts
│   │   ├── github_tool_hunter.py - github_tool_hunter6.py
│   │   ├── bulk_insert_tools.py
│   │   └── insert_github_tools.py
│   ├── seeds/                 # Database seeding scripts
│   │   ├── seed_tools.py
│   │   ├── seed_comprehensive.py
│   │   └── seed_*.py (10 files)
│   ├── fixes/                 # One-off DB fix scripts
│   │   ├── fix_stripe.py
│   │   ├── fix_fake_makers.py
│   │   └── fix_*.py / check_*.py / cleanup_*.py
│   ├── check_tool_freshness.py
│   ├── launch_day.py
│   └── reddit_reply.py
├── migrations/                # SQL migration files
│   └── add_submitter_email.sql
├── marketing/                 # Blog post drafts (Markdown)
│   └── blog-*.md (5 files)
├── docs/                      # Planning docs and questionnaires
│   ├── founders-questionnaire.md
│   └── plans/
├── logo/                      # Logo assets (copied into Docker image)
├── drafts/                    # Draft content
├── smoke_test.py              # Endpoint smoke tests (37+ checks)
├── pyproject.toml             # Package config (hatchling build, dependencies)
├── Dockerfile                 # Multi-stage Python 3.11-slim build
├── fly.toml                   # Fly.io deployment config
├── smithery.yaml              # MCP server registry config
├── server.json                # MCP server metadata
├── CLAUDE.md                  # AI assistant context (design system, constraints)
├── README.md                  # Project README
├── README_PYPI.md             # PyPI package README
├── ARCHITECTURE.md            # High-level architecture doc
├── ROADMAP.md                 # Feature roadmap
├── VISION.md                  # Product vision
└── googleb0483aef4f89d039.html  # Google Search Console verification
```

## Directory Purposes

**`src/indiestack/`:**
- Purpose: The entire web application and MCP server
- Contains: Python modules -- no subdirectories besides `routes/`
- Key files: `main.py` (app setup + API routes), `db.py` (everything database), `mcp_server.py` (MCP distribution)

**`src/indiestack/routes/`:**
- Purpose: Feature-based route modules, each with its own `APIRouter`
- Contains: One `.py` file per feature area, plus `components.py` for shared HTML
- Key files: `components.py` (design system), `dashboard.py` (maker features), `admin.py` (admin panel)

**`scripts/`:**
- Purpose: Operational tooling -- NOT part of the deployed application
- Contains: Database seeding, GitHub scraping, one-off fixes, Reddit automation
- Key files: `scripts/hunters/` for GitHub tool discovery, `scripts/seeds/` for DB population

**`migrations/`:**
- Purpose: SQL schema changes (rarely used -- most schema is in `db.py` SCHEMA string)
- Contains: Single SQL file

**`marketing/`:**
- Purpose: Blog post drafts in Markdown
- Contains: 5 blog post files

## Key File Locations

**Entry Points:**
- `src/indiestack/__main__.py`: Uvicorn startup -- `python -m indiestack`
- `src/indiestack/main.py`: FastAPI app object at line 454
- `src/indiestack/mcp_server.py`: MCP server entry via `main()` function

**Configuration:**
- `src/indiestack/config.py`: BASE_URL only
- `fly.toml`: Fly.io deployment (region, VM size, health check, volume mount)
- `Dockerfile`: Docker build (Python 3.11-slim, multi-stage)
- `pyproject.toml`: Package metadata, dependencies, build config
- `CLAUDE.md`: Design system tokens, brand guidelines, constraints for AI assistants

**Core Logic:**
- `src/indiestack/db.py`: ALL database schema + queries (single 5,097-line file)
- `src/indiestack/main.py`: Middleware stack + inline API endpoints (lines 960-3376)
- `src/indiestack/auth.py`: Password hashing + session management
- `src/indiestack/email.py`: SMTP sending + all email templates

**HTML/UI:**
- `src/indiestack/routes/components.py`: Design tokens (CSS variables), `page_shell()`, `tool_card()`, `nav_html()`, `footer_html()`, all shared UI components
- `src/indiestack/routes/category_icons.py`: SVG icon definitions per category

**Testing:**
- `smoke_test.py`: HTTP endpoint smoke tests (root-level, 37+ endpoint checks)

**AI Agent Integration:**
- `src/indiestack/mcp_server.py`: Full MCP server (13 tools, 4 prompts, 3 resources)
- `smithery.yaml`: MCP registry listing config
- `server.json`: MCP server metadata for discovery

## Naming Conventions

**Files:**
- `snake_case.py`: All Python files use snake_case
- Route modules named by feature: `tool.py`, `search.py`, `dashboard.py`, `alternatives.py`
- Admin sub-modules prefixed: `admin.py`, `admin_analytics.py`, `admin_helpers.py`, `admin_outreach.py`

**Directories:**
- Flat structure: Only one level of nesting under `src/indiestack/`
- `routes/` is the only subdirectory in the app package

**Functions:**
- Route handlers: `async def landing(request: Request)`, `async def tool_detail(request: Request, slug: str)`
- DB query functions: `async def get_tool_by_slug(db, slug)`, `async def search_tools_advanced(db, ...)`
- Component functions: `def page_shell(title, body, ...)`, `def tool_card(tool, compact=False)`
- Helper prefixes: `_` for private/internal (e.g., `_check_rate_limit`, `_landing_cache`)

**Variables:**
- Constants: `UPPERCASE` (e.g., `SCHEMA`, `SEED_CATEGORIES`, `MARKETPLACE_ENABLED`, `PER_PAGE`)
- Module-level caches: `_lowercase_with_underscores` (e.g., `_sitemap_cache`, `_rate_limits`)
- CSS variables: `--kebab-case` (e.g., `--terracotta`, `--font-display`, `--shadow-lg`)

**URLs/Slugs:**
- Tool slugs: `kebab-case` (e.g., `simple-analytics`, `pocketbase`)
- Category slugs: `kebab-case` (e.g., `analytics-metrics`, `ai-dev-tools`)
- Route paths: `/tool/{slug}`, `/category/{slug}`, `/maker/{slug}`, `/api/tools/search`

## Where to Add New Code

**New Page/Feature:**
1. Create `src/indiestack/routes/{feature_name}.py`
2. Define `router = APIRouter()`
3. Add route handlers using `@router.get()` / `@router.post()`
4. Import shared components: `from indiestack.routes.components import page_shell, tool_card`
5. Import DB functions: `from indiestack.db import get_tool_by_slug, ...`
6. Register in `src/indiestack/main.py`: `from indiestack.routes import {feature_name}` then `app.include_router({feature_name}.router)`

**New API Endpoint:**
- JSON API endpoints are defined inline in `src/indiestack/main.py` (lines 960-3376), not in route modules
- Add new `@app.get("/api/...")` or `@app.post("/api/...")` handlers directly in `main.py`
- Return `JSONResponse({...})`

**New Database Table or Query:**
- Add table DDL to `SCHEMA` string in `src/indiestack/db.py`
- Add indexes after the schema block
- Add async query functions in `db.py` (follow pattern: `async def get_X_by_Y(db, param) -> dict | None:`)
- The `init_db()` function runs all DDL on startup -- new tables are created automatically

**New UI Component:**
- Add to `src/indiestack/routes/components.py`
- Follow pattern: `def my_component(data: dict) -> str:` returning HTML string
- Use `escape()` from `html` module for all user-provided text
- Reference CSS variables from `design_tokens()` (e.g., `var(--terracotta)`, `var(--font-display)`)

**New Email Template:**
- Add to `src/indiestack/email.py`
- Follow pattern: `def my_email_html(*, param1: str, param2: str) -> str:` returning HTML string
- Use `escape()` for user data
- Call via `await send_email(to, subject, my_email_html(...))`

**New Background Task:**
- Define `async def _my_task():` in `src/indiestack/main.py` (before the `lifespan()` function)
- Pattern: `while True: await asyncio.sleep(interval); try: ... except: _logger.exception(...)`
- Register in `lifespan()`: `my_task = asyncio.create_task(_my_task())` and cancel in cleanup

**New Smoke Test:**
- Add tuple to `TESTS` list in `smoke_test.py`: `("GET", "/my-path", 200, "Description")`

## Special Directories

**`/data/` (production only):**
- Purpose: Persistent SQLite database storage
- Generated: Yes (by the application)
- Committed: No -- Fly.io volume mount at `/data`
- Contains: `indiestack.db` (the entire database)

**`logo/`:**
- Purpose: Logo image assets
- Generated: No
- Committed: Yes -- copied into Docker image

**`founder-photos/` (referenced but not in repo):**
- Purpose: Founder profile photos
- Generated: No
- Committed: Not in the repo -- likely on production server only

**`.planning/`:**
- Purpose: Planning and analysis documents
- Generated: Yes (by tooling)
- Committed: Varies

**`scripts/`:**
- Purpose: Operational scripts for data management
- Generated: No
- Committed: Yes, but NOT deployed (not in Docker image)

---

*Structure analysis: 2026-03-13*

# Coding Conventions

**Analysis Date:** 2026-03-13

## Naming Patterns

**Files:**
- Snake_case for all Python files: `smoke_test.py`, `mcp_server.py`, `admin_helpers.py`
- Route files named after their domain feature: `tool.py`, `search.py`, `dashboard.py`, `alternatives.py`
- Helper/utility modules use descriptive names: `components.py`, `category_icons.py`, `admin_analytics.py`

**Functions:**
- Snake_case for all functions: `get_tool_by_slug()`, `create_user_session()`, `format_price()`
- Prefix `_` for private/internal functions: `_check_rate_limit()`, `_alert_telegram()`, `_is_valid_gap()`
- Database query functions follow `get_`, `create_`, `update_`, `delete_`, `toggle_` prefixes
- HTML-generating functions use `_html` suffix: `login_form_html()`, `submit_success_page()`, `tool_card()`
- Boolean checks use `is_`/`check_` prefix: `check_admin_session()`, `is_wishlisted()`

**Variables:**
- Snake_case throughout: `tool_count`, `maker_id`, `total_upvotes`
- Module-level constants use UPPER_SNAKE: `DB_PATH`, `SEED_CATEGORIES`, `PER_PAGE`, `ADMIN_PASSWORD`
- Private module-level state prefixed with `_`: `_rate_limits`, `_landing_cache`, `_logo_bytes`
- CSS custom properties use `--kebab-case`: `--terracotta`, `--font-display`, `--shadow-lg`

**Types:**
- No type annotations on most functions. Some use basic annotations: `Optional`, `dict`, `str`, `int`, `bool`
- `db.py` uses `Optional` from typing; route handlers mostly omit return types
- No Pydantic models, dataclasses, or TypedDict usage -- plain dicts throughout

**Routes:**
- URL paths use kebab-case: `/tool/{slug}`, `/api/tools/search`, `/launch-with-me`
- API endpoints under `/api/` prefix: `/api/tools/search`, `/api/upvote`, `/api/badge/{slug}.svg`
- Page routes at root level: `/explore`, `/dashboard`, `/submit`

## Code Style

**Formatting:**
- No formatter configured (no black, ruff, or autopep8 config files)
- Indentation: 4 spaces (Python standard)
- Line length: no enforced limit, many lines exceed 120 characters (especially HTML strings and SQL queries)
- String quotes: double quotes for HTML/CSS content, mixed single/double in Python logic

**Linting:**
- No linter configured (no .flake8, .pylintrc, ruff.toml, or eslint config)
- No pre-commit hooks or CI checks

**HTML Templating:**
- All HTML is Python f-strings -- no template engine (no Jinja2, no React)
- Use `escape()` from `html` module for all user-supplied content: `escape(str(tool['name']))`
- CSS lives in `components.py` in the `design_tokens()` function as inline `<style>` blocks
- No external stylesheets -- everything is inline CSS or CSS custom properties

## Import Organization

**Order:**
1. Standard library imports: `import os`, `import json`, `import hashlib`, `from datetime import date`
2. Third-party imports: `from fastapi import APIRouter, Request`, `import aiosqlite`, `import httpx`
3. Internal imports: `from indiestack.config import BASE_URL`, `from indiestack.db import ...`, `from indiestack.routes.components import ...`

**Path Aliases:**
- No path aliases. All imports use full dotted paths: `from indiestack.routes.components import page_shell`
- Some lazy imports inside functions: `import aiosqlite` inside background tasks, `from indiestack.email import ...` inside handlers

**Import Style:**
- Named imports preferred over module imports: `from indiestack.db import get_tool_by_slug, get_related_tools`
- Long import lists are common (10+ names from `indiestack.db`)
- No `import *` usage

## Error Handling

**Patterns:**
- Bare `except Exception: pass` is the dominant pattern for non-critical operations (pageview tracking, notification sending, API key logging)
- Critical paths use `_logger.exception()` with specific messages: `_logger.exception("Background task failed: session cleanup")`
- Database errors in background tasks trigger Telegram alerts via `_alert_telegram()`
- HTTP errors return `JSONResponse` with `{"error": "message"}` structure
- 404 pages return styled HTML via `page_shell()` with `status_code=404`
- Rate limiting returns `JSONResponse({"error": "Too many requests"}, status_code=429)`
- Global exception handler catches unhandled errors and returns `{"error": "Internal server error"}` with 500

**Error Response Formats:**
```python
# API errors -- JSON
return JSONResponse({"error": "Cross-origin request blocked"}, status_code=403)

# Page not found -- styled HTML
return HTMLResponse(page_shell("Not Found", body, user=user), status_code=404)

# Auth redirects -- 303 redirect
return RedirectResponse(url="/login", status_code=303)
```

**Auth Guard Pattern:**
```python
def require_login(user):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return None

# Usage in route handler:
redirect = require_login(user)
if redirect:
    return redirect
```

## Logging

**Framework:** Python stdlib `logging`

**Patterns:**
- Module-level logger: `_logger = logging.getLogger("indiestack")` in `main.py`
- Per-module loggers: `logger = logging.getLogger(__name__)` in route files
- Some background tasks create local loggers redundantly: `logger = logging.getLogger("indiestack")` inside async functions
- Log levels used: `info` for success events, `exception` for failures (includes traceback), `error` for Stripe issues, `warning` for webhook verification failures
- Email module uses `logging.getLogger("indiestack.email")`

**When to log:**
- Background task successes: `logger.info(f"Auto TOTW: {tool['name']} ({clicks} AI mentions this week)")`
- Background task failures: `_logger.exception("Background task failed: badge nudge")`
- Unhandled exceptions: `_logger.exception("Unhandled exception on %s %s", request.method, request.url.path)`
- Do NOT log routine page requests (middleware handles pageview tracking in DB instead)

## Comments

**When to Comment:**
- Section headers use styled comment blocks: `# -- Section Name -----` (em-dash style dividers)
- Module-level docstrings on every file: `"""Tool detail page."""`, `"""Database schema, migrations, seed data, and all query functions."""`
- Inline comments for non-obvious logic: `# Cleanup every 100 requests`, `# 4 = Friday`
- No JSDoc/TSDoc equivalent -- docstrings are brief or absent on most functions

**Section Divider Style:**
```python
# -- Admin Auth (unchanged) ---
# -- User Password Hashing ---
# -- Schema ---
# -- Seed categories ---
```

## Function Design

**Size:**
- Route handlers are typically 30-100 lines, mixing DB queries, HTML generation, and response building
- HTML-generating functions can be very long (100+ lines of f-string HTML)
- Database query functions in `db.py` are typically 5-20 lines each

**Parameters:**
- Route handlers take `request: Request` and optional `Form(...)` parameters
- HTML builders take plain dicts and keyword arguments: `tool_card(tool: dict, compact: bool = False)`
- Database functions take `db` connection as first parameter: `get_tool_by_slug(db, slug)`

**Return Values:**
- Route handlers return `HTMLResponse`, `JSONResponse`, `RedirectResponse`, or `PlainTextResponse`
- HTML builders return `str` (raw HTML)
- Database functions return `dict`, `list[dict]`, `tuple`, or `None`

## Module Design

**Exports:**
- No `__all__` definitions anywhere
- Each route module exports a `router = APIRouter()` instance
- `components.py` exports individual functions (no class hierarchy)

**Barrel Files:**
- `src/indiestack/routes/__init__.py` is empty (1 line)
- `src/indiestack/__init__.py` is empty
- Route modules are imported individually in `main.py`

## Request/Response Pattern

**Standard route handler structure:**
```python
@router.get("/path", response_class=HTMLResponse)
async def handler_name(request: Request):
    db = request.state.db          # DB connection from middleware
    user = request.state.user      # User from middleware (dict or None)

    # Query data
    data = await get_some_data(db, param)

    # Handle not found
    if not data:
        body = """<div>Not Found HTML</div>"""
        return HTMLResponse(page_shell("Not Found", body, user=user), status_code=404)

    # Build HTML body
    body = f"""
    <div class="container">
        <h1>{escape(data['name'])}</h1>
    </div>
    """

    return HTMLResponse(page_shell("Page Title", body, user=user))
```

**POST handler structure:**
```python
@router.post("/path")
async def handle_post(request: Request, field: str = Form(...)):
    db = request.state.db
    user = request.state.user

    # Validate
    if not field.strip():
        return HTMLResponse(page_shell("Error", error_html, user=user))

    # Mutate
    await create_something(db, field)
    await db.commit()

    # Redirect (POST-redirect-GET)
    return RedirectResponse(url="/success-path", status_code=303)
```

## HTML Generation Pattern

**All HTML is Python f-strings. Follow this pattern for new pages:**

```python
from html import escape
from indiestack.routes.components import page_shell, tool_card

# Always escape user content
name = escape(str(data['name']))

# Use design tokens (CSS variables) not hardcoded colors
body = f"""
<div class="container" style="padding:48px 24px;">
    <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);color:var(--ink);">
        {name}
    </h1>
    <p style="color:var(--ink-muted);font-size:15px;">{escape(str(data['tagline']))}</p>
</div>
"""

return HTMLResponse(page_shell("Page Title", body, user=user))
```

**Key components to reuse from `src/indiestack/routes/components.py`:**
- `page_shell(title, body, *, description="", user=None)` -- wraps body in full HTML document with nav, footer, design tokens
- `tool_card(tool: dict, compact: bool = False)` -- renders a tool card
- `nav_html(user=None)` -- navigation bar
- `footer_html()` -- site footer
- `pagination_html(page, total_pages, base_url)` -- pagination controls
- `design_tokens()` -- CSS custom properties and base styles

## Database Access Pattern

**Connection lifecycle:**
- Middleware opens connection per request: `request.state.db = await db.get_db()`
- Middleware closes connection in `finally` block: `await request.state.db.close()`
- Background tasks open their own connections: `async with aiosqlite.connect(db.DB_PATH) as conn:`

**Query pattern:**
```python
# Read queries -- use dedicated functions from db.py
tool = await get_tool_by_slug(db, slug)

# Write operations -- always commit after mutation
await create_tool(db, **params)
await db.commit()

# Raw queries when needed (in main.py inline routes)
cursor = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")
row = await cursor.fetchone()
count = row['cnt']
```

**Row factory:** All connections use `_dict_factory` -- rows are plain dicts, access fields by name: `row['name']`, `row['id']`.

---

*Convention analysis: 2026-03-13*

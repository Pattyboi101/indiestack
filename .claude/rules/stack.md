# IndieStack — Stack & Patterns

## Core Stack
- Python 3 / FastAPI / SQLite (WAL mode) / Fly.io
- Use `python3` not `python` on this system

## Auth
- Always use `request.state.user` (populated by middleware via sessions table). Never query users table by `session_token` — that column doesn't exist.
- Use `d = request.state.db` to avoid shadowing the `db` module import.

## Templating
- Route files return `HTMLResponse` with Python f-string templates. No Jinja2, React, Vue, or templating engines.
- Shared components in `src/indiestack/routes/components.py`: `page_shell`, `tool_card`, `upvote_js`, `stack_upvote_js`, `category_icon`
- CSS variables defined in components.py `:root` block — never hardcode hex colors
- Touch targets >= 44px for mobile
- Sanitize user data with `html.escape()` before injecting into f-strings

## Adding Routes
- Create file in `src/indiestack/routes/`, add router import in `main.py`

## Key Non-Route Files
`mcp_server.py`, `email.py` (Gmail SMTP), `payments.py`, `auth.py`

## Key Route Files
landing, explore, tool, search, admin, admin_analytics, admin_outreach, dashboard, stacks, gaps, submit, pricing, compare, new, updates, collections, plugins, pulse, what_is, account, verify, calculator, content, built_this, embed, use_cases, gaps, maker, alternatives, developer

## Fly.io
- `min_machines_running = 1`, health check at `/health`
- GZip + security headers middleware

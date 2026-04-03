# IndieStack Agent Instructions

The discovery layer between AI coding agents and 8,000+ developer tools.
Python 3 / FastAPI / SQLite / Fly.io.

## Project Structure
- Routes: `src/indiestack/routes/*.py` (f-string HTML templates)
- Shared components: `src/indiestack/routes/components.py`
- Database: `src/indiestack/db.py` (SQLite, WAL mode, aiosqlite)
- MCP server: `src/indiestack/mcp_server.py` (published to PyPI as `indiestack`)
- Auth: `src/indiestack/auth.py` (GitHub OAuth, sessions)
- Scripts: `scripts/` (ingestion, recategorisation, mining)

## Key Commands
- Smoke test: `python3 smoke_test.py`
- Deploy: `cd ~/indiestack && ~/.fly/bin/flyctl deploy --local-only`
- Local dev: `python3 -m indiestack`

## Rules
- Use `python3` not `python`
- Use `request.state.user` and `d = request.state.db` (avoid shadowing db module)
- HTML is f-string templates with CSS variables from components.py
- Touch targets >= 44px, sanitize with html.escape()
- Stage specific files (never `git add -A`)
- Check `.claude/rules/gotchas.md` for past mistakes before editing

## Current State (Apr 2026)
- 8,197 approved tools across 40 categories
- Multi-category system via tool_categories junction table
- MCP server v1.13.0 on PyPI, 10,000+ installs
- 60 users, Maker Pro at $49/mo (Stripe integration live)
- Search quality: 10/10 test queries passing
- Orchestra: CEO (Opus) + Manager (Sonnet) + 5 dept agents in tmux
- See memory files in `~/.claude/projects/-home-patty-indiestack/memory/`

# IndieStack

The discovery layer between AI coding agents and 6,500+ developer tools.
Python 3 / FastAPI / SQLite / Fly.io. Two founders (Patrick + Ed).

## How This Project Works

- Routes in `src/indiestack/routes/` return HTMLResponse with Python f-string templates
- Shared components in `src/indiestack/routes/components.py` (page_shell, tool_card, upvote_js, category_icon)
- Database logic in `src/indiestack/db.py` — SQLite with aiosqlite, WAL mode
- MCP server in `src/indiestack/mcp_server.py` — published on PyPI as `indiestack`
- Auth in `src/indiestack/auth.py` — GitHub OAuth, sessions
- Payments in `src/indiestack/payments.py` — Stripe subscriptions
- Deploy to Fly.io. Always smoke test first. See rules/deploy.md.

## Key Commands

- `/deploy` — smoke test + deploy to Fly.io
- `/publish-mcp` — bump version + publish MCP server to PyPI
- `/status` — health check dashboard
- `/backup` — backup production database
- `/hub` — query the command hub (tasks, activity, decisions)
- `/orchestrate` — dispatch tasks to the 6-department orchestra
- `/brainstorm` — generate growth/marketing/feature ideas
- `/weekly-stats` — send stats digest to Telegram

## Rules (auto-loaded from .claude/rules/)

Domain knowledge is split into focused rules files that auto-load:

**Always loaded:**
- `vision.md` — product identity, positioning, revenue constraint
- `stack.md` — tech patterns, auth, code style, route creation
- `deploy.md` — deployment procedures, Fly.io
- `gotchas.md` — **past mistakes — CHECK THIS, it grows over time**

**Loaded when editing matching files:**
- `design.md` — design system, tokens, brand (routes + components)
- `database.md` — SQLite patterns, migrations (db.py + scripts)
- `mcp.md` — MCP server architecture, versioning (mcp_server.py + pyproject.toml)
- `stripe.md` — payment logic, webhooks (payments.py + pricing.py)

## Memory

Dynamic state lives in memory files — updated each session:
- `sprint.md` — current work, priorities, blockers
- `decisions.md` — key decisions with rationale (prevents re-litigating)
- `ed.md` — co-founder's current focus

**Update memory when:** decisions are made, sprint status changes, work is completed.
**Update gotchas.md when:** mistakes are discovered or corrections are made.

## Orchestra

6-department agent system in tmux (launch with `orchestra` alias):
- Frontend (Sonnet), Backend (Sonnet), DevOps (Haiku), Content (Sonnet), MCP (Sonnet), Strategy & QA (Opus)
- Agents write results to `/tmp/orchestra-{dept}.txt`
- 3-hourly cron trigger runs autonomous improvements (search quality, data quality, content)

## Ed (Co-founder)

Email: toedgamings@gmail.com. GitHub: rupert61622-blip.
Handles Reddit/social + maker outreach. Check memory/ed.md for his current focus.

## Key Links

- Production: indiestack.ai (indiestack.fly.dev fallback)
- GitHub: Pattyboi101/indiestack (public, sensitive files gitignored)
- PyPI: indiestack (MCP server, current v1.12.0)
- Command Hub: govlink.fly.dev
- Telegram: `bash ~/.claude/telegram.sh "message"`

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
- `/meeting [topic]` — structured meeting with all agents (CEO + 5 depts) via claude-peers; `/meeting close` to finish and write tasks to briefing files
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

## CEO Skill Routing

Automatically classify every task and invoke the right skill. Never ask Patrick which skill to use.

**Categories** — classify every task into one:
1. **BUILD** — new features, components, creative work
2. **FIX** — bugs, test failures, unexpected behaviour
3. **SHIP** — deployment, review, branch completion
4. **DESIGN** — frontend, UI/UX, visual polish
5. **OPERATE** — monitoring, stats, scheduling

After classifying, read `.orchestra/ceo/skills/index.md` for that category, pick the specific skill, invoke via `/skill`. For multi-step work, check `.orchestra/ceo/skills/chains.md`.

## Escalation Assessment

Before starting any task, assess confidence:
```
CONFIDENCE: {"score": 0.XX, "reasoning": "..."}
```

**Below 0.85 → escalate to OATS orchestra.** Above → handle yourself.

Lowers confidence: 3+ file scopes, needs parallel workstreams, previous solo failure, needs security/UX testing.
Raises confidence: single domain, known pattern, under 30 mins, no auth/payment changes.

Hard overrides:
- ALWAYS escalate: explicit user request, or failed twice solo
- NEVER escalate: information retrieval, or user wants in-session handling

Log decisions to `.orchestra/ceo/memory/escalation-log.md` (keep last 20).

## Context Management

- Keep `.orchestra/ceo/state.md` updated with focus, completed items, decisions, next steps
- Don't re-read old tool outputs — work from notes in state.md
- Only use `/compact` as a last resort

## Orchestra

6-department agent system in tmux (launch with `orchestra` alias):
- Frontend (Sonnet), Backend (Sonnet), DevOps (Haiku), Content (Sonnet), MCP (Sonnet), Strategy & QA (Opus)
- S&QA is permanent Devil's Advocate — must CHALLENGE or VETO in ballot rounds
- Tiered meetings: brief (no meeting), ballot (structured single-round), full (max 3 rounds)
- Launch: `python3 .orchestra/orchestrator.py "[task brief]"`
- CEO launcher: `.orchestra/launch-ceo.sh`

## Ed (Co-founder)

Handles Reddit/social + maker outreach. Check memory/ed.md for his current focus.

## Key Links

- Production: indiestack.ai (indiestack.fly.dev fallback)
- GitHub: Pattyboi101/indiestack (public, sensitive files gitignored)
- PyPI: indiestack (MCP server, current v1.12.0)
- Command Hub: govlink.fly.dev
- Telegram: `bash ~/.claude/telegram.sh "message"`

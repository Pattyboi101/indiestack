# Design: Ed's Claude Code Architecture

**Date**: March 15, 2026
**Status**: Approved
**Goal**: Set up Ed (co-founder) with a full Claude Code development environment so both devs can work independently on IndieStack.

---

## Context

- Ed (toedgamings@gmail.com, GitHub: rupert61622-blip) is co-founder
- Previously handled Reddit/social outreach, now moving to full-time coding
- Zero coding experience — less than a month with Claude Code
- Focus areas: frontend polish, new pages, and growth/outreach tooling
- Patrick has 2.5 years of AI experience and a mature Claude Code setup — Ed needs his own

## Approach: Private GitHub Repo (`indiestack-dev-setup`)

A shared private repo containing skills, memory, templates, and the command hub. Both devs clone it. Files are symlinked into `~/.claude/` so `git pull` updates everything. A `bootstrap.md` document tells Ed's Claude how to auto-detect his machine and set everything up.

## Repo Structure

```
Pattyboi101/indiestack-dev-setup (private)
├── README.md
├── bootstrap.md                    # Ed's Claude reads this first
├── shared-skills/
│   ├── status/SKILL.md
│   ├── backup/SKILL.md
│   ├── brainstorm/SKILL.md
│   ├── publish-mcp/SKILL.md
│   ├── deep-research/SKILL.md
│   ├── humanizer/SKILL.md          # SKILL.md only (not the git repo)
│   ├── email-pat/SKILL.md          # NEW — Ed emails Patrick
│   ├── email-ed/SKILL.md           # Moved from Patrick's local
│   └── hub/SKILL.md                # NEW — query command hub
├── shared-memory/
│   ├── indiestack-project.md       # Cleaned & updated (MCP v1.7.0, stripped history)
│   ├── dev-patterns.md             # As-is
│   ├── api-keys.md                 # Light trim
│   ├── feedback-auth-pattern.md    # As-is
│   ├── pro-subscription-architecture.md  # Stripped of personal emails/Stripe IDs
│   ├── github-token-setup.md       # Useful for Ed's setup
│   └── workflow-ideas.md           # Stripped of DONE items
├── templates/
│   ├── personal-claude.md          # Template for ~/CLAUDE.md
│   └── memory-index.md             # Template for MEMORY.md
└── command-hub/
    ├── server.py                   # FastAPI app (~300 lines)
    ├── fly.toml                    # Reuses existing GovLink app
    ├── requirements.txt
    └── Dockerfile
```

## Ed's Personal ~/CLAUDE.md (~35 lines)

Key design decisions:
- Explanatory output style baked in (Ed is learning)
- Push-back behavior: Claude questions ideas for brand fit, scope creep, necessity
- Commands: status, email-pat, brainstorm, what's next, deploy, explain, backup
- No: newsletter, hike, uni, weather, book rec, ai news, weekly-stats
- `email-pat` instead of `email-ed`
- `explain [file/concept]` command for educational deep-dives
- Brand guardian instructions: match design tokens, no generic SaaS vibes

## bootstrap.md (Two-Part Setup)

### Part 1: Ed does manually
1. Clone indiestack + indiestack-dev-setup repos
2. Install flyctl (`curl -L https://fly.io/install.sh | sh`)
3. Accept Fly.io org invite (Patrick sends via `flyctl orgs invite`)
4. Create Telegram bot via BotFather, get bot token + chat ID
5. Start Claude Code session with token/chat ID and point to bootstrap.md

### Part 2: Claude automates
1. Detect OS, username, home directory (`uname`, `whoami`, `$HOME`)
2. Create ~/CLAUDE.md from template
3. Symlink skills: `~/.claude/skills/X` -> `~/indiestack-dev-setup/shared-skills/X`
4. Symlink shared memory files into `~/.claude/projects/` memory directory
5. Create personal memory files (Ed.md, MEMORY.md) — not symlinked
6. Create ~/.claude/telegram.sh with Ed's bot token/chat ID
7. Guide GitHub token setup + add to ~/.bashrc
8. Verify: run /status, send test Telegram, confirm git access
9. First orientation: `explain ~/indiestack/src/indiestack/routes/components.py`

## Sync Strategy

- Shared memory files: symlinked from local `~/.claude/projects/` -> dev-setup repo
- Shared skills: symlinked from `~/.claude/skills/` -> dev-setup repo
- Personal files (Ed.md, Patrick.md, MEMORY.md): local only, not symlinked
- Updates propagate via `git pull` on the dev-setup repo
- Patrick's personal skills (newsletter, weekly-stats) stay in local ~/.claude/skills/

## Command Hub (replaces GovLink entirely)

Existing GovLink Fly app wiped and replaced with shared dev infrastructure.

### Endpoints

**`/cron`** — Scheduled background tasks
- Daily 9am: status ping to both devs' Telegram
- Daily: check for unread cross-dev messages
- Daily: backup staleness check (alert if >48hrs old)
- Weekly Monday: stats digest reminder
- Health check IndieStack (alert if down)

**`/messages`** — Cross-dev messaging
- POST /messages — send message (with Telegram notification)
- GET /messages?for=ed — check inbox
- POST /messages/:id/read — mark read
- Claude-queryable: both devs' Claudes can read/post

**`/tasks`** — Shared task board
- GET /tasks — all tasks, filterable by assignee/status
- POST /tasks — create task
- PATCH /tasks/:id — update status/assignee
- Persists across Claude context compaction
- Both devs' Claudes can read/write

**`/dashboard`** — Browser-accessible web UI
- Site health (proxied from IndieStack /health)
- Task board view
- Message history
- Recent deploys
- Quick stats

**`/webhooks`** — Event receivers
- GitHub push notifications -> Telegram to relevant dev
- Fly.io deploy status -> Telegram alerts

### Tech decisions
- Keep `govlink` app name on Fly (avoids cert/DNS reconfig)
- Auth: `HUB_SECRET` shared env var
- DB: SQLite on existing Fly volume
- Cron: asyncio background tasks (same pattern as IndieStack health refresh)
- Both devs' Telegram bot tokens as env vars (hub pings either dev directly)
- ~300 lines of Python

## Communication Architecture

```
Patrick's Claude                    Ed's Claude
     │                                  │
     ├── /email-ed ──(Fly SMTP)──> Ed's Gmail
     ├── /hub ──────(HTTP)──────> Command Hub
     │                                  │
     │        Command Hub (Fly)         │
     │   ┌──────────────────────┐       │
     │   │ /messages            │<──────┤ /email-pat ──(Fly SMTP)──> Pat's Gmail
     │   │ /tasks               │<──────┤ /hub
     │   │ /cron ──> Telegram   │       │
     │   │ /dashboard           │       │
     │   └──────────────────────┘       │
     │                                  │
Patrick's Telegram              Ed's Telegram
(PattysAssistanBot)             (EdBot — new)
```

## New Skills

**`email-pat`**: Mirror of email-ed. Sends to Patrick's email via Fly SSH SMTP. Shows draft first. Signs off as "Ed".

**`hub`**: Query the command hub — check messages, view/create tasks, see recent activity. Uses HUB_URL and HUB_SECRET from environment.

## Repo CLAUDE.md Technical Patterns

Add ~30 lines to `/home/patty/indiestack/CLAUDE.md` below existing design context:
- Stack (Python 3, FastAPI, SQLite WAL, Fly.io)
- Auth pattern (request.state.user, never query session_token)
- Database conventions (parameterized queries, Row dict access, ALTER TABLE gotcha)
- Deploy workflow (smoke test, flyctl, --buildkit fallback)
- Code style (f-string templates, components.py tokens, no hardcoded hex)

Both devs get this since both clone the IndieStack repo.

## File Cleanup (during implementation)

| File | Action |
|------|--------|
| workflow-ideas.md | Strip all DONE items (~120 lines removed) |
| indiestack-project.md | Update MCP to v1.7.0, strip historical notes, condense marketplace |
| indiestack-details.md | Merge useful parts into project.md, delete file |
| pro-subscription-architecture.md | Strip personal emails and Stripe price IDs |

## Fly.io Org Invite

```bash
~/.fly/bin/flyctl orgs invite toedgamings@gmail.com --org personal
```

## Full Deliverables

| # | Deliverable | Location |
|---|------------|----------|
| 1 | Private `indiestack-dev-setup` repo | GitHub |
| 2 | `bootstrap.md` self-installing guide | In dev-setup repo |
| 3 | Cleaned shared memory files (7 files) | In dev-setup repo |
| 4 | Shared skills (9 skills incl. hub, email-pat) | In dev-setup repo |
| 5 | Ed's personal CLAUDE.md template (~35 lines) | In dev-setup repo |
| 6 | Command Hub (replaces GovLink) | In dev-setup repo, deployed to Fly |
| 7 | Repo CLAUDE.md technical patterns (~30 lines) | IndieStack repo |
| 8 | File cleanup (4 files) | During implementation |
| 9 | Fly.io org invite for Ed | CLI command |
| 10 | IndieStack MCP server in Ed's Claude config | bootstrap.md step |

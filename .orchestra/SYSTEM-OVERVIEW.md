# IndieStack Orchestra & Autonomous Work System — Full Overview

> Written for review by an external LLM. This document describes the complete multi-agent orchestration system used to develop and maintain IndieStack (indiestack.ai), a developer tool discovery platform.

---

## Table of Contents

1. [Architecture Summary](#architecture-summary)
2. [The Orchestra — Multi-Department Agent System](#the-orchestra)
3. [Department Agents](#department-agents)
4. [The Master Orchestrator](#the-master-orchestrator)
5. [Strategy & QA Gate](#strategy--qa-gate)
6. [Communication Layer](#communication-layer)
7. [Memory System](#memory-system)
8. [The Autoloop — Autonomous Improvement Cycle](#the-autoloop)
9. [The Provocation Engine](#the-provocation-engine)
10. [Directives System](#directives-system)
11. [Skills System](#skills-system)
12. [Deployment & Workflows](#deployment--workflows)
13. [Autonomy Roadmap](#autonomy-roadmap)
14. [Current State & Known Issues](#current-state--known-issues)

---

## Architecture Summary

IndieStack uses two parallel autonomous systems built on Claude Code:

```
                      ┌───────────────────────────┐
                      │   Patrick (human founder)  │
                      └────────┬──────────────────-┘
                               │
              ┌────────────────┴────────────────┐
              │                                 │
     ┌────────▼─────────┐            ┌──────────▼──────────┐
     │    Orchestra      │            │     Autoloop         │
     │  (multi-agent,    │            │  (single-agent,      │
     │   on-demand)      │            │   hourly cron)       │
     └────────┬──────────┘            └──────────┬──────────┘
              │                                  │
  ┌───────────┼────────────┐          5 iterations per cycle:
  │     6 departments      │          1. Search quality
  │  + master + S&QA gate  │          2. Data quality
  │  running in tmux       │          3. Competitive scan
  └────────────────────────┘          4. Provocation engine
                                      5. OATS framework
```

**Orchestra**: 6 specialized Claude Code agents running in tmux windows, coordinated by a Master agent via `claude-peers` MCP server. Every task passes through a Strategy & QA gate before execution. Used for complex, multi-department work.

**Autoloop**: A single Claude Code instance running hourly in a tmux session. Executes a fixed 5-iteration improvement cycle autonomously. Used for continuous maintenance and incremental quality improvements.

Both systems are **local-only** — they run on Patrick's Crostini (ChromeOS Linux) machine. A remote cron trigger was tested but disabled because it can't access local tools (flyctl, Telegram, file system).

---

## The Orchestra

### Launch

```bash
# Launch all 6 department agents in tmux (master runs separately)
.orchestra/launch.sh

# Launch specific departments only
.orchestra/launch.sh frontend backend

# Alternative: Python orchestrator for single-task dispatch
python3 .orchestra/orchestrator.py --simple "fix the broken search endpoint"
```

The `launch.sh` script:
1. Creates a tmux session called `orchestra`
2. Opens one tmux window per department
3. Starts a Claude Code instance in each window with `--dangerously-skip-permissions`
4. Waits 8 seconds, then sends each department its init-prompt.md
5. Each agent uses a specified model (Opus for strategy, Sonnet for most, Haiku for DevOps)

### Configuration

```
.orchestra/
├── launch.sh                    # tmux launcher
├── orchestrator.py              # Python-based task dispatcher (alternative to tmux)
├── config.json                  # Budget caps, model assignments
├── README.md                    # Usage docs
├── master/
│   ├── CLAUDE.md                # Master agent rules
│   ├── init-prompt.md           # Master boot prompt
│   └── skills/                  # Master-specific skills (5 files)
├── departments/
│   ├── {dept}/CLAUDE.md         # Department rules (persistent)
│   ├── {dept}/init-prompt.md    # Department boot prompt
│   ├── {dept}/memory.md         # Department accumulated knowledge
│   ├── {dept}/briefing.md       # Per-task context (written by master)
│   └── {dept}/skills/           # Department-specific skills
├── memory/
│   ├── playbook.md              # Shared lessons (all departments read this)
│   └── {dept}.md                # Orchestrator-written department summaries
├── directives/
│   ├── pending/                 # Queued tasks for master to execute
│   └── done/                    # Completed directives
├── logs/                        # Per-run logs (markdown)
├── history/                     # Structured JSON run logs
└── sandbox/                     # Experimental tools and reference docs
```

### Model Assignments

| Department | Model | Rationale |
|------------|-------|-----------|
| Master | Opus | Task decomposition needs strong reasoning |
| Strategy & QA | Opus | Gatekeeper needs to actually think critically |
| Frontend | Sonnet | Execution agent — good enough for HTML/CSS |
| Backend | Sonnet | Execution agent — handles DB/auth/payments |
| DevOps | Haiku | Simple checks (smoke tests, deploys) — cheapest |
| Content/SEO | Sonnet | Copy and meta tags need quality writing |
| MCP/Integration | Sonnet | MCP server work needs code quality |

---

## Department Agents

Each department has a clearly scoped domain, a set of owned files, and explicit "do NOT touch" boundaries.

### Frontend (Sonnet)

- **Owns**: `src/indiestack/routes/*.py`, `src/indiestack/routes/components.py`
- **Does NOT touch**: `db.py`, `auth.py`, `payments.py`, `mcp_server.py`
- **Key rules**: f-string HTML templates only (no Jinja2/React/Vue), CSS variables from `:root` block (never hardcode hex), touch targets >= 44px, `html.escape()` on all user input
- **Skills**: `fstring-html-safety.md`, `synthetic-user.md`
- **Memory tracks**: component patterns, hardcoded color locations, page audit results, dashboard UX branches

### Backend (Sonnet)

- **Owns**: `src/indiestack/db.py`, `auth.py`, `payments.py`, `main.py`, `config.py`, `email.py`, `scripts/`
- **Does NOT touch**: route HTML templates, `mcp_server.py`
- **Key rules**: aiosqlite dict access only (`row["col"]` not `row[0]`), `request.state.user` for auth, `d = request.state.db` to avoid shadowing, parameterized SQL only
- **Skills**: `production-data-patch.md`
- **Memory tracks**: FTS5 architecture, search ranking formula, claim flow, payment functions, production DB state

### DevOps (Haiku)

- **Owns**: `Dockerfile`, `fly.toml`, `smoke_test.py`, `.github/`
- **Does NOT touch**: route files, `db.py`, `mcp_server.py`
- **Key rules**: Always smoke test before deploy, `flyctl deploy --local-only` (fallback `--remote-only`), can't use `cd` in `flyctl ssh console -C`, `scripts/` not in Docker (use inline python)
- **Skills**: `chaos-monkey.md`, `deploy-safely.md`
- **Memory tracks**: deploy workflows, security scan results, MCP registry submission status, smoke test results

### Content/SEO (Sonnet)

- **Owns**: user-facing copy, meta descriptions, JSON-LD schemas, blog content
- **Does NOT touch**: database logic, auth, MCP server, deploy config
- **Key rules**: meta descriptions under 160 chars, valid schema.org JSON-LD, `html.escape()` for dynamic meta content
- **Skills**: `build-in-public.md`, `outreach-copy.md`
- **Memory tracks**: production DB stats, migration path data, blog posts written, outreach plans for Ed, directory submission details
- **Notable files**: ed-outreach-plan.md, ed-leads-*.md, mcp-directory-submissions.md, devto-v112-blog.md, demo-video-script.md

### MCP/Integration (Sonnet)

- **Owns**: `src/indiestack/mcp_server.py`, `pyproject.toml`, `indexer.py`, `enricher.py`
- **Does NOT touch**: route HTML, `db.py`, `auth.py`, deploy config
- **Key rules**: MCP runs from PyPI package (not local source) — presentation changes need PyPI publish, backend API changes take effect on deploy. Version in `pyproject.toml` must match `mcp_server.py`.
- **Dog-Fooding Rule**: When working on MCP tasks, use IndieStack's own MCP server to test searches and note quality issues
- **Skills**: `agent-experience-audit.md`
- **Memory tracks**: registry distribution status, PyPI version, server.json state, dog-fooding results (search quality issues found)

### Strategy & QA (Opus)

- **Owns**: nothing (does not build)
- **Role**: Reviews every plan before any department executes. Can APPROVE, CHALLENGE, or VETO.
- **Review criteria**: Evidence of demand? Revenue path? Opportunity cost? Overconfidence? Strategic coherence? Building toward something or thrashing?
- **Key rules**: "Sounds good" is not approval — must articulate WHY. Default to skepticism. Burden of proof is on the task. Every feature must have a concrete revenue path.
- **Skills**: `review-checklist.md`
- **Memory tracks**: key file locations, architectural patterns, decisions made, current product state

---

## The Master Orchestrator

The Master is the CEO agent — it decomposes tasks, dispatches work, and coordinates results. It runs as Patrick's main Claude Code session (NOT inside the tmux orchestra).

### Task Flow

```
1. Check .orchestra/directives/pending/ for queued tasks
2. Decompose directive into department assignments
3. Send full plan to Strategy & QA for review
4. If S&QA approves → dispatch to departments via claude-peers
5. If S&QA challenges → reformulate and re-submit
6. If S&QA vetoes → log reasoning to playbook, stop
7. Collect results from departments
8. Update playbook with lessons learned
9. Move directive from pending/ to done/
```

### Management Powers

The Master can reshape how departments think:

- **Edit CLAUDE.md** — Change a department's rules, scope, or behavior permanently
- **Create skills** — Write `.md` files in a department's `skills/` directory
- **Edit memory** — Correct or prune a department's `memory.md` if it's learning wrong lessons
- **Update playbook** — Share lessons that all departments should know

### Integrated Tools

The Master has access to several Python scripts:

- `scripts/token_economist.py` — Track department token costs after orchestra sessions
- `scripts/event_reactor.py --watch` — Background watcher for claims, signups, traffic spikes
- `scripts/session_state.py` — Persistent state that survives restarts
- `scripts/results_tracker.py` — Track outreach contacts, check before sending more

### Python Orchestrator (Alternative to tmux)

`orchestrator.py` is a 33KB Python script that can dispatch tasks without tmux:

```bash
# Simple mode — inline output
python3 .orchestra/orchestrator.py --simple "fix the broken search endpoint"

# Dashboard mode — curses TUI
python3 .orchestra/orchestrator.py "fix the broken search endpoint"
```

It:
- Reads `config.json` for model assignments and budget caps
- Spawns Claude Code subprocesses per department
- Injects CLAUDE.md + memory + briefing into each agent's system prompt
- Collects structured `AgentResult` objects (status, files_changed, cost, tokens)
- Logs everything to `history/` as JSON

---

## Strategy & QA Gate

Every task must pass through S&QA before any department executes. This is the most important architectural decision in the system.

### Verdict Types

| Verdict | Effect |
|---------|--------|
| **APPROVE** | Work proceeds as planned |
| **CHALLENGE** | Modify assignments, add conditions, remove scope — resubmit |
| **VETO** | Kill the entire task, reasoning logged to playbook |

### Review Checklist

S&QA evaluates every plan against:

1. **Evidence of demand** — Is anyone asking for this? Check search logs, user feedback.
2. **Revenue path** — Does this move toward $49/mo Maker Pro revenue?
3. **Opportunity cost** — What are we NOT doing while we do this?
4. **Overconfidence** — Are we assuming things we haven't validated?
5. **Strategic coherence** — Does this fit the "discovery layer for AI agents" positioning?
6. **Thrashing detection** — Are we building toward something, or spinning wheels?

### Example Verdicts (from memory)

- **APPROVED**: Distribution prep (with fixes), pricing/MCP audit, migration signals (batch only, max 2)
- **VETOED**: Duplicate code review (waste of tokens)
- **FLAGGED**: Claim email URL bug, restraint recommended after distribution push

---

## Communication Layer

### claude-peers MCP Server

Agents communicate via the `claude-peers` MCP server, which provides:

- `list_peers` — Discover other Claude Code instances (by machine, directory, or repo)
- `send_message` — Send a message to another instance by ID
- `set_summary` — Set a 1-2 sentence description visible to other peers
- `check_messages` — Poll for incoming messages

Each department sets its peer summary on boot (e.g., "IndieStack Frontend — HTML templates, CSS, UX, f-string routes, components").

### Result Delivery

In the tmux-based orchestra, departments also write results to `/tmp/orchestra-{dept}.txt` as a fallback. The Master collects results via both channels.

In the Python orchestrator, results are captured directly from subprocess stdout as structured JSON.

---

## Memory System

Memory is split into multiple layers:

### Playbook (`memory/playbook.md`)

Shared strategic lessons. Read by Master before decomposing tasks, read by S&QA before reviewing. Examples:

- "Distribution > Product polish — with 0 users, every hour polishing is an hour not spent getting found"
- "S&QA catches real bugs — broken claim links would make outreach emails worthless"
- "Don't oversell, don't pivot — 'moat' language was wrong, $299/mo was wrong"

### Department Memory (`departments/{dept}/memory.md`)

Accumulated domain knowledge per department. Injected into their system prompt on each run. Contains:

- Production DB state and schema details
- Past audit results and findings
- Key file locations and line numbers
- Patterns learned from previous tasks

### Orchestrator Memory (`memory/{dept}.md`)

Written by the Master after each orchestrated run. Summarizes what each department accomplished.

### Skills (`departments/{dept}/skills/*.md`)

Reusable patterns the Master can create for departments. Auto-loaded into the department's context. Examples:

- `backend/skills/production-data-patch.md` — How to safely patch production data
- `devops/skills/chaos-monkey.md` — Pre-deploy security scanning
- `frontend/skills/synthetic-user.md` — Post-change UX verification
- `mcp/skills/agent-experience-audit.md` — How to dog-food the MCP server

### User-Level Memory (outside orchestra)

Patrick's personal assistant memory at `~/.claude/projects/-home-patty-indiestack/memory/`:

- `sprint.md` — Current work, priorities, blockers (updated each session)
- `decisions.md` — Strategic decisions with rationale
- `ed.md` — Co-founder's current focus
- Various feedback memories (no API key gating, no Co-Authored-By, clock drift, etc.)

### Gotchas (`~/indiestack/.claude/rules/gotchas.md`)

A growing file of past mistakes. Auto-loaded into every Claude Code session in the repo. Examples:

- "When renaming SQL column aliases in a shared function, grep ALL consumers across the entire codebase"
- "`flyctl ssh console -C` can't use `cd` — use absolute paths"
- "DO NOT gate MCP features behind API keys — it killed adoption before"

---

## The Autoloop — Autonomous Improvement Cycle

### Design

A bash script (`scripts/autonomous_loop.sh`) that runs Claude Code in a loop:

```bash
# Launch
tmux new-session -d -s autoloop 'bash scripts/autonomous_loop.sh'

# Stop
tmux kill-session -t autoloop
```

Every hour, it spawns a fresh Claude Code instance with `--dangerously-skip-permissions` and a long prompt defining 5 iterations:

### Iteration Cycle

| # | Phase | What it does |
|---|-------|-------------|
| 1 | **Search Quality** | Curls the API for 8 test queries, flags bad results, fixes ranking |
| 2 | **Data Quality** | SSHes to production, finds tools with high views but missing data, backfills |
| 3 | **Competitive Scan** | Searches GitHub for trending MCP servers, logs to `.orchestra/logs/` |
| 4 | **Provocation** | Runs `scripts/provoke.py`, evaluates the provocation, acts if criteria pass |
| 5 | **OATS** | Clones the OATS repo, runs its provocation engine, works on the framework |

### Guardrails

The autoloop prompt includes explicit rules:
- Never `git add -A`
- Never `Co-Authored-By Claude` in commits
- Run `smoke_test.py` before pushing
- **DO NOT deploy** (deploy requires human approval)
- OK to exit early if nothing needs doing
- Send a Telegram summary after each cycle

### Current State

The autoloop was running in tmux but the session died overnight. It completed at least one cycle (competitive research + provocation logged at 01:19 AM on April 3). No Telegram output was confirmed received.

---

## The Provocation Engine

`scripts/provoke.py` — A creative stimulus tool that generates random provocations to force novel thinking about IndieStack improvements.

### Five Provocation Types

| Type | Name | Method |
|------|------|--------|
| 1 | **GitHub Trending** | Queries GitHub API for trending dev tools repos. Asks: Is this in our catalog? What can we learn? |
| 2 | **Tool Roleplay** | Picks a random tool from IndieStack's own API. Roleplays as its maker asking: What would make you claim? Pay $49/mo? Share on Twitter? |
| 3 | **Constraint Challenge** | 25 artificial pressure scenarios (e.g., "What if we had to make $100 by Friday?", "A developer uninstalled the MCP server 30 seconds later. Why?") |
| 4 | **Inversion** | 23 destruction/critique questions (e.g., "What's the worst thing about IndieStack?", "Which tools are dead/abandoned?") |
| 5 | **Cross-Domain Steal** | Finds high-star non-dev-tools projects, asks what UX/community ideas to steal |

### Usage

```bash
python3 scripts/provoke.py              # random type
python3 scripts/provoke.py --type 3     # specific type
python3 scripts/provoke.py --dry-run    # preview without HTTP calls
```

### Three-Gate Filter

Before acting on a provocation, the autoloop must verify:
1. Does it help distribution, search quality, or revenue?
2. Is someone else already doing it better?
3. Can it be done in under 30 minutes?

Only act if all three pass. Otherwise, log the thinking to `.orchestra/logs/{date}-thought.md`.

---

## Directives System

The Master orchestrator checks `directives/pending/` for queued tasks. Once completed, directives move to `directives/done/`.

### Structure

```
.orchestra/directives/
├── pending/      # Tasks waiting for master to execute (currently empty)
└── done/         # Completed directives
    ├── awesome-claude-code-prep.md
    └── github-stars-action-plan.md
```

Directives are markdown files with structured action plans — task owners, deadlines, dependencies, and completion status. They serve as the bridge between high-level strategic decisions and the orchestra's task execution.

### Origin

Directives can come from:
- Patrick (human) writing directly to `pending/`
- A "Thought Chain" (autonomous thinking agent running in the cloud — currently disabled)
- The Master itself, generating follow-up directives from completed work

---

## Skills System

Skills are `.md` files that teach departments recurring patterns. They're auto-loaded into the department's context.

### Department Skills

```
departments/
├── backend/skills/
│   └── production-data-patch.md     # Safe production data patching
├── content/skills/
│   ├── build-in-public.md           # Social media post generation
│   └── outreach-copy.md             # Email/outreach templates
├── devops/skills/
│   ├── chaos-monkey.md              # Pre-deploy security scanning
│   └── deploy-safely.md             # Deployment checklist
├── frontend/skills/
│   ├── fstring-html-safety.md       # XSS prevention in f-strings
│   └── synthetic-user.md            # Post-change UX testing
├── mcp/skills/
│   └── agent-experience-audit.md    # Dog-fooding the MCP server
└── strategy/skills/
    └── review-checklist.md          # S&QA evaluation criteria
```

### Master Skills

```
master/skills/
├── ed-integration.md            # Working with co-founder Ed
├── ed-outreach-playbook.md      # Ed's outreach process
├── first-revenue.md             # Revenue generation playbook
├── orchestra-management.md      # How to manage departments
├── outreach-batch.md            # Batch outreach execution
├── rd-architect.md              # R&D architecture decisions
└── token-economist.md           # Token cost tracking
```

### Workflow Skills (`.agents/`)

A separate `.agents/` directory contains Claude Code workflow definitions:

```
.agents/
├── skills/
│   ├── fact-check/SKILL.md      # Fact-check emails against codebase
│   ├── indiestack-frontend/SKILL.md  # Frontend design patterns
│   └── save-tokens/SKILL.md     # Token optimization via IndieStack tools
└── workflows/
    ├── backup.md                # Database backup procedure
    ├── deploy.md                # Full deploy workflow
    ├── hub.md                   # Command Hub query
    ├── publish-mcp.md           # PyPI publish workflow
    └── status.md                # Health check dashboard
```

---

## Deployment & Workflows

### Deploy Flow

1. Run `python3 smoke_test.py` (48 endpoints)
2. Commit all changes (stage specific files, never `git add -A`)
3. `~/.fly/bin/flyctl deploy --local-only` (fallback: `--remote-only`)
4. Verify: `curl -sL -o /dev/null -w "%{http_code}" https://indiestack.fly.dev/`
5. Telegram notification
6. Hub activity log

**Key constraint**: Deploy requires human approval. The autoloop and orchestra agents are explicitly told NOT to deploy.

### MCP Server Publishing (Separate Workflow)

Changes to `mcp_server.py` need a PyPI publish to reach installed clients:

1. Bump version in `pyproject.toml` and `mcp_server.py`
2. Build: `python3 -m build`
3. Publish: `twine upload dist/*`
4. Verify on PyPI

Backend API changes (ranking, filtering) take effect on deploy since the MCP server calls the production API.

---

## Autonomy Roadmap

The system is designed to progress through 5 phases:

| Phase | Status | Description |
|-------|--------|-------------|
| 1. Manual | **Active** | Patrick runs `/orchestrate` with specific tasks. S&QA gates everything. |
| 2. Scheduled | **Complete** | Autoloop runs hourly with crash recovery, structured logging, heartbeat monitoring. Watchdog restarts on failure (5/day cap). |
| 3. Reactive | **Active** | Event reactor runs as Iteration 0 of each autoloop cycle. Monitors: new submissions, health failures, MCP gap anomaly (>15%). Creates directives in pending/ for orchestrator. |
| 4. Proactive | **Not started** | Orchestrator reads its own history to identify patterns, auto-generates preventive tasks. |
| 5. Self-improving | **Not started** | Master writes skills for departments based on patterns. S&QA reviews its own past verdicts. |

---

## Current State & Known Issues

### What's Working
- Site healthy: 48/48 smoke tests passing
- Search quality: 10/10 test queries returning good results
- 8,197 approved tools, 60 users, 10k+ PyPI installs
- Orchestra launch script functional
- Provocation engine operational
- Competitive scanning producing useful intelligence

### Known Issues
- **Autoloop instability**: tmux session dies overnight. No crash logging or auto-restart mechanism.
- **Telegram delivery unconfirmed**: Autoloop is supposed to send Telegram summaries but delivery hasn't been verified.
- **Stale AGENTS.md**: Says 6,500 tools (actual: 8,197). Stale since March.
- **Stale decisions.md**: Still references $299/mo data collection strategy (superseded by $49/mo Maker Pro).
- **Remote cron disabled**: Can't run autonomous work from cloud because local tools (flyctl, Telegram, file system) are required.
- **Orchestra not running**: Currently killed to save tokens. Must be manually launched with `orchestra` alias.
- **orchestrator.py untested recently**: The Python-based orchestrator was used earlier but the tmux-based `launch.sh` has been the primary method.
- **No crash recovery**: Neither the autoloop nor the orchestra auto-restart on failure.
- **Token budget not enforced**: `config.json` has a `budget_cap_usd` setting but enforcement depends on which launch method is used.

### File Inventory

Total files in the orchestra system:
- 7 CLAUDE.md instruction files (1 master + 6 departments)
- 7 init-prompt.md boot prompts
- 7 memory.md department memories
- 6 shared memory files in `memory/`
- 13 skill files across all departments + master
- 2 completed directives
- 1 orchestrator.py (33KB)
- 1 launch.sh
- 1 provoke.py (500 lines)
- ~15 content/outreach planning documents
- Multiple log files

---

## Questions for Review

1. **Is the S&QA gate worth the token cost?** Every task requires an Opus review before any work happens. This catches real bugs but doubles the cost of simple tasks.

2. **Should the autoloop be more resilient?** It currently dies silently. Options: systemd service, supervisor, or at minimum a wrapper that restarts on crash.

3. **Is the memory system too fragmented?** Knowledge lives in: department memory.md, shared playbook.md, user-level sprint.md, rules/gotchas.md, and department skills/. Is there too much overlap or risk of contradiction?

4. **Are the provocation types actually useful?** The engine was built to prevent autonomous stagnation, but it's unclear whether the provocations lead to meaningful improvements vs busywork.

5. **Should departments communicate directly?** Currently all coordination goes through the Master. Peer-to-peer department communication is possible via claude-peers but not actively used.

6. **Is the model assignment optimal?** Haiku for DevOps saves cost but may miss subtle issues. Opus for S&QA is expensive but the gatekeeper role demands it. Are there better tradeoffs?

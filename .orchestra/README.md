# IndieStack Orchestrator

Multi-department agent system for managing IndieStack autonomously.

## Quick Start

```bash
# Simple mode (inline output)
python3 .orchestra/orchestrator.py --simple "fix the broken search endpoint"

# Dashboard mode (curses UI, run in separate terminal)
python3 .orchestra/orchestrator.py "fix the broken search endpoint"
```

## How It Works

```
You / Cron / Schedule
        │
        ▼
   Master Agent (Opus)
   Decomposes task into department assignments
        │
        ▼
   Strategy & QA (Opus)
   Reviews every plan — approve / challenge / veto
        │
        ▼
   Department Agents (Sonnet/Haiku)
   Execute approved work in parallel
        │
        ▼
   Memory + History
   Playbook updated, run logged, departments remember
```

## Departments

| Dept | Model | What it does |
|------|-------|-------------|
| Frontend | sonnet | Routes, components, HTML/CSS, UX |
| Backend | sonnet | db.py, auth, payments, scripts |
| DevOps | haiku | Dockerfile, fly.toml, smoke tests |
| Content/SEO | sonnet | Copy, meta tags, JSON-LD |
| MCP/Integration | sonnet | mcp_server.py, PyPI, APIs |
| Strategy & QA | opus | Reviews everything, can veto |

## Directory Structure

```
.orchestra/
├── orchestrator.py          # The engine
├── config.json              # Budget, models, department scopes
├── README.md                # This file
├── departments/
│   ├── {dept}/CLAUDE.md     # Static instructions per department
│   ├── {dept}/briefing.md   # Dynamic per-task context (written by master)
│   └── {dept}/skills/       # Department-specific skills (master can create)
├── master/
│   └── CLAUDE.md            # Master agent instructions
├── memory/
│   ├── playbook.md          # Master's accumulated lessons
│   └── {dept}.md            # Per-department memory
├── history/                 # Full run logs as JSON
└── logs/                    # Raw agent output per run
```

## Configuration

Edit `.orchestra/config.json`:

```json
{
  "budget_cap_usd": 5.00,          // Stop all agents if exceeded
  "require_approval_for_deploy": true,  // DevOps needs human sign-off
  "require_approval_for_commit": false, // Agents can commit freely
  "models": {
    "master": "opus",     // Task decomposition needs strong reasoning
    "strategy": "opus",   // S&QA needs to actually think
    "frontend": "sonnet", // Execution agents use sonnet
    "backend": "sonnet",
    "devops": "haiku",    // Simple checks, cheap
    "content": "sonnet",
    "mcp": "sonnet"
  }
}
```

## Memory System

**Playbook** (`memory/playbook.md`): Master's lessons learned. Grows after every run.
Read by master before decomposing tasks, read by S&QA before reviewing.

**Department memory** (`memory/{dept}.md`): What each department has done and learned.
Injected into their system prompt on each run.

**History** (`history/`): Full JSON logs of every run — task, decomposition, S&QA review,
results, costs, tokens. Good for auditing what happened and when.

**Skills** (`departments/{dept}/skills/`): Master can create .md skill files that teach
departments recurring patterns. These are auto-loaded into the department's system prompt.

## The S&QA Gate

Every task goes through Strategy & QA before any department executes. S&QA can:

- **Approve**: work proceeds as planned
- **Challenge**: modify assignments, add conditions, remove scope
- **Veto**: kill the entire task with reasoning logged to playbook

S&QA checks for: evidence of demand, revenue path, opportunity cost, overconfidence,
strategic coherence, and whether we're building toward something or thrashing.

---

# Autonomous Operation

## Scheduled Tasks

Use system cron or Claude Code's scheduling to run the orchestrator on a schedule.
Each task type has a different cadence based on how often it's useful.

### Cron Setup

Add to crontab (`crontab -e`):

```cron
# Morning health check — 8am daily
0 8 * * * cd /home/patty/indiestack && python3 .orchestra/orchestrator.py --simple "Run smoke tests, check the site is healthy, verify key pages load correctly. Report any issues." >> .orchestra/logs/cron.log 2>&1

# SEO audit — Monday mornings
0 9 * * 1 cd /home/patty/indiestack && python3 .orchestra/orchestrator.py --simple "Audit 5 high-traffic pages for SEO issues: missing meta descriptions, broken JSON-LD, title tag problems, missing alt text. Only flag real issues, not nice-to-haves." >> .orchestra/logs/cron.log 2>&1

# Code quality sweep — Wednesday afternoons
0 14 * * 3 cd /home/patty/indiestack && python3 .orchestra/orchestrator.py --simple "Review the 3 most recently changed route files for code quality: unused imports, SQL injection risks, missing html.escape on user input, hardcoded values that should be CSS variables. Fix anything clear-cut, flag anything ambiguous." >> .orchestra/logs/cron.log 2>&1

# Stale content check — Friday mornings
0 10 * * 5 cd /home/patty/indiestack && python3 .orchestra/orchestrator.py --simple "Check for stale content: tool counts that don't match reality, outdated copy referencing old features, meta descriptions that no longer match page content. Suggest fixes but don't auto-apply." >> .orchestra/logs/cron.log 2>&1

# Performance check — every 6 hours
0 */6 * * * cd /home/patty/indiestack && python3 .orchestra/orchestrator.py --simple "Quick performance check: run smoke tests, check any endpoints taking over 2 seconds, look for N+1 query patterns in recently changed files. Report only if something is actually wrong." >> .orchestra/logs/cron.log 2>&1
```

### Claude Code Scheduled Triggers

Alternatively, use Claude Code's built-in scheduling from a session:

```
/schedule create --name "morning-health" --cron "0 8 * * *" --prompt "Run the orchestrator health check: python3 .orchestra/orchestrator.py --simple 'health check and smoke test'"

/schedule create --name "weekly-seo" --cron "0 9 * * 1" --prompt "Run SEO audit via orchestrator: python3 .orchestra/orchestrator.py --simple 'audit top 5 pages for SEO issues'"
```

## Autonomous Task Library

These are pre-written tasks the orchestrator handles well autonomously.
Copy-paste or schedule any of these:

### Daily

```bash
# Health check
python3 .orchestra/orchestrator.py --simple "Health check: run smoke tests, verify the site loads, check /health endpoint returns 200. If anything fails, describe what's wrong."

# Quick cleanup
python3 .orchestra/orchestrator.py --simple "Find and fix any obvious issues in files changed in the last 3 git commits: typos in user-facing text, missing html.escape calls, hardcoded colors that should use CSS variables."
```

### Weekly

```bash
# SEO audit
python3 .orchestra/orchestrator.py --simple "SEO audit: check 5 high-traffic pages for meta description length, title tag quality, JSON-LD validity, heading hierarchy. Flag issues with severity."

# Security scan
python3 .orchestra/orchestrator.py --simple "Security review: check for SQL injection in any raw f-string queries, missing html.escape on user input, exposed secrets in git-tracked files, any endpoints missing auth that should have it."

# Dead code
python3 .orchestra/orchestrator.py --simple "Find unused imports, dead routes (defined but not registered in main.py), and orphaned functions in the 5 largest route files. Remove anything clearly dead."

# Accessibility
python3 .orchestra/orchestrator.py --simple "Check 3 key pages (landing, explore, tool detail) for accessibility: missing alt text, low contrast text, touch targets under 44px, missing ARIA labels on interactive elements."
```

### Monthly

```bash
# Architecture review
python3 .orchestra/orchestrator.py --simple "Review the overall codebase architecture: are any files too large (over 500 lines)? Any circular dependencies? Any patterns that should be extracted to shared functions? Report findings, don't refactor."

# Dependency check
python3 .orchestra/orchestrator.py --simple "Check pyproject.toml dependencies: are any packages outdated with security issues? Any unused dependencies? Any packages we're using that have better alternatives?"

# Memory housekeeping
python3 .orchestra/orchestrator.py --simple "Review .orchestra/memory/ files. Remove any entries that are outdated or no longer relevant. Consolidate duplicate learnings in the playbook. Keep memory lean."
```

## Path to Full Autonomy

### Phase 1: Manual (now)
You run `/orchestrate` with specific tasks. S&QA gates everything.
Learn what works, build up the playbook.

### Phase 2: Scheduled (next)
Set up cron jobs for routine tasks (health, SEO, cleanup).
Review the orchestrator's logs each morning.
Adjust tasks based on what's useful vs busywork.

### Phase 3: Reactive
Add a webhook that triggers the orchestrator when:
- A deploy fails (DevOps investigates)
- An error spike is detected (Backend debugs)
- A new tool is submitted (Content writes copy, MCP updates server)

### Phase 4: Proactive
The orchestrator reads its own playbook and history to identify:
- Patterns of recurring issues → creates preventive tasks
- Departments that consistently get challenged → adjusts their CLAUDE.md
- Tasks that always get approved → fast-tracks them past S&QA

### Phase 5: Self-improving
Master starts writing skills for departments based on repeated patterns.
S&QA gets smarter by reviewing its own past verdicts.
The orchestrator proposes its own task queue based on site analytics.

## Cost Management

- Budget cap in config.json prevents runaway spending
- On a Claude subscription, "cost" = rate limit consumption, not real money
- A typical 3-agent run uses ~150k input tokens
- Health checks (1-2 agents) are cheaper than full-stack tasks (4-5 agents)
- Cron jobs should use conservative tasks to avoid burning rate limits overnight
- Check `.orchestra/history/` to see actual cost per task type and calibrate

## Troubleshooting

**"Not logged in"**: The orchestrator can't use `--bare` mode (needs OAuth).
Make sure you're logged into Claude Code in the terminal running the cron.

**Empty results**: Agent tried to use tools/skills instead of responding.
The orchestrator disables slash commands, but if still happening check the
`--tools` flag in orchestrator.py.

**S&QA vetoes everything**: Read `memory/strategy.md` — S&QA may have learned
an overly cautious pattern. Edit the memory or reset it.

**Budget exceeded mid-run**: Increase `budget_cap_usd` in config.json or
use cheaper models (haiku for routine tasks).

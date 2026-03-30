# Orchestrate — Multi-Department Agent Dispatch

Run the IndieStack orchestrator to delegate a task across department agents.

## Usage

The user provides a task after `/orchestrate`. If no task is given, ask them what they want done.

## Run

```bash
cd ~/indiestack && python3 .orchestra/orchestrator.py --simple "$ARGUMENTS"
```

The orchestrator will:
1. Decompose the task into department assignments (Master, Opus)
2. Route through Strategy & QA for approval/challenge/veto (Opus)
3. Dispatch approved work to department agents in parallel (Sonnet/Haiku)
4. Update memory and save run history

## Departments

- **Frontend** — routes, components, HTML/CSS
- **Backend** — db.py, auth, payments, scripts
- **DevOps** — Dockerfile, fly.toml, smoke tests
- **Content/SEO** — copy, meta tags, JSON-LD
- **MCP/Integration** — mcp_server.py, PyPI
- **Strategy & QA** — reviews everything, can veto

## After completion

- Report what each department did and what S&QA flagged
- Show total cost (equivalent, not actual — we're on subscription)
- Check if any files were changed: `git status --short`
- Ask the user if they want to commit the changes

## Notes

- Config: `.orchestra/config.json` (budget cap, models, department scopes)
- Memory grows in `.orchestra/memory/` — orchestrator gets smarter over time
- Logs in `.orchestra/logs/`, history in `.orchestra/history/`
- For the curses dashboard version, user can run directly: `python3 .orchestra/orchestrator.py "task"`

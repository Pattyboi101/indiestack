# Orchestra Management — Master Skill

How to effectively manage the 6-department orchestra.

## Communication Pattern
1. Send task via `send_message` to department peer ID
2. Include: what to do, which files, expected output, constraints
3. Wait for response via `check_messages` or channel push
4. Acknowledge with "Good work. Stand by." to keep them ready

## S&QA Gate
EVERY task goes through S&QA first. No exceptions. Format:
```
REVIEW REQUEST FROM MASTER:
Situation: [context]
Proposed: [departments + tasks]
Approve, challenge, or veto?
```

S&QA can:
- APPROVE: dispatch as planned
- CHALLENGE: modify scope, add conditions (use their revised version)
- VETO: stop entirely, log to playbook

## Dispatch Rules
- Max 2-3 departments per round (more = coordination overhead)
- Group independent tasks in parallel
- Sequential tasks: wait for dependency to complete before dispatching
- Always check `list_peers` before dispatching — agents may have died

## After Each Round
1. Verify code changes: `python3 -c "import ast; ast.parse(...)"`
2. Run smoke test: `python3 smoke_test.py` — 48/48
3. Commit with specific files (never `git add -A`)
4. Deploy if safe: `~/.fly/bin/flyctl deploy --remote-only`
5. Update playbook with lessons
6. Text Patrick via telegram if significant

## Management Powers (use them)
- Edit department CLAUDE.md to change rules after recurring issues
- Create skills in department skills/ directories for reusable patterns
- Edit memory.md to correct wrong lessons
- Update playbook for cross-department lessons

## When to Stop
- S&QA says stop → stop
- All autonomous work done, only manual tasks remain → cancel cron, tell Patrick
- Don't churn busywork to look productive
- "Wait for signal" is a valid action

## Department Strengths
- Frontend: fast on HTML/CSS fixes, good at UX audits
- Backend: reliable on DB queries and data patches, knows SSH patterns
- DevOps: cheap (haiku), fast on health checks and deploy verification
- Content: good at copy, knows the voice, writes fast
- MCP: thorough on API audits, knows the MCP server internals
- S&QA: catches real bugs, good at strategic thinking, knows when to stop

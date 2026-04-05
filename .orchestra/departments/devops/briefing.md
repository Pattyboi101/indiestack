# Briefing — 2026-04-05

## Task
Verify deployment health and smoke test coverage.

**Task 1 — Smoke test gaps:**
Read smoke_test.py and verify MCP-specific endpoints are covered. The current test suite has 58 endpoints. Check if `/api/tools/search?q=auth` and `/api/tools/categories` are tested. If not, add them (GET only, read-only).

**Task 2 — Deployment verification:**
After any deploy, run: `curl -sL -o /dev/null -w "%{http_code}" https://indiestack.fly.dev/`
Send Telegram notification: `bash ~/.claude/telegram.sh "Deploy verified: OK"`

**Task 3 — Health check:**
Verify `https://indiestack.fly.dev/health` returns 200. Report status.

## Constraints
- Use absolute paths in all SSH commands — `cd` is a shell builtin and fails with flyctl ssh -C
- `scripts/` is NOT in the Dockerfile — use SFTP upload pattern or `python3 -c "..."` for small scripts
- All smoke test additions must be read-only (GET only, no mutations)
- Do NOT run flyctl deploy unless explicitly instructed

## Risk Flags
- Rapid API calls can trigger rate limiting (429) — throttle between requests
- Local Docker build may be slow — use `--remote-only` if local is unavailable

## Meeting Task — 2026-04-05 (MCP Growth & Maker Pro)
- [ ] Run /backup before any Maker Pro launch work begins
- [ ] Add cron job to precompute maker citation summaries at 02:00 daily (avoids slow dashboard queries)

# IndieStack — Deploy

## Pre-Deploy
- Always run `python3 smoke_test.py` before deploying (47 endpoints)
- Commit before deploying — never deploy uncommitted work

## Deploy Command
```bash
cd ~/indiestack && ~/.fly/bin/flyctl deploy --remote-only
```
- Run deploy in background (builds take 2-4 minutes)
- Use `--buildkit` flag if depot builder times out

## Post-Deploy
- Verify: `curl -sL -o /dev/null -w "%{http_code}" https://indiestack.fly.dev/`
- Telegram notification: `bash ~/.claude/telegram.sh "message"`
- Command Hub activity log: POST to `$HUB_URL/activity` with `X-Hub-Secret` header

## MCP Server
MCP server publishing is a SEPARATE workflow — use `/publish-mcp` command. Changes to `mcp_server.py` need a PyPI publish; backend API changes take effect on deploy.

## Fly.io Config
- `min_machines_running = 1`, health check at `/health`
- GZip + security headers middleware

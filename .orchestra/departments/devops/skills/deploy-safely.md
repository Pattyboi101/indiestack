# Deploy Safely — DevOps Skill

The deployment checklist for IndieStack on Fly.io.

## Pre-Deploy
1. Verify syntax: `python3 -c "import ast; ast.parse(open('file.py').read())"`
2. Run smoke test: `python3 smoke_test.py` — must be 48/48
3. Commit changes with specific files (never `git add -A`)

## Deploy Command
```bash
# Preferred (uses Fly's builders, avoids local disk issues)
~/.fly/bin/flyctl deploy --remote-only

# Fallback (local Docker build)
~/.fly/bin/flyctl deploy --local-only
```

Use `--remote-only` by default. Local disk filled up during extended sessions (Docker build cache). `--local-only` only when remote builders are down.

## Post-Deploy
1. Verify: `curl -sL -o /dev/null -w "%{http_code}" https://indiestack.fly.dev/health` — expect 200
2. Test key endpoints if relevant changes were made
3. Report to Master

## Gotchas
- `pricing.py` is in .gitignore — needs `git add -f` to commit
- Deploy takes 2-4 minutes in background
- Cardiff Uni WiFi blocks .ai TLD — use indiestack.fly.dev for testing, but it redirects to .ai for non-/health paths
- The Fly metrics token warning is harmless — ignore it
- If deploy fails with "no space left on device", run `docker system prune -af`
- After deploy, the app restarts — smoke test may show connection resets for ~30 seconds

## MCP Server Changes
Changes to mcp_server.py need a PyPI publish (`/publish-mcp`) to reach installed clients. API-side changes take effect on deploy immediately.

# Directive: Investigate Health Check Failure

**Priority:** Critical
**Department:** DevOps
**Trigger:** Event reactor detected consecutive health check failures

## Context

- **Error:** {{error}}
- **Consecutive failures:** {{consecutive_failures}}
- **Detected at:** {{timestamp}}

## Tasks

1. Verify the outage: `curl -sL -o /dev/null -w "%{http_code}" https://indiestack.fly.dev/health`
2. If confirmed down:
   - Check Fly.io status: `~/.fly/bin/flyctl status -a indiestack`
   - Check machine logs: `~/.fly/bin/flyctl logs -a indiestack`
   - If machines are stopped: `~/.fly/bin/flyctl machine start` the stopped machine
3. If API returns errors but health is OK:
   - Check `/api/status` for degradation signals
   - Check recent deploys: `~/.fly/bin/flyctl releases -a indiestack`
4. Send Telegram update with findings

## Constraints

- Do NOT redeploy without understanding the root cause
- Do NOT modify code — this is an investigation directive
- If data corruption suspected, take a backup FIRST

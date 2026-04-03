# Devops Memory

_You are a persistent agent. This file is your long-term knowledge base._
_Read this on startup. Update it after each task with what you learned._
_Focus on: file locations, patterns, gotchas, past decisions, domain knowledge._

---

## 2026-03-31 11:44 — Standard Deploy Workflow Established
Pre-deploy: python3 scripts/chaos_monkey.py → alert Master if any FAIL
Pre-deploy: python3 smoke_test.py → must pass
Deploy: ~/.fly/bin/flyctl deploy --remote-only
Post-deploy: python3 scripts/synthetic_user.py → report failures to Master + Frontend
Both scripts exist and are verified working.
Synthetic user checks: /, /setup, /explore, /analyze, /migrations, /pricing

## 2026-03-31 11:33 — Chaos Monkey Security Scan
Built scripts/chaos_monkey.py and ran against production (https://indiestack.fly.dev)
Result: 13/16 PASS — 3 real findings:
- P2: XSS reflected in search API `query` field (<script>, <svg> tags) — fix with html.escape() in search route
- P1: No rate limiting on /api/tools/search — 20 concurrent requests all 200
- All SQL injection, auth bypass, CSRF, path traversal: PASS
Heuristic note: admin 200 responses are login pages — check for "login" (no space) not just "log in"
Reports to /tmp/chaos_monkey_report.md

## 2026-03-30 20:16 — Fly SSH Tunnel Recovered
SSH tunnel back online at 20:16
- Query executed successfully: recent claims and magic token usage
- Recent claims (6h): None
- Recent magic tokens (6h): 3 ssoready tokens generated but not used (used=0)
- Metrics token warning persists but queries work

## 2026-03-30 20:00 — Fly SSH Tunnel Issue
SSH tunnel to indiestack down (~15min reported by Master)
- Attempted: `flyctl ssh console -a indiestack -C 'echo "tunnel working"'`
- Error: "tunnel unavailable: Error contacting Fly.io API when probing — timed out"
- Fly.io Status Page: All systems operational, no incidents
- Analytics query blocked until tunnel recovers
- Likely transient API probe issue, not a major incident

## 2026-03-30 19:06 — MCP Registry Check
Checked if IndieStack MCP server is live on three registries:
- Glama: NOT LIVE (not in search or homepage)
- Official MCP Registry: NOT LIVE (not in search or homepage)
- Smithery: NOT LIVE (404 on direct page, not in explore)

All submissions appear pending or not yet submitted. Recommend contacting Patrick/Ed for status.

## 2026-03-30 18:19 — Smoke Test (Pre-Visibility Push)
Ran `python3 smoke_test.py` against https://indiestack.ai
Result: 48 passed, 0 failed
- All endpoints healthy (pages, APIs, redirects all expected status codes)
- API search working, authentication guards enforced (403, 401 as expected)
- Health endpoint: 200 OK, returns {"status": "ok"}
- Site ready for visibility push

## 2026-03-30 13:52 — Smoke Test
Ran `python3 smoke_test.py` against https://indiestack.ai
Result: 48 passed, 0 failed
- All endpoints healthy
- API search working, authentication guards enforced
- Health check returning {"status": "ok"}
- Site ready for deployment


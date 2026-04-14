---
description: Deploy to Production
---

Working directory: `~/indiestack`

## 1. Smoke test

```bash
cd ~/indiestack && python3 smoke_test.py
```

If any test fails (ignore 429 rate limit errors), stop and fix before deploying.

## 2. Check for uncommitted changes

```bash
cd ~/indiestack && git status --short
```

If there are uncommitted changes, ask the user if they want to commit first. Do not proceed until resolved.

## 3. Deploy

Run in background:

```bash
cd ~/indiestack && ~/.fly/bin/flyctl deploy --local-only
```

If local Docker fails, fall back to remote:
```bash
cd ~/indiestack && ~/.fly/bin/flyctl deploy --remote-only
```

## 4. Verify

After deploy completes:

```bash
curl -sL -o /dev/null -w "%{http_code}" https://indiestack.fly.dev/
```

Expect 200. If not, alert the user immediately.

## 5. Notify

```bash
bash ~/.claude/telegram.sh "Deployed to production"
```

## 6. Log to hub (best effort)

Skip if HUB_URL is not set.

```bash
curl -s -X POST -H "X-Hub-Secret: $HUB_SECRET" -H "Content-Type: application/json" \
  "$HUB_URL/activity" -d '{"actor":"patrick","action":"deployed to production","detail":"flyctl deploy --local-only"}'
```

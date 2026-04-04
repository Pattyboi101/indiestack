# Briefing — 2026-04-04 15:04

## Task
FULL dashboard claim-to-Pro audit — you own this entirely, both logic and UI. Read src/indiestack/routes/dashboard.py end-to-end. Check: (1) After a user claims a tool, what state/data is available? (2) Does the claimed-tool section show a visible Maker Pro upgrade CTA ($49/mo)? (3) Is there a post-claim redirect or prompt nudging upgrade? (4) If the flow is broken, missing, or visually weak — implement/fix it. This is the revenue path from claimed tools to paid subscriptions, so make the CTA prominent but not aggressive. Do NOT gate features behind payment — just nudge (vision.md: never degrade the free experience).

## S&QA Conditions
- Dashboard work goes to frontend ONLY — backend must not touch dashboard.py
- Backend must not use LIKE '%keyword%' for finding miscategorized tools — use explicit checks or tag-based matching
- Backend data quality changes are LOCAL only this run — production DB fixes need a separate SSH step with FTS rebuild
- Frontend should read vision.md and pricing context before implementing upgrade CTAs — the nudge must be soft, not a gate

## Risk Flags
- Original plan had two agents editing dashboard.py — guaranteed conflict
- Backend LIKE substring matching gotcha is relevant for finding miscategorized tools
- If backend accidentally runs data changes on production without FTS rebuild, search serves stale results

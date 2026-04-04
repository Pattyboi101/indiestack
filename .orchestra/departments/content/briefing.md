# Briefing — 2026-04-04 15:04

## Task
SEO/meta tag audit for landing page, explore page, and tool detail page. Check: OG tags (og:title, og:description, og:image, og:url), Twitter card tags, title tag uniqueness (no duplicates), meta description quality and length (150-160 chars), structured data/JSON-LD presence. Fix anything obviously missing or thin. Files: src/indiestack/routes/landing.py, explore.py, tool.py (and components.py for shared shell).

## S&QA Conditions
- Dashboard work goes to frontend ONLY — backend must not touch dashboard.py
- Backend must not use LIKE '%keyword%' for finding miscategorized tools — use explicit checks or tag-based matching
- Backend data quality changes are LOCAL only this run — production DB fixes need a separate SSH step with FTS rebuild
- Frontend should read vision.md and pricing context before implementing upgrade CTAs — the nudge must be soft, not a gate

## Risk Flags
- Original plan had two agents editing dashboard.py — guaranteed conflict
- Backend LIKE substring matching gotcha is relevant for finding miscategorized tools
- If backend accidentally runs data changes on production without FTS rebuild, search serves stale results

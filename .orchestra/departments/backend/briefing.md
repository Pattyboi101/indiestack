# Briefing — 2026-04-04 22:51

## Task
Tasks 2 and 3 — MUST be done sequentially. FIRST complete Task 2 entirely (local code changes only), THEN start Task 3 (production data changes). Task 2 — Fix 404 routes: check whether /terms, /privacy, /faq exist as route handlers in src/indiestack/routes/. Check content.py for existing legal/FAQ content served under different URLs (e.g. /legal, /about). Either (a) create minimal route handlers pointing to existing content, or (b) update the sitemap route file to use the actual working URLs — whichever is less invasive. Do NOT create placeholder content. Task 3 — Search quality: test the queries 'state management', 'bundler', 'testing framework', and 'websocket' against the production API (https://indiestack.fly.dev/api/tools?q=QUERY). For any misfiring top-3 results, fix via SSH production DB tag or description changes only — no db.py edits this pass. Use file-upload SSH pattern for any production DB changes (write script to /tmp, sftp put, run). Run FTS rebuild after any changes: INSERT INTO tools_fts(tools_fts) VALUES('rebuild') with PRAGMA busy_timeout=60000.

## S&QA Conditions
- Backend MUST complete Task 2 (local sitemap/route fixes) fully before starting Task 3 (production search quality fixes) — do not interleave
- Backend MUST use file-upload SSH pattern for any production DB writes in Task 3 — no inline python3 -c via SSH
- Content should verify /tmp/migration-intel-outreach.txt exists before trying to read it — it was created in pass 12 but confirm
- If any search query returns acceptable results (relevant top 3), skip it — only fix actual misfires

## Risk Flags
- Content SSH query: if sqlite3 quoting gets messy with IN clause, fall back to file-upload pattern rather than fighting nested quotes
- Backend Task 2: if /terms and /privacy content already exists at different URLs (e.g. /legal), prefer updating the sitemap over creating redirect routes — less code surface

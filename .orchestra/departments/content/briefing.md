# Briefing — 2026-04-04 22:51

## Task
Task 1 — Migration pitch outreach: SSH into production DB and run SELECT name, github_url, website FROM tools WHERE slug IN ('vitest', 'vite', 'jest', 'rollup', 'ava'). Read /tmp/migration-intel-outreach.txt as the base template. Write 5 personalised outreach notes to /tmp/migration-pitch-5.txt — one per tool, addressed to that tool's DevRel/maintainer lead, personalised with actual adoption numbers (Vitest: 65 adoptions, Vite: 36, Jest: 25, rollup: 15, Ava: 11) and the tool's real GitHub URL and website from the DB query. For the SSH query, use sqlite3 directly: flyctl ssh console -C "sqlite3 /data/indiestack.db 'SELECT name, github_url, website FROM tools WHERE slug IN (\"vitest\",\"vite\",\"jest\",\"rollup\",\"ava\")'" — or if quoting gets messy, use the file-upload SSH pattern (write .sql to /tmp, sftp put, run sqlite3 < file).

## S&QA Conditions
- Backend MUST complete Task 2 (local sitemap/route fixes) fully before starting Task 3 (production search quality fixes) — do not interleave
- Backend MUST use file-upload SSH pattern for any production DB writes in Task 3 — no inline python3 -c via SSH
- Content should verify /tmp/migration-intel-outreach.txt exists before trying to read it — it was created in pass 12 but confirm
- If any search query returns acceptable results (relevant top 3), skip it — only fix actual misfires

## Risk Flags
- Content SSH query: if sqlite3 quoting gets messy with IN clause, fall back to file-upload pattern rather than fighting nested quotes
- Backend Task 2: if /terms and /privacy content already exists at different URLs (e.g. /legal), prefer updating the sitemap over creating redirect routes — less code surface

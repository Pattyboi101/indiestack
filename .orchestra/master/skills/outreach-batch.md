# Outreach Batch — Master Skill

How to run a maker outreach campaign through the orchestra. Tested 2026-03-30, sent 24 emails with 11 found via this process.

## Process

### 1. Find Targets (Backend)
Query production DB for unclaimed tools sorted by github_stars:
```sql
SELECT slug, name, github_stars FROM tools
WHERE status='approved' AND maker_id IS NULL AND github_stars > 1000
ORDER BY github_stars DESC LIMIT 20
```
Exclude tools already emailed (keep a list).

### 2. Find Emails (Backend)
For each target, Backend uses gh CLI:
- `gh api users/{owner} --jq '.email'`
- `gh api repos/{owner}/{repo} --jq '.owner.email'`
- Check CONTRIBUTING.md, README security contacts
- Check composer.json/package.json author fields

Expect ~70% hit rate on emails.

### 3. Write Emails (Content)
Two template types:
- **Has MCP views:** Hook on "agents recommended your tool X times"
- **0 MCP views (most tools):** Hook on "AI agents couldn't find your tool — we fixed that"

Under 80 words. Casual, from "Pat". Include claim link: `indiestack.ai/claim/magic?tool={slug}`

### 4. Audit Target Pages (MCP dept)
BEFORE sending, check each tool's page has:
- Correct install_command (not wrong tool!)
- Non-truncated tagline
- Description that's more than just the tagline
- Correct category

Fix data issues via Backend SSH before sending.

### 5. Send (Master via SSH)
```python
await send_email(to=email, subject=subject, html_body=body)
```
Send via `~/.fly/bin/fly ssh console -a indiestack`. Max 5 per SSH call. 1 second delay between sends.

### 6. Verify Claim Links Work
Test: `curl indiestack.ai/claim/magic?tool={slug}` — should generate token and show claim page. The ?tool= fallback was added 2026-03-30.

## Gotchas
- Cal.com had mailhog install command — ALWAYS audit target pages before sending
- Claim links originally used ?tool= which broke (route only accepted ?token=) — fixed with fallback
- Airflow's email is an Apache mailing list — not appropriate for cold outreach
- syncthing only has security@syncthing.net — use cautiously

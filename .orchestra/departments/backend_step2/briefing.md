# Briefing — 2026-04-04 18:03

## Task
ONLY START THIS AFTER STEP 1 IS CONFIRMED DONE. Edit src/indiestack/db.py — in the CAT_SYNONYMS dict, add 'flags': 'feature' so that queries like 'feature flags' boost the Feature Flags category instead of broad platforms like PostHog. This is a local code change only — commit it.

## S&QA Conditions
- Step 1 (SSH data migration) must complete and report results BEFORE step 2 (db.py edit) begins — dispatch them sequentially, not in parallel
- The SSH script must print a count and list of moved tools so we can verify the scope was reasonable
- The 'orm' tag match is safe here since we're matching comma-delimited tags, but the script should log any matches for 'orm' specifically so we can verify no false positives like 'platform' leaked in
- Verify the 'database' and 'search-engine' category IDs exist before running UPDATE statements — don't assume

## Risk Flags
- Moving 30 tools at once is a significant data change — reversible but verify the list before committing
- Known failure mode: single-agent briefings with SSH + code changes tend to produce analysis instead of execution — splitting into two dispatches mitigates this
- The 'graphql' tag could match GraphQL API tools that aren't databases — the script should check description context or skip ambiguous ones

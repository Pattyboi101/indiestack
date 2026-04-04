# Briefing — 2026-04-04 14:18

## Task
After deploy completes, SSH into production and rebuild the FTS index: run `INSERT INTO tools_fts(tools_fts) VALUES('rebuild')` and `PRAGMA wal_checkpoint(TRUNCATE)` to pick up recent category fixes. Confirm no errors.

## S&QA Conditions
None

## Risk Flags
None

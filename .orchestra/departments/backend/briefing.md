# Briefing — 2026-04-04 14:52

## Task
Fix 3 search quality issues: (1) 'email' query returns Logto as #1 — check db.py engagement scoring and FTS weighting; if Logto's description is keyword-stuffed with email terms, UPDATE its description in the production DB to be accurate without email-heavy language, then check if a scoring fix in db.py (e.g. category penalty for auth tools on 'email' queries) is needed; (2) 'payments' returns laravel-stripe-webhooks as #1 — investigate its category assignment and FTS rank vs Stripe; fix by correcting its category_id to a more specific one (e.g. webhooks/integration) or adjusting engagement scoring to boost tools whose primary category matches the query term; (3) Duplicate cleanup — query the DB for (btcpay-server, btcpayserver) and (kill-bill, killbill): compare upvotes, view counts, and data completeness; UPDATE the weaker duplicate's status to 'pending' in each pair. After ALL DB changes, run: INSERT INTO tools_fts(tools_fts) VALUES('rebuild') and PRAGMA wal_checkpoint(TRUNCATE) to rebuild the FTS index.

## S&QA Conditions
None

## Risk Flags
None

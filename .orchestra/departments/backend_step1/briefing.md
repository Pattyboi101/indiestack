# Briefing — 2026-04-04 18:03

## Task
SSH into production using file-upload pattern — write a Python script to /tmp, sftp put, then run it. The script should: (a) find tools in the 'developer-tools' category whose tags (comma-delimited field) contain any of these exact tag values: postgres, mysql, sqlite, mongodb, redis, orm, migration, nosql, graphql, prisma, drizzle, sequelize, typeorm, knex, mongoose — use tag boundary matching like ',postgres,' or tags starting with 'postgres,' or ending with ',postgres' or exact match 'postgres' (NOT LIKE '%postgres%' substring). Also find tools whose slug exactly matches known DB tools (supabase, planetscale, neon, turso, etc). (b) Move up to 30 best candidates to the 'database' category. (c) Find tools with tags: meilisearch, typesense, elasticsearch, opensearch, algolia, solr — move to 'search-engine' category if it exists. (d) After all moves, rebuild FTS: INSERT INTO tools_fts(tools_fts) VALUES('rebuild') with PRAGMA busy_timeout=60000 and a retry loop, then PRAGMA wal_checkpoint(TRUNCATE). (e) Print a summary of what was moved. YOUR JOB IS TO EXECUTE THIS, NOT ANALYZE IT. Write the script, upload it, run it, report results.

## S&QA Conditions
- Step 1 (SSH data migration) must complete and report results BEFORE step 2 (db.py edit) begins — dispatch them sequentially, not in parallel
- The SSH script must print a count and list of moved tools so we can verify the scope was reasonable
- The 'orm' tag match is safe here since we're matching comma-delimited tags, but the script should log any matches for 'orm' specifically so we can verify no false positives like 'platform' leaked in
- Verify the 'database' and 'search-engine' category IDs exist before running UPDATE statements — don't assume

## Risk Flags
- Moving 30 tools at once is a significant data change — reversible but verify the list before committing
- Known failure mode: single-agent briefings with SSH + code changes tend to produce analysis instead of execution — splitting into two dispatches mitigates this
- The 'graphql' tag could match GraphQL API tools that aren't databases — the script should check description context or skip ambiguous ones

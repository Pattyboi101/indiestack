# Production Data Patch — Backend Skill

How to safely update data on the production IndieStack database.

## Access
```bash
~/.fly/bin/fly ssh console -a indiestack -C 'python3 -c "..."'
```
Production DB: `/data/indiestack.db`

## Rules
1. ALWAYS use parameterized queries when values come from variables
2. ALWAYS use `row["column_name"]` not `row[0]` — aiosqlite Row objects use dict access
3. ALWAYS verify after updating: query the row back and print it
4. NEVER use `DELETE` without Master approval
5. NEVER update `status` column without Master approval
6. Use `INSERT OR IGNORE` for idempotent inserts (safe to re-run)
7. Use `ON CONFLICT ... DO UPDATE` for upserts

## Common Patches

### Update a tool's install_command
```sql
UPDATE tools SET install_command = 'npm install X' WHERE slug = 'tool-slug';
```

### Update a tool's description
```sql
UPDATE tools SET description = 'New description' WHERE slug = 'tool-slug';
```

### Fix a tool's name
```sql
UPDATE tools SET name = 'Correct Name' WHERE slug = 'tool-slug';
```

### Bulk push autopsy data
Generate SQL file locally, pipe via SSH:
```bash
cat /tmp/data.sql | ~/.fly/bin/fly ssh console -a indiestack -C 'python3 -c "import sys, sqlite3; ..."'
```

## Gotchas
- Shell quoting is painful for inline python via SSH. For complex queries, write a script file and pipe it: `cat script.py | fly ssh console -C 'python3 -'`
- Em dashes (—) and curly quotes cause SyntaxError in inline python. Use -- and straight quotes.
- `PRAGMA journal_mode=WAL` should be set before bulk operations
- The Fly SSH tunnel can go down transiently — retry after 5-10 minutes

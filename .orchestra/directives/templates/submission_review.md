# Directive: Review New Tool Submission

**Priority:** Medium
**Department:** Backend
**Trigger:** Event reactor detected new pending submission

## Context

- **Tool:** {{tool_name}} (`{{tool_slug}}`)
- **Submitted:** {{submitted_at}}

## Tasks

1. Check the tool at `indiestack.ai/admin` — verify it's a legitimate developer tool (not spam, games, or creative tools)
2. If legitimate: approve, verify category assignment is correct, check tags
3. If the tool has a GitHub URL: verify it resolves, check stars/last commit
4. After approval: rebuild FTS index on production
   ```sql
   INSERT INTO tools_fts(tools_fts) VALUES('rebuild');
   PRAGMA wal_checkpoint(TRUNCATE);
   ```
5. If the submitter is a maker: check if they should get a welcome email

## Constraints

- Do NOT auto-approve without human review
- Do NOT deploy — this is a data change only
- Stage specific files only if any code changes are needed

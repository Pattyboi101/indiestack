# Briefing — 2026-04-04 22:21

## Task
Read src/indiestack/routes/explore.py (or equivalent explore/browse route). Check how categories are fetched and ordered for the category grid — is it alphabetical, by tool count, or arbitrary? Identify if popular categories (Database, Authentication, DevOps) appear prominently. If the sort is suboptimal, update the DB query or in-memory sort to order by tool count DESC so high-value categories surface first. Report what the current sort is and what was changed.

## S&QA Conditions
- Backend MUST use file-upload SSH pattern — no inline python via flyctl ssh console -C
- Frontend Frameworks category is RESEARCH ONLY — write recommendation to /tmp, do not create
- Do NOT move OpenAPI/AsyncAPI tools to ai-standards — only genuinely AI-specific standards
- FTS rebuild must use PRAGMA busy_timeout=60000 and retry loop

## Risk Flags
- tags LIKE '%mcp%' without comma-delimited matching could theoretically match unexpected substrings — using proper comma-delimited pattern instead
- ai-standards category may end up with very few tools after excluding OpenAPI/AsyncAPI — that's fine per pass 13 guidance ('leave empty if fewer than 3')
- Backend task is heavy (3 category populations + research query) — may hit budget ceiling before completing all parts

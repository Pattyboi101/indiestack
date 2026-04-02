# Mistakes We've Made — Don't Repeat These

- When renaming SQL column aliases in a shared function (like `get_search_gaps`), grep ALL consumers across the entire codebase — not just the file that triggered the original bug. Every route file that calls the function needs updating.

- `flyctl ssh console -C "cd /app && ..."` fails because `cd` is a shell builtin. Use absolute paths instead: `python3 /app/scripts/foo.py`

- The MCP server runs from the PyPI-installed package, not local source. Changes to `mcp_server.py` presentation (formatting, labels) need a PyPI publish to take effect. Backend API changes (ranking, filtering) take effect immediately on deploy since the MCP server calls the production API.

- `category_slug` doesn't exist as a direct column on the `tools` table — it's on `categories`. Use JOIN: `JOIN categories cat ON t.category_id=cat.id`

- Don't use `git add -A` or `git add .` — stage specific files by name to avoid accidentally committing secrets (.env, credentials) or large binaries.

- Smoke test 429 errors during a session are API rate limiting from earlier MCP tool testing, not code failures.

- `<button>` cannot be nested inside `<a>` in valid HTML — restructure wrapper elements when adding buttons to linked cards.

- ALTER TABLE ADD COLUMN can't include a UNIQUE constraint directly — add the column first, then CREATE UNIQUE INDEX separately.

- When a shared DB function's return shape changes (column aliases renamed), search for ALL callers across ALL route files before deploying. The function is a data contract.

- The `scripts/` directory is not copied in the Dockerfile. To run scripts on production, either add a COPY line or pipe inline via `python3 -c "..."` on SSH.

- FTS5 multi-word queries use AND by default. "payments integration" requires BOTH words to match, returning tools that mention "integration" in descriptions (like scheduling apps) instead of actual payment tools. Fix: strip common stop/filler words (best, alternative, integration, solution, for, etc.) via `_FTS_STOP_WORDS` in db.py's `sanitize_fts()`.

- The engagement scoring passes the raw query for category/tag matching. For multi-word queries, the category match should use the FIRST meaningful term ("auth" from "auth for nextjs") so it matches "Authentication" category. See `_cat_term` in db.py.

- Stats in copy go stale fast. Tool count was "3,100+" when we had 8,197 approved. Repo count was "8,700+" when actual was 4,535. Verify claims against production DB before publishing.

- After fixing data on production (tags, categories, install commands), ALWAYS rebuild the FTS index: `INSERT INTO tools_fts(tools_fts) VALUES('rebuild')` + `PRAGMA wal_checkpoint(TRUNCATE)`. Otherwise the search API serves stale cached results until the next deploy.

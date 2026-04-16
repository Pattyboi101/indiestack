# Mistakes We've Made — Don't Repeat These

- Adding routers pushes `fastapi_x402` lifespan nesting deeper. With 51 routers the nested async context managers exceeded Python's default recursion limit (1000), crashing the app on startup with a `merged_lifespan` RecursionError. Fix: `sys.setrecursionlimit(2000)` at the top of main.py. If adding more routers in future, check this limit.

- NEVER use `docker build --no-cache` for deploys. The `--no-cache` flag pulls fresh pip dependencies, and newer versions of FastAPI/Starlette have lifespan nesting bugs that crash the app with 50 routers. The cached pip layer has the working versions. Use `docker build` (with cache) for all deploys. Only use `--no-cache` if you've explicitly pinned all dependencies AND tested locally first.

- `db.execute_fetchone()` does NOT exist in the db module. Use `await (await d.execute(query, params)).fetchone()` directly on the connection object. The hallucinated function survived in main.py because those calls are wrapped in try/except. Always use the cursor pattern: `cursor = await d.execute(...); row = await cursor.fetchone()`.

- `hello@indiestack.ai` does NOT exist. The contact email is `pajebay1@gmail.com`. This was hallucinated across 5 files (main.py, intel.py, sla.py, trust.py). Always use `pajebay1@gmail.com` until an actual indiestack.ai email is set up.

- Flex child `overflow-x:auto` does NOT work if any ancestor in the flex chain is missing `min-width:0`. The child can never shrink below its content width, so `overflow-x:auto` never triggers. Fix: add `min-width:0` to EVERY flex child in the chain that needs to shrink. Also: never add `overflow:hidden` to the flex wrapper div — it clips scrollable children. The install_block in tool.py hit this; fixed Apr 7.

- `bm25(tools_fts)` with equal column weights lets "alternative to X" descriptions outrank X itself for a brand-name query. A tool with "netlify" 5× in its description beats Netlify for query "netlify". Fix: use weighted bm25 `bm25(tools_fts, 10.0, 5.0, 1.0, 3.0)` (name, tagline, description, tags) AND add a slug-exact-match boost (+2000 engagement) so the exact tool always ranks first.

- `json.dumps()` does NOT escape `<`, `>`, `&` — raw JSON in `<script type="application/ld+json">` blocks is vulnerable to `</script>` injection. Always call `.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')` on the result before embedding in HTML. Fixed in tool.py, browse.py, use_cases.py, launch_with_me.py.

- `stats.get('key', 0)` does NOT guard against `None` — if the key exists with value `None`, it returns `None` and breaks int comparisons. Always use `stats.get('key') or 0` for numeric stats from DB queries. This caused 500s on `/tool/*` pages from `analytics_wall_blurred` in components.py.

- Maker Pro is **$19/mo**. Not $49. The $49 figure appears in old planning docs and keeps getting copy-pasted. The canonical source is stripe.md. Any agent touching pricing.py, landing.py, or copy must verify against stripe.md first.

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

- DO NOT gate MCP features behind API keys or accounts. We tried this before and it tanked MCP adoption. Keep the MCP server fully anonymous and frictionless. If we want accounts, use soft nudges after repeated use — never degrade the anonymous experience.

- After fixing data on production (tags, categories, install commands), ALWAYS rebuild the FTS index: `INSERT INTO tools_fts(tools_fts) VALUES('rebuild')` + `PRAGMA wal_checkpoint(TRUNCATE)`. Otherwise the search API serves stale cached results until the next deploy.

- `LIKE '%orm%'` substring matching is dangerously broad — "transform", "platform", "format", "performance", "information" all contain "orm". When finding tools by name pattern, use exact word matching: check `slug IN (...)` explicit list, or use `LIKE '%,orm,%'` tag matching (which requires "orm" as a standalone comma-delimited tag). Do NOT use `LOWER(name) LIKE '%orm%'` for categorization queries.

- `_CAT_SYNONYMS` values are matched via `LOWER(c.name) LIKE ('%' || LOWER(val) || '%')`. The Developer Tools category name is "Developer Tools" — mapping to `"devtools"` will NEVER match. Always use `"developer"` (matches "Developer Tools"). Previously broken: dotenv, turborepo, nx, zod, yup, valibot, validation. Fixed Apr 10.

- Adding a programming language name to `_FRAMEWORK_QUERY_TERMS` strips it from FTS queries — which breaks searches where that language IS the primary term. `"fastapi python api"` with "python" in `_FRAMEWORK_QUERY_TERMS` strips both "fastapi" AND "python", leaving only "api" which returns garbage. Only add runtime qualifiers that are NEVER the thing being searched for (e.g. "nodejs" is safe; "python", "rust", "java" are not). Fixed Apr 10.

- SDK wrapper libraries (laravel-stripe-webhooks, stripe-serverless-webhook, etc.) have "stripe" in their NAME and thus get huge FTS boosts for "stripe alternative" queries, ranking above actual Stripe alternatives (Polar, Lemon Squeezy). Fix: mark wrapper tools `is_reference=1` AND cap `quality_score` at 40 so their engagement score stays low. Fixed Apr 10.

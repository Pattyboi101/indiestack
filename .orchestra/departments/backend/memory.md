# Backend Memory

_You are a persistent agent. This file is your long-term knowledge base._
_Read this on startup. Update it after each task with what you learned._
_Focus on: file locations, patterns, gotchas, past decisions, domain knowledge._

---

## 2026-04-01

### Production DB State (confirmed)
- Stripe: was `status='rejected'` — fixed to approved, cat=13 (Payments), tags+install added
- Mailgun/Sendgrid/Postmarks/Gumroad: had empty tags — fixed with email/payments tags + install commands
- Postmarks: slug is `postmarks` (not `postmark`), was in Developer Tools, fixed to Email Marketing (cat=2)
- tool_categories junction: Stripe added to Payments, Postmarks added to Email Marketing

### FTS5 Architecture (tools_fts)
- `CREATE VIRTUAL TABLE tools_fts USING fts5(name, tagline, description, tags, content='tools', content_rowid='id')`
- FTS triggers exist: `tools_ai`, `tools_ad`, `tools_au` — auto-update FTS on INSERT/DELETE/UPDATE
- To force full rebuild: `INSERT INTO tools_fts(tools_fts) VALUES('rebuild')`
- After data changes, always run rebuild + WAL checkpoint
- FTS query format: `sanitize_fts("email")` → `'"email"*'` (prefix query)
- BM25 rank is NEGATIVE in FTS5 — more negative = better match

### Search Ranking Formula (db.py:2308–2325)
- Exact name match: +150
- Name prefix match: +60
- Category match (tool_categories junction, NOT primary category_id): +100
- Tag match: +40
- upvote_count * 2
- mcp_view_count * 3
- min(github_stars, 5000) / 100.0
- ORDER BY: `rank - (engagement / 50.0)` — lower is better
- SaaS tools (Stripe, Resend) have 0 stars → ranked below OSS repos. MOAT brain fixing formula.

### Claim Flow (main.py:3457–3537)
- POST /api/claim → email domain match → verification email → GET /api/claim/verify/{token}
- No payment gate — claims are 100% free currently
- CTA copy explicitly says "Free, no commission, no fees"
- `create_verification_checkout` in payments.py exists (£29 verified badge) but NOT in claim flow

### Payments.py Summary
- `create_checkout_session`: marketplace tool sales (Stripe Connect, commission)
- `create_verification_checkout`: £29 verified badge (direct platform charge)
- `create_stack_checkout_session`: Vibe Stack bundles
- `create_connect_account` / `create_onboarding_link`: maker onboarding for selling
- No $99 claim fee — would need new `create_claim_checkout` + success handler

### WAL / SQLite Caching Note
- After committing data changes via SSH sqlite3, live API may serve stale results
- Root cause: app's SQLite page cache retains old state between requests
- Fix: `PRAGMA wal_checkpoint(TRUNCATE)` helps, but full propagation requires app restart/deploy
- Symptoms: DB simulation shows correct results, live API shows old results

## 2026-03-30

### CRITICAL: aiosqlite Row Access
- aiosqlite with row_factory=Row uses DICT access: `row["column_name"]`, NOT `row[0]`
- Always alias computed columns in SQL: `COUNT(*) as n`, then access `row["n"]`
- This caused TWO production bugs. Never use integer index on aiosqlite rows.



### SSH Script Pattern
- For complex Python string operations via fly SSH, inline `python3 -c "..."` breaks on escaping (em-dashes, backslashes, quotes).
- Better pattern: write script to `/tmp/fix.py` locally → `fly sftp shell -a indiestack` to upload → `fly ssh console -a indiestack -C 'python3 /tmp/fix.py'`



### MCP Registry server.json
- File: `server.json` at repo root (already existed at v1.9.0, updated to v1.11.1)
- Schema: `https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json`
- Name format for registry: `io.github.Pattyboi101/indiestack`
- Valid `runtimeHint` values (from constants.go): `npx`, `uvx`, `docker`, `dnx`
- Valid `registryType` values: `npm`, `pypi`, `oci`, `nuget`, `mcpb`
- IndieStack uses `runtimeHint: "uvx"` + `runtimeArguments` to encode `uvx --from indiestack indiestack-mcp`
- Argument objects: `type: "named"` (needs `name` field) or `type: "positional"`. Use `value` for hardcoded values.
- Current MCP version: 1.11.1 (matches pyproject.toml)

## 2026-04-04 — Search quality fixes
- **Logto 'email' bug**: Logto had "email" in its tags (`authentication,authorization,email,identity,jwt`). This caused it to FTS-match "email" queries and show up #3. Fix: removed "email" from tags → now `authentication,authorization,identity,jwt,oidc,sso`.
- **laravel-stripe-webhooks 'payments' bug**: It was in the Payments category (id=13) + had "payments" in tags — giving it both the +180 category bonus AND tag FTS match. Fix: moved to API Tools (id=16) and removed "payments" from tags → now `stripe,webhooks,laravel,php,laravel-package`.
- **Duplicates**: btcpayserver (quality=38.7) and killbill (quality=48.1) both set to status='pending'. Stronger duplicates (btcpay-server quality=100, kill-bill quality=100) remain approved.
- **FTS rebuild**: Always rebuild after tag/category changes: `conn.execute("INSERT INTO tools_fts(tools_fts) VALUES(?)", ("rebuild",))` — NOT a string literal in SQL, use a param! `chr()` is not available in SQLite on production (Alpine).
- **tools table has no view_count column** — it's `mcp_view_count`. Always check PRAGMA table_info(tools) if unsure about columns.
- **SSH inline Python quoting**: For complex queries with FTS MATCH params containing quotes/stars, pipe as base64 or use heredoc approach. The `-C 'python3 -c "..."'` works for simple scripts.


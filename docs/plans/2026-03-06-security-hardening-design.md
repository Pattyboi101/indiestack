# Security Hardening — Design Document

**Goal:** Fix all 25 security audit findings before Product Hunt launch on Saturday.

**Scope:** All source files. No new routes or features — purely defensive hardening.

---

## Group 1: SQL Injection in Analytics (`db.py`)

8 analytics functions use f-string interpolation for `days` parameter:
- `get_trending_scored` (line 3205)
- `get_maker_funnel` (line 3231)
- `get_recent_activity` (line 3272) — 4 sub-queries
- `get_platform_funnel` (line 3888)
- `get_top_tools_by_metric` (line 3920) — also `limit`
- `get_maker_leaderboard` (line 3935)

**Fix:** Replace all `f"...{days}..."` with `datetime('now', ? || ' days')` using parameterized `?`. For `get_top_tools_by_metric`, table/column already whitelisted via `table_map` dict so that's safe — just parameterize `days` and `limit`.

Also fix FK safety in `delete_tool()` (line 1618): wrap in try/finally so `PRAGMA foreign_keys = ON` always runs.

Add FTS5 term length limit in `sanitize_fts()`: cap each term to 40 chars.

Add missing indexes: `search_logs(query)`, `search_logs(source)`, `search_logs(created_at)`.

Reduce health check HTTP timeout from 10s to 5s.

## Group 2: Email HTML Injection (`email.py`)

All email template functions interpolate user-supplied values (`tool_name`, `buyer_email`, `review_body`, `maker_name`, `reviewer_name`, `update_title`, `user_name`) directly into HTML f-strings without escaping.

**Fix:** Add `from html import escape` and wrap all user-supplied values with `escape()` at the point of interpolation in every template function. Values that are URLs (`tool_url`, `delivery_url`, etc.) don't need HTML escaping since they're in href attributes, but tool names, email addresses, and free-text fields do.

## Group 3: Auth Hardening (`auth.py`)

Default admin password `"indiestack-dev-pw"` used as fallback when env var not set.

**Fix:** In production (detected via `FLY_APP_NAME` env var), raise `RuntimeError` if `INDIESTACK_ADMIN_PASSWORD` not set. In local dev, keep the default for convenience.

## Group 4: Stripe Webhook Guard (`payments.py`)

`STRIPE_WEBHOOK_SECRET` defaults to empty string. If empty, `stripe.Webhook.construct_event` may not properly verify signatures.

**Fix:** In `verify_webhook()`, raise `ValueError("Stripe webhook secret not configured")` if `STRIPE_WEBHOOK_SECRET` is empty.

## Group 5: CSRF Token System (`main.py` + `components.py` + all route files)

Current CSRF protection is origin-header-only. No tokens. Origin check allows requests with no Origin AND no Referer.

**Fix — three parts:**

### 5a: Token generation + middleware (`main.py`)
- Generate CSRF token: `secrets.token_urlsafe(32)`
- Store in cookie: `indiestack_csrf`, `httponly=False` (JS needs to read for AJAX), `samesite=lax`, `secure=True`
- Set cookie in security headers middleware if not already present
- Validation middleware: on POST/PUT/DELETE/PATCH, check `csrf_token` form field OR `X-CSRF-Token` header matches cookie value
- Exempt paths: `/webhooks/stripe`, `/api/cite`, `/api/tools/search`, `/api/pulse`, other read-only API endpoints

### 5b: Helper function (`components.py`)
- `csrf_hidden_input(request)` returns `<input type="hidden" name="csrf_token" value="...">`
- All form-rendering code calls this inside `<form>` tags

### 5c: Insert into all forms (all route files)
- Every `<form method="POST">` or `<form method="post">` gets the hidden input
- Forms in: `main.py`, `admin.py`, `admin_outreach.py`, `dashboard.py`, `account.py`, `landing.py`, `tool.py`, `submit.py`, `explore.py`, `stacks.py`

### 5d: Tighten origin check
- Block requests with no Origin AND no Referer (currently allows them through)

## Group 6: XSS Fixes

### Landing search (`landing.py:488-496`)
Add a JS `esc()` function before the search handler:
```javascript
function esc(s){var d=document.createElement('div');d.textContent=s;return d.innerHTML;}
```
Then wrap `t.name`, `t.tagline`, `t.price` with `esc()` in the innerHTML template.

### Pulse feed (`pulse.py:43,50,56`)
`tool_slug` is not escaped — used in href attributes. Apply `escape()` (already imported) or `quote()`.

## Group 7: CSP Header (`main.py`)

Add Content-Security-Policy to security headers middleware:
```
default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' https: data:; font-src 'self' https://fonts.gstatic.com; connect-src 'self'; frame-src https://www.youtube.com https://player.vimeo.com
```

Note: `unsafe-inline` needed for script/style because all JS/CSS is inline in Python templates. `frame-src` for video embeds.

## Group 8: Rate Limiting

### Admin login (`main.py`)
Simple in-memory dict: `{ip: (attempt_count, first_attempt_time)}`. Block after 5 failed attempts within 15 minutes. Reset on success.

### MCP publish_tool (`mcp_server.py`)
In-memory counter per session/API key. Max 10 submissions per hour.

### MCP input validation (`mcp_server.py`)
- Clamp `limit` params to max 50
- Validate URL format on `publish_tool` (must start with `http://` or `https://`)
- Cap string field lengths (name: 200, tagline: 500, description: 5000)

## Group 9: Misc Hardening

- **OAuth redirect** (`account.py`): Validate `next_url` from cookie — must be relative path starting with `/`, not `//`
- **Sitemap** (`main.py`): Add `LIMIT 5000` to tool and maker queries
- **tool_slug length** (`main.py`): Cap at 200 chars on subscribe endpoint
- **URL validation** (`main.py`): Block `javascript:` and `data:` URLs on tool submission
- **Error handler** (`main.py`): Generic "Internal server error" message, don't pass through exception details
- **Email blast** (`admin_outreach.py`): Add 1-second delay between sends to avoid Gmail rate limits
- **Silent exceptions** (`main.py`): Add `logger.exception()` to background task catch blocks

---

## Files Modified

| File | Changes |
|------|---------|
| `db.py` | SQL injection (8 functions), FK safety, FTS5 limits, indexes, health timeout |
| `email.py` | HTML escape all user data in templates |
| `auth.py` | Remove default admin password in prod |
| `payments.py` | Guard empty webhook secret |
| `main.py` | CSRF middleware + cookie, CSP header, admin rate limit, origin check, sitemap limit, URL validation, error handler, background task logging |
| `components.py` | `csrf_hidden_input()` helper |
| `landing.py` | JS XSS escape in search innerHTML, CSRF token in forms |
| `pulse.py` | Escape tool_slug |
| `mcp_server.py` | Rate limiting, input validation |
| `account.py` | OAuth redirect validation, CSRF tokens in forms |
| `admin.py` | CSRF tokens in forms |
| `admin_outreach.py` | CSRF tokens in forms, email blast rate limit |
| `dashboard.py` | CSRF tokens in forms |
| `tool.py` | CSRF tokens in forms |
| `submit.py` | CSRF tokens in forms |
| `explore.py` | CSRF tokens in forms |
| `stacks.py` | CSRF tokens in forms |

## Out of Scope

- Password complexity requirements
- Two-factor authentication
- IP allowlisting for admin
- Full session token rotation
- Encrypted session storage

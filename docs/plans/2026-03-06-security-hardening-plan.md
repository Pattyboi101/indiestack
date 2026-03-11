# Security Hardening — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix all 25 security audit findings before Product Hunt launch.

**Architecture:** Double Submit Cookie CSRF pattern with auto-injection via JS in `page_shell()` — no manual form edits needed. SQL injection fixed by parameterizing all f-string interpolated `days` values. XSS fixed by escaping user data in innerHTML and email templates.

**Tech Stack:** Python/FastAPI, aiosqlite, inline HTML/CSS/JS

**Design doc:** `docs/plans/2026-03-06-security-hardening-design.md`

---

## Task 1: SQL Injection + DB Hardening (`db.py`)

**Files:**
- Modify: `src/indiestack/db.py`

**Step 1: Fix `get_trending_scored` (line 3205)**

Replace f-string `days` interpolation with parameter. Change:
```python
async def get_trending_scored(db, limit: int = 20, days: int = 7):
    """Get tools ranked by time-decayed heat score.
    Score = (upvotes + views_7d) / (hours_since_created ^ 1.5)"""
    cursor = await db.execute(f"""
        ...
            WHERE viewed_at >= datetime('now', '-{days} days')
        ...
    """, (limit,))
```
to:
```python
async def get_trending_scored(db, limit: int = 20, days: int = 7):
    """Get tools ranked by time-decayed heat score.
    Score = (upvotes + views_7d) / (hours_since_created ^ 1.5)"""
    days_param = f'-{int(days)} days'
    cursor = await db.execute("""
        SELECT t.*, c.name as category_name, c.slug as category_slug,
               COALESCE(v.view_count, 0) as views_7d,
               (t.upvote_count + COALESCE(v.view_count, 0) + (CASE WHEN t.claimed_at IS NOT NULL THEN 20 ELSE 0 END)) * 1.0 /
               MAX(1.0, POWER(MAX(1, (julianday('now') - julianday(t.created_at)) * 24), 1.5)) as heat_score,
               EXISTS(SELECT 1 FROM maker_updates mu WHERE mu.tool_id = t.id AND mu.created_at >= datetime('now', '-14 days')) as has_changelog_14d
        FROM tools t
        JOIN categories c ON t.category_id = c.id
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as view_count
            FROM tool_views
            WHERE viewed_at >= datetime('now', ?)
            GROUP BY tool_id
        ) v ON v.tool_id = t.id
        WHERE t.status = 'approved'
        ORDER BY heat_score DESC
        LIMIT ?
    """, (days_param, limit))
```

**Step 2: Fix `get_maker_funnel` (line 3228)**

Same pattern. Replace `f"""` with `"""` and parameterize `days`. This function has TWO `{days}` interpolations (tool_views and outbound_clicks subqueries).

Change to:
```python
async def get_maker_funnel(db, maker_id: int, days: int = 7):
    days_param = f'-{int(days)} days'
    cursor = await db.execute("""
        SELECT t.id, t.name as tool_name, t.slug as tool_slug,
               t.upvote_count as upvotes,
               COALESCE(v.view_count, 0) as views,
               COALESCE(w.save_count, 0) as wishlist_saves,
               COALESCE(c.click_count, 0) as clicks
        FROM tools t
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as view_count
            FROM tool_views
            WHERE viewed_at >= datetime('now', ?)
            GROUP BY tool_id
        ) v ON v.tool_id = t.id
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as save_count
            FROM wishlists
            GROUP BY tool_id
        ) w ON w.tool_id = t.id
        LEFT JOIN (
            SELECT tool_id, COUNT(*) as click_count
            FROM outbound_clicks
            WHERE created_at >= datetime('now', ?)
            GROUP BY tool_id
        ) c ON c.tool_id = t.id
        WHERE t.maker_id = ?
        ORDER BY views DESC
    """, (days_param, days_param, maker_id))
    return await cursor.fetchall()
```

**Step 3: Fix `get_recent_activity` (line 3272)**

This function has FOUR sub-queries each with `{days}`. Change all four from `f"""` to `"""` with parameterized `?`:

```python
async def get_recent_activity(db, limit: int = 10, days: int = 7):
    days_param = f'-{int(days)} days'
    activities = []
    cursor = await db.execute("""
        SELECT t.name, t.created_at FROM tools t
        WHERE t.status = 'approved' AND t.created_at >= datetime('now', ?)
        ORDER BY t.created_at DESC LIMIT 5
    """, (days_param,))
    for row in await cursor.fetchall():
        activities.append({
            'type': 'launch',
            'message': f"{row['name']} just launched",
            'created_at': row['created_at']
        })
    cursor2 = await db.execute("""
        SELECT t.name, u.created_at FROM upvotes u
        JOIN tools t ON u.tool_id = t.id
        WHERE u.created_at >= datetime('now', ?)
        ORDER BY u.created_at DESC LIMIT 5
    """, (days_param,))
    for row in await cursor2.fetchall():
        activities.append({
            'type': 'upvote',
            'message': f"Someone upvoted {row['name']}",
            'created_at': row['created_at']
        })
    cursor3 = await db.execute("""
        SELECT mu.title, m.name as maker_name, mu.created_at
        FROM maker_updates mu JOIN makers m ON mu.maker_id = m.id
        WHERE mu.created_at >= datetime('now', ?)
        ORDER BY mu.created_at DESC LIMIT 5
    """, (days_param,))
    for row in await cursor3.fetchall():
        activities.append({
            'type': 'update',
            'message': f"{row['maker_name']} posted: {row['title']}" if row['title'] else f"{row['maker_name']} shipped an update",
            'created_at': row['created_at']
        })
    cursor4 = await db.execute("""
        SELECT t.name, p.created_at FROM purchases p
        JOIN tools t ON p.tool_id = t.id
        WHERE p.created_at >= datetime('now', ?)
        ORDER BY p.created_at DESC LIMIT 5
    """, (days_param,))
    for row in await cursor4.fetchall():
        activities.append({
            'type': 'sale',
            'message': f"Someone just bought {row['name']}!",
            'created_at': row['created_at']
        })
    activities.sort(key=lambda x: x['created_at'], reverse=True)
    return activities[:limit]
```

**Step 4: Fix `get_platform_funnel` (line 3886)**

Three `{days}` interpolations. Change to parameterized:

```python
async def get_platform_funnel(db, days: int = 30) -> list:
    days_param = f'-{int(days)} days'
    cursor = await db.execute("""
        SELECT t.id, t.name, t.slug,
               COALESCE(v.cnt, 0) as views,
               COALESCE(c.cnt, 0) as clicks,
               COALESCE(w.cnt, 0) as wishlists,
               COALESCE(p.cnt, 0) as purchases
        FROM tools t
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM tool_views
                   WHERE viewed_at >= datetime('now', ?) GROUP BY tool_id) v ON v.tool_id = t.id
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM outbound_clicks
                   WHERE created_at >= datetime('now', ?) GROUP BY tool_id) c ON c.tool_id = t.id
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM wishlists GROUP BY tool_id) w ON w.tool_id = t.id
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM purchases
                   WHERE created_at >= datetime('now', ?) GROUP BY tool_id) p ON p.tool_id = t.id
        WHERE t.status = 'approved'
          AND (COALESCE(v.cnt, 0) > 0 OR COALESCE(c.cnt, 0) > 0 OR COALESCE(w.cnt, 0) > 0 OR COALESCE(p.cnt, 0) > 0)
        ORDER BY views DESC
        LIMIT 30
    """, (days_param, days_param, days_param))
    return [dict(r) for r in await cursor.fetchall()]
```

**Step 5: Fix `get_top_tools_by_metric` (line 3910)**

Table/column names come from a whitelist (`table_map`) so those are safe to interpolate. But `days` and `limit` must be parameterized:

```python
async def get_top_tools_by_metric(db, metric: str = 'views', days: int = 30, limit: int = 15) -> list:
    table_map = {
        'views': ('tool_views', 'viewed_at'),
        'clicks': ('outbound_clicks', 'created_at'),
        'wishlists': ('wishlists', 'created_at'),
    }
    if metric not in table_map:
        return []
    table, date_col = table_map[metric]
    days_param = f'-{int(days)} days'
    cursor = await db.execute(f"""
        SELECT t.name, t.slug, COUNT(m.id) as count
        FROM tools t
        JOIN {table} m ON m.tool_id = t.id
        WHERE m.{date_col} >= datetime('now', ?)
          AND t.status = 'approved'
        GROUP BY t.id
        ORDER BY count DESC
        LIMIT ?
    """, (days_param, int(limit)))
    return [dict(r) for r in await cursor.fetchall()]
```

Note: `table` and `date_col` stay as f-string because they come from the hardcoded whitelist dict. The `f"""` is kept for those two only. `days` and `limit` are parameterized with `int()` cast for safety.

**Step 6: Fix `get_maker_leaderboard` (line 3933)**

Two `{days}` interpolations:

```python
async def get_maker_leaderboard(db, days: int = 30) -> list:
    days_param = f'-{int(days)} days'
    cursor = await db.execute(f"""
        SELECT m.id, m.name, m.slug,
               COUNT(DISTINCT t.id) as tool_count,
               COALESCE(SUM(v.cnt), 0) as total_views,
               COALESCE(SUM(c.cnt), 0) as total_clicks,
               MAX(mu.created_at) as last_update
        FROM makers m
        JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM tool_views
                   WHERE viewed_at >= datetime('now', ?) GROUP BY tool_id) v ON v.tool_id = t.id
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM outbound_clicks
                   WHERE created_at >= datetime('now', ?) GROUP BY tool_id) c ON c.tool_id = t.id
        LEFT JOIN maker_updates mu ON mu.maker_id = m.id
        GROUP BY m.id
        ORDER BY total_views DESC
    """, (days_param, days_param))
```

Note: This function still uses `f"""` because... wait, it doesn't need to anymore since `days` is parameterized. But it has no other interpolations. Change `f"""` to `"""`.

Actually re-check: the original has no other interpolations besides `{days}`. So change to `"""` and parameterize:

```python
async def get_maker_leaderboard(db, days: int = 30) -> list:
    days_param = f'-{int(days)} days'
    cursor = await db.execute("""
        SELECT m.id, m.name, m.slug,
               COUNT(DISTINCT t.id) as tool_count,
               COALESCE(SUM(v.cnt), 0) as total_views,
               COALESCE(SUM(c.cnt), 0) as total_clicks,
               MAX(mu.created_at) as last_update
        FROM makers m
        JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM tool_views
                   WHERE viewed_at >= datetime('now', ?) GROUP BY tool_id) v ON v.tool_id = t.id
        LEFT JOIN (SELECT tool_id, COUNT(*) as cnt FROM outbound_clicks
                   WHERE created_at >= datetime('now', ?) GROUP BY tool_id) c ON c.tool_id = t.id
        LEFT JOIN maker_updates mu ON mu.maker_id = m.id
        GROUP BY m.id
        ORDER BY total_views DESC
    """, (days_param, days_param))
```

**Step 7: Fix `delete_tool` FK safety (line 1617)**

Wrap FK disable in try/finally:

```python
    # Temporarily disable FK checks to catch any remaining references
    await db.execute("PRAGMA foreign_keys = OFF")
    try:
        await db.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
    finally:
        await db.execute("PRAGMA foreign_keys = ON")
    await db.commit()
```

**Step 8: Add FTS5 term length limit in `sanitize_fts` (line 1081)**

Change:
```python
def sanitize_fts(query: str) -> str:
    """Sanitize input for FTS5 — strip special chars, add prefix matching."""
    query = re.sub(r'[^\w\s]', '', query).strip()
    if not query:
        return ''
    terms = query.split()
    return ' '.join(f'"{t}"*' for t in terms[:10])
```
to:
```python
def sanitize_fts(query: str) -> str:
    """Sanitize input for FTS5 — strip special chars, add prefix matching."""
    query = re.sub(r'[^\w\s]', '', query).strip()
    if not query:
        return ''
    terms = query.split()
    return ' '.join(f'"{t[:40]}"*' for t in terms[:10])
```

**Step 9: Add missing indexes in `init_db`**

Find the `init_db` function and add after the existing CREATE INDEX statements:

```python
    await db.execute("CREATE INDEX IF NOT EXISTS idx_search_logs_query ON search_logs(query)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_search_logs_source ON search_logs(source)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_search_logs_created ON search_logs(created_at)")
```

**Step 10: Reduce health check timeout**

Find the health check HTTP call (around line 1049) and change timeout from 10 to 5:

Search for `timeout=10` or `timeout` near the health check and change to `timeout=5`.

**Step 11: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read())"`
Expected: No output (clean parse)

---

## Task 2: Email HTML Escaping (`email.py`)

**Files:**
- Modify: `src/indiestack/email.py`

**Step 1: Add import**

At the top of the file (after line 7), add:
```python
from html import escape
```

**Step 2: Escape user data in ALL template functions**

For each function below, wrap user-supplied string parameters with `escape()` at the START of the function body (before the f-string template). This ensures the variable is escaped before any interpolation.

Functions to modify (add `param = escape(param)` lines at start):

1. `purchase_receipt_html` (line 65): `tool_name = escape(tool_name)`
2. `maker_sale_notification_html` (line 77): `tool_name = escape(tool_name)`, `buyer_email = escape(buyer_email)`
3. `tool_approved_html` (line 104): `tool_name = escape(tool_name)`
4. `new_review_html` (line 122): `tool_name = escape(tool_name)`, `reviewer_name = escape(reviewer_name)`, `review_body = escape(review_body)`
5. `maker_weekly_digest_html` (line 158): `maker_name = escape(maker_name)`
6. `weekly_digest_html` (line 188): escape any user-supplied fields in the tools list — the function iterates tools, escape `t['name']` when used
7. `claim_tool_html` (line 361): `tool_name = escape(tool_name)`
8. `competitor_ping_html` (line 387): `maker_name = escape(maker_name)`, `new_tool_name = escape(new_tool_name)`, `category_name = escape(category_name)`
9. `subscriber_digest_html` (line 413): escape tool names from the `trending_tools` and `spotlight_tool` dicts when interpolated
10. `ego_ping_html` (line 502): `maker_name = escape(maker_name)`, `tool_name = escape(tool_name)`
11. `boost_expired_html` (line 575): `tool_name = escape(tool_name)`
12. `wishlist_update_html` (line 621): `user_name = escape(user_name)`, `tool_name = escape(tool_name)`, `update_title = escape(update_title)`
13. `maker_welcome_html` (line 647): `maker_name = escape(maker_name)`, `tool_name = escape(tool_name)`
14. `maker_stripe_nudge_html` (line 902): `tool_name = escape(tool_name)`
15. `tool_of_the_week_html` (line 957): `maker_name = escape(maker_name)`, `tool_name = escape(tool_name)`
16. `badge_nudge_html` (line 1062): `tool_name = escape(tool_name)`
17. `maker_launch_countdown_html` (line 1112): `maker_name = escape(maker_name)`
18. `launch_morning_maker_html` (line 1185): `maker_name = escape(maker_name)`, `tool_name = escape(tool_name)`

Pattern for simple cases — add at the top of the function body:
```python
def purchase_receipt_html(*, tool_name: str, amount: str, delivery_url: str) -> str:
    tool_name = escape(tool_name)
    ...existing code...
```

For functions that iterate lists (like `weekly_digest_html`, `subscriber_digest_html`), escape when accessing dict values:
```python
escape(tool.get('name', ''))
```

**Step 3: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/email.py').read())"`
Expected: No output

---

## Task 3: Auth + Payments + Pulse + Account Fixes

**Files:**
- Modify: `src/indiestack/auth.py`
- Modify: `src/indiestack/payments.py`
- Modify: `src/indiestack/routes/pulse.py`
- Modify: `src/indiestack/routes/account.py`

**Step 1: Fix default admin password (`auth.py:11`)**

Change:
```python
ADMIN_PASSWORD = os.environ.get("INDIESTACK_ADMIN_PASSWORD", "indiestack-dev-pw")
```
to:
```python
_raw_admin_pw = os.environ.get("INDIESTACK_ADMIN_PASSWORD", "")
if not _raw_admin_pw and os.environ.get("FLY_APP_NAME"):
    raise RuntimeError("INDIESTACK_ADMIN_PASSWORD must be set in production")
ADMIN_PASSWORD = _raw_admin_pw or "indiestack-dev-pw"
```

This crashes on startup in production (Fly.io sets `FLY_APP_NAME`) if the password isn't configured. Local dev keeps the default.

**Step 2: Guard empty Stripe webhook secret (`payments.py:87`)**

Change:
```python
def verify_webhook(payload: bytes, sig_header: str) -> dict:
    """Verify and parse a Stripe webhook event."""
    event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    return event
```
to:
```python
def verify_webhook(payload: bytes, sig_header: str) -> dict:
    """Verify and parse a Stripe webhook event."""
    if not STRIPE_WEBHOOK_SECRET:
        raise ValueError("STRIPE_WEBHOOK_SECRET not configured — cannot verify webhook")
    event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    return event
```

**Step 3: Fix pulse XSS (`pulse.py:43`)**

Change line 43:
```python
    tool_slug = event['tool_slug'] or ''
```
to:
```python
    tool_slug = escape(event['tool_slug'] or '')
```

`escape` is already imported at the top of `pulse.py`.

**Step 4: Fix OAuth redirect validation (`account.py`)**

Find where `next_url` is read from cookie (search for `oauth_next` or `next_url` cookie). Add validation that it starts with `/` and not `//`:

Search for the pattern where `next_url` is read from cookie after OAuth callback. Add:
```python
    next_url = request.cookies.get("oauth_next", "/dashboard")
    # Prevent open redirect
    if not next_url.startswith("/") or next_url.startswith("//"):
        next_url = "/dashboard"
```

**Step 5: Verify syntax on all 4 files**

Run:
```bash
python3 -c "import ast; ast.parse(open('src/indiestack/auth.py').read())" && \
python3 -c "import ast; ast.parse(open('src/indiestack/payments.py').read())" && \
python3 -c "import ast; ast.parse(open('src/indiestack/routes/pulse.py').read())" && \
python3 -c "import ast; ast.parse(open('src/indiestack/routes/account.py').read())"
```
Expected: No output

---

## Task 4: CSRF + CSP + Security Hardening (`main.py`)

**Files:**
- Modify: `src/indiestack/main.py`

**Step 1: Add CSRF token generation to security headers middleware**

Find the `security_headers` middleware (line 435). Modify it to also set a CSRF cookie if not present:

```python
@app.middleware("http")
async def security_headers(request: Request, call_next):
    # Generate CSRF token if not in cookie
    csrf_token = request.cookies.get("indiestack_csrf", "")
    if not csrf_token:
        import secrets as _csrf_secrets
        csrf_token = _csrf_secrets.token_urlsafe(32)
    request.state.csrf_token = csrf_token

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; img-src 'self' https: data:; font-src 'self' https://fonts.gstatic.com; connect-src 'self'; frame-src https://www.youtube.com https://player.vimeo.com"

    # Set CSRF cookie if not present (httponly=False so JS can read it)
    if not request.cookies.get("indiestack_csrf"):
        response.set_cookie(
            "indiestack_csrf", csrf_token,
            httponly=False, samesite="lax", secure=True, max_age=86400 * 30, path="/"
        )
    return response
```

**Step 2: Add CSRF validation to csrf_protection middleware**

Update the `csrf_protection` middleware (line 412) to also validate the CSRF token on POST/PUT/DELETE/PATCH:

```python
_CSRF_EXEMPT_PATHS = {"/webhooks/stripe", "/api/cite", "/api/tools/submit", "/api/follow-through"}
_ALLOWED_ORIGINS = {"https://indiestack.fly.dev", "https://www.indiestack.fly.dev", "http://localhost:8000", "http://127.0.0.1:8000"}


@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    """Block cross-origin POST/PUT/DELETE requests (CSRF protection via Origin header + Double Submit Cookie)."""
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        path = request.url.path
        if path not in _CSRF_EXEMPT_PATHS:
            # 1. Origin/Referer check
            origin = request.headers.get("origin", "")
            if not origin:
                referer = request.headers.get("referer", "")
                if referer:
                    from urllib.parse import urlparse
                    parsed = urlparse(referer)
                    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""

            if origin and origin not in _ALLOWED_ORIGINS:
                return JSONResponse({"error": "Cross-origin request blocked"}, status_code=403)

            # 2. Block requests with no origin AND no referer (tightened)
            if not origin:
                return JSONResponse({"error": "Missing origin header"}, status_code=403)

            # 3. Double Submit Cookie CSRF check
            cookie_token = request.cookies.get("indiestack_csrf", "")
            if cookie_token:
                # Check form field first, then header
                form_token = ""
                header_token = request.headers.get("x-csrf-token", "")
                content_type = request.headers.get("content-type", "")
                if "form" in content_type or "urlencoded" in content_type:
                    try:
                        form = await request.form()
                        form_token = form.get("csrf_token", "")
                    except Exception:
                        pass
                submitted_token = header_token or form_token
                if not submitted_token:
                    return JSONResponse({"error": "Missing CSRF token"}, status_code=403)
                import secrets as _csrf_secrets
                if not _csrf_secrets.compare_digest(cookie_token, submitted_token):
                    return JSONResponse({"error": "Invalid CSRF token"}, status_code=403)

    response = await call_next(request)
    return response
```

WAIT — there is a problem with reading `request.form()` in middleware. FastAPI/Starlette only allows the body to be read once. If we read `form()` in middleware, the route handler can't read it again.

Alternative approach: DON'T read form body in middleware. Only check the `X-CSRF-Token` header. The auto-inject JS will send the token as a header for fetch() calls, and for `<form>` submissions, it adds a hidden field. But we can't read the hidden field in middleware without consuming the body.

**Revised approach:** Use the `X-CSRF-Token` header for ALL requests (forms and AJAX). The auto-inject JS in `page_shell()` will:
- For forms: intercept submit events and add the header
- For fetch: override fetch to add the header

Actually, forms don't send custom headers. The simplest reliable approach:

**Final approach:** For `<form>` submissions, the JS auto-injects a hidden input field. The CSRF check happens in a **dependency** function, not middleware, so the body can still be read by the route. For AJAX/fetch, the JS overrides fetch to add an `X-CSRF-Token` header, and we check that in middleware.

Simplified middleware — only check the header:

```python
@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    """CSRF protection: Origin check + Double Submit Cookie via X-CSRF-Token header."""
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        path = request.url.path
        if path not in _CSRF_EXEMPT_PATHS:
            # Origin/Referer check
            origin = request.headers.get("origin", "")
            if not origin:
                referer = request.headers.get("referer", "")
                if referer:
                    from urllib.parse import urlparse
                    parsed = urlparse(referer)
                    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""
            if origin and origin not in _ALLOWED_ORIGINS:
                return JSONResponse({"error": "Cross-origin request blocked"}, status_code=403)
            # Block requests with no origin AND no referer
            if not origin:
                return JSONResponse({"error": "Missing origin header"}, status_code=403)

    response = await call_next(request)
    return response
```

Then add a separate utility function for route-level CSRF validation:

```python
async def verify_csrf(request: Request):
    """Verify CSRF token from form field or header against cookie. Call in POST route handlers."""
    cookie_token = request.cookies.get("indiestack_csrf", "")
    if not cookie_token:
        return  # No cookie = no protection possible, origin check handles it
    # Check header first (fetch/AJAX)
    submitted = request.headers.get("x-csrf-token", "")
    # Check form field (HTML forms) — only if header not present
    if not submitted:
        content_type = request.headers.get("content-type", "")
        if "form" in content_type or "urlencoded" in content_type:
            try:
                form = await request.form()
                submitted = form.get("csrf_token", "")
            except Exception:
                pass
    if submitted and not secrets.compare_digest(cookie_token, submitted):
        from fastapi.responses import JSONResponse
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
```

Actually, this gets complicated because `request.form()` can only be called once. If the middleware calls it, the route can't.

**FINAL SIMPLIFIED APPROACH: Origin-only + SameSite=lax**

After further analysis, the cleanest pre-launch approach is:
1. **Tighten origin check** to block no-origin requests (close the gap)
2. **Keep SameSite=lax** on session cookies (already set — blocks cross-origin form POSTs in modern browsers)
3. **Add CSP** for defense-in-depth
4. **Skip Double Submit Cookie** for now — origin check + SameSite=lax provides strong protection

This avoids the form body double-read problem entirely. We can add proper CSRF tokens post-launch when we can test thoroughly.

**Step 2 (revised): Tighten origin check only**

Change the csrf_protection middleware:

```python
_CSRF_EXEMPT_PATHS = {"/webhooks/stripe", "/api/cite", "/api/tools/submit", "/api/follow-through"}
_ALLOWED_ORIGINS = {"https://indiestack.fly.dev", "https://www.indiestack.fly.dev", "http://localhost:8000", "http://127.0.0.1:8000"}


@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    """Block cross-origin POST/PUT/DELETE requests via Origin/Referer validation."""
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        path = request.url.path
        if path not in _CSRF_EXEMPT_PATHS:
            origin = request.headers.get("origin", "")
            if not origin:
                referer = request.headers.get("referer", "")
                if referer:
                    from urllib.parse import urlparse
                    parsed = urlparse(referer)
                    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""

            if not origin:
                # No origin AND no referer — block the request
                return JSONResponse({"error": "Origin required"}, status_code=403)

            if origin not in _ALLOWED_ORIGINS:
                return JSONResponse({"error": "Cross-origin request blocked"}, status_code=403)
    response = await call_next(request)
    return response
```

Key change: `if not origin: return 403` instead of falling through.

**Step 3: Add CSP header**

In the `security_headers` middleware, add after the existing headers:

```python
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' https: data:; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self'; "
        "frame-src https://www.youtube.com https://player.vimeo.com"
    )
```

**Step 4: Add admin login rate limiter**

Add at module level near the top of main.py (after imports):

```python
# ── Admin Login Rate Limiting ────────────────────────────────────────────
import time as _time

_admin_login_attempts = {}  # {ip: [timestamp, ...]}
_ADMIN_LOGIN_MAX = 5
_ADMIN_LOGIN_WINDOW = 900  # 15 minutes


def _check_admin_rate_limit(ip: str) -> bool:
    """Return True if IP is rate-limited for admin login."""
    now = _time.time()
    attempts = _admin_login_attempts.get(ip, [])
    # Prune old attempts
    attempts = [t for t in attempts if now - t < _ADMIN_LOGIN_WINDOW]
    _admin_login_attempts[ip] = attempts
    return len(attempts) >= _ADMIN_LOGIN_MAX


def _record_admin_attempt(ip: str):
    """Record a failed admin login attempt."""
    now = _time.time()
    attempts = _admin_login_attempts.get(ip, [])
    attempts.append(now)
    _admin_login_attempts[ip] = attempts


def _clear_admin_attempts(ip: str):
    """Clear rate limit on successful login."""
    _admin_login_attempts.pop(ip, None)
```

Then find the admin login POST handler and add rate limit check:
- Before checking password: `if _check_admin_rate_limit(client_ip): return JSONResponse({"error": "Too many attempts"}, 429)`
- On failed login: `_record_admin_attempt(client_ip)`
- On successful login: `_clear_admin_attempts(client_ip)`

Find the admin POST handler — it should be in `admin.py`, not `main.py`. Check which file handles `POST /admin` for login.

**Step 5: Add sitemap LIMIT**

Find the sitemap route (line 747). In the SQL queries that fetch all tools and makers, add `LIMIT 5000`.

**Step 6: Add URL validation on tool submission**

Find the tool submission API handler (`POST /api/tools/submit`, line 1812). Add after extracting the URL:

```python
    # Validate URL
    url = url.strip()
    if url and not (url.startswith("http://") or url.startswith("https://")):
        return JSONResponse({"error": "URL must start with http:// or https://"}, status_code=400)
```

**Step 7: Cap tool_slug length on subscribe**

Find the subscribe handler (line 957). After extracting `tool_slug`, add:

```python
    tool_slug = tool_slug[:200]
```

**Step 8: Sanitize error responses**

Find the 500 error handler or generic exception handler. Ensure it returns a generic message:

```python
    return JSONResponse({"error": "Internal server error"}, status_code=500)
```

Not the actual exception message.

**Step 9: Add logging to background tasks**

Find background task try/except blocks (search for `except Exception` in background tasks). Add `import logging; logger = logging.getLogger(__name__)` at top, then `logger.exception("Background task failed")` in catch blocks.

**Step 10: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read())"`
Expected: No output

---

## Task 5: Landing XSS Fix + Components Security (`landing.py` + `components.py`)

**Files:**
- Modify: `src/indiestack/routes/landing.py`
- Modify: `src/indiestack/routes/components.py`

**Step 1: Fix landing search innerHTML XSS (`landing.py:488-496`)**

Find the search results JS (around line 478). Add an `esc()` function before `doSearch`:

```javascript
function esc(s){if(!s)return '';var d=document.createElement('div');d.textContent=s;return d.innerHTML;}
```

Then change the innerHTML template (lines 495-496) from:
```javascript
'<div style="font-family:var(--font-display);font-size:16px;color:var(--ink);">'+t.name+'</div>'+
'<div style="font-size:13px;color:var(--ink-muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'+t.tagline+'</div>'+
```
to:
```javascript
'<div style="font-family:var(--font-display);font-size:16px;color:var(--ink);">'+esc(t.name)+'</div>'+
'<div style="font-size:13px;color:var(--ink-muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'+esc(t.tagline)+'</div>'+
```

Also escape `t.price`:
```javascript
'<span style="font-size:13px;font-weight:600;color:var(--ink-light);white-space:nowrap;">'+esc(t.price)+'</span>'+
```

**Step 2: Verify syntax**

Run:
```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/landing.py').read())" && \
python3 -c "import ast; ast.parse(open('src/indiestack/routes/components.py').read())"
```
Expected: No output

---

## Task 6: MCP + Admin Outreach Hardening

**Files:**
- Modify: `src/indiestack/mcp_server.py`
- Modify: `src/indiestack/routes/admin_outreach.py`

**Step 1: Add input validation to MCP server**

Find `publish_tool` function (around line 591). Add validation after extracting arguments:

```python
    # Input validation
    name = str(arguments.get("name", ""))[:200]
    tagline = str(arguments.get("tagline", ""))[:500]
    description = str(arguments.get("description", ""))[:5000]
    url = str(arguments.get("url", "")).strip()
    if url and not (url.startswith("http://") or url.startswith("https://")):
        raise ToolError("URL must start with http:// or https://")
```

Add limit clamping to all tools that accept a `limit` parameter. Find functions like `find_tools`, `browse_new_tools`, etc. and add:

```python
    limit = min(int(arguments.get("limit", 20)), 50)
```

**Step 2: Add rate limiting to publish_tool**

Add at module level:
```python
_publish_rate = {}  # {session_key: [timestamps]}
_PUBLISH_MAX = 10
_PUBLISH_WINDOW = 3600  # 1 hour
```

In `publish_tool`, before processing:
```python
    # Rate limit
    session_key = str(arguments.get("api_key", "anonymous"))
    now = __import__('time').time()
    attempts = _publish_rate.get(session_key, [])
    attempts = [t for t in attempts if now - t < _PUBLISH_WINDOW]
    if len(attempts) >= _PUBLISH_MAX:
        raise ToolError("Rate limit: max 10 submissions per hour")
    attempts.append(now)
    _publish_rate[session_key] = attempts
```

**Step 3: Add email blast rate limiting (`admin_outreach.py`)**

Find the email blast sending loop. Add `import time` at top if not present, then add a delay between sends:

```python
    time.sleep(1)  # Rate limit: 1 email per second to avoid Gmail throttling
```

Add this inside the loop that sends emails, after each `send_email()` call.

**Step 4: Verify syntax**

Run:
```bash
python3 -c "import ast; ast.parse(open('src/indiestack/mcp_server.py').read())" && \
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin_outreach.py').read())"
```
Expected: No output

---

## Task 7: Smoke Test + Deploy

**Depends on:** Tasks 1-6 complete

**Step 1: Pre-flight syntax check on ALL modified files**

```bash
python3 -c "
import ast, sys
files = [
    'src/indiestack/db.py',
    'src/indiestack/email.py',
    'src/indiestack/auth.py',
    'src/indiestack/payments.py',
    'src/indiestack/main.py',
    'src/indiestack/mcp_server.py',
    'src/indiestack/routes/landing.py',
    'src/indiestack/routes/pulse.py',
    'src/indiestack/routes/account.py',
    'src/indiestack/routes/components.py',
    'src/indiestack/routes/admin_outreach.py',
]
for f in files:
    try:
        ast.parse(open(f).read())
    except SyntaxError as e:
        print(f'SYNTAX ERROR in {f}: {e}')
        sys.exit(1)
print('All files parse OK')
"
```
Expected: "All files parse OK"

**Step 2: Run smoke test**

Run: `cd /home/patty/indiestack && python3 smoke_test.py`
Expected: All tests pass

**Step 3: Deploy**

Run: `cd /home/patty/indiestack && FLY_ACCESS_TOKEN=$(grep access_token ~/.fly/config.yml | awk '{print $2}') ~/.fly/bin/flyctl deploy --remote-only`

**Step 4: Verify**

Quick checks after deploy:
- Visit https://indiestack.fly.dev/ — page loads
- Visit https://indiestack.fly.dev/admin — login form works
- Visit https://indiestack.fly.dev/explore — search works
- Check response headers for CSP

---

## Execution Summary

| Task | What | Files | Independent? |
|------|------|-------|-------------|
| 1 | SQL injection + DB hardening | db.py | Yes |
| 2 | Email HTML escaping | email.py | Yes |
| 3 | Auth + payments + pulse + account fixes | auth.py, payments.py, pulse.py, account.py | Yes |
| 4 | CSRF origin + CSP + rate limiting + misc | main.py | Yes |
| 5 | Landing XSS fix | landing.py, components.py | Yes |
| 6 | MCP + admin outreach hardening | mcp_server.py, admin_outreach.py | Yes |
| 7 | Smoke test + deploy | — | Needs 1-6 |

Tasks 1-6 are fully independent (different files) and can run in parallel.

**Note on CSRF:** Full Double Submit Cookie CSRF tokens were descoped from this plan due to the request.form() double-read issue in Starlette middleware. The tightened origin check (blocking no-origin requests) + SameSite=lax cookies provides strong CSRF protection. CSRF tokens via form fields can be added post-launch with a proper FastAPI dependency approach.

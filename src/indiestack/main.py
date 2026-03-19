"""FastAPI app, middleware, router wiring, upvote API."""

import asyncio
import hashlib
import logging
import json as _json
import os as _os
import re
import time as _time
from contextlib import asynccontextmanager
from datetime import date

_logger = logging.getLogger("indiestack")


def _alert_telegram(task_name: str, error: str):
    """Send error alert to Patrick via Telegram (fire-and-forget)."""
    import subprocess
    msg = f"IndieStack BG task FAILED: {task_name}\n{error[:200]}"
    try:
        subprocess.Popen(
            ["bash", "/home/patty/.claude/telegram.sh", msg],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass


from indiestack.config import BASE_URL

from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, Response
from starlette.middleware.gzip import GZipMiddleware

# Rate limiting
_rate_limits: dict[str, list[float]] = {}
_rate_check_counter = 0

# Agent action daily rate limits (per API key per day)
_AGENT_ACTION_LIMITS = {
    "recommend": 50,
    "shortlist": 100,
    "report_outcome": 20,
    "confirm_integration": 10,
    "submit_tool": 3,
}


def _require_scope(api_key: dict | None, scope: str) -> dict:
    """Validate API key exists. Scope parameter kept for backwards compat but no longer enforced."""
    if not api_key:
        raise HTTPException(status_code=401, detail="API key required. Get one at https://indiestack.ai/developer")
    return api_key


def _check_rate_limit(ip: str, path: str, method: str) -> bool:
    """Returns True if request should be blocked (rate limited)."""
    global _rate_check_counter
    _rate_check_counter += 1

    # Cleanup every 100 requests
    if _rate_check_counter % 100 == 0:
        now = _time.time()
        expired_keys = [k for k, v in _rate_limits.items() if all(t < now - 60 for t in v)]
        for k in expired_keys:
            del _rate_limits[k]

    # Rate limit GET for auth and email-sending endpoints, POST for everything else
    get_limited = {"/resend-verification", "/signup", "/login", "/auth/github", "/auth/github/callback", "/auth/magic"}
    if method == "GET" and path not in get_limited:
        return False
    if method not in ("POST", "GET"):
        return False

    limits = {
        "/login": 10,
        "/signup": 10,
        "/auth/github": 10,
        "/auth/github/callback": 10,
        "/submit": 3,
        "/forgot-password": 3,
        "/auth/magic": 3,
        "/resend-verification": 3,
        "/admin": 60,
        "/api/upvote": 10,
        "/api/wishlist": 10,
        "/api/subscribe": 5,
        "/api/claim": 5,
        "/api/tools/submit": 3,
    }

    # Check specific path limits
    max_requests = None
    if path in limits:
        max_requests = limits[path]
    elif path.startswith("/api/"):
        max_requests = 30
    elif path.startswith("/tool/") and method == "POST":
        max_requests = 5

    if max_requests is None:
        return False

    key = f"{ip}:{path}"
    now = _time.time()

    if key not in _rate_limits:
        _rate_limits[key] = []

    # Remove entries older than 60 seconds
    _rate_limits[key] = [t for t in _rate_limits[key] if t > now - 60]

    if len(_rate_limits[key]) >= max_requests:
        return True

    _rate_limits[key].append(now)
    return False

# ── API Rate Limiting ─────────────────────────────────────────────────────
_api_user_monthly: dict[int, dict] = {}  # {user_id: {"month": "YYYY-MM", "count": N}}
_api_ip_daily: dict[str, dict] = {}  # {ip: {"date": "YYYY-MM-DD", "count": N}}

API_MONTHLY_LIMITS = {
    "free": 10,
    "pro": 1000,
}
API_KEYLESS_DAILY_LIMIT = 3


def _check_api_key_rate_limit(user_id: int, tier: str) -> bool:
    """Returns True if user has exceeded their monthly API limit.

    Rate-limits by user_id (not key_id) so revoking and regenerating
    keys cannot bypass the cap. Free tier: 10/month, Pro: 1,000/month.
    """
    from datetime import date
    this_month = date.today().strftime("%Y-%m")
    entry = _api_user_monthly.get(user_id)
    if not entry or entry["month"] != this_month:
        # Clean up stale entries from previous months (prevent memory leak)
        if len(_api_user_monthly) > 200:
            _api_user_monthly.clear()
        _api_user_monthly[user_id] = {"month": this_month, "count": 1}
        return False
    limit = API_MONTHLY_LIMITS.get(tier, 10)
    if entry["count"] >= limit:
        return True
    entry["count"] += 1
    return False


def _check_api_ip_rate_limit(ip: str) -> bool:
    """Returns True if keyless IP has exceeded its daily API limit (3/day)."""
    from datetime import date
    today = date.today().isoformat()
    entry = _api_ip_daily.get(ip)
    if not entry or entry["date"] != today:
        if len(_api_ip_daily) > 500:
            _api_ip_daily.clear()
        _api_ip_daily[ip] = {"date": today, "count": 1}
        return False
    if entry["count"] >= API_KEYLESS_DAILY_LIMIT:
        return True
    entry["count"] += 1
    return False


# ── Admin Login Rate Limiting ────────────────────────────────────────────
_admin_login_attempts = {}  # {ip: [timestamp, ...]}
_ADMIN_LOGIN_MAX = 5
_ADMIN_LOGIN_WINDOW = 900  # 15 minutes


def _check_admin_rate_limit(ip: str) -> bool:
    """Return True if IP is rate-limited for admin login."""
    import time as _rl_time
    now = _rl_time.time()
    attempts = _admin_login_attempts.get(ip, [])
    attempts = [t for t in attempts if now - t < _ADMIN_LOGIN_WINDOW]
    _admin_login_attempts[ip] = attempts
    return len(attempts) >= _ADMIN_LOGIN_MAX


def _record_admin_attempt(ip: str):
    """Record a failed admin login attempt."""
    import time as _rl_time
    _admin_login_attempts.setdefault(ip, []).append(_rl_time.time())


def _clear_admin_attempts(ip: str):
    """Clear rate limit on successful login."""
    _admin_login_attempts.pop(ip, None)


_sitemap_cache: dict[str, object] = {'xml': None, 'expires': 0}

_LOGO_CANDIDATES = [
    Path(__file__).resolve().parent.parent.parent / "logo" / "indiestack.png",
    Path("/app/logo/indiestack.png"),
]
_logo_bytes: bytes | None = None

_FOUNDER_PHOTO_DIR_CANDIDATES = [
    Path(__file__).resolve().parent.parent.parent / "founder-photos",
    Path("/app/founder-photos"),
]
_founder_photo_cache: dict[str, bytes] = {}

from indiestack import db
from indiestack.db import CATEGORY_TOKEN_COSTS, NEED_MAPPINGS, get_user_by_badge_token, get_buyer_tokens_saved_by_token, cleanup_expired_sessions, cleanup_old_page_views, get_makers_for_ego_ping, create_notification, record_tool_pair
from indiestack.email import send_email, ego_ping_html, maker_welcome_html, email_verification_html
from indiestack.auth import get_current_user
from indiestack.routes import landing, browse, tool, search, submit, admin, purchase
from indiestack.routes import maker, collections, compare, new, account, dashboard, pricing, updates, alternatives
from indiestack.routes import stacks
from indiestack.routes import explore, tags

from indiestack.routes.calculator import router as calculator_router
from indiestack.routes import built_this
from indiestack.routes import stripe_guide, launch
from indiestack.routes import embed
from indiestack.routes import launch_with_me
from indiestack.routes import use_cases
from indiestack.routes import why_list
from indiestack.routes import what_is
from indiestack.routes import plugins
from indiestack.routes import gaps
from indiestack.routes import api_docs
from indiestack.routes import geo
from indiestack.routes import changelog
from indiestack.routes import guidelines
from indiestack.routes import audit


async def _periodic_health_refresh():
    """Run health checks every 4 hours to keep tool data fresh."""
    import aiosqlite
    await asyncio.sleep(300)  # First run 5 min after startup
    while True:
        try:
            async with aiosqlite.connect(db.DB_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                # HTTP HEAD checks on tool URLs (batch of 100)
                await db.run_health_checks(conn, batch_size=100)
                # GitHub API checks for stars, commits, archive status (batch of 50)
                await db.run_github_health_checks(conn, batch_size=50)
                # Recompute quality scores with fresh health data
                await db.recompute_all_quality_scores(conn)
        except Exception as e:
            _logger.exception("Background task failed: health refresh")
            _alert_telegram("health_refresh", str(e))
        await asyncio.sleep(4 * 3600)  # Then every 4 hours


async def _periodic_session_cleanup():
    """Run session cleanup every hour."""
    import aiosqlite
    while True:
        await asyncio.sleep(3600)
        try:
            async with aiosqlite.connect(db.DB_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                await cleanup_expired_sessions(conn)
                await cleanup_old_page_views(conn)
        except Exception:
            _logger.exception("Background task failed: session cleanup")


async def _weekly_ego_ping():
    """Send ego ping emails every Friday."""
    import aiosqlite
    from datetime import datetime, timezone
    while True:
        await asyncio.sleep(86400)  # Check daily
        if datetime.now(timezone.utc).weekday() != 4:  # 4 = Friday
            continue
        try:
            async with aiosqlite.connect(db.DB_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                makers = await get_makers_for_ego_ping(conn)
                for m in makers:
                    # Dashboard notification instead of email
                    try:
                        cursor = await conn.execute(
                            "SELECT id FROM users WHERE maker_id = ?",
                            (m['maker_id'],))
                        user_row = await cursor.fetchone()
                        if user_row:
                            views = m['weekly_views']
                            clicks = m.get('weekly_clicks', 0)
                            citations = m.get('weekly_citations', 0)
                            parts = [f"{views} views", f"{clicks} clicks"]
                            if citations > 0:
                                parts.append(f"{citations} AI recommendations")
                            await create_notification(
                                conn, user_row['id'], 'weekly_stats',
                                f"{m['tool_name']}: {', '.join(parts)} this week",
                                f"/tool/{m['tool_slug']}"
                            )
                    except Exception:
                        pass
        except Exception as e:
            _logger.exception("Background task failed: weekly ego ping")
            _alert_telegram("ego ping", str(e))


async def _auto_tool_of_the_week():
    """Auto-select Tool of the Week every Monday based on outbound clicks."""
    import aiosqlite
    from datetime import datetime
    import logging
    logger = logging.getLogger("indiestack")
    while True:
        await asyncio.sleep(86400)
        if datetime.now().weekday() != 0:  # 0 = Monday
            continue
        try:
            async with aiosqlite.connect(db.DB_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                row = await conn.execute_fetchall(
                    """SELECT t.id, t.name, t.slug, t.maker_name, t.maker_id,
                              (COALESCE(sl.cnt, 0) + COALESCE(ac.cnt, 0)) as mentions
                       FROM tools t
                       LEFT JOIN (
                           SELECT top_result_slug, COUNT(*) as cnt FROM search_logs
                           WHERE created_at >= datetime('now', '-7 days')
                             AND top_result_slug IS NOT NULL
                           GROUP BY top_result_slug
                       ) sl ON sl.top_result_slug = t.slug
                       LEFT JOIN (
                           SELECT tool_id, COUNT(*) as cnt FROM agent_citations
                           WHERE created_at >= datetime('now', '-7 days')
                           GROUP BY tool_id
                       ) ac ON ac.tool_id = t.id
                       WHERE t.status = 'approved'
                         AND (COALESCE(sl.cnt, 0) + COALESCE(ac.cnt, 0)) > 0
                       ORDER BY mentions DESC
                       LIMIT 1"""
                )
                if not row:
                    continue
                tool = dict(row[0])
                clicks = tool['mentions']
                await conn.execute("UPDATE tools SET tool_of_the_week = 0 WHERE tool_of_the_week = 1")
                await conn.execute("UPDATE tools SET tool_of_the_week = 1 WHERE id = ?", (tool['id'],))
                await conn.commit()
                # Try to email the maker
                try:
                    maker_email = None
                    if tool.get('maker_id'):
                        maker_row = await conn.execute_fetchall(
                            "SELECT u.email FROM users u WHERE u.maker_id = ? AND COALESCE(u.email_opt_out, 0) = 0", (tool['maker_id'],)
                        )
                        if maker_row and maker_row[0]['email']:
                            maker_email = maker_row[0]['email']
                    if maker_email:
                        from indiestack.email import tool_of_the_week_html
                        badge_url = f"{BASE_URL}/api/badge/{tool['slug']}.svg?style=winner"
                        tool_url = f"{BASE_URL}/tool/{tool['slug']}"
                        html = tool_of_the_week_html(
                            maker_name=tool['maker_name'] or "Maker",
                            tool_name=tool['name'],
                            tool_slug=tool['slug'],
                            clicks=clicks,
                            badge_url=badge_url,
                            tool_url=tool_url,
                        )
                        await send_email(maker_email, f"Your tool is Tool of the Week!", html)
                except Exception:
                    pass
                logger.info(f"Auto TOTW: {tool['name']} ({clicks} AI mentions this week)")
        except Exception as e:
            _logger.exception("Background task failed: auto TOTW")
            _alert_telegram("TOTW selection", str(e))


async def _badge_nudge_check():
    """Send badge nudge emails to tools approved 48-72 hours ago."""
    import aiosqlite
    import logging
    logger = logging.getLogger("indiestack")
    while True:
        await asyncio.sleep(86400)
        try:
            async with aiosqlite.connect(db.DB_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                rows = await conn.execute_fetchall(
                    """SELECT t.id, t.name, t.slug, t.maker_id
                       FROM tools t
                       WHERE t.status = 'approved'
                       AND t.badge_nudge_sent = 0
                       AND t.created_at <= datetime('now', '-2 days')
                       AND t.created_at >= datetime('now', '-3 days')"""
                )
                for tool in rows:
                    tool = dict(tool)
                    # Dashboard notification instead of email
                    if tool.get('maker_id'):
                        try:
                            cursor = await conn.execute(
                                "SELECT id FROM users WHERE maker_id = ?",
                                (tool['maker_id'],))
                            user_row = await cursor.fetchone()
                            if user_row:
                                await create_notification(
                                    conn, user_row['id'], 'badge',
                                    f"Your badge for {tool['name']} is ready — embed it on your site!",
                                    f"/tool/{tool['slug']}#badge"
                                )
                                logger.info(f"Badge nudge notification for {tool['name']}")
                        except Exception:
                            pass
                    await conn.execute("UPDATE tools SET badge_nudge_sent = 1 WHERE id = ?", (tool['id'],))
                await conn.commit()
        except Exception as e:
            _logger.exception("Background task failed: badge nudge")
            _alert_telegram("badge nudge", str(e))


async def _auto_weekly_digest():
    """Send weekly digest emails every Friday."""
    import aiosqlite
    from datetime import datetime
    import logging
    logger = logging.getLogger("indiestack")
    while True:
        await asyncio.sleep(86400)
        if datetime.now().weekday() != 4:  # 4 = Friday
            continue
        try:
            async with aiosqlite.connect(db.DB_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                # Gather stats
                new_count_row = await conn.execute_fetchall(
                    "SELECT COUNT(*) as cnt FROM tools WHERE created_at >= datetime('now', '-7 days') AND status = 'approved'"
                )
                total_tools_row = await conn.execute_fetchall(
                    "SELECT COUNT(*) as cnt FROM tools WHERE status = 'approved'"
                )
                total_makers_row = await conn.execute_fetchall(
                    "SELECT COUNT(*) as cnt FROM makers"
                )
                subscribers = await conn.execute_fetchall(
                    "SELECT email, unsubscribe_token FROM subscribers"
                )
                subscriber_count = len(subscribers)
                totw_row = await conn.execute_fetchall(
                    "SELECT name, slug FROM tools WHERE tool_of_the_week = 1 LIMIT 1"
                )
                top_clicked = await conn.execute_fetchall(
                    """SELECT t.name, t.slug, COUNT(oc.id) as clicks
                       FROM tools t
                       JOIN outbound_clicks oc ON oc.tool_id = t.id
                       WHERE oc.created_at >= datetime('now', '-7 days')
                       GROUP BY t.id
                       ORDER BY clicks DESC
                       LIMIT 5"""
                )
                new_tools = await conn.execute_fetchall(
                    """SELECT name, slug, tagline
                       FROM tools
                       WHERE created_at >= datetime('now', '-7 days') AND status = 'approved'
                       ORDER BY created_at DESC
                       LIMIT 5"""
                )
                top_searched = await conn.execute_fetchall(
                    """SELECT query, COUNT(*) as cnt
                       FROM search_logs
                       WHERE created_at >= datetime('now', '-7 days')
                       GROUP BY query
                       ORDER BY cnt DESC
                       LIMIT 5"""
                )

                total_tools = total_tools_row[0]['cnt'] if total_tools_row else 0
                total_makers = total_makers_row[0]['cnt'] if total_makers_row else 0
                totw_name = totw_row[0]['name'] if totw_row else None
                totw_slug = totw_row[0]['slug'] if totw_row else None
                totw_clicks = 0
                if totw_slug:
                    tc_row = await conn.execute_fetchall(
                        """SELECT COUNT(*) as cnt FROM outbound_clicks oc
                           JOIN tools t ON oc.tool_id = t.id
                           WHERE t.slug = ? AND oc.created_at >= datetime('now', '-7 days')""",
                        (totw_slug,)
                    )
                    totw_clicks = tc_row[0]['cnt'] if tc_row else 0

                new_tools_list = [dict(r) for r in new_tools]
                top_clicked_list = [dict(r) for r in top_clicked]
                top_searched_list = [r['query'] for r in top_searched]

                from datetime import date
                week_label = f"Week of {date.today().strftime('%B %d, %Y')}"

                from indiestack.email import weekly_digest_html
                sent = 0
                for sub in subscribers:
                    unsub_url = f"{BASE_URL}/unsubscribe/{sub['unsubscribe_token']}"
                    html = weekly_digest_html(
                        week_label=week_label,
                        new_tools=new_tools_list,
                        top_clicked=top_clicked_list,
                        top_searched=top_searched_list,
                        totw_name=totw_name,
                        totw_slug=totw_slug,
                        totw_clicks=totw_clicks,
                        total_tools=total_tools,
                        total_makers=total_makers,
                        subscriber_count=subscriber_count,
                        unsubscribe_url=unsub_url,
                    )
                    await send_email(sub['email'], f"IndieStack Weekly \u2014 {week_label}", html, unsubscribe_url=unsub_url)
                    sent += 1
                logger.info(f"Auto digest sent to {sent} subscribers")
        except Exception as e:
            _logger.exception("Background task failed: weekly digest")
            _alert_telegram("weekly digest", str(e))


async def _weekly_pair_generator():
    """Regenerate tool compatibility pairs every Sunday."""
    await asyncio.sleep(600)  # Wait for app to fully start
    while True:
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            if now.weekday() == 6 and now.hour == 6:  # Sunday 6am UTC
                import subprocess
                result = subprocess.run(
                    ["python3", "-m", "indiestack.pair_generator", "--apply"],
                    capture_output=True, text=True, timeout=300,
                    cwd="/app",
                )
                if result.returncode == 0:
                    _logger.info(f"Pair generator completed: {result.stdout[-200:]}")
                else:
                    _logger.error(f"Pair generator failed: {result.stderr[-200:]}")
                    _alert_telegram("pair_generator", result.stderr[-200:])
        except Exception as e:
            _logger.exception("Background task failed: pair generator")
            _alert_telegram("pair_generator", str(e))
        await asyncio.sleep(3600)  # Check every hour


async def _weekly_citation_alert():
    """Send citation alert emails to makers every Wednesday."""
    await asyncio.sleep(120)  # Wait for app to fully start
    while True:
        try:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            if now.weekday() == 2 and now.hour == 10:  # Wednesday 10am UTC
                import aiosqlite
                from indiestack.db import get_weekly_citation_digest, check_pro
                from indiestack.email import send_email, citation_alert_html
                async with aiosqlite.connect(db.DB_PATH) as conn:
                    conn.row_factory = aiosqlite.Row
                    digests = await get_weekly_citation_digest(conn, days=7)
                    sent = 0
                    for d in digests:
                        if d['citation_count'] == 0:
                            continue
                        is_pro = await check_pro(conn, d['user_id'])
                        agent_list = d['agent_names'].split(',') if d['agent_names'] else []
                        try:
                            html = citation_alert_html(
                                maker_name=d['maker_name'],
                                tool_name=d['tool_name'],
                                tool_slug=d['tool_slug'],
                                citation_count=d['citation_count'],
                                agent_names=agent_list,
                                is_pro=is_pro,
                                sample_context=d['sample_context'] or "",
                            )
                            await send_email(
                                to=d['maker_email'],
                                subject=f"AI agents cited {d['tool_name']} {d['citation_count']} times this week",
                                html_body=html,
                            )
                            sent += 1
                        except Exception as email_err:
                            _logger.error(f"Citation email failed for {d.get('maker_email', '?')}: {email_err}")
                    if sent:
                        _logger.info(f"Sent {sent} citation alert emails")
        except Exception as e:
            _logger.exception("Background task failed: citation alert")
            _alert_telegram("citation alert", str(e))
        await asyncio.sleep(3600)  # Check every hour


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    # Run cleanup on startup
    try:
        import aiosqlite
        async with aiosqlite.connect(db.DB_PATH) as conn:
            conn.row_factory = aiosqlite.Row
            await cleanup_expired_sessions(conn)
            await cleanup_old_page_views(conn)
    except Exception:
        pass
    # Start periodic cleanup task
    cleanup_task = asyncio.create_task(_periodic_session_cleanup())
    ego_ping_task = asyncio.create_task(_weekly_ego_ping())
    totw_task = asyncio.create_task(_auto_tool_of_the_week())
    nudge_task = asyncio.create_task(_badge_nudge_check())
    digest_task = asyncio.create_task(_auto_weekly_digest())
    citation_task = asyncio.create_task(_weekly_citation_alert())
    pairs_task = asyncio.create_task(_weekly_pair_generator())
    health_task = asyncio.create_task(_periodic_health_refresh())
    yield
    cleanup_task.cancel()
    ego_ping_task.cancel()
    totw_task.cancel()
    nudge_task.cancel()
    digest_task.cancel()
    citation_task.cancel()
    pairs_task.cancel()
    health_task.cancel()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

# ── Compression ──────────────────────────────────────────────────────────
app.add_middleware(GZipMiddleware, minimum_size=500)


# ── Security Headers ─────────────────────────────────────────────────────

_CSRF_EXEMPT_PATHS = {"/webhooks/stripe", "/api/cite", "/api/tools/submit", "/api/follow-through", "/api/agent/recommend", "/api/agent/shortlist", "/api/agent/outcome", "/api/agent/integration"}
_ALLOWED_ORIGINS = {"https://indiestack.ai", "https://www.indiestack.ai", "https://indiestack.fly.dev", "https://www.indiestack.fly.dev", "http://localhost:8000", "http://127.0.0.1:8000"}


@app.middleware("http")
async def redirect_old_domain(request: Request, call_next):
    host = request.headers.get("host", "")
    if "indiestack.fly.dev" in host and request.url.path != "/health":
        from starlette.responses import RedirectResponse
        new_url = f"https://indiestack.ai{request.url.path}"
        if request.url.query:
            new_url += f"?{request.url.query}"
        return RedirectResponse(url=new_url, status_code=302)
    return await call_next(request)


@app.middleware("http")
async def csrf_protection(request: Request, call_next):
    """Block cross-origin POST/PUT/DELETE requests (CSRF protection via Origin header)."""
    if request.method in ("POST", "PUT", "DELETE", "PATCH"):
        path = request.url.path
        # Skip exempt paths (webhooks from external services)
        if path not in _CSRF_EXEMPT_PATHS:
            origin = request.headers.get("origin", "")
            if not origin:
                # Fall back to Referer header
                referer = request.headers.get("referer", "")
                if referer:
                    # Extract origin from referer (scheme + host)
                    from urllib.parse import urlparse
                    parsed = urlparse(referer)
                    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else ""

            if not origin:
                return JSONResponse({"error": "Origin required"}, status_code=403)
            if origin not in _ALLOWED_ORIGINS:
                return JSONResponse({"error": "Cross-origin request blocked"}, status_code=403)
    response = await call_next(request)
    return response


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "img-src 'self' https: data:; "
        "font-src 'self' https://fonts.gstatic.com; "
        "connect-src 'self'; "
        "frame-src https://www.youtube.com https://player.vimeo.com"
    )
    return response


# ── 404 Error Page ───────────────────────────────────────────────────────

from starlette.exceptions import HTTPException as StarletteHTTPException
from indiestack.routes.components import page_shell


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        from fastapi.responses import HTMLResponse
        body = """
        <section style="text-align:center;padding:100px 24px 80px;max-width:560px;margin:0 auto;">
            <div style="margin-bottom:16px;"><svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg></div>
            <h1 style="font-family:var(--font-display);font-size:clamp(36px,5vw,48px);color:var(--ink);margin-bottom:12px;">
                404 &mdash; Page not found
            </h1>
            <p style="color:var(--ink-muted);font-size:17px;line-height:1.6;margin-bottom:32px;">
                This page doesn&rsquo;t exist. Save your tokens &mdash; don&rsquo;t build it, find what you need instead.
            </p>
            <form action="/search" method="GET" style="max-width:440px;margin:0 auto 24px;">
                <div style="display:flex;align-items:center;background:var(--card-bg, white);border:2px solid var(--border);
                            border-radius:999px;padding:6px 6px 6px 16px;gap:8px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--ink-muted)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                    <input type="text" name="q"
                           placeholder="Search for tools..."
                           style="flex:1;border:none;outline:none;font-size:15px;font-family:var(--font-body);
                                  padding:8px 0;background:transparent;color:var(--ink);">
                    <button type="submit" class="btn btn-primary" style="padding:8px 18px;flex-shrink:0;">
                        Search
                    </button>
                </div>
            </form>
            <a href="/" style="color:var(--ink-muted);font-size:14px;font-weight:600;">&larr; Back to home</a>
        </section>
        """
        user = getattr(request.state, 'user', None)
        return HTMLResponse(page_shell("Page Not Found", body, user=user), status_code=404)
    # For non-404 HTTP errors, return a simple JSON response
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch unhandled exceptions — log detail, return generic message."""
    _logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse({"error": "Internal server error"}, status_code=500)


# ── DB middleware ─────────────────────────────────────────────────────────

@app.middleware("http")
async def db_middleware(request: Request, call_next):
    # Rate limiting
    client_ip = request.headers.get("fly-client-ip", request.client.host if request.client else "unknown")
    if _check_rate_limit(client_ip, request.url.path, request.method):
        from fastapi.responses import JSONResponse as _JSONResponse
        return _JSONResponse({"error": "Too many requests"}, status_code=429)

    request.state.db = await db.get_db()
    try:
        request.state.user = await get_current_user(request, request.state.db)

        # API key resolution (soft enforcement — log but don't block)
        request.state.api_key = None
        path = request.url.path
        if path.startswith("/api/"):
            raw_key = request.query_params.get("key", "")
            if not raw_key:
                auth_header = request.headers.get("authorization", "")
                if auth_header.startswith("Bearer isk_"):
                    raw_key = auth_header[7:]
            if raw_key and raw_key.startswith("isk_"):
                api_key_row = await db.get_api_key_by_key(request.state.db, raw_key)
                if api_key_row:
                    request.state.api_key = api_key_row
                    # Check daily rate limit by user (not key — prevents revoke+regenerate bypass)
                    if _check_api_key_rate_limit(api_key_row["user_id"], api_key_row.get("tier", "free")):
                        return JSONResponse(
                            {"error": "Monthly API limit reached (10/month on free tier). "
                             "Upgrade to Pro for 1,000/month + citation tracking, market gaps, and data export.",
                             "upgrade_url": "https://indiestack.ai/pricing"},
                            status_code=429,
                        )
                    try:
                        await db.touch_api_key(request.state.db, api_key_row["id"])
                        await db.log_api_usage(request.state.db, api_key_row["id"], path)
                        await request.state.db.commit()
                    except Exception:
                        _logger.exception("Failed to log API usage")
            # No valid API key — apply IP-based daily limit (3/day)
            # Exempt non-query paths (embeddable badges, milestones, OpenAPI spec, categories)
            _API_RATE_EXEMPT = ('/api/badge/', '/api/milestone/', '/api/openapi', '/api/categories', '/api/health', '/api/agent/')
            if not request.state.api_key and not path.startswith(_API_RATE_EXEMPT) and _check_api_ip_rate_limit(client_ip):
                return JSONResponse(
                    {"error": "You've used your 3 free daily queries. "
                     "Create a free API key in 10 seconds for 10 queries/month — just sign in with GitHub.",
                     "get_key_url": "https://indiestack.ai/developer",
                     "upgrade_url": "https://indiestack.ai/pricing"},
                    status_code=429,
                )

        # Track pageview (skip static assets, API calls, and auth pages)
        if not path.startswith(('/api/', '/health', '/favicon', '/logo', '/track', '/robots', '/sitemap', '/signup', '/login', '/auth/')):
            visitor_raw = f"{request.headers.get('fly-client-ip', '') or request.headers.get('x-forwarded-for', '').split(',')[0].strip() or request.client.host}:{request.headers.get('user-agent', '')}"
            visitor_id = hashlib.sha256(visitor_raw.encode()).hexdigest()[:16]
            referrer = request.headers.get('referer', '')
            try:
                await db.track_pageview(request.state.db, path, visitor_id, referrer)
            except Exception:
                _logger.exception("Failed to track pageview")
        response = await call_next(request)
    finally:
        await request.state.db.close()
    return response


# ── Client Event Tracking ─────────────────────────────────────────────────

@app.post("/api/track")
async def track_client_event(request: Request):
    """Track client-side events (install copies, etc.)."""
    try:
        data = await request.json()
        event = data.get("event", "")
        if event not in ("install_copied", "cta_clicked"):
            return JSONResponse({"ok": False})
        from indiestack.db import track_event
        user = request.state.user
        visitor_id = hashlib.sha256(request.client.host.encode()).hexdigest()[:16] if request.client else None
        raw_meta = data.get("metadata")
        if raw_meta and len(_json.dumps(raw_meta)) > 1024:
            return JSONResponse({"ok": False})
        await track_event(
            request.state.db, event,
            visitor_id=visitor_id,
            user_id=user['id'] if user else None,
            metadata=raw_meta,
        )
        return JSONResponse({"ok": True})
    except Exception:
        return JSONResponse({"ok": False})


# ── Health ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


# ── Logo ─────────────────────────────────────────────────────────────

@app.get("/logo.png")
async def logo_png():
    global _logo_bytes
    if _logo_bytes is None:
        for p in _LOGO_CANDIDATES:
            if p.exists():
                _logo_bytes = p.read_bytes()
                break
        else:
            return Response(content=b"", status_code=404)
    return Response(content=_logo_bytes, media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


@app.get("/founders/{name}.jpg")
async def founder_photo(name: str):
    # Whitelist valid founder names
    if name not in ("pat", "ed"):
        return Response(content=b"", status_code=404)
    if name in _founder_photo_cache:
        return Response(content=_founder_photo_cache[name], media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})
    for d in _FOUNDER_PHOTO_DIR_CANDIDATES:
        # Try common extensions
        for ext in (".JPG", ".jpg", ".jpeg", ".png"):
            p = d / f"founderphoto-{name.capitalize()}{ext}"
            if p.exists():
                _founder_photo_cache[name] = p.read_bytes()
                return Response(content=_founder_photo_cache[name], media_type="image/jpeg", headers={"Cache-Control": "public, max-age=86400"})
    return Response(content=b"", status_code=404)


@app.get("/promo-video.mp4")
async def promo_video():
    for d in _FOUNDER_PHOTO_DIR_CANDIDATES:
        p = d / "indiestack_promo_vid.mp4"
        if p.exists():
            return FileResponse(p, media_type="video/mp4", headers={"Cache-Control": "public, max-age=86400"})
    return Response(content=b"", status_code=404)


# ── SEO ───────────────────────────────────────────────────────────────────

@app.get("/googleb0483aef4f89d039.html", response_class=PlainTextResponse)
async def google_verification():
    return "google-site-verification: googleb0483aef4f89d039.html"


@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin",
        "Disallow: /dashboard",
        f"Sitemap: {BASE_URL}/sitemap.xml",
        f"# LLMs: {BASE_URL}/llms.txt",
        f"# LLMs Full: {BASE_URL}/llms-full.txt",
    ]
    indexnow_key = _os.environ.get("INDEXNOW_KEY", "")
    if indexnow_key:
        lines.append(f"# IndexNow: {BASE_URL}/{indexnow_key}.txt")
    return "\n".join(lines)


@app.get("/llms.txt", response_class=PlainTextResponse)
async def llms_txt(request: Request):
    """LLMs.txt — structured site info for AI crawlers."""
    try:
        d = request.state.db
        row = await db.execute_fetchone(d, "SELECT COUNT(*) as cnt FROM tools WHERE status = 'approved'")
        tool_count = row['cnt'] if row else 3000
    except Exception:
        tool_count = 3000
    return (
        "# IndieStack\n\n"
        f"> The discovery layer between AI coding agents and {tool_count}+ proven, lightweight developer tools. "
        "Search by keyword, category, or need — so agents recommend instead of rebuild.\n\n"
        "IndieStack plugs into Claude Code, Cursor, and Windsurf via MCP. "
        "Before your AI generates boilerplate for auth, payments, analytics, or email, "
        "it checks IndieStack for an existing tool that does it better. "
        "Saves 30,000-80,000 tokens per use case.\n\n"
        "## Install\n\n"
        f"- [MCP Server (PyPI)](https://pypi.org/project/indiestack/): "
        "`claude mcp add indiestack -- uvx --from indiestack indiestack-mcp`\n"
        f"- [OpenAPI Spec]({BASE_URL}/openapi.json): REST API for any client\n\n"
        "## API Endpoints\n\n"
        f"- [Search Tools]({BASE_URL}/api/tools/search?q=analytics): "
        "`GET /api/tools/search?q=<query>&category=<slug>&source_type=<code|saas>&limit=<n>&offset=<n>`\n"
        f"- [Tool Details]({BASE_URL}/api/tools/simple-analytics): "
        "`GET /api/tools/<slug>` — pricing, integration snippets, compatibility data\n"
        f"- [Tool Index]({BASE_URL}/api/tools/index.json): "
        "`GET /api/tools/index.json` — compact full catalog for prompt caching\n"
        f"- [Categories]({BASE_URL}/api/categories): `GET /api/categories` — 25 categories with tool counts\n"
        f"- [Tags]({BASE_URL}/api/tags): `GET /api/tags` — all tags sorted by popularity\n"
        f"- [Stack Builder]({BASE_URL}/api/stack-builder?needs=auth,payments): "
        "`GET /api/stack-builder?needs=<needs>&budget=<n>`\n"
        f"- [New Tools]({BASE_URL}/api/new): `GET /api/new?limit=<n>&offset=<n>`\n"
        f"- [Stacks]({BASE_URL}/api/stacks): `GET /api/stacks` — curated tool combinations\n"
        f"- [Collections]({BASE_URL}/api/collections): `GET /api/collections` — themed groupings\n\n"
        "## Key Pages\n\n"
        f"- [Explore]({BASE_URL}/explore): Browse all tools with category/source filters\n"
        f"- [Alternatives]({BASE_URL}/alternatives): Indie alternatives to mainstream SaaS\n"
        f"- [Stacks]({BASE_URL}/stacks): Pre-built tool stacks for common architectures\n"
        f"- [Makers]({BASE_URL}/makers): Indie maker directory\n"
        f"- [Submit]({BASE_URL}/submit): Free listing for developer tools\n"
        f"- [Gaps]({BASE_URL}/gaps): Unsolved problems ranked by developer demand\n\n"
        "## Categories\n\n"
        "Analytics & Metrics, Auth & Identity, Automation & Workflows, CMS & Content, "
        "Customer Support, Database & Backend, Design & UI, DevOps & Hosting, "
        "Email & Marketing, Forms & Surveys, Invoicing & Billing, Monitoring & Logging, "
        "Payments & Subscriptions, Privacy & Compliance, Scheduling & Calendar, "
        "Search & Discovery, Security & Encryption, SEO & Growth, Social & Community, "
        "Storage & Files, Testing & QA\n\n"
        "## Agent Cards (Machine-Readable)\n\n"
        f"- Card Index: {BASE_URL}/cards/index.json\n"
        f"- Per-Tool Card: {BASE_URL}/cards/{{slug}}.json\n\n"
        "## Optional\n\n"
        f"- [Blog]({BASE_URL}/blog): Articles about developer tools and the agent ecosystem\n"
        f"- [RSS Feed]({BASE_URL}/feed/rss): Latest tools via RSS\n"
        f"- [Sitemap]({BASE_URL}/sitemap.xml): Full sitemap\n"
        f"- [AI Pulse]({BASE_URL}/pulse): Live feed of AI agent activity\n"
    )


@app.get("/llms-full.txt", response_class=PlainTextResponse)
async def llms_full_txt(request: Request):
    """Extended llms.txt with full tool catalog for deep agent context."""
    try:
        d = request.state.db
        cursor = await d.execute(
            "SELECT t.name, t.slug, t.tagline, t.source_type, c.name as category "
            "FROM tools t LEFT JOIN categories c ON t.category_id = c.id "
            "WHERE t.status = 'approved' ORDER BY c.name, t.name"
        )
        tools = await cursor.fetchall()
    except Exception:
        tools = []

    lines = [
        f"# IndieStack — Full Tool Catalog\n",
        f"> {len(tools)} developer tools across 25 categories. "
        "Use this for comprehensive tool lookup without API calls.\n",
    ]

    current_cat = None
    for t in tools:
        cat = t['category'] or 'Uncategorized'
        if cat != current_cat:
            current_cat = cat
            lines.append(f"\n## {cat}\n")
        source = "[Code]" if t['source_type'] == 'code' else "[SaaS]"
        lines.append(f"- [{t['name']}]({BASE_URL}/tool/{t['slug']}) {source}: {t['tagline'] or ''}")

    lines.append(f"\n---\nGenerated from {BASE_URL}. Install MCP: `claude mcp add indiestack -- uvx --from indiestack indiestack-mcp`")
    return "\n".join(lines)


@app.get("/.well-known/agent-card.json")
async def agent_card(request: Request):
    """A2A Protocol agent card — agent capability discovery."""
    d = request.state.db
    try:
        row = await db.execute_fetchone(d, "SELECT COUNT(*) as cnt FROM tools WHERE status = 'approved'")
        tool_count = row["cnt"] if row else 3000
    except Exception:
        tool_count = 3000
    return JSONResponse({
        "name": "IndieStack",
        "description": f"The discovery layer between AI coding agents and {tool_count}+ proven, lightweight developer tools.",
        "url": BASE_URL,
        "provider": {
            "organization": "IndieStack",
            "url": BASE_URL,
        },
        "version": "1.0.0",
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
        },
        "skills": [
            {"id": "find_tools", "name": "Find Tools", "description": "Search developer tools by keyword, category, or need"},
            {"id": "get_tool_details", "name": "Get Tool Details", "description": "Integration code, pricing, API specs, and compatibility data"},
            {"id": "analyze_dependencies", "name": "Analyze Dependencies", "description": "Scan package.json/requirements.txt for better alternatives"},
            {"id": "evaluate_build_vs_buy", "name": "Build vs Buy", "description": "Should you generate code or use an existing tool?"},
            {"id": "build_stack", "name": "Build Stack", "description": "Turn a 50k-token generation into a 2k-token assembly"},
            {"id": "compare_tools", "name": "Compare Tools", "description": "Side-by-side tool comparison with pricing and features"},
            {"id": "publish_tool", "name": "Publish Tool", "description": "Submit a developer tool to the catalog"},
            {"id": "get_recommendations", "name": "Get Recommendations", "description": "Personalized suggestions based on your search history"},
        ],
        "interfaces": {
            "mcp": {
                "install": "claude mcp add indiestack -- uvx --from indiestack indiestack-mcp",
                "pypi": "https://pypi.org/project/indiestack/",
                "tools": 13,
                "prompts": 4,
                "resources": 3,
            },
            "rest": {
                "openapi": f"{BASE_URL}/openapi.json",
                "base_url": f"{BASE_URL}/api/",
            },
            "llms_txt": f"{BASE_URL}/llms.txt",
            "agent_cards": {
                "catalog_index": "https://indiestack.ai/cards/index.json",
                "card_template": "https://indiestack.ai/cards/{slug}.json",
                "total_tools": tool_count,
                "schema_version": "1.0",
            },
        },
        "authentication": {
            "required": False,
            "schemes": [
                {"type": "apiKey", "description": "Optional INDIESTACK_API_KEY for personalized recommendations"}
            ],
        },
    })


@app.get("/{key}.txt", response_class=PlainTextResponse)
async def indexnow_key_file(key: str):
    """Serve IndexNow verification key file."""
    indexnow_key = _os.environ.get("INDEXNOW_KEY", "")
    if indexnow_key and key == indexnow_key:
        return indexnow_key
    from fastapi.responses import JSONResponse
    return JSONResponse({"error": "Not found"}, status_code=404)


@app.get("/sitemap.xml")
async def sitemap(request: Request):
    if _sitemap_cache['xml'] and _time.time() < _sitemap_cache['expires']:
        return Response(content=_sitemap_cache['xml'], media_type="application/xml")
    today = date.today().isoformat()
    urls = [
        (f"{BASE_URL}/", "daily", "1.0", today),
        (f"{BASE_URL}/submit", "monthly", "0.5", None),
        (f"{BASE_URL}/new", "daily", "0.8", today),
        (f"{BASE_URL}/stacks", "weekly", "0.7", None),
        (f"{BASE_URL}/makers", "daily", "0.8", today),
        (f"{BASE_URL}/updates", "daily", "0.8", today),
        (f"{BASE_URL}/live", "always", "0.6", today),
        (f"{BASE_URL}/pricing", "monthly", "0.6", None),
        (f"{BASE_URL}/developer", "monthly", "0.6", None),
        (f"{BASE_URL}/why-list", "monthly", "0.6", None),
        (f"{BASE_URL}/geo", "monthly", "0.5", None),
        (f"{BASE_URL}/changelog", "monthly", "0.6", None),
        (f"{BASE_URL}/what-is-indiestack", "monthly", "0.7", None),
        (f"{BASE_URL}/pulse", "daily", "0.6", today),
        (f"{BASE_URL}/gaps", "weekly", "0.7", None),
    ]
    for path in ["/about", "/terms", "/privacy", "/faq"]:
        urls.append((f"{BASE_URL}{path}", "monthly", "0.5", None))
    urls.append((f"{BASE_URL}/blog", "weekly", "0.7", None))
    urls.append((f"{BASE_URL}/blog/stop-wasting-tokens", "monthly", "0.8", "2026-02-15"))
    urls.append((f"{BASE_URL}/blog/zero-js-frameworks", "monthly", "0.8", "2026-02-20"))
    urls.append((f"{BASE_URL}/blog/marketplace-launch", "monthly", "0.8", "2026-02-22"))
    urls.append((f"{BASE_URL}/blog/tokens-saved", "monthly", "0.8", "2026-02-25"))
    urls.append((f"{BASE_URL}/blog/agent-infrastructure", "monthly", "0.8", "2026-02-27"))
    urls.append((f"{BASE_URL}/alternatives", "daily", "0.8", today))
    urls.append((f"{BASE_URL}/compare", "weekly", "0.7", None))
    # Individual alternatives pages
    d = request.state.db
    competitors = await db.get_all_competitors(d)
    for comp in competitors:
        comp_slug = comp.lower().replace(" ", "-").replace(".", "-")
        urls.append((f"{BASE_URL}/alternatives/{comp_slug}", "weekly", "0.7", None))
    # Deep comparison pages: /alternatives/{competitor}/vs/{tool}
    for comp in competitors:
        comp_slug = comp.lower().replace(" ", "-").replace(".", "-")
        comp_tools_cursor = await d.execute(
            "SELECT slug FROM tools WHERE status = 'approved' AND LOWER(replaces) LIKE LOWER(?)",
            (f'%{comp}%',))
        comp_tools_rows = await comp_tools_cursor.fetchall()
        for ct in comp_tools_rows:
            urls.append((f"{BASE_URL}/alternatives/{comp_slug}/vs/{ct['slug']}", "weekly", "0.6", None))
    # Use case pages
    urls.append((f"{BASE_URL}/use-cases", "weekly", "0.8", None))
    for uc_slug in db.NEED_MAPPINGS:
        urls.append((f"{BASE_URL}/use-cases/{uc_slug}", "weekly", "0.7", None))
    cats = await db.get_all_categories(d)
    for c in cats:
        urls.append((f"{BASE_URL}/category/{c['slug']}", "daily", "0.8", None))
    # Best-of programmatic SEO pages
    urls.append((f"{BASE_URL}/best", "weekly", "0.8", None))
    for c in cats:
        urls.append((f"{BASE_URL}/best/{c['slug']}", "weekly", "0.7", None))
    cursor = await d.execute("SELECT slug, created_at as lastmod FROM tools WHERE status = 'approved' LIMIT 5000")
    tools = await cursor.fetchall()
    for t in tools:
        lm = t['lastmod'][:10] if t.get('lastmod') else None
        urls.append((f"{BASE_URL}/tool/{t['slug']}", "weekly", "0.7", lm))
    # Maker profiles
    cursor2 = await d.execute("SELECT slug FROM makers LIMIT 5000")
    makers = await cursor2.fetchall()
    for m in makers:
        urls.append((f"{BASE_URL}/maker/{m['slug']}", "weekly", "0.6", None))
    # Stacks
    cursor_stacks = await d.execute("SELECT slug FROM stacks")
    all_stacks_list = await cursor_stacks.fetchall()
    for st in all_stacks_list:
        urls.append((f"{BASE_URL}/stacks/{st['slug']}", "weekly", "0.7", None))
    # Compare pages: verified tool pairs from tool_pairs table (success_count > 0)
    pairs_cursor = await d.execute(
        "SELECT tool_a_slug, tool_b_slug FROM tool_pairs WHERE success_count > 0"
    )
    verified_pairs = await pairs_cursor.fetchall()
    compare_seen = set()
    for p in verified_pairs:
        pair_key = f"{p['tool_a_slug']}-vs-{p['tool_b_slug']}"
        if pair_key not in compare_seen:
            compare_seen.add(pair_key)
            urls.append((f"{BASE_URL}/compare/{pair_key}", "weekly", "0.6", None))
    # Compare pages (top pairs per category, as fallback for pairs not in tool_pairs)
    for c in cats:
        cat_cursor = await d.execute(
            "SELECT slug FROM tools WHERE category_id = ? AND status = 'approved' ORDER BY upvote_count DESC LIMIT 6",
            (c['id'],))
        cat_tools = await cat_cursor.fetchall()
        slugs = [t['slug'] for t in cat_tools]
        for i in range(len(slugs)):
            for j in range(i + 1, len(slugs)):
                pair_key = f"{slugs[i]}-vs-{slugs[j]}"
                if pair_key not in compare_seen:
                    compare_seen.add(pair_key)
                    urls.append((f"{BASE_URL}/compare/{pair_key}", "weekly", "0.5", None))
    urls.append((f"{BASE_URL}/calculator", "weekly", "0.8", None))
    # Explore
    urls.append((f"{BASE_URL}/explore", "daily", "0.9", today))
    # Tags
    urls.append((f"{BASE_URL}/tags", "weekly", "0.7", None))
    all_tags = await db.get_all_tags_with_counts(d, min_count=1)
    for tag_item in all_tags:
        urls.append((f"{BASE_URL}/tag/{tag_item['slug']}", "weekly", "0.6", None))
    def _sitemap_entry(u, f, p, lm):
        parts = [f"<loc>{u}</loc>", f"<changefreq>{f}</changefreq>", f"<priority>{p}</priority>"]
        if lm:
            parts.append(f"<lastmod>{lm}</lastmod>")
        return "  <url>" + "".join(parts) + "</url>"
    entries = "\n".join(
        _sitemap_entry(u, f, p, lm)
        for u, f, p, lm in urls
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>"""
    _sitemap_cache['xml'] = xml
    _sitemap_cache['expires'] = _time.time() + 3600  # 1 hour
    return Response(content=xml, media_type="application/xml")


FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<rect width="100" height="100" rx="16" fill="#1A2D4A"/>
<text x="50" y="72" font-size="60" text-anchor="middle" fill="#00D4F5" font-family="sans-serif" font-weight="bold">iS</text>
</svg>"""


@app.get("/favicon.svg")
async def favicon_svg():
    return Response(content=FAVICON_SVG, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})


@app.get("/favicon.ico")
async def favicon_ico():
    return Response(content=FAVICON_SVG, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=86400"})


# ── Upvote API ────────────────────────────────────────────────────────────

@app.post("/api/upvote")
async def api_upvote(request: Request):
    try:
        body = await request.json()
        tool_id = int(body.get("tool_id", 0))
    except (ValueError, TypeError):
        return JSONResponse({"ok": False, "error": "Invalid request"}, status_code=400)

    if not tool_id:
        return JSONResponse({"ok": False, "error": "Missing tool_id"}, status_code=400)

    ip = request.headers.get("fly-client-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host
    count, upvoted = await db.toggle_upvote(request.state.db, tool_id, ip)

    # Notify maker on upvote
    if upvoted:
        try:
            tool = await db.get_tool_by_id(request.state.db, tool_id)
            if tool and tool.get('maker_id'):
                # Find the user linked to this maker
                cursor = await request.state.db.execute(
                    "SELECT id FROM users WHERE maker_id = ?", (tool['maker_id'],)
                )
                maker_user = await cursor.fetchone()
                if maker_user:
                    # Don't notify if maker upvotes their own tool
                    current_user = request.state.user
                    if not current_user or current_user['id'] != maker_user['id']:
                        await db.create_notification(
                            request.state.db, maker_user['id'], 'upvote',
                            f"{tool['name']} got an upvote!",
                            f"/tool/{tool['slug']}"
                        )
        except Exception:
            _logger.exception("Failed to create upvote notification")

    return JSONResponse({"ok": True, "count": count, "upvoted": upvoted})


@app.post("/api/upvote-check")
async def api_upvote_check(request: Request):
    """Check which tools the current user has upvoted."""
    try:
        body = await request.json()
        tool_ids = body.get("tool_ids", [])
    except (ValueError, TypeError):
        return JSONResponse({"upvoted": []})

    if not tool_ids or not isinstance(tool_ids, list):
        return JSONResponse({"upvoted": []})

    # Cap to 50 to prevent abuse
    tool_ids = [int(t) for t in tool_ids[:50] if isinstance(t, (int, float))]

    ip = request.headers.get("fly-client-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host
    ip_hash = db.hash_ip(ip)
    d = request.state.db
    placeholders = ','.join('?' * len(tool_ids))
    cursor = await d.execute(
        f"SELECT DISTINCT tool_id FROM upvotes WHERE tool_id IN ({placeholders}) AND ip_hash = ?",
        (*tool_ids, ip_hash)
    )
    upvoted_set = {r['tool_id'] for r in await cursor.fetchall()}
    upvoted = [tid for tid in tool_ids if tid in upvoted_set]

    return JSONResponse({"upvoted": upvoted})


@app.post("/api/stack-upvote")
async def api_stack_upvote(request: Request):
    try:
        body = await request.json()
        stack_id = int(body.get("stack_id", 0))
    except (ValueError, TypeError):
        return JSONResponse({"ok": False, "error": "Invalid request"}, status_code=400)
    if not stack_id:
        return JSONResponse({"ok": False, "error": "Missing stack_id"}, status_code=400)
    ip = request.headers.get("fly-client-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host
    count, upvoted = await db.toggle_stack_upvote(request.state.db, stack_id, ip)
    return JSONResponse({"ok": True, "count": count, "upvoted": upvoted})


@app.post("/api/stack-upvote-check")
async def api_stack_upvote_check(request: Request):
    """Check which stacks the current user has upvoted."""
    try:
        body = await request.json()
        stack_ids = body.get("stack_ids", [])
    except (ValueError, TypeError):
        return JSONResponse({"upvoted": []})
    if not stack_ids or not isinstance(stack_ids, list):
        return JSONResponse({"upvoted": []})
    stack_ids = [int(s) for s in stack_ids[:50] if isinstance(s, (int, float))]
    ip = request.headers.get("fly-client-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host
    ip_hash = db.hash_ip(ip)
    d = request.state.db
    placeholders = ','.join('?' * len(stack_ids))
    cursor = await d.execute(
        f"SELECT DISTINCT stack_id FROM stack_upvotes WHERE stack_id IN ({placeholders}) AND ip_hash = ?",
        (*stack_ids, ip_hash)
    )
    upvoted_set = {r['stack_id'] for r in await cursor.fetchall()}
    return JSONResponse({"upvoted": [sid for sid in stack_ids if sid in upvoted_set]})


@app.post("/api/wishlist")
async def api_wishlist(request: Request):
    user = request.state.user
    if not user:
        return JSONResponse({"ok": False, "error": "login_required"}, status_code=401)
    try:
        body = await request.json()
        tool_id = int(body.get("tool_id", 0))
    except (ValueError, TypeError):
        return JSONResponse({"ok": False, "error": "Invalid request"}, status_code=400)
    if not tool_id:
        return JSONResponse({"ok": False, "error": "Missing tool_id"}, status_code=400)
    is_saved, count = await db.toggle_wishlist(request.state.db, user['id'], tool_id)

    # Notify maker when someone saves their tool
    if is_saved:
        try:
            tool = await db.get_tool_by_id(request.state.db, tool_id)
            if tool and tool.get('maker_id'):
                cursor = await request.state.db.execute(
                    "SELECT id FROM users WHERE maker_id = ?", (tool['maker_id'],)
                )
                maker_user = await cursor.fetchone()
                if maker_user and maker_user['id'] != user['id']:
                    await db.create_notification(
                        request.state.db, maker_user['id'], 'wishlist',
                        f"{tool['name']} was saved by someone!",
                        f"/tool/{tool['slug']}"
                    )
        except Exception:
            pass  # Don't break wishlist if notification fails

    return JSONResponse({"ok": True, "saved": is_saved, "count": count})


@app.post("/api/subscribe")
async def api_subscribe(request: Request):
    from fastapi.responses import RedirectResponse as _Redirect

    def _safe_subscribe_next(url: str) -> str:
        """Validate redirect URL — must be relative path, not protocol-relative."""
        if url and url.startswith("/") and not url.startswith("//"):
            return url
        return ""

    try:
        form = await request.form()
        email = str(form.get("email", "")).strip().lower()
        next_url = _safe_subscribe_next(str(form.get("next", "")).strip())
        source = str(form.get("source", "")).strip()
        tool_slug = str(form.get("tool_slug", "")).strip()
        tool_slug = tool_slug[:200]
    except Exception:
        email = ""
        next_url = ""
        source = ""
        tool_slug = ""
    if not email or "@" not in email:
        if next_url:
            return _Redirect(url=next_url, status_code=303)
        return _Redirect(url="/?subscribed=error", status_code=303)
    try:
        import uuid as _uuid
        token = str(_uuid.uuid4())
        await request.state.db.execute(
            "INSERT OR IGNORE INTO subscribers (email, source, tool_slug, unsubscribe_token) VALUES (?, ?, ?, ?)",
            (email, source, tool_slug, token),
        )
        await request.state.db.commit()
    except Exception:
        _logger.exception("Failed to save subscriber")
    if next_url:
        return _Redirect(url=next_url, status_code=303)
    return _Redirect(url="/?subscribed=1", status_code=303)


# ── Unsubscribe ─────────────────────────────────────────────────────────

@app.get("/unsubscribe/{token}")
async def unsubscribe(request: Request, token: str):
    from fastapi.responses import HTMLResponse
    from indiestack.routes.components import page_shell
    from html import escape as _esc
    db = request.state.db
    cursor = await db.execute("SELECT id, email FROM subscribers WHERE unsubscribe_token = ?", (token,))
    row = await cursor.fetchone()
    if row:
        await db.execute("DELETE FROM subscribers WHERE id = ?", (row["id"],))
        await db.execute("INSERT OR IGNORE INTO email_optouts (email) VALUES (?)", (row["email"].lower(),))
        await db.commit()
        body = f"""
        <div style="max-width:480px;margin:80px auto;text-align:center;">
            <h1 style="font-size:28px;margin-bottom:12px;">You've been unsubscribed</h1>
            <p style="color:var(--ink-muted);font-size:15px;line-height:1.6;">
                <strong>{_esc(row['email'])}</strong> has been removed from our mailing list.
                You won't receive any more emails from IndieStack.
            </p>
            <a href="/" style="display:inline-block;margin-top:24px;color:var(--terracotta);font-weight:600;text-decoration:none;">
                &larr; Back to IndieStack
            </a>
        </div>
        """
    else:
        body = """
        <div style="max-width:480px;margin:80px auto;text-align:center;">
            <h1 style="font-size:28px;margin-bottom:12px;">Already unsubscribed</h1>
            <p style="color:var(--ink-muted);font-size:15px;line-height:1.6;">
                This link has already been used or is no longer valid.
            </p>
            <a href="/" style="display:inline-block;margin-top:24px;color:var(--terracotta);font-weight:600;text-decoration:none;">
                &larr; Back to IndieStack
            </a>
        </div>
        """
    return HTMLResponse(page_shell("Unsubscribe — IndieStack", body))


# ── Tool Search API ──────────────────────────────────────────────────────

def _personalize_results(tools: list[dict], profile: dict) -> list[dict]:
    """Rerank search results using a developer's profile. Returns tools with recommendation_reason."""
    import json
    interests = json.loads(profile.get('interests', '{}')) if isinstance(profile.get('interests'), str) else profile.get('interests', {})
    tech_stack = json.loads(profile.get('tech_stack', '[]')) if isinstance(profile.get('tech_stack'), str) else profile.get('tech_stack', [])
    favorites = json.loads(profile.get('favorite_tools', '[]')) if isinstance(profile.get('favorite_tools'), str) else profile.get('favorite_tools', [])
    tech_set = set(kw.lower() for kw in tech_stack)

    scored = []
    for i, tool in enumerate(tools):
        boost = 0.0
        reason = ''

        # Category match
        cat_slug = tool.get('category_slug', '') or tool.get('category', '').lower().replace(' ', '-')
        if cat_slug in interests:
            confidence = interests[cat_slug]
            boost += confidence * 0.3
            cat_name = cat_slug.replace('-', ' ').title()
            reason = f"Matches your interest in {cat_name}"

        # Tech stack match — check tool tags
        tags = (tool.get('tags', '') or '').lower()
        tool_name = (tool.get('name', '') or '').lower()
        matched_tech = [kw for kw in tech_set if kw in tags or kw in tool_name]
        if matched_tech:
            boost += 0.2
            reason = f"Works with {matched_tech[0].title()}" if not reason else reason

        # Favorite boost
        slug = tool.get('slug', '')
        if slug in favorites:
            boost += 0.1

        # Preserve original order as tiebreaker
        tool['_personalization_score'] = boost
        tool['_original_index'] = i
        if reason:
            tool['recommendation_reason'] = reason
        scored.append(tool)

    # Sort by boost descending, original order as tiebreaker
    scored.sort(key=lambda t: (-t['_personalization_score'], t['_original_index']))

    # Clean up internal fields
    for t in scored:
        t.pop('_personalization_score', None)
        t.pop('_original_index', None)

    return scored


def _apply_post_filters(tools, *, price="", health="", exclude="", has_api=False, min_stars=0, language="", tags=""):
    if price == "free":
        tools = [t for t in tools if not t.get('price_pence')]
    elif price == "paid":
        tools = [t for t in tools if t.get('price_pence') and t['price_pence'] > 0]
    if health and health in ("active", "stale", "dead", "archived"):
        tools = [t for t in tools if t.get('health_status') == health]
    if exclude:
        excluded_slugs = {s.strip() for s in exclude.split(",") if s.strip()}
        tools = [t for t in tools if t['slug'] not in excluded_slugs]
    if has_api:
        tools = [t for t in tools if t.get('api_type')]
    if min_stars > 0:
        tools = [t for t in tools if (t.get('github_stars') or 0) >= min_stars]
    if language:
        tools = [t for t in tools if (t.get('github_language') or '').lower() == language.lower()]
    if tags:
        filter_tags = {tg.strip().lower() for tg in tags.split(",") if tg.strip()}
        if filter_tags:
            tools = [t for t in tools if filter_tags.intersection(
                {tg.strip().lower() for tg in (t.get('tags') or '').split(",") if tg.strip()}
            )]
    return tools


@app.get("/api/tools/search")
async def api_tools_search(
    request: Request,
    q: str = "",
    category: str = "",
    limit: int = 20,
    offset: int = 0,
    source: str = "",
    source_type: str = "",
    # Intelligence filters
    compatible_with: str = "",
    price: str = "",
    min_success_rate: int = 0,
    min_confidence: str = "",
    has_api: bool = False,
    language: str = "",
    tags: str = "",
    exclude: str = "",
    health: str = "",
    min_stars: int = 0,
    sort: str = "",
    frameworks: str = "",
):
    """JSON API for searching tools — used by MCP server and integrations."""
    d = request.state.db
    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50
    if offset < 0:
        offset = 0

    # Validate source_type
    st = source_type.strip().lower() if source_type else ""
    if st not in ("code", "saas", ""):
        st = ""

    if q.strip():
        tools = await db.search_tools(
            d, q.strip(), limit=offset + limit, source_type=st,
            compatible_with=compatible_with, price=price,
            min_success_rate=min_success_rate, min_confidence=min_confidence,
            has_api=has_api, language=language, tags=tags,
            exclude=exclude, health=health, min_stars=min_stars, sort=sort,
            frameworks=frameworks,
        )
        tools = tools[offset:]
    elif category.strip():
        cat = await db.get_category_by_slug(d, category.strip())
        if cat:
            page = (offset // limit) + 1
            tools, _ = await db.get_tools_by_category(d, cat['id'], page=page, per_page=limit)
            # Apply post-filters for category browsing
            tools = _apply_post_filters(tools, price=price, health=health, exclude=exclude, has_api=has_api, min_stars=min_stars, language=language, tags=tags)
            if compatible_with:
                pair_cursor = await d.execute(
                    """SELECT CASE WHEN tool_a_slug = ? THEN tool_b_slug ELSE tool_a_slug END as pair_slug
                       FROM tool_pairs WHERE (tool_a_slug = ? OR tool_b_slug = ?) AND success_count >= 1""",
                    (compatible_with, compatible_with, compatible_with),
                )
                compatible_slugs = {r[0] for r in await pair_cursor.fetchall()}
                tools = [t for t in tools if t['slug'] in compatible_slugs]
            if sort == "stars":
                tools.sort(key=lambda t: t.get('github_stars') or 0, reverse=True)
            elif sort == "upvotes":
                tools.sort(key=lambda t: t.get('upvote_count') or 0, reverse=True)
            elif sort == "newest":
                tools.sort(key=lambda t: t.get('created_at') or '', reverse=True)
        else:
            tools = []
    else:
        tools = await db.get_trending_tools(d, limit=offset + limit)
        tools = tools[offset:]
        # Apply post-filters for trending browsing
        tools = _apply_post_filters(tools, price=price, health=health, exclude=exclude, has_api=has_api, min_stars=min_stars, language=language, tags=tags)
        if compatible_with:
            pair_cursor = await d.execute(
                """SELECT CASE WHEN tool_a_slug = ? THEN tool_b_slug ELSE tool_a_slug END as pair_slug
                   FROM tool_pairs WHERE (tool_a_slug = ? OR tool_b_slug = ?) AND success_count >= 1""",
                (compatible_with, compatible_with, compatible_with),
            )
            compatible_slugs = {r[0] for r in await pair_cursor.fetchall()}
            tools = [t for t in tools if t['slug'] in compatible_slugs]
        if sort == "stars":
            tools.sort(key=lambda t: t.get('github_stars') or 0, reverse=True)
        elif sort == "upvotes":
            tools.sort(key=lambda t: t.get('upvote_count') or 0, reverse=True)
        elif sort == "newest":
            tools.sort(key=lambda t: t.get('created_at') or '', reverse=True)

    results = []
    for t in tools:
        price_pence = t.get('price_pence')
        if price_pence and price_pence > 0:
            price_str = f"\u00a3{price_pence / 100:.2f}"
        else:
            price_str = "Free"
        result = {
            "name": t['name'],
            "slug": t['slug'],
            "tagline": t.get('tagline', ''),
            "url": t.get('url', ''),
            "indiestack_url": f"{BASE_URL}/tool/{t['slug']}",
            "category": t.get('category_name', ''),
            "category_slug": t.get('category_slug', ''),
            "price": price_str,
            "is_verified": bool(t.get('is_verified', 0)),
            "upvote_count": int(t.get('upvote_count', 0)),
            "tags": t.get('tags', ''),
            "source_type": t.get('source_type', 'saas'),
            "github_stars": t.get('github_stars'),
            "github_last_commit": t.get('github_last_commit'),
            "health_status": t.get('health_status'),
        }
        # Add plugin metadata if present
        if t.get('tool_type'):
            result["tool_type"] = t['tool_type']
            result["platforms"] = t.get('platforms', '')
            result["install_command"] = t.get('install_command', '')
        results.append(result)

    # Log the search for Live Wire
    try:
        top_slug = tools[0]['slug'] if tools else None
        top_name = tools[0]['name'] if tools else None
        api_key_id = request.state.api_key['id'] if request.state.api_key else None
        agent_client = request.headers.get("User-Agent", "")[:100] or None
        await db.log_search(d, q, 'api', len(results), top_slug, top_name, api_key_id=api_key_id, agent_client=agent_client)
    except Exception:
        pass  # Don't fail the search if logging fails

    # Track MCP views
    if source == "mcp" and tools:
        try:
            tool_ids = [t['id'] for t in tools if t.get('id')]
            await db.increment_mcp_views_bulk(d, tool_ids)
            await db.log_agent_citations_bulk(d, tool_ids, agent_name="mcp")
        except Exception:
            pass

    # Personalize results if API key has a mature profile
    personalized = False
    notice = None
    api_key = request.state.api_key
    if api_key and results:
        profile = await db.get_developer_profile(d, api_key['id'])

        # Rebuild if stale (> 1 hour old) or doesn't exist
        should_rebuild = False
        if not profile:
            should_rebuild = True
        elif profile['last_rebuilt_at']:
            from datetime import datetime, timedelta
            try:
                rebuilt = datetime.fromisoformat(profile['last_rebuilt_at'])
                if datetime.utcnow() - rebuilt > timedelta(hours=1):
                    should_rebuild = True
            except (ValueError, TypeError):
                should_rebuild = True
        else:
            should_rebuild = True

        if should_rebuild:
            profile_data = await db.build_developer_profile(d, api_key['id'])
            profile = await db.get_developer_profile(d, api_key['id'])

        if profile and profile.get('search_count', 0) >= 5 and profile.get('personalization_enabled', 1):
            results = _personalize_results(results, profile)
            personalized = True

        # First-search notice
        if profile and not profile.get('notice_shown', 0):
            notice = "IndieStack is learning your preferences to improve recommendations. View or manage your profile at indiestack.ai/developer"
            await db.mark_notice_shown(d, api_key['id'])

    # Pro MCP enrichment — add citation counts and compatible pairs for Pro keys
    is_pro_key = api_key and api_key.get('tier') == 'pro'
    if is_pro_key and results:
        try:
            tool_ids = [t['id'] for t in tools if t.get('id')]
            tool_slugs = [r['slug'] for r in results]
            slug_to_id = {t['slug']: t['id'] for t in tools if t.get('id')}
            import asyncio as _asyncio
            citation_counts, compat_pairs = await _asyncio.gather(
                db.get_citation_counts_bulk(d, tool_ids),
                db.get_compatible_pairs_bulk(d, tool_slugs),
            )
            for r in results:
                tid = slug_to_id.get(r['slug'])
                if tid:
                    r['citation_count_7d'] = citation_counts.get(tid, 0)
                pairs = compat_pairs.get(r['slug'], [])
                if pairs:
                    r['compatible_with'] = pairs
        except Exception:
            pass  # Don't fail the search if enrichment fails

    response = {
        "tools": results,
        "total": len(results),
        "query": q,
        "offset": offset,
        "personalized": personalized,
    }
    if is_pro_key:
        response["pro_enriched"] = True
    if notice:
        response["notice"] = notice
    if q.strip() and not results:
        demand = await db.get_search_demand(d, q, days=30)
        gap_data = {}
        try:
            normalized = db.normalize_search_query(q)
            gap_cursor = await d.execute(
                """SELECT COUNT(*) as cnt, COUNT(DISTINCT COALESCE(api_key_id, -1)) as unique_sources
                   FROM search_logs WHERE normalized_query = ? AND result_count = 0
                   AND created_at > datetime('now', '-30 days')""",
                (normalized,),
            )
            gap_row = await gap_cursor.fetchone()
            gap_data = {
                "searches_30d": gap_row['cnt'] if gap_row else 0,
                "unique_agents": gap_row['unique_sources'] if gap_row else 0,
            }
        except Exception:
            gap_data = {}
        response["market_gap"] = {
            "message": f"No tools found for '{q.strip()}'. This is an unsolved market gap — consider building one.",
            "submit_url": f"{BASE_URL}/submit",
            "query": q.strip(),
            "searches_30d": gap_data.get("searches_30d", demand),
            "unique_agents": gap_data.get("unique_agents", 0),
        }
    return JSONResponse(response)


@app.get("/api/recommendations")
async def api_recommendations(request: Request, category: str = "", limit: int = 5):
    """Personalized tool recommendations based on developer profile."""
    import json as _json

    limit = max(1, min(10, limit))
    api_key = request.state.api_key
    d = request.state.db

    if not api_key:
        return JSONResponse({"error": "API key required for recommendations. Get one at indiestack.ai/developer"}, status_code=401)

    # Get or build profile
    profile = await db.get_developer_profile(d, api_key['id'])
    if not profile:
        await db.build_developer_profile(d, api_key['id'])
        profile = await db.get_developer_profile(d, api_key['id'])

    if not profile or profile.get('search_count', 0) < 5:
        # Cold profile — return trending instead
        trending = await db.get_trending_scored(d, limit=limit)
        tools_list = []
        for t in trending:
            tools_list.append({
                "name": t['name'], "slug": t['slug'], "tagline": t['tagline'],
                "price": f"£{t['price_pence'] / 100:.2f}" if t.get('price_pence') else "Free",
                "is_verified": bool(t.get('is_verified')),
                "indiestack_url": f"https://indiestack.ai/tool/{t['slug']}",
                "recommendation_reason": "Trending this week",
                "discovery": False,
            })
        return JSONResponse({
            "recommendations": tools_list,
            "profile_maturity": "cold",
            "total_searches": profile.get('search_count', 0) if profile else 0,
            "message": "Not enough search history to personalize yet. Keep using IndieStack through your agent and recommendations will improve.",
        })

    if not profile.get('personalization_enabled', 1):
        return JSONResponse({"error": "Personalization is paused. Enable it at indiestack.ai/developer"}, status_code=403)

    interests = _json.loads(profile['interests']) if isinstance(profile['interests'], str) else profile['interests']
    tech_stack = _json.loads(profile['tech_stack']) if isinstance(profile['tech_stack'], str) else profile['tech_stack']
    favorites = _json.loads(profile['favorite_tools']) if isinstance(profile['favorite_tools'], str) else profile['favorite_tools']

    # Build a weighted query across top interest categories
    recommended = []
    seen_slugs = set(favorites)  # Exclude favorites (they already know these)

    # Get recent search result slugs to avoid repeats
    recent_cursor = await d.execute(
        """SELECT DISTINCT top_result_slug FROM search_logs
           WHERE api_key_id = ? AND top_result_slug IS NOT NULL
           AND created_at >= datetime('now', '-7 days')""",
        (api_key['id'],))
    for row in await recent_cursor.fetchall():
        seen_slugs.add(row['top_result_slug'])

    # Query tools from top interest categories
    sorted_interests = sorted(interests.items(), key=lambda x: -x[1])
    if category:
        # Filter to specific category if requested
        sorted_interests = [(cat, score) for cat, score in sorted_interests if cat == category]

    for cat_slug, confidence in sorted_interests[:5]:
        cat_cursor = await d.execute(
            """SELECT t.*, c.name as category_name, c.slug as category_slug
               FROM tools t JOIN categories c ON t.category_id = c.id
               WHERE c.slug = ? AND t.status = 'approved'
               ORDER BY t.upvote_count DESC LIMIT 10""",
            (cat_slug,))
        for t in await cat_cursor.fetchall():
            t = dict(t)
            if t['slug'] not in seen_slugs and len(recommended) < limit - 1:
                # Generate reason
                tags = (t.get('tags', '') or '').lower()
                tech_match = [kw for kw in tech_stack if kw.lower() in tags or kw.lower() in t['name'].lower()]
                cat_name = t['category_name']

                if tech_match:
                    reason = f"Popular with {tech_match[0].title()} users"
                elif confidence >= 0.7:
                    reason = f"Matches your interest in {cat_name}"
                else:
                    reason = f"Recommended in {cat_name}"

                recommended.append({
                    "name": t['name'], "slug": t['slug'], "tagline": t['tagline'],
                    "price": f"£{t['price_pence'] / 100:.2f}" if t.get('price_pence') else "Free",
                    "is_verified": bool(t.get('is_verified')),
                    "indiestack_url": f"https://indiestack.ai/tool/{t['slug']}",
                    "recommendation_reason": reason,
                    "discovery": False,
                })
                seen_slugs.add(t['slug'])

        if len(recommended) >= limit - 1:
            break

    # Add 1 discovery pick — trending tool outside their interests
    interest_cats = set(interests.keys())
    disc_cursor = await d.execute(
        """SELECT t.*, c.name as category_name, c.slug as category_slug
           FROM tools t JOIN categories c ON t.category_id = c.id
           WHERE t.status = 'approved'
           ORDER BY t.upvote_count DESC LIMIT 50""")
    for t in await disc_cursor.fetchall():
        t = dict(t)
        if t['slug'] not in seen_slugs and t.get('category_slug') not in interest_cats:
            recommended.append({
                "name": t['name'], "slug": t['slug'], "tagline": t['tagline'],
                "price": f"£{t['price_pence'] / 100:.2f}" if t.get('price_pence') else "Free",
                "is_verified": bool(t.get('is_verified')),
                "indiestack_url": f"https://indiestack.ai/tool/{t['slug']}",
                "recommendation_reason": f"Trending in {t['category_name']} — outside your usual picks",
                "discovery": True,
            })
            break

    return JSONResponse({
        "recommendations": recommended[:limit],
        "profile_maturity": "mature",
        "total_searches": profile['search_count'],
    })


@app.get("/api/new")
async def api_new_tools(request: Request, limit: int = 20, offset: int = 0):
    """JSON API for recently added tools."""
    d = request.state.db
    if limit < 1: limit = 1
    if limit > 50: limit = 50
    if offset < 0: offset = 0
    page = (offset // limit) + 1
    tools, total = await db.get_recent_tools_paginated(d, page=page, per_page=limit)
    results = []
    for t in tools:
        price_pence = t.get('price_pence')
        if price_pence and price_pence > 0:
            price_str = f"\u00a3{price_pence / 100:.2f}"
        else:
            price_str = "Free"
        results.append({
            "name": t['name'],
            "slug": t.get('slug', ''),
            "tagline": t.get('tagline', ''),
            "url": t.get('url', ''),
            "indiestack_url": f"{BASE_URL}/tool/{t['slug']}",
            "category": t.get('category_name', ''),
            "price": price_str,
            "is_verified": bool(t.get('is_verified', 0)),
            "upvote_count": int(t.get('upvote_count', 0)),
            "tags": t.get('tags', ''),
            "source_type": t.get('source_type', ''),
            "created_at": t.get('created_at', ''),
        })
    return JSONResponse({"tools": results, "total": total, "offset": offset})


@app.get("/api/tags")
async def api_tags(request: Request):
    """JSON API for all tags with usage counts."""
    d = request.state.db
    results = await db.get_all_tags_with_counts(d)
    return JSONResponse({"tags": results, "total": len(results)})


@app.get("/api/stacks")
async def api_stacks(request: Request, source: str = "", framework: str = "", sort: str = ""):
    """JSON API for tool stacks — curated and auto-generated."""
    d = request.state.db
    if source:
        stacks = await db.get_stacks_by_source(d, source)
    else:
        stacks = await db.get_all_stacks(d)

    if framework:
        stacks = [s for s in stacks if (s.get('framework') or '').lower() == framework.lower()]

    if sort == "confidence":
        stacks.sort(key=lambda s: s.get('confidence_score', 0) or 0, reverse=True)

    results = []
    for s in stacks:
        entry = {
            "title": s['title'],
            "slug": s.get('slug', ''),
            "description": s.get('description', ''),
            "cover_emoji": s.get('cover_emoji', ''),
            "tool_count": int(s.get('tool_count', 0) or s.get('tool_count_cached', 0)),
            "indiestack_url": f"{BASE_URL}/stacks/{s.get('slug', '')}",
            "source": s.get('source', 'curated'),
        }
        # Add intelligence fields if present
        if s.get('confidence_score'):
            entry["confidence_score"] = round(s['confidence_score'], 3)
        if s.get('total_tokens_saved'):
            entry["total_tokens_saved"] = s['total_tokens_saved']
        if s.get('framework'):
            entry["framework"] = s['framework']
        if s.get('replaces_json'):
            try:
                entry["replaces"] = _json.loads(s['replaces_json']) if isinstance(s['replaces_json'], str) else s['replaces_json']
            except (_json.JSONDecodeError, TypeError):
                pass
        results.append(entry)

    return JSONResponse({"stacks": results, "total": len(results)})


@app.get("/api/collections")
async def api_collections(request: Request):
    """Redirects to /api/stacks — collections merged into stacks."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/api/stacks", status_code=301)


@app.get("/api/tools/index.json")
async def api_tools_index(request: Request):
    """Compact index of all tools — designed for agent system prompts and prompt caching."""
    d = request.state.db
    cursor = await d.execute("""
        SELECT t.id, t.name, t.slug, t.tagline, t.price_pence, t.tags,
               t.is_verified, t.upvote_count, t.mcp_view_count,
               c.name as category_name, c.slug as category_slug
        FROM tools t
        JOIN categories c ON t.category_id = c.id
        WHERE t.status = 'approved'
        ORDER BY t.name
    """)
    rows = await cursor.fetchall()
    tools = []
    for r in rows:
        pp = r['price_pence']
        tools.append({
            "id": r['id'], "name": r['name'], "slug": r['slug'],
            "tagline": r['tagline'],
            "category": r['category_name'], "category_slug": r['category_slug'],
            "price": f"\u00a3{pp/100:.2f}" if pp and pp > 0 else "Free",
            "tags": r['tags'] or "",
            "verified": bool(r['is_verified']),
            "upvotes": int(r['upvote_count'] or 0),
            "agent_views": int(r['mcp_view_count'] or 0),
        })
    return JSONResponse(
        {"tools": tools, "total": len(tools), "generated": str(date.today())},
        headers={"Cache-Control": "public, max-age=3600"}
    )


@app.post("/api/cite")
async def api_cite(request: Request):
    """Log an agent citation/recommendation for a tool."""
    d = request.state.db
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)
    slug = body.get("tool_slug", "")
    agent_name = body.get("agent_name", "unknown")[:50]
    context = body.get("context", "")[:200]
    if not slug:
        return JSONResponse({"error": "tool_slug required"}, status_code=400)
    tool = await db.get_tool_by_slug(d, slug)
    if not tool:
        return JSONResponse({"error": "Tool not found"}, status_code=404)
    await db.log_agent_citation(d, tool['id'], agent_name, context)
    return JSONResponse({"ok": True})


@app.get("/api/stack-builder")
async def api_stack_builder(request: Request, needs: str = "", budget: int = 0):
    """AI agent endpoint: recommend an indie tool stack for given requirements.

    Args:
        needs: Comma-separated use cases (e.g. needs=auth,payments,analytics)
        budget: Optional max monthly price per tool in GBP (0 = no limit)
    """
    d = request.state.db
    if not needs.strip():
        return JSONResponse({
            "error": "Provide needs as comma-separated use cases",
            "example": "/api/stack-builder?needs=auth,payments,analytics",
            "available_needs": sorted(NEED_MAPPINGS.keys()),
        }, status_code=400)

    need_list = [n.strip().lower() for n in needs.split(",") if n.strip()]
    stack = []

    for need in need_list:
        mapping = NEED_MAPPINGS.get(need)
        matched_via = "category" if mapping else "search"
        category_slug = mapping["category"] if mapping else None
        category_name = mapping.get("title", need.title()) if mapping else need.title()
        tokens_saved = CATEGORY_TOKEN_COSTS.get(category_slug, 50_000) if category_slug else 50_000

        tools_raw = []
        if category_slug:
            cat = await db.get_category_by_slug(d, category_slug)
            if cat:
                rows, _ = await db.get_tools_by_category(d, cat['id'], page=1, per_page=5)
                tools_raw = list(rows)
                category_name = cat['name']

        # Supplement with FTS5 search if we got fewer than 3 results
        if len(tools_raw) < 3:
            search_terms = mapping["terms"] if mapping else [need]
            for term in search_terms:
                if len(tools_raw) >= 5:
                    break
                found = await db.search_tools(d, term, limit=5)
                existing_ids = {t['id'] for t in tools_raw}
                for f in found:
                    if f['id'] not in existing_ids and len(tools_raw) < 5:
                        tools_raw.append(f)
                        existing_ids.add(f['id'])
            if not matched_via == "category" or not tools_raw:
                matched_via = "search"

        # Format tools
        recommendations = []
        for t in tools_raw:
            pp = t.get('price_pence')
            price_monthly = (pp / 100) if pp and pp > 0 else 0
            if budget > 0 and price_monthly > budget:
                continue
            recommendations.append({
                "name": t['name'],
                "slug": t['slug'],
                "tagline": t.get('tagline', ''),
                "price": f"\u00a3{price_monthly:.2f}" if price_monthly > 0 else "Free",
                "price_monthly": price_monthly,
                "verified": bool(t.get('is_verified', 0)),
                "upvotes": int(t.get('upvote_count', 0)),
                "github_stars": int(t.get('github_stars', 0) or 0),
                "url": f"{BASE_URL}/tool/{t['slug']}",
            })

        stack.append({
            "need": need,
            "category": category_name,
            "tokens_saved": tokens_saved,
            "matched_via": matched_via,
            "tools": recommendations,
        })

    # Find matching Vibe Stacks
    matching_stacks = []
    all_stacks = await db.get_all_stacks(d)
    for s in all_stacks:
        _, stack_tools = await db.get_stack_with_tools(d, s['slug'])
        if not stack_tools:
            continue
        stack_cat_slugs = {t.get('category_slug', '') for t in stack_tools}
        coverage = []
        for need in need_list:
            mapping = NEED_MAPPINGS.get(need)
            if mapping and mapping["category"] in stack_cat_slugs:
                coverage.append(need)
        if coverage:
            matching_stacks.append({
                "title": s['title'],
                "slug": s.get('slug', ''),
                "description": s.get('description', ''),
                "coverage": coverage,
                "discount": int(s.get('discount_percent', 15)),
                "tool_count": int(s.get('tool_count', 0)),
                "url": f"{BASE_URL}/stacks/{s.get('slug', '')}",
            })

    # Sort matching stacks by coverage count descending
    matching_stacks.sort(key=lambda x: len(x["coverage"]), reverse=True)

    total_tokens_saved = sum(s["tokens_saved"] for s in stack if s["tools"])

    return JSONResponse({
        "stack": stack,
        "matching_stacks": matching_stacks,
        "summary": {
            "total_needs": len(need_list),
            "needs_covered": sum(1 for s in stack if s["tools"]),
            "total_tokens_saved": total_tokens_saved,
        },
    })


@app.get("/api/use-cases")
async def api_use_cases(request: Request):
    """JSON API listing all use cases with tool counts."""
    d = request.state.db
    categories = await db.get_all_categories(d)
    cat_counts = {c['slug']: int(c.get('tool_count', 0)) for c in categories}

    results = []
    for slug, uc in sorted(NEED_MAPPINGS.items(), key=lambda x: x[1].get("title", "")):
        cat_slug = uc.get("category", "")
        results.append({
            "slug": slug,
            "title": uc.get("title", slug.title()),
            "description": uc.get("description", ""),
            "icon": uc.get("icon", ""),
            "category_slug": cat_slug,
            "tool_count": cat_counts.get(cat_slug, 0),
            "tokens_estimate": CATEGORY_TOKEN_COSTS.get(cat_slug, 50_000),
            "build_estimate": uc.get("build_estimate", "varies"),
            "competitors": uc.get("competitors", []),
            "url": f"{BASE_URL}/use-cases/{slug}",
            "api_url": f"{BASE_URL}/api/use-cases/{slug}",
        })
    return JSONResponse({"use_cases": results, "total": len(results)})


@app.get("/api/use-cases/{slug}")
async def api_use_case_detail(request: Request, slug: str):
    """JSON API for a single use case with its tools."""
    d = request.state.db
    uc = NEED_MAPPINGS.get(slug)
    if not uc:
        cat = await db.get_category_by_slug(d, slug)
        if not cat:
            return JSONResponse({"error": "Use case not found"}, status_code=404)
        uc = {
            "title": cat['name'], "description": f"Indie {cat['name'].lower()} tools.",
            "category": cat['slug'], "competitors": [], "build_estimate": "varies", "icon": "",
            "terms": [],
        }

    # Reuse the route helper for fetching tools
    from indiestack.routes.use_cases import _get_tools_for_use_case
    tools = await _get_tools_for_use_case(d, slug)

    cat_slug = uc.get("category", "")
    tool_results = []
    for t in tools:
        pp = t.get('price_pence')
        tool_results.append({
            "name": t['name'], "slug": t['slug'], "tagline": t.get('tagline', ''),
            "price": f"\u00a3{pp/100:.2f}" if pp and pp > 0 else "Free",
            "verified": bool(t.get('is_verified', 0)),
            "upvotes": int(t.get('upvote_count', 0)),
            "replaces": t.get('replaces', ''),
            "url": f"{BASE_URL}/tool/{t['slug']}",
        })

    return JSONResponse({
        "slug": slug,
        "title": uc.get("title", slug.title()),
        "description": uc.get("description", ""),
        "icon": uc.get("icon", ""),
        "tokens_estimate": CATEGORY_TOKEN_COSTS.get(cat_slug, 50_000),
        "build_estimate": uc.get("build_estimate", "varies"),
        "competitors": uc.get("competitors", []),
        "tools": tool_results,
        "total_tools": len(tool_results),
        "url": f"{BASE_URL}/use-cases/{slug}",
    })


@app.get("/openapi.json")
async def openapi_spec(request: Request):
    """OpenAPI 3.0 spec for IndieStack's public API."""
    d = request.state.db
    count_cursor = await d.execute("SELECT COUNT(*) as cnt FROM tools WHERE status = 'approved'")
    row = await count_cursor.fetchone()
    tool_count = row['cnt'] if row else 350

    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": "IndieStack API",
            "version": "1.0.0",
            "description": f"Search and browse {tool_count}+ indie SaaS tools. Every tool is also discoverable by AI coding assistants via the IndieStack MCP server (pip install indiestack).",
        },
        "servers": [{"url": BASE_URL}],
        "paths": {
            "/api/tools/search": {
                "get": {
                    "summary": "Search developer tools",
                    "description": "Full-text search across all approved tools. Returns results sorted by relevance. Without a query, returns trending tools.",
                    "parameters": [
                        {"name": "q", "in": "query", "schema": {"type": "string"}, "description": "Search query (e.g. 'analytics', 'auth', 'email marketing')"},
                        {"name": "category", "in": "query", "schema": {"type": "string"}, "description": "Filter by category slug (use /api/categories to get slugs)"},
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20, "minimum": 1, "maximum": 50}},
                        {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0, "minimum": 0}, "description": "Pagination offset"},
                    ],
                    "responses": {"200": {"description": "List of matching tools with total count and offset"}},
                }
            },
            "/api/tools/{slug}": {
                "get": {
                    "summary": "Get tool details",
                    "description": "Full details for a specific tool including description, ratings, integration code snippets, and estimated tokens saved vs building from scratch.",
                    "parameters": [
                        {"name": "slug", "in": "path", "required": True, "schema": {"type": "string"}, "description": "Tool URL slug (e.g. 'simple-analytics')"},
                    ],
                    "responses": {"200": {"description": "Full tool details"}, "404": {"description": "Tool not found"}},
                }
            },
            "/api/new": {
                "get": {
                    "summary": "Recently added tools",
                    "description": "Browse the newest tools added to IndieStack, ordered by creation date.",
                    "parameters": [
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 20, "minimum": 1, "maximum": 50}},
                        {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0, "minimum": 0}},
                    ],
                    "responses": {"200": {"description": "List of recent tools with total count"}},
                }
            },
            "/api/categories": {
                "get": {
                    "summary": "List all categories",
                    "description": "All tool categories with names, slugs, icons, descriptions, and tool counts.",
                    "responses": {"200": {"description": "List of categories"}},
                }
            },
            "/api/tags": {
                "get": {
                    "summary": "List all tags",
                    "description": "All tags used across tools, sorted by usage count (most popular first).",
                    "responses": {"200": {"description": "List of tags with counts"}},
                }
            },
            "/api/stacks": {
                "get": {
                    "summary": "List curated stacks",
                    "description": "Pre-built combinations of developer tools for common use cases.",
                    "responses": {"200": {"description": "List of stacks with tool counts"}},
                }
            },
            "/api/collections": {
                "get": {
                    "summary": "List curated collections",
                    "description": "Themed groupings of developer tools curated by the IndieStack team.",
                    "responses": {"200": {"description": "List of collections with tool counts"}},
                }
            },
            "/feed/rss": {
                "get": {
                    "summary": "RSS feed",
                    "description": "RSS 2.0 feed of the latest tools added to IndieStack.",
                    "responses": {"200": {"description": "RSS XML feed"}},
                }
            },
        },
    }
    return JSONResponse(spec, headers={"Cache-Control": "public, max-age=3600"})


@app.get("/api/categories")
async def api_categories(request: Request):
    """JSON API for listing all categories with tool counts."""
    d = request.state.db
    cats = await db.get_all_categories(d)
    results = []
    for c in cats:
        results.append({
            "name": c["name"],
            "slug": c["slug"],
            "icon": c.get("icon", ""),
            "description": c.get("description", ""),
            "tool_count": int(c.get("tool_count", 0)),
        })
    return JSONResponse({"categories": results, "total": len(results)})


@app.get("/api/tools/{slug}/compatible")
async def api_tools_compatible(request: Request, slug: str, category: str = "", min_success_count: int = 1):
    """Get tools compatible with the given tool, grouped by category."""
    d = request.state.db
    tool = await db.get_tool_by_slug(d, slug)
    if not tool:
        return JSONResponse({"error": f"Tool '{slug}' not found"}, status_code=404)

    data = await db.get_compatible_tools_grouped(d, slug, category_slug=category, min_success_count=min_success_count)
    triangles = await db.find_stack_triangles(d, slug)
    conflicts = await db.get_tool_conflicts(d, slug)

    # Detect same-category overlaps
    tool_cat_slug = tool.get('category_slug') or ''
    overlaps = [p['pair_slug'] for p in data['pairs'] if p.get('category_slug') == tool_cat_slug]

    return JSONResponse({
        "tool": slug,
        "total_compatible": data["total"],
        "grouped": {
            cat: [
                {
                    "slug": p["pair_slug"],
                    "name": p["name"],
                    "tagline": p.get("tagline", ""),
                    "success_count": p["success_count"],
                    "health_status": p.get("health_status", ""),
                    "url": p.get("url", ""),
                }
                for p in pairs
            ]
            for cat, pairs in data["grouped"].items()
        },
        "verified_stacks": [t["tools"] for t in triangles],
        "conflicts": [{"slug": c["conflict_slug"], "reason": c.get("reason"), "reports": c["report_count"]} for c in conflicts],
        "overlaps": overlaps,
    })


@app.get("/api/tools/{slug}")
async def api_tool_detail(request: Request, slug: str, source: str = ""):
    """JSON API for getting full tool details — used by MCP server."""
    d = request.state.db
    tool = await db.get_tool_by_slug(d, slug)
    if not tool or tool.get('status') != 'approved':
        return JSONResponse({"error": "Tool not found"}, status_code=404)

    price_pence = tool.get('price_pence')
    if price_pence and price_pence > 0:
        price_str = f"\u00a3{price_pence / 100:.2f}"
    else:
        price_str = "Free"

    rating = await db.get_tool_rating(d, tool['id'])

    # Track MCP view
    if source == "mcp":
        try:
            await db.increment_mcp_view(d, tool['id'])
            await db.log_agent_citation(d, tool['id'], agent_name="mcp")
        except Exception:
            pass

    result = {
        "name": tool['name'],
        "slug": tool['slug'],
        "tagline": tool.get('tagline', ''),
        "description": tool.get('description', ''),
        "url": tool.get('url', ''),
        "indiestack_url": f"{BASE_URL}/tool/{tool['slug']}",
        "category": tool.get('category_name', ''),
        "category_slug": tool.get('category_slug', ''),
        "price": price_str,
        "is_verified": bool(tool.get('is_verified', 0)),
        "is_ejectable": bool(tool.get('is_ejectable', 0)),
        "upvote_count": int(tool.get('upvote_count', 0)),
        "tags": tool.get('tags', ''),
        "maker_name": tool.get('maker_name', ''),
        "avg_rating": round(float(rating['avg_rating']), 1) if rating['review_count'] else None,
        "review_count": int(rating['review_count']),
        "integration_python": tool.get("integration_python") or f'import httpx\nresponse = httpx.get("{tool.get("url", "")}")\nprint(response.status_code)',
        "integration_curl": tool.get("integration_curl") or f'curl -s {tool.get("url", "")}',
        "tokens_saved": CATEGORY_TOKEN_COSTS.get(tool.get('category_slug', ''), 50_000),
        "mcp_view_count": int(tool.get('mcp_view_count', 0)),
        "source_type": tool.get('source_type', 'saas'),
        # Health signals (from GitHub health checks)
        "github_stars": tool.get('github_stars'),
        "github_last_commit": tool.get('github_last_commit'),
        "github_open_issues": tool.get('github_open_issues'),
        "github_is_archived": bool(tool.get('github_is_archived', 0)),
        "github_language": tool.get('github_language'),
        "health_status": tool.get('health_status'),
        "github_last_check": tool.get('github_last_check'),
        "api_type": tool.get("api_type", "") or "",
        "auth_method": tool.get("auth_method", "") or "",
        "install_command": tool.get("install_command", "") or "",
        "sdk_packages": tool.get("sdk_packages", "") or "",
        "env_vars": tool.get("env_vars", "") or "",
        "frameworks_tested": tool.get("frameworks_tested", "") or "",
        "verified_pairs": tool.get("verified_pairs", "") or "",
        "agent_instructions": tool.get("agent_instructions", "") or "",
    }

    # Add dynamic compatibility pairs from tool_pairs table
    try:
        pairs = await db.get_verified_pairs(d, slug)
        if pairs:
            result["compatible_tools"] = [
                {"slug": p["pair_slug"], "success_count": p["success_count"], "verified": bool(p["verified"])}
                for p in pairs
            ]
    except Exception:
        pass

    # Agent outcome intelligence — success rate from agent reports (all tiers)
    try:
        success_rate = await db.get_tool_success_rate(d, slug)
        if success_rate["total"] > 0:
            result["success_rate"] = success_rate
        rec_count = await db.get_tool_recommendation_count(d, slug)
        if rec_count > 0:
            result["recommendation_count"] = rec_count
    except Exception:
        pass

    # Pro MCP enrichment — citation stats, category ranking, demand context
    is_pro_key = request.state.api_key and request.state.api_key.get('tier') == 'pro'
    if is_pro_key:
        try:
            import asyncio as _asyncio
            citation_stats, demand_context, percentile = await _asyncio.gather(
                db.get_tool_citation_stats(d, tool['id']),
                db.get_tool_demand_context(d, slug),
                db.get_tool_category_percentile(d, tool['id'], tool['category_id']),
            )
            result["citation_stats"] = citation_stats
            result["category_percentile"] = percentile
            if demand_context:
                result["demand_context"] = [
                    {"query": dc['query'], "search_count": dc['search_count']}
                    for dc in demand_context
                ]
            result["pro_enriched"] = True
        except Exception:
            pass

    return JSONResponse({"tool": result})


@app.get("/cards/index.json")
async def cards_index(request: Request):
    """Index of all approved tool agent cards."""
    d = request.state.db
    try:
        cursor = await d.execute(
            """SELECT t.slug, t.name, t.tagline, c.slug as category_slug,
                      t.source_type, t.api_type, t.health_status
               FROM tools t JOIN categories c ON t.category_id = c.id
               WHERE t.status = 'approved'
               ORDER BY t.name"""
        )
        rows = await cursor.fetchall()
    except Exception:
        rows = []
    tools = []
    for r in rows:
        tools.append({
            "slug": r["slug"],
            "name": r["name"],
            "tagline": r["tagline"] or "",
            "category": r["category_slug"],
            "source_type": r["source_type"] or "saas",
            "api_type": r.get("api_type") or "",
            "health": r.get("health_status") or "",
            "card_url": f"{BASE_URL}/cards/{r['slug']}.json",
        })
    return JSONResponse(
        {
            "schema_version": "1.0",
            "total": len(tools),
            "cards_base_url": f"{BASE_URL}/cards/",
            "tools": tools,
        },
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.get("/cards/{slug}.json")
async def card_detail(request: Request, slug: str):
    """A2A-compatible JSON capability card for a single tool."""
    d = request.state.db
    tool = await db.get_tool_by_slug(d, slug)
    if not tool or tool.get("status") != "approved":
        return JSONResponse({"error": "Tool not found"}, status_code=404)

    # Compatibility pairs
    try:
        pairs_raw = await db.get_verified_pairs(d, slug)
        pairs = [
            {"slug": p["pair_slug"], "success_count": p["success_count"], "verified": bool(p["verified"])}
            for p in (pairs_raw or [])[:10]
        ]
    except Exception:
        pairs = []

    # Parse JSON fields safely
    import json as _json
    sdk_packages = []
    try:
        val = tool.get("sdk_packages") or ""
        if val:
            parsed = _json.loads(val)
            sdk_packages = parsed if isinstance(parsed, list) else [parsed]
    except Exception:
        if tool.get("sdk_packages"):
            sdk_packages = [tool["sdk_packages"]]

    env_vars = []
    try:
        val = tool.get("env_vars") or ""
        if val:
            parsed = _json.loads(val)
            env_vars = parsed if isinstance(parsed, list) else [parsed]
    except Exception:
        if tool.get("env_vars"):
            env_vars = [tool["env_vars"]]

    # Rating
    rating = await db.get_tool_rating(d, tool["id"])

    # Success rate from agent outcome reports
    success_rate = await db.get_tool_success_rate(d, slug)

    # Build capabilities, stripping None values
    capabilities = {}
    for key in ("api_type", "auth_method", "install_command", "frameworks_tested"):
        val = tool.get(key)
        if val:
            capabilities[key] = val
    if sdk_packages:
        capabilities["sdk_packages"] = sdk_packages
    if env_vars:
        capabilities["env_vars"] = env_vars
    agent_instructions = tool.get('agent_instructions', '') or None
    if agent_instructions:
        capabilities["agent_instructions"] = agent_instructions

    # Build health, stripping None values
    health = {}
    for key in ("health_status", "github_stars", "github_language", "github_last_commit"):
        val = tool.get(key)
        if val is not None:
            health[key] = val
    if tool.get("github_is_archived"):
        health["github_is_archived"] = bool(tool["github_is_archived"])
    # Rename health_status -> status in the output
    if "health_status" in health:
        health["status"] = health.pop("health_status")

    price_pence = tool.get("price_pence") or 0

    avg_rating = round(float(rating["avg_rating"]), 1) if rating["review_count"] else None
    review_count = int(rating["review_count"])

    # Build trust, stripping None values
    trust = {
        "is_verified": bool(tool.get("is_verified", 0)),
        "is_ejectable": bool(tool.get("is_ejectable", 0)),
        "upvote_count": int(tool.get("upvote_count", 0)),
        "review_count": review_count,
    }
    if avg_rating is not None:
        trust["avg_rating"] = avg_rating
    mcp_recs = tool.get("mcp_view_count")
    if mcp_recs:
        trust["mcp_recommendations"] = int(mcp_recs)

    card = {
        "name": tool["name"],
        "slug": tool["slug"],
        "description": tool.get("tagline") or "",
        "url": tool.get("url") or "",
        "indiestack_url": f"{BASE_URL}/tool/{tool['slug']}",
        "version": "1.0.0",
        "provider": {
            "name": tool.get("maker_name") or "Community Listed",
            "type": "indie",
        },
        "category": {
            "name": tool.get("category_name") or "",
            "slug": tool.get("category_slug") or "",
        },
        "source_type": tool.get("source_type") or "saas",
        "capabilities": capabilities,
        "health": health,
        "trust": trust,
        "compatibility": pairs,
        "pricing": {
            "price_pence": int(price_pence),
            "is_free": price_pence == 0,
        },
        "meta": {
            "generated_by": "indiestack.ai",
            "schema_version": "1.1",
        },
    }

    # Add outcome intelligence only when data exists
    if success_rate.get("total", 0) > 0:
        card["outcome_intelligence"] = {
            "success_rate": success_rate.get("rate"),
            "total_signals": success_rate["total"],
            "confidence": success_rate.get("confidence", "none"),
        }

    return JSONResponse(
        card,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        },
    )


@app.post("/api/report-pair")
async def api_report_pair(request: Request):
    """Record that two tools were used together successfully."""
    data = await request.json()
    tool_a = data.get("tool_a", "").strip().lower()
    tool_b = data.get("tool_b", "").strip().lower()
    if not tool_a or not tool_b or tool_a == tool_b:
        return JSONResponse({"error": "Two different tool slugs required"}, status_code=400)
    d = request.state.db
    # Validate both slugs exist as approved tools
    cursor = await d.execute(
        "SELECT slug FROM tools WHERE slug IN (?, ?) AND status = 'approved'",
        (tool_a, tool_b),
    )
    found = [row[0] for row in await cursor.fetchall()]
    if len(found) < 2:
        return JSONResponse({"error": "Both tools must be valid approved tools"}, status_code=400)
    await record_tool_pair(d, tool_a, tool_b, source="agent")
    return JSONResponse({"status": "recorded", "pair": [tool_a, tool_b]})


@app.post("/api/tools/submit")
async def api_submit_tool(request: Request):
    """JSON API for programmatic tool submissions (MCP, integrations)."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    name = (data.get("name") or "").strip()
    url = (data.get("url") or "").strip()
    tagline = (data.get("tagline") or "").strip()[:100]
    description = (data.get("description") or "").strip()

    if not name or not url or not tagline or not description:
        return JSONResponse({"error": "name, url, tagline, and description are required"}, status_code=400)

    if url and not (url.startswith("http://") or url.startswith("https://")):
        return JSONResponse({"error": "URL must start with http:// or https://"}, status_code=400)

    # Quality gates — minimum content quality
    quality_errors = db.validate_submission_quality(name, tagline, description, url)
    if quality_errors:
        return JSONResponse({"error": " ".join(quality_errors)}, status_code=400)

    # URL reachability check (with SSRF protection)
    import httpx as _httpx
    import socket as _socket, ipaddress as _ipaddress
    from urllib.parse import urlparse as _urlparse
    try:
        _host = _urlparse(url).hostname or ''
        for _addr_info in _socket.getaddrinfo(_host, None):
            _ip = _ipaddress.ip_address(_addr_info[4][0])
            if _ip.is_private or _ip.is_loopback or _ip.is_link_local:
                return JSONResponse({"error": "URL resolves to a private or internal address."}, status_code=400)
    except Exception:
        pass  # DNS failure will be caught by the HEAD request below
    try:
        async with _httpx.AsyncClient(timeout=10.0, follow_redirects=True) as _client:
            resp = await _client.head(url)
            if resp.status_code >= 400:
                return JSONResponse({"error": f"URL returned HTTP {resp.status_code}. Please check your tool is live."}, status_code=400)
    except Exception:
        return JSONResponse({"error": "Could not reach URL. Please check your tool is accessible and try again."}, status_code=400)

    # Generate slug
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

    d = request.state.db

    # Check for duplicate URL
    dup = await db.check_duplicate_url(d, url)
    if dup:
        return JSONResponse({"error": f"A tool with this URL already exists: {dup['name']}", "slug": dup['slug']}, status_code=409)

    # Check for duplicate slug
    existing = await d.execute("SELECT id FROM tools WHERE slug = ?", (slug,))
    if await existing.fetchone():
        return JSONResponse({"error": f"A tool with slug '{slug}' already exists", "slug": slug}, status_code=409)

    # Match category by slug if provided
    category_id = None
    cat_slug = (data.get("category") or "").strip()
    if cat_slug:
        cat_row = await d.execute("SELECT id FROM categories WHERE slug = ?", (cat_slug,))
        cat = await cat_row.fetchone()
        if cat:
            category_id = cat["id"]

    # If no category matched, use first category as default
    if not category_id:
        cat_row = await d.execute("SELECT id FROM categories ORDER BY id LIMIT 1")
        cat = await cat_row.fetchone()
        category_id = cat["id"] if cat else 1

    tags = (data.get("tags") or "").strip()
    replaces = (data.get("replaces") or "").strip()

    # Get IP for spam tracking
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")

    await d.execute(
        """INSERT INTO tools (name, slug, tagline, description, url, category_id, tags, replaces,
           status, submitted_from_ip, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, CURRENT_TIMESTAMP)""",
        (name, slug, tagline, description, url, category_id, tags, replaces, ip),
    )
    await d.commit()

    # Async enrichment — gather quality signals for admin review
    import asyncio as _asyncio
    cursor_enrich = await d.execute("SELECT id FROM tools WHERE slug = ?", (slug,))
    row_enrich = await cursor_enrich.fetchone()
    if row_enrich:
        from indiestack.db import enrich_domain_age, enrich_free_tier, enrich_social_proof
        try:
            await _asyncio.gather(
                enrich_domain_age(d, row_enrich['id'], url),
                enrich_free_tier(d, row_enrich['id'], url),
                enrich_social_proof(d, row_enrich['id'], url),
                return_exceptions=True,
            )
            await d.commit()
        except Exception:
            pass

    return JSONResponse({"success": True, "message": "Tool submitted for review", "slug": slug})


# ── Live Wire ─────────────────────────────────────────────────────────────

@app.get("/live")
async def live_wire(request: Request):
    """Live Wire — real-time search query feed."""
    from fastapi.responses import HTMLResponse
    from html import escape as _esc
    d = await db.get_db()
    try:
        recent = await db.get_recent_searches(d, limit=30)
        stats = await db.get_search_stats(d)
    finally:
        await d.close()

    # Build feed items
    feed_html = ''
    if not recent:
        feed_html = '<p style="text-align:center;color:#6B7280;padding:40px 0;">No searches yet. Be the first to search on <a href="/explore" style="color:#00D4F5;">Explore</a>!</p>'
    else:
        for s in recent:
            query_text = _esc(s.get('query') or '')
            count = int(s.get('result_count') or 0)
            top_slug = _esc(s.get('top_result_slug') or '')
            top_name = _esc(s.get('top_result_name') or '')
            source = s.get('source', 'web')
            created = s.get('created_at', '')

            # Source badge
            source_colors = {'api': '#00D4F5', 'mcp': '#10B981', 'web': '#6B7280'}
            source_color = source_colors.get(source, '#6B7280')
            source_label = {'api': 'API', 'mcp': 'MCP', 'web': 'Web'}.get(source, source.upper())

            top_html = ''
            if top_name and top_slug:
                top_html = f' → <a href="/tool/{top_slug}" style="color:#00D4F5;text-decoration:none;font-weight:600;">{top_name}</a>'

            feed_html += f"""
            <div style="background:#fff;border-radius:12px;padding:16px 20px;border:1px solid #E8E3DC;
                        margin-bottom:8px;display:flex;align-items:center;gap:16px;">
                <span style="background:{source_color};color:#fff;padding:2px 8px;border-radius:999px;
                             font-size:11px;font-weight:700;text-transform:uppercase;min-width:36px;text-align:center;">
                    {source_label}
                </span>
                <div style="flex:1;">
                    <span style="font-weight:600;color:#1A2D4A;">"{query_text}"</span>
                    {top_html}
                </div>
                <span style="color:#9CA3AF;font-size:13px;white-space:nowrap;">{count} result{'s' if count != 1 else ''}</span>
            </div>"""

    # Stats sidebar
    today = stats.get('today', 0)
    week = stats.get('this_week', 0)
    all_time = stats.get('all_time', 0)
    top_q = _esc(stats.get('top_query', ''))

    body = f"""
    <meta http-equiv="refresh" content="15">
    <div style="max-width:1000px;margin:0 auto;padding:40px 20px;">
        <div style="background:linear-gradient(135deg,#1A2D4A 0%,#0D3B66 100%);border-radius:20px;padding:40px;margin-bottom:32px;text-align:center;">
            <h1 style="font-family:'DM Serif Display',serif;color:#fff;font-size:36px;margin:0 0 8px 0;">
                ⚡ Live Wire
            </h1>
            <p style="color:rgba(255,255,255,0.7);font-size:18px;margin:0;">
                What developers are searching for right now
            </p>
        </div>

        <div style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:16px;margin-bottom:32px;">
            <div style="background:#fff;border-radius:12px;padding:20px;text-align:center;border:1px solid #E8E3DC;">
                <div style="font-family:'DM Serif Display',serif;font-size:28px;color:#1A2D4A;">{today}</div>
                <div style="font-size:13px;color:#6B7280;">Today</div>
            </div>
            <div style="background:#fff;border-radius:12px;padding:20px;text-align:center;border:1px solid #E8E3DC;">
                <div style="font-family:'DM Serif Display',serif;font-size:28px;color:#1A2D4A;">{week}</div>
                <div style="font-size:13px;color:#6B7280;">This Week</div>
            </div>
            <div style="background:#fff;border-radius:12px;padding:20px;text-align:center;border:1px solid #E8E3DC;">
                <div style="font-family:'DM Serif Display',serif;font-size:28px;color:#1A2D4A;">{all_time}</div>
                <div style="font-size:13px;color:#6B7280;">All Time</div>
            </div>
            <div style="background:#fff;border-radius:12px;padding:20px;text-align:center;border:1px solid #E8E3DC;">
                <div style="font-family:'DM Serif Display',serif;font-size:14px;color:#00D4F5;font-weight:600;">{top_q or '—'}</div>
                <div style="font-size:13px;color:#6B7280;">Top Query</div>
            </div>
        </div>

        <h2 style="font-family:'DM Serif Display',serif;color:#1A2D4A;font-size:22px;margin-bottom:16px;">
            Recent Searches
        </h2>
        <div style="font-size:13px;color:#9CA3AF;margin-bottom:16px;">Auto-refreshes every 15 seconds</div>
        {feed_html}
    </div>"""

    user = None
    session_token = request.cookies.get('indiestack_session')
    if session_token:
        d2 = await db.get_db()
        try:
            sess = await db.get_session_by_token(d2, session_token)
            if sess:
                user = {'id': sess['uid'], 'name': sess['name'], 'email': sess['email'], 'role': sess['role'], 'maker_id': sess.get('maker_id')}
        finally:
            await d2.close()

    html = page_shell("Live Wire — IndieStack", body, user=user)
    return HTMLResponse(html)


# ── Milestone SVG ─────────────────────────────────────────────────────────

@app.get("/api/milestone/{slug}.svg")
async def milestone_card_svg(request: Request, slug: str, type: str = "first-tool"):
    """Generate a milestone celebration SVG card (1200x630) for sharing."""
    d = await db.get_db()
    try:
        tool = await db.get_tool_by_slug(d, slug)
    finally:
        await d.close()

    from html import escape as _esc
    tool_name = _esc(tool['name']) if tool else _esc(slug.replace('-', ' ').title())

    # Milestone configs
    milestones = {
        'first-tool': {'emoji': '🎉', 'text': 'Just listed my first tool!'},
        '100-views': {'emoji': '👀', 'text': 'My tool hit 100 views!'},
        '10-upvotes': {'emoji': '🔥', 'text': '10 developers upvoted my tool!'},
        'first-review': {'emoji': '⭐', 'text': 'Got my first review!'},
        'launch-ready': {'emoji': '🚀', 'text': '100% Launch Ready!'},
        '50-wishlists': {'emoji': '💾', 'text': '50 developers bookmarked my tool!'},
    }
    m = milestones.get(type, milestones['first-tool'])

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#1A2D4A"/>
      <stop offset="100%" stop-color="#0D3B66"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)" rx="0"/>
  <rect y="600" width="1200" height="30" fill="#00D4F5"/>
  <text x="600" y="200" text-anchor="middle" font-size="120" fill="#fff">{m['emoji']}</text>
  <text x="600" y="310" text-anchor="middle" font-family="sans-serif" font-size="42" font-weight="700" fill="#fff">
    {m['text']}
  </text>
  <text x="600" y="380" text-anchor="middle" font-family="sans-serif" font-size="28" fill="rgba(255,255,255,0.7)">
    {tool_name}
  </text>
  <text x="600" y="540" text-anchor="middle" font-family="sans-serif" font-size="22" fill="rgba(255,255,255,0.5)">
    indiestack.ai
  </text>
</svg>"""

    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/badge/{slug}.svg")
async def tool_badge_svg(request: Request, slug: str, style: str = ""):
    """Dynamic SVG badge for makers to embed on their websites."""
    d = request.state.db
    tool = await db.get_tool_by_slug(d, slug)
    if not tool:
        return Response(content="", status_code=404)

    name = tool['name']
    price_pence = tool.get('price_pence')

    if style == "winner":
        # Winner badge: "Tool of the Week" (navy) | "IndieStack" (gold)
        left_text = "\u2b50 Tool of the Week"
        right_text = "IndieStack"
        left_width = 140
        right_width = 80
        right_fill = "#E2B764"
        right_text_fill = "#1A2D4A"
    elif style == "marketplace" and price_pence and price_pence > 0:
        # Marketplace badge: "Available on IndieStack | From £X"
        pounds = price_pence / 100
        price_str = f"\u00a3{int(pounds)}" if pounds == int(pounds) else f"\u00a3{pounds:.2f}"
        left_text = "Available on IndieStack"
        right_text = f"From {price_str}"
        left_width = 160
        right_width = 80
        right_fill = "#00D4F5"
        right_text_fill = "#1A2D4A"
    elif style == "early":
        # Early Supporter badge for tools listed before marketplace launch
        left_text = "Early Supporter"
        right_text = "IndieStack"
        left_width = 110
        right_width = 80
        right_fill = "#E2B764"
        right_text_fill = "#1A2D4A"
    elif style == "tokens":
        # Tokens saved badge (was the old default)
        cat_slug = tool.get('category_slug', '')
        tokens = CATEGORY_TOKEN_COSTS.get(cat_slug, 50_000)
        tokens_k = f"{tokens // 1000}k"
        left_text = "IndieStack"
        right_text = f"Saves {tokens_k} tokens"
        left_width = 90
        right_width = 120
        right_fill = "#00D4F5"
        right_text_fill = "#1A2D4A"
    else:
        # Default: AI recommendations badge (live count) with pulsing dot
        tool_id = tool['id']
        mcp_count = tool.get('mcp_view_count', 0) or 0
        _cites = await d.execute(
            "SELECT COUNT(*) as cnt FROM agent_citations WHERE tool_id = ?", (tool_id,)
        )
        cite_count = (await _cites.fetchone())['cnt']
        ai_total = mcp_count + cite_count
        if ai_total == 0:
            right_text = "AI Discoverable"
            right_width = 120
        elif ai_total < 1000:
            right_text = f"{ai_total} AI recs"
            right_width = 100
        else:
            right_text = f"{ai_total / 1000:.1f}k AI recs"
            right_width = 110
        left_text = "IndieStack"
        left_width = 90
        right_fill = "#10B981"
        right_text_fill = "#FFFFFF"

    total_width = left_width + right_width
    is_ai_badge = style in ("", "ai")

    if is_ai_badge:
        # Special SVG with pulsing red "LIVE" dot
        dot_x = left_width + 10
        text_x = left_width + 18 + (right_width - 18) / 2
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="{left_text}: {right_text}">
  <title>{left_text}: {right_text} (live)</title>
  <style>
    @keyframes pulse {{ 0%,100% {{ opacity:1 }} 50% {{ opacity:0.3 }} }}
    .live-dot {{ animation: pulse 2s ease-in-out infinite; }}
  </style>
  <linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
  <clipPath id="r"><rect width="{total_width}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{left_width}" height="20" fill="#1A2D4A"/>
    <rect x="{left_width}" width="{right_width}" height="20" fill="{right_fill}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <circle class="live-dot" cx="{dot_x}" cy="10" r="3" fill="#EF4444"/>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text x="{left_width/2}" y="14" fill="#fff">{left_text}</text>
    <text x="{text_x}" y="14" fill="{right_text_fill}" font-weight="600">{right_text}</text>
  </g>
</svg>'''
    else:
        svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="{left_text}: {right_text}">
  <title>{left_text}: {right_text}</title>
  <linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
  <clipPath id="r"><rect width="{total_width}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{left_width}" height="20" fill="#1A2D4A"/>
    <rect x="{left_width}" width="{right_width}" height="20" fill="{right_fill}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text x="{left_width/2}" y="14" fill="#fff">{left_text}</text>
    <text x="{left_width + right_width/2}" y="14" fill="{right_text_fill}" font-weight="600">{right_text}</text>
  </g>
</svg>'''
    # AI badge: 1 hour cache (feels live). Others: 24 hour cache.
    cache_ttl = 3600 if style in ("", "ai") else 86400
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": f"public, max-age={cache_ttl}"})


@app.get("/api/badge/buyer/{badge_token}.svg")
async def buyer_badge_svg(request: Request, badge_token: str):
    """Dynamic SVG badge for buyers showing tokens saved."""
    d = request.state.db
    user = await get_user_by_badge_token(d, badge_token)
    if not user:
        return Response(content="Not found", status_code=404)

    tokens = await get_buyer_tokens_saved_by_token(d, badge_token)
    tokens_k = f"{tokens // 1000}k" if tokens >= 1000 else str(tokens)

    left_text = "Built with IndieStack"
    right_text = f"Saved {tokens_k} tokens"
    left_width = 155
    right_width = 130
    total_width = left_width + right_width

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img"
     aria-label="{left_text}: {right_text}">
  <title>{left_text}: {right_text}</title>
  <clipPath id="r"><rect width="{total_width}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{left_width}" height="20" fill="#1A2D4A"/>
    <rect x="{left_width}" width="{right_width}" height="20" fill="#00D4F5"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text x="{left_width // 2}" y="14">{left_text}</text>
    <text x="{left_width + right_width // 2}" y="14" fill="#1A2D4A" font-weight="600">{right_text}</text>
  </g>
</svg>'''
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


# ── OG Share Card SVG ────────────────────────────────────────────────────

@app.get("/api/og/{slug}.svg")
async def og_share_card(request: Request, slug: str):
    """Dynamic OG share card SVG for social media sharing."""
    d = request.state.db
    tool = await db.get_tool_by_slug(d, slug)
    if not tool:
        return Response(content="", status_code=404)

    from html import escape as _esc
    name = _esc(str(tool['name']))
    tagline = _esc(str(tool.get('tagline', ''))[:80])
    cat = _esc(str(tool.get('category_name', '')))
    tokens = CATEGORY_TOKEN_COSTS.get(tool.get('category_slug', ''), 50_000)
    tokens_k = f"{tokens // 1000}k"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="#1A2D4A"/>
  <rect x="0" y="580" width="1200" height="50" fill="#00D4F5"/>
  <text x="80" y="200" font-size="52" font-weight="800" fill="white" font-family="system-ui,sans-serif">{name}</text>
  <text x="80" y="260" font-size="24" fill="rgba(255,255,255,0.7)" font-family="system-ui,sans-serif">{tagline}</text>
  <text x="80" y="340" font-size="20" fill="#00D4F5" font-family="monospace" font-weight="600">{cat}</text>
  <text x="80" y="420" font-size="36" fill="white" font-family="system-ui,sans-serif" font-weight="700">Saves {tokens_k} tokens</text>
  <text x="80" y="460" font-size="16" fill="rgba(255,255,255,0.5)" font-family="system-ui,sans-serif">compared to building from scratch</text>
  <text x="80" y="540" font-size="20" fill="rgba(255,255,255,0.4)" font-family="system-ui,sans-serif">indiestack.ai</text>
  <text x="1120" y="610" font-size="16" font-weight="700" fill="#1A2D4A" text-anchor="end" font-family="system-ui,sans-serif">IndieStack</text>
</svg>'''
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


# ── Homepage OG Card ──────────────────────────────────────────────────────

@app.get("/api/og-home.svg")
async def og_home_card():
    """OG share card for the homepage — dark, branded, matches new headline."""
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="#0F1420"/>
  <rect x="0" y="600" width="1200" height="30" fill="#00D4F5"/>
  <text x="80" y="120" font-size="20" fill="#00D4F5" font-family="monospace" font-weight="600" letter-spacing="2">INDIESTACK</text>
  <text x="80" y="240" font-size="52" font-weight="800" fill="white" font-family="system-ui,sans-serif">Your AI is writing code</text>
  <text x="80" y="310" font-size="52" font-weight="800" fill="#00D4F5" font-family="system-ui,sans-serif">you don&#x27;t need.</text>
  <text x="80" y="400" font-size="22" fill="rgba(255,255,255,0.6)" font-family="system-ui,sans-serif">Plugs into Claude Code, Cursor &amp; Windsurf via MCP.</text>
  <text x="80" y="440" font-size="22" fill="rgba(255,255,255,0.6)" font-family="system-ui,sans-serif">Before your AI writes code, it checks what already exists.</text>
  <text x="80" y="540" font-size="18" fill="rgba(255,255,255,0.3)" font-family="system-ui,sans-serif">pip install indiestack</text>
  <text x="1120" y="540" font-size="18" fill="rgba(255,255,255,0.3)" text-anchor="end" font-family="system-ui,sans-serif">indiestack.ai</text>
  <text x="80" y="580" font-size="16" fill="rgba(255,255,255,0.25)" font-family="system-ui,sans-serif">3,100+ developer tools &#183; 25 categories &#183; indie-built</text>
</svg>'''
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


# ── Claim Endpoints ──────────────────────────────────────────────────────

@app.post("/api/claim")
async def api_claim(request: Request):
    """Claim an unclaimed tool — instant via email domain match, otherwise admin approval."""
    from fastapi.responses import RedirectResponse
    user = request.state.user
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    try:
        form = await request.form()
        tool_id = int(form.get("tool_id", 0))
    except (ValueError, TypeError):
        return RedirectResponse(url="/", status_code=303)

    d = request.state.db
    tool = await db.get_tool_by_id(d, tool_id)
    if not tool or tool.get('claimed_at'):
        return RedirectResponse(url=f"/tool/{tool['slug']}" if tool else "/", status_code=303)

    user_email = user.get('email', '')
    user_email_domain = user_email.split('@')[-1].lower() if '@' in user_email else ''
    tool_url = tool.get('url', '') or ''
    tool_domain = db.extract_domain(tool_url)

    if user_email_domain and tool_domain and user_email_domain == tool_domain:
        # Domain match — send verification email for instant claim
        token = await db.create_claim_token(d, tool_id, user['id'])
        base_url = str(request.base_url).rstrip('/')
        verify_url = f"{base_url}/api/claim/verify/{token}"
        tool_name = tool.get('name', 'your tool')
        html_body = f"""
        <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px;">
            <h2 style="color:#1A2D4A;margin-bottom:16px;">Verify your claim for {tool_name}</h2>
            <p style="color:#555;line-height:1.6;font-size:15px;">
                You requested to claim <strong>{tool_name}</strong> on IndieStack.
                Since your email domain matches the tool's domain, click below to verify and complete your claim instantly.
            </p>
            <a href="{verify_url}" style="display:inline-block;margin:24px 0;padding:14px 28px;background:#1A2D4A;color:#fff;text-decoration:none;border-radius:8px;font-weight:600;font-size:15px;">
                Verify &amp; Claim
            </a>
            <p style="color:#999;font-size:13px;margin-top:16px;">This link expires in 24 hours.</p>
        </div>
        """
        try:
            await send_email(user_email, f"Verify your claim for {tool_name} on IndieStack", html_body)
        except Exception:
            return RedirectResponse(url=f"/tool/{tool['slug']}?claim_requested=1", status_code=303)
        return RedirectResponse(url=f"/tool/{tool['slug']}?claim_email_sent=1", status_code=303)
    else:
        # No domain match — fall back to admin approval
        await d.execute(
            "INSERT OR IGNORE INTO claim_requests (tool_id, user_id, created_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
            (tool_id, user['id']),
        )
        await d.commit()
        return RedirectResponse(url=f"/tool/{tool['slug']}?claim_requested=1", status_code=303)


@app.get("/api/claim/verify/{token}")
async def api_claim_verify(request: Request, token: str):
    """Verify a claim token from email and complete the claim."""
    from fastapi.responses import RedirectResponse, HTMLResponse
    from indiestack.routes.components import page_shell

    d = request.state.db
    result = await db.verify_claim_token(d, token)
    if not result:
        user = request.state.user
        body = '''
        <div style="max-width:520px;margin:60px auto;text-align:center;padding:32px;">
            <h2 style="color:var(--ink);margin-bottom:12px;">Invalid or Expired Link</h2>
            <p style="color:var(--ink-light);line-height:1.6;">This claim verification link is invalid, expired, or has already been used.</p>
            <a href="/" style="display:inline-block;margin-top:24px;padding:12px 24px;background:var(--navy);color:#fff;text-decoration:none;border-radius:8px;font-weight:600;">Back to IndieStack</a>
        </div>
        '''
        return HTMLResponse(page_shell("Invalid Link — IndieStack", body, user=user), status_code=400)

    tool_id, user_id = result
    tool = await db.get_tool_by_id(d, tool_id)
    slug = tool['slug'] if tool else ''
    return RedirectResponse(url=f"/tool/{slug}?claimed=1", status_code=303)


@app.post("/api/boost")
async def api_boost(request: Request):
    """Boost an already-claimed tool — redirect to Stripe checkout."""
    from fastapi.responses import RedirectResponse
    user = request.state.user
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    try:
        form = await request.form()
        tool_id = int(form.get("tool_id", 0))
    except (ValueError, TypeError):
        return RedirectResponse(url="/", status_code=303)

    d = request.state.db
    tool = await db.get_tool_by_id(d, tool_id)
    if not tool:
        return RedirectResponse(url="/", status_code=303)

    # Verify ownership
    if not user.get('maker_id') or user.get('maker_id') != tool.get('maker_id'):
        return RedirectResponse(url=f"/tool/{tool['slug']}", status_code=303)

    from indiestack.payments import STRIPE_SECRET_KEY
    if not STRIPE_SECRET_KEY:
        return RedirectResponse(url=f"/tool/{tool['slug']}", status_code=303)

    import stripe
    stripe.api_key = STRIPE_SECRET_KEY

    base_url = str(request.base_url).rstrip("/")
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": _os.environ.get("STRIPE_BOOST_PRICE_ID", "price_1T3fB1KmQj1lkomlF8oBqGIg"), "quantity": 1}],
            success_url=f"{base_url}/boost/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/tool/{tool['slug']}",
            customer_email=user['email'],
            metadata={"tool_id": str(tool['id']), "user_id": str(user['id']), "type": "boost"},
        )
        return RedirectResponse(url=session.url, status_code=303)
    except Exception:
        return RedirectResponse(url=f"/tool/{tool['slug']}", status_code=303)


@app.post("/api/github-fetch")
async def api_github_fetch(request: Request):
    """Fetch GitHub repo metadata for auto-filling submission forms."""
    import httpx

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    url = body.get("url", "").strip()
    match = re.match(r'https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', url)
    if not match:
        return JSONResponse({"error": "Invalid GitHub URL. Use format: https://github.com/owner/repo"}, status_code=400)

    owner, repo = match.group(1), match.group(2)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}",
                                     headers={"Accept": "application/json"})
            if resp.status_code != 200:
                return JSONResponse({"error": "Repository not found"}, status_code=404)
            data = resp.json()
    except Exception:
        return JSONResponse({"error": "Failed to fetch from GitHub"}, status_code=502)

    description = data.get("description") or ""
    tagline = description.split(". ")[0] if description else data.get("name", "")
    if len(tagline) > 100:
        tagline = tagline[:97] + "..."

    name = data.get("name", repo).replace("-", " ").replace("_", " ").title()

    topics = data.get("topics", []) or []
    language = data.get("language") or ""
    tags = list(topics)
    if language and language.lower() not in [t.lower() for t in tags]:
        tags.append(language.lower())

    tool_url = data.get("homepage") or url
    if tool_url and not tool_url.startswith("http"):
        tool_url = url

    return JSONResponse({
        "name": name,
        "tagline": tagline,
        "description": description,
        "url": tool_url,
        "github_url": url,
        "tags": ", ".join(tags[:10]),
        "stars": data.get("stargazers_count", 0),
        "language": language,
    })


@app.post("/api/subscribe/demand-pro")
async def subscribe_demand_pro(request: Request):
    """Create a Stripe Checkout session for Demand Pro subscription."""
    user = request.state.user
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)

    import stripe
    stripe.api_key = _os.environ.get("STRIPE_SECRET_KEY")

    price_id = _os.environ.get("STRIPE_DEMAND_PRO_PRICE_ID")
    if not price_id:
        return JSONResponse({"error": "Subscription not configured"}, status_code=500)

    try:
        checkout = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url="https://indiestack.ai/demand?subscribed=true",
            cancel_url="https://indiestack.ai/demand",
            customer_email=user.get("email", ""),
            metadata={"user_id": str(user["id"]), "plan": "demand_pro"},
        )
        return JSONResponse({"checkout_url": checkout.url})
    except Exception as e:
        _logger.error(f"Stripe checkout error: {e}")
        return JSONResponse({"error": "Payment service error"}, status_code=500)


@app.post("/api/subscribe/pro")
async def subscribe_pro(request: Request):
    """Create a Stripe Checkout session for IndieStack Pro."""
    user = request.state.user
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass
    plan = body.get("plan", "pro")  # "pro" or "founder"

    # Prevent duplicate subscriptions
    from indiestack.db import check_pro
    if await check_pro(request.state.db, user["id"]):
        return JSONResponse({"error": "You already have an active Pro subscription"}, status_code=409)

    import stripe
    stripe.api_key = _os.environ.get("STRIPE_SECRET_KEY")

    if plan == "founder":
        price_id = _os.environ.get("STRIPE_FOUNDER_PRICE_ID")
        # Check if founder seats are still available
        from indiestack.db import get_founder_seat_count
        seats_taken = await get_founder_seat_count(request.state.db)
        if seats_taken >= 50:
            return JSONResponse({"error": "All 50 Founding Member seats have been claimed!"}, status_code=410)
    else:
        price_id = _os.environ.get("STRIPE_PRO_PRICE_ID")
        plan = "pro"

    if not price_id:
        return JSONResponse({"error": "Subscription not configured"}, status_code=500)

    try:
        checkout = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url="https://indiestack.ai/dashboard?subscribed=true",
            cancel_url="https://indiestack.ai/pricing",
            customer_email=user.get("email", ""),
            metadata={"user_id": str(user["id"]), "plan": plan},
        )
        return JSONResponse({"checkout_url": checkout.url})
    except Exception as e:
        _logger.error(f"Stripe checkout error: {e}")
        return JSONResponse({"error": "Payment service error"}, status_code=500)


@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events — subscriptions, payments."""
    from indiestack.payments import verify_webhook
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        event = verify_webhook(payload, sig_header)
    except Exception as e:
        logger.warning(f"Stripe webhook verification failed: {e}")
        return JSONResponse({"error": "Invalid signature"}, status_code=400)

    d = request.state.db

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        plan = metadata.get("plan")
        user_id = metadata.get("user_id")

        if plan in ("demand_pro", "pro", "founder") and user_id:
            stripe_sub_id = session.get("subscription", "")
            try:
                await d.execute("""
                    INSERT OR IGNORE INTO subscriptions (user_id, stripe_subscription_id, plan, status)
                    VALUES (?, ?, ?, 'active')
                """, (int(user_id), stripe_sub_id, plan))
                await d.commit()
                logger.info(f"{plan} subscription created for user {user_id}")
                # Upgrade API keys to pro tier
                await d.execute(
                    "UPDATE api_keys SET tier = 'pro' WHERE user_id = ? AND is_active = 1",
                    (int(user_id),)
                )
                await d.commit()
            except Exception as e:
                logger.error(f"Failed to create subscription: {e}")
                return JSONResponse({"error": "Internal error"}, status_code=500)

    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        sub_id = sub.get("id", "")
        if sub_id:
            try:
                # Find the user before updating status so we can downgrade their API keys
                cursor = await d.execute(
                    "SELECT user_id FROM subscriptions WHERE stripe_subscription_id = ?",
                    (sub_id,)
                )
                sub_row = await cursor.fetchone()
                await d.execute(
                    "UPDATE subscriptions SET status = 'cancelled' WHERE stripe_subscription_id = ?",
                    (sub_id,)
                )
                # Downgrade API keys back to free — but only if user has no other active subscription
                if sub_row:
                    cancelled_user_id = sub_row['user_id']
                    other_active = await d.execute(
                        "SELECT id FROM subscriptions WHERE user_id = ? AND status = 'active' LIMIT 1",
                        (cancelled_user_id,)
                    )
                    if not await other_active.fetchone():
                        await d.execute(
                            "UPDATE api_keys SET tier = 'free' WHERE user_id = ? AND is_active = 1",
                            (cancelled_user_id,)
                        )
                        logger.info(f"Downgraded API keys for user {cancelled_user_id}")
                await d.commit()
                logger.info(f"Subscription {sub_id} cancelled")
            except Exception as e:
                logger.error(f"Failed to cancel subscription: {e}")
                return JSONResponse({"error": "Internal error"}, status_code=500)

    return JSONResponse({"received": True})


@app.get("/api/demand-export")
async def demand_export(request: Request):
    """Export demand clusters as JSON or CSV (pro only)."""
    user = request.state.user
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)

    d = request.state.db
    from indiestack.db import check_pro
    if not await check_pro(d, user['id']):
        return JSONResponse({"error": "Pro subscription required"}, status_code=403)

    from indiestack.db import get_demand_clusters_enriched
    clusters = await get_demand_clusters_enriched(d, limit=100)

    fmt = request.query_params.get('format', 'json')
    if fmt == 'csv':
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['query', 'opportunity_score', 'zero_count', 'search_count', 'competitor_density', 'sources', 'first_searched', 'last_searched'])
        for c in clusters:
            writer.writerow([c['query'], c['opportunity_score'], c['zero_count'], c['search_count'], c['competitor_density'], c.get('sources', ''), c.get('first_searched', ''), c.get('last_searched', '')])
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename=indiestack-demand-signals.csv'},
        )

    return JSONResponse([
        {
            "query": c['query'],
            "opportunity_score": c['opportunity_score'],
            "zero_count": c['zero_count'],
            "search_count": c['search_count'],
            "competitor_density": c['competitor_density'],
            "sources": c.get('sources', ''),
            "first_searched": c.get('first_searched', ''),
            "last_searched": c.get('last_searched', ''),
        }
        for c in clusters
    ])


@app.get("/api/click/{slug}")
async def outbound_click(request: Request, slug: str):
    """Track outbound click and show brief interstitial with email capture."""
    import html as _html
    from fastapi.responses import RedirectResponse, HTMLResponse
    from indiestack.db import get_tool_by_slug, record_outbound_click
    d = request.state.db
    tool = await get_tool_by_slug(d, slug)
    if not tool:
        return RedirectResponse("/explore", status_code=302)
    ip = request.headers.get("fly-client-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host
    referrer = request.headers.get("referer", "")
    await record_outbound_click(d, tool['id'], str(tool['url']), ip, referrer)

    return RedirectResponse(str(tool['url']), status_code=302)


@app.get("/boost/success")
async def boost_success(request: Request):
    """Handle successful boost payment from Stripe."""
    from fastapi.responses import RedirectResponse
    user = request.state.user
    session_id = request.query_params.get("session_id", "")
    if not user or not session_id:
        return RedirectResponse(url="/", status_code=303)

    from indiestack.payments import STRIPE_SECRET_KEY
    import stripe
    stripe.api_key = STRIPE_SECRET_KEY

    d = request.state.db
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid" or session.status == "complete":
            tool_id = int(session.metadata.get("tool_id", 0))
            if tool_id:
                # Verify the logged-in user owns this tool
                tool = await db.get_tool_by_id(d, tool_id)
                if tool and tool.get('maker_id') and tool['maker_id'] == user.get('maker_id'):
                    await db.activate_boost(d, tool_id)
                    return RedirectResponse(url=f"/tool/{tool['slug']}?boosted=1", status_code=303)
                elif tool:
                    return RedirectResponse(url=f"/tool/{tool['slug']}", status_code=303)
    except Exception:
        _logger.exception("Boost activation failed")

    return RedirectResponse(url="/dashboard", status_code=303)


@app.get("/verify-claim/{token}")
async def verify_claim(request: Request, token: str):
    """Verify a claim token and link tool to maker."""
    from fastapi.responses import HTMLResponse, RedirectResponse
    d = request.state.db
    result = await db.verify_claim_token(d, token)

    if result:
        tool_id, user_id = result
        tool = await db.get_tool_by_id(d, tool_id)
        slug = tool['slug'] if tool else ''
        # Send maker welcome email
        try:
            user = await db.get_user_by_id(d, user_id)
            if user and tool:
                await send_email(
                    user['email'],
                    f"Welcome to IndieStack — {tool['name']} is live!",
                    maker_welcome_html(
                        maker_name=user['name'],
                        tool_name=tool['name'],
                        tool_slug=tool['slug'],
                        dashboard_url=f"{BASE_URL}/dashboard",
                    ),
                )
        except Exception:
            pass  # Don't block claim on email failure
        return RedirectResponse(url=f"/tool/{slug}?claimed=1", status_code=303)
    else:
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Invalid or Expired Claim Link</h1>
            <p class="text-muted mt-4">This claim link has expired or was already used.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Invalid Claim", body, user=request.state.user), status_code=400)


# ── Magic Claim Endpoints ────────────────────────────────────────────────

@app.post("/admin/magic-link")
async def admin_generate_magic_link(request: Request):
    """Generate a magic 1-click claim link for an unclaimed tool."""
    from indiestack.auth import check_admin_session
    if not check_admin_session(request):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        form = await request.form()
        tool_id = int(form.get("tool_id", 0))
    except (ValueError, TypeError):
        return JSONResponse({"error": "Invalid tool_id"}, status_code=400)

    d = request.state.db
    tool = await db.get_tool_by_id(d, tool_id)
    if not tool:
        return JSONResponse({"error": "Tool not found"}, status_code=404)

    token = await db.create_magic_claim_token(d, tool_id, days=7)
    base_url = str(request.base_url).rstrip("/")
    magic_url = f"{base_url}/claim/magic?token={token}"

    return JSONResponse({"url": magic_url, "tool_name": tool['name']})


@app.get("/claim/magic")
async def magic_claim(request: Request):
    """One-click claim: creates account, logs in, claims tool, redirects to dashboard."""
    from fastapi.responses import HTMLResponse, RedirectResponse

    token = request.query_params.get("token", "")
    if not token:
        return RedirectResponse(url="/", status_code=303)

    d = request.state.db
    magic = await db.get_magic_claim_token(d, token)
    if not magic:
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Invalid or Expired Link</h1>
            <p class="text-muted mt-4">This claim link has expired or was already used. Please contact us for a new one.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Invalid Link", body, user=request.state.user), status_code=400)

    tool_id = magic['tool_id']
    tool = await db.get_tool_by_id(d, tool_id)
    if not tool:
        return RedirectResponse(url="/", status_code=303)

    # Check if tool is already claimed
    if tool.get('maker_id'):
        await db.use_magic_claim_token(d, token)
        return RedirectResponse(url=f"/tool/{tool['slug']}?claimed=1", status_code=303)

    # If user is already logged in, just claim the tool directly
    user = request.state.user
    if user:
        maker_name = user.get('name', '') or user.get('email', '').split('@')[0]
        maker_id = await db.get_or_create_maker(d, maker_name, '')
        await d.execute("UPDATE tools SET maker_id = ?, claimed_at = CURRENT_TIMESTAMP WHERE id = ? AND maker_id IS NULL", (maker_id, tool_id))
        if not user.get('maker_id'):
            await d.execute("UPDATE users SET maker_id = ?, role = 'maker' WHERE id = ?", (maker_id, user['id']))
        await d.commit()
        await db.use_magic_claim_token(d, token)
        return RedirectResponse(url=f"/tool/{tool['slug']}?claimed=1", status_code=303)

    # User not logged in — show a simple signup form pre-filled with the token
    # They just need name + email + password, then we auto-claim
    from html import escape as _h_esc
    tool_name_esc = _h_esc(tool['name'])
    body = f"""
    <div class="container" style="padding:64px 24px;max-width:480px;">
        <div style="text-align:center;margin-bottom:32px;">
            <div style="margin-bottom:12px;"><svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></div>
            <h1 style="font-family:var(--font-display);font-size:28px;color:var(--ink);margin-bottom:8px;">
                Claim {tool['name']}
            </h1>
            <p style="color:var(--ink-muted);font-size:15px;">
                Create your free IndieStack account to claim this tool and start managing your listing.
            </p>
        </div>
        <div class="card" style="padding:24px;">
            <form method="POST" action="/claim/magic/complete">
                <input type="hidden" name="token" value="{token}">
                <div class="form-group">
                    <label for="name">Your Name</label>
                    <input type="text" id="name" name="name" class="form-input" required placeholder="e.g. Jane Smith">
                </div>
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" class="form-input" required placeholder="you@example.com">
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" class="form-input" required minlength="8" placeholder="Min 8 characters">
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:12px;font-size:15px;">
                    Create Account &amp; Claim Tool
                </button>
            </form>
            <p style="text-align:center;margin-top:16px;font-size:13px;color:var(--ink-muted);">
                Already have an account? <a href="/login?next=/claim/magic?token={token}">Log in</a>
            </p>
        </div>
    </div>
    """
    return HTMLResponse(page_shell(f"Claim {tool['name']}", body, user=None,
                                    description=f"Claim {tool['name']} on IndieStack"))


@app.post("/claim/magic/complete")
async def magic_claim_complete(request: Request):
    """Process magic claim signup: create account, log in, claim tool."""
    from fastapi.responses import RedirectResponse, HTMLResponse
    from indiestack.auth import hash_password, create_user_session

    form = await request.form()
    token = str(form.get("token", ""))
    name = str(form.get("name", "")).strip()
    email = str(form.get("email", "")).strip().lower()
    password = str(form.get("password", ""))

    d = request.state.db

    # Validate token
    magic = await db.get_magic_claim_token(d, token)
    if not magic:
        return RedirectResponse(url="/", status_code=303)

    tool_id = magic['tool_id']
    tool = await db.get_tool_by_id(d, tool_id)
    if not tool:
        return RedirectResponse(url="/", status_code=303)

    # Validate inputs
    errors = []
    if not name or len(name) < 2:
        errors.append("Name is required.")
    if not email or '@' not in email:
        errors.append("Valid email is required.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")

    # Check if email already exists
    existing = await db.get_user_by_email(d, email)
    if existing:
        errors.append("An account with this email already exists. Please log in instead.")

    if errors:
        # Re-show form with errors
        error_html = '<div class="alert alert-error" style="margin-bottom:16px;">' + '<br>'.join(errors) + '</div>'
        body = f"""
        <div class="container" style="padding:64px 24px;max-width:480px;">
            <div style="text-align:center;margin-bottom:32px;">
                <h1 style="font-family:var(--font-display);font-size:28px;color:var(--ink);">Claim {_h_esc(tool['name'])}</h1>
            </div>
            <div class="card" style="padding:24px;">
                {error_html}
                <form method="POST" action="/claim/magic/complete">
                    <input type="hidden" name="token" value="{_h_esc(token)}">
                    <div class="form-group">
                        <label>Your Name</label>
                        <input type="text" name="name" class="form-input" required value="{_h_esc(name)}">
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="email" class="form-input" required value="{_h_esc(email)}">
                    </div>
                    <div class="form-group">
                        <label>Password</label>
                        <input type="password" name="password" class="form-input" required minlength="8">
                    </div>
                    <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:12px;">
                        Create Account &amp; Claim Tool
                    </button>
                </form>
            </div>
        </div>
        """
        return HTMLResponse(page_shell(f"Claim {tool['name']}", body, user=None))

    # Create account
    pw_hash = hash_password(password)
    maker_id = await db.get_or_create_maker(d, name, '')
    user_id = await db.create_user(d, email=email, password_hash=pw_hash, name=name, role='maker', maker_id=maker_id)

    # Claim the tool
    await d.execute("UPDATE tools SET maker_id = ?, claimed_at = CURRENT_TIMESTAMP WHERE id = ? AND maker_id IS NULL", (maker_id, tool_id))
    await d.commit()

    # Mark token used
    await db.use_magic_claim_token(d, token)

    # Send verification email
    try:
        verify_token = await db.create_email_verification_token(d, user_id)
        base_url = str(request.base_url).rstrip("/")
        verify_url = f"{base_url}/verify-email?token={verify_token}"
        await send_email(email, "Verify your IndieStack email", email_verification_html(verify_url))
    except Exception:
        _logger.exception("Failed to send verification email during claim")

    # Send maker welcome email
    try:
        await send_email(
            email,
            f"Welcome to IndieStack — {tool['name']} is live!",
            maker_welcome_html(
                maker_name=name,
                tool_name=tool['name'],
                tool_slug=tool['slug'],
                dashboard_url=f"{BASE_URL}/dashboard",
            ),
        )
    except Exception:
        _logger.exception("Failed to send maker welcome email")  # Don't block claim

    # Create session and log them in
    session_token = await create_user_session(d, user_id)
    response = RedirectResponse(url=f"/tool/{tool['slug']}?claimed=1", status_code=303)
    response.set_cookie("indiestack_session", session_token, httponly=True, samesite="lax", max_age=30 * 86400, secure=True)
    return response


# ── Weekly Email Trigger ─────────────────────────────────────────────────

@app.get("/api/send-weekly")
async def send_weekly_digest(request: Request):
    """Trigger weekly digest email to all subscribers. Protected by admin key."""
    import secrets as _secrets
    key = request.query_params.get("key", "")
    admin_key = _os.environ.get("ADMIN_SECRET", "")
    if not admin_key or not _secrets.compare_digest(key, admin_key):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    d = request.state.db
    # Get content for the digest
    trending = await db.get_trending_scored(d, limit=3, days=7)
    recent = await db.get_recent_tools(d, limit=1, days=7)
    tokens_saved = await db.get_platform_tokens_saved(d)
    subscribers = await db.get_all_subscribers(d)

    new_tool = recent[0] if recent else None
    sent = 0
    errors = 0

    from indiestack.email import send_email, subscriber_digest_html
    html = subscriber_digest_html(trending, new_tool, tokens_saved)

    for sub in subscribers:
        try:
            await send_email(sub['email'], "Your Weekly Vibe Check — IndieStack", html)
            sent += 1
        except Exception:
            errors += 1

    return JSONResponse({"ok": True, "sent": sent, "errors": errors, "total_subscribers": len(subscribers)})


@app.get("/admin/send-weekly-pro-reports")
async def send_weekly_pro_reports(request: Request):
    """Send weekly AI report to all Pro subscribers. Protected by ADMIN_SECRET."""
    import secrets as _secrets
    key = request.query_params.get("key", "")
    admin_key = _os.environ.get("ADMIN_SECRET", "")
    if not admin_key or not _secrets.compare_digest(key, admin_key):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    d = request.state.db
    from indiestack.email import send_email, pro_weekly_report_html
    from indiestack.db import (
        get_pro_users_with_makers, get_weekly_citations_by_maker,
        get_new_tools_in_maker_categories, get_listing_quality_score,
        get_tools_by_maker,
    )

    pro_users = await get_pro_users_with_makers(d)
    sent = 0
    errors = 0
    skipped = 0

    for pu in pro_users:
        maker_id = pu.get('maker_id')
        if not maker_id:
            skipped += 1
            continue

        try:
            # Get citation stats for the week
            citation_data = await get_weekly_citations_by_maker(d, maker_id)

            # Get new tools in their categories
            new_tools = await get_new_tools_in_maker_categories(d, maker_id, days=7)

            # Get average listing quality score
            quality_score = None
            maker_tools = await get_tools_by_maker(d, maker_id)
            if maker_tools:
                scores = []
                for t in maker_tools:
                    qs = await get_listing_quality_score(d, t)
                    scores.append(qs.get('total', 50))
                if scores:
                    quality_score = round(sum(scores) / len(scores))

            html = pro_weekly_report_html(
                maker_name=pu.get('maker_name') or pu.get('username') or 'there',
                total_citations=citation_data['total'],
                top_tool_name=citation_data['top_tool_name'],
                top_tool_slug=citation_data['top_tool_slug'],
                top_tool_citations=citation_data['top_tool_citations'],
                agent_breakdown=citation_data['agents'],
                new_tools_in_categories=new_tools,
                quality_score=quality_score,
            )

            await send_email(
                pu['email'],
                "Your Weekly AI Report — IndieStack Pro",
                html,
            )
            sent += 1
        except Exception as e:
            _logger.warning(f"Failed to send Pro report to {pu.get('email')}: {e}")
            errors += 1

    return JSONResponse({
        "ok": True,
        "sent": sent,
        "errors": errors,
        "skipped": skipped,
        "total_pro_users": len(pro_users),
    })


@app.get("/api/follow-through")
async def api_follow_through(request: Request, days: int = 30):
    """Follow-through rate: MCP search → detail view conversion."""
    admin_key = request.query_params.get("admin_key", "")
    import secrets as _secrets_mod
    _admin_secret = _os.environ.get("ADMIN_SECRET", "")
    if not _admin_secret or not _secrets_mod.compare_digest(admin_key, _admin_secret):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    d = request.state.db
    stats = await db.get_follow_through_rate(d, min(days, 365))
    return JSONResponse(stats)


@app.get("/admin/recompute-scores")
async def admin_recompute_scores(request: Request):
    """Cron endpoint: run health checks then recompute all quality scores.
    Protected by ADMIN_SECRET. Called daily by Fly cron.
    """
    import secrets as _secrets
    key = request.query_params.get("key", "")
    admin_key = _os.environ.get("ADMIN_SECRET", "")
    if not admin_key or not _secrets.compare_digest(key, admin_key):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    d = request.state.db
    health_result = await db.run_health_checks(d)
    score_result = await db.recompute_all_quality_scores(d)

    return JSONResponse({
        "ok": True,
        "health": health_result,
        "scores": score_result,
    })


@app.get("/admin/github-health")
async def admin_github_health(request: Request):
    """Cron endpoint: run GitHub maintenance signal checks.
    Protected by ADMIN_SECRET.
    """
    import secrets as _secrets
    key = request.query_params.get("key", "")
    admin_key = _os.environ.get("ADMIN_SECRET", "")
    if not admin_key or not _secrets.compare_digest(key, admin_key):
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    d = request.state.db
    try:
        batch = int(request.query_params.get("batch", "100"))
    except (ValueError, TypeError):
        batch = 100
    batch = min(batch, 200)  # Cap at 200 per run
    result = await db.run_github_health_checks(d, batch_size=batch)
    return JSONResponse({"ok": True, "github_health": result})


# ── RSS Feeds ────────────────────────────────────────────────────────────

def _build_rss_xml(tools: list, title: str, description: str, link: str) -> str:
    """Build RSS 2.0 XML from a list of tool dicts."""
    from html import escape
    items = []
    for t in tools:
        name = escape(str(t.get('name', '')))
        tagline = escape(str(t.get('tagline', '')))
        slug = t.get('slug', '')
        desc = escape(str(t.get('description', '') or t.get('tagline', '')))
        cat = escape(str(t.get('category_name', '')))
        created = str(t.get('created_at', ''))
        items.append(f"""    <item>
      <title>{name}</title>
      <link>{BASE_URL}/tool/{slug}</link>
      <description>{tagline}</description>
      <category>{cat}</category>
      <pubDate>{created}</pubDate>
      <guid>{BASE_URL}/tool/{slug}</guid>
    </item>""")
    items_xml = "\n".join(items)
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{escape(title)}</title>
    <link>{link}</link>
    <description>{escape(description)}</description>
    <language>en</language>
    <atom:link href="{link}" rel="self" type="application/rss+xml"/>
{items_xml}
  </channel>
</rss>"""


@app.get("/feed/rss")
async def rss_all(request: Request):
    """RSS feed of all recent approved tools."""
    tools = await db.get_tools_for_rss(request.state.db, limit=30)
    xml = _build_rss_xml(tools, "IndieStack — New Developer Tools",
                          "The latest developer tools on IndieStack",
                          f"{BASE_URL}/feed/rss")
    return Response(content=xml, media_type="application/rss+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@app.get("/category/{slug}/rss")
async def rss_category(request: Request, slug: str):
    """RSS feed for a specific category."""
    tools = await db.get_tools_for_rss(request.state.db, category_slug=slug, limit=30)
    xml = _build_rss_xml(tools, f"IndieStack — {slug.replace('-', ' ').title()} Tools",
                          f"Developer tools in the {slug.replace('-', ' ')} category",
                          f"{BASE_URL}/category/{slug}/rss")
    return Response(content=xml, media_type="application/rss+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@app.get("/tag/{slug}/rss")
async def rss_tag(request: Request, slug: str):
    """RSS feed for a specific tag."""
    tools = await db.get_tools_for_rss(request.state.db, tag=slug.replace('-', ' '), limit=30)
    xml = _build_rss_xml(tools, f"IndieStack — #{slug} Tools",
                          f"Developer tools tagged with {slug.replace('-', ' ')}",
                          f"{BASE_URL}/tag/{slug}/rss")
    return Response(content=xml, media_type="application/rss+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


# ── LobeChat Plugin Manifest ──────────────────────────────────────────────

@app.get("/manifest.json")
async def lobechat_manifest():
    """LobeChat plugin manifest for the IndieStack search plugin."""
    return {
        "api": [
            {
                "name": "searchIndieTools",
                "url": f"{BASE_URL}/api/tools/search",
                "description": "Search 130+ indie SaaS tools by keyword or category. Use this before building common functionality from scratch — save tokens, ship faster.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "q": {
                            "type": "string",
                            "description": "Search query (e.g. 'invoicing', 'analytics', 'auth')"
                        },
                        "category": {
                            "type": "string",
                            "description": "Optional category slug filter (e.g. 'invoicing-billing', 'analytics-metrics')"
                        },
                        "limit": {
                            "type": "number",
                            "description": "Max results to return (default 10)",
                            "default": 10
                        }
                    },
                    "required": ["q"]
                }
            },
            {
                "name": "getToolDetails",
                "url": f"{BASE_URL}/api/tools/{{slug}}",
                "description": "Get full details for a specific indie tool including description, pricing, ratings, and integration snippets.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "slug": {
                            "type": "string",
                            "description": "The tool's URL slug (e.g. 'plausible-analytics')"
                        }
                    },
                    "required": ["slug"]
                }
            }
        ],
        "identifier": "indiestack",
        "meta": {
            "avatar": "🧱",
            "title": "IndieStack",
            "description": "Search 130+ indie SaaS tools from your AI coding assistant before it writes code.",
            "tags": ["search", "developer-tools", "indie", "saas", "mcp"]
        },
        "version": "1"
    }


@app.post("/api/agent/recommend")
async def agent_recommend(request: Request):
    """Record that an agent recommended a tool to its user."""
    api_key = _require_scope(request.state.api_key, "read")
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    tool_slug = str(data.get("tool_slug", "")).strip()
    query_context = str(data.get("query_context", "")).strip()[:500] or None

    if not tool_slug:
        return JSONResponse({"error": "tool_slug required"}, status_code=400)

    tool = await db.get_tool_by_slug(request.state.db, tool_slug)
    if not tool:
        return JSONResponse({"error": f"Tool '{tool_slug}' not found"}, status_code=404)

    count = await db.count_agent_actions_today(request.state.db, api_key["id"], "recommend")
    if count >= _AGENT_ACTION_LIMITS["recommend"]:
        return JSONResponse({"error": "Daily recommend limit reached (50/day)"}, status_code=429)

    if await db.check_agent_daily_action(request.state.db, api_key["user_id"], "recommend", tool_slug):
        rec_count = await db.get_tool_recommendation_count(request.state.db, tool_slug)
        return JSONResponse({"ok": True, "already_recorded": True, "total_recommendations": rec_count})

    await db.record_agent_action(
        request.state.db, api_key["id"], api_key["user_id"],
        "recommend", tool_slug, query_context=query_context,
    )
    rec_count = await db.get_tool_recommendation_count(request.state.db, tool_slug)
    return JSONResponse({"ok": True, "total_recommendations": rec_count})


@app.post("/api/agent/shortlist")
async def agent_shortlist(request: Request):
    """Record tools the agent considered for a query."""
    api_key = _require_scope(request.state.api_key, "read")
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    tool_slugs = data.get("tool_slugs", [])
    query_context = str(data.get("query_context", "")).strip()[:500] or None

    if not isinstance(tool_slugs, list) or len(tool_slugs) == 0:
        return JSONResponse({"error": "tool_slugs must be a non-empty list"}, status_code=400)
    if len(tool_slugs) > 10:
        return JSONResponse({"error": "Max 10 tool slugs per shortlist"}, status_code=400)

    count = await db.count_agent_actions_today(request.state.db, api_key["id"], "shortlist")
    if count + len(tool_slugs) > _AGENT_ACTION_LIMITS["shortlist"]:
        return JSONResponse({"error": "Daily shortlist limit reached (100/day)"}, status_code=429)

    recorded = 0
    for slug in tool_slugs[:10]:
        slug = str(slug).strip()
        if not slug:
            continue
        tool = await db.get_tool_by_slug(request.state.db, slug)
        if tool:
            await db.record_agent_action(
                request.state.db, api_key["id"], api_key["user_id"],
                "shortlist", slug, query_context=query_context,
            )
            recorded += 1
    return JSONResponse({"ok": True, "recorded": recorded})


@app.post("/api/agent/outcome")
async def agent_outcome(request: Request):
    """Report whether a user successfully used a recommended tool."""
    api_key = request.state.api_key
    if not api_key:
        ip = request.client.host if request.client else "unknown"
        rk = f"outcome_{ip}"
        today = date.today().isoformat()
        if not hasattr(request.app.state, '_outcome_ip_daily'):
            request.app.state._outcome_ip_daily = {}
        ip_counts = request.app.state._outcome_ip_daily
        if rk not in ip_counts or ip_counts[rk][0] != today:
            if len(ip_counts) > 500:
                ip_counts.clear()
            ip_counts[rk] = (today, 0)
        if ip_counts[rk][1] >= 10:
            raise HTTPException(429, detail="Keyless outcome reporting limit reached (10/day). Get a free API key at indiestack.ai/developer for higher limits.")
        ip_counts[rk] = (today, ip_counts[rk][1] + 1)

    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    tool_slug = str(data.get("tool_slug", "")).strip()
    success = data.get("success")
    notes = str(data.get("notes", "")).strip()[:1000] or None

    if not tool_slug:
        return JSONResponse({"error": "tool_slug required"}, status_code=400)
    if success is None or success not in (True, False, 0, 1):
        return JSONResponse({"error": "success must be true or false"}, status_code=400)

    tool = await db.get_tool_by_slug(request.state.db, tool_slug)
    if not tool:
        return JSONResponse({"error": f"Tool '{tool_slug}' not found"}, status_code=404)

    api_key_id = api_key["id"] if api_key else None
    user_id = api_key["user_id"] if api_key else 0

    if api_key_id:
        count = await db.count_agent_actions_today(request.state.db, api_key_id, "report_outcome")
        if count >= _AGENT_ACTION_LIMITS["report_outcome"]:
            return JSONResponse({"error": "Daily outcome report limit reached (20/day)"}, status_code=429)

    if user_id:
        if await db.check_agent_action_exists(request.state.db, user_id, "report_outcome", tool_slug):
            return JSONResponse({"ok": True, "already_recorded": True})
    else:
        # Keyless dedup: max 1 report per tool per day from user_id=0
        dup_cursor = await request.state.db.execute(
            "SELECT 1 FROM agent_actions WHERE user_id = 0 AND action = 'report_outcome' AND tool_slug = ? AND created_at >= date('now') LIMIT 1",
            (tool_slug,),
        )
        if await dup_cursor.fetchone():
            return JSONResponse({"ok": True, "already_recorded": True})

    await db.record_agent_action(
        request.state.db, api_key_id, user_id,
        "report_outcome", tool_slug, success=int(bool(success)), notes=notes,
    )

    # Enrichment is best-effort; primary outcome already recorded
    try:
        # Record stack if used_with provided
        used_with_str = str(data.get("used_with", "")).strip()
        if used_with_str and success:
            companions = [s.strip() for s in used_with_str.split(",") if s.strip()]
            valid_companions = []
            for comp_slug in companions[:5]:  # Limit to 5 companions per report
                comp = await db.get_tool_by_slug(request.state.db, comp_slug)
                if comp:
                    valid_companions.append(comp_slug)
                    # Record pairwise compatibility
                    await db.record_tool_pair(request.state.db, tool_slug, comp_slug, source="agent")
            if valid_companions:
                all_slugs = [tool_slug] + valid_companions
                await db.record_verified_stack(request.state.db, all_slugs, source="agent")

        # Record conflict if incompatible_with provided
        incompatible_with_str = str(data.get("incompatible_with", "")).strip()
        if incompatible_with_str and not success:
            inc_tool = await db.get_tool_by_slug(request.state.db, incompatible_with_str)
            if inc_tool:
                await db.record_tool_conflict(request.state.db, tool_slug, incompatible_with_str, reason=notes)
    except Exception:
        pass

    stats = await db.get_tool_success_rate(request.state.db, tool_slug)
    return JSONResponse({"ok": True, "success_rate": stats})


@app.post("/api/agent/integration")
async def agent_integration(request: Request):
    """Report that two tools were successfully integrated together."""
    api_key = _require_scope(request.state.api_key, "write")
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    tool_a = str(data.get("tool_a_slug", "")).strip()
    tool_b = str(data.get("tool_b_slug", "")).strip()
    notes = str(data.get("notes", "")).strip()[:1000] or None

    if not tool_a or not tool_b:
        return JSONResponse({"error": "tool_a_slug and tool_b_slug required"}, status_code=400)
    if tool_a == tool_b:
        return JSONResponse({"error": "Cannot integrate a tool with itself"}, status_code=400)

    ta = await db.get_tool_by_slug(request.state.db, tool_a)
    tb = await db.get_tool_by_slug(request.state.db, tool_b)
    if not ta:
        return JSONResponse({"error": f"Tool '{tool_a}' not found"}, status_code=404)
    if not tb:
        return JSONResponse({"error": f"Tool '{tool_b}' not found"}, status_code=404)

    count = await db.count_agent_actions_today(request.state.db, api_key["id"], "confirm_integration")
    if count >= _AGENT_ACTION_LIMITS["confirm_integration"]:
        return JSONResponse({"error": "Daily integration report limit reached (10/day)"}, status_code=429)

    a, b = sorted([tool_a, tool_b])
    if await db.check_agent_action_exists(request.state.db, api_key["user_id"], "confirm_integration", a, b):
        return JSONResponse({"ok": True, "already_recorded": True})

    await db.record_agent_action(
        request.state.db, api_key["id"], api_key["user_id"],
        "confirm_integration", a, tool_b_slug=b, notes=notes,
    )
    await record_tool_pair(request.state.db, a, b, source="agent")
    return JSONResponse({"ok": True})


# ── Mount routes ──────────────────────────────────────────────────────────

app.include_router(landing.router)
app.include_router(browse.router)
app.include_router(tool.router)
app.include_router(search.router)
app.include_router(submit.router)
app.include_router(admin.router)
app.include_router(purchase.router)
app.include_router(maker.router)
app.include_router(collections.router)
app.include_router(compare.router)
app.include_router(new.router)
app.include_router(account.router)
app.include_router(dashboard.router)
app.include_router(pricing.router)
app.include_router(updates.router)
from indiestack.routes import content
app.include_router(content.router)
app.include_router(alternatives.router)
app.include_router(stacks.router)
app.include_router(explore.router)
app.include_router(tags.router)

app.include_router(calculator_router)
app.include_router(built_this.router)
app.include_router(stripe_guide.router)
app.include_router(launch.router)
app.include_router(embed.router)
app.include_router(launch_with_me.router)
app.include_router(use_cases.router)
app.include_router(why_list.router)
app.include_router(what_is.router)
app.include_router(plugins.router)
app.include_router(gaps.router)
from indiestack.routes import pulse
app.include_router(pulse.router)
app.include_router(api_docs.router)
app.include_router(geo.router)
app.include_router(changelog.router)
app.include_router(guidelines.router)
app.include_router(audit.router)

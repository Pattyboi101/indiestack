"""FastAPI app, middleware, router wiring, upvote API."""

import asyncio
import hashlib
import os as _os
import time as _time
from contextlib import asynccontextmanager

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

# Rate limiting
_rate_limits: dict[str, list[float]] = {}
_rate_check_counter = 0


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

    # Rate limit GET for email-sending endpoints, POST for everything else
    get_limited = {"/resend-verification"}
    if method == "GET" and path not in get_limited:
        return False
    if method not in ("POST", "GET"):
        return False

    limits = {
        "/login": 5,
        "/signup": 3,
        "/submit": 3,
        "/forgot-password": 3,
        "/resend-verification": 3,
        "/admin": 60,
        "/api/upvote": 10,
        "/api/wishlist": 10,
        "/api/subscribe": 5,
    }

    # Check specific path limits
    max_requests = None
    if path in limits:
        max_requests = limits[path]
    elif path.startswith("/api/"):
        max_requests = 30

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

_sitemap_cache: dict[str, object] = {'xml': None, 'expires': 0}

_LOGO_CANDIDATES = [
    Path(__file__).resolve().parent.parent.parent / "logo" / "indiestack.png",
    Path("/app/logo/indiestack.png"),
]
_logo_bytes: bytes | None = None

from indiestack import db
from indiestack.db import CATEGORY_TOKEN_COSTS, get_user_by_badge_token, get_buyer_tokens_saved_by_token, cleanup_expired_sessions, cleanup_old_page_views, get_makers_for_ego_ping
from indiestack.email import send_email, ego_ping_html
from indiestack.auth import get_current_user
from indiestack.routes import landing, browse, tool, search, submit, admin, purchase
from indiestack.routes import verify, maker, collections, compare, new, account, dashboard, pricing, updates, alternatives
from indiestack.routes import stacks
from indiestack.routes import explore, tags


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
            pass


async def _weekly_ego_ping():
    """Send ego ping emails every Friday."""
    import aiosqlite
    from datetime import datetime
    while True:
        await asyncio.sleep(86400)  # Check daily
        if datetime.utcnow().weekday() != 4:  # 4 = Friday
            continue
        try:
            async with aiosqlite.connect(db.DB_PATH) as conn:
                conn.row_factory = aiosqlite.Row
                makers = await get_makers_for_ego_ping(conn)
                for m in makers:
                    html = ego_ping_html(
                        maker_name=m['maker_name'],
                        tool_name=m['tool_name'],
                        tool_slug=m['tool_slug'],
                        views=m['weekly_views'],
                        clicks=m.get('weekly_clicks', 0),
                        upvotes=m['upvote_count'],
                        wishlists=m['wishlist_count'],
                        has_changelog=m['changelog_count'] > 0,
                        has_active_badge=m['recent_updates'] > 0,
                    )
                    await send_email(m['email'], f"Your week on IndieStack \u2014 {m['tool_name']}", html)
        except Exception:
            pass


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
    yield
    cleanup_task.cancel()
    ego_ping_task.cancel()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)


# ── 404 Error Page ───────────────────────────────────────────────────────

from starlette.exceptions import HTTPException as StarletteHTTPException
from indiestack.routes.components import page_shell


@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404:
        from fastapi.responses import HTMLResponse
        body = """
        <section style="text-align:center;padding:100px 24px 80px;max-width:560px;margin:0 auto;">
            <div style="font-size:72px;margin-bottom:16px;">&#128270;</div>
            <h1 style="font-family:var(--font-display);font-size:clamp(36px,5vw,48px);color:var(--ink);margin-bottom:12px;">
                404 &mdash; Page not found
            </h1>
            <p style="color:var(--ink-muted);font-size:17px;line-height:1.6;margin-bottom:32px;">
                This page doesn&rsquo;t exist. Save your tokens &mdash; don&rsquo;t build it, find what you need instead.
            </p>
            <form action="/search" method="GET" style="max-width:440px;margin:0 auto 24px;">
                <div style="display:flex;align-items:center;background:var(--card-bg, white);border:2px solid var(--border);
                            border-radius:999px;padding:6px 6px 6px 16px;gap:8px;">
                    <span style="font-size:18px;color:var(--ink-muted);">&#128269;</span>
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
        # Track pageview (skip static assets and API calls)
        path = request.url.path
        if not path.startswith(('/api/', '/health', '/favicon', '/logo', '/track', '/robots', '/sitemap')):
            visitor_raw = f"{request.headers.get('fly-client-ip', '') or request.headers.get('x-forwarded-for', '').split(',')[0].strip() or request.client.host}:{request.headers.get('user-agent', '')}"
            visitor_id = hashlib.sha256(visitor_raw.encode()).hexdigest()[:16]
            referrer = request.headers.get('referer', '')
            try:
                await db.track_pageview(request.state.db, path, visitor_id, referrer)
            except Exception:
                pass
        response = await call_next(request)
    finally:
        await request.state.db.close()
    return response


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
    return Response(content=_logo_bytes, media_type="image/png")


# ── SEO ───────────────────────────────────────────────────────────────────

@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return "User-agent: *\nAllow: /\nSitemap: https://indiestack.fly.dev/sitemap.xml"


@app.get("/sitemap.xml")
async def sitemap(request: Request):
    if _sitemap_cache['xml'] and _time.time() < _sitemap_cache['expires']:
        return Response(content=_sitemap_cache['xml'], media_type="application/xml")
    urls = [
        ("https://indiestack.fly.dev/", "daily", "1.0"),
        ("https://indiestack.fly.dev/submit", "monthly", "0.5"),
        ("https://indiestack.fly.dev/new", "daily", "0.8"),
        ("https://indiestack.fly.dev/collections", "weekly", "0.7"),
        ("https://indiestack.fly.dev/makers", "daily", "0.8"),
        ("https://indiestack.fly.dev/updates", "daily", "0.8"),
        ("https://indiestack.fly.dev/live", "always", "0.6"),
    ]
    for path in ["/about", "/terms", "/privacy", "/faq"]:
        urls.append((f"https://indiestack.fly.dev{path}", "monthly", "0.5"))
    urls.append(("https://indiestack.fly.dev/blog", "weekly", "0.7"))
    urls.append(("https://indiestack.fly.dev/blog/stop-wasting-tokens", "monthly", "0.8"))
    urls.append(("https://indiestack.fly.dev/blog/zero-js-frameworks", "monthly", "0.8"))
    urls.append(("https://indiestack.fly.dev/alternatives", "daily", "0.8"))
    # Individual alternatives pages
    d = request.state.db
    competitors = await db.get_all_competitors(d)
    for comp in competitors:
        comp_slug = comp.lower().replace(" ", "-").replace(".", "-")
        urls.append((f"https://indiestack.fly.dev/alternatives/{comp_slug}", "weekly", "0.7"))
    cats = await db.get_all_categories(d)
    for c in cats:
        urls.append((f"https://indiestack.fly.dev/category/{c['slug']}", "daily", "0.8"))
    # Best-of programmatic SEO pages
    urls.append(("https://indiestack.fly.dev/best", "weekly", "0.8"))
    for c in cats:
        urls.append((f"https://indiestack.fly.dev/best/{c['slug']}", "weekly", "0.7"))
    cursor = await d.execute("SELECT slug FROM tools WHERE status = 'approved'")
    tools = await cursor.fetchall()
    for t in tools:
        urls.append((f"https://indiestack.fly.dev/tool/{t['slug']}", "weekly", "0.7"))
    # Maker profiles
    cursor2 = await d.execute("SELECT slug FROM makers")
    makers = await cursor2.fetchall()
    for m in makers:
        urls.append((f"https://indiestack.fly.dev/maker/{m['slug']}", "weekly", "0.6"))
    # Collections
    cursor3 = await d.execute("SELECT slug FROM collections")
    colls = await cursor3.fetchall()
    for cl in colls:
        urls.append((f"https://indiestack.fly.dev/collection/{cl['slug']}", "weekly", "0.7"))
    # Stacks
    urls.append(("https://indiestack.fly.dev/stacks", "weekly", "0.7"))
    cursor_stacks = await d.execute("SELECT slug FROM stacks")
    all_stacks_list = await cursor_stacks.fetchall()
    for st in all_stacks_list:
        urls.append((f"https://indiestack.fly.dev/stacks/{st['slug']}", "weekly", "0.7"))
    # Explore
    urls.append(("https://indiestack.fly.dev/explore", "daily", "0.9"))
    # Tags
    urls.append(("https://indiestack.fly.dev/tags", "weekly", "0.7"))
    all_tags = await db.get_all_tags_with_counts(d, min_count=1)
    for tag_item in all_tags:
        urls.append((f"https://indiestack.fly.dev/tag/{tag_item['slug']}", "weekly", "0.6"))
    entries = "\n".join(
        f"  <url><loc>{u}</loc><changefreq>{f}</changefreq><priority>{p}</priority></url>"
        for u, f, p in urls
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
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


@app.get("/favicon.ico")
async def favicon_ico():
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


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
            pass  # Don't break upvote if notification fails

    return JSONResponse({"ok": True, "count": count, "upvoted": upvoted})


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
    try:
        form = await request.form()
        email = str(form.get("email", "")).strip().lower()
    except Exception:
        email = ""
    if not email or "@" not in email:
        return _Redirect(url="/?subscribed=error", status_code=303)
    try:
        await request.state.db.execute(
            "INSERT OR IGNORE INTO subscribers (email) VALUES (?)", (email,)
        )
        await request.state.db.commit()
    except Exception:
        pass
    return _Redirect(url="/?subscribed=1", status_code=303)


# ── Tool Search API ──────────────────────────────────────────────────────

@app.get("/api/tools/search")
async def api_tools_search(request: Request, q: str = "", category: str = "", limit: int = 20):
    """JSON API for searching tools — used by MCP server and integrations."""
    d = request.state.db
    if limit < 1:
        limit = 1
    if limit > 50:
        limit = 50

    if q.strip():
        tools = await db.search_tools(d, q.strip(), limit=limit)
    elif category.strip():
        cat = await db.get_category_by_slug(d, category.strip())
        if cat:
            tools, _ = await db.get_tools_by_category(d, cat['id'], page=1, per_page=limit)
        else:
            tools = []
    else:
        tools = await db.get_trending_tools(d, limit=limit)

    results = []
    for t in tools:
        price_pence = t.get('price_pence')
        if price_pence and price_pence > 0:
            price_str = f"\u00a3{price_pence / 100:.2f}"
        else:
            price_str = "Free"
        results.append({
            "name": t['name'],
            "tagline": t.get('tagline', ''),
            "url": t.get('url', ''),
            "indiestack_url": f"https://indiestack.fly.dev/tool/{t['slug']}",
            "category": t.get('category_name', ''),
            "price": price_str,
            "is_verified": bool(t.get('is_verified', 0)),
            "upvote_count": int(t.get('upvote_count', 0)),
            "tags": t.get('tags', ''),
        })

    # Log the search for Live Wire
    try:
        top_slug = tools[0]['slug'] if tools else None
        top_name = tools[0]['name'] if tools else None
        await db.log_search(d, q, 'api', len(results), top_slug, top_name)
    except Exception:
        pass  # Don't fail the search if logging fails

    return JSONResponse({
        "tools": results,
        "total": len(results),
        "query": q,
    })


@app.get("/api/tools/{slug}")
async def api_tool_detail(request: Request, slug: str):
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

    result = {
        "name": tool['name'],
        "slug": tool['slug'],
        "tagline": tool.get('tagline', ''),
        "description": tool.get('description', ''),
        "url": tool.get('url', ''),
        "indiestack_url": f"https://indiestack.fly.dev/tool/{tool['slug']}",
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
        "integration_python": f'import httpx\nresponse = httpx.get("{tool.get("url", "")}")\nprint(response.status_code)',
        "integration_curl": f'curl -s {tool.get("url", "")}',
        "tokens_saved": CATEGORY_TOKEN_COSTS.get(tool.get('category_slug', ''), 50_000),
    }

    return JSONResponse({"tool": result})


# ── Live Wire ─────────────────────────────────────────────────────────────

@app.get("/live")
async def live_wire(request: Request):
    """Live Wire — real-time search query feed."""
    from fastapi.responses import HTMLResponse
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
            query_text = s.get('query', '')
            count = s.get('result_count', 0)
            top_slug = s.get('top_result_slug', '')
            top_name = s.get('top_result_name', '')
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
    top_q = stats.get('top_query', '')

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

    tool_name = tool['name'] if tool else slug.replace('-', ' ').title()

    # Milestone configs
    milestones = {
        'first-tool': {'emoji': '🎉', 'text': 'Just listed my first tool!'},
        '100-views': {'emoji': '👀', 'text': 'My tool hit 100 views!'},
        '10-upvotes': {'emoji': '🔥', 'text': '10 developers upvoted my tool!'},
        'first-review': {'emoji': '⭐', 'text': 'Got my first review!'},
        'launch-ready': {'emoji': '🚀', 'text': '100% Launch Ready!'},
        '50-wishlists': {'emoji': '💾', 'text': '50 developers wishlisted my tool!'},
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
    indiestack.fly.dev
  </text>
</svg>"""

    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


@app.get("/api/badge/{slug}.svg")
async def tool_badge_svg(request: Request, slug: str):
    """Dynamic SVG badge for makers to embed on their websites."""
    d = request.state.db
    tool = await db.get_tool_by_slug(d, slug)
    if not tool or tool.get('status') != 'approved':
        return Response(content="", status_code=404)

    name = tool['name']
    cat_slug = tool.get('category_slug', '')
    tokens = CATEGORY_TOKEN_COSTS.get(cat_slug, 50_000)
    tokens_k = f"{tokens // 1000}k"

    # Calculate widths for the two-part badge
    left_text = f"IndieStack"
    right_text = f"Saves {tokens_k} tokens"
    left_width = 90
    right_width = 120
    total_width = left_width + right_width

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" role="img" aria-label="{left_text}: {right_text}">
  <title>{left_text}: {right_text}</title>
  <linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
  <clipPath id="r"><rect width="{total_width}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{left_width}" height="20" fill="#1A2D4A"/>
    <rect x="{left_width}" width="{right_width}" height="20" fill="#00D4F5"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
    <text x="{left_width/2}" y="14" fill="#fff">{left_text}</text>
    <text x="{left_width + right_width/2}" y="14" fill="#1A2D4A" font-weight="600">{right_text}</text>
  </g>
</svg>'''
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


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
    if not tool or tool.get('status') != 'approved':
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
  <text x="80" y="540" font-size="20" fill="rgba(255,255,255,0.4)" font-family="system-ui,sans-serif">indiestack.fly.dev</text>
  <text x="1120" y="610" font-size="16" font-weight="700" fill="#1A2D4A" text-anchor="end" font-family="system-ui,sans-serif">IndieStack</text>
</svg>'''
    return Response(content=svg, media_type="image/svg+xml",
                    headers={"Cache-Control": "public, max-age=86400"})


# ── Claim Endpoints ──────────────────────────────────────────────────────

@app.post("/api/claim")
async def api_claim(request: Request):
    """Instant-claim an unclaimed tool for the logged-in user."""
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
    if not tool or tool.get('maker_id'):
        return RedirectResponse(url=f"/tool/{tool['slug']}" if tool else "/", status_code=303)

    # Instant claim — no email verification needed
    maker_name = user.get('name', '') or user.get('email', '').split('@')[0]
    maker_id = await db.get_or_create_maker(d, maker_name, '')
    await d.execute("UPDATE tools SET maker_id = ? WHERE id = ? AND maker_id IS NULL", (maker_id, tool_id))
    if not user.get('maker_id'):
        await d.execute("UPDATE users SET maker_id = ?, role = 'maker' WHERE id = ?", (maker_id, user['id']))
    await d.commit()

    return RedirectResponse(url=f"/tool/{tool['slug']}?claimed=1", status_code=303)


@app.post("/api/claim-and-boost")
async def api_claim_and_boost(request: Request):
    """Claim a tool and redirect to Stripe checkout for boost payment."""
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

    # Instant claim first (if not already claimed)
    if not tool.get('maker_id'):
        maker_name = user.get('name', '') or user.get('email', '').split('@')[0]
        maker_id = await db.get_or_create_maker(d, maker_name, '')
        await d.execute("UPDATE tools SET maker_id = ? WHERE id = ? AND maker_id IS NULL", (maker_id, tool_id))
        if not user.get('maker_id'):
            await d.execute("UPDATE users SET maker_id = ?, role = 'maker' WHERE id = ?", (maker_id, user['id']))
        await d.commit()

    # Create Stripe checkout for boost
    from indiestack.payments import STRIPE_SECRET_KEY
    if not STRIPE_SECRET_KEY:
        return RedirectResponse(url=f"/tool/{tool['slug']}?claimed=1", status_code=303)

    import stripe
    stripe.api_key = STRIPE_SECRET_KEY

    base_url = str(request.base_url).rstrip("/")
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "product_data": {"name": f"IndieStack Boost — {tool['name']}",
                                     "description": "Featured badge for 30 days, priority placement, weekly newsletter feature"},
                    "unit_amount": 2900,
                },
                "quantity": 1,
            }],
            success_url=f"{base_url}/boost/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/tool/{tool['slug']}?claimed=1",
            customer_email=user['email'],
            metadata={"tool_id": str(tool['id']), "user_id": str(user['id']), "type": "boost"},
        )
        return RedirectResponse(url=session.url, status_code=303)
    except Exception:
        return RedirectResponse(url=f"/tool/{tool['slug']}?claimed=1", status_code=303)


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
            line_items=[{
                "price_data": {
                    "currency": "gbp",
                    "product_data": {"name": f"IndieStack Boost — {tool['name']}",
                                     "description": "Featured badge for 30 days, priority placement, weekly newsletter feature"},
                    "unit_amount": 2900,
                },
                "quantity": 1,
            }],
            success_url=f"{base_url}/boost/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/tool/{tool['slug']}",
            customer_email=user['email'],
            metadata={"tool_id": str(tool['id']), "user_id": str(user['id']), "type": "boost"},
        )
        return RedirectResponse(url=session.url, status_code=303)
    except Exception:
        return RedirectResponse(url=f"/tool/{tool['slug']}", status_code=303)


@app.get("/api/click/{slug}")
async def outbound_click(request: Request, slug: str):
    """Track outbound click and redirect to tool's website."""
    from fastapi.responses import RedirectResponse
    from indiestack.db import get_tool_by_slug, record_outbound_click
    d = request.state.db
    tool = await get_tool_by_slug(d, slug)
    if not tool:
        return RedirectResponse("/explore", status_code=302)
    ip = request.headers.get("fly-client-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host
    referrer = request.headers.get("referer", "")
    await record_outbound_click(d, tool['id'], str(tool['url']), ip, referrer)
    return RedirectResponse(str(tool['url']), status_code=307)


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
                await db.activate_boost(d, tool_id)
                tool = await db.get_tool_by_id(d, tool_id)
                slug = tool['slug'] if tool else ''
                return RedirectResponse(url=f"/tool/{slug}?boosted=1", status_code=303)
    except Exception:
        pass

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
        await d.execute("UPDATE tools SET maker_id = ? WHERE id = ? AND maker_id IS NULL", (maker_id, tool_id))
        if not user.get('maker_id'):
            await d.execute("UPDATE users SET maker_id = ?, role = 'maker' WHERE id = ?", (maker_id, user['id']))
        await d.commit()
        await db.use_magic_claim_token(d, token)
        return RedirectResponse(url=f"/tool/{tool['slug']}?claimed=1", status_code=303)

    # User not logged in — show a simple signup form pre-filled with the token
    # They just need name + email + password, then we auto-claim
    tool_name_esc = tool['name'].replace("'", "\\'").replace('"', '&quot;')
    body = f"""
    <div class="container" style="padding:64px 24px;max-width:480px;">
        <div style="text-align:center;margin-bottom:32px;">
            <div style="font-size:48px;margin-bottom:12px;">&#128075;</div>
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
                <h1 style="font-family:var(--font-display);font-size:28px;color:var(--ink);">Claim {tool['name']}</h1>
            </div>
            <div class="card" style="padding:24px;">
                {error_html}
                <form method="POST" action="/claim/magic/complete">
                    <input type="hidden" name="token" value="{token}">
                    <div class="form-group">
                        <label>Your Name</label>
                        <input type="text" name="name" class="form-input" required value="{name}">
                    </div>
                    <div class="form-group">
                        <label>Email</label>
                        <input type="email" name="email" class="form-input" required value="{email}">
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
    await d.execute("UPDATE tools SET maker_id = ? WHERE id = ? AND maker_id IS NULL", (maker_id, tool_id))
    await d.commit()

    # Mark token used
    await db.use_magic_claim_token(d, token)

    # Create session and log them in
    session_token = await create_user_session(d, user_id)
    response = RedirectResponse(url=f"/tool/{tool['slug']}?claimed=1", status_code=303)
    response.set_cookie("indiestack_session", session_token, httponly=True, samesite="lax", max_age=30 * 86400)
    return response


# ── Weekly Email Trigger ─────────────────────────────────────────────────

@app.get("/api/send-weekly")
async def send_weekly_digest(request: Request):
    """Trigger weekly digest email to all subscribers. Protected by admin key."""
    key = request.query_params.get("key", "")
    admin_key = _os.environ.get("ADMIN_SECRET", "indiestack-admin-secret")
    if key != admin_key:
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
      <link>https://indiestack.fly.dev/tool/{slug}</link>
      <description>{tagline}</description>
      <category>{cat}</category>
      <pubDate>{created}</pubDate>
      <guid>https://indiestack.fly.dev/tool/{slug}</guid>
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
    xml = _build_rss_xml(tools, "IndieStack — New Indie Tools",
                          "The latest indie SaaS tools on IndieStack",
                          "https://indiestack.fly.dev/feed/rss")
    return Response(content=xml, media_type="application/rss+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@app.get("/category/{slug}/rss")
async def rss_category(request: Request, slug: str):
    """RSS feed for a specific category."""
    tools = await db.get_tools_for_rss(request.state.db, category_slug=slug, limit=30)
    xml = _build_rss_xml(tools, f"IndieStack — {slug.replace('-', ' ').title()} Tools",
                          f"Indie tools in the {slug.replace('-', ' ')} category",
                          f"https://indiestack.fly.dev/category/{slug}/rss")
    return Response(content=xml, media_type="application/rss+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


@app.get("/tag/{slug}/rss")
async def rss_tag(request: Request, slug: str):
    """RSS feed for a specific tag."""
    tools = await db.get_tools_for_rss(request.state.db, tag=slug.replace('-', ' '), limit=30)
    xml = _build_rss_xml(tools, f"IndieStack — #{slug} Tools",
                          f"Indie tools tagged with {slug.replace('-', ' ')}",
                          f"https://indiestack.fly.dev/tag/{slug}/rss")
    return Response(content=xml, media_type="application/rss+xml",
                    headers={"Cache-Control": "public, max-age=3600"})


# ── Mount routes ──────────────────────────────────────────────────────────

app.include_router(landing.router)
app.include_router(browse.router)
app.include_router(tool.router)
app.include_router(search.router)
app.include_router(submit.router)
app.include_router(admin.router)
app.include_router(purchase.router)
app.include_router(verify.router)
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

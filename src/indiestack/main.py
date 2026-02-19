"""FastAPI app, middleware, router wiring, upvote API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response

from indiestack import db
from indiestack.routes import landing, browse, tool, search, submit, admin, purchase


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    yield


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None)


# ── DB middleware ─────────────────────────────────────────────────────────

@app.middleware("http")
async def db_middleware(request: Request, call_next):
    request.state.db = await db.get_db()
    try:
        response = await call_next(request)
    finally:
        await request.state.db.close()
    return response


# ── Health ────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


# ── SEO ───────────────────────────────────────────────────────────────────

@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots():
    return "User-agent: *\nAllow: /\nSitemap: https://indiestack.fly.dev/sitemap.xml"


@app.get("/sitemap.xml")
async def sitemap(request: Request):
    urls = [
        ("https://indiestack.fly.dev/", "daily", "1.0"),
        ("https://indiestack.fly.dev/submit", "monthly", "0.5"),
    ]
    d = request.state.db
    cats = await db.get_all_categories(d)
    for c in cats:
        urls.append((f"https://indiestack.fly.dev/category/{c['slug']}", "daily", "0.8"))
    cursor = await d.execute("SELECT slug FROM tools WHERE status = 'approved'")
    tools = await cursor.fetchall()
    for t in tools:
        urls.append((f"https://indiestack.fly.dev/tool/{t['slug']}", "weekly", "0.7"))
    entries = "\n".join(
        f"  <url><loc>{u}</loc><changefreq>{f}</changefreq><priority>{p}</priority></url>"
        for u, f, p in urls
    )
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>"""
    return Response(content=xml, media_type="application/xml")


FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
<rect width="100" height="100" rx="16" fill="#F59E0B"/>
<text x="50" y="72" font-size="60" text-anchor="middle" fill="white" font-family="sans-serif" font-weight="bold">iS</text>
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
    return JSONResponse({"ok": True, "count": count, "upvoted": upvoted})


# ── Mount routes ──────────────────────────────────────────────────────────

app.include_router(landing.router)
app.include_router(browse.router)
app.include_router(tool.router)
app.include_router(search.router)
app.include_router(submit.router)
app.include_router(admin.router)
app.include_router(purchase.router)

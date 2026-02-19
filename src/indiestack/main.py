"""FastAPI app, middleware, router wiring, upvote API."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from indiestack import db
from indiestack.routes import landing, browse, tool, search, submit, admin


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

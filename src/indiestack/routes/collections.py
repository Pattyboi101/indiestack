"""Curated collections — editorially curated tool lists."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card
from indiestack.db import get_all_collections, get_collection_with_tools

router = APIRouter()


@router.get("/collections", response_class=HTMLResponse)
async def collections_index(request: Request):
    db = request.state.db
    collections = await get_all_collections(db)

    if collections:
        cards = ''
        for c in collections:
            emoji = c.get('cover_emoji', '') or '📦'
            title = escape(str(c['title']))
            desc = escape(str(c.get('description', '')))
            slug = escape(str(c['slug']))
            count = c.get('tool_count', 0)
            cards += f"""
            <a href="/collection/{slug}" class="card" style="text-decoration:none;color:inherit;display:block;">
                <span style="font-size:32px;display:block;margin-bottom:8px;">{emoji}</span>
                <h3 style="font-family:var(--font-display);font-size:17px;margin-bottom:6px;color:var(--ink);">{title}</h3>
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:10px;
                          display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;">{desc}</p>
                <span style="font-size:12px;font-weight:600;color:var(--ink-light);background:var(--cream-dark);
                             padding:3px 10px;border-radius:999px;">{count} tool{"s" if count != 1 else ""}</span>
            </a>
            """
        grid_html = f'<div class="card-grid">{cards}</div>'
    else:
        grid_html = """
        <div style="text-align:center;padding:60px 0;">
            <p style="color:var(--ink-muted);font-size:16px;">No collections yet. Check back soon!</p>
        </div>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);">Curated Collections</h1>
            <p style="color:var(--ink-muted);margin-top:8px;font-size:16px;">
                Hand-picked lists of the best indie tools for every use case.
            </p>
        </div>
        {grid_html}
    </div>
    """
    return HTMLResponse(page_shell("Curated Collections", body,
                                    description="Browse curated collections of indie SaaS tools.",
                                    user=request.state.user))


@router.get("/collection/{slug}", response_class=HTMLResponse)
async def collection_detail(request: Request, slug: str):
    db = request.state.db
    coll, tools = await get_collection_with_tools(db, slug)

    if not coll:
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Collection Not Found</h1>
            <p class="text-muted mt-4">We couldn't find that collection.</p>
            <a href="/collections" class="btn btn-primary mt-4">Browse Collections</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body, user=request.state.user), status_code=404)

    title = escape(str(coll['title']))
    desc = escape(str(coll.get('description', '')))
    emoji = coll.get('cover_emoji', '') or '📦'

    if tools:
        cards = '\n'.join(tool_card(t) for t in tools)
        tools_html = f'<div class="card-grid">{cards}</div>'
    else:
        tools_html = """
        <div style="text-align:center;padding:40px 0;">
            <p style="color:var(--ink-muted);">No tools in this collection yet.</p>
        </div>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;">
        <div style="margin-bottom:12px;">
            <a href="/collections" style="color:var(--ink-muted);font-size:14px;">&larr; All Collections</a>
        </div>
        <div style="text-align:center;margin-bottom:40px;">
            <span style="font-size:48px;">{emoji}</span>
            <h1 style="font-family:var(--font-display);font-size:36px;margin-top:8px;color:var(--ink);">{title}</h1>
            <p style="color:var(--ink-muted);margin-top:8px;font-size:16px;max-width:600px;margin-left:auto;margin-right:auto;">{desc}</p>
        </div>
        {tools_html}
    </div>
    """
    return HTMLResponse(page_shell(title, body, description=coll.get('description', ''),
                                    user=request.state.user))

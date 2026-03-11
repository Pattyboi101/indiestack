"""Recently added tools — chronological feed."""

import math
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card, pagination_html
from indiestack.db import get_recent_tools_paginated

router = APIRouter()

PER_PAGE = 12


@router.get("/new", response_class=HTMLResponse)
async def new_tools(request: Request, page: int = 1):
    db = request.state.db
    if page < 1:
        page = 1

    tools, total = await get_recent_tools_paginated(db, page=page, per_page=PER_PAGE)
    total_pages = max(1, math.ceil(total / PER_PAGE))

    if tools:
        cards = '\n'.join(tool_card(t) for t in tools)
        tools_html = f"""
        <div class="card-grid">{cards}</div>
        {pagination_html(page, total_pages, "/new")}
        """
    else:
        tools_html = """
        <div style="text-align:center;padding:60px 0;">
            <p style="font-size:18px;color:var(--ink-muted);">No creations yet. Be the first!</p>
            <a href="/submit" class="btn btn-primary mt-4">Submit Yours</a>
        </div>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);">Recently Added</h1>
            <p style="color:var(--ink-muted);margin-top:8px;font-size:16px;">
                The latest indie creations, fresh off the press.
            </p>
        </div>
        {tools_html}
    </div>
    """
    return HTMLResponse(page_shell("Recently Added", body,
                                    description="Discover the latest indie creations added to IndieStack.",
                                    user=request.state.user))

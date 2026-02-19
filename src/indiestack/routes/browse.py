"""Category browse page."""

import math
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card, pagination_html
from indiestack.db import get_category_by_slug, get_tools_by_category

router = APIRouter()

PER_PAGE = 12


@router.get("/category/{slug}", response_class=HTMLResponse)
async def category_page(request: Request, slug: str, page: int = 1):
    db = request.state.db
    category = await get_category_by_slug(db, slug)

    if not category:
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Category Not Found</h1>
            <p class="text-muted mt-4">We couldn't find that category.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body), status_code=404)

    if page < 1:
        page = 1

    tools, total = await get_tools_by_category(db, int(category['id']), page=page, per_page=PER_PAGE)
    total_pages = max(1, math.ceil(total / PER_PAGE))

    icon = str(category.get('icon', ''))
    name = escape(str(category['name']))
    desc = escape(str(category.get('description', '')))

    if tools:
        cards = '\n'.join(tool_card(t) for t in tools)
        tools_html = f"""
        <div class="card-grid">{cards}</div>
        {pagination_html(page, total_pages, f"/category/{slug}")}
        """
    else:
        tools_html = """
        <div style="text-align:center;padding:60px 0;">
            <p style="font-size:18px;color:var(--stone-400);">No tools in this category yet.</p>
            <a href="/submit" class="btn btn-primary mt-4">Submit the first one</a>
        </div>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <span style="font-size:48px;">{icon}</span>
            <h1 style="font-family:var(--font-display);font-size:36px;margin-top:8px;">{name}</h1>
            <p class="text-muted mt-2">{desc}</p>
        </div>
        {tools_html}
    </div>
    """
    return HTMLResponse(page_shell(name, body, description=desc))

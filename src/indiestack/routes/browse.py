"""Category browse page."""

import json
import math
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card, pagination_html
from indiestack.db import get_category_by_slug, get_tools_by_category, get_category_tools_for_compare

router = APIRouter()

PER_PAGE = 12


@router.get("/category/{slug}", response_class=HTMLResponse)
async def category_page(request: Request, slug: str, page: int = 1):
    db = request.state.db
    category = await get_category_by_slug(db, slug)

    if not category:
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Category Not Found</h1>
            <p class="text-muted mt-4">We couldn't find that category.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body, user=request.state.user), status_code=404)

    if page < 1:
        page = 1

    tools, total = await get_tools_by_category(db, int(category['id']), page=page, per_page=PER_PAGE)
    total_pages = max(1, math.ceil(total / PER_PAGE))

    icon = str(category.get('icon', ''))
    name = escape(str(category['name']))
    desc = escape(str(category.get('description', '')))

    if tools:
        cards = '\n'.join(tool_card(t) for t in tools)

        # Compare links for categories with 2+ tools
        compare_html = ''
        if len(tools) >= 2:
            compare_tools = await get_category_tools_for_compare(db, int(category['id']), limit=6)
            if len(compare_tools) >= 2:
                compare_links = []
                for i in range(len(compare_tools)):
                    for j in range(i + 1, min(i + 2, len(compare_tools))):
                        s1 = escape(str(compare_tools[i]['slug']))
                        s2 = escape(str(compare_tools[j]['slug']))
                        n1 = escape(str(compare_tools[i]['name']))
                        n2 = escape(str(compare_tools[j]['name']))
                        compare_links.append(
                            f'<a href="/compare/{s1}-vs-{s2}" style="color:var(--terracotta);font-size:13px;">{n1} vs {n2}</a>'
                        )
                    if len(compare_links) >= 3:
                        break
                if compare_links:
                    compare_html = f"""
                    <div style="margin-top:24px;padding:16px;background:var(--cream-dark);border-radius:var(--radius-sm);text-align:center;">
                        <span style="font-size:13px;color:var(--ink-muted);font-weight:600;">Compare tools: </span>
                        {' &middot; '.join(compare_links)}
                    </div>
                    """

        tools_html = f"""
        <div class="card-grid">{cards}</div>
        {compare_html}
        {pagination_html(page, total_pages, f"/category/{slug}")}
        """
    else:
        tools_html = """
        <div style="text-align:center;padding:60px 0;">
            <p style="font-size:18px;color:var(--ink-muted);">No tools in this category yet.</p>
            <a href="/submit" class="btn btn-primary mt-4">Submit the first one</a>
        </div>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <span style="font-size:48px;">{icon}</span>
            <h1 style="font-family:var(--font-display);font-size:36px;margin-top:8px;color:var(--ink);">{name}</h1>
            <p class="text-muted mt-2">{desc}</p>
        </div>
        {tools_html}
    </div>
    """
    # JSON-LD ItemList for rich snippets
    json_ld_data = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": str(category['name']),
        "description": str(category.get('description', '')),
        "url": f"https://indiestack.fly.dev/category/{slug}",
        "numberOfItems": total,
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "url": f"https://indiestack.fly.dev/tool/{t['slug']}",
                "name": str(t['name']),
            }
            for i, t in enumerate(tools)
        ]
    }
    extra_head = f'<script type="application/ld+json">{json.dumps(json_ld_data, ensure_ascii=False)}</script>'

    return HTMLResponse(page_shell(name, body, description=desc, user=request.state.user, extra_head=extra_head))

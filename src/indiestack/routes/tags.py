"""Programmatic tag pages for SEO and discovery."""

import json
from math import ceil
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card, pagination_html
from indiestack.db import get_all_tags_with_counts, get_tools_by_tag

router = APIRouter()


@router.get("/tags", response_class=HTMLResponse)
async def tags_index(request: Request):
    """Index page showing all tags with usage counts."""
    db = request.state.db
    user = request.state.user
    tags = await get_all_tags_with_counts(db, min_count=1)

    if tags:
        # Group by first letter for nice presentation
        tag_cards = []
        for t in tags:
            tag_name = escape(t['tag'])
            tag_slug = escape(t['slug'])
            count = t['count']
            tag_cards.append(f'''
                <a href="/tag/{tag_slug}" class="card" style="text-decoration:none;color:inherit;display:flex;align-items:center;justify-content:space-between;padding:16px 20px;">
                    <span style="font-family:var(--font-mono);font-size:14px;font-weight:600;color:var(--ink);">{tag_name}</span>
                    <span style="font-size:13px;color:var(--ink-muted);background:var(--cream-dark);padding:3px 10px;border-radius:999px;">{count} tool{"s" if count != 1 else ""}</span>
                </a>
            ''')
        tags_grid = f'''
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;">
            {"".join(tag_cards)}
        </div>
        '''
    else:
        tags_grid = '<p style="color:var(--ink-muted);text-align:center;padding:40px;">No tags found.</p>'

    body = f'''
    <div class="container" style="padding:48px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin-bottom:8px;">Browse by Tag</h1>
            <p style="color:var(--ink-muted);font-size:16px;">{len(tags)} tags across all indie tools. Click any tag to explore.</p>
        </div>
        {tags_grid}
    </div>
    <style>
        @media (max-width: 768px) {{
            div[style*="grid-template-columns:repeat(3"] {{ grid-template-columns: repeat(2, 1fr) !important; }}
        }}
        @media (max-width: 480px) {{
            div[style*="grid-template-columns:repeat(3"] {{ grid-template-columns: 1fr !important; }}
        }}
    </style>
    '''
    return HTMLResponse(page_shell(title="Browse by Tag", body=body,
                                    description="Browse indie SaaS tools by tag — find tools for APIs, analytics, automation, and more.",
                                    user=user))


@router.get("/tag/{slug}", response_class=HTMLResponse)
async def tag_detail(request: Request, slug: str):
    """Individual tag page showing all tools with that tag."""
    db = request.state.db
    user = request.state.user

    try:
        page_num = int(request.query_params.get("page", "1") or "1")
    except (ValueError, TypeError):
        page_num = 1

    # The slug IS the tag name (lowercased, hyphenated)
    # We need to find the actual tag name — search through tags
    all_tags = await get_all_tags_with_counts(db, min_count=1)
    tag_info = None
    for t in all_tags:
        if t['slug'] == slug:
            tag_info = t
            break

    if not tag_info:
        body = '''
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Tag Not Found</h1>
            <p class="text-muted mt-4">We couldn't find that tag.</p>
            <a href="/tags" class="btn btn-primary mt-4">Browse all tags</a>
        </div>
        '''
        return HTMLResponse(page_shell("Tag Not Found", body, user=user), status_code=404)

    tag_name = tag_info['tag']
    safe_tag = escape(tag_name)

    tools, total = await get_tools_by_tag(db, tag_name, page=page_num, per_page=12)
    total_pages = max(1, ceil(total / 12))

    if tools:
        cards = '\n'.join(tool_card(t) for t in tools)
        tools_html = f'''
        <div class="card-grid">{cards}</div>
        {pagination_html(page_num, total_pages, f"/tag/{escape(slug)}")}
        '''
    else:
        tools_html = '''
        <div style="text-align:center;padding:60px 0;">
            <p style="font-size:18px;color:var(--ink-muted);">No tools with this tag yet.</p>
            <a href="/submit" class="btn btn-primary mt-4">Submit the first one</a>
        </div>
        '''

    # JSON-LD for SEO
    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": f"Indie tools tagged '{tag_name}'",
        "description": f"Discover {total} indie SaaS tools tagged with '{tag_name}' on IndieStack.",
        "url": f"https://indiestack.fly.dev/tag/{slug}",
        "numberOfItems": total,
    })

    # Related tags — show other tags that appear on the same tools
    # Simple approach: just show a few other popular tags
    related_pills = []
    for t in all_tags[:10]:
        if t['slug'] != slug:
            related_pills.append(f'<a href="/tag/{escape(t["slug"])}" style="display:inline-block;padding:4px 12px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid var(--border);color:var(--ink-light);text-decoration:none;font-family:var(--font-mono);">{escape(t["tag"])}</a>')
    related_html = ''
    if related_pills:
        related_html = f'''
        <div style="margin-top:32px;padding:20px;background:var(--cream-dark);border-radius:var(--radius);">
            <span style="font-size:13px;font-weight:600;color:var(--ink-muted);display:block;margin-bottom:10px;">Related Tags</span>
            <div style="display:flex;gap:6px;flex-wrap:wrap;">{"".join(related_pills[:8])}</div>
        </div>
        '''

    body = f'''
    <div class="container" style="padding:48px 24px;">
        <div style="margin-bottom:32px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
                <a href="/tags" style="color:var(--ink-muted);font-size:14px;">&larr; All tags</a>
            </div>
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin-bottom:8px;">
                <span style="font-family:var(--font-mono);background:var(--cream-dark);padding:4px 16px;border-radius:var(--radius-sm);border:1px solid var(--border);">{safe_tag}</span>
            </h1>
            <p style="color:var(--ink-muted);font-size:16px;">{total} indie tool{"s" if total != 1 else ""} tagged with &ldquo;{safe_tag}&rdquo;</p>
        </div>
        {tools_html}
        {related_html}
    </div>
    '''

    desc = f"Discover {total} indie SaaS tools tagged with '{tag_name}'. Save your tokens — use indie builds."
    return HTMLResponse(page_shell(
        title=f"Tools tagged '{safe_tag}'",
        body=body,
        description=desc,
        user=user,
        extra_head=f'<script type="application/ld+json">{json_ld}</script>',
        canonical=f"/tag/{slug}",
    ))

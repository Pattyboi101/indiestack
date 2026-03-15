"""Programmatic tag pages for SEO and discovery."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.routes.components import page_shell
from indiestack.db import get_all_tags_with_counts

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
                    <span style="font-size:13px;color:var(--ink-muted);background:var(--cream-dark);padding:4px 8px;border-radius:999px;">{count} tool{"s" if count != 1 else ""}</span>
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
            <p style="color:var(--ink-muted);font-size:16px;">{len(tags)} tags across all developer tools. Click any tag to explore.</p>
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
    return HTMLResponse(page_shell(title="Browse by Tag — Indie Software Directory | IndieStack", body=body,
                                    description="Browse developer tools by tag — find tools for APIs, analytics, automation, and more.",
                                    user=user, canonical="/tags"))


@router.get("/tag/{slug}")
async def tag_detail(request: Request, slug: str):
    """Redirect individual tag pages to /explore?tag={slug}."""
    return RedirectResponse(url=f"/explore?tag={slug}", status_code=302)

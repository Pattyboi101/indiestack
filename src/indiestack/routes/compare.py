"""Side-by-side tool comparisons."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, verified_badge_html
from indiestack.db import get_tools_for_comparison

router = APIRouter()


def format_price(pence) -> str:
    if not pence or pence <= 0:
        return "Free"
    pounds = pence / 100
    if pounds == int(pounds):
        return f"\u00a3{int(pounds)}"
    return f"\u00a3{pounds:.2f}"


def tool_column(tool: dict) -> str:
    """Render one side of the comparison."""
    name = escape(str(tool['name']))
    tagline = escape(str(tool['tagline']))
    description = escape(str(tool['description']))
    slug = escape(str(tool['slug']))
    url = escape(str(tool['url']))
    cat_name = escape(str(tool.get('category_name', '')))
    upvotes = int(tool.get('upvote_count', 0))
    is_verified = bool(tool.get('is_verified', 0))
    tags = str(tool.get('tags', ''))
    price_pence = tool.get('price_pence')

    badge = verified_badge_html() if is_verified else '<span style="color:var(--ink-muted);font-size:13px;">Not verified</span>'
    price_str = format_price(price_pence)

    tag_html = ''
    if tags.strip():
        tag_list = [t.strip() for t in tags.split(',') if t.strip()][:5]
        tag_html = '<div style="display:flex;gap:6px;flex-wrap:wrap;">'
        for t in tag_list:
            tag_html += f'<span class="tag">{escape(t)}</span>'
        tag_html += '</div>'

    return f"""
    <div style="flex:1;min-width:280px;">
        <div style="text-align:center;padding-bottom:24px;border-bottom:1px solid var(--border);margin-bottom:20px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:8px;">
                <a href="/tool/{slug}" style="color:var(--ink);">{name}</a>
            </h2>
            {badge}
        </div>
        <div style="display:flex;flex-direction:column;gap:20px;">
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:6px;">Tagline</div>
                <p style="color:var(--ink-light);font-size:15px;">{tagline}</p>
            </div>
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:6px;">Description</div>
                <p style="color:var(--ink-light);font-size:14px;line-height:1.6;
                          display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden;">{description}</p>
            </div>
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:6px;">Price</div>
                <span style="font-family:var(--font-display);font-size:20px;color:var(--ink);">{price_str}</span>
            </div>
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:6px;">Category</div>
                <span class="tag">{cat_name}</span>
            </div>
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:6px;">Upvotes</div>
                <span style="font-family:var(--font-display);font-size:20px;color:var(--slate-dark);">&#9650; {upvotes}</span>
            </div>
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:6px;">Tags</div>
                {tag_html if tag_html else '<span style="color:var(--ink-muted);font-size:14px;">No tags</span>'}
            </div>
            <a href="/tool/{slug}" class="btn btn-primary" style="text-align:center;justify-content:center;margin-top:8px;">
                View Tool &rarr;
            </a>
        </div>
    </div>
    """


@router.get("/compare/{slugs}", response_class=HTMLResponse)
async def compare_tools(request: Request, slugs: str):
    db = request.state.db

    parts = slugs.split("-vs-", 1)
    if len(parts) != 2:
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Invalid Comparison</h1>
            <p class="text-muted mt-4">Use the format: /compare/tool1-vs-tool2</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Invalid Comparison", body, user=request.state.user), status_code=400)

    slug1, slug2 = parts[0].strip(), parts[1].strip()
    tool1, tool2 = await get_tools_for_comparison(db, slug1, slug2)

    if not tool1 or not tool2:
        missing = slug1 if not tool1 else slug2
        body = f"""
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Tool Not Found</h1>
            <p class="text-muted mt-4">Couldn't find "{escape(missing)}".</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body, user=request.state.user), status_code=404)

    if tool1['status'] != 'approved' or tool2['status'] != 'approved':
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Comparison Unavailable</h1>
            <p class="text-muted mt-4">One or both tools are not yet approved.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Unavailable", body, user=request.state.user), status_code=404)

    name1 = escape(str(tool1['name']))
    name2 = escape(str(tool2['name']))
    title = f"{tool1['name']} vs {tool2['name']}"

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:900px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">
                {name1} <span style="color:var(--ink-muted);font-weight:normal;">vs</span> {name2}
            </h1>
            <p style="color:var(--ink-muted);margin-top:8px;">Side-by-side comparison of these indie tools</p>
        </div>
        <div style="display:flex;gap:32px;flex-wrap:wrap;">
            {tool_column(tool1)}
            <div style="width:1px;background:var(--border);align-self:stretch;flex-shrink:0;"></div>
            {tool_column(tool2)}
        </div>
    </div>
    """
    return HTMLResponse(page_shell(f"{name1} vs {name2} — Indie Tool Comparison | IndieStack", body,
                                    user=request.state.user,
                                    description=f"Compare {tool1['name']} vs {tool2['name']} side-by-side. Features, pricing, and community ratings on IndieStack.",
                                    canonical=f"/compare/{slug1}-vs-{slug2}"))

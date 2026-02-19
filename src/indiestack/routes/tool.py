"""Tool detail page."""

import json
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card, verified_badge_html
from indiestack.db import get_tool_by_slug, get_related_tools

router = APIRouter()


def format_price(pence: int) -> str:
    """Format pence as display string."""
    pounds = pence / 100
    if pounds == int(pounds):
        return f"\u00a3{int(pounds)}"
    return f"\u00a3{pounds:.2f}"


@router.get("/tool/{slug}", response_class=HTMLResponse)
async def tool_detail(request: Request, slug: str):
    db = request.state.db
    tool = await get_tool_by_slug(db, slug)

    if not tool or tool['status'] != 'approved':
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Tool Not Found</h1>
            <p class="text-muted mt-4">This tool doesn't exist or hasn't been approved yet.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body), status_code=404)

    name = escape(str(tool['name']))
    tagline = escape(str(tool['tagline']))
    description = escape(str(tool['description']))
    url = escape(str(tool['url']))
    maker_name = escape(str(tool.get('maker_name', '')))
    maker_url = escape(str(tool.get('maker_url', '')))
    cat_name = escape(str(tool.get('category_name', '')))
    cat_slug = escape(str(tool.get('category_slug', '')))
    upvotes = int(tool.get('upvote_count', 0))
    tags = str(tool.get('tags', ''))
    is_verified = bool(tool.get('is_verified', 0))
    tool_id = tool['id']
    price_pence = tool.get('price_pence')

    # Tags
    tag_html = ''
    if tags.strip():
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        tag_html = '<div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:16px;">'
        for t in tag_list:
            tag_html += f'<span class="tag">{escape(t)}</span>'
        tag_html += '</div>'

    # Maker info
    maker_html = ''
    if maker_name:
        if maker_url:
            maker_html = f'<p class="text-muted text-sm mt-4">Built by <a href="{maker_url}" target="_blank" rel="noopener">{maker_name}</a></p>'
        else:
            maker_html = f'<p class="text-muted text-sm mt-4">Built by {maker_name}</p>'

    # Price tag
    price_tag_html = ''
    if price_pence and price_pence > 0:
        price_display = format_price(price_pence)
        price_tag_html = f"""
        <span style="display:inline-flex;align-items:center;gap:6px;font-family:var(--font-display);
                     font-size:24px;font-weight:700;color:var(--violet);margin-top:12px;">
            {price_display}
        </span>
        """

    # CTA button — "Buy Now" for paid tools, "Visit Website" for free
    if price_pence and price_pence > 0:
        price_display = format_price(price_pence)
        cta_html = f"""
        <form method="post" action="/api/checkout" style="display:inline;">
            <input type="hidden" name="tool_id" value="{tool_id}">
            <button type="submit" class="btn btn-violet" style="font-size:16px;padding:14px 32px;">
                Buy Now {price_display} &rarr;
            </button>
        </form>
        """
    else:
        cta_html = f"""
        <a href="{url}" target="_blank" rel="noopener" class="btn btn-primary" style="font-size:16px;padding:14px 32px;">
            Visit Website &rarr;
        </a>
        """

    # JSON-LD
    json_ld_data = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": tool['name'],
        "description": tool['tagline'],
        "url": tool['url'],
        "applicationCategory": tool.get('category_name', ''),
    }
    if price_pence and price_pence > 0:
        json_ld_data["offers"] = {
            "@type": "Offer",
            "price": f"{price_pence / 100:.2f}",
            "priceCurrency": "GBP",
        }
    json_ld = json.dumps(json_ld_data)
    extra_head = f'<script type="application/ld+json">{json_ld}</script>'

    # Related tools
    related = await get_related_tools(db, tool_id, int(tool['category_id']))
    related_html = ''
    if related:
        related_cards = '\n'.join(tool_card(r) for r in related)
        related_html = f"""
        <div style="margin-top:64px;">
            <h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:20px;">
                More in {cat_name}
            </h2>
            <div class="card-grid">{related_cards}</div>
        </div>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:800px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:24px;">
            <div style="flex:1;">
                <a href="/category/{cat_slug}" class="tag mb-2" style="display:inline-block;">{cat_name}</a>
                <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:8px;">
                    <h1 style="font-family:var(--font-display);font-size:36px;">{name}</h1>
                    {verified_badge_html() if is_verified else ''}
                </div>
                <p style="font-size:18px;color:var(--stone-500);margin-top:8px;">{tagline}</p>
                {price_tag_html}
            </div>
            <button class="upvote-btn" onclick="upvote({tool_id})" id="upvote-{tool_id}"
                    style="flex-shrink:0;min-width:60px;">
                <span class="arrow">&#9650;</span>
                <span id="count-{tool_id}">{upvotes}</span>
            </button>
        </div>

        <div style="margin-top:32px;">
            <p style="white-space:pre-line;color:var(--stone-700);line-height:1.8;font-size:16px;">{description}</p>
        </div>

        <div style="margin-top:32px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
            {cta_html}
            {maker_html}
        </div>

        {tag_html}
        {related_html}
    </div>
    """
    return HTMLResponse(page_shell(name, body, description=tagline, extra_head=extra_head))

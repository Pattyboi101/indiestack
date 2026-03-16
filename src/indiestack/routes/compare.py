"""Side-by-side tool comparisons."""

import json as _json
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell
from indiestack.db import get_tools_for_comparison

router = APIRouter()


def format_price(pence) -> str:
    if not pence or pence <= 0:
        return "Free"
    pounds = pence / 100
    if pounds == int(pounds):
        return f"\u00a3{int(pounds)}"
    return f"\u00a3{pounds:.2f}"


def _health_badge(status: str) -> str:
    """Render a colored health-status pill."""
    colors = {
        'active': ('var(--success-bg, #D1FAE5)', 'var(--success-text, #065F46)'),
        'stale': ('#FEF3C7', '#92400E'),
        'dead': ('#FEE2E2', '#991B1B'),
    }
    bg, fg = colors.get(status, ('#F3F4F6', '#6B7280'))
    label = escape(status.capitalize()) if status else 'Unknown'
    return (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;'
        f'font-size:12px;font-weight:600;background:{bg};color:{fg};">{label}</span>'
    )


def _intelligence_section(tool: dict) -> str:
    """Render agent-verified intelligence badges for a tool."""
    parts = []

    # Health status
    health = tool.get('health_status') or 'unknown'
    parts.append(f'''
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:8px;">Health</div>
                {_health_badge(health)}
            </div>''')

    # GitHub stars
    stars = tool.get('github_stars')
    if stars and int(stars) > 0:
        star_count = int(stars)
        display = f'{star_count:,}'
        github_url = tool.get('github_url', '')
        star_inner = f'<a href="{escape(str(github_url))}" target="_blank" rel="noopener" style="color:var(--ink);text-decoration:none;">&#9733; {display}</a>' if github_url else f'&#9733; {display}'
        parts.append(f'''
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:8px;">GitHub Stars</div>
                <span style="font-family:var(--font-display);font-size:20px;color:var(--ink);">{star_inner}</span>
            </div>''')

    # Agent citations
    mcp_views = tool.get('mcp_view_count')
    if mcp_views and int(mcp_views) > 0:
        count = int(mcp_views)
        parts.append(f'''
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:8px;">Agent Citations</div>
                <span style="font-size:14px;color:var(--ink-light);">Recommended by AI agents {count:,} time{"s" if count != 1 else ""}</span>
            </div>''')

    return ''.join(parts)


def tool_column(tool: dict) -> str:
    """Render one side of the comparison."""
    name = escape(str(tool['name']))
    tagline = escape(str(tool['tagline']))
    description = escape(str(tool['description']))
    slug = escape(str(tool['slug']))
    url = escape(str(tool['url']))
    cat_name = escape(str(tool.get('category_name', '')))
    upvotes = int(tool.get('upvote_count', 0))
    tags = str(tool.get('tags', ''))
    price_pence = tool.get('price_pence')
    price_str = format_price(price_pence)

    tag_html = ''
    if tags.strip():
        tag_list = [t.strip() for t in tags.split(',') if t.strip()][:5]
        tag_html = '<div style="display:flex;gap:8px;flex-wrap:wrap;">'
        for t in tag_list:
            tag_html += f'<span class="tag">{escape(t)}</span>'
        tag_html += '</div>'

    return f"""
    <div style="flex:1;min-width:280px;">
        <div style="text-align:center;padding-bottom:24px;border-bottom:1px solid var(--border);margin-bottom:24px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:8px;">
                <a href="/tool/{slug}" style="color:var(--ink);">{name}</a>
            </h2>
        </div>
        <div style="display:flex;flex-direction:column;gap:20px;">
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:8px;">Tagline</div>
                <p style="color:var(--ink-light);font-size:15px;">{tagline}</p>
            </div>
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:8px;">Description</div>
                <p style="color:var(--ink-light);font-size:14px;line-height:1.6;
                          display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden;">{description}</p>
            </div>
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:8px;">Price</div>
                <span style="font-family:var(--font-display);font-size:20px;color:var(--ink);">{price_str}</span>
            </div>
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:8px;">Category</div>
                <span class="tag">{cat_name}</span>
            </div>
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:8px;">Upvotes</div>
                <span style="font-family:var(--font-display);font-size:20px;color:var(--slate-dark);">&#9650; {upvotes}</span>
            </div>
            <div>
                <div style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;margin-bottom:8px;">Tags</div>
                {tag_html if tag_html else '<span style="color:var(--ink-muted);font-size:14px;">No tags</span>'}
            </div>
            {_intelligence_section(tool)}
            <a href="/tool/{slug}" class="btn btn-primary" style="text-align:center;justify-content:center;margin-top:8px;">
                View Tool &rarr;
            </a>
        </div>
    </div>
    """


@router.get("/compare/{slugs}", response_class=HTMLResponse)
async def compare_tools(request: Request, slugs: str):
    d = request.state.db

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
    tool1, tool2 = await get_tools_for_comparison(d, slug1, slug2)

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

    # --- Compatibility banner ---
    a_slug, b_slug = sorted([slug1, slug2])
    pair_cursor = await d.execute(
        "SELECT success_count, source FROM tool_pairs WHERE tool_a_slug = ? AND tool_b_slug = ?",
        (a_slug, b_slug)
    )
    pair = await pair_cursor.fetchone()

    conflict_cursor = await d.execute(
        "SELECT reason, report_count FROM tool_conflicts WHERE tool_a_slug = ? AND tool_b_slug = ?",
        (a_slug, b_slug)
    )
    conflict = await conflict_cursor.fetchone()

    if conflict:
        reason = escape(str(conflict['reason'] or 'Potential overlap detected'))
        compat_banner = f'''
        <div style="padding:14px 20px;border-radius:var(--radius-sm);margin-bottom:32px;
                    background:#FEF3C7;border:1px solid #F59E0B;display:flex;align-items:center;gap:10px;">
            <span style="font-size:18px;">&#9888;</span>
            <span style="font-size:14px;color:#92400E;font-weight:500;">Compatibility warning: {reason}</span>
        </div>'''
    elif pair and int(pair['success_count']) > 0:
        sc = int(pair['success_count'])
        compat_banner = f'''
        <div style="padding:14px 20px;border-radius:var(--radius-sm);margin-bottom:32px;
                    background:var(--success-bg, #D1FAE5);border:1px solid var(--success-text, #065F46);display:flex;align-items:center;gap:10px;">
            <span style="font-size:18px;">&#10003;</span>
            <span style="font-size:14px;color:var(--success-text, #065F46);font-weight:500;">These tools work well together &mdash; verified in {sc} agent report{"s" if sc != 1 else ""}</span>
        </div>'''
    elif pair:
        compat_banner = '''
        <div style="padding:14px 20px;border-radius:var(--radius-sm);margin-bottom:32px;
                    background:var(--cream-dark);border:1px solid var(--border);display:flex;align-items:center;gap:10px;">
            <span style="font-size:18px;color:var(--ink-muted);">&#8596;</span>
            <span style="font-size:14px;color:var(--ink-muted);font-weight:500;">These tools may be compatible (inferred from shared framework support)</span>
        </div>'''
    else:
        compat_banner = '''
        <div style="padding:14px 20px;border-radius:var(--radius-sm);margin-bottom:32px;
                    background:var(--cream-dark);border:1px solid var(--border);display:flex;align-items:center;gap:10px;">
            <span style="font-size:18px;color:var(--ink-muted);">&#63;</span>
            <span style="font-size:14px;color:var(--ink-muted);font-weight:500;">No compatibility data yet</span>
        </div>'''

    # --- JSON-LD structured data ---
    def _software_ld(tool):
        ld = {
            "@type": "SoftwareApplication",
            "name": tool['name'],
            "applicationCategory": tool.get('category_name', ''),
            "description": tool.get('tagline', ''),
        }
        if tool.get('url'):
            ld["url"] = tool['url']
        if tool.get('has_free_tier'):
            ld["offers"] = {"@type": "Offer", "price": "0", "priceCurrency": "GBP"}
        return ld

    jsonld = _json.dumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": f"{tool1['name']} vs {tool2['name']} — Indie Tool Comparison",
        "description": f"Compare {tool1['name']} vs {tool2['name']} side-by-side.",
        "url": f"{BASE_URL}/compare/{slug1}-vs-{slug2}",
        "mainEntity": [_software_ld(tool1), _software_ld(tool2)],
    })
    extra_head = f'<script type="application/ld+json">{jsonld}</script>'

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:900px;">
        <div style="text-align:center;margin-bottom:24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">
                {name1} <span style="color:var(--ink-muted);font-weight:normal;">vs</span> {name2}
            </h1>
            <p style="color:var(--ink-muted);margin-top:8px;">Side-by-side comparison of these developer tools</p>
        </div>
        {compat_banner}
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
                                    canonical=f"/compare/{slug1}-vs-{slug2}",
                                    extra_head=extra_head))

"""Side-by-side tool comparisons."""

import json as _json
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell
from indiestack.db import get_tools_for_comparison

router = APIRouter()


def _safe_jld(data) -> str:
    return (
        _json.dumps(data, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


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
        'active': ('var(--success-bg)', 'var(--success-text)'),
        'stale': ('var(--warning-bg)', 'var(--warning-text)'),
        'dead': ('var(--error-bg)', 'var(--error-text)'),
    }
    bg, fg = colors.get(status, ('var(--cream-dark)', 'var(--ink-muted)'))
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
    cat1 = escape(str(tool1.get('category_name', '')))
    cat2 = escape(str(tool2.get('category_name', '')))
    price1 = format_price(tool1.get('price_pence'))
    price2 = format_price(tool2.get('price_pence'))
    upvotes1 = int(tool1.get('upvote_count', 0))
    upvotes2 = int(tool2.get('upvote_count', 0))
    health1 = tool1.get('health_status') or 'unknown'
    health2 = tool2.get('health_status') or 'unknown'

    # --- Compatibility banner (Patrick's feature) ---
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
                    background:var(--warning-bg);border:1px solid var(--warning-border);display:flex;align-items:center;gap:10px;">
            <span style="font-size:18px;">&#9888;</span>
            <span style="font-size:14px;color:var(--warning-text);font-weight:500;">Compatibility warning: {reason}</span>
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

    # --- Quick comparison table ---
    table_html = f"""
    <div style="overflow-x:auto;margin-bottom:40px;">
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
            <thead>
                <tr style="border-bottom:2px solid var(--border);">
                    <th style="text-align:left;padding:12px 16px;color:var(--ink-muted);font-size:12px;text-transform:uppercase;font-weight:600;"></th>
                    <th style="text-align:center;padding:12px 16px;font-family:var(--font-display);font-size:16px;color:var(--ink);">{name1}</th>
                    <th style="text-align:center;padding:12px 16px;font-family:var(--font-display);font-size:16px;color:var(--ink);">{name2}</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom:1px solid var(--border);">
                    <td style="padding:12px 16px;font-weight:600;color:var(--ink-muted);font-size:13px;">Category</td>
                    <td style="padding:12px 16px;text-align:center;color:var(--ink);">{cat1}</td>
                    <td style="padding:12px 16px;text-align:center;color:var(--ink);">{cat2}</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border);">
                    <td style="padding:12px 16px;font-weight:600;color:var(--ink-muted);font-size:13px;">Price</td>
                    <td style="padding:12px 16px;text-align:center;color:var(--ink);">{price1}</td>
                    <td style="padding:12px 16px;text-align:center;color:var(--ink);">{price2}</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border);">
                    <td style="padding:12px 16px;font-weight:600;color:var(--ink-muted);font-size:13px;">Upvotes</td>
                    <td style="padding:12px 16px;text-align:center;color:var(--ink);">&#9650; {upvotes1}</td>
                    <td style="padding:12px 16px;text-align:center;color:var(--ink);">&#9650; {upvotes2}</td>
                </tr>
                <tr style="border-bottom:1px solid var(--border);">
                    <td style="padding:12px 16px;font-weight:600;color:var(--ink-muted);font-size:13px;">Health</td>
                    <td style="padding:12px 16px;text-align:center;">{_health_badge(health1)}</td>
                    <td style="padding:12px 16px;text-align:center;">{_health_badge(health2)}</td>
                </tr>
            </tbody>
        </table>
    </div>
    """

    # --- JSON-LD: WebPage + SoftwareApplication (Patrick's) + FAQ (Ed's) ---
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

    webpage_ld = _safe_jld({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": f"{tool1['name']} vs {tool2['name']} -- Agent-Verified Comparison",
        "description": f"Compare {tool1['name']} vs {tool2['name']} side-by-side with real community data.",
        "url": f"{BASE_URL}/compare/{slug1}-vs-{slug2}",
        "mainEntity": [_software_ld(tool1), _software_ld(tool2)],
    })

    faq_ld = _safe_jld({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"Which is better, {tool1['name']} or {tool2['name']}?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"{tool1['name']} and {tool2['name']} are both developer tools on IndieStack. {tool1['name']} has {upvotes1} upvotes while {tool2['name']} has {upvotes2}. See the full comparison at IndieStack."
                }
            },
            {
                "@type": "Question",
                "name": f"What is the difference between {tool1['name']} and {tool2['name']}?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"{tool1['name']}: {tool1.get('tagline', '')}. {tool2['name']}: {tool2.get('tagline', '')}. Compare features, pricing, and community ratings side-by-side on IndieStack."
                }
            }
        ]
    })

    extra_head = (
        f'<script type="application/ld+json">{webpage_ld}</script>\n'
        f'    <script type="application/ld+json">{faq_ld}</script>'
    )

    # --- FAQ HTML section ---
    faq_html = f"""
    <div style="margin-top:40px;">
        <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:16px;">
            Frequently Asked Questions
        </h2>
        <details style="margin-bottom:12px;border:1px solid var(--border);border-radius:var(--radius-sm);padding:0;">
            <summary style="padding:14px 16px;font-weight:600;font-size:15px;color:var(--ink);cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between;">
                Which is better, {name1} or {name2}?
                <span style="font-size:18px;color:var(--ink-muted);">+</span>
            </summary>
            <div style="padding:0 16px 14px;font-size:14px;color:var(--ink-light);line-height:1.6;">
                It depends on your use case. {name1} has {upvotes1} community upvotes while {name2} has {upvotes2}.
                Browse each tool&rsquo;s full listing to see which fits your stack.
            </div>
        </details>
        <details style="margin-bottom:12px;border:1px solid var(--border);border-radius:var(--radius-sm);padding:0;">
            <summary style="padding:14px 16px;font-weight:600;font-size:15px;color:var(--ink);cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between;">
                What is the difference between {name1} and {name2}?
                <span style="font-size:18px;color:var(--ink-muted);">+</span>
            </summary>
            <div style="padding:0 16px 14px;font-size:14px;color:var(--ink-light);line-height:1.6;">
                {name1}: {escape(str(tool1.get('tagline', '')))}.<br>
                {name2}: {escape(str(tool2.get('tagline', '')))}.
            </div>
        </details>
    </div>
    """

    # --- MCP CTA ---
    mcp_cta = f"""
    <div style="text-align:center;margin-top:48px;padding:32px;background:var(--cream-dark);border-radius:var(--radius);">
        <p style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
            Get this comparison inside your AI coding agent
        </p>
        <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
            Install the IndieStack MCP server: <code style="font-family:var(--font-mono);background:var(--border);padding:2px 8px;border-radius:4px;">pip install indiestack</code>
        </p>
        <a href="/mcp" class="btn btn-primary">Learn More &rarr;</a>
    </div>
    """

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:900px;">
        <div style="text-align:center;margin-bottom:24px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,38px);color:var(--ink);">
                {name1} <span style="color:var(--ink-muted);font-weight:normal;">vs</span> {name2}
            </h1>
            <p style="color:var(--ink-muted);font-size:17px;margin-top:8px;max-width:600px;margin-left:auto;margin-right:auto;">
                Side-by-side comparison with real community data from IndieStack.
                Not opinions -- upvotes, pricing, and tool details.
            </p>
        </div>
        {compat_banner}
        {table_html}
        <div style="display:flex;gap:32px;flex-wrap:wrap;">
            {tool_column(tool1)}
            <div style="width:1px;background:var(--border);align-self:stretch;flex-shrink:0;"></div>
            {tool_column(tool2)}
        </div>

        {faq_html}
        {mcp_cta}
    </div>
    """

    seo_title = f"{tool1['name']} vs {tool2['name']} (2026) — Agent-Verified Comparison | IndieStack"
    seo_desc = f"Compare {tool1['name']} and {tool2['name']} with real community data — pricing, upvotes, features, and AI-agent compatibility."

    return HTMLResponse(page_shell(seo_title, body,
                                    user=request.state.user,
                                    description=seo_desc,
                                    canonical=f"/compare/{slug1}-vs-{slug2}",
                                    extra_head=extra_head))

"""AI Plugins & Skills discovery page."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card

router = APIRouter()

TYPE_LABELS = {
    'mcp_server': 'MCP Servers',
    'plugin': 'Plugins',
    'extension': 'Extensions',
    'skill': 'Skills',
}


@router.get("/plugins", response_class=HTMLResponse)
async def plugins_page(request: Request, type: str = "", platform: str = ""):
    db = request.state.db

    # Build query
    conditions = ["t.status = 'approved'", "t.tool_type IS NOT NULL"]
    params = []

    if type and type in TYPE_LABELS:
        conditions.append("t.tool_type = ?")
        params.append(type)

    if platform.strip():
        conditions.append("t.platforms LIKE ?")
        params.append(f"%{platform.strip()}%")

    where = " AND ".join(conditions)
    cursor = await db.execute(
        f"""SELECT t.*, c.name as category_name, c.slug as category_slug
            FROM tools t
            JOIN categories c ON t.category_id = c.id
            WHERE {where}
            ORDER BY t.upvote_count DESC""",
        params,
    )
    tools = [dict(r) for r in await cursor.fetchall()]

    # Get common platforms for filter pills
    all_cursor = await db.execute(
        "SELECT platforms FROM tools WHERE tool_type IS NOT NULL AND platforms != '' AND status = 'approved'"
    )
    all_platforms_rows = await all_cursor.fetchall()
    platform_counts = {}
    for row in all_platforms_rows:
        for p in row['platforms'].split(','):
            p = p.strip()
            if p:
                platform_counts[p] = platform_counts.get(p, 0) + 1
    # Filter out junk platforms
    platform_counts = {p: c for p, c in platform_counts.items() if p.lower() not in ('google antigravity',)}
    # Sort by frequency, take top 8
    top_platforms = sorted(platform_counts.keys(), key=lambda x: platform_counts[x], reverse=True)[:8]

    # Type filter pills
    type_pills = f'<a href="/plugins" style="padding:8px 16px;border-radius:999px;font-size:14px;font-weight:600;text-decoration:none;border:1px solid {"var(--slate)" if not type else "var(--border)"};color:{"var(--slate)" if not type else "var(--ink-light)"};background:{"rgba(0,212,245,0.08)" if not type else "transparent"};">All</a>'
    for slug, label in TYPE_LABELS.items():
        active = type == slug
        type_pills += (
            f'<a href="/plugins?type={slug}{"&platform=" + escape(platform) if platform else ""}"'
            f' style="padding:8px 16px;border-radius:999px;font-size:14px;font-weight:600;text-decoration:none;'
            f'border:1px solid {"var(--slate)" if active else "var(--border)"};'
            f'color:{"var(--slate)" if active else "var(--ink-light)"};'
            f'background:{"rgba(0,212,245,0.08)" if active else "transparent"};">{label}</a>'
        )

    # Platform filter pills
    platform_pills = ''
    if top_platforms:
        pills_html = ''
        for p in top_platforms:
            active = platform == p
            pills_html += (
                f'<a href="/plugins?platform={escape(p)}{"&type=" + escape(type) if type else ""}"'
                f' style="padding:4px 12px;border-radius:999px;font-size:13px;font-weight:500;text-decoration:none;'
                f'border:1px solid {"var(--slate)" if active else "var(--border)"};'
                f'color:{"var(--slate)" if active else "var(--ink-muted)"};'
                f'background:{"rgba(0,212,245,0.08)" if active else "transparent"};">{escape(p)}</a>'
            )
        platform_pills = f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;">{pills_html}</div>'

    # Tool cards
    if tools:
        cards = ''.join(tool_card(t) for t in tools)
        grid = f'<div class="card-grid">{cards}</div>'
    else:
        grid = (
            '<div style="text-align:center;padding:64px 24px;">'
            '<div style="margin-bottom:16px;"><svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z"/><circle cx="12" cy="14" r="2"/></svg></div>'
            '<h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:8px;">No plugins yet</h2>'
            '<p style="color:var(--ink-muted);margin-bottom:24px;">Be the first to list an agent plugin or MCP server.</p>'
            '<a href="/submit" class="btn btn-primary">Submit Your Plugin</a>'
            '</div>'
        )

    body = f"""
    <div class="container" style="padding:48px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:var(--heading-xl);margin-bottom:8px;">AI Plugins &amp; Skills</h1>
            <p style="font-size:18px;color:var(--ink-muted);max-width:560px;margin:0 auto;">
                MCP servers, extensions, and skills for your AI coding assistant. Install in one command.
            </p>
            <p style="font-size:13px;color:var(--ink-muted);max-width:560px;margin:8px auto 0;">
                Community-curated catalog. Makers can <a href="/submit" style="color:var(--accent);">claim their listing</a> to update details.
            </p>
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-bottom:24px;">
            {type_pills}
        </div>
        <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-bottom:40px;">
            {platform_pills}
        </div>
        {grid}
    </div>
    """

    return page_shell(
        title="AI Plugins & Skills for Developers | IndieStack",
        body=body,
        description="Discover MCP servers, Claude Code plugins, Cursor extensions, and AI skills. Install in one command.",
        user=getattr(request.state, 'user', None),
    )

"""Maker profile + directory pages — public portfolio for tool creators."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card, verified_badge_html, maker_card, indie_badge_html, update_card, pagination_html
from indiestack.db import (get_maker_with_tools, get_maker_stats, get_all_makers_paginated,
                           search_makers, get_updates_by_maker)

router = APIRouter()


@router.get("/makers", response_class=HTMLResponse)
async def makers_directory(request: Request):
    db = request.state.db
    q = request.query_params.get('q', '').strip()
    sort = request.query_params.get('sort', 'most_tools')
    page = int(request.query_params.get('page', '1'))

    if q:
        makers = await search_makers(db, q)
        total = len(makers)
        total_pages = 1
    else:
        makers, total = await get_all_makers_paginated(db, page=page, per_page=12, sort=sort)
        total_pages = max(1, (total + 11) // 12)

    # Sort pills
    sort_pills = ''
    for val, label in [('most_tools', 'Most Tools'), ('most_upvoted', 'Most Upvoted'), ('newest', 'Newest')]:
        active = 'background:var(--terracotta);color:white;border-color:var(--terracotta);' if val == sort else ''
        sort_pills += f'<a href="/makers?sort={val}" style="padding:6px 14px;border-radius:999px;font-size:13px;font-weight:600;border:1px solid var(--border);background:white;color:var(--ink-light);text-decoration:none;{active}">{escape(label)}</a>'

    cards = '\n'.join(maker_card(m) for m in makers)

    body = f"""
    <div class="container" style="padding:48px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);">Maker Directory</h1>
            <p style="color:var(--ink-muted);margin-top:8px;">Discover the indie makers behind the tools. Claim your profile today.</p>
        </div>
        <form action="/makers" method="GET" style="max-width:480px;margin:0 auto 32px;">
            <div class="search-box">
                <span class="search-icon">&#128269;</span>
                <input type="text" name="q" value="{escape(q)}" placeholder="Search makers by name..." style="width:100%;padding:12px 20px 12px 48px;font-size:15px;font-family:var(--font-body);border:2px solid var(--border);border-radius:999px;background:white;">
            </div>
        </form>
        <div style="display:flex;gap:8px;justify-content:center;margin-bottom:32px;">
            {sort_pills}
        </div>
        <div class="card-grid">
            {cards if cards else '<p style="text-align:center;color:var(--ink-muted);grid-column:1/-1;">No makers found.</p>'}
        </div>
        {pagination_html(page, total_pages, f'/makers?sort={escape(sort)}')}
    </div>
    """
    return HTMLResponse(page_shell("Maker Directory", body, description="Discover indie makers building SaaS tools.", user=request.state.user))


@router.get("/maker/{slug}", response_class=HTMLResponse)
async def maker_profile(request: Request, slug: str):
    db = request.state.db
    maker, tools = await get_maker_with_tools(db, slug)

    if not maker:
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Maker Not Found</h1>
            <p class="text-muted mt-4">We couldn't find this maker profile.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body, user=request.state.user), status_code=404)

    name = escape(str(maker['name']))
    bio = escape(str(maker.get('bio', '')))
    url = escape(str(maker.get('url', '')))
    stats = await get_maker_stats(db, maker['id'])
    tool_count = stats['tool_count']
    total_upvotes = stats['total_upvotes']
    verified_count = stats['verified_count']

    # Indie badge
    indie_status = str(maker.get('indie_status', ''))
    badge_html = indie_badge_html(indie_status) if indie_status else ''

    # URL display
    url_html = ''
    if url:
        url_html = f'<a href="{url}" target="_blank" rel="noopener" style="color:var(--terracotta);font-size:14px;">{url}</a>'

    # Bio
    bio_html = ''
    if bio:
        bio_html = f'<p style="color:var(--ink-light);font-size:15px;line-height:1.6;margin-top:12px;max-width:600px;">{bio}</p>'

    # Stats row
    stats_html = f"""
    <div style="display:flex;gap:32px;margin-top:20px;justify-content:center;">
        <div style="text-align:center;">
            <div style="font-family:var(--font-display);font-size:24px;color:var(--ink);">{tool_count}</div>
            <div style="font-size:13px;color:var(--ink-muted);">tool{"s" if tool_count != 1 else ""}</div>
        </div>
        <div style="text-align:center;">
            <div style="font-family:var(--font-display);font-size:24px;color:var(--slate-dark);">{total_upvotes}</div>
            <div style="font-size:13px;color:var(--ink-muted);">upvotes</div>
        </div>
        <div style="text-align:center;">
            <div style="font-family:var(--font-display);font-size:24px;color:var(--gold);">{verified_count}</div>
            <div style="font-size:13px;color:var(--ink-muted);">verified</div>
        </div>
    </div>
    """

    # Tools grid
    if tools:
        cards = '\n'.join(tool_card(t) for t in tools)
        tools_html = f"""
        <div style="margin-top:48px;">
            <h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:20px;color:var(--ink);">
                Tools by {name}
            </h2>
            <div class="card-grid">{cards}</div>
        </div>
        """
    else:
        tools_html = """
        <div style="text-align:center;padding:40px 0;">
            <p style="color:var(--ink-muted);">No published tools yet.</p>
        </div>
        """

    # Recent updates
    updates = await get_updates_by_maker(db, maker['id'], limit=5)
    updates_html = ''
    if updates:
        updates_cards = '\n'.join(update_card(u | {'maker_name': maker['name'], 'maker_slug': maker['slug']}) for u in updates)
        updates_html = f"""
        <div style="margin-top:48px;">
            <h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:20px;color:var(--ink);">Recent Updates</h2>
            {updates_cards}
        </div>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:900px;">
        <div style="text-align:center;margin-bottom:16px;">
            <div style="display:inline-flex;align-items:center;justify-content:center;width:80px;height:80px;
                        border-radius:50%;background:var(--terracotta);color:white;font-size:32px;
                        font-family:var(--font-display);margin-bottom:12px;">
                {name[0].upper() if name else '?'}
            </div>
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">{name}</h1>
            {badge_html}
            {url_html}
            {bio_html}
            {stats_html}
        </div>
        {tools_html}
        {updates_html}
    </div>
    """
    return HTMLResponse(page_shell(f"{maker['name']} — Maker Profile", body,
                                    description=f"Tools built by {maker['name']} on IndieStack.", user=request.state.user,
                                    canonical=f"/maker/{maker['slug']}"))

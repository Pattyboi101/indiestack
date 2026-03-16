"""Maker profile + directory pages — public portfolio for tool creators."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card, verified_badge_html, maker_card, indie_badge_html, update_card, pagination_html
from indiestack.db import (get_maker_with_tools, get_maker_stats, get_all_makers_paginated,
                           search_makers, get_updates_by_maker, get_maker_reputation_leaderboard)

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
        sort_pills += f'<a href="/makers?sort={val}" style="padding:8px 16px;border-radius:999px;font-size:13px;font-weight:600;border:1px solid var(--border);background:white;color:var(--ink-light);text-decoration:none;{active}">{escape(label)}</a>'

    cards = '\n'.join(maker_card(m) for m in makers)

    body = f"""
    <div class="container" style="padding:48px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);">Maker Directory</h1>
            <p style="color:var(--ink-muted);margin-top:8px;">Discover the indie makers behind the tools. Claim your profile today.</p>
        </div>
        <form action="/makers" method="GET" style="max-width:480px;margin:0 auto 32px;">
            <div class="search-box">
                <span class="search-icon"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg></span>
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
    return HTMLResponse(page_shell("Maker Directory", body, description="Discover indie makers and the creations they've built. Browse profiles, see their work, and connect with the people behind the software.", user=request.state.user, canonical="/makers"))


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


# ── Leaderboard ─────────────────────────────────────────────────────────

@router.get("/leaderboard", response_class=HTMLResponse)
async def leaderboard(request: Request):
    db = request.state.db
    makers = await get_maker_reputation_leaderboard(db)

    rows = ''
    for i, m in enumerate(makers):
        rank = i + 1
        if rank == 1:
            medal = '<span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:#E2B764;color:#fff;font-size:11px;font-weight:700;">1</span>'
        elif rank == 2:
            medal = '<span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:#94A3B8;color:#fff;font-size:11px;font-weight:700;">2</span>'
        elif rank == 3:
            medal = '<span style="display:inline-flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:50%;background:#CD7F32;color:#fff;font-size:11px;font-weight:700;">3</span>'
        else:
            medal = f'<span style="font-size:16px;font-weight:700;color:var(--ink-muted);">{rank}</span>'

        name = escape(str(m['name']))
        slug = escape(str(m['slug']))
        tools = m['tool_count']
        upvotes = m['total_upvotes']
        reviews = m['total_reviews']
        clicks = m['total_clicks']
        score = m['reputation_score']
        indie = m.get('indie_status', '')

        indie_pill = ''
        if indie == 'solo':
            indie_pill = '<span style="font-size:11px;font-weight:700;color:var(--info-text);background:var(--info-bg);padding:2px 8px;border-radius:999px;">Solo Maker</span>'
        elif indie == 'small_team':
            indie_pill = '<span style="font-size:11px;font-weight:700;color:var(--info-text);background:var(--info-bg);padding:2px 8px;border-radius:999px;">Small Team</span>'

        active_pill = ''
        if m['has_changelog']:
            active_pill = '<span style="font-size:11px;font-weight:700;color:var(--warning-text);background:var(--warning-bg);padding:2px 8px;border-radius:999px;"><svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:2px;"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg> Active</span>'

        row_bg = 'background:linear-gradient(135deg,rgba(0,212,245,0.05),rgba(26,45,74,0.03));' if rank <= 3 else ''

        rows += f'''
        <tr style="border-bottom:1px solid var(--border);{row_bg}">
            <td style="padding:16px 12px;text-align:center;width:50px;">{medal}</td>
            <td style="padding:16px 12px;">
                <a href="/maker/{slug}" style="font-weight:700;color:var(--ink);font-size:15px;">{name}</a>
                <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:4px;">
                    {indie_pill}{active_pill}
                </div>
            </td>
            <td style="padding:16px 12px;text-align:center;font-family:var(--font-mono);font-size:13px;">{tools}</td>
            <td style="padding:16px 12px;text-align:center;font-family:var(--font-mono);font-size:13px;">{upvotes}</td>
            <td style="padding:16px 12px;text-align:center;font-family:var(--font-mono);font-size:13px;">{reviews}</td>
            <td style="padding:16px 12px;text-align:center;font-family:var(--font-mono);font-size:13px;">{clicks}</td>
            <td style="padding:16px 12px;text-align:center;">
                <span style="font-family:var(--font-display);font-size:18px;font-weight:800;color:var(--terracotta);">{score}</span>
            </td>
        </tr>
        '''

    score_explainer = '''
    <div class="card" style="padding:20px;margin-top:32px;">
        <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:12px;">How Reputation Works</h3>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;font-size:13px;color:var(--ink-muted);">
            <div><strong style="color:var(--ink);">+1</strong> per upvote</div>
            <div><strong style="color:var(--ink);">+5</strong> per review</div>
            <div><strong style="color:var(--ink);">+2</strong> per click (30d)</div>
            <div><strong style="color:var(--ink);">+5</strong> active changelog</div>
        </div>
        <p style="font-size:12px;color:var(--ink-muted);margin-top:12px;">
            Reputation resets clicks monthly. Ship updates, earn reviews, and stay active to climb.
        </p>
    </div>
    '''

    from datetime import date
    launch = date(2026, 3, 2)
    today = date.today()
    days_left = (launch - today).days
    if days_left > 0:
        launch_line = f'AI agents are already searching &mdash; <strong>{days_left} day{"s" if days_left != 1 else ""}</strong> until Product Hunt relaunch.'
    elif days_left == 0:
        launch_line = 'We&rsquo;re <strong>live on Product Hunt today</strong>! Claimed makers get featured.'
    else:
        launch_line = 'AI agents search IndieStack before building from scratch. <strong>Claimed makers rank higher.</strong>'

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:960px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);">Maker Leaderboard</h1>
            <p style="color:var(--ink-muted);margin-top:8px;font-size:16px;">
                The most active and trusted indie makers on IndieStack.
                <br><span style="font-size:14px;">{launch_line}</span>
            </p>
        </div>
        <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:14px;">
                <thead>
                    <tr style="border-bottom:2px solid var(--border);">
                        <th style="padding:12px 12px;text-align:center;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Rank</th>
                        <th style="padding:12px 12px;text-align:left;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Maker</th>
                        <th style="padding:12px 12px;text-align:center;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Tools</th>
                        <th style="padding:12px 12px;text-align:center;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Upvotes</th>
                        <th style="padding:12px 12px;text-align:center;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Reviews</th>
                        <th style="padding:12px 12px;text-align:center;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Clicks</th>
                        <th style="padding:12px 12px;text-align:center;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Score</th>
                    </tr>
                </thead>
                <tbody>
                    {rows if rows else '<tr><td colspan="7" style="padding:40px;text-align:center;color:var(--ink-muted);">No makers yet. <a href="/submit" style="color:var(--accent);">Be the first!</a></td></tr>'}
                </tbody>
            </table>
        </div>
        {score_explainer}
        <div style="text-align:center;margin-top:32px;">
            <a href="/submit" class="btn btn-slate" style="padding:16px 32px;font-size:16px;">Submit Your Tool &rarr;</a>
        </div>
    </div>
    """
    return HTMLResponse(page_shell("Maker Leaderboard", body, user=request.state.user,
                                    description="The most active indie makers on IndieStack, ranked by reputation.",
                                    canonical="/leaderboard"))

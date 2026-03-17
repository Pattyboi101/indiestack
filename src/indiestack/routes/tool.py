"""Tool detail page."""

import json
from datetime import date
from html import escape
from urllib.parse import quote, urlparse

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from indiestack.config import BASE_URL

from indiestack.routes.components import (
    page_shell,
    tool_card,
    boosted_badge_html,
    ejectable_badge_html,
    maker_pulse_html,
    pixel_icon_svg,
    star_rating_html,
    review_card,
    review_form_html,
    update_card,
    maker_discount_badge_html,
    email_sticky_bar,
    analytics_wall_blurred,
    analytics_wall_revealed,
)
from indiestack.db import (
    get_tool_by_slug,
    get_related_tools,
    get_similar_tools,
    slugify,
    get_reviews_for_tool,
    get_tool_rating,
    get_user_review_for_tool,
    create_review,
    record_tool_view,
    is_wishlisted,
    get_tool_changelogs,
    CATEGORY_TOKEN_COSTS,
    get_tool_last_activity,
    get_outbound_click_count,
    toggle_reaction,
    get_reaction_counts,
    get_verified_pairs,
    record_tool_pair,
    get_tool_success_rate,
    get_tool_recommendation_count,
    get_tool_total_citations,
    check_pro,
    get_tool_analytics_wall_data,
)

router = APIRouter()

MARKETPLACE_ENABLED = False


def format_price(pence: int) -> str:
    """Format pence as display string."""
    pounds = pence / 100
    if pounds == int(pounds):
        return f"\u00a3{int(pounds)}"
    return f"\u00a3{pounds:.2f}"


@router.get("/tool/{slug}", response_class=HTMLResponse)
async def tool_detail(request: Request, slug: str):
    db = request.state.db
    user = request.state.user
    tool = await get_tool_by_slug(db, slug)

    if not tool or tool['status'] != 'approved':
        body = """
        <div class="container" style="text-align:center;padding:64px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Not Found</h1>
            <p class="text-muted mt-4">This creation doesn't exist or hasn't been approved yet.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body, user=user), status_code=404)

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
    is_ejectable = bool(tool.get('is_ejectable', 0))
    source_type = tool.get('source_type', 'saas')
    is_totw = bool(tool.get('tool_of_the_week', 0))
    totw_badge = '<span style="display:inline-flex;align-items:center;gap:6px;background:linear-gradient(135deg,#E2B764,#D4A84B);color:#1A2D4A;padding:6px 14px;border-radius:999px;font-size:13px;font-weight:700;white-space:nowrap;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:2px;"><path d="M12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26z"/></svg> Tool of the Week</span>' if is_totw else ''
    tool_type = tool.get('tool_type') or None
    platforms_raw = tool.get('platforms', '')
    install_command = tool.get('install_command', '')
    tool_id = tool['id']
    slug_str = tool['slug']
    success_rate = await get_tool_success_rate(db, slug_str)
    recommendation_count = await get_tool_recommendation_count(db, slug_str)
    click_count = await get_outbound_click_count(db, tool_id, days=30)

    # Analytics wall — determine viewer's relationship to this tool
    is_tool_owner = (
        user and user.get('maker_id')
        and tool.get('maker_id')
        and user['maker_id'] == tool['maker_id']
    )
    is_claimed = bool(tool.get('claimed_at'))
    show_analytics = is_claimed and is_tool_owner

    reactions = await get_reaction_counts(
        db, tool_id,
        user_id=user['id'] if user else None,
        session_id=request.cookies.get('session_id'),
    )
    price_pence = tool.get('price_pence')

    # Indie Ring: check if current user is a maker viewing another maker's paid tool
    is_indie_ring = False
    discounted_price = 0
    if user and price_pence and price_pence > 0:
        buyer_maker_id = user.get('maker_id')
        tool_maker_id = tool.get('maker_id')
        if buyer_maker_id and tool_maker_id and buyer_maker_id != tool_maker_id:
            is_indie_ring = True
            discounted_price = price_pence // 2

    # Record view
    ip = request.headers.get("fly-client-ip") or request.headers.get("x-forwarded-for", "").split(",")[0].strip() or request.client.host
    await record_tool_view(db, tool_id, ip)

    # Fetch reviews and rating
    reviews = await get_reviews_for_tool(db, tool_id)
    rating_info = await get_tool_rating(db, tool_id)
    tool['review_count'] = int(rating_info['review_count'])
    user_review = await get_user_review_for_tool(db, tool_id, user['id']) if user else None
    wishlisted = await is_wishlisted(db, user['id'], tool_id) if user else False

    # Maker pulse
    last_active = await get_tool_last_activity(db, tool_id)
    pulse_html = maker_pulse_html(last_active)

    # Analytics wall (claim-to-reveal)
    analytics_wall_html = ''
    is_tool_owner = (
        user and tool.get('claimed_at') and tool.get('maker_id')
        and user.get('maker_id') == tool.get('maker_id')
    )
    wall_stats = await get_tool_analytics_wall_data(db, slug_str, tool_id, detailed=is_tool_owner)
    if wall_stats['total_agent_queries'] > 0 or wall_stats['total_citations'] > 0:
        if is_tool_owner:
            analytics_wall_html = analytics_wall_revealed(wall_stats, tool['name'])
        elif not tool.get('claimed_at'):
            analytics_wall_html = analytics_wall_blurred(wall_stats, tool['name'], slug_str, user_logged_in=bool(user), tool_id=tool_id)

    # Build rating display
    avg_rating = float(rating_info['avg_rating'])
    review_count = int(rating_info['review_count'])
    rating_display_html = ''
    if review_count > 0:
        rating_display_html = f'<span style="margin-left:12px;">{star_rating_html(avg_rating, review_count)}</span>'

    # Build reviews section — only show if there are reviews or user is logged in
    if reviews or user:
        reviews_html = '<div class="section-divider">'
        reviews_html += '<h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:24px;">Reviews</h2>'
        if reviews:
            for r in reviews:
                reviews_html += review_card(r)
        else:
            reviews_html += '''<div style="text-align:center;padding:32px 24px;background:var(--cream-dark);border-radius:var(--radius);border:1px dashed var(--border);">
    <p style="font-size:28px;margin-bottom:8px;">&#9998;</p>
    <p style="font-weight:600;color:var(--ink);margin-bottom:4px;">No reviews yet</p>
    <p style="color:var(--ink-muted);font-size:14px;">Used this? Be the first to share your experience.</p>
</div>'''

        if user:
            reviews_html += review_form_html(slug, existing_review=user_review)
        else:
            reviews_html += '<p style="margin-top:24px;color:var(--ink-muted);font-size:14px;"><a href="/login">Log in</a> to leave a review.</p>'
        reviews_html += '</div>'
    else:
        reviews_html = ''

    # Tags
    tag_html = ''
    if tags.strip():
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        tag_html = '<div style="display:flex;gap:8px;flex-wrap:wrap;">'
        for t in tag_list:
            tag_html += f'<span class="tag">{escape(t)}</span>'
        tag_html += '</div>'

    # Token savings hint
    token_hint_html = ''
    cat_slug_val = str(tool.get('category_slug', ''))
    token_cost = CATEGORY_TOKEN_COSTS.get(cat_slug_val, 50_000)
    token_k = token_cost // 1000
    # Citation count — use real agent_citations data (all-time)
    citation_count = await get_tool_total_citations(db, tool_id)
    mcp_views = int(tool.get('mcp_view_count', 0))
    # Use the higher of the two counts (citations are more accurate but mcp_views may be higher for older tools)
    ai_rec_count = max(citation_count, mcp_views)
    # Analytics badges — gated by ownership
    mcp_badge = ''
    outcome_badge = ''
    analytics_teaser = ''
    pro_analytics_link = ''

    if show_analytics:
        # Owner viewing their claimed tool — show full analytics
        if ai_rec_count > 0:
            mcp_badge = f'''
            <div style="margin-top:8px;padding:10px 16px;background:linear-gradient(135deg,var(--info-bg),var(--info-bg));border-radius:var(--radius-sm);
                        display:inline-flex;align-items:center;gap:8px;font-size:14px;color:var(--info-text);border:1px solid var(--info-border);font-weight:600;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                Recommended by AI agents {ai_rec_count} time{'s' if ai_rec_count != 1 else ''}
            </div>'''
        if success_rate['total'] > 0:
            rate_color = 'var(--success-text)' if success_rate['rate'] >= 70 else 'var(--warning-text)' if success_rate['rate'] >= 40 else 'var(--error-text)'
            outcome_badge = f'''
            <div style="margin-top:8px;padding:8px 16px;background:var(--card-bg);border-radius:var(--radius-sm);
                        display:inline-flex;align-items:center;gap:8px;font-size:13px;color:var(--ink-light);border:1px solid var(--border);">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
                <span style="font-weight:600;color:{rate_color};">{success_rate['rate']}%</span> agent success rate
                <span style="color:var(--ink-muted);font-size:12px;">({success_rate['total']} report{'s' if success_rate['total'] != 1 else ''})</span>
            </div>'''
        elif recommendation_count > 0:
            outcome_badge = f'''
            <div style="margin-top:8px;padding:8px 16px;background:var(--card-bg);border-radius:var(--radius-sm);
                        display:inline-flex;align-items:center;gap:8px;font-size:13px;color:var(--ink-muted);border:1px solid var(--border);">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>
                Recommended {recommendation_count} time{'s' if recommendation_count != 1 else ''} &mdash; no outcome reports yet
            </div>'''
        # Pro owners get a link to full analytics dashboard
        if user and await check_pro(db, user['id']):
            pro_analytics_link = '''
            <div style="margin-top:8px;">
                <a href="/dashboard#ai-distribution" style="font-size:13px;color:var(--accent);text-decoration:none;font-weight:600;">
                    View full analytics &rarr;
                </a>
            </div>'''
    elif is_claimed and ai_rec_count > 0:
        # Claimed but viewer is not the owner — generic teaser, no numbers
        analytics_teaser = '''
        <div style="margin-top:8px;padding:10px 16px;background:var(--info-bg);border-radius:var(--radius-sm);
                    display:inline-flex;align-items:center;gap:8px;font-size:14px;color:var(--info-text);border:1px solid var(--info-border);font-weight:600;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>
            AI agents recommend this tool
        </div>'''
    elif not is_claimed and ai_rec_count > 0:
        # Unclaimed — teaser + claim nudge
        analytics_teaser = '''
        <div style="margin-top:8px;padding:10px 16px;background:var(--info-bg);border-radius:var(--radius-sm);
                    display:flex;flex-direction:column;gap:4px;font-size:14px;color:var(--info-text);border:1px solid var(--info-border);">
            <div style="display:flex;align-items:center;gap:8px;font-weight:600;">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>
                AI agents are recommending this tool
            </div>
            <span style="font-size:12px;font-weight:400;color:var(--ink-muted);">Claim this listing to see how many times and your success rate.</span>
        </div>'''

    token_hint_html = f'''
        <div style="margin-top:16px;padding:8px 16px;background:var(--cream-dark);border-radius:var(--radius-sm);
                    display:inline-flex;align-items:center;gap:8px;font-size:13px;color:var(--ink-light);">
            <span style="color:var(--slate);display:inline-block;"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg></span>
            Using this saves ~{token_k}k tokens vs building from scratch
        </div>
        {mcp_badge}
        {outcome_badge}
        {pro_analytics_link}
        {analytics_teaser}
    '''

    # GitHub freshness badge
    freshness_badge = ''
    gh_freshness = tool.get('github_freshness')
    if gh_freshness == 'active':
        freshness_badge = '''
        <span style="display:inline-flex;align-items:center;gap:4px;padding:4px 8px;border-radius:999px;
                     font-size:12px;font-weight:600;background:var(--success-bg);color:var(--success-text);border:1px solid var(--success-border);">
            &#9989; Actively maintained
        </span>'''
    elif gh_freshness == 'stale':
        freshness_badge = '''
        <span style="display:inline-flex;align-items:center;gap:4px;padding:4px 8px;border-radius:999px;
                     font-size:12px;font-weight:600;background:var(--warning-bg);color:var(--warning-text);border:1px solid var(--warning-bg);">
            &#9888;&#65039; Last updated 90+ days ago
        </span>'''
    elif gh_freshness == 'inactive':
        freshness_badge = '''
        <span style="display:inline-flex;align-items:center;gap:4px;padding:4px 8px;border-radius:999px;
                     font-size:12px;font-weight:600;background:var(--error-bg);color:var(--error-text);border:1px solid var(--error-border);">
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--error-text,#EF4444);vertical-align:middle;margin-right:4px;"></span> Possibly unmaintained (180+ days)
        </span>'''

    github_badge = ''
    if tool.get('github_url'):
        gh_stars = int(tool.get('github_stars', 0))
        gh_lang = tool.get('github_language', '')
        gh_meta_pills = ''
        if gh_stars:
            gh_meta_pills += f'<span style="display:inline-flex;align-items:center;gap:4px;padding:4px 10px;background:var(--card-bg);border:1px solid var(--border);border-radius:999px;font-size:12px;color:var(--ink-muted);font-weight:500;">&#9733; {gh_stars:,}</span>'
        if gh_lang:
            gh_meta_pills += f'<span style="display:inline-flex;align-items:center;gap:4px;padding:4px 10px;background:var(--card-bg);border:1px solid var(--border);border-radius:999px;font-size:12px;color:var(--ink-muted);font-weight:500;">{escape(gh_lang)}</span>'
        github_badge = f'''
        <div style="display:flex;flex-wrap:wrap;align-items:center;gap:8px;margin-top:8px;">
            <a href="{escape(str(tool['github_url']))}" target="_blank" rel="noopener"
               style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;
                      background:var(--card-bg);color:var(--ink);border:1px solid var(--border);border-radius:999px;font-size:13px;
                      font-weight:600;text-decoration:none;">
                <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
                View on GitHub
            </a>
            {gh_meta_pills}
        </div>'''

        # GitHub maintenance signals
        _gh_signals = []
        _last_commit = tool.get('github_last_commit', '')
        _is_archived = tool.get('github_is_archived', 0)
        _open_issues = int(tool.get('github_open_issues', 0) or 0)
        if _last_commit:
            from datetime import datetime as _dt
            try:
                _commit_dt = _dt.fromisoformat(_last_commit.replace('Z', '+00:00'))
                _days_ago = (_dt.now(_commit_dt.tzinfo) - _commit_dt).days
                if _days_ago < 30:
                    _gh_signals.append(f'<span style="color:var(--success, #22C55E);">Active &mdash; last commit {_days_ago}d ago</span>')
                elif _days_ago < 180:
                    _gh_signals.append(f'<span style="color:var(--gold, #E2B764);">Last commit {_days_ago}d ago</span>')
                else:
                    _gh_signals.append(f'<span style="color:var(--ink-muted, #888);">Last commit {_days_ago}d ago</span>')
            except Exception:
                pass
        if _is_archived:
            _gh_signals.append('<span style="color:var(--danger, #EF4444);"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:2px;"><rect x="2" y="4" width="20" height="5" rx="1"/><path d="M4 9v9a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9"/><path d="M10 13h4"/></svg> Archived</span>')
        if _open_issues:
            _gh_signals.append(f'<span style="color:var(--ink-muted, #888);">{_open_issues} open issues</span>')
        if _gh_signals:
            github_badge += f'''
        <div style="display:flex;flex-wrap:wrap;gap:8px 16px;margin-top:6px;font-size:13px;">
            {"".join(_gh_signals)}
        </div>'''

    # Claim CTA — show for unclaimed tools (maker_id may exist from auto-import but claimed_at is only set on real claims)
    claim_html = ''
    if not tool.get('claimed_at'):
        if user:
            claim_action = f'''
                <form method="POST" action="/api/claim" style="margin:0;">
                    <input type="hidden" name="tool_id" value="{tool['id']}">
                    <button type="submit" class="btn btn-primary" style="padding:12px 24px;font-size:14px;">
                        Claim This Listing
                    </button>
                </form>'''
        else:
            claim_action = f'''
                <a href="/signup?next=/tool/{slug}" class="btn btn-primary" style="padding:12px 24px;font-size:14px;text-decoration:none;">
                    Claim This Listing
                </a>'''
        claim_html = f'''
        <div id="claim" style="margin:16px 0;padding:24px;background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius-sm);">
            <div style="display:flex;align-items:flex-start;gap:12px;flex-wrap:wrap;">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                <div style="flex:1;min-width:200px;">
                    <p style="font-weight:700;font-size:15px;color:var(--ink);margin-bottom:2px;">Did you build this?</p>
                    <p style="font-size:13px;color:var(--ink-light);margin-bottom:12px;">Claim your listing to see exactly how many AI agents recommend this tool, your success rate, and more. Free, no commission, no fees.</p>
                    {claim_action}
                </div>
            </div>
        </div>
        '''

    # Claim status messages
    claim_message = ''
    if request.query_params.get('claim_email_sent'):
        claim_message = '''
        <div style="margin:16px 0;padding:16px 24px;background:var(--success-bg);border:1px solid var(--success-border);border-radius:var(--radius-sm);color:var(--success-text);font-size:14px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg> Verification email sent! Check your inbox and click the link to claim this listing.
        </div>'''
    elif request.query_params.get('claimed'):
        claim_message = '''
        <div style="margin:16px 0;padding:16px 24px;background:var(--success-bg);border:1px solid var(--success-border);border-radius:var(--radius-sm);color:var(--success-text);font-size:14px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg> You've claimed this listing! Visit your <a href="/dashboard" style="color:var(--success-text);font-weight:600;">dashboard</a> to see your analytics.
        </div>'''
    elif request.query_params.get('claim_requested'):
        claim_message = '''
        <div style="margin:16px 0;padding:16px 24px;background:var(--info-bg);border:1px solid var(--info-border);border-radius:var(--radius-sm);color:var(--info-text);font-size:14px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg> Claim request submitted! We'll review it within 24 hours.
        </div>'''

    # Boost section (placeholder for future referral boost feature)
    boost_html = ''

    # Community listing notice — shown on tools listed by Community Curated maker
    community_notice = ''
    maker_slug_val = tool.get('maker_slug', '') or ''
    if maker_slug_val == 'community' or (str(tool.get('maker_name', '')) == 'Community Curated'):
        community_notice = f'''
        <div style="margin:16px 0;padding:16px 24px;background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius-sm);">
            <div style="display:flex;align-items:flex-start;gap:8px;">
                <span style="font-size:18px;flex-shrink:0;">&#9432;</span>
                <div style="font-size:13px;color:var(--ink-light);line-height:1.6;">
                    <strong style="color:var(--ink);">Community listing</strong> &mdash;
                    Listed for free by the IndieStack community &mdash; no fees, no commission.
                    If you built {escape(str(tool['name']))}, you can
                    <a href="/signup?next=/tool/{slug}" style="color:var(--accent);font-weight:600;">claim this listing</a>
                    to manage it, or
                    <a href="mailto:pajebay1@gmail.com?subject=Removal%20request%3A%20{escape(str(tool['name']))}&body=Hi%2C%0A%0AI%27m%20the%20creator%20of%20{escape(str(tool['name']))}%20and%20I%27d%20like%20this%20listing%20removed%20from%20IndieStack.%0A%0AMy%20role%3A%20%0AProof%20of%20ownership%3A%20"
                       style="color:var(--ink-light);text-decoration:underline;">request removal</a>.
                </div>
            </div>
        </div>'''

    # Maker info (link to profile)
    maker_html = ''
    unclaimed_badge = ''
    if not tool.get('claimed_at'):
        unclaimed_badge = '''<span style="display:inline-flex;align-items:center;gap:4px;font-size:12px;color:var(--ink-muted);background:var(--cream-dark);padding:2px 8px;border-radius:999px;border:1px solid var(--border);">
    Listed for free &middot; No commission &middot; <a href="#claim" style="color:var(--accent);text-decoration:none;">Claim this listing</a>
</span>'''
    if maker_name:
        maker_slug = slugify(maker_name)
        maker_html = f'<p class="text-muted text-sm mt-4">Built by <a href="/maker/{escape(maker_slug)}">{maker_name}</a> {unclaimed_badge}</p>'
    elif unclaimed_badge:
        maker_html = f'<p class="text-muted text-sm mt-4">{unclaimed_badge}</p>'

    # Price tag
    price_tag_html = ''
    if price_pence and price_pence > 0:
        if is_indie_ring:
            price_tag_html = f'''
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:12px;">
                <span style="font-family:var(--font-display);font-size:28px;color:var(--ink);">
                    {format_price(discounted_price)}
                </span>
                <span style="text-decoration:line-through;color:var(--ink-muted);font-size:16px;">
                    {format_price(price_pence)}
                </span>
                {maker_discount_badge_html()}
            </div>
            '''
        else:
            price_display = format_price(price_pence)
            price_tag_html = f"""
            <span style="display:inline-flex;align-items:center;gap:8px;font-family:var(--font-display);
                         font-size:24px;color:var(--terracotta);margin-top:12px;">
                {price_display}
            </span>
            """

    # Wishlist button
    wishlist_btn_html = ''
    if user:
        wl_icon = '&#9733;' if wishlisted else '&#9734;'
        wl_color = 'var(--gold)' if wishlisted else 'var(--ink-muted)'
        wl_text = 'Bookmarked' if wishlisted else 'Bookmark'
        wishlist_btn_html = f'''<button class="btn btn-secondary" onclick="toggleWishlist({tool_id})" id="wishlist-{tool_id}"
            style="font-size:14px;padding:8px 20px;">
            <span style="color:{wl_color};" id="wl-icon-{tool_id}">{wl_icon}</span> {wl_text}
        </button>'''
    else:
        wishlist_btn_html = f'<a href="/auth/github?next=/tool/{slug}" class="btn btn-secondary" style="font-size:14px;padding:8px 20px;">&#9734; Bookmark</a>'

    # CTA button — "Buy Now" only if tool has Stripe connected, otherwise link to their site
    has_stripe = bool(tool.get('stripe_account_id'))
    if MARKETPLACE_ENABLED and price_pence and price_pence > 0 and has_stripe:
        cta_price = format_price(discounted_price) if is_indie_ring else format_price(price_pence)
        cta_html = f"""
        <form method="post" action="/api/checkout" style="display:inline;">
            <input type="hidden" name="tool_id" value="{tool_id}">
            {'<input type="hidden" name="indie_ring" value="1">' if is_indie_ring else ''}
            <button type="submit" class="btn btn-slate" style="font-size:16px;padding:14px 32px;">
                Buy Now {cta_price} &rarr;
            </button>
        </form>
        """
    elif MARKETPLACE_ENABLED and price_pence and price_pence > 0:
        cta_price = format_price(price_pence)
        # Check if a real user has claimed this tool (not just backfilled claimed_at)
        _maker_user_row = await db.execute(
            "SELECT 1 FROM users WHERE maker_id = ?", (tool.get('maker_id'),)
        ) if tool.get('maker_id') else None
        is_claimed = bool(_maker_user_row and await _maker_user_row.fetchone())
        if is_claimed:
            # Claimed maker set a price but hasn't connected Stripe yet — show "Notify me"
            _launch = date(2026, 3, 2)
            _pill_text = "Available March 2" if date.today() < _launch else "Available soon"
            cta_pill = f'<div style="display:inline-block;background:var(--terracotta);color:var(--slate);font-size:12px;font-weight:700;padding:4px 12px;border-radius:999px;margin-bottom:8px;">{_pill_text} &middot; {cta_price}/mo</div>'
            if user:
                notify_icon = '&#9989;' if wishlisted else '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>'
                notify_text = 'Notified when available!' if wishlisted else f'Notify me when available ({cta_price})'
                cta_html = f"""
                {cta_pill}
                <button onclick="notifyWhenAvailable({tool_id})" id="notify-btn-{tool_id}"
                        class="btn btn-primary" style="font-size:16px;padding:14px 32px;">
                    <span id="notify-icon-{tool_id}">{notify_icon}</span>
                    <span id="notify-text-{tool_id}">{notify_text}</span>
                </button>
                <script>
                async function notifyWhenAvailable(toolId) {{
                    try {{
                        const res = await fetch('/api/wishlist', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{tool_id: toolId}})
                        }});
                        const data = await res.json();
                        if (data.ok) {{
                            const icon = document.getElementById('notify-icon-' + toolId);
                            const text = document.getElementById('notify-text-' + toolId);
                            if (data.saved) {{
                                icon.innerHTML = '&#9989;';
                                text.textContent = 'Notified when available!';
                                showToast("We'll email you when this tool goes on sale!");
                            }} else {{
                                icon.innerHTML = '&#128276;';
                                text.textContent = 'Notify me when available ({cta_price})';
                                showToast('Notification removed');
                            }}
                        }}
                    }} catch(e) {{ console.error(e); }}
                }}
                </script>
                """
            else:
                cta_html = f"""
                {cta_pill}
                <a href="/auth/github?next=/tool/{slug}" class="btn btn-primary" style="font-size:16px;padding:14px 32px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg> Notify me when available ({cta_price})
                </a>
                """
        else:
            # Unclaimed import with external pricing — link to their site
            _launch = date(2026, 3, 2)
            _pill_text = "Available March 2" if date.today() < _launch else "Available soon"
            unclaimed_pill = f'<div style="display:inline-block;background:var(--terracotta);color:var(--slate);font-size:12px;font-weight:700;padding:4px 12px;border-radius:999px;margin-bottom:8px;">{_pill_text} &middot; {cta_price}/mo</div>'
            cta_html = f"""
            {unclaimed_pill}
            <a href="/api/click/{escape(slug)}" target="_blank" rel="noopener" class="btn btn-primary" style="font-size:16px;padding:14px 32px;">
                Get it from {cta_price}/mo &rarr;
            </a>
            """
    else:
        cta_html = f"""
        <a href="/api/click/{escape(slug)}" target="_blank" rel="noopener" class="btn btn-primary" style="font-size:16px;padding:14px 32px;">
            Visit Website &rarr;
        </a>
        """

    click_badge = (
        f'<div style="font-size:12px;color:var(--ink-muted);margin-top:8px;">'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg> {click_count} developer{"s" if click_count != 1 else ""} visited via IndieStack this month</div>'
    ) if click_count > 0 else ''

    use_active = 'use_this' in reactions['user_reactions']
    bm_active = 'bookmark' in reactions['user_reactions']
    use_count = reactions['counts']['use_this']
    bm_count = reactions['counts']['bookmark']
    reactions_html = f'''
    <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <button onclick="react({tool_id},'use_this')" id="react-use_this"
                style="background:{'var(--accent-light,#E6FAFF)' if use_active else 'var(--card-bg)'};
                       border:1px solid {'var(--accent)' if use_active else 'var(--border)'};
                       padding:8px 16px;border-radius:999px;font-size:13px;cursor:pointer;min-height:44px;
                       color:{'var(--accent)' if use_active else 'var(--ink-light)'};">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-2px;"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg> I use this{f' ({use_count})' if use_count else ''}
        </button>
        <button onclick="react({tool_id},'bookmark')" id="react-bookmark"
                style="background:{'var(--gold-light,#FDF8EE)' if bm_active else 'var(--card-bg)'};
                       border:1px solid {'var(--gold)' if bm_active else 'var(--border)'};
                       padding:8px 16px;border-radius:999px;font-size:13px;cursor:pointer;min-height:44px;
                       color:{'var(--gold)' if bm_active else 'var(--ink-light)'};">
            &#9733; Bookmarked{f' ({bm_count})' if bm_count else ''}
        </button>
    </div>
    <script>
    async function react(toolId, reaction) {{
        const res = await fetch('/api/react/' + toolId, {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{reaction: reaction}})
        }});
        if (res.ok) location.reload();
    }}
    </script>
    '''

    # JSON-LD structured data for SEO
    json_ld_data = {
        "@context": "https://schema.org",
        "@type": "SoftwareApplication",
        "name": tool['name'],
        "description": tool.get('description') or tool['tagline'],
        "url": f"{BASE_URL}/tool/{tool['slug']}",
        "applicationCategory": tool.get('category_name', 'WebApplication'),
        "operatingSystem": "Web",
        "offers": {
            "@type": "Offer",
            "availability": "https://schema.org/InStock",
            "price": "0",
            "priceCurrency": "GBP",
        }
    }
    if tool.get('price_pence') and tool['price_pence'] > 0:
        json_ld_data["offers"]["price"] = f"{tool['price_pence'] / 100:.2f}"
    if tool.get('maker_name') and tool['maker_name'] != 'Community Curated':
        json_ld_data["author"] = {
            "@type": "Person",
            "name": tool['maker_name'],
        }
        if tool.get('maker_url'):
            json_ld_data["author"]["url"] = tool['maker_url']
    if tool.get('url'):
        json_ld_data["installUrl"] = tool['url']
    if tool.get('source_type') == 'code' and tool.get('github_url'):
        json_ld_data["codeRepository"] = tool['github_url']
    if review_count > 0:
        json_ld_data["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": str(avg_rating),
            "reviewCount": str(review_count)
        }
    json_ld = json.dumps(json_ld_data, ensure_ascii=False)
    extra_head = f'<script type="application/ld+json">{json_ld}</script>'

    # Changelogs
    changelogs = await get_tool_changelogs(db, tool_id, limit=10)
    changelog_html = ''
    if changelogs:
        cl_cards = '\n'.join(update_card(cl) for cl in changelogs)
        changelog_html = f"""
        <div class="section-divider">
            <h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:24px;">Changelog</h2>
            {cl_cards}
        </div>
        """

    # Smart similar tools: score by shared tags + same category
    similar = await get_similar_tools(db, tool_id, int(tool['category_id']), tool.get('tags', ''))
    if not similar:
        # Fallback to basic category-based related tools
        similar = await get_related_tools(db, tool_id, int(tool['category_id']))

    # Similar tools section
    if similar:
        similar_cards = "".join(tool_card(t) for t in similar)
        similar_html = f'''
        <div class="section-divider">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:16px;">
                Similar Tools
            </h2>
            <div class="scroll-row card-stagger">{similar_cards}</div>
        </div>
        '''
    else:
        similar_html = ''

    # Success/info banners for claim flow
    banners_html = ''
    if request.query_params.get('claimed') == '1':
        banners_html += '<div class="alert alert-success" style="margin-bottom:16px;"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg> You\'ve claimed this tool! You can now manage it from your <a href="/dashboard" style="font-weight:700;">dashboard</a>.</div>'
    elif request.query_params.get('claim') == 'sent' or request.query_params.get('claim_requested') == '1':
        banners_html += '<div class="alert alert-info" style="margin-bottom:16px;">&#9989; Claim request submitted! We\'ll review it and get back to you shortly.</div>'
    if request.query_params.get('flagged') == '1':
        banners_html += '<div class="alert alert-info" style="margin-bottom:16px;">Thanks for the report. We\'ll review it shortly.</div>'
    boosted_param = request.query_params.get('boosted')
    if boosted_param == '1':
        banners_html += '<div class="alert alert-success" style="margin-bottom:16px;">&#9733; <strong>Your tool is now boosted!</strong> It has priority placement for 30 days and will be featured in our weekly newsletter.</div>'
    claim_banner = banners_html

    # Breadcrumbs
    breadcrumb_html = f'''
<nav style="font-size:13px;color:var(--ink-muted);margin-bottom:16px;">
    <a href="/" style="color:var(--ink-muted);text-decoration:none;">Home</a>
    <span style="margin:0 8px;">&rsaquo;</span>
    <a href="/category/{escape(str(tool.get('category_slug', '')))}" style="color:var(--ink-muted);text-decoration:none;">{escape(str(tool.get('category_name', '')))}</a>
    <span style="margin:0 8px;">&rsaquo;</span>
    <span style="color:var(--ink);">{escape(str(tool['name']))}</span>
</nav>
'''

    # Share row
    tool_url = f"{BASE_URL}/tool/{slug}"
    share_text = f"Check out {name} on IndieStack"
    twitter_url = f"https://twitter.com/intent/tweet?text={quote(share_text)}&url={quote(tool_url)}"
    safe_tool_url = tool_url.replace("'", "\\'")

    share_row = f'''
<div style="display:flex;gap:8px;flex-wrap:wrap;">
    <button onclick="navigator.clipboard.writeText('{safe_tool_url}');this.innerHTML='&#10003; Copied!';setTimeout(()=>this.innerHTML='&#128279; Copy Link',2000)"
            style="padding:8px 16px;min-height:44px;background:var(--cream-dark);border:1px solid var(--border);border-radius:999px;
                   font-size:12px;font-weight:600;cursor:pointer;color:var(--ink-light);font-family:var(--font-body);">
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:2px;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg> Copy Link
    </button>
    <a href="{twitter_url}" target="_blank" rel="noopener"
       style="padding:8px 16px;min-height:44px;background:var(--cream-dark);border:1px solid var(--border);border-radius:999px;
              font-size:12px;font-weight:600;text-decoration:none;color:var(--ink-light);display:inline-flex;align-items:center;gap:4px;">
        &#120143; Share
    </a>
    {'<a href="/dashboard#badge" style="padding:8px 16px;background:var(--cream-dark);border:1px solid var(--border);border-radius:999px;font-size:12px;font-weight:600;text-decoration:none;color:var(--ink-light);display:inline-flex;align-items:center;gap:4px;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:2px;"><path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/></svg> Get Badge</a>' if user and tool.get('maker_id') and user.get('maker_id') == tool.get('maker_id') else ''}
</div>
'''

    # Alternatives links — show if tool replaces competitors
    alternatives_links_html = ''
    replaces_raw = str(tool.get('replaces', '') or '').strip()
    if replaces_raw:
        comp_links = []
        for comp in replaces_raw.split(','):
            comp = comp.strip()
            if not comp:
                continue
            comp_slug = comp.lower().replace(' ', '-').replace('.', '-')
            comp_links.append(
                f'<a href="/alternatives/{escape(comp_slug)}" '
                f'class="pill-link" style="display:inline-block;padding:4px 16px;background:var(--cream-dark);border:1px solid var(--border);'
                f'border-radius:999px;font-size:13px;color:var(--ink-muted);text-decoration:none;font-weight:500;"'
                f'>See indie alternatives to {escape(comp)} &rarr;</a>'
            )
        if comp_links:
            alternatives_links_html = f'''
        <div style="display:flex;gap:8px;flex-wrap:wrap;">
            {"".join(comp_links)}
        </div>'''

    # Plugin type badge
    type_labels = {'mcp_server': 'MCP Server', 'plugin': 'Plugin', 'extension': 'Extension', 'skill': 'Skill'}
    type_badge = ''
    if tool_type and tool_type in type_labels:
        type_badge = (
            f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:12px;font-weight:600;'
            f'color:var(--slate-dark);background:rgba(0,212,245,0.1);padding:4px 12px;border-radius:999px;'
            f'border:1px solid var(--slate);">'
            f'{escape(type_labels[tool_type])}</span>'
        )

    install_block = ''
    if install_command.strip():
        safe_cmd = escape(install_command.strip())
        install_block = (
            f'<div style="background:var(--terracotta-dark);border-radius:var(--radius-sm);padding:16px 24px;'
            f'margin-top:16px;display:flex;align-items:center;justify-content:space-between;gap:16px;">'
            f'<code style="font-family:var(--font-mono);font-size:14px;color:var(--slate);white-space:nowrap;'
            f'overflow-x:auto;">{safe_cmd}</code>'
            f'<button data-copy="{safe_cmd}" style="background:var(--slate,#64748B);color:#fff;border:none;border-radius:999px;'
            f'padding:8px 16px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;">Copy</button>'
            f'</div>'
        )

    platform_tags = ''
    if platforms_raw.strip():
        platform_list = [p.strip() for p in platforms_raw.split(',') if p.strip()]
        pills = ''.join(
            f'<span style="display:inline-block;font-size:12px;font-weight:500;padding:4px 12px;'
            f'background:var(--cream-dark);border:1px solid var(--border);border-radius:999px;'
            f'color:var(--ink-light);">{escape(p)}</span>'
            for p in platform_list
        )
        platform_tags = f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px;">{pills}</div>'

    # Pixel art icon (larger on detail page)
    detail_pixel_html = ''
    pixel_data = str(tool.get('pixel_icon', '') or '')
    if pixel_data and len(pixel_data) == 49:
        detail_pixel_html = pixel_icon_svg(pixel_data, size=48)

    # Build agent assembly metadata section
    _api_type = str(tool.get('api_type', '') or '')
    _auth_method = str(tool.get('auth_method', '') or '')
    _sdk_packages = str(tool.get('sdk_packages', '') or '')
    _env_vars = str(tool.get('env_vars', '') or '')
    _install_cmd_meta = str(tool.get('install_command', '') or '')
    _frameworks = str(tool.get('frameworks_tested', '') or '')

    _has_assembly_meta = any([_api_type, _auth_method, _sdk_packages, _env_vars, _install_cmd_meta, _frameworks])

    assembly_html = ''
    if _has_assembly_meta:
        assembly_html = '<div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:20px;margin:24px 0;">'
        assembly_html += '<h3 style="margin:0 0 16px;font-size:16px;font-family:var(--font-display);">Agent Assembly Metadata</h3>'
        assembly_html += '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px;">'

        if _api_type:
            assembly_html += f'<div><span style="color:var(--ink-muted);font-size:13px;">API Type</span><br><strong>{escape(_api_type)}</strong></div>'
        if _auth_method:
            _auth_labels = {"api_key": "API Key", "oauth2": "OAuth 2.0", "bearer": "Bearer Token", "none": "None (open)"}
            assembly_html += f'<div><span style="color:var(--ink-muted);font-size:13px;">Auth</span><br><strong>{_auth_labels.get(_auth_method, escape(_auth_method))}</strong></div>'
        if _install_cmd_meta:
            assembly_html += f'<div style="grid-column:1/-1;"><span style="color:var(--ink-muted);font-size:13px;">Install</span><br><code style="background:var(--cream-dark);padding:6px 12px;border-radius:6px;font-family:var(--font-mono);font-size:13px;display:inline-block;margin-top:4px;">{escape(_install_cmd_meta)}</code></div>'
        if _sdk_packages:
            assembly_html += f'<div style="grid-column:1/-1;"><span style="color:var(--ink-muted);font-size:13px;">SDK Packages</span><br><code style="background:var(--cream-dark);padding:6px 12px;border-radius:6px;font-family:var(--font-mono);font-size:13px;display:inline-block;margin-top:4px;">{escape(_sdk_packages)}</code></div>'
        if _env_vars:
            assembly_html += f'<div style="grid-column:1/-1;"><span style="color:var(--ink-muted);font-size:13px;">Required Env Vars</span><br><code style="background:var(--cream-dark);padding:6px 12px;border-radius:6px;font-family:var(--font-mono);font-size:13px;display:inline-block;margin-top:4px;">{escape(_env_vars)}</code></div>'
        if _frameworks:
            _fw_pills = ''.join(f'<span style="display:inline-block;background:var(--info-bg);color:var(--info-text);padding:2px 8px;border-radius:999px;font-size:12px;margin:2px 4px 2px 0;">{escape(f.strip())}</span>' for f in _frameworks.split(',') if f.strip())
            assembly_html += f'<div style="grid-column:1/-1;"><span style="color:var(--ink-muted);font-size:13px;">Tested With</span><br><div style="margin-top:4px;">{_fw_pills}</div></div>'

        assembly_html += '</div></div>'

    # Build "Confirmed Works With" section from compatibility pairs
    compatible_html = ''
    try:
        _pairs = await get_verified_pairs(db, slug)
        _has_pairs = bool(_pairs)
        _pair_items = ''
        if _has_pairs:
            for _p in _pairs[:8]:  # limit to 8
                _p_slug = escape(str(_p.get('pair_slug', '')))
                _p_count = int(_p.get('success_count', 0))
                _verified = bool(_p.get('verified', 0))
                _p_url = str(_p.get('pair_url') or '')
                _badge = '<span style="color:var(--success-text);font-size:11px;margin-left:4px;">&#10003;</span>' if _verified else ''
                _count_text = f' <span style="color:var(--ink-muted);font-size:11px;font-weight:400;">&middot; {_p_count} confirmed</span>' if _p_count >= 2 else ''
                _favicon_html = ''
                if _p_url:
                    _parsed = urlparse(_p_url)
                    _domain = _parsed.netloc or _parsed.path.split('/')[0]
                    if _domain:
                        _favicon_html = f'<img src="https://www.google.com/s2/favicons?domain={_domain}&sz=16" width="16" height="16" style="border-radius:4px;" onerror="this.style.display=\'none\'">'
                _pair_items += f'''<a href="/tool/{_p_slug}" style="display:inline-flex;align-items:center;gap:6px;
                    background:var(--card-bg);border:1px solid var(--border);border-radius:999px;
                    padding:6px 14px;text-decoration:none;color:var(--ink);font-size:13px;
                    font-weight:500;transition:border-color 0.15s;"
                    onmouseover="this.style.borderColor='var(--accent)'"
                    onmouseout="this.style.borderColor='var(--border)'"
                    >{_favicon_html}{_p_slug}{_badge}{_count_text}</a>'''

        # "I use this with..." button for logged-in users
        _compat_button = ''
        if user:
            _tool_name = escape(str(tool.get('name', slug)))
            _compat_button = f'''
            <div id="compat-add" style="margin-top:12px;">
                <button onclick="document.getElementById('compat-search-wrap').style.display='block';this.style.display='none';"
                    style="display:inline-flex;align-items:center;gap:6px;background:transparent;
                    border:1px dashed var(--border);border-radius:999px;padding:6px 14px;
                    color:var(--ink-muted);font-size:13px;cursor:pointer;transition:border-color 0.15s;"
                    onmouseover="this.style.borderColor='var(--accent)'"
                    onmouseout="this.style.borderColor='var(--border)'">
                    <span style="color:var(--accent);font-weight:600;font-size:15px;">+</span> I use this with&hellip;
                </button>
                <div id="compat-search-wrap" style="display:none;margin-top:8px;position:relative;">
                    <input id="compat-search-input" type="text" placeholder="Search for a tool..."
                        style="width:100%;max-width:300px;padding:8px 12px;border:1px solid var(--border);
                        border-radius:8px;font-size:13px;background:var(--card-bg);color:var(--ink);
                        outline:none;" autocomplete="off">
                    <div id="compat-search-results" style="position:absolute;top:100%;left:0;width:100%;max-width:300px;
                        background:var(--card-bg);border:1px solid var(--border);border-radius:8px;
                        margin-top:4px;max-height:200px;overflow-y:auto;display:none;z-index:10;
                        box-shadow:0 4px 12px rgba(0,0,0,0.1);"></div>
                </div>
                <div id="compat-msg" style="display:none;margin-top:8px;font-size:13px;"></div>
            </div>
            <script>
            (function() {{
                var input = document.getElementById('compat-search-input');
                var results = document.getElementById('compat-search-results');
                var msg = document.getElementById('compat-msg');
                var timer = null;
                var currentSlug = '{escape(slug)}';
                input.addEventListener('input', function() {{
                    clearTimeout(timer);
                    var q = input.value.trim();
                    if (q.length < 2) {{ results.style.display = 'none'; return; }}
                    timer = setTimeout(function() {{
                        fetch('/api/tools/search?q=' + encodeURIComponent(q))
                            .then(function(r) {{ return r.json(); }})
                            .then(function(data) {{
                                var tools = data.tools || [];
                                if (!tools.length) {{ results.innerHTML = '<div style="padding:8px 12px;color:var(--ink-muted);font-size:13px;">No tools found</div>'; results.style.display = 'block'; return; }}
                                var html = '';
                                for (var i = 0; i < Math.min(tools.length, 6); i++) {{
                                    var t = tools[i];
                                    if (t.slug === currentSlug) continue;
                                    html += '<div class="compat-result" data-slug="' + t.slug + '" style="padding:8px 12px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--border);" onmouseover="this.style.background=\\'var(--cream-dark)\\'" onmouseout="this.style.background=\\'transparent\\'">' + (t.name || t.slug) + '</div>';
                                }}
                                results.innerHTML = html || '<div style="padding:8px 12px;color:var(--ink-muted);font-size:13px;">No other tools found</div>';
                                results.style.display = 'block';
                                results.querySelectorAll('.compat-result').forEach(function(el) {{
                                    el.addEventListener('click', function() {{
                                        var pairSlug = el.getAttribute('data-slug');
                                        results.style.display = 'none';
                                        input.value = '';
                                        var fd = new FormData();
                                        fd.append('pair_slug', pairSlug);
                                        fetch('/tool/' + currentSlug + '/compatible', {{ method: 'POST', body: fd }})
                                            .then(function(r) {{
                                                if (r.status === 409) {{ msg.textContent = 'You already confirmed this pairing'; msg.style.color = 'var(--ink-muted)'; msg.style.display = 'block'; return; }}
                                                if (r.status === 401) {{ window.location = '/login?next=/tool/' + currentSlug; return; }}
                                                if (!r.ok) {{ return r.json().then(function(d) {{ msg.textContent = d.error || 'Error'; msg.style.color = 'var(--error-text)'; msg.style.display = 'block'; }}); }}
                                                return r.json().then(function(d) {{
                                                    msg.innerHTML = '<span style="color:var(--success-text);">Confirmed!</span> ' + pairSlug + ' added.';
                                                    msg.style.display = 'block';
                                                    var pillsDiv = document.getElementById('compat-pills');
                                                    if (pillsDiv) {{
                                                        var newPill = document.createElement('a');
                                                        newPill.href = '/tool/' + pairSlug;
                                                        newPill.style.cssText = 'display:inline-flex;align-items:center;gap:6px;background:var(--card-bg);border:1px solid var(--border);border-radius:999px;padding:6px 14px;text-decoration:none;color:var(--ink);font-size:13px;font-weight:500;';
                                                        newPill.textContent = pairSlug;
                                                        pillsDiv.appendChild(newPill);
                                                    }}
                                                }});
                                            }});
                                    }});
                                }});
                            }});
                    }}, 300);
                }});
                document.addEventListener('click', function(e) {{
                    if (!e.target.closest('#compat-add')) results.style.display = 'none';
                }});
            }})();
            </script>'''

        if _has_pairs:
            compatible_html = f'''<div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:20px;margin:24px 0;">
                <h3 style="margin:0 0 12px;font-size:16px;font-family:var(--font-display);">Confirmed Works With</h3>
                <div id="compat-pills" style="display:flex;flex-wrap:wrap;gap:8px;">{_pair_items}</div>
                {_compat_button}
            </div>'''
        elif user:
            _tool_name = escape(str(tool.get('name', slug)))
            compatible_html = f'''<div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:20px;margin:24px 0;">
                <h3 style="margin:0 0 12px;font-size:16px;font-family:var(--font-display);">Confirmed Works With</h3>
                <p style="color:var(--ink-muted);font-size:13px;margin:0 0 8px;">Know a tool that works with {_tool_name}?</p>
                <div id="compat-pills" style="display:flex;flex-wrap:wrap;gap:8px;"></div>
                {_compat_button}
            </div>'''
    except Exception:
        pass

    # Build maker story section
    maker_story_html = ''
    _story_fields = [
        ('story_motivation', 'Why I built this'),
        ('story_challenge', 'The hardest part'),
        ('story_advice', 'Advice for makers'),
        ('story_fun_fact', 'Fun fact'),
    ]
    _story_items = ''
    for _field, _label in _story_fields:
        _val = str(tool.get(_field) or '').strip()
        if _val:
            _story_items += f'''
            <div style="margin-bottom:16px;">
                <div style="font-size:13px;font-weight:600;color:var(--accent);margin-bottom:4px;">{_label}</div>
                <p style="color:var(--ink-light);font-size:15px;line-height:1.6;margin:0;">{escape(_val)}</p>
            </div>
            '''
    if _story_items:
        _maker_name = escape(str(tool.get('maker_name') or 'the maker'))
        maker_story_html = f'''
        <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius);padding:24px;margin-top:24px;">
            <h3 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                About {_maker_name}
            </h3>
            {_story_items}
        </div>
        '''

    # Community flag / report section
    safe_slug = escape(slug)
    if user:
        flag_trigger = (
            '<button onclick="var p=document.getElementById(&#39;flag-panel&#39;);'
            "p.style.display=p.style.display==='none'?'block':'none'\""
            ' style="background:none;border:none;color:var(--ink-muted);font-size:13px;'
            'cursor:pointer;text-decoration:underline;">Report a problem with this listing</button>'
        )
        flag_form = (
            '<div id="flag-panel" style="display:none;margin-top:16px;text-align:left;'
            'max-width:400px;margin-left:auto;margin-right:auto;background:var(--card-bg);'
            'border:1px solid var(--border);border-radius:var(--radius);padding:20px;">'
            f'<form method="POST" action="/tool/{safe_slug}/flag">'
            '<p style="font-weight:600;font-size:14px;color:var(--ink);margin-bottom:12px;">'
            "What's the issue?</p>"
            '<label style="display:block;margin-bottom:8px;font-size:13px;color:var(--ink-light);cursor:pointer;">'
            '<input type="radio" name="flag_type" value="abandoned" required style="margin-right:8px;">'
            'Abandoned / Dead project</label>'
            '<label style="display:block;margin-bottom:8px;font-size:13px;color:var(--ink-light);cursor:pointer;">'
            '<input type="radio" name="flag_type" value="misleading" style="margin-right:8px;">'
            'Misleading description</label>'
            '<label style="display:block;margin-bottom:8px;font-size:13px;color:var(--ink-light);cursor:pointer;">'
            '<input type="radio" name="flag_type" value="not_indie" style="margin-right:8px;">'
            'Not indie-built (corporate / VC-backed)</label>'
            '<label style="display:block;margin-bottom:8px;font-size:13px;color:var(--ink-light);cursor:pointer;">'
            '<input type="radio" name="flag_type" value="spam" style="margin-right:8px;">'
            'Spam</label>'
            '<label style="display:block;margin-bottom:12px;font-size:13px;color:var(--ink-light);cursor:pointer;">'
            '<input type="radio" name="flag_type" value="other" style="margin-right:8px;">'
            'Other</label>'
            '<textarea name="note" placeholder="Optional: anything else we should know?"'
            ' style="width:100%;padding:8px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);'
            'font-size:13px;resize:vertical;height:60px;background:var(--card-bg);color:var(--ink);'
            'font-family:var(--font-body);margin-bottom:12px;"></textarea>'
            '<button type="submit" class="btn btn-secondary"'
            ' style="width:100%;justify-content:center;font-size:13px;padding:8px;">Submit Report</button>'
            '</form></div>'
        )
    else:
        flag_trigger = (
            '<span style="color:var(--ink-muted);font-size:13px;">Something wrong? '
            f'<a href="/login?next=/tool/{safe_slug}" style="color:var(--ink-muted);text-decoration:underline;">'
            'Log in</a> to report.</span>'
        )
        flag_form = ''

    flag_section_html = (
        '<div style="text-align:center;margin-top:32px;padding-top:24px;border-top:1px solid var(--border);">'
        f'{flag_trigger}{flag_form}</div>'
    )

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:800px;">
        {breadcrumb_html}
        {claim_banner}
        <div style="position:relative;padding:32px 24px 24px;border-radius:var(--radius);
                    background:linear-gradient(135deg, var(--cream-dark) 0%, var(--card-bg) 100%);
                    border:1px solid var(--border);margin-bottom:24px;">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:24px;">
            <div style="flex:1;">
                <a href="/category/{cat_slug}" class="tag mb-2" style="display:inline-block;">{cat_name}</a>
                <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-top:8px;">
                    {detail_pixel_html}
                    <h1 style="font-family:var(--font-display);font-size:36px;">{name}</h1>
                    {totw_badge}
                    {ejectable_badge_html() if is_ejectable else ''}
                    {type_badge}
                    {'<span style="display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:600;background:var(--success-bg);color:var(--success-text);border:1px solid var(--success-border);"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:2px;"><path d="M16.5 9.4 7.55 4.24"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg> Open Source</span>' if source_type == 'code' else '<span style="display:inline-flex;align-items:center;gap:4px;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:600;background:var(--info-bg);color:var(--info-text);border:1px solid var(--info-border);">&#9729; SaaS</span>'}
                    {pulse_html}

                    {rating_display_html}
                </div>
                <p style="font-size:18px;color:var(--ink-muted);margin-top:8px;">{tagline}</p>
                {install_block}
                {platform_tags}
                {price_tag_html}
            </div>
            <button class="upvote-btn" onclick="upvote({tool_id})" id="upvote-{tool_id}"
                    style="flex-shrink:0;min-width:60px;">
                <span class="arrow">&#9650;</span>
                <span id="count-{tool_id}">{'Upvote' if upvotes < 5 else upvotes}</span>
            </button>
        </div>
        </div>

        {claim_message}
        {claim_html}
        {community_notice}
        {analytics_wall_html}
        {boost_html}

        <!-- Description -->
        <div style="margin-top:32px;">
            <p style="white-space:pre-line;color:var(--ink-light);line-height:1.8;font-size:16px;">{description}</p>
        </div>

        <!-- CTA + Maker -->
        <div style="margin-top:24px;display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
            {cta_html}
            {wishlist_btn_html}
        </div>
        <div style="margin-top:12px;">{maker_html}</div>
        {click_badge}

        <!-- Metadata card -->
        <div style="margin-top:32px;padding:24px;background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius);">
            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
                {reactions_html}
            </div>
            <div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border);display:flex;gap:8px;flex-wrap:wrap;align-items:center;">
                {share_row}
            </div>
            {f'<div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border);">' + tag_html + '</div>' if tag_html else ''}
            {f'<div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border);display:flex;gap:8px;flex-wrap:wrap;align-items:center;">' + github_badge + ' ' + freshness_badge + '</div>' if github_badge or freshness_badge else ''}
            {f'<div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border);display:flex;gap:12px;flex-wrap:wrap;align-items:center;">' + token_hint_html + '</div>' if token_hint_html else ''}
            {f'<div style="margin-top:16px;padding-top:16px;border-top:1px solid var(--border);">' + alternatives_links_html + '</div>' if alternatives_links_html else ''}
        </div>

        {maker_story_html}

        {assembly_html}

        {compatible_html}

        {similar_html}

        {changelog_html}

        {reviews_html}

        {flag_section_html}
    </div>
    """
    og_image_url = f"{BASE_URL}/logo.png"
    response = HTMLResponse(page_shell(f"{tool['name']} — {tagline} | IndieStack", body + email_sticky_bar(), description=tagline, extra_head=extra_head, user=user, og_image=og_image_url, canonical=f"/tool/{slug}"))
    response.headers["Cache-Control"] = "public, max-age=120, stale-while-revalidate=600"
    return response


@router.post("/tool/{slug}/review")
async def submit_review(
    request: Request,
    slug: str,
    rating: int = Form(...),
    review_title: str = Form("", alias="review_title"),
    review_body: str = Form("", alias="review_body"),
):
    user = request.state.user
    if not user:
        return RedirectResponse("/login", status_code=302)

    db = request.state.db
    tool = await get_tool_by_slug(db, slug)
    if not tool:
        return RedirectResponse("/", status_code=302)

    # Validate rating
    if rating < 1 or rating > 5:
        rating = 5

    await create_review(
        db,
        tool_id=tool['id'],
        user_id=user['id'],
        rating=rating,
        title=review_title,
        body=review_body,
    )

    return RedirectResponse(f"/tool/{slug}", status_code=303)


@router.post("/tool/{slug}/flag")
async def flag_tool(
    request: Request,
    slug: str,
    flag_type: str = Form(""),
    note: str = Form(""),
):
    user = request.state.user
    if not user:
        return RedirectResponse(f"/login?next=/tool/{slug}", status_code=302)

    db = request.state.db
    tool = await get_tool_by_slug(db, slug)
    if not tool:
        return RedirectResponse("/", status_code=302)

    valid_types = ('abandoned', 'misleading', 'not_indie', 'spam', 'other')
    if flag_type not in valid_types:
        return RedirectResponse(f"/tool/{slug}", status_code=303)

    from indiestack.db import create_tool_flag
    await create_tool_flag(db, tool['id'], user['id'], flag_type, note.strip()[:500])

    return RedirectResponse(f"/tool/{slug}?flagged=1", status_code=303)


@router.post("/api/react/{tool_id}")
async def react_to_tool(request: Request, tool_id: int):
    """Toggle a reaction (use_this or bookmark) on a tool."""
    data = await request.json()
    reaction = data.get("reaction")
    if reaction not in ("use_this", "bookmark"):
        return JSONResponse({"error": "Invalid reaction"}, status_code=400)
    user = request.state.user
    session_id = request.cookies.get("session_id") if not user else None
    result = await toggle_reaction(
        request.state.db, tool_id, reaction,
        user_id=user["id"] if user else None,
        session_id=session_id,
    )
    return JSONResponse({"ok": True, **result})


@router.post("/tool/{slug}/compatible")
async def report_compatible(
    request: Request,
    slug: str,
    pair_slug: str = Form(...),
):
    """Report that two tools work well together (community compatibility)."""
    user = request.state.user
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)

    db = request.state.db

    # Validate both tools exist
    tool = await get_tool_by_slug(db, slug)
    if not tool:
        return JSONResponse({"error": f"Tool '{slug}' not found"}, status_code=404)

    pair_tool = await get_tool_by_slug(db, pair_slug)
    if not pair_tool:
        return JSONResponse({"error": f"Tool '{pair_slug}' not found"}, status_code=404)

    # Reject self-pairing
    if slug == pair_slug:
        return JSONResponse({"error": "Cannot pair a tool with itself"}, status_code=400)

    # Sort alphabetically for consistent storage
    a, b = sorted([slug, pair_slug])

    # Check for duplicate report from this user
    cursor = await db.execute(
        "SELECT id FROM user_tool_pair_reports WHERE user_id = ? AND tool_a_slug = ? AND tool_b_slug = ?",
        (user["id"], a, b),
    )
    existing = await cursor.fetchone()
    if existing:
        return JSONResponse({"error": "Already confirmed"}, status_code=409)

    # Record the user's report
    await db.execute(
        "INSERT INTO user_tool_pair_reports (user_id, tool_a_slug, tool_b_slug) VALUES (?, ?, ?)",
        (user["id"], a, b),
    )

    # Upsert into tool_pairs using existing helper
    await record_tool_pair(db, a, b, source="user")

    return JSONResponse({"ok": True, "pair": pair_slug})

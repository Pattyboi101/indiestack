"""Maker dashboard — tool management, sales, analytics, settings."""

from datetime import datetime, timezone
from html import escape

import csv
import io
import json

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse

from indiestack.config import BASE_URL

from indiestack.routes.components import page_shell, star_rating_html, tool_card, indie_badge_html, pagination_html, update_card, launch_readiness_bar, pixel_icon_svg
from indiestack.db import (
    get_tools_by_maker, get_sales_by_maker, get_maker_revenue, get_maker_stats,
    get_tool_by_id, update_tool, get_all_categories, get_tool_rating,
    get_tool_views_by_maker, get_maker_by_id, update_maker,
    get_user_wishlist, get_updates_by_maker, create_maker_update,
    get_notifications, mark_notifications_read,
    get_tool_changelogs, update_maker_stripe_account,
    get_user_tokens_saved, get_or_create_badge_token,
    get_maker_funnel, get_wishlist_users_for_tool,
    get_launch_readiness, get_similar_makers,
    get_user_milestones, get_unshared_milestones, check_milestones,
    create_user_stack, get_user_stack, add_tool_to_user_stack, remove_tool_from_user_stack, update_user_stack,
    get_tool_by_slug, get_search_terms_for_tool,
    ensure_referral_code, get_referral_count, claim_referral_boost,
    MILESTONE_THRESHOLDS,
    get_purchases_by_email,
    get_total_agent_citations, get_citation_percentile,
    get_maker_query_intelligence, get_maker_agent_breakdown, get_maker_daily_trend,
    create_api_key, get_api_keys_for_user, revoke_api_key, get_api_key_usage_stats,
    get_agent_action_counts, get_agent_action_log, update_api_key_scopes,
    get_developer_profile, toggle_personalization, clear_developer_profile,
    update_user,
    check_pro,
    track_event,
    get_tool_success_rate,
    get_listing_quality_score,
    get_search_gaps,
)
from indiestack.payments import create_connect_account, create_onboarding_link
from indiestack.email import send_email, wishlist_update_html

router = APIRouter()


def require_login(user):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return None


def format_price(pence: int) -> str:
    if not pence:
        return "Free"
    pounds = pence / 100
    if pounds == int(pounds):
        return f"\u00a3{int(pounds)}"
    return f"\u00a3{pounds:.2f}"


# ── Dashboard Overview ───────────────────────────────────────────────────

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_overview(request: Request):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    maker_id = user.get('maker_id')

    # Stats
    tool_count = 0
    total_upvotes = 0
    total_revenue = 0
    total_sales = 0

    if maker_id:
        stats = await get_maker_stats(db, maker_id)
        tool_count = stats['tool_count']
        total_upvotes = stats['total_upvotes']
        revenue = await get_maker_revenue(db, maker_id)
        total_revenue = revenue['total_revenue'] - revenue['total_commission']
        total_sales = revenue['sale_count']

    # Pro subscription check
    is_pro = await check_pro(db, user['id'])

    # Trial banner removed — everything is free now
    trial_banner = ''

    # Pro upsell banner removed — everything is free now
    pro_banner = ''

    # Check if user has any claimed tools
    has_claimed_tools = False
    if maker_id:
        _claimed_cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM tools WHERE maker_id = ? AND claimed_at IS NOT NULL AND status = 'approved'",
            (maker_id,),
        )
        _claimed_row = await _claimed_cursor.fetchone()
        has_claimed_tools = (_claimed_row['cnt'] or 0) > 0

    # Tokens saved
    user_tokens = await get_user_tokens_saved(db, user['id'])
    tokens_k = user_tokens // 1000 if user_tokens else 0

    # Agent citations (30-day)
    agent_citations_30d = await get_total_agent_citations(db, maker_id, days=30) if maker_id else 0
    citation_percentile = await get_citation_percentile(db, maker_id, days=30) if maker_id else None

    # Fetch maker's tools once for success rate + quality score
    _maker_tools = await get_tools_by_maker(db, maker_id) if maker_id else []

    # Aggregate success rate across all maker's tools
    maker_success_rate = None
    if _maker_tools:
        _sr_success = 0
        _sr_total = 0
        for _t in _maker_tools:
            _sr = await get_tool_success_rate(db, _t['slug'])
            _sr_success += _sr.get('success', 0)
            _sr_total += _sr.get('total', 0)
        if _sr_total > 0:
            maker_success_rate = round(_sr_success / _sr_total * 100)

    # Listing Quality Score
    quality_score = None
    quality_tips = []
    if _maker_tools:
        _qs_scores = []
        _qs_all_tips = []
        for _t in _maker_tools[:10]:  # Cap at 10
            _qs = await get_listing_quality_score(db, _t)
            _qs_scores.append(_qs['score'])
            _qs_all_tips.extend(_qs['tips'])
        if _qs_scores:
            quality_score = round(sum(_qs_scores) / len(_qs_scores))
            # Deduplicate tips
            _seen = set()
            for _tip in _qs_all_tips:
                if _tip not in _seen:
                    _seen.add(_tip)
                    quality_tips.append(_tip)
                if len(quality_tips) >= 3:
                    break

    sr_display = f'{maker_success_rate}%' if maker_success_rate is not None else '\u2014'
    sr_color = 'var(--accent)' if (maker_success_rate or 0) >= 70 else '#E2B764' if (maker_success_rate or 0) >= 40 else '#e74c3c'

    pro_badge = ' <span style="display:inline-block;background:var(--accent);color:white;font-size:10px;font-weight:700;padding:2px 8px;border-radius:999px;vertical-align:middle;margin-left:8px;">PRO</span>' if is_pro else ''
    upgrade_html = ''

    just_subscribed_param = request.query_params.get('subscribed') == 'true'
    just_subscribed = just_subscribed_param and is_pro
    welcome_banner = ''
    if just_subscribed:
        welcome_banner = '<div style="background:#ECFDF5;border:1px solid #6EE7B7;border-radius:var(--radius-sm);padding:12px 16px;margin-bottom:16px;color:#065F46;font-weight:600;font-size:14px;">Welcome to IndieStack Pro! Your account has been upgraded.</div>'
    elif just_subscribed_param and not is_pro:
        welcome_banner = '<div style="background:#FEF3C7;border:1px solid #FCD34D;border-radius:var(--radius-sm);padding:12px 16px;margin-bottom:16px;color:#92400E;font-weight:600;font-size:14px;">Payment received! Your Pro access is activating &mdash; refresh in a moment.</div>'

    # Citation intel is now integrated into ai_intel_html below

    maker_stripe_id = None
    payment_card_html = ''

    # Badge embed code for makers
    badge_section = ''
    if maker_id:
        # Get first tool slug for the embed example
        if _maker_tools:
            first_tool = _maker_tools[0]
            first_slug = first_tool['slug']
            has_price = first_tool.get('price_pence') and first_tool['price_pence'] > 0
            has_stripe = bool(first_tool.get('stripe_account_id'))

            badge_url = f"{BASE_URL}/api/badge/{first_slug}.svg"
            tool_url = f"{BASE_URL}/tool/{first_slug}"

            badge_section = f'''
            <div class="card" style="margin-top:24px;">
                <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:4px;">
                    Live AI Recommendation Badge
                </h3>
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                    Shows a live count of how many times AI agents have recommended your tool. The red dot pulses to show it&rsquo;s live. Add it to your README or website.
                </p>
                <div style="margin-bottom:20px;text-align:center;padding:16px;background:var(--cream-dark);border-radius:var(--radius);">
                    <img src="{badge_url}" alt="IndieStack Badge" style="height:20px;">
                </div>
                <div style="display:flex;flex-direction:column;gap:16px;">
                    <div>
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                            <span style="width:22px;height:22px;border-radius:50%;background:var(--accent);color:white;display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0;">1</span>
                            <span style="font-size:13px;font-weight:600;color:var(--ink);">For GitHub README (Markdown)</span>
                        </div>
                        <div style="position:relative;">
                            <pre style="background:var(--ink);color:var(--slate);padding:12px 16px;border-radius:var(--radius-sm);font-size:11px;
                                        font-family:var(--font-mono);overflow-x:auto;margin:0;white-space:pre-wrap;word-break:break-all;">[![{first_tool['name']} on IndieStack]({badge_url})]({tool_url})</pre>
                            <button onclick="navigator.clipboard.writeText(this.dataset.code);this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',1500)"
                                    data-code="[![{first_tool['name']} on IndieStack]({badge_url})]({tool_url})"
                                    style="position:absolute;top:8px;right:8px;padding:4px 10px;background:var(--accent);color:white;border:none;border-radius:4px;font-size:11px;cursor:pointer;">Copy</button>
                        </div>
                        <p style="font-size:11px;color:var(--ink-muted);margin-top:6px;">Paste this anywhere in your README.md file on GitHub.</p>
                    </div>
                    <div>
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                            <span style="width:22px;height:22px;border-radius:50%;background:var(--accent);color:white;display:inline-flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0;">2</span>
                            <span style="font-size:13px;font-weight:600;color:var(--ink);">For your website (HTML)</span>
                        </div>
                        <div style="position:relative;">
                            <pre style="background:var(--ink);color:var(--slate);padding:12px 16px;border-radius:var(--radius-sm);font-size:11px;
                                        font-family:var(--font-mono);overflow-x:auto;margin:0;white-space:pre-wrap;word-break:break-all;">&lt;a href="{tool_url}"&gt;&lt;img src="{badge_url}" alt="{first_tool['name']} on IndieStack"&gt;&lt;/a&gt;</pre>
                            <button onclick="navigator.clipboard.writeText(this.dataset.code);this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',1500)"
                                    data-code='<a href="{tool_url}"><img src="{badge_url}" alt="{first_tool["name"]} on IndieStack"></a>'
                                    style="position:absolute;top:8px;right:8px;padding:4px 10px;background:var(--accent);color:white;border:none;border-radius:4px;font-size:11px;cursor:pointer;">Copy</button>
                        </div>
                        <p style="font-size:11px;color:var(--ink-muted);margin-top:6px;">Paste this into any HTML page, landing page, or docs site.</p>
                    </div>
                </div>
            </div>
            '''

    # ── Funnel Analytics (7-day) ──────────────────────────
    funnel_html = ''
    if user.get('maker_id'):
        funnel_data = await get_maker_funnel(db, user['maker_id'], days=7)
        if funnel_data:
            funnel_rows = ''
            for f in funnel_data:
                funnel_rows += f'''
                <tr>
                    <td style="padding:10px 12px;font-weight:600;"><a href="/tool/{f['tool_slug']}" style="color:var(--terracotta);">{f['tool_name']}</a></td>
                    <td style="padding:10px 12px;text-align:center;">{f['views']}</td>
                    <td style="padding:10px 12px;text-align:center;">{f['clicks']}</td>
                    <td style="padding:10px 12px;text-align:center;">{f['wishlist_saves']}</td>
                    <td style="padding:10px 12px;text-align:center;">{f['upvotes']}</td>
                </tr>
                '''
            funnel_html = f'''
            <div style="margin-top:32px;">
                <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg> Funnel Analytics <span style="font-size:13px;color:var(--ink-muted);font-weight:400;">(last 7 days)</span>
                </h2>
                <div class="card" style="overflow-x:auto;">
                    <table style="width:100%;border-collapse:collapse;font-size:14px;">
                        <thead>
                            <tr style="border-bottom:2px solid var(--border);">
                                <th style="padding:10px 12px;text-align:left;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Tool</th>
                                <th style="padding:10px 12px;text-align:center;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Views</th>
                                <th style="padding:10px 12px;text-align:center;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Clicks</th>
                                <th style="padding:10px 12px;text-align:center;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Bookmarks</th>
                                <th style="padding:10px 12px;text-align:center;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Upvotes</th>
                            </tr>
                        </thead>
                        <tbody>{funnel_rows}</tbody>
                    </table>
                </div>
                <p style="font-size:12px;color:var(--ink-muted);margin-top:8px;">Tip: Active tools with changelogs rank higher in search and get a <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg> streak badge.</p>
            </div>
            '''

    # ── Gap signals for empty state ──────────────────────────
    gaps = await get_search_gaps(db, days=30, min_searches=5, limit=3)
    gap_hint = ""
    if gaps:
        gap_items = " · ".join(f"<strong>{escape(str(g['query']))}</strong> ({g['count']}x)" for g in gaps[:3])
        gap_hint = f'''
        <div style="background:var(--surface-raised);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:24px;">
            <p style="font-size:13px;color:var(--ink-muted);margin-bottom:4px;">AI agents searched for these but found nothing:</p>
            <p style="font-size:14px;">{gap_items}</p>
        </div>'''

    # ── AI Distribution Intelligence ──────────────────────────
    ai_intel_html = ''
    if not has_claimed_tools and maker_id:
        # Branch A: maker exists but no claimed tools — empty state
        ai_intel_html = f'''
        <div id="ai-distribution" style="margin-top:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z"/><circle cx="12" cy="14" r="2"/></svg> AI Distribution Intelligence
            </h2>
            {gap_hint}
            <div class="card" style="text-align:center;padding:48px 24px;">
                <div style="margin-bottom:12px;"><svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg></div>
                <p style="font-weight:700;font-size:16px;color:var(--ink);margin-bottom:4px;">Claim your first tool to unlock analytics</p>
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:20px;">See how often AI agents recommend your tools, your success rate, and which queries find you.</p>
                <a href="/" style="display:inline-block;padding:10px 24px;background:var(--accent);color:#0F1D30;border-radius:8px;font-size:14px;font-weight:600;text-decoration:none;">
                    Find Your Tool
                </a>
            </div>
        </div>'''
    elif has_claimed_tools and maker_id:
        # Branch B: has claimed tools — headline stats + full intel (with existing Pro gating)
        queries = await get_maker_query_intelligence(db, user['maker_id'], days=30)
        agents = await get_maker_agent_breakdown(db, user['maker_id'], days=30)
        trend = await get_maker_daily_trend(db, user['maker_id'], days=30)

        # Query intelligence table
        query_rows = ''
        for q in queries:
            query_rows += f'''
            <tr>
                <td style="padding:8px 12px;font-family:var(--font-mono);font-size:13px;">{escape(q['query'])}</td>
                <td style="padding:8px 12px;text-align:center;font-weight:600;">{q['count']}</td>
                <td style="padding:8px 12px;"><a href="/tool/{q['top_result_slug']}" style="color:var(--accent);font-size:13px;">{escape(q['top_result_name'] or q['top_result_slug'])}</a></td>
            </tr>'''

        # Agent breakdown
        agent_rows = ''
        total_citations = sum(a['count'] for a in agents)
        for a in agents:
            pct = round(a['count'] / total_citations * 100) if total_citations else 0
            bar_width = max(pct, 2)
            agent_label = {
                'mcp': 'MCP Server (Claude, Cursor, etc.)',
                'api': 'REST API',
                'web': 'Web Search',
            }.get(a['agent_name'], a['agent_name'] or 'Unknown')
            agent_rows += f'''
            <div style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px;">
                    <span style="color:var(--ink);">{agent_label}</span>
                    <span style="color:var(--ink-muted);">{a['count']} ({pct}%)</span>
                </div>
                <div style="background:var(--cream-dark);border-radius:4px;height:8px;overflow:hidden;">
                    <div style="background:var(--accent);width:{bar_width}%;height:100%;border-radius:4px;"></div>
                </div>
            </div>'''

        # Sparkline trend (pure CSS bars)
        trend_html = ''
        if trend:
            max_val = max((d['citations'] for d in trend), default=1) or 1
            bars = ''
            for d in trend[-14:]:  # Last 14 days
                h = max(int(d['citations'] / max_val * 40), 2)
                day_label = d['day'][5:]  # MM-DD
                bars += f'<div title="{day_label}: {d["citations"]}" style="width:8px;height:{h}px;background:var(--accent);border-radius:2px;flex-shrink:0;"></div>'
            trend_html = f'''
            <div style="margin-top:16px;">
                <h4 style="font-size:13px;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">Daily AI Recommendations (14d)</h4>
                <div style="display:flex;align-items:flex-end;gap:3px;height:44px;padding:2px 0;">{bars}</div>
            </div>'''

        # Headline stats (visible to all claimed-tool makers)
        _total_recs = sum(a['count'] for a in agents) if agents else 0
        _headline_html = ''
        if _total_recs > 0 or maker_success_rate is not None:
            _sr_display = f'{maker_success_rate}%' if maker_success_rate is not None else '—'
            _headline_html = f'''
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:24px;">
                <div class="card" style="padding:20px;text-align:center;">
                    <p style="font-size:28px;font-weight:700;color:var(--accent);">{_total_recs}</p>
                    <p style="font-size:13px;color:var(--ink-muted);">AI Recommendations (30d)</p>
                </div>
                <div class="card" style="padding:20px;text-align:center;">
                    <p style="font-size:28px;font-weight:700;color:var(--ink);">{_sr_display}</p>
                    <p style="font-size:13px;color:var(--ink-muted);">Agent Success Rate</p>
                </div>
            </div>'''

        if queries or agents:
            # Pre-compute agent card content to avoid nested f-string quote conflicts
            if agents or trend:
                _agent_card_content = f"{agent_rows}{trend_html}"
            else:
                _agent_card_content = '<p style="color:var(--ink-muted);font-size:13px;">No citations yet. As agents recommend your tools, sources will appear here.</p>'

            ai_intel_html = f'''
            <div id="ai-distribution" style="margin-top:32px;">
                <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z"/><circle cx="12" cy="14" r="2"/></svg> AI Distribution Intelligence <span style="font-size:13px;color:var(--ink-muted);font-weight:400;">(last 30 days)</span>
                </h2>
                {_headline_html}
                <style>.ai-intel-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:24px}}@media(max-width:600px){{.ai-intel-grid{{grid-template-columns:1fr}}}}</style>
                <div class="ai-intel-grid">
                    <div class="card">
                        <h3 style="font-size:15px;color:var(--ink);margin-bottom:12px;">Queries Finding Your Tools</h3>
                        <p style="font-size:12px;color:var(--ink-muted);margin-bottom:12px;">What people search for when they discover your creations.</p>
                        {f"""<table style="width:100%;border-collapse:collapse;font-size:14px;">
                            <thead><tr style="border-bottom:1px solid var(--border);">
                                <th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;color:var(--ink-muted);">Query</th>
                                <th style="padding:8px 12px;text-align:center;font-size:11px;text-transform:uppercase;color:var(--ink-muted);">Count</th>
                                <th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;color:var(--ink-muted);">Tool</th>
                            </tr></thead>
                            <tbody>{query_rows}</tbody>
                        </table>""" if queries else '<p style="color:var(--ink-muted);font-size:13px;">No search data yet. Queries will appear here as AI agents discover your tools.</p>'}
                    </div>
                    <div class="card">
                        <h3 style="font-size:15px;color:var(--ink);margin-bottom:12px;">Recommendation Sources</h3>
                        <p style="font-size:12px;color:var(--ink-muted);margin-bottom:12px;">Which AI agents and channels recommend your creations.</p>
                        {_agent_card_content}
                    </div>
                </div>
            </div>'''
        elif _headline_html:
            # Has claimed tools but no query/agent detail yet
            ai_intel_html = f'''
            <div id="ai-distribution" style="margin-top:32px;">
                <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z"/><circle cx="12" cy="14" r="2"/></svg> AI Distribution Intelligence <span style="font-size:13px;color:var(--ink-muted);font-weight:400;">(last 30 days)</span>
                </h2>
                {_headline_html}
                <p style="color:var(--ink-muted);font-size:13px;">As agents recommend your tools more, detailed breakdowns will appear here.</p>
            </div>'''
    # Branch C (implicit): no maker_id — ai_intel_html stays empty string

    # Buyer badge embed section
    buyer_badge_html = ''
    if user_tokens and user_tokens > 0:
        badge_token = await get_or_create_badge_token(db, user['id'])
        badge_url = f"{BASE_URL}/api/badge/buyer/{badge_token}.svg"
        buyer_badge_html = f'''
        <div class="card" style="padding:24px;margin-top:24px;">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M12 2H2v10l9.29 9.29c.94.94 2.48.94 3.42 0l6.58-6.58c.94-.94.94-2.48 0-3.42L12 2Z"/><path d="M7 7h.01"/></svg> Your Tokens Saved Badge
            </h3>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                Show off your indie stack! Embed this badge in your README or website.
            </p>
            <div style="text-align:center;padding:16px;background:var(--cream-dark);border-radius:var(--radius);margin-bottom:16px;">
                <img src="{badge_url}" alt="Built with IndieStack badge" style="height:20px;">
            </div>
            <div style="margin-bottom:12px;">
                <label style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Markdown</label>
                <div style="position:relative;margin-top:4px;">
                    <pre style="background:rgba(0,0,0,0.3);color:var(--ink-light);padding:16px;border-radius:var(--radius-sm);font-size:13px;
                        font-family:var(--font-mono);overflow-x:auto;white-space:pre-wrap;word-break:break-all;border:1px solid rgba(255,255,255,0.1);"><code>[![Built with IndieStack]({badge_url})]({BASE_URL})</code></pre>
                    <button onclick="navigator.clipboard.writeText(this.dataset.code);this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',1500)"
                        data-code="[![Built with IndieStack]({badge_url})]({BASE_URL})"
                        style="position:absolute;top:8px;right:8px;background:rgba(255,255,255,0.1);color:var(--ink-light);border:1px solid rgba(255,255,255,0.1);
                            padding:4px 12px;border-radius:var(--radius-sm);font-size:11px;font-weight:600;cursor:pointer;">Copy</button>
                </div>
            </div>
            <div>
                <label style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">HTML</label>
                <div style="position:relative;margin-top:4px;">
                    <pre style="background:rgba(0,0,0,0.3);color:var(--ink-light);padding:16px;border-radius:var(--radius-sm);font-size:13px;
                        font-family:var(--font-mono);overflow-x:auto;white-space:pre-wrap;word-break:break-all;border:1px solid rgba(255,255,255,0.1);"><code>&lt;a href="{BASE_URL}"&gt;&lt;img src="{badge_url}" alt="Built with IndieStack"&gt;&lt;/a&gt;</code></pre>
                    <button onclick="navigator.clipboard.writeText(this.dataset.code);this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',1500)"
                        data-code='<a href="{BASE_URL}"><img src="{badge_url}" alt="Built with IndieStack"></a>'
                        style="position:absolute;top:8px;right:8px;background:rgba(255,255,255,0.1);color:var(--ink-light);border:1px solid rgba(255,255,255,0.1);
                            padding:4px 12px;border-radius:var(--radius-sm);font-size:11px;font-weight:600;cursor:pointer;">Copy</button>
                </div>
            </div>
        </div>
        '''

    # Launch Readiness (makers only)
    readiness_html = ''
    if user.get('maker_id'):
        readiness = await get_launch_readiness(db, user['maker_id'])
        readiness_html = launch_readiness_bar(readiness)

    # Milestone celebrations
    milestone_html = ''
    if user.get('maker_id') and user.get('id'):
        # Check for new milestones
        maker_tools = await get_tools_by_maker(db, user['maker_id'])
        for t in maker_tools:
            await check_milestones(db, user['id'], t['id'])
        # Show unshared milestones
        unshared = await get_unshared_milestones(db, user['id'])
        if unshared:
            cards = ''
            for ms in unshared[:3]:  # Show max 3
                ms_type = ms.get('milestone_type', '')
                ms_info = MILESTONE_THRESHOLDS.get(ms_type, {})
                emoji = ms_info.get('emoji', '&#127881;')
                desc = ms_info.get('description', 'Achievement unlocked!')
                tool_name = ms.get('tool_name', '')
                tool_slug = ms.get('tool_slug', '')
                share_text = f"{emoji} {desc} on IndieStack!"
                share_url = f"{BASE_URL}/api/milestone/{tool_slug}.svg?type={ms_type}" if tool_slug else ""
                tweet_url = f"https://twitter.com/intent/tweet?text={share_text}&url={BASE_URL}/tool/{tool_slug}" if tool_slug else ""

                cards += f"""
                <div style="background:linear-gradient(135deg,#1A2D4A,var(--terracotta-dark));border-radius:var(--radius);padding:20px 24px;
                            display:flex;align-items:center;gap:16px;margin-bottom:8px;">
                    <span style="font-size:36px;">{emoji}</span>
                    <div style="flex:1;">
                        <div style="color:#fff;font-weight:600;font-size:16px;">{desc}</div>
                        <div style="color:rgba(255,255,255,0.6);font-size:13px;">{tool_name}</div>
                    </div>
                    <a href="{tweet_url}" target="_blank" rel="noopener"
                       style="background:var(--slate);color:var(--terracotta);padding:8px 16px;border-radius:999px;
                              text-decoration:none;font-size:13px;font-weight:700;white-space:nowrap;">
                        Share on &#120143; &rarr;
                    </a>
                </div>"""

            milestone_html = f"""
            <div style="margin-bottom:24px;">
                <h3 style="font-family:var(--font-display);font-size:18px;color:var(--terracotta);margin-bottom:12px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26z"/></svg> New Achievements
                </h3>
                {cards}
            </div>"""

    # Boost performance report
    boost_report_html = ''
    if user.get('maker_id'):
        maker_tools_for_boost = await get_tools_by_maker(db, user['maker_id'])
        for bt in maker_tools_for_boost:
            if bt.get('is_boosted') or bt.get('boost_expires_at'):
                # Get stats for the boost period
                boost_start = bt.get('boost_expires_at', '')
                # Calculate views during boost period from tool_views table
                views_cursor = await db.execute(
                    "SELECT COUNT(*) as cnt FROM tool_views WHERE tool_id = ? AND viewed_at > datetime(?, '-30 days')",
                    (bt['id'], boost_start or 'now'))
                views_row = await views_cursor.fetchone()
                boost_views = views_row['cnt'] if views_row else 0

                # Get total upvotes
                upvotes = bt.get('upvote_count', 0)

                # Get wishlist count
                wl_cursor = await db.execute(
                    "SELECT COUNT(*) as cnt FROM wishlists WHERE tool_id = ?", (bt['id'],))
                wl_row = await wl_cursor.fetchone()
                wishlists = wl_row['cnt'] if wl_row else 0

                # Determine if boost is active or expired
                from datetime import datetime
                is_active = False
                days_left = 0
                expires_str = ''
                if bt.get('boost_expires_at'):
                    try:
                        exp = datetime.fromisoformat(bt['boost_expires_at'])
                        is_active = exp > datetime.utcnow()
                        days_left = max(0, (exp - datetime.utcnow()).days)
                        expires_str = exp.strftime('%d %b %Y')
                    except Exception:
                        pass

                status_badge = (
                    f'<span style="background:#10B981;color:#fff;padding:4px 12px;border-radius:999px;font-size:12px;font-weight:600;">Active &mdash; {days_left} days left</span>'
                    if is_active
                    else f'<span style="background:var(--ink-muted);color:#fff;padding:4px 12px;border-radius:999px;font-size:12px;font-weight:600;">Ended {expires_str}</span>'
                )

                # Get outbound clicks during boost period
                from indiestack.db import get_outbound_click_count
                boost_clicks = await get_outbound_click_count(db, bt['id'], days=30)

                view_listing_btn = ''
                if not is_active:
                    view_listing_btn = '<div style="text-align:center;margin-top:16px;"><a href="/tool/' + escape(str(bt['slug'])) + '" style="background:var(--slate);color:var(--terracotta);padding:10px 24px;border-radius:999px;font-weight:700;text-decoration:none;font-size:14px;">View Your Listing</a></div>'

                boost_report_html += f"""
                <div style="background:linear-gradient(135deg,#1A2D4A,var(--terracotta-dark));border-radius:var(--radius);padding:24px;margin-bottom:24px;color:#fff;">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
                        <h3 style="font-family:var(--font-display);font-size:20px;margin:0;color:#fff;">
                            &#9733; Boost Report &mdash; {escape(str(bt['name']))}
                        </h3>
                        {status_badge}
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
                        <div style="text-align:center;padding:16px;background:rgba(255,255,255,0.1);border-radius:var(--radius);">
                            <div style="font-size:28px;font-weight:800;color:var(--slate);">{boost_views}</div>
                            <div style="font-size:12px;color:rgba(255,255,255,0.7);margin-top:4px;">Profile Views</div>
                        </div>
                        <div style="text-align:center;padding:16px;background:rgba(255,255,255,0.1);border-radius:var(--radius);">
                            <div style="font-size:28px;font-weight:800;color:var(--slate);">{boost_clicks}</div>
                            <div style="font-size:12px;color:rgba(255,255,255,0.7);margin-top:4px;">Outbound Clicks</div>
                        </div>
                        <div style="text-align:center;padding:16px;background:rgba(255,255,255,0.1);border-radius:var(--radius);">
                            <div style="font-size:28px;font-weight:800;color:var(--slate);">{upvotes}</div>
                            <div style="font-size:12px;color:rgba(255,255,255,0.7);margin-top:4px;">Upvotes</div>
                        </div>
                        <div style="text-align:center;padding:16px;background:rgba(255,255,255,0.1);border-radius:var(--radius);">
                            <div style="font-size:28px;font-weight:800;color:var(--slate);">{wishlists}</div>
                            <div style="font-size:12px;color:rgba(255,255,255,0.7);margin-top:4px;">Bookmarks</div>
                        </div>
                    </div>
                    <div style="font-size:13px;color:rgba(255,255,255,0.6);line-height:1.6;">
                        &#9733; Featured badge shown on your listing and in search results<br>
                        &#9733; Priority placement in category and explore pages<br>
                        &#9733; Featured in weekly newsletter sent to all subscribers
                    </div>
                    {view_listing_btn}
                </div>"""

    # Search intent analytics
    search_intent_html = ''
    if user.get('maker_id'):
        maker_tools_for_search = await get_tools_by_maker(db, user['maker_id'])
        all_terms = []
        for t in maker_tools_for_search:
            terms = await get_search_terms_for_tool(db, t['slug'])
            for term in terms:
                all_terms.append({**dict(term), 'tool_name': t['name']})
        if all_terms:
            all_terms.sort(key=lambda x: x.get('count', 0), reverse=True)
            search_rows = ''
            for term in all_terms[:10]:
                search_rows += f"""<tr>
                    <td style="padding:8px 12px;border-bottom:1px solid var(--border);font-weight:500;color:var(--ink);">"{escape(str(term['query']))}"</td>
                    <td style="padding:8px 12px;border-bottom:1px solid var(--border);color:var(--ink-light);">{escape(str(term['tool_name']))}</td>
                    <td style="padding:8px 12px;border-bottom:1px solid var(--border);text-align:center;color:var(--ink-light);">{term['count']}</td>
                </tr>"""
            search_intent_html = f"""
            <div style="background:var(--card-bg);border-radius:var(--radius);padding:24px;border:1px solid var(--border);margin-bottom:24px;">
                <h3 style="font-family:var(--font-display);font-size:18px;color:var(--terracotta);margin-bottom:16px;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg> How Developers Find Your Tools
                </h3>
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="border-bottom:2px solid var(--border);">
                            <th style="padding:8px 12px;text-align:left;font-size:13px;color:var(--ink-muted);">Search Query</th>
                            <th style="padding:8px 12px;text-align:left;font-size:13px;color:var(--ink-muted);">Matched Tool</th>
                            <th style="padding:8px 12px;text-align:center;font-size:13px;color:var(--ink-muted);">Times</th>
                        </tr>
                    </thead>
                    <tbody>{search_rows}</tbody>
                </table>
            </div>"""

    # Maker Matchmaker widget
    matchmaker_html = ''
    if user.get('maker_id'):
        similar_makers = await get_similar_makers(db, user['maker_id'])
        if similar_makers:
            maker_cards = ''
            for sm in similar_makers:
                sm_name = escape(str(sm['name']))
                sm_slug = escape(str(sm['slug']))
                sm_bio = escape(str(sm.get('bio', '') or '')[:80])
                sm_tool = escape(str(sm.get('tool_name', '')))
                indie = sm.get('indie_status', '')
                indie_label = 'Solo Maker' if indie == 'solo' else 'Small Team' if indie == 'small_team' else ''
                indie_pill = f'<span style="font-size:11px;padding:2px 8px;border-radius:999px;background:#EDE9FE;color:#7C3AED;">{indie_label}</span>' if indie_label else ''

                maker_cards += f"""
                <a href="/maker/{sm_slug}" class="hover-lift" style="text-decoration:none;color:inherit;display:block;padding:16px;
                    background:var(--cream-dark);border-radius:var(--radius);">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                        <span style="font-weight:700;color:var(--ink);">{sm_name}</span>
                        {indie_pill}
                    </div>
                    <div style="font-size:13px;color:var(--ink-muted);margin-bottom:4px;">Building {sm_tool}</div>
                    <div style="font-size:12px;color:var(--ink-light);">{sm_bio}{'...' if len(sm.get('bio', '') or '') > 80 else ''}</div>
                </a>"""

            matchmaker_html = f"""
            <div style="background:var(--card-bg);border-radius:var(--radius);padding:24px;border:1px solid var(--border);margin-bottom:24px;">
                <h3 style="font-family:var(--font-display);font-size:18px;color:var(--terracotta);margin-bottom:16px;">
                    Makers Like You
                </h3>
                <div style="display:grid;gap:12px;">{maker_cards}</div>
                <a href="/makers" style="display:block;text-align:center;margin-top:16px;font-size:13px;color:var(--slate);font-weight:600;text-decoration:none;">
                    Browse all makers &rarr;
                </a>
            </div>"""

    # ── Referral Programme ─────────────────────────────────────────
    referral_code = await ensure_referral_code(db, user['id'])
    referral_link = f"{BASE_URL}/signup?ref={referral_code}"
    referral_count = await get_referral_count(db, user['id'])
    boost_days = user.get('referral_boost_days', 0) or 0

    # Claim boost form (only show if user has boost days AND has tools)
    claim_form_html = ''
    if boost_days > 0 and user.get('maker_id'):
        maker_tools_ref = await get_tools_by_maker(db, user['maker_id'])
        if maker_tools_ref:
            options_ref = ''.join(f'<option value="{t["id"]}">{escape(str(t["name"]))}</option>' for t in maker_tools_ref)
            claim_form_html = f'''
            <form method="POST" action="/dashboard/claim-referral-boost" style="margin-top:16px;display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                <select name="tool_id" style="padding:8px 12px;border-radius:var(--radius-sm);border:1px solid var(--border);font-size:14px;">
                    {options_ref}
                </select>
                <button type="submit" style="background:var(--slate);color:var(--terracotta);border:none;padding:8px 20px;border-radius:var(--radius-sm);font-weight:700;font-size:14px;cursor:pointer;">
                    Apply {boost_days} Boost Days
                </button>
            </form>'''

    referral_html = f'''
    <div style="margin-top:32px;">
        <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><polyline points="20 12 20 22 4 22 4 12"/><rect x="2" y="7" width="20" height="5"/><line x1="12" y1="22" x2="12" y2="7"/><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"/><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"/></svg> Referral Programme
        </h2>
        <div class="card">
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                Share your link. When someone signs up and gets a tool approved, you earn <strong>10 free boost days</strong>.
            </p>
            <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;">
                <input type="text" readonly value="{referral_link}" id="ref-link"
                    style="flex:1;min-width:200px;padding:10px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);
                           font-size:13px;font-family:var(--font-mono);background:var(--cream-dark);color:var(--ink);" />
                <button onclick="navigator.clipboard.writeText(document.getElementById('ref-link').value);this.textContent='Copied!';setTimeout(()=>this.textContent='Copy Link',1500)"
                    style="background:var(--terracotta);color:#fff;border:none;padding:10px 20px;border-radius:var(--radius-sm);font-weight:700;font-size:13px;cursor:pointer;">
                    Copy Link
                </button>
            </div>
            <div style="display:flex;gap:24px;margin-top:20px;">
                <div style="text-align:center;padding:12px 16px;background:var(--cream-dark);border-radius:var(--radius-sm);flex:1;">
                    <div style="font-size:24px;font-weight:800;color:var(--ink);">{referral_count}</div>
                    <div style="font-size:12px;color:var(--ink-muted);">Referrals</div>
                </div>
                <div style="text-align:center;padding:12px 16px;background:var(--cream-dark);border-radius:var(--radius-sm);flex:1;">
                    <div style="font-size:24px;font-weight:800;color:var(--slate);">{boost_days}</div>
                    <div style="font-size:12px;color:var(--ink-muted);">Boost Days Earned</div>
                </div>
            </div>
            {claim_form_html}
        </div>
    </div>
    '''

    # ── Welcome perk banner (Perplexity Comet) ──────────────────────
    welcome_perk = '''<div id="comet-banner" style="display:none;background:linear-gradient(135deg,#1A2D4A,var(--terracotta-dark));border:1px solid rgba(0,212,245,0.3);border-radius:var(--radius);padding:16px 20px;margin-bottom:16px;position:relative;">
        <button onclick="localStorage.setItem('comet_dismissed','1');document.getElementById('comet-banner').remove();"
                style="position:absolute;top:10px;right:12px;background:none;border:none;color:var(--ink-muted);font-size:18px;cursor:pointer;line-height:1;">&times;</button>
        <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap;">
            <div style="flex:1;min-width:200px;">
                <div style="font-family:var(--font-display);font-size:16px;color:white;margin-bottom:4px;">
                    Welcome to IndieStack <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-left:4px;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
                </div>
                <p style="font-size:13px;color:var(--ink-muted);margin:0;line-height:1.5;">
                    As a thank you for joining, here&rsquo;s free access to <strong style="color:var(--slate);">Perplexity Comet</strong> &mdash; an AI-powered browser built for students and builders.
                </p>
            </div>
            <a href="https://pplx.ai/patrick-amey" target="_blank" rel="noopener"
               style="display:inline-block;padding:8px 20px;background:var(--slate);color:var(--terracotta);font-size:13px;font-weight:700;
                      border-radius:var(--radius-sm);text-decoration:none;white-space:nowrap;">
                Get Comet Free &rarr;
            </a>
        </div>
    </div>
    <script>if(!localStorage.getItem('comet_dismissed')){document.getElementById('comet-banner').style.display='block';}</script>'''

    # ── API key section for dashboard ────────────────────────────
    user_keys = await get_api_keys_for_user(db, user['id'])
    active_keys = [k for k in user_keys if k['is_active']]
    _usage = await get_api_key_usage_stats(db, user['id'], days=30)
    _usage_map = {u['id']: u['request_count'] for u in _usage}

    if not active_keys:
        api_key_html = '''
        <div class="card" style="padding:24px;margin-bottom:24px;border:1px solid var(--accent);">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
                <div>
                    <h3 style="margin:0 0 4px;font-family:var(--font-display);font-size:18px;">API Key</h3>
                    <p style="margin:0;font-size:13px;color:var(--ink-muted);">Unlock personalized recommendations and migration intelligence.</p>
                </div>
                <form method="POST" action="/developer/create-key">
                    <input type="hidden" name="name" value="Default">
                    <input type="hidden" name="redirect" value="/dashboard">
                    <button type="submit" class="btn btn-primary" style="font-size:13px;padding:10px 20px;">Create Free Key</button>
                </form>
            </div>
        </div>'''
    else:
        _k = active_keys[0]
        _k_count = _usage_map.get(_k['id'], 0)
        _k_last = _k['last_used_at'][:10] if _k.get('last_used_at') else 'Never'
        api_key_html = f'''
        <div class="card" style="padding:24px;margin-bottom:24px;">
            <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;margin-bottom:12px;">
                <h3 style="margin:0;font-family:var(--font-display);font-size:18px;">API Key</h3>
                <span style="font-size:13px;color:var(--ink-muted);">{_k_count} requests this month</span>
            </div>
            <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
                <code style="font-family:var(--font-mono);font-size:13px;background:var(--cream-dark);padding:8px 14px;border-radius:var(--radius-sm);color:var(--ink);">{escape(_k["key_preview"])}</code>
                <span style="font-size:12px;color:var(--ink-muted);">Last used: {_k_last}</span>
            </div>
        </div>'''

    # Show new key banner if just created
    _new_key_param = request.query_params.get("new", "")
    _new_key_banner = ''
    if _new_key_param and _new_key_param.startswith("isk_"):
        _new_key_banner = f'''
        <div class="card" style="border-left:4px solid var(--success-text);margin-bottom:24px;padding:20px;">
            <h3 style="margin:0 0 8px;font-family:var(--font-display);font-size:18px;color:var(--ink);">Key Created</h3>
            <p style="color:var(--ink-muted);font-size:14px;margin:0 0 12px;">Copy this key now — you won't be able to see it again.</p>
            <code id="dash-new-key" style="font-family:var(--font-mono);font-size:14px;background:var(--cream-dark);
                         color:var(--ink);padding:10px 14px;border-radius:var(--radius-sm);display:block;
                         word-break:break-all;">{escape(_new_key_param)}</code>
            <button onclick="navigator.clipboard.writeText(document.getElementById('dash-new-key').textContent);this.textContent='Copied!'"
                    class="btn btn-primary" style="margin-top:12px;font-size:13px;">Copy to Clipboard</button>
        </div>'''

    # api_nudge removed — api_key_html card handles this now

    stripe_launch_banner = ''

    # ── Email verification banner ──────────────────────────────────
    verify_banner = ''
    if not user.get('email_verified'):
        verify_banner = '''<div style="background:#FEF3C7;border:1px solid #FCD34D;border-radius:var(--radius-sm);padding:12px 16px;margin-bottom:16px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
            <span style="color:var(--warning-text);font-size:14px;font-weight:600;">Please verify your email to unlock all features.</span>
            <a href="/resend-verification" style="background:#D97706;color:white;padding:6px 16px;border-radius:var(--radius-sm);font-size:13px;font-weight:600;text-decoration:none;">Resend Verification Email</a>
        </div>'''

    # ── Boost success banner ──────────────────────────────────────
    boosted_param = request.query_params.get('boosted', '')
    boost_success_banner = ''
    if boosted_param == '1':
        boost_success_banner = '<div style="background:#ECFDF5;border:1px solid #6EE7B7;border-radius:var(--radius-sm);padding:12px 16px;margin-bottom:16px;color:#065F46;font-weight:600;font-size:14px;">Referral boost applied! Your tool is now featured.</div>'

    # ── Avatar saved banner ───────────────────────────────────────
    avatar_saved_param = request.query_params.get('avatar', '')
    avatar_saved_banner = ''
    if avatar_saved_param == 'saved':
        avatar_saved_banner = '<div style="background:#ECFDF5;border:1px solid #6EE7B7;border-radius:var(--radius-sm);padding:12px 16px;margin-bottom:16px;color:#065F46;font-weight:600;font-size:14px;">Pixel avatar saved! It\'ll be visible to others once we\'ve reviewed it.</div>'

    # ── Pixel Avatar Editor ───────────────────────────────────────
    existing_avatar = escape(str(user.get('pixel_avatar', '') or ''))
    current_avatar_preview = ''
    raw_pixel = str(user.get('pixel_avatar', '') or '')
    if raw_pixel and len(raw_pixel) == 49:
        approved = bool(user.get('pixel_avatar_approved', 0))
        status_badge = '<span class="badge badge-success">Approved</span>' if approved else '<span class="badge badge-warning">Pending review</span>'
        current_avatar_preview = f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">{pixel_icon_svg(raw_pixel, size=48)} <div><p style="font-size:13px;font-weight:600;color:var(--ink);">Current avatar</p>{status_badge}</div></div>'

    avatar_editor_html = f'''
    <div class="card" style="padding:20px;margin-top:24px;margin-bottom:24px;">
        <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:12px;">Your Pixel Avatar</h3>
        {current_avatar_preview}
        <form method="POST" action="/dashboard/avatar">
            <div style="display:flex;gap:20px;align-items:flex-start;flex-wrap:wrap;">
                <div>
                    <div id="avatar-grid" style="display:grid;grid-template-columns:repeat(7,28px);grid-template-rows:repeat(7,28px);gap:1px;background:var(--border);border:1px solid var(--border);border-radius:4px;cursor:crosshair;"></div>
                    <div id="avatar-palette" style="display:flex;gap:4px;margin-top:8px;"></div>
                </div>
                <div>
                    <p style="font-size:12px;color:var(--ink-muted);margin-bottom:4px;">Preview</p>
                    <div id="avatar-preview" style="border:1px solid var(--border);border-radius:4px;"></div>
                </div>
            </div>
            <input type="hidden" id="pixel_avatar" name="pixel_avatar" value="{existing_avatar}">
            <div style="display:flex;gap:8px;margin-top:12px;">
                <button type="button" onclick="clearAvatarGrid()" style="font-size:12px;color:var(--ink-muted);background:none;border:1px solid var(--border);border-radius:4px;padding:6px 14px;cursor:pointer;">Clear</button>
                <button type="submit" class="btn btn-primary" style="font-size:13px;padding:6px 20px;">Save Avatar</button>
            </div>
        </form>
        <script>
        (function(){{
            var COLORS = ['transparent','#1A2D4A','#00D4F5','#E2B764','#FFFFFF','#64748B','#E07A5F','#22C55E','#000000','#EF4444','#EC4899','#8B5CF6','#F97316','#7DD3FC','#86EFAC','#92400E'];
            var LABELS = ['Erase','Navy','Cyan','Gold','White','Slate','Terracotta','Green','Black','Red','Pink','Purple','Orange','Light Blue','Light Green','Brown'];
            var grid = document.getElementById('avatar-grid');
            var palette = document.getElementById('avatar-palette');
            var input = document.getElementById('pixel_avatar');
            var preview = document.getElementById('avatar-preview');
            var activeColor = '1';
            var cells = [];
            var data = (input.value || '').padEnd(49, '0').split('');

            COLORS.forEach(function(c, i) {{
                var sw = document.createElement('div');
                sw.title = LABELS[i];
                sw.style.cssText = 'width:22px;height:22px;border-radius:4px;cursor:pointer;border:2px solid ' + (i.toString(16) === activeColor ? 'var(--accent)' : 'var(--border)') + ';background:' + (c === 'transparent' ? 'repeating-conic-gradient(#ccc 0% 25%, #fff 0% 50%) 50% / 12px 12px' : c) + ';';
                sw.onclick = function() {{
                    activeColor = i.toString(16);
                    palette.querySelectorAll('div').forEach(function(s, j) {{
                        s.style.borderColor = j === i ? 'var(--accent)' : 'var(--border)';
                    }});
                }};
                palette.appendChild(sw);
            }});

            var isMouseDown = false;
            grid.onmousedown = function() {{ isMouseDown = true; }};
            document.addEventListener('mouseup', function() {{ isMouseDown = false; }});
            for (var i = 0; i < 49; i++) {{
                (function(idx) {{
                    var cell = document.createElement('div');
                    cell.style.cssText = 'background:' + (data[idx] === '0' ? 'var(--card-bg)' : COLORS[parseInt(data[idx],16)]) + ';';
                    cell.onmousedown = function(e) {{ e.preventDefault(); paintAvatar(idx); }};
                    cell.onmouseenter = function() {{ if (isMouseDown) paintAvatar(idx); }};
                    grid.appendChild(cell);
                    cells.push(cell);
                }})(i);
            }}

            function paintAvatar(idx) {{
                data[idx] = activeColor;
                cells[idx].style.background = activeColor === '0' ? 'var(--card-bg)' : COLORS[parseInt(activeColor,16)];
                syncAvatar();
            }}

            function syncAvatar() {{
                input.value = data.join('');
                var svg = '<svg width="24" height="24" viewBox="0 0 7 7" style="image-rendering:pixelated;">';
                for (var i = 0; i < 49; i++) {{
                    if (data[i] !== '0' && COLORS[parseInt(data[i],16)]) {{
                        var x = i % 7, y = Math.floor(i / 7);
                        svg += '<rect x="'+x+'" y="'+y+'" width="1" height="1" fill="'+COLORS[parseInt(data[i],16)]+'"/>';
                    }}
                }}
                svg += '</svg>';
                preview.innerHTML = svg;
            }}

            window.clearAvatarGrid = function() {{
                data = Array(49).fill('0');
                cells.forEach(function(c) {{ c.style.background = 'var(--card-bg)'; }});
                syncAvatar();
            }};

            syncAvatar();
        }})();
        </script>
    </div>
    '''

    # ── AI Visibility Card ─────────────────────────────────────
    ai_visibility_card = ''
    if maker_id:
        top_5_queries = await get_maker_query_intelligence(db, maker_id, days=30)
        top_5_queries = top_5_queries[:5]

        # Percentile display
        if citation_percentile and citation_percentile.get('percentile') is not None:
            pct_val = 100 - citation_percentile['percentile']
            pct_display = f'Top {pct_val}%'
            pct_style = 'font-family:var(--font-display);font-size:28px;color:var(--ink);'
        else:
            pct_display = 'No data yet'
            pct_style = 'font-size:14px;color:var(--ink-muted);'

        # Query list
        query_items = ''
        if top_5_queries:
            for q in top_5_queries:
                query_items += f'''<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border);">
                    <span style="font-family:var(--font-mono);font-size:13px;color:var(--ink);">{escape(q['query'])}</span>
                    <span style="background:var(--cream-dark);padding:2px 8px;border-radius:999px;font-size:12px;font-weight:600;color:var(--ink);flex-shrink:0;margin-left:12px;">{q['count']}</span>
                </div>'''
        else:
            query_items = '<p style="color:var(--ink-muted);font-size:13px;">No search queries yet</p>'

        query_count = len(top_5_queries)

        ai_visibility_card = f'''
        <style>.ai-viz-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:16px;text-align:center;}}@media(max-width:600px){{.ai-viz-grid{{grid-template-columns:1fr;}}}}</style>
        <div class="card" style="padding:24px;margin-bottom:24px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin:0;">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-3px;margin-right:6px;"><circle cx="12" cy="12" r="2"/><path d="M16.24 7.76a6 6 0 0 1 0 8.49m-8.48-.01a6 6 0 0 1 0-8.49m11.31-2.82a10 10 0 0 1 0 14.14m-14.14 0a10 10 0 0 1 0-14.14"/></svg>
                    AI Visibility
                </h3>
                <span style="font-size:12px;color:var(--ink-muted);">(30 days)</span>
            </div>
            <div class="ai-viz-grid">
                <div>
                    <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{agent_citations_30d}</div>
                    <div style="font-size:12px;color:var(--ink-muted);margin-top:4px;">Agent Citations</div>
                </div>
                <div>
                    <div style="{pct_style}">{pct_display}</div>
                    <div style="font-size:12px;color:var(--ink-muted);margin-top:4px;">Category Rank</div>
                </div>
                <div>
                    <div style="font-family:var(--font-display);font-size:28px;color:var(--ink);">{query_count}</div>
                    <div style="font-size:12px;color:var(--ink-muted);margin-top:4px;">Discovery Queries</div>
                </div>
                <div>
                    <div style="font-family:var(--font-display);font-size:28px;color:{sr_color};">{sr_display}</div>
                    <div style="font-size:12px;color:var(--ink-muted);margin-top:4px;">Success Rate</div>
                </div>
            </div>
            <div style="margin-top:4px;">
                <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:var(--ink-muted);margin-bottom:8px;font-weight:600;">Top Search Queries</div>
                {query_items}
            </div>
        </div>
        '''

    # Build header based on Pro status
    _tokens_display = '~' + str(tokens_k) + 'k' if tokens_k > 0 else '0'
    _user_name = escape(str(user['name']))
    if is_pro:
        plan_label = 'Pro'
        if plan_label == 'Founder':
            plan_label = 'Founding Member'
        header_html = f'''
        <style>@media(max-width:600px){{.pro-stats-grid{{grid-template-columns:repeat(2,1fr) !important;}}}}</style>
        <div style="background:linear-gradient(135deg,#1A2D4A 0%,#243B5E 100%);border-radius:var(--radius);padding:32px;margin-bottom:24px;">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:24px;">
                <div>
                    <h1 style="font-family:var(--font-display);font-size:32px;color:white;margin:0 0 4px;">
                        Dashboard
                        <span style="display:inline-block;background:var(--accent);color:#0F1D30;font-size:11px;font-weight:700;padding:3px 10px;border-radius:999px;vertical-align:middle;margin-left:8px;">PRO</span>
                    </h1>
                    <p style="color:rgba(255,255,255,0.6);margin:0;font-size:15px;">Welcome back, {_user_name}</p>
                </div>
                <span style="font-size:13px;color:rgba(255,255,255,0.4);">{plan_label}</span>
            </div>
            <div class="pro-stats-grid" style="display:grid;grid-template-columns:repeat(5,1fr);gap:12px;">
                <div style="text-align:center;padding:16px;background:rgba(255,255,255,0.07);border-radius:var(--radius-sm);">
                    <div style="font-family:var(--font-display);font-size:28px;color:white;">{tool_count}</div>
                    <div style="font-size:12px;color:rgba(255,255,255,0.5);margin-top:4px;">Tools</div>
                </div>
                <div style="text-align:center;padding:16px;background:rgba(255,255,255,0.07);border-radius:var(--radius-sm);">
                    <div style="font-family:var(--font-display);font-size:28px;color:white;">{total_upvotes}</div>
                    <div style="font-size:12px;color:rgba(255,255,255,0.5);margin-top:4px;">Upvotes</div>
                </div>
                <div style="text-align:center;padding:16px;background:rgba(255,255,255,0.07);border-radius:var(--radius-sm);">
                    <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{agent_citations_30d}</div>
                    <div style="font-size:12px;color:rgba(255,255,255,0.5);margin-top:4px;">Agent Citations</div>
                </div>
                <div style="text-align:center;padding:16px;background:rgba(255,255,255,0.07);border-radius:var(--radius-sm);">
                    <div style="font-family:var(--font-display);font-size:28px;color:white;">{_tokens_display}</div>
                    <div style="font-size:12px;color:rgba(255,255,255,0.5);margin-top:4px;">Tokens Saved</div>
                </div>
                <div style="text-align:center;padding:16px;background:rgba(255,255,255,0.07);border-radius:var(--radius-sm);">
                    <div style="font-family:var(--font-display);font-size:28px;color:{sr_color};">{sr_display}</div>
                    <div style="font-size:12px;color:rgba(255,255,255,0.5);margin-top:4px;">Success Rate</div>
                </div>
            </div>
        </div>
        '''
    else:
        header_html = f'''
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
            <div>
                <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Dashboard</h1>
                <p style="color:var(--ink-muted);margin-top:4px;">Welcome back, {_user_name}</p>
            </div>
            {upgrade_html}
        </div>
        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:24px;">
            <div class="card" style="text-align:center;padding:20px;">
                <div style="color:var(--ink-muted);font-size:13px;">Tools</div>
                <div style="font-family:var(--font-display);font-size:28px;margin-top:4px;color:var(--ink);">{tool_count}</div>
            </div>
            <div class="card" style="text-align:center;padding:20px;">
                <div style="color:var(--ink-muted);font-size:13px;">Upvotes</div>
                <div style="font-family:var(--font-display);font-size:28px;margin-top:4px;color:var(--slate-dark);">{total_upvotes}</div>
            </div>
            <div class="card" style="text-align:center;padding:20px;">
                <div style="color:var(--ink-muted);font-size:13px;">Tokens Saved</div>
                <div style="font-family:var(--font-display);font-size:28px;margin-top:4px;color:var(--slate-dark);">{_tokens_display}</div>
            </div>
            <div class="card" style="text-align:center;padding:20px;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{agent_citations_30d}</div>
                <div style="font-size:13px;color:var(--ink-muted);margin-top:4px;">Agent Recs</div>
            </div>
            <div class="card" style="text-align:center;padding:20px;">
                <div style="font-family:var(--font-display);font-size:28px;color:{sr_color};">{sr_display}</div>
                <div style="font-size:13px;color:var(--ink-muted);margin-top:4px;">Success Rate</div>
            </div>
        </div>
        '''

    # Section divider
    def _dash_section(title: str) -> str:
        return f'<div style="margin-top:40px;margin-bottom:16px;padding-bottom:8px;border-bottom:1px solid var(--border);"><h2 style="font-family:var(--font-display);font-size:18px;color:var(--ink-muted);margin:0;">{title}</h2></div>'

    actions_html = f'''
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:32px;">
        <a href="/dashboard/tools" class="btn btn-primary">My Tools</a>
        <a href="/submit" class="btn btn-secondary">Submit New</a>
        <a href="/dashboard/saved" class="btn btn-secondary">Bookmarks</a>
        {'<a href="/dashboard/updates" class="btn btn-secondary">Post Update</a>' if maker_id else ''}
        <a href="/dashboard/my-stack" class="btn btn-secondary">My Stack</a>
    </div>
    '''

    # Build analytics section (only show heading if there's content)
    has_analytics = bool(ai_intel_html or funnel_html or search_intent_html)
    analytics_section = ''
    if has_analytics:
        analytics_section = f'''
        {_dash_section('Analytics')}
        {ai_intel_html}
        {funnel_html}
        {search_intent_html}
        '''

    # Pro features hub — shows Pro users where their features are
    pro_hub_html = ''
    if is_pro:
        _hub_title = "Here's what you unlocked" if just_subscribed else 'Your Pro Features'
        pro_hub_html = f'''
        <div style="margin-bottom:32px;">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:12px;">{_hub_title}</h3>
            <style>.pro-hub-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;}}@media(max-width:600px){{.pro-hub-grid{{grid-template-columns:1fr;}}}}.pro-feat{{text-decoration:none;display:block;padding:20px;border-radius:var(--radius);transition:transform 0.15s ease;}}.pro-feat:hover{{transform:translateY(-1px);}}</style>
            <div class="pro-hub-grid">
                <a href="/gaps" class="pro-feat" style="background:linear-gradient(135deg,#1A2D4A,#243B5E);">
                    <div style="font-size:15px;font-weight:700;color:white;margin-bottom:4px;">Demand Signals</div>
                    <div style="font-size:13px;color:rgba(255,255,255,0.6);line-height:1.4;">Full opportunity scores, sparklines &amp; competition maps</div>
                </a>
                <a href="#ai-distribution" class="pro-feat" style="background:linear-gradient(135deg,#1A2D4A,#243B5E);">
                    <div style="font-size:15px;font-weight:700;color:white;margin-bottom:4px;">Citation Intel</div>
                    <div style="font-size:13px;color:rgba(255,255,255,0.6);line-height:1.4;">See which AI agents recommend your tools &amp; how often</div>
                </a>
                <a href="/setup" class="pro-feat" style="background:linear-gradient(135deg,#1A2D4A,#243B5E);">
                    <div style="font-size:15px;font-weight:700;color:white;margin-bottom:4px;">Priority API</div>
                    <div style="font-size:13px;color:rgba(255,255,255,0.6);line-height:1.4;">Unlimited searches + personalized recommendations</div>
                </a>
                <div class="pro-feat" style="background:var(--card-bg);border:1px solid var(--border);cursor:default;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                        <span style="font-size:15px;font-weight:700;color:var(--ink);">Search Priority</span>
                        <span style="font-size:10px;font-weight:600;color:var(--accent);text-transform:uppercase;">Always On</span>
                    </div>
                    <div style="font-size:13px;color:var(--ink-muted);line-height:1.4;">Your tools rank higher in search &amp; AI discovery</div>
                </div>
                <a href="/dashboard/export?format=json" class="pro-feat" style="background:linear-gradient(135deg,#1A2D4A,#243B5E);">
                    <div style="font-size:15px;font-weight:700;color:white;margin-bottom:4px;">Data Export</div>
                    <div style="font-size:13px;color:rgba(255,255,255,0.6);line-height:1.4;">Download your tools &amp; analytics as JSON or CSV</div>
                </a>
                <div class="pro-feat" style="background:var(--card-bg);border:1px solid var(--border);cursor:default;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                        <span style="font-size:15px;font-weight:700;color:var(--ink);">Weekly AI Report</span>
                        <span style="font-size:10px;font-weight:600;color:var(--accent);text-transform:uppercase;">To Your Inbox</span>
                    </div>
                    <div style="font-size:13px;color:var(--ink-muted);line-height:1.4;">Citation stats, competitor alerts &amp; new tools in your categories</div>
                </div>
            </div>
        </div>
        '''

    # Build quality score card
    quality_html = ''
    if quality_score is not None:
        bar_color = '#2ecc71' if quality_score >= 70 else '#E2B764' if quality_score >= 40 else '#e74c3c'
        tips_html = ''.join(f'<li style="margin-bottom:6px;">{escape(tip)}</li>' for tip in quality_tips)
        tips_section = f'<ul style="margin:12px 0 0;padding-left:20px;font-size:13px;color:var(--ink-muted);list-style:disc;">{tips_html}</ul>' if tips_html else ''

        quality_html = f'''
        <div class="card" style="padding:24px;margin-bottom:24px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
                <h3 style="margin:0;font-family:var(--font-display);font-size:18px;">Listing Quality</h3>
                <span style="font-family:var(--font-display);font-size:24px;color:{bar_color};">{quality_score}/100</span>
            </div>
            <div style="background:var(--border);border-radius:999px;height:8px;overflow:hidden;">
                <div style="background:{bar_color};height:100%;width:{quality_score}%;border-radius:999px;transition:width 0.3s;"></div>
            </div>
            {tips_section}
        </div>
        '''

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:960px;">
        {welcome_banner}
        {trial_banner}
        {pro_banner}
        {verify_banner}
        {boost_success_banner}
        {avatar_saved_banner}
        {_new_key_banner}
        {api_key_html if not active_keys else ''}


        {header_html}
        {actions_html}

        {api_key_html if active_keys else ''}

        {pro_hub_html}

        {quality_html}

        {analytics_section}
    </div>
    """
    return HTMLResponse(page_shell("Dashboard", body, user=user))


# ── Claim Referral Boost ─────────────────────────────────────────────────

@router.post("/dashboard/claim-referral-boost")
async def claim_referral_boost_handler(request: Request):
    """Apply referral boost days to a tool."""
    user = request.state.user
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    form = await request.form()
    tool_id = int(form.get("tool_id", 0))
    if not tool_id:
        return RedirectResponse(url="/dashboard", status_code=303)

    db = request.state.db

    # Verify user owns this tool
    if user.get('maker_id'):
        tool = await get_tool_by_id(db, tool_id)
        if tool and tool.get('maker_id') == user['maker_id']:
            days = await claim_referral_boost(db, user['id'], tool_id)

    return RedirectResponse(url="/dashboard?boosted=1", status_code=303)


# ── Save Pixel Avatar ────────────────────────────────────────────────────

@router.post("/dashboard/avatar", response_class=HTMLResponse)
async def save_avatar(request: Request, pixel_avatar: str = Form("")):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect
    db = request.state.db
    clean = pixel_avatar.strip().lower()
    if clean and (len(clean) != 49 or not all(c in '0123456789abcdef' for c in clean)):
        clean = ''
    await update_user(db, user['id'], pixel_avatar=clean)
    return RedirectResponse(url="/dashboard?avatar=saved", status_code=303)


# ── My Tools ─────────────────────────────────────────────────────────────

@router.get("/dashboard/tools", response_class=HTMLResponse)
async def dashboard_tools(request: Request):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    maker_id = user.get('maker_id')

    if not maker_id:
        body = """
        <div class="container" style="padding:48px 24px;max-width:960px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);margin-bottom:16px;">My Tools</h1>
            <div class="card" style="text-align:center;padding:48px 32px;">
                <div style="margin-bottom:16px;"><svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/><path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0"/><path d="M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5"/></svg></div>
                <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:12px;">List your first creation</h2>
                <p style="color:var(--ink-muted);font-size:15px;line-height:1.6;max-width:400px;margin:0 auto 8px;">
                    Listing takes under 2 minutes. Free to list, no hidden fees.
                </p>
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:24px;">
                    Your maker profile is created automatically when you submit.
                </p>
                <a href="/submit" class="btn btn-primary" style="padding:12px 32px;font-size:16px;">Submit Your First Creation &rarr;</a>
            </div>
        </div>
        """
        return HTMLResponse(page_shell("My Tools", body, user=user))

    tools = await get_tools_by_maker(db, maker_id)
    is_pro = await check_pro(db, user['id'])

    status_styles = {
        'pending': 'background:var(--warning-bg);color:var(--warning-text);',
        'approved': 'background:var(--success-bg);color:var(--success-text);',
        'rejected': 'background:var(--error-bg);color:var(--error-text);',
    }

    rows = ''
    for t in tools:
        s = str(t.get('status', 'pending'))
        style = status_styles.get(s, '')
        name = escape(str(t['name']))
        slug = escape(str(t['slug']))
        price = format_price(t.get('price_pence', 0))
        upvotes = t.get('upvote_count', 0)
        is_totw = t.get('tool_of_the_week', 0) == 1
        mcp_views = t.get('mcp_view_count', 0)
        totw_badge = ' <span style="background:linear-gradient(135deg,#E2B764,#D4A84B);color:#1A2D4A;padding:4px 10px;border-radius:999px;font-size:12px;font-weight:700;"><svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:2px;"><path d="M12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26z"/></svg> Tool of the Week</span>' if is_totw else ''
        totw_line = ' &mdash; <span style="color:var(--gold);font-weight:600;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:2px;"><path d="M12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26z"/></svg> Currently Tool of the Week!</span>' if is_totw else ' &mdash; top tool each week gets featured on our homepage'
        # Get rating
        rating = await get_tool_rating(db, t['id'])
        rating_html = star_rating_html(rating['avg_rating'], rating['review_count'], size=14) if rating['review_count'] else '<span style="color:var(--ink-muted);font-size:12px;">No reviews</span>'
        # Success rate badge
        _tool_sr = await get_tool_success_rate(db, t['slug'])
        if _tool_sr['total'] > 0:
            _sr_badge_color = '#2ecc71' if _tool_sr['rate'] >= 70 else '#E2B764' if _tool_sr['rate'] >= 40 else '#e74c3c'
            sr_badge = f' <span style="font-size:11px;padding:2px 6px;border-radius:4px;background:{_sr_badge_color}22;color:{_sr_badge_color};">{_tool_sr["rate"]}% success</span>'
        else:
            sr_badge = ''

        rows += f"""
        <tr style="border-bottom:1px solid var(--border);">
            <td style="padding:12px;">
                <a href="/tool/{slug}" style="font-weight:600;color:var(--ink);">{name}</a>{totw_badge}{sr_badge}
                <p style="font-size:13px;color:var(--ink-muted);margin-top:8px;margin-bottom:0;">
                    <span style="color:var(--accent);display:inline-flex;align-items:center;"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg></span> {mcp_views} AI recommendations{totw_line}
                </p>
            </td>
            <td style="padding:12px;">
                <span style="display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600;{style}">{s}</span>
            </td>
            <td style="padding:12px;">{upvotes}</td>
            <td style="padding:12px;">{rating_html}</td>
            <td style="padding:12px;">
                <a href="/dashboard/tools/{t['id']}/edit" style="color:var(--terracotta);font-size:13px;font-weight:600;">Edit</a>
            </td>
        </tr>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:960px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">My Tools</h1>
            <a href="/dashboard" style="color:var(--ink-muted);font-size:14px;">&larr; Dashboard</a>
        </div>
        <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:14px;">
                <thead>
                    <tr style="border-bottom:2px solid var(--border);text-align:left;">
                        <th style="padding:12px;">Name</th>
                        <th style="padding:12px;">Status</th>
                        <th style="padding:12px;">Upvotes</th>
                        <th style="padding:12px;">Rating</th>
                        <th style="padding:12px;"></th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        <div style="margin-top:24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;">
            <a href="/submit" class="btn btn-primary">Submit New</a>
            {'<span style="font-size:13px;color:var(--ink-muted);">Export my data: <a href="/dashboard/export?format=json" style="color:var(--accent);font-weight:600;">JSON</a> | <a href="/dashboard/export?format=csv" style="color:var(--accent);font-weight:600;">CSV</a></span>' if is_pro else ''}
        </div>
    </div>
    """
    return HTMLResponse(page_shell("My Tools", body, user=user))


# ── Edit Tool ────────────────────────────────────────────────────────────

@router.get("/dashboard/tools/{tool_id}/edit", response_class=HTMLResponse)
async def edit_tool_get(request: Request, tool_id: int):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    tool = await get_tool_by_id(db, tool_id)
    if not tool or tool.get('maker_id') != user.get('maker_id'):
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Not Found</h1>
            <p class="text-muted mt-4">You don't have permission to edit this tool.</p>
            <a href="/dashboard/tools" class="btn btn-primary mt-4">Back to My Tools</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body, user=user), status_code=404)

    categories = await get_all_categories(db)
    changelogs = await get_tool_changelogs(db, tool_id, limit=20)
    maker = await get_maker_by_id(db, user['maker_id']) if user.get('maker_id') else None
    body = edit_tool_form(tool, categories, changelogs=changelogs, maker=maker)
    return HTMLResponse(page_shell(f"Edit {tool['name']}", body, user=user))


@router.post("/dashboard/tools/{tool_id}/edit", response_class=HTMLResponse)
async def edit_tool_post(
    request: Request, tool_id: int,
    name: str = Form(""), tagline: str = Form(""), description: str = Form(""),
    url: str = Form(""), tags: str = Form(""),
    price: str = Form(""), delivery_url: str = Form(""),
    pixel_icon: str = Form(""),
    story_motivation: str = Form(""), story_challenge: str = Form(""),
    story_advice: str = Form(""), story_fun_fact: str = Form(""),
    api_type: str = Form(""), auth_method: str = Form(""),
    install_command: str = Form(""), sdk_packages: str = Form(""),
    env_vars: str = Form(""), frameworks_tested: str = Form(""),
    agent_instructions: str = Form(""),
):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    tool = await get_tool_by_id(db, tool_id)
    if not tool or tool.get('maker_id') != user.get('maker_id'):
        return RedirectResponse(url="/dashboard/tools", status_code=303)

    # Auto-prepend https:// if missing protocol (mobile users often skip it)
    if url.strip() and not url.startswith("http"):
        url = "https://" + url.strip()

    # Validate
    errors = []
    if not name.strip():
        errors.append("Name is required.")
    if not tagline.strip():
        errors.append("Tagline is required.")
    if not url.strip() or not url.startswith("http"):
        errors.append("Valid URL required.")

    price_pence = tool.get('price_pence')
    if price.strip():
        try:
            pf = float(price.strip())
            if pf < 0.50:
                errors.append("Minimum price is \u00a30.50.")
            else:
                price_pence = int(round(pf * 100))
        except ValueError:
            errors.append("Invalid price format.")
    elif not price.strip():
        price_pence = None

    if errors:
        categories = await get_all_categories(db)
        body = edit_tool_form(tool, categories, error=" ".join(errors))
        return HTMLResponse(page_shell(f"Edit {tool['name']}", body, user=user))

    # Validate pixel_icon if provided
    clean_pixel = pixel_icon.strip().lower()
    if clean_pixel and (len(clean_pixel) != 49 or not all(c in '0123456789abcdef' for c in clean_pixel)):
        clean_pixel = tool.get('pixel_icon', '') or ''  # keep existing if invalid

    await update_tool(db, tool_id,
                      name=name.strip(), tagline=tagline.strip(),
                      description=description.strip(), url=url.strip(),
                      tags=tags.strip(), price_pence=price_pence,
                      delivery_url=delivery_url.strip(),
                      pixel_icon=clean_pixel,
                      api_type=api_type.strip(),
                      auth_method=auth_method.strip(),
                      install_command=install_command.strip(),
                      sdk_packages=sdk_packages.strip(),
                      env_vars=env_vars.strip(),
                      frameworks_tested=frameworks_tested.strip(),
                      agent_instructions=agent_instructions.strip())

    # Save maker story fields
    maker_id = user.get('maker_id')
    if maker_id:
        await update_maker(db, maker_id,
                           story_motivation=story_motivation.strip(),
                           story_challenge=story_challenge.strip(),
                           story_advice=story_advice.strip(),
                           story_fun_fact=story_fun_fact.strip())

    return RedirectResponse(url="/dashboard/tools", status_code=303)


@router.post("/dashboard/tools/{tool_id}/changelog")
async def post_tool_changelog(request: Request, tool_id: int):
    user = request.state.user
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    maker_id = user.get('maker_id')
    if not maker_id:
        return RedirectResponse(url="/dashboard", status_code=303)

    db = request.state.db
    tool = await get_tool_by_id(db, tool_id)
    if not tool or tool.get('maker_id') != maker_id:
        return RedirectResponse(url="/dashboard/tools", status_code=303)

    form = await request.form()
    title = str(form.get('title', '')).strip()
    body_text = str(form.get('body', '')).strip()
    update_type = str(form.get('update_type', 'changelog'))

    if not body_text:
        return RedirectResponse(f"/dashboard/tools/{tool_id}/edit", status_code=303)

    await create_maker_update(db, maker_id, title, body_text, update_type, tool_id=tool_id)

    # Notify wishlist users about the update
    try:
        if tool_id:
            wishlist_users = await get_wishlist_users_for_tool(db, tool_id)
            tool_info = await get_tool_by_id(db, tool_id)
            if tool_info and wishlist_users:
                for wu in wishlist_users:
                    if wu.get('email'):
                        try:
                            await send_email(
                                wu['email'],
                                f"{tool_info['name']} just shipped an update!",
                                wishlist_update_html(
                                    wu.get('name', 'there'),
                                    tool_info['name'],
                                    title,
                                    f"{BASE_URL}/tool/{tool_info['slug']}"
                                )
                            )
                        except Exception:
                            pass  # Don't break on email failure
    except Exception:
        pass

    return RedirectResponse(f"/dashboard/tools/{tool_id}/edit", status_code=303)


def edit_tool_form(tool: dict, categories: list, error: str = "", changelogs: list = None, maker: dict = None) -> str:
    alert = f'<div class="alert alert-error">{escape(error)}</div>' if error else ''
    price_val = f"{tool['price_pence']/100:.2f}" if tool.get('price_pence') else ''

    # Build existing changelogs display
    existing_cl_html = ''
    if changelogs:
        cl_cards = '\n'.join(update_card(cl) for cl in changelogs)
        existing_cl_html = f"""
        <div style="margin-top:32px;">
            <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:12px;color:var(--ink);">Previous Changelogs</h3>
            {cl_cards}
        </div>
        """

    return f"""
    <div class="container" style="max-width:640px;padding:48px 24px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32px;">
            <h1 style="font-family:var(--font-display);font-size:28px;color:var(--ink);">Edit {escape(str(tool['name']))}</h1>
            <a href="/dashboard/tools" style="color:var(--ink-muted);font-size:14px;">&larr; My Tools</a>
        </div>
        {alert}
        <form method="post">
            <div class="form-group">
                <label for="name">Tool Name</label>
                <input type="text" id="name" name="name" class="form-input" required
                       value="{escape(str(tool['name']))}">
            </div>
            <div class="form-group">
                <label for="tagline">Tagline</label>
                <input type="text" id="tagline" name="tagline" class="form-input" required maxlength="100"
                       value="{escape(str(tool['tagline']))}">
            </div>
            <div class="form-group">
                <label for="url">Website URL</label>
                <input type="url" id="url" name="url" class="form-input" required
                       value="{escape(str(tool['url']))}">
            </div>
            <div class="form-group">
                <label for="description">Description</label>
                <textarea id="description" name="description" class="form-textarea" required>{escape(str(tool['description']))}</textarea>
            </div>
            <div class="form-group">
                <label for="tags">Tags (comma-separated)</label>
                <input type="text" id="tags" name="tags" class="form-input"
                       value="{escape(str(tool.get('tags', '')))}">
            </div>
            <div style="border-top:1px solid var(--border);margin-top:24px;padding-top:24px;">
                <h3 style="margin:0 0 8px;font-family:var(--heading-font);">Agent Assembly Metadata</h3>
                <p style="color:var(--ink-muted);font-size:14px;margin:0 0 16px;">Help AI agents integrate your tool. These fields tell agents exactly how to use your creation.</p>

                <label style="font-weight:600;display:block;margin-bottom:4px;">API Type</label>
                <select name="api_type" style="width:100%;padding:10px 12px;border-radius:8px;border:1px solid var(--border);margin-bottom:16px;background:var(--bg-card);color:var(--ink);">
                    <option value="">Not specified</option>
                    <option value="REST"{' selected' if (tool.get('api_type') or '') == 'REST' else ''}>REST API</option>
                    <option value="GraphQL"{' selected' if (tool.get('api_type') or '') == 'GraphQL' else ''}>GraphQL</option>
                    <option value="SDK"{' selected' if (tool.get('api_type') or '') == 'SDK' else ''}>SDK / Library</option>
                    <option value="CLI"{' selected' if (tool.get('api_type') or '') == 'CLI' else ''}>CLI Tool</option>
                    <option value="WebSocket"{' selected' if (tool.get('api_type') or '') == 'WebSocket' else ''}>WebSocket</option>
                </select>

                <label style="font-weight:600;display:block;margin-bottom:4px;">Auth Method</label>
                <select name="auth_method" style="width:100%;padding:10px 12px;border-radius:8px;border:1px solid var(--border);margin-bottom:16px;background:var(--bg-card);color:var(--ink);">
                    <option value="">Not specified</option>
                    <option value="api_key"{' selected' if (tool.get('auth_method') or '') == 'api_key' else ''}>API Key</option>
                    <option value="oauth2"{' selected' if (tool.get('auth_method') or '') == 'oauth2' else ''}>OAuth 2.0</option>
                    <option value="bearer"{' selected' if (tool.get('auth_method') or '') == 'bearer' else ''}>Bearer Token</option>
                    <option value="none"{' selected' if (tool.get('auth_method') or '') == 'none' else ''}>None (open)</option>
                </select>

                <label style="font-weight:600;display:block;margin-bottom:4px;">Install Command</label>
                <input type="text" name="install_command" value="{escape(str(tool.get('install_command','') or ''))}"
                       placeholder="npm install your-package / pip install your-package"
                       style="width:100%;padding:10px 12px;border-radius:8px;border:1px solid var(--border);margin-bottom:16px;font-family:var(--mono);">

                <label style="font-weight:600;display:block;margin-bottom:4px;">SDK Packages <span style="color:var(--ink-muted);font-weight:400;">(JSON)</span></label>
                <input type="text" name="sdk_packages" value="{escape(str(tool.get('sdk_packages','') or ''))}"
                       placeholder='{{"npm": "@your/package", "pip": "your-package"}}'
                       style="width:100%;padding:10px 12px;border-radius:8px;border:1px solid var(--border);margin-bottom:16px;font-family:var(--mono);">

                <label style="font-weight:600;display:block;margin-bottom:4px;">Env Vars <span style="color:var(--ink-muted);font-weight:400;">(JSON array)</span></label>
                <input type="text" name="env_vars" value="{escape(str(tool.get('env_vars','') or ''))}"
                       placeholder='["YOUR_API_KEY", "YOUR_SECRET"]'
                       style="width:100%;padding:10px 12px;border-radius:8px;border:1px solid var(--border);margin-bottom:16px;font-family:var(--mono);">

                <label style="font-weight:600;display:block;margin-bottom:4px;">Frameworks Tested</label>
                <input type="text" name="frameworks_tested" value="{escape(str(tool.get('frameworks_tested','') or ''))}"
                       placeholder="nextjs, fastapi, rails, django"
                       style="width:100%;padding:10px 12px;border-radius:8px;border:1px solid var(--border);margin-bottom:16px;">

                <div style="margin-bottom:20px;">
                    <label style="display:block;font-weight:600;margin-bottom:6px;font-size:14px;">Agent Instructions</label>
                    <p style="font-size:12px;color:var(--ink-muted);margin:0 0 8px;">
                        Tell AI agents how to implement your tool correctly. This text is shown directly to agents when they recommend your tool. Include correct import syntax, common pitfalls, required setup steps, and version-specific notes.
                    </p>
                    <textarea name="agent_instructions" rows="6" maxlength="2000" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--surface);color:var(--ink);font-family:var(--font-mono);font-size:13px;resize:vertical;"
                        placeholder="Example: Use v3 API (v2 is deprecated). Auth requires both API_KEY and PROJECT_ID env vars. For Next.js, wrap in useEffect — SSR is not supported."
                    >{escape(str(tool.get('agent_instructions', '') or ''))}</textarea>
                </div>
            </div>

            <div class="form-group">
                <label>Pixel Icon <span style="color:var(--ink-muted);font-weight:400;font-size:13px;">(7&times;7 pixel art for your tool)</span></label>
                <div style="display:flex;gap:24px;align-items:flex-start;flex-wrap:wrap;">
                    <div>
                        <div id="pixel-grid" style="display:grid;grid-template-columns:repeat(7,32px);grid-template-rows:repeat(7,32px);gap:1px;background:var(--border);border:1px solid var(--border);border-radius:4px;cursor:crosshair;"></div>
                        <div id="pixel-palette" style="display:flex;gap:4px;margin-top:8px;"></div>
                        <button type="button" onclick="clearPixelGrid()" style="margin-top:8px;font-size:12px;color:var(--ink-muted);background:none;border:1px solid var(--border);border-radius:4px;padding:4px 10px;cursor:pointer;">Clear</button>
                    </div>
                    <div>
                        <p style="font-size:12px;color:var(--ink-muted);margin-bottom:4px;">Preview</p>
                        <div id="pixel-preview" style="border:1px solid var(--border);border-radius:4px;"></div>
                    </div>
                </div>
                <input type="hidden" id="pixel_icon" name="pixel_icon" value="{escape(str(tool.get('pixel_icon', '') or ''))}">
            </div>
            <script>
            (function(){{
                var COLORS = ['transparent','#1A2D4A','#00D4F5','#E2B764','#FFFFFF','#64748B','#E07A5F','#22C55E','#000000','#EF4444','#EC4899','#8B5CF6','#F97316','#7DD3FC','#86EFAC','#92400E'];
                var LABELS = ['Erase','Navy','Cyan','Gold','White','Slate','Terracotta','Green','Black','Red','Pink','Purple','Orange','Light Blue','Light Green','Brown'];
                var grid = document.getElementById('pixel-grid');
                var palette = document.getElementById('pixel-palette');
                var input = document.getElementById('pixel_icon');
                var preview = document.getElementById('pixel-preview');
                var activeColor = '1';
                var cells = [];
                var data = (input.value || '').padEnd(49, '0').split('');

                // Build palette
                COLORS.forEach(function(c, i) {{
                    var sw = document.createElement('div');
                    sw.title = LABELS[i];
                    sw.style.cssText = 'width:24px;height:24px;border-radius:4px;cursor:pointer;border:2px solid ' + (i.toString(16) === activeColor ? 'var(--accent)' : 'var(--border)') + ';background:' + (c === 'transparent' ? 'repeating-conic-gradient(#ccc 0% 25%, #fff 0% 50%) 50% / 12px 12px' : c) + ';';
                    sw.onclick = function() {{
                        activeColor = i.toString(16);
                        palette.querySelectorAll('div').forEach(function(s, j) {{
                            s.style.borderColor = j === i ? 'var(--accent)' : 'var(--border)';
                        }});
                    }};
                    palette.appendChild(sw);
                }});

                // Build grid
                var isMouseDown = false;
                grid.onmousedown = function() {{ isMouseDown = true; }};
                document.onmouseup = function() {{ isMouseDown = false; }};
                for (var i = 0; i < 49; i++) {{
                    (function(idx) {{
                        var cell = document.createElement('div');
                        cell.style.cssText = 'background:' + (data[idx] === '0' ? 'var(--card-bg)' : COLORS[parseInt(data[idx],16)]) + ';';
                        cell.onmousedown = function(e) {{ e.preventDefault(); paint(idx); }};
                        cell.onmouseenter = function() {{ if (isMouseDown) paint(idx); }};
                        grid.appendChild(cell);
                        cells.push(cell);
                    }})(i);
                }}

                function paint(idx) {{
                    data[idx] = activeColor;
                    cells[idx].style.background = activeColor === '0' ? 'var(--card-bg)' : COLORS[parseInt(activeColor,16)];
                    sync();
                }}

                function sync() {{
                    input.value = data.join('');
                    // Update preview SVG
                    var svg = '<svg width="24" height="24" viewBox="0 0 7 7" style="image-rendering:pixelated;">';
                    for (var i = 0; i < 49; i++) {{
                        if (data[i] !== '0' && COLORS[parseInt(data[i],16)]) {{
                            var x = i % 7, y = Math.floor(i / 7);
                            svg += '<rect x="'+x+'" y="'+y+'" width="1" height="1" fill="'+COLORS[parseInt(data[i],16)]+'"/>';
                        }}
                    }}
                    svg += '</svg>';
                    preview.innerHTML = svg;
                }}

                window.clearPixelGrid = function() {{
                    data = Array(49).fill('0');
                    cells.forEach(function(c) {{ c.style.background = 'var(--card-bg)'; }});
                    sync();
                }};

                sync();
            }})();
            </script>
            </div>
            <div style="margin-top:32px;padding-top:24px;border-top:1px solid var(--border);">
                <h3 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:4px;">Your Maker Story</h3>
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">Tell the community about your journey. This appears on your tool's page.</p>
                <div class="form-group">
                    <label for="story_motivation">Why did you build this?</label>
                    <textarea id="story_motivation" name="story_motivation"
                        style="width:100%;min-height:80px;padding:12px;border:1px solid var(--border);border-radius:var(--radius-sm);font-family:var(--font-body);font-size:14px;resize:vertical;background:var(--bg);color:var(--ink);"
                        placeholder="What problem were you solving? What made you decide to build it yourself?">{escape(str((maker or {{}}).get('story_motivation', '') or ''))}</textarea>
                </div>
                <div class="form-group">
                    <label for="story_challenge">What was the hardest part?</label>
                    <textarea id="story_challenge" name="story_challenge"
                        style="width:100%;min-height:80px;padding:12px;border:1px solid var(--border);border-radius:var(--radius-sm);font-family:var(--font-body);font-size:14px;resize:vertical;background:var(--bg);color:var(--ink);"
                        placeholder="Technical challenge, design decision, or business hurdle?">{escape(str((maker or {{}}).get('story_challenge', '') or ''))}</textarea>
                </div>
                <div class="form-group">
                    <label for="story_advice">Advice for indie makers?</label>
                    <textarea id="story_advice" name="story_advice"
                        style="width:100%;min-height:80px;padding:12px;border:1px solid var(--border);border-radius:var(--radius-sm);font-family:var(--font-body);font-size:14px;resize:vertical;background:var(--bg);color:var(--ink);"
                        placeholder="What would you tell someone starting a similar project?">{escape(str((maker or {{}}).get('story_advice', '') or ''))}</textarea>
                </div>
                <div class="form-group">
                    <label for="story_fun_fact">Fun fact about this project</label>
                    <textarea id="story_fun_fact" name="story_fun_fact"
                        style="width:100%;min-height:80px;padding:12px;border:1px solid var(--border);border-radius:var(--radius-sm);font-family:var(--font-body);font-size:14px;resize:vertical;background:var(--bg);color:var(--ink);"
                        placeholder="Something surprising, weird, or delightful about building this">{escape(str((maker or {{}}).get('story_fun_fact', '') or ''))}</textarea>
                </div>
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:12px;">
                Save Changes
            </button>
        </form>

        <div style="margin-top:40px;border-top:2px solid var(--border);padding-top:32px;">
            <h2 style="font-family:var(--font-display);font-size:22px;margin-bottom:16px;color:var(--ink);">Post a Changelog</h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">Let users know about bug fixes, new features, and improvements.</p>
            <form method="post" action="/dashboard/tools/{tool['id']}/changelog">
                <div class="form-group">
                    <label for="cl_type">Type</label>
                    <select id="cl_type" name="update_type" class="form-select" style="max-width:200px;">
                        <option value="changelog">Changelog</option>
                        <option value="update">Update</option>
                        <option value="launch">Launch</option>
                        <option value="milestone">Milestone</option>
                    </select>
                </div>
                <div class="form-group">
                    <label for="cl_title">Title</label>
                    <input type="text" id="cl_title" name="title" class="form-input" placeholder="e.g. v2.1 — Dark mode &amp; bug fixes" maxlength="200">
                </div>
                <div class="form-group">
                    <label for="cl_body">Details *</label>
                    <textarea id="cl_body" name="body" class="form-textarea" required placeholder="What changed? List bug fixes, new features, improvements..."></textarea>
                </div>
                <button type="submit" class="btn btn-primary">Post Changelog</button>
            </form>
        </div>

        {existing_cl_html}
    </div>
    """


# ── Sales History (redirects to dashboard — selling paused) ──────────────

@router.get("/dashboard/sales")
async def dashboard_sales(request: Request):
    return RedirectResponse(url="/dashboard", status_code=303)


# ── Analytics ────────────────────────────────────────────────────────────

@router.get("/dashboard/analytics", response_class=HTMLResponse)
async def dashboard_analytics(request: Request):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    is_pro = await check_pro(db, user['id'])
    if not is_pro:
        body = """
        <div class="container" style="text-align:center;padding:80px 24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Analytics</h1>
            <p style="color:var(--ink-muted);margin:16px 0 24px;">Tool view analytics is coming soon.</p>
            <a href="/dashboard" class="btn btn-secondary">Back to Dashboard</a>
        </div>
        """
        return HTMLResponse(page_shell("Analytics", body, user=user))

    maker_id = user.get('maker_id')
    if not maker_id:
        body = """
        <div class="container" style="padding:48px 24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Analytics</h1>
            <p class="text-muted mt-4">Submit a tool to see analytics.</p>
        </div>
        """
        return HTMLResponse(page_shell("Analytics", body, user=user))

    views = await get_tool_views_by_maker(db, maker_id, days=30)

    rows = ''
    for v in views:
        rows += f"""
        <tr style="border-bottom:1px solid var(--border);">
            <td style="padding:10px 12px;font-weight:600;">
                <a href="/tool/{escape(str(v['slug']))}" style="color:var(--ink);">{escape(str(v['name']))}</a>
            </td>
            <td style="padding:10px 12px;font-family:var(--font-display);font-size:18px;color:var(--terracotta);">
                {v['view_count']}
            </td>
        </tr>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:960px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Analytics (Last 30 Days)</h1>
            <a href="/dashboard" style="color:var(--ink-muted);font-size:14px;">&larr; Dashboard</a>
        </div>
        <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:14px;">
                <thead>
                    <tr style="border-bottom:2px solid var(--border);text-align:left;">
                        <th style="padding:10px 12px;">Tool</th>
                        <th style="padding:10px 12px;">Views</th>
                    </tr>
                </thead>
                <tbody>{rows if rows else '<tr><td colspan="2" style="padding:20px;text-align:center;color:var(--ink-muted);">No views yet</td></tr>'}</tbody>
            </table>
        </div>
    </div>
    """
    return HTMLResponse(page_shell("Analytics", body, user=user))


# ── Bookmarks ─────────────────────────────────────────────────────────

@router.get("/dashboard/saved", response_class=HTMLResponse)
async def dashboard_saved(request: Request):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    page = int(request.query_params.get('page', '1'))
    tools, total = await get_user_wishlist(db, user['id'], page=page, per_page=12)
    total_pages = max(1, (total + 11) // 12)

    cards = '\n'.join(tool_card(t) for t in tools) if tools else '<p style="color:var(--ink-muted);text-align:center;">No saved tools yet. Browse and bookmark tools you like!</p>'

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:960px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Bookmarks</h1>
            <a href="/dashboard" style="color:var(--ink-muted);font-size:14px;">&larr; Dashboard</a>
        </div>
        <div class="card-grid">{cards}</div>
        {pagination_html(page, total_pages, '/dashboard/saved')}
    </div>
    """
    return HTMLResponse(page_shell("Bookmarks", body, user=user))


# ── Maker Updates ───────────────────────────────────────────────────────

@router.get("/dashboard/updates", response_class=HTMLResponse)
async def dashboard_updates_get(request: Request):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    maker_id = user.get('maker_id')
    if not maker_id:
        body = """
        <div class="container" style="padding:48px 24px;max-width:960px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Post Update</h1>
            <div class="alert alert-info">Create a maker profile first by submitting a tool.</div>
        </div>
        """
        return HTMLResponse(page_shell("Post Update", body, user=user))

    updates = await get_updates_by_maker(db, maker_id, limit=20)
    maker = await get_maker_by_id(db, maker_id)

    existing_html = ''
    if updates:
        from html import escape as esc
        for u in updates:
            ut = str(u.get('update_type', 'update'))
            title = esc(str(u.get('title', '')))
            body_text = esc(str(u.get('body', '')))
            created = str(u.get('created_at', ''))[:10]
            existing_html += f"""
            <div style="padding:12px 0;border-bottom:1px solid var(--border);">
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                    <span class="tag">{ut}</span>
                    <span style="font-size:12px;color:var(--ink-muted);">{created}</span>
                </div>
                {'<strong>' + title + '</strong><br>' if title else ''}
                <p style="color:var(--ink-light);font-size:14px;margin-top:4px;">{body_text}</p>
            </div>
            """

    type_options = ''
    for val, label in [('update', 'Update'), ('launch', 'Launch'), ('milestone', 'Milestone'), ('changelog', 'Changelog')]:
        type_options += f'<option value="{val}">{label}</option>'

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:640px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Post Update</h1>
            <a href="/dashboard" style="color:var(--ink-muted);font-size:14px;">&larr; Dashboard</a>
        </div>
        <div class="card" style="margin-bottom:32px;">
            <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:16px;">Share what you're building</h3>
            <form method="post" action="/dashboard/updates">
                <div class="form-group">
                    <label for="update_type">Type</label>
                    <select id="update_type" name="update_type" class="form-select" style="max-width:200px;">
                        {type_options}
                    </select>
                </div>
                <div class="form-group">
                    <label for="title">Title (optional)</label>
                    <input type="text" id="title" name="title" class="form-input" maxlength="200" placeholder="e.g. v2.0 launched!">
                </div>
                <div class="form-group">
                    <label for="body">What's new? *</label>
                    <textarea id="body" name="body" class="form-textarea" required placeholder="Share a changelog, milestone, or update..."></textarea>
                </div>
                <button type="submit" class="btn btn-primary">Post Update</button>
            </form>
        </div>
        {'<h2 style="font-family:var(--font-display);font-size:20px;margin-bottom:16px;">Your Updates</h2>' + existing_html if existing_html else ''}
    </div>
    """
    return HTMLResponse(page_shell("Post Update", body, user=user))


@router.post("/dashboard/updates")
async def dashboard_updates_post(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    maker_id = user.get('maker_id')
    if not maker_id:
        return RedirectResponse(url="/dashboard", status_code=303)

    form = await request.form()
    title = str(form.get('title', '')).strip()
    body_text = str(form.get('body', '')).strip()
    update_type = str(form.get('update_type', 'update'))

    if not body_text:
        return RedirectResponse(url="/dashboard/updates", status_code=303)

    await create_maker_update(request.state.db, maker_id, title, body_text, update_type)
    return RedirectResponse(url="/dashboard/updates", status_code=303)


# ── Notifications ────────────────────────────────────────────────────────

@router.get("/dashboard/notifications", response_class=HTMLResponse)
async def dashboard_notifications(request: Request):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    notifications = await get_notifications(db, user['id'], limit=50)

    # Mark all as read after fetching
    await mark_notifications_read(db, user['id'])

    type_icons = {
        'upvote': '&#9650;',
        'wishlist': '&#9733;',
    }
    type_colors = {
        'upvote': 'color:var(--slate-dark);',
        'wishlist': 'color:var(--gold);',
    }

    rows = ''
    for n in notifications:
        is_unread = not n.get('is_read', 1)
        bold = 'font-weight:700;' if is_unread else ''
        bg = 'background:#EDF4F9;' if is_unread else ''
        icon = type_icons.get(n.get('type', ''), '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/></svg>')
        icon_style = type_colors.get(n.get('type', ''), '')
        message = escape(str(n.get('message', '')))
        link = escape(str(n.get('link', '')))
        created = str(n.get('created_at', ''))[:16].replace('T', ' ')
        dot = '<span style="width:8px;height:8px;border-radius:50%;background:var(--slate);display:inline-block;margin-right:8px;"></span>' if is_unread else '<span style="width:8px;display:inline-block;margin-right:8px;"></span>'

        link_open = f'<a href="{link}" style="text-decoration:none;color:inherit;display:block;">' if link else '<div>'
        link_close = '</a>' if link else '</div>'

        rows += f"""
        {link_open}
        <div style="display:flex;align-items:center;gap:12px;padding:14px 16px;border-bottom:1px solid var(--border);{bg}transition:background 0.15s ease;">
            {dot}
            <span style="font-size:20px;{icon_style}">{icon}</span>
            <div style="flex:1;min-width:0;">
                <div style="font-size:14px;{bold}color:var(--ink);">{message}</div>
                <div style="font-size:12px;color:var(--ink-muted);margin-top:2px;">{created}</div>
            </div>
        </div>
        {link_close}
        """

    empty = '<p style="text-align:center;color:var(--ink-muted);padding:40px 0;">No notifications yet. When someone upvotes or saves your tools, you\'ll see it here.</p>'

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:700px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Notifications</h1>
            <a href="/dashboard" style="color:var(--ink-muted);font-size:14px;">&larr; Dashboard</a>
        </div>
        <div class="card" style="padding:0;overflow:hidden;">
            {rows if rows else empty}
        </div>
    </div>
    """
    return HTMLResponse(page_shell("Notifications", body, user=user))


# ── Stripe Connect ──────────────────────────────────────────────────────

@router.post("/dashboard/stripe-connect")
async def stripe_connect(request: Request):
    user = request.state.user
    if not user or not user.get('maker_id'):
        return RedirectResponse("/login", status_code=303)

    db = request.state.db
    maker_id = user['maker_id']

    # Check if maker already has a Stripe account
    row = await db.execute("SELECT stripe_account_id FROM makers WHERE id = ?", (maker_id,))
    existing = await row.fetchone()
    account_id = existing.get('stripe_account_id') or None if existing else None

    try:
        if not account_id:
            # Create new Stripe Connect account
            account = create_connect_account()
            account_id = account.id
            await update_maker_stripe_account(db, maker_id, account_id)
            # Propagate to all maker's tools so "Buy Now" button appears
            await db.execute(
                "UPDATE tools SET stripe_account_id = ? WHERE maker_id = ?",
                (account_id, maker_id)
            )
            await db.commit()

        # Create onboarding link (works for new or returning onboarding)
        base_url = str(request.base_url).rstrip("/").replace("http://", "https://")
        onboarding_url = create_onboarding_link(
            account_id,
            return_url=f"{base_url}/dashboard/stripe-callback",
            refresh_url=f"{base_url}/dashboard",
        )

        return RedirectResponse(onboarding_url, status_code=303)
    except Exception as e:
        error_msg = str(e)
        body = f"""
        <div class="container" style="padding:48px 24px;max-width:640px;text-align:center;">
            <h1 style="font-family:var(--font-display);font-size:28px;color:var(--ink);">Stripe Connect Unavailable</h1>
            <p style="color:var(--ink-muted);margin-top:12px;">Stripe Connect isn't set up yet. The platform admin needs to enable Connect on the Stripe dashboard.</p>
            <p style="color:var(--ink-muted);font-size:13px;margin-top:16px;font-family:var(--font-mono);">{escape(error_msg)}</p>
            <a href="/dashboard" class="btn btn-primary" style="margin-top:24px;">Back to Dashboard</a>
        </div>"""
        return HTMLResponse(page_shell("Stripe Connect", body, user=user))


@router.get("/dashboard/stripe-callback")
async def stripe_callback(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse("/login", status_code=303)

    db = request.state.db

    # Propagate stripe_account_id to maker's tools
    if user.get('maker_id'):
        mk_row = await db.execute("SELECT stripe_account_id FROM makers WHERE id = ?", (user['maker_id'],))
        mk_data = await mk_row.fetchone()
        if mk_data and mk_data.get('stripe_account_id'):
            await db.execute(
                "UPDATE tools SET stripe_account_id = ? WHERE maker_id = ?",
                (mk_data['stripe_account_id'], user['maker_id'])
            )
            await db.commit()

    body = '''
    <div style="max-width:600px;margin:60px auto;text-align:center;padding:40px;">
        <div style="font-size:48px;margin-bottom:20px;">&#10003;</div>
        <h1 style="color:var(--terracotta);font-family:var(--font-display);">Stripe Connected!</h1>
        <p style="color:var(--ink-muted);margin:16px 0;">Your payment account is set up. You can now receive payments for your tools.</p>
        <a href="/dashboard" style="display:inline-block;margin-top:20px;padding:12px 32px;background:var(--terracotta);color:white;border-radius:var(--radius-sm);text-decoration:none;font-weight:600;">Back to Dashboard</a>
    </div>
    '''
    return HTMLResponse(page_shell("Stripe Connected", body, user=user))


# ── My Stack ───────────────────────────────────────────────────────────

@router.get("/dashboard/my-stack", response_class=HTMLResponse)
async def my_stack_page(request: Request):
    """Manage your public tool stack."""
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    stack, tools = await get_user_stack(db, user['id'])
    # Get all approved tools for the "add tool" dropdown
    all_tools_cursor = await db.execute(
        "SELECT id, name, slug FROM tools WHERE status = 'approved' ORDER BY name ASC")
    all_tools = await all_tools_cursor.fetchall()

    # Build tools list
    tools_html = ''
    if not tools:
        tools_html = '<p style="color:var(--ink-muted);text-align:center;padding:20px;">No tools in your stack yet. Add some below!</p>'
    else:
        for t in tools:
            tools_html += f"""
            <div style="display:flex;align-items:center;gap:12px;padding:12px 16px;background:#fff;
                        border-radius:var(--radius);border:1px solid var(--border);margin-bottom:8px;">
                <div style="flex:1;">
                    <a href="/tool/{escape(str(t['slug']))}" style="font-weight:600;color:var(--terracotta);text-decoration:none;">{escape(str(t['name']))}</a>
                    <span style="color:var(--ink-muted);font-size:13px;margin-left:8px;">{escape(str(t.get('category_name', '')))}</span>
                </div>
                <form method="post" action="/dashboard/my-stack/remove" style="margin:0;">
                    <input type="hidden" name="tool_slug" value="{escape(str(t['slug']))}">
                    <button type="submit" style="background:none;border:none;color:var(--error-text);cursor:pointer;font-size:18px;padding:4px 8px;" title="Remove">&times;</button>
                </form>
            </div>"""

    # Tool dropdown options
    existing_slugs = {t['slug'] for t in tools} if tools else set()
    options = ''.join(f'<option value="{escape(str(t["slug"]))}">{escape(str(t["name"]))}</option>' for t in all_tools if t['slug'] not in existing_slugs)

    title = escape(str(stack['title'])) if stack else 'My Stack'
    description = escape(str(stack['description'])) if stack and stack.get('description') else ''
    is_public = stack.get('is_public', 1) if stack else 1
    username_slug = (user.get('name', '') or '').lower().replace(' ', '-')
    share_url = f"{BASE_URL}/stack/{username_slug}" if username_slug else ''

    share_banner = ''
    if share_url and is_public:
        share_banner = f"""
        <div style="background:var(--cream-dark);border-radius:var(--radius);padding:16px 20px;margin-bottom:24px;display:flex;align-items:center;justify-content:space-between;">
            <div><span style="font-weight:600;color:var(--terracotta);">Your public stack:</span> <a href="/stack/{username_slug}" style="color:var(--slate);">{share_url}</a></div>
            <a href="https://twitter.com/intent/tweet?text=Check out my indie tool stack!&url={share_url}" target="_blank" rel="noopener"
               style="background:var(--terracotta);color:#fff;padding:6px 14px;border-radius:999px;text-decoration:none;font-size:13px;font-weight:600;">Share on &#120143;</a>
        </div>"""

    body = f"""
    <div style="max-width:700px;margin:0 auto;padding:40px 20px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;">
            <h1 style="font-family:var(--font-display);color:var(--terracotta);font-size:28px;margin:0;">My Stack</h1>
            <a href="/dashboard" style="color:var(--ink-muted);text-decoration:none;font-size:14px;">&larr; Back to Dashboard</a>
        </div>

        <form method="post" action="/dashboard/my-stack" style="margin-bottom:24px;">
            <div style="background:#fff;border-radius:var(--radius);padding:24px;border:1px solid var(--border);">
                <label style="font-weight:600;color:var(--terracotta);display:block;margin-bottom:8px;">Stack Title</label>
                <input type="text" name="title" value="{title}"
                       style="width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:15px;margin-bottom:16px;box-sizing:border-box;">
                <label style="font-weight:600;color:var(--terracotta);display:block;margin-bottom:8px;">Description</label>
                <textarea name="description" rows="3"
                          style="width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:15px;margin-bottom:16px;box-sizing:border-box;resize:vertical;">{description}</textarea>
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">
                    <input type="checkbox" name="is_public" id="is_public" value="1" {'checked' if is_public else ''}>
                    <label for="is_public" style="font-size:14px;color:var(--ink-light);">Make my stack public</label>
                </div>
                <button type="submit" style="background:var(--terracotta);color:#fff;padding:10px 24px;border:none;border-radius:999px;cursor:pointer;font-weight:600;">
                    Save Settings
                </button>
            </div>
        </form>

        {share_banner}

        <h2 style="font-family:var(--font-display);color:var(--terracotta);font-size:20px;margin-bottom:16px;">Tools in Your Stack</h2>
        {tools_html}

        <form method="post" action="/dashboard/my-stack/add" style="margin-top:16px;display:flex;gap:8px;">
            <select name="tool_slug" style="flex:1;padding:10px 14px;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:15px;">
                <option value="">Select a tool to add...</option>
                {options}
            </select>
            <button type="submit" style="background:var(--slate);color:var(--terracotta);padding:10px 20px;border:none;border-radius:999px;cursor:pointer;font-weight:700;">
                + Add
            </button>
        </form>
    </div>"""

    return HTMLResponse(page_shell("My Stack", body, user=user))


@router.post("/dashboard/my-stack")
async def save_my_stack(request: Request):
    """Save stack settings."""
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    form = await request.form()
    title = str(form.get('title', 'My Stack')).strip()
    description = str(form.get('description', '')).strip()
    is_public = 1 if form.get('is_public') else 0

    db = request.state.db
    stack, _ = await get_user_stack(db, user['id'])
    if not stack:
        await create_user_stack(db, user['id'], title, description)
        stack, _ = await get_user_stack(db, user['id'])
    if stack:
        await update_user_stack(db, stack['id'], title=title, description=description, is_public=is_public)

    return RedirectResponse("/dashboard/my-stack", status_code=303)


@router.post("/dashboard/my-stack/add")
async def add_to_my_stack(request: Request):
    """Add a tool to user's stack."""
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    form = await request.form()
    tool_slug = str(form.get('tool_slug', '')).strip()
    if not tool_slug:
        return RedirectResponse("/dashboard/my-stack", status_code=303)

    db = request.state.db
    # Ensure stack exists
    stack, _ = await get_user_stack(db, user['id'])
    if not stack:
        await create_user_stack(db, user['id'])
        stack, _ = await get_user_stack(db, user['id'])

    tool = await get_tool_by_slug(db, tool_slug)
    if tool and stack:
        await add_tool_to_user_stack(db, stack['id'], tool['id'])

    return RedirectResponse("/dashboard/my-stack", status_code=303)


@router.post("/dashboard/readiness-update", response_class=HTMLResponse)
async def readiness_update(request: Request, field: str = Form(""), value: str = Form(""), tool_id: str = Form("")):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    maker_id = user.get('maker_id')

    # Maker-level fields
    if field in ('bio', 'avatar_url', 'url') and maker_id:
        await update_maker(db, maker_id, **{field: value.strip()})
    # Tool-level fields
    elif field == 'replaces' and tool_id:
        try:
            tid = int(tool_id)
            tool = await get_tool_by_id(db, tid)
            if tool and tool.get('maker_id') == maker_id:
                await update_tool(db, tid, replaces=value.strip())
        except (ValueError, TypeError):
            pass

    return RedirectResponse("/dashboard", status_code=303)


@router.post("/dashboard/my-stack/remove")
async def remove_from_my_stack(request: Request):
    """Remove a tool from user's stack."""
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    form = await request.form()
    tool_slug = str(form.get('tool_slug', '')).strip()

    db = request.state.db
    stack, _ = await get_user_stack(db, user['id'])
    tool = await get_tool_by_slug(db, tool_slug)
    if stack and tool:
        await remove_tool_from_user_stack(db, stack['id'], tool['id'])

    return RedirectResponse("/dashboard/my-stack", status_code=303)


# ── Purchases (redirects to dashboard — selling paused) ──────────────────

@router.get("/dashboard/purchases")
async def dashboard_purchases(request: Request):
    return RedirectResponse(url="/dashboard", status_code=303)


# ── Welcome / Onboarding ───────────────────────────────────────────────

@router.get("/welcome")
async def welcome_page(request: Request):
    """Redirect to /setup — welcome content lives there now."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/setup?welcome=1", status_code=302)


@router.get("/welcome-old", response_class=HTMLResponse)
async def welcome_page_old(request: Request):
    """Old welcome page — kept for reference, not linked anywhere."""
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect
    d = request.state.db
    keys = await get_api_keys_for_user(d, user['id'])
    has_key = any(k['is_active'] for k in keys)
    new_key = request.query_params.get("new", "")

    _tc = await d.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")
    tool_count = (await _tc.fetchone())['cnt']

    from html import escape as _esc
    snippet_key = _esc(new_key) if (new_key and new_key.startswith('isk_')) else 'YOUR_KEY_HERE'

    # Step 1 content
    if new_key and new_key.startswith('isk_'):
        step1 = f'''<div style="background:rgba(110,231,183,0.1);border:1px solid rgba(110,231,183,0.3);border-radius:var(--radius-sm);padding:16px;margin-top:12px;">
            <p style="color:var(--ink);font-size:14px;font-weight:600;margin:0 0 8px;">Key created — copy it now:</p>
            <code id="welcome-key" style="display:block;padding:10px 14px;background:var(--ink);color:var(--slate);border-radius:var(--radius-sm);font-size:14px;word-break:break-all;">{_esc(new_key)}</code>
            <button onclick="navigator.clipboard.writeText(document.getElementById('welcome-key').textContent);this.textContent='Copied!'"
                class="btn btn-primary" style="margin-top:8px;font-size:13px;">Copy to Clipboard</button>
        </div>'''
    elif has_key:
        step1 = '<p style="color:var(--accent);font-weight:600;font-size:14px;margin-top:8px;">Done — you have an active API key.</p>'
    else:
        step1 = '''<form method="POST" action="/developer/create-key" style="margin-top:12px;">
            <input type="hidden" name="name" value="Default">
            <input type="hidden" name="redirect" value="/welcome">
            <button type="submit" class="btn btn-primary" style="font-size:15px;padding:12px 24px;">Create Free API Key</button>
        </form>
        <p style="font-size:12px;color:var(--ink-muted);margin-top:8px;">Unlocks personalized recommendations and migration intelligence.</p>'''

    body = f'''
    <div class="container" style="max-width:640px;padding:48px 24px;">
        <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);margin:0 0 8px;">Welcome to IndieStack</h1>
        <p style="color:var(--ink-muted);font-size:16px;margin:0 0 32px;">Three steps to give your AI access to {tool_count}+ developer tools.</p>

        <div class="card" style="padding:24px;margin-bottom:16px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
                <div style="width:32px;height:32px;border-radius:50%;background:var(--accent);color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0;">1</div>
                <h2 style="font-family:var(--font-display);font-size:18px;margin:0;color:var(--ink);">Create your API key</h2>
            </div>
            <p style="font-size:14px;color:var(--ink-muted);margin:4px 0 0;padding-left:44px;">More queries, personalized recommendations, citation tracking.</p>
            <div style="padding-left:44px;">{step1}</div>
        </div>

        <div class="card" style="padding:24px;margin-bottom:16px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
                <div style="width:32px;height:32px;border-radius:50%;background:{"var(--accent)" if has_key or new_key else "var(--border)"};color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0;">2</div>
                <h2 style="font-family:var(--font-display);font-size:18px;margin:0;color:var(--ink);">Install the MCP server</h2>
            </div>
            <div style="padding-left:44px;margin-top:8px;">
                <a href="/setup" class="btn btn-primary" style="font-size:14px;padding:10px 20px;text-decoration:none;">View install instructions</a>
                <p style="font-size:12px;color:var(--ink-muted);margin:8px 0 0;">Claude Code, Cursor, Windsurf, and more.</p>
            </div>
        </div>

        <div class="card" style="padding:24px;margin-bottom:32px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
                <div style="width:32px;height:32px;border-radius:50%;background:var(--border);color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;flex-shrink:0;">3</div>
                <h2 style="font-family:var(--font-display);font-size:18px;margin:0;color:var(--ink);">Try a search</h2>
            </div>
            <div style="padding-left:44px;margin-top:8px;">
                <p style="font-size:14px;color:var(--ink-muted);margin:0;">Ask your AI agent:</p>
                <code style="display:block;padding:12px 16px;background:var(--cream-dark);border-radius:var(--radius-sm);font-size:14px;color:var(--accent);margin-top:8px;">
                    "Find me a privacy-friendly analytics tool"
                </code>
            </div>
        </div>

        <div style="display:flex;gap:12px;justify-content:center;">
            <a href="/dashboard" class="btn btn-primary" style="padding:12px 24px;">Go to Dashboard</a>
            <a href="/explore" class="btn btn-secondary" style="padding:12px 24px;">Explore the Catalog</a>
        </div>
    </div>'''

    return HTMLResponse(page_shell("Welcome — IndieStack", body, user=user))


# ── Developer API Keys ──────────────────────────────────────────────────

@router.get("/developer", response_class=HTMLResponse)
async def developer_page(request: Request):
    user = request.state.user

    # Logged-in users go to dashboard (API key management lives there now)
    if user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/dashboard", status_code=302)

    # Public API docs for logged-out visitors
    if not user:
        public_body = f'''
    <div class="container" style="max-width:800px;padding:48px 24px;">
        <div style="margin-bottom:32px;text-align:center;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin:0 0 12px;">Give your AI agent access to 3,100+ developer tools</h1>
            <p style="color:var(--ink-muted);font-size:17px;margin:0;max-width:560px;margin-left:auto;margin-right:auto;line-height:1.6;">
                Without IndieStack, your AI writes infrastructure from scratch. With IndieStack, it finds proven tools first.
            </p>
        </div>

        <div style="text-align:center;padding:24px;margin-bottom:32px;background:linear-gradient(135deg,#1A2D4A,#0F1D30);border-radius:var(--radius);border:1px solid rgba(0,212,245,0.2);">
            <p style="color:#fff;font-size:16px;font-weight:600;margin:0 0 4px;">Everything is free &mdash; unlimited searches</p>
            <p style="color:rgba(255,255,255,0.6);font-size:13px;margin:0 0 16px;">Create a key for personalized recommendations and migration intelligence.</p>
            <a href="/login?next=/welcome" class="btn btn-primary" style="font-size:15px;padding:12px 32px;background:var(--accent);color:#0F1D30;border:none;border-radius:8px;font-weight:600;text-decoration:none;">
                Sign in to create your API key
            </a>
        </div>

        <details style="margin-bottom:24px;">
            <summary style="cursor:pointer;font-family:var(--font-display);font-size:20px;color:var(--ink);padding:12px 0;list-style:none;">
                <span style="margin-right:8px;">&#9654;</span> API Documentation
            </summary>

            <div class="card" style="padding:24px;margin-top:12px;margin-bottom:24px;">
                <h2 style="font-family:var(--font-display);font-size:20px;margin:0 0 16px;color:var(--ink);">Endpoints</h2>

                <div style="margin-bottom:20px;">
                    <div style="font-size:13px;font-weight:700;color:var(--accent);font-family:var(--font-mono);margin-bottom:4px;">GET /api/tools/search?q=&lt;query&gt;</div>
                    <p style="font-size:13px;color:var(--ink-muted);margin:0;">Search the catalog by keyword. Returns matching tools with scores.</p>
                    <pre style="background:var(--terracotta);color:var(--slate);padding:14px;border-radius:var(--radius-sm);font-size:13px;font-family:var(--font-mono);overflow-x:auto;margin:8px 0 0;">curl "{BASE_URL}/api/tools/search?q=analytics&amp;key=isk_your_key"</pre>
                </div>

                <div style="margin-bottom:20px;">
                    <div style="font-size:13px;font-weight:700;color:var(--accent);font-family:var(--font-mono);margin-bottom:4px;">GET /api/tools/&lt;slug&gt;</div>
                    <p style="font-size:13px;color:var(--ink-muted);margin:0;">Get full details for a single tool by its slug.</p>
                    <pre style="background:var(--terracotta);color:var(--slate);padding:14px;border-radius:var(--radius-sm);font-size:13px;font-family:var(--font-mono);overflow-x:auto;margin:8px 0 0;">curl "{BASE_URL}/api/tools/my-tool?key=isk_your_key"</pre>
                </div>

                <div style="margin-bottom:20px;">
                    <div style="font-size:13px;font-weight:700;color:var(--accent);font-family:var(--font-mono);margin-bottom:4px;">GET /api/tools/index</div>
                    <p style="font-size:13px;color:var(--ink-muted);margin:0;">List all tools in the catalog. Supports pagination.</p>
                </div>

                <div>
                    <div style="font-size:13px;font-weight:700;color:var(--accent);font-family:var(--font-mono);margin-bottom:4px;">GET /api/categories</div>
                    <p style="font-size:13px;color:var(--ink-muted);margin:0;">List all tool categories.</p>
                </div>
            </div>

            <div class="card" style="padding:24px;margin-bottom:24px;">
                <h2 style="font-family:var(--font-display);font-size:20px;margin:0 0 16px;color:var(--ink);">Rate Limits</h2>
                <table style="width:100%;border-collapse:collapse;font-size:14px;">
                    <thead><tr style="border-bottom:2px solid var(--border);">
                        <th style="padding:10px;text-align:left;font-size:13px;color:var(--ink-muted);">Tier</th>
                        <th style="padding:10px;text-align:right;font-size:13px;color:var(--ink-muted);">Limit</th>
                    </tr></thead>
                    <tbody>
                        <tr style="border-bottom:1px solid var(--border);">
                            <td style="padding:10px;color:var(--ink);">No API key</td>
                            <td style="padding:10px;text-align:right;font-weight:600;color:var(--ink);">3 / day</td>
                        </tr>
                        <tr style="border-bottom:1px solid var(--border);">
                            <td style="padding:10px;color:var(--ink);">Free API key</td>
                            <td style="padding:10px;text-align:right;font-weight:600;color:var(--ink);">10 / month</td>
                        </tr>
                        <tr>
                            <td style="padding:10px;color:var(--ink);">Pro <span style="background:var(--accent);color:white;font-size:10px;font-weight:700;padding:2px 6px;border-radius:999px;margin-left:4px;">PRO</span></td>
                            <td style="padding:10px;text-align:right;font-weight:600;color:var(--accent);">1,000 / month</td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <div class="card" style="padding:24px;margin-bottom:24px;">
                <h2 style="font-family:var(--font-display);font-size:20px;margin:0 0 12px;color:var(--ink);">MCP Server</h2>
                <p style="font-size:13px;color:var(--ink-muted);margin:0 0 12px;">
                    Add IndieStack as a tool source for Claude Code, Cursor, or any MCP-compatible agent.
                </p>
                <pre style="background:var(--terracotta);color:var(--slate);padding:14px;border-radius:var(--radius-sm);font-size:13px;font-family:var(--font-mono);overflow-x:auto;">claude mcp add indiestack -- uvx --from indiestack indiestack-mcp</pre>
            </div>
        </details>
    </div>'''
        return HTMLResponse(page_shell("Developer API — IndieStack", public_body, user=None))

    new_key = request.query_params.get("new", "")
    db = request.state.db
    keys = await get_api_keys_for_user(db, user['id'])
    usage = await get_api_key_usage_stats(db, user['id'], days=30)
    usage_map = {u['id']: u['request_count'] for u in usage}

    # Determine API key for install snippet
    from html import escape as _escape
    snippet_key = _escape(new_key) if (new_key and new_key.startswith('isk_')) else 'your-api-key-here'

    # Load developer profile (from first active API key)
    profile_html = ''
    if keys:
        first_key_id = keys[0]['id'] if keys else None
        if first_key_id:
            profile = await get_developer_profile(db, first_key_id)
            if profile and profile.get('search_count', 0) > 0:
                import json as _json
                interests = _json.loads(profile['interests']) if isinstance(profile['interests'], str) else profile['interests']
                tech_stack = _json.loads(profile['tech_stack']) if isinstance(profile['tech_stack'], str) else profile['tech_stack']
                favorites = _json.loads(profile['favorite_tools']) if isinstance(profile['favorite_tools'], str) else profile['favorite_tools']
                enabled = profile.get('personalization_enabled', 1)

                # Interest pills
                interest_pills = ''
                for cat, score in sorted(interests.items(), key=lambda x: -x[1])[:8]:
                    level = 'high' if score >= 0.7 else ('medium' if score >= 0.4 else 'low')
                    color = 'var(--success-text)' if level == 'high' else ('var(--gold)' if level == 'medium' else 'var(--ink-muted)')
                    cat_display = cat.replace('-', ' ').title()
                    interest_pills += f'<span style="display:inline-block;padding:4px 12px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid {color};color:{color};margin:2px;">{cat_display} ({level})</span>'

                # Tech stack pills
                tech_pills = ''.join(
                    f'<span style="display:inline-block;padding:4px 12px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid var(--accent);color:var(--accent);margin:2px;">{kw}</span>'
                    for kw in tech_stack[:8]
                ) if tech_stack else '<span style="color:var(--ink-muted);font-size:13px;">None inferred yet</span>'

                # Favorite tools
                fav_pills = ''.join(
                    f'<a href="/tool/{slug}" style="display:inline-block;padding:4px 12px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid var(--border);color:var(--ink-light);margin:2px;text-decoration:none;">{slug}</a>'
                    for slug in favorites[:6]
                ) if favorites else '<span style="color:var(--ink-muted);font-size:13px;">None yet</span>'

                toggle_text = 'Pause Personalization' if enabled else 'Resume Personalization'
                toggle_color = 'var(--ink-muted)' if enabled else 'var(--success-text)'

                profile_html = f'''
                <div id="profile" class="card" style="padding:24px;margin-bottom:32px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                        <h3 style="font-family:var(--font-display);font-size:20px;margin:0;">Your Profile</h3>
                        <span style="font-size:12px;color:var(--ink-muted);">{profile['search_count']} searches analyzed</span>
                    </div>
                    <p style="font-size:13px;color:var(--ink-muted);margin-bottom:16px;">
                        Built from your search patterns. We store category interests and tech keywords — never raw queries.
                    </p>
                    <div style="margin-bottom:16px;">
                        <div style="font-size:13px;font-weight:600;color:var(--ink-light);margin-bottom:8px;">Interests</div>
                        <div style="display:flex;flex-wrap:wrap;gap:4px;">{interest_pills if interest_pills else '<span style="color:var(--ink-muted);font-size:13px;">None yet</span>'}</div>
                    </div>
                    <div style="margin-bottom:16px;">
                        <div style="font-size:13px;font-weight:600;color:var(--ink-light);margin-bottom:8px;">Inferred Stack</div>
                        <div style="display:flex;flex-wrap:wrap;gap:4px;">{tech_pills}</div>
                    </div>
                    <div style="margin-bottom:24px;">
                        <div style="font-size:13px;font-weight:600;color:var(--ink-light);margin-bottom:8px;">Favorite Tools</div>
                        <div style="display:flex;flex-wrap:wrap;gap:4px;">{fav_pills}</div>
                    </div>
                    <div style="display:flex;gap:12px;">
                        <form method="POST" action="/developer/toggle-personalization" style="margin:0;">
                            <button type="submit" class="btn btn-secondary" style="font-size:13px;padding:8px 16px;color:{toggle_color};">{toggle_text}</button>
                        </form>
                        <form method="POST" action="/developer/clear-profile" style="margin:0;"
                              onsubmit="return confirm('Clear your preferences? Your profile will rebuild from scratch.')">
                            <button type="submit" class="btn btn-secondary" style="font-size:13px;padding:8px 16px;color:var(--danger);">Clear Preferences</button>
                        </form>
                    </div>
                </div>
                '''

    # Show full key once after creation
    new_key_html = ""
    if new_key and new_key.startswith("isk_"):
        new_key_html = f'''
        <div class="card" style="border-left:4px solid var(--success-text);margin-bottom:24px;padding:20px;">
            <h3 style="margin:0 0 8px;font-family:var(--font-display);font-size:18px;color:var(--ink);">Key Created</h3>
            <p style="color:var(--ink-muted);font-size:14px;margin:0 0 12px;">
                Copy this key now &mdash; you won&rsquo;t be able to see it again.
            </p>
            <code id="new-key-value" style="font-family:var(--font-mono);font-size:14px;background:var(--terracotta);
                         color:var(--slate);padding:10px 14px;border-radius:var(--radius-sm);display:block;
                         word-break:break-all;">{escape(new_key)}</code>
            <button onclick="navigator.clipboard.writeText(document.getElementById('new-key-value').textContent);this.textContent='Copied!'"
                    class="btn btn-primary" style="margin-top:12px;font-size:13px;">
                Copy to Clipboard
            </button>
        </div>'''

    # Keys table rows
    key_rows = ""
    for k in keys:
        count = usage_map.get(k['id'], 0)
        status = '<span class="badge-success" style="font-size:11px;padding:2px 8px;">Active</span>' if k['is_active'] else '<span class="badge-danger" style="font-size:11px;padding:2px 8px;">Revoked</span>'
        last_used = escape(str(k['last_used_at'] or 'Never'))
        revoke_btn = ""
        if k['is_active']:
            revoke_btn = f'''
            <form method="POST" action="/developer/revoke-key" style="display:inline;">
                <input type="hidden" name="key_id" value="{k['id']}">
                <button type="submit" class="btn btn-secondary"
                        style="font-size:11px;padding:3px 10px;"
                        onclick="return confirm('Revoke this key? This cannot be undone.')">Revoke</button>
            </form>'''
        key_rows += f'''
        <tr style="border-bottom:1px solid var(--border);">
            <td style="padding:10px;font-family:var(--font-mono);font-size:13px;">{escape(k['key_preview'])}</td>
            <td style="padding:10px;">{escape(k['name'])}</td>
            <td style="padding:10px;">{status}</td>
            <td style="padding:10px;text-align:right;font-weight:600;">{count}</td>
            <td style="padding:10px;font-size:12px;color:var(--ink-muted);">{last_used}</td>
            <td style="padding:10px;">{revoke_btn}</td>
        </tr>'''

    empty_row = '<tr><td colspan="6" style="padding:24px;text-align:center;color:var(--ink-muted);">No API keys yet. Create one to get started.</td></tr>'

    onboarding_card = ''
    if not keys:
        onboarding_card = '''
        <div style="background:linear-gradient(135deg,#1A2D4A,#0F1D30);border:1px solid rgba(0,212,245,0.2);
                    border-radius:var(--radius);padding:32px;margin-bottom:24px;text-align:center;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:#fff;margin:0 0 8px;">
                Create your API key
            </h2>
            <p style="color:rgba(255,255,255,0.7);font-size:15px;margin:0 0 24px;max-width:460px;margin-left:auto;margin-right:auto;line-height:1.6;">
                An API key unlocks more queries, personalized recommendations, and citation tracking.
            </p>
            <form method="POST" action="/developer/create-key">
                <input type="hidden" name="name" value="Default">
                <button type="submit" class="btn btn-primary" style="font-size:16px;padding:14px 32px;">
                    Create Free API Key
                </button>
            </form>
            <p style="color:rgba(255,255,255,0.4);font-size:12px;margin:12px 0 0;">
                All searches are free and unlimited. Create a key for personalized recommendations.
            </p>
        </div>'''

    # Agent Activity
    action_counts = await get_agent_action_counts(db, user['id'], days=30)
    action_log = await get_agent_action_log(db, user['id'], limit=10)

    rec_count = action_counts.get('recommend', 0)
    short_count = action_counts.get('shortlist', 0)
    outcome_count = action_counts.get('report_outcome', 0)
    ok_count = action_counts.get('outcomes_success', 0)
    fail_count = action_counts.get('outcomes_fail', 0)
    integ_count = action_counts.get('confirm_integration', 0)
    submit_count = action_counts.get('submit_tool', 0)
    has_activity = rec_count or short_count or outcome_count or integ_count or submit_count

    log_rows = ''
    for a in action_log:
        ts = a['created_at'][:16].replace('T', ' ') if a.get('created_at') else ''
        action_label = a['action'].replace('_', ' ').title()
        tools = escape(a['tool_slug'])
        if a.get('tool_b_slug'):
            tools += f" + {escape(a['tool_b_slug'])}"
        ctx = f" &mdash; {escape(a['query_context'][:80])}" if a.get('query_context') else ''
        log_rows += f'<tr><td style="padding:8px 10px;color:var(--ink-muted);font-size:13px;white-space:nowrap;">{ts}</td><td style="padding:8px 10px;">{action_label}</td><td style="padding:8px 10px;">{tools}{ctx}</td></tr>'

    agent_activity_html = f'''
    <div class="card" style="margin-top:32px;">
        <h2 style="font-family:var(--font-display);font-size:22px;margin-bottom:16px;">Agent Activity <span style="font-size:13px;color:var(--ink-muted);font-weight:400;">last 30 days</span></h2>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:16px;margin-bottom:24px;">
            <div style="text-align:center;"><div style="font-size:28px;font-weight:700;color:var(--accent);">{rec_count}</div><div style="font-size:13px;color:var(--ink-muted);">Recommendations</div></div>
            <div style="text-align:center;"><div style="font-size:28px;font-weight:700;color:var(--ink);">{short_count}</div><div style="font-size:13px;color:var(--ink-muted);">Shortlisted</div></div>
            <div style="text-align:center;"><div style="font-size:28px;font-weight:700;color:var(--ink);">{outcome_count}</div><div style="font-size:13px;color:var(--ink-muted);">Outcomes ({ok_count} ok, {fail_count} fail)</div></div>
            <div style="text-align:center;"><div style="font-size:28px;font-weight:700;color:var(--ink);">{integ_count}</div><div style="font-size:13px;color:var(--ink-muted);">Integrations</div></div>
        </div>
        {"<table style='width:100%;font-size:14px;border-collapse:collapse;'><thead><tr><th style='text-align:left;padding:8px 10px;border-bottom:2px solid var(--border);'>Time</th><th style='text-align:left;padding:8px 10px;border-bottom:2px solid var(--border);'>Action</th><th style='text-align:left;padding:8px 10px;border-bottom:2px solid var(--border);'>Tool(s)</th></tr></thead><tbody>" + log_rows + "</tbody></table>" if log_rows else "<p style='color:var(--ink-muted);font-size:14px;'>No agent actions yet. Configure your API key in your AI agent to get started.</p>"}
    </div>
    ''' if has_activity or action_log else ''

    body = f'''
    <div class="container" style="max-width:800px;padding:48px 24px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;flex-wrap:wrap;gap:12px;">
            <div>
                <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);margin:0;">
                    Developer
                </h1>
                <p style="color:var(--ink-muted);font-size:15px;margin:4px 0 0;">
                    API keys for the IndieStack MCP server and REST API.
                </p>
            </div>
            <a href="/dashboard" class="btn btn-secondary" style="font-size:13px;">&larr; Dashboard</a>
        </div>

        {new_key_html}

        {profile_html}

        {onboarding_card}

        <div class="card" style="margin-bottom:24px;padding:24px;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
                <h2 style="font-family:var(--font-display);font-size:20px;margin:0;color:var(--ink);">Your API Keys</h2>
                <form method="POST" action="/developer/create-key">
                    <input type="hidden" name="name" value="Default">
                    <button type="submit" class="btn btn-primary" style="font-size:13px;">+ New Key</button>
                </form>
            </div>
            <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:14px;">
                <thead><tr style="border-bottom:2px solid var(--border);">
                    <th style="padding:10px;text-align:left;font-size:13px;color:var(--ink-muted);">Key</th>
                    <th style="padding:10px;text-align:left;font-size:13px;color:var(--ink-muted);">Name</th>
                    <th style="padding:10px;text-align:left;font-size:13px;color:var(--ink-muted);">Status</th>
                    <th style="padding:10px;text-align:right;font-size:13px;color:var(--ink-muted);">Requests (30d)</th>
                    <th style="padding:10px;text-align:left;font-size:13px;color:var(--ink-muted);">Last Used</th>
                    <th style="padding:10px;font-size:13px;"></th>
                </tr></thead>
                <tbody>{key_rows if key_rows else empty_row}</tbody>
            </table>
            </div>
        </div>

        {agent_activity_html}

        <div class="card" style="padding:24px;">
            <h2 style="font-family:var(--font-display);font-size:20px;margin:0 0 4px;color:var(--ink);">Quick Start</h2>
            <p style="font-size:14px;color:var(--ink-muted);margin:0 0 20px;">Integrate IndieStack into your workflow</p>

            <div style="position:relative;">
                <pre id="install-snippet" style="background:var(--terracotta);color:var(--slate);padding:16px;border-radius:var(--radius-sm);font-size:13px;
                            font-family:var(--font-mono);overflow-x:auto;margin-bottom:12px;line-height:1.6;"># Install the MCP server
# Claude Code
claude mcp add indiestack -- uvx --from indiestack indiestack-mcp

# Set your API key (optional — enables personalized recommendations)
export INDIESTACK_API_KEY="{snippet_key}"</pre>
                <button onclick="var text=document.getElementById('install-snippet').textContent.trim();navigator.clipboard.writeText(text).then(function(){{var b=event.target;b.textContent='Copied!';setTimeout(function(){{b.textContent='Copy';}},2000);}});"
                    style="position:absolute;top:10px;right:10px;background:rgba(255,255,255,0.12);color:var(--slate);border:1px solid rgba(255,255,255,0.2);
                           padding:4px 12px;border-radius:var(--radius-sm);font-size:12px;font-family:var(--font-body);cursor:pointer;
                           min-height:44px;min-width:44px;display:flex;align-items:center;justify-content:center;">Copy</button>
            </div>

            <p style="font-size:13px;color:var(--ink-muted);margin:0 0 8px;line-height:1.5;">
                With an API key, searches build your preference profile for personalized recommendations.
                We store category interests only &mdash; never raw queries.
            </p>
            <a href="#profile" style="font-size:13px;color:var(--accent);text-decoration:none;">Learn how personalization works &rarr;</a>

            <div style="margin-top:24px;padding-top:24px;border-top:1px solid var(--border);">
                <h3 style="font-size:15px;margin:0 0 8px;color:var(--ink);">REST API</h3>
                <p style="font-size:13px;color:var(--ink-muted);margin:0 0 8px;">Query the API directly with your key as a query parameter.</p>
                <pre style="background:var(--terracotta);color:var(--slate);padding:14px;border-radius:var(--radius-sm);font-size:13px;
                            font-family:var(--font-mono);overflow-x:auto;margin-bottom:20px;">curl &quot;{BASE_URL}/api/tools/search?q=analytics&amp;key={snippet_key}&quot;</pre>

                <p style="font-size:13px;color:var(--ink-muted);margin:0 0 8px;">Or use the Authorization header:</p>
                <pre style="background:var(--terracotta);color:var(--slate);padding:14px;border-radius:var(--radius-sm);font-size:13px;
                            font-family:var(--font-mono);overflow-x:auto;">curl -H &quot;Authorization: Bearer {snippet_key}&quot; &quot;{BASE_URL}/api/tools/search?q=analytics&quot;</pre>
            </div>
        </div>
    </div>'''

    return HTMLResponse(page_shell("Developer — IndieStack", body, user=user))


@router.post("/developer/create-key")
async def developer_create_key(request: Request):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    form = await request.form()
    name = str(form.get("name", "Default")).strip()[:50] or "Default"

    db = request.state.db
    # Max 1 active key per user — rate limit is per-user so multiple keys don't help
    max_keys = 1
    keys = await get_api_keys_for_user(db, user['id'])
    active = [k for k in keys if k['is_active']]
    if len(active) >= max_keys:
        return RedirectResponse(url="/dashboard", status_code=303)

    result = await create_api_key(db, user['id'], name)
    await track_event(db, 'key_created', user_id=user['id'])
    redir = str(form.get("redirect", "/dashboard")).strip()
    if not redir.startswith("/") or redir.startswith("//"):
        redir = "/developer"
    return RedirectResponse(url=f"{redir}?new={result['key']}", status_code=303)


@router.post("/developer/revoke-key")
async def developer_revoke_key(request: Request):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    form = await request.form()
    try:
        key_id = int(form.get("key_id", 0))
    except (ValueError, TypeError):
        return RedirectResponse(url="/developer", status_code=303)

    await revoke_api_key(request.state.db, key_id, user['id'])
    return RedirectResponse(url="/developer", status_code=303)


@router.post("/dashboard/api-keys/{key_id}/scope")
async def toggle_key_scope(request: Request, key_id: int):
    user = request.state.user
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    keys = await get_api_keys_for_user(request.state.db, user['id'])
    current_key = next((k for k in keys if k['id'] == key_id), None)
    if not current_key:
        return RedirectResponse(url="/developer", status_code=303)
    new_scopes = "read" if current_key.get('scopes', 'read') == 'read,write' else "read,write"
    await update_api_key_scopes(request.state.db, key_id, user['id'], new_scopes)
    return RedirectResponse(url="/developer", status_code=303)


@router.post("/developer/toggle-personalization")
async def toggle_personalization_route(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse("/login?next=/developer", status_code=303)
    db_conn = request.state.db
    keys = await get_api_keys_for_user(db_conn, user['id'])
    if keys:
        await toggle_personalization(db_conn, keys[0]['id'])
    return RedirectResponse("/developer", status_code=303)


@router.post("/developer/clear-profile")
async def clear_profile_route(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse("/login?next=/developer", status_code=303)
    db_conn = request.state.db
    keys = await get_api_keys_for_user(db_conn, user['id'])
    if keys:
        await clear_developer_profile(db_conn, keys[0]['id'])
    return RedirectResponse("/developer", status_code=303)


# ── Data Export (Pro) ────────────────────────────────────────────────────

@router.get("/dashboard/export")
async def dashboard_export(request: Request):
    """Export tools & analytics data for Pro subscribers."""
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    # Export is free for everyone now
    maker_id = user.get('maker_id')
    fmt = request.query_params.get('format', 'json').lower()
    if fmt not in ('json', 'csv'):
        fmt = 'json'

    # Gather tools with basic analytics
    tools_data = []
    if maker_id:
        tools = await get_tools_by_maker(db, maker_id)
        for t in tools:
            # Per-tool citation count (all time)
            cit_cursor = await db.execute(
                "SELECT COUNT(*) as cnt FROM agent_citations WHERE tool_id = ?",
                (t['id'],),
            )
            cit_row = await cit_cursor.fetchone()
            citation_count = cit_row['cnt'] if cit_row else 0

            tools_data.append({
                'name': t['name'],
                'slug': t['slug'],
                'category': t.get('category_name', ''),
                'description': t.get('description', ''),
                'created_at': t.get('created_at', ''),
                'status': t.get('status', ''),
                'upvotes': t.get('upvote_count', 0),
                'saves': t.get('save_count', 0),
                'mcp_views': t.get('mcp_view_count', 0),
                'agent_citations': citation_count,
            })

    if fmt == 'json':
        export = {
            'exported_at': datetime.now(timezone.utc).isoformat(),
            'user': user.get('username', user.get('email', '')),
            'tools': tools_data,
        }
        content = json.dumps(export, indent=2, default=str)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": 'attachment; filename="indiestack-export.json"'},
        )

    # CSV format
    output = io.StringIO()
    fieldnames = ['name', 'slug', 'category', 'description', 'created_at',
                  'status', 'upvotes', 'saves', 'mcp_views', 'agent_citations']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in tools_data:
        writer.writerow(row)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="indiestack-export.csv"'},
    )

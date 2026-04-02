"""Admin Command Center — unified dashboard with 4 tabs: Overview, Tools, People, Growth."""

import json
import secrets as _secrets
from datetime import datetime
from html import escape
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell, pixel_icon_svg
from indiestack.db import (get_pending_tools, get_all_tools_admin, update_tool_status, toggle_verified, toggle_ejectable,
                           bulk_create_tools, get_purchase_stats, set_featured_tool, clear_featured_tool,
                           get_collection_by_slug, get_all_reviews_admin, delete_review, get_all_makers_admin, update_maker,
                           toggle_tool_boost, create_stack, get_all_stacks, add_tool_to_stack, remove_tool_from_stack, delete_stack,
                           get_tool_by_id, get_makers_in_category, get_all_purchases_admin,
                           update_tool, get_all_categories, delete_tool, get_pro_subscriber_stats,
                           create_notification, get_pending_avatars, update_user,
                           get_follow_through_rate, get_outcome_stats, get_search_gaps)
from indiestack.email import send_email, tool_approved_html
from indiestack.auth import check_admin_session, make_session_token, ADMIN_PASSWORD
from indiestack.main import _check_admin_rate_limit, _record_admin_attempt, _clear_admin_attempts

# New imports for consolidated admin
from indiestack.routes.admin_helpers import (
    time_ago, kpi_card, pending_alert_bar, status_badge, role_badge,
    tab_nav, growth_sub_nav, tools_sub_nav, row_bg, data_table
)
from indiestack.routes.admin_analytics import (
    render_charts_section, render_tables_section, render_funnels_section,
    render_search_section, render_growth_section
)
from indiestack.routes.admin_outreach import (
    render_email_section, render_magic_section, render_makers_section,
    render_stale_section, render_social_section, handle_outreach_post
)

router = APIRouter()


# ── Outreach actions to delegate ─────────────────────────────────────────
OUTREACH_ACTIONS = {
    'send_totw', 'send_digest_test', 'send_digest_all',
    'send_launch_test', 'send_launch_all',
    'send_ph_test', 'send_ph_all',
    'send_maker_countdown_test', 'send_maker_countdown_all',
    'test_email', 'blast_email', 'send_preview',
    'generate_magic', 'generate_all_csv', 'send_nudge', 'send_stripe_nudge'
}


# ── Login form ───────────────────────────────────────────────────────────

def login_form_html(error: str = "") -> str:
    alert = f'<div class="alert alert-error">{escape(error)}</div>' if error else ''
    return f"""
    <div style="display:flex;justify-content:center;align-items:center;min-height:60vh;">
        <div class="card" style="max-width:400px;width:100%;">
            <h2 style="font-family:var(--font-display);font-size:24px;text-align:center;margin-bottom:24px;color:var(--ink);">
                Admin Login
            </h2>
            {alert}
            <form method="post" action="/admin">
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" class="form-input" required
                           placeholder="Enter admin password">
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;">
                    Sign In
                </button>
            </form>
        </div>
    </div>
    """


# ── GET /admin ───────────────────────────────────────────────────────────

@router.get("/admin", response_class=HTMLResponse)
async def admin_get(request: Request):
    if not check_admin_session(request):
        return HTMLResponse(page_shell("Admin Login", login_form_html(), user=request.state.user))

    db = request.state.db
    tab = request.query_params.get('tab', 'overview')
    toast = request.query_params.get('toast', '')

    pending = await get_pending_tools(db)
    pending_count = len(pending)

    toast_html = ''
    if toast:
        toast_html = f'<div style="background:#DCFCE7;color:#166534;padding:10px 16px;border-radius:var(--radius-sm);margin-bottom:16px;font-size:14px;">{escape(toast)}</div>'

    if tab == 'overview':
        section_html = await render_overview(db, request, pending)
    elif tab == 'tools':
        section_html = await render_tools_tab(db, request, pending)
    elif tab == 'people':
        section_html = await render_people_tab(db, request)
    elif tab == 'growth':
        section_html = await render_growth_tab(db, request)
    elif tab == 'content':
        # Legacy redirect — content moved to tools sub-tabs
        section_html = await render_tools_tab(db, request, pending)
        tab = 'tools'
    else:
        tab = 'overview'
        section_html = await render_overview(db, request, pending)

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:1280px;">
        <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);margin:0;">
                Command Center
            </h1>
            <span style="font-size:13px;color:var(--ink-muted);">{datetime.utcnow().strftime("%A, %d %b %Y · %H:%M UTC")}</span>
        </div>
        {toast_html}
        {tab_nav(tab, pending_count)}
        {pending_alert_bar(pending_count) if tab != 'tools' else ''}
        {section_html}
    </div>
    """
    return HTMLResponse(page_shell("Admin", body, user=request.state.user))


# ── Overview Tab ─────────────────────────────────────────────────────────

async def render_overview(db, request, pending):
    """Overview tab: two-column command centre — Action Items + Today's Pulse."""
    from datetime import datetime, timedelta
    pending_count = len(pending)
    pending_avatars = await get_pending_avatars(db)

    # ── LEFT COLUMN: Action Items ──

    # Pending tools — ALL of them with approve/reject
    pending_html = ''
    if pending:
        bulk_html = ''
        if pending_count > 1:
            bulk_html = f'''
            <div style="display:flex;gap:8px;margin-bottom:12px;padding:10px 14px;background:var(--cream-dark);border-radius:var(--radius);align-items:center;">
                <form method="post" action="/admin" style="display:inline;">
                    <input type="hidden" name="action" value="approve_all">
                    <button type="submit" class="btn" style="background:#16a34a;color:white;padding:6px 16px;font-size:12px;font-weight:600;">
                        Approve All ({pending_count})
                    </button>
                </form>
                <form method="post" action="/admin" style="display:inline;">
                    <input type="hidden" name="action" value="reject_all">
                    <button type="submit" class="btn" style="background:#dc2626;color:white;padding:6px 16px;font-size:12px;font-weight:600;"
                            onclick="return confirm('Reject all {pending_count} pending tools?')">
                        Reject All
                    </button>
                </form>
            </div>
            '''
        cards = ''
        for t in pending:
            tid = t['id']
            name = escape(str(t['name']))
            tagline = escape(str(t['tagline']))
            # Quality flags from pre-screening
            qf_html = ''
            qf_raw = str(t.get('quality_flags', '') or '')
            if qf_raw:
                try:
                    import json as _json
                    qf_list = _json.loads(qf_raw)
                    if qf_list:
                        pills = ''
                        for qf in qf_list:
                            sev = qf.get('severity', 'info')
                            sev_color = {'error': '#dc2626', 'warning': '#d97706', 'info': '#6b7280'}.get(sev, '#6b7280')
                            pills += f'<span style="display:inline-block;font-size:10px;padding:2px 6px;border-radius:999px;background:{sev_color}22;color:{sev_color};font-weight:600;margin-right:4px;" title="{escape(str(qf.get("message", "")))}">{escape(str(qf.get("type", "")))}</span>'
                        qf_html = f'<div style="margin-top:4px;">{pills}</div>'
                except Exception:
                    pass
            cards += f"""
            <div class="card" style="margin-bottom:8px;padding:12px 14px;">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:180px;">
                        <strong style="font-size:14px;color:var(--ink);">{name}</strong>
                        <span style="color:var(--ink-muted);font-size:12px;margin-left:6px;">{tagline}</span>
                        {qf_html}
                    </div>
                    <div style="display:flex;gap:6px;">
                        <form method="post" action="/admin" style="margin:0;">
                            <input type="hidden" name="tool_id" value="{tid}">
                            <input type="hidden" name="action" value="approve">
                            <button type="submit" style="padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;
                                    cursor:pointer;background:#16a34a;color:white;border:none;">Approve</button>
                        </form>
                        <form method="post" action="/admin" style="margin:0;">
                            <input type="hidden" name="tool_id" value="{tid}">
                            <input type="hidden" name="action" value="reject">
                            <button type="submit" style="padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;
                                    cursor:pointer;background:#dc2626;color:white;border:none;">Reject</button>
                        </form>
                    </div>
                </div>
            </div>
            """
        pending_html = f"""
        <div style="margin-bottom:24px;">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:10px;">
                Pending Tools ({pending_count})
            </h3>
            {bulk_html}
            {cards}
        </div>
        """

    # Pending avatars
    avatars_html = ''
    if pending_avatars:
        avatar_cards = ''
        for a in pending_avatars:
            a_name = escape(str(a.get('name', '') or a.get('email', '')))
            avatar_cards += f"""
            <div class="card" style="padding:12px;text-align:center;width:120px;">
                {pixel_icon_svg(a['pixel_avatar'], size=40)}
                <p style="font-size:11px;color:var(--ink-muted);margin-top:6px;">{a_name}</p>
                <div style="display:flex;gap:4px;margin-top:6px;">
                    <form method="post" action="/admin" style="flex:1;">
                        <input type="hidden" name="action" value="approve_avatar">
                        <input type="hidden" name="user_id" value="{a['id']}">
                        <button type="submit" class="btn btn-primary" style="width:100%;padding:3px;font-size:10px;">&#10003;</button>
                    </form>
                    <form method="post" action="/admin" style="flex:1;">
                        <input type="hidden" name="action" value="reject_avatar">
                        <input type="hidden" name="user_id" value="{a['id']}">
                        <button type="submit" class="btn btn-secondary" style="width:100%;padding:3px;font-size:10px;">&#10007;</button>
                    </form>
                </div>
            </div>
            """
        avatars_html = f"""
        <div style="margin-bottom:24px;">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">Pending Avatars ({len(pending_avatars)})</h3>
            <div style="display:flex;flex-wrap:wrap;gap:12px;">{avatar_cards}</div>
        </div>
        """

    # Claim requests
    claim_cursor = await db.execute(
        """SELECT cr.id, cr.tool_id, cr.user_id, cr.created_at,
                  t.name as tool_name, t.slug as tool_slug,
                  u.name as user_name, u.email as user_email
           FROM claim_requests cr
           JOIN tools t ON t.id = cr.tool_id
           JOIN users u ON u.id = cr.user_id
           WHERE cr.status = 'pending'
           ORDER BY cr.created_at DESC""")
    claims = [dict(r) for r in await claim_cursor.fetchall()]
    claims_html = ''
    if claims:
        claim_cards = ''
        for c in claims:
            claim_cards += f'''
            <div class="card" style="padding:12px 14px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <a href="/tool/{escape(str(c['tool_slug']))}" style="font-weight:700;color:var(--ink);font-size:14px;">{escape(str(c['tool_name']))}</a>
                    <span style="color:var(--ink-muted);font-size:12px;margin-left:6px;">by {escape(str(c['user_name'] or c['user_email']))}</span>
                </div>
                <div style="display:flex;gap:6px;">
                    <form method="post" action="/admin" style="display:inline;">
                        <input type="hidden" name="action" value="approve_claim">
                        <input type="hidden" name="claim_id" value="{c['id']}">
                        <input type="hidden" name="tool_id" value="{c['tool_id']}">
                        <input type="hidden" name="user_id" value="{c['user_id']}">
                        <button type="submit" style="padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;
                                cursor:pointer;background:#16a34a;color:white;border:none;">Approve</button>
                    </form>
                    <form method="post" action="/admin" style="display:inline;">
                        <input type="hidden" name="action" value="reject_claim">
                        <input type="hidden" name="claim_id" value="{c['id']}">
                        <button type="submit" style="padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;
                                cursor:pointer;background:#dc2626;color:white;border:none;">Reject</button>
                    </form>
                </div>
            </div>'''
        claims_html = f"""
        <div style="margin-bottom:24px;">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:10px;">Claim Requests ({len(claims)})</h3>
            {claim_cards}
        </div>
        """

    # Flagged tools section
    from indiestack.db import get_flagged_tools
    flagged = await get_flagged_tools(db)
    flagged_html = ''
    if flagged:
        flag_type_labels = {
            'abandoned': 'Abandoned', 'misleading': 'Misleading',
            'not_indie': 'Not Indie', 'spam': 'Spam', 'other': 'Other'
        }
        flag_cards = ''
        for f in flagged:
            f_name = escape(str(f['name']))
            f_slug = escape(str(f['slug']))
            f_count = int(f['flag_count'])
            f_types = str(f['flag_types'] or '')
            type_pills = ''
            for ft in f_types.split(','):
                ft = ft.strip()
                if ft:
                    type_pills += f'<span style="display:inline-block;font-size:10px;padding:2px 6px;border-radius:999px;background:#dc262622;color:#dc2626;font-weight:600;margin-right:4px;">{escape(flag_type_labels.get(ft, ft))}</span>'
            flag_cards += f'''
            <div class="card" style="padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center;gap:8px;">
                <div>
                    <a href="/tool/{f_slug}" style="font-weight:700;font-size:13px;color:var(--ink);">{f_name}</a>
                    <span style="font-size:11px;color:var(--ink-muted);margin-left:4px;">{f_count} flag{"s" if f_count != 1 else ""}</span>
                    <div style="margin-top:2px;">{type_pills}</div>
                </div>
                <span style="font-size:12px;color:var(--ink-muted);">{escape(str(f['status']))}</span>
            </div>'''
        flagged_html = f'''
        <div style="margin-bottom:24px;">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:10px;">
                Flagged by Community ({len(flagged)})
            </h3>
            {flag_cards}
        </div>
        '''

    # Build left column
    left_col = pending_html + avatars_html + claims_html + flagged_html
    if not left_col.strip():
        left_col = '<div class="card" style="padding:32px;text-align:center;color:var(--ink-muted);font-size:15px;">All clear &mdash; nothing to review</div>'

    # ── RIGHT COLUMN: Today's Pulse ──
    # Use date() for comparisons — page_views uses 'T' separator, other tables use space
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM page_views WHERE date(timestamp) = date('now')")
    views_today = (await cursor.fetchone())['cnt']

    cursor = await db.execute("SELECT COUNT(DISTINCT visitor_id) as cnt FROM page_views WHERE date(timestamp) = date('now') AND visitor_id IS NOT NULL")
    unique_today = (await cursor.fetchone())['cnt']

    cursor = await db.execute("SELECT COUNT(*) as cnt FROM outbound_clicks WHERE date(created_at) = date('now')")
    clicks_today = (await cursor.fetchone())['cnt']

    cursor = await db.execute("SELECT COUNT(*) as cnt FROM search_logs WHERE date(created_at) = date('now')")
    searches_today = (await cursor.fetchone())['cnt']

    cursor = await db.execute("SELECT COUNT(*) as cnt FROM users WHERE date(created_at) = date('now')")
    signups_today = (await cursor.fetchone())['cnt']

    cursor = await db.execute("SELECT COUNT(*) as cnt FROM agent_citations WHERE date(created_at) = date('now')")
    ai_recs_today = (await cursor.fetchone())['cnt']

    follow_through = await get_follow_through_rate(db, 30)

    kpi_grid = f"""
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:20px;">
        {kpi_card("Page Views", f"{views_today:,}", color="var(--slate)")}
        {kpi_card("Unique Visitors", f"{unique_today:,}", color="var(--terracotta)")}
        {kpi_card("Outbound Clicks", f"{clicks_today:,}", color="#E2B764")}
        {kpi_card("Searches", f"{searches_today:,}", color="var(--accent)")}
        {kpi_card("Signups", f"{signups_today}", color="#16a34a")}
        {kpi_card("AI Recs", f"{ai_recs_today:,}", color="#7C3AED")}
    </div>
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px;padding:10px 14px;background:var(--cream-dark);border-radius:var(--radius-sm);">
        <span style="font-size:var(--heading-lg);font-weight:700;color:var(--accent);">{follow_through['rate']}%</span>
        <span style="font-size:var(--text-sm);color:var(--text-secondary);">Follow-through (30d) &mdash; {follow_through['details']:,} detail views / {follow_through['searches']:,} MCP searches</span>
    </div>
    """

    # Alerts strip
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM tools WHERE status='approved' AND created_at < datetime('now', '-90 days')"
    )
    stale_count = (await cursor.fetchone())['cnt']
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM search_logs WHERE result_count = 0 AND created_at >= datetime('now', '-30 days')"
    )
    search_gaps = (await cursor.fetchone())['cnt']

    alert_parts = []
    if stale_count > 0:
        alert_parts.append(f'<span style="color:#D97706;font-weight:600;">{stale_count} stale</span>')
    if search_gaps > 0:
        alert_parts.append(f'<span style="color:#DC2626;font-weight:600;">{search_gaps} gaps</span>')
    alerts_html = ''
    if alert_parts:
        alerts_html = f'<div style="font-size:12px;color:var(--ink-muted);margin-bottom:16px;padding:8px 12px;background:var(--cream-dark);border-radius:var(--radius-sm);">{" &middot; ".join(alert_parts)}</div>'

    # Last 5 submissions
    cursor = await db.execute(
        """SELECT t.name, t.status, t.created_at
           FROM tools t ORDER BY t.created_at DESC LIMIT 5"""
    )
    recent = await cursor.fetchall()
    recent_html = ''
    if recent:
        lines = ''
        for rt in recent:
            name = escape(str(rt['name']))
            status = str(rt['status'])
            ago = time_ago(rt.get('created_at'))
            dot_color = '#16a34a' if status == 'approved' else '#D97706' if status == 'pending' else '#991B1B'
            lines += f'<div style="font-size:12px;color:var(--ink);padding:4px 0;"><span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{dot_color};margin-right:6px;vertical-align:middle;"></span>{name} <span style="color:var(--ink-muted);">{ago}</span></div>'
        recent_html = f'<div style="margin-top:4px;"><h4 style="font-size:13px;color:var(--ink-muted);margin-bottom:8px;font-weight:600;">Last 5 Submissions</h4>{lines}</div>'

    # Quality score distribution (graceful if column doesn't exist yet)
    qs_html = ''
    try:
        qs_cursor = await db.execute("""
            SELECT
                COUNT(CASE WHEN quality_score = 0 THEN 1 END) as dead,
                COUNT(CASE WHEN quality_score > 0 AND quality_score <= 40 THEN 1 END) as low,
                COUNT(CASE WHEN quality_score > 40 AND quality_score <= 70 THEN 1 END) as mid,
                COUNT(CASE WHEN quality_score > 70 THEN 1 END) as high,
                ROUND(AVG(quality_score), 1) as avg_score
            FROM tools WHERE status = 'approved'
        """)
        qs = await qs_cursor.fetchone()
        qs_html = f'''
        <div style="margin-top:12px;padding:12px;border-radius:8px;background:var(--surface-alt);">
            <h4 style="font-size:13px;color:var(--ink-muted);margin-bottom:8px;font-weight:600;">Quality Score</h4>
            <div style="font-size:12px;color:var(--ink);">
                Avg: <strong>{qs["avg_score"] or 0}</strong> &nbsp;|&nbsp;
                High (&gt;70): {qs["high"]} &nbsp;|&nbsp;
                Mid (40–70): {qs["mid"]} &nbsp;|&nbsp;
                Low (1–40): {qs["low"]} &nbsp;|&nbsp;
                Dead (0): {qs["dead"]}
            </div>
        </div>
        '''
    except Exception:
        pass

    # ── Trust Layer Stats ──
    trust_html = ''
    try:
        outcome_stats = await get_outcome_stats(db)
        top_rows = ''
        for t in outcome_stats['top_tools']:
            t_name = escape(str(t.get('name') or t['tool_slug']))
            rate_color = '#16a34a' if t['rate'] >= 70 else '#D97706' if t['rate'] >= 40 else '#DC2626'
            top_rows += f'<div style="display:flex;justify-content:space-between;font-size:12px;padding:3px 0;"><span style="color:var(--ink);">{t_name}</span><span><span style="color:{rate_color};font-weight:600;">{t["rate"]}%</span> <span style="color:var(--ink-muted);">({t["total"]})</span></span></div>'

        trust_html = f'''
        <div style="margin-top:12px;padding:12px;border-radius:8px;background:var(--surface-alt);">
            <h4 style="font-size:13px;color:var(--ink-muted);margin-bottom:8px;font-weight:600;">Trust Layer</h4>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px;margin-bottom:8px;">
                <div style="color:var(--ink);">Reports (all): <strong>{outcome_stats["total_all"]}</strong></div>
                <div style="color:var(--ink);">Reports (30d): <strong>{outcome_stats["total_30d"]}</strong></div>
                <div style="color:var(--ink);">Tools with data: <strong>{outcome_stats["unique_tools"]}</strong></div>
                <div style="color:var(--ink);">Avg success: <strong>{outcome_stats["avg_rate"]}%</strong></div>
            </div>
            {f'<div style="border-top:1px solid var(--border);padding-top:8px;"><div style="font-size:11px;color:var(--ink-muted);margin-bottom:4px;font-weight:600;">Top Reported Tools</div>{top_rows}</div>' if top_rows else '<div style="font-size:12px;color:var(--ink-muted);font-style:italic;">No outcome reports yet</div>'}
        </div>
        '''
    except Exception:
        pass

    # ── Demand Gaps Panel ──
    gaps = await get_search_gaps(db, days=30, min_searches=2, limit=10)
    gaps_html = ""
    if gaps:
        gap_rows = "".join(
            f'<tr><td style="padding:8px 12px;font-weight:500;">{escape(str(g["query"]))}</td>'
            f'<td style="padding:8px 12px;text-align:center;">{g["count"]}</td>'
            f'<td style="padding:8px 12px;text-align:center;">{g["unique_sources"]}</td>'
            f'<td style="padding:8px 12px;color:var(--ink-muted);font-size:13px;">{escape(str(g["sources"]))}</td></tr>'
            for g in gaps
        )
        gaps_html = f'''
        <div style="margin-top:32px;">
            <h3 style="font-size:16px;font-weight:600;margin-bottom:12px;">Demand Gaps (30d)</h3>
            <p style="font-size:13px;color:var(--ink-muted);margin-bottom:12px;">Queries where agents found nothing — your tool acquisition priority list.</p>
            <table style="width:100%;border-collapse:collapse;">
                <thead><tr style="border-bottom:1px solid var(--border);">
                    <th style="padding:8px 12px;text-align:left;font-size:13px;">Query</th>
                    <th style="padding:8px 12px;text-align:center;font-size:13px;">Searches</th>
                    <th style="padding:8px 12px;text-align:center;font-size:13px;">Unique Agents</th>
                    <th style="padding:8px 12px;text-align:left;font-size:13px;">Source</th>
                </tr></thead>
                <tbody>{gap_rows}</tbody>
            </table>
        </div>'''

    # ── Hero stat strip queries ──
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")
    total_tools = (await cursor.fetchone())['cnt']

    cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
    total_users_count = (await cursor.fetchone())['cnt']

    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM search_logs WHERE source='mcp' AND date(created_at)=date('now')"
    )
    mcp_today = (await cursor.fetchone())['cnt']

    pro_stats = await get_pro_subscriber_stats(db)
    pro_count = pro_stats.get('active_count', 0) or 0
    mrr_pence = pro_stats.get('mrr_pence', 0) or 0

    # ── Activity feed (last 48h: signups, MCP searches, claims) ──
    cursor = await db.execute(
        "SELECT name as label, created_at FROM users "
        "WHERE created_at >= datetime('now', '-48 hours') ORDER BY created_at DESC LIMIT 15"
    )
    signup_feed = [('signup', str(r['label'] or ''), str(r['created_at'])) for r in await cursor.fetchall()]

    cursor = await db.execute(
        "SELECT query as label, created_at FROM search_logs "
        "WHERE source='mcp' AND created_at >= datetime('now', '-48 hours') ORDER BY created_at DESC LIMIT 15"
    )
    mcp_feed = [('mcp', str(r['label'] or ''), str(r['created_at'])) for r in await cursor.fetchall()]

    cursor = await db.execute(
        """SELECT t.name as label, cr.created_at FROM claim_requests cr
           JOIN tools t ON t.id=cr.tool_id
           WHERE cr.created_at >= datetime('now', '-48 hours')
           ORDER BY cr.created_at DESC LIMIT 8"""
    )
    claim_feed = [('claim', str(r['label'] or ''), str(r['created_at'])) for r in await cursor.fetchall()]

    feed_items = signup_feed + mcp_feed + claim_feed
    feed_items.sort(key=lambda x: x[2], reverse=True)
    feed_items = feed_items[:25]

    feed_rows = ''
    _type_cfg = {'signup': ('#16a34a', 'User'), 'mcp': ('#00D4F5', 'MCP'), 'claim': ('#E2B764', 'Claim')}
    for evt_type, lbl, ts in feed_items:
        color, badge = _type_cfg.get(evt_type, ('#6b7280', evt_type))
        ago = time_ago(ts)
        lbl_display = escape(lbl[:50] + ('…' if len(lbl) > 50 else ''))
        feed_rows += (
            f'<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border);">'
            f'<span style="display:inline-block;padding:2px 7px;border-radius:999px;font-size:10px;font-weight:700;background:{color}22;color:{color};flex-shrink:0;">{badge}</span>'
            f'<span style="font-size:13px;color:var(--ink);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{lbl_display}</span>'
            f'<span style="font-size:11px;color:var(--ink-muted);white-space:nowrap;">{ago}</span>'
            f'</div>'
        )

    if feed_rows:
        activity_html = (
            '<div style="margin-bottom:20px;">'
            '<h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:12px;">Live Activity</h3>'
            '<div class="card" style="padding:16px;max-height:400px;overflow-y:auto;">'
            + feed_rows +
            '</div></div>'
        )
    else:
        activity_html = (
            '<div style="margin-bottom:20px;">'
            '<h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:12px;">Live Activity</h3>'
            '<div class="card" style="padding:32px;text-align:center;color:var(--ink-muted);font-size:14px;">No activity in the last 48 hours</div>'
            '</div>'
        )

    hero_strip = f"""
    <div class="hero-strip" style="display:grid;grid-template-columns:repeat(6,1fr);gap:12px;margin-bottom:32px;">
        {kpi_card("Total Tools", f"{total_tools:,}", color="#1A2D4A")}
        {kpi_card("Total Users", f"{total_users_count:,}", color="var(--terracotta)")}
        {kpi_card("Searches Today", f"{searches_today:,}", color="var(--slate)")}
        {kpi_card("MCP Today", f"{mcp_today:,}", color="#16a34a")}
        {kpi_card("Pro Subscribers", f"{pro_count:,}", color="#7C3AED")}
        {kpi_card("MRR", f"£{mrr_pence / 100:.0f}", color="#E2B764")}
    </div>
    <style>
        @media(max-width:900px){{.hero-strip{{grid-template-columns:repeat(3,1fr)!important;}}}}
        @media(max-width:600px){{.hero-strip{{grid-template-columns:repeat(2,1fr)!important;}}}}
    </style>
    """

    right_col = f"""
    {activity_html}
    {alerts_html}
    {qs_html}
    {trust_html}
    {gaps_html}
    """

    return f"""
    {hero_strip}
    <div style="display:grid;grid-template-columns:3fr 2fr;gap:32px;align-items:start;">
        <div>{left_col}</div>
        <div>{right_col}</div>
    </div>
    <style>@media(max-width:768px){{[style*="grid-template-columns:3fr 2fr"]{{grid-template-columns:1fr!important;}}}}</style>
    """


# ── Tools Tab ────────────────────────────────────────────────────────────

async def render_tools_tab(db, request, pending):
    """Tools tab: sub-nav with Pending, All, Claims, Stacks, Reviews."""
    section = request.query_params.get('section', 'pending')
    pending_count = len(pending)
    html = tools_sub_nav(section, pending_count)

    if section == 'pending':
        html += await _render_tools_pending(db, request, pending)
    elif section == 'all':
        html += await _render_tools_all(db, request)
    elif section == 'claims':
        html += await _render_tools_claims(db)
    elif section == 'stacks':
        html += await _render_tools_stacks(db)
    elif section == 'reviews':
        html += await _render_tools_reviews(db)
    else:
        html += await _render_tools_pending(db, request, pending)

    return html


async def _render_tools_pending(db, request, pending):
    """Pending tools with bulk approve/reject."""
    pending_count = len(pending)
    html = f'<h2 style="font-family:var(--font-display);margin-bottom:16px;color:var(--ink);">Pending Review ({pending_count})</h2>'
    if pending:
        if pending_count > 1:
            html += f'''
            <div style="display:flex;gap:8px;margin-bottom:16px;padding:12px 16px;background:var(--cream-dark);border-radius:var(--radius);align-items:center;">
                <form method="post" action="/admin" style="display:inline;">
                    <input type="hidden" name="action" value="approve_all">
                    <button type="submit" class="btn" style="background:#16a34a;color:white;padding:8px 20px;font-weight:600;">
                        Approve All ({pending_count})
                    </button>
                </form>
                <form method="post" action="/admin" style="display:inline;">
                    <input type="hidden" name="action" value="reject_all">
                    <button type="submit" class="btn" style="background:#dc2626;color:white;padding:8px 20px;font-weight:600;"
                            onclick="return confirm('Reject all {pending_count} pending tools?')">
                        Reject All
                    </button>
                </form>
                <span style="color:var(--ink-muted);font-size:13px;margin-left:8px;">{pending_count} tool{"s" if pending_count != 1 else ""} waiting</span>
            </div>
            '''
        for t in pending:
            tid = t['id']
            name = escape(str(t['name']))
            tagline = escape(str(t['tagline']))
            t_url = escape(str(t['url']))
            maker = escape(str(t.get('maker_name', '')))
            cat = escape(str(t.get('category_name', '')))
            price_p = t.get('price_pence')
            price_str = f'\u00a3{price_p/100:.2f}' if price_p else 'Free'
            source = t.get('source_type', 'saas')

            # Enrichment badges
            domain_age = t.get('domain_age_days')
            if domain_age is not None:
                if domain_age < 30:
                    age_badge = f'<span style="background:#dc2626;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">{domain_age}d old</span>'
                elif domain_age < 90:
                    age_badge = f'<span style="background:#ca8a04;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">{domain_age}d old</span>'
                else:
                    yrs = domain_age // 365
                    age_badge = f'<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">{yrs}y old</span>' if yrs else f'<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">{domain_age}d old</span>'
            else:
                age_badge = '<span style="background:#6b7280;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">Age?</span>'

            free_tier = t.get('has_free_tier')
            if free_tier == 1:
                free_badge = '<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">Free tier</span>'
            elif free_tier == 0 and source == 'saas':
                free_badge = '<span style="background:#ca8a04;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">No free tier</span>'
            else:
                free_badge = ''

            social = t.get('social_mentions_count')
            if social is not None and social > 0:
                social_badge = f'<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">{social} HN</span>'
            elif social == 0:
                social_badge = '<span style="background:#dc2626;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">0 HN</span>'
            else:
                social_badge = ''

            health = t.get('health_status', 'unknown')
            if health == 'dead':
                health_badge = '<span style="background:#dc2626;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">Dead</span>'
            elif health == 'alive':
                health_badge = '<span style="background:#16a34a;color:white;padding:2px 8px;border-radius:999px;font-size:11px;">Alive</span>'
            else:
                health_badge = ''

            source_badge = f'<span style="background:var(--accent);color:white;padding:2px 8px;border-radius:999px;font-size:11px;">{source}</span>'

            badges = f'<div style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px;">{source_badge} {age_badge} {free_badge} {social_badge} {health_badge}</div>'

            reject_options = ''.join(f'<option value="{r}">{r}</option>' for r in [
                'Default deployment URL',
                'No free tier or trial',
                'Tool appears unmaintained',
                'Insufficient documentation',
                'Duplicate of existing tool',
            ])

            html += f"""
            <div class="card" style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
                    <div style="flex:1;min-width:200px;">
                        <strong style="font-size:16px;color:var(--ink);">{name}</strong>
                        <p style="color:var(--ink-muted);font-size:14px;margin-top:4px;">{tagline}</p>
                        <p style="font-size:14px;margin-top:8px;">
                            <a href="{t_url}" target="_blank" rel="noopener">{t_url}</a>
                        </p>
                        <p style="color:var(--ink-muted);font-size:14px;">Maker: {maker} &middot; Category: {cat} &middot; Price: {price_str}</p>
                        {badges}
                    </div>
                    <div style="display:flex;flex-direction:column;gap:8px;align-items:flex-end;">
                        <div style="display:flex;gap:8px;align-items:center;">
                            <a href="/admin/edit/{tid}" class="btn" style="background:var(--accent);color:white;padding:8px 16px;text-decoration:none;font-size:14px;">Edit</a>
                            <form method="post" action="/admin">
                                <input type="hidden" name="tool_id" value="{tid}">
                                <input type="hidden" name="action" value="approve">
                                <button type="submit" class="btn" style="background:#16a34a;color:white;padding:8px 16px;">Approve</button>
                            </form>
                        </div>
                        <form method="post" action="/admin" style="display:flex;gap:6px;align-items:center;">
                            <input type="hidden" name="tool_id" value="{tid}">
                            <input type="hidden" name="action" value="reject">
                            <select name="rejection_reason" style="padding:6px 8px;border-radius:8px;font-size:12px;border:1px solid var(--border);background:var(--cream);color:var(--ink);">
                                <option value="">Reason...</option>
                                {reject_options}
                                <option value="other">Other</option>
                            </select>
                            <button type="submit" class="btn" style="background:#dc2626;color:white;padding:8px 16px;">Reject</button>
                        </form>
                    </div>
                </div>
            </div>
            """
    else:
        html += '<p style="color:var(--ink-muted);">No tools pending review.</p>'
    return html


async def _render_tools_all(db, request):
    """All tools table with filters — slimmed columns (no Boost, Feature, Price)."""
    all_tools = await get_all_tools_admin(db)

    status_filter = request.query_params.get('status', '')
    search_q = request.query_params.get('q', '')
    sort_by = request.query_params.get('sort', 'newest')
    special_filter = request.query_params.get('filter', '')

    status_opts = ''
    for sv, sl in [('', 'All Status'), ('approved', 'Approved'), ('pending', 'Pending'), ('rejected', 'Rejected')]:
        sel = ' selected' if sv == status_filter else ''
        status_opts += f'<option value="{sv}"{sel}>{sl}</option>'

    filter_opts = ''
    for fv, fl in [('', 'All Tools'), ('unclaimed', 'Unclaimed'), ('boosted', 'Boosted')]:
        sel = ' selected' if fv == special_filter else ''
        filter_opts += f'<option value="{fv}"{sel}>{fl}</option>'

    sort_opts = ''
    for sv, sl in [('newest', 'Newest First'), ('oldest', 'Oldest First'), ('upvotes', 'Most Upvoted'), ('name', 'A-Z')]:
        sel = ' selected' if sv == sort_by else ''
        sort_opts += f'<option value="{sv}"{sel}>{sl}</option>'

    select_style = 'padding:6px 10px;border:1px solid var(--border);border-radius:999px;font-size:13px;'

    filter_bar = f'''
    <form method="GET" action="/admin" style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:16px;">
        <input type="hidden" name="tab" value="tools">
        <input type="hidden" name="section" value="all">
        <input type="text" name="q" value="{escape(search_q)}" placeholder="Search tools..." style="padding:6px 12px;border:1px solid var(--border);border-radius:999px;font-size:13px;width:180px;">
        <select name="status" style="{select_style}" onchange="this.form.submit()">{status_opts}</select>
        <select name="filter" style="{select_style}" onchange="this.form.submit()">{filter_opts}</select>
        <select name="sort" style="{select_style}" onchange="this.form.submit()">{sort_opts}</select>
        <button type="submit" class="btn btn-primary" style="padding:6px 16px;font-size:13px;">Filter</button>
        <a href="/admin?tab=tools&section=all" style="font-size:12px;color:var(--ink-muted);">Clear</a>
    </form>
    '''

    filtered = list(all_tools)
    if status_filter:
        filtered = [t for t in filtered if t.get('status') == status_filter]
    if special_filter == 'unclaimed':
        filtered = [t for t in filtered if not t.get('maker_id')]
    elif special_filter == 'boosted':
        filtered = [t for t in filtered if t.get('is_boosted')]
    if search_q:
        q_lower = search_q.lower()
        filtered = [t for t in filtered if q_lower in str(t.get('name', '')).lower() or q_lower in str(t.get('tags', '')).lower()]
    if sort_by == 'newest':
        filtered.sort(key=lambda t: t.get('created_at', '') or '', reverse=True)
    elif sort_by == 'oldest':
        filtered.sort(key=lambda t: t.get('created_at', '') or '')
    elif sort_by == 'upvotes':
        filtered.sort(key=lambda t: int(t.get('upvote_count', 0) or 0), reverse=True)
    elif sort_by == 'name':
        filtered.sort(key=lambda t: str(t.get('name', '')).lower())

    per_page = 50
    total_filtered = len(filtered)
    total_pages = max(1, (total_filtered + per_page - 1) // per_page)
    page = int(request.query_params.get('page', '1'))
    page = max(1, min(page, total_pages))
    paginated_tools = filtered[(page-1)*per_page : page*per_page]

    count_line = f'<p style="font-size:13px;color:var(--ink-muted);margin-bottom:12px;">Showing {len(paginated_tools)} of {total_filtered} tools (page {page}/{total_pages})</p>'

    html = filter_bar + count_line
    if filtered:
        status_styles = {
            'pending': 'background:#FDF8EE;color:#92400E;border:1px solid var(--gold);',
            'approved': 'background:#DCFCE7;color:#166534;',
            'rejected': 'background:#FEE2E2;color:#991B1B;',
        }
        rows = ''
        for t in paginated_tools:
            s = str(t.get('status', 'pending'))
            style = status_styles.get(s, '')
            is_v = bool(t.get('is_verified', 0))
            is_e = bool(t.get('is_ejectable', 0))
            e_label = 'Uneject' if is_e else 'Eject'
            e_style = 'background:#E8F5E9;color:#2E7D32;border:1px solid #A5D6A7;' if is_e else 'background:var(--cream-dark);color:var(--ink-light);border:1px solid var(--border);'
            e_badge = '<span style="display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;background:#E8F5E9;color:#2E7D32;border:1px solid #A5D6A7;">Ejectable</span>' if is_e else ''
            v_label = 'Unverify' if is_v else 'Verify'
            v_style = 'background:var(--gold-light);color:#92400E;border:1px solid var(--gold);' if is_v else 'background:var(--cream-dark);color:var(--ink-light);border:1px solid var(--border);'
            v_badge = '<span style="display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;background:linear-gradient(135deg,var(--gold-light),var(--gold));color:#92400E;border:1px solid var(--gold);">Verified</span>' if is_v else ''
            added_ago = time_ago(t.get('created_at'))
            maker_id_val = t.get('maker_id')
            if not maker_id_val:
                magic_cell = f'''
                <td style="padding:10px 12px;">
                    <button onclick="generateMagicLink({t['id']}, this)"
                            style="padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;
                                   cursor:pointer;background:#00D4F5;color:#1A2D4A;border:none;
                                   font-family:var(--font-body);">
                        <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:2px;"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg> Copy Link
                    </button>
                </td>'''
            else:
                magic_cell = '<td style="padding:10px 12px;"><span style="font-size:11px;color:var(--ink-muted);">Claimed</span></td>'
            rows += f"""
            <tr style="border-bottom:1px solid var(--border);">
                <td style="padding:10px 12px;font-weight:600;color:var(--ink);">{escape(str(t['name']))} {v_badge} {e_badge}
                    <a href="/admin/edit/{t['id']}" style="font-size:11px;font-weight:400;color:var(--accent);margin-left:6px;text-decoration:none;">edit</a>
                </td>
                <td style="padding:10px 12px;">
                    <span style="display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;
                                 font-weight:600;{style}">{escape(s)}</span>
                </td>
                <td style="padding:10px 12px;">{t.get('upvote_count', 0)}</td>
                <td style="padding:10px 12px;">{escape(str(t.get('category_name', '')))}</td>
                <td style="padding:10px 12px;font-size:12px;color:var(--ink-muted);white-space:nowrap;">{added_ago}</td>
                <td style="padding:10px 12px;">
                    <form method="post" action="/admin" style="margin:0;">
                        <input type="hidden" name="tool_id" value="{t['id']}">
                        <input type="hidden" name="action" value="toggle_verified">
                        <button type="submit" style="padding:4px 12px;border-radius:999px;font-size:12px;
                                font-weight:600;cursor:pointer;{v_style}">{v_label}</button>
                    </form>
                </td>
                <td style="padding:10px 12px;">
                    <form method="post" action="/admin" style="margin:0;">
                        <input type="hidden" name="tool_id" value="{t['id']}">
                        <input type="hidden" name="action" value="toggle_ejectable">
                        <button type="submit" style="padding:4px 12px;border-radius:999px;font-size:12px;
                                font-weight:600;cursor:pointer;{e_style}">{e_label}</button>
                    </form>
                </td>
                <td style="padding:10px 12px;">
                    <form method="post" action="/admin" style="margin:0;"
                          onsubmit="return confirm('Permanently delete {escape(str(t['name']).replace(chr(39), ''))}? This cannot be undone.')">
                        <input type="hidden" name="tool_id" value="{t['id']}">
                        <input type="hidden" name="action" value="delete_tool">
                        <button type="submit" style="padding:4px 12px;border-radius:999px;font-size:12px;
                                font-weight:600;cursor:pointer;background:#FEE2E2;color:#991B1B;border:1px solid #FECACA;">
                            Delete
                        </button>
                    </form>
                </td>
                {magic_cell}
            </tr>
            """
        html += f"""
        <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:14px;">
                <thead>
                    <tr style="border-bottom:2px solid var(--border);text-align:left;">
                        <th style="padding:10px 12px;color:var(--ink);">Name</th>
                        <th style="padding:10px 12px;color:var(--ink);">Status</th>
                        <th style="padding:10px 12px;color:var(--ink);">Upvotes</th>
                        <th style="padding:10px 12px;color:var(--ink);">Category</th>
                        <th style="padding:10px 12px;color:var(--ink);">Added</th>
                        <th style="padding:10px 12px;color:var(--ink);">Verified</th>
                        <th style="padding:10px 12px;color:var(--ink);">Ejectable</th>
                        <th style="padding:10px 12px;color:var(--ink);">Delete</th>
                        <th style="padding:10px 12px;font-size:12px;">Magic Link</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """
        base_params = {k: v for k, v in request.query_params.items() if k != 'page'}
        pagination_html = '<div style="display:flex;justify-content:center;align-items:center;gap:16px;padding:20px 0;">'
        if page > 1:
            prev_params = urlencode({**base_params, 'page': page - 1})
            pagination_html += f'<a href="/admin?{prev_params}" style="padding:8px 16px;background:var(--cream-dark);border-radius:8px;text-decoration:none;color:var(--ink);font-weight:600;">&larr; Previous</a>'
        pagination_html += f'<span style="color:var(--ink-muted);font-size:13px;">Page {page} of {total_pages} ({total_filtered} tools)</span>'
        if page < total_pages:
            next_params = urlencode({**base_params, 'page': page + 1})
            pagination_html += f'<a href="/admin?{next_params}" style="padding:8px 16px;background:var(--cream-dark);border-radius:8px;text-decoration:none;color:var(--ink);font-weight:600;">Next &rarr;</a>'
        pagination_html += '</div>'
        html += pagination_html
    else:
        html += '<p style="color:var(--ink-muted);">No tools match the current filters.</p>'

    html += """
    <script>
    async function generateMagicLink(toolId, btn) {
        btn.disabled = true;
        btn.innerHTML = '...';
        try {
            var form = new FormData();
            form.append('tool_id', toolId);
            var resp = await fetch('/admin/magic-link', {method: 'POST', body: form});
            var data = await resp.json();
            if (data.url) {
                await navigator.clipboard.writeText(data.url);
                btn.innerHTML = '&#10003; Copied!';
                btn.style.background = '#16a34a';
                btn.style.color = 'white';
                setTimeout(function() {
                    btn.innerHTML = '&#128279; Copy Link';
                    btn.style.background = '#00D4F5';
                    btn.style.color = '#1A2D4A';
                    btn.disabled = false;
                }, 3000);
            } else {
                btn.innerHTML = 'Error';
                btn.disabled = false;
            }
        } catch(e) {
            btn.innerHTML = 'Error';
            btn.disabled = false;
        }
    }
    </script>
    """
    return html


async def _render_tools_claims(db):
    """Claim requests management."""
    claim_rows = await db.execute(
        """SELECT cr.id, cr.tool_id, cr.user_id, cr.status, cr.created_at,
                  t.name as tool_name, t.slug as tool_slug,
                  u.name as user_name, u.email as user_email
           FROM claim_requests cr
           JOIN tools t ON t.id = cr.tool_id
           JOIN users u ON u.id = cr.user_id
           WHERE cr.status = 'pending'
           ORDER BY cr.created_at DESC""")
    claims = [dict(r) for r in await claim_rows.fetchall()]
    html = f'<h2 style="font-family:var(--font-display);margin-bottom:16px;color:var(--ink);">Claim Requests ({len(claims)})</h2>'
    if claims:
        html += '<div style="display:flex;flex-direction:column;gap:12px;">'
        for c in claims:
            html += f'''
            <div class="card" style="padding:16px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px;">
                <div>
                    <a href="/tool/{escape(str(c['tool_slug']))}" style="font-weight:700;color:var(--ink);font-size:15px;">{escape(str(c['tool_name']))}</a>
                    <span style="color:var(--ink-muted);font-size:13px;margin-left:8px;">claimed by {escape(str(c['user_name'] or c['user_email']))}</span>
                    <span style="color:var(--ink-muted);font-size:12px;margin-left:8px;">{escape(str(c['created_at'][:10]))}</span>
                </div>
                <div style="display:flex;gap:8px;">
                    <form method="post" action="/admin" style="display:inline;">
                        <input type="hidden" name="action" value="approve_claim">
                        <input type="hidden" name="claim_id" value="{c['id']}">
                        <input type="hidden" name="tool_id" value="{c['tool_id']}">
                        <input type="hidden" name="user_id" value="{c['user_id']}">
                        <button type="submit" class="btn" style="background:#16a34a;color:white;padding:6px 16px;font-size:13px;">Approve</button>
                    </form>
                    <form method="post" action="/admin" style="display:inline;">
                        <input type="hidden" name="action" value="reject_claim">
                        <input type="hidden" name="claim_id" value="{c['id']}">
                        <button type="submit" class="btn" style="background:#dc2626;color:white;padding:6px 16px;font-size:13px;">Reject</button>
                    </form>
                </div>
            </div>'''
        html += '</div>'
    else:
        html += '<p style="color:var(--ink-muted);">No pending claim requests.</p>'
    return html


async def _render_tools_stacks(db):
    """Stacks management — no collapsible wrapper."""
    all_tools = await get_all_tools_admin(db)
    approved_tools = [t for t in all_tools if t.get('status') == 'approved']
    display_tools = approved_tools[:200]
    total_approved = len(approved_tools)

    all_stacks = await get_all_stacks(db)
    tool_options = ''.join(f'<option value="{t["id"]}">{escape(str(t["name"]))}</option>' for t in display_tools)
    if total_approved > 200:
        tool_options += f'<option disabled>... and {total_approved - 200} more</option>'
    stack_options = ''.join(f'<option value="{s["id"]}">{escape(str(s["title"]))}</option>' for s in all_stacks)

    stacks_rows = ''
    for s in all_stacks:
        stacks_rows += f'''
        <tr style="border-bottom:1px solid var(--border);">
            <td style="padding:8px 12px;">{s['id']}</td>
            <td style="padding:8px 12px;">{escape(str(s['title']))}</td>
            <td style="padding:8px 12px;">{s.get('cover_emoji', '')}</td>
            <td style="padding:8px 12px;">{s.get('tool_count', 0)}</td>
            <td style="padding:8px 12px;">{s.get('discount_percent', 15)}%</td>
            <td style="padding:8px 12px;">
                <form method="post" action="/admin" style="display:inline;">
                    <input type="hidden" name="action" value="delete_stack">
                    <input type="hidden" name="stack_id" value="{s['id']}">
                    <button type="submit" style="padding:4px 10px;border-radius:999px;font-size:11px;font-weight:600;
                            cursor:pointer;background:#FEE2E2;color:#991B1B;border:1px solid #FECACA;"
                            onclick="return confirm('Delete this stack?')">Delete</button>
                </form>
            </td>
        </tr>'''

    add_tool_html = ''
    if all_stacks and display_tools:
        add_tool_html = f"""
        <div class="card" style="padding:16px;margin-bottom:16px;">
            <h4 style="font-size:14px;margin-bottom:10px;color:var(--ink);">Add Tool to Stack</h4>
            <form method="post" action="/admin" style="display:flex;gap:8px;align-items:end;flex-wrap:wrap;">
                <input type="hidden" name="action" value="add_to_stack">
                <div>
                    <label style="font-size:12px;display:block;margin-bottom:4px;color:var(--ink-muted);">Stack</label>
                    <select name="stack_id" style="padding:6px 10px;border:1px solid var(--border);border-radius:4px;font-size:13px;">{stack_options}</select>
                </div>
                <div>
                    <label style="font-size:12px;display:block;margin-bottom:4px;color:var(--ink-muted);">Tool</label>
                    <select name="tool_id" style="padding:6px 10px;border:1px solid var(--border);border-radius:4px;font-size:13px;">{tool_options}</select>
                </div>
                <button type="submit" class="btn btn-primary" style="padding:6px 16px;font-size:13px;">Add</button>
            </form>
        </div>
        """

    return f"""
    <h2 style="font-family:var(--font-display);margin-bottom:16px;color:var(--ink);">Stacks ({len(all_stacks)})</h2>
    <div class="card" style="padding:16px;margin-bottom:16px;">
        <h4 style="font-size:14px;margin-bottom:10px;color:var(--ink);">Create New Stack</h4>
        <form method="post" action="/admin" style="display:flex;gap:8px;flex-wrap:wrap;align-items:end;">
            <input type="hidden" name="action" value="create_stack">
            <div>
                <label style="font-size:12px;display:block;margin-bottom:4px;color:var(--ink-muted);">Title</label>
                <input type="text" name="stack_title" required style="padding:6px 10px;border:1px solid var(--border);border-radius:4px;font-size:13px;">
            </div>
            <div>
                <label style="font-size:12px;display:block;margin-bottom:4px;color:var(--ink-muted);">Emoji</label>
                <input type="text" name="stack_emoji" placeholder="&#128230;" style="padding:6px 10px;border:1px solid var(--border);border-radius:4px;width:60px;font-size:13px;">
            </div>
            <div>
                <label style="font-size:12px;display:block;margin-bottom:4px;color:var(--ink-muted);">Discount %</label>
                <input type="number" name="stack_discount" value="15" min="0" max="50" style="padding:6px 10px;border:1px solid var(--border);border-radius:4px;width:70px;font-size:13px;">
            </div>
            <div>
                <label style="font-size:12px;display:block;margin-bottom:4px;color:var(--ink-muted);">Description</label>
                <input type="text" name="stack_desc" placeholder="Optional" style="padding:6px 10px;border:1px solid var(--border);border-radius:4px;width:200px;font-size:13px;">
            </div>
            <button type="submit" class="btn btn-primary" style="padding:6px 16px;font-size:13px;">Create</button>
        </form>
    </div>
    {add_tool_html}
    <div style="overflow-x:auto;">
        <table style="width:100%;border-collapse:collapse;font-size:14px;">
            <thead>
                <tr style="border-bottom:2px solid var(--border);text-align:left;">
                    <th style="padding:8px 12px;color:var(--ink);">ID</th>
                    <th style="padding:8px 12px;color:var(--ink);">Title</th>
                    <th style="padding:8px 12px;color:var(--ink);">Emoji</th>
                    <th style="padding:8px 12px;color:var(--ink);">Tools</th>
                    <th style="padding:8px 12px;color:var(--ink);">Discount</th>
                    <th style="padding:8px 12px;color:var(--ink);">Actions</th>
                </tr>
            </thead>
            <tbody>{stacks_rows}</tbody>
        </table>
    </div>
    """


async def _render_tools_reviews(db):
    """Reviews management — no collapsible wrapper."""
    reviews = await get_all_reviews_admin(db)
    total_reviews = len(reviews)
    display_reviews = reviews[:50]

    html = f'<h2 style="font-family:var(--font-display);margin-bottom:16px;color:var(--ink);">Reviews ({total_reviews})</h2>'
    if display_reviews:
        if total_reviews > 50:
            html += f'<p style="color:var(--ink-muted);font-size:13px;margin-bottom:12px;">Showing most recent 50 of {total_reviews} reviews</p>'
        for rv in display_reviews:
            rv_tool_name = escape(str(rv.get('tool_name', 'Unknown')))
            rv_tool_slug = escape(str(rv.get('tool_slug', '')))
            rv_reviewer = escape(str(rv.get('reviewer_name', 'Anonymous')))
            rv_rating = int(rv.get('rating', 0))
            rv_body = escape(str(rv.get('body', '')))
            rv_id = rv['id']
            stars_html = '<span style="color:var(--gold);font-size:16px;">' + ('&#9733;' * rv_rating) + ('&#9734;' * (5 - rv_rating)) + '</span>'
            html += f"""
            <div class="card" style="margin-bottom:10px;padding:14px 16px;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                    <div style="flex:1;">
                        <div style="margin-bottom:4px;">
                            <a href="/tool/{rv_tool_slug}" style="font-weight:600;color:var(--slate);text-decoration:none;">{rv_tool_name}</a>
                            <span style="margin-left:8px;">{stars_html}</span>
                        </div>
                        <div style="font-size:13px;color:var(--ink-muted);margin-bottom:6px;">by {rv_reviewer}</div>
                        <p style="font-size:14px;color:var(--ink);margin:0;">{rv_body}</p>
                    </div>
                    <form method="post" action="/admin" style="margin:0;">
                        <input type="hidden" name="action" value="delete_review">
                        <input type="hidden" name="review_id" value="{rv_id}">
                        <button type="submit" style="padding:4px 10px;border-radius:999px;font-size:11px;font-weight:600;
                                cursor:pointer;background:#FEE2E2;color:#991B1B;border:1px solid #FECACA;"
                                onclick="return confirm('Delete this review?')">Delete</button>
                    </form>
                </div>
            </div>
            """
    else:
        html += '<p style="color:var(--ink-muted);padding:12px 0;">No reviews yet.</p>'
    return html


# ── People Tab ───────────────────────────────────────────────────────────

async def render_people_tab(db, request):
    """People tab: unified view of makers and users with role badges and search."""
    role_filter = request.query_params.get('role', '')
    search_q = request.query_params.get('q', '')

    # UNION query merging makers and users
    cursor = await db.execute("""
        SELECT COALESCE(u.name, m.name) as name, u.email, m.id as maker_id, m.slug as maker_slug,
               m.indie_status, u.id as user_id, COUNT(t.id) as tool_count,
               m.stripe_account_id, MAX(t.created_at) as last_active,
               'maker' as role
        FROM makers m
        LEFT JOIN users u ON u.maker_id = m.id
        LEFT JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
        GROUP BY m.id

        UNION ALL

        SELECT u.name, u.email, NULL, NULL, NULL, u.id, 0, NULL, u.created_at, 'user' as role
        FROM users u WHERE u.maker_id IS NULL

        ORDER BY last_active DESC NULLS LAST
    """)
    all_people = await cursor.fetchall()

    # Apply role filter
    if role_filter == 'makers':
        all_people = [p for p in all_people if p['role'] == 'maker']
    elif role_filter == 'users':
        all_people = [p for p in all_people if p['role'] == 'user']

    # Apply text search
    if search_q:
        q_lower = search_q.lower()
        all_people = [p for p in all_people if
                      q_lower in str(p.get('name', '') or '').lower() or
                      q_lower in str(p.get('email', '') or '').lower()]

    # Role filter pills
    pills = ''
    for val, label in [('', 'All'), ('makers', 'Makers'), ('users', 'Users')]:
        active_style = 'background:var(--slate);color:white;' if val == role_filter else 'background:var(--cream-dark);color:var(--ink-muted);border:1px solid var(--border);'
        pills += f'<a href="/admin?tab=people{f"&role={val}" if val else ""}" style="{active_style}padding:6px 14px;font-size:13px;border-radius:999px;text-decoration:none;font-weight:600;display:inline-block;">{label}</a> '

    search_input = f'''
    <form method="GET" action="/admin" style="display:inline;">
        <input type="hidden" name="tab" value="people">
        {"<input type='hidden' name='role' value='" + escape(role_filter) + "'>" if role_filter else ""}
        <input type="text" name="q" value="{escape(search_q)}" placeholder="Search name or email..."
               style="padding:6px 12px;border:1px solid var(--border);border-radius:999px;font-size:13px;width:200px;">
        <button type="submit" class="btn btn-primary" style="padding:6px 14px;font-size:12px;">Search</button>
    </form>
    '''
    filter_html = f'<div style="display:flex;gap:8px;margin-bottom:20px;align-items:center;flex-wrap:wrap;">{pills}{search_input}</div>'

    # Count summaries
    maker_count = sum(1 for p in all_people if p['role'] == 'maker') if not role_filter else len([p for p in all_people if p['role'] == 'maker'])
    user_count = len(all_people) - maker_count if not role_filter else len(all_people)

    # Build table rows
    rows_html = ''
    for idx, p in enumerate(all_people[:100]):
        name = escape(str(p['name'] or ''))
        email = escape(str(p['email'] or ''))
        role = p['role']
        tool_count = p['tool_count'] or 0
        maker_slug = p.get('maker_slug') or ''
        stripe = p.get('stripe_account_id')
        last_active = time_ago(p.get('last_active'))

        name_cell = name
        if maker_slug:
            name_cell = f'<a href="/maker/{escape(maker_slug)}" style="color:var(--slate);text-decoration:none;font-weight:600;">{name}</a>'

        stripe_cell = ''
        if role == 'maker':
            if stripe:
                stripe_cell = '<span style="color:#16a34a;font-size:12px;font-weight:600;">Connected</span>'
            else:
                stripe_cell = '<span style="color:#D97706;font-size:12px;">Not set</span>'
        else:
            stripe_cell = '<span style="color:var(--ink-muted);font-size:11px;">N/A</span>'

        # Indie status form for makers
        indie_cell = ''
        if role == 'maker' and p.get('maker_id'):
            mk_status = str(p.get('indie_status', '') or '')
            status_options = ''
            for sv, sl in [('', 'Not set'), ('solo', 'Solo'), ('small_team', 'Small Team'), ('company', 'Company')]:
                selected = ' selected' if sv == mk_status else ''
                status_options += f'<option value="{sv}"{selected}>{sl}</option>'
            indie_cell = f"""
            <form method="post" action="/admin" style="display:flex;gap:4px;margin:0;">
                <input type="hidden" name="action" value="update_indie_status">
                <input type="hidden" name="maker_id" value="{p['maker_id']}">
                <select name="indie_status" style="font-size:11px;padding:2px 6px;border-radius:999px;border:1px solid var(--border);max-width:100px;">{status_options}</select>
                <button type="submit" style="padding:2px 8px;border-radius:999px;font-size:10px;font-weight:600;cursor:pointer;background:var(--cream-dark);color:var(--ink-light);border:1px solid var(--border);">Set</button>
            </form>
            """

        rows_html += f"""
        <tr style="border-bottom:1px solid var(--border);{row_bg(idx)}">
            <td style="padding:10px 12px;font-size:13px;">{name_cell}</td>
            <td style="padding:10px 12px;font-size:13px;color:var(--ink-muted);">{email}</td>
            <td style="padding:10px 12px;">{role_badge(role)}</td>
            <td style="padding:10px 12px;font-size:13px;text-align:center;">{tool_count if role == 'maker' else ''}</td>
            <td style="padding:10px 12px;">{stripe_cell}</td>
            <td style="padding:10px 12px;font-size:12px;color:var(--ink-muted);white-space:nowrap;">{last_active}</td>
            <td style="padding:10px 12px;">{indie_cell}</td>
        </tr>
        """

    count_label = f'{len(all_people)} people'
    if len(all_people) > 100:
        count_label = f'Showing 100 of {len(all_people)} people'

    table_html = data_table(
        f"People ({count_label})",
        ["Name", "Email", "Role", "Tools", "Stripe", "Last Active", "Indie Status"],
        rows_html
    )

    return f"""
    {filter_html}
    {table_html}
    """


# ── Growth Tab ───────────────────────────────────────────────────────────

async def render_growth_tab(db, request):
    """Growth tab: 4 consolidated sections (Traffic, Funnels, Search, Outreach)."""
    section = request.query_params.get('section', 'traffic')
    _aliases = {
        'charts': 'traffic', 'tables': 'traffic',
        'email': 'outreach', 'magic': 'outreach',
        'makers': 'outreach', 'stale': 'outreach', 'social': 'outreach',
    }
    section = _aliases.get(section, section)
    html = growth_sub_nav(section)

    if section == 'traffic':
        html += await render_charts_section(db, request)
        html += await render_tables_section(db, request)
    elif section == 'funnels':
        html += await render_funnels_section(db)
    elif section == 'search':
        html += await render_search_section(db)
    elif section == 'outreach':
        html += await render_email_section(db, request)
        html += await render_magic_section(db, request)
        html += await render_makers_section(db, request)
        html += await render_stale_section(db, request)
        html += await render_social_section(db)
    else:
        html += await render_charts_section(db, request)
        html += await render_tables_section(db, request)

    return html


# ── POST /admin ──────────────────────────────────────────────────────────

@router.post("/admin")
async def admin_post(request: Request):
    form = await request.form()

    # Login
    if "password" in form:
        client_ip = request.headers.get("fly-client-ip", request.client.host if request.client else "unknown")
        if _check_admin_rate_limit(client_ip):
            return HTMLResponse(page_shell("Admin Login", login_form_html("Too many attempts. Try again in 15 minutes."), user=request.state.user))
        password = str(form["password"])
        if _secrets.compare_digest(password, ADMIN_PASSWORD):
            _clear_admin_attempts(client_ip)
            token = make_session_token(password)
            response = RedirectResponse(url="/admin", status_code=303)
            response.set_cookie(key="indiestack_admin", value=token, httponly=True, samesite="lax", secure=True, max_age=8*3600)
            return response
        else:
            _record_admin_attempt(client_ip)
            return HTMLResponse(page_shell("Admin Login", login_form_html("Invalid password."), user=request.state.user))

    # Approve / Reject / Verify / all other actions
    if "action" in form:
        if not check_admin_session(request):
            return RedirectResponse(url="/admin", status_code=303)

        def _safe_int(val) -> int | None:
            try:
                return int(val) if val else None
            except (ValueError, TypeError):
                return None

        db = request.state.db
        tool_id_int = _safe_int(form.get("tool_id"))
        action = str(form.get("action", ""))

        # Delegate outreach actions
        if action in OUTREACH_ACTIONS:
            return await handle_outreach_post(db, form, request)

        # Avatar approve/reject
        if action == "approve_avatar":
            user_id = int(form.get("user_id", 0))
            if user_id:
                await update_user(db, user_id, pixel_avatar_approved=1)
            return RedirectResponse(url="/admin?toast=Avatar+approved", status_code=303)

        if action == "reject_avatar":
            user_id = int(form.get("user_id", 0))
            if user_id:
                await update_user(db, user_id, pixel_avatar='', pixel_avatar_approved=0)
            return RedirectResponse(url="/admin?toast=Avatar+rejected", status_code=303)

        # Bulk actions
        if action == "approve_all":
            cursor = await db.execute("SELECT id FROM tools WHERE status = 'pending'")
            pending_ids = [r['id'] for r in await cursor.fetchall()]
            for pid in pending_ids:
                await update_tool_status(db, pid, "approved")
            return RedirectResponse(url="/admin?tab=tools&toast=All+tools+approved", status_code=303)
        elif action == "reject_all":
            cursor = await db.execute("SELECT id FROM tools WHERE status = 'pending'")
            pending_ids = [r['id'] for r in await cursor.fetchall()]
            for pid in pending_ids:
                await update_tool_status(db, pid, "rejected")
            return RedirectResponse(url="/admin?tab=tools&toast=All+tools+rejected", status_code=303)
        elif tool_id_int and action in ("approve", "reject"):
            new_status = "approved" if action == "approve" else "rejected"
            await update_tool_status(db, tool_id_int, new_status)
            # Store rejection reason if provided
            if new_status == "rejected":
                reason = str(form.get("rejection_reason", "")).strip()
                if reason:
                    await db.execute(
                        "UPDATE tools SET rejection_reason = ? WHERE id = ?",
                        (reason, tool_id_int),
                    )
                    await db.commit()
            if new_status == "approved":
                # ── Competitor pings (dashboard notification, no email) ──
                try:
                    approved_tool = await get_tool_by_id(db, tool_id_int)
                    if approved_tool:
                        cat_id = approved_tool['category_id']
                        cat_name = approved_tool.get('category_name', '')
                        tool_name = approved_tool['name']
                        tool_slug = approved_tool.get('slug', '')
                        competitors = await get_makers_in_category(db, cat_id, exclude_tool_id=tool_id_int)
                        for comp in competitors:
                            try:
                                cursor = await db.execute(
                                    "SELECT id FROM users WHERE maker_id = ?",
                                    (comp['maker_id'],))
                                user_row = await cursor.fetchone()
                                if user_row:
                                    await create_notification(
                                        db, user_row['id'], 'competition',
                                        f"New in {cat_name}: {tool_name} just launched",
                                        f"/tool/{tool_slug}"
                                    )
                            except Exception:
                                pass
                except Exception:
                    pass

                # Credit referral boost if this tool's maker was referred
                try:
                    updated_tool = await get_tool_by_id(db, tool_id_int)
                    if updated_tool and updated_tool.get('maker_id'):
                        maker_user_cursor = await db.execute(
                            "SELECT id, referred_by FROM users WHERE maker_id = ?",
                            (updated_tool['maker_id'],))
                        maker_user = await maker_user_cursor.fetchone()
                        if maker_user and maker_user['referred_by']:
                            first_check = await db.execute(
                                "SELECT COUNT(*) as cnt FROM tools WHERE maker_id = ? AND status = 'approved'",
                                (updated_tool['maker_id'],))
                            first_row = await first_check.fetchone()
                            if first_row and first_row['cnt'] == 1:
                                from indiestack.db import credit_referral_boost
                                await credit_referral_boost(db, maker_user['referred_by'], 10)
                except Exception:
                    pass
            toast_msg = "Tool+approved" if action == "approve" else "Tool+rejected"
            return RedirectResponse(url=f"/admin?tab=tools&toast={toast_msg}", status_code=303)
        elif action == "approve_claim":
            claim_id = int(form.get("claim_id", 0))
            claim_tool_id = int(form.get("tool_id", 0))
            claim_user_id = int(form.get("user_id", 0))
            if claim_id and claim_tool_id and claim_user_id:
                # Create or get maker, assign to tool
                u_cursor = await db.execute("SELECT name, email, maker_id FROM users WHERE id = ?", (claim_user_id,))
                claim_user = await u_cursor.fetchone()
                if claim_user:
                    maker_name = claim_user['name'] or claim_user['email'].split('@')[0]
                    if claim_user['maker_id']:
                        mid = claim_user['maker_id']
                    else:
                        from indiestack.db import get_or_create_maker
                        mid = await get_or_create_maker(db, maker_name, '')
                        await db.execute("UPDATE users SET maker_id = ?, role = 'maker' WHERE id = ?", (mid, claim_user_id))
                    await db.execute("UPDATE tools SET maker_id = ?, claimed_at = CURRENT_TIMESTAMP WHERE id = ? AND maker_id IS NULL", (mid, claim_tool_id))
                    await db.execute("UPDATE claim_requests SET status = 'approved' WHERE id = ?", (claim_id,))
                    await db.commit()
            return RedirectResponse(url="/admin?tab=tools&toast=Claim+approved", status_code=303)
        elif action == "reject_claim":
            claim_id = int(form.get("claim_id", 0))
            if claim_id:
                await db.execute("UPDATE claim_requests SET status = 'rejected' WHERE id = ?", (claim_id,))
                await db.commit()
            return RedirectResponse(url="/admin?tab=tools&toast=Claim+rejected", status_code=303)
        elif tool_id_int and action == "toggle_verified":
            await toggle_verified(db, tool_id_int)
            return RedirectResponse(url="/admin?tab=tools&toast=Verified+toggled", status_code=303)
        elif tool_id_int and action == "toggle_ejectable":
            await toggle_ejectable(db, tool_id_int)
            return RedirectResponse(url="/admin?tab=tools&toast=Ejectable+toggled", status_code=303)
        elif tool_id_int and action == "feature":
            headline = str(form.get("headline", "")).strip()
            feature_desc = str(form.get("feature_desc", "")).strip()
            await set_featured_tool(db, tool_id_int, headline, feature_desc)
            return RedirectResponse(url="/admin?tab=tools&toast=Featured+tool+updated", status_code=303)
        elif action == "clear_featured":
            await clear_featured_tool(db)
            return RedirectResponse(url="/admin?tab=tools&toast=Tool+of+the+Week+cleared", status_code=303)
        elif tool_id_int and action == "delete_tool":
            await delete_tool(db, tool_id_int)
            return RedirectResponse(url="/admin?tab=tools&toast=Tool+permanently+deleted", status_code=303)
        elif action == "delete_review":
            review_id = _safe_int(form.get("review_id"))
            if review_id:
                await delete_review(db, review_id)
            return RedirectResponse(url="/admin?tab=tools&section=reviews&toast=Review+deleted", status_code=303)
        elif action == "toggle_boost":
            tool_id = int(form.get("tool_id", 0))
            competitor = str(form.get("competitor", "")).strip().lower().replace(" ", "-")
            if tool_id:
                await toggle_tool_boost(db, tool_id, competitor)
            return RedirectResponse(url="/admin?tab=tools&toast=Boost+updated", status_code=303)
        elif action == "update_indie_status":
            maker_id_val = _safe_int(form.get("maker_id"))
            ind_status = str(form.get("indie_status", ""))
            if maker_id_val and ind_status in ('', 'solo', 'small_team', 'company'):
                await update_maker(db, maker_id_val, indie_status=ind_status)
            return RedirectResponse(url="/admin?tab=people&toast=Indie+status+updated", status_code=303)
        elif action == "create_stack":
            stack_title = str(form.get("stack_title", "")).strip()
            stack_desc = str(form.get("stack_desc", "")).strip()
            stack_emoji = str(form.get("stack_emoji", "")).strip() or "\U0001F4E6"
            stack_discount = int(form.get("stack_discount", 15) or 15)
            if stack_title:
                await create_stack(db, title=stack_title, description=stack_desc,
                                  cover_emoji=stack_emoji, discount_percent=stack_discount)
            return RedirectResponse(url="/admin?tab=tools&section=stacks&toast=Stack+created", status_code=303)
        elif action == "add_to_stack":
            stack_id_val = int(form.get("stack_id", 0) or 0)
            tool_id_val = int(form.get("tool_id", 0) or 0)
            if stack_id_val and tool_id_val:
                await add_tool_to_stack(db, stack_id_val, tool_id_val)
            return RedirectResponse(url="/admin?tab=tools&section=stacks&toast=Tool+added+to+stack", status_code=303)
        elif action == "remove_from_stack":
            stack_id_val = int(form.get("stack_id", 0) or 0)
            tool_id_val = int(form.get("tool_id", 0) or 0)
            if stack_id_val and tool_id_val:
                await remove_tool_from_stack(db, stack_id_val, tool_id_val)
            return RedirectResponse(url="/admin?tab=tools&section=stacks&toast=Tool+removed+from+stack", status_code=303)
        elif action == "delete_stack":
            stack_id_val = int(form.get("stack_id", 0) or 0)
            if stack_id_val:
                await delete_stack(db, stack_id_val)
            return RedirectResponse(url="/admin?tab=tools&section=stacks&toast=Stack+deleted", status_code=303)
        return RedirectResponse(url="/admin", status_code=303)

    return RedirectResponse(url="/admin", status_code=303)


# ── Redirect routes (old analytics/outreach URLs) ────────────────────────

@router.get("/admin/analytics")
async def admin_analytics_redirect(request: Request):
    tab = request.query_params.get("tab", "overview")
    section_map = {"overview": "charts", "funnels": "funnels", "search": "search", "growth": "charts"}
    return RedirectResponse(url=f"/admin?tab=growth&section={section_map.get(tab, 'charts')}", status_code=302)


@router.get("/admin/outreach")
async def admin_outreach_redirect(request: Request):
    tab = request.query_params.get("tab", "email")
    section_map = {"email": "email", "magic": "magic", "makers": "makers", "stale": "stale", "social": "social"}
    return RedirectResponse(url=f"/admin?tab=growth&section={section_map.get(tab, 'email')}", status_code=302)


# ── Bulk Import ──────────────────────────────────────────────────────────

IMPORT_EXAMPLE = """[
  {
    "name": "InvoiceOwl",
    "tagline": "Simple invoicing for freelancers",
    "description": "Generate professional invoices in seconds.",
    "url": "https://invoiceowl.example.com",
    "category": "Invoicing & Billing",
    "maker_name": "Jane Doe",
    "maker_url": "https://janedoe.dev",
    "tags": "invoicing, freelance, billing"
  }
]"""


def import_form_html(result: str = "") -> str:
    return f"""
    <div class="container" style="max-width:800px;padding:48px 24px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Bulk Import Tools</h1>
            <a href="/admin" class="btn" style="background:var(--cream-dark);color:var(--ink-light);border:1px solid var(--border);">
                &larr; Back to Admin
            </a>
        </div>
        <p style="color:var(--ink-muted);margin-bottom:24px;">
            Paste a JSON array of tools below. Each tool needs: <code>name</code>, <code>tagline</code>,
            <code>description</code>, <code>url</code>, <code>category</code> (must match an existing category name).
            Optional: <code>maker_name</code>, <code>maker_url</code>, <code>tags</code>.
            All imported tools are <strong>auto-approved</strong>.
        </p>
        {result}
        <form method="post" action="/admin/import">
            <div class="form-group">
                <label for="json_data">Tool Data (JSON array)</label>
                <textarea id="json_data" name="json_data" class="form-textarea"
                          style="min-height:400px;font-family:var(--font-mono);font-size:13px;"
                          placeholder='{escape(IMPORT_EXAMPLE)}'></textarea>
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:14px;">
                Import Tools
            </button>
        </form>
    </div>
    """


@router.get("/admin/import", response_class=HTMLResponse)
async def admin_import_get(request: Request):
    if not check_admin_session(request):
        return RedirectResponse(url="/admin", status_code=303)
    return HTMLResponse(page_shell("Bulk Import", import_form_html(), user=request.state.user))


@router.post("/admin/import", response_class=HTMLResponse)
async def admin_import_post(request: Request):
    if not check_admin_session(request):
        return RedirectResponse(url="/admin", status_code=303)

    form = await request.form()
    json_data = str(form.get("json_data", "")).strip()

    if not json_data:
        result = '<div class="alert alert-error">Please paste some JSON data.</div>'
        return HTMLResponse(page_shell("Bulk Import", import_form_html(result), user=request.state.user))

    try:
        tools_data = json.loads(json_data)
        if not isinstance(tools_data, list):
            raise ValueError("Expected a JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        result = f'<div class="alert alert-error">Invalid JSON: {escape(str(e))}</div>'
        return HTMLResponse(page_shell("Bulk Import", import_form_html(result), user=request.state.user))

    created, errors = await bulk_create_tools(request.state.db, tools_data)

    parts = []
    if created:
        parts.append(f'<div class="alert alert-success">Successfully imported {created} tool{"s" if created != 1 else ""}!</div>')
    if errors:
        error_list = "".join(f"<li>{escape(e)}</li>" for e in errors)
        parts.append(f'<div class="alert alert-error"><strong>Errors:</strong><ul style="margin:8px 0 0 16px;">{error_list}</ul></div>')

    return HTMLResponse(page_shell("Bulk Import", import_form_html("".join(parts)), user=request.state.user))


# ── Tool Edit Form ────────────────────────────────────────────────────────

@router.get("/admin/edit/{tool_id}", response_class=HTMLResponse)
async def admin_edit_tool_get(request: Request, tool_id: int):
    if not check_admin_session(request):
        return RedirectResponse(url="/admin", status_code=303)
    db = request.state.db
    tool = await get_tool_by_id(db, tool_id)
    if not tool:
        return RedirectResponse(url="/admin?tab=tools&toast=Tool+not+found", status_code=303)
    categories = await get_all_categories(db)
    toast = request.query_params.get("toast", "")
    toast_html = f'<div style="background:var(--success-bg);color:var(--success-text);padding:10px 16px;border-radius:var(--radius);margin-bottom:16px;font-size:14px;">{escape(toast)}</div>' if toast else ''

    cat_options = ""
    for c in categories:
        selected = " selected" if c['id'] == tool['category_id'] else ""
        cat_options += f'<option value="{c["id"]}"{selected}>{escape(str(c["name"]))}</option>'

    inp = 'style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:var(--radius);font-size:14px;background:var(--card-bg);font-family:var(--font-body);"'
    html = f"""
    <div class="container" style="max-width:800px;padding:48px 24px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Edit Tool: {escape(str(tool['name']))}</h1>
            <a href="/admin?tab=tools" class="btn" style="background:var(--cream-dark);color:var(--ink-light);border:1px solid var(--border);">
                &larr; Back to Tools
            </a>
        </div>
        {toast_html}
        <form method="post" action="/admin/edit/{tool_id}">
            <div style="margin-bottom:16px;">
                <label style="font-weight:600;font-size:14px;display:block;margin-bottom:6px;">Name</label>
                <input type="text" name="name" value="{escape(str(tool['name']))}" {inp} required>
            </div>
            <div style="margin-bottom:16px;">
                <label style="font-weight:600;font-size:14px;display:block;margin-bottom:6px;">Tagline</label>
                <input type="text" name="tagline" value="{escape(str(tool['tagline']))}" {inp}>
            </div>
            <div style="margin-bottom:16px;">
                <label style="font-weight:600;font-size:14px;display:block;margin-bottom:6px;">URL</label>
                <input type="url" name="url" value="{escape(str(tool['url']))}" {inp} required>
            </div>
            <div style="margin-bottom:16px;">
                <label style="font-weight:600;font-size:14px;display:block;margin-bottom:6px;">Description</label>
                <textarea name="description" rows="4" {inp} style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:var(--radius);font-size:14px;background:var(--card-bg);font-family:var(--font-body);resize:vertical;">{escape(str(tool['description']))}</textarea>
            </div>
            <div style="margin-bottom:16px;">
                <label style="font-weight:600;font-size:14px;display:block;margin-bottom:6px;">Tags (comma-separated)</label>
                <input type="text" name="tags" value="{escape(str(tool.get('tags', '')))}" {inp}>
            </div>
            <div style="margin-bottom:16px;">
                <label style="font-weight:600;font-size:14px;display:block;margin-bottom:6px;">Category</label>
                <select name="category_id" {inp}>
                    {cat_options}
                </select>
            </div>
            <div style="margin-bottom:16px;">
                <label style="font-weight:600;font-size:14px;display:block;margin-bottom:6px;">Delivery URL</label>
                <input type="text" name="delivery_url" value="{escape(str(tool.get('delivery_url', '')))}" {inp}>
            </div>
            <div style="margin-top:16px;">
                <label style="font-weight:600;font-size:14px;display:block;margin-bottom:6px;">Python Integration Snippet</label>
                <textarea name="integration_python" rows="8"
                    style="width:100%;font-family:var(--font-mono);font-size:13px;padding:12px;border:1px solid var(--border);border-radius:var(--radius);background:var(--card-bg);resize:vertical;"
                    placeholder="Custom Python integration code (leave empty for auto-generated)">{escape(str(tool.get('integration_python', '') or ''))}</textarea>
            </div>
            <div style="margin-top:16px;">
                <label style="font-weight:600;font-size:14px;display:block;margin-bottom:6px;">cURL Integration Snippet</label>
                <textarea name="integration_curl" rows="5"
                    style="width:100%;font-family:var(--font-mono);font-size:13px;padding:12px;border:1px solid var(--border);border-radius:var(--radius);background:var(--card-bg);resize:vertical;"
                    placeholder="Custom cURL integration code (leave empty for auto-generated)">{escape(str(tool.get('integration_curl', '') or ''))}</textarea>
            </div>

            <div style="border-top:1px solid var(--border);margin-top:24px;padding-top:24px;">
            <h3 style="margin:0 0 16px;font-family:var(--heading-font);">Agent Assembly Metadata</h3>

            <label style="font-weight:600;display:block;margin-bottom:4px;">API Type</label>
            <select name="api_type" style="width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--border);margin-bottom:12px;background:var(--bg-card);color:var(--ink);">
                <option value="">Not specified</option>
                <option value="REST"{"" if (tool.get("api_type") or "") != "REST" else " selected"}>REST</option>
                <option value="GraphQL"{"" if (tool.get("api_type") or "") != "GraphQL" else " selected"}>GraphQL</option>
                <option value="SDK"{"" if (tool.get("api_type") or "") != "SDK" else " selected"}>SDK / Library</option>
                <option value="CLI"{"" if (tool.get("api_type") or "") != "CLI" else " selected"}>CLI</option>
                <option value="WebSocket"{"" if (tool.get("api_type") or "") != "WebSocket" else " selected"}>WebSocket</option>
            </select>

            <label style="font-weight:600;display:block;margin-bottom:4px;">Auth Method</label>
            <select name="auth_method" style="width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--border);margin-bottom:12px;background:var(--bg-card);color:var(--ink);">
                <option value="">Not specified</option>
                <option value="api_key"{"" if (tool.get("auth_method") or "") != "api_key" else " selected"}>API Key</option>
                <option value="oauth2"{"" if (tool.get("auth_method") or "") != "oauth2" else " selected"}>OAuth 2.0</option>
                <option value="bearer"{"" if (tool.get("auth_method") or "") != "bearer" else " selected"}>Bearer Token</option>
                <option value="none"{"" if (tool.get("auth_method") or "") != "none" else " selected"}>None (open)</option>
            </select>

            <label style="font-weight:600;display:block;margin-bottom:4px;">SDK Packages <span style="color:var(--ink-muted);font-weight:400;">(JSON: {{"npm": "pkg", "pip": "pkg"}})</span></label>
            <input type="text" name="sdk_packages" value="{escape(str(tool.get('sdk_packages','') or ''))}"
                   style="width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--border);margin-bottom:12px;font-family:var(--mono);">

            <label style="font-weight:600;display:block;margin-bottom:4px;">Env Vars <span style="color:var(--ink-muted);font-weight:400;">(JSON array: ["VAR1", "VAR2"])</span></label>
            <input type="text" name="env_vars" value="{escape(str(tool.get('env_vars','') or ''))}"
                   style="width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--border);margin-bottom:12px;font-family:var(--mono);">

            <label style="font-weight:600;display:block;margin-bottom:4px;">Frameworks Tested <span style="color:var(--ink-muted);font-weight:400;">(comma-separated)</span></label>
            <input type="text" name="frameworks_tested" value="{escape(str(tool.get('frameworks_tested','') or ''))}"
                   placeholder="nextjs, fastapi, rails"
                   style="width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--border);margin-bottom:12px;">

            <label style="font-weight:600;display:block;margin-bottom:4px;">Verified Compatible Tools <span style="color:var(--ink-muted);font-weight:400;">(comma-separated slugs)</span></label>
            <input type="text" name="verified_pairs" value="{escape(str(tool.get('verified_pairs','') or ''))}"
                   style="width:100%;padding:8px 12px;border-radius:8px;border:1px solid var(--border);margin-bottom:12px;">
            </div>

            <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:14px;margin-top:24px;">
                Save Changes
            </button>
        </form>
    </div>
    """
    return HTMLResponse(page_shell(f"Edit {tool['name']}", html, user=request.state.user))


@router.post("/admin/edit/{tool_id}", response_class=HTMLResponse)
async def admin_edit_tool_post(request: Request, tool_id: int):
    if not check_admin_session(request):
        return RedirectResponse(url="/admin", status_code=303)
    db = request.state.db
    tool = await get_tool_by_id(db, tool_id)
    if not tool:
        return RedirectResponse(url="/admin?tab=tools&toast=Tool+not+found", status_code=303)

    form = await request.form()
    name = str(form.get("name", "")).strip()
    tagline = str(form.get("tagline", "")).strip()
    url = str(form.get("url", "")).strip()
    description = str(form.get("description", "")).strip()
    tags = str(form.get("tags", "")).strip()
    category_id = int(form.get("category_id", tool['category_id']))
    delivery_url = str(form.get("delivery_url", "")).strip()
    integration_python = str(form.get("integration_python", "")).strip()
    integration_curl = str(form.get("integration_curl", "")).strip()
    api_type = str(form.get("api_type", "")).strip()
    auth_method = str(form.get("auth_method", "")).strip()
    sdk_packages = str(form.get("sdk_packages", "")).strip()
    env_vars = str(form.get("env_vars", "")).strip()
    frameworks_tested = str(form.get("frameworks_tested", "")).strip()
    verified_pairs = str(form.get("verified_pairs", "")).strip()

    if not name or not url:
        return RedirectResponse(url=f"/admin/edit/{tool_id}?toast=Name+and+URL+are+required", status_code=303)

    await update_tool(db, tool_id,
                      name=name,
                      tagline=tagline,
                      url=url,
                      description=description,
                      tags=tags,
                      category_id=category_id,
                      delivery_url=delivery_url,
                      integration_python=integration_python,
                      integration_curl=integration_curl,
                      api_type=api_type,
                      auth_method=auth_method,
                      sdk_packages=sdk_packages,
                      env_vars=env_vars,
                      frameworks_tested=frameworks_tested,
                      verified_pairs=verified_pairs)

    return RedirectResponse(url=f"/admin/edit/{tool_id}?toast=Tool+updated+successfully", status_code=303)

"""Admin Command Center — unified dashboard with 5 tabs: Overview, Tools, People, Content, Growth."""

import json
import secrets as _secrets
from datetime import datetime
from html import escape
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell
from indiestack.db import (get_pending_tools, get_all_tools_admin, update_tool_status, toggle_verified, toggle_ejectable,
                           bulk_create_tools, get_purchase_stats, set_featured_tool, clear_featured_tool,
                           get_collection_by_slug, get_all_reviews_admin, delete_review, get_all_makers_admin, update_maker,
                           toggle_tool_boost, create_stack, get_all_stacks, add_tool_to_stack, remove_tool_from_stack, delete_stack,
                           get_tool_by_id, get_makers_in_category, get_all_purchases_admin,
                           update_tool, get_all_categories, delete_tool, get_pro_subscriber_stats)
from indiestack.email import send_email, competitor_ping_html, tool_approved_html
from indiestack.auth import check_admin_session, make_session_token, ADMIN_PASSWORD

# New imports for consolidated admin
from indiestack.routes.admin_helpers import (
    time_ago, kpi_card, pending_alert_bar, status_badge, role_badge,
    tab_nav, growth_sub_nav, row_bg, data_table
)
from indiestack.routes.admin_analytics import (
    render_traffic_section, render_funnels_section,
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
    elif tab == 'content':
        section_html = await render_content_tab(db, request)
    elif tab == 'growth':
        section_html = await render_growth_tab(db, request)
    else:
        tab = 'overview'
        section_html = await render_overview(db, request, pending)

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:1000px;">
        <h1 style="font-family:var(--font-display);font-size:28px;color:var(--ink);margin-bottom:24px;">
            Admin Command Center
        </h1>
        {toast_html}
        {tab_nav(tab, pending_count)}
        {pending_alert_bar(pending_count) if tab != 'tools' else ''}
        {section_html}
    </div>
    """
    return HTMLResponse(page_shell("Admin", body, user=request.state.user))


# ── Overview Tab ─────────────────────────────────────────────────────────

async def render_overview(db, request, pending):
    """Overview tab: KPI cards, pending queue, alerts, recent activity."""
    pending_count = len(pending)

    # KPI data
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status = 'approved'")
    total_tools = (await cursor.fetchone())['cnt']

    cursor = await db.execute("SELECT COUNT(*) as cnt FROM makers")
    total_makers = (await cursor.fetchone())['cnt']

    cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
    total_users = (await cursor.fetchone())['cnt']

    stats = await get_purchase_stats(db)
    total_revenue_pence = stats.get('total_revenue', 0) or 0

    cursor = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE maker_id IS NULL AND status = 'approved'")
    unclaimed_count = (await cursor.fetchone())['cnt']

    cursor = await db.execute(
        "SELECT COALESCE(SUM(mcp_view_count), 0) as cnt FROM tools WHERE status = 'approved'"
    )
    mcp_views = (await cursor.fetchone())['cnt']

    pro_stats = await get_pro_subscriber_stats(db)
    pro_count = pro_stats.get('active_count', 0) or 0

    # 8 KPI cards in 4x2 grid
    kpi_html = f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px;">
        {kpi_card("Total Tools", f"{total_tools:,}", color="var(--slate)", link="/admin?tab=tools")}
        {kpi_card("Makers", f"{total_makers:,}", color="var(--slate)", link="/admin?tab=people")}
        {kpi_card("Users", f"{total_users:,}", color="var(--slate)", link="/admin?tab=people")}
        {kpi_card("Revenue", f"£{total_revenue_pence / 100:.2f}", color="#16a34a")}
    </div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px;">
        {kpi_card("Pending", f"{pending_count}", color="#EA580C", link="/admin?tab=tools&status=pending")}
        {kpi_card("Unclaimed", f"{unclaimed_count}", color="#D97706", link="/admin?tab=tools&filter=unclaimed")}
        {kpi_card("MCP Views (7d)", f"{mcp_views:,}", color="var(--accent)")}
        {kpi_card("Pro Subscribers", f"{pro_count}", color="#7C3AED")}
    </div>
    """

    # Pending queue
    pending_html = ''
    if pending:
        cards = ''
        for t in pending[:5]:
            tid = t['id']
            name = escape(str(t['name']))
            tagline = escape(str(t['tagline']))
            t_url = escape(str(t['url']))
            cards += f"""
            <div class="card" style="margin-bottom:10px;padding:14px 16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:200px;">
                        <strong style="font-size:15px;color:var(--ink);">{name}</strong>
                        <span style="color:var(--ink-muted);font-size:13px;margin-left:8px;">{tagline}</span>
                    </div>
                    <div style="display:flex;gap:6px;">
                        <form method="post" action="/admin" style="margin:0;">
                            <input type="hidden" name="tool_id" value="{tid}">
                            <input type="hidden" name="action" value="approve">
                            <button type="submit" style="padding:5px 14px;border-radius:999px;font-size:12px;font-weight:600;
                                    cursor:pointer;background:#16a34a;color:white;border:none;">Approve</button>
                        </form>
                        <form method="post" action="/admin" style="margin:0;">
                            <input type="hidden" name="tool_id" value="{tid}">
                            <input type="hidden" name="action" value="reject">
                            <button type="submit" style="padding:5px 14px;border-radius:999px;font-size:12px;font-weight:600;
                                    cursor:pointer;background:#dc2626;color:white;border:none;">Reject</button>
                        </form>
                    </div>
                </div>
            </div>
            """
        more_link = ''
        if pending_count > 5:
            more_link = f'<a href="/admin?tab=tools&status=pending" style="font-size:13px;color:var(--slate);font-weight:600;">View all {pending_count} pending &rarr;</a>'
        pending_html = f"""
        <div style="margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:12px;">
                Pending Review ({pending_count})
            </h2>
            {cards}
            {more_link}
        </div>
        """

    # Alerts strip
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM tools WHERE status='approved' AND created_at < datetime('now', '-90 days')"
    )
    stale_count = (await cursor.fetchone())['cnt']

    cursor = await db.execute(
        """SELECT COUNT(*) as cnt FROM search_logs
           WHERE result_count = 0 AND created_at >= datetime('now', '-30 days')"""
    )
    search_gaps = (await cursor.fetchone())['cnt']

    cursor = await db.execute(
        """SELECT COUNT(*) as cnt FROM makers m
           JOIN users u ON u.maker_id = m.id
           WHERE m.stripe_account_id IS NULL
           AND EXISTS (SELECT 1 FROM tools t WHERE t.maker_id = m.id AND t.price_pence > 0)"""
    )
    stripe_needed = (await cursor.fetchone())['cnt']

    alerts_html = ''
    alert_items = []
    if stale_count > 0:
        alert_items.append(f'<span style="color:#D97706;font-weight:600;">{stale_count} stale tools</span> (no update in 90+ days)')
    if search_gaps > 0:
        alert_items.append(f'<span style="color:#DC2626;font-weight:600;">{search_gaps} search gaps</span> (searches with no results — people looking for tools we don\'t have yet)')
    if stripe_needed > 0:
        alert_items.append(f'<span style="color:#7C3AED;font-weight:600;">{stripe_needed} makers</span> need Stripe setup')

    if alert_items:
        items_html = ' &middot; '.join(alert_items)
        alerts_html = f"""
        <div class="card" style="padding:14px 20px;margin-bottom:32px;border-left:3px solid #D97706;">
            <div style="font-size:13px;color:var(--ink);">
                <strong style="color:var(--ink);margin-right:8px;">Alerts:</strong> {items_html}
            </div>
        </div>
        """

    # Recent activity: last 10 tool submissions
    cursor = await db.execute(
        """SELECT t.name, t.status, t.created_at, m.name as maker_name
           FROM tools t LEFT JOIN makers m ON t.maker_id = m.id
           ORDER BY t.created_at DESC LIMIT 10"""
    )
    recent_tools = await cursor.fetchall()

    recent_tools_rows = ''
    for idx, rt in enumerate(recent_tools):
        name = escape(str(rt['name']))
        status = escape(str(rt['status']))
        maker = escape(str(rt.get('maker_name', '') or ''))
        ago = time_ago(rt.get('created_at'))
        status_styles = {
            'pending': 'background:#FDF8EE;color:#92400E;',
            'approved': 'background:#DCFCE7;color:#166534;',
            'rejected': 'background:#FEE2E2;color:#991B1B;',
        }
        s_style = status_styles.get(status, '')
        recent_tools_rows += f"""
        <tr style="border-bottom:1px solid var(--border);{row_bg(idx)}">
            <td style="padding:8px 12px;font-size:13px;font-weight:600;color:var(--ink);">{name}</td>
            <td style="padding:8px 12px;"><span style="display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;{s_style}">{status}</span></td>
            <td style="padding:8px 12px;font-size:13px;color:var(--ink-muted);">{maker or 'Unknown'}</td>
            <td style="padding:8px 12px;font-size:13px;color:var(--ink-muted);">{ago}</td>
        </tr>
        """

    recent_tools_table = data_table("Recent Submissions", ["Tool", "Status", "Maker", "When"], recent_tools_rows)

    # Last 10 purchases
    cursor = await db.execute(
        """SELECT p.created_at, p.amount_pence, t.name as tool_name, p.buyer_email
           FROM purchases p
           LEFT JOIN tools t ON p.tool_id = t.id
           ORDER BY p.created_at DESC LIMIT 10"""
    )
    recent_purchases = await cursor.fetchall()

    recent_purchases_rows = ''
    for idx, rp in enumerate(recent_purchases):
        tool_name = escape(str(rp.get('tool_name', '') or 'Unknown'))
        buyer = escape(str(rp.get('buyer_email', '') or ''))
        amount = (rp.get('amount_pence', 0) or 0) / 100
        ago = time_ago(rp.get('created_at'))
        recent_purchases_rows += f"""
        <tr style="border-bottom:1px solid var(--border);{row_bg(idx)}">
            <td style="padding:8px 12px;font-size:13px;font-weight:600;color:var(--ink);">{tool_name}</td>
            <td style="padding:8px 12px;font-size:13px;color:var(--ink-muted);">{buyer}</td>
            <td style="padding:8px 12px;font-size:13px;color:#16a34a;font-weight:600;">£{amount:.2f}</td>
            <td style="padding:8px 12px;font-size:13px;color:var(--ink-muted);">{ago}</td>
        </tr>
        """

    recent_purchases_table = data_table("Recent Purchases", ["Tool", "Buyer", "Amount", "When"], recent_purchases_rows)

    return f"""
    {kpi_html}
    {pending_html}
    {alerts_html}
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
        {recent_tools_table}
        {recent_purchases_table}
    </div>
    """


# ── Tools Tab ────────────────────────────────────────────────────────────

async def render_tools_tab(db, request, pending):
    """Tools tab: pending cards at top, then full tools table with filters."""
    pending_count = len(pending)
    all_tools = await get_all_tools_admin(db)

    # --- Pending section ---
    pending_html = f'<h2 style="font-family:var(--font-display);margin-bottom:16px;color:var(--ink);">Pending Review ({pending_count})</h2>'
    if pending:
        pending_html += f'''
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
            pending_html += f"""
            <div class="card" style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
                    <div style="flex:1;min-width:200px;">
                        <strong style="font-size:16px;color:var(--ink);">{name}</strong>
                        <p style="color:var(--ink-muted);font-size:14px;margin-top:4px;">{tagline}</p>
                        <p style="font-size:14px;margin-top:8px;">
                            <a href="{t_url}" target="_blank" rel="noopener">{t_url}</a>
                        </p>
                        <p style="color:var(--ink-muted);font-size:14px;">Maker: {maker} &middot; Category: {cat} &middot; Price: {price_str}</p>
                    </div>
                    <div style="display:flex;gap:8px;">
                        <form method="post" action="/admin">
                            <input type="hidden" name="tool_id" value="{tid}">
                            <input type="hidden" name="action" value="approve">
                            <button type="submit" class="btn" style="background:#16a34a;color:white;padding:8px 16px;">
                                Approve
                            </button>
                        </form>
                        <form method="post" action="/admin">
                            <input type="hidden" name="tool_id" value="{tid}">
                            <input type="hidden" name="action" value="reject">
                            <button type="submit" class="btn" style="background:#dc2626;color:white;padding:8px 16px;">
                                Reject
                            </button>
                        </form>
                    </div>
                </div>
            </div>
            """
    else:
        pending_html += '<p style="color:var(--ink-muted);">No tools pending review.</p>'

    # --- Filter & Sort bar ---
    status_filter = request.query_params.get('status', '')
    cat_filter = request.query_params.get('category', '')
    search_q = request.query_params.get('q', '')
    sort_by = request.query_params.get('sort', 'newest')
    special_filter = request.query_params.get('filter', '')

    status_opts = ''
    for sv, sl in [('', 'All Status'), ('approved', 'Approved'), ('pending', 'Pending'), ('rejected', 'Rejected')]:
        sel = ' selected' if sv == status_filter else ''
        status_opts += f'<option value="{sv}"{sel}>{sl}</option>'

    filter_opts = ''
    for fv, fl in [('', 'All Tools'), ('unclaimed', 'Unclaimed'), ('verified', 'Verified'), ('boosted', 'Boosted')]:
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
        <input type="text" name="q" value="{escape(search_q)}" placeholder="Search tools..." style="padding:6px 12px;border:1px solid var(--border);border-radius:999px;font-size:13px;width:180px;">
        <select name="status" style="{select_style}" onchange="this.form.submit()">{status_opts}</select>
        <select name="filter" style="{select_style}" onchange="this.form.submit()">{filter_opts}</select>
        <select name="sort" style="{select_style}" onchange="this.form.submit()">{sort_opts}</select>
        <button type="submit" class="btn btn-primary" style="padding:6px 16px;font-size:13px;">Filter</button>
        <a href="/admin?tab=tools" style="font-size:12px;color:var(--ink-muted);">Clear</a>
    </form>
    '''

    # --- Apply filters ---
    filtered = list(all_tools)
    if status_filter:
        filtered = [t for t in filtered if t.get('status') == status_filter]
    if special_filter == 'unclaimed':
        filtered = [t for t in filtered if not t.get('maker_id')]
    elif special_filter == 'verified':
        filtered = [t for t in filtered if t.get('is_verified')]
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

    # --- Paginate ---
    per_page = 50
    total_filtered = len(filtered)
    total_pages = max(1, (total_filtered + per_page - 1) // per_page)
    page = int(request.query_params.get('page', '1'))
    page = max(1, min(page, total_pages))
    paginated_tools = filtered[(page-1)*per_page : page*per_page]

    count_line = f'<p style="font-size:13px;color:var(--ink-muted);margin-bottom:12px;">Showing {len(paginated_tools)} of {total_filtered} tools (page {page}/{total_pages})</p>'

    # --- All tools table ---
    all_html = '<h2 style="font-family:var(--font-display);margin:40px 0 16px;color:var(--ink);">All Tools</h2>'
    all_html += filter_bar + count_line
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
            t_price_p = t.get('price_pence')
            price_cell = f'\u00a3{t_price_p/100:.2f}' if t_price_p else 'Free'
            added_ago = time_ago(t.get('created_at'))
            # Magic link button (only for unclaimed tools)
            maker_id_val = t.get('maker_id')
            if not maker_id_val:
                magic_cell = f'''
                <td style="padding:10px 12px;">
                    <button onclick="generateMagicLink({t['id']}, this)"
                            style="padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;
                                   cursor:pointer;background:#00D4F5;color:#1A2D4A;border:none;
                                   font-family:var(--font-body);">
                        &#128279; Copy Link
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
                <td style="padding:10px 12px;">{price_cell}</td>
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
                <td style="font-size:12px;padding:10px 12px;">
                    {f'<span style="color:#00D4F5;font-weight:600;">{escape(str(t.get("boosted_competitor", "") or ""))}</span>' if t.get('boosted_competitor') else '<span style="color:var(--ink-muted);">&#8212;</span>'}
                    <form method="post" action="/admin" style="display:inline;margin-left:4px;">
                        <input type="hidden" name="action" value="toggle_boost">
                        <input type="hidden" name="tool_id" value="{t['id']}">
                        <input type="text" name="competitor" value="{escape(str(t.get('boosted_competitor', '') or ''))}" placeholder="e.g. google-analytics"
                               style="width:110px;font-size:11px;padding:2px 6px;border:1px solid var(--border);border-radius:4px;">
                        <button type="submit" style="font-size:11px;padding:2px 8px;background:#00D4F5;color:#1A2D4A;border:none;border-radius:4px;cursor:pointer;font-weight:600;">
                            Set
                        </button>
                    </form>
                </td>
                <td style="padding:10px 12px;">
                    <details style="position:relative;">
                        <summary style="cursor:pointer;padding:4px 12px;border-radius:999px;font-size:12px;
                                        font-weight:600;background:var(--cream-dark);border:1px solid var(--border);
                                        color:var(--ink-light);list-style:none;">&#9733; Feature</summary>
                        <div style="position:absolute;right:0;top:100%;z-index:10;background:white;border:1px solid var(--border);
                                    border-radius:var(--radius-sm);padding:12px;width:260px;box-shadow:0 4px 16px rgba(0,0,0,0.1);margin-top:4px;">
                            <form method="post" action="/admin">
                                <input type="hidden" name="tool_id" value="{t['id']}">
                                <input type="hidden" name="action" value="feature">
                                <input type="text" name="headline" placeholder="Headline (optional)" class="form-input"
                                       style="font-size:12px;padding:6px 10px;margin-bottom:8px;">
                                <input type="text" name="feature_desc" placeholder="Short blurb (optional)" class="form-input"
                                       style="font-size:12px;padding:6px 10px;margin-bottom:8px;">
                                <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:6px;font-size:12px;">
                                    Set as Tool of the Week
                                </button>
                            </form>
                            <form method="post" action="/admin" style="margin-top:8px;">
                                <input type="hidden" name="action" value="clear_featured">
                                <button type="submit" class="btn" style="width:100%;justify-content:center;padding:6px;font-size:12px;background:#FEE2E2;color:#991B1B;border:1px solid #FECACA;">
                                    Clear Tool of the Week
                                </button>
                            </form>
                        </div>
                    </details>
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
        all_html += f"""
        <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:14px;">
                <thead>
                    <tr style="border-bottom:2px solid var(--border);text-align:left;">
                        <th style="padding:10px 12px;color:var(--ink);">Name</th>
                        <th style="padding:10px 12px;color:var(--ink);">Status</th>
                        <th style="padding:10px 12px;color:var(--ink);">Upvotes</th>
                        <th style="padding:10px 12px;color:var(--ink);">Price</th>
                        <th style="padding:10px 12px;color:var(--ink);">Category</th>
                        <th style="padding:10px 12px;color:var(--ink);">Added</th>
                        <th style="padding:10px 12px;color:var(--ink);">Verified</th>
                        <th style="padding:10px 12px;color:var(--ink);">Ejectable</th>
                        <th style="padding:10px 12px;color:var(--ink);">Boost</th>
                        <th style="padding:10px 12px;color:var(--ink);">Feature</th>
                        <th style="padding:10px 12px;color:var(--ink);">Delete</th>
                        <th style="padding:10px 12px;font-size:12px;">Magic Link</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """
        # --- Pagination controls ---
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
        all_html += pagination_html
    else:
        all_html += '<p style="color:var(--ink-muted);">No tools match the current filters.</p>'

    section_html = pending_html + '<hr style="margin:32px 0;border:none;border-top:1px solid var(--border);">' + all_html
    section_html += """
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
    return section_html


# ── People Tab ───────────────────────────────────────────────────────────

async def render_people_tab(db, request):
    """People tab: unified view of makers and users with role badges."""
    role_filter = request.query_params.get('role', '')

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

    # Role filter pills
    pills = ''
    for val, label in [('', 'All'), ('makers', 'Makers'), ('users', 'Users')]:
        active_style = 'background:var(--slate);color:white;' if val == role_filter else 'background:var(--cream-dark);color:var(--ink-muted);border:1px solid var(--border);'
        pills += f'<a href="/admin?tab=people{f"&role={val}" if val else ""}" style="{active_style}padding:6px 14px;font-size:13px;border-radius:999px;text-decoration:none;font-weight:600;display:inline-block;">{label}</a> '

    filter_html = f'<div style="display:flex;gap:8px;margin-bottom:20px;">{pills}</div>'

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


# ── Content Tab ──────────────────────────────────────────────────────────

async def render_content_tab(db, request):
    """Content tab: collapsible sections for stacks and reviews."""
    all_tools = await get_all_tools_admin(db)
    approved_tools = [t for t in all_tools if t.get('status') == 'approved']
    display_tools = approved_tools[:200]

    # ── Stacks section ──
    all_stacks = await get_all_stacks(db)
    stacks_html = _render_stacks_section(all_stacks, display_tools, len(approved_tools))

    # ── Reviews section ──
    reviews = await get_all_reviews_admin(db)
    reviews_html = _render_reviews_section(reviews)

    return f"""
    {stacks_html}
    <div style="margin-top:20px;">{reviews_html}</div>
    """


def _render_stacks_section(all_stacks, display_tools, total_approved):
    """Collapsible stacks management section."""
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
    <details>
        <summary style="font-family:var(--font-display);font-size:20px;color:var(--ink);cursor:pointer;padding:12px 0;
                        border-bottom:1px solid var(--border);margin-bottom:16px;list-style:none;display:flex;align-items:center;gap:8px;">
            <span style="font-size:14px;">&#9654;</span> Stacks ({len(all_stacks)})
        </summary>
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
    </details>
    """


def _render_reviews_section(reviews):
    """Collapsible reviews management section."""
    total_reviews = len(reviews)
    display_reviews = reviews[:50]

    items_html = ''
    if display_reviews:
        if total_reviews > 50:
            items_html += f'<p style="color:var(--ink-muted);font-size:13px;margin-bottom:12px;">Showing most recent 50 of {total_reviews} reviews</p>'
        for rv in display_reviews:
            rv_tool_name = escape(str(rv.get('tool_name', 'Unknown')))
            rv_tool_slug = escape(str(rv.get('tool_slug', '')))
            rv_reviewer = escape(str(rv.get('reviewer_name', 'Anonymous')))
            rv_rating = int(rv.get('rating', 0))
            rv_body = escape(str(rv.get('body', '')))
            rv_id = rv['id']
            stars_html = '<span style="color:var(--gold);font-size:16px;">' + ('&#9733;' * rv_rating) + ('&#9734;' * (5 - rv_rating)) + '</span>'
            items_html += f"""
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
        items_html = '<p style="color:var(--ink-muted);padding:12px 0;">No reviews yet.</p>'

    return f"""
    <details>
        <summary style="font-family:var(--font-display);font-size:20px;color:var(--ink);cursor:pointer;padding:12px 0;
                        border-bottom:1px solid var(--border);margin-bottom:16px;list-style:none;display:flex;align-items:center;gap:8px;">
            <span style="font-size:14px;">&#9654;</span> Reviews ({total_reviews})
        </summary>
        {items_html}
    </details>
    """


# ── Growth Tab ───────────────────────────────────────────────────────────

async def render_growth_tab(db, request):
    """Growth tab: sub-nav with Traffic & Funnels, Search, Email, Social sections."""
    section = request.query_params.get('section', 'traffic')
    html = growth_sub_nav(section)

    if section == 'traffic':
        html += await render_traffic_section(db, request)
        html += await render_funnels_section(db)
    elif section == 'search':
        html += await render_search_section(db)
    elif section == 'email':
        html += await render_email_section(db, request)
    elif section == 'social':
        html += await render_social_section(db)
    else:
        html += await render_traffic_section(db, request)
        html += await render_funnels_section(db)

    return html


# ── POST /admin ──────────────────────────────────────────────────────────

@router.post("/admin")
async def admin_post(request: Request):
    form = await request.form()

    # Login
    if "password" in form:
        password = str(form["password"])
        if _secrets.compare_digest(password, ADMIN_PASSWORD):
            token = make_session_token(password)
            response = RedirectResponse(url="/admin", status_code=303)
            response.set_cookie(key="indiestack_admin", value=token, httponly=True, samesite="lax", secure=True, max_age=8*3600)
            return response
        else:
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
            if new_status == "approved":
                # ── Competitor pings + approval notification ──
                try:
                    approved_tool = await get_tool_by_id(db, tool_id_int)
                    if approved_tool:
                        cat_id = approved_tool['category_id']
                        cat_name = approved_tool.get('category_name', '')
                        tool_name = approved_tool['name']
                        competitors = await get_makers_in_category(db, cat_id, exclude_tool_id=tool_id_int)
                        for comp in competitors:
                            if comp.get('email'):
                                try:
                                    await send_email(
                                        comp['email'],
                                        f"New tool in {cat_name}: {tool_name}",
                                        competitor_ping_html(
                                            comp.get('maker_name', comp.get('name', 'there')),
                                            tool_name,
                                            cat_name,
                                            f"{BASE_URL}/dashboard"
                                        )
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
            return RedirectResponse(url="/admin?tab=content&toast=Review+deleted", status_code=303)
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
            return RedirectResponse(url="/admin?tab=content&toast=Stack+created", status_code=303)
        elif action == "add_to_stack":
            stack_id_val = int(form.get("stack_id", 0) or 0)
            tool_id_val = int(form.get("tool_id", 0) or 0)
            if stack_id_val and tool_id_val:
                await add_tool_to_stack(db, stack_id_val, tool_id_val)
            return RedirectResponse(url="/admin?tab=content&toast=Tool+added+to+stack", status_code=303)
        elif action == "remove_from_stack":
            stack_id_val = int(form.get("stack_id", 0) or 0)
            tool_id_val = int(form.get("tool_id", 0) or 0)
            if stack_id_val and tool_id_val:
                await remove_tool_from_stack(db, stack_id_val, tool_id_val)
            return RedirectResponse(url="/admin?tab=content&toast=Tool+removed+from+stack", status_code=303)
        elif action == "delete_stack":
            stack_id_val = int(form.get("stack_id", 0) or 0)
            if stack_id_val:
                await delete_stack(db, stack_id_val)
            return RedirectResponse(url="/admin?tab=content&toast=Stack+deleted", status_code=303)
        return RedirectResponse(url="/admin", status_code=303)

    return RedirectResponse(url="/admin", status_code=303)


# ── Redirect routes (old analytics/outreach URLs) ────────────────────────

@router.get("/admin/analytics")
async def admin_analytics_redirect(request: Request):
    tab = request.query_params.get("tab", "overview")
    section_map = {"overview": "traffic", "funnels": "traffic", "search": "search", "growth": "traffic"}
    return RedirectResponse(url=f"/admin?tab=growth&section={section_map.get(tab, 'traffic')}", status_code=302)


@router.get("/admin/outreach")
async def admin_outreach_redirect(request: Request):
    tab = request.query_params.get("tab", "email")
    section_map = {"email": "email", "magic": "email", "makers": "email", "stale": "email", "social": "social"}
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
    toast_html = f'<div style="background:#DCFCE7;color:#166534;padding:10px 16px;border-radius:var(--radius);margin-bottom:16px;font-size:14px;">{escape(toast)}</div>' if toast else ''

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
                      integration_curl=integration_curl)

    return RedirectResponse(url=f"/admin/edit/{tool_id}?toast=Tool+updated+successfully", status_code=303)

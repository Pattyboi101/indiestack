"""Admin dashboard — password-protected tool review + bulk import."""

import json
import secrets as _secrets
from datetime import datetime, timedelta
from html import escape
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.routes.components import page_shell
from indiestack.db import (get_pending_tools, get_all_tools_admin, update_tool_status, toggle_verified, toggle_ejectable,
                           bulk_create_tools, get_purchase_stats, set_featured_tool, get_all_collections,
                           create_collection, add_tool_to_collection, remove_tool_from_collection, delete_collection,
                           get_collection_by_slug, get_all_reviews_admin, delete_review, get_all_makers_admin, update_maker,
                           toggle_tool_boost, create_stack, get_all_stacks, add_tool_to_stack, remove_tool_from_stack, delete_stack,
                           get_tool_by_id, get_makers_in_category)
from indiestack.email import send_email, competitor_ping_html, tool_approved_html
from indiestack.auth import check_admin_session, make_session_token, ADMIN_PASSWORD

router = APIRouter()


def _time_ago(dt_str):
    """Format a datetime string as relative time (e.g. '3d ago', '2w ago')."""
    if not dt_str:
        return '\u2014'
    try:
        dt = datetime.fromisoformat(str(dt_str).replace('Z', '+00:00').split('+')[0])
        delta = datetime.utcnow() - dt
        if delta.days > 30:
            return f'{delta.days // 30}mo ago'
        if delta.days > 0:
            return f'{delta.days}d ago'
        hours = delta.seconds // 3600
        if hours > 0:
            return f'{hours}h ago'
        return 'just now'
    except (ValueError, TypeError):
        return '\u2014'


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


@router.get("/admin", response_class=HTMLResponse)
async def admin_get(request: Request):
    if not check_admin_session(request):
        return HTMLResponse(page_shell("Admin Login", login_form_html(), user=request.state.user))

    db = request.state.db
    pending = await get_pending_tools(db)
    all_tools = await get_all_tools_admin(db)
    stats = await get_purchase_stats(db)

    # ── URL-routed tab ────────────────────────────────────────────────
    tab = request.query_params.get('tab', 'tools')

    tab_items = [
        ('tools', 'Tools'),
        ('collections', 'Collections'),
        ('stacks', 'Stacks'),
        ('reviews', 'Reviews'),
        ('makers', 'Makers'),
        ('import', 'Bulk Import'),
    ]
    tab_nav = '<div style="display:flex;gap:0;border-bottom:2px solid var(--border);margin-bottom:24px;">'
    for tab_slug, tab_label in tab_items:
        active_style = 'color:var(--terracotta);border-bottom:2px solid var(--terracotta);font-weight:700;' if tab == tab_slug else 'color:var(--ink-muted);border-bottom:2px solid transparent;'
        tab_nav += f'<a href="/admin?tab={tab_slug}" style="padding:10px 20px;font-size:14px;text-decoration:none;margin-bottom:-2px;{active_style}">{tab_label}</a>'
    tab_nav += '</div>'

    # ── KPI action cards ──────────────────────────────────────────────
    pending_count = len(pending)
    unclaimed_count_row = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE maker_id IS NULL AND status = 'approved'")
    unclaimed_count = (await unclaimed_count_row.fetchone())['cnt']
    boost_count_row = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE is_boosted = 1 AND boost_expires_at > datetime('now')")
    boost_count = (await boost_count_row.fetchone())['cnt']
    total_tools = len(all_tools)

    kpi_cards = f'''
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px;">
        <a href="/admin?tab=tools&status=pending" class="card" style="text-decoration:none;text-align:center;padding:16px;{('border-color:#EA580C;background:#FFF7ED;' if pending_count else '')}">
            <div style="font-size:28px;font-weight:700;color:var(--ink);font-family:var(--font-display);">{pending_count}</div>
            <div style="font-size:13px;color:var(--ink-muted);font-weight:600;">Pending Review</div>
        </a>
        <a href="/admin?tab=tools&filter=unclaimed" class="card" style="text-decoration:none;text-align:center;padding:16px;">
            <div style="font-size:28px;font-weight:700;color:var(--ink);font-family:var(--font-display);">{unclaimed_count}</div>
            <div style="font-size:13px;color:var(--ink-muted);font-weight:600;">Unclaimed Tools</div>
        </a>
        <a href="/admin?tab=tools" class="card" style="text-decoration:none;text-align:center;padding:16px;">
            <div style="font-size:28px;font-weight:700;color:var(--ink);font-family:var(--font-display);">{total_tools}</div>
            <div style="font-size:13px;color:var(--ink-muted);font-weight:600;">Total Tools</div>
        </a>
        <a href="/admin?tab=tools&filter=boosted" class="card" style="text-decoration:none;text-align:center;padding:16px;">
            <div style="font-size:28px;font-weight:700;color:var(--ink);font-family:var(--font-display);">{boost_count}</div>
            <div style="font-size:13px;color:var(--ink-muted);font-weight:600;">Active Boosts</div>
        </a>
    </div>
    '''

    # ── Section content based on active tab ───────────────────────────
    section_html = ''

    if tab == 'tools':
        # --- Pending section (always shown on tools tab) ---
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

        # --- Apply filters to all_tools ---
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

        # --- Paginate filtered results ---
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
                added_ago = _time_ago(t.get('created_at'))
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
                    <td style="padding:10px 12px;font-weight:600;color:var(--ink);">{escape(str(t['name']))} {v_badge} {e_badge}</td>
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
                            </div>
                        </details>
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

    elif tab == 'collections':
        # Collections management
        all_collections = await get_all_collections(db)
        collections_admin_html = '<h2 style="font-family:var(--font-display);margin-bottom:16px;color:var(--ink);">Collections</h2>'
        collections_admin_html += """
        <div class="card" style="margin-bottom:16px;padding:16px;">
            <form method="post" action="/admin" style="display:flex;gap:8px;align-items:flex-end;flex-wrap:wrap;">
                <input type="hidden" name="action" value="create_collection">
                <div style="flex:1;min-width:150px;">
                    <label style="font-size:12px;font-weight:600;color:var(--ink-muted);">Title</label>
                    <input type="text" name="coll_title" class="form-input" style="font-size:13px;padding:6px 10px;" placeholder="e.g. Best Free Invoicing Tools" required>
                </div>
                <div style="flex:1;min-width:150px;">
                    <label style="font-size:12px;font-weight:600;color:var(--ink-muted);">Description</label>
                    <input type="text" name="coll_desc" class="form-input" style="font-size:13px;padding:6px 10px;" placeholder="Short description">
                </div>
                <div style="width:60px;">
                    <label style="font-size:12px;font-weight:600;color:var(--ink-muted);">Emoji</label>
                    <input type="text" name="coll_emoji" class="form-input" style="font-size:13px;padding:6px 10px;" placeholder="&#128230;">
                </div>
                <button type="submit" class="btn btn-primary" style="padding:6px 16px;font-size:13px;">Create</button>
            </form>
        </div>
        """
        if all_collections:
            for c in all_collections:
                c_emoji = c.get('cover_emoji', '') or ''
                c_title = escape(str(c['title']))
                c_count = c.get('tool_count', 0)
                collections_admin_html += f"""
                <div class="card" style="margin-bottom:8px;padding:12px 16px;display:flex;justify-content:space-between;align-items:center;">
                    <div>
                        <span style="margin-right:8px;">{c_emoji}</span>
                        <strong>{c_title}</strong>
                        <span class="text-muted text-sm" style="margin-left:8px;">{c_count} tools</span>
                    </div>
                    <div style="display:flex;gap:8px;align-items:center;">
                        <details style="position:relative;">
                            <summary style="cursor:pointer;padding:4px 12px;border-radius:999px;font-size:12px;
                                            font-weight:600;background:var(--cream-dark);border:1px solid var(--border);
                                            color:var(--ink-light);list-style:none;">+ Add Tool</summary>
                            <div style="position:absolute;right:0;top:100%;z-index:10;background:white;border:1px solid var(--border);
                                        border-radius:var(--radius-sm);padding:12px;width:200px;box-shadow:0 4px 16px rgba(0,0,0,0.1);margin-top:4px;">
                                <form method="post" action="/admin">
                                    <input type="hidden" name="action" value="add_to_collection">
                                    <input type="hidden" name="collection_id" value="{c['id']}">
                                    <select name="tool_id" class="form-select" style="font-size:12px;padding:6px;margin-bottom:8px;">
                """
                # Cap dropdown at 200 tools to prevent massive HTML
                approved_for_dropdown = [t for t in all_tools if t.get('status') == 'approved']
                display_tools_coll = approved_for_dropdown[:200]
                for t in display_tools_coll:
                    collections_admin_html += f'<option value="{t["id"]}">{escape(str(t["name"]))}</option>'
                if len(approved_for_dropdown) > 200:
                    collections_admin_html += f'<option disabled>... and {len(approved_for_dropdown) - 200} more</option>'
                collections_admin_html += f"""
                                    </select>
                                    <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:4px;font-size:12px;">Add</button>
                                </form>
                            </div>
                        </details>
                        <form method="post" action="/admin" style="margin:0;">
                            <input type="hidden" name="action" value="delete_collection">
                            <input type="hidden" name="collection_id" value="{c['id']}">
                            <button type="submit" style="padding:4px 10px;border-radius:999px;font-size:11px;font-weight:600;
                                    cursor:pointer;background:#FEE2E2;color:#991B1B;border:1px solid #FECACA;"
                                    onclick="return confirm('Delete this collection?')">Delete</button>
                        </form>
                    </div>
                </div>
                """
        else:
            collections_admin_html += '<p style="color:var(--ink-muted);">No collections yet.</p>'
        section_html = collections_admin_html

    elif tab == 'stacks':
        # Stacks management
        all_stacks = await get_all_stacks(db)
        stacks_rows = ''
        for s in all_stacks:
            stacks_rows += f'''
            <tr>
                <td>{s['id']}</td>
                <td>{escape(str(s['title']))}</td>
                <td>{s.get('cover_emoji', '')}</td>
                <td>{s.get('tool_count', 0)}</td>
                <td>{s.get('discount_percent', 15)}%</td>
                <td>
                    <form method="post" style="display:inline;">
                        <input type="hidden" name="action" value="delete_stack">
                        <input type="hidden" name="stack_id" value="{s['id']}">
                        <button type="submit" style="background:#e74c3c;color:#fff;border:none;padding:4px 10px;border-radius:4px;font-size:12px;cursor:pointer;">Delete</button>
                    </form>
                </td>
            </tr>'''

        approved_tools_for_stacks = [t for t in all_tools if t.get('status') == 'approved']
        # Cap dropdown at 200 tools to prevent massive HTML
        display_tools_stacks = approved_tools_for_stacks[:200]
        tool_options = ''.join(f'<option value="{t["id"]}">{escape(str(t["name"]))}</option>' for t in display_tools_stacks)
        if len(approved_tools_for_stacks) > 200:
            tool_options += f'<option disabled>... and {len(approved_tools_for_stacks) - 200} more</option>'
        stack_options = ''.join(f'<option value="{s["id"]}">{escape(str(s["title"]))}</option>' for s in all_stacks)

        stacks_section = f'''
<h2 style="font-family:var(--font-display);margin-bottom:16px;color:var(--ink);">Vibe Stacks</h2>

<!-- Create Stack -->
<div class="card" style="padding:20px;margin-bottom:20px;">
    <h3 style="margin-bottom:12px;font-size:16px;">Create New Stack</h3>
    <form method="post" style="display:flex;gap:8px;flex-wrap:wrap;align-items:end;">
        <input type="hidden" name="action" value="create_stack">
        <div>
            <label style="font-size:12px;display:block;margin-bottom:4px;">Title</label>
            <input type="text" name="stack_title" required style="padding:6px 10px;border:1px solid #ddd;border-radius:4px;">
        </div>
        <div>
            <label style="font-size:12px;display:block;margin-bottom:4px;">Emoji</label>
            <input type="text" name="stack_emoji" placeholder="&#128230;" style="padding:6px 10px;border:1px solid #ddd;border-radius:4px;width:60px;">
        </div>
        <div>
            <label style="font-size:12px;display:block;margin-bottom:4px;">Discount %</label>
            <input type="number" name="stack_discount" value="15" min="0" max="50" style="padding:6px 10px;border:1px solid #ddd;border-radius:4px;width:70px;">
        </div>
        <div>
            <label style="font-size:12px;display:block;margin-bottom:4px;">Description</label>
            <input type="text" name="stack_desc" placeholder="Optional" style="padding:6px 10px;border:1px solid #ddd;border-radius:4px;width:200px;">
        </div>
        <button type="submit" class="btn btn-primary" style="padding:6px 16px;font-size:13px;">Create</button>
    </form>
</div>

{f"""<!-- Add Tool to Stack -->
<div class="card" style="padding:20px;margin-bottom:20px;">
    <h3 style="margin-bottom:12px;font-size:16px;">Add Tool to Stack</h3>
    <form method="post" style="display:flex;gap:8px;align-items:end;">
        <input type="hidden" name="action" value="add_to_stack">
        <div>
            <label style="font-size:12px;display:block;margin-bottom:4px;">Stack</label>
            <select name="stack_id" style="padding:6px 10px;border:1px solid #ddd;border-radius:4px;">{stack_options}</select>
        </div>
        <div>
            <label style="font-size:12px;display:block;margin-bottom:4px;">Tool</label>
            <select name="tool_id" style="padding:6px 10px;border:1px solid #ddd;border-radius:4px;">{tool_options}</select>
        </div>
        <button type="submit" class="btn btn-primary" style="padding:6px 16px;font-size:13px;">Add</button>
    </form>
</div>""" if all_stacks and approved_tools_for_stacks else ""}

<!-- Stacks Table -->
<table style="width:100%;border-collapse:collapse;font-size:14px;">
    <thead>
        <tr style="border-bottom:2px solid var(--ink);text-align:left;">
            <th style="padding:8px;">ID</th>
            <th style="padding:8px;">Title</th>
            <th style="padding:8px;">Emoji</th>
            <th style="padding:8px;">Tools</th>
            <th style="padding:8px;">Discount</th>
            <th style="padding:8px;">Actions</th>
        </tr>
    </thead>
    <tbody>{stacks_rows}</tbody>
</table>
'''
        section_html = stacks_section

    elif tab == 'reviews':
        all_reviews = await get_all_reviews_admin(db)
        total_reviews = len(all_reviews)
        all_reviews = all_reviews[:50]  # Show 50 most recent
        reviews_admin_html = f'<h2 style="font-family:var(--font-display);margin-bottom:16px;color:var(--ink);">Reviews ({total_reviews})</h2>'
        if total_reviews > 50:
            reviews_admin_html += f'<p style="color:var(--ink-muted);font-size:13px;margin-bottom:12px;">Showing most recent 50 of {total_reviews} reviews</p>'
        if all_reviews:
            for rv in all_reviews:
                rv_tool_name = escape(str(rv.get('tool_name', 'Unknown')))
                rv_tool_slug = escape(str(rv.get('tool_slug', '')))
                rv_reviewer = escape(str(rv.get('reviewer_name', 'Anonymous')))
                rv_rating = int(rv.get('rating', 0))
                rv_body = escape(str(rv.get('body', '')))
                rv_id = rv['id']
                stars_html = '<span style="color:var(--gold);font-size:16px;">' + ('&#9733;' * rv_rating) + ('&#9734;' * (5 - rv_rating)) + '</span>'
                reviews_admin_html += f"""
                <div class="card" style="margin-bottom:12px;padding:16px;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;">
                        <div style="flex:1;">
                            <div style="margin-bottom:4px;">
                                <a href="/tool/{rv_tool_slug}" style="font-weight:600;color:var(--terracotta);text-decoration:none;">{rv_tool_name}</a>
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
            reviews_admin_html += '<p style="color:var(--ink-muted);">No reviews yet.</p>'
        section_html = reviews_admin_html

    elif tab == 'makers':
        all_makers = await get_all_makers_admin(db)
        total_makers = len(all_makers)
        all_makers = all_makers[:50]  # Show first 50 makers
        makers_admin_html = f'<h2 style="font-family:var(--font-display);margin-bottom:16px;color:var(--ink);">Makers ({total_makers})</h2>'
        if total_makers > 50:
            makers_admin_html += f'<p style="color:var(--ink-muted);font-size:13px;margin-bottom:12px;">Showing first 50 of {total_makers} makers</p>'
        if all_makers:
            maker_rows = ''
            for mk in all_makers:
                mk_name = escape(str(mk['name']))
                mk_slug = escape(str(mk['slug']))
                mk_status = str(mk.get('indie_status', '') or '')
                mk_tools = mk.get('tool_count', 0)
                status_options = ''
                for sv, sl in [('', 'Not set'), ('solo', 'Solo'), ('small_team', 'Small Team'), ('company', 'Company')]:
                    selected = ' selected' if sv == mk_status else ''
                    status_options += f'<option value="{sv}"{selected}>{sl}</option>'
                maker_rows += f"""
                <tr style="border-bottom:1px solid var(--border);">
                    <td style="padding:10px 12px;"><a href="/maker/{mk_slug}" style="font-weight:600;color:var(--ink);">{mk_name}</a></td>
                    <td style="padding:10px 12px;">{mk_tools}</td>
                    <td style="padding:10px 12px;">
                        <form method="post" action="/admin" style="display:flex;gap:6px;margin:0;">
                            <input type="hidden" name="action" value="update_indie_status">
                            <input type="hidden" name="maker_id" value="{mk['id']}">
                            <select name="indie_status" class="form-select" style="font-size:12px;padding:4px 8px;border-radius:999px;max-width:130px;">{status_options}</select>
                            <button type="submit" style="padding:4px 10px;border-radius:999px;font-size:11px;font-weight:600;cursor:pointer;background:var(--cream-dark);color:var(--ink-light);border:1px solid var(--border);">Set</button>
                        </form>
                    </td>
                </tr>
                """
            makers_admin_html += f"""
            <div style="overflow-x:auto;">
                <table style="width:100%;border-collapse:collapse;font-size:14px;">
                    <thead><tr style="border-bottom:2px solid var(--border);text-align:left;">
                        <th style="padding:10px 12px;">Name</th><th style="padding:10px 12px;">Tools</th><th style="padding:10px 12px;">Indie Status</th>
                    </tr></thead>
                    <tbody>{maker_rows}</tbody>
                </table>
            </div>
            """
        else:
            makers_admin_html += '<p style="color:var(--ink-muted);">No makers yet.</p>'
        section_html = makers_admin_html

    elif tab == 'import':
        section_html = f"""
        <h2 style="font-family:var(--font-display);margin-bottom:16px;color:var(--ink);">Bulk Import Tools</h2>
        <p style="color:var(--ink-muted);margin-bottom:24px;">
            Paste a JSON array of tools below. Each tool needs: <code>name</code>, <code>tagline</code>,
            <code>description</code>, <code>url</code>, <code>category</code> (must match an existing category name).
            Optional: <code>maker_name</code>, <code>maker_url</code>, <code>tags</code>.
            All imported tools are <strong>auto-approved</strong>.
        </p>
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
        """

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:960px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Admin Dashboard</h1>
            <a href="/admin/analytics" class="btn" style="background:var(--terracotta);color:white;">
                Analytics
            </a>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px;">
            <div class="card" style="text-align:center;padding:16px;">
                <div style="color:var(--ink-muted);font-size:14px;">Total Purchases</div>
                <div style="font-family:var(--font-display);font-size:28px;margin-top:4px;color:var(--ink);">{stats['total_purchases']}</div>
            </div>
            <div class="card" style="text-align:center;padding:16px;">
                <div style="color:var(--ink-muted);font-size:14px;">Total Revenue</div>
                <div style="font-family:var(--font-display);font-size:28px;color:var(--terracotta);margin-top:4px;">&pound;{stats['total_revenue'] / 100:.2f}</div>
            </div>
            <div class="card" style="text-align:center;padding:16px;">
                <div style="color:var(--ink-muted);font-size:14px;">Platform Commission</div>
                <div style="font-family:var(--font-display);font-size:28px;color:var(--slate-dark);margin-top:4px;">&pound;{stats['total_commission'] / 100:.2f}</div>
            </div>
        </div>
        {kpi_cards}
        {tab_nav}
        {section_html}
    </div>
    """
    return HTMLResponse(page_shell("Admin Dashboard", body, user=request.state.user))


@router.post("/admin")
async def admin_post(request: Request):
    form = await request.form()

    # Login
    if "password" in form:
        password = str(form["password"])
        if _secrets.compare_digest(password, ADMIN_PASSWORD):
            token = make_session_token(password)
            response = RedirectResponse(url="/admin", status_code=303)
            response.set_cookie(key="indiestack_admin", value=token, httponly=True, samesite="lax")
            return response
        else:
            return HTMLResponse(page_shell("Admin Login", login_form_html("Invalid password."), user=request.state.user))

    # Approve / Reject / Verify
    if "action" in form:
        if not check_admin_session(request):
            return RedirectResponse(url="/admin", status_code=303)

        def _safe_int(val) -> int | None:
            try:
                return int(val) if val else None
            except (ValueError, TypeError):
                return None

        tool_id_int = _safe_int(form.get("tool_id"))
        action = str(form.get("action", ""))

        # Bulk actions
        if action == "approve_all":
            db = request.state.db
            cursor = await db.execute("SELECT id FROM tools WHERE status = 'pending'")
            pending_ids = [r['id'] for r in await cursor.fetchall()]
            for pid in pending_ids:
                await update_tool_status(db, pid, "approved")
        elif action == "reject_all":
            db = request.state.db
            cursor = await db.execute("SELECT id FROM tools WHERE status = 'pending'")
            pending_ids = [r['id'] for r in await cursor.fetchall()]
            for pid in pending_ids:
                await update_tool_status(db, pid, "rejected")
        elif tool_id_int and action in ("approve", "reject"):
            new_status = "approved" if action == "approve" else "rejected"
            db = request.state.db
            await update_tool_status(db, tool_id_int, new_status)
            if new_status == "approved":
                # ── Round 9: Competitor pings + approval notification ──
                try:
                    approved_tool = await get_tool_by_id(db, tool_id_int)
                    if approved_tool:
                        cat_id = approved_tool['category_id']
                        cat_name = approved_tool.get('category_name', '')
                        tool_name = approved_tool['name']
                        # Email competitor makers in the same category
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
                                            "https://indiestack.fly.dev/dashboard"
                                        )
                                    )
                                except Exception:
                                    pass
                except Exception:
                    pass  # Don't break admin flow if emails fail

                # Credit referral boost if this tool's maker was referred
                try:
                    updated_tool = await get_tool_by_id(db, tool_id_int)
                    if updated_tool and updated_tool.get('maker_id'):
                        # Find the user who owns this maker
                        maker_user_cursor = await db.execute(
                            "SELECT id, referred_by FROM users WHERE maker_id = ?",
                            (updated_tool['maker_id'],))
                        maker_user = await maker_user_cursor.fetchone()
                        if maker_user and maker_user['referred_by']:
                            # Check this is the first approved tool from this referred user
                            first_check = await db.execute(
                                "SELECT COUNT(*) as cnt FROM tools WHERE maker_id = ? AND status = 'approved'",
                                (updated_tool['maker_id'],))
                            first_row = await first_check.fetchone()
                            if first_row and first_row['cnt'] == 1:  # Just this one was approved
                                from indiestack.db import credit_referral_boost
                                await credit_referral_boost(db, maker_user['referred_by'], 10)
                except Exception:
                    pass  # Don't let referral credit failure block approval
        elif tool_id_int and action == "toggle_verified":
            await toggle_verified(request.state.db, tool_id_int)
        elif tool_id_int and action == "toggle_ejectable":
            await toggle_ejectable(request.state.db, tool_id_int)
        elif tool_id_int and action == "feature":
            headline = str(form.get("headline", "")).strip()
            feature_desc = str(form.get("feature_desc", "")).strip()
            await set_featured_tool(request.state.db, tool_id_int, headline, feature_desc)
        elif action == "create_collection":
            coll_title = str(form.get("coll_title", "")).strip()
            coll_desc = str(form.get("coll_desc", "")).strip()
            coll_emoji = str(form.get("coll_emoji", "")).strip()
            if coll_title:
                await create_collection(request.state.db, title=coll_title, description=coll_desc, cover_emoji=coll_emoji)
        elif action == "add_to_collection" and tool_id_int:
            coll_id = _safe_int(form.get("collection_id"))
            if coll_id:
                await add_tool_to_collection(request.state.db, coll_id, tool_id_int)
        elif action == "remove_from_collection" and tool_id_int:
            coll_id = _safe_int(form.get("collection_id"))
            if coll_id:
                await remove_tool_from_collection(request.state.db, coll_id, tool_id_int)
        elif action == "delete_collection":
            coll_id = _safe_int(form.get("collection_id"))
            if coll_id:
                await delete_collection(request.state.db, coll_id)
        elif action == "delete_review":
            review_id = _safe_int(form.get("review_id"))
            if review_id:
                await delete_review(request.state.db, review_id)
        elif action == "toggle_boost":
            tool_id = int(form.get("tool_id", 0))
            competitor = str(form.get("competitor", "")).strip().lower().replace(" ", "-")
            if tool_id:
                await toggle_tool_boost(request.state.db, tool_id, competitor)
        elif action == "update_indie_status":
            maker_id_val = _safe_int(form.get("maker_id"))
            ind_status = str(form.get("indie_status", ""))
            if maker_id_val and ind_status in ('', 'solo', 'small_team', 'company'):
                await update_maker(request.state.db, maker_id_val, indie_status=ind_status)
        elif action == "create_stack":
            stack_title = str(form.get("stack_title", "")).strip()
            stack_desc = str(form.get("stack_desc", "")).strip()
            stack_emoji = str(form.get("stack_emoji", "")).strip() or "\U0001F4E6"
            stack_discount = int(form.get("stack_discount", 15) or 15)
            if stack_title:
                await create_stack(request.state.db, title=stack_title, description=stack_desc,
                                  cover_emoji=stack_emoji, discount_percent=stack_discount)
        elif action == "add_to_stack":
            stack_id_val = int(form.get("stack_id", 0) or 0)
            tool_id_val = int(form.get("tool_id", 0) or 0)
            if stack_id_val and tool_id_val:
                await add_tool_to_stack(request.state.db, stack_id_val, tool_id_val)
        elif action == "delete_stack":
            stack_id_val = int(form.get("stack_id", 0) or 0)
            if stack_id_val:
                await delete_stack(request.state.db, stack_id_val)
        return RedirectResponse(url="/admin", status_code=303)

    return RedirectResponse(url="/admin", status_code=303)


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


# ── Analytics ────────────────────────────────────────────────────────────

@router.get("/admin/analytics", response_class=HTMLResponse)
async def admin_analytics(request: Request):
    if not check_admin_session(request):
        return RedirectResponse(url="/admin", status_code=303)

    db = request.state.db
    period = request.query_params.get("period", "7")

    # Determine date filter
    now = datetime.utcnow()
    if period == "today":
        since = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        period_label = "Today"
    elif period == "30":
        since = (now - timedelta(days=30)).isoformat()
        period_label = "Last 30 days"
    elif period == "all":
        since = "2000-01-01T00:00:00"
        period_label = "All time"
    else:
        period = "7"
        since = (now - timedelta(days=7)).isoformat()
        period_label = "Last 7 days"

    # Stats
    cursor = await db.execute(
        "SELECT COUNT(*) as total FROM page_views WHERE timestamp >= ?", (since,)
    )
    total_views = (await cursor.fetchone())['total']

    cursor = await db.execute(
        "SELECT COUNT(DISTINCT visitor_id) as uniques FROM page_views WHERE timestamp >= ?", (since,)
    )
    unique_visitors = (await cursor.fetchone())['uniques']

    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM page_views WHERE timestamp >= ?", (today_start,)
    )
    views_today = (await cursor.fetchone())['cnt']

    # Daily views for last 14 days (bar chart)
    chart_days = 14
    daily_data = []
    for i in range(chart_days - 1, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        day_end = (day.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)).isoformat()
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM page_views WHERE timestamp >= ? AND timestamp < ?",
            (day_start, day_end)
        )
        cnt = (await cursor.fetchone())['cnt']
        daily_data.append((day.strftime("%b %d"), cnt))

    max_views = max((d[1] for d in daily_data), default=1) or 1

    chart_bars = ""
    for label, count in daily_data:
        pct = (count / max_views) * 100
        chart_bars += f"""
        <div style="display:flex;flex-direction:column;align-items:center;flex:1;min-width:0;">
            <span style="font-size:11px;color:var(--ink);font-weight:600;margin-bottom:4px;">{count}</span>
            <div style="width:100%;max-width:40px;height:120px;display:flex;align-items:flex-end;">
                <div style="width:100%;height:{max(pct, 2):.0f}%;background:var(--terracotta);border-radius:4px 4px 0 0;min-height:2px;"></div>
            </div>
            <span style="font-size:10px;color:var(--ink-muted);margin-top:4px;white-space:nowrap;">{label}</span>
        </div>
        """

    # Top pages
    cursor = await db.execute(
        """SELECT page, COUNT(*) as views FROM page_views
           WHERE timestamp >= ? GROUP BY page ORDER BY views DESC LIMIT 10""",
        (since,)
    )
    top_pages = await cursor.fetchall()
    max_page_views = top_pages[0]['views'] if top_pages else 1

    top_pages_rows = ""
    for p in top_pages:
        pg = escape(str(p['page']))
        v = p['views']
        bar_pct = (v / max_page_views) * 100
        top_pages_rows += f"""
        <tr style="border-bottom:1px solid var(--border);">
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                <a href="{pg}" style="color:var(--ink);text-decoration:none;">{pg}</a>
            </td>
            <td style="padding:10px 12px;width:50%;min-width:120px;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <div style="flex:1;height:18px;background:var(--cream-dark);border-radius:4px;overflow:hidden;">
                        <div style="height:100%;width:{bar_pct:.0f}%;background:var(--terracotta);border-radius:4px;"></div>
                    </div>
                    <span style="font-size:13px;font-weight:600;color:var(--ink);min-width:40px;text-align:right;">{v}</span>
                </div>
            </td>
        </tr>
        """

    # Top referrers
    cursor = await db.execute(
        """SELECT referrer, COUNT(*) as views FROM page_views
           WHERE timestamp >= ? AND referrer != '' AND referrer NOT LIKE '%indiestack%'
           GROUP BY referrer ORDER BY views DESC LIMIT 10""",
        (since,)
    )
    top_referrers = await cursor.fetchall()

    referrer_rows = ""
    if top_referrers:
        max_ref_views = top_referrers[0]['views']
        for r in top_referrers:
            ref = escape(str(r['referrer']))
            # Truncate long referrers for display
            ref_display = ref if len(ref) <= 60 else ref[:57] + "..."
            rv = r['views']
            bar_pct = (rv / max_ref_views) * 100
            referrer_rows += f"""
            <tr style="border-bottom:1px solid var(--border);">
                <td style="padding:10px 12px;font-size:14px;color:var(--ink);max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
                    title="{ref}">
                    <a href="{ref}" target="_blank" rel="noopener" style="color:var(--ink);text-decoration:none;">{ref_display}</a>
                </td>
                <td style="padding:10px 12px;width:40%;min-width:100px;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <div style="flex:1;height:18px;background:var(--cream-dark);border-radius:4px;overflow:hidden;">
                            <div style="height:100%;width:{bar_pct:.0f}%;background:var(--terracotta);border-radius:4px;"></div>
                        </div>
                        <span style="font-size:13px;font-weight:600;color:var(--ink);min-width:40px;text-align:right;">{rv}</span>
                    </div>
                </td>
            </tr>
            """
    else:
        referrer_rows = '<tr><td colspan="2" style="padding:12px;color:var(--ink-muted);font-size:14px;">No external referrers yet.</td></tr>'

    # Recent visitors (last 20)
    cursor = await db.execute(
        "SELECT timestamp, page, referrer FROM page_views ORDER BY timestamp DESC LIMIT 20"
    )
    recent = await cursor.fetchall()

    recent_rows = ""
    for rv in recent:
        ts_raw = str(rv['timestamp'])
        # Format time nicely
        try:
            ts_dt = datetime.fromisoformat(ts_raw)
            ts_display = ts_dt.strftime("%b %d, %H:%M")
        except Exception:
            ts_display = ts_raw[:16]
        pg = escape(str(rv['page']))
        ref = escape(str(rv.get('referrer', '') or ''))
        ref_short = ref if len(ref) <= 40 else ref[:37] + "..."
        source = f'<a href="{ref}" target="_blank" rel="noopener" style="color:var(--ink-muted);text-decoration:none;" title="{ref}">{ref_short}</a>' if ref else '<span style="color:var(--ink-muted);">direct</span>'
        recent_rows += f"""
        <tr style="border-bottom:1px solid var(--border);">
            <td style="padding:8px 12px;font-size:13px;color:var(--ink-muted);white-space:nowrap;">{ts_display}</td>
            <td style="padding:8px 12px;font-size:13px;color:var(--ink);">{pg}</td>
            <td style="padding:8px 12px;font-size:13px;">{source}</td>
        </tr>
        """

    # Period filter pills
    pills = ""
    for val, label in [("today", "Today"), ("7", "Last 7 days"), ("30", "Last 30 days"), ("all", "All time")]:
        active_style = "background:var(--terracotta);color:white;" if val == period else "background:var(--cream-dark);color:var(--ink-light);border:1px solid var(--border);"
        pills += f'<a href="/admin/analytics?period={val}" class="btn" style="{active_style}padding:6px 16px;font-size:13px;border-radius:999px;text-decoration:none;font-weight:600;">{label}</a>'

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:960px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Site Analytics</h1>
            <a href="/admin" class="btn" style="background:var(--cream-dark);color:var(--ink-light);border:1px solid var(--border);">
                &larr; Back to Admin
            </a>
        </div>

        <!-- Period filter -->
        <div style="display:flex;gap:8px;margin-bottom:24px;flex-wrap:wrap;">
            {pills}
        </div>

        <!-- Stats cards -->
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:32px;">
            <div class="card" style="text-align:center;padding:16px;">
                <div style="color:var(--ink-muted);font-size:14px;">Page Views</div>
                <div style="font-family:var(--font-display);font-size:28px;margin-top:4px;color:var(--terracotta);">{total_views:,}</div>
                <div style="color:var(--ink-muted);font-size:12px;margin-top:2px;">{period_label}</div>
            </div>
            <div class="card" style="text-align:center;padding:16px;">
                <div style="color:var(--ink-muted);font-size:14px;">Unique Visitors</div>
                <div style="font-family:var(--font-display);font-size:28px;margin-top:4px;color:var(--terracotta);">{unique_visitors:,}</div>
                <div style="color:var(--ink-muted);font-size:12px;margin-top:2px;">{period_label}</div>
            </div>
            <div class="card" style="text-align:center;padding:16px;">
                <div style="color:var(--ink-muted);font-size:14px;">Views Today</div>
                <div style="font-family:var(--font-display);font-size:28px;margin-top:4px;color:var(--terracotta);">{views_today:,}</div>
            </div>
        </div>

        <!-- Traffic chart -->
        <div class="card" style="padding:24px;margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">Daily Traffic (Last 14 Days)</h2>
            <div style="display:flex;gap:4px;align-items:flex-end;">
                {chart_bars}
            </div>
        </div>

        <!-- Top pages -->
        <div class="card" style="padding:24px;margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">Top Pages</h2>
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="border-bottom:2px solid var(--border);">
                        <th style="padding:8px 12px;text-align:left;font-size:13px;color:var(--ink-muted);font-weight:600;">Page</th>
                        <th style="padding:8px 12px;text-align:left;font-size:13px;color:var(--ink-muted);font-weight:600;">Views</th>
                    </tr>
                </thead>
                <tbody>{top_pages_rows}</tbody>
            </table>
        </div>

        <!-- Referrers -->
        <div class="card" style="padding:24px;margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">Top Referrers</h2>
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="border-bottom:2px solid var(--border);">
                        <th style="padding:8px 12px;text-align:left;font-size:13px;color:var(--ink-muted);font-weight:600;">Source</th>
                        <th style="padding:8px 12px;text-align:left;font-size:13px;color:var(--ink-muted);font-weight:600;">Views</th>
                    </tr>
                </thead>
                <tbody>{referrer_rows}</tbody>
            </table>
        </div>

        <!-- Recent visitors -->
        <div class="card" style="padding:24px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">Recent Visitors</h2>
            <div style="overflow-x:auto;">
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="border-bottom:2px solid var(--border);">
                            <th style="padding:8px 12px;text-align:left;font-size:13px;color:var(--ink-muted);font-weight:600;">Time</th>
                            <th style="padding:8px 12px;text-align:left;font-size:13px;color:var(--ink-muted);font-weight:600;">Page</th>
                            <th style="padding:8px 12px;text-align:left;font-size:13px;color:var(--ink-muted);font-weight:600;">Source</th>
                        </tr>
                    </thead>
                    <tbody>{recent_rows}</tbody>
                </table>
            </div>
        </div>
    </div>
    """
    return HTMLResponse(page_shell("Site Analytics", body, user=request.state.user))

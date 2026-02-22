"""Maker dashboard — tool management, sales, analytics, settings."""

from html import escape

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.routes.components import page_shell, star_rating_html, tool_card, indie_badge_html, pagination_html, update_card, launch_readiness_bar
from indiestack.db import (
    get_tools_by_maker, get_sales_by_maker, get_maker_revenue, get_maker_stats,
    get_tool_by_id, update_tool, get_all_categories, get_tool_rating,
    get_tool_views_by_maker, get_active_subscription, get_maker_by_id, update_maker,
    get_user_wishlist, get_updates_by_maker, create_maker_update,
    get_notifications, mark_notifications_read,
    get_tool_changelogs, update_maker_stripe_account,
    get_user_tokens_saved, get_or_create_badge_token,
    get_maker_funnel, get_wishlist_users_for_tool,
    get_launch_readiness,
    get_user_milestones, get_unshared_milestones, check_milestones,
    create_user_stack, get_user_stack, add_tool_to_user_stack, remove_tool_from_user_stack, update_user_stack,
    get_tool_by_slug, get_search_terms_for_tool,
    MILESTONE_THRESHOLDS,
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
    sub = await get_active_subscription(db, user['id'])
    is_pro = sub is not None

    # Tokens saved
    user_tokens = await get_user_tokens_saved(db, user['id'])
    tokens_k = user_tokens // 1000 if user_tokens else 0

    pro_badge = '<span style="font-size:11px;font-weight:700;color:#5C3D0E;background:linear-gradient(135deg,var(--gold-light),var(--gold));padding:2px 10px;border-radius:999px;margin-left:8px;">PRO</span>' if is_pro else ''
    upgrade_html = '' if is_pro else '<a href="/pricing" class="btn btn-secondary" style="font-size:13px;padding:6px 16px;">Upgrade to Pro</a>'

    payment_card_html = ''

    # Badge embed code for makers
    badge_section = ''
    if maker_id:
        # Get first tool slug for the embed example
        maker_tools_list = await get_tools_by_maker(db, maker_id)
        if maker_tools_list:
            first_slug = maker_tools_list[0]['slug']
            badge_url = f"https://indiestack.fly.dev/api/badge/{first_slug}.svg"
            tool_url = f"https://indiestack.fly.dev/tool/{first_slug}"
            badge_section = f'''
            <div class="card" style="margin-top:24px;">
                <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:12px;">
                    &#127991; Embed Your IndieStack Badge
                </h3>
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                    Add this badge to your website to show you&rsquo;re listed on IndieStack. It auto-updates with your token savings estimate.
                </p>
                <div style="margin-bottom:16px;text-align:center;padding:16px;background:var(--cream-dark);border-radius:var(--radius);">
                    <img src="{badge_url}" alt="IndieStack Badge" style="height:20px;">
                </div>
                <div style="margin-bottom:8px;">
                    <label style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">HTML</label>
                    <div style="position:relative;">
                        <pre style="background:var(--ink);color:#00D4F5;padding:12px 16px;border-radius:8px;font-size:13px;
                                    font-family:var(--font-mono);overflow-x:auto;margin-top:4px;"><code>&lt;a href="{tool_url}"&gt;&lt;img src="{badge_url}" alt="Listed on IndieStack"&gt;&lt;/a&gt;</code></pre>
                        <button onclick="navigator.clipboard.writeText(this.dataset.code);this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',1500)"
                                data-code='&lt;a href=&quot;{tool_url}&quot;&gt;&lt;img src=&quot;{badge_url}&quot; alt=&quot;Listed on IndieStack&quot;&gt;&lt;/a&gt;'
                                style="position:absolute;top:8px;right:8px;background:#00D4F5;color:#1A2D4A;border:none;
                                       padding:4px 12px;border-radius:4px;font-size:11px;font-weight:600;cursor:pointer;">Copy</button>
                    </div>
                </div>
                <div>
                    <label style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Markdown</label>
                    <div style="position:relative;">
                        <pre style="background:var(--ink);color:#00D4F5;padding:12px 16px;border-radius:8px;font-size:13px;
                                    font-family:var(--font-mono);overflow-x:auto;margin-top:4px;"><code>[![Listed on IndieStack]({badge_url})]({tool_url})</code></pre>
                        <button onclick="navigator.clipboard.writeText(this.dataset.code);this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',1500)"
                                data-code="[![Listed on IndieStack]({badge_url})]({tool_url})"
                                style="position:absolute;top:8px;right:8px;background:#00D4F5;color:#1A2D4A;border:none;
                                       padding:4px 12px;border-radius:4px;font-size:11px;font-weight:600;cursor:pointer;">Copy</button>
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
                    <td style="padding:10px 12px;text-align:center;">{f['wishlist_saves']}</td>
                    <td style="padding:10px 12px;text-align:center;">{f['upvotes']}</td>
                </tr>
                '''
            funnel_html = f'''
            <div style="margin-top:32px;">
                <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                    &#128200; Funnel Analytics <span style="font-size:13px;color:var(--ink-muted);font-weight:400;">(last 7 days)</span>
                </h2>
                <div class="card" style="overflow-x:auto;">
                    <table style="width:100%;border-collapse:collapse;font-size:14px;">
                        <thead>
                            <tr style="border-bottom:2px solid var(--border);">
                                <th style="padding:10px 12px;text-align:left;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Tool</th>
                                <th style="padding:10px 12px;text-align:center;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Views</th>
                                <th style="padding:10px 12px;text-align:center;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Wishlist Saves</th>
                                <th style="padding:10px 12px;text-align:center;color:var(--ink-muted);font-size:12px;text-transform:uppercase;">Upvotes</th>
                            </tr>
                        </thead>
                        <tbody>{funnel_rows}</tbody>
                    </table>
                </div>
                <p style="font-size:12px;color:var(--ink-muted);margin-top:8px;">Tip: Active tools with changelogs rank higher in search and get a &#128293; streak badge.</p>
            </div>
            '''

    # Buyer badge embed section
    buyer_badge_html = ''
    if user_tokens and user_tokens > 0:
        badge_token = await get_or_create_badge_token(db, user['id'])
        badge_url = f"https://indiestack.fly.dev/api/badge/buyer/{badge_token}.svg"
        buyer_badge_html = f'''
        <div class="card" style="padding:24px;margin-top:24px;">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                &#127991; Your Tokens Saved Badge
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
                    <pre style="background:var(--ink);color:#00D4F5;padding:12px 16px;border-radius:8px;font-size:13px;
                        font-family:var(--font-mono);overflow-x:auto;white-space:pre-wrap;word-break:break-all;"><code>[![Built with IndieStack]({badge_url})](https://indiestack.fly.dev)</code></pre>
                    <button onclick="navigator.clipboard.writeText(this.dataset.code);this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',1500)"
                        data-code="[![Built with IndieStack]({badge_url})](https://indiestack.fly.dev)"
                        style="position:absolute;top:8px;right:8px;background:#00D4F5;color:#1A2D4A;border:none;
                            padding:4px 12px;border-radius:4px;font-size:11px;font-weight:600;cursor:pointer;">Copy</button>
                </div>
            </div>
            <div>
                <label style="font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">HTML</label>
                <div style="position:relative;margin-top:4px;">
                    <pre style="background:var(--ink);color:#00D4F5;padding:12px 16px;border-radius:8px;font-size:13px;
                        font-family:var(--font-mono);overflow-x:auto;white-space:pre-wrap;word-break:break-all;"><code>&lt;a href="https://indiestack.fly.dev"&gt;&lt;img src="{badge_url}" alt="Built with IndieStack"&gt;&lt;/a&gt;</code></pre>
                    <button onclick="navigator.clipboard.writeText(this.dataset.code);this.textContent='Copied!';setTimeout(()=>this.textContent='Copy',1500)"
                        data-code='<a href="https://indiestack.fly.dev"><img src="{badge_url}" alt="Built with IndieStack"></a>'
                        style="position:absolute;top:8px;right:8px;background:#00D4F5;color:#1A2D4A;border:none;
                            padding:4px 12px;border-radius:4px;font-size:11px;font-weight:600;cursor:pointer;">Copy</button>
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
                share_url = f"https://indiestack.fly.dev/api/milestone/{tool_slug}.svg?type={ms_type}" if tool_slug else ""
                tweet_url = f"https://twitter.com/intent/tweet?text={share_text}&url=https://indiestack.fly.dev/tool/{tool_slug}" if tool_slug else ""

                cards += f"""
                <div style="background:linear-gradient(135deg,#1A2D4A,#0D3B66);border-radius:16px;padding:20px 24px;
                            display:flex;align-items:center;gap:16px;margin-bottom:8px;">
                    <span style="font-size:36px;">{emoji}</span>
                    <div style="flex:1;">
                        <div style="color:#fff;font-weight:600;font-size:16px;">{desc}</div>
                        <div style="color:rgba(255,255,255,0.6);font-size:13px;">{tool_name}</div>
                    </div>
                    <a href="{tweet_url}" target="_blank" rel="noopener"
                       style="background:#00D4F5;color:#1A2D4A;padding:8px 16px;border-radius:999px;
                              text-decoration:none;font-size:13px;font-weight:700;white-space:nowrap;">
                        Share on &#120143; &rarr;
                    </a>
                </div>"""

            milestone_html = f"""
            <div style="margin-bottom:24px;">
                <h3 style="font-family:'DM Serif Display',serif;font-size:18px;color:#1A2D4A;margin-bottom:12px;">
                    &#127942; New Achievements
                </h3>
                {cards}
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
                    <td style="padding:8px 12px;border-bottom:1px solid #F3F4F6;font-weight:500;">"{escape(str(term['query']))}"</td>
                    <td style="padding:8px 12px;border-bottom:1px solid #F3F4F6;color:#6B7280;">{escape(str(term['tool_name']))}</td>
                    <td style="padding:8px 12px;border-bottom:1px solid #F3F4F6;text-align:center;">{term['count']}</td>
                </tr>"""
            search_intent_html = f"""
            <div style="background:#fff;border-radius:16px;padding:24px;border:1px solid #E8E3DC;margin-bottom:24px;">
                <h3 style="font-family:'DM Serif Display',serif;font-size:18px;color:#1A2D4A;margin-bottom:16px;">
                    &#128269; How Developers Find Your Tools
                </h3>
                <table style="width:100%;border-collapse:collapse;">
                    <thead>
                        <tr style="border-bottom:2px solid #E8E3DC;">
                            <th style="padding:8px 12px;text-align:left;font-size:13px;color:#6B7280;">Search Query</th>
                            <th style="padding:8px 12px;text-align:left;font-size:13px;color:#6B7280;">Matched Tool</th>
                            <th style="padding:8px 12px;text-align:center;font-size:13px;color:#6B7280;">Times</th>
                        </tr>
                    </thead>
                    <tbody>{search_rows}</tbody>
                </table>
            </div>"""

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:960px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32px;">
            <div>
                <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">
                    Dashboard{pro_badge}
                </h1>
                <p style="color:var(--ink-muted);margin-top:4px;">Welcome back, {escape(str(user['name']))}</p>
            </div>
            {upgrade_html}
        </div>

        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:16px;margin-bottom:40px;">
            <div class="card" style="text-align:center;padding:20px;">
                <div style="color:var(--ink-muted);font-size:13px;">Tools</div>
                <div style="font-family:var(--font-display);font-size:28px;margin-top:4px;color:var(--ink);">{tool_count}</div>
            </div>
            <div class="card" style="text-align:center;padding:20px;">
                <div style="color:var(--ink-muted);font-size:13px;">Total Sales</div>
                <div style="font-family:var(--font-display);font-size:28px;margin-top:4px;color:var(--ink);">{total_sales}</div>
            </div>
            <div class="card" style="text-align:center;padding:20px;">
                <div style="color:var(--ink-muted);font-size:13px;">Earnings</div>
                <div style="font-family:var(--font-display);font-size:28px;margin-top:4px;color:var(--terracotta);">{format_price(total_revenue)}</div>
            </div>
            <div class="card" style="text-align:center;padding:20px;">
                <div style="color:var(--ink-muted);font-size:13px;">Upvotes</div>
                <div style="font-family:var(--font-display);font-size:28px;margin-top:4px;color:var(--slate-dark);">{total_upvotes}</div>
            </div>
            <div class="card" style="text-align:center;padding:20px;">
                <div style="color:var(--ink-muted);font-size:13px;">&#9889; Tokens Saved</div>
                <div style="font-family:var(--font-display);font-size:28px;margin-top:4px;color:var(--slate-dark);">{'~' + str(tokens_k) + 'k' if tokens_k > 0 else '0'}</div>
            </div>
        </div>

        {readiness_html}
        {milestone_html}

        <div style="display:flex;gap:12px;flex-wrap:wrap;">
            <a href="/dashboard/tools" class="btn btn-primary">My Tools</a>
            <a href="/dashboard/sales" class="btn btn-secondary">Sales History</a>
            {'<a href="/dashboard/analytics" class="btn btn-secondary">Analytics</a>' if is_pro else ''}
            <a href="/submit" class="btn btn-secondary">Submit New Tool</a>
            <a href="/dashboard/saved" class="btn btn-secondary">Saved Tools</a>
            {'<a href="/dashboard/updates" class="btn btn-secondary">Post Update</a>' if maker_id else ''}
            <a href="/dashboard/my-stack" class="btn btn-secondary">My Stack</a>
        </div>

        {funnel_html}
        {search_intent_html}
        {payment_card_html}
        {badge_section}
        {buyer_badge_html}
    </div>
    """
    return HTMLResponse(page_shell("Dashboard", body, user=user))


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
                <div style="font-size:48px;margin-bottom:16px;">&#128640;</div>
                <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:12px;">List your first tool</h2>
                <p style="color:var(--ink-muted);font-size:15px;line-height:1.6;max-width:400px;margin:0 auto 8px;">
                    Listing takes under 2 minutes. You keep 92% of every sale.
                </p>
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:24px;">
                    Your maker profile is created automatically when you submit.
                </p>
                <a href="/submit" class="btn btn-primary" style="padding:12px 32px;font-size:16px;">Submit Your First Tool &rarr;</a>
            </div>
        </div>
        """
        return HTMLResponse(page_shell("My Tools", body, user=user))

    tools = await get_tools_by_maker(db, maker_id)

    status_styles = {
        'pending': 'background:#FDF8EE;color:#92400E;',
        'approved': 'background:#DCFCE7;color:#166534;',
        'rejected': 'background:#FEE2E2;color:#991B1B;',
    }

    rows = ''
    for t in tools:
        s = str(t.get('status', 'pending'))
        style = status_styles.get(s, '')
        name = escape(str(t['name']))
        slug = escape(str(t['slug']))
        price = format_price(t.get('price_pence', 0))
        upvotes = t.get('upvote_count', 0)
        is_v = bool(t.get('is_verified', 0))
        v_badge = '<span style="display:inline-block;padding:2px 6px;border-radius:999px;font-size:10px;font-weight:600;background:linear-gradient(135deg,var(--gold-light),var(--gold));color:#92400E;margin-left:6px;">V</span>' if is_v else ''

        # Get rating
        rating = await get_tool_rating(db, t['id'])
        rating_html = star_rating_html(rating['avg_rating'], rating['review_count'], size=14) if rating['review_count'] else '<span style="color:var(--ink-muted);font-size:12px;">No reviews</span>'

        rows += f"""
        <tr style="border-bottom:1px solid var(--border);">
            <td style="padding:12px;">
                <a href="/tool/{slug}" style="font-weight:600;color:var(--ink);">{name}</a>{v_badge}
            </td>
            <td style="padding:12px;">
                <span style="display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;font-weight:600;{style}">{s}</span>
            </td>
            <td style="padding:12px;">{price}</td>
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
                        <th style="padding:12px;">Price</th>
                        <th style="padding:12px;">Upvotes</th>
                        <th style="padding:12px;">Rating</th>
                        <th style="padding:12px;"></th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        <div style="margin-top:24px;">
            <a href="/submit" class="btn btn-primary">Submit New Tool</a>
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
    body = edit_tool_form(tool, categories, changelogs=changelogs)
    return HTMLResponse(page_shell(f"Edit {tool['name']}", body, user=user))


@router.post("/dashboard/tools/{tool_id}/edit", response_class=HTMLResponse)
async def edit_tool_post(
    request: Request, tool_id: int,
    name: str = Form(""), tagline: str = Form(""), description: str = Form(""),
    url: str = Form(""), tags: str = Form(""),
    price: str = Form(""), delivery_url: str = Form(""),
):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    tool = await get_tool_by_id(db, tool_id)
    if not tool or tool.get('maker_id') != user.get('maker_id'):
        return RedirectResponse(url="/dashboard/tools", status_code=303)

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

    await update_tool(db, tool_id,
                      name=name.strip(), tagline=tagline.strip(),
                      description=description.strip(), url=url.strip(),
                      tags=tags.strip(), price_pence=price_pence,
                      delivery_url=delivery_url.strip())

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
                                    f"https://indiestack.fly.dev/tool/{tool_info['slug']}"
                                )
                            )
                        except Exception:
                            pass  # Don't break on email failure
    except Exception:
        pass

    return RedirectResponse(f"/dashboard/tools/{tool_id}/edit", status_code=303)


def edit_tool_form(tool: dict, categories: list, error: str = "", changelogs: list = None) -> str:
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
            <div class="form-group">
                <label for="price">Price (GBP, leave blank for free)</label>
                <input type="number" id="price" name="price" class="form-input" step="0.01" min="0.50"
                       value="{price_val}">
            </div>
            <div id="earnings-calc" style="background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius-sm);padding:16px;margin-bottom:20px;display:none;">
                <p style="font-size:13px;font-weight:600;color:var(--ink);margin-bottom:8px;">Earnings Breakdown</p>
                <div style="font-size:14px;color:var(--ink-light);line-height:2;">
                    <div style="display:flex;justify-content:space-between;">You set: <span id="calc-price">-</span></div>
                    <div style="display:flex;justify-content:space-between;">Stripe (~3%): <span id="calc-stripe" style="color:var(--ink-muted);">-</span></div>
                    <div style="display:flex;justify-content:space-between;">Platform (5%): <span id="calc-platform" style="color:var(--ink-muted);">-</span></div>
                    <div style="display:flex;justify-content:space-between;border-top:1px solid var(--border);padding-top:6px;margin-top:4px;">
                        <strong style="color:var(--terracotta);">You earn:</strong>
                        <strong id="calc-earn" style="color:var(--terracotta);">-</strong>
                    </div>
                </div>
            </div>
            <script>
            document.getElementById('price').addEventListener('input', function() {{
                const calc = document.getElementById('earnings-calc');
                const v = parseFloat(this.value);
                if (v > 0) {{
                    calc.style.display = 'block';
                    const stripe = v * 0.03;
                    const platform = v * 0.05;
                    const earn = v - stripe - platform;
                    document.getElementById('calc-price').textContent = '\u00a3' + v.toFixed(2);
                    document.getElementById('calc-stripe').textContent = '-\u00a3' + stripe.toFixed(2);
                    document.getElementById('calc-platform').textContent = '-\u00a3' + platform.toFixed(2);
                    document.getElementById('calc-earn').textContent = '\u00a3' + earn.toFixed(2);
                }} else {{ calc.style.display = 'none'; }}
            }});
            (function(){{ var p = document.getElementById('price'); if (p && p.value) p.dispatchEvent(new Event('input')); }})();
            </script>
            <div class="form-group">
                <label for="delivery_url">Delivery URL</label>
                <input type="url" id="delivery_url" name="delivery_url" class="form-input"
                       value="{escape(str(tool.get('delivery_url', '')))}">
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


# ── Sales History ────────────────────────────────────────────────────────

@router.get("/dashboard/sales", response_class=HTMLResponse)
async def dashboard_sales(request: Request):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    maker_id = user.get('maker_id')

    if not maker_id:
        body = """
        <div class="container" style="padding:48px 24px;max-width:960px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);margin-bottom:16px;">Sales</h1>
            <div class="card" style="text-align:center;padding:40px 32px;">
                <div style="font-size:40px;margin-bottom:12px;">&#128176;</div>
                <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:8px;">No sales yet</h2>
                <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;max-width:420px;margin:0 auto;">
                    Set a price on your tools and share your listing link to start selling.
                    You keep 92% of every sale &mdash; we handle checkout and delivery.
                </p>
            </div>
        </div>
        """
        return HTMLResponse(page_shell("Sales", body, user=user))

    sales = await get_sales_by_maker(db, maker_id)
    revenue = await get_maker_revenue(db, maker_id)

    rows = ''
    for s in sales:
        tool_name = escape(str(s.get('tool_name', '')))
        amount = format_price(s['amount_pence'])
        commission = format_price(s['commission_pence'])
        net = format_price(s['amount_pence'] - s['commission_pence'])
        email = escape(str(s.get('buyer_email', '')))
        date = str(s.get('created_at', ''))[:10]
        rows += f"""
        <tr style="border-bottom:1px solid var(--border);">
            <td style="padding:10px 12px;">{date}</td>
            <td style="padding:10px 12px;font-weight:600;">{tool_name}</td>
            <td style="padding:10px 12px;">{email}</td>
            <td style="padding:10px 12px;">{amount}</td>
            <td style="padding:10px 12px;color:var(--ink-muted);">{commission}</td>
            <td style="padding:10px 12px;color:var(--terracotta);font-weight:600;">{net}</td>
        </tr>
        """

    net_total = revenue['total_revenue'] - revenue['total_commission']

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:960px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Sales History</h1>
            <a href="/dashboard" style="color:var(--ink-muted);font-size:14px;">&larr; Dashboard</a>
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:32px;">
            <div class="card" style="text-align:center;padding:16px;">
                <div style="color:var(--ink-muted);font-size:13px;">Total Sales</div>
                <div style="font-family:var(--font-display);font-size:24px;margin-top:4px;">{revenue['sale_count']}</div>
            </div>
            <div class="card" style="text-align:center;padding:16px;">
                <div style="color:var(--ink-muted);font-size:13px;">Gross Revenue</div>
                <div style="font-family:var(--font-display);font-size:24px;margin-top:4px;">{format_price(revenue['total_revenue'])}</div>
            </div>
            <div class="card" style="text-align:center;padding:16px;">
                <div style="color:var(--ink-muted);font-size:13px;">Your Earnings</div>
                <div style="font-family:var(--font-display);font-size:24px;margin-top:4px;color:var(--terracotta);">{format_price(net_total)}</div>
            </div>
        </div>
        {'<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:14px;"><thead><tr style="border-bottom:2px solid var(--border);text-align:left;"><th style="padding:10px 12px;">Date</th><th style="padding:10px 12px;">Tool</th><th style="padding:10px 12px;">Buyer</th><th style="padding:10px 12px;">Amount</th><th style="padding:10px 12px;">Fee</th><th style="padding:10px 12px;">Net</th></tr></thead><tbody>' + rows + '</tbody></table></div>' if rows else '<p class="text-muted">No sales yet.</p>'}
    </div>
    """
    return HTMLResponse(page_shell("Sales", body, user=user))


# ── Analytics (Pro only) ─────────────────────────────────────────────────

@router.get("/dashboard/analytics", response_class=HTMLResponse)
async def dashboard_analytics(request: Request):
    user = request.state.user
    redirect = require_login(user)
    if redirect:
        return redirect

    db = request.state.db
    sub = await get_active_subscription(db, user['id'])
    if not sub:
        body = """
        <div class="container" style="text-align:center;padding:80px 24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Analytics</h1>
            <p style="color:var(--ink-muted);margin:16px 0 24px;">Tool view analytics is a Pro feature.</p>
            <a href="/pricing" class="btn btn-primary">Upgrade to Pro</a>
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


# ── Saved Tools ─────────────────────────────────────────────────────────

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
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Saved Tools</h1>
            <a href="/dashboard" style="color:var(--ink-muted);font-size:14px;">&larr; Dashboard</a>
        </div>
        <div class="card-grid">{cards}</div>
        {pagination_html(page, total_pages, '/dashboard/saved')}
    </div>
    """
    return HTMLResponse(page_shell("Saved Tools", body, user=user))


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
        icon = type_icons.get(n.get('type', ''), '&#128276;')
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
    account_id = existing.get('stripe_account_id') if existing else None

    try:
        if not account_id:
            # Create new Stripe Connect account
            account = create_connect_account()
            account_id = account.id
            await update_maker_stripe_account(db, maker_id, account_id)

        # Create onboarding link (works for new or returning onboarding)
        base_url = str(request.base_url).rstrip("/")
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
            <p style="color:#9CA3AF;font-size:13px;margin-top:16px;font-family:var(--font-mono);">{escape(error_msg)}</p>
            <a href="/dashboard" class="btn btn-primary" style="margin-top:24px;">Back to Dashboard</a>
        </div>"""
        return HTMLResponse(page_shell("Stripe Connect", body, user=user))


@router.get("/dashboard/stripe-callback")
async def stripe_callback(request: Request):
    user = request.state.user
    if not user:
        return RedirectResponse("/login", status_code=303)

    body = '''
    <div style="max-width:600px;margin:60px auto;text-align:center;padding:40px;">
        <div style="font-size:48px;margin-bottom:20px;">&#10003;</div>
        <h1 style="color:var(--terracotta);font-family:var(--font-display);">Stripe Connected!</h1>
        <p style="color:var(--ink-muted);margin:16px 0;">Your payment account is set up. You can now receive payments for your tools.</p>
        <a href="/dashboard" style="display:inline-block;margin-top:20px;padding:12px 32px;background:var(--terracotta);color:white;border-radius:8px;text-decoration:none;font-weight:600;">Back to Dashboard</a>
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
        tools_html = '<p style="color:#6B7280;text-align:center;padding:20px;">No tools in your stack yet. Add some below!</p>'
    else:
        for t in tools:
            tools_html += f"""
            <div style="display:flex;align-items:center;gap:12px;padding:12px 16px;background:#fff;
                        border-radius:12px;border:1px solid #E8E3DC;margin-bottom:8px;">
                <div style="flex:1;">
                    <a href="/tool/{escape(str(t['slug']))}" style="font-weight:600;color:#1A2D4A;text-decoration:none;">{escape(str(t['name']))}</a>
                    <span style="color:#6B7280;font-size:13px;margin-left:8px;">{escape(str(t.get('category_name', '')))}</span>
                </div>
                <form method="post" action="/dashboard/my-stack/remove" style="margin:0;">
                    <input type="hidden" name="tool_slug" value="{escape(str(t['slug']))}">
                    <button type="submit" style="background:none;border:none;color:#EF4444;cursor:pointer;font-size:18px;padding:4px 8px;" title="Remove">&times;</button>
                </form>
            </div>"""

    # Tool dropdown options
    existing_slugs = {t['slug'] for t in tools} if tools else set()
    options = ''.join(f'<option value="{escape(str(t["slug"]))}">{escape(str(t["name"]))}</option>' for t in all_tools if t['slug'] not in existing_slugs)

    title = escape(str(stack['title'])) if stack else 'My Stack'
    description = escape(str(stack['description'])) if stack and stack.get('description') else ''
    is_public = stack.get('is_public', 1) if stack else 1
    username_slug = (user.get('name', '') or '').lower().replace(' ', '-')
    share_url = f"https://indiestack.fly.dev/stack/{username_slug}" if username_slug else ''

    share_banner = ''
    if share_url and is_public:
        share_banner = f"""
        <div style="background:#E8F9FA;border-radius:12px;padding:16px 20px;margin-bottom:24px;display:flex;align-items:center;justify-content:space-between;">
            <div><span style="font-weight:600;color:#0D7377;">Your public stack:</span> <a href="/stack/{username_slug}" style="color:#00D4F5;">{share_url}</a></div>
            <a href="https://twitter.com/intent/tweet?text=Check out my indie tool stack!&url={share_url}" target="_blank" rel="noopener"
               style="background:#1A2D4A;color:#fff;padding:6px 14px;border-radius:999px;text-decoration:none;font-size:13px;font-weight:600;">Share on &#120143;</a>
        </div>"""

    body = f"""
    <div style="max-width:700px;margin:0 auto;padding:40px 20px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;">
            <h1 style="font-family:'DM Serif Display',serif;color:#1A2D4A;font-size:28px;margin:0;">My Stack</h1>
            <a href="/dashboard" style="color:#6B7280;text-decoration:none;font-size:14px;">&larr; Back to Dashboard</a>
        </div>

        <form method="post" action="/dashboard/my-stack" style="margin-bottom:24px;">
            <div style="background:#fff;border-radius:16px;padding:24px;border:1px solid #E8E3DC;">
                <label style="font-weight:600;color:#1A2D4A;display:block;margin-bottom:6px;">Stack Title</label>
                <input type="text" name="title" value="{title}"
                       style="width:100%;padding:10px 14px;border:1px solid #D1D5DB;border-radius:8px;font-size:15px;margin-bottom:16px;box-sizing:border-box;">
                <label style="font-weight:600;color:#1A2D4A;display:block;margin-bottom:6px;">Description</label>
                <textarea name="description" rows="3"
                          style="width:100%;padding:10px 14px;border:1px solid #D1D5DB;border-radius:8px;font-size:15px;margin-bottom:16px;box-sizing:border-box;resize:vertical;">{description}</textarea>
                <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">
                    <input type="checkbox" name="is_public" id="is_public" value="1" {'checked' if is_public else ''}>
                    <label for="is_public" style="font-size:14px;color:#4B5563;">Make my stack public</label>
                </div>
                <button type="submit" style="background:#1A2D4A;color:#fff;padding:10px 24px;border:none;border-radius:999px;cursor:pointer;font-weight:600;">
                    Save Settings
                </button>
            </div>
        </form>

        {share_banner}

        <h2 style="font-family:'DM Serif Display',serif;color:#1A2D4A;font-size:20px;margin-bottom:16px;">Tools in Your Stack</h2>
        {tools_html}

        <form method="post" action="/dashboard/my-stack/add" style="margin-top:16px;display:flex;gap:8px;">
            <select name="tool_slug" style="flex:1;padding:10px 14px;border:1px solid #D1D5DB;border-radius:8px;font-size:15px;">
                <option value="">Select a tool to add...</option>
                {options}
            </select>
            <button type="submit" style="background:#00D4F5;color:#1A2D4A;padding:10px 20px;border:none;border-radius:999px;cursor:pointer;font-weight:700;">
                + Add
            </button>
        </form>
    </div>"""

    return HTMLResponse(page_shell("My Stack &mdash; IndieStack", body, user=user))


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

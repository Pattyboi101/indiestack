"""Admin analytics helpers — traffic, funnels, search, growth rendering."""

from datetime import datetime, timedelta
from html import escape

from indiestack.routes.admin_helpers import kpi_card, bar_chart, data_table, row_bg, status_badge
from indiestack.db import (
    get_revenue_timeseries,
    get_pro_subscriber_stats,
    get_platform_funnel,
    get_top_tools_by_metric,
    get_maker_leaderboard,
    get_search_gaps,
    get_search_trends,
    get_subscriber_growth,
    get_subscriber_count,
    get_purchase_stats,
)


# ── Tab renderers ────────────────────────────────────────────────────────

async def render_charts_section(db, request) -> str:
    """Charts portion of traffic tab — KPIs, daily/hourly charts, revenue."""
    period = request.query_params.get("period", "7")
    now = datetime.utcnow()

    if period == "today":
        since = now.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
        period_label = "Today"
    elif period == "30":
        since = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        period_label = "Last 30 days"
    elif period == "all":
        since = "2000-01-01 00:00:00"
        period_label = "All time"
    else:
        period = "7"
        since = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
        period_label = "Last 7 days"

    # ── KPI queries ──
    cursor = await db.execute(
        "SELECT COUNT(*) as total FROM page_views WHERE timestamp >= ?", (since,)
    )
    total_views = (await cursor.fetchone())['total']

    cursor = await db.execute(
        "SELECT COUNT(DISTINCT visitor_id) as uniques FROM page_views WHERE timestamp >= ?", (since,)
    )
    unique_visitors = (await cursor.fetchone())['uniques']

    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM outbound_clicks WHERE created_at >= ?", (since,)
    )
    outbound_clicks = (await cursor.fetchone())['cnt']

    if period == "today":
        # Returning visitor = visited today AND has visited on any prior day
        # Use two lightweight queries instead of a correlated subquery
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
        cursor = await db.execute(
            """SELECT COUNT(*) as cnt FROM (
                SELECT visitor_id FROM page_views
                WHERE visitor_id IS NOT NULL
                GROUP BY visitor_id
                HAVING MIN(DATE(timestamp)) < DATE(?)
                AND MAX(DATE(timestamp)) >= DATE(?)
            )""", (today_start, today_start)
        )
    else:
        cursor = await db.execute(
            """SELECT COUNT(*) as cnt FROM (
                SELECT visitor_id FROM page_views
                WHERE timestamp >= ? AND visitor_id IS NOT NULL
                GROUP BY visitor_id HAVING COUNT(DISTINCT DATE(timestamp)) > 1
            )""", (since,)
        )
    returning_visitors = (await cursor.fetchone())['cnt']

    purchase_stats = await get_purchase_stats(db)
    total_revenue_pence = purchase_stats.get('total_revenue', 0) or 0

    pro_stats = await get_pro_subscriber_stats(db)
    pro_count = pro_stats.get('active_count', 0) or 0
    mrr_pence = pro_stats.get('mrr_pence', 0) or 0

    # Period filter pills
    pills = ""
    for val, label in [("today", "Today"), ("7", "Last 7 days"), ("30", "Last 30 days"), ("all", "All time")]:
        active_style = "background:var(--slate);color:white;" if val == period else "background:var(--cream-dark);color:var(--ink-light);border:1px solid var(--border);"
        pills += f'<a href="/admin?tab=growth&section=traffic&period={val}" class="btn" style="{active_style}padding:6px 16px;font-size:13px;border-radius:999px;text-decoration:none;font-weight:600;">{label}</a>'

    # Daily traffic — single GROUP BY query
    chart_since = (now - timedelta(days=13)).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    cursor = await db.execute(
        """SELECT DATE(timestamp) as day, COUNT(*) as cnt
           FROM page_views WHERE timestamp >= ?
           GROUP BY DATE(timestamp) ORDER BY day""",
        (chart_since,)
    )
    daily_rows = {r['day']: r['cnt'] for r in await cursor.fetchall()}
    daily_data = []
    for i in range(13, -1, -1):
        day = now - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        label = day.strftime("%b %d")
        daily_data.append((label, daily_rows.get(day_str, 0)))

    traffic_chart = bar_chart(daily_data, "Daily Traffic (Last 14 Days)")

    # Hourly traffic — single GROUP BY query
    cursor = await db.execute(
        """SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour, COUNT(*) as cnt
           FROM page_views WHERE timestamp >= datetime('now', '-7 days')
           GROUP BY hour ORDER BY hour"""
    )
    hourly_rows = {r['hour']: r['cnt'] for r in await cursor.fetchall()}
    hourly_data = [(f"{h:02d}:00", hourly_rows.get(h, 0)) for h in range(24)]

    hourly_chart = bar_chart(hourly_data, "Traffic by Hour of Day (Last 7 Days)")

    # ── Revenue time series ──
    rev_data = await get_revenue_timeseries(db, days=30)
    rev_chart = ""
    if rev_data:
        rev_points = [(r['date'], r['revenue_pence'] / 100) for r in rev_data]
        rev_chart = bar_chart(rev_points, "Daily Revenue (Last 30 Days)", value_prefix="\u00a3")

    return f"""
        <!-- Period filter -->
        <div style="display:flex;gap:8px;margin-bottom:24px;flex-wrap:wrap;">
            {pills}
        </div>

        <!-- KPI cards -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:32px;">
            {kpi_card("Page Views", f"{total_views:,}", sublabel=period_label)}
            {kpi_card("Unique Visitors", f"{unique_visitors:,}", sublabel=period_label)}
            {kpi_card("Returning Visitors", f"{returning_visitors:,}", sublabel=period_label)}
            {kpi_card("Outbound Clicks", f"{outbound_clicks:,}", sublabel=period_label)}
        </div>
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:32px;">
            {kpi_card("Total Revenue", f"£{total_revenue_pence / 100:.2f}")}
            {kpi_card("Pro Subscribers", f"{pro_count:,}")}
            {kpi_card("MRR", f"£{mrr_pence / 100:.2f}")}
        </div>

        {traffic_chart}
        {hourly_chart}
        {rev_chart}
    """


async def render_tables_section(db, request) -> str:
    """Tables portion of traffic tab — top pages, referrers, recent visitors."""
    period = request.query_params.get("period", "7")
    now = datetime.utcnow()

    if period == "today":
        since = now.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%d %H:%M:%S")
    elif period == "30":
        since = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
    elif period == "all":
        since = "2000-01-01 00:00:00"
    else:
        period = "7"
        since = (now - timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")

    # Period filter pills
    pills = ""
    for val, label in [("today", "Today"), ("7", "Last 7 days"), ("30", "Last 30 days"), ("all", "All time")]:
        active_style = "background:var(--slate);color:white;" if val == period else "background:var(--cream-dark);color:var(--ink-light);border:1px solid var(--border);"
        pills += f'<a href="/admin?tab=growth&section=traffic&period={val}" class="btn" style="{active_style}padding:6px 16px;font-size:13px;border-radius:999px;text-decoration:none;font-weight:600;">{label}</a>'

    # ── Top pages ──
    cursor = await db.execute(
        """SELECT page, COUNT(*) as views FROM page_views
           WHERE timestamp >= ? GROUP BY page ORDER BY views DESC LIMIT 10""",
        (since,)
    )
    top_pages = await cursor.fetchall()
    max_page_views = top_pages[0]['views'] if top_pages else 1

    top_pages_rows = ""
    for idx, p in enumerate(top_pages):
        pg = escape(str(p['page']))
        v = p['views']
        bar_pct = (v / max_page_views) * 100
        top_pages_rows += f"""
        <tr style="border-bottom:1px solid var(--border);{row_bg(idx)}">
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                <a href="{pg}" style="color:var(--ink);text-decoration:none;">{pg}</a>
            </td>
            <td style="padding:10px 12px;width:50%;min-width:120px;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <div style="flex:1;height:18px;background:var(--cream-dark);border-radius:4px;overflow:hidden;">
                        <div style="height:100%;width:{bar_pct:.0f}%;background:var(--slate);border-radius:4px;"></div>
                    </div>
                    <span style="font-size:13px;font-weight:600;color:var(--ink);min-width:40px;text-align:right;">{v}</span>
                </div>
            </td>
        </tr>
        """

    top_pages_table = data_table("Top Pages", ["Page", "Views"], top_pages_rows)

    # ── Top referrers ──
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
        for idx, r in enumerate(top_referrers):
            ref = escape(str(r['referrer']))
            ref_display = ref if len(ref) <= 60 else ref[:57] + "..."
            rv = r['views']
            bar_pct = (rv / max_ref_views) * 100
            referrer_rows += f"""
            <tr style="border-bottom:1px solid var(--border);{row_bg(idx)}">
                <td style="padding:10px 12px;font-size:14px;color:var(--ink);max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"
                    title="{ref}">
                    <a href="{ref}" target="_blank" rel="noopener" style="color:var(--ink);text-decoration:none;">{ref_display}</a>
                </td>
                <td style="padding:10px 12px;width:40%;min-width:100px;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <div style="flex:1;height:18px;background:var(--cream-dark);border-radius:4px;overflow:hidden;">
                            <div style="height:100%;width:{bar_pct:.0f}%;background:var(--slate);border-radius:4px;"></div>
                        </div>
                        <span style="font-size:13px;font-weight:600;color:var(--ink);min-width:40px;text-align:right;">{rv}</span>
                    </div>
                </td>
            </tr>
            """

    referrers_table = data_table("Top Referrers", ["Source", "Views"], referrer_rows, empty_msg="No external referrers yet.")

    # ── Recent visitors ──
    cursor = await db.execute(
        "SELECT timestamp, page, referrer FROM page_views ORDER BY timestamp DESC LIMIT 20"
    )
    recent = await cursor.fetchall()

    recent_rows = ""
    for idx, rv in enumerate(recent):
        ts_raw = str(rv['timestamp'])
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
        <tr style="border-bottom:1px solid var(--border);{row_bg(idx)}">
            <td style="padding:8px 12px;font-size:13px;color:var(--ink-muted);white-space:nowrap;">{ts_display}</td>
            <td style="padding:8px 12px;font-size:13px;color:var(--ink);">{pg}</td>
            <td style="padding:8px 12px;font-size:13px;">{source}</td>
        </tr>
        """

    recent_table = data_table("Recent Visitors", ["Time", "Page", "Source"], recent_rows)

    return f"""
        {top_pages_table}
        {referrers_table}
        {recent_table}
    """


async def render_traffic_section(db, request) -> str:
    """Legacy wrapper — renders charts + tables together."""
    return await render_charts_section(db, request) + await render_tables_section(db, request)


async def render_funnels_section(db) -> str:
    """Funnels — platform funnel bar, per-tool funnel, maker leaderboard."""
    funnel_data = await get_platform_funnel(db, days=30)

    # Aggregate totals
    total_views = sum(t.get('views', 0) or 0 for t in funnel_data)
    total_clicks = sum(t.get('clicks', 0) or 0 for t in funnel_data)
    total_wishlists = sum(t.get('wishlists', 0) or 0 for t in funnel_data)
    total_purchases = sum(t.get('purchases', 0) or 0 for t in funnel_data)

    # Funnel summary bar
    stages = [
        ("Views", total_views, "#1A2D4A"),
        ("Clicks", total_clicks, "#00D4F5"),
        ("Bookmarks", total_wishlists, "#16a34a"),
        ("Purchases", total_purchases, "#EA580C"),
    ]
    funnel_bar = ""
    if total_views > 0:
        segments = ""
        for label, count, color in stages:
            pct = (count / total_views) * 100 if total_views else 0
            segments += f'<div style="flex:{max(pct, 2)};background:{color};height:36px;display:flex;align-items:center;justify-content:center;color:white;font-size:12px;font-weight:600;min-width:60px;" title="{label}: {count:,}">{label} {count:,}</div>'

        drop_labels = ""
        if total_views > 0 and total_clicks > 0:
            drop_labels += f'<span style="font-size:12px;color:var(--ink-muted);">Views&rarr;Clicks: {total_clicks/total_views*100:.1f}%</span>'
        if total_clicks > 0 and total_wishlists > 0:
            drop_labels += f'<span style="font-size:12px;color:var(--ink-muted);">Clicks&rarr;Bookmarks: {total_wishlists/total_clicks*100:.1f}%</span>'
        if total_wishlists > 0 and total_purchases > 0:
            drop_labels += f'<span style="font-size:12px;color:var(--ink-muted);">Bookmarks&rarr;Purchases: {total_purchases/total_wishlists*100:.1f}%</span>'

        funnel_bar = f"""
        <div class="card" style="padding:24px;margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">Platform Funnel (30 Days)</h2>
            <div style="display:flex;border-radius:var(--radius-sm);overflow:hidden;margin-bottom:12px;">
                {segments}
            </div>
            <div style="display:flex;gap:16px;flex-wrap:wrap;">
                {drop_labels}
            </div>
        </div>
        """
    else:
        funnel_bar = """
        <div class="card" style="padding:24px;margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">Platform Funnel (30 Days)</h2>
            <p style="color:var(--ink-muted);font-size:14px;">No funnel data yet</p>
        </div>
        """

    # Per-tool funnel table
    tool_rows = ""
    sorted_tools = sorted(funnel_data, key=lambda t: t.get('views', 0) or 0, reverse=True)
    for idx, t in enumerate(sorted_tools):
        name = escape(str(t.get('name', '')))
        slug = escape(str(t.get('slug', '')))
        views = t.get('views', 0) or 0
        clicks = t.get('clicks', 0) or 0
        wishlists = t.get('wishlists', 0) or 0
        purchases = t.get('purchases', 0) or 0
        ctr = f"{clicks / views * 100:.1f}%" if views > 0 else "0%"
        tool_rows += f"""
        <tr style="border-bottom:1px solid var(--border);{row_bg(idx)}">
            <td style="padding:10px 12px;font-size:14px;"><a href="/tool/{slug}" style="color:var(--slate);text-decoration:none;font-weight:600;">{name}</a></td>
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);text-align:right;">{views:,}</td>
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);text-align:right;">{clicks:,}</td>
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);text-align:right;">{ctr}</td>
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);text-align:right;">{wishlists:,}</td>
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);text-align:right;">{purchases:,}</td>
        </tr>
        """

    tool_funnel_table = data_table("Per-Tool Funnel (30 Days)", ["Tool", "Views", "Clicks", "CTR%", "Bookmarks", "Purchases"], tool_rows)

    # Maker leaderboard
    makers = await get_maker_leaderboard(db, days=30)
    maker_rows = ""
    for idx, m in enumerate(makers):
        name = escape(str(m.get('name', '')))
        slug = escape(str(m.get('slug', '')))
        tool_count = m.get('tool_count', 0) or 0
        views = m.get('total_views', 0) or 0
        clicks = m.get('total_clicks', 0) or 0
        last_update = m.get('last_update', '')

        # Status badge based on last update
        if last_update:
            try:
                lu_dt = datetime.fromisoformat(str(last_update))
                days_ago_val = (datetime.utcnow() - lu_dt).days
                if days_ago_val > 60:
                    badge = status_badge("dormant")
                elif days_ago_val > 14:
                    badge = status_badge("idle")
                else:
                    badge = status_badge("active")
            except Exception:
                badge = status_badge("unknown")
        else:
            badge = status_badge("dormant")

        lu_display = ""
        if last_update:
            try:
                lu_display = datetime.fromisoformat(str(last_update)).strftime("%b %d, %Y")
            except Exception:
                lu_display = str(last_update)[:10]
        else:
            lu_display = "Never"

        maker_rows += f"""
        <tr style="border-bottom:1px solid var(--border);{row_bg(idx)}">
            <td style="padding:10px 12px;font-size:14px;"><a href="/maker/{slug}" style="color:var(--slate);text-decoration:none;font-weight:600;">{name}</a></td>
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);text-align:right;">{tool_count}</td>
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);text-align:right;">{views:,}</td>
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);text-align:right;">{clicks:,}</td>
            <td style="padding:10px 12px;font-size:14px;color:var(--ink-muted);text-align:right;">{lu_display}</td>
            <td style="padding:10px 12px;text-align:center;">{badge}</td>
        </tr>
        """

    maker_table = data_table("Maker Leaderboard (30 Days)", ["Name", "Tools", "Views", "Clicks", "Last Update", "Status"], maker_rows)

    return f"""
        {funnel_bar}
        {tool_funnel_table}
        {maker_table}
    """


async def render_search_section(db) -> str:
    """Search — volume, gap analysis, top queries."""
    now = datetime.utcnow()
    since_30 = (now - timedelta(days=30)).isoformat()

    # Search volume
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM search_logs WHERE created_at >= ?", (since_30,)
    )
    search_volume = (await cursor.fetchone())['cnt']

    # Search gaps
    gaps = await get_search_gaps(db, limit=30)
    gap_rows = ""
    for idx, g in enumerate(gaps):
        query = escape(str(g.get('query', '')))
        count = g.get('count', 0) or 0
        last_searched = g.get('last_searched', '')
        ls_display = ""
        if last_searched:
            try:
                ls_display = datetime.fromisoformat(str(last_searched)).strftime("%b %d, %Y")
            except Exception:
                ls_display = str(last_searched)[:10]
        gap_rows += f"""
        <tr style="border-bottom:1px solid var(--border);{row_bg(idx)}">
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);font-family:var(--font-mono);">{query}</td>
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);text-align:right;">{count}</td>
            <td style="padding:10px 12px;font-size:14px;color:var(--ink-muted);text-align:right;">{ls_display}</td>
        </tr>
        """

    gaps_table = data_table(
        "\u26a0\ufe0f Search Gap Analysis",
        ["Query", "Times Searched", "Last Searched"],
        gap_rows,
        empty_msg="No zero-result searches recorded yet."
    )

    # Top search queries
    trends = await get_search_trends(db, days=30, limit=20)
    trend_rows = ""
    for idx, t in enumerate(trends):
        query = escape(str(t.get('query', '')))
        count = t.get('count', 0) or 0
        avg_results = t.get('avg_results', 0) or 0
        trend_rows += f"""
        <tr style="border-bottom:1px solid var(--border);{row_bg(idx)}">
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);font-family:var(--font-mono);">{query}</td>
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);text-align:right;">{count}</td>
            <td style="padding:10px 12px;font-size:14px;color:var(--ink);text-align:right;">{avg_results:.1f}</td>
        </tr>
        """

    trends_table = data_table("Top Search Queries (30 Days)", ["Query", "Searches", "Avg Results"], trend_rows)

    volume_card = kpi_card("Search Volume (30 Days)", f"{search_volume:,}")

    # ── Search source breakdown (30 days) ──
    cursor = await db.execute(
        """SELECT source, COUNT(*) as cnt FROM search_logs
           WHERE created_at >= ? GROUP BY source ORDER BY cnt DESC""",
        (since_30,)
    )
    source_rows = await cursor.fetchall()
    source_counts = {str(r['source'] or 'web'): r['cnt'] for r in source_rows}
    source_total = sum(source_counts.values()) or 1

    mcp_30d = source_counts.get('mcp', 0)
    web_30d = source_counts.get('web', 0)
    api_30d = source_counts.get('api', 0)

    mcp_pct = mcp_30d / source_total * 100
    web_pct = web_30d / source_total * 100
    api_pct = api_30d / source_total * 100

    source_cards = f"""
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:16px;">
        <div style="background:var(--cream-dark);border-radius:var(--radius);padding:20px;">
            <div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;color:var(--success-text);margin-bottom:8px;">MCP (AI Agents)</div>
            <div style="font-size:28px;font-weight:700;color:var(--ink);font-family:var(--font-display);">{mcp_30d:,}</div>
            <div style="font-size:13px;color:var(--ink-muted);margin-top:4px;">{mcp_pct:.1f}% of searches</div>
        </div>
        <div style="background:var(--cream-dark);border-radius:var(--radius);padding:20px;">
            <div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;color:var(--ink-light);margin-bottom:8px;">Web</div>
            <div style="font-size:28px;font-weight:700;color:var(--ink);font-family:var(--font-display);">{web_30d:,}</div>
            <div style="font-size:13px;color:var(--ink-muted);margin-top:4px;">{web_pct:.1f}% of searches</div>
        </div>
        <div style="background:var(--cream-dark);border-radius:var(--radius);padding:20px;">
            <div style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;color:var(--info-text);margin-bottom:8px;">API</div>
            <div style="font-size:28px;font-weight:700;color:var(--ink);font-family:var(--font-display);">{api_30d:,}</div>
            <div style="font-size:13px;color:var(--ink-muted);margin-top:4px;">{api_pct:.1f}% of searches</div>
        </div>
    </div>
    """

    # ── All-time MCP searches ──
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM search_logs WHERE source = 'mcp'"
    )
    mcp_alltime = (await cursor.fetchone())['cnt']

    mcp_alltime_card = f"""
    <div style="background:var(--cream-dark);border-radius:var(--radius);padding:12px 20px;margin-bottom:32px;display:inline-block;">
        <span style="font-size:13px;color:var(--ink-muted);">All-time MCP searches: </span>
        <span style="font-size:15px;font-weight:700;color:var(--success-text);">{mcp_alltime:,}</span>
    </div>
    """

    return f"""
        <div style="display:grid;grid-template-columns:1fr;gap:16px;margin-bottom:32px;">
            {volume_card}
        </div>
        {source_cards}
        {mcp_alltime_card}
        {gaps_table}
        {trends_table}
    """


async def render_growth_section(db) -> str:
    """Growth — subscriber count, growth chart, user signups, claim conversion."""

    # Subscriber count
    sub_count = await get_subscriber_count(db)

    # Subscriber growth
    growth_data = await get_subscriber_growth(db)
    growth_points = [(g['date'], g.get('cumulative', 0) or 0) for g in growth_data] if growth_data else []
    growth_chart = bar_chart(growth_points, "Subscriber Growth (Cumulative)")

    # User signup stats
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
    total_users = (await cursor.fetchone())['cnt']

    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM users WHERE created_at >= datetime('now', '-30 days')"
    )
    new_users_30d = (await cursor.fetchone())['cnt']

    # Claim conversion
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM tools WHERE maker_id IS NOT NULL AND status='approved'"
    )
    claimed_tools = (await cursor.fetchone())['cnt']

    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM tools WHERE status='approved'"
    )
    total_tools = (await cursor.fetchone())['cnt']

    claim_pct = f"{claimed_tools / total_tools * 100:.1f}%" if total_tools > 0 else "0%"

    return f"""
        <!-- KPI cards -->
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:32px;">
            {kpi_card("Email Subscribers", f"{sub_count:,}")}
            {kpi_card("Total Users", f"{total_users:,}")}
            {kpi_card("New Users (30d)", f"{new_users_30d:,}")}
        </div>

        {growth_chart}

        <!-- Claim conversion -->
        <div class="card" style="padding:24px;margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">Tool Claim Conversion</h2>
            <div style="display:flex;align-items:center;gap:16px;">
                <div style="flex:1;height:24px;background:var(--cream-dark);border-radius:var(--radius-sm);overflow:hidden;">
                    <div style="height:100%;width:{claimed_tools / total_tools * 100 if total_tools else 0:.0f}%;background:#16a34a;border-radius:var(--radius-sm);"></div>
                </div>
                <span style="font-size:14px;font-weight:600;color:var(--ink);">{claim_pct}</span>
            </div>
            <div style="display:flex;gap:24px;margin-top:12px;">
                <span style="font-size:13px;color:var(--ink-muted);">Claimed: <strong style="color:var(--ink);">{claimed_tools}</strong></span>
                <span style="font-size:13px;color:var(--ink-muted);">Total approved: <strong style="color:var(--ink);">{total_tools}</strong></span>
            </div>
        </div>
    """

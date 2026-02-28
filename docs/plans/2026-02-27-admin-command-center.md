# Admin Command Center Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Consolidate the 3-page admin section (admin.py, admin_analytics.py, admin_outreach.py) into a single `/admin?tab=X` page with 5 focused tabs: Overview, Tools, People, Content, Growth.

**Architecture:** The main admin.py keeps its router and handles all routes. admin_analytics.py and admin_outreach.py lose their routers and become helper modules exporting rendering functions. A new unified People tab merges makers and users into one view. The Growth tab absorbs both analytics and outreach content via sub-navigation.

**Tech Stack:** Python/FastAPI, aiosqlite, pure Python string HTML templates, inline CSS with design tokens from components.py.

---

## Context for Implementers

### Project Structure
- **Route files:** `src/indiestack/routes/admin.py` (~1256 lines), `admin_analytics.py` (~602 lines), `admin_outreach.py` (~1143 lines)
- **Shared components:** `src/indiestack/routes/components.py` — provides `page_shell()` wrapper
- **DB module:** `src/indiestack/db.py` — all database queries
- **Email module:** `src/indiestack/email.py` — email HTML builders + send function
- **Auth module:** `src/indiestack/auth.py` — `check_admin_session()`, `ADMIN_PASSWORD`, `make_session_token()`
- **Main app:** `src/indiestack/main.py` — registers routers via `app.include_router()`

### Design Tokens (from components.py `:root`)
- Colors: `--ink` (text), `--ink-muted` (secondary), `--accent` (#00D4F5 cyan), `--border`, `--cream-dark` (bg), `--card-bg`
- Font: `--font-display` (DM Serif Display), `--font-body` (DM Sans), `--font-mono` (JetBrains Mono)
- The current admin uses `--terracotta` (#EA580C) for active states — we're switching to `--slate` (#1A2D4A navy) for tabs

### Key Database Tables
- `tools` — main tool listings (status, maker_id, is_verified, is_boosted, price_pence, etc.)
- `makers` — tool owner profiles (name, slug, stripe_account_id, indie_status)
- `users` — user accounts (email, name, maker_id FK, created_at)
- `page_views` — analytics (timestamp, page, referrer, visitor_id)
- `outbound_clicks` — click tracking
- `search_logs` — search queries and result counts
- `agent_citations` — AI agent recommendation tracking

### Current Admin Action Forms
All admin POST actions submit to `/admin` with a hidden `action` field. The outreach POST actions submit to `/admin/outreach`. These form `action` URLs must be updated to all point to `/admin` in the consolidated version.

### Testing Approach
No automated tests exist for admin routes. Verification is done via:
1. `python3 -c "import ast; ast.parse(open('path').read())"` — syntax check
2. `python3 smoke_test.py` — 37-endpoint smoke test (includes `/admin`)
3. Manual browser check after deploy

### Deploy Command
```bash
cd /home/patty/indiestack && ~/.fly/bin/flyctl deploy --remote-only --buildkit
```

---

## Task 1: Shared Admin Helpers Module

Create a shared helpers file with reusable rendering functions used across all tabs.

**Files:**
- Create: `src/indiestack/routes/admin_helpers.py`

**Step 1: Create the helpers file**

```python
"""Shared rendering helpers for the admin command center."""

from html import escape
from datetime import datetime


def time_ago(dt_str):
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


def days_ago_label(days):
    """Human-readable label for days-inactive count."""
    if days is None:
        return "Never"
    if days == 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    if days < 30:
        return f"{days}d ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


def kpi_card(label, value, color="var(--slate)", link="", sublabel=""):
    """Render a KPI stat card with optional left-border color and link."""
    sub = f'<div style="color:var(--ink-muted);font-size:11px;margin-top:2px;">{sublabel}</div>' if sublabel else ''
    tag = 'a' if link else 'div'
    href = f' href="{link}"' if link else ''
    link_style = 'text-decoration:none;' if link else ''
    return f"""
    <{tag}{href} class="card" style="{link_style}text-align:center;padding:16px;border-left:3px solid {color};">
        <div style="font-family:var(--font-display);font-size:28px;color:var(--ink);">{value}</div>
        <div style="font-size:12px;color:var(--ink-muted);font-weight:600;margin-top:2px;">{escape(label)}</div>
        {sub}
    </{tag}>
    """


def pending_alert_bar(count):
    """Orange alert bar shown on ALL tabs when pending tools exist."""
    if count <= 0:
        return ""
    return f"""
    <div style="display:flex;align-items:center;justify-content:space-between;padding:12px 20px;
                background:#FFF7ED;border:1px solid #FDBA74;border-left:4px solid #EA580C;
                border-radius:var(--radius-sm);margin-bottom:24px;">
        <span style="font-size:14px;font-weight:600;color:#9A3412;">
            \u26a0\ufe0f {count} tool{'s' if count != 1 else ''} pending review
        </span>
        <a href="/admin?tab=tools&status=pending" class="btn"
           style="background:#EA580C;color:white;padding:6px 16px;font-size:13px;font-weight:600;text-decoration:none;">
            Review Now
        </a>
    </div>
    """


def status_badge(status):
    """Activity status badge (active/idle/dormant)."""
    if status == "active":
        return '<span style="display:inline-block;padding:2px 10px;border-radius:9999px;font-size:12px;font-weight:600;background:#DCFCE7;color:#16a34a;">Active</span>'
    if status == "idle":
        return '<span style="display:inline-block;padding:2px 10px;border-radius:9999px;font-size:12px;font-weight:600;background:#FEF3C7;color:#D97706;">Idle</span>'
    return '<span style="display:inline-block;padding:2px 10px;border-radius:9999px;font-size:12px;font-weight:600;background:#FEE2E2;color:#DC2626;">Dormant</span>'


def role_badge(role):
    """Person role badge for People tab."""
    colors = {
        "maker": ("background:#DCFCE7;color:#16a34a;", "Maker"),
        "subscriber": ("background:#DBEAFE;color:#2563EB;", "Subscriber"),
        "buyer": ("background:#F3E8FF;color:#7C3AED;", "Buyer"),
        "unclaimed": ("background:#F3F4F6;color:#6B7280;", "Unclaimed"),
    }
    style, label = colors.get(role, ("background:#F3F4F6;color:#6B7280;", role.title()))
    return f'<span style="display:inline-block;padding:2px 8px;border-radius:9999px;font-size:11px;font-weight:600;{style}">{label}</span>'


def tab_nav(active_tab, pending_count=0):
    """Render the 5-tab navigation bar."""
    tabs = [
        ('overview', 'Overview'),
        ('tools', 'Tools'),
        ('people', 'People'),
        ('content', 'Content'),
        ('growth', 'Growth'),
    ]
    html = '<div style="display:flex;gap:0;border-bottom:2px solid var(--border);margin-bottom:24px;">'
    for slug, label in tabs:
        if slug == active_tab:
            style = 'color:var(--slate);border-bottom:2px solid var(--slate);font-weight:700;background:rgba(26,45,74,0.04);'
        else:
            style = 'color:var(--ink-muted);border-bottom:2px solid transparent;'
        # Show pending dot on tools tab
        dot = ''
        if slug == 'tools' and pending_count > 0:
            dot = f' <span style="display:inline-block;width:8px;height:8px;background:#EA580C;border-radius:50%;margin-left:4px;vertical-align:middle;"></span>'
        html += f'<a href="/admin?tab={slug}" style="padding:10px 20px;font-size:14px;text-decoration:none;margin-bottom:-2px;{style}">{label}{dot}</a>'
    html += '</div>'
    return html


def growth_sub_nav(active_section):
    """Lighter sub-navigation within the Growth tab."""
    sections = [
        ('traffic', 'Traffic & Funnels'),
        ('search', 'Search'),
        ('email', 'Email'),
        ('social', 'Social'),
    ]
    html = '<div style="display:flex;gap:4px;margin-bottom:24px;border-bottom:1px solid var(--border);padding-bottom:0;">'
    for slug, label in sections:
        if slug == active_section:
            style = 'color:var(--slate);border-bottom:2px solid var(--slate);font-weight:600;'
        else:
            style = 'color:var(--ink-muted);'
        html += f'<a href="/admin?tab=growth&section={slug}" style="padding:8px 16px;font-size:13px;text-decoration:none;margin-bottom:-1px;{style}">{label}</a>'
    html += '</div>'
    return html


def bar_chart(data, title, value_prefix="", value_suffix=""):
    """Reusable bar chart. data = [(label, value), ...]."""
    if not data:
        return f"""
        <div class="card" style="padding:24px;margin-bottom:24px;">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:16px;">{title}</h3>
            <p style="color:var(--ink-muted);font-size:14px;">No data yet</p>
        </div>
        """
    max_val = max((d[1] for d in data), default=1) or 1
    bars = ""
    for label, count in data:
        pct = (count / max_val) * 100
        display_val = f"{value_prefix}{count}{value_suffix}" if isinstance(count, int) else f"{value_prefix}{count:.2f}{value_suffix}"
        bars += f"""
        <div style="display:flex;flex-direction:column;align-items:center;flex:1;min-width:0;">
            <span style="font-size:11px;color:var(--ink);font-weight:600;margin-bottom:4px;">{display_val}</span>
            <div style="width:100%;max-width:40px;height:120px;display:flex;align-items:flex-end;">
                <div style="width:100%;height:{max(pct, 2):.0f}%;background:var(--slate);border-radius:4px 4px 0 0;min-height:2px;"></div>
            </div>
            <span style="font-size:10px;color:var(--ink-muted);margin-top:4px;white-space:nowrap;">{label}</span>
        </div>
        """
    return f"""
    <div class="card" style="padding:24px;margin-bottom:24px;">
        <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:16px;">{title}</h3>
        <div style="display:flex;gap:4px;align-items:flex-end;">
            {bars}
        </div>
    </div>
    """


def data_table(title, headers, rows_html, empty_msg="No data yet"):
    """Reusable table card with alternating rows."""
    head_cells = ""
    for h in headers:
        head_cells += f'<th style="padding:8px 12px;text-align:left;font-size:12px;color:var(--ink-muted);font-weight:600;text-transform:uppercase;position:sticky;top:0;background:var(--card-bg);z-index:1;">{h}</th>'
    content = rows_html if rows_html else f'<tr><td colspan="{len(headers)}" style="padding:16px;color:var(--ink-muted);font-size:14px;">{empty_msg}</td></tr>'
    return f"""
    <div class="card" style="padding:24px;margin-bottom:24px;">
        <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:16px;">{title}</h3>
        <div style="overflow-x:auto;max-height:600px;overflow-y:auto;">
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="border-bottom:2px solid var(--border);">
                        {head_cells}
                    </tr>
                </thead>
                <tbody>{content}</tbody>
            </table>
        </div>
    </div>
    """


# Row style helper for alternating backgrounds
def row_bg(index):
    """Return alternating row background style."""
    return 'background:var(--cream-dark);' if index % 2 == 0 else ''
```

**Step 2: Syntax check**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin_helpers.py').read())"`
Expected: No output (success)

---

## Task 2: Refactor admin_analytics.py Into Helper Functions

Remove the router and route handlers from admin_analytics.py. Convert tab renderers into exported async functions that accept `db` and `request` and return HTML strings. Remove `_nav_bar()` and `_sub_tabs()` (replaced by shared helpers).

**Files:**
- Modify: `src/indiestack/routes/admin_analytics.py`

**Step 1: Rewrite admin_analytics.py**

The file should:
1. Remove `router = APIRouter()` and the `@router.get("/admin/analytics")` route handler
2. Remove `_nav_bar()` and `_sub_tabs()` local helpers
3. Keep `_bar_chart`, `_table`, `_kpi_card` but rename them to avoid conflicts (or import from admin_helpers)
4. Export 4 async functions: `render_traffic_section(db, request)`, `render_funnels_section(db)`, `render_search_section(db)`, `render_growth_section(db)`
5. Each function returns the same HTML it does now, just without the page wrapper

Replace the file contents. Keep all existing query logic and rendering intact, just restructure:

```python
"""Admin analytics helpers — traffic, funnels, search, growth rendering."""

from datetime import datetime, timedelta
from html import escape

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
from indiestack.routes.admin_helpers import kpi_card, bar_chart, data_table


async def render_traffic_section(db, request) -> str:
    """Traffic overview — KPIs, charts, top pages, referrers, recent visitors."""
    period = request.query_params.get("period", "7")
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

    # KPI queries
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

    purchase_stats = await get_purchase_stats(db)
    total_revenue_pence = purchase_stats.get('total_revenue', 0) or 0

    pro_stats = await get_pro_subscriber_stats(db)
    mrr_pence = pro_stats.get('mrr_pence', 0) or 0

    # Period filter pills
    pills = '<div style="display:flex;gap:8px;margin-bottom:24px;flex-wrap:wrap;">'
    for val, label in [("today", "Today"), ("7", "Last 7 days"), ("30", "Last 30 days"), ("all", "All time")]:
        active_style = "background:var(--slate);color:white;" if val == period else "background:var(--cream-dark);color:var(--ink-muted);border:1px solid var(--border);"
        pills += f'<a href="/admin?tab=growth&section=traffic&period={val}" style="{active_style}padding:6px 16px;font-size:13px;border-radius:999px;text-decoration:none;font-weight:600;display:inline-block;">{label}</a>'
    pills += '</div>'

    # 14-day traffic chart
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

    traffic_chart = bar_chart(daily_data, "Daily Traffic (Last 14 Days)")

    # Revenue chart
    rev_data = await get_revenue_timeseries(db, days=30)
    rev_chart = ""
    if rev_data:
        rev_points = [(r['date'], r['revenue_pence'] / 100) for r in rev_data]
        rev_chart = bar_chart(rev_points, "Daily Revenue (Last 30 Days)", value_prefix="\u00a3")

    # Top pages
    cursor = await db.execute(
        "SELECT page, COUNT(*) as views FROM page_views WHERE timestamp >= ? GROUP BY page ORDER BY views DESC LIMIT 10",
        (since,)
    )
    top_pages = await cursor.fetchall()
    max_page_views = top_pages[0]['views'] if top_pages else 1

    top_pages_rows = ""
    for idx, p in enumerate(top_pages):
        pg = escape(str(p['page']))
        v = p['views']
        bar_pct = (v / max_page_views) * 100
        bg = 'background:var(--cream-dark);' if idx % 2 == 0 else ''
        top_pages_rows += f"""
        <tr style="border-bottom:1px solid var(--border);{bg}">
            <td style="padding:8px 12px;font-size:13px;color:var(--ink);max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
                <a href="{pg}" style="color:var(--ink);text-decoration:none;">{pg}</a>
            </td>
            <td style="padding:8px 12px;width:50%;min-width:120px;">
                <div style="display:flex;align-items:center;gap:8px;">
                    <div style="flex:1;height:16px;background:var(--cream-dark);border-radius:4px;overflow:hidden;">
                        <div style="height:100%;width:{bar_pct:.0f}%;background:var(--slate);border-radius:4px;"></div>
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
        for idx, r in enumerate(top_referrers):
            ref = escape(str(r['referrer']))
            ref_display = ref if len(ref) <= 60 else ref[:57] + "..."
            rv = r['views']
            bar_pct = (rv / max_ref_views) * 100
            bg = 'background:var(--cream-dark);' if idx % 2 == 0 else ''
            referrer_rows += f"""
            <tr style="border-bottom:1px solid var(--border);{bg}">
                <td style="padding:8px 12px;font-size:13px;color:var(--ink);max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="{ref}">
                    <a href="{ref}" target="_blank" rel="noopener" style="color:var(--ink);text-decoration:none;">{ref_display}</a>
                </td>
                <td style="padding:8px 12px;width:40%;min-width:100px;">
                    <div style="display:flex;align-items:center;gap:8px;">
                        <div style="flex:1;height:16px;background:var(--cream-dark);border-radius:4px;overflow:hidden;">
                            <div style="height:100%;width:{bar_pct:.0f}%;background:var(--slate);border-radius:4px;"></div>
                        </div>
                        <span style="font-size:13px;font-weight:600;color:var(--ink);min-width:40px;text-align:right;">{rv}</span>
                    </div>
                </td>
            </tr>
            """

    # Recent visitors
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
        bg = 'background:var(--cream-dark);' if idx % 2 == 0 else ''
        recent_rows += f"""
        <tr style="border-bottom:1px solid var(--border);{bg}">
            <td style="padding:6px 12px;font-size:13px;color:var(--ink-muted);white-space:nowrap;">{ts_display}</td>
            <td style="padding:6px 12px;font-size:13px;color:var(--ink);">{pg}</td>
            <td style="padding:6px 12px;font-size:13px;">{source}</td>
        </tr>
        """

    return f"""
        {pills}
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px;">
            {kpi_card("Page Views", f"{total_views:,}", link="/admin?tab=growth&section=traffic", sublabel=period_label)}
            {kpi_card("Unique Visitors", f"{unique_visitors:,}", sublabel=period_label)}
            {kpi_card("Outbound Clicks", f"{outbound_clicks:,}", sublabel=period_label)}
        </div>
        <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:24px;">
            {kpi_card("Total Revenue", f"&pound;{total_revenue_pence / 100:.2f}", color="#16a34a")}
            {kpi_card("MRR", f"&pound;{mrr_pence / 100:.2f}", color="#16a34a")}
        </div>
        {traffic_chart}
        {rev_chart}
        {data_table("Top Pages", ["Page", "Views"], top_pages_rows)}
        {data_table("Top Referrers", ["Source", "Views"], referrer_rows, empty_msg="No external referrers yet.")}
        {data_table("Recent Visitors", ["Time", "Page", "Source"], recent_rows)}
    """


async def render_funnels_section(db) -> str:
    """Funnels — platform funnel, per-tool funnel, maker leaderboard."""
    funnel_data = await get_platform_funnel(db, days=30)

    total_views = sum(t.get('views', 0) or 0 for t in funnel_data)
    total_clicks = sum(t.get('clicks', 0) or 0 for t in funnel_data)
    total_wishlists = sum(t.get('wishlists', 0) or 0 for t in funnel_data)
    total_purchases = sum(t.get('purchases', 0) or 0 for t in funnel_data)

    stages = [
        ("Views", total_views, "#1A2D4A"),
        ("Clicks", total_clicks, "#00D4F5"),
        ("Wishlists", total_wishlists, "#16a34a"),
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
            drop_labels += f'<span style="font-size:12px;color:var(--ink-muted);">Clicks&rarr;Wishlists: {total_wishlists/total_clicks*100:.1f}%</span>'
        if total_wishlists > 0 and total_purchases > 0:
            drop_labels += f'<span style="font-size:12px;color:var(--ink-muted);">Wishlists&rarr;Purchases: {total_purchases/total_wishlists*100:.1f}%</span>'

        funnel_bar = f"""
        <div class="card" style="padding:24px;margin-bottom:24px;">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:16px;">Platform Funnel (30 Days)</h3>
            <div style="display:flex;border-radius:var(--radius-sm);overflow:hidden;margin-bottom:12px;">{segments}</div>
            <div style="display:flex;gap:16px;flex-wrap:wrap;">{drop_labels}</div>
        </div>
        """
    else:
        funnel_bar = """
        <div class="card" style="padding:24px;margin-bottom:24px;">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:16px;">Platform Funnel (30 Days)</h3>
            <p style="color:var(--ink-muted);font-size:14px;">No funnel data yet</p>
        </div>
        """

    # Per-tool funnel
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
        bg = 'background:var(--cream-dark);' if idx % 2 == 0 else ''
        tool_rows += f"""
        <tr style="border-bottom:1px solid var(--border);{bg}">
            <td style="padding:8px 12px;font-size:13px;"><a href="/tool/{slug}" style="color:var(--slate);text-decoration:none;font-weight:600;">{name}</a></td>
            <td style="padding:8px 12px;font-size:13px;text-align:right;">{views:,}</td>
            <td style="padding:8px 12px;font-size:13px;text-align:right;">{clicks:,}</td>
            <td style="padding:8px 12px;font-size:13px;text-align:right;">{ctr}</td>
            <td style="padding:8px 12px;font-size:13px;text-align:right;">{wishlists:,}</td>
            <td style="padding:8px 12px;font-size:13px;text-align:right;">{purchases:,}</td>
        </tr>
        """

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

        badge = '<span style="color:#16a34a;font-weight:600;font-size:12px;">Active</span>'
        if last_update:
            try:
                lu_dt = datetime.fromisoformat(str(last_update))
                days_ago = (datetime.utcnow() - lu_dt).days
                if days_ago > 60:
                    badge = '<span style="color:#dc2626;font-weight:600;font-size:12px;">Dormant</span>'
                elif days_ago > 14:
                    badge = '<span style="color:#D97706;font-weight:600;font-size:12px;">Idle</span>'
            except Exception:
                badge = '<span style="color:var(--ink-muted);font-size:12px;">Unknown</span>'
        else:
            badge = '<span style="color:#dc2626;font-weight:600;font-size:12px;">Dormant</span>'

        lu_display = ""
        if last_update:
            try:
                lu_display = datetime.fromisoformat(str(last_update)).strftime("%b %d, %Y")
            except Exception:
                lu_display = str(last_update)[:10]
        else:
            lu_display = "Never"

        bg = 'background:var(--cream-dark);' if idx % 2 == 0 else ''
        maker_rows += f"""
        <tr style="border-bottom:1px solid var(--border);{bg}">
            <td style="padding:8px 12px;font-size:13px;"><a href="/maker/{slug}" style="color:var(--slate);text-decoration:none;font-weight:600;">{name}</a></td>
            <td style="padding:8px 12px;font-size:13px;text-align:right;">{tool_count}</td>
            <td style="padding:8px 12px;font-size:13px;text-align:right;">{views:,}</td>
            <td style="padding:8px 12px;font-size:13px;text-align:right;">{clicks:,}</td>
            <td style="padding:8px 12px;font-size:13px;color:var(--ink-muted);text-align:right;">{lu_display}</td>
            <td style="padding:8px 12px;text-align:center;">{badge}</td>
        </tr>
        """

    return f"""
        {funnel_bar}
        {data_table("Per-Tool Funnel (30 Days)", ["Tool", "Views", "Clicks", "CTR%", "Wishlists", "Purchases"], tool_rows)}
        {data_table("Maker Leaderboard (30 Days)", ["Name", "Tools", "Views", "Clicks", "Last Update", "Status"], maker_rows)}
    """


async def render_search_section(db) -> str:
    """Search gap analysis and top queries."""
    now = datetime.utcnow()
    since_30 = (now - timedelta(days=30)).isoformat()

    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM search_logs WHERE created_at >= ?", (since_30,)
    )
    search_volume = (await cursor.fetchone())['cnt']

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
        bg = 'background:var(--cream-dark);' if idx % 2 == 0 else ''
        gap_rows += f"""
        <tr style="border-bottom:1px solid var(--border);{bg}">
            <td style="padding:8px 12px;font-size:13px;color:var(--ink);font-family:var(--font-mono);">{query}</td>
            <td style="padding:8px 12px;font-size:13px;text-align:right;">{count}</td>
            <td style="padding:8px 12px;font-size:13px;color:var(--ink-muted);text-align:right;">{ls_display}</td>
        </tr>
        """

    trends = await get_search_trends(db, days=30, limit=20)
    trend_rows = ""
    for idx, t in enumerate(trends):
        query = escape(str(t.get('query', '')))
        count = t.get('count', 0) or 0
        avg_results = t.get('avg_results', 0) or 0
        bg = 'background:var(--cream-dark);' if idx % 2 == 0 else ''
        trend_rows += f"""
        <tr style="border-bottom:1px solid var(--border);{bg}">
            <td style="padding:8px 12px;font-size:13px;color:var(--ink);font-family:var(--font-mono);">{query}</td>
            <td style="padding:8px 12px;font-size:13px;text-align:right;">{count}</td>
            <td style="padding:8px 12px;font-size:13px;text-align:right;">{avg_results:.1f}</td>
        </tr>
        """

    return f"""
        <div style="margin-bottom:24px;">
            {kpi_card("Search Volume (30 Days)", f"{search_volume:,}", color="var(--accent)")}
        </div>
        {data_table("\u26a0\ufe0f Search Gap Analysis", ["Query", "Times Searched", "Last Searched"], gap_rows, empty_msg="No zero-result searches recorded yet.")}
        {data_table("Top Search Queries (30 Days)", ["Query", "Searches", "Avg Results"], trend_rows)}
    """


async def render_growth_section(db) -> str:
    """Growth metrics — subscribers, users, claim conversion."""
    sub_count = await get_subscriber_count(db)
    growth_data = await get_subscriber_growth(db)
    growth_points = [(g['date'], g.get('cumulative', 0) or 0) for g in growth_data] if growth_data else []
    growth_chart = bar_chart(growth_points, "Subscriber Growth (Cumulative)")

    cursor = await db.execute("SELECT COUNT(*) as cnt FROM users")
    total_users = (await cursor.fetchone())['cnt']

    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM users WHERE created_at >= datetime('now', '-30 days')"
    )
    new_users_30d = (await cursor.fetchone())['cnt']

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
        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px;">
            {kpi_card("Email Subscribers", f"{sub_count:,}", color="var(--accent)")}
            {kpi_card("Total Users", f"{total_users:,}")}
            {kpi_card("New Users (30d)", f"{new_users_30d:,}", color="#16a34a" if new_users_30d > 0 else "var(--slate)")}
        </div>
        {growth_chart}
        <div class="card" style="padding:24px;margin-bottom:24px;">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:16px;">Tool Claim Conversion</h3>
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
```

**Step 2: Syntax check**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin_analytics.py').read())"`
Expected: No output (success)

---

## Task 3: Refactor admin_outreach.py Into Helper Functions

Remove the router and route handlers. Convert rendering functions into exported helpers. Move POST action handlers into a single function that admin.py can call.

**Files:**
- Modify: `src/indiestack/routes/admin_outreach.py`

**Step 1: Rewrite admin_outreach.py**

The file should:
1. Remove `router = APIRouter()` and all `@router` decorators
2. Remove `_nav_bar()` and `_sub_tabs()` local helpers
3. Keep all rendering functions (`_render_totw_panel`, `_render_digest_panel`, `_render_launch_day_panel`, `_render_maker_countdown_panel`, `_render_email_tab`, `_render_magic_tab`, `_render_makers_tab`, `_render_stale_tab`, `_render_social_kit`, `_social_card`, `_freshness_badge`)
4. Export all render functions and the action handlers
5. Update all form `action` URLs from `/admin/outreach` to `/admin`
6. Export an `async def handle_outreach_post(db, form, request)` that contains all the POST action logic and returns `RedirectResponse`
7. Export an `async def render_email_section(db, request)` that returns the full email tab content
8. Export an `async def render_magic_section(db)` that returns magic links content
9. Export an `async def render_makers_section(db, request)` that returns maker tracker content
10. Export an `async def render_stale_section(db)` that returns stale tools content
11. Export an `async def render_social_section(db)` that returns social kit content

Key change: ALL form actions must POST to `/admin` instead of `/admin/outreach`. Also update the Stripe nudge form to POST to `/admin` instead of `/admin/outreach/stripe-nudge`.

This is a large file (~1143 lines). The restructure keeps all the same rendering and action logic — it just removes the router and renames the entry points.

**Step 2: Syntax check**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin_outreach.py').read())"`
Expected: No output (success)

---

## Task 4: Rewrite admin.py — The Unified Command Center

This is the main task. Rewrite admin.py to:
1. Handle all 5 tabs (Overview, Tools, People, Content, Growth)
2. Import rendering helpers from admin_analytics and admin_outreach
3. Add the People tab with unified maker+user query
4. Add the Overview tab with 8 KPI cards, pending queue, alerts, and activity
5. Consolidate Content tab (collections + stacks + reviews)
6. Wire Growth tab to analytics + outreach helpers
7. Handle ALL POST actions (from old admin.py + admin_outreach.py)
8. Add redirects for old `/admin/analytics` and `/admin/outreach` URLs

**Files:**
- Modify: `src/indiestack/routes/admin.py`

**Key structural changes:**

### GET handler structure:
```python
@router.get("/admin", response_class=HTMLResponse)
async def admin_get(request: Request):
    if not check_admin_session(request):
        return HTMLResponse(page_shell("Admin Login", login_form_html(), user=request.state.user))

    db = request.state.db
    tab = request.query_params.get('tab', 'overview')  # Default to overview now

    # Pending count (for alert bar on all tabs)
    pending = await get_pending_tools(db)
    pending_count = len(pending)

    # Tab content
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
        {tab_nav(tab, pending_count)}
        {pending_alert_bar(pending_count) if tab != 'tools' else ''}
        {section_html}
    </div>
    """
    return HTMLResponse(page_shell("Admin", body, user=request.state.user))
```

### Overview tab:
- 8 KPI cards in 2x4 grid (Tools, Makers, Users, Revenue, Pending, Unclaimed, Agent Recs 7d, Pro Subs)
- Pending queue (if any) — reuse existing pending cards
- Alerts strip (stale tools, search gaps, makers needing Stripe)
- Recent activity (last 10 tool submissions, purchases, reviews)

### People tab query:
```sql
-- Claimed makers (with user account)
SELECT COALESCE(u.name, m.name) as name, u.email, m.id as maker_id, m.slug as maker_slug,
       m.indie_status, u.id as user_id, COUNT(t.id) as tool_count,
       m.stripe_account_id, MAX(t.updated_at) as last_active
FROM makers m
LEFT JOIN users u ON u.maker_id = m.id
LEFT JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
GROUP BY m.id

UNION ALL

-- Users without maker profiles
SELECT u.name, u.email, NULL, NULL, NULL, u.id, 0, NULL, u.created_at
FROM users u WHERE u.maker_id IS NULL

ORDER BY last_active DESC
```

### POST handler:
Must handle ALL actions from both old admin.py and admin_outreach.py:
- Tool actions: approve, reject, approve_all, reject_all, toggle_verified, toggle_ejectable, toggle_boost, feature, clear_featured, delete_tool
- Content actions: create_collection, add_to_collection, remove_from_collection, delete_collection, create_stack, add_to_stack, remove_from_stack, delete_stack, delete_review
- People actions: update_indie_status, generate_magic, generate_all_csv, send_nudge, send_stripe_nudge
- Email actions: test_email, blast_email, send_preview, send_totw, send_digest_test, send_digest_all, send_launch_test, send_launch_all, send_maker_countdown_test, send_maker_countdown_all
- Import action: import_tools (from old import tab)
- Login action: password check

All POST redirects should go to `/admin?tab=X` instead of `/admin/outreach?tab=X`.

### Redirect routes:
```python
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
```

**Step 2: Syntax check**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin.py').read())"`
Expected: No output (success)

---

## Task 5: Update main.py Router Registration

Remove the separate router registrations for admin_analytics and admin_outreach (they no longer have routers). Keep admin.py router only.

**Files:**
- Modify: `src/indiestack/main.py` (lines ~2530-2531)

**Step 1: Update router imports and registration**

Remove or comment out:
```python
app.include_router(admin_analytics.router)
app.include_router(admin_outreach.router)
```

Also update the imports at the top of main.py — the `from indiestack.routes import admin_analytics, admin_outreach` lines should be removed or the imports adjusted since these modules no longer have `router` attributes.

**Step 2: Syntax check**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read())"`
Expected: No output (success)

---

## Task 6: Smoke Test & Deploy

**Step 1: Run smoke test**

Run: `cd /home/patty/indiestack && python3 smoke_test.py`
Expected: 37/37 pass (or close — `/admin/analytics` and `/admin/outreach` may now redirect instead of 200, which the smoke test should handle as 302→200)

**Step 2: Check if smoke test needs updating**

If the smoke test expects 200 from `/admin/analytics` or `/admin/outreach`, update it to expect 302 or remove those entries (they now redirect to `/admin?tab=growth`).

**Step 3: Deploy**

Run: `cd /home/patty/indiestack && ~/.fly/bin/flyctl deploy --remote-only --buildkit`
Expected: Successful deploy

**Step 4: Verify in browser**

- `/admin` → Overview tab with 8 KPI cards
- `/admin?tab=tools` → Tools table with filters
- `/admin?tab=people` → Unified people table
- `/admin?tab=content` → Collapsible collections/stacks/reviews
- `/admin?tab=growth` → Traffic section with charts
- `/admin?tab=growth&section=email` → Email blast panels
- `/admin/analytics` → Redirects to `/admin?tab=growth`
- `/admin/outreach` → Redirects to `/admin?tab=growth&section=email`

---

## Execution Order & Dependencies

| Task | Depends On | Can Parallelize With |
|------|-----------|---------------------|
| 1. Shared Helpers | None | Tasks 2, 3 |
| 2. Refactor analytics | Task 1 | Task 3 |
| 3. Refactor outreach | Task 1 | Task 2 |
| 4. Rewrite admin.py | Tasks 1, 2, 3 | None |
| 5. Update main.py | Task 4 | None |
| 6. Smoke test & deploy | Task 5 | None |

**Recommended parallel execution:**
- Phase 1: Task 1 (shared helpers)
- Phase 2: Tasks 2 + 3 in parallel (refactor analytics + outreach)
- Phase 3: Task 4 (rewrite admin.py — the big one)
- Phase 4: Tasks 5 + 6 (wire up + deploy)

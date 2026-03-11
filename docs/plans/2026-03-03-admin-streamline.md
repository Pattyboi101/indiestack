# Admin Streamline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reorganise the admin Command Centre from a cluttered 5-tab layout into a focused 4-tab layout with proper sub-navigation, trimmed Overview, and consistent code patterns.

**Architecture:** Pure reorganisation — no new features, no DB changes. Drop Content tab (merge stacks/reviews into Tools sub-nav). Surface Growth's hidden sections (magic links, makers, stale tools) as proper sub-nav items. Split Traffic into Charts/Tables/Funnels. Trim Overview to actionables + today's pulse. Add search to People. Deduplicate badge helpers. Optimise chart queries from 38 → 2.

**Tech Stack:** Python/FastAPI, pure HTML string templates, SQLite (aiosqlite), design tokens from components.py `:root`

---

### Task 1: Deduplicate badge helpers into admin_helpers.py

**Files:**
- Modify: `src/indiestack/routes/admin_helpers.py:45-59` — add `freshness_badge()` function
- Modify: `src/indiestack/routes/admin_outreach.py:27-56` — delete `_days_ago_label()`, `_status_badge()`, `_freshness_badge()`
- Modify: `src/indiestack/routes/admin_analytics.py:318-331` — replace inline badge logic with `status_badge()` import

**Step 1: Add `freshness_badge()` to admin_helpers.py**

Add after the existing `status_badge()` function (after line 119):

```python
def freshness_badge(freshness):
    """Tool freshness badge: active (green), stale (yellow), inactive (red), unknown (gray)."""
    f = (freshness or "").lower().strip()
    if f == "active":
        bg, fg, label = "#DCFCE7", "#16a34a", "Active"
    elif f == "stale":
        bg, fg, label = "#FEF9C3", "#CA8A04", "Stale"
    elif f == "inactive":
        bg, fg, label = "#FEE2E2", "#DC2626", "Inactive"
    else:
        bg, fg, label = "#F3F4F6", "#6B7280", "Unknown"
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:9999px;'
        f'font-size:11px;font-weight:700;background:{bg};color:{fg};">'
        f'{label}</span>'
    )
```

**Step 2: Update admin_outreach.py imports and delete private helpers**

Replace lines 27-56 (the three private helper functions) with nothing. Update the imports at the top to add:

```python
from indiestack.routes.admin_helpers import time_ago, days_ago_label, status_badge, freshness_badge, kpi_card, data_table, row_bg
```

Then find-and-replace throughout admin_outreach.py:
- `_days_ago_label(` → `days_ago_label(`
- `_status_badge(` → `status_badge(`
- `_freshness_badge(` → `freshness_badge(`

**Step 3: Update admin_analytics.py inline badge logic**

In `render_funnels_section()` (lines 318-331), replace the inline Active/Idle/Dormant badge logic with:

```python
from indiestack.routes.admin_helpers import status_badge as activity_badge
```

Then replace the entire badge calculation block (lines 319-331) with:

```python
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
```

**Step 4: Update admin_helpers.py exports**

Add `freshness_badge` to the module's public API. The existing `days_ago_label` is already exported (line 45).

**Step 5: Syntax check all 3 files**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin_helpers.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin_outreach.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin_analytics.py').read()); print('OK')"
```

---

### Task 2: Update tab_nav and growth_sub_nav in admin_helpers.py

**Files:**
- Modify: `src/indiestack/routes/admin_helpers.py:139-199` — update `tab_nav()` (4 tabs) and `growth_sub_nav()` (9 sections)

**Step 1: Update `tab_nav()` — remove Content tab**

Replace the `tabs` list (lines 141-147) with:

```python
    tabs = [
        ("overview", "Overview"),
        ("tools", "Tools"),
        ("people", "People"),
        ("growth", "Growth"),
    ]
```

**Step 2: Update `growth_sub_nav()` — 9 honest sections**

Replace the `sections` list (lines 178-183) with:

```python
    sections = [
        ("charts", "Charts"),
        ("tables", "Tables"),
        ("funnels", "Funnels"),
        ("search", "Search"),
        ("email", "Email"),
        ("magic", "Magic Links"),
        ("makers", "Makers"),
        ("stale", "Stale Tools"),
        ("social", "Social"),
    ]
```

**Step 3: Add tools_sub_nav() function**

Add after `growth_sub_nav()`:

```python
def tools_sub_nav(active_section, pending_count=0):
    """Sub-nav within the Tools tab."""
    sections = [
        ("pending", f"Pending ({pending_count})" if pending_count else "Pending"),
        ("all", "All Tools"),
        ("claims", "Claims"),
        ("stacks", "Stacks"),
        ("reviews", "Reviews"),
    ]
    items = []
    for slug, label in sections:
        is_active = (active_section or "").lower() == slug
        if is_active:
            style = "color:var(--slate);border-bottom:2px solid var(--slate);font-weight:600;"
        else:
            style = "color:var(--ink-muted);border-bottom:2px solid transparent;"
        items.append(
            f'<a href="/admin?tab=tools&amp;section={slug}" style="{style}padding:8px 14px;'
            f'text-decoration:none;font-size:13px;font-family:var(--font-body);'
            f'white-space:nowrap;">{label}</a>'
        )
    return (
        f'<div style="display:flex;border-bottom:1px solid var(--border);'
        f'margin-bottom:20px;gap:0;opacity:0.85;">{"".join(items)}</div>'
    )
```

**Step 4: Syntax check**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin_helpers.py').read()); print('OK')"
```

---

### Task 3: Rewrite Overview tab (command centre)

**Files:**
- Modify: `src/indiestack/routes/admin.py:125-355` — rewrite `render_overview()`

**Step 1: Rewrite `render_overview()` with two-column layout**

Replace the entire function (lines 125-355) with:

```python
async def render_overview(db, request, pending):
    """Overview: action items (left) + today's pulse (right)."""
    from datetime import datetime, timedelta

    pending_count = len(pending)
    pending_avatars = await get_pending_avatars(db)

    # ── Claim Requests ──
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

    # ── LEFT COLUMN: Action Items ──
    # Pending tools
    pending_html = ''
    if pending:
        cards = ''
        for t in pending:
            tid = t['id']
            name = escape(str(t['name']))
            tagline = escape(str(t['tagline']))
            cards += f"""
            <div class="card" style="margin-bottom:8px;padding:12px 16px;">
                <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap;">
                    <div style="flex:1;min-width:200px;">
                        <strong style="font-size:14px;color:var(--ink);">{name}</strong>
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
        if pending_count > 1:
            cards = f"""
            <div style="display:flex;gap:6px;margin-bottom:8px;">
                <form method="post" action="/admin" style="margin:0;">
                    <input type="hidden" name="action" value="approve_all">
                    <button type="submit" style="padding:5px 14px;border-radius:999px;font-size:12px;font-weight:600;
                            cursor:pointer;background:#16a34a;color:white;border:none;">Approve All ({pending_count})</button>
                </form>
                <form method="post" action="/admin" style="margin:0;">
                    <input type="hidden" name="action" value="reject_all">
                    <button type="submit" style="padding:5px 14px;border-radius:999px;font-size:12px;font-weight:600;
                            cursor:pointer;background:#dc2626;color:white;border:none;"
                            onclick="return confirm('Reject all {pending_count} pending tools?')">Reject All</button>
                </form>
            </div>
            """ + cards
        pending_html = f"""
        <div style="margin-bottom:24px;">
            <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:8px;">
                Pending Tools ({pending_count})
            </h3>
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
                {pixel_icon_svg(a['pixel_avatar'], size=48)}
                <p style="font-size:11px;color:var(--ink-muted);margin-top:6px;">{a_name}</p>
                <div style="display:flex;gap:4px;margin-top:6px;">
                    <form method="post" action="/admin" style="flex:1;">
                        <input type="hidden" name="action" value="approve_avatar">
                        <input type="hidden" name="user_id" value="{a['id']}">
                        <button type="submit" style="width:100%;padding:4px;font-size:11px;background:#16a34a;color:white;border:none;border-radius:999px;cursor:pointer;">&#10003;</button>
                    </form>
                    <form method="post" action="/admin" style="flex:1;">
                        <input type="hidden" name="action" value="reject_avatar">
                        <input type="hidden" name="user_id" value="{a['id']}">
                        <button type="submit" style="width:100%;padding:4px;font-size:11px;background:#dc2626;color:white;border:none;border-radius:999px;cursor:pointer;">&#10007;</button>
                    </form>
                </div>
            </div>
            """
        avatars_html = f"""
        <div style="margin-bottom:24px;">
            <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:8px;">Pending Avatars ({len(pending_avatars)})</h3>
            <div style="display:flex;flex-wrap:wrap;gap:12px;">{avatar_cards}</div>
        </div>
        """

    # Claims
    claims_html = ''
    if claims:
        claim_cards = ''
        for c in claims:
            claim_cards += f"""
            <div class="card" style="padding:12px 16px;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
                <div>
                    <strong style="font-size:14px;color:var(--ink);">{escape(str(c['tool_name']))}</strong>
                    <span style="color:var(--ink-muted);font-size:12px;margin-left:8px;">by {escape(str(c['user_name'] or c['user_email']))}</span>
                </div>
                <div style="display:flex;gap:6px;">
                    <form method="post" action="/admin" style="margin:0;">
                        <input type="hidden" name="action" value="approve_claim">
                        <input type="hidden" name="claim_id" value="{c['id']}">
                        <input type="hidden" name="tool_id" value="{c['tool_id']}">
                        <input type="hidden" name="user_id" value="{c['user_id']}">
                        <button type="submit" style="padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;cursor:pointer;background:#16a34a;color:white;border:none;">Approve</button>
                    </form>
                    <form method="post" action="/admin" style="margin:0;">
                        <input type="hidden" name="action" value="reject_claim">
                        <input type="hidden" name="claim_id" value="{c['id']}">
                        <button type="submit" style="padding:4px 12px;border-radius:999px;font-size:11px;font-weight:600;cursor:pointer;background:#dc2626;color:white;border:none;">Reject</button>
                    </form>
                </div>
            </div>
            """
        claims_html = f"""
        <div style="margin-bottom:24px;">
            <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:8px;">Claim Requests ({len(claims)})</h3>
            {claim_cards}
        </div>
        """

    # "All clear" if nothing pending
    if not pending and not pending_avatars and not claims:
        left_col = '<div style="display:flex;align-items:center;justify-content:center;padding:48px 0;color:var(--ink-muted);font-size:15px;">&#10003; All clear &mdash; nothing to review</div>'
    else:
        left_col = pending_html + avatars_html + claims_html

    # ── RIGHT COLUMN: Today's Pulse ──
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM page_views WHERE timestamp >= ?", (today_start,))
    views_today = (await cursor.fetchone())['cnt']

    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM search_logs WHERE created_at >= ?", (today_start,))
    searches_today = (await cursor.fetchone())['cnt']

    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM users WHERE created_at >= ?", (today_start,))
    signups_today = (await cursor.fetchone())['cnt']

    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM agent_citations WHERE created_at >= ?", (today_start,))
    ai_recs_today = (await cursor.fetchone())['cnt']

    kpi_html = f"""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px;">
        {kpi_card("Page Views", f"{views_today:,}", sublabel="Today")}
        {kpi_card("Searches", f"{searches_today:,}", sublabel="Today")}
        {kpi_card("Signups", f"{signups_today:,}", sublabel="Today")}
        {kpi_card("AI Recs", f"{ai_recs_today:,}", sublabel="Today")}
    </div>
    """

    # Alerts
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM tools WHERE status='approved' AND created_at < datetime('now', '-90 days')")
    stale_count = (await cursor.fetchone())['cnt']
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM search_logs WHERE result_count = 0 AND created_at >= datetime('now', '-30 days')")
    gap_count = (await cursor.fetchone())['cnt']

    alert_items = []
    if stale_count > 0:
        alert_items.append(f'<span style="color:#D97706;font-weight:600;">{stale_count}</span> stale tools')
    if gap_count > 0:
        alert_items.append(f'<span style="color:#DC2626;font-weight:600;">{gap_count}</span> search gaps')

    alerts_html = ''
    if alert_items:
        alerts_html = f'<div style="font-size:12px;color:var(--ink-muted);padding:10px 14px;background:var(--cream-dark);border-radius:var(--radius-sm);margin-bottom:16px;">{" &middot; ".join(alert_items)}</div>'

    # Last 5 submissions
    cursor = await db.execute(
        """SELECT t.name, t.status, t.created_at
           FROM tools t ORDER BY t.created_at DESC LIMIT 5""")
    recent = await cursor.fetchall()
    recent_html = ''
    if recent:
        items = ''
        for r in recent:
            name = escape(str(r['name']))
            ago = time_ago(r['created_at'])
            status = str(r['status'])
            dot_color = '#16a34a' if status == 'approved' else '#D97706' if status == 'pending' else '#dc2626'
            items += f'<div style="display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid var(--border);font-size:13px;"><span style="width:6px;height:6px;border-radius:50%;background:{dot_color};flex-shrink:0;"></span><span style="color:var(--ink);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{name}</span><span style="color:var(--ink-muted);font-size:11px;white-space:nowrap;">{ago}</span></div>'
        recent_html = f'<div style="margin-top:4px;"><p style="font-size:12px;font-weight:600;color:var(--ink-muted);margin-bottom:6px;">Latest submissions</p>{items}</div>'

    right_col = kpi_html + alerts_html + recent_html

    return f"""
    <div style="display:grid;grid-template-columns:3fr 2fr;gap:32px;align-items:start;">
        <div>{left_col}</div>
        <div>{right_col}</div>
    </div>
    <style>@media(max-width:768px){{[style*="grid-template-columns:3fr 2fr"]{{grid-template-columns:1fr!important;}}}}</style>
    """
```

**Step 2: Syntax check**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin.py').read()); print('OK')"
```

---

### Task 4: Rewrite Tools tab with sub-navigation

**Files:**
- Modify: `src/indiestack/routes/admin.py:358-726` — rewrite `render_tools_tab()` with sub-nav
- Modify: `src/indiestack/routes/admin.py:842-1009` — move stacks/reviews into tools tab, delete `render_content_tab()`

**Step 1: Import `tools_sub_nav` in admin.py**

Update the import at the top (line 25-28) to add `tools_sub_nav`:

```python
from indiestack.routes.admin_helpers import (
    time_ago, kpi_card, pending_alert_bar, status_badge, role_badge,
    tab_nav, growth_sub_nav, tools_sub_nav, row_bg, data_table
)
```

**Step 2: Rewrite `render_tools_tab()` with sub-nav routing**

Replace the function with a sub-nav router that delegates to section renderers:

```python
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
```

Then extract each existing section into its own function. The pending and all-tools sections stay largely the same, but the all-tools table loses the Boost, Feature, and Price columns (those move to the edit page). Claims is extracted verbatim. Stacks and Reviews are moved from `render_content_tab()`.

**Key changes to All Tools table**: Remove columns for Boost (inline input + Set button), Feature (details dropdown), and Price. Keep: Name (with edit link + badges), Status, Upvotes, Category, Added, Verify toggle, Ejectable toggle, Delete, Magic Link.

The `_render_tools_pending()`, `_render_tools_all()`, `_render_tools_claims()` functions contain the existing code from `render_tools_tab()` split into logical sections.

`_render_tools_stacks()` = the existing `_render_stacks_section()` code but without the `<details>` wrapper (rendered directly).

`_render_tools_reviews()` = the existing `_render_reviews_section()` code but without the `<details>` wrapper.

**Step 3: Delete `render_content_tab()` and its helpers**

Delete lines 842-1009 (`render_content_tab()`, `_render_stacks_section()`, `_render_reviews_section()`).

**Step 4: Update the GET router to remove content tab**

In `admin_get()` (line 95-107), remove the `elif tab == 'content'` branch. Update the redirect for content-related POST actions (delete_review, create_stack, etc.) to redirect to `tab=tools&section=stacks` or `tab=tools&section=reviews` instead of `tab=content`.

**Step 5: Add the magic link JS to the pending/all section**

The `generateMagicLink()` JS function needs to be included when rendering the `all` section (it's currently appended at the end of `render_tools_tab()`).

**Step 6: Syntax check**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin.py').read()); print('OK')"
```

---

### Task 5: Add search to People tab

**Files:**
- Modify: `src/indiestack/routes/admin.py:731-839` — add search input to People tab

**Step 1: Add search parameter and input**

Add `search_q = request.query_params.get('q', '')` alongside the existing `role_filter`.

Add a search input to the filter bar:

```python
    search_input = f'''
    <form method="GET" action="/admin" style="display:inline;">
        <input type="hidden" name="tab" value="people">
        {'<input type="hidden" name="role" value="' + escape(role_filter) + '">' if role_filter else ''}
        <input type="text" name="q" value="{escape(search_q)}" placeholder="Search name or email..."
               style="padding:6px 12px;border:1px solid var(--border);border-radius:999px;font-size:13px;width:200px;">
        <button type="submit" class="btn btn-primary" style="padding:6px 14px;font-size:12px;">Search</button>
    </form>
    '''
```

**Step 2: Apply search filter**

After the role filter, add:

```python
    if search_q:
        q_lower = search_q.lower()
        all_people = [p for p in all_people if
                      q_lower in str(p.get('name', '') or '').lower() or
                      q_lower in str(p.get('email', '') or '').lower()]
```

**Step 3: Update filter_html to include search input**

```python
    filter_html = f'<div style="display:flex;gap:8px;margin-bottom:20px;align-items:center;flex-wrap:wrap;">{pills}{search_input}</div>'
```

**Step 4: Syntax check**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin.py').read()); print('OK')"
```

---

### Task 6: Rewrite Growth tab routing with 9 sub-nav items

**Files:**
- Modify: `src/indiestack/routes/admin.py:1012-1032` — update `render_growth_tab()` routing
- Modify: `src/indiestack/routes/admin_analytics.py` — split `render_traffic_section()` into charts + tables

**Step 1: Update `render_growth_tab()` routing**

Replace lines 1014-1032 with:

```python
async def render_growth_tab(db, request):
    """Growth tab: 9 sub-nav sections."""
    section = request.query_params.get('section', 'charts')
    html = growth_sub_nav(section)

    if section == 'charts':
        html += await render_charts_section(db, request)
    elif section == 'tables':
        html += await render_tables_section(db, request)
    elif section == 'funnels':
        html += await render_funnels_section(db)
    elif section == 'search':
        html += await render_search_section(db)
    elif section == 'email':
        html += await render_email_section(db, request)
    elif section == 'magic':
        html += await render_magic_section(db, request)
    elif section == 'makers':
        html += await render_makers_section(db, request)
    elif section == 'stale':
        html += await render_stale_section(db, request)
    elif section == 'social':
        html += await render_social_section(db)
    else:
        html += await render_charts_section(db, request)

    return html
```

**Step 2: Update imports in admin.py**

Update the analytics imports to include the new split functions:

```python
from indiestack.routes.admin_analytics import (
    render_charts_section, render_tables_section, render_funnels_section,
    render_search_section, render_growth_section
)
```

**Step 3: Split `render_traffic_section()` in admin_analytics.py**

Split the existing function into two:
- `render_charts_section(db, request)` — period pills, 6 KPI cards, daily bar chart, hourly heatmap, revenue chart
- `render_tables_section(db, request)` — top pages table, top referrers table, recent visitors table

Both share the same `period` / `since` parameter parsing.

**Step 4: Optimise chart queries — replace 38 individual queries with 2 GROUP BY queries**

Replace the daily chart loop (lines 73-83):

```python
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
```

Replace the hourly chart loop (lines 88-98):

```python
    # Hourly traffic — single GROUP BY query
    cursor = await db.execute(
        """SELECT CAST(strftime('%H', timestamp) AS INTEGER) as hour, COUNT(*) as cnt
           FROM page_views WHERE timestamp >= datetime('now', '-7 days')
           GROUP BY hour ORDER BY hour"""
    )
    hourly_rows = {r['hour']: r['cnt'] for r in await cursor.fetchall()}
    hourly_data = [(f"{h:02d}:00", hourly_rows.get(h, 0)) for h in range(24)]
```

**Step 5: Update the old outreach redirect**

In `admin_outreach_redirect()` (line 1247-1251), update the section_map for the new sub-nav slugs:

```python
    section_map = {"email": "email", "magic": "magic", "makers": "makers", "stale": "stale", "social": "social"}
```

**Step 6: Syntax check all files**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin_analytics.py').read()); print('OK')"
```

---

### Task 7: Update POST action redirects

**Files:**
- Modify: `src/indiestack/routes/admin.py:1035-1233` — update redirect URLs for moved sections

**Step 1: Update Content-related redirects to Tools tab**

Find and replace these redirect URLs in the POST handler:

- `tab=content&toast=Review+deleted` → `tab=tools&section=reviews&toast=Review+deleted`
- `tab=content&toast=Stack+created` → `tab=tools&section=stacks&toast=Stack+created`
- `tab=content&toast=Tool+added+to+stack` → `tab=tools&section=stacks&toast=Tool+added+to+stack`
- `tab=content&toast=Tool+removed+from+stack` → `tab=tools&section=stacks&toast=Tool+removed+from+stack`
- `tab=content&toast=Stack+deleted` → `tab=tools&section=stacks&toast=Stack+deleted`

**Step 2: Syntax check**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin.py').read()); print('OK')"
```

---

### Task 8: Smoke test and deploy

**Step 1: Run all syntax checks**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin.py').read()); print('admin OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin_helpers.py').read()); print('helpers OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin_analytics.py').read()); print('analytics OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/admin_outreach.py').read()); print('outreach OK')"
```

**Step 2: Run smoke tests**

```bash
python3 smoke_test.py
```

Expected: All 38 pass. The admin page itself requires auth so it returns 200 (login form) which still passes.

**Step 3: Deploy**

```bash
~/.fly/bin/flyctl deploy --remote-only
```

**Step 4: Manual verification**

Visit `/admin` and check:
- 4 tabs visible (no Content tab)
- Overview shows two columns: action items left, today's pulse right
- Tools tab has sub-nav: Pending / All / Claims / Stacks / Reviews
- People tab has search input
- Growth tab has 9 sub-nav items: Charts / Tables / Funnels / Search / Email / Magic Links / Makers / Stale Tools / Social
- All redirects work (old `/admin?tab=content` falls through to overview)

---

## Execution Strategy

**Parallel agents (3 groups):**

- **Agent A**: Task 1 (deduplicate helpers) + Task 2 (update nav functions) — both in `admin_helpers.py`
- **Agent B**: Task 3 (Overview rewrite) + Task 4 (Tools tab rewrite) + Task 5 (People search) — all in `admin.py`
- **Agent C**: Task 6 (Growth tab split + chart optimisation) — `admin.py` routing + `admin_analytics.py` split

Then sequentially: Task 7 (redirect fixups) → Task 8 (smoke test + deploy)

# Demand Signals Pro Upgrade — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform the Demand Signals Pro dashboard from a raw data table into an actionable intelligence engine with Opportunity Scores, sparklines, competitor density, insight cards, and a gaps-only live feed.

**Architecture:** All changes live in two files: `db.py` (new query: `get_demand_clusters_enriched`) and `gaps.py` (rewrite the pro dashboard section of `demand_pro()`). The enriched query returns all derived metrics (opportunity score, competitor density, 14-day sparkline data) in a single SQL + Python pass, and the template renders them with inline SVG and CSS. No new tables, no JS frameworks, no external libraries.

**Tech Stack:** Python 3.11, FastAPI, aiosqlite, inline SVG, CSS-only visualizations, vanilla JS for filter toggles.

---

## File Map

| File | Changes |
|------|---------|
| `src/indiestack/db.py` | New function `get_demand_clusters_enriched()` — enriches clusters with opportunity score, competitor density, 14-day daily counts for sparklines |
| `src/indiestack/routes/gaps.py` | Rewrite pro dashboard: insight cards, new table with opportunity score + sparklines + density, gaps-only live feed filter, CSV export link |
| `src/indiestack/routes/pulse.py` | Add `filter` query param to `/api/pulse` for gaps-only mode |

---

### Task 1: Enriched demand clusters query in db.py

**Files:**
- Modify: `src/indiestack/db.py` (after `get_demand_clusters` at line ~5094)

**What it does:** New `get_demand_clusters_enriched()` function that returns everything the pro dashboard needs in one call. For each zero-result query cluster, it calculates:
- `opportunity_score`: `zero_count * (1 + zero_count / max(search_count, 1))` — higher when demand is high AND supply is low
- `competitor_density`: count of approved tools whose name, tagline, or tags match the query (FTS-like LIKE query)
- `daily_counts`: list of 14 integers — search counts per day for the last 14 days (for sparkline rendering)
- All existing fields: query, search_count, zero_count, last_searched, first_searched, sources

**Implementation:**

Add this function after `get_demand_clusters` (~line 5113):

```python
async def get_demand_clusters_enriched(db, limit: int = 50) -> list:
    """Enriched demand clusters with opportunity score, competitor density, and sparkline data."""
    # Base clusters
    cursor = await db.execute("""
        SELECT LOWER(TRIM(query)) as query,
               COUNT(*) as search_count,
               SUM(CASE WHEN result_count = 0 THEN 1 ELSE 0 END) as zero_count,
               MAX(created_at) as last_searched,
               MIN(created_at) as first_searched,
               COUNT(DISTINCT source) as source_count,
               GROUP_CONCAT(DISTINCT source) as sources
        FROM search_logs
        WHERE LENGTH(TRIM(query)) >= 3
          AND query NOT LIKE '%http%'
          AND query NOT LIKE '%.com%'
        GROUP BY LOWER(TRIM(query))
        HAVING zero_count > 0
        ORDER BY zero_count DESC, search_count DESC
        LIMIT ?
    """, (limit,))
    clusters = [dict(r) for r in await cursor.fetchall()]

    for c in clusters:
        # Opportunity score: demand * gap ratio
        sc = max(c['search_count'], 1)
        c['opportunity_score'] = round(c['zero_count'] * (1 + c['zero_count'] / sc), 1)

        # Competitor density: how many approved tools match this query?
        q_like = f"%{c['query']}%"
        cur2 = await db.execute(
            """SELECT COUNT(*) as cnt FROM tools
               WHERE status = 'approved'
               AND (LOWER(name) LIKE ? OR LOWER(tagline) LIKE ? OR LOWER(tags) LIKE ?)""",
            (q_like, q_like, q_like),
        )
        row = await cur2.fetchone()
        c['competitor_density'] = row['cnt'] if row else 0

        # 14-day sparkline data
        cur3 = await db.execute(
            """SELECT DATE(created_at) as day, COUNT(*) as cnt
               FROM search_logs
               WHERE LOWER(TRIM(query)) = ?
                 AND created_at >= datetime('now', '-14 days')
               GROUP BY DATE(created_at)
               ORDER BY day""",
            (c['query'],),
        )
        day_rows = await cur3.fetchall()
        day_map = {r['day']: r['cnt'] for r in day_rows}
        # Build 14-element list (fill missing days with 0)
        from datetime import date, timedelta
        today = date.today()
        c['daily_counts'] = [day_map.get((today - timedelta(days=13 - i)).isoformat(), 0) for i in range(14)]

    # Re-sort by opportunity score descending
    clusters.sort(key=lambda c: c['opportunity_score'], reverse=True)
    return clusters
```

**Verify:** `python3 -c "import py_compile; py_compile.compile('src/indiestack/db.py', doraise=True); print('OK')"`

---

### Task 2: SVG sparkline renderer in gaps.py

**Files:**
- Modify: `src/indiestack/routes/gaps.py` (add helper function near top, after `_relative_time`)

**What it does:** Pure Python function that takes a list of 14 integers and returns an inline SVG sparkline string. 80px wide, 20px tall. Uses SVG `<polyline>` — no JS.

**Implementation:**

Add after `_relative_time()` (~line 57):

```python
def _sparkline_svg(daily_counts: list, width: int = 80, height: int = 20) -> str:
    """Render a 14-day sparkline as inline SVG."""
    if not daily_counts or all(v == 0 for v in daily_counts):
        return '<span style="color:var(--ink-muted);font-size:11px;">no data</span>'
    max_val = max(daily_counts) or 1
    n = len(daily_counts)
    step = width / max(n - 1, 1)
    points = ' '.join(
        f'{round(i * step, 1)},{round(height - (v / max_val) * (height - 2) - 1, 1)}'
        for i, v in enumerate(daily_counts)
    )
    return (
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'style="vertical-align:middle;">'
        f'<polyline points="{points}" fill="none" stroke="var(--accent)" '
        f'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>'
        f'</svg>'
    )
```

**Verify:** `python3 -c "import py_compile; py_compile.compile('src/indiestack/routes/gaps.py', doraise=True); print('OK')"`

---

### Task 3: Competitor density indicator in gaps.py

**Files:**
- Modify: `src/indiestack/routes/gaps.py` (add helper function near top)

**What it does:** Renders 5 small squares — filled green (empty market) to red (saturated) based on competitor count. 0 competitors = all green, 5+ = all red.

**Implementation:**

Add after `_sparkline_svg()`:

```python
def _density_indicator(count: int) -> str:
    """Render competitor density as 5 colored squares."""
    if count == 0:
        label = 'Empty market'
        color = '#22C55E'
    elif count <= 2:
        label = f'{count} similar tool{"s" if count > 1 else ""}'
        color = '#84CC16'
    elif count <= 4:
        label = f'{count} similar tools'
        color = '#E2B764'
    else:
        label = f'{count}+ similar tools'
        color = '#EF4444'
    filled = min(count, 5)
    squares = ''
    for i in range(5):
        bg = color if i < filled else 'var(--border)'
        squares += f'<span style="display:inline-block;width:6px;height:6px;border-radius:1px;background:{bg};"></span>'
    return f'<span title="{label}" style="display:inline-flex;gap:2px;align-items:center;">{squares}</span>'
```

**Verify:** `python3 -c "import py_compile; py_compile.compile('src/indiestack/routes/gaps.py', doraise=True); print('OK')"`

---

### Task 4: Rewrite the pro dashboard in gaps.py

**Files:**
- Modify: `src/indiestack/routes/gaps.py` — the `demand_pro()` function, lines 603-831

**What it does:** Complete rewrite of the pro dashboard body. Replaces the current stats bar + bar chart + basic table + noisy live feed with:

1. **Hero** (keep, minor copy tweak)
2. **Stats bar** (keep, add "Top Opportunity Score" as 4th stat)
3. **Insight cards** — top 3 opportunities as styled cards with sparkline + density + score
4. **Enriched table** — Opportunity Score column (sortable via vanilla JS), sparkline column, density column, existing columns
5. **Gaps-only live feed** — filter pulse to show only gap events by default, with toggle

**Implementation:**

Replace everything from `# ── Pro dashboard ──` (line 603) to the end of `demand_pro()` (line 831) with the following:

```python
    # ── Pro dashboard ──────────────────────────────────────────────────
    from indiestack.db import get_demand_clusters_enriched, get_demand_trends, get_pulse_feed
    clusters = await get_demand_clusters_enriched(db, limit=50)
    trends = await get_demand_trends(db, days=30)
    pulse_events = await get_pulse_feed(db, limit=30)

    # Filter pulse to gaps only for cleaner default view
    gap_events = [dict(e) for e in pulse_events if e['type'] == 'gap']

    # Stats
    total_searches_30d = sum(t['total_searches'] for t in trends) if trends else 0
    zero_results_30d = sum(t['zero_results'] for t in trends) if trends else 0
    fill_rate = round(((total_searches_30d - zero_results_30d) / total_searches_30d * 100) if total_searches_30d > 0 else 0, 1)
    top_opp = clusters[0]['opportunity_score'] if clusters else 0

    # ── Hero ──
    hero = f'''
    <section style="padding:64px 24px 32px;text-align:center;">
        <div class="container" style="max-width:900px;">
            <p style="font-size:13px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
                Pro Dashboard
            </p>
            <h1 style="font-family:var(--heading-font, var(--font-display));font-size:clamp(28px,4vw,42px);color:var(--ink);margin-bottom:16px;line-height:1.2;">
                Demand Signals Pro
            </h1>
            <p style="font-size:17px;color:var(--ink-muted);max-width:600px;margin:0 auto 32px;line-height:1.6;">
                What AI agents are searching for, scored by opportunity. Build what the market actually wants.
            </p>
        </div>
    </section>
    '''

    # ── Stats bar (4 stats) ──
    stats_bar = f'''
    <section style="padding:0 24px 40px;">
        <div class="container" style="max-width:900px;">
            <div style="display:flex;gap:1px;background:var(--border);border-radius:12px;overflow:hidden;border:1px solid var(--border);">
                <div style="flex:1;background:var(--card-bg);padding:20px 16px;text-align:center;">
                    <div style="font-family:var(--font-display);font-size:28px;font-weight:700;color:var(--accent);margin-bottom:4px;">{total_searches_30d:,}</div>
                    <div style="font-size:12px;color:var(--ink-muted);">Searches (30d)</div>
                </div>
                <div style="flex:1;background:var(--card-bg);padding:20px 16px;text-align:center;">
                    <div style="font-family:var(--font-display);font-size:28px;font-weight:700;color:#EF4444;margin-bottom:4px;">{zero_results_30d:,}</div>
                    <div style="font-size:12px;color:var(--ink-muted);">Zero Results</div>
                </div>
                <div style="flex:1;background:var(--card-bg);padding:20px 16px;text-align:center;">
                    <div style="font-family:var(--font-display);font-size:28px;font-weight:700;color:var(--accent);margin-bottom:4px;">{fill_rate}%</div>
                    <div style="font-size:12px;color:var(--ink-muted);">Fill Rate</div>
                </div>
                <div style="flex:1;background:var(--card-bg);padding:20px 16px;text-align:center;">
                    <div style="font-family:var(--font-display);font-size:28px;font-weight:700;color:var(--accent);margin-bottom:4px;">{top_opp}</div>
                    <div style="font-size:12px;color:var(--ink-muted);">Top Opp. Score</div>
                </div>
            </div>
        </div>
    </section>
    '''

    # ── Insight cards (top 3 opportunities) ──
    insight_cards_html = ''
    for c in clusters[:3]:
        q = escape(c['query'])
        density_html = _density_indicator(c['competitor_density'])
        spark = _sparkline_svg(c['daily_counts'])
        density_label = 'Empty market' if c['competitor_density'] == 0 else f"{c['competitor_density']} similar tool{'s' if c['competitor_density'] != 1 else ''}"
        insight_cards_html += f'''
            <div style="flex:1;min-width:220px;background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:24px;">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                    <span style="font-size:11px;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:0.5px;">Score {c['opportunity_score']}</span>
                    {density_html}
                </div>
                <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin:0 0 8px;line-height:1.3;">
                    &ldquo;{q}&rdquo;
                </h3>
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:12px;">
                    {spark}
                    <span style="font-size:12px;color:var(--ink-muted);">14d trend</span>
                </div>
                <div style="font-size:13px;color:var(--ink-muted);margin-bottom:16px;">
                    {c['zero_count']} failed search{'es' if c['zero_count'] != 1 else ''} &middot; {density_label}
                </div>
                <a href="/submit?name={quote(c['query'])}"
                   style="display:inline-block;padding:8px 18px;background:var(--accent);color:white;border-radius:8px;font-size:13px;font-weight:600;text-decoration:none;">
                    Build This &rarr;
                </a>
            </div>'''

    insights_section = f'''
    <section style="padding:0 24px 40px;">
        <div class="container" style="max-width:900px;">
            <h2 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:16px;">Top Opportunities</h2>
            <div style="display:flex;gap:16px;flex-wrap:wrap;">
                {insight_cards_html if insight_cards_html else '<p style="color:var(--ink-muted);">No signals yet.</p>'}
            </div>
        </div>
    </section>
    '''

    # ── Enriched signals table ──
    cluster_rows = ''
    for idx, c in enumerate(clusters):
        q = escape(c['query'])
        spark = _sparkline_svg(c['daily_counts'])
        density_html = _density_indicator(c['competitor_density'])
        sources = escape(c['sources'] or 'web')
        first_seen = _relative_time(c['first_searched'])
        last_seen = _relative_time(c['last_searched'])
        opp = c['opportunity_score']

        if c['zero_count'] >= 10:
            badge_label, badge_bg, badge_color = 'HIGH', 'rgba(239,68,68,0.12)', '#EF4444'
        elif c['zero_count'] >= 5:
            badge_label, badge_bg, badge_color = 'GROWING', 'rgba(226,183,100,0.12)', '#E2B764'
        elif c['zero_count'] >= 2:
            badge_label, badge_bg, badge_color = 'EMERGING', 'rgba(0,212,245,0.12)', 'var(--accent)'
        else:
            badge_label, badge_bg, badge_color = 'NEW', 'rgba(255,255,255,0.04)', 'var(--ink-muted)'

        cluster_rows += f'''
            <tr style="border-bottom:1px solid var(--border);" data-opp="{opp}" data-zero="{c['zero_count']}" data-last="{idx}">
                <td style="padding:12px 16px;font-weight:500;color:var(--ink);">{q}</td>
                <td style="padding:12px 16px;text-align:center;">
                    <span style="font-family:var(--font-mono);font-size:14px;font-weight:700;color:var(--accent);">{opp}</span>
                </td>
                <td style="padding:12px 16px;text-align:center;">{spark}</td>
                <td style="padding:12px 16px;text-align:center;">{density_html}</td>
                <td style="padding:12px 16px;text-align:center;color:#EF4444;font-weight:600;">{c['zero_count']}</td>
                <td style="padding:12px 16px;text-align:center;color:var(--ink-muted);">{c['search_count']}</td>
                <td style="padding:12px 16px;text-align:center;font-size:12px;color:var(--ink-muted);">{last_seen}</td>
                <td style="padding:12px 16px;text-align:center;">
                    <span style="display:inline-block;padding:3px 10px;border-radius:999px;font-size:11px;font-weight:700;letter-spacing:0.5px;background:{badge_bg};color:{badge_color};">{badge_label}</span>
                </td>
            </tr>'''

    # Sort JS (vanilla, no framework)
    sort_js = '''
    <script>
    (function() {
        var table = document.getElementById('signals-table');
        if (!table) return;
        var headers = table.querySelectorAll('th[data-sort]');
        headers.forEach(function(th) {
            th.style.cursor = 'pointer';
            th.addEventListener('click', function() {
                var key = th.dataset.sort;
                var tbody = table.querySelector('tbody');
                var rows = Array.from(tbody.querySelectorAll('tr'));
                var asc = th.dataset.dir !== 'asc';
                th.dataset.dir = asc ? 'asc' : 'desc';
                // Reset other headers
                headers.forEach(function(h) { if (h !== th) h.dataset.dir = ''; });
                rows.sort(function(a, b) {
                    var va = parseFloat(a.dataset[key]) || 0;
                    var vb = parseFloat(b.dataset[key]) || 0;
                    return asc ? va - vb : vb - va;
                });
                rows.forEach(function(r) { tbody.appendChild(r); });
            });
        });
    })();
    </script>
    '''

    clusters_section = f'''
    <section style="padding:0 24px 40px;">
        <div class="container" style="max-width:900px;">
            <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;overflow:hidden;">
                <div style="display:flex;align-items:center;justify-content:space-between;padding:20px 24px;border-bottom:1px solid var(--border);">
                    <h2 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin:0;">All Demand Signals</h2>
                    <div style="display:flex;gap:12px;align-items:center;">
                        <a href="/api/demand-export?format=csv" style="font-size:13px;color:var(--ink-muted);text-decoration:none;">CSV</a>
                        <a href="/api/demand-export" style="font-size:13px;color:var(--accent);text-decoration:none;">JSON</a>
                    </div>
                </div>
                <div style="overflow-x:auto;">
                    <table id="signals-table" style="width:100%;border-collapse:collapse;font-size:14px;">
                        <thead>
                            <tr style="border-bottom:2px solid var(--border);background:var(--card-bg);">
                                <th style="padding:12px 16px;text-align:left;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Query</th>
                                <th data-sort="opp" style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Score &#x25BE;</th>
                                <th style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">14d Trend</th>
                                <th style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Competition</th>
                                <th data-sort="zero" style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Failed</th>
                                <th style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Total</th>
                                <th data-sort="last" style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Last Seen</th>
                                <th style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Tier</th>
                            </tr>
                        </thead>
                        <tbody>
                            {cluster_rows if cluster_rows else '<tr><td colspan="8" style="padding:40px;text-align:center;color:var(--ink-muted);">No demand signals yet.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </section>
    {sort_js}
    '''

    # ── Live feed (gaps only by default) ──
    gap_pulse_rows = ''.join(_pulse_event_html(e) for e in gap_events) if gap_events else '''
        <div style="text-align:center;padding:40px 20px;color:var(--ink-muted);">
            <p style="font-size:14px;">No gap events yet.</p>
        </div>'''

    pulse_section = f'''
    <style>
        @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
        .pulse-live-dot {{ display:inline-block;width:8px;height:8px;background:#EF4444;border-radius:50%;animation:blink 1.5s ease-in-out infinite; }}
    </style>
    <section style="padding:0 24px 40px;">
        <div class="container" style="max-width:900px;">
            <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;overflow:hidden;">
                <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;">
                    <span style="font-family:var(--font-display);font-size:17px;color:var(--ink);">
                        <span class="pulse-live-dot" style="margin-right:8px;vertical-align:middle;"></span>
                        Live Gap Feed
                    </span>
                    <span style="font-size:12px;color:var(--ink-muted);font-family:var(--font-mono);">gaps only &mdash; refreshes every 30s</span>
                </div>
                <div id="pulse-events" style="max-height:400px;overflow-y:auto;">
                    {gap_pulse_rows}
                </div>
            </div>
        </div>
    </section>

    <script>
    (function() {{
        setInterval(function() {{
            fetch('/api/pulse?filter=gaps')
                .then(function(r) {{ return r.json(); }})
                .then(function(data) {{
                    if (data.html) document.getElementById('pulse-events').innerHTML = data.html;
                }})
                .catch(function() {{}});
        }}, 30000);
    }})();
    </script>
    '''

    body = hero + stats_bar + insights_section + clusters_section + pulse_section

    return HTMLResponse(page_shell(
        title="Demand Signals Pro Dashboard | IndieStack",
        body=body,
        user=user,
        description="Pro demand signal analytics — opportunity scores, trend sparklines, and competitor density for every gap.",
    ))
```

**Note:** The existing trend chart section (14-day CSS bar chart) is removed — sparklines per signal replace it with more granular data. The stats bar captures the aggregate view.

**Verify:** `python3 -c "import py_compile; py_compile.compile('src/indiestack/routes/gaps.py', doraise=True); print('OK')"`

---

### Task 5: Gaps-only filter on pulse API

**Files:**
- Modify: `src/indiestack/routes/pulse.py` — the `pulse_api()` function at line 70

**What it does:** Adds a `filter=gaps` query parameter support. When present, only returns gap events (type == 'gap'). The pro dashboard polls with this parameter.

**Implementation:**

Replace the `pulse_api` function (lines 70-79) with:

```python
@router.get("/api/pulse")
async def pulse_api(request: Request):
    """JSON endpoint for auto-refresh polling (used by pro dashboard)."""
    db = request.state.db
    events = await get_pulse_feed(db, limit=30)
    filter_type = request.query_params.get('filter', '')
    if filter_type == 'gaps':
        events = [e for e in events if e['type'] == 'gap']
    html = ''.join(_event_html(dict(e)) for e in events) if events else '''
        <div style="text-align:center;padding:40px 20px;color:var(--ink-muted);">
            <p style="font-size:14px;">Waiting for activity...</p>
        </div>'''
    return JSONResponse({"html": html})
```

**Verify:** `python3 -c "import py_compile; py_compile.compile('src/indiestack/routes/pulse.py', doraise=True); print('OK')"`

---

### Task 6: Enhanced CSV/JSON export

**Files:**
- Modify: `src/indiestack/main.py` — the `demand_export()` function at line ~2825

**What it does:** Adds `format=csv` query param support. Both formats now include `opportunity_score` and `competitor_density`. Uses the enriched clusters query.

**Implementation:**

Replace the `demand_export` function with:

```python
@app.get("/api/demand-export")
async def demand_export(request: Request):
    """Export demand clusters as JSON or CSV (pro only)."""
    user = request.state.user
    if not user:
        return JSONResponse({"error": "Login required"}, status_code=401)

    d = request.state.db
    cursor = await d.execute(
        "SELECT id FROM subscriptions WHERE user_id = ? AND status = 'active' AND plan IN ('demand_pro', 'pro')",
        (user['id'],),
    )
    if not await cursor.fetchone():
        return JSONResponse({"error": "Pro subscription required"}, status_code=403)

    from indiestack.db import get_demand_clusters_enriched
    clusters = await get_demand_clusters_enriched(d, limit=100)

    fmt = request.query_params.get('format', 'json')
    if fmt == 'csv':
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['query', 'opportunity_score', 'zero_count', 'search_count', 'competitor_density', 'sources', 'first_searched', 'last_searched'])
        for c in clusters:
            writer.writerow([c['query'], c['opportunity_score'], c['zero_count'], c['search_count'], c['competitor_density'], c.get('sources', ''), c.get('first_searched', ''), c.get('last_searched', '')])
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type='text/csv',
            headers={'Content-Disposition': 'attachment; filename=indiestack-demand-signals.csv'},
        )

    # JSON (default)
    return JSONResponse([
        {
            "query": c['query'],
            "opportunity_score": c['opportunity_score'],
            "zero_count": c['zero_count'],
            "search_count": c['search_count'],
            "competitor_density": c['competitor_density'],
            "sources": c.get('sources', ''),
            "first_searched": c.get('first_searched', ''),
            "last_searched": c.get('last_searched', ''),
        }
        for c in clusters
    ])
```

**Verify:** `python3 -c "import py_compile; py_compile.compile('src/indiestack/main.py', doraise=True); print('OK')"`

---

## Execution

### Parallel agents (3 groups):

**Agent 1:** Task 1 (db.py — enriched query)
**Agent 2:** Tasks 2 + 3 (gaps.py — sparkline + density helpers)
**Agent 3:** Task 5 (pulse.py — gaps filter)

Then sequentially:
**Agent 4:** Task 4 (gaps.py — full dashboard rewrite, depends on Tasks 1-3)
**Agent 5:** Task 6 (main.py — export enhancement)

### Verification
1. Syntax check all 4 files
2. Deploy to Fly.io
3. Visit /demand as logged-in Oat user — verify insight cards, sparklines, density indicators, sortable table, gaps-only feed

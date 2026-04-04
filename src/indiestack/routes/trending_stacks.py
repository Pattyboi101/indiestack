"""Trending Stacks — live data from dependency analyses."""

import datetime
from html import escape
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell

router = APIRouter()


@router.get("/trending-stacks", response_class=HTMLResponse)
async def trending_stacks_page(request: Request):
    user = request.state.user
    d = request.state.db

    # Most common tool pairs from real manifests
    c = await d.execute("""
        SELECT mc.tool_a_slug, mc.tool_b_slug, mc.cooccurrence_count,
               t1.name as name_a, t2.name as name_b
        FROM manifest_cooccurrences mc
        LEFT JOIN tools t1 ON t1.slug = mc.tool_a_slug
        LEFT JOIN tools t2 ON t2.slug = mc.tool_b_slug
        WHERE mc.cooccurrence_count >= 3
          AND mc.tool_a_slug NOT LIKE 'npm-types-%'
          AND mc.tool_b_slug NOT LIKE 'npm-types-%'
          AND mc.tool_a_slug NOT LIKE 'npm-eslint-%'
          AND mc.tool_b_slug NOT LIKE 'npm-eslint-%'
          AND mc.tool_a_slug NOT LIKE 'npm-babel-%'
          AND mc.tool_b_slug NOT LIKE 'npm-babel-%'
        ORDER BY mc.cooccurrence_count DESC
        LIMIT 20
    """)
    top_pairs = await c.fetchall()

    # Total analyses and pairs
    c = await d.execute("SELECT COUNT(*) as cnt FROM dependency_analyses")
    total_analyses = (await c.fetchone())["cnt"]
    c = await d.execute("SELECT COUNT(*) as cnt FROM manifest_cooccurrences")
    total_pairs = (await c.fetchone())["cnt"]

    # Most analyzed tools (hub tools)
    c = await d.execute("""
        SELECT tool_a_slug as slug, SUM(cooccurrence_count) as total
        FROM manifest_cooccurrences
        WHERE tool_a_slug NOT LIKE 'npm-types-%'
          AND tool_a_slug NOT LIKE 'npm-eslint-%'
          AND tool_a_slug NOT LIKE 'npm-babel-%'
        GROUP BY tool_a_slug
        UNION ALL
        SELECT tool_b_slug, SUM(cooccurrence_count)
        FROM manifest_cooccurrences
        WHERE tool_b_slug NOT LIKE 'npm-types-%'
          AND tool_b_slug NOT LIKE 'npm-eslint-%'
          AND tool_b_slug NOT LIKE 'npm-babel-%'
        GROUP BY tool_b_slug
    """)
    rows = await c.fetchall()
    tool_freq = {}
    for r in rows:
        slug = r["slug"] if isinstance(r, dict) else r[0]
        cnt = r["total"] if isinstance(r, dict) else r[1]
        tool_freq[slug] = tool_freq.get(slug, 0) + cnt

    top_tools = sorted(tool_freq.items(), key=lambda x: x[1], reverse=True)[:15]

    # Get names for top tools — track which slugs exist in our DB
    tool_names = {}
    tool_in_db = set()
    for slug, _ in top_tools:
        c = await d.execute("SELECT name FROM tools WHERE slug = ? LIMIT 1", (slug,))
        row = await c.fetchone()
        if row:
            tool_names[slug] = row["name"]
            tool_in_db.add(slug)
        else:
            tool_names[slug] = slug.replace("npm-", "").replace("pypi-", "")

    as_of = datetime.date.today().strftime("%-d %B %Y")

    # Build top tools bar chart
    tools_html = ""
    for slug, freq in top_tools:
        name = tool_names.get(slug, slug)
        bar_width = min(100, int((freq / top_tools[0][1]) * 100))
        escaped_name = escape(name)
        escaped_slug = escape(slug)
        if slug in tool_in_db:
            name_cell = f'<a href="/tools/{escaped_slug}" style="font-family:var(--font-mono);font-size:var(--text-sm);min-width:140px;color:var(--ink);text-decoration:none;" aria-label="View {escaped_name} on IndieStack">{escaped_name}</a>'
        else:
            name_cell = f'<span style="font-family:var(--font-mono);font-size:var(--text-sm);min-width:140px;color:var(--ink);">{escaped_name}</span>'
        tools_html += f'''<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">
            {name_cell}
            <div style="flex:1;height:20px;background:var(--cream-dark);border-radius:4px;overflow:hidden;">
                <div style="width:{bar_width}%;height:100%;background:var(--accent);border-radius:4px;"></div>
            </div>
            <span style="font-size:var(--text-xs);color:var(--ink-muted);min-width:40px;text-align:right;">{freq}</span>
        </div>'''

    # Build pairs table
    pairs_html = ""
    for i, p in enumerate(top_pairs):
        raw_name_a = p["name_a"] if isinstance(p, dict) else p[3]
        raw_name_b = p["name_b"] if isinstance(p, dict) else p[4]
        slug_a = p["tool_a_slug"] if isinstance(p, dict) else p[0]
        slug_b = p["tool_b_slug"] if isinstance(p, dict) else p[1]
        count = p["cooccurrence_count"] if isinstance(p, dict) else p[2]

        name_a = raw_name_a or slug_a.replace("npm-", "").replace("pypi-", "")
        name_b = raw_name_b or slug_b.replace("npm-", "").replace("pypi-", "")

        escaped_name_a = escape(name_a)
        escaped_name_b = escape(name_b)
        escaped_slug_a = escape(slug_a)
        escaped_slug_b = escape(slug_b)

        # Only link if the tool exists in our DB (JOIN succeeded)
        if raw_name_a:
            cell_a = f'<a href="/tools/{escaped_slug_a}" style="color:var(--ink);text-decoration:none;font-weight:500;" aria-label="View {escaped_name_a}">{escaped_name_a}</a>'
        else:
            cell_a = escaped_name_a

        if raw_name_b:
            cell_b = f'<a href="/tools/{escaped_slug_b}" style="color:var(--ink);text-decoration:none;font-weight:500;" aria-label="View {escaped_name_b}">{escaped_name_b}</a>'
        else:
            cell_b = escaped_name_b

        row_border = "border-top:1px solid var(--border);" if i > 0 else ""
        pairs_html += f'''<tr style="{row_border}" class="hover-highlight">
            <td style="padding:12px 16px;font-family:var(--font-mono);font-size:var(--text-sm);">{cell_a}</td>
            <td style="padding:12px 8px;color:var(--ink-muted);font-size:var(--text-lg);">+</td>
            <td style="padding:12px 16px;font-family:var(--font-mono);font-size:var(--text-sm);">{cell_b}</td>
            <td style="padding:12px 16px;text-align:right;color:var(--ink-muted);font-size:var(--text-sm);white-space:nowrap;">{count:,}&times;</td>
        </tr>'''

    body = f'''
    <div style="max-width:800px;margin:0 auto;padding:0 16px;">
        <div style="text-align:center;padding:32px 0 24px;">
            <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);color:var(--ink);margin:0 0 8px;">
                Trending Stacks
            </h1>
            <p style="color:var(--ink-muted);font-size:var(--text-md);margin:0 0 4px;">
                All-time most common tool combinations from {total_analyses:,} real dependency files.
            </p>
            <p style="color:var(--ink-light);font-size:var(--text-sm);margin:0;">
                {total_pairs:,} compatibility pairs tracked &middot; as of {as_of}
            </p>
        </div>

        <!-- Most used tools -->
        <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-lg);padding:24px;margin-bottom:24px;">
            <h2 style="font-family:var(--font-display);font-size:var(--text-lg);color:var(--ink);margin:0 0 16px;">
                Most Common Dependencies
            </h2>
            {tools_html}
        </div>

        <!-- Top pairs -->
        <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;margin-bottom:24px;">
            <div style="padding:16px 24px;border-bottom:1px solid var(--border);">
                <h2 style="font-family:var(--font-display);font-size:var(--text-lg);color:var(--ink);margin:0;">
                    Most Common Pairs
                </h2>
                <p style="font-size:var(--text-sm);color:var(--ink-muted);margin:4px 0 0;">
                    Tools that appear together in real package.json and requirements.txt files
                </p>
            </div>
            <table style="width:100%;border-collapse:collapse;">
                <tbody>
                    {pairs_html}
                </tbody>
            </table>
        </div>

        <!-- CTA -->
        <div style="text-align:center;padding:24px;background:var(--cream-dark);border-radius:var(--radius-lg);margin-bottom:32px;">
            <p style="font-family:var(--font-body);color:var(--ink);margin:0 0 12px;">
                Check how your stack compares
            </p>
            <a href="/analyze" class="btn-primary" style="padding:12px 24px;text-decoration:none;">
                Analyze your dependencies
            </a>
        </div>
    </div>'''

    return HTMLResponse(page_shell(
        "Trending Stacks | IndieStack",
        body,
        description=f"All-time most common tool combinations from {total_analyses:,} real dependency files. {total_pairs:,} compatibility pairs tracked.",
        user=user,
    ))

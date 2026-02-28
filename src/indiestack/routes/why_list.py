"""Why List Your Tool on IndieStack — factual page for makers and agents."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell

router = APIRouter()


@router.get("/why-list", response_class=HTMLResponse)
async def why_list_page(request: Request):
    user = request.state.user
    db = request.state.db

    # Pull real stats
    _tc = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")
    tool_count = (await _tc.fetchone())['cnt']
    _mc = await db.execute("SELECT COUNT(*) as cnt FROM makers")
    maker_count = (await _mc.fetchone())['cnt']
    _cc = await db.execute("SELECT COUNT(*) as cnt FROM categories")
    cat_count = (await _cc.fetchone())['cnt']
    _mcp = await db.execute("SELECT COALESCE(SUM(mcp_view_count), 0) as cnt FROM tools")
    mcp_views = (await _mcp.fetchone())['cnt']
    _clicks = await db.execute("SELECT COUNT(*) as cnt FROM outbound_clicks WHERE created_at >= datetime('now', '-30 days')")
    clicks_30d = (await _clicks.fetchone())['cnt']
    _searches = await db.execute("SELECT COUNT(*) as cnt FROM search_logs WHERE created_at >= datetime('now', '-7 days')")
    searches_week = (await _searches.fetchone())['cnt']

    # Notable tools — grab a few verified or high-click tools
    _notable = await db.execute("""
        SELECT t.name, t.slug FROM tools t
        WHERE t.status='approved' AND (t.is_verified=1 OR t.mcp_view_count > 5)
        ORDER BY t.mcp_view_count DESC LIMIT 8
    """)
    notable_tools = [dict(r) for r in await _notable.fetchall()]
    notable_html = ', '.join(
        f'<a href="/tool/{escape(t["slug"])}" style="color:var(--accent);text-decoration:none;font-weight:600;">{escape(t["name"])}</a>'
        for t in notable_tools
    ) if notable_tools else f'{tool_count} indie tools and growing'

    body = f'''
    <div style="max-width:720px;margin:0 auto;padding:64px 24px;">

        <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);line-height:1.2;margin-bottom:8px;">
            Why List Your Tool on IndieStack
        </h1>
        <p style="font-size:18px;color:var(--ink-muted);line-height:1.6;margin-bottom:48px;">
            A curated catalog of {tool_count} indie tools, searchable by AI agents and humans alike. Here's what you get.
        </p>

        <!-- Stat cards -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(140px, 1fr));gap:16px;margin-bottom:48px;">
            <div class="card" style="padding:20px;text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--ink);">{tool_count}</div>
                <div style="font-size:13px;color:var(--ink-muted);">curated tools</div>
            </div>
            <div class="card" style="padding:20px;text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--ink);">{cat_count}</div>
                <div style="font-size:13px;color:var(--ink-muted);">categories</div>
            </div>
            <div class="card" style="padding:20px;text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{mcp_views}</div>
                <div style="font-size:13px;color:var(--ink-muted);">AI agent lookups</div>
            </div>
            <div class="card" style="padding:20px;text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--ink);">{clicks_30d}</div>
                <div style="font-size:13px;color:var(--ink-muted);">clicks to tools (30d)</div>
            </div>
        </div>

        <!-- Section 1: AI Agent Discovery -->
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                &#129302; Your tool shows up in AI conversations
            </h2>
            <p style="color:var(--ink-light);line-height:1.7;">
                IndieStack has an <a href="https://pypi.org/project/indiestack/" style="color:var(--accent);">MCP server on PyPI</a>
                and the <a href="https://registry.modelcontextprotocol.io/" style="color:var(--accent);">official MCP Registry</a>.
                When developers install it in Claude, Cursor, or Windsurf, their AI assistant searches our catalog
                before writing code from scratch. Your tool gets recommended in the conversation &mdash; not buried on page 3 of a directory.
            </p>
            <div class="card" style="padding:16px 20px;margin-top:12px;font-size:14px;color:var(--ink-light);background:var(--cream);">
                <strong>{mcp_views} AI agent lookups</strong> so far &mdash; and growing weekly as more developers install the MCP server.
            </div>
        </div>

        <!-- Section 2: What you get -->
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                &#9889; What you get (free)
            </h2>
            <ul style="color:var(--ink-light);line-height:2;padding-left:20px;">
                <li><strong>Tool profile page</strong> &mdash; description, tags, screenshots, changelog, reviews</li>
                <li><strong>AI agent discoverability</strong> &mdash; your tool appears in MCP search results</li>
                <li><strong>SEO pages</strong> &mdash; alternatives pages, use-case comparisons, category listings</li>
                <li><strong>Outbound click tracking</strong> &mdash; see how many developers click through to your site</li>
                <li><strong>Embeddable badge</strong> &mdash; "Listed on IndieStack" SVG for your README</li>
                <li><strong>Maker profile</strong> &mdash; showcase all your tools in one place</li>
                <li><strong>Vibe Stacks</strong> &mdash; get included in curated tool bundles</li>
                <li><strong>Changelog updates</strong> &mdash; post updates that show on the IndieStack feed</li>
            </ul>
        </div>

        <!-- Section 3: Who's already here -->
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                &#128100; Who&rsquo;s already here
            </h2>
            <p style="color:var(--ink-light);line-height:1.7;">
                {notable_html}, and {maker_count} makers total.
                Every tool is reviewed by a human before it goes live &mdash; no spam, no abandoned projects.
            </p>
        </div>

        <!-- Section 4: How it works -->
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                &#128295; How to list your tool
            </h2>
            <div style="display:flex;flex-direction:column;gap:16px;">
                <div style="display:flex;gap:16px;align-items:flex-start;">
                    <div style="min-width:32px;height:32px;border-radius:50%;background:var(--accent);color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;">1</div>
                    <div>
                        <strong style="color:var(--ink);">Submit your tool</strong>
                        <p style="color:var(--ink-light);margin:4px 0 0;font-size:14px;">Fill out the form at <a href="/submit" style="color:var(--accent);">/submit</a>. Takes 2 minutes.</p>
                    </div>
                </div>
                <div style="display:flex;gap:16px;align-items:flex-start;">
                    <div style="min-width:32px;height:32px;border-radius:50%;background:var(--accent);color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;">2</div>
                    <div>
                        <strong style="color:var(--ink);">We review it</strong>
                        <p style="color:var(--ink-light);margin:4px 0 0;font-size:14px;">Every tool is manually reviewed. We check it&rsquo;s real, indie, and actively maintained.</p>
                    </div>
                </div>
                <div style="display:flex;gap:16px;align-items:flex-start;">
                    <div style="min-width:32px;height:32px;border-radius:50%;background:var(--accent);color:white;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:14px;">3</div>
                    <div>
                        <strong style="color:var(--ink);">You&rsquo;re live</strong>
                        <p style="color:var(--ink-light);margin:4px 0 0;font-size:14px;">Your tool appears on the site, in search, in AI agent results, and on relevant alternatives pages.</p>
                    </div>
                </div>
            </div>
        </div>

        <!-- Section 5: Real activity -->
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                &#128200; Real activity this week
            </h2>
            <p style="color:var(--ink-light);line-height:1.7;">
                {searches_week} searches in the last 7 days. {clicks_30d} outbound clicks to tool websites in the last 30 days.
                These are real developers finding tools &mdash; not bot traffic.
            </p>
        </div>

        <!-- CTA -->
        <div style="text-align:center;padding:40px 0;border-top:1px solid var(--border);margin-top:16px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">
                List your tool for free
            </h2>
            <p style="color:var(--ink-muted);margin-bottom:24px;font-size:15px;">
                Takes 2 minutes. No payment required.
            </p>
            <a href="/submit" class="btn btn-lg btn-primary" style="font-size:16px;padding:14px 32px;">
                Submit Your Tool &rarr;
            </a>
        </div>

    </div>
    '''

    # JSON-LD for agents
    json_ld = f'''<script type="application/ld+json">{{
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "Why List Your Tool on IndieStack",
        "description": "IndieStack is a curated catalog of {tool_count} indie tools searchable by AI agents via MCP. Free to list.",
        "url": "{BASE_URL}/why-list",
        "mainEntity": {{
            "@type": "Organization",
            "name": "IndieStack",
            "url": "{BASE_URL}",
            "description": "Curated indie tool catalog with AI agent discovery via MCP server"
        }}
    }}</script>'''

    return HTMLResponse(page_shell(
        "Why List Your Tool on IndieStack",
        body,
        user=user,
        description=f"IndieStack is a curated catalog of {tool_count} indie tools searchable by AI agents. Free to list. {mcp_views} AI agent lookups and counting.",
        extra_head=json_ld,
        canonical="/why-list",
    ))

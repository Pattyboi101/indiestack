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

    # Notable tools — grab a few high-activity tools
    _notable = await db.execute("""
        SELECT t.name, t.slug FROM tools t
        WHERE t.status='approved' AND t.mcp_view_count > 5
        ORDER BY t.mcp_view_count DESC LIMIT 8
    """)
    notable_tools = [dict(r) for r in await _notable.fetchall()]
    notable_html = ', '.join(
        f'<a href="/tool/{escape(t["slug"])}" style="color:var(--accent);text-decoration:none;font-weight:600;">{escape(t["name"])}</a>'
        for t in notable_tools
    ) if notable_tools else f'{tool_count} developer tools and growing'

    body = f'''
    <div style="max-width:720px;margin:0 auto;padding:64px 24px;">

        <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);line-height:1.2;margin-bottom:8px;">
            Why List on IndieStack
        </h1>
        <p style="font-size:18px;color:var(--ink-muted);line-height:1.6;margin-bottom:48px;">
            A curated catalog of {tool_count} developer tools, searchable by AI agents and humans alike. Here's what you get.
        </p>

        <!-- Stat cards -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(140px, 1fr));gap:16px;margin-bottom:48px;">
            <div class="card" style="padding:24px;text-align:center;cursor:default;transition:all 0.2s ease;"
                 onmouseenter="this.style.transform='translateY(-2px)';this.style.boxShadow='var(--shadow-md)';this.style.borderColor='rgba(255,255,255,0.15)'"
                 onmouseleave="this.style.transform='';this.style.boxShadow='';this.style.borderColor=''">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--ink);">{tool_count}</div>
                <div style="font-size:13px;color:var(--ink-muted);">curated tools</div>
            </div>
            <div class="card" style="padding:24px;text-align:center;cursor:default;transition:all 0.2s ease;"
                 onmouseenter="this.style.transform='translateY(-2px)';this.style.boxShadow='var(--shadow-md)';this.style.borderColor='rgba(255,255,255,0.15)'"
                 onmouseleave="this.style.transform='';this.style.boxShadow='';this.style.borderColor=''">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--ink);">{cat_count}</div>
                <div style="font-size:13px;color:var(--ink-muted);">categories</div>
            </div>
            <div class="card" style="padding:24px;text-align:center;cursor:default;transition:all 0.2s ease;"
                 onmouseenter="this.style.transform='translateY(-2px)';this.style.boxShadow='var(--shadow-md)';this.style.borderColor='rgba(255,255,255,0.15)'"
                 onmouseleave="this.style.transform='';this.style.boxShadow='';this.style.borderColor=''">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{mcp_views}</div>
                <div style="font-size:13px;color:var(--ink-muted);">AI agent lookups</div>
            </div>
            <div class="card" style="padding:24px;text-align:center;cursor:default;transition:all 0.2s ease;"
                 onmouseenter="this.style.transform='translateY(-2px)';this.style.boxShadow='var(--shadow-md)';this.style.borderColor='rgba(255,255,255,0.15)'"
                 onmouseleave="this.style.transform='';this.style.boxShadow='';this.style.borderColor=''">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--ink);">{clicks_30d}</div>
                <div style="font-size:13px;color:var(--ink-muted);">outbound clicks (30d)</div>
            </div>
        </div>

        <!-- Section 1: AI Agent Discovery -->
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M12 2a4 4 0 0 0-4 4v2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V10a2 2 0 0 0-2-2h-2V6a4 4 0 0 0-4-4z"/><circle cx="12" cy="14" r="2"/></svg> AI agents recommend your tool directly
            </h2>
            <p style="color:var(--ink-light);line-height:1.7;">
                IndieStack&rsquo;s <a href="https://pypi.org/project/indiestack/" style="color:var(--accent);">MCP server</a> has
                <strong style="color:var(--ink);">10,000+ installs</strong> on PyPI and is listed on the
                <a href="https://registry.modelcontextprotocol.io/" style="color:var(--accent);">official MCP Registry</a>.
                When developers ask Claude, Cursor, or Windsurf &ldquo;what should I use for payments?&rdquo; &mdash;
                IndieStack is consulted. Your tool shows up in the AI&rsquo;s answer, not buried on a search results page.
            </p>
            <div class="card" style="padding:16px 20px;margin-top:12px;font-size:14px;color:var(--ink-light);background:var(--cream);">
                <strong>{mcp_views:,} AI agent lookups</strong> logged so far &mdash; growing weekly as MCP adoption accelerates across AI coding tools.
            </div>
        </div>

        <!-- Section 1b: Maker Pro -->
        <div style="margin-bottom:40px;padding:24px;border:1px solid var(--accent);border-radius:12px;background:rgba(0,212,245,0.04);">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
                <span style="background:var(--accent);color:#0a0a0a;font-size:11px;font-weight:700;padding:3px 8px;border-radius:999px;letter-spacing:0.05em;">MAKER PRO</span>
                <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin:0;">See exactly where your tool gets recommended</h2>
            </div>
            <p style="color:var(--ink-light);line-height:1.7;margin-bottom:16px;">
                Maker Pro ($19/mo) gives you a live dashboard showing how AI agents find and recommend your tool:
                which queries trigger it, how often it&rsquo;s the top result, and what developers are searching for
                when they land on your listing.
            </p>
            <ul style="color:var(--ink-light);line-height:2.0;padding-left:0;list-style:none;margin-bottom:16px;">
                <li style="position:relative;padding-left:24px;"><span style="position:absolute;left:0;color:var(--accent);font-weight:700;">&mdash;</span><strong>Agent citation analytics</strong> &mdash; how many AI sessions recommended your tool</li>
                <li style="position:relative;padding-left:24px;"><span style="position:absolute;left:0;color:var(--accent);font-weight:700;">&mdash;</span><strong>Search query data</strong> &mdash; what developers were searching for when they found you</li>
                <li style="position:relative;padding-left:24px;"><span style="position:absolute;left:0;color:var(--accent);font-weight:700;">&mdash;</span><strong>Verified badge</strong> &mdash; signals to agents that you&rsquo;re an active, claimed maker</li>
                <li style="position:relative;padding-left:24px;"><span style="position:absolute;left:0;color:var(--accent);font-weight:700;">&mdash;</span><strong>Priority placement</strong> &mdash; boosted ranking in search and agent results</li>
            </ul>
            <a href="/pricing" style="color:var(--accent);font-weight:600;font-size:14px;">See Maker Pro &rarr;</a>
        </div>

        <!-- Section 2: What you get -->
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-2px;"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg> What you get (free)
            </h2>
            <ul style="color:var(--ink-light);line-height:2.2;padding-left:0;list-style:none;">
                <li style="position:relative;padding-left:24px;"><span style="position:absolute;left:0;color:var(--accent);font-weight:700;">&mdash;</span><strong>Profile page</strong> &mdash; description, tags, screenshots, changelog, reviews</li>
                <li style="position:relative;padding-left:24px;"><span style="position:absolute;left:0;color:var(--accent);font-weight:700;">&mdash;</span><strong>AI agent discoverability</strong> &mdash; your tool appears in MCP search results</li>
                <li style="position:relative;padding-left:24px;"><span style="position:absolute;left:0;color:var(--accent);font-weight:700;">&mdash;</span><strong>SEO pages</strong> &mdash; alternatives pages, use-case comparisons, category listings</li>
                <li style="position:relative;padding-left:24px;"><span style="position:absolute;left:0;color:var(--accent);font-weight:700;">&mdash;</span><strong>Outbound click tracking</strong> &mdash; see how many developers click through to your site</li>
                <li style="position:relative;padding-left:24px;"><span style="position:absolute;left:0;color:var(--accent);font-weight:700;">&mdash;</span><strong>Embeddable badge</strong> &mdash; "Listed on IndieStack" SVG for your README</li>
                <li style="position:relative;padding-left:24px;"><span style="position:absolute;left:0;color:var(--accent);font-weight:700;">&mdash;</span><strong>Maker profile</strong> &mdash; showcase all your tools in one place</li>
                <li style="position:relative;padding-left:24px;"><span style="position:absolute;left:0;color:var(--accent);font-weight:700;">&mdash;</span><strong>Vibe Stacks</strong> &mdash; get included in curated bundles</li>
                <li style="position:relative;padding-left:24px;"><span style="position:absolute;left:0;color:var(--accent);font-weight:700;">&mdash;</span><strong>Changelog updates</strong> &mdash; post updates that show on the IndieStack feed</li>
            </ul>
        </div>

        <!-- Section 3: Who's already here -->
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg> Who&rsquo;s already here
            </h2>
            <p style="color:var(--ink-light);line-height:1.7;">
                {notable_html}, and {maker_count} makers total.
                Every submission is reviewed by a human before it goes live &mdash; no spam, no abandoned projects.
            </p>
        </div>

        <!-- Section 4: How it works -->
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg> How to list your tool
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
                        <p style="color:var(--ink-light);margin:4px 0 0;font-size:14px;">Every submission is manually reviewed. We check it&rsquo;s real, indie, and actively maintained.</p>
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
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg> Real activity this week
            </h2>
            <p style="color:var(--ink-light);line-height:1.7;">
                {searches_week} searches in the last 7 days. {clicks_30d} outbound clicks in the last 30 days.
                These are real people finding tools &mdash; not bot traffic.
            </p>
        </div>

        <!-- CTA -->
        <div style="text-align:center;padding:40px 0;border-top:1px solid var(--border);margin-top:16px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:16px;">
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
        "name": "Why List on IndieStack",
        "description": "IndieStack is a curated catalog of {tool_count} developer tools searchable by AI agents via MCP server (10,000+ installs). Free to list. Maker Pro analytics from $19/mo.",
        "url": "{BASE_URL}/why-list",
        "mainEntity": {{
            "@type": "Organization",
            "name": "IndieStack",
            "url": "{BASE_URL}",
            "description": "Curated indie catalog with AI agent discovery via MCP server"
        }}
    }}</script>'''

    return HTMLResponse(page_shell(
        "Why List on IndieStack",
        body,
        user=user,
        description=f"IndieStack's MCP server has 10,000+ installs. AI agents recommend your tool in real developer conversations. Free to list. Maker Pro from $19/mo.",
        extra_head=json_ld,
        canonical="/why-list",
    ))

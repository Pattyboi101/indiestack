"""Landing page — AI tool discovery layer, trending tools, category grid."""

import time as _time
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card, featured_card, update_card, stack_card
from indiestack.db import get_all_categories, get_trending_tools, get_featured_tool, get_recent_tools, get_all_collections, get_recent_updates, get_platform_tokens_saved, get_all_stacks, get_recent_activity, get_trending_scored

router = APIRouter()

# Landing page cache — avoids repeated DB queries on every homepage load
_landing_cache: dict = {
    'data': None,
    'expires': 0,
}


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    db = request.state.db

    if _landing_cache['data'] and _time.time() < _landing_cache['expires']:
        cached = _landing_cache['data']
        tool_count = cached['tool_count']
        cat_count = cached['cat_count']
        maker_count = cached['maker_count']
        sales_count = cached['sales_count']
        trending = cached['trending']
        categories = cached['categories']
        featured = cached['featured']
        recent = cached['recent']
        collections = cached['collections']
        recent_updates = cached['recent_updates']
        tokens_saved = cached['tokens_saved']
        activities = cached['activities']
        stacks_list = cached['stacks_list']
    else:
        _tc = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")
        tool_count = (await _tc.fetchone())['cnt']
        _cc = await db.execute("SELECT COUNT(*) as cnt FROM categories")
        cat_count = (await _cc.fetchone())['cnt']
        _mc = await db.execute("SELECT COUNT(*) as cnt FROM makers")
        maker_count = (await _mc.fetchone())['cnt']
        # Monthly sales count
        _sc = await db.execute("SELECT COUNT(*) as cnt FROM purchases WHERE created_at > datetime('now', '-30 days')")
        sales_count = (await _sc.fetchone())['cnt']
        trending = await get_trending_scored(db, limit=6, days=7)
        categories = await get_all_categories(db)
        featured = await get_featured_tool(db)
        recent = await get_recent_tools(db, limit=3, days=7)
        collections = await get_all_collections(db)
        recent_updates = await get_recent_updates(db, limit=3)
        tokens_saved = await get_platform_tokens_saved(db)
        activities = await get_recent_activity(db, limit=8, days=7)
        stacks_list = await get_all_stacks(db)

        _landing_cache['data'] = {
            'tool_count': tool_count,
            'cat_count': cat_count,
            'maker_count': maker_count,
            'sales_count': sales_count,
            'trending': trending,
            'categories': categories,
            'featured': featured,
            'recent': recent,
            'collections': collections,
            'recent_updates': recent_updates,
            'tokens_saved': tokens_saved,
            'activities': activities,
            'stacks_list': stacks_list,
        }
        _landing_cache['expires'] = _time.time() + 300  # 5 minutes

    # ── Hero ──────────────────────────────────────────────────────────
    _tokens_pill = ('<span style="color:var(--border);">|</span><span>~' + str(tokens_saved // 1000) + 'k tokens saved by devs</span>') if tokens_saved > 0 else ''
    hero = (
        '<section style="text-align:center;padding:64px 24px 56px;'
        '                background:var(--cream);">'
        '    <h1 style="font-family:var(--font-display);font-size:clamp(32px,5vw,52px);'
        '               line-height:1.15;max-width:700px;margin:0 auto;color:var(--ink);">'
        '        <span style="background:linear-gradient(135deg, #00D4F5 0%, #fff 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">Your AI is writing code you don&rsquo;t need.</span>'
        '    </h1>'
        '    <p style="font-size:19px;color:var(--ink-muted);max-width:540px;margin:16px auto 32px;line-height:1.6;">'
        '        IndieStack plugs into your AI editor. Before it writes code, it checks if an indie tool already does it.'
        '    </p>'
        # Hero visual — code conversation block
        '    <div class="hero-glow">'
        '    <div style="max-width:560px;margin:0 auto 28px;text-align:left;background:#0D1B2A;border-radius:var(--radius);'
        '                padding:28px 28px;font-family:var(--font-mono);font-size:15px;line-height:1.9;'
        '                box-shadow:0 8px 32px rgba(0,0,0,0.3);position:relative;z-index:1;overflow:hidden;">'
        '        <div style="position:absolute;top:14px;left:16px;display:flex;gap:6px;">'
        '            <span style="width:10px;height:10px;border-radius:50%;background:#FF5F56;display:inline-block;"></span>'
        '            <span style="width:10px;height:10px;border-radius:50%;background:#FFBD2E;display:inline-block;"></span>'
        '            <span style="width:10px;height:10px;border-radius:50%;background:#27C93F;display:inline-block;"></span>'
        '        </div>'
        '        <div style="margin-top:18px;">'
        '            <span style="color:#FFBD2E;font-weight:700;">You:</span>'
        '            <span style="color:#FFFFFF;"> &ldquo;Build me an analytics dashboard&rdquo;</span><br><br>'
        '            <span style="color:#00D4F5;font-weight:700;">AI: </span>'
        '            <span style="color:#E0E0E0;"> &ldquo;Before I write ~50k tokens of code, I found</span><br>'
        '            <span style="color:#E0E0E0;">&#160;&#160;&#160;&#160;&#160;</span>'
        '            <span style="color:#00D4F5;font-weight:700;">Simple Analytics</span>'
        '            <span style="color:#E0E0E0;"> on IndieStack &mdash; privacy-first,</span><br>'
        '            <span style="color:#E0E0E0;">&#160;&#160;&#160;&#160;&#160;2-line install. Use it instead?&rdquo;</span>'
        '        </div>'
        '    </div>'
        '    </div>'
        # CTAs
        '    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:24px;">'
        '        <a href="#mcp-install" class="btn btn-primary" style="padding:14px 28px;font-size:16px;">'
        '            Install the MCP Server'
        '        </a>'
        '        <a href="/stacks/generator" class="btn btn-secondary" style="padding:14px 28px;font-size:16px;">'
        '            Paste your package.json'
        '        </a>'
        '    </div>'
        # Stats pills
        f'    <div style="display:inline-flex;flex-wrap:wrap;gap:8px 16px;justify-content:center;background:var(--card-bg);border:1px solid var(--border);'
        f'                border-radius:var(--radius-sm);padding:10px 28px;font-size:14px;color:var(--ink-light);'
        f'                box-shadow:0 1px 3px rgba(26,45,74,0.06);">'
        f'        <span>{tool_count} curated tools</span>'
        f'        <span style="color:var(--border);">|</span>'
        f'        <span>{cat_count} categories</span>'
        f'        <span style="color:var(--border);">|</span>'
        f'        <span>{"Hand-picked by humans" if maker_count < 5 else str(maker_count) + " makers"}</span>'
        f'{_tokens_pill}'
        f'    </div>'
        '</section>'
    )

    # ── Works with AI Tools (MCP) — directly below hero ───────────────
    mcp_section = """
    <section id="mcp-install" style="padding:48px 24px;background:var(--cream-dark);">
        <div class="container">
            <h2 style="font-family:var(--font-display);font-size:28px;text-align:center;margin-bottom:12px;color:var(--ink);">
                Works with your AI tools
            </h2>
            <p style="text-align:center;color:var(--ink-muted);font-size:16px;margin-bottom:40px;max-width:560px;margin-left:auto;margin-right:auto;">
                Install the IndieStack MCP server and your AI coding tool will search IndieStack
                before building from scratch. Save tokens, ship faster.
            </p>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:24px;max-width:700px;margin:0 auto 40px;">
                <div class="card" style="padding:24px;border-left:3px solid #00D4F5;">
                    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:8px;">Claude Code</h3>
                    <code style="font-family:var(--font-mono);font-size:12px;color:var(--ink-muted);">claude mcp add indiestack</code>
                </div>
                <div class="card" style="padding:24px;border-left:3px solid #00D4F5;">
                    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:8px;">Cursor</h3>
                    <code style="font-family:var(--font-mono);font-size:12px;color:var(--ink-muted);">pip install indiestack</code>
                </div>
                <div class="card" style="padding:24px;border-left:3px solid #00D4F5;">
                    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:8px;">Windsurf</h3>
                    <code style="font-family:var(--font-mono);font-size:12px;color:var(--ink-muted);">pip install indiestack</code>
                </div>
            </div>
            <div style="max-width:600px;margin:0 auto;">
                <p style="font-size:14px;font-weight:600;color:var(--ink);margin-bottom:8px;">Quick install:</p>
                <div style="background:var(--ink);color:var(--slate);border-radius:var(--radius-sm);padding:16px 20px;
                            font-family:var(--font-mono);font-size:13px;line-height:1.8;overflow-x:auto;">
                    <span style="color:var(--ink-muted);"># Install the MCP server</span><br>
                    pip install indiestack<br><br>
                    <span style="color:var(--ink-muted);"># Add to your Claude Code config</span><br>
                    claude mcp add indiestack -- python -m indiestack.mcp_server
                </div>
                <p style="font-size:13px;color:var(--ink-muted);margin-top:12px;">
                    When you ask your AI to &ldquo;build invoicing&rdquo;, it checks IndieStack first:
                    <em>&ldquo;Before you spend 50k tokens, there&rsquo;s InvoiceNinja on IndieStack for &pound;9.&rdquo;</em>
                </p>
            </div>
        </div>
    </section>
    """

    # ── Live Fire Ticker ──────────────────────────────────────
    ticker_html = ''
    if activities:
        ticker_items = ' &nbsp;&middot;&nbsp; '.join(
            f'<span style="white-space:nowrap;">&ndash; {a["message"]}</span>'
            for a in activities
        )
        # Double the items for seamless loop
        ticker_html = f'''
        <div style="overflow:hidden;background:var(--cream-dark);border-bottom:1px solid var(--border);padding:10px 0;">
            <div style="display:flex;animation:ticker 30s linear infinite;width:max-content;">
                <div style="display:flex;gap:0;font-size:13px;color:var(--ink-light);font-weight:500;">
                    {ticker_items} &nbsp;&middot;&nbsp; {ticker_items}
                </div>
            </div>
        </div>
        <style>
            @keyframes ticker {{
                0% {{ transform: translateX(0); }}
                100% {{ transform: translateX(-50%); }}
            }}
        </style>
        '''

    # ── Package.json Analyzer CTA ─────────────────────────────────────
    pkg_json_cta = """
    <section class="container" style="padding:48px 24px;">
        <div class="card" style="text-align:center;padding:40px 32px;border-left:3px solid #00D4F5;background:var(--cream);">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
                Already have a project?
            </h2>
            <p style="color:var(--ink-muted);font-size:16px;max-width:480px;margin:0 auto 20px;line-height:1.6;">
                Paste your package.json and see what you&rsquo;re rebuilding.
                We&rsquo;ll show you indie tools that replace your DIY code.
            </p>
            <a href="/stacks/generator" class="btn btn-primary" style="padding:12px 28px;font-size:16px;">
                Analyze Your Stack
            </a>
        </div>
    </section>
    """

    # ── Discover Tools — tabbed section (Trending / New / Featured) ────
    # Tab JS for switching panels
    tab_js = """
    <script>
    function switchTab(tabName) {
        document.querySelectorAll('.discover-panel').forEach(p => p.style.display = 'none');
        document.querySelectorAll('.discover-tab').forEach(t => {
            t.style.borderBottom = '2px solid transparent';
            t.style.color = 'var(--ink-muted)';
        });
        document.getElementById('panel-' + tabName).style.display = 'block';
        var active = document.getElementById('tab-' + tabName);
        active.style.borderBottom = '2px solid var(--ink)';
        active.style.color = 'var(--ink)';
    }
    </script>
    """

    # Build tab content
    trending_cards = "\n".join(tool_card(t) for t in trending) if trending else ''
    new_cards = "\n".join(tool_card(t) for t in recent) if recent else ''
    featured_block = featured_card(featured) if featured else ''

    # Determine default tab
    default_tab = 'trending' if trending else ('new' if recent else 'featured')

    tab_style = 'font-family:var(--font-display);font-size:16px;padding:8px 16px;cursor:pointer;border:none;background:none;'
    active_tab_style = tab_style + 'border-bottom:2px solid var(--ink);color:var(--ink);'
    inactive_tab_style = tab_style + 'border-bottom:2px solid transparent;color:var(--ink-muted);'

    # Only build tabs that have content
    tabs_html = '<div style="display:flex;gap:4px;border-bottom:1px solid var(--border);margin-bottom:24px;">'
    if trending:
        s = active_tab_style if default_tab == 'trending' else inactive_tab_style
        tabs_html += f'<button id="tab-trending" class="discover-tab" style="{s}" onclick="switchTab(\'trending\')">Trending</button>'
    if recent:
        s = active_tab_style if default_tab == 'new' else inactive_tab_style
        tabs_html += f'<button id="tab-new" class="discover-tab" style="{s}" onclick="switchTab(\'new\')">New This Week</button>'
    if featured:
        s = active_tab_style if default_tab == 'featured' else inactive_tab_style
        tabs_html += f'<button id="tab-featured" class="discover-tab" style="{s}" onclick="switchTab(\'featured\')">Tool of the Week</button>'
    tabs_html += '</div>'

    panels_html = ''
    if trending:
        d = 'block' if default_tab == 'trending' else 'none'
        panels_html += f'<div id="panel-trending" class="discover-panel" style="display:{d};"><div class="scroll-row">{trending_cards}</div></div>'
    if recent:
        d = 'block' if default_tab == 'new' else 'none'
        panels_html += f'<div id="panel-new" class="discover-panel" style="display:{d};"><div class="scroll-row">{new_cards}</div></div>'
    if featured:
        d = 'block' if default_tab == 'featured' else 'none'
        panels_html += f'<div id="panel-featured" class="discover-panel" style="display:{d};">{featured_block}</div>'

    has_any_tools = bool(trending or recent or featured)
    if has_any_tools:
        discover_section = f"""
        <section class="container" style="padding:48px 24px;">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:0;">
                <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">Discover Tools</h2>
                <a href="/explore" style="color:var(--terracotta);font-size:14px;font-weight:600;text-decoration:none;">
                    Browse all
                </a>
            </div>
            {tabs_html}
            {panels_html}
            {tab_js}
        </section>
        """
    else:
        discover_section = """
        <section class="container" style="padding:48px 24px;text-align:center;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">Be the First to List</h2>
            <p style="color:var(--ink-muted);font-size:16px;margin-bottom:24px;">We're curating the best indie tools. Yours could be here.</p>
            <a href="/submit" class="btn btn-primary" style="padding:12px 28px;font-size:16px;">Submit Your Tool</a>
        </section>
        """

    # ── Save Your Tokens ──────────────────────────────────────────────
    save_tokens = """
    <section style="padding:48px 24px;background:#1A2D4A;color:white;">
        <div class="container">
            <h2 style="font-family:var(--font-display);font-size:28px;text-align:center;margin-bottom:12px;">
                Why vibe-code it when someone already built it better?
            </h2>
            <p style="text-align:center;color:rgba(255,255,255,0.6);font-size:16px;margin-bottom:48px;max-width:560px;margin-left:auto;margin-right:auto;">
                You can build anything with AI. But should you build <em>everything</em>?
            </p>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:32px;max-width:900px;margin:0 auto;">
                <div style="text-align:center;border-top:1px solid rgba(255,255,255,0.15);padding-top:24px;">
                    <p style="color:rgba(255,255,255,0.5);font-size:14px;text-decoration:line-through;margin-bottom:8px;">50k tokens to build invoicing</p>
                    <p style="color:var(--slate);font-size:16px;font-weight:600;">A polished tool that already works, ready to install.</p>
                </div>
                <div style="text-align:center;border-top:1px solid rgba(255,255,255,0.15);padding-top:24px;">
                    <p style="color:rgba(255,255,255,0.5);font-size:14px;text-decoration:line-through;margin-bottom:8px;">3 hours debugging auth flows</p>
                    <p style="color:var(--slate);font-size:16px;font-weight:600;">A battle-tested solution from someone who&rsquo;s done it 100 times.</p>
                </div>
                <div style="text-align:center;border-top:1px solid rgba(255,255,255,0.15);padding-top:24px;">
                    <p style="color:rgba(255,255,255,0.5);font-size:14px;text-decoration:line-through;margin-bottom:8px;">Ship next week, maybe</p>
                    <p style="color:var(--slate);font-size:16px;font-weight:600;">Ship today. Use indie tools for the boring bits. Save your tokens for the magic.</p>
                </div>
            </div>
            <p style="text-align:center;margin-top:40px;font-size:15px;color:rgba(255,255,255,0.5);">
                Built by humans who ship. Supported by humans who care.<br>
                <strong style="color:var(--gold);">Save your tokens &mdash; use indie builds.</strong>
            </p>
        </div>
    </section>
    """

    # ── Categories ────────────────────────────────────────────────────
    cat_cards = ""
    for i, c in enumerate(categories):
        count = c.get("tool_count", 0)
        count_label = f"{count} tool{'s' if count != 1 else ''}" if count else "Coming soon"
        cat_cards += f"""
        <a href="/category/{escape(str(c['slug']))}" class="card cat-card"
           style="text-decoration:none;color:inherit;padding:20px;display:{'none' if i >= 6 else 'block'};transition:background 0.15s;"
           onmouseover="this.style.background='var(--cream-dark)'"
           onmouseout="this.style.background=''">
            <span style="font-size:28px;display:block;margin-bottom:8px;">{c['icon']}</span>
            <h3 style="font-family:var(--font-display);font-size:16px;margin-bottom:4px;color:var(--ink);">{escape(str(c['name']))}</h3>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:10px;">{escape(str(c['description']))}</p>
            <span style="font-size:12px;font-weight:600;color:var(--ink-light);background:var(--cream-dark);
                         padding:3px 10px;border-radius:999px;">{count_label}</span>
        </a>
        """

    show_all_btn = ''
    if len(categories) > 6:
        show_all_btn = f"""
        <div style="text-align:center;margin-top:24px;">
            <button onclick="document.querySelectorAll('.cat-card').forEach(c=>c.style.display='block');this.style.display='none';"
                    class="btn btn-secondary" style="padding:10px 24px;">
                Show all {len(categories)} categories
            </button>
        </div>
        """

    categories_html = f"""
    <section class="container" style="padding:48px 24px;">
        <h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:20px;color:var(--ink);">Browse by Problem</h2>
        <div class="card-grid">{cat_cards}</div>
        {show_all_btn}
    </section>
    """

    # ── Curated Collections ───────────────────────────────────────────
    collections_html_section = ""
    if collections:
        coll_cards = ""
        for c in collections[:3]:
            emoji = c.get('cover_emoji', '') or '\U0001f4e6'
            c_title = escape(str(c['title']))
            c_slug = escape(str(c['slug']))
            c_count = c.get('tool_count', 0)
            coll_cards += f"""
            <a href="/collection/{c_slug}" class="card" style="text-decoration:none;color:inherit;display:block;">
                <span style="font-size:28px;display:block;margin-bottom:8px;">{emoji}</span>
                <h3 style="font-family:var(--font-display);font-size:16px;margin-bottom:4px;color:var(--ink);">{c_title}</h3>
                <span style="font-size:12px;font-weight:600;color:var(--ink-light);background:var(--cream-dark);
                             padding:3px 10px;border-radius:999px;">{c_count} tool{"s" if c_count != 1 else ""}</span>
            </a>
            """
        collections_html_section = f"""
        <section class="container" style="padding:0 24px 48px;">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:20px;">
                <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);">Curated Lists</h2>
                <a href="/collections" style="color:var(--terracotta);font-size:14px;font-weight:600;">
                    View all
                </a>
            </div>
            <div class="card-grid">{coll_cards}</div>
        </section>
        """

    # ── Vibe Stacks ────────────────────────────────────────────────────
    stacks_section = ''
    if stacks_list:
        stack_cards_html = "\n".join(stack_card(s) for s in stacks_list[:3])
        stacks_section = f"""
        <section class="container" style="padding:48px 24px 0;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                <h2 style="font-family:var(--font-display);font-size:28px;color:var(--ink);">
                    Vibe Stacks
                </h2>
                <a href="/stacks" style="color:var(--ink-muted);font-weight:600;font-size:14px;text-decoration:none;">View all</a>
            </div>
            <p style="color:var(--ink-muted);font-size:15px;margin-bottom:20px;max-width:560px;">
                Pre-built indie tool bundles. One checkout, bundled discount, full stack shipped.
            </p>
            <div class="card-grid">{stack_cards_html}</div>
        </section>
        """

    # ── For Makers ───────────────────────────────────────────────────
    for_makers_section = """
    <section class="container" style="padding:48px 24px;">
        <h2 style="font-family:var(--font-display);font-size:28px;text-align:center;margin-bottom:12px;color:var(--ink);">
            For Makers
        </h2>
        <p style="text-align:center;color:var(--ink-muted);font-size:16px;margin-bottom:40px;max-width:480px;margin-left:auto;margin-right:auto;">
            Built something cool? List it on IndieStack and get discovered by developers and their AI tools.
        </p>
        <div class="card-grid">
            <div class="card" style="text-align:center;padding:32px 24px;">
                <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--ink-muted);margin-bottom:6px;">Trust</div>
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:8px;color:var(--ink);">Verified Indie</h3>
                <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                    Every listing is manually reviewed. Real makers, real products &mdash; no VC copycats or vapourware.
                </p>
            </div>
            <div class="card" style="text-align:center;padding:32px 24px;">
                <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--ink-muted);margin-bottom:6px;">Pricing</div>
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:8px;color:var(--ink);">Free to List</h3>
                <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                    No listing fees, no hidden charges. Get your tool in front of developers and AI coding assistants for free.
                </p>
            </div>
            <div class="card" style="text-align:center;padding:32px 24px;">
                <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;color:var(--ink-muted);margin-bottom:6px;">Discovery</div>
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:8px;color:var(--ink);">Search by Problem</h3>
                <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                    No sponsored results. No SEO gaming. Find tools by what they solve, ranked by the community.
                </p>
            </div>
        </div>
        <div style="text-align:center;margin-top:32px;">
            <a href="/submit" class="btn btn-primary" style="padding:14px 32px;font-size:16px;">
                Submit Your Tool
            </a>
        </div>
    </section>
    """

    # ── Indie Ring ─────────────────────────────────────────────────────
    indie_ring_section = """
    <section class="container" style="padding:0 24px;">
        <div style="text-align:center;padding:48px 24px;background:var(--cream-dark);border:1px solid var(--border);
                    border-radius:var(--radius);max-width:var(--max-w);margin:0 auto;">
            <h2 style="font-family:var(--font-display);font-size:28px;color:var(--ink);margin:0 0 8px;">
                Indie Ring: Makers Help Makers
            </h2>
            <p style="color:var(--ink-muted);font-size:16px;max-width:480px;margin:0 auto 20px;">
                Listed a tool on IndieStack? Get <strong>50% off</strong> every other maker&rsquo;s tool.
                The indie community, supporting itself.
            </p>
            <a href="/submit" class="btn btn-primary">List Your Tool &amp; Join</a>
        </div>
    </section>
    """

    # ── CTA ───────────────────────────────────────────────────────────
    cta = """
    <section style="text-align:center;padding:48px 24px;
                    background:#1A2D4A;color:white;">
        <h2 style="font-family:var(--font-display);font-size:28px;margin-bottom:12px;">Built something cool?</h2>
        <p style="color:rgba(255,255,255,0.7);margin-bottom:24px;font-size:16px;">
            List your tool for free or sell it directly to people who need it.
        </p>
        <a href="/submit" class="btn" style="background:var(--terracotta);color:white;font-weight:700;
                                              padding:14px 32px;font-size:16px;">
            Submit Your Tool
        </a>
    </section>
    """

    # New order: hero → MCP (immediate) → ticker → pkg.json → discover (tabbed) → save tokens → categories → collections → stacks → for makers → indie ring → CTA
    def _reveal(html):
        return f'<div class="reveal">{html}</div>'

    body = hero + _reveal(mcp_section) + _reveal(save_tokens) + _reveal(ticker_html) + _reveal(pkg_json_cta) + _reveal(discover_section) + _reveal(categories_html) + _reveal(collections_html_section) + _reveal(stacks_section) + _reveal(for_makers_section) + _reveal(indie_ring_section) + _reveal(cta)

    import json as _json
    website_ld = _json.dumps({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "IndieStack",
        "url": "https://indiestack.fly.dev",
        "description": "Your AI's tool discovery layer. Search 130+ vetted indie SaaS tools before building from scratch.",
        "potentialAction": {
            "@type": "SearchAction",
            "target": "https://indiestack.fly.dev/search?q={search_term_string}",
            "query-input": "required name=search_term_string"
        }
    }, ensure_ascii=False)
    extra_head = f'<script type="application/ld+json">{website_ld}</script>'
    # Force dark mode on landing page (doesn't save to localStorage, so other pages respect user preference)
    extra_head += (
        '<script>'
        '(function(){'
        'var saved=localStorage.getItem("indiestack-theme");'
        'if(!saved){document.documentElement.setAttribute("data-theme","dark");}'
        '})();'
        '</script>'
    )
    extra_head += (
        '<style>'
        '.reveal{opacity:0;transform:translateY(24px);transition:opacity 0.6s ease,transform 0.6s ease;}'
        '.reveal.visible{opacity:1;transform:translateY(0);}'
        '@media(prefers-reduced-motion:reduce){.reveal{opacity:1;transform:none;transition:none;}}'
        '.hero-glow{position:relative;}'
        '.hero-glow::before{content:\'\';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);'
        'width:500px;height:500px;background:radial-gradient(circle,rgba(0,212,245,0.12) 0%,transparent 70%);'
        'pointer-events:none;z-index:0;}'
        '</style>'
        '<script>'
        'document.addEventListener(\'DOMContentLoaded\',function(){'
        'var observer=new IntersectionObserver(function(entries){'
        'entries.forEach(function(entry){'
        'if(entry.isIntersecting){entry.target.classList.add(\'visible\');observer.unobserve(entry.target);}'
        '});'
        '},{threshold:0.15,rootMargin:\'0px 0px -60px 0px\'});'
        'document.querySelectorAll(\'.reveal\').forEach(function(el){observer.observe(el);});'
        '});'
        '</script>'
        '<noscript><style>.reveal{opacity:1;transform:none}</style></noscript>'
    )

    return HTMLResponse(page_shell("IndieStack \u2014 Stop your AI writing code you don\u2019t need", body,
                                   description="IndieStack plugs into Claude, Cursor, and Windsurf. Before your AI writes code, it checks if an indie tool already does it.",
                                   user=request.state.user, canonical="/", extra_head=extra_head,
                                   og_image="https://indiestack.fly.dev/api/og-home.svg"))

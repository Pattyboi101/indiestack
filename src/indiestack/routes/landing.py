"""Landing page — hero, trending tools, category grid, how it works."""

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
    _tokens_pill = ('<span style="color:var(--border);">|</span><span>~' + str(tokens_saved // 1000) + 'k tokens saved</span>') if tokens_saved > 0 else ''
    hero = (
        '<section style="text-align:center;padding:80px 24px 64px;'
        '                background:linear-gradient(180deg, var(--cream) 0%, var(--cream-dark) 50%, var(--cream) 100%);'
        '                position:relative;overflow:hidden;">'
        '    <div style="position:absolute;top:-60px;left:-60px;width:200px;height:200px;border-radius:50%;'
        '                background:rgba(26,45,74,0.06);"></div>'
        '    <div style="position:absolute;bottom:-40px;right:-40px;width:160px;height:160px;border-radius:50%;'
        '                background:rgba(0,212,245,0.06);"></div>'
        '    <h1 style="font-family:var(--font-display);font-size:clamp(32px,5vw,52px);'
        '               line-height:1.15;max-width:700px;margin:0 auto;color:var(--ink);position:relative;">'
        '        Skip the boilerplate. Launch this weekend.'
        '    </h1>'
        '    <p style="font-size:19px;color:var(--ink-muted);max-width:540px;margin:16px auto 32px;line-height:1.6;">'
        '        Stop rebuilding auth, payments, and analytics from scratch.'
        '        Discover battle-tested indie tools and ship your product faster. Makers keep ~92%.'
        '    </p>'
        '    <form action="/search" method="GET" style="max-width:520px;margin:0 auto;">'
        '        <div style="display:flex;align-items:center;background:var(--card-bg, white);border:2px solid var(--border);'
        '                    border-radius:999px;padding:6px 6px 6px 16px;gap:8px;'
        '                    transition:border-color 0.2s;box-shadow:0 4px 20px rgba(45,41,38,0.06);"'
        '             onfocus="this.style.borderColor=\'var(--terracotta)\'" onblur="this.style.borderColor=\'var(--border)\'">'
        '            <span style="font-size:18px;color:var(--ink-muted);">&#128269;</span>'
        '            <input type="text" name="q"'
        '                   placeholder="I need to send invoices, track analytics, collect feedback..."'
        '                   style="flex:1;border:none;outline:none;font-size:16px;font-family:var(--font-body);'
        '                          padding:10px 0;background:transparent;color:var(--ink);">'
        '            <button type="submit" class="btn btn-primary" style="padding:10px 20px;flex-shrink:0;">'
        '                Search'
        '            </button>'
        '        </div>'
        '    </form>'
        f'    <div style="display:inline-flex;flex-wrap:wrap;gap:8px 16px;justify-content:center;background:var(--card-bg);border:1px solid var(--border);'
        f'                border-radius:999px;padding:10px 28px;margin-top:24px;font-size:14px;color:var(--ink-light);'
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

    # ── Live Fire Ticker ──────────────────────────────────────
    ticker_html = ''
    if activities:
        ticker_items = ' &nbsp;&middot;&nbsp; '.join(
            f'<span style="white-space:nowrap;">&#128293; {a["message"]}</span>'
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

    # ── Trending ──────────────────────────────────────────────────────
    trending_html = ""
    if trending:
        cards = "\n".join(tool_card(t) for t in trending)
        trending_html = f"""
        <section class="container" style="padding:0 24px 64px;">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:20px;">
                <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);">Trending Tools</h2>
                <a href="/search?q=" style="color:var(--terracotta);font-size:14px;font-weight:600;text-decoration:none;">
                    View all &rarr;
                </a>
            </div>
            <div class="scroll-row">{cards}</div>
        </section>
        """
    else:
        trending_html = """
        <section class="container" style="padding:0 24px 64px;text-align:center;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">Be the First to List</h2>
            <p style="color:var(--ink-muted);font-size:16px;margin-bottom:24px;">We're curating the best indie tools. Yours could be here.</p>
            <a href="/submit" class="btn btn-primary" style="padding:12px 28px;font-size:16px;">Submit Your Tool &rarr;</a>
        </section>
        """

    # ── How it works (for makers) ─────────────────────────────────────
    how_it_works = """
    <section style="padding:64px 24px;background:linear-gradient(135deg, var(--ink) 0%, #3D3936 100%);color:white;">
        <div class="container">
            <h2 style="font-family:var(--font-display);font-size:28px;text-align:center;margin-bottom:48px;">
                How IndieStack Works
            </h2>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:40px;max-width:800px;margin:0 auto;">
                <div style="text-align:center;">
                    <div style="width:64px;height:64px;border-radius:16px;background:rgba(26,45,74,0.2);
                                display:flex;align-items:center;justify-content:center;margin:0 auto 16px;font-size:28px;">&#128270;</div>
                    <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:8px;">Discover</h3>
                    <p style="color:rgba(255,255,255,0.65);font-size:14px;line-height:1.6;">Search by the problem you need solved. No sponsored results, no noise.</p>
                </div>
                <div style="text-align:center;">
                    <div style="width:64px;height:64px;border-radius:16px;background:rgba(0,212,245,0.2);
                                display:flex;align-items:center;justify-content:center;margin:0 auto 16px;font-size:28px;">&#9650;</div>
                    <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:8px;">Upvote</h3>
                    <p style="color:rgba(255,255,255,0.65);font-size:14px;line-height:1.6;">Vote for tools you love. The best rise to the top organically.</p>
                </div>
                <div style="text-align:center;">
                    <div style="width:64px;height:64px;border-radius:16px;background:rgba(226,183,100,0.2);
                                display:flex;align-items:center;justify-content:center;margin:0 auto 16px;font-size:28px;">&#128640;</div>
                    <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:8px;">Submit</h3>
                    <p style="color:rgba(255,255,255,0.65);font-size:14px;line-height:1.6;">Built something? List it free or sell it directly on IndieStack.</p>
                </div>
            </div>
        </div>
    </section>
    """

    # ── Categories ────────────────────────────────────────────────────
    cat_cards = ""
    for i, c in enumerate(categories):
        count = c.get("tool_count", 0)
        count_label = f"{count} tool{'s' if count != 1 else ''}" if count else "Coming soon"
        hidden = ' style="display:none;"' if i >= 6 else ''
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
                Show all {len(categories)} categories &darr;
            </button>
        </div>
        """

    categories_html = f"""
    <section class="container" style="padding:56px 24px;">
        <h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:20px;color:var(--ink);">Browse by Problem</h2>
        <div class="card-grid">{cat_cards}</div>
        {show_all_btn}
    </section>
    """

    # ── CTA ───────────────────────────────────────────────────────────
    cta = """
    <section style="text-align:center;padding:64px 24px;
                    background:linear-gradient(135deg, var(--ink) 0%, #3D3936 50%, var(--terracotta-dark) 100%);
                    color:white;position:relative;overflow:hidden;">
        <div style="position:absolute;top:-30px;right:10%;width:120px;height:120px;border-radius:50%;
                    background:rgba(26,45,74,0.15);"></div>
        <div style="position:absolute;bottom:-20px;left:15%;width:80px;height:80px;border-radius:50%;
                    background:rgba(226,183,100,0.1);"></div>
        <h2 style="font-family:var(--font-display);font-size:28px;margin-bottom:12px;position:relative;">Built something cool?</h2>
        <p style="color:rgba(255,255,255,0.7);margin-bottom:24px;font-size:16px;position:relative;">
            List your tool for free or sell it directly to people who need it.
        </p>
        <a href="/submit" class="btn" style="background:var(--terracotta);color:white;font-weight:700;
                                              padding:14px 32px;font-size:16px;border-radius:999px;position:relative;">
            Submit Your Tool &rarr;
        </a>
    </section>
    """

    # ── Featured Tool of the Week ────────────────────────────────────
    featured_html = ""
    if featured:
        featured_html = f"""
        <section class="container" style="padding:0 24px 32px;">
            {featured_card(featured)}
        </section>
        """

    # ── New This Week ─────────────────────────────────────────────────
    new_html = ""
    if recent:
        new_cards = "\n".join(tool_card(t) for t in recent)
        new_html = f"""
        <section class="container" style="padding:0 24px 56px;">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:20px;">
                <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);">New This Week</h2>
                <a href="/new" style="color:var(--terracotta);font-size:14px;font-weight:600;">
                    View all &rarr;
                </a>
            </div>
            <div class="scroll-row">{new_cards}</div>
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
        <section class="container" style="padding:0 24px 56px;">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:20px;">
                <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);">Curated Lists</h2>
                <a href="/collections" style="color:var(--terracotta);font-size:14px;font-weight:600;">
                    View all &rarr;
                </a>
            </div>
            <div class="card-grid">{coll_cards}</div>
        </section>
        """

    updates_html = ""
    if recent_updates:
        updates_cards = "\n".join(update_card(u) for u in recent_updates)
        updates_html = f"""
        <section class="container" style="padding:0 24px 56px;">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:20px;">
                <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);">Latest from Makers</h2>
                <a href="/updates" style="color:var(--terracotta);font-size:14px;font-weight:600;">
                    View all &rarr;
                </a>
            </div>
            {updates_cards}
        </section>
        """

    # ── Why IndieStack? ──────────────────────────────────────────────
    why_section = """
    <section class="container" style="padding:56px 24px;">
        <h2 style="font-family:var(--font-display);font-size:28px;text-align:center;margin-bottom:40px;color:var(--ink);">
            Why IndieStack?
        </h2>
        <div class="card-grid">
            <div class="card" style="text-align:center;padding:32px 24px;">
                <div style="font-size:36px;margin-bottom:12px;">&#9989;</div>
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:8px;color:var(--ink);">Verified Indie</h3>
                <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                    Every listing is manually reviewed. Real makers, real products &mdash; no VC copycats or vapourware.
                </p>
            </div>
            <div class="card" style="text-align:center;padding:32px 24px;">
                <div style="font-size:36px;margin-bottom:12px;">&#128176;</div>
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:8px;color:var(--ink);">Fair Fees</h3>
                <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                    5% commission (3% on Pro). Makers keep ~92% of every sale. No hidden charges, no listing fees.
                </p>
            </div>
            <div class="card" style="text-align:center;padding:32px 24px;">
                <div style="font-size:36px;margin-bottom:12px;">&#128269;</div>
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:8px;color:var(--ink);">Search by Problem</h3>
                <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                    No sponsored results. No SEO gaming. Find tools by what they solve, ranked by the community.
                </p>
            </div>
        </div>
    </section>
    """

    # ── Our Commitments ─────────────────────────────────────────────
    testimonials_section = """
    <section class="container" style="padding:0 24px 56px;">
        <h2 style="font-family:var(--font-display);font-size:24px;text-align:center;margin-bottom:32px;color:var(--ink);">
            Our Commitments
        </h2>
        <div class="card-grid">
            <div class="card" style="text-align:center;padding:32px 24px;">
                <div style="font-size:36px;margin-bottom:12px;">&#9989;</div>
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:8px;color:var(--ink);">Every tool manually reviewed</h3>
                <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                    No spam, no copycats. Every listing is checked by a human before it goes live.
                </p>
            </div>
            <div class="card" style="text-align:center;padding:32px 24px;">
                <div style="font-size:36px;margin-bottom:12px;">&#128176;</div>
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:8px;color:var(--ink);">Makers keep 92&ndash;94%</h3>
                <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                    We charge 5% (3% on Pro). That's it. No hidden fees, no lock-in.
                </p>
            </div>
            <div class="card" style="text-align:center;padding:32px 24px;">
                <div style="font-size:36px;margin-bottom:12px;">&#128269;</div>
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:8px;color:var(--ink);">Search by problem, not by ad spend</h3>
                <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                    Results ranked by relevance, not who paid the most. Verified indie tools only.
                </p>
            </div>
        </div>
    </section>
    """

    # ── Save Your Tokens ──────────────────────────────────────────────
    save_tokens = """
    <section style="padding:64px 24px;background:linear-gradient(135deg, #0F1D30 0%, #1A2D4A 50%, #2B4A6E 100%);color:white;position:relative;overflow:hidden;">
        <div style="position:absolute;top:-40px;right:-40px;width:160px;height:160px;border-radius:50%;background:rgba(0,212,245,0.08);"></div>
        <div style="position:absolute;bottom:-30px;left:-30px;width:120px;height:120px;border-radius:50%;background:rgba(226,183,100,0.06);"></div>
        <div class="container">
            <h2 style="font-family:var(--font-display);font-size:28px;text-align:center;margin-bottom:12px;position:relative;">
                Why vibe-code it when someone already built it better?
            </h2>
            <p style="text-align:center;color:rgba(255,255,255,0.6);font-size:16px;margin-bottom:48px;max-width:560px;margin-left:auto;margin-right:auto;position:relative;">
                You can build anything with AI. But should you build <em>everything</em>?
            </p>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:32px;max-width:900px;margin:0 auto;">
                <div style="text-align:center;position:relative;">
                    <div style="font-size:36px;margin-bottom:12px;">&#129302;</div>
                    <p style="color:rgba(255,255,255,0.5);font-size:14px;text-decoration:line-through;margin-bottom:8px;">50k tokens to build invoicing</p>
                    <p style="color:var(--slate);font-size:16px;font-weight:600;">&pound;10 for a polished tool that already works.</p>
                </div>
                <div style="text-align:center;position:relative;">
                    <div style="font-size:36px;margin-bottom:12px;">&#128293;</div>
                    <p style="color:rgba(255,255,255,0.5);font-size:14px;text-decoration:line-through;margin-bottom:8px;">3 hours debugging auth flows</p>
                    <p style="color:var(--slate);font-size:16px;font-weight:600;">A battle-tested solution from someone who&rsquo;s done it 100 times.</p>
                </div>
                <div style="text-align:center;position:relative;">
                    <div style="font-size:36px;margin-bottom:12px;">&#128640;</div>
                    <p style="color:rgba(255,255,255,0.5);font-size:14px;text-decoration:line-through;margin-bottom:8px;">Ship next week, maybe</p>
                    <p style="color:var(--slate);font-size:16px;font-weight:600;">Ship today. Use indie tools for the boring bits. Save your tokens for the magic.</p>
                </div>
            </div>
            <p style="text-align:center;margin-top:40px;font-size:15px;color:rgba(255,255,255,0.5);position:relative;">
                Built by humans who ship. Supported by humans who care.<br>
                <strong style="color:var(--gold);">Save your tokens &mdash; use indie builds.</strong>
            </p>
        </div>
    </section>
    """

    # ── Works with AI Tools (MCP) ────────────────────────────────────
    mcp_section = """
    <section style="padding:64px 24px;background:var(--cream-dark);">
        <div class="container">
            <h2 style="font-family:var(--font-display);font-size:28px;text-align:center;margin-bottom:12px;color:var(--ink);">
                Works with your AI tools
            </h2>
            <p style="text-align:center;color:var(--ink-muted);font-size:16px;margin-bottom:40px;max-width:560px;margin-left:auto;margin-right:auto;">
                Install the IndieStack MCP server and your AI coding tool will search IndieStack
                before building from scratch. Save tokens, ship faster.
            </p>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:24px;max-width:700px;margin:0 auto 40px;">
                <div class="card" style="text-align:center;padding:24px;">
                    <div style="font-size:28px;margin-bottom:8px;">&#129302;</div>
                    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:4px;">Claude Code</h3>
                    <p style="font-size:13px;color:var(--ink-muted);">MCP server integration</p>
                </div>
                <div class="card" style="text-align:center;padding:24px;">
                    <div style="font-size:28px;margin-bottom:8px;">&#9997;</div>
                    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:4px;">Cursor</h3>
                    <p style="font-size:13px;color:var(--ink-muted);">MCP server integration</p>
                </div>
                <div class="card" style="text-align:center;padding:24px;">
                    <div style="font-size:28px;margin-bottom:8px;">&#127754;</div>
                    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:4px;">Windsurf</h3>
                    <p style="font-size:13px;color:var(--ink-muted);">MCP server integration</p>
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

    # ── Vibe Stacks ────────────────────────────────────────────────────
    stacks_section = ''
    if stacks_list:
        stack_cards_html = "\n".join(stack_card(s) for s in stacks_list[:3])
        stacks_section = f"""
        <section class="container" style="padding:48px 24px 0;">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;">
                <h2 style="font-family:var(--font-display);font-size:28px;color:var(--ink);">
                    &#128230; Vibe Stacks
                </h2>
                <a href="/stacks" style="color:var(--ink-muted);font-weight:600;font-size:14px;text-decoration:none;">View all &rarr;</a>
            </div>
            <p style="color:var(--ink-muted);font-size:15px;margin-bottom:20px;max-width:560px;">
                Pre-built indie tool bundles. One checkout, bundled discount, full stack shipped.
            </p>
            <div class="card-grid">{stack_cards_html}</div>
        </section>
        """

    # ── Indie Ring ─────────────────────────────────────────────────────
    indie_ring_section = """
    <section class="container" style="padding:0 24px;">
        <div style="text-align:center;padding:48px 24px;background:linear-gradient(135deg, #ECFDF5 0%, var(--cream) 100%);
                    border-radius:var(--radius);max-width:var(--max-w);margin:0 auto;">
            <span style="font-size:40px;">&#129309;</span>
            <h2 style="font-family:var(--font-display);font-size:28px;color:var(--ink);margin:12px 0 8px;">
                Indie Ring: Makers Help Makers
            </h2>
            <p style="color:var(--ink-muted);font-size:16px;max-width:480px;margin:0 auto 20px;">
                Listed a tool on IndieStack? Get <strong>50% off</strong> every other maker&rsquo;s tool.
                The indie community, supporting itself.
            </p>
            <a href="/submit" class="btn btn-primary">List Your Tool &amp; Join &rarr;</a>
        </div>
    </section>
    """

    body = hero + ticker_html + featured_html + trending_html + new_html + collections_html_section + stacks_section + updates_html + how_it_works + save_tokens + mcp_section + why_section + indie_ring_section + testimonials_section + categories_html + cta
    return HTMLResponse(page_shell("IndieStack — Discover Indie SaaS Tools", body,
                                   description="Discover the best software tools built by indie makers and solo developers. Search by problem, not product name.",
                                   user=request.state.user, canonical="/"))

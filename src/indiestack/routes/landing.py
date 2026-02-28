"""Landing page — MCP-first product story with interactive search."""

import time as _time
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell, tool_card
from indiestack.db import get_all_categories, get_trending_scored, get_search_stats, get_search_trends

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
        trending = cached['trending']
        categories = cached['categories']
        mcp_views = cached.get('mcp_views', 0)
        search_stats = cached.get('search_stats', {'this_week': 0})
        search_trends = cached.get('search_trends', [])
    else:
        _tc = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")
        tool_count = (await _tc.fetchone())['cnt']
        _cc = await db.execute("SELECT COUNT(*) as cnt FROM categories")
        cat_count = (await _cc.fetchone())['cnt']
        _mc = await db.execute("SELECT COUNT(*) as cnt FROM makers")
        maker_count = (await _mc.fetchone())['cnt']
        trending = await get_trending_scored(db, limit=6, days=7)
        categories = await get_all_categories(db)
        _mcp = await db.execute("SELECT COALESCE(SUM(mcp_view_count), 0) as cnt FROM tools")
        mcp_views = (await _mcp.fetchone())['cnt']
        search_stats = await get_search_stats(db)
        search_trends = await get_search_trends(db, days=7, limit=5)

        _landing_cache['data'] = {
            'tool_count': tool_count,
            'cat_count': cat_count,
            'maker_count': maker_count,
            'mcp_views': mcp_views,
            'trending': trending,
            'categories': categories,
            'search_stats': search_stats,
            'search_trends': search_trends,
        }
        _landing_cache['expires'] = _time.time() + 300  # 5 minutes

    # ── Top Banner ────────────────────────────────────────────────
    launch_banner = (
        '<div style="background:linear-gradient(135deg,var(--terracotta),var(--terracotta-dark));padding:12px 24px;text-align:center;">'
        '    <a href="#mcp-install" style="color:white;text-decoration:none;font-size:14px;font-weight:600;">'
        '        &#9889; MCP Server v0.4.0 &mdash; AI agents can now search ' + str(tool_count) + ' indie tools. '
        '        <span style="text-decoration:underline;">Install in one command</span>'
        '    </a>'
        '</div>'
    )

    # ── Hero ──────────────────────────────────────────────────────────
    hero = (
        launch_banner
        + '<section style="text-align:center;padding:64px 24px 56px;'
        '                background:var(--cream);">'
        '    <h1 style="font-family:var(--font-display);font-size:clamp(32px,5vw,52px);'
        '               line-height:1.15;max-width:700px;margin:0 auto;color:var(--ink);">'
        '        <span style="background:linear-gradient(135deg, var(--slate) 0%, #fff 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">The indie tool catalog your AI actually uses.</span>'
        '    </h1>'
        '    <p style="font-size:19px;color:var(--ink-muted);max-width:540px;margin:16px auto 32px;line-height:1.6;">'
        f'        {tool_count} tools curated by hand. Your AI searches them before writing code from scratch.'
        '    </p>'
        # Hero visual — code conversation block
        '    <div class="hero-glow">'
        '    <div style="max-width:560px;margin:0 auto 28px;text-align:left;background:var(--terracotta-dark);border-radius:var(--radius);'
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
        '        <a href="#mcp-install" class="btn btn-lg btn-primary">'
        '            Install the MCP Server'
        '        </a>'
        '        <a href="/explore" class="btn btn-lg btn-secondary">'
        '            Browse Tools'
        '        </a>'
        '    </div>'
        # Stats pills
        f'    <div style="display:inline-flex;flex-wrap:wrap;gap:8px 16px;justify-content:center;background:var(--card-bg);border:1px solid var(--border);'
        f'                border-radius:var(--radius-sm);padding:10px 28px;font-size:14px;color:var(--ink-light);'
        f'                box-shadow:0 1px 3px rgba(26,45,74,0.06);">'
        f'        <span>{tool_count} tools, hand-curated</span>'
        f'        <span style="color:var(--border);">|</span>'
        f'        <span>{search_stats["this_week"]} searches this week</span>'
        f'        <span style="color:var(--border);">|</span>'
        f'        <span style="color:var(--accent);">{mcp_views} AI agent lookups</span>'
        f'    </div>'
        + (
            '<div style="margin-top:16px;display:flex;flex-wrap:wrap;gap:6px;justify-content:center;align-items:center;">'
            '    <span style="font-size:13px;color:var(--ink-muted);margin-right:4px;">Popular searches:</span>'
            + ' '.join(
                f'<a href="/search?q={escape(t["query"])}" style="background:var(--card-bg);border:1px solid var(--border);'
                f'padding:4px 12px;border-radius:999px;font-size:13px;color:var(--ink-light);text-decoration:none;">'
                f'{escape(t["query"])}</a>'
                for t in search_trends[:5]
            )
            + '</div>'
        if search_trends else '') +
        f'    <div style="margin-top:16px;">'
        f'        <a href="/submit" class="btn btn-slate" style="padding:10px 24px;font-size:14px;">Add Your Tool &rarr;</a>'
        f'        <p style="font-size:12px;color:var(--ink-muted);margin-top:8px;">Sign up free &mdash; get a welcome perk from <strong style="color:var(--accent);">Perplexity</strong></p>'
        f'    </div>'
        '</section>'
    )

    # ── MCP Walkthrough ──────────────────────────────────────────────
    mcp_walkthrough = f"""
    <section id="mcp-install" style="padding:64px 24px;background:var(--cream-dark);">
        <div class="container" style="max-width:800px;">
            <h2 style="font-family:var(--font-display);font-size:clamp(24px,3.5vw,32px);text-align:center;margin-bottom:8px;color:var(--ink);">
                How it works
            </h2>
            <p style="text-align:center;color:var(--ink-muted);font-size:16px;margin-bottom:48px;max-width:520px;margin-left:auto;margin-right:auto;">
                Three steps. Your AI stops reinventing the wheel.
            </p>

            <!-- 3-step flow -->
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:40px;margin-bottom:48px;">
                <div style="text-align:center;">
                    <div style="width:40px;height:40px;border-radius:50%;background:var(--accent);color:white;
                                display:flex;align-items:center;justify-content:center;font-weight:700;font-size:18px;
                                margin:0 auto 14px;">1</div>
                    <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin-bottom:6px;">Install</h3>
                    <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                        One command. Works with Claude&nbsp;Code, Cursor, and Windsurf.
                    </p>
                </div>
                <div style="text-align:center;">
                    <div style="width:40px;height:40px;border-radius:50%;background:var(--accent);color:white;
                                display:flex;align-items:center;justify-content:center;font-weight:700;font-size:18px;
                                margin:0 auto 14px;">2</div>
                    <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin-bottom:6px;">Your AI searches</h3>
                    <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                        When you ask your AI to build something, it checks IndieStack first.
                    </p>
                </div>
                <div style="text-align:center;">
                    <div style="width:40px;height:40px;border-radius:50%;background:var(--accent);color:white;
                                display:flex;align-items:center;justify-content:center;font-weight:700;font-size:18px;
                                margin:0 auto 14px;">3</div>
                    <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin-bottom:6px;">It recommends real tools</h3>
                    <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                        Instead of writing 50k tokens of code, your AI suggests a vetted indie tool.
                    </p>
                </div>
            </div>

            <!-- Install cards -->
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:32px;">
                <div class="card" style="padding:24px;border-left:3px solid var(--slate);">
                    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:8px;">Claude Code</h3>
                    <code style="font-family:var(--font-mono);font-size:12px;color:var(--ink-muted);word-break:break-all;">claude mcp add indiestack</code>
                </div>
                <div class="card" style="padding:24px;border-left:3px solid var(--slate);">
                    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:8px;">Cursor</h3>
                    <code style="font-family:var(--font-mono);font-size:12px;color:var(--ink-muted);">pip install indiestack</code>
                </div>
                <div class="card" style="padding:24px;border-left:3px solid var(--slate);">
                    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:8px;">Windsurf</h3>
                    <code style="font-family:var(--font-mono);font-size:12px;color:var(--ink-muted);">pip install indiestack</code>
                </div>
            </div>

            <!-- Quick install block -->
            <div style="max-width:600px;margin:0 auto 32px;">
                <p style="font-size:14px;font-weight:600;color:var(--ink);margin-bottom:8px;">Quick install:</p>
                <div style="background:var(--ink);color:var(--slate);border-radius:var(--radius-sm);padding:16px 20px;
                            font-family:var(--font-mono);font-size:13px;line-height:1.8;overflow-x:auto;">
                    <span style="color:var(--ink-muted);"># Install the MCP server</span><br>
                    pip install indiestack<br><br>
                    <span style="color:var(--ink-muted);"># Add to your Claude Code config</span><br>
                    claude mcp add indiestack -- python -m indiestack.mcp_server
                </div>
            </div>

            <!-- Proof stats -->
            <div style="display:flex;flex-wrap:wrap;gap:8px 24px;justify-content:center;font-size:14px;color:var(--ink-muted);">
                <span><strong style="color:var(--accent);">{mcp_views}</strong> agent lookups</span>
                <span style="color:var(--border);">&middot;</span>
                <span><strong style="color:var(--ink);">{tool_count}</strong> tools indexed</span>
                <span style="color:var(--border);">&middot;</span>
                <span><strong style="color:var(--ink);">{search_stats["this_week"]}</strong> searches this week</span>
            </div>
        </div>
    </section>
    """

    # ── "What are you building?" Search Widget ───────────────────────
    search_widget = """
    <section style="padding:64px 24px;">
        <div class="container" style="max-width:600px;">
            <h2 style="font-family:var(--font-display);font-size:clamp(22px,3vw,28px);text-align:center;margin-bottom:8px;color:var(--ink);">
                What are you building?
            </h2>
            <p style="text-align:center;color:var(--ink-muted);font-size:16px;margin-bottom:28px;">
                Search our catalog &mdash; your AI already does.
            </p>
            <div style="display:flex;gap:8px;max-width:560px;margin:0 auto;">
                <input type="text" id="landing-search"
                       placeholder="e.g. invoicing, analytics, auth..."
                       style="flex:1;padding:14px 18px;font-size:16px;font-family:var(--font-body);
                              border:1px solid var(--border);border-radius:var(--radius-sm);
                              background:var(--card-bg);color:var(--ink);outline:none;"
                       onfocus="this.style.borderColor='var(--accent)'"
                       onblur="this.style.borderColor='var(--border)'">
                <button id="landing-search-btn" class="btn btn-primary"
                        style="padding:14px 24px;font-size:16px;white-space:nowrap;cursor:pointer;">
                    Search
                </button>
            </div>
            <div id="landing-search-results" style="max-width:560px;margin:16px auto 0;"></div>
            <div id="landing-search-empty" style="display:none;max-width:560px;margin:16px auto 0;text-align:center;
                                                   padding:24px;background:var(--cream-dark);border-radius:var(--radius-sm);">
                <p style="color:var(--ink-muted);font-size:15px;margin-bottom:12px;">
                    No indie tool for that yet &mdash; sounds like a gap worth filling.
                </p>
                <a href="/submit" class="btn btn-primary" style="padding:10px 24px;font-size:14px;">
                    Submit yours &rarr;
                </a>
            </div>
        </div>
    </section>
    <script>
    (function(){
        var input=document.getElementById('landing-search');
        var btn=document.getElementById('landing-search-btn');
        var results=document.getElementById('landing-search-results');
        var empty=document.getElementById('landing-search-empty');
        function doSearch(){
            var q=input.value.trim();
            if(!q)return;
            btn.disabled=true;btn.textContent='Searching...';
            results.innerHTML='';empty.style.display='none';
            fetch('/api/tools/search?q='+encodeURIComponent(q)+'&limit=3&source=landing')
            .then(function(r){return r.json();})
            .then(function(data){
                btn.disabled=false;btn.textContent='Search';
                if(data.tools&&data.tools.length>0){
                    results.innerHTML=data.tools.map(function(t){
                        var verified=t.is_verified?'<span style="color:var(--accent);font-size:11px;font-weight:700;margin-left:6px;">&#10003; Verified</span>':'';
                        return '<a href="/tool/'+t.indiestack_url.split("/tool/")[1]+'" style="display:flex;align-items:center;gap:16px;'+
                            'padding:16px 20px;text-decoration:none;color:inherit;background:var(--card-bg);'+
                            'border:1px solid var(--border);border-radius:var(--radius-sm);margin-bottom:8px;'+
                            'transition:border-color 0.15s;" onmouseenter="this.style.borderColor=\\'var(--accent)\\'" '+
                            'onmouseleave="this.style.borderColor=\\'var(--border)\\'">'+
                            '<div style="flex:1;min-width:0;">'+
                            '<div style="font-family:var(--font-display);font-size:16px;color:var(--ink);">'+t.name+verified+'</div>'+
                            '<div style="font-size:13px;color:var(--ink-muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'+t.tagline+'</div>'+
                            '</div>'+
                            '<span style="font-size:13px;font-weight:600;color:var(--ink-light);white-space:nowrap;">'+t.price+'</span>'+
                            '</a>';
                    }).join('');
                }else{
                    empty.style.display='block';
                }
            })
            .catch(function(){btn.disabled=false;btn.textContent='Search';});
        }
        btn.addEventListener('click',doSearch);
        input.addEventListener('keydown',function(e){if(e.key==='Enter')doSearch();});
    })();
    </script>
    """

    # ── Trending Strip ───────────────────────────────────────────────
    trending_strip = ''
    if trending:
        trending_cards = "\n".join(tool_card(t) for t in trending[:6])
        trending_strip = f"""
        <section class="container" style="padding:48px 24px;">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:16px;">
                <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);">Trending this week</h2>
                <a href="/explore" style="color:var(--terracotta);font-size:14px;font-weight:600;text-decoration:none;">
                    Browse all &rarr;
                </a>
            </div>
            <div class="scroll-row">{trending_cards}</div>
        </section>
        """

    # ── Compact Category Grid ────────────────────────────────────────
    cat_items = ''
    for c in categories:
        count = c.get('tool_count', 0)
        cat_items += (
            f'<a href="/category/{escape(str(c["slug"]))}" class="cat-compact-item"'
            f'   style="display:flex;align-items:center;gap:10px;padding:12px 16px;'
            f'   border:1px solid var(--border);border-radius:var(--radius-sm);'
            f'   text-decoration:none;color:inherit;transition:background 0.15s;"'
            f'   onmouseenter="this.style.background=\'var(--cream-dark)\'"'
            f'   onmouseleave="this.style.background=\'transparent\'">'
            f'  <span style="font-size:22px;flex-shrink:0;">{c["icon"]}</span>'
            f'  <span style="font-size:14px;font-weight:600;color:var(--ink);flex:1;">{escape(str(c["name"]))}</span>'
            f'  <span style="font-size:12px;color:var(--ink-muted);">{count}</span>'
            f'</a>'
        )

    categories_compact = f"""
    <section class="container" style="padding:48px 24px;">
        <h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:20px;color:var(--ink);">Browse by category</h2>
        <div class="cat-compact-grid">{cat_items}</div>
    </section>
    """

    # ── Maker CTA ────────────────────────────────────────────────────
    maker_cta = f"""
    <section style="text-align:center;padding:56px 24px;background:var(--terracotta);color:white;">
        <p style="font-family:var(--font-display);font-size:clamp(24px,3.5vw,32px);margin-bottom:8px;">
            {maker_count}+ makers already listed
        </p>
        <p style="color:rgba(255,255,255,0.7);font-size:16px;margin-bottom:28px;max-width:440px;margin-left:auto;margin-right:auto;">
            List your tool for free. AI agents and developers will find it.
        </p>
        <a href="/submit" class="btn" style="background:var(--slate);color:var(--terracotta-dark);font-weight:700;
                                              padding:14px 32px;font-size:16px;">
            Submit Your Tool &rarr;
        </a>
    </section>
    """

    # ── Assembly ─────────────────────────────────────────────────────
    def _reveal(html):
        return f'<div class="reveal">{html}</div>'

    body = hero + _reveal(mcp_walkthrough) + _reveal(search_widget) + _reveal(trending_strip) + _reveal(categories_compact) + _reveal(maker_cta)

    import json as _json
    website_ld = _json.dumps({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "IndieStack",
        "url": BASE_URL,
        "description": "Your AI's tool discovery layer. Search 130+ vetted indie SaaS tools before building from scratch.",
        "potentialAction": {
            "@type": "SearchAction",
            "target": f"{BASE_URL}/search?q={{search_term_string}}",
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
        '.cat-compact-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}'
        '@media(max-width:768px){.cat-compact-grid{grid-template-columns:repeat(2,1fr);}}'
        '@media(max-width:480px){.cat-compact-grid{grid-template-columns:1fr;}}'
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

    return HTMLResponse(page_shell("IndieStack \u2014 The procurement layer for AI agents", body,
                                   description="IndieStack plugs into Claude, Cursor, and Windsurf. Before your AI writes code, it checks if an indie tool already does it.",
                                   user=request.state.user, canonical="/", extra_head=extra_head,
                                   og_image=f"{BASE_URL}/api/og-home.svg"))

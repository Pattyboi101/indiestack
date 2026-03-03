"""Landing page — MCP-first product story with interactive search."""

import os
import time as _time
from datetime import date
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
        ai_recs = cached.get('ai_recs', 0)
        search_stats = cached.get('search_stats', {'this_week': 0})
        search_trends = cached.get('search_trends', [])
        claimed_count = cached.get('claimed_count', 0)
        today_ai_count = cached.get('today_ai_count', 0)
        featured = cached.get('featured', None)
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
        _searches = await db.execute("SELECT COUNT(*) as cnt FROM search_logs")
        search_count = (await _searches.fetchone())['cnt']
        _cites = await db.execute("SELECT COUNT(*) as cnt FROM agent_citations")
        cite_count = (await _cites.fetchone())['cnt']
        ai_recs = mcp_views + search_count + cite_count
        search_stats = await get_search_stats(db)
        search_trends = await get_search_trends(db, days=7, limit=5)
        _claimed = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE claimed_at IS NOT NULL AND status='approved'")
        claimed_count = (await _claimed.fetchone())['cnt']
        _today_ai = await db.execute("SELECT COUNT(*) as cnt FROM search_logs WHERE date(created_at)=date('now')")
        today_ai_count = (await _today_ai.fetchone())['cnt']
        _today_cites = await db.execute("SELECT COUNT(*) as cnt FROM agent_citations WHERE date(created_at)=date('now')")
        today_ai_count += (await _today_cites.fetchone())['cnt']
        try:
            # Try TOTW flag first, then fall back to most AI-recommended tool
            featured = None
            try:
                _totw = await db.execute(
                    """SELECT t.name, t.slug, t.tagline, c.slug as category_slug
                       FROM tools t JOIN categories c ON t.category_id = c.id
                       WHERE t.tool_of_the_week = 1 AND t.status = 'approved'
                       LIMIT 1"""
                )
                featured = await _totw.fetchone()
            except Exception:
                pass  # column may not exist yet
            if not featured:
                _totw2 = await db.execute(
                    """SELECT t.name, t.slug, t.tagline, c.slug as category_slug
                       FROM tools t JOIN categories c ON t.category_id = c.id
                       WHERE t.status = 'approved' AND t.mcp_view_count > 0
                       ORDER BY t.mcp_view_count DESC LIMIT 1"""
                )
                featured = await _totw2.fetchone()
        except Exception:
            featured = None

        _landing_cache['data'] = {
            'tool_count': tool_count,
            'cat_count': cat_count,
            'maker_count': maker_count,
            'ai_recs': ai_recs,
            'claimed_count': claimed_count,
            'trending': trending,
            'categories': categories,
            'search_stats': search_stats,
            'search_trends': search_trends,
            'today_ai_count': today_ai_count,
            'featured': featured,
        }
        _landing_cache['expires'] = _time.time() + 300  # 5 minutes

    # ── Top Banner (PH launch week: March 2-9, then MCP fallback) ──
    _today = date.today()
    if False and date(2026, 3, 1) <= _today <= date(2026, 3, 9):
        _hn_url = os.environ.get("HN_URL", "https://news.ycombinator.com/item?id=47209709")
        launch_banner = (
            '<div style="background:linear-gradient(135deg,#FF6600,#E55A00);padding:12px 24px;text-align:center;">'
            '    <a href="' + _hn_url + '" target="_blank" rel="noopener" style="color:white;text-decoration:none;font-size:14px;font-weight:600;">'
            '        &#128640; We\'re live on Hacker News! Check it out &rarr;'
            '    </a>'
            '</div>'
        )
    else:
        launch_banner = (
            '<div style="background:linear-gradient(135deg,var(--terracotta),var(--terracotta-dark));padding:12px 24px;text-align:center;">'
            '    <a href="#mcp-install" style="color:white;text-decoration:none;font-size:14px;font-weight:600;">'
            '        &#9889; MCP Server v0.5.0 &mdash; ' + str(tool_count) + ' indie tools. '
            '        <span style="text-decoration:underline;">Install in one command</span>'
            '    </a>'
            '    <span class="pulse-banner-sep" style="color:rgba(255,255,255,0.4);margin:0 12px;font-size:14px;">&middot;</span>'
            '    <a href="/pulse" class="pulse-banner-link" style="color:rgba(255,255,255,0.9);text-decoration:none;font-size:14px;font-weight:500;white-space:nowrap;">'
            '        <span style="display:inline-block;width:8px;height:8px;background:#FF3B30;border-radius:50%;'
            '                     animation:pulse-dot 1.5s ease-in-out infinite;margin-right:6px;vertical-align:middle;"></span>'
            f'       {today_ai_count:,} AI lookups today &rarr;'
            '    </a>'
            '</div>'
        )
        launch_banner += (
            '<style>'
            '@keyframes pulse-dot{0%,100%{opacity:1;transform:scale(1)}50%{opacity:0.4;transform:scale(0.8)}}'
            '@media(max-width:600px){.pulse-banner-sep,.pulse-banner-link{display:none!important}}'
            '</style>'
        )

    # ── Hero code block — dynamic Tool of the Week ─────────────────
    _CATEGORY_PROMPTS = {
        'analytics-metrics': 'I need analytics for my app',
        'authentication': 'Add auth to my project',
        'payments': 'I need to accept payments',
        'email-marketing': 'I need email sending for my app',
        'monitoring-uptime': 'Set up uptime monitoring',
        'invoicing-billing': 'Build an invoicing system',
        'developer-tools': 'I need a dev tool for this',
        'api-tools': 'I need an API for this',
        'design-creative': 'I need a design tool',
        'project-management': 'I need project management',
        'forms-surveys': 'Build me a form handler',
        'seo-tools': 'I need SEO tooling',
        'customer-support': 'Add a support widget',
        'crm-sales': 'I need a CRM',
        'social-media': 'I need social media tooling',
        'landing-pages': 'Build me a landing page',
        'scheduling-booking': 'I need booking functionality',
        'file-management': 'I need file storage',
        'feedback-reviews': 'Add a feedback widget',
        'ai-automation': 'I need AI automation',
    }
    if featured and (featured.get('name') or featured.get('tool_name')):
        _hero_tool_name = escape(featured.get('name') or featured.get('tool_name', ''))
        _hero_tool_slug = featured.get('slug') or featured.get('tool_slug', 'simple-analytics')
        _hero_tagline = escape(featured.get('tagline', ''))
        _hero_prompt = _CATEGORY_PROMPTS.get(featured.get('category_slug', ''), 'Build me something')
    else:
        _hero_tool_name = 'Simple Analytics'
        _hero_tool_slug = 'simple-analytics'
        _hero_tagline = 'privacy-first, 2-line install'
        _hero_prompt = 'Build me an analytics dashboard'

    # Truncate tagline at word boundary for the code block
    if len(_hero_tagline) > 35:
        _hero_tagline = _hero_tagline[:35].rsplit(' ', 1)[0] + '...'

    # ── Hero ──────────────────────────────────────────────────────────
    hero = (
        launch_banner
        + '<section style="text-align:center;padding:64px 24px 48px;'
        '                background:var(--cream);">'
        '    <h1 style="font-family:var(--font-display);font-size:clamp(32px,5vw,52px);'
        '               line-height:1.15;max-width:700px;margin:0 auto;color:var(--ink);">'
        '        <span class="hero-headline">Stop letting your AI reinvent the wheel.</span>'
        '    </h1>'
        '    <p style="font-size:20px;color:var(--ink-muted);max-width:560px;margin:16px auto 32px;line-height:1.6;">'
        f'        Install our MCP server. Your AI searches {tool_count} indie tools before writing a single line of code.'
        '    </p>'
        # Hero visual — code conversation block
        '    <div class="hero-glow">'
        '    <div style="max-width:560px;margin:0 auto 24px;text-align:left;background:var(--terracotta-dark);border-radius:var(--radius);'
        '                padding:24px 24px;font-family:var(--font-mono);font-size:15px;line-height:1.9;'
        '                box-shadow:var(--shadow-floating);position:relative;z-index:1;overflow:hidden;">'
        '        <div style="position:absolute;top:16px;left:16px;display:flex;gap:8px;">'
        '            <span style="width:12px;height:12px;border-radius:50%;background:#FF5F56;display:inline-block;"></span>'
        '            <span style="width:12px;height:12px;border-radius:50%;background:var(--gold);display:inline-block;"></span>'
        '            <span style="width:12px;height:12px;border-radius:50%;background:#27C93F;display:inline-block;"></span>'
        '        </div>'
        '        <div style="margin-top:16px;">'
        '            <span style="color:var(--gold);font-weight:700;">You:</span>'
        f'            <span style="color:white;"> &ldquo;{_hero_prompt}&rdquo;</span><br><br>'
        '            <span style="color:var(--slate);font-weight:700;">AI: </span>'
        '            <span style="color:rgba(255,255,255,0.85);"> &ldquo;Before I write ~50k tokens of code,</span><br>'
        '            <span style="color:rgba(255,255,255,0.85);">&#160;&#160;&#160;&#160;&#160;I found </span>'
        f'            <a href="/tool/{_hero_tool_slug}" style="color:var(--slate);font-weight:700;text-decoration:underline;text-decoration-style:dotted;text-underline-offset:3px;">{_hero_tool_name}</a>'
        '            <span style="color:rgba(255,255,255,0.85);"> on IndieStack.</span><br>'
        '            <span style="color:rgba(255,255,255,0.85);">&#160;&#160;&#160;&#160;&#160;Use it instead?&rdquo;</span>'
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
        f'    <div style="display:inline-flex;flex-wrap:wrap;gap:8px 16px;justify-content:center;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);'
        f'                border-radius:var(--radius-sm);padding:12px 24px;font-size:14px;color:var(--ink-light);'
        f'                backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);">'
        f'        <span>{tool_count} tools</span>'
        f'        <span style="color:var(--border);">|</span>'
        f'        <span>{maker_count} makers</span>'
        f'        <span style="color:var(--border);">|</span>'
        f'        <span style="color:var(--accent);">{ai_recs:,} AI recommendations</span>'
        f'    </div>'
        + (
            '<div style="margin-top:16px;display:flex;flex-wrap:wrap;gap:8px;justify-content:center;align-items:center;">'
            '    <span style="font-size:13px;color:var(--ink-muted);margin-right:4px;">Popular searches:</span>'
            + ' '.join(
                f'<a href="/search?q={escape(t["query"])}" style="display:inline-flex;align-items:center;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);'
                f'padding:6px 12px;border-radius:999px;font-size:13px;color:var(--ink-light);text-decoration:none;min-height:32px;transition:border-color 0.15s ease;">'
                f'{escape(t["query"])}</a>'
                for t in search_trends[:5]
            )
            + '</div>'
        if search_trends else '') +
        f'    <div style="margin-top:16px;">'
        f'        <a href="/submit" class="btn btn-slate" style="padding:12px 24px;font-size:14px;">Add Your Tool &rarr;</a>'
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
            <p style="text-align:center;color:var(--ink-muted);font-size:16px;margin-bottom:16px;max-width:520px;margin-left:auto;margin-right:auto;">
                Three steps. Your AI stops reinventing the wheel.
            </p>
            <p style="text-align:center;font-size:13px;color:var(--ink-light);margin-bottom:48px;max-width:480px;margin-left:auto;margin-right:auto;">
                MCP (Model Context Protocol) lets AI assistants like Claude and Cursor use external tools.
                IndieStack&rsquo;s MCP server gives your AI access to 900+ indie tools &mdash; so it finds existing solutions instead of coding from scratch.
            </p>

            <!-- 3-step flow -->
            <div class="card-stagger" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:40px;margin-bottom:48px;">
                <div style="text-align:center;">
                    <div style="width:40px;height:40px;border-radius:50%;background:var(--accent);color:white;
                                display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;
                                margin:0 auto 16px;">1</div>
                    <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin-bottom:8px;">Install</h3>
                    <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                        One command. Works with Claude&nbsp;Code, Cursor, and Windsurf.
                    </p>
                </div>
                <div style="text-align:center;">
                    <div style="width:40px;height:40px;border-radius:50%;background:var(--accent);color:white;
                                display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;
                                margin:0 auto 16px;">2</div>
                    <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin-bottom:8px;">Your AI searches</h3>
                    <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                        When you ask your AI to build something, it checks IndieStack first.
                    </p>
                </div>
                <div style="text-align:center;">
                    <div style="width:40px;height:40px;border-radius:50%;background:var(--accent);color:white;
                                display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;
                                margin:0 auto 16px;">3</div>
                    <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin-bottom:8px;">It recommends real tools</h3>
                    <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                        Instead of writing 50k tokens of code, your AI suggests a vetted indie tool &mdash; and learns your preferences over time.
                    </p>
                </div>
            </div>

            <!-- Install cards -->
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:24px;margin-bottom:32px;">
                <div class="card" style="padding:24px;border-left:3px solid var(--slate);">
                    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:8px;">Claude Code</h3>
                    <code style="font-family:var(--font-mono);font-size:12px;color:var(--ink-muted);word-break:break-all;">claude mcp add indiestack -- uvx --from indiestack indiestack-mcp</code>
                </div>
                <div class="card" style="padding:24px;border-left:3px solid var(--slate);">
                    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:8px;">Cursor / Windsurf</h3>
                    <code style="font-family:var(--font-mono);font-size:11px;color:var(--ink-muted);word-break:break-all;">Add to .cursor/mcp.json or mcp_config.json</code>
                </div>
                <div class="card" style="padding:24px;border-left:3px solid var(--slate);">
                    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin-bottom:8px;">VS Code Copilot</h3>
                    <code style="font-family:var(--font-mono);font-size:11px;color:var(--ink-muted);word-break:break-all;">Add to .vscode/mcp.json</code>
                </div>
            </div>

            <!-- Quick install block -->
            <div style="max-width:600px;margin:0 auto 32px;">
                <p style="font-size:14px;font-weight:600;color:var(--ink);margin-bottom:8px;">Quick install:</p>
                <div style="background:var(--ink);color:var(--slate);border-radius:var(--radius-sm);padding:16px 24px;
                            font-family:var(--font-mono);font-size:13px;line-height:1.8;overflow-x:auto;">
                    <span style="color:var(--ink-muted);"># Claude Code (one command)</span><br>
                    claude mcp add indiestack -- uvx --from indiestack indiestack-mcp<br><br>
                    <span style="color:var(--ink-muted);"># Cursor / Windsurf / VS Code — add to mcp config:</span><br>
                    {{"command": "uvx", "args": ["--from", "indiestack", "indiestack-mcp"]}}
                </div>
            </div>

            <!-- Personalization note -->
            <div style="max-width:560px;margin:0 auto 32px;padding:20px 24px;background:var(--card-bg);
                        border:1px solid var(--border);border-radius:var(--radius-sm);text-align:center;">
                <p style="font-size:14px;color:var(--ink);margin-bottom:4px;font-weight:600;">
                    &#10024; It gets smarter the more you use it
                </p>
                <p style="font-size:13px;color:var(--ink-muted);margin-bottom:12px;line-height:1.6;">
                    Add a free API key and the MCP server learns what you build &mdash; personalised recommendations, no raw queries stored.
                </p>
                <a href="/developer" style="font-size:13px;color:var(--accent);font-weight:600;text-decoration:none;">
                    Get your API key &rarr;
                </a>
            </div>

            <!-- Proof stats -->
            <div style="display:flex;flex-wrap:wrap;gap:8px 24px;justify-content:center;font-size:14px;color:var(--ink-muted);">
                <span><strong style="color:var(--accent);">{ai_recs:,}</strong> AI recommendations</span>
                <span style="color:var(--border);">&middot;</span>
                <span><strong style="color:var(--ink);">{tool_count}</strong> tools</span>
                <span style="color:var(--border);">&middot;</span>
                <span><strong style="color:var(--ink);">{maker_count}</strong> makers</span>
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
            <p style="text-align:center;color:var(--ink-muted);font-size:16px;margin-bottom:24px;">
                Search our catalog &mdash; your AI already does.
            </p>
            <div style="display:flex;gap:8px;max-width:560px;margin:0 auto;">
                <input type="text" id="landing-search"
                       placeholder="e.g. invoicing, analytics, auth..."
                       style="flex:1;padding:16px 16px;font-size:16px;font-family:var(--font-body);
                              border:1px solid rgba(255,255,255,0.1);border-radius:var(--radius-sm);
                              background:rgba(0,0,0,0.2);color:var(--ink);outline:none;
                              box-shadow:inset 0 2px 4px rgba(0,0,0,0.2);"
                       class="form-input">
                <button id="landing-search-btn" class="btn btn-primary"
                        style="padding:16px 24px;font-size:16px;white-space:nowrap;cursor:pointer;">
                    Search
                </button>
            </div>
            <div id="landing-search-results" style="max-width:560px;margin:16px auto 0;"></div>
            <div id="landing-search-empty" style="display:none;max-width:560px;margin:16px auto 0;text-align:center;
                                                   padding:24px;background:var(--cream-dark);border-radius:var(--radius-sm);">
                <p style="color:var(--ink-muted);font-size:15px;margin-bottom:12px;">
                    No indie tool for that yet &mdash; sounds like a gap worth filling.
                </p>
                <a href="/submit" class="btn btn-primary" style="padding:12px 24px;font-size:14px;">
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
                        return '<a href="/tool/'+t.indiestack_url.split("/tool/")[1]+'" style="display:flex;align-items:center;gap:16px;'+
                            'padding:16px 24px;text-decoration:none;color:inherit;background:var(--card-bg);'+
                            'border:1px solid var(--border);border-radius:var(--radius-sm);margin-bottom:8px;'+
                            'transition:border-color 0.15s;" onmouseenter="this.style.borderColor=\\'var(--accent)\\'" '+
                            'onmouseleave="this.style.borderColor=\\'var(--border)\\'">'+
                            '<div style="flex:1;min-width:0;">'+
                            '<div style="font-family:var(--font-display);font-size:16px;color:var(--ink);">'+t.name+'</div>'+
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
            f'   style="display:flex;align-items:center;gap:12px;padding:12px 16px;'
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
        <h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:24px;color:var(--ink);">Browse by category</h2>
        <div class="cat-compact-grid card-stagger">{cat_items}</div>
    </section>
    """

    # ── Maker CTA ────────────────────────────────────────────────────
    maker_cta = f"""
    <section style="text-align:center;padding:48px 24px;background:var(--terracotta);color:white;">
        <p style="font-family:var(--font-display);font-size:clamp(24px,3.5vw,32px);margin-bottom:8px;">
            {maker_count}+ makers already listed
        </p>
        <p style="color:rgba(255,255,255,0.7);font-size:16px;margin-bottom:24px;max-width:440px;margin-left:auto;margin-right:auto;">
            List your tool for free. AI agents and developers will find it.
        </p>
        <a href="/submit" class="btn" style="background:var(--slate);color:var(--terracotta-dark);font-weight:700;
                                              padding:16px 32px;font-size:16px;">
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
        '.hero-headline{background:linear-gradient(135deg,var(--slate) 0%,var(--terracotta) 100%);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}'
        '[data-theme="dark"] .hero-headline{background:linear-gradient(135deg,var(--slate) 0%,#fff 100%);'
        '-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;}'
        '.hero-glow{position:relative;}'
        '.hero-glow::before{content:\'\';position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);'
        'width:800px;height:800px;background:radial-gradient(circle,rgba(64,232,255,0.15) 0%,rgba(64,232,255,0.05) 40%,transparent 70%);'
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

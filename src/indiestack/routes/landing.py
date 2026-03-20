"""Landing page — MCP-first product story with interactive search."""

import os
import time as _time
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell, tool_card
from indiestack.routes.category_icons import category_icon
from indiestack.db import get_all_categories, get_trending_scored, get_showcase_tools, get_search_stats, get_search_trends, get_search_gaps

router = APIRouter()

# Junk query filter for demand gaps (mirrors gaps.py)
_GAP_BLOCKLIST = {
    'xbox game pass', 'akoraimagbuot', 'wace', 'test', 'asdf', 'hello',
    'indiestack', 'xxx', 'porn', 'sex', '{search_term_string}',
}

def _is_valid_gap(query: str) -> bool:
    q = query.strip().lower()
    if len(q) < 3 or len(q) > 60:
        return False
    if q in _GAP_BLOCKLIST:
        return False
    if not any(c.isalpha() for c in q):
        return False
    return True

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
        category_count = len(categories)
        ai_recs = cached.get('ai_recs', 0)
        search_stats = cached.get('search_stats', {'this_week': 0})
        search_trends = cached.get('search_trends', [])
        claimed_count = cached.get('claimed_count', 0)
        today_ai_count = cached.get('today_ai_count', 0)
        featured = cached.get('featured', None)
        demand_gaps = cached.get('demand_gaps', [])
    else:
        _tc = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")
        tool_count = (await _tc.fetchone())['cnt']
        _cc = await db.execute("SELECT COUNT(*) as cnt FROM categories")
        cat_count = (await _cc.fetchone())['cnt']
        _mc = await db.execute("SELECT COUNT(*) as cnt FROM makers")
        maker_count = (await _mc.fetchone())['cnt']
        trending = await get_showcase_tools(db, limit=6)
        categories = await get_all_categories(db)
        category_count = len(categories)
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

        # Fetch demand gaps for the teaser (top 4 valid gaps)
        raw_gaps = await get_search_gaps(db, limit=20)
        demand_gaps = [g for g in raw_gaps if _is_valid_gap(g['query'])][:4]

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
            'demand_gaps': demand_gaps,
        }
        _landing_cache['expires'] = _time.time() + 300  # 5 minutes

    # ── Top Banner (removed — duplicated hero content) ──────────────

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
        '<section id="hero-section" style="text-align:center;padding:64px 24px 48px;'
        '                background:var(--cream);">'
        '    <div>'
        '    <div class="status-tag" style="margin-bottom:24px;justify-content:center;">'
        '        <span class="dot"></span>DISCOVERY LAYER FOR AI CODING AGENTS'
        '    </div>'
        '    <h1 style="font-family:var(--font-display);font-size:clamp(36px,6vw,64px);'
        '               line-height:1.15;max-width:700px;margin:0 auto;color:var(--ink);letter-spacing:-0.03em;">'
        '        <span class="hero-headline">The discovery layer for AI coding agents.</span>'
        '    </h1>'
        '    <p style="font-size:20px;color:var(--ink-muted);max-width:560px;margin:16px auto 32px;line-height:1.6;">'
        f'        {tool_count}+ developer tools your AI can discover, compare, and recommend &mdash; so it stops reinventing the wheel.'
        '    </p>'
        # Hero visual — code conversation block
        '    <div style="max-width:560px;margin:0 auto 24px;text-align:left;background:rgba(10,14,26,0.8);'
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
        f'    <p style="font-size:12px;color:var(--ink-muted);margin-top:8px;margin-bottom:0;">'
        f'        &#9733; <a href="/tool/{_hero_tool_slug}" style="color:var(--accent);text-decoration:none;font-weight:600;">{_hero_tool_name}</a> is this week&rsquo;s Pick of the Week &mdash; featured right here.'
        f'    </p>'
        # Inline install command in hero
        '    <div style="max-width:500px;margin:0 auto 16px;">'
        '        <div style="display:flex;align-items:center;gap:12px;padding:12px 16px;border:1px solid rgba(255,255,255,0.12);border-radius:var(--radius-sm);'
        '                    font-family:var(--font-mono);font-size:12px;color:var(--slate);overflow:hidden;">'
        '            <code style="flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
        '                claude mcp add indiestack -- uvx --from indiestack indiestack-mcp'
        '            </code>'
        '            <button onclick="navigator.clipboard.writeText(\'claude mcp add indiestack -- uvx --from indiestack indiestack-mcp\');this.textContent=\'Copied!\';setTimeout(()=>this.textContent=\'Copy\',2000)"'
        '                    style="background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);color:var(--slate);'
        '                           padding:6px 14px;border-radius:var(--radius-sm);font-size:12px;cursor:pointer;'
        '                           min-height:44px;min-width:44px;font-family:var(--font-body);white-space:nowrap;">Copy</button>'
        '        </div>'
        '    </div>'
        # CTAs
        '    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin-bottom:24px;margin-top:16px;">'
        '        <a href="/signup?next=/welcome" class="btn btn-lg btn-primary landing-neon">'
        '            Get Started Free'
        '        </a>'
        '        <a href="/explore" class="btn btn-lg btn-secondary">'
        '            Browse the Catalog'
        '        </a>'
        '    </div>'
        + f'    <p style="font-size:13px;color:var(--ink-light);margin-top:16px;">'
        f'        {tool_count}+ tools &middot; {ai_recs:,}+ AI recommendations'
        f'    </p>'
        '    </div>'  # close content wrapper
        '</section>'
    )

    # ── Video Section (disabled — waiting for better video) ──────────
    video_section = ""

    # ── Stats Bar (removed — duplicated hero) ──────────────────────
    stats_bar = ""

    # ── MCP Walkthrough (simplified) ────────────────────────────────
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
                <div style="text-align:center;padding:24px;">
                    <div style="width:40px;height:40px;border-radius:50%;background:var(--accent);color:white;
                                display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;
                                margin:0 auto 16px;">1</div>
                    <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin-bottom:8px;">Install</h3>
                    <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                        One command. Works with Claude&nbsp;Code, Cursor, and Windsurf.
                    </p>
                </div>
                <div style="text-align:center;padding:24px;">
                    <div style="width:40px;height:40px;border-radius:50%;background:var(--accent);color:white;
                                display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;
                                margin:0 auto 16px;">2</div>
                    <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin-bottom:8px;">Your AI searches</h3>
                    <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                        When you ask your AI to build something, it checks IndieStack first.
                    </p>
                </div>
                <div style="text-align:center;padding:24px;">
                    <div style="width:40px;height:40px;border-radius:50%;background:var(--accent);color:white;
                                display:flex;align-items:center;justify-content:center;font-weight:700;font-size:16px;
                                margin:0 auto 16px;">3</div>
                    <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin-bottom:8px;">It finds what exists</h3>
                    <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;">
                        Instead of writing 50k tokens of code, your AI suggests a vetted tool.
                    </p>
                </div>
            </div>

            <!-- Install code block -->
            <div style="max-width:600px;margin:0 auto;">
                <div style="color:var(--slate);border-radius:var(--radius-sm);padding:16px 24px;border:1px solid rgba(255,255,255,0.12);
                            background:rgba(10,14,26,0.6);font-family:var(--font-mono);font-size:13px;line-height:1.8;overflow-x:auto;">
                    <span style="color:var(--ink-muted);"># Claude Code (one command)</span><br>
                    claude mcp add indiestack -- uvx --from indiestack indiestack-mcp<br><br>
                    <span style="color:var(--ink-muted);"># Cursor / Windsurf / VS Code — add to mcp config:</span><br>
                    {{"command": "uvx", "args": ["--from", "indiestack", "indiestack-mcp"]}}
                </div>
                <p style="text-align:center;font-size:13px;color:var(--ink-light);margin-top:12px;">
                    Want more queries? <a href="/developer" style="color:var(--accent);text-decoration:none;">Get a free API key</a> for 10/month &rarr;
                </p>
            </div>
        </div>
    </section>
    """

    build_vs_buy = ""

    # ── "Try it yourself" Search Widget ────────────────────────────────
    search_widget = """
    <section style="padding:64px 24px;">
        <div class="container" style="max-width:600px;">
            <h2 style="font-family:var(--font-display);font-size:clamp(22px,3vw,28px);text-align:center;margin-bottom:8px;color:var(--ink);">
                Try it yourself
            </h2>
            <p style="text-align:center;color:var(--ink-muted);font-size:16px;margin-bottom:24px;">
                Search like your AI agent does. Pick one or type your own.
            </p>
            <div style="display:flex;gap:8px;max-width:560px;margin:0 auto;">
                <input type="text" id="landing-search"
                       placeholder="e.g. invoicing, design, games..."
                       style="flex:1;padding:16px 16px;font-size:16px;font-family:var(--font-body);
                              border:1px solid rgba(255,255,255,0.08);border-radius:var(--radius-sm);
                              background:rgba(255,255,255,0.03);backdrop-filter:blur(16px);-webkit-backdrop-filter:blur(16px);
                              color:var(--ink);outline:none;
                              box-shadow:inset 0 2px 4px rgba(0,0,0,0.2);"
                       class="form-input">
                <button id="landing-search-btn" class="btn btn-primary landing-neon"
                        style="padding:16px 24px;font-size:16px;white-space:nowrap;cursor:pointer;">
                    Search
                </button>
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;max-width:560px;margin:12px auto 0;">
                <button class="search-pill" onclick="document.getElementById('landing-search').value='analytics';document.getElementById('landing-search-btn').click();"
                        style="padding:6px 16px;font-size:13px;font-family:var(--font-body);background:rgba(255,255,255,0.05);
                               border:1px solid rgba(255,255,255,0.1);border-radius:999px;color:var(--ink-muted);cursor:pointer;
                               transition:all 0.15s;"
                        onmouseenter="this.style.borderColor='var(--accent)';this.style.color='var(--accent)'"
                        onmouseleave="this.style.borderColor='rgba(255,255,255,0.1)';this.style.color='var(--ink-muted)'">analytics</button>
                <button class="search-pill" onclick="document.getElementById('landing-search').value='design';document.getElementById('landing-search-btn').click();"
                        style="padding:6px 16px;font-size:13px;font-family:var(--font-body);background:rgba(255,255,255,0.05);
                               border:1px solid rgba(255,255,255,0.1);border-radius:999px;color:var(--ink-muted);cursor:pointer;
                               transition:all 0.15s;"
                        onmouseenter="this.style.borderColor='var(--accent)';this.style.color='var(--accent)'"
                        onmouseleave="this.style.borderColor='rgba(255,255,255,0.1)';this.style.color='var(--ink-muted)'">design</button>
                <button class="search-pill" onclick="document.getElementById('landing-search').value='invoicing';document.getElementById('landing-search-btn').click();"
                        style="padding:6px 16px;font-size:13px;font-family:var(--font-body);background:rgba(255,255,255,0.05);
                               border:1px solid rgba(255,255,255,0.1);border-radius:999px;color:var(--ink-muted);cursor:pointer;
                               transition:all 0.15s;"
                        onmouseenter="this.style.borderColor='var(--accent)';this.style.color='var(--accent)'"
                        onmouseleave="this.style.borderColor='rgba(255,255,255,0.1)';this.style.color='var(--ink-muted)'">invoicing</button>
                <button class="search-pill" onclick="document.getElementById('landing-search').value='newsletter';document.getElementById('landing-search-btn').click();"
                        style="padding:6px 16px;font-size:13px;font-family:var(--font-body);background:rgba(255,255,255,0.05);
                               border:1px solid rgba(255,255,255,0.1);border-radius:999px;color:var(--ink-muted);cursor:pointer;
                               transition:all 0.15s;"
                        onmouseenter="this.style.borderColor='var(--accent)';this.style.color='var(--accent)'"
                        onmouseleave="this.style.borderColor='rgba(255,255,255,0.1)';this.style.color='var(--ink-muted)'">newsletter</button>
            </div>
            <div id="landing-search-results" style="max-width:560px;margin:16px auto 0;"></div>
            <div id="landing-search-empty" style="display:none;max-width:560px;margin:16px auto 0;text-align:center;
                                                   padding:24px;background:var(--cream-dark);border-radius:var(--radius-sm);">
                <p style="color:var(--ink-muted);font-size:15px;margin-bottom:12px;">
                    Nothing indie-built for that yet &mdash; sounds like a gap worth filling.
                </p>
                <a href="/submit" class="btn btn-primary" style="padding:12px 24px;font-size:14px;">
                    Submit yours &rarr;
                </a>
            </div>
        </div>
    </section>
    <script>
    function esc(s){if(!s)return '';var d=document.createElement('div');d.textContent=s;return d.innerHTML;}
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
                            '<div style="font-family:var(--font-display);font-size:16px;color:var(--ink);">'+esc(t.name)+'</div>'+
                            '<div style="font-size:13px;color:var(--ink-muted);margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'+esc(t.tagline)+'</div>'+
                            '</div>'+
                            '<span style="font-size:13px;font-weight:600;color:var(--ink-light);white-space:nowrap;">'+esc(t.price)+'</span>'+
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
        trending_cards = "\n".join(tool_card(t, compact=True) for t in trending[:6])
        trending_strip = f"""
        <section class="container" style="padding:48px 24px;">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:16px;">
                <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);">Trending right now</h2>
                <a href="/explore" style="color:var(--terracotta);font-size:14px;font-weight:600;text-decoration:none;">
                    Browse all &rarr;
                </a>
            </div>
            <div class="scroll-row">{trending_cards}</div>
        </section>
        """

    # ── Compact Category Grid (top 8) ────────────────────────────────
    _top_cats = sorted(categories, key=lambda c: c.get('tool_count', 0), reverse=True)[:8]
    cat_items = ''
    for c in _top_cats:
        count = c.get('tool_count', 0)
        cat_items += (
            f'<a href="/category/{escape(str(c["slug"]))}" class="cat-compact-item"'
            f'   style="display:flex;align-items:center;gap:12px;padding:12px 16px;'
            f'   border:1px solid var(--border);border-radius:var(--radius-sm);'
            f'   text-decoration:none;color:inherit;transition:background 0.15s;"'
            f'   onmouseenter="this.style.background=\'rgba(255,255,255,0.03)\';this.style.borderColor=\'rgba(0,212,245,0.3)\';this.style.backdropFilter=\'blur(16px)\'"'
            f'   onmouseleave="this.style.background=\'transparent\';this.style.borderColor=\'var(--border)\';this.style.backdropFilter=\'none\'">'
            f'  <span style="flex-shrink:0;color:var(--slate);display:flex;align-items:center;">{category_icon(c["slug"])}</span>'
            f'  <span style="font-size:14px;font-weight:600;color:var(--ink);flex:1;">{escape(str(c["name"]))}</span>'
            f'  <span style="font-size:12px;color:var(--ink-muted);">&rarr;</span>'
            f'</a>'
        )

    categories_compact = f"""
    <section class="container" style="padding:48px 24px;">
        <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:24px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);">Browse by category</h2>
            <a href="/explore" style="color:var(--accent);font-size:14px;font-weight:600;text-decoration:none;">
                All {category_count} categories &rarr;
            </a>
        </div>
        <div class="cat-compact-grid">{cat_items}</div>
    </section>
    """

    # ── Maker CTA (slim) ────────────────────────────────────────────
    maker_cta = (
        '<div style="text-align:center;padding:32px 24px 48px;">'
        '  <p style="font-size:14px;color:var(--ink-muted);">'
        '    Built something indie? <a href="/submit" style="color:var(--accent);font-weight:600;text-decoration:none;">Submit your tool</a> &rarr;'
        '  </p>'
        '</div>'
    )

    # ── Assembly ─────────────────────────────────────────────────────
    def _reveal(html):
        return f'<div class="reveal">{html}</div>'

    body = hero + stats_bar + _reveal(video_section) + _reveal(mcp_walkthrough) + _reveal(build_vs_buy) + _reveal(search_widget) + _reveal(trending_strip) + _reveal(categories_compact) + _reveal(maker_cta)

    import json as _json
    website_ld = _json.dumps({
        "@context": "https://schema.org",
        "@type": "WebSite",
        "name": "IndieStack",
        "url": BASE_URL,
        "description": f"The discovery layer between AI coding agents and developer tools. Search {tool_count}+ tools before building from scratch.",
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
        '.cat-compact-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}'
        '@media(max-width:768px){.cat-compact-grid{grid-template-columns:repeat(2,1fr);}}'
        '@media(max-width:480px){.cat-compact-grid{grid-template-columns:1fr;}}'
        '/* System status tag */'
        '.status-tag{display:inline-flex;align-items:center;gap:8px;font-family:var(--font-mono);text-transform:uppercase;letter-spacing:0.15em;font-size:11px;font-weight:600;color:#1A2D4A;}'
        '[data-theme="dark"] .status-tag{color:rgba(255,255,255,0.5);}'
        '.status-tag .dot{width:6px;height:6px;border-radius:50%;background:var(--slate);animation:status-pulse 2s ease-in-out infinite;}'
        '@keyframes status-pulse{0%,100%{opacity:1;box-shadow:0 0 8px rgba(0,212,245,0.6)}50%{opacity:0.4;box-shadow:0 0 2px rgba(0,212,245,0.2)}}'
        '/* Neon primary button override for landing */'
        '.landing-neon{box-shadow:0 0 30px rgba(0,212,245,0.3);transition:all 0.3s cubic-bezier(0.4,0,0.2,1);}'
        '.landing-neon:hover{box-shadow:0 0 50px rgba(0,212,245,0.5);transform:translateY(-2px);}'
        '/* Float animation */'
        '@keyframes float-gentle{0%,100%{transform:translateY(0)}50%{transform:translateY(-8px)}}'
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

    response = HTMLResponse(page_shell("The discovery layer for AI coding agents", body,
                                   description="IndieStack plugs into Claude, Cursor, and Windsurf. Before your AI builds from scratch, it checks if a developer tool already exists.",
                                   user=request.state.user, canonical="/", extra_head=extra_head,
                                   og_image=f"{BASE_URL}/logo.png"))
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response

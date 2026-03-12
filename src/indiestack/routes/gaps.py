"""Demand Bounty Board — real-time demand signals from AI agents."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from html import escape
from urllib.parse import quote
from datetime import datetime, timezone

from indiestack.routes.components import page_shell
from indiestack.db import get_search_gaps, get_search_demand, get_demand_trends, get_demand_clusters

router = APIRouter()

# Junk queries to filter out (typos, nonsense, non-tool searches)
_BLOCKLIST = {
    'xbox game pass', 'akoraimagbuot', 'wace', 'test', 'asdf', 'hello',
    'indiestack', 'xxx', 'porn', 'sex',
}


def _is_valid_gap(query: str) -> bool:
    """Filter out junk queries that aren't real tool gaps."""
    q = query.strip().lower()
    if len(q) < 3 or len(q) > 60:
        return False
    if q in _BLOCKLIST:
        return False
    # Filter out queries that are just random characters
    if not any(c.isalpha() for c in q):
        return False
    return True


def _relative_time(timestamp: str) -> str:
    """Convert a timestamp string to relative time like '2 hours ago'."""
    if not timestamp:
        return ''
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        now = datetime.now(timezone.utc)
        diff = now - dt
        seconds = int(diff.total_seconds())
        if seconds < 60:
            return 'just now'
        minutes = seconds // 60
        if minutes < 60:
            return f'{minutes} min{"s" if minutes != 1 else ""} ago'
        hours = minutes // 60
        if hours < 24:
            return f'{hours} hour{"s" if hours != 1 else ""} ago'
        days = hours // 24
        if days < 30:
            return f'{days} day{"s" if days != 1 else ""} ago'
        months = days // 30
        return f'{months} month{"s" if months != 1 else ""} ago'
    except (ValueError, TypeError):
        return timestamp[:10] if len(timestamp) >= 10 else timestamp


@router.get("/gaps", response_class=HTMLResponse)
async def gaps_page(request: Request):
    user = request.state.user
    db = request.state.db

    # Get all zero-result searches, then filter
    raw_gaps = await get_search_gaps(db, limit=100)
    gaps = [g for g in raw_gaps if _is_valid_gap(g['query'])][:30]

    # Stats
    total_gaps = len(gaps)
    total_searches = sum(g['count'] for g in gaps) if gaps else 0

    # Build gap cards
    gap_cards = ''
    for gap in gaps:
        query = escape(gap['query'])
        count = gap['count']
        last = gap.get('last_searched', '')
        last_display = _relative_time(last)

        # Demand tier badge
        if count >= 10:
            badge_label = 'HIGH DEMAND'
            badge_bg = 'var(--error-bg, rgba(239,68,68,0.12))'
            badge_color = 'var(--error-text, #EF4444)'
        elif count >= 5:
            badge_label = 'GROWING'
            badge_bg = 'var(--warning-bg, rgba(226,183,100,0.12))'
            badge_color = 'var(--warning-text, #E2B764)'
        elif count >= 2:
            badge_label = 'EMERGING'
            badge_bg = 'var(--info-bg, rgba(0,212,245,0.12))'
            badge_color = 'var(--info-text, #00D4F5)'
        else:
            badge_label = 'NEW SIGNAL'
            badge_bg = 'var(--bg-card, rgba(255,255,255,0.04))'
            badge_color = 'var(--ink-muted)'

        gap_cards += f'''
        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:24px;
                    display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;
                    transition:border-color 0.2s;">
            <div style="flex:1;min-width:220px;">
                <div style="display:flex;align-items:center;gap:12px;margin-bottom:10px;flex-wrap:wrap;">
                    <span style="font-family:var(--heading-font, var(--font-display));font-size:18px;font-weight:600;color:var(--ink);">
                        {query}
                    </span>
                    <span style="display:inline-block;padding:3px 10px;border-radius:999px;font-size:11px;
                                 font-weight:700;letter-spacing:0.5px;background:{badge_bg};color:{badge_color};">
                        {badge_label}
                    </span>
                </div>
                <div style="display:flex;gap:16px;font-size:13px;color:var(--ink-muted);flex-wrap:wrap;">
                    <span><strong style="color:var(--ink);">{count}</strong> agent search{"es" if count != 1 else ""}</span>
                    {f'<span style="color:var(--border);">&middot;</span><span>Last searched {last_display}</span>' if last_display else ''}
                </div>
            </div>
            <div style="flex-shrink:0;text-align:right;">
                <a href="/submit?name={quote(gap['query'])}"
                   style="display:inline-block;padding:10px 20px;background:var(--accent);color:white;
                          border-radius:8px;font-size:14px;font-weight:600;text-decoration:none;
                          white-space:nowrap;transition:opacity 0.2s;">
                    Build This &rarr;
                </a>
                <div style="font-size:11px;color:var(--ink-muted);margin-top:6px;">
                    Guaranteed distribution to AI agents
                </div>
            </div>
        </div>'''

    # Hero section
    hero = f'''
    <section style="padding:64px 24px 32px;text-align:center;">
        <div class="container" style="max-width:740px;">
            <p style="font-size:13px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
                Live from the IndieStack MCP Server
            </p>
            <h1 style="font-family:var(--heading-font, var(--font-display));font-size:clamp(28px,4vw,42px);color:var(--ink);margin-bottom:16px;line-height:1.2;">
                Demand Bounty Board
            </h1>
            <p style="font-size:17px;color:var(--ink-muted);max-width:600px;margin:0 auto 32px;line-height:1.6;">
                Real-time demand signals from AI agents. These tools were searched for and couldn&rsquo;t be found.
                Build one and get instant distribution.
            </p>
        </div>
    </section>
    '''

    # Stats bar
    stats_bar = f'''
    <section style="padding:0 24px 40px;">
        <div class="container" style="max-width:740px;">
            <div style="display:flex;gap:1px;background:var(--border);border-radius:12px;overflow:hidden;
                        border:1px solid var(--border);">
                <div style="flex:1;background:var(--bg-card);padding:20px 24px;text-align:center;">
                    <div style="font-family:var(--heading-font, var(--font-display));font-size:28px;font-weight:700;color:var(--accent);margin-bottom:4px;">
                        {total_gaps}
                    </div>
                    <div style="font-size:13px;color:var(--ink-muted);">Unfilled Gaps</div>
                </div>
                <div style="flex:1;background:var(--bg-card);padding:20px 24px;text-align:center;">
                    <div style="font-family:var(--heading-font, var(--font-display));font-size:28px;font-weight:700;color:var(--accent);margin-bottom:4px;">
                        {total_searches}
                    </div>
                    <div style="font-size:13px;color:var(--ink-muted);">Failed Agent Searches</div>
                </div>
                <div style="flex:1;background:var(--bg-card);padding:20px 24px;text-align:center;">
                    <div style="font-size:14px;font-weight:600;color:var(--ink);line-height:1.4;">
                        Every gap = guaranteed AI recommendations when filled
                    </div>
                </div>
            </div>
        </div>
    </section>
    '''

    # Gap list
    gap_list = f'''
    <section style="padding:0 24px 64px;">
        <div class="container" style="max-width:740px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;">
                <h2 style="font-family:var(--heading-font, var(--font-display));font-size:22px;color:var(--ink);">Open Bounties</h2>
                <span style="font-size:13px;color:var(--ink-muted);">Sorted by demand</span>
            </div>
            <div style="display:flex;flex-direction:column;gap:12px;">
                {gap_cards if gap_cards else '<p style="color:var(--ink-muted);text-align:center;padding:40px;">No gaps detected yet. As more AI agents use the MCP server, bounties will appear here.</p>'}
            </div>
        </div>
    </section>
    '''

    # How it works
    how_it_works = '''
    <section style="padding:0 24px 64px;">
        <div class="container" style="max-width:740px;">
            <h2 style="font-family:var(--heading-font, var(--font-display));font-size:22px;color:var(--ink);text-align:center;margin-bottom:32px;">
                How It Works
            </h2>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:20px;">
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:24px 20px;text-align:center;">
                    <div style="width:36px;height:36px;border-radius:999px;background:var(--accent);color:white;
                                display:inline-flex;align-items:center;justify-content:center;font-weight:700;
                                font-size:16px;margin-bottom:12px;">1</div>
                    <p style="font-size:14px;font-weight:600;color:var(--ink);margin-bottom:4px;">Agent Searches</p>
                    <p style="font-size:13px;color:var(--ink-muted);line-height:1.5;">AI agents search IndieStack for tools</p>
                </div>
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:24px 20px;text-align:center;">
                    <div style="width:36px;height:36px;border-radius:999px;background:var(--accent);color:white;
                                display:inline-flex;align-items:center;justify-content:center;font-weight:700;
                                font-size:16px;margin-bottom:12px;">2</div>
                    <p style="font-size:14px;font-weight:600;color:var(--ink);margin-bottom:4px;">Gap Logged</p>
                    <p style="font-size:13px;color:var(--ink-muted);line-height:1.5;">When they find nothing, the search is logged here</p>
                </div>
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:24px 20px;text-align:center;">
                    <div style="width:36px;height:36px;border-radius:999px;background:var(--accent);color:white;
                                display:inline-flex;align-items:center;justify-content:center;font-weight:700;
                                font-size:16px;margin-bottom:12px;">3</div>
                    <p style="font-size:14px;font-weight:600;color:var(--ink);margin-bottom:4px;">You Build It</p>
                    <p style="font-size:13px;color:var(--ink-muted);line-height:1.5;">You build the tool and submit it to IndieStack</p>
                </div>
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:24px 20px;text-align:center;">
                    <div style="width:36px;height:36px;border-radius:999px;background:var(--accent);color:white;
                                display:inline-flex;align-items:center;justify-content:center;font-weight:700;
                                font-size:16px;margin-bottom:12px;">4</div>
                    <p style="font-size:14px;font-weight:600;color:var(--ink);margin-bottom:4px;">Instant Distribution</p>
                    <p style="font-size:13px;color:var(--ink-muted);line-height:1.5;">Every agent that searches next will recommend YOUR creation</p>
                </div>
            </div>
        </div>
    </section>
    '''

    # CTA
    cta = '''
    <section style="padding:48px 24px;background:var(--cream-dark);">
        <div class="container" style="max-width:600px;text-align:center;">
            <h2 style="font-family:var(--heading-font, var(--font-display));font-size:24px;color:var(--ink);margin-bottom:12px;">
                Built something that fills a gap?
            </h2>
            <p style="font-size:15px;color:var(--ink-muted);margin-bottom:24px;line-height:1.6;">
                Submit your creation and it&rsquo;ll start showing up in AI recommendations immediately.
                You&rsquo;ll get a live badge showing how many times agents recommend it.
            </p>
            <a href="/submit" class="btn btn-primary" style="padding:14px 32px;font-size:15px;">
                Submit Your Creation &rarr;
            </a>
        </div>
    </section>
    '''

    body = hero + stats_bar + gap_list + how_it_works + cta

    return HTMLResponse(page_shell(
        title="Demand Bounty Board — Tools AI Agents Are Searching For | IndieStack",
        body=body,
        user=user,
        description="Real-time demand signals from AI agents. See what tools were searched for and couldn't be found. Build one and get instant distribution.",
    ))


@router.get("/demand", response_class=HTMLResponse)
async def demand_pro(request: Request):
    """Pro demand signal dashboard — paid tier."""
    user = request.state.user
    db = request.state.db

    # Check if user has active demand_pro (or pro) subscription
    is_pro = False
    if user:
        cursor = await db.execute(
            "SELECT id FROM subscriptions WHERE user_id = ? AND status = 'active' AND plan IN ('demand_pro', 'pro')",
            (user['id'],),
        )
        sub = await cursor.fetchone()
        if sub:
            is_pro = True

    if not is_pro:
        # Show upgrade CTA page
        cta_page = '''
    <section style="padding:80px 24px 48px;text-align:center;">
        <div class="container" style="max-width:740px;">
            <p style="font-size:13px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
                Pro Analytics
            </p>
            <h1 style="font-family:var(--heading-font, var(--font-display));font-size:clamp(28px,4vw,42px);color:var(--ink);margin-bottom:16px;line-height:1.2;">
                Demand Signals Pro
            </h1>
            <p style="font-size:17px;color:var(--ink-muted);max-width:600px;margin:0 auto 48px;line-height:1.6;">
                Real-time data on what AI agents search for and can&rsquo;t find.
                Clustered signals, trend charts, source breakdowns &mdash; the data you need
                to build exactly what the market wants.
            </p>
        </div>
    </section>

    <section style="padding:0 24px 48px;">
        <div class="container" style="max-width:740px;">
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;">
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:32px 24px;text-align:center;">
                    <div style="font-size:28px;margin-bottom:12px;">&#x1f4ca;</div>
                    <h3 style="font-family:var(--heading-font, var(--font-display));font-size:18px;color:var(--ink);margin-bottom:8px;">Clustered Signals</h3>
                    <p style="font-size:14px;color:var(--ink-muted);line-height:1.5;">Similar searches grouped together to reveal real demand patterns, not noise.</p>
                </div>
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:32px 24px;text-align:center;">
                    <div style="font-size:28px;margin-bottom:12px;">&#x1f4c8;</div>
                    <h3 style="font-family:var(--heading-font, var(--font-display));font-size:18px;color:var(--ink);margin-bottom:8px;">Trend Data</h3>
                    <p style="font-size:14px;color:var(--ink-muted);line-height:1.5;">Daily search volume over the past 30 days. See what&rsquo;s rising before it peaks.</p>
                </div>
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:32px 24px;text-align:center;">
                    <div style="font-size:28px;margin-bottom:12px;">&#x1f310;</div>
                    <h3 style="font-family:var(--heading-font, var(--font-display));font-size:18px;color:var(--ink);margin-bottom:8px;">Source Breakdown</h3>
                    <p style="font-size:14px;color:var(--ink-muted);line-height:1.5;">See where searches come from &mdash; web, MCP, or API. Know your distribution channels.</p>
                </div>
            </div>
        </div>
    </section>

    <section style="padding:0 24px 48px;">
        <div class="container" style="max-width:480px;text-align:center;">
            <div style="background:var(--bg-card);border:2px solid var(--accent);border-radius:16px;padding:40px 32px;">
                <p style="font-size:13px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                    Demand Signals Pro
                </p>
                <div style="font-family:var(--heading-font, var(--font-display));font-size:48px;font-weight:700;color:var(--ink);margin-bottom:4px;">
                    $15<span style="font-size:18px;color:var(--ink-muted);font-weight:400;">/month</span>
                </div>
                <p style="font-size:14px;color:var(--ink-muted);margin-bottom:24px;">
                    Cancel anytime. Data updates in real-time.
                </p>
                <button onclick="subscribeDemandPro()" id="subscribe-btn"
                    style="display:inline-block;padding:14px 40px;background:var(--accent);color:white;
                           border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;
                           transition:opacity 0.2s;width:100%;">
                    Subscribe Now
                </button>
                <p id="subscribe-error" style="font-size:13px;color:var(--error-text, #EF4444);margin-top:12px;display:none;"></p>
            </div>
            <p style="font-size:13px;color:var(--ink-muted);margin-top:16px;">
                Want the basics? Check out the free <a href="/gaps" style="color:var(--accent);text-decoration:underline;">Demand Bounty Board</a>.
            </p>
        </div>
    </section>

    <script>
    async function subscribeDemandPro() {
        const btn = document.getElementById('subscribe-btn');
        const err = document.getElementById('subscribe-error');
        btn.disabled = true;
        btn.textContent = 'Loading...';
        err.style.display = 'none';
        try {
            const res = await fetch('/api/subscribe/demand-pro', {method: 'POST'});
            const data = await res.json();
            if (data.checkout_url) {
                window.location.href = data.checkout_url;
            } else {
                err.textContent = data.error || 'Something went wrong';
                err.style.display = 'block';
                btn.disabled = false;
                btn.textContent = 'Subscribe Now';
            }
        } catch (e) {
            err.textContent = 'Network error. Please try again.';
            err.style.display = 'block';
            btn.disabled = false;
            btn.textContent = 'Subscribe Now';
        }
    }
    </script>
'''

        return HTMLResponse(page_shell(
            title="Demand Signals Pro — Deep Analytics for Builders | IndieStack",
            body=cta_page,
            user=user,
            description="Pro demand signal analytics. Clustered signals, trend data, and source breakdowns to build what the market wants.",
        ))

    # ── Pro dashboard ──────────────────────────────────────────────────
    trends = await get_demand_trends(db, days=30)
    clusters = await get_demand_clusters(db, limit=50)

    # Stats
    total_searches_30d = sum(t['total_searches'] for t in trends) if trends else 0
    zero_results_30d = sum(t['zero_results'] for t in trends) if trends else 0
    fill_rate = round(((total_searches_30d - zero_results_30d) / total_searches_30d * 100) if total_searches_30d > 0 else 0, 1)

    # Stats bar
    stats_bar = f'''
    <section style="padding:0 24px 40px;">
        <div class="container" style="max-width:900px;">
            <div style="display:flex;gap:1px;background:var(--border);border-radius:12px;overflow:hidden;
                        border:1px solid var(--border);">
                <div style="flex:1;background:var(--bg-card);padding:20px 24px;text-align:center;">
                    <div style="font-family:var(--heading-font, var(--font-display));font-size:28px;font-weight:700;color:var(--accent);margin-bottom:4px;">
                        {total_searches_30d:,}
                    </div>
                    <div style="font-size:13px;color:var(--ink-muted);">Searches (30d)</div>
                </div>
                <div style="flex:1;background:var(--bg-card);padding:20px 24px;text-align:center;">
                    <div style="font-family:var(--heading-font, var(--font-display));font-size:28px;font-weight:700;color:var(--error-text, #EF4444);margin-bottom:4px;">
                        {zero_results_30d:,}
                    </div>
                    <div style="font-size:13px;color:var(--ink-muted);">Zero Results</div>
                </div>
                <div style="flex:1;background:var(--bg-card);padding:20px 24px;text-align:center;">
                    <div style="font-family:var(--heading-font, var(--font-display));font-size:28px;font-weight:700;color:var(--accent);margin-bottom:4px;">
                        {fill_rate}%
                    </div>
                    <div style="font-size:13px;color:var(--ink-muted);">Fill Rate</div>
                </div>
            </div>
        </div>
    </section>
    '''

    # Trend chart (CSS-only bar chart, last 14 days)
    recent_trends = sorted(trends, key=lambda t: t['day'])[-14:]
    max_searches = max((t['total_searches'] for t in recent_trends), default=1)

    trend_bars = ''
    for t in recent_trends:
        day_label = t['day'][5:]  # MM-DD
        pct = int(t['total_searches'] / max_searches * 100) if max_searches > 0 else 0
        zero_pct = int(t['zero_results'] / max_searches * 100) if max_searches > 0 else 0
        trend_bars += f'''
            <div style="display:flex;align-items:end;gap:2px;flex:1;min-width:40px;flex-direction:column;">
                <div style="width:100%;display:flex;align-items:end;gap:2px;height:120px;">
                    <div style="flex:1;background:var(--accent);border-radius:4px 4px 0 0;height:{pct}%;min-height:2px;opacity:0.7;" title="{t['total_searches']} searches"></div>
                    <div style="flex:1;background:var(--error-text, #EF4444);border-radius:4px 4px 0 0;height:{zero_pct}%;min-height:2px;opacity:0.7;" title="{t['zero_results']} zero results"></div>
                </div>
                <div style="font-size:10px;color:var(--ink-muted);text-align:center;width:100%;white-space:nowrap;">{day_label}</div>
            </div>'''

    trend_section = f'''
    <section style="padding:0 24px 40px;">
        <div class="container" style="max-width:900px;">
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:24px;">
                <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">
                    <h2 style="font-family:var(--heading-font, var(--font-display));font-size:18px;color:var(--ink);margin:0;">Search Volume (14 days)</h2>
                    <div style="display:flex;gap:16px;font-size:12px;">
                        <span style="display:flex;align-items:center;gap:4px;"><span style="display:inline-block;width:10px;height:10px;background:var(--accent);border-radius:2px;opacity:0.7;"></span> Total</span>
                        <span style="display:flex;align-items:center;gap:4px;"><span style="display:inline-block;width:10px;height:10px;background:var(--error-text, #EF4444);border-radius:2px;opacity:0.7;"></span> Zero results</span>
                    </div>
                </div>
                <div style="display:flex;gap:4px;align-items:end;">
                    {trend_bars}
                </div>
            </div>
        </div>
    </section>
    '''

    # Clusters table
    cluster_rows = ''
    for c in clusters:
        query = escape(c['query'])
        zero = c['zero_count']
        total = c['search_count']
        sources = escape(c['sources'] or 'web')
        first_seen = _relative_time(c['first_searched'])
        last_seen = _relative_time(c['last_searched'])

        if zero >= 10:
            badge_label = 'HIGH'
            badge_bg = 'var(--error-bg, rgba(239,68,68,0.12))'
            badge_color = 'var(--error-text, #EF4444)'
        elif zero >= 5:
            badge_label = 'GROWING'
            badge_bg = 'var(--warning-bg, rgba(226,183,100,0.12))'
            badge_color = 'var(--warning-text, #E2B764)'
        elif zero >= 2:
            badge_label = 'EMERGING'
            badge_bg = 'var(--info-bg, rgba(0,212,245,0.12))'
            badge_color = 'var(--info-text, #00D4F5)'
        else:
            badge_label = 'NEW'
            badge_bg = 'var(--bg-card, rgba(255,255,255,0.04))'
            badge_color = 'var(--ink-muted)'

        cluster_rows += f'''
            <tr style="border-bottom:1px solid var(--border);">
                <td style="padding:12px 16px;font-weight:500;color:var(--ink);">{query}</td>
                <td style="padding:12px 16px;text-align:center;color:var(--error-text, #EF4444);font-weight:600;">{zero}</td>
                <td style="padding:12px 16px;text-align:center;color:var(--ink-muted);">{total}</td>
                <td style="padding:12px 16px;text-align:center;font-size:12px;color:var(--ink-muted);">{sources}</td>
                <td style="padding:12px 16px;text-align:center;font-size:12px;color:var(--ink-muted);">{first_seen}</td>
                <td style="padding:12px 16px;text-align:center;font-size:12px;color:var(--ink-muted);">{last_seen}</td>
                <td style="padding:12px 16px;text-align:center;">
                    <span style="display:inline-block;padding:3px 10px;border-radius:999px;font-size:11px;
                                 font-weight:700;letter-spacing:0.5px;background:{badge_bg};color:{badge_color};">
                        {badge_label}
                    </span>
                </td>
            </tr>'''

    clusters_section = f'''
    <section style="padding:0 24px 40px;">
        <div class="container" style="max-width:900px;">
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;overflow:hidden;">
                <div style="display:flex;align-items:center;justify-content:space-between;padding:20px 24px;border-bottom:1px solid var(--border);">
                    <h2 style="font-family:var(--heading-font, var(--font-display));font-size:18px;color:var(--ink);margin:0;">Top Demand Signals</h2>
                    <a href="/api/demand-export" style="font-size:13px;color:var(--accent);text-decoration:none;">Export JSON</a>
                </div>
                <div style="overflow-x:auto;">
                    <table style="width:100%;border-collapse:collapse;font-size:14px;">
                        <thead>
                            <tr style="border-bottom:2px solid var(--border);background:var(--bg-card);">
                                <th style="padding:12px 16px;text-align:left;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Query</th>
                                <th style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Failed</th>
                                <th style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Total</th>
                                <th style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Sources</th>
                                <th style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">First Seen</th>
                                <th style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Last Seen</th>
                                <th style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Tier</th>
                            </tr>
                        </thead>
                        <tbody>
                            {cluster_rows if cluster_rows else '<tr><td colspan="7" style="padding:40px;text-align:center;color:var(--ink-muted);">No demand signals yet. Data populates as agents search.</td></tr>'}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    </section>
    '''

    hero = f'''
    <section style="padding:64px 24px 32px;text-align:center;">
        <div class="container" style="max-width:740px;">
            <p style="font-size:13px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
                Pro Dashboard
            </p>
            <h1 style="font-family:var(--heading-font, var(--font-display));font-size:clamp(28px,4vw,42px);color:var(--ink);margin-bottom:16px;line-height:1.2;">
                Demand Signals Pro
            </h1>
            <p style="font-size:17px;color:var(--ink-muted);max-width:600px;margin:0 auto 32px;line-height:1.6;">
                Deep analytics on what AI agents are searching for. Build what the market actually wants.
            </p>
        </div>
    </section>
    '''

    body = hero + stats_bar + trend_section + clusters_section

    return HTMLResponse(page_shell(
        title="Demand Signals Pro Dashboard | IndieStack",
        body=body,
        user=user,
        description="Pro demand signal analytics with clustered signals, trend data, and source breakdowns.",
    ))

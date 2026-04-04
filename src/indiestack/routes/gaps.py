"""Demand Bounty Board — real-time demand signals from AI agents."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from html import escape
from urllib.parse import quote
from datetime import datetime, timezone

from indiestack.routes.components import page_shell
from indiestack.db import get_search_gaps, get_search_demand, get_demand_trends, get_demand_clusters, get_pulse_feed

router = APIRouter()

# Junk queries to filter out (typos, nonsense, non-tool searches)
_BLOCKLIST = {
    'xbox game pass', 'akoraimagbuot', 'wace', 'test', 'asdf', 'hello',
    'indiestack', 'xxx', 'porn', 'sex', '{search_term_string}',
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


def _pulse_event_html(event: dict) -> str:
    """Render a single pulse event as a compact HTML row."""
    etype = event['type']
    ts = event.get('created_at', '')
    time_str = _relative_time(ts) if ts else ''
    query = escape(event['query'] or '') if event.get('query') else ''
    tool_name = escape(event['tool_name'] or '') if event.get('tool_name') else ''
    tool_slug = escape(event['tool_slug'] or '') if event.get('tool_slug') else ''

    if etype == 'recommend':
        dot = 'var(--success-text, #10B981)'
        tool_link = f'<a href="/tool/{tool_slug}" style="color:var(--accent);text-decoration:none;font-weight:600;">{tool_name}</a>' if tool_slug else tool_name
        text = f'Agent recommended {tool_link}'
    elif etype == 'search':
        dot = 'var(--accent)'
        tool_link = f'<a href="/tool/{tool_slug}" style="color:var(--accent);text-decoration:none;font-weight:600;">{tool_name}</a>' if tool_slug else tool_name
        text = f'Search found {tool_link}'
    else:
        dot = 'var(--error-text, #EF4444)'
        text = f'No tool found for &ldquo;{query}&rdquo;'

    return f'''
    <div style="display:flex;align-items:center;gap:10px;padding:10px 16px;border-bottom:1px solid var(--border);font-size:13px;">
        <span style="color:{dot};font-size:8px;">&#9679;</span>
        <span style="color:var(--ink);flex:1;">{text}</span>
        <span style="color:var(--ink-muted);font-size:11px;font-family:var(--font-mono);white-space:nowrap;">{time_str}</span>
    </div>'''


@router.get("/gaps", response_class=HTMLResponse)
async def gaps_page(request: Request):
    user = request.state.user
    db = request.state.db

    # Get all zero-result searches, then filter — but only show top 5
    raw_gaps = await get_search_gaps(db, limit=100)
    all_gaps = [g for g in raw_gaps if _is_valid_gap(g['query'])]
    gaps = all_gaps[:20]  # No limits — show all gaps
    total_gap_count = len(all_gaps)

    # Get a few recent pulse events for the activity preview
    pulse_events = await get_pulse_feed(db, limit=3)

    # Build gap cards — NO exact counts, just tier badges
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
                    <a href="/gaps/{escape(gap['query'].lower().replace(' ', '-'))}" style="font-family:var(--heading-font, var(--font-display));font-size:18px;font-weight:600;color:var(--ink);text-decoration:none;">
                        &ldquo;{query}&rdquo;
                    </a>
                    <span style="display:inline-block;padding:3px 10px;border-radius:999px;font-size:11px;
                                 font-weight:700;letter-spacing:0.5px;background:{badge_bg};color:{badge_color};">
                        {badge_label}
                    </span>
                </div>
                <div style="font-size:13px;color:var(--ink-muted);">
                    {f'Last searched {last_display}' if last_display else 'Recently searched'}
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
    hero = '''
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

    # Gap list (top 5 only)
    remaining = total_gap_count - 5
    upgrade_note = ''
    if remaining > 0:
        upgrade_note = f'''
            <div style="margin-top:20px;padding:28px;background:var(--card-bg);border:2px solid var(--border);
                        border-radius:12px;">
                <p style="font-size:16px;color:var(--ink);margin-bottom:4px;font-weight:600;text-align:center;">
                    +{remaining} more signals in Pro
                </p>
                <p style="font-size:13px;color:var(--ink-muted);margin-bottom:20px;text-align:center;">
                    Stop guessing. Know exactly what to build.
                </p>
                <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px;">
                    <div style="flex:1;min-width:140px;padding:12px;background:var(--card-bg);border:1px solid var(--border);border-radius:8px;">
                        <div style="font-size:12px;font-weight:700;color:var(--accent);margin-bottom:4px;">OPPORTUNITY SCORE</div>
                        <div style="font-size:12px;color:var(--ink-muted);">Algorithmic ranking of the best gaps to fill</div>
                    </div>
                    <div style="flex:1;min-width:140px;padding:12px;background:var(--card-bg);border:1px solid var(--border);border-radius:8px;">
                        <div style="font-size:12px;font-weight:700;color:var(--accent);margin-bottom:4px;">TREND SPARKLINES</div>
                        <div style="font-size:12px;color:var(--ink-muted);">14-day search trends per signal</div>
                    </div>
                    <div style="flex:1;min-width:140px;padding:12px;background:var(--card-bg);border:1px solid var(--border);border-radius:8px;">
                        <div style="font-size:12px;font-weight:700;color:var(--accent);margin-bottom:4px;">COMPETITION MAP</div>
                        <div style="font-size:12px;color:var(--ink-muted);">See how saturated each gap is</div>
                    </div>
                </div>
                <div style="text-align:center;">
                    <a href="/demand" style="display:inline-block;padding:12px 28px;background:var(--accent);color:white;
                           border-radius:8px;font-size:14px;font-weight:600;text-decoration:none;">
                        Unlock Demand Signals Pro &rarr;
                    </a>
                </div>
            </div>'''

    gap_list = f'''
    <section style="padding:0 24px 48px;">
        <div class="container" style="max-width:740px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;">
                <h2 style="font-family:var(--heading-font, var(--font-display));font-size:22px;color:var(--ink);">Top Bounties</h2>
                <span style="font-size:13px;color:var(--ink-muted);">Showing top 5</span>
            </div>
            <div style="display:flex;flex-direction:column;gap:12px;">
                {gap_cards if gap_cards else '<p style="color:var(--ink-muted);text-align:center;padding:40px;">No gaps detected yet. As more AI agents use the MCP server, bounties will appear here.</p>'}
            </div>
            {upgrade_note}
        </div>
    </section>
    '''

    # Recent activity preview (mini pulse — 3 events)
    pulse_html = ''
    if pulse_events:
        pulse_rows = ''.join(_pulse_event_html(dict(e)) for e in pulse_events)
        pulse_html = f'''
    <section style="padding:0 24px 48px;">
        <div class="container" style="max-width:740px;">
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;overflow:hidden;">
                <div style="padding:14px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;">
                    <span style="font-family:var(--heading-font, var(--font-display));font-size:16px;color:var(--ink);">
                        Recent Agent Activity
                    </span>
                    <a href="/demand" style="font-size:12px;color:var(--accent);text-decoration:none;">See full feed &rarr;</a>
                </div>
                {pulse_rows}
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
                Submit your tool and it&rsquo;ll start showing up in AI recommendations immediately.
                You&rsquo;ll get a live badge showing how many times agents recommend it.
            </p>
            <a href="/submit" class="btn btn-primary" style="padding:14px 32px;font-size:15px;">
                Submit Your Tool &rarr;
            </a>
        </div>
    </section>
    '''

    body = hero + gap_list + pulse_html + how_it_works + cta

    return HTMLResponse(page_shell(
        title="Demand Bounty Board — Tools AI Agents Are Searching For | IndieStack",
        body=body,
        user=user,
        description="Real-time demand signals from AI agents. See what tools were searched for and couldn't be found. Build one and get instant distribution.",
        canonical="/gaps",
    ))


@router.get("/gaps/{query_slug}", response_class=HTMLResponse)
async def gap_detail(request: Request, query_slug: str):
    """Individual gap detail page — SEO-friendly page per demand signal."""
    user = request.state.user
    db = request.state.db

    # Convert slug back to query
    query_text = query_slug.replace("-", " ")

    # Try exact match first
    cursor = await db.execute(
        """SELECT query, COUNT(*) as search_count, MAX(created_at) as last_searched
           FROM search_logs
           WHERE result_count = 0 AND LOWER(TRIM(query)) = LOWER(?)
           GROUP BY LOWER(TRIM(query))""",
        (query_text,),
    )
    row = await cursor.fetchone()

    # If no exact match, try fuzzy match on slug
    if not row:
        cursor = await db.execute(
            """SELECT query, COUNT(*) as search_count, MAX(created_at) as last_searched
               FROM search_logs
               WHERE result_count = 0 AND LOWER(REPLACE(TRIM(query), ' ', '-')) = LOWER(?)
               GROUP BY LOWER(TRIM(query))""",
            (query_slug,),
        )
        row = await cursor.fetchone()

    if not row:
        # 404 page
        not_found_body = '''
        <section style="padding:120px 24px 80px;text-align:center;">
            <div class="container" style="max-width:600px;">
                <h1 style="font-family:var(--heading-font, var(--font-display));font-size:36px;color:var(--ink);margin-bottom:16px;">
                    Signal Not Found
                </h1>
                <p style="font-size:16px;color:var(--ink-muted);margin-bottom:32px;line-height:1.6;">
                    This demand signal doesn&rsquo;t exist or hasn&rsquo;t been searched for yet.
                </p>
                <a href="/gaps" style="display:inline-block;padding:12px 28px;background:var(--accent);color:white;
                       border-radius:8px;font-size:15px;font-weight:600;text-decoration:none;">
                    &larr; Back to Demand Board
                </a>
            </div>
        </section>'''
        return HTMLResponse(
            page_shell(title="Signal Not Found | IndieStack", body=not_found_body, user=user),
            status_code=404,
        )

    gap_query = row['query'] if isinstance(row, dict) else row[0]
    search_count = row['search_count'] if isinstance(row, dict) else row[1]
    last_searched = row['last_searched'] if isinstance(row, dict) else row[2]
    last_display = _relative_time(last_searched) if last_searched else 'Recently'

    # Demand tier
    if search_count >= 10:
        tier_label = 'HIGH DEMAND'
        tier_color = '#EF4444'
        tier_bg = 'rgba(239,68,68,0.12)'
    elif search_count >= 5:
        tier_label = 'GROWING'
        tier_color = '#F59E0B'
        tier_bg = 'rgba(245,158,11,0.12)'
    elif search_count >= 2:
        tier_label = 'EMERGING'
        tier_color = 'var(--accent)'
        tier_bg = 'var(--info-bg, rgba(0,212,245,0.12))'
    else:
        tier_label = 'NEW SIGNAL'
        tier_color = 'var(--ink-muted)'
        tier_bg = 'var(--bg-card, rgba(255,255,255,0.04))'

    # Fetch 5 related gaps
    raw_related = await get_search_gaps(db, limit=50)
    related_gaps = [
        g for g in raw_related
        if _is_valid_gap(g['query']) and g['query'].lower() != gap_query.lower()
    ][:5]

    related_html = ''
    if related_gaps:
        related_items = ''
        for rg in related_gaps:
            rg_slug = rg['query'].lower().replace(' ', '-')
            rg_count = rg['count']
            if rg_count >= 10:
                rg_badge = '<span style="padding:2px 8px;border-radius:999px;font-size:10px;font-weight:700;background:rgba(239,68,68,0.12);color:#EF4444;">HIGH</span>'
            elif rg_count >= 5:
                rg_badge = '<span style="padding:2px 8px;border-radius:999px;font-size:10px;font-weight:700;background:rgba(245,158,11,0.12);color:#F59E0B;">GROWING</span>'
            elif rg_count >= 2:
                rg_badge = '<span style="padding:2px 8px;border-radius:999px;font-size:10px;font-weight:700;background:var(--info-bg, rgba(0,212,245,0.12));color:var(--accent);">EMERGING</span>'
            else:
                rg_badge = '<span style="padding:2px 8px;border-radius:999px;font-size:10px;font-weight:700;background:var(--bg-card, rgba(255,255,255,0.04));color:var(--ink-muted);">NEW</span>'
            related_items += f'''
                <a href="/gaps/{escape(rg_slug)}" style="display:flex;align-items:center;justify-content:space-between;padding:14px 16px;
                           border-bottom:1px solid var(--border);text-decoration:none;transition:background 0.15s;"
                   onmouseover="this.style.background='var(--bg-card)'" onmouseout="this.style.background='transparent'">
                    <span style="color:var(--ink);font-size:15px;font-weight:500;">&ldquo;{escape(rg['query'])}&rdquo;</span>
                    {rg_badge}
                </a>'''

        related_html = f'''
        <section style="padding:0 24px 48px;">
            <div class="container" style="max-width:680px;">
                <h2 style="font-family:var(--heading-font, var(--font-display));font-size:20px;color:var(--ink);margin-bottom:16px;">
                    Related Gaps
                </h2>
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;overflow:hidden;">
                    {related_items}
                </div>
            </div>
        </section>'''

    body = f'''
    <section style="padding:48px 24px 16px;">
        <div class="container" style="max-width:680px;">
            <a href="/gaps" style="font-size:14px;color:var(--accent);text-decoration:none;">&larr; Back to Demand Board</a>
        </div>
    </section>

    <section style="padding:16px 24px 32px;">
        <div class="container" style="max-width:680px;">
            <div style="margin-bottom:16px;">
                <span style="display:inline-block;padding:4px 12px;border-radius:999px;font-size:12px;
                             font-weight:700;letter-spacing:0.5px;background:{tier_bg};color:{tier_color};">
                    {tier_label}
                </span>
            </div>
            <h1 style="font-family:var(--heading-font, var(--font-display));font-size:clamp(24px,4vw,36px);color:var(--ink);margin-bottom:16px;line-height:1.3;">
                AI agents are searching for &ldquo;{escape(gap_query)}&rdquo;
            </h1>
            <p style="font-size:16px;color:var(--ink-muted);line-height:1.6;">
                This query has been searched <strong style="color:var(--ink);">{search_count} time{"s" if search_count != 1 else ""}</strong>
                by AI agents on IndieStack with zero results.
                Last searched {last_display}.
            </p>
        </div>
    </section>

    <section style="padding:0 24px 32px;">
        <div class="container" style="max-width:680px;">
            <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:28px;">
                <h2 style="font-family:var(--heading-font, var(--font-display));font-size:18px;color:var(--ink);margin-bottom:12px;">
                    Why this matters
                </h2>
                <p style="font-size:15px;color:var(--ink-muted);line-height:1.7;margin-bottom:0;">
                    When a developer asks their AI coding assistant to find a tool for &ldquo;{escape(gap_query)}&rdquo;,
                    the agent checks IndieStack &mdash; and comes up empty. This is a real, validated demand signal
                    from actual AI workflows. If you build a tool that fills this gap, every future agent search
                    will recommend <em>your</em> creation instead.
                </p>
            </div>
        </div>
    </section>

    <section style="padding:0 24px 48px;">
        <div class="container" style="max-width:680px;text-align:center;">
            <a href="/submit?name={quote(gap_query)}"
               style="display:inline-block;padding:14px 36px;background:var(--accent);color:white;
                      border-radius:8px;font-size:16px;font-weight:600;text-decoration:none;
                      transition:opacity 0.2s;">
                Submit a Tool for This Gap &rarr;
            </a>
            <p style="font-size:13px;color:var(--ink-muted);margin-top:12px;">
                Guaranteed distribution to AI agents searching for this.
            </p>
        </div>
    </section>

    {related_html}
    '''

    return HTMLResponse(page_shell(
        title=f'"{escape(gap_query)}" — AI Agents Need This Tool | IndieStack',
        body=body,
        user=user,
        description=f'AI agents searched for "{escape(gap_query)}" {search_count} times but nothing exists yet. Build it and get instant distribution.',
    ))


@router.get("/demand", response_class=HTMLResponse)
async def demand_pro(request: Request):
    """Pro demand signal dashboard — paid tier."""
    user = request.state.user
    db = request.state.db

    if False:  # Pro gate removed — all data is free now
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
                Stop guessing what to build. Opportunity Scores rank every gap by demand vs. supply.
                Sparklines show what&rsquo;s trending. Competition maps show what&rsquo;s empty.
            </p>
        </div>
    </section>

    <section style="padding:0 24px 48px;">
        <div class="container" style="max-width:740px;">
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;">
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:32px 24px;text-align:center;">
                    <div style="font-size:28px;margin-bottom:12px;">&#x1f3af;</div>
                    <h3 style="font-family:var(--heading-font, var(--font-display));font-size:18px;color:var(--ink);margin-bottom:8px;">Opportunity Score</h3>
                    <p style="font-size:14px;color:var(--ink-muted);line-height:1.5;">Every gap ranked algorithmically. Higher score = more demand, less competition. Know what to build first.</p>
                </div>
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:32px 24px;text-align:center;">
                    <div style="font-size:28px;margin-bottom:12px;">&#x1f4c8;</div>
                    <h3 style="font-family:var(--heading-font, var(--font-display));font-size:18px;color:var(--ink);margin-bottom:8px;">Trend Sparklines</h3>
                    <p style="font-size:14px;color:var(--ink-muted);line-height:1.5;">14-day search trends per signal. See what&rsquo;s rising before it peaks.</p>
                </div>
                <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:32px 24px;text-align:center;">
                    <div style="font-size:28px;margin-bottom:12px;">&#x1f7e2;</div>
                    <h3 style="font-family:var(--heading-font, var(--font-display));font-size:18px;color:var(--ink);margin-bottom:8px;">Competition Map</h3>
                    <p style="font-size:14px;color:var(--ink-muted);line-height:1.5;">See market saturation at a glance. Green = empty market, red = crowded. Find the gaps with no competition.</p>
                </div>
            </div>
        </div>
    </section>

    <section style="padding:0 24px 48px;">
        <div class="container" style="max-width:480px;text-align:center;">
            <div style="background:var(--bg-card);border:2px solid var(--accent);border-radius:16px;padding:40px 32px;">
                <p style="font-size:13px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                    Part of IndieStack Pro
                </p>
                <div style="font-family:var(--heading-font, var(--font-display));font-size:48px;font-weight:700;color:var(--ink);margin-bottom:4px;">
                    $19<span style="font-size:18px;color:var(--ink-muted);font-weight:400;">/month</span>
                </div>
                <p style="font-size:14px;color:var(--ink-muted);margin-bottom:24px;">
                    Demand signals + agent citations + priority API access. One subscription, everything unlocked.
                </p>
                <a href="/pricing"
                    style="display:inline-block;padding:14px 40px;background:var(--accent);color:white;
                           border:none;border-radius:8px;font-size:16px;font-weight:600;cursor:pointer;
                           transition:opacity 0.2s;width:100%;text-decoration:none;box-sizing:border-box;">
                    View Pricing
                </a>
            </div>
            <p style="font-size:13px;color:var(--ink-muted);margin-top:16px;">
                Want the basics? Check out the free <a href="/gaps" style="color:var(--accent);text-decoration:underline;">Demand Bounty Board</a>.
            </p>
        </div>
    </section>
'''

        return HTMLResponse(page_shell(
            title="Demand Signals Pro — Deep Analytics for Builders | IndieStack",
            body=cta_page,
            user=user,
            description="Pro demand signal analytics. Clustered signals, trend data, and source breakdowns to build what the market wants.",
        ))

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
                    <span title="Higher = more demand + less competition" style="font-size:11px;font-weight:700;color:var(--accent);text-transform:uppercase;letter-spacing:0.5px;">Score {c['opportunity_score']}</span>
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
                                <th data-sort="opp" title="Opportunity Score: higher = more demand + less supply. Combines search volume with zero-result rate." style="padding:12px 16px;text-align:center;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.5px;">Score &#x25BE;</th>
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

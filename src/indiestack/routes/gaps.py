"""Public page showing what developers are asking AI for that doesn't exist yet."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from html import escape
from urllib.parse import quote

from indiestack.routes.components import page_shell
from indiestack.db import get_search_gaps, get_search_demand

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


@router.get("/gaps", response_class=HTMLResponse)
async def gaps_page(request: Request):
    user = request.state.user
    db = request.state.db

    # Get all zero-result searches, then filter
    raw_gaps = await get_search_gaps(db, limit=100)
    gaps = [g for g in raw_gaps if _is_valid_gap(g['query'])][:30]

    # Stats
    total_gaps = len(gaps)

    # Build gap cards
    gap_cards = ''
    for i, gap in enumerate(gaps):
        query = escape(gap['query'])
        count = gap['count']
        last = gap.get('last_searched', '')
        if last:
            # Show relative time
            last_display = last[:10]  # Just the date
        else:
            last_display = ''

        # Demand indicator
        if count >= 5:
            heat = '🔥🔥🔥'
            heat_label = 'High demand'
            heat_color = 'var(--danger, #EF4444)'
        elif count >= 3:
            heat = '🔥🔥'
            heat_label = 'Growing demand'
            heat_color = 'var(--gold, #E2B764)'
        elif count >= 2:
            heat = '🔥'
            heat_label = 'Emerging'
            heat_color = 'var(--accent, #00D4F5)'
        else:
            heat = ''
            heat_label = 'New'
            heat_color = 'var(--ink-muted)'

        gap_cards += f'''
        <div class="card" style="padding:20px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;">
            <div style="flex:1;min-width:200px;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
                    <span style="font-family:var(--font-display);font-size:17px;color:var(--ink);">{query}</span>
                    {f'<span style="font-size:13px;">{heat}</span>' if heat else ''}
                </div>
                <div style="display:flex;gap:16px;font-size:13px;color:var(--ink-muted);">
                    <span>Searched <strong style="color:var(--ink);">{count}</strong> time{"s" if count != 1 else ""}</span>
                    {f'<span style="color:var(--border);">&middot;</span><span>Last: {last_display}</span>' if last_display else ''}
                    <span style="color:var(--border);">&middot;</span>
                    <span style="color:{heat_color};font-weight:600;">{heat_label}</span>
                </div>
            </div>
            <a href="/submit?name={quote(gap['query'])}" style="padding:8px 16px;background:var(--accent);color:white;border-radius:999px;
                      font-size:13px;font-weight:600;text-decoration:none;white-space:nowrap;flex-shrink:0;">
                Fill this gap &rarr;
            </a>
        </div>'''

    # Hero section
    hero = f'''
    <section style="padding:64px 24px 32px;text-align:center;">
        <div class="container" style="max-width:700px;">
            <p style="font-size:13px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
                Live from the IndieStack MCP Server
            </p>
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,40px);color:var(--ink);margin-bottom:16px;line-height:1.2;">
                Tools developers are asking AI for&mdash;that don&rsquo;t exist yet.
            </h1>
            <p style="font-size:17px;color:var(--ink-muted);max-width:560px;margin:0 auto 24px;line-height:1.6;">
                Every time an AI agent searches IndieStack and finds nothing, it lands here.
                These are real gaps in the indie ecosystem&mdash;ranked by demand.
            </p>
            <div style="display:inline-flex;gap:24px;font-size:14px;color:var(--ink-muted);background:var(--card-bg);
                        border:1px solid var(--border);padding:12px 24px;border-radius:var(--radius-sm);">
                <span><strong style="color:var(--accent);">{total_gaps}</strong> open gaps</span>
                <span style="color:var(--border);">|</span>
                <span>Updated live</span>
            </div>
        </div>
    </section>
    '''

    # How it works
    how_it_works = '''
    <section style="padding:0 24px 48px;">
        <div class="container" style="max-width:700px;">
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:24px;margin-bottom:48px;">
                <div style="text-align:center;padding:20px;">
                    <div style="font-size:28px;margin-bottom:8px;">🔍</div>
                    <p style="font-size:14px;font-weight:600;color:var(--ink);margin-bottom:4px;">Dev asks AI for a tool</p>
                    <p style="font-size:13px;color:var(--ink-muted);">&ldquo;Find me an indie Vercel alternative&rdquo;</p>
                </div>
                <div style="text-align:center;padding:20px;">
                    <div style="color:var(--slate);margin-bottom:8px;"><svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg></div>
                    <p style="font-size:14px;font-weight:600;color:var(--ink);margin-bottom:4px;">AI searches IndieStack</p>
                    <p style="font-size:13px;color:var(--ink-muted);">MCP server finds 0 results</p>
                </div>
                <div style="text-align:center;padding:20px;">
                    <div style="font-size:28px;margin-bottom:8px;">📊</div>
                    <p style="font-size:14px;font-weight:600;color:var(--ink);margin-bottom:4px;">Gap appears here</p>
                    <p style="font-size:13px;color:var(--ink-muted);">Ranked by how many devs searched</p>
                </div>
            </div>
        </div>
    </section>
    '''

    # Gap list
    gap_list = f'''
    <section style="padding:0 24px 64px;">
        <div class="container" style="max-width:700px;">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;">
                <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);">Open Gaps</h2>
                <span style="font-size:13px;color:var(--ink-muted);">Sorted by demand</span>
            </div>
            <div style="display:flex;flex-direction:column;gap:12px;">
                {gap_cards if gap_cards else '<p style="color:var(--ink-muted);text-align:center;padding:40px;">No gaps detected yet. As more developers use the MCP server, gaps will appear here.</p>'}
            </div>
        </div>
    </section>
    '''

    # CTA
    cta = '''
    <section style="padding:48px 24px;background:var(--cream-dark);">
        <div class="container" style="max-width:600px;text-align:center;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:12px;">
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

    body = hero + how_it_works + gap_list + cta

    return HTMLResponse(page_shell(
        title="Market Gaps — Tools Developers Are Asking AI For | IndieStack",
        body=body,
        user=user,
        description="Real-time demand signals from AI agents. See what tools developers are searching for that don't exist yet.",
    ))

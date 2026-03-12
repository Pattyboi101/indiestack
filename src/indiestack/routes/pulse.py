"""AI Pulse — live feed of what AI agents are recommending right now."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from html import escape
from datetime import datetime, timezone
from urllib.parse import quote

from indiestack.routes.components import page_shell
from indiestack.db import get_pulse_feed, get_search_stats

router = APIRouter()


def _relative_time(ts_str: str) -> str:
    """Convert a timestamp string to a human-readable relative time."""
    try:
        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        diff = (now - ts).total_seconds()
        if diff < 0:
            return "just now"
        elif diff < 60:
            return f"{int(diff)}s ago"
        elif diff < 3600:
            return f"{int(diff / 60)}m ago"
        elif diff < 86400:
            return f"{int(diff / 3600)}h ago"
        else:
            return f"{int(diff / 86400)}d ago"
    except (ValueError, TypeError, AttributeError):
        return ""


def _event_html(event: dict) -> str:
    """Render a single pulse event as an HTML row."""
    etype = event['type']
    time_str = _relative_time(event['created_at'])
    query = escape(event['query'] or '') if event['query'] else ''
    tool_name = escape(event['tool_name'] or '') if event['tool_name'] else ''
    tool_slug = escape(event['tool_slug'] or '')
    agent = escape(event['agent'] or 'AI Agent')

    if etype == 'recommend':
        # Agent citation — a tool was explicitly recommended
        dot = '#10B981'  # green
        icon = '&#9679;'  # filled circle
        tool_link = f'<a href="/tool/{tool_slug}" style="color:var(--accent);text-decoration:none;font-weight:600;">{tool_name}</a>' if tool_slug else tool_name
        text = f'<span style="color:var(--ink-muted);">{agent}</span> recommended {tool_link}'
    elif etype == 'search':
        # Search that found results
        dot = '#00D4F5'  # cyan
        icon = '&#9679;'
        tool_link = f'<a href="/tool/{tool_slug}" style="color:var(--accent);text-decoration:none;font-weight:600;">{tool_name}</a>' if tool_slug else tool_name
        text = f'<span style="color:var(--ink-muted);">{agent}</span> found {tool_link} for &ldquo;{query}&rdquo;'
    else:
        # Gap — no results found
        dot = '#EF4444'  # red
        icon = '&#9679;'
        gap_link = f'<a href="/gaps" style="color:var(--error-text);text-decoration:none;font-weight:600;">{query}</a>'
        text = f'No tool found for &ldquo;{gap_link}&rdquo; &mdash; <a href="/submit?name={quote(query)}" style="color:var(--gold);text-decoration:none;font-weight:600;">fill this gap</a>'

    return f'''
    <div class="pulse-row" style="display:flex;align-items:center;gap:14px;padding:14px 20px;
                border-bottom:1px solid var(--border);transition:background 0.15s;">
        <div style="flex-shrink:0;display:flex;align-items:center;gap:8px;min-width:70px;">
            <span class="pulse-dot" style="color:{dot};font-size:10px;line-height:1;">{icon}</span>
            <span style="font-size:12px;color:var(--ink-muted);font-family:var(--font-mono);white-space:nowrap;">{time_str}</span>
        </div>
        <div style="font-size:14px;color:var(--ink);line-height:1.5;flex:1;">
            {text}
        </div>
    </div>'''


@router.get("/pulse", response_class=HTMLResponse)
async def pulse_page(request: Request):
    user = request.state.user
    db = request.state.db

    events = await get_pulse_feed(db, limit=50)
    stats = await get_search_stats(db)

    # Build event rows
    event_rows = ''.join(_event_html(dict(e)) for e in events) if events else '''
        <div style="text-align:center;padding:60px 20px;color:var(--ink-muted);">
            <p style="font-size:17px;margin-bottom:8px;">Waiting for activity...</p>
            <p style="font-size:14px;">Events will appear here as AI agents search and recommend tools.</p>
        </div>'''

    body = f'''
    <style>
        @keyframes pulse-fade {{
            0% {{ opacity: 0; transform: translateY(-8px); }}
            100% {{ opacity: 1; transform: translateY(0); }}
        }}
        .pulse-row {{ animation: pulse-fade 0.4s ease-out; }}
        .pulse-row:hover {{ background: var(--cream-dark); }}
        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.3; }}
        }}
        .pulse-live-dot {{
            display: inline-block;
            width: 8px; height: 8px;
            background: #EF4444;
            border-radius: 50%;
            animation: blink 1.5s ease-in-out infinite;
        }}
    </style>

    <!-- Hero -->
    <section style="padding:64px 24px 32px;text-align:center;">
        <div class="container" style="max-width:700px;">
            <p style="font-size:13px;font-weight:600;color:var(--accent);text-transform:uppercase;letter-spacing:1px;margin-bottom:12px;">
                <span class="pulse-live-dot" style="margin-right:6px;vertical-align:middle;"></span> Live Feed
            </p>
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,40px);color:var(--ink);margin-bottom:16px;line-height:1.2;">
                AI Pulse
            </h1>
            <p style="font-size:17px;color:var(--ink-muted);max-width:560px;margin:0 auto 24px;line-height:1.6;">
                Watch AI agents search, recommend, and discover indie creations in real time.
                Every event below is a real interaction with the IndieStack MCP server.
            </p>
            <div style="display:inline-flex;gap:24px;font-size:14px;color:var(--ink-muted);background:var(--card-bg);
                        border:1px solid var(--border);padding:12px 24px;border-radius:var(--radius-sm);flex-wrap:wrap;justify-content:center;">
                <span><strong style="color:var(--accent);">{stats['today']}</strong> today</span>
                <span style="color:var(--border);">|</span>
                <span><strong style="color:var(--accent);">{stats['this_week']}</strong> this week</span>
                <span style="color:var(--border);">|</span>
                <span><strong style="color:var(--accent);">{stats['all_time']}</strong> all time</span>
            </div>
        </div>
    </section>

    <!-- Legend -->
    <section style="padding:0 24px 24px;">
        <div class="container" style="max-width:700px;">
            <div style="display:flex;gap:24px;justify-content:center;flex-wrap:wrap;font-size:13px;color:var(--ink-muted);">
                <span><span style="color:var(--success-text);">&#9679;</span> AI recommended a tool</span>
                <span><span style="color:var(--accent);">&#9679;</span> Search found a match</span>
                <span><span style="color:var(--error-text);">&#9679;</span> No tool found (gap!)</span>
            </div>
        </div>
    </section>

    <!-- Feed -->
    <section style="padding:0 24px 64px;">
        <div class="container" style="max-width:700px;">
            <div class="card" style="overflow:hidden;" id="pulse-feed">
                <div style="padding:16px 20px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;">
                    <span style="font-family:var(--font-display);font-size:17px;color:var(--ink);">
                        <span class="pulse-live-dot" style="margin-right:8px;vertical-align:middle;"></span>
                        Activity Feed
                    </span>
                    <span style="font-size:12px;color:var(--ink-muted);font-family:var(--font-mono);" id="pulse-status">
                        live &mdash; refreshes every 30s
                    </span>
                </div>
                <div id="pulse-events">
                    {event_rows}
                </div>
            </div>
        </div>
    </section>

    <!-- CTA -->
    <section style="padding:48px 24px;background:var(--cream-dark);">
        <div class="container" style="max-width:600px;text-align:center;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:12px;">
                Want your tool on this feed?
            </h2>
            <p style="font-size:15px;color:var(--ink-muted);margin-bottom:24px;line-height:1.6;">
                Submit your creation to IndieStack and AI agents will start recommending it to developers.
                Every recommendation shows up here, live.
            </p>
            <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
                <a href="/submit" class="btn btn-primary" style="padding:14px 32px;font-size:15px;">
                    Submit Your Creation &rarr;
                </a>
                <a href="/gaps" class="btn" style="padding:14px 32px;font-size:15px;border:1px solid var(--border);color:var(--ink);background:var(--card-bg);">
                    See Market Gaps
                </a>
            </div>
        </div>
    </section>

    <!-- Auto-refresh script -->
    <script>
    (function() {{
        var refreshInterval = 30000;
        setInterval(function() {{
            fetch('/api/pulse')
                .then(function(r) {{ return r.json(); }})
                .then(function(data) {{
                    if (data.html) {{
                        document.getElementById('pulse-events').innerHTML = data.html;
                    }}
                }})
                .catch(function() {{}});
        }}, refreshInterval);
    }})();
    </script>
    '''

    return HTMLResponse(page_shell(
        title="AI Pulse — Live AI Agent Activity | IndieStack",
        body=body,
        user=user,
        description="Live feed of AI agent activity on IndieStack. Watch in real-time as AI assistants discover, search, and recommend indie creations.",
        canonical="/pulse",
    ))


@router.get("/api/pulse")
async def pulse_api(request: Request):
    """JSON endpoint for auto-refresh polling."""
    db = request.state.db
    events = await get_pulse_feed(db, limit=50)
    html = ''.join(_event_html(dict(e)) for e in events) if events else '''
        <div style="text-align:center;padding:60px 20px;color:var(--ink-muted);">
            <p style="font-size:17px;margin-bottom:8px;">Waiting for activity...</p>
            <p style="font-size:14px;">Events will appear here as AI agents search and recommend tools.</p>
        </div>'''
    return JSONResponse({"html": html})

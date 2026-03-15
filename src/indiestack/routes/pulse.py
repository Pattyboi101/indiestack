"""AI Pulse — public real-time feed of AI agent activity across IndieStack."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from html import escape
from datetime import datetime, timezone
from urllib.parse import quote

from indiestack.db import get_pulse_feed

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


@router.get("/pulse")
async def pulse_page(request: Request):
    """Redirect to Demand Signals Pro — pulse feed is now a pro feature."""
    return RedirectResponse(url="/demand", status_code=302)


@router.get("/api/pulse")
async def pulse_api(request: Request):
    """JSON endpoint for auto-refresh polling (used by pro dashboard)."""
    db = request.state.db
    events = await get_pulse_feed(db, limit=30)
    filter_type = request.query_params.get('filter', '')
    if filter_type == 'gaps':
        events = [e for e in events if e['type'] == 'gap']
    html = ''.join(_event_html(dict(e)) for e in events) if events else '''
        <div style="text-align:center;padding:40px 20px;color:var(--ink-muted);">
            <p style="font-size:14px;">Waiting for activity...</p>
        </div>'''
    return JSONResponse({"html": html})

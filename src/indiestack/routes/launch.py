"""Launch day page — goes live March 2, 2026. Returns 404 before that."""

from datetime import date
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from indiestack.routes.components import page_shell

router = APIRouter()

LAUNCH_DATE = date(2026, 3, 2)


def _value_card(icon: str, title: str, desc: str) -> str:
    return f'''
    <div class="card" style="text-align:center;padding:28px 20px;">
        <div style="font-size:32px;margin-bottom:12px;">{icon}</div>
        <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin:0 0 8px;">{title}</h3>
        <p style="color:var(--ink-muted);font-size:14px;line-height:1.5;margin:0;">{desc}</p>
    </div>
    '''


@router.get("/launch", response_class=HTMLResponse)
async def launch_page(request: Request):
    preview = request.query_params.get("preview") == "1"
    if not preview and date.today() < LAUNCH_DATE:
        return Response(status_code=404)

    db = request.state.db
    user = request.state.user

    # Pull live stats
    tool_count = (await (await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status = 'approved'")).fetchone())['cnt']
    maker_count = (await (await db.execute("SELECT COUNT(*) as cnt FROM makers")).fetchone())['cnt']
    cat_count = (await (await db.execute("SELECT COUNT(*) as cnt FROM categories")).fetchone())['cnt']
    mcp_views = (await (await db.execute("SELECT COALESCE(SUM(mcp_view_count), 0) as cnt FROM tools")).fetchone())['cnt']
    search_count = (await (await db.execute(
        "SELECT COUNT(*) as cnt FROM search_logs WHERE created_at >= datetime('now', '-7 days')"
    )).fetchone())['cnt']

    stats_html = f'''
    <div style="display:flex;justify-content:center;gap:32px;flex-wrap:wrap;margin:32px 0;">
        <div style="text-align:center;">
            <div style="font-family:var(--font-display);font-size:32px;color:var(--slate);">{tool_count}</div>
            <div style="color:var(--ink-muted);font-size:13px;">indie creations</div>
        </div>
        <div style="text-align:center;">
            <div style="font-family:var(--font-display);font-size:32px;color:var(--slate);">{cat_count}</div>
            <div style="color:var(--ink-muted);font-size:13px;">categories</div>
        </div>
        <div style="text-align:center;">
            <div style="font-family:var(--font-display);font-size:32px;color:var(--accent);">{mcp_views}</div>
            <div style="color:var(--ink-muted);font-size:13px;">AI agent lookups</div>
        </div>
        <div style="text-align:center;">
            <div style="font-family:var(--font-display);font-size:32px;color:var(--slate);">{search_count}</div>
            <div style="color:var(--ink-muted);font-size:13px;">searches/week</div>
        </div>
    </div>
    '''

    values_html = f'''
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin:40px 0;">
        {_value_card("&#129302;", "AI-Native Discovery", "Your AI assistant checks IndieStack before building from scratch. It finds existing creations so you don't rebuild what already exists.")}
        {_value_card("&#128269;", "Search + Alternatives", "Search for any tool or competitor. Looking for Auth0? We'll show you indie alternatives. Looking for something that doesn't exist? We'll tell you.")}
        {_value_card('<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg>', "Market Gap Intelligence", "Every failed search is a signal. See what developers and AI agents are looking for but can't find — and build it first.")}
    </div>
    '''

    email_capture = '''
    <div class="card" style="text-align:center;padding:32px;margin-top:40px;border-left:3px solid var(--slate);">
        <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin:0 0 8px;">
            Stay in the loop
        </h2>
        <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
            Get notified when new tools launch and makers ship updates.
        </p>
        <form method="post" action="/subscribe" style="display:flex;gap:8px;max-width:400px;margin:0 auto;">
            <input type="email" name="email" placeholder="you@example.com" required
                   style="flex:1;padding:12px 16px;border:1px solid var(--border);border-radius:var(--radius);
                          font-size:14px;background:var(--card-bg);color:var(--ink);">
            <button type="submit" class="btn btn-primary" style="white-space:nowrap;">Subscribe</button>
        </form>
    </div>
    '''

    body = f'''
    <div class="container" style="max-width:760px;padding:48px 24px;">
        <div style="text-align:center;margin-bottom:32px;">
            <div style="display:inline-block;padding:8px 16px;border-radius:999px;font-size:13px;font-weight:700;
                        background:linear-gradient(135deg,var(--slate),#0D7377);color:white;margin-bottom:16px;">
                Now Live
            </div>
            <h1 style="font-family:var(--font-display);font-size:42px;color:var(--ink);margin:0;line-height:1.1;">
                The Knowledge Layer<br>for AI Agents
            </h1>
            <p style="color:var(--ink-muted);font-size:18px;margin-top:12px;max-width:560px;display:inline-block;">
                {tool_count} indie creations, searchable by AI coding assistants and developers.
                Stop building what already exists.
            </p>
        </div>

        {stats_html}

        <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;margin:32px 0;">
            <a href="/explore" class="btn btn-primary" style="font-size:16px;padding:14px 28px;">
                Explore Tools &rarr;
            </a>
            <a href="/submit" class="btn btn-secondary" style="font-size:16px;padding:14px 28px;">
                List Your Tool
            </a>
        </div>

        {values_html}

        <div class="card" style="text-align:center;padding:28px;background:linear-gradient(135deg,var(--terracotta) 0%,var(--terracotta-dark) 100%);">
            <p style="font-size:24px;margin-bottom:8px;">&#129302;</p>
            <h2 style="font-family:var(--font-display);font-size:20px;color:white;margin:0 0 8px;">
                Install the MCP Server
            </h2>
            <p style="color:rgba(255,255,255,0.7);font-size:14px;line-height:1.6;margin-bottom:16px;">
                One command. Cursor, Claude Code, and Windsurf will search IndieStack
                before your AI writes a single line of code.
            </p>
            <code style="font-family:var(--font-mono);font-size:13px;color:var(--accent);background:rgba(0,212,245,0.1);padding:8px 16px;border-radius:var(--radius-sm);display:inline-block;">
                claude mcp add indiestack -- uvx --from indiestack indiestack-mcp
            </code>
        </div>

        <div class="card" style="text-align:center;padding:28px;margin-top:24px;background:linear-gradient(135deg,var(--terracotta),var(--terracotta-dark));">
            <h2 style="font-family:var(--font-display);font-size:22px;color:white;margin:0 0 8px;">
                For Makers
            </h2>
            <p style="color:rgba(255,255,255,0.7);font-size:15px;margin-bottom:16px;">
                List your tool for free. AI agents will recommend it to developers.
                See how often your tool gets picked.
            </p>
            <a href="/submit" class="btn" style="background:var(--slate);color:var(--terracotta-dark);font-weight:700;font-size:15px;padding:12px 24px;">
                Submit Your Creation &rarr;
            </a>
        </div>

        {email_capture}
    </div>
    '''

    return HTMLResponse(page_shell(
        "The Knowledge Layer for AI Agents",
        body,
        user=user,
        description=f"IndieStack: {tool_count} indie creations searchable by AI coding assistants. The knowledge layer for developers and AI agents.",
    ))

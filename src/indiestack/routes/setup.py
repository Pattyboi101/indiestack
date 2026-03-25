"""Setup page — one-click MCP install + CLAUDE.md generator."""
import json as _json
from html import escape
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from indiestack.routes.components import page_shell

router = APIRouter()

# ── Install commands per IDE ─────────────────────────────────────────────
IDES = {
    "claude-code": {
        "name": "Claude Code",
        "install": "claude mcp add indiestack -- uvx --from indiestack indiestack-mcp",
        "note": "Run this in your terminal. IndieStack will appear as a tool source in your next session.",
    },
    "cursor": {
        "name": "Cursor",
        "install": '{\n  "mcpServers": {\n    "indiestack": {\n      "command": "uvx",\n      "args": ["--from", "indiestack", "indiestack-mcp"]\n    }\n  }\n}',
        "note": "Add this to <code>.cursor/mcp.json</code> in your project root, or to your global Cursor settings.",
    },
    "windsurf": {
        "name": "Windsurf",
        "install": '{\n  "mcpServers": {\n    "indiestack": {\n      "command": "uvx",\n      "args": ["--from", "indiestack", "indiestack-mcp"]\n    }\n  }\n}',
        "note": "Add this to your Windsurf MCP configuration file.",
    },
    "other": {
        "name": "Other / Manual",
        "install": "pip install indiestack\npython -m indiestack.mcp_server",
        "note": "Install from PyPI and point your MCP client at the server process.",
    },
}

# ── CLAUDE.md content ────────────────────────────────────────────────────
CLAUDE_MD_TEMPLATE = """# IndieStack — Dependency Intelligence

## Setup
MCP: `claude mcp add indiestack -- uvx --from indiestack indiestack-mcp`

## Rules
- Before installing any new package (npm/pip/cargo), call `analyze_dependencies`
  with the current manifest to check the health score
- If the score drops below 70, flag the problematic dependency and suggest
  the alternatives from the report before proceeding
- Before writing auth, payments, databases, email, or monitoring from scratch,
  call `find_tools` to check for existing solutions
- After integrating a tool, call `report_outcome(slug, success=true/false)`
- If two tools work well together, call `report_compatibility(tool_a, tool_b)`

## What's available
- `analyze_dependencies(manifest)` — 0-100 health score for your stack
- `find_tools(query)` — search 6,500+ developer tools
- `get_tool_details(slug)` — integration docs and API specs
- `check_health(slugs)` — verify tools are still maintained
- `build_stack(needs)` — complete stack recommendation
"""

CURSORRULES_TEMPLATE = """# IndieStack — Dependency Intelligence

## MCP Setup
Add to `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "indiestack": {
      "command": "uvx",
      "args": ["--from", "indiestack", "indiestack-mcp"]
    }
  }
}
```

## Rules
- Before installing any new package, call `analyze_dependencies` with the
  current manifest. If score < 70, suggest alternatives before proceeding.
- Before writing infrastructure (auth, payments, email, databases, monitoring),
  call `find_tools` to check for existing solutions first.
- After integrating a tool, call `report_outcome(slug, success=true/false)`.
"""

_COPY_BTN = '''<button class="copy-btn" style="position:absolute;top:8px;right:8px;padding:6px 14px;
font-size:12px;font-weight:600;background:rgba(255,255,255,0.1);color:#e2e8f0;
border:1px solid rgba(255,255,255,0.2);border-radius:6px;cursor:pointer;">Copy</button>'''


@router.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    user = request.state.user

    # Build IDE tab buttons and content panels
    tab_buttons = ""
    tab_panels = ""
    for i, (ide_key, ide) in enumerate(IDES.items()):
        active = "active" if i == 0 else ""
        tab_buttons += f'''
            <button class="setup-tab {active}" data-tab="{ide_key}"
                    style="padding:10px 20px;font-size:14px;font-weight:600;
                           border:1px solid var(--border);background:{"var(--card-bg)" if i == 0 else "transparent"};
                           color:var(--ink);border-radius:8px;cursor:pointer;
                           min-height:44px;white-space:nowrap;">
                {ide["name"]}
            </button>'''

        install_escaped = escape(ide["install"])

        tab_panels += f'''
            <div class="setup-panel" data-tab="{ide_key}" style="display:{"block" if i == 0 else "none"};">
                <div style="position:relative;">
                    <pre class="copyable" style="background:var(--ink);color:#e2e8f0;padding:16px 50px 16px 16px;
                                border-radius:var(--radius-sm);font-size:13px;font-family:var(--font-mono);
                                overflow-x:auto;line-height:1.6;margin:0;">{install_escaped}</pre>
                    {_COPY_BTN}
                </div>
                <p style="font-size:13px;color:var(--ink-muted);margin:10px 0 0;">{ide["note"]}</p>
            </div>'''

    # CLAUDE.md section
    claude_md_escaped = escape(CLAUDE_MD_TEMPLATE.strip())

    is_welcome = request.query_params.get("welcome") == "1"
    welcome_banner = ''
    if is_welcome and user:
        from html import escape as _esc
        _name = _esc(user.get('name', '').split()[0] or 'there')
        welcome_banner = f'''
        <div style="background:linear-gradient(135deg,#065F46,#064E3B);border:1px solid rgba(110,231,183,0.3);
                    border-radius:var(--radius);padding:20px 24px;margin-bottom:24px;text-align:center;">
            <p style="color:#6EE7B7;font-size:20px;font-weight:700;margin:0 0 4px;">Welcome to IndieStack, {_name}!</p>
            <p style="color:rgba(255,255,255,0.7);font-size:14px;margin:0;">Follow these steps to connect your AI agent to 6,500+ developer tools.</p>
        </div>'''

    body = f'''
    <div class="container" style="max-width:760px;padding:48px 24px 80px;">

        {welcome_banner}

        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,40px);color:var(--ink);margin:0 0 12px;">
                Set up IndieStack
            </h1>
            <p style="color:var(--ink-muted);font-size:17px;line-height:1.6;max-width:520px;margin:0 auto;">
                Give your AI agent access to 6,500+ developer tools.
                One command. Works in seconds.
            </p>
        </div>

        <!-- Step 1: Install MCP -->
        <div style="margin-bottom:40px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
                <span style="width:32px;height:32px;border-radius:50%;background:var(--accent);color:#0F1D30;
                             display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;flex-shrink:0;">1</span>
                <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin:0;">Install the MCP server</h2>
            </div>

            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px;">
                {tab_buttons}
            </div>

            {tab_panels}
        </div>

        <!-- Step 2: Add CLAUDE.md -->
        <div style="margin-bottom:40px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
                <span style="width:32px;height:32px;border-radius:50%;background:var(--accent);color:#0F1D30;
                             display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;flex-shrink:0;">2</span>
                <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin:0;">Add to your project <span style="font-size:14px;font-weight:400;color:var(--ink-muted);">(optional)</span></h2>
            </div>
            <p style="font-size:14px;color:var(--ink-muted);margin:0 0 12px;line-height:1.6;">
                Drop this in your project root. Your agent will check dependency health scores and search for existing tools before writing infrastructure from scratch.
            </p>

            <div style="position:relative;">
                <pre class="copyable" style="background:var(--ink);color:#e2e8f0;padding:16px 50px 16px 16px;
                            border-radius:var(--radius-sm);font-size:12px;font-family:var(--font-mono);
                            overflow-x:auto;line-height:1.6;margin:0;max-height:240px;overflow-y:auto;">{claude_md_escaped}</pre>
                {_COPY_BTN}
            </div>
            <p style="font-size:12px;color:var(--ink-light);margin:8px 0 0;">
                Download: <a href="/setup/claude.md" style="color:var(--accent);">CLAUDE.md</a> | <a href="/setup/cursorrules" style="color:var(--accent);">.cursorrules</a>
            </p>
        </div>

        <!-- Step 3: Get API key -->
        <div style="margin-bottom:40px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
                <span style="width:32px;height:32px;border-radius:50%;background:var(--accent);color:#0F1D30;
                             display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;flex-shrink:0;">3</span>
                <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin:0;">Get your API key <span style="font-size:14px;font-weight:400;color:var(--ink-muted);">(free)</span></h2>
            </div>
            <p style="font-size:14px;color:var(--ink-muted);margin:0 0 16px;line-height:1.6;">
                Without a key you get 3 searches/day. A free key gets 10/month. Pro gets 1,000/month + market intelligence.
            </p>
            <div style="display:flex;gap:12px;flex-wrap:wrap;">
                <a href="{"/dashboard" if user else "/login?next=/dashboard"}"
                   class="btn btn-primary" style="padding:12px 24px;font-size:14px;text-decoration:none;min-height:44px;">
                    {"Get your API key" if user else "Sign in to get your API key"}
                </a>
            </div>
        </div>

        <!-- What happens next -->
        <div class="card" style="padding:24px;">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin:0 0 12px;">What happens next</h3>
            <div style="font-size:14px;color:var(--ink-muted);line-height:1.8;">
                Your AI agent will automatically search IndieStack when you need developer infrastructure.
                Instead of generating auth code from scratch, it finds Clerk or Lucia. Instead of writing
                a payment flow, it finds LemonSqueezy or Polar. 40 categories, 6,500+ tools, verified
                compatibility data.
            </div>
        </div>

    </div>

    <script>
    // Tab switching
    document.querySelectorAll('.setup-tab').forEach(btn => {{
        btn.addEventListener('click', () => {{
            document.querySelectorAll('.setup-tab').forEach(b => {{
                b.classList.remove('active');
                b.style.background = 'transparent';
            }});
            btn.classList.add('active');
            btn.style.background = 'var(--card-bg)';
            const tab = btn.dataset.tab;
            document.querySelectorAll('.setup-panel').forEach(p => {{
                p.style.display = p.dataset.tab === tab ? 'block' : 'none';
            }});
        }});
    }});

    // Copy buttons — copy the text content of the adjacent <pre>
    document.querySelectorAll('.copy-btn').forEach(btn => {{
        btn.addEventListener('click', () => {{
            const pre = btn.parentElement.querySelector('pre.copyable');
            if (pre) {{
                navigator.clipboard.writeText(pre.textContent);
                btn.textContent = 'Copied!';
                setTimeout(() => btn.textContent = 'Copy', 2000);
            }}
        }});
    }});
    </script>
    '''

    return HTMLResponse(page_shell("Set up IndieStack", body, user=user))


@router.get("/setup/claude.md", response_class=PlainTextResponse)
async def claude_md_download(request: Request):
    """Downloadable CLAUDE.md file."""
    return PlainTextResponse(
        CLAUDE_MD_TEMPLATE.strip(),
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=CLAUDE.md"},
    )


@router.get("/setup/cursorrules", response_class=PlainTextResponse)
async def cursorrules_download(request: Request):
    """Downloadable .cursorrules file."""
    return PlainTextResponse(
        CURSORRULES_TEMPLATE.strip(),
        media_type="text/markdown",
        headers={"Content-Disposition": "attachment; filename=.cursorrules"},
    )

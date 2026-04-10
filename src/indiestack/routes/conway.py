"""IndieStack Conway — landing page for always-on AI coding agents."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell

router = APIRouter()


@router.get("/conway", response_class=HTMLResponse)
async def conway_page(request: Request):
    user = request.state.user

    body = '''
    <div style="max-width:760px;margin:0 auto;padding:80px 24px 64px;">

        <!-- Badge -->
        <div style="display:inline-block;padding:6px 14px;border-radius:999px;
                     background:rgba(0,212,245,0.08);border:1px solid rgba(0,212,245,0.2);
                     font-size:12px;font-weight:600;letter-spacing:0.05em;
                     text-transform:uppercase;color:var(--accent);margin-bottom:24px;">
            For Always-On Agents
        </div>

        <!-- Hero -->
        <h1 style="font-family:var(--font-display);font-size:clamp(32px,5vw,48px);
                    color:var(--ink);line-height:1.15;margin-bottom:16px;">
            Your agent runs 24/7.<br>
            Its tool knowledge shouldn't be frozen.
        </h1>
        <p style="font-size:18px;color:var(--ink-muted);line-height:1.7;margin-bottom:48px;max-width:600px;">
            IndieStack gives always-on agents like Conway live access to 6,500+
            developer tools — with confidence scores, migration paths, and
            session-aware context that improves across runs.
        </p>

        <!-- Four pillars -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px;margin-bottom:56px;">

            <div class="card" style="padding:28px;cursor:default;">
                <div style="font-size:24px;margin-bottom:12px;">&#x1F50D;</div>
                <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                    Structured Search
                </h3>
                <p style="font-size:14px;color:var(--ink-muted);line-height:1.6;">
                    23 MCP tools. Search by need, compare alternatives, check compatibility —
                    all returning structured data your agent can act on directly.
                </p>
            </div>

            <div class="card" style="padding:28px;cursor:default;">
                <div style="font-size:24px;margin-bottom:12px;">&#x1F4CA;</div>
                <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                    Confidence Rationale
                </h3>
                <p style="font-size:14px;color:var(--ink-muted);line-height:1.6;">
                    Every result includes a confidence score with reasons — active maintenance,
                    real GitHub data, install verification. Your agent can explain why it picked a tool.
                </p>
            </div>

            <div class="card" style="padding:28px;cursor:default;">
                <div style="font-size:24px;margin-bottom:12px;">&#x1F504;</div>
                <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                    Session Tracking
                </h3>
                <p style="font-size:14px;color:var(--ink-muted);line-height:1.6;">
                    Pass a <code style="font-family:var(--font-mono);font-size:13px;">session_id</code>
                    and IndieStack remembers what your agent searched, shortlisted, and integrated
                    across runs.
                </p>
            </div>

            <div class="card" style="padding:28px;cursor:default;">
                <div style="font-size:24px;margin-bottom:12px;">&#x26A1;</div>
                <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                    Zero Config
                </h3>
                <p style="font-size:14px;color:var(--ink-muted);line-height:1.6;">
                    No API key, no account, no rate limits for search.
                    One line to install, immediately useful. Agents shouldn't fight setup.
                </p>
            </div>
        </div>

        <!-- Install CTA -->
        <div style="background:var(--cream-dark);border:1px solid var(--border);
                     border-radius:var(--radius-md);padding:32px;margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
                Get started in one line
            </h2>
            <p style="font-size:14px;color:var(--ink-muted);margin-bottom:20px;">
                Install the MCP server and your agent has access to the full catalog.
            </p>
            <div style="position:relative;">
                <pre style="background:var(--code-bg);border:1px solid var(--border);
                            border-radius:var(--radius-sm);padding:16px 20px;
                            font-family:var(--font-mono);font-size:14px;color:var(--ink);
                            overflow-x:auto;margin:0;">uvx --from indiestack indiestack-mcp</pre>
            </div>
            <p style="font-size:12px;color:var(--ink-muted);margin-top:12px;">
                Or add to your Claude MCP config:
                <code style="font-family:var(--font-mono);font-size:12px;">
                    {"mcpServers": {"indiestack": {"command": "uvx", "args": ["--from", "indiestack", "indiestack-mcp"]}}}
                </code>
            </p>
        </div>

        <!-- Technical footnote -->
        <div style="border-top:1px solid var(--border);padding-top:32px;margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                For agent developers
            </h2>
            <div style="display:grid;gap:12px;">
                <div style="display:flex;gap:12px;align-items:baseline;">
                    <code style="font-family:var(--font-mono);font-size:13px;color:var(--accent);white-space:nowrap;">context</code>
                    <span style="font-size:14px;color:var(--ink-muted);line-height:1.6;">
                        Pass a structured context param (framework, language, project type) to
                        bias results toward compatible tools.
                    </span>
                </div>
                <div style="display:flex;gap:12px;align-items:baseline;">
                    <code style="font-family:var(--font-mono);font-size:13px;color:var(--accent);white-space:nowrap;">session_id</code>
                    <span style="font-size:14px;color:var(--ink-muted);line-height:1.6;">
                        Unique per-project string. Enables shortlisting, outcome tracking, and
                        cross-session memory so your agent gets smarter over time.
                    </span>
                </div>
                <div style="display:flex;gap:12px;align-items:baseline;">
                    <code style="font-family:var(--font-mono);font-size:13px;color:var(--accent);white-space:nowrap;">report_outcome</code>
                    <span style="font-size:14px;color:var(--ink-muted);line-height:1.6;">
                        After integrating a tool, report success/failure. This feeds the
                        recommendation engine — every agent makes the catalog better.
                    </span>
                </div>
            </div>
        </div>

        <!-- Links -->
        <div style="display:flex;flex-wrap:wrap;gap:12px;margin-bottom:40px;">
            <a href="/setup" style="display:inline-flex;align-items:center;gap:8px;
                                    padding:12px 24px;background:var(--accent);color:white;
                                    border-radius:var(--radius-sm);text-decoration:none;
                                    font-weight:600;font-size:14px;">
                Setup Guide &#x2192;
            </a>
            <a href="/sla" style="display:inline-flex;align-items:center;gap:8px;
                                  padding:12px 24px;background:var(--cream-dark);
                                  border:1px solid var(--border);color:var(--ink);
                                  border-radius:var(--radius-sm);text-decoration:none;
                                  font-weight:600;font-size:14px;">
                SLA &#x2192;
            </a>
            <a href="/api/docs" style="display:inline-flex;align-items:center;gap:8px;
                                       padding:12px 24px;background:var(--cream-dark);
                                       border:1px solid var(--border);color:var(--ink);
                                       border-radius:var(--radius-sm);text-decoration:none;
                                       font-weight:600;font-size:14px;">
                API Docs &#x2192;
            </a>
        </div>

        <p style="font-size:13px;color:var(--ink-muted);line-height:1.6;">
            IndieStack is free for all agents. No API key required.
            <a href="/pricing" style="color:var(--accent);text-decoration:none;">Maker Pro</a>
            ($19/mo) gives tool makers analytics on how agents discover and recommend their tools.
        </p>

    </div>
    '''

    return HTMLResponse(page_shell(
        title="Conway — IndieStack for Always-On Agents",
        description="Live tool intelligence for always-on AI coding agents. 6,500+ tools, confidence scoring, session tracking, zero config.",
        body=body,
        user=user,
        canonical="/conway",
    ))

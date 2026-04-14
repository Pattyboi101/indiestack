"""IndieStack SLA — uptime commitments, latency targets, incident response."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell

router = APIRouter()


@router.get("/sla", response_class=HTMLResponse)
async def sla_page(request: Request):
    user = request.state.user

    body = '''
    <div style="max-width:720px;margin:0 auto;padding:64px 24px;">

        <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);line-height:1.2;margin-bottom:8px;">
            Service Level Agreement
        </h1>
        <p style="font-size:18px;color:var(--ink-muted);line-height:1.6;margin-bottom:8px;">
            Honest commitments. No legal boilerplate.
        </p>
        <p style="font-size:13px;color:var(--ink-muted);margin-bottom:48px;">
            Effective: April 2026 &nbsp;·&nbsp; Last updated: April 7, 2026
        </p>

        <!-- Commitment cards -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:48px;">
            <div class="card" style="padding:24px;text-align:center;cursor:default;">
                <div style="font-family:var(--font-display);font-size:32px;color:var(--accent);">99.5%</div>
                <div style="font-size:14px;font-weight:600;color:var(--ink);margin:4px 0;">Monthly Uptime</div>
                <div style="font-size:12px;color:var(--ink-muted);">Measured on indiestack.ai</div>
            </div>
            <div class="card" style="padding:24px;text-align:center;cursor:default;">
                <div style="font-family:var(--font-display);font-size:32px;color:var(--accent);">&lt;150ms</div>
                <div style="font-size:14px;font-weight:600;color:var(--ink);margin:4px 0;">API p95 Latency</div>
                <div style="font-size:12px;color:var(--ink-muted);">Search + tool detail endpoints</div>
            </div>
            <div class="card" style="padding:24px;text-align:center;cursor:default;">
                <div style="font-family:var(--font-display);font-size:32px;color:var(--accent);">1h</div>
                <div style="font-size:14px;font-weight:600;color:var(--ink);margin:4px 0;">Critical Response</div>
                <div style="font-size:12px;color:var(--ink-muted);">P1 incidents during business hours</div>
            </div>
        </div>

        <!-- Sections -->
        <div style="border-top:1px solid var(--border);padding-top:40px;margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">Uptime</h2>
            <p style="color:var(--ink-muted);line-height:1.7;margin-bottom:12px;">
                We target <strong style="color:var(--ink);">99.5% monthly uptime</strong> for indiestack.ai and all public API endpoints
                (<code style="font-family:var(--font-mono);font-size:13px;">/api/tools/search</code>, <code style="font-family:var(--font-mono);font-size:13px;">/api/tools/{slug}</code>, MCP server).
            </p>
            <p style="color:var(--ink-muted);line-height:1.7;margin-bottom:12px;">
                The MCP server (<code style="font-family:var(--font-mono);font-size:13px;">uvx --from indiestack indiestack-mcp</code>) calls the production API.
                Downtime on indiestack.ai affects MCP tool availability.
            </p>
            <p style="color:var(--ink-muted);line-height:1.7;">
                Infrastructure: <a href="https://fly.io" target="_blank" rel="noopener" style="color:var(--accent);text-decoration:none;">Fly.io</a> (sjc region, 2 minimum machines).
                Fly.io status: <a href="https://status.flyio.net" target="_blank" rel="noopener" style="color:var(--accent);text-decoration:none;">status.flyio.net</a>.
            </p>
        </div>

        <div style="border-top:1px solid var(--border);padding-top:40px;margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">API Performance</h2>
            <div style="display:grid;gap:12px;">
                <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px;background:var(--cream-dark);border-radius:var(--radius-sm);border:1px solid var(--border);">
                    <code style="font-family:var(--font-mono);font-size:13px;">GET /api/tools/search</code>
                    <span style="font-weight:600;color:var(--ink);">&lt;150ms p95</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px;background:var(--cream-dark);border-radius:var(--radius-sm);border:1px solid var(--border);">
                    <code style="font-family:var(--font-mono);font-size:13px;">GET /api/tools/{slug}</code>
                    <span style="font-weight:600;color:var(--ink);">&lt;100ms p95</span>
                </div>
                <div style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px;background:var(--cream-dark);border-radius:var(--radius-sm);border:1px solid var(--border);">
                    <code style="font-family:var(--font-mono);font-size:13px;">GET /health</code>
                    <span style="font-weight:600;color:var(--ink);">&lt;50ms p99</span>
                </div>
            </div>
            <p style="font-size:13px;color:var(--ink-muted);margin-top:12px;">
                Targets measured at the Fly.io edge. Cold-start latency (machine wake from stop) may be higher — we run a minimum of 2 machines to minimise this.
            </p>
        </div>

        <div style="border-top:1px solid var(--border);padding-top:40px;margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">Incident Response</h2>
            <div style="display:grid;gap:8px;margin-bottom:16px;">
                <div style="display:grid;grid-template-columns:80px 1fr;gap:16px;align-items:baseline;">
                    <span style="font-weight:700;color:var(--ink);">P1 — Critical</span>
                    <span style="color:var(--ink-muted);">Full outage or data loss. Response within 1 hour during business hours (09:00–18:00 GMT).</span>
                </div>
                <div style="display:grid;grid-template-columns:80px 1fr;gap:16px;align-items:baseline;">
                    <span style="font-weight:700;color:var(--ink);">P2 — High</span>
                    <span style="color:var(--ink-muted);">Search degraded or MCP server returning errors. Response within 4 hours.</span>
                </div>
                <div style="display:grid;grid-template-columns:80px 1fr;gap:16px;align-items:baseline;">
                    <span style="font-weight:700;color:var(--ink);">P3 — Low</span>
                    <span style="color:var(--ink-muted);">UI issues, slow pages, non-critical endpoint failures. Response within 24 hours.</span>
                </div>
            </div>
            <p style="color:var(--ink-muted);line-height:1.7;margin-bottom:12px;">
                Report incidents: <a href="mailto:pajebay1@gmail.com" style="color:var(--accent);text-decoration:none;">pajebay1@gmail.com</a>
                or open an issue at <a href="https://github.com/Pattyboi101/indiestack/issues" target="_blank" rel="noopener" style="color:var(--accent);text-decoration:none;">github.com/Pattyboi101/indiestack</a>.
            </p>
            <p style="color:var(--ink-muted);line-height:1.7;">
                See our full <a href="/trust/incidents" style="color:var(--accent);text-decoration:none;">incident response protocol</a> for severity definitions and response times.
            </p>
        </div>

        <div style="border-top:1px solid var(--border);padding-top:40px;margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">Planned Changes</h2>
            <p style="color:var(--ink-muted);line-height:1.7;margin-bottom:12px;">
                We plan to migrate from SQLite to Postgres in <strong style="color:var(--ink);">Q2 2026</strong> for multi-region read performance.
                We'll announce at least 48 hours in advance and target zero downtime via blue-green deployment.
            </p>
            <p style="color:var(--ink-muted);line-height:1.7;">
                All planned maintenance is announced via <a href="https://github.com/Pattyboi101/indiestack" target="_blank" rel="noopener" style="color:var(--accent);text-decoration:none;">GitHub</a>.
            </p>
        </div>

        <div style="border-top:1px solid var(--border);padding-top:40px;margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">Incident Log</h2>
            <div style="padding:24px;background:var(--cream-dark);border-radius:var(--radius-sm);border:1px solid var(--border);text-align:center;">
                <div style="font-size:32px;margin-bottom:8px;">&#x2714;</div>
                <div style="font-weight:600;color:var(--ink);margin-bottom:4px;">No incidents in the last 90 days</div>
                <div style="font-size:13px;color:var(--ink-muted);margin-bottom:12px;">Incidents will be logged here with timeline and resolution details.</div>
                <a href="/trust/incidents" style="display:inline-block;padding:8px 16px;background:var(--accent);color:white;border-radius:var(--radius-sm);text-decoration:none;font-size:13px;font-weight:600;">View incident response protocol →</a>
            </div>
        </div>

        <div style="border-top:1px solid var(--border);padding-top:32px;">
            <p style="font-size:13px;color:var(--ink-muted);line-height:1.6;">
                IndieStack is built by two founders. We don't offer financial SLA credits — if the service is down, we fix it fast.
                This document reflects our genuine operational targets, not legal minimums.
            </p>
        </div>

    </div>
    '''

    return HTMLResponse(page_shell(
        title="SLA — IndieStack",
        description="IndieStack service level agreement: 99.5% uptime, <150ms API p95, 1h critical response.",
        body=body,
        user=user,
        canonical="/sla",
    ))

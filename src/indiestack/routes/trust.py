"""IndieStack Trust — incident response protocol and incident log."""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell

router = APIRouter()


@router.get("/trust/incidents", response_class=HTMLResponse)
async def incidents_page(request: Request):
    user = request.state.user

    body = '''
    <div style="max-width:720px;margin:0 auto;padding:64px 24px;">

        <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);line-height:1.2;margin-bottom:8px;">
            Incident Response Protocol
        </h1>
        <p style="font-size:18px;color:var(--ink-muted);line-height:1.6;margin-bottom:8px;">
            How we respond to service incidents.
        </p>
        <p style="font-size:13px;color:var(--ink-muted);margin-bottom:48px;">
            Last updated: April 7, 2026
        </p>

        <!-- How to report -->
        <div style="border-top:1px solid var(--border);padding-top:40px;margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">Report an Incident</h2>
            <p style="color:var(--ink-muted);line-height:1.7;margin-bottom:16px;">
                If you spot a problem, let us know immediately:
            </p>
            <ul style="color:var(--ink-muted);line-height:1.8;margin-bottom:16px;padding-left:20px;">
                <li><strong style="color:var(--ink);">Email:</strong> <a href="mailto:hello@indiestack.ai" style="color:var(--accent);text-decoration:none;">hello@indiestack.ai</a> (fastest response)</li>
                <li><strong style="color:var(--ink);">GitHub:</strong> <a href="https://github.com/Pattyboi101/indiestack/issues" target="_blank" rel="noopener" style="color:var(--accent);text-decoration:none;">github.com/Pattyboi101/indiestack/issues</a></li>
                <li><strong style="color:var(--ink);">API Status:</strong> Check <a href="https://indiestack.ai/api/status" style="color:var(--accent);text-decoration:none;">indiestack.ai/api/status</a> for real-time metrics</li>
            </ul>
            <p style="color:var(--ink-muted);line-height:1.7;font-size:13px;">
                Include: what you observed, when it happened, and which endpoint (if API-related). Screenshots are helpful.
            </p>
        </div>

        <!-- Severity levels -->
        <div style="border-top:1px solid var(--border);padding-top:40px;margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">Severity Levels</h2>
            <div style="display:grid;gap:12px;">
                <div style="padding:16px;border-radius:var(--radius-sm);border:1px solid var(--border);">
                    <div style="font-weight:700;color:#d32f2f;margin-bottom:6px;">P1 — Critical</div>
                    <div style="font-size:13px;color:var(--ink-muted);">Full outage, MCP server down, data loss, or API errors affecting all users. We aim to respond within 1 hour during business hours (09:00–18:00 GMT).</div>
                </div>
                <div style="padding:16px;border-radius:var(--radius-sm);border:1px solid var(--border);">
                    <div style="font-weight:700;color:#f57c00;margin-bottom:6px;">P2 — High</div>
                    <div style="font-size:13px;color:var(--ink-muted);">Search is slow, partial errors on some endpoints, or degraded availability. Response target: 4 hours.</div>
                </div>
                <div style="padding:16px;border-radius:var(--radius-sm);border:1px solid var(--border);">
                    <div style="font-weight:700;color:#fbc02d;margin-bottom:6px;">P3 — Low</div>
                    <div style="font-size:13px;color:var(--ink-muted);">UI glitches, slow pages, non-critical feature failures, or documentation issues. Response target: 24 hours.</div>
                </div>
            </div>
        </div>

        <!-- Response timeline -->
        <div style="border-top:1px solid var(--border);padding-top:40px;margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">Our Process</h2>
            <div style="display:grid;gap:12px;margin-bottom:24px;">
                <div style="display:grid;grid-template-columns:120px 1fr;gap:16px;align-items:baseline;">
                    <span style="font-weight:700;color:var(--ink);font-size:13px;">Acknowledge</span>
                    <span style="color:var(--ink-muted);font-size:13px;">We receive your report and start investigating (1-2 min for P1).</span>
                </div>
                <div style="display:grid;grid-template-columns:120px 1fr;gap:16px;align-items:baseline;">
                    <span style="font-weight:700;color:var(--ink);font-size:13px;">Investigate</span>
                    <span style="color:var(--ink-muted);font-size:13px;">We check logs, metrics, and deployments to understand the cause.</span>
                </div>
                <div style="display:grid;grid-template-columns:120px 1fr;gap:16px;align-items:baseline;">
                    <span style="font-weight:700;color:var(--ink);font-size:13px;">Mitigate</span>
                    <span style="color:var(--ink-muted);font-size:13px;">We deploy a fix or rollback. For P1, this is the priority.</span>
                </div>
                <div style="display:grid;grid-template-columns:120px 1fr;gap:16px;align-items:baseline;">
                    <span style="font-weight:700;color:var(--ink);font-size:13px;">Post-Mortem</span>
                    <span style="color:var(--ink-muted);font-size:13px;">We identify root cause and prevent recurrence. Shared in incident log below.</span>
                </div>
            </div>
            <p style="color:var(--ink-muted);line-height:1.7;font-size:13px;">
                All P1 incidents and major outages are logged with timeline, impact, root cause, and remediation steps.
            </p>
        </div>

        <!-- Status monitoring -->
        <div style="border-top:1px solid var(--border);padding-top:40px;margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">Real-Time Status</h2>
            <p style="color:var(--ink-muted);line-height:1.7;margin-bottom:16px;">
                Check our health status anytime:
            </p>
            <div style="padding:16px;background:var(--cream-dark);border-radius:var(--radius-sm);border:1px solid var(--border);margin-bottom:12px;">
                <code style="font-family:var(--font-mono);font-size:13px;color:var(--ink);">GET https://indiestack.ai/api/status</code>
                <p style="font-size:12px;color:var(--ink-muted);margin-top:8px;">
                    Returns: uptime %, latency percentiles (p50/p95/p99), error count, last incident, and links to this log.
                </p>
            </div>
            <p style="color:var(--ink-muted);line-height:1.7;font-size:13px;">
                Also check <a href="https://status.flyio.net" target="_blank" rel="noopener" style="color:var(--accent);text-decoration:none;">Fly.io status</a> for infrastructure incidents (we run in the sjc region).
            </p>
        </div>

        <!-- Incident log -->
        <div style="border-top:1px solid var(--border);padding-top:40px;margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">Incident Log</h2>
            <div style="padding:24px;background:var(--cream-dark);border-radius:var(--radius-sm);border:1px solid var(--border);text-align:center;">
                <div style="font-size:32px;margin-bottom:8px;">✓</div>
                <div style="font-weight:600;color:var(--ink);margin-bottom:4px;">No major incidents reported</div>
                <div style="font-size:13px;color:var(--ink-muted);">
                    Service has been stable since launch. Significant incidents (P1/P2) will appear here with details.
                </div>
            </div>
        </div>

        <!-- Maintenance -->
        <div style="border-top:1px solid var(--border);padding-top:40px;margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:16px;">Planned Maintenance</h2>
            <p style="color:var(--ink-muted);line-height:1.7;margin-bottom:12px;">
                We announce planned maintenance at least 48 hours in advance on <a href="https://github.com/Pattyboi101/indiestack" target="_blank" rel="noopener" style="color:var(--accent);text-decoration:none;">GitHub</a>.
            </p>
            <p style="color:var(--ink-muted);line-height:1.7;">
                Current plans: Postgres migration and multi-region failover in May 2026.
            </p>
        </div>

        <div style="border-top:1px solid var(--border);padding-top:32px;">
            <p style="font-size:13px;color:var(--ink-muted);line-height:1.6;">
                Questions? Email <a href="mailto:hello@indiestack.ai" style="color:var(--accent);text-decoration:none;">hello@indiestack.ai</a>.
                Read our full <a href="https://indiestack.ai/sla" style="color:var(--accent);text-decoration:none;">SLA page</a> for uptime commitments.
            </p>
        </div>

    </div>
    '''

    return HTMLResponse(page_shell(
        title="Incident Response — IndieStack",
        description="How we respond to service incidents and maintain reliability.",
        body=body,
        user=user,
        canonical="/trust/incidents",
    ))

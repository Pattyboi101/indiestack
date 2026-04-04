"""Data Product — /data route.

Marketing page selling API access to migration intelligence data.
Target: tool maker marketing teams ($299-999/mo).
"""

from html import escape
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell

router = APIRouter()


@router.get("/data", response_class=HTMLResponse)
async def data_product_page(request: Request):
    user = request.state.user
    d = request.state.db

    # Live stats for credibility
    c = await d.execute("SELECT COUNT(DISTINCT repo) as n FROM verified_combos")
    repos = (await c.fetchone())["n"]
    c = await d.execute("SELECT COUNT(*) as n FROM migration_paths")
    migrations = (await c.fetchone())["n"]
    c = await d.execute("SELECT COUNT(*) as n FROM verified_combos")
    combos = (await c.fetchone())["n"]
    c = await d.execute("SELECT COUNT(DISTINCT from_package || '→' || to_package) as n FROM migration_paths")
    unique_paths = (await c.fetchone())["n"]

    # Pre-compute parts that need escaping (Python 3.11 f-string backslash limitation)
    repos_fmt = f"{repos:,}"
    migrations_fmt = f"{migrations:,}"
    paths_fmt = f"{unique_paths:,}"
    combos_fmt = f"{combos:,}"
    stat_repos = _proof_stat(repos_fmt, "Repos Scanned")
    stat_mig = _proof_stat(migrations_fmt, "Migration Events")
    stat_paths = _proof_stat(paths_fmt, "Unique Paths")
    stat_combos = _proof_stat(combos_fmt, "Verified Combos")
    uc1 = _use_case("Competitive Intelligence",
        "See how many repos migrated FROM your competitor TO you — or the other way around. Real numbers, not surveys.",
        "var(--slate)")
    uc2 = _use_case("Market Sizing",
        "How many active repos use your category of tool? What is the total addressable market based on actual adoption data?",
        "var(--gold)")
    uc3 = _use_case("Win/Loss Analysis",
        "Which specific repos switched away from you? What did they switch to? Identify patterns in churn before it becomes a trend.",
        "#EF4444")
    uc4 = _use_case("Content Marketing",
        'Publish data-backed migration reports. "73% of repos that left Moment.js chose date-fns." Content that writes itself.',
        "#10B981")

    body = f'''
    <div style="max-width:800px;margin:0 auto;padding:24px 16px;">

        <!-- Hero -->
        <div style="text-align:center;padding:48px 0 40px;">
            <div style="font-family:var(--font-mono);font-size:var(--text-xs);color:var(--slate);text-transform:uppercase;letter-spacing:0.1em;margin-bottom:12px;">Migration Intelligence API</div>
            <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);color:var(--ink);margin:0 0 16px;line-height:1.15;">
                Know where developers are<br>moving — before they do
            </h1>
            <p style="color:var(--ink-muted);font-size:var(--text-md);margin:0 0 32px;max-width:550px;margin-left:auto;margin-right:auto;line-height:1.6;">
                Real migration data from {repos_fmt} GitHub repos. See which packages developers
                are abandoning, what they're switching to, and which combinations actually work in production.
            </p>
            <a href="#pricing" class="btn-primary" style="padding:14px 32px;font-size:var(--text-md);text-decoration:none;">
                Get API Access
            </a>
        </div>

        <!-- Live proof -->
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--border);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;margin-bottom:48px;">
            {stat_repos}
            {stat_mig}
            {stat_paths}
            {stat_combos}
        </div>

        <!-- Use cases -->
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:var(--heading-md);color:var(--ink);text-align:center;margin:0 0 32px;">
                Built for tool makers
            </h2>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:20px;">
                {uc1}
                {uc2}
                {uc3}
                {uc4}
            </div>
        </div>

        <!-- API preview -->
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:var(--heading-md);color:var(--ink);text-align:center;margin:0 0 8px;">
                Simple REST API
            </h2>
            <p style="color:var(--ink-muted);font-size:var(--text-sm);text-align:center;margin:0 0 24px;">
                JSON responses. No SDK required.
            </p>
            <div style="background:var(--terracotta-dark);border-radius:var(--radius-lg);padding:24px;overflow-x:auto;">
                <pre style="margin:0;font-family:var(--font-mono);font-size:var(--text-sm);color:rgba(255,255,255,0.9);line-height:1.7;"><span style="color:var(--ink-muted);">// Who's migrating away from express?</span>
<span style="color:var(--slate);">GET</span> /api/migrations?package=express

<span style="color:var(--ink-muted);">// Response</span>
{{
  "package": "express",
  "migrating_from": [
    {{
      "to": "fastify",
      "count": 12,
      "confidence": "swap",
      "sample_repos": ["vercel/next.js", "..."]
    }},
    {{
      "to": "hono",
      "count": 8,
      "confidence": "swap"
    }}
  ]
}}

<span style="color:var(--ink-muted);">// What works with prisma in production?</span>
<span style="color:var(--slate);">GET</span> /api/combos?package=prisma

<span style="color:var(--ink-muted);">// CI outcomes for a specific manifest</span>
<span style="color:var(--slate);">GET</span> /api/moat/stats</pre>
            </div>
        </div>

        <!-- Pricing -->
        <div id="pricing" style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:var(--heading-md);color:var(--ink);text-align:center;margin:0 0 32px;">
                Pricing
            </h2>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:20px;max-width:750px;margin:0 auto;">

                <!-- Explorer -->
                <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-lg);padding:28px;">
                    <div style="font-family:var(--font-body);font-weight:600;font-size:var(--text-sm);color:var(--ink-muted);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:12px;">Explorer</div>
                    <div style="font-family:var(--font-display);font-size:var(--heading-md);color:var(--ink);margin-bottom:4px;">Free</div>
                    <div style="font-size:var(--text-xs);color:var(--ink-muted);margin-bottom:20px;">For indie devs and researchers</div>
                    <ul style="list-style:none;padding:0;margin:0 0 24px;font-size:var(--text-sm);color:var(--ink-light);line-height:2;">
                        <li>&#10003; Browse /migrations page</li>
                        <li>&#10003; 50 API queries/day (free key)</li>
                        <li>&#10003; Migration data in /analyze results</li>
                    </ul>
                    <a href="/developer" class="btn-secondary" style="display:block;text-align:center;padding:10px;text-decoration:none;font-size:var(--text-sm);">
                        Get Free Key
                    </a>
                </div>

                <!-- Pro -->
                <div style="background:var(--card-bg);border:2px solid var(--slate);border-radius:var(--radius-lg);padding:28px;position:relative;">
                    <div style="position:absolute;top:-12px;right:20px;background:var(--slate);color:white;font-size:var(--text-xs);font-weight:600;padding:4px 12px;border-radius:12px;">POPULAR</div>
                    <div style="font-family:var(--font-body);font-weight:600;font-size:var(--text-sm);color:var(--slate);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:12px;">Pro</div>
                    <div style="font-family:var(--font-display);font-size:var(--heading-md);color:var(--ink);margin-bottom:4px;">$299<span style="font-size:var(--text-sm);color:var(--ink-muted);font-family:var(--font-body);">/mo</span></div>
                    <div style="font-size:var(--text-xs);color:var(--ink-muted);margin-bottom:20px;">For tool maker marketing teams</div>
                    <ul style="list-style:none;padding:0;margin:0 0 24px;font-size:var(--text-sm);color:var(--ink-light);line-height:2;">
                        <li>&#10003; Unlimited API queries</li>
                        <li>&#10003; Competitive migration tracking</li>
                        <li>&#10003; Weekly CSV data exports</li>
                        <li>&#10003; Repo-level detail</li>
                        <li>&#10003; Combo verification data</li>
                    </ul>
                    <a href="mailto:pajebay1@gmail.com?subject=Migration%20Intelligence%20Pro" class="btn-primary" style="display:block;text-align:center;padding:10px;text-decoration:none;font-size:var(--text-sm);">
                        Contact Us
                    </a>
                </div>

                <!-- Enterprise -->
                <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-lg);padding:28px;">
                    <div style="font-family:var(--font-body);font-weight:600;font-size:var(--text-sm);color:var(--gold);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:12px;">Enterprise</div>
                    <div style="font-family:var(--font-display);font-size:var(--heading-md);color:var(--ink);margin-bottom:4px;">Custom</div>
                    <div style="font-size:var(--text-xs);color:var(--ink-muted);margin-bottom:20px;">For VCs and market intelligence</div>
                    <ul style="list-style:none;padding:0;margin:0 0 24px;font-size:var(--text-sm);color:var(--ink-light);line-height:2;">
                        <li>&#10003; Everything in Pro</li>
                        <li>&#10003; Raw data licensing</li>
                        <li>&#10003; Custom scanning targets</li>
                        <li>&#10003; CI outcome data feed</li>
                        <li>&#10003; Dedicated support</li>
                    </ul>
                    <a href="mailto:pajebay1@gmail.com?subject=Migration%20Intelligence%20Enterprise" class="btn-secondary" style="display:block;text-align:center;padding:10px;text-decoration:none;font-size:var(--text-sm);">
                        Let's Talk
                    </a>
                </div>
            </div>
        </div>

        <!-- Data freshness note -->
        <div style="text-align:center;padding:24px;color:var(--ink-muted);font-size:var(--text-xs);">
            Data updated continuously from live GitHub repo scans. Currently tracking {repos_fmt} repositories.
            <br>Migration paths verified from real git commit history — not surveys or estimates.
        </div>
    </div>'''

    return HTMLResponse(page_shell(
        "Migration Intelligence API — IndieStack",
        body,
        description="Real migration data from GitHub repos. See which packages developers are abandoning and what they're switching to. API access for tool makers.",
        canonical="/data",
        user=user,
    ))


def _proof_stat(value: str, label: str) -> str:
    return f'''
    <div style="background:var(--card-bg);padding:20px;text-align:center;">
        <div style="font-family:var(--font-display);font-size:var(--heading-sm);color:var(--ink);">{value}</div>
        <div style="font-family:var(--font-body);font-size:var(--text-xs);color:var(--ink-muted);margin-top:4px;">{label}</div>
    </div>'''


def _use_case(title: str, desc: str, color: str) -> str:
    return f'''
    <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-lg);padding:24px;">
        <div style="width:8px;height:8px;background:{color};border-radius:50%;margin-bottom:12px;"></div>
        <h3 style="font-family:var(--font-body);font-weight:600;font-size:var(--text-sm);color:var(--ink);margin:0 0 8px;">{title}</h3>
        <p style="font-size:var(--text-sm);color:var(--ink-muted);margin:0;line-height:1.5;">{desc}</p>
    </div>'''

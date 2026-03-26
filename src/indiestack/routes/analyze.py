"""Lighthouse for Dependencies — /analyze route."""

import json
from html import escape
from urllib.parse import quote
import httpx
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from indiestack.routes.components import page_shell
from indiestack import db as db_module
from indiestack.analyze import (
    run_analysis, save_analysis, load_analysis, count_analyses, parse_manifest,
)

router = APIRouter()

SAMPLE_PACKAGE_JSON = """{
  "dependencies": {
    "express": "^4.18.2",
    "passport": "^0.7.0",
    "stripe": "^14.0.0",
    "mongoose": "^8.0.0",
    "nodemailer": "^6.9.0"
  },
  "devDependencies": {
    "jest": "^29.7.0",
    "eslint": "^8.50.0"
  }
}"""


def _score_color(score: int) -> str:
    if score >= 80:
        return "#10B981"
    elif score >= 60:
        return "var(--gold)"
    return "#EF4444"


def _score_label(score: int) -> str:
    if score >= 90:
        return "Excellent"
    elif score >= 80:
        return "Good"
    elif score >= 60:
        return "Needs attention"
    return "At risk"


def _freshness_badge(status: str) -> str:
    colors = {
        "active": ("var(--success-bg)", "var(--success-text)", "var(--success-border)"),
        "maintained": ("var(--success-bg)", "var(--success-text)", "var(--success-border)"),
        "stale": ("var(--warning-bg)", "var(--warning-text)", "var(--warning-border)"),
        "dormant": ("var(--error-bg)", "var(--error-text)", "var(--error-border)"),
        "dead": ("var(--error-bg)", "var(--error-text)", "var(--error-border)"),
        "unknown": ("var(--info-bg)", "var(--info-text)", "var(--info-border)"),
    }
    bg, text, border = colors.get(status, colors["unknown"])
    return f'<span style="display:inline-block;padding:2px 8px;border-radius:var(--radius-sm);font-size:var(--text-xs);font-weight:600;background:{bg};color:{text};border:1px solid {border};">{escape(status)}</span>'


def _render_dial(score: int, label: str, size: int = 100) -> str:
    color = _score_color(score)
    r = 45
    circumference = 2 * 3.14159 * r
    offset = circumference - (score / 100) * circumference
    font_size = 28 if size >= 100 else 22
    return f'''<div style="display:flex;flex-direction:column;align-items:center;">
        <svg fill="none" viewBox="0 0 100 100" style="width:{size}px;height:{size}px;transform:rotate(-90deg);">
            <circle cx="50" cy="50" r="{r}" stroke="var(--border)" stroke-width="8" />
            <circle cx="50" cy="50" r="{r}" stroke="{color}" stroke-width="8"
                stroke-dasharray="{circumference:.1f}" stroke-dashoffset="{offset:.1f}"
                stroke-linecap="round" style="transition:stroke-dashoffset 1s ease-out;" />
            <text x="50" y="50" font-family="var(--font-display)" font-size="{font_size}" font-weight="bold"
                fill="var(--ink)" text-anchor="middle" dominant-baseline="central"
                transform="rotate(90 50 50)">{score}</text>
        </svg>
        <span style="font-family:var(--font-body);font-size:var(--text-xs);font-weight:600;color:var(--ink-muted);margin-top:4px;">{escape(label)}</span>
    </div>'''


def _render_form(prefill: str = "") -> str:
    return f'''
    <div style="max-width:700px;margin:0 auto;">
        <div style="text-align:center;margin-bottom:32px;">
            <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);color:var(--ink);margin:0 0 8px;">
                Stack Health Check
            </h1>
            <p style="font-family:var(--font-body);color:var(--ink-muted);font-size:var(--text-md);margin:0;">
                Paste your dependency file. Get a health score in seconds.
            </p>
        </div>

        <form method="POST" action="/analyze" id="analyze-form">
            <div style="margin-bottom:16px;">
                <div style="display:flex;gap:12px;margin-bottom:12px;">
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
                        <input type="radio" name="manifest_type" value="package.json" checked
                            style="accent-color:var(--gold);"> package.json
                    </label>
                    <label style="display:flex;align-items:center;gap:6px;cursor:pointer;">
                        <input type="radio" name="manifest_type" value="requirements.txt"
                            style="accent-color:var(--gold);"> requirements.txt
                    </label>
                </div>
                <textarea name="manifest" rows="14"
                    placeholder='Paste your package.json or requirements.txt here...'
                    style="width:100%;font-family:var(--font-mono);font-size:var(--text-sm);
                    padding:16px;border:1px solid var(--border);border-radius:var(--radius-md);
                    background:var(--card-bg);color:var(--ink);resize:vertical;
                    line-height:1.5;">{escape(prefill)}</textarea>
            </div>
            <div style="display:flex;gap:12px;align-items:center;">
                <button type="submit" class="btn-primary"
                    style="padding:12px 32px;font-size:var(--text-md);min-width:180px;">
                    Analyze Stack
                </button>
                <button type="button" id="try-sample" class="btn-secondary"
                    style="padding:12px 20px;font-size:var(--text-sm);">
                    Try sample
                </button>
            </div>
        </form>
    </div>

    <script>
    document.getElementById('try-sample').addEventListener('click', function() {{
        document.querySelector('textarea[name="manifest"]').value = {json.dumps(SAMPLE_PACKAGE_JSON)};
        document.querySelector('input[value="package.json"]').checked = true;
    }});
    </script>'''


def _render_results(result: dict, user=None, share_uuid: str = "") -> str:
    s = result["score"]
    total = s["total"]
    color = _score_color(total)
    label = _score_label(total)
    matched = result["packages_matched"]
    total_pkgs = result["packages_total"]
    pct = int((matched / total_pkgs) * 100) if total_pkgs else 0

    # Main score
    main_dial = _render_dial(total, "Overall", 140)
    sub_dials = "".join([
        _render_dial(s["freshness"], "Freshness", 80),
        _render_dial(s["cohesion"], "Cohesion", 80),
        _render_dial(s["modernity"], "Modernity", 80),
    ])

    # Per-dependency table
    dep_rows = ""
    for mp in result["matched"]:
        t = mp["tool"]
        f = mp.get("freshness", {})
        status = f.get("status", "unknown")
        badge = _freshness_badge(status)
        dep_rows += f'''<tr>
            <td style="padding:10px 12px;font-family:var(--font-mono);font-size:var(--text-sm);">
                <a href="/tool/{escape(t['slug'])}" style="color:var(--slate);text-decoration:none;">{escape(mp['package'])}</a>
            </td>
            <td style="padding:10px 12px;">{escape(t['name'])}</td>
            <td style="padding:10px 12px;text-align:center;">{badge}</td>
        </tr>'''

    # Unmatched packages
    unmatched_html = ""
    if result["unmatched"]:
        unmatched_list = ", ".join(
            f'<code style="font-size:var(--text-xs);background:var(--cream-dark);padding:2px 6px;border-radius:4px;">{escape(p)}</code>'
            for p in result["unmatched"][:20]
        )
        remaining = len(result["unmatched"]) - 20
        if remaining > 0:
            unmatched_list += f" +{remaining} more"
        unmatched_html = f'''
        <div style="margin-top:24px;padding:16px;background:var(--info-bg);border:1px solid var(--info-border);border-radius:var(--radius-md);">
            <strong style="color:var(--info-text);font-size:var(--text-sm);">Not in catalog ({len(result['unmatched'])})</strong>
            <p style="margin:8px 0 0;font-size:var(--text-sm);color:var(--ink-muted);line-height:1.6;">{unmatched_list}</p>
        </div>'''

    # Modernity suggestions
    modernity_html = ""
    if result["modernity_details"]:
        mod_items = ""
        for md in result["modernity_details"]:
            alts = ", ".join(
                f'<a href="/tool/{escape(a["slug"])}" style="color:var(--slate);text-decoration:none;font-weight:600;">{escape(a["name"])}</a>'
                for a in md["alternatives"]
            )
            mod_items += f'''<li style="margin-bottom:8px;">
                <strong>{escape(md["name"])}</strong> — consider: {alts}
            </li>'''
        modernity_html = f'''
        <div style="margin-top:24px;">
            <h3 style="font-family:var(--font-display);font-size:var(--text-lg);margin:0 0 12px;">
                Alternatives to explore
            </h3>
            <ul style="font-family:var(--font-body);font-size:var(--text-sm);color:var(--ink-light);line-height:1.6;padding-left:20px;">
                {mod_items}
            </ul>
        </div>'''

    # Cohesion pairs
    cohesion_html = ""
    if result["cohesion_details"]:
        pair_items = ""
        for cd in result["cohesion_details"]:
            icon = "&#10003;" if cd["status"] == "compatible" else "&#9888;"
            pair_color = "var(--success-text)" if cd["status"] == "compatible" else "var(--warning-text)"
            pair_items += f'''<li style="margin-bottom:4px;">
                <span style="color:{pair_color};">{icon}</span>
                <code>{escape(cd["a"])}</code> + <code>{escape(cd["b"])}</code>
                — {cd["status"]} ({cd["evidence"]} reports)
            </li>'''
        cohesion_html = f'''
        <div style="margin-top:24px;">
            <h3 style="font-family:var(--font-display);font-size:var(--text-lg);margin:0 0 12px;">
                Compatibility data
            </h3>
            <ul style="font-family:var(--font-body);font-size:var(--text-sm);color:var(--ink-light);line-height:1.8;padding-left:20px;list-style:none;">
                {pair_items}
            </ul>
        </div>'''

    # Share URL
    share_text = f"My stack scored {total}/100 on IndieStack Stack Health Check"
    result_link = f"https://indiestack.ai/analyze/{share_uuid}" if share_uuid else "https://indiestack.ai/analyze"
    share_url = f"https://twitter.com/intent/tweet?text={quote(share_text)}&url={quote(result_link)}"

    return f'''
    <div style="max-width:700px;margin:0 auto;">
        <!-- Score header -->
        <div style="text-align:center;padding:32px 0 24px;">
            <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);color:var(--ink);margin:0 0 4px;">
                Stack Health Check
            </h1>
            <p style="color:var(--ink-muted);font-size:var(--text-md);margin:0;">
                {matched} of {total_pkgs} packages matched ({pct}% coverage)
            </p>
        </div>

        <!-- Score dials -->
        <div style="position:relative;background:linear-gradient(145deg, var(--card-bg), var(--cream-dark));border:1px solid var(--border);border-radius:var(--radius-lg);padding:32px;margin-bottom:24px;text-align:center;overflow:hidden;">
            <div style="margin-bottom:24px;">
                {main_dial}
            </div>
            <p style="font-family:var(--font-display);font-size:var(--text-lg);color:{color};margin:0 0 20px;">{label}</p>
            <div style="display:flex;justify-content:center;gap:32px;flex-wrap:wrap;">
                {sub_dials}
            </div>
            <div style="position:absolute;bottom:8px;right:12px;opacity:0.35;font-family:var(--font-body);font-size:11px;font-weight:600;color:var(--ink-muted);">indiestack.ai</div>
        </div>

        <!-- Share + Reanalyze -->
        <div style="display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap;">
            <a href="{escape(share_url)}"
                target="_blank" rel="noopener" class="btn-secondary"
                style="padding:10px 20px;font-size:var(--text-sm);text-decoration:none;">
                Share score
            </a>
            <a href="/analyze" class="btn-secondary"
                style="padding:10px 20px;font-size:var(--text-sm);text-decoration:none;">
                Analyze another
            </a>
        </div>

        <!-- Dependency table -->
        {f"""
        <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;margin-bottom:24px;">
            <table style="width:100%;border-collapse:collapse;font-family:var(--font-body);font-size:var(--text-sm);">
                <thead>
                    <tr style="background:var(--cream-dark);border-bottom:1px solid var(--border);">
                        <th style="padding:10px 12px;text-align:left;font-weight:600;color:var(--ink-muted);">Package</th>
                        <th style="padding:10px 12px;text-align:left;font-weight:600;color:var(--ink-muted);">Tool</th>
                        <th style="padding:10px 12px;text-align:center;font-weight:600;color:var(--ink-muted);">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {dep_rows}
                </tbody>
            </table>
        </div>
        """ if dep_rows else ""}

        {unmatched_html}
        {cohesion_html}
        {modernity_html}

        <!-- CTA -->
        <div style="margin-top:32px;padding:24px;background:var(--cream-dark);border-radius:var(--radius-lg);text-align:center;">
            <p style="font-family:var(--font-body);font-size:var(--text-md);color:var(--ink);margin:0 0 12px;">
                Want continuous stack monitoring via AI agents?
            </p>
            <a href="/pricing" class="btn-primary" style="padding:12px 24px;text-decoration:none;">
                Upgrade to Pro
            </a>
        </div>
    </div>'''


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request):
    user = request.state.user
    body = _render_form()
    return HTMLResponse(page_shell(
        "Stack Health Check | IndieStack",
        body,
        description="Paste your package.json or requirements.txt and get a dependency health score in seconds.",
        user=user,
    ))


@router.post("/analyze", response_class=HTMLResponse)
async def analyze_submit(request: Request, manifest: str = Form(...), manifest_type: str = Form("package.json")):
    user = request.state.user
    d = request.state.db

    # Rate limiting
    user_id = user["id"] if user else None
    session_id = request.cookies.get("session") if not user else None
    if not user_id and not session_id:
        client_ip = request.headers.get("fly-client-ip", request.client.host if request.client else "unknown")
        session_id = f"ip:{client_ip}"
    usage = await count_analyses(d, user_id=user_id, session_id=session_id)

    is_pro = user and user.get("is_pro")
    limit = 1000 if is_pro else 10
    if usage >= limit:
        body = f'''<div style="max-width:600px;margin:40px auto;text-align:center;">
            <h1 style="font-family:var(--font-display);font-size:var(--heading-md);">Analysis limit reached</h1>
            <p style="color:var(--ink-muted);">You've used {usage} of {limit} analyses this month.</p>
            <a href="/pricing" class="btn-primary" style="margin-top:16px;display:inline-block;padding:12px 24px;text-decoration:none;">Upgrade to Pro</a>
        </div>'''
        return HTMLResponse(page_shell("Limit Reached | IndieStack", body, user=user))

    # Validate
    manifest = manifest.strip()
    if len(manifest) > 512_000:
        body = f'''<div style="max-width:600px;margin:40px auto;text-align:center;">
            <h1 style="font-family:var(--font-display);font-size:var(--heading-md);">Manifest too large</h1>
            <p style="color:var(--ink-muted);">Maximum size is 512KB. Try trimming devDependencies.</p>
            <a href="/analyze" class="btn-secondary" style="margin-top:16px;display:inline-block;padding:12px 24px;text-decoration:none;">Try again</a>
        </div>'''
        return HTMLResponse(page_shell("Too Large | IndieStack", body, user=user))
    if not manifest:
        body = _render_form()
        return HTMLResponse(page_shell("Stack Health Check | IndieStack", body, user=user))

    if manifest_type not in ("package.json", "requirements.txt"):
        manifest_type = "package.json"

    try:
        result = await run_analysis(d, manifest, manifest_type)
    except ValueError as e:
        body = f'''<div style="max-width:600px;margin:40px auto;text-align:center;">
            <h1 style="font-family:var(--font-display);font-size:var(--heading-md);">Could not analyze</h1>
            <p style="color:var(--ink-muted);">{escape(str(e))}</p>
            <a href="/analyze" class="btn-secondary" style="margin-top:16px;display:inline-block;padding:12px 24px;text-decoration:none;">Try again</a>
        </div>'''
        return HTMLResponse(page_shell("Error | IndieStack", body, user=user))

    # Save analysis and redirect to shareable URL
    share_uuid = await save_analysis(d, user_id, session_id, manifest_type, result)
    return RedirectResponse(url=f"/analyze/{share_uuid}", status_code=303)


@router.get("/analyze/{share_uuid}", response_class=HTMLResponse)
async def analyze_view(request: Request, share_uuid: str):
    """View a cached analysis by share UUID."""
    user = request.state.user
    d = request.state.db

    result = await load_analysis(d, share_uuid)
    if not result:
        body = f'''<div style="max-width:600px;margin:40px auto;text-align:center;">
            <h1 style="font-family:var(--font-display);font-size:var(--heading-md);">Analysis not found</h1>
            <p style="color:var(--ink-muted);">This analysis may have expired or the link is invalid.</p>
            <a href="/analyze" class="btn-primary" style="margin-top:16px;display:inline-block;padding:12px 24px;text-decoration:none;">Run a new analysis</a>
        </div>'''
        return HTMLResponse(page_shell("Not Found | IndieStack", body, user=user), status_code=404)

    score = result["score"]["total"]
    matched_count = result.get("packages_matched", 0)
    total_pkgs = result.get("packages_total", 0)
    body = _render_results(result, user=user, share_uuid=share_uuid)
    return HTMLResponse(page_shell(
        f"Score: {score}/100 | Stack Health Check",
        body,
        description=f"This stack scored {score}/100 — {matched_count} dependencies analyzed for freshness, compatibility, and modernity.",
        og_image=f"https://indiestack.ai/api/og/analyze/{share_uuid}.svg",
        canonical=f"https://indiestack.ai/analyze/{share_uuid}",
        user=user,
    ))


@router.post("/api/analyze", response_class=JSONResponse)
async def analyze_api(request: Request):
    """JSON API endpoint for MCP and programmatic access."""
    user = request.state.user
    d = request.state.db

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    manifest = body.get("manifest", "").strip()
    manifest_type = body.get("manifest_type", "package.json")

    if not manifest:
        return JSONResponse({"error": "No manifest provided"}, status_code=400)

    if len(manifest) > 512_000:
        return JSONResponse({"error": "Manifest too large (max 512KB)"}, status_code=413)

    if manifest_type not in ("package.json", "requirements.txt"):
        return JSONResponse({"error": "Invalid manifest_type"}, status_code=400)

    # GitHub Actions get unlimited analyses (we want the data volume)
    is_github_action = request.headers.get("x-github-action") == "true"
    github_repo = body.get("repo", "") or request.headers.get("x-github-repo", "")

    # Rate limiting (exempt GitHub Actions)
    if not is_github_action:
        user_id = user["id"] if user else None
        session_id = request.cookies.get("session") if not user else None
        if not user_id and not session_id:
            client_ip = request.headers.get("fly-client-ip", request.client.host if request.client else "unknown")
            session_id = f"ip:{client_ip}"
        usage = await count_analyses(d, user_id=user_id, session_id=session_id)
        is_pro = user and user.get("is_pro")
        limit = 1000 if is_pro else 10
        if usage >= limit:
            return JSONResponse({"error": "Analysis limit reached", "usage": usage, "limit": limit}, status_code=429)
    else:
        user_id = None
        session_id = f"gh:{github_repo}" if github_repo else None

    try:
        result = await run_analysis(d, manifest, manifest_type)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    share_uuid = await save_analysis(d, user_id, session_id, manifest_type, result)
    result["share_url"] = f"https://indiestack.ai/analyze/{share_uuid}"
    return JSONResponse(result)


@router.get("/api/og/analyze/{share_uuid}.svg")
async def og_image(request: Request, share_uuid: str):
    """Dynamic SVG social card for shared analyses."""
    d = request.state.db
    result = await load_analysis(d, share_uuid)
    if not result:
        from fastapi.responses import Response
        return Response(status_code=404)

    score = result["score"]["total"]
    freshness = result["score"]["freshness"]
    cohesion = result["score"]["cohesion"]
    modernity = result["score"]["modernity"]
    matched = result.get("packages_matched", 0)
    total = result.get("packages_total", 0)

    color = "#10B981" if score >= 80 else ("#E2B764" if score >= 60 else "#EF4444")
    label = "Excellent" if score >= 90 else ("Good" if score >= 80 else ("Needs attention" if score >= 60 else "At risk"))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <defs>
    <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#0F1D30"/>
      <stop offset="100%" style="stop-color:#1A2D4A"/>
    </linearGradient>
  </defs>
  <rect width="1200" height="630" fill="url(#bg)" rx="0"/>

  <!-- Score circle -->
  <circle cx="300" cy="300" r="120" fill="none" stroke="#2B4A6E" stroke-width="12"/>
  <circle cx="300" cy="300" r="120" fill="none" stroke="{color}" stroke-width="12"
    stroke-dasharray="{2 * 3.14159 * 120:.0f}"
    stroke-dashoffset="{2 * 3.14159 * 120 - (score / 100) * 2 * 3.14159 * 120:.0f}"
    stroke-linecap="round" transform="rotate(-90 300 300)"/>
  <text x="300" y="290" text-anchor="middle" font-family="Georgia,serif" font-size="72" font-weight="bold" fill="white">{score}</text>
  <text x="300" y="330" text-anchor="middle" font-family="sans-serif" font-size="20" fill="#94A3B8">/100</text>

  <!-- Label -->
  <text x="300" y="470" text-anchor="middle" font-family="Georgia,serif" font-size="28" fill="{color}">{label}</text>

  <!-- Sub scores -->
  <text x="650" y="200" font-family="sans-serif" font-size="22" fill="#94A3B8">Freshness</text>
  <text x="1050" y="200" text-anchor="end" font-family="Georgia,serif" font-size="28" font-weight="bold" fill="white">{freshness}</text>
  <rect x="650" y="215" width="400" height="4" rx="2" fill="#2B4A6E"/>
  <rect x="650" y="215" width="{freshness * 4}" height="4" rx="2" fill="{color}"/>

  <text x="650" y="280" font-family="sans-serif" font-size="22" fill="#94A3B8">Cohesion</text>
  <text x="1050" y="280" text-anchor="end" font-family="Georgia,serif" font-size="28" font-weight="bold" fill="white">{cohesion}</text>
  <rect x="650" y="295" width="400" height="4" rx="2" fill="#2B4A6E"/>
  <rect x="650" y="295" width="{cohesion * 4}" height="4" rx="2" fill="{color}"/>

  <text x="650" y="360" font-family="sans-serif" font-size="22" fill="#94A3B8">Modernity</text>
  <text x="1050" y="360" text-anchor="end" font-family="Georgia,serif" font-size="28" font-weight="bold" fill="white">{modernity}</text>
  <rect x="650" y="375" width="400" height="4" rx="2" fill="#2B4A6E"/>
  <rect x="650" y="375" width="{modernity * 4}" height="4" rx="2" fill="{color}"/>

  <!-- Footer -->
  <text x="650" y="460" font-family="sans-serif" font-size="18" fill="#64748B">{matched} of {total} packages analyzed</text>

  <!-- Branding -->
  <text x="60" y="590" font-family="Georgia,serif" font-size="24" font-weight="bold" fill="#E2B764">IndieStack</text>
  <text x="255" y="590" font-family="sans-serif" font-size="18" fill="#64748B">Stack Health Check</text>
  <text x="1140" y="590" text-anchor="end" font-family="sans-serif" font-size="16" fill="#475569">indiestack.ai/analyze</text>
</svg>'''

    from fastapi.responses import Response
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/api/badge/health/{owner}/{repo}.svg")
async def repo_health_badge(request: Request, owner: str, repo: str):
    """Dynamic shields.io-style badge showing a repo's stack health score."""
    from fastapi.responses import Response
    d = request.state.db

    # Check cache first (analysis from GitHub Action or previous badge request)
    c = await d.execute(
        """SELECT score_total FROM dependency_analyses
           WHERE session_id = ? ORDER BY created_at DESC LIMIT 1""",
        (f"gh:{owner}/{repo}",),
    )
    row = await c.fetchone()

    if row:
        score = row["score_total"] if isinstance(row, dict) else row[0]
    else:
        # Fetch manifest from GitHub and analyze on-the-fly
        try:
            client = httpx.AsyncClient(timeout=10.0)
            # Try package.json first, then requirements.txt
            manifest = None
            manifest_type = "package.json"
            for fname, mtype in [("package.json", "package.json"), ("requirements.txt", "requirements.txt")]:
                resp = await client.get(f"https://raw.githubusercontent.com/{owner}/{repo}/main/{fname}")
                if resp.status_code == 200:
                    manifest = resp.text
                    manifest_type = mtype
                    break
                # Try master branch
                resp = await client.get(f"https://raw.githubusercontent.com/{owner}/{repo}/master/{fname}")
                if resp.status_code == 200:
                    manifest = resp.text
                    manifest_type = mtype
                    break
            await client.aclose()

            if not manifest:
                return _badge_svg("stack health", "no manifest", "#999")

            result = await run_analysis(d, manifest, manifest_type)
            score = result["score"]["total"]
            # Cache it
            await save_analysis(d, None, f"gh:{owner}/{repo}", manifest_type, result)
        except Exception:
            return _badge_svg("stack health", "error", "#999")

    # Generate badge
    color = "#10B981" if score >= 80 else ("#E2B764" if score >= 60 else "#EF4444")
    return _badge_svg("stack health", f"{score}/100", color)


def _badge_svg(label: str, value: str, color: str) -> "Response":
    """Generate a shields.io-style SVG badge."""
    from fastapi.responses import Response
    label_width = len(label) * 7 + 12
    value_width = len(value) * 7 + 12
    total_width = label_width + value_width

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{total_width}" height="20" viewBox="0 0 {total_width} 20">
  <linearGradient id="s" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <clipPath id="r"><rect width="{total_width}" height="20" rx="3" fill="#fff"/></clipPath>
  <g clip-path="url(#r)">
    <rect width="{label_width}" height="20" fill="#555"/>
    <rect x="{label_width}" width="{value_width}" height="20" fill="{color}"/>
    <rect width="{total_width}" height="20" fill="url(#s)"/>
  </g>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="{label_width / 2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
    <text x="{label_width / 2}" y="14">{label}</text>
    <text x="{label_width + value_width / 2}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
    <text x="{label_width + value_width / 2}" y="14">{value}</text>
  </g>
</svg>'''
    return Response(
        content=svg,
        media_type="image/svg+xml",
        headers={"Cache-Control": "public, max-age=3600"},
    )

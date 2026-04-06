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
                Dependency Health Check
            </h1>
            <p style="font-family:var(--font-body);color:var(--ink-muted);font-size:var(--text-md);margin:0 0 4px;">
                Paste your <code style="font-family:var(--font-mono);font-size:0.9em;background:var(--cream-dark);padding:1px 5px;border-radius:4px;">package.json</code> or <code style="font-family:var(--font-mono);font-size:0.9em;background:var(--cream-dark);padding:1px 5px;border-radius:4px;">requirements.txt</code> and get a 0–100 health score,
                per-package freshness status, migration warnings, and smarter alternative suggestions. Free, no login.
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

        <div style="display:flex;gap:20px;justify-content:center;margin-top:20px;flex-wrap:wrap;">
            <span style="font-family:var(--font-body);font-size:var(--text-sm);color:var(--ink-muted);">&#10003;&nbsp;0–100 health score</span>
            <span style="font-family:var(--font-body);font-size:var(--text-sm);color:var(--ink-muted);">&#10003;&nbsp;Freshness per package</span>
            <span style="font-family:var(--font-body);font-size:var(--text-sm);color:var(--ink-muted);">&#10003;&nbsp;Migration signals</span>
            <span style="font-family:var(--font-body);font-size:var(--text-sm);color:var(--ink-muted);">&#10003;&nbsp;Better alternatives</span>
        </div>
    </div>

    <script>
    document.getElementById('try-sample').addEventListener('click', function() {{
        document.querySelector('textarea[name="manifest"]').value = {json.dumps(SAMPLE_PACKAGE_JSON)};
        document.querySelector('input[value="package.json"]').checked = true;
    }});
    </script>'''


def _render_migration_intel(migration_data: list = None) -> str:
    """Render migration intelligence cards for analyze results."""
    if not migration_data:
        return ""

    items = ""
    for m in migration_data[:5]:
        from_pkg = escape(m["from_package"])
        to_pkg = escape(m["to_package"])
        count = m["repo_count"]
        confidence = m["confidence"]
        conf_color = "var(--slate)" if confidence == "swap" else "var(--gold)"

        items += f'''
        <div style="display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--border);">
            <code style="font-family:var(--font-mono);font-size:var(--text-sm);color:#EF4444;">{from_pkg}</code>
            <span style="color:var(--ink-muted);">&#8594;</span>
            <code style="font-family:var(--font-mono);font-size:var(--text-sm);color:#10B981;">{to_pkg}</code>
            <span style="margin-left:auto;font-family:var(--font-mono);font-size:var(--text-xs);color:{conf_color};font-weight:600;">{count} repos</span>
        </div>'''

    return f'''
    <div style="margin-top:24px;">
        <h3 style="font-family:var(--font-display);font-size:var(--text-lg);margin:0 0 4px;">
            Migration intelligence
        </h3>
        <p style="color:var(--ink-muted);font-size:var(--text-xs);margin:0 0 12px;">
            Packages in your stack that developers are actively migrating from — based on real git history.
        </p>
        <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-md);padding:4px 16px;">
            {items}
        </div>
        <a href="/migrations" style="display:inline-block;margin-top:8px;font-size:var(--text-xs);color:var(--slate);text-decoration:none;">
            View all migration data &#8594;
        </a>
    </div>'''


def _render_results(result: dict, user=None, share_uuid: str = "", migration_data: list = None) -> str:
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
        {_render_migration_intel(migration_data)}

        <!-- CTA -->
        <div style="margin-top:32px;padding:24px;background:var(--cream-dark);border-radius:var(--radius-lg);text-align:center;">
            <p style="font-family:var(--font-body);font-size:var(--text-md);color:var(--ink);margin:0 0 12px;">
                Check your dependencies on every PR automatically
            </p>
            <a href="/setup" class="btn-primary" style="padding:12px 24px;text-decoration:none;">
                Set up GitHub Action
            </a>
        </div>
    </div>'''


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/analyze", response_class=HTMLResponse)
async def analyze_page(request: Request):
    user = request.state.user
    body = _render_form()
    return HTMLResponse(page_shell(
        "Dependency Health Check | IndieStack",
        body,
        description="Paste your package.json or requirements.txt. Get a 0–100 health score, per-package freshness, migration warnings, and alternative suggestions. Free, no login.",
        canonical="/analyze",
        user=user,
    ))


@router.post("/analyze", response_class=HTMLResponse)
async def analyze_submit(request: Request, manifest: str = Form(...), manifest_type: str = Form("package.json")):
    user = request.state.user
    d = request.state.db

    # Track usage for analytics (no rate limit — we want volume for the data moat)
    user_id = user["id"] if user else None
    session_id = request.cookies.get("session") if not user else None
    if not user_id and not session_id:
        client_ip = request.headers.get("fly-client-ip", request.client.host if request.client else "unknown")
        session_id = f"ip:{client_ip}"

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

    # Query migration intelligence for packages in this analysis
    user_packages = [m["package"] for m in result.get("matched", [])]
    user_packages += result.get("unmatched", [])
    migration_data = []
    if user_packages:
        placeholders = ",".join("?" for _ in user_packages)
        c = await d.execute(f"""
            SELECT from_package, to_package, confidence,
                   COUNT(DISTINCT repo) as repo_count
            FROM migration_paths
            WHERE from_package IN ({placeholders})
            GROUP BY from_package, to_package
            ORDER BY repo_count DESC
            LIMIT 10
        """, user_packages)
        migration_data = [dict(r) for r in await c.fetchall()]

    body = _render_results(result, user=user, share_uuid=share_uuid, migration_data=migration_data)
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

    # Track source for analytics — all analyses are free (data collection IS the product)
    github_repo = body.get("repo", "") or request.headers.get("x-github-repo", "")
    is_github_action = request.headers.get("x-github-action") == "true"
    user_id = user["id"] if user else None
    if is_github_action:
        session_id = f"gh:{github_repo}" if github_repo else None
    else:
        session_id = request.cookies.get("session") if not user else None
        if not user_id and not session_id:
            client_ip = request.headers.get("fly-client-ip", request.client.host if request.client else "unknown")
            session_id = f"ip:{client_ip}"

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


@router.get("/api/analyze/stats")
async def analyze_stats(request: Request):
    """Pivot metrics dashboard — separates real usage from internal testing."""
    user = request.state.user
    if not user or not user.get("is_admin"):
        return JSONResponse({"error": "Admin only"}, status_code=403)

    d = request.state.db

    # Known internal sessions to exclude from "real" metrics
    # Our IPs, scanner runs, and test sessions
    INTERNAL_FILTER = """
        AND session_id NOT IN ('ip:51.6.194.97', 'ip:212.219.61.254')
        AND session_id NOT LIKE 'audit:%'
        AND (session_id IS NULL OR session_id NOT LIKE 'ip:10.%')
    """
    # Scanner runs used X-GitHub-Action header, stored as gh:{repo}
    # But real Action installs would too — need to check if the repo
    # actually has our workflow file. For now, flag scanner runs by
    # checking if all gh: runs came in the same hour (batch = scanner)
    SCANNER_FILTER = """
        AND session_id NOT IN (
            SELECT session_id FROM dependency_analyses
            WHERE session_id LIKE 'gh:%'
            GROUP BY session_id HAVING COUNT(*) <= 2
            AND MIN(created_at) > datetime('now', '-2 days')
        )
    """

    stats = {}

    # ── North Star Metrics ──
    # Total analyses (all)
    c = await d.execute("SELECT COUNT(*) as cnt FROM dependency_analyses")
    stats["total_all"] = (await c.fetchone())["cnt"]

    # External analyses (excluding our known IPs and scanner)
    c = await d.execute(f"""
        SELECT COUNT(*) as cnt FROM dependency_analyses
        WHERE 1=1 {INTERNAL_FILTER}
    """)
    stats["total_external"] = (await c.fetchone())["cnt"]

    # External in last 14 days
    c = await d.execute(f"""
        SELECT COUNT(*) as cnt FROM dependency_analyses
        WHERE created_at > datetime('now', '-14 days') {INTERNAL_FILTER}
    """)
    stats["external_14d"] = (await c.fetchone())["cnt"]

    # Technographic API calls
    c = await d.execute("""
        SELECT COUNT(*) as cnt FROM search_logs
        WHERE query LIKE '%technographic%' OR source = 'technographic'
    """)
    try:
        stats["technographic_calls"] = (await c.fetchone())["cnt"]
    except Exception:
        stats["technographic_calls"] = 0

    # ── Leading Indicators ──
    # Badge requests (from access logs — we can't track this directly yet)
    stats["badge_requests"] = "not tracked yet — add access log counter"

    # Unique external IPs
    c = await d.execute(f"""
        SELECT COUNT(DISTINCT session_id) as cnt FROM dependency_analyses
        WHERE session_id LIKE 'ip:%' {INTERNAL_FILTER}
    """)
    stats["unique_external_ips"] = (await c.fetchone())["cnt"]

    # GitHub Action installs (repos with gh: session that aren't from scanner batch)
    c = await d.execute("""
        SELECT COUNT(DISTINCT session_id) as cnt FROM dependency_analyses
        WHERE session_id LIKE 'gh:%'
    """)
    stats["total_gh_action_repos"] = (await c.fetchone())["cnt"]

    # ── Data Moat ──
    c = await d.execute("SELECT COUNT(*) as cnt FROM manifest_cooccurrences")
    stats["cooccurrence_pairs"] = (await c.fetchone())["cnt"]

    c = await d.execute("SELECT COUNT(*) as cnt FROM tools WHERE is_reference = 1")
    stats["reference_tools"] = (await c.fetchone())["cnt"]

    c = await d.execute("SELECT COUNT(*) as cnt FROM tools WHERE status = 'approved'")
    stats["total_tools"] = (await c.fetchone())["cnt"]

    c = await d.execute("SELECT COUNT(*) as cnt FROM tool_pairs WHERE success_count > 0")
    stats["verified_pairs"] = (await c.fetchone())["cnt"]

    # report_outcome calls (the feedback loop)
    try:
        c = await d.execute("""
            SELECT COUNT(*) as cnt FROM agent_actions
            WHERE action = 'report_outcome'
        """)
        stats["outcome_reports"] = (await c.fetchone())["cnt"]
    except Exception:
        stats["outcome_reports"] = 0

    # ── Revenue ──
    c = await d.execute("SELECT COUNT(*) as cnt FROM users")
    stats["total_users"] = (await c.fetchone())["cnt"]

    c = await d.execute("SELECT COUNT(*) as cnt FROM users WHERE is_pro = 1")
    try:
        stats["pro_users"] = (await c.fetchone())["cnt"]
    except Exception:
        stats["pro_users"] = 0

    # ── Daily Breakdown (external only) ──
    c = await d.execute(f"""
        SELECT DATE(created_at) as day,
               COUNT(*) as total,
               SUM(CASE WHEN session_id LIKE 'gh:%' THEN 1 ELSE 0 END) as gh_action,
               SUM(CASE WHEN session_id LIKE 'ip:%' THEN 1 ELSE 0 END) as web
        FROM dependency_analyses
        WHERE created_at > datetime('now', '-14 days')
        GROUP BY DATE(created_at) ORDER BY day DESC
    """)
    stats["daily"] = [
        {"day": r["day"], "total": r["total"], "gh_action": r["gh_action"], "web": r["web"]}
        for r in await c.fetchall()
    ]

    # ── Session breakdown ──
    c = await d.execute(f"""
        SELECT session_id, COUNT(*) as cnt
        FROM dependency_analyses
        WHERE session_id IS NOT NULL {INTERNAL_FILTER}
        GROUP BY session_id ORDER BY cnt DESC LIMIT 20
    """)
    stats["top_external_sessions"] = [
        {"session": r["session_id"], "count": r["cnt"]}
        for r in await c.fetchall()
    ]

    # ── Verdict ──
    stats["verdict"] = {
        "external_analyses": stats["external_14d"],
        "target": 250,
        "on_track": stats["external_14d"] >= 18,  # 250/14 days = ~18/day needed
        "days_tracked": len(stats["daily"]),
        "honest_assessment": (
            "No external usage yet" if stats["external_14d"] == 0
            else f"{stats['external_14d']} external analyses — need 250 in 14 days"
        ),
    }

    return JSONResponse(stats)


@router.get("/admin/pivot", response_class=HTMLResponse)
async def pivot_dashboard(request: Request):
    """Visual pivot metrics dashboard."""
    user = request.state.user
    if not user or not user.get("is_admin"):
        from fastapi.responses import RedirectResponse
        return RedirectResponse("/login?next=/admin/pivot")

    d = request.state.db

    # Known internal
    INTERNAL = "('ip:51.6.194.97', 'ip:212.219.61.254')"

    # Totals
    c = await d.execute("SELECT COUNT(*) as cnt FROM dependency_analyses")
    total = (await c.fetchone())["cnt"]

    c = await d.execute(f"SELECT COUNT(*) as cnt FROM dependency_analyses WHERE session_id NOT IN {INTERNAL} AND session_id NOT LIKE 'audit:%'")
    external = (await c.fetchone())["cnt"]

    internal = total - external

    # Data moat
    c = await d.execute("SELECT COUNT(*) as cnt FROM manifest_cooccurrences")
    pairs = (await c.fetchone())["cnt"]
    c = await d.execute("SELECT COUNT(*) as cnt FROM tools WHERE is_reference = 1")
    refs = (await c.fetchone())["cnt"]
    c = await d.execute("SELECT COUNT(*) as cnt FROM tools WHERE status = 'approved' AND is_reference = 0")
    real_tools = (await c.fetchone())["cnt"]

    # Users
    c = await d.execute("SELECT COUNT(*) as cnt FROM users")
    users = (await c.fetchone())["cnt"]

    # Daily breakdown
    c = await d.execute(f"""
        SELECT DATE(created_at) as day,
               COUNT(*) as total,
               SUM(CASE WHEN session_id IN {INTERNAL} OR session_id LIKE 'audit:%' THEN 1 ELSE 0 END) as internal,
               SUM(CASE WHEN session_id NOT IN {INTERNAL} AND session_id NOT LIKE 'audit:%' THEN 1 ELSE 0 END) as external
        FROM dependency_analyses
        WHERE created_at > datetime('now', '-14 days')
        GROUP BY DATE(created_at) ORDER BY day DESC
    """)
    daily_rows = ""
    for r in await c.fetchall():
        ext = r["external"]
        color = "var(--success-text)" if ext > 0 else "var(--ink-muted)"
        daily_rows += f'<tr><td>{r["day"]}</td><td>{r["total"]}</td><td>{r["internal"]}</td><td style="color:{color};font-weight:600;">{ext}</td></tr>'

    # External sessions
    c = await d.execute(f"""
        SELECT session_id, COUNT(*) as cnt
        FROM dependency_analyses
        WHERE session_id NOT IN {INTERNAL} AND session_id NOT LIKE 'audit:%'
        GROUP BY session_id ORDER BY cnt DESC LIMIT 15
    """)
    session_rows = ""
    for r in await c.fetchall():
        session_rows += f'<tr><td style="font-family:var(--font-mono);font-size:12px;">{escape(r["session_id"] or "anonymous")}</td><td>{r["cnt"]}</td></tr>'

    # Verdict
    if external == 0:
        verdict = '<span style="color:var(--error-text);font-weight:700;">No external usage yet</span>'
    elif external < 18:
        verdict = f'<span style="color:var(--warning-text);font-weight:700;">{external} external — need ~18/day for kill criteria</span>'
    else:
        verdict = f'<span style="color:var(--success-text);font-weight:700;">{external} external — on track</span>'

    body = f'''
    <div style="max-width:800px;margin:0 auto;padding:0 16px;">
        <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);margin:24px 0 8px;">Pivot Metrics</h1>
        <p style="color:var(--ink-muted);margin:0 0 24px;">Honest numbers. Internal usage filtered out.</p>

        <!-- Verdict -->
        <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-lg);padding:24px;margin-bottom:24px;">
            <h2 style="font-family:var(--font-display);font-size:var(--text-lg);margin:0 0 8px;">Verdict</h2>
            <p style="font-size:var(--text-lg);margin:0;">{verdict}</p>
        </div>

        <!-- North Star -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:16px;margin-bottom:24px;">
            <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-md);padding:16px;text-align:center;">
                <div style="font-size:32px;font-weight:700;color:var(--ink);">{external}</div>
                <div style="font-size:12px;color:var(--ink-muted);">External Analyses</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-md);padding:16px;text-align:center;">
                <div style="font-size:32px;font-weight:700;color:var(--ink-light);">{internal}</div>
                <div style="font-size:12px;color:var(--ink-muted);">Internal (us)</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-md);padding:16px;text-align:center;">
                <div style="font-size:32px;font-weight:700;color:var(--ink);">{users}</div>
                <div style="font-size:12px;color:var(--ink-muted);">Users</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-md);padding:16px;text-align:center;">
                <div style="font-size:32px;font-weight:700;color:var(--gold);">0</div>
                <div style="font-size:12px;color:var(--ink-muted);">Revenue</div>
            </div>
        </div>

        <!-- Data Moat -->
        <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-lg);padding:24px;margin-bottom:24px;">
            <h2 style="font-family:var(--font-display);font-size:var(--text-lg);margin:0 0 12px;">Data Moat</h2>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:12px;">
                <div><span style="font-size:20px;font-weight:700;">{pairs:,}</span><br><span style="font-size:12px;color:var(--ink-muted);">Cooccurrence pairs</span></div>
                <div><span style="font-size:20px;font-weight:700;">{refs:,}</span><br><span style="font-size:12px;color:var(--ink-muted);">Reference tools</span></div>
                <div><span style="font-size:20px;font-weight:700;">{real_tools:,}</span><br><span style="font-size:12px;color:var(--ink-muted);">Curated tools</span></div>
            </div>
        </div>

        <!-- Daily Breakdown -->
        <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;margin-bottom:24px;">
            <div style="padding:16px 24px;border-bottom:1px solid var(--border);">
                <h2 style="font-family:var(--font-display);font-size:var(--text-lg);margin:0;">Daily Breakdown</h2>
            </div>
            <table style="width:100%;border-collapse:collapse;font-size:var(--text-sm);">
                <thead><tr style="background:var(--cream-dark);">
                    <th style="padding:8px 16px;text-align:left;">Day</th>
                    <th style="padding:8px 16px;text-align:left;">Total</th>
                    <th style="padding:8px 16px;text-align:left;">Internal</th>
                    <th style="padding:8px 16px;text-align:left;">External</th>
                </tr></thead>
                <tbody>{daily_rows}</tbody>
            </table>
        </div>

        <!-- External Sessions -->
        <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-lg);overflow:hidden;margin-bottom:24px;">
            <div style="padding:16px 24px;border-bottom:1px solid var(--border);">
                <h2 style="font-family:var(--font-display);font-size:var(--text-lg);margin:0;">External Sessions</h2>
            </div>
            <table style="width:100%;border-collapse:collapse;font-size:var(--text-sm);">
                <thead><tr style="background:var(--cream-dark);">
                    <th style="padding:8px 16px;text-align:left;">Session</th>
                    <th style="padding:8px 16px;text-align:left;">Analyses</th>
                </tr></thead>
                <tbody>{session_rows if session_rows else '<tr><td colspan="2" style="padding:16px;color:var(--ink-muted);text-align:center;">No external sessions yet</td></tr>'}</tbody>
            </table>
        </div>
    </div>'''

    return HTMLResponse(page_shell("Pivot Metrics | IndieStack", body, user=user))


# ── Technographic API ────────────────────────────────────────────────────

@router.get("/api/technographics/{tool_slug}")
async def technographic_data(request: Request, tool_slug: str):
    """What tools are used alongside a given tool? Sell this to tool makers."""
    d = request.state.db

    # Auth: require API key for technographic data (this is the paid product)
    api_key = request.query_params.get("key", "")
    if not api_key:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            api_key = auth_header[7:]

    if not api_key:
        return JSONResponse({
            "error": "API key required for technographic data",
            "get_key": "https://indiestack.ai/developer",
            "pricing": "Contact pajebay1@gmail.com for technographic API access",
        }, status_code=401)

    # Verify API key exists
    c = await d.execute("SELECT id, user_id FROM api_keys WHERE key_hash = ?",
                        (api_key,))
    key_row = await c.fetchone()
    if not key_row:
        # Try unhashed (legacy)
        c = await d.execute("SELECT id, user_id FROM api_keys WHERE key_hash = ? OR key_hash = ?",
                            (api_key, api_key))
        key_row = await c.fetchone()
    if not key_row:
        return JSONResponse({"error": "Invalid API key"}, status_code=401)

    # Look up the tool
    c = await d.execute(
        "SELECT id, name, slug, category_id FROM tools WHERE slug = ? AND status = 'approved' LIMIT 1",
        (tool_slug,),
    )
    tool = await c.fetchone()
    if not tool:
        return JSONResponse({"error": f"Tool '{tool_slug}' not found"}, status_code=404)

    tool_name = tool["name"]

    # Get cooccurrence data — what's used alongside this tool
    c = await d.execute("""
        SELECT
            CASE WHEN tool_a_slug = ? THEN tool_b_slug ELSE tool_a_slug END as companion_slug,
            cooccurrence_count
        FROM manifest_cooccurrences
        WHERE (tool_a_slug = ? OR tool_b_slug = ?)
          AND cooccurrence_count >= 2
        ORDER BY cooccurrence_count DESC
        LIMIT 50
    """, (tool_slug, tool_slug, tool_slug))
    raw_companions = await c.fetchall()

    # Enrich with tool names and categories
    companions = []
    for r in raw_companions:
        slug = r["companion_slug"]
        count = r["cooccurrence_count"]
        c2 = await d.execute(
            """SELECT name, category_id, github_stars, health_status, is_reference
               FROM tools WHERE slug = ? LIMIT 1""",
            (slug,),
        )
        info = await c2.fetchone()
        if not info:
            continue

        # Get category name
        cat_name = ""
        if info.get("category_id"):
            c3 = await d.execute("SELECT name FROM categories WHERE id = ?", (info["category_id"],))
            cat_row = await c3.fetchone()
            cat_name = cat_row["name"] if cat_row else ""

        companions.append({
            "slug": slug,
            "name": info["name"],
            "category": cat_name,
            "cooccurrence_count": count,
            "github_stars": info.get("github_stars") or 0,
            "health": info.get("health_status", "unknown"),
            "is_mainstream": bool(info.get("is_reference", 0)),
        })

    # Also check curated compatibility pairs
    c = await d.execute("""
        SELECT
            CASE WHEN tool_a_slug = ? THEN tool_b_slug ELSE tool_a_slug END as pair_slug,
            success_count
        FROM tool_pairs
        WHERE (tool_a_slug = ? OR tool_b_slug = ?)
          AND success_count > 0
        ORDER BY success_count DESC
    """, (tool_slug, tool_slug, tool_slug))
    verified_pairs = []
    for r in await c.fetchall():
        verified_pairs.append({
            "slug": r["pair_slug"],
            "verified_success_count": r["success_count"],
        })

    # Compute market share within category
    category_id = tool.get("category_id")
    category_stats = None
    if category_id:
        c = await d.execute(
            "SELECT COUNT(*) as cnt FROM tools WHERE category_id = ? AND status = 'approved' AND is_reference = 0",
            (category_id,),
        )
        total_in_cat = (await c.fetchone())["cnt"]
        # How many manifests include this tool vs competitors
        c = await d.execute("""
            SELECT SUM(cooccurrence_count) as total
            FROM manifest_cooccurrences
            WHERE tool_a_slug = ? OR tool_b_slug = ?
        """, (tool_slug, tool_slug))
        row = await c.fetchone()
        tool_appearances = row["total"] if row and row["total"] else 0

        c2 = await d.execute("SELECT name FROM categories WHERE id = ?", (category_id,))
        cat_row = await c2.fetchone()

        category_stats = {
            "category": cat_row["name"] if cat_row else "",
            "total_tools_in_category": total_in_cat,
            "manifest_appearances": tool_appearances,
        }

    return JSONResponse({
        "tool": {
            "slug": tool_slug,
            "name": tool_name,
        },
        "companions": companions,
        "verified_compatible": verified_pairs,
        "category_stats": category_stats,
        "data_sources": {
            "manifest_analyses": "Real package.json and requirements.txt files analyzed",
            "cooccurrence_pairs": "Tools that appear together in the same manifest",
            "verified_pairs": "Curated compatibility data from GitHub repo analysis",
        },
    })


# ── Audit Report API ─────────────────────────────────────────────────────

@router.get("/api/audit/{owner}/{repo}")
async def repo_audit(request: Request, owner: str, repo: str):
    """Full dependency health audit for a repo. The consulting product."""
    d = request.state.db

    # Fetch manifest from GitHub
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        manifest = None
        manifest_type = "package.json"
        for fname, mtype in [("package.json", "package.json"), ("requirements.txt", "requirements.txt")]:
            for branch in ["main", "master"]:
                resp = await client.get(f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{fname}")
                if resp.status_code == 200 and len(resp.text) > 10:
                    manifest = resp.text
                    manifest_type = mtype
                    break
            if manifest:
                break

    if not manifest:
        return JSONResponse({"error": "No package.json or requirements.txt found"}, status_code=404)

    # Run analysis
    try:
        result = await run_analysis(d, manifest, manifest_type)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)

    # Save with repo tracking
    share_uuid = await save_analysis(d, None, f"audit:{owner}/{repo}", manifest_type, result)

    # Enrich with audit-specific data
    score = result["score"]
    matched = result.get("matched", [])

    # Risk assessment
    risks = []
    for m in matched:
        f = m.get("freshness", {})
        if f.get("status") in ("dead", "dormant"):
            risks.append({
                "package": m["package"],
                "tool": m["tool"]["name"],
                "severity": "high" if f["status"] == "dead" else "medium",
                "issue": f"Package is {f['status']} — last activity unknown or over 12 months ago",
                "recommendation": "Replace with an actively maintained alternative",
            })

    # Migration suggestions
    migrations = []
    for md in result.get("modernity_details", []):
        migrations.append({
            "from": md["name"],
            "to": [a["name"] for a in md.get("alternatives", [])],
            "reason": "More actively maintained alternatives with higher community traction",
        })

    audit = {
        "repo": f"{owner}/{repo}",
        "generated_at": "2026-03-26",
        "share_url": f"https://indiestack.ai/analyze/{share_uuid}",
        "summary": {
            "score": score["total"],
            "grade": "Excellent" if score["total"] >= 90 else ("Good" if score["total"] >= 80 else ("Needs attention" if score["total"] >= 60 else "At risk")),
            "freshness": score["freshness"],
            "cohesion": score["cohesion"],
            "modernity": score["modernity"],
            "total_dependencies": result["packages_total"],
            "matched_dependencies": result["packages_matched"],
        },
        "dependencies": [
            {
                "package": m["package"],
                "tool": m["tool"]["name"],
                "status": m.get("freshness", {}).get("status", "unknown"),
                "freshness_score": m.get("freshness", {}).get("freshness", 50),
            }
            for m in matched
        ],
        "risks": risks,
        "recommended_migrations": migrations,
        "compatibility": result.get("cohesion_details", []),
    }

    return JSONResponse(audit)


# ── CI Outcome Reporting ─────────────────────────────────────────────────

@router.post("/api/outcomes", response_class=JSONResponse)
async def report_outcome(request: Request):
    """Receive CI build outcome from GitHub Action.

    Every install of our GitHub Action becomes a Waze-like outcome sensor.
    No auth required — this is public data collection for the moat.
    """
    d = request.state.db
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    repo = body.get("repo", "").strip()
    manifest_hash = body.get("manifest_hash", "").strip()
    packages_json = body.get("packages_json", "")
    ci_passed = body.get("ci_passed")
    action_version = body.get("action_version", "")

    if not repo or ci_passed is None:
        return JSONResponse({"error": "repo and ci_passed are required"}, status_code=400)

    # Normalize packages_json to string
    if isinstance(packages_json, (dict, list)):
        packages_json = json.dumps(packages_json)

    await d.execute(
        """INSERT INTO build_outcomes (repo, manifest_hash, packages_json, ci_passed, action_version)
           VALUES (?, ?, ?, ?, ?)""",
        (repo, manifest_hash, packages_json, 1 if ci_passed else 0, action_version)
    )
    await d.commit()

    return JSONResponse({"status": "recorded", "repo": repo, "ci_passed": bool(ci_passed)})


@router.get("/api/tool-trust", response_class=JSONResponse)
async def tool_trust(request: Request):
    """Public tool trust leaderboard — citation counts + agent outcome data.

    Returns the tools most cited and successfully used by AI agents.
    Agents can query this to find proven tools before recommending.

    Query params:
        tool: filter to a specific tool slug (e.g. ?tool=stripe)
        limit: number of results (default 20, max 100)
        min_citations: minimum citation count (default 1)
    """
    d = request.state.db
    tool_slug = request.query_params.get("tool", "").strip().lower()
    try:
        limit = min(int(request.query_params.get("limit", "20")), 100)
        min_citations = int(request.query_params.get("min_citations", "1"))
    except ValueError:
        limit, min_citations = 20, 1

    if tool_slug:
        # Single tool lookup
        c = await d.execute(
            """SELECT t.slug, t.name, t.description,
                      COUNT(DISTINCT ac.id) as citation_count,
                      SUM(CASE WHEN aa.success = 1 THEN 1 ELSE 0 END) as success_count,
                      COUNT(DISTINCT aa.id) as outcome_count
               FROM tools t
               LEFT JOIN agent_citations ac ON ac.tool_id = t.id
               LEFT JOIN agent_actions aa ON aa.tool_slug = t.slug
               WHERE t.slug = ? AND t.status = 'approved'
               GROUP BY t.id""",
            (tool_slug,)
        )
        row = await c.fetchone()
        if not row:
            return JSONResponse({"error": "Tool not found"}, status_code=404)
        result = dict(row)
        result["success_rate"] = (
            round(result["success_count"] / result["outcome_count"] * 100)
            if result["outcome_count"] else None
        )
        return JSONResponse({"tool": result})

    # Leaderboard mode
    c = await d.execute(
        """SELECT t.slug, t.name,
                  COUNT(DISTINCT ac.id) as citation_count,
                  SUM(CASE WHEN aa.success = 1 THEN 1 ELSE 0 END) as success_count,
                  COUNT(DISTINCT aa.id) as outcome_count
           FROM tools t
           JOIN agent_citations ac ON ac.tool_id = t.id
           LEFT JOIN agent_actions aa ON aa.tool_slug = t.slug
           WHERE t.status = 'approved'
           GROUP BY t.id
           HAVING citation_count >= ?
           ORDER BY citation_count DESC
           LIMIT ?""",
        (min_citations, limit)
    )
    rows = await c.fetchall()
    results = []
    for r in rows:
        entry = dict(r)
        entry["success_rate"] = (
            round(entry["success_count"] / entry["outcome_count"] * 100)
            if entry["outcome_count"] else None
        )
        results.append(entry)

    return JSONResponse({
        "tools": results,
        "total": len(results),
        "note": "citation_count = times cited by AI agents. success_rate = % of report_outcome() calls that were successful (null if no reports yet)."
    }, headers={"Cache-Control": "public, max-age=300"})


@router.get("/api/migrations", response_class=JSONResponse)
async def get_migrations(request: Request):
    """Query migration paths for a package. The moat data endpoint."""
    d = request.state.db
    package = request.query_params.get("package", "").strip()
    if not package:
        return JSONResponse({"error": "package parameter required"}, status_code=400)

    # Migrations FROM this package (people leaving it)
    cursor = await d.execute(
        """SELECT to_package, COUNT(*) as count, confidence,
                  GROUP_CONCAT(DISTINCT repo) as repos
           FROM migration_paths WHERE from_package = ?
           GROUP BY to_package, confidence
           ORDER BY count DESC LIMIT 20""",
        (package,)
    )
    from_rows = await cursor.fetchall()

    # Migrations TO this package (people adopting it)
    cursor = await d.execute(
        """SELECT from_package, COUNT(*) as count, confidence,
                  GROUP_CONCAT(DISTINCT repo) as repos
           FROM migration_paths WHERE to_package = ?
           GROUP BY from_package, confidence
           ORDER BY count DESC LIMIT 20""",
        (package,)
    )
    to_rows = await cursor.fetchall()

    return JSONResponse({
        "package": package,
        "migrating_from": [
            {"to": r["to_package"], "count": r["count"], "confidence": r["confidence"],
             "sample_repos": r["repos"].split(",")[:5] if r["repos"] else []}
            for r in from_rows
        ],
        "migrating_to": [
            {"from": r["from_package"], "count": r["count"], "confidence": r["confidence"],
             "sample_repos": r["repos"].split(",")[:5] if r["repos"] else []}
            for r in to_rows
        ],
    })


@router.get("/api/combos", response_class=JSONResponse)
async def get_combos(request: Request):
    """Query verified package combinations. What actually works together in production."""
    d = request.state.db
    package = request.query_params.get("package", "").strip()
    if not package:
        return JSONResponse({"error": "package parameter required"}, status_code=400)

    cursor = await d.execute(
        """SELECT
               CASE WHEN package_a = ? THEN package_b ELSE package_a END as partner,
               COUNT(*) as repo_count,
               SUM(repo_stars) as total_stars,
               GROUP_CONCAT(DISTINCT repo) as repos
           FROM verified_combos
           WHERE package_a = ? OR package_b = ?
           GROUP BY partner
           ORDER BY repo_count DESC, total_stars DESC
           LIMIT 30""",
        (package, package, package)
    )
    rows = await cursor.fetchall()

    return JSONResponse({
        "package": package,
        "verified_with": [
            {
                "package": r["partner"],
                "repo_count": r["repo_count"],
                "total_stars": r["total_stars"] or 0,
                "sample_repos": r["repos"].split(",")[:5] if r["repos"] else [],
            }
            for r in rows
        ],
    })


@router.get("/api/moat/stats", response_class=JSONResponse)
async def moat_stats(request: Request):
    """Aggregate stats on the data moat — how much unique data we've collected."""
    d = request.state.db

    migrations = await (await d.execute("SELECT COUNT(*) as n FROM migration_paths")).fetchone()
    combos = await (await d.execute("SELECT COUNT(*) as n FROM verified_combos")).fetchone()
    outcomes = await (await d.execute("SELECT COUNT(*) as n FROM build_outcomes")).fetchone()
    unique_migrations = await (await d.execute(
        "SELECT COUNT(DISTINCT from_package || '→' || to_package) as n FROM migration_paths"
    )).fetchone()
    repos_scanned = await (await d.execute(
        "SELECT COUNT(DISTINCT repo) as n FROM verified_combos"
    )).fetchone()

    return JSONResponse({
        "migration_paths": migrations["n"],
        "unique_migrations": unique_migrations["n"],
        "verified_combos": combos["n"],
        "build_outcomes": outcomes["n"],
        "repos_scanned": repos_scanned["n"],
    })

"""Stack Auditor — paste a manifest, get indie alternatives.

First audit is free (no login). Ongoing monitoring requires Pro.
"""

import re
from datetime import datetime, timedelta, timezone
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell

router = APIRouter()

MAX_MANIFEST_SIZE = 50_000  # bytes
MAX_DEPS = 100  # cap dependencies to prevent N+1 explosion


def _escape_like(s: str) -> str:
    """Escape LIKE metacharacters to prevent wildcard injection."""
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# ---------------------------------------------------------------------------
# Dependency → category mapping for smarter matching
# ---------------------------------------------------------------------------
DEPENDENCY_MAPPINGS: dict[str, str] = {
    # Auth
    "auth0": "authentication", "passport": "authentication", "next-auth": "authentication",
    "clerk": "authentication", "supabase": "authentication", "firebase": "authentication",
    "lucia": "authentication", "better-auth": "authentication", "kinde": "authentication",
    # Payments
    "stripe": "payments", "paddle": "payments", "lemon": "payments",
    "lemonsqueezy": "payments", "chargebee": "payments",
    # Analytics
    "google-analytics": "analytics", "segment": "analytics", "mixpanel": "analytics",
    "amplitude": "analytics", "hotjar": "analytics", "vercel-analytics": "analytics",
    "plausible": "analytics", "posthog": "analytics",
    # Email
    "sendgrid": "email", "mailgun": "email", "postmark": "email", "ses": "email",
    "resend": "email", "mailchimp": "email", "nodemailer": "email",
    # Monitoring
    "sentry": "monitoring", "datadog": "monitoring", "newrelic": "monitoring",
    "bugsnag": "monitoring", "logrocket": "monitoring",
    # Forms
    "typeform": "forms", "jotform": "forms",
    # Support
    "intercom": "customer support", "zendesk": "customer support", "crisp": "customer support",
    # Hosting
    "heroku": "hosting", "netlify": "hosting", "render": "hosting",
    # Cloud
    "aws-sdk": "cloud infrastructure", "googleapis": "cloud infrastructure",
    # Database
    "prisma": "database", "mongoose": "database", "sequelize": "database",
    "drizzle": "database", "knex": "database", "typeorm": "database",
    # Design
    "tailwindcss": "design", "bootstrap": "design",
    # Frameworks
    "express": "web framework", "fastify": "web framework", "koa": "web framework",
    "react": "frontend framework", "vue": "frontend framework", "svelte": "frontend framework",
    "next": "frontend framework", "nuxt": "frontend framework",
    # Testing
    "jest": "testing", "mocha": "testing", "cypress": "testing", "vitest": "testing",
    "playwright": "testing",
    # Build
    "webpack": "build tools", "vite": "build tools", "esbuild": "build tools",
    "turbo": "build tools", "rollup": "build tools",
    # CMS
    "contentful": "cms", "sanity": "cms", "strapi": "cms",
    # Search
    "algolia": "search", "meilisearch": "search", "typesense": "search",
    # Storage
    "cloudinary": "storage", "uploadthing": "storage",
}

# ---------------------------------------------------------------------------
# Sample package.json for the "Try an example" button
# ---------------------------------------------------------------------------
SAMPLE_MANIFEST = """{
  "name": "my-saas-app",
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "@auth0/nextjs-auth0": "^3.1.0",
    "stripe": "^14.0.0",
    "@sentry/nextjs": "^7.80.0",
    "@sendgrid/mail": "^7.7.0",
    "mixpanel-browser": "^2.48.1",
    "intercom-client": "^4.0.0",
    "prisma": "^5.6.0"
  }
}"""

# ---------------------------------------------------------------------------
# Manifest parsers
# ---------------------------------------------------------------------------

def _parse_package_json(text: str) -> list[str]:
    """Extract dependency names from package.json."""
    deps: list[str] = []
    # Match keys inside "dependencies", "devDependencies", "peerDependencies"
    in_block = False
    brace_depth = 0
    for line in text.splitlines():
        stripped = line.strip()
        if re.search(r'"(dependencies|devDependencies|peerDependencies)"', stripped):
            in_block = True
            brace_depth = 0
            if "{" in stripped:
                brace_depth += stripped.count("{") - stripped.count("}")
            continue
        if in_block:
            brace_depth += stripped.count("{") - stripped.count("}")
            if brace_depth <= 0:
                in_block = False
                continue
            m = re.match(r'"(@?[^"]+)"', stripped)
            if m:
                # Normalize: @scope/pkg → pkg, @sentry/nextjs → sentry
                raw = m.group(1)
                if raw.startswith("@"):
                    parts = raw.split("/")
                    # Use scope name without @ as the key (e.g. @auth0/x → auth0)
                    deps.append(parts[0][1:])
                    # Also keep the package part
                    if len(parts) > 1:
                        deps.append(parts[1])
                else:
                    deps.append(raw)
    return list(dict.fromkeys(deps))  # dedupe preserving order


def _parse_requirements_txt(text: str) -> list[str]:
    """Extract package names from requirements.txt."""
    deps: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        # Remove version specifiers
        name = re.split(r"[><=!~;\[]", line)[0].strip()
        if name:
            deps.append(name.lower().replace("_", "-"))
    return list(dict.fromkeys(deps))


def _parse_go_mod(text: str) -> list[str]:
    """Extract module names from go.mod."""
    deps: list[str] = []
    in_require = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("require ("):
            in_require = True
            continue
        if in_require and stripped == ")":
            in_require = False
            continue
        if in_require or stripped.startswith("require "):
            # e.g. github.com/stripe/stripe-go/v76 v76.0.0
            parts = stripped.replace("require ", "").strip().split()
            if parts:
                mod = parts[0]
                # Take last path segment
                segments = mod.split("/")
                name = segments[-1] if segments else mod
                # Strip version suffixes like v76
                name = re.sub(r"^v\d+$", "", name)
                if not name and len(segments) >= 2:
                    name = segments[-2]
                if name:
                    deps.append(name.lower())
    return list(dict.fromkeys(deps))


def _parse_cargo_toml(text: str) -> list[str]:
    """Extract crate names from Cargo.toml."""
    deps: list[str] = []
    in_deps = False
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"\[(.*dependencies.*)\]", stripped):
            in_deps = True
            continue
        if stripped.startswith("[") and in_deps:
            in_deps = False
            continue
        if in_deps:
            m = re.match(r"(\w[\w-]*)\s*=", stripped)
            if m:
                deps.append(m.group(1).lower())
    return list(dict.fromkeys(deps))


def parse_manifest(text: str) -> tuple[str, list[str]]:
    """Detect format and parse dependencies. Returns (format_name, dep_list)."""
    text = text.strip()
    if not text:
        return ("unknown", [])

    # package.json
    if text.startswith("{") and '"dependencies"' in text.lower():
        return ("package.json", _parse_package_json(text))

    # go.mod
    if text.startswith("module ") or "require (" in text:
        return ("go.mod", _parse_go_mod(text))

    # Cargo.toml
    if "[dependencies]" in text or "[package]" in text:
        return ("Cargo.toml", _parse_cargo_toml(text))

    # requirements.txt (fallback — line-per-dep)
    lines = [l.strip() for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]
    if lines:
        return ("requirements.txt", _parse_requirements_txt(text))

    return ("unknown", [])


# ---------------------------------------------------------------------------
# Health indicator helpers
# ---------------------------------------------------------------------------

def _health_icon(health_status: str | None, last_commit: str | None) -> str:
    """Return a colored health indicator."""
    if health_status == "archived" or health_status == "dead":
        return '<span style="color:#EF4444;" title="Archived / inactive">&#x2716;</span>'

    # Try to use last_commit date
    if last_commit:
        try:
            commit_dt = datetime.fromisoformat(last_commit.replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - commit_dt
            if age < timedelta(days=90):
                return '<span style="color:#22C55E;" title="Active (commit &lt; 90 days)">&#x2714;</span>'
            elif age < timedelta(days=365):
                return '<span style="color:#EAB308;" title="Stale (no commits in 90+ days)">&#x26A0;</span>'
            else:
                return '<span style="color:#EF4444;" title="Inactive (no commits in 1yr+)">&#x2716;</span>'
        except (ValueError, TypeError):
            pass

    if health_status == "active":
        return '<span style="color:#22C55E;" title="Active">&#x2714;</span>'
    if health_status == "stale":
        return '<span style="color:#EAB308;" title="Stale">&#x26A0;</span>'

    return '<span style="color:var(--ink-muted);" title="Unknown">&#x2014;</span>'


def _format_stars(stars: int | None) -> str:
    if not stars:
        return ""
    if stars >= 1000:
        return f'<span style="color:var(--ink-muted);font-size:13px;">&#9733; {stars / 1000:.1f}k</span>'
    return f'<span style="color:var(--ink-muted);font-size:13px;">&#9733; {stars}</span>'


def _format_price(price_pence: int | None) -> str:
    if price_pence is None or price_pence <= 0:
        return '<span style="color:#22C55E;font-weight:600;">Free</span>'
    pounds = price_pence / 100
    if pounds == int(pounds):
        return f'<span style="color:var(--ink);">&pound;{int(pounds)}</span>'
    return f'<span style="color:var(--ink);">&pound;{pounds:.2f}</span>'


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def _form_html(manifest_value: str = "", error: str = "") -> str:
    """Render the audit input form."""
    error_html = ""
    if error:
        error_html = f'<p style="color:#EF4444;margin-bottom:16px;font-size:14px;">{escape(error)}</p>'

    escaped_manifest = escape(manifest_value)
    # Escape for JS template literal (backticks, ${})
    escaped_sample = SAMPLE_MANIFEST.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

    return f"""
    <section style="max-width:720px;margin:0 auto;padding:48px 20px 32px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,5vw,42px);color:var(--ink);margin-bottom:12px;">
                Audit Your Stack
            </h1>
            <p style="font-size:17px;color:var(--ink-muted);max-width:480px;margin:0 auto;line-height:1.6;">
                Paste your manifest file and discover indie-built alternatives to every dependency in your project.
            </p>
        </div>

        {error_html}

        <form method="post" action="/audit" id="audit-form">
            <div style="position:relative;">
                <textarea
                    name="manifest"
                    id="manifest-input"
                    placeholder="Paste your package.json, requirements.txt, go.mod, or Cargo.toml here..."
                    style="width:100%;min-height:220px;padding:16px;font-family:var(--font-mono);font-size:13px;
                           line-height:1.6;border:2px solid var(--border);border-radius:var(--radius);
                           background:var(--card-bg,white);color:var(--ink);resize:vertical;
                           box-sizing:border-box;transition:border-color 0.15s;"
                    onfocus="this.style.borderColor='var(--accent)'"
                    onblur="this.style.borderColor='var(--border)'"
                >{escaped_manifest}</textarea>
            </div>

            <div style="display:flex;align-items:center;gap:12px;margin-top:16px;flex-wrap:wrap;">
                <button type="submit"
                        style="flex:1;min-width:200px;padding:14px 32px;background:var(--accent);color:#000;
                               font-family:var(--font-body);font-weight:700;font-size:16px;border:none;
                               border-radius:var(--radius);cursor:pointer;transition:opacity 0.15s;"
                        onmouseover="this.style.opacity='0.85'"
                        onmouseout="this.style.opacity='1'">
                    Audit My Stack
                </button>
                <button type="button"
                        onclick="document.getElementById('manifest-input').value = `{escaped_sample}`;"
                        style="padding:14px 24px;background:transparent;color:var(--ink-muted);
                               font-family:var(--font-body);font-weight:600;font-size:14px;border:2px solid var(--border);
                               border-radius:var(--radius);cursor:pointer;transition:border-color 0.15s,color 0.15s;"
                        onmouseover="this.style.borderColor='var(--accent)';this.style.color='var(--ink)'"
                        onmouseout="this.style.borderColor='var(--border)';this.style.color='var(--ink-muted)'">
                    Try an example
                </button>
            </div>

            <p style="text-align:center;margin-top:16px;font-size:13px;color:var(--ink-muted);">
                Free &mdash; no account needed
            </p>
        </form>
    </section>
    """


def _results_html(
    manifest_value: str,
    format_name: str,
    dep_count: int,
    matches: list[dict],
    total_alternatives: int,
    user: dict | None,
) -> str:
    """Render the audit report."""

    # Summary header
    html = f"""
    <section style="max-width:720px;margin:0 auto;padding:0 20px 24px;">
        <div style="background:var(--card-bg,white);border:1px solid var(--border);border-radius:var(--radius);
                    padding:24px 28px;margin-bottom:32px;">
            <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;margin-bottom:8px;">
                <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin:0;">
                    Stack Audit Report
                </h2>
                <span style="font-family:var(--font-mono);font-size:12px;color:var(--ink-muted);
                             background:var(--border);padding:4px 10px;border-radius:999px;">
                    {escape(format_name)}
                </span>
            </div>
            <p style="color:var(--ink-muted);font-size:15px;margin:0;">
                <strong style="color:var(--ink);">{dep_count}</strong> dependenc{"y" if dep_count == 1 else "ies"} analysed
                &nbsp;&middot;&nbsp;
                <strong style="color:var(--accent);">{total_alternatives}</strong> indie alternative{"" if total_alternatives == 1 else "s"} found
            </p>
        </div>
    """

    if not matches:
        html += """
        <div style="text-align:center;padding:48px 20px;">
            <p style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin-bottom:12px;">
                Your stack is already indie-friendly!
            </p>
            <p style="color:var(--ink-muted);font-size:15px;margin-bottom:24px;">
                We didn't find any dependencies with known indie alternatives &mdash; nice work.
            </p>
            <a href="/explore" style="display:inline-block;padding:12px 28px;background:var(--accent);color:#000;
                                      font-weight:700;border-radius:var(--radius);text-decoration:none;">
                Browse Indie Tools &rarr;
            </a>
        </div>
        """
    else:
        for match in matches:
            dep_name = escape(match["dep"])
            category = escape(match.get("category", ""))
            alternatives = match.get("alternatives", [])

            category_badge = ""
            if category:
                category_badge = f"""
                <span style="font-size:11px;font-weight:600;color:var(--accent);background:rgba(0,212,245,0.1);
                             padding:3px 10px;border-radius:999px;text-transform:uppercase;letter-spacing:0.5px;">
                    {category}
                </span>"""

            alt_cards = ""
            for alt in alternatives:
                name = escape(str(alt.get("name", "")))
                slug = escape(str(alt.get("slug", "")))
                tagline = escape(str(alt.get("tagline", "")))
                health = _health_icon(alt.get("health_status"), alt.get("github_last_commit"))
                stars = _format_stars(alt.get("github_stars"))
                price = _format_price(alt.get("price"))
                upvotes = int(alt.get("upvote_count", 0))

                alt_cards += f"""
                <a href="/tool/{slug}" style="display:block;text-decoration:none;padding:14px 16px;
                                              border:1px solid var(--border);border-radius:var(--radius-sm);
                                              transition:border-color 0.15s,box-shadow 0.15s;
                                              background:var(--card-bg,white);"
                   onmouseover="this.style.borderColor='var(--accent)';this.style.boxShadow='var(--shadow-sm)'"
                   onmouseout="this.style.borderColor='var(--border)';this.style.boxShadow='none'">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                        <div style="display:flex;align-items:center;gap:8px;">
                            {health}
                            <span style="font-family:var(--font-display);font-size:16px;color:var(--ink);">{name}</span>
                        </div>
                        <div style="display:flex;align-items:center;gap:12px;">
                            {stars}
                            {price}
                        </div>
                    </div>
                    <p style="margin:0;font-size:13px;color:var(--ink-muted);line-height:1.5;">{tagline}</p>
                    <div style="margin-top:6px;font-size:12px;color:var(--ink-muted);">
                        &#9650; {upvotes}
                    </div>
                </a>
                """

            html += f"""
            <div style="margin-bottom:24px;">
                <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
                    <code style="font-family:var(--font-mono);font-size:14px;color:var(--ink);
                                 background:var(--border);padding:4px 10px;border-radius:var(--radius-sm);">
                        {dep_name}
                    </code>
                    {category_badge}
                </div>
                <div style="display:flex;flex-direction:column;gap:8px;padding-left:12px;
                            border-left:2px solid var(--border);">
                    {alt_cards}
                </div>
            </div>
            """

    # Pro upsell CTA
    html += f"""
        <div style="background:#1A2D4A;border-radius:var(--radius);padding:32px 28px;margin-top:40px;
                    text-align:center;">
            <h3 style="font-family:var(--font-display);font-size:20px;color:#fff;margin-bottom:8px;">
                Want deeper intelligence?
            </h3>
            <p style="color:rgba(255,255,255,0.7);font-size:15px;line-height:1.6;margin-bottom:20px;max-width:480px;margin-left:auto;margin-right:auto;">
                IndieStack Pro includes demand signal analytics, AI citation tracking, weekly AI reports to your inbox, and 1,000 API queries per day.
            </p>
            <a href="/pricing"
               style="display:inline-block;padding:12px 32px;background:var(--accent);color:#000;
                      font-weight:700;font-size:15px;border-radius:var(--radius);text-decoration:none;
                      transition:opacity 0.15s;"
               onmouseover="this.style.opacity='0.85'"
               onmouseout="this.style.opacity='1'">
                See Pro Plans &rarr;
            </a>
        </div>
    </section>
    """

    return html


@router.get("/audit", response_class=HTMLResponse)
async def audit_page(request: Request):
    user = getattr(request.state, "user", None)
    body = _form_html()
    return HTMLResponse(page_shell(
        "Audit Your Stack | IndieStack",
        body,
        description="Paste your package.json or requirements.txt and discover indie alternatives to every dependency.",
        user=user,
        canonical="/audit",
    ))


@router.post("/audit", response_class=HTMLResponse)
async def audit_submit(request: Request):
    user = getattr(request.state, "user", None)
    db = request.state.db

    form = await request.form()
    manifest_text = str(form.get("manifest", "")).strip()

    if len(manifest_text) > MAX_MANIFEST_SIZE:
        body = _form_html(error="Manifest too large. Please paste a file under 50KB.")
        return HTMLResponse(page_shell(
            "Audit Your Stack | IndieStack",
            body,
            description="Paste your package.json or requirements.txt and discover indie alternatives to every dependency.",
            user=user,
            canonical="/audit",
        ))

    if not manifest_text:
        body = _form_html(error="Paste a manifest file to get started.")
        return HTMLResponse(page_shell(
            "Audit Your Stack | IndieStack",
            body,
            description="Paste your package.json or requirements.txt and discover indie alternatives to every dependency.",
            user=user,
            canonical="/audit",
        ))

    format_name, deps = parse_manifest(manifest_text)

    if not deps:
        body = _form_html(
            manifest_value=manifest_text,
            error="Couldn't parse any dependencies. Make sure you're pasting a valid package.json, requirements.txt, go.mod, or Cargo.toml.",
        )
        return HTMLResponse(page_shell(
            "Audit Your Stack | IndieStack",
            body,
            description="Paste your package.json or requirements.txt and discover indie alternatives to every dependency.",
            user=user,
            canonical="/audit",
        ))

    # Search for indie alternatives
    deps = deps[:MAX_DEPS]
    matches: list[dict] = []
    seen_tool_ids: set[int] = set()
    total_alternatives = 0

    for dep in deps:
        dep_lower = dep.lower()
        alternatives: list[dict] = []

        # 1) Direct name / slug / tagline search
        cursor = await db.execute(
            "SELECT id, name, slug, tagline, price_pence, source_type, health_status, "
            "github_last_commit, github_stars, upvote_count "
            "FROM tools WHERE status='approved' AND (LOWER(name) LIKE ? ESCAPE '\\' OR tagline LIKE ? ESCAPE '\\' OR slug LIKE ? ESCAPE '\\') LIMIT 3",
            (f"%{_escape_like(dep_lower)}%", f"%{_escape_like(dep_lower)}%", f"%{_escape_like(dep_lower)}%"),
        )
        rows = await cursor.fetchall()
        for row in rows:
            if row[0] not in seen_tool_ids:
                seen_tool_ids.add(row[0])
                alternatives.append({
                    "id": row[0], "name": row[1], "slug": row[2], "tagline": row[3],
                    "price": row[4], "source_type": row[5], "health_status": row[6],
                    "github_last_commit": row[7], "github_stars": row[8], "upvote_count": row[9],
                })

        # 2) Category search via mapping
        category = DEPENDENCY_MAPPINGS.get(dep_lower, "")
        if not category:
            # Try partial matching (e.g. "stripe" matches "stripe" key)
            for key, cat in DEPENDENCY_MAPPINGS.items():
                if key in dep_lower or dep_lower in key:
                    category = cat
                    break

        if category:
            cursor = await db.execute(
                "SELECT t.id, t.name, t.slug, t.tagline, t.price_pence, t.source_type, "
                "t.health_status, t.github_last_commit, t.github_stars, t.upvote_count "
                "FROM tools t JOIN categories c ON t.category_id = c.id "
                "WHERE t.status='approved' AND LOWER(c.name) LIKE ? "
                "ORDER BY t.upvote_count DESC LIMIT 5",
                (f"%{category}%",),
            )
            rows = await cursor.fetchall()
            for row in rows:
                if row[0] not in seen_tool_ids and len(alternatives) < 5:
                    seen_tool_ids.add(row[0])
                    alternatives.append({
                        "id": row[0], "name": row[1], "slug": row[2], "tagline": row[3],
                        "price": row[4], "source_type": row[5], "health_status": row[6],
                        "github_last_commit": row[7], "github_stars": row[8], "upvote_count": row[9],
                    })

        if alternatives:
            total_alternatives += len(alternatives)
            matches.append({
                "dep": dep,
                "category": category,
                "alternatives": alternatives,
            })

    # Build the page: form (pre-filled) + results
    body = _form_html(manifest_value=manifest_text)
    body += _results_html(
        manifest_value=manifest_text,
        format_name=format_name,
        dep_count=len(deps),
        matches=matches,
        total_alternatives=total_alternatives,
        user=user,
    )

    return HTMLResponse(page_shell(
        f"Stack Audit Report — {total_alternatives} Alternatives | IndieStack",
        body,
        description=f"Stack audit: {len(deps)} dependencies analysed, {total_alternatives} indie alternatives found.",
        user=user,
        canonical="/audit",
    ))

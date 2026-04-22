"""GEO Lead Magnet — generate llms.txt + Agent Card from any URL."""

import json
import logging
import re
from html import escape

import aiosqlite
import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from indiestack.auth import get_current_user
from indiestack.config import BASE_URL
from indiestack.db import DB_PATH, slugify, create_tool, get_all_categories
from indiestack.routes.components import page_shell

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────────────


def _extract_metadata(url: str, page_html: str) -> dict:
    """Extract structured metadata from raw HTML using stdlib only."""
    meta: dict = {
        "url": url,
        "name": "",
        "tagline": "",
        "description": "",
        "features": [],
        "github_url": None,
    }

    # Title tag
    m = re.search(r"<title[^>]*>(.*?)</title>", page_html, re.IGNORECASE | re.DOTALL)
    if m:
        raw_title = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        raw_title = re.sub(r"&[^;]+;", " ", raw_title).strip()
        for sep in [" | ", " — ", " – ", " - "]:
            if sep in raw_title:
                parts = raw_title.split(sep, 1)
                meta["name"] = parts[0].strip()
                meta["tagline"] = parts[1].strip()
                break
        if not meta["name"]:
            meta["name"] = raw_title

    # Meta description
    for pattern in [
        r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']',
        r'<meta\s+content=["\'](.*?)["\']\s+name=["\']description["\']',
        r'<meta\s+property=["\']og:description["\']\s+content=["\'](.*?)["\']',
        r'<meta\s+content=["\'](.*?)["\']\s+property=["\']og:description["\']',
    ]:
        m = re.search(pattern, page_html, re.IGNORECASE | re.DOTALL)
        if m:
            meta["description"] = re.sub(r"<[^>]+>", "", m.group(1)).strip()
            break

    # OG title as name fallback
    if not meta["name"]:
        m = re.search(
            r'<meta\s+property=["\']og:title["\']\s+content=["\'](.*?)["\']',
            page_html, re.IGNORECASE,
        )
        if m:
            meta["name"] = m.group(1).strip()

    # H1 as name fallback
    if not meta["name"]:
        m = re.search(r"<h1[^>]*>(.*?)</h1>", page_html, re.IGNORECASE | re.DOTALL)
        if m:
            meta["name"] = re.sub(r"<[^>]+>", "", m.group(1)).strip()

    # H2/H3 headings as features (up to 8)
    headings = re.findall(r"<h[23][^>]*>(.*?)</h[23]>", page_html, re.IGNORECASE | re.DOTALL)
    features = []
    for h in headings:
        cleaned = re.sub(r"<[^>]+>", "", h).strip()
        cleaned = re.sub(r"&[^;]+;", " ", cleaned).strip()
        if cleaned and len(cleaned) < 120 and cleaned not in features:
            features.append(cleaned)
            if len(features) >= 8:
                break
    meta["features"] = features

    # GitHub URL
    m = re.search(r'href=["\'](https://github\.com/[^"\'#\s]+)["\']', page_html, re.IGNORECASE)
    if m:
        meta["github_url"] = m.group(1)

    return meta


def _generate_llms_txt(meta: dict) -> str:
    """Generate markdown-formatted llms.txt content."""
    lines = [f"# {meta.get('name', 'Unknown Tool')}"]
    if meta.get("tagline"):
        lines.append(f"> {meta['tagline']}")
    lines.append("")
    lines.append("## About")
    lines.append(meta.get("description", ""))
    lines.append(f"- Website: {meta.get('url', '')}")
    if meta.get("github_url"):
        lines.append(f"- Source: {meta['github_url']}")
    if meta.get("features"):
        lines.append("")
        lines.append("## Features")
        for feat in meta["features"]:
            lines.append(f"- {feat}")
    lines.append("")
    lines.append("## Discovery")
    lines.append("- IndieStack: https://indiestack.ai")
    return "\n".join(lines)


def _generate_agent_card(meta: dict) -> dict:
    """Generate an A2A-style Agent Card dict."""
    return {
        "name": meta.get("name", ""),
        "description": meta.get("description", meta.get("tagline", "")),
        "url": meta.get("url", ""),
        "version": "1.0.0",
        "provider": {
            "organization": meta.get("name", ""),
            "url": meta.get("url", ""),
        },
        "capabilities": {
            "features": meta.get("features", []),
        },
        "health": {
            "status": "unknown",
        },
        "trust": {
            "source": meta.get("github_url") or meta.get("url", ""),
        },
        "meta": {
            "generated_by": "IndieStack GEO",
            "generated_from": meta.get("url", ""),
            "catalog": "https://indiestack.ai",
        },
    }


# ── GET /geo — Landing page ─────────────────────────────────────────────


@router.get("/geo")
async def geo_landing(request: Request):
    content = f"""
    <style>
        .geo-hero {{
            text-align: center;
            padding: 64px 24px 48px;
            max-width: 780px;
            margin: 0 auto;
        }}
        .geo-hero h1 {{
            font-family: var(--font-display);
            font-size: var(--heading-xl);
            color: var(--ink);
            margin-bottom: 16px;
            line-height: 1.15;
        }}
        .geo-hero .subtitle {{
            font-size: var(--text-lg);
            color: var(--ink-muted);
            max-width: 560px;
            margin: 0 auto 40px;
            line-height: 1.6;
        }}
        .geo-cards {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 24px;
            max-width: 720px;
            margin: 0 auto 48px;
        }}
        @media (max-width: 600px) {{
            .geo-cards {{ grid-template-columns: 1fr; }}
            .geo-hero h1 {{ font-size: var(--heading-lg); }}
        }}
        .geo-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 28px 24px;
            text-align: left;
        }}
        .geo-card h3 {{
            font-family: var(--font-display);
            font-size: var(--heading-sm);
            color: var(--ink);
            margin-bottom: 8px;
        }}
        .geo-card p {{
            color: var(--ink-muted);
            font-size: var(--text-base);
            line-height: 1.6;
        }}
        .geo-card .file-badge {{
            display: inline-block;
            background: var(--terracotta);
            color: white;
            font-family: var(--font-mono);
            font-size: var(--text-xs);
            padding: 3px 10px;
            border-radius: 999px;
            margin-bottom: 12px;
        }}
        .geo-form-section {{
            max-width: 600px;
            margin: 0 auto 56px;
            padding: 0 24px;
        }}
        .geo-input-group {{
            display: flex;
            gap: 12px;
        }}
        @media (max-width: 600px) {{
            .geo-input-group {{ flex-direction: column; }}
        }}
        .geo-input-group input {{
            flex: 1;
            padding: 14px 18px;
            font-size: var(--text-base);
            font-family: var(--font-body);
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--card-bg);
            color: var(--ink);
            outline: none;
            transition: border-color 0.2s;
        }}
        .geo-input-group input:focus {{
            border-color: var(--slate);
        }}
        .geo-input-group button {{
            padding: 14px 28px;
            font-size: var(--text-base);
            font-weight: 600;
            font-family: var(--font-body);
            background: var(--terracotta);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            white-space: nowrap;
            transition: opacity 0.2s;
        }}
        .geo-input-group button:hover {{
            opacity: 0.9;
        }}
        .geo-input-group button:disabled {{
            opacity: 0.5;
            cursor: not-allowed;
        }}
        .geo-error {{
            color: var(--error-text);
            font-size: var(--text-sm);
            margin-top: 10px;
            display: none;
        }}

        /* Results area */
        .geo-results {{
            display: none;
            max-width: 720px;
            margin: 0 auto 56px;
            padding: 0 24px;
        }}
        .geo-results.visible {{
            display: block;
        }}
        .geo-tabs {{
            display: flex;
            gap: 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 20px;
        }}
        .geo-tab {{
            padding: 10px 20px;
            font-size: var(--text-sm);
            font-weight: 600;
            font-family: var(--font-body);
            color: var(--ink-muted);
            background: none;
            border: none;
            border-bottom: 2px solid transparent;
            cursor: pointer;
            transition: color 0.2s, border-color 0.2s;
        }}
        .geo-tab.active {{
            color: var(--slate);
            border-bottom-color: var(--slate);
        }}
        .geo-output {{
            background: var(--terracotta-dark);
            color: var(--border);
            font-family: var(--font-mono);
            font-size: var(--text-sm);
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-word;
            line-height: 1.6;
            max-height: 420px;
            overflow-y: auto;
        }}
        .geo-output-panel {{
            display: none;
        }}
        .geo-output-panel.active {{
            display: block;
        }}
        .geo-cta-box {{
            text-align: center;
            margin-top: 28px;
            padding: 24px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
        }}
        .geo-cta-box p {{
            color: var(--ink-muted);
            font-size: var(--text-sm);
            margin-bottom: 14px;
        }}
        .geo-cta-box a {{
            display: inline-block;
            padding: 12px 28px;
            background: var(--terracotta);
            color: white;
            font-weight: 600;
            font-size: var(--text-base);
            border-radius: 8px;
            text-decoration: none;
            transition: opacity 0.2s;
        }}
        .geo-cta-box a:hover {{
            opacity: 0.9;
        }}

        /* Why section */
        .geo-why {{
            max-width: 720px;
            margin: 0 auto 64px;
            padding: 0 24px;
        }}
        .geo-why h2 {{
            font-family: var(--font-display);
            font-size: var(--heading-md);
            color: var(--ink);
            margin-bottom: 28px;
            text-align: center;
        }}
        .geo-why-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
        }}
        @media (max-width: 768px) {{
            .geo-why-grid {{ grid-template-columns: 1fr; }}
        }}
        .geo-why-item {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
        }}
        .geo-why-item h4 {{
            font-family: var(--font-display);
            font-size: var(--text-lg);
            color: var(--ink);
            margin-bottom: 8px;
        }}
        .geo-why-item p {{
            color: var(--ink-muted);
            font-size: var(--text-sm);
            line-height: 1.6;
        }}
    </style>

    <!-- Hero -->
    <div class="geo-hero">
        <h1>Make Your Tool AI-Discoverable</h1>
        <p class="subtitle">
            AI agents are replacing search engines. If your tool doesn't have an
            <code style="font-family:var(--font-mono);background:var(--cream-dark);padding:2px 6px;border-radius:4px;">llms.txt</code>
            and Agent Card, AI can't find you. Generate both in seconds.
        </p>
    </div>

    <!-- What you get -->
    <div class="geo-cards">
        <div class="geo-card">
            <span class="file-badge">llms.txt</span>
            <h3>LLM Discovery File</h3>
            <p>A structured markdown file that tells AI models what your tool does,
            its features, and how to recommend it. The new robots.txt for the AI era.</p>
        </div>
        <div class="geo-card">
            <span class="file-badge">agent-card.json</span>
            <h3>Agent Card</h3>
            <p>A machine-readable JSON profile following the A2A protocol. Lets AI
            agents understand your tool's capabilities and trust signals.</p>
        </div>
    </div>

    <!-- URL Form -->
    <div class="geo-form-section">
        <div class="geo-input-group">
            <input type="url" id="geo-url" placeholder="https://your-tool.com"
                   aria-label="Your tool URL" />
            <button id="geo-btn" onclick="geoGenerate()">Generate</button>
        </div>
        <p class="geo-error" id="geo-error"></p>
    </div>

    <!-- Results -->
    <div class="geo-results" id="geo-results">
        <div class="geo-tabs">
            <button class="geo-tab active" onclick="geoTab('llms')" id="tab-llms">llms.txt</button>
            <button class="geo-tab" onclick="geoTab('agent')" id="tab-agent">Agent Card</button>
        </div>
        <div class="geo-output-panel active" id="panel-llms">
            <pre class="geo-output" id="output-llms"></pre>
        </div>
        <div class="geo-output-panel" id="panel-agent">
            <pre class="geo-output" id="output-agent"></pre>
        </div>
        <div class="geo-cta-box">
            <p>Sign in with GitHub to claim this tool and add it to the IndieStack catalog.</p>
            <a href="/auth/github?next=/geo/claim" id="geo-claim-link">Sign in with GitHub</a>
        </div>
    </div>

    <!-- Why this matters -->
    <div class="geo-why">
        <h2>Why This Matters</h2>
        <div class="geo-why-grid">
            <div class="geo-why-item">
                <h4>AI-First Discovery</h4>
                <p>Developers increasingly ask AI assistants to find tools for them.
                Without structured metadata, your tool is invisible to these agents.</p>
            </div>
            <div class="geo-why-item">
                <h4>Zero-Effort Listing</h4>
                <p>Claiming your generated files automatically adds your tool to the
                IndieStack catalog — discoverable by Claude, Cursor, and Windsurf.</p>
            </div>
            <div class="geo-why-item">
                <h4>Open Standards</h4>
                <p>llms.txt and Agent Cards are emerging open formats. Getting yours
                set up now means you're ahead of every competitor who hasn't.</p>
            </div>
        </div>
    </div>

    <script>
    async function geoGenerate() {{
        const urlInput = document.getElementById('geo-url');
        const btn = document.getElementById('geo-btn');
        const errEl = document.getElementById('geo-error');
        const results = document.getElementById('geo-results');
        const url = urlInput.value.trim();

        errEl.style.display = 'none';
        if (!url || (!url.startsWith('http://') && !url.startsWith('https://'))) {{
            errEl.textContent = 'Please enter a valid URL starting with http:// or https://';
            errEl.style.display = 'block';
            return;
        }}

        btn.disabled = true;
        btn.textContent = 'Analysing...';

        try {{
            const resp = await fetch('/geo/generate', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{url: url}})
            }});
            const data = await resp.json();
            if (!resp.ok) {{
                throw new Error(data.detail || 'Generation failed');
            }}

            document.getElementById('output-llms').textContent = data.llms_txt;
            document.getElementById('output-agent').textContent = JSON.stringify(data.agent_card, null, 2);

            // Store meta in sessionStorage for claim flow
            sessionStorage.setItem('geo_meta', JSON.stringify(data.meta));

            results.classList.add('visible');
            geoTab('llms');
            results.scrollIntoView({{behavior: 'smooth', block: 'start'}});
        }} catch (e) {{
            errEl.textContent = e.message || 'Something went wrong. Try again.';
            errEl.style.display = 'block';
        }} finally {{
            btn.disabled = false;
            btn.textContent = 'Generate';
        }}
    }}

    function geoTab(which) {{
        document.querySelectorAll('.geo-tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.geo-output-panel').forEach(p => p.classList.remove('active'));
        document.getElementById('tab-' + which).classList.add('active');
        document.getElementById('panel-' + which).classList.add('active');
    }}
    </script>
    """
    return HTMLResponse(page_shell("GEO — Make Your Tool AI-Discoverable", content))


# ── POST /geo/generate ──────────────────────────────────────────────────


@router.post("/geo/generate")
async def geo_generate(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"detail": "Invalid JSON body"}, status_code=400)

    url = (body.get("url") or "").strip()
    if not url or not url.startswith("http"):
        return JSONResponse({"detail": "URL must start with http:// or https://"}, status_code=400)

    # SSRF protection: block private/reserved IPs and internal hostnames
    from urllib.parse import urlparse
    import socket
    import ipaddress
    try:
        hostname = urlparse(url).hostname or ""
        if not hostname:
            return JSONResponse({"detail": "Invalid URL"}, status_code=400)
        # Block obvious internal hostnames
        if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "[::]", "[::1]"):
            return JSONResponse({"detail": "Internal URLs are not allowed"}, status_code=400)
        # Resolve and check IP
        resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for _, _, _, _, addr in resolved:
            ip = ipaddress.ip_address(addr[0])
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return JSONResponse({"detail": "Internal URLs are not allowed"}, status_code=400)
    except (socket.gaierror, ValueError):
        return JSONResponse({"detail": "Could not resolve hostname"}, status_code=400)

    try:
        async with httpx.AsyncClient(
            timeout=15, follow_redirects=True,
            headers={"User-Agent": "IndieStack GEO Bot/1.0 (+https://indiestack.ai/geo)"},
        ) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            page_html = resp.text
    except httpx.TimeoutException:
        return JSONResponse({"detail": "Timed out fetching the URL. Is the site reachable?"}, status_code=422)
    except httpx.HTTPStatusError as exc:
        return JSONResponse({"detail": f"Site returned HTTP {exc.response.status_code}"}, status_code=422)
    except Exception as exc:
        logger.warning("GEO fetch error for %s: %s", url, exc)
        return JSONResponse({"detail": "Could not fetch the URL. Check it's correct and publicly accessible."}, status_code=422)

    meta = _extract_metadata(url, page_html)
    llms_txt = _generate_llms_txt(meta)
    agent_card = _generate_agent_card(meta)

    return JSONResponse({
        "llms_txt": llms_txt,
        "agent_card": agent_card,
        "meta": meta,
    })


# ── GET /geo/claim — Pre-filled claim form ──────────────────────────────


@router.get("/geo/claim")
async def geo_claim_form(request: Request):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        user = await get_current_user(request, db)

    if not user:
        return RedirectResponse("/auth/github?next=/geo/claim", status_code=303)

    user_name = escape(user.get("name", ""))

    content = f"""
    <style>
        .claim-wrap {{
            max-width: 580px;
            margin: 0 auto;
            padding: 48px 24px;
        }}
        .claim-wrap h1 {{
            font-family: var(--font-display);
            font-size: var(--heading-lg);
            color: var(--ink);
            margin-bottom: 8px;
        }}
        .claim-wrap .sub {{
            color: var(--ink-muted);
            font-size: var(--text-base);
            margin-bottom: 32px;
        }}
        .claim-form label {{
            display: block;
            font-weight: 600;
            font-size: var(--text-sm);
            color: var(--ink);
            margin-bottom: 6px;
        }}
        .claim-form input, .claim-form textarea {{
            width: 100%;
            padding: 12px 14px;
            font-size: var(--text-base);
            font-family: var(--font-body);
            border: 1px solid var(--border);
            border-radius: 8px;
            background: var(--card-bg);
            color: var(--ink);
            margin-bottom: 20px;
            outline: none;
            box-sizing: border-box;
        }}
        .claim-form input:focus, .claim-form textarea:focus {{
            border-color: var(--slate);
        }}
        .claim-form textarea {{
            min-height: 80px;
            resize: vertical;
        }}
        .claim-form button {{
            padding: 14px 32px;
            font-size: var(--text-base);
            font-weight: 600;
            font-family: var(--font-body);
            background: var(--terracotta);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: opacity 0.2s;
        }}
        .claim-form button:hover {{
            opacity: 0.9;
        }}
    </style>

    <div class="claim-wrap">
        <h1>Claim Your Tool</h1>
        <p class="sub">Confirm the details below to add your tool to the IndieStack catalog.</p>

        <form class="claim-form" method="POST" action="/geo/claim">
            <label for="name">Tool Name</label>
            <input type="text" id="name" name="name" required />

            <label for="url">Website URL</label>
            <input type="url" id="url" name="url" required />

            <label for="tagline">Tagline</label>
            <input type="text" id="tagline" name="tagline" maxlength="120" />

            <label for="description">Description</label>
            <textarea id="description" name="description" rows="3"></textarea>

            <button type="submit">Claim &amp; List on IndieStack</button>
        </form>
    </div>

    <script>
    (function() {{
        try {{
            const raw = sessionStorage.getItem('geo_meta');
            if (!raw) return;
            const meta = JSON.parse(raw);
            if (meta.name) document.getElementById('name').value = meta.name;
            if (meta.url) document.getElementById('url').value = meta.url;
            if (meta.tagline) document.getElementById('tagline').value = meta.tagline;
            if (meta.description) document.getElementById('description').value = meta.description;
        }} catch(e) {{}}
    }})();
    </script>
    """
    return HTMLResponse(page_shell("Claim Your Tool — IndieStack", content))


# ── POST /geo/claim — Process submission ─────────────────────────────────


@router.post("/geo/claim")
async def geo_claim_submit(request: Request):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        user = await get_current_user(request, db)

        if not user:
            return RedirectResponse("/auth/github?next=/geo/claim", status_code=303)

        form = await request.form()
        name = (form.get("name") or "").strip()
        url = (form.get("url") or "").strip()
        tagline = (form.get("tagline") or "").strip()
        description = (form.get("description") or "").strip()

        if not name or not url:
            content = """
            <div style="max-width:580px;margin:0 auto;padding:48px 24px;text-align:center;">
                <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);color:var(--ink);margin-bottom:12px;">
                    Missing Info
                </h1>
                <p style="color:var(--ink-muted);margin-bottom:24px;">Name and URL are required.</p>
                <a href="/geo/claim" style="color:var(--slate);font-weight:600;text-decoration:none;">
                    &larr; Go back
                </a>
            </div>
            """
            return HTMLResponse(page_shell("Missing Info", content), status_code=400)

        # Check for duplicate slug
        slug = slugify(name)
        cursor = await db.execute("SELECT id FROM tools WHERE slug = ?", (slug,))
        if await cursor.fetchone():
            content = f"""
            <div style="max-width:580px;margin:0 auto;padding:48px 24px;text-align:center;">
                <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);color:var(--ink);margin-bottom:12px;">
                    Already Listed
                </h1>
                <p style="color:var(--ink-muted);margin-bottom:24px;">
                    A tool called <strong>{escape(name)}</strong> already exists on IndieStack.
                </p>
                <a href="/tool/{escape(slug)}" style="color:var(--slate);font-weight:600;text-decoration:none;">
                    View it &rarr;
                </a>
            </div>
            """
            return HTMLResponse(page_shell("Already Listed", content))

        # Get default category (first one)
        cats = await get_all_categories(db)
        cat_id = cats[0]["id"] if cats else 1

        # Detect source_type
        url_lower = url.lower()
        source_type = "code" if any(h in url_lower for h in ("github.com", "gitlab.com", "codeberg.org")) else "saas"

        # Insert as pending
        maker_name = user.get("name", "")
        tool_id = await create_tool(
            db,
            name=name,
            tagline=tagline,
            description=description,
            url=url,
            maker_name=maker_name,
            maker_url="",
            category_id=cat_id,
            tags="",
        )

        card_url = f"{BASE_URL}/cards/{escape(slug)}.json"

        content = f"""
        <div style="max-width:600px;margin:0 auto;padding:48px 24px;text-align:center;">
            <div style="margin-bottom:16px;"><svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div>
            <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);color:var(--ink);margin-bottom:12px;">
                {escape(name)} Claimed!
            </h1>
            <p style="color:var(--ink-muted);font-size:var(--text-base);margin-bottom:32px;">
                Your tool has been submitted for review. Once approved, it'll be discoverable
                by AI agents through IndieStack's MCP server.
            </p>

            <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:24px;text-align:left;margin-bottom:24px;">
                <h3 style="font-family:var(--font-display);font-size:var(--text-lg);color:var(--ink);margin-bottom:12px;">
                    Next Steps
                </h3>
                <ol style="color:var(--ink-muted);font-size:var(--text-sm);line-height:1.8;padding-left:20px;margin:0;">
                    <li>Add the generated <code style="font-family:var(--font-mono);background:var(--cream-dark);padding:2px 6px;border-radius:4px;">llms.txt</code> to your site root</li>
                    <li>Your Agent Card will be live at <a href="{card_url}" style="color:var(--slate);text-decoration:none;">{card_url}</a></li>
                    <li>We'll review and approve within 24 hours</li>
                </ol>
            </div>

            <a href="/geo" style="color:var(--slate);font-weight:600;text-decoration:none;">
                Generate for another tool &rarr;
            </a>
        </div>
        """
        return HTMLResponse(page_shell(f"{name} Claimed! — IndieStack", content))

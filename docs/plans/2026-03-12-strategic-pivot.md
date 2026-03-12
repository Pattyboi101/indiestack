# Strategic Pivot: Agent Cards + GEO Lead Magnet + Demand Signal Pro

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform IndieStack from a destination directory into headless agent infrastructure — per-tool Agent Cards for machine discovery, a GEO Lead Magnet that auto-grows the catalog, and a paid Demand Signal dashboard for revenue.

**Architecture:** Three features that form a flywheel: (1) Agent Cards make every tool machine-discoverable, (2) the GEO tool attracts indie devs who want AI discoverability and auto-adds their tools to the catalog, (3) the Demand Signal dashboard monetizes search gap data. All built on existing FastAPI routes, SQLite, pure Python HTML, Stripe Connect.

**Tech Stack:** Python/FastAPI, aiosqlite, SQLite, httpx (scraping), Stripe (subscriptions), GitHub OAuth (existing), pure Python string HTML templates

---

## Task 1: Per-Tool Agent Cards (`/cards/{slug}.json`)

**Files:**
- Modify: `src/indiestack/main.py`
- Modify: `src/indiestack/db.py` (if helper needed)

**What this does:** Exposes a structured A2A-compatible JSON capability card for every approved tool in the catalog. Agents can fetch `indiestack.ai/cards/hanko.json` and get machine-readable metadata: what the tool does, how to install it, what it's compatible with, auth method, API type — everything an orchestrator agent needs to decide whether to use this tool.

**Step 1: Add the `/cards/{slug}.json` endpoint to main.py**

Add this endpoint near the existing `/api/tools/{slug}` endpoint (around line 1859):

```python
@app.get("/cards/{slug}.json")
async def tool_agent_card(slug: str):
    """A2A-compatible Agent Card for a single tool — machine-readable capability definition."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT t.*, c.name as category_name, c.slug as category_slug
            FROM tools t
            JOIN categories c ON t.category_id = c.id
            WHERE t.slug = ? AND t.status = 'approved'
        """, (slug,))
        tool = cursor.fetchone()
        if not tool:
            return JSONResponse({"error": "Tool not found"}, status_code=404)
        tool = dict(await tool) if hasattr(tool, 'keys') else dict(tool)

        # Fetch compatibility pairs
        pairs_cursor = await db.execute("""
            SELECT CASE WHEN tool_a_slug = ? THEN tool_b_slug ELSE tool_a_slug END as pair_slug,
                   success_count, verified
            FROM tool_pairs
            WHERE (tool_a_slug = ? OR tool_b_slug = ?)
            ORDER BY success_count DESC LIMIT 10
        """, (slug, slug, slug))
        pairs = [dict(r) for r in await pairs_cursor.fetchall()]

    # Parse JSON fields safely
    import json as _json
    try:
        sdk = _json.loads(tool.get("sdk_packages") or "{}")
    except Exception:
        sdk = {}
    try:
        envs = _json.loads(tool.get("env_vars") or "[]")
    except Exception:
        envs = []
    frameworks = [f.strip() for f in (tool.get("frameworks_tested") or "").split(",") if f.strip()]

    # Build A2A-style card
    card = {
        "name": tool["name"],
        "slug": tool["slug"],
        "description": tool.get("tagline") or tool.get("description", ""),
        "url": tool.get("url", ""),
        "indiestack_url": f"https://indiestack.ai/tool/{slug}",
        "version": "1.0.0",
        "provider": {
            "name": tool.get("maker_name") or "Community Listed",
            "type": "indie"
        },
        "category": {
            "name": tool.get("category_name", ""),
            "slug": tool.get("category_slug", "")
        },
        "source_type": tool.get("source_type", "code"),
        "capabilities": {
            "api_type": tool.get("api_type") or None,
            "auth_method": tool.get("auth_method") or None,
            "install_command": tool.get("install_command") or None,
            "sdk_packages": sdk if sdk else None,
            "env_vars": envs if envs else None,
            "frameworks_tested": frameworks if frameworks else None,
        },
        "health": {
            "status": tool.get("health_status") or "unknown",
            "github_stars": tool.get("github_stars"),
            "github_language": tool.get("github_language"),
            "github_last_commit": tool.get("github_last_commit"),
            "github_is_archived": bool(tool.get("github_is_archived")),
        },
        "trust": {
            "is_verified": bool(tool.get("is_verified")),
            "is_ejectable": bool(tool.get("is_ejectable")),
            "upvote_count": tool.get("upvote_count", 0),
            "review_count": tool.get("review_count", 0),
            "avg_rating": tool.get("avg_rating"),
            "mcp_recommendations": tool.get("mcp_view_count", 0),
        },
        "compatibility": [
            {"slug": p["pair_slug"], "success_count": p["success_count"], "verified": bool(p["verified"])}
            for p in pairs
        ],
        "pricing": {
            "price_pence": tool.get("price_pence", 0),
            "is_free": (tool.get("price_pence") or 0) == 0,
        },
        "meta": {
            "generated_by": "indiestack.ai",
            "schema_version": "1.0",
            "catalog_size": 3095,
        }
    }

    # Strip None values from capabilities for cleaner output
    card["capabilities"] = {k: v for k, v in card["capabilities"].items() if v is not None}
    card["health"] = {k: v for k, v in card["health"].items() if v is not None}

    return JSONResponse(
        card,
        headers={
            "Cache-Control": "public, max-age=3600",
            "Access-Control-Allow-Origin": "*",
        }
    )
```

**Step 2: Add a catalog index of all cards**

Add endpoint for `/cards/index.json` that returns an array of all tool slugs with basic metadata, so agents can discover what cards exist:

```python
@app.get("/cards/index.json")
async def agent_cards_index():
    """Index of all available Agent Cards in the catalog."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT t.slug, t.name, t.tagline, c.slug as category_slug,
                   t.source_type, t.api_type, t.health_status
            FROM tools t
            JOIN categories c ON t.category_id = c.id
            WHERE t.status = 'approved'
            ORDER BY t.name
        """)
        tools = [dict(r) for r in await cursor.fetchall()]

    return JSONResponse({
        "schema_version": "1.0",
        "total": len(tools),
        "cards_base_url": "https://indiestack.ai/cards/",
        "tools": [
            {
                "slug": t["slug"],
                "name": t["name"],
                "tagline": t["tagline"],
                "category": t["category_slug"],
                "source_type": t["source_type"],
                "api_type": t.get("api_type") or None,
                "health": t.get("health_status") or "unknown",
                "card_url": f"https://indiestack.ai/cards/{t['slug']}.json"
            }
            for t in tools
        ]
    }, headers={
        "Cache-Control": "public, max-age=3600",
        "Access-Control-Allow-Origin": "*",
    })
```

**Step 3: Update the main agent-card.json to reference per-tool cards**

In the existing `/.well-known/agent-card.json` handler (main.py ~line 780), add to the `interfaces` object:

```python
"agent_cards": {
    "catalog_index": "https://indiestack.ai/cards/index.json",
    "card_template": "https://indiestack.ai/cards/{slug}.json",
    "total_tools": tool_count,
    "schema_version": "1.0"
}
```

**Step 4: Update llms.txt to reference cards**

In the `/llms.txt` handler (main.py ~line 691), add a line to the output:

```
## Agent Cards (Machine-Readable)
- Card Index: https://indiestack.ai/cards/index.json
- Per-Tool Card: https://indiestack.ai/cards/{slug}.json
```

**Step 5: Add `/cards/{slug}.json` to smoke test**

In `smoke_test.py`, add a test for the new endpoint:

```python
("/cards/index.json", 200, "cards index"),
```

Pick a known tool slug for a specific card test too.

**Verify:** `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read())"` then `python3 smoke_test.py`

---

## Task 2: GEO Lead Magnet (`/geo`)

**Files:**
- Create: `src/indiestack/routes/geo.py`
- Modify: `src/indiestack/main.py` (register router)
- Modify: `src/indiestack/routes/components.py` (add nav link if needed)

**What this does:** A free tool where indie devs paste their product URL → IndieStack scrapes it → generates optimized `llms.txt` + Agent Card files → requires GitHub OAuth to download → auto-adds the tool to the IndieStack catalog as a side effect. This is the inbound growth flywheel.

**Step 1: Create the route file with the landing page**

Create `src/indiestack/routes/geo.py`:

```python
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
import httpx
import html
import re
import json
from .components import page_shell

router = APIRouter()


def _extract_metadata(url: str, page_html: str) -> dict:
    """Extract metadata from a web page's HTML without BeautifulSoup."""
    meta = {"url": url, "name": "", "tagline": "", "description": "", "features": []}

    # Title
    title_match = re.search(r'<title[^>]*>(.*?)</title>', page_html, re.IGNORECASE | re.DOTALL)
    if title_match:
        raw_title = title_match.group(1).strip()
        # Clean common patterns like "Tool Name | Tagline" or "Tool Name - Tagline"
        parts = re.split(r'\s*[|–—-]\s*', raw_title, maxsplit=1)
        meta["name"] = html.unescape(parts[0].strip())
        if len(parts) > 1:
            meta["tagline"] = html.unescape(parts[1].strip())

    # Meta description
    desc_match = re.search(
        r'<meta\s+(?:[^>]*?\s+)?(?:name|property)=["\'](?:description|og:description)["\']'
        r'\s+content=["\']([^"\']*)["\']',
        page_html, re.IGNORECASE
    )
    if not desc_match:
        desc_match = re.search(
            r'<meta\s+content=["\']([^"\']*)["\']'
            r'\s+(?:name|property)=["\'](?:description|og:description)["\']',
            page_html, re.IGNORECASE
        )
    if desc_match:
        meta["description"] = html.unescape(desc_match.group(1).strip())

    # OG title fallback
    if not meta["name"]:
        og_title = re.search(
            r'<meta\s+(?:[^>]*?\s+)?property=["\']og:title["\']\s+content=["\']([^"\']*)["\']',
            page_html, re.IGNORECASE
        )
        if og_title:
            meta["name"] = html.unescape(og_title.group(1).strip())

    # H1 fallback for name
    if not meta["name"]:
        h1_match = re.search(r'<h1[^>]*>(.*?)</h1>', page_html, re.IGNORECASE | re.DOTALL)
        if h1_match:
            meta["name"] = html.unescape(re.sub(r'<[^>]+>', '', h1_match.group(1)).strip())

    # Extract h2/h3 as potential features
    headings = re.findall(r'<h[23][^>]*>(.*?)</h[23]>', page_html, re.IGNORECASE | re.DOTALL)
    for h in headings[:8]:
        clean = html.unescape(re.sub(r'<[^>]+>', '', h).strip())
        if clean and len(clean) > 3 and len(clean) < 100:
            meta["features"].append(clean)

    # Detect GitHub URL
    gh_match = re.search(r'href=["\']?(https://github\.com/[^/]+/[^/"\'>\s#?]+)', page_html, re.IGNORECASE)
    if gh_match:
        meta["github_url"] = gh_match.group(1)

    return meta


def _generate_llms_txt(meta: dict) -> str:
    """Generate an llms.txt file from extracted metadata."""
    lines = [f"# {meta.get('name', 'Unnamed Tool')}"]
    if meta.get("tagline"):
        lines.append(f"\n> {meta['tagline']}")
    lines.append(f"\n## About\n{meta.get('description', 'No description available.')}")
    if meta.get("url"):
        lines.append(f"\n- Website: {meta['url']}")
    if meta.get("github_url"):
        lines.append(f"- Source: {meta['github_url']}")
    if meta.get("features"):
        lines.append("\n## Features")
        for f in meta["features"][:6]:
            lines.append(f"- {f}")
    lines.append(f"\n## Discovery\n- IndieStack: https://indiestack.ai")
    lines.append(f"- Agent Card: https://indiestack.ai/cards/index.json")
    return "\n".join(lines)


def _generate_agent_card(meta: dict) -> dict:
    """Generate an A2A Agent Card JSON from extracted metadata."""
    return {
        "name": meta.get("name", ""),
        "description": meta.get("description") or meta.get("tagline", ""),
        "url": meta.get("url", ""),
        "version": "1.0.0",
        "provider": {"type": "indie"},
        "capabilities": {},
        "health": {"status": "unknown"},
        "trust": {"is_verified": False},
        "meta": {
            "generated_by": "indiestack.ai/geo",
            "schema_version": "1.0",
        }
    }


@router.get("/geo")
async def geo_page(request: Request):
    """GEO Lead Magnet — optimize your tool for AI agent discovery."""
    content = f'''
    <div style="max-width:720px;margin:0 auto;padding:40px 20px;">
        <h1 style="font-family:var(--serif);font-size:var(--heading-xl);margin:0 0 12px;">
            Make Your Tool AI-Discoverable
        </h1>
        <p style="color:var(--ink-muted);font-size:18px;line-height:1.6;margin:0 0 32px;">
            AI agents are replacing search engines. When someone asks Claude, Cursor, or Copilot
            to build something, will the agent know your tool exists?
            Generate the files that make your tool visible to every AI agent on the internet.
        </p>

        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:24px;margin:0 0 32px;">
            <h2 style="margin:0 0 8px;font-size:18px;">What you get</h2>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:16px;">
                <div style="padding:16px;background:var(--bg);border-radius:8px;">
                    <strong style="color:var(--cyan);">llms.txt</strong>
                    <p style="color:var(--ink-muted);font-size:14px;margin:8px 0 0;">
                        The standard file AI models read to understand your product. Like robots.txt, but for LLMs.
                    </p>
                </div>
                <div style="padding:16px;background:var(--bg);border-radius:8px;">
                    <strong style="color:var(--cyan);">Agent Card</strong>
                    <p style="color:var(--ink-muted);font-size:14px;margin:8px 0 0;">
                        Structured JSON that tells orchestrator agents exactly what your tool does and how to use it.
                    </p>
                </div>
            </div>
        </div>

        <div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:24px;">
            <h2 style="margin:0 0 16px;font-size:18px;">Paste your URL</h2>
            <form id="geo-form" style="display:flex;gap:8px;">
                <input type="url" id="geo-url" placeholder="https://your-tool.com"
                       required
                       style="flex:1;padding:12px 16px;border-radius:8px;border:1px solid var(--border);
                              background:var(--bg);color:var(--ink);font-size:16px;">
                <button type="submit"
                        style="padding:12px 24px;border-radius:8px;border:none;
                               background:var(--cyan);color:#000;font-weight:600;font-size:16px;
                               cursor:pointer;white-space:nowrap;">
                    Generate
                </button>
            </form>
            <p style="color:var(--ink-muted);font-size:13px;margin:8px 0 0;">
                We'll scan your page and generate AI discovery files in seconds.
            </p>
        </div>

        <div id="geo-results" style="display:none;margin-top:32px;">
            <div style="display:flex;gap:16px;margin-bottom:24px;">
                <button onclick="showTab('llms')" id="tab-llms" class="geo-tab geo-tab-active"
                        style="padding:8px 16px;border-radius:8px;border:1px solid var(--border);
                               background:var(--cyan);color:#000;font-weight:600;cursor:pointer;">
                    llms.txt
                </button>
                <button onclick="showTab('card')" id="tab-card" class="geo-tab"
                        style="padding:8px 16px;border-radius:8px;border:1px solid var(--border);
                               background:var(--bg-card);color:var(--ink);cursor:pointer;">
                    Agent Card JSON
                </button>
            </div>

            <div id="result-llms">
                <pre id="llms-output"
                     style="background:var(--bg);border:1px solid var(--border);border-radius:8px;
                            padding:16px;font-family:var(--mono);font-size:13px;line-height:1.6;
                            overflow-x:auto;white-space:pre-wrap;color:var(--ink);"></pre>
            </div>
            <div id="result-card" style="display:none;">
                <pre id="card-output"
                     style="background:var(--bg);border:1px solid var(--border);border-radius:8px;
                            padding:16px;font-family:var(--mono);font-size:13px;line-height:1.6;
                            overflow-x:auto;white-space:pre-wrap;color:var(--ink);"></pre>
            </div>

            <div style="margin-top:24px;padding:20px;background:var(--bg-card);border:1px solid var(--cyan);
                        border-radius:12px;text-align:center;">
                <p style="margin:0 0 12px;font-size:16px;">
                    <strong>Want these files hosted for you?</strong>
                </p>
                <p style="color:var(--ink-muted);margin:0 0 16px;font-size:14px;">
                    Sign in with GitHub to claim your tool on IndieStack. We'll host your Agent Card,
                    list your tool in our catalog, and make it discoverable to every AI agent using our MCP server.
                </p>
                <a href="/auth/github?next=/geo/claim" id="geo-claim-btn"
                   style="display:inline-block;padding:12px 24px;border-radius:8px;
                          background:var(--navy);color:#fff;font-weight:600;text-decoration:none;
                          font-size:16px;">
                    Sign in with GitHub to Claim
                </a>
            </div>
        </div>

        <div style="margin-top:48px;padding-top:32px;border-top:1px solid var(--border);">
            <h2 style="font-family:var(--serif);font-size:24px;margin:0 0 16px;">
                Why this matters
            </h2>
            <div style="display:grid;gap:16px;">
                <div style="display:flex;gap:12px;align-items:flex-start;">
                    <span style="color:var(--cyan);font-size:20px;line-height:1;">1</span>
                    <div>
                        <strong>Search traffic is declining</strong>
                        <p style="color:var(--ink-muted);margin:4px 0 0;font-size:14px;">
                            AI overviews are replacing blue links. Traditional SEO alone won't cut it.
                        </p>
                    </div>
                </div>
                <div style="display:flex;gap:12px;align-items:flex-start;">
                    <span style="color:var(--cyan);font-size:20px;line-height:1;">2</span>
                    <div>
                        <strong>Agents need structured data</strong>
                        <p style="color:var(--ink-muted);margin:4px 0 0;font-size:14px;">
                            llms.txt and Agent Cards tell AI exactly what your tool does — no hallucination.
                        </p>
                    </div>
                </div>
                <div style="display:flex;gap:12px;align-items:flex-start;">
                    <span style="color:var(--cyan);font-size:20px;line-height:1;">3</span>
                    <div>
                        <strong>First movers win</strong>
                        <p style="color:var(--ink-muted);margin:4px 0 0;font-size:14px;">
                            Tools with Agent Cards get recommended. Tools without them get rebuilt from scratch.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
    const form = document.getElementById('geo-form');
    const results = document.getElementById('geo-results');
    const llmsOut = document.getElementById('llms-output');
    const cardOut = document.getElementById('card-output');

    form.addEventListener('submit', async (e) => {{
        e.preventDefault();
        const url = document.getElementById('geo-url').value.trim();
        if (!url) return;
        const btn = form.querySelector('button');
        btn.textContent = 'Scanning...';
        btn.disabled = true;
        try {{
            const resp = await fetch('/geo/generate', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{url}})
            }});
            const data = await resp.json();
            if (data.error) {{
                alert(data.error);
                return;
            }}
            llmsOut.textContent = data.llms_txt;
            cardOut.textContent = JSON.stringify(data.agent_card, null, 2);
            results.style.display = 'block';
            // Store in sessionStorage for claim flow
            sessionStorage.setItem('geo_meta', JSON.stringify(data.meta));
            // Update claim link with tool data
            const claimBtn = document.getElementById('geo-claim-btn');
            claimBtn.href = '/auth/github?next=/geo/claim';
        }} catch(err) {{
            alert('Failed to scan URL. Please try again.');
        }} finally {{
            btn.textContent = 'Generate';
            btn.disabled = false;
        }}
    }});

    function showTab(tab) {{
        document.getElementById('result-llms').style.display = tab === 'llms' ? '' : 'none';
        document.getElementById('result-card').style.display = tab === 'card' ? '' : 'none';
        document.querySelectorAll('.geo-tab').forEach(t => {{
            t.style.background = 'var(--bg-card)';
            t.style.color = 'var(--ink)';
        }});
        document.getElementById('tab-' + tab).style.background = 'var(--cyan)';
        document.getElementById('tab-' + tab).style.color = '#000';
    }}
    </script>
    '''
    return HTMLResponse(page_shell(request, "Make Your Tool AI-Discoverable — IndieStack", content))


@router.post("/geo/generate")
async def geo_generate(request: Request):
    """Scrape a URL and generate llms.txt + Agent Card."""
    try:
        data = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    url = (data.get("url") or "").strip()
    if not url or not url.startswith("http"):
        return JSONResponse({"error": "Please provide a valid URL starting with http"}, status_code=400)

    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            resp = await client.get(url, headers={
                "User-Agent": "IndieStack-GEO/1.0 (https://indiestack.ai/geo)"
            })
            if resp.status_code != 200:
                return JSONResponse({"error": f"Could not fetch URL (status {resp.status_code})"}, status_code=400)
            page_html = resp.text
    except httpx.TimeoutException:
        return JSONResponse({"error": "URL timed out after 15 seconds"}, status_code=400)
    except Exception as e:
        return JSONResponse({"error": f"Could not fetch URL: {str(e)[:100]}"}, status_code=400)

    meta = _extract_metadata(url, page_html)
    llms_txt = _generate_llms_txt(meta)
    agent_card = _generate_agent_card(meta)

    return JSONResponse({
        "llms_txt": llms_txt,
        "agent_card": agent_card,
        "meta": meta,
    })


@router.get("/geo/claim")
async def geo_claim(request: Request):
    """After GitHub OAuth, show the claim/submit form pre-filled with GEO data."""
    session_token = request.cookies.get("indiestack_session")
    if not session_token:
        return HTMLResponse('<script>window.location="/auth/github?next=/geo/claim";</script>')

    content = f'''
    <div style="max-width:600px;margin:0 auto;padding:40px 20px;">
        <h1 style="font-family:var(--serif);font-size:var(--heading-lg);margin:0 0 12px;">
            Claim Your Tool
        </h1>
        <p style="color:var(--ink-muted);margin:0 0 24px;">
            Review the details below and submit to add your tool to IndieStack's catalog.
            Your Agent Card will be hosted automatically.
        </p>

        <form method="POST" action="/geo/claim" style="display:grid;gap:16px;">
            <div>
                <label style="font-weight:600;display:block;margin-bottom:4px;">Tool Name</label>
                <input type="text" name="name" id="claim-name" required
                       style="width:100%;padding:10px;border-radius:8px;border:1px solid var(--border);
                              background:var(--bg);color:var(--ink);font-size:16px;">
            </div>
            <div>
                <label style="font-weight:600;display:block;margin-bottom:4px;">URL</label>
                <input type="url" name="url" id="claim-url" required
                       style="width:100%;padding:10px;border-radius:8px;border:1px solid var(--border);
                              background:var(--bg);color:var(--ink);font-size:16px;">
            </div>
            <div>
                <label style="font-weight:600;display:block;margin-bottom:4px;">Tagline</label>
                <input type="text" name="tagline" id="claim-tagline" maxlength="120"
                       style="width:100%;padding:10px;border-radius:8px;border:1px solid var(--border);
                              background:var(--bg);color:var(--ink);">
            </div>
            <div>
                <label style="font-weight:600;display:block;margin-bottom:4px;">Description</label>
                <textarea name="description" id="claim-desc" rows="4"
                          style="width:100%;padding:10px;border-radius:8px;border:1px solid var(--border);
                                 background:var(--bg);color:var(--ink);resize:vertical;"></textarea>
            </div>
            <button type="submit"
                    style="padding:12px 24px;border-radius:8px;border:none;
                           background:var(--cyan);color:#000;font-weight:600;font-size:16px;
                           cursor:pointer;">
                Submit & Get Your Agent Card
            </button>
        </form>
    </div>

    <script>
    // Pre-fill from sessionStorage if available
    try {{
        const meta = JSON.parse(sessionStorage.getItem('geo_meta') || '{{}}');
        if (meta.name) document.getElementById('claim-name').value = meta.name;
        if (meta.url) document.getElementById('claim-url').value = meta.url;
        if (meta.tagline) document.getElementById('claim-tagline').value = meta.tagline;
        if (meta.description) document.getElementById('claim-desc').value = meta.description;
    }} catch(e) {{}}
    </script>
    '''
    return HTMLResponse(page_shell(request, "Claim Your Tool — IndieStack", content))


@router.post("/geo/claim")
async def geo_claim_submit(request: Request):
    """Process the GEO claim form — submit tool + auto-claim for user."""
    import aiosqlite
    from ..db import DB_PATH, generate_slug

    session_token = request.cookies.get("indiestack_session")
    if not session_token:
        return HTMLResponse('<script>window.location="/auth/github?next=/geo/claim";</script>')

    form = await request.form()
    name = (form.get("name") or "").strip()
    url = (form.get("url") or "").strip()
    tagline = (form.get("tagline") or "").strip()
    description = (form.get("description") or "").strip()

    if not name or not url:
        return HTMLResponse('<script>alert("Name and URL are required");history.back();</script>')

    slug = generate_slug(name)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        # Get current user from session
        cursor = await db.execute(
            "SELECT id, name as user_name FROM users WHERE session_token = ?",
            (session_token,)
        )
        user = await cursor.fetchone()
        if not user:
            return HTMLResponse('<script>window.location="/auth/github?next=/geo/claim";</script>')

        user_id = user["id"]

        # Check for existing tool with this slug
        existing = await db.execute("SELECT id FROM tools WHERE slug = ?", (slug,))
        if await existing.fetchone():
            # Tool exists — redirect to it
            return HTMLResponse(
                f'<script>window.location="/tool/{slug}?msg=already_exists";</script>'
            )

        # Get default category (Developer Tools)
        cat_cursor = await db.execute("SELECT id FROM categories LIMIT 1")
        cat_row = await cat_cursor.fetchone()
        category_id = cat_row["id"] if cat_row else 1

        # Detect source type
        source_type = "code" if "github.com" in url or "gitlab.com" in url or "codeberg.org" in url else "saas"

        # Insert tool as pending (will be auto-approved or reviewed)
        await db.execute("""
            INSERT INTO tools (name, slug, url, tagline, description, category_id,
                             status, source_type, submitted_from_ip)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, ?)
        """, (name, slug, url, tagline, description, category_id,
              source_type, request.client.host))
        await db.commit()

        # Get the new tool id
        tool_cursor = await db.execute("SELECT id FROM tools WHERE slug = ?", (slug,))
        tool_row = await tool_cursor.fetchone()

    card_url = f"https://indiestack.ai/cards/{slug}.json"
    content = f'''
    <div style="max-width:600px;margin:0 auto;padding:40px 20px;text-align:center;">
        <div style="font-size:48px;margin-bottom:16px;">&#10003;</div>
        <h1 style="font-family:var(--serif);font-size:var(--heading-lg);margin:0 0 12px;">
            Tool Submitted!
        </h1>
        <p style="color:var(--ink-muted);margin:0 0 24px;">
            <strong>{html.escape(name)}</strong> has been submitted to IndieStack.
            Once approved, your Agent Card will be live at:
        </p>
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;
                    padding:12px;font-family:var(--mono);font-size:14px;margin:0 0 24px;
                    word-break:break-all;">
            {html.escape(card_url)}
        </div>

        <h2 style="font-size:18px;margin:32px 0 12px;">Add to your website now</h2>
        <p style="color:var(--ink-muted);font-size:14px;margin:0 0 16px;">
            Place these files at your site root to boost AI discoverability immediately:
        </p>

        <div style="text-align:left;background:var(--bg-card);border:1px solid var(--border);
                    border-radius:8px;padding:16px;margin:0 0 16px;">
            <strong style="font-size:14px;">llms.txt</strong>
            <p style="color:var(--ink-muted);font-size:13px;margin:4px 0 8px;">
                Save as <code>llms.txt</code> at your site root
            </p>
            <code style="font-size:12px;color:var(--ink-muted);">yoursite.com/llms.txt</code>
        </div>

        <div style="text-align:left;background:var(--bg-card);border:1px solid var(--border);
                    border-radius:8px;padding:16px;margin:0 0 24px;">
            <strong style="font-size:14px;">Agent Card</strong>
            <p style="color:var(--ink-muted);font-size:13px;margin:4px 0 8px;">
                Save as <code>.well-known/agent-card.json</code>
            </p>
            <code style="font-size:12px;color:var(--ink-muted);">yoursite.com/.well-known/agent-card.json</code>
        </div>

        <a href="/tool/{slug}" style="display:inline-block;padding:12px 24px;border-radius:8px;
                                       background:var(--cyan);color:#000;font-weight:600;
                                       text-decoration:none;font-size:16px;">
            View Your Tool Page
        </a>
    </div>
    '''
    return HTMLResponse(page_shell(request, "Tool Submitted! — IndieStack", content))
```

**Step 2: Register the router in main.py**

Near the other router includes (search for `app.include_router`), add:

```python
from .routes.geo import router as geo_router
app.include_router(geo_router)
```

**Step 3: Add /geo to smoke test**

```python
("/geo", 200, "GEO lead magnet page"),
```

**Step 4: Add "AI Optimize" to nav (optional — Browse dropdown)**

In `components.py`, in the Browse dropdown items, add:

```python
'<a href="/geo" ...>AI Optimize</a>'
```

**Verify:** Syntax check all modified files, then `python3 smoke_test.py`

---

## Task 3: Demand Signal Pro Dashboard (`/demand`)

**Files:**
- Modify: `src/indiestack/routes/gaps.py`
- Modify: `src/indiestack/main.py` (Stripe subscription endpoint)
- Modify: `src/indiestack/db.py` (demand analytics queries)

**What this does:** Enhances the existing Demand Bounty Board with a paid tier that shows deeper analytics — clustered demand signals, trend data over time, weekly demand digest, and export. Free tier stays as-is. Pro tier is $15/month via Stripe.

**Step 1: Add demand analytics queries to db.py**

Add these helper functions to db.py:

```python
async def get_demand_trends(db, days: int = 30) -> list:
    """Get demand signal trends over time — zero-result searches grouped by day."""
    cursor = await db.execute("""
        SELECT DATE(created_at) as day,
               COUNT(*) as total_searches,
               SUM(CASE WHEN result_count = 0 THEN 1 ELSE 0 END) as zero_results
        FROM search_logs
        WHERE created_at >= datetime('now', ?)
        GROUP BY DATE(created_at)
        ORDER BY day DESC
    """, (f'-{days} days',))
    return [dict(r) for r in await cursor.fetchall()]


async def get_demand_clusters(db, limit: int = 50) -> list:
    """Get clustered demand signals with richer metadata than basic gaps."""
    cursor = await db.execute("""
        SELECT LOWER(query) as query,
               COUNT(*) as search_count,
               SUM(CASE WHEN result_count = 0 THEN 1 ELSE 0 END) as zero_count,
               MAX(created_at) as last_searched,
               MIN(created_at) as first_searched,
               COUNT(DISTINCT source) as source_count,
               GROUP_CONCAT(DISTINCT source) as sources
        FROM search_logs
        WHERE LENGTH(query) >= 3
          AND query NOT LIKE '%http%'
          AND query NOT LIKE '%.com%'
        GROUP BY LOWER(query)
        HAVING zero_count > 0
        ORDER BY zero_count DESC, search_count DESC
        LIMIT ?
    """, (limit,))
    return [dict(r) for r in await cursor.fetchall()]
```

**Step 2: Add subscription check table migration to db.py**

In the migration block:

```python
await db.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        stripe_subscription_id TEXT,
        plan TEXT NOT NULL DEFAULT 'demand_pro',
        status TEXT NOT NULL DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
""")
```

**Step 3: Add pro section to gaps.py**

After the existing free gaps content, add a "Pro" section that's gated:

```python
@router.get("/demand")
async def demand_pro(request: Request):
    """Pro demand signal dashboard — paid tier."""
    session_token = request.cookies.get("indiestack_session")
    is_pro = False

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row

        if session_token:
            cursor = await db.execute(
                "SELECT id FROM users WHERE session_token = ?", (session_token,)
            )
            user = await cursor.fetchone()
            if user:
                sub_cursor = await db.execute(
                    "SELECT id FROM subscriptions WHERE user_id = ? AND status = 'active' AND plan = 'demand_pro'",
                    (user["id"],)
                )
                is_pro = bool(await sub_cursor.fetchone())

        if not is_pro:
            # Show upgrade CTA
            content = _demand_pro_cta()
            return HTMLResponse(page_shell(request, "Demand Signals Pro — IndieStack", content))

        # Pro user — show full data
        trends = await get_demand_trends(db, days=30)
        clusters = await get_demand_clusters(db, limit=50)

    content = _demand_pro_dashboard(trends, clusters)
    return HTMLResponse(page_shell(request, "Demand Signals Pro — IndieStack", content))
```

Where `_demand_pro_cta()` renders the upgrade page with pricing and value prop, and `_demand_pro_dashboard()` renders the full analytics view with trend charts (CSS-only bar charts, no JS libraries needed) and the clustered demand table.

**Step 4: Add Stripe subscription endpoint to main.py**

```python
@app.post("/api/subscribe/demand-pro")
async def subscribe_demand_pro(request: Request):
    """Create a Stripe Checkout session for Demand Pro subscription."""
    session_token = request.cookies.get("indiestack_session")
    if not session_token:
        return JSONResponse({"error": "Login required"}, status_code=401)

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT id, email FROM users WHERE session_token = ?", (session_token,)
        )
        user = await cursor.fetchone()
        if not user:
            return JSONResponse({"error": "Login required"}, status_code=401)

    import stripe
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

    checkout = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": os.environ.get("STRIPE_DEMAND_PRO_PRICE_ID"), "quantity": 1}],
        success_url="https://indiestack.ai/demand?subscribed=true",
        cancel_url="https://indiestack.ai/demand",
        customer_email=user["email"] if user.get("email") else None,
        metadata={"user_id": str(user["id"]), "plan": "demand_pro"},
    )
    return JSONResponse({"checkout_url": checkout.url})
```

**Step 5: Handle subscription webhook**

Add to the existing Stripe webhook handler in main.py — on `checkout.session.completed` with `mode=subscription`, insert into `subscriptions` table.

**Step 6: Add /demand to smoke test and nav**

**Verify:** Syntax check all files, `python3 smoke_test.py`

---

## Parallelisation Strategy

- **Task 1** (Agent Cards) and **Task 2** (GEO Lead Magnet) can run as **parallel agents** — they touch different parts of main.py and Task 2 creates a new file
- **Task 3** (Demand Pro) depends on nothing from Tasks 1-2 but is lower priority — run after or in parallel if agents available
- All three touch `main.py` but in different sections — coordinate imports at the end

## Post-Implementation

1. Run `python3 smoke_test.py` — all tests pass
2. Deploy: `cd /home/patty/indiestack && ~/.fly/bin/flyctl deploy --remote-only`
3. Create Stripe Price for Demand Pro subscription ($15/month) and set `STRIPE_DEMAND_PRO_PRICE_ID` as Fly secret
4. Test GEO flow end-to-end: paste URL → see generated files → sign in → tool submitted
5. Verify `/cards/hanko.json` returns valid JSON
6. Update MCP server instructions to mention Agent Cards
7. Update MEMORY.md files

## Constraints

- All CSS inline or via existing design tokens in components.py `:root`
- No Jinja2, no React — pure Python f-string HTML
- Run syntax check after every file edit (PostToolUse hook handles this)
- Run smoke tests before deploying
- Use `python3` not `python`
- Import `html` for `html.escape()` on any user-provided data rendered in HTML
- No external dependencies beyond what's already installed (httpx, stripe, aiosqlite)

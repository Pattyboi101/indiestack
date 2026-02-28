"""Tool submission form."""

import logging
from datetime import date
from html import escape
from typing import Optional

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell
from urllib.parse import quote

from indiestack.db import get_all_categories, create_tool, get_tool_by_id, slugify, get_maker_by_id, get_tool_by_slug

logger = logging.getLogger(__name__)

router = APIRouter()


def submit_success_page(tool_name, tool_slug, maker_slug=""):
    tool_url = f"{BASE_URL}/tool/{tool_slug}"
    tweet_text = quote(f"Just listed {tool_name} on @IndieStack! \U0001f680")
    tweet_url = quote(tool_url)
    badge_src = f"{BASE_URL}/api/badge/{tool_slug}.svg"
    embed_code = escape(f'<a href="{tool_url}"><img src="{badge_src}" alt="{tool_name} on IndieStack"></a>')

    launch_link = ""
    if maker_slug:
        launch_link = f"""
        <div style="text-align:center;margin-top:24px;">
            <a href="/launch/{escape(maker_slug)}" style="color:var(--navy);font-weight:600;font-size:15px;text-decoration:none;">
                View your Launch page &rarr;
            </a>
        </div>
        """

    return f"""
    <div class="container" style="max-width:640px;padding:48px 24px;">
        <!-- Celebration header -->
        <div style="text-align:center;margin-bottom:32px;">
            <div style="font-size:64px;margin-bottom:16px;">&#127881;</div>
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);margin-bottom:8px;">
                {escape(tool_name)} is listed!
            </h1>
            <p style="color:var(--ink-muted);font-size:15px;">We'll review within 24 hours.</p>
        </div>

        <!-- AI Discovery callout -->
        <div style="background:linear-gradient(135deg, #1A2D4A 0%, #0D1B2A 100%);border-radius:var(--radius);padding:24px;margin-bottom:24px;">
            <p style="color:white;font-size:15px;line-height:1.6;margin:0;">
                &#129302; Your tool is now searchable by AI coding assistants (Cursor, Windsurf, Claude Code) through our MCP server.
            </p>
        </div>

        <!-- Milestone card -->
        <div style="background:white;border:1px solid var(--border);border-radius:var(--radius);padding:24px;margin-bottom:24px;text-align:center;">
            <img src="/api/milestone/{escape(tool_slug)}.svg?type=first-tool" alt="Milestone"
                 style="max-width:100%;margin-bottom:16px;">
            <div style="display:flex;justify-content:center;gap:12px;">
                <a href="/api/milestone/{escape(tool_slug)}.svg?type=first-tool" download
                   class="btn" style="padding:10px 20px;font-size:14px;">
                    Download
                </a>
                <a href="https://twitter.com/intent/tweet?text={tweet_text}&url={tweet_url}"
                   target="_blank" rel="noopener"
                   class="btn btn-primary" style="padding:10px 20px;font-size:14px;">
                    Share on X
                </a>
            </div>
        </div>

        <!-- Embeddable badge -->
        <div style="background:white;border:1px solid var(--border);border-radius:var(--radius);padding:24px;margin-bottom:24px;">
            <p style="font-weight:600;font-size:15px;color:var(--ink);margin-bottom:12px;">Embeddable Badge</p>
            <div style="text-align:center;margin-bottom:12px;">
                <img src="/api/badge/{escape(tool_slug)}.svg" alt="{escape(tool_name)} on IndieStack">
            </div>
            <textarea id="badge-embed" readonly
                      style="width:100%;height:60px;padding:10px;font-family:var(--font-mono);font-size:12px;border:1px solid var(--border);border-radius:var(--radius-sm);resize:none;background:var(--cream-dark);color:var(--ink);">{embed_code}</textarea>
            <button type="button" onclick="navigator.clipboard.writeText(document.getElementById('badge-embed').value).then(function(){{this.textContent='Copied!'}}.bind(this))"
                    style="margin-top:8px;padding:8px 16px;background:var(--ink);color:white;border:none;border-radius:var(--radius-sm);font-size:13px;font-weight:600;cursor:pointer;">
                Copy
            </button>
        </div>

        {launch_link}

        <!-- Verified upsell -->
        <div style="background:#FDF8EE;border:1px solid var(--gold);border-radius:var(--radius);padding:24px;margin-top:24px;text-align:center;">
            <p style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:6px;">
                Want to stand out?
            </p>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                Get a verified badge for &pound;29 &mdash; rank higher, build trust, and get noticed.
            </p>
            <a href="/verify/{escape(tool_slug)}" class="btn" style="background:linear-gradient(135deg, var(--gold), #D4A24A);
                    color:#5C3D0E;font-weight:700;padding:10px 24px;border-radius:999px;border:1px solid var(--gold);">
                Get Verified &rarr;
            </a>
        </div>
    </div>
    """


def submit_form(categories, values: dict = None, error: str = "", success: str = "", tool_count: int = 0) -> str:
    v = values or {}
    name_val = escape(str(v.get('name', '')))
    tagline_val = escape(str(v.get('tagline', '')))
    url_val = escape(str(v.get('url', '')))
    desc_val = escape(str(v.get('description', '')))
    maker_name_val = escape(str(v.get('maker_name', '')))
    maker_url_val = escape(str(v.get('maker_url', '')))
    tags_val = escape(str(v.get('tags', '')))
    replaces_val = escape(str(v.get('replaces', '')))
    selected_cat = v.get('category_id', '')
    price_val = escape(str(v.get('price', '')))
    delivery_url_val = escape(str(v.get('delivery_url', '')))
    selected_delivery = v.get('delivery_type', 'link')

    alert = ''
    if error:
        alert = f'<div class="alert alert-error">{escape(error)}</div>'
    if success:
        alert = f'<div class="alert alert-success">{escape(success)}</div>'

    cat_options = '<option value="">Select a category...</option>'
    for c in categories:
        sel = ' selected' if str(c['id']) == str(selected_cat) else ''
        cat_options += f'<option value="{c["id"]}"{sel}>{escape(str(c["name"]))}</option>'

    delivery_options = ''
    for dtype, dlabel in [('link', 'Link / redirect'), ('download', 'File download'), ('license_key', 'License key')]:
        dsel = ' selected' if dtype == selected_delivery else ''
        delivery_options += f'<option value="{dtype}"{dsel}>{dlabel}</option>'

    github_import = """
        <div style="background:var(--cream-dark);border:2px solid var(--border);border-radius:var(--radius);padding:28px 24px;margin-bottom:0;">
            <div style="text-align:center;margin-bottom:16px;">
                <svg width="32" height="32" viewBox="0 0 16 16" fill="var(--ink)" style="margin-bottom:8px;"><path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
                <p style="font-size:20px;font-weight:700;color:var(--ink);margin:0 0 4px;">Paste your GitHub URL</p>
                <p style="font-size:14px;color:var(--ink-muted);margin:0;">We'll auto-fill everything. Done in 30 seconds.</p>
            </div>
            <div style="display:flex;gap:8px;">
                <input type="text" id="github-url" placeholder="https://github.com/you/your-repo"
                       style="flex:1;padding:12px 14px;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:14px;background:white;">
                <button type="button" id="github-fetch-btn" onclick="fetchGitHub()"
                        style="padding:12px 22px;background:var(--terracotta);color:white;border:none;border-radius:var(--radius-sm);font-weight:700;font-size:14px;cursor:pointer;white-space:nowrap;">
                    Auto-fill &rarr;
                </button>
            </div>
            <p id="github-status" style="font-size:12px;color:var(--ink-muted);margin-top:8px;display:none;"></p>
        </div>
        <div style="display:flex;align-items:center;gap:16px;margin:28px 0;"><div style="flex:1;height:1px;background:var(--border);"></div><span style="color:var(--ink-muted);font-size:13px;white-space:nowrap;">or fill in the form manually</span><div style="flex:1;height:1px;background:var(--border);"></div></div>
    """

    github_js = """
        <script>
        async function fetchGitHub() {
            var url = document.getElementById('github-url').value.trim();
            if (!url) return;
            var btn = document.getElementById('github-fetch-btn');
            var status = document.getElementById('github-status');
            btn.textContent = 'Fetching...';
            btn.disabled = true;
            status.style.display = 'block';
            status.textContent = 'Pulling repo details...';
            status.style.color = 'var(--ink-muted)';
            try {
                var resp = await fetch('/api/github-fetch', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({url: url})
                });
                var data = await resp.json();
                if (data.error) {
                    status.textContent = data.error;
                    status.style.color = '#c0392b';
                } else {
                    if (data.name) document.getElementById('name').value = data.name;
                    if (data.tagline) document.getElementById('tagline').value = data.tagline;
                    if (data.description) document.getElementById('description').value = data.description;
                    if (data.url) document.getElementById('url').value = data.url;
                    if (data.tags) document.getElementById('tags').value = data.tags;
                    status.textContent = 'Auto-filled! Review and edit below.';
                    status.style.color = '#27ae60';
                }
            } catch(e) {
                status.textContent = 'Failed to fetch. Check the URL.';
                status.style.color = '#c0392b';
            }
            btn.textContent = 'Auto-fill';
            btn.disabled = false;
        }
        </script>
    """

    return f"""
    <div class="container" style="max-width:640px;padding:48px 24px;">
        {"" if date.today() >= date(2026, 3, 2) else '''<div style="background:linear-gradient(135deg,#1A2D4A 0%,#0D1B2A 100%);border-radius:var(--radius);padding:20px 24px;margin-bottom:32px;text-align:center;">
            <p style="color:white;font-size:15px;font-weight:600;margin:0;">
                &#128640; Marketplace launches March 2nd
            </p>
            <p style="color:rgba(255,255,255,0.7);font-size:13px;margin:6px 0 0;">
                List now for free. Set a price to queue for launch. Tools with early reviews and upvotes rank higher on day one.
            </p>
        </div>'''}
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);">Make Your Tool Discoverable by AI</h1>
            <p style="color:var(--ink-muted);margin-top:8px;">{f"{tool_count}+ tools are already searchable by AI coding assistants via our MCP server. List yours free — we'll review within 24 hours." if tool_count > 0 else "Tools listed here are searchable by AI coding assistants via our MCP server. List yours free — we'll review within 24 hours."}</p>
        </div>
        {alert}
        {github_import}
        <form method="post" action="/submit">
            <div class="form-group">
                <label for="name">Tool Name *</label>
                <input type="text" id="name" name="name" class="form-input" required value="{name_val}"
                       placeholder="e.g. InvoiceNinja">
            </div>
            <div class="form-group">
                <label for="tagline">Tagline * <span style="color:var(--ink-muted);font-size:13px;font-weight:400;">(max 100 chars)</span></label>
                <input type="text" id="tagline" name="tagline" class="form-input" required maxlength="100"
                       value="{tagline_val}" placeholder="e.g. Open-source invoicing for freelancers">
            </div>
            <div class="form-group">
                <label for="url">Website URL *</label>
                <input type="url" id="url" name="url" class="form-input" required value="{url_val}"
                       placeholder="https://your-tool.com">
            </div>
            <div class="form-group">
                <label for="description">Description *</label>
                <textarea id="description" name="description" class="form-textarea" required
                          placeholder="Tell us what your tool does and who it's for...">{desc_val}</textarea>
            </div>
            <div class="form-group">
                <label for="category_id">Category *</label>
                <select id="category_id" name="category_id" class="form-select" required>
                    {cat_options}
                </select>
            </div>

            <div style="background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius);padding:24px;margin:28px 0;">
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:4px;color:var(--ink);">Listing &amp; Pricing</h3>

                <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:20px;">
                    <div style="background:white;border:1px solid var(--border);border-radius:var(--radius-sm);padding:16px;">
                        <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
                            <span style="font-size:14px;">&#9989;</span>
                            <strong style="font-size:14px;color:var(--ink);">Free listing</strong>
                        </div>
                        <p style="color:var(--ink-muted);font-size:13px;line-height:1.5;margin:0;">
                            Goes live immediately after approval. Your tool gets reviews, upvotes,
                            and AI discovery through our MCP server.
                        </p>
                    </div>
                    <div style="background:white;border:1px solid #00D4F5;border-radius:var(--radius-sm);padding:16px;">
                        <div style="display:flex;align-items:center;gap:6px;margin-bottom:6px;">
                            <span style="font-size:14px;">&#128176;</span>
                            <strong style="font-size:14px;color:var(--ink);">Sell on IndieStack</strong>
                            <span style="font-size:11px;font-weight:700;color:#00D4F5;background:rgba(0,212,245,0.1);padding:2px 8px;border-radius:999px;">{"Live" if date.today() >= date(2026, 3, 2) else "March 2nd"}</span>
                        </div>
                        <p style="color:var(--ink-muted);font-size:13px;line-height:1.5;margin:0;">
                            Set a price to queue for our marketplace launch. Build reviews and
                            upvotes now &mdash; top-rated tools rank higher on launch day.
                        </p>
                    </div>
                </div>
                <div style="background:linear-gradient(135deg,#1A2D4A 0%,#0D1B2A 100%);border-radius:var(--radius-sm);padding:16px;margin-top:16px;">
                    <p style="color:white;font-size:14px;font-weight:600;margin-bottom:4px;">&#129302; AI Discovery — included free</p>
                    <p style="color:rgba(255,255,255,0.7);font-size:13px;line-height:1.5;margin:0;">
                        Every listed tool is instantly searchable by AI coding assistants (Cursor, Windsurf, Claude Code) through IndieStack's MCP server.
                    </p>
                </div>

                <div class="form-group">
                    <label for="price">Price (GBP) <span style="color:var(--ink-muted);font-size:13px;font-weight:400;">&mdash; leave blank for a free listing</span></label>
                    <div style="position:relative;">
                        <span style="position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--ink-muted);font-weight:600;">&pound;</span>
                        <input type="number" id="price" name="price" class="form-input" step="0.01" min="0.50"
                               value="{price_val}" placeholder="e.g. 9.00"
                               style="padding-left:30px;">
                    </div>
                </div>
                {"" if not (date(2026, 3, 2) <= date.today() <= date(2026, 3, 16)) else '''<div style="background:linear-gradient(135deg,var(--gold-light) 0%,rgba(226,183,100,0.15) 100%);border:1px solid var(--gold);border-radius:var(--radius-sm);padding:12px 16px;margin-top:12px;">
                    <p style="margin:0;font-size:13px;font-weight:600;color:var(--gold-dark);">
                        &#127881; Launch Week Special &mdash; 0% platform commission until March 16th. You keep everything (minus Stripe fees).
                    </p>
                </div>'''}
                <div id="submit-earnings-calc" style="background:white;border:1px solid var(--border);border-radius:var(--radius-sm);padding:14px;margin-top:12px;display:none;">
                    <p style="font-size:13px;font-weight:600;color:var(--ink);margin-bottom:8px;">Earnings Preview</p>
                    <div style="font-size:14px;color:var(--ink-light);line-height:2;">
                        <div style="display:flex;justify-content:space-between;">You set: <span id="sc-price">-</span></div>
                        <div style="display:flex;justify-content:space-between;">Stripe (~3%): <span id="sc-stripe" style="color:var(--ink-muted);">-</span></div>
                        <div style="display:flex;justify-content:space-between;">Platform (<span id="sc-rate">5</span>%): <span id="sc-platform" style="color:var(--ink-muted);">-</span></div>
                        <div style="display:flex;justify-content:space-between;border-top:1px solid var(--border);padding-top:6px;margin-top:4px;">
                            <strong style="color:var(--terracotta);">You earn:</strong>
                            <strong id="sc-earn" style="color:var(--terracotta);">-</strong>
                        </div>
                    </div>
                </div>
                <script>
                document.getElementById('price').addEventListener('input', function() {{
                    var calc = document.getElementById('submit-earnings-calc');
                    var v = parseFloat(this.value);
                    if (v > 0) {{
                        calc.style.display = 'block';
                        var now = new Date();
                        var launchStart = new Date(2026, 2, 2);
                        var launchEnd = new Date(2026, 2, 16);
                        var isHoliday = (now >= launchStart && now <= launchEnd);
                        var platformRate = isHoliday ? 0 : 0.05;
                        var stripe = v * 0.03;
                        var platform = v * platformRate;
                        var earn = v - stripe - platform;
                        document.getElementById('sc-price').textContent = '\\u00a3' + v.toFixed(2);
                        document.getElementById('sc-stripe').textContent = '-\\u00a3' + stripe.toFixed(2);
                        document.getElementById('sc-platform').textContent = '-\\u00a3' + platform.toFixed(2);
                        document.getElementById('sc-rate').textContent = isHoliday ? '0' : '5';
                        document.getElementById('sc-earn').textContent = '\\u00a3' + earn.toFixed(2);
                    }} else {{ calc.style.display = 'none'; }}
                }});
                </script>
                <div class="form-group">
                    <label for="delivery_type">How will buyers receive it? <span style="color:var(--ink-muted);font-size:13px;font-weight:400;">&mdash; you can update this before launch</span></label>
                    <select id="delivery_type" name="delivery_type" class="form-select">
                        {delivery_options}
                    </select>
                </div>
                <div class="form-group" style="margin-bottom:0;">
                    <label for="delivery_url">Delivery URL <span style="color:var(--ink-muted);font-size:13px;font-weight:400;">&mdash; optional for now</span></label>
                    <input type="url" id="delivery_url" name="delivery_url" class="form-input"
                           value="{delivery_url_val}" placeholder="e.g. https://github.com/you/repo or https://your-tool.com/download">
                </div>
            </div>

            <div class="form-group">
                <label for="maker_name">Your Name</label>
                <input type="text" id="maker_name" name="maker_name" class="form-input"
                       value="{maker_name_val}" placeholder="Jane Doe">
            </div>
            <div class="form-group">
                <label for="maker_url">Your Website / Twitter</label>
                <input type="url" id="maker_url" name="maker_url" class="form-input"
                       value="{maker_url_val}" placeholder="https://twitter.com/you">
            </div>
            <div class="form-group">
                <label for="tags">Tags <span style="color:var(--ink-muted);font-size:13px;font-weight:400;">(comma-separated, optional)</span></label>
                <input type="text" id="tags" name="tags" class="form-input"
                       value="{tags_val}" placeholder="e.g. open-source, freemium, API">
            </div>
            <div class="form-group">
                <label for="replaces">Replaces <span style="color:var(--ink-muted);font-size:13px;font-weight:400;">(what big-tech tool does yours replace? comma-separated)</span></label>
                <input type="text" id="replaces" name="replaces" class="form-input"
                       value="{replaces_val}" placeholder="e.g. Mailchimp, Google Analytics, Auth0">
                <p style="color:var(--ink-muted);font-size:12px;margin-top:6px;">
                    This helps us generate &ldquo;alternatives to&rdquo; pages that drive traffic to your listing.
                </p>
            </div>
            <div class="form-group">
                <label style="display:flex;align-items:center;gap:10px;cursor:pointer;">
                    <input type="checkbox" name="supports_export" value="1"
                           style="accent-color:var(--terracotta);width:18px;height:18px;">
                    <span>
                        <strong style="font-size:14px;color:var(--ink);">&#128275; My tool supports full data export</strong>
                        <br><span style="font-size:13px;color:var(--ink-muted);">Tools with clean data export get a &ldquo;Certified Ejectable&rdquo; badge after admin review.</span>
                    </span>
                </label>
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:14px;">
                Submit for Review
            </button>
        </form>
        {github_js}
    </div>
    """


@router.get("/submit", response_class=HTMLResponse)
async def submit_get(request: Request):
    db = request.state.db

    # Handle success page (accessible without login for public submissions)
    if request.query_params.get('status') == 'success':
        tool_slug = request.query_params.get('tool', '')
        tool_name = "Your Tool"
        maker_slug = ""
        if tool_slug:
            tool = await get_tool_by_slug(db, tool_slug)
            if tool:
                tool_name = tool['name']
        user = request.state.user
        if user and user.get('maker_id'):
            maker = await get_maker_by_id(db, user['maker_id'])
            if maker:
                maker_slug = maker.get('slug', '')
        body = submit_success_page(tool_name, tool_slug, maker_slug=maker_slug)
        return HTMLResponse(page_shell("Tool Submitted", body, user=request.state.user))

    # Require login for the submit form itself
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)

    categories = await get_all_categories(db)
    values = {}
    user = request.state.user
    if user.get('maker_id'):
        maker = await get_maker_by_id(db, user['maker_id'])
        if maker:
            values['maker_name'] = maker.get('name', '')
            values['maker_url'] = maker.get('url', '')
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")
    row = await cursor.fetchone()
    tool_count = row['cnt'] if row else 0
    body = submit_form(categories, values=values, tool_count=tool_count)
    return HTMLResponse(page_shell("Make Your Tool Discoverable by AI", body, user=user))


@router.post("/submit", response_class=HTMLResponse)
async def submit_post(
    request: Request,
    name: str = Form(""),
    tagline: str = Form(""),
    url: str = Form(""),
    description: str = Form(""),
    category_id: str = Form(""),
    maker_name: str = Form(""),
    maker_url: str = Form(""),
    tags: str = Form(""),
    price: str = Form(""),
    delivery_type: str = Form("link"),
    delivery_url: str = Form(""),
    replaces: str = Form(""),
    supports_export: str = Form(""),
    # Public (no-login) submission fields
    email: str = Form(""),
    website2: str = Form(""),  # honeypot
):
    # Honeypot check: bots fill the hidden website2 field, humans don't
    if website2:
        logger.warning(f"Honeypot triggered from {request.client.host}")
        return RedirectResponse(url="/submit?status=success", status_code=303)

    # Allow public submissions if email is provided (no login required)
    is_public = not request.state.user
    if is_public and not email.strip():
        return RedirectResponse(url="/login", status_code=303)

    db = request.state.db
    categories = await get_all_categories(db)

    values = dict(name=name, tagline=tagline, url=url, description=description,
                  category_id=category_id, maker_name=maker_name, maker_url=maker_url,
                  tags=tags, replaces=replaces, price=price, delivery_type=delivery_type, delivery_url=delivery_url)

    # Validation
    errors = []
    if not name.strip():
        errors.append("Tool name is required.")
    if not tagline.strip():
        errors.append("Tagline is required.")
    if not url.strip() or not url.startswith("http"):
        errors.append("A valid URL starting with http is required.")
    if not description.strip():
        errors.append("Description is required.")
    if not category_id or not str(category_id).isdigit():
        errors.append("Please select a category.")

    # Parse price
    price_pence = None
    if price.strip():
        try:
            price_float = float(price.strip())
            if price_float < 0.50:
                errors.append("Minimum price is \u00a30.50.")
            else:
                price_pence = int(round(price_float * 100))
        except ValueError:
            errors.append("Invalid price format.")

    # Delivery URL is optional pre-launch — makers can add it before March 2nd

    if delivery_type not in ('link', 'download', 'license_key'):
        delivery_type = 'link'

    if errors:
        body = submit_form(categories, values, error=" ".join(errors))
        return HTMLResponse(page_shell("Make Your Tool Discoverable by AI", body, user=request.state.user))

    tool_id = await create_tool(
        db, name=name.strip(), tagline=tagline.strip(), description=description.strip(),
        url=url.strip(), maker_name=maker_name.strip(), maker_url=maker_url.strip(),
        category_id=int(category_id), tags=tags.strip(),
        price_pence=price_pence, delivery_type=delivery_type,
        delivery_url=delivery_url.strip(),
    )

    # Auto-detect GitHub URL
    if 'github.com/' in url:
        import re as _re
        gh_match = _re.match(r'https?://github\.com/([^/]+)/([^/]+)', url)
        if gh_match:
            await db.execute("UPDATE tools SET github_url = ? WHERE id = ?", (url.strip(), tool_id))
            await db.commit()

    # Save replaces field if provided
    if replaces.strip():
        await db.execute("UPDATE tools SET replaces = ? WHERE id = ?", (replaces.strip(), tool_id))
        await db.commit()

    # Store submitter email for public (no-login) submissions
    if is_public and email.strip():
        await db.execute(
            "UPDATE tools SET submitter_email = ?, submitted_from_ip = ? WHERE id = ?",
            (email.strip().lower(), request.client.host, tool_id),
        )
        await db.commit()
        logger.info(f"Public submission: '{name.strip()}' from {email.strip()} ({request.client.host})")

    # Get the tool slug for verification link
    tool = await get_tool_by_id(db, tool_id)
    tool_slug = tool['slug'] if tool else slugify(name.strip())

    # Public submissions get a simple redirect (no session for page_shell)
    if is_public:
        return RedirectResponse(url=f"/submit?status=success&tool={tool_slug}", status_code=303)

    # Look up maker_slug for logged-in users
    maker_slug = ""
    if request.state.user and request.state.user.get('maker_id'):
        maker = await get_maker_by_id(db, request.state.user['maker_id'])
        if maker:
            maker_slug = maker.get('slug', '')

    body = submit_success_page(name.strip(), tool_slug, maker_slug)
    return HTMLResponse(page_shell("Tool Submitted", body, user=request.state.user))

"""Submission form."""

import logging
from datetime import date
from html import escape
from typing import Optional

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell
from urllib.parse import quote

from indiestack.db import get_all_categories, create_tool, get_tool_by_id, slugify, get_maker_by_id, get_tool_by_slug, track_event, validate_submission_quality, check_duplicate_url

logger = logging.getLogger(__name__)

router = APIRouter()


def submit_success_page(tool_name, tool_slug, maker_slug="", tool_type=None):
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
        <div style="background:linear-gradient(135deg, var(--terracotta) 0%, var(--terracotta-dark) 100%);border-radius:var(--radius);padding:24px;margin-bottom:24px;">
            <p style="color:white;font-size:15px;line-height:1.6;margin:0;">
                &#129302; {"Your " + escape({"mcp_server": "MCP server", "plugin": "plugin", "extension": "extension", "skill": "skill"}.get(tool_type, "plugin")) + " is now discoverable by AI coding assistants through our MCP server and plugin directory." if tool_type else "Your creation is now discoverable by AI agents (Cursor, Windsurf, Claude Code) through our MCP server."}
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

    </div>
    """


def submit_form(categories, values: dict = None, error: str = "", success: str = "", tool_count: int = 0, logged_in: bool = True) -> str:
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

    if logged_in:
        email_field = ''
        submit_or_login_btn = '<button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:14px;">Submit for Review</button>'
    else:
        email_val = escape(str(v.get('email', '')))
        email_field = f'''
            <div class="form-group">
                <label for="email">Your Email * <span style="color:var(--ink-muted);font-size:13px;font-weight:400;">(so we can follow up)</span></label>
                <input type="email" id="email" name="email" class="form-input" required value="{email_val}"
                       placeholder="you@example.com">
            </div>
            <div style="position:absolute;left:-9999px;" aria-hidden="true">
                <input type="text" name="website2" tabindex="-1" autocomplete="off">
            </div>
        '''
        submit_or_login_btn = (
            '<button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:14px;">Submit for Review</button>'
            '<p style="text-align:center;color:var(--ink-muted);font-size:13px;margin-top:12px;">'
            'No account needed. <a href="/login" style="color:var(--accent);">Log in with GitHub</a> to claim and manage your listing later.</p>'
        )

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
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);">Make Your Creation Discoverable by AI</h1>
            <p style="color:var(--ink-muted);margin-top:8px;">{f"{tool_count}+ creations are already discoverable by AI agents via our MCP server. List yours free — we'll review within 24 hours." if tool_count > 0 else "Creations listed here are discoverable by AI agents via our MCP server. List yours free — we'll review within 24 hours."}</p>
            <p style="color:var(--ink-muted);font-size:14px;margin-top:12px;">
                Before submitting, please read our <a href="/guidelines" style="color:var(--accent);font-weight:600;">submission guidelines</a>.
            </p>
        </div>

        <div style="background:var(--info-bg);border:1px solid var(--info-border);border-radius:var(--radius);padding:20px 24px;margin-bottom:32px;line-height:1.7;">
            <p style="font-size:14px;color:var(--info-text);margin:0;">
                <strong>A note from us:</strong> IndieStack is still young &mdash; a small, curated directory built by two uni students in Cardiff.
                We&rsquo;re building something we think matters: a knowledge base where AI agents recommend real creations
                instead of building from scratch. Games, utilities, newsletters, dev tools &mdash; anything you&rsquo;ve built. Every listing helps craft that generational knowledge.
                Early listers get the most visibility as the catalog grows.
            </p>
            <p style="font-size:14px;color:var(--info-text);margin:12px 0 0 0;">
                &#127942; <strong>Pick of the Week:</strong> The most AI-recommended creation each week gets featured
                on our homepage. The more agents discover yours, the higher your chances.
            </p>
        </div>
        {alert}
        {github_import}
        <form method="post" action="/submit">
            <div class="form-group">
                <label for="name">Name *</label>
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
                       placeholder="https://yourproject.com">
            </div>
            <div class="form-group">
                <label for="description">Description *</label>
                <textarea id="description" name="description" class="form-textarea" required
                          placeholder="Tell us what you've built and who it's for...">{desc_val}</textarea>
            </div>
            <div class="form-group">
                <label for="category_id">Category *</label>
                <select id="category_id" name="category_id" class="form-select" required>
                    {cat_options}
                </select>
            </div>

            <!-- Agent Plugin Section -->
            <div style="background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius);padding:24px;margin:24px 0;">
                <label style="display:flex;align-items:center;gap:12px;cursor:pointer;margin-bottom:0;">
                    <input type="checkbox" id="is_plugin" name="is_plugin" value="1"
                           onchange="document.getElementById('plugin-fields').style.display=this.checked?'block':'none'"
                           class="custom-checkbox"
                           {"checked" if v.get('tool_type') else ""}>
                    <div>
                        <strong style="font-size:15px;color:var(--ink);">This is an agent plugin or extension</strong>
                        <p style="color:var(--ink-muted);font-size:13px;margin:4px 0 0;">MCP server, Claude Code plugin, Cursor extension, AI skill, etc.</p>
                    </div>
                </label>
                <div id="plugin-fields" style="display:{"block" if v.get("tool_type") else "none"};margin-top:24px;">
                    <div class="form-group">
                        <label for="tool_type">Type *</label>
                        <select id="tool_type" name="tool_type" class="form-select">
                            <option value="">Select type...</option>
                            <option value="mcp_server" {"selected" if v.get("tool_type") == "mcp_server" else ""}>MCP Server</option>
                            <option value="plugin" {"selected" if v.get("tool_type") == "plugin" else ""}>Plugin</option>
                            <option value="extension" {"selected" if v.get("tool_type") == "extension" else ""}>Extension</option>
                            <option value="skill" {"selected" if v.get("tool_type") == "skill" else ""}>Skill</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="platforms">Compatible platforms <span style="color:var(--ink-muted);font-size:13px;font-weight:400;">(comma-separated)</span></label>
                        <input type="text" id="platforms" name="platforms" class="form-input"
                               value="{escape(str(v.get('platforms', '')))}" placeholder="e.g. Claude Code, Cursor, Windsurf">
                    </div>
                    <div class="form-group">
                        <label for="install_command">Install command</label>
                        <input type="text" id="install_command" name="install_command" class="form-input"
                               value="{escape(str(v.get('install_command', '')))}"
                               placeholder="e.g. claude mcp add your-tool"
                               style="font-family:var(--font-mono);font-size:14px;">
                    </div>
                </div>
            </div>

            <div style="background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius);padding:24px;margin:28px 0;">
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:16px;color:var(--ink);">What You Get</h3>

                <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
                    <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-sm);padding:16px;">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                            <span style="font-size:14px;">&#9989;</span>
                            <strong style="font-size:14px;color:var(--ink);">Free forever</strong>
                        </div>
                        <p style="color:var(--ink-muted);font-size:13px;line-height:1.5;margin:0;">
                            No fees, no commission, no catch. Your creation gets reviews, upvotes,
                            and a permanent listing in the catalog.
                        </p>
                    </div>
                    <div style="background:var(--card-bg);border:1px solid var(--accent);border-radius:var(--radius-sm);padding:16px;">
                        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                            <span style="font-size:14px;">&#129302;</span>
                            <strong style="font-size:14px;color:var(--ink);">AI Discovery</strong>
                            <span style="font-size:11px;font-weight:700;color:var(--slate);background:rgba(0,212,245,0.1);padding:2px 8px;border-radius:999px;">Live</span>
                        </div>
                        <p style="color:var(--ink-muted);font-size:13px;line-height:1.5;margin:0;">
                            AI agents (Cursor, Windsurf, Claude Code) search IndieStack via MCP
                            before building from scratch. Your creation becomes part of the supply chain.
                        </p>
                    </div>
                </div>

                <input type="hidden" id="price" name="price" value="">
                <input type="hidden" id="delivery_type" name="delivery_type" value="link">
                <input type="hidden" id="delivery_url" name="delivery_url" value="{delivery_url_val}">
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
                           class="custom-checkbox">
                    <span>
                        <strong style="font-size:14px;color:var(--ink);">&#128275; Supports full data export</strong>
                        <br><span style="font-size:13px;color:var(--ink-muted);">Creations with clean data export get a &ldquo;Certified Ejectable&rdquo; badge after admin review.</span>
                    </span>
                </label>
            </div>
            {email_field}
            {submit_or_login_btn}
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
        tool_name = "Your Creation"
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
        return HTMLResponse(page_shell("Submitted", body, user=request.state.user))

    categories = await get_all_categories(db)
    values = {}
    # Pre-fill name from query param (e.g. from /gaps "Fill this gap" links)
    prefill_name = request.query_params.get('name', '').strip()
    if prefill_name:
        values['name'] = prefill_name
    user = request.state.user
    logged_in = user is not None
    if logged_in and user.get('maker_id'):
        maker = await get_maker_by_id(db, user['maker_id'])
        if maker:
            values['maker_name'] = maker.get('name', '')
            values['maker_url'] = maker.get('url', '')
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")
    row = await cursor.fetchone()
    tool_count = row['cnt'] if row else 0
    body = submit_form(categories, values=values, tool_count=tool_count, logged_in=logged_in)
    return HTMLResponse(page_shell("Make Your Creation Discoverable by AI", body, user=user))


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
    is_plugin: str = Form(""),
    tool_type: str = Form(""),
    platforms: str = Form(""),
    install_command: str = Form(""),
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
                  tags=tags, replaces=replaces, price=price, delivery_type=delivery_type, delivery_url=delivery_url,
                  tool_type=tool_type if is_plugin else None,
                  platforms=platforms if is_plugin else '',
                  install_command=install_command if is_plugin else '',
                  email=email)

    # Auto-prepend https:// if missing protocol (mobile users often skip it)
    if url.strip() and not url.startswith("http"):
        url = "https://" + url.strip()

    # Validation
    errors = []
    if not name.strip():
        errors.append("Name is required.")
    if not tagline.strip():
        errors.append("Tagline is required.")
    if not url.strip() or not url.startswith("http"):
        errors.append("A valid URL starting with http is required.")
    if not description.strip():
        errors.append("Description is required.")
    if not category_id or not str(category_id).isdigit():
        errors.append("Please select a category.")
    if is_public and (not email.strip() or '@' not in email):
        errors.append("A valid email is required.")

    # Quality gates — minimum content quality
    if not errors:
        quality_errors = validate_submission_quality(name, tagline, description, url)
        errors.extend(quality_errors)

    # URL reachability check — reject dead URLs before they enter the queue
    if not errors and url.strip():
        import httpx as _httpx
        from urllib.parse import urlparse as _urlparse
        import socket as _socket, ipaddress as _ipaddress
        _skip_check = False
        try:
            _host = _urlparse(url.strip()).hostname or ''
            for _addr_info in _socket.getaddrinfo(_host, None):
                _ip = _ipaddress.ip_address(_addr_info[4][0])
                if _ip.is_private or _ip.is_loopback or _ip.is_link_local:
                    errors.append("URL resolves to a private or internal address.")
                    _skip_check = True
                    break
        except Exception:
            pass  # DNS failure will be caught by the HEAD request below
        if not _skip_check and not errors:
            try:
                async with _httpx.AsyncClient(timeout=10.0, follow_redirects=True) as _client:
                    resp = await _client.head(url.strip())
                    if resp.status_code >= 400:
                        errors.append(f"Your URL returned HTTP {resp.status_code}. Please check that your tool is live and accessible.")
            except Exception:
                errors.append("We couldn't reach your URL. Please check that your tool is live and accessible, then try again.")

    # Duplicate URL check
    if not errors and url.strip():
        existing = await check_duplicate_url(db, url.strip())
        if existing:
            errors.append(f"A tool with this URL already exists: {escape(existing['name'])} (/{escape(existing['slug'])}).")

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
        body = submit_form(categories, values, error=" ".join(errors), logged_in=not is_public)
        return HTMLResponse(page_shell("Make Your Creation Discoverable by AI", body, user=request.state.user))

    tool_id = await create_tool(
        db, name=name.strip(), tagline=tagline.strip(), description=description.strip(),
        url=url.strip(), maker_name=maker_name.strip(), maker_url=maker_url.strip(),
        category_id=int(category_id), tags=tags.strip(),
        price_pence=price_pence, delivery_type=delivery_type,
        delivery_url=delivery_url.strip(),
        tool_type=tool_type.strip() if is_plugin and tool_type.strip() else None,
        platforms=platforms.strip() if is_plugin else '',
        install_command=install_command.strip() if is_plugin else '',
    )

    # Post-create updates (single commit for all)
    if 'github.com/' in url:
        import re as _re
        gh_match = _re.match(r'https?://github\.com/([^/]+)/([^/]+)', url)
        if gh_match:
            await db.execute("UPDATE tools SET github_url = ? WHERE id = ?", (url.strip(), tool_id))
    if replaces.strip():
        await db.execute("UPDATE tools SET replaces = ? WHERE id = ?", (replaces.strip(), tool_id))
    if is_public and email.strip():
        await db.execute(
            "UPDATE tools SET submitter_email = ?, submitted_from_ip = ? WHERE id = ?",
            (email.strip().lower(), request.client.host, tool_id),
        )
        logger.info(f"Public submission: '{name.strip()}' from {email.strip()} ({request.client.host})")
    await db.commit()

    # Async enrichment — gather quality signals for admin review
    import asyncio as _asyncio
    from indiestack.db import enrich_domain_age, enrich_free_tier, enrich_social_proof
    try:
        await _asyncio.gather(
            enrich_domain_age(db, tool_id, url.strip()),
            enrich_free_tier(db, tool_id, url.strip()),
            enrich_social_proof(db, tool_id, url.strip()),
            return_exceptions=True,
        )
        await db.commit()
    except Exception:
        pass  # Enrichment is best-effort — don't block submission

    # Track submission event
    user = request.state.user
    tool_slug_for_event = slugify(name.strip())
    await track_event(db, 'tool_submitted', user_id=user['id'] if user else None, metadata={'slug': tool_slug_for_event})

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

    body = submit_success_page(name.strip(), tool_slug, maker_slug, tool_type=tool_type.strip() if is_plugin and tool_type.strip() else None)
    return HTMLResponse(page_shell("Submitted", body, user=request.state.user))

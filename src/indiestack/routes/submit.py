"""Tool submission form."""

import logging
from html import escape
from typing import Optional

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.routes.components import page_shell
from indiestack.db import get_all_categories, create_tool, get_tool_by_id, slugify, get_maker_by_id

logger = logging.getLogger(__name__)

router = APIRouter()


def submit_form(categories, values: dict = None, error: str = "", success: str = "") -> str:
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

    return f"""
    <div class="container" style="max-width:640px;padding:48px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);">Submit Your Tool</h1>
            <p style="color:var(--ink-muted);margin-top:8px;">Share your indie SaaS tool with the community. We'll review it within 24 hours.</p>
        </div>
        {alert}
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
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:4px;color:var(--ink);">Sell on IndieStack</h3>
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                    Set a price to sell directly through IndieStack. Leave blank for a free listing.
                </p>

                <div style="background:white;border:1px solid var(--border);border-radius:var(--radius-sm);padding:16px;margin-bottom:20px;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;">
                        <span style="font-size:16px;">&#9989;</span>
                        <strong style="font-size:14px;color:var(--ink);">Free to list</strong>
                        <br><span style="font-size:13px;color:var(--ink-muted);margin-top:4px;display:inline-block;">Get your tool discovered by developers and AI coding assistants.</span>
                    </div>
                    <p style="color:var(--ink-muted);font-size:13px;line-height:1.5;margin:0;">
                        No listing fees, no hidden charges. Your tool gets its own page with reviews,
                        upvotes, integration snippets, and visibility through our MCP server.
                    </p>
                </div>

                <div class="form-group">
                    <label for="price">Price (GBP)</label>
                    <div style="position:relative;">
                        <span style="position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--ink-muted);font-weight:600;">&pound;</span>
                        <input type="number" id="price" name="price" class="form-input" step="0.01" min="0.50"
                               value="{price_val}" placeholder="e.g. 9.00"
                               style="padding-left:30px;">
                    </div>
                </div>
                <div id="submit-earnings-calc" style="background:white;border:1px solid var(--border);border-radius:var(--radius-sm);padding:14px;margin-top:12px;display:none;">
                    <p style="font-size:13px;font-weight:600;color:var(--ink);margin-bottom:8px;">Earnings Preview</p>
                    <div style="font-size:14px;color:var(--ink-light);line-height:2;">
                        <div style="display:flex;justify-content:space-between;">You set: <span id="sc-price">-</span></div>
                        <div style="display:flex;justify-content:space-between;">Stripe (~3%): <span id="sc-stripe" style="color:var(--ink-muted);">-</span></div>
                        <div style="display:flex;justify-content:space-between;">Platform (5%): <span id="sc-platform" style="color:var(--ink-muted);">-</span></div>
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
                        var stripe = v * 0.03;
                        var platform = v * 0.05;
                        var earn = v - stripe - platform;
                        document.getElementById('sc-price').textContent = '\\u00a3' + v.toFixed(2);
                        document.getElementById('sc-stripe').textContent = '-\\u00a3' + stripe.toFixed(2);
                        document.getElementById('sc-platform').textContent = '-\\u00a3' + platform.toFixed(2);
                        document.getElementById('sc-earn').textContent = '\\u00a3' + earn.toFixed(2);
                    }} else {{ calc.style.display = 'none'; }}
                }});
                </script>
                <div class="form-group">
                    <label for="delivery_type">How will buyers receive it?</label>
                    <select id="delivery_type" name="delivery_type" class="form-select">
                        {delivery_options}
                    </select>
                    <p style="color:var(--ink-muted);font-size:12px;margin-top:6px;">
                        After payment, the buyer is redirected to your delivery URL.
                        This could be a private GitHub repo, a download page, or a license portal.
                    </p>
                </div>
                <div class="form-group" style="margin-bottom:0;">
                    <label for="delivery_url">Delivery URL <span style="color:var(--ink-muted);font-size:13px;font-weight:400;">(where buyers go after purchase)</span></label>
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
    </div>
    """


@router.get("/submit", response_class=HTMLResponse)
async def submit_get(request: Request):
    if not request.state.user:
        return RedirectResponse(url="/login", status_code=303)
    db = request.state.db
    categories = await get_all_categories(db)
    values = {}
    user = request.state.user
    if user.get('maker_id'):
        maker = await get_maker_by_id(db, user['maker_id'])
        if maker:
            values['maker_name'] = maker.get('name', '')
            values['maker_url'] = maker.get('url', '')
    body = submit_form(categories, values=values)
    return HTMLResponse(page_shell("Submit Your Tool", body, user=user))


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

    if price_pence and not delivery_url.strip():
        errors.append("Delivery URL is required for paid tools.")

    if delivery_type not in ('link', 'download', 'license_key'):
        delivery_type = 'link'

    if errors:
        body = submit_form(categories, values, error=" ".join(errors))
        return HTMLResponse(page_shell("Submit Your Tool", body, user=request.state.user))

    tool_id = await create_tool(
        db, name=name.strip(), tagline=tagline.strip(), description=description.strip(),
        url=url.strip(), maker_name=maker_name.strip(), maker_url=maker_url.strip(),
        category_id=int(category_id), tags=tags.strip(),
        price_pence=price_pence, delivery_type=delivery_type,
        delivery_url=delivery_url.strip(),
    )

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

    verify_upsell = f"""
    <div style="background:#FDF8EE;border:1px solid var(--gold);border-radius:var(--radius);
                padding:24px;margin-bottom:24px;text-align:center;">
        <p style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:6px;">
            Want to stand out?
        </p>
        <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
            Get a verified badge for &pound;29 — rank higher, build trust, and get noticed.
        </p>
        <a href="/verify/{tool_slug}" class="btn" style="background:linear-gradient(135deg, var(--gold), #D4A24A);
                color:#5C3D0E;font-weight:700;padding:10px 24px;border-radius:999px;border:1px solid var(--gold);">
            Get Verified &rarr;
        </a>
    </div>
    """

    # Public submissions get a simple redirect (no session for page_shell)
    if is_public:
        return RedirectResponse(url="/submit?status=success", status_code=303)

    body = submit_form(categories, success="Your tool has been submitted! We'll review it shortly.")
    # Insert upsell before the form
    body = verify_upsell + body
    return HTMLResponse(page_shell("Submit Your Tool", body, user=request.state.user))

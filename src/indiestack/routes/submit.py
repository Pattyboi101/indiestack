"""Tool submission form."""

from html import escape
from typing import Optional

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell
from indiestack.db import get_all_categories, create_tool

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
            <h1 style="font-family:var(--font-display);font-size:36px;">Submit Your Tool</h1>
            <p class="text-muted mt-2">Share your indie SaaS tool with the community. We'll review it within 24 hours.</p>
        </div>
        {alert}
        <form method="post" action="/submit">
            <div class="form-group">
                <label for="name">Tool Name *</label>
                <input type="text" id="name" name="name" class="form-input" required value="{name_val}"
                       placeholder="e.g. InvoiceNinja">
            </div>
            <div class="form-group">
                <label for="tagline">Tagline * <span class="text-muted text-sm">(max 100 chars)</span></label>
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

            <div style="background:var(--stone-100);border:1px solid var(--stone-200);border-radius:var(--radius);padding:24px;margin:28px 0;">
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:4px;">Sell on IndieStack</h3>
                <p class="text-muted text-sm" style="margin-bottom:20px;">
                    Set a price to sell directly through IndieStack. Leave blank for a free listing.
                </p>
                <div class="form-group">
                    <label for="price">Price (GBP)</label>
                    <div style="position:relative;">
                        <span style="position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--stone-400);font-weight:600;">&pound;</span>
                        <input type="number" id="price" name="price" class="form-input" step="0.01" min="0.50"
                               value="{price_val}" placeholder="e.g. 9.00"
                               style="padding-left:30px;">
                    </div>
                </div>
                <div class="form-group">
                    <label for="delivery_type">Delivery method</label>
                    <select id="delivery_type" name="delivery_type" class="form-select">
                        {delivery_options}
                    </select>
                </div>
                <div class="form-group" style="margin-bottom:0;">
                    <label for="delivery_url">Delivery URL <span class="text-muted text-sm">(link or download URL sent after purchase)</span></label>
                    <input type="url" id="delivery_url" name="delivery_url" class="form-input"
                           value="{delivery_url_val}" placeholder="https://your-tool.com/download">
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
                <label for="tags">Tags <span class="text-muted text-sm">(comma-separated, optional)</span></label>
                <input type="text" id="tags" name="tags" class="form-input"
                       value="{tags_val}" placeholder="e.g. open-source, freemium, API">
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:14px;">
                Submit for Review
            </button>
        </form>
    </div>
    """


@router.get("/submit", response_class=HTMLResponse)
async def submit_get(request: Request):
    db = request.state.db
    categories = await get_all_categories(db)
    body = submit_form(categories)
    return HTMLResponse(page_shell("Submit Your Tool", body))


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
):
    db = request.state.db
    categories = await get_all_categories(db)

    values = dict(name=name, tagline=tagline, url=url, description=description,
                  category_id=category_id, maker_name=maker_name, maker_url=maker_url,
                  tags=tags, price=price, delivery_type=delivery_type, delivery_url=delivery_url)

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
    if not category_id:
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
        return HTMLResponse(page_shell("Submit Your Tool", body))

    await create_tool(
        db, name=name.strip(), tagline=tagline.strip(), description=description.strip(),
        url=url.strip(), maker_name=maker_name.strip(), maker_url=maker_url.strip(),
        category_id=int(category_id), tags=tags.strip(),
        price_pence=price_pence, delivery_type=delivery_type,
        delivery_url=delivery_url.strip(),
    )

    body = submit_form(categories, success="Your tool has been submitted! We'll review it shortly.")
    return HTMLResponse(page_shell("Submit Your Tool", body))

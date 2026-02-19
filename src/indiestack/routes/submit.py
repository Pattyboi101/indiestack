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

    alert = ''
    if error:
        alert = f'<div class="alert alert-error">{escape(error)}</div>'
    if success:
        alert = f'<div class="alert alert-success">{escape(success)}</div>'

    cat_options = '<option value="">Select a category...</option>'
    for c in categories:
        sel = ' selected' if str(c['id']) == str(selected_cat) else ''
        cat_options += f'<option value="{c["id"]}"{sel}>{escape(str(c["name"]))}</option>'

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
):
    db = request.state.db
    categories = await get_all_categories(db)

    values = dict(name=name, tagline=tagline, url=url, description=description,
                  category_id=category_id, maker_name=maker_name, maker_url=maker_url, tags=tags)

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

    if errors:
        body = submit_form(categories, values, error=" ".join(errors))
        return HTMLResponse(page_shell("Submit Your Tool", body))

    await create_tool(
        db, name=name.strip(), tagline=tagline.strip(), description=description.strip(),
        url=url.strip(), maker_name=maker_name.strip(), maker_url=maker_url.strip(),
        category_id=int(category_id), tags=tags.strip(),
    )

    body = submit_form(categories, success="Your tool has been submitted! We'll review it shortly.")
    return HTMLResponse(page_shell("Submit Your Tool", body))

"""Admin dashboard — password-protected tool review + bulk import."""

import json
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.routes.components import page_shell
from indiestack.db import get_pending_tools, get_all_tools_admin, update_tool_status, toggle_verified, bulk_create_tools
from indiestack.auth import check_admin_session, make_session_token, ADMIN_PASSWORD

router = APIRouter()


def login_form_html(error: str = "") -> str:
    alert = f'<div class="alert alert-error">{escape(error)}</div>' if error else ''
    return f"""
    <div style="display:flex;justify-content:center;align-items:center;min-height:60vh;">
        <div class="card" style="max-width:400px;width:100%;">
            <h2 style="font-family:var(--font-display);font-size:24px;text-align:center;margin-bottom:24px;">
                Admin Login
            </h2>
            {alert}
            <form method="post" action="/admin">
                <div class="form-group">
                    <label for="password">Password</label>
                    <input type="password" id="password" name="password" class="form-input" required
                           placeholder="Enter admin password">
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;">
                    Sign In
                </button>
            </form>
        </div>
    </div>
    """


@router.get("/admin", response_class=HTMLResponse)
async def admin_get(request: Request):
    if not check_admin_session(request):
        return HTMLResponse(page_shell("Admin Login", login_form_html()))

    db = request.state.db
    pending = await get_pending_tools(db)
    all_tools = await get_all_tools_admin(db)

    # Pending section
    pending_count = len(pending)
    pending_html = f'<h2 style="font-family:var(--font-display);margin-bottom:16px;">Pending Review ({pending_count})</h2>'

    if pending:
        for t in pending:
            tid = t['id']
            name = escape(str(t['name']))
            tagline = escape(str(t['tagline']))
            t_url = escape(str(t['url']))
            maker = escape(str(t.get('maker_name', '')))
            cat = escape(str(t.get('category_name', '')))
            pending_html += f"""
            <div class="card" style="margin-bottom:12px;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
                    <div style="flex:1;min-width:200px;">
                        <strong style="font-size:16px;">{name}</strong>
                        <p class="text-muted text-sm" style="margin-top:4px;">{tagline}</p>
                        <p class="text-sm mt-2">
                            <a href="{t_url}" target="_blank" rel="noopener">{t_url}</a>
                        </p>
                        <p class="text-muted text-sm">Maker: {maker} &middot; Category: {cat}</p>
                    </div>
                    <div style="display:flex;gap:8px;">
                        <form method="post" action="/admin">
                            <input type="hidden" name="tool_id" value="{tid}">
                            <input type="hidden" name="action" value="approve">
                            <button type="submit" class="btn" style="background:#16a34a;color:white;padding:8px 16px;">
                                Approve
                            </button>
                        </form>
                        <form method="post" action="/admin">
                            <input type="hidden" name="tool_id" value="{tid}">
                            <input type="hidden" name="action" value="reject">
                            <button type="submit" class="btn" style="background:#dc2626;color:white;padding:8px 16px;">
                                Reject
                            </button>
                        </form>
                    </div>
                </div>
            </div>
            """
    else:
        pending_html += '<p class="text-muted">No tools pending review.</p>'

    # All tools table
    all_html = '<h2 style="font-family:var(--font-display);margin:40px 0 16px;">All Tools</h2>'
    if all_tools:
        status_styles = {
            'pending': 'background:#FEF3C7;color:#92400E;',
            'approved': 'background:#DCFCE7;color:#166534;',
            'rejected': 'background:#FEE2E2;color:#991B1B;',
        }
        rows = ''
        for t in all_tools:
            s = str(t.get('status', 'pending'))
            style = status_styles.get(s, '')
            is_v = bool(t.get('is_verified', 0))
            v_label = 'Unverify' if is_v else 'Verify'
            v_style = 'background:#FEF3C7;color:#92400E;border:1px solid #F59E0B;' if is_v else 'background:var(--stone-100);color:var(--stone-600);border:1px solid var(--stone-200);'
            v_badge = '<span style="display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;background:linear-gradient(135deg,#FEF3C7,#FDE68A);color:#D97706;border:1px solid #F59E0B;">Verified</span>' if is_v else ''
            rows += f"""
            <tr style="border-bottom:1px solid var(--stone-200);">
                <td style="padding:10px 12px;font-weight:600;">{escape(str(t['name']))} {v_badge}</td>
                <td style="padding:10px 12px;">
                    <span style="display:inline-block;padding:2px 10px;border-radius:999px;font-size:12px;
                                 font-weight:600;{style}">{escape(s)}</span>
                </td>
                <td style="padding:10px 12px;">{t.get('upvote_count', 0)}</td>
                <td style="padding:10px 12px;">{escape(str(t.get('category_name', '')))}</td>
                <td style="padding:10px 12px;">
                    <form method="post" action="/admin" style="margin:0;">
                        <input type="hidden" name="tool_id" value="{t['id']}">
                        <input type="hidden" name="action" value="toggle_verified">
                        <button type="submit" style="padding:4px 12px;border-radius:6px;font-size:12px;
                                font-weight:600;cursor:pointer;{v_style}">{v_label}</button>
                    </form>
                </td>
            </tr>
            """
        all_html += f"""
        <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:14px;">
                <thead>
                    <tr style="border-bottom:2px solid var(--stone-200);text-align:left;">
                        <th style="padding:10px 12px;">Name</th>
                        <th style="padding:10px 12px;">Status</th>
                        <th style="padding:10px 12px;">Upvotes</th>
                        <th style="padding:10px 12px;">Category</th>
                        <th style="padding:10px 12px;">Verified</th>
                    </tr>
                </thead>
                <tbody>{rows}</tbody>
            </table>
        </div>
        """
    else:
        all_html += '<p class="text-muted">No tools submitted yet.</p>'

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:900px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32px;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Admin Dashboard</h1>
            <a href="/admin/import" class="btn" style="background:var(--stone-100);color:var(--stone-700);border:1px solid var(--stone-300);">
                Bulk Import
            </a>
        </div>
        {pending_html}
        <hr style="margin:32px 0;border:none;border-top:1px solid var(--stone-200);">
        {all_html}
    </div>
    """
    return HTMLResponse(page_shell("Admin Dashboard", body))


@router.post("/admin")
async def admin_post(request: Request):
    form = await request.form()

    # Login
    if "password" in form:
        password = str(form["password"])
        if password == ADMIN_PASSWORD:
            token = make_session_token(password)
            response = RedirectResponse(url="/admin", status_code=303)
            response.set_cookie(key="indiestack_admin", value=token, httponly=True, samesite="lax")
            return response
        else:
            return HTMLResponse(page_shell("Admin Login", login_form_html("Invalid password.")))

    # Approve / Reject / Verify
    if "action" in form:
        if not check_admin_session(request):
            return RedirectResponse(url="/admin", status_code=303)
        tool_id = form.get("tool_id")
        action = str(form.get("action", ""))
        if tool_id and action in ("approve", "reject"):
            status = "approved" if action == "approve" else "rejected"
            await update_tool_status(request.state.db, int(tool_id), status)
        elif tool_id and action == "toggle_verified":
            await toggle_verified(request.state.db, int(tool_id))
        return RedirectResponse(url="/admin", status_code=303)

    return RedirectResponse(url="/admin", status_code=303)


# ── Bulk Import ──────────────────────────────────────────────────────────

IMPORT_EXAMPLE = """[
  {
    "name": "InvoiceOwl",
    "tagline": "Simple invoicing for freelancers",
    "description": "Generate professional invoices in seconds.",
    "url": "https://invoiceowl.example.com",
    "category": "Invoicing & Billing",
    "maker_name": "Jane Doe",
    "maker_url": "https://janedoe.dev",
    "tags": "invoicing, freelance, billing"
  }
]"""


def import_form_html(result: str = "") -> str:
    return f"""
    <div class="container" style="max-width:800px;padding:48px 24px;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:32px;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Bulk Import Tools</h1>
            <a href="/admin" class="btn" style="background:var(--stone-100);color:var(--stone-700);border:1px solid var(--stone-300);">
                &larr; Back to Admin
            </a>
        </div>
        <p class="text-muted" style="margin-bottom:24px;">
            Paste a JSON array of tools below. Each tool needs: <code>name</code>, <code>tagline</code>,
            <code>description</code>, <code>url</code>, <code>category</code> (must match an existing category name).
            Optional: <code>maker_name</code>, <code>maker_url</code>, <code>tags</code>.
            All imported tools are <strong>auto-approved</strong>.
        </p>
        {result}
        <form method="post" action="/admin/import">
            <div class="form-group">
                <label for="json_data">Tool Data (JSON array)</label>
                <textarea id="json_data" name="json_data" class="form-textarea"
                          style="min-height:400px;font-family:var(--font-mono);font-size:13px;"
                          placeholder='{escape(IMPORT_EXAMPLE)}'></textarea>
            </div>
            <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:14px;">
                Import Tools
            </button>
        </form>
    </div>
    """


@router.get("/admin/import", response_class=HTMLResponse)
async def admin_import_get(request: Request):
    if not check_admin_session(request):
        return RedirectResponse(url="/admin", status_code=303)
    return HTMLResponse(page_shell("Bulk Import", import_form_html()))


@router.post("/admin/import", response_class=HTMLResponse)
async def admin_import_post(request: Request):
    if not check_admin_session(request):
        return RedirectResponse(url="/admin", status_code=303)

    form = await request.form()
    json_data = str(form.get("json_data", "")).strip()

    if not json_data:
        result = '<div class="alert alert-error">Please paste some JSON data.</div>'
        return HTMLResponse(page_shell("Bulk Import", import_form_html(result)))

    try:
        tools_data = json.loads(json_data)
        if not isinstance(tools_data, list):
            raise ValueError("Expected a JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        result = f'<div class="alert alert-error">Invalid JSON: {escape(str(e))}</div>'
        return HTMLResponse(page_shell("Bulk Import", import_form_html(result)))

    created, errors = await bulk_create_tools(request.state.db, tools_data)

    parts = []
    if created:
        parts.append(f'<div class="alert alert-success">Successfully imported {created} tool{"s" if created != 1 else ""}!</div>')
    if errors:
        error_list = "".join(f"<li>{escape(e)}</li>" for e in errors)
        parts.append(f'<div class="alert alert-error"><strong>Errors:</strong><ul style="margin:8px 0 0 16px;">{error_list}</ul></div>')

    return HTMLResponse(page_shell("Bulk Import", import_form_html("".join(parts))))

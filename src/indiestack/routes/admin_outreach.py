"""Admin outreach helpers — email blasts, magic links, maker tracking, social kit."""

import os
from datetime import datetime
from html import escape
from urllib.parse import quote

from fastapi.responses import RedirectResponse, HTMLResponse

from indiestack.config import BASE_URL
from indiestack.db import (
    get_maker_activity_status,
    get_all_subscribers_with_dates,
    get_unclaimed_tools_for_outreach,
    create_magic_claim_token,
    get_recently_claimed_tools,
    get_top_tools_by_metric,
    get_outbound_click_count,
)
from indiestack.email import send_email, maker_stripe_nudge_html, marketplace_preview_html, tool_of_the_week_html, weekly_digest_html, launch_day_html, maker_launch_countdown_html

SMTP_FROM = os.environ.get("SMTP_FROM", "")


# ── Small helpers ─────────────────────────────────────────────────────────

def _days_ago_label(days):
    if days is None:
        return "Never"
    if days == 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    if days < 30:
        return f"{days}d ago"
    if days < 365:
        return f"{days // 30}mo ago"
    return f"{days // 365}y ago"


def _status_badge(status):
    if status == "active":
        return '<span style="display:inline-block;padding:2px 10px;border-radius:9999px;font-size:12px;font-weight:600;background:#DCFCE7;color:#16a34a;">Active</span>'
    if status == "idle":
        return '<span style="display:inline-block;padding:2px 10px;border-radius:9999px;font-size:12px;font-weight:600;background:#FEF3C7;color:#D97706;">Idle</span>'
    return '<span style="display:inline-block;padding:2px 10px;border-radius:9999px;font-size:12px;font-weight:600;background:#FEE2E2;color:#DC2626;">Dormant</span>'


def _freshness_badge(freshness):
    if freshness == "active":
        return '<span style="display:inline-block;padding:2px 10px;border-radius:9999px;font-size:12px;font-weight:600;background:#DCFCE7;color:#16a34a;">Active</span>'
    if freshness == "stale":
        return '<span style="display:inline-block;padding:2px 10px;border-radius:9999px;font-size:12px;font-weight:600;background:#FEF3C7;color:#D97706;">Stale</span>'
    if freshness == "inactive":
        return '<span style="display:inline-block;padding:2px 10px;border-radius:9999px;font-size:12px;font-weight:600;background:#FEE2E2;color:#DC2626;">Inactive</span>'
    return '<span style="display:inline-block;padding:2px 10px;border-radius:9999px;font-size:12px;font-weight:600;background:#F3F4F6;color:#6B7280;">Unknown</span>'


# ── Tool of the Week panel ────────────────────────────────────────────────

def _render_totw_panel(top_tools):
    """Render Tool of the Week panel with top 5 tools by clicks."""
    if not top_tools:
        return '''<div class="card" style="padding:20px;margin-bottom:24px;border-left:3px solid #00D4F5;">
            <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin:0 0 8px;">Tool of the Week</h3>
            <p style="color:var(--ink-muted);font-size:13px;margin:0;">No click data this week yet.</p>
        </div>'''

    rows = ""
    for t in top_tools:
        name = escape(str(t["name"]))
        slug = escape(str(t["slug"]))
        clicks = t.get("count", 0)
        maker_email = escape(str(t.get("maker_email") or "\u2014"))
        rows += f'''<tr style="border-bottom:1px solid var(--border);">
            <td style="padding:8px;font-size:13px;font-weight:600;">
                <a href="/tool/{slug}" style="color:#00D4F5;text-decoration:none;">{name}</a>
            </td>
            <td style="padding:8px;font-size:13px;text-align:center;font-weight:700;color:var(--ink);">{clicks}</td>
            <td style="padding:8px;font-size:13px;font-family:var(--font-mono);">{maker_email}</td>
            <td style="padding:8px;font-size:13px;">
                <form method="POST" action="/admin?tab=growth&section=email" style="display:inline;">
                    <input type="hidden" name="action" value="send_totw">
                    <input type="hidden" name="slug" value="{slug}">
                    <button type="submit"
                            onclick="return confirm('Send Tool of the Week email for {name}?')"
                            style="padding:4px 12px;font-size:12px;background:#00D4F5;color:#0D1B2A;border:none;border-radius:var(--radius-sm);font-weight:600;cursor:pointer;">
                        Send Winner Email
                    </button>
                </form>
            </td>
        </tr>'''

    return f'''<div class="card" style="padding:20px;margin-bottom:24px;border-left:3px solid #00D4F5;">
    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin:0 0 4px;">Tool of the Week</h3>
    <p style="color:var(--ink-muted);font-size:13px;margin:0 0 12px;">Top 5 tools by outbound clicks (last 7 days). Send a winner congrats email.</p>
    <div style="overflow-x:auto;">
    <table style="width:100%;border-collapse:collapse;">
        <thead>
            <tr style="border-bottom:2px solid var(--border);text-align:left;">
                <th style="padding:8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Tool</th>
                <th style="padding:8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;text-align:center;">Clicks</th>
                <th style="padding:8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Maker Email</th>
                <th style="padding:8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Action</th>
            </tr>
        </thead>
        <tbody>{rows}</tbody>
    </table>
    </div>
</div>'''


# ── Email Blast tab ──────────────────────────────────────────────────────

def _render_digest_panel(new_count, top_clicked_name, top_search, subscriber_count):
    """Render the Weekly Digest one-click card."""
    summary_parts = [f"{new_count} new tool{'s' if new_count != 1 else ''}"]
    if top_clicked_name:
        summary_parts.append(f"top clicked: {escape(top_clicked_name)}")
    if top_search:
        summary_parts.append(f"top search: {escape(top_search)}")
    summary = ", ".join(summary_parts)

    return f'''<div class="card" style="padding:20px;margin-bottom:24px;border-left:3px solid #00D4F5;">
    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin:0 0 4px;">Weekly Digest Newsletter</h3>
    <p style="color:var(--ink-muted);font-size:13px;margin:0 0 8px;">Auto-generated from DB data. Zero writing needed — one click to send.</p>
    <p style="font-size:13px;color:var(--ink);margin:0 0 12px;padding:8px 12px;background:var(--cream-dark);border-radius:var(--radius-sm);">
        <strong>This week&rsquo;s digest:</strong> {summary}
    </p>
    <div style="display:flex;gap:10px;">
        <form method="POST" action="/admin?tab=growth&section=email">
            <input type="hidden" name="action" value="send_digest_test">
            <button type="submit"
                    style="padding:8px 16px;background:var(--cream-dark);color:var(--ink);border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px;font-weight:600;cursor:pointer;">
                Send Test to Me
            </button>
        </form>
        <form method="POST" action="/admin?tab=growth&section=email">
            <input type="hidden" name="action" value="send_digest_all">
            <button type="submit"
                    onclick="return confirm(\'Send weekly digest to all {subscriber_count} subscribers?\')"
                    style="padding:8px 16px;background:#00D4F5;color:#0D1B2A;border:none;border-radius:var(--radius-sm);font-size:13px;font-weight:700;cursor:pointer;">
                Send to All {subscriber_count}
            </button>
        </form>
    </div>
</div>'''


def _render_launch_day_panel(subscriber_count, tool_count, maker_count):
    """Render the Launch Day Email one-click card."""
    return f'''<div class="card" style="padding:20px;margin-bottom:24px;border-left:3px solid #00D4F5;">
    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin:0 0 4px;">Launch Day Blast</h3>
    <p style="color:var(--ink-muted);font-size:13px;margin:0 0 8px;">March 2 launch email. {tool_count} tools, {maker_count} makers.</p>
    <div style="display:flex;gap:10px;">
        <form method="POST" action="/admin?tab=growth&section=email">
            <input type="hidden" name="action" value="send_launch_test">
            <button type="submit"
                    style="padding:8px 16px;background:var(--cream-dark);color:var(--ink);border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px;font-weight:600;cursor:pointer;">
                Send Test to Me
            </button>
        </form>
        <form method="POST" action="/admin?tab=growth&section=email">
            <input type="hidden" name="action" value="send_launch_all">
            <button type="submit"
                    onclick="return confirm(\'Send launch day email to all {subscriber_count} subscribers?\')"
                    style="padding:8px 16px;background:#00D4F5;color:#0D1B2A;border:none;border-radius:var(--radius-sm);font-size:13px;font-weight:700;cursor:pointer;">
                Send to All {subscriber_count}
            </button>
        </form>
    </div>
</div>'''


def _render_maker_countdown_panel(claimed_maker_count):
    """Render the Maker Launch Countdown email panel."""
    return f'''<div class="card" style="padding:20px;margin-bottom:24px;border-left:3px solid #E2B764;">
    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin:0 0 4px;">Maker Launch Countdown</h3>
    <p style="color:var(--ink-muted);font-size:13px;margin:0 0 8px;">Personalized email to claimed makers — connect Stripe before March 2. {claimed_maker_count} claimed makers.</p>
    <div style="display:flex;gap:10px;">
        <form method="POST" action="/admin?tab=growth&section=email">
            <input type="hidden" name="action" value="send_maker_countdown_test">
            <button type="submit"
                    style="padding:8px 16px;background:var(--cream-dark);color:var(--ink);border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px;font-weight:600;cursor:pointer;">
                Send Test to Me
            </button>
        </form>
        <form method="POST" action="/admin?tab=growth&section=email">
            <input type="hidden" name="action" value="send_maker_countdown_all">
            <button type="submit"
                    onclick="return confirm(\'Send countdown email to all {claimed_maker_count} claimed makers?\')"
                    style="padding:8px 16px;background:#00D4F5;color:#0D1B2A;border:none;border-radius:var(--radius-sm);font-size:13px;font-weight:700;cursor:pointer;">
                Send to All {claimed_maker_count} Makers
            </button>
        </form>
    </div>
</div>'''


def _render_email_tab(subscribers, result_html="", totw_html="", digest_html="", launch_day_html_panel="", maker_countdown_panel=""):
    count = len(subscribers)
    pill = f'<span style="display:inline-block;background:var(--terracotta);color:white;padding:3px 12px;border-radius:9999px;font-size:13px;font-weight:600;margin-bottom:16px;">{count} subscribers</span>'

    return f"""
{pill}
{result_html}
{totw_html}
{digest_html}
{launch_day_html_panel}
{maker_countdown_panel}
<div class="card" style="padding:20px;margin-bottom:24px;border-left:3px solid #00D4F5;">
    <h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin:0 0 8px;">Marketplace Preview Email</h3>
    <p style="color:var(--ink-muted);font-size:13px;margin:0 0 12px;">Auto-generated email featuring top priced tools. Subject: "Marketplace Opens Monday"</p>
    <div style="display:flex;gap:10px;">
        <form method="POST" action="/admin?tab=growth&section=email">
            <input type="hidden" name="action" value="send_preview">
            <input type="hidden" name="target" value="test">
            <button type="submit"
                    style="padding:8px 16px;background:var(--cream-dark);color:var(--ink);border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px;font-weight:600;cursor:pointer;">
                Send Test to Me
            </button>
        </form>
        <form method="POST" action="/admin?tab=growth&section=email">
            <input type="hidden" name="action" value="send_preview">
            <input type="hidden" name="target" value="all">
            <button type="submit"
                    onclick="return confirm('Send marketplace preview to all {count} subscribers?')"
                    style="padding:8px 16px;background:#00D4F5;color:#0D1B2A;border:none;border-radius:var(--radius-sm);font-size:13px;font-weight:700;cursor:pointer;">
                Send to All {count}
            </button>
        </form>
    </div>
</div>
<h3 style="font-family:var(--font-display);font-size:16px;color:var(--ink);margin:0 0 12px;">Custom Email</h3>
<form method="POST" action="/admin?tab=growth&section=email" style="display:flex;flex-direction:column;gap:16px;">
    <div>
        <label style="display:block;font-size:13px;font-weight:600;color:var(--ink);margin-bottom:4px;">Subject</label>
        <input type="text" name="subject" required
               style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:14px;font-family:var(--font-body);box-sizing:border-box;">
    </div>
    <div>
        <label style="display:block;font-size:13px;font-weight:600;color:var(--ink);margin-bottom:4px;">HTML Body</label>
        <textarea name="html_body" required rows="16"
                  style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px;font-family:var(--font-mono);line-height:1.5;box-sizing:border-box;resize:vertical;"></textarea>
    </div>
    <div style="display:flex;gap:10px;">
        <button type="submit" name="action" value="test_email"
                style="padding:10px 20px;background:var(--cream-dark);color:var(--ink);border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px;font-weight:600;cursor:pointer;">
            Send Test to Me
        </button>
        <button type="submit" name="action" value="blast_email"
                onclick="return confirm('Send to all {count} subscribers?')"
                style="padding:10px 20px;background:var(--terracotta);color:white;border:none;border-radius:var(--radius-sm);font-size:13px;font-weight:600;cursor:pointer;">
            Send to All {count} Subscribers
        </button>
    </div>
</form>
"""


# ── Magic Links tab ──────────────────────────────────────────────────────

def _render_magic_tab(tools, generated_links=None, csv_text=None, recently_claimed=None):
    if not tools:
        return '<div style="padding:32px;text-align:center;color:var(--ink-muted);font-size:15px;">All tools are claimed!</div>'

    generated_links = generated_links or {}

    claimed_section = ""
    if recently_claimed:
        claimed_rows = ""
        for c in recently_claimed:
            name = escape(str(c["name"]))
            maker = escape(str(c.get("maker_name") or ""))
            maker_slug = escape(str(c.get("maker_slug") or ""))
            email = escape(str(c.get("maker_email") or ""))
            claimed_at = c.get("claimed_at", "")[:10] if c.get("claimed_at") else "—"
            maker_link = f'<a href="/maker/{maker_slug}" style="color:var(--terracotta);text-decoration:none;font-weight:600;">{maker}</a>' if maker_slug else maker
            email_display = email or "—"
            claimed_rows += f'''<tr style="border-bottom:1px solid var(--border);">
                <td style="padding:8px;font-size:13px;font-weight:600;">{name}</td>
                <td style="padding:8px;font-size:13px;">{maker_link}</td>
                <td style="padding:8px;font-size:13px;font-family:var(--font-mono);">{email_display}</td>
                <td style="padding:8px;font-size:13px;">{claimed_at}</td>
            </tr>'''
        claimed_section = f'''
        <div style="margin-bottom:32px;">
            <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin:0 0 4px;">Recently Claimed</h3>
            <p style="font-size:13px;color:var(--ink-muted);margin:0 0 12px;">Tools claimed by makers — your outreach is working!</p>
            <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;">
                <thead>
                    <tr style="border-bottom:2px solid var(--border);text-align:left;">
                        <th style="padding:8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Tool</th>
                        <th style="padding:8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Maker</th>
                        <th style="padding:8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Email</th>
                        <th style="padding:8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Claimed</th>
                    </tr>
                </thead>
                <tbody>{claimed_rows}</tbody>
            </table>
            </div>
        </div>
        <hr style="border:none;border-top:1px solid var(--border);margin:24px 0;">
        '''

    rows = ""
    for t in tools:
        tid = t["id"]
        name = escape(str(t["name"]))
        maker = escape(str(t["maker_name"] or ""))
        maker_url = escape(str(t["maker_url"] or ""))
        maker_link = f'<a href="{maker_url}" target="_blank" style="color:var(--terracotta);text-decoration:underline;">{maker_url}</a>' if maker_url else "--"

        if tid in generated_links:
            link = generated_links[tid]
            link_cell = f'<input type="text" value="{escape(link)}" readonly style="width:260px;padding:4px 8px;font-size:12px;font-family:var(--font-mono);border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--cream-dark);">'
            copy_cell = f'<button onclick="navigator.clipboard.writeText(\'{escape(link)}\')" style="padding:4px 10px;font-size:12px;background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius-sm);cursor:pointer;">Copy</button>'
        else:
            link_cell = f"""<form method="POST" action="/admin?tab=growth&section=email" style="display:inline;">
                <input type="hidden" name="action" value="generate_magic">
                <input type="hidden" name="tool_id" value="{tid}">
                <button type="submit" style="padding:4px 12px;font-size:12px;background:var(--terracotta);color:white;border:none;border-radius:var(--radius-sm);cursor:pointer;">Generate Link</button>
            </form>"""
            copy_cell = ""

        rows += f"""<tr style="border-bottom:1px solid var(--border);">
            <td style="padding:10px 8px;font-size:13px;font-weight:600;">{name}</td>
            <td style="padding:10px 8px;font-size:13px;">{maker}</td>
            <td style="padding:10px 8px;font-size:13px;">{maker_link}</td>
            <td style="padding:10px 8px;font-size:13px;">{link_cell}</td>
            <td style="padding:10px 8px;font-size:13px;">{copy_cell}</td>
        </tr>"""

    csv_section = ""
    if csv_text is not None:
        csv_section = f"""
        <div style="margin-top:20px;">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px;">
                <label style="font-size:13px;font-weight:600;color:var(--ink);">CSV Output (tool_name, maker_url, magic_link)</label>
                <button onclick="navigator.clipboard.writeText(document.getElementById('csv-output').value).then(()=>{{this.textContent='Copied!';setTimeout(()=>this.textContent='Copy CSV',2000)}})" style="padding:4px 12px;font-size:12px;background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius-sm);cursor:pointer;">Copy CSV</button>
            </div>
            <textarea id="csv-output" readonly rows="10" style="width:100%;padding:10px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:12px;font-family:var(--font-mono);box-sizing:border-box;resize:vertical;">{escape(csv_text)}</textarea>
        </div>"""

    return f"""
{claimed_section}
<div style="margin-bottom:16px;display:flex;gap:10px;align-items:center;">
    <form method="POST" action="/admin?tab=growth&section=email" style="display:inline;">
        <button type="submit" name="action" value="generate_all_csv" style="padding:8px 16px;font-size:13px;font-weight:600;background:var(--terracotta);color:white;border:none;border-radius:var(--radius-sm);cursor:pointer;">
            Generate All Magic Links
        </button>
    </form>
    <span id="csv-count" style="font-size:13px;color:var(--ink-muted);">{len(tools)} unclaimed tools</span>
</div>
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;">
    <thead>
        <tr style="border-bottom:2px solid var(--border);text-align:left;">
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Tool Name</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Maker Name</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Maker URL</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Magic Link</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Copy</th>
        </tr>
    </thead>
    <tbody>{rows}</tbody>
</table>
</div>
{csv_section}
"""


# ── Maker Tracker tab ────────────────────────────────────────────────────

def _render_makers_tab(makers, needs_stripe_ids=None):
    active = sum(1 for m in makers if m["status"] == "active")
    idle = sum(1 for m in makers if m["status"] == "idle")
    dormant = sum(1 for m in makers if m["status"] == "dormant")

    pills = f"""<div style="display:flex;gap:10px;margin-bottom:20px;">
        <span style="padding:4px 14px;border-radius:9999px;font-size:13px;font-weight:600;background:#DCFCE7;color:#16a34a;">{active} Active</span>
        <span style="padding:4px 14px;border-radius:9999px;font-size:13px;font-weight:600;background:#FEF3C7;color:#D97706;">{idle} Idle</span>
        <span style="padding:4px 14px;border-radius:9999px;font-size:13px;font-weight:600;background:#FEE2E2;color:#DC2626;">{dormant} Dormant</span>
    </div>"""

    needs_stripe_ids = needs_stripe_ids or set()
    sorted_makers = sorted(makers, key=lambda m: m.get("days_inactive") or 0, reverse=True)

    rows = ""
    for m in sorted_makers:
        name = escape(str(m["name"] or ""))
        slug = escape(str(m.get("slug") or ""))
        maker_id = m.get("id", "")
        tools = m.get("tool_count", 0)
        days = m.get("days_inactive")
        last = _days_ago_label(days)
        email = escape(str(m.get("email") or ""))
        status = m.get("status", "dormant")
        badge = _status_badge(status)

        name_link = f'<a href="/maker/{slug}" style="color:var(--terracotta);text-decoration:none;font-weight:600;">{name}</a>' if slug else name

        nudge = ""
        if email:
            nudge = f'''<form method="POST" action="/admin?tab=people" style="display:inline;">
                <input type="hidden" name="maker_email" value="{email}">
                <input type="hidden" name="maker_name" value="{name}">
                <button type="submit" name="action" value="send_nudge"
                    onclick="return confirm('Send nudge email to {name}?')"
                    style="padding:4px 10px;font-size:12px;background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--ink);cursor:pointer;">
                    Send Nudge
                </button>
            </form>'''
        if maker_id in needs_stripe_ids and email:
            nudge += f''' <form method="POST" action="/admin" style="display:inline;"
                    onsubmit="return confirm('Send Stripe Connect nudge to {name}?')">
                <input type="hidden" name="action" value="send_stripe_nudge">
                <input type="hidden" name="maker_id" value="{maker_id}">
                <button type="submit" class="btn btn-sm" style="background:#00D4F5;color:#1A2D4A;font-size:12px;padding:4px 10px;">
                    Stripe Nudge
                </button>
            </form>'''

        rows += f"""<tr style="border-bottom:1px solid var(--border);">
            <td style="padding:10px 8px;font-size:13px;">{name_link}</td>
            <td style="padding:10px 8px;font-size:13px;text-align:center;">{tools}</td>
            <td style="padding:10px 8px;font-size:13px;">{last}</td>
            <td style="padding:10px 8px;font-size:13px;text-align:center;">{days if days is not None else '--'}</td>
            <td style="padding:10px 8px;font-size:13px;font-family:var(--font-mono);">{email or '--'}</td>
            <td style="padding:10px 8px;font-size:13px;">{badge}</td>
            <td style="padding:10px 8px;font-size:13px;">{nudge}</td>
        </tr>"""

    return f"""
{pills}
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;">
    <thead>
        <tr style="border-bottom:2px solid var(--border);text-align:left;">
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Name</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;text-align:center;">Tools</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Last Update</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;text-align:center;">Days Inactive</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Email</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Status</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Nudge</th>
        </tr>
    </thead>
    <tbody>{rows}</tbody>
</table>
</div>
"""


# ── Stale Tools tab ──────────────────────────────────────────────────────

def _render_stale_tab(stale_tools, counts):
    stale_count = counts.get("stale", 0)
    inactive_count = counts.get("inactive", 0)
    active_count = counts.get("active", 0)
    unknown_count = counts.get("unknown", 0)
    no_github = counts.get("no_github", 0)

    pills = f"""<div style="display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;">
        <span style="padding:4px 14px;border-radius:9999px;font-size:13px;font-weight:600;background:#DCFCE7;color:#16a34a;">{active_count} Active</span>
        <span style="padding:4px 14px;border-radius:9999px;font-size:13px;font-weight:600;background:#FEF3C7;color:#D97706;">{stale_count} Stale</span>
        <span style="padding:4px 14px;border-radius:9999px;font-size:13px;font-weight:600;background:#FEE2E2;color:#DC2626;">{inactive_count} Inactive</span>
        <span style="padding:4px 14px;border-radius:9999px;font-size:13px;font-weight:600;background:#F3F4F6;color:#6B7280;">{unknown_count} Unknown &middot; {no_github} No GitHub</span>
    </div>"""

    if not stale_tools:
        return pills + '''<div style="text-align:center;padding:40px 20px;color:var(--ink-muted);">
            <p style="font-size:16px;margin-bottom:8px;">No stale or inactive tools found.</p>
            <p style="font-size:13px;">Run the freshness checker to scan GitHub repos.</p>
        </div>'''

    rows = ""
    for t in stale_tools:
        name = escape(str(t["name"]))
        slug = escape(str(t["slug"]))
        github_url = escape(str(t.get("github_url") or ""))
        freshness = t.get("github_freshness", "unknown")
        last_commit = t.get("last_github_commit") or ""
        maker_email = escape(str(t.get("maker_email") or ""))

        commit_display = ""
        if last_commit:
            try:
                dt = datetime.fromisoformat(last_commit)
                days_ago = (datetime.utcnow() - dt).days
                commit_display = f'{dt.strftime("%Y-%m-%d")} ({days_ago}d ago)'
            except (ValueError, TypeError):
                commit_display = last_commit

        rows += f"""<tr style="border-bottom:1px solid var(--border);">
            <td style="padding:10px 8px;font-size:13px;font-weight:600;">
                <a href="/tool/{slug}" style="color:#00D4F5;text-decoration:none;">{name}</a>
            </td>
            <td style="padding:10px 8px;font-size:13px;">
                {'<a href="' + github_url + '" target="_blank" style="color:var(--ink-muted);text-decoration:none;font-family:var(--font-mono);font-size:12px;">' + github_url.replace("https://github.com/", "") + '</a>' if github_url else ''}
            </td>
            <td style="padding:10px 8px;font-size:13px;">{commit_display or '&mdash;'}</td>
            <td style="padding:10px 8px;font-size:13px;">{_freshness_badge(freshness)}</td>
            <td style="padding:10px 8px;font-size:13px;font-family:var(--font-mono);">{maker_email or '&mdash;'}</td>
        </tr>"""

    instructions = '''<div style="margin-top:24px;padding:16px;background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius-sm);">
        <h4 style="font-family:var(--font-display);font-size:14px;color:var(--ink);margin:0 0 8px;">Run Freshness Check</h4>
        <p style="font-size:13px;color:var(--ink-muted);margin:0 0 8px;">SSH into the server and run the checker script:</p>
        <code style="display:block;padding:10px;background:#1A2D4A;color:#00D4F5;border-radius:6px;font-size:13px;font-family:var(--font-mono);overflow-x:auto;">flyctl ssh console -a indiestack -C "python3 scripts/check_tool_freshness.py"</code>
        <p style="font-size:12px;color:var(--ink-muted);margin:8px 0 0;">Set GITHUB_TOKEN env var on Fly for higher API rate limits (5000 req/hr vs 60).</p>
    </div>'''

    return f"""{pills}
<div style="overflow-x:auto;">
<table style="width:100%;border-collapse:collapse;">
    <thead>
        <tr style="border-bottom:2px solid var(--border);text-align:left;">
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Tool</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">GitHub Repo</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Last Commit</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Status</th>
            <th style="padding:10px 8px;font-size:12px;font-weight:600;color:var(--ink-muted);text-transform:uppercase;">Maker Email</th>
        </tr>
    </thead>
    <tbody>{rows}</tbody>
</table>
</div>
{instructions}
"""


# ── Social Kit tab ────────────────────────────────────────────────────────

def _social_card(card_id, title, text, include_tweet=False):
    """Render a single social kit card with copy button and optional tweet link."""
    escaped_text = escape(text)
    tweet_btn = ""
    if include_tweet:
        tweet_url = f"https://twitter.com/intent/tweet?text={quote(text)}"
        tweet_btn = f'''<a href="{tweet_url}" target="_blank"
            style="display:inline-block;padding:8px 16px;background:#1DA1F2;color:white;border:none;border-radius:var(--radius-sm);font-size:13px;font-weight:600;text-decoration:none;cursor:pointer;">
            Tweet
        </a>'''
    return f'''<div style="background:white;border:1px solid var(--border);border-radius:var(--radius);padding:20px;margin-bottom:16px;">
    <h3 style="font-family:var(--font-display);font-size:15px;color:var(--ink);margin:0 0 10px;">{escape(title)}</h3>
    <div id="{card_id}" style="white-space:pre-wrap;font-size:13px;background:var(--cream-dark);padding:12px;border-radius:var(--radius-sm);margin-bottom:12px;line-height:1.5;">{escaped_text}</div>
    <div style="display:flex;gap:8px;">
        <button onclick="navigator.clipboard.writeText(document.getElementById('{card_id}').innerText).then(()=>this.textContent='Copied!')"
            style="padding:8px 16px;background:var(--cream-dark);color:var(--ink);border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px;font-weight:600;cursor:pointer;">
            Copy
        </button>
        {tweet_btn}
    </div>
</div>'''


def _render_social_kit(totw, new_tools, tool_count, maker_count):
    """Render the Social Kit section with pre-written posts."""
    cards = ""

    # Card 1: TOTW Tweet
    if totw:
        totw_text = (
            f"\U0001f3c6 This week's Tool of the Week on IndieStack: {totw['name']} \u2014 {totw['tagline']}\n\n"
            f"{tool_count}+ indie tools, all searchable by AI coding assistants.\n\n"
            f"{BASE_URL}/tool/{totw['slug']}"
        )
        cards += _social_card("social-totw", "Tool of the Week Tweet", totw_text, include_tweet=True)

    # Card 2: New This Week Tweet
    if new_tools:
        bullet_list = "\n".join(f"\u2022 {t['name']}" for t in new_tools)
        new_text = (
            f"{len(new_tools)} new indie tools on IndieStack this week:\n\n"
            f"{bullet_list}\n\n"
            f"All discoverable by AI coding assistants via our MCP server \U0001f916\n\n"
            f"{BASE_URL}/new"
        )
        cards += _social_card("social-new", "New This Week Tweet", new_text, include_tweet=True)

    # Card 3: Launch Thread
    launch_text = (
        f"\U0001f680 IndieStack Marketplace is LIVE\n\n"
        f"{tool_count} indie tools. {maker_count} makers. Zero big-tech gatekeepers.\n\n"
        f"Every tool is searchable by AI coding assistants (Cursor, Windsurf, Claude Code) through our MCP server.\n\n"
        f"0% commission for launch week (March 2-16).\n\n"
        f"List your tool free \u2192 {BASE_URL}/submit"
    )
    cards += _social_card("social-launch", "Launch Thread (March 2nd)", launch_text, include_tweet=True)

    # Card 4: Reddit Post
    reddit_text = (
        f"Title: IndieStack Marketplace \u2014 {tool_count} indie tools discoverable by AI coding assistants\n\n"
        f"Body: We built IndieStack as a directory of indie SaaS tools, but with a twist: "
        f"every tool listed is instantly searchable by AI coding assistants (Cursor, Windsurf, Claude Code) "
        f"through our MCP server.\n\n"
        f"{tool_count} tools from {maker_count} independent makers. Categories from analytics to authentication to email marketing.\n\n"
        f"The marketplace launches March 2nd with 0% commission for the first two weeks.\n\n"
        f"If you've built something, list it free: {BASE_URL}/submit"
    )
    cards += _social_card("social-reddit", "Reddit Post", reddit_text, include_tweet=False)

    return f"""
<div>
    <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin:0 0 4px;">Social Kit</h2>
    <p style="color:var(--ink-muted);font-size:14px;margin:0 0 20px;">Pre-written posts for Twitter and Reddit. Copy and go.</p>
    {cards}
</div>
"""


# ── Public async section renderers ────────────────────────────────────────

async def render_email_section(db, request) -> str:
    """Render the full email blast section with all panels."""
    subscribers = await get_all_subscribers_with_dates(db)
    toast = request.query_params.get("toast", "")
    result_html = ""
    if toast:
        result_html = f'<div style="padding:12px 16px;background:#DCFCE7;color:#16a34a;border-radius:var(--radius-sm);margin-bottom:16px;font-size:14px;font-weight:600;">{escape(toast)}</div>'
    # Tool of the Week data
    top_tools = await get_top_tools_by_metric(db, metric='clicks', days=7, limit=5)
    for t in top_tools:
        cursor = await db.execute(
            "SELECT u.email FROM tools tl JOIN makers m ON tl.maker_id = m.id JOIN users u ON u.maker_id = m.id WHERE tl.slug = ?",
            (t["slug"],),
        )
        row = await cursor.fetchone()
        t["maker_email"] = row["email"] if row else None
    totw_html = _render_totw_panel(top_tools)
    # Weekly Digest data
    cursor = await db.execute(
        "SELECT name, slug, tagline FROM tools WHERE status='approved' AND created_at > datetime('now', '-7 days') ORDER BY created_at DESC LIMIT 5"
    )
    digest_new_tools = [dict(r) for r in await cursor.fetchall()]
    cursor = await db.execute(
        "SELECT query, COUNT(*) as cnt FROM search_logs WHERE created_at > datetime('now', '-7 days') GROUP BY query ORDER BY cnt DESC LIMIT 5"
    )
    digest_top_searches = [r["query"] for r in await cursor.fetchall()]
    digest_top_clicked_name = top_tools[0]["name"] if top_tools else ""
    digest_html = _render_digest_panel(
        new_count=len(digest_new_tools),
        top_clicked_name=digest_top_clicked_name,
        top_search=digest_top_searches[0] if digest_top_searches else "",
        subscriber_count=len(subscribers),
    )
    # Launch Day panel data
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")
    launch_tool_count = (await cursor.fetchone())["cnt"]
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM makers")
    launch_maker_count = (await cursor.fetchone())["cnt"]
    launch_panel = _render_launch_day_panel(len(subscribers), launch_tool_count, launch_maker_count)
    # Maker countdown panel
    _cm = await db.execute("SELECT COUNT(DISTINCT m.id) as cnt FROM makers m JOIN users u ON u.maker_id = m.id")
    claimed_maker_count = (await _cm.fetchone())["cnt"]
    countdown_panel = _render_maker_countdown_panel(claimed_maker_count)
    return _render_email_tab(subscribers, result_html, totw_html=totw_html, digest_html=digest_html, launch_day_html_panel=launch_panel, maker_countdown_panel=countdown_panel)


async def render_magic_section(db) -> str:
    """Render the magic links section."""
    tools = await get_unclaimed_tools_for_outreach(db)
    claimed = await get_recently_claimed_tools(db)
    return _render_magic_tab(tools, recently_claimed=claimed)


async def render_makers_section(db, request) -> str:
    """Render the maker tracker section with readiness KPIs."""
    makers = await get_maker_activity_status(db)
    # Find makers who have priced tools but no Stripe connected
    cursor = await db.execute(
        "SELECT DISTINCT maker_id FROM tools WHERE price_pence > 0 AND (stripe_account_id IS NULL OR stripe_account_id = '')"
    )
    needs_stripe_ids = {r["maker_id"] for r in await cursor.fetchall()}
    toast = request.query_params.get("toast", "")
    toast_html = ""
    if toast:
        toast_html = f'<div style="padding:12px 16px;background:#DCFCE7;color:#16a34a;border-radius:var(--radius-sm);margin-bottom:16px;font-size:14px;font-weight:600;">{escape(toast)}</div>'
    # Maker readiness KPIs
    _c1 = await db.execute("SELECT COUNT(DISTINCT m.id) as cnt FROM makers m JOIN users u ON u.maker_id = m.id")
    total_claimed = (await _c1.fetchone())["cnt"]
    _c2 = await db.execute("SELECT COUNT(DISTINCT m.id) as cnt FROM makers m JOIN users u ON u.maker_id = m.id WHERE m.stripe_account_id IS NOT NULL AND m.stripe_account_id != ''")
    stripe_count = (await _c2.fetchone())["cnt"]
    _c3 = await db.execute("SELECT COUNT(DISTINCT t.maker_id) as cnt FROM tools t JOIN users u ON u.maker_id = t.maker_id WHERE t.price_pence > 0")
    priced_count = (await _c3.fetchone())["cnt"]
    _c4 = await db.execute("SELECT COUNT(DISTINCT m.id) as cnt FROM makers m JOIN users u ON u.maker_id = m.id JOIN tools t ON t.maker_id = m.id WHERE m.stripe_account_id IS NOT NULL AND m.stripe_account_id != '' AND t.price_pence > 0")
    ready_count = (await _c4.fetchone())["cnt"]
    def _kpi(label, value, color="var(--terracotta)"):
        return f'<div class="card" style="text-align:center;padding:16px;"><div style="color:var(--ink-muted);font-size:13px;">{label}</div><div style="font-family:var(--font-display);font-size:26px;margin-top:4px;color:{color};">{value}</div></div>'
    readiness_html = f'''<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px;">
        {_kpi("Claimed Makers", str(total_claimed))}
        {_kpi("Stripe Connected", f"{stripe_count}/{total_claimed}", "#10B981" if stripe_count > 0 else "#DC2626")}
        {_kpi("Have Pricing", f"{priced_count}/{total_claimed}", "#10B981" if priced_count > 0 else "#D97706")}
        {_kpi("Ready to Sell", f"{ready_count}/{total_claimed}", "#10B981" if ready_count > 0 else "#DC2626")}
    </div>'''
    return toast_html + readiness_html + _render_makers_tab(makers, needs_stripe_ids=needs_stripe_ids)


async def render_stale_section(db) -> str:
    """Render the stale tools section."""
    counts = {}
    for status_val in ("active", "stale", "inactive", "unknown"):
        cursor = await db.execute(
            "SELECT COUNT(*) as cnt FROM tools WHERE status='approved' AND github_freshness = ?",
            (status_val,),
        )
        counts[status_val] = (await cursor.fetchone())["cnt"]
    cursor = await db.execute(
        "SELECT COUNT(*) as cnt FROM tools WHERE status='approved' AND (github_url IS NULL OR github_url = '')"
    )
    counts["no_github"] = (await cursor.fetchone())["cnt"]
    # Stale + inactive tools with maker email
    cursor = await db.execute(
        """SELECT t.name, t.slug, t.github_url, t.github_freshness, t.last_github_commit,
                  u.email as maker_email
           FROM tools t
           LEFT JOIN makers m ON t.maker_id = m.id
           LEFT JOIN users u ON u.maker_id = m.id
           WHERE t.status = 'approved'
             AND t.github_freshness IN ('stale', 'inactive')
           ORDER BY t.last_github_commit ASC"""
    )
    stale_tools = [dict(r) for r in await cursor.fetchall()]
    return _render_stale_tab(stale_tools, counts)


async def render_social_section(db) -> str:
    """Render the social kit section."""
    # Tool of the Week
    cursor = await db.execute("SELECT name, slug, tagline FROM tools WHERE tool_of_the_week = 1 LIMIT 1")
    totw_row = await cursor.fetchone()
    totw = dict(totw_row) if totw_row else None
    # New tools this week
    cursor = await db.execute(
        "SELECT name, slug FROM tools WHERE created_at >= datetime('now', '-7 days') AND status = 'approved' ORDER BY created_at DESC LIMIT 5"
    )
    new_tools = [dict(r) for r in await cursor.fetchall()]
    # Total tool count
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status = 'approved'")
    social_tool_count = (await cursor.fetchone())["cnt"]
    # Total maker count
    cursor = await db.execute("SELECT COUNT(*) as cnt FROM makers")
    social_maker_count = (await cursor.fetchone())["cnt"]
    return _render_social_kit(totw, new_tools, social_tool_count, social_maker_count)


# ── POST action handler ──────────────────────────────────────────────────

async def handle_outreach_post(db, form, request) -> RedirectResponse:
    """Handle all outreach POST actions. Returns a RedirectResponse."""
    action = form.get("action", "")

    def _unsub_url(token):
        return f"{BASE_URL}/unsubscribe/{token}" if token else ""

    # ── Email actions ────────────────────────────────────────────────────
    if action == "test_email":
        subject = form.get("subject", "")
        html_body = form.get("html_body", "")
        smtp_from = os.environ.get("SMTP_FROM", "")
        if not smtp_from:
            toast = "SMTP_FROM not configured"
        else:
            ok = await send_email(smtp_from, subject, html_body)
            toast = "Test email sent!" if ok else "Test email failed"
        return RedirectResponse(url=f"/admin?tab=growth&section=email&toast={toast}", status_code=303)

    if action == "blast_email":
        subject = form.get("subject", "")
        html_body = form.get("html_body", "")
        subscribers = await get_all_subscribers_with_dates(db)
        success = 0
        fail = 0
        for sub in subscribers:
            ok = await send_email(sub["email"], subject, html_body, unsubscribe_url=_unsub_url(sub.get("unsubscribe_token")))
            if ok:
                success += 1
            else:
                fail += 1
        toast = f"Sent: {success} success, {fail} failed"
        return RedirectResponse(url=f"/admin?tab=growth&section=email&toast={toast}", status_code=303)

    # ── Marketplace preview blast ────────────────────────────────────────
    if action == "send_preview":
        cursor = await db.execute("""
            SELECT t.name, t.slug, t.tagline, t.price_pence, m.name as maker_name
            FROM tools t JOIN makers m ON t.maker_id = m.id
            WHERE t.price_pence > 0 AND t.status = 'approved'
            ORDER BY t.upvote_count DESC LIMIT 5
        """)
        tools = [dict(r) for r in await cursor.fetchall()]
        if not tools:
            cursor = await db.execute("""
                SELECT t.name, t.slug, t.tagline, t.price_pence, m.name as maker_name
                FROM tools t JOIN makers m ON t.maker_id = m.id
                JOIN users u ON u.maker_id = m.id
                WHERE t.status = 'approved'
                ORDER BY t.upvote_count DESC LIMIT 5
            """)
            tools = [dict(r) for r in await cursor.fetchall()]
        subject = "Marketplace Opens Monday \u2014 Here's What's Coming"
        target = form.get("target", "all")
        if target == "test":
            smtp_from = os.environ.get("SMTP_FROM", "")
            html_body = marketplace_preview_html(tools)
            ok = await send_email(smtp_from, subject, html_body)
            toast = "Preview test sent!" if ok else "Preview test failed"
        else:
            subscribers = await get_all_subscribers_with_dates(db)
            success = fail = 0
            for sub in subscribers:
                unsub = _unsub_url(sub.get("unsubscribe_token"))
                html_body = marketplace_preview_html(tools, unsubscribe_url=unsub)
                ok = await send_email(sub["email"], subject, html_body, unsubscribe_url=unsub)
                if ok:
                    success += 1
                else:
                    fail += 1
            toast = f"Preview sent: {success} success, {fail} failed"
        return RedirectResponse(url=f"/admin?tab=growth&section=email&toast={toast}", status_code=303)

    # ── Tool of the Week winner email ──────────────────────────────────────
    if action == "send_totw":
        slug = form.get("slug", "")
        if not slug:
            return RedirectResponse(url="/admin?tab=growth&section=email&toast=No+tool+slug+provided", status_code=303)
        cursor = await db.execute(
            "SELECT t.id, t.name, t.slug, m.name as maker_name, m.id as maker_id FROM tools t JOIN makers m ON t.maker_id = m.id WHERE t.slug = ?",
            (slug,),
        )
        tool_row = await cursor.fetchone()
        if not tool_row:
            return RedirectResponse(url="/admin?tab=growth&section=email&toast=Tool+not+found", status_code=303)
        tool_row = dict(tool_row)
        cursor = await db.execute("SELECT u.email FROM users u WHERE u.maker_id = ?", (tool_row["maker_id"],))
        email_row = await cursor.fetchone()
        maker_email = email_row["email"] if email_row else ""
        if not maker_email:
            return RedirectResponse(url="/admin?tab=growth&section=email&toast=No+email+for+this+maker", status_code=303)
        clicks = await get_outbound_click_count(db, tool_row["id"], days=7)
        badge_url = f"{BASE_URL}/api/badge/{slug}.svg?style=winner"
        tool_url = f"{BASE_URL}/tool/{slug}"
        html_body = tool_of_the_week_html(
            maker_name=tool_row["maker_name"],
            tool_name=tool_row["name"],
            tool_slug=slug,
            clicks=clicks,
            badge_url=badge_url,
            tool_url=tool_url,
        )
        subj = f"Congrats! {tool_row['name']} is IndieStack's Tool of the Week"
        ok = await send_email(maker_email, subj, html_body)
        maker_name_enc = escape(tool_row["maker_name"]).replace(" ", "+")
        toast = f"Winner+email+sent+to+{maker_name_enc}" if ok else "Failed+to+send+winner+email"
        return RedirectResponse(url=f"/admin?tab=growth&section=email&toast={toast}", status_code=303)

    # ── Weekly Digest ─────────────────────────────────────────────────────
    if action in ("send_digest_test", "send_digest_all"):
        from datetime import timedelta
        now = datetime.utcnow()
        week_start = now - timedelta(days=7)
        week_label = f"{week_start.strftime('%b %d')} \u2013 {now.strftime('%b %d, %Y')}"

        cursor = await db.execute(
            "SELECT name, slug, tagline FROM tools WHERE status='approved' AND created_at > datetime('now', '-7 days') ORDER BY created_at DESC LIMIT 5"
        )
        new_tools = [dict(r) for r in await cursor.fetchall()]

        top_clicked_raw = await get_top_tools_by_metric(db, metric='clicks', days=7, limit=5)
        top_clicked = [{"name": t["name"], "slug": t["slug"], "clicks": t.get("count", 0)} for t in top_clicked_raw]

        cursor = await db.execute(
            "SELECT query, COUNT(*) as cnt FROM search_logs WHERE created_at > datetime('now', '-7 days') GROUP BY query ORDER BY cnt DESC LIMIT 5"
        )
        top_searched = [r["query"] for r in await cursor.fetchall()]

        totw_name = top_clicked[0]["name"] if top_clicked else None
        totw_slug = top_clicked[0]["slug"] if top_clicked else None
        totw_clicks = top_clicked[0]["clicks"] if top_clicked else 0

        cursor = await db.execute("SELECT COUNT(*) FROM tools WHERE status='approved'")
        total_tools = (await cursor.fetchone())[0]
        cursor = await db.execute("SELECT COUNT(*) FROM makers")
        total_makers = (await cursor.fetchone())[0]
        subscribers = await get_all_subscribers_with_dates(db)
        subscriber_count = len(subscribers)

        _digest_kwargs = dict(
            week_label=week_label,
            new_tools=new_tools,
            top_clicked=top_clicked,
            top_searched=top_searched,
            totw_name=totw_name,
            totw_slug=totw_slug,
            totw_clicks=totw_clicks,
            total_tools=total_tools,
            total_makers=total_makers,
            subscriber_count=subscriber_count,
        )
        subject = f"IndieStack Weekly \u2014 {week_label}"

        if action == "send_digest_test":
            smtp_from = os.environ.get("SMTP_FROM", "")
            if not smtp_from:
                toast = "SMTP_FROM not configured"
            else:
                html_body = weekly_digest_html(**_digest_kwargs)
                ok = await send_email(smtp_from, subject, html_body)
                toast = "Digest test sent!" if ok else "Digest test failed"
        else:
            success = fail = 0
            for sub in subscribers:
                unsub = _unsub_url(sub.get("unsubscribe_token"))
                html_body = weekly_digest_html(**_digest_kwargs, unsubscribe_url=unsub)
                ok = await send_email(sub["email"], subject, html_body, unsubscribe_url=unsub)
                if ok:
                    success += 1
                else:
                    fail += 1
            toast = f"Digest sent: {success} success, {fail} failed"
        return RedirectResponse(url=f"/admin?tab=growth&section=email&toast={toast}", status_code=303)

    # ── Launch Day email ─────────────────────────────────────────────────
    if action in ("send_launch_test", "send_launch_all"):
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM tools WHERE status='approved'")
        tool_count = (await cursor.fetchone())["cnt"]
        cursor = await db.execute("SELECT COUNT(*) as cnt FROM makers")
        maker_count = (await cursor.fetchone())["cnt"]
        subject = f"The IndieStack Marketplace is Live \u2014 Browse {tool_count} Indie Tools"

        if action == "send_launch_test":
            smtp_from = os.environ.get("SMTP_FROM", "")
            if not smtp_from:
                toast = "SMTP_FROM not configured"
            else:
                html_body = launch_day_html(tool_count=tool_count, maker_count=maker_count)
                ok = await send_email(smtp_from, subject, html_body)
                toast = "Launch day test sent!" if ok else "Launch day test failed"
        else:
            subscribers = await get_all_subscribers_with_dates(db)
            success = fail = 0
            for sub in subscribers:
                unsub = _unsub_url(sub.get("unsubscribe_token"))
                html_body = launch_day_html(tool_count=tool_count, maker_count=maker_count, unsubscribe_url=unsub)
                ok = await send_email(sub["email"], subject, html_body, unsubscribe_url=unsub)
                if ok:
                    success += 1
                else:
                    fail += 1
            toast = f"Launch day email sent: {success} success, {fail} failed"
        return RedirectResponse(url=f"/admin?tab=growth&section=email&toast={toast}", status_code=303)

    # ── Maker Launch Countdown email ─────────────────────────────────────
    if action in ("send_maker_countdown_test", "send_maker_countdown_all"):
        subject = "The Marketplace Opens Monday \u2014 Connect Stripe Now"

        if action == "send_maker_countdown_test":
            smtp_from = os.environ.get("SMTP_FROM", "")
            if not smtp_from:
                toast = "SMTP_FROM not configured"
            else:
                html_body = maker_launch_countdown_html("Test Maker", "test-maker", 3)
                from indiestack.email import _email_wrapper
                ok = await send_email(smtp_from, subject, _email_wrapper(html_body))
                toast = "Maker countdown test sent!" if ok else "Maker countdown test failed"
        else:
            cursor = await db.execute(
                """SELECT m.id, m.name, m.slug, u.email, COUNT(t.id) as tool_count
                   FROM makers m
                   JOIN users u ON u.maker_id = m.id
                   LEFT JOIN tools t ON t.maker_id = m.id AND t.status = 'approved'
                   GROUP BY m.id"""
            )
            claimed_makers = [dict(r) for r in await cursor.fetchall()]
            success = fail = 0
            for mk in claimed_makers:
                mk_name = mk.get("name") or "Maker"
                mk_slug = mk.get("slug") or ""
                mk_tools = mk.get("tool_count") or 0
                html_body = maker_launch_countdown_html(mk_name, mk_slug, mk_tools)
                from indiestack.email import _email_wrapper
                ok = await send_email(mk["email"], subject, _email_wrapper(html_body))
                if ok:
                    success += 1
                else:
                    fail += 1
            toast = f"Maker countdown sent: {success} success, {fail} failed"
        return RedirectResponse(url=f"/admin?tab=growth&section=email&toast={toast}", status_code=303)

    # ── Nudge action ──────────────────────────────────────────────────────
    if action == "send_nudge":
        maker_email = form.get("maker_email", "")
        maker_name = form.get("maker_name", "Unknown")
        if maker_email:
            subj = f"Quick update on {maker_name}'s IndieStack listing"
            html_body = f"""<p>Hi {escape(maker_name)},</p>
<p>Just a friendly nudge \u2014 your IndieStack listing could use a fresh changelog update.
Even a small note about what you've been working on helps your tool stand out and keeps your profile active.</p>
<p>You can post an update here: <a href="{BASE_URL}/dashboard">indiestack.fly.dev/dashboard</a></p>
<p>Cheers,<br>IndieStack</p>"""
            ok = await send_email(maker_email, subj, html_body)
            toast = f"Nudge sent to {maker_name}!" if ok else f"Failed to send nudge to {maker_name}"
        else:
            toast = "No email address for this maker"
        return RedirectResponse(url=f"/admin?tab=people&toast={toast}", status_code=303)

    # ── Magic link actions ───────────────────────────────────────────────
    if action == "generate_magic":
        tool_id = form.get("tool_id", "")
        if tool_id:
            await create_magic_claim_token(db, int(tool_id), days=7)
        return RedirectResponse(url="/admin?tab=growth&section=email&toast=Magic+link+generated", status_code=303)

    if action == "generate_all_csv":
        tools = await get_unclaimed_tools_for_outreach(db)
        for t in tools:
            await create_magic_claim_token(db, t["id"], days=7)
        return RedirectResponse(url=f"/admin?tab=growth&section=email&toast=Generated+{len(tools)}+magic+links", status_code=303)

    # ── Stripe nudge action ──────────────────────────────────────────────
    if action == "send_stripe_nudge":
        maker_id = form.get("maker_id", "")
        if not maker_id:
            return RedirectResponse(url="/admin?tab=people&toast=No+maker+ID+provided", status_code=303)

        cursor = await db.execute("SELECT u.email FROM users u WHERE u.maker_id = ?", (int(maker_id),))
        row = await cursor.fetchone()
        maker_email = row["email"] if row else ""
        if not maker_email:
            return RedirectResponse(url="/admin?tab=people&toast=No+email+for+this+maker", status_code=303)

        cursor2 = await db.execute(
            "SELECT name FROM tools WHERE maker_id = ? AND price_pence > 0 AND (stripe_account_id IS NULL OR stripe_account_id = '')",
            (int(maker_id),),
        )
        priced_tools = [dict(r) for r in await cursor2.fetchall()]
        if not priced_tools:
            return RedirectResponse(url="/admin?tab=people&toast=No+priced+tools+without+Stripe", status_code=303)

        tool_name = priced_tools[0]["name"]
        html_body = maker_stripe_nudge_html(tool_name=tool_name, dashboard_url=f"{BASE_URL}/dashboard")
        subj = "Connect Stripe \u2014 IndieStack Marketplace launches March 2nd"
        ok = await send_email(maker_email, subj, html_body)
        toast = "Stripe+nudge+sent" if ok else "Failed+to+send+Stripe+nudge"
        return RedirectResponse(url=f"/admin?tab=people&toast={toast}", status_code=303)

    # Default fallback
    return RedirectResponse(url="/admin?tab=growth&section=email", status_code=303)

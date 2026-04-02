"""Shared rendering helpers for the IndieStack Admin Command Center.

Provides reusable UI components (KPI cards, badges, charts, tables, navigation)
used across the consolidated admin interface. All functions return HTML strings
using the project's design token system from components.py.
"""

from html import escape
from datetime import datetime


def time_ago(dt_str):
    """Format a datetime string as relative time ('3d ago', '2w ago', 'just now').
    Returns em-dash for None or invalid input."""
    if not dt_str:
        return "\u2014"
    try:
        dt = datetime.fromisoformat(str(dt_str).replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        delta = now - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "just now"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m ago"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h ago"
        days = hours // 24
        if days < 7:
            return f"{days}d ago"
        weeks = days // 7
        if weeks < 5:
            return f"{weeks}w ago"
        months = days // 30
        if months < 12:
            return f"{months}mo ago"
        years = days // 365
        return f"{years}y ago"
    except Exception:
        return "\u2014"


def days_ago_label(days):
    """Human-readable label for a days count."""
    if days is None:
        return "Never"
    if days == 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    if days < 30:
        return f"{days}d ago"
    if days < 365:
        months = days // 30
        return f"{months}mo ago"
    years = days // 365
    return f"{years}y ago"


def kpi_card(label, value, color="var(--slate)", link="", sublabel="", delta=None):
    """Stat card with colored left border, large value, muted label, and optional trend delta."""
    inner = f'''
        <div style="font-family:var(--font-display);font-size:28px;color:var(--ink);line-height:1.2;">
            {value}
        </div>
        <div style="font-size:12px;color:var(--ink-muted);margin-top:4px;">
            {escape(str(label))}
        </div>
    '''
    if sublabel:
        inner += f'''
        <div style="font-size:11px;color:var(--ink-muted);margin-top:2px;">
            {escape(str(sublabel))}
        </div>
        '''
    if delta is not None:
        try:
            delta_num = float(str(delta).replace("%", "").replace("+", ""))
            if delta_num > 0:
                delta_color, arrow = "#16a34a", "▲"
            elif delta_num < 0:
                delta_color, arrow = "#DC2626", "▼"
            else:
                delta_color, arrow = "var(--ink-muted)", "—"
        except (ValueError, TypeError):
            delta_color, arrow = "var(--ink-muted)", ""
        inner += f'<div style="font-size:11px;color:{delta_color};margin-top:4px;font-weight:600;">{arrow} {escape(str(delta))}</div>'

    style = f"border-left:3px solid {color};padding:16px 20px;"

    if link:
        return f'<a href="{escape(str(link))}" class="card" style="{style}text-decoration:none;display:block;">{inner}</a>'
    return f'<div class="card" style="{style}">{inner}</div>'


def pending_alert_bar(count):
    """Orange alert bar shown when pending tools exist."""
    if not count or count <= 0:
        return ""
    return f'''
    <div style="background:#FFF7ED;border:1px solid #FDBA74;border-left:4px solid #EA580C;
                border-radius:var(--radius-sm);padding:12px 16px;margin-bottom:20px;
                display:flex;align-items:center;justify-content:space-between;">
        <span style="color:#9A3412;font-size:14px;font-weight:600;">
            \u26a0\ufe0f {count} tool{"s" if count != 1 else ""} pending review
        </span>
        <a href="/admin?tab=tools&amp;status=pending"
           style="background:#EA580C;color:#fff;padding:6px 14px;border-radius:var(--radius-sm);
                  font-size:12px;font-weight:600;text-decoration:none;">
            Review Now
        </a>
    </div>
    '''


def status_badge(status):
    """Activity status badge: active (green), idle (yellow), dormant (red)."""
    s = (status or "").lower().strip()
    if s == "active":
        bg, fg, label = "#DCFCE7", "#16a34a", "Active"
    elif s == "idle":
        bg, fg, label = "#FEF9C3", "#CA8A04", "Idle"
    else:
        bg, fg, label = "#FEE2E2", "#DC2626", "Dormant"
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:9999px;'
        f'font-size:11px;font-weight:700;background:{bg};color:{fg};">'
        f'{label}</span>'
    )


def freshness_badge(freshness):
    """Tool freshness badge: active (green), stale (yellow), inactive (red), unknown (gray)."""
    f = (freshness or "").lower().strip()
    if f == "active":
        bg, fg, label = "#DCFCE7", "#16a34a", "Active"
    elif f == "stale":
        bg, fg, label = "#FEF9C3", "#CA8A04", "Stale"
    elif f == "inactive":
        bg, fg, label = "#FEE2E2", "#DC2626", "Inactive"
    else:
        bg, fg, label = "#F3F4F6", "#6B7280", "Unknown"
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:9999px;'
        f'font-size:11px;font-weight:700;background:{bg};color:{fg};">'
        f'{label}</span>'
    )


def role_badge(role):
    """Person role badge for the People tab."""
    r = (role or "").lower().strip()
    colors = {
        "maker": ("#DCFCE7", "#16a34a"),
        "subscriber": ("#DBEAFE", "#2563EB"),
        "buyer": ("#F3E8FF", "#7C3AED"),
    }
    bg, fg = colors.get(r, ("#F3F4F6", "#6B7280"))
    label = r.capitalize() if r in colors else "Unclaimed"
    return (
        f'<span style="display:inline-block;padding:2px 8px;border-radius:9999px;'
        f'font-size:11px;font-weight:700;background:{bg};color:{fg};">'
        f'{escape(label)}</span>'
    )


def tab_nav(active_tab, pending_count=0):
    """5-tab navigation bar for the admin command center."""
    tabs = [
        ("overview", "Overview"),
        ("tools", "Tools"),
        ("people", "People"),
        ("growth", "Growth"),
    ]
    items = []
    for slug, label in tabs:
        is_active = (active_tab or "").lower() == slug
        if is_active:
            style = (
                "color:var(--slate);border-bottom:2px solid var(--slate);"
                "font-weight:700;background:rgba(26,45,74,0.04);"
            )
        else:
            style = "color:var(--ink-muted);border-bottom:2px solid transparent;"
        dot = ""
        if slug == "tools" and pending_count and pending_count > 0:
            dot = (
                '<span style="display:inline-block;width:8px;height:8px;'
                'border-radius:50%;background:#EA580C;margin-left:6px;'
                'vertical-align:middle;"></span>'
            )
        items.append(
            f'<a href="/admin?tab={slug}" style="{style}padding:10px 16px;'
            f'text-decoration:none;font-size:14px;font-family:var(--font-body);'
            f'white-space:nowrap;">{escape(label)}{dot}</a>'
        )
    return (
        f'<div style="display:flex;border-bottom:1px solid var(--border);'
        f'margin-bottom:24px;gap:0;overflow-x:auto;">{"".join(items)}</div>'
    )


def growth_sub_nav(active_section):
    """Sub-nav within the Growth tab — 4 consolidated sections."""
    _aliases = {
        "charts": "traffic", "tables": "traffic",
        "email": "outreach", "magic": "outreach",
        "makers": "outreach", "stale": "outreach", "social": "outreach",
    }
    active_section = _aliases.get((active_section or "").lower(), active_section)
    sections = [
        ("traffic", "Traffic"),
        ("funnels", "Funnels"),
        ("search", "Search"),
        ("outreach", "Outreach"),
    ]
    items = []
    for slug, label in sections:
        is_active = (active_section or "").lower() == slug
        if is_active:
            style = "color:var(--slate);border-bottom:2px solid var(--slate);font-weight:600;"
        else:
            style = "color:var(--ink-muted);border-bottom:2px solid transparent;"
        items.append(
            f'<a href="/admin?tab=growth&amp;section={slug}" style="{style}padding:8px 14px;'
            f'text-decoration:none;font-size:13px;font-family:var(--font-body);'
            f'white-space:nowrap;">{escape(label)}</a>'
        )
    return (
        f'<div style="display:flex;border-bottom:1px solid var(--border);'
        f'margin-bottom:20px;gap:0;opacity:0.85;">{"".join(items)}</div>'
    )


def tools_sub_nav(active_section, pending_count=0):
    """Sub-nav within the Tools tab."""
    sections = [
        ("pending", f"Pending ({pending_count})" if pending_count else "Pending"),
        ("all", "All Tools"),
        ("claims", "Claims"),
        ("stacks", "Stacks"),
        ("reviews", "Reviews"),
    ]
    items = []
    for slug, label in sections:
        is_active = (active_section or "").lower() == slug
        if is_active:
            style = "color:var(--slate);border-bottom:2px solid var(--slate);font-weight:600;"
        else:
            style = "color:var(--ink-muted);border-bottom:2px solid transparent;"
        items.append(
            f'<a href="/admin?tab=tools&amp;section={slug}" style="{style}padding:8px 14px;'
            f'text-decoration:none;font-size:13px;font-family:var(--font-body);'
            f'white-space:nowrap;">{label}</a>'
        )
    return (
        f'<div style="display:flex;border-bottom:1px solid var(--border);'
        f'margin-bottom:20px;gap:0;opacity:0.85;">{"".join(items)}</div>'
    )


def bar_chart(data, title, value_prefix="", value_suffix=""):
    """Reusable vertical bar chart. data = [(label, value), ...]."""
    if not data:
        return (
            '<div class="card" style="padding:20px;text-align:center;'
            'color:var(--ink-muted);font-size:14px;">No data yet</div>'
        )
    max_val = max((v for _, v in data), default=1) or 1
    bars = []
    for label, value in data:
        height = max(int((value / max_val) * 200), 2)
        bars.append(
            f'<div style="display:flex;flex-direction:column;align-items:center;'
            f'flex:1;min-width:0;gap:6px;">'
            f'<span style="font-size:12px;font-weight:600;color:var(--ink);'
            f'font-family:var(--font-mono);white-space:nowrap;">'
            f'{escape(str(value_prefix))}{escape(str(value))}{escape(str(value_suffix))}</span>'
            f'<div style="width:100%;max-width:48px;height:{height}px;'
            f'background:var(--slate);border-radius:var(--radius-sm) var(--radius-sm) 0 0;"></div>'
            f'<span style="font-size:11px;color:var(--ink-muted);text-align:center;'
            f'word-break:break-word;line-height:1.2;">{escape(str(label))}</span>'
            f'</div>'
        )
    return (
        f'<div class="card" style="padding:20px;">'
        f'<h3 style="font-family:var(--font-display);font-size:18px;margin:0 0 16px 0;'
        f'color:var(--ink);">{escape(str(title))}</h3>'
        f'<div style="display:flex;align-items:flex-end;gap:8px;height:260px;'
        f'padding-top:20px;border-top:1px solid var(--border);margin-top:auto;">{"".join(bars)}</div></div>'
    )


def data_table(title, headers, rows_html, empty_msg="No data yet"):
    """Reusable table card with sticky header and scrollable body."""
    if not rows_html or not rows_html.strip():
        return (
            f'<div class="card" style="padding:20px;">'
            f'<h3 style="font-family:var(--font-display);font-size:18px;margin:0 0 12px 0;'
            f'color:var(--ink);">{escape(str(title))}</h3>'
            f'<p style="color:var(--ink-muted);font-size:14px;text-align:center;'
            f'padding:24px 0;">{escape(str(empty_msg))}</p></div>'
        )
    header_cells = "".join(
        f'<th style="text-transform:uppercase;font-size:12px;color:var(--ink-muted);'
        f'font-weight:700;padding:10px 12px;text-align:left;white-space:nowrap;'
        f'position:sticky;top:0;background:var(--card-bg);z-index:1;'
        f'border-bottom:1px solid var(--border);">{escape(str(h))}</th>'
        for h in headers
    )
    return (
        f'<div class="card" style="padding:20px;">'
        f'<h3 style="font-family:var(--font-display);font-size:18px;margin:0 0 12px 0;'
        f'color:var(--ink);">{escape(str(title))}</h3>'
        f'<div style="overflow-x:auto;max-height:600px;overflow-y:auto;">'
        f'<table style="width:100%;border-collapse:collapse;font-size:13px;">'
        f'<thead><tr>{header_cells}</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        f'</table></div></div>'
    )


def row_bg(index):
    """Return alternating row background style. Even indices get cream-dark."""
    if index % 2 == 0:
        return "background:var(--cream-dark);"
    return ""

"""Launch With Me — co-marketing pages for indie makers."""

import json
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.config import BASE_URL
from indiestack.payments import is_launch_holiday
from indiestack.routes.components import page_shell, tool_card, indie_badge_html
from indiestack.db import get_maker_with_tools, get_maker_stats

router = APIRouter()


@router.get("/launch/{slug}", response_class=HTMLResponse)
async def launch_with_me(request: Request, slug: str):
    db = request.state.db
    maker, tools = await get_maker_with_tools(db, slug)

    if not maker:
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Maker Not Found</h1>
            <p class="text-muted mt-4">We couldn't find this maker profile.</p>
            <a href="/makers" class="btn btn-primary mt-4">Browse Makers</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body, user=request.state.user), status_code=404)

    name = escape(str(maker['name']))
    bio = escape(str(maker.get('bio', '')))
    url = escape(str(maker.get('url', '')))
    maker_slug = escape(str(maker['slug']))
    stats = await get_maker_stats(db, maker['id'])
    tool_count = stats['tool_count']
    total_upvotes = stats['total_upvotes']
    # Tool names for subtitle
    tool_names = ', '.join(escape(str(t.get('name', ''))) for t in tools[:3])
    if len(tools) > 3:
        tool_names += f' and {len(tools) - 3} more'

    # Indie badge
    indie_status = str(maker.get('indie_status', ''))
    badge_html = indie_badge_html(indie_status) if indie_status else ''

    # Page URL for sharing
    page_url = f"{BASE_URL}/launch/{maker_slug}"

    # ── Launch Week Banner (only during launch holiday: March 2-16) ────
    if is_launch_holiday():
        banner_html = """
        <div style="background:linear-gradient(135deg,var(--terracotta),var(--terracotta-dark));
                    color:white;text-align:center;padding:14px 24px;font-size:14px;font-weight:600;">
            Launch Week Special: 0% commission &mdash; makers keep 100%
        </div>
        """
    else:
        banner_html = ""

    # ── Hero Section ────────────────────────────────────────────────────
    hero_html = f"""
    <div style="text-align:center;padding:56px 24px 32px;">
        <div style="display:inline-flex;align-items:center;justify-content:center;width:96px;height:96px;
                    border-radius:50%;background:var(--terracotta);color:white;font-size:40px;
                    font-family:var(--font-display);margin-bottom:16px;box-shadow:var(--shadow-md);">
            {name[0].upper() if name else '?'}
        </div>
        <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin-bottom:8px;">
            Launch with {name}
        </h1>
        <p style="color:var(--ink-light);font-size:17px;max-width:600px;margin:0 auto;">
            Meet the maker behind {tool_names if tool_names else 'these tools'}
        </p>
        {badge_html}
    </div>
    """

    # ── URL display ─────────────────────────────────────────────────────
    url_html = ''
    if url:
        url_html = f"""
        <div style="text-align:center;margin-bottom:8px;">
            <a href="{url}" target="_blank" rel="noopener"
               style="color:var(--slate-dark);font-size:14px;font-weight:500;">
                {url}
            </a>
        </div>
        """

    # ── Bio ──────────────────────────────────────────────────────────────
    bio_html = ''
    if bio:
        bio_html = f"""
        <div style="text-align:center;margin-bottom:24px;">
            <p style="color:var(--ink-light);font-size:15px;line-height:1.6;max-width:600px;margin:0 auto;">
                {bio}
            </p>
        </div>
        """

    # ── Stats Row ────────────────────────────────────────────────────────
    stats_html = f"""
    <div style="display:flex;gap:32px;justify-content:center;margin:24px 0 40px;">
        <div style="text-align:center;">
            <div style="font-family:var(--font-display);font-size:28px;color:var(--ink);">{tool_count}</div>
            <div style="font-size:13px;color:var(--ink-muted);">tool{"s" if tool_count != 1 else ""}</div>
        </div>
        <div style="text-align:center;">
            <div style="font-family:var(--font-display);font-size:28px;color:var(--slate-dark);">{total_upvotes}</div>
            <div style="font-size:13px;color:var(--ink-muted);">upvotes</div>
        </div>
    </div>
    """

    # ── Tools Grid ───────────────────────────────────────────────────────
    if tools:
        cards = '\n'.join(tool_card(t) for t in tools)
        tools_html = f"""
        <div style="margin:0 auto;max-width:900px;padding:0 24px;">
            <h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:20px;color:var(--ink);text-align:center;">
                Tools by {name}
            </h2>
            <div class="card-grid">{cards}</div>
        </div>
        """
    else:
        tools_html = """
        <div style="text-align:center;padding:40px 0;">
            <p style="color:var(--ink-muted);">No published tools yet.</p>
        </div>
        """

    # ── CTAs ─────────────────────────────────────────────────────────────
    cta_html = f"""
    <div style="text-align:center;padding:40px 24px;">
        <a href="/maker/{maker_slug}" class="btn btn-primary"
           style="padding:14px 28px;font-size:16px;margin-right:12px;">
            View Maker Profile &rarr;
        </a>
        <a href="/makers" class="btn btn-slate"
           style="padding:14px 28px;font-size:16px;">
            Browse All Makers
        </a>
    </div>
    """

    # ── Share Section ────────────────────────────────────────────────────
    share_html = f"""
    <div style="max-width:600px;margin:0 auto;padding:32px 24px;text-align:center;">
        <div class="section-divider" style="margin-bottom:32px;"></div>
        <h3 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:12px;">
            Share this page
        </h3>
        <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
            Help {name} get discovered by sharing their launch page.
        </p>
        <div style="display:flex;gap:8px;justify-content:center;align-items:center;">
            <input type="text" id="share-url" value="{page_url}" readonly
                   style="flex:1;max-width:400px;padding:12px 16px;font-size:13px;font-family:var(--font-mono);
                          border:1px solid var(--border);border-radius:var(--radius-sm);background:var(--cream);
                          color:var(--ink);">
            <button onclick="navigator.clipboard.writeText(document.getElementById('share-url').value).then(()=>this.textContent='Copied!')"
                    style="padding:12px 20px;font-size:13px;font-weight:600;font-family:var(--font-body);
                           background:var(--terracotta);color:white;border:none;border-radius:var(--radius-sm);
                           cursor:pointer;">
                Copy
            </button>
        </div>
    </div>
    """

    # ── JSON-LD ──────────────────────────────────────────────────────────
    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ProfilePage",
        "name": f"Launch with {maker['name']}",
        "description": f"Co-marketing page for {maker['name']} on IndieStack. {tool_count} tools, {total_upvotes} upvotes.",
        "url": page_url,
        "mainEntity": {
            "@type": "Person",
            "name": maker['name'],
            "url": maker.get('url', ''),
        }
    })

    extra_head = f'<script type="application/ld+json">{json_ld}</script>'

    # ── Assemble Page ────────────────────────────────────────────────────
    body = f"""
    {banner_html}
    <div class="container" style="padding-bottom:48px;max-width:900px;">
        {hero_html}
        {url_html}
        {bio_html}
        {stats_html}
        {tools_html}
        {cta_html}
        {share_html}
    </div>
    """

    description = f"Launch with {maker['name']} on IndieStack. Discover {tool_count} indie tool{'s' if tool_count != 1 else ''} built by this maker."

    return HTMLResponse(page_shell(
        f"Launch with {maker['name']}",
        body,
        description=description,
        extra_head=extra_head,
        user=request.state.user,
        canonical=f"/launch/{maker['slug']}",
    ))

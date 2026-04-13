"""Developer Intent Intelligence — B2B competitive data for tool companies."""

import logging
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from indiestack import db
from indiestack.auth import check_admin_session
from indiestack.routes.components import page_shell

_log = logging.getLogger("indiestack.intel")
router = APIRouter()


# -- Shared data fetching --------------------------------------------------

async def _fetch_intel(d, slug: str) -> dict | None:
    """Fetch all intelligence data for a tool. Returns None if tool not found."""
    tool = await db.execute_fetchone(d,
        "SELECT id, name, slug FROM tools WHERE slug = ? AND status = 'approved'", (slug,))
    if not tool:
        return None

    tool_id = tool['id']
    name = tool['name']

    views = await db.execute_fetchone(d,
        "SELECT COUNT(*) as total FROM tool_views WHERE tool_id = ?", (tool_id,))

    clicks = await db.execute_fetchone(d,
        "SELECT COUNT(*) as total FROM outbound_clicks WHERE tool_id = ?", (tool_id,))

    citations = await db.execute_fetchone(d,
        "SELECT COUNT(*) as total FROM agent_citations WHERE tool_id = ?", (tool_id,))

    # What tools do viewers compare this to?
    cursor_compared = await d.execute(
        "SELECT t2.slug, t2.name, COUNT(*) as overlap_count "
        "FROM tool_views v1 "
        "JOIN tool_views v2 ON v1.ip_hash = v2.ip_hash AND v2.tool_id != v1.tool_id "
        "JOIN tools t2 ON v2.tool_id = t2.id "
        "WHERE v1.tool_id = ? "
        "GROUP BY t2.slug ORDER BY overlap_count DESC LIMIT 10", (tool_id,))
    compared_to = [dict(r) for r in await cursor_compared.fetchall()]

    # Migration momentum — leaving
    cursor_from = await d.execute(
        "SELECT to_package, COUNT(*) as cnt FROM migration_paths "
        "WHERE from_package = ? GROUP BY to_package ORDER BY cnt DESC LIMIT 5", (slug,))
    migrating_away = [dict(r) for r in await cursor_from.fetchall()]

    # Migration momentum — arriving
    cursor_to = await d.execute(
        "SELECT from_package, COUNT(*) as cnt FROM migration_paths "
        "WHERE to_package = ? GROUP BY from_package ORDER BY cnt DESC LIMIT 5", (slug,))
    migrating_to = [dict(r) for r in await cursor_to.fetchall()]

    # Search queries leading here
    cursor_search = await d.execute(
        "SELECT query, COUNT(*) as cnt FROM search_logs "
        "WHERE top_result_slug = ? GROUP BY query ORDER BY cnt DESC LIMIT 10", (slug,))
    search_queries = [dict(r) for r in await cursor_search.fetchall()]

    # Co-occurrence — commonly paired packages
    cursor_cooc = await d.execute(
        "SELECT tool_b_slug as paired_with, cooccurrence_count FROM manifest_cooccurrences "
        "WHERE tool_a_slug = ? "
        "UNION ALL "
        "SELECT tool_a_slug as paired_with, cooccurrence_count FROM manifest_cooccurrences "
        "WHERE tool_b_slug = ? "
        "ORDER BY cooccurrence_count DESC LIMIT 10", (slug, slug))
    commonly_paired = [dict(r) for r in await cursor_cooc.fetchall()]

    return {
        "tool": {"slug": slug, "name": name},
        "views": views['total'] if views else 0,
        "outbound_clicks": clicks['total'] if clicks else 0,
        "agent_citations": citations['total'] if citations else 0,
        "compared_to": compared_to,
        "commonly_paired_with": commonly_paired,
        "migration_away": migrating_away,
        "migration_towards": migrating_to,
        "search_queries": search_queries,
    }


# -- JSON API endpoint -----------------------------------------------------

@router.get("/api/intel/{slug}")
async def tool_intelligence_api(request: Request, slug: str):
    """Competitive intelligence API. Requires API key with intel scope."""
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return JSONResponse({"error": "Authorization: Bearer <api_key> required"}, status_code=401)

    key_str = auth[7:]
    d = request.state.db
    cursor = await d.execute(
        "SELECT id, tier, scopes FROM api_keys WHERE key = ? AND is_active = 1", (key_str,))
    key = await cursor.fetchone()
    if not key:
        return JSONResponse({"error": "Invalid API key"}, status_code=401)

    scopes = (key['scopes'] or '').split(',')
    if 'intel' not in scopes and 'admin' not in scopes:
        return JSONResponse({"error": "API key requires 'intel' scope"}, status_code=403)

    data = await _fetch_intel(d, slug.lower().strip())
    if not data:
        return JSONResponse({"error": f"Tool '{slug}' not found"}, status_code=404)

    return JSONResponse(data)


# -- Visual dashboard ------------------------------------------------------

@router.get("/intel/{slug}", response_class=HTMLResponse)
async def intel_dashboard(request: Request, slug: str):
    """Visual competitive intelligence dashboard for a tool."""
    user = getattr(request.state, "user", None)
    is_admin = check_admin_session(request)

    if not is_admin:
        return HTMLResponse(page_shell(
            "Developer Intent Intelligence — IndieStack",
            '<div style="max-width:600px;margin:80px auto;text-align:center;">'
            '<h1 style="font-family:var(--font-heading);">Developer Intent Intelligence</h1>'
            '<p style="color:var(--text-muted);margin:16px 0;">Competitive intelligence for developer tool companies. '
            'See what developers compare your tool to, where they migrate, and what they search for.</p>'
            '<p style="color:var(--text-muted);margin-top:24px;">Contact '
            '<a href="mailto:hello@indiestack.ai" style="color:var(--accent);">hello@indiestack.ai</a> '
            'for access — starting at $499/mo.</p></div>',
            user=user,
        ))

    d = request.state.db
    safe_slug = escape(slug.lower().strip())
    data = await _fetch_intel(d, slug.lower().strip())

    if not data:
        return HTMLResponse(page_shell("Not Found — IndieStack",
            f'<div style="text-align:center;padding:80px 20px;">'
            f'<h1 style="font-family:var(--font-heading);">Tool "{safe_slug}" not found</h1></div>',
            user=user), status_code=404)

    name = escape(data['tool']['name'])
    v = data['views']
    c = data['outbound_clicks']
    ci = data['agent_citations']

    # Stats bar
    stats = f'''
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:32px;">
      <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:20px;text-align:center;">
        <div style="font-size:2rem;font-weight:700;color:var(--accent);">{v:,}</div>
        <div style="color:var(--text-muted);font-size:0.85rem;">Tool Page Views</div>
      </div>
      <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:20px;text-align:center;">
        <div style="font-size:2rem;font-weight:700;color:var(--accent);">{c:,}</div>
        <div style="color:var(--text-muted);font-size:0.85rem;">Outbound Clicks</div>
      </div>
      <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:20px;text-align:center;">
        <div style="font-size:2rem;font-weight:700;color:var(--accent);">{ci:,}</div>
        <div style="color:var(--text-muted);font-size:0.85rem;">Agent Citations</div>
      </div>
    </div>'''

    # Compared-to table
    rows = "".join(
        f'<tr><td><a href="/tool/{escape(x["slug"])}" style="color:var(--accent);">{escape(x["name"])}</a></td>'
        f'<td style="text-align:right;">{x["overlap_count"]}</td></tr>'
        for x in data['compared_to'][:8]
    ) or '<tr><td colspan="2" style="color:var(--text-muted);padding:12px 0;">No comparison data yet</td></tr>'
    compared = f'''
    <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:24px;margin-bottom:24px;">
      <h3 style="margin:0 0 16px;font-family:var(--font-heading);">Developers Also Viewed</h3>
      <p style="color:var(--text-muted);font-size:0.85rem;margin-bottom:12px;">Tools viewed by the same developers who looked at {name}</p>
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr style="border-bottom:1px solid var(--border);"><th style="text-align:left;padding:8px 0;color:var(--text-muted);font-size:0.8rem;">Tool</th><th style="text-align:right;padding:8px 0;color:var(--text-muted);font-size:0.8rem;">Overlap</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>'''

    # Migration
    away = "".join(f'<li>{escape(m["to_package"])} ({m["cnt"]} repos)</li>' for m in data['migration_away']) or '<li style="color:var(--text-muted);">No outward migration detected</li>'
    toward = "".join(f'<li>{escape(m["from_package"])} ({m["cnt"]} repos)</li>' for m in data['migration_towards']) or '<li style="color:var(--text-muted);">No inward migration detected</li>'
    migration = f'''
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-bottom:24px;">
      <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:24px;">
        <h3 style="margin:0 0 12px;font-family:var(--font-heading);font-size:1.1rem;">Migrating Away</h3>
        <ul style="margin:0;padding-left:20px;color:var(--text-muted);">{away}</ul>
      </div>
      <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:24px;">
        <h3 style="margin:0 0 12px;font-family:var(--font-heading);font-size:1.1rem;">Migrating To</h3>
        <ul style="margin:0;padding-left:20px;color:var(--text-muted);">{toward}</ul>
      </div>
    </div>'''

    # Search queries
    qrows = "".join(
        f'<tr><td style="padding:6px 0;">{escape(q["query"])}</td><td style="text-align:right;padding:6px 0;">{q["cnt"]}</td></tr>'
        for q in data['search_queries'][:8]
    ) or '<tr><td colspan="2" style="color:var(--text-muted);padding:12px 0;">No search data yet</td></tr>'
    search = f'''
    <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:24px;margin-bottom:24px;">
      <h3 style="margin:0 0 16px;font-family:var(--font-heading);">Search Queries Leading Here</h3>
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr style="border-bottom:1px solid var(--border);"><th style="text-align:left;padding:8px 0;color:var(--text-muted);font-size:0.8rem;">Query</th><th style="text-align:right;padding:8px 0;color:var(--text-muted);font-size:0.8rem;">Count</th></tr></thead>
        <tbody>{qrows}</tbody>
      </table>
    </div>'''

    # Commonly paired
    paired_items = "".join(
        f'<span style="display:inline-block;background:var(--bg);border:1px solid var(--border);border-radius:999px;padding:4px 12px;margin:4px;font-size:0.85rem;">{escape(p["paired_with"])} <span style="color:var(--text-muted);">({p["cooccurrence_count"]})</span></span>'
        for p in data['commonly_paired_with'][:12]
    ) or '<span style="color:var(--text-muted);">No co-occurrence data</span>'
    paired = f'''
    <div style="background:var(--card-bg);border:1px solid var(--border);border-radius:12px;padding:24px;margin-bottom:24px;">
      <h3 style="margin:0 0 16px;font-family:var(--font-heading);">Commonly Paired With</h3>
      <div>{paired_items}</div>
    </div>'''

    content = f'''
    <div style="max-width:820px;margin:0 auto;padding:40px 20px;">
      <div style="margin-bottom:32px;">
        <div style="color:var(--text-muted);font-size:0.85rem;margin-bottom:4px;">Developer Intent Intelligence</div>
        <h1 style="font-family:var(--font-heading);font-size:2rem;margin:0;">{name}</h1>
      </div>
      {stats}
      {compared}
      {migration}
      {search}
      {paired}
      <div style="text-align:center;padding:24px 0;border-top:1px solid var(--border);color:var(--text-muted);font-size:0.8rem;">
        IndieStack Developer Intelligence &middot; {v:,} developer interactions
        &middot; <a href="mailto:hello@indiestack.ai" style="color:var(--accent);">Get API access</a>
      </div>
    </div>'''

    return HTMLResponse(page_shell(
        f"{name} — Developer Intelligence — IndieStack", content,
        description=f"Competitive intelligence for {name}. Developer comparison data, migration trends, and search intent.",
        user=user,
    ))

from math import ceil

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from html import escape
from urllib.parse import urlencode

from indiestack.routes.components import page_shell, tool_card, search_filters_html, pagination_html, email_sticky_bar
from indiestack.db import search_tools_advanced, get_all_categories, log_search, get_search_demand, get_batch_success_rates

router = APIRouter()


@router.get("/search", response_class=HTMLResponse)
async def search(request: Request):
    user = request.state.user

    # ── Parse query params ────────────────────────────────────────────
    query = request.query_params.get("q", "")
    price = request.query_params.get("price", "")
    sort = request.query_params.get("sort", "relevance")
    verified = request.query_params.get("verified", "")
    category = request.query_params.get("category", "")
    try:
        page = int(request.query_params.get("page", "1") or "1")
    except (ValueError, TypeError):
        page = 1

    safe_query = escape(query)

    search_box_html = f"""
    <form action="/search" method="GET" style="margin-bottom:2rem;">
        <div style="display:flex;gap:8px;max-width:520px;">
            <input
                type="text"
                name="q"
                value="{safe_query}"
                placeholder="Search creations..."
                class="form-input"
                style="flex:1;border-radius:999px;padding:12px 20px;"
            />
            <button type="submit" class="btn btn-primary" style="padding:12px 24px;">
                Search
            </button>
        </div>
    </form>
    """

    db = request.state.db
    categories = await get_all_categories(db)

    filters_html = search_filters_html(
        query=query,
        price_filter=price,
        sort=sort,
        verified_only=bool(verified),
        categories=categories,
        category_id=int(category) if category and category.isdigit() else None,
    )

    results, total = await search_tools_advanced(
        db,
        query=query,
        price_filter=price,
        sort=sort,
        verified_only=bool(verified),
        category_id=int(category) if category and category.isdigit() else None,
        page=page,
        per_page=12,
    )

    total_pages = ceil(total / 12) if total else 0

    # Build base URL for pagination (preserve all filters except page)
    params = {}
    if query:
        params["q"] = query
    if price:
        params["price"] = price
    if sort and sort != "relevance":
        params["sort"] = sort
    if verified:
        params["verified"] = verified
    if category:
        params["category"] = category
    base_url = "/search?" + urlencode(params) if params else "/search"

    pagination = pagination_html(page, total_pages, base_url)

    # Log the search for analytics
    if query.strip():
        try:
            top_slug = results[0]['slug'] if results else None
            top_name = results[0]['name'] if results else None
            await log_search(db, query, 'web', total, top_slug, top_name)
        except Exception:
            pass

    if not results:
        no_results_msg = ""
        if query.strip():
            demand = await get_search_demand(db, query, days=30)
            demand_line = ""
            if demand > 1:
                demand_line = f"""
                <p style="font-size:13px;color:var(--accent);font-weight:600;margin:8px 0 0 0;">
                    {demand} people have searched for this in the last 30 days
                </p>
                """
            no_results_msg = f"""
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                0 results for &ldquo;{safe_query}&rdquo;
            </h2>
            <p style="color:var(--ink-muted);font-size:16px;margin-bottom:24px;">
                No indie creations found for that query. Try different keywords or
                <a href="/" style="color:var(--terracotta);">browse categories</a>.
            </p>
            <div style="background:linear-gradient(135deg, var(--cream-dark), #FFF7ED);border:1px solid var(--border);
                        border-left:3px solid var(--accent);border-radius:var(--radius-sm);padding:20px 24px;">
                <h3 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin:0 0 8px 0;">
                    Market gap spotted
                </h3>
                <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;margin:0 0 12px 0;">
                    Nobody&rsquo;s built an indie <strong>{safe_query}</strong> creation yet.
                    If you&rsquo;re a maker, this is a gap waiting to be filled &mdash;
                    be the first to list yours and own this category.
                </p>
                {demand_line}
                <a href="/submit" class="btn btn-primary" style="padding:12px 20px;font-size:14px;margin-top:12px;">
                    Submit Your Creation
                </a>
            </div>
            """
        else:
            no_results_msg = '<p style="color:var(--ink-muted);font-size:16px;">Enter a search term to find creations.</p>'

        body = f"""
        <div class="container" style="padding:48px 24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);margin-bottom:24px;">Search</h1>
            {search_box_html}
            {filters_html}
            {no_results_msg}
        </div>
        """
        return HTMLResponse(page_shell(title="Search", body=body + email_sticky_bar(), user=user))

    # Inject trust badge data (success rates from agent outcome reports)
    try:
        slugs = [str(r.get('slug', '')) for r in results if r.get('slug')]
        sr_map = await get_batch_success_rates(db, slugs)
        for r in results:
            s = str(r.get('slug', ''))
            if s in sr_map:
                r['_success_rate'] = sr_map[s]
    except Exception:
        pass

    cards_html = "".join(tool_card(tool) for tool in results)
    result_label = f'{total} result{"s" if total != 1 else ""}'
    if query.strip():
        result_label += f' for &ldquo;{safe_query}&rdquo;'

    # Check if results came from 'replaces' fallback (alternatives)
    alternatives_banner = ""
    if query.strip() and results:
        q_lower = query.strip().lower()
        is_alternatives = any(
            q_lower in (r.get('replaces', '') or '').lower()
            for r in results
        )
        if is_alternatives:
            alt_slug = q_lower.replace(' ', '-').replace('.', '-')
            result_label = f'{total} indie alternative{"s" if total != 1 else ""} to &ldquo;{safe_query}&rdquo;'
            alternatives_banner = f"""
            <div style="background:var(--cream-dark);border:1px solid var(--border);border-left:3px solid var(--accent);
                        border-radius:var(--radius-sm);padding:12px 16px;margin-bottom:20px;font-size:14px;color:var(--ink);">
                Looking for <strong>{safe_query}</strong>? These indie creations are alternatives you can use instead.
                <a href="/alternatives/{escape(alt_slug)}" style="color:var(--accent);font-weight:600;margin-left:4px;">
                    View full comparison &rarr;
                </a>
            </div>
            """

    body = f"""
    <div class="container" style="padding:48px 24px;">
        <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);margin-bottom:24px;">Search</h1>
        {search_box_html}
        {filters_html}
        <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:16px;">
            {result_label}
        </h2>
        {alternatives_banner}
        <div class="card-grid">
            {cards_html}
        </div>
        {pagination}
    </div>
    """
    return HTMLResponse(page_shell(title=f"Search: {safe_query}" if query else "Search", body=body + email_sticky_bar(), user=user))

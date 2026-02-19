from math import ceil

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from html import escape
from urllib.parse import urlencode

from indiestack.routes.components import page_shell, tool_card, search_filters_html, pagination_html
from indiestack.db import search_tools_advanced, get_all_categories

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
                placeholder="Search tools..."
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

    if not results:
        no_results_msg = ""
        if query.strip():
            no_results_msg = f"""
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:12px;">
                0 results for &ldquo;{safe_query}&rdquo;
            </h2>
            <p style="color:var(--ink-muted);font-size:16px;">
                No tools found for that query. Try different keywords or
                <a href="/" style="color:var(--terracotta);">browse categories</a>.
            </p>
            """
        else:
            no_results_msg = '<p style="color:var(--ink-muted);font-size:16px;">Enter a search term to find tools.</p>'

        body = f"""
        <div class="container" style="padding:48px 24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);margin-bottom:24px;">Search</h1>
            {search_box_html}
            {filters_html}
            {no_results_msg}
        </div>
        """
        return HTMLResponse(page_shell(title="Search", body=body, user=user))

    cards_html = "".join(tool_card(tool) for tool in results)
    result_label = f'{total} result{"s" if total != 1 else ""}'
    if query.strip():
        result_label += f' for &ldquo;{safe_query}&rdquo;'

    body = f"""
    <div class="container" style="padding:48px 24px;">
        <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);margin-bottom:24px;">Search</h1>
        {search_box_html}
        {filters_html}
        <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:16px;">
            {result_label}
        </h2>
        <div class="card-grid">
            {cards_html}
        </div>
        {pagination}
    </div>
    """
    return HTMLResponse(page_shell(title=f"Search: {safe_query}" if query else "Search", body=body, user=user))

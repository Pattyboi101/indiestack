"""Unified explore page with faceted filtering."""

from math import ceil
from html import escape
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card, pagination_html
from indiestack.db import explore_tools, get_all_categories, get_all_tags_with_counts

router = APIRouter()


@router.get("/explore", response_class=HTMLResponse)
async def explore(request: Request):
    user = request.state.user
    db = request.state.db

    # Parse query params
    category = request.query_params.get("category", "")
    tag = request.query_params.get("tag", "")
    price = request.query_params.get("price", "")
    sort = request.query_params.get("sort", "hot")
    verified = request.query_params.get("verified", "")
    ejectable = request.query_params.get("ejectable", "")
    try:
        page = int(request.query_params.get("page", "1") or "1")
    except (ValueError, TypeError):
        page = 1

    # Fetch filter data
    categories = await get_all_categories(db)
    tags = await get_all_tags_with_counts(db, min_count=1)

    per_page = 24
    results, total = await explore_tools(
        db,
        category_id=int(category) if category and category.isdigit() else None,
        tag=tag,
        price_filter=price,
        sort=sort,
        verified_only=bool(verified),
        ejectable_only=bool(ejectable),
        page=page,
        per_page=per_page,
    )
    total_pages = ceil(total / per_page) if total else 0

    # Build base URL for pagination
    params = {}
    if category: params["category"] = category
    if tag: params["tag"] = tag
    if price: params["price"] = price
    if sort and sort != "hot": params["sort"] = sort
    if verified: params["verified"] = verified
    if ejectable: params["ejectable"] = ejectable
    base_url = "/explore?" + urlencode(params) if params else "/explore"

    # ── Build filter bar HTML ──────────────────────────────
    # Category dropdown
    cat_options = '<option value="">All Categories</option>'
    for c in categories:
        sel = ' selected' if category and str(c['id']) == category else ''
        cat_options += f'<option value="{c["id"]}"{sel}>{escape(str(c["name"]))}</option>'

    # Tag pills — show top 20 tags as clickable pills
    tag_pills_html = ''
    top_tags = tags[:20]
    if top_tags:
        pills = []
        for t in top_tags:
            t_name = escape(t['tag'])
            t_slug = escape(t['slug'])
            active = 'background:var(--terracotta);color:white;border-color:var(--terracotta);' if tag.lower() == t['tag'].lower() else ''
            pills.append(f'<a href="/explore?tag={t_slug}" style="display:inline-block;padding:5px 12px;border-radius:999px;font-size:12px;font-weight:600;border:1px solid var(--border);color:var(--ink-light);text-decoration:none;white-space:nowrap;{active}">{t_name} <span style="color:var(--ink-muted);font-size:11px;">({t["count"]})</span></a>')
        tag_pills_html = f'''
        <div style="margin-bottom:16px;">
            <div style="font-size:13px;font-weight:600;color:var(--ink-muted);margin-bottom:8px;">Popular Tags</div>
            <div style="display:flex;gap:6px;overflow-x:auto;padding-bottom:8px;-webkit-overflow-scrolling:touch;scrollbar-width:thin;">
                {"".join(pills)}
            </div>
        </div>
        '''

    # Price pills
    price_pills = ''
    for val, label in [("", "All"), ("free", "Free"), ("paid", "Paid")]:
        active_style = 'background:var(--terracotta);color:white;border-color:var(--terracotta);' if val == price else ''
        price_pills += f'<button type="submit" name="price" value="{val}" style="padding:5px 12px;border-radius:999px;font-size:12px;font-weight:600;cursor:pointer;border:1px solid var(--border);background:var(--card-bg);color:var(--ink-light);{active_style}">{label}</button>'

    # Sort dropdown
    sort_options = ''
    for val, label in [("hot", "Hot"), ("trending", "Trending"), ("newest", "Newest"), ("upvotes", "Most Upvoted"), ("name", "A-Z")]:
        sel = ' selected' if val == sort else ''
        sort_options += f'<option value="{val}"{sel}>{label}</option>'

    # Verified + Ejectable checkboxes
    verified_checked = ' checked' if verified else ''
    ejectable_checked = ' checked' if ejectable else ''

    # Active filter description
    active_filters = []
    if tag:
        active_filters.append(f'Tag: <strong>{escape(tag)}</strong>')
    if category:
        for c in categories:
            if str(c['id']) == category:
                active_filters.append(f'Category: <strong>{escape(str(c["name"]))}</strong>')
                break
    if verified:
        active_filters.append('<strong>Verified</strong>')
    if ejectable:
        active_filters.append('<strong>Ejectable</strong>')
    if price == 'free':
        active_filters.append('<strong>Free</strong>')
    elif price == 'paid':
        active_filters.append('<strong>Paid</strong>')

    active_html = ''
    if active_filters:
        active_html = f'''
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;flex-wrap:wrap;">
            <span style="font-size:13px;color:var(--ink-muted);">Filters:</span>
            {" &middot; ".join(active_filters)}
            <a href="/explore" style="font-size:12px;color:var(--ink-muted);text-decoration:underline;">Clear all</a>
        </div>
        '''

    filter_bar = f'''
    <form action="/explore" method="GET" style="margin-bottom:24px;">
        {"<input type='hidden' name='tag' value='" + escape(tag) + "'>" if tag else ""}
        <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:12px;">
            <select name="category" class="form-select" style="max-width:180px;font-size:13px;padding:6px 10px;border-radius:999px;" onchange="this.form.submit()">
                {cat_options}
            </select>
            <div style="display:flex;gap:6px;">
                {price_pills}
            </div>
            <select name="sort" class="form-select" style="max-width:160px;font-size:13px;padding:6px 10px;border-radius:999px;" onchange="this.form.submit()">
                {sort_options}
            </select>
            <label style="display:flex;align-items:center;gap:4px;font-size:13px;color:var(--ink-light);cursor:pointer;">
                <input type="checkbox" name="verified" value="1"{verified_checked} onchange="this.form.submit()" style="accent-color:var(--terracotta);">
                Verified
            </label>
            <label style="display:flex;align-items:center;gap:4px;font-size:13px;color:var(--ink-light);cursor:pointer;">
                <input type="checkbox" name="ejectable" value="1"{ejectable_checked} onchange="this.form.submit()" style="accent-color:var(--success-text);">
                Ejectable
            </label>
        </div>
    </form>
    '''

    # Newsletter signup banner (inline JS to avoid redirect away from explore)
    newsletter_banner = """
    <div style="background:linear-gradient(135deg,var(--terracotta),var(--terracotta-dark));border-radius:16px;padding:32px;
        margin:32px 0;text-align:center;color:#fff;">
        <h3 style="font-family:'DM Serif Display',serif;font-size:22px;margin-bottom:8px;">
            Get the best indie tools in your inbox
        </h3>
        <p style="color:rgba(255,255,255,0.7);font-size:14px;margin-bottom:20px;">
            Weekly curated picks, new launches, and maker stories. Join 2,000+ developers.
        </p>
        <form id="explore-subscribe" style="display:flex;gap:8px;max-width:400px;margin:0 auto;flex-wrap:wrap;justify-content:center;"
              onsubmit="event.preventDefault();var f=this;var em=f.email.value;fetch('/api/subscribe',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'email='+encodeURIComponent(em)}).then(function(){f.innerHTML='<p style=&quot;color:var(--success-text);font-weight:600;font-size:16px;&quot;>You\\'re in! Check your inbox.</p>'}).catch(function(){f.innerHTML='<p style=&quot;color:#EF4444;&quot;>Something went wrong. Try again.</p>'})">
            <input type="email" name="email" placeholder="you@example.com" required
                style="flex:1;min-width:200px;padding:12px 16px;border:none;border-radius:999px;font-size:14px;
                    font-family:inherit;">
            <button type="submit" style="background:var(--slate);color:var(--terracotta);border:none;padding:12px 24px;
                border-radius:999px;font-weight:700;font-size:14px;cursor:pointer;white-space:nowrap;">
                Subscribe Free
            </button>
        </form>
    </div>
    """

    # Results
    if results:
        cards_html = "".join(tool_card(t) for t in results)
        result_label = f'{total} tool{"s" if total != 1 else ""}'
        results_section = f'''
        <p style="font-size:14px;color:var(--ink-muted);margin-bottom:16px;">{result_label}</p>
        <div class="card-grid">{cards_html}</div>
        {pagination_html(page, total_pages, base_url)}
        {newsletter_banner}
        '''
    else:
        results_section = '''
        <div style="text-align:center;padding:60px 0;">
            <div style="font-size:48px;margin-bottom:12px;">&#128270;</div>
            <p style="color:var(--ink-muted);font-size:16px;">No tools match your filters.</p>
            <a href="/explore" class="btn btn-secondary mt-4">Clear filters</a>
        </div>
        '''

    body = f'''
    <div class="container" style="padding:48px 24px;overflow-x:hidden;">
        <div style="margin-bottom:32px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin-bottom:8px;">Explore Tools</h1>
            <p style="color:var(--ink-muted);font-size:16px;">Discover indie SaaS tools with powerful filters. Find exactly what you need.</p>
        </div>
        <form action="/search" method="GET" style="margin-bottom:24px;">
            <div style="display:flex;gap:8px;max-width:480px;">
                <input type="text" name="q" placeholder="Search tools..." class="form-input"
                    style="flex:1;border-radius:999px;padding:10px 20px;font-size:14px;">
                <button type="submit" class="btn btn-primary" style="padding:10px 20px;font-size:14px;">Search</button>
            </div>
        </form>
        {tag_pills_html}
        {filter_bar}
        {active_html}
        {results_section}
    </div>
    '''

    desc = "Browse and filter indie SaaS tools by category, tags, verification status, and price. Find the perfect indie alternative."
    return HTMLResponse(page_shell(title="Explore Indie Tools — Filter by Category, Tag, Price | IndieStack", body=body, description=desc, user=user, canonical="/explore"))

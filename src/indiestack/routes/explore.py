"""Unified explore page with faceted filtering."""

import json
from math import ceil
from html import escape
from urllib.parse import urlencode

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell, tool_card, pagination_html, email_sticky_bar
from indiestack.routes.category_icons import category_icon
from indiestack.db import explore_tools, get_all_categories, get_all_tags_with_counts, get_new_for_user, get_tool_by_slug, get_batch_success_rates

router = APIRouter()

# Per-category SEO meta descriptions — keyword-rich, mention IndieStack, under 160 chars with count inserted
_CAT_META: dict[str, str] = {
    "authentication": "Browse {count}+ authentication tools on IndieStack — OAuth, SSO, passkeys, and magic link auth solutions recommended by AI agents.",
    "payments": "Explore {count}+ payment tools on IndieStack — Stripe alternatives, billing, subscriptions, and checkout for indie developers.",
    "database": "Find {count}+ database tools on IndieStack — SQLite, Postgres, NoSQL, embedded DBs, and BaaS backends for your stack.",
    "analytics-metrics": "Discover {count}+ analytics tools on IndieStack — privacy-first, cookie-free alternatives to Google Analytics for developers.",
    "monitoring-uptime": "Browse {count}+ monitoring and uptime tools on IndieStack — status pages, alerting, and observability for indie projects.",
    "email-marketing": "Find {count}+ email tools on IndieStack — transactional APIs, newsletter platforms, and SMTP alternatives for developers.",
    "devops-infrastructure": "Explore {count}+ DevOps and infrastructure tools on IndieStack — CI/CD, deployment, and hosting solutions for indie developers.",
    "headless-cms": "Browse {count}+ headless CMS tools on IndieStack — API-first and git-based content management systems for developers.",
    "search-engine": "Discover {count}+ search engine tools on IndieStack — self-hosted and cloud search APIs. Meilisearch, Typesense, and more.",
    "testing-tools": "Find {count}+ testing tools on IndieStack — unit testing, E2E testing, and QA tools recommended by AI coding agents.",
}


@router.get("/explore", response_class=HTMLResponse)
async def explore(request: Request):
    user = request.state.user
    db = request.state.db

    # Parse query params
    q = request.query_params.get("q", "").strip()
    category = request.query_params.get("category", "")
    tag = request.query_params.get("tag", "")
    price = ""
    sort = request.query_params.get("sort", "hot")
    verified = ""
    ejectable = request.query_params.get("ejectable", "")
    source_type = request.query_params.get("source_type", "")
    compatible_with = request.query_params.get("compatible_with", "").strip()
    try:
        page = int(request.query_params.get("page", "1") or "1")
    except (ValueError, TypeError):
        page = 1

    # "New for you" personalized section (logged-in users only)
    new_for_you_html = ''
    if user and not any([category, tag, source_type, ejectable, q]) and page == 1:
        new_for_you = await get_new_for_user(db, user['id'], limit=6)
        if new_for_you:
            nfy_cards = ''.join(tool_card(t) for t in new_for_you)
            new_for_you_html = f'''
        <div style="margin-bottom:32px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;">
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>
                <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin:0;">New for you</h2>
                <span style="font-size:12px;color:var(--ink-muted);background:var(--cream-dark);padding:4px 10px;border-radius:999px;">Based on your bookmarks</span>
            </div>
            <div class="card-grid">{nfy_cards}</div>
            <div style="border-bottom:1px solid var(--border);margin-top:24px;"></div>
        </div>
        '''

    # Fetch filter data
    categories = await get_all_categories(db)
    tags = await get_all_tags_with_counts(db, min_count=1)

    # ── Visual category grid — shown when no filters active ──────────────
    if not any([q, category, tag, source_type, ejectable, compatible_with]):
        visible_cats = sorted(
            [c for c in categories if (c.get('tool_count') or 0) >= 10],
            key=lambda c: c.get('tool_count', 0) or 0, reverse=True
        )
        if len(visible_cats) < 8:
            visible_cats = sorted(categories, key=lambda c: c.get('tool_count', 0) or 0, reverse=True)[:12]
        cat_grid_items = ''
        for c in visible_cats:
            c_id = escape(str(c['id']))
            c_name = escape(str(c['name']))
            c_count = c.get('tool_count', 0) or 0
            icon_html = category_icon(str(c['slug']), size=28)
            cat_grid_items += (
                f'<a href="/explore?category={c_id}" style="display:flex;flex-direction:column;align-items:center;'
                f'gap:8px;padding:20px 12px;background:var(--card-bg);border:1px solid var(--border);'
                f'border-radius:var(--radius);text-decoration:none;text-align:center;'
                f'transition:border-color 0.15s,box-shadow 0.15s;"'
                f' onmouseover="this.style.borderColor=\'var(--slate)\';this.style.boxShadow=\'var(--shadow-md)\'"'
                f' onmouseout="this.style.borderColor=\'var(--border)\';this.style.boxShadow=\'none\'">'
                f'<span style="color:var(--slate);">{icon_html}</span>'
                f'<span style="font-size:13px;font-weight:600;color:var(--ink);">{c_name}</span>'
                f'<span style="font-size:11px;color:var(--ink-muted);">{c_count:,} tools</span>'
                f'</a>'
            )
        category_grid_html = (
            '<div style="margin-bottom:32px;">'
            '<h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin:0 0 16px 0;">Browse by category</h2>'
            '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;">'
            + cat_grid_items +
            '</div>'
            '</div>'
        )
    else:
        category_grid_html = ''

    per_page = 24
    # Validate compatible_with slug against real tools
    compat_tool = None
    if compatible_with:
        compat_tool = await get_tool_by_slug(db, compatible_with)
        if not compat_tool:
            compatible_with = ""  # Silently ignore invalid slugs

    results, total = await explore_tools(
        db,
        category_id=int(category) if category and category.isdigit() else None,
        tag=tag,
        price_filter=price,
        sort=sort,
        verified_only=bool(verified),
        ejectable_only=bool(ejectable),
        source_type=source_type if source_type in ("code", "saas") else "",
        query=q,
        compatible_with=compatible_with,
        page=page,
        per_page=per_page,
    )
    total_pages = ceil(total / per_page) if total else 0

    # Build base URL for pagination
    params = {}
    if q: params["q"] = q
    if category: params["category"] = category
    if tag: params["tag"] = tag
    if sort and sort != "hot": params["sort"] = sort
    if ejectable: params["ejectable"] = ejectable
    if source_type in ("code", "saas"): params["source_type"] = source_type
    if compatible_with: params["compatible_with"] = compatible_with
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
            is_active = tag.lower() == t['tag'].lower()
            pills.append(f'<a href="/explore?tag={t_slug}" class="pill-filter{" active" if is_active else ""}">{t_name} <span style="color:var(--ink-muted);font-size:11px;">({t["count"]})</span></a>')
        tag_pills_html = f'''
        <div style="margin-bottom:16px;">
            <div style="font-size:13px;font-weight:600;color:var(--ink-muted);margin-bottom:8px;">Popular Tags</div>
            <div style="display:flex;gap:8px;overflow-x:auto;padding-bottom:8px;-webkit-overflow-scrolling:touch;scrollbar-width:thin;">
                {"".join(pills)}
            </div>
        </div>
        '''

    price_pills = ''

    # Sort dropdown
    sort_options = ''
    for val, label in [("hot", "Hot"), ("trending", "Trending"), ("newest", "Newest"), ("upvotes", "Most Upvoted"), ("name", "A-Z")]:
        sel = ' selected' if val == sort else ''
        sort_options += f'<option value="{val}"{sel}>{label}</option>'

    # Source type tabs (All / Code / SaaS)
    source_type_pills = ''
    for val, label in [("", "All"), ("code", "Code"), ("saas", "SaaS")]:
        is_active = val == source_type
        source_type_pills += f'<button type="submit" name="source_type" value="{val}" class="pill-filter{" active" if is_active else ""}">{label}</button>'

    # Ejectable checkbox
    ejectable_checked = ' checked' if ejectable else ''

    # Active filter description
    active_filters = []
    if q:
        active_filters.append(f'Search: <strong>{escape(q)}</strong>')
    if tag:
        active_filters.append(f'Tag: <strong>{escape(tag)}</strong>')
    if category:
        for c in categories:
            if str(c['id']) == category:
                active_filters.append(f'Category: <strong>{escape(str(c["name"]))}</strong>')
                break
    if compatible_with and compat_tool:
        compat_name = escape(str(compat_tool['name']))
        # Build clear URL (current params minus compatible_with)
        clear_params = {k: v for k, v in params.items() if k != 'compatible_with'}
        clear_url = "/explore?" + urlencode(clear_params) if clear_params else "/explore"
        active_filters.append(
            f'Compatible with: <strong>{compat_name}</strong> '
            f'<a href="{clear_url}" style="color:var(--ink-muted);text-decoration:none;font-size:14px;" title="Clear filter">&times;</a>'
        )
    if ejectable:
        active_filters.append('<strong>Ejectable</strong>')
    if source_type == 'code':
        active_filters.append('<strong>Code (Open Source)</strong>')
    elif source_type == 'saas':
        active_filters.append('<strong>SaaS (Hosted)</strong>')

    active_html = ''
    if active_filters:
        active_html = f'''
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;flex-wrap:wrap;">
            <span style="font-size:13px;color:var(--ink-muted);">Filters:</span>
            {" &middot; ".join(active_filters)}
            <a href="/explore" style="font-size:12px;color:var(--ink-muted);text-decoration:underline;display:inline-flex;align-items:center;padding:10px 12px;min-height:44px;box-sizing:border-box;">Clear all</a>
        </div>
        '''

    escaped_query = escape(q, quote=True)
    filters_open = ' open' if (tag or source_type in ('code', 'saas') or ejectable) else ''

    filter_bar = f'''
    <form action="/explore" method="GET" style="margin-bottom:24px;">
        <input type="text" name="q" value="{escaped_query}" placeholder="Search tools..."
            aria-label="Search tools"
            style="width:100%;padding:12px 16px;border:1px solid var(--border);border-radius:8px;font-size:15px;background:var(--card-bg);color:var(--ink);font-family:var(--font-body);margin-bottom:16px;"
        />
        <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:12px;">
            <select name="category" class="form-select-pill" aria-label="Filter by category" onchange="this.form.submit()">
                {cat_options}
            </select>
            <select name="sort" class="form-select-pill" aria-label="Sort by" onchange="this.form.submit()">
                {sort_options}
            </select>
        </div>
        <details{filters_open} style="margin-top:12px;">
            <summary style="cursor:pointer;color:var(--accent);font-size:14px;font-weight:500;">
                More filters &#9662;
            </summary>
            <div style="margin-top:12px;">
                <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:12px;">
                    <div style="display:flex;gap:8px;">
                        {source_type_pills}
                    </div>
                    <label style="display:flex;align-items:center;gap:4px;font-size:13px;color:var(--ink-light);cursor:pointer;">
                        <input type="checkbox" name="ejectable" value="1"{ejectable_checked} onchange="this.form.submit()" class="custom-checkbox">
                        Ejectable
                    </label>
                </div>
                {tag_pills_html}
            </div>
        </details>
        {"<input type='hidden' name='tag' value='" + escape(tag) + "'>" if tag else ""}
        {"<input type='hidden' name='source_type' value='" + escape(source_type) + "'>" if source_type in ("code", "saas") else ""}
    </form>
    '''

    # Banner — signup CTA for logged-out, newsletter for logged-in
    if not user:
        mid_page_banner = '''
        <div style="background:linear-gradient(135deg,var(--terracotta),var(--terracotta-dark));border-radius:var(--radius);padding:32px;
            margin:32px 0;text-align:center;color:#fff;">
            <h3 style="font-family:var(--font-display);font-size:22px;margin:0 0 8px;">
                Track the tools AI agents actually recommend
            </h3>
            <p style="color:rgba(255,255,255,0.7);font-size:14px;margin:0 0 20px;">
                Create a free account to save tools and get AI-powered recommendations.
            </p>
            <a href="/signup?next=/explore" style="display:inline-block;padding:14px 32px;background:var(--slate);color:var(--terracotta);
                border-radius:999px;font-weight:700;font-size:15px;text-decoration:none;">
                Sign Up Free &rarr;
            </a>
        </div>'''
    else:
        mid_page_banner = """
        <div style="background:linear-gradient(135deg,var(--terracotta),var(--terracotta-dark));border-radius:var(--radius);padding:32px;
            margin:32px 0;text-align:center;color:#fff;">
            <h3 style="font-family:var(--font-display);font-size:24px;margin-bottom:8px;">
                Get the best developer tools in your inbox
            </h3>
            <p style="color:rgba(255,255,255,0.7);font-size:14px;margin-bottom:24px;">
                Weekly curated picks, new launches, and maker stories.
            </p>
            <form id="explore-subscribe" style="display:flex;gap:8px;max-width:400px;margin:0 auto;flex-wrap:wrap;justify-content:center;"
                  onsubmit="event.preventDefault();var f=this;var em=f.email.value;fetch('/api/subscribe',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'email='+encodeURIComponent(em)}).then(function(){f.innerHTML='<p style=&quot;color:var(--success-text);font-weight:600;font-size:16px;&quot;>You\\'re in! Check your inbox.</p>'}).catch(function(){f.innerHTML='<p style=&quot;color:var(--danger);&quot;>Something went wrong. Try again.</p>'})">
                <input type="email" name="email" placeholder="you@example.com" required
                    aria-label="Email address"
                    style="flex:1;min-width:200px;padding:12px 16px;border:none;border-radius:999px;font-size:14px;
                        font-family:inherit;">
                <button type="submit" style="background:var(--slate);color:var(--terracotta);border:none;padding:12px 24px;
                    min-height:44px;border-radius:999px;font-weight:700;font-size:14px;cursor:pointer;white-space:nowrap;">
                    Subscribe Free
                </button>
            </form>
        </div>
        """

    # Inject agent success rates for trust badges
    try:
        slugs = [str(r.get('slug', '')) for r in results if r.get('slug')]
        if slugs:
            sr_map = await get_batch_success_rates(db, slugs)
            for r in results:
                s = str(r.get('slug', ''))
                if s in sr_map:
                    r['_success_rate'] = sr_map[s]
    except Exception:
        pass

    # Results
    if results:
        cards_html = "".join(tool_card(t) for t in results)
        result_label = f'{total} tool{"s" if total != 1 else ""}'
        results_section = f'''
        <p style="font-size:14px;color:var(--ink-muted);margin-bottom:16px;">{result_label}</p>
        <div class="card-grid card-stagger">{cards_html}</div>
        {pagination_html(page, total_pages, base_url)}
        {mid_page_banner}
        '''
    else:
        results_section = '''
        <div style="text-align:center;padding:64px 0;">
            <div style="margin-bottom:12px;"><svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg></div>
            <p style="color:var(--ink-muted);font-size:16px;">No tools match your filters.</p>
            <a href="/explore" class="btn btn-secondary mt-4">Clear filters</a>
        </div>
        '''

    body = f'''
    <div class="container" style="padding:48px 24px;overflow-x:hidden;">
        <div style="margin-bottom:32px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin-bottom:8px;">Explore</h1>
            <p style="color:var(--ink-muted);font-size:16px;">Community-curated catalog of developer tools. Makers can <a href="/submit" style="color:var(--accent);">claim their listing</a> to update details and verify ownership.</p>
        </div>
        <a href="/surprise" style="display:inline-flex;align-items:center;gap:6px;padding:10px 20px;
            background:var(--cream-dark);border:1px solid var(--border);border-radius:999px;
            color:var(--ink-light);font-size:14px;font-weight:500;text-decoration:none;
            transition:all 0.2s;margin-bottom:16px;"
            onmouseover="this.style.background='var(--accent)';this.style.color='#fff';this.style.borderColor='var(--accent)'"
            onmouseout="this.style.background='var(--cream-dark)';this.style.color='var(--ink-light)';this.style.borderColor='var(--border)'">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><rect x="2" y="2" width="20" height="20" rx="5"/><circle cx="8" cy="8" r="1.5" fill="currentColor"/><circle cx="16" cy="16" r="1.5" fill="currentColor"/></svg> Surprise me
        </a>
        {category_grid_html}
        {filter_bar}
        {active_html}
        {new_for_you_html}
        {results_section}
    </div>
    '''

    # Build category-specific meta if a category filter is active
    _active_cat_obj = None
    if category:
        for _c in categories:
            if str(_c['id']) == category:
                _active_cat_obj = _c
                break

    if _active_cat_obj:
        _c_slug = str(_active_cat_obj.get('slug', ''))
        _c_name = str(_active_cat_obj.get('name', 'Tools'))
        _c_count = _active_cat_obj.get('tool_count', 0) or 0
        if _c_slug in _CAT_META:
            desc = _CAT_META[_c_slug].format(count=_c_count)
        else:
            desc = f"Browse {_c_count}+ {_c_name} tools on IndieStack — curated developer tools discoverable by AI coding agents."
        explore_page_title = f"{_c_name} Tools — {_c_count}+ Options | IndieStack"
        explore_canonical = f"/explore?category={category}"
    else:
        desc = "Browse and filter 8,000+ developer tools by category, tag, type, and compatibility. Find the right auth, payments, analytics, or email tool for your stack."
        explore_page_title = "Explore 8,000+ Developer Tools by Category | IndieStack"
        explore_canonical = "/explore"

    explore_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Explore Developer Tools",
        "description": desc,
        "url": f"{BASE_URL}/explore",
        "isPartOf": {"@type": "WebSite", "name": "IndieStack", "url": BASE_URL},
        "numberOfItems": total,
    }, ensure_ascii=False)
    explore_head = f'<script type="application/ld+json">{explore_ld}</script>'
    response = HTMLResponse(page_shell(title=explore_page_title, body=body + email_sticky_bar(), description=desc, user=user, canonical=explore_canonical, extra_head=explore_head))
    response.headers["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"
    return response


@router.get("/surprise", response_class=RedirectResponse)
async def surprise(request: Request):
    db = request.state.db
    row = await db.execute("SELECT slug FROM tools WHERE status='approved' ORDER BY RANDOM() LIMIT 1")
    tool = await row.fetchone()
    if tool:
        return RedirectResponse(f"/tool/{tool['slug']}", status_code=302)
    return RedirectResponse("/explore", status_code=302)

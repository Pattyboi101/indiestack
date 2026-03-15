"""Use Case comparison pages — dual-audience (HTML for humans, JSON-LD for agents)."""

import json
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, Response

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell, tool_card
from indiestack.db import (
    get_all_categories, get_category_by_slug, get_tools_by_category,
    search_tools, CATEGORY_TOKEN_COSTS, NEED_MAPPINGS,
)

router = APIRouter()


def _get_all_use_cases():
    """Build combined list: curated USE_CASES + auto-generated from categories."""
    return NEED_MAPPINGS


async def _get_tools_for_use_case(db, slug: str, limit: int = 10):
    """Fetch tools for a use case — by category first, then FTS5 fallback."""
    mapping = NEED_MAPPINGS.get(slug)
    tools = []

    if mapping:
        cat = await get_category_by_slug(db, mapping["category"])
        if cat:
            rows, _ = await get_tools_by_category(db, cat['id'], page=1, per_page=limit)
            tools = list(rows)

        # Supplement with search if needed
        if len(tools) < 3:
            for term in mapping.get("terms", [slug]):
                if len(tools) >= limit:
                    break
                found = await search_tools(db, term, limit=limit)
                existing_ids = {t['id'] for t in tools}
                for f in found:
                    if f['id'] not in existing_ids and len(tools) < limit:
                        tools.append(f)
                        existing_ids.add(f['id'])
    else:
        # Try as a category slug directly
        cat = await get_category_by_slug(db, slug)
        if cat:
            rows, _ = await get_tools_by_category(db, cat['id'], page=1, per_page=limit)
            tools = list(rows)

    return tools


def _use_case_card(slug: str, uc: dict, tool_count: int = 0) -> str:
    """Render a use case card for the index page."""
    icon = uc.get("icon", "\U0001f527")
    title = escape(uc.get("title", slug.title()))
    desc = escape(uc.get("description", ""))
    tokens = CATEGORY_TOKEN_COSTS.get(uc.get("category", ""), 50_000)
    return f'''
    <a href="/use-cases/{escape(slug)}" class="card" style="display:block;text-decoration:none;padding:24px;transition:transform 0.15s;">
        <div style="font-size:28px;margin-bottom:8px;">{icon}</div>
        <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin:0 0 8px;">{title}</h3>
        <p style="color:var(--ink-muted);font-size:13px;line-height:1.5;margin:0 0 8px;">{desc}</p>
        <div style="display:flex;gap:12px;font-size:12px;color:var(--ink-muted);">
            <span>{tool_count} tools</span>
            <span>{tokens:,} tokens saved</span>
        </div>
    </a>
    '''


def _comparison_row(tool: dict) -> str:
    """Render a row in the comparison table."""
    pp = tool.get('price_pence')
    price = f"\u00a3{pp/100:.2f}/mo" if pp and pp > 0 else '<span style="color:var(--accent);">Free</span>'
    upvotes = int(tool.get('upvote_count', 0))
    replaces = escape(tool.get('replaces', '') or '')
    name = escape(tool['name'])
    slug = escape(tool['slug'])
    tagline = escape(tool.get('tagline', ''))

    return f'''
    <tr>
        <td style="padding:12px;">
            <a href="/tool/{slug}" style="color:var(--ink);font-weight:600;text-decoration:none;">{name}</a>
            <div style="font-size:12px;color:var(--ink-muted);margin-top:2px;">{tagline}</div>
        </td>
        <td style="padding:12px;text-align:center;">{price}</td>
        <td style="padding:12px;text-align:center;">{upvotes}</td>
        <td style="padding:12px;font-size:12px;color:var(--ink-muted);">{replaces}</td>
    </tr>
    '''


# ── Index page ────────────────────────────────────────────────────────────

@router.get("/use-cases", response_class=HTMLResponse)
async def use_cases_index(request: Request):
    db = request.state.db
    user = request.state.user
    use_cases = _get_all_use_cases()

    # Get tool counts per category for display
    categories = await get_all_categories(db)
    cat_counts = {c['slug']: int(c.get('tool_count', 0)) for c in categories}

    cards_html = ""
    for slug, uc in sorted(use_cases.items(), key=lambda x: x[1].get("title", "")):
        count = cat_counts.get(uc.get("category", ""), 0)
        cards_html += _use_case_card(slug, uc, tool_count=count)

    body = f'''
    <div class="container" style="max-width:900px;padding:48px 24px;">
        <div style="text-align:center;margin-bottom:32px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin:0 0 8px;">
                Use Cases
            </h1>
            <p style="color:var(--ink-muted);font-size:16px;max-width:560px;margin:0 auto;">
                Compare developer tools by use case. Each page shows the best tools, token savings, and build-vs-buy analysis.
            </p>
        </div>

        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;">
            {cards_html}
        </div>

        <div style="text-align:center;margin-top:40px;">
            <p style="color:var(--ink-muted);font-size:14px;">Need a full stack?</p>
            <a href="/stacks" class="btn btn-primary" style="margin-top:8px;">Browse Vibe Stacks &rarr;</a>
        </div>
    </div>
    '''

    return HTMLResponse(page_shell(
        "Use Cases — Compare Developer Tools",
        body,
        user=user,
        description="Compare indie developer tools by use case. Authentication, payments, analytics, and more.",
        canonical=f"{BASE_URL}/use-cases",
    ))


# ── Detail page ───────────────────────────────────────────────────────────

@router.get("/use-cases/{slug}", response_class=HTMLResponse)
async def use_case_detail(request: Request, slug: str):
    db = request.state.db
    user = request.state.user

    # Resolve use case (curated or category fallback)
    uc = NEED_MAPPINGS.get(slug)
    if not uc:
        # Try as category slug
        cat = await get_category_by_slug(db, slug)
        if not cat:
            return Response(status_code=404)
        uc = {
            "title": cat['name'],
            "description": f"Discover indie {cat['name'].lower()} tools on IndieStack.",
            "category": cat['slug'],
            "competitors": [],
            "build_estimate": "varies",
            "icon": "\U0001f527",
            "terms": [],
        }

    tools = await _get_tools_for_use_case(db, slug)
    title = uc.get("title", slug.title())
    icon = uc.get("icon", "\U0001f527")
    description = uc.get("description", "")
    build_estimate = uc.get("build_estimate", "varies")
    competitors = uc.get("competitors", [])
    category_slug = uc.get("category", "")
    tokens_saved = CATEGORY_TOKEN_COSTS.get(category_slug, 50_000)
    # Comparison table rows
    table_rows = "".join(_comparison_row(t) for t in tools)
    if not table_rows:
        table_rows = '<tr><td colspan="5" style="padding:24px;text-align:center;color:var(--ink-muted);">No tools found for this use case yet.</td></tr>'

    # Competitors section
    competitors_html = ""
    if competitors:
        comp_links = " ".join(
            f'<a href="/alternatives/{escape(c.lower().replace(" ", "-"))}" class="badge badge-muted" style="text-decoration:none;">{escape(c)}</a>'
            for c in competitors
        )
        competitors_html = f'''
        <div style="margin-top:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:12px;">
                Replaces
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:12px;">
                These developer tools are alternatives to:
            </p>
            <div style="display:flex;flex-wrap:wrap;gap:8px;">{comp_links}</div>
        </div>
        '''

    # JSON-LD
    json_ld_items = []
    for i, t in enumerate(tools):
        pp = t.get('price_pence')
        price_str = f"{pp/100:.2f}" if pp and pp > 0 else "0"
        json_ld_items.append({
            "@type": "ListItem",
            "position": i + 1,
            "item": {
                "@type": "SoftwareApplication",
                "name": t['name'],
                "url": f"{BASE_URL}/tool/{t['slug']}",
                "applicationCategory": title,
                "offers": {"@type": "Offer", "price": price_str, "priceCurrency": "GBP"},
            }
        })

    json_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Best Indie {title} Tools",
        "description": description,
        "numberOfItems": len(tools),
        "itemListElement": json_ld_items,
    })

    breadcrumb_ld = json.dumps({
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Home", "item": BASE_URL},
            {"@type": "ListItem", "position": 2, "name": "Use Cases", "item": f"{BASE_URL}/use-cases"},
            {"@type": "ListItem", "position": 3, "name": title},
        ]
    })

    extra_head = f'''
    <script type="application/ld+json">{json_ld}</script>
    <script type="application/ld+json">{breadcrumb_ld}</script>
    '''

    body = f'''
    <div class="container" style="max-width:860px;padding:48px 24px;">
        <!-- Breadcrumbs -->
        <nav style="font-size:13px;color:var(--ink-muted);margin-bottom:24px;">
            <a href="/" style="color:var(--ink-muted);text-decoration:none;">Home</a>
            <span style="margin:0 8px;">/</span>
            <a href="/use-cases" style="color:var(--ink-muted);text-decoration:none;">Use Cases</a>
            <span style="margin:0 8px;">/</span>
            <span style="color:var(--ink);">{escape(title)}</span>
        </nav>

        <!-- Hero -->
        <div style="text-align:center;margin-bottom:32px;">
            <div style="font-size:48px;margin-bottom:12px;">{icon}</div>
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin:0 0 8px;">
                {escape(title)}
            </h1>
            <p style="color:var(--ink-muted);font-size:16px;max-width:520px;margin:0 auto;">
                {escape(description)}
            </p>
        </div>

        <!-- Stats bar -->
        <div style="display:flex;justify-content:center;gap:32px;margin-bottom:32px;flex-wrap:wrap;">
            <div style="text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--slate);">{len(tools)}</div>
                <div style="font-size:12px;color:var(--ink-muted);">developer tools</div>
            </div>
            <div style="text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--slate);">{tokens_saved:,}</div>
                <div style="font-size:12px;color:var(--ink-muted);">tokens saved</div>
            </div>
        </div>

        <!-- Build vs Buy -->
        <div class="card" style="padding:24px;border-left:3px solid var(--accent);margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin:0 0 8px;">
                Build vs Buy
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;line-height:1.6;margin:0;">
                Building {escape(title.lower())} from scratch takes roughly <strong>{escape(build_estimate)}</strong>
                and ~<strong>{tokens_saved:,} tokens</strong> of AI-assisted development. Or use one of these developer tools
                and ship today.
            </p>
        </div>

        <!-- Comparison table -->
        <div style="overflow-x:auto;">
            <table style="width:100%;border-collapse:collapse;font-size:14px;">
                <thead>
                    <tr style="border-bottom:2px solid var(--border);text-align:left;">
                        <th style="padding:12px;font-weight:600;color:var(--ink);">Tool</th>
                        <th style="padding:12px;text-align:center;font-weight:600;color:var(--ink);">Price</th>
                        <th style="padding:12px;text-align:center;font-weight:600;color:var(--ink);">Upvotes</th>
                        <th style="padding:12px;font-weight:600;color:var(--ink);">Replaces</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>

        {competitors_html}

        <!-- CTA -->
        <div style="text-align:center;margin-top:40px;">
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:12px;">Need more than just {escape(title.lower())}?</p>
            <a href="/stacks" class="btn btn-primary" style="padding:14px 28px;font-size:16px;">
                Build Your Full Stack &rarr;
            </a>
        </div>
    </div>
    '''

    return HTMLResponse(page_shell(
        f"Best Indie {title} Tools",
        body,
        user=user,
        description=f"Compare {len(tools)} indie {title.lower()} tools. {description}",
        extra_head=extra_head,
        canonical=f"{BASE_URL}/use-cases/{slug}",
    ))

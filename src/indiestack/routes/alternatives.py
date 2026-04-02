"""Programmatic 'alternatives to X' pages for SEO."""

import json as _json
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell, tool_card
from indiestack.db import get_tools_replacing, get_all_competitors, slugify, get_sponsored_for_competitor

router = APIRouter()


def _alt_health_badge(status: str) -> str:
    """Render a colored health-status pill for alternatives pages."""
    colors = {
        'active': ('var(--success-bg, #D1FAE5)', 'var(--success-text, #065F46)'),
        'stale': ('#FEF3C7', '#92400E'),
        'dead': ('#FEE2E2', '#991B1B'),
    }
    bg, fg = colors.get(status, ('#F3F4F6', '#6B7280'))
    label = escape(status.capitalize()) if status else 'Unknown'
    return (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;'
        f'font-size:12px;font-weight:600;background:{bg};color:{fg};">{label}</span>'
    )


def _alt_github_stars(tool: dict) -> str:
    """Render GitHub stars badge if available."""
    stars = tool.get('github_stars')
    if not stars or int(stars) <= 0:
        return ''
    star_count = int(stars)
    github_url = tool.get('github_url', '')
    inner = f'{star_count:,}'
    if github_url:
        return (
            f'<a href="{escape(str(github_url))}" target="_blank" rel="noopener" '
            f'style="display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;'
            f'font-weight:600;background:var(--cream-dark);color:var(--ink);text-decoration:none;'
            f'border:1px solid var(--border);">&#9733; {inner}</a>'
        )
    return (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;'
        f'font-weight:600;background:var(--cream-dark);color:var(--ink);border:1px solid var(--border);">'
        f'&#9733; {inner}</span>'
    )


def _alt_agent_citations(tool: dict) -> str:
    """Render agent citation badge if mcp_view_count > 0."""
    mcp_views = tool.get('mcp_view_count')
    if not mcp_views or int(mcp_views) <= 0:
        return ''
    count = int(mcp_views)
    return (
        f'<span style="display:inline-block;padding:3px 10px;border-radius:999px;font-size:12px;'
        f'font-weight:600;background:#EDE9FE;color:#7C3AED;">'
        f'AI agents recommend this {count:,} time{"s" if count != 1 else ""}</span>'
    )


@router.get("/compare", response_class=HTMLResponse)
async def compare_index(request: Request):
    """SEO index page listing all tool-vs-competitor comparison pairs, grouped by category."""
    db = request.state.db

    # Get all approved tools that have a replaces field, with their category
    cursor = await db.execute(
        """SELECT t.id, t.name, t.slug, t.replaces, t.category_id,
                  c.name as category_name, c.slug as category_slug
           FROM tools t
           JOIN categories c ON c.id = t.category_id
           WHERE t.status = 'approved' AND t.replaces != '' AND t.replaces IS NOT NULL
           ORDER BY c.name, t.name"""
    )
    rows = await cursor.fetchall()
    tools = [dict(r) for r in rows]

    # Build pairs: for each tool, create a (competitor, tool) pair
    # Group by category
    from collections import defaultdict
    categories = defaultdict(list)  # category_name -> list of (competitor_name, competitor_slug, tool_name, tool_slug)

    for t in tools:
        replaces = t.get('replaces', '') or ''
        for comp in replaces.split(','):
            comp = comp.strip()
            if comp:
                comp_slug = slugify(comp)
                categories[t['category_name']].append(
                    (comp, comp_slug, t['name'], t['slug'])
                )

    # Deduplicate and limit to 10 pairs per category
    category_count = 0
    total_pairs = 0
    sections_html = ''

    for cat_name in sorted(categories.keys()):
        pairs = categories[cat_name]
        # Deduplicate by (competitor_slug, tool_slug)
        seen = set()
        unique_pairs = []
        for comp_name, comp_slug, tool_name, tool_slug in pairs:
            key = (comp_slug, tool_slug)
            if key not in seen:
                seen.add(key)
                unique_pairs.append((comp_name, comp_slug, tool_name, tool_slug))

        if len(unique_pairs) < 1:
            continue

        category_count += 1
        # Limit to top 10 pairs per category
        display_pairs = unique_pairs[:10]
        total_pairs += len(display_pairs)

        pills = ''
        for comp_name, comp_slug, tool_name, tool_slug in display_pairs:
            safe_comp = escape(comp_name)
            safe_tool = escape(tool_name)
            pills += f'''<a href="/alternatives/{escape(comp_slug)}/vs/{escape(tool_slug)}"
                style="display:inline-block;padding:8px 16px;background:var(--cream-dark);border:1px solid var(--border);
                border-radius:var(--radius-sm);font-size:13px;color:var(--ink);text-decoration:none;font-weight:500;
                transition:border-color 0.15s,box-shadow 0.15s;"
                onmouseover="this.style.borderColor='var(--accent)';this.style.boxShadow='var(--shadow-sm)'"
                onmouseout="this.style.borderColor='var(--border)';this.style.boxShadow='none'"
                >{safe_comp} vs {safe_tool}</a>\n'''

        safe_cat = escape(cat_name)
        sections_html += f'''
        <div style="margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
                {safe_cat}
            </h2>
            <div style="display:flex;flex-wrap:wrap;gap:8px;">
                {pills}
            </div>
        </div>'''

    if not sections_html:
        body = """
        <div class="container" style="text-align:center;padding:80px 24px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);">Tool Comparisons</h1>
            <p style="color:var(--ink-muted);margin-top:12px;">No comparisons available yet.</p>
        </div>
        """
        return HTMLResponse(page_shell("Tool Comparisons — IndieStack", body, user=request.state.user))

    # JSON-LD CollectionPage
    jsonld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Tool Comparisons — IndieStack",
        "description": f"Side-by-side comparisons of developer tools across {category_count} categories. {total_pairs} comparison pages.",
        "url": f"{BASE_URL}/compare",
    }
    jsonld_script = f'<script type="application/ld+json">{_json.dumps(jsonld)}</script>'

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:960px;">
        <div style="text-align:center;margin-bottom:48px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);">
                Tool Comparisons
            </h1>
            <p style="color:var(--ink-muted);font-size:17px;margin-top:12px;max-width:600px;margin-left:auto;margin-right:auto;">
                Side-by-side comparisons of developer tools across {category_count} categories.
                Find the best alternative for your stack.
            </p>
            <a href="/alternatives" style="color:var(--ink-muted);font-size:14px;font-weight:600;margin-top:12px;display:inline-block;">
                &larr; Back to Alternatives
            </a>
        </div>

        {sections_html}

        <div style="text-align:center;margin-top:48px;padding:32px;background:var(--cream-dark);border-radius:var(--radius);">
            <p style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                Don&rsquo;t see your tool?
            </p>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                Submit it for free and get listed on comparison pages.
            </p>
            <a href="/submit" class="btn btn-primary">Submit Your Tool &rarr;</a>
        </div>
    </div>
    """
    return HTMLResponse(page_shell(
        "Tool Comparisons — IndieStack", body,
        description=f"Browse {total_pairs} side-by-side comparisons of developer tools across {category_count} categories. Find the best alternative for your stack.",
        user=request.state.user, canonical="/compare",
        extra_head=jsonld_script,
    ))


@router.get("/alternatives", response_class=HTMLResponse)
async def alternatives_index(request: Request):
    """List all competitors that IndieStack tools can replace."""
    db = request.state.db
    competitors = await get_all_competitors(db)

    if not competitors:
        body = """
        <div class="container" style="text-align:center;padding:80px 24px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);">Indie Alternatives</h1>
            <p style="color:var(--ink-muted);margin-top:12px;">No alternatives listed yet. Makers can add the big-tech tools they replace when submitting.</p>
            <a href="/submit" class="btn btn-primary mt-8">Submit Your Tool</a>
        </div>
        """
        return HTMLResponse(page_shell("Indie Alternatives", body, user=request.state.user))

    # Get tool counts per competitor
    comp_counts = {}
    for comp in competitors:
        comp_tools = await get_tools_replacing(db, comp, limit=100)
        comp_counts[comp] = len(comp_tools)

    # Build grid of competitor pills
    pills_html = ''
    for comp in competitors:
        comp_slug = slugify(comp)
        pills_html += f"""
        <a href="/alternatives/{escape(comp_slug)}" class="card"
           style="text-decoration:none;color:inherit;padding:16px 20px;display:flex;align-items:center;gap:12px;">
            <span style="color:var(--slate);display:inline-block;"><svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg></span>
            <div>
                <div style="font-family:var(--font-display);font-size:16px;color:var(--ink);">{escape(comp)} alternatives</div>
                <div style="font-size:13px;color:var(--ink-muted);">{comp_counts.get(comp, 0)} developer tools</div>
            </div>
        </a>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:900px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);">
                Indie Alternatives to Big Tech
            </h1>
            <p style="color:var(--ink-muted);font-size:17px;margin-top:12px;max-width:560px;margin-left:auto;margin-right:auto;">
                Looking for an alternative to expensive software?
                These developer tools offer the same features &mdash; with better pricing, more flexibility,
                and personal support from the makers who built them.
            </p>
        </div>
        <div class="card-grid">{pills_html}</div>

        <div style="text-align:center;margin-top:24px;">
            <a href="/compare" style="color:var(--ink-muted);font-size:14px;font-weight:600;text-decoration:none;">
                View all comparisons &rarr;
            </a>
        </div>

        <div style="text-align:center;margin-top:48px;padding:32px;background:var(--cream-dark);border-radius:var(--radius);">
            <p style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                Know an indie alternative we&rsquo;re missing?
            </p>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                Submit it for free and help others discover better tools.
            </p>
            <a href="/submit" class="btn btn-primary">Submit Your Tool &rarr;</a>
        </div>
    </div>
    """
    alt_ld = _json.dumps({
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": "Indie Alternatives to Mainstream SaaS",
        "description": "Side-by-side comparisons of developer tools across categories.",
        "url": f"{BASE_URL}/alternatives",
        "isPartOf": {"@type": "WebSite", "name": "IndieStack", "url": BASE_URL},
    }, ensure_ascii=False)
    alt_head = f'<script type="application/ld+json">{alt_ld}</script>'

    return HTMLResponse(page_shell("Indie Alternatives to Big Tech", body,
                                   description="Discover indie SaaS alternatives to popular big-tech tools. Save money, support indie makers.",
                                   user=request.state.user, canonical="/alternatives",
                                   extra_head=alt_head))


def _stackshare_comparison_page(request: Request) -> HTMLResponse:
    """Render a custom IndieStack vs StackShare comparison landing page."""
    jsonld = _json.dumps({
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": "IndieStack vs StackShare — AI-Native Developer Tool Discovery",
        "description": "Compare IndieStack and StackShare. IndieStack uses agent-verified data, not stale self-reports. Free MCP server for Claude, Cursor, and Windsurf.",
        "url": f"{BASE_URL}/alternatives/stackshare",
    }, ensure_ascii=False)
    jsonld_script = f'<script type="application/ld+json">{jsonld}</script>'

    body = """
    <div class="container" style="padding:48px 24px;max-width:860px;">

        <!-- Breadcrumb -->
        <div style="margin-bottom:8px;">
            <a href="/alternatives" style="color:var(--ink-muted);font-size:14px;font-weight:600;">&larr; All Alternatives</a>
        </div>

        <!-- Hero -->
        <div style="margin-bottom:48px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);margin-bottom:12px;">
                IndieStack vs StackShare
            </h1>
            <p style="color:var(--ink-muted);font-size:18px;max-width:600px;line-height:1.6;">
                StackShare shows what devs <em>say</em> they use. IndieStack shows what actually works.
            </p>
        </div>

        <!-- Comparison table -->
        <div class="card" style="padding:0;overflow:hidden;margin-bottom:48px;">
            <div style="overflow-x:auto;">
                <table style="width:100%;border-collapse:collapse;font-size:14px;">
                    <thead>
                        <tr style="background:var(--cream-dark);">
                            <th style="text-align:left;padding:14px 20px;font-family:var(--font-display);font-size:15px;color:var(--ink);border-bottom:1px solid var(--border);width:35%;">Feature</th>
                            <th style="text-align:left;padding:14px 20px;font-size:13px;color:var(--ink-muted);border-bottom:1px solid var(--border);font-weight:600;width:32.5%;">StackShare</th>
                            <th style="text-align:left;padding:14px 20px;font-size:13px;color:var(--accent);border-bottom:1px solid var(--border);font-weight:700;width:32.5%;">IndieStack</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);font-weight:600;color:var(--ink);">Data source</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink-muted);">Self-reported (stale)</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink);">Agent-verified (live)</td>
                        </tr>
                        <tr>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);font-weight:600;color:var(--ink);">AI integration</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink-muted);">None</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink);">MCP server for all agents</td>
                        </tr>
                        <tr>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);font-weight:600;color:var(--ink);">Tool count</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink-muted);">7,000</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink);">8,000+ (indie-focused)</td>
                        </tr>
                        <tr>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);font-weight:600;color:var(--ink);">Compatibility data</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink-muted);">None (just lists)</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink);">Verified pairs + conflict detection</td>
                        </tr>
                        <tr>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);font-weight:600;color:var(--ink);">Health monitoring</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink-muted);">None</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink);">Active/stale/dead tracking</td>
                        </tr>
                        <tr>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);font-weight:600;color:var(--ink);">Success rates</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink-muted);">None</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink);">Agent outcome tracking</td>
                        </tr>
                        <tr>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);font-weight:600;color:var(--ink);">Last updated</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink-muted);">2024 (acquired by FOSSA)</td>
                            <td style="padding:12px 20px;border-bottom:1px solid var(--border);color:var(--ink);">Updated daily</td>
                        </tr>
                        <tr>
                            <td style="padding:12px 20px;font-weight:600;color:var(--ink);">API</td>
                            <td style="padding:12px 20px;color:var(--ink-muted);">Dead ($99/mo, closed beta)</td>
                            <td style="padding:12px 20px;color:var(--ink);">Free MCP server</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- CTA: MCP Server -->
        <div style="margin-bottom:48px;padding:32px;background:var(--cream-dark);border-radius:var(--radius);border:1px solid var(--border);">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
                Install the MCP Server
            </h2>
            <p style="color:var(--ink-muted);font-size:15px;margin-bottom:20px;line-height:1.6;">
                Give your AI agent access to 8,000+ developer tools. Works with Claude, Cursor, and Windsurf.
            </p>
            <div style="background:var(--ink);border-radius:var(--radius-sm);padding:16px 20px;overflow-x:auto;">
                <code style="font-family:var(--font-mono);font-size:14px;color:var(--accent);white-space:nowrap;">claude mcp add indiestack -- uvx --from indiestack indiestack-mcp</code>
            </div>
        </div>

        <!-- CTA: Explore -->
        <div style="text-align:center;padding:32px;background:var(--cream-dark);border-radius:var(--radius);">
            <p style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                See what&rsquo;s in the database
            </p>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                Browse 8,000+ indie developer tools across 40+ categories.
            </p>
            <a href="/explore" class="btn btn-primary">Explore Tools &rarr;</a>
        </div>
    </div>
    """

    return HTMLResponse(page_shell(
        "IndieStack vs StackShare — AI-Native Developer Tool Discovery",
        body,
        description="Compare IndieStack and StackShare. IndieStack uses agent-verified data, not stale self-reports. Free MCP server for Claude, Cursor, and Windsurf.",
        user=request.state.user,
        canonical="/alternatives/stackshare",
        extra_head=jsonld_script,
    ))


@router.get("/alternatives/{competitor_slug}", response_class=HTMLResponse)
async def alternatives_for(request: Request, competitor_slug: str):
    """Show all developer tools that replace a specific competitor."""
    # Special case: StackShare is a platform, not a tool in our DB
    if competitor_slug == "stackshare":
        return _stackshare_comparison_page(request)

    db = request.state.db

    # Reconstruct competitor name from slug — search broadly
    # Try to find the original name from the database
    all_competitors = await get_all_competitors(db)
    competitor_name = competitor_slug.replace('-', ' ').title()
    for comp in all_competitors:
        if slugify(comp) == competitor_slug:
            competitor_name = comp
            break

    tools = await get_tools_replacing(db, competitor_name, limit=20)

    # Also try slug-based matching if no results
    if not tools:
        tools = await get_tools_replacing(db, competitor_slug.replace('-', ' '), limit=20)

    if not tools:
        body = f"""
        <div class="container" style="text-align:center;padding:80px 24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">
                No alternatives to {escape(competitor_name)} yet
            </h1>
            <p style="color:var(--ink-muted);margin-top:12px;max-width:480px;margin-left:auto;margin-right:auto;">
                We don&rsquo;t have any indie alternatives to {escape(competitor_name)} listed yet.
                If your tool replaces {escape(competitor_name)}, list it now!
            </p>
            <a href="/submit" class="btn btn-primary mt-8">Submit Your Tool</a>
        </div>
        """
        return HTMLResponse(page_shell(f"Alternatives to {competitor_name}", body,
                                       user=request.state.user,
                                       extra_head='<meta name="robots" content="noindex">'))

    safe_name = escape(competitor_name)

    # Get sponsored placements for this competitor
    sponsored = await get_sponsored_for_competitor(db, competitor_slug)

    sponsored_html = ''
    if sponsored:
        for sp in sponsored:
            sp_name = escape(str(sp['name']))
            sp_slug = escape(str(sp['slug']))
            sp_tagline = escape(str(sp.get('tagline', '')))
            sp_label = escape(str(sp.get('label', 'Sponsored')))
            sp_price = sp.get('price_pence')
            if sp_price is not None and isinstance(sp_price, int) and sp_price > 0:
                price_text = f'From &pound;{sp_price/100:.0f}/mo'
            else:
                price_text = 'Free'

            sponsored_html += f"""
            <a href="/tool/{sp_slug}" class="card" style="text-decoration:none;color:inherit;display:block;
                border:2px solid var(--slate);background:linear-gradient(135deg,var(--cream),#fff);position:relative;overflow:hidden;">
                <div style="position:absolute;top:12px;right:12px;">
                    <span style="background:linear-gradient(135deg,var(--slate),var(--slate-light));color:var(--terracotta);padding:3px 10px;
                        border-radius:999px;font-size:11px;font-weight:700;">{sp_label}</span>
                </div>
                <h3 style="font-family:var(--font-display);font-size:18px;margin-bottom:8px;color:var(--ink);">{sp_name}</h3>
                <p style="color:var(--ink-muted);font-size:14px;margin-bottom:10px;">{sp_tagline}</p>
                <div style="display:flex;gap:8px;align-items:center;">
                    <span style="font-size:13px;font-weight:600;color:var(--success-text);">{price_text}</span>
                    <span style="font-size:12px;color:var(--ink-muted);">Indie alternative to {safe_name}</span>
                </div>
            </a>"""

        sponsored_html = f"""
        <div style="margin-bottom:32px;">
            {sponsored_html}
        </div>"""

    tool_count = len(tools)

    import json as _json

    # Build ItemList JSON-LD
    item_list_items = []
    for i, t in enumerate(tools):
        item_list_items.append({
            "@type": "ListItem",
            "position": i + 1,
            "url": f"{BASE_URL}/tool/{t['slug']}",
            "name": t['name'],
        })

    jsonld_itemlist = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": f"Indie Alternatives to {competitor_name}",
        "description": f"Compare {tool_count} bootstrapped and open-source alternatives to {competitor_name}.",
        "numberOfItems": tool_count,
        "itemListElement": item_list_items,
    }

    # Build FAQ JSON-LD
    # Check if any tools are free
    free_tools = [t for t in tools if not t.get('price_pence') or t['price_pence'] == 0]
    top_tool = tools[0] if tools else None

    faq_entries = []

    # Q1: "What are the best alternatives to X?" — always present
    top_names = ", ".join(str(t['name']) for t in tools[:5])
    faq_entries.append({
        "@type": "Question",
        "name": f"What are the best alternatives to {competitor_name}?",
        "acceptedAnswer": {
            "@type": "Answer",
            "text": f"Top alternatives to {competitor_name} on IndieStack include {top_names}. All {tool_count} options are indie and bootstrapped developer tools with transparent pricing."
        }
    })

    # Q2: "Is there a free alternative to X?" — only if free tools exist
    if free_tools:
        free_names = ", ".join(str(t['name']) for t in free_tools[:5])
        faq_entries.append({
            "@type": "Question",
            "name": f"Is there a free alternative to {competitor_name}?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": f"Yes! {len(free_tools)} free indie alternatives to {competitor_name} are available on IndieStack, including {free_names}."
            }
        })

    # Q3: "What do developers use instead of X?" — always present
    dev_names = ", ".join(str(t['name']) for t in tools[:3])
    faq_entries.append({
        "@type": "Question",
        "name": f"What do developers use instead of {competitor_name}?",
        "acceptedAnswer": {
            "@type": "Answer",
            "text": f"Developers looking for {competitor_name} alternatives commonly choose {dev_names}. These indie tools offer similar functionality with better pricing and direct maker support."
        }
    })

    # Q4: "What is the best open-source alternative to X?" — only if top_tool exists
    if top_tool:
        faq_entries.append({
            "@type": "Question",
            "name": f"What is the best open-source alternative to {competitor_name}?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": f"Based on community upvotes, {top_tool['name']} is the top-rated indie alternative to {competitor_name} on IndieStack. Browse all {tool_count} alternatives to find the best fit for your needs."
            }
        })

    jsonld_faq = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": faq_entries,
    }

    jsonld_script = (
        f'<script type="application/ld+json">{_json.dumps(jsonld_itemlist)}</script>\n'
        f'    <script type="application/ld+json">{_json.dumps(jsonld_faq)}</script>'
    )

    # Build HTML FAQ section
    faq_html = ""

    # Q1: "What are the best alternatives to X?" — always present
    top_names_html = ", ".join(f'<a href="/tool/{t["slug"]}" style="color:var(--terracotta);text-decoration:underline;">{escape(str(t["name"]))}</a>' for t in tools[:5])
    faq_html += f'''
        <details style="margin-bottom:12px;border:1px solid var(--border);border-radius:var(--radius-sm);padding:0;">
            <summary style="padding:14px 16px;font-weight:600;font-size:15px;color:var(--ink);cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between;">
                What are the best alternatives to {safe_name}?
                <span style="font-size:18px;color:var(--ink-muted);">+</span>
            </summary>
            <div style="padding:0 16px 14px;font-size:14px;color:var(--ink-light);line-height:1.6;">
                Top alternatives to {safe_name} on IndieStack include {top_names_html}. All {tool_count} options are indie and bootstrapped developer tools with transparent pricing.
            </div>
        </details>'''

    # Q2: "Is there a free alternative to X?" — only if free tools exist
    if free_tools:
        free_names_html = ", ".join(f'<a href="/tool/{t["slug"]}" style="color:var(--terracotta);text-decoration:underline;">{escape(str(t["name"]))}</a>' for t in free_tools[:5])
        faq_html += f'''
        <details style="margin-bottom:12px;border:1px solid var(--border);border-radius:var(--radius-sm);padding:0;">
            <summary style="padding:14px 16px;font-weight:600;font-size:15px;color:var(--ink);cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between;">
                Is there a free alternative to {safe_name}?
                <span style="font-size:18px;color:var(--ink-muted);">+</span>
            </summary>
            <div style="padding:0 16px 14px;font-size:14px;color:var(--ink-light);line-height:1.6;">
                Yes! {len(free_tools)} free indie alternatives to {safe_name} are available, including {free_names_html}.
            </div>
        </details>'''

    # Q3: "What do developers use instead of X?" — always present
    dev_names_html = ", ".join(f'<a href="/tool/{t["slug"]}" style="color:var(--terracotta);text-decoration:underline;">{escape(str(t["name"]))}</a>' for t in tools[:3])
    faq_html += f'''
        <details style="margin-bottom:12px;border:1px solid var(--border);border-radius:var(--radius-sm);padding:0;">
            <summary style="padding:14px 16px;font-weight:600;font-size:15px;color:var(--ink);cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between;">
                What do developers use instead of {safe_name}?
                <span style="font-size:18px;color:var(--ink-muted);">+</span>
            </summary>
            <div style="padding:0 16px 14px;font-size:14px;color:var(--ink-light);line-height:1.6;">
                Developers looking for {safe_name} alternatives commonly choose {dev_names_html}. These indie tools offer similar functionality with better pricing and direct maker support.
            </div>
        </details>'''

    # Q4: "What is the best open-source alternative to X?" — only if top_tool exists
    if top_tool:
        faq_html += f'''
        <details style="margin-bottom:12px;border:1px solid var(--border);border-radius:var(--radius-sm);padding:0;">
            <summary style="padding:14px 16px;font-weight:600;font-size:15px;color:var(--ink);cursor:pointer;list-style:none;display:flex;align-items:center;justify-content:space-between;">
                What is the best open-source alternative to {safe_name}?
                <span style="font-size:18px;color:var(--ink-muted);">+</span>
            </summary>
            <div style="padding:0 16px 14px;font-size:14px;color:var(--ink-light);line-height:1.6;">
                Based on community upvotes, <a href="/tool/{top_tool['slug']}" style="color:var(--terracotta);text-decoration:underline;">{escape(str(top_tool['name']))}</a> is the top-rated indie alternative to {safe_name} on IndieStack. Browse all {tool_count} alternatives to find the best fit.
            </div>
        </details>'''

    cards_parts = []
    for t in tools:
        card = tool_card(t)
        if t.get('boosted_competitor', ''):
            # Wrap boosted tool cards with a Featured badge
            card = f'''<div style="position:relative;">
                <span style="position:absolute;top:-8px;right:12px;background:var(--slate);color:var(--terracotta);font-size:11px;
                    font-weight:700;padding:2px 10px;border-radius:999px;z-index:1;text-transform:uppercase;
                    letter-spacing:0.5px;">&#9733; Featured</span>
                {card}
            </div>'''
        # Add "Indie alternative to X" subtitle and pricing comparison
        tool_name = escape(str(t.get('name', '')))
        price_pence = t.get('price_pence')
        pricing_html = ''
        if price_pence is not None and isinstance(price_pence, int) and price_pence > 0:
            price_display = f"&pound;{price_pence / 100:.0f}" if price_pence >= 100 else f"{price_pence}p"
            pricing_html = f'<span style="font-size:12px;font-weight:600;color:var(--success-text);background:var(--success-bg);padding:2px 10px;border-radius:999px;margin-left:8px;">From {price_display}</span>'
        elif price_pence is None or (isinstance(price_pence, int) and price_pence == 0):
            pricing_html = '<span style="font-size:12px;font-weight:600;color:var(--success-text);background:var(--success-bg);padding:2px 10px;border-radius:999px;margin-left:8px;">Free</span>'
        alt_subtitle = f'''<div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;margin-bottom:8px;">
            <span style="font-size:12px;color:var(--ink-muted);font-weight:500;">Indie alternative to {safe_name}</span>
            {pricing_html}
        </div>'''
        card = f'<div>{alt_subtitle}{card}</div>'
        cards_parts.append(card)
    cards_html = '\n'.join(cards_parts)

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:900px;">
        <div style="margin-bottom:40px;">
            <a href="/alternatives" style="color:var(--ink-muted);font-size:14px;font-weight:600;">&larr; All Alternatives</a>
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);margin-top:12px;">
                {tool_count} Indie Alternative{"s" if tool_count != 1 else ""} to {safe_name}
            </h1>
            <p style="color:var(--ink-muted);font-size:17px;margin-top:8px;max-width:600px;">
                Looking for a {safe_name} alternative? These developer tools offer the same features
                with better pricing, more flexibility, and personal support from the makers who built them.
            </p>
        </div>

        {sponsored_html}

        <div class="card-grid">{cards_html}</div>

        <!-- Email capture banner -->
        <div id="alt-sub-banner" style="display:none;margin-top:40px;padding:28px 24px;background:var(--terracotta);
            border-radius:var(--radius);position:relative;box-shadow:var(--shadow-md);">
            <button onclick="document.getElementById('alt-sub-banner').style.display='none';
                localStorage.setItem('alt_sub_{escape(competitor_slug)}_dismissed','1');"
                style="position:absolute;top:10px;right:14px;background:none;border:none;color:rgba(255,255,255,0.7);
                font-size:22px;cursor:pointer;line-height:1;padding:4px;" aria-label="Dismiss">&times;</button>
            <p style="font-family:var(--font-display);font-size:20px;color:#fff;margin-bottom:8px;">
                Get notified when a new {safe_name} alternative launches
            </p>
            <p style="font-size:14px;color:rgba(255,255,255,0.8);margin-bottom:16px;">
                We&rsquo;ll email you when indie makers ship new tools that replace {safe_name}. No spam, ever.
            </p>
            <form action="/api/subscribe" method="POST"
                style="display:flex;gap:8px;flex-wrap:wrap;align-items:stretch;">
                <input type="hidden" name="source" value="alternatives">
                <input type="hidden" name="tool_slug" value="{escape(competitor_slug)}">
                <input type="hidden" name="next" value="/alternatives/{escape(competitor_slug)}">
                <input type="email" name="email" required placeholder="you@example.com"
                    style="flex:1;min-width:200px;height:48px;padding:0 16px;border:1px solid rgba(255,255,255,0.2);
                    border-radius:var(--radius-sm);font-size:15px;font-family:var(--font-body);
                    background:rgba(0,0,0,0.3);color:#FFFFFF;outline:none;transition:border-color 0.2s ease;"
                    onfocus="this.style.borderColor='var(--accent)';this.style.boxShadow='0 0 0 3px rgba(0,212,245,0.15)'"
                    onblur="this.style.borderColor='rgba(255,255,255,0.2)';this.style.boxShadow='none'">
                <button type="submit"
                    style="height:48px;padding:0 24px;background:var(--accent);color:#000;font-weight:700;
                    font-size:14px;border:none;border-radius:var(--radius-sm);cursor:pointer;font-family:var(--font-body);
                    white-space:nowrap;">Notify Me &rarr;</button>
            </form>
        </div>
        <script>
            (function() {{
                if (!localStorage.getItem('alt_sub_{escape(competitor_slug)}_dismissed')) {{
                    document.getElementById('alt-sub-banner').style.display = 'block';
                }}
            }})();
        </script>

        <div style="margin-top:48px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:16px;">
                Frequently Asked Questions
            </h2>
            {faq_html}
        </div>

        <div style="text-align:center;margin-top:48px;padding:32px;background:var(--cream-dark);border-radius:var(--radius);">
            <p style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                Know an indie alternative to {safe_name} we&rsquo;re missing?
            </p>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                Submit it for free and help others find better, more affordable tools.
            </p>
            <a href="/submit" class="btn btn-primary">Submit Your Tool &rarr;</a>
        </div>
    </div>
    """
    return HTMLResponse(page_shell(f"{tool_count} Indie Alternatives to {competitor_name} (2026)", body,
                                   description=f"Compare {tool_count} bootstrapped and open-source alternatives to {competitor_name}. Curated developer tools, no VC-funded software.",
                                   user=request.state.user, canonical=f"/alternatives/{competitor_slug}",
                                   extra_head=jsonld_script))


@router.get("/alternatives/{competitor_slug}/vs/{tool_slug}", response_class=HTMLResponse)
async def alternative_vs(request: Request, competitor_slug: str, tool_slug: str):
    """Deep comparison: one incumbent vs one indie tool."""
    import json as _json
    db = request.state.db

    # Resolve competitor name
    all_competitors = await get_all_competitors(db)
    competitor_name = competitor_slug.replace('-', ' ').title()
    for comp in all_competitors:
        if slugify(comp) == competitor_slug:
            competitor_name = comp
            break

    # Get the tool
    cursor = await db.execute(
        "SELECT t.*, c.name as category_name, c.slug as category_slug "
        "FROM tools t JOIN categories c ON t.category_id = c.id "
        "WHERE t.slug = ? AND t.status = 'approved'", (tool_slug,))
    tool = await cursor.fetchone()
    if not tool:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/alternatives/{competitor_slug}", status_code=303)
    tool = dict(tool)

    # Validate this tool actually replaces the competitor
    replaces_list = [r.strip().lower() for r in (tool.get('replaces') or '').split(',')]
    if competitor_name.lower() not in replaces_list and competitor_slug.replace('-', ' ') not in replaces_list:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/alternatives/{competitor_slug}", status_code=303)

    safe_comp = escape(competitor_name)
    safe_name = escape(str(tool['name']))
    safe_tagline = escape(str(tool.get('tagline', '')))
    safe_desc = escape(str(tool.get('description', '')))
    tool_slug_safe = escape(str(tool['slug']))

    # Pricing display
    price_pence = tool.get('price_pence')
    if price_pence and isinstance(price_pence, int) and price_pence > 0:
        price_display = f"From &pound;{price_pence / 100:.0f}/mo"
    else:
        price_display = "Free"

    # Badges
    ejectable_badge = '<span style="display:inline-block;background:var(--info-bg, #EDE9FE);color:var(--info-text, #7C3AED);padding:3px 10px;border-radius:999px;font-size:12px;font-weight:600;"><svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:inline-block;vertical-align:-1px;"><path d="M13 2 3 14h9l-1 8 10-12h-9l1-8z"/></svg> Ejectable</span>' if tool.get('is_ejectable') else ''

    # Get other alternatives for cross-linking
    other_tools = await get_tools_replacing(db, competitor_name, limit=6)
    other_tools = [t for t in other_tools if t['slug'] != tool_slug]

    cross_links = ""
    if other_tools:
        links = []
        for ot in other_tools[:5]:
            ot_name = escape(str(ot['name']))
            ot_slug = escape(str(ot['slug']))
            links.append(f'<a href="/alternatives/{escape(competitor_slug)}/vs/{ot_slug}" style="display:inline-block;padding:6px 14px;background:var(--cream-dark);border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px;color:var(--ink);text-decoration:none;font-weight:500;">{safe_comp} vs {ot_name}</a>')
        cross_links = f'''
        <div style="margin-top:40px;">
            <h2 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:12px;">
                Other {safe_comp} Alternatives
            </h2>
            <div style="display:flex;flex-wrap:wrap;gap:8px;">
                {"".join(links)}
            </div>
        </div>'''

    # JSON-LD
    jsonld = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "name": f"{competitor_name} vs {tool['name']} — Indie Alternative Comparison",
        "description": f"Compare {competitor_name} with {tool['name']}, an indie alternative. {tool.get('tagline', '')}",
        "mainEntity": {
            "@type": "SoftwareApplication",
            "name": tool['name'],
            "url": tool.get('url', ''),
            "applicationCategory": tool.get('category_name', ''),
            "description": tool.get('tagline', ''),
        }
    }
    jsonld_script = f'<script type="application/ld+json">{_json.dumps(jsonld)}</script>'

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:800px;">
        <div style="margin-bottom:8px;">
            <a href="/alternatives/{escape(competitor_slug)}" style="color:var(--ink-muted);font-size:14px;font-weight:600;">&larr; All {safe_comp} Alternatives</a>
        </div>

        <h1 style="font-family:var(--font-display);font-size:clamp(26px,4vw,38px);color:var(--ink);margin-bottom:8px;">
            {safe_comp} vs {safe_name}
        </h1>
        <p style="color:var(--ink-muted);font-size:17px;margin-bottom:32px;">
            Is {safe_name} a good alternative to {safe_comp}? Here&rsquo;s what you need to know.
        </p>

        <div class="card" style="padding:24px;">
            <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;flex-wrap:wrap;">
                <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);margin:0;">{safe_name}</h2>
                {ejectable_badge}
                <span style="font-size:14px;font-weight:600;color:var(--success-text);background:var(--success-bg);padding:4px 12px;border-radius:999px;">{price_display}</span>
            </div>
            <p style="font-size:16px;color:var(--ink);margin-bottom:12px;font-weight:500;">{safe_tagline}</p>
            <p style="font-size:14px;color:var(--ink-light);line-height:1.7;margin-bottom:20px;">{safe_desc}</p>

            <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:20px;">
                {_alt_health_badge(tool.get('health_status') or 'unknown')}
                {_alt_github_stars(tool)}
                {_alt_agent_citations(tool)}
            </div>

            <div style="display:flex;gap:10px;flex-wrap:wrap;">
                <a href="/api/click/{tool_slug_safe}" target="_blank" rel="noopener" class="btn btn-primary" style="font-size:14px;">
                    Visit {safe_name} &rarr;
                </a>
                <a href="/tool/{tool_slug_safe}" class="btn" style="font-size:14px;background:var(--cream-dark);color:var(--ink);border:1px solid var(--border);">
                    View Full Listing
                </a>
            </div>
        </div>

        <div style="margin-top:32px;padding:24px;background:var(--cream-dark);border-radius:var(--radius);">
            <h2 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                Why switch from {safe_comp}?
            </h2>
            <ul style="color:var(--ink-light);font-size:14px;line-height:1.8;padding-left:20px;">
                <li><strong>Indie pricing</strong> &mdash; no enterprise markup or per-seat fees</li>
                <li><strong>Direct maker support</strong> &mdash; talk to the person who built it</li>
                <li><strong>Transparent &amp; open</strong> &mdash; many indie tools are open-source</li>
                <li><strong>No vendor lock-in</strong> &mdash; own your data, export anytime</li>
            </ul>
        </div>

        {cross_links}

        <div style="text-align:center;margin-top:48px;padding:32px;background:var(--cream-dark);border-radius:var(--radius);">
            <p style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                Building an alternative to {safe_comp}?
            </p>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                List your tool on IndieStack for free and reach developers looking to switch.
            </p>
            <a href="/submit" class="btn btn-primary">Submit Your Tool &rarr;</a>
        </div>
    </div>
    """

    return HTMLResponse(page_shell(
        f"{competitor_name} vs {tool['name']} — Indie Alternative Comparison (2026)",
        body,
        description=f"Compare {competitor_name} with {tool['name']}, a bootstrapped indie alternative. {tool.get('tagline', '')}",
        user=request.state.user,
        canonical=f"/alternatives/{competitor_slug}/vs/{tool_slug}",
        extra_head=jsonld_script,
    ))

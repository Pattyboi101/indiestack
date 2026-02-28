"""SaaS cost calculator — engineering-as-marketing for IndieStack."""

import json as _json
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell
from indiestack.db import get_tools_replacing, slugify

router = APIRouter()

COMPETITOR_PRICING = {
    "Datadog": {"price": "$23/host/mo", "annual": 276, "unit": "host"},
    "Vercel": {"price": "$20/member/mo", "annual": 240, "unit": "member"},
    "Auth0": {"price": "$35/1K MAU/mo", "annual": 420, "unit": "1K MAU"},
    "Stripe": {"price": "2.9% + 30¢/txn", "annual": 3480, "unit": "flat"},
    "Intercom": {"price": "$74/seat/mo", "annual": 888, "unit": "seat"},
    "Slack": {"price": "$8.75/user/mo", "annual": 105, "unit": "user"},
    "Notion": {"price": "$10/member/mo", "annual": 120, "unit": "member"},
    "Jira": {"price": "$8.15/user/mo", "annual": 98, "unit": "user"},
    "Mailchimp": {"price": "$13/500 contacts/mo", "annual": 156, "unit": "500 contacts"},
    "HubSpot": {"price": "$20/seat/mo", "annual": 240, "unit": "seat"},
    "Zendesk": {"price": "$19/agent/mo", "annual": 228, "unit": "agent"},
    "Heroku": {"price": "$7/dyno/mo", "annual": 84, "unit": "dyno"},
    "Firebase": {"price": "$25 Blaze/mo", "annual": 300, "unit": "flat"},
    "Sentry": {"price": "$26/member/mo", "annual": 312, "unit": "member"},
    "Cloudflare": {"price": "$20 Pro/mo", "annual": 240, "unit": "flat"},
    "Linear": {"price": "$8/member/mo", "annual": 96, "unit": "member"},
    "Figma": {"price": "$15/editor/mo", "annual": 180, "unit": "editor"},
    "Postman": {"price": "$14/user/mo", "annual": 168, "unit": "user"},
    "Algolia": {"price": "Usage-based", "annual": 600, "unit": "flat"},
    "Google Analytics": {"price": "Free (data cost)", "annual": 0, "unit": "flat"},
}


@router.get("/calculator", response_class=HTMLResponse)
@router.get("/savings", response_class=HTMLResponse)
async def calculator(request: Request):
    db = request.state.db
    preselected = set()
    tools_param = request.query_params.get("tools", "")
    if tools_param:
        preselected = {t.strip().lower() for t in tools_param.split(",")}

    # Get indie alternative counts per competitor
    alt_counts = {}
    for comp in COMPETITOR_PRICING:
        tools = await get_tools_replacing(db, comp, limit=50)
        alt_counts[comp] = len(tools)

    # Build competitor cards
    cards_html = ""
    for comp, info in COMPETITOR_PRICING.items():
        comp_slug = slugify(comp)
        checked = "checked" if comp_slug in preselected or comp.lower() in preselected else ""
        alt_count = alt_counts.get(comp, 0)
        alt_badge = f'<span style="font-size:11px;color:#0D7377;font-weight:600;">{alt_count} indie alt{"s" if alt_count != 1 else ""}</span>' if alt_count > 0 else '<span style="font-size:11px;color:var(--ink-muted);">No alts yet</span>'
        border_color = "var(--accent)" if checked else "var(--border)"

        cards_html += f'''
        <label data-comp="{escape(comp)}" data-annual="{info["annual"]}" data-slug="{comp_slug}"
               style="display:block;cursor:pointer;border:2px solid {border_color};border-radius:var(--radius);padding:16px;
                      transition:border-color 0.15s;background:var(--card-bg);"
               onclick="this.style.borderColor=this.querySelector('input').checked?'var(--accent)':'var(--border)'">
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
                <input type="checkbox" name="tools" value="{comp_slug}" {checked}
                       onchange="updateCalc()" style="accent-color:var(--accent);width:16px;height:16px;">
                <span style="font-family:var(--font-display);font-size:16px;color:var(--ink);">{escape(comp)}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:13px;color:var(--ink-muted);">{escape(info["price"])}</span>
                {alt_badge}
            </div>
            <div style="font-size:12px;color:var(--ink-muted);margin-top:4px;">
                &pound;{info["annual"]:,}/yr est.
            </div>
        </label>'''

    # Pricing data as JSON for JS
    pricing_json = _json.dumps({slugify(k): {"name": k, "annual": v["annual"], "price": v["price"]} for k, v in COMPETITOR_PRICING.items()})

    # JSON-LD
    jsonld = {
        "@context": "https://schema.org",
        "@type": "WebApplication",
        "name": "IndieStack SaaS Cost Calculator",
        "url": f"{BASE_URL}/calculator",
        "description": "Calculate how much you spend on SaaS tools and find cheaper indie alternatives.",
        "applicationCategory": "BusinessApplication",
        "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
    }
    jsonld_script = f'<script type="application/ld+json">{_json.dumps(jsonld)}</script>'

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:960px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);">
                How Much Are You Spending on SaaS?
            </h1>
            <p style="color:var(--ink-muted);font-size:17px;margin-top:12px;max-width:560px;margin-left:auto;margin-right:auto;">
                Select the tools you use. We&rsquo;ll show you the annual cost and indie alternatives that could save you thousands.
            </p>
        </div>

        <!-- Results banner (hidden until selection) -->
        <div id="results-banner" style="display:none;background:linear-gradient(135deg,#1A2D4A,#0D1B2A);border-radius:var(--radius);
             padding:28px 24px;margin-bottom:32px;text-align:center;">
            <div style="font-size:14px;color:#94A3B8;margin-bottom:4px;">Your estimated annual SaaS spend</div>
            <div id="total-spend" style="font-family:var(--font-display);font-size:48px;color:#00D4F5;font-weight:700;">
                &pound;0
            </div>
            <div id="tool-count-label" style="font-size:14px;color:#94A3B8;margin-top:4px;">across 0 tools</div>
            <div id="share-url" style="margin-top:12px;">
                <button onclick="navigator.clipboard.writeText(window.location.href).then(()=>{{this.textContent='Link copied!';setTimeout(()=>this.textContent='Share this calculation',2000)}})"
                        style="padding:6px 16px;font-size:12px;background:rgba(255,255,255,0.1);color:#94A3B8;border:1px solid rgba(255,255,255,0.2);
                               border-radius:var(--radius-sm);cursor:pointer;">
                    Share this calculation
                </button>
            </div>
        </div>

        <!-- Breakdown table (hidden until selection) -->
        <div id="breakdown" style="display:none;margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:12px;">Cost Breakdown</h2>
            <div id="breakdown-rows" style="display:flex;flex-direction:column;gap:8px;"></div>
        </div>

        <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
            Select your tools
        </h2>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px;margin-bottom:48px;">
            {cards_html}
        </div>

        <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
            <a href="/alternatives" class="btn btn-primary">Browse All Alternatives &rarr;</a>
            <a href="/submit" class="btn" style="background:var(--cream-dark);color:var(--ink);border:1px solid var(--border);">List Your Tool</a>
        </div>
    </div>

    <script>
    const PRICING = {pricing_json};
    function updateCalc() {{
        const checks = document.querySelectorAll('input[name="tools"]:checked');
        const slugs = Array.from(checks).map(c => c.value);
        let total = 0;
        let rows = '';

        // Update card borders
        document.querySelectorAll('label[data-comp]').forEach(label => {{
            const inp = label.querySelector('input');
            label.style.borderColor = inp.checked ? 'var(--accent)' : 'var(--border)';
        }});

        slugs.forEach(slug => {{
            const d = PRICING[slug];
            if (!d) return;
            total += d.annual;
            rows += '<div style="display:flex;justify-content:space-between;align-items:center;padding:12px 16px;background:var(--card-bg);border:1px solid var(--border);border-radius:var(--radius-sm);">'
                + '<div><span style="font-weight:600;color:var(--ink);">' + d.name + '</span>'
                + '<span style="margin-left:8px;font-size:13px;color:var(--ink-muted);">' + d.price + '</span></div>'
                + '<span style="font-family:var(--font-display);font-size:16px;color:var(--ink);">\u00a3' + d.annual.toLocaleString() + '/yr</span>'
                + '</div>';
        }});

        const banner = document.getElementById('results-banner');
        const breakdown = document.getElementById('breakdown');
        if (slugs.length > 0) {{
            banner.style.display = 'block';
            breakdown.style.display = 'block';
            document.getElementById('total-spend').innerHTML = '\u00a3' + total.toLocaleString() + '<span style="font-size:20px;color:#94A3B8;">/yr</span>';
            document.getElementById('tool-count-label').textContent = 'across ' + slugs.length + ' tool' + (slugs.length === 1 ? '' : 's');
            document.getElementById('breakdown-rows').innerHTML = rows;
        }} else {{
            banner.style.display = 'none';
            breakdown.style.display = 'none';
        }}

        // Update URL
        const url = new URL(window.location);
        if (slugs.length > 0) {{
            url.searchParams.set('tools', slugs.join(','));
        }} else {{
            url.searchParams.delete('tools');
        }}
        history.replaceState(null, '', url);
    }}

    // Run on load if pre-selected
    document.addEventListener('DOMContentLoaded', updateCalc);
    </script>
    """

    return HTMLResponse(page_shell(
        "SaaS Cost Calculator — Find Cheaper Indie Alternatives",
        body,
        description="Calculate your annual SaaS spend and discover indie alternatives. Compare pricing for Datadog, Vercel, Auth0, Stripe, and more.",
        user=request.state.user,
        canonical="/calculator",
        extra_head=jsonld_script,
    ))

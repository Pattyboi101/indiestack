"""Category browse page."""

import json
import math
from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell, tool_card, pagination_html
from indiestack.routes.category_icons import category_icon
from indiestack.db import get_category_by_slug, get_tools_by_category, get_category_tools_for_compare, get_batch_success_rates

router = APIRouter()

PER_PAGE = 12

# Category-specific meta descriptions for SEO. Key = category slug.
# Each value is a template string with a single {total} placeholder.
_CATEGORY_META: dict[str, str] = {
    "authentication": "{total}+ open-source auth tools — OAuth, SSO, passkeys, MFA, and session management. Alternatives to Auth0, Clerk, and Firebase Auth.",
    "payments": "{total}+ payment tools for developers — Stripe alternatives, subscriptions, checkout, and billing. Bootstrapped and open-source options.",
    "analytics-metrics": "{total}+ privacy-first analytics tools — Google Analytics alternatives, event tracking, dashboards, and A/B testing. GDPR-compliant options.",
    "email-marketing": "{total}+ email tools for developers — transactional APIs, newsletter platforms, and drip campaigns. Alternatives to Mailchimp and SendGrid.",
    "database": "{total}+ database tools — PostgreSQL, ORMs, migrations, vector databases, and BaaS. Alternatives to PlanetScale, Supabase, and Neon.",
    "hosting-infrastructure": "{total}+ hosting and infrastructure tools — PaaS, VPS, serverless, and container platforms. Heroku and Render alternatives for indie developers.",
    "frontend-frameworks": "{total}+ frontend tools — JavaScript frameworks, UI libraries, bundlers, and state management. React, Vue, Svelte, Vite, and TypeScript ecosystem tools.",
    "caching": "{total}+ caching tools — Redis alternatives, in-memory stores, and serverless key-value databases for high-performance apps.",
    "mcp-servers": "{total}+ MCP server implementations — give AI agents (Claude, Cursor, Windsurf) access to your data, APIs, and tools via the Model Context Protocol.",
    "boilerplates": "{total}+ boilerplate kits and starter templates — SaaS starters, Next.js templates, and full-stack scaffolds. Ship your next project faster.",
    "developer-tools": "{total}+ developer tools — CLI utilities, debugging tools, SDKs, and productivity tools built by indie developers. No enterprise pricing.",
    "monitoring-uptime": "{total}+ monitoring tools — uptime checks, error tracking, APM, and alerting. Self-hostable Datadog and PagerDuty alternatives.",
    "cms-content": "{total}+ headless CMS and content tools — Contentful, Sanity, and WordPress alternatives. API-first CMS for modern web development.",
    "background-jobs": "{total}+ background job tools — cron schedulers, task queues, and workflow engines. Alternatives to Celery, Bull, and AWS SQS.",
    "ai-dev-tools": "{total}+ AI dev tools — MCP servers, coding assistants, agent frameworks, and LLM integrations built by indie developers.",
    "ai-automation": "{total}+ AI and automation tools — LLM integrations, workflow automation, and AI-powered features. Open-source alternatives to enterprise AI platforms.",
    "devops-infrastructure": "{total}+ DevOps tools — CI/CD, Docker, Kubernetes, IaC, and deployment automation. Open-source alternatives to GitHub Actions and CircleCI.",
    "security-tools": "{total}+ security tools — vulnerability scanners, secret management, WAF, and penetration testing utilities. Open-source and bootstrapped.",
}


@router.get("/category/{slug}", response_class=HTMLResponse)
async def category_page(request: Request, slug: str, page: int = 1):
    db = request.state.db
    category = await get_category_by_slug(db, slug)

    if not category:
        body = """
        <div class="container" style="text-align:center;padding:80px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Category Not Found</h1>
            <p class="text-muted mt-4">We couldn't find that category.</p>
            <a href="/" class="btn btn-primary mt-4">Back to Home</a>
        </div>
        """
        return HTMLResponse(page_shell("Not Found", body, user=request.state.user), status_code=404)

    if page < 1:
        page = 1

    tools, total = await get_tools_by_category(db, int(category['id']), page=page, per_page=PER_PAGE)
    total_pages = max(1, math.ceil(total / PER_PAGE))

    icon = category_icon(str(category.get('slug', '')), size=48)
    name = str(category['name'])
    name_esc = escape(name)
    _desc_tpl = _CATEGORY_META.get(
        str(category.get('slug', '')),
        "Discover {total}+ indie " + name + " tools built by independent makers. Open-source and bootstrapped alternatives with install commands and compatibility data.",
    )
    desc = _desc_tpl.format(total=total)

    if tools:
        # Inject trust badge data
        try:
            slugs = [str(t.get('slug', '')) for t in tools if t.get('slug')]
            sr_map = await get_batch_success_rates(db, slugs)
            for t in tools:
                s = str(t.get('slug', ''))
                if s in sr_map:
                    t['_success_rate'] = sr_map[s]
        except Exception:
            pass

        cards = '\n'.join(tool_card(t) for t in tools)

        # Compare links for categories with 2+ tools
        compare_html = ''
        if len(tools) >= 2:
            compare_tools = await get_category_tools_for_compare(db, int(category['id']), limit=6)
            if len(compare_tools) >= 2:
                compare_links = []
                for i in range(len(compare_tools)):
                    for j in range(i + 1, min(i + 2, len(compare_tools))):
                        s1 = escape(str(compare_tools[i]['slug']))
                        s2 = escape(str(compare_tools[j]['slug']))
                        n1 = escape(str(compare_tools[i]['name']))
                        n2 = escape(str(compare_tools[j]['name']))
                        compare_links.append(
                            f'<a href="/compare/{s1}-vs-{s2}" style="color:var(--terracotta);font-size:13px;">{n1} vs {n2}</a>'
                        )
                    if len(compare_links) >= 3:
                        break
                if compare_links:
                    compare_html = f"""
                    <div style="margin-top:24px;padding:16px;background:var(--cream-dark);border-radius:var(--radius-sm);text-align:center;">
                        <span style="font-size:13px;color:var(--ink-muted);font-weight:600;">Compare tools: </span>
                        {' &middot; '.join(compare_links)}
                    </div>
                    """

        tools_html = f"""
        <div class="card-grid">{cards}</div>
        {compare_html}
        {pagination_html(page, total_pages, f"/category/{slug}")}
        """
    else:
        tools_html = """
        <div style="text-align:center;padding:60px 0;">
            <p style="font-size:18px;color:var(--ink-muted);">No tools in this category yet.</p>
            <a href="/submit" class="btn btn-primary mt-4">Submit the first one</a>
        </div>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <span style="color:var(--slate);display:inline-block;">{icon}</span>
            <h1 style="font-family:var(--font-display);font-size:36px;margin-top:8px;color:var(--ink);">{name_esc}</h1>
            <p class="text-muted mt-2">{desc}</p>
        </div>
        {tools_html}
    </div>
    """
    # JSON-LD ItemList for rich snippets
    json_ld_data = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": str(category['name']),
        "description": str(category.get('description', '')),
        "url": f"{BASE_URL}/category/{slug}",
        "numberOfItems": total,
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "url": f"{BASE_URL}/tool/{t['slug']}",
                "name": str(t['name']),
            }
            for i, t in enumerate(tools)
        ]
    }
    _json_ld = json.dumps(json_ld_data, ensure_ascii=False).replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
    extra_head = f'<script type="application/ld+json">{_json_ld}</script>'

    # For categories where the name already implies "tools", omit the trailing word
    _NO_TOOLS_SUFFIX = {"frontend-frameworks", "mcp-servers", "boilerplates", "background-jobs",
                        "devops-infrastructure", "ai-dev-tools", "security-tools", "testing-tools"}
    if str(category.get('slug', '')) in _NO_TOOLS_SUFFIX:
        title = f"Best {name} | IndieStack"
    else:
        title = f"Best Indie {name} Tools | IndieStack"
    return HTMLResponse(page_shell(title, body, description=desc, user=request.state.user, extra_head=extra_head, canonical=f"/category/{slug}"))

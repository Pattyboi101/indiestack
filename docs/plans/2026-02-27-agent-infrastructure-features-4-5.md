# Agent Infrastructure Features 4 & 5 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a Stack Builder API (agents request tools by need) and Use Case Pages (human + agent comparison pages) to complete the agent infrastructure layer.

**Architecture:** Feature 4 adds `GET /api/stack-builder` + `build_stack` MCP tool using a keyword-to-category mapping dict. Feature 5 adds a new `routes/use_cases.py` with curated + auto-generated comparison pages at `/use-cases/{slug}` plus JSON APIs at `/api/use-cases`. Both features share a `NEED_MAPPINGS` pattern that maps common keywords to category slugs.

**Tech Stack:** Python/FastAPI, SQLite (existing FTS5 search), Pure Python HTML templates, MCP server (FastMCP)

---

## Task 1: Add NEED_MAPPINGS to db.py

**Files:**
- Modify: `src/indiestack/db.py` — insert after `CATEGORY_TOKEN_COSTS` dict (line 453)

**Step 1: Add the NEED_MAPPINGS dict**

Insert after line 453 (closing `}` of `CATEGORY_TOKEN_COSTS`):

```python
# Maps common need keywords to category slugs, search terms, and competitors.
# Used by Stack Builder API and Use Case pages.
NEED_MAPPINGS = {
    "auth": {"category": "authentication", "terms": ["auth", "login", "SSO", "identity"], "competitors": ["Auth0", "Firebase Auth", "Okta", "Cognito"], "title": "Authentication", "description": "Add login, signup, SSO, and session management without building from scratch.", "build_estimate": "2-3 weeks", "icon": "\U0001f510"},
    "payments": {"category": "payments", "terms": ["payments", "billing", "checkout", "subscriptions"], "competitors": ["Stripe", "PayPal", "Square"], "title": "Payments", "description": "Accept payments, manage subscriptions, and handle checkouts.", "build_estimate": "3-4 weeks", "icon": "\U0001f4b3"},
    "analytics": {"category": "analytics-metrics", "terms": ["analytics", "metrics", "tracking", "dashboards"], "competitors": ["Google Analytics", "Mixpanel", "Amplitude"], "title": "Analytics & Metrics", "description": "Track user behavior, measure funnels, and build dashboards.", "build_estimate": "2-3 weeks", "icon": "\U0001f4ca"},
    "email": {"category": "email-marketing", "terms": ["email", "newsletter", "drip", "marketing"], "competitors": ["Mailchimp", "SendGrid", "ConvertKit"], "title": "Email Marketing", "description": "Send newsletters, drip campaigns, and transactional emails.", "build_estimate": "2-3 weeks", "icon": "\U0001f4e7"},
    "invoicing": {"category": "invoicing-billing", "terms": ["invoicing", "billing", "receipts", "accounting"], "competitors": ["FreshBooks", "QuickBooks", "Xero"], "title": "Invoicing & Billing", "description": "Generate invoices, track payments, and manage billing workflows.", "build_estimate": "3-4 weeks", "icon": "\U0001f9fe"},
    "monitoring": {"category": "monitoring-uptime", "terms": ["monitoring", "uptime", "alerting", "observability"], "competitors": ["Datadog", "PagerDuty", "Pingdom"], "title": "Monitoring & Uptime", "description": "Monitor uptime, get alerts, and track application health.", "build_estimate": "2-3 weeks", "icon": "\U0001f6a8"},
    "forms": {"category": "forms-surveys", "terms": ["forms", "surveys", "feedback", "questionnaires"], "competitors": ["Typeform", "Google Forms", "SurveyMonkey"], "title": "Forms & Surveys", "description": "Build forms, collect responses, and run surveys.", "build_estimate": "1-2 weeks", "icon": "\U0001f4cb"},
    "scheduling": {"category": "scheduling-booking", "terms": ["scheduling", "booking", "calendar", "appointments"], "competitors": ["Calendly", "Acuity", "Cal.com"], "title": "Scheduling & Booking", "description": "Let users book meetings, schedule appointments, and manage availability.", "build_estimate": "2-3 weeks", "icon": "\U0001f4c5"},
    "cms": {"category": "cms-content", "terms": ["cms", "content", "blog", "headless"], "competitors": ["WordPress", "Contentful", "Sanity"], "title": "CMS & Content", "description": "Manage content, run blogs, and build headless CMS backends.", "build_estimate": "3-5 weeks", "icon": "\U0001f4dd"},
    "support": {"category": "customer-support", "terms": ["support", "helpdesk", "chat", "ticketing"], "competitors": ["Zendesk", "Intercom", "Freshdesk"], "title": "Customer Support", "description": "Add helpdesks, live chat, and ticketing systems.", "build_estimate": "3-4 weeks", "icon": "\U0001f3a7"},
    "seo": {"category": "seo-tools", "terms": ["seo", "search", "ranking", "keywords"], "competitors": ["Ahrefs", "SEMrush", "Moz"], "title": "SEO Tools", "description": "Track rankings, audit sites, and optimize for search engines.", "build_estimate": "2-3 weeks", "icon": "\U0001f50d"},
    "storage": {"category": "file-management", "terms": ["storage", "files", "upload", "media"], "competitors": ["AWS S3", "Dropbox", "Cloudinary"], "title": "File Storage", "description": "Upload files, manage media assets, and serve content.", "build_estimate": "1-2 weeks", "icon": "\U0001f4c1"},
    "crm": {"category": "crm-sales", "terms": ["crm", "sales", "leads", "pipeline"], "competitors": ["Salesforce", "HubSpot", "Pipedrive"], "title": "CRM & Sales", "description": "Manage contacts, track deals, and automate sales pipelines.", "build_estimate": "4-6 weeks", "icon": "\U0001f91d"},
    "devtools": {"category": "developer-tools", "terms": ["developer", "tools", "sdk", "api"], "competitors": ["Postman", "Ngrok"], "title": "Developer Tools", "description": "Debug, test, and ship faster with indie developer tools.", "build_estimate": "varies", "icon": "\U0001f6e0\ufe0f"},
    "ai": {"category": "ai-automation", "terms": ["ai", "automation", "ml", "llm"], "competitors": ["OpenAI", "AWS AI", "Google AI"], "title": "AI & Automation", "description": "Add AI features, automate workflows, and integrate LLMs.", "build_estimate": "3-5 weeks", "icon": "\U0001f916"},
    "design": {"category": "design-creative", "terms": ["design", "ui", "creative", "graphics"], "competitors": ["Figma", "Canva", "Adobe"], "title": "Design & Creative", "description": "Create designs, generate graphics, and build UI components.", "build_estimate": "varies", "icon": "\U0001f3a8"},
    "feedback": {"category": "feedback-reviews", "terms": ["feedback", "reviews", "nps", "ratings"], "competitors": ["Hotjar", "UserTesting", "Typeform"], "title": "Feedback & Reviews", "description": "Collect user feedback, run NPS surveys, and manage reviews.", "build_estimate": "1-2 weeks", "icon": "\U0001f4ac"},
    "social": {"category": "social-media", "terms": ["social", "community", "social media"], "competitors": ["Buffer", "Hootsuite"], "title": "Social Media", "description": "Schedule posts, manage social accounts, and grow communities.", "build_estimate": "2-3 weeks", "icon": "\U0001f4f1"},
}
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/indiestack/db.py
git commit -m "feat: add NEED_MAPPINGS dict for stack builder and use case pages"
```

---

## Task 2: Add Stack Builder API endpoint to main.py

**Files:**
- Modify: `src/indiestack/main.py` — insert new endpoint after `/api/cite` (after line ~1070)

**Context needed:**
- Read `src/indiestack/main.py` lines 1050-1075 to find exact insertion point
- The endpoint reuses `db.search_tools`, `db.get_tools_by_category`, `db.get_category_by_slug`, `db.get_all_stacks`, `db.get_stack_with_tools`
- Import `NEED_MAPPINGS` and `CATEGORY_TOKEN_COSTS` from db

**Step 1: Add import for NEED_MAPPINGS**

In main.py, find the existing `from indiestack import db` import. Also add near the top where db is imported:

```python
from indiestack.db import CATEGORY_TOKEN_COSTS, NEED_MAPPINGS
```

**Step 2: Add the /api/stack-builder endpoint**

Insert after the `/api/cite` endpoint:

```python
@app.get("/api/stack-builder")
async def api_stack_builder(request: Request, needs: str = "", budget: int = 0):
    """AI agent endpoint: recommend an indie tool stack for given requirements.

    Args:
        needs: Comma-separated use cases (e.g. needs=auth,payments,analytics)
        budget: Optional max monthly price per tool in GBP (0 = no limit)
    """
    d = request.state.db
    if not needs.strip():
        return JSONResponse({
            "error": "Provide needs as comma-separated use cases",
            "example": "/api/stack-builder?needs=auth,payments,analytics",
            "available_needs": sorted(NEED_MAPPINGS.keys()),
        }, status_code=400)

    need_list = [n.strip().lower() for n in needs.split(",") if n.strip()]
    stack = []

    for need in need_list:
        mapping = NEED_MAPPINGS.get(need)
        matched_via = "category" if mapping else "search"
        category_slug = mapping["category"] if mapping else None
        category_name = mapping.get("title", need.title()) if mapping else need.title()
        tokens_saved = CATEGORY_TOKEN_COSTS.get(category_slug, 50_000) if category_slug else 50_000

        tools_raw = []
        if category_slug:
            cat = await db.get_category_by_slug(d, category_slug)
            if cat:
                rows, _ = await db.get_tools_by_category(d, cat['id'], page=1, per_page=5)
                tools_raw = list(rows)
                category_name = cat['name']

        # Supplement with FTS5 search if we got fewer than 3 results
        if len(tools_raw) < 3:
            search_terms = mapping["terms"] if mapping else [need]
            for term in search_terms:
                if len(tools_raw) >= 5:
                    break
                found = await db.search_tools(d, term, limit=5)
                existing_ids = {t['id'] for t in tools_raw}
                for f in found:
                    if f['id'] not in existing_ids and len(tools_raw) < 5:
                        tools_raw.append(f)
                        existing_ids.add(f['id'])
            if not matched_via == "category" or not tools_raw:
                matched_via = "search"

        # Format tools
        recommendations = []
        for t in tools_raw:
            pp = t.get('price_pence')
            price_monthly = (pp / 100) if pp and pp > 0 else 0
            if budget > 0 and price_monthly > budget:
                continue
            recommendations.append({
                "name": t['name'],
                "slug": t['slug'],
                "tagline": t.get('tagline', ''),
                "price": f"\u00a3{price_monthly:.2f}" if price_monthly > 0 else "Free",
                "price_monthly": price_monthly,
                "verified": bool(t.get('is_verified', 0)),
                "upvotes": int(t.get('upvote_count', 0)),
                "url": f"{BASE_URL}/tool/{t['slug']}",
            })

        stack.append({
            "need": need,
            "category": category_name,
            "tokens_saved": tokens_saved,
            "matched_via": matched_via,
            "tools": recommendations,
        })

    # Find matching Vibe Stacks
    matching_stacks = []
    all_stacks = await db.get_all_stacks(d)
    for s in all_stacks:
        _, stack_tools = await db.get_stack_with_tools(d, s['slug'])
        if not stack_tools:
            continue
        stack_cat_slugs = {t.get('category_slug', '') for t in stack_tools}
        coverage = []
        for need in need_list:
            mapping = NEED_MAPPINGS.get(need)
            if mapping and mapping["category"] in stack_cat_slugs:
                coverage.append(need)
        if coverage:
            matching_stacks.append({
                "title": s['title'],
                "slug": s.get('slug', ''),
                "description": s.get('description', ''),
                "coverage": coverage,
                "discount": int(s.get('discount_percent', 15)),
                "tool_count": int(s.get('tool_count', 0)),
                "url": f"{BASE_URL}/stacks/{s.get('slug', '')}",
            })

    # Sort matching stacks by coverage count descending
    matching_stacks.sort(key=lambda x: len(x["coverage"]), reverse=True)

    total_tokens_saved = sum(s["tokens_saved"] for s in stack if s["tools"])

    return JSONResponse({
        "stack": stack,
        "matching_stacks": matching_stacks,
        "summary": {
            "total_needs": len(need_list),
            "needs_covered": sum(1 for s in stack if s["tools"]),
            "total_tokens_saved": total_tokens_saved,
        },
    })
```

**Step 3: Update llms.txt**

In the `llms_txt` function, add this line to the API Endpoints section (after `/api/collections`):

```
- GET /api/stack-builder?needs={{needs}}&budget={{n}} — Build an indie tool stack. Provide comma-separated needs (auth,payments,analytics) and optional max monthly budget.
```

And add to Key Pages section:

```
- /use-cases — Use case comparison pages (auth, payments, analytics, etc.)
- /use-cases/{{slug}} — Detailed comparison for a specific use case
```

**Step 4: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read()); print('OK')"`
Expected: `OK`

**Step 5: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: add /api/stack-builder endpoint for agent tool procurement"
```

---

## Task 3: Add build_stack MCP tool

**Files:**
- Modify: `src/indiestack/mcp_server.py` — insert new tool before `if __name__` (line 509)

**Step 1: Add the build_stack tool**

Insert before `if __name__ == "__main__":` (line 509):

```python
@mcp.tool()
def build_stack(needs: str, budget: int = 0) -> str:
    """Build an indie tool stack for your requirements.

    Provide comma-separated needs and get recommended tools for each.
    Returns the best indie tool for each need, matching Vibe Stacks, and total tokens saved.

    Args:
        needs: Comma-separated requirements (e.g. "auth,payments,analytics,email")
        budget: Optional max monthly price per tool in GBP (0 = no limit)
    """
    params = {"needs": needs}
    if budget > 0:
        params["budget"] = str(budget)
    try:
        data = _api_get("/api/stack-builder", params)
    except Exception as e:
        return f"Could not build stack: {e}"

    stack = data.get("stack", [])
    matching = data.get("matching_stacks", [])
    summary = data.get("summary", {})

    lines = [f"# Recommended Indie Stack ({summary.get('needs_covered', 0)}/{summary.get('total_needs', 0)} needs covered)\n"]
    lines.append(f"**Total tokens saved:** {summary.get('total_tokens_saved', 0):,}\n")

    for s in stack:
        lines.append(f"\n## {s['need'].title()} ({s['category']})")
        lines.append(f"*Tokens saved: {s['tokens_saved']:,} | Matched via: {s['matched_via']}*\n")
        if not s["tools"]:
            lines.append("No tools found for this need.\n")
            continue
        for t in s["tools"]:
            verified = " \u2705" if t["verified"] else ""
            lines.append(
                f"- **{t['name']}**{verified} — {t['tagline']}\n"
                f"  {t['price']} | {t['upvotes']} upvotes | {t['url']}"
            )

    if matching:
        lines.append(f"\n---\n\n## Matching Vibe Stacks")
        for ms in matching:
            lines.append(
                f"- **{ms['title']}** — covers: {', '.join(ms['coverage'])}\n"
                f"  {ms['tool_count']} tools, {ms['discount']}% bundle discount | {ms['url']}"
            )

    return "\n".join(lines)
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/mcp_server.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/indiestack/mcp_server.py
git commit -m "feat: add build_stack MCP tool"
```

---

## Task 4: Create Use Case Pages route file

**Files:**
- Create: `src/indiestack/routes/use_cases.py`

**Context needed:**
- Read `src/indiestack/routes/components.py` line 756+ for `tool_card` function signature
- Read `src/indiestack/routes/components.py` line 1027+ for `page_shell` function signature
- Patterns from existing route files (landing.py, alternatives.py) for HTML structure
- Import from `indiestack.db`: `get_all_categories`, `get_category_by_slug`, `get_tools_by_category`, `search_tools`, `CATEGORY_TOKEN_COSTS`, `NEED_MAPPINGS`
- Import from `indiestack.config`: `BASE_URL`
- Import from `indiestack.routes.components`: `page_shell`, `tool_card`

**Step 1: Create the route file**

Create `src/indiestack/routes/use_cases.py` with:

```python
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
        <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin:0 0 6px;">{title}</h3>
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
    verified = '\u2705' if tool.get('is_verified') else ''
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
        <td style="padding:12px;text-align:center;">{verified}</td>
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
                Compare indie tools by use case. Each page shows the best tools, token savings, and build-vs-buy analysis.
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
        "Use Cases — Compare Indie Tools",
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
    verified_count = sum(1 for t in tools if t.get('is_verified'))

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
                These indie tools are alternatives to:
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
            <span style="margin:0 6px;">/</span>
            <a href="/use-cases" style="color:var(--ink-muted);text-decoration:none;">Use Cases</a>
            <span style="margin:0 6px;">/</span>
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
                <div style="font-size:12px;color:var(--ink-muted);">indie tools</div>
            </div>
            <div style="text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{verified_count}</div>
                <div style="font-size:12px;color:var(--ink-muted);">verified</div>
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
                and ~<strong>{tokens_saved:,} tokens</strong> of AI-assisted development. Or use one of these indie tools
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
                        <th style="padding:12px;text-align:center;font-weight:600;color:var(--ink);">Verified</th>
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
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/routes/use_cases.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/indiestack/routes/use_cases.py
git commit -m "feat: add use case comparison pages (HTML + JSON-LD)"
```

---

## Task 5: Add JSON API endpoints for use cases

**Files:**
- Modify: `src/indiestack/main.py` — add two API endpoints after the stack-builder endpoint

**Step 1: Add /api/use-cases and /api/use-cases/{slug} endpoints**

Insert after the `/api/stack-builder` endpoint:

```python
@app.get("/api/use-cases")
async def api_use_cases(request: Request):
    """JSON API listing all use cases with tool counts."""
    d = request.state.db
    categories = await db.get_all_categories(d)
    cat_counts = {c['slug']: int(c.get('tool_count', 0)) for c in categories}

    results = []
    for slug, uc in sorted(NEED_MAPPINGS.items(), key=lambda x: x[1].get("title", "")):
        cat_slug = uc.get("category", "")
        results.append({
            "slug": slug,
            "title": uc.get("title", slug.title()),
            "description": uc.get("description", ""),
            "icon": uc.get("icon", ""),
            "category_slug": cat_slug,
            "tool_count": cat_counts.get(cat_slug, 0),
            "tokens_estimate": CATEGORY_TOKEN_COSTS.get(cat_slug, 50_000),
            "build_estimate": uc.get("build_estimate", "varies"),
            "competitors": uc.get("competitors", []),
            "url": f"{BASE_URL}/use-cases/{slug}",
            "api_url": f"{BASE_URL}/api/use-cases/{slug}",
        })
    return JSONResponse({"use_cases": results, "total": len(results)})


@app.get("/api/use-cases/{slug}")
async def api_use_case_detail(request: Request, slug: str):
    """JSON API for a single use case with its tools."""
    d = request.state.db
    uc = NEED_MAPPINGS.get(slug)
    if not uc:
        cat = await db.get_category_by_slug(d, slug)
        if not cat:
            return JSONResponse({"error": "Use case not found"}, status_code=404)
        uc = {
            "title": cat['name'], "description": f"Indie {cat['name'].lower()} tools.",
            "category": cat['slug'], "competitors": [], "build_estimate": "varies", "icon": "",
            "terms": [],
        }

    # Reuse the route helper for fetching tools
    from indiestack.routes.use_cases import _get_tools_for_use_case
    tools = await _get_tools_for_use_case(d, slug)

    cat_slug = uc.get("category", "")
    tool_results = []
    for t in tools:
        pp = t.get('price_pence')
        tool_results.append({
            "name": t['name'], "slug": t['slug'], "tagline": t.get('tagline', ''),
            "price": f"\u00a3{pp/100:.2f}" if pp and pp > 0 else "Free",
            "verified": bool(t.get('is_verified', 0)),
            "upvotes": int(t.get('upvote_count', 0)),
            "replaces": t.get('replaces', ''),
            "url": f"{BASE_URL}/tool/{t['slug']}",
        })

    return JSONResponse({
        "slug": slug,
        "title": uc.get("title", slug.title()),
        "description": uc.get("description", ""),
        "icon": uc.get("icon", ""),
        "tokens_estimate": CATEGORY_TOKEN_COSTS.get(cat_slug, 50_000),
        "build_estimate": uc.get("build_estimate", "varies"),
        "competitors": uc.get("competitors", []),
        "tools": tool_results,
        "total_tools": len(tool_results),
        "url": f"{BASE_URL}/use-cases/{slug}",
    })
```

**Step 2: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read()); print('OK')"`
Expected: `OK`

**Step 3: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: add /api/use-cases JSON endpoints"
```

---

## Task 6: Register use_cases router + update sitemap

**Files:**
- Modify: `src/indiestack/main.py` — add import and include_router, update sitemap

**Step 1: Add import**

After line 98 (`from indiestack.routes import embed`), add:

```python
from indiestack.routes import use_cases
```

**Step 2: Add include_router**

After line 2339 (`app.include_router(launch_with_me.router)`), add:

```python
app.include_router(use_cases.router)
```

**Step 3: Add to sitemap**

In the `sitemap` function, after the alternatives section (around line 613), add:

```python
    # Use case pages
    urls.append((f"{BASE_URL}/use-cases", "weekly", "0.8"))
    for uc_slug in db.NEED_MAPPINGS:
        urls.append((f"{BASE_URL}/use-cases/{uc_slug}", "weekly", "0.7"))
```

**Step 4: Update llms.txt API section**

Add to the API Endpoints section:
```
- GET /api/use-cases — All use cases with tool counts and token estimates.
- GET /api/use-cases/{{slug}} — Detailed use case with comparison tools.
```

**Step 5: Verify syntax**

Run: `python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read()); print('OK')"`
Expected: `OK`

**Step 6: Commit**

```bash
git add src/indiestack/main.py
git commit -m "feat: register use_cases router, update sitemap and llms.txt"
```

---

## Task 7: Verify and deploy

**Step 1: Run full syntax check on all modified files**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/db.py').read()); print('db.py OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read()); print('main.py OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/mcp_server.py').read()); print('mcp_server.py OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/use_cases.py').read()); print('use_cases.py OK')"
```

**Step 2: Run smoke test**

```bash
python3 smoke_test.py
```

Expected: 37/37 passing

**Step 3: Deploy**

```bash
~/.fly/bin/flyctl deploy --remote-only --buildkit
```

**Step 4: Verify new endpoints**

```bash
curl -s "https://indiestack.fly.dev/api/stack-builder?needs=auth,payments,analytics" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['summary'])"
curl -s "https://indiestack.fly.dev/api/use-cases" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['total'], 'use cases')"
curl -s -o /dev/null -w '%{http_code}' "https://indiestack.fly.dev/use-cases"
curl -s -o /dev/null -w '%{http_code}' "https://indiestack.fly.dev/use-cases/auth"
```

Expected: Stack builder returns summary, 18 use cases, 200 for both HTML pages.

**Step 5: Run smoke test against production**

```bash
python3 smoke_test.py
```

Expected: 37/37 passing

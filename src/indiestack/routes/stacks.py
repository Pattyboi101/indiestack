"""Stacks — curated 1-click tool bundles with bundle discount."""

import os
import json
import logging
from html import escape

import stripe
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.config import BASE_URL

from indiestack.routes.components import page_shell, tool_card, stack_card, user_stack_card
from indiestack.db import (
    get_stacks_by_source, get_stack_stats,
    get_stack_with_tools, get_stack_by_id,
    create_stack_purchase, get_stack_purchase_by_session,
    get_stack_purchase_by_token, get_active_subscription,
    create_purchase, CATEGORY_TOKEN_COSTS,
    get_user_stack_by_username, get_public_stacks,
)
from indiestack.payments import (
    create_stack_checkout_session, create_transfer,
    calculate_commission, PLATFORM_FEE_PERCENT, PRO_FEE_PERCENT,
)

from indiestack.routes.compare import _health_badge

logger = logging.getLogger("indiestack.stacks")
router = APIRouter()

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
MARKETPLACE_ENABLED = False


def format_price(pence: int) -> str:
    pounds = pence / 100
    if pounds == int(pounds):
        return f"\u00a3{int(pounds)}"
    return f"\u00a3{pounds:.2f}"


@router.get("/stacks", response_class=HTMLResponse)
async def stacks_index(request: Request):
    """Browse all Stacks — intelligence-powered discovery hub."""
    db = request.state.db

    stats = await get_stack_stats(db)
    framework_stacks = await get_stacks_by_source(db, "auto-framework")
    usecase_stacks = await get_stacks_by_source(db, "auto-usecase")
    curated_stacks_list = await get_stacks_by_source(db, "curated")
    community_stacks_list = await get_public_stacks(db, limit=6)

    # Batch-fetch distinct category slugs per stack for card icons
    all_display_stacks = list(framework_stacks) + list(usecase_stacks) + list(curated_stacks_list)
    stack_ids = [s['id'] for s in all_display_stacks if s.get('id')]
    cats_by_stack = {}
    if stack_ids:
        placeholders = ",".join("?" * len(stack_ids))
        cursor = await db.execute(
            f"""SELECT st.stack_id, c.slug as cat_slug
                FROM stack_tools st
                JOIN tools t ON t.id = st.tool_id
                JOIN categories c ON c.id = t.category_id
                WHERE st.stack_id IN ({placeholders})
                ORDER BY st.stack_id, st.position
            """, tuple(stack_ids))
        rows = await cursor.fetchall()
        for r in rows:
            sid = r['stack_id']
            if sid not in cats_by_stack:
                cats_by_stack[sid] = []
            cs = r['cat_slug']
            if cs not in cats_by_stack[sid]:
                cats_by_stack[sid].append(cs)
    for s in all_display_stacks:
        s['_category_slugs'] = cats_by_stack.get(s.get('id'), [])

    hero_html = f"""
    <div style="text-align:center;margin-bottom:48px;">
        <h1 style="font-family:var(--font-display);font-size:clamp(28px,5vw,48px);color:var(--ink);margin-bottom:12px;">
            Stacks That Actually Work
        </h1>
        <p style="color:var(--ink-muted);font-size:18px;max-width:600px;margin:0 auto 32px;">
            Built from {stats['pair_count']:,} compatibility pairs across {stats['tool_count']:,} tools.
            Every stack is backed by agent-verified data, not self-reported profiles.
        </p>
        <div style="display:flex;flex-wrap:wrap;justify-content:center;gap:24px;">
            <div style="text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{stats['pair_count']:,}+</div>
                <div style="font-size:13px;color:var(--ink-muted);font-weight:600;">Compatibility Pairs</div>
            </div>
            <div style="text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{stats['tool_count']:,}+</div>
                <div style="font-size:13px;color:var(--ink-muted);font-weight:600;">Tools Indexed</div>
            </div>
            <div style="text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{stats['auto_stack_count']}</div>
                <div style="font-size:13px;color:var(--ink-muted);font-weight:600;">Auto-Generated Stacks</div>
            </div>
            <div style="text-align:center;">
                <div style="font-family:var(--font-display);font-size:28px;color:var(--accent);">{stats['framework_count']}</div>
                <div style="font-size:13px;color:var(--ink-muted);font-weight:600;">Frameworks Covered</div>
            </div>
        </div>
    </div>
    """

    generator_html = """
    <div class="card" style="padding:32px;text-align:center;margin-bottom:48px;
                             border:2px solid var(--accent);background:var(--cream);">
        <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
            Analyse Your Dependencies
        </h2>
        <p style="color:var(--ink-muted);font-size:15px;margin-bottom:20px;max-width:540px;margin-left:auto;margin-right:auto;">
            Paste your <code style="font-family:var(--font-mono);background:var(--cream-dark);padding:2px 6px;border-radius:4px;font-size:13px;">package.json</code>
            or <code style="font-family:var(--font-mono);background:var(--cream-dark);padding:2px 6px;border-radius:4px;font-size:13px;">requirements.txt</code>
            &mdash; we'll scan your deps and show you indie tools that can replace big-tech dependencies.
        </p>
        <a href="/stacks/generator" class="btn btn-primary" style="font-size:16px;padding:14px 32px;">
            Paste &amp; Scan &rarr;
        </a>
    </div>
    """

    if framework_stacks:
        fw_cards = "\n".join(stack_card(s) for s in framework_stacks)
        framework_html = f"""
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
                Framework Stacks
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:20px;">
                Tools grouped by framework compatibility — auto-generated from {stats['pair_count']:,} verified pairs.
            </p>
            <div class="card-grid">{fw_cards}</div>
        </div>
        """
    else:
        framework_html = ""

    if usecase_stacks:
        uc_cards = "\n".join(stack_card(s) for s in usecase_stacks)
        usecase_html = f"""
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
                Use Case Stacks
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:20px;">
                Pre-built combinations for common project types — every tool has compatibility data with the others.
            </p>
            <div class="card-grid">{uc_cards}</div>
        </div>
        """
    else:
        usecase_html = ""

    if curated_stacks_list:
        curated_cards = "\n".join(stack_card(s) for s in curated_stacks_list)
        curated_html = f"""
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
                Curated Bundles
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:20px;">
                Hand-picked tool bundles with bundle discounts.
            </p>
            <div class="card-grid">{curated_cards}</div>
        </div>
        """
    else:
        curated_html = ""

    if community_stacks_list:
        community_cards = "\n".join(user_stack_card(s) for s in community_stacks_list)
        community_html = f"""
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
                Community Stacks
            </h2>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:20px;">
                See what other developers are building with.
            </p>
            <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px;">
                {community_cards}
            </div>
        </div>
        """
    else:
        community_html = """
        <div style="margin-bottom:48px;">
            <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin-bottom:8px;">
                Community Stacks
            </h2>
            <div class="card" style="padding:32px;text-align:center;">
                <p style="color:var(--ink-muted);font-size:15px;margin-bottom:16px;">
                    Share your stack &mdash; show what tools you use and why.
                </p>
                <a href="/dashboard/my-stack" class="btn btn-primary" style="font-size:14px;padding:12px 24px;">
                    Create Your Stack &rarr;
                </a>
            </div>
        </div>
        """

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:1000px;">
        {hero_html}
        {generator_html}
        {framework_html}
        {usecase_html}
        {curated_html}
        {community_html}
    </div>
    """
    return HTMLResponse(page_shell(
        "Stacks — Intelligence-Powered Tool Combinations",
        body,
        description=f"Stacks built from {stats['pair_count']:,}+ compatibility pairs. Framework stacks, use-case bundles, and community stacks — all backed by agent-verified data.",
        user=request.state.user,
        canonical="/stacks",
    ))


@router.get("/stacks/community", response_class=HTMLResponse)
async def community_stacks(request: Request):
    """Gallery of public user-curated stacks."""
    db = request.state.db
    stacks = await get_public_stacks(db, limit=30)

    cards_html = ''
    if stacks:
        for s in stacks:
            cards_html += user_stack_card(s)
    else:
        cards_html = """
        <div style="text-align:center;padding:60px 20px;">
            <div style="margin-bottom:16px;"><svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg></div>
            <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);">No stacks yet</h2>
            <p style="color:var(--ink-muted);margin:8px 0 24px 0;">Be the first to create a public stack!</p>
            <a href="/dashboard/my-stack" class="btn btn-primary">Create Your Stack &rarr;</a>
        </div>"""

    body = f"""
    <div class="container" style="max-width:1000px;padding:48px 24px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,36px);color:var(--ink);margin-bottom:8px;">
                Community Stacks
            </h1>
            <p style="color:var(--ink-muted);font-size:18px;margin:0;">
                See what developer tools other developers are using
            </p>
        </div>
        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:20px;">
            {cards_html}
        </div>
    </div>"""

    return HTMLResponse(page_shell("Community Stacks", body, user=request.state.user,
                                   description="Browse curated indie stacks shared by the community."))


# ── Stack Generator — paste package.json / requirements.txt ──────────────


@router.get("/stacks/generator", response_class=HTMLResponse)
async def stack_generator_form(request: Request):
    """Form page: paste your package.json or requirements.txt to get indie alternatives."""
    body = """
    <div class="container" style="max-width:760px;padding:48px 24px;">
        <div style="text-align:center;margin-bottom:36px;">
            <span style="display:block;margin-bottom:12px;"><svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg></span>
            <h1 style="font-family:var(--font-display);font-size:clamp(26px,4vw,38px);color:var(--ink);margin-bottom:12px;">
                Stack Generator
            </h1>
            <p style="color:var(--ink-muted);font-size:17px;max-width:520px;margin:0 auto;line-height:1.6;">
                Paste your <code style="font-family:var(--font-mono);background:var(--cream-dark);padding:2px 8px;border-radius:var(--radius-sm);font-size:14px;">package.json</code> or
                <code style="font-family:var(--font-mono);background:var(--cream-dark);padding:2px 8px;border-radius:var(--radius-sm);font-size:14px;">requirements.txt</code>
                and we&rsquo;ll find indie replacements for your dependencies.
            </p>
        </div>

        <form method="post" action="/stacks/generator">
            <label for="deps" style="font-weight:600;color:var(--ink);font-size:15px;display:block;margin-bottom:8px;">
                Your dependencies
            </label>
            <textarea id="deps" name="deps"
                      rows="14"
                      placeholder='{\n  "dependencies": {\n    "express": "^4.18.2",\n    "stripe": "^12.0.0",\n    "nodemailer": "^6.9.0"\n  }\n}\n\n&mdash; or &mdash;\n\nflask==3.0.0\nstripe>=5.0\ncelery[redis]'
                      style="width:100%;font-family:var(--font-mono);font-size:14px;padding:16px;
                             border:2px solid var(--border);border-radius:var(--radius-sm);
                             background:var(--card-bg);color:var(--ink);resize:vertical;
                             line-height:1.5;"></textarea>
            <button type="submit" class="btn btn-primary"
                    style="margin-top:16px;font-size:16px;padding:16px 40px;width:100%;">
                Find Indie Alternatives &rarr;
            </button>
        </form>

        <div style="margin-top:32px;padding:20px;border:1px dashed var(--border);border-radius:var(--radius-sm);">
            <p style="font-weight:600;color:var(--ink);font-size:14px;margin-bottom:8px;">How it works</p>
            <ol style="color:var(--ink-muted);font-size:14px;line-height:1.8;padding-left:20px;margin:0;">
                <li>Paste the contents of your <code style="font-family:var(--font-mono);font-size:13px;">package.json</code> or <code style="font-family:var(--font-mono);font-size:13px;">requirements.txt</code></li>
                <li>We extract dependency names and search our indie catalog</li>
                <li>You get a list of indie-built alternatives for each dependency</li>
            </ol>
        </div>
    </div>
    """
    return HTMLResponse(page_shell(
        "Stack Generator — Find Indie Alternatives", body,
        user=request.state.user,
        description="Paste your package.json or requirements.txt and discover indie tool replacements for your dependencies.",
    ))


@router.post("/stacks/generator", response_class=HTMLResponse)
async def stack_generator_results(request: Request, deps: str = Form("")):
    """Parse pasted dependencies and find matching developer tools."""
    db = request.state.db
    pasted_text = deps.strip()

    if not pasted_text:
        return RedirectResponse(url="/stacks/generator", status_code=303)

    # Extract dependency names
    dependencies: list[str] = []
    try:
        pkg = json.loads(pasted_text)
        dependencies = list(pkg.get('dependencies', {}).keys()) + list(pkg.get('devDependencies', {}).keys())
    except (json.JSONDecodeError, AttributeError):
        # Try requirements.txt format
        for line in pasted_text.split('\n'):
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('-'):
                pkg_name = line.split('==')[0].split('>=')[0].split('<=')[0].split('!=')[0].split('[')[0].split(';')[0].strip()
                if pkg_name:
                    dependencies.append(pkg_name)

    # Cap at 30 to prevent abuse
    dependencies = dependencies[:30]

    if not dependencies:
        body = """
        <div class="container" style="max-width:760px;padding:48px 24px;text-align:center;">
            <h1 style="font-family:var(--font-display);font-size:28px;color:var(--ink);">No dependencies found</h1>
            <p style="color:var(--ink-muted);margin-top:8px;">
                We couldn&rsquo;t parse any package names from what you pasted.
                Make sure it&rsquo;s a valid <code>package.json</code> or <code>requirements.txt</code>.
            </p>
            <a href="/stacks/generator" class="btn btn-primary" style="margin-top:24px;">Try Again &rarr;</a>
        </div>
        """
        return HTMLResponse(page_shell("No Dependencies Found", body, user=request.state.user))

    # Search for indie matches
    matches = []
    unmatched = []
    for dep in dependencies:
        safe_dep = dep.replace('%', '').replace('_', ' ')
        cursor = await db.execute(
            """SELECT t.id, t.name, t.slug, t.tagline,
                      c.name as category_name, c.slug as category_slug,
                      t.price_pence, t.replaces, t.tags
               FROM tools t
               JOIN categories c ON t.category_id = c.id
               WHERE t.status = 'approved'
               AND (t.replaces LIKE ? OR t.tags LIKE ? OR t.name LIKE ?)
               LIMIT 3""",
            (f'%{safe_dep}%', f'%{safe_dep}%', f'%{safe_dep}%'))
        results = await cursor.fetchall()
        if results:
            matches.append({'dependency': dep, 'alternatives': [dict(r) for r in results]})
        else:
            unmatched.append(dep)

    # Build results HTML
    match_count = len(matches)
    total = len(dependencies)

    matches_html = ''
    for m in matches:
        dep_name = escape(m['dependency'])
        cards = ''
        for t in m['alternatives']:
            t_name = escape(str(t['name']))
            t_tagline = escape(str(t.get('tagline', '')))
            t_slug = escape(str(t.get('slug', '')))
            logo_html = '<div style="width:36px;height:36px;border-radius:var(--radius-sm);background:linear-gradient(135deg,var(--terracotta),var(--slate));display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:16px;">{}</div>'.format(t_name[0] if t_name else '?')
            cards += f"""
            <a href="/tool/{t_slug}" style="text-decoration:none;display:flex;align-items:center;gap:12px;
                     padding:12px 16px;border-radius:var(--radius-sm);border:1px solid var(--border);
                     background:var(--card-bg);transition:border-color .15s;">
                {logo_html}
                <div style="min-width:0;">
                    <div style="font-weight:600;color:var(--ink);font-size:15px;">{t_name}</div>
                    <div style="font-size:13px;color:var(--ink-muted);overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{t_tagline}</div>
                </div>
            </a>"""

        matches_html += f"""
        <div style="margin-bottom:28px;">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                <code style="font-family:var(--font-mono);font-size:14px;background:var(--cream-dark);
                             padding:4px 12px;border-radius:var(--radius-sm);color:var(--ink);">{dep_name}</code>
                <span style="font-size:13px;color:var(--ink-muted);">&rarr; {len(m['alternatives'])} indie alternative{'s' if len(m['alternatives']) != 1 else ''}</span>
            </div>
            <div style="display:flex;flex-direction:column;gap:8px;">
                {cards}
            </div>
        </div>"""

    # Unmatched section
    unmatched_html = ''
    if unmatched:
        dep_pills = ' '.join(
            f'<span style="display:inline-block;font-family:var(--font-mono);font-size:13px;background:var(--cream-dark);padding:4px 12px;border-radius:var(--radius-sm);color:var(--ink-muted);margin:4px 2px;">{escape(u)}</span>'
            for u in unmatched
        )
        unmatched_html = f"""
        <div style="margin-top:36px;padding:24px;border:1px dashed var(--border);border-radius:var(--radius-sm);">
            <p style="font-weight:600;color:var(--ink);font-size:15px;margin-bottom:12px;">
                No indie matches yet ({len(unmatched)})
            </p>
            <div style="line-height:2;">{dep_pills}</div>
            <p style="margin-top:16px;">
                <a href="/submit" style="color:var(--slate);font-weight:600;text-decoration:none;">
                    Built an indie alternative? Submit it to IndieStack &rarr;
                </a>
            </p>
        </div>"""

    body = f"""
    <div class="container" style="max-width:760px;padding:48px 24px;">
        <a href="/stacks/generator" style="color:var(--ink-muted);font-size:14px;font-weight:600;text-decoration:none;">&larr; Paste another file</a>

        <div style="margin-top:24px;margin-bottom:32px;">
            <h1 style="font-family:var(--font-display);font-size:clamp(24px,3.5vw,34px);color:var(--ink);margin-bottom:8px;">
                Your Indie Stack
            </h1>
            <p style="color:var(--ink-muted);font-size:16px;">
                We scanned <strong>{total}</strong> dependenc{'y' if total == 1 else 'ies'} and found
                <strong>{match_count}</strong> with indie alternatives.
            </p>
        </div>

        {matches_html}
        {unmatched_html}
    </div>
    """
    return HTMLResponse(page_shell(
        f"Stack Generator — {match_count} Indie Matches", body,
        user=request.state.user,
        description=f"Found {match_count} indie alternatives for {total} dependencies.",
    ))


@router.get("/stacks/{slug}", response_class=HTMLResponse)
async def stack_detail(request: Request, slug: str):
    """Stack detail page with compatibility matrix and intelligence data."""
    db = request.state.db
    stack, tools = await get_stack_with_tools(db, slug)

    if not stack:
        body = """
        <div class="container" style="text-align:center;padding:80px 24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Stack not found</h1>
            <p style="color:var(--ink-muted);margin-top:12px;">This stack doesn&rsquo;t exist or has been removed.</p>
            <a href="/stacks" class="btn btn-primary" style="margin-top:24px;">Browse Stacks</a>
        </div>
        """
        return HTMLResponse(page_shell("Stack Not Found", body, user=request.state.user), status_code=404)

    source = stack.get('source', 'curated')
    confidence = stack.get('confidence_score', 0) or 0
    tokens_saved = stack.get('total_tokens_saved', 0) or 0
    tokens_k = tokens_saved // 1000
    emoji = stack.get('cover_emoji', '') or '\U0001f4e6'
    title = escape(str(stack['title']))
    desc = escape(str(stack.get('description', '')))

    # Source badge
    if source == 'auto-framework':
        source_badge = '<span style="font-size:12px;font-weight:600;color:#1E40AF;background:#DBEAFE;padding:4px 12px;border-radius:999px;">Auto-generated from framework data</span>'
    elif source == 'auto-usecase':
        source_badge = '<span style="font-size:12px;font-weight:600;color:#7C3AED;background:#EDE9FE;padding:4px 12px;border-radius:999px;">Auto-generated from compatibility data</span>'
    else:
        source_badge = '<span style="font-size:12px;font-weight:600;color:#065F46;background:#D1FAE5;padding:4px 12px;border-radius:999px;">Curated by IndieStack</span>'

    # Replaces list
    replaces_html = ""
    replaces_raw = stack.get('replaces_json')
    if replaces_raw:
        try:
            replaces = json.loads(replaces_raw) if isinstance(replaces_raw, str) else replaces_raw
            if replaces:
                replaces_html = f'<span style="color:var(--ink-muted);font-size:14px;">Replaces: {escape(", ".join(replaces))}</span>'
        except (json.JSONDecodeError, TypeError):
            pass

    # Stats row
    # ── Compatibility Matrix ──
    tool_slugs = [t['slug'] for t in tools]
    slug_set = tuple(tool_slugs)

    pairs = {}
    conflicts = set()
    if len(slug_set) >= 2:
        placeholders = ",".join("?" * len(slug_set))
        cursor = await db.execute(
            f"SELECT tool_a_slug, tool_b_slug, success_count FROM tool_pairs WHERE tool_a_slug IN ({placeholders}) AND tool_b_slug IN ({placeholders})",
            slug_set + slug_set,
        )
        pair_rows = await cursor.fetchall()
        pairs = {(r['tool_a_slug'], r['tool_b_slug']): r['success_count'] for r in pair_rows}

        cursor = await db.execute(
            f"SELECT tool_a_slug, tool_b_slug FROM tool_conflicts WHERE tool_a_slug IN ({placeholders}) AND tool_b_slug IN ({placeholders})",
            slug_set + slug_set,
        )
        conflict_rows = await cursor.fetchall()
        conflicts = {(r['tool_a_slug'], r['tool_b_slug']) for r in conflict_rows}

    n = len(tools)
    max_pairs = n * (n - 1) // 2
    verified_count = sum(1 for sc in pairs.values() if sc > 0)
    inferred_count = sum(1 for sc in pairs.values() if sc == 0)
    conflict_count = len(conflicts)

    # Stats row (built after pair queries so we can show verified count)
    stats_items = [f'<span style="font-weight:600;">{len(tools)} tools</span>']
    total_pairs = verified_count + inferred_count
    if total_pairs > 0:
        stats_items.append(f'<span style="color:#065F46;font-weight:600;">{verified_count} of {max_pairs} pairs verified</span>')
    if tokens_k > 0:
        stats_items.append(f'<span>~{tokens_k}k tokens saved</span>')
    stats_html = ' &middot; '.join(stats_items)

    if 2 <= n <= 6:
        # Full grid matrix
        header_cells = ''.join(
            f'<th style="font-size:11px;font-weight:600;padding:6px 8px;color:var(--ink-muted);transform:rotate(-45deg);white-space:nowrap;">{escape(str(t["name"])[:12])}</th>'
            for t in tools
        )
        rows_html = ""
        for i, t1 in enumerate(tools):
            cells = f'<td style="font-size:12px;font-weight:600;padding:6px 8px;color:var(--ink);">{escape(str(t1["name"])[:12])}</td>'
            for j, t2 in enumerate(tools):
                if i == j:
                    cells += '<td style="text-align:center;color:var(--ink-muted);">&mdash;</td>'
                else:
                    a, b = sorted([t1['slug'], t2['slug']])
                    key = (a, b)
                    if key in conflicts:
                        cells += '<td style="text-align:center;color:#DC2626;font-weight:700;" title="Known conflict">&#10007;</td>'
                    elif key in pairs:
                        if pairs[key] > 0:
                            cells += '<td style="text-align:center;color:#059669;font-weight:700;" title="Verified compatible">&#10003;</td>'
                        else:
                            cells += '<td style="text-align:center;color:var(--ink-muted);" title="Inferred compatible">&middot;</td>'
                    else:
                        cells += '<td style="text-align:center;"></td>'
            rows_html += f'<tr>{cells}</tr>'

        matrix_html = f"""
        <div style="margin-bottom:40px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:12px;">
                Compatibility Matrix
            </h2>
            <div style="overflow-x:auto;">
                <table style="border-collapse:collapse;width:auto;">
                    <thead><tr><th></th>{header_cells}</tr></thead>
                    <tbody>{rows_html}</tbody>
                </table>
            </div>
            <div style="display:flex;gap:16px;margin-top:12px;font-size:12px;color:var(--ink-muted);">
                <span><span style="color:#059669;font-weight:700;">&#10003;</span> Verified</span>
                <span><span style="color:var(--ink-muted);">&middot;</span> Inferred</span>
                <span><span style="color:#DC2626;font-weight:700;">&#10007;</span> Conflict</span>
            </div>
        </div>
        """
    elif n >= 2:
        total_known = verified_count + inferred_count
        matrix_html = f"""
        <div class="card" style="padding:20px;margin-bottom:40px;">
            <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin-bottom:8px;">Compatibility</h3>
            <p style="color:var(--ink-muted);font-size:14px;">
                {total_known} of {max_pairs} possible pairs have compatibility data.
                {f'<span style="color:#059669;font-weight:600;">{verified_count} verified</span>, ' if verified_count else ''}
                {f'<span>{inferred_count} inferred</span>' if inferred_count else ''}
                {f', <span style="color:#DC2626;font-weight:600;">{conflict_count} conflicts</span>' if conflict_count else ''}
            </p>
        </div>
        """
    else:
        matrix_html = ""

    # ── Batch-query success rates ──
    success_rates = {}
    if tool_slugs:
        placeholders = ",".join("?" * len(tool_slugs))
        cursor = await db.execute(
            f"""SELECT tool_slug,
                       SUM(CASE WHEN success=1 THEN 1 ELSE 0 END) as wins,
                       COUNT(*) as total
                FROM agent_actions
                WHERE action='report_outcome' AND tool_slug IN ({placeholders})
                GROUP BY tool_slug""",
            tuple(tool_slugs),
        )
        for r in await cursor.fetchall():
            total = r['total']
            rate = round(r['wins'] / total * 100) if total > 0 else 0
            success_rates[r['tool_slug']] = {"rate": rate, "total": total}

    # ── Enhanced tool cards ──
    tool_cards = []
    for t in tools:
        name = escape(str(t['name']))
        tagline = escape(str(t.get('tagline', '')))
        t_slug = escape(str(t['slug']))
        cat_name = escape(str(t.get('category_name', '')))

        health = t.get('health_status') or 'unknown'
        health_html = _health_badge(health)

        mcp_views = t.get('mcp_view_count') or 0
        citation_html = f'<span style="font-size:13px;color:var(--ink-muted);">Cited by agents {mcp_views:,}x</span>' if mcp_views > 0 else ''

        sr = success_rates.get(t['slug'])
        sr_html = ''
        if sr and sr['total'] >= 3:
            sr_html = f'<span style="font-size:13px;color:#059669;font-weight:600;">{sr["rate"]}% success rate ({sr["total"]} reports)</span>'

        compat_count = 0
        for other in tools:
            if other['slug'] != t['slug']:
                key = tuple(sorted([t['slug'], other['slug']]))
                if key in pairs:
                    compat_count += 1
        compat_html = f'<span style="font-size:12px;color:var(--ink-muted);">Compatible with {compat_count}/{len(tools)-1} tools in stack</span>' if len(tools) > 1 else ''

        pp = t.get('price_pence', 0) or 0
        price_str = f"\u00a3{pp/100:.2f}" if pp > 0 else "Free"

        tool_cards.append(f"""
        <a href="/tool/{t_slug}" class="card" style="text-decoration:none;color:inherit;display:block;padding:20px;">
            <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:8px;">
                <h3 style="font-family:var(--font-display);font-size:17px;color:var(--ink);margin:0;">{name}</h3>
                {health_html}
            </div>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:12px;">{tagline}</p>
            <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-bottom:8px;">
                <span style="font-size:12px;font-weight:600;color:var(--ink-light);background:var(--cream-dark);padding:3px 10px;border-radius:999px;">{cat_name}</span>
                <span style="font-size:13px;font-weight:600;color:var(--ink);">{price_str}</span>
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;">
                {citation_html}
                {sr_html}
            </div>
            {f'<div style="margin-top:8px;">{compat_html}</div>' if compat_html else ''}
        </a>
        """)

    cards_html = "\n".join(tool_cards)

    # ── Pricing (curated only) ──
    if source == 'curated' and MARKETPLACE_ENABLED:
        discount_percent = stack.get('discount_percent', 15)
        full_price = sum(t.get('price_pence', 0) or 0 for t in tools)
        discount_amount = full_price * discount_percent // 100
        bundle_price = full_price - discount_amount
        has_paid = full_price > 0
        if has_paid:
            pricing_html = f"""
            <div class="card" style="text-align:center;padding:32px;margin-bottom:40px;">
                <div style="font-size:14px;color:var(--ink-muted);text-decoration:line-through;">{format_price(full_price)}</div>
                <div style="font-family:var(--font-display);font-size:36px;color:var(--ink);margin-bottom:4px;">{format_price(bundle_price)}</div>
                <div class="badge badge-success" style="font-weight:700;margin-bottom:16px;">Save {discount_percent}%</div>
                <form method="post" action="/api/checkout-stack">
                    <input type="hidden" name="stack_id" value="{stack['id']}">
                    <button type="submit" class="btn btn-primary" style="font-size:16px;padding:16px 40px;">Buy This Stack &rarr;</button>
                </form>
            </div>
            """
        else:
            pricing_html = ""
    else:
        pricing_html = ""

    # ── JSON-LD ──
    tools_jsonld = ",".join(
        f'{{"@type":"SoftwareApplication","name":"{escape(str(t["name"]))}","url":"{BASE_URL}/tool/{escape(str(t["slug"]))}"}}' for t in tools
    )
    jsonld = f"""
    <script type="application/ld+json">
    {{
        "@context":"https://schema.org",
        "@type":"ItemList",
        "name":"{title}",
        "description":"{escape(desc[:200])}",
        "numberOfItems":{len(tools)},
        "itemListElement":[{tools_jsonld}]
    }}
    </script>
    """

    body = f"""
    {jsonld}
    <div class="container" style="padding:48px 24px;max-width:900px;">
        <a href="/stacks" style="color:var(--ink-muted);font-size:14px;font-weight:600;">&larr; All Stacks</a>
        <div style="margin-top:16px;margin-bottom:32px;">
            <span style="font-size:48px;">{emoji}</span>
            <h1 style="font-family:var(--font-display);font-size:clamp(28px,4vw,42px);color:var(--ink);margin-top:12px;">
                {title}
            </h1>
            <div style="margin-top:8px;margin-bottom:8px;">{source_badge}</div>
            <p style="color:var(--ink-muted);font-size:17px;margin-top:8px;max-width:600px;">{desc}</p>
            <div style="display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin-top:12px;font-size:14px;color:var(--ink-muted);">
                {stats_html}
            </div>
            {f'<div style="margin-top:8px;">{replaces_html}</div>' if replaces_html else ''}
        </div>

        {pricing_html}
        {matrix_html}

        <h2 style="font-family:var(--font-display);font-size:22px;color:var(--ink);margin:0 0 20px;">
            What&rsquo;s in the Stack
        </h2>
        <div class="card-grid">{cards_html}</div>
    </div>
    """
    return HTMLResponse(page_shell(
        f"{stack['title']} — Stack",
        body,
        description=f"{len(tools)} indie developer tools that work together. {stack.get('description', '')}",
        user=request.state.user,
        canonical=f"/stacks/{slug}",
    ))


@router.post("/api/checkout-stack")
async def api_checkout_stack(request: Request, stack_id: int = Form(0)):
    """Create Stripe checkout for a Vibe Stack bundle."""
    user = request.state.user
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    if not STRIPE_SECRET_KEY:
        return RedirectResponse(url="/stacks", status_code=303)

    db = request.state.db
    stack = await get_stack_by_id(db, stack_id)
    if not stack:
        return RedirectResponse(url="/stacks", status_code=303)

    _, tools = await get_stack_with_tools(db, stack['slug'])
    paid_tools = [t for t in tools if t.get('price_pence') and t['price_pence'] > 0]
    if not paid_tools:
        return RedirectResponse(url=f"/stacks/{stack['slug']}", status_code=303)

    full_price = sum(t['price_pence'] for t in paid_tools)
    discount_percent = stack.get('discount_percent', 15)
    discount_amount = full_price * discount_percent // 100
    bundle_price = full_price - discount_amount

    base_url = str(request.base_url).rstrip("/").replace("http://", "https://")
    try:
        session = create_stack_checkout_session(
            stack_title=stack['title'],
            stack_id=stack['id'],
            total_pence=bundle_price,
            success_url=f"{base_url}/stacks/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{base_url}/stacks/{stack['slug']}",
            buyer_email=user.get('email', ''),
        )
        return RedirectResponse(url=session.url, status_code=303)
    except Exception as e:
        logger.error(f"Stack checkout failed: {e}")
        return RedirectResponse(url=f"/stacks/{stack['slug']}", status_code=303)


@router.get("/stacks/success", response_class=HTMLResponse)
async def stack_purchase_success(request: Request, session_id: str = ""):
    """Handle successful stack purchase — record purchase and distribute to makers."""
    if not session_id:
        return RedirectResponse(url="/stacks", status_code=303)

    db = request.state.db

    # Check if already processed
    existing = await get_stack_purchase_by_session(db, session_id)
    if existing:
        return RedirectResponse(url=f"/stacks/purchase/{existing['purchase_token']}", status_code=303)

    # Retrieve from Stripe
    try:
        stripe.api_key = STRIPE_SECRET_KEY
        session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        logger.error(f"Stack Stripe retrieve failed: {e}")
        return RedirectResponse(url="/stacks", status_code=303)

    if session.payment_status != 'paid':
        return RedirectResponse(url="/stacks", status_code=303)

    stack_id = int(session.metadata.get('stack_id', 0))
    if not stack_id:
        return RedirectResponse(url="/stacks", status_code=303)

    stack = await get_stack_by_id(db, stack_id)
    if not stack:
        return RedirectResponse(url="/stacks", status_code=303)

    buyer_email = ''
    if session.customer_details:
        buyer_email = session.customer_details.email or ''
    amount_total = session.amount_total or 0
    discount_percent = stack.get('discount_percent', 15)

    # Record the stack purchase
    purchase_token = await create_stack_purchase(
        db, stack_id=stack_id, buyer_email=buyer_email,
        stripe_session_id=session_id, total_amount_pence=amount_total,
        discount_pence=amount_total * discount_percent // (100 - discount_percent) if discount_percent < 100 else 0,
    )

    # Distribute to each maker
    _, tools = await get_stack_with_tools(db, stack['slug'])
    paid_tools = [t for t in tools if t.get('price_pence') and t['price_pence'] > 0]
    full_price = sum(t['price_pence'] for t in paid_tools) or 1

    transfer_group = f"stack_{purchase_token}"

    for t in paid_tools:
        tool_share_ratio = t['price_pence'] / full_price
        tool_amount = int(amount_total * tool_share_ratio)

        # Check if maker has Pro subscription for commission rate
        is_pro = False
        if t.get('maker_id'):
            maker_user_cur = await db.execute("SELECT id FROM users WHERE maker_id = ?", (t['maker_id'],))
            maker_user_row = await maker_user_cur.fetchone()
            if maker_user_row:
                sub = await get_active_subscription(db, maker_user_row['id'])
                is_pro = sub is not None

        commission = calculate_commission(tool_amount, is_pro=is_pro)
        maker_payout = tool_amount - commission

        # Get maker's Stripe account
        stripe_acct_cur = await db.execute(
            "SELECT stripe_account_id FROM tools WHERE id = ?", (t['id'],))
        stripe_acct_row = await stripe_acct_cur.fetchone()
        stripe_account_id = stripe_acct_row['stripe_account_id'] if stripe_acct_row else ''

        if stripe_account_id and maker_payout > 0:
            try:
                create_transfer(maker_payout, stripe_account_id, transfer_group)
            except Exception as e:
                logger.error(f"Transfer to {stripe_account_id} failed: {e}")

        # Create individual purchase record for delivery tracking
        try:
            await create_purchase(
                db, tool_id=t['id'], buyer_email=buyer_email,
                stripe_session_id=f"{session_id}_stack_{t['id']}",
                amount_pence=tool_amount, commission_pence=commission,
                discount_pence=t['price_pence'] - tool_amount,
            )
        except Exception as e:
            logger.error(f"Individual purchase record failed for tool {t['id']}: {e}")

    return RedirectResponse(url=f"/stacks/purchase/{purchase_token}", status_code=303)


@router.get("/stacks/purchase/{token}", response_class=HTMLResponse)
async def stack_purchase_delivery(request: Request, token: str):
    """Show stack purchase confirmation with all tool delivery info."""
    db = request.state.db
    purchase = await get_stack_purchase_by_token(db, token)
    if not purchase:
        body = """
        <div class="container" style="text-align:center;padding:80px 24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Purchase not found</h1>
            <a href="/stacks" class="btn btn-primary" style="margin-top:24px;">Browse Stacks</a>
        </div>
        """
        return HTMLResponse(page_shell("Purchase Not Found", body, user=request.state.user), status_code=404)

    emoji = purchase.get('cover_emoji', '') or '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16.5 9.4 7.55 4.24"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>'
    stack_title = escape(str(purchase['stack_title']))
    amount = purchase['total_amount_pence']

    # Get the tools in this stack for delivery links
    _, tools = await get_stack_with_tools(db, purchase['stack_slug'])

    tool_delivery_html = ''
    for t in tools:
        name = escape(str(t['name']))
        delivery_url = t.get('delivery_url', '') or ''
        delivery_type = t.get('delivery_type', 'link')
        if delivery_url:
            tool_delivery_html += f"""
            <div class="card" style="padding:16px 20px;display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-weight:600;color:var(--ink);">{name}</div>
                    <div style="font-size:13px;color:var(--ink-muted);">{escape(str(t.get('tagline', '')))}</div>
                </div>
                <a href="{escape(delivery_url)}" target="_blank" class="btn btn-primary" style="font-size:13px;padding:8px 16px;">
                    {'Download' if delivery_type == 'download' else 'Access'} &rarr;
                </a>
            </div>
            """
        else:
            tool_delivery_html += f"""
            <div class="card" style="padding:16px 20px;display:flex;justify-content:space-between;align-items:center;">
                <div>
                    <div style="font-weight:600;color:var(--ink);">{name}</div>
                    <div style="font-size:13px;color:var(--ink-muted);">{escape(str(t.get('tagline', '')))}</div>
                </div>
                <a href="/tool/{escape(str(t.get('slug', '')))}" class="btn btn-primary" style="font-size:13px;padding:8px 16px;">
                    View &rarr;
                </a>
            </div>
            """

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:700px;">
        <div style="text-align:center;margin-bottom:32px;">
            <span style="display:block;margin-bottom:12px;"><svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></span>
            <h1 style="font-family:var(--font-display);font-size:28px;color:var(--ink);">
                Stack Purchased!
            </h1>
            <p style="color:var(--ink-muted);margin-top:8px;">
                {emoji} {stack_title} &middot; {format_price(amount)}
            </p>
        </div>

        <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);margin-bottom:16px;">
            Your Tools
        </h2>
        <div style="display:flex;flex-direction:column;gap:12px;">
            {tool_delivery_html}
        </div>

        <div style="text-align:center;margin-top:40px;">
            <a href="/dashboard" class="btn btn-primary">Go to Dashboard &rarr;</a>
        </div>
    </div>
    """
    return HTMLResponse(page_shell("Stack Purchased!", body, user=request.state.user))


@router.get("/stack/{username}", response_class=HTMLResponse)
async def public_user_stack(request: Request, username: str):
    """Public page showing a user's curated tool stack."""
    db = request.state.db
    stack, tools, stack_info = await get_user_stack_by_username(db, username)

    if not stack:
        body = f"""
        <div class="container" style="text-align:center;padding:80px 24px;">
            <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);">Stack not found</h1>
            <p style="color:var(--ink-muted);margin-top:12px;">This user hasn&rsquo;t created a public stack yet.</p>
            <a href="/stacks/community" class="btn btn-primary" style="margin-top:24px;">Browse community stacks &rarr;</a>
        </div>"""
        return HTMLResponse(page_shell("Stack Not Found", body, user=request.state.user), status_code=404)

    user_name = stack['user_name'] if stack.get('user_name') else username
    title = escape(str(stack.get('title', 'My Stack')))
    description = escape(str(stack.get('description', '')))
    tool_count = len(tools)

    # Build tool cards with optional personal notes
    cards_html = ''
    if tools:
        for t in tools:
            note = t.get('note', '')
            cards_html += tool_card(t)
            if note:
                cards_html += f'<div style="background:var(--surface,var(--cream));border-radius:var(--radius-sm);padding:12px 16px;margin:-8px 0 16px 0;font-size:14px;color:var(--ink-muted);border-left:3px solid var(--slate);"><svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle;margin-right:4px;"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg> {escape(str(note))}</div>'
    else:
        cards_html = '<p style="text-align:center;color:var(--ink-muted);padding:40px;">This stack is empty.</p>'

    # Share URL
    share_url = f"{BASE_URL}/stack/{escape(username)}"
    share_text = f"Check out {escape(user_name)}'s indie tool stack — {tool_count} tool{'s' if tool_count != 1 else ''} for building better software!"
    tweet_url = f"https://twitter.com/intent/tweet?text={share_text}&amp;url={share_url}"

    og_description = description or f"{escape(user_name)}'s curated collection of {tool_count} indie SaaS tools on IndieStack."

    body = f"""
    <div class="container" style="max-width:800px;padding:48px 24px;">
        <div style="background:linear-gradient(135deg,var(--terracotta) 0%,var(--terracotta-dark) 100%);border-radius:var(--radius);padding:40px;margin-bottom:32px;">
            <div style="display:flex;align-items:center;gap:16px;margin-bottom:16px;">
                <div style="width:56px;height:56px;border-radius:50%;background:linear-gradient(135deg,var(--slate),var(--success-text));
                            display:flex;align-items:center;justify-content:center;color:#fff;font-weight:700;font-size:24px;">
                    {escape(user_name[0].upper()) if user_name else '?'}
                </div>
                <div>
                    <h1 style="font-family:var(--font-display);color:#fff;font-size:clamp(22px,3vw,28px);margin:0;">{title}</h1>
                    <p style="color:rgba(255,255,255,0.6);margin:4px 0 0 0;font-size:15px;">by {escape(user_name)} &middot; {tool_count} tool{'s' if tool_count != 1 else ''}</p>
                </div>
            </div>
            {f'<p style="color:rgba(255,255,255,0.8);font-size:16px;line-height:1.6;margin:0;">{description}</p>' if description else ''}
            <div style="margin-top:24px;">
                <a href="{tweet_url}" target="_blank" rel="noopener"
                   style="background:var(--slate);color:var(--terracotta);padding:12px 24px;border-radius:999px;
                          text-decoration:none;font-weight:700;font-size:14px;">
                    Share on &#120143; &rarr;
                </a>
            </div>
        </div>

        <div class="card-grid">
            {cards_html}
        </div>

        <div style="text-align:center;margin-top:32px;">
            <a href="/stacks/community" style="color:var(--slate);text-decoration:none;font-weight:600;">
                &larr; Browse more community stacks
            </a>
        </div>
    </div>"""

    return HTMLResponse(page_shell(
        f"{stack.get('title', 'My Stack')} by {user_name}", body,
        user=request.state.user,
        description=og_description,
    ))

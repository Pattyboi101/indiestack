"""Programmatic 'alternatives to X' pages for SEO."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card
from indiestack.db import get_tools_replacing, get_all_competitors, slugify

router = APIRouter()


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

    # Build grid of competitor pills
    pills_html = ''
    for comp in competitors:
        comp_slug = slugify(comp)
        pills_html += f"""
        <a href="/alternatives/{escape(comp_slug)}" class="card"
           style="text-decoration:none;color:inherit;padding:16px 20px;display:flex;align-items:center;gap:12px;">
            <span style="font-size:24px;">&#9889;</span>
            <div>
                <div style="font-family:var(--font-display);font-size:16px;color:var(--ink);">{escape(comp)} alternatives</div>
                <div style="font-size:13px;color:var(--ink-muted);">Indie tools that replace {escape(comp)}</div>
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
                Why pay big-tech prices or burn tokens building from scratch?
                These indie tools do the same job &mdash; often better, always fairer.
            </p>
        </div>
        <div class="card-grid">{pills_html}</div>
    </div>
    """
    return HTMLResponse(page_shell("Indie Alternatives to Big Tech", body,
                                   description="Discover indie SaaS alternatives to popular big-tech tools. Save money, support indie makers.",
                                   user=request.state.user, canonical="/alternatives"))


@router.get("/alternatives/{competitor_slug}", response_class=HTMLResponse)
async def alternatives_for(request: Request, competitor_slug: str):
    """Show all indie tools that replace a specific competitor."""
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
                                       user=request.state.user))

    safe_name = escape(competitor_name)
    tool_count = len(tools)
    cards_parts = []
    for t in tools:
        card = tool_card(t)
        if t.get('boosted_competitor', ''):
            # Wrap boosted tool cards with a Featured badge
            card = f'''<div style="position:relative;">
                <span style="position:absolute;top:-8px;right:12px;background:#00D4F5;color:#1A2D4A;font-size:11px;
                    font-weight:700;padding:2px 10px;border-radius:999px;z-index:1;text-transform:uppercase;
                    letter-spacing:0.5px;">&#9733; Featured</span>
                {card}
            </div>'''
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
                Stop paying {safe_name} prices or burning tokens building a clone.
                These indie tools solve the same problem &mdash; built by humans, priced fairly.
            </p>
        </div>

        <div class="card-grid">{cards_html}</div>

        <div style="text-align:center;margin-top:48px;padding:32px;background:var(--cream-dark);border-radius:var(--radius);">
            <p style="font-family:var(--font-display);font-size:18px;color:var(--ink);margin-bottom:8px;">
                Built a better {safe_name}?
            </p>
            <p style="color:var(--ink-muted);font-size:14px;margin-bottom:16px;">
                List your tool on IndieStack and get discovered by developers searching for alternatives.
            </p>
            <a href="/submit" class="btn btn-primary">Submit Your Tool &rarr;</a>
        </div>
    </div>
    """
    return HTMLResponse(page_shell(f"Indie Alternatives to {safe_name}", body,
                                   description=f"Discover {tool_count} indie SaaS alternatives to {competitor_name}. Built by indie makers, priced fairly.",
                                   user=request.state.user, canonical=f"/alternatives/{competitor_slug}"))

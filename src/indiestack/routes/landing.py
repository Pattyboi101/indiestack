"""Landing page — hero, trending tools, category grid, how it works."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card
from indiestack.db import get_all_categories, get_trending_tools

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    db = request.state.db
    trending = await get_trending_tools(db, limit=6)
    categories = await get_all_categories(db)

    # ── Hero ──────────────────────────────────────────────────────────
    hero = """
    <section style="text-align:center;padding:72px 24px 56px;">
        <h1 style="font-family:var(--font-display);font-size:clamp(32px,5vw,52px);
                   font-weight:700;line-height:1.1;max-width:700px;margin:0 auto;">
            The best software built by
            <span style="background:linear-gradient(135deg,var(--amber),var(--violet));
                         -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                indie makers</span>
        </h1>
        <p style="font-size:18px;color:var(--stone-500);max-width:540px;margin:16px auto 32px;line-height:1.6;">
            Discover tools built by solo developers and tiny teams.
            Search by the problem you're solving, not the product name.
        </p>
        <form action="/search" method="GET" style="max-width:520px;margin:0 auto;">
            <div style="display:flex;align-items:center;background:white;border:2px solid var(--stone-200);
                        border-radius:var(--radius);padding:6px 6px 6px 16px;gap:8px;
                        transition:border-color 0.2s;box-shadow:0 2px 8px rgba(0,0,0,0.04);"
                 onfocus="this.style.borderColor='var(--amber)'" onblur="this.style.borderColor='var(--stone-200)'">
                <span style="font-size:18px;color:var(--stone-400);">&#128269;</span>
                <input type="text" name="q"
                       placeholder="I need to send invoices, track analytics, collect feedback..."
                       style="flex:1;border:none;outline:none;font-size:16px;font-family:var(--font-body);
                              padding:10px 0;background:transparent;color:var(--stone-800);">
                <button type="submit" class="btn btn-primary" style="padding:10px 20px;flex-shrink:0;">
                    Search
                </button>
            </div>
        </form>
    </section>
    """

    # ── Trending ──────────────────────────────────────────────────────
    trending_html = ""
    if trending:
        cards = "\n".join(tool_card(t) for t in trending)
        trending_html = f"""
        <section class="container" style="padding:0 24px 56px;">
            <div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:20px;">
                <h2 style="font-family:var(--font-display);font-size:24px;">Trending Tools</h2>
                <a href="/search?q=" style="color:var(--amber-dark);font-size:14px;font-weight:600;text-decoration:none;">
                    View all &rarr;
                </a>
            </div>
            <div class="card-grid">{cards}</div>
        </section>
        """

    # ── How it works (for makers) ─────────────────────────────────────
    how_it_works = """
    <section style="background:var(--stone-100);padding:56px 24px;margin:0 -24px;">
        <div class="container">
            <h2 style="font-family:var(--font-display);font-size:24px;text-align:center;margin-bottom:40px;">
                How IndieStack Works
            </h2>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:32px;max-width:800px;margin:0 auto;">
                <div style="text-align:center;">
                    <div style="font-size:32px;margin-bottom:12px;">&#128270;</div>
                    <h3 style="font-family:var(--font-display);font-size:17px;margin-bottom:8px;">Discover</h3>
                    <p class="text-muted text-sm">Search by the problem you need solved. No sponsored results, no noise.</p>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:32px;margin-bottom:12px;">&#9650;</div>
                    <h3 style="font-family:var(--font-display);font-size:17px;margin-bottom:8px;">Upvote</h3>
                    <p class="text-muted text-sm">Vote for tools you love. The best rise to the top organically.</p>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:32px;margin-bottom:12px;">&#128640;</div>
                    <h3 style="font-family:var(--font-display);font-size:17px;margin-bottom:8px;">Submit</h3>
                    <p class="text-muted text-sm">Built something? List it free or sell it directly on IndieStack.</p>
                </div>
            </div>
        </div>
    </section>
    """

    # ── Categories ────────────────────────────────────────────────────
    cat_cards = ""
    for c in categories:
        count = c.get("tool_count", 0)
        count_label = f"{count} tool{'s' if count != 1 else ''}" if count else "Coming soon"
        cat_cards += f"""
        <a href="/category/{escape(str(c['slug']))}" class="card"
           style="text-decoration:none;color:inherit;padding:20px;display:block;
                  transition:transform 0.15s,box-shadow 0.15s;"
           onmouseover="this.style.transform='translateY(-2px)';this.style.boxShadow='0 8px 24px rgba(0,0,0,0.08)'"
           onmouseout="this.style.transform='none';this.style.boxShadow='none'">
            <span style="font-size:28px;display:block;margin-bottom:8px;">{c['icon']}</span>
            <h3 style="font-family:var(--font-display);font-size:16px;margin-bottom:4px;">{escape(str(c['name']))}</h3>
            <p class="text-muted text-sm" style="margin-bottom:10px;">{escape(str(c['description']))}</p>
            <span style="font-size:12px;font-weight:600;color:var(--stone-500);background:var(--stone-100);
                         padding:3px 10px;border-radius:999px;">{count_label}</span>
        </a>
        """

    categories_html = f"""
    <section class="container" style="padding:56px 24px;">
        <h2 style="font-family:var(--font-display);font-size:24px;margin-bottom:20px;">Browse by Problem</h2>
        <div class="card-grid">{cat_cards}</div>
    </section>
    """

    # ── CTA ───────────────────────────────────────────────────────────
    cta = """
    <section style="text-align:center;padding:56px 24px;background:linear-gradient(135deg,var(--stone-900),var(--stone-800));
                    color:white;margin:0 -24px;">
        <h2 style="font-family:var(--font-display);font-size:28px;margin-bottom:12px;">Built something cool?</h2>
        <p style="color:var(--stone-400);margin-bottom:24px;font-size:16px;">
            List your tool for free or sell it directly to people who need it.
        </p>
        <a href="/submit" class="btn" style="background:var(--amber);color:var(--stone-900);font-weight:700;
                                              padding:14px 32px;font-size:16px;">
            Submit Your Tool &rarr;
        </a>
    </section>
    """

    body = hero + trending_html + how_it_works + categories_html + cta
    return HTMLResponse(page_shell("IndieStack — Discover Indie SaaS Tools", body,
                                   description="Discover the best software tools built by indie makers and solo developers. Search by problem, not product name."))

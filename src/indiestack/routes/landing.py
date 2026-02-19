from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, tool_card
from indiestack.db import get_all_categories, get_trending_tools

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    db = request.state.db
    trending_tools = await get_trending_tools(db, limit=6)
    categories = await get_all_categories(db)

    # --- Hero Section ---
    hero_html = """
    <section class="hero" style="text-align:center; padding:4rem 1rem 3rem;">
        <h1 style="font-size:2.8rem; margin-bottom:0.75rem;">Discover Indie SaaS Tools</h1>
        <p style="font-size:1.2rem; max-width:640px; margin:0 auto 2rem; opacity:0.85;">
            Find the perfect tool built by solo developers and small teams.
            Searchable by problem, not product name.
        </p>
        <form action="/search" method="GET" style="max-width:520px; margin:0 auto;">
            <div class="search-box" style="display:flex; align-items:center; background:#fff; border:1px solid #ddd; border-radius:8px; padding:0.5rem 1rem; gap:0.5rem;">
                <span style="font-size:1.2rem;">&#128269;</span>
                <input
                    type="text"
                    name="q"
                    placeholder="Search by problem you are trying to solve..."
                    style="flex:1; border:none; outline:none; font-size:1rem; padding:0.5rem 0;"
                />
            </div>
        </form>
    </section>
    """

    # --- Trending Tools Section ---
    tool_cards_html = "".join(tool_card(t) for t in trending_tools)
    trending_html = f"""
    <section style="padding:2rem 1rem 3rem;">
        <h2 style="font-size:1.8rem; margin-bottom:1.5rem;">&#128293; Trending Tools</h2>
        <div class="card-grid">
            {tool_cards_html}
        </div>
    </section>
    """

    # --- Category Grid Section ---
    category_cards = ""
    for cat in categories:
        category_cards += f"""
        <a href="/category/{cat["slug"]}" class="card" style="text-decoration:none; color:inherit; padding:1.5rem; border-radius:10px; border:1px solid #e5e5e5; display:block;">
            <span style="font-size:2rem; display:block; margin-bottom:0.5rem;">{cat["icon"]}</span>
            <h3 style="margin:0 0 0.25rem; font-size:1.1rem;">{cat["name"]}</h3>
            <p style="margin:0 0 0.75rem; font-size:0.9rem; opacity:0.7;">{cat["description"]}</p>
            <span class="badge" style="font-size:0.8rem; background:#f0f0f0; padding:0.2rem 0.6rem; border-radius:999px;">
                {cat["tool_count"]} tools
            </span>
        </a>
        """

    categories_html = f"""
    <section style="padding:2rem 1rem 3rem;">
        <h2 style="font-size:1.8rem; margin-bottom:1.5rem;">Browse by Problem</h2>
        <div class="card-grid">
            {category_cards}
        </div>
    </section>
    """

    body = hero_html + trending_html + categories_html
    return HTMLResponse(page_shell(title="IndieStack - Discover Indie SaaS Tools", body=body))

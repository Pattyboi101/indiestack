from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from html import escape

from indiestack.routes.components import page_shell, tool_card
from indiestack.db import search_tools

router = APIRouter()


@router.get("/search", response_class=HTMLResponse)
async def search(request: Request):
    query = request.query_params.get("q", "")
    safe_query = escape(query)

    search_box_html = f"""
    <form action="/search" method="GET" class="search-form" style="margin-bottom:2rem;">
        <input
            type="text"
            name="q"
            value="{safe_query}"
            placeholder="Search tools..."
            style="padding:0.75rem 1rem; font-size:1rem; border:1px solid #ccc; border-radius:6px; width:100%; max-width:480px;"
        />
        <button
            type="submit"
            style="padding:0.75rem 1.25rem; font-size:1rem; background:#0D7377; color:#fff; border:none; border-radius:6px; cursor:pointer; margin-left:0.5rem;"
        >Search</button>
    </form>
    """

    if not query.strip():
        body = search_box_html + """
        <p style="color:#666; font-size:1.1rem;">Enter a search term to find tools.</p>
        """
        return HTMLResponse(page_shell(title="Search", body=body))

    db = request.state.db
    results = await search_tools(db, query)

    if not results:
        body = search_box_html + f"""
        <h2>{len(results)} results for &ldquo;{safe_query}&rdquo;</h2>
        <p style="color:#666; font-size:1.1rem;">
            No tools found for that query. Try different keywords or
            <a href="/" style="color:#0D7377;">browse categories</a>.
        </p>
        """
        return HTMLResponse(page_shell(title=f"Search: {safe_query}", body=body))

    cards_html = "".join(tool_card(tool) for tool in results)
    body = search_box_html + f"""
    <h2>{len(results)} result{"s" if len(results) != 1 else ""} for &ldquo;{safe_query}&rdquo;</h2>
    <div class="card-grid">
        {cards_html}
    </div>
    """
    return HTMLResponse(page_shell(title=f"Search: {safe_query}", body=body))

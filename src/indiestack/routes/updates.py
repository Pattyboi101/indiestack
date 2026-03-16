"""Maker updates feed — build in public."""

from html import escape

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from indiestack.routes.components import page_shell, update_card
from indiestack.db import get_recent_updates

router = APIRouter()


@router.get("/updates", response_class=HTMLResponse)
async def updates_feed(request: Request):
    db = request.state.db
    updates = await get_recent_updates(db, limit=30)

    if updates:
        cards = '\n'.join(update_card(u) for u in updates)
    else:
        cards = '''<div style="text-align:center;padding:60px 20px;">
    <div style="margin-bottom:16px;"><svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m3 11 18-5v12L3 13v-2z"/><path d="M11.6 16.8a3 3 0 1 1-5.8-1.6"/></svg></div>
    <h2 style="font-family:var(--font-display);font-size:24px;color:var(--ink);">No updates yet</h2>
    <p style="color:var(--ink-muted);margin:8px 0 24px 0;">When makers post changelogs and updates, they&rsquo;ll appear here.</p>
    <a href="/makers" style="color:var(--cyan);font-weight:600;text-decoration:none;">Browse makers &rarr;</a>
</div>'''

    body = f"""
    <div class="container" style="padding:48px 24px;max-width:700px;">
        <div style="text-align:center;margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:36px;color:var(--ink);">Maker Updates</h1>
            <p style="color:var(--ink-muted);margin-top:8px;">See what indie makers are building, launching, and shipping.</p>
        </div>
        {cards}
    </div>
    """
    return HTMLResponse(page_shell("Maker Updates", body, description="Latest updates from indie makers on IndieStack.", user=request.state.user))

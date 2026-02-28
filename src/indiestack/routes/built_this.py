"""Lightweight 'Built This' submission — one-field form for first-time builders."""

import re
import logging
from html import escape

import httpx
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from indiestack.routes.components import page_shell
from indiestack.db import create_tool, get_tool_by_id, slugify

logger = logging.getLogger(__name__)

router = APIRouter()

TOPIC_CATEGORY_MAP = {
    "analytics": "analytics-metrics", "auth": "authentication", "authentication": "authentication",
    "billing": "invoicing-billing", "payments": "payments", "cms": "landing-pages",
    "crm": "crm-sales", "monitoring": "monitoring-uptime",
    "ai": "ai-dev-tools", "machine-learning": "ai-dev-tools", "llm": "ai-dev-tools",
    "automation": "ai-automation", "email": "email-marketing", "design": "design-creative",
    "forms": "forms-surveys", "support": "customer-support",
}


def _built_this_form(error: str = "", url_val: str = "", desc_val: str = "",
                     email_val: str = "", show_email: bool = False) -> str:
    alert = f'<div class="alert alert-error">{escape(error)}</div>' if error else ''
    email_field = ""
    if show_email:
        email_field = f"""
            <div class="form-group">
                <label for="email" style="font-size:14px;font-weight:600;color:var(--ink);">
                    Email <span style="color:var(--ink-muted);font-weight:400;">(so we can notify you)</span>
                </label>
                <input type="email" id="email" name="email" class="form-input"
                       value="{escape(email_val)}" placeholder="you@example.com">
            </div>
        """
    return f"""
    <div style="display:flex;justify-content:center;align-items:center;min-height:60vh;">
        <div class="card" style="max-width:520px;width:100%;">
            <div style="text-align:center;margin-bottom:28px;">
                <p style="font-size:32px;margin-bottom:8px;">&#128736;&#65039;</p>
                <h1 style="font-family:var(--font-display);font-size:28px;color:var(--ink);margin-bottom:8px;">
                    Just built something?
                </h1>
                <p style="color:var(--ink-muted);font-size:15px;line-height:1.5;">
                    Share it with 350+ indie tools and the devs who use them.
                </p>
            </div>
            {alert}
            <form method="post" action="/built-this">
                <div class="form-group">
                    <label for="url" style="font-size:14px;font-weight:600;color:var(--ink);">
                        Link to your project *
                    </label>
                    <input type="url" id="url" name="url" class="form-input" required
                           value="{escape(url_val)}"
                           placeholder="https://github.com/you/your-project">
                    <p style="font-size:12px;color:var(--ink-muted);margin-top:4px;">
                        GitHub repos get auto-filled. Any link works.
                    </p>
                </div>
                <div class="form-group">
                    <label for="description" style="font-size:14px;font-weight:600;color:var(--ink);">
                        One-sentence description <span style="color:var(--ink-muted);font-weight:400;">(optional for GitHub repos)</span>
                    </label>
                    <textarea id="description" name="description" class="form-textarea"
                              rows="2" placeholder="What does it do?">{escape(desc_val)}</textarea>
                </div>
                {email_field}
                <button type="submit" class="btn btn-primary" style="width:100%;justify-content:center;padding:14px;">
                    Share what I built &rarr;
                </button>
            </form>
            <p style="text-align:center;margin-top:16px;font-size:13px;color:var(--ink-muted);line-height:1.5;">
                We'll review it within 24 hours. Your project gets discovered<br>
                by AI agents via our <a href="/explore" style="color:var(--cyan);text-decoration:none;">MCP server</a>.
            </p>
        </div>
    </div>
    """


@router.get("/built-this", response_class=HTMLResponse)
async def built_this_get(request: Request):
    return RedirectResponse(url="/submit", status_code=301)


@router.post("/built-this", response_class=HTMLResponse)
async def built_this_post(
    request: Request,
    url: str = Form(""),
    description: str = Form(""),
    email: str = Form(""),
):
    db = request.state.db
    user = request.state.user
    show_email = not user

    url = url.strip()
    description = description.strip()

    if not url or not url.startswith("http"):
        body = _built_this_form("Please enter a valid URL starting with http.", url, description, email, show_email)
        return HTMLResponse(page_shell("Share What You Built", body, user=user))

    name = ""
    tagline = ""
    tags = ""
    github_url = ""
    github_stars = 0
    github_language = ""
    category_slug = "developer-tools"
    tool_url = url

    # GitHub auto-fill
    gh_match = re.match(r'https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$', url)
    if gh_match:
        owner, repo = gh_match.group(1), gh_match.group(2)
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}",
                                        headers={"Accept": "application/json"})
                if resp.status_code == 200:
                    data = resp.json()
                    name = data.get("name", repo).replace("-", " ").replace("_", " ").title()
                    gh_desc = data.get("description") or ""
                    tagline = gh_desc.split(". ")[0][:100] if gh_desc else name
                    if not description:
                        description = gh_desc
                    topics = data.get("topics", []) or []
                    language = data.get("language") or ""
                    tag_list = list(topics)
                    if language and language.lower() not in [t.lower() for t in tag_list]:
                        tag_list.append(language.lower())
                    tags = ", ".join(tag_list[:10])
                    github_url = url
                    github_stars = data.get("stargazers_count", 0)
                    github_language = language
                    tool_url = data.get("homepage") or url
                    if tool_url and not tool_url.startswith("http"):
                        tool_url = url
                    # Auto-detect category
                    for topic in topics:
                        if topic.lower() in TOPIC_CATEGORY_MAP:
                            category_slug = TOPIC_CATEGORY_MAP[topic.lower()]
                            break
        except Exception:
            logger.warning(f"GitHub API fetch failed for {owner}/{repo}")

    # For non-GitHub URLs, require description as tagline
    if not name:
        if not description:
            body = _built_this_form("Please add a short description for non-GitHub links.", url, description, email, show_email)
            return HTMLResponse(page_shell("Share What You Built", body, user=user))
        # Use domain as name fallback
        from urllib.parse import urlparse
        parsed = urlparse(url)
        name = parsed.hostname.replace("www.", "").split(".")[0].title() if parsed.hostname else "My Project"
        tagline = description[:100]

    # Look up category
    cursor = await db.execute("SELECT id FROM categories WHERE slug = ?", (category_slug,))
    cat_row = await cursor.fetchone()
    if not cat_row:
        cursor = await db.execute("SELECT id FROM categories WHERE slug = 'developer-tools'")
        cat_row = await cursor.fetchone()
    category_id = cat_row[0] if cat_row else 1

    tool_id = await create_tool(
        db, name=name, tagline=tagline, description=description or tagline,
        url=tool_url, maker_name="", maker_url="",
        category_id=category_id, tags=tags,
    )

    # Store GitHub fields
    if github_url:
        await db.execute(
            "UPDATE tools SET github_url = ?, github_stars = ?, github_language = ? WHERE id = ?",
            (github_url, github_stars, github_language, tool_id),
        )
        await db.commit()

    # Store email for non-logged-in users
    if not user and email.strip():
        await db.execute(
            "UPDATE tools SET submitter_email = ?, submitted_from_ip = ? WHERE id = ?",
            (email.strip().lower(), request.client.host, tool_id),
        )
        await db.commit()

    tool = await get_tool_by_id(db, tool_id)
    tool_slug = tool['slug'] if tool else slugify(name)
    return RedirectResponse(url=f"/submit?status=success&tool={tool_slug}", status_code=303)

"""Agent services registry — browse, detail, submit, and search API."""

import json
from html import escape

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from indiestack.config import BASE_URL
from indiestack.routes.components import page_shell
from indiestack.db import (
    search_agent_services,
    get_agent_service_by_slug,
    get_all_agent_services,
    create_agent_service,
    get_all_categories,
    slugify,
)

router = APIRouter()


# ── Helpers ──────────────────────────────────────────────────────────────

def _capability_pills(tags_str: str) -> str:
    """Render comma-separated capability tags as pill badges."""
    if not tags_str:
        return ""
    pills = []
    for tag in tags_str.split(","):
        tag = tag.strip()
        if tag:
            pills.append(
                f'<span style="display:inline-block;padding:4px 10px;'
                f'font-size:12px;font-family:var(--font-mono);'
                f'background:rgba(0,212,245,0.08);color:var(--accent);'
                f'border-radius:999px;margin:2px 4px 2px 0;">'
                f'{escape(tag)}</span>'
            )
    return "".join(pills)


def _format_cost(cents, unit: str = "per_task") -> str:
    """Format cost_estimate_cents into a readable string."""
    if cents is None:
        return "Free / Contact"
    dollars = cents / 100
    unit_label = unit.replace("_", " ") if unit else "per task"
    if dollars == int(dollars):
        return f"${int(dollars)} {unit_label}"
    return f"${dollars:.2f} {unit_label}"


def _agent_card(agent) -> str:
    """Render a single agent service card."""
    name = escape(agent["name"])
    tagline = escape(agent["tagline"] or "")
    slug = escape(agent["slug"])
    sla = agent["estimated_sla_minutes"] or 0
    cost_txt = _format_cost(agent["cost_estimate_cents"], agent["cost_unit"] or "per_task")
    success = agent["success_count"] or 0
    source = escape(agent["source_type"] or "saas")

    return f"""
    <a href="/agents/{slug}" style="text-decoration:none;color:inherit;display:block;">
        <div style="background:var(--card-bg);border:1px solid var(--border);
                    border-radius:12px;padding:24px;
                    transition:box-shadow 0.2s, border-color 0.2s;"
             onmouseover="this.style.borderColor='var(--accent)';this.style.boxShadow='var(--shadow-md)'"
             onmouseout="this.style.borderColor='var(--border)';this.style.boxShadow='none'">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px;">
                <h3 style="font-family:var(--font-display);font-size:18px;
                           color:var(--ink);margin:0;">{name}</h3>
                <span style="font-size:11px;font-family:var(--font-mono);
                             padding:3px 8px;border-radius:999px;
                             background:rgba(0,212,245,0.08);color:var(--accent);
                             white-space:nowrap;">{source}</span>
            </div>
            <p style="color:var(--ink-muted);font-size:14px;line-height:1.5;
                      margin:0 0 12px;">{tagline}</p>
            <div style="margin-bottom:12px;">
                {_capability_pills(agent["capability_tags"])}
            </div>
            <div style="display:flex;gap:16px;font-size:13px;color:var(--ink-muted);">
                <span title="Estimated SLA">
                    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14"
                         viewBox="0 0 24 24" fill="none" stroke="currentColor"
                         stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                         style="vertical-align:-2px;margin-right:2px;">
                        <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
                    </svg>
                    {sla}m SLA
                </span>
                <span title="Cost estimate">{escape(cost_txt)}</span>
                <span title="Successful executions">{success} runs</span>
            </div>
        </div>
    </a>
    """


# ── GET /agents — Browse page ────────────────────────────────────────────

@router.get("/agents", response_class=HTMLResponse)
async def agents_browse(request: Request):
    db = request.state.db
    user = request.state.user
    services = await get_all_agent_services(db, limit=100)

    cards = "".join(_agent_card(s) for s in services)
    if not cards:
        cards = """
        <div style="grid-column:1/-1;text-align:center;padding:48px 0;">
            <p style="color:var(--ink-muted);font-size:15px;">
                No agent services listed yet.
                <a href="/agents/submit" style="color:var(--accent);text-decoration:underline;">
                    Submit the first one</a>.
            </p>
        </div>
        """

    body = f"""
    <div class="container" style="max-width:1100px;padding:48px 24px;">
        <div style="display:flex;justify-content:space-between;align-items:center;
                    flex-wrap:wrap;gap:16px;margin-bottom:32px;">
            <div>
                <h1 style="font-family:var(--font-display);font-size:32px;color:var(--ink);
                           margin:0 0 8px;">Agent Services</h1>
                <p style="color:var(--ink-muted);font-size:15px;margin:0;">
                    Discoverable services that AI agents can invoke — APIs, automations, and tools
                    with structured I/O.
                </p>
            </div>
            <a href="/agents/submit" class="btn btn-primary"
               style="padding:12px 24px;font-size:14px;white-space:nowrap;">
                Submit a Service
            </a>
        </div>

        <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));
                    gap:20px;">
            {cards}
        </div>
    </div>
    """

    return HTMLResponse(page_shell(
        "Agent Services | IndieStack",
        body,
        description="Browse agent services — APIs and automations that AI coding agents can discover and invoke.",
        user=user,
        canonical="/agents",
    ))


# ── GET /agents/submit — Submission form ─────────────────────────────────

@router.get("/agents/submit", response_class=HTMLResponse)
async def agents_submit_form(request: Request):
    user = request.state.user
    msg = request.query_params.get("msg", "")

    success_banner = ""
    if msg:
        success_banner = f"""
        <div style="background:rgba(0,212,245,0.08);border:1px solid var(--accent);
                    border-radius:8px;padding:16px;margin-bottom:24px;
                    color:var(--accent);font-size:14px;">
            {escape(msg)}
        </div>
        """

    body = f"""
    <div class="container" style="max-width:640px;padding:48px 24px;">
        <h1 style="font-family:var(--font-display);font-size:28px;color:var(--ink);
                   margin:0 0 8px;">Submit an Agent Service</h1>
        <p style="color:var(--ink-muted);font-size:15px;margin:0 0 32px;">
            List a service that AI agents can discover and invoke.
        </p>

        {success_banner}

        <form method="POST" action="/agents/submit"
              style="display:flex;flex-direction:column;gap:20px;">

            <label style="font-size:14px;font-weight:600;color:var(--ink);">
                Name *
                <input name="name" required maxlength="120"
                       style="display:block;width:100%;margin-top:6px;padding:12px;
                              font-size:15px;border:1px solid var(--border);
                              border-radius:8px;background:var(--card-bg);
                              color:var(--ink);box-sizing:border-box;">
            </label>

            <label style="font-size:14px;font-weight:600;color:var(--ink);">
                Tagline *
                <input name="tagline" required maxlength="200"
                       placeholder="One-line description of what this service does"
                       style="display:block;width:100%;margin-top:6px;padding:12px;
                              font-size:15px;border:1px solid var(--border);
                              border-radius:8px;background:var(--card-bg);
                              color:var(--ink);box-sizing:border-box;">
            </label>

            <label style="font-size:14px;font-weight:600;color:var(--ink);">
                Description
                <textarea name="description" rows="4"
                          placeholder="Detailed explanation of the service capabilities"
                          style="display:block;width:100%;margin-top:6px;padding:12px;
                                 font-size:15px;border:1px solid var(--border);
                                 border-radius:8px;background:var(--card-bg);
                                 color:var(--ink);box-sizing:border-box;resize:vertical;">
                </textarea>
            </label>

            <label style="font-size:14px;font-weight:600;color:var(--ink);">
                Capability Tags *
                <input name="capability_tags" required
                       placeholder="e.g. code-review, testing, deployment, monitoring"
                       style="display:block;width:100%;margin-top:6px;padding:12px;
                              font-size:15px;border:1px solid var(--border);
                              border-radius:8px;background:var(--card-bg);
                              color:var(--ink);box-sizing:border-box;">
                <span style="font-size:12px;color:var(--ink-muted);">Comma-separated</span>
            </label>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px;">
                <label style="font-size:14px;font-weight:600;color:var(--ink);">
                    Estimated SLA (minutes) *
                    <input name="estimated_sla_minutes" type="number" required
                           value="5" min="1"
                           style="display:block;width:100%;margin-top:6px;padding:12px;
                                  font-size:15px;border:1px solid var(--border);
                                  border-radius:8px;background:var(--card-bg);
                                  color:var(--ink);box-sizing:border-box;">
                </label>

                <label style="font-size:14px;font-weight:600;color:var(--ink);">
                    Cost Estimate (cents)
                    <input name="cost_estimate" type="number" min="0"
                           placeholder="Leave blank if free"
                           style="display:block;width:100%;margin-top:6px;padding:12px;
                                  font-size:15px;border:1px solid var(--border);
                                  border-radius:8px;background:var(--card-bg);
                                  color:var(--ink);box-sizing:border-box;">
                </label>
            </div>

            <label style="font-size:14px;font-weight:600;color:var(--ink);">
                Input Schema (JSON)
                <textarea name="input_schema" rows="4"
                          placeholder='{"type": "object", "properties": {...}}'
                          style="display:block;width:100%;margin-top:6px;padding:12px;
                                 font-size:13px;font-family:var(--font-mono);
                                 border:1px solid var(--border);border-radius:8px;
                                 background:var(--card-bg);color:var(--ink);
                                 box-sizing:border-box;resize:vertical;">
                </textarea>
            </label>

            <label style="font-size:14px;font-weight:600;color:var(--ink);">
                Output Schema (JSON)
                <textarea name="output_schema" rows="4"
                          placeholder='{"type": "object", "properties": {...}}'
                          style="display:block;width:100%;margin-top:6px;padding:12px;
                                 font-size:13px;font-family:var(--font-mono);
                                 border:1px solid var(--border);border-radius:8px;
                                 background:var(--card-bg);color:var(--ink);
                                 box-sizing:border-box;resize:vertical;">
                </textarea>
            </label>

            <label style="font-size:14px;font-weight:600;color:var(--ink);">
                URL
                <input name="url" type="url" placeholder="https://..."
                       style="display:block;width:100%;margin-top:6px;padding:12px;
                              font-size:15px;border:1px solid var(--border);
                              border-radius:8px;background:var(--card-bg);
                              color:var(--ink);box-sizing:border-box;">
            </label>

            <label style="font-size:14px;font-weight:600;color:var(--ink);">
                Source Type *
                <select name="source_type" required
                        style="display:block;width:100%;margin-top:6px;padding:12px;
                               font-size:15px;border:1px solid var(--border);
                               border-radius:8px;background:var(--card-bg);
                               color:var(--ink);box-sizing:border-box;">
                    <option value="saas">SaaS (hosted API)</option>
                    <option value="code">Code (self-hosted)</option>
                </select>
            </label>

            <button type="submit" class="btn btn-primary"
                    style="padding:14px 24px;font-size:15px;margin-top:8px;
                           min-height:44px;cursor:pointer;">
                Submit Service
            </button>
        </form>
    </div>
    """

    return HTMLResponse(page_shell(
        "Submit Agent Service | IndieStack",
        body,
        description="Submit an agent service to be discovered by AI coding agents.",
        user=user,
        canonical="/agents/submit",
    ))


# ── POST /agents/submit — Handle submission ──────────────────────────────

@router.post("/agents/submit")
async def agents_submit_post(
    request: Request,
    name: str = Form(...),
    tagline: str = Form(...),
    description: str = Form(""),
    capability_tags: str = Form(...),
    estimated_sla_minutes: int = Form(5),
    cost_estimate: int = Form(None),
    input_schema: str = Form("{}"),
    output_schema: str = Form("{}"),
    url: str = Form(""),
    source_type: str = Form("saas"),
):
    db = request.state.db

    # Validate required fields
    name = name.strip()
    tagline = tagline.strip()
    capability_tags = capability_tags.strip()
    if not name or not tagline or not capability_tags:
        return RedirectResponse(
            "/agents/submit?msg=Name, tagline, and capability tags are required.",
            status_code=303,
        )

    # Validate JSON schemas if provided
    for label, raw in [("Input schema", input_schema), ("Output schema", output_schema)]:
        raw = raw.strip()
        if raw and raw != "{}":
            try:
                json.loads(raw)
            except json.JSONDecodeError:
                return RedirectResponse(
                    f"/agents/submit?msg={label} is not valid JSON.",
                    status_code=303,
                )

    # Validate source_type
    if source_type not in ("saas", "code"):
        source_type = "saas"

    await create_agent_service(
        db,
        name=name,
        tagline=tagline,
        description=description.strip(),
        capability_tags=capability_tags,
        estimated_sla_minutes=estimated_sla_minutes,
        cost_estimate_cents=cost_estimate if cost_estimate else None,
        input_schema=input_schema.strip() or "{}",
        output_schema=output_schema.strip() or "{}",
        url=url.strip() or None,
        source_type=source_type,
    )

    return RedirectResponse(
        "/agents?msg=Service+submitted+successfully.+We'll+review+it+shortly.",
        status_code=303,
    )


# ── GET /agents/{slug} — Detail page ────────────────────────────────────

@router.get("/agents/{slug}", response_class=HTMLResponse)
async def agent_detail(request: Request, slug: str):
    db = request.state.db
    user = request.state.user
    agent = await get_agent_service_by_slug(db, slug)

    if not agent:
        body = """
        <div class="container" style="text-align:center;padding:64px 0;">
            <h1 style="font-family:var(--font-display);font-size:32px;">Not Found</h1>
            <p style="color:var(--ink-muted);margin-top:16px;">
                This agent service doesn't exist or hasn't been approved yet.
            </p>
            <a href="/agents" class="btn btn-primary" style="margin-top:24px;
               display:inline-block;padding:12px 24px;">Back to Agent Services</a>
        </div>
        """
        return HTMLResponse(
            page_shell("Not Found | IndieStack", body, user=user),
            status_code=404,
        )

    name = escape(agent["name"])
    tagline = escape(agent["tagline"] or "")
    description = escape(agent["description"] or "No description provided.")
    sla = agent["estimated_sla_minutes"] or 0
    cost_txt = _format_cost(agent["cost_estimate_cents"], agent["cost_unit"] or "per_task")
    success = agent["success_count"] or 0
    timeout = agent["timeout_count"] or 0
    timeout_rate = agent["timeout_rate"] or 0.0
    source = escape(agent["source_type"] or "saas")
    url = agent["url"] or ""

    # Format schemas
    def _pretty_schema(raw: str) -> str:
        try:
            parsed = json.loads(raw or "{}")
            formatted = json.dumps(parsed, indent=2)
            return escape(formatted)
        except (json.JSONDecodeError, TypeError):
            return escape(raw or "{}")

    input_schema_html = _pretty_schema(agent["input_schema"])
    output_schema_html = _pretty_schema(agent["output_schema"])

    url_block = ""
    if url:
        url_escaped = escape(url)
        url_block = f"""
        <a href="{url_escaped}" target="_blank" rel="noopener"
           class="btn btn-primary"
           style="display:inline-block;padding:12px 24px;font-size:14px;
                  margin-bottom:32px;min-height:44px;">
            Visit Service &rarr;
        </a>
        """

    body = f"""
    <div class="container" style="max-width:800px;padding:48px 24px;">
        <a href="/agents" style="color:var(--ink-muted);font-size:13px;
           text-decoration:none;display:inline-block;margin-bottom:24px;">
            &larr; All Agent Services
        </a>

        <div style="display:flex;justify-content:space-between;align-items:flex-start;
                    flex-wrap:wrap;gap:12px;margin-bottom:16px;">
            <h1 style="font-family:var(--font-display);font-size:32px;
                       color:var(--ink);margin:0;">{name}</h1>
            <span style="font-size:12px;font-family:var(--font-mono);
                         padding:4px 10px;border-radius:999px;
                         background:rgba(0,212,245,0.08);color:var(--accent);">
                {source}
            </span>
        </div>

        <p style="color:var(--ink-muted);font-size:16px;line-height:1.6;
                  margin:0 0 20px;">{tagline}</p>

        <div style="margin-bottom:24px;">
            {_capability_pills(agent["capability_tags"])}
        </div>

        {url_block}

        <!-- Stats row -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
                    gap:16px;margin-bottom:32px;">
            <div style="background:var(--card-bg);border:1px solid var(--border);
                        border-radius:12px;padding:20px;text-align:center;">
                <div style="font-size:24px;font-weight:700;color:var(--ink);">{sla}m</div>
                <div style="font-size:12px;color:var(--ink-muted);margin-top:4px;">Est. SLA</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--border);
                        border-radius:12px;padding:20px;text-align:center;">
                <div style="font-size:24px;font-weight:700;color:var(--ink);">{escape(cost_txt)}</div>
                <div style="font-size:12px;color:var(--ink-muted);margin-top:4px;">Cost</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--border);
                        border-radius:12px;padding:20px;text-align:center;">
                <div style="font-size:24px;font-weight:700;color:var(--accent);">{success}</div>
                <div style="font-size:12px;color:var(--ink-muted);margin-top:4px;">Successes</div>
            </div>
            <div style="background:var(--card-bg);border:1px solid var(--border);
                        border-radius:12px;padding:20px;text-align:center;">
                <div style="font-size:24px;font-weight:700;color:var(--ink);">{timeout}</div>
                <div style="font-size:12px;color:var(--ink-muted);margin-top:4px;">
                    Timeouts ({timeout_rate:.0%})
                </div>
            </div>
        </div>

        <!-- Description -->
        <div style="margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);
                       margin:0 0 12px;">Description</h2>
            <p style="color:var(--ink);font-size:15px;line-height:1.7;
                      white-space:pre-wrap;">{description}</p>
        </div>

        <!-- Input Schema -->
        <div style="margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);
                       margin:0 0 12px;">Input Schema</h2>
            <pre style="background:var(--card-bg);border:1px solid var(--border);
                        border-radius:8px;padding:16px;font-size:13px;
                        font-family:var(--font-mono);color:var(--ink);
                        overflow-x:auto;line-height:1.5;">{input_schema_html}</pre>
        </div>

        <!-- Output Schema -->
        <div style="margin-bottom:32px;">
            <h2 style="font-family:var(--font-display);font-size:20px;color:var(--ink);
                       margin:0 0 12px;">Output Schema</h2>
            <pre style="background:var(--card-bg);border:1px solid var(--border);
                        border-radius:8px;padding:16px;font-size:13px;
                        font-family:var(--font-mono);color:var(--ink);
                        overflow-x:auto;line-height:1.5;">{output_schema_html}</pre>
        </div>
    </div>
    """

    return HTMLResponse(page_shell(
        f"{agent['name']} | Agent Services | IndieStack",
        body,
        description=f"{agent['name']} — {tagline}. Agent service on IndieStack.",
        user=user,
        canonical=f"/agents/{escape(slug)}",
    ))


# ── GET /api/agents/search — JSON API ───────────────────────────────────

@router.get("/api/agents/search")
async def api_agents_search(request: Request):
    db = request.state.db

    capability = request.query_params.get("capability", "").strip()
    if not capability:
        return JSONResponse(
            {"error": "capability query parameter is required"},
            status_code=400,
        )

    try:
        max_sla = int(request.query_params.get("max_sla", "0") or "0")
    except (ValueError, TypeError):
        max_sla = 0

    try:
        max_cost = int(request.query_params.get("max_cost", "0") or "0")
    except (ValueError, TypeError):
        max_cost = 0

    source_type = request.query_params.get("source_type", "all").strip()
    if source_type not in ("saas", "code", "all"):
        source_type = "all"

    try:
        limit = min(int(request.query_params.get("limit", "10") or "10"), 50)
    except (ValueError, TypeError):
        limit = 10

    results = await search_agent_services(
        db,
        capability,
        max_sla=max_sla,
        max_cost=max_cost,
        source_type=source_type,
        limit=limit,
    )

    agents_list = []
    for r in results:
        agents_list.append({
            "slug": r["slug"],
            "name": r["name"],
            "tagline": r["tagline"],
            "capability_tags": r["capability_tags"],
            "estimated_sla_minutes": r["estimated_sla_minutes"],
            "cost_estimate_cents": r["cost_estimate_cents"],
            "cost_unit": r["cost_unit"],
            "success_count": r["success_count"] or 0,
            "timeout_rate": r["timeout_rate"] or 0.0,
            "source_type": r["source_type"],
            "url": r["url"],
        })

    return JSONResponse({"agents": agents_list})

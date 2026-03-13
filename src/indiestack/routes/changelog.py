from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from indiestack.routes.components import page_shell

router = APIRouter()

# Add new entries at the top. Each entry is one ship day.
CHANGELOG = [
    {
        "date": "2026-03-13",
        "title": "Demand Signals Pro Upgrade & Site Polish",
        "items": [
            ("feat", "Demand Signals Pro: Opportunity Score — algorithmic ranking of best gaps to fill"),
            ("feat", "Demand Signals Pro: Inline SVG sparklines — 14-day trend per signal"),
            ("feat", "Demand Signals Pro: Competitor density indicators — see market saturation at a glance"),
            ("feat", "Demand Signals Pro: Top 3 insight cards with sparklines and build CTAs"),
            ("feat", "Demand Signals Pro: Sortable columns (Score, Failed, Last Seen)"),
            ("feat", "Demand Signals Pro: Gaps-only live feed — filtered to what matters"),
            ("feat", "Demand Signals Pro: CSV export with enriched data"),
            ("feat", "Public tool submissions — no login required, just an email"),
            ("feat", "Sitewide copy-to-clipboard with visual feedback on all code blocks"),
            ("feat", "This changelog page — build in public"),
            ("feat", "Demand signal SEO improvements"),
            ("fix", "GitHub button readability on tool detail pages"),
            ("fix", "Dropdown menu contrast in dark mode"),
        ],
    },
    {
        "date": "2026-03-12",
        "title": "Website Rework & Supply Chain Pivot",
        "items": [
            ("feat", "Nav restructure: Explore | For Makers | Resources | Submit"),
            ("feat", "Landing page demand teaser — live gaps from agent searches"),
            ("feat", "Explore page search bar and collapsible filters"),
            ("feat", "Sitewide copy pivot: 'knowledge layer' to 'open-source supply chain'"),
            ("fix", "Hero text contrast on light mode"),
            ("fix", "Returning visitors analytics query"),
        ],
    },
    {
        "date": "2026-03-12",
        "title": "Agentic Package Manager",
        "items": [
            ("feat", "GitHub auto-indexer — 73 queries, catalog grew to 3,095 tools"),
            ("feat", "README enricher — auto-extracted metadata for 1,200+ tools"),
            ("feat", "1,279 compatibility pairs via pair generator"),
            ("feat", "Structured metadata on every tool: api_type, auth_method, sdk_packages, env_vars"),
            ("feat", "MCP Server v1.3.1 — scan_project, report_compatibility, check_health"),
            ("feat", "Per-tool Agent Cards at /cards/slug.json"),
            ("feat", "Demand Signals Pro — clusters, trends, export"),
            ("feat", "GEO lead magnet — generate llms.txt and Agent Card from any URL"),
        ],
    },
    {
        "date": "2026-03-07",
        "title": "Product Hunt Launch",
        "items": [
            ("feat", "Launched on Product Hunt"),
            ("feat", "25 categories — added Games, Learning, Newsletters, Creative"),
            ("feat", "What is IndieStack? explainer page"),
            ("feat", "Full vision alignment — indie tools to indie creations across 20+ files"),
            ("feat", "MCP Server v1.1.0 on PyPI"),
        ],
    },
    {
        "date": "2026-03-06",
        "title": "Pre-Launch Polish",
        "items": [
            ("feat", "Glassmorphism landing page with interactive grid canvas"),
            ("feat", "SVG icons replacing all emoji across the site"),
            ("feat", "Dark/light mode contrast fixes"),
            ("feat", "Maker stories on tool detail pages"),
            ("feat", "Tool health monitoring via GitHub API"),
            ("feat", "REST API docs page at /api"),
        ],
    },
]


def _badge(kind: str) -> str:
    colors = {
        "feat": ("var(--accent)", "rgba(0,212,245,0.1)"),
        "fix": ("var(--green,#22C55E)", "rgba(34,197,94,0.1)"),
        "improve": ("var(--gold,#E2B764)", "rgba(226,183,100,0.1)"),
    }
    fg, bg = colors.get(kind, ("var(--ink-muted)", "var(--card-bg)"))
    return f'<span style="display:inline-block;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;padding:2px 8px;border-radius:4px;color:{fg};background:{bg};margin-right:8px;">{kind}</span>'


@router.get("/changelog", response_class=HTMLResponse)
async def changelog_page(request: Request):
    user = getattr(request.state, "user", None)

    entries_html = ""
    for entry in CHANGELOG:
        items_html = ""
        for kind, text in entry["items"]:
            items_html += f'''
            <li style="display:flex;align-items:flex-start;gap:8px;padding:8px 0;border-bottom:1px solid var(--border);">
                {_badge(kind)}
                <span style="color:var(--ink);font-size:14px;line-height:1.5;">{text}</span>
            </li>'''

        entries_html += f'''
        <div style="margin-bottom:48px;">
            <div style="display:flex;align-items:baseline;gap:12px;margin-bottom:16px;">
                <time style="font-family:var(--font-mono);font-size:13px;color:var(--ink-muted);white-space:nowrap;">{entry["date"]}</time>
                <h2 style="font-family:var(--font-display);font-size:var(--heading-sm);color:var(--ink);margin:0;">{entry["title"]}</h2>
            </div>
            <ul style="list-style:none;padding:0;margin:0;">
                {items_html}
            </ul>
        </div>'''

    body = f'''
    <main style="max-width:720px;margin:0 auto;padding:48px 20px;">
        <div style="margin-bottom:40px;">
            <h1 style="font-family:var(--font-display);font-size:var(--heading-lg);color:var(--ink);margin:0 0 8px;">Changelog</h1>
            <p style="color:var(--ink-muted);font-size:15px;margin:0;">What we shipped, when we shipped it. Built in public by two uni students in Cardiff.</p>
        </div>
        {entries_html}
    </main>'''

    return page_shell("Changelog — IndieStack", body, description="What we shipped and when. IndieStack's build-in-public changelog.", user=user)

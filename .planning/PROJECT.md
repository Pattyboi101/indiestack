# IndieStack Growth Features

## What This Is

Four new features for IndieStack.ai that leverage existing but underutilized infrastructure -- agent citations, compatibility pairs, dependency analysis, and milestone SVGs -- to create compounding growth flywheels. These features surface hidden data to makers and developers, driving retention, acquisition, and SEO without manual marketing effort.

## Core Value

Give makers and developers actionable intelligence they can't get anywhere else -- AI citation data, empirical compatibility reports, vendor risk diagnostics, and shareable milestone cards -- all powered by data IndieStack already collects.

## Requirements

### Validated

- ✓ Agent citations tracked in `agent_citations` table via `/api/cite` -- existing
- ✓ 1,272 compatibility pairs stored, `report_compatibility()` in MCP + `/api/report-pair` on web -- existing
- ✓ `analyze_dependencies()` + `scan_project()` in MCP server -- existing
- ✓ `github_freshness` column populated for all tools via `check_tool_freshness.py` -- existing
- ✓ `milestones` table + `/api/milestone/{slug}.svg` generator -- existing
- ✓ `notifications` table + maker dashboard at `/dashboard` -- existing
- ✓ `tool_views`, `outbound_clicks`, `search_logs` analytics tables -- existing
- ✓ Demand signals via `/gaps` (free) and `/demand` (pro) -- existing
- ✓ `/alternatives/{slug}` competitive analysis pages -- existing

### Active

- [ ] AI Visibility Score -- surface citation data on maker dashboards
- [ ] Compatibility Graph -- "Works With" section on tool pages + explore filter
- [ ] Stack Import + Vendor Risk Report -- web UI for dependency analysis with shareable URLs
- [ ] Maker Ego Pings -- automated milestone triggers + shareable SVG cards

### Out of Scope

- AI chatbot / conversational UI -- MCP server handles AI-native discovery better
- Star rating system overhaul -- existing reviews table is sufficient
- Product Hunt-style launch pages -- PH owns this, our value is long-tail discovery
- New payment integrations -- Stripe Connect is sufficient for now
- Mobile app -- web-first, responsive design handles mobile

## Context

IndieStack is a production FastAPI + SQLite monolith with 3,095 tools, 19K+ weekly visitors, and a working MCP server on PyPI. The codebase uses pure Python string HTML templates (no Jinja2/React). All routes are in `src/indiestack/routes/`, DB queries in `src/indiestack/db.py` (5,097 lines), shared HTML in `routes/components.py`.

Key existing infrastructure to build on:
- `agent_citations` table: logs every MCP query that surfaces a tool
- Compatibility pairs: 1,272 pairs via `/api/report-pair` and MCP `report_compatibility()`
- MCP server: `analyze_dependencies()` parses package.json/requirements.txt
- Freshness monitoring: `github_freshness` column (active/stale/inactive/unknown)
- Milestones: achievement system with SVG card generator
- Notifications: in-app bell alerts on maker dashboard

Patrick deploys from his machine via Fly.io. We push to GitHub, he reviews and deploys.

## Constraints

- **Tech stack**: Pure Python string HTML (f-strings). No Jinja2, no React, no build step.
- **CSS**: All in `components.py` design_tokens() or inline. No external stylesheets.
- **Database**: SQLite via aiosqlite. All queries in `db.py`. WAL mode.
- **Deploy**: Patrick reviews + deploys. We push code to GitHub repo.
- **Design**: Navy/Cyan/Gold palette, DM Serif Display + DM Sans fonts, 12px radius cards.
- **Testing**: `smoke_test.py` with 40+ endpoint checks. No pytest.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Build all 4 features as one project | They share infrastructure (citations, pairs, milestones) and compound together | -- Pending |
| Start with AI Visibility Score | Smallest build, most differentiated, uses data already being collected | -- Pending |
| Coarse phase structure (3-5 phases) | Features are well-scoped, avoid over-engineering the plan | -- Pending |
| Follow existing code patterns | Python string HTML, all queries in db.py, routes in routes/ | -- Pending |

---
*Last updated: 2026-03-13 after initialization*

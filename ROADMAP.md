# IndieStack Roadmap

> Created 2026-03-06. Updated 2026-03-13. Living document.

See `VISION.md` for the full picture of where IndieStack is going.

---

## Phase 1: Launch (Complete — March 7)

- [x] "What is IndieStack" page (`/what-is-indiestack`)
- [x] Landing page hero — broadened from "dev tools" to "everything indie"
- [x] 25 categories (added Games, Learning, Newsletters, Creative)
- [x] Submit page — "Submit your creation" messaging
- [x] Full site vision alignment — "indie tools" → "indie creations" across 20+ files
- [x] MCP Server v1.1.0 on PyPI
- [x] Product Hunt launch (March 7)

---

## Phase 2: Post-Launch Growth (Complete — March 8-13)

- [x] "Surprise me" discovery button on explore page
- [x] "Featured on Product Hunt" badge (env var gated)
- [x] Seed 25 non-dev listings (games, newsletters, learning, creative)
- [x] GitHub auto-indexer — 73 search queries, grew catalog 835 → 3,095
- [x] README enricher — auto-extracted install commands, env vars, frameworks for 1,200+ tools
- [x] Pair generator — 1,279 compatibility pairs
- [x] Agentic Package Manager metadata — api_type, auth_method, sdk_packages, env_vars on every tool
- [x] MCP Server v1.3.1 — scan_project, report_compatibility, check_health (15 tools total)
- [x] Per-tool Agent Cards (`/cards/{slug}.json`)
- [x] Demand Signals Pro ($15/month) — clusters, trends, source breakdown, JSON export
- [x] GEO lead magnet (`/geo`) — generate llms.txt + Agent Card from any URL
- [x] Pixel avatars — 7x7, 16 colors, admin approval
- [x] Pixel art tool icons — 6x6, 8 colors, maker-editable on dashboard

---

## Phase 3: Site Refresh & Quality (In Progress — March 13+)

- [x] Nav restructure — Explore | For Makers ▾ | Resources ▾ | [Submit]
- [x] Landing page refresh — demand teaser, updated hero, supply chain positioning
- [x] Explore page simplification — search bar, collapsible filters
- [x] "What is IndieStack?" rewrite for new positioning
- [x] Sitewide copy pass — "knowledge layer" → "open-source supply chain"
- [x] `/new` and `/tag/{slug}` redirects to `/explore`
- [x] Maker stories on tool detail pages
- [x] Tool health monitoring (GitHub API)
- [x] Proactive recommendations ("New for you" on explore)
- [x] REST API docs page (`/api`)
- [ ] Integration recipes — "how to wire Hanko + Polar + Plausible into Next.js"
- [ ] "This Week in Indie" auto-generated digest
- [ ] Community reviews and integration guides
- [ ] Cross-domain discovery — "developers who use X also use Y"

---

## Phase 4: Flywheel & Revenue (Next)

- [ ] Ignite the growth flywheel — demand signals → maker submissions → agent recs → more signals
- [ ] First real Demand Signals Pro customers
- [ ] Measurable MCP server install/usage telemetry
- [ ] Compatibility matrix from real agent usage data
- [ ] Agent-to-agent discovery protocol
- [ ] Content strategy for organic traffic (alternatives pages, comparison pages, guides)
- [ ] Ed's role defined — clear ownership of a product area

---

## Phase 5: The Moat (Late 2026+)

- [ ] "AI Recommendations" as a distribution channel (10K+ recs/day)
- [ ] Every new AI agent connects to IndieStack as default
- [ ] Tool makers publish to IndieStack like devs publish to npm
- [ ] IndieStack becomes the canonical supply chain for all AI agents
- [ ] The flywheel: more agents → more recs → more makers → better catalog → more agents

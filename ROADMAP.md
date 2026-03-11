# IndieStack Roadmap

> Created 2026-03-06. Living document.

See `VISION.md` for the full picture of where IndieStack is going.

---

## Phase 1: Launch Ready (Before Saturday March 7)

- [x] **"What is IndieStack" page** (`/what-is-indiestack`) — full story: what, why, where it's going. Nav link.
- [x] **Landing page hero update** — broadened from "dev tools" to "everything indie." Hints at bigger vision.
- [x] **Expand categories** — added Games & Entertainment, Learning & Education, Newsletters & Content, Creative Tools. Moved Questarr, Minimalistic_Flashcards into correct categories. 25 total.
- [x] **Submit page messaging** — "Submit your creation" not "Submit your tool." Welcomes anything indie-built.
- [x] **Full site vision alignment** — "indie tools" → "indie creations" across 20+ files. CTAs, descriptions, SEO, footer, emails, social templates.
- [x] **MCP Server v1.1.0** — Published to PyPI. Broader instructions, `source_type='all'` default, new `discover-indie` prompt, "creations" language.
- [x] **PH welcome banner** — Auto-detects `?ref=producthunt`, persists via localStorage, dismissible.
- [ ] **PH gallery screenshots** — 5 images at 1270x760px
- [ ] **PH listing created** — all assets uploaded, first comment pre-written

---

## Phase 2: Post-Launch Week (March 8-14)

- [x] **"Surprise me" discovery button** on explore page — random creation on every click
- [x] ~~**Public roadmap page**~~ — built then killed pre-launch (too much "not ready" energy for PH visitors)
- [x] **"Featured on Product Hunt" badge** — prepped on landing page, activate with `PH_FEATURED` env var
- [ ] Process PH-exclusive tool submissions (instant review)
- [ ] Submit to Hacker News (3-5 days after PH, technical angle)
- [x] **Seed 25 non-dev listings** — 7 games, 5 newsletters, 6 learning, 7 creative tools. All genuinely indie-built.
- [ ] Write "what we learned launching on PH" Twitter thread

---

## Phase 3: Depth (March-April 2026)

- [x] **Maker stories on tool detail pages** — questionnaire on dashboard (motivation, challenge, advice, fun fact). Displays as "About the Maker" on tool page.
- [ ] "This Week in Indie" auto-generated digest page
- [ ] Integration recipes — "how to wire Hanko + Polar + Plausible into Next.js"
- [x] **Tool health monitoring** — GitHub API checks for last commit, open issues, archive status. `/admin/github-health` trigger. Activity signals shown on tool detail page.
- [ ] Backfill descriptions for 47 hidden/pending tools
- [ ] Grow catalog toward 1,500 listings
- [ ] Community reviews and integration guides

---

## Phase 4: Intelligence (Summer 2026)

- [ ] Compatibility matrix — track which tools work well together from usage data
- [x] **Proactive recommendations** — "New for you" section on explore page based on bookmark history. Personalized, no-filter first page only.
- [ ] Cross-domain discovery — "developers who use X also use Y"
- [x] **REST API docs page** (`/api`) — documents all 15+ JSON endpoints with params, examples, and curl snippets
- [x] **Browser extension scaffold** — Chrome Manifest V3, detects 21 SaaS sites, shows indie alternatives. `/extension/` directory.
- [ ] Agent-to-agent protocol support

---

## Phase 5: The Moat (Late 2026+)

- [ ] "AI Recommendations" as a distribution channel (10K+ recs/day)
- [ ] Every new AI agent connects to IndieStack as default knowledge source
- [ ] Tool makers publish to IndieStack like devs publish to npm
- [ ] IndieStack becomes the canonical knowledge layer for all AI agents
- [ ] The flywheel: more agents -> more recs -> more makers -> better catalog -> more agents

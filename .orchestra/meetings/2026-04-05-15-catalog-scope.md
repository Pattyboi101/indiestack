# Meeting: Catalog Scope — Out-of-Scope Tools
**Date:** 2026-04-05 15:00
**Status:** Closed
**Attendees:** Patrick (chair), CEO, Frontend, Backend, DevOps, Content, MCP

---

## Agenda

During today's catalog cleanup (~430 tools re-categorised), a pattern emerged: the catalog contains ~20-30 approved **consumer apps** that are clearly out of IndieStack's developer-tool scope.

Examples found and parked in developer-tools:
- Fitness trackers: fastnfitness, foodyou, flexify, git-sweaty, hitrava
- Weather: forecastie, bo-android
- Crypto wallets: dogecoin, grin
- GTA modding: gta-dat-toolkit-inspector-chase-nodes-converter
- Recipes: cook
- Music players: algermusicplayer, listen1-desktop, lx-music-mobile (now moved to media-server)
- Baby tracker: babybuddy
- Mental health app: ifme

Context:
- IndieStack scope = developer tools for indie devs and small teams (auth, payments, analytics, infra etc.)
- "Indie" is the curation filter, not a content type
- These were presumably bulk-imported and manually approved by mistake
- They're diluting search quality and category accuracy

Key questions:
1. Should we bulk-reject these via admin? Who does it?
2. Do we need a clearer scope policy at submission time (prevent future inflow)?
3. Is there value in a "general apps" or "open source projects" category, or is rejection cleaner?
4. Are there any of these we'd keep? (e.g. audiobookshelf as a media server has dev relevance)

---

## Discussion

### CEO

These need to go. Consumer apps dilute the catalog's signal for AI agents and developers alike. "IndieStack recommended a fitness tracker" is a trust killer for our primary use case. Bulk rejection is the right call — not a new "general apps" category, which would just be a holding pen for junk. Patrick to action via /admin. We should also update submission guidelines to block future inflow. Any claimed tools (makers who paid Maker Pro for these) should be handled case-by-case — but a quick check suggests none of these consumer apps have claimed makers.

---

### Frontend

From a UX perspective, rejection beats a catch-all category. If we add "open source projects" or similar, we'd need to maintain it and it'd show up on the explore page looking out of place. The cleanest outcome: these tools simply disappear from search results and category pages. The explore page categories already look better after today's cleanup — fitness trackers in "developer-tools" was the worst outcome of the batch import.

---

### Backend

Mechanical: `UPDATE tools SET status='rejected' WHERE slug IN (...)` on production. Low risk. Before running, check if any of these are claimed (`SELECT maker_id FROM tools WHERE slug IN (...) AND maker_id IS NOT NULL`). If any have maker_ids, those users should be notified (email) before rejection. Also worth checking: do any of these have upvotes or stack inclusions? Can note them but shouldn't block rejection. A future improvement is a submission-time scope filter — simple keyword check against the tool description could catch "fitness", "recipe", "weather", "wallet" etc. before they enter the review queue.

---

### DevOps

No infra changes needed. Run a backup before the bulk rejection (standard practice for any bulk DB write). The FTS index will need rebuilding after status changes — same `INSERT INTO tools_fts(tools_fts) VALUES('rebuild')` pattern used today. No deploy required for a pure status update on production.

---

### Content

The submission form needs explicit scope language. Current copy says "developer tools" which is vague. Suggest adding: *"IndieStack is for developer tools only — auth, payments, analytics, databases, APIs, SDKs, CLIs, dev infrastructure, and developer-facing SaaS. Consumer apps, games, creative tools, and personal productivity apps are out of scope."* Add this to the submit page and the /guidelines page. For the ~25 tools being rejected: no announcement needed, they were approved by mistake.

---

### MCP

The MCP server's `find_tools` and `get_recommendations` currently surface these tools if their tags or descriptions match a query. A developer asking for "health tracking API" could surface a consumer fitness app — that's a bad agent experience. Rejection removes them from FTS immediately. No MCP server code change needed, just the DB status update + FTS rebuild. This reinforces why catalog data quality matters: agents trust our results. Every consumer app in the catalog is a potential false recommendation.

---

## Action Items

- [ ] **Patrick** — Bulk-reject consumer apps via /admin (confirmed via tag audit):
  - **Fitness/health**: fastnfitness, foodyou, flexify, git-sweaty, hitrava, export2garmin, kenko, fitness, open-wearables, opennutritracker, mi-fit-and-zepp-workout-exporter
  - **Weather**: forecastie, bo-android, open-source-android-weather-app
  - **Food/recipes**: cook, mealie, kitchenowl
  - **Crypto wallets**: dogecoin, grin
  - **Consumer misc**: babybuddy, ifme, lifeforge, norteapp, simple-wedding-invitation, gta-dat-toolkit-inspector-chase-nodes-converter
  - **Music players (already moved to media-server)**: algermusicplayer, listen1-desktop, lx-music-mobile
- [ ] **Patrick** — Check `/admin` for any other obvious consumer apps that slipped through; run audit query if needed
- [ ] **Backend** — Before bulk reject, run: `SELECT slug, maker_id FROM tools WHERE slug IN (...) AND maker_id IS NOT NULL` to check for claimed tools
- [ ] **Content** — Update submit page and /guidelines with explicit scope statement (consumer apps out of scope)
- [ ] **Backend** (future) — Add submission-time keyword filter for obvious consumer app terms ("fitness", "recipe", "crypto wallet", "weather app") to flag before review queue

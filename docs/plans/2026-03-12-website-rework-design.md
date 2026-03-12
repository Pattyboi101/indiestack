# Website Rework Design

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refresh the site's navigation, landing page, explore page, and copy to reflect the strategic pivot from "knowledge layer for AI agents" to "open-source supply chain for agentic workflows."

**Architecture:** Pure copy/template changes across 5 route files + components.py. No new database tables, no new routes. Existing routes /new and /tags become redirects to /explore with query params.

---

## 1. Navigation Restructure

### Current
- Desktop: `Explore | Browse ▾ (AI Optimize, New, Tags, Stacks, Demand Board, What is IndieStack?) | Submit`
- Mobile: Flat list of all items

### New
- Desktop: `Explore | For Makers ▾ (AI Optimize, Submit a Tool) | Resources ▾ (What is IndieStack?, Demand Board, Stacks) | [Submit button]`
- Mobile: Flat list — Explore, AI Optimize, Stacks, Demand Board, What is IndieStack?, Submit

### Rationale
- "Browse" dropdown mixed discovery pages with maker tools and informational pages
- "Explore" vs "Browse" distinction was confusing — now Explore is the single discovery surface
- Maker-oriented items grouped under "For Makers" (AI Optimize = GEO lead magnet, Submit)
- Informational/product items grouped under "Resources"
- Submit button stays as cyan pill CTA in the nav bar

### Files
- `src/indiestack/routes/components.py` — `nav_html()` function

---

## 2. Landing Page Refresh

### Current sections (top to bottom)
1. MCP banner (v1.3 announcement)
2. Hero (Tool of the Week, "Stop letting your AI reinvent the wheel")
3. MCP Walkthrough (3-step install flow)
4. Search Widget ("Try it Yourself")
5. Trending Strip (6 tools)
6. Browse by Category (25-category grid)
7. Maker CTA (blue gradient, "Join our list of makers")

### New sections
1. **Banner** — Update from MCP v1.3 announcement to "3,095+ indie creations. Agent Cards live." or similar milestone messaging
2. **Hero** — Keep structure (TOTW, conversational code block, CTAs). Update copy:
   - Status tag: "KNOWLEDGE LAYER FOR AI AGENTS" → keep or update to "OPEN-SOURCE SUPPLY CHAIN FOR AI" (TBD at implementation)
   - Subtitle: Update to reference 3,095 tools and the agentic workflow positioning
   - Stats pills: Keep tool count + AI recommendations
3. **MCP Walkthrough** — Keep as-is. Update description text if it references old positioning.
4. **Search Widget** — Keep as-is.
5. **Trending Strip** — Keep. Consider renaming to "Popular right now."
6. **Browse by Category** — Keep as-is.
7. **Demand Teaser** *(NEW)* — Replace maker CTA with a compact "What agents are searching for" section:
   - 3-4 live demand gaps from `get_demand_gaps()` (same data as /gaps free tier)
   - Each gap shows the search query + "Build This →" button
   - "See more on the Demand Board →" link to /gaps
   - Shows platform is alive, creates urgency for makers
8. **Maker CTA** *(SLIMMED)* — Single line + submit button below the demand teaser. No full gradient section needed since "For Makers" is now in the nav.

### Files
- `src/indiestack/routes/landing.py`

---

## 3. Explore Page Simplification

### Current
- Category dropdown (25+ categories)
- Tag pills (top 20 tags)
- Sort options (relevance/hot/newest/upvotes)
- Source type pills (All/Code/SaaS)
- "New for you" personalized section (logged in)
- 24 items per page

### New
- **Search bar at top** — prominent, replaces need to manually browse filters
- **Smart defaults** — loads with "hot" sort, no filters pre-selected. Feels like a feed.
- **Visible filters** — Category dropdown + Sort dropdown only
- **Collapsible "More filters"** — Tags, Source type (Code/SaaS) hidden behind a toggle. Power users can expand.
- **"New for you" stays** — good personalisation signal for logged-in users

### Route absorption
- `/new` → redirect to `/explore?sort=newest`
- `/tags` → redirect to `/explore?tag=X` (index page) or keep as standalone if it has unique value as a tag cloud

### Files
- `src/indiestack/routes/explore.py`
- `src/indiestack/routes/new.py` — add redirect
- `src/indiestack/routes/tags.py` — evaluate redirect vs keep

---

## 4. "What is IndieStack?" Update

### Current
- Hero: "The Knowledge Layer for AI Agents"
- PH launch story framing
- Stats: tool count, code/SaaS split, category count

### New
- Hero: "The Open-Source Supply Chain for Agentic Workflows"
- Reframe story: agents assemble from existing indie building blocks rather than building from scratch
- Updated stats: 3,095 tools, 25 categories, Agent Cards, GEO
- Mention Agent Cards + MCP server as the delivery mechanism
- Remove PH-launch-specific language that feels stale
- Keep the "creation is exploding" narrative — it's still true and compelling

### Files
- `src/indiestack/routes/what_is.py`

---

## 5. Sitewide Copy Pass

Find and update across all public route files:
- "knowledge layer for AI agents" → "open-source supply chain for agentic workflows" (or shorter contextual variants)
- Hardcoded tool counts → dynamic where possible (most are already dynamic)
- Footer tagline if it references old positioning
- Meta descriptions / OG tags referencing old positioning
- `agent-card.json` description field
- `llms.txt` description

### Files
- `src/indiestack/routes/components.py` — footer, meta tags
- `src/indiestack/main.py` — agent-card.json, llms.txt
- Any route file with hardcoded "knowledge layer" references

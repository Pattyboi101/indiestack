# Website Rework Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refresh navigation, landing page, explore page, and sitewide copy to reflect the strategic pivot to "open-source supply chain for agentic workflows."

**Architecture:** Pure template changes across Python string HTML files. No new database tables, no new routes (just redirects). All changes are in `src/indiestack/routes/` and `src/indiestack/main.py`.

**Tech Stack:** Python/FastAPI, pure f-string HTML templates, aiosqlite.

**Testing:** No unit tests for templates. Verification is `python3 smoke_test.py` (38 endpoints) + syntax checks via `python3 -c "import ast; ast.parse(open('FILE').read())"`.

**Design doc:** `docs/plans/2026-03-12-website-rework-design.md`

---

## Task 1: Navigation Restructure

**Files:**
- Modify: `src/indiestack/routes/components.py` — `nav_html()` function (lines ~607-692)

**Context:** The nav currently has "Explore" as a standalone link and "Browse" as a dropdown with 6 mixed items (AI Optimize, New, Tags, Stacks, Demand Board, What is IndieStack?). This is confusing — items aren't all "browse" actions. We're restructuring to: `Explore | For Makers ▾ | Resources ▾ | [Submit]`.

**Step 1: Read the current nav**

```bash
cd /home/patty/indiestack
python3 -c "import ast; ast.parse(open('src/indiestack/routes/components.py').read()); print('OK')"
```

Read `src/indiestack/routes/components.py` lines 607-692 to see the exact nav HTML.

**Step 2: Replace the Browse dropdown with two new dropdowns**

In the desktop nav section, replace the "Browse" dropdown with:

**"For Makers" dropdown:**
```html
<div class="nav-dropdown">
    <button class="nav-link nav-dropdown-trigger">For Makers <span style="font-size:10px;margin-left:2px;">&#9662;</span></button>
    <div class="nav-dropdown-menu">
        <a href="/geo" class="nav-dropdown-item">AI Optimize</a>
        <a href="/submit" class="nav-dropdown-item">Submit a Tool</a>
    </div>
</div>
```

**"Resources" dropdown:**
```html
<div class="nav-dropdown">
    <button class="nav-link nav-dropdown-trigger">Resources <span style="font-size:10px;margin-left:2px;">&#9662;</span></button>
    <div class="nav-dropdown-menu">
        <a href="/what-is-indiestack" class="nav-dropdown-item">What is IndieStack?</a>
        <a href="/gaps" class="nav-dropdown-item">Demand Board</a>
        <a href="/stacks" class="nav-dropdown-item">Stacks</a>
    </div>
</div>
```

Keep: "Explore" standalone link, Submit cyan pill button, theme toggle, auth links.

**Step 3: Update the mobile menu**

Replace the mobile menu links with the flat list:
- Explore (`/explore`)
- AI Optimize (`/geo`)
- Stacks (`/stacks`)
- Demand Board (`/gaps`)
- What is IndieStack? (`/what-is-indiestack`)
- Submit (`/submit`)

**Step 4: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/components.py').read()); print('OK')"
```

**Step 5: Smoke test**

```bash
python3 smoke_test.py
```

Expected: 38/38 pass (nav change is cosmetic, all routes still exist).

---

## Task 2: Landing Page — Copy & Banner Update

**Files:**
- Modify: `src/indiestack/routes/landing.py` (lines ~106-230)

**Context:** The landing page hero and banner still reference "MCP Server v1.3" and "KNOWLEDGE LAYER FOR AI AGENTS." We're updating to reflect 3,095 tools, Agent Cards, and the new positioning.

**Step 1: Read the current landing page**

Read `src/indiestack/routes/landing.py` lines 100-230 to see the exact banner and hero HTML.

**Step 2: Update the banner**

Find the banner section (~lines 106-128). The current banner promotes MCP Server v1.3. Update the copy to something like:
- "3,095+ indie creations — now with Agent Cards" or similar milestone messaging
- Keep the AI lookups counter if it's still relevant

**Step 3: Update the hero copy**

- Status tag (~line 178): Change from "KNOWLEDGE LAYER FOR AI AGENTS" to "OPEN-SOURCE SUPPLY CHAIN FOR AI" (or keep if Patrick prefers — check design doc)
- Subheading (~line 184-185): Update to reference the new positioning. Something like: "3,095+ indie creations your AI can discover, compare, and assemble — before building from scratch."
- Main headline "Stop letting your AI reinvent the wheel" — keep (it's good)
- Stats pills (~lines 222-227): Keep as-is (already dynamic)

**Step 4: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/landing.py').read()); print('OK')"
```

---

## Task 3: Landing Page — Demand Teaser Section

**Files:**
- Modify: `src/indiestack/routes/landing.py` (lines ~477-493, the maker CTA section)

**Context:** The current maker CTA at the bottom is a blue gradient section saying "Join our list of makers." We're replacing it with a demand teaser (live gaps from agent searches) + a slimmed maker CTA below.

**Step 1: Read the current maker CTA section**

Read `src/indiestack/routes/landing.py` lines 470-500.

**Step 2: Check what demand data is available**

The landing page function already has DB access and caching. Check `src/indiestack/db.py` for `get_demand_gaps()` or similar functions used by `/gaps`. We need to call the same query to get 3-4 recent demand gaps.

**Step 3: Add demand data fetch**

In the landing page route function, add a cached query to fetch 3-4 demand gaps. Use the same pattern as other cached queries in the file (TTL cache). Something like:

```python
# Inside the landing page route, with the other cached queries
demand_gaps = await get_demand_gaps(db, limit=4)  # or whatever the function signature is
```

Make sure to import the function at the top of the file.

**Step 4: Replace the maker CTA with demand teaser + slim CTA**

Replace the blue gradient maker CTA section with:

```python
# Demand teaser
demand_section = ''
if demand_gaps:
    gap_items = ''
    for gap in demand_gaps[:4]:
        query = escape(gap['query'] if isinstance(gap, dict) else gap[0])
        gap_items += f'''
        <div style="display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid var(--border);">
            <span style="color:var(--ink);font-size:14px;">"{query}"</span>
            <a href="/submit" style="color:var(--accent);font-size:13px;font-weight:600;text-decoration:none;">Build This &rarr;</a>
        </div>'''
    demand_section = f'''
    <section style="max-width:700px;margin:60px auto;padding:0 20px;">
        <h2 style="font-family:var(--font-display);font-size:var(--heading-md);color:var(--ink);text-align:center;margin-bottom:8px;">What agents are searching for</h2>
        <p style="text-align:center;color:var(--ink-muted);font-size:14px;margin-bottom:24px;">Real queries from AI agents that found no matching tool</p>
        <div style="border:1px solid var(--border);border-radius:12px;overflow:hidden;background:var(--surface);">
            {gap_items}
        </div>
        <p style="text-align:center;margin-top:16px;"><a href="/gaps" style="color:var(--accent);font-size:14px;text-decoration:none;font-weight:500;">See more on the Demand Board &rarr;</a></p>
    </section>'''
```

Then add a slim maker CTA below:

```python
maker_cta = f'''
<section style="text-align:center;padding:40px 20px 60px;">
    <p style="color:var(--ink-muted);font-size:15px;margin-bottom:16px;">Built something indie? Get it discovered by AI agents.</p>
    <a href="/submit" style="display:inline-block;background:var(--accent);color:#fff;padding:12px 28px;border-radius:99px;font-weight:600;text-decoration:none;font-size:15px;">Submit Your Creation</a>
</section>'''
```

**Step 5: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/landing.py').read()); print('OK')"
```

**Step 6: Smoke test**

```bash
python3 smoke_test.py
```

---

## Task 4: Explore Page Simplification

**Files:**
- Modify: `src/indiestack/routes/explore.py` (lines ~82-147, filter rendering)

**Context:** The explore page has too many visible filters — category dropdown, 20 tag pills, sort options, source type pills, ejectable checkbox. We're simplifying to show Category + Sort by default, with everything else behind a "More filters" toggle.

**Step 1: Read the current explore page**

Read `src/indiestack/routes/explore.py` fully.

**Step 2: Add a search bar at the top of the filter area**

Above the existing filters, add a search input that submits to `/explore?q=QUERY`:

```html
<div style="margin-bottom:20px;">
    <input type="text" name="q" value="{escape(query)}" placeholder="Search tools..."
        style="width:100%;padding:12px 16px;border:1px solid var(--border);border-radius:8px;font-size:15px;background:var(--surface);color:var(--ink);font-family:var(--font-body);"
    />
</div>
```

Make sure the route handler accepts a `q` parameter and filters results accordingly (check if it already does).

**Step 3: Keep Category + Sort visible, wrap others in collapsible**

Keep the category dropdown and sort dropdown visible. Wrap the tag pills, source type pills, and ejectable checkbox in a collapsible section:

```html
<details style="margin-top:12px;">
    <summary style="cursor:pointer;color:var(--accent);font-size:14px;font-weight:500;list-style:none;">
        More filters <span style="font-size:10px;">&#9662;</span>
    </summary>
    <div style="margin-top:12px;">
        <!-- Tag pills, source type pills, ejectable checkbox go here -->
    </div>
</details>
```

The `<details>` element is native HTML — no JS needed, works everywhere.

**Step 4: Auto-open filters if any are active**

If a tag, source type, or ejectable filter is active, add the `open` attribute to `<details>`:

```python
filters_open = ' open' if (active_tag or source_type != 'all' or ejectable) else ''
f'<details{filters_open} style="margin-top:12px;">'
```

**Step 5: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/explore.py').read()); print('OK')"
```

**Step 6: Smoke test**

```bash
python3 smoke_test.py
```

---

## Task 5: Redirect /new and /tags

**Files:**
- Modify: `src/indiestack/routes/new.py`
- Modify: `src/indiestack/routes/tags.py`

**Context:** Now that Explore absorbs New and Tags functionality, we redirect `/new` to `/explore?sort=newest`. For `/tags`, we keep the tag index page (it has SEO value as a tag cloud) but it's no longer in the nav. Individual tag pages `/tag/{slug}` redirect to `/explore?tag={slug}`.

**Step 1: Read both files**

Read `src/indiestack/routes/new.py` and `src/indiestack/routes/tags.py`.

**Step 2: Redirect /new**

Replace the `/new` route handler body with a redirect:

```python
from fastapi.responses import RedirectResponse

@router.get("/new")
async def new_tools(request: Request):
    return RedirectResponse(url="/explore?sort=newest", status_code=302)
```

Keep imports clean — remove any now-unused imports.

**Step 3: Redirect individual tag pages**

In `tags.py`, change the `/tag/{slug}` route to redirect:

```python
@router.get("/tag/{slug}")
async def tag_page(request: Request, slug: str):
    return RedirectResponse(url=f"/explore?tag={slug}", status_code=302)
```

Keep the `/tags` index page as-is (tag cloud has SEO value, just not in the nav anymore).

**Step 4: Verify the explore page handles tag= parameter**

Read the explore page route to confirm it accepts a `tag` query parameter and filters by it. If not, add that filter logic.

**Step 5: Verify syntax on both files**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/new.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/tags.py').read()); print('OK')"
```

**Step 6: Smoke test**

```bash
python3 smoke_test.py
```

Note: Smoke test may need updating if it tests `/new` or `/tag/{slug}` and now gets 302 instead of 200. Update expected status codes if needed.

---

## Task 6: "What is IndieStack?" Page Update

**Files:**
- Modify: `src/indiestack/routes/what_is.py` (lines ~45-307)

**Context:** The page currently says "The Knowledge Layer for AI Agents" and has PH-launch-era copy. We're updating to "The Open-Source Supply Chain for Agentic Workflows" with refreshed messaging.

**Step 1: Read the full file**

Read `src/indiestack/routes/what_is.py`.

**Step 2: Update the hero**

- Title (~line 48): "The Knowledge Layer for AI Agents" → "The Open-Source Supply Chain for Agentic Workflows"
- Subtitle: Update to reference 3,095 tools, Agent Cards, and the assembly-over-reinvention narrative

**Step 3: Update section copy**

- "The Shift" section (~lines 65-84): Keep the "creation is exploding" narrative. Update to emphasise agents assembling from building blocks rather than building from scratch.
- "If someone made it" section (~lines 86-151): Keep the category examples — they're great. Update framing language if it says "knowledge layer."
- "How it Works" section (~lines 155-196): Update feature card descriptions to mention Agent Cards, compatibility pairs, and the supply chain model.
- "For Everyone/Builders/Makers" sections (~lines 200-277): Refresh copy to match new positioning.
- "Creation Explosion" section (~lines 280-307): Keep "built by two uni students" — authentic and good. Update any stale stats.

**Step 4: Remove stale PH-specific language**

Search for "Product Hunt", "launched", "launch week" or similar and remove or reframe.

**Step 5: Verify syntax**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/routes/what_is.py').read()); print('OK')"
```

---

## Task 7: Sitewide Copy Pass

**Files:**
- Modify: `src/indiestack/main.py` (lines ~692-842)
- Modify: `src/indiestack/routes/components.py` (footer ~line 804, meta tags)

**Context:** "Knowledge layer for AI agents" appears in the footer, llms.txt, agent-card.json, and possibly meta descriptions. We're updating all references.

**Step 1: Update footer**

In `components.py`, find the footer tagline (~line 804):
- "The knowledge layer for AI agents and indie creators." → "The open-source supply chain for AI agents and indie creators."

**Step 2: Update llms.txt**

In `main.py`, find the llms.txt endpoint (~line 703):
- "The knowledge layer for AI agents" → "The open-source supply chain for agentic workflows"

**Step 3: Update agent-card.json**

In `main.py`, find the agent-card.json description (~line 795):
- Already uses f-string with `{tool_count}+`. Update the prefix: "The knowledge layer for AI agents." → "The open-source supply chain for agentic workflows."

**Step 4: Check meta descriptions**

In `components.py`, check the `page_shell()` function (~line 1348) for default meta description. Update if it references "knowledge layer."

**Step 5: Grep for any remaining references**

```bash
cd /home/patty/indiestack
grep -rn "knowledge layer" src/indiestack/
```

Fix any remaining occurrences.

**Step 6: Verify syntax on both files**

```bash
python3 -c "import ast; ast.parse(open('src/indiestack/main.py').read()); print('OK')"
python3 -c "import ast; ast.parse(open('src/indiestack/routes/components.py').read()); print('OK')"
```

**Step 7: Full smoke test**

```bash
python3 smoke_test.py
```

Expected: 38/38 pass (or 36/38 if /new and /tag redirects changed expected codes — update smoke test if needed).

---

## Parallelisation

These tasks can be grouped for parallel execution:

**Group A (independent — can run in parallel):**
- Task 1: Nav restructure (components.py nav_html)
- Task 6: What is IndieStack update (what_is.py)

**Group B (independent — can run in parallel after Group A):**
- Task 2: Landing page copy update (landing.py hero/banner)
- Task 4: Explore page simplification (explore.py)

**Group C (depends on Task 4):**
- Task 5: Redirect /new and /tags

**Group D (depends on Task 1):**
- Task 3: Landing page demand teaser (landing.py bottom section)
- Task 7: Sitewide copy pass (main.py + components.py footer)

**Final verification after all tasks:**
```bash
cd /home/patty/indiestack
python3 smoke_test.py
```
